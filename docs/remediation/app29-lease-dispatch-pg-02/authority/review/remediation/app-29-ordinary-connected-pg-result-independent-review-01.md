# W03 ordinary-connected PG01 — independent actual-result review

2026-09-13 UTC · `/root/app71_research_regression` · private0600.

**FAIL confirmed; do not accept PG21 or rerun the unchanged batch.** All21 intended
methods executed: **20 PASS /1 FAIL /0 ERROR /0 SKIP**. The single failure is the
native-commit-fault method's **owned-pool teardown**, following a real Hikari close
executor shutdown timeout. Collector success is not test success. No product
correction or further execution is authorized by this report.

## Independence and method

I am non-author of the ordinary-connected implementation, the selected21 tests,
and the PG01 carrier/collector. The admitted author scopes identify Admin01/core
and Backend02/peer ownership; carrier handoff identifies `w03_core_author_resume`.
I previously authored independent regression reviews, including
`app-29-ordinary-phase-connected-regression-correction-independent-review-01.md`.
Those are historical context, **not own-authored material approved again here**.
This review independently evaluates raw results; any follow-up proposal below is
unimplemented and requires separate author/non-author review.

Read workspace/backend `AGENTS.md`, scoped backend `docs/PLAN.md` context, the
accepted PG preparation, carrier actual-delta, literal-binding and execution-
preparation reviews, and primary preparation/admission records. No product/tooling
write, Git command, JVM, Gradle/test/checker, controller/helper import or execution,
service/process control, acquisition/network, CI dispatch or subagent was used.
Only passive text/JSON/XML/archive/classfile inspection, hashing and new review
artifacts were performed. Main agent retains acceptance, tracker and dispatch.

## Exact reviewed evidence

Workspace-relative aliases:

- **L** = `review/working/app-29-ordinary-connected-pg-admission-01/launch-01/`.
- **A** = L `artifacts/`.
- **C** = `review/working/app-29-ordinary-connected-pg-carrier-01/`.
- **E** = `review/working/app-29-ordinary-connected-pg-result-independent-review-01/`.

E `evidence-pins.tsv` names **95 exact paths, byte lengths and hashes**; it is the
complete pin inventory for this report, not a claim of full semantic review of
all source files. E `passive-findings.json` retains exact21 outcomes, the complete
failing XML trace, source/identity comparisons, process/cleanup projections,
container events and source read ranges.

| Evidence | SHA-256 |
|---|---|
| E `evidence-pins.tsv` | `0772c21e435835ac44e8284ffec42502774cd2f9b7eb3bb42ada9d993b88f05a` |
| E `passive-findings.json` | `8f14d105b596512d087de8c22853190264ef6f14edc2d5079a11654bec13e543` |
| A `result.json` | `750de524bf2a76805a33f0453a93177e4fe14b74a810bcacdb74bc04073eb30c` |
| A `gradle-test.log` | `ba8a9a958fc7978f3078149752f8cc2cad7bcd08f99aa755a24cd1827f9f1896` |
| L `workflow.log` | `6a16e2ddf098db9d2ccbe8347743e8078b747ad44f36e42ceea48dd7cca91c97` |
| L `run-final.json` | `58054685b9ddb7827c12afdbfebd941c9365e6d4e058769b8b2670d558c9a78c` |
| L `collection.json` | `c0fd7b6f7acec53b3399240797a61b8e579ca9a15506cf3f8f7664b9369087c4` |
| L `lane-release.json` | `9ea6130d4202c1e4e3f673b0bc2622a2f8233b7d4614ddd736c3511cc81c32f1` |
| A OwnershipIT XML | `de0a3b68933690ca5309411057b164575c4b2b51f759c8da32a9e425b2177835` |
| A CleanupIT XML | `24c0e99c5aa39e7d8ae3a76e943bbf2f7ae90f464c60fc09ede1eb4a47e9af23` |
| A before/after `source-hashes.json` (each) | `a25ec55bc80af083cd87087bd11a76b737df7a38c7b53feac6bbcf0c9dbe639a` |
| A `container-events.log` | `09384fa956b85de4cc7286aabcd30978ebb3dd4b269f37cfcbb56d7bc53916e7` |

