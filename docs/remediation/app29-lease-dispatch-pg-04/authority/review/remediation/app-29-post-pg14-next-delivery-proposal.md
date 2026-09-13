# App29 after PG14 — smallest next gate and product step

2026-09-12 UTC, Admin04. **Bounded source-only proposal, not admission or acceptance.**
Private Backend remains `6db944871c1584bd6a1f28263e8010cadd766fab`. PG14 actual-result
acceptance is primary/Web03-owned and was pending when this investigation began.
Do not rerun it. Paths below: **P** = Backend
`src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`; **Q** =
the matching `src/test/kotlin/` package. All proposals require primary authorization.

## 1. Next bounded gate: the existing one-method SQLClientInfo control

**Yes: select it alone, not alongside PG14.** Exact selector:

```
me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest.real lease preserves Properties client info defaults and declared stale and foreign failure shapes
```

One `test` task, one `--tests` pair (three task argv elements), one ordinary XML case
named the method plus `()`. No new test, fixture, second class or redundant14 rerun.

- `Q/PhysicalJdbcDescendantsTest.kt:40–48` owns one PER_CLASS/SAME_THREAD lazy
  `PgLifecycleDatabaseFixture`, stopped in AfterAll. The method is at211–238.
- The shared `withOwnedCutPool` at
  `Q/PersistencePgOwnedCutIntegrationTest.kt:1370–1387` uses that **passed server**;
  its one Hikari slot/two physical custody cells are not two PostgreSQL containers.
  Calling this top-level helper does not select or instantiate its neighbouring
  PG14 JUnit class. `Q/PgLifecycleDatabaseFixture.kt` creates one PostgreSQL17.6-alpine.
- Thus the expected separately owned run is still **one PostgreSQL + one Ryuk =2**.
  This is the same population envelope, not reuse of PG14's stopped containers or
  a promise that future cleanup will pass. Keep existing ownership/event/absence
  checks and all budgets; no container guard relaxation is needed.
- The method reaches actual `P/LeaseJdbcFacade.kt:39–48,112` checked-declaration
  adaptation and `P/PhysicalJdbcDescendants.kt:159–170,266–284` Properties copying:
  default-backed String values, non-String same-key fallback without caller mutation,
  both foreign-thread `setClientInfo` overloads yielding `SQLClientInfoException`,
  and stale Properties-overload refusal after close. It does **not** inject every
  finally failure or assert the stale String overload here; do not enlarge its claim.

Use an explicitly reviewed **new one-case/class/profile/request/XML binding** on the
same source/JAR/helper bytes. Reuse the existing carrier, not another harness. Retain
the complete source inventory, candidate/classpath/JDK pins, normal task dependencies,
one worker/fork, source transport and cleanup rules. No extra standalone compile/static
batch and no replay of unchanged38 units is justified by a selection-only change.

**Diagnostic scope must change explicitly for this separate profile:** the method
never sets `OwnedCutPool.shutdownDiagnosticCase`; the helper returns without emitting
the two PG14 labels. Its ordinary teardown assertions remain active, including actual
shutdown observation and zero future lease entries/active operations. Require no invented PG14 rows or
positive consumer witness. PG14's original four required raw rows remain mandatory
for PG14 and stay in its accepted evidence; do not run this selection under PG14's
count/scalar controls or silently weaken that profile to accommodate missing rows.

## 2. Actual product blocker: selected Spring phase ownership is still absent

The September9 claim that no physical/lease/pool composition exists is now obsolete.
Do **not** rebuild it. The current concrete boundary is:

| Current existing source | Missing product connection |
| --- | --- |
| `P/GuardedDataSource.kt:12–45,108` | Private, explicitly not a Spring bean; only CONTROLLED_TEST_ONLY starts/allows business. UNKNOWN fails closed. There is no production launch profile. Test endpoint/timeout choices do not establish ordinary Boot configuration compatibility. |
| `P/PersistenceJdbcTransaction.kt` | Per-lease transaction/auto-commit safety, not a Spring selected-resource phase executor. |
| `P/OrdinaryPersistenceAdmission.kt`, `P/LocalPersistencePermit.kt`; `complaint/infrastructure/transaction/DeletionPersistenceAdmission.kt` | Local accounting exists; the transaction directory currently has only deletion admission. No named phase connects admission → selected manager/lease → SQL → actual quiescence before release. |
| Existing `security/AdminStepUpService.kt` and `audit/infrastructure/JpaAuditRepositoryAdapter.kt` | Step-up password work is still inside `@Transactional issue`; audit is ordinary JPA. Neither has the required complaint phase/allocation/selected-holder routing. |

