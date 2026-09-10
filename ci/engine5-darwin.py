"""TARGETED NATIVE DRAFT with R4 diagnostics: closed Engine5 lane, not a general runner. Review before execution."""
import hashlib, json, os, platform, plistlib, re, select, shutil, signal, subprocess, sys, tarfile, time
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

CONTROL = Path(__file__).resolve().parent.parent
RUN = Path(os.environ['ENGINE5_RUN'])
REPORTS = RUN / 'reports'
OWNER = os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT']
VERSION = '0.1.0-engine5-darwin-' + OWNER
INPUTS = CONTROL / 'docs/remediation/engine5-darwin'
XCODE = {'neutral': '/Applications/Xcode_26.0.1.app/Contents/Developer',
         'app': '/Applications/Xcode_26.4.1.app/Contents/Developer'}
PINS = {
    'neutral': ('fc55c149398068d1f47c2fb08597dbc08f0bf28a',
                '28e6f5df04b5514b76b04ad43ce8a667f80cfc9059db506137a9e1888c28baff',
                'a2a8270df4c39db59edeaabac70a44d2903512359124bb0a588f574e9c9ff5cb', 58),
    'app': ('c0db2f63c916932dbed1a3314c9a06d30c1696b5',
            '5c4e739191cdf8b5bca0b5c20d65dd7df27feb69c609a069561651952a0bf428',
            '77e3421d5dc999ef01f6fcc4c419a4089de6d0c732decd7bdb04047c98af5653', 2768),
}
APP_BASELINE_MANIFEST = '2db3aa3bf6373e9debf80c51b47c73e9d129f2e49a418f33915a1276228730b9'
APP_WRITER = {
    'path': 'composeApp/src/commonTest/kotlin/me/manga/kira/sources/runtime/SourceHttpLoopback.kt',
    'beforeSha256': 'be63b5eff16382b5d3e39b0f2a7bd5dc4552fb7e6b0be23a8a6f9c9bdffe6091',
    'afterSha256': 'b7a52c4c0e71afc8e422d7b6d63776888f539488fa2024981dd945d21150fc1d',
    'patchSha256': '5ae20d2ef9415f47b971e5e18401de42b5be1663a6b349bbdbac4a08c79f927d',
    'manifestSha256': '0cc99c2675e9d94dee4f043f266c489975f4e7404afe564ba1796774d173ec5a',
    'reviewSha256': '4d91e0f277bd71b2ca74d69ef66ec4c1eb6bda7290b3eefe4976c2a1f64159cb',
}
NATIVE_HOST_PROJECT = ':engine5DarwinBoundary'
NATIVE_HOST_BUILD = 'ci/engine5-darwin.host.gradle.kts'
NATIVE_HOST_SOURCE_SETS = {
    'commonMain': ['composeApp/src/commonMain/kotlin/me/manga/kira/sources/runtime/KtorHttpExecutor.kt'],
    'commonTest': ['composeApp/src/commonTest/kotlin/me/manga/kira/sources/runtime/' + name for name in (
        'SourceHttpTestFixture.kt', 'SourceHttpLoopback.kt', 'SourceHttpLoopbackCases.kt')],
    'iosSimulatorArm64Test': ['composeApp/src/iosTest/kotlin/me/manga/kira/sources/runtime/KtorSourceDarwinBoundaryTest.kt'],
}
MIB = 1024 * 1024
JSON_LIMIT, TOOL_CAPTURE_LIMIT, TOOL_LOG_LIMIT = MIB, MIB, 4 * MIB
GRADLE_LOG_LIMIT, XML_LIMIT, EVIDENCE_LIMIT = 8 * MIB, 4 * MIB, 32 * MIB
DISK_FLOOR = 8 * 1024 * MIB
TOOL_SIGNALS = []
DEADLINE_SECONDS = {'publish': 480, 'test': 1080}
DEADLINE_GRACE_SECONDS, DEADLINE_REAP_SECONDS = 10, 2
PROCESS_IDENTITY_LIMIT = 32

def deadline_capabilities():
    # CPython documents waitid on macOS from 3.13; reject an older/different interpreter, never install one.
    require(all(hasattr(os, name) for name in ('waitid', 'P_PID', 'WEXITED', 'WNOHANG', 'WNOWAIT', 'CLD_EXITED', 'killpg')),
            'Python lacks non-reaping POSIX deadline ownership APIs; no installation/fallback')
    require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL,
            'Deadline requires default SIGCHLD handling; an automatic reaper would lose group ownership')

def identity_rows(raw):
    # Numeric fields plus ps comm, not argv/environment. Callers retain only their already-owned targets.
    for row in raw.splitlines():
        parts = row.split(None, 5)
        require(len(parts) == 6 and all(value.isdigit() for value in parts[:4]), 'Malformed process identity census')
        yield {'pid': int(parts[0]), 'uid': int(parts[1]), 'ppid': int(parts[2]), 'pgid': int(parts[3]),
               'state': parts[4][:16], 'executable': PurePosixPath(parts[5]).name[:256]}

