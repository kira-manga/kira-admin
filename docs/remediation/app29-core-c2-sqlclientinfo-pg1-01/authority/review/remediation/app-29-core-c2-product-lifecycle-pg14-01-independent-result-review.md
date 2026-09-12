# CoreC2 PG14 hosted01 — independent actual-result review

2026-09-12 UTC — Web03, independent reviewer, not the source/carrier author or
runtime operator. This review used the retained local evidence only.

## Disposition

**ACCEPT the focused PG14 result on private Backend6db944, with the limitations
below.** The raw XML independently establishes exactly14 ordinary selected
methods PASS, zero failures/errors/skips. Source/admission bindings, raw capture,
owned-command/process/container receipts and output cleanup agree with the
reviewed carrier. No new cleanup-control defect was found within that envelope.

**Not graceful PostgreSQL shutdown or zero-kill proof:** the CURRENT PG14 Docker
journal records PostgreSQL signal9, exit137, then destruction. Controller-unforced
final absence satisfies the existing gate; it must not be renamed graceful stop.
No W03/App29/full47/Native05/consumer/provider qualification follows from this run.
Primary alone adopts this independent disposition; this report authorizes no rerun,
source change, dispatch, release or public push of private ancestry.

## Exact run and evidence roots

- Run34701415662, attempt1; private `kira-manga/kira-admin`, branch
  `remediation/app-29-backend-complaints`.
- Carrier `d4c6289df3f611f8efe467a4e5a19c2f6600d48c`.
- Backend `6db944871c1584bd6a1f28263e8010cadd766fab`.
- One completed `diagnostics` job103573736100, all recorded steps successful;
  job15:10:21–15:15:51 UTC. Controller318.575246731s, below1200s.
- Artifact10300293714,
  `app29-core-c2-product-lifecycle-pg14-01-34701415662-1`, retention3days.
- Run URL: https://github.com/kira-manga/kira-admin/actions/runs/34701415662

Path aliases below are exact workspace-relative roots:

- **H** = `review/working/app-29-core-c2-product-lifecycle-pg14-hosted-01/`
- **A** = `review/working/app-29-core-c2-product-lifecycle-pg14-admission-01/`
- **P** = `review/working/app-29-core-c2-product-lifecycle-pg14-preparation-01/`
- **F** = `review/working/app-29-w03-integrated-driver-core-c2-product-lifecycle-pg14-01/`
- **D** = `kira-admin/docs/remediation/app29-core-c2-product-lifecycle-pg14-01/`

### Primary binding and collection hashes

