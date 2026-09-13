"""UNBOUND App65 recipe: real project generation, isolated unsigned resource probe only."""
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
OWNER = '9f69c87182eba29030fcd65c49b4e8459a41749440dab9767f3fbfe0c02db6cf'
INPUTS = '007db9f9b4fe744309584af66c0cb160e580b8d7967a2a1a041b81cd9b9f04c3'
CORRECTION = '8fee4602c1ae9bbbe2a34493b7d2d7bc725a55097d902a1af8066edc29005271'
XCODE = '/Applications/Xcode_26.4.1.app/Contents/Developer'
XCODEGEN = '8774da746668bc18fe74e54cbaf10f2631a1fb05947cd374179aa912f14f99db'
XCODEGEN_RELATIVE = 'xcodegen.artifactbundle/xcodegen-2.46.0-macosx/bin/xcodegen'
REXML_GEM = '19e0a2c3425dfbf2d4fc1189747bdb2f849b6c5e74180401b15734bc97b5d142'
TARGET = 'App65NoticeProbe'
RESOURCE = 'iosApp/iosApp/Settings.bundle'
LOCALES = ('en', 'ar', 'de', 'es', 'fr', 'id', 'in', 'it', 'ja', 'pt', 'ru', 'tr')
RESOURCES = ('Root.plist', 'Acknowledgements.plist', *(x + '.lproj/Root.strings' for x in LOCALES))


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular input: ' + str(path))
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    return value.hexdigest()


def read_json(path, limit=131072):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit, 'Invalid/oversized JSON')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def checked_request():
    request = read_json(CONTROL / 'ci/app65-apple.request.json')
    fixed = {'schema': 'app65-apple-resources-v1', 'authorization': 'APP65_APPLE01_ONE_ATTEMPT_AUTHORIZED',
             'sourceRepository': 'kira-manga/kira-app', 'expectedRunAttempt': 1,
             'sourceCorrectionReviewSha256': CORRECTION, 'sourcePinsSha256': INPUTS,
             'ownerSha256': OWNER, 'developerDir': XCODE, 'xcodegenSha256': XCODEGEN,
             'rexmlGemSha256': REXML_GEM}
    variable = {'sourceSha', 'sourceTree', 'controllerSha256', 'proofSha256', 'prerequisitesSha256', 'workflowSha256',
                'independentToolingReviewSha256', 'toolPrerequisitesReviewSha256'}
    require(isinstance(request, dict) and set(request) == set(fixed) | variable, 'Unexpected request shape')
    require(type(request['expectedRunAttempt']) is int and all(request[k] == v for k, v in fixed.items()),
            'UNBOUND/unapproved or changed request')
    for key in variable:
        size = 40 if key in ('sourceSha', 'sourceTree') else 64
        require(isinstance(request[key], str) and re.fullmatch('[0-9a-f]{' + str(size) + '}', request[key])
                and request[key] != '0' * size, 'Unbound ' + key)
    context = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'kira-manga/kira-admin',
               'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF': 'refs/heads/remediation/app-29-backend-complaints',
               'GITHUB_RUN_ATTEMPT': '1', 'RUNNER_OS': 'macOS', 'RUNNER_ARCH': 'ARM64',
               'RUNNER_ENVIRONMENT': 'github-hosted', 'ImageOS': 'macos26'}
    require(all(os.environ.get(k) == v for k, v in context.items()), 'Wrong private hosted context')
    require(re.fullmatch('[1-9][0-9]*', os.environ.get('GITHUB_RUN_ID', ''))
            and re.fullmatch('[0-9a-f]{40}', os.environ.get('GITHUB_SHA', '')), 'Invalid run/carrier identity')
    require(read_json(Path(os.environ['GITHUB_EVENT_PATH']))['repository']['private'] is True, 'Not private')
    paths = {'controllerSha256': 'ci/app65-apple.py', 'proofSha256': 'ci/app65-apple-proof.rb',
             'prerequisitesSha256': 'ci/app65-apple-prerequisites.py',
             'workflowSha256': '.github/workflows/app65-apple.yml', 'sourcePinsSha256': 'ci/app65-apple.source-pins.json',
             'ownerSha256': 'ci/app8-apple.py'}
    require(all(digest(CONTROL / p) == request[k] for k, p in paths.items()), 'Changed admitted tooling')
    return request


