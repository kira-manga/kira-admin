#!/usr/bin/env python3
"""Private, reviewed-input Linux PostgreSQL lifecycle controller; never runs on import.

--prepare-only is read-only and cannot establish runtime readiness. Actual execution
requires --execute-reviewed, a fresh v2 source manifest, caller-pinned hashes, and all
resource/ownership/API/smoke gates. Historical Colima evidence is never reused as proof.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import time

import freeze_app29_integrated_driver_v2 as inventory
import run_app29_integrated_driver_validation_linux as driver
import app29_linux_owned_processes as owned_processes


ROOT = Path(__file__).absolute().parents[2]
CONFIG = ".kira-runtime-tools/vm/launch-config.json"
CONFIG_SHA256 = "e9cfa86b22cf37c59d81744f8e8fc687be132d0ffc8899b054797c39fbe7ad84"
CONFIG_REVIEW = "review/working/campaign-resume-20260908-linux-01/runtime-provisioning/launch-config.json"
THIS_TOOL = "review/working/run_app29_integrated_postgres_validation_linux.py"
CONTROL_TESTS = "review/working/test_app29_linux_postgres_runner.py"
DRIVER = "review/working/run_app29_integrated_driver_validation_linux.py"
DRIVER_TESTS = "review/working/test_app29_linux_validation_runner.py"
OWNERSHIP_TOOL = "review/working/app29_linux_owned_processes.py"
OWNERSHIP_TESTS = "review/working/test_app29_linux_owned_processes.py"
NOTE = "review/remediation/app-29-w03-development08-linux-postgres-runner.md"
GIB = 1024**3
MIN_FREE_BYTES = 8 * GIB
PORTS = {"ssh": 24922, "docker_api": 24975, "mapped_first": 25000, "mapped_last": 25127}
RESOURCE_LIMITS = {"vcpus": 2, "guest_memory_mib": 4096, "virtual_disk_bytes": 8 * GIB,
                   "host_free_disk_prerequisite_bytes": MIN_FREE_BYTES}
API_VERSION = "1.32"
POSTGRES_IMAGE = "postgres:17.6-alpine"
ALLOWED_IMAGES = {POSTGRES_IMAGE, "testcontainers/ryuk:0.12.0"}
OWNER_LABEL = "me.manga.kira.runtime-owner"
BATCH_LABEL = "me.manga.kira.runtime-batch"
CONTROLLER = "kira-app29-linux-postgres-controller-v1"
SMOKE_MEMORY = 512 * 1024**2


class Refused(RuntimeError):
    pass


class Unavailable(Refused):
    """Only incomplete fixture startup, not a failed ownership/resource assertion."""


def require(condition, message):
    if not condition:
        raise Refused(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def remaining(deadline, cap=None):
    value = deadline - time.monotonic()
    require(value > 0, "Bounded operation deadline expired")
    return value if cap is None else min(value, cap)


def safe(path: Path) -> Path:
    """Validate the root/ancestors too; never use resolve() to hide a symlink."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "Expected an absolute non-traversing path")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        require(not current.is_symlink(), "Symlink in controlled path")
        if current.exists() and current != path:
            require(current.is_dir(), "Non-directory controlled parent")
    return path


def regular(path: Path) -> Path:
    path = safe(path)
    require(path.is_file() and stat.S_ISREG(path.lstat().st_mode), "Missing/nonregular controlled input")
    require(path.stat().st_nlink == 1, "Unexpected hard-linked controlled input")
    return path


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with regular(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            result.update(chunk)
    return result.hexdigest()


def json_bytes(data):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique)


def load_json(path):
    require(regular(path).stat().st_size <= 8 * 1024**2, "Oversized metadata input")
    return json_bytes(path.read_bytes())


def all_ports(config):
    p = config["ports"]
    return {p["ssh"], p["docker_api"], *range(p["mapped_first"], p["mapped_last"] + 1)}


def verify_tool_tree(config):
    declared = config["tool_tree_manifest"]
    manifest_path = Path(declared["path"])
    require(digest(manifest_path) == declared["sha256"], "Private tool-tree manifest drift")
    manifest = load_json(manifest_path)
    root = safe(Path(declared["root"]))
    require(root.is_dir(), "Missing private tool-tree root")
    require(manifest["schema"] == declared["schema"] == "kira-private-tool-tree-sha256-v1"
            and manifest["root"] == str(root) and manifest["excludes"] == [], "Invalid private tool-tree contract")
    actual = []
    # os.walk does not traverse symlink directories. Symlink leaves are compared literally.
    def walk_error(error):
        raise error
    for folder, directories, files in os.walk(root, followlinks=False, onerror=walk_error):
        for path in [Path(folder)] + [Path(folder) / n for n in directories + files if (Path(folder) / n).is_symlink()
                                     or not (Path(folder) / n).is_dir()]:
            value = path.lstat()
            row = {"path": path.relative_to(root).as_posix(), "mode": f"{stat.S_IMODE(value.st_mode):04o}"}
            if stat.S_ISLNK(value.st_mode):
                row.update(type="symlink", target=os.readlink(path))
            elif stat.S_ISDIR(value.st_mode):
                row.update(type="directory")
            elif stat.S_ISREG(value.st_mode):
                row.update(type="file", size=value.st_size, sha256=digest(path))
            else:
                raise Refused("Special file in private tool tree")
            actual.append(row)
    actual.sort(key=lambda row: row["path"])
    expected = manifest["entries"]
    require(isinstance(expected, list) and len({row["path"] for row in expected}) == len(expected), "Duplicate private tool-tree member")
    # The pinned producer orders pathlib components, not POSIX string separators.
    # Its bytes/order are already committed by sha256; compare exact member rows
    # independently of that traversal order, without normalizing any row content.
    require(actual == sorted(expected, key=lambda row: row["path"]) and len(actual) == declared["entry_count"],
            "Private tool-tree byte/mode/membership drift")
    return {"manifest_sha256": declared["sha256"], "entries_verified": len(actual)}


def overlay_info(config):
    path = regular(Path(config["paths"]["overlay"]))
    with path.open("rb") as stream:
        header = stream.read(104)
        require(len(header) >= 72, "Short qcow2 header")
        magic, version, backing_offset, backing_size, cluster_bits, size = struct.unpack(">4sIQIIQ", header[:32])
        require(magic == b"QFI\xfb" and version in (2, 3) and size == 8 * GIB
                and 9 <= cluster_bits <= 21 and 0 < backing_size <= 4096, "Unexpected qcow2/virtual disk size")
        require(backing_offset >= 72 and backing_offset + backing_size <= path.stat().st_size, "Invalid backing filename extent")
        if version == 3:
            # Incompatible dirty/corrupt flags must not be silently adopted after a crash.
            require(len(header) == 104 and struct.unpack(">Q", header[72:80])[0] == 0,
                    "Dirty/corrupt/unsupported retained overlay; review recovery first")
            require(struct.unpack(">I", header[100:104])[0] >= 104, "Invalid qcow2 v3 header length")
        stream.seek(backing_offset)
        backing = stream.read(backing_size).decode("utf-8")
    require(backing == config["paths"]["read_only_base_image"], "Overlay backing image changed")
    return {"virtual_bytes": size, "backing_image": backing, "size_before": path.stat().st_size,
            "allocated_bytes_before": path.stat().st_blocks * 512, "sha256_before": digest(path)}


