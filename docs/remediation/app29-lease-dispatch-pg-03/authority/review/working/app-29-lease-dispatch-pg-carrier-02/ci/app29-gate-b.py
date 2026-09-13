#!/usr/bin/env python3
"""Inert private lease-dispatch PG successor: exact17 plus one former failed method, not qualification."""
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
from xml.etree import ElementTree as ET

ADMIN = Path(__file__).resolve().parent.parent
BACKEND = ADMIN.parent / 'backend'
PAYLOAD = ADMIN / 'docs/remediation/app29-lease-dispatch-pg-01-transport-02'
GATE = 'app-29-lease-dispatch-pg-01'
CHECKPOINT_SCHEMA = 'app29-lease-dispatch-clean-checkpoint-v1'
PROFILE_ID = 'app-29-lease-dispatch-pg-profile-01'
PROFILE_FILE = 'review/working/app-29-lease-dispatch-pg-carrier-02/profile/profile.json'
PROFILE_SHA = '315509d24f0fd4c84fd8172231e7eb79639bad1a0ae589db6e18ce0268b4ed79'  # Primary actual-value binding; no product acceptance.
PROFILE_INIT = 'review/working/app-29-lease-dispatch-pg-carrier-02/profile/profile.init.gradle'
PROFILE_INIT_SHA = 'd7315be66f9bf654e2ae62b164e9252c7ee3deeeccc66a5b6e826104707e7a2d'  # Primary actual-value binding; no product acceptance.
MANIFEST_FILE = 'review/working/app-29-w03-integrated-driver-lease-dispatch-pg-01-transport-02/manifest.json'
CREATOR_CLASS = 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest'
OWNERSHIP_CLASS = 'me.manga.kira.backend.common.infrastructure.persistence.OrdinarySourceGrantCleanupOwnershipIT'
CREATOR_METHOD = 'actual creator publication restoration and outer adapter faults retain exact obligations through process only exit'
CREATOR_MODES = (
    'POOL_LEASE_CREATOR_ENTRY_BEFORE_TL', 'POOL_LEASE_CREATOR_ENTRY_AFTER_TL',
    'POOL_LEASE_CREATOR_END_BEFORE_TL', 'POOL_LEASE_CREATOR_END_AFTER_TL',
    'POOL_LEASE_CREATOR_CORE_BEFORE_TL', 'POOL_LEASE_CREATOR_CORE_AFTER_TL',
    'POOL_LEASE_CREATOR_CLIENT_INFO_TAIL', 'POOL_LEASE_CREATOR_DECLARED_TAIL',
)
METHODS = {
    CREATOR_CLASS: (
        'MODEL fatal connection commit creates the first real Hikari close Worker and drains its task',
        'MODEL fatal Hikari statement execution creates the first real close Worker and drains its task',
        'repeated nested admitted dispatches retain one future RETURN and no lower native fallback',
        'only exact admitted guard dispatch lease epoch and issuer can enter a creator',
        'mixed pool creator nesting refuses wrong top fallback and unrelated lease use',
        'present returned dispatch cannot upgrade through pool authority and a revoked lease cannot enter a prepared creator',
        'foreign actual statement cancellation keeps only its own outer tail while original RETURN waits for it',
        'real post core outer tail refuses reentrant self wait and remains in exact terminal and loan proofs',
        'MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement',
        CREATOR_METHOD,
    ),
    OWNERSHIP_CLASS: (
        'native commit failure stays unknown after Spring cleanup while authentic local quiescence permits only refund',
    ),
}
# Historical syntax guard only: this separate profile rejects every emitted PG14 row.
DIAGNOSTIC_CASES = ('RETURN_SAMPLE', 'FAILED_POST_CONSENT_TAIL')
TEST_COUNTS = {CREATOR_CLASS: 17, OWNERSHIP_CLASS: 1}
# Default @ParameterizedTest naming is evidenced by development-cycle13's real enum XML.
# Unlike the explicit {displayName} templates in other tests, these names have no method prefix.
# This is the expected identity set, NOT fabricated execution outcomes; any naming drift fails closed.
EXPECTED_TESTS = [
    {'class': name, 'method': method, 'display_name': display}
    for name, methods in METHODS.items() for method in methods
    for display in ([f'[{index}] mode={mode}' for index, mode in enumerate(CREATOR_MODES, 1)]
                    if name == CREATOR_CLASS and method == CREATOR_METHOD else [method + '()'])
]
TEST_SELECTORS = [name + '.' + method for name, methods in METHODS.items() for method in methods]
TASKS = ['test'] + [arg for selector in TEST_SELECTORS for arg in ('--tests', selector)]
LOCAL_PREFLIGHT_FILE = str(PurePosixPath(MANIFEST_FILE).parent / 'hosted-local-preflight.json')
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
CORE_BASELINE = '49da0919d9ec3091cb7bb041009dc9bd5f3e090f'
PRIVATE_PARENT = '989a8c07b90d956a5f2484f223be41b5d99a8a3c'
PREVIOUS_PRIVATE_PARENT = '926927ab805a2a3b78957862f3b744d0fe399ac5'
DIAGNOSTIC_PARENT = 'eb8fed8b6b620a0c7448c223bf49c1683f8eaadc'
PRODUCT_LIFECYCLE_PARENT = '1c91f0c2d1a4d797e83a0e33b871b417ebcfaae1'
ORDINARY_PARENT = '6db944871c1584bd6a1f28263e8010cadd766fab'
ORDINARY_HEAD = 'ccdbb28f6362117882501b4da040257be6fc1990'
ORDINARY_TREE = 'd172ecf246a9606194f43023a0703d778b877566'
LEASE_HEAD = '8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3'  # Primary actual-value binding; no product acceptance.
LEASE_TREE = 'fc480e82630091138da145ade1812cedcd75e58e'  # Primary actual-value binding; no product acceptance.
LEASE_SOURCE_PATHS = tuple('src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/' + name for name in (
    'GuardedDataSource.kt', 'LeaseJdbcFacade.kt', 'PersistenceJdbcGuardCall.kt', 'PersistenceJdbcGuardProtocol.kt',
    'PersistenceJdbcLease.kt', 'PersistenceJdbcLeaseInvocation.kt', 'PersistenceJdbcPoolTransfer.kt',
    'PersistenceLeaseCompletion.kt', 'PersistenceProducerEpoch.kt', 'PhysicalJdbcDescendants.kt',
    'PoolLifecycle.kt', 'PoolLifecycleFrames.kt',
)) + tuple('src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/' + name for name in (
    'PgLifecycleDatabaseProbe.kt', 'PgLifecycleDatabaseProbeProcess.kt', 'PgLifecycleDatabaseRecipe.kt',
    'OwnedPoolLeaseCreatorPendingProbe.kt', 'PoolLeaseDispatchCreatorIntegrationTest.kt',
))
SOURCE_BUNDLE = {'public_prerequisite_sha': PUBLIC_PREREQUISITE, 'private_parent_sha': ORDINARY_HEAD,
                 'ref': 'refs/heads/' + BACKEND_BRANCH,
                 'source_path': 'review/working/app-29-lease-dispatch-source-checkpoint-01/backend.bundle',
                 'path': 'docs/remediation/app29-lease-dispatch-pg-01-transport-02/inputs/backend.bundle',
                 'sha256': '235fca34c51710930fd9ced4444d0931e5273137bd4178169c3b8c9c4010ec50', 'bytes': 280735}
BUNDLE_MAX_BYTES = 8 * 1024**2
DEPLOYMENTS = {f'review/working/app-29-lease-dispatch-pg-carrier-02/{p}': p for p in (
    'ci/app29-gate-b.py', '.github/workflows/app29-gate-b.yml')}
