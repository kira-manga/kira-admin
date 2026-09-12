"""Private focused Backend11 physical-owner/unit/Redis/PostgreSQL/static batch; never import as a library.

Even PASS covers only the selected cases, not provider enablement or full Backend11 acceptance.
"""
import hashlib, json, os, re, shutil, signal, subprocess, tarfile, time
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

ADMIN = Path(__file__).resolve().parent.parent
BACKEND = ADMIN.parent / 'backend'
RUN = Path(os.environ['BACKEND11_RUN'])
RUN.mkdir(mode=0o700, exist_ok=False)
REPORTS, HOME, W01, TEMP = (RUN / n for n in ('reports', 'gradle', 'w01', 'tmp'))
for directory in (REPORTS, HOME, W01, TEMP): directory.mkdir(mode=0o700)
ENV = dict(os.environ, GRADLE_USER_HOME=str(HOME), W01_RUN=str(W01), TMPDIR=str(TEMP),
           JAVA_TOOL_OPTIONS=f'-Djava.io.tmpdir={TEMP}', DOCKER_HOST='unix:///var/run/docker.sock')
TARGETS = json.loads((ADMIN / 'ci/backend11-completion-leases.request.json').read_text())
CLASSES, METHODS = TARGETS['classes'], TARGETS['methods']

