"""Private scoped config/header checks. Never build, start an app, or execute kira-deploy."""

import argparse
import hashlib
import http.client
import importlib.util
import io
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
HSTS_HOSTS = ('kiramanga.me', 'www.kiramanga.me', 'api.kiramanga.me', 'admin.kiramanga.me')
HSTS_VHOSTS = ('api.kiramanga.me', 'admin.kiramanga.me', 'kiramanga.me')
HSTS_FILES = tuple('deploy/server3/nginx/' + host + '.' + variant + '.conf'
                   for host in HSTS_VHOSTS for variant in ('http', 'tls')) + (
    'deploy/server3/verify_hsts.py', 'deploy/server3/test_verify_hsts.py',
)
HSTS_IMAGE = 'docker.io/library/nginx@sha256:0dcc88822d45581e65ae329f8be769762bf628d3b2bb7d2a077d4aa5c98b30e3'
UPSTREAM_POLICY = 'max-age=31536000; includeSubDomains'
ACME_PATH = '/.well-known/acme-challenge/kira-owned-hsts-check'
ACME_BODY = 'kira-owned-acme-fixture\n'
CANCELLED = False


class CheckFailure(Exception):
    pass


def require(condition, message):
    if not condition:
        raise CheckFailure(message)


def targets():
    """No subprocesses or Docker access before all primary bindings pass."""
    data = json.loads((CONTROL / 'ci/backend10-config.targets.json').read_text())
    require(isinstance(data, dict) and type(data.get('schemaVersion')) is int and
            data['schemaVersion'] in (1, 2), 'Invalid target schema')
    keys = {'schemaVersion', 'backend', 'nginx'}
    if data['schemaVersion'] == 2:
        keys |= {'scope', 'sourceSha256'}
    require(set(data) == keys, 'Invalid target fields')
    backend, nginx = data['backend'], data['nginx']
    require(isinstance(backend, dict) and set(backend) == {'repository', 'sha'} and
            backend['repository'] == 'kira-manga/Kira-backend', 'Wrong Backend repository')
    require(isinstance(backend['sha'], str) and re.fullmatch(r'[0-9a-f]{40}', backend['sha']) and
            backend['sha'] != '0' * 40, 'Primary must bind the exact Backend issue commit')
    require(isinstance(nginx, dict) and set(nginx) == {'image'} and isinstance(nginx['image'], str) and
            re.fullmatch(r'docker\.io/library/nginx@sha256:[0-9a-f]{64}', nginx['image']) and
            not nginx['image'].endswith(':' + '0' * 64),
            'Primary must bind an official Nginx image digest')
    if data['schemaVersion'] == 2:
        require(data['scope'] == 'server3-hsts', 'Unknown validation scope')
        require(nginx['image'] == HSTS_IMAGE, 'HSTS checks require the reviewed Nginx 1.28.3 image')
        hashes = data['sourceSha256']
        require(isinstance(hashes, dict) and set(hashes) == set(HSTS_FILES) and
                all(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) and value != '0' * 64
                    for value in hashes.values()), 'Bind all six HSTS templates and the helper/test sources')
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


def hsts_certificate(check):
    work = check.work
    check.command('synthetic-ca', ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                  '-days', '1', '-subj', '/CN=Kira-owned-config-CA', '-keyout', str(work / 'ca-key.pem'),
                  '-out', str(work / 'ca.pem'), '-addext', 'basicConstraints=critical,CA:TRUE'])
    check.command('synthetic-certificate-request', ['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes',
                  '-subj', '/CN=kiramanga.me', '-keyout', str(work / 'key.pem'), '-out', str(work / 'server.csr')])
    (work / 'certificate.ext').write_text(
        'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n'
        'extendedKeyUsage=serverAuth\nsubjectAltName=' + ','.join('DNS:' + host for host in HSTS_HOSTS) + '\n')
    check.command('synthetic-signed-certificate', ['openssl', 'x509', '-req', '-in', str(work / 'server.csr'),
                  '-CA', str(work / 'ca.pem'), '-CAkey', str(work / 'ca-key.pem'), '-set_serial', '1',
                  '-days', '1', '-extfile', str(work / 'certificate.ext'), '-out', str(work / 'cert.pem')])