def tcp_listeners(proc_root=Path("/proc")):
    rows = []
    for family in ("tcp", "tcp6"):
        for line in (proc_root / "net" / family).read_text().splitlines()[1:]:
            columns = line.split()
            if len(columns) > 9 and columns[3] == "0A":
                address, port = columns[1].split(":")
                rows.append({"family": family, "address": address, "port": int(port, 16), "inode": columns[9]})
    return rows


def require_unused_ports(config, rows):
    require(not any(row["port"] in all_ports(config) for row in rows), "A requested forwarded port already has a listener")


def require_owned_listeners(config, pid, rows, fd_inodes):
    wanted = all_ports(config)
    selected = [row for row in rows if row["port"] in wanted]
    owned = [row for row in rows if row["inode"] in fd_inodes]
    require(len(selected) == len({row["port"] for row in selected}), "Duplicate QEMU forwarded listeners")
    require(all(row["family"] == "tcp" and row["address"] == "0100007F" and row["inode"] in fd_inodes for row in selected),
            "Forwarded listener is non-loopback or not owned by this QEMU")
    require({row["port"] for row in owned} <= wanted, "Unexpected owned TCP listener")
    if {row["port"] for row in selected} != wanted:
        raise Unavailable("QEMU forwards are not yet complete")
    return {"qemu_pid": pid, "loopback_listener_count": len(selected), "ports": sorted(wanted)}


def configuration(root, expected_sha, *, free_bytes=None, affinity=None, listeners=None):
    root = safe(Path(root).absolute())
    path = regular(root / CONFIG)
    require(expected_sha == CONFIG_SHA256 and digest(path) == expected_sha, "Unreviewed or changed launch configuration")
    require(digest(regular(root / CONFIG_REVIEW)) == expected_sha, "Private and reviewed launch configurations differ")
    config = load_json(path)
    prefix = safe(root / ".kira-runtime-tools")
    require(config["owner"] == load_json(prefix / "ownership.json") and config["owner"]["prefix"] == str(prefix), "Runtime ownership mismatch")
    require(config["ports"] == PORTS and config["resources"] == RESOURCE_LIMITS, "Port/resource limits changed")
    require(config["requires_primary_review_and_explicit_launch"] is True, "Missing explicit launch restriction")
    for key in ("prefix", "vm_root", "read_only_tool_share"):
        require(Path(config["paths"][key]).is_relative_to(prefix), "Foreign runtime directory")
    for key, value in config["paths"].items():
        if not key.startswith("guest_"):
            require(safe(Path(value)).is_relative_to(prefix), "Runtime path escaped private prefix")
    for directory in (prefix, prefix / "vm"):
        require(directory.is_dir() and directory.stat().st_uid == os.geteuid()
                and stat.S_IMODE(directory.stat().st_mode) & 0o077 == 0,
                "Runtime directory must remain private")
    for candidate in (prefix / "ownership.json", Path(config["paths"]["overlay"]), Path(config["paths"]["ssh_private_key"])):
        value = regular(candidate).stat()
        require(value.st_uid == os.geteuid() and stat.S_IMODE(value.st_mode) == 0o600, "Private runtime file ownership/mode differs")
    # Never read/hash/copy the private identity; only its location/type/permissions are checked.
    require(config["argv"][0] == str(prefix / "root/usr/bin/qemu-system-x86_64")
            and "-daemonize" not in config["argv"] and "-accel" in config["argv"]
            and config["argv"][config["argv"].index("-accel") + 1] == "tcg,thread=multi", "Not the reviewed foreground TCG command")
    require(config["api_compatibility"]["required_client_api_version"] == API_VERSION
            and config["api_compatibility"]["guest_daemon_min_api_version"] == API_VERSION, "Docker API compatibility changed")
    require(config["test_environment"] == {"DOCKER_HOST": "tcp://127.0.0.1:24975", "TESTCONTAINERS_HOST_OVERRIDE": "127.0.0.1",
                                          "TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE": "/run/kira-runtime/docker.sock"}, "Foreign test Docker endpoint")
    for filename, expected in config["immutable_hashes"].items():
        candidate = Path(filename)
        require(candidate.is_relative_to(root) or filename == "/usr/bin/ssh", "Foreign immutable input")
        require(digest(candidate) == expected, "Immutable runtime input changed")
    selected = config["cpu_affinity"]
    allowed = set(os.sched_getaffinity(0) if affinity is None else affinity)
    require(len(selected) == 2 and len(set(selected)) == 2 and set(selected) <= allowed, "Two reviewed host CPUs are not available")
    available = shutil.disk_usage(root).free if free_bytes is None else free_bytes
    require(available >= MIN_FREE_BYTES, "Require at least 8 GiB free before the batch")
    tree = verify_tool_tree(config)
    overlay = overlay_info(config)
    for key in ("qmp_socket", "qemu_pidfile", "serial_log"):
        target = safe(Path(config["paths"][key]))
        require(not target.exists(), "Pre-existing runtime process/output artifact; never overwrite")
    require_unused_ports(config, tcp_listeners() if listeners is None else listeners)
    return config, {"launch_config_sha256": expected_sha, "tool_tree": tree, "overlay": overlay,
                    "minimum_free_bytes": MIN_FREE_BYTES, "free_bytes_before": available, "host_cpu_affinity": selected}


def process_identity(pid):
    result = owned_processes.process_identity(pid)
    if result is None:
        return None
    try:
        result["executable"] = os.readlink(Path("/proc", str(pid), "exe")) if result["state"] != "Z" else None
        return result
    except FileNotFoundError:
        return None


def same_process(expected, current):
    return owned_processes.same_identity(expected, current)


class Journal:
    def __init__(self, folder, initial):
        self.folder = folder
        self.data = {**initial, "started_at": now(), "commands": [], "failures": [], "cleanup": {}}
        self.sequence = 0
        self.publication_failed = False

    def publish(self):
        self.sequence += 1
        try:
            temporary = safe(self.folder / f"state-{self.sequence:06d}.tmp")
            with temporary.open("x") as output:
                json.dump(self.data, output, indent=2)
                output.write("\n")
            safe(self.folder / "result.json")
            os.replace(temporary, self.folder / "result.json")
        except BaseException:
            self.publication_failed = True
            raise

    def failure(self, label, error):
        # Do not serialize arbitrary exception text, HTTP bodies, credentials or environments.
        self.data["failures"].append({"stage": label, "type": type(error).__name__})

    def attempt(self, label, action):
        try:
            value = action()
            self.data["cleanup"][label] = {"completed": True, "proof": value}
            return value
        except BaseException as error:
            self.failure(label, error)
            self.data["cleanup"][label] = {"completed": False}
        finally:
            try:
                self.publish()
            except BaseException as error:
                self.failure("publish-" + label, error)


