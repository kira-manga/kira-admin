#!/usr/bin/env python3
"""Local02 controller adapted for one exact hosted Linux remaining-phase check."""
import ctypes, hashlib, json, os, pathlib, shutil, signal, subprocess, time

ROOT = pathlib.Path(os.environ['GITHUB_WORKSPACE']).resolve()
WT = ROOT/'source'
OUT = ROOT/'admin-app29-moderation-linux02-evidence'
TEMP = OUT/'scratch'
GENERATED = [WT/'node_modules', WT/'.next', WT/'tsconfig.tsbuildinfo', TEMP]
COMMIT = 'e0901d2f1eb9fe6f8594aa8e880fb584c67e8997'
TREE = 'c011d49a662083b186061b46fb62e1d7c1b7c651'
FLOOR = 8*1024**3
SELF = os.getpid()
owned, roots, records, reaped = {}, [], [], []
before, paths, next_before = {}, [], None
out_owned = outputs_owned = cleaning = stopping = False
result = {'status': 'NOT_STARTED', 'phases': {}, 'cleanup_errors': [],
          'carried_lint': 'local02 PASS for unchanged files; two changed test files linted here'}

class Abort(Exception):
    pass

def interrupted(number, _frame):
    result.setdefault('abort', f'Signal {number}')
    if not cleaning and not stopping:
        raise Abort(result['abort'])

def hashes():
    return {p: hashlib.sha256((WT/p).read_bytes()).hexdigest() for p in paths}

def resources():
    mem = {x.split(':')[0]: int(x.split()[1])*1024
           for x in pathlib.Path('/proc/meminfo').read_text().splitlines()}
    return dict(time=time.time(), available_ram=mem['MemAvailable'], free_disk=shutil.disk_usage(WT).free)

def info(pid):
    try:
        fields = pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, state=fields[0], ppid=int(fields[1]), start=int(fields[19]))
    except (FileNotFoundError, ProcessLookupError):
        return None

def descendants():
    for child in roots:
        child.poll()  # Popen alone owns phase-root exit status.
    snapshot = {}
    for entry in pathlib.Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                value = info(int(entry.name))
                if value:
                    snapshot[value['pid']] = value
            except PermissionError:
                if int(entry.name) in owned:
                    raise
    parents = {SELF} | {pid for pid, start in owned.items()
                        if pid in snapshot and snapshot[pid]['start'] == start}
    while True:
        added = {pid for pid, value in snapshot.items() if pid not in parents and value['ppid'] in parents}
        if not added:
            break
        for pid in added:
            owned[pid] = snapshot[pid]['start']
        parents.update(added)
    root_pids = {child.pid for child in roots}
    for pid, start in list(owned.items()):
        value = info(pid)
        # Reap only actual direct/adopted descendants; never waitpid(-1).
        if value and value['start'] == start and value['ppid'] == SELF and pid not in root_pids:
            try:
                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited:
                    reaped.append(dict(pid=pid, start=start, wait_status=status))
            except ChildProcessError:
                pass
    live = []
    for pid, start in list(owned.items()):
        value = info(pid)
        if value and value['start'] == start:
            live.append(value)
        else:
            del owned[pid]
    return live

def stop():
    global stopping
    previous, stopping = stopping, True
    started, sent = time.monotonic(), set()
    try:
        while True:
            live = descendants()
            if not live or time.monotonic()-started >= 3:
                return live
            number = signal.SIGTERM if time.monotonic()-started < 1 else signal.SIGKILL
            for value in live:
                key = (value['pid'], value['start'], number)
                if value['state'] == 'Z' or key in sent:
                    continue
                try:
                    fd = os.pidfd_open(value['pid'], 0)
                    try:
                        current = info(value['pid'])
                        if current and current['start'] == value['start']:
                            signal.pidfd_send_signal(fd, number, None, 0)
                    finally:
                        os.close(fd)
                except ProcessLookupError:
                    pass
                sent.add(key)
            time.sleep(.05)
    finally:
        stopping = previous

