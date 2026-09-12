"""Private Backend17 realPG3/corrected-two-file-static batch; never import as a library."""
import hashlib, json, os, re, shutil, signal, subprocess, tarfile, time
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

ADMIN = Path(__file__).resolve().parent.parent
BACKEND = ADMIN.parent / 'backend'
RUN = Path(os.environ['BACKEND17_RUN'])
RUN.mkdir(mode=0o700, exist_ok=False)
REPORTS, HOME, W01, TEMP = (RUN / n for n in ('reports', 'gradle', 'w01', 'tmp'))
for directory in (REPORTS, HOME, W01, TEMP): directory.mkdir(mode=0o700)
ENV = dict(os.environ, GRADLE_USER_HOME=str(HOME), W01_RUN=str(W01), TMPDIR=str(TEMP),
           JAVA_TOOL_OPTIONS=f'-Djava.io.tmpdir={TEMP}', DOCKER_HOST='unix:///var/run/docker.sock')
TARGETS = json.loads((ADMIN / 'ci/backend17-history-pg03.request.json').read_text())
CLASSES = TARGETS['classes']
SELECTORS = TARGETS['selectors']
STATIC_FILES = TARGETS['static_files']

EXPECTED_BACKEND_SHA = 'a7d0eec5924b016e09710b0d1f92de95ec64f76c'  # Primary-only isolated Backend17 checkpoint binding; not the private root Backend.
EXPECTED_CLASSES = {
    'me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT': 3,
}
EXPECTED_SELECTORS = ['me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT']
EXPECTED_XML_IDENTITIES = {
    ('me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT', 'growing TOAST histories keep query columns row consumption and deep seek bounded()'),
    ('me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT', 'gapped older traversal survives a newer insert and ends without duplicate or lost rows()'),
    ('me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT', 'real authentication still gates bounded array history reads()'),
}
EXPECTED_STATIC_FILES = {
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/AdminHistoryJdbcObserver.kt': '377a20271b7437a8c4c23a84a4247949e7ccf80fcea85b69cca5b0e6b5cc582f',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/AdminHistoryRepositoryIT.kt': 'f3475014fe632ebb93206ed550d7408ce1f2e1eebc9b86abc794a97e29ccd31f',
}
EXPECTED_STATIC_TASKS = {'ktlint': ':runKtlintCheckOverTestSourceSet', 'detekt': ':detekt'}
EXPECTED_TASK_GRAPH = sorted([
    ':checkKotlinGradlePluginConfigurationErrors', ':compileKotlin', ':compileJava',
    ':processResources', ':classes', ':jar', ':compileTestKotlin', ':compileTestJava',
    ':processTestResources', ':testClasses', ':w01SourceClasspathEvidence', ':test',
    ':loadKtlintReporters', ':runKtlintCheckOverTestSourceSet', ':ktlintTestSourceSetCheck', ':detekt',
])
EXPECTED_STATIC_POLICY = {
    'ktlint_engine': '1.8.0', 'ktlint_ignore_failures': False, 'ktlint_baseline_present': False,
    'detekt_version': '1.23.8', 'detekt_ignore_failures': False, 'detekt_auto_correct': False,
    'detekt_baseline_present': False, 'detekt_dry_run_property_present': False,
}
OWNED_CHILDREN_SHA = '56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385'
PREFIX = 'review/working/app-29-w01-local-dependencies-20260905/'
ARCHIVE_SHA = 'da94218f74eb0f5831241c8606c8f82142e49b818acfaff027a78f2efe77faab'
MANIFEST_SHA = 'c67fcc5fe64a9a795373c4683c7c1edd6407146e3cd07609fa7018a8a98db79a'
INIT_SHA = '429961b98254b89f7ce1d7ba1efa61b8cba28a3bae35353bf3a8ba85f4a1c839'
SCOPE_INIT_SHA = '7c5b8c3204ec677603717ed02544cd9b84461e6277ddc1f7989383e5f55b9488'
STATIC_SCOPE_INIT = r"""// Source-only Backend17 PG03 draft. Embedded verbatim in the proposed private controller.
// Only actual static-task inputs change; source sets, compilation and test classpaths do not.
import groovy.json.JsonOutput
import java.nio.file.Files
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import org.gradle.api.GradleException
import org.gradle.api.tasks.testing.Test

gradle.projectsEvaluated {
    def p = gradle.rootProject
    if (p.name != 'kira-backend') {
        throw new GradleException('Backend17 PG03 scope is backend-only')
    }
    def expectedFiles = [
        'src/test/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/AdminHistoryJdbcObserver.kt': '377a20271b7437a8c4c23a84a4247949e7ccf80fcea85b69cca5b0e6b5cc582f',
        'src/test/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/AdminHistoryRepositoryIT.kt': 'f3475014fe632ebb93206ed550d7408ce1f2e1eebc9b86abc794a97e29ccd31f',
    ]
    def only = expectedFiles.keySet().collect { relative -> p.file(relative).canonicalFile }.sort { it.path }
    def expectedGraph = [
        ':checkKotlinGradlePluginConfigurationErrors', ':compileKotlin', ':compileJava',
        ':processResources', ':classes', ':jar', ':compileTestKotlin', ':compileTestJava',
        ':processTestResources', ':testClasses', ':w01SourceClasspathEvidence', ':test',
        ':loadKtlintReporters', ':runKtlintCheckOverTestSourceSet', ':ktlintTestSourceSetCheck', ':detekt'
    ].sort()
    def expectedPolicy = [
        ktlint_engine: '1.8.0', ktlint_ignore_failures: false, ktlint_baseline_present: false,
        detekt_version: '1.23.8', detekt_ignore_failures: false, detekt_auto_correct: false,
        detekt_baseline_present: false, detekt_dry_run_property_present: false
    ]
    def lint = p.tasks.named('runKtlintCheckOverTestSourceSet').get()
    def detekt = p.tasks.named('detekt').get()
    def ktlintExtension = p.extensions.getByName('ktlint')
    def detektExtension = p.extensions.getByName('detekt')

    // Released ktlint-gradle14.2.0 public setSource replaces the real lint worker's inputs.
    // Released Detekt1.23.8 extends SourceTask and passes its source to InputArgument.
    lint.setSource(p.files(only))
    detekt.setSource(p.files(only))

    def inventory = { task ->
        def actual = task.source.files.collect { it.canonicalFile }.sort { it.path }
        if (actual != only || actual.any { !it.isFile() }) {
            throw new GradleException('Backend17 exact static source mismatch for ' + task.path + ': ' + actual)
        }
        def files = actual.collectEntries { file ->
            [(p.relativePath(file)): MessageDigest.getInstance('SHA-256').digest(file.bytes).encodeHex().toString()]
        }
        if (files != expectedFiles) {
            throw new GradleException('Backend17 static source hash/path changed for ' + task.path)
        }
        files
    }
    def policy = {
        [
            ktlint_engine: ktlintExtension.version.get(),
            ktlint_ignore_failures: ktlintExtension.ignoreFailures.get(),
            ktlint_baseline_present: (ktlintExtension.baseline.asFile.orNull?.exists() ?: false),
            detekt_version: detektExtension.toolVersion,
            detekt_ignore_failures: detekt.ignoreFailures,
            detekt_auto_correct: detekt.autoCorrect,
            detekt_baseline_present: detekt.baseline.isPresent(),
            detekt_dry_run_property_present: p.providers.gradleProperty('detekt-dry-run').isPresent()
        ]
    }
    gradle.taskGraph.whenReady { graph ->
        def paths = graph.allTasks.collect { it.path }.sort()
        if (paths != expectedGraph || graph.allTasks.findAll { it instanceof Test }.collect { it.path } != [':test']) {
            throw new GradleException('Unexpected Backend17 PG03 task graph: ' + paths)
        }
        [':compileKotlin', ':compileTestKotlin', ':test', ':loadKtlintReporters',
         ':runKtlintCheckOverTestSourceSet', ':ktlintTestSourceSetCheck', ':detekt'].each { path ->
            if (!graph.allTasks.find { it.path == path }.enabled) {
                throw new GradleException('Required Backend17 task disabled: ' + path)
            }
        }
        if (policy() != expectedPolicy) {
            throw new GradleException('Backend17 requires existing static versions, failures, no baselines or autocorrection')
        }
        [ktlint: lint, detekt: detekt].each { tool, task ->
            inventory(task)
            task.doFirst {
                def actualFiles = inventory(task)
                def actualPolicy = policy()
                if (actualPolicy != expectedPolicy) {
                    throw new GradleException('Backend17 static policy changed before action: ' + task.path)
                }
                def receipt = new File(p.layout.buildDirectory.get().asFile, 'reports/backend17-pg03-' + tool + '-scope.json')
                Files.createDirectories(receipt.parentFile.toPath())
                def observation = [
                    schema: 'backend17.pg03.static-scope.v1', phase: 'before-task-action',
                    tool: tool, task: task.path, static_files: actualFiles, graph: paths, policy: actualPolicy
                ]
                Files.writeString(
                    receipt.toPath(), JsonOutput.prettyPrint(JsonOutput.toJson(observation)) + '\n',
                    StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE
                )
                println('BACKEND17_PG03_STATIC_SCOPE ' + JsonOutput.toJson(observation))
            }
        }
    }
}
"""

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