Both XML files are under A `test-results/test/`, named
`TEST-me.manga.kira.backend.common.infrastructure.persistence.<class>.xml` with
classes `OrdinarySourceGrantCleanupOwnershipIT` and `OrdinarySourceGrantCleanupIT`.
I parsed both full XML documents and their identities/counts, read the complete
failure and relevant stdout fault/startup/teardown regions, and searched both
stdout/stderr for diagnostic rows. Gradle/workflow logs were read; large class-load
text was inspected for relevant actual origins, not exhaustively interpreted.
All59 raw files were independently rehashed against collection inventory; all58
non-result files also match the controller's retained inventory, and all four
captured report hashes match. No missing/extra files, mismatches or symlinks.
Workflow and artifact metadata agree on the uploaded332075-byte ZIP's digest
`3185ec305a97e113c04b6bd2cf004b7e05bf5162325b91c055a2e4cd69fb8ace`.
The ZIP itself is not retained locally; extracted-file hashes, not a fresh ZIP
rehash, were verified here.

Relevant C controller ranges581–650,823–906,940–1053 and collector85–106 were read
as text to interpret failure, collection and cleanup—not executed or reapproved.
Exact test/fixture/pool/native-dispatch source ranges are listed in E findings.
The reviewed source files rehash to both frozen and hosted before/after maps.

## Actual run, counts and failing stage

