# App29 lease-dispatch PG03 — independent actual-result / failure review 01

2026-09-13T22:47:24.004363+00:00 · NONAUTHOR `/root/w03_static_nonauthor_review`.
**ACCEPT THE FAITHFUL FAILED RESULT AND BOUNDED CAPTURE/DISPOSAL EVIDENCE.**
PG03 remains **FAIL:1 PASS/1 FAIL**, not aggregate PASS, qualification or closure.
The original MODEL failure is a concrete test stack-witness JVM-name mismatch;
its later actor/expiry/retirement assertions have not been exercised successfully.
No source change, build, JVM/compiler, controller/collector/helper invocation,
network, CI, rerun, resource control or historical-result edit was performed here.
Only this new private0600 report was authored.

## Identity, capture and source binding

L=`review/working/app-29-lease-dispatch-pg03-admission-01/launch-01/`;
E=L`artifacts/`. Actual private run **34786407104, attempt1**, completed **failure**,
carrier `69997b8bf003e89b7e976a3d0a305e526d2c04ef`, backend
`f2e58eac0b139dca3a042c724d69c66a3d65278e`. Collector exit0 is collection success,
not gate success. `run-final.json` and the unique, nonexpired, same-run/same-carrier
artifact metadata agree. The artifact is `app29-lease-dispatch-pg-03-34786407104-1`.
The nested `run` in lane-release is the initial in-progress snapshot; completed
status comes from the retained final API result, not merely lock release.

