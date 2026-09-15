"""Source predicates and mocked /proc races; no SDK, namespace or child execution.

Importing the draft loads definitions only. Synthetic receipts are not native or
isolation evidence. Primary must separately authorize even these tests.
"""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

SOURCE = Path(__file__).with_name('app8-android.py')
SPEC = importlib.util.spec_from_file_location('app8_android_draft', SOURCE)
DRAFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRAFT)


def waiting_commands(process, end=200.0):
    commands = object.__new__(DRAFT.Commands)  # No helper import/subreaper or process creation.
    commands.owner = SimpleNamespace(active={process.pid: process})
    commands.reports, commands.end = Path('/unused-reports'), end
    commands.events, commands.joined, commands.absence_proved = [], {}, False
    return commands


def phase_inputs(phase):
    nonce = 'a' * 32
    ready = {'phase': phase, 'nonce': nonce, 'pid': 123, 'bindHost': '127.0.0.1', 'port': 43210,
             'lifetimeSeconds': 25, 'readyMonotonicSeconds': 100.0, 'deadlineMonotonicSeconds': 125.0}
    receipt = dict(ready, closedMonotonicSeconds=125.1, elapsedSeconds=25.1,
                   fixtureOK=True, windowComplete=True, errors=[], connections=[], receivedBytes=0)
    native = {'phase': phase, 'nonce': nonce, 'sdk': 26, 'minSdk': 26, 'targetSdk': 36,
              'proxyHost': '127.0.0.1', 'proxyPort': 43210, 'ok': True, 'observations': []}
    for host in DRAFT.HOSTS:
        row = {'url': f'http://{host}/{nonce}', 'policyPermits': phase == 'allow'}
        if phase == 'allow':
            row.update(outcome='canned-response', responseCode=200, usingProxy=True,
                       receivedBodyBytes=len(f'app8-no-forward {nonce} {host}\n'))
            receipt['connections'].append({'error': None, 'bytes': 128, 'host': host,
                                           'cannedResponseSent': True, 'peerEOF': True})
            receipt['receivedBytes'] += 128
        else:
            row.update(outcome='native-cleartext-policy-rejection', responseCode=None, receivedBodyBytes=0,
                       errorClass='java.io.IOException', errorMessage=f'Cleartext HTTP traffic to {host} not permitted')
        native['observations'].append(row)
    return [native, ready, receipt, phase, nonce, 123, 101.0, 110.0]


