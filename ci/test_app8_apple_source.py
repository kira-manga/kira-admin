"""Pure new parser/refusal tests only. No SDK/PF/child/fixture/native action."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('app8_apple_draft', Path(__file__).with_name('app8-apple.py'))
DRAFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRAFT)


def snapshot(armed=False):
    return {
        'status': 'Status: ' + ('Enabled' if armed else 'Disabled') + ' Debug: Urgent\n',
        'references': 'PID Process Name TOKEN TIMESTAMP\n123 pfctl 42 Thu Sep 10 2026\n' if armed else 'No pf starter references held\n',
        'rules': 'block drop quick all\n' if armed else 'scrub-anchor "com.apple/*" all fragment reassemble\nanchor "com.apple/*" all\n',
        'nat': '' if armed else 'nat-anchor "com.apple/*" all\nrdr-anchor "com.apple/*" all\n',
        'anchors': 'com.apple\n', 'states': '',
        'interfaces': 'ALL\nen0\nlo0' + (' (skip)' if armed else '') + '\nutun0\n',
        'ifconfig': 'lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384 index 1\n'
                    '\tinet 127.0.0.1 netmask 0xff000000\n\tinet6 ::1 prefixlen 128\n'
                    'en0: flags=8863<UP,BROADCAST,RUNNING,MULTICAST> mtu 1500 index 7\n'
                    '\tinet 192.0.2.2 netmask 0xffffff00\n\ttype: Ethernet\n\tstatus: active\n'
                    'utun0: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST> mtu 1380 index 8\n'
                    '\tinet6 fe80::1%utun0 prefixlen 64\n',
        'ipv4': 'Routing tables\nInternet:\nDestination Gateway Flags Netif Expire\ndefault 192.0.2.1 UGScg en0\n127 127.0.0.1 UCS lo0\n',
        'ipv6': 'Routing tables\nInternet6:\nDestination Gateway Flags Netif Expire\ndefault fe80::%utun0 UGcIg utun0\n::1 ::1 UHL lo0\n',
    }


def phase_inputs(phase):
    nonce, port, pid = 'a' * 32, 43210, 123
    ready = {'phase': phase, 'nonce': nonce, 'pid': pid, 'bindHost': '127.0.0.1', 'port': port, 'lifetimeSeconds': 25,
             'readyMonotonicSeconds': 100.0, 'deadlineMonotonicSeconds': 125.0}
    receipt = dict(ready, closedMonotonicSeconds=125.1, elapsedSeconds=25.1, fixtureOK=True, windowComplete=True,
                   errors=[], connections=[], receivedBytes=0)
    native = {'phase': phase, 'nonce': nonce, 'ok': True, 'failure': '', 'proxyHost': '127.0.0.1', 'proxyPort': port,
              'systemVersion': '26.4.1', 'deploymentTarget': '15.0', 'minimumIOS15RuntimeProven': False,
              'loadedATS': DRAFT.OLD_ATS if phase == 'allow' else None, 'observations': []}
    for host in DRAFT.HOSTS:
        row = {'url': f'http://{host}/{nonce}', 'violation': '', 'metrics': []}
        if phase == 'allow':
            row.update(responseURL=row['url'], outcome='canned-response', responseCode=200, errorDomain='', errorCode=0,
                       receivedBodyBytes=len(f'app8-no-forward {nonce} {host}\n'),
                       metrics=[{'proxy': True, 'networkLoad': True, 'remoteAddress': '127.0.0.1', 'remotePort': port}])
            receipt['connections'].append({'error': None, 'bytes': 128, 'host': host, 'cannedResponseSent': True, 'peerEOF': True})
            receipt['receivedBytes'] += 128
        else:
            row.update(outcome='native-ATS-policy-rejection', responseCode=None, errorDomain='NSURLErrorDomain', errorCode=-1022, receivedBodyBytes=0)
        native['observations'].append(row)
    return [native, ready, receipt, phase, nonce, pid, 101.0, 110.0]


class ParserRefusals(unittest.TestCase):
    def test_initial_profile_rejects_unknown_owner_skip_route_and_bypass(self):
        good = snapshot()
        DRAFT.check_pf(good)
        for key, value in (
            ('status', 'Status: Enabled Debug: Urgent'), ('references', ''), ('rules', 'pass all'),
            ('interfaces', good['interfaces'].replace('en0\n', 'en0 (skip)\n')),
            ('interfaces', good['interfaces'] + 'unknown0\n'),
            ('ifconfig', good['ifconfig'] + '\teflags=1<MANAGEMENT>\n'),
            ('ipv6', good['ipv6'].replace('utun0', 'unexpected0')),
        ):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                DRAFT.check_pf(dict(good, **{key: value}))

    def test_armed_profile_requires_exact_deny_sole_token_and_empty_states(self):
        good = snapshot(True)
        DRAFT.check_pf(good, '42')
        for key, value in (
            ('rules', 'block drop quick all\npass quick all\n'), ('nat', 'nat-anchor "com.apple/*" all'),
            ('states', 'nonempty state'), ('interfaces', good['interfaces'].replace('lo0 (skip)', 'lo0')),
            ('references', good['references'] + '124 pfctl 43 Thu Sep 10 2026\n'),
            ('references', good['references'].replace('pfctl 42', 'pfctl 43')),
            ('anchors', 'unknown-owner\n'),
        ):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                DRAFT.check_pf(dict(good, **{key: value}), '42')

    def test_token_is_observed_once_not_inferred_or_guessed(self):
        self.assertEqual(DRAFT.owned_token('No ALTQ support in kernel\nALTQ related functions disabled\npf enabled\nToken : 42\n'), '42')
        for text in ('', 'pf enabled', 'Token : 0', 'Token : 42\nToken : 43', 'Token : ' + str(2 ** 64)):
            with self.subTest(text=text), self.assertRaises(RuntimeError):
                DRAFT.owned_token(text)

    def test_release_requires_persisted_token_and_complete_absence(self):
        record = {'token': '42', 'policySha256': hashlib.sha256(DRAFT.PF_RULES.encode()).hexdigest()}
        absence = dict.fromkeys(('nativeAbsent', 'fixturesAbsent', 'commandsAbsent', 'workersAbsent', 'simulatorRemoved', 'receiptSaved'), True)
        self.assertTrue(DRAFT.may_release(record, '42', True, absence))
        for key in absence:
            self.assertFalse(DRAFT.may_release(record, '42', True, dict(absence, **{key: False})))
        self.assertFalse(DRAFT.may_release(None, '42', True, absence))
        self.assertFalse(DRAFT.may_release(record, None, True, absence))
        self.assertFalse(DRAFT.may_release(record, '42', False, absence))
        self.assertFalse(DRAFT.may_release(dict(record, token='43'), '42', True, absence))
        state = {'ownershipVerified': False, 'ownershipLost': False}
        with mock.patch.object(DRAFT, 'pf_snapshot', return_value=snapshot(True)):
            DRAFT.verify_owned_pf(None, 'synthetic', '42', state)
        self.assertTrue(state['ownershipVerified'])
        with mock.patch.object(DRAFT, 'pf_snapshot', side_effect=RuntimeError('synthetic lost readback')):
            with self.assertRaises(RuntimeError):
                DRAFT.verify_owned_pf(None, 'synthetic', '42', state)
        self.assertTrue(state['ownershipLost'])
        self.assertFalse(DRAFT.may_release(record, '42', state['ownershipVerified'], absence))
        with mock.patch.object(DRAFT, 'pf_snapshot', return_value=snapshot(True)):
            with self.assertRaises(RuntimeError):
                DRAFT.verify_owned_pf(None, 'synthetic', '42', state)

    def test_plist_derivation_preserves_literal_policy_and_refuses_unknown_placeholder(self):
        suffixes = ('download.processing', 'download.continued', 'library.refresh')
        original = {'CFBundleIdentifier': '$(PRODUCT_BUNDLE_IDENTIFIER)', 'NSAppTransportSecurity': DRAFT.OLD_ATS,
                    'BGTaskSchedulerPermittedIdentifiers': ['$(PRODUCT_BUNDLE_IDENTIFIER).' + suffix for suffix in suffixes],
                    'literal': {'nested': ['keep', True]}}
        before = copy.deepcopy(original)
        changed = DRAFT.derived_plist(original)
        self.assertEqual(changed['CFBundleIdentifier'], DRAFT.PACKAGE)
        self.assertEqual(changed['BGTaskSchedulerPermittedIdentifiers'], [DRAFT.PACKAGE + '.' + suffix for suffix in suffixes])
        self.assertEqual(changed['NSAppTransportSecurity'], original['NSAppTransportSecurity'])
        self.assertEqual(changed['literal'], original['literal'])
        self.assertEqual(original, before)
        for unknown in ('$(UNREVIEWED)', '$(UNREVIEWED).library.refresh',
                        '$(PRODUCT_BUNDLE_IDENTIFIER).unreviewed', 'prefix-$(PRODUCT_BUNDLE_IDENTIFIER).library.refresh',
                        '$(PRODUCT_BUNDLE_IDENTIFIER).library.refresh$(UNREVIEWED)'):
            with self.subTest(unknown=unknown), self.assertRaises(RuntimeError):
                DRAFT.derived_plist(dict(original, unknown=unknown))

    def test_ats_proxy_and_natural_window_oracles_do_not_accept_connectivity_failure(self):
        for phase in ('allow', 'deny'):
            DRAFT.accept_phase(*phase_inputs(phase))
        for field, value in (('errorCode', -1001), ('errorDomain', 'generic'), ('responseCode', 200), ('receivedBodyBytes', 1)):
            changed = phase_inputs('deny')
            changed[0]['observations'][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                DRAFT.accept_phase(*changed)
        changed = copy.deepcopy(phase_inputs('allow'))
        changed[0]['observations'][0]['metrics'][0]['proxy'] = False
        with self.assertRaises(RuntimeError):
            DRAFT.accept_phase(*changed)
        changed = phase_inputs('deny')
        changed[2]['windowComplete'] = False
        with self.assertRaises(RuntimeError):
            DRAFT.accept_phase(*changed)
        changed = phase_inputs('deny')
        changed[6] = 102.1
        with self.assertRaises(RuntimeError):
            DRAFT.accept_phase(*changed)


if __name__ == '__main__':
    unittest.main()
