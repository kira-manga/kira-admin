# App29 lease-dispatch PG01 transport02 — independent actual-result review

2026-09-13 UTC. Passive, non-author review for the primary; no rerun or change authority.

## Disposition

**Verified actual FAIL: 18 cases, 16 PASS / 2 FAIL, no ERROR/SKIP.** The selected scope and W03 are not accepted. Raw/source custody is consistent, and the retained cleanup records support final absence and input preservation separately from the failing test/child outcome. Neither new failure is erased or relabeled as a pass.

Run: https://github.com/kira-manga/kira-admin/actions/runs/34762007741, attempt 1, completed/failure. Backend `8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3` (tree `fc480e82630091138da145ade1812cedcd75e58e`); carrier `6794795c9d40b6a99a4af9b4c46cf6e7a0f68d27` (tree `2443abc41e32c7a0af125b2af7c12436c5965d9b`). Use completed `run-final.json`, not the stale in-progress nested run copy.

Below, `L=review/working/app-29-lease-dispatch-pg-admission-02/launch-01`, `A=L/artifacts`. Backend source prefixes: `P=src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence`, `T=src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence`.

## Custody and actual scope

- Independently recomputed all 60 retained-file hashes/lengths and all 61 collection entries: exact roster `60 + result.json`, no missing/extra files, error fields, symlinks or non-0600 raw files. Four captured-file entries agree with retained bytes.
- Before/after source-hash files are byte-identical: all **866** path/hash entries match Git blobs at backend8938526 and the live clean backend at review. Both tracked-path lists equal the complete 866-path Git tree; both recorded status logs are empty. All **481** frozen manifest source hashes are an exact subset. This is byte custody, not a semantic audit of every source file.
- All **593** authority pins match originals and deployed authority files, with an exact deployed roster. Five tooling originals/deployments, source bundle and checkpoint also match; all **600** bound deployed paths match carrier6794795 Git blobs. Admin was clean at that carrier. Bundle is 280735 bytes; no target binding/checker was executed or imported.
- Full two-suite XML failure stacks/stdout/stderr were read (stderr empty). XML contains exactly the frozen profile's 18 distinct `(class, display_name)` identities; no duplicate/missing/extra case. The eight parameterized names are the exact indexed `mode=POOL_LEASE_CREATOR_*` rows, not fabricated no-arg method names.
- Retained Gradle log shows normal main/test Kotlin compilation and one test invocation with 11 filters, then `18 tests completed, 2 failed`; no fresh Ktlint/Detekt invocation is claimed. `PoolLeaseDispatchCreatorIntegrationTest`: 17 cases, 15 PASS/2 FAIL (31.808s). `OrdinarySourceGrantCleanupOwnershipIT`: one PASS (14.905s).
- Effective classpath records Native05 JAR `50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`, checker-qual3.55.1 `857658c8bdcbff794949a8d9922f88d63ee3751c203c7cd7d21ea97f9e745288`, and HikariCP6.3.3 `709f378c05756280939ce50fc1b1f1a53bb8e1899dc1b249f21f12703640b48b`. Targeted class-load rows identify Driver, SharedTimer and PgConnection from Native05, and HikariDataSource/HikariPool from that Hikari JAR. Stock PG42.7.12 is recorded as removed. Retained Native05/checker input bytes match these hashes. This is runtime-origin evidence, not final-JAR consumer qualification.
- Artifact metadata identifies id10319890785, name `app29-lease-dispatch-pg-01-34762007741-1`, 333525-byte archive, server digest `8e2c1f5811be4a8c57b4c18a435f89ee018948569fd90a44e536bed0f64d2049`. No retained ZIP was independently rehashed; extracted-byte checks above are the independent verification.

### Principal evidence pins (SHA-256)

