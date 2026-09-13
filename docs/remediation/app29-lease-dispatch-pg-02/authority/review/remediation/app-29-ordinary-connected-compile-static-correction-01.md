# W03 connected ordinary phase — first Linux compile/static correction01

2026-09-13 UTC · `/root/backend20_correction_review` · private0600.
**SOURCE AUTHORING ONLY — UNCOMPILED / STATIC CHECKS NOT RERUN / TESTS UNEXECUTED.**
Request independent actual-diff review and primary-owned validation; this is not
self-approval, a static PASS, W03/P3 acceptance or production qualification.

## 1. Scope and authority

Worktree: `/root/projects/Kira/kira-backend`, branch
`remediation/app-29-backend-complaints`, unchanged private HEAD
`6db944871c1584bd6a1f28263e8010cadd766fab`. **Do not publicly publish this ancestry or private evidence.**

Read root/backend AGENTS (no deeper backend AGENTS found), applicable PLAN architecture,
persistence/security/completion/test boundaries, SECURITY, complaint lifecycle and current
remediation owner boundaries; read the connected plan/admission, source/correction handoffs,
current Linux selection and bounded ownership correction review before edits. Historical
owner-doc development07 status is not the result of this new connected batch.

Primary assigned only reported W03 connected paths, permitted explicit Java setters and
scoped formatting, and then specifically permitted justified declaration-local complexity
suppressions where restructuring ownership/dispatch/finally order merely for numeric limits
would be inappropriate. No file-wide suppression, baseline/config change, guard removal or
broad refactor was authorized or performed. Primary retains heavy-lane, tracker and
notification ownership.

Control inputs under `review/remediation/`:

| Input | SHA-256 |
|---|---|
| `app-29-ordinary-phase-connected-linux-selection-01.md` | `38ecd98127413de86a67b7464f2645e18a46a40a4bebb5fd81a0b46f0a194200` |
| `app-29-ordinary-phase-connected-correction-agreement-01.md` | `c363d521fe7fa8f97fa1d6b6957d9d1cb5c7ff8f4c97a24a00c7385ecba078ec` |
| `app-29-ordinary-phase-connected-correction-handoff-01.md` | `6b63d53a4591398389feac4b99a8beb9d45ed761a8360f544f68d40e50c6e2f5` |
| `app-29-ordinary-phase-connected-source-handoff-02.md` | `ae011b05b5d0899274a2751daadedc79fb29f4ba247ead9dcdcd61ec11724919` |

## 2. Actual first Linux failure — not historical test failures

`review/working/app-29-ordinary-connected-linux-01/validation.log` records:

- `compileKotlin` failed on **two** `'val' cannot be reassigned` assignments:
  `P/GuardedJpaTransactionManager.kt:42` and `P/PersistencePhaseContext.kt:57`.
- Main Ktlint: **24** findings; test Ktlint: **61** findings.
- Detekt: **27** weighted findings: 2 cyclomatic, 1 nested depth, 2 function-count,
  10 complex-condition, 1 long-method, 8 broad-catch, 1 swallowed-exception,
  1 throws-count and 1 max-line-length.
- **No tests executed.** Main compilation prevented test compilation/execution;
  `test_evidence=null` and no retained main/test bytecode. The runner's test-evidence
  `ValueError` is missing test evidence, not a discovered JUnit failure. These are
  not development07's two historical failing tests.
- Validation exit1; the retained result reports both Gradle stops exit0, five natural
  descendant barriers, no forced signal, outputs absent and frozen/dependency inputs
  preserved. Those are observations from the retained run, **not cleanup rerun here**.

Exact failure inputs (paths relative to `review/working/`):

| Input | SHA-256 |
|---|---|
| `app-29-w03-integrated-driver-ordinary-connected-01/manifest.json` | `064ec427d6dda2acb7027487cc5279bfb1e8ff8578cb3c8ef0ecc6deadd2766e` |
| `app-29-ordinary-connected-linux-01/result.json` | `44ae613363dbbe9bd11e5873c1da14f565ba717bbcb7ef08b24c118c773e3bb3` |
| `app-29-ordinary-connected-linux-01/validation.log` | `995a23c821557859eacca7df3ce70691a479a9f4f89f4c142ea1f21f19f17516` |
| `app-29-ordinary-connected-linux-01/reports/reports/detekt/detekt.txt` | `a4e514fa7f8de1a6261c0da6bb9482d7228dbb2c1e8280dc8870939fa996e537` |
| `app-29-ordinary-connected-linux-01/reports/reports/ktlint/ktlintMainSourceSetCheck/ktlintMainSourceSetCheck.txt` | `3fcb150ad9ef5b0ba24877e233a50df1d0163fdcb0184f6849da8b1ef8d10b47` |
| `app-29-ordinary-connected-linux-01/reports/reports/ktlint/ktlintTestSourceSetCheck/ktlintTestSourceSetCheck.txt` | `fe866f71b648677f6e2e20ede9b01397c29988f51ee64946d187490247d2ebe9` |

