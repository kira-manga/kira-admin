# Core C2 diagnostics01 — independent actual-result and cleanup review

2026-09-12 UTC · `/root/backend_05_history_hosted_review` · **PRIVATE / NONAUTHOR**

**FAIL: 0 PASS / 2 FAIL / 0 ERROR / 0 SKIP.** The exact-two run produced valid
diagnostic captures, not passing tests. Final child/container absence is supported,
but the earlier container gate failed and six private output directories remained.
Neither `diagnostics=RECORDED` nor eventual absence repairs the failed run.

## Actual identity and evidence integrity

Packet `L = review/working/app-29-core-c2-diagnostics-launch-01/`; artifact `A = L/artifact/`.

- Run **34678157417**, attempt1 artifact **10292971308**; carrier
  `9c802bb5eefcd8af23f7c30cb662a2eb6c7d3dec`, Backend
  `eb8fed8b6b620a0c7448c223bf49c1683f8eaadc` agree across retained launch,
  artifact metadata, request and runtime records. `run.json` is an earlier
  in-progress observation, not a final workflow-conclusion receipt.
- Independently checked all **48 files / 1,943,459 bytes**: all47 retained hashes
  and byte counts, all3 captured-payload hashes, and exact file inventory match.
  Collection/metadata agree on ZIP SHA
  `23266ce388791799c667e63f4c9cc3e1e171f9e3e656217ab52d6dc914f9eb52`
  and221,689 bytes. The temporary ZIP is gone; its digest is receipt evidence,
  not a new ZIP rehash or remote verification by this reviewer.
- All373 deployed authority hashes match. Both851-path tracked inventories and
  source-hash maps are identical; clean-status logs are empty. All466 frozen
  source pins match those maps;348 seed paths and199 snapshots remain bound.
  Before/after commit-log bytes independently hash to the recorded four commits
  and preserve the chain `eb8fed8b → 989a8c07 → 926927ab → 49da0919 → 3d839130`.
- The accepted test source is exactly
  `09ff840b9b3c4532c33ce24c09a60a2b0479084b480ed29f6d21478751e78f99`.
  Request, checkpoint, strict prerequisite-limited bundle, deployed controller,
  workflow, profile/init and helper pins match the reviewed preparation. No source
  or tool drift was found. The one actual Gradle argv ends with the exact five
  `test --tests method --tests method` elements in the frozen profile/manifest.

## Observed tests and all six shutdown captures

Exactly one XML suite, `PersistencePgOwnedCutIntegrationTest`, contains these two
unique methods under `me.manga.kira.backend.common.infrastructure.persistence`:

| Diagnostic label | Exact XML method | Result / seconds |
|---|---|---|
| RETURN_SAMPLE | `throwing original RETURN override leaves F G T free and retires its exact source without a second return()` | FAIL /27.875 |
| FAILED_POST_CONSENT_TAIL | `failed post consent real Hikari tail seals actor admission but cannot retire the successor epoch()` | FAIL /18.143 |

Both failure elements report `PersistenceBoundaryException: TIME_BUDGET_EXHAUSTED`
at `OwnedCutPool.close:1282` → `awaitLifecycleFact:86`, while waiting for the
shutdown receipt to stop being PENDING. The latter helper has its own8,000ms
allowance. The final expected-observation/actor-retirement assertions were not
reached; their success must not be inferred from method-body progress.

Read the complete XML, including **every** shutdown capture. All six raw lines
and all parsed fields exactly match `result.json`, one CAPTURED record for each
case/phase, no UNAVAILABLE or duplicate record. In the table, SAMPLE and TAIL
denote the labels above; N/R/I mean NOT_OBSERVED/RETURNED/NOT_INVOKED respectively.

| Case | Phase | Budget ms | Invocation / first close | Observation | Close queue | Shutdown |
|---|---|---:|---|---|---:|---|
| SAMPLE | BEFORE_SHUTDOWN |9999| NOT_RETURNED / I | N |0|false|
| SAMPLE | AFTER_SHUTDOWN |0| R / R | N |1|true|
| SAMPLE | OBSERVATION_FAILED |0| R / R | PENDING |1|true|
| TAIL | BEFORE_SHUTDOWN |9999| NOT_RETURNED / I | N |1|false|
| TAIL | AFTER_SHUTDOWN |0| R / R | N |1|true|
| TAIL | OBSERVATION_FAILED |0| R / R | PENDING |1|true|

Every row additionally has: actor capacity64, retained2, constructing0, retired0,
factory sealed=true, fault=BOOKKEEPING_FAILED; future lease entries0 and active
operations0; close pool size0, active count0, completed tasks0, terminated=false.
These account for all18 scalar fields, in addition to case/phase/status.

**What this genuinely localizes:** each Hikari shutdown logs a roughly10-second
wait and `Timed-out waiting for close connection executor to shutdown`, followed
by `Shutdown completed`. The invocation/first-close calls returned, but the
executor remained nonterminated with queued work at both later samples and the
receipt remained PENDING. The retained shutdown budget was already exhausted
before the fixture's separate observation wait failed. Frozen
`PoolLifecycle.kt:425–430` corroborates a blocking condition: zero remaining
shutdown budget returns PENDING before `actors.observeTerminations()`.

This is not evidence that retained2 means two still-live threads, nor that the
BOOKKEEPING_FAILED fault first arose during shutdown: it is present in both
BEFORE records. The scalar reads are non-atomic and do not identify queued task
identity, every intervening state, or the complete cause of missing executor
progress. No deadline extension, bookkeeping reset, queue discard or other fix
is inferred. Backend03's separate causal investigation is not replaced here.

