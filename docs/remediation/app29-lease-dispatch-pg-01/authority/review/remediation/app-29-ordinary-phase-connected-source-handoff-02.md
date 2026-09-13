# W03 connected ordinary phase — resumed core source handoff 02

2026-09-13 UTC · `/root/w03_core_author_resume` (Admin01 scope) · private0600.
**AUTHORED / UNEXECUTED. Request independent actual-diff review; not self-approval,
primary source freeze, execution admission, W03 completion or production qualification.**

Private backend HEAD remains `6db944871c1584bd6a1f28263e8010cadd766fab`.
**Never publish this ancestry.** Source-only capture time: 2026-09-13T03:07:20Z.
Primary alone owns notifications, convergence, any later affected validation and owned cleanup.

## 1. Authority, preservation and exact scope

The admitted boundary is
`app-29-ordinary-phase-connected-implementation-admission-01.md` (`ebf90de2…`),
with primary plan `caa1cd86…`, technical review `977b0a98…`, regression review
`31d3af5d…`, and normative P3 `eb51e11c…`, particularly §§3–5/8. Full input hashes
are retained in the packet; the exact saved Spring6.2.19/Hibernate6.6.53.Final
research was reused, not replaced with a new dependency/runtime audit.

**E** = `review/working/app-29-ordinary-phase-connected-source-resume-02/`.
All source paths in E are relative to `kira-backend/`:

- **18 admitted main + 3 admitted test paths**, each with exact after bytes/hash.
  `after.json` and `owned-after.sha256` are the complete path list, not an inferred
  directory-wide permission. No other product/test path was edited.
- Relative to the private HEAD: **20 changed paths**, comprising **11 tracked
  modifications + 9 untracked additions**; owned final patch is **2251 inserted /
  35 deleted lines**. `PersistenceJdbcPoolTransfer.kt` is admitted but unchanged.
- Relative to the retained resume-entry worktree: **17 changed paths** (15 existing
  files modified, two tests added), **1182 inserted / 67 deleted lines**. Four admitted
  files are byte-identical to resume entry: `GuardedJdbcTransactionManager.kt`,
  `PersistenceJdbcTransaction.kt`, `PersistenceJdbcPoolTransfer.kt`, and
  `OrdinaryPersistencePhaseExecutor.kt`. Their already-authored content is preserved,
  not represented as a new edit in this resume's patch.
- E's original `before/`, `before.json`, `status-before.txt` and
  `tracked-diff-before.patch` are unchanged. They preserve all 19 initially present
  owned files and record the two absent tests. In particular the pre-existing dirty
  transaction-outcome file was retained exactly. The prior author's separate
  `app-29-ordinary-phase-connected-source-01/` evidence was not rewritten.
- The peer's three cleanup-owned paths were read/hashed, **never edited**. All match
  the peer handoff `app-29-ordinary-source-cleanup-source-handoff-01.md`, SHA256
  `778929293a8cbc26f6a3040cbc89b9c8cbe283e2197cebf31aca8a2264ad1efc`.
  Peer evidence is separately bound by `peer-inputs.json`, not claimed as core authorship.
- No live caller/repository, schema, bean/configuration, driver/vendor/native artifact,
  existing lifecycle fixture owner, PG14/SQLClientInfo test, authoritative tracker or
  other repository source was changed. The app's separately observed WIP was left alone.

## 2. Connected source now handed off

`P/` below means `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`.
These are descriptions of authored mechanisms, **not claims that the unexecuted
oracles have established runtime behavior**.

1. **Named ordinary-JPA entry.** The internal, non-bean executor exposes only
   `cleanupSourceGrants(): Int`. It samples its trusted injected wall Clock once and
   invokes the frozen `SourceGrantCleanup.deleteEligibleSourceGrants(Instant): Int`
   port. There is no caller-selected cutoff/SQL/lambda/flag/resource switch. The core
   `requireSourceGrantCleanup(JdbcTemplate)` checks exact phase, selected DataSource,
   existing JPA-created connection/EM holders, retained lease and one-operation use
   before the fixed peer SQL. The fixture subset already frozen with the peer is
   preserved; only additive clock/observer helpers were introduced.
