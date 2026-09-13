# W03 connected ordinary phase — bounded correction handoff01

2026-09-13 UTC · `/root/w03_core_author_resume` · private0600.
**SOURCE AUTHORING ONLY / UNCOMPILED / UNEXECUTED.** This is a four-path correction
packet for independent review, not the primary's combined freeze, execution admission,
a test result, W03/P3 completion or production qualification.

Private authorized backend baseline: `6db944871c1584bd6a1f28263e8010cadd766fab`.
**Never publicly publish that ancestry or this private evidence.** No Git writes occurred.

## 1. Authority and preserved starting point

All following document paths are under workspace `review/remediation/`:

| Input | SHA-256 |
|---|---|
| `app-29-ordinary-phase-connected-correction-agreement-01.md` | `c363d521fe7fa8f97fa1d6b6957d9d1cb5c7ff8f4c97a24a00c7385ecba078ec` |
| `app-29-ordinary-phase-connected-ownership-independent-diff-01.md` | `6eab917006f67dbfa50143a683233e92f2d4ab100292ae386222b0b24d2b3a09` |
| `app-29-ordinary-phase-connected-regression-independent-diff-01.md` | `3ccfff09f4a9f1593e4867b7e019c1b912de4359382d0e94b32f6995763438ad` |
| `app-29-ordinary-phase-connected-source-handoff-02.md` | `ae011b05b5d0899274a2751daadedc79fb29f4ba247ead9dcdcd61ec11724919` |

Core02 at `review/working/app-29-ordinary-phase-connected-source-resume-02/` was
not rewritten. Its seal hash remains
`86fa8cebb700c34a758bc474d7f0b3a90c222c69e6b867a35ee0a85480a68767`.
Passive current hashes of its63 sealed members reproduce the original seal bytes.

**Primary follow-up disposition for L1:** during this correction the primary expressly
removed the synthetic quarantine/sentinel test request. Source review plus the later
affected compilation/statics is sufficient for this bounded diagnostic retention;
existing quarantine/custody gates stay open. No fabricated phase, outcome, permit or
sentinel was added, and no compilation/statics were executed by this author.

## 2. Exact corrected source