class ProcessScope:
    """Popen ownership is recorded in memory before any fallible evidence publication."""

    def __init__(self, journal, children):
        self.journal, self.children = journal, children
        self.handles = []

    def spawn(self, label, command, env, *, affinity=None, cleanup=False):
        require(self.children.active, "Active child ownership is required before Popen")
        log = safe(self.journal.folder / (label + ".log"))
        entry = {"name": label, "command": command, "started_at": now()}
        self.journal.data["commands"].append(entry)
        def publish():
            try:
                self.journal.publish()
            except BaseException as error:
                self.journal.failure(label + "-publication", error)
                if not cleanup:
                    raise
        publish()
        with contextlib.ExitStack() as resources:
            try:
                output = resources.enter_context(log.open("xb"))
            except BaseException as error:
                self.journal.failure(label + "-log", error)
                if not cleanup:
                    raise
                output, log = subprocess.DEVNULL, None
            process = subprocess.Popen(command, env=env, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True,
                                       preexec_fn=(lambda: os.sched_setaffinity(0, affinity)) if affinity is not None else None)
            owned = {"process": process, "entry": entry, "identity": None, "log": log}
            self.handles.append(owned)  # Never move behind identity(), checkpoint(), or a filesystem read.
            self.children.track()
        owned["identity"] = process_identity(process.pid)
        require(owned["identity"] is not None and owned["identity"]["pgid"] == process.pid, "Cannot bind owned process identity")
        entry.update(pid=process.pid, identity=owned["identity"])
        publish()
        return owned

    def wait(self, owned, timeout, *, output_limit=128 * 1024**2, cleanup=False):
        process = owned["process"]
        deadline = time.monotonic() + timeout
        while True:
            if owned["log"] is not None:
                require(regular(owned["log"]).stat().st_size <= output_limit, "Owned command output exceeded its evidence bound")
            try:
                code = process.wait(timeout=min(0.25, max(0.001, deadline - time.monotonic())))
                owned["entry"].update(exit_code=code, finished_at=now())
                if owned["log"] is not None:
                    require(regular(owned["log"]).stat().st_size <= output_limit,
                            "Joined command output exceeded its evidence bound")
                try:
                    self.journal.publish()
                except BaseException as error:
                    self.journal.failure(owned["entry"]["name"] + "-join-publication", error)
                    if not cleanup:
                        raise
                return code
            except subprocess.TimeoutExpired:
                require(time.monotonic() < deadline, "Owned command exceeded its bounded deadline")

    def stop(self, owned, grace=15):
        process = owned["process"]
        if process.poll() is not None:
            process.wait(timeout=1)
            return {"pid": process.pid, "joined": True, "exit_code": process.returncode}
        current = process_identity(process.pid)
        expected = owned["identity"]
        # Before the first identity publication, an unreaped Popen child still belongs to us.
        if expected is None:
            require(current is not None and current["ppid"] == os.getpid() and current["pgid"] == process.pid,
                    "Cannot recover post-spawn command ownership")
            expected = owned["identity"] = current
        require(same_process(expected, current) and current["pgid"] == process.pid
                and current["executable"] == expected["executable"], "Refusing to signal a changed process identity")
        self.children.signal_owned(expected, signal.SIGTERM)
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            current = process_identity(process.pid)
            require(same_process(expected, current) and current["pgid"] == process.pid, "Lost owned process before escalation")
            self.children.signal_owned(expected, signal.SIGKILL)
            process.wait(timeout=10)
        owned["entry"].update(exit_code=process.returncode, joined_after_stop=True, finished_at=now())
        return {"pid": process.pid, "joined": True, "exit_code": process.returncode}

    def run(self, label, command, env, timeout=30, *, cleanup=False):
        owned = None
        try:
            owned = self.spawn(label, command, env, cleanup=cleanup)
            code = self.wait(owned, timeout, output_limit=2 * 1024**2, cleanup=cleanup)
            if code != 0:
                raise Unavailable("Owned helper did not complete successfully")
            require(owned["log"] is not None, "Cleanup ran without a retainable output proof")
            return regular(owned["log"]).read_bytes()
        finally:
            # Includes failure after Popen but before spawn() could return the handle.
            candidates = [row for row in self.handles if row["entry"]["name"] == label]
            for row in candidates:
                self.stop(row)


class _DeadlineReader(io.RawIOBase):
    """Keep status/header/chunk/body reads on one absolute monotonic budget."""
    def __init__(self, raw_socket, raw_file, deadline):
        self.socket, self.file, self.deadline = raw_socket, raw_file, deadline

    def readable(self):
        return True

    def readinto(self, data):
        self.socket.settimeout(remaining(self.deadline))
        size = self.file.readinto(data)
        remaining(self.deadline)
        return size

    def close(self):
        try:
            self.file.close()
        finally:
            super().close()


class _DeadlineSocket:
    def __init__(self, stream, deadline):
        self.stream, self.deadline = stream, deadline

    def sendall(self, data):
        data = memoryview(data)
        while data:
            self.stream.settimeout(remaining(self.deadline))
            size = self.stream.send(data)
            require(size > 0, "Short bounded HTTP write")
            data = data[size:]
        remaining(self.deadline)

    def makefile(self, mode):
        require(mode == "rb", "Unexpected HTTP stream mode")
        # SocketIO retains the fd if HTTPConnection closes a Connection:close socket
        # before the response body is read. Closing the response releases that reference.
        return io.BufferedReader(_DeadlineReader(self.stream, self.stream.makefile("rb", buffering=0), self.deadline))

    def close(self):
        self.stream.close()


class DockerAPI:
    """Only the explicit loopback endpoint; no Docker context, proxy, auth or credential loading."""

    def __init__(self, port, journal):
        require(port == PORTS["docker_api"], "Foreign Docker API port")
        self.port, self.journal = port, journal

    def request(self, method, path, body=None, *, expected=(200,), timeout=10, maximum=2 * 1024**2, raw=False):
        require(path.startswith("/") and not path.startswith("//"), "Unsafe API path")
        require(0 < timeout <= 600 and 0 < maximum <= 16 * 1024**2, "Unbounded Docker API request")
        deadline = time.monotonic() + timeout
        record = {"method": method, "path": path, "started_at": now()}
        self.journal.data.setdefault("docker_requests", []).append(record)
        # Bodies are not logged: future container configuration may contain fixture credentials.
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=remaining(deadline))
        response = None
        try:
            data = None if body is None else json.dumps(body).encode()
            connection.connect()
            connection.sock = _DeadlineSocket(connection.sock, deadline)
            connection.request(method, path, body=data, headers={"Content-Type": "application/json"} if data else {})
            response = connection.getresponse()
            record["status"] = response.status
            parts, size = [], 0
            while True:
                remaining(deadline)
                chunk = response.read1(min(65536, maximum + 1 - size))
                remaining(deadline)
                if not chunk:
                    break
                parts.append(chunk)
                size += len(chunk)
                require(size <= maximum, "Oversized Docker API response")
            payload = b"".join(parts)
            require(len(payload) <= maximum and response.status in expected, "Unexpected/oversized Docker API response")
            return payload if raw else json_bytes(payload) if payload else None
        finally:
            record["finished_at"] = now()
            try:
                if response is not None:
                    response.close()
            finally:
                connection.close()


def validate_api(version, info):
    def parse(text):
        require(isinstance(text, str) and re.fullmatch(r"[0-9]+\.[0-9]+", text) is not None, "Invalid Docker API version")
        return tuple(int(part) for part in text.split("."))
    require(re.fullmatch(r"29\.1\.3(?:[-+].*)?", version.get("Version", "")) is not None, "Unexpected Docker engine version")
    require(parse(version["MinAPIVersion"]) == (1, 32) <= parse(version["ApiVersion"]), "Docker29 client API1.32 compatibility not proved")
    require(info.get("NCPU") == 2 and 3 * GIB <= info.get("MemTotal", 0) <= 4 * GIB,
            "Guest Docker CPU/memory bounds not proved")
    require(info.get("MemoryLimit") is True and info.get("CpuCfsQuota") is True and info.get("CgroupVersion") == "2",
            "Guest memory/CPU cgroup enforcement is unavailable")
    require(info.get("DockerRootDir") == "/var/lib/kira-runtime/docker" and info.get("Driver") == "overlay2",
            "Unexpected guest Docker ownership/storage")
    return {key: info[key] for key in ("NCPU", "MemTotal", "MemoryLimit", "CpuCfsQuota", "CgroupVersion", "DockerRootDir", "Driver")}


