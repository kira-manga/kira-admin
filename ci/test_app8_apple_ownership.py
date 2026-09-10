"""Four bounded ownership families. Every process, signal and clock is mocked."""
from contextlib import ExitStack
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from test_app8_apple_source import snapshot

SPEC = importlib.util.spec_from_file_location('app8_apple_ownership_draft', Path(__file__).with_name('app8-apple.py'))
DRAFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRAFT)


class Host:
    """Only fixed fake children and an in-memory clock; no subprocess is created."""
    def __enter__(self):
        self.stack = ExitStack()
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix='app8-apple03-mocked-')))
        for name in ('reports', 'work'):
            (self.root / name).mkdir()
        self.now, self.sleeps, self.plans, self.children, self.signals = 10.0, [], [], [], []
        self.extra_rows, self.transform, self.signal_error = [], lambda rows: rows, None
        for target, name, replacement in (
            (DRAFT.time, 'monotonic', lambda: self.now), (DRAFT.time, 'sleep', self.sleep),
            (DRAFT.subprocess, 'Popen', self.launch), (DRAFT.os, 'waitid', self.waitid),
            (DRAFT.os, 'killpg', self.killpg), (DRAFT.os, 'getpid', lambda: 777),
            (DRAFT.os, 'getuid', lambda: 501), (DRAFT.os, 'geteuid', lambda: 501),
        ):
            self.stack.enter_context(mock.patch.object(target, name, side_effect=replacement))
        self.stack.enter_context(mock.patch.object(DRAFT, 'CANCELLED', False))
        self.commands = DRAFT.Commands(self.root, {'HOME': str(self.root)}, 100.0)
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def plan(self, **values):
        self.plans.append(values)

    def launch(self, argv, **kwargs):
        values = self.plans.pop(0) if self.plans else {}
        task = self.commands.tasks[-1]
        assert task['process'] is None and task['receipt']['pid'] is None
        if task['leaf']:
            assert self.commands.observer is task
            assert not any(t['leaf'] and t['process'] is not None and not t['receipt']['leaderReaped']
                           for t in self.commands.tasks[:-1])
        assert kwargs['start_new_session'] is True and kwargs['close_fds'] is True
        child = SimpleNamespace(pid=1000 + len(self.children), uid=values.get('uid', 501),
                                code=values.get('code', 0), exit_at=values.get('exit_at', self.now),
                                reaped=False, waits=[], info=values.get('info'), argv=argv)
        def wait(timeout):
            child.waits.append(timeout)
            if values.get('reap_error') or child.exit_at is None or self.now < child.exit_at:
                raise DRAFT.subprocess.TimeoutExpired(argv, timeout)
            child.reaped = True
            return child.code
        child.wait = wait
        self.children.append(child)
        self.now += values.get('spawn_delay', 0)
        if argv in (DRAFT.PS, DRAFT.GROUP_PS):
            full = argv == DRAFT.PS
            rows = [dict(pid=p.pid, uid=p.uid, ppid=777, pgid=p.pid,
                         state='R' if p is child else 'Z' if p.exit_at is not None and self.now >= p.exit_at else 'S',
                         executable='owned-tool', command='owned-tool') for p in self.children if not p.reaped]
            rows = self.transform(rows + [dict(row) for row in self.extra_rows])
            raw = '\n'.join(' '.join(str(row[key]) for key in ('pid', 'uid', 'ppid', 'pgid', 'state'))
                            + (' ' + row['executable'] + ' ' + row['command'] if full else '') for row in rows) + '\n'
        else:
            raw = 'ok\n'
        kwargs['stdout'].write(values.get('raw', raw).encode())
        return child

    def waitid(self, kind, pid, flags):
        assert kind == DRAFT.os.P_PID and flags == (DRAFT.os.WEXITED | DRAFT.os.WNOHANG | DRAFT.os.WNOWAIT)
        child = next(p for p in self.children if p.pid == pid)
        if child.reaped:
            raise ChildProcessError('already reaped')
        if child.info is not None:
            return child.info
        if child.exit_at is None or self.now < child.exit_at:
            return None
        return SimpleNamespace(si_pid=pid, si_uid=child.uid, si_code=DRAFT.os.CLD_EXITED, si_status=child.code)

    def killpg(self, pid, sig):
        self.signals.append((pid, sig))
        if self.signal_error:
            raise self.signal_error
        next(p for p in self.children if p.pid == pid).exit_at = self.now

    def target(self, **plan):
        self.plan(**plan)
        return self.commands.start(['/usr/bin/owned-tool'], 'mock-target')

    def root_member(self, task, state='S', escaped=False):
        self.extra_rows.append(dict(pid=9000, uid=0, ppid=1 if escaped else task['process'].pid,
                                    pgid=9000 if escaped else task['process'].pid, state=state,
                                    executable=DRAFT.EXECUTABLE if escaped else 'root-child',
                                    command=str(self.root / 'worker') if escaped else 'root-child'))


