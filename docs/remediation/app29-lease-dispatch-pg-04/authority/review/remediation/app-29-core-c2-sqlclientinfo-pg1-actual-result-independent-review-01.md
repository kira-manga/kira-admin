# CoreC2 SQLClientInfo PG1 — independent actual-result review01

2026-09-12T18:22:35.071192+00:00. Reviewer: Web03 (`/root/web_03_media_validation`), independent
of carrier preparation and launch. **ACCEPT_FOCUSED_SQLCLIENTINFO_PG1_ONLY** is the
independent recommendation; primary acceptance remains separate. No blocking
actual-result defect found within this admitted scope.

## Run, authority and exact evidence

- Run `34709458222`, attempt1, private carrier
  `02ebe6024d151e082c1f685cb58280000f81e4a0`.
- URL: https://github.com/kira-manga/kira-admin/actions/runs/34709458222
- Backend: `6db944871c1584bd6a1f28263e8010cadd766fab`; no new product source delta.
- Raw root: `review/working/app-29-core-c2-sqlclientinfo-pg1-admission-01/launch-03/artifacts/`.
- Reuses source-only review `239b36d38051b768b7c587ee0da8d99880e8a0744e159a5d01b6ac1e02af3bed`
  and preparation seal `8ab15f7e7292cee545350553572955941f9c74db00c40ff104d3b3de45130a9f`;
  no repeated helper/source audit.

| Evidence | SHA256 |
| --- | --- |
| Raw `result.json` | `5d640b6fc1b39a521577374e1e47186368f860b49e3d1bb55da98ab61a478fe1` |
| Raw `test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest.xml` | `5ebe3fd65ccc2c1b57116f4be6c63bb3c235794890bf7beb0c03645e9a740185` |
| Launch03 `collection.json` | `af165183b5fedf7548079009165ebc4642d1173fb7c59f28a0129980830f9fe5` |
| Fresh PG1 `manifest.json` | `2cde6562f651eb1240ba6fcc7e13d87400a993d10fa4d8b681acf2316cf2f99c` |
| Fresh `hosted-local-preflight.json` | `3b6e6541725e1cd8569aa04d34782120ad3e6439e70c9eafaf728cf3b0083a1a` |
| Deployed PG1 `checkpoint.json` | `80400d3c1f8afc8bd410e256a171d4dafdc79f3acc2a94b49f2889cdd5caca09` |
| Final authorized `kira-admin/ci/app29-gate-b.request.json` | `1d99235e7cb6abc289a44e58c9d378b9a0a237660878e78c9770316a255338b4` |
| Raw `container-events.log` | `53e502f5f5d11ea41c316038abb7a59fe2133657bc28feccf4057447a08958fb` |
| Raw `reports/core-c2-sqlclientinfo-pg1-01/effective-classpath.txt` | `46c9e26eb46d331ae63ca4fcae7d0f07b16dc17044e52411f5f986a709955e07` |
| Raw `jdk.json` | `f95c67557fd2ae701f15f089ab0b7a6bdffef78c432a699e6411a45b24c30589` |

The compact input receipt `app-29-core-c2-sqlclientinfo-pg1-actual-result-independent-review-01.inputs.sha256` pins 42 direct files,
SHA256 `9ddbbbc42182a16d9a0f9327f6101a72860137efb08f19d5005a76bed12f6040`. Its pinned collection/transport manifests enumerate the
complete56 raw files and474 authority files; the compact receipt does not duplicate
those complete maps. Every collected file's hash/size, all55 result-retained entries
(excluding the self-referential result), and all3 pre-deletion capture entries
matched independent local readback. Total expanded raw bytes: **1,918,599**.

The upload log and API metadata agree on artifact `10302444907`, name
`app29-core-c2-sqlclientinfo-pg1-01-34709458222-1`,220471 compressed bytes and ZIP digest
`2ac9f43117b91917a88deee373a3565f6e4bbad1710638eaaf540cdc1ba07745`.
No ZIP file was supplied locally: that compressed digest is corroborated metadata,
**not** an independently recomputed archive hash. Extracted-member hashes were checked.

## Exact observed one-case result

One XML suite and one ordinary testcase, with **PASS1 / FAIL0 / ERROR0 / SKIP0**:

`me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest.real lease preserves Properties client info defaults and declared stale and foreign failure shapes()`

XML timestamp `2026-09-12T17:56:57.846Z`, case duration11.875s. No additional XML
suite, duplicate identity or skipped testcase. The single Gradle validation command
ends with exactly the approved3 argv (`test`, `--tests`, the literal selector without
parentheses); it exited0. Normal compilation dependencies ran, not a separate
compile/static batch or an unchanged38-unit/PG14 rerun.

Profile, raw XML, classpath and result agree on the one-case selection. Result
`fixed_scalar_capture=NOT_APPLICABLE`, scope is explicitly0 expected records,
`raw_shutdown_diagnostics=[]`, coverage is empty, and XML contains no fixed scalar
rows. This is nonapplicability, not vacuous CAPTURED or a waiver of original PG14's
four required rows. Raw ordinary fixture output records real pool shutdown and
`PG_LIFECYCLE_ROOT_CLEANUP result=TRACKED_LOCAL_ENDED ... proof=REAL_COMPOSITION`.
That output is not proof of graceful PostgreSQL-container shutdown.

