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
