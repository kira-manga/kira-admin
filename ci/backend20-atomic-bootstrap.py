"""Private Backend22 COMPARE-only derivative; source pinned, request NOT authorized.

Exactly one normal signed-fixture comparison plus the configured test-source Ktlint check.
The accepted TEST-ONLY fixture is input, never an export/copy target. No App validation,
deployment or issue closure is claimed. Legacy backend20* carrier names remain unchanged.
Primary must independently review/bind tooling, authorize one request, and hold the existing
host-local batch.lock through collection/cleanup; this VM does not claim that lock.
"""
import hashlib, json, os, re, shutil, signal, subprocess, tarfile, time
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

# Exact primary-supplied public source checkpoint; this literal is not launch authorization.
EXPECTED_BACKEND_SHA = '9eb41c547f1c3f979148539eca00699af2cbe4c3'
if (not isinstance(EXPECTED_BACKEND_SHA, str) or
        not re.fullmatch('[0-9a-f]{40}', EXPECTED_BACKEND_SHA) or EXPECTED_BACKEND_SHA == '0' * 40):
    raise SystemExit('UNBOUND Backend22 comparison source checkpoint; no request/output/helper/workload permitted')
PHASE = 'COMPARE'
EXPORT_RESULT_REVIEW_SHA = '0f0220d8f8a876a9cda91ce7464842b6a4fdf1db7770172da893c61f958b8ca7'
FIXTURE_ADMISSION_RECEIPT_SHA = '6c790d0ea99d4c7a12f7cc253c7c7bd93c2694abd1c3ae2eb2957f8acb938bee'
EXPECTED_FIXTURE_SHA = 'cfe2375bec17a9e137b373262cffb97a455d6e9a03f84dcbd4cdfca2eb018b65'
GENERATE_ENV = 'KIRA_BACKEND22_GENERATE_FIXTURE'
FIXTURE_RESOURCE = 'fixtures/bootstrap-v2-v6-signed.json'

ADMIN = Path(__file__).resolve().parent.parent
BACKEND = ADMIN.parent / 'backend'
REQUEST_PATH = ADMIN / 'ci/backend20-atomic-bootstrap.request.json'
TARGETS = json.loads(REQUEST_PATH.read_text())
if (set(TARGETS) != {'authorization', 'authorized', 'runAllowed', 'backend_sha', 'classes', 'methods', 'status'} or
        TARGETS.get('authorization') != 'BACKEND22_ONE_TARGETED_BATCH_AUTHORIZED' or
        TARGETS.get('authorized') is not True or TARGETS.get('runAllowed') is not True or
        TARGETS.get('status') != 'PRIMARY_BOUND_COMPARE' or TARGETS.get('backend_sha') != EXPECTED_BACKEND_SHA):
    raise SystemExit('Disabled, unbound or wrong-phase Backend22 comparison request; no outputs/helpers permitted')
CLASSES, METHODS = TARGETS['classes'], TARGETS['methods']
RUN = Path(os.environ['BACKEND20_RUN'])
RUN.mkdir(mode=0o700, exist_ok=False)
REPORTS, HOME, W01, TEMP = (RUN / n for n in ('reports', 'gradle', 'w01', 'tmp'))
for directory in (REPORTS, HOME, W01, TEMP): directory.mkdir(mode=0o700)
ENV = dict(os.environ, GRADLE_USER_HOME=str(HOME), W01_RUN=str(W01), TMPDIR=str(TEMP),
           JAVA_TOOL_OPTIONS=f'-Djava.io.tmpdir={TEMP}', DOCKER_HOST='unix:///var/run/docker.sock')
# Generation is absent from every command, including the selected Test and both same-home stops.
ENV.pop(GENERATE_ENV, None)
CANDIDATE_BUILD = BACKEND / 'build'  # Forbidden producer root: comparison never creates, adopts, copies or deletes it.
EXPECTED_FIXTURE_PATH = BACKEND / 'src/test/resources' / FIXTURE_RESOURCE

