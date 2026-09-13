# W03 PG02 test-only successor — authoring handoff 01

2026-09-13 UTC. **AUTHOR HANDOFF ONLY; pending distinct actual-diff review, uncompiled/unexecuted.**
Primary authorized source authoring under plan `app-29-lease-dispatch-pg02-primary-correction-plan-01.md`
SHA256 `b67977472e0e31c1c4c30d23de3c61338c13f8d0ca515786dbe7d048cbc7f335`
and distinct plan concurrence. This author does not approve the plan/delta or authorize execution.

## Exact source delta

Backend HEAD remains PRIVATE `8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3`. Only these two tracked files changed:

| Path (relative to kira-backend) | Current SHA-256 | Bytes |
|---|---|---:|
| `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PersistencePgOwnedCutIntegrationTest.kt` | `7a0d78b74ab590d5fc270b4a274b38dfadd2ce38a2880f951758f101d0441465` | 129877 |
| `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLeaseDispatchCreatorIntegrationTest.kt` | `901e29adf7b81bfcbd3f0358b3f61edf86268f83ed459a5d576bb04f4f791fa2` | 51241 |

Complete repository diff equals the two-file scoped diff. SHA256 **`03efcc0de0111b4b40d7774bf6321423e50cbc48921e091f30f57d31258e52a3`**,
25065 bytes, generated read-only by:
`GIT_OPTIONAL_LOCKS=0 git -C kira-backend diff --no-ext-diff --no-textconv --full-index 8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3 -- <the two paths above>`.
Diffstat: 2 files, 257 insertions / 84 deletions; much of the creator-method diff is indentation around failure-custody scopes.
No production, vendor, ordinary-fixture, carrier, build/static config, baseline, ref or existing evidence file was edited.

## A. Paired shutdown seam

`PersistencePgOwnedCutIntegrationTest.kt:1370–1413,1428–1447`:
- `withOwnedCutPool` accepts an optional existing companion. A test-only AutoCloseable teardown is
  registered before the inner GuardedDataSource construction, activation and readiness checks.
  The mixed test's only body change is `companion = first` at creator-test327; its existing body
  assertions and both connection/creator scopes remain.
- `OwnedCutPool.close` now calls `awaitShutdown(initiateShutdown())`. Initiation contains the same
  real request, actual shutdown invocation, diagnostics and RETURNED/ALREADY_CLAIMED assertion.
  The subsequent await/receipt/actor assertion block is unchanged apart from receiving those two
  captured values. `PgLifecycleTestScope` and all polling/production budgets are unchanged.
- Paired teardown attempts inner initiation, then companion initiation, before calling the inner
  await. Each initiation is independently caught; an earlier failure cannot omit the second attempt.
  Inner await is still attempted when its initiation returned, even if companion initiation failed.
  The first cleanup failure is rethrown with later failures suppressed in that deterministic order;
  enclosing standard `use` retains the setup/body failure as primary and then performs root cleanup.
- If inner construction fails before an OwnedCutPool exists, registered teardown still initiates
  the companion before the unstarted inner scope's default root close. No actors were activated at
  that constructor point. If activation/readiness/body fails after fixture publication, both real
  pool initiations are attempted before any explicit shutdown observation.
- The outer companion's ordinary close still performs its full receipt/actor/root checks. Its later
  real request/invocation observes the existing first-close claim (normally ALREADY_CLAIMED); the
  production request retains the original shutdown budget. No receipt/count/token is rewritten or
  disposal synthesized. The one-pool default directly delegates to the same OwnedCutPool.close path;
  no companion action occurs there.

## B. Finite MODEL failure custody

`PoolLeaseDispatchCreatorIntegrationTest.kt:529–644,678–787`:
- One small private diagnostic helper holds the first unexpected Throwable atomically, the separately
  retained public-call and final phase exceptions, and a fixed 13-value reached-stage set. Actor
  publication remains the existing AtomicBoolean/AtomicReference route; no additional actor is made.
- Stages are STORE_ENTERED, LEASE_OBTAINED, SETUP_OBTAINED, LOWER_RETURNED, CLOCK_ARMED,
  CLOCK_ENTERED, TAIL_WITNESSED, MODEL_EXPIRED, RETIREMENT_OBSERVED, ACTOR_CONSTRUCTED,
  ACTOR_STARTED, ACTOR_TERMINATED, WITNESS_COMPLETED. Each is written only when that named
  fact is reached; composite witnesses follow all corresponding checks. Missing stages imply no
  successful witness claim, not an invented cause.