def deadline_live_pids(pgid, seconds=1, identity=None):
    # Reuse bounded small-tool capture, never pipe/buffer Gradle through command(). No census during TERM grace.
    rows = command(['ps', '-axww', '-o', 'pid=,uid=,ppid=,pgid=,stat=,comm='], seconds=seconds, log_output=False)
    live, owned = [], []
    for row in identity_rows(rows):
        if row['pgid'] == pgid:
            row['basis'] = ['process-group-held-by-unreaped-leader']
            owned.append(row) # Keep zombie identity too, without changing the live/quiet predicate.
            if not row['state'].startswith('Z'): live.append(row['pid'])
    require(len(live) <= 1024, 'Oversized deadline group inventory')
    if identity is not None:
        identity.update(observedMonotonicSeconds=time.monotonic(), ownedCount=len(owned),
                        omittedOwnedCount=max(0, len(owned) - PROCESS_IDENTITY_LIMIT),
                        processes=sorted(owned, key=lambda row: row['pid'])[:PROCESS_IDENTITY_LIMIT])
    return sorted(live)

def deadline():
    scope()
    require(len(sys.argv) >= 4 and sys.argv[2] in DEADLINE_SECONDS, 'Expected closed deadline publish/test role and argv')
    deadline_capabilities()
    role, argv = sys.argv[2], sys.argv[3:]
    started = time.monotonic()
    expires = started + DEADLINE_SECONDS[role]
    receipt = {'deadline': 'INCOMPLETE', 'role': role, 'argv': argv, 'seconds': DEADLINE_SECONDS[role],
               'graceSeconds': DEADLINE_GRACE_SECONDS, 'reapSeconds': DEADLINE_REAP_SECONDS,
               'startNewSession': True, 'childPid': None, 'pgid': None, 'childExitCode': None,
               'timedOut': False, 'forced': False, 'groupQuiet': False, 'leaderReaped': False,
               'signalAttempts': [], 'errors': {}, 'startMonotonicSeconds': started, 'lastGroupIdentity': {}}
    process, quiet, leader_owned = None, False, True
    first_signal, repeated_signal = None, False
    handlers = {}

    def interrupted(signum, _frame):
        # Never raise across Popen's spawn-to-assignment window; repeated signals cannot reset the grace clock.
        nonlocal first_signal, repeated_signal
        if first_signal is None: first_signal = signum
        else: repeated_signal = True

    def error(phase, failure): receipt['errors'][phase] = str(failure)[:1000]

    def checkpoint():
        try:
            receipt.update(elapsedSeconds=time.monotonic() - started,
                           interruptedBy=signal.Signals(first_signal).name if first_signal is not None else None,
                           repeatedInterruption=repeated_signal)
            save(REPORTS / (role + '-deadline.json'), receipt)
        except BaseException as failure:
            error('receipt', failure)
            return False
        return True

    def peek():
        nonlocal leader_owned
        try: return os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError:
            leader_owned = False
            raise RuntimeError('Leader was unexpectedly reaped; refuse signaling a potentially recycled PGID')

    def send(attempt, sig):
        attempt['attemptedAfterSeconds'] = time.monotonic() - started
        try:
            os.killpg(process.pid, sig)
            attempt['outcome'] = 'sent'
        except ProcessLookupError: attempt['outcome'] = 'alreadyGone'
        except BaseException as failure:
            attempt['outcome'] = 'failed'
            error(sig.name, failure)

    def force_group():
        receipt['forced'] = True
        # No wait()/poll() until all group signaling is finished: even an exit-0 leader pins the numeric PGID.
        try: peek()
        except BaseException as failure: error('ownership', failure)
        if not leader_owned: return
        attempts = [{'pgid': process.pid, 'signal': sig.name, 'outcome': 'planned'}
                    for sig in (signal.SIGTERM, signal.SIGKILL)]
        receipt['signalAttempts'] = attempts
        checkpoint() # Both intents before TERM. Receipt failure must not abandon this explicitly owned group.
        # Diagnostic snapshot at the existing signal-receipt boundary, after ownership/intents and before grace.
        # This is not the KILL-instant membership; a diagnostic failure must not abandon the owned group.
        receipt['beforeSignalGroupIdentity'] = {}
        try: deadline_live_pids(process.pid, identity=receipt['beforeSignalGroupIdentity'])
        except BaseException as failure: receipt['beforeSignalGroupIdentity']['error'] = str(failure)[:1000]
        checkpoint()
        grace_end = time.monotonic() + DEADLINE_GRACE_SECONDS
        try:
            send(attempts[0], signal.SIGTERM)
            while time.monotonic() < grace_end:
                time.sleep(min(0.1, max(0, grace_end - time.monotonic())))
        finally:
            # No census, receipt writes or subprocess waits between TERM and KILL; grace never restarts.
            send(attempts[1], signal.SIGKILL)
        checkpoint()

    try:
        require(checkpoint(), 'Cannot record deadline start')
        for sig in (signal.SIGTERM, signal.SIGINT):
            handlers[sig] = signal.signal(sig, interrupted)
        require(first_signal is None, 'Interrupted before deadline child spawn')
        # Inherit stdout/stderr into the unchanged external bounded capture; argv is not interpreted by a shell.
        process = subprocess.Popen(argv, start_new_session=True)
        receipt.update(childPid=process.pid, pgid=process.pid)
        require(checkpoint(), 'Cannot record deadline child ownership')
        while True:
            if first_signal is not None:
                receipt['reason'] = 'interrupted'
                break
            if time.monotonic() >= expires:
                receipt.update(timedOut=True, reason='timeout')
                break
            info = peek()
            if info is not None:
                remaining = expires - time.monotonic()
                if remaining <= 0: continue
                live = deadline_live_pids(process.pid, seconds=min(1, remaining), identity=receipt['lastGroupIdentity'])
                receipt['lastLivePids'] = live
                if first_signal is not None or time.monotonic() >= expires: continue
                if not live:
                    quiet = True
                    break
                if info.si_code != os.CLD_EXITED or info.si_status != 0:
                    receipt['reason'] = 'child-failed-with-live-group'
                    break
            time.sleep(min(0.1, max(0, expires - time.monotonic())))
    except BaseException as failure:
        error('run', failure)
    finally:
        try:
            if process is not None:
                try:
                    if not quiet:
                        force_group()
                        receipt['lastLivePids'] = deadline_live_pids(
                            process.pid, identity=receipt['lastGroupIdentity'] if leader_owned else None)
                        quiet = not receipt['lastLivePids']
                except BaseException as failure: error('groupCleanup', failure)
                finally:
                    # Signaling is now closed forever, including if reaping/census/receipt recording fails.
                    try:
                        receipt['childExitCode'] = process.wait(timeout=DEADLINE_REAP_SECONDS)
                        receipt['leaderReaped'] = True
                    except BaseException as failure: error('reap', failure)
            receipt['groupQuiet'] = quiet
            receipt['deadline'] = 'PASS' if (quiet and receipt['leaderReaped'] and receipt['childExitCode'] == 0
                and not receipt['forced'] and first_signal is None and not receipt['errors']) else 'FAIL'
            checkpoint()
        finally:
            for sig, handler in handlers.items(): signal.signal(sig, handler)
    # Also reject an interruption or receipt failure in the final checkpoint/handler-restoration window.
    if first_signal is not None or receipt['errors']:
        receipt['deadline'] = 'FAIL'
        checkpoint()
    require(receipt['deadline'] == 'PASS', 'Deadline phase failed: ' + role)

