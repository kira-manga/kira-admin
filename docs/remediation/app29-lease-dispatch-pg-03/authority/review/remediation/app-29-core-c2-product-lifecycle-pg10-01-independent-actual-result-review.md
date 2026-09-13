# PG10-01 independent actual-result review

2026-09-12 — private, nonauthor, artifact-only review by `backend_05_history_hosted_review`.

**ACCEPT the bounded exact-ten hosted diagnostic result and retained cleanup evidence.**
This is not overall candidate, static, full47, consumer, native, W03 or App29 acceptance.
No candidate/helper execution, Git, build/test/checker, service, network, rerun, source/ref/control
change or repeated controller/preflight audit was performed for this actual-result review.
The requested GPT-6-Astra/max reviewer configuration is not independently runtime-attested.

## Identity and custody

Evidence root: `review/working/app-29-core-c2-product-lifecycle-pg10-launch-01/` (`L`);
`A = L/artifact/`.

- Retained metadata consistently identifies run **34691665288**, attempt **1**, successful
  `diagnostics` job **103547878637**, artifact **10296464635** named
  `app29-core-c2-product-lifecycle-pg10-01-34691665288-1`.
- Source: `1c91f0c2d1a4d797e83a0e33b871b417ebcfaae1`;
  carrier: `67e11edb4b8a8f40e0752339ceed63d06a1c1a3b`.
- Admission binds adopted-review SHA-256
  `3ef02afe6ba535aed17349948958409fdb7669f5b88c14e58be0b5769f3ec048`.
  Replacing the saved request's sole `authorized: false` with `true`, in memory only,
  reproduces admission/launch request SHA-256
  `b44e501172be7960b58ccff72f548e790de5a6929c47251e16af4bd54ec21f16`.
  Source/carrier and original 25-minute/1200/120/900/180-second budgets agree;
  receipts record one attempt, no prior matching active run and no public backend push.
- Independently rehashed all **54 extracted regular files / 1,986,786 bytes**, exactly matching
  collection sizes/hashes, with no links or extras. Controller inventories match all **53**
  retained files excluding `result.json`, plus the overlapping **3** captured evidence files.
- Original ZIP: **224,742 bytes**, advertised/recorded SHA-256
  `707197b81677f6c759db7f0569e6f73570d48b7bd789204677cca81b6489e49f`.
  API metadata and collection agree. The primary records verification and deletion; the ZIP is
  absent, so **I could not independently rehash the original ZIP**. Extracted-file verification
  is independent; ZIP authentication remains retained receipt evidence, not a fresh download check.

Key independently rehashed anchors:

| File, relative to L | SHA-256 |
| --- | --- |
| `collection.json` | `18462802afbb57d630f3fb8b6ebb87b1825bd8942da3cc4502765ec6fc7381a1` |
| `artifact/result.json` | `f0543607fb687e762cd26a67ec91d9ed9f4ee87e023a5c65379157a136e930cc` |
| `artifact/test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest.xml` | `038a0164161dbb676743283341cdcaea159f3fdc2e7f7ea34566159dfbe87612` |
| `artifact/reports/core-c2-product-lifecycle-pg10-01/effective-classpath.txt` | `da47a9f36d05ad760d4b5afffd1b953275b7189a0fb0bcc19179087f81214d3b` |
| `artifact/reports/core-c2-product-lifecycle-pg10-01/class-load-2565.txt` | `e2062374d01352528ed0f58faa584a09176804b0c29c3d0255e1434df6ab28ad` |

## Source, normal compilation and actual class origins

Before/after raw tracked-name lists and source-hash maps contain the same **851** unique paths;
all **466** frozen source hashes match, and the inherited removed source is absent. Source
bindings agree before/after: 348 seed, 199 snapshots, 425 authority files and 21 core sources.
Raw commit objects independently reproduce the recorded chain
`1c91f0c2 -> eb8fed8b -> 989a8c07 -> 926927ab -> 49da0919 -> 3d839130`.
Before/after status is clean; head/branch and preserved 208,275-byte private bundle agree.

The raw Gradle log records normal `compileKotlin`, `compileTestKotlin`, `testClasses` and `test`,
**BUILD SUCCESSFUL in 4m36s; 6 actionable tasks, 6 executed**. Final 21 task arguments match
the pinned PG10 profile; normal wrapper/strict verification/in-process compiler and explicit
Temurin 21.0.12.1+1-LTS toolchain are recorded. This hosted run downloaded dependencies;
it was **not an offline run**. JDK hashes are remote receipt evidence, not locally rehashed host
binaries. Controller elapsed time is 299.020283065 seconds.