def resource_projection(document, project, target_name, expected, probe=False):
    """Resolve real generated PBX membership; never infer it from YAML text/comments."""
    objects = document['objects']
    root = objects[document['rootObject']]
    require(root['isa'] == 'PBXProject', 'Not a generated PBX project')
    candidates = [objects[x] for x in root['targets'] if objects[x].get('name') == target_name]
    require(len(candidates) == 1 and candidates[0]['productType'] == 'com.apple.product-type.application',
            'Wrong generated application target')
    target = candidates[0]
    parents = {}
    for key, obj in objects.items():
        if obj['isa'] in ('PBXGroup', 'PBXVariantGroup'):
            for child in obj.get('children', []):
                parents.setdefault(child, []).append(key)
    def resolve(key, seen=()):
        require(key not in seen and len(seen) < 32, 'Cyclic/deep PBX group path')
        obj = objects[key]
        tree, path = obj.get('sourceTree', '<group>'), Path(obj.get('path', ''))
        if tree == '<absolute>':
            require(path.is_absolute(), 'Relative absolute PBX path')
            return path.resolve()
        if tree == 'SOURCE_ROOT' or key == root['mainGroup']:
            return (project.parent / path).resolve()
        require(tree == '<group>' and len(parents.get(key, [])) == 1, 'Unsupported/ambiguous PBX path')
        return (resolve(parents[key][0], (*seen, key)) / path).resolve()
    bundle_refs = []
    for key, obj in objects.items():
        if obj['isa'] == 'PBXFileReference' and obj.get('sourceTree') != 'BUILT_PRODUCTS_DIR':
            if obj.get('sourceTree', '<group>') not in ('<group>', 'SOURCE_ROOT', '<absolute>'):
                require('Settings.bundle' not in obj.get('path', ''), 'Settings uses an unexpected source tree')
                continue  # Unrelated SDKROOT references cannot resolve to this checkout's bundle.
            path = resolve(key)
            if path == expected or expected in path.parents:
                require(path == expected, 'Flattened Settings child in generated project')
                bundle_refs.append(key)
    require(len(bundle_refs) == 1, 'Missing/duplicate whole-bundle PBX reference')
    hits = []
    for phase_id in target['buildPhases']:
        phase = objects[phase_id]
        for build_id in phase.get('files', []):
            build = objects[build_id]
            if build.get('fileRef') == bundle_refs[0]:
                hits.append((phase_id, phase, build_id, build))
    require(len(hits) == 1 and hits[0][1]['isa'] == 'PBXResourcesBuildPhase',
            'Settings must occur once in the actual Copy Bundle Resources phase')
    ref = objects[bundle_refs[0]]
    file_type = ref.get('explicitFileType', ref.get('lastKnownFileType', ''))
    require(file_type.startswith('wrapper.'), 'Settings reference is not an intact wrapper')
    if probe:
        require(not root.get('packageReferences') and not target.get('dependencies')
                and not target.get('packageProductDependencies'), 'Unexpected probe dependency/package')
        require(all(objects[x]['isa'] != 'PBXShellScriptBuildPhase' for x in target['buildPhases']), 'Probe has a script')
        resource_phases = [objects[x] for x in target['buildPhases'] if objects[x]['isa'] == 'PBXResourcesBuildPhase']
        require(len(resource_phases) == 1 and resource_phases[0]['files'] == [hits[0][2]], 'Extra probe resource')
    return {'resolvedPath': str(expected), 'fileType': file_type, 'buildSettings': hits[0][3].get('settings', {}),
            'fileReference': bundle_refs[0], 'resourcePhase': hits[0][0], 'buildFile': hits[0][2]}