def require(ok, message):
    if not ok: raise RuntimeError(message)

def digest(path):
    with path.open('rb') as stream:
        value = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''): value.update(block)
        return value.hexdigest()

def save(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    require(len(data) <= JSON_LIMIT, 'Oversized JSON; refuse partial receipt: ' + path.name)
    path.write_bytes(data)

def limit_receipt(name, limit, observed):
    save(REPORTS / (name + '.limit.json'), {'status': 'FAIL', 'truncated': True,
         'file': name, 'limitBytes': limit, 'observedBytesAtLeast': observed})

def append_log(name, data, limit=TOOL_LOG_LIMIT):
    path = REPORTS / name
    size = path.stat().st_size if path.exists() else 0
    with path.open('ab') as log: log.write(data[:max(0, limit - size)])
    if size + len(data) > limit: limit_receipt(name, limit, size + len(data))

def capture():
    # Drain the bounded Gradle pipeline even after the cap, retaining separate real-link receipts.
    scope()
    path = Path(sys.argv[2]) # The exact owned path also makes a stranded capture visible to cleanup census.
    require(path in {REPORTS / 'neutral.log', REPORTS / 'darwin.log'}, 'Unknown Gradle log')
    name = path.stem
    observed = 0
    with path.open('xb') as log:
        for block in iter(lambda: sys.stdin.buffer.read(65536), b''):
            room = max(0, GRADLE_LOG_LIMIT - observed)
            log.write(block[:room])
            if observed <= GRADLE_LOG_LIMIT < observed + len(block):
                limit_receipt(name + '.log', GRADLE_LOG_LIMIT, observed + len(block))
            observed += len(block)
    truncated = observed > GRADLE_LOG_LIMIT
    save(REPORTS / (name + '-capture.json'), {'complete': True, 'truncated': truncated,
         'observedBytes': observed, 'retainedBytes': min(observed, GRADLE_LOG_LIMIT)})
    require(not truncated, 'Gradle log cap exceeded: ' + name)

def command(argv, seconds=20, role='app', log='tools-and-simulator.log', log_output=True):
    process = subprocess.Popen(argv, env=dict(os.environ, DEVELOPER_DIR=XCODE[role],
                               GRADLE_USER_HOME=str(RUN / 'gradle-home')),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    data, observed = bytearray(), 0
    record = {'argv': argv, 'developerDir': XCODE[role], 'timeoutSeconds': seconds}
    deadline = time.monotonic() + seconds
    try:
        while True:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([process.stdout], [], [], left)[0]:
                raise subprocess.TimeoutExpired(argv, seconds)
            block = os.read(process.stdout.fileno(), 65536)
            if not block: break
            data.extend(block[:max(0, TOOL_CAPTURE_LIMIT - len(data))])
            if observed <= TOOL_CAPTURE_LIMIT < observed + len(block):
                limit_receipt(log, TOOL_CAPTURE_LIMIT, observed + len(block))
            observed += len(block)
        process.wait(timeout=max(0, deadline - time.monotonic()))
    except Exception as failure:
        record['error'] = str(failure)[:1000]
        raise
    finally:
        if process.poll() is None:
            attempt = {'pid': process.pid, 'signal': 'SIGKILL', 'outcome': 'attempting'}
            TOOL_SIGNALS.append(attempt)
            signal_path = REPORTS / (sys.argv[1] + '-command-signals.json')
            save(signal_path, TOOL_SIGNALS) # Persist intent before every explicit timeout signal.
            try:
                process.kill()
                attempt['outcome'] = 'sent'
                process.wait(timeout=2)
            except Exception as failure: attempt['outcome'] = str(failure)[:1000]
            finally: save(signal_path, TOOL_SIGNALS)
        process.stdout.close()
        record.update(exit=process.returncode, observedBytes=observed, truncated=observed > TOOL_CAPTURE_LIMIT)
        append_log(log, (json.dumps(record) + '\n').encode() + (bytes(data) if log_output else b'[output not logged]') + b'\n',
                   TOOL_CAPTURE_LIMIT if log == 'gradle-stop.log' else TOOL_LOG_LIMIT)
    require(observed <= TOOL_CAPTURE_LIMIT, 'Command output cap exceeded; refuse partial output')
    if process.returncode: raise subprocess.CalledProcessError(process.returncode, argv)
    return data.decode('utf-8', errors='replace')

def scope():
    require(RUN.is_absolute() and RUN.parent.resolve() == Path(os.environ['RUNNER_TEMP']).resolve()
            and RUN.name == 'engine5-darwin-' + OWNER and not RUN.is_symlink(), 'Unsafe run root')
    require((RUN / 'owner').read_text() == OWNER, 'Missing run ownership marker')
    require(REPORTS.is_dir() and not REPORTS.is_symlink(), 'Unsafe report directory')

def prepare():
    require(RUN.is_absolute() and RUN.parent.resolve() == Path(os.environ['RUNNER_TEMP']).resolve()
            and RUN.name == 'engine5-darwin-' + OWNER, 'Unsafe new run root')
    RUN.mkdir(mode=0o700, exist_ok=False)
    REPORTS.mkdir(mode=0o700)
    (RUN / 'owner').write_text(OWNER)
    scope()
    free = shutil.disk_usage(RUN).free
    save(REPORTS / 'disk.json', {'freeBytes': free, 'minimumFreeBytes': DISK_FLOOR,
                               'sufficient': free >= DISK_FLOOR, 'notACompilationFitGuarantee': True})
    require(free >= DISK_FLOOR, 'Less than 8 GiB free; refuse cold native preparation')
    request_path = CONTROL / 'ci/engine5-darwin.request.json'
    request = json.loads(request_path.read_text())
    require(request['schemaVersion'] == 1 and request['lane'] == 'engine5-darwin-one-test', 'Wrong request')
    require(request.get('validationHost') == 'engine5DarwinBoundary-v1', 'Expected explicit targeted native host request')
    binding = {'carrierSha': os.environ['GITHUB_SHA'], 'requestSha256': digest(request_path),
               'candidate': VERSION, 'sources': request, 'controlSha256': {
                   name: digest(CONTROL / name) for name in (
                       '.github/workflows/engine5-darwin.yml', 'ci/engine5-darwin.py', 'ci/engine5-darwin.init.gradle', NATIVE_HOST_BUILD)}}
    save(REPORTS / 'bindings.json', binding)
    before = {}
    for role, (base, patch, manifest_sha, count) in PINS.items():
        target = request[role]
        patch_key = 'baselinePatchSha256' if role == 'app' else 'patchSha256'
        require((target['baseSha'], target[patch_key], target['manifestSha256'], target['files'])
                == (base, patch, manifest_sha, count), 'Reviewed source identity drift: ' + role)
        if role == 'app':
            require(target['baselineManifestSha256'] == APP_BASELINE_MANIFEST and target['writerCorrection'] == APP_WRITER,
                    'Unbound/different reviewed App writer correction')
        archive = INPUTS / (role + '.tar.gz')
        expected = target['archiveSha256']
        require(re.fullmatch('[0-9a-f]{64}', expected) and expected != '0' * 64
                and digest(archive) == expected, 'Unbound/different private archive: ' + role)
        manifest_path = INPUTS / (role + '.after.json')
        require(digest(manifest_path) == manifest_sha, 'Wrong reviewed/derived manifest: ' + role)
        manifest = json.loads(manifest_path.read_text())
        entries = manifest['changed_files'] if role == 'neutral' else manifest
        destination = RUN / role
        destination.mkdir(mode=0o700)
        with tarfile.open(archive, 'r:gz') as bundle:
            members = bundle.getmembers()
            require(len(members) == count and sum(m.size for m in members) < 64 * 1024 * 1024,
                    'Wrong/oversized source archive inventory: ' + role)
            seen = set()
            for member in members:
                path = PurePosixPath(member.name)
                require(member.isfile() and not path.is_absolute() and '..' not in path.parts
                        and '\\' not in member.name and str(path) == member.name and member.name not in seen
                        and '.git' not in path.parts and 0 <= member.size < 32 * 1024 * 1024,
                        'Unsafe/duplicate source member: ' + member.name)
                require(path.name not in {'local.properties', 'google-services.json', 'GoogleService-Info.plist'}
                        and not (path.name.startswith('.env') and not path.name.endswith('.example'))
                        and not any(part in {'.gradle', '.kotlin', 'build'} for part in path.parts),
                        'Local secret/cache/output in source archive: ' + member.name)
                seen.add(member.name)
                data = bundle.extractfile(member).read()
                require(len(data) == member.size, 'Truncated source member')
                output = destination / member.name
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)
                output.chmod(0o700 if member.mode & 0o111 else 0o600)
                before[role + '/' + member.name] = hashlib.sha256(data).hexdigest()
        for item in entries:
            require(before.get(role + '/' + item['path']) == item['after_sha256'], 'Reviewed file mismatch: ' + item['path'])
    # Add only reviewed validation configuration. All five Kotlin sources stay at their original archive paths.
    host_control = CONTROL / NATIVE_HOST_BUILD
    require(host_control.is_file() and not host_control.is_symlink() and host_control.stat().st_size <= 64 * 1024,
            'Invalid/oversized native host build control')
    host_build = RUN / 'app/engine5DarwinBoundary/build.gradle.kts'
    host_build.parent.mkdir(mode=0o700, exist_ok=False) # Never reuse a project supplied by an archive.
    host_build.write_bytes(host_control.read_bytes())
    host_build.chmod(0o600)
    host_sha = binding['controlSha256'][NATIVE_HOST_BUILD]
    require(digest(host_build) == host_sha, 'Native host control changed while preparing')
    before['app/engine5DarwinBoundary/build.gradle.kts'] = host_sha
    binding['nativeHost'] = {'project': NATIVE_HOST_PROJECT, 'buildFile': str(host_build.resolve()), 'buildSha256': host_sha,
                            'sourceSets': {source_set: {name: before['app/' + name] for name in names}
                                           for source_set, names in NATIVE_HOST_SOURCE_SETS.items()}}
    save(RUN / 'before.json', before)
    webp = RUN / 'app/platform/libs/libwebp/ios-arm64-simulator/libwebp.a'
    require(webp.read_bytes().startswith(b'!<arch>\n'), 'libwebp is missing or an LFS pointer')
    binding['libwebpSimulatorSha256'] = digest(webp)
    save(REPORTS / 'bindings.json', binding)
    for name in ('gradle-home', 'konan', 'repository', 'home', 'tmp'): (RUN / name).mkdir(mode=0o700)
    (RUN / 'test-Info.plist').write_bytes(plistlib.dumps({'NSAppTransportSecurity': {
        'NSExceptionDomains': {'127.0.0.1': {'NSExceptionAllowsInsecureHTTPLoads': True}}}}))
    require(sys.platform == 'darwin' and platform.machine() == 'arm64', 'Standard ARM macOS runner required')
    tools = {'machine': platform.machine(), 'macOS': platform.mac_ver()[0], 'logicalCPUs': os.cpu_count(),
             'python': {'executable': sys.executable, 'version': sys.version},
             'memoryBytes': command(['sysctl', '-n', 'hw.memsize']).strip(), 'diskFreeBytes': shutil.disk_usage(RUN).free,
             'ImageOS': os.environ.get('ImageOS'), 'ImageVersion': os.environ.get('ImageVersion'),
             'java': command([os.environ['JAVA_HOME'] + '/bin/java', '-version']), 'xcode': {}}
    for role, baseline in [('neutral', '26.0'), ('app', '26.4')]:
        require(Path(XCODE[role]).is_dir(), 'Required Xcode absent: ' + role)
        version = command(['xcodebuild', '-version'], role=role)
        sdk = command(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], role=role).strip()
        require(version.splitlines()[0] == 'Xcode ' + baseline + '.1' and sdk == baseline,
                'Different selected Xcode/SDK: ' + role)
        tools['xcode'][role] = {'developerDir': XCODE[role], 'version': version, 'simulatorSDK': sdk}
    save(REPORTS / 'tools.json', tools)
    require(not list(REPORTS.glob('*.limit.json')), 'Preparation output was truncated')