| Exact path (using aliases above) | SHA256 |
| --- | --- |
| `H/artifact.zip` | `1a9e60f9a1896ccc5a08b3ac1506921e2f9d6931d5530a13b67b663faec51258` |
| `H/artifacts.json` | `3545524943b46e6eee8f607655bf00eae0ff2460e2616aa16a06e21f36b0bead` |
| `H/run.json` | `685b4d9e9e39dfb108c5daba7daa48feca12db90e2faff720670493f3fd3f805` |
| `H/job.log` | `5566c9afc826926b192e1923d691b55f483e70349bbf9a2bcabab51e89ef8db1` |
| `H/collection.json` | `b5a2e129d004f0963a2f715e3a7b36f2933c5853099d590818bdab22ae1375be` |
| `P/SEAL.sha256` | `846a81ded067851f620d80a4531845ee68923f004a2329e9018cd5c6bfa8dce2` |
| `P/SHA256SUMS` | `7389a601e8622a2d972f0d5a8a61e83a730229f4ef56c99f69681e13bc776af9` |
| `P/carrier.patch` | `16e46e7f4615db69d367369f50215cbea0a0e7186fcd68e6383d330f94fb2e06` |
| `P/profile/profile.json` | `36c3637229efbe08186014f4c60684aa0569430b26bae9d13f8b811917e82225` |
| `P/profile/profile.init.gradle` | `61fb92e47baa8dcabcd6a7521e01872984e196d16cfd643776f3a50b25a81964` |
| `P/ci/app29-gate-b.py` | `7fce9fae743a4d235350d2c93610142fc7a0177f2b7d7e44031b56b8315f0576` |
| `P/.github/workflows/app29-gate-b.yml` | `790377568f065d1e2f64bad1a796a3d17f4a32cea224204adda25465c5d3a328` |
| `P/ci/app29-gate-b.request.json` | `2934820e9714dff3bd2fc1cdf013b611db03cabb238b2ef6676456e982a837fb` |
| `review/remediation/app-29-core-c2-product-lifecycle-pg14-preparation-01-independent-review.md` | `ca56b68ac2a30d5c62f367e4ad50fd87592b70111f0e6a78c6760be84b274d21` |
| `A/primary-source-preparation-disposition.json` | `314cd72ce2b89c155298f5dbbd1aacac40e554684933ccebe383e1c58372741a` |
| `A/primary-admission.json` | `cf1ed646ff9b2f579a46dd7f9f45295a5f0526291ff2fbec71e2deb9c08a8288` |
| `A/freeze-adoption.json` | `9acb348581a640ebef70e96ad82a06aa916a228cbee47e29752f33ac6ded68e0` |
| `A/freeze-command.json` | `0578a682a72ab1f426855edc122ab9711b79d3f1c31803e8d29397b0d287e105` |
| `A/preflight-command.json` | `80a2d321ed7c585734b9d696c882f23959406fcb21c6213b5def7b78e2755c5b` |
| `A/transport.json` | `8fc03deb25543d4c24e72bf9fe4e6217166db325ddf4430585ff9a7a22efb453` |
| `A/launch.json` | `0757c6bbd357300770a03a53cc6e2feb7ebf5a3468470687d3aafb606c366ae6` |
| `A/local-layout-probe-failure.json` | `e8d30931537a1d8c1bd04bca9af88f0b41830b33c1ef19db01065203ae290b3a` |
| `A/deployed-binding-check.json` | `32dfd06f567f9ca0416666ab08c14d77a6e295e4f7759768bcfa9585967323bf` |
| `A/emit-target-command.json` | `00539454a751fb3cbb918f2a3c5d7320e2cc84d4b3f96ce0f875c769f2fa133d` |
| `A/repository-privacy.json` | `657d702a09872e66960a444d0612673f34c1e312762027bb6e792889cc5c9453` |
| `A/other-requests-before.json` | `95338fab709d76546149c81b929aaf79a872608efdf969b8229ec64688ede6d9` |
| `F/manifest.json` | `fc979ee558b53d18337b0a5104f2b574e0bde2147a52f5ac96585a779c56a121` |
| `F/hosted-local-preflight.json` | `3b6e6541725e1cd8569aa04d34782120ad3e6439e70c9eafaf728cf3b0083a1a` |
| `D/checkpoint.json` | `b977d7836997e0da2866ee440dad5140452a108731f6d740b68c43032b3fe5bb` |
| `kira-admin/ci/app29-gate-b.request.json` | `14c5b4a48388e3f9318e8b2742a2ef21e7b072173bbe5f1df0c0ba76b75aabd7` |

The retained artifact metadata and job upload log both advertise the ZIP digest
`1a9e60f9a1896ccc5a08b3ac1506921e2f9d6931d5530a13b67b663faec51258`;
local bytes independently match. ZIP227795 bytes expands to exactly56 unique
regular-file members /2,009,899 bytes. No duplicate, absolute, traversal, encrypted
or link/special entry was found. Every archived member exactly matches its retained
`H/raw/` file; there are no extra extracted files. No re-extraction was performed.

All55 `retained_file_hashes` entries match their actual bytes/sizes and exactly
cover raw files except `result.json`; all three `captured_file_hashes` entries
(XML, class-load log and effective-classpath) match as well. A complete raw file
hash readback appears at the end of this report. GitHub success alone was not used
as the test or cleanup oracle.

## Preparation, admission and source reconciliation

The unchanged sealed PG14 preparation and prior independent source review were
rehashed. The deployed carrier/workflow/profile/init/helper match their accepted
pins. Final request SHA14c5b4a4 differs from the sealed unauthorized draft only in
`authorized: false -> true` and replacing64 zero checkpoint digits with the actual
deployed checkpoint SHA `b977d7836997e0da2866ee440dad5140452a108731f6d740b68c43032b3fe5bb`.
The separate primary one-attempt admission binds that request, the reviewed seal,
14 selected tests and unchanged25min/1200s/120s/900s/180s limits.