class Recipe:
    def __init__(self, owner, source, run, tools, request, intake):
        self.owner, self.source, self.run, self.tools, self.request = owner, source, run, tools, request
        self.end = time.monotonic() + 720
        self.work_end = self.end - 120
        self.reports, self.work = run / 'reports', run / 'work'
        self.project = source / 'iosApp/iosApp.xcodeproj'
        self.project_intended, self.source_ready, self.commands = False, False, None
        self.errors = []
        self.result = {'status': 'INCOMPLETE', 'accepted': False, 'sourceSha': request['sourceSha'],
                       'sourceTree': request['sourceTree'], 'carrierSha': os.environ['GITHUB_SHA'],
                       'scope': 'ISOLATED_UNSIGNED_RESOURCE_PROBE_NOT_SHIPPING_APP_ARCHIVE_IPA', 'errors': self.errors,
                       'workSeconds': 600, 'cleanupReserveSeconds': 120, 'globalServicesRestored': False}
        self.pins = read_json(CONTROL / 'ci/app65-apple.source-pins.json')['files']
        self.env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(run / 'home'),
                    'TMPDIR': str(run / 'tmp') + '/', 'DEVELOPER_DIR': XCODE,
                    'GEM_HOME': str(tools / 'gems'), 'GEM_PATH': str(tools / 'gems'),
                    'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'CI': 'true',
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0'}
        self.prerequisites = intake.Prerequisites(self)
        self.save('request.json', request)
        self.save('result.json', self.result)

    def save(self, name, value, limit=131072):
        self.owner.save(self.reports / name, value, limit=limit)

    def call(self, argv, label, seconds=30, cleaning=False, extra=None, end=None):
        limit = self.end if cleaning else self.work_end
        return self.commands.call(argv, label, seconds=seconds, end=limit if end is None else min(limit, end),
                                  cleaning=cleaning, extra=extra)

    def source_receipt(self, after=False):
        git = ['/usr/bin/git', '-C', self.source]
        label = 'source-after' if after else 'source-before'
        identity = self.call(git + ['rev-parse', 'HEAD', 'HEAD^{tree}'], label + '-identity', cleaning=after).splitlines()
        require(identity == [self.request['sourceSha'], self.request['sourceTree']], 'Wrong source commit/tree')
        require(not self.call(git + ['status', '--porcelain', '--untracked-files=all'], label + '-status', cleaning=after),
                'Dirty source checkout')
        observed = {}
        for path, row in self.pins.items():
            file = self.source / path
            require(file.resolve() == file and file.stat().st_size == row['bytes'], 'Changed/linked source input')
            observed[path] = digest(file)
            require(observed[path] == row['sha256'], 'Changed pinned source: ' + path)
        self.save(label + '.json', {'sourceSha': identity[0], 'sourceTree': identity[1], 'inputs': observed})
        self.result[label] = True

    def generated(self, project, label, target, probe=False):
        pbx = project / 'project.pbxproj'
        raw = pbx.read_bytes()
        require(len(raw) <= 2097152 and pbx.resolve() == pbx, 'Invalid generated project')
        (self.reports / (label + '.pbxproj')).write_bytes(raw)
        output = self.reports / (label + '.json')
        self.call(['/usr/bin/plutil', '-convert', 'json', '-o', output, pbx], label + '-apple-decode')
        projection = resource_projection(read_json(output, 2097152), project, target,
                                         (self.source / RESOURCE).resolve(), probe)
        self.save(label + '-resource.json', {'projectSha256': digest(pbx), **projection})
        return projection

    def execute(self):
        self.owner.deadline_capabilities()
        self.commands = self.owner.Commands(self.run, self.env, self.end)
        self.source_receipt()
        require(not self.project.exists() and not self.project.is_symlink(), 'Preexisting generated project')
        require(not (self.source / 'iosApp/iosApp/GoogleService-Info.plist').exists(), 'Unexpected private Firebase input')
        self.source_ready = True
        tools = {'developerDir': XCODE, 'python': sys.version, 'pythonExecutable': sys.executable,
                 'imageVersion': os.environ.get('ImageVersion'),
                 'rubyPath': '/usr/bin/ruby', 'rubySha256': digest(Path('/usr/bin/ruby')),
                 'plutilSha256': digest(Path('/usr/bin/plutil')), 'rexmlGemSha256': REXML_GEM,
                 'toolPrerequisitesReviewSha256': self.request['toolPrerequisitesReviewSha256']}
        self.save('tools.json', tools)
        for key, argv, expected in (
            ('xcode', ['/usr/bin/xcodebuild', '-version'], 'Xcode 26.4.1\nBuild version 17E202'),
            ('sdk', ['/usr/bin/xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], '26.4'),
            ('sdkBuild', ['/usr/bin/xcrun', '--sdk', 'iphonesimulator', '--show-sdk-build-version'], '23E252'),
        ):
            tools[key] = self.call(argv, key + '-version').strip()
            self.save('tools.json', tools)
            require(tools[key] == expected, 'Selected Apple toolchain differs: ' + key)
        # One admitted prerequisite step in this same owned attempt; never use ambient tools.
        xcodegen = self.prerequisites.prepare()
        require(xcodegen == self.tools / XCODEGEN_RELATIVE and xcodegen.resolve() == xcodegen
                and digest(xcodegen) == XCODEGEN, 'Admitted XcodeGen2.46.0 missing/changed')
        require(digest(self.tools / 'gems/cache/rexml-3.4.4.gem') == REXML_GEM, 'Admitted locked REXML package missing/changed')
        tools.update(xcodegenSha256=digest(xcodegen), rexmlInstalledReceiptSha256=self.prerequisites.rexml_sha)
        self.result['prerequisitesReady'] = True
        user_output = self.call(['/usr/bin/id', '-un'], 'generator-user')
        user = user_output.removesuffix('\n')
        require(user_output == user + '\n' and re.fullmatch('[A-Za-z_][A-Za-z0-9_.-]{0,63}', user)
                and os.getuid() == os.geteuid() == self.commands.owner['realUid'] > 0, 'Generator identity mismatch')
        tools['generatorUser'] = user
        tools['xcodegenVersion'] = self.call([xcodegen, '--version'], 'xcodegen-version', extra={'USER': user}).strip()
        require(re.search(r'(?<![\w.])2\.46\.0(?![\w.])', tools['xcodegenVersion']), 'Wrong XcodeGen version')
        self.save('tools.json', tools)
        proof = CONTROL / 'ci/app65-apple-proof.rb'
        rexml_binding = [self.tools, self.reports / 'rexml-installed.json', self.prerequisites.rexml_sha]
        self.call(['/usr/bin/ruby', proof, 'source', self.source, *rexml_binding,
                   self.reports / 'source-notices.json'], 'source-notices')
        self.prerequisites.reconcile_runtime(read_json(self.reports / 'source-notices.json'))
        self.project_intended = True
        self.call([xcodegen, 'generate', '--spec', self.source / 'iosApp/project.yml', '--project', self.source / 'iosApp'],
                  'generate-real-project', seconds=60, extra={'USER': user})
        actual = self.generated(self.project, 'real-project', 'iosApp')
        probe = self.work / 'probe'
        probe.mkdir(mode=0o700)
        (probe / 'main.c').write_text('int main(void) { return 0; }\n')
        spec = {'name': TARGET, 'options': {'deploymentTarget': {'iOS': '15.0'}}, 'targets': {
            TARGET: {'type': 'application', 'platform': 'iOS', 'sources': [
                {'path': 'main.c', 'buildPhase': 'sources'},
                {'path': actual['resolvedPath'], 'type': 'file', 'buildPhase': 'resources'}],
                'settings': {'base': {'PRODUCT_BUNDLE_IDENTIFIER': 'local.validation.app65.notices',
                                     'PRODUCT_NAME': TARGET, 'GENERATE_INFOPLIST_FILE': 'YES',
                                     'TARGETED_DEVICE_FAMILY': '1,2', 'CODE_SIGNING_ALLOWED': 'NO',
                                     'CODE_SIGNING_REQUIRED': 'NO', 'DEBUG_INFORMATION_FORMAT': 'dwarf'}}}},
            'schemes': {TARGET: {'build': {'targets': {TARGET: 'all'}}}}}
        # JSON is a YAML subset; no new YAML parser/dependency is used by this controller.
        (probe / 'project.yml').write_text(json.dumps(spec, indent=2) + '\n')
        self.save('probe-spec.json', spec)
        self.call([xcodegen, 'generate', '--spec', probe / 'project.yml', '--project', probe],
                  'generate-resource-probe', seconds=60, extra={'USER': user})
        projected = self.generated(probe / (TARGET + '.xcodeproj'), 'probe-project', TARGET, probe=True)
        require(all(projected[k] == actual[k] for k in ('resolvedPath', 'fileType', 'buildSettings')),
                'Probe did not preserve the real resolved resource projection')
        require(digest(xcodegen) == XCODEGEN, 'Generator bytes changed')
        derived = self.work / 'DerivedData'
        log = self.call(['/usr/bin/xcodebuild', '-project', probe / (TARGET + '.xcodeproj'), '-scheme', TARGET,
                         '-configuration', 'Debug', '-sdk', 'iphonesimulator', '-destination', 'generic/platform=iOS Simulator',
                         '-derivedDataPath', derived, '-jobs', '1', '-disableAutomaticPackageResolution', '-skipPackageUpdates',
                         'build', 'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=YES', 'CODE_SIGNING_ALLOWED=NO',
                         'CODE_SIGNING_REQUIRED=NO', 'CODE_SIGN_IDENTITY=', 'COMPILER_INDEX_STORE_ENABLE=NO'],
                        'build-resource-probe', seconds=240)
        app = derived / ('Build/Products/Debug-iphonesimulator/' + TARGET + '.app')
        copied = app / 'Settings.bundle'
        copy_lines = [line for line in log.splitlines() if line.startswith('CpResource ')
                      and str(copied) in line and actual['resolvedPath'] in line]
        require(len(copy_lines) == 1 and '** BUILD SUCCEEDED **' in log, 'Missing actual normal Copy Resources action')
        require(app.resolve() == app and app.is_dir() and not (app / '_CodeSignature').exists(), 'Not an unsigned fresh probe app')
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        require(info['CFBundleIdentifier'] == 'local.validation.app65.notices'
                and info['CFBundleSupportedPlatforms'] == ['iPhoneSimulator'], 'Wrong probe identity/platform')
        binary_app = self.work / 'BinaryNoticeProbe.app'
        # Only the fixed fourteen small files, never an unbounded app/directory copy.
        for relative in RESOURCES:
            built = copied / relative
            require(built.resolve() == built and built.is_file() and 0 < built.stat().st_size <= 32768,
                    'Invalid built Settings resource')
            destination = binary_app / 'Settings.bundle' / relative
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            destination.write_bytes(built.read_bytes())
        paths = [binary_app / 'Settings.bundle' / name for name in RESOURCES]
        self.call(['/usr/bin/plutil', '-convert', 'binary1', *paths], 'apple-binary-conversion')
        for relative, path in zip(RESOURCES, paths):
            original = self.source / RESOURCE / relative
            built = copied / relative
            require(path.read_bytes().startswith(b'bplist00'), 'Apple binary conversion not actually observed')
            require(plistlib.loads(original.read_bytes()) == plistlib.loads(built.read_bytes()) == plistlib.loads(path.read_bytes()),
                    'Independent source/built/Apple-binary value mismatch: ' + relative)
        self.call(['/usr/bin/ruby', proof, 'artifacts', self.source, *rexml_binding, app, binary_app,
                   self.reports / 'artifact-notices.json'], 'production-reader-artifacts', seconds=60)
        receipt = read_json(self.reports / 'artifact-notices.json')
        self.prerequisites.reconcile_runtime(receipt)
        # Keep only the actual small resource bytes; never the built executable/application/archive.
        for label, key, bundle in (('built-resources', 'built_app_as_packaged', copied),
                                   ('binary-resources', 'apple_binary_roundtrip_copy', binary_app / 'Settings.bundle')):
            for relative in RESOURCES:
                data = (bundle / relative).read_bytes()
                require(0 < len(data) <= 32768, 'Unbounded resource capture')
                expected = receipt['bundles'][key]['resources'][relative]
                require(len(data) == expected['bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256'],
                        'Validated resource changed before capture')
                destination = self.reports / label / relative
                destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                destination.write_bytes(data)
        self.save('build-resource-witness.json', {'isolatedProbe': True, 'notShippingApp': True,
                  'copyResourcesLines': copy_lines, 'appPath': str(app), 'info': info,
                  'executableSha256': digest(app / TARGET), 'infoSha256': digest(app / 'Info.plist'),
                  'sourceBundle': actual['resolvedPath'], 'resourceCount': len(RESOURCES), 'binaryPlistCount': len(paths)})
        self.save('rexml-after.json', {'installedReceiptSha256': self.prerequisites.rexml_sha,
                  'gemspecSha256': self.prerequisites.verify_rexml(self.work_end), 'allPackageFilesStillMatch': True})
        self.result['resourceProofComplete'] = True

    def finish(self):
        scoped_quiet = False
        try:
            if self.commands is not None:
                require(self.commands.drain(), 'Immediate command settlement failed')
                if self.source_ready:
                    try:
                        self.source_receipt(after=True)
                    except Exception as error:
                        self.errors.append('source-after: ' + str(error))
                observation = self.commands.observe(cleaning=True, full=True)
                markers = (str(self.run) + '/', str(self.source) + '/', str(self.tools) + '/')
                remaining = [row for row in observation['rows'] if row['pid'] != os.getpid()
                             and not row['state'].startswith('Z') and any(x in row['command'] for x in markers)]
                settled = self.commands.drain(observation)
                self.commands.fresh(observation)
                self.save('owned-absence.json', {'groupsSettled': settled, 'scopedWorkersAbsent': not remaining,
                          'workers': [{k: v for k, v in row.items() if k != 'command'} for row in remaining]})
                require(settled and not remaining, 'Unsettled owned workers; retain scratch')
                scoped_quiet = True
            require(not self.project_intended or self.project.resolve() == self.project, 'Unsafe generated project cleanup')
            if self.project_intended and self.project.exists():
                shutil.rmtree(self.project)
            require(not self.project_intended or (not self.project.exists() and not self.project.is_symlink()),
                    'Generated project remains')
            for name in ('work', 'home', 'tmp'):
                path = self.run / name
                require(path.resolve() == path and path.is_dir(), 'Unsafe owned scratch')
                shutil.rmtree(path)
            self.result['scratchRemoved'] = True
        except Exception as error:
            self.errors.append('cleanup: ' + str(error))
            if self.commands is not None:
                for action in (self.commands.retire_observer, self.commands.checkpoint):
                    try:
                        action()
                    except Exception as nested:
                        self.errors.append('owner retirement: ' + str(nested))
        # Independently attempted even if project/run-scratch removal failed. No new census,
        # child, broad fallback or deletion when the one final owned barrier was inconclusive.
        try:
            self.result['prerequisitesRemoved'] = self.prerequisites.cleanup(scoped_quiet)
        except Exception as error:
            self.errors.append('prerequisite cleanup: ' + str(error))
        self.result['normalOwnedCompletion'] = bool(self.commands and self.commands.normal())
        self.result['cancelled'] = self.owner.CANCELLED
        upload = self.run / 'upload'
        upload.mkdir(mode=0o700)
        self.owner.save(upload / 'result.json', self.result)
        try:
            remaining_bytes = 8 * 1048576 - 131072
            files = sorted(p for p in self.reports.rglob('*') if p.is_file() or p.is_symlink())
            require(len(files) <= 128, 'Too many retained evidence files')
            for path in files:
                if path.name == 'result.json':
                    continue
                require(path.resolve() == path and path.suffix in ('.json', '.log', '.pbxproj', '.plist', '.strings'),
                        'Unexpected evidence entry')
                require(time.monotonic() < self.end, 'Evidence retention exceeded deadline')
                limit = min(1048576 if path.suffix == '.log' else 2097152, remaining_bytes)
                with path.open('rb') as stream:
                    data = stream.read(limit + 1)
                require(len(data) <= limit, 'Evidence retention cap exceeded')
                target = upload / path.relative_to(self.reports)
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(data)
                remaining_bytes -= len(data)
        except Exception as error:
            self.errors.append('bounded retention: ' + str(error))
        complete = (self.result.get('resourceProofComplete') and self.result.get('source-after')
                    and self.result.get('prerequisitesReady') and self.result.get('prerequisitesRemoved')
                    and self.result.get('scratchRemoved') and self.result['normalOwnedCompletion']
                    and not self.errors and not self.owner.CANCELLED and time.monotonic() < self.end)
        self.result['status'] = 'RESULT_REVIEW_REQUIRED' if complete else 'FAILED'
        self.save('result.json', self.result)
        self.owner.save(upload / 'result.json', self.result)
        return 0 if complete else 1


def main():
    require(sys.argv[1:] in (['request'], ['run']), 'Expected request or run')
    request = checked_request()  # Refuses UNBOUND before owner import, scratch or any child launch.
    if sys.argv[1] == 'request':
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as stream:
            stream.write('source_sha=' + request['sourceSha'] + '\n')
        return 0
    require(os.uname().sysname == 'Darwin' and os.uname().machine == 'arm64' and Path(XCODE).is_dir(), 'Wrong/missing Apple host')
    workspace, temporary = Path(os.environ['GITHUB_WORKSPACE']).resolve(), Path(os.environ['RUNNER_TEMP']).resolve()
    source, run, tools = workspace / 'app65-source', Path(os.environ['APP65_RUN']), Path(os.environ['APP65_TOOLS'])
    suffix = os.environ['GITHUB_RUN_ID'] + '-1'
    require(CONTROL == workspace / 'control' and source.resolve() == source and source.is_dir(), 'Wrong checkout paths')
    require(run == temporary / ('app65-apple-' + suffix) and run.resolve() == run and not run.exists()
            and not run.is_symlink() and not any(c.isspace() for c in str(run)), 'Unsafe/nonfresh run root')
    require(tools == temporary / ('app65-apple-prerequisites-' + suffix) and tools.resolve() == tools
            and not tools.exists() and not tools.is_symlink(), 'Prerequisite tools root must be fresh/absent')
    spec = importlib.util.spec_from_file_location('app65_reviewed_owner', CONTROL / 'ci/app8-apple.py')
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)  # Definitions only; App8 main/PF/Simulator recipe is never called.
    intake_spec = importlib.util.spec_from_file_location('app65_admitted_prerequisites', CONTROL / 'ci/app65-apple-prerequisites.py')
    intake = importlib.util.module_from_spec(intake_spec)
    intake_spec.loader.exec_module(intake)  # Definitions only, after the exact request/hash gate.
    os.umask(0o077)
    run.mkdir(mode=0o700)
    for name in ('work', 'home', 'tmp', 'reports'):
        (run / name).mkdir(mode=0o700)
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, owner.interrupted)
    recipe = Recipe(owner, source, run, tools, request, intake)
    try:
        recipe.execute()
    except Exception as error:
        recipe.errors.append('validation: ' + str(error))
    return recipe.finish()


if __name__ == '__main__':
    sys.exit(main())
