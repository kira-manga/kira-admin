# Kira workspace instructions

This workspace contains two independent repositories. There is no root Gradle build.
Choose the repository first and run commands with that repository's own wrapper.

| Repository | Path | Current role |
|---|---|---|
| Kira Manga app | [`Kira manga/`](Kira%20manga/) | Kotlin Multiplatform manga reader: Android, iOS, and Desktop/JVM. Android and iOS are the shipping targets. |
| Backend | [`kira-backend/`](kira-backend/) | Single-module Spring Boot/PostgreSQL service for source-config authoring/publishing, JWT auth, admin/audit, and the echo completion API. |

The app currently ships a bundled `SourceConfigDocument` string at
`Kira manga/composeApp/src/commonMain/kotlin/me/manga/kira/sources/runtime/BundledSourcesConfig.kt`.
The backend is intended to become its remote authority. The backend owns `kcj-1` canonical JSON
and SHA-256 snapshot bytes; the app currently parses and validates the bundled/accepted document
and does not contain the backend canonicalizer. Do not describe the two sides as already sharing
byte-identical serialization without checking the current contract and tests.

## Working rules

- App tasks run from `Kira manga/` with `./gradlew`; backend tasks run from `kira-backend/` with
  `./gradlew`. The vendored parity reference has a third, separate build under
  `Kira manga/native-app/`.
- Read the nearest project `AGENTS.md` before changing code. It routes to the deeper owner docs:
  [`Kira manga/CLAUDE.md`](Kira%20manga/CLAUDE.md) and
  [`kira-backend/docs/PLAN.md`](kira-backend/docs/PLAN.md).
- Preserve existing worktree changes. Inspect each repository's `git status` and avoid unrelated
  cleanup, especially around owner-WIP files.
- Secrets are local/BYO and ignored: app Firebase files (`app/google-services.json` and
  `iosApp/iosApp/GoogleService-Info.plist`) and backend `.env`. Use the committed example files.
- `Kira manga/native-app/` and the `sources_repositry` package inside
  `Kira manga/sources/legacy/` are behavior/reference or legacy-scraper trees. Treat them as
  read-only unless the user explicitly authorizes a change.

## Cross-project contract changes

When changing a source-config field, default, validation rule, strategy name, lifecycle meaning,
or canonicalization assumption, inspect both implementations and their tests. The app-side
contract lives in `sources/contracts` and `sources/engine`; the backend mirror lives under
`sourceconfig/domain/model`, `sourceconfig/validation`, and `sourceconfig/parsing`.

## Internal Release Skip Tags

Push-triggered store workflows run only from `Kira manga/` on `internal-testing`. Include one of
these exact tags in the latest pushed commit message when a store should be skipped:

- `[skip ios]` — run Android Internal Testing only.
- `[skip android]` — run iOS/TestFlight only.
- `[skip both]` — skip both store workflows.

With no skip tag, both workflows run. When pushing multiple commits, the tag must be present in
the final commit message because the workflows inspect the latest pushed commit.
