#!/usr/bin/env python3
"""Collect Timer-A02 separately from unchanged accepted20 recipes. No execution or acceptance is invented."""
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'kira-backend'
EVIDENCE = ROOT / 'review/working' / sys.argv[1]
OUTPUT = EVIDENCE / 'primary-summary.json'
assert not OUTPUT.exists(), 'Do not overwrite a collected run.'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def absent(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def read_xml(folder):
    totals, cases, suites, failures, lines = Counter(), Counter(), {}, [], {}
    for path in sorted((folder / 'reports/test-results/test').glob('TEST-*.xml')):
        node = ET.parse(path).getroot()
        name = node.attrib['name']
        items = node.findall('testcase')
        assert name not in suites and len(items) == int(node.attrib['tests'])
        suites[name] = len(items)
        for key in ('tests', 'failures', 'errors', 'skipped'):
            totals[key] += int(node.attrib[key])
        for item in items:
            cases[(item.attrib['classname'], item.attrib['name'])] += 1
            for tag in ('failure', 'error', 'skipped'):
                failure = item.find(tag)
                if failure is not None:
                    failures.append(dict(suite=name, test=item.attrib['name'], kind=tag,
                                         detail=failure.attrib, report=str(path.relative_to(folder))))
        lines[name] = [line for part in node.findall('system-out') + node.findall('system-err')
                       for line in (part.text or '').splitlines() if line]
    return totals, cases, suites, failures, lines


def normalize(line):
    # Same exact recipe, ordered tuples and platform/virtual kinds; only fresh process/Thread IDs vary.
    line = re.sub(r'\b(?:pid|thread_id)=[1-9]\d*', lambda m: m[0].split('=')[0] + '=<owned>', line)
    line = re.sub(r'nonce=[0-9a-f-]{36}', 'nonce=<synthetic>', line)
    line = re.sub(r'thread_ids=\[([\d,]*)\]', lambda m: 'thread_ids=[' + ','.join('<owned>' for x in m[1].split(',') if x) + ']', line)
    return re.sub(r'threads=\[((?:[1-9]\d*:(?:platform|virtual)(?:,[1-9]\d*:(?:platform|virtual))*)?)\]',
                  lambda m: 'threads=[' + re.sub(r'[1-9]\d*:', '<owned>:', m[1]) + ']', line)


CHILD_PREFIXES = ('ENDPOINT_PROBE ', 'ENDPOINT_PROBE_CLEANUP ', 'JDBC_PROFILE_PROBE ',
                  'JDBC_PROBE_CLEANUP ', 'BOOTSTRAP_CLEANUP ', 'BOOTSTRAP_UID_CLEANUP ', 'PG_PROBE_CLEANUP ')
SCOPE_PREFIXES = ('FACTORY_SCOPE_EXIT ', 'TRANSPORT_SCOPE_EXIT ', 'OWNED_CALLER_SCOPE_EXIT ',
                  'RETAINED_ACTOR_SCOPE_EXIT ', 'OWNED_WORKER_SCOPE_EXIT ', 'PG_PEER_CLEANUP ',
                  'PG_OPENING_SCOPE_CLEANUP ', 'PG_ROTATION_ACTORS_CLEANUP ', 'PG_REQUIRE_OBSERVER_CLEANUP ')


def recipes(lines, selected, prefixes):
    return Counter((name, normalize(line)) for name in selected for line in lines.get(name, []) if line.startswith(prefixes))


result_path = EVIDENCE / 'result.json'
result = json.loads(result_path.read_text())
assert result.get('finished_at'), 'Wait for the runner to collect evidence and finish cleanup.'
manifest_path = ROOT / result['source_manifest']
assert sha(manifest_path) == result['source_manifest_sha256']
manifest = json.loads(manifest_path.read_text())
for section in ('snapshots', 'validation_tooling', 'approved_inputs'):
    for path, digest in manifest[section].items():
        assert sha(ROOT / path) == digest, path
for path, digest in manifest['source_hashes'].items():
    assert sha(REPO / path) == digest, path
for item in result['retained_reports'] + result.get('retained_bytecode', []) + result.get('retained_test_bytecode', []):
    assert sha(EVIDENCE / item['path']) == item['sha256'], item['path']
assert sha(EVIDENCE / 'input.patch') == manifest['complete_diff_sha256'] == result['diff_sha256']
assert hashlib.sha256(subprocess.check_output(['git', 'diff', '--binary'], cwd=REPO)).hexdigest() == result['diff_sha256']
for repo, expected in manifest['repositories'].items():
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT / repo, text=True)
    assert dict(head=git('rev-parse', 'HEAD').strip(), branch=git('branch', '--show-current').strip(),
                status=git('status', '--porcelain=v1')) == expected, repo
    assert not git('diff', '--cached', '--name-only'), repo
    assert git('rev-parse', 'remediation/production-readiness-2026-09-04').strip() == manifest['integration_refs'][repo], repo

