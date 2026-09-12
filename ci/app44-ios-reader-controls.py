"""Private App44 leaf only. Source-only draft; its unapproved request cannot launch work."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shlex
import shutil
import signal
import stat
import sys
import time
import zipfile

CONTROL = Path(__file__).resolve().parents[1]
TARGET, CLASS = 'ReaderChromeControlsTests', 'ReaderChromeBarsTests'
METHODS = ('testSinglePageChapterButtonsKeepEnablementAndEnabledActions',
           'testEmptyChapterKeepsChapterButtonsAndSliderHidden',
           'testOneManyOneTransitionsKeepFiniteLayoutAndChapterRelativeSeeking')
LEAF = 'iosApp/reader-controls-tests'
INPUTS = {
    'iosApp/iosApp/NativeReader/ReaderChromeView.swift': 'bf9bad6dcc21a5c284fd448be270012df9f3feffaca7b58d44859172b697c6ae',
    LEAF + '/ReaderChromeBarsTests.swift': '00521a691a65c1a419df289fabef2f727f877f751ac3075369c549d5b4eb67ae',
    LEAF + '/project.yml': '7347aafc7e9c10662ab02664aedd8ed25a75ad866aa94bfc7ce6bfc272b5d084',
    LEAF + '/.gitignore': '71560d61d40d33d0b45905f47b600fac842947f43310422b5c61b0012fe7de4e',
}
OWNER_SHA = 'b7c9e9b16cc0bc6975b9c34cdd136f09c8ca224a934da3ac341ebc3758345f8b'
XCODE = '/Applications/Xcode_26.4.1.app/Contents/Developer'
XCODEGEN = {
    'version': '2.46.0',
    'url': 'https://github.com/yonaskolb/XcodeGen/releases/download/2.46.0/xcodegen.artifactbundle.zip',
    'archiveBytes': 4286070,
    'archiveSha256': 'ef6d0a23bfb7393387f98e321ffd78a487231172e2e78c48d3c26275c263fd0c',
    'entryCount': 47,
    'expandedBytes': 14237480,
    'layoutSha256': 'c1083f8d7cb229bf4628f1bc141756901a4f65d2328361d1cd551305da89c42d',
    'executable': 'xcodegen.artifactbundle/xcodegen-2.46.0-macosx/bin/xcodegen',
    'executableBytes': 14229032,
    'executableSha256': '8774da746668bc18fe74e54cbaf10f2631a1fb05947cd374179aa912f14f99db',
}
RUNTIME, DEVICE = 'com.apple.CoreSimulator.SimRuntime.iOS-26-4', 'com.apple.CoreSimulator.SimDeviceType.iPhone-17'
UUID = r'[0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12}'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular file: ' + str(path))
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    return value.hexdigest()


def read_json(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 65536, 'Invalid request/event file')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise RuntimeError('Non-finite JSON')
    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=constant)


def checked_request():
    request = read_json(CONTROL / 'ci/app44-ios-reader-controls.request.json')
    fixed = {'schema': 'app44-ios-reader-controls-private-v1', 'authorization': 'APP44_APPLE_ONE_ATTEMPT_AUTHORIZED',
             'sourceRepository': 'kira-manga/kira-app', 'nativeInputs': INPUTS, 'target': TARGET, 'class': CLASS,
             'methods': list(METHODS), 'expectedRunAttempt': 1, 'ownerSha256': OWNER_SHA, 'developerDir': XCODE,
             'xcodegenIntake': XCODEGEN}
    require(set(request) == set(fixed) | {'sourceSha', 'controllerSha256', 'workflowSha256'}, 'Unknown/missing request field')
    require(type(request['expectedRunAttempt']) is int and all(request[key] == value for key, value in fixed.items()),
            'Unapproved or changed request')
    require(isinstance(request['sourceSha'], str) and re.fullmatch('[0-9a-f]{40}', request['sourceSha'])
            and request['sourceSha'] != '0' * 40, 'An exact reviewed issue commit is required')
    context = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'kira-manga/kira-admin', 'GITHUB_EVENT_NAME': 'push',
               'GITHUB_REF': 'refs/heads/remediation/app-29-backend-complaints', 'GITHUB_RUN_ATTEMPT': '1',
               'RUNNER_OS': 'macOS', 'RUNNER_ARCH': 'ARM64', 'RUNNER_ENVIRONMENT': 'github-hosted', 'ImageOS': 'macos26'}
    require(all(os.environ.get(key) == value for key, value in context.items()), 'Wrong private hosted invocation')
    require(re.fullmatch('[1-9][0-9]*', os.environ.get('GITHUB_RUN_ID', ''))
            and re.fullmatch('[0-9a-f]{40}', os.environ.get('GITHUB_SHA', '')), 'Invalid run/carrier identity')
    require(read_json(Path(os.environ['GITHUB_EVENT_PATH']))['repository']['private'] is True, 'Carrier is not private')
    paths = {'controllerSha256': 'ci/app44-ios-reader-controls.py',
             'workflowSha256': '.github/workflows/app44-ios-reader-controls.yml', 'ownerSha256': 'ci/app8-apple.py'}
    require(all(request[key] == digest(CONTROL / path) for key, path in paths.items()), 'Changed controller/workflow/owner')
    return request


class Leaf:
    def __init__(self, owner, source, run, request):
        self.owner, self.source, self.run, self.request = owner, source, run, request
        self.end = time.monotonic() + 1200
        self.work_end = self.end - 240
        self.reports, self.project = run / 'reports', source / LEAF / (TARGET + '.xcodeproj')
        self.derived, self.bundle = run / 'work/DerivedData', run / 'reports' / (TARGET + '.xcresult')
        self.state = {'name': 'App44-' + os.environ['GITHUB_RUN_ID'] + '-1', 'creating': False, 'udid': None}
        self.errors, self.source_ready, self.project_intended = [], False, False
        self.env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(Path.home().resolve()),
                    'TMPDIR': str(run / 'tmp') + '/', 'DEVELOPER_DIR': XCODE, 'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8'}
        self.commands = None  # No child, including a census, before the borrowed capability gate.
        self.result = {'status': 'INCOMPLETE', 'nativeTestAccepted': False,
                       'sourceSha': request['sourceSha'], 'carrierSha': os.environ['GITHUB_SHA'],
                       'run': run.name, 'testCommandSucceeded': False, 'errors': self.errors, 'globalServicesRestored': False}
        self.save('request.json', request)
        self.save('result.json', self.result)

    def save(self, name, value, limit=131072):
        self.owner.save(self.reports / name, value, limit=limit)

    def call(self, argv, label, seconds=30, cleaning=False, end=None):
        self.result['finalOwnedAbsence'] = False
        return self.commands.call(argv, label, seconds=seconds, cleaning=cleaning,
                                  end=end if end is not None else (self.end if cleaning else self.work_end))

    def source_receipt(self, after=False):
        git = ['/usr/bin/git', '-C', str(self.source)]
        sha = self.call(git + ['rev-parse', 'HEAD'], 'source-after-sha' if after else 'source-sha', cleaning=after).strip()
        status = self.call(git + ['status', '--porcelain', '--untracked-files=all'],
                           'source-after-status' if after else 'source-status', cleaning=after)
        require(sha == self.request['sourceSha'] and not status, 'Changed/wrong/nonclean exact source checkout')
        require(all((self.source / path).resolve() == self.source / path for path in INPUTS), 'Symlinked native input')
        hashes = {path: digest(self.source / path) for path in INPUTS}
        require(hashes == INPUTS, 'Native source/spec/test inputs changed')
        self.save('source-after.json' if after else 'source-before.json', {'sourceSha': sha, 'nativeInputs': hashes})
        self.result['sourceAfterVerified' if after else 'sourceBeforeVerified'] = True

    def tools_and_project(self):
        self.source_receipt()
        require(not self.project.exists() and not self.project.is_symlink(), 'Preexisting generated project; refuse cleanup')
        self.source_ready = True
        prerequisites = {'developerDir': XCODE, 'developerDirExists': Path(XCODE).is_dir(),
                         'xcodegenLookup': {'status': 'NOT_OBSERVED'}, 'fallback': {'status': 'NOT_REACHED'}}
        self.save('prerequisites.json', prerequisites)
        try:
            lookup = shutil.which('xcodegen')  # Observe the ambient lookup; do not broaden the child PATH.
            prerequisites['xcodegenLookup'] = {'status': 'OBSERVED', 'found': lookup is not None,
                                               'lookupPath': lookup, 'resolvedPath': None}
            self.save('prerequisites.json', prerequisites)
            installed = Path(lookup).resolve() if lookup else None
            prerequisites['xcodegenLookup']['resolvedPath'] = str(installed) if installed else None
        except Exception as error:
            prerequisites['xcodegenLookup'].update(status='FAILED', error=str(error))
            raise RuntimeError('XCODEGEN_LOOKUP_FAILED: ' + str(error)) from error
        finally:
            self.save('prerequisites.json', prerequisites)
        require(prerequisites['developerDirExists'], 'PINNED_XCODE_MISSING: ' + XCODE + '; no fallback/installation')
        identities = {'developerDir': XCODE, 'python': sys.version, 'pythonExecutable': str(Path(sys.executable).resolve()),
                      'imageVersion': os.environ.get('ImageVersion')}
        self.save('tools.json', identities)
        for key, argv, label, expected in (
            ('xcode', ['/usr/bin/xcodebuild', '-version'], 'xcode-version', 'Xcode 26.4.1\nBuild version 17E202'),
            ('sdk', ['/usr/bin/xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], 'sdk-version', '26.4'),
            ('sdkBuild', ['/usr/bin/xcrun', '--sdk', 'iphonesimulator', '--show-sdk-build-version'], 'sdk-build', '23E252'),
        ):
            identities[key] = self.call(argv, label).strip()
            self.save('tools.json', identities)
            require(identities[key] == expected, 'PINNED_' + key.upper() + '_IDENTITY_MISMATCH; no fallback')
        xcodegen = self.select_xcodegen(installed, prerequisites)
        identities.update(xcodegenPath=str(xcodegen), xcodegenSha256=XCODEGEN['executableSha256'],
                          xcodegenOrigin=prerequisites['selectedXcodegen']['origin'], xcodegenRelease=XCODEGEN['version'])
        self.save('tools.json', identities)
        try:
            version_output = self.call([xcodegen, '--version'], 'xcodegen-version').strip()
            require(len(version_output) <= 128, 'XCODEGEN_VERSION_OUTPUT_OVERSIZED; raw log retained')
            identities['xcodegen'] = version_output
            prerequisites['selectedXcodegen']['versionOutput'] = identities['xcodegen']
            require(re.search(r'(?<![\w.])' + re.escape(XCODEGEN['version'])
                    + r'(?![\w.])', identities['xcodegen']), 'XCODEGEN_VERSION_MISMATCH')
        except Exception as error:
            prerequisites['selectedXcodegen']['versionError'] = str(error)
            raise RuntimeError('XCODEGEN_VERSION_FAILED: ' + str(error)) from error
        finally:
            self.save('prerequisites.json', prerequisites)
            self.save('tools.json', identities)
        self.xcresulttool = Path(self.call(['/usr/bin/xcrun', '--find', 'xcresulttool'], 'xcresulttool-path').strip()).resolve()
        require(self.xcresulttool.is_relative_to(Path(XCODE)), 'Result tool is outside the selected Xcode')
        self.xcresulttool_sha = digest(self.xcresulttool)
        identities.update(xcresulttoolPath=str(self.xcresulttool), xcresulttoolSha256=self.xcresulttool_sha)
        self.save('tools.json', identities)
        require(hashlib.sha256(self.xcodegen_bytes(xcodegen, XCODEGEN['executableBytes'], self.work_end)).hexdigest()
                == XCODEGEN['executableSha256'], 'XCODEGEN_CHANGED_BEFORE_GENERATION')
        self.project_intended = True
        self.call([xcodegen, 'generate', '--spec', self.source / LEAF / 'project.yml', '--project', self.source / LEAF],
                  'generate-project', seconds=60)
        require(hashlib.sha256(self.xcodegen_bytes(xcodegen, XCODEGEN['executableBytes'], self.work_end)).hexdigest()
                == XCODEGEN['executableSha256'], 'XCODEGEN_CHANGED_DURING_GENERATION')
        self.save('project.json', {'pbxprojSha256': digest(self.project / 'project.pbxproj'),
                                  'schemeSha256': digest(self.project / 'xcshareddata/xcschemes' / (TARGET + '.xcscheme'))})

    def xcodegen_bytes(self, path, limit, end):
        require(not self.owner.CANCELLED and time.monotonic() < end and path.resolve() == path,
                'XCODEGEN_INTAKE_LATE_OR_UNSAFE_PATH')
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit <= 33554432,
                    'XCODEGEN_INTAKE_NONREGULAR_OR_OVERSIZED_FILE')
            data = stream.read(before.st_size + 1)
        after = path.lstat()
        require(not self.owner.CANCELLED and time.monotonic() < end and len(data) == before.st_size
                and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode),
                'XCODEGEN_INTAKE_LATE_OR_CHANGED_FILE')
        return data

    def select_xcodegen(self, installed, prerequisites):
        lookup = prerequisites['xcodegenLookup']
        lookup.update(accepted=False, acceptancePolicy='Exact reviewed universal binary SHA-256; unknown binaries are not executed')
        try:
            if installed is not None:
                require(installed.is_file() and os.access(installed, os.X_OK), 'XCODEGEN_LOOKUP_PATH_CHANGED')
                lookup['bytes'] = installed.stat().st_size
                if 0 <= lookup['bytes'] <= 33554432:
                    data = self.xcodegen_bytes(installed, 33554432, min(self.work_end, time.monotonic() + 30))
                    lookup['sha256'] = hashlib.sha256(data).hexdigest()
                    lookup['accepted'] = lookup['sha256'] == XCODEGEN['executableSha256']
                lookup['reason'] = 'reviewed-binary' if lookup['accepted'] else 'binary-not-reviewed-or-over-cap'
            else:
                lookup['reason'] = 'not-found'
        except Exception as error:
            lookup['acceptanceError'] = str(error)
            raise RuntimeError('XCODEGEN_INSTALLED_IDENTITY_FAILED: ' + str(error)) from error
        finally:
            self.save('prerequisites.json', prerequisites)
        if lookup['accepted']:
            xcodegen, origin = installed, 'preinstalled-reviewed-binary'
            prerequisites['fallback']['status'] = 'NOT_NEEDED'
        else:
            xcodegen, origin = self.intake_xcodegen(prerequisites), 'pinned-upstream-release'
        prerequisites['selectedXcodegen'] = {'path': str(xcodegen), 'origin': origin, 'release': XCODEGEN['version'],
                                             'sha256': XCODEGEN['executableSha256'], 'versionOutput': None}
        self.save('prerequisites.json', prerequisites)
        return xcodegen

    def intake_xcodegen(self, prerequisites):
        end = min(self.work_end, time.monotonic() + 30)
        receipt = {'status': 'STARTED', 'stage': 'curl-identity', 'pin': XCODEGEN, 'curlPath': '/usr/bin/curl', 'secondsCap': 30,
                   'expandedBytesCap': 33554432, 'entryCap': 64, 'retryCount': 0}
        prerequisites['fallback'] = receipt
        self.save('prerequisites.json', prerequisites)
        try:
            curl = Path('/usr/bin/curl')
            receipt['curlSha256'] = hashlib.sha256(self.xcodegen_bytes(curl, 33554432, end)).hexdigest()
            curl_version = self.call([curl, '-q', '--version'], 'xcodegen-curl-version', end=end).splitlines()[0]
            require(len(curl_version) <= 512, 'Curl version header oversized; raw log retained')
            receipt['curlVersion'] = curl_version
            version = re.match(r'curl (\d+)\.(\d+)\.(\d+)\b', receipt['curlVersion'])
            require(version is not None and tuple(map(int, version.groups())) >= (8, 4, 0),
                    'Curl 8.4.0+ required for a streaming byte cap; no installation')
            root = self.run / 'work/xcodegen-intake'
            root.mkdir(mode=0o700)
            archive = root / 'xcodegen.artifactbundle.zip'
            receipt['stage'] = 'download'
            self.save('prerequisites.json', prerequisites)
            downloaded = self.call([curl, '-q', '--proto', '=https', '--proto-redir', '=https', '--tlsv1.2',
                '--connect-timeout', '5', '--max-time', '30', '--max-filesize', str(XCODEGEN['archiveBytes']),
                '--max-redirs', '3', '--retry', '0', '--fail', '--silent', '--show-error', '--location',
                '--output', archive, '--write-out', '%{http_code} %{size_download}\n', XCODEGEN['url']],
                'xcodegen-download', end=end).strip()
            require(len(downloaded) <= 128, 'Unexpected download diagnostic; raw log retained')
            receipt['downloadOutput'] = downloaded
            require(downloaded == '200 ' + str(XCODEGEN['archiveBytes']), 'Unexpected upstream HTTP/byte receipt')
            receipt['stage'] = 'archive-verification'
            self.save('prerequisites.json', prerequisites)
            data = self.xcodegen_bytes(archive, XCODEGEN['archiveBytes'], end)
            receipt.update(archiveBytes=len(data), archiveSha256=hashlib.sha256(data).hexdigest())
            require(len(data) == XCODEGEN['archiveBytes'] and receipt['archiveSha256'] == XCODEGEN['archiveSha256'],
                    'Pinned upstream archive size/digest mismatch')
            receipt['stage'] = 'safe-extraction'
            self.save('prerequisites.json', prerequisites)
            layout, names = [], set()
            with zipfile.ZipFile(io.BytesIO(data)) as bundle:
                members = bundle.infolist()
                require(len(members) == XCODEGEN['entryCount'] <= 64
                        and sum(item.file_size for item in members) == XCODEGEN['expandedBytes'] <= 33554432,
                        'Unexpected/over-budget archive entry set')
                for member in members:
                    require(not self.owner.CANCELLED and time.monotonic() < end, 'Extraction cancelled/expired')
                    name, mode = PurePosixPath(member.filename), member.external_attr >> 16
                    require(member.orig_filename == member.filename and member.filename not in names
                            and not name.is_absolute() and '..' not in name.parts and '\\' not in member.filename
                            and str(name) + ('/' if member.is_dir() else '') == member.filename
                            and member.compress_type in (0, 8) and not member.flag_bits & 1
                            and stat.S_IFMT(mode) == (stat.S_IFDIR if member.is_dir() else stat.S_IFREG)
                            and not mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX), 'Unsafe ZIP member')
                    names.add(member.filename)
                    target = root / str(name)
                    require(target.resolve() == target and target.is_relative_to(root), 'Unsafe extraction target')
                    with bundle.open(member) as stream:
                        content = stream.read(member.file_size + 1)
                    require(len(content) == member.file_size and time.monotonic() < end, 'Late/oversized ZIP content')
                    if member.is_dir():
                        require(not content, 'Nonempty ZIP directory')
                        target.mkdir(mode=0o700)
                    else:
                        with target.open('xb') as stream:
                            stream.write(content)  # No archive permissions, extractall, installer or executable invocation.
                        require(hashlib.sha256(self.xcodegen_bytes(target, member.file_size, end)).digest()
                                == hashlib.sha256(content).digest(), 'Extracted content changed')
                    layout.append({'path': member.filename, 'type': 'directory' if member.is_dir() else 'file',
                                   'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
            layout_bytes = (json.dumps(sorted(layout, key=lambda row: row['path']), sort_keys=True, separators=(',', ':')) + '\n').encode()
            receipt['layoutSha256'] = hashlib.sha256(layout_bytes).hexdigest()
            require(receipt['layoutSha256'] == XCODEGEN['layoutSha256'], 'Reviewed archive content layout mismatch')
            info = read_json(root / 'xcodegen.artifactbundle/info.json')
            expected = {'version': XCODEGEN['version'], 'type': 'executable', 'variants': [{
                'path': 'xcodegen-2.46.0-macosx/bin/xcodegen', 'supportedTriples': ['x86_64-apple-macosx', 'arm64-apple-macosx']}]}
            require(info == {'schemaVersion': '1.0', 'artifacts': {'xcodegen': expected}}, 'Executable/version/ARM64 mapping changed')
            executable = root / XCODEGEN['executable']
            receipt['executableSha256'] = hashlib.sha256(self.xcodegen_bytes(executable, XCODEGEN['executableBytes'], end)).hexdigest()
            require(receipt['executableSha256'] == XCODEGEN['executableSha256'], 'Extracted executable digest mismatch')
            executable.chmod(0o700)  # Private owned scratch only; sibling resource bundle remains beside the binary.
            archive.unlink()
            require(not self.owner.CANCELLED and time.monotonic() < end, 'XcodeGen intake cancelled/expired')
            receipt.update(status='READY', stage='complete', archiveRemoved=True)
            return executable
        except Exception as error:
            receipt.update(status='FAILED', error=str(error))
            raise RuntimeError('XCODEGEN_INTAKE_' + receipt['stage'].upper().replace('-', '_') + '_FAILED: ' + str(error)) from error
        finally:
            self.save('prerequisites.json', prerequisites)

    def devices(self, cleaning=False, end=None):
        inventory = self.owner.parse_json(self.call(['/usr/bin/xcrun', 'simctl', 'list', 'devices', '--json'],
                                                   'devices', cleaning=cleaning, end=end))['devices']
        rows = [dict(row, runtime=runtime) for runtime, values in inventory.items() for row in values]
        require(len(rows) <= 256 and len({row['udid'] for row in rows}) == len(rows), 'Invalid device inventory')
        return rows

    def save_device(self):
        self.owner.save(self.run / 'simulator.json', self.state)
        self.save('simulator.json', self.state)

    def own_device(self, row):
        require(row['name'] == self.state['name'] and row['runtime'] == RUNTIME
                and re.fullmatch(UUID, row['udid']) and (not self.state['udid'] or row['udid'] == self.state['udid']),
                'Ambiguous/foreign Simulator identity')
        root = Path(self.env['HOME']) / 'Library/Developer/CoreSimulator/Devices' / row['udid']
        require(Path(row['dataPath']).resolve() == root / 'data' and root.is_dir() and not root.is_symlink()
                and root.stat().st_uid == os.getuid(), 'Foreign/missing Simulator data root')
        self.state.update(udid=row['udid'], dataRoot=str(root))
        self.save_device()

    def prepare_device(self):
        runtimes = self.owner.parse_json(self.call(['/usr/bin/xcrun', 'simctl', 'list', 'runtimes', '--json'],
                                                  'runtimes', seconds=90))['runtimes']
        matches = [row for row in runtimes if row['identifier'] == RUNTIME]
        require(len(matches) == 1 and matches[0].get('isAvailable') is True and matches[0]['version'] == '26.4.1'
                and matches[0]['buildversion'] == '23E254a' and 'arm64' in matches[0]['supportedArchitectures'],
                'Exact installed ARM64 iOS26.4.1 runtime required; no download/fallback/retry')
        types = self.owner.parse_json(self.call(['/usr/bin/xcrun', 'simctl', 'list', 'devicetypes', '--json'], 'device-types'))
        require(sum(row['identifier'] == DEVICE for row in types['devicetypes']) == 1, 'Missing iPhone17 device type')
        require(not any(self.state['name'] in row['name'] for row in self.devices()), 'Owned Simulator name already present')
        self.state.update(creating=True, runtime=RUNTIME, runtimeVersion='26.4.1', runtimeBuild='23E254a', deviceType=DEVICE)
        self.save_device()
        created = self.call(['/usr/bin/xcrun', 'simctl', 'create', self.state['name'], DEVICE, RUNTIME], 'create-device').strip()
        require(re.fullmatch(UUID, created), 'Invalid returned owned Simulator UDID')
        self.state.update(udid=created, creating=False)
        self.save_device()
        matches = [row for row in self.devices() if row['udid'] == self.state['udid']]
        require(len(matches) == 1 and matches[0]['state'] == 'Shutdown', 'Created device is not uniquely shut down')
        self.own_device(matches[0])
        end = min(self.work_end, time.monotonic() + 180)
        self.call(['/usr/bin/xcrun', 'simctl', 'boot', self.state['udid']], 'boot-device', end=end)
        self.call(['/usr/bin/xcrun', 'simctl', 'bootstatus', self.state['udid'], '-b'], 'bootstatus', seconds=180, end=end)
        matches = [row for row in self.devices(end=end) if row['udid'] == self.state['udid']]
        require(len(matches) == 1 and matches[0]['state'] == 'Booted', 'Owned Simulator boot is unproved')
        self.own_device(matches[0])
        self.state['booted'] = True
        self.save_device()

    def test_argv(self):
        return ['/usr/bin/xcodebuild', 'test', '-project', self.project, '-scheme', TARGET, '-configuration', 'Debug',
                '-sdk', 'iphonesimulator', '-destination', 'platform=iOS Simulator,id=' + self.state['udid'],
                '-destination-timeout', '60', '-jobs', '1', '-parallel-testing-enabled', 'NO',
                '-maximum-concurrent-test-simulator-destinations', '1', '-test-iterations', '1',
                '-test-timeouts-enabled', 'YES', '-default-test-execution-time-allowance', '30',
                '-maximum-test-execution-time-allowance', '60', '-derivedDataPath', self.derived,
                '-resultBundlePath', self.bundle, '-disableAutomaticPackageResolution', '-skipPackageUpdates',
                *['-only-testing:' + TARGET + '/' + CLASS + '/' + method for method in METHODS],
                'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=YES', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO']

    def collect_tests(self, end):
        require(self.bundle.is_dir() and not self.bundle.is_symlink(), 'Missing real xcresult bundle')
        require(digest(self.xcresulttool) == self.xcresulttool_sha, 'Selected result tool changed')
        outputs = {}
        for kind in ('summary', 'tests'):
            for schema in (True, False):
                label = 'xcresult-' + kind + ('-schema' if schema else '')
                argv = [self.xcresulttool, 'get', 'test-results', kind, '--path', self.bundle]
                if schema:
                    argv.append('--schema')
                # No established numeric version: same selected binary/default and actual bundle for both outputs.
                self.call(argv, label, cleaning=True, end=end)
                task = next(task for task in self.commands.tasks if task['receipt']['label'] == label)
                with task['log'].open('rb') as stream:
                    data = stream.read(1048577)
                require(time.monotonic() < end and len(data) <= 1048576, 'Late/oversized result output')
                self.owner.parse_json(data.decode('utf-8'))  # Syntax only; no guessed result/schema grammar.
                name = label + '.json'
                with (self.reports / name).open('xb') as stream:
                    stream.write(data)  # Exact captured bytes, never a JSON reserialization or marker substitute.
                outputs[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                 'argv': list(map(str, argv)), 'commandOutput': task['log'].name}
        require(digest(self.xcresulttool) == self.xcresulttool_sha, 'Result tool changed during capture')
        self.save('xcresult-evidence.json', {
            'adjudication': 'NOT_PERFORMED', 'schemaVersionArgument': None,
            'xcresulttoolPath': str(self.xcresulttool), 'xcresulttoolSha256': self.xcresulttool_sha,
            'bundle': str(self.bundle), 'outputs': outputs,
            'requiredPrimaryReview': [
                'Establish actual schema/result correspondence and version information from bound raw evidence; no guessed version.',
                'Exactly the requested target/class/three methods, passed once each; verify actual plan/configuration/bundle/suite identities.',
                'Exactly one owned UDID/device and Debug ARM64 iOS26.4.1 Simulator configuration; no repeated/hidden executions.',
                'Exactly three tests, zero failures/errors/skips/expected failures; missing or ambiguous evidence blocks acceptance.',
            ],
            'target': TARGET, 'class': CLASS, 'methods': list(METHODS), 'ownedUdid': self.state['udid'],
        })
        self.result_outputs = outputs
        self.result['resultEvidencePreserved'] = True
        folder = self.derived / 'Build/Intermediates.noindex' / (TARGET + '.build') / 'Debug-iphonesimulator' / (TARGET + '.build')
        filelist = folder / 'Objects-normal/arm64' / (TARGET + '.SwiftFileList')
        require(filelist.is_file() and not filelist.is_symlink() and filelist.stat().st_size <= 65536, 'Missing actual Swift file list')
        files = shlex.split(filelist.read_text())
        expected = {str(self.source / path) for path in INPUTS if path.endswith('.swift')}
        require(len(files) == 2 and set(files) == expected, 'Actual compilation did not use exactly the two bound Swift files')
        log = next(task['log'] for task in self.commands.tasks if task['receipt']['label'] == 'xcodebuild-test')
        raw = log.read_text(errors='replace')
        require(str(filelist) in raw, 'No actual Swift file-list invocation in the raw build log')
        require(not any(text in raw for text in ('Unable to simultaneously satisfy constraints', 'UIViewAlertForUnsatisfiableConstraints')),
                'Unexplained UIKit constraint diagnostic; retain for primary review')
        bundle = self.derived / 'Build/Products/Debug-iphonesimulator' / (TARGET + '.xctest')
        info_path = bundle / 'Info.plist'
        require(bundle.resolve() == bundle and info_path.is_file() and not info_path.is_symlink()
                and info_path.stat().st_size <= 65536, 'Missing/nonregular compiled bundle metadata')
        with info_path.open('rb') as stream:
            info = plistlib.load(stream)
        require(info['CFBundleIdentifier'] == 'me.manga.kira.readercontrols.tests' and info['CFBundleExecutable'] == TARGET,
                'Wrong compiled XCTest bundle identity')
        self.owner.inspect_macho(self.commands, bundle / TARGET, 'xctest-binary', end)
        self.save('compilation-evidence.json', {'swiftInputs': sorted(files), 'filelistSha256': digest(filelist),
                                              'binarySha256': digest(bundle / TARGET)})
        self.result['compilationEvidencePreserved'] = True

    def bundle_snapshot(self, end, target=None):
        require(self.bundle.is_dir() and self.bundle.resolve() == self.bundle, 'No regular fresh xcresult to retain')
        if target is not None:
            target.mkdir(mode=0o700)
        entries, pending, total = [], [self.bundle], 0
        while pending:
            directory = pending.pop()
            require(time.monotonic() < end and directory.is_dir() and directory.resolve() == directory,
                    'Late/changed xcresult directory')
            with os.scandir(directory) as children:
                for child in children:
                    require(time.monotonic() < end and len(entries) < 4096, 'Late/oversized xcresult entry set')
                    path = Path(child.path)
                    info = path.lstat()
                    row = {'path': str(path.relative_to(self.bundle)), 'bytes': info.st_size}
                    if stat.S_ISDIR(info.st_mode):
                        row['type'] = 'directory'
                        pending.append(path)
                        if target is not None:
                            (target / row['path']).mkdir(mode=0o700)
                    else:
                        require(stat.S_ISREG(info.st_mode), 'Symlink/nonregular xcresult entry')
                        total += info.st_size
                        require(0 <= info.st_size and total <= 67108864, 'Complete xcresult exceeds its private evidence budget')
                        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
                            opened = os.fstat(stream.fileno())
                            require(stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino, opened.st_size)
                                    == (info.st_dev, info.st_ino, info.st_size), 'xcresult entry changed before reading')
                            data = stream.read(info.st_size + 1)
                        current = path.lstat()
                        require(time.monotonic() < end and len(data) == info.st_size
                                and (current.st_dev, current.st_ino, current.st_mode, current.st_size, current.st_mtime_ns)
                                == (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns),
                                'xcresult entry changed during bounded reading')
                        row.update(type='file', sha256=hashlib.sha256(data).hexdigest())
                        if target is not None:
                            copied = target / row['path']
                            with copied.open('xb') as stream:
                                stream.write(data)
                            require(copied.stat().st_size == row['bytes'] and digest(copied) == row['sha256'] and time.monotonic() < end,
                                    'Copied xcresult evidence changed')
                    entries.append(row)
        require(time.monotonic() < end and any(row['path'] == 'Info.plist' and row['type'] == 'file' for row in entries),
                'Late/empty/incomplete xcresult package')
        return {'bytes': total, 'entries': sorted(entries, key=lambda row: row['path'])}

    def dispose_device(self):
        if not self.state['creating'] and not self.state['udid']:
            self.result['deviceDisposition'] = 'not-created'
            return True
        rows = self.devices(cleaning=True)
        matches = [row for row in rows if row['name'] == self.state['name'] or row['udid'] == self.state['udid']]
        require(len(matches) <= 1, 'Ambiguous owned Simulator during cleanup')
        if matches:
            self.own_device(matches[0])
            if matches[0]['state'] != 'Shutdown':
                self.call(['/usr/bin/xcrun', 'simctl', 'shutdown', self.state['udid']], 'shutdown-owned-device', cleaning=True)
            current = [row for row in self.devices(cleaning=True) if row['udid'] == self.state['udid']]
            require(len(current) == 1 and current[0]['state'] == 'Shutdown', 'Owned shutdown unproved')
            self.call(['/usr/bin/xcrun', 'simctl', 'delete', self.state['udid']], 'delete-owned-device', cleaning=True)
            self.result['deviceDisposition'] = 'deleted'
        else:
            self.result['deviceDisposition'] = 'absent-after-create-intent'
        require(not any(self.state['name'] in row['name'] or row['udid'] == self.state['udid']
                        for row in self.devices(cleaning=True)), 'Owned/related Simulator remains')
        require(not self.state.get('dataRoot') or not Path(self.state['dataRoot']).exists(), 'Owned Simulator data root remains')
        return True

    def absence(self):
        self.result['finalOwnedAbsence'] = False
        self.commands.drain()
        observation = self.commands.observe(cleaning=True, full=True)
        markers = (str(self.run) + '/', str(self.source) + '/', self.state['udid'])
        rows = [row for row in observation['rows'] if row['pid'] != os.getpid() and not row['state'].startswith('Z')
                and any(marker and marker in row['command'] for marker in markers)]
        settled = self.commands.drain(observation)
        self.commands.fresh(observation)
        receipt = {'commandGroupsSettled': settled, 'scopedWorkersAbsent': not rows,
                   'workers': [{key: value for key, value in row.items() if key != 'command'} for row in rows]}
        self.save('owned-absence.json', receipt)
        require(settled and not rows, 'Owned command/device/path worker remains; no global-name or historical-PID signaling')
        self.result['finalOwnedAbsence'] = True

    def remove_scratch(self):
        if self.commands is not None:
            try:
                if self.source_ready:
                    self.source_receipt(after=True)
            finally:
                self.absence()  # A failed source check still needs fresh settlement before retaining evidence.
        else:
            require(not self.project_intended and not self.state['creating'] and not self.state['udid'], 'Unexpected unowned work')
        if self.project_intended and self.project.exists():
            require(self.project.resolve() == self.project and self.project.is_dir(), 'Unsafe generated project cleanup')
            shutil.rmtree(self.project)
        require(not self.project_intended or (not self.project.exists() and not self.project.is_symlink()), 'Generated project remains')
        for name in ('work', 'tmp'):
            path = self.run / name
            require(path.resolve() == path and path.is_dir(), 'Unsafe owned scratch root')
            shutil.rmtree(path)
        self.result['scratchRemoved'] = True  # No further census: its scratch has now been removed.

    def stage_upload(self):
        upload = self.run / 'upload'
        upload.mkdir(mode=0o700)
        self.owner.save(upload / 'result.json', self.result)  # Always fail-closed if later staging aborts.
        remaining_json, remaining_logs = 8388608 - 131072, 4194304  # Reserve the final result receipt within the same JSON cap.
        for path in sorted(self.reports.iterdir()):
            require(time.monotonic() < self.end, 'Report snapshot exceeded the controller deadline')
            if path == self.bundle or path.name == 'result.json':
                continue
            require(path.resolve() == path and path.is_file() and path.suffix in ('.json', '.log'), 'Unexpected report entry')
            limit = min(2097152, remaining_json) if path.suffix == '.json' else min(1048576, remaining_logs)
            with path.open('rb') as stream:
                data = stream.read(limit + 1)
            if len(data) > limit:
                self.errors.append('Artifact report cap exceeded: ' + path.name)
                data = data[:limit]
            expected = getattr(self, 'result_outputs', {}).get(path.name)
            require(expected is None or (len(data) == expected['bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256']),
                    'Captured raw schema/result changed or was truncated')
            with (upload / path.name).open('xb') as stream:
                stream.write(data)  # Stable bounded snapshot even if an unresolved writer still owns the original inode.
            if path.suffix == '.json':
                remaining_json -= len(data)
            else:
                remaining_logs -= len(data)
        if not self.bundle.exists() or not self.result.get('finalOwnedAbsence'):
            self.result['bundleExcludedFromUpload'] = 'Missing/unsettled/over-budget; source evidence remains on disposable VM'
            return
        target = upload / self.bundle.name
        try:
            # All three complete inventories occur after the final owned barrier, with no further child launch.
            inventory = self.bundle_snapshot(self.end)
            require(self.bundle_snapshot(self.end, target) == inventory, 'xcresult entry set/content changed during complete copy')
            require(self.bundle_snapshot(self.end) == inventory, 'xcresult entry set/content changed after complete copy')
            self.save('xcresult-files.json', inventory, limit=min(2097152, remaining_json))
            self.owner.save(upload / 'xcresult-files.json', inventory, limit=min(2097152, remaining_json))
            self.result['completeBundleRetained'] = True
        except Exception:
            self.result['bundleExcludedFromUpload'] = 'Changed/invalid/over-budget final bundle; no complete retention claim'
            if target.exists():
                shutil.rmtree(target)  # Only this controller's incomplete upload copy, never original evidence.
            raise

    def finish(self):
        if self.commands is None:
            self.result.update(noChildOwnerCreated=True, ownedDeviceAbsent=True, deviceDisposition='not-created',
                               normalOwnedCompletion=False, logsWithinCap=True)
            try:
                self.remove_scratch()
            except Exception as error:
                self.errors.append('unused scratch: ' + str(error))
        else:
            try:
                self.result['immediateGroupsSettled'] = self.commands.drain()
                require(self.result['immediateGroupsSettled'], 'Immediate owned command settlement failed')
                capture_end = min(self.end - 180, time.monotonic() + 60)
                if self.result.get('testAttempted'):
                    try:
                        self.collect_tests(capture_end)
                    except Exception as error:
                        self.errors.append('XCTest evidence: ' + str(error))
                    finally:
                        require(self.commands.drain(), 'XCTest extraction command remains owned/unsettled')
            except Exception as error:
                self.errors.append('immediate stop/evidence: ' + str(error))
            try:
                self.commands.drain()
                self.result['ownedDeviceAbsent'] = self.dispose_device()
                self.absence()
                self.remove_scratch()
            except Exception as error:
                self.errors.append('owned cleanup: ' + str(error))
                for label, action in (('observer retirement', self.commands.retire_observer), ('receipt', self.commands.checkpoint)):
                    try:
                        action()
                    except Exception as nested:
                        self.errors.append(label + ': ' + str(nested))
            self.result.update(normalOwnedCompletion=self.commands.normal(), logsWithinCap=self.commands.within_cap())
        self.result['cancelled'] = self.owner.CANCELLED
        try:
            self.stage_upload()
        except Exception as error:
            self.errors.append('bounded artifact capture: ' + str(error))
        self.result['commandAndCaptureSucceeded'] = bool(self.result['testCommandSucceeded'] and self.result.get('resultEvidencePreserved')
            and self.result.get('compilationEvidencePreserved')
            and self.result.get('completeBundleRetained') and self.result.get('ownedDeviceAbsent')
            and self.result.get('deviceDisposition') == 'deleted' and self.result.get('scratchRemoved')
            and self.result.get('sourceBeforeVerified') and self.result.get('sourceAfterVerified')
            and self.result['normalOwnedCompletion'] and self.result['logsWithinCap'] and not self.owner.CANCELLED
            and not self.errors and time.monotonic() < self.end)
        self.result['status'] = 'RESULT_REVIEW_REQUIRED' if self.result['commandAndCaptureSucceeded'] else 'FAILED'
        self.save('result.json', self.result)
        if (self.run / 'upload').is_dir():
            self.owner.save(self.run / 'upload/result.json', self.result)


def native(request):
    require(os.uname().sysname == 'Darwin' and os.uname().machine == 'arm64' and os.getuid() > 0, 'Standard hosted macOS ARM required')
    workspace, temporary = Path(os.environ['GITHUB_WORKSPACE']).resolve(), Path(os.environ['RUNNER_TEMP']).resolve()
    source, run = workspace / 'app44-source', Path(os.environ['APP44_RUN'])
    require(CONTROL == workspace / 'control' and source.is_dir() and source.resolve() == source, 'Wrong checkout paths')
    require(run == temporary / ('app44-reader-controls-' + os.environ['GITHUB_RUN_ID'] + '-1') and run.resolve() == run
            and not run.exists() and not run.is_symlink(), 'Fresh exact owned run root required')
    spec = importlib.util.spec_from_file_location('app44_existing_darwin_owner', CONTROL / 'ci/app8-apple.py')
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)  # Definitions only; never App8 main, PF, fixtures or probes.
    os.umask(0o077)
    run.mkdir(mode=0o700)
    for name in ('work', 'tmp', 'reports'):
        (run / name).mkdir(mode=0o700)
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, owner.interrupted)
    leaf = Leaf(owner, source, run, request)
    try:
        owner.deadline_capabilities()
        leaf.commands = owner.Commands(run, leaf.env, leaf.end)
        leaf.tools_and_project()
        leaf.prepare_device()
        require(not leaf.bundle.exists() and not leaf.bundle.is_symlink(), 'Preexisting XCTest result')
        leaf.result['testAttempted'] = True
        leaf.save('result.json', leaf.result)
        leaf.call(leaf.test_argv(), 'xcodebuild-test', seconds=720)
        leaf.result['testCommandSucceeded'] = True
    except Exception as error:
        leaf.errors.append('validation: ' + str(error))
    finally:
        leaf.finish()
    print('APP44 APPLE ' + leaf.result['status'] + '; native-test acceptance requires explicit primary schema/result adjudication')
    return 0 if leaf.result['status'] == 'RESULT_REVIEW_REQUIRED' else 1


def main():
    require(sys.argv[1:] in (['request'], ['native']), 'Expected one fixed phase')
    request = checked_request()
    if sys.argv[1] == 'request':
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as stream:
            stream.write('source_sha=' + request['sourceSha'] + '\n')
        return 0
    return native(request)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('APP44 APPLE INCOMPLETE: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