The frozen run's issue-baseline diff remains
`97846b15de02f78eda344e7b2f33d1c03e147e611692ad2e15bfb8f4f36933be`.
It is not this author's incremental correction patch.

## 3. Compiler correction and preserved behavior

Both diagnostics reject assignment through the effective Java-property projection. The
minimal correction invokes the Java mutator explicitly, rather than changing any Kotlin
owner/state `val` to `var` or changing transaction configuration:

1. `GuardedJpaTransactionManager`: `setJpaDialect(supportedDialect)` in the same private
   delegate `apply` block, still **after** Spring autodetection. The retained Framework
   6.2.19 `spring-JpaTransactionManager.java:296–304` supplies this setter/getter; the
   setter stores the passed non-null dialect. The earlier exact EMF/DataSource check and
   later exact effective EMF/DS/dialect validation are unchanged. No DataSource reset,
   new discovery borrow, injectable delegate or factory-customizer acceptance was added.
2. `PersistencePhaseContext.begin`: `setName("SOURCE_GRANT_CLEANUP")` on the same
   `DefaultTransactionDefinition`, with REQUIRED and timeout2 unchanged.
3. The already-reported `Q/OrdinarySourceGrantCleanupOwnershipIT.kt:215` contains the
   identical `DefaultTransactionDefinition.name` assignment in its existing unscoped
   positive. It now uses `setName("ordinary-positive-control")`; its name assertion is
   unchanged. **This third occurrence was found in source, not a test-compiler diagnostic:**
   the first batch never compiled tests.

No compiler-internals/nullability-bug diagnosis beyond the observed read-only projection
is claimed. Explicit-setter compatibility still requires the normal primary-owned compile.

All remaining changes are manual layout/braces, comments, local rule suppressions, and
renaming one unused catch parameter to `_`. Existing predicate operand/short-circuit order,
catch/finally order, broad-catch coverage, dispatch/scanner/driver/lease authority, SQL and
outcome transitions remain unchanged in this delta. No runtime branch was removed or
replaced to meet a metric.

## 4. Static findings addressed in source, not claimed green

### Ktlint — manual scoped layout only

All 85 retained Ktlint findings are covered by the authored layout corrections:

| Reported file | Count | Layout correction |
|---|---:|---|
| `P/GuardedJpaTransactionManager.kt` | 7 | Fitting constructor signature, supertype line, declaration spacing, multiline-if braces. |
| `P/PersistenceJdbcGuardProtocol.kt` | 1 | Space before annotated phase field. |
| `P/PersistenceJdbcLease.kt` | 1 | Multiline-if braces, unchanged guard. |
| `P/PersistencePhaseContext.kt` | 13 | Annotated-field spacing, when-branch spacing and multiline-if braces. |
| `P/PersistencePhaseOwnership.kt` | 1 | Space before commented declaration. |
| `P/PersistenceProducerEpoch.kt` | 1 | Space before annotated phase field. |
| `Q/OrdinarySourceGrantCleanupFixture.kt` | 4 | Fitting signature and wrapped expression body for `newExecutor`. |
| `Q/OrdinarySourceGrantCleanupIT.kt` | 3 | Join three fitting expression-body signatures and reindent their existing bodies. |
| `Q/OrdinarySourceGrantCleanupOwnershipIT.kt` | 54 | Signature/supertype/argument wrapping, statement braces/newlines, when/annotation spacing, max-line fix. |

No Ktlint rule was suppressed. No formatter was launched. The peer IT edit is formatting
only; its scope/expiry/50-row/SKIP LOCKED/clock/rollback assertions and six method names
are unchanged. Ownership tests retain their original assertions, observation ordering,
reflection targets, locks, joins, time budgets, positive/negative controls and 15 methods.
There are no new tests or altered failure extents.

