# Core C2 hosted02 — independent actual-result review

Reviewer: Backend05 (`/root/backend_05_history_hosted_review`), NONAUTHOR, 2026-09-12 UTC.

**Disposition: verified failed development run, 45 PASS / 2 FAIL. Not Core47 PASS, not JAR qualification.** The retained evidence supports the actual selection, source/runtime bindings and outer cleanup, but does not establish the precise internal cause of the two failures.

## Scope and evidence

- `D` = `review/working/app-29-core-c2-hosted-launch-02/`; `A` = `D/artifact/`.
- `F` = `review/working/app-29-w03-integrated-driver-core-c2-hosted-02/`.
- Reviewed already-downloaded local JSON/XML/logs, bound source and file hashes only. No Git commands, helper/controller execution, builds/checkers, CI/network/service operations, imports or reruns. Only this separate private report was written.
- Prior design/staging reviews remain separate: `app-29-gate-b-hosted-draft06-independent-actual-review.md` SHA-256 `baca287b58d86f7fc833f0bf2a423613a4bb035179d9c4c75495dcb55b4f121d`; `app-29-core-c2-sensitive-staging-02-independent-actual-review.md` SHA-256 `c154e27c98593c849cfe7fa3fab14d1cb57717cccfb9f070c1ad09eedeec1abe`. Their bytes and all 25 draft06 seal entries still match. This is not another design audit.

## Actual result and smallest demonstrated failure boundary

Both raw XML files contain exactly the profile04 identities, including all 47 distinct expected class/display-name pairs, with no missing, extra, duplicate, error or skipped cases.

| Suite | PASS | FAIL | Suite seconds |
|---|---:|---:|---:|
| `PhysicalJdbcDescendantsTest` | 16 | 0 | 2.279 |
| `PersistencePgOwnedCutIntegrationTest` | 29 | 2 | 55.649 |
| **New aggregate** | **45** | **2** | |

The only failures are:

1. `throwing original RETURN override leaves F G T free and retires its exact source without a second return()` — 31.624 seconds; test line 730.
2. `failed post consent real Hikari tail seals actor admission but cannot retire the successor epoch()` — 18.070 seconds; test line 576.

Both raw primary stacks identify the same boundary:

```text
PersistenceBoundaryException: Persistence boundary rejected: TIME_BUDGET_EXHAUSTED.
PersistenceTimeBudget.remainingMillis(PersistenceTimeBudget.kt:27)
awaitLifecycleFact(PgLifecycleTestScope.kt:86, default at :84)
OwnedCutPool.close(PersistencePgOwnedCutIntegrationTest.kt:1265)
AutoCloseableKt.closeFinally(AutoCloseableJVM.kt:42)
withOwnedCutPool(PersistencePgOwnedCutIntegrationTest.kt:1241)
```

The exact bound fixture at lines 1261–1280 first obtains a non-null shutdown receipt and checks invocation `RETURNED` or `ALREADY_CLAIMED`, then polls until `receipt.observe()` is not `PENDING`. Its fresh default allowance is 8,000 ms; the visible rejection occurs when the remaining floor milliseconds reach zero. Thus the demonstrated failure is **failure of that pool receipt to leave `PENDING` within the fixture's allowance after an allowed shutdown-invocation result**. The subsequent expected `UNKNOWN`/`TRACKED_LOCAL_ENDED` and actor/factory/retired-generation assertions are not reached in that close invocation. This is not evidence of permanent pending or of a particular retained actor/thread.

The first test selects `ReturnCallerFault.SAMPLE`; the second sets `expectedPoolUnknown=true` and selects `failTail=true`. Neither XML failure contains an earlier assertion, `Caused by`, or suppressed failure. I do **not** infer blanket test-body success or a root cause merely from the teardown frame or that absence; source/state diagnosis is separate.

The raw suite output also records HikariPool-1 shutdown at 04:17:52.960 and a close-executor timeout at 04:18:02.963, and HikariPool-6 shutdown at 04:18:11.605 with the same warning at 04:18:21.623. Each subsequently logs “Shutdown completed.” The aggregate output does not itself label those pool IDs with testcase names. Those warnings are relevant correlated evidence, not proof of which queued task/worker remained or of product disposal. The actual loaded Hikari version is **6.3.3**, not an assumed declared version.

## Run, authorization and immutable bindings

