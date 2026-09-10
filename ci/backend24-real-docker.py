"""One private, disposable Web-only real-Docker gate. No product build, SSH or retry."""

import argparse
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

CONTROL = Path(__file__).resolve().parents[1]
BACKEND = CONTROL.parent / 'backend'
AUTHORIZATION = 'BACKEND24_ONE_REAL_DOCKER_GATE_AUTHORIZED'
SOURCE_HASHES = {
    'deploy/server3/kira-deploy': 'fa0fbbff16e6bf4067de55ea6add651d7860c7e665708efbb6f61c34d6695f17',
    'scripts/ci/image_release.py': 'c9492de4168fcdcddd1c1856ab54a78c8d1bc43771259a34c7a80fada2016c18',
}
OWNED_CHILDREN_SHA256 = '56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385'
BASE = 'docker.io/library/busybox@sha256:29989570aeecad61a019f684218ea74d4b8c1c74f9e0abeb34ca926b81174ee1'
BASE_ID = 'sha256:cafb65f54bc46b59c4915955dc3c1e89e0a4ceab9f42a998e58a173f191d04ff'
SYNTHETIC_SHA = '2424242424242424242424242424242424242424'
TAG = 'kira-web:' + SYNTHETIC_SHA
LABEL = 'me.kira.backend24-gate-owner'
ROOT = Path('/opt/kira')
RECEIVER = Path('/usr/local/sbin/kira-deploy')
HELPER = Path('/usr/local/libexec/kira-image-release.py')
LOCK = Path('/run/lock/kira-deploy.lock')
MAX_TAR = 32 * 1024 * 1024
MAX_GZIP = 8 * 1024 * 1024
CANCELLED = False


class GateFailure(Exception):
    pass


def require(value, message):
    if not value:
        raise GateFailure(message)


def regular_bytes(path, maximum=128 * 1024):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_size <= maximum, 'Nonregular or oversized bound file')
    return path.read_bytes()


def digest(path, maximum=128 * 1024):
    return hashlib.sha256(regular_bytes(path, maximum)).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(regular_bytes(path, 4 * 1024 * 1024), object_pairs_hook=unique)


def write_json(path, value, public=False):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    require(len(raw) <= 128 * 1024, 'Compact receipt limit exceeded')
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    try:
        temporary.chmod(0o644 if public else 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def request():
    """Fail before root fixture creation, helper import, Docker, or checkout outputs."""
    value = read_json(CONTROL / 'ci/backend24-real-docker.request.json')
    require(set(value) == {'schema', 'authorization', 'backendSha', 'sourceSha256', 'base',
                           'syntheticSha', 'scriptSha256', 'workflowSha256', 'checkpointSha256',
                           'ownedChildrenSha256'},
            'Unexpected request fields')
    require(value['schema'] == 'backend24-one-real-docker-v1' and
            value['authorization'] == AUTHORIZATION, 'Draft is not authorized for execution')
    require(re.fullmatch(r'[0-9a-f]{40}', value['backendSha']) and value['backendSha'] != '0' * 40,
            'Primary must bind the reconciled accepted source commit')
    require(value['sourceSha256'] == SOURCE_HASHES and value['base'] == BASE and
            value['syntheticSha'] == SYNTHETIC_SHA, 'Reviewed source/base/fixture bindings changed')
    require(value['scriptSha256'] == digest(Path(__file__)) and value['workflowSha256'] ==
            digest(CONTROL / '.github/workflows/backend24-real-docker.yml'), 'Carrier bytes changed')
    require(value['ownedChildrenSha256'] == OWNED_CHILDREN_SHA256 ==
            digest(CONTROL / 'ci/app29_owned_children.py'), 'Reused hosted lifecycle utility changed')
    checkpoint = CONTROL / 'ci/backend24-real-docker.checkpoint.json'
    require(value['checkpointSha256'] == digest(checkpoint), 'Checkpoint digest changed')
    checkpoint_value = read_json(checkpoint)
    require(checkpoint_value.get('sourceAccepted') is True and type(checkpoint_value.get('jobMinutes')) is int
            and type(checkpoint_value.get('runAttempts')) is int, 'Invalid checkpoint acceptance/limit types')
    require(checkpoint_value == {
        'schema': 'backend24-real-docker-checkpoint-v1', 'authorization': AUTHORIZATION,
        'sourceAccepted': True, 'backendSha': value['backendSha'], 'sourceSha256': SOURCE_HASHES,
        'base': BASE, 'syntheticSha': SYNTHETIC_SHA, 'jobMinutes': 10, 'runAttempts': 1,
    }, 'Primary source acceptance and separate one-run checkpoint are required')
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin' and
            os.environ.get('GITHUB_REF') == 'refs/heads/remediation/app-29-backend-complaints' and
            os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1',
            'Wrong private carrier event or prohibited rerun')
    require(os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted' and
            os.environ.get('RUNNER_OS') == 'Linux' and os.environ.get('RUNNER_ARCH') == 'X64',
            'Dedicated hosted Linux x64 runner required')
    event = read_json(Path(os.environ['GITHUB_EVENT_PATH']))
    require(event.get('repository', {}).get('private') is True and
            event['repository'].get('full_name') == 'kira-manga/kira-admin', 'Private repository required')
    require(re.fullmatch(r'[1-9][0-9]{0,15}', os.environ.get('GITHUB_RUN_ID', '')) and
            re.fullmatch(r'[0-9a-f]{40}', os.environ.get('GITHUB_SHA', '')), 'Invalid hosted identities')
    return value


