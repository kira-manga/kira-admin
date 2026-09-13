# App29 — lease-dispatch creator independent actual-diff review 01

2026-09-13. **PRIVATE. Source-only; one blocking test-compilation finding.**

## Decision and scope

**HOLD the current 17-path candidate for F1 below.** Apart from that visibility defect, I found no additional blocking production/concurrency defect in the reviewed correction. The non-consuming creator and exact-epoch outer-tail integration are source-consistent with the primary agreement. This is not a compilation result, execution admission, candidate freeze, runtime acceptance or W03 completion.

Repository: `/root/projects/Kira/kira-backend`; HEAD `ccdbb28f6362117882501b4da040257be6fc1990`; branch `remediation/app-29-backend-complaints`. The actual worktree delta is 14 tracked modifications plus 3 new paths: 12 production and 5 test files. All 17 current hashes independently match the author handoff below, and the same HEAD/path set remained at final passive inspection.

I read every tracked hunk, all three new files, surrounding admission/finalization/proof boundaries, backend AGENTS.md and relevant normative PLAN sections. I did not author this implementation or its tests. **Reviewer builds, compilers, tests, checkers, JVM executions and acquisitions: NONE.** No product/test/tooling/Git/CI/tracker changes, service/network work, runner/helper execution/imports or process/lease-control actions were performed. Only this new mode-0600 report was written.

## F1 — blocking: public parameterized test exposes an internal enum

- Location: `T/PoolLeaseDispatchCreatorIntegrationTest.kt:39,602–612`; enum declaration `T/PgLifecycleDatabaseRecipe.kt:29`.
- The class is public by default, as is the parameterized method at line 612, but its parameter type `PgLifecycleDatabaseMode` is internal. This is Kotlin's `EXPOSED_PARAMETER_TYPE` visibility error; selecting only another test does not bypass compilation of this test source. There is no file/declaration suppression or relevant compiler opt-out in the inspected source/build configuration.
- Minimal correction: change line 39 to **`internal class PoolLeaseDispatchCreatorIntegrationTest`**, matching the existing database parameterized-test classes. Do not widen the enum or suppress the diagnostic. This preserves the named class/method/enum-row scope.
- This finding follows from the source/type rules, not a compiler invocation. Primary acknowledged it and requested preserving the reviewed pins until this report; neither reviewer nor author applied the correction during review. Rehash the changed test file and validate compilation/discovery in a separately admitted step.

## Production boundary review

1. **Exact acquisition association and non-consuming rights.** `M/PersistenceJdbcLease.kt:28–40` binds once before exposure; `M/PoolLifecycle.kt:435–459,700–708` checks exact lifecycle, captured handle, lease, prepared epoch/context and authentic active acquisition entitlement. Creator admission additionally requires the genuine top admitted guard, exact upper identity/kind/dispatch issuance and actual caller (`M/PersistenceJdbcGuardCall.kt:90–99`; `M/PersistenceJdbcLease.kt:368–406`). Creator entry increments only `operations`; it does not reserve terminal `prepared`, decrement `futureEntries`, consume or revoke RETURN/EVICTION (`M/PoolLifecycle.kt:477–487`). Guard budgets are carried by identity, including null/unbudgeted calls. Multiple internally prepared candidates can exist before admission, but guard/dispatch retention allows only one admitted creator per actual invocation; this is not a stronger single-preparation guarantee.

2. **AVAILABLE admission is separate from already-active tail custody.** The entitlement's AVAILABLE check can refuse creator setup, including a prepared candidate revoked before entry. Once admitted, recognition/end do not re-run business readiness, availability, lease OPEN state, epoch retirement or elapsed budget. Thus a legitimate failure tail remains a creator without reopening JDBC/native admission. Original-caller BUSINESS and terminal entitlement authentication remain unchanged; permitted foreign cancellation uses its own genuine admitted guard/caller, not the terminal entitlement's original-caller authority.