DEPLOYMENTS[PROFILE_FILE] = PROFILE_FILE
DEPLOYMENTS[PROFILE_INIT] = PROFILE_INIT
DEPLOYMENTS['review/working/app-29-targeted-private-ci-draft-v2/ci/app29_owned_children.py'] = 'ci/app29_owned_children.py'
CACHE_PATHS = ('.gradle', '.kotlin', 'build', 'buildSrc/build', 'out')
GUARD_IDS = {
    'Unsafe bound path': 'BOUND_PATH',
    'Symlink in bound input/output': 'BOUND_LINK',
    'Missing/oversized regular input': 'BOUNDED_REGULAR_FILE',
    'Duplicate JSON key': 'DUPLICATE_KEY',
    'Required test/report root missing': 'CAPTURE_ROOT',
    'Report link': 'CAPTURE_LINK',
    'Evidence copy drift': 'CAPTURE_COPY_DRIFT',
    'Required raw evidence inventory missing': 'CAPTURE_REQUIRED_INVENTORY',
    'Wrong diagnostic XML inventory': 'XML_INVENTORY',
    'Require exactly the18 fixed lease-dispatch source identities': 'XML_EXPECTED_IDENTITIES',
    'Unsafe XML': 'XML_SAFE',
    'Missing, extra or duplicate diagnostic testcase': 'XML_ACTUAL_IDENTITIES',
    'Contradictory diagnostic testcase outcome': 'XML_OUTCOME',
    'Diagnostic XML count mismatch': 'XML_COUNTS',
    'Malformed fixed diagnostic record': 'DIAGNOSTIC_FORMAT',
    'Wrong fixed diagnostic labels or scalar fields': 'DIAGNOSTIC_FIELDS',
    'PG14 fixed diagnostic rows are nonapplicable to this selection': 'DIAGNOSTIC_NOT_APPLICABLE',
    'Wrong actual diagnostic classpath/profile/JDK': 'CONTEXT_CLASSPATH_BINDING',
    'Stock/duplicate classpath supplier': 'CONTEXT_STOCK_OR_DUPLICATE',
    'Wrong explicit class supplier': 'CONTEXT_SUPPLIER',
    'Owned output became a non-directory': 'OWNED_PATH_TYPE',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_profile_pins():
    require(all(isinstance(sha, str) and re.fullmatch('[0-9a-f]{64}', sha) and sha != '0' * 64
                for sha in (PROFILE_SHA, PROFILE_INIT_SHA)),
            'Inert lease-dispatch derivative: final profile/init hashes are UNBOUND')
    require(all(isinstance(sha, str) and re.fullmatch('[0-9a-f]{40}', sha) and sha != '0' * 40
                for sha in (LEASE_HEAD, LEASE_TREE)), 'New private source checkpoint/tree are UNBOUND')


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
            and value['sha256'] != '0' * 64 and isinstance(value['source_path'], str) and bool(value['source_path'])
            and binding['backend_sha'] == LEASE_HEAD
            and binding['backend_sha'] not in (PUBLIC_PREREQUISITE, CORE_BASELINE, PRIVATE_PARENT, PREVIOUS_PRIVATE_PARENT,
                                               DIAGNOSTIC_PARENT, PRODUCT_LIFECYCLE_PARENT, ORDINARY_PARENT, ORDINARY_HEAD),
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
    require_profile_pins()  # Before request reading, emit-target output or helper/resource acquisition.
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
    require(digest(safe(ADMIN, PROFILE_FILE)) == PROFILE_SHA and digest(safe(ADMIN, PROFILE_INIT)) == PROFILE_INIT_SHA,
            'Require the sealed diagnostic profile/init bytes, not a hosted replacement')
    profile = read_json(safe(ADMIN, PROFILE_FILE))
    require(profile['lease_source_stage_status'] == 'BOUND_BY_PRIMARY'
            and all(isinstance(profile[key]['path'], str) and bool(profile[key]['path'])
                    and isinstance(profile[key]['sha256'], str)
                    and re.fullmatch('[0-9a-f]{64}', profile[key]['sha256'])
                    and profile[key]['sha256'] != '0' * 64
                    for key in ('lease_source_target', 'lease_source_checkpoint', 'lease_checkpoint_paths'))
            and set(profile['lease_dispatch_source_delta']) == set(LEASE_SOURCE_PATHS)
            and all(isinstance(row['after_sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['after_sha256'])
                    and row['after_sha256'] != '0' * 64 for row in profile['lease_dispatch_source_delta'].values())
            and all(type(profile['lease_source_target'][key]) is int and profile['lease_source_target'][key] > 0
                    for key in ('source_count', 'snapshot_count')),
            'New lease source stage is UNBOUND; no emit-target, helper or resource acquisition')
    require(digest(ADMIN / 'ci/app29_owned_children.py') == OWNER_SHA, 'Shared ownership utility changed')
    require(digest(PAYLOAD / 'checkpoint.json') == value['checkpoint_sha256'], 'Unbound checkpoint receipt')
    checkpoint = read_json(PAYLOAD / 'checkpoint.json')
    require(checkpoint['schema'] == CHECKPOINT_SCHEMA and checkpoint['source_accepted'] is True
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
    require(checkpoint['schema'] == CHECKPOINT_SCHEMA and checkpoint['source_accepted'] is True
            and checkpoint['backend_sha'] == binding['backend_sha']
            and checkpoint['manifest_path'] == MANIFEST_FILE, 'Missing fresh primary source acceptance')
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
    previous = profile['current_source_freeze']
    require(manifest['approved_inputs'].get(previous['path']) == previous['sha256']
            and digest(safe(authority, previous['path'])) == previous['sha256'], 'Current source freeze missing or changed')
    current = read_json(safe(authority, previous['path']))
    test_binding = profile['binding_test']
    require(current['repositories']['kira-backend'] == {'head': DIAGNOSTIC_PARENT, 'branch': BACKEND_BRANCH, 'status': ''}
            and previous['backend_sha'] == DIAGNOSTIC_PARENT
            and len(current['source_hashes']) == previous['source_count'] == 466
            and len(current['approved_inputs']) == previous['approved_input_count'] == 63
            and len(current['historical_input_hashes']) == previous['historical_input_count'] == 102
            and current['source_hashes'][test_binding['path']] == test_binding['after_sha256'],
            'Wrong immutable diagnostics01 current466 source baseline')
    source_delta = profile['product_lifecycle_source_delta']
    require(len(source_delta) == 8 and all(current['source_hashes'].get(p) == row['before_sha256']
                                          for p, row in source_delta.items()), 'Wrong accepted eight-source baseline')
    expected_sources = dict(current['source_hashes'])
    expected_sources.update({p: row['after_sha256'] for p, row in source_delta.items()})
    # Preserve the accepted PG10 stage before applying only the nineteen structural successors.
    predecessor = profile['post_structural_predecessor']
    require(manifest['approved_inputs'].get(predecessor['path']) == predecessor['sha256']
            and digest(safe(authority, predecessor['path'])) == predecessor['sha256'], 'Accepted PG10 source freeze missing or changed')
    pg10 = read_json(safe(authority, predecessor['path']))
    # Bind historical PG10 argv to its own immutable profile, never a slice of the new TASKS.
    pg10_selection = profile['predecessor_profile']
    require(manifest['approved_inputs'].get(pg10_selection['path']) == pg10_selection['sha256']
            and digest(safe(authority, pg10_selection['path'])) == pg10_selection['sha256'], 'Historical PG10 selection profile missing or changed')
    pg10_profile = read_json(safe(authority, pg10_selection['path']))
    require(pg10['repositories']['kira-backend'] == {'head': PRODUCT_LIFECYCLE_PARENT, 'branch': BACKEND_BRANCH, 'status': ''}
            and predecessor['backend_sha'] == PRODUCT_LIFECYCLE_PARENT
            and pg10_profile['profile_id'] == 'app-29-core-c2-product-lifecycle-pg10-profile-01'
            and pg10_profile['expected_test_count'] == 10 and len(pg10_profile['task_args']) == 21
            and pg10['validation_task_args'] == pg10_profile['task_args']
            and pg10['source_hashes'] == expected_sources and pg10['removed_paths'] == current['removed_paths']
            and pg10['review_subject_paths'] == current['review_subject_paths']
            and pg10['historical_input_hashes'] == current['historical_input_hashes'], 'Wrong immutable PG10 source/authority predecessor')
    require(pg10['approved_inputs'].items() <= manifest['approved_inputs'].items()
            and pg10['validation_tooling'].items() <= manifest['approved_inputs'].items(), 'PG10 approved authority or tooling provenance omitted')
    structural = profile['post_structural_checkpoint']
    require(manifest['approved_inputs'].get(structural['path']) == structural['sha256']
            and digest(safe(authority, structural['path'])) == structural['sha256'], 'Private structural checkpoint missing or changed')
    structural_checkpoint = read_json(safe(authority, structural['path']))
    historical_bundle = profile['historical_pg1_source_bundle']
    require(manifest['approved_inputs'].get(historical_bundle['path']) == historical_bundle['sha256']
            and digest(safe(authority, historical_bundle['path'])) == historical_bundle['sha256']
            and safe(authority, historical_bundle['path']).stat().st_size == historical_bundle['bytes'],
            'Historical structural/PG1 bundle missing or changed')
    post_delta = profile['post_structural_source_delta']
    require(len(post_delta) == 19 and structural_checkpoint['source_delta'] == post_delta
            and structural_checkpoint['head'] == ORDINARY_PARENT
            and structural_checkpoint['parent'] == PRODUCT_LIFECYCLE_PARENT and structural_checkpoint['branch'] == BACKEND_BRANCH
            and structural_checkpoint['public_push_authorized'] is False and structural_checkpoint['source_count'] == 466
            and structural_checkpoint['seed_paths_preserved'] == 348
            and structural_checkpoint['bundle_path'] == historical_bundle['path']
            and structural_checkpoint['bundle_sha256'] == historical_bundle['sha256']
            and structural_checkpoint['bundle_bytes'] == historical_bundle['bytes'] == 217809
            and all(expected_sources.get(p) == row['before'] for p, row in post_delta.items()), 'Wrong accepted nineteen-source successor binding')
    expected_sources.update({p: row['after'] for p, row in post_delta.items()})
    # PG14 and its selector-only PG1 successor remain historical466 stages, not the new checkpoint.
    validation_predecessor = profile['validation_predecessor']
    validation_selection = profile['validation_predecessor_profile']
    for item in (validation_predecessor, validation_selection):
        require(manifest['approved_inputs'].get(item['path']) == item['sha256']
                and digest(safe(authority, item['path'])) == item['sha256'], 'PG14 source/selection predecessor missing or changed')
    pg14 = read_json(safe(authority, validation_predecessor['path']))
    pg14_profile = read_json(safe(authority, validation_selection['path']))
    require(pg14['repositories']['kira-backend'] == {'head': ORDINARY_PARENT, 'branch': BACKEND_BRANCH, 'status': ''}
            and validation_predecessor['backend_sha'] == ORDINARY_PARENT
            and pg14_profile['profile_id'] == 'app-29-core-c2-product-lifecycle-pg14-profile-01'
            and pg14_profile['expected_test_count'] == 14 and len(pg14_profile['task_args']) == 29
            and pg14['validation_task_args'] == pg14_profile['task_args']
            and pg14['source_hashes'] == expected_sources and pg14['removed_paths'] == current['removed_paths']
            and pg14['review_subject_paths'] == current['review_subject_paths']
            and pg14['historical_input_hashes'] == current['historical_input_hashes'], 'Require unchanged complete PG14 source and historical authority')
    require(pg14['approved_inputs'].items() <= manifest['approved_inputs'].items()
            and pg14['validation_tooling'].items() <= manifest['approved_inputs'].items(), 'PG14 approved authority or tooling provenance omitted')

    pg1_binding = profile['ordinary_source_predecessor']
    pg1_selection = profile['ordinary_source_predecessor_profile']
    target_binding = profile['ordinary_source_target']
    transition_binding = profile['ordinary_source_transition']
    source_checkpoint_binding = profile['ordinary_source_checkpoint']
    checkpoint_paths_binding = profile['ordinary_checkpoint_paths']
    for item in (pg1_binding, pg1_selection, target_binding, transition_binding,
                 source_checkpoint_binding, checkpoint_paths_binding, profile['ordinary_selection'],
                 profile['historical_ordinary_source'], profile['historical_ordinary_source_bundle'],
                 profile['historical_ordinary_result'], profile['source_inventory']):
        require(manifest['approved_inputs'].get(item['path']) == item['sha256']
                and digest(safe(authority, item['path'])) == item['sha256'],
                'Ordinary source/selection/checkpoint authority missing or changed')
    pg1 = read_json(safe(authority, pg1_binding['path']))
    pg1_profile = read_json(safe(authority, pg1_selection['path']))
    require(pg1['repositories']['kira-backend'] == {'head': ORDINARY_PARENT, 'branch': BACKEND_BRANCH, 'status': ''}
            and pg1_binding['backend_sha'] == ORDINARY_PARENT
            and pg1_profile['profile_id'] == 'app-29-core-c2-sqlclientinfo-pg1-profile-01'
            and pg1_profile['expected_test_count'] == 1 and len(pg1_profile['task_args']) == 3
            and pg1['validation_task_args'] == pg1_profile['task_args']
            and profile['selection_source_delta'] == pg1_profile['selection_source_delta'] == {}
            and len(pg1['source_hashes']) == pg1_binding['source_count'] == 466
            and len(pg1['snapshots']) == pg1_binding['snapshot_count'] == previous['snapshot_count'] == 199
            and len(pg1['approved_inputs']) == pg1_binding['approved_input_count'] == 170
            and len(pg1['historical_input_hashes']) == pg1_binding['historical_input_count'] == 102
            and pg1['source_hashes'] == expected_sources and pg1['removed_paths'] == current['removed_paths']
            and pg1['review_subject_paths'] == current['review_subject_paths']
            and pg1['historical_input_hashes'] == current['historical_input_hashes'],
            'Require the complete historical PG1 stage before the ordinary source transition')
    target = read_json(safe(authority, target_binding['path']))
    transition = read_json(safe(authority, transition_binding['path']))
    source_checkpoint = read_json(safe(authority, source_checkpoint_binding['path']))
    checkpoint_paths = read_json(safe(authority, checkpoint_paths_binding['path']))
    delta = transition['source_delta']
    actual_delta = [{'path': p, 'before_sha256': pg1['source_hashes'].get(p),
                     'after_sha256': target['source_hashes'].get(p)}
                    for p in sorted(pg1['source_hashes'].keys() | target['source_hashes'].keys())
                    if pg1['source_hashes'].get(p) != target['source_hashes'].get(p)]
    require(transition['schema'] == 'app-29-ordinary-connected-pg-source-transition-v1'
            and transition['historical_pg1_manifest'] == {k: pg1_binding[k] for k in ('path', 'sha256')}
            and transition['historical_pg1_backend_sha'] == ORDINARY_PARENT
            and transition['target_source_manifest'] == {k: target_binding[k] for k in ('path', 'sha256')}
            and transition['before_source_count'] == 466 and transition['after_source_count'] == 478
            and transition['unchanged_count'] == 455 and transition['changed_count'] == 11
            and transition['added_count'] == 12 and transition['removed_count'] == 0
            and transition['seed_path_count'] == 348 and transition['review_subject_count'] == 211
            and transition['historical_input_count'] == 102
            and delta == actual_delta == checkpoint_paths and len(delta) == 23
            and len({row['path'] for row in delta}) == 23
            and sum(row['before_sha256'] is None for row in delta) == 12
            and sum(row['before_sha256'] is not None for row in delta) == 11
            and all(isinstance(row['after_sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['after_sha256'])
                    for row in delta), 'Require exact11 replacements plus12 additions and no new removal')
    expected_sources.update({row['path']: row['after_sha256'] for row in delta})
    require(expected_sources == target['source_hashes'] and len(expected_sources) == target_binding['source_count'] == 478
            and sum(pg1['source_hashes'].get(p) == sha for p, sha in target['source_hashes'].items()) == 455
            and target['removed_paths'] == current['removed_paths'] == transition['required_removed_paths']
            and target['historical_input_hashes'] == current['historical_input_hashes']
            and len(target['review_subject_paths']) == len(set(target['review_subject_paths'])) == 211
            and set(target['review_subject_paths']) == (set(pg1['review_subject_paths'])
                | {row['path'] for row in delta if row['before_sha256'] is None})
            and len(target['snapshots']) == target_binding['snapshot_count'] == 211,
            'Require the whole immutable target478 source map and211 review subjects, not a selected subset')
    ordinary_bundle = profile['historical_ordinary_source_bundle']
    require(source_checkpoint['status'] == 'PRIVATE_TRANSPORT_CHECKPOINT_NOT_FIX_ACCEPTANCE'
            and source_checkpoint['head'] == ORDINARY_HEAD
            and source_checkpoint['parent'] == ORDINARY_PARENT and source_checkpoint['tree'] == ORDINARY_TREE
            and source_checkpoint['branch'] == BACKEND_BRANCH and source_checkpoint['public_prerequisite'] == PUBLIC_PREREQUISITE
            and source_checkpoint['source_manifest'] == target_binding['path']
            and source_checkpoint['source_manifest_sha256'] == target_binding['sha256']
            and source_checkpoint['source_count'] == 478 and source_checkpoint['development07_seed_keys_preserved'] == 348
            and source_checkpoint['modified_paths'] == 11 and source_checkpoint['newly_tracked_paths'] == 12
            and source_checkpoint['source_bytes_unchanged'] is True and source_checkpoint['clean_worktree'] is True
            and source_checkpoint['public_push_forbidden'] is True and source_checkpoint['integration_changed'] is False
            and source_checkpoint['tests_run'] is False
            and source_checkpoint['bundle'] == ordinary_bundle and ordinary_bundle['bytes'] == 257140
            and safe(authority, ordinary_bundle['path']).stat().st_size == ordinary_bundle['bytes'],
            'Require the historical ordinary checkpoint/bundle, not the new lease transport')
    ordinary_selection = read_json(safe(authority, profile['ordinary_selection']['path']))
    pg01 = read_json(safe(authority, profile['historical_ordinary_source']['path']))
    require(ordinary_selection['schema'] == 'app-29-ordinary-connected-pg-selection-v1'
            and ordinary_selection['source_freeze'] == {k: target_binding[k] for k in ('path', 'sha256')}
            and ordinary_selection['source_hashes'].items() <= target['source_hashes'].items()
            and ordinary_selection['expected_test_count'] == 21 and len(ordinary_selection['expected_tests']) == 21
            and ordinary_selection['task_argv_count'] == len(ordinary_selection['task_args']) == 43
            and pg01['validation_task_args'] == ordinary_selection['task_args']
            and pg01['repositories']['kira-backend'] == {'head': ORDINARY_HEAD, 'branch': BACKEND_BRANCH, 'status': ''}
            and pg01['untracked_paths'] == [] and pg01['source_hashes'] == expected_sources
            and pg01['review_subject_paths'] == target['review_subject_paths']
            and pg01['removed_paths'] == target['removed_paths']
            and pg01['historical_input_hashes'] == target['historical_input_hashes'],
            'Preserve exact immutable PG01 source/selection; its result remains20 PASS/1 FAIL')

    # One bounded new source stage; all pins remain null until primary binds actual compiled/reviewed bytes.
    lease_binding = profile['lease_source_target']
    lease_checkpoint_binding = profile['lease_source_checkpoint']
    for item in (lease_binding, lease_checkpoint_binding, profile['lease_checkpoint_paths']):
        require(manifest['approved_inputs'].get(item['path']) == item['sha256']
                and digest(safe(authority, item['path'])) == item['sha256'], 'New lease source/checkpoint authority missing')
    lease_target = read_json(safe(authority, lease_binding['path']))
    lease_checkpoint = read_json(safe(authority, lease_checkpoint_binding['path']))
    lease_paths = read_json(safe(authority, profile['lease_checkpoint_paths']['path']))
    lease_delta = profile['lease_dispatch_source_delta']
    require(profile['lease_source_stage_status'] == 'BOUND_BY_PRIMARY' and set(lease_delta) == set(LEASE_SOURCE_PATHS)
            and sum(row['before_sha256'] is None for row in lease_delta.values()) == 3
            and all(expected_sources.get(p) == row['before_sha256'] and row['after_sha256'] != row['before_sha256']
                    and isinstance(row['after_sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['after_sha256'])
                    and row['after_sha256'] != '0' * 64 for p, row in lease_delta.items()),
            'Require exact14 replacements plus3 additions, not an unreviewed source delta')
    expected_sources.update({p: row['after_sha256'] for p, row in lease_delta.items()})
    require(lease_paths == [{'path': p, **lease_delta[p]} for p in sorted(lease_delta)]
            and lease_target['schema_version'] == 3
            and lease_target['source_hashes'] == expected_sources
            and len(expected_sources) == lease_binding['source_count']
            and lease_target['removed_paths'] == target['removed_paths']
            and lease_target['historical_input_hashes'] == target['historical_input_hashes']
            and lease_target['inventory_seed_manifest'] == SEED and lease_target['inventory_seed_manifest_sha256'] == SEED_SHA
            and lease_target['inventory_seed_path_count'] == lease_target['inventory_seed_preserved_count'] == 348
            and len(lease_target['review_subject_paths']) == len(set(lease_target['review_subject_paths']))
                == lease_binding['snapshot_count'] == len(lease_target['snapshots'])
            and set(lease_target['review_subject_paths']) <= expected_sources.keys()
            and set(target['review_subject_paths']) <= set(lease_target['review_subject_paths'])
            and {p for p, row in lease_delta.items() if row['before_sha256'] is None} <= set(lease_target['review_subject_paths']),
            'Require the complete actual lease source map and additive inventory; do not invent source/snapshot counts')
    require(lease_checkpoint['status'] == 'PRIVATE_TRANSPORT_CHECKPOINT_NOT_FIX_ACCEPTANCE'
            and lease_checkpoint['head'] == binding['backend_sha'] == LEASE_HEAD
            and lease_checkpoint['parent'] == ORDINARY_HEAD and lease_checkpoint['tree'] == LEASE_TREE
            and lease_checkpoint['branch'] == BACKEND_BRANCH and lease_checkpoint['public_prerequisite'] == PUBLIC_PREREQUISITE
            and lease_checkpoint['source_manifest'] == lease_binding['path']
            and lease_checkpoint['source_manifest_sha256'] == lease_binding['sha256']
            and lease_checkpoint['source_count'] == len(expected_sources) and lease_checkpoint['development07_seed_keys_preserved'] == 348
            and lease_checkpoint['modified_paths'] == 14 and lease_checkpoint['newly_tracked_paths'] == 3
            and lease_checkpoint['source_bytes_unchanged'] is True and lease_checkpoint['clean_worktree'] is True
            and lease_checkpoint['public_push_forbidden'] is True and lease_checkpoint['integration_changed'] is False
            and lease_checkpoint['tests_run'] is False
            and lease_checkpoint['bundle'] == {'path': source_bundle['source_path'], 'sha256': source_bundle['sha256'],
                                              'bytes': source_bundle['bytes']},
            'Require genuine new private source checkpoint/bundle; not historical PG01 or invented preflight data')
    selection = read_json(safe(authority, profile['source_inventory']['path']))
    selected = selection['hosted']
    require(selection['schema'] == 'app-29-lease-dispatch-inert-selection-proposal-v1'
            and selected['focused_class'] == CREATOR_CLASS and selected['focused_noarg_methods'] == list(METHODS[CREATOR_CLASS][:-1])
            and selected['focused_parameterized_method']['method'] == CREATOR_METHOD
            and selected['focused_parameterized_method']['enum_values'] == list(CREATOR_MODES)
            and selected['unchanged_previously_failed_method']['class'] == OWNERSHIP_CLASS
            and selected['unchanged_previously_failed_method']['method'] == METHODS[OWNERSHIP_CLASS][0]
            and selected['expected_test_counts'] == TEST_COUNTS and profile['test_classes'] == list(TEST_COUNTS)
            and selected['expected_test_invocations'] == profile['expected_test_count'] == profile['source_inventory']['expected_test_count'] == 18
            and selected['method_filter_count'] == len(TEST_SELECTORS) == 11 and profile['test_selectors'] == TEST_SELECTORS
            and selected['task_args'] == TASKS and selected['task_argv_count'] == len(TASKS) == 23
            and profile['expected_tests'] == EXPECTED_TESTS
            and sorted(selected['expected_xml_files']) == sorted(profile['expected_xml_files'])
                == sorted('TEST-' + name + '.xml' for name in TEST_COUNTS)
            and selected['shutdown_diagnostics'] == profile['shutdown_diagnostics']
            and expected_sources['src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/OrdinarySourceGrantCleanupOwnershipIT.kt']
                == selected['unchanged_previously_failed_method']['source_sha256'],
            'Require exact11 declarations and18 source-bound invocations; preserve the unchanged failed method')
    provenance = {}
    for predecessor_manifest in (pg1, target):
        for field in ('approved_inputs', 'validation_tooling'):
            for relative, sha in predecessor_manifest[field].items():
                require(relative not in provenance or provenance[relative] == sha, 'Contradictory PG1/target provenance pin')
                provenance[relative] = sha
    require(len(provenance) == 188 and provenance.items() <= manifest['approved_inputs'].items(),
            'Preserve all188 PG1/target approved/tooling provenance pairs')
    for predecessor_manifest in (pg01, lease_target):
        for field in ('approved_inputs', 'validation_tooling'):
            for relative, sha in predecessor_manifest[field].items():
                require(relative not in provenance or provenance[relative] == sha, 'Contradictory PG01/lease provenance pin')
                provenance[relative] = sha
    require(provenance.items() <= manifest['approved_inputs'].items(), 'PG01/lease approved/tooling provenance omitted')
    expected_snapshots = {str(PurePosixPath(MANIFEST_FILE).parent / 'sources' / p): expected_sources[p]
                          for p in lease_target['review_subject_paths']}
    require(manifest['source_hashes'] == expected_sources
            and manifest['removed_paths'] == lease_target['removed_paths']
            and manifest['review_subject_paths'] == lease_target['review_subject_paths']
            and len(manifest['snapshots']) == lease_binding['snapshot_count']
            and manifest['snapshots'] == expected_snapshots, 'Require complete new lease source binding and all fresh snapshots')
    require(manifest['historical_input_hashes'] == current['historical_input_hashes']
            and current['approved_inputs'].items() <= manifest['approved_inputs'].items(),
            'Historical authority or original approved input omitted')
    expected_tooling = {p: sha for p, sha in current['validation_tooling'].items()
                        if p not in current['additional_validation_tooling_paths']}
    require(len(expected_tooling) == 5 and all(expected_tooling == {
                p: sha for p, sha in predecessor_manifest['validation_tooling'].items()
                if p not in predecessor_manifest['additional_validation_tooling_paths']}
                for predecessor_manifest in (pg1, target, pg01, lease_target)), 'Historical and target base tooling must remain identical')
    expected_tooling.update({original: digest(safe(ADMIN, deployed)) for original, deployed in DEPLOYMENTS.items()})
    require(manifest['validation_tooling'] == expected_tooling and len(expected_tooling) == 10
            and len(manifest['additional_validation_tooling_paths']) == 5
            and set(manifest['additional_validation_tooling_paths']) == set(DEPLOYMENTS),
            'Require the unchanged five base tools plus exactly five lease deployment tools')
    require(manifest['approved_inputs'].get(test_binding['proposal_path']) == test_binding['after_sha256']
            and manifest['approved_inputs'].get(test_binding['patch_path']) == test_binding['patch_sha256']
            and all(manifest['approved_inputs'].get(row['proposal_path']) == row['after_sha256'] for row in source_delta.values())
            and all(manifest['approved_inputs'].get(p) == sha
                    for field in ('native_candidate_evidence', 'diagnostic_authority', 'product_lifecycle_authority',
                                  'post_structural_authority', 'selection_authority', 'ordinary_connected_authority', 'lease_dispatch_provenance')
                    for p, sha in profile[field].items()),
            'Missing exact accepted proposals, source/history authority or retained Native05 inputs')
    require(manifest['inventory_seed_manifest'] == SEED and manifest['inventory_seed_manifest_sha256'] == SEED_SHA
            and manifest['inventory_seed_path_count'] == manifest['inventory_seed_preserved_count'] == 348,
            'Complete historical inventory continuity required')
    require(digest(safe(authority, SEED)) == SEED_SHA, 'Seed changed')
    seed = read_json(safe(authority, SEED))
    require(len(seed['source_hashes']) == 348 and seed['source_hashes'].keys() <= manifest['source_hashes'].keys(), 'Seed path omitted')
    proof = checkpoint['local_v3_preflight']
    require(proof['manifest_sha256'] == checkpoint['manifest_sha256']
            and proof['receipt_path'] == LOCAL_PREFLIGHT_FILE
            and proof['tool_sha256'] == 'e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe'
            and digest(safe(authority, proof['receipt_path'])) == proof['receipt_sha256'], 'Unbound local verification receipt')
    receipt = read_json(safe(authority, proof['receipt_path']))
    require(receipt == {'status': 'READ_ONLY_V3_PREFLIGHT_PASSED', 'source_paths': len(manifest['source_hashes'])},
            'Local v3 validation is missing; hosted transport cannot replace it')
    require(all(checkpoint['manifest_path'] not in manifest[field] and proof['receipt_path'] not in manifest[field]
                and 'ci/app29-gate-b.request.json' not in manifest[field]
                and (PAYLOAD / 'checkpoint.json').relative_to(ADMIN).as_posix() not in manifest[field]
                for field in ('snapshots', 'historical_input_hashes', 'approved_inputs', 'validation_tooling')),
            'Fresh manifest must not contain its own receipt, later deployment checkpoint or request')
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
    require(manifest['approved_inputs'].get(PROFILE_FILE) == PROFILE_SHA, 'Sealed development profile missing')
    for key in ('source_inventory', 'core_source_manifest'):
        item = profile[key]
        require(manifest['approved_inputs'].get(item['path']) == item['sha256'], 'Core C2/probes authority missing')
    core = read_json(safe(authority, profile['core_source_manifest']['path']))
    rows = core['source_paths']
    require(core['baseline_head'] == CORE_BASELINE and core['local_only'] is True
            and core['public_push_authorized'] is False and len(rows) == 21
            and len({row['path'] for row in rows}) == 21, 'Wrong closed Core C2 source manifest')
    require([row['sha256'] for row in rows if row['path'] == test_binding['path']] == [test_binding['before_sha256']],
            'Diagnostic test is not based on the original bound C2 source')
    for row in rows:
        sha = test_binding['after_sha256'] if row['path'] == test_binding['path'] else row['sha256']
        require(current['source_hashes'].get(row['path']) == sha, 'Diagnostic baseline changed original Core C2 source')
        if row['path'] in source_delta:
            sha = source_delta[row['path']]['after_sha256']
        if row['path'] in post_delta:
            sha = post_delta[row['path']]['after']
        require(pg1['source_hashes'].get(row['path']) == sha,
                'Historical PG1 source is not exact C2 plus accepted diagnostics, product and structural deltas')
    return {'manifest_sha256': checkpoint['manifest_sha256'], 'sources': len(manifest['source_hashes']),
            'seed_paths': 348, 'local_v3': 'PRIMARY_BOUND_LOCAL_RECEIPT_NOT_HOSTED_REEXECUTION', 'authority_files': len(pins),
            'core_sources': 21, 'snapshots': len(manifest['snapshots']), 'profile': PROFILE_ID,
            'validation_predecessor_sha256': pg1_binding['sha256'], 'historical_pg14_manifest_sha256': validation_predecessor['sha256'],
            'historical_ordinary_target_sha256': target_binding['sha256'], 'historical_ordinary_transition_sha256': transition_binding['sha256'],
            'target_source_manifest_sha256': lease_binding['sha256'], 'source_checkpoint_sha256': lease_checkpoint_binding['sha256'],
            'selection_source_delta_count': len(lease_delta),
            'source_delta': {'changed': 14, 'added': 3, 'unchanged': len(pg01['source_hashes']) - 14, 'removed': 0},
            'historical_pg1_selection_source_delta_count': 0, 'historical_ordinary_selection_source_delta_count': 23,
            'provenance_pairs': len(provenance),
            'candidate_id': profile['final_jar']['candidate_id'], 'candidate_sha256': profile['final_jar']['sha256'],
            'candidate_qualification': 'UNQUALIFIED'}


class Gate:
    def __init__(self, binding):
        require_profile_pins()  # Also refuse direct execute() use while the author pins are unbound.
        from app29_owned_children import OwnedChildren  # Hash checked first; immutable import has no actions.
        self.binding, self.owner = binding, None
        self.start = time.monotonic()
        self.end = self.start + binding['budgets']['controller_seconds']
        self.phase_end = self.start + binding['budgets']['preflight_seconds']
        self.cancelled, self.started, self.clean_daemon, self.events_since = False, False, False, None
        self.run = Path(os.environ['RUNNER_TEMP']) / ('app29-lease-dispatch-pg-01-' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT'])
        self.run.mkdir(mode=0o700, exist_ok=False)
        for name in ('reports', 'gradle', 'w01', 'tmp', 'home', 'project-cache', 'kotlin-cache'):
            (self.run / name).mkdir(mode=0o700)
        self.reports, self.w01 = self.run / 'reports', self.run / 'w01'
        self.result = {'status': 'FAIL', 'gate': GATE, 'backend_sha': binding['backend_sha'],
                       'carrier_sha': os.environ['GITHUB_SHA'], 'commands': [], 'failures': [], 'processes': [],
                       'containers': 'UNKNOWN', 'outputs_absent': False, 'capture_complete': False,
                       'captured_file_hashes': {}, 'owned_output_cleanup': {}, 'diagnostics': {'status': 'NOT_EVALUATED'},
                       'consumer': {'status': 'NOT_EVALUATED', 'scope': 'OUTSIDE_LEASE_DISPATCH_PG_VALIDATION'}}
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
        row = {'stage': stage, 'type': type(error).__name__}
        # Never retain exception text; only translate exact literal require() guards.
        if type(error) is ValueError and len(error.args) == 1 and type(error.args[0]) is str:
            guard = GUARD_IDS.get(error.args[0])
            if guard is not None:
                row['guard'] = guard
        if stage == 'diagnostics' and type(error) is ET.ParseError:
            row['guard'] = 'XML_PARSE'
        self.result['failures'].append(row)

    def attempt(self, stage, action):
        try:
            return action()
        except BaseException as error:
            self.fail(stage, error)
            return None

    def cleanup_outputs(self, root, paths, stage, allowed, skip_reason):
        for relative in paths:
            row = {'cleanup_stage': stage, 'cleanup_attempted': bool(allowed), 'cleanup_complete': False,
                   'cleanup_skipped_reason': None if allowed else skip_reason, 'absent': None}
            self.result['owned_output_cleanup'][str(root / relative)] = row
            if allowed:
                row['cleanup_complete'] = self.attempt(stage, lambda p=relative: (remove_owned(root, p), True)[1]) is True

    def output_absence(self):
        for root, paths in ((BACKEND, CACHE_PATHS), (self.run, ('w01', 'project-cache', 'kotlin-cache', 'gradle', 'tmp', 'home'))):
            for relative in paths:
                row = self.result['owned_output_cleanup'][str(root / relative)]
                row['absent'] = self.attempt('output-absence', lambda r=root, p=relative: not safe(r, p).exists())
        return all(row['absent'] is True for row in self.result['owned_output_cleanup'].values())

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
        trees = [row[5:].decode('ascii') for row in header.split(b'\n') if row.startswith(b'tree ')]
        ordinary = self.command(label + '-ordinary-parent-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', ORDINARY_HEAD], cleaning=cleaning)
        ordinary_header, ordinary_separator, _ = ordinary.partition(b'\n\n')
        ordinary_parents = [row[7:].decode('ascii') for row in ordinary_header.split(b'\n') if row.startswith(b'parent ')]
        ordinary_trees = [row[5:].decode('ascii') for row in ordinary_header.split(b'\n') if row.startswith(b'tree ')]
        structural = self.command(label + '-post-structural-parent-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', ORDINARY_PARENT], cleaning=cleaning)
        structural_header, structural_separator, _ = structural.partition(b'\n\n')
        structural_parents = [row[7:].decode('ascii') for row in structural_header.split(b'\n') if row.startswith(b'parent ')]
        product = self.command(label + '-product-lifecycle-parent-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', PRODUCT_LIFECYCLE_PARENT], cleaning=cleaning)
        product_header, product_separator, _ = product.partition(b'\n\n')
        product_parents = [row[7:].decode('ascii') for row in product_header.split(b'\n') if row.startswith(b'parent ')]
        diagnostic = self.command(label + '-diagnostic-parent-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', DIAGNOSTIC_PARENT], cleaning=cleaning)
        diagnostic_header, diagnostic_separator, _ = diagnostic.partition(b'\n\n')
        diagnostic_parents = [row[7:].decode('ascii') for row in diagnostic_header.split(b'\n') if row.startswith(b'parent ')]
        ancestor = self.command(label + '-private-parent-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', PRIVATE_PARENT], cleaning=cleaning)
        ancestor_header, ancestor_separator, _ = ancestor.partition(b'\n\n')
        ancestor_parents = [row[7:].decode('ascii') for row in ancestor_header.split(b'\n') if row.startswith(b'parent ')]
        previous = self.command(label + '-previous-private-parent-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', PREVIOUS_PRIVATE_PARENT], cleaning=cleaning)
        previous_header, previous_separator, _ = previous.partition(b'\n\n')
        previous_parents = [row[7:].decode('ascii') for row in previous_header.split(b'\n') if row.startswith(b'parent ')]
        core_baseline = self.command(label + '-core-baseline-commit', ['git', '--no-replace-objects', 'cat-file', 'commit', CORE_BASELINE], cleaning=cleaning)
        core_header, core_separator, _ = core_baseline.partition(b'\n\n')
        core_parents = [row[7:].decode('ascii') for row in core_header.split(b'\n') if row.startswith(b'parent ')]
        self.result.setdefault('source_checkout_final', {})[label] = {
            'head': sha, 'branch': branch, 'parents': parents, 'trees': trees,
            'ordinary_parent': {'head': ORDINARY_HEAD, 'parents': ordinary_parents, 'trees': ordinary_trees},
            'post_structural_parent': {'head': ORDINARY_PARENT, 'parents': structural_parents},
            'product_lifecycle_parent': {'head': PRODUCT_LIFECYCLE_PARENT, 'parents': product_parents},
            'diagnostic_parent': {'head': DIAGNOSTIC_PARENT, 'parents': diagnostic_parents},
            'private_parent': {'head': PRIVATE_PARENT, 'parents': ancestor_parents},
            'previous_private_parent': {'head': PREVIOUS_PRIVATE_PARENT, 'parents': previous_parents},
            'core_baseline': {'head': CORE_BASELINE, 'parents': core_parents}}
        require(sha == self.binding['backend_sha'] == LEASE_HEAD and branch == BACKEND_BRANCH
                and separator and parents == [ORDINARY_HEAD] and trees == [LEASE_TREE]
                and ordinary_separator and ordinary_parents == [ORDINARY_PARENT] and ordinary_trees == [ORDINARY_TREE]
                and structural_separator and structural_parents == [PRODUCT_LIFECYCLE_PARENT]
                and product_separator and product_parents == [DIAGNOSTIC_PARENT]
                and diagnostic_separator and diagnostic_parents == [PRIVATE_PARENT]
                and ancestor_separator and ancestor_parents == [PREVIOUS_PRIVATE_PARENT]
                and previous_separator and previous_parents == [CORE_BASELINE]
                and core_separator and core_parents == [PUBLIC_PREREQUISITE],
                'Require exact lease tip/tree ->ccdbb28f ->6db944 ->1c91 ->eb8fed8 ->989a ->926927 ->49da ->public prerequisite, with no merges or extra descendants')
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
        self.result['source_checkout_final'][label]['tracked_path_count'] = len(hashes)
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
        require(len(created) == 3 and sum(r['image'] == 'postgres:17.6-alpine' for r in created.values()) == 2
                and sum(r['image'] == 'testcontainers/ryuk:0.12.0' for r in created.values()) == 1
                and destroyed <= created.keys() and remaining <= created.keys(), 'Incomplete/unexpected container journal')
        pg = [r for r in created.values() if r['image'] == 'postgres:17.6-alpine']
        ryuk = next(r for r in created.values() if r['image'] != 'postgres:17.6-alpine')
        sessions = {row.get('org.testcontainers.sessionId', '') for row in pg}
        require(len(sessions) == 1, 'Both selected class fixtures must belong to the one Test worker session')
        session = sessions.pop()
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


def capture_reports(gate, profile):
    inventory = gate.result['captured_file_hashes']
    build = safe(gate.run, 'w01/backend-build')
    reports = safe(gate.run, 'reports')
    def scan_error(error):
        raise error
    for name in ('test-results', 'reports'):
        source = safe(build, name)
        require(source.is_dir(), 'Required test/report root missing')
        for folder, directories, files in os.walk(source, followlinks=False, onerror=scan_error):
            directories.sort()
            for name in sorted(directories + files):
                path = Path(folder) / name
                require(not path.is_symlink(), 'Report link')
                if path.is_file() and path.suffix in ('.xml', '.txt', '.json', '.log'):
                    relative = path.relative_to(build).as_posix()
                    row = {'bytes': None, 'sha256': None}
                    inventory[relative] = row
                    before = digest(path, 64 * 1024**2)
                    row['bytes'] = path.stat().st_size
                    destination = safe(reports, relative)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, destination)
                    require(digest(destination, 64 * 1024**2) == before == digest(path, 64 * 1024**2), 'Evidence copy drift')
                    row['sha256'] = before
    required = {'test-results/test/TEST-' + name + '.xml' for name in TEST_COUNTS}
    required.add(profile['report_directory'] + '/effective-classpath.txt')
    class_logs = [p for p in inventory if PurePosixPath(p).parent.as_posix() == profile['report_directory']
                  and re.fullmatch(r'class-load-[1-9][0-9]*\.txt', PurePosixPath(p).name)]
    # Presence/copy integrity only; diagnostics below retain actual outcomes, never consumer qualification.
    require(required <= inventory.keys() and class_logs, 'Required raw evidence inventory missing')
    return True


def diagnostics(reports, profile, java):
    xmls = list((reports / 'test-results/test').glob('*.xml'))
    expected_files = ['TEST-' + name + '.xml' for name in TEST_COUNTS]
    require(sorted(p.name for p in xmls) == sorted(expected_files) == sorted(profile['expected_xml_files']),
            'Wrong diagnostic XML inventory')
    expected = [(row['class'], row['display_name']) for row in EXPECTED_TESTS]
    require(profile['expected_test_count'] == 18 and profile['test_classes'] == list(TEST_COUNTS)
            and profile['expected_witnesses'] == [] and profile['expected_tests'] == EXPECTED_TESTS,
            'Require exactly the18 fixed lease-dispatch source identities')
    identities, outcomes, suites, suite_results = [], [], [], []
    for name, count in TEST_COUNTS.items():
        path = safe(reports, 'test-results/test/TEST-' + name + '.xml')
        digest(path, 64 * 1024**2)
        raw = path.read_text(encoding='utf-8-sig')
        require('\x00' not in raw and '<!DOCTYPE' not in raw.upper() and '<!ENTITY' not in raw.upper(), 'Unsafe XML')
        suite = ET.fromstring(raw)
        cases = suite.findall('testcase')
        actual = [(case.get('classname'), case.get('name')) for case in cases]
        required = [(row['class'], row['display_name']) for row in EXPECTED_TESTS if row['class'] == name]
        require(suite.tag == 'testsuite' and suite.get('name') == name and suite.get('tests') == str(count)
                and len(cases) == count and sorted(actual) == sorted(required),
                'Missing, extra or duplicate diagnostic testcase')
        suite_outcomes = []
        for case in cases:
            states = [state for tag, state in (('failure', 'FAIL'), ('error', 'ERROR'), ('skipped', 'SKIP')) if case.find(tag) is not None]
            require(len(states) <= 1, 'Contradictory diagnostic testcase outcome')
            suite_outcomes.append({'class': case.get('classname'), 'display_name': case.get('name'),
                                   'status': states[0] if states else 'PASS'})
        suite_counts = {state: sum(row['status'] == state for row in suite_outcomes) for state in ('PASS', 'FAIL', 'ERROR', 'SKIP')}
        require(all(suite.get(field) == str(suite_counts[state]) for field, state in
                    (('failures', 'FAIL'), ('errors', 'ERROR'), ('skipped', 'SKIP'))), 'Diagnostic XML count mismatch')
        identities.extend(actual)
        outcomes.extend(suite_outcomes)
        suites.append(suite)
        suite_results.append({'class': name, 'tests': count, 'counts': suite_counts})
    require(len(identities) == len(set(identities)) == 18 and sorted(identities) == sorted(expected),
            'Missing, extra or duplicate diagnostic testcase')
    counts = {state: sum(row['status'] == state for row in outcomes) for state in ('PASS', 'FAIL', 'ERROR', 'SKIP')}
    phases = ('BEFORE_SHUTDOWN', 'AFTER_SHUTDOWN', 'OBSERVATION_FAILED')
    scalars = set(('budget_remaining_ms invocation_result first_close observation actor_capacity actor_retained '
                   'actor_constructing actor_retired actor_factory_sealed actor_fault future_lease_entries active_operations '
                   'close_queue_size close_pool_size close_active_count close_completed_tasks close_shutdown close_terminated').split())
    records = []
    for suite in suites:
        for output in (*suite.iter('system-out'), *suite.iter('system-err')):
            for line in (output.text or '').splitlines():
                if not line.startswith('OWNED_CUT_SHUTDOWN_DIAGNOSTIC'):
                    continue
                tokens = line.split()
                pairs = [token.split('=', 1) for token in tokens[1:]]
                require(tokens[0] == 'OWNED_CUT_SHUTDOWN_DIAGNOSTIC' and all(len(pair) == 2 for pair in pairs),
                        'Malformed fixed diagnostic record')
                fields = unique(pairs)
                require(fields.get('case') in DIAGNOSTIC_CASES and fields.get('phase') in phases
                        and fields.get('status') in ('CAPTURED', 'UNAVAILABLE')
                        and fields.keys() == {'case', 'phase', 'status'} | (scalars if fields.get('status') == 'CAPTURED' else set())
                        and all(re.fullmatch(r'[A-Z][A-Z0-9_]*|-?[0-9]+|true|false', value) for value in fields.values()),
                        'Wrong fixed diagnostic labels or scalar fields')
                records.append({'raw': line, 'fields': fields})
    require(profile['shutdown_diagnostics'] == {'status': 'NOT_APPLICABLE', 'expected_record_count': 0}
            and not records, 'PG14 fixed diagnostic rows are nonapplicable to this selection')
    coverage = {}  # No required PG14 case/phase slots in either selected suite.
    folder = safe(reports, profile['report_directory'])
    cp = read_json(folder / 'effective-classpath.txt')
    require(cp['profile'] == PROFILE_ID and cp['java_home'] == str(java)
            and cp['source_inventory'] == profile['source_inventory'] and cp['expected_test_count'] == 18
            and cp['expected_witnesses'] == [], 'Wrong actual diagnostic classpath/profile/JDK')
    entries = cp['entries']
    require(len({e['path'] for e in entries}) == len(entries)
            and cp['removed_stock']['sha256'] == profile['removed_stock']['sha256']
            and cp['removed_stock']['path'] not in {e['path'] for e in entries}, 'Stock/duplicate classpath supplier')
    for key, flag in (('final_jar', 'postgres_classes'), ('checker', 'checker_classes')):
        rows = [e for e in entries if e[flag] > 0]
        require(len(rows) == 1 and rows[0]['path'] == str(safe(ADMIN, profile[key]['path']))
                and rows[0]['sha256'] == profile[key]['sha256'], 'Wrong explicit class supplier')
    return {'status': 'RECORDED', 'test_status': 'PASS' if counts == {'PASS': 18, 'FAIL': 0, 'ERROR': 0, 'SKIP': 0} else 'FAIL',
            'tests': 18, 'classes': TEST_COUNTS, 'identities': sorted(identities), 'outcomes': outcomes, 'counts': counts,
            'suites': suite_results, 'profile': PROFILE_ID, 'fixed_scalar_capture': 'NOT_APPLICABLE',
            'raw_shutdown_diagnostics': records, 'diagnostic_coverage': coverage,
            'diagnostic_limit': profile['shutdown_diagnostics_note'], 'diagnostic_scope': profile['shutdown_diagnostics'],
            'historical_pg14_result': profile['historical_pg14_result'], 'historical_pg10_result': profile['historical_pg10_result'],
            'historical_pg1_result': profile['historical_pg1_result'], 'accepted_linux03_result': profile['accepted_linux03_result'],
            'historical_ordinary_result': profile['historical_ordinary_result'],
            'historical_result': profile['historical_result'], 'historical_diagnostics_result': profile['historical_diagnostics_result'],
            'candidate_qualification': 'UNQUALIFIED'}


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
        profile = read_json(safe(ADMIN, PROFILE_FILE))
        require(profile['profile_id'] == PROFILE_ID and profile['task_args'] == TASKS
                and profile['expected_test_count'] == 18 and profile['expected_witnesses'] == []
                and profile['test_selectors'] == TEST_SELECTORS
                and profile['expected_tests'] == EXPECTED_TESTS and profile['test_classes'] == list(TEST_COUNTS)
                and profile['shutdown_diagnostics'] == {'status': 'NOT_APPLICABLE', 'expected_record_count': 0}
                and profile['final_jar']['qualification'] == 'UNQUALIFIED',
                'Wrong exact18 lease-dispatch profile/task/candidate scope')
        gate.result['historical_result'] = profile['historical_result']
        gate.result['historical_diagnostics_result'] = profile['historical_diagnostics_result']
        gate.result['historical_pg14_result'] = profile['historical_pg14_result']
        gate.result['historical_pg10_result'] = profile['historical_pg10_result']
        gate.result['historical_pg1_result'] = profile['historical_pg1_result']
        gate.result['accepted_linux03_result'] = profile['accepted_linux03_result']
        gate.result['historical_ordinary_result'] = profile['historical_ordinary_result']
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
                     '--init-script', str(safe(ADMIN, PROFILE_INIT)), *TASKS], seconds=binding['budgets']['validation_seconds'])
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
            gate.result['capture_complete'] = gate.attempt('capture-reports', lambda: capture_reports(gate, profile)) is True
            if gate.result['capture_complete']:
                gate.result['diagnostics'] = gate.attempt('diagnostics', lambda: diagnostics(gate.reports, profile, gate.java)) or {'status': 'FAIL'}
            def postflight():
                require(baseline is not None and gate.sources('after', cleaning=True) == baseline, 'Effective source changed')
                require(request() == binding, 'Initially accepted request changed')
                gate.result['source_binding_after'] = bind_freeze(binding, profile)
                require(local is not None and all(digest(safe(gate.w01, p)) == sha for p, sha in local.items()), 'Private dependency input drift')
                require(jdk is not None and all(digest(safe(gate.java, p)) == sha for p, sha in jdk.items()), 'JDK input drift')
            gate.result['inputs_preserved'] = gate.attempt('postflight', lambda: (postflight(), True)[1]) is True
        before_file_cleanup = workers_gone and containers_gone and gate.drain('before-file-cleanup')
        files_safe = before_file_cleanup and gate.result['capture_complete']
        file_skip = ('AFTER_IMMEDIATE_STOP_NOT_ABSENT' if not workers_gone else
                     'CONTAINER_CLEANUP_NOT_ABSENT' if not containers_gone else
                     'BEFORE_FILE_CLEANUP_NOT_ABSENT' if not before_file_cleanup else
                     'CAPTURE_INCOMPLETE' if not gate.result['capture_complete'] else None)
        gate.cleanup_outputs(BACKEND, CACHE_PATHS, 'backend-output-cleanup', files_safe, file_skip)
        gate.cleanup_outputs(gate.run, ('w01', 'project-cache', 'kotlin-cache'), 'private-output-cleanup', files_safe, file_skip)
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
        home_skip = (file_skip if not files_safe else
                     'AFTER_FINAL_STOP_NOT_ABSENT' if not final_children else
                     'FINAL_CONTAINER_CENSUS_NOT_ABSENT' if final_containers is not True else
                     'BEFORE_HOME_CLEANUP_NOT_ABSENT' if not after_commands else None)
        gate.cleanup_outputs(gate.run, ('gradle', 'tmp', 'home'), 'private-home-cleanup', home_safe, home_skip)
        gate.result['outputs_absent'] = gate.attempt('output-absence', gate.output_absence) is True
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
                  and gate.result.get('diagnostics', {}).get('test_status') == 'PASS'
                  and gate.result['diagnostics'].get('fixed_scalar_capture') == 'NOT_APPLICABLE' and gate.result['containers'] == 'NORMAL_ABSENT'
                  and all(r['outcome'] == 'NORMAL' for r in gate.result['commands']) and final_containers is True)
        gate.result['status'] = 'PASS' if passed else 'FAIL'
        gate.result['limitation'] = 'Only focused17 lease-dispatch invocations plus the unchanged former failed OwnershipIT method are selected:11 declaration filters/18 cases. Intended identities are not observed passes. Historical PG01 remains20 PASS/1 FAIL and its actor/queue mechanism is unmeasured; a later PASS does not establish that historical cause. Registered-tail faults do not cover an absent unregistered tail; MODEL fatal/ClientInfo and declared-stream limits remain. Negative child exit23 is PROCESS_ONLY product_end=false, never product disposal. PG14 diagnostics are NOT_APPLICABLE here; original records remain separate. Historical Linux03 carries only56 nonDB/compile/Ktlint, with bounded prior Detekt reuse, and PG1/PG14/PG10 results remain unchanged. Preserve raw kill/die events: NORMAL_ABSENT is not graceful-shutdown or zero-kill proof. UNKNOWN grants no retry authority. Native05 UNQUALIFIED; full47/consumer/opaque/liveness/W03/full-P3/production/new-data and installation recovery remain open; W06 excluded. No integration or public private-ancestry push authority.'
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