The effective classpath contains 186 entries: exactly one PG-bearing entry (512 PG classes,
one PG service), the accepted Native05 JAR SHA-256
`50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`,
and one checker-bearing entry (385 classes), SHA-256
`857658c8bdcbff794949a8d9922f88d63ee3751c203c7cd7d21ea97f9e745288`.
Stock `org.postgresql:postgresql:42.7.12` is explicitly excluded with its accepted hash.
The sole worker class-load log observes `org.postgresql.Driver` and `PgConnection` from that
Native05 JAR, the selected test from this run's normal Kotlin test output, and
`PersistenceJdbcLease`, `GuardedDataSource`, `PoolLifecycle`, `PoolActorCustody` from its normal
main output. This is actual selected-class origin evidence, **not consumer-loader or JAR
qualification**; consumer status is `NOT_EVALUATED / OUTSIDE_PG10_VALIDATION`.

## Exact XML10 and original diagnostic samples

Raw XML contains exactly ten distinct testcase identities in
`me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest`.
The exact set matches pinned profile `expected_tests`, selectors and controller identities/outcomes
(accounting only for the ordinary terminal `()` XML display suffix): RETURN seven, original
failed post-consent tail, ordinary consented tail, and exact-sample/adjacent-budget discriminator.
There are **10 PASS / 0 FAIL / 0 ERROR / 0 SKIP**, no extra/duplicate testcase or hidden failure,
error or skipped child. Suite timestamp is 11:45:18.421Z; duration 10.808 seconds.

Exactly four original `OWNED_CUT_SHUTDOWN_DIAGNOSTIC` lines occur in raw XML stdout: each
case's BEFORE_SHUTDOWN and AFTER_SHUTDOWN. All are `CAPTURED`, with no missing, duplicate,
unavailable or observation-failed row; the raw lines and parsed fields match the controller.

| Case | Budget ms before -> after | actor_retained | close_pool_size | close_completed_tasks |
| --- | --- | --- | --- | --- |
| RETURN_SAMPLE | 9999 -> 9964 | 2 -> 3 | 0 -> 0 | 0 -> 1 |
| FAILED_POST_CONSENT_TAIL | 9999 -> 9986 | 3 -> 3 | 1 -> 0 | 1 -> 1 |

For both cases: `invocation_result NOT_RETURNED -> RETURNED`, `first_close NOT_INVOKED -> RETURNED`,
`close_shutdown/close_terminated false -> true`. Throughout all four samples,
`observation=NOT_OBSERVED`, `actor_factory_sealed=false`, `actor_fault=BOOKKEEPING_FAILED`,
capacity=64; constructing, retired, future-lease entries, active operations, close queue and
close active count are zero. **These are non-atomic diagnostic scalars, not completion,
causality, repair, opaque-eviction or consumer proof.**

## Owned cleanup and unchanged limits

All 46 recorded command leaders have distinct PIDs and `NORMAL / actual_exit=0`. Four process
barriers contain the exact cumulative 21/44/45/46 leaders; all report empty remaining/active/
adopted/TERM/KILL sets and no errors. Both Gradle stop logs report no daemons running.
All **11** owned output paths (backend 5, private output 3, private home 3) have attempted,
complete, absent receipts with no skip. Final children/containers/outputs absence, capture,
input preservation and retained-inventory completion are true; cancellation is false.

Nine raw Docker events identify exactly one owned PostgreSQL17.6-alpine and one Ryuk0.12.0
container in the same Testcontainers session; both are destroyed. Initial/final inventories
are empty, polling resolves to empty, and the owned-container receipt has no remainder.
**Important: PostgreSQL has a raw `kill signal=9` and `die exitCode=137` before destruction.**
No controller `docker kill/rm/stop` command appears, and controller process force-cleanup sets
are empty. Thus `NORMAL_ABSENT` supports controller-unforced final absence, **not absence of
an infrastructure kill or graceful PostgreSQL shutdown**. Remote cleanup is supported by
retained receipts, not an independent live filesystem/process inspection.

The earlier Linux static result remains **FAIL** (ktlint main66/test61/script0; detekt41
weighted), despite its separate exact38 test pass. Historical full47 remains **45/47**.
Run **34678157417** remains **0 PASS / 2 FAIL; cleanup FAIL; containers UNKNOWN;
outputs_absent=false; six private directories retained**; this changed-source result does
not rewrite that history. Native05 remains **UNQUALIFIED**, D05 **PARTIAL / not import-ready**,
D06 **unreviewed/unexecuted**; native/full/W03/App29 qualification is unchanged. MODEL and
direct-boundary evidence does not establish opaque real-eviction hard-fault/liveness or zero
internal physical attempts. No broader qualification or historical repair is granted.
