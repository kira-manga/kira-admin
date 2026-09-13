# CoreC2 Linux01 — independent actual-result review

**Disposition: overall FAIL.** Normal compilation and the exact bounded38 tests passed; owning Ktlint and Detekt failed. Retained evidence and scoped cleanup are coherent. No static waiver or broader acceptance follows.

Backend05, nonauthor, artifact-only review. Read/hash/JSON/XML/source-text analysis only: no Git, helper imports/execution, freezer/preflight, build/test/checker, process/service/network action, source edit or rerun. Only this private report is written. Requested model/effort is not independently runtime-attested. Primary owns notifications and any later launch.

## Bound evidence

All aliases are beneath `review/working/`:
- Q: `app-29-core-c2-product-lifecycle-linux01-preparation/`
- A: `app-29-core-c2-product-lifecycle-linux01-admission/`
- F: `app-29-w03-integrated-driver-core-c2-product-lifecycle-linux-01/`
- L: `app-29-core-c2-product-lifecycle-linux-01/`
- B0: `app-29-w03-integrated-driver-core-c2-diagnostics-01/`

| Artifact | SHA-256 |
|---|---|
| Q/recipe.json | `184a337998ecbf1ec499f08e461038499326cb7f6f1bbcf0a6a4f57fae3ba0a3` |
| F/manifest.json | `c332933651cda68222bed4335bf7fe5c32873fd137780fdc04480e62898ff603` |
| A/freeze-command.json | `4524f372d15ef6deb7c04246336284493a5d6dccee8074a138e5af3cda76d2a2` |
| A/preflight-command.json | `5823a037d7cac5b9a34764e9f8e2668389c17e7176c4d35a6de6e1ecbc582ce9` |
| A/admission.json | `dc20ca0a83c7999d8283b84159d3950d61222a6455bbb3635800747430aec42c` |
| L/result.json | `eb57bdd4c4925046b6a81bbb3d8f59d42f8849dbbfb8d22d3178b83570478e07` |
| L/validation.log | `e4dafa0bf687061d9a5b7a9fe1a8fa565dbb074baa9f4c98cc4a3837b87c9327` |
| L/primary-post-run-cleanup.json | `05a01e702bd769a22f03938b493dad61acdda1a28c3b67e7fb504c34ffbe0ef8` |

The recorded freeze197, read-only validation19 and admitted runner18 argv entries exactly match Q, substituting only F's actual SHA for the approved placeholder. Exit0 freeze/preflight receipts and exact466 preflight output agree; admission precedes the run. The actual Gradle task tail is exactly `testClasses test --tests …PoolLifecycleTest --tests …PoolActorCustodyTest ktlintCheck detekt --continue`, offline, with the unchanged pinned v3 runner/init.

F's entire466-entry source map equals B0 plus exactly the accepted8 replacements; the other458 values are unchanged. All466 known live source files and199 snapshot bytes matched independently. All348 seed keys remain; the sole removal is inherited, with no new waiver/removal. All102 historical pins are unchanged and rehashed; exact87 approved inputs retain prior63; active8 tools match Q, with all prior10 pins retained (5 active,5 provenance). Both fixture pins and all7 protected build/config/wrapper pins match. F's full diff and L/input.patch are byte-identical, SHA `c018f138e878c93de61d7ca18733929134186f28bd872db372cc2beb7e2f978f`. All18 local dependency artifact hashes match. Recorded private head is eb8fed8b6b620a0c7448c223bf49c1683f8eaadc; refs were not independently queried. Strict dependency verification is **not** proof of the transitive dependency-byte closure.

## Actual compilation and exact identities

The log records normal `compileKotlin`, `compileTestKotlin`, `testClasses` and `test`, not cached/replayed successes:15 actionable tasks,15 executed. All9 retained report pins,10 main class pins and1 test-class pin match result.json. The11 class headers are genuine classfile magic/major65; the retained successful javap command/log names the expected classes, including normally compiled PgRequireErrorHandlerTest. No javap was rerun by this reviewer.

Exactly two XML files exist: PoolLifecycleTest19 and PoolActorCustodyTest19; each has zero failures/errors/skips,19 distinct actual testcase identities, and no failure/error/skipped child. Exact names, signatures, parameter names, index order and ValueSource values match the hash-pinned frozen source and Q/declared-cases.json—not totals alone. All protected prior18+16 identities survive. The only new invocations are lifecycle's `MODEL exact RETURN incident retains custody and seals only the empty UNKNOWN cut` (1) and actor custody's `MODEL RETURN incident preserves authentic creation and generic or factory hard faults stay dominant` (incident-first,hard-first,operation-hard:3). Runner identities equal the XML identities.