3. **Guard cleanup precedes fallible setup; missing-tail custody is retained.** `M/LeaseJdbcFacade.kt:98–140` and `M/PhysicalJdbcDescendants.kt:492–580` establish the guard finally before `invocation.enter`. The outer holder retains its prepared ticket before enter; the call/dispatch retain it before tail allocation/registration; the call retains the tail before counted registration and pool-TL publication (`M/PersistenceJdbcLeaseInvocation.kt:11–15`; `M/PoolLifecycle.kt:462–504`; `M/PersistenceProducerEpoch.kt:174–193`). If preparation fails after the guard retained the creator but before the ticket receives `tail`, `M/PersistenceJdbcGuardCall.kt:126–130` prevents dropping the producer. PREPARED/REGISTERING tails also prevent core finish via `tailRegistrationSettled`. Failed setup, restoration or end marks sticky bookkeeping failure and seals/retires only the exact epoch without releasing counts (`M/PoolLifecycle.kt:542–550`; `M/PersistenceJdbcGuardProtocol.kt:405–415`). A genuinely unadmitted refusal may settle; a retained failed setup is not relabeled as such.

4. **The actual outer adapters are enclosed.** Connection `invoke` and descendant `invokeClosed`, not merely inner dispatch restoration, own the holder (`M/LeaseJdbcFacade.kt:43–63`; `M/PhysicalJdbcDescendants.kt:456–471`). Coverage includes Hikari exception/inline work, output guarding, inner failure conversion, dispatch restoration, driver/core finalizers, `afterJdbcCall` and the outer SQLClientInfo/declared-failure converters reached from a failing finally. `finishReturned` distinguishes an actual return from all guard finalizers from a mere producer end claim (`M/PersistenceJdbcGuardCall.kt:71–87,102–103`). Ticket-end failure is marked before fallback exception allocation/adaptation and remains retained; a successful end returns directly without another adapter (`M/PersistenceJdbcLeaseInvocation.kt:24–38`).

5. **Exact-epoch completion is load-bearing, not just a pool counter.** Registration shares the existing epoch state CAS with producer/seal accounting and occurs while the authentic producer cannot yet finish. `sealedAndEnded` includes `outerTails == 0` (`M/PersistenceProducerEpoch.kt:79,181–236`); exact lease quiescence separately requires its own epoch's tails ended (`M/PersistenceLeaseCompletion.kt:85–92`). The unchanged ownership/physical-completion/transfer readers therefore cannot consent, prove native drain or reclaim around a held tail. No ownership-lock-to-pool callback, profile query, new registry or historical ticket scan was introduced. On successful creator end, pool-TL restoration and validation precede the final epoch cut; only prevalidated scalar pool/completion/frame publications follow (`M/PoolLifecycle.kt:507–538`; `M/PersistenceProducerEpoch.kt:196–207`). Failure before that cut retains the obligation.

6. **One coherent lineage; no lower-authority widening.** New creators use the same `PoolCallFrames` chain as acquisition/RETURN/EVICTION/shutdown. Creation uses only the top authentic active frame, without wrong/stale/unadmitted-top fallback to an outer ticket or Worker (`M/PoolLifecycle.kt:255–259`). `isAuthenticPoolCaller` explicitly excludes creator-only frames and also refuses top-frame fallback (`:85–99`); unchanged `M/PhysicalJdbcFacade.kt:251–257` still rejects a present stale dispatch and cannot select a leased epoch via absent-dispatch pool fallback. `M/PrivateJdbcDataSource.kt:16–29` remains separately authenticated. Pool close/observation see the common lineage after core TL restoration, and RETURN's self-wait check walks only the current caller's lineage outside ownership locks (`M/PersistenceJdbcPoolTransfer.kt:68–77`; `M/PoolLifecycleFrames.kt:111–118`). `PoolActorCustody` is unchanged: hard seals/capacity still dominate; generations retain scalar creator completion, not a lease graph; full Worker/replacement termination remains required.

## Test source review — exactly 17 intended invocations, all UNEXECUTED

All selectors below are in `me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest`. They are source identities, not JUnit observations or a claim that a CLI filter selects an individual enum row.

| # | Method / row | Source line |
|---|---|---|
| 1 | `MODEL fatal connection commit creates the first real Hikari close Worker and drains its task` | 51 |
| 2 | `MODEL fatal Hikari statement execution creates the first real close Worker and drains its task` | 54 |
| 3 | `repeated nested admitted dispatches retain one future RETURN and no lower native fallback` | 191 |
| 4 | `only exact admitted guard dispatch lease epoch and issuer can enter a creator` | 269 |
| 5 | `mixed pool creator nesting refuses wrong top fallback and unrelated lease use` | 316 |
| 6 | `present returned dispatch cannot upgrade through pool authority and a revoked lease cannot enter a prepared creator` | 349 |
| 7 | `foreign actual statement cancellation keeps only its own outer tail while original RETURN waits for it` | 403 |
| 8 | `real post core outer tail refuses reentrant self wait and remains in exact terminal and loan proofs` | 474 |
| 9 | `MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement` | 519 |