2. **Entry versus participation.** `PersistencePhaseOwnership` uses the existing
   shared fail-fast `OrdinaryPersistenceAdmission`, including source-only floor1,
   bounded slots and caller-local outstanding acquisitions/leases. Entry first
   refuses current phase, ambient transaction/synchronization, any bound Spring
   resource and outstanding unbound custody. Manager composition runs before Spring
   propagation/suspension. Only the selected root REQUIRED begin can consume one
   acquisition right; a legal same-manager REQUIRED join verifies the original
   holder/lease and cannot get another permit or physical transaction.
3. **Begin/materialization custody.** The private real `JpaTransactionManager`
   retains the exact created EntityManager before its real transaction begin.
   `PersistenceManagedStatus` retains a returned native status before selected lazy
   holder materialization/validation. The acquisition receipt is retained before
   acquisition entry/Hikari and binds the real checkout transfer, lease, facade and
   consent in order. Both DataSource overloads use the same consumed authority.
   No DataSourceUtils fallback or manually installed accepted holder is added.
4. **Budgets and call guards.** One monotonic2s budget starts immediately after real
   checkout consent, before its acquisition tail and remaining JPA setup. Positive
   remaining LOCAL transaction/statement/idle/lock caps precede the fixed business
   operation, and JDBC reads are re-clipped on the same lease. One cached1s emergency
   allowance is separate from the original work interval. Nested internal read-cap
   calls retain their CLEANUP kind rather than accidentally requiring failed/expired
   business authority. Cleanup-budget access authenticates the original owner.
   The original connection read cap is restored before return or the lease is retired.
5. **Exact outcomes.** Lower `PhysicalJdbcFacade` records native commit/rollback
   return immediately after `Method.invoke` returns, before capture/wrapping/driver
   finalizers. Native invocation throw is distinct from later wrapper failure.
   The preserved outcome model separates NONE/COMMITTED/ROLLED_BACK/UNKNOWN from
   reuse uncertainty: later rollback/reset cannot erase acknowledged commit or
   resolve an unknown commit, and successor epochs do not inherit an old DB result.
   The bounded exception exposes code, exact DB outcome and cleanup/refund separately.
   Existing phase refusal codes survive executor/manager failure recording.
6. **Logical release and real finalization.** Scoped facade close only records
   logical release. The synchronous outer finalizer first settles Spring, then
   restores/returns or retires through the existing one-shot real lease protocol.
   Unscoped close retains its original immediate1s return policy. The new receipt
   requires actual ingress/acquisition/checkout and RETURN dispatch/transfer/pool
   operation tails, disposition of the preissued entitlement, and either real
   return consent or the existing terminal-reclamation conjunction. No closed flag,
   global-zero count, Spring afterCompletion or successor slot is completion proof.
7. **Deadline/terminal connection.** The existing scanner samples phase expiry
   outside F/G/T and checks the exact old epoch under the existing G cut before
   requesting retirement. The detached terminal fact is published only at the
   existing final F→G reclamation conjunction; no replacement physical registry or
   worker is introduced. Quarantine retains the original bounded permit/custody and
   blocks fresh scoped admission. Only authentic later quiescence permits local
   refund, including an UNKNOWN DB result; it grants no replay/reconciliation authority.

## 3. Intentionally unsupported hooks and admission/gate differences

These restrictions must be visible to primary and both reviewers; none is silently
credited as full P3 Spring/production compatibility.

