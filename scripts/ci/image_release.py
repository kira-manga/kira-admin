#!/usr/bin/env python3
"""Linux/GitHub-only exact-image release helper. Standard library; no candidate code execution."""

import argparse
import base64
import contextlib
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

REPOSITORY = 'kira-manga/kira-admin'
CI = '.github/workflows/ci.yml'
PROMOTION = '.github/workflows/deploy-server3.yml'
CONTRACT_FILES = (CI, PROMOTION, 'scripts/ci/image_release.py', 'scripts/ci/test_image_release.py',
                  'scripts/ci/grype.yaml', 'Dockerfile', '.dockerignore', 'package.json', 'package-lock.json')
ROOT = Path(__file__).resolve().parents[2]
MAX_IMAGE = 512 * 1024 * 1024
MAX_TAR = 2 * 1024 * 1024 * 1024
MAX_RECEIPT = 16 * 1024
MAX_SCAN = 8 * 1024 * 1024
FILES = {'image.tar.gz': MAX_IMAGE, 'receipt.json': MAX_RECEIPT, 'scan.json': MAX_SCAN}
GRYPE_VERSION = '0.118.0'
GRYPE_SHA = '1d444c5e7360471815f7158f71935fcecc68a3c417d85c7344f770854300bba2'
GRYPE_DB_URL = 'https://grype.anchore.io/databases/v6/latest.json'
SCAN_POLICY = 'grype-high-critical-including-unfixed-v1'
MAX_DB_AGE = 120 * 60 * 60
GITHUB_ACTIONS_APP_ID = 15368
MAX_DIAGNOSTIC_ENTRIES = 4
MAX_DIAGNOSTIC_FRAMES = 4
MAX_DIAGNOSTIC_TRACE = 64
MAX_DIAGNOSTIC_LINE = 999999
MAX_DIAGNOSTIC_BYTES = 2048


class Refused(Exception):
    """Only fixed, non-sensitive diagnostics leave this process."""


def need(condition, message):
    if not condition:
        raise Refused(message)


def integer(value):
    need(type(value) is int and 0 < value <= 2**53 - 1, 'invalid numeric identity')
    return value


def number_input(value):
    need(isinstance(value, str) and re.fullmatch(r'[1-9][0-9]{0,15}', value), 'invalid numeric input')
    return integer(int(value))


def hex_value(value, length=64):
    need(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{' + str(length) + '}', value), 'invalid digest identity')
    return value


def image_id(value):
    need(isinstance(value, str) and value.startswith('sha256:'), 'invalid image identity')
    hex_value(value[7:])
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_json(data, maximum):
    need(len(data) <= maximum, 'JSON exceeds its byte limit')

    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON field')
            result[key] = value
        return result

    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Refused('invalid JSON number')))
    except (ValueError, UnicodeError):
        raise Refused('invalid JSON document') from None


def keys(value, expected):
    need(type(value) is dict and set(value) == set(expected.split()), 'unexpected receipt fields')


def timestamp(value):
    need(isinstance(value, str) and len(value) <= 40, 'invalid timestamp')
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise Refused('invalid timestamp') from None
    need(parsed.tzinfo is not None, 'timestamp has no timezone')
    return parsed.timestamp()


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def file_bytes(path, maximum):
    need(path.is_file() and stat.S_ISREG(path.lstat().st_mode) and path.stat().st_size <= maximum,
         'missing, nonregular or oversized file')
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    need(len(data) <= maximum, 'file exceeds its byte limit')
    return data


def copy_bounded(source, target, maximum):
    size, checksum = 0, hashlib.sha256()
    while chunk := source.read(65536):
        size += len(chunk)
        need(size <= maximum, 'stream exceeds its byte limit')
        checksum.update(chunk)
        if target is not None:
            target.write(chunk)
    return {'bytes': size, 'sha256': checksum.hexdigest()}


def file_identity(path, maximum):
    need(stat.S_ISREG(path.lstat().st_mode), 'nonregular archive')
    with path.open('rb') as stream:
        return copy_bounded(stream, None, maximum)


@contextlib.contextmanager
def deadline(seconds):
    # A whole-operation alarm also bounds slow drips; socket inactivity timeouts alone do not.
    def expired(_signal, _frame):
        raise Refused('network operation timed out')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, _request, _fp, _code, _message, _headers, _url):
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def request(url, token=None):
    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
               'User-Agent': 'kira-admin-exact-image'}
    if token:
        parsed = urllib.parse.urlsplit(url)
        need(parsed.scheme == 'https' and parsed.hostname == 'api.github.com' and parsed.port in (None, 443)
             and not parsed.username and not parsed.password, 'refusing API token forwarding')
        headers['Authorization'] = 'Bearer ' + token
    return urllib.request.Request(url, headers=headers)