Rows 10–17 use the parameterized method `actual creator publication restoration and outer adapter faults retain exact obligations through process only exit` at line 612, with exactly these `PgLifecycleDatabaseMode` values (lines 605–609):

10. `POOL_LEASE_CREATOR_ENTRY_BEFORE_TL`
11. `POOL_LEASE_CREATOR_ENTRY_AFTER_TL`
12. `POOL_LEASE_CREATOR_END_BEFORE_TL`
13. `POOL_LEASE_CREATOR_END_AFTER_TL`
14. `POOL_LEASE_CREATOR_CORE_BEFORE_TL`
15. `POOL_LEASE_CREATOR_CORE_AFTER_TL`
16. `POOL_LEASE_CREATOR_CLIENT_INFO_TAIL`
17. `POOL_LEASE_CREATOR_DECLARED_TAIL`

The two fatal-route cases inspect the exact stock-Hikari close executor's initial zero pool/largest/active counts, empty queue and zero completed tasks before injection. They then hold its actual close task on a distinct authenticated Worker and require the specific task's drain (`T/PoolLeaseDispatchCreatorIntegrationTest.kt:56–187`). The executor/factory are not replaced. The interposed fatal delegate and close observation make these **MODEL failure routes**, not real native PG commit evidence; global retired-generation count alone is not their route oracle.

The remaining non-process cases exercise actual RETURN consent/single consumption, post-core lower denial, exact/wrong identity, duplicate entry/end, mixed pools, foreign statement cancellation, a reentrant RETURN that refuses without exhausting its original one-second budget, exact loan/native proof, and caller-bound MODEL budget expiry inside actual `afterJdbcCall`. The direct factory call in the budget-expiry case is a rights test, not represented as the real first-close-worker regression.

The eight additive process rows use the existing negative-lane protocol. Child evidence is asserted on the exact dead caller/retained invocation and checked again across RETAINED/EXIT; exit 23 is only `PROCESS_ONLY product_end=false`. Existing positive `awaitVerified` still rejects it; the original parent deadlines and product-end rejection oracle are unchanged (`T/PgLifecycleDatabaseProbe.kt:46–62`; `T/PgLifecycleDatabaseProbeProcess.kt:62–157`). Only the already selected Hikari artifact is added by the existing closed pool-case classpath rule.

## Meaningful gaps and source-only limits

- The final **retained creator with `tail == null` before registration** correction has no separately injected case among these 17. Its safety was traced in source through the retained producer and sticky exact-epoch failure. Do not count the entry-before-pool-TL cases as that regression: they already require one registered tail (`T/OwnedPoolLeaseCreatorPendingProbe.kt:245–256`).
- The SQLClientInfo lifetime hold is explicitly a **per-instance MODEL substitution** of private `SafeJdbcFailure.postgresExceptionClass`, not production trust for overridden PG getters. The helper restores that exact field in finally and releases/joins the held caller (`T/OwnedPoolLeaseCreatorPendingProbe.kt:208–235,302–320,383–412,67–85`). Unchanged production preparation rejects overridden PG scalar getters (`M/SafeJdbcFailure.kt:119–129`).
- The declared-stream case holds its prerequisite failing finally **after the actual core TL write**, then checks outer IOException conversion; it does not suspend inside that converter. Both adapter-failure modes retain an unfinished core producer, so their negative native proof alone would not isolate the additional epoch-tail term. The separate post-core barrier and `afterJdbcCall` cases do isolate a tail after ordinary producer completion.
- The mixed-pool case covers creator-over-creator top precedence, not every stale/unadmitted-creator-over-Worker permutation. Those refusal branches and unchanged Worker replacement/CallerRuns mechanisms were inspected in source; the existing controls remain unexecuted in this review.
- Compilation (including F1 correction), JUnit discovery, reflective instance-final-field behavior, timing/one-second cancellation overlap, subprocess closure and all actual result oracles remain unverified. No amount of source concurrence supplies runtime qualification.

## Preserved acceptance and evidence

`T/OrdinarySourceGrantCleanupOwnershipIT.kt:511–550` remains unchanged, including the real native-commit witness, UNKNOWN outcome, genuine local quiescence/refund and database/session assertions. `T/PersistencePgOwnedCutIntegrationTest.kt:1403–1435` retains its original owned-pool teardown expectations/budgets. The original two pending-pool cases, lower native dispatcher, actor custody and SafeJdbcFailure production allowlist are unchanged.

