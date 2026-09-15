"""PUBLIC SYNTHETIC UNEXECUTED App8 draft. One API26 tiny host; no shipping build.

Imports have no SDK/network/process actions. Reuses the existing reviewed Linux
OwnedChildren unchanged; this file only adapts its finite command/cleanup recipe.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import zipfile

ISSUE = 'd7b024a1c77f434726c64df36e059ea5af55961c'
BASE = '2d6bf4bb9a67773abbf9c6c6bf641ffbd1de670c'
MANIFEST = 'b5f0070646575c99a2f9ef5b46d2550b949c6810459ac7ab7788c29e42baf6b0'
OWNER_HASH = '56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385'
POLICIES = {'allow': '03d8bc818916ef40f4ba440aab50100c170a216acab814957d74fbf41f434b6a',
            'deny': 'dea35ebed76536c24c13f74036f02dc874f944147cb3a49c2ad0550f71e3e0c7'}
INPUTS = ('android/AndroidManifest.xml', 'android/TransportProbe.java', 'fixture/no_forward_proxy.py',
          'policy-inputs/allow/network_security_config.xml', 'policy-inputs/deny/network_security_config.xml',
          'policy-inputs.json', 'provenance.json')
# Historical construction metadata remains bound to the original frozen probe manifest.
BUILD_HASH = 'fb1929a19efcac2e9d843bd3f1946f2573ff486747abf514fcf76f5f80b55889'
APP_MANIFEST_HASH = 'fc86dea1b63549f7df4c0cb289e6be2dd207c1520ed90616b8e251d122da22a9'
GUARD_HASH = 'c33add8f6fc647a9186e5e06affb433a174077601c4fb04c10ca4ef7bc2841a6'
# Current reviewed App8 join: exact source checkpoint, not a shipping-artifact assertion.
CHECKPOINT_BUILD_HASH = '2f5af388a012de3933fe5b3d10bb8071fbc35acd14b3fb83eb8ca8d5dc767cd8'
CHECKPOINT_APP_MANIFEST_HASH = '43219eaa3bbdacd7640209aa675423b0261ff2aabf177ef4ba9cbd0e74869952'
CHECKPOINT_GUARD_HASH = '68a99cbc40fcc5cde08028411c019d8505f350b711282eb5c334f0c1e7efdede'
POLICY_PATH = 'app/src/main/res/xml/network_security_config.xml'
IMAGE = 'system-images;android-26;google_apis;x86_64'
PACKAGE = 'me.manga.kira.transportprobe'
HOSTS = ('raijinscan.co', 'app8-probe.raijinscan.co')
CANCELLED = False


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def interrupted(_number, _frame):
    global CANCELLED
    CANCELLED = True  # Never interrupt Popen construction/registration or finite cleanup.


def digest(path, end=None):
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular bound input: ' + str(path))
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            require(not CANCELLED and (end is None or time.monotonic() < end), 'Cancelled/expired input hashing')
            block = stream.read(1048576)
            if not block:
                return value.hexdigest()
            value.update(block)


def read_json(path):
    require(path.stat().st_size <= 131072, 'Oversized JSON receipt/input')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise RuntimeError('Non-finite JSON input')
    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=constant)


def save(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.write('\n')


def owner_class(path):
    require(digest(path) == OWNER_HASH, 'Unreviewed ownership helper')
    spec = importlib.util.spec_from_file_location('app8_frozen_owned_children', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OwnedChildren


def normal_drain(receipt, joined):
    return (receipt.get('ok') is True and receipt.get('empty') is True
            and all(receipt.get(key) == [] for key in ('term', 'kill', 'remaining', 'active_popen'))
            and receipt.get('errors') == {} and isinstance(receipt.get('adopted'), list)
            and all(row.get('actual_exit') == 0 for row in receipt['adopted'])
            and isinstance(receipt.get('leaders'), list)
            and all(row['pid'] in joined and row['actual_exit'] == joined[row['pid']] for row in receipt['leaders']))


def owned_absence(receipt):
    # Forced/unjoined exits stay abnormal, but cannot keep proved-empty scratch alive.
    return (receipt.get('ok') is True and receipt.get('empty') is True
            and receipt.get('remaining') == [] and receipt.get('active_popen') == []
            and receipt.get('errors') == {})


def scan_timeout_diagnostic(owner, process, end):
    result = {'pid': process.pid, 'capturedMonotonicSeconds': time.monotonic(), 'fields': {}}
    # Fixed fields only; check cleanup priority before each read, with no wait/retry/new deadline.
    # Do not poll/reap here: the owner's unreaped Popen keeps its PID from being reused.
    for name in ('clockTicksPerSecond', 'stat', 'io', 'cwd', 'fd/3', 'fd/4', 'fd/5', 'fd/6'):
        try:
            if CANCELLED or time.monotonic() >= end:
                field = {'unavailable': 'cancelled_or_work_deadline'}
            elif owner.active.get(process.pid) is not process or process.returncode is not None:
                field = {'unavailable': 'not_owned_unreaped_child'}
            elif name == 'clockTicksPerSecond':
                field = {'value': os.sysconf('SC_CLK_TCK')}
            elif name in ('stat', 'io'):
                cap = 2048 if name == 'stat' else 1024
                with open(f'/proc/{process.pid}/{name}', 'rb', buffering=0) as stream:
                    raw = stream.read(cap + 1)
                field = {'value': raw[:cap].decode('utf-8', errors='replace'), 'truncated': len(raw) > cap}
            else:
                value = os.readlink(f'/proc/{process.pid}/{name}')  # Link text only, never its target.
                field = {'value': value[:512], 'truncated': len(value) > 512}
            result['fields'][name] = field
        except Exception as error:
            result['fields'][name] = {'unavailable': type(error).__name__}
    return result


def logs_within_cap(reports):
    sizes = [path.stat().st_size for path in reports.glob('*.log')]
    return not sizes or (max(sizes) <= 1048576 and sum(sizes) <= 4194304)


class Commands:
    def __init__(self, reports, env, helper, end):
        self.owner = owner_class(helper)()  # Subreaper before the first child.
        self.reports, self.env, self.end = reports, env, end
        self.sequence, self.events, self.joined = 0, [], {}
        self.absence_proved = False

    def start(self, argv, label, stdin=None, end=None, cleaning=False):
        deadline = self.end if end is None else (end if cleaning else min(self.end, end))
        require((cleaning or not CANCELLED) and time.monotonic() < deadline,
                'Cancelled/expired before command launch')
        require(cleaning or logs_within_cap(self.reports), 'Diagnostic output limit exceeded before launch')
        self.sequence += 1
        log = self.reports / f'{self.sequence:03d}-{label}.log'
        self.absence_proved = False
        with log.open('xb') as output:
            process = self.owner.track(subprocess.Popen(
                list(map(str, argv)), env=self.env, cwd=self.env['HOME'],
                stdin=subprocess.DEVNULL if stdin is None else stdin,
                stdout=output, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True))
        self.joined.pop(process.pid, None)
        self.events.append({'label': label, 'argv': list(map(str, argv)), 'pid': process.pid,
                            'started': time.monotonic(), 'log': log.name})
        return process, log

    def wait(self, task, seconds=30, end=None, cleaning=False, accepted=(0,)):
        process, log = task
        limit = self.end if end is None else (end if cleaning else min(self.end, end))
        deadline = min(time.monotonic() + seconds, limit)
        while process.poll() is None and time.monotonic() < deadline and (cleaning or not CANCELLED):
            require(cleaning or logs_within_cap(self.reports), 'Diagnostic output limit exceeded')
            time.sleep(0.05)
        ended = time.monotonic()
        event = {'pid': process.pid, 'actual_exit': process.returncode, 'ended': ended, 'deadline': deadline,
                 'cancelled': CANCELLED and not cleaning, 'accepted_exit_codes': list(accepted), 'normal_join': False}
        self.events.append(event)
        if (not cleaning and not CANCELLED and ended >= deadline and process.returncode is None
                and log.name.endswith('-no-host-ipc.log') and self.owner.active.get(process.pid) is process):
            try:
                event['scan_timeout_diagnostic'] = scan_timeout_diagnostic(self.owner, process, self.end)
            except Exception as error:
                event['scan_timeout_diagnostic'] = {'unavailable': type(error).__name__}
        require((cleaning or not CANCELLED) and ended < deadline and process.returncode in accepted,
                'Command failed, cancelled or exceeded its cap: ' + log.name)
        require(cleaning or logs_within_cap(self.reports), 'Diagnostic output limit exceeded at command exit')
        self.joined[process.pid] = process.returncode
        event['normal_join'] = True
        return '' if cleaning else log.read_text(errors='replace')

    def run(self, argv, label, seconds=30, stdin=None, end=None, cleaning=False, accepted=(0,)):
        limit = self.end if end is None else (end if cleaning else min(self.end, end))
        deadline = min(time.monotonic() + seconds, limit)
        task = self.start(argv, label, stdin=stdin, end=deadline, cleaning=cleaning)
        return self.wait(task, seconds, end=deadline, cleaning=cleaning, accepted=accepted)

    def dispose(self, name):
        self.absence_proved = False  # An unknown/failed new drain must not reuse preparation's receipt.
        receipt = self.owner.drain()
        save(self.reports / (name + '-children.json'), receipt)
        save(self.reports / (name + '-commands.json'), self.events)
        self.absence_proved = owned_absence(receipt)
        return normal_drain(receipt, self.joined)


# Fixed Ubuntu24.04 runtime-prefix profile, not a host-firewall/resolver restoration tool.
# Only private mounts are changed; namespace lifetime is the fence. No networking
# handle, service socket, host /proc, TAP/veth or shared /dev/shm enters the root.
BOOTSTRAP = r'''
set -euo pipefail
umask 022
root=$1; sdk=$2; jdk=$3; inputs=$4; work=$5; reports=$6; uid=$7; gid=$8; kvm_gid=$9
[[ $uid =~ ^[1-9][0-9]*$ && $gid =~ ^[1-9][0-9]*$ && $kvm_gid =~ ^[1-9][0-9]*$ ]]
fail_layout() { printf 'Unsupported declared runtime layout: %s\n' "$1" >&2; exit 1; }
[[ -f /etc/os-release ]] || fail_layout '/etc/os-release must be a regular file'
grep -Fxq 'ID=ubuntu' /etc/os-release || fail_layout '/etc/os-release must declare ID=ubuntu'
grep -Fxq 'VERSION_ID="24.04"' /etc/os-release || fail_layout '/etc/os-release must declare VERSION_ID="24.04"'
runtime_prefixes=(/usr/bin /usr/sbin /usr/lib/x86_64-linux-gnu /usr/lib64 /usr/lib/python3.12 /usr/lib/locale)
sdk_prefixes=(cmdline-tools/latest platform-tools emulator build-tools/36.0.0 platforms/android-36 system-images/android-26/google_apis/x86_64)
for prefix in "${sdk_prefixes[@]}"; do
  path="$sdk/$prefix"
  [[ -d "$path" && ! -L "$path" && $(readlink -e "$path") == "$path" ]] || fail_layout "$path must be a direct complete package directory"
done
[[ -f "$sdk/.knownPackages" && ! -L "$sdk/.knownPackages" ]] || fail_layout 'SDK discovery hash must be a regular file'
for path in /usr /usr/lib "${runtime_prefixes[@]}" /usr/lib/python3.12/encodings /usr/lib/python3.12/lib-dynload; do
  [[ -d "$path" && ! -L "$path" && $(readlink -e "$path") == "$path" ]] || fail_layout "$path must be a direct directory"
done
for pair in /bin:usr/bin /sbin:usr/sbin /lib:usr/lib /lib64:usr/lib64 /usr/bin/python3:python3.12; do
  path=${pair%%:*}; target=${pair#*:}
  [[ -L "$path" && $(readlink "$path") == "$target" ]] || fail_layout "$path must link to $target"
done
loader_destination_allowed() {
  case "$1" in
    /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2|/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2|../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2)
      [[ "$2" == /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 ]] ;;
    *) return 1 ;;
  esac
}
loader_link=/usr/lib64/ld-linux-x86-64.so.2
[[ -L "$loader_link" ]] || fail_layout "$loader_link observed spelling unavailable: must be a symlink"
# The sentinel preserves exact readlink bytes, including any trailing newlines.
loader_spelling=$(readlink -n "$loader_link" && printf .) || fail_layout "$loader_link observed spelling unavailable: readlink failed"
loader_spelling=${loader_spelling%.}
loader_canonical=$(readlink -e -n "$loader_link" && printf .) || fail_layout "$loader_link observed spelling '$loader_spelling'; canonical destination unavailable"
loader_canonical=${loader_canonical%.}
loader_destination_allowed "$loader_spelling" "$loader_canonical" ||
  fail_layout "$loader_link observed spelling '$loader_spelling', canonical destination '$loader_canonical'; expected an approved direct spelling to /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"
for path in /usr/bin/python3.12 /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2; do
  [[ -f "$path" && -x "$path" && ! -L "$path" ]] || fail_layout "$path must be a regular executable"
done
[[ -f /usr/lib/python3.12/os.py && ! -L /usr/lib/python3.12/os.py ]] || fail_layout '/usr/lib/python3.12/os.py must be a regular file'
run() { timeout --signal=TERM --kill-after=1s 10s "$@"; }
run mount --make-rprivate /
run mount --bind "$root" "$root"
# Own only scaffold parents before any borrowed package/runtime mount.
for path in usr usr/lib sdk sdk/cmdline-tools sdk/build-tools sdk/platforms sdk/system-images \
            sdk/system-images/android-26 sdk/system-images/android-26/google_apis \
            jdk inputs work reports proc sys dev dev/shm tmp run var var/tmp etc; do
  mkdir -p "$root/$path"; chown "$uid:$gid" "$root/$path"
done
ln -s usr/bin "$root/bin"; ln -s usr/sbin "$root/sbin"; ln -s usr/lib "$root/lib"
ln -s usr/lib64 "$root/lib64"
for prefix in "${runtime_prefixes[@]}"; do
  mkdir -p "$root$prefix"
  run mount --bind "$prefix" "$root$prefix"
  run mount -o remount,bind,ro,nosuid,nodev "$root$prefix"
done
for prefix in "${sdk_prefixes[@]}"; do
  mkdir -p "$root/sdk/$prefix"
  run mount --bind "$sdk/$prefix" "$root/sdk/$prefix"
  run mount -o remount,bind,ro,nosuid,nodev "$root/sdk/$prefix"
done
touch "$root/sdk/.knownPackages"
run mount --bind "$sdk/.knownPackages" "$root/sdk/.knownPackages"
run mount -o remount,bind,ro,nosuid,nodev "$root/sdk/.knownPackages"
for pair in "$jdk:jdk" "$inputs:inputs" "$work:work" "$reports:reports"; do
  source=${pair%:*}; target=${pair##*:}; run mount --bind "$source" "$root/$target"
  if [[ $target != work && $target != reports ]]; then run mount -o remount,bind,ro,nosuid,nodev "$root/$target"; fi
done
run mount -t proc -o ro,nosuid,nodev,noexec proc "$root/proc"
run mount -t sysfs -o ro,nosuid,nodev,noexec sysfs "$root/sys"
run mount -t tmpfs -o mode=755,nosuid,noexec,size=1m tmpfs "$root/dev"
mkdir "$root/dev/shm"
for device in null zero random urandom kvm; do touch "$root/dev/$device"; run mount --bind "/dev/$device" "$root/dev/$device"; done
ln -s /proc/self/fd "$root/dev/fd"
run mount -t tmpfs -o mode=1777,nosuid,nodev,size=128m tmpfs "$root/dev/shm"
for directory in tmp var/tmp; do run mount -t tmpfs -o mode=1777,nosuid,nodev,size=256m tmpfs "$root/$directory"; done
run mount -t tmpfs -o mode=755,nosuid,nodev,noexec,size=1m tmpfs "$root/run"
ln -s /run "$root/var/run"
printf '127.0.0.1 localhost\n::1 localhost\n' > "$root/etc/hosts"
printf 'hosts: files\npasswd: files\ngroup: files\n' > "$root/etc/nsswitch.conf"
printf 'nameserver 127.0.0.1\noptions attempts:1 timeout:1\n' > "$root/etc/resolv.conf"
printf 'app8:x:%s:%s::/work/home:/bin/sh\n' "$uid" "$gid" > "$root/etc/passwd"
printf 'app8:x:%s:\nkvm:x:%s:app8\n' "$gid" "$kvm_gid" > "$root/etc/group"
run ip link set lo up
run mount -o remount,bind,ro "$root"
set -o noclobber
cat > "$reports/runtime-profile.json" <<APP8_RUNTIME_PROFILE
{
  "schema": "app8-android-runtime-prefix-v1",
  "profile": "ubuntu-24.04-x86_64-python3.12",
  "stage": "bootstrap-before-full-ipc-scan",
  "usrView": "synthetic",
  "sdkView": "synthetic-complete-packages",
  "readOnlySdkPackagePrefixes": ["/sdk/cmdline-tools/latest", "/sdk/platform-tools", "/sdk/emulator", "/sdk/build-tools/36.0.0", "/sdk/platforms/android-36", "/sdk/system-images/android-26/google_apis/x86_64"],
  "readOnlySdkDiscoveryMetadata": ["/sdk/.knownPackages"],
  "javaCommandPath": "/jdk/bin/java",
  "readOnlyRuntimePrefixes": ["/usr/bin", "/usr/sbin", "/usr/lib/x86_64-linux-gnu", "/usr/lib64", "/usr/lib/python3.12", "/usr/lib/locale"],
  "recursiveBind": false,
  "mountFlags": ["ro", "nosuid", "nodev"],
  "mergedUsrLinks": {"/bin": "usr/bin", "/sbin": "usr/sbin", "/lib": "usr/lib", "/lib64": "usr/lib64"},
  "python3LinkTarget": "python3.12",
  "loaderLinkTarget": "$loader_spelling",
  "loaderCanonicalTarget": "$loader_canonical",
  "layoutValidated": true,
  "prefixMountsApplied": true,
  "nativeDependencyClosure": "unproved",
  "scanPerformance": "unproved"
}
APP8_RUNTIME_PROFILE
exec chroot "$root" /usr/bin/setpriv --reuid="$uid" --regid="$gid" --groups="$gid,$kvm_gid" \
  --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs \
  /usr/bin/env -i PATH=/jdk/bin:/usr/bin:/bin:/usr/sbin:/sbin HOME=/work/home TMPDIR=/tmp LANG=C.UTF-8 \
  JAVA_HOME=/jdk ANDROID_HOME=/sdk ANDROID_SDK_ROOT=/sdk ANDROID_USER_HOME=/work/android \
  ANDROID_AVD_HOME=/work/avd ANDROID_EMULATOR_HOME=/work/android \
  ADB_SERVER_SOCKET=tcp:127.0.0.1:5037 \
  /usr/bin/python3 -B /inputs/app8-android.py --inside
'''


def check_topology(links, addresses, routes):
    require(len(links) == 1 and links[0]['ifname'] == 'lo'
            and {'UP', 'LOOPBACK'} <= set(links[0]['flags']), 'Namespace is not loopback-only')
    require(len(addresses) == 1 and addresses[0]['ifname'] == 'lo', 'Unexpected address interface')
    locals_ = {row['local'] for row in addresses[0]['addr_info']}
    require('127.0.0.1' in locals_ and locals_ <= {'127.0.0.1', '::1'}, 'Missing/non-loopback address')
    require(all(row.get('dev') == 'lo' and row.get('dst') not in ('default', '0.0.0.0/0', '::/0')
                and 'gateway' not in row and 'via' not in row for row in routes), 'External/default route')


def namespace_identity(pid):
    return {kind: os.readlink(f'/proc/{pid}/ns/{kind}') for kind in ('net', 'mnt', 'ipc', 'pid')}


def isolated_process(pid, expected):
    require(namespace_identity(pid) == expected, 'Child namespace mismatch')
    fields = dict(line.split(':', 1) for line in Path(f'/proc/{pid}/status').read_text().splitlines() if ':' in line)
    require(os.getuid() > 0 and set(map(int, fields['Uid'].split())) == {os.getuid()}, 'Child retains another/saved root UID')
    require(all(int(fields[key].strip(), 16) == 0 for key in ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb'))
            and fields['NoNewPrivs'].strip() == '1', 'Child retains privilege')
    child_root, private_root = os.stat(f'/proc/{pid}/root'), os.stat('/')
    require((child_root.st_dev, child_root.st_ino) == (private_root.st_dev, private_root.st_ino), 'Child escaped the private root')
    return {'pid': pid, 'namespaces': expected, 'capabilities': 'all-zero', 'noNewPrivileges': True}


def inspect_package(manifest, policy, resources, phase):
    require('package="me.manga.kira.transportprobe"' in manifest, 'Wrong packaged application')
    def attribute(text, name):
        names = [name]
        if name.startswith('android:'):
            names.append('http://schemas.android.com/apk/res/android:' + name.removeprefix('android:'))
        rows = re.findall(r'^\s*A: (?:' + '|'.join(map(re.escape, names))
                          + r')(?:\(0x[0-9a-fA-F]+\))?=(.*)$', text, re.M)
        require(len(rows) == 1, 'Missing/ambiguous compiled attribute: ' + name)
        return rows[0].strip()
    def boolean(text, name, value):
        actual = attribute(text, name)
        word, number = ('true', '0xffffffff') if value else ('false', '0x0')
        require(actual in (word, f'(type 0x12){number}', f'"{word}" (Raw: "{word}")'), 'Unexpected compiled boolean')
    require(attribute(manifest, 'android:minSdkVersion') in ('26', '(type 0x10)0x1a')
            and attribute(manifest, 'android:targetSdkVersion') in ('36', '(type 0x10)0x24'), 'Wrong packaged SDK levels')
    boolean(manifest, 'android:debuggable', False)
    binding = attribute(manifest, 'android:networkSecurityConfig')
    require(re.fullmatch(r'@0x[0-9a-fA-F]{8}', binding), 'Missing compiled policy association')
    require(re.search(r'resource ' + re.escape(binding[1:]) + r' (?:\S+:)?xml/network_security_config\b', resources),
            'Packaged manifest does not reference the packaged XML')
    elements = re.findall(r'^\s*E: ([a-z-]+)', policy, re.M)
    require(elements == (['network-security-config', 'domain-config', 'domain'] if phase == 'allow'
                         else ['network-security-config', 'base-config']), 'Unexpected compiled policy structure')
    boolean(policy, 'cleartextTrafficPermitted', phase == 'allow')
    if phase == 'allow':
        boolean(policy, 'includeSubdomains', True)
        require('raijinscan.co' in policy, 'Historical domain missing from compiled policy')


def accept_phase(native, ready, receipt, phase, nonce, fixture_pid, started, ended):
    require(phase in POLICIES, 'Unknown phase')
    for record in (native, ready, receipt):
        require(record['phase'] == phase and record['nonce'] == nonce, 'Phase/nonce mismatch')
    port = ready['port']
    require(type(port) is int and 0 < port <= 65535, 'Invalid fixture port')
    for record in (ready, receipt):
        require(record['pid'] == fixture_pid and record['bindHost'] == '127.0.0.1'
                and record['port'] == port and record['lifetimeSeconds'] == 25, 'Fixture ownership mismatch')
    require(native['ok'] is True and native['sdk'] == 26 and native['minSdk'] == 26 and native['targetSdk'] == 36
            and native['proxyHost'] == '127.0.0.1' and native['proxyPort'] == port, 'Invalid native result')
    for key in ('readyMonotonicSeconds', 'deadlineMonotonicSeconds'):
        require(math.isfinite(ready[key]) and ready[key] == receipt[key], 'Fixture clock binding mismatch')
    require(ready['readyMonotonicSeconds'] <= started <= ready['readyMonotonicSeconds'] + 2
            and 0 < ready['deadlineMonotonicSeconds'] - ready['readyMonotonicSeconds'] <= 25
            and started <= ended <= ready['deadlineMonotonicSeconds']
            and ready['deadlineMonotonicSeconds'] <= receipt['closedMonotonicSeconds'] <= ready['deadlineMonotonicSeconds'] + 5
            and 25 <= receipt['elapsedSeconds'] <= 30, 'Native call/window incomplete or out of bounds')
    require(receipt['fixtureOK'] is True and receipt['windowComplete'] is True and receipt['errors'] == [],
            'Fixture did not finish normally')
    rows = native['observations']
    require(len(rows) == 2, 'Missing native observation')
    for host, row in zip(HOSTS, rows):
        require(row['url'] == f'http://{host}/{nonce}' and row['policyPermits'] is (phase == 'allow'), 'Wrong native policy subject')
        if phase == 'allow':
            require(row['outcome'] == 'canned-response' and row['responseCode'] == 200 and row['usingProxy'] is True
                    and row['receivedBodyBytes'] == len(f'app8-no-forward {nonce} {host}\n'), 'Historical positive control failed')
        else:
            require(row['outcome'] == 'native-cleartext-policy-rejection' and row['responseCode'] is None
                    and row['receivedBodyBytes'] == 0 and row['errorClass'] == 'java.io.IOException'
                    and row['errorMessage'] == f'Cleartext HTTP traffic to {host} not permitted', 'Not the specific API26 denial')
    connections = receipt['connections']
    require(len(connections) <= 8 and all(row['error'] is None and type(row['bytes']) is int and 0 <= row['bytes'] <= 8192 for row in connections)
            and receipt['receivedBytes'] == sum(row['bytes'] for row in connections), 'Incomplete receiver accounting')
    if phase == 'allow':
        require(len(connections) == 2 and sorted(row['host'] for row in connections) == sorted(HOSTS)
                and all(row['bytes'] > 0 and row['cannedResponseSent'] and row['peerEOF'] for row in connections), 'Missing historical wire positive')
    else:
        require(receipt['receivedBytes'] == 0, 'Candidate sent HTTP bytes')


def inside():
    work, reports, inputs = Path('/work'), Path('/reports'), Path('/inputs')
    runtime, request = read_json(inputs / 'runtime.json'), read_json(inputs / 'request.json')
    commands = Commands(reports, dict(os.environ), inputs / 'app29_owned_children.py', runtime['workDeadline'])
    adb = ['/sdk/platform-tools/adb', '-H', '127.0.0.1', '-P', '5037']
    device = adb + ['-s', 'emulator-5554']
    bt, jar = Path('/sdk/build-tools/36.0.0'), Path('/sdk/platforms/android-36/android.jar')
    emulator = server = fixture = None
    avd_intended = installed = False
    mapping = None
    passed, failure, phase_receipts, memberships = False, None, [], []
    try:
        require(os.getpid() == 1 and os.getuid() > 0, 'Not the unprivileged private PID-namespace leader')
        namespaces = namespace_identity('self')
        require(all(namespaces[k] != runtime['hostNamespaces'][k] for k in namespaces), 'Namespace isolation was not established')
        isolated_process('self', namespaces)
        for number in os.listdir('/proc/self/fd'):
            try:
                info = os.fstat(int(number))
            except OSError:
                continue  # The directory enumeration descriptor has already closed.
            require((int(number) == 0 and stat.S_ISCHR(info.st_mode) and info.st_rdev == os.stat('/dev/null').st_rdev)
                    or (int(number) in (1, 2) and stat.S_ISREG(info.st_mode)), 'Inherited IPC/network descriptor')
        # Scope is trusted installed Ubuntu/JDK/SDK tools and the fixed probe's IP path,
        # not confinement of malicious tools using unrelated non-IP families.
        links = json.loads(commands.run(['ip', '-j', 'link', 'show'], 'links'))
        addresses = json.loads(commands.run(['ip', '-j', 'address', 'show'], 'addresses'))
        routes = []
        for family in ('-4', '-6'):
            routes += json.loads(commands.run(['ip', '-j', family, 'route', 'show', 'table', 'all'], 'routes' + family))
        check_topology(links, addresses, routes)
        require(not commands.run(['find', '/usr', '/jdk', '/sdk', '/inputs', '-type', 's', '-o', '-type', 'p'], 'no-host-ipc').strip(),
                'Host socket/FIFO exposed by runtime mounts')
        with open('/dev/kvm', 'rb+', buffering=0):
            pass
        save(reports / 'isolation.json', {'namespaces': namespaces, 'links': links, 'addresses': addresses, 'routes': routes,
                                        'root': 'private-read-only', 'nonIpConfinement': 'not-claimed', 'inheritedNetworkFds': False})
        for relative, expected in runtime['sdkHashes'].items():
            require(digest(Path('/sdk') / relative, commands.end) == expected, 'Prepared SDK tool/platform or image properties changed before isolation')
        require(digest(Path('/jdk/bin/java'), commands.end) == runtime['jdkJavaSha256'], 'Prepared JDK java changed before isolation')
        pulse_library = Path('/usr/lib/x86_64-linux-gnu/libpulse.so.0')
        pulse_resolved = pulse_library.resolve(strict=True)
        require(pulse_resolved.is_relative_to(pulse_library.parent)
                and str(pulse_resolved) == runtime['libpulse0']['resolvedPath'],
                'libpulse0 canonical target escaped the fixed prefix or changed across isolation')
        require(digest(pulse_resolved, commands.end) == runtime['libpulse0']['sha256'],
                'Prepared libpulse0 changed or is unavailable in the existing isolated runtime prefix')
        save(reports / 'tool-identities.json', runtime)
        for argv, label in ((['/jdk/bin/javac', '-version'], 'javac-version'), ([bt / 'aapt2', 'version'], 'aapt-version'),
                            ([adb[0], 'version'], 'adb-version'), (['/sdk/emulator/emulator', '-version'], 'emulator-version')):
            commands.run(argv, label)
        for name in ('classes', 'dex', 'avd', 'android'):
            (work / name).mkdir()
        compile_end = min(time.monotonic() + 90, commands.end)
        commands.run(['/jdk/bin/javac', '--release', '8', '-classpath', jar, '-d', work / 'classes',
                      inputs / 'probe/android/TransportProbe.java'], 'javac', end=compile_end)
        classes = sorted((work / 'classes/me/manga/kira/transportprobe').glob('*.class'))
        require(classes, 'No compiled native probe')
        commands.run([bt / 'd8', '--min-api', '26', '--lib', jar, '--output', work / 'dex', *classes], 'd8', end=compile_end)
        commands.run(['/jdk/bin/keytool', '-genkeypair', '-noprompt', '-keystore', work / 'probe.keystore', '-alias', 'app8',
                      '-keyalg', 'RSA', '-keysize', '2048', '-validity', '1', '-dname', 'CN=App8LocalProbe',
                      '-storepass', 'app8-probe-only', '-keypass', 'app8-probe-only'], 'test-key', end=compile_end)
        shared_dex = (work / 'dex/classes.dex').read_bytes()
        package_bindings = []
        for phase in ('allow', 'deny'):
            directory = work / phase
            (directory / 'res/xml').mkdir(parents=True)
            policy = directory / 'res/xml/network_security_config.xml'
            shutil.copyfile(inputs / f'probe/policy-inputs/{phase}/network_security_config.xml', policy)
            require(digest(policy) == POLICIES[phase], 'Copied shipping policy changed')
            commands.run([bt / 'aapt2', 'compile', '--dir', directory / 'res', '-o', directory / 'resources.zip'], phase + '-resources', end=compile_end)
            commands.run([bt / 'aapt2', 'link', '-I', jar, '--manifest', inputs / 'probe/android/AndroidManifest.xml',
                          '-o', directory / 'unaligned.apk', directory / 'resources.zip'], phase + '-link', end=compile_end)
            with zipfile.ZipFile(directory / 'unaligned.apk', 'a') as archive:
                require('classes.dex' not in archive.namelist(), 'Unexpected preexisting bytecode')
                archive.writestr('classes.dex', shared_dex)
            commands.run([bt / 'zipalign', '-f', '4', directory / 'unaligned.apk', directory / 'aligned.apk'], phase + '-align', end=compile_end)
            apk = directory / 'probe.apk'
            commands.run([bt / 'apksigner', 'sign', '--ks', work / 'probe.keystore', '--ks-key-alias', 'app8',
                          '--ks-pass', 'pass:app8-probe-only', '--key-pass', 'pass:app8-probe-only', '--min-sdk-version', '26',
                          '--v4-signing-enabled', 'false', '--out', apk, directory / 'aligned.apk'], phase + '-sign', end=compile_end)
            commands.run([bt / 'apksigner', 'verify', '--verbose', apk], phase + '-verify', end=compile_end)
            manifest = commands.run([bt / 'aapt2', 'dump', 'xmltree', apk, '--file', 'AndroidManifest.xml'], phase + '-manifest', end=compile_end)
            policy_dump = commands.run([bt / 'aapt2', 'dump', 'xmltree', apk, '--file', 'res/xml/network_security_config.xml'], phase + '-policy', end=compile_end)
            resources = commands.run([bt / 'aapt2', 'dump', 'resources', apk], phase + '-resource-table', end=compile_end)
            inspect_package(manifest, policy_dump, resources, phase)
            with zipfile.ZipFile(apk) as archive:
                require(archive.namelist().count('classes.dex') == 1 and archive.read('classes.dex') == shared_dex, 'Packaged code differs')
            package_bindings.append({'phase': phase, 'policySha256': digest(policy), 'apkSha256': digest(apk),
                                     'resourcesSha256': digest(directory / 'resources.zip'), 'sharedDexSha256': hashlib.sha256(shared_dex).hexdigest()})
        save(reports / 'packages.json', package_bindings)
        avd_intended = True
        save(reports / 'owned-intent.json', {'avd': runtime['avd'], 'serial': 'emulator-5554', 'adbHost': '127.0.0.1', 'adbPort': 5037})
        answer = work / 'avd-answer'
        answer.write_text('no\n')  # Fixed default hardware profile; no interactive retry.
        with answer.open('rb') as stdin:
            commands.run(['/sdk/cmdline-tools/latest/bin/avdmanager', 'create', 'avd', '-n', runtime['avd'], '-k', IMAGE,
                          '-p', work / 'device'], 'create-avd', stdin=stdin)
        server = commands.start([adb[0], '-L', 'tcp:127.0.0.1:5037', 'nodaemon', 'server'], 'private-adb')
        boot_end = min(time.monotonic() + 180, commands.end)
        while True:
            require(server[0].poll() is None and time.monotonic() < boot_end and not CANCELLED, 'Private adb readiness failed')
            try:
                with socket.create_connection(('127.0.0.1', 5037), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        memberships.append(isolated_process(server[0].pid, namespaces))
        emulator = commands.start(['/sdk/emulator/emulator', '-avd', runtime['avd'], '-port', '5554', '-accel', 'on',
                                   '-no-window', '-no-audio', '-no-snapshot', '-no-boot-anim', '-gpu', 'swiftshader_indirect',
                                   '-memory', '1536', '-cores', '2', '-camera-back', 'none', '-camera-front', 'none',
                                   '-dns-server', '127.0.0.1'], 'emulator')
        while time.monotonic() < boot_end:
            require(emulator[0].poll() is None and server[0].poll() is None, 'Owned emulator/adb exited before readiness')
            text = commands.run(device + ['shell', 'getprop', 'sys.boot_completed'], 'boot-property', seconds=5, end=boot_end, accepted=(0, 1))
            if text.strip() == '1':
                break
            time.sleep(1)
        else:
            raise RuntimeError('API26 boot deadline exceeded')
        memberships.append(isolated_process(emulator[0].pid, namespaces))
        require(commands.run(device + ['shell', 'getprop', 'ro.build.version.sdk'], 'sdk-level').strip() == '26', 'Not API26')
        require(commands.run(adb + ['devices'], 'private-devices').splitlines()[1:] == ['emulator-5554\tdevice', ''], 'Unexpected private device inventory')
        for phase in ('allow', 'deny'):
            require(time.monotonic() + 30 < commands.end, 'Insufficient complete fixture window budget')
            require(not commands.run(device + ['shell', 'pm', 'list', 'packages', PACKAGE], phase + '-absent').strip(), 'Probe package already installed')
            installed = True  # Creation intent precedes the install cancellation window.
            commands.run(device + ['install', '-t', work / phase / 'probe.apk'], phase + '-install')
            require(not commands.run(device + ['reverse', '--list'], phase + '-reverse-before').strip(), 'Preexisting reverse mapping')
            require(time.monotonic() + 30 < commands.end, 'Insufficient live fixture and join budget after install')
            fixture = commands.start(['/usr/bin/python3', '-B', inputs / 'probe/fixture/no_forward_proxy.py', '--phase', phase,
                                      '--nonce', runtime['nonce'], '--output', work / phase / 'fixture'], phase + '-fixture')
            ready_path = work / phase / 'fixture/ready.json'
            readiness = time.monotonic() + 2
            while not ready_path.exists() and time.monotonic() < readiness and fixture[0].poll() is None and not CANCELLED:
                time.sleep(0.01)
            require(ready_path.exists() and time.monotonic() < readiness, 'Fixture readiness missed')
            ready = read_json(ready_path)
            require(ready['pid'] == fixture[0].pid and ready['phase'] == phase and ready['nonce'] == runtime['nonce']
                    and ready['bindHost'] == '127.0.0.1' and type(ready['port']) is int and 0 < ready['port'] <= 65535, 'Unbound fixture readiness')
            memberships.append(isolated_process(fixture[0].pid, namespaces))
            mapping = 'tcp:' + str(ready['port'])
            commands.run(device + ['reverse', mapping, mapping], phase + '-reverse', end=ready['readyMonotonicSeconds'] + 2)
            started = time.monotonic()
            require(started <= ready['readyMonotonicSeconds'] + 2, 'Native phase did not start promptly')
            output = commands.run(device + ['shell', 'am', 'instrument', '-w', '-r', '-e', 'phase', phase,
                                          '-e', 'nonce', runtime['nonce'], '-e', 'port', str(ready['port']),
                                          PACKAGE + '/' + PACKAGE + '.TransportProbe'], phase + '-native', seconds=20,
                                  end=ready['deadlineMonotonicSeconds'])
            ended = time.monotonic()
            matches = re.findall(r'(?m)^(?:INSTRUMENTATION_RESULT: stream=)?APP8_NATIVE_RESULT (\{[^\n]+\})$', output)
            require(len(matches) == 1 and output.count('APP8_NATIVE_RESULT ') == 1, 'Missing/ambiguous native JSON')
            native = json.loads(matches[0])
            commands.wait(fixture, seconds=30, end=ready['deadlineMonotonicSeconds'] + 5)
            receipt = read_json(work / phase / 'fixture/receipt.json')
            accept_phase(native, ready, receipt, phase, runtime['nonce'], fixture[0].pid, started, ended)
            save(reports / (phase + '-result.json'), {'native': native, 'ready': ready, 'fixture': receipt, 'started': started, 'ended': ended})
            phase_receipts.append(phase)
            fixture = None
            commands.run(device + ['reverse', '--remove', mapping], phase + '-remove-reverse')
            mapping = None
            require(not commands.run(device + ['reverse', '--list'], phase + '-reverse-gone').strip(), 'Reverse mapping survived removal')
            commands.run(device + ['uninstall', PACKAGE], phase + '-uninstall')
            installed = False
            require(not commands.run(device + ['shell', 'pm', 'list', 'packages', PACKAGE], phase + '-package-gone').strip(), 'Package survived uninstall')
            require(not commands.run(device + ['shell', 'pidof', PACKAGE], phase + '-process-gone', accepted=(0, 1)).strip(), 'Native process survived uninstall')
        passed = phase_receipts == ['allow', 'deny']
    except Exception as error:
        failure = str(error)
    finally:
        cleanup_end, cleanup_ok = min(time.monotonic() + 60, runtime['cleanupDeadline']), True
        def cleanup(argv, label):
            nonlocal cleanup_ok
            try:
                commands.run(argv, label, seconds=8, end=cleanup_end - 8, cleaning=True)
            except Exception:
                cleanup_ok = False
        if fixture is not None:
            try:
                commands.wait(fixture, seconds=30, end=cleanup_end - 8, cleaning=True)
            except Exception:
                cleanup_ok = False
        if server is not None and server[0].poll() is None:
            if mapping is not None:
                cleanup(device + ['reverse', '--remove', mapping], 'cleanup-reverse')
            if installed:
                cleanup(device + ['uninstall', PACKAGE], 'cleanup-package')
            if emulator is not None and emulator[0].poll() is None:
                cleanup(device + ['emu', 'kill'], 'shutdown-owned-emulator')
                try:
                    commands.wait(emulator, seconds=15, end=cleanup_end - 8, cleaning=True)
                except Exception:
                    cleanup_ok = False
            cleanup(adb + ['kill-server'], 'shutdown-private-adb')
            try:
                commands.wait(server, seconds=5, end=cleanup_end - 8, cleaning=True)
            except Exception:
                cleanup_ok = False
        if avd_intended and (emulator is None or emulator[0].poll() is not None):
            cleanup(['/sdk/cmdline-tools/latest/bin/avdmanager', 'delete', 'avd', '-n', runtime['avd']], 'delete-owned-avd')
        absence = commands.dispose('inside')
        save(reports / 'namespace-membership.json', memberships)
        output_ok = logs_within_cap(reports)
        save(reports / 'native-summary.json', {'passed': passed and cleanup_ok and absence and output_ok and not CANCELLED,
                                             'failure': failure, 'normalCleanup': cleanup_ok and absence,
                                             'logsWithinCap': output_ok, 'phases': phase_receipts,
                                             'scope': 'copied-policy SDK-only API26 host'})
    return 0 if passed and cleanup_ok and absence and output_ok and not CANCELLED else 1


def outside():
    source = Path(__file__).resolve()
    request = read_json(source.with_name('app8-android.request.json'))
    require(request['authorization'] == 'APP8_ANDROID_SINGLE_RUN_AUTHORIZED', 'Public synthetic draft has no execution authorization')
    require(request['schema'] == 'app8-android-private-v1' and request['issueSha'] == ISSUE and request['historicalSha'] == BASE
            and request['probeManifestSha256'] == MANIFEST and request['policySha256'] == POLICIES
            and request['ownedChildrenSha256'] == OWNER_HASH and request['orchestratorSha256'] == digest(source)
            and request['shippingBuildInputSha256'] == CHECKPOINT_BUILD_HASH and request['shippingManifestSha256'] == CHECKPOINT_APP_MANIFEST_HASH
            and request['shippingCompileSdk'] == 37
            and request['shippingPolicyPath'] == POLICY_PATH and request['acceptedSourceGuardResultSha256'] == CHECKPOINT_GUARD_HASH,
            'Unbound request/source')
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin'
            and os.environ.get('GITHUB_REF') == 'refs/heads/validation/app8-libpulse-target-20260915-01'
            and os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
            and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted', 'Wrong hosted invocation')
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'Hosted x86_64 Linux required')
    run = Path(os.environ['APP8_RUN'])
    require(run.is_absolute() and run.parent.resolve() == Path(os.environ['RUNNER_TEMP']).resolve()
            and re.fullmatch(r'app8-android-[1-9][0-9]*-1', run.name) and not run.exists(), 'Not a fresh owned run path')
    run.mkdir(mode=0o700)
    reports, home = run / 'reports', run / 'home'
    reports.mkdir(mode=0o700); home.mkdir(mode=0o700)
    deadline = time.monotonic() + 540  # Includes optional preparation; reserves the job's final minute.
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(home), 'LANG': 'C.UTF-8'}
    commands = Commands(reports, env, source.with_name('app29_owned_children.py'), deadline)
    passed, failure = False, None
    try:
        require(os.getuid() > 0 and stat.S_ISCHR(Path('/dev/kvm').stat().st_mode), 'Missing KVM/unprivileged runner')
        for tool in ('sudo', 'unshare', 'chroot', 'setpriv', 'mount', 'ip', 'timeout', 'find', 'dpkg-query', 'apt-get'):
            require(shutil.which(tool, path=env['PATH']), 'Missing installed isolation prerequisite: ' + tool)
        tools = request['toolchain']
        require(tools == {'javaHomeEnvironment': 'JAVA_HOME_17_X64', 'buildTools': '36.0.0', 'compilePlatform': 'android-36',
                          'systemImage': IMAGE, 'missingSdkPreparationSeconds': 120}, 'Unsupported toolchain request')
        sdk = Path(os.environ['ANDROID_HOME']).resolve()
        jdk = Path(os.environ['JAVA_HOME_17_X64']).resolve()
        require(':' not in str(sdk) + str(jdk) + str(run), 'Unsupported path separator')
        expected_tools = ['platform-tools/adb', 'emulator/emulator', 'build-tools/36.0.0/aapt2', 'build-tools/36.0.0/d8',
                          'build-tools/36.0.0/zipalign', 'build-tools/36.0.0/apksigner', 'platforms/android-36/android.jar',
                          'cmdline-tools/latest/bin/sdkmanager', 'cmdline-tools/latest/bin/avdmanager']
        for relative in ('cmdline-tools/latest/bin/sdkmanager', 'cmdline-tools/latest/bin/avdmanager'):
            require((sdk / relative).is_file(), 'Missing installed SDK command-line tool: ' + relative)
        require((jdk / 'bin/javac').is_file() and (jdk / 'bin/keytool').is_file()
                and (jdk / 'bin/java').is_file() and not (jdk / 'bin/java').is_symlink(), 'Missing installed JDK17')
        payload = source.parent.parent / 'docs/remediation/app8-native'
        require(digest(payload / 'manifest.json') == MANIFEST, 'Frozen native manifest mismatch')
        manifest = read_json(payload / 'manifest.json')
        entries = {row['path']: row for row in manifest['files']}
        require(len(entries) == len(manifest['files']), 'Duplicate frozen manifest path')
        inputs, work, root = (run / name for name in ('inputs', 'work', 'root'))
        for directory in (inputs, work, root):
            directory.mkdir(mode=0o700)
        (work / 'home').mkdir(mode=0o700)
        for relative in INPUTS:
            src = payload / relative
            require(src.stat().st_size == entries[relative]['bytes'] and digest(src) == entries[relative]['sha256'], 'Frozen Android input mismatch')
            dst = inputs / 'probe' / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        for phase in POLICIES:
            require(digest(inputs / f'probe/policy-inputs/{phase}/network_security_config.xml') == POLICIES[phase], 'Shipping policy-byte binding failed')
        metadata = read_json(inputs / 'probe/policy-inputs.json')
        provenance = read_json(inputs / 'probe/provenance.json')
        build_inputs = {row['path']: row['sha256'] for row in metadata['currentBuildInputsReadDirectly']}
        require(metadata['base'] == BASE and metadata['android']['minSdk'] == 26
                and metadata['android']['targetSdk'] == 36 and metadata['android']['compileSdk'] == 37
                and metadata['android']['manifestAssociation'] == '@xml/network_security_config'
                and build_inputs['app/build.gradle.kts'] == BUILD_HASH
                and build_inputs['app/src/main/AndroidManifest.xml'] == APP_MANIFEST_HASH
                and provenance['sourceGuardResultSha256'] == GUARD_HASH
                and provenance['productBase'] == BASE
                and metadata['productPatchSha256'] == provenance['productPatchSha256'], 'Frozen source provenance mismatch')
        checkpoint_path = payload / 'checkpoint-policy-provenance.json'
        require(digest(checkpoint_path) == request['checkpointProvenanceSha256'], 'Missing/unbound primary checkpoint provenance')
        checkpoint = {'schema': 'app8-source-checkpoint-v1', **{key: request[key] for key in (
            'issueSha', 'historicalSha', 'shippingPolicyPath', 'policySha256', 'shippingBuildInputSha256',
            'shippingManifestSha256', 'probeManifestSha256', 'acceptedSourceGuardResultSha256')}}
        require(read_json(checkpoint_path) == checkpoint, 'Primary checkpoint does not attest the bound policy bytes')
        save(reports / 'source-bindings.json', {'checkpoint': checkpoint, 'checkpointProvenanceSha256': digest(checkpoint_path),
                                             'frozenInputs': {relative: entries[relative] for relative in INPUTS},
                                             'frozenInputsScope': 'historical probe construction; current source target is checkpoint',
                                             'shippingCompileSdk': metadata['android']['compileSdk'],
                                             'probeCompilePlatform': tools['compilePlatform'],
                                             'sourceGuardRerun': False})
        shutil.copyfile(source, inputs / 'app8-android.py')
        shutil.copyfile(source.with_name('app29_owned_children.py'), inputs / 'app29_owned_children.py')
        shutil.copyfile(source.with_name('app8-android.request.json'), inputs / 'request.json')
        # No preparation, namespace or native command precedes immutable input binding.
        commands.env = dict(env, JAVA_HOME=str(jdk), ANDROID_HOME=str(sdk), ANDROID_SDK_ROOT=str(sdk))
        pulse_library = Path('/usr/lib/x86_64-linux-gnu/libpulse.so.0')
        pulse_status = commands.run(['/usr/bin/dpkg-query', '-W', '-f=${Status}', 'libpulse0'],
                                    'libpulse0-package-status', seconds=5, accepted=(0, 1)).strip()
        pulse_present = pulse_library.is_file()
        pulse_prepared = pulse_status != 'install ok installed' or not pulse_present
        if pulse_prepared:
            # Root-side deadline precedes the outer cap; the existing drain must still prove absence.
            require(time.monotonic() + 80 < deadline - 70, 'Insufficient bounded libpulse0 preparation window')
            commands.run(['sudo', '-n', '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '60s',
                          '/usr/bin/env', 'DEBIAN_FRONTEND=noninteractive', 'NEEDRESTART_MODE=l',
                          '/usr/bin/apt-get', '--yes', '--no-install-recommends', '--no-remove',
                          '-o', 'DPkg::Lock::Timeout=10', 'install', 'libpulse0'],
                         'prepare-required-libpulse0', seconds=70, end=deadline - 70)
        pulse_resolved = pulse_library.resolve(strict=True)
        require(pulse_resolved.is_file() and pulse_resolved.is_relative_to(pulse_library.parent),
                'libpulse0 SONAME is not available within the existing declared runtime prefix')
        image = sdk / 'system-images/android-26/google_apis/x86_64'
        package_inputs = {
            'emulator': ('emulator/emulator',),
            'platform-tools': ('platform-tools/adb',),
            'build-tools;36.0.0': ('build-tools/36.0.0/aapt2', 'build-tools/36.0.0/d8',
                                 'build-tools/36.0.0/zipalign', 'build-tools/36.0.0/apksigner'),
            'platforms;android-36': ('platforms/android-36/android.jar',),
            IMAGE: ('system-images/android-26/google_apis/x86_64/source.properties',),
        }
        missing_packages = [package for package, required in package_inputs.items()
                            if any(not (sdk / relative).is_file() for relative in required)]
        prepared = IMAGE in missing_packages
        if missing_packages:
            commands.run([sdk / 'cmdline-tools/latest/bin/sdkmanager', '--sdk_root=' + str(sdk), *missing_packages],
                         'prepare-missing-declared-sdk', seconds=120)
        require(commands.dispose('preparation'), 'SDK/runtime preparation left abnormal/forced descendants; refusing isolation')
        for relative in expected_tools:
            require((sdk / relative).is_file(), 'Missing required SDK tool/platform after preparation: ' + relative)
        properties = dict(line.split('=', 1) for line in (image / 'source.properties').read_text().splitlines() if '=' in line)
        properties = {key.strip(): value.strip() for key, value in properties.items()}
        require(properties.get('AndroidVersion.ApiLevel') == '26' and properties.get('SystemImage.Abi') == 'x86_64'
                and properties.get('SystemImage.TagId') == 'google_apis' and properties.get('Pkg.Revision'), 'Wrong prepared API26 image')
        # Bind SDK tools/platform and image identity/revision, not multi-GB image contents.
        image_properties = str((image / 'source.properties').relative_to(sdk))
        sdk_hashes = {relative: digest(sdk / relative, deadline - 70) for relative in expected_tools + [image_properties]}
        require((sdk / '.knownPackages').is_file() and not (sdk / '.knownPackages').is_symlink()
                and (sdk / '.knownPackages').stat().st_size <= 256, 'Unsupported SDK discovery hash')
        sdk_hashes['.knownPackages'] = digest(sdk / '.knownPackages', deadline - 70)
        nonce = secrets.token_hex(16)
        runtime = {'issueSha': ISSUE, 'historicalSha': BASE, 'carrierSha': os.environ['GITHUB_SHA'],
                   'nonce': nonce, 'avd': 'App8-' + nonce, 'workDeadline': deadline - 70, 'cleanupDeadline': deadline - 10,
                   'hostNamespaces': namespace_identity('self'), 'sdkHashes': sdk_hashes,
                   'jdkJavacSha256': digest(jdk / 'bin/javac'), 'jdkJavaSha256': digest(jdk / 'bin/java'),
                   'libpulse0': {'packageStatusBefore': pulse_status, 'sonamePresentBefore': pulse_present,
                                 'preparationAttempted': pulse_prepared, 'resolvedPath': str(pulse_resolved),
                                 'sha256': digest(pulse_resolved, deadline - 70)},
                   'imageProperties': properties, 'imagePrepared': prepared,
                   'sdkPreparedPackages': missing_packages,
                   'shippingCompileSdk': metadata['android']['compileSdk'], 'probeCompilePlatform': tools['compilePlatform'],
                   'probeManifestSha256': MANIFEST, 'sourceGuardRerun': False}
        save(inputs / 'runtime.json', runtime)
        commands.env = env  # Never inherit Actions tokens/proxies/agents into the namespace.
        kvm_gid = Path('/dev/kvm').stat().st_gid
        task = commands.start(['sudo', '-n', 'unshare', '--net', '--mount', '--ipc', '--pid', '--fork', '--kill-child=KILL',
                               'bash', '--noprofile', '--norc', '-c', BOOTSTRAP, 'app8-private-root', root, sdk, jdk,
                               inputs, work, reports, os.getuid(), os.getgid(), kvm_gid], 'isolated-phase')
        commands.wait(task, seconds=max(0.1, deadline - time.monotonic()))
        summary = read_json(reports / 'native-summary.json')
        require(summary['passed'] is True and summary['normalCleanup'] is True, 'Native evidence/normal disposal incomplete')
        passed = True
    except Exception as error:
        failure = str(error)
    finally:
        normal_cleanup = commands.dispose('outside')
        absence = commands.absence_proved
        output_ok = logs_within_cap(reports)  # Evaluate final bytes before any retention truncation.
        scratch_removed = False
        if absence:
            try:
                for name in ('root', 'work', 'inputs', 'home'):
                    target = run / name
                    if target.exists():
                        shutil.rmtree(target)  # Only after namespace leader/descendant absence.
                scratch_removed = True
            except OSError as error:
                failure = (failure or '') + '; owned scratch removal failed: ' + str(error)
        passed = passed and normal_cleanup and absence and output_ok and scratch_removed and not CANCELLED
        # Only failed oversized logs can be truncated; a truncated log never supports PASS.
        if not output_ok:
            remaining = 4194304
            for path in sorted(reports.glob('*.log')):
                keep = min(1048576, remaining)
                with path.open('r+b') as stream:
                    stream.truncate(min(path.stat().st_size, keep))
                remaining -= path.stat().st_size
        save(reports / 'result.json', {'passed': passed and not CANCELLED, 'failure': failure, 'normalOwnedCleanup': normal_cleanup,
                                      'ownedProcessAbsenceProved': absence,
                                      'logsWithinCapBeforeTruncation': output_ok, 'ownedScratchRemoved': scratch_removed,
                                      'issueSha': ISSUE, 'historicalSha': BASE, 'scope': 'public synthetic Android SDK-only copied policies',
                                      'shippingApkMergeAccepted': False, 'macOSAttempted': False})
    return 0 if passed and not CANCELLED else 1


def main():
    os.umask(0o077)
    for number in (signal.SIGTERM, signal.SIGINT):
        signal.signal(number, interrupted)
    try:
        return inside() if sys.argv[1:] == ['--inside'] else outside()
    except Exception as error:
        print('APP8 INCOMPLETE: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
