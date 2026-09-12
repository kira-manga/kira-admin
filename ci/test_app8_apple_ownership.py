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
                    host.plan(spawn_delay=11)
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
        for case in ('settled-then-failed-full', 'eperm', 'budget'):
            with self.subTest(cleanup_created=case), Host() as host:
                cleanup = dict.fromkeys(keys, True)
                state = {'udid': 'mock-created-device', 'name': 'mock-owned-simulator'}
                self.assertTrue(host.commands.drain())  # Main's initial empty drain precedes disposal.
                host.plan(exit_at=None)
                with self.assertRaisesRegex(RuntimeError, 'Child cancelled or exceeded its cap: devices'):
                    DRAFT.dispose_simulator(host.commands, state, cleanup)
                target = host.commands.tasks[0]
                self.assertFalse(target['leaf'])
                deadline, target_errors = target['receipt']['deadline'], list(target['receipt']['errors'])
                self.assertTrue(target['receipt']['timedOut'] and target_errors)
                host.plan(exit_at=None)
                with self.assertRaisesRegex(RuntimeError, 'Child cancelled or exceeded its cap: owned-groups'):
                    host.commands.observe(cleaning=True)
                observer = host.commands.observer
                observer_errors = list(observer['receipt']['errors'])
                progress, sleeps = host.commands.progress, list(host.sleeps)
                self.assertEqual(host.commands.failed_observer_progress, progress)
                observer['process'].exit_at = host.now  # Only the failed observer exits, not the target.
                self.assertNotIn('lastExitObservation', target['receipt'])
                self.assertEqual(host.commands.progress, progress)
                if case == 'eperm':
                    host.signal_error = PermissionError(1, 'mock EPERM')
                elif case == 'budget':
                    host.commands.end = host.now + 0.5
                else:
                    host.plan()  # Normal numeric post-signal group proof, if the drain is reached.
                    host.plan(raw='bad cleanup full census\n')  # Settlement is not full absence.
                end = host.commands.end
                for entry in range(2):  # Later absence and scratch entries must not renew/retry work.
                    with self.assertRaises(RuntimeError) as failure:
                        DRAFT.absence_barrier(host.commands, state, cleanup, [])
                    self.assertEqual((host.commands.end, target['receipt']['deadline']), (end, deadline))
                    self.assertTrue(observer['receipt']['leaderReaped'] and observer['receipt']['groupQuiet'])
                    self.assertEqual(observer['receipt']['actualExit'], 0)
                    self.assertEqual(observer['receipt']['errors'], observer_errors)
                    self.assertTrue(observer['receipt']['timedOut'])
                    self.assertFalse(observer['receipt']['normalJoin'] or observer['receipt']['forced'])
                    self.assertEqual(len(observer['process'].waits), 1)
                    self.assertTrue(target['receipt']['timedOut'])
                    self.assertEqual(target['receipt']['errors'][:len(target_errors)], target_errors)
                    self.assertFalse(any(cleanup[key] for key in keys if key != 'simulatorRemoved'))
                    self.assertFalse(DRAFT.may_release(record, '42', True, cleanup) or host.commands.normal())
                    expected_signals = [] if case == 'budget' else [
                        (target['process'].pid, DRAFT.signal.SIGTERM), (target['process'].pid, DRAFT.signal.SIGKILL)]
                    self.assertEqual(host.signals, expected_signals)
                    self.assertEqual(host.sleeps, sleeps + ([] if case == 'budget' else [10]))
                    self.assertEqual(target['receipt']['forced'], case != 'budget')
                    self.assertEqual(target['signalingClosed'], case != 'budget')
                    self.assertFalse(target['receipt']['ownershipLost'])
                    self.assertEqual(host.commands.failed_observer_progress, host.commands.progress)
                    if case == 'settled-then-failed-full':
                        self.assertTrue(target['receipt']['leaderReaped'] and target['receipt']['groupQuiet'])
                        self.assertEqual(len(target['process'].waits), 1)
                        self.assertGreater(host.commands.progress, progress)
                        self.assertEqual([item['outcome'] for item in target['receipt']['signalAttempts']], ['sent', 'sent'])
                        self.assertEqual([child.argv for child in host.children[1:]],
                                         [DRAFT.GROUP_PS, DRAFT.GROUP_PS, DRAFT.PS])
                        group, full = host.commands.tasks[-2:]
                        self.assertTrue(group['receipt']['normalJoin'])
                        self.assertEqual(target['receipt']['groupObserverPid'], group['receipt']['pid'])
                        self.assertFalse(full['receipt']['normalJoin'])
                        expected_error = 'Malformed owned-process census' if entry == 0 else 'Observer failed without relevant target progress'
                    else:
                        self.assertFalse(target['receipt']['leaderReaped'] or target['receipt']['groupQuiet'])
                        self.assertNotIn('lastExitObservation', target['receipt'])
                        self.assertNotIn('lastGroup', target['receipt'])
                        self.assertEqual((target['process'].waits, host.commands.progress, len(host.children)), ([], progress, 2))
                        if case == 'eperm':
                            self.assertEqual(len(target['receipt']['signalAttempts']), 2)
                            self.assertTrue(all('EPERM' in item['outcome'] for item in target['receipt']['signalAttempts']))
                        else:
                            self.assertEqual(target['receipt']['signalAttempts'], [])
                        expected_error = 'Observer failed without relevant target progress'
                    self.assertEqual(str(failure.exception), expected_error)
                    self.assertFalse(any('-X' in child.argv for child in host.children))
        with Host() as host:
            cleanup, observations = dict.fromkeys(keys, True), []
            observe = host.commands.observe
            def cleanup_launch_before_full(cleaning=False, full=False, end=None):
                if full:
                    host.target(exit_at=None)  # Registered after pre-drain; real post-proof drain must act.
                observation = observe(cleaning=cleaning, full=full, end=end)
                observations.append(observation)
                return observation
            with mock.patch.object(host.commands, 'observe', side_effect=cleanup_launch_before_full):
                with self.assertRaisesRegex(RuntimeError, 'Missing/stale/failed process observation'):
                    DRAFT.absence_barrier(host.commands, {}, cleanup, [])
            full, post_signal = observations
            self.assertTrue(full['full'] and full['drained'])
            self.assertFalse(post_signal['full'])
            self.assertGreater(post_signal['epoch'], full['epoch'])
            target = host.commands.tasks[0]
            self.assertTrue(target['receipt']['leaderReaped'] and target['receipt']['forced'])
            self.assertFalse(any(cleanup[key] for key in keys if key != 'simulatorRemoved'))
            self.assertFalse(DRAFT.may_release(record, '42', True, cleanup) or host.commands.normal())
            self.assertFalse(any('-X' in child.argv for child in host.children))
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

    def test_rejected_rows_record_only_the_first_fixed_predicate(self):
        for full in (False, True):
            suffix, width = (' PRIVATE_COMMAND PRIVATE_ARGS', 7) if full else ('', 5)
            cases = (
                ('PRIVATE_FIELDS', 'FIELD_COUNT', 1), ('', 'FIELD_COUNT', 0),
                ('9 0 777 9 R' if full else '9 0 777 9 R PRIVATE_EXTRA', 'FIELD_COUNT', 5 if full else 6),
                ('PRIVATE_PID PRIVATE_UID PRIVATE_PPID PRIVATE_PGID PRIVATE_STAT' + suffix, 'PID_DIGITS', width),
                ('9 PRIVATE_UID PRIVATE_PPID PRIVATE_PGID PRIVATE_STAT' + suffix, 'UID_DIGITS', width),
                ('9 0 PRIVATE_PPID PRIVATE_PGID PRIVATE_STAT' + suffix, 'PPID_DIGITS', width),
                ('9 0 777 PRIVATE_PGID PRIVATE_STAT' + suffix, 'PGID_DIGITS', width),
                ('9 0 777 9 PRIVATE_STAT' + suffix, 'STAT', width),
            )
            for bad, predicate, count in cases:
                with self.subTest(full=full, predicate=predicate, fields=count), Host() as host:
                    first = '1000 501 777 1000 R' + (' owned-tool owned-tool' if full else '')
                    host.plan(raw=first + '\n' + bad + '\nPRIVATE_LATER_ROW\n')
                    with self.assertRaisesRegex(RuntimeError, '^Malformed owned-process census$'):
                        host.commands.observe(full=full)
                    task, receipt = host.commands.observer, host.commands.observer['receipt']
                    self.assertEqual(receipt['censusParseFailure'],
                                     {'lineIndex': 2, 'fieldCount': count, 'predicate': predicate})
                    self.assertEqual(receipt['errors'], ['Malformed owned-process census'])
                    self.assertNotIn('PRIVATE_', DRAFT.json.dumps(receipt))
                    if full:
                        self.assertNotIn('censusRetention', receipt)
                        self.assertEqual(receipt['output'], 'private census; not retained')
                        self.assertFalse(task['log'].exists())
                        self.assertEqual(list((host.root / 'reports').glob('*.log')), [])
                    else:
                        self.assertEqual(receipt['censusRetention']['status'], 'RETAINED')
                        self.assertEqual(task['log'], host.root / 'reports/001-malformed-owned-groups.log')
                    self.assertFalse(receipt['normalJoin'] or host.commands.normal())
                    with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                        host.commands.observe(cleaning=True)
                    self.assertEqual((len(host.children), host.signals, host.sleeps), (1, [], []))

    def test_accepted_rows_keep_the_existing_projection_and_state_rules(self):
        for full, raw in (
            (False, '01000 0 0777 01000 I<ALNs+\n'),
            (True, '1000 501 777 1000 R /bin/ps\n'),
            (True, '1000 501 777 1000 Z /bin/ps args with spaces\n'),
        ):
            with self.subTest(full=full, raw=raw), Host() as host:
                host.plan(raw=raw)
                observation = host.commands.observe(full=full)
                receipt = observation['observer']['receipt']
                self.assertTrue(receipt['normalJoin'] and host.commands.normal())
                self.assertNotIn('censusParseFailure', receipt)
                self.assertNotIn('censusRetention', receipt)
                self.assertEqual(list((host.root / 'reports').glob('*.log')), [])
                self.assertFalse(observation['observer']['log'].exists())
                self.assertEqual((host.signals, host.sleeps), ([], []))

    def test_retained_group_bytes_stay_accounted_if_scratch_unlink_fails(self):
        for unlink_error in (False, True):
            with self.subTest(unlink_error=unlink_error), Host() as host:
                raw = b'1000 501 777 1000 R\r\nPRIVATE_BAD_ROW\r\n'
                host.plan(raw=raw.decode())
                scratch = host.root / 'work/001-owned-groups.log'
                retained = host.root / 'reports/001-malformed-owned-groups.log'
                unlink, failed, original_errors = Path.unlink, host.commands.failed, []
                def remove(path, *args, **kwargs):
                    if unlink_error and path == scratch:
                        raise OSError('PRIVATE_UNLINK_ERROR')
                    return unlink(path, *args, **kwargs)
                def remember(task, error):
                    original_errors.append(error)
                    failed(task, error)
                with mock.patch.object(Path, 'unlink', new=remove), mock.patch.object(host.commands, 'failed', side_effect=remember):
                    with self.assertRaisesRegex(RuntimeError, '^Malformed owned-process census$') as failure:
                        host.commands.observe()
                task, receipt = host.commands.observer, host.commands.observer['receipt']
                self.assertIs(failure.exception, original_errors[0])
                self.assertEqual(receipt['errors'], ['Malformed owned-process census']
                                 + (['Malformed group census retention failed'] if unlink_error else []))
                self.assertEqual(receipt['censusRetention'], {
                    'status': 'FAILED' if unlink_error else 'RETAINED', 'name': retained.name,
                    'bytesAtRetention': len(raw), 'sha256AtRetention': DRAFT.hashlib.sha256(raw).hexdigest(),
                    'scratchRemoved': not unlink_error,
                })
                self.assertEqual((task['log'], receipt['output'], receipt['outputBytesAtLastRead']),
                                 (retained, retained.name, len(raw)))
                self.assertEqual(retained.read_bytes(), raw)
                self.assertEqual(scratch.exists(), unlink_error)
                if unlink_error:
                    self.assertTrue(scratch.samefile(retained))
                self.assertEqual(DRAFT.read_json(host.root / 'reports/commands.json'), [receipt])
                self.assertNotIn('PRIVATE_', DRAFT.json.dumps(receipt))
                self.assertTrue(receipt['leaderReaped'] and receipt['groupQuiet'])
                self.assertFalse(receipt['normalJoin'] or receipt['forced'] or receipt['timedOut'] or host.commands.normal())
                self.assertTrue(host.commands.within_cap())
                retained.write_bytes(b'x' * 1048577)
                self.assertFalse(host.commands.within_cap())  # Includes the reports file, even after scratch is gone.
                host.commands.retire_observer()
                with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                    host.commands.observe(cleaning=True)
                self.assertEqual(host.commands.failed_observer_progress, host.commands.progress)
                self.assertEqual((len(host.children), host.signals, host.sleeps), (1, [], []))

    def test_group_retention_refuses_existing_destinations_symlinks_and_link_errors(self):
        for case in ('existing', 'destination-symlink', 'raced-destination', 'source-symlink', 'link-error'):
            with self.subTest(case=case), Host() as host:
                raw, prior = b'PRIVATE_FIELDS\n', b'preserve existing evidence\n'
                host.plan(raw=raw.decode())
                scratch = host.root / 'work/001-owned-groups.log'
                destination = host.root / 'reports/001-malformed-owned-groups.log'
                if case == 'existing':
                    destination.write_bytes(prior)
                elif case == 'destination-symlink':
                    destination.symlink_to(host.root / 'not-created')
                elif case == 'raced-destination':
                    link = DRAFT.os.link
                    def race(source, target, **kwargs):
                        self.assertEqual(kwargs, {'follow_symlinks': False})
                        target.write_bytes(prior)
                        return link(source, target, **kwargs)
                    host.stack.enter_context(mock.patch.object(DRAFT.os, 'link', side_effect=race))
                elif case == 'source-symlink':
                    output = host.commands.output
                    def substitute(task, cleaning=False):
                        value = output(task, cleaning)
                        original = host.root / 'work/private-original'
                        task['log'].rename(original)
                        task['log'].symlink_to(original)
                        return value
                    host.stack.enter_context(mock.patch.object(host.commands, 'output', side_effect=substitute))
                else:
                    host.stack.enter_context(mock.patch.object(DRAFT.os, 'link', side_effect=OSError('PRIVATE_LINK_ERROR')))
                with self.assertRaisesRegex(RuntimeError, '^Malformed owned-process census$'):
                    host.commands.observe()
                task, receipt = host.commands.observer, host.commands.observer['receipt']
                self.assertEqual(receipt['errors'], ['Malformed owned-process census', 'Malformed group census retention failed'])
                self.assertEqual(receipt['censusRetention'], {'status': 'FAILED'})
                self.assertEqual((task['log'], receipt['output']), (scratch, 'private census; not retained'))
                self.assertEqual(scratch.read_bytes(), raw)
                self.assertNotIn('PRIVATE_', DRAFT.json.dumps(receipt))
                if case in ('existing', 'raced-destination'):
                    self.assertEqual(destination.read_bytes(), prior)
                elif case == 'destination-symlink':
                    self.assertTrue(destination.is_symlink())
                    self.assertFalse(destination.exists() or (host.root / 'not-created').exists())
                else:
                    self.assertFalse(destination.exists())
                self.assertFalse(receipt['normalJoin'] or host.commands.normal())
                with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                    host.commands.observe(cleaning=True)
                self.assertEqual((len(host.children), host.signals, host.sleeps), (1, [], []))

    def test_group_retention_enforces_file_and_total_caps_even_during_cleanup(self):
        for cap in ('file', 'total'):
            with self.subTest(cap=cap), Host() as host:
                if cap == 'total':
                    for _ in range(4):
                        host.target(raw='x' * 1048576)
                else:
                    output = host.commands.output
                    def grow(task, cleaning=False):
                        value = output(task, cleaning)
                        task['log'].write_bytes(b'x' * 1048577)
                        return value
                    host.stack.enter_context(mock.patch.object(host.commands, 'output', side_effect=grow))
                host.plan(raw='PRIVATE_FIELDS\n')
                with self.assertRaisesRegex(RuntimeError, '^Malformed owned-process census$'):
                    host.commands.observe(cleaning=True)
                task, receipt = host.commands.observer, host.commands.observer['receipt']
                self.assertEqual(receipt['errors'], ['Malformed owned-process census', 'Malformed group census retention failed'])
                self.assertEqual(receipt['censusRetention'], {'status': 'FAILED'})
                self.assertEqual(receipt['output'], 'private census; not retained')
                self.assertEqual(task['log'].parent, host.root / 'work')
                self.assertTrue(task['log'].exists())
                self.assertFalse(host.commands.within_cap() or receipt['normalJoin'] or host.commands.normal())
                self.assertEqual(list((host.root / 'reports').glob('*-malformed-owned-groups.log')), [])
                with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                    host.commands.observe(cleaning=True)
                self.assertEqual((len(host.children), host.signals, host.sleeps), (5 if cap == 'total' else 1, [], []))

    def test_retention_keeps_existing_deadlines_across_added_work(self):
        for bound in ('observer', 'owner'):
            for phase in ('entry', 'source-hash', 'link', 'report-hash', 'unlink'):
                with self.subTest(bound=bound, phase=phase), Host() as host:
                    host.plan(raw='PRIVATE_FIELDS\n')
                    scratch = host.root / 'work/001-owned-groups.log'
                    report = host.root / 'reports/001-malformed-owned-groups.log'
                    failed, sha256, link, unlink = host.commands.failed, DRAFT.hashlib.sha256, DRAFT.os.link, Path.unlink
                    original_errors, hashes, links, unlinks = [], [], [], []
                    def expire():
                        host.now = min(host.commands.observer['receipt']['deadline'], host.commands.end)
                    def remember(task, error):
                        original_errors.append(error)
                        failed(task, error)
                        if bound == 'owner':
                            host.commands.end = 15.0  # Inject only a stricter owner end; observer deadline stays at clock20.
                        if phase == 'entry':
                            expire()
                    def timed_hash(data=b''):
                        result = sha256(data)
                        hashes.append(1)
                        if (phase == 'source-hash' and len(hashes) == 1) or (phase == 'report-hash' and len(hashes) == 2):
                            expire()
                        return result
                    def timed_link(source, destination, **kwargs):
                        result = link(source, destination, **kwargs)
                        links.append(destination)
                        if phase == 'link':
                            expire()
                        return result
                    def timed_unlink(path, *args, **kwargs):
                        result = unlink(path, *args, **kwargs)
                        if path == scratch:
                            unlinks.append(path)
                            if phase == 'unlink':
                                expire()
                        return result
                    for target, name, replacement in (
                        (host.commands, 'failed', remember), (DRAFT.hashlib, 'sha256', timed_hash),
                        (DRAFT.os, 'link', timed_link), (Path, 'unlink', timed_unlink),
                    ):
                        host.stack.enter_context(mock.patch.object(target, name, new=replacement))
                    with self.assertRaisesRegex(RuntimeError, '^Malformed owned-process census$') as failure:
                        host.commands.observe()
                    task, receipt = host.commands.observer, host.commands.observer['receipt']
                    linked = phase in ('link', 'report-hash', 'unlink')
                    self.assertIs(failure.exception, original_errors[0])
                    self.assertEqual(receipt['errors'], ['Malformed owned-process census', 'Malformed group census retention failed'])
                    self.assertEqual(receipt['censusRetention']['status'], 'FAILED')
                    self.assertEqual((task['log'], receipt['output']),
                                     (report, report.name) if linked else (scratch, 'private census; not retained'))
                    self.assertEqual((len(hashes), len(links), len(unlinks)),
                                     (0 if phase == 'entry' else 1 if phase in ('source-hash', 'link') else 2,
                                      int(linked), int(phase == 'unlink')))
                    self.assertEqual((receipt['deadline'], host.commands.end, host.now),
                                     (20.0, 15.0 if bound == 'owner' else 100.0, 15.0 if bound == 'owner' else 20.0))
                    self.assertEqual(scratch.exists(), phase != 'unlink')
                    if linked:
                        self.assertTrue(report.exists())
                        self.assertEqual(receipt['censusRetention']['scratchRemoved'], phase == 'unlink')
                    else:
                        self.assertFalse(report.exists())
                    self.assertNotIn('PRIVATE_', DRAFT.json.dumps(receipt))
                    self.assertTrue(receipt['leaderReaped'] and receipt['groupQuiet'])
                    self.assertFalse(receipt['normalJoin'] or receipt['forced'] or host.commands.normal())
                    host.commands.retire_observer()
                    with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                        host.commands.observe(cleaning=True)
                    self.assertEqual(host.commands.failed_observer_progress, host.commands.progress)
                    self.assertEqual((len(host.children), host.signals, host.sleeps), (1, [], []))

    def test_linked_artifact_growth_substitution_and_bytes_fail_closed(self):
        for case in ('growth', 'replacement', 'symlink', 'same-size-bytes', 'aggregate'):
            with self.subTest(case=case), Host() as host:
                if case == 'aggregate':
                    for _ in range(4):
                        host.target()
                sequence = len(host.commands.tasks) + 1
                raw = b'PRIVATE_FIELDS\n'
                host.plan(raw=raw.decode())
                scratch = host.root / 'work' / f'{sequence:03d}-owned-groups.log'
                report = host.root / 'reports' / f'{sequence:03d}-malformed-owned-groups.log'
                link = DRAFT.os.link
                def change_at_link(source, destination, **kwargs):
                    self.assertEqual(kwargs, {'follow_symlinks': False})
                    if case == 'growth':
                        source.write_bytes(b'x' * 1048577)
                    elif case in ('replacement', 'symlink'):
                        original = host.root / 'work/original-at-link'
                        source.rename(original)  # Keep the original inode live; replacement cannot reuse it.
                        if case == 'symlink':
                            source.symlink_to(original)
                        else:
                            source.write_bytes(raw)
                    elif case == 'same-size-bytes':
                        prior = source.lstat()
                        source.write_bytes(b'x' * len(raw))
                        DRAFT.os.utime(source, ns=(prior.st_atime_ns, prior.st_mtime_ns))
                    else:
                        for target in host.commands.tasks[:-1]:
                            target['log'].write_bytes(b'x' * 1048576)
                    return link(source, destination, **kwargs)
                with mock.patch.object(DRAFT.os, 'link', side_effect=change_at_link):
                    with self.assertRaisesRegex(RuntimeError, '^Malformed owned-process census$'):
                        host.commands.observe()
                task, receipt = host.commands.observer, host.commands.observer['receipt']
                self.assertEqual((task['log'], receipt['output']), (report, report.name))
                self.assertEqual(receipt['errors'], ['Malformed owned-process census', 'Malformed group census retention failed'])
                self.assertEqual(receipt['censusRetention'], {'status': 'FAILED', 'name': report.name, 'scratchRemoved': False})
                self.assertTrue(scratch.exists() and report.exists())
                self.assertEqual(report.is_symlink(), case == 'symlink')
                self.assertEqual(host.commands.within_cap(), case not in ('growth', 'aggregate'))
                self.assertNotIn('PRIVATE_', DRAFT.json.dumps(receipt))
                self.assertTrue(receipt['leaderReaped'] and receipt['groupQuiet'])
                self.assertFalse(receipt['normalJoin'] or receipt['forced'] or host.commands.normal())
                with self.assertRaisesRegex(RuntimeError, 'Observer failed without relevant target progress'):
                    host.commands.observe(cleaning=True)
                self.assertEqual(host.commands.failed_observer_progress, host.commands.progress)
                self.assertEqual((len(host.children), host.signals, host.sleeps), (sequence, [], []))


if __name__ == '__main__':
    unittest.main()