prior = ROOT / 'review/working/app-29-w03-d1-c6-wip-cycle-20'
assert sha(prior / 'result.json') == 'a8b5690851b0fc66cd4febbda59e0a840e6c7302d051b525bb45c4b114f02000'
prior_result = json.loads((prior / 'result.json').read_text())
for item in prior_result['retained_reports'] + prior_result['retained_bytecode'] + prior_result['retained_test_bytecode']:
    assert sha(prior / item['path']) == item['sha256'], item['path']
prior_totals, prior_ids, prior_suites, prior_failures, prior_lines = read_xml(prior)
assert prior_totals == Counter(tests=2705, failures=0, errors=0, skipped=0) and len(prior_suites) == 87 and not prior_failures
totals, ids, suites, failures, lines = read_xml(EVIDENCE)
inventory = json.loads((ROOT / manifest['test_inventory']).read_text())
assert sha(ROOT / manifest['test_inventory']) == manifest['test_inventory_sha256']
timer_suites = set(inventory['suites'])
new_ids = ids - prior_ids
discovered_methods = []
inventory_ok = True
for name, suite in inventory['suites'].items():
    assert sha(REPO / suite['source']) == suite['source_sha256']
    for method in suite['methods']:
        actual = Counter({label: count for (owner, label), count in new_ids.items()
                          if owner == name and label.startswith(method['method'] + '(')})
        if method['kind'] == 'Test':
            expected = Counter({method['method'] + '()': 1})
        else:
            expected = Counter({method['method'] + '(PgTimerProbeCase) [' + str(i) + '] mode=' + mode: 1
                                for i, mode in enumerate(method['arguments'], 1)})
        discovered_methods.append(dict(suite=name, method=method['method'], expected=dict(expected), actual=dict(actual)))
        inventory_ok = inventory_ok and actual == expected

# Collect only the separate timer launcher; do not broaden historical PG opening/rotation receipts.
timer_groups, timer_children, timer_errors = {}, [], []
for name in sorted(timer_suites):
    pending = []
    for line in lines.get(name, []):
        if not line.startswith('PG_TIMER_CHILD_CLEANUP '):
            pending.append(line)
            continue
        match = re.fullmatch(r'PG_TIMER_CHILD_CLEANUP mode=([A-Z_]+) nonce=([0-9a-f-]{36}) pid=([1-9]\d*) exit_observed=true alive=false forced=false', line)
        if not match:
            timer_errors.append('Invalid child cleanup: ' + line)
            pending = []
            continue
        mode, nonce, pid = match[1], match[2], int(match[3])
        if mode in timer_groups or str(uuid.UUID(nonce)) != nonce:
            timer_errors.append('Duplicate mode or invalid nonce: ' + mode)
        timer_groups[mode] = dict(suite=name, nonce=nonce, lines=pending, child_receipt=line, pid=pid)
        timer_children.append(dict(suite=name, mode=mode, nonce=nonce, pid=pid, absent=absent(pid), receipt=line))
        pending = []
    if pending:
        timer_errors.append('Unattributed trailing timer output in ' + name)

