# Kira Admin Studio

Private administration dashboard for Kira source catalogs and tutorials. Source operations include
optimistic server drafts, strict validation, quick single-source publishing, atomic multi-source
changesets, lifecycle/order management, immutable revision history, and safe audit metadata.

## Run locally

1. Copy `.env.example` to `.env.local`. Set `KIRA_BACKEND_URL` to the API and
   `KIRA_ADMIN_ORIGIN` to the exact browser origin (for example `http://localhost:3100` locally).
   Set `KIRA_ADMIN_SESSION_SECRET` to an independently generated secret as described below.
2. Run `npm install`.
3. Run `npm run dev` and open the configured admin origin.
4. Sign in with an existing Kira `ADMIN` account.

The browser never receives the backend URL or stores JWTs or step-up proofs in browser-readable
storage. Next.js proxies a narrow allowlist, keeps credentials in HTTP-only same-site cookies, and
requires same-origin CSRF tokens for every mutation.

## Verification

Run `npm run verify` before committing. It runs ESLint, strict TypeScript, the BFF route-policy
regression tests, and a standalone production build. Run `npm audit --audit-level=high` as part of
dependency changes; the committed lockfile currently resolves with zero known vulnerabilities.

## Production deployment

**Deployment is currently externally blocked, not operationally protected.** The 2026-09-09 policy
receipts show a private repository with no production reviewers or deployment-ref policy, admin
bypass enabled, and an unavailable main-protection API. Source changes and fixture tests do not fix
account enforcement. An owner-authorized, supported private-repository approval/protection setup
is required; **Pro alone does not provide the required private reviewer/bypass features**. Do not
make the repository public, change settings/plans, or provision credentials merely to pass a gate.

This release path removes automatic deployment. Main-push CI builds once, smoke-tests the actual
image ID, confirms `kira-admin:<40-character-sha>` still resolves to it, exports that tag once, and
scans that exact export. The image and bounded receipt become one immutable private artifact.
The existing production npm audit remains a separate, complementary gate.

Promotion is manual through **Deploy server3**, from literal `main`, with four explicit inputs:

- `run_id`: completed, successful **push/main CI** producer run ID.
- `run_attempt`: its exact successful attempt; a later rerun makes the old attempt ineligible.
- `artifact_id`: the immutable `admin-image-<run_id>-<run_attempt>` artifact ID.
- `zip_sha256`: the outer artifact ZIP SHA-256, 64 lowercase hexadecimal characters.

Preflight authenticates/rechecks the run, source SHA/tree, artifact and current-main release-contract
bytes, then displays a frozen candidate summary **before native production-environment approval**.
Dispatch is not approval. Old producer and old promotion/checker revisions cannot approve one
another after the current-main contract changes. A deleted, expired, replaced, ambiguous or
newly rerun candidate fails; a promotion rerun must reuse exactly the selected artifact or fail,
never resolve “latest” or rebuild a substitute.

The credentialed job uses only its trusted promotion revision, rechecks the frozen candidate and
native policy after approval, loads/inspects the image ID/platform/revision/tag, and streams the
**original verified gzip bytes** through the fixed `deploy admin <40hex>` gateway. It does not
install dependencies, build, scan, or run candidate code/containers. SSH uses pinned known hosts,
bounded commands and private owned scratch/key cleanup, never shared `~/.ssh` files. The existing
server gateway health-gates deployment and restores the prior image on failure; installed behavior
and the actual remote running-image identity still require separate authorized verification.

### External protection and read authority

Both preflight and the post-approval policy step require repository secret
`ADMIN8_POLICY_READ_TOKEN`: an **owner-authorized, single-repository, read-only** credential with
Administration:read and the required environment/metadata read capabilities. Ordinary
`GITHUB_TOKEN` contents/actions:read must not be assumed sufficient for full main-protection reads.
Only the policy API step receives this separate token, not download, build, scanner or SSH commands.
Its authorization and actual API visibility are external prerequisites; no token is provisioned here.

The narrow checker requires all of the following, with complete readable API responses:

- Native production human reviewers as the sole protection rule, self-review prevented, admin bypass
  disabled; exactly one custom environment policy `{type: branch, name: main}` with no extra ref/tag.
- Explicit **User** reviewers. Teams are unsupported by this narrow checker, not inherently insecure.
- Main protection enforcing PR approval, dismissing stale reviews, requiring last-push approval,
  applying to admins, with no PR-review bypass, force-push or deletion allowance.
- Strict required `verify` and `container` checks bound to the GitHub Actions app.

Missing credentials, unsupported/unknown fields, incomplete lists and API errors fail closed.
Metadata checks are not substitute approvals and cannot make revocation atomic. Account support,
real native approval/self-review/bypass enforcement and revocation races remain **external
verification required**, even after an offline suite or no-deploy rehearsal succeeds.

### Artifact and scan contract

