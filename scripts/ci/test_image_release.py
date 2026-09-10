"""Focused offline release-boundary tests; fixtures are NOT Docker/platform approval evidence.

No Docker, SSH, scanner or network is executed. Only the subprocess-budget tests start small,
owned Python children. The separate authorized real-image rehearsal remains necessary.
"""

import base64
import contextlib
import copy
import datetime as dt
import http.client
import io
import json
import os
from pathlib import Path
import re
import signal
import stat
import struct
import sys
import tarfile
import tempfile
from types import TracebackType
import unittest
from unittest import mock
import urllib.error
import zipfile

import image_release as release

SHA, CONSUMER_SHA, MAIN_SHA, TREE = (digit * 40 for digit in '1234')
IMAGE = 'sha256:' + 'a' * 64
NOW = dt.datetime(2026, 9, 9, 12, tzinfo=dt.timezone.utc).timestamp()


def at(seconds=0):
    return dt.datetime.fromtimestamp(NOW + seconds, dt.timezone.utc).isoformat()


def change(document, path, value):
    for key in path[:-1]:
        document = document[key]
    document[path[-1]] = value


def zip_bytes(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as bundle:
        for name, value, mode in entries:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            bundle.writestr(info, value)
    return output.getvalue()


def tar_bytes(name, content):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as bundle:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        bundle.addfile(info, io.BytesIO(content))
    return output.getvalue()


def scan_report():
    return {
        'descriptor': {
            'name': 'grype', 'version': release.GRYPE_VERSION, 'timestamp': at(-60),
            'configuration': {
                'check-for-app-update': False, 'timestamp': True, 'fail-on-severity': 'high',
                'search': {'scope': 'squashed'}, 'only-fixed': False, 'only-notfixed': False,
                'ignore-wontfix': '', 'match-upstream-kernel-headers': True,
                'ignore': [], 'exclude': [], 'vex-documents': [], 'vex-add': [],
                'db': {'auto-update': True, 'require-update-check': True, 'validate-age': True,
                       'validate-by-hash-on-start': True, 'max-allowed-built-age': 432000000000000,
                       'update-url': release.GRYPE_DB_URL, 'max-update-check-frequency': 0},
            },
            'db': {'schemaVersion': '6.0.0', 'built': at(-3600), 'valid': True,
                   'from': 'https://grype.anchore.io/databases/v6/fixture.tar.zstd'},
        },
        'source': {'type': 'image', 'target': {'imageID': IMAGE}},
        'matches': [{'vulnerability': {'severity': 'Medium', 'fix': {'state': 'not-fixed'}}}],
    }


def inspected(image):
    return release.canonical([{'Id': image['id'], 'Os': image['os'], 'Architecture': image['architecture'],
                               'RepoTags': [image['tag']], 'Config': {'Labels': {
                                   'org.opencontainers.image.revision': image['revision'],
                                   'org.opencontainers.image.version': image['revision']}}}])


class Fixture:
    """Small explicit API/receipt model, not a replacement GitHub policy implementation."""

    def __init__(self, rehearsal=False):
        self.contract = {name: release.digest(name.encode()) for name in release.CONTRACT_FILES}
        self.ctx = {'repository': release.REPOSITORY, 'repository_id': 55, 'sha': CONSUMER_SHA,
                    'workflow_sha': CONSUMER_SHA, 'ref': 'refs/heads/main', 'event_name': 'workflow_dispatch',
                    'run_id': 202, 'run_attempt': 1, 'job': 'preflight'}
        path = release.CI if rehearsal else release.PROMOTION
        if rehearsal:
            self.ctx.update(sha=SHA, workflow_sha=SHA, ref='refs/heads/feature/admin8',
                            run_id=101, run_attempt=2, job='rehearsal')
        self.ctx['workflow_ref'] = f"{release.REPOSITORY}/{path}@{self.ctx['ref']}"
        self.selected = {'run_id': 101, 'run_attempt': 2, 'artifact_id': 303, 'zip_sha256': '0' * 64}
        repo = {'id': 55, 'full_name': release.REPOSITORY}
        producer = {'workflow': release.CI, 'run_id': 101, 'run_attempt': 2,
                    'event': 'workflow_dispatch' if rehearsal else 'push',
                    'ref': self.ctx['ref'] if rehearsal else 'refs/heads/main'}
        self.run = {'id': 101, 'run_attempt': 2, 'workflow_id': 60, 'path': release.CI,
                    'head_sha': SHA, 'head_branch': producer['ref'][11:], 'event': producer['event'],
                    'status': 'in_progress' if rehearsal else 'completed',
                    'conclusion': None if rehearsal else 'success', 'repository': repo, 'head_repository': repo}
        own = {**self.run, 'id': self.ctx['run_id'], 'run_attempt': self.ctx['run_attempt'],
               'workflow_id': 60 if rehearsal else 61, 'path': path, 'head_sha': self.ctx['sha'],
               'head_branch': self.ctx['ref'][11:], 'event': 'workflow_dispatch',
               'status': 'in_progress', 'conclusion': None}
        self.scan = scan_report()
        self.plain = tar_bytes('fixture.txt', b'NOT a Docker image; archive-integrity fixture only.\n')
        compressed = release.gzip.compress(self.plain, mtime=0)
        raw_scan = release.canonical(self.scan)
        self.receipt = {
            'schema': 1, 'purpose': 'no-deploy-rehearsal' if rehearsal else 'production-candidate',
            'source': {'repository': release.REPOSITORY, 'repository_id': 55, 'sha': SHA, 'tree': TREE},
            'producer': producer, 'contract': self.contract,
            'image': {'id': IMAGE, 'tag': 'kira-admin:' + SHA, 'os': 'linux', 'architecture': 'amd64', 'revision': SHA},
            'archive': {'bytes': len(compressed), 'sha256': release.digest(compressed),
                        'expanded_bytes': len(self.plain), 'expanded_sha256': release.digest(self.plain)},
            'scan': {'bytes': len(raw_scan), 'sha256': release.digest(raw_scan), 'result': 'pass',
                     'policy': release.SCAN_POLICY,
                     'tool': {'name': 'grype', 'version': release.GRYPE_VERSION, 'archive_sha256': release.GRYPE_SHA},
                     'database': {'schemaVersion': '6.0.0', 'built': at(-3600), 'valid': True,
                                  'from': self.scan['descriptor']['db']['from'], 'scanned_at': at(-60)}},
        }
        self.files = {'image.tar.gz': compressed, 'scan.json': raw_scan}
        self.render_receipt()
        self.blob = zip_bytes((name, value, stat.S_IFREG | 0o600) for name, value in self.files.items())
        self.selected['zip_sha256'] = release.digest(self.blob)
        self.artifact = {'id': 303, 'name': 'admin-image-101-2', 'expired': False, 'expires_at': at(86400),
                         'digest': 'sha256:' + self.selected['zip_sha256'], 'size_in_bytes': len(self.blob),
                         'workflow_run': {'id': 101, 'repository_id': 55, 'head_repository_id': 55,
                                          'head_sha': SHA, 'head_branch': producer['ref'][11:]}}
        self.records = {
            '': {**repo, 'private': True, 'default_branch': 'main', 'archived': False, 'disabled': False},
            '/actions/workflows/ci.yml': {'id': 60, 'path': release.CI, 'state': 'active'},
            '/actions/workflows/deploy-server3.yml': {'id': 61, 'path': release.PROMOTION, 'state': 'active'},
            '/actions/runs/101': copy.deepcopy(self.run), '/actions/runs/101/attempts/2': copy.deepcopy(self.run),
            '/git/ref/heads/main': {'ref': 'refs/heads/main', 'object': {'type': 'commit', 'sha': MAIN_SHA}},
        }
        self.records[f"/actions/runs/{self.ctx['run_id']}"] = own
        self.set_artifact(self.artifact)
        self.contracts = {sha: (TREE, copy.deepcopy(self.contract)) for sha in (SHA, CONSUMER_SHA, MAIN_SHA)}
        self.calls, self.downloads = [], []
        self.after_download = lambda: None

    def render_receipt(self):
        self.files['receipt.json'] = release.canonical(self.receipt)

    def set_artifact(self, artifact):
        self.records['/actions/artifacts/303'] = copy.deepcopy(artifact)
        self.records['/actions/runs/101/artifacts?per_page=100'] = {'total_count': 1, 'artifacts': [copy.deepcopy(artifact)]}

    def get(self, path):
        self.calls.append(path)
        return copy.deepcopy(self.records[path])

    def contract_at(self, sha):
        return copy.deepcopy(self.contracts[sha])

    def download(self, artifact, destination, expected):
        self.downloads.append(artifact)
        release.need(artifact == 303 and expected == {'bytes': len(self.blob), 'sha256': release.digest(self.blob)},
                     'fixture download identity mismatch')
        destination.write_bytes(self.blob)
        self.after_download()

    def api(self):
        return mock.Mock(get=self.get, contract=self.contract_at, download=self.download)

    def metadata(self):
        return {'sha': SHA, 'tree': TREE, 'contract': self.contract, 'purpose': self.receipt['purpose'],
                'producer': self.receipt['producer']}

    def write_files(self, directory):
        directory.mkdir(exist_ok=True)
        for name, content in self.files.items():
            (directory / name).write_bytes(content)


def policy_fixture():
    environment = {'name': 'production', 'can_admins_bypass': False,
                   'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True},
                   'protection_rules': [{'type': 'required_reviewers', 'prevent_self_review': True,
                                         'reviewers': [{'type': 'User', 'reviewer': {'id': 77, 'type': 'User', 'login': 'reviewer'}}]}]}
    branches = {'total_count': 1, 'branch_policies': [{'name': 'main', 'type': 'branch'}]}
    protection = {'enforce_admins': {'enabled': True}, 'allow_force_pushes': {'enabled': False},
                  'allow_deletions': {'enabled': False},
                  'required_pull_request_reviews': {'required_approving_review_count': 1, 'dismiss_stale_reviews': True,
                                                    'require_last_push_approval': True,
                                                    'bypass_pull_request_allowances': {'users': [], 'teams': [], 'apps': []}},
                  'required_status_checks': {'strict': True, 'contexts': ['verify', 'container'],
                                             'checks': [{'context': name, 'app_id': release.GITHUB_ACTIONS_APP_ID}
                                                        for name in ('verify', 'container')]}}
    return environment, branches, protection


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {'PATH': os.defpath, 'HOME': str(self.tmp),
                                                       'RUNNER_TEMP': str(self.tmp), 'GITHUB_TOKEN': 'fixture-token'}, clear=True))
        self.enterContext(mock.patch.object(release.time, 'time', return_value=NOW))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        # Any forgotten mock fails instead of accessing network, Docker, SSH or scanner.
        self.network = self.enterContext(mock.patch.object(release.OPENER, 'open', side_effect=AssertionError('unexpected network')))
        self.process = self.enterContext(mock.patch.object(release, 'command', side_effect=AssertionError('unexpected subprocess')))

    def use(self, fixture):
        self.enterContext(mock.patch.object(release, 'GitHub', return_value=fixture.api()))
        self.enterContext(mock.patch.object(release, 'local_contract', return_value=fixture.contract))