def command(argv, name, seconds=60, extra=None, cleaning=False):
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

def static_source_pins_match():
    return all(not (BACKEND / path).is_symlink() and (BACKEND / path).is_file() and
               hashlib.sha256((BACKEND / path).read_bytes()).hexdigest() == digest
               for path, digest in EXPECTED_STATIC_FILES.items())

result, started, before, cleanup_failed, project_caches = 1, False, None, False, []
gradle_exit, xml_verified, sources_clean, preserved, containers_absent = None, False, False, False, None
container_force_requested = False
xml_observations, static_reports, static_scopes = [], {}, {}
static_scopes_verified = False
try:
    require(set(TARGETS) == {'authorization', 'backend_sha', 'classes', 'selectors', 'static_files', 'status'}, 'Unexpected request fields')
    require(TARGETS['authorization'] == 'BACKEND17_PG03_ONE_TARGETED_BATCH_AUTHORIZED', 'Draft is not authorized')
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin' and
            os.environ.get('GITHUB_REF') == 'refs/heads/remediation/app-29-backend-complaints' and
            os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Wrong carrier/event or rerun')
    require(hashlib.sha256((ADMIN / 'ci/app29_owned_children.py').read_bytes()).hexdigest() == OWNED_CHILDREN_SHA, 'Owned-child utility changed')
    from app29_owned_children import OwnedChildren
    OWNER = OwnedChildren()  # Refuse unavailable subreaping before the first command.
    target = TARGETS['backend_sha']
    require(CLASSES == EXPECTED_CLASSES and all(type(count) is int for count in CLASSES.values()) and
            SELECTORS == EXPECTED_SELECTORS and STATIC_FILES == EXPECTED_STATIC_FILES,
            'Invalid exact Backend17 three-method/count/two-static-file selection')
    note('Primary-bound request: ' + json.dumps(TARGETS, sort_keys=True))
    require(isinstance(target, str) and re.fullmatch('[0-9a-f]{40}', target) and target != '0' * 40 and
            target == EXPECTED_BACKEND_SHA, 'Wrong/unbound primary backend checkpoint')
    require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha') == 0, 'Cannot read backend SHA')
    require((REPORTS / 'backend-sha.log').read_text().strip() == target, 'Backend checkout SHA mismatch')
    require(static_source_pins_match(), 'Reviewed Backend17 corrected test sources hash/type mismatch')
    require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-before') == 0 and
            not (REPORTS / 'source-before.log').read_text().strip(), 'Backend checkout is not clean')
    require(command(['git', '-C', str(ADMIN), 'rev-parse', 'HEAD'], 'admin-sha') == 0, 'Cannot read Admin SHA')
    require((REPORTS / 'admin-sha.log').read_text().strip() == os.environ.get('GITHUB_SHA'), 'Carrier checkout SHA mismatch')
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
    scope_bytes = STATIC_SCOPE_INIT.encode('utf-8')
    require(hashlib.sha256(scope_bytes).hexdigest() == SCOPE_INIT_SHA, 'Private static-scope init hash mismatch')
    with (W01 / 'backend17-pg03-static-scope.init.gradle').open('xb') as output: output.write(scope_bytes)
    shutil.copyfile(W01 / 'backend17-pg03-static-scope.init.gradle', REPORTS / 'backend17-pg03-static-scope.init.gradle')
    note('Exact two-test-file static init: ' + SCOPE_INIT_SHA)
    require(command(['java', '-XshowSettings:properties', '-version'], 'java-version') == 0, 'JDK settings/version command failed')
    java_tmp = re.findall(r'^\s*java\.io\.tmpdir\s*=\s*(.*?)\s*$', (REPORTS / 'java-version.log').read_text(), re.MULTILINE)
    require(java_tmp == [str(TEMP)], 'JVM temp escaped the owned directory; no batch started')
    require(command(['docker', 'version'], 'docker-version') == 0, 'Docker unavailable; no runtime installation attempted')
    require(command(['docker', 'ps', '-aq', '--no-trunc'], 'preexisting-containers', extra={'DOCKER_API_VERSION': '1.32'}) == 0, 'Docker API 1.32 unsupported/unavailable; refusing without adaptation')
    before = set((REPORTS / 'preexisting-containers.log').read_text().splitlines())
    require(not before, 'Expected a dedicated clean hosted runner; do not touch preexisting containers')
    # Historical MVC73/service5/conditional-response5 and unchanged main statics are not replayed.
    require(not CANCELLED, 'Cancelled before validation')
    started = True
    tasks = ['compileKotlin', 'compileTestKotlin', 'test', '--tests', SELECTORS[0], 'ktlintTestSourceSetCheck', 'detekt', '--continue', '-x', 'jacocoTestReport']
    gradle_exit = command(['./gradlew', '--no-daemon', '--no-parallel', '--no-configuration-cache', '--console=plain', '--max-workers=1', '--no-build-cache', '-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m', '-Dorg.gradle.vfs.watch=false', '-Pkotlin.compiler.execution.strategy=in-process', '-PkiraUseMavenLocal=false', '-Porg.gradle.java.installations.auto-download=false', '--init-script', str(W01 / 'original.init.gradle'), '--init-script', str(W01 / 'backend17-pg03-static-scope.init.gradle'), *tasks], 'gradle-test', 18 * 60)
    result = gradle_exit