- Setup/install, real lower call, callback and actor failures are retained before the phase can sanitize
  them. Shim installation is now within its restoring try/finally; restoration disarms the callback
  before inspecting/restoring the same delegate. The original clock offset is never rewound, and
  the same advance(2000), work budget, retirement route and authentic actor are retained.
- Only a direct PersistencePhaseException with TIME_BUDGET_EXHAUSTED after WITNESS_COMPLETED
  is classified as the intended public-call expiry. This matches LeaseJdbcFacade.afterJdbcCall ->
  PersistencePhaseContext.requireWork in the pinned production source. That exact Throwable is
  excluded by identity from unexpected-failure retention; arbitrary early refusals, JDBC failures or
  callback assertions are not accepted as the intended expiry. A returned call still fails the original oracle.
- The actual final phase code/databaseOutcome/cleanupProven are saved after the unchanged typed
  assertThrows. The original first unexpected failure is rethrown outside sanitization; the formerly
  combined final assertion is split into named callback and actor checks. Existing outer-tail,
  quiescence and admission assertions remain. Two explicit checks require the observed intended
  expiry and final TIME_BUDGET_EXHAUSTED code; neither relaxes the prior witnesses.
- Diagnostic custody is outside withOrdinarySourceGrantCleanup, while its callback body is also
  captured. Thus a retained MODEL setup/body/callback failure remains the exact Throwable thrown
  after authentic fixture cleanup, even if the ordinary fixture's emf.destroy finally replaces the
  escaping exception. Later restoration/escaping cleanup failures are attached, avoiding duplicate
  self-suppression. One bounded PG_POOL_CREATOR_MODEL row reports only stage names, existing
  actor flag, call return/type, separate call/phase enum outcomes/cleanup booleans and unexpected type;
  it logs no SQL text, credentials, payload or raw production object.

## Author self-review and boundaries for the nonauthor

- Manually reread the changed source and bounded production caller/close graph; no syntax/AST/static
  checker, compiler, build/test, target helper import/execution, acquisition or process/resource probe
  was run. Current source is a draft for distinct review, not evidence that either test now passes.
- Pair ordering is a source-supported correction direction, not newly measured SharedTimer attribution.
  MODEL changes are diagnostic; the next authorized attempt may deliberately expose another failure.
- Please scrutinize the signature/default close equivalence, failure order on second-pool construction/
  start/readiness, the repeated real outer shutdown call using the original claim/budget, and the
  narrowed expected-timeout discriminator. No extra test replay is proposed by this author: start with
  the two failed methods; any affected existing default-path control is the nonauthor/primary decision.
- Local custody protects failures produced inside the MODEL test callback and store/shim/callback
  before emf.destroy. The shared ordinary fixture was deliberately not refactored: an exception in
  its own pre-callback EMF initialization followed by another exception in emf.destroy is not newly
  recoverable by this local helper. This is outside the observed line613 path; reviewer should decide
  whether the plan intended that additional shared-fixture edge before broadening scope.
- Throwable.addSuppressed follows JVM semantics. An unexpected bounded PersistencePhaseException
  has suppression disabled by production; its identity and scalar outcome are retained, but the helper
  cannot force suppression onto that object without wrapping/changing the original Throwable. No
  production exception change or general-purpose failure framework was introduced. Review this edge
  if the requirement demands retained cleanup stacks even with a suppression-disabled first failure.
- Existing run34762007741 remains16PASS/2FAIL; unchanged prior16 are historical, not a fresh18.
  Source needs distinct review and primary-owned fresh freeze/checkpoint/profile binding before any
  separately authorized validation. Native05 remains UNQUALIFIED; consumer/W03/full-P3/new-data
  and installation recovery remain open; W06 excluded. No private ancestry was pushed anywhere.

Only the two test source files and this new private0600 author report were written. No workers,
new temporary outputs, freeze/checkpoint/ref/CI/lock/lease actions or owner notifications were created;
primary coordinates nonauthor review, execution and Telegram.
