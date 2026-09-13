# CoreC2 diagnostics01 — Backend03 bounded product lifecycle correction plan

2026-09-12. Plan only, for primary architecture disposition and Backend05 independent review. Read independent contract disposition **c556d1a9** and retain accepted **416c0723**. No product/test/harness edit, build, candidate/helper execution, diagnostic process, service, CI/network or Git action. This document is the only addition. Existing run34678157417 remains **0 PASS / 2 FAIL**; nothing below is execution evidence or qualification.

## 1. Proposed decision

**Keep business failed, but do not make an accounted RETURN incident itself a hard ThreadFactory seal.** Preserve the existing authenticated creator population and C64 custody until the actual final cut. Keep hard sealing for factory/profile/actor/frame-integrity failures. Never reopen an already sealed factory.

This is a lifecycle-policy correction, not a PENDING fixture exemption. Both existing tests keep UNKNOWN, retirement, exact Entry/epoch/single-return and managed native teardown assertions. Do not widen/reset either original budget, move observation ahead of expiry, prewarm an executor, retry Hikari close or start another cleanup/observer actor.

The smallest defensible implementation is **three lifecycle/lease files plus the existing two-method retirement/eviction boundary**: `PoolActorCustody.kt`, `PoolLifecycle.kt`, `PersistenceJdbcLease.kt`, `PersistenceOwnership.kt`, `GuardedDataSource.kt`. The extra boundary is necessary to distinguish the repeated overriding sample from an opaque eviction/submit failure caught by the same existing catch. A blind two-line replacement of `failBeforeEnd` is not this plan. No native/ABI, ThreadFactory interface, stock executor, physical registry, producer/transfer rule or public API change is proposed.

The controlling agreement is real-pool implementation agreement §2:32–68 and §4:119–138: sticky business refusal and finite actual custody are separate from the late authentic creation rights needed by the one pool close. W03/P3:373–379,576–579,642–648 still distinguishes unresolved containment from actual reclamation. Approved CoreC2 review:113–134 and the two accepted dispositions preserve these particular stronger test obligations.

## 2. Separate the five authorities — do not invent a cleanup-task classifier

| Authority/state | Proposed meaning and unchanged boundary |
|---|---|
| Business admission | Sticky `BOOKKEEPING_FAILED` plus `businessSealed=true`. `businessReady`, new acquisition entry, new future-entitlement issuance and final transfer admission remain denied. No fault clearing, recovery generation or successful new lease follows. |
| Preissued RETURN/EVICTION entitlement | Existing exact original-caller one-use cleanup ingress remains available. Entry consumes its future count and retains the actual outer Operation, including caller-runs and finalizers. Incident recording neither consumes another right nor ends/revokes the counted Operation. |
| Actor creation authority | Existing exact active pool frame **or** exact emitted Thread running its complete retained Worker; unchanged `creatorCompletionLocked` / `actualCreatorLocked`. Not an operation name, thread name, Runnable class, empty ThreadLocal or guessed executor role. |
| Entry/epoch/native authority | Existing still-current source/cleanup credentials only. Actor membership is not Entry authority. Consent revoked the old lease before recycle; a post-consent incident must not request retirement of its successor. Native/physical uncertainty remains in its existing owner. |
| Actual actor retirement and receipt | Reserve before Thread construction/publication; retain every unresolved cell; reuse only after exact TERMINATED and `!isAlive`. Final population closure, sticky failure classification and independent native observation remain separate facts. |

**“Cleanup can create” does not mean “the factory recognizes cleanup-only Runnables.”** The shared factory sees generic complete Workers. The safe in-scope model is to preserve its already approved authenticated creator closure after the narrowly recorded incidents. That includes still-active admitted acquisition/RETURN/eviction/shutdown frames, existing Workers and their replacement finally, subject to the same C64 reserve/refusal. New acquisitions cannot enter; a preexisting admitted acquisition stays counted and cannot issue a new entitlement after the seal. During shutdown, Hikari sets `POOL_SHUTDOWN` before eviction, and the managed owner separately refuses new physical requests.

This is a bound on **retained unretired generations**, not a bound of64 total lifetime creations or a universal scheduling/liveness theorem. A worker may retire and free a cell only on genuine termination. Arbitrary stalled callbacks/VM failures or an emitted NEW Thread still cannot be certified by this policy.

