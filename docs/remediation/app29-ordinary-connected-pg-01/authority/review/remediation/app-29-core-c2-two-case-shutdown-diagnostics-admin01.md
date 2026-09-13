# Core C2 — two-case shutdown diagnostics, author note

Author: `/root/admin_01_history_author`, 2026-09-12. Test-only candidate for independent
actual-diff review; **not compiled or executed**, and not a product/timeout/expected-state repair.

## Exact change

Repository remains on `remediation/app-29-backend-complaints`, HEAD
`989a8c07b90d956a5f2484f223be41b5d99a8a3c`. The sole changed repository file is:

`kira-backend/src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PersistencePgOwnedCutIntegrationTest.kt`

- Baseline SHA-256: `a92f7a1bc152576c0bc2cd55d3dea49614ca073aea3868c2929e5bf1fea48017`.
- Candidate SHA-256: `09ff840b9b3c4532c33ce24c09a60a2b0479084b480ed29f6d21478751e78f99`.
- Exact full-index diff: `review/remediation/app-29-core-c2-two-case-shutdown-diagnostics-admin01.diff`.
- Diff SHA-256: `9b3f80e5c18d3c82d31671d033713b71c00a16625c52bacd10e93e59b9d10338`.

Only these two existing test bodies enable a per-fixture enum label:

- `throwing original RETURN override leaves F G T free and retires its exact source without a second return()` → `RETURN_SAMPLE`.
- `failed post consent real Hikari tail seals actor admission but cannot retire the successor epoch()` → `FAILED_POST_CONSENT_TAIL`.

The fixture's default is null. All other 45 existing cases leave diagnostics off; the helper
returns before reflection, clock, actor, executor or output operations. No test is added,
renamed, removed, skipped or changed to expect a different result.

## Read-only diagnostic behavior

`OwnedCutPool.close` captures before/after its **one existing** `shutdownInvocation()`;
the same RETURNED/ALREADY_CLAIMED membership assertion checks its captured return value.
The existing `receipt.observe()` loop is unchanged in count and predicate. On a thrown
observation/wait failure, the diagnostic receives only the last successfully returned
observation, or `NOT_OBSERVED` if none returned. It does not call an observer itself.

The small private helper emits one fixed-label scalar line per capture: original shutdown
budget remaining (using the same retained budget and existing zero-on-expiry reader),
invocation result/first-close outcome/last observation; all actor snapshot counters, seal
flag and fault enum; and the existing Hikari closer's queue size, pool size, active count,
completed-task count, shutdown and terminated flags. These are **non-atomic diagnostics**,
not completion proof. No task, Thread, connection, raw handle, exception or arbitrary
object is rendered. No factory, executor, worker or observer is created or replaced.

The after-invocation capture is in `finally`; invocation failures retain their original
propagation. Observation failures are rethrown as the **same Throwable**, without wrapping,
adaptation, added suppression or stack resetting. Both capture and best-effort fixed
`UNAVAILABLE` output are Throwable-contained, so a diagnostic failure cannot replace or
mutate the original test failure. Existing nested `.use` cleanup remains in place.

## Static checks and limits

- Nearest backend `AGENTS.md`, README test guidance and routed PLAN inspected; no deeper
  source-ancestor `AGENTS.md` was present. App owner-WIP files were left untouched.
- Read-only Git status/diff show exactly the one test file changed; `git diff --check` passes.
- Source counts remain 31 owned-cut tests and 16 descendant tests. Exactly two label
  assignments exist. In the fixture, requestShutdown/shutdownInvocation/receipt.observe
  callsite counts remain 1/1/1, with zero new budget-start calls.
- Original test assertions/expected states and all production budgets/code are unchanged;
  only the invocation result was extracted to support the diagnostic snapshot.
- No builds, tests, controllers/runners, CI, network/downloads, commits or Git mutations.
  No harness, full-suite rerun, prewarming, unsealing, queue draining or cleanup change.
- Prior diagnosis `0428ead2…`, sealed history and raw hosted results remain unchanged.

Backend05 has been asked to independently review this exact actual diff and source pin.
Any later compile/runtime authorization and runner narrowing remain the primary's decision.
