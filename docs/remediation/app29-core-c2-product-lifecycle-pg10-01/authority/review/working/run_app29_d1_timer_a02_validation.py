#!/usr/bin/env python3
"""Timer-A02 bounded correction verification runner: retain results, stop Gradle immediately, clean, and stop again.

This is evidence tooling, not a product build configuration or a release verifier.
The init script routes only the explicitly snapshotted local source-engine coordinates.
"""

import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "kira-backend"
EVIDENCE = ROOT / "review" / "working" / sys.argv[1]
INIT = ROOT / "review" / "working" / "app-29-w01-local-dependencies.init.gradle"
DEPENDENCY_RUN = ROOT / "review" / "working" / "app-29-w01-local-dependencies-20260905"
TASKS = sys.argv[2:]
if not TASKS or not EVIDENCE.name.startswith("app-29-") or EVIDENCE.exists():
    raise SystemExit("Use a fresh app-29-* evidence directory and explicit Gradle tasks/options.")
if not INIT.is_file():
    raise SystemExit("The reviewed explicit local-dependency route is required first.")
MANIFEST = ROOT / "review/working/app-29-w03-d1-timer-a-02/manifest.json"
manifest = json.loads(MANIFEST.read_text())
for relative, expected in manifest['validation_tooling'].items():
    if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit('Frozen validation tooling changed: ' + relative)
for relative, expected in manifest['snapshots'].items():
    if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit('Frozen source snapshot changed: ' + relative)
for relative, expected in manifest["source_hashes"].items():
    if hashlib.sha256((REPO / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit("Frozen WIP source changed before validation: " + relative)
# Timer-A may add only its frozen new components and one additive bootstrap seam.
previous_manifest = json.loads((ROOT / "review/working/app-29-w03-d1-c6-wip-20/manifest.json").read_text())
allowed_change = "src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PersistenceDriverBootstrap.kt"
if manifest["changed_previous_paths"] != [allowed_change]:
    raise SystemExit("Unexpected existing-source change allowlist.")
for relative, expected in previous_manifest["source_hashes"].items():
    if relative != allowed_change and manifest["source_hashes"].get(relative) != expected:
        raise SystemExit("Timer-A changed protected source: " + relative)
timer01 = json.loads((ROOT / "review/working/app-29-w03-d1-timer-a-01/manifest.json").read_text())
correction = json.loads((ROOT / "review/working/app-29-w03-d1-timer-a-02-direction-v1.json").read_text())
if set(manifest["changed_timer01_paths"]) != set(correction["allowed_change_paths"]):
    raise SystemExit("Correction differs from the approved four-file allowlist.")
for relative, expected in timer01["source_hashes"].items():
    if relative not in correction["allowed_change_paths"] and manifest["source_hashes"].get(relative) != expected:
        raise SystemExit("Correction changed protected timer01 source: " + relative)
if TASKS != manifest["validation_task_args"]:
    raise SystemExit("Validation tasks differ from the frozen candidate.")
for relative in manifest.get("removed_paths", []):
    if (REPO / relative).exists() or (REPO / relative).is_symlink():
        raise SystemExit("The frozen content-preserving rename source is still present.")
# Reject drift before execution, including untracked sources outside the frozen map.
for repository, expected in manifest["repositories"].items():
    folder = ROOT / repository
    current = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=folder, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=folder, text=True).strip(),
        "status": subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=folder, text=True),
    }
    if current != expected or subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=folder):
        raise SystemExit("Frozen repository state changed before validation: " + repository)
    if subprocess.check_output(['git', 'rev-parse', 'remediation/production-readiness-2026-09-04'], cwd=folder, text=True).strip() != manifest['integration_refs'][repository]:
        raise SystemExit('Integration ref changed before validation: ' + repository)
if hashlib.sha256(subprocess.check_output(["git", "diff", "--binary"], cwd=REPO)).hexdigest() != manifest["complete_diff_sha256"]:
    raise SystemExit("Frozen complete diff changed before validation.")
if shutil.disk_usage(ROOT).free < 3 * 1024**3:
    raise SystemExit("Less than 3 GiB free; refusing to begin another build cycle.")