# One exact comparison only; no export counterpart, ordinary11 repeat or whole-class selector.
EXPECTED_CLASSES = {
    'me.manga.kira.backend.sourceconfig.public.BootstrapSignedCatalogFixtureIT': 1,
}
EXPECTED_METHODS = {
    'me.manga.kira.backend.sourceconfig.public.BootstrapSignedCatalogFixtureIT': [
        'bootstrapMatchesCommittedFixture',
    ],
}
EXPECTED_CASES = {
    'me.manga.kira.backend.sourceconfig.public.BootstrapSignedCatalogFixtureIT': [
        'bootstrapMatchesCommittedFixture()',
    ],
}
# Prior52 named pins: only the whitespace-corrected Kotlin hash changes; admitted fixture adds pin53.
EXPECTED_SOURCE_SHA256 = {
    '.editorconfig': 'ecc589d2ee57adaacd3e951b625a6f4ad31f6ebc41f354e332cf0b9b39f2c6cd',
    'AGENTS.md': 'e65987b4aacc4b090d2cc3e3bcba040d56fefae4c0357afef3588b323f59f7b9',
    'README.md': '6e61bfbc8fcb87976b68b081a916f7a8f7399377abb1ae1b03f5a387ae50151a',
    'build.gradle.kts': '8b6116173f5a5fd76de7c9654685754631e2df1a480a692082995b3122fb7aa0',
    'config/detekt/detekt.yml': '509eb13c3915934d49a3de84dcb5332ff372deee0326c6aaceeed4c2a0b38760',
    'docs/LOCAL_DEV.md': 'b17f1680b045d33d8420b2c64ba5f00ddff57d10c4ab9be46dc1a16a3ad8a5aa',
    'docs/MIGRATION_BUNDLED_TO_REMOTE.md': 'a688796bea719124b77ca3266dea202863252915d3092d3ff72e3bcddc419d08',
    'docs/PLAN.md': 'a4023a9a1c488075db2379a6a40b967dffde00aea778f84f3b5d2ff878da21c6',
    'docs/SOURCE_CONFIG_LIFECYCLE.md': '8dff875d302a67667858fc0669a4947b80f2d12f3aa9853100c0deffbe5c46ae',
    'docs/SOURCE_DOCUMENT_SIGNING.md': 'be9f52ebb202a66cce2adf070affcc1c462be88389afa8b8d7f833674c99aa6f',
    'docs/USAGE.md': 'b9987018093ceacf036ba006617bcd1dc5138dafa4c2b6bfa837a9de095c54f9',
    'gradle.lockfile': '5e4078d2b0dff054871f67fc58b2349ab28b2c79d703ce541a5c9a9b2b50605f',
    'gradle/libs.versions.toml': '041f4429eef81414ad3ede5825d570d1e1f8790fd8014332c9355a3a2177a120',
    'gradle/wrapper/gradle-wrapper.jar': '7d3a4ac4de1c32b59bc6a4eb8ecb8e612ccd0cf1ae1e99f66902da64df296172',
    'gradle/wrapper/gradle-wrapper.properties': '89032df14851e71a09ea7eaaffde8c85d3e806cb5365bd747ae9ec843dcae1dd',
    'gradlew': 'b187b4c52e749f5760afdd6fadc31b2a98ad35fb249bf0dff03b72650f320409',
    'settings.gradle.kts': 'f2ffbdad8a2e99edd1b87d7b03d66e669ea2e1965bde5abab10d630d50841044',
    'src/main/kotlin/me/manga/kira/backend/config/ClockConfig.kt': '6fc237a25dc359abf91fb96507809c5e04254af11e6f1ce272e03e701ba572f1',
    'src/main/kotlin/me/manga/kira/backend/config/KiraConfigProperties.kt': '003d8c331f896e0d62cc7decffc2ce9946c4fc2ea452b3c245954eccf9aa53e3',
    'src/main/kotlin/me/manga/kira/backend/security/JwtService.kt': '5d81bc94df2f1a28337220ab99151002c10045879a690267bdc65b412090ecc0',
    'src/main/kotlin/me/manga/kira/backend/security/SecurityConfig.kt': 'f421d64ce0aea32b7d9e95c6624ebd9c62bd3a09e69838c652252ce7b99ffb60',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/application/DocumentAssemblyService.kt': '1dce418396abe743a70a2a1156cb843978883a6629e3030cf73aadd3a85e885f',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/application/GenericV2CutoverService.kt': '33c118e558fdd8ab8230e068c5445dd1ca0527bdf3059ab51cf65433631d6f01',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/domain/InitialSourceCatalogPolicy.kt': '23d53cc1ee42ef25c31f1a887938c269076416ff9839ae7b9919fbb3fea46966',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/ClasspathInitialSourceCatalogPolicy.kt': '78d3767b580c3df392f8a54654b9ed5442a92da40d6e2a3c5026110915a40e60',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/RevisionFloorStartupValidator.kt': '06157babfda0a6a3d6f6416775bd35b170fb796667efd89178e76be02edc113a',
    'src/main/resources/db/migration/V10__source_catalog_v2.sql': '02861602565a779ba3c135f353b658fcdb70921e813cd55c840aac8f6b868d41',
    'src/main/resources/db/migration/V11__source_editor_drafts.sql': 'd07498dea1167916b539733d0087539438377b73399ecb816120b8b10258e268',
    'src/main/resources/db/migration/V12__admin_step_up_grants.sql': '83ba1521125518bb6c81a3fccf390f73ad1ceba2e758ebb6cfb2cb79c8d08073',
    'src/main/resources/db/migration/V13_1__user_credential_version.sql': '08086569e570276c2bad7184a1a2cc70410d1d07c7a6eed57563f51c01f4575e',
    'src/main/resources/db/migration/V13_2__source_catalog_bootstrap_state.sql': 'f3b283507efe057ff15516060c02b27908449f60ab7a03f757a2747d75930045',
    'src/main/resources/db/migration/V13__source_changesets.sql': '2860a22d36a52c4f3b79c30704aa8a9dea6bcf554a0dde5c255529ca778eaa60',
    'src/main/resources/db/migration/V1__users.sql': '258b001e00c9e196d6a03f41a12ac5c3114cb026b886f00a9eb0c06c5aabfa3f',
    'src/main/resources/db/migration/V2__source_config.sql': '62be7c7851b1726041bf20c4dd6b94d4ce84f942d8610c7c9cb5dd66a597e3c2',
    'src/main/resources/db/migration/V3__published_documents.sql': 'e1c3681df987f70e9f71402212c6219d469581b811fbc7c68958d0fb5b51bd23',
    'src/main/resources/db/migration/V4__audit_log.sql': 'e53c6125b720b3adf73584a1a804869caf69c003504e0e10766ab496b6423204',
    'src/main/resources/db/migration/V5__completions.sql': '34f863306aa47d138c9c6971a70d32c22f4928b7d39d60d4b45f1410f39ac6c5',
    'src/main/resources/db/migration/V6__completion_retention.sql': '90dfc7a272cac558b87c495519275e1437ecbc38a0fae0364d7e981f4183d1cc',
    'src/main/resources/db/migration/V7__signed_published_documents.sql': 'd6ddaa2b248598e34e507544e9426be86a7c6740e806a00ed32154f4a9fee243',
    'src/main/resources/db/migration/V8__enforce_completion_result_xor.sql': '3bb5490732cd45fb7fa97420a31cd5d9ff57b4690a7447a3b6f5b97bc60b13ea',
    'src/main/resources/db/migration/V9__tutorials.sql': '03a61db889326d7b7893904ab2914f4d667228d3d42853cfe16ec324a1186ea2',
    'src/main/resources/source-config/bootstrap/app-bundle-v6-generic.json': '42a26ca29182a0c8c1150196ff55979fc41a8d828ed60556e9dcf6062b8b9095',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/InitialSourceCatalogFixtures.kt': '07e729dd897ba0899d086f8b2b1b2f5b6ec8aa3a87c582dd3e9f928cefa77bab',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/InitialSourceCatalogFixturesTest.kt': '947db836a03a6f17fb966b43c937bf17bba7381362884b8459badc9e01ada396',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/StartupConsistencyIT.kt': '1ed4070a137a5555dd3a5796ed233a6e03c6446d1b4bc66596474b729b1390dc',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/AbstractAdminSourceIT.kt': '757ca4c2c54b59365259340f245c8ddef523bea6aa9a728c09d35b6dc875f212',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/BootstrapEndpointIT.kt': 'f38c37fcbe3ddd6022d8699d9e358405f1af88d07f7cbe3ab2b1b402a5df0fd5',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/FullBundledParityIT.kt': '35c1a00ae1359ba64ae90feb4ce4c3269786c1186759369258abf8b6dc3e84e7',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/BootstrapSignedCatalogFixtureIT.kt': '4756e1f21e6deeca4a14c729870f816a12cd2eea2816d7731fdc576ff53cb3a7',
    'src/test/kotlin/me/manga/kira/backend/support/AbstractIntegrationTest.kt': 'b39a14d78dcfe1385b03e69d56b7aa7f4b45b7a3c48b0b5e6970154231a21496',
    'src/test/resources/application-test.yml': 'af538d332c0dd2b05a7d555b28f434d5e8d3ac445810e1a22a83bffaabc7f17e',
    'src/test/resources/fixtures/bootstrap-v2-v6-signed.json': 'cfe2375bec17a9e137b373262cffb97a455d6e9a03f84dcbd4cdfca2eb018b65',
    'src/test/resources/fixtures/bundled-full.json': '1aa86aac2f1ac4aa1fb2b7e3770617b0f364d699bfdd5e14788d6c3d71c9643c',
}
REFERENCE_RESOURCE = 'source-config/bootstrap/app-bundle-v6-generic.json'
REFERENCE_SHA = '42a26ca29182a0c8c1150196ff55979fc41a8d828ed60556e9dcf6062b8b9095'
# This small extra init leaves the pinned dependency/ownership helper unchanged. It witnesses
# the actual test task's classpath before its selected tests, not a Boot jar or provider run.
REFERENCE_INIT = r'''import groovy.json.JsonOutput
import java.net.URLClassLoader
import java.nio.file.Files
import java.security.MessageDigest
import org.gradle.api.tasks.testing.Test
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension

gradle.projectsEvaluated {
    def p = gradle.rootProject
    p.tasks.named('test', Test).configure {
        extensions.getByType(JacocoTaskExtension).enabled = false
        workingDir = p.projectDir
        systemProperty 'junit.jupiter.execution.parallel.enabled', 'false'
        doFirst {
            def resource = '@REFERENCE_RESOURCE@'
            def expected = '@REFERENCE_SHA@'
            def fixture = 'fixtures/bootstrap-v2-v6-signed.json'
            def expectedFixture = '@EXPECTED_FIXTURE_SHA@'
            def fixtureSource = p.file('src/test/resources/' + fixture).absoluteFile
            def fixtureProcessed = new File(p.layout.buildDirectory.get().asFile, 'resources/test/' + fixture).absoluteFile
            def generateName = 'KIRA_BACKEND22_GENERATE_FIXTURE'
            def source = p.file('src/main/resources/' + resource).canonicalFile
            def processed = new File(p.layout.buildDirectory.get().asFile, 'resources/main/' + resource).canonicalFile
            def urls = classpath.files.collect { it.toURI().toURL() } as URL[]
            def digest = { bytes -> MessageDigest.getInstance('SHA-256').digest(bytes).encodeHex().toString() }
            def receipt = [test_task: path, resource: resource, expected_sha256: expected,
                source_path: source.path, processed_path: processed.path,
                classpath: urls.collect { it.toExternalForm() }, accepted: false,
                phase: 'COMPARE', project_directory: p.projectDir.canonicalPath,
                working_directory: workingDir.canonicalPath, max_parallel_forks: maxParallelForks,
                fork_every: forkEvery, max_heap_size: maxHeapSize,
                junit_parallel_enabled: systemProperties['junit.jupiter.execution.parallel.enabled'],
                generation_environment_present: environment.containsKey(generateName),
                generation_environment_value: environment[generateName],
                expected_fixture_sha256: expectedFixture,
                expected_fixture_source_path: fixtureSource.path, expected_fixture_processed_path: fixtureProcessed.path,
                expected_fixture_source_regular: fixtureSource.isFile() && !Files.isSymbolicLink(fixtureSource.toPath()),
                expected_fixture_processed_regular: fixtureProcessed.isFile() && !Files.isSymbolicLink(fixtureProcessed.toPath())]
            def loader = new URLClassLoader(urls, (ClassLoader) null)
            try {
                receipt.source_sha256 = digest(source.bytes)
                receipt.processed_sha256 = digest(processed.bytes)
                def resources = Collections.list(loader.getResources(resource))
                receipt.resolved_resources = resources.collect { it.toExternalForm() }
                def fixtureResources = Collections.list(loader.getResources(fixture))
                receipt.expected_fixture_resources = fixtureResources.collect { it.toExternalForm() }
                receipt.expected_fixture_source_sha256 = digest(fixtureSource.bytes)
                receipt.expected_fixture_processed_sha256 = digest(fixtureProcessed.bytes)
                if (fixtureResources.size() == 1) {
                    receipt.expected_fixture_loaded_sha256 = fixtureResources[0].openStream().withCloseable { digest(it.bytes) }
                }
                if (resources.size() == 1) {
                    receipt.loaded_sha256 = resources[0].openStream().withCloseable { digest(it.bytes) }
                }
                receipt.accepted = receipt.source_sha256 == expected && receipt.processed_sha256 == expected &&
                    receipt.loaded_sha256 == expected && receipt.resolved_resources == [processed.toURI().toURL().toExternalForm()] &&
                    receipt.working_directory == receipt.project_directory && receipt.max_parallel_forks == 1 &&
                    receipt.fork_every == 0 && receipt.max_heap_size == '512m' && receipt.junit_parallel_enabled == 'false' &&
                    !receipt.generation_environment_present && receipt.generation_environment_value == null &&
                    receipt.expected_fixture_source_regular && receipt.expected_fixture_processed_regular &&
                    receipt.expected_fixture_source_sha256 == expectedFixture && receipt.expected_fixture_processed_sha256 == expectedFixture &&
                    receipt.expected_fixture_loaded_sha256 == expectedFixture &&
                    receipt.expected_fixture_resources == [fixtureProcessed.toURI().toURL().toExternalForm()]
                if (!receipt.accepted) throw new GradleException('Backend22 comparison reference/configuration/fixture-resource mismatch')
            } finally {
                try { loader.close() } finally {
                    new File(System.getenv('W01_RUN'), 'bootstrap-reference-resource.json').text = JsonOutput.prettyPrint(JsonOutput.toJson(receipt)) + '\n'
                    println('BACKEND20_BOOTSTRAP_REFERENCE ' + JsonOutput.toJson(receipt))
                }
            }
        }
    }
}
'''.replace('@REFERENCE_RESOURCE@', REFERENCE_RESOURCE).replace('@REFERENCE_SHA@', REFERENCE_SHA).replace('@EXPECTED_FIXTURE_SHA@', EXPECTED_FIXTURE_SHA)
OWNED_CHILDREN_SHA = '56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385'
PREFIX = 'review/working/app-29-w01-local-dependencies-20260905/'
ARCHIVE_SHA = 'da94218f74eb0f5831241c8606c8f82142e49b818acfaff027a78f2efe77faab'
MANIFEST_SHA = 'c67fcc5fe64a9a795373c4683c7c1edd6407146e3cd07609fa7018a8a98db79a'
INIT_SHA = '429961b98254b89f7ce1d7ba1efa61b8cba28a3bae35353bf3a8ba85f4a1c839'

