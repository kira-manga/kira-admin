"""Four authorized, finite PG03 cleanup groups; never import the controller.

Adapts the existing draft06 whitelisted-AST/exact-finalization-slice test approach.
Only listed functions and statements execute. No Gate init, owner, real command,
real drain, binding, diagnostics parser, main, Docker, JVM or CI can execute.
All destructive operations target a fresh TemporaryDirectory under this packet.
Synthetic diagnostic-success/custody inputs are not runtime qualification.
"""
import ast
import copy
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
SOURCE = ROOT / 'review/working/app-29-lease-dispatch-pg03-failure-cleanup-preparation-01/ci/app29-gate-b.py'
SOURCE_SHA = '30b9ab8a43b6b9277ac401569ddfa62ef44282929d6bb21badbf2f7abe5c1024'
REVIEW = ROOT / 'review/remediation/app-29-lease-dispatch-pg03-failure-cleanup-independent-review-01.md'
REVIEW_SHA = '1907703d923d440311b720137016d420702ecfa861f87009cd53b9f2283bcbb1'
BASIS = ROOT / 'review/working/app-29-gate-b-hosted-draft-06/tests/test_failed_capture_cleanup.py'
BASIS_SHA = '0437ff7cf1327b890509b7934d76b7b3e05e532cfd1f70624020c5355de41689'
DETAILS, FIXTURES, EXTRACTION = [], [], {}
PG, RYUK, UNKNOWN = 'a' * 64, 'b' * 64, 'f' * 64
SESSION = '11111111-1111-1111-1111-111111111111'


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def save_new(name, value):
    path = PACKET / name
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as output:
        output.write(json.dumps(value, indent=2) + '\n')


def isolated_source():
    raw = SOURCE.read_bytes()
    if digest_bytes(raw) != SOURCE_SHA:
        raise ValueError('Candidate pin mismatch: refuse any execution')
    source = raw.decode()
    tree = ast.parse(source, filename=str(SOURCE))
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    gate = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Gate'))
    methods = ('fail', 'attempt', 'cleanup_outputs', 'output_absence', 'census', 'containers')
    gate.body = [n for n in gate.body if isinstance(n, ast.FunctionDef) and n.name in methods]
    if {n.name for n in gate.body} != set(methods):
        raise ValueError('Finite Gate method extraction mismatch')
    constants = {'CREATOR_CLASS', 'METHODS', 'TEST_COUNTS', 'EXPECTED_TESTS', 'IMAGES', 'CACHE_PATHS', 'GUARD_IDS'}
    definitions = [n for n in tree.body if isinstance(n, ast.Assign)
                   and isinstance(n.targets[0], ast.Name) and n.targets[0].id in constants]
    if {n.targets[0].id for n in definitions} != constants:
        raise ValueError('Finite constant extraction mismatch')
    helpers = ('require', 'safe', 'digest', 'unique', 'save', 'remove_owned',
               'capture_reports', 'required_capture_inventory')
    definitions += [functions[name] for name in helpers] + [gate]
    final = next(n for n in functions['execute'].body if isinstance(n, ast.Try)).finalbody
    workers = next(n for n in final if isinstance(n, ast.If) and ast.unparse(n.test) == 'workers_gone').body

    def index(nodes, target):
        return next(i for i, n in enumerate(nodes) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == target)

    capture = index(workers, "gate.result['capture_complete']")
    files = index(final, 'before_file_cleanup')
    stop = next(i for i in range(files, len(final)) if isinstance(final[i], ast.If)
                and ast.unparse(final[i].test) == 'gate.started')
    ending = index(final, 'final_children')
    absence = index(final, "gate.result['outputs_absent']")
    status = index(final, 'passed')
    groups = {'definitions': definitions, 'capture': workers[capture:capture + 2],
              'files': final[files:stop], 'ending': final[ending:absence + 1],
              'status': final[status:status + 2]}
    for name, node in [(n.name, n) for n in gate.body] + [(name, functions[name]) for name in helpers]:
        EXTRACTION[name] = {'start_line': node.lineno, 'end_line': node.end_lineno,
                            'source_segment_sha256': digest_bytes(ast.get_source_segment(source, node).encode())}
    EXTRACTION['constants'] = sorted(constants)
    EXTRACTION['statement_slices'] = {name: [[n.lineno, n.end_lineno] for n in nodes]
                                      for name, nodes in groups.items() if name != 'definitions'}
    return {name: compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes), type_ignores=[])),
                          str(SOURCE), 'exec') for name, nodes in groups.items()}