### Detekt — exact retained locations and rationale

Locations below refer to **Linux01 pre-edit lines**, so they map directly to retained reports.
Each suppression is method-local, except the two explicitly named class-only function-count
suppressions. Existing exception suppressions in `closeActual` and `invokeGuarded` were
extended only for their newly reported rule.

| Reported site(s) | Reported rules/count | Authored disposition/rationale |
|---|---|---|
| `P/LeaseJdbcFacade.kt:54`, `invokeConnection` | CyclomaticComplexMethod (1) | Local suppression; keep one invocation's admission, checked-failure adaptation, output handling and dispatch-finally extent together. |
| `P/PersistencePhaseContext.kt:18` | TooManyFunctions (1;46/40) | Class-only suppression; all transitions retain one phase/permit/lease custody identity, not separate authorities. |
| Same, `authorizeAcquisition:129` | ComplexCondition (1) | Local suppression; selected resource/start stage and single-use authority stay one pre-checkout gate in the same evaluation order. |
| Same, `requireSelectedHolder:180` | ComplexCondition (1) | Local suppression; verify actual Spring flags and exact holders before consulting the retained holder's connection. No moved materialization/lookup. |
| Same, `beforeCompletion:213` | ComplexCondition (1) | Local suppression; root completion must match its commit/rollback stage without overlapping dispatch. |
| Same, `connectionKind:264,275` | CyclomaticComplexMethod + ComplexCondition (2) | Local suppression; preserve the closed JDBC capability table and full rollback-stage conjunction, including read-cap cleanup classification. |
| Same, `finish:347,352` | NestedBlockDepth + ComplexCondition (2) | Local suppression; rollback requires the returned/incomplete status and ended begin/no active completion; restoration flag reset stays nested inside the same cleanup/catch/finally boundaries. |
| Same, `finish:356,374,384` | TooGenericExceptionCaught (3) | Local suppression; every failure still records bounded failure/interrupt state and retains retirement/finalizer custody, including non-Exception throwables. No raw cause/logging added. |
| Same, restoration catch `finish:391` | TooGenericExceptionCaught + SwallowedException (2) | Rename unused `problem` to `_`, with a precise comment. Raw details are intentionally discarded, **but** CLEANUP_UNRESOLVED and `springSettled=false` remain; this path still forbids a refund claim. No SwallowedException suppression added. |
| Same, `springCompletionProven:404,409` | ComplexCondition (2) | Local suppression; neither empty Spring state nor no-status begin alone proves ended dispatch and exact EM closure custody. |
| `P/PhysicalJdbcDescendants.kt:465`, `invokeGuarded` | LongMethod (1;100/100) | Extend existing method suppression; child logical close, driver/output capture and final dispatch accounting remain in the same guarded extent. |
| `P/PersistenceJdbcGuardProtocol.kt:56`, `PersistenceJdbcGuardContext` | TooManyFunctions (1;42/40) | Class-only suppression; entry/child/native-driver/phase seams share the same private graph and authorities. |
| `P/PersistenceJdbcLease.kt:142`, `closeActual` | ComplexCondition (1) | Extend existing method suppression; requested retirement, poisoned epoch, failed child graph and uncertain transaction each veto reuse before Hikari close, inside the same retained return tail. |
| `Q/OrdinarySourceGrantCleanupOwnershipIT.kt:821`, `OrdinaryCommitObservation.get` | ComplexCondition (1) | Local suppression; the single live-call discriminator still excludes setup/wrapping/later-rollback failures. No observation moved or weakened. |
| Same, `OrdinaryReturnTailBarrier.remove:1035` | ComplexCondition (1) | Local suppression; caller identity, genuine RETURN frame, consent and the one-shot CAS remain in the same order before actual tail end. |
| `P/PersistencePhaseOwnership.kt:25,48`, `enterSourceGrantCleanup` | ThrowsCount + TooGenericExceptionCaught (2) | Local suppression; ordered fail-fast refusals preserve each side-effect boundary; catch settles only genuinely unused entry custody and preserves the existing bounded reason. |
| Same, `PersistenceManagerDispatch.getTransaction:149` | TooGenericExceptionCaught (1) | Local suppression; retain scoped begin/status-validation failure before finally, while unscoped throwables remain rethrown unchanged. |
| Same, `PersistenceManagerDispatch.complete:165` | TooGenericExceptionCaught (1) | Local suppression; retain scoped failure/interrupt state without replacing separately recorded DB outcome, then end dispatch in the original finally. |
| `T/OrdinaryPersistencePhaseExecutor.kt:22` | TooGenericExceptionCaught (1) | Local suppression; every work/completion failure reaches the same phase finalizer and bounded outcome/refund result. |
| `Q/OrdinarySourceGrantCleanupOwnershipIT.kt:630` | MaxLineLength (1) | Wrap the existing `assertEquals` arguments; same same-session JDBC-cap assertion/message. |

