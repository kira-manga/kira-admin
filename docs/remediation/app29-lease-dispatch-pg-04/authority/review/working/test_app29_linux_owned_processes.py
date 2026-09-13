#!/usr/bin/env python3
"""No-service controls: fake process tables/syscalls only; never enable real prctl."""

import copy
import importlib.util
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).absolute().parent))
import app29_linux_owned_processes as owned


BOOT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def row(pid, ppid=100, *, ticks=None, state="S", pgid=None, session=None):
    return {"pid": pid, "ppid": ppid, "pgid": pid if pgid is None else pgid,
            "session": pid if session is None else session,
            "start_ticks": pid * 10 if ticks is None else ticks, "state": state, "boot_id": BOOT}


class FakeKernel:
    """An in-memory Linux process tree. Even signal 0 and pidfds are fake."""
    def __init__(self):
        self.rows = {100: row(100, 1)}
        self.time = 0.0
        self.previous = 0
        self.settings = []
        self.opened = {}
        self.closed = []
        self.sent = []
        self.nextfd = 1000
        self.table_calls = 0
        self.on_table = None
        self.on_sleep = None
        self.on_open = None
        self.on_send = None
        self.on_close = None
        self.on_setting = None
        self.supports = True

    def supported(self):
        return self.supports

    def getpid(self):
        return 100

    def clock(self):
        return self.time

    def sleep(self, amount):
        self.time += amount
        if self.on_sleep:
            self.on_sleep(self)

    def table(self):
        self.table_calls += 1
        if self.on_table:
            self.on_table(self)
        return copy.deepcopy(self.rows)

    def get_subreaper(self):
        return self.settings[-1] if self.settings else self.previous

    def set_subreaper(self, value):
        if self.on_setting:
            self.on_setting(self, value)
        self.settings.append(value)

    def open_pidfd(self, pid):
        if pid not in self.rows:
            raise ProcessLookupError()
        fd = self.nextfd
        self.nextfd += 1
        self.opened[fd] = copy.deepcopy(self.rows[pid])
        if self.on_open:
            self.on_open(self, pid)
        return fd

    def close_pidfd(self, fd):
        self.closed.append(fd)
        if self.on_close:
            self.on_close(self, fd)

    def exited(self, fd):
        before = self.opened[fd]
        current = self.rows.get(before["pid"])
        return not owned.same_identity(before, current) or current["state"] == "Z"

    def send(self, fd, signum):
        before = self.opened[fd]
        self.sent.append((before["pid"], signum))
        if self.on_send:
            self.on_send(self, before["pid"], signum)

    def reap(self, pid):
        current = self.rows.get(pid)
        if current and current["state"] == "Z" and current["ppid"] == 100:
            self.remove(pid)
            return True
        return False

    def remove(self, pid):
        self.rows.pop(pid, None)
        for child in self.rows.values():
            if child["ppid"] == pid:
                child["ppid"] = 100  # Private subreaper adopts every remaining descendant.

    def terminate(self, pid):
        self.rows[pid]["state"] = "Z"
        for child in self.rows.values():
            if child["ppid"] == pid:
                child["ppid"] = 100


