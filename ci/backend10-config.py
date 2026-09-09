"""Private config-only checks. Never build, start an app, or execute kira-deploy."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

CONTROL = Path(__file__).resolve().parent.parent
BACKEND = CONTROL.parent / 'backend'
LABEL = 'me.kira.backend10-config-owner'
FILES = (
    'deploy/server3/README.md',
    'deploy/server3/compose.yaml',
    'deploy/server3/ingress.env.example',
    'deploy/server3/kira-deploy',
    'deploy/server3/nginx/admin.kiramanga.me.tls.conf',
    'deploy/server3/nginx/api.kiramanga.me.http.conf',
    'deploy/server3/nginx/api.kiramanga.me.tls.conf',
)
CANCELLED = False


class CheckFailure(Exception):
    pass


def require(condition, message):
    if not condition:
        raise CheckFailure(message)


def targets():
    """No subprocesses or Docker access before both primary bindings pass."""
    data = json.loads((CONTROL / 'ci/backend10-config.targets.json').read_text())
    require(set(data) == {'schemaVersion', 'backend', 'nginx'} and data['schemaVersion'] == 1,
            'Invalid target schema')
    backend, nginx = data['backend'], data['nginx']
    require(set(backend) == {'repository', 'sha'} and
            backend['repository'] == 'kira-manga/Kira-backend', 'Wrong Backend repository')
    require(isinstance(backend['sha'], str) and re.fullmatch(r'[0-9a-f]{40}', backend['sha']) and
            backend['sha'] != '0' * 40, 'Primary must bind the exact Backend issue commit')
    require(set(nginx) == {'image'} and isinstance(nginx['image'], str) and
            re.fullmatch(r'docker\.io/library/nginx@sha256:[0-9a-f]{64}', nginx['image']) and
            not nginx['image'].endswith(':' + '0' * 64),
            'Primary must bind an official Nginx image digest')
    return data


def context():
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin', 'Private carrier required')
    run_id, attempt = os.environ.get('GITHUB_RUN_ID', ''), os.environ.get('GITHUB_RUN_ATTEMPT', '')
    require(re.fullmatch(r'[0-9]+', run_id) and re.fullmatch(r'[0-9]+', attempt), 'Hosted run required')
    owner = run_id + '-' + attempt
    root = Path(os.environ['RUNNER_TEMP']).resolve() / ('backend10-config-' + owner)
    require(Path(os.environ['BACKEND10_RUN']) == root and not root.is_symlink(), 'Unsafe output root')
    return root, owner


def interrupted(signum, frame):
    global CANCELLED
    CANCELLED = True  # Defer interruption until the subprocess is registered, then clean in finally.


class Checks:
    def __init__(self, root, owner, result):
        self.root, self.owner, self.result = root, owner, result
        self.work = root / 'scratch'
        require(not self.work.is_symlink(), 'Unsafe scratch path')
        self.work.mkdir(mode=0o700, exist_ok=True)
        (self.work / 'home').mkdir(mode=0o700, exist_ok=True)
        self.env = {'PATH': os.environ['PATH'], 'HOME': str(self.work / 'home'),
                    'TMPDIR': str(self.work), 'LC_ALL': 'C', 'DOCKER_HOST': 'unix:///var/run/docker.sock'}
        self.deadline = time.monotonic() + 360

    def note(self, message):
        print(message, flush=True)
        with (self.root / 'reports/result.log').open('a') as log:
            log.write(message + '\n')

    def command(self, name, argv, seconds=20, expected=0, cleaning=False):
        require(cleaning or not CANCELLED, 'Validation cancelled')
        budget = seconds if cleaning else min(seconds, self.deadline - time.monotonic())
        require(budget > 0, 'Validation deadline expired')
        started, timed_out = time.monotonic(), False
        process = subprocess.Popen(argv, cwd=self.work, env=self.env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            while True:
                try:
                    out, err = process.communicate(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() - started >= budget or (CANCELLED and not cleaning):
                        timed_out = True
                        os.killpg(process.pid, signal.SIGKILL)
                        out, err = process.communicate(timeout=3)
                        break
        finally:
            # Compose may have a plugin child; reap the direct child and stop its owned group.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
        receipt = {'check': name, 'exit': process.returncode, 'timeout_or_cancel': timed_out,
                   'seconds': round(time.monotonic() - started, 3)}
        self.result.setdefault('commands', []).append(receipt)
        self.note(json.dumps(receipt, sort_keys=True))  # Never log argv, env, model or raw diagnostics.
        require(not timed_out, name + ': deadline/cancellation')
        require(len(out) + len(err) <= 256 * 1024, name + ': excessive output')
        require(expected is None or process.returncode == expected, name + ': unexpected exit')
        return process.returncode, out.decode('utf-8', 'replace'), err.decode('utf-8', 'replace')

    def cleanup(self):
        ok = True
        try:
            if (self.root / 'container-intent').exists():
                require((self.root / 'container-intent').read_text() == self.owner, 'Wrong cleanup owner')
                query = ['docker', 'ps', '-aq', '--no-trunc', '--filter', 'label=' + LABEL + '=' + self.owner]
                ids = self.command('owned-containers', query, seconds=10, cleaning=True)[1].split()
                require(all(re.fullmatch(r'[0-9a-f]{64}', cid) for cid in ids), 'Invalid owned container ID')
                if ids:
                    self.command('remove-owned-containers', ['docker', 'rm', '-f', *ids],
                                 seconds=15, cleaning=True)
                require(not self.command('owned-containers-absent', query, seconds=10, cleaning=True)[1].strip(),
                        'Owned containers remain')
        except Exception:
            self.note('FAIL: owned-container disposal could not be verified')
            ok = False
        try:
            shutil.rmtree(self.work)
            require(not self.work.exists(), 'Scratch remains')
        except Exception:
            self.note('FAIL: owned scratch disposal could not be verified')
            ok = False
        return ok


def compose_checks(check):
    work = check.work
    shutil.copyfile(BACKEND / 'deploy/server3/compose.yaml', work / 'compose.yaml')
    fixtures = {
        'postgres.env': '', 'migration.env': '',
        'images.env': ''.join('KIRA_' + name.upper() + '_IMAGE=kira-' + name + ':synthetic\n'
                              for name in ('backend', 'web', 'admin')),
        'backend.env': 'SPRING_PROFILES_ACTIVE=dev\nKIRA_SERVER3_HOST_PEER=203.0.113.20\n'
                       'KIRA_SERVER3_ADMIN_ADDRESS=203.0.113.21\n',
        'admin.env': 'KIRA_ADMIN_ORIGIN=https://admin.invalid\nKIRA_BACKEND_URL=https://ignored.invalid\n'
                     'KIRA_ADMIN_TRUSTED_INGRESS=false\n',
        'ingress.env': 'KIRA_SERVER3_ADMIN_SUBNET=192.0.2.0/24\nKIRA_SERVER3_ADMIN_GATEWAY=192.0.2.1\n'
                       'KIRA_SERVER3_ADMIN_ADDRESS=192.0.2.10\nKIRA_SERVER3_HOST_PEER=198.51.100.1\n',
    }
    for name, content in fixtures.items():
        (work / name).write_text(content)

    def command(env_file, *args):
        return ['docker', 'compose', '--project-name', 'kira', '--file', str(work / 'compose.yaml'),
                '--env-file', str(work / 'images.env'), '--env-file', str(work / env_file),
                '--profile', 'tools', 'config', *args]

    check.command('compose-quiet', command('ingress.env', '--quiet'))
    model = json.loads(check.command('compose-effective-model', command('ingress.env', '--format', 'json'))[1])
    services = model['services']
    require(set(services) == {'postgres', 'backend-migrate', 'backend', 'web', 'admin'}, 'Unexpected service set')
    require({name for name, service in services.items() if 'admin-ingress' in service.get('networks', {})}
            == {'backend', 'admin'}, 'Dedicated ingress membership mismatch')
    for service, networks, port in (('backend', {'database', 'proxy', 'admin-ingress'}, '18080'),
                                    ('web', {'proxy'}, '18081'), ('admin', {'admin-ingress'}, '18082')):
        require(set(services[service]['networks']) == networks, 'Service network mismatch: ' + service)
        ports = services[service]['ports']
        require(len(ports) == 1 and ports[0]['host_ip'] == '127.0.0.1' and ports[0]['target'] == 8080
                and str(ports[0]['published']) == port, 'Loopback publication mismatch: ' + service)
    backend_env, admin_env = services['backend']['environment'], services['admin']['environment']
    require(all(backend_env.get(key) == value for key, value in {
        'SPRING_PROFILES_ACTIVE': 'prod,server3', 'KIRA_SERVER3_HOST_PEER': '198.51.100.1',
        'KIRA_SERVER3_ADMIN_ADDRESS': '192.0.2.10'}.items()), 'Backend effective environment mismatch')
    require(admin_env.get('KIRA_BACKEND_URL') == 'http://backend:8080' and
            admin_env.get('KIRA_ADMIN_TRUSTED_INGRESS') == 'true', 'Admin effective trust/URL mismatch')
    network = model['networks']['admin-ingress']
    require(network['name'] == 'kira-admin-ingress' and network['driver'] == 'bridge' and
            not network.get('internal', False) and not network.get('enable_ipv6', False) and
            network['driver_opts']['com.docker.network.bridge.gateway_mode_ipv4'] == 'nat' and
            network['ipam']['config'] == [{'subnet': '192.0.2.0/24', 'gateway': '192.0.2.1'}] and
            services['admin']['networks']['admin-ingress']['ipv4_address'] == '192.0.2.10',
            'Effective ingress network mismatch')
    for key in ('KIRA_SERVER3_HOST_PEER', 'KIRA_SERVER3_ADMIN_ADDRESS'):
        missing = ''.join(line + '\n' for line in fixtures['ingress.env'].splitlines()
                          if not line.startswith(key + '='))
        for state, contents in (('missing', missing), ('blank', missing + key + '=\n')):
            (work / 'bad.env').write_text(contents)
            code, _, diagnostics = check.command('compose-' + state + '-' + key,
                                                 command('bad.env', '--quiet'), expected=None)
            require(code == 1 and key + ' is required' in diagnostics,
                    'Mandatory peer rejection not established')
    check.result['compose'] = {'positive': True, 'effective_model': True, 'mandatory_peer_negatives': 4}


def source_checks(check):
    path = BACKEND / 'deploy/server3/kira-deploy'
    check.command('deploy-bash-syntax', ['bash', '-n', str(path)], seconds=10)
    source = path.read_text()
    require('--env-file "$images_file" --env-file "$ingress_file" "$@"' in source and
            '--profile tools config --quiet >/dev/null 2>&1' in source, 'Preflight helper mismatch')
    for component in ('backend', 'web', 'admin'):
        match = re.search(r'(?ms)^activate_' + component + r'\(\) \{\n.*?^\}', source)
        require(match is not None, 'Missing activation source')
        body = match.group()
        gate = 'KIRA_' + component.upper() + '_IMAGE="$image" preflight_configuration'
        require(body.index(gate) < body.index('docker image inspect') < body.index('compose up'),
                'Candidate preflight source ordering mismatch')
        if component == 'backend':
            require(body.index(gate) < body.index('prepare_tutorial_media_volume') < body.index('backup_database'),
                    'Backend preflight mutation ordering mismatch')
    check.result['deploy_helper_source_only'] = True


def nginx_checks(check, image):
    work, le = check.work, check.work / 'letsencrypt'
    le.mkdir()
    check.command('synthetic-certificate', ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                  '-days', '1', '-subj', '/CN=syntax.invalid', '-keyout', str(work / 'key.pem'),
                  '-out', str(work / 'cert.pem')])
    for domain in ('api.kiramanga.me', 'admin.kiramanga.me'):
        live = le / 'live' / domain
        live.mkdir(parents=True)
        shutil.copyfile(work / 'cert.pem', live / 'fullchain.pem')
        shutil.copyfile(work / 'key.pem', live / 'privkey.pem')
    (le / 'options-ssl-nginx.conf').write_text('ssl_protocols TLSv1.2 TLSv1.3;\n')
    check.command('synthetic-dh-parameters', ['openssl', 'genpkey', '-genparam', '-algorithm', 'DH',
                  '-pkeyopt', 'group:ffdhe2048', '-out', str(le / 'ssl-dhparams.pem')])
    check.command('pull-pinned-nginx-tool', ['docker', 'pull', image], seconds=120)
    check.result['nginx'] = {}
    for variant, vhosts in (('http', ['api.kiramanga.me.http.conf']),
                            ('tls', ['api.kiramanga.me.tls.conf', 'admin.kiramanga.me.tls.conf'])):
        config = work / (variant + '.conf')
        config.write_text('pid /tmp/nginx.pid;\nerror_log stderr;\nevents {}\nhttp {\naccess_log off;\n' +
                          ''.join('include /vhosts/' + name + ';\n' for name in vhosts) + '}\n')
        (check.root / 'container-intent').write_text(check.owner)
        _, _, diagnostics = check.command('nginx-test-' + variant, [
            'docker', 'run', '--rm', '--pull=never', '--name', 'backend10-config-' + check.owner + '-' + variant,
            '--label', LABEL + '=' + check.owner, '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--user', str(os.getuid()) + ':' + str(os.getgid()),
            '--memory', '128m', '--cpus', '1', '--pids-limit', '32',
            '--tmpfs', '/tmp:rw,nosuid,noexec,size=16m,mode=1777',
            '--tmpfs', '/var/cache/nginx:rw,nosuid,noexec,size=16m,mode=1777',
            '--mount', 'type=bind,src=' + str(work) + ',dst=/check,readonly',
            '--mount', 'type=bind,src=' + str(le) + ',dst=/etc/letsencrypt,readonly',
            '--mount', 'type=bind,src=' + str(BACKEND / 'deploy/server3/nginx') + ',dst=/vhosts,readonly',
            '--entrypoint', 'nginx', image, '-t', '-q', '-v', '-e', 'stderr', '-c', '/check/' + variant + '.conf',
        ], seconds=30)
        version = re.search(r'(?m)^nginx version: (nginx/[0-9][0-9A-Za-z.+~-]*)$', diagnostics)
        require(version is not None, 'Missing Nginx version receipt')
        check.result['nginx'][variant] = {'passed': True, 'version': version.group(1), 'vhosts': vhosts}


def write_result(root, result):
    (root / 'reports/result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


def validation(data):
    root, owner = context()
    root.mkdir(mode=0o700, exist_ok=False)
    (root / 'owner.json').write_text(json.dumps({'owner': owner, 'carrier': os.environ['GITHUB_SHA']}))
    (root / 'reports').mkdir(mode=0o700)
    result = {'status': 'FAIL', 'targets': data, 'checks_passed': False, 'final_cleanup': False,
              'limits': 'Config syntax only; installed Engine>=28, NAT/firewall/isolation, Nginx global policy '
                        'and actual ingress peers still require external verification.'}
    check = Checks(root, owner, result)
    try:
        for name, repo, expected in (('backend', BACKEND, data['backend']['sha']),
                                     ('carrier', CONTROL, os.environ['GITHUB_SHA'])):
            actual = check.command(name + '-sha', ['git', '-C', str(repo), 'rev-parse', 'HEAD'], seconds=5)[1].strip()
            require(actual == expected, 'Source SHA mismatch: ' + name)
            require(not check.command(name + '-clean', ['git', '-C', str(repo), 'status', '--porcelain'],
                                      seconds=5)[1].strip(), 'Dirty checkout: ' + name)
            result[name + '_sha'] = actual
        result['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['source_sha256'] = {name: hashlib.sha256((BACKEND / name).read_bytes()).hexdigest() for name in FILES}
        docker = check.command('docker-version', ['docker', 'version', '--format', '{{.Client.Version}} {{.Server.Version}}'])[1].strip()
        compose = check.command('compose-version', ['docker', 'compose', 'version', '--short'])[1].strip()
        openssl = re.match(r'OpenSSL ([0-9][0-9A-Za-z.+~-]*)\b',
                           check.command('openssl-version', ['openssl', 'version'])[1])
        require(re.fullmatch(r'[0-9A-Za-z.+~_-]+ [0-9A-Za-z.+~_-]+', docker) and
                re.fullmatch(r'v?[0-9][0-9A-Za-z.+~_-]*', compose) and openssl,
                'Unexpected tool version output')
        result['versions'] = {'docker_client_server': docker, 'compose': compose,
                              'openssl': openssl.group(1), 'python': sys.version.split()[0]}
        source_checks(check)
        compose_checks(check)
        nginx_checks(check, data['nginx']['image'])
        require(not check.command('backend-still-clean', ['git', '-C', str(BACKEND), 'status', '--porcelain'],
                                  seconds=5)[1].strip(), 'Backend checkout changed')
        require(not CANCELLED, 'Validation cancelled')
        result['checks_passed'] = True
    except CheckFailure as failure:
        result['failure'] = str(failure)
        check.note('FAIL: ' + str(failure))
    except Exception as failure:
        result['failure'] = 'Validation aborted: ' + type(failure).__name__
        check.note(result['failure'])  # Never serialize subprocess exceptions or raw parser output.
    finally:
        result['first_cleanup'] = check.cleanup()
        result['cancelled'] = CANCELLED
        ok = result['checks_passed'] and result['first_cleanup'] and not CANCELLED
        result['status'] = 'CHECKS_PASSED_PENDING_FINAL_CLEANUP' if ok else 'FAIL'
        write_result(root, result)
    return 0 if ok else 1


def final_cleanup():
    root, owner = context()
    if not root.exists():
        print('No owned validation outputs were created')
        return 0
    require(json.loads((root / 'owner.json').read_text()) ==
            {'owner': owner, 'carrier': os.environ['GITHUB_SHA']}, 'Wrong run ownership marker')
    report = root / 'reports/result.json'
    result = json.loads(report.read_text()) if report.exists() else {'checks_passed': False, 'status': 'FAIL'}
    check = Checks(root, owner, result)
    result['final_cleanup'] = check.cleanup()
    result['final_cleanup_cancelled'] = CANCELLED
    ok = (result.get('status') == 'CHECKS_PASSED_PENDING_FINAL_CLEANUP'
          and os.environ.get('BACKEND10_VALIDATION_OUTCOME') == 'success'
          and result.get('checks_passed') and result.get('first_cleanup') and result['final_cleanup']
          and not result.get('cancelled') and not CANCELLED)
    result['status'] = 'PASS' if ok else 'FAIL'
    check.note('FINAL ' + result['status'] + '; config-only, not installed-host acceptance')
    write_result(root, result)
    return 0 if result['final_cleanup'] and not CANCELLED else 1


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-targets', action='store_true')
    mode.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    try:
        data = targets()  # Must precede context creation, checkout outputs, or any subprocess.
        if args.check_targets:
            with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
                output.write('backend_sha=' + data['backend']['sha'] + '\n')
            print('Primary-bound Backend SHA and official Nginx digest accepted')
            return 0
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        return final_cleanup() if args.cleanup else validation(data)
    except CheckFailure as failure:
        print('FAIL: ' + str(failure))
    except Exception as failure:
        print('FAIL: config harness aborted (' + type(failure).__name__ + ')')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