def run(phase, args, deadline):
    sample = resources()
    records.append(sample)
    if sample['available_ram'] <= FLOOR or sample['free_disk'] <= FLOOR or time.monotonic() >= deadline:
        raise Abort('Resource floor or phase deadline')
    with (OUT/f'{phase}.log').open('xb') as log:
        child = subprocess.Popen(['taskset', '-c', cpus, *args], cwd=WT, env=env,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        roots.append(child)
        value = info(child.pid)
        if value:
            owned[child.pid] = value['start']
        try:
            while child.poll() is None:
                time.sleep(5)
                sample = resources()
                records.append(sample)
                descendants()
                if sample['available_ram'] <= FLOOR or sample['free_disk'] <= FLOOR or time.monotonic() >= deadline:
                    raise Abort('Resource floor or phase deadline')
        finally:
            left = stop()
            result['phases'][phase] = child.poll()
            if left:
                result.setdefault('abort', 'Owned descendants remain')
    print(phase, result['phases'][phase], flush=True)
    return result['phases'][phase] == 0 and not result.get('abort')

try:
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_OS') != 'Linux':
        raise Abort('Hosted Linux only; no local repeat')
    if WT.is_symlink() or WT.resolve() != ROOT/'source':
        raise Abort('Unexpected source checkout path')
    OUT.mkdir(mode=0o700)
    out_owned = True
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER before any phase spawn.
        raise Abort('Cannot establish child subreaper')
    if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
        raise Abort('Linux pidfd support required')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD', 'HEAD^{tree}'], cwd=WT).decode().split()
    if os.environ.get('PRIMARY_SOURCE_COMMIT') != COMMIT or actual != [COMMIT, TREE]:
        raise Abort('Exact source commit/tree mismatch')
    result.update(source_commit=COMMIT, source_tree=TREE, controls_commit=os.environ['GITHUB_SHA'])
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=WT):
        raise Abort('Source checkout not clean')
    if any(os.path.lexists(p) for p in GENERATED):
        raise Abort('Refusing existing generated output')
    outputs_owned = True
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=WT).decode().split('\0')
    paths = sorted(p for p in paths if p and (WT/p).is_file())
    before = hashes()
    (OUT/'source-before.json').write_text(json.dumps(before, indent=2)+'\n')
    next_before = (WT/'next-env.d.ts').read_bytes()
    TEMP.mkdir()
    (TEMP/'tmp').mkdir()
    env = os.environ.copy()
    env.update(NODE_OPTIONS='--max-old-space-size=3072', NEXT_TELEMETRY_DISABLED='1',
               npm_config_cache=str(TEMP/'npm-cache'), TMPDIR=str(TEMP/'tmp'), CI='1')
    allowed = sorted(os.sched_getaffinity(0))[:2]
    if len(allowed) != 2:
        raise Abort('Two allowed CPUs required')
    cpus = ','.join(map(str, allowed))
    result['cpu_affinity'] = allowed
    result['status'] = 'RUNNING'
    if run('install', ['npm', 'ci', '--no-audit', '--no-fund'], time.monotonic()+600):
        deadline = time.monotonic()+900
        for phase, args in [('lint', ['node', 'node_modules/eslint/bin/eslint.js', 'src/app/api/backend/[...path]/complaint-detail.test.ts', 'src/app/api/catalog/manifest/route.test.ts']),
                            ('typecheck', ['npm', 'run', 'typecheck']),
                            ('test', ['npm', 'test', '--', '--maxWorkers=2', 'src/app/api/backend/[...path]/complaint-detail.test.ts', 'src/app/api/catalog/manifest/route.test.ts', '--testNamePattern', 'strips upstream read401 challenge|accepts exactly 1 MiB']),
                            ('build', ['npm', 'run', 'build'])]:
            if not run(phase, args, deadline):
                break
except Abort as error:
    result['abort'] = str(error)
except Exception as error:
    result['error_type'] = type(error).__name__
finally:
    cleaning = True
    left = 'UNKNOWN'
    try:
        left = stop()
    except Exception as error:
        result['cleanup_errors'].append('shutdown: '+type(error).__name__)
    result['remaining_owned_processes'] = left
    try:
        if next_before is not None:
            after_next = (WT/'next-env.d.ts').read_bytes()
            if after_next != next_before:
                allowed_next = next_before.replace(b'import "./.next/types/routes.d.ts";',
                    b'import "./.next/types/routes.d.ts";\nimport "./.next/types/root-params.d.ts";')
                if after_next == allowed_next:
                    (WT/'next-env.d.ts').write_bytes(next_before)
                    result['known_generated_next_env_restored'] = True
                else:
                    result['unexpected_next_env_change'] = True
        if before:
            result['source_changes'] = [p for p, h in hashes().items() if before[p] != h]
    except Exception as error:
        result['cleanup_errors'].append('source readback: '+type(error).__name__)
    if outputs_owned and left == []:
        for path in GENERATED:
            try:
                if path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                elif path.exists():
                    path.unlink()
            except Exception as error:
                result['cleanup_errors'].append(path.name+': '+type(error).__name__)
    result['outputs_absent'] = all(not os.path.lexists(p) for p in GENERATED)
    try:
        records.append(resources())
        if before:
            result['final_git_status'] = subprocess.check_output(
                ['git', 'status', '--porcelain', '--untracked-files=all'], cwd=WT).decode()
    except Exception as error:
        result['cleanup_errors'].append('final readback: '+type(error).__name__)
    passed = (result['phases'] == {'install': 0, 'lint': 0, 'typecheck': 0, 'test': 0, 'build': 0}
              and not result.get('abort') and not result.get('error_type') and not result['cleanup_errors']
              and result.get('source_changes') == [] and not result.get('unexpected_next_env_change')
              and result.get('final_git_status') == '' and left == [] and result['outputs_absent'])
    result['status'] = 'PASS' if passed else ('ABORT' if result.get('abort') else 'FAIL')
    result['reaped_adopted_descendants'] = reaped
    if out_owned:
        for log in OUT.glob('*.log'):
            if log.stat().st_size > 4*1024**2:
                with log.open('r+b') as stream:
                    head = stream.read(2*1024**2)
                    stream.seek(-2*1024**2, os.SEEK_END)
                    tail = stream.read()
                    stream.seek(0)
                    stream.write(head+b'\n[controller: middle omitted]\n'+tail)
                    stream.truncate()
                result.setdefault('truncated_logs', []).append(log.name)
        (OUT/'resources.json').write_text(json.dumps(records, indent=2)+'\n')
        (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
raise SystemExit(0 if result['status'] == 'PASS' else 1)