class Ownership(unittest.TestCase):
    def test_exited_exact_leaf_settles_without_signals_or_laundering(self):
        for argv in (DRAFT.PS, DRAFT.GROUP_PS):
            for case in ('clean', 'late-zero', 'nonzero', 'prior-error', 'cancelled'):
                with self.subTest(argv=argv[-1], case=case), Host() as host:
                    host.plan(code=7 if case == 'nonzero' else 0)
                    task = host.commands.start(argv, 'leaf', seconds=1)
                    if case == 'late-zero':
                        task['receipt'].update(deadline=host.now - 1, timedOut=True)
                    if case in ('late-zero', 'prior-error', 'cancelled'):
                        task['receipt']['errors'].append(case)
                    DRAFT.CANCELLED = case == 'cancelled'
                    prior = list(task['receipt']['errors'])
                    host.commands.end = host.now + 0.5  # Deliberately no 12s signal reservation.
                    with mock.patch.object(host.commands, 'observe', side_effect=AssertionError('recursive observer')):
                        host.commands.force(task)
                    self.assertTrue(task['receipt']['leaderReaped'] and task['receipt']['groupQuiet'])
                    self.assertEqual(task['receipt']['actualExit'], 7 if case == 'nonzero' else 0)
                    self.assertEqual(task['receipt']['errors'], prior)
                    self.assertFalse(task['receipt']['normalJoin'] or task['receipt']['forced'])
                    self.assertFalse(host.commands.normal())
                    self.assertEqual((host.signals, host.sleeps, len(host.commands.tasks)), ([], [], 1))
                    self.assertLessEqual(task['process'].waits[0], 0.5)
        for case in ('running', 'wrong-exit-pid', 'lost', 'reap-failed', 'not-exact-argv'):
            with self.subTest(case=case), Host() as host:
                values = {'exit_at': None} if case == 'running' else {'reap_error': True} if case == 'reap-failed' else {}
                if case == 'wrong-exit-pid':
                    values['info'] = SimpleNamespace(si_pid=9999, si_uid=501, si_code=DRAFT.os.CLD_EXITED, si_status=0)
                host.plan(**values)
                task = host.commands.start(DRAFT.GROUP_PS + (['-x'] if case == 'not-exact-argv' else []), 'refusal')
                task['receipt']['ownershipLost'] = case == 'lost'
                host.commands.end = host.now + 0.5
                with self.assertRaises((RuntimeError, DRAFT.subprocess.TimeoutExpired)):
                    host.commands.force(task)
                self.assertFalse(task['receipt']['leaderReaped'])
                self.assertEqual((host.signals, host.sleeps, len(host.commands.tasks)), ([], [], 1))

    def test_pinned_all_uid_groups_share_one_observation(self):
        with Host() as host:
            first, second = host.target(uid=0), host.target()
            host.root_member(first, state='Z')
            with mock.patch.object(host.commands, 'wait', side_effect=AssertionError('recursive wait')):
                self.assertTrue(host.commands.drain())
            self.assertEqual(len([p for p in host.children if p.argv == DRAFT.GROUP_PS]), 1)
            self.assertTrue(host.commands.normal())
            self.assertTrue(all(task['receipt']['leaderReaped'] for task in (first, second)))
            self.assertIn(0, [row['uid'] for row in first['receipt']['lastGroup']])
            self.assertEqual(first['receipt']['groupObserverPid'], second['receipt']['groupObserverPid'])
            self.assertEqual((host.signals, host.sleeps), ([], []))
        with Host() as host:
            host.plan(exit_at=host.now + 0.05)
            task = host.commands.start(['/usr/bin/owned-tool'], 'short-normal-cap', seconds=0.1)
            self.assertEqual(host.commands.wait(task), 'ok\n')
            self.assertTrue(all(0 < timeout <= 0.1 for child in host.children for timeout in child.waits))
        with Host() as host:
            target = host.target()
            host.root_member(target)
            observation = host.commands.observe()
            self.assertFalse(host.commands.group_quiet(target, observation))
            self.assertFalse(target['receipt']['leaderReaped'])
            self.assertIn(0, [row['uid'] for row in target['receipt']['lastGroup']])
        for case in ('omitted', 'wrong-ppid', 'wrong-pgid'):
            with self.subTest(case=case), Host() as host:
                target = host.target()
                pid = target['process'].pid
                def transform(rows):
                    return [dict(row, **({'ppid': 1} if case == 'wrong-ppid' else {'pgid': 9999}))
                            if row['pid'] == pid else row for row in rows
                            if case != 'omitted' or row['pid'] != pid]
                host.transform = transform
                with self.assertRaises(RuntimeError):
                    host.commands.group_quiet(target, host.commands.observe())
                self.assertTrue(target['receipt']['ownershipLost'])
                self.assertFalse(target['receipt']['groupQuiet'] or target['receipt']['leaderReaped'])
                with self.assertRaises(RuntimeError):
                    host.commands.force(target)
                self.assertEqual(host.signals, [])

    def test_observer_failures_do_not_grow_or_supply_stale_evidence(self):
        for case in ('malformed', 'truncated', 'duplicate', 'empty', 'missing-observer', 'late'):
            with self.subTest(case=case), Host() as host:
                if case in ('malformed', 'truncated', 'empty'):
                    host.plan(raw={'malformed': 'bad row\n', 'truncated': '1000 501 777 1000 R', 'empty': ''}[case])
                elif case == 'duplicate':
                    host.transform = lambda rows: rows + rows
                elif case == 'missing-observer':
                    host.transform = lambda rows: [dict(rows[0], pid=8888)]
                else:
                    host.plan(spawn_delay=2)
                with self.assertRaises(RuntimeError):
                    host.commands.observe()
                observer = host.commands.observer
                host.commands.retire_observer()
                self.assertTrue(observer['receipt']['leaderReaped'])
                self.assertFalse(observer['receipt']['normalJoin'])
                self.assertFalse(host.commands.normal())
                with self.assertRaises(RuntimeError):
                    host.commands.observe(cleaning=True)
                self.assertEqual((len(host.children), host.signals, host.sleeps), (1, [], []))
        with Host() as host:
            host.plan(exit_at=None)
            with self.assertRaises(RuntimeError):
                host.commands.observe()
            progress = host.commands.progress
            host.commands.retire_observer()  # Even signaling a failed observer is not target progress.
            self.assertTrue(host.commands.observer['receipt']['leaderReaped'])
            self.assertEqual(host.commands.progress, progress)
            with self.assertRaises(RuntimeError):
                host.commands.observe(cleaning=True)
            self.assertEqual((len(host.children), host.sleeps.count(10)), (1, 1))
        with Host() as host:
            checkpoint, calls = host.commands.checkpoint, []
            def fail_after_spawn():
                calls.append(1)
                if len(calls) == 2:
                    host.commands.audit_failed = True
                    raise OSError('mock post-spawn receipt failure')
                checkpoint()
            with mock.patch.object(host.commands, 'checkpoint', side_effect=fail_after_spawn):
                with self.assertRaises(OSError):
                    host.commands.observe()
            self.assertIs(host.commands.observer, host.commands.tasks[0])
            self.assertEqual(host.commands.observer['receipt']['pid'], 1000)
            host.commands.retire_observer()
            self.assertTrue(host.commands.observer['receipt']['leaderReaped'])
            self.assertFalse(host.commands.normal())
            self.assertEqual(host.signals, [])
        with Host() as host:
            host.plan(exit_at=None)
            with self.assertRaises(RuntimeError):
                host.commands.observe()
            first = host.commands.observer
            target = host.target()
            with self.assertRaises(RuntimeError):
                host.commands.observe(cleaning=True)  # Relevant launch does not bypass an unreaped observer.
            self.assertEqual(len(host.children), 2)
            first['process'].exit_at = host.now
            host.commands.retire_observer()
            with self.assertRaises(RuntimeError):
                host.commands.observe(cleaning=True)  # Reaping only the failed observer is not target progress.
            host.commands.peek(target)
            with mock.patch.object(host.commands, 'wait', side_effect=AssertionError('nested wait')):
                observation = host.commands.observe(cleaning=True)
            self.assertTrue(host.commands.group_quiet(target, observation))
            self.assertEqual(len(host.children), 3)
        with Host() as host:
            target = host.target()
            observation = host.commands.observe()
            host.target()  # Includes PF/device launches: no old epoch can establish absence.
            with self.assertRaises(RuntimeError):
                host.commands.group_quiet(target, observation)
            self.assertFalse(target['receipt']['groupQuiet'])
        with Host() as host:
            host.target()
            observation = host.commands.observe(full=True)
            self.assertTrue(host.commands.drain(observation))
            with self.assertRaises(RuntimeError):
                host.commands.drain(observation)
            self.assertEqual(len(host.children), 2)

    def test_cleanup_and_fresh_pf_barriers_refuse_unknown_permission_or_budget(self):
        keys = ('nativeAbsent', 'fixturesAbsent', 'commandsAbsent', 'workersAbsent', 'simulatorRemoved', 'receiptSaved')
        record = {'token': '42', 'policySha256': DRAFT.hashlib.sha256(DRAFT.PF_RULES.encode()).hexdigest()}
        with Host() as host:
            cleanup = dict.fromkeys(keys, True)
            host.plan(exit_at=None)
            with self.assertRaises(RuntimeError):
                DRAFT.absence_barrier(host.commands, {}, cleanup, [])
            observer = host.commands.observer
            self.assertFalse(observer['receipt']['leaderReaped'])
            prior_errors = list(observer['receipt']['errors'])
            self.assertTrue(observer['receipt']['timedOut'] and prior_errors)
            observer['process'].exit_at = host.now  # It exits only after the failed helper returns.
            host.commands.end = host.now + 0.5  # No TERM/KILL reservation remains.
            progress, sleeps = host.commands.progress, list(host.sleeps)
            for _ in range(2):  # Later cleanup and final scratch helper entries.
                with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                    DRAFT.absence_barrier(host.commands, {}, cleanup, [])
                self.assertTrue(observer['receipt']['leaderReaped'] and observer['receipt']['groupQuiet'])
                self.assertEqual(observer['receipt']['actualExit'], 0)
                self.assertEqual(observer['receipt']['errors'], prior_errors)
                self.assertTrue(observer['receipt']['timedOut'])
                self.assertFalse(observer['receipt']['normalJoin'] or observer['receipt']['forced'])
                self.assertEqual(host.commands.progress, progress)
                self.assertEqual(host.commands.failed_observer_progress, progress)
                self.assertEqual((len(host.children), len(host.commands.tasks), host.signals, host.sleeps), (1, 1, [], sleeps))
                self.assertFalse(any(cleanup[key] for key in keys if key != 'simulatorRemoved'))
                self.assertFalse(DRAFT.may_release(record, '42', True, cleanup))
                self.assertFalse(host.commands.normal())
            self.assertEqual(len(observer['process'].waits), 1)
        with Host() as host:
            target = host.target(uid=0)
            host.root_member(target)
            host.signal_error = PermissionError(1, 'mock EPERM')
            self.assertFalse(host.commands.drain())
            self.assertFalse(target['receipt']['leaderReaped'] or target['receipt']['groupQuiet'])
            self.assertTrue(target['signalingClosed'])
            self.assertEqual(host.sleeps, [10])
            self.assertEqual(len(host.signals), 2)
            self.assertTrue(all('EPERM' in item['outcome'] for item in target['receipt']['signalAttempts']))
            cleanup = dict.fromkeys(keys, True)
            DRAFT.absence_barrier(host.commands, {}, cleanup, [])
            self.assertFalse(cleanup['commandsAbsent'])
            self.assertFalse(DRAFT.may_release(record, '42', True, cleanup))
            self.assertFalse(host.commands.normal())
        with Host() as host:
            target = host.target()
            host.root_member(target)
            host.plan()  # Initial complete observation.
            host.plan(raw='bad post-signal census\n')
            self.assertFalse(host.commands.drain())
            self.assertFalse(target['receipt']['leaderReaped'] or target['receipt']['groupQuiet'])
            self.assertTrue(target['signalingClosed'])
            count = len(host.children)
            self.assertFalse(host.commands.drain())
            self.assertEqual(len(host.children), count)  # No serial failed-observer/reap retry loop.
            self.assertEqual(host.sleeps, [10])
        with Host() as host:
            target = host.target()
            host.root_member(target)
            leaf = host.commands.start(DRAFT.GROUP_PS, 'completed-failed-leaf', seconds=1)
            leaf['receipt'].update(deadline=host.now - 1, timedOut=True)
            host.commands.end = host.now + 0.5
            cleanup = dict.fromkeys(keys, True)
            cleanup['commandsAbsent'] = host.commands.drain()
            self.assertTrue(leaf['receipt']['leaderReaped'])
            self.assertFalse(cleanup['commandsAbsent'])
            self.assertFalse(DRAFT.may_release(record, '42', True, cleanup))
            self.assertEqual((host.signals, host.sleeps), ([], []))
        with Host() as host:
            escaped = {'process': SimpleNamespace(pid=9000)}
            host.root_member(escaped, escaped=True)
            cleanup = dict.fromkeys(keys, True)
            DRAFT.absence_barrier(host.commands, {}, cleanup, [])
            self.assertTrue(cleanup['commandsAbsent'])
            self.assertFalse(cleanup['workersAbsent'] or cleanup['nativeAbsent'])
            self.assertEqual(cleanup['workers'][0]['uid'], 0)
            self.assertFalse(DRAFT.may_release(record, '42', True, cleanup))
            self.assertEqual(host.signals, [])
        with Host() as host:
            cleanup, firewall = dict.fromkeys(keys, True), {'ownershipVerified': True, 'ownershipLost': False}
            DRAFT.absence_barrier(host.commands, {}, cleanup, [])
            self.assertTrue(DRAFT.may_release(record, '42', True, cleanup))
            old_epoch = host.commands.epoch
            def final_pf_queries(*_args):
                host.commands.call(DRAFT.PF + ['-s', 'info'], 'mock-final-pf-query', seconds=5, cleaning=True)
                return snapshot(True)
            with mock.patch.object(DRAFT, 'pf_snapshot', side_effect=final_pf_queries):
                DRAFT.verify_owned_pf(host.commands, 'mock-final-pf', '42', firewall, cleaning=True)
            self.assertGreater(host.commands.epoch, old_epoch)
            host.plan(raw='bad fresh final barrier\n')
            with self.assertRaises(RuntimeError):
                DRAFT.absence_barrier(host.commands, {}, cleanup, [])
            self.assertFalse(any(cleanup[key] for key in keys if key != 'simulatorRemoved'))
            self.assertFalse(DRAFT.may_release(record, '42', firewall['ownershipVerified'], cleanup))
            self.assertFalse(any('-X' in child.argv for child in host.children))


if __name__ == '__main__':
    unittest.main()