**PG01 remains 20 PASS / 1 FAIL.** The missing implicit-eviction creator route is a source defect; its correction is not a diagnosis of PG01's unmeasured actor/queue state. Later real-PG acceptance is the single existing failed method, unchanged, under separate primary admission. Preserve historical 348-path seed evidence and the frozen 478-source manifest; any corrected candidate must be new, not an evidence rewrite. This review rehashed the specified manifest/result and protected source anchors, not every historical seed body.

No public push of this ancestry; W06 remains excluded. New-backend-data and installation recovery remain required. No W03/package completion credit.

## Binding report/evidence pins

Paths here are relative to `/root/projects/Kira/`; SHA-256 values were passively rechecked.

| Path | SHA-256 |
|---|---|
| `review/remediation/app-29-lease-dispatch-creator-primary-agreement-01.md` | `e082e0f991b3d472c173ebd83182dcf50ea3df87bc793de5f5507428cc3b28f7` |
| `review/remediation/app-29-lease-dispatch-creator-author-handoff-01.md` | `ddc881e76efbb0c9e9a8fba6b2e0fcfcfef684f4cfd3d32c1e8f04677cc8e376` |
| `review/remediation/app-29-ordinary-implicit-eviction-source-investigation-01.md` | `ec9ed982cbe8325444b842e4c32cadea781ef8c65d4c770a12ee18a2c82bdc18` |
| `review/remediation/app-29-lease-dispatch-creator-concurrency-review-01.md` | `6ee1c1726b93b49775f33387835b79c45e04fa91da514e48bda9447b97bc83ec` |
| `review/working/app-29-w03-integrated-driver-ordinary-connected-pg-01/manifest.json` | `7c5e775dc0250948ead0ba20aff89cb38e2565fdbb82751575291fa96a80d63c` |
| `review/working/app-29-ordinary-connected-pg-admission-01/launch-01/artifacts/test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.OrdinarySourceGrantCleanupOwnershipIT.xml` | `de0a3b68933690ca5309411057b164575c4b2b51f759c8da32a9e425b2177835` |

## Exact changed/reviewed path pins

Paths below are relative to `kira-backend/`. `M/` expands to `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`; `T/` expands to the same package under `src/test/kotlin/`. These identify the reviewed bytes **before F1's recommended correction**, not a freeze or test result.

| Path | State | SHA-256 |
|---|---|---|
| `M/GuardedDataSource.kt` | modified | `7395aa04bfbb6702043dddf1a6393cf94b2abd67128bf669ee81ff39df2ca448` |
| `M/LeaseJdbcFacade.kt` | modified | `28e63d187150a4768661ee7fb257cf4d5e29d99b7a0e642619abfb2661705afd` |
| `M/PersistenceJdbcGuardCall.kt` | modified | `bcc7385e7ba6f2fcb08a21804357cc00901297fba14c603f10e8588fdd309a70` |
| `M/PersistenceJdbcGuardProtocol.kt` | modified | `f0209738f66ed56298799a1b58d1f8e67e518d8a5d3f5bc591f944224cd43063` |
| `M/PersistenceJdbcLease.kt` | modified | `52adf32aef2bb2651cfedabd076785a585a6ac3549d1d0fcf160c11022affc1f` |
| `M/PersistenceJdbcLeaseInvocation.kt` | new | `d4a41dc996bc34604b380a073606e4ddf699bb27d9c30036f414c2c0f6e67c28` |
| `M/PersistenceJdbcPoolTransfer.kt` | modified | `d77f0b6c32d970e6bc121dd3c87d5b81fbf2cc43632fe02bc8160833155ca8bf` |
| `M/PersistenceLeaseCompletion.kt` | modified | `72b28bb29e2eb3e173aa129691f7217ce7fd431bbed4bfdce66ebe506e6d7955` |
| `M/PersistenceProducerEpoch.kt` | modified | `ceba65cea2616a82f0e6614bfda229ecf7221e77c5209ff6bbaf33ea1c270cba` |
| `M/PhysicalJdbcDescendants.kt` | modified | `70aa9d92b96ad0595b321ed30dcc05cd73cc370c921fd05dfc87f370a1868220` |
| `M/PoolLifecycle.kt` | modified | `1a4f606b75dea09e2f3d6897fe9170007ed9bae5449c609e12961ea6e28a2564` |
| `M/PoolLifecycleFrames.kt` | modified | `8dff17640c0c242c8243364d0bd6490dadc61c0eda46c637405e8431eda90367` |
| `T/PgLifecycleDatabaseProbe.kt` | modified | `de5190a19261b63a009b830912896297ea291c1fa6d155e723fc3c59760b0859` |
| `T/PgLifecycleDatabaseProbeProcess.kt` | modified | `f8dd59a17d0334a5d8cc9c9b577b26e5ecead537a7f30180c975d0a25b88264a` |
| `T/PgLifecycleDatabaseRecipe.kt` | modified | `e405d48f71463bd8512a9433311509e92b387807f1b4c6682843dc9708ac128e` |
| `T/OwnedPoolLeaseCreatorPendingProbe.kt` | new | `e2e62c2fd4fd36d54f9c6a900c277a2c961e3238384bfd1220d83daa38fd333f` |
| `T/PoolLeaseDispatchCreatorIntegrationTest.kt` | new | `da4ead51ebdded37bc6b97e88b2c1d9f43ec6b28d36da25775ca74db601d7e9b` |

