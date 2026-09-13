# W03 lease-dispatch creator — inert Linux01 preparation

2026-09-13 UTC. **TOOLING AUTHORSHIP ONLY; NOT INDEPENDENT APPROVAL OR ADMISSION.**
Only this private directory is authored. No executable derivative, source freeze,
checkpoint, request, CI deployment or result is supplied. The primary owns those
later decisions, resource ownership and notifications. `selection.json` is proposal
data, **not** a profile consumable by the historical runners unchanged.

## Current disposition

- Primary applied F1's sole correction: `internal class PoolLeaseDispatchCreatorIntegrationTest`.
  Test SHA256 `8ffac7e6c44fd2cd6503b0b1fd9d00ed70efa45e2bed8880f4b1f042b03790a9`;
  receipt `review/working/app-29-lease-dispatch-creator-visibility-correction-01/receipt.json`,
  SHA256 `80ada48647b1a0689b393db81cf9808934805be75e217835366bf3028edc5579`.
  This is **UNCOMPILED / UNEXECUTED**, not a replacement for future source inventory.
- Primary decided not to add an injected retained-creator/absent-tail regression now.
  Conservative retention before tail registration is source-traced only; the eight
  registered-tail rows must not be credited as that missing runtime case. No new
  allocation-failure harness or extra case is proposed.
- The focused class's lazy `PgLifecycleDatabaseFixture` starts real Testcontainers
  PostgreSQL even for its MODEL-labelled tests. **None of the17 is proposed locally.**
  The reported VPS limitation is no Docker/PostgreSQL executable/socket, as recorded
  in the prior PG preparation and reiterated by primary; no host probe was performed.

## Smallest local batch: normal compilation and statics, no tests

Reuse **unchanged** `review/working/run_app29_integrated_driver_validation_linux_v3.py`
(the Linux03 donor, SHA256 `bec0d6b5ebf63a68fc9d93aab0dca9dff828c9136baeda7066dd02af85e372cf`)
with future frozen task args:

```text
testClasses ktlintCheck detekt --continue
```

`testClasses` retains normal main/test Kotlin compilation and resource processing;
it does not execute JUnit. Run the configured aggregate script/main/test Ktlint and
normal configured Detekt, without formatter, baseline, rule or source-set edits.
Do not use `test`, `check`, `clean build`, compile skips or narrowed source roots.
Normal scope includes **all current** `src/main/kotlin`, `src/test/kotlin`, resources
and configured Gradle-script/static inputs, not only these changed files:

| Relative to the persistence package | Changed-path scope, not a freeze |
|---|---|
| `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/` | `GuardedDataSource.kt`, `LeaseJdbcFacade.kt`, `PersistenceJdbcGuardCall.kt`, `PersistenceJdbcGuardProtocol.kt`, `PersistenceJdbcLease.kt`, **new** `PersistenceJdbcLeaseInvocation.kt`, `PersistenceJdbcPoolTransfer.kt`, `PersistenceLeaseCompletion.kt`, `PersistenceProducerEpoch.kt`, `PhysicalJdbcDescendants.kt`, `PoolLifecycle.kt`, `PoolLifecycleFrames.kt` |
| `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/` | `PgLifecycleDatabaseProbe.kt`, `PgLifecycleDatabaseProbeProcess.kt`, `PgLifecycleDatabaseRecipe.kt`, **new** `OwnedPoolLeaseCreatorPendingProbe.kt`, **new** `PoolLeaseDispatchCreatorIntegrationTest.kt` |

No rerun of Linux03's56 successful tests or PG1 is included. Linux03's narrowly
approved Detekt reuse for a former two-test-file correction does **not** cover this
production delta. Require fresh configured static reports and actual main/test
compilation; local `test_evidence` should be `NOT_REQUESTED`, not PASS17 or PASS56.