def note(message):
    print(message, flush=True)
    with (REPORTS / 'result.log').open('a') as log: log.write(message + '\n')

OWNER, CANCELLED, DRAINS = None, False, []
def interrupted(signum, frame):
    global CANCELLED
    CANCELLED = True  # Do not interrupt Popen construction/registration or the finite cleanup phase.
signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)

# Observe actual available bytes, not total capacity or a guessed alternate Docker daemon.
MIN_FREE_BYTES, SPACE_POLL_SECONDS = 8 * 1024**3, 1.0
SPACE_PATHS = [BACKEND, RUN, REPORTS, HOME, W01, TEMP]
SPACE_FAILURE, SPACE_CHECKS, SPACE_NEXT = None, 0, 0.0
SPACE_MINIMUM = {}

def space_ok(phase, force=False):
    global CANCELLED, SPACE_FAILURE, SPACE_CHECKS, SPACE_NEXT
    if SPACE_FAILURE is not None: return False  # Failure stays sticky through cleanup.
    now = time.monotonic()
    if not force and now < SPACE_NEXT: return True
    SPACE_NEXT = now + SPACE_POLL_SECONDS
    observation = {'phase': phase, 'monotonic': now, 'floor_bytes': MIN_FREE_BYTES, 'devices': {}}
    failure = None
    try:
        for path in SPACE_PATHS:
            info = path.stat()
            if not path.is_dir(): raise OSError('Space-observation path is not a directory')
            device = str(info.st_dev)
            if device not in observation['devices']:
                fs = os.statvfs(path)
                free = fs.f_bavail * fs.f_frsize
                observation['devices'][device] = {'available_bytes': free, 'paths': []}
                SPACE_MINIMUM[device] = min(SPACE_MINIMUM.get(device, free), free)
                if free < MIN_FREE_BYTES:
                    failure = {'reason': 'below-eight-GiB', 'phase': phase, 'device': device, 'available_bytes': free}
            observation['devices'][device]['paths'].append(str(path))
    except OSError as problem:
        failure = {'reason': 'space-measurement-unavailable', 'phase': phase, 'error_type': type(problem).__name__, 'errno': problem.errno}
    SPACE_CHECKS += 1
    observation['failure'] = failure
    try:
        with (REPORTS / 'disk-space.jsonl').open('a') as log: log.write(json.dumps(observation, sort_keys=True) + '\n')
    except OSError as problem:
        failure = {'reason': 'space-evidence-unavailable', 'phase': phase, 'error_type': type(problem).__name__, 'errno': problem.errno}
    if failure is not None:
        SPACE_FAILURE, CANCELLED = failure, True  # Existing cancellation/drain/finally path owns stopping.
    return SPACE_FAILURE is None