def owned_container_ids(rows, owner, batch):
    require(isinstance(rows, list), "Invalid container inventory")
    ids = []
    for row in rows:
        labels = row.get("Labels") or {}
        tagged = labels.get("org.testcontainers") == "true"
        smoke = labels.get(OWNER_LABEL) == owner and labels.get(BATCH_LABEL) == batch
        require(row.get("Image") in ALLOWED_IMAGES and (tagged or smoke), "Unknown container: refuse removal, still stop owned VM")
        value = row.get("Id", "")
        require(re.fullmatch(r"[0-9a-f]{64}", value) is not None and value not in ids, "Invalid/duplicate container identity")
        ids.append(value)
    return ids


def recv_exact(stream, count, deadline):
    result = b""
    while len(result) < count:
        stream.settimeout(remaining(deadline))
        chunk = stream.recv(count - len(result))
        remaining(deadline)
        if not chunk:
            raise Unavailable("PostgreSQL fixture closed its startup connection")
        result += chunk
    return result


def postgres_smoke(port, deadline=None):
    require(PORTS["mapped_first"] <= port <= PORTS["mapped_last"], "Refusing a port outside owned QEMU forwards")
    deadline = time.monotonic() + 8 if deadline is None else min(deadline, time.monotonic() + 8)
    with socket.create_connection(("127.0.0.1", port), timeout=remaining(deadline, 3)) as stream:
        def send(data):
            stream.settimeout(remaining(deadline))
            stream.sendall(data)
            remaining(deadline)
        startup = struct.pack(">I", 196608) + b"user\0postgres\0database\0postgres\0application_name\0kira-owned-smoke\0\0"
        send(struct.pack(">I", len(startup) + 4) + startup)
        authenticated, ready, result, complete = False, False, False, False
        for _ in range(64):
            kind = recv_exact(stream, 1, deadline)
            size = struct.unpack(">I", recv_exact(stream, 4, deadline))[0]
            require(4 <= size <= 65536, "Unbounded PostgreSQL smoke frame")
            payload = recv_exact(stream, size - 4, deadline)
            if kind == b"E":
                raise Unavailable("PostgreSQL fixture not ready (error body intentionally not recorded)")
            require(kind in (b"R", b"S", b"K", b"Z", b"T", b"D", b"C", b"N"), "Unexpected PostgreSQL frame type")
            if kind == b"R":
                require(not ready and not authenticated and payload == b"\0\0\0\0", "Unexpected authentication request; never supply/log a password")
                authenticated = True
            if kind == b"Z":
                require(payload == b"I", "PostgreSQL fixture was not idle")
                if not ready:
                    require(authenticated, "Missing PostgreSQL authentication receipt")
                    query = b"select 1;\0"
                    send(b"Q" + struct.pack(">I", len(query) + 4) + query)
                    ready = True
                else:
                    require(result and complete, "PostgreSQL smoke did not complete the expected row/query")
                    send(b"X\0\0\0\4")
                    return {"query": "select 1", "expected_row_observed": True}
            if kind == b"D":
                require(ready and not result and payload == b"\0\1\0\0\0\1" + b"1", "Unexpected PostgreSQL smoke DataRow")
                result = True
            if kind == b"C":
                require(ready and result and not complete and payload == b"SELECT 1\0", "Unexpected PostgreSQL command completion")
                complete = True
        raise Refused("PostgreSQL smoke exceeded its frame bound")


def parse_exec_limits(data):
    stdout = b""
    while data:
        require(len(data) >= 8 and data[0] in (1, 2) and data[1:4] == b"\0\0\0", "Invalid Docker exec frame")
        size = struct.unpack(">I", data[4:8])[0]
        require(size <= 4096 and len(data) >= 8 + size and data[0] == 1, "Unexpected exec stderr/extent")
        stdout += data[8:8 + size]
        data = data[8 + size:]
    lines = stdout.decode("ascii").splitlines()
    require(len(lines) == 2 and lines[0] == str(SMOKE_MEMORY), "Actual container memory.max was not enforced")
    quota, period = (int(part) for part in lines[1].split())
    require(quota > 0 and period > 0 and quota * 2 == period, "Actual container CPU quota was not enforced")
    return {"memory_max": int(lines[0]), "cpu_quota": quota, "cpu_period": period}


GUEST_STATUS = r'''
import json, pathlib, subprocess
p=pathlib.Path
def service(name):
    data=subprocess.run(['systemctl','show',name,'--property=LoadState,ActiveState,MainPID,Result'],capture_output=True,text=True,check=True).stdout
    return dict(line.split('=',1) for line in data.splitlines())
print(json.dumps({'owner':json.loads(p('/etc/kira-runtime/owner.json').read_text()),
'prepared':p('/run/kira-runtime/preflight.txt').is_file(),
'prepare_service':service('kira-runtime-prepare.service'),'docker_service':service('kira-docker.service')}))
'''

GUEST_PROBE = r'''
import json, os, pathlib, subprocess
p=pathlib.Path
mem={line.split(':')[0]:line.split(':')[1].strip() for line in p('/proc/meminfo').read_text().splitlines()}
mounts=[line.split() for line in p('/proc/mounts').read_text().splitlines()]
service=subprocess.run(['systemctl','show','kira-docker.service','--property=ActiveState,MainPID'],capture_output=True,text=True,check=True).stdout
print(json.dumps({'owner':json.loads(p('/etc/kira-runtime/owner.json').read_text()),'cpus':len(os.sched_getaffinity(0)),
'memory_bytes':int(mem['MemTotal'].split()[0])*1024,'controllers':p('/sys/fs/cgroup/cgroup.controllers').read_text().split(),
'cgroup2':any(row[1]=='/sys/fs/cgroup' and row[2]=='cgroup2' for row in mounts),
'port_range':[int(x) for x in p('/proc/sys/net/ipv4/ip_local_port_range').read_text().split()],
'tool_mount_readonly':any(row[1]=='/opt/kira-tools' and row[2]=='9p' and 'ro' in row[3].split(',') for row in mounts),
'service':dict(line.split('=',1) for line in service.splitlines()),'daemon_min_api':json.loads(p('/etc/kira-runtime/daemon.json').read_text())['min-api-version']}))
'''

