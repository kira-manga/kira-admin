"""Authored, UNEXECUTED stdlib correction tests; no controller/module/owner import.

Only whitelisted data helpers and exact finalization slices are evaluated if this
file is separately admitted. All paths and custody answers are synthetic and
run-owned; no command, checkout, JVM, Docker, source binder or main can execute.
These controls cannot establish actual process/container absence or hosted PASS.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


PACKET = Path(__file__).resolve().parents[1]
SOURCE = PACKET / 'ci/app29-gate-b.py'


def isolated_source():
    tree = ast.parse(SOURCE.read_text())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    gate = copy.deepcopy(next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Gate'))
    gate.body = [node for node in gate.body if node.name in ('fail', 'attempt', 'cleanup_outputs', 'output_absence')]
    constants = {'CLASS', 'DESCENDANTS', 'TEST_COUNTS', 'PROFILE_ID', 'CACHE_PATHS', 'GUARD_IDS'}
    helpers = ('require', 'safe', 'digest', 'unique', 'read_json', 'remove_owned', 'capture_reports', 'consumer')
    definitions = [node for node in tree.body if isinstance(node, ast.Assign)
                   and isinstance(node.targets[0], ast.Name) and node.targets[0].id in constants]
    definitions += [functions[name] for name in helpers] + [gate]
    final = next(node for node in functions['execute'].body if isinstance(node, ast.Try)).finalbody
    workers = next(node for node in final if isinstance(node, ast.If) and ast.unparse(node.test) == 'workers_gone').body

    def index(nodes, target):
        return next(i for i, node in enumerate(nodes) if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == target)

    def code(nodes):
        return compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes), type_ignores=[])), str(SOURCE), 'exec')

    capture = index(workers, "gate.result['capture_complete']")
    files = index(final, 'before_file_cleanup')
    stop = next(i for i in range(files, len(final)) if isinstance(final[i], ast.If) and ast.unparse(final[i].test) == 'gate.started')
    home = index(final, 'after_commands')
    absence = index(final, "gate.result['outputs_absent']")
    status = index(final, 'passed')
    return tuple(code(nodes) for nodes in (definitions, workers[capture:capture + 2], final[files:stop],
                                           final[home:absence + 1], final[status:status + 2]))


class FailedCaptureCleanupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='app29-capture-unit-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.ns = {name: globals()[name] for name in ('hashlib', 'json', 'os', 'Path', 'PurePosixPath',
                                                     're', 'shutil', 'unquote', 'urlsplit', 'ET')}
        self.ns.update(ADMIN=root / 'admin', BACKEND=root / 'backend')
        definitions, self.capture, self.files, self.home, self.status = isolated_source()
        exec(definitions, self.ns)
        self.gate = self.ns['Gate']()  # __init__/owner/command/drain are deliberately absent.
        self.gate.run = root / 'run'
        self.gate.reports = self.gate.run / 'reports'
        self.gate.java = root / 'never-executed-jdk'
        self.gate.cancelled = False
        self.gate.drain = lambda stage: True  # Synthetic custody answers, never runtime evidence.
        self.gate.result = {'status': 'FAIL', 'failures': [], 'commands': [], 'capture_complete': False,
                            'captured_file_hashes': {}, 'owned_output_cleanup': {}, 'consumer': {'status': 'NOT_EVALUATED'},
                            'outputs_absent': False, 'inputs_preserved': True, 'retained_inventory_complete': True,
                            'containers': 'NORMAL_ABSENT', 'elapsed_seconds': 0}
        self.profile = json.loads((PACKET / 'reference/profile03.json').read_text())
        self.ns.update(gate=self.gate, profile=self.profile, workers_gone=True, containers_gone=True,
                       final_children=True, final_containers=True)
        self.owned = [self.ns['BACKEND'] / p for p in self.ns['CACHE_PATHS']]
        self.owned += [self.gate.run / p for p in ('w01', 'project-cache', 'kotlin-cache', 'gradle', 'tmp', 'home')]
        for path in self.owned + [self.gate.reports]:
            path.mkdir(parents=True, exist_ok=True)
        build = self.gate.run / 'w01/backend-build'
        xml_root = build / 'test-results/test'
        xml_root.mkdir(parents=True)
        for name, count in self.ns['TEST_COUNTS'].items():
            failed = name == self.ns['CLASS']
            suite = ET.Element('testsuite', name=name, tests=str(count), failures=str(int(failed)), errors='0', skipped='0')
            for item in (item for item in self.profile['expected_tests'] if item['class'] == name):
                ET.SubElement(suite, 'testcase', classname=name, name=item['display_name'])
            if failed:
                ET.SubElement(suite[0], 'failure', message='synthetic failed-test fixture')
            ET.ElementTree(suite).write(xml_root / ('TEST-' + name + '.xml'), encoding='utf-8')
        self.raw = build / self.profile['report_directory']
        self.raw.mkdir(parents=True)
        for name in ('effective-classpath.txt', 'class-load-123.txt', *(item['file'] for item in self.profile['expected_witnesses'])):
            (self.raw / name).write_text('Synthetic capture-only bytes; no provenance claim.\n')

    def finish(self):
        for code in (self.files, self.home, self.status):
            exec(code, self.ns)

    def assert_held(self, guard):
        self.assertFalse(self.gate.result['capture_complete'])
        self.assertEqual(self.gate.result['consumer'], {'status': 'NOT_EVALUATED'})
        self.assertEqual(self.gate.result['failures'][-1]['guard'], guard)
        self.finish()
        self.assertTrue(all(path.is_dir() for path in self.owned))
        rows = self.gate.result['owned_output_cleanup']
        self.assertEqual(set(rows), {str(path) for path in self.owned})
        self.assertTrue(all(not row['cleanup_attempted'] and not row['cleanup_complete'] and row['absent'] is False
                            and row['cleanup_skipped_reason'] == 'CAPTURE_INCOMPLETE' for row in rows.values()))
        self.assertFalse(self.gate.result['outputs_absent'])
        self.assertEqual(self.gate.result['status'], 'FAIL')

    def test_retained_failed_xml_allows_cleanup_without_erasing_failures(self):
        historical = {'stage': 'after-immediate-stop-nonzero-child', 'type': 'RuntimeError'}
        self.gate.result['failures'].append(historical)
        exec(self.capture, self.ns)
        self.assertTrue(self.gate.result['capture_complete'])
        self.assertEqual(self.gate.result['consumer'], {'status': 'FAIL'})
        self.assertEqual(self.gate.result['failures'], [historical, {'stage': 'consumer', 'type': 'ValueError', 'guard': 'XML_SUITE_PASS'}])
        self.finish()
        self.assertTrue(self.gate.result['outputs_absent'])
        self.assertFalse(any(path.exists() for path in self.owned))
        rows = self.gate.result['owned_output_cleanup']
        self.assertEqual(set(rows), {str(path) for path in self.owned})
        self.assertTrue(all(row['cleanup_attempted'] and row['cleanup_complete'] and row['absent'] is True
                            and row['cleanup_skipped_reason'] is None for row in rows.values()))
        self.assertEqual(len(self.gate.result['captured_file_hashes']), 6)
        for relative, row in self.gate.result['captured_file_hashes'].items():
            data = (self.gate.reports / relative).read_bytes()
            self.assertEqual(row, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        self.assertEqual(self.gate.result['status'], 'FAIL')

    def test_missing_required_raw_file_holds_cleanup(self):
        (self.raw / self.profile['expected_witnesses'][0]['file']).unlink()
        exec(self.capture, self.ns)
        self.assert_held('CAPTURE_REQUIRED_INVENTORY')

    def test_failed_copy_digest_holds_cleanup(self):
        with patch.object(shutil, 'copyfile', side_effect=lambda source, target: Path(target).write_bytes(b'corrupt')):
            exec(self.capture, self.ns)
        self.assert_held('CAPTURE_COPY_DRIFT')

    def test_unrecognized_exception_text_is_not_retained(self):
        self.gate.fail('consumer', ValueError('arbitrary synthetic text must not appear in the receipt'))
        self.assertEqual(self.gate.result['failures'], [{'stage': 'consumer', 'type': 'ValueError'}])


if __name__ == '__main__':
    unittest.main()