class CandidateTests(OfflineCase):
    def test_positive_candidate_verifies_real_zip_gzip_receipt_and_rechecks_metadata(self):
        fixture = Fixture()
        self.use(fixture)
        receipt = release.verify_candidate(self.tmp, fixture.ctx, fixture.selected)
        self.assertEqual(receipt, fixture.receipt)
        self.assertEqual((self.tmp / 'image.tar').read_bytes(), fixture.plain)
        self.assertEqual(fixture.downloads, [303])
        self.assertEqual(fixture.calls.count('/actions/runs/101/attempts/2'), 2)
        self.assertTrue((self.tmp / 'candidate.json').is_file())

    def test_wrong_trigger_ref_workflow_or_context_never_downloads(self):
        for key, value in [('event_name', 'push'), ('ref', 'refs/tags/main'), ('repository', 'fork/admin'),
                           ('workflow_ref', 'fork/admin/.github/workflows/deploy-server3.yml@refs/heads/main'),
                           ('workflow_sha', SHA), ('repository_id', 999), ('run_attempt', 2)]:
            with self.subTest(key=key):
                fixture = Fixture()
                fixture.ctx[key] = value
                with mock.patch.object(release, 'local_contract', return_value=fixture.contract), self.assertRaises(release.Refused):
                    release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)
                self.assertFalse(fixture.downloads)

    def test_producer_latest_and_selected_attempt_must_both_be_eligible(self):
        bad = [('event', 'pull_request'), ('head_branch', 'feature/x'), ('workflow_id', 999), ('path', 'other.yml'),
               ('run_attempt', 3), ('head_sha', 'x' * 40), ('status', 'in_progress'), ('conclusion', 'failure'),
               ('head_repository', {'id': 999, 'full_name': release.REPOSITORY})]
        for endpoint in ('/actions/runs/101', '/actions/runs/101/attempts/2'):
            for key, value in bad:
                with self.subTest(endpoint=endpoint, key=key):
                    fixture = Fixture()
                    fixture.records[endpoint][key] = value
                    with mock.patch.object(release, 'local_contract', return_value=fixture.contract), self.assertRaises(release.Refused):
                        release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)

    def test_old_producer_and_old_consumer_cannot_agree_against_new_current_main(self):
        for changed_sha in (MAIN_SHA, CONSUMER_SHA, SHA):
            with self.subTest(changed_sha=changed_sha):
                fixture = Fixture()
                fixture.contracts[changed_sha][1]['scripts/ci/image_release.py'] = 'f' * 64
                with mock.patch.object(release, 'local_contract', return_value=fixture.contract), self.assertRaises(release.Refused):
                    release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)
        fixture = Fixture()
        with mock.patch.object(release, 'local_contract', return_value={}), self.assertRaises(release.Refused):
            release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)

    def test_missing_ambiguous_replaced_expired_or_unbound_artifact_fails(self):
        cases = [('expired', True), ('expires_at', at(-1)), ('id', 404), ('name', 'admin-image-101-1'),
                 ('digest', None), ('size_in_bytes', release.MAX_IMAGE + 1),
                 ('workflow_run', {'id': 999, 'repository_id': 55, 'head_repository_id': 55,
                                   'head_sha': SHA, 'head_branch': 'main'})]
        for key, value in cases:
            with self.subTest(key=key):
                fixture = Fixture()
                fixture.artifact[key] = value
                fixture.set_artifact(fixture.artifact)
                with mock.patch.object(release, 'local_contract', return_value=fixture.contract), self.assertRaises(release.Refused):
                    release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)
        for artifacts, count in (([], 0), ([Fixture().artifact] * 2, 2), ([Fixture().artifact], 101)):
            fixture = Fixture()
            fixture.records['/actions/runs/101/artifacts?per_page=100'] = {'artifacts': artifacts, 'total_count': count}
            with mock.patch.object(release, 'local_contract', return_value=fixture.contract), self.assertRaises(release.Refused):
                release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)

    def test_artifact_decoration_is_not_a_binding_but_required_fields_are(self):
        fixture = Fixture()
        fixture.records['/actions/artifacts/303']['url'] = 'https://api.github.com/decorative'
        with mock.patch.object(release, 'local_contract', return_value=fixture.contract):
            release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)
            fixture.records['/actions/artifacts/303']['size_in_bytes'] += 1
            with self.assertRaises(release.Refused):
                release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)

    def test_rerun_started_during_download_and_approved_fingerprint_change_fail(self):
        for race in (True, False):
            with self.subTest(race=race):
                fixture = Fixture()
                directory = self.tmp / str(race)
                directory.mkdir()
                if race:
                    fixture.after_download = lambda: fixture.records['/actions/runs/101'].update(run_attempt=3)
                with mock.patch.object(release, 'GitHub', return_value=fixture.api()), \
                     mock.patch.object(release, 'local_contract', return_value=fixture.contract), \
                     mock.patch.dict(os.environ, {'EXPECTED_CANDIDATE': '' if race else 'f' * 64}), self.assertRaises(release.Refused):
                    release.verify_candidate(directory, fixture.ctx, fixture.selected)
                self.assertFalse((directory / 'candidate.json').exists())

    def test_manual_rehearsal_is_own_attempt_only_and_never_production_eligible(self):
        fixture = Fixture(rehearsal=True)
        with mock.patch.object(release, 'local_contract', return_value=fixture.contract):
            metadata = release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected, rehearsal=True)
            self.assertEqual(metadata['purpose'], 'no-deploy-rehearsal')
            with self.assertRaises(release.Refused):
                release.candidate_metadata(fixture.api(), fixture.ctx, fixture.selected)
            with self.assertRaises(release.Refused):
                release.candidate_metadata(fixture.api(), fixture.ctx, {**fixture.selected, 'run_attempt': 1}, rehearsal=True)
        fixture.write_files(self.tmp)
        metadata['purpose'] = 'production-candidate'
        with self.assertRaises(release.Refused):
            release.validate_receipt(self.tmp, metadata, fixture.ctx)