| Boundary | Actual selected behavior / remaining gate |
|---|---|
| **TransactionExecutionListener hooks** | The private JPA delegate is constructed with no execution listeners. A **nonempty listener collection is refused before scoped dispatch**, including before/after begin, commit and rollback listeners. No customization/initializer API exposes the delegate. The authored listener-negative case checks refusal and a subsequent legal positive. This is a declared dormant configuration restriction, **not recovery of arbitrary throwing APTM afterBegin listeners**. |
| **Other Spring hooks** | No EntityManager initializer or transaction-manager customizer entry is offered. EntityManagerFactory/vendor behavior still runs through the actual selected factory. A failure before returning an EM, or after doBegin but before status return, is not assumed harmless: when exact closed-EM/empty-Spring/ended-dispatch proof is unavailable, custody remains quarantined. The no-status test deliberately faults real `EntityTransaction.begin` after success within JPA's failed-begin cleanup extent; it does not certify every post-doBegin callback. |
| **Synchronizations are different** | Ordinary in-phase `TransactionSynchronization` callbacks are **not blanket-refused**; the authored join/commit-fault tests use them. Entry refuses *ambient* synchronization, and forbidden propagation is intercepted before suspension callbacks. An arbitrary callback stall cannot be turned into a bounded synchronous-stack termination guarantee. |
| **Propagation/configuration** | Only REQUIRED root/participation is allowed within this named phase; every non-REQUIRED definition and every other manager is refused before delegation. Nested transactions are disabled on both private wrappers, and a scoped JPA delegate with nested support re-enabled is refused. Outside a phase, wrapped ordinary dispatch is retained; it is not Boot bean-alias/customizer compatibility proof. |
| **Request/admission expiry** | This entry has no HTTP/request-selected deadline or authenticated W05 admission value. It enforces its existing finite ordinary checkout budget and accepted-lease work budget, including late acquisition-tail refusal. No absent earlier request-expiry integration is claimed. Primary must keep that broader request-admission gate distinct from this internal named slice. |
| **Uncertain Spring/cleanup completion** | Exact proof is required; no-status return or empty Spring flags alone does not refund. An unprovable failure can remain quarantined rather than pretending to have a status, manually unbinding, or fabricating closure. Retained custody is containment, **not bounded-resource-lifetime PASS**. The incident is a bounded retained failure/exception and occupied slot; no live operational incident sink is wired here. |
| **Production wiring and breadth** | All new product types remain internal/non-bean; `UNKNOWN`/production stay inert. Controlled minimumIdle0 fixture use proves nothing yet about Boot EMF/DS aliases, customizers, UTC/validation/Flyway, ordinary health/metadata or real deployment pools. There is no deletion phase, password/throttle/step-up split, complaint grant/capacity/audit writer, controller, scheduler or new live connection-free call site in this slice. |

The old live `JdbcAdminStepUpGrantRepository.deleteExpiredOrUsed` remains unbounded
and all-scope and was not rerouted. This dormant source-only store is **not a claim
that production cross-scope cleanup or all of §8 has been fixed**. The source/complaint
scope, SQL predicate, one-batch rule and count-only port remain the peer's fixed API.

## 4. Authored test oracles — all unexecuted

E's `tests.json` records exact method identities/lines from source text, not runtime
discovery: **13 ownership IT methods + 7 pure outcome methods**. The peer's six SQL/
scope methods are separately listed in its handoff and `peer-inputs.json` (26 authored
methods across the three test classes, **zero execution claims in this task**).