class SyntheticClock:
    def __init__(self):
        self.tick = 0

    def monotonic(self):
        self.tick += 100
        return self.tick

    def time(self):
        return 1234567890

    def sleep(self, seconds):
        raise AssertionError('Synthetic cases must never sleep or poll repeatedly')


def events(complete=True):
    rows = []
    for cid, image in ((PG, 'postgres:17.6-alpine'), (RYUK, 'testcontainers/ryuk:0.12.0')):
        labels = {'image': image, 'org.testcontainers': 'true', 'org.testcontainers.version': '1.21.4',
                  'org.testcontainers.sessionId': SESSION}
        if cid == RYUK:
            labels['name'] = 'testcontainers-ryuk-' + SESSION
        rows.append({'Action': 'create', 'Actor': {'ID': cid, 'Attributes': labels}})
    if not complete:
        return rows[:1]
    return rows + [dict(row, Action='destroy') for row in rows]


class Fixture:
    def __init__(self, root, code):
        self.root, self.code = root, code
        self.ns = {name: globals()[name] for name in ('hashlib', 'json', 'os', 'Path', 'PurePosixPath',
                                                     're', 'shutil', 'stat', 'ET')}
        self.ns.update(__name__='pg03_synthetic_isolated', time=SyntheticClock(), BACKEND=root / 'backend')
        exec(code['definitions'], self.ns)
        self.gate = self.ns['Gate']()  # The real constructor/owner/command/drain are absent.
        self.gate.run, self.gate.reports = root / 'run', root / 'run/reports'
        self.gate.java = root / 'never-executed-jdk'
        self.gate.cancelled = False
        self.gate.clean_daemon, self.gate.events_since = True, 1234567890
        self.gate.result = {
            'status': 'FAIL', 'failures': [], 'commands': [], 'containers': 'UNKNOWN',
            'container_topology_complete': False, 'capture_complete': False,
            'required_capture_complete': False, 'capture_roots': {}, 'captured_file_hashes': {},
            'owned_output_cleanup': {}, 'diagnostics': {'status': 'NOT_EVALUATED'},
            'outputs_absent': False, 'inputs_preserved': True, 'retained_inventory_complete': True,
            'elapsed_seconds': 0,
        }
        self.profile = {'report_directory': 'reports/synthetic-context'}
        self.ns.update(gate=self.gate, profile=self.profile, workers_gone=True, containers_gone=False)
        self.owned = [self.ns['BACKEND'] / p for p in self.ns['CACHE_PATHS']]
        self.owned += [self.gate.run / p for p in ('w01', 'project-cache', 'kotlin-cache', 'gradle', 'tmp', 'home')]
        for path in self.owned + [self.gate.reports]:
            path.mkdir(parents=True, exist_ok=True)
        self.build = self.gate.run / 'w01/backend-build'
        self.raw = self.build / self.profile['report_directory']
        self.journal, self.normal_ids, self.after_ids = [], [], []
        self.after_error = None
        self.drains, self.diagnostics_calls, self.flag_probes = [], [], {}
        self.gate.command = self.command
        self.gate.drain = lambda stage: (self.drains.append(stage), True)[1]
        self.ns['diagnostics'] = self.diagnostics_boundary

    def command(self, name, argv, **kwargs):
        row = {'name': name, 'argv': argv, 'synthetic': True, 'actual_exit': 0, 'outcome': 'NORMAL'}
        self.gate.result['commands'].append(row)
        if name in ('containers-before', 'containers-final'):
            return b''
        if name.startswith('containers-normal-'):
            return ''.join(cid + '\n' for cid in self.normal_ids).encode()
        if name == 'containers-after-cleanup':
            if self.after_error:
                row.update(actual_exit=1, outcome='UNKNOWN')
                raise self.after_error
            return ''.join(cid + '\n' for cid in self.after_ids).encode()
        if name == 'container-events':
            return ''.join(json.dumps(event) + '\n' for event in self.journal).encode()
        if name.startswith('image-'):
            image = argv[-1]
            if image not in self.ns['IMAGES']:
                raise AssertionError('Unexpected image request')
            return json.dumps({'id': 'sha256:' + 'c' * 64, 'tags': [image],
                               'digests': [image.split(':')[0] + '@sha256:' + 'd' * 64]}).encode()
        raise AssertionError('Forbidden synthetic command, including every removal or real process: ' + name)

    def diagnostics_boundary(self, reports, profile, java):
        self.diagnostics_calls.append('SYNTHETIC_SUCCESS_BOUNDARY_ONLY')
        return {'test_status': 'PASS', 'fixed_scalar_capture': 'NOT_APPLICABLE', 'synthetic_boundary': True}

    def put(self, relative, data):
        path = self.build / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def complete_inventory(self):
        for name, count in self.ns['TEST_COUNTS'].items():
            suite = ET.Element('testsuite', name=name, tests=str(count), failures='0', errors='0', skipped='0')
            for item in self.ns['EXPECTED_TESTS']:
                ET.SubElement(suite, 'testcase', classname=item['class'], name=item['display_name'])
            self.put('test-results/test/TEST-' + name + '.xml', ET.tostring(suite))
        self.put(self.profile['report_directory'] + '/effective-classpath.txt',
                 b'{"synthetic_inventory_only": true, "not_real_classpath_evidence": true}\n')
        self.put(self.profile['report_directory'] + '/class-load-123.txt', b'synthetic inventory bytes\n')

    def custody(self):
        if self.gate.census('containers-before', cleaning=False) != set():
            raise AssertionError('Synthetic starting census must be empty')
        self.ns['containers_gone'] = self.gate.attempt('containers', self.gate.containers)
        return self.ns['containers_gone']

    def capture(self):
        exec(self.code['capture'], self.ns)

    def finish(self):
        for part in ('files', 'ending', 'status'):
            exec(self.code[part], self.ns)

    def copies_match(self, test):
        for relative, row in self.gate.result['captured_file_hashes'].items():
            if row['sha256'] is not None:
                data = (self.gate.reports / relative).read_bytes()
                test.assertEqual(row, {'bytes': len(data), 'sha256': digest_bytes(data)})

    def assert_disposed(self, test):
        test.assertEqual(set(self.gate.result['owned_output_cleanup']), {str(p) for p in self.owned})
        test.assertTrue(self.gate.result['outputs_absent'])
        test.assertTrue(all(not p.exists() for p in self.owned))
        test.assertTrue((self.gate.reports / 'owned-containers.json').is_file())
        self.copies_match(test)  # Retained evidence must survive the actual synthetic owned-path deletion.
        test.assertTrue(all(r['cleanup_attempted'] and r['cleanup_complete'] and r['absent']
                            and r['cleanup_skipped_reason'] is None
                            for r in self.gate.result['owned_output_cleanup'].values()))

    def assert_held(self, test, reason):
        test.assertEqual(set(self.gate.result['owned_output_cleanup']), {str(p) for p in self.owned})
        test.assertFalse(self.gate.result['outputs_absent'])
        test.assertTrue(all(p.is_dir() for p in self.owned))
        test.assertTrue(all(not r['cleanup_attempted'] and not r['cleanup_complete'] and r['absent'] is False
                            and r['cleanup_skipped_reason'] == reason
                            for r in self.gate.result['owned_output_cleanup'].values()))
        test.assertEqual(self.gate.result['status'], 'FAIL')

    def snapshot(self, case, assertions_completed):
        row = {'case': case, 'assertions_completed': assertions_completed,
               'result': copy.deepcopy(self.gate.result), 'synthetic_drains': list(self.drains),
               'diagnostics_boundary_calls': list(self.diagnostics_calls), 'new_pass_flag_probes': self.flag_probes}
        return json.loads(json.dumps(row).replace(str(self.root), '<test-created-fixture>'))