Fresh v3 freeze SHA
`fc979ee558b53d18337b0a5104f2b574e0bde2147a52f5ac96585a779c56a121`
was created15:03:18 UTC after the documented Backend11 integration decision.
Its local/origin integration aliases both bind
`b2324508dd7c3c11d894e4c9a815f5e30387369a`; private source remains clean6db944.
The current local aliases still matched during review. This is distinct from the
historical residual-static Git context and from the source transport receipt.

Independent passive reconciliation verified:

-466 source hashes,348 seed paths,199 snapshot subjects/copies,102 historical
 inputs,143 approved inputs and10 active tools; every source/snapshot hash matches;
- unchanged diagnostics8-replacement historical stage -> exact PG10 map -> exact19
 structural replacements -> PG14 map;447 PG10 source hashes remain unchanged;
- every PG10 approved-input and old-tooling provenance pair remains retained;
 original5 active tools plus reviewed new5, with all29 exact task argv elements;
- actual freezer/preflight argv and success receipt match the pinned manifest and
 task list; preflight stderr is empty. The unchanged freezer is
 `e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`;
- all447 transported authority entries /14,168,584 bytes match both workspace
 originals and deployed copies, including all history, snapshots, tools and diff;
-455 bound carrier files (447 authority plus request/checkpoint/five tools/bundle)
 agree with immutable carrier Git blobs. Its454 changed paths are within the
 approved carrier/payload scope; all15 other request-file hashes are unchanged;
- hosted before/after complete851 tracked-file inventories are byte-identical and
 their851 hashes independently match the exact private Backend Git tree, not just
 each other. The466 frozen-source map is an exact subset; both status logs are empty.

Raw initial checkout is clean detached public prerequisite
`3d839130c807f6a0a9b1c896c1c6cca4b41c4538`. Raw bundle verification/import and
before/after commit objects bind the exact source bundle217809 bytes,
SHA `2506c18cc5e40f089cc1176a65a79d449ff02b13f4c08e0719c24d359e9882da`,
with singleton private ref and complete SHA1-v2 ancestry:

```
6db944871c1584bd6a1f28263e8010cadd766fab
-> 1c91f0c2d1a4d797e83a0e33b871b417ebcfaae1
-> eb8fed8b6b620a0c7448c223bf49c1683f8eaadc
-> 989a8c07b90d956a5f2484f223be41b5d99a8a3c
-> 926927ab805a2a3b78957862f3b744d0fe399ac5
-> 49da0919d9ec3091cb7bb041009dc9bd5f3e090f
-> 3d839130c807f6a0a9b1c896c1c6cca4b41c4538
```

The raw commit-object bytes independently reproduce their Git IDs. Hosted
source/bundle bindings before and after agree. No merge, rebase or extra private
child was substituted. The transport source receipt
`review/working/app-29-core-c2-post-structural-private-checkpoint-01/checkpoint.json`
remains SHA `6e7cfcdb0598531092750a122b3cae985fe06f629455ee030773ba2242992556`;
it was not misused as the deployed acceptance checkpoint.

The retained local layout inspection failure is not concealed: the first primary
read-only binding inspection used hosted `ADMIN.parent/backend` where local source
is `kira-backend`; the subsequent local-only mapping inspection succeeded without
carrier edits. Neither inspection was a PG execution or retry. The genuine local
v3 preflight and actual hosted binding receipts are separate evidence. This reviewer
did not import/run either checker or carrier.

## Exact14 observed test outcomes

One ordinary XML suite:
`me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest`.
Suite14 tests /0 failures /0 errors /0 skipped,11.42s. No duplicate/extra identity,
parameterized expansion, failure/error/skipped element or XML entity/DTD was found.
Raw testcase identities exactly equal the profile14; independently reconstructed
outcomes equal `result.json`. Suite stderr is empty.

The table is in the approved selector order, **not** a claim that JUnit executed
in that order. Display names are exactly the following method names plus `()`.

