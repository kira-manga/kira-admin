#!/usr/bin/env python3
"""One read-only SDK metadata capture; no SDK tools, child processes or network."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import xml.etree.ElementTree as ET

BRANCH = 'refs/heads/validation/app8-android-sdk-metadata-20260915-01'
PACKAGES = ('cmdline-tools/latest', 'platform-tools', 'emulator', 'build-tools/36.0.0',
            'platforms/android-36', 'system-images/android-26/google_apis/x86_64')
LAUNCHERS = ('build-tools/36.0.0/d8', 'build-tools/36.0.0/apksigner', 'cmdline-tools/latest/bin/avdmanager')
LEAVES = (*LAUNCHERS, 'cmdline-tools/latest/bin/sdkmanager', 'cmdline-tools/latest/lib/avdmanager-classpath.jar',
          'platform-tools/adb', 'emulator/emulator', 'build-tools/36.0.0/lib/d8.jar',
          'build-tools/36.0.0/lib/apksigner.jar', 'platforms/android-36/android.jar')
PROPERTIES = ('Pkg.Revision', 'Pkg.Path', 'Pkg.Desc', 'Pkg.BuildId', 'AndroidVersion.ApiLevel',
              'AndroidVersion.ExtensionLevel', 'AndroidVersion.IsBaseSdk', 'SystemImage.Abi',
              'SystemImage.TagId', 'SystemImage.VendorId', 'Platform.MinToolsRev')


def bounded(path):
    with path.open('rb') as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError('metadata file cap')
    return data


def describe(path):
    if not path.exists() and not path.is_symlink():
        return {'state': 'ABSENT'}
    return {'state': 'PRESENT', 'targetExists': path.exists(), 'symlink': path.is_symlink(),
            'link': os.readlink(path) if path.is_symlink() else None,
            'realpath': str(path.resolve())}


def read_sdk(sdk, path):
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(sdk) or not stat.S_ISREG(resolved.stat().st_mode):
        raise ValueError('metadata must be a regular file within SDK')
    return bounded(resolved)


def package(sdk, relative):
    path = sdk / relative
    row = describe(path)
    if row['state'] == 'ABSENT':
        return row
    if not path.resolve(strict=True).is_relative_to(sdk) or not path.is_dir():
        raise ValueError('package must resolve within SDK')
    # Direct entries only: no recursive SDK, resources, image or library traversal.
    row['topLevel'], row['directSymlinks'] = [], {}
    with os.scandir(path) as entries:
        for entry in entries:
            if len(row['topLevel']) >= 128:
                raise ValueError('package direct-entry cap')
            row['topLevel'].append(entry.name)
            if entry.is_symlink():
                row['directSymlinks'][entry.name] = describe(Path(entry.path))
    row['topLevel'].sort()
    for name in ('source.properties', 'package.xml'):
        target = path / name
        if not target.exists():
            row[name] = {'state': 'ABSENT'}
            continue
        raw = read_sdk(sdk, target)
        meta = {'state': 'PRESENT', 'sha256': hashlib.sha256(raw).hexdigest()}
        if name == 'source.properties':
            values = [line.split('=', 1) for line in raw.decode('utf-8').splitlines() if '=' in line]
            meta['properties'] = {key.strip(): value.strip() for key, value in values if key.strip() in PROPERTIES}
        else:
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise ValueError('unexpected XML declaration')
            locals_ = [node for node in ET.fromstring(raw) if node.tag.rsplit('}', 1)[-1] == 'localPackage']
            if len(locals_) != 1:
                raise ValueError('missing localPackage')
            local = locals_[0]
            meta['path'] = local.get('path')
            # Never publish license bodies or an archive: only relevant package nodes.
            meta['nodes'] = {node.tag.rsplit('}', 1)[-1]: ET.tostring(node, encoding='unicode') for node in local
                             if node.tag.rsplit('}', 1)[-1] in ('revision', 'type-details', 'dependencies')}
        row[name] = meta
    return row


def expired(_signal, _frame):
    raise TimeoutError('metadata deadline')


def main():
    source = Path(__file__).resolve()
    request = json.loads(bounded(source.with_name('app8-sdk-metadata.request.json')))
    assert request['authorization'] == 'APP8_SDK_METADATA_SINGLE_RUN_AUTHORIZED', 'INERT: primary admission required'
    assert request['collectorSha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert request['baseCarrier'] == '455364ee3433df78d0d47f735e968ba60a65df89'
    assert request['issueSha'] == 'd7b024a1c77f434726c64df36e059ea5af55961c'
    assert hashlib.sha256(source.with_name('app8-android.py').read_bytes()).hexdigest() == request['unchangedNativeControllerSha256']
    assert os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin'
    assert os.environ.get('GITHUB_REF') == BRANCH and os.environ.get('GITHUB_EVENT_NAME') == 'push'
    assert os.environ.get('GITHUB_RUN_ATTEMPT') == '1' and re.fullmatch('[0-9a-f]{40}', os.environ.get('GITHUB_SHA', ''))
    sdk = Path(os.environ['ANDROID_HOME']).resolve(strict=True)
    assert sdk == Path('/usr/local/lib/android/sdk'), 'Unexpected hosted SDK root; do not broaden reads'
    jdk = Path(os.environ['JAVA_HOME_17_X64']).resolve(strict=True)
    assert jdk.is_relative_to('/usr/lib/jvm') or jdk.is_relative_to('/opt/hostedtoolcache')
    run_id = os.environ['GITHUB_RUN_ID']
    assert run_id.isdecimal()
    output = Path(os.environ['RUNNER_TEMP']) / ('app8-sdk-metadata-' + run_id + '-1')
    output.mkdir(mode=0o700, exist_ok=False)
    report = {'schema': 'app8-sdk-metadata-v1', 'carrierSha': os.environ['GITHUB_SHA'],
              'baseCarrier': request['baseCarrier'], 'issueSha': request['issueSha'],
              'collectorSha256': request['collectorSha256'], 'captureStatus': 'INCOMPLETE',
              'sdkRoot': str(sdk), 'packages': {}, 'launchers': {}, 'knownLeaves': {},
              'authoritativeApi26': request['authoritativeApi26'],
              'nativeRun': False, 'runtimeClosureValidated': False, 'sdkMutated': False,
              'scope': 'six package direct entries and fixed metadata/launchers; no recursive traversal'}
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(45)
    try:
        for relative in PACKAGES:
            report['packages'][relative] = package(sdk, relative)
        for relative in LEAVES:
            report['knownLeaves'][relative] = describe(sdk / relative)
        for relative in LAUNCHERS:
            raw = read_sdk(sdk, sdk / relative)
            report['launchers'][relative] = {'sha256': hashlib.sha256(raw).hexdigest(), 'text': raw.decode('utf-8')}
        known = sdk / '.knownPackages'
        report['rootDiscoveryMetadata'] = {'.knownPackages': describe(known)}
        if known.exists():
            raw = read_sdk(sdk, known)
            if len(raw) > 256:
                raise ValueError('unexpected knownPackages hash size')
            report['rootDiscoveryMetadata']['.knownPackages'].update(sha256=hashlib.sha256(raw).hexdigest(), hex=raw.hex())
        # Read link identities, not Java binaries or environment dumps; never run java.
        report['javaResolution'] = {str(path): describe(path) for path in
                                    (Path('/usr/bin/java'), Path('/etc/alternatives/java'), jdk / 'bin/java')}
        report['currentIsolatedPath'] = '/usr/bin:/bin:/usr/sbin:/sbin'
        report['api26Installed'] = report['packages'][PACKAGES[-1]]['state'] == 'PRESENT'
        report['captureStatus'] = 'COMPLETE_METADATA_ONLY'
    except Exception as error:
        report['errorType'] = type(error).__name__  # No arbitrary exception/host data export.
    finally:
        signal.alarm(0)
        payload = json.dumps(report, indent=2, sort_keys=True) + '\n'
        if len(payload.encode()) > 262144:
            raise ValueError('report cap')
        with (output / 'sdk-metadata.json').open('x') as stream:
            stream.write(payload)
    assert report['captureStatus'] == 'COMPLETE_METADATA_ONLY', 'Metadata incomplete; no retry or native fallback'


if __name__ == '__main__':
    if __debug__ is not True:
        raise SystemExit('Assertions required')
    main()