Important admission distinction: `PrivateJdbcDataSource:16–31` currently authenticates its caller before the independently owned native factory request; it does not atomically couple that physical reservation to `businessSealed`. Therefore do **not** claim this amendment prevents every internal physical attempt between the incident and ordinary shutdown. Existing bounded physical custody remains, and BIND/CHECKOUT/RETURN consent rechecks `businessAdmissionOpen` under G (`PersistenceOwnership:96–124`). Borrower business is denied by `PersistenceJdbcLease:39–43`; a successor's still-current physical cleanup permit need not itself be revoked. No new public business capability follows. A stronger no-new-physical-reservation cut would require a separate F/G admission amendment, not a ThreadFactory flag change.

## 3. Exhaustive `failBeforeEnd` disposition

The frozen tree has **10 external callsites**: two acquisition and eight RETURN sites; plus the private implementation and its two forwarding methods. References below are frozen source lines, not proposed line numbers.

| Callsite | Proposed disposition / reason |
|---|---|
| `GuardedDataSource:63` — failed capture | **Keep hard.** Authentic handle/capture bookkeeping is uncertain. Do not turn ambiguous acquisition custody into the new RETURN incident. |
| `GuardedDataSource:78` — obtained/end-attempted but undelivered | **Keep hard.** Attachment/wrapping/delivery/end may have failed. Preserve retained handle, entitlement revocation/handoff and failed initialization rules. |
| `PersistenceJdbcLease:116` — consented Hikari tail or retained RETURN sample failure | **Accounted RETURN incident**, through a new narrow Operation method. Exact Operation/issuer/original Thread/current ACTIVE frame and consumed entitlement must still be valid; holder/dispatch/outer counts are not changed. A consented tail is no longer source authority. Known hard actor faults already recorded by the factory/Worker stay hard. A generic tail throw supplies no new start/disposal receipt; any emitted NEW identity stays unresolved. |
| `PersistenceJdbcLease:132` — owned eviction throws | **Keep this generic catch hard.** Add a separate positive outcome for the exact overriding sample failure inside `retireLeasedState`, before Hikari eviction is called, and record only that outcome as an accounted RETURN incident. The same catch currently also covers authentication, retirement bookkeeping, Hikari removal/submission and creation/start failures; a prior `callerSamplingFailed` flag does not identify the current exception. |
| `PersistenceJdbcLease:151` — C5 restoration fails | **Keep hard in this smallest slice.** This catch includes the caller-presence check and restoration. Do not globally reclassify all callbacks to fix the two selected fixtures. Preserve one restoration and actual outer end. |
| `PersistenceJdbcLease:159` — adaptation/restoration preparation fails | **Keep hard.** It mixes ownership-lock/invariant checks, detached envelope preparation, failure adaptation and callback outcomes. `SafeJdbcFailure:76–87,138–143` can also refuse an unsupported JDBC-log-writer profile or rethrow Error. No broad soft-Throwable rule. |
| `PersistenceJdbcLease:170` — holder end throws | **Keep hard.** Retain the holder/end uncertainty; do not publish Operation end. |
| `PersistenceJdbcLease:178` — dispatch restoration throws | **Keep hard.** Retain its original lineage/count; no successor or current-owner fallback. |
| `PersistenceJdbcLease:187` — Operation end false/not actually ended | **Keep hard.** `endFrame` owns ENDING/restoration/count transitions. An invalid/ENDING frame cannot obtain a new incident grant or counterfeit ENDED. |
| `PersistenceJdbcLease:194` — holder or dispatch not ended | **Keep hard.** Keep the outer Operation counted; a caught exception or caller Thread termination cannot discharge it. |

The existing `Acquisition.failBeforeEnd`, `Operation.failBeforeEnd` and `recordBookkeepingFailure` remain hard APIs; do not change their common implementation into the soft path. All direct `actors.failLocked` sites remain hard: unsupported installation/profile (`PoolLifecycle:45,78`), close setup/flag/TL bookkeeping (:156,217), entry/refusal/end bookkeeping (:299,313,320,337,352), failed startup (:363), and actor refusal/construction/entry/body/restore/observed-failure paths (`PoolActorCustody:63,99–100,123,138,142,147,160,165,188,196,206`). The first retained fault must not prevent a **later** hard fault from sealing.

This is deliberately not a claim that every restoration callback damages custody. Keeping those mixed catches conservative avoids expanding the accepted fault policy beyond the two required incident paths. Their existing strong regressions remain required and unchanged.