def published():
    scope()
    receipts = {}
    for base in ('source-contract', 'source-engine'):
        for module in (base, base + '-iossimulatorarm64'):
            root = RUN / 'repository/me/manga/kira/source' / module / VERSION
            suffix = '.jar' if module == base else '.klib'
            files = [root / (module + '-' + VERSION + ext) for ext in ('.pom', '.module', suffix)]
            require(all(p.is_file() for p in files), 'Missing required publication: ' + module)
            metadata = json.loads(files[1].read_text())
            require(metadata['component']['version'] == VERSION, 'Wrong publication version')
            receipts[module] = {'sha256': {p.name: digest(p) for p in files}, 'variants': metadata['variants']}
    save(REPORTS / 'published.json', receipts)

def devices(seconds=20):
    return [d for values in json.loads(command(['xcrun', 'simctl', 'list', 'devices', '--json'], seconds=seconds))['devices'].values() for d in values]

def simulator():
    scope()
    started = time.monotonic()
    timing = {'clock': 'monotonic', 'startSeconds': started, 'elapsedSeconds': None,
              'finalPhase': 'inventory', 'outcome': 'FAIL',
              'bootStartSeconds': None, 'bootElapsedSeconds': None,
              'bootstatusStartSeconds': None, 'bootstatusElapsedSeconds': None,
              'bootstatusTimeoutSeconds': 180}
    try:
        runtimes = json.loads(command(['xcrun', 'simctl', 'list', 'runtimes', '--json']))['runtimes']
        types = json.loads(command(['xcrun', 'simctl', 'list', 'devicetypes', '--json']))['devicetypes']
        matches = [r for r in runtimes if r.get('isAvailable') and r['identifier'].startswith('com.apple.CoreSimulator.SimRuntime.iOS-')
                   and re.fullmatch(r'26\.4(?:\.\d+)?', r['version'])]
        require(len(matches) == 1, 'Expected one available iOS 26.4.x runtime; do not guess or install')
        phone = [d for d in types if d['identifier'] == 'com.apple.CoreSimulator.SimDeviceType.iPhone-17']
        require(len(phone) == 1, 'Expected iPhone 17 device type')
        name = 'Engine5-' + OWNER
        require(not any(d['name'] == name for d in devices()), 'Owned simulator name already exists')
        timing['finalPhase'] = 'create'
        state = {'name': name, 'runtime': matches[0], 'deviceType': phone[0], 'creating': True}
        save(RUN / 'simulator.json', state) # Records ownership before creation, including cancellation window.
        state['udid'] = command(['xcrun', 'simctl', 'create', name, phone[0]['identifier'], matches[0]['identifier']]).strip()
        require(re.fullmatch('[0-9A-Fa-f-]{36}', state['udid']), 'Invalid created simulator UUID')
        state['creating'] = False
        save(RUN / 'simulator.json', state)
        timing['finalPhase'] = 'boot'
        timing['bootStartSeconds'] = time.monotonic()
        command(['xcrun', 'simctl', 'boot', state['udid']])
        timing['bootElapsedSeconds'] = time.monotonic() - timing['bootStartSeconds']
        timing['finalPhase'] = 'bootstatus'
        timing['bootstatusStartSeconds'] = time.monotonic()
        state['bootstatus'] = command(['xcrun', 'simctl', 'bootstatus', state['udid'], '-b'], seconds=180)
        timing['bootstatusElapsedSeconds'] = time.monotonic() - timing['bootstatusStartSeconds']
        timing['finalPhase'] = 'receipt'
        save(REPORTS / 'simulator.json', state)
        timing.update(finalPhase='complete', outcome='PASS')
    finally:
        # Fixed-size timing only; elapsed command time includes its existing bounded failure cleanup.
        ended = time.monotonic()
        timing['elapsedSeconds'] = ended - started
        for step in ('boot', 'bootstatus'):
            if timing[step + 'StartSeconds'] is not None and timing[step + 'ElapsedSeconds'] is None:
                timing[step + 'ElapsedSeconds'] = ended - timing[step + 'StartSeconds']
        failing = sys.exc_info()[0] is not None
        try: save(REPORTS / 'simulator-timing.json', timing)
        except Exception:
            if not failing: raise # Preserve the original failure if diagnostic persistence also fails.