except (Exception, KeyboardInterrupt) as failure:
    note('FAIL: ' + str(failure))
    result = 1
finally:
    def cleanup_command(argv, name):
        global cleanup_failed
        try:
            ok = command(argv, name, cleaning=True) == 0
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
        for tool in EXPECTED_STATIC_TASKS:
            path = W01 / ('backend-build/reports/backend17-pg03-' + tool + '-scope.json')
            if path.is_file(): shutil.copyfile(path, REPORTS / ('static-scope-' + tool + '.json'))
        preserved = True  # Missing output is reported below; a failed copy forbids its deletion.
        for tool in EXPECTED_STATIC_TASKS:
            path = REPORTS / ('static-scope-' + tool + '.json')
            try: observation = json.loads(path.read_text())
            except Exception as failure: observation = {'status': 'MISSING_OR_UNREADABLE', 'error': str(failure)}
            static_scopes[tool] = observation
            note('Raw static source observation: ' + json.dumps({'tool': tool, 'settled': workers_gone, 'observation': observation}, sort_keys=True))
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
            require(len(identities) == expected and set(identities) == EXPECTED_XML_IDENTITIES, 'Wrong/duplicate exact PG03 testcase identity')
            require(not any(node.tag in ('failure', 'error', 'skipped') for node in suite.iter()), 'Failure/error/skip in focused XML')
        xml_verified = True
        require(all(static_reports.get(tool) for tool in ('ktlint', 'detekt')), 'Missing static reports')
        for tool, task in EXPECTED_STATIC_TASKS.items():
            require(static_scopes.get(tool) == {
                'schema': 'backend17.pg03.static-scope.v1', 'phase': 'before-task-action',
                'tool': tool, 'task': task, 'static_files': EXPECTED_STATIC_FILES,
                'graph': EXPECTED_TASK_GRAPH, 'policy': EXPECTED_STATIC_POLICY,
            }, 'Missing/wrong exact-file static scope evidence: ' + tool)
        static_scopes_verified = True
        require(static_source_pins_match(), 'Reviewed Backend17 corrected test sources changed during validation')
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
    passed = result == 0 and gradle_exit == 0 and xml_verified and static_scopes_verified and sources_clean and preserved and ownership_status == 'COMPLETE' and not cleanup_failed and not CANCELLED
    note(f'validation_result={result}; process_ownership={process_status}; container_ownership={container_status}; ownership={ownership_status}; cleanup_failed={cleanup_failed}; cancelled={CANCELLED}; job_exit={0 if passed else 1}')
    (REPORTS / 'result.json').write_text(json.dumps({'backend_sha': TARGETS['backend_sha'], 'carrier_sha': os.environ.get('GITHUB_SHA'), 'classes': CLASSES, 'selectors': SELECTORS, 'static_files': STATIC_FILES, 'scope_init_sha256': SCOPE_INIT_SHA, 'gradle_exit': gradle_exit, 'validation_exit': result, 'xml_verified': xml_verified, 'xml': xml_observations, 'static_reports': static_reports, 'static_scopes': static_scopes, 'static_scopes_verified': static_scopes_verified, 'sources_clean': sources_clean, 'reports_preserved': preserved, 'drains': DRAINS, 'process_ownership_status': process_status, 'container_ownership_status': container_status, 'ownership_status': ownership_status, 'cleanup_failed': cleanup_failed, 'containers_absent': containers_absent, 'container_force_requested': container_force_requested, 'cancelled': CANCELLED, 'outputs_absent': outputs_absent, 'status': 'PASS' if passed else 'FAIL'}, indent=2) + '\n')
raise SystemExit(0 if passed else 1)
