#!/usr/bin/env python3
"""Verify the private handoff archive; optionally restore without overwriting existing work."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def safe_relative(name):
    path = PurePosixPath(name)
    if (path.is_absolute() or len(path.parts) < 2 or path.parts[0] != 'review'
            or '..' in path.parts or str(path) != name or '\\' in name):
        raise ValueError('Unsafe archive path: ' + name)
    return Path(*path.parts)


def safe_destination(workspace, relative):
    current = workspace
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Refusing existing symlink: ' + str(current))
    return current


def verify_and_restore(workspace, restore):
    manifest_path = HERE / 'review-manifest.json'
    if manifest_path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Unexpected manifest size')
    manifest = json.loads(manifest_path.read_text())
    archive = HERE / 'review-evidence.tar.gz'
    if archive.is_symlink() or digest(archive) != manifest['archive_sha256']:
        raise ValueError('Archive SHA-256 mismatch or symlink')
    rows = manifest['files']
    expected = {row['path']: row for row in rows}
    if len(expected) != len(rows) or len(rows) != manifest['file_count']:
        raise ValueError('Duplicate or inconsistent file inventory')
    if sum(row['size'] for row in rows) != manifest['uncompressed_bytes']:
        raise ValueError('Inconsistent byte inventory')
    for row in rows:
        safe_relative(row['path'])
        if row['size'] < 0 or row['mode'] not in (0o644, 0o755):
            raise ValueError('Invalid file bounds/mode')
    if not workspace.is_dir() or workspace.is_symlink():
        raise ValueError('Workspace must be an existing real directory')
    seen = set()
    # One-file streaming hash; an extraction stage exists only for the explicit --restore action.
    with tempfile.TemporaryDirectory(prefix='.kira-review-restore-', dir=workspace) as temporary:
        stage = Path(temporary)
        with tarfile.open(archive, 'r|gz') as stream:
            for member in stream:
                relative = safe_relative(member.name)
                row = expected.get(member.name)
                if not member.isfile() or row is None or member.name in seen or member.size != row['size']:
                    raise ValueError('Unexpected, duplicate or non-regular archive member: ' + member.name)
                h = hashlib.sha256()
                size = 0
                staged = stage / relative
                if restore:
                    staged.parent.mkdir(parents=True, exist_ok=True)
                output = staged.open('xb') if restore else None
                try:
                    with stream.extractfile(member) as source:
                        for chunk in iter(lambda: source.read(1024 * 1024), b''):
                            size += len(chunk)
                            if size > row['size']:
                                raise ValueError('File exceeds recorded size')
                            h.update(chunk)
                            if output:
                                output.write(chunk)
                finally:
                    if output:
                        output.close()
                if size != row['size'] or h.hexdigest() != row['sha256']:
                    raise ValueError('Member checksum mismatch: ' + member.name)
                if restore:
                    staged.chmod(row['mode'])
                seen.add(member.name)
        if seen != set(expected):
            raise ValueError('Archive omits inventoried files')
        if not restore:
            print('VERIFIED', len(seen), 'files;', manifest['uncompressed_bytes'], 'bytes; no review files written')
            return
        # Check every conflict before creating any review file. Identical existing files are kept.
        for name, row in expected.items():
            target = safe_destination(workspace, safe_relative(name))
            if target.exists() and (not target.is_file() or digest(target) != row['sha256']):
                raise ValueError('Existing work differs; nothing overwritten: ' + name)
        created = 0
        for name, row in expected.items():
            relative = safe_relative(name)
            target = safe_destination(workspace, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            safe_destination(workspace, relative)
            try:
                # Same-filesystem atomic no-clobber creation; no tar extraction/link directives.
                os.link(stage / relative, target, follow_symlinks=False)
                created += 1
            except FileExistsError:
                if target.is_symlink() or not target.is_file() or digest(target) != row['sha256']:
                    raise ValueError('Concurrent conflicting work; never overwritten: ' + name)
        print('RESTORED', created, 'new files; kept', len(expected) - created, 'identical existing files')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verify-only', action='store_true')
    mode.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    verify_and_restore(args.workspace.absolute(), args.restore)


if __name__ == '__main__':
    main()
