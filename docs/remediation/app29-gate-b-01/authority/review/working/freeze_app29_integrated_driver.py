#!/usr/bin/env python3
"""Freeze development/final lifecycle source and exact validation tasks without modifying product files."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
repo = root / 'kira-backend'
name, *tasks = sys.argv[1:]
assert name.startswith('app-29-w03-integrated-driver-') and Path(name).name == name and tasks
out = root / 'review/working' / name
assert not out.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
previous = root / 'review/working/app-29-w03-d1-timer-a-02/manifest.json'
baseline = json.loads(previous.read_text())
git = lambda d, *args: subprocess.check_output(['git', *args], cwd=d, text=True)
paths = set(baseline['source_hashes'])
paths.update(git(repo, 'diff', '--name-only').splitlines())
paths.update(git(repo, 'ls-files', '--others', '--exclude-standard').splitlines())
source = {p: sha(repo / p) for p in sorted(paths) if (repo / p).is_file()}
removed = sorted(paths - source.keys())
assert removed == sorted(baseline['removed_paths']), 'Review new removal/rename explicitly before freezing.'
changed = [p for p in baseline['source_hashes'] if source[p] != baseline['source_hashes'][p]]
added = sorted(source.keys() - baseline['source_hashes'].keys())
subjects = sorted(changed + added)
out.mkdir()
snapshots = {}
for p in subjects:
    dst = out / 'sources' / p
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes((repo / p).read_bytes())
    snapshots[str(dst.relative_to(root))] = sha(dst)
repos, refs = {}, {}
for name in ['Kira manga', 'kira-backend', 'kira-admin', 'kira-source-engine', 'kira-web']:
    folder = root / name
    repos[name] = {'head': git(folder, 'rev-parse', 'HEAD').strip(), 'branch': git(folder, 'branch', '--show-current').strip(),
                   'status': git(folder, 'status', '--porcelain=v1')}
    assert not git(folder, 'diff', '--cached', '--name-only')
    refs[name] = git(folder, 'rev-parse', 'remediation/production-readiness-2026-09-04').strip()
tooling = ['review/working/run_app29_integrated_driver_validation.py', 'review/working/app-29-w01-local-dependencies.init.gradle',
           str(Path(__file__).resolve().relative_to(root))]
plans = ['review/remediation/app-29-w03-integrated-driver-completion-plan-v1.md',
         'review/remediation/app-29-w03-integrated-driver-development-corrections.md']
manifest = {
    'timestamp': datetime.datetime.now().astimezone().isoformat(), 'status': 'FROZEN DEVELOPMENT CANDIDATE - NOT ACCEPTANCE',
    'validation_scope': 'DEVELOPMENT ONLY: integrated lifecycle corrections; full D1/W03/release acceptance remains incomplete',
    'source_hashes': source, 'snapshots': snapshots, 'review_subject_paths': subjects,
    'changed_previous_paths': changed, 'added_paths': added, 'removed_paths': removed,
    'previous_manifest': str(previous.relative_to(root)), 'previous_manifest_sha256': sha(previous),
    'repositories': repos, 'integration_refs': refs,
    'complete_diff_sha256': hashlib.sha256(subprocess.check_output(['git', 'diff', '--binary'], cwd=repo)).hexdigest(),
    'approved_inputs': {p: sha(root / p) for p in plans}, 'validation_tooling': {p: sha(root / p) for p in tooling},
    'validation_task_args': tasks,
    'evidence_class_names': ['PersistenceJdbcLifecycleOwner', 'PersistenceJdbcDriverRoot', 'PersistenceJdbcParticipant',
                           'PersistenceTerminalWork', 'PersistenceTerminalRunner', 'PersistencePhysicalCompletion', 'PersistenceDriverTimer',
                           'PersistencePgTimerAccess$Boundary', 'PersistencePgTimerAccess$BoundaryCell', 'PersistencePgTimerAccess$BoundaryTask'],
    'runtime': 'UNKNOWN', 'W03': 'INCOMPLETE',
}
path = out / 'manifest.json'
path.write_text(json.dumps(manifest, indent=2) + '\n')
print(path.relative_to(root), sha(path))
print('Source paths:', len(source), 'review subjects:', len(subjects))