| File | SHA-256 |
|---|---|
| `A/result.json` (79812 bytes) | `e64b94410e240f7585ac6d4a2d70c90b3b8952d75e61cfa5e055f15fb1e69bc9` |
| `L/collection.json` | `dded7894078740b37f22ec22b2c5ca6cd09982169240bb4759bf6cef4374cc93` |
| `L/run-final.json` | `3793e3a58f73cd93cae2222db537582a7130d145d000e2be17c0cb785c3d8b05` |
| `A/test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.xml` | `1e40141e4e41cd40b9f8ba7544da766d3e6bb1e10c16e47e72bb772b0ec2acdd` |
| Same directory, `TEST-me.manga.kira.backend.common.infrastructure.persistence.OrdinarySourceGrantCleanupOwnershipIT.xml` | `d4aebf27f8ed9ed58e43889be5e2613d33b0728712bc827aee222db19f1d257d` |
| `A/gradle-test.log` | `3d13c1dd5a353540b1165990724d5c896915946881949516607b89b7f05a6e6c` |
| `A/before-source-hashes.json` = `A/after-source-hashes.json` | `d65f6ecf66fabd482e897ccb09e44e78ce95d25fad1951a49630ca20ec080f8c` |
| `A/reports/lease-dispatch-pg-01/effective-classpath.txt` | `019d964757fb49aa74d0fc023a2d12fddf7da898ad14e821cb7f89313ed7628d` |
| Same directory, `class-load-2645.txt` | `66293704bda9fa6d99a868bd5085e85763c1f67e2d65444722f850e9a50eef83` |
| `A/container-events.log` | `969782bcad4c82a6bcc9814aa7eacc8e9ffeee9f1739c2d3edbed7b6ca3f8d61` |
| `A/owned-containers.json` | `20061594ebecd7cdf3fda62cf50c8ccbfc741583403b944a1a982a6ef292f2bd` |

Frozen manifest `review/working/app-29-w03-integrated-driver-lease-dispatch-pg-01-transport-02/manifest.json`: `1387f68bccac8797a5fc413d58495d748c3b28715f60b6074f7dca7e19ef94ba`; transport metadata (parent of L): `38caa0045dd4a79bf1fdf011f2aa798a1796257651ddcfa83fb52e1c202bce38`. Source checkpoint `review/working/app-29-lease-dispatch-source-checkpoint-01/checkpoint.json`: `2d291cf217291106d35343c6f74f4d892299e766b72615620bec122ee0f79e37`; sibling `backend.bundle`: `235fca34c51710930fd9ced4444d0931e5273137bd4178169c3b8c9c4010ec50`.

## Failure 1 — mixed-pool creator nesting

**Observed:** `mixed pool creator nesting refuses wrong top fallback and unrelated lease use()` failed in 20.087s. Primary `TIME_BUDGET_EXHAUSTED` originates at `PersistenceTimeBudget.kt:25` -> `PgLifecycleTestScope.kt:86` -> **`OwnedCutPool.close` (`T/PersistencePgOwnedCutIntegrationTest.kt:1415`)**, on the inner fixture at creator-test327. The only suppressed exception is managed-shutdown `PENDING` from `PgLifecycleTestScope.close:61`.

This is **inner-pool teardown failure**, not a recorded body assertion failure. The `use`/`closeFinally` chain preserves an existing body throwable as primary; here close itself is primary. On this recorded path the nested body/connection scopes returned before the failing fixture close. That does not make the test pass or prove complete disposal.

Stdout records HikariPool8 shutdown at 14:18:38.912–38.940, then HikariPool7 shutdown at 14:18:58.914–58.916, followed by one root `TRACKED_LOCAL_ENDED`/12 actors cleanup line. Hikari's completion message alone is not root/actor termination proof. No per-root timer/actor branch scalars were captured.

**Source-supported explanation, not measured branch identification:**

1. Creator-test325–356 nests two `withOwnedCutPool` calls. Each fixture1370–1386 constructs a separate lifecycle root and waits for timer readiness, then attempts full inner-root closure before outer teardown begins.
2. `P/PersistenceDriverTimer.kt:76–113` acquires/releases only its own reference; `PersistenceJdbcDriverRoot.kt:76–105` and timer44–60 require both local drain and actual captured Timer-thread termination. Own-reference release is not sufficient.
3. Native05 `Driver.java:753–755` returns static SHARED_TIMER; `util/SharedTimer.java:47–95` increments references and intentionally leaves the Timer alive while another reference remains. The still-open outer root therefore supplies a structural reason an inner full-end demand cannot complete normally. The timer controller releases asynchronously after root/participants/scanner drain; this does not require a second observer worker.
4. `PoolLifecycle.observe:445–489` also has other PENDING gates. No actual timer-reference identity/count, participant gate or actor branch was logged. The 8-second `awaitLifecycleFact` predicate can itself call the original 10-second pool/root observer; the additional scope-close observation has its own existing budget. Timing is consistent with that path, not evidence that work needed a larger allowance.