The table accounts for all27 findings: 24 are covered by rule-specific declaration-local
suppressions, two by the explicitly discarded restoration-catch parameter, and one by
argument wrapping. The exact original diagnostics are also indexed in `E/reported-findings.json`.
This is authored disposition, **not evidence that Detekt accepts these bytes**.

## 5. Exact correction delta and preservation

**12 existing WIP paths, +223/-117.** No source path was added, deleted or renamed.
P = `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`;
Q = matching `src/test/kotlin/` package;
T = `src/main/kotlin/me/manga/kira/backend/complaint/infrastructure/transaction/`.

The requested patch is **pre-correction current WIP → authored current WIP**, including
already-untracked files as modifications. It is **not HEAD → worktree** and must not be
mistaken for the earlier authors' much larger core/peer contribution. Ordinary Git diff
would omit untracked files and include prior tracked work, so the patch uses exact saved
preimages. No patch application/check command was executed.

- Patch: `review/remediation/app-29-ordinary-connected-compile-static-correction-01.patch`
- SHA-256: `1480fc3e3ed99b9b63c172a34491171811c59b4e40937fb3f3c6b31bf681506d`
- Bytes: **45769**; paths: **12**; line delta: **+223/-117**.

| Path | Before SHA-256 | After SHA-256 | Delta |
|---|---|---|---|
| `P/GuardedJpaTransactionManager.kt` | `551e6c9295566f522f55bcafba7d54b98314c8dc34b003c940277e3d81404f00` | `5fd30b1120b4beb6e006264209833935b883bdb3d604b9b855c5eeedf1899b53` | +10/-7 |
| `P/LeaseJdbcFacade.kt` | `b7abcce6314860ffb90df58c4d13a402ee5cbe08bbbfc3489ed0bc37d80d29c2` | `9a7ce9fcb0022420975b8144eb6c55328ffe0f9ba270da84b1f0d83c62634697` | +2/-0 |
| `P/PersistenceJdbcGuardProtocol.kt` | `5d2662e4d9f1adbac9bce6d423f46c0bbe096444586101aeb4585e5c38402143` | `03abd003fa21d8aa62ccc6b1faf9e5a12b6b0a16965a8ca9abb69b7b73351e7c` | +6/-1 |
| `P/PersistenceJdbcLease.kt` | `88f77802a704ba701588185290aecefbc3c2335933384cae2b8b92a27e320272` | `22cb07b46e0d3a3093cd1753598027dc30c972c5f5aec53a22a5fdc6b9a0e0d5` | +5/-2 |
| `P/PersistencePhaseContext.kt` | `def1ebd792eafe08c2bc559270a7d281e238c298f7bca03f045f10cbcec5a878` | `2ce0328657f28541b93ba6b568f477070d09d9070ffdf902e29ac42da63b6237` | +41/-7 |
| `P/PersistencePhaseOwnership.kt` | `19d2e91e3358316c2a369fc62e09a566b0e14fc15bdaefb44310cd36d8a5e500` | `b751fc526efdbee8c5c3b2fad6ec3896753270d86b28669f7a51ce63993ffdf2` | +7/-0 |
| `P/PersistenceProducerEpoch.kt` | `a6656b3d43c89281f9770815465a0a5e2543d0da5dabd7d27e9cb828af29b495` | `0bd9bec8de141db1b930dad8dea250eeda0ee5fec526c066b3fa61783e9f2c30` | +1/-0 |
| `P/PhysicalJdbcDescendants.kt` | `7dcebf2df14e22754406a09413d83a41f655c5ed189e8c82bad36615df4ed010` | `a919897ed97ffe30c0969faaace1ab878d7e4229d068945d544eaea2776ff286` | +2/-1 |
| `T/OrdinaryPersistencePhaseExecutor.kt` | `3234ea5e809f5f26432ac70d383ae96bf2633921385583230c13e6d2e1b9afa8` | `43ef1e1ab32603ac03a5d5ec64ccf04f73bd1e6776763a830292efd151576cbc` | +2/-0 |
| `Q/OrdinarySourceGrantCleanupFixture.kt` | `4cea94d0f27384bd16ae00f8ea0dad4f446e890412f6f1506b95497028a7d461` | `2ff79b0a4058cd30be1f9b298210c9d5fd28d6fc3ee2eac32e28b11c3c594ed9` | +2/-4 |
| `Q/OrdinarySourceGrantCleanupIT.kt` | `4c265dbc8e073896f395f5140be1ad96906bf89749a751d3452e144d67fdad31` | `d95a4a06510dc7b8b63d9064c643d8e8c91b783f52203d7328f4f141d24c1167` | +37/-40 |
| `Q/OrdinarySourceGrantCleanupOwnershipIT.kt` | `0a2e78581410bc91df644acee2110fd6993f0b746efd0c93ec6cda8034dbede5` | `0dd13453b6242db6f95cbcd961e6c19fde46b07db48a2b53221280cb006e0902` | +108/-55 |

