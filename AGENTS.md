# Repository Guidelines

## Project Structure

This repository is the private Next.js administration dashboard for Kira. App Router pages and
server-only API handlers live in `src/app/`. Interactive views are in `src/components/`, shared
browser types and API helpers are in `src/lib/`, and global styling is in
`src/app/globals.css`. The production backend URL is server-only configuration.

## Development Commands

- `npm ci` installs the exact locked dependency graph.
- `npm run dev` starts the dashboard at `http://localhost:3100`.
- `npm run lint` runs the Next.js ESLint rules.
- `npm run typecheck` performs strict TypeScript checking without emitting files.
- `npm test` runs the BFF allowlist/security regression suite.
- `npm run build` creates the production standalone build.
- `npm run verify` runs lint, type-checking, and the production build.

## Style and Naming

Use strict TypeScript, two-space indentation, single quotes, and semicolons. React components use
PascalCase (`SourcesView`); functions and variables use camelCase. Keep server-only code in route
handlers or files named `server-*`; never import it into a client component. Reuse the existing
design tokens and UI primitives before adding new visual patterns.

## Security and Testing

Never expose backend JWTs, step-up proofs, passwords, or backend URLs to browser-readable storage.
All mutations must pass the same-origin and CSRF checks in the BFF. Keep proxy routes allowlisted;
do not add catch-all access to destructive backend endpoints. Run `npm run verify` before every
commit and manually exercise login, session expiry, stale ETags, validation failure, and step-up
consumption when changing those flows.

## Commits and Pull Requests

Use concise, imperative commit subjects such as `Add atomic source changeset editor`. Keep commits
focused. Pull requests should describe the operator workflow, security impact, verification run,
and screenshots for visible UI changes. Never include `.env.local`, credentials, or production
response bodies.