class CleanupSyntheticGroups(unittest.TestCase):
    @contextmanager
    def fixture(self, case):
        temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=PACKET)
        root = Path(temporary.name)
        receipt = {'path': str(root), 'removed': False}
        FIXTURES.append(receipt)
        fixture, completed = None, False
        try:
            fixture = Fixture(root, CODE)
            yield fixture
            completed = True
        finally:
            try:
                if fixture is not None:
                    DETAILS.append(fixture.snapshot(case, completed))
            finally:
                temporary.cleanup()  # Only the exact TemporaryDirectory created above.
                receipt['removed'] = not root.exists()
                if not receipt['removed']:
                    raise AssertionError('Test-created temporary fixture survived cleanup')

    def test_01_known_empty_disposal_still_fails(self):
        with self.fixture('known_empty_both_roots_absent') as f:
            historical = {'stage': 'after-immediate-stop-nonzero-child', 'type': 'RuntimeError'}
            f.gate.result['failures'].append(historical)
            self.assertIs(f.custody(), True)
            self.assertFalse(f.gate.result['container_topology_complete'])
            self.assertEqual(json.loads((f.gate.reports / 'owned-containers.json').read_text()),
                             {'created': {}, 'destroyed': [], 'remaining': []})
            f.capture()
            self.assertEqual(f.gate.result['capture_roots'], {'test-results': 'ABSENT', 'reports': 'ABSENT'})
            self.assertTrue(f.gate.result['capture_complete'])
            self.assertFalse(f.gate.result['required_capture_complete'])
            self.assertEqual(f.diagnostics_calls, [])
            self.assertEqual(f.gate.result['failures'], [
                historical,
                {'stage': 'container-required-topology', 'type': 'ValueError', 'guard': 'CONTAINER_REQUIRED_TOPOLOGY'},
                {'stage': 'required-capture-inventory', 'type': 'ValueError', 'guard': 'CAPTURE_ROOT'},
            ])
            f.finish()
            f.assert_disposed(self)
            self.assertEqual(f.gate.result['status'], 'FAIL')
            self.assertFalse(any(r['name'].startswith('image-') or 'remove' in r['name']
                                 for r in f.gate.result['commands']))
            self.assertEqual([r['name'] for r in f.gate.result['commands']],
                             ['containers-before', 'containers-normal-0', 'container-events',
                              'containers-after-cleanup', 'containers-final'])

    def test_02_available_capture_vs_required_success(self):
        for case in ('missing_first_root_existing_reports', 'present_roots_missing_required_xml'):
            with self.subTest(case=case), self.fixture(case) as f:
                f.journal = events()
                self.assertIs(f.custody(), True)
                if case == 'missing_first_root_existing_reports':
                    expected = {}
                    for suffix in ('.xml', '.txt', '.json', '.log'):
                        relative = 'reports/available/evidence' + suffix
                        expected[relative] = ('retained synthetic ' + suffix + '\n').encode()
                        f.put(relative, expected[relative])
                    f.put('reports/available/not-in-scope.html', b'not a required captured format\n')
                    roots, guard = {'test-results': 'ABSENT', 'reports': 'CAPTURED'}, 'CAPTURE_ROOT'
                else:
                    f.complete_inventory()
                    next((f.build / 'test-results/test').glob('TEST-*.xml')).unlink()
                    roots, guard = {'test-results': 'CAPTURED', 'reports': 'CAPTURED'}, 'CAPTURE_REQUIRED_INVENTORY'
                    expected = {p.relative_to(f.build).as_posix(): p.read_bytes() for p in f.build.rglob('*') if p.is_file()}
                f.capture()
                self.assertEqual(f.gate.result['capture_roots'], roots)
                self.assertTrue(f.gate.result['capture_complete'])
                self.assertFalse(f.gate.result['required_capture_complete'])
                self.assertEqual(f.diagnostics_calls, [])
                self.assertEqual(f.gate.result['failures'], [
                    {'stage': 'required-capture-inventory', 'type': 'ValueError', 'guard': guard}])
                self.assertEqual(set(f.gate.result['captured_file_hashes']), set(expected))
                for relative, data in expected.items():
                    self.assertEqual((f.gate.reports / relative).read_bytes(), data)
                f.copies_match(self)
                f.finish()
                f.assert_disposed(self)
                self.assertEqual(f.gate.result['status'], 'FAIL')

    def test_03_fail_closed_negative_boundaries(self):
        custody_cases = ('ignored_raw_event', 'unknown_current_id', 'orphan_destroy',
                         'partial_topology', 'unknown_image', 'fresh_census_nonempty', 'fresh_census_error')
        for case in custody_cases:
            with self.subTest(case=case), self.fixture(case) as f:
                f.complete_inventory()
                if case == 'ignored_raw_event':
                    f.journal = [{'Action': 'die'}]
                elif case == 'unknown_current_id':
                    f.normal_ids = [UNKNOWN]
                elif case == 'orphan_destroy':
                    f.journal = [dict(events(False)[0], Action='destroy')]
                elif case == 'partial_topology':
                    f.journal = events(False)
                elif case == 'unknown_image':
                    f.journal = events(False)
                    f.journal[0]['Actor']['Attributes']['image'] = 'unknown/image:unowned'
                elif case == 'fresh_census_nonempty':
                    f.after_ids = [UNKNOWN]
                else:
                    f.after_error = RuntimeError('synthetic Docker API failure; no real Docker call')
                self.assertIsNone(f.custody())
                self.assertFalse(f.gate.result['container_topology_complete'])
                self.assertEqual(f.gate.result['containers'], 'UNKNOWN')
                self.assertEqual(f.gate.result['failures'][-1]['stage'], 'containers')
                f.capture()
                self.assertTrue(f.gate.result['capture_complete'])
                self.assertTrue(f.gate.result['required_capture_complete'])
                f.finish()
                f.assert_held(self, 'CONTAINER_CLEANUP_NOT_ABSENT')
                self.assertFalse(any('remove' in r['name'] for r in f.gate.result['commands']))

        capture_cases = ('root_permission_error', 'root_regular_file', 'nested_link', 'nested_fifo',
                         'walk_error', 'enumerated_entry_disappears', 'copy_drift', 'oversized_file')
        for case in capture_cases:
            with self.subTest(case=case), self.fixture(case) as f:
                f.journal = events()
                self.assertIs(f.custody(), True)
                f.complete_inventory()
                target = f.build / 'test-results'
                if case == 'root_permission_error':
                    original_lstat, original_link = Path.lstat, Path.is_symlink
                    def denied(path):
                        if path == target:
                            raise PermissionError('synthetic direct root lstat denied')
                        return original_lstat(path)
                    def known_fixture_not_link(path):
                        return False if path == target else original_link(path)
                    with patch.object(Path, 'is_symlink', new=known_fixture_not_link), patch.object(Path, 'lstat', new=denied):
                        f.capture()
                    expected_type, guard = 'PermissionError', None
                    self.assertEqual(f.gate.result['capture_roots']['test-results'], 'UNKNOWN')
                elif case == 'root_regular_file':
                    shutil.rmtree(target)
                    target.write_bytes(b'not a directory')
                    f.capture()
                    expected_type, guard = 'ValueError', 'CAPTURE_ROOT'
                elif case == 'nested_link':
                    (f.raw / 'link.log').symlink_to(f.raw / 'class-load-123.txt')
                    f.capture()
                    expected_type, guard = 'ValueError', 'CAPTURE_LINK'
                elif case == 'nested_fifo':
                    os.mkfifo(f.raw / 'fifo.log', 0o600)
                    f.capture()
                    expected_type, guard = 'ValueError', 'CAPTURE_TYPE'
                elif case == 'walk_error':
                    def denied_walk(source, **kwargs):
                        kwargs['onerror'](PermissionError('synthetic scandir failure'))
                        return iter(())
                    with patch.object(os, 'walk', new=denied_walk):
                        f.capture()
                    expected_type, guard = 'PermissionError', None
                elif case == 'enumerated_entry_disappears':
                    target = f.put(f.profile['report_directory'] + '/zz-disappeared.log', b'listed before disappearance\n')
                    original_lstat = Path.lstat
                    def vanished(path):
                        if path == target:
                            raise FileNotFoundError('synthetic enumerated entry disappeared')
                        return original_lstat(path)
                    with patch.object(Path, 'lstat', new=vanished):
                        f.capture()
                    expected_type, guard = 'FileNotFoundError', None
                    self.assertEqual(f.gate.result['capture_roots']['reports'], 'UNKNOWN')
                    self.assertTrue(any(r['sha256'] is not None for r in f.gate.result['captured_file_hashes'].values()))
                elif case == 'copy_drift':
                    with patch.object(shutil, 'copyfile', side_effect=lambda source, destination: Path(destination).write_bytes(b'corrupt')):
                        f.capture()
                    expected_type, guard = 'ValueError', 'CAPTURE_COPY_DRIFT'
                else:
                    with (f.raw / 'oversized.log').open('wb') as sparse:
                        sparse.truncate(64 * 1024**2 + 1)
                    f.capture()
                    expected_type, guard = 'ValueError', 'BOUNDED_REGULAR_FILE'
                self.assertFalse(f.gate.result['capture_complete'])
                self.assertFalse(f.gate.result['required_capture_complete'])
                self.assertEqual(f.diagnostics_calls, [])
                failure = f.gate.result['failures'][-1]
                self.assertEqual(failure['stage'], 'capture-reports')
                self.assertEqual(failure['type'], expected_type)
                self.assertEqual(failure.get('guard'), guard)
                f.copies_match(self)
                f.finish()
                f.assert_held(self, 'CAPTURE_INCOMPLETE')

    def test_04_complete_inventory_and_new_pass_flags(self):
        with self.fixture('complete_inventory_valid_topology_predicate_only') as f:
            f.journal = events()
            f.complete_inventory()
            self.assertIs(f.custody(), True)
            self.assertTrue(f.gate.result['container_topology_complete'])
            f.capture()
            self.assertTrue(f.gate.result['capture_complete'])
            self.assertTrue(f.gate.result['required_capture_complete'])
            self.assertEqual(f.gate.result['capture_roots'], {'test-results': 'CAPTURED', 'reports': 'CAPTURED'})
            self.assertEqual(f.diagnostics_calls, ['SYNTHETIC_SUCCESS_BOUNDARY_ONLY'])
            self.assertEqual(len(f.gate.result['captured_file_hashes']), 3)
            f.copies_match(self)
            f.finish()
            f.assert_disposed(self)
            self.assertEqual(f.gate.result['failures'], [])
            self.assertEqual(f.gate.result['status'], 'PASS')  # Synthetic predicate outcome, not PG/diagnostic evidence.
            for flag in ('capture_complete', 'required_capture_complete', 'container_topology_complete'):
                with self.subTest(required_flag=flag):
                    f.gate.result[flag] = False
                    exec(f.code['status'], f.ns)
                    self.assertEqual(f.gate.result['status'], 'FAIL')
                    f.flag_probes[flag] = f.gate.result['status']
                    f.gate.result[flag] = True
            exec(f.code['status'], f.ns)
            self.assertEqual(f.gate.result['status'], 'PASS')
            self.assertEqual([r['name'] for r in f.gate.result['commands'] if r['name'].startswith('image-')],
                             ['image-0', 'image-1'])
            self.assertFalse(any('remove' in r['name'] for r in f.gate.result['commands']))