**E/** = `review/working/app-29-ordinary-connected-compile-static-correction-01/`.
E is a new private packet, not a rewritten frozen source/run packet. It retains exact
12-path `before/` and `after/` copies, metadata, pre/post Git status and a passive retained
source digest inventory. `after.json` additionally contains each per-file diff SHA-256.

| E metadata | SHA-256 |
|---|---|
| `before.json` | `0011c1bd5cd1cc8ffd55818f896bda406540170003bb95724dd5bd2b51dc9c82` |
| `after.json` | `528e22069dcc33051b50f9823e4bc5982b70d38d36849b19ae1582e64ecc8fff` |
| `reported-findings.json` | `67a5467a7de06cad7cb81fde37d177f0138314f599eaab36147006b642ee7faa` |
| `retained-source-before.json` | `f71e442c2fcbaf102e50be9851fb19d1fa09051709b01d53e959ff66f09b6f3e` |

Passive byte observations: all12 preimages matched the first Linux freeze; among the
478 retained current-source paths, only these12 changed and the other466 remained
byte-identical. All six pinned failure inputs above retained their hashes. Backend
HEAD and status path inventory stayed unchanged (existing11 tracked modifications and
12 untracked paths); no earlier WIP was removed/recreated. In particular the two peer
SQL/port sources and the core's other unreported paths were left unchanged. App work,
App75's frozen packet, trackers, old source snapshots, driver/vendor artifacts, live
wiring, schemas and security/completion contracts were not edited.

## 6. Unexecuted checks and remaining concerns

Only source/document/report reads, read-only Git observations, scoped authoring and
passive copies/diffs/hashes were performed. **No Gradle, compiler, test, Ktlint, Detekt,
formatter, project checker/helper/runner, Git diff/apply check, service/container/worker,
CI, network call, Git mutation or push was launched.** No owned/foreign process was
stopped and no frozen evidence was rewritten. No subagent was spawned.

Primary must independently review the actual incremental diff, then select/refreeze and
run the configured compile/static/five-class batch. Since Linux01 executed no test class,
none of its five selected families has a new passing result to reuse. Test compilation
may expose additional previously unreachable diagnostics; manual formatting/suppression
placement also remains unvalidated by the configured tools.

The original connected15 ownership +6 peer real Spring/JPA/PostgreSQL methods remain
unexecuted in this correction. In particular actual lower failed-commit reachability,
positive exact-PID/backend-start PgSleep witness within unchanged accepted-lease-through-
disposition3000ms, durable afterCommit/interruption, and actual same-session read-cap
restoration are not established by this patch. The seven pure outcome cases and other
four selected regression families likewise have no execution credit from Linux01.

No timeout/guard/assertion was relaxed and no scope/grant selection was changed. Existing
COMMITTED/UNKNOWN retention versus local cleanup/refund remains separate. Dormant
non-bean/live-wiring restrictions, production/UNKNOWN, Boot/customizers, W05 request
expiry, operational incident sink, native/opaque/liveness/full-P3/W03 and new-data recovery
gates remain open. PG1 and W06 exclusions remain unchanged. No package acceptance,
integration, deployment, Store/main merge or issue closure is implied.
