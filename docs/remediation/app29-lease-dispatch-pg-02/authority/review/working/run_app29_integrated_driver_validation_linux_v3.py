#!/usr/bin/env python3
"""Linux successor: frozen inputs, private Gradle, stop/preserve/scoped-clean/stop.

Private evidence tooling, not release acceptance. Historical macOS scripts are immutable.
The independently owned PostgreSQL wrapper proves runtime bounds and owns its entire lifecycle.
"""

import argparse
import datetime
import fcntl
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET

from app29_linux_owned_processes import OwnedChildren
import freeze_app29_integrated_driver_v3 as inventory


ROOT = Path(__file__).resolve().parents[2]
SOURCE_INPUTS = "review/working/app-29-w01-local-dependencies-20260905"
DEPENDENCY_MANIFEST_SHA256 = "c67fcc5fe64a9a795373c4683c7c1edd6407146e3cd07609fa7018a8a98db79a"
DEPENDENCY_FILE_COUNT = 18
INIT = "review/working/app-29-w01-local-dependencies.init.gradle"
BUILD_HOME = ".kira-validation/backend-linux"
OWNER = "kira-app29-linux-validation-v1"
MIN_FREE_BYTES = 8 * 1024**3
ALLOWED_TASKS = {"test", "testClasses", "classes", "ktlintCheck", "detekt", "check"}
OWNERSHIP_TOOLING = (
    "review/working/app29_linux_owned_processes.py",
    "review/working/test_app29_linux_owned_processes.py",
    "review/working/test_app29_linux_validation_runner.py",
)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def safe_path(root, relative):
    """Reject links/special parents, INCLUDING the root and all its absolute ancestors."""
    root, value = Path(root), Path(relative)
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Expected an absolute managed root")
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise ValueError("Expected a workspace-relative path")
    result = root / value
    current = Path(result.anchor)
    for part in result.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("Refusing symlink in managed path")
        if current.exists() and current != result and not current.is_dir():
            raise ValueError("Non-directory managed parent")
    return result


def regular(path):
    checked = safe_path(path.parent, path.name)
    if not stat.S_ISREG(checked.stat().st_mode):
        raise ValueError("Expected a regular managed file")
    return checked


def require_owned_tooling(manifest):
    """The caller cannot omit newly shared executable/negative-control bytes from a freeze."""
    pins = manifest.get("validation_tooling", {})
    for relative in OWNERSHIP_TOOLING:
        if relative not in pins or pins[relative] != digest(regular(safe_path(ROOT, relative))):
            raise ValueError("Missing/changed frozen Linux ownership tooling: " + relative)


def require_tasks(tasks):
    if not tasks:
        raise ValueError("Explicit frozen validation tasks are required")
    index, has_selectors = 0, False
    while index < len(tasks):
        item = tasks[index]
        if item == "--tests":
            index += 1
            has_selectors = True
            if index == len(tasks) or not re.fullmatch(r"[A-Za-z0-9_.*$]+", tasks[index]):
                raise ValueError("Expected a bounded test-class selector")
        elif item not in ALLOWED_TASKS and item != "--continue":
            raise ValueError("Not an authorized local validation task/option: " + item)
        index += 1
    if not any(task in ALLOWED_TASKS for task in tasks):
        raise ValueError("At least one validation task is required")
    if has_selectors and not {"test", "check"}.intersection(tasks):
        raise ValueError("A test selector requires test execution")