class GitHub:
    def __init__(self, token):
        need(isinstance(token, str) and bool(token), 'required read-only API credential is missing')
        self.token = token
        self.blobs = {}

    def get(self, suffix):
        need(suffix == '' or suffix.startswith('/'), 'invalid API path')
        with deadline(30), OPENER.open(request('https://api.github.com/repos/' + REPOSITORY + suffix,
                                               self.token), timeout=15) as response:
            need(response.status == 200 and 'rel="next"' not in response.headers.get('Link', ''),
                 'incomplete API response')
            return parse_json(response.read(4 * 1024 * 1024 + 1), 4 * 1024 * 1024)

    def download(self, artifact, destination, expected):
        # Authenticate only the fixed API endpoint. Never store/log the signed storage URL.
        url = f'https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{integer(artifact)}/zip'
        with deadline(180):
            try:
                unexpected = OPENER.open(request(url, self.token), timeout=15)
            except urllib.error.HTTPError as response:
                try:
                    need(response.code == 302, 'artifact download was not available')
                    location = response.headers.get('Location', '')
                finally:
                    response.close()
            else:
                unexpected.close()
                raise Refused('unexpected artifact download response')
            parsed = urllib.parse.urlsplit(location)
            host = parsed.hostname or ''
            need(parsed.scheme == 'https' and parsed.port in (None, 443) and not parsed.username
                 and not parsed.password and not parsed.fragment and
                 (host.endswith('.blob.core.windows.net') or host.endswith('.actions.githubusercontent.com')),
                 'unexpected artifact storage destination')
            # New request, no Authorization header and no automatic second redirect.
            with OPENER.open(request(location), timeout=15) as response, destination.open('xb') as output:
                need(response.status == 200, 'artifact storage refused download')
                actual = copy_bounded(response, output, MAX_IMAGE)
            need(actual == expected, 'outer ZIP digest or size mismatch')

    def contract(self, commit):
        commit = hex_value(commit, 40)
        record = self.get('/git/commits/' + commit)
        need(record.get('sha') == commit, 'Git commit mismatch')
        tree = hex_value(record['tree']['sha'], 40)
        listing = self.get('/git/trees/' + tree + '?recursive=1')
        need(listing.get('sha') == tree and listing.get('truncated') is False, 'incomplete Git tree')
        entries = {item['path']: item for item in listing['tree']}
        need(len(entries) == len(listing['tree']), 'ambiguous Git tree')
        hashes = {}
        for name in CONTRACT_FILES:
            entry = entries.get(name, {})
            need(entry.get('type') == 'blob' and entry.get('mode') in ('100644', '100755'),
                 'contract file is missing or nonregular')
            blob = hex_value(entry.get('sha'), 40)
            if blob not in self.blobs:
                content = self.get('/git/blobs/' + blob)
                need(content.get('sha') == blob and content.get('encoding') == 'base64'
                     and type(content.get('size')) is int and 0 < content['size'] <= 512 * 1024,
                     'invalid contract blob')
                raw = base64.b64decode(content['content'].replace('\n', ''), validate=True)
                need(len(raw) == content['size'], 'contract blob size mismatch')
                self.blobs[blob] = digest(raw)
            hashes[name] = self.blobs[blob]
        return tree, hashes


def local_contract():
    return {name: digest(file_bytes(ROOT / name, 512 * 1024)) for name in CONTRACT_FILES}


def context():
    result = {name: os.environ.get('GITHUB_' + name.upper(), '')
              for name in ('repository', 'repository_id', 'sha', 'workflow_sha', 'workflow_ref',
                           'ref', 'event_name', 'run_id', 'run_attempt', 'job')}
    need(result['repository'] == REPOSITORY, 'wrong repository context')
    for name in ('run_id', 'run_attempt', 'repository_id'):
        result[name] = number_input(result[name])
    hex_value(result['sha'], 40)
    hex_value(result['workflow_sha'], 40)
    return result


def selection():
    return {'run_id': number_input(os.environ.get('CANDIDATE_RUN_ID', '')),
            'run_attempt': number_input(os.environ.get('CANDIDATE_ATTEMPT', '')),
            'artifact_id': number_input(os.environ.get('CANDIDATE_ARTIFACT_ID', '')),
            'zip_sha256': hex_value(os.environ.get('CANDIDATE_ZIP_SHA256', ''))}


def verify_dispatch(ctx, rehearsal=False):
    path = CI if rehearsal else PROMOTION
    need(ctx['repository'] == REPOSITORY and ctx['event_name'] == 'workflow_dispatch' and
         ctx['workflow_ref'] == f"{REPOSITORY}/{path}@{ctx['ref']}", 'manual trusted workflow required')
    need(ctx['workflow_sha'] == ctx['sha'], 'workflow/source revision mismatch')
    need(ctx['ref'].startswith('refs/heads/') if rehearsal else ctx['ref'] == 'refs/heads/main',
         'wrong promotion ref')


def validate_run(run, repo_id, workflow_id, run_id, attempt, event, branch, completed):
    need(run.get('id') == run_id and run.get('run_attempt') == attempt
         and type(run.get('run_attempt')) is int
         and run.get('workflow_id') == workflow_id and run.get('path') == CI
         and run.get('event') == event and run.get('head_branch') == branch, 'producer run identity mismatch')
    for name in ('repository', 'head_repository'):
        repo = run.get(name, {})
        need(repo.get('id') == repo_id and repo.get('full_name') == REPOSITORY, 'fork or wrong producer repository')
    need(run.get('status') == ('completed' if completed else 'in_progress')
         and run.get('conclusion') == ('success' if completed else None), 'producer attempt is not eligible')
    return hex_value(run.get('head_sha'), 40)


def artifact_name(run, attempt):
    return f'admin-image-{integer(run)}-{integer(attempt)}'


def artifact_identity(artifact):
    # List/GET responses may have different URL decoration. Compare the full required binding,
    # not decoration, and never cache mutable artifact/run/policy metadata.
    result = {key: artifact.get(key) for key in ('id', 'name', 'size_in_bytes', 'digest', 'expired', 'expires_at')}
    run = artifact.get('workflow_run', {})
    result['workflow_run'] = {key: run.get(key) for key in
                              ('id', 'repository_id', 'head_repository_id', 'head_sha', 'head_branch')}
    return result