| # | Exact method | Outcome | XML seconds |
| --- | --- | --- | --- |
| 1 | `throwing original RETURN override leaves F G T free and retires its exact source without a second return` | PASS | 9.242 |
| 2 | `blocked overriding final RETURN sample spends the same real allowance and cannot commit after expiry` | PASS | 1.06 |
| 3 | `actual RETURN interruption defeats a false override while outer actor custody survives held restoration` | PASS | 0.078 |
| 4 | `throwing RETURN interrupt restoration cannot undo retirement or erase its actor failure` | PASS | 0.104 |
| 5 | `RETURN override InterruptedException publishes source failure before an overriding self interrupt can block` | PASS | 0.061 |
| 6 | `RETURN InterruptedException adaptation throwing another InterruptedException never retries restoration after actor end` | PASS | 0.072 |
| 7 | `RETURN InterruptedException adaptation throwing Error preserves that error without a late restoration callback` | PASS | 0.071 |
| 8 | `failed post consent real Hikari tail seals actor admission but cannot retire the successor epoch` | PASS | 0.08 |
| 9 | `consented real Hikari recycle tail retains no successor eviction or abort authority` | PASS | 0.186 |
| 10 | `exact retirement sample result preserves its Throwable and does not absorb adjacent budget failure` | PASS | 0.081 |
| 11 | `throwing overriding original checkout sample cannot orphan its captured handle or future return right` | PASS | 0.094 |
| 12 | `genuine throwing RETURN TL entry restores the authentic lineage and revokes only its still unused future right` | PASS | 0.056 |
| 13 | `real post commit Blob work cannot silently commit through Hikari auto commit reset` | PASS | 0.144 |
| 14 | `real commit failure retains unknown outcome and refuses reset before native auto commit` | PASS | 0.067 |

Normal main/all-test compilation completed as dependencies of the single `test`
task. Gradle8.14.5 reports BUILD SUCCESSFUL in4m52s, six actionable tasks/six
executed: compileKotlin, processResources, compileTestKotlin,
processTestResources, w01SourceClasspathEvidence and test. Java compilation is
NO-SOURCE; jar/Jacoco tasks are skipped as planned. No new static batch or38-unit
rerun occurred. Cold image/download activity is retained; no prewarm or retry is
credited. The first method's9.242s includes initial fixture startup; per-test XML
timing is not a replacement for the source's per-operation budget assertions.

### Changed-risk coverage supported, and its boundaries

The selection advisory remains
`review/remediation/app-29-core-c2-post-structural-pg-selection-advisory.md`, SHA
`d934676c715da7aaef8e008c264e0b5e5e7cb30e4a909103878f521a44bc4f64`.
The frozen test source is SHA
`b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322`.
The guard residual source is SHA
`f45890e53648b8e4abb30fdc9ff6250de6927413a9f510cc672babef1b43462c`.

-1–7 rerun the real RETURN caller/sample/budget, restoration/Throwable identity,
 actor-retention and actual end/retirement negative controls through the changed
 phase/helper structure. No weakened timeout or assertion was introduced.
-8–9 exercise failed and ordinary consented old Hikari tail behavior versus the
 successor epoch/Entry: real successor SQL, no stale close/abort authority and
 both extracted final-close assertion arms.
-10 discriminates exact retirement-sample Throwable/count from expiry and adjacent
 budget failure on a real pool. It remains an internal-boundary discriminator,
 not an opaque native-eviction fault execution.
-11 adds actual runtime evidence for throwing checkout SAMPLE cleanup: withheld
 exposure, original failure, captured source retirement, entitlement cleanup and
 restored authentic lineage/counters on the extracted undelivered path.
-12 adds genuine failed RETURN TL entry: original REFUSED frame rather than a
 fabricated END, original injected failure, lineage restoration, one injection,
 unused future-right revocation, no lower transfer/Hikari close and duplicate-close
 identity/no new operation. It is not either process-only END-TL/core-last-count probe.