**Smallest justified correction direction:** a test-only paired/two-phase fixture teardown, after both connection/creator scopes unwind: request shutdown and invoke actual close for **both** owned pools before waiting for either full-root end. Retain original budgets, receipts, all actor/root assertions, failure precedence and guaranteed cleanup of both fixtures, including exceptional paths. If needed add bounded per-root scalar diagnostics to identify the actual PENDING gate. No timeout increase, Timer cancel, foreign-pin release, synthetic completion or relaxed production observer is justified. No correction was applied or validated by this reviewer.

## Failure 2 — MODEL work expiry in actual afterJdbcCall

**Observed:** `MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement()` failed in 1.648s at **creator-test613**, `assertTrue(witnessed && actorRan.get())`. No suppressed teardown failure is recorded; HikariPool11/EMF close and root cleanup follow. The generic `assertThrows<PersistencePhaseException>` at606 succeeded and the `requireConnectionFree` wait607–612 returned. Final outer-tail/quiescence/active-owner assertions614–616 were **not reached**.

The failed conjunction records neither individual flag. It proves only that at least one flag was false, not which one. It does **not** establish store/callback entry, clock advancement, retirement, actor construction/start/termination, or an actor-admission rejection.

**Why the actual inner cause is unavailable:** test529–618 swaps the selected Hikari handle's delegate with a test-only `getClientInfo` shim. After the real lower call, its clock callback553–591 checks creator/lease/original-budget identity, actual `afterJdbcCall` stack, ended guard/restored dispatch, advances the MODEL clock, requests/observes epoch retirement, and attempts to create/start/wait for termination of an authentic Hikari actor. `witnessed=true` is last. Any earlier setup/shim/callback assertion or call failure can escape into `src/main/kotlin/me/manga/kira/backend/complaint/infrastructure/transaction/OrdinaryPersistencePhaseExecutor.kt:15–29`, which catches **Throwable** and finishes the phase. `P/PersistencePhaseContext.kt:247–258,482–491` converts the failure to a bounded phase result; `PersistencePhaseOwnership.kt:124–128` deliberately retains no cause/suppression/stack. The broad expected-type assertion can therefore accept a different preceding failure and leave only line613 visible. This is **body diagnostic masking**, not teardown masking.

Reviewed call ordering includes `LeaseJdbcFacade.kt:88–140`, `PersistenceJdbcGuardCall.kt:71–107,128–154`, `PersistenceJdbcLeaseInvocation.kt:24–40`, `PersistencePhaseContext.afterJdbcCall:342–344`/`requireWork:503–510`, `PoolActorCustody.reserveLocked:140–159`, and the test clock652–670. The creator's outer-adapter extent surrounds `phase.afterJdbcCall`; no definite ordering defect or actual expired-business-budget recheck at actor reservation is established. Native05 `PgConnection.getClientInfo(String):1744–1747` was read; no evidence identifies it as the failing step.

**Smallest justified next step:** test-only diagnostics, not a speculative product change. Retain the first exact setup/shim/callback failure and surface it outside the sanitizing phase, after shim/phase cleanup while preserving fixture teardown and original failure precedence. Capture bounded checkpoints (store entry, lower return/callback armed and entered, budget identity/expiry, retirement observed, actor constructed/started/terminated), split the final booleans, and retain caught phase `code/databaseOutcome/cleanupProven`. Keep the MODEL label, original budgets, source route and all existing oracles. Do not relax613, broaden the expected exception, or claim expiry/actor progress without recorded evidence. This recommendation grants no rerun authority.

### Source pins for the bounded analysis

All backend sources are additionally bound by the complete 866-file receipt/Git check above.

