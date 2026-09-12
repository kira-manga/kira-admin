#!/usr/bin/env python3
"""App29 v3 Backend-batch inventory/preflight. Import and default CLI mode are read-only.

Historical manifests/tools are inputs, never rewritten. Only explicit --freeze writes a
fresh candidate; it does not execute Gradle, Git mutations, services, or network commands.
The Linux runner must call validate_manifest before execution and retain issue_diff(root).
Unrelated workspace progress is documentary only, never a live Backend execution gate.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Callable


class InventoryError(RuntimeError):
    """Fail-closed inventory, continuity, or preflight error."""


REPOSITORIES = ("Kira manga", "kira-backend", "kira-admin", "kira-source-engine", "kira-web")
INTEGRATION_BRANCH = "remediation/production-readiness-2026-09-04"
ISSUE_DIFF_BASE = "c8bdff9a8acebb7c8e8ce40c65b8c7315ef9c014"
SEED_MANIFEST = "review/working/app-29-w03-integrated-driver-development-07/manifest.json"
SEED_SHA256 = "3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a"
TIMER_MANIFEST = "review/working/app-29-w03-d1-timer-a-02/manifest.json"
TIMER_SHA256 = "e955789a8342a21c224f216147bad9190161a4c0df5d36b977622320154917f2"
CHECKPOINT_LEDGER = "kira-admin/docs/remediation/checkpoint-2026-09-08/repository-checkpoint.json"
CHECKPOINT_LEDGER_SHA256 = "0b80c2e78ac1ee2a5a4287c8749cbdef6f9c7c6dade627cca756a128c5181d54"
TOOL_PATH = "review/working/freeze_app29_integrated_driver_v3.py"
REQUIRED_TOOLING = (
    TOOL_PATH,
    "review/working/test_freeze_app29_integrated_driver_v3.py",
    "review/working/run_app29_integrated_driver_validation_linux_v3.py",
    "review/working/run_app29_integrated_postgres_validation_linux.py",
    "review/working/app-29-w01-local-dependencies.init.gradle",
)
INVENTORY_NOTE = "review/remediation/app-29-w03-development08-inventory-tool.md"
ADAPTATION_NOTE = "review/remediation/app-29-development11-snapshot-adaptation-advice.md"
BATCH_IDENTITY_FIELDS = ("repositories", "integration_refs", "integration_ref_names", "integration_ref_aliases")
WORKSPACE_CONTEXT = {
    "authority": "DOCUMENTARY_PRIMARY_REPORT_ONLY_NOT_LIVE_REF_VALIDATION",
    "source": "review/working/campaign-resume-20260908-linux-01/status-reconciliation-21/result.json",
    "reported_at": "2026-09-09T08:33:08.231149+00:00",
    "kira-admin": {
        "reported_issue_branch": "remediation/admin-5-featured-order",
        "reported_issue_commit": "6711113675768797d1f40c5ac4dd47a43e368183",
        "reported_integration_branch": INTEGRATION_BRANCH,
        "reported_integration_commit": "4f43288e8fd578418f45ec365dd989a8ab3f02d4",
        "reported_tested_tree": "eb848a68e961724ad7ec3ec2beb61bf315629101",
        "validation_reference": "review/working/admin-5-final-verification/",
        "remote_verification": "PRIMARY_REPORTED_TRUE_NOT_QUERIED_BY_THIS_TOOL",
        "checked_out_head": "UNOBSERVED", "checked_out_branch": "UNOBSERVED",
        "local_integration_ref": "UNOBSERVED", "origin_tracking_integration_ref": "UNOBSERVED",
    },
    "kira-web": {"live_refs": "UNOBSERVED", "backend_batch_input": False},
    "other_workspace_refs": "UNOBSERVED_NOT_BACKEND_BATCH_GATES",
}
DIFF_OPTIONS = (
    "diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-renames",
    "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--unified=3",
    "--inter-hunk-context=0", "--diff-algorithm=myers", "--no-indent-heuristic", "--ignore-submodules=none",
)
GitReader = Callable[..., bytes]


@dataclass(frozen=True)
class EvidenceSpec:
    """Fixed production pins; alternate instances are only for isolated synthetic tests."""

    seed: str = SEED_MANIFEST
    seed_sha256: str = SEED_SHA256
    seed_count: int = 348
    timer: str = TIMER_MANIFEST
    timer_sha256: str = TIMER_SHA256
    issue_base: str = ISSUE_DIFF_BASE
    ledger: str = CHECKPOINT_LEDGER
    ledger_sha256: str = CHECKPOINT_LEDGER_SHA256
    tooling: tuple[str, ...] = REQUIRED_TOOLING
    required_inputs: tuple[str, ...] = (INVENTORY_NOTE, ADAPTATION_NOTE)


SPEC = EvidenceSpec()


@dataclass
class Candidate:
    fields: dict
    source_bytes: dict[str, bytes]
    diff_bytes: bytes
    missing_tooling: list[str]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def _digest(value: object, label: str) -> str:
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             "Invalid SHA256: " + label)
    return value


def _relative(value: object) -> str:
    _require(isinstance(value, str) and bool(value), "Expected nonempty relative path")
    path = PurePosixPath(value)
    _require(bool(path.parts) and not path.is_absolute() and str(path) == value and ".." not in path.parts
             and ".git" not in path.parts and "\\" not in value
             and not any(ord(char) < 32 or ord(char) == 127 for char in value),
             "Unsafe relative path: " + repr(value))
    _require(path.name not in {".env", "google-services.json", "GoogleService-Info.plist"}
             and not path.name.endswith((".p12", ".pfx", ".jks", ".keystore"))
             and not (path.name.startswith(".env.") and path.name not in {".env.example", ".env.sample"}),
             "Credential/signing path is not an inventory input: " + value)
    return value


def _path(root: Path, relative: str) -> Path:
    relative = _relative(relative)
    cursor = root
    _require(root.is_absolute() and root.is_dir() and not root.is_symlink(), "Unsafe workspace root")
    for part in PurePosixPath(relative).parts:
        cursor = cursor / part
        _require(not cursor.is_symlink(), "Symlink inventory path: " + relative)
        if cursor.exists() and cursor != root / relative:
            _require(cursor.is_dir(), "Non-directory inventory parent: " + relative)
    return cursor


def _read(root: Path, relative: str, *, missing_ok: bool = False) -> bytes | None:
    path = _path(root, relative)
    if not path.exists():
        _require(missing_ok, "Missing inventory input: " + relative)
        return None
    _require(stat.S_ISREG(path.lstat().st_mode), "Non-regular inventory input: " + relative)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode), "Non-regular inventory input: " + relative)
        data = stream.read()
        after = os.fstat(stream.fileno())
    _require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             "Input changed while reading: " + relative)
    return data


def _json(data: bytes, label: str) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "Duplicate JSON key in " + label + ": " + key)
            result[key] = value
        return result

    try:
        value = json.loads(data, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as error:
        raise InventoryError("Invalid JSON input: " + label) from error
    _require(isinstance(value, dict), "Expected JSON object: " + label)
    return value


def _hash_map(value: object, label: str) -> dict[str, str]:
    _require(isinstance(value, dict), "Expected hash map: " + label)
    return {_relative(p): _digest(h, label + ": " + p) for p, h in value.items()}


def _paths(value: object, label: str) -> list[str]:
    _require(isinstance(value, list) and all(isinstance(p, str) for p in value), "Expected path list: " + label)
    _require(len(value) == len(set(value)), "Duplicate paths: " + label)
    return sorted(_relative(p) for p in value)


def _verify_hashes(root: Path, mapping: dict[str, str], label: str) -> None:
    for path, expected in mapping.items():
        _require(sha256(_read(root, path)) == expected, label + " changed: " + path)


def _git(repo: Path, *args: str) -> bytes:
    # Do not refresh/write indexes, execute textconv/external diff helpers, or perform network I/O.
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(["git", "-c", "core.quotePath=true", *args], cwd=repo, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode == 1 and args[:3] == ("rev-parse", "--verify", "--quiet"):
        return b""
    _require(result.returncode == 0, "Read-only Git query failed: " + repo.name + " " + " ".join(args))
    return result.stdout


def issue_diff(root: Path, *, spec: EvidenceSpec = SPEC, git: GitReader = _git) -> bytes:
    """Full pinned issue baseline to worktree; untracked bytes are separately inventoried."""
    return git(root / "kira-backend", *DIFF_OPTIONS, spec.issue_base, "--")


def _git_paths(data: bytes) -> set[str]:
    _require(not data or data.endswith(b"\0"), "Git path inventory was not NUL terminated")
    try:
        return {_relative(p.decode("utf-8")) for p in data.split(b"\0") if p}
    except UnicodeError as error:
        raise InventoryError("Non-UTF8 Git path; explicit review required") from error


def _discover(root: Path, spec: EvidenceSpec, git: GitReader) -> tuple[set[str], set[str]]:
    repo = root / "kira-backend"
    changed = _git_paths(git(repo, "diff", "--name-only", "-z", "--no-ext-diff", "--no-textconv",
                             "--no-renames", "--no-relative", "--ignore-submodules=none", spec.issue_base, "--"))
    untracked = _git_paths(git(repo, "ls-files", "--others", "--exclude-standard", "-z"))
    return changed, untracked


def _history(root: Path, spec: EvidenceSpec) -> tuple[dict, dict, dict[str, str]]:
    pins = {spec.seed: spec.seed_sha256, spec.timer: spec.timer_sha256}
    _verify_hashes(root, pins, "Immutable baseline manifest")
    seed = _json(_read(root, spec.seed), spec.seed)
    timer = _json(_read(root, spec.timer), spec.timer)
    for manifest, label in ((seed, "development07"), (timer, "Timer-A02")):
        manifest["source_hashes"] = _hash_map(manifest.get("source_hashes"), label)
        manifest["removed_paths"] = _paths(manifest.get("removed_paths"), label + " removals")
        _require(not set(manifest["removed_paths"]) & manifest["source_hashes"].keys(),
                 label + " lists a source as both present and removed")
        for field in ("snapshots", "validation_tooling"):
            entries = _hash_map(manifest.get(field), label + " " + field)
            _verify_hashes(root, entries, label + " " + field)
            pins.update(entries)
    _require(len(seed["source_hashes"]) == spec.seed_count, "development07 seed inventory count changed")
    _require(seed.get("previous_manifest") == spec.timer and seed.get("previous_manifest_sha256") == spec.timer_sha256,
             "development07 no longer names the pinned Timer-A02 baseline")
    _require(set(timer["removed_paths"]) <= set(seed["removed_paths"]), "Inherited Timer removals disappeared")
    _check_comparison(seed, timer["source_hashes"], "development07 Timer-A02")
    _verify_snapshot_layout(root, Path(spec.seed).parent.as_posix(), seed)
    approved = _hash_map(seed.get("approved_inputs"), "development07 approved inputs")
    _verify_hashes(root, approved, "Historical approved input")
    pins.update(approved)
    return seed, timer, pins


def _comparison(source: dict, baseline: dict) -> tuple[list[str], list[str], list[str]]:
    changed = sorted(p for p in baseline.keys() & source.keys() if source[p] != baseline[p])
    added = sorted(source.keys() - baseline.keys())
    return changed, added, sorted(changed + added)


def _check_comparison(manifest: dict, baseline: dict, label: str) -> None:
    changed, added, subjects = _comparison(manifest["source_hashes"], baseline)
    for field, expected in (("changed_previous_paths", changed), ("added_paths", added), ("review_subject_paths", subjects)):
        # Historical07 follows Timer's insertion order, not lexical order, for changed paths.
        # Check exact duplicate-free membership without rewriting that hash-pinned history.
        _require(_paths(manifest.get(field), label + " " + field) == expected, label + " comparison mismatch: " + field)
    _require(baseline.keys() <= manifest["source_hashes"].keys() | set(manifest["removed_paths"]),
             label + " lost a baseline source")


def _verify_snapshot_layout(root: Path, folder: str, manifest: dict) -> None:
    expected = {folder + "/sources/" + p: manifest["source_hashes"][p] for p in manifest["review_subject_paths"]}
    _require(manifest.get("snapshots") == expected, "Snapshot inventory is incomplete or misbound")
    _verify_hashes(root, expected, "Frozen source snapshot")


def _checkpoint(root: Path, spec: EvidenceSpec, seed: dict) -> tuple[dict, dict]:
    data = _read(root, spec.ledger)
    _require(sha256(data) == spec.ledger_sha256, "Immutable checkpoint ledger changed")
    ledger = _json(data, spec.ledger)
    rows = ledger.get("repositories", [])
    _require(isinstance(rows, list) and len(rows) == len(REPOSITORIES), "Incomplete checkpoint repository ledger")
    expected = {}
    for row in rows:
        _require(isinstance(row, dict), "Invalid checkpoint repository entry")
        name = row.get("directory")
        _require(name in REPOSITORIES and name not in expected, "Unexpected/duplicate checkpoint repository")
        head = row.get("checkpoint_head", "")
        # Preserve the hash-pinned historical marker; never resolve it through today's Admin HEAD.
        containing_commit = name == "kira-admin" and head.startswith("CONTAINING_COMMIT:")
        _require(containing_commit or re.fullmatch(r"[0-9a-f]{40}", head) is not None,
                 "Invalid checkpoint HEAD: " + name)
        _require(row.get("integration_branch") == INTEGRATION_BRANCH
                 and row.get("integration_head") == seed["integration_refs"].get(name),
                 "Checkpoint integration baseline changed: " + name)
        expected[name] = {"head": head, "branch": row.get("branch"), "integration": row["integration_head"]}
    _require(expected["kira-backend"]["integration"] == spec.issue_base, "Issue diff base differs from integration baseline")
    _require(expected["kira-backend"]["branch"] == "remediation/app-29-backend-complaints", "Unauthorized backend branch")
    return expected, {spec.ledger: sha256(data)}


def _repository_states(root: Path, expected: dict, git: GitReader, *, frozen: dict | None = None) -> dict:
    repositories, refs, names, aliases = {}, {}, {}, {}
    for name in ("kira-backend",):
        folder = _path(root, name)
        _require(not git(folder, "diff", "--cached", "--name-only", "-z"), "Staged changes are not allowed: " + name)
        current = {
            "head": git(folder, "rev-parse", "HEAD").decode().strip(),
            "branch": git(folder, "branch", "--show-current").decode().strip(),
            "status": git(folder, "status", "--porcelain=v1").decode(),
        }
        _require(re.fullmatch(r"[0-9a-f]{40}", current["head"]) is not None
                 and current["branch"] == expected[name]["branch"], "Invalid Backend batch HEAD/issue branch")
        resolved = {}
        for prefix in ("refs/heads/", "refs/remotes/origin/"):
            ref = prefix + INTEGRATION_BRANCH
            value = git(folder, "rev-parse", "--verify", "--quiet", ref + "^{commit}").decode().strip()
            if value:
                _require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, "Invalid Backend integration ref: " + ref)
                resolved[ref] = value
        _require(bool(resolved), "Missing Backend integration ref")
        repositories[name], refs[name], names[name], aliases[name] = current, next(iter(resolved.values())), next(iter(resolved)), resolved
    states = {"repositories": repositories, "integration_refs": refs, "integration_ref_names": names, "integration_ref_aliases": aliases}
    _require(frozen is None or states == frozen, "Frozen Backend batch identity changed")
    return states


def _seed_preserved_count(seed_sources: dict, sources: dict) -> int:
    _require(seed_sources.keys() <= sources.keys(), "Candidate must retain every development07 source path; no seed-removal waiver")
    return len(seed_sources)


def _removals(root: Path, path: str | None, missing: set[str], inherited: set[str], seed: dict,
              spec: EvidenceSpec, git: GitReader) -> tuple[dict, dict]:
    fresh = missing - inherited
    receipts, pins = {}, {}
    if path is not None:
        _require(path.startswith("review/"), "Removal receipt must be review evidence")
        data = _read(root, path)
        document = _json(data, path)
        _require(document.get("schema_version") == 1 and document.get("seed_manifest_sha256") == spec.seed_sha256,
                 "Removal receipt does not bind the immutable seed")
        _require(isinstance(document.get("removals"), list), "Removal receipt requires a removals list")
        pins[path] = sha256(data)
        for receipt in document["removals"]:
            _require(isinstance(receipt, dict), "Invalid removal receipt entry")
            relative = _relative(receipt.get("path"))
            _require(relative not in receipts and relative in fresh, "Unexpected, present, or duplicate reviewed removal: " + relative)
            prior = seed["source_hashes"].get(relative)
            if prior is None:
                tree = git(root / "kira-backend", "ls-tree", "-z", spec.issue_base, "--", relative)
                _require(tree.startswith((b"100644 blob ", b"100755 blob ")) and tree.endswith(b"\t" + relative.encode() + b"\0"),
                         "Removal lacks a regular-file baseline: " + relative)
                prior = sha256(git(root / "kira-backend", "show", spec.issue_base + ":" + relative))
            _require(receipt.get("previous_sha256") == prior, "Reviewed removal previous hash mismatch: " + relative)
            review = _relative(receipt.get("review_document"))
            _require(review.startswith("review/") and review != path and isinstance(receipt.get("reason"), str)
                     and bool(receipt["reason"].strip()), "Removal lacks separate review/rationale: " + relative)
            pins[review] = _digest(receipt.get("review_document_sha256"), review)
            receipts[relative] = receipt
    _require(set(receipts) == fresh, "Unreviewed missing/removal paths: " + ", ".join(sorted(fresh - receipts.keys())))
    _verify_hashes(root, pins, "Reviewed removal evidence")
    return dict(sorted(receipts.items())), pins


def prepare_candidate(root: Path, tasks: list[str], *, approved_inputs=(), extra_tooling=(),
                      reviewed_removals: str | None = None, allow_missing_tooling: bool = False,
                      frozen_backend_identity: dict | None = None, workspace_context: dict | None = None,
                      spec: EvidenceSpec = SPEC, git: GitReader = _git) -> Candidate:
    """Collect/recheck bytes in memory only. No candidate directory is created."""
    root = Path(root).absolute()
    _require(isinstance(tasks, list) and bool(tasks) and all(isinstance(t, str) and t and "\0" not in t for t in tasks),
             "Explicit nonempty validation tasks/options are required")
    seed, timer, historical_pins = _history(root, spec)
    expected, ledger_pin = _checkpoint(root, spec, seed)
    historical_pins.update(ledger_pin)
    before = _repository_states(root, expected, git, frozen=frozen_backend_identity)
    git(root / "kira-backend", "merge-base", "--is-ancestor", spec.issue_base, "HEAD")
    changed_paths, untracked_paths = _discover(root, spec, git)
    inherited = set(seed["removed_paths"])
    paths = set(seed["source_hashes"]) | set(timer["source_hashes"]) | inherited | changed_paths | untracked_paths
    source_bytes, missing = {}, set()
    for relative in sorted(paths):
        data = _read(root / "kira-backend", relative, missing_ok=True)
        if data is None:
            missing.add(relative)
        else:
            _require(relative not in inherited, "Inherited removed/renamed source reappeared: " + relative)
            source_bytes[relative] = data
    removals, removal_pins = _removals(root, reviewed_removals, missing, inherited, seed, spec, git)
    source = {p: sha256(data) for p, data in source_bytes.items()}
    approved = dict(seed["approved_inputs"])
    for relative in sorted(set(spec.required_inputs) | set(approved_inputs)):
        _require(_relative(relative).startswith("review/"), "Additional approved input must be review evidence")
        value = sha256(_read(root, relative))
        _require(relative not in approved or approved[relative] == value, "Cannot override historical approved input")
        approved[relative] = value
    approved.update(removal_pins)
    tooling, missing_tooling = {}, []
    for relative in sorted(set(spec.tooling) | set(extra_tooling)):
        _require(_relative(relative).startswith("review/working/"), "Tooling must remain under review/working")
        data = _read(root, relative, missing_ok=allow_missing_tooling)
        if data is None:
            missing_tooling.append(relative)
        else:
            tooling[relative] = sha256(data)
    changed, added, subjects = _comparison(source, timer["source_hashes"])
    seed_changed, seed_added, _ = _comparison(source, seed["source_hashes"])
    diff = issue_diff(root, spec=spec, git=git)
    fields = {
        "schema_version": 3,
        "status": "FROZEN DEVELOPMENT CANDIDATE - NOT ACCEPTANCE",
        "validation_scope": seed["validation_scope"],
        "source_hashes": source, "review_subject_paths": subjects,
        "changed_previous_paths": changed, "added_paths": added, "removed_paths": sorted(missing),
        "changed_seed_paths": seed_changed, "added_since_seed_paths": seed_added,
        "removed_since_seed_paths": sorted(removals), "reviewed_removals": removals,
        "reviewed_removals_input": reviewed_removals,
        "previous_manifest": spec.timer, "previous_manifest_sha256": spec.timer_sha256,
        "inventory_seed_manifest": spec.seed, "inventory_seed_manifest_sha256": spec.seed_sha256,
        "inventory_seed_path_count": spec.seed_count,
        "inventory_seed_preserved_count": _seed_preserved_count(seed["source_hashes"], source),
        "historical_checkpoint_repositories": expected,
        "workspace_context": copy.deepcopy(WORKSPACE_CONTEXT if workspace_context is None else workspace_context),
        "historical_input_hashes": dict(sorted(historical_pins.items())),
        "approved_inputs": dict(sorted(approved.items())), "validation_tooling": tooling,
        "additional_approved_input_paths": sorted(set(approved_inputs)),
        "additional_validation_tooling_paths": sorted(set(extra_tooling)),
        "validation_task_args": list(tasks), "evidence_class_names": seed["evidence_class_names"],
        "issue_diff_base": spec.issue_base, "issue_diff_args": [*DIFF_OPTIONS, spec.issue_base, "--"],
        "complete_diff_sha256": sha256(diff),
        "complete_diff_scope": "issue baseline to working tree; untracked bytes are hashed and snapshotted separately",
        "issue_changed_paths": sorted(changed_paths), "untracked_paths": sorted(untracked_paths),
        "runtime": "UNKNOWN", "W03": "INCOMPLETE", **before,
    }
    _check_comparison(fields, timer["source_hashes"], "Candidate Timer-A02")
    _require(set(seed["source_hashes"]) <= source.keys(), "Candidate lost a development07 path")
    _verify_hashes(root / "kira-backend", source, "Source during inventory collection")
    for relative in sorted(missing):
        _require(_read(root / "kira-backend", relative, missing_ok=True) is None,
                 "Removed source reappeared during inventory collection: " + relative)
    for pins in (historical_pins, approved, tooling):
        _verify_hashes(root, pins, "Evidence during inventory collection")
    _require(before == _repository_states(root, expected, git), "Repository/ref state changed during inventory collection")
    _require((changed_paths, untracked_paths) == _discover(root, spec, git), "Path discovery changed during inventory collection")
    _require(diff == issue_diff(root, spec=spec, git=git), "Full issue diff changed during inventory collection")
    return Candidate(fields, source_bytes, diff, missing_tooling)


def _candidate_again(root: Path, fields: dict, *, spec: EvidenceSpec, git: GitReader) -> Candidate:
    return prepare_candidate(root, fields["validation_task_args"],
                             approved_inputs=fields["additional_approved_input_paths"],
                             extra_tooling=fields["additional_validation_tooling_paths"],
                             reviewed_removals=fields["reviewed_removals_input"],
                             frozen_backend_identity={key: fields[key] for key in BATCH_IDENTITY_FIELDS},
                             workspace_context=fields["workspace_context"], spec=spec, git=git)


def validate_manifest(root: Path, manifest_path: Path, tasks: list[str],
                      expected_manifest_sha256: str | None = None, *,
                      spec: EvidenceSpec = SPEC, git: GitReader = _git) -> dict:
    """Read-only execution preflight: recompute membership AND every pinned invariant."""
    root = Path(root).absolute()
    path = Path(manifest_path)
    if path.is_absolute():
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError as error:
            raise InventoryError("Manifest is outside the workspace") from error
    else:
        relative = path.as_posix()
    _require(_relative(relative).startswith("review/working/"), "Manifest must be under review/working")
    data = _read(root, relative)
    original_hash = sha256(data)
    if expected_manifest_sha256 is not None:
        _require(original_hash == _digest(expected_manifest_sha256, "manifest"), "Frozen manifest hash changed")
    manifest = _json(data, relative)
    _require(manifest.get("schema_version") == 3, "Only successor v3 manifests are accepted; historical candidates stay immutable")
    _require(manifest.get("validation_task_args") == tasks, "Validation tasks differ from the frozen candidate")
    required = {"additional_approved_input_paths", "additional_validation_tooling_paths", "reviewed_removals_input", "workspace_context"}
    _require(required | set(BATCH_IDENTITY_FIELDS) <= manifest.keys(), "Incomplete v3 manifest inputs")
    for field in ("additional_approved_input_paths", "additional_validation_tooling_paths"):
        _paths(manifest[field], field)
    actual = _candidate_again(root, manifest, spec=spec, git=git)
    for field, expected in actual.fields.items():
        _require(manifest.get(field) == expected, "Frozen candidate drift or incomplete inventory: " + field)
    folder = PurePosixPath(relative).parent.as_posix()
    _verify_snapshot_layout(root, folder, manifest)
    patch = folder + "/issue-baseline.patch"
    _require(manifest.get("complete_diff_path") == patch, "Full issue diff snapshot path changed")
    _require(_read(root, patch) == actual.diff_bytes, "Frozen full issue diff snapshot changed")
    _require(sha256(_read(root, relative)) == original_hash, "Manifest changed during preflight")
    return manifest


def _write_new(root: Path, relative: str, data: bytes) -> None:
    path = _path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    _path(root, relative)
    with path.open("xb") as output:
        output.write(data)


def freeze_candidate(root: Path, candidate: Candidate, name: str, *,
                     spec: EvidenceSpec = SPEC, git: GitReader = _git) -> Path:
    """Explicit opt-in only; never overwrite/clean an output. A failure retains partial evidence."""
    root = Path(root).absolute()
    _require(re.fullmatch(r"app-29-w03-integrated-driver-[a-z0-9][a-z0-9-]*", name) is not None,
             "Require a fresh app-29-w03-integrated-driver-* candidate name")
    _require(not candidate.missing_tooling, "Missing successor tooling; cannot freeze")
    relative = "review/working/" + name
    out = _path(root, relative)
    _require(not out.exists(), "Refusing to overwrite existing candidate: " + relative)
    current = _candidate_again(root, candidate.fields, spec=spec, git=git)
    _require(current.fields == candidate.fields and current.source_bytes == candidate.source_bytes
             and current.diff_bytes == candidate.diff_bytes, "Candidate changed before freezing")
    out.mkdir()
    manifest = dict(candidate.fields)
    manifest["snapshots"] = {}
    for path in manifest["review_subject_paths"]:
        snapshot = relative + "/sources/" + path
        _write_new(root, snapshot, candidate.source_bytes[path])
        manifest["snapshots"][snapshot] = manifest["source_hashes"][path]
    manifest["complete_diff_path"] = relative + "/issue-baseline.patch"
    _write_new(root, manifest["complete_diff_path"], candidate.diff_bytes)
    _verify_snapshot_layout(root, relative, manifest)
    final = _candidate_again(root, candidate.fields, spec=spec, git=git)
    _require(final.fields == candidate.fields, "Candidate drifted while writing snapshots; no manifest published")
    manifest["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _write_new(root, relative + "/manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    return out / "manifest.json"


def _summary(candidate: Candidate) -> dict:
    fields = candidate.fields
    return {
        "status": "DRY_VALIDATED_INVENTORY_ONLY_NOT_A_FREEZE",
        "no_candidate_written": True,
        "source_path_count": len(fields["source_hashes"]),
        "development07_seed_count": fields["inventory_seed_path_count"],
        "development07_paths_preserved": fields["inventory_seed_preserved_count"],
        "changed_since_development07": fields["changed_seed_paths"],
        "added_since_development07": fields["added_since_seed_paths"],
        "removed_since_development07": fields["removed_since_seed_paths"],
        "inherited_removed_paths": fields["removed_paths"],
        "timer_a02_changed_paths": fields["changed_previous_paths"],
        "timer_a02_added_count": len(fields["added_paths"]),
        "prospective_snapshot_count": len(fields["review_subject_paths"]),
        "issue_diff_base": fields["issue_diff_base"],
        "full_issue_diff_sha256": fields["complete_diff_sha256"],
        "full_issue_diff_bytes": len(candidate.diff_bytes),
        "missing_validation_tooling": candidate.missing_tooling,
        "validation_task_args": fields["validation_task_args"],
        "approved_input_hashes": fields["approved_inputs"],
        "validation_tooling_hashes": fields["validation_tooling"],
        "repositories": fields["repositories"],
        "integration_ref_names": fields["integration_ref_names"],
        "integration_ref_aliases": fields["integration_ref_aliases"],
        "historical_checkpoint_repositories": fields["historical_checkpoint_repositories"],
        "workspace_context_documentary_only": fields["workspace_context"],
        "not_an_execution_authorization": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).absolute().parents[2])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="default; inventory in memory and print summary only")
    mode.add_argument("--freeze", metavar="FRESH_NAME", help="explicit future fresh-directory freeze; no builds")
    mode.add_argument("--validate-manifest", type=Path, help="read-only revalidation of a successor v3 candidate")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--approved-input", action="append", default=[])
    parser.add_argument("--tooling", action="append", default=[])
    parser.add_argument("--reviewed-removals")
    parser.add_argument("tasks", nargs=argparse.REMAINDER, help="exact Gradle tasks/options after --")
    args = parser.parse_args(argv)
    tasks = args.tasks[1:] if args.tasks[:1] == ["--"] else args.tasks
    try:
        if args.validate_manifest:
            _require(bool(tasks), "Manifest validation requires explicit exact tasks")
            manifest = validate_manifest(args.workspace, args.validate_manifest, tasks, args.manifest_sha256)
            print(json.dumps({"status": "READ_ONLY_V3_PREFLIGHT_PASSED", "source_paths": len(manifest["source_hashes"])}))
        else:
            _require(not args.manifest_sha256, "--manifest-sha256 requires --validate-manifest")
            _require(not args.freeze or bool(tasks), "Freezing requires explicit tasks; dry-run defaults are not authority")
            if not tasks:
                seed, _, _ = _history(args.workspace, SPEC)
                tasks = seed["validation_task_args"]
            candidate = prepare_candidate(args.workspace, tasks, approved_inputs=args.approved_input,
                                          extra_tooling=args.tooling, reviewed_removals=args.reviewed_removals,
                                          allow_missing_tooling=not bool(args.freeze))
            if args.freeze:
                manifest = freeze_candidate(args.workspace, candidate, args.freeze)
                print(manifest.relative_to(args.workspace), sha256(manifest.read_bytes()))
            else:
                print(json.dumps(_summary(candidate), indent=2))
        return 0
    except (InventoryError, OSError, KeyError, TypeError) as error:
        parser.exit(1, "INVENTORY REFUSED: " + str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