Paths below are relative to `kira-backend/`. **P/** is
`src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`;
**Q/** is its corresponding test directory.

| Path | Core02 before SHA-256 | Corrected SHA-256 |
|---|---|---|
| `P/GuardedJpaTransactionManager.kt` | `4b3513022676e442c9797d0fa83d8d5219134466d97744fb3461c2b3d4faf96a` | `551e6c9295566f522f55bcafba7d54b98314c8dc34b003c940277e3d81404f00` |
| `P/PersistencePhaseOwnership.kt` | `2d5ed320e3c63864362d90cc5784bec7da2998109975a1677d2abd41fe61f104` | `19d2e91e3358316c2a369fc62e09a566b0e14fc15bdaefb44310cd36d8a5e500` |
| `Q/OrdinarySourceGrantCleanupFixture.kt` | `4706962d0171bf4be9bab1aa49f3eb62a328acb40b4243602a18d4ba4c7f3b7c` | `4cea94d0f27384bd16ae00f8ea0dad4f446e890412f6f1506b95497028a7d461` |
| `Q/OrdinarySourceGrantCleanupOwnershipIT.kt` | `e58bca0fc1308e36fe51fef350f087fa172977838dfccee11d42147c0c92f69e` | `0a2e78581410bc91df644acee2110fd6993f0b746efd0c93ec6cda8034dbede5` |

No helper-file split or new repository source path was needed. All other17 core02
paths retain their exact bytes, including `PersistencePhaseContext.kt`
(`def1ebd792eafe08c2bc559270a7d281e238c298f7bca03f045f10cbcec5a878`).

### H1 — exact real EMF/resource association before admission or begin

The constructor now requires `EntityManagerFactoryInfo` with `dataSource ===` the
selected `GuardedDataSource` before creating the private delegate. Unknown metadata,
null metadata and foreign/same-endpoint substitutions refuse without a discovery
borrow. Metadata failures remain value-free. After Spring's unconditional autodetection,
the manager installs its own fixed `HibernateJpaDialect` and validates the effective
private EMF/DS/dialect identities. It does **not** reset the DS to conceal a foreign
factory. Factory-supplied dialect customization is not an accepted contract.

The same resource check runs before a phase permit and before scoped/unscoped
`getTransaction`. The delegate stays private; listener/customizer/nested restrictions
are unchanged. No Boot/alias/provider-switch integration was added.

One new test pairs a healthy, real same-endpoint foreign EMF with the selected guarded
pool after both real positives have run. Forwarded EM creation/begin observations and
actual acquisition observations are first calibrated, then asserted unchanged across
foreign, metadata-unknown and null-DS constructor refusals. Foreign observation uses
the existing independent reader, not another pool. Its positive performs a real begin,
query and rollback with explicit EM close in finally. Existing exact-EMF commit/join,
failed-real-begin and post-status lazy-materialization tests remain; both original fault
decorators still forward `EntityManagerFactoryInfo` and assert their intended fault.

### B1 — positive in-flight sleep witness, unchanged lifetime bound

The existing blocking test now starts an independent observer with its own connection
and prepared statement before the work clock starts. It receives only PID/backend-start/
accepted-at scalars and positively queries that exact backend in active `Timeout/PgSleep`.
It never executes or copies the business transaction. Observation is bounded; its own
finally closes the connection, and the test's finally stops/joins it.

The positive witness is asserted **outside** the expected-exception extent. Original
accepted-lease-to-disposition `<=3000ms`, old-session disappearance, restored row, actual
independent row-lock acquisition and exact receipt remain. No Future expiry, minimum
elapsed-time surrogate or timing relaxation was introduced.

### B2 — exact lower commit-failure discriminator

The real `pg_terminate_backend` fault remains in `beforeCommit`. A test-only observation
of the existing own-project instance ThreadLocal and driver `Invocation` now selects the
exact lower BUSINESS `commit` call/root. It records that call prepared with outcome NONE
before arm, then armed/unended with ordinary failure and UNKNOWN **while that same commit
is still current**, before any subsequent rollback. Preparation/arm failure, another
commit, observation error and mere final UNKNOWN cannot satisfy the assertions. Actual
core end and native armed/disarmed/ended fields are also required outside `assertThrows`.

This uses the retained owned-cut observation seam and the pinned closed dispatch order;
it does not assign an outcome, invoke a replacement commit, alter a driver/call/receipt
field or install a product fault switch. The observer delegates original TL storage and
is restored in finally. Independent session/row disposition and local refund remain
separate from UNKNOWN. This discriminator is source-authored, not runtime-confirmed.

### Combined afterCommit/interruption case, read caps, and L1

- One new real `afterCommit` callback throws `InterruptedException`. An independent
  reader checks durable deletion inside the reached callback before the throw; assertions
  after the executor require retained COMMITTED, exact receipt/quiescence/refund and the
  original caller's restored interrupt. The test clears the flag only in finally.
- Existing caps coverage now observes actual JDBC `networkTimeout` clipping. Existing
  same-PID/new-epoch successor coverage compares its actual read cap with the pre-phase
  value before and after stale old close. The offset-clock assertions remain MODEL-only.
- L1 preserves an existing bounded `PersistencePhaseException` after unused-entry cleanup
  succeeds. Unexpected entry failures remain value-free; unsuccessful unused-entry cleanup
  reports bounded CLEANUP_UNRESOLVED with `cleanupProven=false`, not a refund claim.
  The primary's narrowed L1 validation disposition is recorded above.
- Existing occupancy counters are **not** relabeled cumulative acquisition history. Only
  the new calibrated H1 observation records acquisition-frame publications for that case.

## 3. Authored inventory and verification limits

The source inventory is now **15 ownership methods +7 unchanged pure outcome methods
+6 unchanged peer methods**: 28 textual authored methods, **none compiled or run here**.
The original13 ownership methods remain; only the foreign-EMF and combined afterCommit
methods are added. `authored-method-inventory.txt` records current source function lines,
not JUnit discovery. Runtime feasibility remains for independent review and primary
validation: especially the lower-commit witness under the real remote fault, observer
scheduling within the existing3s ceiling, and actual same-session cap restoration.
There is no result-based justification to weaken those assertions if they fail later.

Only source/document reads, allowed read-only Git observations, four-path authoring,
passive byte copies/hashes/line inventories and this handoff were performed. No build,
compiler, project checker/helper/test/runner, service/container/worker, network/CI,
Git mutation/publication, driver/vendor edit, live wiring/schema edit or subagent launch
occurred. No historical freezer/checker was invoked.

## 4. Correction packet and preservation

**E/** = `review/working/app-29-ordinary-phase-connected-correction-01/`.
E contains the four exact before/after snapshots, the correction-only patch, input and
source pins, authored inventory and passive preservation observations. `SEAL.sha256`
binds E's files; the report/seal hashes accompany the handoff to the primary.

| E member | SHA-256 |
|---|---|
| `correction-after.sha256` | `b2d1a421f985cef91e438c30a199b7950a0ef474e097449a529e1ebb39557574` |
| `core02-to-correction.patch` | `d3c5aae0108aa17acfbf26b634bb1c103dcb5a6b2b6e05ff1041c7e75c725140` |
| `core02-unchanged-current.sha256` —17 paths, matches expected | `039eea206a74af34e0b720a9cd63be2f4bea6663b4107272fa8bc1c4ff4172eb` |
| `peer-current.sha256` —3 unchanged paths | `5d5b344c250bde1f0b4b9e5c96eafad7ed16d8a773151a099f032fc63d1f5215` |
| `membership-current.sha256` —478 present catalog paths | `442994e871afd895462c99f5281471ad5637ae340f98bce7a02a63e4d30ffb80` |
| `development07-seed-current.sha256` —348 present paths | `1da885305731b3c545658471b745e45cf425b608d86a04f9a43402953e446b07` |
| `authored-method-inventory.txt` | `b25603c3492bfa3d9b9fb6ced1e6dea3bbc3a751818198cc10b13f8653876faa` |
| `core02-sealed-members-current.sha256` —63 unchanged members | `86fa8cebb700c34a758bc474d7f0b3a90c222c69e6b867a35ee0a85480a68767` |

The full retained478-path digest delta contains only the four authorized paths. All348
development07 seed members remain present; seed-path inclusion has no missing member.
Prior seed-to-core02 changes were preserved, not declared restored to original seed
bytes. The inherited nonseed absence of `TransportBoundTestFixtures.kt` remains absent.
Current untracked source has no path outside the retained catalog. These are passive
membership observations, not a fresh combined-freeze validator or test count.

Peer bytes remain:
`SourceGrantCleanup.kt` `020a40ee44d38611bdaed358519472ebbb7e29a18eb58be411c184fa0086eaa0`;
`JdbcSourceGrantCleanupStore.kt` `3521657245fd5922718c21e703120bae9bac9664bdab331564170f53714ce689`;
`OrdinarySourceGrantCleanupIT.kt` `4c265dbc8e073896f395f5140be1ad96906bf89749a751d3452e144d67fdad31`.

Primary next reads the actual correction, requests the two independent bounded
re-reviews, then owns the complete348-seed/current/new freeze, selected affected
compilation/static/runtime admission and cleanup. No broader driver/pool audit is
requested. Production/UNKNOWN, Boot/customizers, W05 request expiry, operational sink,
full P3/native/opaque/liveness and live cleanup wiring remain OPEN. W06/history and
trackers were untouched; NEW backend/installation recovery remains required.