def main():
    global CODE
    for path, expected in ((SOURCE, SOURCE_SHA), (REVIEW, REVIEW_SHA), (BASIS, BASIS_SHA)):
        if digest_bytes(path.read_bytes()) != expected:
            raise ValueError('Immutable input pin mismatch before tests')
    CODE = isolated_source()
    save_new('inputs.json', {
        'candidate': {'path': str(SOURCE.relative_to(ROOT)), 'sha256': SOURCE_SHA},
        'independent_review': {'path': str(REVIEW.relative_to(ROOT)), 'sha256': REVIEW_SHA},
        'existing_harness_basis': {'path': str(BASIS.relative_to(ROOT)), 'sha256': BASIS_SHA},
        'test_source_sha256': digest_bytes(Path(__file__).read_bytes()),
        'exercised_candidate_segments': EXTRACTION,
        'diagnostics': 'explicit synthetic success boundary; real parser/classpath/JDK/PG tests excluded',
        'custody': 'stub command bytes and always-true synthetic drains; no ownership proof',
        'destructive_scope': 'only exact TemporaryDirectory fixtures created under this packet',
    })
    started = time.monotonic()
    with os.fdopen(os.open(PACKET / 'tests.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(CleanupSyntheticGroups))
    candidate_preserved = digest_bytes(SOURCE.read_bytes()) == SOURCE_SHA
    fixtures_absent = all(row['removed'] and not Path(row['path']).exists() for row in FIXTURES)
    passed = result.wasSuccessful() and candidate_preserved and fixtures_absent and result.testsRun == 4
    record = {
        'status': 'PASS' if passed else 'FAIL', 'scope': 'FOUR_SYNTHETIC_CLEANUP_GROUPS_ONLY_NOT_PG_OR_OWNERSHIP',
        'python': sys.version, 'pid': os.getpid(), 'argv': sys.argv,
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': len(result.skipped), 'failure_ids': [str(test) for test, _ in result.failures],
        'error_ids': [str(test) for test, _ in result.errors], 'elapsed_seconds': time.monotonic() - started,
        'candidate_sha256_after': digest_bytes(SOURCE.read_bytes()), 'candidate_preserved': candidate_preserved,
        'test_source_sha256': digest_bytes(Path(__file__).read_bytes()),
        'tests_log_sha256': digest_bytes((PACKET / 'tests.log').read_bytes()),
        'disposable_fixtures_absent': fixtures_absent, 'fixtures': FIXTURES,
        'case_count': len(DETAILS), 'cases': DETAILS,
        'real_docker_gradle_ci_commands': 0, 'owner_or_controller_module_imported': False,
        'spawned_children': 0, 'live_product_admin_edits': 0,
        'limitations': 'Actual selected function/slice control flow over synthetic inputs and private file fixtures only. '
                       'Diagnostic success and custody/drains are stubs. No full execute/main, real Docker, JVM, CI, '
                       'resource ownership, PG test result, source binding or public validation is established.',
    }
    save_new('result.json', record)
    print(json.dumps({key: record[key] for key in ('status', 'tests_run', 'failures', 'errors', 'skipped',
                                                   'case_count', 'disposable_fixtures_absent', 'candidate_preserved')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