## 4. Concrete source plan

### A. Monotone incident recording, not unsealing

In `PoolActorCustody`, add a separate internal operation for an **accounted caller incident** that records the existing `BOOKKEEPING_FAILED` first-failure value and seals business, but does not write `factorySealed=false` or revoke existing creation authority. Keep `failLocked` setting `factorySealed=true` unconditionally, even when firstFailure was already recorded. Thus incident→hard, hard→incident and repeated incident all preserve monotonicity. No new public enum/diagnostic meaning is needed; the fixtures retain their exact firstFailure assertion.

In `PoolLifecycle`, expose this only through a narrowly named RETURN Operation method, not a caller-supplied Boolean/exception category. Verify exact issuer/pool/current original Thread, ACTIVE top frame, RETURN kind and this Operation's consumed preissued entitlement/count under the existing gate. Reject foreign, fabricated, ended or unresolved-ENDing callers; no incident method repairs failed accounting. Perform no overridable sample, Hikari/native call, wait or epoch mutation in this gate. For an otherwise authentic current ACTIVE RETURN, a violated count/entitlement invariant remains a hard bookkeeping failure without releasing the count; actual ENDING/restoration failures remain owned by the existing hard end path. Do not grant a forged/foreign ticket authority to fail another pool.

Crucially, recording the incident does **not** call `requestShutdown`, native-owner shutdown, Hikari close or `requestRetirement` on a guessed current Entry. Such an early native shutdown could retire the successor before the old-tail test's nonretirement assertions; supplying the RETURN1s budget there would also change which shutdown budget wins. Leave ordinary shutdown initiation exactly where it is today.

### B. Identify the repeated C5 sample without changing its protocol

Use one small closed internal result along the existing chain `PersistenceOwnership.retireLeasedState` → `PersistenceJdbcLease.claimEviction` → `GuardedDataSource.evictOwned`: **REFUSED / CLAIMED / CALLER_SAMPLE_FAILED(original Throwable)**. The result describes the retirement claim/callback outcome, **not** Hikari execution, lower close, actor termination or native disposal.

Only the exact `caller.sampleOutsideLocks()` invocation in `retireLeasedState:147` can produce CALLER_SAMPLE_FAILED. Catch that invocation locally, while the genuine outer RETURN remains retained and no G lock is held. Preserve its original Throwable for the existing outer adaptation; do not adapt, interrupt, retry or sample again here. Preserve the precise original loop/check order, original caller and budget, actual-flag primitives, tryLock/recheck and retirement mutations. Any failure preparing the result or in the other invariant/lock/bookkeeping steps continues to throw to the hard catch.

`claimEviction` keeps exact pool/handle/original Thread/RETURNING/source/one-CAS checks and refusal after consent. `evictOwned` obtains that result itself: only CLAIMED permits its one existing `pool.evictConnection(handle)` call; a sample-failure result is returned **without entering Hikari**. Hikari/submit exceptions still propagate to :132's unchanged hard catch. Do not accept a caller-supplied CLAIMED token or expose the raw handle. Its existing stale-tail test caller still gets refusal and no Hikari action.

`PersistenceJdbcLease.close` records the positive sample-failure outcome through the new incident method, preserves the existing first-failure precedence, and then runs the same nested holder/dispatch/Operation finalizers. At :116 use the same incident method for the existing sample/consented-tail predicate. Do not use that sticky predicate to soften later unrelated failures. This removes the second seal in RETURN_SAMPLE without changing its sample count, no-consent source retirement or single-return path.

### C. Fix UNKNOWN-before-final-seal, not budget-before-observation

Backend05's hazard is real: `PoolActorCustody.observationLocked:83` returns UNKNOWN before :84 seals the factory. Once incidents no longer seal early, this ordering is insufficient.

Keep the checks in this order under the **same existing gate**:

1. Nonzero construction, unclosed synchronous/future-entitlement population or unresolved live creator → PENDING.
2. Published NEW/unproved start disposition → UNPROVEN, retaining its exact cell; no retirement or successful final-cut fiction.
3. Only the actual empty, fully closed actor population may set `factorySealed=true` irreversibly.
4. Then classify its sticky failure as UNKNOWN, otherwise ENDED.