def nginx_response(check, container, label, scheme, host, path, port=None, extra=()):
    """One bounded, non-following curl hop inside this network-none container. No public resolver."""
    port = port or (443 if scheme == 'https' else 80)
    require(host in HSTS_HOSTS and scheme in ('http', 'https') and port in (80, 443, 18080, 18081, 18082),
            'Unexpected synthetic response target')
    url = scheme + '://' + host + ((':' + str(port)) if port not in (80, 443) else '') + path
    _, output, _ = check.command(label, [
        'docker', 'exec', container, 'curl', '--disable', '--silent', '--show-error', '--http1.1',
        '--noproxy', '*', '--proto', '=http,https', '--max-redirs', '0',
        '--connect-timeout', '2', '--max-time', '5', '--max-filesize', '65536',
        '--resolve', host + ':' + str(port) + ':127.0.0.1', '--cacert', '/check/ca.pem', '--include',
        *extra, url,
    ], seconds=10)
    status_line, separator, rest = output.partition('\r\n')
    status = re.fullmatch(r'HTTP/1\.[01] ([2-5][0-9]{2}) [^\r\n]*', status_line)
    raw_headers, boundary, body = rest.partition('\r\n\r\n')
    require(separator and status and boundary and raw_headers.isascii(), label + ': invalid response framing')
    headers = http.client.parse_headers(io.BytesIO((raw_headers + '\r\n\r\n').encode('ascii')))
    require(not headers.defects, label + ': malformed response headers')
    return url, int(status.group(1)), list(headers.raw_items()), body


def hsts_header_checks(check, container, variant, helper):
    """Use the actual Backend helper's pure contract, never its public-host request/CLI path."""
    rows = check.result['nginx'][variant]['responses'] = []
    path = helper.HTTP_PROBE_PATH

    def probe(label, scheme, host, expected, policy='edge', origin=None, port=None,
              request_path=path, extra=(), location=None, body=None):
        url, status, headers, content = nginx_response(check, container, variant + '-' + label,
                                                       scheme, host, request_path, port, extra)
        values = lambda name: [value.strip(' \t') for field, value in headers if field.lower() == name]
        require(status == expected, label + ': unexpected HTTP status')
        if policy == 'edge':
            try:
                helper.check_response(url, status, headers)
            except helper.CheckFailure:
                raise CheckFailure(label + ': HSTS/redirect policy mismatch') from None
        else:
            require(values('strict-transport-security') == ([UPSTREAM_POLICY] if policy == 'upstream' else []),
                    label + ': upstream/bootstrap/ACME policy mismatch')
        require(values('x-kira-fixture-upstream') == ([origin] if origin else []), label + ': wrong response origin')
        if origin:
            require(values('x-kira-fixture-uri') == [request_path], label + ': changed proxy path/query')
        if location is not None:
            require(values('location') == [location], label + ': wrong redirect target')
        if body is not None:
            require(content == body, label + ': ACME did not serve the owned token')
        row = {'probe': label, 'status': status, 'hsts_fields': len(values('strict-transport-security')), 'passed': True}
        rows.append(row)
        check.note(json.dumps({'variant': variant, **row}, sort_keys=True))

    # Positive controls show that each real upstream emits a conflicting STS field before edge suppression.
    for component, port in (('api', 18080), ('web', 18081), ('admin', 18082)):
        probe('upstream-' + component, 'http', 'kiramanga.me', 200, 'upstream', component, port)
    if variant == 'tls':
        for host in HSTS_HOSTS:
            origin = {'kiramanga.me': 'web', 'api.kiramanga.me': 'api', 'admin.kiramanga.me': 'admin'}.get(host)
            probe('https-' + host, 'https', host, 200 if origin else 301, origin=origin,
                  location=None if origin else 'https://kiramanga.me' + path)
        error_path = '/__kira_upstream_error__'
        probe('upstream-error-control', 'http', 'api.kiramanga.me', 503, 'upstream', 'api', 18080,
              request_path=error_path)
        probe('https-upstream-error', 'https', 'api.kiramanga.me', 503, origin='api', request_path=error_path)
        probe('https-local-body-limit', 'https', 'api.kiramanga.me', 413,
              extra=('--request', 'POST', '--header', 'Content-Length: 6291456', '--header', 'Expect:'))
        for host in HSTS_HOSTS:
            probe('http-redirect-' + host, 'http', host, 301)
    else:
        for host, origin in (('api.kiramanga.me', 'api'), ('kiramanga.me', 'web'), ('www.kiramanga.me', 'web')):
            probe('http-bootstrap-' + host, 'http', host, 200, 'none', origin)
        probe('http-admin-redirect', 'http', 'admin.kiramanga.me', 301)
    for host in HSTS_HOSTS:
        probe('http-acme-' + host, 'http', host, 200, 'none', request_path=ACME_PATH, body=ACME_BODY)