| Ownership IT case | Intended independent/real boundary |
|---|---|
| REQUIRED join | Same holder/lease/PID/xact, no early outcome/refund, real committed delete independently durable. |
| Wrong dispatch/propagation/extra borrows | Both overloads, wrong JPA/JDBC manager, nested entry and foreign adapter refuse with no extra acquisition/suspension; legal REQUIRED positive. |
| Ambient/unbound entry | Synchronization-only, known holder, actual unscoped tx and outstanding loan refuse; live positive controls before/after. |
| Missing/foreign selected holder | True transaction flags cannot authorize SQL; the negative sentinel cannot dispatch JDBC; original holder restored only by test finally. |
| Unscoped wrapped JPA | Real commit and immediate release without a short-phase permit. |
| Listener restriction | Nonempty execution-listener configuration refuses before begin/lease; clean configuration positive. |
| Failed begin without status | Real begin succeeds then test decorator throws; retained exact EM, real rollback/close and receipt required. |
| Post-status materialization fault | Test decorator faults the existing selected Hibernate lazy getter after retained status; rollback uses that status, without fallback borrow. |
| Accepted-but-undelivered acquisition | A real acquisition bookkeeping tail is held beyond2s; no body or premature refund, then real disposition. Handoff may seal this pool; no retry/retarget assertion is smuggled in. |
| Caps / shared budgets | Actual LOCAL caps plus additive offset-clock **MODEL** assertions of the original2s and one emergency1s identity; not resource-lifetime evidence. |
| Real blocking SQL | A real delete precedes `pg_sleep(5)`; assert session disappearance, restored row and released row lock, exact receipt and ≤3s measured **from the actual accepted-lease clock through the independent disposition probes**, not from query dispatch/Future completion. |
| Unknown native completion | Server termination in Spring beforeCommit; unknown lower outcome remains separate from authentic local refund and independent restored row/session disappearance. |
| Post-consent return tail / successor | Hold actual RETURN bookkeeping beyond2s after Spring unbinding; permit remains, old DB commit is durable, unscoped same-PID/new-epoch successor survives stale close, late commit remains known. |

The seven pure tests cover acknowledged commit versus later rollback/reset, sticky
unknown commit/rollback, known rollback versus clean reuse, nonterminal savepoint
rollback, successor outcome isolation, and post-outcome descendant work.

Test-only fault helpers use public JPA/Hibernate interfaces (`SessionImplementor`,
`JdbcCoordinator`, `LogicalConnectionImplementor`) and existing own-project instance
field interception for `PoolCallFrames.storage.current`. They do not replace a
static-final Spring/JDK ThreadLocal or fabricate receipt/count changes. Their actual
ThreadLocal restoration and thread joins/finally releases are **authored, not run**.
The existing retained PG/Hikari/physical fixture remains the real lifecycle owner.

### Runtime and review risks retained, not waived

- No compiler/static discovery checked these APIs, overloads, proxy interfaces,
  resource-key equivalence, import/format rules or fixture behavior. All require the
  separately admitted affected batch after actual-diff review.
- The unknown-completion fault must genuinely reach the lower commit invocation;
  an earlier read-cap/setup fault is not the same oracle. The intended server timing
  and UNKNOWN assertion are unexecuted and must be inspected in actual results.
- The5s barrier waits, real2s/1s bounds, no-status cleanup, true terminal receipt and
  same-session successor reuse are not inferred from source. If any deadline/resource
  proof fails, return the design/evidence to review rather than relabeling containment
  as success or loosening the bound.
- The synchronous old owner cannot be released while a held actual tail remains.
  The deliberate late-tail test is evidence intent for custody/stale safety, not a
  claim that arbitrary application/framework/native stalls are supported bounded faults.
- Fixture observer connections and all test cleanup need their actual owned cleanup
  result. Adding `requireConnectionFree()` at fixture close prevents independent row
  deletion from masking a leaked named owner; it is not itself a cleanup receipt.

## 5. Seed preservation and next primary inventory

E's passive catalog retains **all348 development07 source-path members**, manifest
SHA256 `3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`.
**348 is a source-path count, not a test count.** There are no missing seed paths.
At this capture299 are byte-identical to that historical seed and49 differ; those
historical/private-worktree differences are explicitly listed, not all attributed
to this resume or represented as an old-candidate PASS.

Membership is the union of all348 seeds, the full issue-baseline diff from
`c8bdff9a8acebb7c8e8ce40c65b8c7315ef9c014`, and every current untracked/nonignored
path. It includes **478 present paths** (including docs/tooling/vendor sources, not
478 product files/tests), **130 present paths outside the seed inventory**, and the inherited
absent `TransportBoundTestFixtures.kt` record. The full tracked issue diff names466
paths and current untracked membership is12, so committed additions cannot disappear
merely because they are clean relative to HEAD. The complete catalog has479 rows
including that inherited absence; no new removal was authored.