`run-final.json`: run **34745356347**, attempt1, completed/**failure**, carrier
`9587cb74ecc51f39b749c6060326e59d4eb3dab9`, private remediation branch.
A `result.json`: **FAIL**, Backend
`ccdbb28f6362117882501b4da040257be6fc1990`, elapsed323.281s, cancelled=false.
Workflow276 records controller exit1; raw Gradle records :test failure/exit1.
The parent-reported collector session96120 exit0 means collection completed:
collector96–100 records the remote conclusion and prints collected without
requiring test success. L collection explicitly says `RAW_RESULT_REVIEW_REQUIRED`.

| Class | Intended / executed | PASS | FAIL | ERROR / SKIP |
|---|---:|---:|---:|---:|
| OrdinarySourceGrantCleanupOwnershipIT | 15 /15 | 14 | 1 | 0 /0 |
| OrdinarySourceGrantCleanupIT | 6 /6 | 6 | 0 | 0 /0 |
| Total | 21 /21 | 20 | 1 | 0 /0 |

The21 XML `(class, display_name)` pairs are unique and exactly equal to the
admitted profile/selection. Exact43 task argv match selection, fresh manifest,
profile and actual Gradle command tail. No missing, duplicate, extra or skipped
case; no initialization-only substitute. The sole failed method is:

`OrdinarySourceGrantCleanupOwnershipIT.native commit failure stays unknown after Spring cleanup while authentic local quiescence permits only refund()`

Gradle17–25 shows ordinary main/test Kotlin compilation reached completion;
35–42 and61–62 show21 tests completed/one failed, six actionable tasks executed.
This is not a compile, dependency-resolution, Docker-startup, global900s validation
budget, workflow cancellation or artifact-upload failure. No new Ktlint/Detekt
result is claimed for this run.

## Proven failure chain — not merely the controller's type labels

1. Ownership XML171–203 records the **real native commit** stack through
   `PgConnection.commit`, lower facade, Hikari, lease facade, Hibernate and Spring,
   with SQLSTATE **57P01**, “terminating connection due to administrator command”.
   The pinned test530 deliberately terminates that exact PID in beforeCommit;
   this PostgreSQL error is the intended fault, not the uncaught JUnit failure.

2. XML295–298 records EMF destruction, then HikariPool-11:
   - 07:34:24.331: shutdown initiated;
   - 07:34:34.333: **“Timed-out waiting for close connection executor to shutdown”**;
   - 07:34:34.333: Hikari's “Shutdown completed” log.
   The last log is not a proof that the executor terminated: the preceding
   timeout explicitly contradicts that interpretation.

3. The sole XML failure's primary trace is
   `PersistenceBoundaryException: TIME_BUDGET_EXHAUSTED` →
   `PersistenceTimeBudget.remainingMillis:27` → `awaitLifecycleFact:86` →
   `OwnedCutPool.close:1415` → `withOwnedCutPool:1379` → ordinary fixture → test513.
   It contains no suppressed failure. OwnedCutPool1415–1419 waits for its authentic
   shutdown receipt to become non-PENDING; `awaitLifecycleFact` defaults to8000ms.
   Thus the directly observed failing obligation is **pool completion observation
   remaining PENDING through that bounded wait**, after Hikari's10s timeout.
   The18.654s method duration and next fixture at07:34:42.369 agree with this chain.

4. At source level, PoolLifecycle110–119 retains one original shutdown budget
   (default10000ms), and456–461 returns PENDING when that budget is exhausted,
   before observing actor terminations. It never replaces the original budget.
   Hikari's observed10s close wait is sufficient to consume that allowance;
   an earlier supplied allowance would not be restarted at fixture close.
   Increasing only the later8s fixture wait cannot repair an exhausted pool
   receipt. Setting `expectedPoolUnknown` alone also cannot help: the expected
   outcome comparison occurs only **after** the failing non-PENDING wait.
   Exact budget/actor scalar values were not captured; this is a source-grounded
   explanation of why waiting longer is not a justified correction, not a claim
   of an unrecorded scalar snapshot.

The primary `.use` close failure, together with the pinned composition, places
this failure after the business lambda returned, including its native-fault,
UNKNOWN, quiescence, row/session and local-refund assertions. There is no separate
per-assertion receipt; this is a control-flow deduction, **not a PASS for this
method**. Its required pool teardown is part of the method and failed.

A result's six failure records are not six independent incidents. The validation
ValueError follows `command`644 rejecting Gradle exit1. The five
`*-nonzero-child` records each retain that same PID2290/exit1 in successive drains
(controller614–648). The `interrupted-gradle-test` label is also used for ordinary
nonzero command exceptions; cancelled=false and empty term/kill lists prohibit
calling it an actual cancellation here.

## Mechanism narrowed, but missing runtime state must stay missing

The local **HikariCP6.3.3** JAR rehashes to actual classpath SHA
`709f378c05756280939ce50fc1b1f1a53bb8e1899dc1b249f21f12703640b48b`.
Passive Code-attribute/reference inspection—not JVM execution—finds:

- `ProxyConnection.checkException`, bytecode231: `PoolEntry.evict` after its
  matching broken-connection warning;
- `PoolEntry.evict`, bytecode6: `HikariPool.closeConnection`;
- `HikariPool.closeConnection`, bytecode28: `closeConnectionExecutor.execute`
  after successful bag removal;
- `HikariPool.shutdown`, bytecode283: `awaitTermination(10, SECONDS)`, with its
  observed close-executor timeout warning at293–295.

This directs the smallest further source investigation to **implicit Hikari
broken-connection eviction inside a BUSINESS JDBC exception tail**. Current
LeaseJdbcFacade75–126/PersistenceJdbcLease64–66 establish JDBC dispatch, not a
PoolCallFrame. PoolLifecycle245–249 recognizes an active issued pool frame or an
authentic retained pool actor as creator. PoolActorCustody140–149 refuses null
creator with `UNAUTHENTICATED_CREATION`/factory seal. PoolCallKind112–117 has only
ACQUISITION, RETURN, EVICTION, SHUTDOWN. Thus a first automatic eviction requesting
a close worker from a BUSINESS caller is a concrete provenance edge to inspect;
later explicit RETURN/EVICTION coverage does not by itself cover that earlier
Hikari error path.

**PG01 does not record whether that creator-refusal branch happened**, whether
there was already a close worker, the queue size, the exact actor fault or the
remaining shutdown budget. Do not promote the static lead to a measured root-cause
claim or assert a specific leaked worker. The proven raw cause remains the
close-executor shutdown timeout followed by failure to prove pool completion.
Both suites intentionally emit zero PG14 scalar rows (`NOT_APPLICABLE`), so the
existing diagnostic collector cannot answer those missing-state questions.

## Source identity and cleanup findings

- Public prerequisite initially `3d839130c807f6a0a9b1c896c1c6cca4b41c4538`; retained
  source-bundle verify/fetch/checkout logs import the private ccdbb28f target.
  Before/after branch, SHA, seven commit records, full tracked inventory and source
  hash maps agree. Independently deriving Git commit-object SHA1 from retained
  bytes—not invoking Git—reproduces the target and six ancestry objects. Target
  tree `d172ecf246a9606194f43023a0703d778b877566`, direct parent6db94487.
- Exact **863** unique tracked paths in both NUL inventories, both status files
  empty, all863 before/after hashes equal. These are not the governed count.
  Fresh manifest `7c5e775dc0250948ead0ba20aff89cb38e2565fdbb82751575291fa96a80d63c`
  names **478** governed paths; every one equals both hosted maps and the current
  local Backend bytes at review. Source-binding before/after records remain
 478/348 seeds/211 snapshots/540 authority files. The latter historical/full-
  authority checks retain accepted prep scope; this result review did not rerun
  the freezer or semantically re-audit all540 authorities.
- Classpath has186 unique entries, one profile-pinned PostgreSQL supplier and
  checker supplier, and the stock42.7.12 JAR is removed. Actual class-load lines
  identify Hikari6.3.3, compiled test/main directories and PgConnection from
  candidate SHA `50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`.
  Actual runtime is Temurin21.0.12.1+1-LTS. These are context facts only.
- All five owned process drains report empty/ok/NORMAL_ABSENT, no adopted child,
  no remaining active handle and no controller term/kill action. The sticky
  nonzero Gradle result remains in each receipt. Both Gradle-stop logs report no
  daemon. All **11** owned output obligations are cleanup-attempted/complete/absent;
  capture_complete, retained_inventory_complete and inputs_preserved are true.
  There is no separately observed controller file/container cleanup failure.
- Exactly **two PostgreSQL17.6-alpine +one Ryuk0.12.0** were created, in one retained
  Testcontainers session. All three were destroyed and final census is empty.
  Raw14 events explicitly include **kill9 → die137 → destroy for each PG container**;
  Ryuk dies0/destroys. NORMAL_ABSENT means controller-unforced final absence, never
  graceful PostgreSQL shutdown or zero-kill proof.
- XML contains6+15 `PG_LIFECYCLE_ROOT_CLEANUP ... TRACKED_LOCAL_ENDED actors=12
  all_terminated=true` markers, including after the failed pool wait. Those refer
  to PgLifecycleTestScope's native-root actors, **not the separate Hikari actor
  population**. They do not repair the failed pool receipt; later JVM/container
  disappearance does not repair it either.
- L lane-release has truthful completed/collected flags but its nested `run` is the
  earlier `in_progress` discovery snapshot, including an older workflow label.
  Use L run-final/collection/workflow for terminal identity/conclusion. Preserve
  original evidence; this bookkeeping staleness is not another runtime failure
  and must not be read as a successful run or fresh launch authority.

## Smallest justified next check / disposition

1. Keep this attempt **failed with20 observed passing methods**, not accepted21.
   Preserve the native-fault method and its complete teardown assertions. Do not
   widen budgets, prewarm the close executor, skip/mark-passing the failed test,
   relabel a pending receipt UNKNOWN, weaken creator admission or rerun the same21.
2. First audit the narrow implicit-eviction creator path above against the exact
   retained Hikari/JDK semantics and the lease's full exception/finalizer extent.
   A proposed correction must establish authentic, exact-pool/lease/caller-bound
   creator lifetime through the whole Hikari tail, not grant authority merely
   because a thread can call JDBC. No product patch is justified by an assumed
   actor-fault/queue value from this run.
3. If that bounded source review cannot settle the mechanism, the minimum new
   evidence proposal is test-only scalar capture for **this native-commit-fault
   case**, before/after pool shutdown and on observation failure: actor first
   fault/retained/constructing/future-entry counts, original budget remaining,
   close-executor queue/pool/active/completed/shutdown/terminated and real close
   result. Reuse the existing read-only scalar approach without making the
   diagnostic a completion proof or cleanup action. Use a distinct new case/profile
   binding; do not impersonate either historic PG14 case or rewrite its evidence.
   This is a proposal for primary review/admission, not permission to execute.

The two real-PG suites have no population gap, but **the failed pool completion
obligation and unobserved executor/creator state are material gaps**. Accepted
Linux03's56 nonDB, PG1's one case, PG14, PG10 and older failures remain separate,
not additions to21 or grounds for accepting this attempt. Consumer/original-
provider/full47, opaque/native-finalizer/pin/compaction/liveness/recovery, Native05,
full-P3/W03/App29/production/native gates remain open; Native05 is UNQUALIFIED.
UNKNOWN database outcome supplies neither success, replay nor reconciliation
permission. This review confers no integration, closure or public-push authority.