def nginx_checks(check, image, hsts=False):
    work, le = check.work, check.work / 'letsencrypt'
    if hsts:
        require(os.getuid() != 0, 'HSTS containers require the nonroot hosted runner UID')
    le.mkdir()
    if hsts:
        hsts_certificate(check)
    else:
        check.command('synthetic-certificate', ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                      '-days', '1', '-subj', '/CN=syntax.invalid', '-keyout', str(work / 'key.pem'),
                      '-out', str(work / 'cert.pem')])
    for domain in (HSTS_VHOSTS if hsts else ('api.kiramanga.me', 'admin.kiramanga.me')):
        live = le / 'live' / domain
        live.mkdir(parents=True)
        shutil.copyfile(work / 'cert.pem', live / 'fullchain.pem')
        shutil.copyfile(work / 'key.pem', live / 'privkey.pem')
    (le / 'options-ssl-nginx.conf').write_text('ssl_protocols TLSv1.2 TLSv1.3;\n')
    check.command('synthetic-dh-parameters', ['openssl', 'genpkey', '-genparam', '-algorithm', 'DH',
                  '-pkeyopt', 'group:ffdhe2048', '-out', str(le / 'ssl-dhparams.pem')])
    check.command('pull-pinned-nginx-tool', ['docker', 'pull', image], seconds=120)
    check.result['nginx'] = {}
    variants = (('http', ['api.kiramanga.me.http.conf']),
                ('tls', ['api.kiramanga.me.tls.conf', 'admin.kiramanga.me.tls.conf']))
    upstreams, helper = '', None
    if hsts:
        variants = tuple((variant, [host + '.' + variant + '.conf' for host in HSTS_VHOSTS])
                         for variant in ('http', 'tls'))
        token = work / 'acme' / ACME_PATH.lstrip('/')
        token.parent.mkdir(parents=True)
        token.write_text(ACME_BODY)
        for component, port in (('api', 18080), ('web', 18081), ('admin', 18082)):
            upstreams += ('server { listen 127.0.0.1:' + str(port) + ';\n'
                          'add_header Strict-Transport-Security "' + UPSTREAM_POLICY + '" always;\n'
                          'add_header X-Kira-Fixture-Upstream ' + component + ' always;\n'
                          'add_header X-Kira-Fixture-URI $request_uri always;\n'
                          'location = /__kira_upstream_error__ { return 503; }\n'
                          'location / { return 200 "synthetic-' + component + '\\n"; }\n}\n')
        sys.dont_write_bytecode = True  # Keep the exact checkout clean even outside the workflow's -B mode.
        spec = importlib.util.spec_from_file_location('backend31_hsts', BACKEND / 'deploy/server3/verify_hsts.py')
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)  # Hash-bound source import; no --check, fetch_headers, or test suite.
        require(helper.HOSTS == HSTS_HOSTS and helper.POLICY == 'max-age=86400', 'Unexpected HSTS helper contract')
        check.result['helper_unit_tests'] = 'Not run here; primary-owned local validation'
    for variant, vhosts in variants:
        config = work / (variant + '.conf')
        config.write_text('pid /tmp/nginx.pid;\nerror_log stderr;\nevents {}\nhttp {\naccess_log off;\n' +
                          ''.join('include /vhosts/' + name + ';\n' for name in vhosts) + upstreams + '}\n')
        (check.root / 'container-intent').write_text(check.owner)
        name = 'backend10-config-' + check.owner + '-' + variant
        launch = [
            'docker', 'run', '--rm', '--pull=never', '--name', name,
            '--label', LABEL + '=' + check.owner, '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--user', str(os.getuid()) + ':' + str(os.getgid()),
            '--memory', '128m', '--cpus', '1', '--pids-limit', '32',
            '--tmpfs', '/tmp:rw,nosuid,noexec,size=16m,mode=1777',
            '--tmpfs', '/var/cache/nginx:rw,nosuid,noexec,size=16m,mode=1777',
            '--mount', 'type=bind,src=' + str(work) + ',dst=/check,readonly',
            '--mount', 'type=bind,src=' + str(le) + ',dst=/etc/letsencrypt,readonly',
            '--mount', 'type=bind,src=' + str(BACKEND / 'deploy/server3/nginx') + ',dst=/vhosts,readonly',
        ]
        if hsts:
            # Namespaced only: the same nonroot/no-capability image must bind the unmodified 80/443 templates.
            launch += ['--detach', '--sysctl', 'net.ipv4.ip_unprivileged_port_start=0',
                       '--mount', 'type=bind,src=' + str(work / 'acme') + ',dst=/var/www/letsencrypt,readonly']
        launch += ['--entrypoint', 'nginx', image]
        arguments = ['-e', 'stderr', '-c', '/check/' + variant + '.conf']
        if hsts:
            container = check.command('nginx-start-' + variant,
                                      launch + ['-g', 'daemon off;', *arguments], seconds=30)[1].strip()
            require(re.fullmatch(r'[0-9a-f]{64}', container), 'Missing owned Nginx container ID')
            command = ['docker', 'exec', container, 'nginx']
        else:
            command = launch
        _, _, diagnostics = check.command('nginx-test-' + variant, command + ['-t', '-q', '-v', *arguments], seconds=30)
        version = re.search(r'(?m)^nginx version: (nginx/[0-9][0-9A-Za-z.+~-]*)$', diagnostics)
        require(version is not None, 'Missing Nginx version receipt')
        check.result['nginx'][variant] = {'passed': not hsts, 'version': version.group(1), 'vhosts': vhosts}
        if hsts:
            check.result['nginx'][variant]['syntax_passed'] = True
            require(version.group(1) == 'nginx/1.28.3', 'Unexpected HSTS Nginx version')
            # This exact official image installs curl/ca-certificates; fail, never install/rebuild on absence.
            curl = check.command('curl-version-' + variant, ['docker', 'exec', container, 'curl', '--disable', '--version'])[1]
            curl_version = re.match(r'curl ([0-9][0-9A-Za-z.+~-]*)\b', curl)
            protocols = re.search(r'(?m)^Protocols: (.+)$', curl)
            require(curl_version and protocols and {'http', 'https'} <= set(protocols.group(1).split()),
                    'Pinned image lacks the expected HTTP(S) curl tool')
            check.result['nginx'][variant]['curl_version'] = curl_version.group(1)
            hsts_header_checks(check, container, variant, helper)
            check.command('nginx-remove-' + variant, ['docker', 'rm', '-f', container], seconds=15)
            check.result['nginx'][variant]['passed'] = True