Independently verified **exact64 regular0600 artifact files /3,890,250 bytes**,
no links/extra files, all collection sizes/hashes, all63 result-retained members
(excluding result's own hash), and the exact3 captured report members: one test
XML, class-load log and effective-classpath record. Both capture roots are present.

Before/after source-hash, tracked-path, SHA, branch, commit and clean-status bytes
match. The866-entry recorded source map contains all481 frozen source pins exactly;
source-binding/source-bundle and full checkout-before/after records also agree.
Accepted708-authority/214-snapshot/348-seed binding checks were **reused**, not
replayed. For diagnosis, separately matched current files and immutable f2e58eac
Git blobs for the test, phase, adapter, build, settings and Kotlin catalog to the
recorded map. Carrier Git blobs also match admitted controller
`406b9fd6af8913de5ec5aa9eb1426cd9bc8eb95a0a1717deb818a9d42ec4b382`
and authorized request `70444875f92e79816900b2df23ee68d1a9382f3cc1a535c36a9ccee7b143107d`.
No new binding authorization is implied.

## Actual normal compilation and exact two outcomes

Raw Gradle output records normal `:compileKotlin` and `:compileTestKotlin`, then
`:test`; neither Kotlin compile is skipped/up-to-date/frozen. Six actionable tasks
executed; build fails at tests, not the historical PG02 Kotlin compilation error.
The sole gradle-test receipt is exit1/outcome UNKNOWN. Actual final five task argv
match the unchanged selection exactly: `test`, then the two literal `--tests`
selectors; no enum or previous16 replay. The XML contains the same exact identities,
**2 cases,1 failure,0 errors,0 skips**, agreeing with decoded diagnostics:

Class: `me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest`.

| Exact method display name | Actual |
|---|---|
| `mixed pool creator nesting refuses wrong top fallback and unrelated lease use()` | PASS |
| `MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement()` | FAIL |

This establishes the focused mixed-pool case only, not all methods in that class,
a rewritten PG18, or successful MODEL execution at the later repaired assertThrows
callsite. PG14 fixed-scalar diagnostics correctly remain NOT_APPLICABLE/zero rows;
the MODEL factual line is raw evidence, not a new acceptance parser/oracle.

## Concrete failure: source name is not internal JVM method name

T=`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLeaseDispatchCreatorIntegrationTest.kt`:
SHA256 `f8583ac5daef026d2e691e2c42d14be93573dfbe442bee8c5f5d3188482eca1a`.
At **T:564** the existing witness is:

`assertTrue(Thread.currentThread().stackTrace.any { it.methodName == "afterJdbcCall" })`

The original retained AssertionFailedError stack, not just Gradle's abbreviated
T:627 summary, has this concrete call chain (outer→inner):

```text
LeaseConnectionCalls.invokeConnection                       LeaseJdbcFacade.kt:140
PersistencePhaseContext.afterJdbcCall$kira_backend            PersistencePhaseContext.kt:343
PersistencePhaseContext.requireWork                          PersistencePhaseContext.kt:509
PersistencePhaseContext.deadlineExpired$kira_backend          PersistencePhaseContext.kt:498
PersistenceFactoryProtocolKt.persistenceFactoryRemainingMillis  PersistenceFactoryProtocol.kt:141
PersistenceTimeBudget.remainingMillis                       PersistenceTimeBudget.kt:24
CreatorTailClock.nanoTime                                    T:806
...getClientInfo$lambda$8$lambda$7$lambda$6                    T:564
```

The phase source at342 declares **`internal fun afterJdbcCall`**, with343 calling
requireWork for BUSINESS. Internal-member JVM name mangling accounts for the
observed `$kira_backend` suffix: settings name the module `kira-backend`, and the
catalog/build pin Kotlin2.1.21. The actual stack independently exposes the emitted
name; no fresh compiler run or guessed method table is used as evidence.

Class-load records resolve the exact phase and LeaseConnectionCalls classes to
this run's normal `backend-build/classes/kotlin/main/`; the test, CreatorTailClock
and CreatorTailDiagnostics resolve to its normal `classes/kotlin/test/` (log lines
12963,6412,2243,2451,2452 respectively). Thus this is not a stack from an unrelated
same-named class or a missing actual afterJdbcCall path. The literal source-name
comparison cannot recognize its desired, visibly present internal JVM frame.
The exception stack is retained; the separately evaluated Thread.stackTrace array
itself was not saved, so this report does not pretend to inspect that array.

**Bounded next source correction:** retain the real frame witness, using the exact
product declaring-class identity and the observed JVM method identity (or an
equally exact reviewed derivation), not broad substring/prefix matching, removal
of the assertion or a production visibility/budget change. Test/synthetic method
names themselves contain `afterJdbcCall`, making broad matching especially weak.
This diagnosis does not authorize that change or another run; primary owns both.
No product defect beyond this test witness is established by this failure alone.

## What did and did not run

The single factual line ends at these six stages:
`STORE_ENTERED,LEASE_OBTAINED,SETUP_OBTAINED,LOWER_RETURNED,CLOCK_ARMED,CLOCK_ENTERED`.
It reports `actor_ran=false call_returned=false call_failure=AssertionFailedError
expected_expiry=false call_code=null call_database=null call_cleanup=null
phase_code=WORK_FAILED phase_database=ROLLED_BACK phase_cleanup=true
unexpected=AssertionFailedError`.

Source order and the original failure agree: frame/ticket lookup precedes564, but
identity/budget/dispatch/count assertions at565–571 have not passed; neither
TAIL_WITNESSED572, MODEL clock advance573, expiry575, retirement578 nor actor
construction/start/completion599–609 was reached. Do not turn actor_ran=false into
an actor-dispatch defect or TIME_BUDGET_EXHAUSTED evidence. Those outcomes remain
unmeasured for this run.

CreatorTailDiagnostics retains the first failure at709–718, treats a pre-witness
assertion as unexpected at721–736, and rethrows it through635/759–760/763–779.
The phase's WORK_FAILED/ROLLED_BACK/cleanup=true record does not erase that original
assertion. T:627 in the Gradle summary is the executor entry on its stack, not proof
of a separate failed assertThrows-type expectation or intended work expiry.

## Disposal evidence, with all six sticky failures preserved

Recorded immediate/final `./gradlew --stop` both exit0 and say no daemons running.
All five owned-process barriers are NORMAL_ABSENT, empty/no remaining processes,
no adopted process, no term/kill/errors. Every barrier still retains the original
gradle-test leader pid2287 exit1. Controller drain deliberately accepts absence
for disposal while appending nonzero-child failure; command's nonzero require
also records validation failure. All **six** raw sticky stages remain:

1. `interrupted-gradle-test-nonzero-child`
2. `validation`
3. `after-immediate-stop-nonzero-child`
4. `before-file-cleanup-nonzero-child`
5. `after-final-stop-nonzero-child`
6. `before-home-cleanup-nonzero-child`

These are five repeated observations of the failed Gradle leader plus its validation
failure, not six independent source failures. They are never erased by cleanup.

Raw events independently match owned-containers.json: exactly one PostgreSQL17.6
and one Ryuk0.12.0, both created/destroyed, none remaining. PostgreSQL has **kill9,
die137, destroy**; Ryuk has **die0, destroy**. Natural controller final absence is
**not graceful shutdown or zero-kill**. Census0–8 retains Ryuk, census9/after-cleanup/
final are empty. Both capture roots/required capture, topology, input preservation,
retained inventory, final children and final containers flags are true and supported
by their records. All11 owned-output rows record cleanup attempted/complete and
absent with no skip reason. These are retained hosted observations, not current
filesystem/process inspection of the completed runner.

Aggregate PASS remains impossible: tests failed, gradle-test is nonzero/UNKNOWN and
failures is nonempty. Controller elapsed242.055s/cancelled=false and successful
bounded cleanup do not qualify the failed attempt.

## Pins and unchanged limits

| File | SHA256 |
|---|---|
| E`result.json` | `a7bf8ad299b8805009c367d226bdf90b2fcf1b7515b8d909ae29b4d4a2cba79a` |
| L`collection.json` | `ebdd6aaa17cff574eac67638923e8af0c88f8b2282a07c5a77899a9d111c6487` |
| L`run-final.json` | `17e28998aa1382c523422fb002e8a3c7300c3cbe673422af2db5635161608abe` |
| L`artifacts-metadata.json` | `50372b5668a3aabce59ad2e559495c3fe0fbc408e938c527402eea904c0dbf97` |
| E`test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.xml` | `7b9e31356522d9c22dac2e79839c65f5f5e80d456fa52e855eafdab74e41a943` |
| E`gradle-test.log` | `e03efc80fee2874fcf80a932fd3ba908cf07d194367dd6e217a356527ba80816` |
| E`reports/lease-dispatch-pg-03/class-load-2421.txt` | `84a642eb1ebf872e6da2e71999d0d79763c6588ee26b9b7c1d2f89e16274de39` |
| E`reports/lease-dispatch-pg-03/effective-classpath.txt` | `5956dd8fa2c2fdea6cf57b5a9680d8ee8453d078a29bf9ee489d72472d9352e2` |
| E`container-events.log` | `37b8168275b843434c6c20b613f4c027d50caf12e2ef72af3954b6ccdbd5cd64` |
| E`owned-containers.json` | `6e2acb1a987fe5d5690aab1c9eca0d5c17a6ff6c34e505fc1422fc307b27593c` |

Historical PG02 remains compileTestKotlin failure/no XML/seven sticky failures and
its original retained-output limitations. PG18 remains16 PASS/2 FAIL with its raw
six failures; this review does not prove earlier causation or rewrite history.
Native05 remains UNQUALIFIED. No full47/consumer/opaque/liveness/W03/full-P3/
production/new-data/installation-recovery or App integration credit; W06 excluded.
Suppression-disabled Throwable and pre-callback EMF-init limits remain. Only
primary may adopt a separately reviewed correction and admit new evidence; this
consumed PG03 attempt grants no rerun/dispatch or public-private-ancestry push right.
