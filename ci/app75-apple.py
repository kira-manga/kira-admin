"""One private App75 compilation recipe. Definitions only on import; no local execution authority."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import sys
import time

CONTROL = Path(__file__).resolve().parents[1]
TASKS = [':data:compileKotlinIosSimulatorArm64', ':ui:compileKotlinIosSimulatorArm64']
MODULES = (':core', ':domain', ':platform', ':data:local', ':data:remote', ':sources:legacy',
           ':data:download', ':sources:contracts', ':data', ':presentation', ':ui')
MAINS = [module + ':compileKotlinIosSimulatorArm64' for module in MODULES]
KSP = ':data:local:kspKotlinIosSimulatorArm64'
CINTEROP = ':platform:cinteropLibwebpIosSimulatorArm64'
REQUIRED = MAINS + [KSP, CINTEROP]
OWNER_HASH = '9f69c87182eba29030fcd65c49b4e8459a41749440dab9767f3fbfe0c02db6cf'
INPUTS_HASH = '62826a371557dfef8f1fcae983fdf657f317df6072ecac4e795157e668b6e9f2'
XCODE = '/Applications/Xcode_26.4.1.app/Contents/Developer'
SCRATCH = ('gradle-home', 'konan', 'home', 'tmp', 'project-cache', 'kotlin', 'work')
OUTPUTS = ('build', *(module[1:].replace(':', '/') + '/build' for module in MODULES), '.gradle', '.kotlin')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular bound file: ' + str(path))
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def read_json(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 65536, 'Invalid JSON input')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise RuntimeError('Non-finite JSON')
    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=constant)


def validate_request(request, context):
    fixed = {'schema': 'app75-apple-private-v1', 'authorization': 'APP75_APPLE01_ONE_ATTEMPT_AUTHORIZED',
             'sourceRepository': 'kira-manga/kira-app', 'tasks': TASKS, 'expectedRunAttempt': 1,
             'sourceInputsSha256': INPUTS_HASH, 'ownerHelperSha256': OWNER_HASH, 'developerDir': XCODE,
             'coldPublicAcquisitionAuthorized': True,
             'android05ReviewSha256': 'a8982200e42538a3cc0f53fc334f01be9fc04ea5549b71b317c713db345fbcbb',
             'desktop04ReviewSha256': '76818634e9e354d5c7a5ebbb6364c8731f426fb3c4f5d337ec0a83bb2e80481a',
             'desktop04AcceptanceSha256': '16be9a2a7613bc614b6e779a3ab64d0de91bf7475129383edc83de647067e93b'}
    require(isinstance(request, dict)
            and set(request) == set(fixed) | {'sourceSha', 'controllerSha256', 'initSha256', 'workflowSha256'},
            'Unknown/missing request field')
    require(type(request['expectedRunAttempt']) is int, 'Run attempt must be an integer, not a boolean')
    require(type(request['coldPublicAcquisitionAuthorized']) is bool, 'Acquisition authorization must be boolean')
    require(all(request[key] == value for key, value in fixed.items()), 'Unbound or unauthorized request')
    sha = request['sourceSha']
    require(isinstance(sha, str) and re.fullmatch('[0-9a-f]{40}', sha) and sha != '0' * 40, 'Exact source SHA required')
    for key in ('controllerSha256', 'initSha256', 'workflowSha256'):
        require(isinstance(request[key], str) and re.fullmatch('[0-9a-f]{64}', request[key]), 'Invalid control hash')
    expected = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'kira-manga/kira-admin',
                'GITHUB_REF': 'refs/heads/remediation/app-29-backend-complaints', 'GITHUB_EVENT_NAME': 'push',
                'GITHUB_RUN_ATTEMPT': '1', 'RUNNER_OS': 'macOS', 'RUNNER_ARCH': 'ARM64',
                'RUNNER_ENVIRONMENT': 'github-hosted'}
    require(all(context.get(key) == value for key, value in expected.items()), 'Wrong private hosted invocation')
    require(re.fullmatch('[1-9][0-9]*', context.get('GITHUB_RUN_ID', '')) is not None, 'Invalid run identity')
    require(re.fullmatch('[0-9a-f]{40}', context.get('GITHUB_SHA', '')) is not None, 'Invalid carrier SHA')
    return sha


def checked_request():
    request = read_json(CONTROL / 'ci/app75-apple.request.json')
    validate_request(request, os.environ)
    require(read_json(Path(os.environ['GITHUB_EVENT_PATH']))['repository']['private'] is True, 'Carrier is not private')
    files = {'controllerSha256': 'ci/app75-apple.py', 'initSha256': 'ci/app75-apple.init.gradle',
             'workflowSha256': '.github/workflows/app75-apple.yml', 'ownerHelperSha256': 'ci/app8-apple.py',
             'sourceInputsSha256': 'ci/app75-apple-source-inputs.json'}
    require(all(digest(CONTROL / path) == request[key] for key, path in files.items()), 'Bound controller/helper changed')
    return request


def child_environment(run, original):
    marker = 'app75.apple.owner=' + run.name
    result = {'PATH': original['PATH'], 'JAVA_HOME': original['JAVA_HOME'], 'HOME': str(run / 'home'),
              'GRADLE_USER_HOME': str(run / 'gradle-home'), 'KONAN_DATA_DIR': str(run / 'konan'),
              'TMPDIR': str(run / 'tmp') + '/', 'DEVELOPER_DIR': XCODE, 'CI': 'true',
              'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'GIT_CONFIG_NOSYSTEM': '1',
              'GIT_CONFIG_GLOBAL': '/dev/null', 'KIRA_SOURCE_CONFIG_BASE_URL': '', 'KIRA_SOURCE_CONFIG_PINNED_KEYS': '',
              'KIRA_APP_VERSION': '1.0.5', 'APP75_RUN': str(run), 'APP75_PROOF': str(run / 'reports/task-proof.json'),
              'JAVA_OPTS': f'-Xmx128m -D{marker} -Duser.home={run / "home"} -Djava.io.tmpdir={run / "tmp"}'}
    for key in ('ANDROID_HOME', 'ANDROID_SDK_ROOT'):
        if original.get(key):
            result[key] = original[key]
    return result


def compilation_argv(source, run):
    return [str(source / 'gradlew'), '-p', str(source), *TASKS, '--no-daemon', '--no-parallel', '--max-workers=1',
            '--no-build-cache', '--no-configuration-cache', '--console=plain', '--stacktrace',
            '--project-cache-dir', str(run / 'project-cache'), '-I', str(CONTROL / 'ci/app75-apple.init.gradle'),
            '-Pkotlin.compiler.execution.strategy=in-process', '-Pkotlin.native.disableCompilerDaemon=false',
            '-Pkotlin.native.parallelThreads=1',
            '-Pkotlin.incremental=false', '-PkiraUseMavenLocal=false',
            '-Porg.gradle.java.installations.auto-download=false', '-Dorg.gradle.vfs.watch=false',
            '-Pkotlin.project.persistent.dir=' + str(run / 'kotlin'),
            f'-Dorg.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=768m -Dapp75.apple.owner={run.name} '
            f'-Duser.home={run / "home"} -Djava.io.tmpdir={run / "tmp"}']


def absence(commands, run, source):
    settled = commands.drain()
    rows = commands.census(cleaning=True)
    workers = [row for row in rows if row['pid'] != os.getpid() and not row['state'].startswith('Z')
               and any(value in row['command'] for value in (str(run), str(source), 'app75.apple.owner=' + run.name))]
    return {'absent': settled and not workers, 'groupsSettled': settled, 'remainingOwned': workers}


def remove_scoped(root, names):
    require(root.is_dir() and root.resolve() == root and not root.is_symlink(), 'Unsafe cleanup owner')
    removed = []
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.resolve().is_relative_to(root), 'Unsafe cleanup root')
        if path.exists():
            require(path.is_dir(), 'Expected owned generated directory')
            shutil.rmtree(path)
        require(not path.exists(), 'Owned scratch remains')
        removed.append(name)
    return removed


def output_proof(source, reports, request):
    proof = read_json(reports / 'task-proof.json')
    require(proof['schema'] == 'app75-apple-task-v1' and proof['requestedTasks'] == TASKS
            and proof['requiredTasks'] == REQUIRED and proof['sourceSha'] == request['sourceSha']
            and proof['gradleVersion'] == '9.6.1', 'Missing real task proof')
    work = proof['work']
    require(set(work) == set(REQUIRED), 'Missing/extra required action receipt')
    entries, files, task_files, total = set(), {}, {}, 0
    for task in REQUIRED:
        state = proof['states'][task]
        require(all(state[name] is True for name in ('executed', 'didWork', 'actionsReachedEnd'))
                and all(state[name] is False for name in ('skipped', 'upToDate', 'noSource'))
                and state['failure'] is None, 'Required action did not execute normally: ' + task)
        row = work[task]
        require(isinstance(row['outputs'], list) and len(row['outputs']) == 1, 'Invalid declared output')
        if task in MAINS:
            require(row['target'] == 'ios_simulator_arm64' and row['sourceCount'] > 0, 'Wrong/empty main target')
        module = task.rsplit(':', 1)[0][1:].replace(':', '/')
        root = source / module / 'build'
        path = source / row['outputs'][0]
        require(path.exists() and not path.is_symlink() and path.resolve().is_relative_to(root),
                'Unexpected output path')
        task_files[task] = []
        for item in ([path] if path.is_file() else path.rglob('*')):
            require(not item.is_symlink() and item.resolve().is_relative_to(root), 'Unsafe compiler output')
            entries.add(item)
            # Primary-approved proportional inventory bound: 11 main klibs + KSP/cinterop, not one App3 klib.
            require(len(entries) <= 4096, 'Oversized output inventory')
            if item.is_file():
                require(item not in files, 'Overlapping output ownership')
                size = item.stat().st_size
                total += size
                require(total <= 67108864, 'Oversized compiler output')
                files[item] = {'task': task, 'path': str(item.relative_to(source)), 'bytes': size, 'sha256': digest(item)}
                task_files[task].append(item)
        require(task_files[task], 'Missing required output: ' + task)
        if task != KSP:
            require(any(item.suffix == '.klib' or item.name == 'manifest' for item in task_files[task]),
                    'No compiled klib output: ' + task)
    generated = work[KSP]['generatedSources']
    require(len(generated) == 2 and {Path(name).name for name in generated} ==
            {'MangaDatabase_Impl.kt', 'ChapterDownloadDao_Impl.kt'}, 'Missing/ambiguous Room source receipts')
    room = []
    for name in generated:
        path = source / name
        require(path in task_files[KSP] and path.stat().st_size <= 131072, 'Missing/oversized generated Room source')
        room.append(dict(files[path], utf8=path.read_bytes().decode('utf-8')))
    result = {'sourceSha': request['sourceSha'], 'entryCount': len(entries), 'fileCount': len(files), 'bytes': total,
              'files': [files[path] for path in sorted(files)], 'roomGenerated': room}
    require(len((json.dumps(result, sort_keys=True, indent=2) + '\n').encode('utf-8')) <= 2097152,
            'Oversized output receipt')
    return result


def native_markers(run):
    # File evidence only; never invoke another compiler or hash/copy the whole SDK/distribution.
    roots = list((run / 'konan').glob('kotlin-native*'))
    require(len(roots) == 1 and 'macos-aarch64' in roots[0].name and roots[0].name.endswith('-2.4.0'),
            'Missing/ambiguous Kotlin Native 2.4.0 host distribution')
    root = roots[0]
    require(root.is_dir() and not root.is_symlink(), 'Invalid native distribution directory')
    names = ('konan/konan.properties', 'bin/konanc')
    return {'distribution': root.name, 'kotlinVersionFromBoundCatalog': '2.4.0',
            'markers': {name: digest(root / name) for name in names}}


def run_recipe(owner, source, run, request, system):
    """Fixed recipe; the borrowed owner supplies all child launch, wait, census and signal logic."""
    source_inputs = read_json(CONTROL / 'ci/app75-apple-source-inputs.json')
    end = time.monotonic() + 1440
    work_end = end - 240
    env = child_environment(run, os.environ)
    env['APP75_SOURCE_SHA'] = request['sourceSha']
    commands = None
    reports, errors, started, source_ready = run / 'reports', [], False, False
    result = {'schema': 'app75-apple-result-v1', 'passed': False, 'sourceSha': request['sourceSha'],
              'carrierSha': os.environ['GITHUB_SHA'], 'tasks': TASKS, 'run': run.name, 'system': system, 'errors': errors,
              'limits': {'workSeconds': 1200, 'cleanupReserveSeconds': 240, 'stopSecondsEach': 40,
                         'sampledCommandLogBytes': 1048576, 'sampledTotalCommandLogBytes': 4194304,
                         'outputInventoryEntries': 4096, 'outputInventoryBytes': 67108864,
                         'roomSourceBytesEach': 131072, 'outputReceiptBytes': 2097152}}
    owner.save(run / 'owner.json', {'run': run.name, 'pid': os.getpid(), 'sourceSha': request['sourceSha']})
    owner.save(reports / 'request.json', request)
    owner.save(reports / 'result.json', result)  # Fail-closed evidence even if the helper capability gate refuses.
    def stop(label):
        try:
            commands.call([str(source / 'gradlew'), '--stop'], label, seconds=40, cleaning=True)
        except Exception as error:
            errors.append(label + ': ' + str(error))
    try:
        owner.deadline_capabilities()
        commands = owner.Commands(run, env, end)
        git = ['/usr/bin/git', '-C', str(source)]
        require(commands.call(git + ['rev-parse', 'HEAD'], 'source-sha', end=work_end).strip() == request['sourceSha'], 'Source SHA mismatch')
        require(not commands.call(git + ['status', '--porcelain', '--untracked-files=all'], 'source-clean', end=work_end), 'Dirty source checkout')
        inputs = {path: digest(source / path) for path in source_inputs}
        require(inputs == source_inputs, 'Reviewed source/build input changed')
        require(all(not (source / name).exists() and not (source / name).is_symlink() for name in OUTPUTS),
                'Preexisting generated output; refuse compilation and source cleanup')
        source_ready = True
        owner.save(reports / 'source.json', {'sha': request['sourceSha'], 'inputs': inputs})
        tools = {'python': sys.version, 'pythonExecutable': sys.executable, 'developerDir': XCODE}
        tools['java'] = commands.call([str(Path(env['JAVA_HOME']) / 'bin/java'), '-version'], 'java-version', end=work_end)
        tools['xcode'] = commands.call(['/usr/bin/xcodebuild', '-version'], 'xcode-version', end=work_end)
        tools['sdk'] = commands.call(['/usr/bin/xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], 'sdk-version', end=work_end)
        require(tools['xcode'].strip() == 'Xcode 26.4.1\nBuild version 17E202' and tools['sdk'].strip() == '26.4',
                'Selected Xcode/SDK differs from the bound toolchain')
        owner.save(reports / 'tools.json', tools)
        started = True
        commands.call(compilation_argv(source, run), 'compile', seconds=1200, end=work_end)
        result['compileSucceeded'] = True
    except Exception as error:
        errors.append('validation: ' + str(error))
    finally:
        if started:
            stop('gradle-stop-immediate')
        try:
            result['afterImmediateStop'] = (absence(commands, run, source) if commands else
                                            {'absent': True, 'noChildOwnerCreated': True})
            require(result['afterImmediateStop']['absent'], 'Owned workers remain; retain outputs/scratch')
            if source_ready and started:
                try:
                    if result.get('compileSucceeded'):
                        owner.save(reports / 'outputs.json', output_proof(source, reports, request), limit=2097152)
                        owner.save(reports / 'native-markers.json', native_markers(run))
                        result['outputProofPreserved'] = True
                    require({path: digest(source / path) for path in source_inputs} == source_inputs,
                            'Source/build inputs changed during compilation')
                    require(not commands.call(['/usr/bin/git', '-C', str(source), 'status', '--porcelain', '--untracked-files=all'],
                                              'source-after', cleaning=True).strip(), 'Tracked/untracked source changed during compilation')
                except Exception as error:
                    errors.append('evidence: ' + str(error))
                result['outputsRemoved'] = remove_scoped(source, OUTPUTS)
        except Exception as error:
            errors.append('preserve/clean: ' + str(error))
        if started:
            stop('gradle-stop-final')
        try:
            result['afterFinalStop'] = (absence(commands, run, source) if commands else
                                        {'absent': True, 'noChildOwnerCreated': True})
            require(result['afterFinalStop']['absent'], 'Owned workers remain; retain scratch')
            result['scratchRemoved'] = remove_scoped(run, SCRATCH)
        except Exception as error:
            errors.append('final ownership/clean: ' + str(error))
            if commands is not None:
                try:
                    commands.retire_observer()  # One final existing-owner opportunity; never another census.
                except Exception as retirement_error:
                    errors.append('final observer retirement: ' + str(retirement_error))
                try:
                    commands.checkpoint()  # Also persist errors caught inside retire_observer itself.
                except Exception as checkpoint_error:
                    errors.append('final observer retirement receipt: ' + str(checkpoint_error))
        result['sourceBaselineVerified'] = source_ready
        result['compileAttempted'] = started
        result['normalOwnedCompletion'] = commands.normal() if commands else False
        result['cancelled'] = owner.CANCELLED
        result['logBytesBeforeRetentionCap'] = {path.name: path.stat().st_size for path in reports.glob('*.log')}
        remaining = 4194304
        for path in sorted(reports.glob('*.log')):
            limit = min(1048576, remaining)
            with path.open('rb') as stream:
                prefix = stream.read(limit)
            if path.stat().st_size > limit:
                errors.append('Log cap exceeded: ' + path.name)
            # Stable bounded prefix even on an incomplete owned-worker cleanup; later writes
            # cannot enlarge the retained inode. This is not an instantaneous execution disk cap.
            pending = path.with_suffix('.retained')
            with pending.open('xb') as stream:
                stream.write(prefix)
            pending.replace(path)
            remaining -= len(prefix)
        result['passed'] = bool(result.get('compileSucceeded') and result.get('outputProofPreserved')
                                and result.get('outputsRemoved') == list(OUTPUTS)
                                and result.get('scratchRemoved') == list(SCRATCH)
                                and not errors and result['normalOwnedCompletion'] and not owner.CANCELLED)
        owner.save(reports / 'result.json', result)
    return 0 if result['passed'] else 1


def compile_once(request):
    require(os.uname().sysname == 'Darwin' and os.uname().machine == 'arm64', 'macOS ARM required')
    with Path('/System/Library/CoreServices/SystemVersion.plist').open('rb') as stream:
        system = plistlib.load(stream)
    require(system['ProductVersion'].startswith('26.') and Path(XCODE).is_dir(), 'Required macOS26/Xcode unavailable')
    workspace, temporary = Path(os.environ['GITHUB_WORKSPACE']).resolve(), Path(os.environ['RUNNER_TEMP']).resolve()
    source, run = workspace / 'app75-source', Path(os.environ['APP75_RUN'])
    require(CONTROL == workspace / 'control' and source.is_dir() and not source.is_symlink(), 'Wrong checkout paths')
    require(run == temporary / ('app75-apple-' + os.environ['GITHUB_RUN_ID'] + '-1')
            and run.resolve() == run and not run.exists() and not any(c.isspace() for c in str(run)), 'Unsafe/nonfresh run root')
    spec = importlib.util.spec_from_file_location('app75_existing_darwin_owner', CONTROL / 'ci/app8-apple.py')
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)  # Definitions only; never App8 main/PF/Simulator. No scratch if import fails.
    run.mkdir(mode=0o700)
    for name in (*SCRATCH, 'reports'):
        (run / name).mkdir()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, owner.interrupted)
    return run_recipe(owner, source, run, request, system)


def main():
    require(sys.argv[1:] in (['request'], ['compile']), 'Expected one fixed phase')
    request = checked_request()
    if sys.argv[1] == 'request':
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as stream:
            stream.write('source_sha=' + request['sourceSha'] + '\n')
        return 0
    return compile_once(request)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('APP75 APPLE INCOMPLETE: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