def dependency_inputs(root, home, *, provision=False):
    """Independent immutable pin, exact inventory, no overwrite, verified source AND destination."""
    source = safe_path(root, SOURCE_INPUTS)
    manifest = regular(safe_path(source, "local-inputs.sha256"))
    contents = manifest.read_bytes()
    if hashlib.sha256(contents).hexdigest() != DEPENDENCY_MANIFEST_SHA256:
        raise ValueError("Retained dependency manifest differs from its independent historical pin")
    rows, seen = [], set()
    for line in contents.decode("utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        if not re.fullmatch(r"[0-9a-f]{64}", expected) or relative in seen:
            raise ValueError("Invalid/duplicate retained dependency entry")
        seen.add(relative)
        original = regular(safe_path(source, "repository/" + relative))
        target = safe_path(home, "repository/" + relative)
        if digest(original) != expected:
            raise ValueError("Retained dependency input differs: " + relative)
        if target.exists() and digest(regular(target)) != expected:
            raise ValueError("Existing isolated dependency differs: " + relative)
        if not provision and not target.exists():
            raise ValueError("Staged dependency input missing: " + relative)
        rows.append((original, target, expected, relative))
    if len(rows) != DEPENDENCY_FILE_COUNT:
        raise ValueError("Retained dependency inventory differs")
    target_manifest = safe_path(home, "local-inputs.sha256")
    if target_manifest.exists() and regular(target_manifest).read_bytes() != contents:
        raise ValueError("Existing dependency manifest differs")
    if not provision and not target_manifest.exists():
        raise ValueError("Staged dependency manifest missing")
    if provision:
        for original, target, _, _ in rows:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                regular(original)
                safe_path(home, str(target.relative_to(home)))
                with target.open("xb") as output, original.open("rb") as source_file:
                    shutil.copyfileobj(source_file, output)
        if not target_manifest.exists():
            with target_manifest.open("xb") as output:
                output.write(contents)
    # Recheck rather than trusting either a copy or a self-reported replacement manifest.
    if digest(regular(manifest)) != DEPENDENCY_MANIFEST_SHA256:
        raise ValueError("Retained dependency manifest changed during staging")
    if digest(regular(target_manifest)) != DEPENDENCY_MANIFEST_SHA256:
        raise ValueError("Staged dependency manifest differs")
    for original, target, expected, _ in rows:
        if digest(regular(original)) != expected or digest(regular(target)) != expected:
            raise ValueError("Dependency bytes changed during staging/validation")
    return {"manifest_sha256": DEPENDENCY_MANIFEST_SHA256, "files_verified": len(rows),
            "artifact_hashes": {relative: expected for _, _, expected, relative in rows}}


def provision_inputs(root, home):
    return dependency_inputs(root, home, provision=True)


def private_daemon_pids(home):
    """Private log identities only. PID reuse is conservative, never a PID-directed kill."""
    daemons, live = safe_path(home, "gradle-home/daemon"), []
    if daemons.is_dir():
        for log in daemons.glob("*/daemon-*.out.log"):
            regular(log)
            match = re.fullmatch(r"daemon-([0-9]+)\.out\.log", log.name)
            if not match:
                continue
            pid = int(match.group(1))
            try:
                command = Path("/proc", str(pid), "cmdline").read_bytes().split(b"\0")
            except FileNotFoundError:
                continue
            if b"org.gradle.launcher.daemon.bootstrap.GradleDaemon" in command:
                live.append(pid)
    return sorted(set(live))


def process_group_members(group):
    """Only process stat identities, no environments/credentials. A census error is not absence."""
    result = []
    for path in Path("/proc").iterdir():
        if not path.name.isdecimal():
            continue
        try:
            fields = (path / "stat").read_text().rsplit(") ", 1)[1].split()
        except FileNotFoundError:
            continue
        if int(fields[2]) == group:
            if int(fields[3]) != group:
                raise ValueError("Owned process group no longer has its private session")
            result.append(int(path.name))
    return sorted(result)


def build_environment(root, home):
    java = Path(shutil.which("java") or "").resolve()
    if not java.is_file() or java.parent.name != "bin":
        raise ValueError("A real Java 21 installation is required")
    java_home = java.parent.parent
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR") if key in os.environ}
    env.update(JAVA_HOME=str(java_home), GRADLE_USER_HOME=str(home / "gradle-home"),
               W01_RUN=str(home), TZ="UTC")
    for key in ("DOCKER_HOST", "TESTCONTAINERS_HOST_OVERRIDE", "TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE"):
        if key in os.environ:
            env[key] = os.environ[key]
    version = subprocess.check_output([str(java), "-version"], env=env, stderr=subprocess.STDOUT,
                                      text=True, timeout=30)
    if not re.search(r'version "21(?:\.|\")', version):
        raise ValueError("Java 21 is required; no silent toolchain substitution")
    cache = Path.home() / ".gradle/caches"
    if cache.is_dir():
        env["GRADLE_RO_DEP_CACHE"] = str(cache)
    return env, {"java_home": str(java_home), "java_version": version,
                 "java_binary_sha256": digest(java), "java_modules_sha256": digest(java_home / "lib/modules"),
                 "read_only_dependency_cache": env.get("GRADLE_RO_DEP_CACHE")}


def test_evidence(evidence, reports, tasks):
    """Require real, internally consistent Gradle JUnit cases and each frozen class selector."""
    if not {"test", "check"}.intersection(tasks):
        return {"status": "NOT_REQUESTED", "total": 0, "identities": [], "limitation": "No test execution requested"}
    paths = [row["path"] for row in reports if row["path"].startswith("reports/test-results/test/TEST-")
             and row["path"].endswith(".xml")]
    if not paths:
        raise ValueError("Tests requested but no JUnit XML retained")
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    identities, classes, suites = [], set(), set()
    for path in paths:
        source = regular(safe_path(evidence, path))
        if source.stat().st_size > 32 * 1024**2:
            raise ValueError("Unexpectedly large JUnit XML")
        # Gradle writes UTF-8. Decode before checking declarations so UTF-16/32 cannot hide a DTD.
        data = source.read_bytes().decode("utf-8-sig")
        declaration = re.match(r"\s*<\?xml\s+[^?]*encoding\s*=\s*['\"]([^'\"]+)['\"]", data, re.IGNORECASE)
        if "\x00" in data or (declaration and declaration.group(1).lower() not in {"utf-8", "utf8"}):
            raise ValueError("JUnit must be UTF-8, not an alternate encoding")
        if "<!DOCTYPE" in data.upper() or "<!ENTITY" in data.upper():
            raise ValueError("JUnit XML cannot declare external/internal entities")
        suite = ET.fromstring(data)
        name = suite.get("name", "")
        if suite.tag != "testsuite" or not re.fullmatch(r"[A-Za-z0-9_.$]+", name) or name in suites:
            raise ValueError("Unexpected/duplicate JUnit suite")
        suites.add(name)
        cases = suite.findall("testcase")
        observed = {"tests": len(cases), "failures": 0, "errors": 0, "skipped": 0}
        for case in cases:
            if case.get("classname") != name or not case.get("name"):
                raise ValueError("JUnit case identity is absent/inconsistent")
            flags = {key: case.find(tag) is not None for key, tag in
                     (("failures", "failure"), ("errors", "error"), ("skipped", "skipped"))}
            if sum(flags.values()) > 1:
                raise ValueError("JUnit case has inconsistent terminal statuses")
            for key, value in flags.items():
                observed[key] += value
            identities.append({"class": name, "name": case.get("name"),
                               "status": next((key for key, value in flags.items() if value), "passed")})
            classes.add(name)
        for key, count in observed.items():
            raw = suite.get(key, "")
            if not re.fullmatch(r"[0-9]+", raw) or int(raw) != count:
                raise ValueError("JUnit declared/observed counts differ")
            totals[key] += count
    if not totals["tests"]:
        raise ValueError("JUnit contains zero genuine test cases")
    selectors = [tasks[index + 1] for index, task in enumerate(tasks) if task == "--tests"]
    matching = {selector: sorted(name for name in classes if fnmatch.fnmatchcase(name, selector)
                                or fnmatch.fnmatchcase(name.rsplit(".", 1)[-1], selector))
                for selector in selectors}
    if any(not names for names in matching.values()):
        raise ValueError("A frozen test selector has no executed cases")
    return {"status": "PASS" if not any(totals[key] for key in ("failures", "errors", "skipped")) else "FAIL",
            "total": totals.pop("tests"), **totals, "classes": sorted(classes), "selectors": matching,
            "identities": identities, "limitation": "Discovery/counts only; full protected-baseline comparison remains required"}


class Commands:
    """Every acquired Popen handle immediately enters wait/termination protection."""

    def __init__(self, evidence, repo, env, ledger, children):
        self.evidence, self.repo, self.env, self.ledger = evidence, repo, env, ledger
        self.children = children

    def failure(self, stage, problem):
        self.ledger["failures"].append({"stage": stage, "type": type(problem).__name__})

    def attempt(self, stage, action, default=None):
        try:
            return action()
        except BaseException as problem:
            self.failure(stage, problem)
            return default

    def checkpoint(self):
        target = safe_path(self.evidence, "result.json")
        if target.exists():
            regular(target)
        target.write_text(json.dumps(self.ledger, indent=2) + "\n")

    def publish(self):
        return self.attempt("evidence-checkpoint", lambda: (self.checkpoint(), True)[1], False)

    def terminate(self, process, entry):
        entry["termination_requested"] = True
        def send(sig):
            # Full live descendant identities, including detached sessions, not a numeric PGID.
            # Every signal rechecks the anchored tree through a short-lived pidfd.
            for identity in self.children.track():
                if identity["state"] != "Z":
                    self.attempt("owned-signal", lambda: self.children.signal_owned(identity, sig))
        self.attempt("owned-term", lambda: send(signal.SIGTERM))
        try:
            entry["exit_code"] = process.wait(timeout=20)
            entry["joined"] = True
        except BaseException as problem:
            if not isinstance(problem, subprocess.TimeoutExpired):
                self.failure("owned-term-wait", problem)
            self.attempt("owned-kill", lambda: send(signal.SIGKILL))
            try:
                entry["exit_code"] = process.wait(timeout=20)
                entry["joined"] = True
            except BaseException as final:
                self.failure("owned-kill-wait", final)
                entry["joined"] = False

    def run(self, name, command, timeout=1800, *, cleanup=False):
        if not self.children.active:
            raise ValueError("An active private child scope is required before Popen")
        entry = {"name": name, "command": command, "started_at": now(), "joined": False}
        self.ledger["commands"].append(entry)
        if not self.publish() and not cleanup:
            raise OSError("Cannot publish owned command intent")
        output = None
        try:
            try:
                output = safe_path(self.evidence, name + ".log").open("x")
            except BaseException as problem:
                self.failure(name + "-log", problem)
                if not cleanup:
                    raise
            process = subprocess.Popen(command, cwd=self.repo, env=self.env,
                                       stdout=output if output is not None else subprocess.DEVNULL,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            # No fallible publication outside this immediate lifecycle try.
            try:
                entry["pid"] = process.pid
                entry["owned_descendants_at_acquisition"] = self.children.track()
                if not self.publish() and not cleanup:
                    raise OSError("Cannot publish acquired owned process")
                entry["exit_code"] = process.wait(timeout=timeout)
                entry["joined"] = True
            except BaseException as problem:
                self.failure(name, problem)
                self.terminate(process, entry)
                raise
            finally:
                entry["finished_at"] = now()
                self.publish()
        finally:
            if output is not None:
                self.attempt(name + "-log-close", output.close)
        return entry.get("exit_code")

    def groups(self):
        return {str(row["pid"]): process_group_members(row["pid"])
                for row in self.ledger["commands"] if "pid" in row}

    def record_residue(self):
        before = self.groups()
        self.ledger["owned_groups_after_gradle_stop"] = before
        if any(before.values()):
            self.failure("owned-group-residue", RuntimeError())
        # Never kill by an old numeric PGID after wait/reap. The driver-local child scope
        # proves disposal BEFORE capture/deletion; the outer wrapper remains death fallback.
        return before

    def barrier(self, stage):
        """Complete anchored quietness, not just observed Gradle logs/process groups.

        A forced-but-absent receipt permits capture but never PASS or output deletion.
        Unknown/residual/error receipts forbid capture and preserve outputs for recovery.
        """
        receipt, returned_normally = None, False
        try:
            receipt = self.children.barrier()
            returned_normally = True
        except BaseException as problem:
            self.failure(stage, problem)
            # Exception receipts are diagnostic only. Neither one nor last_receipt
            # can authorize capture/deletion after this operation failed to return.
            receipt = getattr(problem, "receipt", None)
        self.ledger["owned_descendant_barriers"].append({
            "stage": stage, "returned_normally": returned_normally, "receipt": receipt})
        known_absent = (returned_normally and isinstance(receipt, dict)
                        and receipt.get("absent") is True and receipt.get("errors") == []
                        and isinstance(receipt.get("forced"), bool))
        if not known_absent or receipt["forced"]:
            self.failure(stage + "-not-clean", RuntimeError())
        return receipt if known_absent else None


def capture_outputs(commands, build, manifest):
    evidence, ledger = commands.evidence, commands.ledger

    def capture(source, relative, key):
        regular(source)
        target = safe_path(evidence, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output, source.open("rb") as original:
            shutil.copyfileobj(original, output)
        if digest(regular(target)) != digest(regular(source)):
            raise ValueError("Evidence copy changed")
        ledger[key].append({"path": relative, "sha256": digest(target)})

    for relative in ("test-results", "reports"):
        folder = safe_path(build, relative)
        if folder.exists():
            if not folder.is_dir():
                raise ValueError("Report root is not a directory")
            for source in sorted(folder.rglob("*")):
                safe_path(build, str(source.relative_to(build)))
                if source.is_file() and source.suffix in {".xml", ".txt", ".sarif"}:
                    capture(source, "reports/" + str(source.relative_to(build)), "retained_reports")
    package = "me/manga/kira/backend/common/infrastructure/persistence/"
    for name in manifest["evidence_class_names"]:
        source = safe_path(build, "classes/kotlin/main/" + package + name + ".class")
        if source.exists():
            capture(source, "bytecode/" + source.name, "retained_bytecode")
    source = safe_path(build, "classes/kotlin/test/" + package + "PgRequireErrorHandlerTest.class")
    if source.exists():
        capture(source, "test-bytecode/" + source.name, "retained_test_bytecode")
    classes = [str(evidence / row["path"]) for row in ledger["retained_bytecode"] + ledger["retained_test_bytecode"]]
    if classes:
        commands.run("inspect-retained-bytecode", [str(Path(commands.env["JAVA_HOME"]) / "bin/javap"),
                                                  "-c", "-p", "-s", *classes], timeout=90)
    return True


def clean_outputs(outputs, ledger):
    for path in outputs:
        safe_path(ROOT, str(path.relative_to(ROOT)))
        if path.exists():
            if not path.is_dir():
                raise ValueError("Unexpected generated output type")
            shutil.rmtree(path)
            ledger["scoped_cleanup"].append(str(path.relative_to(ROOT)))


def execute_batch(args, manifest_path, manifest, home, evidence, outputs, env, java, inputs):
    repo, build = safe_path(ROOT, "kira-backend"), outputs[0]
    base = ["./gradlew", "--no-daemon", "--no-parallel", "--max-workers=1", "--no-build-cache",
            "--no-configuration-cache", "--dependency-verification=strict", "--project-cache-dir",
            str(home / "backend-project-cache"), "--console=plain",
            "-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m", "-Dorg.gradle.vfs.watch=false",
            "-PkiraUseMavenLocal=false", "-Pkotlin.compiler.execution.strategy=in-process",
            "-Pkotlin.project.persistent.dir=" + str(home / "backend-kotlin-cache"),
            "--init-script", str(ROOT / INIT)]
    if args.dependency_mode == "offline":
        base.append("--offline")
    ledger = {"started_at": now(), "source_manifest": args.manifest,
              "source_manifest_sha256": args.manifest_sha256, "scope": manifest["validation_scope"],
              "runtime_authority": "UNKNOWN", "W03": "INCOMPLETE", "platform": platform.platform(),
              "java": java, "dependency_inputs": inputs, "dependency_mode": args.dependency_mode,
              "dependency_verification_limitation": "No project verification-metadata.xml: strict flag is NOT transitive artifact-byte proof; retained local inputs, dependency locks and wrapper checksum are narrower pins",
              "gradle_user_home": env["GRADLE_USER_HOME"], "commands": [], "failures": [], "retained_reports": [],
              "retained_bytecode": [], "retained_test_bytecode": [], "minimum_free_bytes": MIN_FREE_BYTES,
              "free_bytes_before": shutil.disk_usage(ROOT).free, "scoped_cleanup": [],
              "owned_descendant_barriers": [], "child_scope_restored": False,
              "capture_complete": False, "outputs_absent": False, "frozen_inputs_preserved": False,
              "dependency_inputs_preserved": False, "private_daemon_pids_after_stop": None,
              "private_daemon_pids_after_clean": None, "owned_command_pids_absent": False,
              "owned_groups_final": None, "test_evidence": None}
    children = OwnedChildren()  # Inert until activate; tests inject a no-kernel model.
    commands = Commands(evidence, repo, env, ledger, children)
    try:
        try:
            ledger["child_scope_acquisition"] = children.activate()
            with safe_path(evidence, "input.patch").open("xb") as output:
                output.write(inventory.issue_diff(ROOT))
            ledger["diff_sha256"] = digest(evidence / "input.patch")
            commands.checkpoint()
            inventory.validate_manifest(ROOT, manifest_path, args.tasks, args.manifest_sha256)
            dependency_inputs(ROOT, home)
            commands.run("validation", base + args.tasks)
        except BaseException as problem:
            commands.failure("validation-batch", problem)
        finally:
            # Stop immediately after the batch, before report/census work. Even a report,
            # ownership or cleanup failure cannot skip the independent final owned stop.
            if children.active:
                try:
                    commands.attempt("stop-after-validation", lambda: commands.run(
                        "stop-after-validation", ["./gradlew", "--stop"], timeout=120, cleanup=True))
                    quiet = commands.barrier("before-capture")
                    ledger["private_daemon_pids_after_stop"] = commands.attempt(
                        "daemon-census-after-stop", lambda: private_daemon_pids(home))
                    groups = commands.attempt("owned-group-census", commands.record_residue)
                    if quiet:
                        ledger["capture_complete"] = commands.attempt(
                            "capture", lambda: capture_outputs(commands, build, manifest), False)
                    # javap/capture can launch another child or fail partway. Prove quietness
                    # again before any deletion, including on its exceptional paths.
                    delete_quiet = commands.barrier("before-output-deletion")
                    if (ledger["capture_complete"] and quiet and delete_quiet
                            and quiet["forced"] is False and delete_quiet["forced"] is False
                            and ledger["private_daemon_pids_after_stop"] == []
                            and groups is not None and not any(groups.values())):
                        commands.attempt("scoped-output-cleanup", lambda: clean_outputs(outputs, ledger))
                    else:
                        ledger["outputs_preserved_for_recovery"] = True
                finally:
                    commands.attempt("stop-after-clean", lambda: commands.run(
                        "stop-after-clean", ["./gradlew", "--stop"], timeout=120, cleanup=True))
            else:
                ledger["outputs_preserved_for_recovery"] = True
        if children.active:
            commands.barrier("after-final-stop")
            ledger["private_daemon_pids_after_clean"] = commands.attempt(
                "daemon-census-after-clean", lambda: private_daemon_pids(home))
            ledger["owned_groups_after_clean"] = commands.attempt("owned-group-postflight", commands.groups)
            ledger["frozen_inputs_preserved"] = commands.attempt("frozen-input-postflight", lambda: (
                inventory.validate_manifest(ROOT, manifest_path, args.tasks, args.manifest_sha256), True)[1], False)
            ledger["dependency_inputs_preserved"] = commands.attempt("dependency-postflight", lambda: (
                dependency_inputs(ROOT, home), True)[1], False)
            commands.attempt("git-diff-check", lambda: commands.run("git-diff-check", ["git", "diff", "--check"], timeout=60))
            commands.attempt("jps-after", lambda: commands.run("jps-after", [str(Path(env["JAVA_HOME"]) / "bin/jps"), "-l"], timeout=30))
            commands.barrier("after-postflight-commands")
            ledger["owned_command_pids_absent"] = commands.attempt("owned-pid-postflight", lambda: all(
                not Path("/proc", str(row["pid"])).exists() for row in ledger["commands"] if "pid" in row), False)
            ledger["owned_groups_final"] = commands.attempt("owned-group-final", commands.groups)
            ledger["test_evidence"] = commands.attempt(
                "test-evidence", lambda: test_evidence(evidence, ledger["retained_reports"], args.tasks))
            ledger["free_bytes_after"] = commands.attempt("free-space-postflight", lambda: shutil.disk_usage(ROOT).free)
    except BaseException as problem:
        commands.failure("orchestration", problem)
    finally:
        # The scope is restored before computing/publishing PASS. This fallback also covers
        # partial activation and exceptional paths outside the normal stop/capture flow.
        try:
            if children.active:
                commands.barrier("unconditional-final-barrier")
        finally:
            restored = commands.attempt("restore-child-scope", children.restore)
            ledger["child_scope_restore"] = restored
            ledger["child_scope_restored"] = restored is not None and not children.active
    ledger["outputs_absent"] = commands.attempt("output-absence", lambda: all(
        not safe_path(ROOT, str(path.relative_to(ROOT))).exists() for path in outputs), False)
    ledger["output_paths"] = [str(path.relative_to(ROOT)) for path in outputs]
    ledger["finished_at"] = now()
    required_main = len(manifest["evidence_class_names"]) if {"test", "check", "testClasses", "classes"}.intersection(args.tasks) else 0
    required_test = 1 if {"test", "check", "testClasses"}.intersection(args.tasks) else 0
    paths = [row["path"] for row in ledger["retained_reports"]]
    ledger["static_report_coverage"] = {
        tool: any(path.startswith("reports/reports/" + tool + "/") or path == "reports/reports/" + tool + ".xml" for path in paths)
        for tool, task in (("ktlint", "ktlintCheck"), ("detekt", "detekt")) if task in args.tasks or "check" in args.tasks}
    success = (not ledger["failures"] and all(row.get("exit_code") == 0 and row.get("joined") for row in ledger["commands"])
               and ledger["child_scope_restored"] and len(ledger["owned_descendant_barriers"]) == 5
               and all(row["returned_normally"] and isinstance(row["receipt"], dict)
                       and row["receipt"].get("absent") is True and row["receipt"].get("forced") is False
                       and row["receipt"].get("errors") == [] for row in ledger["owned_descendant_barriers"])
               and ledger["outputs_absent"] and ledger["frozen_inputs_preserved"] and ledger["dependency_inputs_preserved"]
               and ledger["private_daemon_pids_after_stop"] == [] and ledger["private_daemon_pids_after_clean"] == []
               and ledger["owned_command_pids_absent"] and ledger["owned_groups_final"] is not None
               and not any(ledger["owned_groups_final"].values()) and ledger["capture_complete"]
               and len(ledger["retained_bytecode"]) == required_main and len(ledger["retained_test_bytecode"]) == required_test
               and ledger["test_evidence"] is not None and ledger["test_evidence"]["status"] in {"PASS", "NOT_REQUESTED"}
               and all(ledger["static_report_coverage"].values()))
    ledger["runner_status"] = "PASS" if success else "FAIL"
    if not commands.publish():
        success = False
        ledger["runner_status"] = "FAIL"
        commands.publish()
    print(json.dumps({"runner_status": "PASS" if success else "FAIL", "evidence": str(evidence.relative_to(ROOT)),
                      "outputs_absent": ledger["outputs_absent"], "frozen_inputs_preserved": ledger["frozen_inputs_preserved"]}), flush=True)
    return 0 if success else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependency-mode", choices=("online", "offline"), default="online")
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("manifest")
    parser.add_argument("evidence_name")
    parser.add_argument("tasks", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if platform.system() != "Linux":
        raise ValueError("This successor is specifically the Linux execution profile")
    require_tasks(args.tasks)
    if not re.fullmatch(r"app-29-[A-Za-z0-9_-]+", args.evidence_name):
        raise ValueError("Use a fresh app-29-* evidence directory")
    if not re.fullmatch(r"[0-9a-f]{64}", args.manifest_sha256):
        raise ValueError("The caller must pin the frozen manifest digest")
    manifest_path = safe_path(ROOT, args.manifest)
    manifest = inventory.validate_manifest(ROOT, manifest_path, args.tasks, args.manifest_sha256)
    require_owned_tooling(manifest)
    evidence = safe_path(ROOT, "review/working/" + args.evidence_name)
    if evidence.exists():
        raise ValueError("Never overwrite prior evidence")
    if shutil.disk_usage(ROOT).free < MIN_FREE_BYTES:
        raise ValueError("Require at least 8 GiB free before any batch")
    home = safe_path(ROOT, BUILD_HOME)
    home.parent.mkdir(mode=0o700, exist_ok=True)
    if not home.exists():
        home.mkdir(mode=0o700)
        with safe_path(home, "OWNER").open("x") as output:
            output.write(OWNER + "\n")
    if regular(safe_path(home, "OWNER")).read_text() != OWNER + "\n":
        raise ValueError("Unowned validation directory")
    with safe_path(home, "batch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        outputs = (safe_path(home, "backend-build"), safe_path(ROOT, "kira-backend/build"),
                   safe_path(ROOT, "kira-backend/buildSrc/build"))
        if any(path.exists() for path in outputs):
            raise ValueError("Refusing to overwrite or clean pre-existing generated outputs")
        if private_daemon_pids(home):
            raise ValueError("A private Gradle daemon predates this batch; reconcile ownership first")
        inputs = provision_inputs(ROOT, home)
        env, java = build_environment(ROOT, home)
        evidence.mkdir(mode=0o700)
        previous_handler = signal.getsignal(signal.SIGTERM)
        def interrupted(_signum, _frame):
            raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM, interrupted)
        try:
            return execute_batch(args, manifest_path, manifest, home, evidence, outputs, env, java, inputs)
        finally:
            signal.signal(signal.SIGTERM, previous_handler)


if __name__ == "__main__":
    sys.exit(main())