class PolicyTests(OfflineCase):
    def test_native_policy_normalizes_only_enforced_fields(self):
        environment, branches, protection = policy_fixture()
        expected = release.validate_policy(environment, branches, protection)
        protection['required_status_checks']['checks'].reverse()
        protection['required_pull_request_reviews']['url'] = 'decorative'
        environment['protection_rules'][0]['reviewers'][0]['reviewer']['avatar_url'] = 'decorative'
        self.assertEqual(expected, release.validate_policy(environment, branches, protection))

    def test_missing_bypass_self_review_team_and_extra_ref_policies_fail(self):
        cases = [
            (0, ['can_admins_bypass'], True), (0, ['protection_rules'], []),
            (0, ['deployment_branch_policy'], None),
            (0, ['protection_rules', 0, 'prevent_self_review'], False),
            (0, ['protection_rules', 0, 'reviewers'], []),
            (0, ['protection_rules', 0, 'reviewers', 0, 'type'], 'Team'),
            (0, ['protection_rules', 0, 'reviewers', 0, 'reviewer', 'type'], 'Bot'),
            (1, ['branch_policies', 0, 'name'], '*'), (1, ['branch_policies', 0, 'type'], 'tag'),
            (1, ['total_count'], 2), (2, ['enforce_admins', 'enabled'], False),
            (2, ['allow_force_pushes', 'enabled'], True), (2, ['allow_deletions', 'enabled'], True),
            (2, ['required_pull_request_reviews', 'required_approving_review_count'], 0),
            (2, ['required_pull_request_reviews', 'dismiss_stale_reviews'], False),
            (2, ['required_pull_request_reviews', 'require_last_push_approval'], False),
            (2, ['required_pull_request_reviews', 'bypass_pull_request_allowances'], {'users': [77], 'teams': [], 'apps': []}),
            (2, ['required_status_checks', 'strict'], False), (2, ['required_status_checks', 'checks'], []),
            (2, ['required_status_checks', 'checks', 0, 'app_id'], -1),
            (2, ['required_status_checks', 'contexts'], ['verify']),
        ]
        for index, path, value in cases:
            with self.subTest(path=path):
                values = policy_fixture()
                change(values[index], path, value)
                with self.assertRaises(release.Refused):
                    release.validate_policy(*values)

    def test_absent_policy_token_and_unavailable_policy_api_never_write_proof(self):
        fixture = Fixture()
        with self.assertRaises(release.Refused):
            release.policy(self.tmp, fixture.ctx)
        self.network.assert_not_called()
        for code in (403, 404):
            api = mock.Mock()
            api.get.side_effect = urllib.error.HTTPError('https://api.github.com/fixture', code, 'unavailable', {}, io.BytesIO())
            with mock.patch.object(release, 'GitHub', return_value=api), self.assertRaises(urllib.error.HTTPError):
                release.policy(self.tmp, fixture.ctx)
        self.assertFalse((self.tmp / 'policy.json').exists())

    def test_policy_proof_binds_candidate_and_refuses_changed_approval_policy(self):
        fixture = Fixture()
        values = policy_fixture()
        records = dict(zip(('/environments/production', '/environments/production/deployment-branch-policies?per_page=100',
                            '/branches/main/protection'), values))
        api = mock.Mock(get=lambda path: records[path])
        release.write_json(self.tmp / 'candidate.json', {'fingerprint': 'e' * 64})
        with mock.patch.dict(os.environ, {'ADMIN8_POLICY_READ_TOKEN': 'fixture-policy-token'}), \
             mock.patch.object(release, 'GitHub', return_value=api) as constructor, \
             mock.patch.object(release, 'utc_now', return_value=at()):
            release.policy(self.tmp, fixture.ctx)
            constructor.assert_called_once_with('fixture-policy-token')
            proof = release.parse_json((self.tmp / 'policy.json').read_bytes(), release.MAX_RECEIPT)
            self.assertEqual((proof['candidate'], proof['run_id'], proof['attempt']), ('e' * 64, 202, 1))
            self.assertEqual(proof['checked_at'], at())
            os.environ['EXPECTED_POLICY'] = proof['fingerprint']
            values[2]['required_pull_request_reviews']['required_approving_review_count'] = 2
            with self.assertRaises(release.Refused):
                release.policy(self.tmp, fixture.ctx)