GUEST_STOP = r'''
import json, pathlib, subprocess, time
p=pathlib.Path
expected=OWNER_JSON
assert json.loads(p('/etc/kira-runtime/owner.json').read_text())==expected
stopped=subprocess.run(['systemctl','stop','kira-docker.service'],timeout=110).returncode
end=time.monotonic()+20
while True:
    live=[]
    for f in p('/proc').iterdir():
        if not f.name.isdigit(): continue
        try: exe=str((f/'exe').readlink())
        except FileNotFoundError: continue
        if exe.startswith('/opt/kira-tools/') and any(name in exe.rsplit('/',1)[-1] for name in ('dockerd','containerd','docker-proxy','runc')): live.append(int(f.name))
    if not live or time.monotonic()>=end: break
    time.sleep(.2)
properties=subprocess.run(['systemctl','show','kira-docker.service','--property=ActiveState,MainPID'],capture_output=True,text=True,check=True).stdout
listeners=[]
for family in ('tcp','tcp6'):
    for line in (p('/proc/net')/family).read_text().splitlines()[1:]:
        row=line.split(); port=int(row[1].rsplit(':',1)[1],16)
        if row[3]=='0A' and (port==2375 or 25000<=port<=25127): listeners.append(port)
print(json.dumps({'stop_exit':stopped,'properties':dict(line.split('=',1) for line in properties.splitlines()),
'owned_service_pids':live,'guest_runtime_listeners':listeners,'docker_pidfile_absent':not p('/run/kira-runtime/dockerd.pid').exists()}))
'''


def validate_guest(proof, owner):
    require(proof.get("owner") == owner, "Guest ownership receipt differs")
    require(proof.get("cpus") == 2 and 3 * GIB <= proof.get("memory_bytes", 0) <= 4 * GIB, "Guest resource bounds differ")
    require(proof.get("cgroup2") is True and {"cpu", "memory"} <= set(proof.get("controllers", [])), "Guest cgroup controllers absent")
    require(proof.get("port_range") == [25000, 25127] and proof.get("tool_mount_readonly") is True,
            "Guest port allocator/read-only share proof failed")
    require(proof.get("daemon_min_api") == API_VERSION and proof.get("service", {}).get("ActiveState") == "active"
            and int(proof["service"].get("MainPID", 0)) > 1, "Guest daemon not configured/active")
    return proof


def guest_prepared(proof, owner):
    require(proof.get("owner") == owner, "Connected guest is not owned")
    for key in ("prepare_service", "docker_service"):
        state = proof.get(key, {})
        require(state.get("ActiveState") in ("inactive", "activating", "active"), "Guest preparation/service failed")
        require(state.get("LoadState") in ("not-found", "loaded"), "Guest service loading failed")
        require(state.get("Result", "success") == "success", "Guest service recorded a failure")
    return (proof.get("prepared") is True and proof["prepare_service"]["ActiveState"] == "active"
            and proof["docker_service"]["ActiveState"] == "active"
            and int(proof["docker_service"].get("MainPID", 0)) > 1)


def validate_guest_stop(proof):
    require(proof.get("stop_exit") == 0 and proof.get("properties", {}).get("ActiveState") == "inactive"
            and proof["properties"].get("MainPID") == "0" and proof.get("owned_service_pids") == []
            and proof.get("guest_runtime_listeners") == [] and proof.get("docker_pidfile_absent") is True,
            "Guest container/service/process/listener absence was not proved")
    return proof


def successful_vm_termination(proof):
    """Absence is not successful termination; reject missing or loosely typed outcomes."""
    return (isinstance(proof, dict) and proof.get("spawned") is True and proof.get("never_spawned") is not True
            and type(proof.get("pid")) is int and proof["pid"] > 0
            and proof.get("joined") is True and proof.get("identity_bound") is True
            and proof.get("process_absent") is True and proof.get("exit_code_known") is True
            and proof.get("exit_code_type") == "int"
            and type(proof.get("exit_code")) is int and proof["exit_code"] == 0)


