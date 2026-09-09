# Kira Admin Studio

Private administration dashboard for Kira source catalogs and tutorials. Source operations include
optimistic server drafts, strict validation, quick single-source publishing, atomic multi-source
changesets, lifecycle/order management, immutable revision history, and safe audit metadata.

## Run locally

1. Copy `.env.example` to `.env.local`. Set `KIRA_BACKEND_URL` to the API and
   `KIRA_ADMIN_ORIGIN` to the exact browser origin (for example `http://localhost:3100` locally).
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

Pushes to `main` first run the full CI and read-only container smoke test. Only a successful CI run
may start the protected `production` deployment, which builds the exact verified commit and streams
`kira-admin:<40-character-sha>` through server3's restricted deployment gateway. The server
health-gates the new container and restores the previously configured image on failure.

The GitHub `production` Environment contains `SERVER3_HOST`, `SERVER3_PORT`, and `SERVER3_USER`
variables plus `SERVER3_SSH_PRIVATE_KEY` and `SERVER3_KNOWN_HOSTS` secrets. Runtime configuration
stays on server3 in `/opt/kira/admin.env`:

```text
KIRA_BACKEND_URL=http://backend:8080
KIRA_ADMIN_ORIGIN=https://admin.kiramanga.me
```

No ADMIN password or backend JWT is deployed with the dashboard. Operators authenticate through the
existing backend login; the BFF keeps the resulting short-lived credentials in secure HTTP-only
cookies.

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