- Private run **34672394928**, consumer job **103496098502**, completed `failure`; only the validation step failed. Evidence upload and post steps succeeded.
- Executed carrier **`b25f6adcdb37b25b44b4efb783889f06c02c85d9`** agrees across job checkout, `A/carrier-sha.log`, launch/completion and artifact metadata. `D/carrier-commit.json` instead records intermediate `2356cea993f6e3828a34d68991d9c6fc2a308526`, explicitly `NOT_PUSHED_YET`; it is **not** the executed carrier receipt. No new Git/history reconstruction was performed.
- The local archived authorized request is SHA-256 `d153820f2c8668ceef0bb8d3e65ffa93026ae7bbe0936eba248465125de37c4c`, identical to the deployed local request. Only `authorized` differs from the archived false request. Primary admission SHA-256 `89616c33609bfceb495a9d180a639047a780878fb56789ccff20cb206bad52a6` binds that change; the job records a successful immutable-input/one-run authorization gate. Request tool hashes match the local deployed/sealed files.
- Backend **`989a8c07b90d956a5f2484f223be41b5d99a8a3c`**, tree **`6e21c50e94ff863715ccf0c5b67183743b1a5046`**. Hashing the retained raw commit-object bytes with the commit-object header independently reproduces the before/after sole-parent chain `989a8c07… → 926927ab805a2a3b78957862f3b744d0fe399ac5 → 49da0919d9ec3091cb7bb041009dc9bd5f3e090f → public 3d839130c807f6a0a9b1c896c1c6cca4b41c4538`.
- Checkpoint SHA-256 `e9c815f0e2572be36b86c9d3c1302bb041bf56780d25976a71f319ad7a3e1a73`; bundle 198,761 bytes, SHA-256 `d3000767393f723ab10b9a66e142fd6a0eb470738972e398df8ce6ba53589e8c`. Initial public detached checkout and successful private bundle verify/fetch/checkout are retained; before/after bundle receipts agree.
- `F/manifest.json` SHA-256 **`40000ce7fc95efec6ba4ce966deedb41df4e7d99731cf1e92947909d3781a6d5`**. Both raw source-hash maps contain the same 851 tracked paths; both tracked inventories match those maps and both status logs are empty. Every one of the 466 frozen source hashes matches both maps; all 199 local retained snapshot hashes match the manifest. The single changed source relative to hosted01 remains the provenance-binding test, SHA-256 `a92f7a1bc152576c0bc2cd55d3dea49614ca073aea3868c2929e5bf1fea48017`. Both source-binding receipts agree on 348 seed paths, 357 authority files, 21 Core sources, profile04 and Native05 `UNQUALIFIED`.

## Raw provenance subevidence — not an overall consumer PASS

Independent comparison of the raw data against the sealed profile finds:

- All 186 effective-classpath paths are unique. Stock PostgreSQL 42.7.12 SHA-256 `31fbf6f06b2217fb51d5100cee51b22625cc81640da0679b47914e54c1e6377c` is explicitly removed and absent. The only PostgreSQL-class/service supplier is Native05, 1,200,036 bytes, SHA-256 **`50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`**, with 512 PostgreSQL classes/one service. The only Checker supplier has 385 classes, SHA-256 `857658c8bdcbff794949a8d9922f88d63ee3751c203c7cd7d21ea97f9e745288`. Local candidate/Checker input bytes also match the profile hashes/sizes.
- Exactly the required and original witness files exist, with 81 and 83 unique keys. Both associated selected tests actually PASS in XML. Both record profile04, the exact JAR/Checker hashes, one PostgreSQL provider, the expected MR Cleaner fields and identical worker **PID 2611** / JDK / executable / positive loader **`jdk.internal.loader.ClassLoaders$AppClassLoader@639fee48`**.
- All expected positive class-source/loader mappings agree, including original `PgConnection`. The sole PID-bound class-load file supplies exactly one expected `source:file` association for each of the 13 PostgreSQL origin classes and Checker class. Intentional negative `defineClass` loads are not substituted for positive suppliers.
- Worker JVM/process arguments include profile04 and both no-attach/no-dynamic-agent flags. The unchanged `app-29-gate-b-hosted-01` scalar is the original-provider compatibility assertion, **not** the identity/acceptance of this run.
- Actual runtime: Temurin **21.0.12.1+1-LTS**, Gradle **8.14.5**, HikariCP **6.3.3** (SHA-256 `709f378c05756280939ce50fc1b1f1a53bb8e1899dc1b249f21f12703640b48b`), Kotlin stdlib **2.1.21** (SHA-256 `263bdc679e1f62012db7b091796279b6d71cf36f4797a98ff1ace05835f201c8`), JUnit Jupiter API **5.12.2**. Class-load lines confirm `HikariDataSource`, `HikariPool`, `ProxyConnection` and `AutoCloseableKt` originate from those actual JARs. Real PostgreSQL 17.6-alpine/Testcontainers 1.21.4 started successfully; image receipts retain PostgreSQL and Ryuk 0.12.0 digests.

These independent data comparisons support the narrow provenance subevidence. **The controller consumer itself remains `FAIL` at `XML_SUITE_PASS`, before completing its later provenance gates.** Neither the witness text `provenance=PASS` nor this independent comparison converts that consumer to PASS.