Keep the existing isolated Java21/Gradle wrapper, one worker, in-process Kotlin,
2GiB heap/512MiB metaspace, no build/configuration cache, verified18 W01 source-engine
inputs and W01 init. Propose explicit offline mode; a missing dependency requires
primary disposition, not an automatic network retry. W01 classpath logging is a
Test dependency, so no new runtime/classpath receipt is inferred from testClasses.

The donor already accepts these tasks and owns the shared
`.kira-validation/backend-linux/batch.lock`, immediate owned stop, five natural
absence barriers, capture-before-delete, scoped output cleanup, final stop and
source/dependency postflight. Reuse its ownership helper and required tooling pins;
do not acquire the lock, probe processes or execute even a dry-run now. Future
admission must still check resources and reconcile prior ownership before launch.

## One later private hosted PG job: focused17 plus the unchanged failed method

`selection.json` lists nine ordinary methods and eight enum invocations of one
parameterized method. Together with the unchanged prior failed OwnershipIT method,
this is **11 method filters /23 task-argv elements /18 intended invocations**, not
18 independently filterable methods. Parameter values are source identities, not
observed CLI selection or XML evidence. No other former PG21 method is selected.

Use the existing ordinary-connected-PG01 private Linux Actions donor:

| Donor | SHA256 |
|---|---|
| `review/working/app-29-ordinary-connected-pg-carrier-01/ci/app29-gate-b.py` | `30b30d4907f6e5be366b0a0ef527686136b1ddb5fa8acef9d3830cdc8e937d88` |
| same directory `.github/workflows/app29-gate-b.yml` | `20d4f52e799bc291e51333fe45a9f2215d32884692f34578091d6924ee56bb85` |
| same directory `profile/profile.json` | `2cf80540dccd11b5b1088a36244a3c7ab68d8b6050a32008d921862265fa0438` |
| same directory `profile/profile.init.gradle` | `edbe0440d247e66c5a7c8efc17de347e7f077c0eca49b10fbd719ba4b2ce2172` |

These are actual final donor bytes, not their earlier author-handoff pins. Do not
edit or dispatch them. The smallest later derivative needs only these adaptations:

1. New namespace/profile/run paths and genuine new source/transport pins. Preserve
   PG01's complete478-source map, ccdbb28f checkpoint and all older stages as history;
   add the reviewed creator delta as a **new** stage. Do not require its changed
   bytes to equal the old current-source map, simply replace counts, reuse the old
   bundle, or publish private ancestry. A future clean private child checkpoint,
   bounded complete singleton bundle and real preflight remain primary work.
2. Separate the11 declaration filters from18 expected invocations in controller,
   profile and init. CLI and programmatic include sets must agree. The old
   `method + '()'` derivation and `exactMethods.size() == expected_test_count` are
   wrong for the parameterized method. Preserve raw XML names and compare exactly
   nine no-arg creator methods, eight distinct `(method, mode)` rows, and the one
   unchanged OwnershipIT method. Bind the ordinary Gradle/JUnit signature/index/
   argument spelling during the small derivative's review; do not guess a passing
   XML result, accept count-only evidence, add a provider exporter, or invent a
   new harness. Missing/duplicate/extra/failing/error/skipped cases cannot pass.
3. Two XML suites remain, but counts become17/1 and effective-classpath count18.
   Compare sorted actual and expected filenames. Update source-inventory/profile
   bindings and scope strings consistently. Keep PG14 scalar diagnostics explicitly
   `NOT_APPLICABLE`/zero; neither selected class sets `shutdownDiagnosticCase`.
4. Keep **two PostgreSQL17.6-alpine + one Ryuk0.12.0**, not one database: each selected
   PER_CLASS/SAME_THREAD class owns its own lazy fixture/AfterAll close. Mixed pools
   reuse their passed database. The eight existing negative child JVMs connect to
   the first class's fixture, creating no extra containers. Preserve the localhost
   prerequisite, one512MiB Test worker/forkEvery0, explicit JUnit parallel=false,
   normal full main/test compilation and the existing pinned driver/checker overlay.
   The child classpath still uses the selected driver and pinned stock Hikari6.3.3;
   no child provider or fixture substitution is proposed.