class SourcePredicates(unittest.TestCase):
    def test_current_checkpoint_binding_rejects_stale_historical_source_before_host_setup(self):
        request = json.loads(SOURCE.with_name('app8-android.request.json').read_text())
        with mock.patch.dict(DRAFT.os.environ, {}, clear=True):
            with mock.patch.object(DRAFT, 'read_json', return_value=request):
                with self.assertRaisesRegex(RuntimeError, 'Public synthetic draft has no execution authorization'):
                    DRAFT.outside()
            request['authorization'] = 'APP8_ANDROID_SINGLE_RUN_AUTHORIZED'
            with mock.patch.object(DRAFT, 'read_json', return_value=request):
                with self.assertRaisesRegex(RuntimeError, 'Wrong hosted invocation'):
                    DRAFT.outside()  # Current binding accepted, then stopped before any owner/SDK setup.
            hosted = {'GITHUB_REPOSITORY': 'kira-manga/kira-admin',
                      'GITHUB_REF': 'refs/heads/remediation/app-29-backend-complaints',
                      'GITHUB_EVENT_NAME': 'push', 'GITHUB_RUN_ATTEMPT': '1',
                      'RUNNER_ENVIRONMENT': 'github-hosted'}
            with mock.patch.dict(DRAFT.os.environ, hosted, clear=True):
                with mock.patch.object(DRAFT, 'read_json', return_value=request):
                    with self.assertRaisesRegex(RuntimeError, 'Wrong hosted invocation'):
                        DRAFT.outside()  # Old complaint carrier branch is not admitted.
            hosted['GITHUB_REF'] = 'refs/heads/validation/app8-libpulse-target-20260915-01'
            with mock.patch.dict(DRAFT.os.environ, hosted, clear=True):
                with mock.patch.object(DRAFT, 'read_json', return_value=request):
                    with mock.patch.object(DRAFT.platform, 'system', return_value='NOT_A_HOST'):
                        with self.assertRaisesRegex(RuntimeError, 'Hosted x86_64 Linux required'):
                            DRAFT.outside()  # Exact new branch accepted; stopped before path/owner/SDK setup.
            stale = {'issueSha': 'cebc952602fb69e03eb654dab30937e2f830a239',
                     'shippingBuildInputSha256': DRAFT.BUILD_HASH,
                     'shippingManifestSha256': DRAFT.APP_MANIFEST_HASH,
                     'acceptedSourceGuardResultSha256': DRAFT.GUARD_HASH}
            for field, value in stale.items():
                with self.subTest(field=field):
                    changed = dict(request, **{field: value})
                    with mock.patch.object(DRAFT, 'read_json', return_value=changed):
                        with self.assertRaisesRegex(RuntimeError, 'Unbound request/source'):
                            DRAFT.outside()

    def test_timed_out_scan_keeps_failure_with_bounded_partial_diagnostics(self):
        process = SimpleNamespace(pid=150, returncode=None, poll=mock.Mock(return_value=None))
        commands = waiting_commands(process)
        clock = iter((80.0, 110.023, 110.023))
        stat_stream = mock.mock_open(read_data=b'x' * 2049)

        def read_stat(path, mode, buffering):
            self.assertEqual((mode, buffering), ('rb', 0))
            if path == '/proc/150/io':
                raise PermissionError('proc I/O counters unavailable')
            self.assertEqual(path, '/proc/150/stat')
            return stat_stream()

        def link(path):
            if path == '/proc/150/fd/4':
                raise FileNotFoundError('descriptor closed between reads')
            return {'/proc/150/cwd': '/sdk', '/proc/150/fd/3': '/sdk/' + 'x' * 600,
                    '/proc/150/fd/5': '/usr/lib/python3.12', '/proc/150/fd/6': '/inputs'}[path]

        with mock.patch.object(DRAFT, 'CANCELLED', False), \
                mock.patch.object(DRAFT.time, 'monotonic', side_effect=lambda: next(clock, 110.023)), \
                mock.patch.object(DRAFT.time, 'sleep', side_effect=AssertionError('No diagnostic wait')), \
                mock.patch.object(DRAFT.os, 'sysconf', return_value=100), \
                mock.patch('builtins.open', side_effect=read_stat) as opened, \
                mock.patch.object(DRAFT.os, 'readlink', side_effect=link) as links, \
                mock.patch.object(DRAFT.os, 'listdir', side_effect=AssertionError('No fd enumeration')):
            with self.assertRaisesRegex(RuntimeError, 'Command failed, cancelled or exceeded its cap: 005-no-host-ipc.log'):
                commands.wait((process, Path('/reports/005-no-host-ipc.log')))
        event, = commands.events
        self.assertEqual((event['deadline'], event['ended'], event['actual_exit']), (110.0, 110.023, None))
        self.assertIs(event['normal_join'], False)
        self.assertEqual(commands.joined, {})
        process.poll.assert_called_once_with()  # No diagnostic poll/reap could release this PID.
        snapshot = event['scan_timeout_diagnostic']
        self.assertEqual((snapshot['pid'], snapshot['capturedMonotonicSeconds']), (150, 110.023))
        fields = snapshot['fields']
        self.assertEqual(fields['clockTicksPerSecond'], {'value': 100})
        self.assertEqual(fields['stat'], {'value': 'x' * 2048, 'truncated': True})
        self.assertEqual(fields['io'], {'unavailable': 'PermissionError'})
        self.assertEqual(fields['cwd'], {'value': '/sdk', 'truncated': False})
        self.assertEqual(fields['fd/3'], {'value': ('/sdk/' + 'x' * 600)[:512], 'truncated': True})
        self.assertEqual(fields['fd/4'], {'unavailable': 'FileNotFoundError'})
        self.assertEqual(opened.call_args_list, [mock.call('/proc/150/stat', 'rb', buffering=0),
                                                mock.call('/proc/150/io', 'rb', buffering=0)])
        stat_stream().read.assert_called_once_with(2049)
        self.assertEqual(links.call_args_list, [mock.call('/proc/150/' + name)
                                               for name in ('cwd', 'fd/3', 'fd/4', 'fd/5', 'fd/6')])

    def test_scan_diagnostic_stops_reads_on_ownership_or_cleanup_race(self):
        for race in ('lost-owner', 'reaped', 'cancelled', 'work-deadline'):
            with self.subTest(race=race):
                process = SimpleNamespace(pid=150, returncode=None)
                owner, clock = SimpleNamespace(active={150: process}), [100.0]

                def ticks(_name):
                    if race == 'lost-owner':
                        owner.active.clear()
                    elif race == 'reaped':
                        process.returncode = 0
                    elif race == 'cancelled':
                        DRAFT.CANCELLED = True
                    else:
                        clock[0] = 200.0
                    return 100

                with mock.patch.object(DRAFT, 'CANCELLED', False), \
                        mock.patch.object(DRAFT.time, 'monotonic', side_effect=lambda: clock[0]), \
                        mock.patch.object(DRAFT.os, 'sysconf', side_effect=ticks), \
                        mock.patch('builtins.open') as opened, \
                        mock.patch.object(DRAFT.os, 'readlink') as links:
                    snapshot = DRAFT.scan_timeout_diagnostic(owner, process, 200.0)
                self.assertEqual(snapshot['fields']['clockTicksPerSecond'], {'value': 100})
                reason = ('not_owned_unreaped_child' if race in ('lost-owner', 'reaped')
                          else 'cancelled_or_work_deadline')
                self.assertEqual({name: field for name, field in snapshot['fields'].items() if name != 'clockTicksPerSecond'},
                                 {name: {'unavailable': reason} for name in ('stat', 'io', 'cwd', 'fd/3', 'fd/4', 'fd/5', 'fd/6')})
                opened.assert_not_called()
                links.assert_not_called()

    def test_scan_diagnostic_is_not_used_for_other_exits_or_unowned_pid(self):
        for label, code, owned, cleaning, cancelled in (
                ('other-command', None, True, False, False), ('no-host-ipc', 0, True, False, False),
                ('no-host-ipc', 1, True, False, False), ('no-host-ipc', None, False, False, False),
                ('no-host-ipc', None, True, True, False), ('no-host-ipc', None, True, False, True)):
            with self.subTest(label=label, code=code, owned=owned, cleaning=cleaning, cancelled=cancelled):
                process = SimpleNamespace(pid=150, returncode=code, poll=mock.Mock(return_value=code))
                commands = waiting_commands(process, end=110.0)
                if not owned:
                    commands.owner.active.clear()
                with mock.patch.object(DRAFT, 'CANCELLED', cancelled), \
                        mock.patch.object(DRAFT.time, 'monotonic', return_value=110.0), \
                        mock.patch.object(DRAFT, 'scan_timeout_diagnostic') as diagnostic:
                    with self.assertRaisesRegex(RuntimeError, 'Command failed, cancelled or exceeded its cap:'):
                        commands.wait((process, Path('/reports/005-' + label + '.log')), cleaning=cleaning)
                diagnostic.assert_not_called()
                self.assertNotIn('scan_timeout_diagnostic', commands.events[-1])
                self.assertIs(commands.events[-1]['normal_join'], False)
                self.assertEqual(commands.joined, {})

    def test_failed_empty_drain_proves_absence_but_unknown_or_forced_is_never_normal(self):
        receipt = {'ok': True, 'empty': True, 'term': [], 'kill': [], 'remaining': [], 'active_popen': [],
                   'errors': {}, 'leaders': [{'pid': 2113, 'actual_exit': 0}, {'pid': 2206, 'actual_exit': 1}],
                   'adopted': []}  # Android05 outside shape: preparation joined; failed isolation did not.
        forced = dict(receipt, term=[2206], leaders=[{'pid': 2206, 'actual_exit': -15}])
        commands = waiting_commands(SimpleNamespace(pid=2206))
        commands.owner = SimpleNamespace(drain=mock.Mock())
        with mock.patch.object(DRAFT, 'save') as saved:
            for name, value, joined, absent in (
                    ('failed-empty', receipt, {2113: 0}, True), ('forced-empty', forced, {2206: -15}, True),
                    ('unknown', dict(receipt, ok=False, empty=None, errors={'children': 'unavailable'}), {}, False),
                    ('remaining', dict(receipt, remaining=[2206]), {}, False),
                    ('active', dict(receipt, active_popen=[2206]), {}, False)):
                with self.subTest(name=name):
                    commands.absence_proved, commands.joined = True, joined
                    commands.owner.drain.return_value = value
                    self.assertIs(commands.dispose(name), False)
                    self.assertIs(commands.absence_proved, absent)
                    self.assertEqual(saved.call_args_list[-2], mock.call(commands.reports / (name + '-children.json'), value))
            commands.absence_proved = True
            commands.owner.drain.side_effect = OSError('Current drain unavailable')
            with self.assertRaises(OSError):
                commands.dispose('drain-error')
            self.assertIs(commands.absence_proved, False)

    def test_loopback_only_and_route_refusals(self):
        links = [{'ifname': 'lo', 'flags': ['UP', 'LOOPBACK']}]
        addresses = [{'ifname': 'lo', 'addr_info': [{'local': '127.0.0.1'}, {'local': '::1'}]}]
        routes = [{'dev': 'lo', 'dst': '127.0.0.0/8'}, {'dev': 'lo', 'dst': '::1'}]
        DRAFT.check_topology(links, addresses, routes)
        cases = [
            (links + [{'ifname': 'eth0', 'flags': ['UP']}], addresses, routes),
            (links, addresses, routes + [{'dev': 'eth0', 'dst': 'default', 'gateway': '192.0.2.1'}]),
            (links, addresses, routes + [{'dev': 'lo', 'dst': 'default'}]),
            (links, addresses, routes + [{'dev': 'lo', 'dst': '::/0', 'via': '::1'}]),
            (links, [{'ifname': 'lo', 'addr_info': [{'local': '192.0.2.1'}]}], routes),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                DRAFT.check_topology(*case)

    def test_forced_or_abnormal_cleanup_never_normal(self):
        receipt = {'ok': True, 'empty': True, 'term': [], 'kill': [], 'remaining': [], 'active_popen': [],
                   'errors': {}, 'leaders': [{'pid': 456, 'actual_exit': 1}], 'adopted': [{'actual_exit': 0}]}
        # A known readiness/pidof exit 1 is checked by its explicit command caller.
        self.assertTrue(DRAFT.normal_drain(receipt, {456: 1}))
        self.assertFalse(DRAFT.normal_drain(receipt, {}))
        self.assertFalse(DRAFT.normal_drain(receipt, {456: 0}))
        for key, value in [('term', [123]), ('kill', [123]), ('remaining', [123]), ('active_popen', [123]),
                           ('errors', {'123': 'unreaped'}), ('empty', None), ('adopted', [{'actual_exit': -9}])]:
            with self.subTest(key=key):
                changed = dict(receipt, **{key: value})
                self.assertFalse(DRAFT.normal_drain(changed, {456: 1}))

    def test_exact_allow_and_deny_synthetic_receipts(self):
        for phase in ('allow', 'deny'):
            DRAFT.accept_phase(*phase_inputs(phase))

    def test_generic_connectivity_failure_is_not_native_denial(self):
        for field, value in [('errorClass', 'java.net.SocketTimeoutException'), ('errorMessage', 'Connection refused'),
                             ('outcome', 'policy-getter-only'), ('responseCode', 200), ('receivedBodyBytes', 1)]:
            changed = phase_inputs('deny')
            changed[0]['observations'][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                DRAFT.accept_phase(*changed)
        changed = phase_inputs('allow')
        changed[0]['observations'][0]['usingProxy'] = False
        with self.assertRaises(RuntimeError):
            DRAFT.accept_phase(*changed)

    def test_window_and_receiver_bindings(self):
        base = phase_inputs('deny')
        changes = [(6, None, 102.1), (7, None, 125.1), (2, 'closedMonotonicSeconds', 124.9),
                   (2, 'elapsedSeconds', 24.9), (2, 'windowComplete', False), (2, 'receivedBytes', 1),
                   (1, 'pid', 124), (1, 'nonce', 'b' * 32), (1, 'lifetimeSeconds', 24)]
        for index, field, value in changes:
            changed = copy.deepcopy(base)
            if field is None:
                changed[index] = value
            else:
                changed[index][field] = value
            with self.subTest(index=index, field=field), self.assertRaises(RuntimeError):
                DRAFT.accept_phase(*changed)

    def test_draft_is_not_an_authorization_and_trigger_is_dedicated(self):
        request = json.loads(SOURCE.with_name('app8-android.request.json').read_text())
        self.assertEqual(request['authorization'], 'DRAFT_NOT_AUTHORIZED')
        self.assertEqual(request['orchestratorSha256'], DRAFT.digest(SOURCE))
        checkpoint = SOURCE.parent.parent / 'docs/remediation/app8-native/checkpoint-policy-provenance.json'
        self.assertEqual(request['checkpointProvenanceSha256'], DRAFT.digest(checkpoint))
        workflow = (SOURCE.parent.parent / '.github/workflows/app8-android.yml').read_text()
        branch = 'validation/app8-libpulse-target-20260915-01'
        self.assertIn('branches: [' + branch + ']', workflow)
        self.assertIn("github.ref == 'refs/heads/" + branch + "'", workflow)
        self.assertIn('github.event.repository.private == false', workflow)
        self.assertNotIn('github.event.repository.private == true', workflow)
        self.assertIn("os.environ.get('GITHUB_REF') == 'refs/heads/" + branch + "'", SOURCE.read_text())
        self.assertNotIn('remediation/app-29-backend-complaints', workflow)
        self.assertIn('contents: read', workflow)
        self.assertIn('retention-days: 3', workflow)
        self.assertIn('public synthetic', workflow)
        self.assertIn('github.run_attempt == 1', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        report_names = ('result.json', 'native-summary.json', 'source-bindings.json', 'tool-identities.json',
                        'runtime-profile.json', 'isolation.json', 'packages.json', 'owned-intent.json',
                        'namespace-membership.json', 'preparation-children.json', 'inside-children.json',
                        'outside-children.json', 'inside-commands.json', 'allow-result.json', 'deny-result.json',
                        '001-libpulse0-package-status.log', '002-prepare-required-libpulse0.log',
                        '005-no-host-ipc.log', '009-emulator-version.log',
                        '*-allow-native.log', '*-deny-native.log')
        prefix = '${{ runner.temp }}/app8-android-${{ github.run_id }}-${{ github.run_attempt }}/reports/'
        self.assertEqual(workflow.count('          path: |\n'), 1)
        published = workflow.split('          path: |\n', 1)[1].split('          retention-days:', 1)[0]
        self.assertEqual([line.strip() for line in published.splitlines()], [prefix + name for name in report_names])
        self.assertIn('paths: [ci/app8-android.request.json]', workflow)
        self.assertIn('timeout-minutes: 10', workflow)
        self.assertNotIn('workflow_dispatch', workflow)
        self.assertNotIn('macos-', workflow)

    def test_source_wires_fence_and_preparation_barrier(self):
        text = SOURCE.read_text()
        self.assertIn("'--net', '--mount', '--ipc', '--pid', '--fork', '--kill-child=KILL'", text)
        self.assertIn('--bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs', DRAFT.BOOTSTRAP)
        self.assertIn('hosts: files', DRAFT.BOOTSTRAP)
        self.assertNotIn('socket.AF_VSOCK', text)
        self.assertIn("'nonIpConfinement': 'not-claimed'", text)
        self.assertNotIn("'vsock': 'unavailable'", text)
        self.assertNotIn('image.rglob', text)
        self.assertIn("str((image / 'source.properties').relative_to(sdk))", text)
        self.assertIn('expected_tools + [image_properties]', text)
        self.assertIn("for relative, expected in runtime['sdkHashes'].items()", text)
        self.assertEqual(json.loads(SOURCE.with_name('app8-android.request.json').read_text())['toolchain']['missingSdkPreparationSeconds'], 120)
        self.assertIn("'systemImage': IMAGE, 'missingSdkPreparationSeconds': 120", text)
        request = json.loads(SOURCE.with_name('app8-android.request.json').read_text())
        self.assertEqual(request['shippingCompileSdk'], 37)
        self.assertEqual(request['toolchain']['compilePlatform'], 'android-36')
        self.assertIn("request['shippingCompileSdk'] == 37", text)
        self.assertIn("metadata['android']['compileSdk'] == 37", text)
        self.assertEqual(text.count("'probeCompilePlatform': tools['compilePlatform']"), 2)
        self.assertIn("Path('/sdk/platforms/android-36/android.jar')", text)
        self.assertIn("'platforms;android-36': ('platforms/android-36/android.jar',)", text)
        self.assertNotIn('android-37', text)
        self.assertIn("'prepare-missing-declared-sdk', seconds=120)", text)
        self.assertLess(text.index('Missing installed SDK command-line tool'), text.index('package_inputs = {'))
        self.assertLess(text.index('Missing installed JDK17'), text.index('package_inputs = {'))
        self.assertLess(text.index('Primary checkpoint does not attest'), text.index('package_inputs = {'))
        self.assertLess(text.index("inputs / 'request.json'"), text.index('package_inputs = {'))
        self.assertLess(text.index('package_inputs = {'), text.index("'prepare-missing-declared-sdk'"))
        self.assertEqual(text.count("'prepare-missing-declared-sdk'"), 1)
        outside = text.split('def outside():', 1)[1]
        pulse = outside.split("pulse_library = Path('/usr/lib/x86_64-linux-gnu/libpulse.so.0')", 1)[1].split("image = sdk /", 1)[0]
        self.assertIn("['/usr/bin/dpkg-query', '-W', '-f=${Status}', 'libpulse0']", pulse)
        self.assertIn("'libpulse0-package-status', seconds=5, accepted=(0, 1)", pulse)
        self.assertIn("pulse_prepared = pulse_status != 'install ok installed' or not pulse_present\n        if pulse_prepared:", pulse)
        self.assertIn("require(time.monotonic() + 80 < deadline - 70", pulse)
        self.assertIn("['sudo', '-n', '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '60s'", pulse)
        self.assertIn("'/usr/bin/env', 'DEBIAN_FRONTEND=noninteractive', 'NEEDRESTART_MODE=l'", pulse)
        self.assertIn("'/usr/bin/apt-get', '--yes', '--no-install-recommends', '--no-remove',\n                          '-o', 'DPkg::Lock::Timeout=10', 'install', 'libpulse0']", pulse)
        self.assertIn("'prepare-required-libpulse0', seconds=70, end=deadline - 70)", pulse)
        self.assertIn('pulse_resolved = pulse_library.resolve(strict=True)', pulse)
        self.assertIn('pulse_resolved.is_file() and pulse_resolved.is_relative_to(pulse_library.parent)', pulse)
        self.assertEqual(text.count("'/usr/bin/apt-get'"), 1)
        self.assertLess(text.index("inputs / 'request.json'"), text.index("'libpulse0-package-status'"))
        self.assertLess(text.index("'prepare-required-libpulse0'"), text.index("commands.dispose('preparation')"))
        inside = text.split('def inside():', 1)[1].split('def outside():', 1)[0]
        self.assertIn("pulse_library = Path('/usr/lib/x86_64-linux-gnu/libpulse.so.0')", inside)
        self.assertIn('pulse_resolved = pulse_library.resolve(strict=True)', inside)
        self.assertIn("pulse_resolved.is_relative_to(pulse_library.parent)\n                and str(pulse_resolved) == runtime['libpulse0']['resolvedPath']", inside)
        self.assertIn("digest(pulse_resolved, commands.end) == runtime['libpulse0']['sha256']", inside)
        self.assertLess(inside.index('pulse_resolved.is_relative_to'), inside.index('digest(pulse_resolved,'))
        self.assertIn("'resolvedPath': str(pulse_resolved)", outside)
        self.assertIn("'sha256': digest(pulse_resolved, deadline - 70)", outside)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'libpulse.so.fixture'
            target.write_bytes(b'app8 synthetic SONAME target\n')
            soname = Path(directory) / 'libpulse.so.0'
            soname.symlink_to(target.name)
            with self.assertRaisesRegex(RuntimeError, 'Missing/nonregular bound input'):
                DRAFT.digest(soname)  # Generic digest remains strict.
            self.assertEqual(DRAFT.digest(soname.resolve(strict=True)), DRAFT.digest(target))
        self.assertLess(text.index("commands.dispose('preparation')"), text.index('Missing required SDK tool/platform after preparation'))
        self.assertLess(text.index("commands.dispose('preparation')"), text.index("commands.start(['sudo'"))
        self.assertEqual(text.count("commands.run(['/jdk/bin/javac'"), 1)
        self.assertLess(text.index('output_ok = logs_within_cap(reports)  # Evaluate final bytes'), text.index('stream.truncate'))
        self.assertIn("normal_cleanup = commands.dispose('outside')\n        absence = commands.absence_proved", text)
        self.assertIn('passed and normal_cleanup and absence and output_ok and scratch_removed and not CANCELLED', text)
        self.assertIn("'normalOwnedCleanup': normal_cleanup", text)
        self.assertIn("'ownedProcessAbsenceProved': absence", text)

        # Relevant rows from the hash-matched aapt2 36.0.0 local allow dump.
        namespace = 'http://schemas.android.com/apk/res/android:'
        manifest = f'''    A: package="me.manga.kira.transportprobe" (Raw: "me.manga.kira.transportprobe")
        A: {namespace}minSdkVersion(0x0101020c)=26
        A: {namespace}targetSdkVersion(0x01010270)=36
        A: {namespace}debuggable(0x0101000f)=false
        A: {namespace}networkSecurityConfig(0x01010527)=@0x7f010000
'''
        policy = '''E: network-security-config (line=2)
    E: domain-config (line=3)
      A: cleartextTrafficPermitted=true
        E: domain (line=4)
          A: includeSubdomains=true
            T: 'raijinscan.co'
'''
        resources = '    resource 0x7f010000 xml/network_security_config\n'
        DRAFT.inspect_package(manifest, policy, resources, 'allow')
        deny = 'E: network-security-config\n    E: base-config\n      A: cleartextTrafficPermitted=false\n'
        DRAFT.inspect_package(manifest, deny, resources, 'deny')  # Synthetic deny spelling, not native evidence.
        legacy = manifest.replace(namespace, 'android:').replace(')=26', ')=(type 0x10)0x1a').replace(')=36', ')=(type 0x10)0x24')
        for true, false in [('(type 0x12)0xffffffff', '(type 0x12)0x0'),
                            ('"true" (Raw: "true")', '"false" (Raw: "false")')]:
            DRAFT.inspect_package(legacy.replace('=false', '=' + false), policy.replace('=true', '=' + true), resources, 'allow')
            DRAFT.inspect_package(legacy.replace('=false', '=' + false), deny.replace('=false', '=' + false), resources, 'deny')
        for bad, reason in [
                (manifest.replace(')=26', ')=25'), 'Wrong packaged SDK levels'),
                (manifest.replace(')=36', ')=37'), 'Wrong packaged SDK levels'),
                (manifest.replace(')=false', ')=true'), 'Unexpected compiled boolean'),
                (manifest.replace(namespace, ''), 'Missing/ambiguous compiled attribute'),
                (manifest.replace(namespace, 'http://example.invalid/android:'), 'Missing/ambiguous compiled attribute'),
                (manifest + f'A: {namespace}minSdkVersion(0x0101020c)=26\n', 'Missing/ambiguous compiled attribute'),
                (manifest + 'A: android:minSdkVersion(0x0101020c)=26\n', 'Missing/ambiguous compiled attribute'),
                (manifest.replace('@0x7f010000', '@0x7f010001'), 'does not reference the packaged XML')]:
            with self.subTest(reason=reason, manifest=bad):
                with self.assertRaisesRegex(RuntimeError, reason):
                    DRAFT.inspect_package(bad, policy, resources, 'allow')
        for bad in [policy.replace('cleartextTrafficPermitted=true', 'cleartextTrafficPermitted=false'),
                    policy.replace('includeSubdomains=true', 'includeSubdomains=false')]:
            with self.assertRaisesRegex(RuntimeError, 'Unexpected compiled boolean'):
                DRAFT.inspect_package(manifest, bad, resources, 'allow')

    def test_declared_runtime_prefixes_keep_one_complete_ipc_scan(self):
        bootstrap, text = DRAFT.BOOTSTRAP, SOURCE.read_text()
        prefixes = ['/usr/bin', '/usr/sbin', '/usr/lib/x86_64-linux-gnu', '/usr/lib64',
                    '/usr/lib/python3.12', '/usr/lib/locale']
        self.assertEqual(bootstrap.count('runtime_prefixes=(' + ' '.join(prefixes) + ')'), 1)
        self.assertEqual(bootstrap.count('runtime_prefixes='), 1)
        self.assertEqual(bootstrap.count('for prefix in "${runtime_prefixes[@]}"; do'), 1)
        self.assertIn('run mount --bind "$prefix" "$root$prefix"', bootstrap)
        self.assertIn('run mount -o remount,bind,ro,nosuid,nodev "$root$prefix"', bootstrap)
        self.assertNotIn('"/usr:usr"', bootstrap)
        self.assertNotIn('--rbind', bootstrap)
        sdk_prefixes = ['cmdline-tools/latest', 'platform-tools', 'emulator', 'build-tools/36.0.0',
                        'platforms/android-36', 'system-images/android-26/google_apis/x86_64']
        self.assertEqual(bootstrap.count('sdk_prefixes=(' + ' '.join(sdk_prefixes) + ')'), 1)
        scaffolds = bootstrap.split('for path in usr usr/lib sdk ', 1)[1].split('done', 1)[0]
        self.assertEqual(scaffolds.split('; do', 1)[0].replace('\\\n', ' ').split(),
                         ['sdk/cmdline-tools', 'sdk/build-tools', 'sdk/platforms', 'sdk/system-images',
                          'sdk/system-images/android-26', 'sdk/system-images/android-26/google_apis',
                          'jdk', 'inputs', 'work', 'reports', 'proc', 'sys', 'dev', 'dev/shm',
                          'tmp', 'run', 'var', 'var/tmp', 'etc'])
        self.assertIn('mkdir -p "$root/$path"; chown "$uid:$gid" "$root/$path"', scaffolds)
        self.assertEqual(bootstrap.count('chown '), 1)
        self.assertLess(bootstrap.index('chown "$uid:$gid" "$root/$path"'),
                        bootstrap.index('for prefix in "${runtime_prefixes[@]}"; do'))
        self.assertEqual(bootstrap.count('for prefix in "${sdk_prefixes[@]}"; do'), 2)
        self.assertIn('run mount --bind "$sdk/$prefix" "$root/sdk/$prefix"', bootstrap)
        self.assertIn('run mount -o remount,bind,ro,nosuid,nodev "$root/sdk/$prefix"', bootstrap)
        self.assertIn('run mount --bind "$sdk/.knownPackages" "$root/sdk/.knownPackages"', bootstrap)
        self.assertIn('run mount -o remount,bind,ro,nosuid,nodev "$root/sdk/.knownPackages"', bootstrap)
        self.assertNotIn('"$sdk:sdk"', bootstrap)
        self.assertIn('for pair in "$jdk:jdk" "$inputs:inputs" "$work:work" "$reports:reports"; do', bootstrap)
        self.assertIn('PATH=/jdk/bin:/usr/bin:/bin:/usr/sbin:/sbin HOME=/work/home', bootstrap)
        self.assertIn("sdk_hashes['.knownPackages'] = digest(sdk / '.knownPackages', deadline - 70)", text)
        self.assertLess(text.index("commands.dispose('preparation')"), text.index("sdk_hashes['.knownPackages']"))
        self.assertIn("'jdkJavaSha256': digest(jdk / 'bin/java')", text)
        self.assertIn("digest(Path('/jdk/bin/java'), commands.end) == runtime['jdkJavaSha256']", text)
        self.assertIn('for path in /usr /usr/lib "${runtime_prefixes[@]}" /usr/lib/python3.12/encodings /usr/lib/python3.12/lib-dynload;', bootstrap)
        self.assertIn('-d "$path" && ! -L "$path" && $(readlink -e "$path") == "$path"', bootstrap)
        self.assertIn('-L "$path" && $(readlink "$path") == "$target"', bootstrap)
        self.assertIn('-f "$path" && -x "$path" && ! -L "$path"', bootstrap)
        self.assertIn("grep -Fxq 'ID=ubuntu' /etc/os-release || fail_layout", bootstrap)
        self.assertIn("grep -Fxq 'VERSION_ID=\"24.04\"' /etc/os-release || fail_layout", bootstrap)
        self.assertLess(bootstrap.index("fail_layout '/usr/lib/python3.12/os.py"), bootstrap.index('run mount --make-rprivate /'))
        marker = 'cat > "$reports/runtime-profile.json" <<APP8_RUNTIME_PROFILE\n'
        profile = json.loads(bootstrap.split(marker, 1)[1].split('\nAPP8_RUNTIME_PROFILE', 1)[0])
        self.assertEqual(profile['readOnlyRuntimePrefixes'], prefixes)
        self.assertEqual(profile['profile'], 'ubuntu-24.04-x86_64-python3.12')
        self.assertEqual(profile['stage'], 'bootstrap-before-full-ipc-scan')
        self.assertEqual(profile['usrView'], 'synthetic')
        self.assertEqual(profile['sdkView'], 'synthetic-complete-packages')
        self.assertEqual(profile['readOnlySdkPackagePrefixes'], ['/sdk/' + prefix for prefix in sdk_prefixes])
        self.assertEqual(profile['readOnlySdkDiscoveryMetadata'], ['/sdk/.knownPackages'])
        self.assertEqual(profile['javaCommandPath'], '/jdk/bin/java')
        self.assertEqual(profile['mountFlags'], ['ro', 'nosuid', 'nodev'])
        self.assertIs(profile['recursiveBind'], False)
        self.assertIs(profile['layoutValidated'], True)
        self.assertIs(profile['prefixMountsApplied'], True)
        self.assertEqual(profile['nativeDependencyClosure'], 'unproved')
        self.assertEqual(profile['scanPerformance'], 'unproved')
        links = {'/bin': 'usr/bin', '/sbin': 'usr/sbin', '/lib': 'usr/lib', '/lib64': 'usr/lib64'}
        self.assertEqual(profile['mergedUsrLinks'], links)
        self.assertEqual(profile['python3LinkTarget'], 'python3.12')
        self.assertEqual(profile['loaderLinkTarget'], '$loader_spelling')
        self.assertEqual(profile['loaderCanonicalTarget'], '$loader_canonical')
        self.assertIn('loader_link=/usr/lib64/ld-linux-x86-64.so.2', bootstrap)
        self.assertIn('[[ -L "$loader_link" ]] || fail_layout', bootstrap)
        self.assertIn('loader_spelling=$(readlink -n "$loader_link" && printf .)', bootstrap)
        self.assertIn('loader_spelling=${loader_spelling%.}', bootstrap)
        self.assertIn('loader_canonical=$(readlink -e -n "$loader_link" && printf .)', bootstrap)
        self.assertIn('loader_canonical=${loader_canonical%.}', bootstrap)
        self.assertIn('loader_destination_allowed "$loader_spelling" "$loader_canonical" ||', bootstrap)
        checked_links = {**links, '/usr/bin/python3': profile['python3LinkTarget']}
        for path, target in checked_links.items():
            self.assertIn(path + ':' + target, bootstrap)
        self.assertLess(bootstrap.index('run mount -o remount,bind,ro "$root"'), bootstrap.index(marker))
        self.assertLess(bootstrap.index(marker), bootstrap.index('exec chroot'))
        self.assertIn('set -o noclobber', bootstrap)
        scan = "commands.run(['find', '/usr', '/jdk', '/sdk', '/inputs', '-type', 's', '-o', '-type', 'p'], 'no-host-ipc')"
        self.assertEqual(text.count(scan), 1)
        self.assertEqual(text.count("commands.run(['find'"), 1)
        self.assertEqual(DRAFT.Commands.run.__defaults__[0], 30)
        self.assertNotIn('-xdev', text)
        self.assertNotIn('-prune', text)


if __name__ == '__main__':
    unittest.main()