def interrupted(_signum, _frame):
    global CANCELLED
    CANCELLED = True  # No exception in Popen construction or finite cleanup; never qualifies as PASS.


class Gate:
    def __init__(self, binding, cleaning):
        require(os.geteuid() == 0 and sys.platform == 'linux', 'Disposable hosted root required')
        self.binding = binding
        self.owner = os.environ['GITHUB_RUN_ID'] + '-1'
        temporary = Path(os.environ['RUNNER_TEMP'])
        require(temporary.is_absolute() and temporary.resolve() == temporary, 'Unsafe runner temp')
        self.path = temporary / ('backend24-real-docker-' + self.owner)
        self.work = self.path / 'scratch'
        self.report = self.path / 'reports/result.json'
        self.deadline = time.monotonic() + 240
        self.cleaning = cleaning
        self.lease = {'owner': self.owner, 'carrierSha': os.environ['GITHUB_SHA'], 'paths': {},
                      'fixedPathsArmed': False, 'newLibexec': False, 'dockerArmed': False, 'baseOwned': False}
        if cleaning:
            require(self.path.is_dir() and not self.path.is_symlink(), 'Missing owned run directory')
            self.lease = read_json(self.path / 'owner.json')
            require(self.lease['owner'] == self.owner and self.lease['carrierSha'] == os.environ['GITHUB_SHA'],
                    'Wrong cleanup owner')
            self.result = read_json(self.report) if self.report.exists() else {'status': 'FAIL'}
        else:
            self.path.mkdir(mode=0o755)  # Exclusive creation; uploader can read compact reports, not scratch.
            self.path.chmod(0o755)
            self.work.mkdir(mode=0o700)
            (self.path / 'reports').mkdir(mode=0o755)
            (self.path / 'reports').chmod(0o755)
            self.result = {'status': 'FAIL', 'backendSha': binding['backendSha'],
                           'carrierSha': os.environ['GITHUB_SHA'], 'sourceSha256': SOURCE_HASHES,
                           'base': BASE, 'syntheticSha': SYNTHETIC_SHA, 'checksPassed': False,
                           'lifecycleNormal': True, 'ownedChildrenSha256': OWNED_CHILDREN_SHA256}
            self.save_lease()  # Pre-armed intent exists before any privileged fixture or daemon mutation.
            self.save()
        self.work.mkdir(mode=0o700, exist_ok=True)
        (self.work / 'home').mkdir(mode=0o700, exist_ok=True)
        os.environ['HOME'] = str(self.work / 'home')
        os.environ['TMPDIR'] = str(self.work)
        os.environ['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        # Reuse R2's byte-identical command lifecycle, including single-owner WNOWAIT/group-absence checks.
        for relative, expected in SOURCE_HASHES.items():
            require(digest(BACKEND / relative) == expected, 'Reviewed Backend bytes changed')
        spec = importlib.util.spec_from_file_location('backend24_bound_helper', BACKEND / 'scripts/ci/image_release.py')
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)  # No CLI, producer, API or network function is called on import.
        owner_spec = importlib.util.spec_from_file_location('backend24_owned_children', CONTROL / 'ci/app29_owned_children.py')
        owner_module = importlib.util.module_from_spec(owner_spec)
        owner_spec.loader.exec_module(owner_module)
        # Existing Admin utility, unchanged: adopt any timeout/plugin descendants outside the command's PGID.
        # Drain only AFTER helper.command() returns/raises, never concurrently with its single wait owner.
        self.children = owner_module.OwnedChildren()

    def save_lease(self):
        write_json(self.path / 'owner.json', self.lease)

    def save(self):
        write_json(self.report, self.result, public=True)

    def command(self, name, argv, seconds=10, expected=0, stdin=None, output=None, maximum=256 * 1024):
        require(self.cleaning or not CANCELLED, 'Gate cancelled')
        budget = min(seconds, self.deadline - time.monotonic() - 12)  # R2's four + existing drain's eight.
        require(budget > 0, 'Gate phase deadline expired')
        captured = io.BytesIO() if output is None else output
        entry = {'check': name, 'exit': None, 'ownedCommandCompleted': False}
        self.result.setdefault('commands', []).append(entry)
        started = time.monotonic()
        try:
            code = self.helper.command(argv, seconds=budget, stdin=subprocess.DEVNULL if stdin is None else stdin, output=captured,
                                       maximum=maximum, return_status=True)
            entry.update(exit=code, ownedCommandCompleted=True)
            require(expected is None or code == expected, 'Unexpected command exit: ' + name)
            require(self.cleaning or not CANCELLED, 'Gate cancelled')
            return code, captured.getvalue() if output is None else b''
        finally:
            joined = self.children.drain()
            normal = joined['ok'] and not joined['term'] and not joined['kill']
            self.result['lifecycleNormal'] = self.result.get('lifecycleNormal', True) and normal
            entry.update(ownedChildrenAbsent=joined['ok'], forcedChildSignals=len(joined['term']) + len(joined['kill']))
            entry['seconds'] = round(time.monotonic() - started, 3)
            self.save()  # Only fixed names/exits; never argv, environment, stdout/stderr, or raw logs.
            require(joined['ok'] and (self.cleaning or normal), 'Owned command descendants did not finish normally')

    def text(self, name, argv, **kwargs):
        return self.command(name, argv, **kwargs)[1].decode('ascii').strip()

    def docker_ids(self, kind, owned=False):
        arguments = ['docker', kind, 'ls', '--all', '--quiet', '--no-trunc']
        if owned:
            arguments += ['--filter', 'label=' + LABEL + '=' + self.owner]
        identities = set(self.text(('owned-' if owned else 'all-') + kind + '-ids', arguments).split())
        pattern = r'sha256:[0-9a-f]{64}' if kind == 'image' else r'[0-9a-f]{64}'
        require(len(identities) <= 64 and all(re.fullmatch(pattern, x) for x in identities),
                'Invalid or excessive fixture inventory')
        return identities

    def image(self, reference):
        value = self.text('image-id', ['docker', 'image', 'inspect', '--format', '{{.Id}}', reference])
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', value), 'Invalid full image identity')
        return value

    def claim(self, path):
        info = path.lstat()
        require(info.st_uid == 0 and not stat.S_ISLNK(info.st_mode), 'Unexpected fixture owner')
        self.lease['paths'][str(path)] = [info.st_dev, info.st_ino]
        self.save_lease()

    def install(self, path, raw, mode=0o600):
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(mode)
        self.claim(path)

    def preflight(self):
        release = Path('/etc/os-release').read_text()
        require('\nID=ubuntu\n' in '\n' + release and '\nVERSION_ID="24.04"\n' in '\n' + release,
                'Ubuntu 24.04 is required')
        for name in ('docker', 'git', 'gzip', 'bash', 'timeout', 'flock', 'awk', 'stat', 'mktemp',
                     'install', 'grep', 'ln', 'cmp', 'mv', 'rm', 'chmod', 'sleep'):
            require(shutil.which(name) is not None, 'Required installed tool is absent')
        socket = Path('/run/docker.sock').lstat()
        require(Path('/usr/bin/python3').is_file() and stat.S_ISSOCK(socket.st_mode) and socket.st_uid == 0
                and Path('/var/run/docker.sock').resolve() == Path('/run/docker.sock'),
                'Default local Docker socket is required')
        for parent in (ROOT.parent, RECEIVER.parent, HELPER.parent.parent):
            info = parent.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
                    and parent.resolve() == parent, 'Unsafe fixed installation parent')
        if HELPER.parent.exists():
            info = HELPER.parent.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
                    'Unsafe preexisting libexec directory')
        lock_parent = LOCK.parent.lstat()
        require(stat.S_ISDIR(lock_parent.st_mode) and lock_parent.st_uid == 0 and
                (not lock_parent.st_mode & 0o022 or lock_parent.st_mode & stat.S_ISVTX), 'Unsafe lock directory')
        for name, checkout, expected in (('carrier', CONTROL, os.environ['GITHUB_SHA']),
                                          ('backend', BACKEND, self.binding['backendSha'])):
            git = ['git', '-c', 'safe.directory=' + str(checkout), '-C', str(checkout)]
            require(self.text(name + '-commit', git + ['rev-parse', 'HEAD']) == expected and
                    not self.text(name + '-clean', git + ['status', '--porcelain']), 'Checkout identity/cleanliness changed')
        for path in (ROOT, RECEIVER, HELPER, LOCK):
            require(not os.path.lexists(path), 'Preexisting fixed fixture path; no changes authorized')
        self.lease['fixedPathsArmed'] = True
        self.lease['newLibexec'] = not os.path.lexists(HELPER.parent)
        self.save_lease()
        require(not self.docker_ids('container'), 'Preexisting containers; isolated hosted daemon required')
        initial_images = self.docker_ids('image')
        require(BASE_ID not in initial_images and not self.docker_ids('image', owned=True),
                'Preexisting base/fixture identity; do not adopt or remove it')
        require(not self.text('preexisting-web-tags', ['docker', 'image', 'ls', '--quiet', '--filter',
                                                     'reference=kira-web:*']), 'Preexisting Web image tags')
        for kind in ('network', 'volume'):
            require(not self.text('preexisting-kira-' + kind, ['docker', kind, 'ls', '--quiet', '--filter',
                                 'label=com.docker.compose.project=kira']), 'Preexisting Kira Compose resources')
        docker = self.text('docker-version', ['docker', 'version', '--format', '{{.Client.Version}} {{.Server.Version}}'])
        compose = self.text('compose-version', ['docker', 'compose', 'version', '--short'])
        require(re.fullmatch(r'[0-9A-Za-z.+_-]+ [0-9A-Za-z.+_-]+', docker) and
                re.fullmatch(r'v?[0-9][0-9A-Za-z.+_-]*', compose), 'Required Docker/Compose versions unavailable')
        require(self.text('docker-context', ['docker', 'context', 'show']) == 'default', 'Unexpected Docker context')
        require(shutil.disk_usage(self.work).free >= 128 * 1024 * 1024, 'Insufficient bounded scratch space')
        self.result['versions'] = {'dockerClientServer': docker, 'compose': compose}
        self.lease['dockerArmed'] = True
        self.save_lease()

    def fixture(self):
        ROOT.mkdir(mode=0o700)
        self.claim(ROOT)
        if not HELPER.parent.exists():
            HELPER.parent.mkdir(mode=0o755)
            self.claim(HELPER.parent)
        require(HELPER.parent.is_dir() and not HELPER.parent.is_symlink(), 'Unsafe helper parent')
        self.install(LOCK, b'')
        self.install(RECEIVER, regular_bytes(BACKEND / 'deploy/server3/kira-deploy'), 0o755)
        self.install(HELPER, regular_bytes(BACKEND / 'scripts/ci/image_release.py'))
        require(digest(RECEIVER) == SOURCE_HASHES['deploy/server3/kira-deploy'] and
                digest(HELPER) == SOURCE_HASHES['scripts/ci/image_release.py'], 'Installed bytes differ')
        self.install(ROOT / 'images.env', ('KIRA_WEB_IMAGE=' + TAG + '\n').encode())
        self.install(ROOT / 'ingress.env', b'')
        compose = ('services:\n  web:\n    image: ${KIRA_WEB_IMAGE:?required}\n'
                   '    container_name: kira-web\n    network_mode: none\n    pull_policy: never\n'
                   '    read_only: true\n    user: "65534:65534"\n    cap_drop: [ALL]\n'
                   '    security_opt: [no-new-privileges:true]\n    pids_limit: 16\n'
                   '    mem_limit: 32m\n    cpus: 0.25\n    restart: "no"\n'
                   '    logging:\n      driver: none\n    labels:\n      ' + LABEL + ': "' + self.owner + '"\n')
        self.install(ROOT / 'compose.yaml', compose.encode())

    def build_export(self, variant):
        context = self.work / variant
        context.mkdir(mode=0o700)
        dockerfile = ('FROM ' + BASE + '\nLABEL ' + LABEL + '="' + self.owner + '"\n'
                      'LABEL org.opencontainers.image.revision="' + SYNTHETIC_SHA + '"\n'
                      'COPY health /fixture-health\nUSER 65534:65534\n'
                      'HEALTHCHECK --interval=1s --timeout=1s --retries=1 CMD ["/bin/sh", "/fixture-health"]\n'
                      'CMD ["/bin/sleep", "600"]\n')
        (context / 'Dockerfile').write_text(dockerfile)
        (context / 'health').write_text('exit ' + ('0' if variant == 'A' else '1') + '\n')
        (context / 'health').chmod(0o444)  # COPY preserves mode; nonroot health checks must be able to read it.
        self.command('build-' + variant, ['docker', 'build', '--platform', 'linux/amd64', '--pull=false',
                     '--no-cache', '--network', 'none', '--quiet', '--tag', TAG, str(context)], seconds=45)
        identity = self.image(TAG)
        require(identity in self.docker_ids('image', owned=True), 'Built image is not labeled as owned')
        plain, archive = self.work / (variant + '.tar'), self.work / (variant + '.tar.gz')
        with plain.open('xb') as target:
            self.command('export-' + variant, ['docker', 'save', TAG], seconds=20, output=target, maximum=MAX_TAR)
        expanded = self.helper.file_identity(plain, MAX_TAR)
        with archive.open('xb') as target:
            self.command('gzip-' + variant, ['gzip', '--no-name', '--stdout', str(plain)],
                         seconds=10, output=target, maximum=MAX_GZIP)
        compressed = self.helper.file_identity(archive, MAX_GZIP)
        plain.unlink()
        expected = identity + ' ' + compressed['sha256']
        require(self.text('archive-' + variant, ['/usr/bin/python3', '-I', '-B', str(HELPER), 'archive',
                     'web', SYNTHETIC_SHA, str(archive), compressed['sha256'], identity], seconds=15) == expected,
                'Actual exported archive validation mismatch')
        self.result.setdefault('images', {})[variant] = {
            'imageId': identity, 'archive': compressed, 'expandedArchive': expanded, 'archiveValidated': True,
        }
        self.save()
        return identity, archive, compressed['sha256']

    def snapshot(self, identity, archive_digest):
        model = '{{.Id}} {{.Image}} {{.State.Running}} {{.State.Health.Status}} ' + \
                '{{index .Config.Labels "com.docker.compose.project"}} ' + \
                '{{index .Config.Labels "com.docker.compose.service"}} {{index .Config.Labels "' + LABEL + '"}}'
        fields = self.text('runtime-health-identity', ['docker', 'container', 'inspect', '--format', model, 'kira-web']).split()
        require(len(fields) == 7 and re.fullmatch(r'[0-9a-f]{64}', fields[0]) and
                fields[1:] == [identity, 'true', 'healthy', 'kira', 'web', self.owner], 'Wrong immutable owned healthy runtime')
        require(regular_bytes(ROOT / 'images.env') == ('KIRA_WEB_IMAGE=' + identity + '\n').encode(),
                'Persisted target is not the actual immutable image')
        require({path.name for path in ROOT.iterdir()} == {'compose.yaml', 'images.env', 'ingress.env', 'releases'},
                'Unexpected Web-only fixture state or temporary persistence file remains')
        releases = ROOT / 'releases/web'
        activation = ('active ' + SYNTHETIC_SHA + ' ' + identity + ' ' + archive_digest + '\nprevious - - -\n').encode()
        require(regular_bytes(releases / 'activation') == activation, 'Activation record did not preserve A')
        require({path.name for path in releases.iterdir()} == {'activation', archive_digest + '.tar.gz'},
                'Unexpected archive, pending marker or incoming scratch remains')
        archive = releases / (archive_digest + '.tar.gz')
        require(digest(archive, MAX_GZIP) == archive_digest, 'Retained A archive bytes changed')
        return {'containerId': fields[0], 'imageId': identity, 'health': 'healthy', 'persistedImageId': identity,
                'activationSha256': digest(releases / 'activation'), 'retainedArchiveSha256': archive_digest,
                'archiveInode': archive.stat().st_ino, 'pendingAndIncomingAbsent': True}

    def deploy(self, variant, archive, expected):
        with archive.open('rb') as stream:
            return self.command('deploy-' + variant, [str(RECEIVER), 'deploy', 'web', SYNTHETIC_SHA],
                                seconds=65, stdin=stream, expected=expected)[0]

    def exercise(self):
        self.preflight()
        self.fixture()
        self.lease['baseOwned'] = True  # Absence already proved; intent precedes the one pinned pull.
        self.save_lease()
        self.command('pull-pinned-base-once', ['docker', 'pull', '--platform', 'linux/amd64', BASE], seconds=45)
        require(self.image(BASE) == BASE_ID, 'Pinned base config/platform identity changed')
        a_id, a_archive, a_digest = self.build_export('A')
        b_id, b_archive, b_digest = self.build_export('B')
        require(a_id != b_id and a_digest != b_digest and self.image(TAG) == b_id, 'Fixture A/B identities not distinct')
        owned = self.docker_ids('image', owned=True)
        require({a_id, b_id} <= owned, 'Fixture image ownership unavailable before first load')
        self.command('remove-exported-fixture-identities', ['docker', 'image', 'rm', '--force', *sorted(owned)], seconds=15)
        require(not self.docker_ids('image', owned=True) and not ({a_id, b_id} & self.docker_ids('image')),
                'Daemon fixture identities remain before archive loading')
        self.result['beforeFirstLoad'] = {'fixtureImageIdsAbsent': [a_id, b_id], 'containersAbsent': not self.docker_ids('container')}
        require(self.result['beforeFirstLoad']['containersAbsent'], 'A container appeared before initial load')
        self.result['activationAExit'] = self.deploy('A', a_archive, 0)
        first = self.snapshot(a_id, a_digest)
        require(self.image(TAG) == a_id, 'Initial A tag did not load from the archive')
        self.result['activationA'] = first
        since = str(int(time.time()) - 1)
        self.result['failedBExit'] = self.deploy('B', b_archive, 71)
        restored = self.snapshot(a_id, a_digest)
        require(self.image(TAG) == b_id and restored['containerId'] != first['containerId'] and
                restored['activationSha256'] == first['activationSha256'] and
                restored['archiveInode'] == first['archiveInode'], 'B overwrite or immutable A restoration/retention not proved')
        # Historical events avoid an unowned background monitor and survive B's removal by rollback.
        events = self.text('bounded-B-health-events', ['docker', 'events', '--since', since,
                     '--until', str(int(time.time()) + 1), '--filter', 'type=container', '--filter',
                     'label=' + LABEL + '=' + self.owner, '--format', '{{json .}}'], seconds=5)
        unhealthy = []
        for line in events.splitlines():
            event = json.loads(line)
            actor = event.get('Actor', {})
            attrs = actor.get('Attributes', {})
            if event.get('Action') == 'health_status: unhealthy' and attrs.get('image') == b_id:
                require(re.fullmatch(r'[0-9a-f]{64}', actor.get('ID', '')) and
                        attrs.get(LABEL) == self.owner and attrs.get('com.docker.compose.project') == 'kira'
                        and attrs.get('com.docker.compose.service') == 'web', 'Wrong B health event ownership')
                unhealthy.append(actor['ID'])
        require(len(set(unhealthy)) == 1, 'Deterministic unhealthy B was not observed')
        self.result['failedB'] = {'candidateImageId': b_id, 'candidateContainerId': unhealthy[0],
                                 'candidateHealth': 'unhealthy', 'tagImageAfterRollback': b_id,
                                 'restoredA': restored, 'BArchiveNotRetained': True}
        self.result['identicalAExit'] = self.deploy('identical-A', a_archive, 0)
        repeat = self.snapshot(a_id, a_digest)
        require(repeat == restored and self.image(TAG) == b_id, 'Identical A was not a retaining no-op')
        self.result['identicalA'] = {'unchangedRuntimeAndRecord': True, 'unchangedArchiveInode': True,
                                     'tagStillB': True, 'receiverExit': 0}
        for relative, expected in SOURCE_HASHES.items():
            require(digest(BACKEND / relative) == expected, 'Source changed during the gate')
        require(digest(RECEIVER) == SOURCE_HASHES['deploy/server3/kira-deploy'] and
                digest(HELPER) == SOURCE_HASHES['scripts/ci/image_release.py'], 'Installed source changed')
        for name, checkout in (('carrier', CONTROL), ('backend', BACKEND)):
            require(not self.text(name + '-still-clean', ['git', '-c', 'safe.directory=' + str(checkout),
                         '-C', str(checkout), 'status', '--porcelain']), 'Checkout changed during the gate')
        require(not CANCELLED, 'Gate cancelled')
        self.result['checksPassed'] = True

    def cleanup(self):
        self.cleaning, self.deadline = True, time.monotonic() + 45
        receipt = {'containersAbsent': False, 'fixtureImageIdsAbsent': False,
                   'composeNetworksVolumesAbsent': False, 'ownedPathsAbsent': False,
                   'scratchAbsent': False, 'ok': False}
        self.result.setdefault('cleanup', []).append(receipt)
        lock = None
        try:
            # Hold the inherited receiver lock THROUGH cleanup, not merely an earlier absence observation.
            if str(LOCK) in self.lease['paths'] and os.path.lexists(LOCK):
                info = LOCK.lstat()
                require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and
                        [info.st_dev, info.st_ino] == self.lease['paths'][str(LOCK)], 'Wrong receiver lock owner')
                lock = LOCK.open('rb')
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.lease['dockerArmed']:
                owned = self.docker_ids('container', owned=True)
                if owned:
                    self.command('remove-owned-containers', ['docker', 'container', 'rm', '--force', *sorted(owned)], seconds=8)
                require(not self.docker_ids('container', owned=True) and not self.docker_ids('container'),
                        'Owned or unexpected containers remain; do not remove unowned containers')
                receipt['containersAbsent'] = True
                images = self.docker_ids('image', owned=True)
                if images:
                    self.command('remove-owned-images', ['docker', 'image', 'rm', '--force', *sorted(images)], seconds=8)
                if self.lease['baseOwned'] and BASE_ID in self.docker_ids('image'):
                    self.command('remove-owned-base', ['docker', 'image', 'rm', '--force', BASE_ID], seconds=8)
                require(not self.docker_ids('image', owned=True) and
                        (not self.lease['baseOwned'] or BASE_ID not in self.docker_ids('image')), 'Owned image identities remain')
                receipt['fixtureImageIdsAbsent'] = True
                for kind in ('network', 'volume'):
                    require(not self.text('final-kira-' + kind, ['docker', kind, 'ls', '--quiet', '--filter',
                                 'label=com.docker.compose.project=kira']), 'Unexpected Kira Compose resource remains')
                receipt['composeNetworksVolumesAbsent'] = True
            else:
                receipt.update(containersAbsent=None, fixtureImageIdsAbsent=None, composeNetworksVolumesAbsent=None)
            for name, identity in sorted(self.lease['paths'].items(), key=lambda item: len(item[0]), reverse=True):
                path = Path(name)
                if not os.path.lexists(path):
                    continue
                # Child files under the exclusively owned /opt/kira may be atomically replaced by the receiver.
                if ROOT in path.parents:
                    continue
                info = path.lstat()
                require([info.st_dev, info.st_ino] == identity and info.st_uid == 0 and
                        not stat.S_ISLNK(info.st_mode), 'Owned cleanup path identity changed')
                if path == ROOT:
                    shutil.rmtree(path)
                elif stat.S_ISDIR(info.st_mode):
                    path.rmdir()  # Only a directory this gate created, and only if empty.
                else:
                    path.unlink()
            require(not any(os.path.lexists(name) for name in self.lease['paths']), 'Owned paths remain')
            if self.lease['fixedPathsArmed']:
                require(not any(os.path.lexists(path) for path in (ROOT, RECEIVER, HELPER, LOCK)) and
                        (not self.lease['newLibexec'] or not os.path.lexists(HELPER.parent)),
                        'Unrecorded fixture path remains; do not delete without owned identity')
            receipt['ownedPathsAbsent'] = True
            shutil.rmtree(self.work)
            receipt['scratchAbsent'] = not self.work.exists()
            receipt['ok'] = receipt['scratchAbsent']
        except Exception as failure:
            receipt['failureClass'] = type(failure).__name__  # Never arbitrary exception text.
        finally:
            if lock is not None:
                lock.close()
        self.save()
        return receipt['ok']


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check-request', action='store_true')
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    binding = request()
    if args.check_request:
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
            output.write('backend_sha=' + binding['backendSha'] + '\n')
        return 0
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    gate = Gate(binding, args.cleanup)
    if args.cleanup:
        previous = gate.result.get('status') == 'CHECKS_PASSED_PENDING_FINAL_CLEANUP'
        ok = gate.cleanup()
        passed = (previous and os.environ.get('BACKEND24_VALIDATION_OUTCOME') == 'success' and
                  gate.result.get('checksPassed') and gate.result.get('firstCleanup') and
                  gate.result.get('lifecycleNormal') and
                  not gate.result.get('cancelled') and ok and not CANCELLED)
        gate.result['status'] = 'PASS' if passed else 'FAIL'
        gate.save()
        print('Backend24 tiny receiver gate: ' + gate.result['status'])
        return 0 if passed else 1
    try:
        gate.exercise()
    except Exception as failure:
        gate.result['failureClass'] = type(failure).__name__
        if isinstance(failure, GateFailure):
            gate.result['failure'] = str(failure)  # Only fixed harness diagnostics, not subprocess output.
    finally:
        gate.result['firstCleanup'] = gate.cleanup()
        gate.result['cancelled'] = CANCELLED
        passed = (gate.result['checksPassed'] and gate.result['firstCleanup'] and
                  gate.result['lifecycleNormal'] and not CANCELLED)
        gate.result['status'] = 'CHECKS_PASSED_PENDING_FINAL_CLEANUP' if passed else 'FAIL'
        gate.save()
    return 0 if passed else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as failure:
        print('Backend24 gate refused (' + type(failure).__name__ + '); no success claim')
        raise SystemExit(1)