ROOT_BUILD = REPO / "build"
if ROOT_BUILD.exists() or ROOT_BUILD.is_symlink():
    raise SystemExit("Refusing to touch a pre-existing root build directory.")
BUILD = DEPENDENCY_RUN / "backend-build"
if BUILD.exists() or BUILD.is_symlink():
    raise SystemExit("Refusing to overwrite or clean pre-existing build outputs.")
if subprocess.check_output(["git", "ls-files", "--", "build"], cwd=REPO):
    raise SystemExit("Refusing a generated-output path containing tracked files.")
branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip()
if branch != "remediation/app-29-backend-complaints":
    raise SystemExit("Not on the authorized App #29 issue branch.")
EVIDENCE.mkdir()
env = os.environ.copy()
env["JAVA_HOME"] = subprocess.check_output(["/usr/libexec/java_home", "-v", "21"], text=True).strip()
env["GRADLE_USER_HOME"] = str(DEPENDENCY_RUN / "gradle-home")
env["GRADLE_RO_DEP_CACHE"] = str(Path.home() / ".gradle" / "caches")
env["W01_RUN"] = str(DEPENDENCY_RUN)
for secret_variable in ("KIRA_PACKAGES_READ_TOKEN", "GITHUB_TOKEN"):
    env.pop(secret_variable, None)