expected_modes = inventory['enum_modes']
positive = set(m for m in expected_modes if m.startswith(('META_', 'MODEL_', 'REAL_')))
scope_receipts = []
for mode, group in timer_groups.items():
    content, nonce = group['lines'], group['nonce']
    tagged = [line for line in content if line.startswith('PG_TIMER_')]
    verified = [line for line in tagged if line.startswith('PG_TIMER_VERIFIED ')]
    cleanup = f'PG_TIMER_SCENARIO_CLEANUP mode={mode} all_terminated=true'
    if mode in positive:
        wanted = f'PG_TIMER_VERIFIED mode={mode} nonce={nonce}'
        if content[-2:] != [cleanup, wanted] or verified != [wanted] or content.count(cleanup) != 1:
            timer_errors.append('Positive cleanup/nonce/order mismatch: ' + mode)
    else:
        expected = {
            'ASSERTION_FAILURE': [], 'MISSING_RECEIPT': [],
            'WRONG_RECEIPT': [f'PG_TIMER_VERIFIED mode={mode} nonce=wrong'],
            'DUPLICATE_RECEIPT': [f'PG_TIMER_VERIFIED mode={mode} nonce={nonce}'] * 2,
        }.get(mode)
        if expected is None or verified != expected or cleanup in content:
            timer_errors.append('Negative launcher witness mismatch: ' + mode)
        if mode == 'ASSERTION_FAILURE' and content.count(f'PG_TIMER_EXPECTED_ASSERTION mode={mode} nonce={nonce}') != 1:
            timer_errors.append('Missing deliberate assertion witness')
    controllers = [line for line in tagged if line.startswith('PG_TIMER_CONTROLLER_CLEANUP ')]
    fixtures = [line for line in tagged if line.startswith('PG_TIMER_FIXTURE_CLEANUP ')]
    foreign = [line for line in tagged if line.startswith('PG_TIMER_FOREIGN_CLEANUP ')]
    expected_controller = 1 if mode == 'META_EXACT' or mode.startswith(('MODEL_', 'REAL_')) else 0
    expected_fixture = 1 if mode.startswith(('META_', 'MODEL_')) else 0
    expected_foreign = 1 if mode in ('REAL_HELD_TASK', 'REAL_FOREIGN_REFERENCE', 'REAL_NO_CAPTURE') else 0
    if len(controllers) != expected_controller or len(fixtures) != expected_fixture or len(foreign) != expected_foreign:
        timer_errors.append('Owned scope recipe mismatch: ' + mode)
    if any(not re.fullmatch(r'PG_TIMER_CONTROLLER_CLEANUP thread_id=[1-9]\d* all_terminated=true', x) for x in controllers):
        timer_errors.append('Invalid controller cleanup: ' + mode)
    if fixtures != ['PG_TIMER_FIXTURE_CLEANUP all_terminated=true emergency=false proof=MODEL_PROVIDER'] * expected_fixture:
        timer_errors.append('Synthetic fixture emergency or missing cleanup: ' + mode)
    if any(not re.fullmatch(r'PG_TIMER_FOREIGN_CLEANUP thread_id=[1-9]\d* all_terminated=true own_ref_only=true', x) for x in foreign):
        timer_errors.append('Foreign ownership cleanup mismatch: ' + mode)
    for receipt in controllers + fixtures + foreign:
        scope_receipts.append(dict(suite=group['suite'], mode=mode, receipt=receipt))