class OwnershipControls(unittest.TestCase):
    def setUp(self):
        # Any accidental real process/kernel mutation is a test failure.
        for target in ("os.kill", "os.killpg", "os.pidfd_open", "signal.pidfd_send_signal",
                       "subprocess.Popen", "ctypes.CDLL"):
            patcher = mock.patch(target, side_effect=AssertionError("real syscall forbidden"))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.ops = FakeKernel()
        self.scope = owned.OwnedChildren(self.ops)

    def activate_child(self, *children):
        self.scope.activate()
        for child in children or (row(101),):
            self.ops.rows[child["pid"]] = child
        self.scope.track()

    def assert_fds_closed(self):
        self.assertEqual(set(self.ops.opened), set(self.ops.closed))
        self.assertEqual(len(self.ops.closed), len(set(self.ops.closed)))

    def test_import_and_constructor_do_not_mutate_kernel(self):
        spec = importlib.util.spec_from_file_location("inert_owned_helper", Path(owned.__file__))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertFalse(module.OwnedChildren().active)
        self.assertEqual(self.ops.settings, [])

    def test_activate_probes_self_pidfd_and_restores_previous_zero(self):
        proof = self.scope.activate()
        self.assertEqual(proof["parent"], row(100, 1))
        self.assertTrue(self.scope.active)
        self.assertEqual(self.ops.sent, [(100, 0)])
        self.assertEqual(self.scope.barrier(0, 0, 0)["absent"], True)
        self.assertFalse(self.scope.last_receipt["forced"])
        self.scope.restore()
        self.assertEqual(self.ops.settings, [1, 0])
        self.assert_fds_closed()

    def test_restore_preserves_preexisting_subreaper_value_one(self):
        self.ops.previous = 1
        self.scope.activate()
        self.scope.restore()
        self.assertEqual(self.ops.settings, [1, 1])

    def test_initial_children_refused_without_signals_or_setting(self):
        self.ops.rows[101] = row(101)
        self.ops.rows[102] = row(102, 101, session=777)
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertFalse(self.scope.active)
        self.assertEqual((self.ops.sent, self.ops.settings, self.ops.opened), ([], [], {}))

    def test_missing_parent_refused(self):
        self.ops.rows.clear()
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertEqual(self.ops.settings, [])

    def test_unsupported_pidfd_refused_before_setting(self):
        self.ops.supports = False
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertEqual(self.ops.settings, [])

    def test_probe_error_closes_fd_and_prevents_activation(self):
        self.ops.on_send = lambda *_: (_ for _ in ()).throw(PermissionError())
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertFalse(self.scope.active)
        self.assertEqual(self.ops.settings, [])
        self.assert_fds_closed()

    def test_setting_failure_is_not_active(self):
        self.ops.on_setting = lambda *_: (_ for _ in ()).throw(OSError())
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertFalse(self.scope.active)
        self.assert_fds_closed()

    def test_failure_after_activation_retains_active_scope_for_cleanup(self):
        def fail_after_set(kernel):
            if kernel.table_calls == 3:
                raise PermissionError()
        self.ops.on_table = fail_after_set
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertTrue(self.scope.active)
        with self.assertRaises(owned.OwnershipError) as error:
            self.scope.barrier(0, 0, 0)
        self.assertFalse(error.exception.receipt["absent"])
        self.assertTrue(error.exception.receipt["absence_observed_before_error"])
        self.scope.restore()
        self.assertFalse(self.scope.active)
        self.assert_fds_closed()

    def test_double_activation_refused(self):
        self.scope.activate()
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertEqual(self.ops.settings, [1])

    def test_track_anchors_full_tree_including_detached_session(self):
        self.activate_child(row(101), row(102, 101, pgid=999, session=999), row(103, 102))
        self.ops.rows[555] = row(555, 1)
        self.assertEqual({item["pid"] for item in self.scope.track()}, {101, 102, 103})
        self.assertEqual({item["pid"] for item in self.scope.observed.values()}, {101, 102, 103})

    def test_natural_exit_adoption_and_zombie_reaping_need_no_signal(self):
        self.activate_child(row(101), row(102, 101, session=900))
        self.ops.terminate(101)
        self.ops.terminate(102)
        proof = self.scope.barrier(.2, .2, .2)
        self.assertTrue(proof["absent"])
        self.assertFalse(proof["forced"])
        self.assertEqual(set(proof["reaped"]), {101, 102})
        self.assertEqual(self.ops.sent, [(100, 0)])

    def test_term_forced_absence_is_sticky_and_not_pass(self):
        self.activate_child(row(101), row(102, 101, session=900))
        self.ops.on_send = lambda kernel, pid, sig: kernel.terminate(pid)
        proof = self.scope.barrier(0, .3, .3)
        self.assertTrue(proof["absent"] and proof["forced"])
        self.assertEqual(self.ops.sent[1:], [(102, signal.SIGTERM), (101, signal.SIGTERM)])
        self.assertTrue(self.scope.barrier(0, 0, 0)["forced"])
        self.assert_fds_closed()

    def test_kill_escalation_is_once_per_identity_per_phase(self):
        self.activate_child()
        def only_kill(kernel, pid, sig):
            if sig == signal.SIGKILL:
                kernel.terminate(pid)
        self.ops.on_send = only_kill
        proof = self.scope.barrier(0, .15, .2)
        self.assertTrue(proof["absent"] and proof["forced"])
        self.assertEqual(self.ops.sent[1:], [(101, signal.SIGTERM), (101, signal.SIGKILL)])
        self.assertLessEqual(self.ops.time, .4)
        self.assert_fds_closed()

    def test_new_child_created_during_termination_is_adopted_and_disposed(self):
        self.activate_child()
        def exit_and_fork(kernel, pid, sig):
            if pid == 101:
                kernel.rows[102] = row(102, 101, session=998)
            kernel.terminate(pid)
        self.ops.on_send = exit_and_fork
        proof = self.scope.barrier(0, .4, .2)
        self.assertTrue(proof["absent"])
        self.assertEqual({item["pid"] for item in proof["observed"]}, {101, 102})
        self.assertEqual({pid for pid, sig in self.ops.sent if sig}, {101, 102})

    def test_stubborn_residue_fails_boundedly_and_blocks_restore(self):
        self.activate_child()
        with self.assertRaises(owned.OwnershipError) as error:
            self.scope.barrier(.1, .1, .1)
        self.assertFalse(error.exception.receipt["absent"])
        self.assertTrue(error.exception.receipt["forced"])
        self.assertLessEqual(self.ops.time, .31)
        self.assertEqual(self.ops.sent[1:], [(101, signal.SIGTERM), (101, signal.SIGKILL)])
        with self.assertRaises(owned.OwnershipError):
            self.scope.restore()
        self.assertTrue(self.scope.active)
        self.assert_fds_closed()

    def test_pid_reuse_before_open_never_signals_replacement(self):
        self.activate_child()
        before = row(101)
        self.ops.rows[101] = row(101, 1, ticks=9999)
        with self.assertRaises(owned.OwnershipError):
            self.scope.signal_owned(before, signal.SIGTERM)
        self.assertEqual(self.ops.sent, [(100, 0)])
        self.assert_fds_closed()

    def test_pid_reuse_after_pidfd_open_never_signals_replacement(self):
        self.activate_child()
        self.ops.on_open = lambda kernel, pid: kernel.rows.update({pid: row(pid, 1, ticks=9999)})
        with self.assertRaises(owned.OwnershipError):
            self.scope.signal_owned(row(101), signal.SIGTERM)
        self.assertEqual(self.ops.sent, [(100, 0)])
        self.assert_fds_closed()

    def test_exit_during_pidfd_open_closes_without_signal(self):
        self.activate_child()
        self.ops.on_open = lambda kernel, pid: kernel.remove(pid)
        self.assertFalse(self.scope.signal_owned(row(101), signal.SIGTERM))
        self.assertEqual(self.ops.sent, [(100, 0)])
        self.assert_fds_closed()

    def test_changed_parent_identity_blocks_signal_and_restore(self):
        self.activate_child()
        self.ops.rows[100]["start_ticks"] += 1
        with self.assertRaises(owned.OwnershipError):
            self.scope.signal_owned(row(101), signal.SIGTERM)
        with self.assertRaises(owned.OwnershipError):
            self.scope.restore()
        self.assertEqual(self.ops.sent, [(100, 0)])

    def test_live_anchored_process_outside_tree_is_unknown_not_absence(self):
        self.activate_child()
        self.ops.rows[101]["ppid"] = 1
        with self.assertRaises(owned.OwnershipError) as error:
            self.scope.barrier(0, 0, 0)
        self.assertFalse(error.exception.receipt["absent"])
        self.assertEqual(self.ops.sent, [(100, 0)])
        with self.assertRaises(owned.OwnershipError):
            self.scope.restore()

    def test_census_error_stays_failure_but_does_not_skip_later_safe_cleanup(self):
        self.activate_child()
        count = self.ops.table_calls
        def fail_once(kernel):
            if kernel.table_calls == count + 1:
                raise PermissionError("must not be logged")
        self.ops.on_table = fail_once
        self.ops.on_send = lambda kernel, pid, sig: kernel.terminate(pid)
        with self.assertRaises(owned.OwnershipError) as error:
            self.scope.barrier(.1, .2, .2)
        self.assertFalse(error.exception.receipt["absent"])
        self.assertTrue(error.exception.receipt["absence_observed_before_error"])
        self.assertTrue(error.exception.receipt["forced"])
        self.assertNotIn("must not be logged", repr(error.exception.receipt))
        self.scope.restore()
        self.assert_fds_closed()

    def test_one_signal_failure_does_not_skip_another_owned_child(self):
        self.activate_child(row(101), row(102))
        def error_for_one(kernel, pid, sig):
            if pid == 102:
                raise PermissionError()
            kernel.terminate(pid)
        self.ops.on_send = error_for_one
        with self.assertRaises(owned.OwnershipError):
            self.scope.barrier(0, .1, .1)
        self.assertNotIn(101, self.ops.rows)
        self.assertIn(102, self.ops.rows)
        self.assert_fds_closed()

    def test_close_error_is_fail_closed(self):
        self.activate_child()
        self.ops.on_close = lambda *_: (_ for _ in ()).throw(OSError())
        with self.assertRaises(owned.OwnershipError):
            self.scope.signal_owned(row(101), signal.SIGTERM)
        self.assertIn({"stage": "pidfd-close", "type": "OSError"}, self.scope.errors)
        self.assert_fds_closed()

    def test_restore_failure_retains_active_ownership(self):
        self.scope.activate()
        self.ops.on_setting = lambda *_: (_ for _ in ()).throw(OSError())
        with self.assertRaises(owned.OwnershipError):
            self.scope.restore()
        self.assertTrue(self.scope.active)

    def test_two_independent_empty_scans_are_required(self):
        self.scope.activate()
        before = self.ops.table_calls
        self.scope.barrier(0, 0, 0)
        self.assertEqual(self.ops.table_calls - before, 2)

    def test_invalid_budgets_and_inactive_barrier_refused(self):
        with self.assertRaises(owned.OwnershipError):
            self.scope.barrier()
        self.scope.activate()
        for budget in (-1, 601, float("nan"), "1"):
            with self.subTest(budget=budget), self.assertRaises(owned.OwnershipError):
                self.scope.barrier(budget, 0, 0)

    def test_current_sleep_interrupt_never_exposes_previous_clean_receipt(self):
        self.scope.activate()
        previous = self.scope.barrier(0, 0, 0)
        self.ops.rows[101] = row(101, session=999)
        self.ops.on_sleep = lambda *_: (_ for _ in ()).throw(KeyboardInterrupt())
        with self.assertRaises(owned.OwnershipError) as error:
            self.scope.barrier()
        self.assertTrue(previous["absent"])
        self.assertFalse(error.exception.receipt["absent"])
        self.assertFalse(self.scope.last_receipt["absent"])
        self.assertGreater(error.exception.receipt["barrier_generation"], previous["barrier_generation"])
        self.assertEqual(error.exception.receipt["observed"][0]["pid"], 101)
        self.assertIn({"stage": "barrier-operation", "type": "KeyboardInterrupt"}, self.scope.errors)

    def test_current_clock_failure_invalidates_clean_receipt_before_census(self):
        self.scope.activate()
        self.scope.barrier(0, 0, 0)
        self.ops.rows[101] = row(101)
        with mock.patch.object(self.ops, "clock", side_effect=OSError()):
            with self.assertRaises(owned.OwnershipError) as error:
                self.scope.barrier()
        self.assertFalse(error.exception.receipt["absent"])
        self.assertTrue(error.exception.receipt["errors"])

    def test_current_late_clock_interrupt_is_wrapped_and_sticky(self):
        self.activate_child()
        with mock.patch.object(self.ops, "clock", side_effect=[0, KeyboardInterrupt()]):
            with self.assertRaises(owned.OwnershipError) as error:
                self.scope.barrier()
        self.assertFalse(error.exception.receipt["absent"])
        self.ops.remove(101)
        with self.assertRaises(owned.OwnershipError) as recovered:
            self.scope.barrier(0, 0, 0)
        self.assertFalse(recovered.exception.receipt["absent"])
        self.assertTrue(recovered.exception.receipt["absence_observed_before_error"])
        self.scope.restore()

    def test_invalid_current_barrier_does_not_reuse_previous_receipt(self):
        self.scope.activate()
        self.scope.barrier(0, 0, 0)
        with self.assertRaises(owned.OwnershipError) as error:
            self.scope.barrier(-1, 0, 0)
        self.assertFalse(error.exception.receipt["absent"])

    def test_track_invalidates_previous_absence_after_new_child(self):
        self.scope.activate()
        self.scope.barrier(0, 0, 0)
        self.ops.rows[101] = row(101)
        self.scope.track()
        self.assertFalse(self.scope.last_receipt["absent"])

    def test_applied_acquisition_then_interrupt_keeps_restoration_obligation(self):
        original = self.ops.set_subreaper
        def apply_then_interrupt(value):
            original(value)
            if value == 1:
                raise KeyboardInterrupt()
        self.ops.set_subreaper = apply_then_interrupt
        with self.assertRaises(owned.OwnershipError):
            self.scope.activate()
        self.assertFalse(self.scope.active)
        self.assertTrue(self.scope.restoration_pending)
        self.assertEqual(self.ops.get_subreaper(), 1)
        receipt = self.scope.restore()
        self.assertEqual(self.ops.get_subreaper(), 0)
        self.assertEqual(self.ops.settings, [1, 0])
        self.assertFalse(self.scope.restoration_pending)
        self.assertEqual(receipt["restored_previous_setting"], 0)
        self.assert_fds_closed()

    def test_activation_readback_failure_does_not_authorize_child_launch(self):
        for failed_readback in (0, OSError()):
            with self.subTest(failed_readback=type(failed_readback).__name__):
                kernel = FakeKernel()
                scope = owned.OwnedChildren(kernel)
                with mock.patch.object(kernel, "get_subreaper", side_effect=[0, failed_readback]):
                    with self.assertRaises(owned.OwnershipError):
                        scope.activate()
                self.assertFalse(scope.active)
                self.assertTrue(scope.restoration_pending)
                scope.restore()
                self.assertEqual(kernel.settings, [1, 0])
                self.assertFalse(scope.restoration_pending)

    def test_applied_restoration_then_interrupt_retains_debt_until_verified_retry(self):
        self.scope.activate()
        original = self.ops.set_subreaper
        interrupted = []
        def apply_then_interrupt(value):
            original(value)
            if not interrupted:
                interrupted.append(True)
                raise KeyboardInterrupt()
        self.ops.set_subreaper = apply_then_interrupt
        with self.assertRaises(owned.OwnershipError):
            self.scope.restore()
        self.assertEqual(self.ops.get_subreaper(), 0)
        self.assertTrue(self.scope.active)
        self.assertTrue(self.scope.restoration_pending)
        self.scope.restore()
        self.assertEqual(self.ops.settings, [1, 0, 0])
        self.assertFalse(self.scope.active)
        self.assertFalse(self.scope.restoration_pending)

    def test_restoration_readback_mismatch_never_issues_restored_receipt(self):
        self.scope.activate()
        with mock.patch.object(self.ops, "get_subreaper", return_value=1):
            with self.assertRaises(owned.OwnershipError):
                self.scope.restore()
        self.assertTrue(self.scope.active)
        self.assertTrue(self.scope.restoration_pending)
        self.scope.restore()
        self.assertFalse(self.scope.restoration_pending)


