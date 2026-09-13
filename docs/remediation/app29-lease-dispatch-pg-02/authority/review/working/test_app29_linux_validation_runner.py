#!/usr/bin/env python3
"""No-build controls for the versioned Linux validation helper's boundaries."""
import hashlib
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import app29_linux_owned_processes as owned
from app29_linux_owned_processes import OwnershipError
import run_app29_integrated_driver_validation_linux as runner
from test_app29_linux_owned_processes import FakeKernel, row


class LinuxRunnerControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="app29-runner-control-")
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_import_has_no_commands_or_filesystem_side_effect(self):
        spec = importlib.util.spec_from_file_location("app29_runner_import_control", Path(runner.__file__))
        module = importlib.util.module_from_spec(spec)
        with patch("subprocess.Popen", side_effect=AssertionError("command on import")):
            spec.loader.exec_module(module)

    def test_full_and_targeted_tasks_permitted(self):
        runner.require_tasks(["check", "--continue"])
        runner.require_tasks(["test", "--tests", "me.manga.kira.backend.ExampleTest", "ktlintCheck", "detekt", "--continue"])

    def test_deploy_release_publish_and_arbitrary_flags_rejected(self):
        for tasks in ([], ["bootRun"], ["publish"], ["--init-script", "/tmp/unsafe"],
                      ["test", "--tests"], ["test", "--tests", "../../escape"],
                      ["test", "--dependency-verification=off"], ["test", "-x", "check"]):
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                runner.require_tasks(tasks)

    def test_safe_path_rejects_absolute_and_traversal(self):
        for relative in ("/etc/passwd", "x/../out", "../out", ""):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                runner.safe_path(self.root, relative)

    def test_safe_path_rejects_symlink_leaf_and_parent(self):
        (self.root / "real").mkdir()
        (self.root / "link").symlink_to(self.root / "real", target_is_directory=True)
        for relative in ("link", "link/nested"):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                runner.safe_path(self.root, relative)

    def source_inputs(self, data=b"verified fixture bytes"):
        original = self.root / runner.SOURCE_INPUTS
        source = original / "repository/me/manga/test.bin"
        source.parent.mkdir(parents=True)
        source.write_bytes(data)
        (original / "local-inputs.sha256").write_text(hashlib.sha256(data).hexdigest() + "  me/manga/test.bin\n")
        home = self.root / "owned"
        home.mkdir()
        for name, value in (("DEPENDENCY_MANIFEST_SHA256", runner.digest(original / "local-inputs.sha256")),
                            ("DEPENDENCY_FILE_COUNT", 1)):
            control = patch.object(runner, name, value)
            control.start()
            self.addCleanup(control.stop)
        return original, home

    def test_pinned_inputs_copy_idempotently_without_source_change(self):
        original, home = self.source_inputs()
        first = runner.provision_inputs(self.root, home)
        inode = (home / "repository/me/manga/test.bin").stat().st_ino
        self.assertEqual(first, runner.provision_inputs(self.root, home))
        self.assertEqual(first["files_verified"], 1)
        self.assertEqual(inode, (home / "repository/me/manga/test.bin").stat().st_ino)
        self.assertEqual((original / "repository/me/manga/test.bin").read_bytes(), b"verified fixture bytes")

    def test_bad_source_digest_copies_nothing(self):
        original, home = self.source_inputs()
        (original / "repository/me/manga/test.bin").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(list(home.iterdir()), [])

    def test_existing_different_input_is_preserved(self):
        _, home = self.source_inputs()
        target = home / "repository/me/manga/test.bin"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"newer local work")
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(target.read_bytes(), b"newer local work")

    def test_dependency_path_traversal_is_rejected(self):
        original, home = self.source_inputs()
        (original / "local-inputs.sha256").write_text("0" * 64 + "  ../out\n")
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)

    def test_dependency_manifest_link_is_rejected(self):
        _, home = self.source_inputs()
        outside = self.root / "outside"
        outside.write_text("keep me")
        (home / "local-inputs.sha256").symlink_to(outside)
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(outside.read_text(), "keep me")

    def test_cold_private_home_has_no_daemon_identity(self):
        self.assertEqual(runner.private_daemon_pids(self.root), [])

    def test_old_pid_never_treated_as_daemon_by_filename_alone(self):
        folder = self.root / "gradle-home/daemon/8.14.5"
        folder.mkdir(parents=True)
        (folder / f"daemon-{os.getpid()}.out.log").touch()
        self.assertEqual(runner.private_daemon_pids(self.root), [])

    def test_eight_gib_prerequisite_not_lowered(self):
        self.assertEqual(runner.MIN_FREE_BYTES, 8 * 1024**3)

    def test_historical_manifest_is_independently_pinned(self):
        self.assertEqual(runner.DEPENDENCY_MANIFEST_SHA256,
                         "c67fcc5fe64a9a795373c4683c7c1edd6407146e3cd07609fa7018a8a98db79a")
        self.assertEqual(runner.DEPENDENCY_FILE_COUNT, 18)

    def test_selectors_without_test_execution_rejected(self):
        for tasks in (["--continue"], ["testClasses", "--tests", "ExampleTest"]):
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                runner.require_tasks(tasks)

    def test_root_symlink_is_rejected(self):
        (self.root / "real").mkdir()
        (self.root / "link").symlink_to(self.root / "real", target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.safe_path(self.root / "link", "file")

    def test_absolute_root_ancestor_symlink_is_rejected(self):
        (self.root / "real/sub").mkdir(parents=True)
        (self.root / "link").symlink_to(self.root / "real", target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.safe_path(self.root / "link/sub", "file")

    def test_destination_repository_root_link_never_writes_outside(self):
        _, home = self.source_inputs()
        outside = self.root / "not-owned"
        outside.mkdir()
        (home / "repository").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(list(outside.iterdir()), [])

    def test_source_repository_root_link_is_rejected(self):
        original, home = self.source_inputs()
        outside = self.root / "not-owned"
        (original / "repository").rename(outside)
        (original / "repository").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(list(home.iterdir()), [])

    def test_source_manifest_link_is_rejected(self):
        original, home = self.source_inputs()
        manifest = original / "local-inputs.sha256"
        outside = self.root / "not-owned-manifest"
        manifest.rename(outside)
        manifest.symlink_to(outside)
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(list(home.iterdir()), [])

    def test_artifact_and_self_reported_manifest_replacement_is_rejected(self):
        original, home = self.source_inputs()
        replacement = b"not the original inputs"
        (original / "repository/me/manga/test.bin").write_bytes(replacement)
        (original / "local-inputs.sha256").write_text(hashlib.sha256(replacement).hexdigest() + "  me/manga/test.bin\n")
        with self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(list(home.iterdir()), [])

    def test_staging_checks_destination_after_copy(self):
        _, home = self.source_inputs()
        with patch.object(runner.shutil, "copyfileobj", side_effect=lambda _source, target: target.write(b"corrupt")):
            with self.assertRaises(ValueError):
                runner.provision_inputs(self.root, home)

    def test_postflight_does_not_repair_a_missing_staged_file(self):
        _, home = self.source_inputs()
        runner.provision_inputs(self.root, home)
        target = home / "repository/me/manga/test.bin"
        target.unlink()
        with self.assertRaises(ValueError):
            runner.dependency_inputs(self.root, home)
        self.assertFalse(target.exists())

    def test_wrong_exact_inventory_count_is_rejected(self):
        _, home = self.source_inputs()
        with patch.object(runner, "DEPENDENCY_FILE_COUNT", 18), self.assertRaises(ValueError):
            runner.provision_inputs(self.root, home)
        self.assertEqual(list(home.iterdir()), [])

    def tooling_manifest(self):
        pins = {}
        for relative in runner.OWNERSHIP_TOOLING:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC MODEL TOOL: " + relative)
            pins[relative] = runner.digest(path)
        return {"validation_tooling": pins}

    def test_all_shared_ownership_and_control_bytes_must_be_frozen(self):
        manifest = self.tooling_manifest()
        with patch.object(runner, "ROOT", self.root):
            runner.require_owned_tooling(manifest)
            for relative in runner.OWNERSHIP_TOOLING:
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    runner.require_owned_tooling({"validation_tooling": {
                        key: value for key, value in manifest["validation_tooling"].items() if key != relative}})

    def test_changed_shared_ownership_tool_cannot_use_an_old_freeze(self):
        manifest = self.tooling_manifest()
        (self.root / runner.OWNERSHIP_TOOLING[0]).write_text("MODEL changed shared helper")
        with patch.object(runner, "ROOT", self.root), self.assertRaises(ValueError):
            runner.require_owned_tooling(manifest)


def xml_report(name="example.FixtureTest", case='<testcase name="genuine case" classname="example.FixtureTest"/>',
               tests=1, failures=0, errors=0, skipped=0):
    return (f'<testsuite name="{name}" tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}">'
            + case + '</testsuite>')


class TestEvidenceControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="app29-junit-control-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def reports(self, data):
        relative = "reports/test-results/test/TEST-example.FixtureTest.xml"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        return [{"path": relative, "sha256": runner.digest(path)}]

    def test_actual_cases_and_exact_selector_are_required_and_recorded(self):
        result = runner.test_evidence(self.root, self.reports(xml_report()),
                                      ["test", "--tests", "example.FixtureTest"])
        self.assertEqual((result["status"], result["total"], result["failures"]), ("PASS", 1, 0))
        self.assertEqual(result["selectors"], {"example.FixtureTest": ["example.FixtureTest"]})
        self.assertEqual(len(result["identities"]), 1)

    def test_short_and_wildcard_class_selectors_have_real_cases(self):
        result = runner.test_evidence(self.root, self.reports(xml_report()),
                                      ["test", "--tests", "FixtureTest", "--tests", "example.*Test"])
        self.assertEqual(result["status"], "PASS")

    def test_static_reports_cannot_replace_junit(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, [{"path": "reports/reports/detekt/detekt.txt"}], ["test", "detekt"])

    def test_compile_only_is_explicitly_not_test_execution(self):
        result = runner.test_evidence(self.root, [], ["testClasses"])
        self.assertEqual((result["status"], result["total"]), ("NOT_REQUESTED", 0))

    def test_zero_actual_cases_rejected(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports(xml_report(case="", tests=0)), ["test"])

    def test_malformed_xml_rejected(self):
        with self.assertRaises(runner.ET.ParseError):
            runner.test_evidence(self.root, self.reports("<testsuite"), ["test"])

    def test_declared_counts_cannot_invent_cases(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports(xml_report(tests=2)), ["test"])

    def test_case_identity_must_match_suite(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports(xml_report(name="example.OtherTest")), ["test"])

    def test_unmatched_selected_class_rejected(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports(xml_report()), ["test", "--tests", "example.MissingTest"])

    def test_failure_error_and_skip_each_deny_pass(self):
        for key, tag in (("failures", "failure"), ("errors", "error"), ("skipped", "skipped")):
            with self.subTest(key=key):
                case = f'<testcase name="case" classname="example.FixtureTest"><{tag}/></testcase>'
                result = runner.test_evidence(self.root, self.reports(xml_report(case=case, **{key: 1})), ["test"])
                self.assertEqual((result["status"], result[key]), ("FAIL", 1))

    def test_hidden_failure_not_in_header_rejected(self):
        case = '<testcase name="case" classname="example.FixtureTest"><failure/></testcase>'
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports(xml_report(case=case)), ["test"])

    def test_xml_entity_declaration_rejected_before_parse(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports('<!DOCTYPE testsuite [<!ENTITY x "bad">]>' + xml_report()), ["test"])

    def test_utf16_and_utf32_cannot_hide_entity_declarations(self):
        data = '<!DOCTYPE testsuite [<!ENTITY x "expanded">]>' + xml_report()
        for encoding in ("utf-16", "utf-16-le", "utf-16-be", "utf-32", "utf-32-le", "utf-32-be"):
            with self.subTest(encoding=encoding):
                rows = self.reports(data)
                (self.root / rows[0]["path"]).write_bytes(data.encode(encoding))
                with self.assertRaises(ValueError):
                    runner.test_evidence(self.root, rows, ["test"])

    def test_non_utf8_xml_declaration_is_rejected(self):
        with self.assertRaises(ValueError):
            runner.test_evidence(self.root, self.reports('<?xml version="1.0" encoding="iso-8859-1"?>' + xml_report()), ["test"])

    def test_gradle_utf8_xml_declaration_remains_valid(self):
        result = runner.test_evidence(self.root, self.reports('<?xml version="1.0" encoding="UTF-8"?>' + xml_report()), ["test"])
        self.assertEqual(result["status"], "PASS")


class BarrierReceiptControls(unittest.TestCase):
    """Actual Commands/helper composition with an in-memory kernel, never real workers."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target in ("subprocess.Popen", "ctypes.CDLL", "os.kill", "os.killpg",
                       "os.pidfd_open", "signal.pidfd_send_signal"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("Real process/kernel operation forbidden")))

    def commands(self, children):
        ledger = {"failures": [], "owned_descendant_barriers": []}
        return runner.Commands(None, None, {}, ledger, children)

    def test_only_current_normal_return_can_authorize_absence(self):
        receipt = {"absent": True, "forced": False, "errors": []}
        children = SimpleNamespace(barrier=Mock(return_value=receipt), last_receipt=None)
        commands = self.commands(children)
        self.assertIs(commands.barrier("current"), receipt)
        self.assertEqual(commands.ledger["failures"], [])
        self.assertTrue(commands.ledger["owned_descendant_barriers"][0]["returned_normally"])

    def test_raw_exception_never_reuses_prior_clean_receipt(self):
        for failure in (KeyboardInterrupt(), OSError(), RuntimeError(), SystemExit()):
            with self.subTest(failure=type(failure).__name__):
                children = SimpleNamespace(barrier=Mock(side_effect=failure),
                                           last_receipt={"absent": True, "forced": False, "errors": []})
                commands = self.commands(children)
                self.assertIsNone(commands.barrier("failed-current"))
                entry = commands.ledger["owned_descendant_barriers"][0]
                self.assertFalse(entry["returned_normally"])
                self.assertIsNone(entry["receipt"])

    def test_even_clean_exception_receipt_is_only_diagnostic(self):
        receipt = {"absent": True, "forced": False, "errors": []}
        commands = self.commands(SimpleNamespace(barrier=Mock(side_effect=OwnershipError("MODEL", receipt))))
        self.assertIsNone(commands.barrier("failed-current"))
        self.assertIs(commands.ledger["owned_descendant_barriers"][0]["receipt"], receipt)
        self.assertFalse(commands.ledger["owned_descendant_barriers"][0]["returned_normally"])

    def test_missing_or_malformed_current_receipt_cannot_authorize(self):
        for receipt in (None, True, {}, {"absent": True},
                        {"absent": True, "forced": False},
                        {"absent": True, "forced": 0, "errors": []},
                        {"absent": True, "forced": False, "errors": None}):
            with self.subTest(receipt=receipt):
                commands = self.commands(SimpleNamespace(barrier=Mock(return_value=receipt)))
                self.assertIsNone(commands.barrier("malformed-current"))
                self.assertTrue(commands.ledger["failures"])

    def test_actual_helper_new_descendant_plus_interruption_cannot_reuse_absence(self):
        for boundary in ("clock", "sleep"):
            with self.subTest(boundary=boundary):
                kernel = FakeKernel()
                scope = owned.OwnedChildren(kernel)
                scope.activate()
                scope.barrier(0, 0, 0)
                kernel.rows[101] = row(101, pgid=701, session=801)

                def interrupted(*_args):
                    raise KeyboardInterrupt()

                if boundary == "clock":
                    kernel.clock = interrupted
                else:
                    kernel.on_sleep = interrupted
                commands = self.commands(scope)
                self.assertIsNone(commands.barrier("before-output-deletion"))
                self.assertIn(101, kernel.rows)
                self.assertFalse(commands.ledger["owned_descendant_barriers"][0]["returned_normally"])
                kernel.clock = lambda: kernel.time
                kernel.on_sleep = None
                kernel.remove(101)
                scope.restore()
                self.assertFalse(scope.active)


class BatchControls(unittest.TestCase):
    """Synthetic orchestration only: every Popen, census and signal is replaced; no worker starts."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="app29-orchestration-control-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "kira-backend").mkdir()
        (self.root / "review/working").mkdir(parents=True)
        self.home = self.root / runner.BUILD_HOME
        self.build = self.home / "backend-build"
        self.evidence = self.root / "review/working/app-29-control"
        self.manifest = {"validation_scope": "SYNTHETIC MODEL ONLY", "evidence_class_names": ["Fixture"]}
        self.launched, self.handles, self.waits = [], [], []
        self.next_pid = 9000000
        self.validation_wait = []
        self.create_xml = True
        self.validation_exit = 0
        self.stop_count = 0
        self.fail_first_stop_spawn = False
        self.scope_events, self.barrier_effects, self.child_errors = [], [], []
        self.children = SimpleNamespace(active=False, last_receipt={"absent": False, "forced": False, "errors": []})
        self.children.activate = Mock(side_effect=self.fake_activate)
        self.children.track = Mock(side_effect=self.fake_track)
        self.children.signal_owned = Mock(return_value=True)
        self.children.barrier = Mock(side_effect=self.fake_barrier)
        self.children.restore = Mock(side_effect=self.fake_restore)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch.object(runner, "ROOT", self.root))
        self.stack.enter_context(patch.object(runner.platform, "system", return_value="Linux"))
        self.stack.enter_context(patch.object(runner.platform, "platform", return_value="MODEL-Linux"))
        self.stack.enter_context(patch.object(runner.shutil, "disk_usage", return_value=SimpleNamespace(free=12 * 1024**3)))
        self.validator = self.stack.enter_context(patch.object(runner.inventory, "validate_manifest", return_value=self.manifest))
        self.tooling_check = self.stack.enter_context(patch.object(runner, "require_owned_tooling"))
        self.scope_constructor = self.stack.enter_context(patch.object(runner, "OwnedChildren", return_value=self.children))
        self.stack.enter_context(patch.object(runner.inventory, "issue_diff", return_value=b"fixture-only-diff"))
        self.stack.enter_context(patch.object(runner, "provision_inputs", return_value={"fixture": True}))
        self.dependencies = self.stack.enter_context(patch.object(runner, "dependency_inputs", return_value={"fixture": True}))
        self.stack.enter_context(patch.object(runner, "build_environment", return_value=(
            {"JAVA_HOME": str(self.root / "java"), "GRADLE_USER_HOME": str(self.home / "gradle-home")}, {"fixture": True})))
        self.daemons = self.stack.enter_context(patch.object(runner, "private_daemon_pids", return_value=[]))
        self.stack.enter_context(patch.object(runner, "process_group_members", return_value=[]))
        self.numeric_signals = self.stack.enter_context(patch.object(
            runner.os, "killpg", side_effect=AssertionError("Numeric group signalling is forbidden")))
        for target in ("ctypes.CDLL", "os.kill", "os.pidfd_open", "signal.pidfd_send_signal"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("Real kernel operation forbidden")))
        self.stack.enter_context(patch("signal.signal", return_value=runner.signal.SIG_DFL))
        self.signals = self.children.signal_owned
        self.popen = self.stack.enter_context(patch.object(runner.subprocess, "Popen", side_effect=self.fake_popen))

    def fake_activate(self):
        self.scope_events.append("activate")
        self.children.active = True
        return {"MODEL": True, "previous_setting": 0}

    def fake_track(self):
        self.scope_events.append("track")
        self.assertTrue(self.children.active)
        return [{"pid": handle.pid, "start_ticks": handle.pid, "boot_id": "MODEL", "state": "S"}
                for handle in self.handles if handle.poll() is None]

    def fake_barrier(self):
        self.scope_events.append("barrier")
        self.assertTrue(self.children.active)
        effect = self.barrier_effects.pop(0) if self.barrier_effects else None
        if isinstance(effect, BaseException):
            receipt = getattr(effect, "receipt", None)
            if isinstance(receipt, dict):
                self.children.last_receipt = receipt
                self.child_errors.extend(receipt.get("errors", []))
            raise effect
        receipt = {"absent": True, "forced": self.signals.called, "errors": self.child_errors.copy()}
        if effect is not None:
            receipt.update(effect)
        self.children.last_receipt = receipt
        if receipt["errors"]:
            raise OwnershipError("MODEL sticky earlier ownership error", receipt)
        return receipt

    def fake_restore(self):
        self.scope_events.append("restore")
        self.children.active = False
        return {"active": False, "restored_previous_setting": 0}

    def generated(self):
        package = "me/manga/kira/backend/common/infrastructure/persistence/"
        for path in ("classes/kotlin/main/" + package + "Fixture.class",
                     "classes/kotlin/test/" + package + "PgRequireErrorHandlerTest.class",
                     "reports/detekt/detekt.txt", "reports/ktlint/ktlintTestSourceSetCheck/report.txt"):
            target = self.build / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"SYNTHETIC MODEL - NOT JVM BYTECODE")
        if self.create_xml:
            target = self.build / "test-results/test/TEST-example.FixtureTest.xml"
            target.parent.mkdir(parents=True)
            target.write_text(xml_report())

    def fake_popen(self, command, **options):
        self.assertTrue(self.children.active)
        self.assertTrue(options["start_new_session"])
        self.next_pid += 1
        name = ("stop" if "--stop" in command else "validation") if command[0] == "./gradlew" else Path(command[0]).name
        self.launched.append(name)
        self.scope_events.append("launch:" + name)
        if name == "stop":
            self.stop_count += 1
            if self.fail_first_stop_spawn and self.stop_count == 1:
                raise OSError("MODEL stop spawn failure")
        if name == "validation":
            self.generated()
        handle = SimpleNamespace(pid=self.next_pid, returncode=None)
        def wait(timeout=None):
            self.waits.append((name, timeout))
            if name == "validation" and self.validation_wait:
                effect = self.validation_wait.pop(0)
                if isinstance(effect, BaseException):
                    raise effect
            handle.returncode = self.validation_exit if name == "validation" else 0
            return handle.returncode
        handle.wait = wait
        handle.poll = lambda: handle.returncode
        self.handles.append(handle)
        return handle

    def invoke(self):
        return runner.main(["--manifest-sha256", "0" * 64, "fixture.json", "app-29-control", "test", "--tests",
                            "example.FixtureTest", "ktlintCheck", "detekt", "--continue"])

    def result(self):
        return json.loads((self.evidence / "result.json").read_text())

    def assert_stops_and_lock_released(self):
        self.assertEqual(self.launched.count("stop"), 2)
        with (self.home / "batch.lock").open("a") as lock:
            runner.fcntl.flock(lock, runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)
        self.numeric_signals.assert_not_called()

    def test_positive_model_preserves_real_junit_and_cleans_owned_outputs(self):
        self.assertEqual(self.invoke(), 0)
        self.assertEqual(self.result()["test_evidence"]["total"], 1)
        self.assertTrue(self.result()["outputs_absent"])
        self.assertEqual(self.result()["runner_status"], "PASS")
        self.assert_stops_and_lock_released()

    def test_zero_xml_is_not_pass_even_with_static_reports_and_bytecode(self):
        self.create_xml = False
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.result()["runner_status"], "FAIL")
        self.assertIn("test-evidence", [row["stage"] for row in self.result()["failures"]])
        self.assert_stops_and_lock_released()

    def test_census_error_preserves_outputs_and_still_captures_and_final_stops(self):
        self.daemons.side_effect = [[], OSError("MODEL census unavailable"), []]
        self.assertEqual(self.invoke(), 1)
        result = self.result()
        self.assertTrue(self.build.is_dir())
        self.assertTrue(result["capture_complete"])
        self.assertIsNone(result["private_daemon_pids_after_stop"])
        self.assertTrue(result["outputs_preserved_for_recovery"])
        self.assert_stops_and_lock_released()

    def test_final_census_failure_is_not_absence_or_pass(self):
        self.daemons.side_effect = [[], [], OSError("MODEL census unavailable")]
        self.assertEqual(self.invoke(), 1)
        self.assertIsNone(self.result()["private_daemon_pids_after_clean"])
        self.assert_stops_and_lock_released()

    def test_post_popen_checkpoint_failure_terminates_and_joins_owned_process(self):
        original, failed = runner.Commands.checkpoint, []
        def checkpoint(commands):
            if not failed and any(row["name"] == "validation" and "pid" in row for row in commands.ledger["commands"]):
                failed.append(True)
                raise OSError("MODEL post-spawn evidence failure")
            original(commands)
        with patch.object(runner.Commands, "checkpoint", checkpoint):
            self.assertEqual(self.invoke(), 1)
        self.assertTrue(any(name == "validation" for name, _ in self.waits))
        self.signals.assert_called()
        entry = next(row for row in self.result()["commands"] if row["name"] == "validation")
        self.assertTrue(entry["joined"])
        self.assertTrue(entry["termination_requested"])
        self.assert_stops_and_lock_released()

    def test_timeout_terminates_and_joins_then_final_stops(self):
        self.validation_wait = [subprocess.TimeoutExpired("MODEL", 1)]
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(sum(name == "validation" for name, _ in self.waits), 2)
        self.signals.assert_called()
        self.assert_stops_and_lock_released()

    def test_interrupt_terminates_and_joins_then_final_stops(self):
        self.validation_wait = [KeyboardInterrupt()]
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(sum(name == "validation" for name, _ in self.waits), 2)
        self.signals.assert_called()
        self.assert_stops_and_lock_released()

    def test_timeout_escalates_only_pidfd_anchored_descendants_and_joins(self):
        self.validation_wait = [subprocess.TimeoutExpired("MODEL", 1), subprocess.TimeoutExpired("MODEL", 20)]
        self.assertEqual(self.invoke(), 1)
        self.assertEqual([call.args[1] for call in self.signals.call_args_list], [runner.signal.SIGTERM, runner.signal.SIGKILL])
        self.assertTrue(all(call.args[0]["boot_id"] == "MODEL" for call in self.signals.call_args_list))
        self.assertEqual(sum(name == "validation" for name, _ in self.waits), 3)
        self.assert_stops_and_lock_released()

    def test_capture_failure_retains_source_outputs_and_final_stop(self):
        with patch.object(runner, "capture_outputs", side_effect=OSError("MODEL capture failure")):
            self.assertEqual(self.invoke(), 1)
        self.assertTrue(self.build.is_dir())
        self.assertFalse(self.result()["capture_complete"])
        self.assert_stops_and_lock_released()

    def test_reaped_group_residue_is_not_signalled_by_an_old_numeric_pid(self):
        with patch.object(runner, "process_group_members", return_value=[9999999]):
            self.assertEqual(self.invoke(), 1)
        self.assertTrue(self.build.is_dir())
        self.signals.assert_not_called()
        self.assert_stops_and_lock_released()

    def test_cleanup_failure_does_not_skip_final_stop(self):
        with patch.object(runner, "clean_outputs", side_effect=OSError("MODEL cleanup failure")):
            self.assertEqual(self.invoke(), 1)
        self.assertTrue(self.build.is_dir())
        self.assert_stops_and_lock_released()

    def test_persistent_evidence_failure_cannot_prevent_shutdown_commands(self):
        with patch.object(runner.Commands, "checkpoint", side_effect=OSError("MODEL disk unavailable")):
            self.assertEqual(self.invoke(), 1)
        self.assertNotIn("validation", self.launched)
        self.assert_stops_and_lock_released()

    def test_stop_log_failure_still_starts_owned_stop_without_log(self):
        original = Path.open
        def failing_log(path, *args, **kwargs):
            if path.name in {"stop-after-validation.log", "stop-after-clean.log"}:
                raise OSError("MODEL log unavailable")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", failing_log):
            self.assertEqual(self.invoke(), 1)
        self.assert_stops_and_lock_released()

    def test_stop_spawn_failure_still_attempts_final_stop(self):
        self.fail_first_stop_spawn = True
        self.assertEqual(self.invoke(), 1)
        self.assert_stops_and_lock_released()

    def test_source_postflight_error_still_returns_failure_with_cleanup_receipt(self):
        self.validator.side_effect = [self.manifest, self.manifest, OSError("MODEL source drift")]
        self.assertEqual(self.invoke(), 1)
        self.assertFalse(self.result()["frozen_inputs_preserved"])
        self.assertTrue(self.result()["outputs_absent"])
        self.assert_stops_and_lock_released()

    def test_dependency_postflight_replacement_cannot_pass(self):
        self.dependencies.side_effect = [{}, ValueError("MODEL changed staged dependency")]
        self.assertEqual(self.invoke(), 1)
        self.assertFalse(self.result()["dependency_inputs_preserved"])
        self.assert_stops_and_lock_released()

    def test_gradle_nonzero_is_failure_despite_complete_reports(self):
        self.validation_exit = 1
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.result()["test_evidence"]["status"], "PASS")
        self.assertEqual(self.result()["runner_status"], "FAIL")
        self.assert_stops_and_lock_released()

    def test_preexisting_output_is_never_overwritten_or_removed(self):
        self.build.mkdir(parents=True)
        (self.home / "OWNER").write_text(runner.OWNER + "\n")
        prior = self.build / "keep-existing-work"
        prior.write_text("unchanged")
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(prior.read_text(), "unchanged")
        self.assertEqual(self.launched, [])

    def test_failure_before_command_releases_lock(self):
        self.daemons.side_effect = OSError("MODEL preflight census error")
        with self.assertRaises(OSError):
            self.invoke()
        self.assertEqual(self.launched, [])
        with (self.home / "batch.lock").open("a") as lock:
            runner.fcntl.flock(lock, runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)

    def test_scope_activates_before_popen_and_barriers_cover_every_phase_before_restore(self):
        capture = runner.capture_outputs
        clean = runner.clean_outputs
        def captured(*args):
            self.scope_events.append("capture")
            return capture(*args)
        def cleaned(*args):
            self.scope_events.append("delete")
            return clean(*args)
        with patch.object(runner, "capture_outputs", side_effect=captured), patch.object(runner, "clean_outputs", side_effect=cleaned):
            self.assertEqual(self.invoke(), 0)
        self.assertEqual(self.scope_events, [
            "activate", "launch:validation", "track", "launch:stop", "track", "barrier", "capture",
            "launch:javap", "track", "barrier", "delete", "launch:stop", "track", "barrier",
            "launch:git", "track", "launch:jps", "track", "barrier", "barrier", "restore"])
        self.assertTrue(self.result()["child_scope_restored"])
        self.assertEqual([row["stage"] for row in self.result()["owned_descendant_barriers"]], [
            "before-capture", "before-output-deletion", "after-final-stop", "after-postflight-commands",
            "unconditional-final-barrier"])
        self.assert_stops_and_lock_released()

    def test_unknown_complete_descendant_census_blocks_capture_and_deletion_but_not_stops(self):
        receipt = {"absent": False, "forced": False, "errors": [{"stage": "census", "type": "OSError"}]}
        self.barrier_effects = [OwnershipError("MODEL unknown descendant census", receipt)]
        with patch.object(runner, "capture_outputs") as capture, patch.object(runner, "clean_outputs") as clean:
            self.assertEqual(self.invoke(), 1)
        capture.assert_not_called()
        clean.assert_not_called()
        self.assertTrue(self.build.is_dir())
        self.assertFalse(self.result()["capture_complete"])
        self.assertTrue(self.result()["outputs_preserved_for_recovery"])
        self.children.restore.assert_called_once()
        self.assert_stops_and_lock_released()

    def test_forced_but_absent_children_allow_capture_not_pass_or_deletion(self):
        self.barrier_effects = [{"forced": True}] * 5
        self.assertEqual(self.invoke(), 1)
        self.assertTrue(self.result()["capture_complete"])
        self.assertTrue(self.build.is_dir())
        self.assertTrue(self.result()["outputs_preserved_for_recovery"])
        self.assert_stops_and_lock_released()

    def test_javap_descendant_residue_denies_deletion_after_capture(self):
        self.barrier_effects = [None, {"absent": False}]
        self.assertEqual(self.invoke(), 1)
        self.assertTrue(self.result()["capture_complete"])
        self.assertTrue(self.build.is_dir())
        self.assert_stops_and_lock_released()

    def test_raw_predelete_interrupt_keeps_outputs_despite_prior_clean_receipt(self):
        self.barrier_effects = [None, KeyboardInterrupt()]
        with patch.object(runner, "clean_outputs") as clean:
            self.assertEqual(self.invoke(), 1)
        clean.assert_not_called()
        self.assertTrue(self.result()["capture_complete"])
        self.assertTrue(self.result()["outputs_preserved_for_recovery"])
        self.assertTrue(self.build.is_dir())
        entry = self.result()["owned_descendant_barriers"][1]
        self.assertFalse(entry["returned_normally"])
        self.assertIsNone(entry["receipt"])
        self.assert_stops_and_lock_released()

    def test_clean_exception_receipt_cannot_authorize_capture_or_deletion(self):
        receipt = {"absent": True, "forced": False, "errors": []}
        self.barrier_effects = [OwnershipError("MODEL current operation failed", receipt)]
        with patch.object(runner, "capture_outputs") as capture, patch.object(runner, "clean_outputs") as clean:
            self.assertEqual(self.invoke(), 1)
        capture.assert_not_called()
        clean.assert_not_called()
        self.assertTrue(self.build.is_dir())
        self.assert_stops_and_lock_released()

    def test_forced_capture_receipt_still_denies_deletion_if_later_receipt_is_clean(self):
        self.barrier_effects = [{"forced": True}, {"forced": False}]
        self.assertEqual(self.invoke(), 1)
        self.assertTrue(self.result()["capture_complete"])
        self.assertTrue(self.build.is_dir())
        self.assert_stops_and_lock_released()

    def test_actual_helper_interrupt_after_javap_never_deletes_with_live_descendant(self):
        kernel = FakeKernel()
        scope = owned.OwnedChildren(kernel)
        self.children = scope
        self.scope_constructor.return_value = scope
        original_popen = self.fake_popen
        interrupted = []

        def fake_popen(command, **options):
            handle = original_popen(command, **options)
            if Path(command[0]).name == "javap":
                original_wait = handle.wait

                def completed_javap(timeout=None):
                    result = original_wait(timeout)
                    kernel.rows[777] = row(777, pgid=1777, session=2777)
                    return result

                handle.wait = completed_javap
            return handle

        def fake_sleep(model):
            if 777 in model.rows:
                if not interrupted:
                    interrupted.append(True)
                    raise KeyboardInterrupt()
                model.remove(777)

        kernel.on_sleep = fake_sleep
        self.popen.side_effect = fake_popen
        with patch.object(runner, "clean_outputs") as clean:
            self.assertEqual(self.invoke(), 1)
        clean.assert_not_called()
        self.assertTrue(self.build.is_dir())
        self.assertTrue(self.result()["capture_complete"])
        self.assertTrue(self.result()["outputs_preserved_for_recovery"])
        self.assertFalse(self.result()["owned_descendant_barriers"][1]["returned_normally"])
        self.assertNotIn(777, kernel.rows)
        self.assertFalse(scope.active)
        self.assert_stops_and_lock_released()

    def test_postflight_descendant_failure_is_not_a_pass(self):
        self.barrier_effects = [None, None, None, {"absent": False}]
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.result()["runner_status"], "FAIL")
        self.assert_stops_and_lock_released()

    def test_final_fallback_barrier_failure_denies_previously_clean_outcome(self):
        self.barrier_effects = [None, None, None, None, {"absent": False}]
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.result()["runner_status"], "FAIL")
        self.children.restore.assert_called_once()
        self.assert_stops_and_lock_released()

    def test_restore_failure_cannot_follow_a_finalized_pass(self):
        self.children.restore.side_effect = OwnershipError("MODEL restore failed")
        self.assertEqual(self.invoke(), 1)
        self.assertFalse(self.result()["child_scope_restored"])
        self.assertEqual(self.result()["runner_status"], "FAIL")
        self.assert_stops_and_lock_released()

    def test_partial_activation_failure_still_restores_and_attempts_both_stops(self):
        def partial_acquire():
            self.fake_activate()
            raise OwnershipError("MODEL acquisition follow-up failure")
        self.children.activate.side_effect = partial_acquire
        self.assertEqual(self.invoke(), 1)
        self.assertNotIn("validation", self.launched)
        self.children.restore.assert_called_once()
        self.assert_stops_and_lock_released()

    def test_unacquired_scope_never_launches_commands_and_still_releases_lock(self):
        self.children.activate.side_effect = OwnershipError("MODEL preexisting children")
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.launched, [])
        self.children.barrier.assert_not_called()
        self.children.restore.assert_called_once()
        with (self.home / "batch.lock").open("a") as lock:
            runner.fcntl.flock(lock, runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)

    def test_actual_helper_applied_activation_interrupt_restores_without_launching(self):
        kernel = FakeKernel()
        scope = owned.OwnedChildren(kernel)
        self.children = scope
        self.scope_constructor.return_value = scope

        def applied_then_interrupted(value):
            kernel.settings.append(value)
            if value == 1:
                raise KeyboardInterrupt()

        kernel.set_subreaper = applied_then_interrupted
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.launched, [])
        self.assertEqual(kernel.settings, [1, 0])
        self.assertFalse(scope.active)
        self.assertFalse(scope.restoration_pending)
        self.assertTrue(self.result()["child_scope_restored"])
        with (self.home / "batch.lock").open("a") as lock:
            runner.fcntl.flock(lock, runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)

    def test_actual_helper_failed_activation_readback_forbids_even_cleanup_popen(self):
        kernel = FakeKernel()
        scope = owned.OwnedChildren(kernel)
        self.children = scope
        self.scope_constructor.return_value = scope
        kernel.get_subreaper = Mock(side_effect=[0, 0, 1, 0])
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.launched, [])
        self.assertEqual(kernel.settings, [1, 0])
        self.assertFalse(scope.active)
        self.assertFalse(scope.restoration_pending)
        self.assertTrue(self.result()["child_scope_restored"])
        with (self.home / "batch.lock").open("a") as lock:
            runner.fcntl.flock(lock, runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)

    def test_post_popen_tracking_failure_is_lifecycle_protected(self):
        initial = self.fake_track
        failures = []
        def failed_track():
            if not failures:
                failures.append(True)
                raise OwnershipError("MODEL track failure after Popen")
            return initial()
        self.children.track.side_effect = failed_track
        self.assertEqual(self.invoke(), 1)
        entry = next(row for row in self.result()["commands"] if row["name"] == "validation")
        self.assertTrue(entry["joined"])
        self.assertTrue(entry["termination_requested"])
        self.assert_stops_and_lock_released()

    def test_orchestration_exception_still_runs_fallback_barrier_and_restore(self):
        original = runner.Commands.barrier
        def exceptional(commands, stage):
            if stage == "before-capture":
                raise RuntimeError("MODEL unexpected outer orchestration error")
            return original(commands, stage)
        with patch.object(runner.Commands, "barrier", exceptional):
            self.assertEqual(self.invoke(), 1)
        self.assertEqual([row["stage"] for row in self.result()["owned_descendant_barriers"]], ["unconditional-final-barrier"])
        self.children.restore.assert_called_once()
        self.assertTrue(self.build.is_dir())
        self.assert_stops_and_lock_released()

    def test_missing_frozen_ownership_tooling_refuses_before_home_or_process(self):
        self.tooling_check.side_effect = ValueError("MODEL missing helper pin")
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertFalse(self.home.exists())
        self.assertEqual(self.launched, [])
        self.scope_constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