Do not move `PoolLifecycle.observeEndedPool:427` behind this work: the original shutdown budget check still occurs before actor reaping/classification. Continue actual termination observations outside F/G/T, exact-generation rechecks under the gate, and the independently budgeted-with-the-same-budget managed-owner observation at :432. No unconditional UNKNOWN shortcut. UNKNOWN in other failure branches is not automatically an all-actors/native-disposed theorem.

## 5. Why this addresses the actual cold-closer obstruction

Exact Hikari6.3.3 source in the retained source JAR:

1. `GuardedDataSource:22–36` retains the inert stock pool and installs the sole factory. `HikariPool:110–114` creates adder and closer executors using it. `UtilityElf:150–172` supplies a bounded queue, core=max1,5s core timeout and **no prestart**; the closer uses CallerRunsPolicy.
2. `HikariDataSource.close:340–356` consumes its one-shot flag and calls `HikariPool.shutdown`. That shutdown sets POOL_SHUTDOWN (:204), soft-evicts (:217), stops/awaits the adder, destroys housekeeping, closes the bag, creates/uses/stops the late assassin (:228–241), then stops network/closer executors (:244–248). A10s closer await warning still returns; it is not termination evidence.
3. Idle eviction reaches `softEvictConnection:626–631` → `closeConnection:457–466`: remove the bag entry and capture its lower connection **before** submitting the lower-close Runnable. The actual new Thread wraps the executor Worker, not that Runnable. The authenticated creator is the existing RETURN/eviction or SHUTDOWN frame, depending on when this route runs.
4. With current hard sealing, `reserveLocked:141–143` returns null. Retained JDK21 reference `ThreadPoolExecutor:1362–1376` permits initial addWorker failure, successful enqueue, then failed zero-worker replacement without CallerRunsPolicy; :715–721 prevents orderly termination with a nonempty queue. This matches the observed queue1/pool0/completed0 warning sequence. It remains a source mechanism, not an exact-runtime per-event trace; the JDK reference is21.0.11, not executed Temurin21.0.12.1.
5. RETURN_SAMPLE sets the failure at :116 and repeats the overriding sample in `retireLeasedState`, currently reaching :132. Its diagnostic pre-shutdown queue was0. The narrow new result prevents that callback from re-hard-sealing, so the original SHUTDOWN frame can reserve a real cold closer cell. The physical Entry's existing retirement is not undone.
6. FAILED_POST_CONSENT_TAIL fails at :116 after consent. The successor is still current and unretired by that tail. Its **own** later failed close consumes its own RETURN right and can legitimately enqueue eviction before shutdown; its diagnostic pre-shutdown queue was already1. Therefore a SHUTDOWN-only exception, opening the factory only at close, or retrying the same shutdown is insufficient. Existing authenticated RETURN creation rights must survive the incident too.

After the narrow correction, a valid cold worker can be reserved/published/entered under the original creator, drain the actual task and actually terminate. The product can then reap it, close the population, preserve BOOKKEEPING_FAILED/UNKNOWN and observe native cleanup **within the unchanged original allowance**. This is a proposed removal of the starvation cause, not a promise that arbitrary failures or scheduling always fit the budget. Only the future unchanged real tests can verify sufficiency.

## 6. Safety proof obligations and focused regressions

**Population proof.** Reservation/construction/publication and final sealing share one gate. A reserved construction, published NEW, entered Worker or active original frame prevents the final cut. An actual Worker remains a creator throughout the complete supplied Runnable and replacement finally. After genuine TERMINATED/!isAlive retirement, empty cells plus zero acquisitions/operations/future rights and the ended one-shot close exclude every future authentic creator. Prepared but unentered business tickets cannot cross the business seal; consumed/revoked entitlements cannot enter again. Neither failure classification nor observer timeout changes these facts.

**Epoch proof.** Leave `PersistenceOwnership:127–165,221–231`, `PersistenceJdbcLease:213–217`, and `PhysicalJdbcFacade:166–187` semantics intact: exact unconsented source retirement/current-owner cleanup, refusal of consented old eviction, and no upgrading a present stale dispatch credential through pool membership. The narrow retirement result reports the existing attempt; it does not grant a new attempt, source, budget or successor permit.

Add only focused cases to the **existing** `PoolLifecycleTest`, `PoolActorCustodyTest` and `PersistencePgOwnedCutIntegrationTest`; no separate process-only runner, observer service or opaque orchestration layer. Proposed cases, not executed tests:

