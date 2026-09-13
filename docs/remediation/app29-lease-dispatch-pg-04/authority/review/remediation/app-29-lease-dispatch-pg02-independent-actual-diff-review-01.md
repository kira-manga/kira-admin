# W03 PG02 — independent actual-diff review 01

2026-09-13 UTC · `w03_static_nonauthor_review` · NONAUTHOR.

**HOLD this exact delta for two small diagnostic-custody corrections below.**
The paired-pool lifetime change is sound on source review. No production change,
longer budget, wider test selection, or new ordinary-fixture framework is justified.
No runtime cause or successful correction is claimed.

## Exact reviewed inputs

Backend `/root/projects/Kira/kira-backend` remains private HEAD
`8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3`, committed tree
`fc480e82630091138da145ade1812cedcd75e58e`; only two modified test files.

- Plan `app-29-lease-dispatch-pg02-primary-correction-plan-01.md`:
  `b67977472e0e31c1c4c30d23de3c61338c13f8d0ca515786dbe7d048cbc7f335`.
- Prior independent plan concurrence:
  `d0f67c7fe45647bed792a8625ec0a60439f57c303554d31f3de8ca8841ddc2b7`.
- Entire author handoff `app-29-lease-dispatch-pg02-test-authoring-report-01.md`:
  `384fadaf7c93b3f8a661cb917f9661d3204c494ea6bd2932ce4b8a1e0b8f4155`.
- Complete actual full-index diff against that HEAD:
  `03efcc0de0111b4b40d7774bf6321423e50cbc48921e091f30f57d31258e52a3`;
  independently read in full, 2 files, +257/-84.

T = `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`.

| Current file | SHA256 |
|---|---|
| T/PersistencePgOwnedCutIntegrationTest.kt | `7a0d78b74ab590d5fc270b4a274b38dfadd2ce38a2880f951758f101d0441465` |
| T/PoolLeaseDispatchCreatorIntegrationTest.kt | `901e29adf7b81bfcbd3f0358b3f61edf86268f83ed459a5d576bb04f4f791fa2` |
| T/OrdinarySourceGrantCleanupFixture.kt (unchanged) | `ce0110d46c15fefe5e152d6aa4be30d1c0539247f468c54d4cb15969db52418b` |
| T/PgLifecycleTestScope.kt (unchanged) | `7574167d18008256a43ff056e5797d5882abe1defc4ffcdda46e72a02a0ae9ec` |

## Two bounded fixes

### R1 — preserve later errors at the existing capture boundary

Creator test695–715: `retain` performs only first-error CAS; `capture` subsequently
rethrows a distinct later error without preserving it on the saved first one.
This leaves a fixable masking path even when the first Throwable supports suppression:

1. An in-store/shim/callback error F is retained before phase sanitization.
2. The existing post-phase `requireConnectionFree` observation (627–632) fails with C.
   The outer `capture` sees C, but `retain(C)` discards it because F is already stored.
3. `OrdinarySourceGrantCleanupFixture`'s plain `finally { emf.destroy() }` throws E,
   replacing C on escape. `withFixture` preserves E on F, but C is now lost.

This is a source-derived exceptional path, **not** an allegation that these errors
occurred in run34762007741. It directly concerns the plan's later cleanup-error custody,
not the unrelated pre-callback initialization caveat.

Smallest correction: when an already-retained first error exists, preserve a distinct
later observed error at `capture`/`retain` before rethrow/sanitization can erase it,
using the helper's existing identity/deduplication discipline. Do not replace F,
recapture the expected expiry, expand deadlines, or refactor the ordinary fixture.

### R2 — diagnostic emission must not replace the saved primary

Creator test761–772 computes the correct saved first error, then runs unguarded
`println(describe())` before throwing it. If formatting/output throws, that diagnostic
failure escapes instead of F. The new diagnostic must not recreate the failure-masking
problem it exists to diagnose.