The helper distinguishes the **outer ZIP digest**, **inner `image.tar.gz` digest**, and **Docker
image ID**; these are different identities. Authenticated ZIP download never forwards the API token
to signed storage. Only regular `image.tar.gz`, `receipt.json`, and `scan.json` ZIP members are
accepted; actual byte limits are 512 MiB each for ZIP/gzip, 2 GiB expanded Docker tar, 16 KiB receipt,
and 8 MiB scan report. ZIP64/comments/extra entries are unsupported. These are initial fail-safe
ceilings, not measured image sizes; do not automatically relax them. Artifacts have three-day private
retention, compression level zero and no overwrite. A receipt is not an independent signature: its
authority depends on the protected producer, authenticated artifact identity and native approval.

Grype **0.118.0**, checksum-pinned in `scripts/ci/image_release.py`, scans the exported runtime image
with explicit `scripts/ci/grype.yaml`. HIGH/CRITICAL findings **including unfixed**, every nonzero tool
exit and DB failures block receipt publication. DB update checks, hash validation and a maximum
120-hour DB age are mandatory; ignores, VEX, exclusions and only-fixed fallbacks are forbidden.
Implicit kernel-header ignore rules are explicitly disabled. The receipt binds actual tool/DB/scan
metadata and report digest. This is an identified CI-time scan, not a current-at-deployment rescan
or proof of no vulnerabilities; bundled application discovery can be incomplete. Bounded failed
scan diagnostics may be retained separately, but are never promotion candidates.

### Offline checks and no-deploy rehearsal

On Linux with Python 3.11+, the focused standard-library suite is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/ci -p 'test_*.py'
```

The separately authorized **CI** manual input `purpose: no-deploy-rehearsal` uses one producer and
one fresh secretless consumer job. The consumer downloads/verifies/loads/smokes the **same immutable
artifact twice**, without rebuilding. The manual path skips the outer UI verification job because
the unchanged Dockerfile already runs `npm run verify`; it retains the production npm audit.
Manual/feature rehearsal receipts are **never** production candidates. There is no production
environment, policy token, SSH secret or deployment in this rehearsal.

Workflow registration/dispatch availability on a private nondefault ref must be checked by the
coordinating owner. Do not merge to main or change the default branch merely to register dispatch,
and do not invent another trigger to bypass a concrete API restriction. Fixture success does not
prove GitHub ZIP metadata, real scanner output, Docker image-ID compatibility, or production policy.
The one authorized real-image rehearsal must record source/tree, run/attempt, artifact ID/ZIP digest,
image ID/platform, gzip digest and observed sizes; real scan failures remain blocking findings.

### Server configuration

The GitHub `production` Environment contains `SERVER3_HOST`, `SERVER3_PORT`, and `SERVER3_USER`
variables plus `SERVER3_SSH_PRIVATE_KEY` and `SERVER3_KNOWN_HOSTS` secrets. Runtime configuration
stays on server3 in `/opt/kira/admin.env`:

```text
KIRA_BACKEND_URL=http://backend:8080
KIRA_ADMIN_ORIGIN=https://admin.kiramanga.me
KIRA_ADMIN_SESSION_SECRET=<BYO random secret; never commit>
```

No ADMIN password or backend JWT is deployed with the dashboard. Operators authenticate through the
existing backend login; the BFF keeps the resulting short-lived credentials in secure HTTP-only
cookies.

### Admin session and approval identity

`KIRA_ADMIN_SESSION_SECRET` is required **at runtime**: 32–64 independently random bytes, encoded as
64–128 lowercase hexadecimal characters (an even length). Generate it privately, for example with
`openssl rand -hex 32`. Use the same value on every Admin replica and after restarts, and different
keys for independent deployments. Missing or
malformed configuration returns a generic authentication HTTP 503; there is no generated per-process
key, bearer-derived signing key, in-memory security registry, or build-time secret. Rotation requires
all operators to sign in again. Installing this BYO runtime secret remains an owner/deployment step.

Each login creates a random **G**, even if the backend happens to issue an identical JWT twice in one
second. A domain-separated HMAC binds G, JWT, CSRF and absolute expiry in a uniquely named HttpOnly
session cookie (`Path=/`). Each password verification creates a random **P** and an independently
named HttpOnly proof cookie (`Path=/api`, shared by issuer, logout and backend proxy). Its signed
envelope binds G, the exact signed session, scope, P and absolute expiry. Backend complaint grant IDs,
when supplied, stay inside that envelope; they are not browser approval selectors.

The browser stores **only the opaque G selector** in per-tab `sessionStorage`, sends it explicitly on
API/upload requests and in same-origin image URLs, and holds CSRF in memory. If storage is unavailable,
selection is memory-only and a reload requires login. No cookie scanning, newest-cookie guessing or
fallback session is allowed. G and P alone authenticate nothing. The non-secret approval ACK is exactly
`{scope, expiresAt, generation, proofId}` and belongs to the captured action/session; no global latest
proof pointer exists. Login/logout and obsolete UI completions cannot adopt a different session.

New responses set only their own immutable names. Login retires the identities captured in that login
request; logout/session rejection retires only captured names for the selected G. Delayed responses
cannot delete a newer G/P they never received. Source proof P is retired at its original `/api` path
only on a direct, non-redirected HTTP 200 from the exact changeset-apply, draft-publish or operational-mode
handler. Transport failures, redirects, 4xx/5xx and ambiguous outcomes retain it. Backend expiry and
one-time consumption remain authoritative: retention is **not** permission to reuse a consumed grant.
Complaint mutations remain closed; historical complaint-consumed metadata never clears another proof.

Processing is bounded to 16 KiB of raw Cookie headers, 128 cookie fields, four session cookies and
eight proof cookies; issuance refuses at capacity. Each signed envelope is at most 3,800 characters.
Sessions last at most 24 hours, proofs at most 15 minutes and never beyond the selected session.
Both signed expiry and cookie `Expires` are absolute; delayed delivery never renews them. Concurrent
issuances across tabs/replicas may exceed an observed admission count; this is not a distributed slot
reservation. The next over-bound request fails closed. Sign out before reaching the bound, wait for
expiry, or deliberately clear this site's cookies to recover; there is no automatic alternative selection.
An issuance arriving after logout can leave an unselected cookie until expiry, but cannot restore client
ownership. Stateless logout is local cookie retirement, not backend JWT revocation of a copied token.
Actual browser/ingress header limits may be stricter and are not verified by these fixture bounds.

Legacy fixed-name cookies are not authenticated generations and require re-login. Old proof names at
`/api/backend` are no longer read or upgraded; inaccessible legacy cookies expire naturally. Successful
login removes only captured legacy root session/CSRF names. Production rollout must coordinate the
runtime secret and re-login; build/fixture success does not verify deployment or browser operation.

### Authentication client identity

`KIRA_ADMIN_TRUSTED_INGRESS` is server-only and defaults off, including in production. Only the exact
values `true` and `false` are accepted when set. `true` also requires the exact
`KIRA_BACKEND_URL=http://backend:8080` (no trailing slash); configuration is checked when server config
loads. Other deployments retain their configurable backend URL with trust unset/false.