def drain(name):
    global cleanup_failed
    try: receipt = OWNER.drain() if OWNER is not None else {'ok': False, 'spawned': False, 'reason': 'subreaper/child-list capability not established'}
    except (Exception, KeyboardInterrupt) as failure: receipt = {'ok': False, 'error': str(failure)}
    DRAINS.append({'phase': name, **receipt})
    note(name + ': ' + json.dumps(receipt, sort_keys=True))
    # Successful forced cleanup is not proof that a validation worker ended normally.
    normal = receipt['ok'] and not receipt.get('term') and not receipt.get('kill')
    cleanup_failed |= not normal
    return receipt['ok']  # Actual absence still permits safe scoped deletion on a failed batch.

def command(argv, name, seconds=30, extra=None, cleaning=False):
    global started
    with (REPORTS / 'commands.log').open('a') as log: log.write(json.dumps({'argv': argv, 'cwd': str(BACKEND), 'seconds': seconds, 'env_overrides': extra}) + '\n')
    # Refuse a new workload before Popen; cleanup remains possible after cancellation/low space.
    if not cleaning and (not space_ok('prelaunch-' + name, force=True) or CANCELLED):
        reason = 'disk_floor' if SPACE_FAILURE is not None else 'cancelled'
        result = 125 if reason == 'disk_floor' else 124
        (REPORTS / (name + '.log')).write_text('NOT SPAWNED: ' + reason + '\n')
        with (REPORTS / 'commands.log').open('a') as log:
            log.write(json.dumps({'log': name, 'pid': None, 'actual_exit': None, 'policy_result': result, 'terminal_reason': reason}) + '\n')
        return result
    with (REPORTS / (name + '.log')).open('wb') as log:
        process = OWNER.track(subprocess.Popen(argv, cwd=BACKEND, env=ENV | (extra or {}), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        if name == 'gradle-test': started = True  # Stops/container cleanup are owed only after an actual launch.
        deadline = time.monotonic() + seconds
        while process.poll() is None and time.monotonic() < deadline and (cleaning or not CANCELLED):
            if not cleaning and not space_ok('inflight-' + name): break
            time.sleep(0.05)
        if not cleaning: space_ok('postwait-' + name, force=True)
        terminal_reason = ('disk_floor' if SPACE_FAILURE is not None and not cleaning else
                           ('cancelled' if CANCELLED and not cleaning else
                            ('deadline' if time.monotonic() >= deadline or process.returncode is None else None)))
        if terminal_reason is not None: drain('interrupted-' + name)
        result = 125 if terminal_reason == 'disk_floor' else (124 if terminal_reason is not None else process.returncode)
    with (REPORTS / 'commands.log').open('a') as log: log.write(json.dumps({'log': name, 'pid': process.pid, 'actual_exit': process.returncode, 'policy_result': result, 'terminal_reason': terminal_reason}) + '\n')
    return result

def require(condition, message):
    if not condition: raise RuntimeError(message)

def verify_source_pins(phase):
    observed = {}
    try:
        for relative in EXPECTED_SOURCE_SHA256:
            path = BACKEND / relative
            observed[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else None
    finally:
        (REPORTS / ('source-pins-' + phase + '.json')).write_text(json.dumps(observed, indent=2) + '\n')
    require(observed == EXPECTED_SOURCE_SHA256, 'Backend22 comparison source pins differ: ' + phase)

result, started, before, cleanup_failed, project_caches = 1, False, None, False, []
raw_reports_copied, report_failure = False, None
gradle_exit, xml_verified, sources_clean, preserved, containers_absent = None, False, False, False, None
container_force_requested = False
xml_observations, static_reports = [], {}
reference_source_sha, reference_observation, reference_verified = None, {}, False
fixture_source_sha, fixture_observation, fixture_verified = None, {}, False
source_pins_before_verified, source_pins_after_verified = False, False
try:
    require(set(TARGETS) == {'authorization', 'authorized', 'runAllowed', 'backend_sha', 'classes', 'methods', 'status'}, 'Unexpected request fields')
    require(TARGETS['authorization'] == 'BACKEND22_ONE_TARGETED_BATCH_AUTHORIZED', 'Draft is not authorized')
    require(TARGETS['authorized'] is True and TARGETS['runAllowed'] is True, 'Execution is explicitly disabled')
    require(TARGETS['status'] == 'PRIMARY_BOUND_COMPARE', 'Wrong Backend22 phase/status')
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin' and
            os.environ.get('GITHUB_REF') == 'refs/heads/remediation/app-29-backend-complaints' and
            os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Wrong carrier/event or rerun')
    require(hashlib.sha256((ADMIN / 'ci/app29_owned_children.py').read_bytes()).hexdigest() == OWNED_CHILDREN_SHA, 'Owned-child utility changed')
    from app29_owned_children import OwnedChildren
    OWNER = OwnedChildren()  # Refuse unavailable subreaping before the first command.
    target = TARGETS['backend_sha']
    require(CLASSES == EXPECTED_CLASSES and all(type(count) is int for count in CLASSES.values()) and
            METHODS == EXPECTED_METHODS, 'Invalid exact Backend22 comparison class/count/method selection')
    note('Primary-bound request: ' + json.dumps(TARGETS, sort_keys=True))
    require(isinstance(target, str) and re.fullmatch('[0-9a-f]{40}', target) and target != '0' * 40 and
            target == EXPECTED_BACKEND_SHA, 'Unbound or unexpected backend target')
    require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha') == 0, 'Cannot read backend SHA')
    require((REPORTS / 'backend-sha.log').read_text().strip() == target, 'Backend checkout SHA mismatch')
    require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-before') == 0 and
            not (REPORTS / 'source-before.log').read_text().strip(), 'Backend checkout is not clean')
    require(command(['git', '-C', str(ADMIN), 'rev-parse', 'HEAD'], 'admin-sha') == 0, 'Cannot read Admin SHA')
    require((REPORTS / 'admin-sha.log').read_text().strip() == os.environ.get('GITHUB_SHA'), 'Carrier checkout SHA mismatch')
    verify_source_pins('before')
    source_pins_before_verified = True
    reference_source_sha = hashlib.sha256((BACKEND / 'src/main/resources' / REFERENCE_RESOURCE).read_bytes()).hexdigest()
    note('Source bootstrap reference SHA256: ' + reference_source_sha)
    require(reference_source_sha == REFERENCE_SHA, 'Backend22 comparison source bootstrap reference differs from the reviewed bytes')
    for name in ('.gradle', '.kotlin'): require(not (BACKEND / name).exists(), 'Unexpected preexisting project cache: ' + name)
    project_caches = [BACKEND / '.gradle', BACKEND / '.kotlin']
    require(BACKEND.is_dir() and not BACKEND.is_symlink() and BACKEND.resolve() == BACKEND, 'Unsafe Backend project directory')
    require(not CANDIDATE_BUILD.exists() and not CANDIDATE_BUILD.is_symlink(), 'Preexisting real Backend build root; not owned')
    require(EXPECTED_FIXTURE_PATH.is_file() and not EXPECTED_FIXTURE_PATH.is_symlink(), 'Comparison requires the admitted expected fixture resource')
    fixture_source_sha = hashlib.sha256(EXPECTED_FIXTURE_PATH.read_bytes()).hexdigest()
    require(fixture_source_sha == EXPECTED_FIXTURE_SHA, 'Comparison fixture differs from primary-admitted bytes')
    require(space_ok('before-private-inputs', force=True), 'Insufficient or unknown free space before private inputs')
    archive = ADMIN / 'docs/remediation/checkpoint-2026-09-08/review-evidence.tar.gz'
    with archive.open('rb') as stream: require(hashlib.file_digest(stream, 'sha256').hexdigest() == ARCHIVE_SHA, 'Private archive hash mismatch')
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()  # Headers only; never extractall, links, or unrelated payloads.
        def member(name, digest, limit=16 * 1024 * 1024):
            matches = [m for m in members if m.name == name]
            require(len(matches) == 1 and matches[0].isfile() and 0 <= matches[0].size <= limit, 'Invalid allowlisted archive member: ' + name)
            data = bundle.extractfile(matches[0]).read(limit + 1)
            require(len(data) == matches[0].size and hashlib.sha256(data).hexdigest() == digest, 'Archive member hash mismatch: ' + name)
            return data
        manifest = member(PREFIX + 'local-inputs.sha256', MANIFEST_SHA, 16384)
        entries = [line.split('  ', 1) for line in manifest.decode('ascii').splitlines()]
        require(len(entries) == 18 and all(len(e) == 2 for e in entries), 'Expected exactly 18 input records')
        require(len({e[1] for e in entries}) == 18, 'Duplicate local input')
        (W01 / 'local-inputs.sha256').write_bytes(manifest)
        (W01 / 'original.init.gradle').write_bytes(member('review/working/app-29-w01-local-dependencies.init.gradle', INIT_SHA, 16384))
        for digest, relative in entries:
            path = PurePosixPath(relative)
            require(re.fullmatch('[0-9a-f]{64}', digest) and not path.is_absolute() and '..' not in path.parts and '\\' not in relative and relative.startswith('me/manga/kira/source/'), 'Unsafe input path')
            require(space_ok('private-input-' + relative, force=True), 'Free-space floor failed during input preparation')
            destination = W01 / 'repository' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(member(PREFIX + 'repository/' + relative, digest))
    note(f'Private inputs verified: archive={ARCHIVE_SHA} manifest={MANIFEST_SHA} init={INIT_SHA}; 18 inputs')
    (W01 / 'bootstrap-reference.init.gradle').write_text(REFERENCE_INIT)
    require(command(['java', '-XshowSettings:properties', '-version'], 'java-version') == 0, 'JDK settings/version command failed')
    java_tmp = re.findall(r'^\s*java\.io\.tmpdir\s*=\s*(.*?)\s*$', (REPORTS / 'java-version.log').read_text(), re.MULTILINE)
    require(java_tmp == [str(TEMP)], 'JVM temp escaped the owned directory; no batch started')
    require(not ENV.get('DOCKER_CONTEXT'), 'Docker context override would invalidate local storage observation')
    require(command(['docker', 'version'], 'docker-version') == 0, 'Docker unavailable; no runtime installation attempted')
    require(command(['docker', 'info', '--format', '{{json .DockerRootDir}}'], 'docker-storage-root') == 0, 'Cannot identify actual Docker storage')
    docker_storage = json.loads((REPORTS / 'docker-storage-root.log').read_text())
    require(isinstance(docker_storage, str) and Path(docker_storage).is_absolute(), 'Invalid Docker storage root')
    SPACE_PATHS.append(Path(docker_storage))
    require(space_ok('actual-docker-storage', force=True), 'Docker storage free space is insufficient or unknown')
    require(command(['docker', 'ps', '-aq', '--no-trunc'], 'preexisting-containers', extra={'DOCKER_API_VERSION': '1.32'}) == 0, 'Docker API 1.32 unsupported/unavailable; refusing without adaptation')
    before = set((REPORTS / 'preexisting-containers.log').read_text().splitlines())
    require(not before, 'Expected a dedicated clean hosted runner; do not touch preexisting containers')
    require(not CANCELLED, 'Cancelled before validation')
    selectors = [name + '.' + method for name in CLASSES for method in METHODS[name]]
    tasks = ['compileKotlin', 'compileTestKotlin', 'test'] + [part for name in selectors for part in ('--tests', name)] + ['ktlintTestSourceSetCheck', '--continue', '-x', 'jacocoTestReport']
    gradle_exit = command(['./gradlew', '--no-daemon', '--no-parallel', '--no-configuration-cache', '--console=plain', '--max-workers=1', '--no-build-cache', '-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m', '-Dorg.gradle.vfs.watch=false', '-Pkotlin.compiler.execution.strategy=in-process', '--init-script', str(W01 / 'original.init.gradle'), '--init-script', str(W01 / 'bootstrap-reference.init.gradle'), *tasks], 'gradle-test', 18 * 60)
    result = gradle_exit
except (Exception, KeyboardInterrupt) as failure:
    note('FAIL: ' + str(failure))
    result = 1
finally:
    def cleanup_command(argv, name):
        global cleanup_failed
        try:
            ok = command(argv, name, seconds=60 if argv == ['./gradlew', '--stop'] else 30, cleaning=True) == 0
            cleanup_failed |= not ok
            return ok
        except (Exception, KeyboardInterrupt) as failure:
            cleanup_failed = True
            note('CLEANUP FAIL: ' + str(failure))
            return False
    if started: cleanup_command(['./gradlew', '--stop'], 'gradle-stop-immediate')
    workers_gone = drain('after-immediate-stop')
    try:
        xmls = list((W01 / 'backend-build/test-results/test').glob('*.xml'))
        for xml in xmls: shutil.copyfile(xml, REPORTS / xml.name)
        for tool in ('ktlint',):
            directory = W01 / 'backend-build/reports' / tool
            files = [p for p in directory.rglob('*') if p.is_file()] if directory.exists() else []
            files += list((W01 / 'backend-build/reports').glob(tool + '.*'))
            static_reports[tool] = []
            for path in files:
                if path.suffix in ('.xml', '.txt', '.html'):
                    destination = REPORTS / ('static-' + tool + '-' + path.name)
                    require(not destination.exists(), 'Ambiguous static report filename')
                    shutil.copyfile(path, destination)
                    static_reports[tool].append(destination.name)
        for filename in ('bootstrap-reference.init.gradle', 'bootstrap-reference-resource.json'):
            if (W01 / filename).is_file(): shutil.copyfile(W01 / filename, REPORTS / filename)
        raw_reports_copied = True  # No candidate custody exists in COMPARE; preserve raw reports even on task failure.
        preserved = raw_reports_copied
        processed_reference = W01 / 'backend-build/resources/main' / REFERENCE_RESOURCE
        source_reference = BACKEND / 'src/main/resources' / REFERENCE_RESOURCE
        reference_observation = {'settled': workers_gone, 'expected_sha256': REFERENCE_SHA, 'source_before_sha256': reference_source_sha,
                           'source_after_sha256': hashlib.sha256(source_reference.read_bytes()).hexdigest() if source_reference.is_file() else None,
                           'processed_sha256': hashlib.sha256(processed_reference.read_bytes()).hexdigest() if processed_reference.is_file() else None}
        processed_fixture = W01 / 'backend-build/resources/test' / FIXTURE_RESOURCE
        fixture_observation = {'settled': workers_gone, 'expected_sha256': EXPECTED_FIXTURE_SHA, 'source_before_sha256': fixture_source_sha,
                               'source_after_sha256': hashlib.sha256(EXPECTED_FIXTURE_PATH.read_bytes()).hexdigest() if EXPECTED_FIXTURE_PATH.is_file() else None,
                               'processed_sha256': hashlib.sha256(processed_fixture.read_bytes()).hexdigest() if processed_fixture.is_file() else None}
        resource_receipt = REPORTS / 'bootstrap-reference-resource.json'
        try: reference_observation['witness'] = json.loads(resource_receipt.read_text()) if resource_receipt.is_file() else None
        except Exception as failure: reference_observation['witness_error'] = str(failure)
        note('Raw bootstrap reference observation: ' + json.dumps(reference_observation, sort_keys=True))
        note('Raw admitted fixture observation: ' + json.dumps(fixture_observation, sort_keys=True))
        for xml in xmls:
            try:
                suite = ET.parse(REPORTS / xml.name).getroot()
                cases = suite.findall('testcase')
                observation = {'file': xml.name, 'suite': suite.attrib, 'settled': workers_gone, 'cases': []}
                for case in cases:
                    status = 'UNKNOWN_UNSETTLED' if not workers_gone else next((tag.upper() for tag in ('failure', 'error', 'skipped') if case.find(tag) is not None), 'PASS')
                    observation['cases'].append({'classname': case.get('classname'), 'name': case.get('name'), 'status': status})
                xml_observations.append(observation)
                note('Raw XML observation: ' + json.dumps(observation, sort_keys=True))
            except Exception as failure:
                xml_observations.append({'file': xml.name, 'status': 'UNREADABLE', 'error': str(failure)})
        require(workers_gone, 'XML/source results are unsettled; owned workers remain or absence is unknown')
        require({p.name for p in xmls} == {'TEST-' + name + '.xml' for name in CLASSES}, 'Missing/unexpected focused XML')
        for name, expected in CLASSES.items():
            suite = ET.parse(REPORTS / ('TEST-' + name + '.xml')).getroot()
            cases = suite.findall('testcase')
            require(suite.tag == 'testsuite' and suite.get('name') == name and int(suite.get('tests', '-1')) == len(cases) == expected and all(int(suite.get(k, '-1')) == 0 for k in ('failures', 'errors', 'skipped')), 'Focused XML totals differ: ' + name)
            identities = [(case.get('classname'), case.get('name')) for case in cases]
            require(len(set(identities)) == expected and all(cls == name and method for cls, method in identities), 'Wrong/duplicate testcase identity')
            require(not any(node.tag in ('failure', 'error', 'skipped') for node in suite.iter()), 'Failure/error/skip in focused XML')
            require({method for _, method in identities} == set(EXPECTED_CASES[name]), 'Wrong Backend22 comparison testcase identities: ' + name)
        xml_verified = True
        witness = reference_observation.get('witness') or {}
        # java.io.File.toURI().toURL() spells local URLs file:/..., not pathlib's file:///....
        processed_url = processed_reference.resolve().as_uri().replace('file:///', 'file:/', 1)
        processed_fixture_url = processed_fixture.resolve().as_uri().replace('file:///', 'file:/', 1)
        require(reference_source_sha == REFERENCE_SHA and reference_observation['source_after_sha256'] == REFERENCE_SHA and
                reference_observation['processed_sha256'] == REFERENCE_SHA and witness.get('accepted') is True and
                witness.get('test_task') == ':test' and witness.get('resource') == REFERENCE_RESOURCE and
                all(witness.get(field) == REFERENCE_SHA for field in ('expected_sha256', 'source_sha256', 'processed_sha256', 'loaded_sha256')) and
                witness.get('resolved_resources') == [processed_url] and witness.get('phase') == PHASE and
                witness.get('working_directory') == witness.get('project_directory') == str(BACKEND) and
                witness.get('max_parallel_forks') == 1 and witness.get('fork_every') == 0 and witness.get('max_heap_size') == '512m' and
                witness.get('junit_parallel_enabled') == 'false' and witness.get('generation_environment_present') is False and
                'generation_environment_value' in witness and witness['generation_environment_value'] is None,
                'Missing/mismatched reference or generation-UNSET Test configuration evidence')
        reference_verified = True
        require(fixture_source_sha == EXPECTED_FIXTURE_SHA and fixture_observation['source_after_sha256'] == EXPECTED_FIXTURE_SHA and
                fixture_observation['processed_sha256'] == EXPECTED_FIXTURE_SHA and
                all(witness.get(field) == EXPECTED_FIXTURE_SHA for field in ('expected_fixture_sha256', 'expected_fixture_source_sha256',
                    'expected_fixture_processed_sha256', 'expected_fixture_loaded_sha256')) and
                witness.get('expected_fixture_source_path') == str(EXPECTED_FIXTURE_PATH) and
                witness.get('expected_fixture_processed_path') == str(processed_fixture) and
                witness.get('expected_fixture_source_regular') is True and witness.get('expected_fixture_processed_regular') is True and
                witness.get('expected_fixture_resources') == [processed_fixture_url],
                'Missing/mismatched admitted fixture source/processed/unique-classpath evidence')
        fixture_verified = True
        require('static-ktlint-ktlintTestSourceSetCheck.txt' in static_reports.get('ktlint', []), 'Missing configured test-source Ktlint report')
        require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha-after', cleaning=True) == 0 and
                (REPORTS / 'backend-sha-after.log').read_text().strip() == TARGETS['backend_sha'], 'Backend SHA changed during validation')
        require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-after', cleaning=True) == 0 and
                not (REPORTS / 'source-after.log').read_text().strip(), 'Backend source changed during validation')
        verify_source_pins('after')
        source_pins_after_verified = True
        require(not CANDIDATE_BUILD.exists() and not CANDIDATE_BUILD.is_symlink(), 'Comparison created a forbidden real Backend build/candidate root')
        sources_clean = True
    except Exception as failure:
        report_failure = str(failure)
        note('REPORT FAIL: ' + str(failure))
        result = result or 1
    if started and before is not None and workers_gone:
        if cleanup_command(['docker', 'ps', '-aq', '--no-trunc', '--filter', 'label=org.testcontainers=true'], 'remaining-testcontainers'):
            owned = sorted(set((REPORTS / 'remaining-testcontainers.log').read_text().splitlines()) - before)
            if all(re.fullmatch('[0-9a-f]{64}', cid) for cid in owned) and drain('before-owned-container-delete'):
                if owned:
                    container_force_requested = cleanup_failed = True
                    note('FORCED container cleanup requested; proved absence will not qualify as normal completion')
                    cleanup_command(['docker', 'rm', '-fv', *owned], 'remove-owned-testcontainers')
                if cleanup_command(['docker', 'ps', '-aq', '--no-trunc', '--filter', 'label=org.testcontainers=true'], 'testcontainers-after-cleanup'):
                    containers_absent = not bool(set((REPORTS / 'testcontainers-after-cleanup.log').read_text().splitlines()) - before)
                    cleanup_failed |= not containers_absent
            else:
                cleanup_failed = True
                note('CLEANUP FAIL: invalid container ID or unsettled ownership; no container deletion')
    containers_safe = not started or containers_absent is True
    files_safe = workers_gone and drain('after-docker-before-files') and preserved and containers_safe
    if not containers_safe: note('RETAINING owned outputs/home/temp/project caches: container absence not proved')
    elif not files_safe: note('RETAINING owned outputs/home/temp/project caches: process absence or report preservation not proved')
    for directory in ((W01, TEMP, *(project_caches if started else [])) if files_safe else ()):
        try:
            if directory.exists(): shutil.rmtree(directory)
        except Exception as failure:
            cleanup_failed = True
            note('SCOPED CLEANUP FAIL: ' + str(failure))
    try: TEMP.mkdir(mode=0o700, exist_ok=True)  # Keep an empty owned temp path for the final JVM stop.
    except Exception as failure:
        cleanup_failed = True
        note('FINAL STOP TEMP FAIL: ' + str(failure))
    if started: cleanup_command(['./gradlew', '--stop'], 'gradle-stop-final')
    home_safe = drain('after-final-stop-before-home')
    try:
        if files_safe and home_safe:
            shutil.rmtree(HOME)
            shutil.rmtree(TEMP)
        else: note('RETAINING private home/temp: combined ownership or report preservation not proved; runner disposal is not a join claim')
    except Exception as failure:
        cleanup_failed = True
        note('GRADLE HOME CLEANUP FAIL: ' + str(failure))
    outputs_absent = not any(path.exists() for path in (W01, HOME, TEMP, *project_caches)) and not CANDIDATE_BUILD.exists() and not CANDIDATE_BUILD.is_symlink()
    cleanup_failed |= not outputs_absent or (started and containers_absent is not True)
    process_status = 'UNKNOWN_OR_INCOMPLETE' if any(not item['ok'] for item in DRAINS) else ('FORCED' if any(item.get('term') or item.get('kill') for item in DRAINS) else 'COMPLETE')
    container_status = 'NOT_STARTED' if not started else ('UNKNOWN' if containers_absent is None else ('PRESENT' if not containers_absent else ('FORCED' if container_force_requested else 'COMPLETE')))
    ownership_status = 'UNKNOWN_OR_INCOMPLETE' if process_status == 'UNKNOWN_OR_INCOMPLETE' or container_status in ('UNKNOWN', 'PRESENT') else ('FORCED' if process_status == 'FORCED' or container_status == 'FORCED' else 'COMPLETE')
    passed = result == 0 and gradle_exit == 0 and xml_verified and reference_verified and fixture_verified and sources_clean and preserved and ownership_status == 'COMPLETE' and not cleanup_failed and not CANCELLED and source_pins_before_verified and source_pins_after_verified and SPACE_CHECKS > 0 and SPACE_FAILURE is None
    note(f'validation_result={result}; process_ownership={process_status}; container_ownership={container_status}; ownership={ownership_status}; cleanup_failed={cleanup_failed}; cancelled={CANCELLED}; job_exit={0 if passed else 1}')
    (REPORTS / 'result.json').write_text(json.dumps({'backend_sha': TARGETS['backend_sha'], 'carrier_sha': os.environ.get('GITHUB_SHA'), 'classes': CLASSES, 'methods': METHODS, 'gradle_exit': gradle_exit, 'validation_exit': result, 'xml_verified': xml_verified, 'xml': xml_observations, 'static_reports': static_reports, 'reference_verified': reference_verified, 'reference': reference_observation, 'scope': 'BACKEND22_COMPARE_ONLY: exact1 normal signed-fixture comparison + configured test-source Ktlint; not EXPORT, App, deployment or cross-repo acceptance', 'phase': PHASE, 'fixture_verified': fixture_verified, 'fixture': fixture_observation, 'fixture_admission_receipt_sha256': FIXTURE_ADMISSION_RECEIPT_SHA, 'export_result_review_sha256': EXPORT_RESULT_REVIEW_SHA, 'candidate_build_root_absent': not CANDIDATE_BUILD.exists() and not CANDIDATE_BUILD.is_symlink(), 'sources_clean': sources_clean, 'source_pins_before_verified': source_pins_before_verified, 'source_pins_after_verified': source_pins_after_verified, 'disk_space': {'floor_bytes': MIN_FREE_BYTES, 'poll_seconds': SPACE_POLL_SECONDS, 'observations': SPACE_CHECKS, 'minimum_available_by_device': SPACE_MINIMUM, 'failure': SPACE_FAILURE, 'receipt': 'disk-space.jsonl'}, 'serialization': {'hosted_concurrency_group': 'backend11-private-completion-leases', 'primary_host_lock': 'PRIMARY_OWNED_EXTERNAL_PREREQUISITE; not observed by this VM'}, 'reports_preserved': preserved, 'drains': DRAINS, 'process_ownership_status': process_status, 'container_ownership_status': container_status, 'ownership_status': ownership_status, 'cleanup_failed': cleanup_failed, 'containers_absent': containers_absent, 'container_force_requested': container_force_requested, 'cancelled': CANCELLED, 'outputs_absent': outputs_absent, 'status': 'PASS' if passed else 'FAIL'}, indent=2) + '\n')
raise SystemExit(0 if passed else 1)