class ArchiveAndScanTests(OfflineCase):
    def test_duplicate_json_nan_and_oversized_receipt_are_rejected(self):
        for raw in (b'{"schema":1,"schema":1}', b'{"value":NaN}', b'\xff', b' ' * (release.MAX_RECEIPT + 1)):
            with self.subTest(raw=raw[:30]), self.assertRaises(release.Refused):
                release.parse_json(raw, release.MAX_RECEIPT)

    def test_zip_traversal_duplicate_link_unexpected_and_oversized_members_fail(self):
        fixture = Fixture()
        normal = [(name, content, stat.S_IFREG | 0o600) for name, content in fixture.files.items()]
        cases = [normal[:2] + [('../receipt.json', b'{}', stat.S_IFREG | 0o600)],
                 normal[:2] + [normal[0]], normal[:2] + [('receipt.json', b'target', stat.S_IFLNK | 0o777)],
                 normal + [('unexpected', b'x', stat.S_IFREG | 0o600)],
                 normal[:2] + [('receipt.json', b'x' * (release.MAX_RECEIPT + 1), stat.S_IFREG | 0o600)]]
        for index, entries in enumerate(cases):
            with self.subTest(index=index):
                archive, destination = self.tmp / f'{index}.zip', self.tmp / str(index)
                archive.write_bytes(zip_bytes(entries))
                destination.mkdir()
                with self.assertRaises(release.Refused):
                    release.unpack_zip(archive, destination)
        self.assertFalse((self.tmp / 'receipt.json').exists())

    def test_directory_bomb_is_rejected_before_zipfile_allocates_entries(self):
        archive = self.tmp / 'bomb.zip'
        archive.write_bytes(struct.pack('<4s4H2LH', b'PK\x05\x06', 0, 0, 65535, 65535, 0, 0, 0))
        with mock.patch.object(release.zipfile, 'ZipFile', side_effect=AssertionError('directory allocated')), self.assertRaises(release.Refused):
            release.unpack_zip(archive, self.tmp)

    def test_inner_archive_receipt_scan_and_image_identity_corruption_fails(self):
        mutations = [(['source', 'tree'], '9' * 40), (['producer', 'run_attempt'], 1),
                     (['contract', release.CI], 'f' * 64), (['image', 'architecture'], 'arm64'),
                     (['image', 'id'], 'sha256:' + 'b' * 64), (['image', 'revision'], CONSUMER_SHA),
                     (['archive', 'sha256'], 'f' * 64), (['archive', 'expanded_sha256'], 'f' * 64),
                     (['scan', 'sha256'], 'f' * 64), (['scan', 'result'], 'failure'),
                     (['scan', 'tool', 'archive_sha256'], 'f' * 64), (['unexpected'], True)]
        for index, (path, value) in enumerate(mutations):
            with self.subTest(path=path):
                fixture, directory = Fixture(), self.tmp / str(index)
                change(fixture.receipt, path, value)
                fixture.render_receipt()
                fixture.write_files(directory)
                with self.assertRaises(release.Refused):
                    release.validate_receipt(directory, Fixture().metadata(), fixture.ctx)

    def test_actual_gzip_tampering_and_expanded_byte_limit_fail(self):
        for tamper in (True, False):
            with self.subTest(tamper=tamper):
                fixture, directory = Fixture(), self.tmp / str(tamper)
                fixture.write_files(directory)
                if tamper:
                    (directory / 'image.tar.gz').write_bytes(fixture.files['image.tar.gz'] + b'x')
                with mock.patch.object(release, 'MAX_TAR', len(fixture.plain) - 1), self.assertRaises(release.Refused):
                    release.validate_receipt(directory, fixture.metadata(), fixture.ctx)

    def test_high_critical_including_unfixed_and_suppressed_or_unknown_results_fail(self):
        for severity in ('High', 'Critical', 'high', None):
            report = scan_report()
            report['matches'][0]['vulnerability']['severity'] = severity
            with self.subTest(severity=severity), self.assertRaises(release.Refused):
                release.validate_scan(report, IMAGE)
        report = scan_report()
        report['ignoredMatches'] = [{'vulnerability': {'severity': 'High'}}]
        with self.assertRaises(release.Refused):
            release.validate_scan(report, IMAGE)

    def test_scanner_version_database_update_age_hash_and_no_suppression_are_mandatory(self):
        cases = [(['descriptor', 'version'], '0.1.0'), (['descriptor', 'timestamp'], at(1)),
                 (['descriptor', 'timestamp'], at(-4 * 86400)), (['descriptor', 'db', 'valid'], False),
                 (['descriptor', 'db', 'error'], 'database failed'), (['descriptor', 'db', 'built'], at(-6 * 86400)),
                 (['descriptor', 'db', 'from'], 'https://untrusted.invalid/db'),
                 (['source', 'target', 'imageID'], 'sha256:' + 'b' * 64)]
        cases += [(['descriptor', 'configuration', field], value) for field, value in
                  [('only-fixed', True), ('only-notfixed', True), ('ignore-wontfix', 'not-fixed'),
                   ('match-upstream-kernel-headers', False), ('fail-on-severity', 'critical'),
                   ('ignore', [{'vulnerability': 'CVE-fixture'}]), ('exclude', ['/app']),
                   ('vex-documents', ['fixture.json']), ('vex-add', ['affected'])]]
        cases += [(['descriptor', 'configuration', 'db', field], value) for field, value in
                  [('auto-update', False), ('require-update-check', False), ('validate-age', False),
                   ('validate-by-hash-on-start', False), ('max-allowed-built-age', 0),
                   ('update-url', 'https://untrusted.invalid/db'), ('max-update-check-frequency', 3600)]]
        self.assertTrue(release.validate_scan(scan_report(), IMAGE)['valid'])
        for path, value in cases:
            with self.subTest(path=path):
                report = scan_report()
                change(report, path, value)
                with self.assertRaises(release.Refused):
                    release.validate_scan(report, IMAGE)