def collect():
    scope()
    require(all(p.stat().st_size <= JSON_LIMIT for p in REPORTS.glob('*.json')), 'Oversized JSON receipt')
    prior_outcome = os.environ.get('ENGINE5_VALIDATION_OUTCOME')
    if prior_outcome != 'success':
        # Separate detail survives the unchanged main failure handler's result.json overwrite.
        save(REPORTS / 'failed-collection.json',
             {'validation': 'FAIL', 'priorValidationOutcome': prior_outcome[:64] if prior_outcome is not None else None,
              'checks': {'sourceRecheck': 'NOT_RUN', 'linkInspection': 'NOT_RUN', 'xmlVerification': 'NOT_RUN'}})
        require(False, 'Publication/compile/link/test stage did not succeed')
    binary_receipt = REPORTS / 'linked-binary.json'
    if binary_receipt.is_file():
        linked = json.loads(binary_receipt.read_text())
        binary = Path(linked['file'])
        require(binary.resolve().is_relative_to((RUN / 'app/engine5DarwinBoundary/build').resolve()) and binary.is_file()
                and digest(binary) == linked['sha256'], 'Changed/missing test executable')
        load_commands = command(['xcrun', 'vtool', '-show-build', str(binary)])
        plist_section = command(['xcrun', 'otool', '-s', '__TEXT', '__info_plist', str(binary)])
        append_log('binary-inspection.log', (load_commands + '\n' + plist_section).encode(), TOOL_CAPTURE_LIMIT)
        require('IOSSIMULATOR' in load_commands and '(__TEXT,__info_plist)' in plist_section, 'Wrong Mach-O platform/missing embedded test plist')
    before = json.loads((RUN / 'before.json').read_text())
    require(all((RUN / name).is_file() and digest(RUN / name) == expected for name, expected in before.items()), 'Source bytes changed during validation')
    require(os.environ.get('ENGINE5_VALIDATION_OUTCOME') == 'success', 'Publication/compile/link/test stage did not succeed')
    for name in ('published.json', 'native-closure.json', 'link-inputs.json', 'linked-binary.json', 'test-invocation.json', 'simulator.json'):
        require((REPORTS / name).is_file(), 'Missing actual runtime receipt: ' + name)
    for name, task in [('native-closure.json', 'linkDebugTestIosSimulatorArm64'), ('link-inputs.json', 'linkDebugTestIosSimulatorArm64'),
                       ('linked-binary.json', 'linkDebugTestIosSimulatorArm64'), ('test-invocation.json', 'iosSimulatorArm64Test')]:
        require(json.loads((REPORTS / name).read_text())['task'] == NATIVE_HOST_PROJECT + ':' + task, 'Wrong native host task: ' + name)
    closure = json.loads((REPORTS / 'native-closure.json').read_text())
    require(closure['validation'] == 'PASS' and closure['project'] == NATIVE_HOST_PROJECT and closure['candidate'] == VERSION,
            'Targeted native dependency/source closure was not accepted')
    for name in ('neutral', 'darwin'):
        captured = json.loads((REPORTS / (name + '-capture.json')).read_text())
        require(captured['complete'] and not captured['truncated'], 'Incomplete Gradle diagnostic capture: ' + name)
    xmls = list((REPORTS / 'xml').glob('*.xml'))
    require(len(xmls) == 1 and xmls[0].stat().st_size <= XML_LIMIT, 'Expected exactly one focused XML suite within 4 MiB')
    suite = ET.parse(xmls[0]).getroot()
    cases = suite.findall('testcase')
    cls = 'me.manga.kira.sources.runtime.KtorSourceDarwinBoundaryTest'
    method = 'darwin_single_hop_bridge_cancellation_and_managed_closure'
    require(suite.tag == 'testsuite' and int(suite.get('tests', '-1')) == len(cases) == 1
            and all(int(suite.get(k, '-1')) == 0 for k in ('failures', 'errors', 'skipped'))
            and cases[0].get('classname') == cls and cases[0].get('name') in {method, method + '[iosSimulatorArm64]'}
            and not any(n.tag in ('failure', 'error', 'skipped') for n in suite.iter()), 'Focused native XML did not prove one passing selected case')
    require(not list(REPORTS.glob('*.limit.json')), 'Truncated diagnostic evidence is not a PASS')
    save(REPORTS / 'result.json', {'validation': 'PASS', 'candidate': VERSION,
                                  'testcase': cases[0].attrib, 'sourceBytesUnchanged': True,
                                  'validationScope': 'targeted-native-boundary', 'fullAppNativeCompilation': 'SEPARATE_OBLIGATION',
                                  'requiresSeparateCleanupPass': True, 'requiresSeparateEvidencePass': True})

