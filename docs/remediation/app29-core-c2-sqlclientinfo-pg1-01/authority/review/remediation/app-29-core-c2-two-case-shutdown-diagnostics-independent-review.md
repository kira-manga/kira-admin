# Core C2 — independent actual review of two-case shutdown diagnostics

Reviewer: Backend05 (`/root/backend_05_history_hosted_review`), NONAUTHOR, 2026-09-12 UTC.

**Disposition: no blocking findings in the supplied diagnostic source delta. Accept within the authorized source-only scope; compilation/runtime are NOT VERIFIED. This is not a product fix or execution authorization.**

## Exact reviewed bytes

Sole path in the supplied diff:
`kira-backend/src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PersistencePgOwnedCutIntegrationTest.kt`.

| Input | SHA-256 |
|---|---|
| Hosted02 frozen baseline test, bound to Backend `989a8c07b90d956a5f2484f223be41b5d99a8a3c` | `a92f7a1bc152576c0bc2cd55d3dea49614ca073aea3868c2929e5bf1fea48017` |
| Actual candidate test (121,028 bytes) | `09ff840b9b3c4532c33ce24c09a60a2b0479084b480ed29f6d21478751e78f99` |
| `review/remediation/app-29-core-c2-two-case-shutdown-diagnostics-admin01.diff` | `9b3f80e5c18d3c82d31671d033713b71c00a16625c52bacd10e93e59b9d10338` |
| Author note, same stem with `.md` | `8e2ba4024e71968f33c2d4fba1ca6ad7e796554f78d383cba53393ea04a58282` |

I independently reconstructed the candidate **in memory** from all six supplied text hunks and the frozen baseline; it equals the actual candidate bytes. Independently computed blob-object hashes also match the diff header (`a3ec95274accb9ca3b2749cfdfdc4493ec68cb67` → `1bfbcbae07b340c83b45da62ed05e4cf49dab5e8`). No patch was applied to source, and no Git command or broader worktree/history audit was performed.

## Bounded source checks

1. **Only the two authorized cases enable capture.** Exactly two assignments select `FAILED_POST_CONSENT_TAIL` and `RETURN_SAMPLE` in the two previously failing named tests. The per-fixture default is null; the private diagnostic helper returns at line 1312 before any reflection, clock, actor/executor reads or output when disabled. All 31 owned-cut test names match the sealed profile; only those two test blocks differ, the other 29 are byte-identical. The 16-case descendant file remains byte-identical to hosted02. No tests are added, renamed, skipped or removed.

2. **One existing shutdown invocation; no extra lifecycle observer.** `OwnedCutPool.close` retains one `pool.requestShutdown()`, one `pool.shutdownInvocation()` and the existing single `receipt.observe()` callsite inside the same wait/predicate. `BEFORE_SHUTDOWN` is after the existing request retains its budget and before the actual `shutdownInvocation`; `AFTER_SHUTDOWN` is in its `finally`. The original membership assertion checks the saved invocation result. All subsequent expected-state and actor/factory/retirement assertions remain unchanged.

3. **Original budget, no reset or enlarged wait.** The helper reads the existing `shutdownBudget`; it adds no `PersistenceTimeBudget.start`, supplied budget, wait, retry or shutdown call. The existing `persistenceFactoryRemainingMillis` reads that budget and maps only its exhaustion to zero. The unchanged production lifecycle retains its original budget (default 10,000 ms); the fixture still uses the unchanged default 8,000 ms wait. Diagnostic elapsed time is not compensated or waived.

4. **Passive fixed scalars, not completion observations.** The helper reads `firstCloseOutcome()` (atomic outcome reads) and `actorSnapshot()` (a non-mutating counter/fault snapshot under the existing gate). Neither invokes actor termination observation, state retirement, sealing or receipt observation. Reflection reads the already-existing `GuardedDataSource.pool → HikariDataSource.pool → closeConnectionExecutor`, then obtains only queue size, pool size, active/completed counts and shutdown/termination flags. The existing Hikari 6.3.3 source archive confirms those fields and the executor type. There is no factory/executor/worker creation or replacement, prewarming, queue draining, cancellation, unsealing or product change.

5. **Output is bounded in kind.** Three fixed phase labels, two enum case labels, fixed status/sentinel tokens, enum names, integers/longs and booleans are rendered. No task, Thread, connection, raw handle, exception text, object `toString`, environment value or arbitrary caller string is printed. Counts/state are explicitly best-effort and non-atomic; they are not lifecycle completion proof.

6. **Original failure remains primary.** If invocation throws, `finally` adds only Throwable-contained diagnostics and the invocation exception continues unchanged. If observation/wait throws, the helper receives the last successfully returned observation (or `NOT_OBSERVED`) and the catch rethrows the **same Throwable**. There is no wrapping, stack reset or suppression mutation. Both normal capture and fixed `UNAVAILABLE` fallback contain diagnostic/output Throwables. The original nested `.use` cleanup remains in place. No extra receipt call is made to populate a diagnostic.

For these read paths, the current `GuardedDataSource`, `PoolLifecycle`, `PoolActorCustody`, `PersistenceFactoryProtocol` and `PersistenceTimeBudget` files match their retained hosted02 source-map hashes. The existing Hikari source archive remains SHA-256 `65a247c9ddb809885696ad2dbb1e77e923debc82c94972ca4c48f40a83c0e0a5`; no dependency was acquired or executed.

## Limits

- Review used only local source/text/hash analysis and this separate report. No source edits, compiler/checker/tests/builds, helper/controller/runner execution, CI/network/service operations, dependency acquisition or Git commands.
- Read-only metrics/logging can perturb timing and can be unavailable; even `CAPTURED` is a non-atomic diagnostic, not a proof of queue causality, actor completion or product repair. Reflection compatibility, compilation and actual output remain unexecuted obligations.
- Hosted02 remains **45 PASS / 2 FAIL**; historical **20 PASS / 27 FAIL** is separate. Native05 remains **UNQUALIFIED**, D05 **PARTIAL**, D06 **unreviewed**. Existing result/seal bytes are not revised by this candidate.
- The primary alone handles any newly bound **exact-two-only** existing-runner adaptation and subsequent authorization. This review authorizes no run and no full47 rerun, product/timeout/assertion correction, publication or release.
