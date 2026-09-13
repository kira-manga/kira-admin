"""App65 fixed inputs only; all children/lifecycle barriers belong to existing Commands.

Definitions only. No CLI, ambient-tool selection, independent owner or retry path.
"""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import time
import zipfile

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
REXML = {'name': 'rexml', 'version': '3.4.4', 'url': 'https://rubygems.org/downloads/rexml-3.4.4.gem',
         'bytes': 105984, 'sha256': '19e0a2c3425dfbf2d4fc1189747bdb2f849b6c5e74180401b15734bc97b5d142'}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read_json(path, limit=262144):
    require(path.resolve() == path and path.is_file() and path.stat().st_size <= limit, 'Invalid prerequisite JSON')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise RuntimeError('Non-finite JSON')
    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=constant)


class Prerequisites:
    def __init__(self, recipe):
        self.recipe, self.owner, self.root = recipe, recipe.owner, recipe.tools
        self.call, self.save = recipe.call, recipe.save
        self.identity, self.rexml, self.rexml_sha = None, None, None
        self.created = False
        self.work_end = recipe.work_end
        self.receipt = {'status': 'NOT_STARTED', 'toolsRoot': str(self.root), 'secondsCap': 180,
                        'xcodegen': {'status': 'NOT_REACHED'}, 'rexml': {'status': 'NOT_REACHED'}}

    # Fixed App44 intake; only the destination/receipt seam differs. No select_xcodegen/main.
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

    def intake_xcodegen(self, prerequisites):
        end = min(self.work_end, time.monotonic() + 30)
        receipt = {'status': 'STARTED', 'stage': 'curl-identity', 'pin': XCODEGEN, 'curlPath': '/usr/bin/curl', 'secondsCap': 30,
                   'expandedBytesCap': 33554432, 'entryCap': 64, 'retryCount': 0}
        prerequisites['xcodegen'] = receipt
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
            root = self.root  # Already exclusively created by this prerequisite step.
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
            info = read_json(root / 'xcodegen.artifactbundle/info.json', 65536)
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

    def package_inventory(self, data, end):
        """Read, never extract/execute, data.tar.gz from the already byte-verified gem."""
        outer = {}
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as package:
            for member in package:
                require(not self.owner.CANCELLED and time.monotonic() < end, 'REXML package read expired')
                require(member.name in ('metadata.gz', 'data.tar.gz', 'checksums.yaml.gz')
                        and member.name not in outer and member.isreg() and not member.issparse()
                        and not member.pax_headers and 0 < member.size <= REXML['bytes'], 'Unexpected gem envelope')
                with package.extractfile(member) as stream:
                    outer[member.name] = stream.read(member.size + 1)
                require(len(outer[member.name]) == member.size, 'Changed gem member size')
        require(set(outer) == {'metadata.gz', 'data.tar.gz', 'checksums.yaml.gz'}, 'Incomplete gem envelope')
        with gzip.GzipFile(fileobj=io.BytesIO(outer['data.tar.gz'])) as stream:
            payload = stream.read(8388608 + 1)
        require(len(payload) <= 8388608 and time.monotonic() < end, 'Oversized/late gem payload')
        files, directories, names, total = {}, set(), set(), 0
        with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
            for member in archive:
                require(not self.owner.CANCELLED and time.monotonic() < end, 'REXML payload read expired')
                path = PurePosixPath(member.name)
                require(0 < len(member.name) <= 240 and not path.is_absolute() and '..' not in path.parts
                        and '\\' not in member.name and '\x00' not in member.name
                        and str(path) == member.name.rstrip('/') and str(path) not in ('', '.')
                        and member.name not in names and len(names) < 512 and not member.pax_headers
                        and member.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
                        and not member.issparse() and not member.mode & 0o7000
                        and 0 <= member.size <= 1048576, 'Unsafe/oversized REXML member')
                names.add(member.name)
                directories.update(str(parent) for parent in path.parents if str(parent) != '.')
                if member.isdir():
                    require(member.size == 0, 'Nonempty REXML directory')
                    directories.add(str(path))
                else:
                    with archive.extractfile(member) as stream:
                        content = stream.read(member.size + 1)
                    require(len(content) == member.size, 'Changed REXML content size')
                    total += len(content)
                    require(total <= 8388608 and str(path) not in files, 'Duplicate/oversized REXML payload')
                    files[str(path)] = {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
        require(files and 'lib/rexml/document.rb' in files and not set(files) & directories,
                'Incomplete/colliding REXML payload')
        return {'packageFiles': files, 'packageDirectories': sorted(directories), 'packageFileBytes': total,
                'dataTarSha256': hashlib.sha256(payload).hexdigest()}

    def tree(self, root, end, cleaning=False):
        """Bounded private-file inventory, not a subprocess ownership implementation."""
        require(root.resolve() == root and root.is_dir(), 'Unsafe tools inventory root')
        rows, pending, total = [], [root], 0
        while pending:
            require((cleaning or not self.owner.CANCELLED) and time.monotonic() < end, 'Tools inventory expired')
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    require((cleaning or not self.owner.CANCELLED) and time.monotonic() < end
                            and len(rows) < 2048, 'Tools tree expired/over entry cap')
                    path, info = Path(entry.path), entry.stat(follow_symlinks=False)
                    require(path.resolve() == path and info.st_uid == os.geteuid()
                            and info.st_dev == self.identity[0] and len(path.relative_to(root).parts) <= 16
                            and (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)), 'Unsafe tools tree entry')
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(path)
                    else:
                        total += info.st_size
                        require(info.st_nlink == 1 and 0 <= info.st_size <= 33554432 and total <= 67108864,
                                'Linked/oversized tools tree file')
                    rows.append((path, info))
        return rows

    def verify_rexml(self, end):
        expected = self.rexml
        gem_root = Path(expected['rexmlRoot'])
        rows = self.tree(self.root / 'gems', end)
        files = {str(path.relative_to(self.root / 'gems')) for path, info in rows if stat.S_ISREG(info.st_mode)}
        require(files == {'gems/rexml-3.4.4/' + name for name in expected['packageFiles']} |
                {'cache/rexml-3.4.4.gem', 'specifications/rexml-3.4.4.gemspec'}, 'Extra/missing installed gem files')
        directories = {str(path.relative_to(gem_root)) for path, info in rows
                       if path != gem_root and path.is_relative_to(gem_root) and stat.S_ISDIR(info.st_mode)}
        require(directories == set(expected['packageDirectories']) and not self.tree(self.root / 'bin', end),
                'Changed REXML directory set or unexpected executable')
        for name, row in expected['packageFiles'].items():
            data = self.xcodegen_bytes(gem_root / name, 1048576, end)
            require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'],
                    'Installed REXML differs from verified package: ' + name)
        cache = self.xcodegen_bytes(self.root / 'gems/cache/rexml-3.4.4.gem', REXML['bytes'], end)
        require(len(cache) == REXML['bytes'] and hashlib.sha256(cache).hexdigest() == REXML['sha256'], 'Wrong cached REXML')
        spec = self.xcodegen_bytes(self.root / 'gems/specifications/rexml-3.4.4.gemspec', 1048576, end)
        spec_sha = hashlib.sha256(spec).hexdigest()
        require(expected.get('gemspecSha256', spec_sha) == spec_sha, 'Installed gemspec changed')
        return spec_sha

    def intake_rexml(self):
        end = min(self.work_end, time.monotonic() + 30)
        receipt = self.receipt['rexml']
        receipt.update(status='STARTED', stage='download', pin=REXML, acquisitionSecondsCap=30, installSecondsCap=90)
        self.save('prerequisites.json', self.receipt)
        try:
            lock = self.xcodegen_bytes(self.recipe.source / 'Gemfile.lock', 65536, end)
            require(('  rexml (3.4.4) sha256=' + REXML['sha256']).encode() in lock.splitlines(), 'Lock pin differs')
            downloads = self.root / 'downloads'
            downloads.mkdir(mode=0o700)
            archive = downloads / 'rexml-3.4.4.gem'
            # Reuse the already admitted system curl and its 8.4+ streaming cap.
            curl = Path('/usr/bin/curl')
            require(hashlib.sha256(self.xcodegen_bytes(curl, 33554432, end)).hexdigest() ==
                    self.receipt['xcodegen']['curlSha256'], 'System curl changed')
            downloaded = self.call([curl, '-q', '--proto', '=https', '--proto-redir', '=https', '--tlsv1.2',
                '--connect-timeout', '5', '--max-time', '30', '--max-filesize', str(REXML['bytes']),
                '--max-redirs', '3', '--retry', '0', '--fail', '--silent', '--show-error', '--location',
                '--output', archive, '--write-out', '%{http_code} %{size_download}\n', REXML['url']],
                'rexml-download', end=end).strip()
            require(downloaded == '200 ' + str(REXML['bytes']), 'Unexpected REXML HTTP/byte receipt')
            receipt.update(stage='package-attribution', downloadOutput=downloaded)
            self.save('prerequisites.json', self.receipt)
            data = self.xcodegen_bytes(archive, REXML['bytes'], end)
            require(len(data) == REXML['bytes'] and hashlib.sha256(data).hexdigest() == REXML['sha256'],
                    'REXML package bytes/hash mismatch before parsing/install')
            self.rexml = {'schema': 'app65-rexml-package-install-v1', 'toolsRoot': str(self.root), 'package': REXML,
                          'rexmlRoot': str(self.root / 'gems/gems/rexml-3.4.4'),
                          'sourceLockSha256': hashlib.sha256(lock).hexdigest(), **self.package_inventory(data, end)}
            (self.root / 'gems').mkdir(mode=0o700)
            (self.root / 'bin').mkdir(mode=0o700)
            gem_script = Path('/usr/bin/gem').resolve(strict=True)  # One system locator, never PATH/gem discovery.
            receipt.update(stage='gemrc-absence', rubySha256=hashlib.sha256(
                self.xcodegen_bytes(Path('/usr/bin/ruby'), 33554432, self.work_end)).hexdigest(),
                gemScriptPath=str(gem_script), gemScriptRequestedPath='/usr/bin/gem',
                gemScriptSha256=hashlib.sha256(self.xcodegen_bytes(gem_script, 1048576, self.work_end)).hexdigest())
            self.save('prerequisites.json', self.receipt)
            # Apple RubyGems 3.0.3.1 reads rc files before --norc suppresses their merge.
            # Metadata only for its two exact paths; do not load RubyGems/configuration here.
            gemrc_paths = self.call(['/usr/bin/ruby', '--disable-gems', '-retc', '-e', """
abort 'Unexpected gemrc environment' if ENV.key?('GEMRC') || Dir.home != ENV.fetch('HOME')
paths = [File.join(Etc.sysconfdir, 'gemrc'), File.join(Dir.home, '.gemrc')]
paths.each do |path|
  begin
    File.lstat(path)
  rescue Errno::ENOENT
    next
  end
  abort "Ambient gemrc must be absent: #{path}"
end
puts paths
"""], 'rexml-gemrc-absence', seconds=10, end=self.work_end).splitlines()
            require(len(gemrc_paths) == 2 and all(len(path) <= 4096 and path.startswith('/') for path in gemrc_paths)
                    and gemrc_paths[1] == str(self.recipe.run / 'home/.gemrc'), 'Unexpected gemrc absence receipt')
            receipt.update(stage='local-install', absentGemrcPaths=gemrc_paths)
            self.save('prerequisites.json', self.receipt)
            self.call(['/usr/bin/ruby', '--disable-gems', gem_script, 'install', '--norc', '--local', archive,
                       '--install-dir', self.root / 'gems', '--bindir', self.root / 'bin', '--no-user-install',
                       '--no-document', '--ignore-dependencies'], 'rexml-local-install', seconds=90, end=self.work_end)
            receipt['stage'] = 'installed-attribution'
            self.save('prerequisites.json', self.receipt)
            self.rexml['gemspecSha256'] = self.verify_rexml(self.work_end)
            self.save('rexml-installed.json', self.rexml, limit=262144)
            self.rexml_sha = hashlib.sha256(self.xcodegen_bytes(self.recipe.reports / 'rexml-installed.json',
                                                             262144, self.work_end)).hexdigest()
            archive.unlink()
            downloads.rmdir()
            receipt.update(status='READY', stage='complete', installedReceiptSha256=self.rexml_sha, downloadRemoved=True)
        except Exception as error:
            receipt.update(status='FAILED', error=str(error))
            raise
        finally:
            self.save('prerequisites.json', self.receipt)

    def prepare(self):
        self.work_end = min(self.work_end, time.monotonic() + 180)
        self.receipt['status'] = 'STARTED'
        self.save('prerequisites.json', self.receipt)
        try:
            require(not self.owner.CANCELLED and time.monotonic() < self.work_end
                    and os.getuid() == os.geteuid() == self.recipe.commands.owner['realUid']
                    == self.recipe.commands.owner['effectiveUid'] > 0, 'Prerequisite owner/cancellation mismatch')
            require(not self.root.exists() and not self.root.is_symlink() and self.root.resolve() == self.root,
                    'Prerequisites require an absent canonical private tools root')
            self.root.mkdir(mode=0o700)
            self.created = True
            info = self.root.lstat()
            self.identity = (info.st_dev, info.st_ino, info.st_uid, info.st_mode)
            require(self.root.resolve() == self.root and stat.S_ISDIR(info.st_mode)
                    and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, 'Nonprivate tools root')
            self.receipt['rootIdentity'] = list(self.identity)
            self.save('prerequisites.json', self.receipt)
            executable = self.intake_xcodegen(self.receipt)
            self.intake_rexml()
            require(not self.owner.CANCELLED and time.monotonic() < self.work_end, 'Prerequisites expired/cancelled')
            self.receipt['status'] = 'READY'
            return executable
        except Exception as error:
            self.receipt.update(status='FAILED', error=str(error))
            raise
        finally:
            self.save('prerequisites.json', self.receipt)

    def reconcile_runtime(self, proof):
        runtime = proof['runtime']
        require(proof['accepted'] is True and proof['isolatedResourceProofOnly'] is True
                and runtime['rexmlVersion'] == REXML['version'] and runtime['rexmlRoot'] == self.rexml['rexmlRoot']
                and runtime['rexmlPackageSha256'] == REXML['sha256'] and runtime['rexmlInstalledReceiptSha256'] == self.rexml_sha
                and runtime['gemspecSha256'] == self.rexml['gemspecSha256'] and runtime['loadedRexmlAfterProof'] is True,
                'Runtime does not match the admitted REXML installation')
        loaded = runtime['loadedRexmlSha256']
        require('lib/rexml/document.rb' in loaded and all(name in self.rexml['packageFiles']
                and sha == self.rexml['packageFiles'][name]['sha256'] for name, sha in loaded.items()),
                'Loaded REXML cannot be attributed to the verified package')

    def cleanup(self, scoped_quiet):
        end = min(self.recipe.end, time.monotonic() + 30)
        receipt = {'status': 'STARTED', 'toolsRoot': str(self.root), 'rootIdentity': self.identity,
                   'created': self.created, 'ownedScopedAbsence': scoped_quiet, 'secondsCap': 30,
                   'entryCap': 2048, 'bytesCap': 67108864, 'removed': False}
        self.save('prerequisites-cleanup.json', receipt)
        try:
            if self.identity is None:
                require(not self.created, 'Retain tools root: created but identity unavailable')
                receipt.update(status='NOT_CREATED', removed=False)
                return False
            require(scoped_quiet, 'Retain prerequisites: final owned absence unproven')
            info = self.root.lstat()
            require(self.root.resolve() == self.root and stat.S_ISDIR(info.st_mode)
                    and (info.st_dev, info.st_ino, info.st_uid, info.st_mode) == self.identity
                    and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, 'Tools ownership changed')
            rows = self.tree(self.root, end, cleaning=True)
            for path, before in sorted(rows, key=lambda row: len(row[0].parts), reverse=True):
                require(time.monotonic() < end and path.resolve() == path, 'Prerequisite cleanup expired/unsafe')
                after = path.lstat()
                require((before.st_dev, before.st_ino, before.st_uid, before.st_mode) ==
                        (after.st_dev, after.st_ino, after.st_uid, after.st_mode), 'Tools entry identity changed')
                if stat.S_ISDIR(after.st_mode):
                    path.rmdir()
                else:
                    require((before.st_size, before.st_mtime_ns, before.st_nlink) ==
                            (after.st_size, after.st_mtime_ns, after.st_nlink), 'Tools file changed during cleanup')
                    path.unlink()
            require(time.monotonic() < end, 'Prerequisite cleanup expired before root removal')
            info = self.root.lstat()
            require((info.st_dev, info.st_ino, info.st_uid, info.st_mode) == self.identity, 'Tools root replaced')
            self.root.rmdir()
            require(not self.root.exists() and not self.root.is_symlink(), 'Prerequisites remain')
            receipt.update(status='REMOVED', removed=True, removedEntries=len(rows) + 1)
            return True
        except Exception as error:
            receipt.update(status='FAILED', error=str(error))
            raise
        finally:
            self.save('prerequisites-cleanup.json', receipt)