-13–14 execute both changed negative auto-commit guard branches: real post-commit
 Blob fastpath work stays pending and is rolled back rather than silently committed;
 a real deferred UNIQUE-constraint commit failure has SQLState23505 and UNKNOWN
 transaction outcome. Both assert refusal before native autoCommit becomes true.

These are current focused runtime checks after the19-path structural checkpoint,
not fresh runtime coverage for every method or every moved assertion in those19
files. The SQLClientInfo declaration/defaults/foreign-caller control remains in a
second PG-owning class and was not selected.

## Four required raw scalar rows — exact preservation

XML and result contain exactly the same four raw
`OWNED_CUT_SHUTDOWN_DIAGNOSTIC` rows, all CAPTURED, one per required case/phase.
No duplicate, missing, UNAVAILABLE or OBSERVATION_FAILED row is present.

| Case | Phase | Budget ms | Invocation / first_close | Actor retained | Close pool / active / completed | Close shutdown / terminated |
| --- | --- | --- | --- | --- | --- | --- |
| RETURN_SAMPLE | BEFORE_SHUTDOWN |9999| NOT_RETURNED / NOT_INVOKED |2|0 /0 /0|false /false|
| RETURN_SAMPLE | AFTER_SHUTDOWN |9962| RETURNED / RETURNED |3|0 /0 /1|true /true|
| FAILED_POST_CONSENT_TAIL | BEFORE_SHUTDOWN |9999| NOT_RETURNED / NOT_INVOKED |3|1 /1 /0|false /false|
| FAILED_POST_CONSENT_TAIL | AFTER_SHUTDOWN |9978| RETURNED / RETURNED |3|0 /0 /1|true /true|

All four also retain: observation=NOT_OBSERVED, actor_capacity=64,
actor_constructing=0, actor_retired=0, actor_factory_sealed=false,
actor_fault=BOOKKEEPING_FAILED, future_lease_entries=0, active_operations=0 and
close_queue_size=0. These fault labels/counter values are not discarded because
the tests pass. They are best-effort **non-atomic** observations, not a causal
repair, zero-retention, actor-liveness or consumer proof. In particular, neither
`observation=NOT_OBSERVED` nor the retained counts can be relabelled a completed
native-observation witness.

## Runtime/classpath identity

- Ubuntu24.04.5, runner2.337.0, image ubuntu-24.04/20260907.300.1. Pinned action
 SHAs and contents:read/metadata:read appear in the retained job log. No actual
 platform error is recorded; action Node24/deprecation and Gradle9 compatibility
 warnings remain non-failing maintenance context, not hidden test failures.
- Actual canonical JDK is `/usr/lib/jvm/temurin-21-jdk-amd64`, Eclipse Adoptium
 Temurin21.0.12.1+1, runtime21.0.12.1+1-LTS. JDK release/version output and worker
 launcher agree; the release text hashes to its recorded SHA. The setup action's
 tool-cache label21.0.12+1 is not substituted for this actual captured identity.
- Effective classpath186 unique entries =180 JAR entries plus six allowed
 compilation/resource directories. Exact PG14 profile/count/source-inventory
 metadata and `expected_witnesses=[]` agree.
- Exactly one PostgreSQL class/service supplier: Native05 candidate
 SHA `50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`,
512 indexed PG classes and one driver-service entry. The exact Checker JAR is
 SHA `857658c8bdcbff794949a8d9922f88d63ee3751c203c7cd7d21ea97f9e745288`,
385 indexed classes; no duplicate checker artifact was present. Recorded stock
42.7.12 runtime SHA31fbf6f0 is removed, not a second supplier.
- The class-load log records actual selected test/product classes from the normal
 test/main compilation directories and PG Driver/PgConnection/PgBlob from that
 candidate JAR; there is no competing file-backed PostgreSQL origin. Dynamic
 lambda records name their originating PG classes, not additional JAR suppliers.
- Commanded Gradle heap2GiB/512MiB metaspace, one worker, no parallel/build/
 configuration cache and planned512MiB test JVM/no-agent flags remain unchanged.
 `java.io.tmpdir`/user.home are the private run paths. This is context capture,
 not complete independent remeasurement of the worker VM or every dependency byte.