The raw log shows main/test Kotlin compilation and resource tasks reaching the
test task, then `2 tests completed, 2 failed`, Gradle exit1. No statics, packaging
or full-suite success follows. Retained context reports Temurin21.0.12.1,
Kotlin2.1.21 and stock Hikari6.3.3; classpath/class-load evidence identifies the
pinned Native05 JAR, but consumer witnesses were unselected and consumer status
is NOT_EVALUATED. Native qualification is not supplied by loading that JAR.

## Cleanup: concrete carrier mismatch, not retroactive acceptance

**Additional carrier failure:** reviewed controller3922 still requires THREE
created containers — two PostgreSQL fixtures and one Ryuk — at
`ci/app29-gate-b.py:504–506`. The exact-two methods belong to one PER_CLASS test
instance with one lazy database fixture (`PersistencePgOwnedCutIntegrationTest:50–60`).
The complete journal contains **two** creates: one `postgres:17.6-alpine` and one
`testcontainers/ryuk:0.12.0`, with matching destroys. Its cardinality cannot pass
that retained full-selection guard. This newly demonstrated preparation defect
is separate from the two product/fixture failures; the prior source-only review
did not catch it.

The guard explains the `containers/ValueError` before owned-container/image
receipts or the successful cleanup return. No such receipts or resolved-image
identity logs were retained. The controller correctly preserves UNKNOWN rather
than silently accepting a different inventory.

- All four process drains report NORMAL_ABSENT, empty remaining/active lists and
  no TERM/KILL actions. Both Gradle stops exit0 and report no running daemons.
  The same Gradle leader2378/exit1 recurs in all four nonzero-child failure rows;
  these are sticky observations of one failed command, not four new leaked jobs.
- Initial container census is empty. Normal censuses0–8 retain only Ryuk;
  normal9 and final census are empty. The journal records PostgreSQL signal9,
  exit137 and destruction; Ryuk exits0 and is destroyed. Final absence is
  supported, **not graceful PostgreSQL/product disposal**. No controller
  `docker rm` command occurred.
- All11 scoped deletion attempts were skipped with
  `CONTAINER_CLEANUP_NOT_ABSENT`. Five Backend-local output paths were already
  absent; private `w01`, `project-cache`, `kotlin-cache`, `gradle`, `tmp` and `home`
  were explicitly present. Thus `outputs_absent=false` is actual residual-output
  evidence, not merely a missing PASS label.
- Capture and input preservation succeeded, but the six failure rows remain,
  `containers=UNKNOWN`, and overall FAIL is correct. Final absence must not
  retroactively authorize those earlier skipped deletions. Hosted runner teardown
  is not an explicit cleanup receipt.

## Recomputed pins

Paths in the first rows are relative to `L` above.

| Artifact | SHA-256 |
|---|---|
| `artifact/result.json` | `14d1f192614853639b1990f17323863683bd0fab32a4a62e9cd3f2c6810d8559` |
| `artifact/test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest.xml` | `3d049dab1afbd0a4246a2b5c8ba1d4a1253a5e6544a9c2d133e5bebbd922169f` |
| `artifact/gradle-test.log` | `fe3e886ea77c8c15ff2c22dcba32ebba8a70cad96a0a8015b7726f86d9985225` |
| `artifact/container-events.log` | `ba44289e787a74ccd6da1a6c53d374a2f2df64d81b5743b45238c63f28d5259e` |
| `artifact/before-source-hashes.json` and `after-source-hashes.json` | `7caa9622576dab7e05c0a168d913ca5bc04dad6c1398b807a47d5ff126548ea4` |
| `artifact/reports/core-c2-diagnostics-01/effective-classpath.txt` | `569cca9cdecccde5fc26c6caec3f3e7c40242ee81e90b69ac5a32d9d6b6ea75f` |
| `artifact/reports/core-c2-diagnostics-01/class-load-2543.txt` | `bdf50278c1627f1461ac95295cbfcda0df86f61a39d0dfa01a8b1e9fc450fb6e` |
| `authorized-request.json` | `10789f102f964ef8fd73fbf1c094cf688976a619acf10ac3c3b79c597148eade` |
| `collection.json` | `ef753d751e71a18d8cbee22093758c7f75b914c839cae45719f64015b2bf95f2` |
| `artifact-metadata.json` | `ff94fc672328cf14db11cbed076c9c7bcee1ecc8e6e613522f860a6fd66d601c` |

Deployed `kira-admin/docs/remediation/app29-core-c2-diagnostics-01/checkpoint.json`:
`341f756f968c63dccab3aa9bf8451f6c6ae4b223302ef4a5dba2d61c7bc4c7de`.
Frozen `review/working/app-29-w03-integrated-driver-core-c2-diagnostics-01/manifest.json`:
`2e6ba4a28bdc628d42937c3ed0f7f435c835b61d4e6f73702b50e6a2edd85511`.
Controller: `39224054c4bd61bbf665568c982302c12f84fa5df3e293c568f338a9cbeae9ca`.

Historical hosted02 **45 PASS/2 FAIL** remains separate, not a current47 result.
Native05 remains **UNQUALIFIED**, D05 **PARTIAL**, D06 unreviewed; W03/full/native
qualification stays open. Product disposition, the demonstrated carrier mismatch,
any source/tool correction and any future one-attempt authorization remain
primary decisions. No guessed fix or rerun is proposed.

Workspace/Backend guidance and the failed-run custody/resource-cleanup agreement
were read. This reviewer performed only local bounded read/hash/JSON/XML/text
analysis and wrote this new private report: **tests observed, none executed**.
No source/history edit, candidate/helper import, Git command, build, checker,
service, dependency acquisition, CI/network action, cleanup or rerun occurred.
All reviewer commands are finished; no child workers were launched.