base = [
    "./gradlew", "--no-daemon", "--offline", "--no-parallel", "--max-workers=1",
    "--no-build-cache", "--no-configuration-cache",
    "--project-cache-dir", str(DEPENDENCY_RUN / "backend-project-cache"),
    "--console=plain", "-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m",
    "-Dorg.gradle.vfs.watch=false", "-PkiraUseMavenLocal=false",
    "-Pkotlin.compiler.execution.strategy=in-process",
    "-Pkotlin.project.persistent.dir=" + str(DEPENDENCY_RUN / "backend-kotlin-cache"),
    "--init-script", str(INIT),
]
ledger = {
    "started_at": datetime.datetime.now().astimezone().isoformat(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
    "branch": branch,
    "scope": "Timer-A low-level public utility and capture verification; not record-boundary/root/terminal/native-disposal, full check or release proof",
    "source_manifest": str(MANIFEST.relative_to(ROOT)),
    "source_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
    "java_home": env["JAVA_HOME"],
    "gradle_user_home": env["GRADLE_USER_HOME"],
    "read_only_dependency_cache": env["GRADLE_RO_DEP_CACHE"],
    "commands": [],
}
diff = subprocess.check_output(["git", "diff", "--binary"], cwd=REPO)
(EVIDENCE / "input.patch").write_bytes(diff)
ledger["diff_sha256"] = hashlib.sha256(diff).hexdigest()
ledger["init_sha256"] = hashlib.sha256(INIT.read_bytes()).hexdigest()


def checkpoint():
    (EVIDENCE / "result.json").write_text(json.dumps(ledger, indent=2) + "\n")


def run(name, command, timeout=1200):
    item = {"name": name, "command": command, "started_at": datetime.datetime.now().astimezone().isoformat()}
    ledger["commands"].append(item)
    checkpoint()
    print("RUN", name, flush=True)
    with (EVIDENCE / (name + ".log")).open("w") as log:
        process = subprocess.Popen(command, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        item["pid"] = process.pid
        checkpoint()
        try:
            item["exit_code"] = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            item["interrupted"] = True
            item["exit_code"] = process.returncode
            raise
        finally:
            item["finished_at"] = datetime.datetime.now().astimezone().isoformat()
            checkpoint()
    print("RESULT", name, item["exit_code"], flush=True)
    return item["exit_code"]


def interrupted(_signum, _frame):
    raise KeyboardInterrupt()


signal.signal(signal.SIGTERM, interrupted)
try:
    run("validation", base + TASKS)
finally:
    try:
        run("stop-after-validation", ["./gradlew", "--stop"], timeout=120)
    finally:
        try:
            # Capture only the exact new class evidence before cleaning, never a release/signed artifact.
            bytecode = BUILD / "classes/kotlin/main/me/manga/kira/backend/common/infrastructure/persistence"
            class_names = manifest["evidence_class_names"]
            compiled = [bytecode / (name + ".class") for name in class_names]
            if compiled and all(path.is_file() and not path.is_symlink() for path in compiled):
                folder = EVIDENCE / "bytecode"
                folder.mkdir()
                ledger["retained_bytecode"] = []
                for path in compiled:
                    target = folder / path.name
                    shutil.copyfile(path, target)
                    ledger["retained_bytecode"].append({"path": str(target.relative_to(EVIDENCE)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
                run("inspect-owned-control-bytecode", [str(Path(env["JAVA_HOME"]) / "bin/javap"), "-c", "-p", "-s"] + [str(p) for p in compiled], timeout=90)
                ledger["control_when_mappings_class_present"] = (bytecode / "PersistenceOwnedCallerControl$WhenMappings.class").exists()
                checkpoint()
            # Preserve the separate accepted race-test descriptor evidence; never substitute it for main classes.
            test_class = BUILD / "classes/kotlin/test/me/manga/kira/backend/common/infrastructure/persistence/PgRequireErrorHandlerTest.class"
            if test_class.is_file() and not test_class.is_symlink():
                test_folder = EVIDENCE / "test-bytecode"
                test_folder.mkdir()
                target = test_folder / test_class.name
                shutil.copyfile(test_class, target)
                ledger["retained_test_bytecode"] = [{"path": str(target.relative_to(EVIDENCE)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}]
                run("inspect-handler-test-bytecode", [str(Path(env["JAVA_HOME"]) / "bin/javap"), "-c", "-p", "-s", str(test_class)], timeout=90)
                checkpoint()
        except BaseException as capture_failure:
            ledger["bytecode_capture_failure"] = type(capture_failure).__name__
            checkpoint()
        try:
            # Results are small XML/text only, never an unrelated signed or private artifact.
            retained = []
            for folder in (BUILD / "test-results", BUILD / "reports"):
                if folder.is_dir():
                    for source in sorted(folder.rglob("*")):
                        if source.is_file() and not source.is_symlink() and source.suffix in {".xml", ".txt", ".sarif"}:
                            target = EVIDENCE / "reports" / source.relative_to(BUILD)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(source, target)
                            retained.append({"path": str(target.relative_to(EVIDENCE)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
            ledger["retained_reports"] = retained
            checkpoint()
        except BaseException as capture_failure:
            ledger["report_capture_failure"] = type(capture_failure).__name__
            ledger["retained_reports"] = retained
            checkpoint()
        finally:
            # A failed evidence copy must not skip the mandatory generated-output cleanup.
            try:
                run("clean", base + ["clean"], timeout=240)
            finally:
                run("stop-after-clean", ["./gradlew", "--stop"], timeout=120)
                ledger["build_directory_absent"] = not BUILD.exists() and not BUILD.is_symlink()
                ledger["root_build_absent"] = not ROOT_BUILD.exists() and not ROOT_BUILD.is_symlink()
                ledger["source_hashes_preserved"] = all(hashlib.sha256((REPO / p).read_bytes()).hexdigest() == h for p,h in manifest["source_hashes"].items())
                ledger["finished_at"] = datetime.datetime.now().astimezone().isoformat()
                ledger["jps_after"] = subprocess.check_output([str(Path(env["JAVA_HOME"]) / "bin/jps"), "-l"], text=True)
                ledger["git_diff_check_exit"] = subprocess.run(["git", "diff", "--check"], cwd=REPO, capture_output=True).returncode
                checkpoint()
                print(json.dumps(ledger, indent=2), flush=True)

sys.exit(0 if all(item.get("exit_code") == 0 for item in ledger["commands"]) and ledger["build_directory_absent"] and ledger["root_build_absent"] and ledger["source_hashes_preserved"] and not ledger.get("bytecode_capture_failure") and not ledger.get("report_capture_failure") and len(ledger.get("retained_test_bytecode", [])) == 1 and len(ledger.get("retained_bytecode", [])) == len(manifest["evidence_class_names"]) else 1)