| Regression | Required discriminator |
|---|---|
| Accounted incident versus hard fault | In an authentic preissued RETURN, firstFailure=BOOKKEEPING_FAILED and business closed immediately, but the incident alone leaves an open factory open and counts/entitlement/frame unchanged. Foreign/wrong-pool/fabricated/ended calls acquire no authority. Explicitly MODEL cases are not native completion proof. |
| Exact repeated sample versus unrelated eviction failure | A sample failure at the retirement loop is returned before any Hikari call, preserves the original exception/budget/caller and single ingress. An earlier samplingFailed flag must **not** soften a later different Hikari/submit/bookkeeping throw. No extra sample or restoration. |
| Cold actual RETURN and shutdown creation | Keep both original fault fixtures and all body/teardown assertions; do not prewarm. Require the positive post-incident cold-creation/actual-retirement path, not just a snapshot showing an open factory. Existing scalar diagnostics may help describe it but cannot replace end evidence. |
| Hard fault dominance in both orders | Incident then genuine null/unauthenticated/capacity/construction/Worker failure, and hard failure then incident: factory stays sealed, business stays failed, original firstFailure is retained. No generation escapes C64. Existing64-NEW/refused65 and96-actual-retire cases remain. |
| Complete Worker and unresolved tails | Existing stock replacement-finally/caller-runs cases remain; a held holder/dispatch/Operation, active creator, constructing ticket or published NEW cannot be reclassified as ended by the incident. No test cleanup starts NEW merely to obtain a receipt. |
| Final UNKNOWN ordering | In a narrowly labelled MODEL case with no earlier hard seal, factorySealed must become true at the actual empty final cut **before** UNKNOWN is returned; repeat observation stays UNKNOWN/sealed. Add the same final-state discriminator to the real incident path without relaxing its actual end requirements. |
| Budget and native/epoch co-gates | Existing `PoolLifecycleTest:219–238` expired-original-budget/duplicate-request PENDING remains; all1s RETURN and10s shutdown identities remain. Keep exact Entry absence, fresh same-Entry/PID Root, old-tail nonretirement, duplicate close/abort denial, no second restoration, actual caller end, retiredGenerations>0 and `PgLifecycleTestScope:53–64` actual owned-thread teardown. |

The existing fixture's retiredGenerations>0 is positive retirement evidence, not by itself an all-generations theorem. Any added final-empty assertion is additional evidence, not a replacement for native teardown. A two-test pass, if later obtained, still would not qualify the full47/native/W03 gates.

## 7. Primary decision and stopping conditions

Primary must explicitly accept **survival of existing authenticated creator rights after these accounted RETURN incidents**, not a fictitious cleanup-only task privilege. Backend05 should check the closed sample-result boundary, all unchanged hard paths, the final seal ordering and the authority table before implementation authorization.

If the required policy instead forbids *all* non-cleanup stock work after any incident, the current shared factory cannot prove it: it has neither a task-role credential nor control of each executor's submission/start cut. Satisfying that stronger requirement needs separately approved authenticated executor/task provenance or a different lifecycle seam; names, reflection, prewarming or a caller-supplied cleanup flag are not substitutes. Likewise, proving an abandoned NEW Thread inert needs a genuine start-disposition extension, not this plan. Do not silently widen the approved stock-factory model to claim either property.

If the narrow classification cannot be implemented without weakening hard custody handling or changing the original protocol, stop for that specific architecture decision. Do **not** replace either test with process-owned PENDING teardown. No implementation, runtime adequacy, cleanup repair or acceptance is established here. Original diagnostics/cleanup failures and historical qualification limits remain unchanged.

## Reviewed bindings

R=`review/remediation/`; W=`review/working/`; F=`W/app-29-w03-integrated-driver-core-c2-diagnostics-01/`. P/T=`F/sources/src/{main,test}/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`. B=`kira-backend/src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/` for manifest-bound baseline files not copied into F. Static verification matched all28 cited path hashes, all18 cited source/test manifest bindings and all12 current/frozen P comparisons. Prior causal report e299603c and original raw XML remain unchanged. The Hikari line references are read directly from the pinned source JAR, without running Java. No full source-inventory/runtime requalification is claimed.