Reuse the existing owned-child controller, container custody/create/destroy/session/
image guards, raw capture and four drains/11 output-absence obligations. Preserve
25min job/1200s controller,120s preflight/900s validation/180s cleanup,8GiB free floor,
8MiB bundle bound and existing heaps. These are inherited ceilings, not a prediction
that the new batch fits. No timeout extension, silent skip, retry-until-green or
forced-cleanup PASS. NORMAL_ABSENT is not graceful PostgreSQL shutdown or zero-kill
proof. Keep private-repository/read-only-token/exact-checkout/pinned-action guards,
Ubuntu24.04/Temurin21, shared workflow concurrency with cancellation disabled, and
always-retained private reports. Reuse the PG01 launch/collection lock discipline
on the **same local heavy lock**; no concurrent local batch while its hosted run is
unreconciled. No live request or collector is authored here.

## Future inventory is additive; nothing is frozen here

Reuse unchanged `review/working/freeze_app29_integrated_driver_v3.py`, SHA256
`e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`.
Keep all348 development07 seed **keys** from manifest SHA256
`3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`, every retained
PG01 source member, and all current changed/new members, with fresh actual byte
hashes/snapshot subjects/diff and inherited reviewed removal/provenance pins. No
seed removal, old-byte substitution, focused-test-only inventory, or historical
manifest rewrite. Final source/snapshot counts must be measured, not copied from
478/211 or inferred as already frozen from the17-path review. The current review
and F1 correction are inputs, not the final source identity.

Primary first needs independent review of this authored preparation, then a real
local-selection freeze/admission. Any compile/static correction changes the bytes
to review. A later hosted selection must bind the actual final source and its own
exact task args/transport/admission using the same existing inventory machinery.
All those bindings remain null; this packet does not issue a preflight receipt.

## Evidence limits and exact review accounting

Linux03 stays historical PASS56 with normal compile/Ktlint and only its stated
Detekt reuse; PG1 stays historical PASS1. **PG01 stays20 PASS/1 FAIL**, including
required owned-pool teardown. Its close-executor actor/queue mechanism remains
unmeasured: a missing creator route found in source is not proof of that mechanism.
The unchanged failed method retains the real failed-native-commit discriminator,
UNKNOWN/refund assertions and original OwnedCutPool teardown/budgets.

New first-worker tests inject MODEL failures around real Hikari; they are not stock
PG commit-failure evidence. ClientInfo is MODEL private-field substitution, not
stock-PG getter proof; the declared-stream case observes conversion after the held
finally. Negative rows require live RETAINED/EXIT, exact exit23 and healthy joined
cleanup while the positive oracle rejects that exit. **PROCESS_ONLY product_end=false
never proves product disposal.** Native05/full47/consumer/opaque/liveness/W03/full-P3,
new-backend-data/installation recovery and production remain open; W06 excluded.

`inputs.sha256` names the exact external files used as byte/context references;
it is not a new source inventory or independent preservation audit. Source reading
for this preparation focused on the test declarations/fixture/negative-child lane,
unchanged failed method/OwnedCutPool teardown, build/static configuration, v3
inventory collection/validation/CLI, v3 local task/capture/cleanup path and PG01
selection/source-stage/classpath/container/XML/cleanup path. Historical reports
were read as reports, not re-executed or reapproved. The v4 local runner was also
read during discovery, but is **not** the selected Linux03 donor.

Only passive file/Git-status/text/hash inspection and the four new private files
`README.md`, `selection.json`, `inputs.sha256`, `SHA256SUMS` occurred. No helper or
runner import/execution, syntax checker, inventory preflight/freezer, build/test/
Gradle/JVM, network/acquisition, process/service/lease/lock action, Git mutation,
CI action, product/test edit or delegation occurred. No candidate approval or
verification PASS is claimed. Files are0600 in a0700 directory.