def owned_pids():
    marker = '-Dengine5.darwin.owner=' + OWNER
    rows = command(['ps', '-axww', '-o', 'pid=,command='], seconds=5, log_output=False).splitlines()
    owned = {}
    for row in rows:
        if row.strip() and (marker in row.split() or str(RUN) + '/' in row):
            pid = int(row.split(None, 1)[0])
            if pid != os.getpid():
                owned[pid] = [basis for basis, matched in (
                    ('exact-owner-argument', marker in row.split()), ('owned-run-path', str(RUN) + '/' in row)) if matched]
    return owned # Same PID selection; values record the existing match basis, never full command text.

def worker_identity(owned):
    # Only the first 32 already-owned PIDs, one bounded query at an existing census/signal boundary, no sampler.
    selected = sorted(owned)[:PROCESS_IDENTITY_LIMIT]
    snapshot = {'ownedCount': len(owned), 'omittedOwnedCount': max(0, len(owned) - PROCESS_IDENTITY_LIMIT),
                'processes': [], 'unobservedPids': selected}
    try:
        if selected:
            raw = command(['ps', '-ww', '-p', ','.join(map(str, selected)), '-o', 'pid=,uid=,ppid=,pgid=,stat=,comm='],
                          seconds=1, log_output=False)
            found = {}
            for row in identity_rows(raw):
                pid = row['pid']
                require(pid in selected and pid not in found, 'Unexpected/duplicate targeted identity row')
                row['basis'] = owned[pid]
                found[pid] = row
            snapshot['processes'] = [found[pid] for pid in sorted(found)]
            snapshot['unobservedPids'] = sorted(set(selected) - found.keys())
    except Exception as failure:
        snapshot['error'] = str(failure)[:1000] # Observation only; does not authorize or suppress any worker signal.
    snapshot['observedMonotonicSeconds'] = time.monotonic()
    return snapshot