| Path | SHA-256 |
|---|---|
| R/app-29-core-c2-diagnostics01-independent-contract-disposition.md | c556d1a9678b6a1b745c8c4af8d2f399d05d368b336cab5db351dd08656f8270 |
| R/app-29-core-c2-diagnostics01-backend03-contract-addendum.md | 416c07232afd55d67adb4fe3e58aee9062e2c08f7f54e6a19673f2e7259b042c |
| R/app-29-real-pool-lease-implementation-agreement.md | f9046e74cd2a38b0a16ee55de1058c6bcc95dbd14f34e965e0b22ae510302138 |
| R/app-29-real-pool-actors-independent-review.md | 0c16b70b893e05c73e81ab1794001844de5ea465e8beae8d1f75e8ae61a636c1 |
| R/app-29-real-pool-return-adaptation-c2-01-independent-review.md | 08bf7d11e4108f2704db1ea5778934b0c2027240e6e5fad0482ab79ea2982f35 |
| R/app-29-w03-plan-p3-frozen.md | eb51e11c308d6269f616fa07a249b240477dde4afcfee8b3f050766fc68305ca |
| R/app-29-w03-integrated-driver-completion-plan-v1.md | 48bbd5582ca369e0bb0aa5d7d6970d40e9634267a8a0439209e095ab912daf92 |
| F/manifest.json | 2e6ba4a28bdc628d42937c3ed0f7f435c835b61d4e6f73702b50e6a2edd85511 |
| P/PoolActorCustody.kt | 0e45d75ee8a2421b6db238ced31298b7a5012db4ad3232e8675ae0f889e8c857 |
| P/PoolLifecycle.kt | def7c6ef36145b6d1dcf71342a5e6c1956f6f40055464e231e946eff05ade9f2 |
| P/PoolLifecycleFrames.kt | 2cbd7a055d12000953c37301a7d08839df739d391b4fafa453e8acb62944963e |
| P/PersistenceJdbcLease.kt | dd73ba8b486e285ac76c16e56d98bdac475027c86fed9eb5ffe3f7c1a5a820fd |
| P/GuardedDataSource.kt | a6730fbc65d378713dd89bd0794b5514a764320f1186c681c4b44efabd1d09c7 |
| P/PrivateJdbcDataSource.kt | 57d702ce9988b0bdd650387dd604d47edd0a4d3640f4f0071f6ad6311467a691 |
| P/PersistenceOwnership.kt | 5bee8dc7f22219542a6ff28df8230e401268884c4711289afebf397c39d2d334 |
| P/PersistenceJdbcPoolTransfer.kt | 04ff9655211046f13af24395eb9bb489c3375702fc3dd057f225792da11e3b49 |
| P/PhysicalJdbcFacade.kt | a58c7aedd83c96dc572f94351fe77387922c949a066ca5a49f80744b569b6c74 |
| P/PreparedPoolConnection.kt | 1f184fdd95401e528b4fc9900fc532448f8ceae7d07bd77b1b824b2cf47a9a79 |
| P/PersistenceJdbcGuardProtocol.kt | c3c2095193dac21bae09219e75a50b79b2da6ed5512db4ad0168da88676b30c0 |
| P/PersistenceJdbcParticipant.kt | 2769b92239a1d444b34ae1bef2223104669f7561c1436822d6a56fba4884630b |
| B/PersistenceOwnedFactoryCaller.kt | b43a7c3251c9f84762a1befb65b5e531fe0052598b5f1a894eae53474dd9f28b |
| B/SafeJdbcFailure.kt | 03b502ed83f9b323f7278273eb8b2dcb6fb22b8003f52310470170cd24cb63a0 |
| T/PoolActorCustodyTest.kt | 7ddc9fac7597febfb42de44c041e4c2ccfdc01bc864e973346738a5ffd0209fa |
| T/PoolLifecycleTest.kt | f5f194f46eddb89b32ba1142fcbedd5617255abae5b3ffe0bd507b26449c0665 |
| T/PersistencePgOwnedCutIntegrationTest.kt | 09ff840b9b3c4532c33ce24c09a60a2b0479084b480ed29f6d21478751e78f99 |
| T/PgLifecycleTestScope.kt | 7574167d18008256a43ff056e5797d5882abe1defc4ffcdda46e72a02a0ae9ec |
| W/app-29-w03-driver-bootstrap-advisory/hikari-6.3.3-sources.jar | 65a247c9ddb809885696ad2dbb1e77e923debc82c94972ca4c48f40a83c0e0a5 |
| W/app-29-w03-factory-ownership-advisory/sources/jdk21-ThreadPoolExecutor.java | c95cd4ef67c936350fb6b85db3f7858a1185ddeac62bf00f4236efe6b5fd2427 |
