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