Enable it only after the reviewed server3 ingress topology is installed and verified: Nginx must
overwrite X-Real-IP and X-Forwarded-For with the observed peer and clear Forwarded; Admin must be
reachable only through that ingress, with host-loopback publication and a dedicated non-internal
Backend/Admin NAT bridge excluding Web. Follow the backend server3 runbook's Engine >=28.0.0,
firewall, routing and actual peer checks. Host and Backend remain trusted. Server3 Compose pins the
internal URL and opt-in, overriding env-file values. Installed isolation remains external verification;
Origin/CSRF checks alone do not authenticate the proxy.

Only login and password step-up consume one bounded numeric X-Real-IP and construct a fresh canonical
X-Forwarded-For. Incoming XFF/Forwarded chains are never copied, and the generic BFF is unchanged.
With trust off or missing/invalid/duplicate/oversized metadata, neither forwarding header is sent:
the backend falls back to the BFF peer, a **degraded shared throttle bucket**, not distinct-client isolation.
No client-IP form field, browser configuration or new secret is introduced.

## Live catalog view and post-deploy smoke

**View live catalog** opens the same-origin /api/catalog/manifest endpoint in a new tab.
Its fixed server-only GET fetches /api/v2/source-config/manifest using KIRA_BACKEND_URL;
the browser never receives that origin, and the proxy does not forward admin credentials.
It preserves the signed manifest bytes and public integrity headers, including conditional 304
responses, but disables caching for this operator view.

The view has a **1,048,576-byte decoded-body limit** and a **10-second fetch-and-body deadline**.
This is a proxy-local display budget, not a backend publication limit: larger valid manifests
return a generic 502 through this view. A no-publication 404, upstream/configuration failure 502,
or timeout 504 is not successful release verification. Do not create a publication or fall back
to an unrelated route just to make smoke pass.

After a separately authorized deployment, set KIRA_ADMIN_ORIGIN to the exact public admin origin
without a trailing slash and make one bounded, read-only request (no credentials or redirects):

    curl --fail --silent --show-error --max-time 15 --dump-header - --output /dev/null \
      "$KIRA_ADMIN_ORIGIN/api/catalog/manifest"

Require HTTP 200, application/json, ETag and X-Config-Checksum, with no-store/no-transform and
nosniff headers. Then click the actual shell link: it must open the same-origin JSON in a new tab,
show catalogRevision and sources, and never expose the backend origin or the obsolete v1/catalog
404. Do not paste production response bodies into issues or build logs. Deployment/publication
prerequisites remain external verification; the existing container root-page smoke alone does not
exercise this endpoint.