class ProcParsingControls(unittest.TestCase):
    def test_stat_parsing_handles_parentheses_without_env_or_cmdline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "101").mkdir()
            fields = ["S", "100", "999", "888"] + ["0"] * 15 + ["1234"]
            (root / "101/stat").write_text("101 (fixture (worker)) " + " ".join(fields))
            result = owned.process_identity(101, proc_root=root, boot_id=BOOT)
            self.assertEqual(result["start_ticks"], 1234)
            self.assertEqual(result["pgid"], 999)
            self.assertEqual(result["session"], 888)
            self.assertEqual(set(root.joinpath("101").iterdir()), {root / "101/stat"})

    def test_disappearance_is_absence_and_malformed_stat_is_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertIsNone(owned.process_identity(101, proc_root=root, boot_id=BOOT))
            (root / "101").mkdir()
            (root / "101/stat").write_text("corrupt")
            with self.assertRaises(owned.OwnershipError):
                owned.process_identity(101, proc_root=root, boot_id=BOOT)

    def test_descendant_graph_does_not_include_foreign_session_or_parent(self):
        table = {100: row(100, 1), 101: row(101), 102: row(102, 101, session=500), 103: row(103, 1)}
        self.assertEqual(set(owned.descendants_from(table, 100)), {101, 102})


if __name__ == "__main__":
    unittest.main(verbosity=2)