- W01 source-engine/source-contract JAR hashes agree between classpath and all
 six raw compile/test classpath-evidence rows. Strict dependency-verification
 without verification metadata is still not transitive dependency-byte proof.

No `worker-runtime.txt` positive-consumer witness is expected or present. Its
absence is not a missing required capture in this14-method profile. `consumer`
remains NOT_EVALUATED; candidate_qualification remains UNQUALIFIED.

## Ownership and cleanup: supported narrow acceptance

All48 recorded owned commands have distinct recorded leaders, actual_exit0 and
NORMAL outcomes. The final owner receipt's PID set exactly covers those48
commands. No nonzero exit, cancellation or retained failure is hidden behind the
XML result.

| Drain boundary | Recorded leaders | Remaining / active Popen / adopted | TERM / KILL | Outcome |
| --- | --- | --- | --- | --- |
| after-immediate-stop |22|empty /empty /empty|empty /empty|NORMAL_ABSENT|
| before-file-cleanup |46|empty /empty /empty|empty /empty|NORMAL_ABSENT|
| after-final-stop |47|empty /empty /empty|empty /empty|NORMAL_ABSENT|
| before-home-cleanup |48|empty /empty /empty|empty /empty|NORMAL_ABSENT|

Both actual `./gradlew --stop` logs say `No Gradle daemons are running.` The
reviewed source's protected stop/drain/container-check -> capture/postflight ->
drain -> file cleanup -> final stop/drains/census -> home cleanup order is
consistent with the commands and receipts. The final job log's generic orphan
cleanup contains no listed orphan termination; that generic line is not used
instead of the owned drain receipts.

Docker evidence contains exactly two created identities and their destroy events:

- PostgreSQL17.6-alpine:
 `7fcc8dea6b9e548e4bf224a04afe5aa822d64898de1d7ab6f04835c7f4a4c04c`;
- Ryuk0.12.0:
 `731d7aa893f6081cdb90597be7a2e8b601fd51f4bbf529ee2152e66718d1d768`.

Both are Testcontainers1.21.4-owned; the PG session and Ryuk name agree on
`9021c7a9-1571-479f-8f1a-efb54dc82bee`. Resolved image digests are
`postgres@sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94`
and
`testcontainers/ryuk@sha256:dd3f023a6ed7015b3f95a49ccd65a2daf0c56e681422c12952b19a810dfa6298`.
The nine raw events are ordered and agree with owned-containers.json.

Initial census is empty. Normal polls0–8 contain only the known Ryuk ID; poll9,
after-cleanup and final census are empty. No controller `docker rm` command or
forced-container flag appears. Nevertheless, the raw CURRENT PostgreSQL sequence
is **kill(signal9) -> die(exit137) -> destroy**; Ryuk dies0 then is destroyed.
Thus NORMAL_ABSENT means eventual controller-unforced absence under the accepted
create/destroy gate, **not** normal PostgreSQL exit or a zero-SIGKILL shutdown.
This is a retained limitation, not evidence that the narrower gate was weakened.

All11 owned-output rows show attempted/completed cleanup, no skip reason and
measured absence: five Backend outputs/caches and six private run directories.
Capture_complete, inputs_preserved, retained_inventory_complete,
final_children_absent, final_containers_absent and outputs_absent are true;
cancelled=false and failures=[]. Captured XML/classpath/log bytes were retained
before deletion and match the final artifact. No cleanup action was performed by
this reviewer, and no post-job live census is implied.

The XML also records14 `PG_LIFECYCLE_ROOT_CLEANUP` rows (actors12,
TRACKED_LOCAL_ENDED/REAL_COMPOSITION/all_terminated=true), nine owned-caller scope
exit rows and two factory scope exit rows, all with all_terminated=true. They
support these ordinary fixtures' tracked teardown, not unselected process-only
or opaque native liveness branches.

## Retained open gates and historical evidence

PG10 run34691665288 remains accepted10 on1c91 only, including its original
kill9/die137; no graceful-stop claim is made for either that run or PG14.
Historical hosted02 run34672394928 remains45/47 and diagnostics01 run34678157417
remains0/2, cleanupFAIL/containersUNKNOWN/outputs_absent=false and six retained
private directories. Those historical maps are unchanged in this result/authority.
Prior38 unit results and residual compile/static acceptance remain separate
carried evidence, not newly executed results or an aggregate blanket pass.

