# W03 connected ordinary phase — independent regression correction review01

2026-09-13 UTC · `/root/app71_research_regression` · private0600.
**CONCUR at source-review level: B1/B2 are addressed; no new blocking regression
finding in this bounded correction. UNCOMPILED / UNEXECUTED.** This is not execution
admission, a runtime PASS, ownership-review substitution, or W03/P3 qualification.

Private backend baseline: `6db944871c1584bd6a1f28263e8010cadd766fab`.
Never publicly publish that ancestry or this evidence.

## Reviewed evidence and preservation

The original regression report and correction agreement were read before the corrective
delta. The actual four-path patch and relevant current source were reviewed, with bounded
supporting reads of the retained Spring/native dispatch and fixture sources.

Paths in this table are under workspace `review/`:

| Authority | SHA-256 |
|---|---|
| `remediation/app-29-ordinary-phase-connected-regression-independent-diff-01.md` | `3ccfff09f4a9f1593e4867b7e019c1b912de4359382d0e94b32f6995763438ad` |
| `remediation/app-29-ordinary-phase-connected-correction-agreement-01.md` | `c363d521fe7fa8f97fa1d6b6957d9d1cb5c7ff8f4c97a24a00c7385ecba078ec` |
| `remediation/app-29-ordinary-phase-connected-correction-handoff-01.md` | `6b63d53a4591398389feac4b99a8beb9d45ed761a8360f544f68d40e50c6e2f5` |
| `working/app-29-ordinary-phase-connected-correction-01/SEAL.sha256` | `1ebcb7bf0afbb90e0536240c405011f428c16ed42a6048aa016766eb4a32f12c` |
| `working/app-29-ordinary-phase-connected-correction-01/core02-to-correction.patch` | `d3c5aae0108aa17acfbf26b634bb1c103dcb5a6b2b6e05ff1041c7e75c725140` |

All correction seal members and eight pinned supporting references match. The four
before snapshots equal core02's after snapshots; the four current files equal the
corrected snapshots and hashes below. The other17 core files equal their core02
snapshots and expected/current manifests; all three peer files match the supplied
unchanged pins. Core02's seal still hashes to
`86fa8cebb700c34a758bc474d7f0b3a90c222c69e6b867a35ee0a85480a68767`.
These are passive byte checks, not a requalification of the complete348-seed/478-path
inventory or the primary's next combined freeze.

**P/** = `kira-backend/src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`;
**Q/** = the corresponding `src/test/kotlin/` directory.

| Corrected current file | SHA-256 |
|---|---|
| `P/GuardedJpaTransactionManager.kt` | `551e6c9295566f522f55bcafba7d54b98314c8dc34b003c940277e3d81404f00` |
| `P/PersistencePhaseOwnership.kt` | `19d2e91e3358316c2a369fc62e09a566b0e14fc15bdaefb44310cd36d8a5e500` |
| `Q/OrdinarySourceGrantCleanupFixture.kt` | `4cea94d0f27384bd16ae00f8ea0dad4f446e890412f6f1506b95497028a7d461` |
| `Q/OrdinarySourceGrantCleanupOwnershipIT.kt` | `0a2e78581410bc91df644acee2110fd6993f0b746efd0c93ec6cda8034dbede5` |

## Regression correction findings

- **B1 — nonvacuous sleep oracle.** OwnershipIT452–493 and Fixture179–245 now
  require a positive independent `pg_stat_activity` witness for the exact PID and
  backend-start in active `Timeout/PgSleep`, outside `assertThrows`. Only scalar
  identity/time data cross to that observer. It prepares its own connection/statement
  before acceptance, bounds polling and JDBC reads, closes its own resources with
  `use`, and must stop/join in the test's finally. The actual accepted-lease clock,
  restored row, independent lock acquisition, old-session disappearance and retained
  lease's quiescent completion still must fit **1..3000ms**. A pre-sleep setup refusal
  no longer passes; no Future timeout or elapsed-time surrogate supplies the witness.

- **B2 — lower commit failure, not rollback-derived UNKNOWN.** OwnershipIT497–534,
  785–860 select one exact lower BUSINESS `commit`/call/root, prepared with outcome
  NONE, then armed and unended with ORDINARY_FAILURE and UNKNOWN. Preparation/arm
  failures, observation errors and additional commits are rejected. The unchanged
  `PhysicalJdbcFacade.kt:207–245` validates/prepares/arms before `Method.invoke`, sets
  the invoked flag immediately before it, and records `connectionFailed` only when
  native return did not occur. `failedBeforeBoxing` publishes failure before the
  subsequent same-frame observation, native end, and any Spring rollback. Successful
  native return instead records COMMITTED before output handling. This closes the
  original alternative path. The tap delegates/restores the existing instance TL;
  it does not assign driver/call/outcome/receipt state. Assertions require actual core
  end and native arm/disarm/end outside the expected-error extent. The real remote
  fault and independent row/session checks remain; local refund does not resolve UNKNOWN.

- **Real afterCommit interruption.** OwnershipIT538–575 checks independently durable
  deletion in the reached callback, then throws an actual `InterruptedException`.
  Post-executor assertions jointly require COMMITTED on failure/receipt, exact matching
  quiescent cleanup, zero owners, connection-free state, and the original caller's
  restored interrupt; only test finally clears it. The pinned Spring afterCommit/finally
  ordering and current manager failure/finalization path support this authored oracle.

- **Actual read caps.** OwnershipIT410–448 and579–650 add JDBC `networkTimeout`
  scalars, not merely MODEL-clock values. The existing ordinary fixture defaults to a
  3000ms socket cap; assertions demand a positive cap no greater than1000ms in-phase.
  The successor must be the original PID in a new epoch, with the original cap restored
  both before and after stale old close. MODEL budget assertions remain explicitly separate.

- **H1 fixture/calibration only.** The new negative first calibrates real exact-pair
  creation/begin/acquisition and a healthy foreign same-endpoint EMF's real begin/query/
  rollback/close. It then requires unchanged creation/begin and both resource-acquisition
  histories across foreign/unknown/null metadata refusals. The foreign factory reuses
  the existing independent reader, not a new pool. Forwarding metadata preserves the
  existing failed-real-begin/lazy-holder faults. No additional fixture blocker found;
  H1 product/resource ownership remains the other independent reviewer's decision.
  Existing occupancy counters are not reinterpreted as cumulative acquisition history.

- **L1 disposition respected.** The bounded entry code is preserved after successful
  unused-entry cleanup; unexpected failures stay value-free. The primary explicitly
  withdrew the synthetic quarantine test request. No replacement test or wider incident
  framework is requested here; existing quarantine/custody gates remain open.

## Remaining gates

Textual source inventory confirms **15 ownership +7 pure +6 peer =28 authored methods**,
with the original13 ownership methods retained. This is not JUnit discovery or execution.
Actual observer scheduling within3s, remote-fault arrival at the exact lower commit,
real afterCommit cleanup and same-session cap restoration require the primary's later
bounded validation; a failure must not be hidden by weakening these oracles.

Only passive source/document/hash inspection and this report write were performed:
no source edits, Git operations, builds, static/project checkers, helper imports,
tests/runners, network/CI, runtime services, cleanup or new audit. Delegate privacy and
unsupported listener/customizer/nested composition remain explicit. Live wiring/W05,
operational sink, full P3/native/opaque/liveness, production UNKNOWN handling and NEW
backend/installation recovery remain outside this concurrence.