`source-membership.json` binds paths/current hashes/seed hashes/membership causes,
absence records and the deterministic full tracked issue-diff hash
`97846b15de02f78eda344e7b2f33d1c03e147e611692ad2e15bfb8f4f36933be`.
Untracked bytes are separately hashed; they are not falsely said to be in Git's
tracked diff. This is **only passive evidence collection**. Neither the old freezer,
new freezer, inventory validator/checker, tests nor any build was invoked. No execution
scope/tasks or all-repository ref preflight has been certified.

Two passive reads found the owned source hashes, backend status and HEAD unchanged
during capture. That is not an atomic freeze or continuing authority over concurrent
work. Primary must rebind the combined core/peer tree and preserve the348-member
seed when preparing its eventual candidate after both independent actual-diff reviews.

## 6. Exact evidence artifacts and next owner

E contains the unchanged initial before evidence, all21 after snapshots, exact
before→after and HEAD→owned-final patches (including all nine untracked owned files),
explicit changed-path lists, peer-only hashes, textual test inventory and passive
seed/current-membership catalog. `SEAL.sha256` seals all packet members except itself;
`REPORT.md` is an exact copy of this report. SHA256 bindings:

| E-relative artifact | SHA256 |
|---|---|
| `before.json` | `1c063bbd4facdf9759f5ee7178d67ecbc5a7beef55046d31b60b4bfbc01f9ec2` |
| `after.json` | `2ae9df839bd1ef71d6efc09161feadc0c31cde1f66c2efb470bd8ae9eb4d399a` |
| `owned-after.sha256` | `fc73337faba2689d52435c1a587d9299107d67423e2f324f8f16dbdd3c4c4bef` |
| `before-to-after.patch` | `a69b5e166e66edaad20d8340bae55301b553e32800a53db0ec9e63ef029d8aeb` |
| `head-to-owned-final.patch` | `b199d065b8a7964a8f9601d520f41923a1dadb6a426175778077b4529bc044a1` |
| `tests.json` | `ef2f245a5314d1480c635eec67075db349e90f0575ea007b520be19dd2a37d5f` |
| `peer-inputs.json` | `14e382c8f86ebb17e68226234ffa1a0455dbc552e6d5c1ec1ed40369aa1b12b3` |
| `source-membership.json` | `cd388b1d69d16b919bbef5f558c305b126ec1adc00143a9f54cceaef75606b6a` |
| `source-membership-current.sha256` | `9db1659df0579de78e7c8bbc25da557536313d352e644d84f7a2c080e351bcac` |
| `capture-observation.json` | `c841843af502ddf702c48bb0e7a78878e43dae1947eab0372ae30fe30d12bd5b` |
| `inputs.sha256` | `0a7411ef1e06c04a924789f675ba9a6ba27551c0592a315b9ddc5ddce5222aaf` |
| `summary.json` | `7c540d17593ec41695d2127c93181e5d4a86a56fe308b45e8e4b1177dd6eac43` |

No build/compiler, unit/IT/static check, dependency resolution, DB/container, test
worker, CI request, Git mutation/commit/push, external publication or subagent was
started by this author. Only read-only Git status/diff/ls-files, source/document
reads, passive inventory/digests and admitted source/evidence writes were used.

**Next:** primary dispositions the explicit hook/gate restrictions, obtains separate
technical and regression/security actual-diff reviews, then alone selects/fixes the
exact combined candidate and any affected validation batch with immediate owned
cleanup. This handoff authorizes none of those executions. Existing PG1/14+1/38
results remain separate; native/opaque/liveness/full47/consumer and complete P3
capacity/audit/step-up and production gates stay OPEN. W06/history is excluded;
NEW backend/installation recovery work remains required and untouched.