### Supporting source/context pins

Selected proof/authority/control boundaries were read; this table is not a claim of a new whole-file audit of every supporting file. These files are unchanged by the 17-path delta.

| Path | SHA-256 |
|---|---|
| `M/PhysicalJdbcFacade.kt` | `740572baed8baea8dd998b69ec3aa115a19862eee610b108e00f97d6820c3b19` |
| `M/PoolActorCustody.kt` | `c658703d6fe07c23fd67bd2db98c568cc589bc096d3dda89ea2dcdcec597a503` |
| `M/SafeJdbcFailure.kt` | `03b502ed83f9b323f7278273eb8b2dcb6fb22b8003f52310470170cd24cb63a0` |
| `M/PersistencePhaseContext.kt` | `2ce0328657f28541b93ba6b568f477070d09d9070ffdf902e29ac42da63b6237` |
| `M/PersistencePhaseOwnership.kt` | `b751fc526efdbee8c5c3b2fad6ec3896753270d86b28669f7a51ce63993ffdf2` |
| `M/PersistenceOwnership.kt` | `617e630de2d5b8351f9046769eaa8bf3b58f1d7f1ba88b00497efe9280ae6f34` |
| `M/PersistencePhysicalCompletion.kt` | `1ffc209d1d160fb5089acb07a045788e84b4eb2401d26b3ebc6c4ab959b5a1ec` |
| `M/PrivateJdbcDataSource.kt` | `57d702ce9988b0bdd650387dd604d47edd0a4d3640f4f0071f6ad6311467a691` |
| `M/PersistencePgOwnedCutAccess.kt` | `6b11275185862051541d5fe1ba0c2d3b7bfa4b2a95a531161c381e01e3dc35c9` |
| `M/PersistenceTimeBudget.kt` | `a3f5f7024067aea99dcf1acdf8dd1a007a68bfaba01bd6077d5d019cd19cd2ef` |
| `T/PoolLifecycleTest.kt` | `953d018327fc7b40c53ab291bed061cae48751f8f20e0c5c0c3a369e03a2513e` |
| `T/PoolActorCustodyTest.kt` | `44a4712a49c7ea1f5b04081421b34296a8798b76d580c96b5db7bcdace00f1d1` |
| `T/OrdinarySourceGrantCleanupOwnershipIT.kt` | `a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557` |
| `T/PersistencePgOwnedCutIntegrationTest.kt` | `b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322` |
| `AGENTS.md` | `e65987b4aacc4b090d2cc3e3bcba040d56fefae4c0357afef3588b323f59f7b9` |
| `docs/PLAN.md` | `2d22357fd867d9edfccbffc1cbe1e6b9fbee9638967ffdaffd7e00d3e83050ea` |
| `build.gradle.kts` | `8b6116173f5a5fd76de7c9654685754631e2df1a480a692082995b3122fb7aa0` |
| `T/PgLifecycleDatabaseControlsTest.kt` | `ae098432000c15bdd4e90c45ddbf7ebb02e819dde2ebdf0db535b6ff720c056e` |
| `T/PersistenceJdbcDatabaseLifecycleTest.kt` | `3b10b0ffa4819df6d7e209402f02d9b91618487d26d6af5e47d9c9079e353917` |

**Final action recommendation:** primary applies only F1's internal-class correction, records the new test pin, and then separately admits the required focused compilation/tests and unchanged single-method real-PG acceptance. This report itself authorizes none of those executions.