XML SHA-256: lifecycle `ca17be23d1286761028147e8bf18a2126f57809f4c40f5e4477515bf54e8c91d`; actor `22ac2503267f33c6cd1168a187bb7fbfcd9ecc8610fdf599debc01296996f17d`. This is bounded MODEL/direct-boundary execution, not execution of the real-PG suite, opaque eviction/queue liveness, or zero internal physical attempts.

## Static failures are actual, not waived

Ktlint: **main66 + test61 =127 findings**; script report empty and script task succeeds. Detekt: **41 findings /41 weighted issues**, across13 rule categories. XML/SARIF/log match exact path,line,column,rule,message; text matches all41 identities. Every Ktlint report occurrence is corroborated by the log, and its declared rule summary equals the parsed occurrences. The log reports three failed tasks: ktlintMainSourceSetCheck, ktlintTestSourceSetCheck, detekt. Both recorded runner exit and validation command exit are1; `runner_status=FAIL`. An empty runner `failures` bookkeeping list does not turn that into PASS.

Counts by file (all under `common/infrastructure/persistence`; main/test prefix shown):

| File | Ktlint | Detekt |
|---|---:|---:|
| main/GuardedDataSource.kt | 1 | 1 |
| main/LeaseJdbcFacade.kt | 8 | 3 |
| main/PersistenceJdbcGuardProtocol.kt | 1 | 3 |
| main/PersistenceJdbcLease.kt | 5 | 9 |
| main/PersistenceJdbcPoolTransfer.kt | 1 | 0 |
| main/PersistenceJdbcTransaction.kt | 4 | 1 |
| main/PersistenceManagedObserver.kt | 4 | 0 |
| main/PersistenceOwnership.kt | 4 | 1 |
| main/PersistencePgOwnedCutAccess.kt | 1 | 0 |
| main/PhysicalJdbcDescendants.kt | 4 | 0 |
| main/PhysicalJdbcFacade.kt | 11 | 2 |
| main/PoolActorCustody.kt | 7 | 2 |
| main/PoolLifecycle.kt | 8 | 8 |
| main/PoolLifecycleFrames.kt | 7 | 0 |
| test/PersistencePgOwnedCutIntegrationTest.kt | 46 | 8 |
| test/PgLifecycleDatabaseProbeProcess.kt | 4 | 0 |
| test/PhysicalJdbcDescendantsTest.kt | 3 | 0 |
| test/PoolActorCustodyTest.kt | 8 | 2 |
| test/PoolLifecycleTest.kt | 0 | 1 |

Detekt categories: ComplexCondition=10, CyclomaticComplexMethod=3, InstanceOfCheckForException=5, LargeClass=1, LongMethod=2, LoopWithTooManyJumpStatements=1, MaxLineLength=6, NestedBlockDepth=4, ReturnCount=4, ThrowingExceptionFromFinally=2, TooGenericExceptionCaught=1, TooManyFunctions=1, UseCheckOrError=1.

**Earlier executed provenance: UNKNOWN.** No directly available earlier same-scope executed static packet was identified in the permitted finite CoreC2 material; historical searching was not expanded. The accepted before image proves the lifecycle MODEL method at line218 is newly added source, and its NestedBlockDepth finding is therefore associated with a new source site. That is not a prior executed baseline, nor proof that every other finding is retained. Unchanged source/lines must not be relabeled prior staticPASS. Separate future source triage does not alter this failed batch.

## Scoped cleanup and limits

The six command records are chronological and joined: validation exit1; stop, retained-bytecode inspection, second stop, diff-check and jps exit0. All five anchored barriers return normally, absent=true/forced=false, generations1–5, no signals/reaps/errors; each has exactly the expected cumulative acquired identities. The before-capture/before-deletion gates and capture-complete evidence agree with the unchanged runner's capture-before-scoped-delete order. Final six owned groups and both private-daemon lists are empty; child subreaper setting is restored to0. Process absence is credited as recorded receipt evidence, not a new kernel/process observation.

Both runner/supplement record all3 allowed generated paths absent; read-only filesystem checks confirmed absence. Only backend-build is listed as actually deleted. All40 admission-baseline daemon logs still match hash and size; the sole owned daemon19225 archive matches72323 bytes/SHA `c7a0b81c68f40dbe39bb86fc8809941e95f3bc8fdc7f07a3303f333c9a4a48ca`, and its original log path is absent. The supplement's cleanup/status/XML fields are consistent with the runner and independently read artifacts. Current466-source and18-local-dependency hash checks corroborate recorded input preservation. Cleanup does not rescue staticFAIL.

Historical run34678157417 remains **0 PASS/2 FAIL; cleanup FAIL; containers UNKNOWN; outputs_absent=false; six private directories retained**. Historical full47=45/47 stays separate; Native05 remains UNQUALIFIED. Native/full/W03/App29 status is unchanged. This report neither authorizes a rerun/checkpoint/PG10 launch nor grants real-PG/native/full/release acceptance.