old_children = [(name, line) for name in prior_suites for line in lines.get(name, []) if line.startswith(CHILD_PREFIXES)]
old_pids = [int(re.search(r'\bpid=(\d+)\b', line)[1]) for _, line in old_children]
old_scopes = [(name, line) for name in prior_suites for line in lines.get(name, []) if line.startswith(SCOPE_PREFIXES)]
commands = result['commands']
log = (EVIDENCE / 'validation.log').read_text()
cleanup_commands = {c['name']: c for c in commands if c['name'] in ('stop-after-validation', 'clean', 'stop-after-clean')}
builds = [REPO / 'build', ROOT / 'review/working/app-29-w01-local-dependencies-20260905/backend-build']
lint = [i for i in result['retained_reports'] if '/ktlint/' in i['path']]
detekt = EVIDENCE / 'reports/reports/detekt/detekt.xml'
detekt_errors = [dict(e.attrib) for e in ET.parse(detekt).getroot().iter('error')] if detekt.exists() else ['missing report']
current_classes = {Path(i['path']).stem: i['sha256'] for i in result.get('retained_bytecode', [])}
prior_classes = {Path(i['path']).stem: i['sha256'] for i in prior_result['retained_bytecode']}
disassembly_path = EVIDENCE / 'inspect-owned-control-bytecode.log'
disassembly = disassembly_path.read_bytes() if disassembly_path.exists() else b''
test_disassembly_path = EVIDENCE / 'inspect-handler-test-bytecode.log'
test_disassembly = test_disassembly_path.read_text() if test_disassembly_path.exists() else ''
race = 'MODEL concurrent duplicate during capture cannot be overwritten by callback success'
checks = {
    'all_tests_pass': bool(suites) and not failures and all(totals[k] == 0 for k in ('failures', 'errors', 'skipped')),
    'exact_frozen_test_and_suite_counts': totals['tests'] == manifest['expected_total_tests'] and len(suites) == manifest['expected_total_suites'],
    'all_2705_actual20_occurrences_preserved': not (prior_ids - ids),
    'all_87_actual20_suite_counts_preserved': all(suites.get(name) == count for name, count in prior_suites.items()),
    'only_two_timer_suites_added': set(suites) - set(prior_suites) == timer_suites and all(n in timer_suites for n, _ in new_ids),
    'exact_44_timer_method_argument_occurrences': inventory_ok and sum(new_ids.values()) == 44,
    'baseline_133_child_recipes_preserved': len(old_children) == 133 and recipes(lines, prior_suites, CHILD_PREFIXES) == recipes(prior_lines, prior_suites, CHILD_PREFIXES),
    'baseline_587_scope_recipes_preserved': len(old_scopes) == 587 and recipes(lines, prior_suites, SCOPE_PREFIXES) == recipes(prior_lines, prior_suites, SCOPE_PREFIXES),
    'baseline_all_pg_protocol_recipes_preserved': recipes(lines, prior_suites, ('PG_',)) == recipes(prior_lines, prior_suites, ('PG_',)),
    'all_baseline_child_pids_absent': len(old_pids) == 133 and all(absent(p) for p in old_pids),
    'timer_42_distinct_modes_and_natural_exits': set(timer_groups) == set(expected_modes) and len(timer_children) == 42 and len({c['nonce'] for c in timer_children}) == 42 and all(c['absent'] for c in timer_children),
    'timer_38_positive_four_negative_and_owned_cleanup_recipes': not timer_errors and len(timer_groups) == 42 and len(scope_receipts) == 56,
    'ktlint_unfiltered_pass': len(lint) == 3 and all(not (EVIDENCE / i['path']).read_text().strip() for i in lint) and '> Task :ktlintCheck\n' in log,
    'detekt_unfiltered_pass': not detekt_errors and '> Task :detekt\n' in log and ':detekt FAILED' not in log,
    'no_compiler_errors_or_warnings': not any(x.startswith(('w: ', 'e: ')) for x in log.splitlines()),
    'all_verification_inspection_commands_zero': all(c.get('exit_code') == 0 for c in commands),
    'exact_frozen_validation_cli_tasks': commands[0]['command'][-len(manifest['validation_task_args']):] == manifest['validation_task_args'],
    'immediate_stop_clean_final_stop_pass': len(cleanup_commands) == 3 and all(c['exit_code'] == 0 for c in cleanup_commands.values()) and commands[1]['name'] == 'stop-after-validation' and commands[-2]['name'] == 'clean' and commands[-1]['name'] == 'stop-after-clean',
    'owned_command_pids_absent': all(absent(c['pid']) for c in commands),
    'owned_build_outputs_absent': all(not p.exists() and not p.is_symlink() for p in builds),
    'all_frozen_class_evidence_retained': set(current_classes) == set(manifest['evidence_class_names']) and not result.get('bytecode_capture_failure'),
    'baseline20_class_bytes_preserved': all(current_classes.get(n) == digest for n, digest in prior_classes.items()),
    'baseline20_full_disassembly_prefix_preserved': disassembly.startswith((prior / 'inspect-owned-control-bytecode.log').read_bytes()),
    'race_descriptor_and_separate_test_class_preserved': len(result.get('retained_test_bytecode', [])) == 1 and result['retained_test_bytecode'][0]['sha256'] == prior_result['retained_test_bytecode'][0]['sha256'] and bool(re.search(re.escape('public final void ' + race + '();') + r'\s+descriptor: \(\)V', test_disassembly)),
    'reports_collected': not result.get('report_capture_failure'),
    'git_diff_check_pass': result['git_diff_check_exit'] == 0,
}
non_test = {k for k in checks if k.startswith(('ktlint_', 'detekt_', 'no_compiler_', 'all_verification_', 'exact_frozen_validation_', 'immediate_', 'owned_', 'all_frozen_class_', 'baseline20_', 'race_descriptor_', 'reports_', 'git_'))}
states = {k: ('NOT_RUN' if not suites and k not in non_test else 'PASS' if v else 'FAIL') for k, v in checks.items()}
summary = dict(timestamp=datetime.datetime.now().astimezone().isoformat(),
               status='FOCUSED_STATIC_PASS_NOT_TIMER_ACCEPTANCE' if all(checks.values()) else 'FAILED_NOT_ACCEPTED',
               collection_basis='Fresh Timer-A02 correction run; failed timer-A01 stays immutable; accepted actual20 source/case/receipt baseline; no historical execution repeated.',
               checks=checks, check_states=states, totals=dict(totals), suites=suites, suite_count=len(suites),
               test_execution='EXECUTED' if suites else 'NOT_EXECUTED', failed_tests=failures,
               missing_baseline_occurrences=sum((prior_ids - ids).values()), added_occurrences=sum(new_ids.values()),
               timer_discovery=discovered_methods, timer_groups=timer_groups, timer_child_receipts=timer_children,
               timer_scope_receipts=scope_receipts, timer_receipt_errors=timer_errors,
               baseline_child_count=len(old_children), baseline_scope_count=len(old_scopes), baseline_child_pids=old_pids,
               compiler_diagnostics=[x for x in log.splitlines() if x.startswith(('w: ', 'e: '))], detekt_findings=detekt_errors,
               source_manifest=result['source_manifest'], source_manifest_sha256=result['source_manifest_sha256'],
               result_sha256=sha(result_path), validation_log_sha256=sha(EVIDENCE / 'validation.log'),
               report_count=len(result['retained_reports']), main_class_count=len(current_classes),
               disk_free_gib=round(shutil.disk_usage(ROOT).free / 2**30, 2),
               runtime='UNKNOWN', D1_W03='INCOMPLETE', accepted_packages='2/9 unequal; W06 excluded', delivered='0/152',
               limits='Independent actual-diff/execution reviews required. No root/drain/terminal/physical-disposal or production acceptance; scheduler-interference premise UNVERIFIED. MODEL provider/cell cuts are not real partial VM failure. Per-suite receipts do not manufacture per-case resource ownership.')
with OUTPUT.open('x') as target:
    json.dump(summary, target, indent=2)
    target.write('\n')
print(OUTPUT.relative_to(ROOT), sha(OUTPUT))
print(summary['status'], dict(totals), 'suites', len(suites), 'timer additions', sum(new_ids.values()))
print('Failed checks:', [k for k, v in checks.items() if not v])
print('Timer receipt errors:', timer_errors)
