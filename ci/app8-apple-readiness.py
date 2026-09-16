"""One public-metadata runtime observation, never native/PF acceptance or setup.

Reuse only the frozen App8 command owner and absence barrier. No helper main,
compiler, device inventory/creation/boot, PF operation, download or global reset.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import sys
import time

REPOSITORY = 'kira-manga/kira-admin'
REF = 'refs/heads/validation/app8-readiness-20260916-01'
WORKFLOW = '.github/workflows/app8-apple-readiness.yml'
HELPER_SHA256 = '9f69c87182eba29030fcd65c49b4e8459a41749440dab9767f3fbfe0c02db6cf'
XCODE = '/Applications/Xcode_26.4.1.app/Contents/Developer'
SDK = XCODE + '/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator26.4.sdk'
PROFILE = {'developerDir': XCODE, 'xcodeVersion': '26.4.1', 'xcodeBuild': '17E202',
           'sdkPath': SDK, 'sdkVersion': '26.4', 'sdkBuild': '23E252',
           'runtimeIdentifier': 'com.apple.CoreSimulator.SimRuntime.iOS-26-4',
           'runtimeVersion': '26.4.1', 'runtimeBuild': '23E254a', 'architecture': 'arm64'}
BUDGET = {'overall': 150, 'work': 105, 'cleanup': 40, 'receipts': 5,
          'identity': 10, 'runtime': 30, 'runtimeReserve': 31}


def main():
    started = time.monotonic()
    os.umask(0o077)
    source = Path(__file__).resolve()
    helper = source.with_name('app8-apple.py')
    if not helper.is_file() or helper.is_symlink() or helper.stat().st_size > 131072:
        raise RuntimeError('Missing/nonregular frozen command owner')
    helper_bytes = helper.read_bytes()
    if hashlib.sha256(helper_bytes).hexdigest() != HELPER_SHA256:
        raise RuntimeError('Command owner differs from reviewed bytes')
    spec = importlib.util.spec_from_file_location('app8_readiness_owner', helper)
    h = importlib.util.module_from_spec(spec)
    # Execute the exact hashed bytes as an imported module, never as __main__.
    exec(compile(helper_bytes, str(helper), 'exec'), h.__dict__)
    for number in (signal.SIGTERM, signal.SIGINT):
        signal.signal(number, h.interrupted)
    request_path = source.with_name('app8-apple-readiness.request.json')
    request_sha = h.digest(request_path)
    bindings = {'wrapperSha256': h.digest(source), 'workflowSha256': h.digest(source.parents[1] / WORKFLOW),
                'controllerSha256': HELPER_SHA256}
    h.require(not sys.argv[1:] and h.read_json(request_path) == {
        'schema': 'app8-apple-readiness-v1', 'authorization': 'APP8_APPLE_READINESS_SINGLE_RUN_AUTHORIZED',
        'repository': REPOSITORY, 'repositoryPrivate': False, 'ref': REF, 'exclusiveDisposableJobVm': True,
        'toolchain': PROFILE, 'budgetSeconds': BUDGET, **bindings}, 'Inactive or unbound readiness request')
    sha, run_id = os.environ.get('GITHUB_SHA', ''), os.environ.get('GITHUB_RUN_ID', '')
    h.require(re.fullmatch(r'[0-9a-f]{40}', sha) and re.fullmatch(r'[1-9][0-9]{0,19}', run_id)
              and os.environ.get('GITHUB_WORKFLOW_SHA') == sha
              and os.environ.get('GITHUB_WORKFLOW_REF') == REPOSITORY + '/' + WORKFLOW + '@' + REF
              and os.environ.get('GITHUB_REPOSITORY') == REPOSITORY and os.environ.get('GITHUB_REF') == REF
              and os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
              and os.environ.get('APP8_REPOSITORY_PRIVATE') == 'false'
              and source.parents[1] == Path(os.environ['GITHUB_WORKSPACE']).resolve(), 'Wrong exact source/request invocation')
    h.require(os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted' and os.environ.get('ImageOS') == 'macos26'
              and platform.system() == 'Darwin' and platform.machine() == 'arm64' and os.getuid() > 0,
              'Only the standard disposable hosted Darwin/arm64 image is admitted')
    run = Path(os.environ['APP8_READINESS_RUN'])
    h.require(run.is_absolute() and run == Path(os.environ['RUNNER_TEMP']).resolve() / ('app8-apple-readiness-' + run_id + '-1')
              and not run.exists() and not run.is_symlink(), 'Not a fresh owned readiness path')
    run.mkdir(mode=0o700)
    for name in ('reports', 'work'):
        (run / name).mkdir(mode=0o700)
    owned_identity = (run.stat().st_dev, run.stat().st_ino)
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(Path.home().resolve()),
           'LANG': 'C', 'LC_ALL': 'C', 'DEVELOPER_DIR': XCODE}
    commands = h.Commands(run, env, started + BUDGET['work'])
    cleanup = {'errors': [], 'ownedScratchRemoved': False}
    tools = {'developerDir': XCODE, 'macOS': platform.mac_ver()[0], 'kernel': platform.release(),
             'imageOS': os.environ.get('ImageOS'), 'imageVersion': os.environ.get('ImageVersion'),
             'architecture': platform.machine(), 'python': sys.version,
             'pythonExecutable': str(Path(sys.executable).resolve())}
    observed, matched, failure = None, False, None
    try:
        h.save(commands.reports / 'tool-identities.json', tools)
        h.deadline_capabilities()
        h.require(Path(XCODE).is_dir() and tools['imageVersion'], 'Missing fixed Xcode/image identity; no installation')
        identities = ((['xcodebuild', '-version'], 'xcode-version', 'xcode', 'Xcode 26.4.1\nBuild version 17E202'),
                      (['--sdk', 'iphonesimulator', '--show-sdk-version'], 'sdk-version', 'sdkVersion', '26.4'),
                      (['--sdk', 'iphonesimulator', '--show-sdk-path'], 'sdk-path', 'sdkPath', SDK),
                      (['--sdk', 'iphonesimulator', '--show-sdk-build-version'], 'sdk-build', 'sdkBuild', '23E252'))
        for args, label, key, expected in identities:
            tools[key] = commands.call(['/usr/bin/xcrun', *args], label, seconds=BUDGET['identity']).strip()
            h.save(commands.reports / 'tool-identities.json', tools)
            h.require(tools[key] == expected, 'Different installed identity: ' + key)
        h.require(Path(SDK).is_dir() and Path(SDK).resolve().is_relative_to(Path(XCODE).resolve()),
                  'SDK escapes the fixed installed Xcode')
        tools['sdkSettingsSha256'] = h.digest(Path(SDK) / 'SDKSettings.plist')
        tools['toolSha256'] = {str(path): h.digest(path) for path in
                              (Path('/usr/bin/xcrun'), Path(XCODE) / 'usr/bin/simctl', Path(sys.executable).resolve())}
        h.save(commands.reports / 'tool-identities.json', tools)
        h.require(not h.CANCELLED and time.monotonic() + BUDGET['runtimeReserve'] <= commands.end,
                  'Insufficient original runtime-query window; no launch')
        runtimes = h.parse_json(commands.call(['/usr/bin/xcrun', 'simctl', 'list', 'runtimes', '--json'],
                                             'runtimes', seconds=BUDGET['runtime']))['runtimes']
        matches = [row for row in runtimes if row['identifier'] == PROFILE['runtimeIdentifier'] and row.get('isAvailable') is True]
        h.require(len(matches) == 1 and matches[0]['version'] == PROFILE['runtimeVersion']
                  and matches[0]['buildversion'] == PROFILE['runtimeBuild']
                  and isinstance(matches[0]['supportedArchitectures'], list)
                  and 'arm64' in matches[0]['supportedArchitectures'], 'Missing exact available runtime; no download/fallback')
        observed = {key: matches[0][key] for key in ('identifier', 'version', 'buildversion', 'isAvailable', 'supportedArchitectures')}
        h.require(h.digest(request_path) == request_sha and not h.CANCELLED and time.monotonic() < commands.end,
                  'Readiness request changed or work cancelled/expired')
        matched = True
    except Exception as error:
        failure = str(error)[:500]
    finally:
        commands.end = min(time.monotonic() + BUDGET['cleanup'], started + BUDGET['overall'] - BUDGET['receipts'])
        try:
            h.absence_barrier(commands, {'udid': None, 'creating': False}, cleanup, [])
            h.require(all(cleanup[key] for key in ('nativeAbsent', 'fixturesAbsent', 'commandsAbsent', 'workersAbsent', 'receiptSaved'))
                      and time.monotonic() < commands.end, 'Incomplete owned absence; retain scratch')
            h.require(not run.is_symlink() and owned_identity == (run.stat().st_dev, run.stat().st_ino)
                      and (run / 'work').is_dir() and not (run / 'work').is_symlink(), 'Owned scratch identity changed')
            shutil.rmtree(run / 'work')
            cleanup['ownedScratchRemoved'] = True
            h.require(time.monotonic() < commands.end, 'Owned scratch cleanup exceeded its deadline')
        except Exception as error:
            cleanup['errors'].append(str(error)[:500])
        normal = commands.normal() and not cleanup['errors'] and not h.CANCELLED
        output_ok = commands.within_cap()
        # Lifetime absence/deletion cannot erase any timeout, force or failed normal join.
        passed = matched and normal and output_ok and cleanup['ownedScratchRemoved']
        receipt_end = min(time.monotonic() + BUDGET['receipts'], started + BUDGET['overall'])
        h.require(time.monotonic() < receipt_end, 'No final receipt budget remains')
        h.save(commands.reports / 'cleanup.json', cleanup)
        h.save(commands.reports / 'readiness.json', {
            'passed': passed, 'failure': failure, 'runtimeMatched': matched, 'runtime': observed,
            'normalOwnedCleanup': normal, 'logsWithinCap': output_ok, 'ownedScratchRemoved': cleanup['ownedScratchRemoved'],
            'carrierSha': sha, 'run': run.name, 'requestSha256': request_sha, **bindings,
            'budgetSeconds': BUDGET, 'elapsedSeconds': time.monotonic() - started,
            'scope': 'Installed-runtime readiness observation only; not native/PF eligibility or acceptance',
            'historicalNativeOSProfileMatches': tools['macOS'] == '26.6.2' and tools['kernel'] == '25.6.0',
            'nativeAccepted': False, 'pfAttempted': False, 'buildAttempted': False, 'deviceCreationAttempted': False,
            'launchdServiceOwnershipClaimed': False, 'globalCleanupClaimed': False})
        h.require(time.monotonic() < receipt_end, 'Final receipt budget exceeded')
    return 0 if passed and not h.CANCELLED else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('APP8 READINESS INCOMPLETE (' + type(error).__name__ + ')', file=sys.stderr)
        raise SystemExit(1)