## Source and runtime-context binding

- Final request differs from the sealed unauthorized draft only in authorization
  and the actual new checkpoint hash. Exact five deployed tool pins match the
  approved preparation/shared helper. Primary admission binds this request,
  checkpoint, source review and fresh manifest.
- Independently rehashed **all474 transported authority files and their original
  counterparts**, with exact path-set equality. Manifest:466 sources,199 fresh
  snapshot subjects,348 preserved seed paths,102 historical inputs,170 approved
  inputs and10 active tools. All original PG14 approved143/tooling10 provenance
  pairs remain included; original5 plus new5 remains the active-tool rule.
- All466 manifest source hashes match the raw before/after tracked maps. All851
  tracked hashes and inventories are unchanged before/after and equal the already
  accepted PG14 full tracked maps. All348 seed keys are retained; all199 new-path
  snapshots match their source hashes. The removed path remains absent from the
  tracked maps. Raw clean-status, branch, tip and six parent links agree. These are
  captured receipts cross-checked with accepted history, not a new live Git audit.
- Source bundle remains217809 bytes, SHA256
  `2506c18cc5e40f089cc1176a65a79d449ff02b13f4c08e0719c24d359e9882da`.
  Source/deployed Native05 and checker bytes match their approved pins. Native05:
  `50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`,1200036 bytes,
  **UNQUALIFIED**. Checker:
  `857658c8bdcbff794949a8d9922f88d63ee3751c203c7cd7d21ea97f9e745288`,241885 bytes.
- Captured Temurin21.0.12.1+1-LTS / `/usr/lib/jvm/temurin-21-jdk-amd64` agrees across
  JDK/version/classpath records. The186-entry classpath has one Native05 supplier
  (512 PostgreSQL classes, one service), one checker supplier (385 classes), no
  duplicate paths and no retained stock PostgreSQL supplier. Actual Driver and
  PgConnection class-load records use the bound Native05 JAR. Planned worker flags
  retain512MiB heap, disabled attach/dynamic agents and no forbidden loader override.
  This is context evidence, not consumer/JAR/JDK qualification or complete transitive
  dependency-byte proof; strict Gradle mode alone does not supply that proof.

## Actual cleanup evidence and limits

**Current PG1 PostgreSQL also has kill9/die137**, not merely historical PG14:

| Container | Image | Actual journal tail |
| --- | --- | --- |
| `d87ba53f44d5517522bea88bb2863d414eab1d23f7768d707b49e13fb4624ab4` | `postgres:17.6-alpine` | create, start, kill(signal9), die(exit137), destroy |
| `461ceaa990b90d8aa8a39dd9b51c78786ef0d965d32921afdaad6c203e450c5b` | `testcontainers/ryuk:0.12.0` | create, start, die(exit0), destroy |

Exactly2 created IDs and9 journal events; Testcontainers1.21.4 ownership/session
labels and owned-container inventory match. Initial census is empty. Normal polls0–8
contain only Ryuk; poll9, after-cleanup and final censuses are empty. Both IDs have
actual destroy events. `NORMAL_ABSENT` means controller-unforced final absence;
it is **not graceful shutdown or zero-kill evidence**.

All48 owned commands report actual_exit0/NORMAL. Four process drains are empty,
with no TERM/KILL/adopted/active/remaining entries or errors; the final drain accounts
for all48 command leaders. Both Gradle stops report no running daemon. All11 explicit
owned output paths record attempted, completed cleanup and absence with no skipped
reason. Capture/retained hashes independently match. Result failures are empty,
cancelled=false, inputs_preserved=true, final child/container absence=true; elapsed
358.269596882s. No contradictory raw cleanup, output or source record was found.
These are the admitted controller's scoped receipts, not a live global-host probe.

Non-blocking collection bookkeeping: `launch-03/lane-release.json` embeds the
initial `in_progress` run snapshot and stale old workflow name. It is not used as
final-run-state proof. Separately captured `run-final.json`, workflow upload and raw
collection bind the completed exact PG1 run. Local collector reaping/lock release
was reported by primary, not independently probed by this reviewer.

## Preserved unresolved gates

Only this named test's defaults-backed Properties/non-String fallback, foreign-thread
both-overload and stale Properties-overload assertions gain this one-case runtime
result. No stale String-overload or every-finally-failure claim. Prior accepted
PG14/PG10 and38 units remain separate; original45/47 and diagnostics0/2 cleanupFAIL,
UNKNOWN containers, outputs_absent=false and six retained-directory history remain
unchanged. Original PG14's four rows and kill9/die137 are not waived or repaired.

Native05/original-provider/consumer/full47, opaque real-eviction hard-fault,
native-finalizer/pin/compaction/liveness, P3/W03/App29 and full qualification remain
open. Preserve original D05/D06 artifacts and their reviewed/imported v2 successors;
do not restart them. No shipping enablement, public private-source push or issue
closure follows this recommendation.

Verification used passive local text/JSON/XML/hash/path comparisons only. No network,
Git, Docker/process probes, helper/carrier/freezer import/evaluation, checker/build/
test/rerun/dispatch, source edit, deletion or cleanup was performed. Only this private
receipt and its compact input manifest were created.