class Runtime:
    def __init__(self, root, config, args, journal, controller):
        self.root, self.config, self.args, self.journal, self.controller = root, config, args, journal, controller
        self.reaper = owned_processes.OwnedChildren()
        self.scope = ProcessScope(journal, self.reaper)
        self.api = DockerAPI(config["ports"]["docker_api"], journal)
        self.guest_owned = False
        self.helper_sequence = 0
        self.runtime_artifacts = {}
        self.ssh_env = {"PATH": "/usr/bin:/bin", "HOME": str(controller), "LANG": "C.UTF-8", "TZ": "UTC"}

    def vm(self):
        return next((row for row in self.scope.handles if row["entry"]["name"] == "qemu"), None)

    def acquire(self):
        self.journal.data["subreaper"] = self.reaper.activate()
        self.journal.publish()

    def launch(self):
        _config, proof = configuration(self.root, self.args.launch_config_sha256)
        self.journal.data["configuration_rechecked_at_launch"] = proof
        self.journal.publish()
        env = {**self.ssh_env, **self.config["environment"]}
        self.scope.spawn("qemu", self.config["argv"], env, affinity=self.config["cpu_affinity"])

    def ssh(self, name, script, timeout=30, *, cleanup=False):
        self.listener_proof()
        self.helper_sequence += 1
        command = [*self.config["ssh_argv_prefix"], shlex.join(["sudo", "-n", "python3", "-c", script])]
        output = self.scope.run(f"ssh-{self.helper_sequence:03d}-{name}", command, self.ssh_env, timeout, cleanup=cleanup)
        return json_bytes(output)

    def listener_proof(self):
        vm = self.vm()
        require(vm is not None and vm["process"].poll() is None, "Owned VM exited before runtime proof")
        current = process_identity(vm["process"].pid)
        require(same_process(vm["identity"], current) and current["executable"] == self.config["argv"][0], "VM executable/identity changed")
        require(set(os.sched_getaffinity(current["pid"])) == set(self.config["cpu_affinity"]), "VM CPU affinity changed")
        inodes = set()
        for fd in Path("/proc", str(current["pid"]), "fd").iterdir():
            try:
                target = os.readlink(fd)
            except FileNotFoundError:
                continue
            if target.startswith("socket:["):
                inodes.add(target[8:-1])
        return require_owned_listeners(self.config, current["pid"], tcp_listeners(), inodes)

    def ready(self):
        deadline = time.monotonic() + 420
        listeners = None
        while time.monotonic() < deadline:
            try:
                listeners = self.listener_proof()
                break
            except Unavailable:
                time.sleep(remaining(deadline, 1))
        require(listeners is not None, "Bounded QEMU listener readiness failed")
        # Bind early: an ownership/service/API failure later must not erase safe VM evidence.
        self.bind_artifacts()
        prepared = False
        while time.monotonic() < deadline:
            try:
                status = self.ssh("startup", GUEST_STATUS, timeout=remaining(deadline, 12))
            except Unavailable:
                require(not self.journal.publication_failed, "Readiness evidence publication failed")
                time.sleep(remaining(deadline, 1))
                continue
            # Malformed JSON, wrong owner, failed service and wrong resource values
            # are not transient availability and are never retried into approval.
            require(status.get("owner") == self.config["owner"], "Connected guest is not owned")
            if not self.guest_owned:
                self.guest_owned = True
                self.pin_host_key()
            prepared = guest_prepared(status, self.config["owner"])
            if prepared:
                break
            time.sleep(remaining(deadline, 1))
        require(self.guest_owned and prepared, "Bounded guest SSH/service readiness failed")
        proof = validate_guest(self.ssh("resources", GUEST_PROBE, timeout=remaining(deadline, 30)), self.config["owner"])
        require(self.api.request("GET", "/_ping", raw=True, timeout=remaining(deadline, 10)).strip() == b"OK", "Docker ping failed")
        version = self.api.request("GET", "/version", timeout=remaining(deadline, 10))
        info = validate_api(version, self.api.request("GET", "/v1.32/info", timeout=remaining(deadline, 10)))
        self.journal.data["runtime_proof"] = {"listeners": listeners, "guest": proof, "docker": info,
                                               "version": {key: version[key] for key in ("Version", "ApiVersion", "MinAPIVersion")}}
        self.journal.publish()

    def pin_host_key(self):
        known = regular(Path(self.config["paths"]["ssh_known_hosts"]))
        known_digest = digest(known)
        receipt = self.controller / "known-hosts.sha256"
        if receipt.exists():
            require(regular(receipt).read_text().strip() == known_digest, "Owned SSH host key changed")
        else:
            with receipt.open("x") as output:
                output.write(known_digest + "\n")

    def bind_artifacts(self):
        for key in ("qemu_pidfile", "serial_log", "qmp_socket"):
            path = safe(Path(self.config["paths"][key]))
            value = path.lstat()
            require((stat.S_ISSOCK(value.st_mode) if key == "qmp_socket" else stat.S_ISREG(value.st_mode)), "Unexpected VM-owned artifact type")
            require(value.st_uid == os.geteuid() and value.st_nlink == 1, "Unexpected runtime artifact ownership/link count")
            if key == "qemu_pidfile":
                require(path.read_text().strip() == str(self.vm()["process"].pid), "QEMU pidfile does not bind this child")
            self.runtime_artifacts[key] = (value.st_dev, value.st_ino)
        self.journal.data["runtime_artifact_identities"] = self.runtime_artifacts.copy()
        self.journal.publish()

    def remove_containers(self):
        require(self.guest_owned, "No guest ownership proof; do not contact/remove unknown containers")
        self.listener_proof()
        rows = self.api.request("GET", "/v1.32/containers/json?all=1")
        ids = owned_container_ids(rows, self.config["owner"]["ownership_token"], self.args.evidence_name)
        for value in ids:
            self.api.request("DELETE", "/v1.32/containers/" + value + "?force=1&v=1", expected=(204,))
        require(self.api.request("GET", "/v1.32/containers/json?all=1") == [], "Owned container absence not proved")
        return {"removed_ids": ids, "containers_absent": True}

    def smoke(self):
        self.remove_containers()
        # Pull only the public fixture image; streamed progress is bounded and never retained raw.
        response = self.api.request("POST", "/v1.32/images/create?fromImage=postgres&tag=17.6-alpine",
                                    timeout=600, maximum=16 * 1024**2, raw=True)
        for line in response.splitlines():
            if line.strip():
                item = json_bytes(line)
                require(isinstance(item, dict) and not {"error", "errorDetail"}.intersection(item), "Public PostgreSQL fixture pull failed")
        image = self.api.request("GET", "/v1.32/images/postgres:17.6-alpine/json")
        require(re.fullmatch(r"sha256:[0-9a-f]{64}", image.get("Id", "")) is not None, "Missing actual fixture image identity")
        labels = {OWNER_LABEL: self.config["owner"]["ownership_token"], BATCH_LABEL: self.args.evidence_name}
        body = {"Image": POSTGRES_IMAGE, "Env": ["POSTGRES_HOST_AUTH_METHOD=trust"], "Labels": labels,
                "ExposedPorts": {"5432/tcp": {}}, "HostConfig": {"Memory": SMOKE_MEMORY, "NanoCpus": 500000000, "PidsLimit": 128,
                "PortBindings": {"5432/tcp": [{"HostIp": "10.0.2.15", "HostPort": ""}]}}}
        created = self.api.request("POST", "/v1.32/containers/create", body, expected=(201,))
        cid = created["Id"]
        require(re.fullmatch(r"[0-9a-f]{64}", cid) is not None, "Invalid smoke container ID")
        self.journal.data["smoke_created_id"] = cid
        self.journal.publish()
        self.api.request("POST", "/v1.32/containers/" + cid + "/start", expected=(204,))
        state = self.api.request("GET", "/v1.32/containers/" + cid + "/json")
        require(state.get("Image") == image["Id"] and state.get("State", {}).get("Running") is True
                and all(state["Config"]["Labels"].get(key) == value for key, value in labels.items()), "Smoke image/ownership identity differs")
        mapping = state["NetworkSettings"]["Ports"]["5432/tcp"]
        require(len(mapping) == 1 and mapping[0]["HostIp"] == "10.0.2.15", "Unreviewed smoke port binding")
        port = int(mapping[0]["HostPort"])
        require(25000 <= port <= 25127, "Docker published outside the owned forwarding range")
        deadline = time.monotonic() + 180
        while True:
            self.listener_proof()
            try:
                sql = postgres_smoke(port, deadline)
                break
            except (OSError, Unavailable):
                time.sleep(remaining(deadline, 1))
        result = self.api.request("POST", "/v1.32/containers/" + cid + "/exec",
                                  {"AttachStdout": True, "AttachStderr": True,
                                   "Cmd": ["/bin/sh", "-c", "cat /sys/fs/cgroup/memory.max; cat /sys/fs/cgroup/cpu.max"]}, expected=(201,))
        eid = result["Id"]
        require(re.fullmatch(r"[0-9a-f]{64}", eid) is not None, "Invalid owned exec ID")
        limits = parse_exec_limits(self.api.request("POST", "/v1.32/exec/" + eid + "/start", {"Detach": False, "Tty": False}, raw=True))
        require(self.api.request("GET", "/v1.32/exec/" + eid + "/json").get("ExitCode") == 0, "Resource proof exec failed")
        self.journal.data["published_port_smoke"] = {"image": POSTGRES_IMAGE, "image_id": image["Id"],
                                                     "repository_digests": image.get("RepoDigests", []), "port": port,
                                                     "disposable_auth_mode": "trust; no password created or recorded", "sql": sql, "limits": limits}
        self.remove_containers()
        self.journal.publish()

    def run_driver(self):
        require(shutil.disk_usage(self.root).free >= MIN_FREE_BYTES, "Less than8GiB free before Gradle")
        inventory.validate_manifest(self.root, Path(self.args.manifest), self.args.tasks, self.args.manifest_sha256)
        env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR") if key in os.environ}
        env.update(self.config["test_environment"])
        command = [sys.executable, "-B", str(self.root / DRIVER), "--dependency-mode", self.args.dependency_mode,
                   "--manifest-sha256", self.args.manifest_sha256, self.args.manifest, self.args.evidence_name, *self.args.tasks]
        owned = self.scope.spawn("driver", command, env)
        require(self.scope.wait(owned, 2700) == 0, "Driver validation failed")
        self.journal.data["driver_reconciliation"] = self.reconcile_driver()

    def reconcile_driver(self):
        result_path = regular(self.root / "review/working" / self.args.evidence_name / "result.json")
        result = load_json(result_path)
        require(result.get("runner_status") == "PASS" and result.get("source_manifest_sha256") == self.args.manifest_sha256,
                "Driver result does not prove the pinned successful batch")
        outputs = [driver.BUILD_HOME + "/backend-build", "kira-backend/build", "kira-backend/buildSrc/build"]
        require(result.get("output_paths") == outputs and result.get("outputs_absent") is True
                and result.get("capture_complete") is True and result.get("frozen_inputs_preserved") is True
                and result.get("failures") == [], "Inner output/capture/input proof is incomplete")
        require(all(not safe(self.root / path).exists() for path in outputs), "Driver generated output residue remains")
        retained = []
        for category in ("retained_reports", "retained_bytecode", "retained_test_bytecode"):
            require(isinstance(result.get(category), list), "Missing retained inner evidence inventory")
            for entry in result[category]:
                relative = Path(entry["path"])
                require(not relative.is_absolute() and ".." not in relative.parts and relative.parts
                        and relative.parts[0] in {"reports", "bytecode", "test-bytecode"}, "Escaping inner evidence path")
                require(entry["path"] not in retained, "Duplicate inner evidence path")
                require(digest(result_path.parent / relative) == entry["sha256"], "Retained inner evidence changed")
                retained.append(entry["path"])
        actual_digest = digest(result_path)
        previous = self.journal.data.get("driver_result_sha256")
        require(previous is None or previous == actual_digest, "Inner result changed after validation")
        self.journal.data["driver_result_sha256"] = actual_digest
        return {"result_sha256": actual_digest, "retained_artifacts_verified": len(retained),
                "output_paths": outputs, "outputs_independently_absent": True}

    def stop_driver_helpers(self):
        receipts, failures = [], []
        for owned in reversed(self.scope.handles):
            if owned["entry"]["name"] == "qemu":
                continue
            try:
                receipts.append(self.scope.stop(owned, grace=480 if owned["entry"]["name"] == "driver" else 15))
            except BaseException as error:
                failures.append(type(error).__name__)
        require(not failures, "Some owned driver/helper joins failed")
        return receipts

    def stop_guest(self):
        require(self.guest_owned, "Guest service ownership was not proved")
        script = GUEST_STOP.replace("OWNER_JSON", repr(self.config["owner"]))
        return validate_guest_stop(self.ssh("stop-owned-docker", script, timeout=150, cleanup=True))

    def qmp_powerdown(self):
        path = safe(Path(self.config["paths"]["qmp_socket"]))
        require(path.exists() and stat.S_ISSOCK(path.lstat().st_mode), "No owned QMP socket")
        require(self.runtime_artifacts.get("qmp_socket") == (path.lstat().st_dev, path.lstat().st_ino), "Unbound/replaced QMP socket")
        self.listener_proof()
        deadline = time.monotonic() + 10
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(remaining(deadline))
            stream.connect(str(path))
            peer_pid, peer_uid, _ = struct.unpack("3i", stream.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            require(peer_pid == self.vm()["process"].pid and peer_uid == os.geteuid(), "QMP peer is not this owned VM")
            self.listener_proof()
            pending = b""
            def read_reply():
                nonlocal pending
                while b"\n" not in pending:
                    stream.settimeout(remaining(deadline))
                    chunk = stream.recv(min(4096, 65537 - len(pending)))
                    require(chunk and len(pending) + len(chunk) <= 65536, "Missing/oversized QMP reply")
                    pending += chunk
                line, pending = pending.split(b"\n", 1)
                remaining(deadline)
                return json_bytes(line)
            require("QMP" in read_reply(), "Invalid QMP greeting")
            for command in ("qmp_capabilities", "system_powerdown"):
                stream.settimeout(remaining(deadline))
                stream.sendall((json.dumps({"execute": command, "id": command}) + "\n").encode())
                for _ in range(16):
                    reply = read_reply()
                    if reply.get("id") == command:
                        require("return" in reply and "error" not in reply, "QMP command failed")
                        break
                else:
                    raise Refused("Missing QMP reply")
        return {"commands": ["qmp_capabilities", "system_powerdown"]}

    def stop_vm(self):
        owned = self.vm()
        proof = {"spawned": owned is not None, "pid": None if owned is None else owned["process"].pid,
                 "joined": False, "identity_bound": False, "process_absent": None,
                 "exit_code": None, "exit_code_known": False, "exit_code_type": "unobserved"}
        # Current-operation diagnostics survive an abnormal exit or an identity-read failure.
        # Never reuse a previous stop's successful receipt after a new failed/unknown stop.
        self.journal.data["qemu_termination"] = proof
        if owned is None:
            proof["never_spawned"] = True
            return proof
        process = owned["process"]
        proof["identity_bound"] = owned["identity"] is not None
        try:
            try:
                if process.poll() is None:
                    try:
                        self.journal.data["qmp_shutdown"] = self.qmp_powerdown()
                        process.wait(timeout=90)
                    except BaseException as error:
                        self.journal.failure("graceful-qemu-shutdown", error)
            finally:
                # Includes already-exited QEMU: join the owned handle without numeric signalling.
                proof["joined"] = self.scope.stop(owned, grace=20).get("joined") is True
        finally:
            code = process.returncode
            proof.update(exit_code=code if type(code) is int else None,
                         exit_code_known=type(code) is int, exit_code_type=type(code).__name__)
        current = process_identity(process.pid)
        if proof["identity_bound"]:
            proof["process_absent"] = not same_process(owned["identity"], current)
        require(successful_vm_termination(proof), "Owned VM exit was abnormal/unknown or absence was not proved")
        return proof

    def postflight(self):
        require_unused_ports(self.config, tcp_listeners())
        for key in ("serial_log", "qemu_pidfile", "qmp_socket"):
            require(not safe(Path(self.config["paths"][key])).exists(), "Runtime artifact absence was not proved")
        for owned in self.scope.handles:
            require(owned["process"].poll() is not None, "An owned command remains live")
        require(self.reaper.track() == [], "Owned child/adoptee process absence not proved")
        require(digest(self.root / CONFIG) == self.args.launch_config_sha256
                and digest(self.root / CONFIG_REVIEW) == self.args.launch_config_sha256, "Postflight launch config drift")
        for filename, expected in self.config["immutable_hashes"].items():
            require(digest(Path(filename)) == expected, "Postflight immutable runtime input drift")
        verify_tool_tree(self.config)
        inventory.validate_manifest(self.root, Path(self.args.manifest), self.args.tasks, self.args.manifest_sha256)
        self.reconcile_driver()
        self.journal.data["overlay_after"] = overlay_info(self.config)
        return {"owned_processes_absent": True, "all_forwarded_listeners_absent": True,
                "runtime_inputs_preserved": True, "frozen_source_inputs_preserved": True}

    def descendant_barrier(self):
        self.journal.data["descendant_disposal"] = {"absent": False, "barrier_returned_normally": False}
        try:
            proof = self.reaper.barrier()
        except BaseException as error:
            # Never borrow last_receipt (possibly an older operation) as authority.
            self.journal.data["descendant_disposal"]["exception_type"] = type(error).__name__
            if isinstance(error, owned_processes.OwnershipError):
                self.journal.data["descendant_disposal"]["diagnostic_only"] = error.receipt
            raise
        self.journal.data["descendant_disposal"] = {**proof, "barrier_returned_normally": True}
        require(proof.get("absent") is True and proof.get("forced") is False and proof.get("errors") == [],
                "Owned descendants needed forced/uncertain disposal")
        return proof

    def retain_artifacts(self):
        # VM must be gone before reading/unlinking only the artifacts bound to this launch.
        require(self.vm() is None or self.vm()["process"].poll() is not None, "Cannot collect/retire live runtime artifacts")
        # A prior thrown barrier plus one later empty census is not capture authority.
        # Forced-but-proven absence may preserve evidence, but remains a batch failure.
        self.journal.data["artifact_descendant_disposal"] = {"absent": False, "barrier_returned_normally": False}
        proof = self.reaper.barrier()
        require(proof.get("absent") is True and proof.get("errors") == [],
                "Cannot collect/retire artifacts without current descendant absence")
        self.journal.data["artifact_descendant_disposal"] = {**proof, "barrier_returned_normally": True}
        retained = []
        for key in ("serial_log", "qemu_pidfile", "qmp_socket"):
            source = safe(Path(self.config["paths"][key]))
            if not source.exists():
                continue
            value = source.lstat()
            require(self.runtime_artifacts.get(key) == (value.st_dev, value.st_ino), "Unbound runtime artifact: retain, never delete")
            if key != "qmp_socket":
                require(stat.S_ISREG(value.st_mode) and value.st_size <= 64 * 1024**2, "Oversized/nonregular runtime evidence")
                target = safe(self.journal.folder / (key + ".retained"))
                with source.open("rb") as original, target.open("xb") as output:
                    shutil.copyfileobj(original, output)
                require(digest(target) == digest(source), "Runtime evidence copy drift")
                retained.append({"path": target.name, "sha256": digest(target)})
            else:
                require(stat.S_ISSOCK(value.st_mode), "Changed QMP artifact type")
            require((source.lstat().st_dev, source.lstat().st_ino) == self.runtime_artifacts[key], "Runtime artifact ownership changed")
            source.unlink()  # Only this launch's inode, after VM exit and successful evidence capture.
        return retained


def run_batch(runtime):
    """Orchestration seam used by no-process controls; every cleanup action is independent."""
    journal = runtime.journal
    completed = False
    try:
        runtime.acquire()
        runtime.launch()
        runtime.ready()
        runtime.smoke()
        runtime.run_driver()
        completed = True
    except BaseException as error:
        journal.failure("batch", error)
    finally:
        # Publication, container census or guest stop failure cannot skip VM/descendant teardown.
        journal.attempt("owned-driver-helpers", runtime.stop_driver_helpers)
        journal.attempt("owned-containers", runtime.remove_containers)
        journal.attempt("guest-service-absence", runtime.stop_guest)
        journal.attempt("owned-vm-absence", runtime.stop_vm)
        if runtime.reaper.active:
            journal.attempt("owned-descendant-reaping", runtime.descendant_barrier)
        journal.attempt("runtime-artifact-capture", runtime.retain_artifacts)
        journal.attempt("postflight", runtime.postflight)
        if runtime.reaper.active:
            # Postflight's source verifier can launch its own bounded Git helpers.
            journal.attempt("final-owned-descendant-reaping", runtime.descendant_barrier)
        journal.attempt("restore-subreaper", runtime.reaper.restore)
    proof_keys = {"runtime_proof", "published_port_smoke", "driver_result_sha256", "driver_reconciliation", "descendant_disposal"}
    success = (completed and proof_keys <= journal.data.keys()
               and successful_vm_termination(journal.data.get("qemu_termination")) and not runtime.reaper.active
               and not getattr(runtime.reaper, "restoration_pending", False)
               and not journal.data["failures"] and not journal.publication_failed)
    journal.data.update(status="PASS" if success else "FAIL", finished_at=now(), runtime_authority="UNKNOWN", W03="INCOMPLETE")
    try:
        journal.publish()
    except BaseException as error:
        journal.failure("final-publication", error)
        journal.data["status"] = "FAIL"
        success = False
        try:
            journal.publish()
        except BaseException as publication:
            journal.failure("final-failure-publication", publication)
    return 0 if success else 1


@contextlib.contextmanager
def owned_controller(root, config, evidence_name):
    controller = safe(root / ".kira-runtime-tools/vm/controller")
    marker = {"controller": CONTROLLER, "runtime_owner": config["owner"]}
    if not controller.exists():
        controller.mkdir(mode=0o700)
        with (controller / "owner.json").open("x") as output:
            json.dump(marker, output)
    require(controller.is_dir() and controller.stat().st_uid == os.geteuid()
            and stat.S_IMODE(controller.stat().st_mode) == 0o700
            and load_json(controller / "owner.json") == marker, "Unowned controller directory")
    lock_path = safe(controller / "batch.lock")
    if lock_path.exists():
        regular(lock_path)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        known = safe(Path(config["paths"]["ssh_known_hosts"]))
        known_pin = safe(controller / "known-hosts.sha256")
        if known.exists() or known_pin.exists():
            require(known.exists() and known_pin.exists() and regular(known_pin).read_text().strip() == digest(known), "Unowned/changed SSH host-key receipt")
        for relative in (evidence_name, evidence_name + "-runtime"):
            path = safe(root / "review/working" / relative)
            require(not path.exists(), "Never overwrite prior validation/runtime evidence")
        folder = safe(root / "review/working" / (evidence_name + "-runtime"))
        folder.mkdir(mode=0o700)
        yield controller, folder


@contextlib.contextmanager
def signal_scope():
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    seen = []

    def interrupt(signum, _frame):
        seen.append(signum)
        if len(seen) == 1:
            raise KeyboardInterrupt()
        # A second interruption cannot skip the bounded finally teardown.

    try:
        for sig in previous:
            signal.signal(sig, interrupt)
        yield seen
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--execute-reviewed", action="store_true")
    parser.add_argument("--launch-config-sha256", required=True)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--dependency-mode", choices=("online", "offline"), default="online")
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("evidence_name", nargs="?")
    parser.add_argument("tasks", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    config, static = configuration(ROOT, args.launch_config_sha256)
    if args.prepare_only:
        require(not args.manifest and not args.tasks and not args.evidence_name, "Preparation does not accept execution arguments")
        print(json.dumps({"status": "STATIC_PREPARATION_ONLY_RUNTIME_UNVERIFIED", "no_process_or_service_started": True,
                          "not_execution_authorization": True, **static}, indent=2))
        return 0
    require(args.manifest and args.manifest_sha256 and args.evidence_name, "Execution requires explicit frozen inputs/evidence name")
    require(re.fullmatch(r"app-29-[A-Za-z0-9_-]{1,100}", args.evidence_name) is not None, "Invalid fresh evidence name")
    driver.require_tasks(args.tasks)
    manifest = inventory.validate_manifest(ROOT, Path(args.manifest), args.tasks, args.manifest_sha256)
    require(manifest["approved_inputs"].get(CONFIG_REVIEW) == args.launch_config_sha256 and NOTE in manifest["approved_inputs"],
            "Runtime configuration/implementation note was not included in the frozen approved inputs")
    require({THIS_TOOL, CONTROL_TESTS, DRIVER, DRIVER_TESTS, OWNERSHIP_TOOL, OWNERSHIP_TESTS} <= manifest["validation_tooling"].keys(),
            "Missing wrapper/driver/shared ownership/control tooling pins")
    with owned_controller(ROOT, config, args.evidence_name) as (controller, folder):
        with signal_scope() as interruptions:
            journal = Journal(folder, {"source_manifest": args.manifest, "source_manifest_sha256": args.manifest_sha256,
                                       "configuration": static, "runtime_owner": config["owner"], "signal_receipts": interruptions})
            runtime = Runtime(ROOT, config, args, journal, controller)
            code = run_batch(runtime)
            print(json.dumps({"status": journal.data["status"], "runtime_evidence": str(folder.relative_to(ROOT)),
                              "failure_stages": [row["stage"] for row in journal.data["failures"]]}), flush=True)
            return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refused, owned_processes.OwnershipError, OSError, ValueError, KeyError, TypeError) as failure:
        # Do not echo arbitrary guest/API/config exception bodies.
        print("RUNTIME REFUSED: " + type(failure).__name__, file=sys.stderr)
        raise SystemExit(1)