class ApiTests(OfflineCase):
    def test_download_authenticates_only_api_then_verifies_actual_zip_bytes(self):
        fixture = Fixture()
        requests = []

        def opened(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                raise urllib.error.HTTPError(request.full_url, 302, 'redirect',
                                             {'Location': 'https://fixture.blob.core.windows.net/image?signature=fixture'}, io.BytesIO())
            response = io.BytesIO(fixture.blob)
            response.status = 200
            return response

        self.network.side_effect = opened
        release.GitHub('fixture-api-token').download(303, self.tmp / 'artifact.zip',
                                                    {'bytes': len(fixture.blob), 'sha256': release.digest(fixture.blob)})
        self.assertEqual(requests[0].get_header('Authorization'), 'Bearer fixture-api-token')
        self.assertIsNone(requests[1].get_header('Authorization'))
        self.assertEqual((self.tmp / 'artifact.zip').read_bytes(), fixture.blob)

    def test_untrusted_redirect_wrong_digest_and_actual_byte_overflow_fail(self):
        for location in ('http://fixture.blob.core.windows.net/x', 'https://attacker.invalid/x',
                         'https://fixture.blob.core.windows.net.attacker.invalid/x',
                         'https://user:pass@fixture.blob.core.windows.net/x', 'https://fixture.blob.core.windows.net:444/x'):
            self.network.reset_mock()
            self.network.side_effect = urllib.error.HTTPError('https://api.github.com/fixture', 302, 'redirect',
                                                              {'Location': location}, io.BytesIO())
            with self.subTest(location=location), self.assertRaises(release.Refused):
                release.GitHub('fixture').download(303, self.tmp / 'absent.zip', {'bytes': 3, 'sha256': '0' * 64})
            self.assertEqual(self.network.call_count, 1)
        for ceiling in (2, 100):
            response = io.BytesIO(b'zip')
            response.status = 200
            self.network.side_effect = [urllib.error.HTTPError('https://api.github.com/fixture', 302, 'redirect',
                                                               {'Location': 'https://fixture.blob.core.windows.net/x'}, io.BytesIO()), response]
            with mock.patch.object(release, 'MAX_IMAGE', ceiling), self.assertRaises(release.Refused):
                release.GitHub('fixture').download(303, self.tmp / f'{ceiling}.zip', {'bytes': 3, 'sha256': '0' * 64})

    def test_api_pagination_and_storage_second_redirect_do_not_fall_back(self):
        response = io.BytesIO(b'{}')
        response.status, response.headers = 200, {'Link': '<https://api.github.com/next>; rel="next"'}
        self.network.side_effect = [response]
        with self.assertRaises(release.Refused):
            release.GitHub('fixture').get('/actions/artifacts')
        self.network.side_effect = [urllib.error.HTTPError('https://api.github.com/fixture', 302, 'redirect',
                                                           {'Location': 'https://fixture.blob.core.windows.net/x'}, io.BytesIO()),
                                    urllib.error.HTTPError('https://fixture.blob.core.windows.net/x', 302, 'redirect',
                                                           {'Location': 'https://attacker.invalid/x'}, io.BytesIO())]
        with self.assertRaises(urllib.error.HTTPError):
            release.GitHub('fixture').download(303, self.tmp / 'absent.zip', {'bytes': 1, 'sha256': '0' * 64})
        self.assertIsNone(release.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://attacker.invalid'))

    def test_git_contract_hashes_immutable_regular_blobs_and_rejects_incomplete_data(self):
        entries, records, expected = [], {}, {}
        for index, name in enumerate(release.CONTRACT_FILES, 1):
            blob, raw = f'{index:040x}', ('fixture ' + name).encode()
            entries.append({'path': name, 'type': 'blob', 'mode': '100644', 'sha': blob})
            records['/git/blobs/' + blob] = {'sha': blob, 'encoding': 'base64', 'size': len(raw),
                                            'content': base64.b64encode(raw).decode() + '\n'}
            expected[name] = release.digest(raw)
        records['/git/commits/' + SHA] = {'sha': SHA, 'tree': {'sha': TREE}}
        records['/git/trees/' + TREE + '?recursive=1'] = {'sha': TREE, 'truncated': False, 'tree': entries}
        api = release.GitHub('fixture')
        with mock.patch.object(api, 'get', side_effect=lambda path: copy.deepcopy(records[path])):
            self.assertEqual(api.contract(SHA), (TREE, expected))
            entries[0]['mode'] = '120000'
            with self.assertRaises(release.Refused):
                api.contract(SHA)
            entries[0]['mode'] = '100644'
            records['/git/trees/' + TREE + '?recursive=1']['truncated'] = True
            with self.assertRaises(release.Refused):
                api.contract(SHA)

    def test_local_contract_hashes_actual_checker_bytes_and_refuses_symlinks(self):
        root, expected = self.tmp / 'checkout', {}
        for name in release.CONTRACT_FILES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = ('local fixture ' + name).encode()
            path.write_bytes(raw)
            expected[name] = release.digest(raw)
        with mock.patch.object(release, 'ROOT', root):
            self.assertEqual(release.local_contract(), expected)
            helper = root / 'scripts/ci/image_release.py'
            helper.unlink()
            helper.symlink_to(root / 'Dockerfile')
            with self.assertRaises(release.Refused):
                release.local_contract()


class SmokeProbeTests(OfflineCase):
    @contextlib.contextmanager
    def probe_fixture(self):
        image, owner = Fixture().receipt['image'], 'f' * 32
        name = 'kira-admin8-smoke-' + owner
        self.network.reset_mock()
        self.process.reset_mock()
        self.process.side_effect = [inspected(image), b'created', b'started',
                                    release.canonical([{'Config': {'Labels': {'kira.admin8.smoke': owner}}}]), b'removed']
        with mock.patch.object(release.uuid, 'uuid4', return_value=mock.Mock(hex=owner)), \
             mock.patch.object(release.time, 'sleep') as sleeps, \
             mock.patch.object(release.signal, 'signal') as alarms, \
             mock.patch.object(release.signal, 'setitimer') as timer:
            yield image, sleeps, alarms
            self.assertEqual(timer.call_args_list, [mock.call(signal.ITIMER_REAL, 70), mock.call(signal.ITIMER_REAL, 0)])
        self.assertEqual(self.process.call_count, 5)
        self.assertEqual(self.process.call_args_list[1].args[0][-1], IMAGE)
        self.assertEqual(self.process.call_args_list[2], mock.call(['docker', 'start', name], seconds=30))
        self.assertEqual(self.process.call_args_list[-2:], [
            mock.call(['docker', 'container', 'inspect', name], seconds=30),
            mock.call(['docker', 'rm', '--force', name], seconds=30),
        ])

    def test_url_and_representative_bare_os_probe_failures_retry_until_200(self):
        response = io.BytesIO()
        response.status = 200
        with self.probe_fixture() as (image, sleeps, _alarms):
            # Representative paths, not an attribution of the historical OSError subtype.
            self.network.side_effect = [urllib.error.URLError('synthetic'), OSError('synthetic'),
                                        ConnectionResetError('synthetic'), http.client.RemoteDisconnected('synthetic'), response]
            self.assertIsNone(release.smoke(image))
            self.assertEqual(self.network.call_args_list, [mock.call('http://127.0.0.1:18082/', timeout=2)] * 5)
            self.assertEqual(sleeps.call_args_list, [mock.call(2)] * 4)
            self.assertTrue(response.closed)

    def test_persistent_os_failures_and_non_200_responses_exhaust_the_attempt_bound(self):
        for outcome in ('os', 'non-200'):
            with self.subTest(outcome=outcome), self.probe_fixture() as (image, sleeps, _alarms):
                def probe(*_args, **_kwargs):
                    if outcome == 'os':
                        raise OSError('synthetic persistent failure')
                    response = io.BytesIO()
                    response.status = 204
                    return response

                self.network.side_effect = probe
                with self.assertRaisesRegex(release.Refused, '^exact-image runtime smoke failed$'):
                    release.smoke(image)
                self.assertEqual(self.network.call_args_list, [mock.call('http://127.0.0.1:18082/', timeout=2)] * 30)
                self.assertEqual(sleeps.call_args_list, [mock.call(2)] * 30)

    def test_non_os_protocol_and_deadline_refusals_propagate_without_retry_and_with_cleanup(self):
        for failure in ('protocol', 'deadline'):
            with self.subTest(failure=failure), self.probe_fixture() as (image, sleeps, alarms):
                def expired(*_args, **_kwargs):
                    # Invoke the real deadline callback without scheduling a process-wide alarm.
                    alarms.call_args_list[0].args[1](signal.SIGALRM, None)

                protocol_error = http.client.BadStatusLine('synthetic protocol error')
                self.network.side_effect = protocol_error if failure == 'protocol' else expired
                expected = http.client.BadStatusLine if failure == 'protocol' else release.Refused
                with self.assertRaises(expected) as raised:
                    release.smoke(image)
                if failure == 'protocol':
                    self.assertIs(raised.exception, protocol_error)
                else:
                    self.assertEqual(str(raised.exception), 'network operation timed out')
                self.network.assert_called_once_with('http://127.0.0.1:18082/', timeout=2)
                sleeps.assert_not_called()


class RuntimeAndTransferTests(OfflineCase):
    def test_image_id_tag_platform_and_both_labels_are_inspected(self):
        image = Fixture().receipt['image']
        baseline = release.parse_json(inspected(image), 4096)
        for path, value in [([0, 'Id'], 'sha256:' + 'b' * 64), ([0, 'RepoTags'], []), ([0, 'Os'], 'windows'),
                            ([0, 'Architecture'], 'arm64'),
                            ([0, 'Config', 'Labels', 'org.opencontainers.image.revision'], CONSUMER_SHA),
                            ([0, 'Config', 'Labels', 'org.opencontainers.image.version'], CONSUMER_SHA)]:
            record = copy.deepcopy(baseline)
            change(record, path, value)
            self.process.side_effect = None
            self.process.return_value = release.canonical(record)
            with self.subTest(path=path), self.assertRaises(release.Refused):
                release.inspect_image(image)

    def test_smoke_executes_actual_id_and_removes_only_its_owned_container_on_failure(self):
        image, calls, owner = Fixture().receipt['image'], [], None

        def command(argv, **_kwargs):
            nonlocal owner
            calls.append(argv)
            if argv[:3] == ['docker', 'image', 'inspect']:
                return inspected(image)
            if argv[:2] == ['docker', 'create']:
                self.assertEqual(argv[-1], IMAGE)
                self.assertIn('KIRA_BACKEND_URL=http://127.0.0.1:9', argv)
                owner = argv[argv.index('--label') + 1].split('=', 1)[1]
                return b'fixture-container'
            if argv[:2] == ['docker', 'start']:
                raise release.Refused('injected start failure')
            if argv[:3] == ['docker', 'container', 'inspect']:
                return release.canonical([{'Config': {'Labels': {'kira.admin8.smoke': owner}}}])
            self.assertEqual(argv[:3], ['docker', 'rm', '--force'])
            return b''

        self.process.side_effect = command
        with self.assertRaises(release.Refused):
            release.smoke(image)
        self.assertEqual(calls[-1][:3], ['docker', 'rm', '--force'])
        self.assertTrue(calls[-1][-1].startswith('kira-admin8-smoke-'))

    def prepare_transfer(self, directory):
        fixture = Fixture()
        fixture.ctx['job'] = 'promote'
        self.use(fixture)
        fixture.write_files(directory)
        fingerprint = release.digest(release.canonical({'selection': fixture.selected, 'receipt': fixture.receipt}))
        release.write_json(directory / 'candidate.json', {'selection': fixture.selected, 'receipt': fixture.receipt, 'fingerprint': fingerprint})
        release.write_json(directory / 'policy.json', {'fingerprint': 'f' * 64, 'candidate': fingerprint,
                                                      'checked_at': at(-1), 'run_id': 202, 'attempt': 1})
        os.environ.update(EXPECTED_CANDIDATE=fingerprint, EXPECTED_POLICY='f' * 64, DEPLOY_KEY='fixture-private-key',
                          KNOWN_HOSTS='fixture-host ssh-ed25519 fixture-key', DEPLOY_HOST='server.example',
                          DEPLOY_USER='deploy', DEPLOY_PORT='22')
        return fixture

    def test_pre_key_failures_do_not_create_credentials_or_attempt_ssh(self):
        for issue in ('rerun', 'stale-policy', 'archive', 'image', 'destination', 'fingerprint'):
            with self.subTest(issue=issue):
                directory = self.tmp / issue
                fixture = self.prepare_transfer(directory)
                if issue == 'rerun':
                    fixture.records['/actions/runs/101']['run_attempt'] = 3
                elif issue == 'stale-policy':
                    proof = release.parse_json((directory / 'policy.json').read_bytes(), release.MAX_RECEIPT)
                    proof['checked_at'] = at(-181)
                    (directory / 'policy.json').write_bytes(release.canonical(proof))
                elif issue == 'archive':
                    (directory / 'image.tar.gz').write_bytes(b'tampered')
                elif issue == 'destination':
                    os.environ['DEPLOY_HOST'] = 'host; touch bad'
                elif issue == 'fingerprint':
                    os.environ['EXPECTED_CANDIDATE'] = 'e' * 64
                self.process.reset_mock()
                self.process.side_effect = release.Refused('injected image mismatch') if issue == 'image' else None
                self.process.return_value = inspected(fixture.receipt['image'])
                with mock.patch.object(release.os, 'open', wraps=os.open) as opened, self.assertRaises(release.Refused):
                    release.transfer(directory, fixture.ctx, fixture.selected)
                self.assertFalse(any(str(call.args[0]).endswith(('ssh-key', 'known-hosts')) for call in opened.call_args_list))
                self.assertFalse(any(call.args[0][0] == 'ssh' for call in self.process.call_args_list))
                self.assertFalse((directory / 'ssh-key').exists())
                self.assertFalse((directory / 'known-hosts').exists())

    def test_transfer_streams_original_gzip_fixed_gateway_and_cleans_keys_even_on_ssh_failure(self):
        for fail in (False, True):
            directory = self.tmp / str(fail)
            fixture = self.prepare_transfer(directory)
            transfers = []

            def command(argv, **kwargs):
                if argv[:3] == ['docker', 'image', 'inspect']:
                    return inspected(fixture.receipt['image'])
                self.assertEqual(argv[0], 'ssh')
                self.assertEqual(argv[-2:], ['deploy@server.example', 'deploy admin ' + SHA])
                for option in ('StrictHostKeyChecking=yes', 'IdentitiesOnly=yes', 'GlobalKnownHostsFile=/dev/null'):
                    self.assertIn(option, argv)
                self.assertEqual(argv[1:3], ['-F', '/dev/null'])
                for name in ('ssh-key', 'known-hosts'):
                    self.assertEqual(stat.S_IMODE((directory / name).stat().st_mode), 0o600)
                transfers.append(kwargs['stdin'].read())
                if fail:
                    raise release.Refused('injected SSH failure')
                return b''

            self.process.side_effect = command
            with self.subTest(fail=fail):
                if fail:
                    with self.assertRaises(release.Refused):
                        release.transfer(directory, fixture.ctx, fixture.selected)
                else:
                    release.transfer(directory, fixture.ctx, fixture.selected)
                self.assertEqual(transfers, [fixture.files['image.tar.gz']])
                self.assertFalse((directory / 'ssh-key').exists())
                self.assertFalse((directory / 'known-hosts').exists())

    def test_fresh_rehearsal_downloads_same_artifact_twice_without_rebuild(self):
        fixture = Fixture(rehearsal=True)
        self.use(fixture)
        with mock.patch.object(release, 'load_image') as loaded, mock.patch.object(release, 'smoke') as smoked, \
             mock.patch.object(release, 'remove_image') as removed:
            release.rehearse(self.tmp, fixture.ctx, fixture.selected)
        self.assertEqual(fixture.downloads, [303, 303])
        self.assertEqual(loaded.call_count, 2)
        self.assertEqual(smoked.call_args_list, [mock.call(fixture.receipt['image'])] * 2)
        self.assertEqual(removed.call_count, 2)
        self.process.assert_not_called()
        self.assertFalse((self.tmp / '1').exists())
        self.assertFalse((self.tmp / '2').exists())

    def test_partial_load_records_expected_tag_but_cleanup_refuses_a_different_image(self):
        image = Fixture().receipt['image']
        self.process.side_effect = release.Refused('injected partial Docker load failure')
        with self.assertRaises(release.Refused):
            release.load_image(self.tmp, self.tmp, image)
        self.assertTrue((self.tmp / 'owned-image.json').exists())
        wrong = {**image, 'id': 'sha256:' + 'b' * 64}
        self.process.reset_mock()
        self.process.side_effect = None
        self.process.return_value = inspected(wrong)
        with self.assertRaises(release.Refused):
            release.remove_image(self.tmp)
        self.assertFalse(any(call.args[0][:3] == ['docker', 'image', 'rm'] for call in self.process.call_args_list))
        self.process.side_effect = lambda argv, **_kwargs: inspected(image) if argv[:3] == ['docker', 'image', 'inspect'] else b''
        release.remove_image(self.tmp)
        self.assertFalse((self.tmp / 'owned-image.json').exists())

    def test_owned_cleanup_preserves_sibling_and_rejects_other_run_or_symlink(self):
        fixture = Fixture()
        os.environ.update({'GITHUB_' + key.upper(): str(value) for key, value in fixture.ctx.items()})
        scratch, sibling = self.tmp / 'kira-admin8-owned', self.tmp / 'unrelated'
        scratch.mkdir()
        sibling.mkdir()
        (sibling / 'keep').write_text('preserve')
        owner = {key: os.environ[key] for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_JOB')}
        release.write_json(scratch / 'owner.json', owner)
        self.assertEqual(release.owned(scratch), scratch)
        link = self.tmp / 'kira-admin8-link'
        link.symlink_to(sibling, target_is_directory=True)
        with self.assertRaises(release.Refused):
            release.owned(link)
        with mock.patch.dict(os.environ, {'GITHUB_RUN_ID': '999'}), self.assertRaises(release.Refused):
            release.owned(scratch)
        with mock.patch.object(sys, 'argv', ['image_release.py', 'cleanup', '--scratch', str(scratch)]), \
             mock.patch.object(release.signal, 'signal'), mock.patch.object(release.os, 'umask'), \
             mock.patch.object(release, 'remove_image', side_effect=release.Refused('injected Docker cleanup failure')), self.assertRaises(release.Refused):
            release.main()
        self.assertFalse(scratch.exists())
        self.assertEqual((sibling / 'keep').read_text(), 'preserve')


class ProducerTests(OfflineCase):
    def test_receipt_written_only_after_exact_id_smoke_one_export_and_successful_scan(self):
        for result in ('pass', 'smoke-error', 'tool-checksum', 'tool-error', 'database-error'):
            with self.subTest(result=result):
                fixture, directory = Fixture(), self.tmp / result
                directory.mkdir()
                ctx = {**fixture.ctx, 'sha': SHA, 'workflow_sha': SHA, 'event_name': 'push', 'job': 'container',
                       'workflow_ref': f'{release.REPOSITORY}/{release.CI}@refs/heads/main', 'run_id': 101, 'run_attempt': 2}
                # This executable is never run: command is mocked. Only its archive/checksum path is exercised.
                scanner = release.gzip.compress(tar_bytes('grype', b'fixture, not an executable'), mtime=0)
                calls = []

                def command(argv, **kwargs):
                    calls.append(argv)
                    if argv == ['git', 'rev-parse', 'HEAD']:
                        return SHA.encode() + b'\n'
                    if argv == ['git', 'status', '--porcelain', '--untracked-files=all']:
                        return b''
                    if argv == ['git', 'rev-parse', 'HEAD^{tree}']:
                        return TREE.encode() + b'\n'
                    if argv[:3] == ['docker', 'image', 'inspect']:
                        return inspected(fixture.receipt['image'])
                    if argv[:2] == ['docker', 'save']:
                        self.assertEqual(argv[2:], ['kira-admin:' + SHA])
                        kwargs['output'].write(fixture.plain)
                    elif argv[0] == 'gzip':
                        self.assertEqual(argv[-1], str(directory / 'image.tar'))
                        kwargs['output'].write(fixture.files['image.tar.gz'])
                    else:
                        self.assertEqual(argv[0], str(directory / 'grype'))
                        self.assertEqual(argv[-1], 'docker-archive:' + str(directory / 'image.tar'))
                        self.assertEqual(argv[1:3], ['--config', str(release.ROOT / 'scripts/ci/grype.yaml')])
                        self.assertEqual(set(kwargs['env']), {'PATH', 'HOME', 'TMPDIR', 'GRYPE_DB_CACHE_DIR'})
                        if result == 'tool-error':
                            raise release.Refused('injected scanner nonzero')
                        report = copy.deepcopy(fixture.scan)
                        if result == 'database-error':
                            report['descriptor']['db']['valid'] = False
                        kwargs['output'].write(release.canonical(report))
                    return b''

                self.process.side_effect = command
                with mock.patch.object(release, 'smoke', side_effect=release.Refused('injected smoke failure')
                                       if result == 'smoke-error' else None) as smoke, \
                     mock.patch.object(release.urllib.request, 'urlopen', return_value=io.BytesIO(scanner)), \
                     mock.patch.object(release, 'GRYPE_SHA', '0' * 64 if result == 'tool-checksum' else release.digest(scanner)), \
                     mock.patch.object(release, 'local_contract', return_value=fixture.contract):
                    if result == 'pass':
                        release.produce(directory, ctx, IMAGE)
                        receipt = release.parse_json((directory / 'receipt.json').read_bytes(), release.MAX_RECEIPT)
                        self.assertEqual(receipt['image'], fixture.receipt['image'])
                        self.assertEqual(receipt['archive'], fixture.receipt['archive'])
                        self.assertEqual(receipt['scan']['result'], 'pass')
                    else:
                        with self.assertRaises(release.Refused):
                            release.produce(directory, ctx, IMAGE)
                        self.assertFalse((directory / 'receipt.json').exists())
                    smoke.assert_called_once_with(fixture.receipt['image'])
                self.assertEqual(sum(argv[:2] == ['docker', 'save'] for argv in calls), 0 if result == 'smoke-error' else 1)


class FailureDiagnosticTests(OfflineCase):
    def diagnostic(self, error):
        value = release.failure_diagnostic(error)
        self.assertLessEqual(len(value.encode('ascii')) + 1, release.MAX_DIAGNOSTIC_BYTES)
        self.assertTrue(value.startswith('DIAGNOSTIC: '))
        return json.loads(value.removeprefix('DIAGNOSTIC: '))

    def test_projection_never_formats_sensitive_exception_data_or_class_names(self):
        secret = 'synthetic-secret https://credential@backend.invalid/private?token=synthetic'

        class SensitiveDiagnosticClass(Exception):
            def __str__(self):
                raise AssertionError('exception formatting must not run')

            __repr__ = __str__

        errors = [
            (SensitiveDiagnosticClass(secret, {'command': secret, 'environment': secret, 'locals': secret}), 'other'),
            (release.subprocess.CalledProcessError(7, [secret], output=secret, stderr=secret), 'process'),
            (urllib.error.HTTPError(secret, 500, secret, {'Authorization': secret}, None), 'network'),
            (release.Refused(secret), 'refused'),
        ]
        for error, family in errors:
            with self.subTest(family=family):
                self.assertEqual(self.diagnostic(error), {
                    'entries': [{'parent': None, 'via': 'raised', 'family': family,
                                 'lines': [], 'frames_limited': False}],
                    'chain_limited': False, 'chain_repeated': False,
                })

    def test_locations_are_helper_only_with_bounded_retention_and_traversal(self):
        try:
            release.need(False, 'synthetic refusal')
        except release.Refused as error:
            external, helper = error.__traceback__, error.__traceback__.tb_next
            entry = self.diagnostic(error)['entries'][0]
            self.assertEqual(entry['lines'], [helper.tb_lineno])
            self.assertFalse(entry['frames_limited'])
        # Synthetic traceback metadata puts a different helper line beyond the traversal cap.
        trace = TracebackType(None, helper.tb_frame, helper.tb_lasti, release.main.__code__.co_firstlineno)
        for _ in range(release.MAX_DIAGNOSTIC_TRACE):
            trace = TracebackType(trace, helper.tb_frame, helper.tb_lasti, helper.tb_lineno)
        trace = TracebackType(trace, external.tb_frame, external.tb_lasti, external.tb_lineno)
        entry = self.diagnostic(ValueError('synthetic-secret').with_traceback(trace))['entries'][0]
        self.assertEqual(entry['lines'], [helper.tb_lineno] * release.MAX_DIAGNOSTIC_FRAMES)
        self.assertTrue(entry['frames_limited'])
        self.assertTrue(all(0 < line <= release.MAX_DIAGNOSTIC_LINE for line in entry['lines']))

    def test_cleanup_failure_retains_the_primary_failure_as_a_separate_context_entry(self):
        primary, cleanup = KeyError('synthetic-primary-secret'), OSError('synthetic-cleanup-secret')
        image = Fixture().receipt['image']

        def command(argv, **_kwargs):
            if argv[:3] == ['docker', 'image', 'inspect']:
                return inspected(image)
            if argv[:2] == ['docker', 'create']:
                return b'fixture-container'
            if argv[:2] == ['docker', 'start']:
                raise primary
            self.assertEqual(argv[:3], ['docker', 'container', 'inspect'])
            raise cleanup

        self.process.side_effect = command
        try:
            release.smoke(image)
        except OSError as error:
            self.assertIs(error, cleanup)
            self.assertIs(error.__context__, primary)
            report = self.diagnostic(error)
        else:
            self.fail('expected the injected cleanup failure')
        entries = report['entries']
        self.assertEqual([entry['family'] for entry in entries], ['os', 'lookup'])
        self.assertEqual([entry['via'] for entry in entries], ['raised', 'context'])
        self.assertEqual([entry['parent'] for entry in entries], [None, 0])
        self.assertEqual([len(entry['lines']) for entry in entries], [1, 1])
        self.assertNotEqual(entries[0]['lines'], entries[1]['lines'])
        self.assertFalse(report['chain_limited'])

    def test_explicit_cause_suppressed_context_cycles_and_entry_limits_are_bounded(self):
        surfaced, cause, primary = OSError('synthetic'), TypeError('synthetic'), LookupError('synthetic')
        surfaced.__cause__, surfaced.__context__, surfaced.__suppress_context__ = cause, primary, True
        cause.__context__ = surfaced
        report = self.diagnostic(surfaced)
        self.assertEqual([entry['family'] for entry in report['entries']], ['os', 'type', 'lookup'])
        self.assertEqual([entry['via'] for entry in report['entries']], ['raised', 'cause', 'context'])
        self.assertEqual([entry['parent'] for entry in report['entries']], [None, 0, 0])
        self.assertTrue(report['chain_repeated'])
        self.assertFalse(report['chain_limited'])
        tail = primary
        for _ in range(release.MAX_DIAGNOSTIC_ENTRIES + 1):
            tail.__context__ = ValueError('synthetic-secret')
            tail = tail.__context__
        report = self.diagnostic(surfaced)
        self.assertEqual(len(report['entries']), release.MAX_DIAGNOSTIC_ENTRIES)
        self.assertTrue(report['chain_limited'])

    def test_unavailable_reporting_preserves_failure_exit_and_fixed_refusal_policy(self):
        class UnavailableContext(Exception):
            @property
            def __context__(self):
                raise RuntimeError('synthetic-secret')

        self.assertEqual(release.failure_diagnostic(UnavailableContext()), 'DIAGNOSTIC: unavailable')
        with mock.patch.object(release, 'MAX_DIAGNOSTIC_BYTES', 64):
            self.assertEqual(release.failure_diagnostic(ValueError('synthetic')), 'DIAGNOSTIC: unavailable')
        for error, message in [(ValueError('synthetic-secret'), 'release operation failed closed'),
                               (release.Refused('command or scanner gate failed'), 'command or scanner gate failed')]:
            stderr = io.StringIO()
            with mock.patch.object(release, 'main', side_effect=error), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exited:
                    release.run()
            self.assertEqual(exited.exception.code, 1)
            self.assertEqual(stderr.getvalue().splitlines()[0], 'REFUSED: ' + message)
            self.assertNotIn(message, stderr.getvalue().splitlines()[1])
            self.assertNotIn('synthetic-secret', stderr.getvalue())
        stderr = io.StringIO()
        with mock.patch.object(release, 'main', side_effect=ValueError('synthetic-secret')), \
             mock.patch.object(release, 'failure_diagnostic', side_effect=SystemExit(0)), \
             contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as exited:
            release.run()
        self.assertEqual(exited.exception.code, 1)
        self.assertEqual(stderr.getvalue(), 'REFUSED: release operation failed closed\n')
        with mock.patch.object(release, 'main'), mock.patch.object(release, 'failure_diagnostic') as diagnostic:
            release.run()
        diagnostic.assert_not_called()


class SubprocessTests(unittest.TestCase):
    def test_nonzero_timeout_stdout_and_stderr_limits_reap_owned_child(self):
        cases = [('import sys; sys.exit(2)', {}), ('import time; time.sleep(20)', {'seconds': 0.5}),
                 ('import os,time; os.write(1,b"x"*65536); time.sleep(20)', {'maximum': 10}),
                 ('import os,time; os.write(2,b"x"*70000); time.sleep(20)', {'errors': io.BytesIO()})]
        for source, kwargs in cases:
            with self.subTest(source=source):
                real_popen, children = release.subprocess.Popen, []

                def start(*args, **options):
                    child = real_popen(*args, **options)
                    children.append(child)
                    return child

                with mock.patch.object(release.subprocess, 'Popen', side_effect=start), self.assertRaises(release.Refused):
                    release.command([sys.executable, '-c', source], **kwargs)
                self.assertIsNotNone(children[0].poll())

    @unittest.skipUnless(sys.platform == 'linux', 'Linux process-group cleanup contract')
    def test_timeout_terminates_descendant_even_after_direct_child_exits(self):
        source = ('import os,signal,time\n'
                  'if os.fork() == 0:\n'
                  ' signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
                  ' print(os.getpid(), flush=True)\n'
                  ' time.sleep(30)\n')
        captured = io.BytesIO()
        with self.assertRaises(release.Refused):
            release.command([sys.executable, '-c', source], seconds=1, output=captured)
        pid = int(captured.getvalue().strip())
        status = Path(f'/proc/{pid}/stat')
        # A dead orphan can briefly remain a zombie until the host init reaps it; it is not running.
        for _ in range(50):
            try:
                state = status.read_text().split(') ', 1)[1].split()[0]
            except FileNotFoundError:
                break
            if state == 'Z':
                break
            release.time.sleep(0.02)
        else:
            self.fail('owned descendant still running after bounded group cleanup')

    def test_child_environment_does_not_inherit_api_or_deployment_secrets(self):
        names = ('GITHUB_TOKEN', 'ADMIN8_POLICY_READ_TOKEN', 'DEPLOY_KEY', 'KNOWN_HOSTS')
        with mock.patch.dict(os.environ, {name: 'fixture-secret' for name in names}):
            output = release.command([sys.executable, '-c', 'import os; print(any(k in os.environ for k in ' + repr(names) + '))'])
        self.assertEqual(output, b'False\n')


class WorkflowTests(unittest.TestCase):
    def test_manual_main_native_approval_and_step_isolated_tokens(self):
        source = (release.ROOT / release.PROMOTION).read_text()
        self.assertNotIn('workflow_run', source)
        self.assertRegex(source, r'on:\n  workflow_dispatch:\n')
        jobs = dict(re.findall(r'^  (\w+):\n(.*?)(?=^  \w+:\n|\Z)', source.split('jobs:\n', 1)[1], re.M | re.S))
        self.assertEqual(set(jobs), {'preflight', 'promote'})
        self.assertNotIn('environment:', jobs['preflight'])
        self.assertIn('environment: production', jobs['promote'])
        self.assertIn('needs: preflight', jobs['promote'])
        self.assertIn('EXPECTED_CANDIDATE: ${{ needs.preflight.outputs.candidate }}', jobs['promote'])
        self.assertIn('EXPECTED_POLICY: ${{ needs.preflight.outputs.policy }}', jobs['promote'])
        for job in jobs.values():
            self.assertIn("github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'", job)
            self.assertIn("github.repository == 'kira-manga/kira-admin'", job)
            self.assertIn('ref: ${{ github.sha }}', job)
            self.assertIn('persist-credentials: false', job)
            self.assertIn("if: always() && steps.scratch.outputs.path != ''", job)
            for step in job.split('\n      - name: ')[1:]:
                if 'ADMIN8_POLICY_READ_TOKEN:' in step:
                    self.assertIn('run: python3 scripts/ci/image_release.py policy', step)
                    self.assertNotIn('GITHUB_TOKEN:', step)
                    self.assertNotIn('DEPLOY_KEY:', step)
                if 'DEPLOY_KEY:' in step or 'KNOWN_HOSTS:' in step:
                    self.assertIn('run: python3 scripts/ci/image_release.py transfer', step)
            for command in re.findall(r'^        run: (.+)$', job, re.M):
                self.assertRegex(command, r'^python3 scripts/ci/image_release\.py (scratch|verify|policy|transfer|cleanup)$')
        self.assertEqual(re.findall(r'^  \w+: (read|write)$', source, re.M), ['read', 'read'])

    def test_one_producer_fresh_secretless_consumer_pins_and_short_immutable_retention(self):
        ci = (release.ROOT / release.CI).read_text()
        rehearsal = ci.split('\n  rehearsal:\n', 1)[1]
        self.assertIn('options: [no-deploy-rehearsal]', ci)
        self.assertIn("if: github.event_name != 'workflow_dispatch'", ci)
        self.assertEqual(ci.count('run: npm run verify'), 1)
        self.assertEqual(ci.count('run: npm audit --omit=dev --audit-level=high'), 2)
        self.assertEqual(ci.count('uses: docker/build-push-action@'), 1)
        self.assertIn('platforms: linux/amd64', ci)
        self.assertIn('BUILT_IMAGE_ID: ${{ steps.build.outputs.imageid }}', ci)
        self.assertIn('name: admin-image-${{ github.run_id }}-${{ github.run_attempt }}', ci)
        self.assertEqual(ci.count('retention-days: 3'), 2)
        self.assertEqual(ci.count('compression-level: 0'), 2)
        self.assertEqual(ci.count('overwrite: false'), 2)
        self.assertIn('if-no-files-found: error', ci)
        self.assertNotIn('secrets.', rehearsal)
        self.assertNotIn('environment:', rehearsal)
        self.assertNotIn('build-push-action', rehearsal)
        self.assertIn('CANDIDATE_ARTIFACT_ID: ${{ needs.container.outputs.artifact_id }}', rehearsal)
        self.assertIn('CANDIDATE_ZIP_SHA256: ${{ needs.container.outputs.zip_sha256 }}', rehearsal)
        self.assertIn('run: python3 scripts/ci/image_release.py rehearse', rehearsal)
        for source in (ci, (release.ROOT / release.PROMOTION).read_text()):
            for line in source.splitlines():
                if 'uses:' in line:
                    self.assertRegex(line, r'uses: [\w/-]+@[0-9a-f]{40}(?:\s+#.*)?$')
        self.assertIn('actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02', ci)
        self.assertEqual(release.GRYPE_SHA, '1d444c5e7360471815f7158f71935fcecc68a3c417d85c7344f770854300bba2')


if __name__ == '__main__':
    unittest.main()