- `T/PoolLeaseDispatchCreatorIntegrationTest.kt`: `db140c4c0e93a349608b6e05e80033fd07e298aee4c272932e78b6d69564ce4a`.
- `T/PersistencePgOwnedCutIntegrationTest.kt`: `b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322`.
- `T/PgLifecycleTestScope.kt`: `7574167d18008256a43ff056e5797d5882abe1defc4ffcdda46e72a02a0ae9ec`.
- `T/OrdinarySourceGrantCleanupOwnershipIT.kt`: `a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557`, identical at parentccdbb28 and source8938526; current native-fault method512–550 was read.
- Executor at the exact complaint path above: `43ef1e1ab32603ac03a5d5ec64ccf04f73bd1e6776763a830292efd151576cbc`.
- Native source root `.kira-validation/pgjdbc-owned-cut/upstream/pgjdbc/src/main/java/org/postgresql`: Driver `a9041811fc89d250f98fd8be08be3d52a107e19846117457822409008a648abe`, util/SharedTimer `b70ea6b561f15bed5ed66071fcd8d924eda032afe9fd0cbc808255637f39a066`, jdbc/PgConnection `486aba8d77f3a38b9b0b16540bf7f62010c438803bf4cc426e05bbb5c3528114`. All three match Native05 `sources-after.json` (`e3ae4b1579c4e46a7571f7d0c80fd15f9ff946d4056e0089c204a70cbac0d57e`); this is not a full native-source re-audit.

## Cleanup, sticky outcomes and limits

- Result records `containers=NORMAL_ABSENT`, `outputs_absent=true`, `inputs_preserved=true`, complete capture/inventory, final children/containers absent, cancelled=false. All 11 owned-output entries record attempted/completed cleanup and absence, no skipped reason. Source before/after custody independently agrees.
- Five process barriers record empty `NORMAL_ABSENT`, no remaining/activePopen/adopted children, term/kill operations or errors. **Every barrier still retains gradle-test leader pid2462 actual_exit=1.** Of 52 command records, gradle-test is the only nonzero command (outcome UNKNOWN); both stop commands exit0 and say no Gradle daemons running.
- All **six failure entries remain sticky**: validation ValueError plus nonzero-child RuntimeError at interrupted-gradle-test, after-immediate-stop, before-file-cleanup, after-final-stop and before-home-cleanup. Later absence does not turn these into a successful run. UNKNOWN grants no retry authority.
- Actual events record two postgres:17.6-alpine containers and one Ryuk created and destroyed; both PostgreSQL containers have **kill signal9 / die137**, Ryuk die0. `owned-containers.json.remaining=[]`; normal polls0–8 retain Ryuk, poll9/final/after-cleanup logs are empty. Thus controller-unforced final absence is supported, **not graceful-shutdown or zero-kill proof**. No live host/container/process probing was performed.
- Eight passing fault-child cases retain PROCESS_ONLY/product_end=false, not product disposal. Controlled fatal SQLState57P01 and clock seams remain MODEL. Registered-tail faults do not cover an absent/unregistered tail.
- PG14 fixed-scalar diagnostics are explicitly **NOT_APPLICABLE**, zero rows, not CAPTURED. Consumer is NOT_EVALUATED. Native05 remains **UNQUALIFIED**.
- Current unchanged OwnershipIT PASS is evidence for this source/run only; historical ordinaryPG01 remains20PASS/1FAIL with its close-executor actor/queue mechanism unmeasured. Prior transport01 run34760235411 remains a pretest FAIL with containersUNKNOWN/cleanupFAIL. Historical PG14/PG10/PG1/nonDB56 are not fresh cases in this run.
- No full18/47, consumer/opaque/liveness/W03/full-P3, production/new-data, installation-recovery, integration/public private-ancestry push, or rerun acceptance follows. W06 remains excluded.

Review actions were passive file/text/JSON/XML/hash/stat reads and Git reads with `GIT_OPTIONAL_LOCKS=0`. No target runner/helper execution or import, AST/syntax/checker/build/test, acquisition, resource/process probe, CI/ref/binding/lock/lease/worker action, source/tooling edit or rerun occurred. The only new write is this private0600 report; no workers or temporary outputs were created. Hash coverage does not claim a full semantic re-audit of accepted tooling or donor sources. Primary handles owner notifications and any separately authorized correction.