Still outside this run: SQLClientInfo declaration/defaults/foreign-caller coverage;
descriptor/original-provider/consumer-provenance witnesses; process-only acquisition
END-TL/core-last-count probes; foreign native-stream cancellation; opaque native
hard-fault/real-eviction/first-close/liveness branches; full47. Native05 remains
UNQUALIFIED, D05 PARTIAL/not import-ready, D06 unreviewed/unexecuted;
W03/App29/native/full qualification remains open. No unchanged-success rerun is
needed to support the narrowly accepted evidence here.

## Review actions and preservation

Only local source/text/JSON/XML/ZIP/hash/path/Git-object inspection and independent
in-memory data comparisons were performed. No candidate/carrier/helper/freezer
import or evaluation, static/syntax checker, build/test, download/network query,
CI action, source/ref/index edit, process/resource manipulation or cleanup occurred.
The sole write is this separate mode0600 report, read back after creation.
Existing preparation and artifacts were unchanged; Backend/Admin worktrees were
clean at final inspection, at6db944 andd4c6289 respectively. Primary owns final
adoption, notifications and any later action.

## Complete raw evidence hash readback

Paths below are relative to **H/raw/**. Every file was byte-compared with the
retained ZIP; result.json also pins the55 other files through its retained map.

| File | Bytes | SHA256 |
| --- | --- | --- |
| `after-backend-branch.log` | 38 | `7b48f4083ede426131b1eff936e7c0d0297d2281a7221979a6ae135706be019b` |
| `after-backend-commit.log` | 344 | `cbe394112a049b6a605d8b0196ba48f94f9fdb4629bf434d15ac38e140ccca34` |
| `after-backend-sha.log` | 41 | `c9f95b1446021b325d88c0d81bba0ea5ab261b6cce601d6f38816880785d2c99` |
| `after-core-baseline-commit.log` | 639 | `98cdf85b08d699721c6350fa51e484a662d4ab3dd0ffc7112d8c3b9a56e2b516` |
| `after-diagnostic-parent-commit.log` | 352 | `cf767d2023a74d90e99c620b5495ce90d60c83cb103786fa6e149816f4f2abc2` |
| `after-previous-private-parent-commit.log` | 361 | `0116d0a9fa46cb8dc2a1125ec38db5c1d9d75b85e9bff64e4ddc53e054ace7ab` |
| `after-private-parent-commit.log` | 373 | `78f53743490218d3e856c68dffaae952360f89a7585c7679e87ca1cc1ffeb2e2` |
| `after-product-lifecycle-parent-commit.log` | 368 | `90b0ed3b9c7a6b61c61998c320086226d64ee593a6c69abb9a97394f24abab00` |
| `after-source-hashes.json` | 133767 | `d87999b554b6fccdb213baf6725f5929ee4481035d06a93bfcec8df373afac8c` |
| `after-status.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `after-tracked.log` | 71641 | `39a0c2f85d8622f12a83d5df9d8c5f57b681b2b132beea2e9d69a53532e6bfc1` |
| `before-backend-branch.log` | 38 | `7b48f4083ede426131b1eff936e7c0d0297d2281a7221979a6ae135706be019b` |
| `before-backend-commit.log` | 344 | `cbe394112a049b6a605d8b0196ba48f94f9fdb4629bf434d15ac38e140ccca34` |
| `before-backend-sha.log` | 41 | `c9f95b1446021b325d88c0d81bba0ea5ab261b6cce601d6f38816880785d2c99` |
| `before-core-baseline-commit.log` | 639 | `98cdf85b08d699721c6350fa51e484a662d4ab3dd0ffc7112d8c3b9a56e2b516` |
| `before-diagnostic-parent-commit.log` | 352 | `cf767d2023a74d90e99c620b5495ce90d60c83cb103786fa6e149816f4f2abc2` |
| `before-previous-private-parent-commit.log` | 361 | `0116d0a9fa46cb8dc2a1125ec38db5c1d9d75b85e9bff64e4ddc53e054ace7ab` |
| `before-private-parent-commit.log` | 373 | `78f53743490218d3e856c68dffaae952360f89a7585c7679e87ca1cc1ffeb2e2` |
| `before-product-lifecycle-parent-commit.log` | 368 | `90b0ed3b9c7a6b61c61998c320086226d64ee593a6c69abb9a97394f24abab00` |
| `before-source-hashes.json` | 133767 | `d87999b554b6fccdb213baf6725f5929ee4481035d06a93bfcec8df373afac8c` |
| `before-status.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `before-tracked.log` | 71641 | `39a0c2f85d8622f12a83d5df9d8c5f57b681b2b132beea2e9d69a53532e6bfc1` |
| `carrier-sha.log` | 41 | `6f2b38d6e16d247c63f5896b75b69b843c3a098e28adaf7e2a3d7eb27dbf61db` |
| `container-events.log` | 5056 | `a7bf615155092a8731249ddc7922659f82b11896f07ae2deda027c925bf012ea` |
| `containers-after-cleanup.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `containers-before.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `containers-final.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `containers-normal-0.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-1.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-2.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-3.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-4.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-5.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-6.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-7.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-8.log` | 65 | `d18ee805b406665c561818df2c720c696ddb8d67ba5da850155a1252dbc72aaf` |
| `containers-normal-9.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `docker-version.log` | 792 | `a634037cf6df509bb12f1496d80dd258857175c09727b4a4cfe8167cf1951716` |
| `gradle-stop-final.log` | 31 | `9bb9c19238f3fdde3213f2be84912b0c7e87b3e2295ec372ec245deab200d46d` |
| `gradle-stop-immediate.log` | 31 | `9bb9c19238f3fdde3213f2be84912b0c7e87b3e2295ec372ec245deab200d46d` |
| `gradle-test.log` | 3682 | `4b8914669795790378f340fcc717cd2ad9ede5c8d2a2483740b1f39ea64c3410` |
| `image-0.log` | 208 | `42f9580f26e131dd7eaaea13e73f7b73e182f2eb870be56499f9cf697d911a42` |
| `image-1.log` | 225 | `2fcef07881f4f4e9564c412f22f516b80bbaaf19b5735c750d25961945316f40` |
| `initial-backend-branch.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `initial-backend-sha.log` | 41 | `f8f42cc7bc7d592bf99e042b3aa9953662f86136ed64204a86e469f1804c3fdb` |
| `initial-backend-status.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `jdk-version.log` | 2196 | `540a6583cc97a590636d0f810847387e5ab8aeb3269fba48e1c4522ccafdf91d` |
| `jdk.json` | 2023 | `f95c67557fd2ae701f15f089ab0b7a6bdffef78c432a699e6411a45b24c30589` |
| `owned-containers.json` | 924 | `c026540e36cd27d0f3a11f363e0058e2c3c8dee4b8e3479a7f348b217a3d4c14` |
| `reports/core-c2-product-lifecycle-pg14-01/class-load-2561.txt` | 1398984 | `ae3ec852acbdb2dcc693f0ba4e33f78474d3049df2347aa2f18e778539d50dd6` |
| `reports/core-c2-product-lifecycle-pg14-01/effective-classpath.txt` | 88251 | `18badd05f3fce4fd446313e441024031aeca356b0b94ebb06d93ed97f58d6a0c` |
| `result.json` | 68140 | `45384ff17fcd5dd28296aab8bd27f9f2ea9d8fadbfc26d3f3650261548ed2533` |
| `source-bundle-checkout.log` | 171 | `0cb3d81d86240f35738133180b56b184a7f5af12cd850cd9cfd2096230b17326` |
| `source-bundle-fetch.log` | 230 | `8090d5de3d5417db02b6d7cb5491dfd81b82151cb4d5e8cc8ac74229ccc49f34` |
| `source-bundle-verify.log` | 367 | `f326375529f1f81f0a223dd759659a36402e1da9859c4cd0273a8c5c48653041` |
| `test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest.xml` | 22073 | `e522fd0b91191c9d62f6243522d651534506829ab48f0cd37dfd1d3555335c6e` |
