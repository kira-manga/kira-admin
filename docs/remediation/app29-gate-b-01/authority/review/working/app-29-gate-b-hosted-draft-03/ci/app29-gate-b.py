#!/usr/bin/env python3
"""One private Gate B consumer check. No execution on import; request is unbound by default."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import tarfile
import time
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

ADMIN = Path(__file__).resolve().parent.parent
BACKEND = ADMIN.parent / 'backend'
PAYLOAD = ADMIN / 'docs/remediation/app29-gate-b-01'
GATE = 'app-29-gate-b-hosted-01'
CLASS = 'me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest'
METHOD = 'original provider retains a real opening capsule without inventing tracked transport evidence'
TASKS = ['test', '--tests', CLASS + '.original*']
SEED = 'review/working/app-29-w03-integrated-driver-development-07/manifest.json'
SEED_SHA = '3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a'
OWNER_SHA = '56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385'
ARCHIVE_SHA = 'da94218f74eb0f5831241c8606c8f82142e49b818acfaff027a78f2efe77faab'
LOCAL_SHA = 'c67fcc5fe64a9a795373c4683c7c1edd6407146e3cd07609fa7018a8a98db79a'
INIT_SHA = '429961b98254b89f7ce1d7ba1efa61b8cba28a3bae35353bf3a8ba85f4a1c839'
PREFIX = 'review/working/app-29-w01-local-dependencies-20260905/'
IMAGES = {'postgres:17.6-alpine', 'testcontainers/ryuk:0.12.0'}
BACKEND_BRANCH = 'remediation/app-29-backend-complaints'
PUBLIC_PREREQUISITE = '3d839130c807f6a0a9b1c896c1c6cca4b41c4538'
SOURCE_BUNDLE = {'public_prerequisite_sha': PUBLIC_PREREQUISITE, 'ref': 'refs/heads/' + BACKEND_BRANCH,
                 'source_path': 'review/working/app-29-gate-b-private-checkpoint-01/backend.bundle',
                 'path': 'docs/remediation/app29-gate-b-01/inputs/backend.bundle'}
BUNDLE_MAX_BYTES = 8 * 1024**2
DEPLOYMENTS = {f'review/working/app-29-gate-b-hosted-draft-03/{p}': p for p in (
    'ci/app29-gate-b.py', 'ci/app29-gate-b.profile.json', 'ci/app29-gate-b.init.gradle',
    '.github/workflows/app29-gate-b.yml')}
DEPLOYMENTS['review/working/app-29-targeted-private-ci-draft-v2/ci/app29_owned_children.py'] = 'ci/app29_owned_children.py'
CACHE_PATHS = ('.gradle', '.kotlin', 'build', 'buildSrc/build', 'out')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe(root, relative):
    parts = PurePosixPath(relative).parts
    require(isinstance(relative, str) and parts and not relative.startswith('/')
            and all(p not in ('', '.', '..') for p in parts) and '\\' not in relative
            and PurePosixPath(relative).as_posix() == relative, 'Unsafe bound path')
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), 'Symlink in bound input/output')
    return path


def digest(path, limit=512 * 1024**2):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit, 'Missing/oversized regular input')
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def read_json(path):
    digest(path, 16 * 1024**2)
    return json.loads(path.read_text(), object_pairs_hook=unique)


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def remove_owned(root, relative):
    path = safe(root, relative)
    if path.exists():
        require(path.is_dir(), 'Owned output became a non-directory')
        shutil.rmtree(path)


def source_bundle_binding(binding):
    value = binding['source_bundle']
    require(isinstance(value, dict) and set(value) == set(SOURCE_BUNDLE) | {'sha256', 'bytes'}
            and all(value[k] == v for k, v in SOURCE_BUNDLE.items()), 'Wrong fixed private source transport')
    require(type(value['bytes']) is int and 0 < value['bytes'] <= BUNDLE_MAX_BYTES
            and isinstance(value['sha256'], str) and re.fullmatch('[0-9a-f]{64}', value['sha256'])
            and value['sha256'] != '0' * 64 and binding['backend_sha'] != PUBLIC_PREREQUISITE,
            'Unbound/oversized private checkpoint bundle')
    return value


def bundle_header(data, tip):
    header, separator, pack = data.partition(b'\n\n')
    lines = header.split(b'\n')
    require(len(data) <= BUNDLE_MAX_BYTES and separator and len(header) <= 4096
            and len(pack) >= 32 and pack.startswith(b'PACK'), 'Missing/bounded complete bundle header/pack')
    require(len(lines) == 3 and lines[0] == b'# v2 git bundle'
            and re.fullmatch(b'-' + PUBLIC_PREREQUISITE.encode('ascii') + rb' [^\x00-\x1f\x7f]*', lines[1])
            and lines[2] == (tip + ' ' + SOURCE_BUNDLE['ref']).encode('ascii'),
            'Expected complete SHA1 v2 singleton prerequisite/ref/tip; no capabilities or filtering')
    return {'format': 'git-bundle-v2-sha1-complete', 'tip': tip}


def read_source_bundle(binding):
    item = source_bundle_binding(binding)
    path = safe(ADMIN, item['path'])
    require(path.is_file() and not path.is_symlink() and path.stat().st_size == item['bytes'],
            'Private source bundle must be a pinned regular bounded file')
    with path.open('rb') as source:
        data = source.read(BUNDLE_MAX_BYTES + 1)
    require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
            'Initially bound private source bundle changed')
    return item | bundle_header(data, binding['backend_sha'])


def request():
    value = read_json(ADMIN / 'ci/app29-gate-b.request.json')
    require(value['schema'] == GATE and value['authorized'] is True and value['attempts'] == 1,
            'Primary execution authority and one attempt are required')
    require(re.fullmatch('[0-9a-f]{40}', value['backend_sha']) and value['backend_sha'] != '0' * 40,
            'Unbound checkpoint')
    require(value['budgets'] == {'job_minutes': 25, 'controller_seconds': 1200,
                                'preflight_seconds': 120, 'validation_seconds': 900, 'cleanup_seconds': 180},
            'Separately approved fixed phase/total budgets required')
    require(set(value['tool_sha256']) == set(DEPLOYMENTS.values()), 'Wrong dedicated tooling inventory')
    for relative, sha in value['tool_sha256'].items():
        require(digest(safe(ADMIN, relative)) == sha, 'Changed dedicated tool')
    require(digest(ADMIN / 'ci/app29_owned_children.py') == OWNER_SHA, 'Shared ownership utility changed')
    require(digest(PAYLOAD / 'checkpoint.json') == value['checkpoint_sha256'], 'Unbound checkpoint receipt')
    checkpoint = read_json(PAYLOAD / 'checkpoint.json')
    require(checkpoint['schema'] == 'app29-gate-b-clean-checkpoint-v1' and checkpoint['source_accepted'] is True
            and checkpoint['backend_sha'] == value['backend_sha']
            and checkpoint['source_bundle'] == source_bundle_binding(value), 'Unbound accepted private source transport')
    return value


def extract_local(w01):
    archive = ADMIN / 'docs/remediation/checkpoint-2026-09-08/review-evidence.tar.gz'
    require(digest(archive) == ARCHIVE_SHA, 'Historical private archive changed')
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()  # Reuse the 18-member allowlist; never extractall or links.

        def member(name, sha, limit=16 * 1024**2):
            selected = [m for m in members if m.name == name]
            require(len(selected) == 1 and selected[0].isfile() and 0 <= selected[0].size <= limit, 'Invalid allowlisted member')
            data = bundle.extractfile(selected[0]).read(limit + 1)
            require(len(data) == selected[0].size and hashlib.sha256(data).hexdigest() == sha, 'Archive member changed')
            return data

        manifest = member(PREFIX + 'local-inputs.sha256', LOCAL_SHA, 16384)
        entries = [line.split('  ', 1) for line in manifest.decode('ascii').splitlines()]
        require(len(entries) == 18 and all(len(e) == 2 for e in entries)
                and len({e[1] for e in entries}) == 18, 'Expected the exact 18-member manifest')
        (w01 / 'local-inputs.sha256').write_bytes(manifest)
        (w01 / 'original.init.gradle').write_bytes(member('review/working/app-29-w01-local-dependencies.init.gradle', INIT_SHA, 16384))
        for sha, relative in entries:
            require(re.fullmatch('[0-9a-f]{64}', sha) and relative.startswith('me/manga/kira/source/'), 'Unsafe local input')
            path = safe(w01 / 'repository', relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(member(PREFIX + 'repository/' + relative, sha))
    return {str(p.relative_to(w01)): digest(p) for p in w01.rglob('*') if p.is_file()}


def bind_freeze(binding, profile):
    """Transport check of a locally validated clean-checkpoint freeze, NOT hosted v3 validation."""
    require(digest(PAYLOAD / 'checkpoint.json') == binding['checkpoint_sha256'], 'Initially bound checkpoint changed')
    checkpoint = read_json(PAYLOAD / 'checkpoint.json')
    require(checkpoint['schema'] == 'app29-gate-b-clean-checkpoint-v1' and checkpoint['source_accepted'] is True
            and checkpoint['backend_sha'] == binding['backend_sha'], 'Missing primary source acceptance')
    source_bundle = source_bundle_binding(binding)
    require(checkpoint['source_bundle'] == source_bundle, 'Checkpoint/private bundle binding changed')
    authority = PAYLOAD / 'authority'
    path = safe(authority, checkpoint['manifest_path'])
    require(digest(path) == checkpoint['manifest_sha256'], 'Frozen manifest changed')
    manifest = read_json(path)
    require(manifest['schema_version'] == 3 and manifest['validation_task_args'] == TASKS
            and manifest['repositories']['kira-backend'] == {'head': binding['backend_sha'],
                 'branch': 'remediation/app-29-backend-complaints', 'status': ''}
            and manifest['untracked_paths'] == [], 'Freeze must follow the clean source checkpoint')
    require(manifest['inventory_seed_manifest'] == SEED and manifest['inventory_seed_manifest_sha256'] == SEED_SHA
            and manifest['inventory_seed_path_count'] == manifest['inventory_seed_preserved_count'] == 348,
            'Complete historical inventory continuity required')
    require(digest(safe(authority, SEED)) == SEED_SHA, 'Seed changed')
    seed = read_json(safe(authority, SEED))
    require(len(seed['source_hashes']) == 348 and seed['source_hashes'].keys() <= manifest['source_hashes'].keys(), 'Seed path omitted')
    proof = checkpoint['local_v3_preflight']
    require(proof['manifest_sha256'] == checkpoint['manifest_sha256']
            and proof['tool_sha256'] == 'e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe'
            and digest(safe(authority, proof['receipt_path'])) == proof['receipt_sha256'], 'Unbound local verification receipt')
    receipt = read_json(safe(authority, proof['receipt_path']))
    require(receipt == {'status': 'READ_ONLY_V3_PREFLIGHT_PASSED', 'source_paths': len(manifest['source_hashes'])},
            'Local v3 validation is missing; hosted transport cannot replace it')
    pins = {checkpoint['manifest_path']: checkpoint['manifest_sha256'], proof['receipt_path']: proof['receipt_sha256']}
    for field in ('snapshots', 'historical_input_hashes', 'approved_inputs', 'validation_tooling'):
        for relative, sha in manifest[field].items():
            require(relative not in pins or pins[relative] == sha, 'Contradictory authority pin')
            pins[relative] = sha
    pins[manifest['complete_diff_path']] = manifest['complete_diff_sha256']
    for relative, sha in pins.items():
        require(digest(safe(authority, relative)) == sha, 'Transported authority/snapshot/diff changed')
    require(manifest['approved_inputs'].get(source_bundle['source_path']) == source_bundle['sha256']
            and safe(authority, source_bundle['source_path']).stat().st_size == source_bundle['bytes'],
            'Private source bundle missing from original approved freeze inputs')
    for relative, sha in manifest['source_hashes'].items():
        require(digest(safe(BACKEND, relative)) == sha, 'Effective checkpoint differs from frozen source')
    require(all(not safe(BACKEND, p).exists() for p in manifest['removed_paths']), 'Removed source reappeared')
    for original, deployed in DEPLOYMENTS.items():
        require(manifest['validation_tooling'].get(original) == digest(safe(ADMIN, deployed)), 'Deployed tool differs from freeze')
    for key in ('final_jar', 'checker'):
        item = profile[key]
        path = safe(ADMIN, item['path'])
        require(manifest['approved_inputs'].get(item['source_path']) == item['sha256']
                and digest(path) == item['sha256'] and path.stat().st_size == item['bytes'], 'Wrong consumer artifact')
    reference = profile['input_profile_reference']
    require(manifest['approved_inputs'].get(reference['path']) == reference['sha256'], 'Historical input reference missing')
    return {'manifest_sha256': checkpoint['manifest_sha256'], 'sources': len(manifest['source_hashes']),
            'seed_paths': 348, 'local_v3': 'PRIMARY_BOUND_LOCAL_RECEIPT_NOT_HOSTED_REEXECUTION', 'authority_files': len(pins)}


class Gate:
    def __init__(self, binding):
        from app29_owned_children import OwnedChildren  # Hash checked first; immutable import has no actions.
        self.binding, self.owner = binding, None
        self.start = time.monotonic()
        self.end = self.start + binding['budgets']['controller_seconds']
        self.phase_end = self.start + binding['budgets']['preflight_seconds']
        self.cancelled, self.started, self.clean_daemon, self.events_since = False, False, False, None
        self.run = Path(os.environ['RUNNER_TEMP']) / ('app29-gate-b-' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT'])
        self.run.mkdir(mode=0o700, exist_ok=False)
        for name in ('reports', 'gradle', 'w01', 'tmp', 'home', 'project-cache', 'kotlin-cache'):
            (self.run / name).mkdir(mode=0o700)
        self.reports, self.w01 = self.run / 'reports', self.run / 'w01'
        self.result = {'status': 'FAIL', 'gate': GATE, 'backend_sha': binding['backend_sha'],
                       'carrier_sha': os.environ['GITHUB_SHA'], 'commands': [], 'failures': [], 'processes': [],
                       'containers': 'UNKNOWN', 'outputs_absent': False, 'capture_complete': False}
        self.java = Path(os.environ['JAVA_HOME']).resolve()
        self.env = {'PATH': str(self.java / 'bin') + ':/usr/bin:/bin', 'JAVA_HOME': str(self.java),
                    'HOME': str(self.run / 'home'), 'GRADLE_USER_HOME': str(self.run / 'gradle'),
                    'W01_RUN': str(self.w01), 'TMPDIR': str(self.run / 'tmp'), 'LANG': 'C.UTF-8', 'TZ': 'UTC',
                    'GATE_B_ADMIN': str(ADMIN), 'GATE_B_BACKEND': str(BACKEND), 'GATE_B_RUN': str(self.run),
                    'DOCKER_HOST': 'unix:///var/run/docker.sock', 'TESTCONTAINERS_REUSE_ENABLE': 'false',
                    'TESTCONTAINERS_RYUK_DISABLED': 'false'}
        self.owner_type = OwnedChildren  # Acquisition happens inside execute's protected try/finally.
        save(self.reports / 'result.json', self.result)

    def fail(self, stage, error):
        self.result['failures'].append({'stage': stage, 'type': type(error).__name__})

    def attempt(self, stage, action):
        try:
            return action()
        except BaseException as error:
            self.fail(stage, error)
            return None

    def drain(self, stage):
        receipt = self.attempt(stage, self.owner.drain) if self.owner is not None else None
        absent = isinstance(receipt, dict) and receipt.get('ok') is True
        outcome = 'UNKNOWN' if not absent else ('FORCED_ABSENT' if receipt.get('term') or receipt.get('kill') else 'NORMAL_ABSENT')
        self.result['processes'].append({'stage': stage, 'outcome': outcome, 'receipt': receipt})
        if outcome != 'NORMAL_ABSENT':
            self.fail(stage, RuntimeError())
        if absent and any(row.get('actual_exit') != 0 for row in receipt.get('leaders', []) + receipt.get('adopted', [])):
            self.fail(stage + '-nonzero-child', RuntimeError())
        return absent

    def command(self, name, argv, seconds=30, cleaning=False, cwd=BACKEND, api=False):
        require(self.owner is not None, 'No owned child capability')
        deadline = min(self.end, time.monotonic() + seconds, self.end if cleaning else self.phase_end)
        require(deadline > time.monotonic() and (cleaning or not self.cancelled), 'Phase/cancellation budget exhausted')
        path = self.reports / (name + '.log')
        entry = {'name': name, 'argv': argv, 'cwd': str(cwd), 'actual_exit': None, 'outcome': 'UNKNOWN'}
        self.result['commands'].append(entry)
        save(self.reports / 'result.json', self.result)
        with path.open('xb') as log:
            process = subprocess.Popen(argv, cwd=cwd, env=self.env | ({'DOCKER_API_VERSION': '1.32'} if api else {}),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            self.owner.active[process.pid] = process  # Protect the handle BEFORE any fallible collection/publication.
            entry['pid'] = process.pid
            try:
                while process.poll() is None:
                    require(time.monotonic() < deadline and (cleaning or not self.cancelled), 'Command deadline/cancellation')
                    require(path.stat().st_size <= 64 * 1024**2, 'Command output limit')
                    time.sleep(0.05)
                entry['actual_exit'] = process.returncode
                require(process.returncode == 0, 'Nonzero owned command')
                entry['outcome'] = 'NORMAL'
            except BaseException:
                self.drain('interrupted-' + name)
                entry['actual_exit'] = process.returncode
                raise
        digest(path, 64 * 1024**2)
        return path.read_bytes()

    def materialize_source(self):
        initial = {
            'head': self.command('initial-backend-sha', ['git', 'rev-parse', 'HEAD']).decode().strip(),
            'branch': self.command('initial-backend-branch', ['git', 'branch', '--show-current']).decode().strip(),
            'status': self.command('initial-backend-status', ['git', 'status', '--porcelain=v1', '--untracked-files=all']).decode()}
        self.result['source_checkout_initial'] = initial
        require(initial == {'head': PUBLIC_PREREQUISITE, 'branch': '', 'status': ''},
                'Require exact clean detached public prerequisite before private import')
        require(digest(PAYLOAD / 'checkpoint.json') == self.binding['checkpoint_sha256'], 'Initially bound checkpoint changed before import')
        self.result['source_bundle_before'] = read_source_bundle(self.binding)
        path = str(safe(ADMIN, SOURCE_BUNDLE['path']))
        self.command('source-bundle-verify', ['git', 'bundle', 'verify', path])
        self.command('source-bundle-fetch', ['git', '-c', 'protocol.allow=never', '-c', 'protocol.file.allow=always',
                     'fetch', '--no-tags', '--no-recurse-submodules', '--no-write-fetch-head', '--no-auto-maintenance',
                     '--', path, SOURCE_BUNDLE['ref'] + ':' + SOURCE_BUNDLE['ref']])
        self.command('source-bundle-checkout', ['git', '-c', 'core.hooksPath=/dev/null', 'checkout',
                     '--no-guess', '--no-recurse-submodules', BACKEND_BRANCH])

    def sources(self, label, cleaning=False):
        sha = self.command(label + '-backend-sha', ['git', 'rev-parse', 'HEAD'], cleaning=cleaning).decode().strip()
        branch = self.command(label + '-backend-branch', ['git', 'branch', '--show-current'], cleaning=cleaning).decode().strip()
        commit = self.command(label + '-backend-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', 'HEAD'], cleaning=cleaning)
        header, separator, _ = commit.partition(b'\n\n')
        parents = [row[7:].decode('ascii') for row in header.split(b'\n') if row.startswith(b'parent ')]
        self.result.setdefault('source_checkout_final', {})[label] = {'head': sha, 'branch': branch, 'parents': parents}
        require(sha == self.binding['backend_sha'] and branch == BACKEND_BRANCH
                and separator and parents == [PUBLIC_PREREQUISITE], 'Effective checkout HEAD/branch/sole parent changed')
        require(not self.command(label + '-status', ['git', 'status', '--porcelain=v1', '--untracked-files=all'], cleaning=cleaning), 'Checkpoint is dirty')
        names = self.command(label + '-tracked', ['git', 'ls-files', '-z'], cleaning=cleaning).decode().split('\0')[:-1]
        hashes = {p: digest(safe(BACKEND, p)) for p in names}
        actual = set()
        for folder, directories, files in os.walk(BACKEND, followlinks=False):
            relative = Path(folder).relative_to(BACKEND)
            directories[:] = [d for d in directories if (relative / d).as_posix() not in ('.git', *CACHE_PATHS)]
            require(not any((Path(folder) / d).is_symlink() for d in directories), 'Unexpected source directory link')
            actual.update((relative / f).as_posix() for f in files)
        require(actual == set(hashes), 'Extra/untracked/ignored effective source input')
        save(self.reports / (label + '-source-hashes.json'), hashes)
        return hashes

    def census(self, label, cleaning=True):
        data = self.command(label, ['docker', 'ps', '-aq', '--no-trunc'], cleaning=cleaning, api=True).decode().splitlines()
        require(all(re.fullmatch('[0-9a-f]{64}', cid) for cid in data) and len(data) == len(set(data)), 'Invalid container census')
        return set(data)

    def containers(self):
        require(self.clean_daemon and self.events_since is not None, 'No clean dedicated-daemon/run binding')
        until = time.monotonic() + 20
        for index in range(21):
            remaining = self.census('containers-normal-' + str(index))
            if not remaining or time.monotonic() >= until:
                break
            time.sleep(1)
        journal = self.command('container-events', ['docker', 'events', '--since', str(self.events_since),
                               '--until', str(int(time.time()) + 1), '--filter', 'type=container', '--format', '{{json .}}'],
                               cleaning=True, api=True).decode().splitlines()
        created, destroyed = {}, set()
        for line in journal:
            event = json.loads(line, object_pairs_hook=unique)
            if event.get('Action') not in ('create', 'destroy'):
                continue
            actor = event['Actor']
            cid, labels = actor['ID'], actor['Attributes']
            require(re.fullmatch('[0-9a-f]{64}', cid) and labels.get('image') in IMAGES
                    and labels.get('org.testcontainers') == 'true' and labels.get('org.testcontainers.version') == '1.21.4',
                    'Unknown container custody; do not remove')
            if event['Action'] == 'create':
                require(cid not in created, 'Duplicate container creation identity')
                created[cid] = labels
            else:
                destroyed.add(cid)
        require(len(created) == 2 and {r['image'] for r in created.values()} == IMAGES
                and destroyed <= created.keys() and remaining <= created.keys(), 'Incomplete/unexpected container journal')
        pg = next(r for r in created.values() if r['image'] == 'postgres:17.6-alpine')
        ryuk = next(r for r in created.values() if r['image'] != 'postgres:17.6-alpine')
        session = pg.get('org.testcontainers.sessionId', '')
        require(re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', session)
                and ryuk.get('name') == 'testcontainers-ryuk-' + session, 'Unknown fixture/Ryuk session')
        save(self.reports / 'owned-containers.json', {'created': created, 'destroyed': sorted(destroyed), 'remaining': sorted(remaining)})
        for index, image in enumerate(sorted(IMAGES)):
            raw = self.command('image-' + str(index), ['docker', 'image', 'inspect', '--format',
                               '{"id":{{json .Id}},"tags":{{json .RepoTags}},"digests":{{json .RepoDigests}}}', image], cleaning=True, api=True)
            identity = json.loads(raw, object_pairs_hook=unique)
            require(re.fullmatch('sha256:[0-9a-f]{64}', identity['id']) and image in identity['tags']
                    and identity['digests'] and all(re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', d) for d in identity['digests']),
                    'Incomplete resolved image identity')
        if remaining:
            self.result['containers'] = 'FORCED_PENDING'
            self.result['container_forced'] = True
            self.fail('container-normal-cleanup', RuntimeError())
            # Known created IDs only; clean dedicated daemon and same Testcontainers session are prerequisites.
            self.command('remove-owned-containers', ['docker', 'rm', '-fv', *sorted(remaining)], cleaning=True, api=True)
        else:
            require(destroyed == created.keys(), 'Missing normal destroy events')
        require(not self.census('containers-after-cleanup'), 'Container absence unproved')
        self.result['containers'] = 'FORCED_ABSENT' if remaining else 'NORMAL_ABSENT'
        return True


def consumer(reports, profile, java):
    xmls = list((reports / 'test-results/test').glob('*.xml'))
    require([p.name for p in xmls] == ['TEST-' + CLASS + '.xml'], 'Wrong one-case XML inventory')
    raw = xmls[0].read_text(encoding='utf-8-sig')
    require('\x00' not in raw and '<!DOCTYPE' not in raw.upper() and '<!ENTITY' not in raw.upper(), 'Unsafe XML')
    suite = ET.fromstring(raw)
    cases = suite.findall('testcase')
    require(suite.tag == 'testsuite' and suite.get('name') == CLASS and suite.get('tests') == '1'
            and all(suite.get(k) == '0' for k in ('failures', 'errors', 'skipped')) and len(cases) == 1
            and cases[0].get('classname') == CLASS and cases[0].get('name') == METHOD + '()'
            and not any(node.tag in ('failure', 'error', 'skipped') for node in suite.iter()), 'Gate B testcase did not pass exactly once')
    folder = reports / 'reports/final-jar-profile'
    cp = read_json(folder / 'effective-classpath.txt')
    require(cp['profile'] == GATE and cp['java_home'] == str(java)
            and cp['input_profile_reference'] == profile['input_profile_reference'], 'Wrong actual classpath/profile/JDK')
    entries = cp['entries']
    require(len({e['path'] for e in entries}) == len(entries)
            and cp['removed_stock']['sha256'] == profile['removed_stock']['sha256']
            and cp['removed_stock']['path'] not in {e['path'] for e in entries}, 'Stock/duplicate classpath supplier')
    for key, flag in (('final_jar', 'postgres_classes'), ('checker', 'checker_classes')):
        rows = [e for e in entries if e[flag] > 0]
        require(len(rows) == 1 and rows[0]['path'] == str(safe(ADMIN, profile[key]['path']))
                and rows[0]['sha256'] == profile[key]['sha256'], 'Wrong explicit class supplier')
    lines = (folder / 'worker-runtime.txt').read_text().splitlines()
    pairs = [line.split('=', 1) for line in lines]
    require(all(len(p) == 2 for p in pairs), 'Malformed worker witness')
    worker = unique(pairs)
    require(worker['profile'] == profile['input_profile_reference']['profile_id'] and worker['provenance'] == 'PASS'
            and worker['java.home'] == str(java) and worker['worker.executable'] == str(java / 'bin/java')
            and '-Dkira.finalJarConsumer.gate=' + GATE in worker.values(), 'Wrong actual Gate B worker binding')
    require(re.fullmatch('[1-9][0-9]*', worker['worker.pid']), 'Invalid worker PID')
    logs = list(folder.glob('class-load-*.txt'))
    require([p.name for p in logs] == ['class-load-' + worker['worker.pid'] + '.txt'], 'Wrong worker class-load log inventory')
    observed = re.findall(r'\[class,load\s*\]\s+(\S+) source: (file:[^\r\n]+)', logs[0].read_text())
    bindings = [(n, profile['final_jar']['path']) for n in profile['origin_classes']] + [(profile['checker_class'], profile['checker']['path'])]
    for name, relative in bindings:
        sources = [urlsplit(uri) for actual, uri in observed if actual == name]
        expected = str(safe(ADMIN, relative))
        require(len(sources) == 1 and not sources[0].netloc and unquote(sources[0].path) == expected
                and worker['class.' + name + '.source'] == expected, 'Missing actual class-definition association')
    return {'status': 'PASS', 'tests': 1, 'class': CLASS, 'method': METHOD + '()', 'raw_class': 'org.postgresql.jdbc.PgConnection'}


def execute(binding):
    gate = Gate(binding)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: setattr(gate, 'cancelled', True))
    profile, baseline, local, jdk = None, None, None, None
    try:
        gate.owner = gate.owner_type()  # Before the first child, inside failure/cleanup protection.
        require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin'
                and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Dedicated private carrier/attempt required')
        require(not any(k in os.environ for k in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS')),
                'Inherited Java override is outside this profile')
        require(shutil.disk_usage(gate.run).free >= 8 * 1024**3, 'Require at least 8 GiB free')
        require(not any(safe(BACKEND, p).exists() for p in CACHE_PATHS), 'Preexisting outputs/caches; do not clean')
        carrier = gate.command('carrier-sha', ['git', 'rev-parse', 'HEAD'], cwd=ADMIN).decode().strip()
        require(carrier == os.environ['GITHUB_SHA'], 'Carrier checkout differs from exact workflow SHA')
        profile = read_json(ADMIN / 'ci/app29-gate-b.profile.json')
        require(profile['profile_id'] == GATE and profile['task_args'] == TASKS, 'Wrong Gate B profile')
        gate.materialize_source()
        baseline = gate.sources('before')
        gate.result['source_binding_before'] = bind_freeze(binding, profile)
        local = extract_local(gate.w01)
        release = (gate.java / 'release').read_text()
        require('IMPLEMENTOR="Eclipse Adoptium"' in release and re.search(r'^JAVA_VERSION="21(?:\.|\")', release, re.MULTILINE), 'Expected hosted Temurin21')
        jdk = {p: digest(safe(gate.java, p)) for p in ('bin/java', 'lib/modules', 'release')}
        save(gate.reports / 'jdk.json', {'home': str(gate.java), 'files': jdk, 'release': release})
        gate.command('jdk-version', [str(gate.java / 'bin/java'), '-Djava.io.tmpdir=' + str(gate.run / 'tmp'),
                                    '-Duser.home=' + str(gate.run / 'home'), '-XshowSettings:properties', '-version'])
        gate.command('docker-version', ['docker', 'version'], api=True)
        require(not gate.census('containers-before', cleaning=False), 'Preexisting containers; refuse daemon custody')
        require(time.monotonic() < gate.phase_end, 'Preflight phase expired')
        gate.clean_daemon = True
        gate.events_since = int(time.time())
        gate.phase_end = min(gate.end - binding['budgets']['cleanup_seconds'], time.monotonic() + binding['budgets']['validation_seconds'])
        gate.started = True
        gate.command('gradle-test', ['./gradlew', '--no-daemon', '--no-parallel', '--no-build-cache', '--no-configuration-cache',
                     '--dependency-verification=strict', '--max-workers=1', '--console=plain', '--project-cache-dir', str(gate.run / 'project-cache'),
                     '-Djava.io.tmpdir=' + str(gate.run / 'tmp'), '-Duser.home=' + str(gate.run / 'home'),
                     '-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m -Djava.io.tmpdir=' + str(gate.run / 'tmp') + ' -Duser.home=' + str(gate.run / 'home'),
                     '-Dorg.gradle.vfs.watch=false', '-PkiraUseMavenLocal=false', '-Pkotlin.compiler.execution.strategy=in-process',
                     '-Pkotlin.project.persistent.dir=' + str(gate.run / 'kotlin-cache'), '-Porg.gradle.java.installations.auto-download=false',
                     '-Porg.gradle.java.installations.auto-detect=false', '-Porg.gradle.java.installations.paths=' + str(gate.java),
                     '--init-script', str(ADMIN / 'ci/app29-gate-b.init.gradle'), *TASKS], seconds=binding['budgets']['validation_seconds'])
    except BaseException as error:
        gate.fail('validation', error)
    finally:
        gate.phase_end = gate.end  # Cleanup is bounded by the original total; signals only latch failure.
        if gate.started:
            gate.attempt('gradle-stop-immediate', lambda: gate.command('gradle-stop-immediate', ['./gradlew', '--stop'], seconds=60, cleaning=True))
        workers_gone = gate.drain('after-immediate-stop')
        containers_gone = gate.attempt('containers', gate.containers) if workers_gone and gate.started else False
        if workers_gone:
            gate.result['source_bundle_after'] = gate.attempt('source-bundle-postflight', lambda: read_source_bundle(binding))
            def capture():
                build = gate.w01 / 'backend-build'
                for name in ('test-results', 'reports'):
                    source = build / name
                    require(source.is_dir(), 'Required test/report root missing')
                    for path in source.rglob('*'):
                        require(not path.is_symlink(), 'Report link')
                        if path.is_file() and path.suffix in ('.xml', '.txt', '.json', '.log'):
                            digest(path, 64 * 1024**2)
                            destination = safe(gate.reports, str(path.relative_to(build)))
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(path, destination)
                            require(digest(destination) == digest(path), 'Evidence copy drift')
                gate.result['consumer'] = consumer(gate.reports, profile, gate.java)
                gate.result['capture_complete'] = True
            gate.attempt('capture-and-consumer', capture)
            def postflight():
                require(baseline is not None and gate.sources('after', cleaning=True) == baseline, 'Effective source changed')
                require(request() == binding, 'Initially accepted request changed')
                gate.result['source_binding_after'] = bind_freeze(binding, profile)
                require(local is not None and all(digest(safe(gate.w01, p)) == sha for p, sha in local.items()), 'Private dependency input drift')
                require(jdk is not None and all(digest(safe(gate.java, p)) == sha for p, sha in jdk.items()), 'JDK input drift')
            gate.result['inputs_preserved'] = gate.attempt('postflight', lambda: (postflight(), True)[1]) is True
        files_safe = workers_gone and containers_gone and gate.drain('before-file-cleanup') and gate.result['capture_complete']
        if files_safe:
            for relative in CACHE_PATHS:
                gate.attempt('backend-output-cleanup', lambda p=relative: remove_owned(BACKEND, p))
            for name in ('w01', 'project-cache', 'kotlin-cache'):
                gate.attempt('private-output-cleanup', lambda p=name: remove_owned(gate.run, p))
        if gate.started:
            gate.attempt('gradle-stop-final', lambda: gate.command('gradle-stop-final', ['./gradlew', '--stop'], seconds=60, cleaning=True))
        final_children = gate.drain('after-final-stop')
        final_containers = gate.attempt('final-container-census', lambda: not gate.census('containers-final')) if gate.clean_daemon else False
        gate.result['final_children_absent'] = final_children
        gate.result['final_containers_absent'] = final_containers
        if final_containers is not True or not containers_gone:
            gate.result['containers'] = 'UNKNOWN'
        after_commands = gate.drain('before-home-cleanup')
        home_safe = files_safe and final_children and final_containers is True and after_commands
        if home_safe:
            for name in ('gradle', 'tmp', 'home'):
                gate.attempt('private-home-cleanup', lambda p=name: remove_owned(gate.run, p))
        gate.result['outputs_absent'] = gate.attempt('output-absence', lambda: (
            not any((gate.run / n).exists() for n in ('gradle', 'tmp', 'home', 'w01', 'project-cache', 'kotlin-cache'))
            and not any(safe(BACKEND, p).exists() for p in CACHE_PATHS))) is True
        gate.result['cancelled'] = gate.cancelled
        gate.result['retained_file_hashes'] = {}
        def inventory():
            def scan_error(error):
                gate.result['retained_inventory_error'] = {'path': error.filename, 'error': type(error).__name__}
                raise error
            for folder, directories, files in os.walk(gate.reports, followlinks=False, onerror=scan_error):
                for name in directories + files:
                    path = Path(folder) / name
                    if path == gate.reports / 'result.json':
                        continue
                    relative = str(path.relative_to(gate.reports))
                    row = {'bytes': None, 'sha256': None, 'error': None}
                    gate.result['retained_file_hashes'][relative] = row
                    try:
                        row['bytes'] = path.lstat().st_size
                        require(not path.is_symlink(), 'Retained evidence link')
                        if path.is_dir():
                            del gate.result['retained_file_hashes'][relative]
                            continue
                        row['sha256'] = digest(path, 64 * 1024**2)
                    except BaseException as error:
                        row['error'] = type(error).__name__
                        gate.fail('retained-file:' + relative, error)
            return all(row['error'] is None for row in gate.result['retained_file_hashes'].values())
        gate.result['retained_inventory_complete'] = gate.attempt('retained-file-inventory', inventory) is True
        gate.result['elapsed_seconds'] = time.monotonic() - gate.start
        passed = (not gate.result['failures'] and not gate.cancelled and gate.result['elapsed_seconds'] < 1200
                  and gate.result['outputs_absent'] and gate.result['retained_inventory_complete'] and gate.result.get('inputs_preserved') is True
                  and gate.result.get('consumer', {}).get('status') == 'PASS' and gate.result['containers'] == 'NORMAL_ABSENT'
                  and all(r['outcome'] == 'NORMAL' for r in gate.result['commands']) and final_containers is True)
        gate.result['status'] = 'PASS' if passed else 'FAIL'
        gate.result['limitation'] = 'One hosted final-JAR ordinary JDBC/SCRAM consumer only; W03/core/native qualification remains open.'
        save(gate.reports / 'result.json', gate.result)
    return 0 if gate.result['status'] == 'PASS' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit-target', action='store_true')
    args = parser.parse_args()
    binding = request()
    if args.emit_target:
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
            output.write('public_prerequisite_sha=' + binding['source_bundle']['public_prerequisite_sha'] + '\n')
        return 0
    return execute(binding)


if __name__ == '__main__':
    raise SystemExit(main())