def candidate_metadata(api, ctx, selected, rehearsal=False):
    verify_dispatch(ctx, rehearsal)
    repo = api.get('')
    need(repo.get('id') == ctx['repository_id'] and repo.get('full_name') == REPOSITORY
         and repo.get('private') is True and repo.get('default_branch') == 'main'
         and repo.get('archived') is False and repo.get('disabled') is False, 'repository policy mismatch')
    workflow = api.get('/actions/workflows/ci.yml')
    need(workflow.get('path') == CI and workflow.get('state') == 'active', 'producer workflow is not active')
    workflow_id = integer(workflow.get('id'))
    branch = ctx['ref'][11:] if rehearsal else 'main'
    event = 'workflow_dispatch' if rehearsal else 'push'
    if rehearsal:
        need(selected['run_id'] == ctx['run_id'] and selected['run_attempt'] == ctx['run_attempt'],
             'rehearsal must consume its own immutable producer attempt')
    latest = api.get(f"/actions/runs/{selected['run_id']}")
    attempt = api.get(f"/actions/runs/{selected['run_id']}/attempts/{selected['run_attempt']}")
    sha = validate_run(latest, repo['id'], workflow_id, selected['run_id'], selected['run_attempt'], event, branch, not rehearsal)
    need(validate_run(attempt, repo['id'], workflow_id, selected['run_id'], selected['run_attempt'], event, branch, not rehearsal) == sha,
         'attempt source changed')
    own = api.get(f"/actions/runs/{ctx['run_id']}")
    own_workflow = api.get('/actions/workflows/' + (CI if rehearsal else PROMOTION).split('/')[-1])
    need(own_workflow.get('state') == 'active' and own_workflow.get('path') == (CI if rehearsal else PROMOTION)
         and own.get('workflow_id') == integer(own_workflow.get('id')) and own.get('id') == ctx['run_id']
         and own.get('path') == own_workflow['path'] and own.get('head_sha') == ctx['sha']
         and own.get('run_attempt') == ctx['run_attempt'] and type(own.get('run_attempt')) is int
         and own.get('event') == 'workflow_dispatch' and own.get('head_branch') == ctx['ref'][11:]
         and own.get('status') == 'in_progress' and own.get('conclusion') is None,
         'consumer workflow identity mismatch')
    for name in ('repository', 'head_repository'):
        need(own.get(name, {}).get('id') == repo['id'] and own[name].get('full_name') == REPOSITORY,
             'wrong consumer repository')
    if rehearsal:
        need(sha == ctx['sha'], 'rehearsal source mismatch')
        _, trusted = api.contract(ctx['sha'])
    else:
        main = api.get('/git/ref/heads/main')
        need(main.get('ref') == 'refs/heads/main' and main.get('object', {}).get('type') == 'commit', 'main is not a commit')
        _, trusted = api.contract(main['object']['sha'])
        _, consumer = api.contract(ctx['sha'])
        need(consumer == trusted, 'stale promotion/checker contract')
    need(local_contract() == trusted, 'checkout is not the trusted checker contract')
    tree, producer = api.contract(sha)
    need(producer == trusted, 'stale producer contract')
    listing = api.get(f"/actions/runs/{selected['run_id']}/artifacts?per_page=100")
    artifacts = listing.get('artifacts')
    need(type(artifacts) is list and type(listing.get('total_count')) is int
         and listing['total_count'] == len(artifacts) <= 100, 'incomplete artifact listing')
    matches = [a for a in artifacts if a.get('name') == artifact_name(selected['run_id'], selected['run_attempt'])]
    need(len(matches) == 1, 'missing or ambiguous attempt artifact')
    artifact = artifact_identity(api.get(f"/actions/artifacts/{selected['artifact_id']}"))
    need(artifact_identity(matches[0]) == artifact, 'artifact listing/identity changed')
    need(artifact.get('id') == selected['artifact_id'] and artifact.get('expired') is False
         and artifact.get('digest') == 'sha256:' + selected['zip_sha256']
         and 0 < integer(artifact.get('size_in_bytes')) <= MAX_IMAGE
         and timestamp(artifact.get('expires_at')) > time.time(), 'artifact expired or digest identity changed')
    binding = artifact.get('workflow_run', {})
    need(binding.get('id') == selected['run_id'] and binding.get('repository_id') == repo['id']
         and binding.get('head_repository_id') == repo['id'] and binding.get('head_sha') == sha
         and binding.get('head_branch') == branch, 'artifact is not bound to the producer source')
    return {'sha': sha, 'tree': tree, 'contract': trusted, 'artifact': artifact,
            'purpose': 'no-deploy-rehearsal' if rehearsal else 'production-candidate',
            'producer': {'workflow': CI, 'run_id': selected['run_id'], 'run_attempt': selected['run_attempt'],
                         'event': event, 'ref': 'refs/heads/' + branch}}