## Capture and outer cleanup

- Every one of the **52 retained ledger files** matches its recorded byte count/SHA-256, with no ledger errors. All **six captured raw files** match both capture and retained hash/byte entries. The exact extracted closure is **53 regular files** (52 plus `result.json`), with no missing/extra files or symlinks.
- Artifact **10290114628**, `app29-core-c2-02-34672394928-1`, is reported as 236,154 compressed bytes with SHA-256 `fdbcd4e5e3e4704ceaa3d1b455f9ba2cb558bcd2675de0c258dc2baf3deb1e54`, agreeing between metadata and upload log. No ZIP is retained here; I verified extracted-file hashes, **not an independently recomputed archive hash**.
- Controller result is `FAIL`, elapsed 366.608559264 seconds, `cancelled=false`. Of 42 recorded commands, only `gradle-test` PID 2431 exits 1 (`UNKNOWN`); the other 41 exit 0. Gradle actually compiled main/test Kotlin and executed six actionable tasks, with no cache/up-to-date substitution; failure is at the completed Test task.
- All five process drains report `NORMAL_ABSENT`, empty/OK, no remaining/active handles, TERM, KILL or errors. Each retains the **same** historical PID 2431/exit 1. The seven failure receipts are five sticky nonzero-child records plus validation and `XML_SUITE_PASS`, **not seven independent test or cleanup failures**.
- Capture completed; both same-home Gradle stops returned 0 and recorded no running daemons. All 11 owned output/home cleanup rows are attempted, complete and absent, with no skipped reason. Inputs are preserved, final child/container absence is recorded, and final raw container censuses are empty.
- Container events cover exactly two PostgreSQL containers and one matching-session Ryuk, all destroyed; no controller `remove-owned-containers` fallback ran. **`NORMAL_ABSENT` is not a claim of graceful PostgreSQL exit:** both PostgreSQL containers have Docker signal 9 / exit 137 events before destroy; Ryuk exits 0/destroys. This proves outer absence according to the retained ownership receipts, not positive product lifecycle completion.
- The two deliberate pending probes explicitly retain `PROCESS_ONLY`, `product_end=false`; their child receipts show unforced absence (PIDs 3210 and 3245). They remain negative probe evidence, not disposal or a general exit-code waiver.

## Principal evidence hashes

All values are SHA-256; XML names below share `me.manga.kira.backend.common.infrastructure.persistence.`.

| File | SHA-256 |
|---|---|
| `A/result.json` | `103b93f13e89a298653319497468b544d15a47970e1c2b9fcc1230decfca36eb` |
| `A/test-results/test/TEST-…PersistencePgOwnedCutIntegrationTest.xml` | `465024fa05e267de6ec2eae2a8189363e397422baf7e2004f7286992f28b816f` |
| `A/test-results/test/TEST-…PhysicalJdbcDescendantsTest.xml` | `ee2bfcbb25e2386967c0215e587873b730ec585d2532413d50db22c66f7ecf8c` |
| `A/reports/final-jar-profile-04/effective-classpath.txt` | `febc6af689a032df63d55c2fc7a44378ed1eeb2409bec5685f0675f72e10dded` |
| `A/reports/final-jar-profile-04/class-load-2611.txt` | `149351a025e40f8fd704a3a71586e43de8a3131a603ce41c9546a199cbc2fca7` |
| `A/reports/final-jar-profile-04/worker-runtime-required.txt` | `2a9db841c98811bcd224605eb28e5d170636d1fef49b707b2ca1dd01fd3caa0a` |
| `A/reports/final-jar-profile-04/worker-runtime-original.txt` | `97c20460143e80a7f43b0024bf70ab4475769f25508cfdef27430189178a437d` |
| `D/job.log` | `d33a88d1a492badb6051b8a62d6bddf10f8ea808dd13f0b0792ad8082bf296fb` |
| `D/run-completed.json` | `97d300e473f885f4fcdab886f71bf3c314649ec072789ed2903fdc81b99a9d8b` |
| `D/artifacts.json` | `5bb2e781949efca22bd1211cb8eb7db3c180eed55e8b7cbe33ed59bc380403e5` |

## Limits / disposition

Accept this evidence **as a bound actual failed run with complete retained outer-cleanup receipts**, not Core acceptance. The historical **20 PASS / 27 FAIL** result stays separate and unchanged; the new result is **45 PASS / 2 FAIL**. Native05 remains **UNQUALIFIED**; **D05 PARTIAL / D06 unreviewed**, W03/native/full qualification and release boundaries remain unchanged.

Any follow-up must first identify the relevant pool receipt/state/worker failure under the bound runtime. This review does not justify an assertion waiver, larger timeout, unchanged rerun, public publication or release; operations and acceptance decisions remain with the primary.