Named P3 files `config/PersistenceConfiguration.kt`,
`config/KiraComplaintPersistenceProperties.kt`,
`P/GuardedJpaTransactionManager.kt`, `P/GuardedJdbcTransactionManager.kt`, the
`complaint/infrastructure/transaction/` phase executor and
`complaint/infrastructure/capacity/` checked JDBC adapter are absent. The pure22-counter
domain math already exists; it is not the missing transactional writer.

**Recommended next implementation authorization:** one connected, still-private
**ordinary named phase → guarded selected Spring resource → real scalar JDBC
operation → commit/rollback → proven lease/permit release** slice, using P3 §§3–5
and the existing composition/admission. Scope the new phase/manager files above plus
only necessary `GuardedDataSource`/lease hooks. Its meaningful tests must prove:

1. Ambient transaction/synchronization, outstanding unbound lease, wrong manager,
   cross-resource or second borrow are refused **before** checkout; both DS overloads
   obey the same boundary. Same-resource ordinary REQUIRED joins remain legal.
2. Actual JdbcTemplate/manager work shares the selected bound connection; failure
   rolls back a real write, not a MODEL disposition. Return/retirement drains before
   `LocalPersistencePermit.releaseAfterQuiescence`; timeout/unknown cannot refund early.
3. Existing2s phase/separate1s cleanup policy and ordinary configuration are preserved;
   no raw getter, copied Spring context, callback escape, new pool/registry or public
   production-profile enablement substitutes for the guard.

This is a proposal for connected product code, not another helper certificate.
Primary must select concrete named ports/resource binding before edits. Subsequent
checked whole-vector capacity SQL, existing audit/grant routing and connection-free
step-up orchestration remain a connected follow-on, not silently credited by this
first phase. Deletion/public beans remain closed until their relevant gates pass;
do not flip CONTROLLED_TEST_ONLY into production on eventual focused14+1 results.

## 3. Do not restart the preserved original D05/D06 drafts

The current shorthand is artifact-specific: original D05 manifest `063f3785...`
is PARTIAL/not import-ready; original D06 transfer `f0ed266e...` is unreviewed/
unexecuted transfer evidence. Keep both and their false import flags unchanged.

**Already-completed successor work must also survive:** D05-v2 source review
`d9ea4b95...`, D06-v2 controlled-import review `70aeb9a6...` and
`working/campaign-resume-20260908-linux-01/primary-controlled-import-01/result.json`
(`4189c930...`) record reviewed minimal imports across43 test paths/21 additions.
Current `Q/PgLifecycleDatabaseFaultControlsTest.kt` and
`Q/PgLifecycleNegotiationControlTest.kt` exist. Therefore the original handoff's
missing relay/negotiation authoring is **not** a reason to restart that work or apply
its stale baseline. Neither historical import approval nor this read establishes
current full D05/D06 runtime acceptance. Use existing successor/result evidence when
primary addresses those distinct gates; this proposal does not rerun/review that matrix.

## 4. Evidence carry and limits

Carry accepted38 units and the normal compile/static disposition `dae02d33...` as
their actual scope; after primary accepts PG14, carry its exact14 result separately.
The one SQLClientInfo result would close only that named declaration/default/foreign
caller seam. It cannot qualify opaque eviction, native-finalizer interiors,
pin/compaction, successful wire cancellation, liveness invalidator closure or actual
shipping cut/exception tables/initialization. Native05 remains UNQUALIFIED; source/
classpath hashes and strict dependency mode without verification metadata are not
defined-byte/transitive-dependency or full consumer proof.

Full D01–D15/C6, P3 Spring/JSON/capacity/audit/step-up and final W03 regression/reviews
remain. Preserve original45/47, PG10 and0/2 cleanupFAIL histories; kill9/die137 and
NORMAL_ABSENT are not graceful-shutdown proof. No W03/package/issue completion,
Firebase retirement, public private-ancestry push or W06 work follows. These open
qualification gates block enablement/acceptance, not a claim that all connected
product authoring must be replaced by another general audit.

Only this proposal and its `.inputs.sha256` were written. Reads were limited to
named plans/status records, exact fixture/selector/implementation seams and relevant
config/transaction directory listings. No source/live-carrier/PG14-packet edits,
imports, execution, checkers, builds, tests, probes, acquisition or D05/D06 application.
Companion input pins are workspace-relative, not a new source freeze.