# Source-derived selection: 51 exact methods / 78 invocations (56 unit + 16 real Redis + 6 real PG).
EXPECTED_CLASSES = {
    'me.manga.kira.backend.completion.CompletionExecutionOwnershipTest': 12,
    'me.manga.kira.backend.completion.CompletionLifecycleTest': 15,
    'me.manga.kira.backend.completion.CompletionInterruptionTest': 1,
    'me.manga.kira.backend.completion.CompletionStartupTest': 7,
    'me.manga.kira.backend.completion.CompletionAdmissionResponseTest': 16,
    'me.manga.kira.backend.completion.InMemoryCompletionAdmissionTest': 1,
    'me.manga.kira.backend.completion.CompletionDefaultModelTest': 3,
    'me.manga.kira.backend.completion.EchoCompletionProviderTest': 1,
    'me.manga.kira.backend.completion.RedisCompletionAdmissionIT': 12,
    'me.manga.kira.backend.security.RedisCoordinationIT': 4,
    'me.manga.kira.backend.completion.CompletionReleaseFailureHttpIT': 2,
    'me.manga.kira.backend.completion.CompletionLifecycleIT': 3,
    'me.manga.kira.backend.completion.CompletionOverloadIT': 1,
}
EXPECTED_METHODS = {
    'me.manga.kira.backend.completion.CompletionExecutionOwnershipTest': [
        'only the second of caller close and actual body exit releases',
        'caller close before entry prevents late work and activation',
        'close racing actual entry never releases an entered body',
        'slow raw release does not hold the ownership lock',
        'owed cleanup clears only prior interruption and restores flags even on failure',
        'canceled or shutdown queued bodies never enter and caller close releases once',
        'rejected submission leaves a never-entered owner owing one close',
    ],
    'me.manga.kira.backend.completion.CompletionLifecycleTest': [
        'only committed overload ownership can turn an equal-looking winner into 503',
        'persistence failure remains primary when Redis release is unconfirmed',
        'failed or rejected RUNNING startup resolves before the queue deadline without provider work',
        'two workers cannot replace physically running work after caller timeout or interruption',
        'normal publication precedes slow release even when its acknowledgement fails',
        'activation denial maps 503 only when its sanitized candidate wins',
        'activation delay shares the original startup deadline and cancellation still forbids invocation',
    ],
    'me.manga.kira.backend.completion.CompletionInterruptionTest': [
        'request interruption persists a sanitized terminal outcome before restoring interrupt',
    ],
    'me.manga.kira.backend.completion.CompletionStartupTest': [
        'authorization rejects the original startup deadline including equality',
        'timely authorization survives a descheduled caller and starts its own provider budget',
        'an observable completed Future can win at the provider wait deadline',
        'cancellation independently forbids both pending and post-claim authorization',
        'activation time still consumes the original startup budget and cannot replace a prior decision',
    ],
    'me.manga.kira.backend.completion.CompletionAdmissionResponseTest': [
        'Redis defined rejections preserve codes retries and their HTTP distinction',
        'indeterminate Redis acquisition denies work without speculative release',
        'Redis acquire transport failure is unavailable not a caller limit',
        'malformed Redis acquisition replies deny without a speculative release',
        'Redis acquire zero and activation one alone admit and release once',
        'unconfirmed Redis release preserves the result and reports once per application attempt',
        'invalid release acknowledgements and known decode failures preserve the outcome without retry',
        'activation denies expired or indeterminate replies without speculative cleanup',
        'unrelated Redis programming failure is not swallowed as unconfirmed cleanup',
    ],
    'me.manga.kira.backend.completion.InMemoryCompletionAdmissionTest': [
        'activation is explicit single-use and cannot revive a closed reservation',
    ],
    'me.manga.kira.backend.completion.CompletionDefaultModelTest': [
        'invalid defaults reject direct construction before executor metrics admission or provider work',
        'UNKNOWN and actual HTTP providers reject before executor metrics admission or invocation',
        'disabled service startup needs no model provider credentials or collaborators',
    ],
    'me.manga.kira.backend.completion.EchoCompletionProviderTest': [
        'name is echo',
    ],
    'me.manga.kira.backend.completion.RedisCompletionAdmissionIT': [
        'two instances sustain unexpired overlapping pending reservations beyond the first key deadline',
        'expired and replayed releases cannot touch successor tokens or their deadlines',
        'shorter pending reservations and turnover never shorten a live longer reservation',
        'acknowledged peer pins remain persistent beyond pending deadlines and only exact release removes them',
        'expired pending peers cannot activate and pruning never removes a pin',
        'unknown activation acknowledgement grants nothing while the real pin remains until owned cleanup',
        'real service pending delay past its actual deadline cannot activate or disturb a pinned successor',
        'two real services keep a timed out physical worker pinned beyond its former TTL',
        'legacy malformed oversized and expiring pin state is refused without repair on every operation',
        'enabled rate state is preflighted before any earlier counter or lease mutation',
        'token collision and invalid protocol arguments refuse before writes',
        'exact deadline arithmetic rejects overflow and retains the greatest canonical decimal',
    ],
    'me.manga.kira.backend.security.RedisCoordinationIT': [
        'later completion closes do not repeat an unconfirmed pending release',
        'unconfirmed pin release retains capacity unless real removal happened before the transport failure',
    ],
    'me.manga.kira.backend.completion.CompletionReleaseFailureHttpIT': [
        'committed HTTP outcome survives Redis release failure',
    ],
    'me.manga.kira.backend.completion.CompletionLifecycleIT': [
        'cancellation wins delayed RUNNING work without relying on its interrupt bit',
    ],
    'me.manga.kira.backend.completion.CompletionOverloadIT': [
        'queue timeout persists a failure returns 503 and cancels queued provider work',
    ],
}
# Gradle's JUnit XML uses parameter display names, not the enclosing method name.
# Ordinary methods retain (); parameterized identities are pinned to the reviewed source.
EXPECTED_CASES = {
    'me.manga.kira.backend.completion.CompletionExecutionOwnershipTest': [
        '[1] callerFirst=false',
        '[2] callerFirst=true',
        'caller close before entry prevents late work and activation()',
        'close racing actual entry never releases an entered body()',
        'slow raw release does not hold the ownership lock()',
        '[1] interruptedBefore=false, throws=false',
        '[2] interruptedBefore=true, throws=false',
        '[3] interruptedBefore=false, throws=true',
        '[4] interruptedBefore=true, throws=true',
        '[1] cancelQueued=false',
        '[2] cancelQueued=true',
        'rejected submission leaves a never-entered owner owing one close()',
    ],
    'me.manga.kira.backend.completion.CompletionLifecycleTest': [
        '[1] won=false',
        '[2] won=true',
        'persistence failure remains primary when Redis release is unconfirmed()',
        '[1] throwFromClaim=false',
        '[2] throwFromClaim=true',
        'two-worker ownership [1] interruptCaller=false',
        'two-worker ownership [2] interruptCaller=true',
        '[1] releaseFailure=false',
        '[2] releaseFailure=true',
        '[1] activation=EXPIRED, won=true',
        '[2] activation=EXPIRED, won=false',
        '[3] activation=UNAVAILABLE, won=true',
        '[4] activation=UNAVAILABLE, won=false',
        'activation startup deadline [1] interruptCaller=false',
        'activation startup deadline [2] interruptCaller=true',
    ],
    'me.manga.kira.backend.completion.CompletionInterruptionTest': [
        'request interruption persists a sanitized terminal outcome before restoring interrupt()',
    ],
    'me.manga.kira.backend.completion.CompletionStartupTest': [
        '[1] at=110',
        '[2] at=111',
        'timely authorization survives a descheduled caller and starts its own provider budget()',
        'an observable completed Future can win at the provider wait deadline()',
        '[1] claimAlreadyStarted=false',
        '[2] claimAlreadyStarted=true',
        'activation time still consumes the original startup budget and cannot replace a prior decision()',
    ],
    'me.manga.kira.backend.completion.CompletionAdmissionResponseTest': [
        '[1] result=1, status=429, code=COMPLETION_USER_RATE_LIMIT, retry=60',
        '[2] result=2, status=429, code=COMPLETION_GLOBAL_RATE_LIMIT, retry=60',
        '[3] result=3, status=429, code=COMPLETION_DAILY_QUOTA, retry=86400',
        '[4] result=4, status=503, code=COMPLETION_CONCURRENCY_LIMIT, retry=1',
        '[1] result=null',
        '[2] result=-1',
        '[3] result=5',
        '[4] result=9223372036854775807',
        'Redis acquire transport failure is unavailable not a caller limit()',
        'malformed Redis acquisition replies deny without a speculative release()',
        'Redis acquire zero and activation one alone admit and release once()',
        '[1] releaseFailure=true',
        '[2] releaseFailure=false',
        'invalid release acknowledgements and known decode failures preserve the outcome without retry()',
        'activation denies expired or indeterminate replies without speculative cleanup()',
        'unrelated Redis programming failure is not swallowed as unconfirmed cleanup()',
    ],
    'me.manga.kira.backend.completion.InMemoryCompletionAdmissionTest': [
        'activation is explicit single-use and cannot revive a closed reservation()',
    ],
    'me.manga.kira.backend.completion.CompletionDefaultModelTest': [
        'invalid defaults reject direct construction before executor metrics admission or provider work()',
        'UNKNOWN and actual HTTP providers reject before executor metrics admission or invocation()',
        'disabled service startup needs no model provider credentials or collaborators()',
    ],
    'me.manga.kira.backend.completion.EchoCompletionProviderTest': [
        'name is echo()',
    ],
    'me.manga.kira.backend.completion.RedisCompletionAdmissionIT': [
        'two instances sustain unexpired overlapping pending reservations beyond the first key deadline()',
        'expired and replayed releases cannot touch successor tokens or their deadlines()',
        'shorter pending reservations and turnover never shorten a live longer reservation()',
        'acknowledged peer pins remain persistent beyond pending deadlines and only exact release removes them()',
        'expired pending peers cannot activate and pruning never removes a pin()',
        'unknown activation acknowledgement grants nothing while the real pin remains until owned cleanup()',
        'real service pending delay past its actual deadline cannot activate or disturb a pinned successor()',
        'two real services keep a timed out physical worker pinned beyond its former TTL()',
        'legacy malformed oversized and expiring pin state is refused without repair on every operation()',
        'enabled rate state is preflighted before any earlier counter or lease mutation()',
        'token collision and invalid protocol arguments refuse before writes()',
        'exact deadline arithmetic rejects overflow and retains the greatest canonical decimal()',
    ],
    'me.manga.kira.backend.security.RedisCoordinationIT': [
        'unconfirmed pending release [1] applyBeforeFailure=false',
        'unconfirmed pending release [2] applyBeforeFailure=true',
        'unconfirmed pinned release [1] applyBeforeFailure=false',
        'unconfirmed pinned release [2] applyBeforeFailure=true',
    ],
    'me.manga.kira.backend.completion.CompletionReleaseFailureHttpIT': [
        '[1] refused=false',
        '[2] refused=true',
    ],
    'me.manga.kira.backend.completion.CompletionLifecycleIT': [
        '[1] point=STARTUP_TIMEOUT',
        '[2] point=BEFORE_CLAIM',
        '[3] point=AFTER_COMMIT',
    ],
    'me.manga.kira.backend.completion.CompletionOverloadIT': [
        'queue timeout persists a failure returns 503 and cancels queued provider work()',
    ],
}
LUA_RESOURCE = 'redis/completion-admission.lua'
LUA_SHA = '29e9cba7ef88e41883999fa4f9c59729df15203ead5cceeeeb005ef8c8a734b8'
# This small extra init leaves the pinned dependency/ownership helper unchanged. It witnesses
# the actual test task's classpath before its selected tests, not a Boot jar or provider run.
LUA_INIT = r'''import groovy.json.JsonOutput
import java.net.URLClassLoader
import java.security.MessageDigest
import org.gradle.api.tasks.testing.Test
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension

gradle.projectsEvaluated {
    def p = gradle.rootProject
    p.tasks.named('test', Test).configure {
        extensions.getByType(JacocoTaskExtension).enabled = false
        doFirst {
            def resource = '@LUA_RESOURCE@'
            def expected = '@LUA_SHA@'
            def source = p.file('src/main/resources/' + resource).canonicalFile
            def processed = new File(p.layout.buildDirectory.get().asFile, 'resources/main/' + resource).canonicalFile
            def urls = classpath.files.collect { it.toURI().toURL() } as URL[]
            def digest = { bytes -> MessageDigest.getInstance('SHA-256').digest(bytes).encodeHex().toString() }
            def receipt = [test_task: path, resource: resource, expected_sha256: expected,
                source_path: source.path, processed_path: processed.path,
                classpath: urls.collect { it.toExternalForm() }, accepted: false]
            def loader = new URLClassLoader(urls, (ClassLoader) null)
            try {
                receipt.source_sha256 = digest(source.bytes)
                receipt.processed_sha256 = digest(processed.bytes)
                def resources = Collections.list(loader.getResources(resource))
                receipt.resolved_resources = resources.collect { it.toExternalForm() }
                if (resources.size() == 1) {
                    receipt.loaded_sha256 = resources[0].openStream().withCloseable { digest(it.bytes) }
                }
                receipt.accepted = receipt.source_sha256 == expected && receipt.processed_sha256 == expected &&
                    receipt.loaded_sha256 == expected && receipt.resolved_resources == [processed.toURI().toURL().toExternalForm()]
                if (!receipt.accepted) throw new GradleException('Backend11 Lua source/processed/classpath loading mismatch')
            } finally {
                try { loader.close() } finally {
                    new File(System.getenv('W01_RUN'), 'completion-lua-resource.json').text = JsonOutput.prettyPrint(JsonOutput.toJson(receipt)) + '\n'
                    println('BACKEND11_LUA_RESOURCE ' + JsonOutput.toJson(receipt))
                }
            }
        }
    }
}
'''.replace('@LUA_RESOURCE@', LUA_RESOURCE).replace('@LUA_SHA@', LUA_SHA)
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
    with (REPORTS / 'commands.log').open('a') as log: log.write(json.dumps({'argv': argv, 'cwd': str(BACKEND), 'seconds': seconds, 'env_overrides': extra}) + '\n')
    with (REPORTS / (name + '.log')).open('wb') as log:
        process = OWNER.track(subprocess.Popen(argv, cwd=BACKEND, env=ENV | (extra or {}), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        deadline = time.monotonic() + seconds
        while process.poll() is None and time.monotonic() < deadline and (cleaning or not CANCELLED): time.sleep(0.05)
        terminal_reason = 'cancelled' if CANCELLED and not cleaning else ('deadline' if time.monotonic() >= deadline or process.returncode is None else None)
        if terminal_reason is not None: drain('interrupted-' + name)
        result = 124 if terminal_reason is not None else process.returncode
    with (REPORTS / 'commands.log').open('a') as log: log.write(json.dumps({'log': name, 'pid': process.pid, 'actual_exit': process.returncode, 'policy_result': result, 'terminal_reason': terminal_reason}) + '\n')
    return result

def require(condition, message):
    if not condition: raise RuntimeError(message)

result, started, before, cleanup_failed, project_caches = 1, False, None, False, []
gradle_exit, xml_verified, sources_clean, preserved, containers_absent = None, False, False, False, None
container_force_requested = False
xml_observations, static_reports = [], {}
lua_source_sha, lua_observation, lua_verified = None, {}, False
try:
    require(set(TARGETS) == {'authorization', 'backend_sha', 'classes', 'methods', 'status'}, 'Unexpected request fields')
    require(TARGETS['authorization'] == 'BACKEND11_ONE_TARGETED_BATCH_AUTHORIZED', 'Draft is not authorized')
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin' and
            os.environ.get('GITHUB_REF') == 'refs/heads/remediation/app-29-backend-complaints' and
            os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Wrong carrier/event or rerun')
    require(hashlib.sha256((ADMIN / 'ci/app29_owned_children.py').read_bytes()).hexdigest() == OWNED_CHILDREN_SHA, 'Owned-child utility changed')
    from app29_owned_children import OwnedChildren
    OWNER = OwnedChildren()  # Refuse unavailable subreaping before the first command.
    target = TARGETS['backend_sha']
    require(CLASSES == EXPECTED_CLASSES and all(type(count) is int for count in CLASSES.values()) and
            METHODS == EXPECTED_METHODS, 'Invalid exact Backend11 class/count/method selection')
    note('Primary-bound request: ' + json.dumps(TARGETS, sort_keys=True))
    require(re.fullmatch('[0-9a-f]{40}', target) and target != '0' * 40, 'Unbound backend target')
    require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha') == 0, 'Cannot read backend SHA')
    require((REPORTS / 'backend-sha.log').read_text().strip() == target, 'Backend checkout SHA mismatch')
    require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-before') == 0 and
            not (REPORTS / 'source-before.log').read_text().strip(), 'Backend checkout is not clean')
    require(command(['git', '-C', str(ADMIN), 'rev-parse', 'HEAD'], 'admin-sha') == 0, 'Cannot read Admin SHA')
    require((REPORTS / 'admin-sha.log').read_text().strip() == os.environ.get('GITHUB_SHA'), 'Carrier checkout SHA mismatch')
    lua_source_sha = hashlib.sha256((BACKEND / 'src/main/resources' / LUA_RESOURCE).read_bytes()).hexdigest()
    note('Source Lua SHA256: ' + lua_source_sha)
    require(lua_source_sha == LUA_SHA, 'Backend11 source Lua differs from the reviewed bytes')
    for name in ('.gradle', '.kotlin'): require(not (BACKEND / name).exists(), 'Unexpected preexisting project cache: ' + name)
    project_caches = [BACKEND / '.gradle', BACKEND / '.kotlin']
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
            destination = W01 / 'repository' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(member(PREFIX + 'repository/' + relative, digest))
    note(f'Private inputs verified: archive={ARCHIVE_SHA} manifest={MANIFEST_SHA} init={INIT_SHA}; 18 inputs')
    (W01 / 'completion-lua.init.gradle').write_text(LUA_INIT)
    require(command(['java', '-XshowSettings:properties', '-version'], 'java-version') == 0, 'JDK settings/version command failed')
    java_tmp = re.findall(r'^\s*java\.io\.tmpdir\s*=\s*(.*?)\s*$', (REPORTS / 'java-version.log').read_text(), re.MULTILINE)
    require(java_tmp == [str(TEMP)], 'JVM temp escaped the owned directory; no batch started')
    require(command(['docker', 'version'], 'docker-version') == 0, 'Docker unavailable; no runtime installation attempted')
    require(command(['docker', 'ps', '-aq', '--no-trunc'], 'preexisting-containers', extra={'DOCKER_API_VERSION': '1.32'}) == 0, 'Docker API 1.32 unsupported/unavailable; refusing without adaptation')
    before = set((REPORTS / 'preexisting-containers.log').read_text().splitlines())
    require(not before, 'Expected a dedicated clean hosted runner; do not touch preexisting containers')
    require(not CANCELLED, 'Cancelled before validation')
    started = True
    selectors = [name + '.' + method for name in CLASSES for method in METHODS[name]]
    tasks = ['compileKotlin', 'compileTestKotlin', 'test'] + [part for name in selectors for part in ('--tests', name)] + ['ktlintMainSourceSetCheck', 'ktlintTestSourceSetCheck', 'detekt', '--continue', '-x', 'jacocoTestReport']
    gradle_exit = command(['./gradlew', '--no-daemon', '--no-parallel', '--no-configuration-cache', '--console=plain', '--max-workers=1', '--no-build-cache', '-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m', '-Dorg.gradle.vfs.watch=false', '-Pkotlin.compiler.execution.strategy=in-process', '--init-script', str(W01 / 'original.init.gradle'), '--init-script', str(W01 / 'completion-lua.init.gradle'), *tasks], 'gradle-test', 18 * 60)
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
        for tool in ('ktlint', 'detekt'):
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
        for filename in ('completion-lua.init.gradle', 'completion-lua-resource.json'):
            if (W01 / filename).is_file(): shutil.copyfile(W01 / filename, REPORTS / filename)
        preserved = True  # Missing output is reported below; a failed copy forbids its deletion.
        processed_lua = W01 / 'backend-build/resources/main' / LUA_RESOURCE
        source_lua = BACKEND / 'src/main/resources' / LUA_RESOURCE
        lua_observation = {'settled': workers_gone, 'expected_sha256': LUA_SHA, 'source_before_sha256': lua_source_sha,
                           'source_after_sha256': hashlib.sha256(source_lua.read_bytes()).hexdigest() if source_lua.is_file() else None,
                           'processed_sha256': hashlib.sha256(processed_lua.read_bytes()).hexdigest() if processed_lua.is_file() else None}
        resource_receipt = REPORTS / 'completion-lua-resource.json'
        try: lua_observation['witness'] = json.loads(resource_receipt.read_text()) if resource_receipt.is_file() else None
        except Exception as failure: lua_observation['witness_error'] = str(failure)
        note('Raw Lua observation: ' + json.dumps(lua_observation, sort_keys=True))
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
            require({method for _, method in identities} == set(EXPECTED_CASES[name]), 'Wrong Backend11 testcase identities: ' + name)
        xml_verified = True
        witness = lua_observation.get('witness') or {}
        # java.io.File.toURI().toURL() spells local URLs file:/..., not pathlib's file:///....
        processed_url = processed_lua.resolve().as_uri().replace('file:///', 'file:/', 1)
        require(lua_source_sha == LUA_SHA and lua_observation['source_after_sha256'] == LUA_SHA and
                lua_observation['processed_sha256'] == LUA_SHA and witness.get('accepted') is True and
                witness.get('test_task') == ':test' and witness.get('resource') == LUA_RESOURCE and
                all(witness.get(field) == LUA_SHA for field in ('expected_sha256', 'source_sha256', 'processed_sha256', 'loaded_sha256')) and
                witness.get('resolved_resources') == [processed_url], 'Missing/mismatched source, processed or loaded Lua evidence')
        lua_verified = True
        require(all(static_reports.get(tool) for tool in ('ktlint', 'detekt')), 'Missing static reports')
        require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha-after', cleaning=True) == 0 and
                (REPORTS / 'backend-sha-after.log').read_text().strip() == TARGETS['backend_sha'], 'Backend SHA changed during validation')
        require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-after', cleaning=True) == 0 and
                not (REPORTS / 'source-after.log').read_text().strip(), 'Backend source changed during validation')
        sources_clean = True
    except Exception as failure:
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
    outputs_absent = not any(path.exists() for path in (W01, HOME, TEMP, *project_caches))
    cleanup_failed |= not outputs_absent or (started and containers_absent is not True)
    process_status = 'UNKNOWN_OR_INCOMPLETE' if any(not item['ok'] for item in DRAINS) else ('FORCED' if any(item.get('term') or item.get('kill') for item in DRAINS) else 'COMPLETE')
    container_status = 'NOT_STARTED' if not started else ('UNKNOWN' if containers_absent is None else ('PRESENT' if not containers_absent else ('FORCED' if container_force_requested else 'COMPLETE')))
    ownership_status = 'UNKNOWN_OR_INCOMPLETE' if process_status == 'UNKNOWN_OR_INCOMPLETE' or container_status in ('UNKNOWN', 'PRESENT') else ('FORCED' if process_status == 'FORCED' or container_status == 'FORCED' else 'COMPLETE')
    passed = result == 0 and gradle_exit == 0 and xml_verified and lua_verified and sources_clean and preserved and ownership_status == 'COMPLETE' and not cleanup_failed and not CANCELLED
    note(f'validation_result={result}; process_ownership={process_status}; container_ownership={container_status}; ownership={ownership_status}; cleanup_failed={cleanup_failed}; cancelled={CANCELLED}; job_exit={0 if passed else 1}')
    (REPORTS / 'result.json').write_text(json.dumps({'backend_sha': TARGETS['backend_sha'], 'carrier_sha': os.environ.get('GITHUB_SHA'), 'classes': CLASSES, 'methods': METHODS, 'gradle_exit': gradle_exit, 'validation_exit': result, 'xml_verified': xml_verified, 'xml': xml_observations, 'static_reports': static_reports, 'lua_verified': lua_verified, 'lua': lua_observation, 'physical_provider_cap': 'TARGETED_TEST_EVIDENCE_ONLY; not provider enablement or full Backend11 acceptance', 'sources_clean': sources_clean, 'reports_preserved': preserved, 'drains': DRAINS, 'process_ownership_status': process_status, 'container_ownership_status': container_status, 'ownership_status': ownership_status, 'cleanup_failed': cleanup_failed, 'containers_absent': containers_absent, 'container_force_requested': container_force_requested, 'cancelled': CANCELLED, 'outputs_absent': outputs_absent, 'status': 'PASS' if passed else 'FAIL'}, indent=2) + '\n')
raise SystemExit(0 if passed else 1)