def write_result(root, result):
    (root / 'reports/result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


def validation(data):
    hsts = data.get('scope') == 'server3-hsts'
    root, owner = context()
    root.mkdir(mode=0o700, exist_ok=False)
    (root / 'owner.json').write_text(json.dumps({'owner': owner, 'carrier': os.environ['GITHUB_SHA']}))
    (root / 'reports').mkdir(mode=0o700)
    limits = ('Isolated unmodified Nginx templates and synthetic response headers only; helper unit tests '
              'are primary-owned/local. Installed/global/Certbot policy, reload, public TLS, actual '
              'normal/error/HTTP/ACME/bootstrap behavior and rollout require EXTERNAL verification.' if hsts else
              'Config syntax only; installed Engine>=28, NAT/firewall/isolation, Nginx global policy '
              'and actual ingress peers still require external verification.')
    result = {'status': 'FAIL', 'targets': data, 'checks_passed': False, 'final_cleanup': False,
              'scope': data.get('scope', 'backend10-config'), 'limits': limits}
    check = Checks(root, owner, result)
    try:
        result['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['source_sha256'] = {name: hashlib.sha256((BACKEND / name).read_bytes()).hexdigest()
                                   for name in (HSTS_FILES if hsts else FILES)}
        if hsts:
            require(result['source_sha256'] == data['sourceSha256'], 'HSTS source hash mismatch')
        for name, repo, expected in (('backend', BACKEND, data['backend']['sha']),
                                     ('carrier', CONTROL, os.environ['GITHUB_SHA'])):
            actual = check.command(name + '-sha', ['git', '-C', str(repo), 'rev-parse', 'HEAD'], seconds=5)[1].strip()
            require(actual == expected, 'Source SHA mismatch: ' + name)
            require(not check.command(name + '-clean', ['git', '-C', str(repo), 'status', '--porcelain'],
                                      seconds=5)[1].strip(), 'Dirty checkout: ' + name)
            result[name + '_sha'] = actual
        docker = check.command('docker-version', ['docker', 'version', '--format', '{{.Client.Version}} {{.Server.Version}}'])[1].strip()
        compose = None if hsts else check.command('compose-version', ['docker', 'compose', 'version', '--short'])[1].strip()
        openssl = re.match(r'OpenSSL ([0-9][0-9A-Za-z.+~-]*)\b',
                           check.command('openssl-version', ['openssl', 'version'])[1])
        require(re.fullmatch(r'[0-9A-Za-z.+~_-]+ [0-9A-Za-z.+~_-]+', docker) and
                (hsts or re.fullmatch(r'v?[0-9][0-9A-Za-z.+~_-]*', compose)) and openssl,
                'Unexpected tool version output')
        result['versions'] = {'docker_client_server': docker,
                              'openssl': openssl.group(1), 'python': sys.version.split()[0]}
        if not hsts:
            result['versions']['compose'] = compose
            source_checks(check)
            compose_checks(check)
        nginx_checks(check, data['nginx']['image'], hsts=hsts)
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
    check.note('FINAL ' + result['status'] + '; isolated config/headers only, not installed-host acceptance')
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