Smallest correction: make this final formatting/emission failure-safe with respect to
an existing first error. A later reporting failure may be secondary; it cannot become
primary when F already exists. Preserve genuine failure when reporting is the only
failure. No new logging payload, output framework or synthetic success is needed.

## Paired lifetime and default semantics: no blocking finding

Owned-pool fixture1377–1388 registers cleanup before inner pool construction, activation
and readiness. The fixture reference is published before start. If construction fails,
the inner root has not been activated; companion initiation is still attempted before
that scope's close. Earlier failure constructing the scope itself cannot leave a newly
started inner owner, and the enclosing outer use still closes its owner.

`closeOwnedCutPool`1394–1412 independently attempts inner then companion initiation
before any explicit pool/root full-end observation. A request throw/null refusal,
actual-invocation throw, or refused invocation fails its initiation but cannot skip the
peer attempt. When the inner initiation returned, its original await/assert block is
still attempted even if peer initiation failed. Cleanup exceptions are ordered and
standard outer `use` keeps setup/body failure primary. A later ALREADY_CLAIMED outer
close does not erase the already propagated early failure.

With companion=null the new wrapper calls the same close path. `close` is exactly
initiate-then-await; the receipt/actor/UNKNOWN assertions are unchanged. Existing
callers retain their trailing-lambda form. Production `PoolLifecycle`120–129/466–474
retains the first shutdown budget; the outer repeated invocation does not renew it.
All current mixed-test body assertions remain. No Timer reference/count/receipt is
written, no new actor is introduced and no end oracle is replaced by local emptiness.

## MODEL semantics and the author's declared boundaries

The same original work budget, advance(2000), real lower getClientInfo, actual
`afterJdbcCall`, retirement, authentic Hikari actor and termination witness remain.
The fixed13 stage set records reached facts, not an actor-cause guess. Named witness
and actor assertions, tail/quiescence/admission checks remain; intended-expiry and
final TIME_BUDGET_EXHAUSTED checks strengthen rather than relax the original oracle.
The direct post-witness PersistencePhaseException discriminator is supported by the
unchanged LeaseJdbcFacade/phase route. Early SQL/setup/callback errors are not excused
as expected expiry. Delegate installation is within restoration, callback disarms,
and the clock offset is not rewound. Phase and public-call scalar outcomes are separate.

The author's **pre-callback EMF-init followed by emf.destroy masking** limitation is
real but outside the diagnosed in-store/MODEL callback boundary. Do not broaden this
slice merely to repair that existing shared-fixture behavior; do not claim this helper
recovers an exception it never observed.

Production PersistencePhaseException disables suppression/stack/cause. Its unchanged
identity cannot simultaneously be forced to accept suppressed errors. That limitation
must remain explicit: this review does not grant full cleanup-stack custody for such
an object or authorize production exception changes. R1 concerns fixable loss of later
errors already observed by the helper, including suppression-enabled primaries, and
must not be dismissed as this inherent JVM limitation.

## Seed scope and smallest validation

Development07 manifest hash remains
`3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`.
Its source_hashes contains348 paths: all remain present in the backend and all belong
to the prior PG transport02 manifest's source inventory. No tracked path is deleted or
renamed. No production/vendor/config/seed-selection machinery delta exists. This is
path-preservation review, not a newly created/approved freeze; primary must carry all348
into its later fresh freeze, not substitute only these two test files.

After the tiny helper correction and exact independent recheck, changed-Kotlin statics
remain required under existing baselines, without suppression/config expansion.
Then primary may checkpoint/freeze/bind the existing lane for **only the failed2 first**,
with normal required compilation. No material single-pool default change justifies
additional controls; the MODEL method also exercises the default path. Prior16PASS
remain historical. No full47/reassurance replay; the diagnostic retry may still FAIL.

No source edits, execution/import, syntax/AST/static checker, build/test, acquisition,
freeze, commit/ref/CI or resource-control operation was performed. Only this new private
0600 report was written. Historical raw failures and acceptance limitations remain.