def validate_policy(environment, branches, protection):
    need(environment.get('name') == 'production' and environment.get('can_admins_bypass') is False,
         'production approval is missing or bypassable')
    need(environment.get('deployment_branch_policy') == {'protected_branches': False, 'custom_branch_policies': True},
         'native exact-main environment policy required')
    policies = branches.get('branch_policies')
    need(type(branches.get('total_count')) is int and branches['total_count'] == 1 and type(policies) is list and len(policies) == 1
         and policies[0].get('name') == 'main' and policies[0].get('type') == 'branch', 'extra or unsupported deployment ref')
    rules = environment.get('protection_rules')
    # GitHub may also report its native branch_policy marker here; the complete
    # exact-main policy is checked independently above, never inferred from it.
    need(type(rules) is list and 1 <= len(rules) <= 2
         and all(type(rule) is dict and rule.get('type') in ('required_reviewers', 'branch_policy') for rule in rules),
         'unsupported environment protection rules')
    approval = [rule for rule in rules if rule['type'] == 'required_reviewers']
    need(len(approval) == 1 and approval[0].get('prevent_self_review') is True, 'non-self human approval required')
    reviewers = approval[0].get('reviewers')
    need(type(reviewers) is list and 1 <= len(reviewers) <= 6, 'missing human reviewer identities')
    users = []
    for entry in reviewers:
        user = entry.get('reviewer', {})
        need(entry.get('type') == 'User' and user.get('type') == 'User'
             and isinstance(user.get('login'), str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', user['login']),
             'this narrow policy supports explicit User reviewers only')
        users.append(integer(user.get('id')))
    need(len(set(users)) == len(users), 'duplicate reviewer identity')
    need(protection.get('enforce_admins', {}).get('enabled') is True
         and protection.get('allow_force_pushes', {}).get('enabled') is False
         and protection.get('allow_deletions', {}).get('enabled') is False, 'main protection is bypassable')
    reviews = protection.get('required_pull_request_reviews', {})
    need(type(reviews.get('required_approving_review_count')) is int and 1 <= reviews['required_approving_review_count'] <= 6
         and reviews.get('dismiss_stale_reviews') is True and reviews.get('require_last_push_approval') is True
         and reviews.get('bypass_pull_request_allowances') == {'users': [], 'teams': [], 'apps': []},
         'enforcing source/workflow review protection is missing')
    checks = protection.get('required_status_checks', {})
    required = checks.get('checks')
    need(checks.get('strict') is True and type(required) is list
         and {(item.get('context'), item.get('app_id')) for item in required}
         == {('verify', GITHUB_ACTIONS_APP_ID), ('container', GITHUB_ACTIONS_APP_ID)}
         and len(required) == 2, 'required GitHub Actions CI protection is missing')
    need(type(checks.get('contexts')) is list and sorted(checks['contexts']) == ['container', 'verify'],
         'inconsistent required CI contexts')
    # Hash only enforced policy fields, not avatar URLs or unrelated mutable API decoration.
    return digest(canonical({'users': sorted(users), 'review_count': reviews['required_approving_review_count'],
                             'dismiss_stale_reviews': True, 'require_last_push_approval': True,
                             'review_bypass': False, 'strict_ci': True,
                             'checks': sorted((item['context'], item['app_id']) for item in required),
                             'main_only': True, 'self_review': False, 'admin_bypass': False}))


def validate_scan(report, expected_image, now=None):
    now = time.time() if now is None else now
    descriptor = report.get('descriptor', {})
    need(descriptor.get('name') == 'grype' and descriptor.get('version') == GRYPE_VERSION, 'wrong scanner version')
    scanned = timestamp(descriptor.get('timestamp'))
    need(0 <= now - scanned <= 3 * 24 * 3600 + 60, 'invalid scan timestamp')
    config = descriptor.get('configuration', {})
    need(config.get('check-for-app-update') is False and config.get('timestamp') is True
         and config.get('fail-on-severity') == 'high' and config.get('search', {}).get('scope') == 'squashed'
         and config.get('only-fixed') is False and config.get('only-notfixed') is False
         and config.get('ignore-wontfix') == '' and config.get('match-upstream-kernel-headers') is True,
         'wrong scanner threshold or unfixed policy')
    for field in ('ignore', 'exclude', 'vex-documents', 'vex-add'):
        need(config.get(field) in (None, []), 'scanner suppression is forbidden')
    db_config = config.get('db', {})
    need(all(db_config.get(field) is True for field in ('auto-update', 'require-update-check', 'validate-age', 'validate-by-hash-on-start'))
         and db_config.get('max-allowed-built-age') in (MAX_DB_AGE * 1_000_000_000, '120h', '120h0m0s')
         and db_config.get('update-url') == GRYPE_DB_URL
         and db_config.get('max-update-check-frequency') in (0, '0s'),
         'scanner database policy mismatch')
    database = descriptor.get('db')
    need(type(database) is dict and type(database.get('status')) is dict, 'invalid scanner database metadata')
    db = database['status']  # Grype 0.118.0 reports status separately from provider metadata.
    need(db.get('valid') is True and not db.get('error') and isinstance(db.get('schemaVersion'), str)
         and re.fullmatch(r'v6(?:\.[0-9]+){0,2}', db['schemaVersion'])
         and isinstance(db.get('from'), str) and db['from'].startswith('https://grype.anchore.io/databases/'),
         'invalid scanner database metadata')
    need(0 <= scanned - timestamp(db.get('built')) <= MAX_DB_AGE, 'scanner database was stale at scan time')
    need(report.get('source', {}).get('type') == 'image'
         and report['source'].get('target', {}).get('imageID') == expected_image, 'scan covered a different image')
    matches = report.get('matches')
    need(type(matches) is list and report.get('ignoredMatches', []) == [], 'unknown or suppressed scan results')
    for match in matches:
        need(match.get('vulnerability', {}).get('severity') in ('Unknown', 'Negligible', 'Low', 'Medium'),
             'HIGH/CRITICAL or malformed scan result')
    return {'schemaVersion': db['schemaVersion'], 'built': db['built'], 'from': db['from'],
            'valid': True, 'scanned_at': descriptor['timestamp']}


def unpack_zip(archive, destination):
    # Bound the central directory BEFORE ZipFile materializes entries. ZIP64 is unnecessary below512MiB.
    size = archive.stat().st_size
    need(22 <= size <= MAX_IMAGE, 'outer ZIP size limit')
    with archive.open('rb') as source:
        source.seek(-22, 2)
        end = struct.unpack('<4s4H2LH', source.read(22))
    need(end[:5] == (b'PK\x05\x06', 0, 0, 3, 3) and end[5] <= 65536
         and end[6] + end[5] == size - 22 and end[7] == 0, 'unsupported ZIP directory or entry count')
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        need(len(entries) == 3 and {item.filename for item in entries} == set(FILES), 'unexpected ZIP member')
        for item in entries:
            need(stat.S_ISREG(item.external_attr >> 16) and not item.is_dir() and not item.flag_bits & 1
                 and item.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                 and 0 < item.file_size <= FILES[item.filename], 'nonregular or oversized ZIP member')
            with bundle.open(item) as source, (destination / item.filename).open('xb') as target:
                actual = copy_bounded(source, target, FILES[item.filename])
            need(actual['bytes'] == item.file_size, 'ZIP member size mismatch')


def validate_receipt(directory, metadata, ctx):
    receipt = parse_json(file_bytes(directory / 'receipt.json', MAX_RECEIPT), MAX_RECEIPT)
    keys(receipt, 'schema purpose source producer contract image archive scan')
    need(type(receipt['schema']) is int and receipt['schema'] == 1 and receipt['purpose'] == metadata['purpose'],
         'ineligible receipt purpose/version')
    need(receipt['source'] == {'repository': REPOSITORY, 'repository_id': ctx['repository_id'],
                               'sha': metadata['sha'], 'tree': metadata['tree']}
         and receipt['producer'] == metadata['producer'] and receipt['contract'] == metadata['contract'],
         'receipt source/attempt/contract mismatch')
    image = receipt['image']
    keys(image, 'id tag os architecture revision')
    image_id(image['id'])
    need(image == {'id': image['id'], 'tag': 'kira-admin:' + metadata['sha'], 'os': 'linux',
                   'architecture': 'amd64', 'revision': metadata['sha']}, 'image platform/label mismatch')
    archive = receipt['archive']
    keys(archive, 'bytes sha256 expanded_bytes expanded_sha256')
    need(file_identity(directory / 'image.tar.gz', MAX_IMAGE) == {k: archive[k] for k in ('bytes', 'sha256')},
         'inner gzip digest or size mismatch')
    with gzip.open(directory / 'image.tar.gz', 'rb') as source, (directory / 'image.tar').open('xb') as target:
        expanded = copy_bounded(source, target, MAX_TAR)
    need(expanded == {'bytes': archive['expanded_bytes'], 'sha256': archive['expanded_sha256']}
         and expanded['bytes'] > 0, 'expanded Docker archive mismatch')
    scan = receipt['scan']
    keys(scan, 'bytes sha256 policy result tool database')
    raw = file_bytes(directory / 'scan.json', MAX_SCAN)
    need(scan['bytes'] == len(raw) and scan['sha256'] == digest(raw) and scan['policy'] == SCAN_POLICY
         and scan['result'] == 'pass' and scan['tool'] == {'name': 'grype', 'version': GRYPE_VERSION,
                                                         'archive_sha256': GRYPE_SHA}, 'scan receipt mismatch')
    need(scan['database'] == validate_scan(parse_json(raw, MAX_SCAN), image['id']), 'scan database receipt mismatch')
    return receipt


def command(argv, *, seconds=60, output=None, maximum=1024 * 1024, env=None, stdin=None, errors=None):
    # No shell, bounded stdout and time, terminate only this owned process group on every failure.
    # API/SSH secrets belong only to their Python API/transfer step, never child process environments.
    if env is None:
        env = {key: os.environ[key] for key in ('PATH', 'HOME', 'TMPDIR', 'LANG') if key in os.environ}
    result = bytearray()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE if errors is not None else subprocess.DEVNULL, stdin=stdin,
                               env=env, start_new_session=True)
    end, count, error_count = time.monotonic() + seconds, 0, 0
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            if errors is not None:
                selector.register(process.stderr, selectors.EVENT_READ)
            while selector.get_map():
                remaining = end - time.monotonic()
                need(remaining > 0, 'command timed out')
                ready = selector.select(remaining)
                if not ready:
                    raise Refused('command timed out')
                for key, _ in ready:
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if key.fileobj is process.stderr:
                        error_count += len(chunk)
                        need(error_count <= 65536, 'scanner error output limit exceeded')
                        errors.write(chunk)
                    else:
                        count += len(chunk)
                        need(count <= maximum, 'command output limit exceeded')
                        if output is None:
                            result.extend(chunk)
                        else:
                            output.write(chunk)
        try:
            status = process.wait(timeout=max(0.1, end - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise Refused('command timed out') from None
        need(status == 0, 'command or scanner gate failed')
        return bytes(result)
    finally:
        # Include descendants even if the direct child exited while they held stdout open.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        if process.poll() is None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def inspect_image(expected):
    value = parse_json(command(['docker', 'image', 'inspect', expected['tag']], seconds=30), 1024 * 1024)
    need(type(value) is list and len(value) == 1, 'unexpected Docker image inspection')
    item = value[0]
    need(item.get('Id') == expected['id'] and item.get('Os') == expected['os']
         and item.get('Architecture') == expected['architecture']
         and item.get('Config', {}).get('Labels', {}).get('org.opencontainers.image.revision') == expected['revision']
         and item['Config']['Labels'].get('org.opencontainers.image.version') == expected['revision']
         and expected['tag'] in item.get('RepoTags', []), 'loaded image/tag/platform/labels do not match')


def inspect_runtime(name):
    # Fixed read-only probe in the existing container; bound APK reads and process output/time.
    script = r"""
const fs = require('node:fs');
const fd = fs.openSync('/lib/apk/db/installed', 'r');
const metadata = fs.fstatSync(fd);
if (!metadata.isFile() || metadata.size < 1 || metadata.size > 262144) throw new Error('invalid APK inventory');
const data = Buffer.alloc(metadata.size);
if (fs.readSync(fd, data, 0, data.length, 0) !== data.length) throw new Error('incomplete APK inventory');
fs.closeSync(fd);
const apk = data.toString('utf8').split(/\n\n+/)
  .map(block => [block.match(/^P:(.+)$/m)?.[1], block.match(/^V:(.+)$/m)?.[1]])
  .filter(([name]) => name === 'libcrypto3' || name === 'libssl3')
  .sort(([a], [b]) => a.localeCompare(b));
const paths = [
  '/usr/local/lib/node_modules/npm', '/usr/local/lib/node_modules/corepack', '/opt/yarn-v1.22.22',
  '/usr/local/bin/npm', '/usr/local/bin/npx', '/usr/local/bin/corepack', '/usr/local/bin/yarn', '/usr/local/bin/yarnpkg',
];
process.stdout.write(JSON.stringify({
  node: process.versions.node, openssl: process.versions.openssl, uid: process.getuid(), euid: process.geteuid(), apk,
  tool_paths_present: paths.filter(path => fs.lstatSync(path, {throwIfNoEntry: false}) !== undefined),
}));
"""
    inventory = parse_json(command(['docker', 'exec', name, '/usr/local/bin/node', '--eval', script],
                                   seconds=15, maximum=4096), 4096)
    need(type(inventory) is dict and set(inventory) == {'node', 'openssl', 'uid', 'euid', 'apk', 'tool_paths_present'}
         and inventory['node'] == '24.21.0' and inventory['openssl'] == '3.5.8'
         and all(type(inventory[field]) is int and 0 < inventory[field] < 2**32 for field in ('uid', 'euid'))
         and inventory['apk'] == [['libcrypto3', '3.5.8-r0'], ['libssl3', '3.5.8-r0']]
         and inventory['tool_paths_present'] == [], 'exact-image runtime inventory mismatch')
    print('PASS exact-image runtime inventory:', canonical(inventory).decode())
    return inventory


def smoke(expected):
    inspect_image(expected)
    owner = uuid.uuid4().hex
    name = 'kira-admin8-smoke-' + owner
    created = False
    try:
        command(['docker', 'create', '--name', name, '--read-only', '--tmpfs', '/tmp:size=16m',
                 '--label', 'kira.admin8.smoke=' + owner,
                 '--env', 'KIRA_BACKEND_URL=http://127.0.0.1:9', '--env', 'KIRA_ADMIN_ORIGIN=http://127.0.0.1:18082',
                 '--publish', '127.0.0.1:18082:8080', expected['id']], seconds=30)
        created = True
        command(['docker', 'start', name], seconds=30)
        inspect_runtime(name)
        with deadline(70):
            for _ in range(30):
                try:
                    with OPENER.open('http://127.0.0.1:18082/', timeout=2) as response:
                        if response.status == 200:
                            return
                except OSError:
                    pass
                time.sleep(2)
        raise Refused('exact-image runtime smoke failed')
    finally:
        try:
            found = parse_json(command(['docker', 'container', 'inspect', name], seconds=30), 1024 * 1024)
        except Refused:
            need(not created, 'smoke container cleanup could not be observed')
        else:
            need(type(found) is list and len(found) == 1
                 and found[0].get('Config', {}).get('Labels', {}).get('kira.admin8.smoke') == owner,
                 'refusing cleanup of an unowned container')
            command(['docker', 'rm', '--force', name], seconds=30)


def write_json(path, value, maximum=MAX_RECEIPT):
    raw = canonical(value) + b'\n'
    need(len(raw) <= maximum, 'output document limit exceeded')
    with path.open('xb') as output:
        output.write(raw)


def output(name, value):
    need('\n' not in str(value), 'invalid workflow output')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            stream.write(f'{name}={value}\n')


def owned(path):
    path = Path(path)
    need(path.parent.resolve() == Path(os.environ['RUNNER_TEMP']).resolve() and path.name.startswith('kira-admin8-')
         and path.is_dir() and not path.is_symlink(), 'scratch is not owned by this run')
    owner = parse_json(file_bytes(path / 'owner.json', 1024), 1024)
    need(owner == {key: os.environ.get(key) for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_JOB')},
         'scratch belongs to another run/job')
    return path


def image_for(ctx, identity):
    return {'id': image_id(identity), 'tag': 'kira-admin:' + ctx['sha'], 'os': 'linux',
            'architecture': 'amd64', 'revision': ctx['sha']}


def remember_image(directory, image):
    inspect_image(image)
    write_json(directory / 'owned-image.json', image)


def load_image(directory, archive_directory, image):
    # Fresh hosted consumer runner. Record the intended tag before loading, so a partial failed
    # load can still clean it up IF inspection proves it is this exact expected image, never another.
    write_json(directory / 'owned-image.json', image)
    command(['docker', 'load', '--input', str(archive_directory / 'image.tar')], seconds=180)
    inspect_image(image)  # Loading/inspecting is not running candidate code.


def remove_image(directory):
    marker = directory / 'owned-image.json'
    if marker.exists():
        image = parse_json(file_bytes(marker, 1024), 1024)
        need(image['tag'] == 'kira-admin:' + hex_value(image['revision'], 40), 'invalid owned image tag')
        image_id(image['id'])
        inspect_image(image)
        command(['docker', 'image', 'rm', image['tag']], seconds=60)
        marker.unlink()


def produce(directory, ctx, identity):
    production = ctx['event_name'] == 'push' and ctx['ref'] == 'refs/heads/main'
    need(production or ctx['event_name'] == 'workflow_dispatch', 'not an artifact-producing event')
    need(ctx['workflow_ref'] == f"{REPOSITORY}/{CI}@{ctx['ref']}" and ctx['workflow_sha'] == ctx['sha'],
         'wrong producer workflow')
    need(command(['git', 'rev-parse', 'HEAD']).decode().strip() == ctx['sha']
         and not command(['git', 'status', '--porcelain', '--untracked-files=all']).strip(), 'producer checkout is dirty or changed')
    tree = hex_value(command(['git', 'rev-parse', 'HEAD^{tree}']).decode().strip(), 40)
    image = image_for(ctx, identity)
    remember_image(directory, image)
    smoke(image)  # This exact ID, not a mutable tag, is executed.
    inspect_image(image)  # The one tag exported below must STILL resolve to the smoked ID.
    plain = directory / 'image.tar'
    with plain.open('xb') as target:
        command(['docker', 'save', image['tag']], seconds=180, output=target, maximum=MAX_TAR)
    expanded = file_identity(plain, MAX_TAR)
    with (directory / 'image.tar.gz').open('xb') as target:
        command(['gzip', '--no-name', '--stdout', str(plain)], seconds=180, output=target, maximum=MAX_IMAGE)
    archive = file_identity(directory / 'image.tar.gz', MAX_IMAGE)

    scanner_archive = directory / 'grype.tar.gz'
    scanner_url = f'https://github.com/anchore/grype/releases/download/v{GRYPE_VERSION}/grype_{GRYPE_VERSION}_linux_amd64.tar.gz'
    # Public pinned tool download: no API or production credential is supplied.
    with deadline(120), urllib.request.urlopen(scanner_url, timeout=15) as source, scanner_archive.open('xb') as target:
        downloaded = copy_bounded(source, target, 40 * 1024 * 1024)
    need(downloaded['sha256'] == GRYPE_SHA, 'scanner archive checksum mismatch')
    executable = directory / 'grype'
    with tarfile.open(scanner_archive, 'r:gz') as bundle:
        members = [member for member in bundle if member.name == 'grype']
        need(len(members) == 1 and members[0].isfile() and 0 < members[0].size <= 128 * 1024 * 1024,
             'unexpected scanner executable')
        with bundle.extractfile(members[0]) as source, executable.open('xb') as target:
            copy_bounded(source, target, 128 * 1024 * 1024)
    executable.chmod(0o700)
    scan_env = {'PATH': os.environ['PATH'], 'HOME': str(directory), 'TMPDIR': str(directory),
                'GRYPE_DB_CACHE_DIR': str(directory / 'db')}
    with (directory / 'scan.json').open('xb') as target, (directory / 'scan-error.log').open('xb') as errors:
        command([str(executable), '--config', str(ROOT / 'scripts/ci/grype.yaml'), '--fail-on', 'high',
                 '--scope', 'squashed', '--output', 'json', 'docker-archive:' + str(plain)],
                seconds=300, maximum=MAX_SCAN, output=target, env=scan_env, errors=errors)
    raw_scan = file_bytes(directory / 'scan.json', MAX_SCAN)
    database = validate_scan(parse_json(raw_scan, MAX_SCAN), image['id'])
    receipt = {'schema': 1, 'purpose': 'production-candidate' if production else 'no-deploy-rehearsal',
               'source': {'repository': REPOSITORY, 'repository_id': ctx['repository_id'], 'sha': ctx['sha'], 'tree': tree},
               'producer': {'workflow': CI, 'run_id': ctx['run_id'], 'run_attempt': ctx['run_attempt'],
                            'event': ctx['event_name'], 'ref': ctx['ref']},
               'contract': local_contract(), 'image': image,
               'archive': {**archive, 'expanded_bytes': expanded['bytes'], 'expanded_sha256': expanded['sha256']},
               'scan': {'bytes': len(raw_scan), 'sha256': digest(raw_scan), 'policy': SCAN_POLICY, 'result': 'pass',
                        'tool': {'name': 'grype', 'version': GRYPE_VERSION, 'archive_sha256': GRYPE_SHA}, 'database': database}}
    write_json(directory / 'receipt.json', receipt)  # Only after smoke, export AND scan pass.
    print('PASS exact-image smoke/export/scan:', canonical({'image': image, 'archive': receipt['archive'], 'database': database}).decode())


def verify_candidate(directory, ctx, selected, rehearsal=False):
    api = GitHub(os.environ.get('GITHUB_TOKEN'))
    metadata = candidate_metadata(api, ctx, selected, rehearsal)
    api.download(selected['artifact_id'], directory / 'artifact.zip',
                 {'bytes': metadata['artifact']['size_in_bytes'], 'sha256': selected['zip_sha256']})
    unpack_zip(directory / 'artifact.zip', directory)
    receipt = validate_receipt(directory, metadata, ctx)
    # Detect deleted/expired artifacts, rerun attempts and trusted-main contract changes during download.
    need(candidate_metadata(api, ctx, selected, rehearsal) == metadata, 'candidate changed during verification')
    fingerprint = digest(canonical({'selection': selected, 'receipt': receipt}))
    expected = os.environ.get('EXPECTED_CANDIDATE')
    need(not expected or fingerprint == expected, 'approved immutable candidate changed')
    write_json(directory / 'candidate.json', {'selection': selected, 'receipt': receipt, 'fingerprint': fingerprint})
    output('candidate', fingerprint)
    summary = {'source': receipt['source'], 'producer': receipt['producer'], 'selection': selected,
               'image': receipt['image'], 'archive': receipt['archive'], 'scan_policy': SCAN_POLICY,
               'scan_result': 'pass', 'candidate_fingerprint': fingerprint}
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write('### Frozen exact-image candidate (dispatch is not approval)\n```json\n'
                         + json.dumps(summary, indent=2) + '\n```\n')
    print('PASS immutable candidate:', fingerprint)
    return receipt


def policy(directory, ctx):
    verify_dispatch(ctx)
    # This process receives ONLY the separately authorized repository-scoped read-only policy token.
    api = GitHub(os.environ.get('ADMIN8_POLICY_READ_TOKEN'))
    fingerprint = validate_policy(api.get('/environments/production'),
                                  api.get('/environments/production/deployment-branch-policies?per_page=100'),
                                  api.get('/branches/main/protection'))
    expected = os.environ.get('EXPECTED_POLICY')
    need(not expected or fingerprint == expected, 'approval/source policy changed after preflight')
    candidate = parse_json(file_bytes(directory / 'candidate.json', MAX_RECEIPT * 2), MAX_RECEIPT * 2)
    write_json(directory / 'policy.json', {'fingerprint': fingerprint, 'candidate': candidate['fingerprint'],
                                          'checked_at': utc_now(), 'run_id': ctx['run_id'], 'attempt': ctx['run_attempt']})
    output('policy', fingerprint)
    print('PASS native approval/ref/source-policy prerequisites; actual native job approval is still required.')


def transfer(directory, ctx, selected):
    # No key file, image execution, rebuild or transfer occurs until all pre-key checks below pass.
    need(ctx['job'] == 'promote', 'transfer is restricted to the protected promotion job')
    need(bool(os.environ.get('EXPECTED_CANDIDATE')) and bool(os.environ.get('EXPECTED_POLICY')), 'missing frozen approval binding')
    api = GitHub(os.environ.get('GITHUB_TOKEN'))
    metadata = candidate_metadata(api, ctx, selected)
    candidate = parse_json(file_bytes(directory / 'candidate.json', MAX_RECEIPT * 2), MAX_RECEIPT * 2)
    receipt = candidate['receipt']
    need(candidate['selection'] == selected and candidate['fingerprint'] == os.environ['EXPECTED_CANDIDATE']
         and digest(canonical({'selection': selected, 'receipt': receipt})) == candidate['fingerprint']
         and receipt['source']['sha'] == metadata['sha'] and receipt['contract'] == metadata['contract'], 'pre-key candidate changed')
    proof = parse_json(file_bytes(directory / 'policy.json', MAX_RECEIPT), MAX_RECEIPT)
    need(proof['fingerprint'] == os.environ['EXPECTED_POLICY'] and proof['candidate'] == candidate['fingerprint']
         and proof['run_id'] == ctx['run_id'] and proof['attempt'] == ctx['run_attempt']
         and 0 <= time.time() - timestamp(proof['checked_at']) <= 180, 'policy recheck is missing or stale')
    need(file_identity(directory / 'image.tar.gz', MAX_IMAGE) == {k: receipt['archive'][k] for k in ('bytes', 'sha256')},
         'archive changed before SSH setup')
    inspect_image(receipt['image'])
    host, user = os.environ.get('DEPLOY_HOST', ''), os.environ.get('DEPLOY_USER', '')
    port = os.environ.get('DEPLOY_PORT') or '22'
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}', host) and re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', user)
         and re.fullmatch(r'[1-9][0-9]{0,4}', port) and int(port) <= 65535, 'invalid fixed SSH destination')
    private, hosts = os.environ.get('DEPLOY_KEY', ''), os.environ.get('KNOWN_HOSTS', '')
    need(0 < len(private.encode()) <= 16384 and 0 < len(hosts.encode()) <= 16384, 'missing or oversized SSH credential')
    key, known = directory / 'ssh-key', directory / 'known-hosts'
    try:
        for path, value in ((key, private), (known, hosts)):
            with open(path, 'x', opener=lambda name, flags: os.open(name, flags, 0o600)) as target:
                target.write(value + '\n')
        # Stream the ORIGINAL verified gzip, never another docker save or build.
        with (directory / 'image.tar.gz').open('rb') as source:
            command(['ssh', '-F', '/dev/null', '-i', str(key), '-p', port, '-o', 'BatchMode=yes',
                     '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'GlobalKnownHostsFile=/dev/null',
                     '-o', 'UserKnownHostsFile=' + str(known), '-o', 'ConnectTimeout=15',
                     '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
                     user + '@' + host, 'deploy admin ' + hex_value(receipt['source']['sha'], 40)],
                    seconds=600, stdin=source)
    finally:
        key.unlink(missing_ok=True)
        known.unlink(missing_ok=True)


