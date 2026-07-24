# Kira Tutorial Studio

Local administration dashboard for Kira tutorial categories, bilingual tutorial revisions,
publishing, rollback, ordering, archiving, and screenshot media.

## Run locally

1. Copy `.env.example` to `.env.local` and change `KIRA_BACKEND_URL` when using a local backend.
2. Run `npm install`.
3. Run `npm run dev` and open `http://localhost:3100`.
4. Sign in with an existing Kira `ADMIN` account.

The browser never receives the backend URL or stores the JWT in local storage. Next.js proxies the
small allowlisted tutorial-admin API surface and keeps the access token in an HTTP-only cookie.