def stage_evidence():
    # Called only after cleanup validated ownership. Upload only this byte-bounded snapshot.
    target = REPORTS / 'upload'
    target.mkdir(mode=0o700, exist_ok=False)
    reserve = 64 * 1024
    receipt = {'budget': 'FAIL', 'complete': False, 'limitBytes': EVIDENCE_LIMIT, 'files': [], 'omitted': []}
    save(target / 'evidence-budget.json', receipt)
    core = {'bindings.json', 'tools.json', 'published.json', 'native-closure.json', 'link-inputs.json', 'linked-binary.json',
            'test-invocation.json', 'simulator.json', 'result.json', 'cleanup.json', 'binary-inspection.log'}
    files = sorted([*REPORTS.glob('*.json'), *(REPORTS / 'xml').glob('*.xml'), *REPORTS.glob('*.log')],
                   key=lambda p: (p.name not in core and p.suffix != '.xml', p.suffix == '.log', str(p)))
    receipt['discoveredFiles'] = len(files)
    receipt['omittedByFileCountCap'] = max(0, len(files) - 64)
    used = 0
    for path in files[:64]:
        name = str(path.relative_to(REPORTS))
        cap = JSON_LIMIT if path.suffix == '.json' else XML_LIMIT if path.suffix == '.xml' else GRADLE_LOG_LIMIT
        reason = None
        if path.is_symlink() or not path.is_file() or (REPORTS / 'xml').is_symlink() or not path.resolve().is_relative_to(REPORTS.resolve()):
            reason = 'not an owned regular receipt'
        elif path.stat().st_size > min(cap, EVIDENCE_LIMIT - reserve - used):
            reason = 'file/aggregate byte cap'
        else:
            with path.open('rb') as source: data = source.read(min(cap, EVIDENCE_LIMIT - reserve - used) + 1)
            if len(data) > min(cap, EVIDENCE_LIMIT - reserve - used): reason = 'grew beyond byte cap'
        if reason:
            receipt['omitted'].append({'file': name[:256], 'reason': reason})
            continue
        output = target / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data) # Never truncate a required JSON/XML receipt to manufacture a PASS.
        used += len(data)
        receipt['files'].append({'file': name[:256], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    receipt.update(complete=True, copiedBytes=used, truncatedInputs=bool(list(REPORTS.glob('*.limit.json'))))
    receipt['budget'] = 'PASS' if len(files) <= 64 and not receipt['omitted'] and not receipt['truncatedInputs'] else 'FAIL'
    encoded = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode()
    require(len(encoded) <= reserve, 'Evidence inventory exceeded its reserved bound')
    (target / 'evidence-budget.json').write_bytes(encoded)
    return receipt['budget'] == 'PASS'

def cleanup():
    scope()
    receipt = {'cleanup': 'INCOMPLETE', 'errors': {}, 'signalAttempts': [], 'commandSignalAttempts': TOOL_SIGNALS,
               'workersAbsent': False, 'simulatorRemoved': False, 'scratchRemoved': False, 'workerIdentity': {}}
    def error(phase, failure): receipt['errors'][phase] = str(failure)[:1000]
    def checkpoint():
        try: save(REPORTS / 'cleanup.json', receipt)
        except Exception as failure:
            error('receipt', failure)
            return False
        return True
    checkpoint()
    try:
        distributions = list((RUN / 'gradle-home/wrapper/dists').glob('gradle-9.6.1-bin/*/gradle-9.6.1/bin/gradle'))
        require(len(distributions) <= 1, 'Unexpected Gradle distribution inventory')
        if distributions:
            # Never invoke a missing wrapper or address a shared Gradle home.
            command([str(distributions[0]), '--stop', '--gradle-user-home', str(RUN / 'gradle-home')],
                    seconds=20, log='gradle-stop.log')
        receipt['gradleStop'] = 'PASS' if distributions else 'NOT_INSTALLED'
    except Exception as failure: error('gradleStop', failure)
    checkpoint()
    try:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            candidates = owned_pids()
            identity = worker_identity(candidates)
            confirmed = owned_pids() # Fresh confirmation stays AFTER diagnostics; a failed census never authorizes a signal.
            targets = candidates.keys() & confirmed.keys()
            for row in identity['processes']: row['confirmedForSignal'] = row['pid'] in targets
            receipt['workerIdentity'][sig.name] = identity # Earlier observation, not identity at the signal instant.
            for pid in sorted(targets):
                attempt = {'pid': pid, 'signal': sig.name, 'outcome': 'attempting', 'basis': confirmed[pid]}
                receipt['signalAttempts'].append(attempt)
                require(checkpoint(), 'Cannot record signal intent; refuse unrecorded signal')
                try:
                    os.kill(pid, sig)
                    attempt['outcome'] = 'sent'
                except ProcessLookupError: attempt['outcome'] = 'alreadyGone'
                except Exception as failure:
                    attempt['outcome'] = str(failure)[:1000]
                    error('signal-' + str(pid), failure)
                checkpoint()
            time.sleep(3) # Also re-census initially empty sets; late KILL targets are recorded above.
        remaining = owned_pids()
        receipt['remainingPids'] = sorted(remaining)
        receipt['workerIdentity']['remaining'] = worker_identity(remaining)
        receipt['workersAbsent'] = not receipt['remainingPids']
        require(receipt['workersAbsent'], 'Owned workers remain; retain scratch')
    except Exception as failure: error('workers', failure)
    checkpoint()
    # Device disposal is independent of Gradle-stop/census/worker failures, but never guesses ownership.
    try:
        name, udid = 'Engine5-' + OWNER, None
        state_path = RUN / 'simulator.json'
        inventory = devices(seconds=10)
        if state_path.is_file():
            require(not state_path.is_symlink(), 'Unsafe simulator ownership record')
            state = json.loads(state_path.read_text())
            udid = state.get('udid')
            require(state['name'] == name and (re.fullmatch('[0-9A-Fa-f-]{36}', udid) if udid else state.get('creating') is True),
                    'Invalid owned simulator record')
            matches = [d for d in inventory if d['name'] == name or d['udid'] == udid]
            require(len(matches) <= 1 and all(d['name'] == name and (not udid or d['udid'] == udid) for d in matches),
                    'Ambiguous owned simulator; refuse disposal')
            for device in matches:
                if device['state'] != 'Shutdown':
                    try: command(['xcrun', 'simctl', 'shutdown', device['udid']], seconds=15)
                    except Exception as failure: error('simulatorShutdown', failure)
                try: command(['xcrun', 'simctl', 'delete', device['udid']], seconds=15)
                except Exception as failure: error('simulatorDelete', failure)
            inventory = devices(seconds=10)
        require(not any(d['name'] == name or d['udid'] == udid for d in inventory),
                'Simulator present without proven disposal; retain scratch')
        receipt['simulatorRemoved'] = True
    except Exception as failure: error('simulator', failure)
    checkpoint()
    try:
        require(receipt['workersAbsent'] and receipt['simulatorRemoved'], 'Worker/device absence not proven; retain scratch')
        receipt['workersAbsent'] = False
        before_remove = owned_pids()
        receipt['workersAbsent'] = not before_remove
        receipt['workerIdentity']['beforeScratchRemoval'] = worker_identity(before_remove)
        require(receipt['workersAbsent'], 'Owned workers appeared during cleanup; retain scratch')
        for path in RUN.iterdir():
            if path == REPORTS: continue
            if path.is_dir() and not path.is_symlink(): shutil.rmtree(path)
            else: path.unlink()
        receipt['scratchRemoved'] = set(RUN.iterdir()) == {REPORTS}
    except Exception as failure: error('scratch', failure)
    receipt['cleanup'] = 'PASS' if (receipt['scratchRemoved'] and not receipt['errors']
        and not receipt['signalAttempts'] and not TOOL_SIGNALS and not list(REPORTS.glob('*.limit.json'))) else 'FAIL'
    receipt_ok = checkpoint()
    evidence_ok = stage_evidence()
    require(receipt_ok and receipt['cleanup'] == 'PASS' and evidence_ok,
            'Forced/failed cleanup or incomplete/bounded-out evidence is not a PASS')

if __name__ == '__main__':
    phase = sys.argv[1]
    require(phase in {'prepare', 'published', 'simulator', 'collect', 'cleanup', 'capture', 'deadline'}, 'Unknown closed lane phase')
    try:
        globals()[phase]()
    except Exception as failure:
        if REPORTS.is_dir():
            save(REPORTS / (phase + '-failure.json'), {'phase': phase, 'error': str(failure)[:1000]})
            if phase == 'collect': save(REPORTS / 'result.json', {'validation': 'FAIL', 'error': str(failure)[:1000]})
        raise