def rehearse(directory, ctx, selected):
    identities = []
    for attempt in (1, 2):
        child = directory / str(attempt)
        child.mkdir(mode=0o700)
        try:
            receipt = verify_candidate(child, ctx, selected, rehearsal=True)
            load_image(directory, child, receipt['image'])
            smoke(receipt['image'])
            identities.append((receipt['image'], receipt['archive']))
        finally:
            try:
                remove_image(directory)
            finally:
                shutil.rmtree(child)
    need(identities[0] == identities[1], 'rehearsal artifact reuse changed the image')
    print('PASS no-deploy rehearsal: one immutable artifact, two verified loads/smokes, ZERO rebuilds or deployment credentials.')


def main():
    def interrupted(_signal, _frame):
        raise Refused('release operation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('scratch', 'cleanup', 'smoke', 'produce', 'verify', 'policy', 'transfer', 'rehearse'))
    parser.add_argument('--scratch', default=os.environ.get('SCRATCH', ''))
    parser.add_argument('--image-id', default=os.environ.get('BUILT_IMAGE_ID', ''))
    args = parser.parse_args()
    os.umask(0o077)
    ctx = context()
    if args.operation == 'scratch':
        directory = Path(tempfile.mkdtemp(prefix='kira-admin8-', dir=os.environ['RUNNER_TEMP']))
        write_json(directory / 'owner.json', {key: os.environ.get(key) for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_JOB')})
        output('path', directory)
        return
    if args.operation == 'smoke':
        directory = owned(args.scratch)
        remember_image(directory, image_for(ctx, args.image_id))
        smoke(image_for(ctx, args.image_id))
        return
    directory = owned(args.scratch)
    if args.operation == 'cleanup':
        try:
            remove_image(directory)
        finally:
            shutil.rmtree(directory)
        print('CLEANUP owned image archives, scanner/cache and credential scratch removed.')
    elif args.operation == 'produce':
        produce(directory, ctx, args.image_id)
    elif args.operation == 'policy':
        policy(directory, ctx)
    elif args.operation == 'transfer':
        transfer(directory, ctx, selection())
    elif args.operation == 'verify':
        receipt = verify_candidate(directory, ctx, selection())
        if ctx['job'] == 'promote':
            load_image(directory, directory, receipt['image'])
    elif args.operation == 'rehearse':
        rehearse(directory, ctx, selection())


def diagnostic_family(error):
    # Fixed family codes only; never obtain an exception's name, message, arguments or repr.
    for family, kinds in (
        ('refused', Refused), ('timeout', (TimeoutError, subprocess.TimeoutExpired)),
        ('network', urllib.error.URLError), ('archive', (tarfile.TarError, zipfile.BadZipFile, gzip.BadGzipFile)),
        ('process', subprocess.SubprocessError), ('os', OSError), ('lookup', LookupError),
        ('value', ValueError), ('type', TypeError), ('attribute', AttributeError), ('runtime', RuntimeError),
    ):
        if issubclass(type(error), kinds):
            return family
    return 'other'


def diagnostic_frames(error):
    trace, lines, limited = error.__traceback__, [], False
    for _ in range(MAX_DIAGNOSTIC_TRACE):
        if trace is None:
            break
        frame = trace.tb_frame
        if frame.f_globals is globals() and frame.f_code.co_filename == diagnostic_frames.__code__.co_filename:
            line = trace.tb_lineno
            if type(line) is int and 0 < line <= MAX_DIAGNOSTIC_LINE:
                if len(lines) == MAX_DIAGNOSTIC_FRAMES:
                    lines.pop(0)
                    limited = True
                lines.append(line)
            else:
                limited = True
        trace = trace.tb_next
    return {'lines': lines, 'frames_limited': limited or trace is not None}


def failure_diagnostic(error):
    """Bounded, best-effort location evidence, not a traceback or a root-cause assertion."""
    try:
        pending, entries, seen, repeated = [(error, None, 'raised')], [], set(), False
        while pending and len(entries) < MAX_DIAGNOSTIC_ENTRIES:
            current, parent, via = pending.pop(0)
            if id(current) in seen:
                repeated = True
                continue
            seen.add(id(current))
            index = len(entries)
            entries.append({'parent': parent, 'via': via, 'family': diagnostic_family(current),
                            **diagnostic_frames(current)})
            # Keep context even when suppressed or different from an explicit cause: cleanup can mask it.
            for attribute, link in (('__cause__', 'cause'), ('__context__', 'context')):
                previous = getattr(current, attribute)
                if previous is not None:
                    pending.append((previous, index, link))
        value = 'DIAGNOSTIC: ' + canonical({'entries': entries, 'chain_limited': bool(pending),
                                           'chain_repeated': repeated}).decode('ascii')
        if len(value) + 1 <= MAX_DIAGNOSTIC_BYTES:  # Include print's newline; all projected data is ASCII.
            return value
    except BaseException:
        pass
    return 'DIAGNOSTIC: unavailable'


def run():
    try:
        main()
    except Exception as error:
        print('REFUSED: ' + (str(error) if isinstance(error, Refused) else 'release operation failed closed'), file=sys.stderr)
        # Diagnostics cannot replace an already-failed operation's exit status, even if interrupted.
        with contextlib.suppress(BaseException):
            print(failure_diagnostic(error), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    run()
