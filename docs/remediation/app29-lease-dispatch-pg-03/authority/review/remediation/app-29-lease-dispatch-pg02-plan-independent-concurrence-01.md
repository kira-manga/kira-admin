# W03 PG02 correction plan — independent concurrence

2026-09-13 UTC. Reviewer: `w03_static_nonauthor_review` (NONAUTHOR).

**CONCUR with the bounded test-only plan. No design blocker.** This is plan/source
review, not approval of an unwritten delta, execution authority, or correctness credit.
A distinct author may implement; the actual diff still needs independent review.

## Exact inputs

- `app-29-lease-dispatch-pg02-primary-correction-plan-01.md`:
  `b67977472e0e31c1c4c30d23de3c61338c13f8d0ca515786dbe7d048cbc7f335`.
- Complete latest diagnosis,
  `app-29-lease-dispatch-pg01-transport02-independent-actual-result-review-01.md`:
  `0cd81ef933388b61e3f512bcd915962e9eced17ede60f32a6ce0698b76a1f8d4`.
- Live repository: `/root/projects/Kira/kira-backend`, clean at review,
  HEAD `8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3`,
  tree `fc480e82630091138da145ade1812cedcd75e58e`.

Below, T is `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`.
The following entire-file hashes were independently checked:

| File | SHA256 |
|---|---|
| T/PoolLeaseDispatchCreatorIntegrationTest.kt | `db140c4c0e93a349608b6e05e80033fd07e298aee4c272932e78b6d69564ce4a` |
| T/PersistencePgOwnedCutIntegrationTest.kt | `b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322` |
| T/PgLifecycleTestScope.kt | `7574167d18008256a43ff056e5797d5882abe1defc4ffcdda46e72a02a0ae9ec` |
| T/OrdinarySourceGrantCleanupFixture.kt | `ce0110d46c15fefe5e152d6aa4be30d1c0539247f468c54d4cb15969db52418b` |
| complaint/infrastructure/transaction/OrdinaryPersistencePhaseExecutor.kt (main package) | `43ef1e1ab32603ac03a5d5ec64ccf04f73bd1e6776763a830292efd151576cbc` |

## A. Paired teardown: supported, with exceptional paths mandatory

The mixed-pool test (creator test 325–356) nests full `withOwnedCutPool` lifetimes.
The fixture registers `OwnedCutPool.use` before start/readiness (1377–1384), but its
close (1402–1442) completes request, actual invocation, and full receipt observation
before the enclosing pool can close. `PgLifecycleTestScope.close` then also demands
root/actor end. In the clean source tree, `PersistenceDriverTimer` 44–60/76–113 and
`PersistenceJdbcDriverRoot` 76–105 require both local retirement and captured Timer
termination. Native SharedTimer retains the Timer while another reference exists.
Thus initiating both owners before either full-end observation is structurally sound;
it does not prove which PENDING gate caused the historical run.

Mandatory actual-diff checks:

1. Companion cleanup is registered **before inner start/readiness**, not only on entry
   to the test body. Partial acquisition/startup failure retains cleanup for every
   acquired owner; constructing an inert second pool must not strand the first.
2. Both shutdown initiations are attempted before either pool **or scope/root** full
   observation, even if the first request/invocation throws or refuses. A plain
   sequential call or throwing `finally` must not skip the peer or replace the body/
   setup failure. Later cleanup failures have deterministic suppression order;
   an early failed initiation cannot be silently replaced by a later ALREADY_CLAIMED.
3. Default single-pool behavior remains request → actual invocation/check → unchanged
   receipt/actor assertions → scope close. Preserve UNKNOWN expectations and every
   current end oracle. `PoolLifecycle` 120–129 retains the first shutdown budget;
   no budget renewal, poll change, foreign-pin release, or completion fabrication.

## B. MODEL failure custody: necessary diagnostic, not a guessed fix

Creator test 539–603 has several fallible setup/lower/callback operations before
`witnessed=true`. The executor catches Throwable (15–29), phase recording retains a
bounded code rather than the original error (`PersistencePhaseContext` 247–258),
and `PersistencePhaseException` disables cause/suppression/stack (128). Therefore
capturing the original at the test boundary before sanitization is appropriate.

Keep the plan's finite reached-stage facts and named witness/actor assertions.
In particular:

- A lower-call error **before the clock is armed** is not the deliberate expiry just
  because it is JDBC-shaped. Capture setup, lower, callback and actor-body failures
  at their originating boundary. Retain the public-call/phase outcome separately;
  do not blanket-rethrow expected expiry or blanket-ignore SQLExceptions.
- Saved unexpected failure identity must dominate later assertThrows/witness/cleanup
  errors outside sanitization. Disarming the callback and restoring the delegate
  must also survive failed installation/callback/restoration. Do not rewind the MODEL
  offset or replace the original work budget to make cleanup pass.
- Do not stop authentic phase finalization or fixture cleanup to surface diagnostics.
  `OrdinarySourceGrantCleanupFixture` 47–54 uses `use` followed by a plain
  `finally { emf.destroy() }`: merely rethrowing the saved error inside the body can
  still let a destruction failure replace it. The implementation must retain the
  original outside that boundary and preserve later cleanup failures; inspect any
  supporting fixture delta rather than assuming `use` alone settles precedence.
- Preserve all tail/quiescence/admission checks. Current `LeaseJdbcFacade` 138–140
  finishes the guard then calls actual `afterJdbcCall`; the outer invocation finally
  (44–62) ends the creator afterwards. No production ordering defect is established.

Native structural corroboration was passive only: workspace
`.kira-validation/pgjdbc-owned-cut/upstream/pgjdbc/src/main/java/org/postgresql/`
`Driver.java` SHA256 `a9041811fc89d250f98fd8be08be3d52a107e19846117457822409008a648abe`
and `util/SharedTimer.java` SHA256
`b70ea6b561f15bed5ed66071fcd8d924eda032afe9fd0cbc808255637f39a066`.

## Smallest next validation and limits

After distinct actual-diff review and the primary's exact checkpoint/fresh freeze,
run **only the two failed methods first**, with ordinary required compilation.
Carry prior16PASS as historical, not fresh18. Additional existing controls require
concrete default-fixture impact in the actual delta; no full-suite reassurance replay.
Changed-Kotlin statics use existing baselines, no suppression/config expansion.
The diagnostic MODEL retry may still fail and earns no correctness credit by itself.

No source edits, target/helper execution/import, checks/builds/tests, acquisition,
process/resource control, Git/ref/CI changes, external sharing, or subagents occurred.
Only this new private0600 report was written. Reuse the existing admitted machinery;
preserve all348 development07 seeds and historical raw failures. Native05, consumer,
full-P3, new-data recovery, W03 and App29 package acceptance remain incomplete.
