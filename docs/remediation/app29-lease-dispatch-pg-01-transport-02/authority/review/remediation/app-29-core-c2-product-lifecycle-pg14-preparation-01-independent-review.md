# CoreC2 PG14 preparation01 — independent source-only review

2026-09-12 UTC — Web03, independent of Admin04's preparation.

## Disposition

**ACCEPT_SOURCE_ONLY for the exact sealed five-file derivative and inert handoff recipe.**
No material source-level defect or weakened selection, source-binding, resource,
cleanup or privacy gate was found. This accepts preparation bytes only: **not a
fresh v3 freeze, local preflight, deployed acceptance checkpoint, execution
admission, test result, native/consumer qualification or W03 acceptance.**

Primary alone dispositions this review and owns all subsequent actions. The
sealed request must remain unauthorized and immutable; it is not runnable
admission and must not be edited in place to launch.

## Reviewed identities and integrity

Packet: `review/working/app-29-core-c2-product-lifecycle-pg14-preparation-01/`.
All paths in the following table are packet-relative.

| Input | SHA256 |
| --- | --- |
| `SEAL.sha256` | `846a81ded067851f620d80a4531845ee68923f004a2329e9018cd5c6bfa8dce2` |
| `SHA256SUMS` | `7389a601e8622a2d972f0d5a8a61e83a730229f4ef56c99f69681e13bc776af9` |
| `packet.json` | `94d4f755a50bdaf064cc18ba7e6eea4ca97c7beaac3fc0999d78df388aab1588` |
| `carrier.patch` | `16e46e7f4615db69d367369f50215cbea0a0e7186fcd68e6383d330f94fb2e06` |
| `README.md` | `b570249c77ef8c58633f4898ed1f89a624286b5b0e373f0e4c37d5546324de11` |
| `recipe.json` | `1d899043472877bf6b6b76db84be3df25659814eae4a3b05386c598e1dc26cda` |
| `inputs.sha256` | `f563d6ebbec74c50f066c73b27adbcc2a25e8ba9a01221376925bf64e494ffa2` |

| Candidate | Accepted before SHA256 | Reviewed after SHA256 |
| --- | --- | --- |
| `ci/app29-gate-b.py` | `230140399aa9353ef6f3628c1c961aa1cda96f52bbfa5b97c8245fa9f2b3b301` | `7fce9fae743a4d235350d2c93610142fc7a0177f2b7d7e44031b56b8315f0576` |
| `.github/workflows/app29-gate-b.yml` | `7822bd6fb67d1916977520ceb5e77adf1949a2ae774ac5e9b8917a99e72da625` | `790377568f065d1e2f64bad1a796a3d17f4a32cea224204adda25465c5d3a328` |
| `ci/app29-gate-b.request.json` | `b44e501172be7960b58ccff72f548e790de5a6929c47251e16af4bd54ec21f16` | `2934820e9714dff3bd2fc1cdf013b611db03cabb238b2ef6676456e982a837fb` |
| `profile/profile.json` | `f721c8d972206b973b2d3aefa4246bbd2d768c66f6f2908c470b3f896526b339` | `36c3637229efbe08186014f4c60684aa0569430b26bae9d13f8b811917e82225` |
| `profile/profile.init.gradle` | `09742b6796f0fe3d65f2b172272ab8a697ea5a07dadad7298bed1c062ee61ada` | `61fb92e47baa8dcabcd6a7521e01872984e196d16cfd643776f3a50b25a81964` |

- Independently matched all17 sealed members and19 directly pinned external
  inputs. The exact inventory contains no extra files or links; packet files are
  mode0600 and directories0700. The seal matches the checksum list.
- All five before-images match their declared origins, including the live
  authorized PG10 request rather than its older preparation draft. Candidate and
  before byte sizes match `packet.json`.
- Reconstructed the entire five-file unified diff in memory from the actual
  before/after text; its bytes and hash exactly match `carrier.patch`. Read all
  changed hunks and their binding/lifecycle/selection context, not merely labels.
- The unchanged owner utility is
  `56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385`.
  Request, recipe and actual candidate deployment hashes agree for all five
  active additional tools.

## Selection and count binding

Authority: `review/remediation/app-29-core-c2-post-structural-pg-selection-advisory.md`,
SHA256 `d934676c715da7aaef8e008c264e0b5e5e7cb30e4a909103878f521a44bc4f64`.

The carrier `METHODS`/`TEST_COUNTS`/`TASKS`, profile `expected_tests`/count/class,
init exact-method count/uniqueness, request/profile hashes, recipe argv, XML
identity/count checks, classpath report count and PASS criterion all agree on
**14 ordinary tests in one existing class**, under the new PG14 identity. Run,
report and artifact paths are likewise PG14. No active PG10 count remains.

The first10 methods and first21 task argv elements exactly equal the accepted
PG10 profile, in unchanged order. Only these four methods are appended:

1. `throwing overriding original checkout sample cannot orphan its captured handle or future return right`
2. `genuine throwing RETURN TL entry restores the authentic lineage and revokes only its still unused future right`
3. `real post commit Blob work cannot silently commit through Hikari auto commit reset`
4. `real commit failure retains unknown outcome and refuses reset before native auto commit`

All14 names resolve textually exactly once to ordinary `@Test` declarations in
`me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest`.
Its PER_CLASS/SAME_THREAD lazy database fixture and AfterAll close are retained.
The profile/recipe have exactly29 task argv elements: one `test` plus14 literal
`--tests CLASS.method` pairs, without wildcards, backticks or parentheses.
Expected XML names add only `()`. Explicit init filters intersect CLI selection;
normal compilation is not narrowed. No second PG-owning class, SQLClientInfo
control, process-only probe, new harness or positive witness was introduced.

## Source ladder and private transport

The source receipt is
`review/working/app-29-core-c2-post-structural-private-checkpoint-01/checkpoint.json`,
SHA256 `6e7cfcdb0598531092750a122b3cae985fe06f629455ee030773ba2242992556`.
Its217809-byte bundle hashes to
`2506c18cc5e40f089cc1176a65a79d449ff02b13f4c08e0719c24d359e9882da`.
Independently inspected the singleton complete SHA1 v2 bundle header and verified
all19 Git delta paths and their before/after blob hashes. Actual single-parent
ancestry is:

```
6db944871c1584bd6a1f28263e8010cadd766fab
-> 1c91f0c2d1a4d797e83a0e33b871b417ebcfaae1
-> eb8fed8b6b620a0c7448c223bf49c1683f8eaadc
-> 989a8c07b90d956a5f2484f223be41b5d99a8a3c
-> 926927ab805a2a3b78957862f3b744d0fe399ac5
-> 49da0919d9ec3091cb7bb041009dc9bd5f3e090f
-> 3d839130c807f6a0a9b1c896c1c6cca4b41c4538
```

Carrier lines228–367 preserve the original diagnostics466 map, historical test
binding and eight product replacements, then require their exact equality to
PG10 manifest `f44346d3f76072b62c61e72fa8231e318650ec0cd0da8d976f2ef043f16dbb3d`.
A distinct19-row structural stage then binds the new receipt, parent, branch,
bundle, count and before hashes. The original21-source loop applies both stages.
Nothing overwrites the old8 provenance with new19 evidence.

Independent passive map comparisons confirm:

- unchanged original8, diagnostic/native/product authority and historical results;
- exact19 structural replacements over PG10,447 unchanged hashes and466 total keys;
- all466 resulting live source hashes agree with private6db944 and with the bytes
  in historical residual-static manifest
  `7a48620648806214d5c4158488cd33432b57e9c234a1a5c94b76015fcf36cacf`;
- all348 seed paths, unchanged removals,199 snapshot subjects and102 historical
  pins; original CoreC2 source21 checks also reconcile with both stages;
- the recipe's139 currently known unique approved-input union has no contradictory
  pins and every referenced file hash matches. This is **not** a final manifest
  input count: README/recipe and future review/disposition still require actual
  inclusion. All121 PG10 approved inputs and10 old tool provenance pairs must be
  retained. Active tools remain the identical original5 plus new5, not old+new
  active runners.

The historical residual manifest has matching source bytes but **not current Git
context**. No fresh PG14 manifest or199 fresh snapshots were created or accepted
by this review. The source receipt is not a deployed acceptance checkpoint.

Source materialization retains the clean detached public prerequisite check,
8MiB bounded bundle/header/hash/ref gates and local file-only private import.
The new parent stage is checked and recorded both before and after, preserving
the full older chain and clean/effective-file inventories. No public private-tip
fetch/push, extra child, merge or rebase is authorized.

## Lifecycle, resources, capture and privacy

The actual diff preserves the accepted ownership and cleanup implementation:
protected owner acquisition; handle publication before fallible collection;
sticky nonzero, forced-drain and cancellation failures; stop/drain/container
verification before capture; capture before deletion; postflight and another
drain before file cleanup; final stop/drains/census before home cleanup; explicit
absence and retained-file inventories. Failed capture or unproved absence cannot
silently authorize deletion. No broad cleanup or foreign-container removal was added.

- Fixed25min job,1200s controller,120s preflight,900s validation and180s cleanup
  reserve remain unchanged. No prewarm, retry or enlarged test/operation budget.
- Same Gradle2GiB/512MiB metaspace, max-workers1, one512MiB test worker,
  forkEvery0, disabled reuse/build/configuration caches and8GiB free-space floor.
- Exactly two created containers remain required: one PostgreSQL17.6-alpine and
  one Ryuk0.12.0, with the existing Testcontainers1.21.4/session/image/event,
  known-ID removal and measured final-absence gates. Forced removal remains FAIL.
- Same private-repository job guard, contents:read, pinned actions, exact carrier
  checkout, persist-credentials:false, three-day private artifact retention,
  sanitized child environment, private paths and inherited-Java-override refusal.
- JDK21 identity and classpath supplier checks, explicit JAR/checker hashes,
  stock-runtime removal/dedup, no-agent/loader/MR checks, bounded archive/regular
  file/path handling and duplicate JSON/XML guards are unchanged. Structured
  failures retain type/literal guard IDs, not exception text.
- Exactly the original four required raw shutdown rows remain: RETURN_SAMPLE and
  FAILED_POST_CONSENT_TAIL, each CAPTURED BEFORE_SHUTDOWN/AFTER_SHUTDOWN. Missing,
  duplicate or UNAVAILABLE required rows cannot pass. The scalar reader is
  unchanged; these non-atomic observations are not causal or completion proof.

These are reviewed source properties, not measured results of a new run.

## Required primary-only continuation and limitations

1. Disposition this exact source review. Resolve Backend11 integration-ref
   advancement before creating the fresh PG14 full-v3 context; never reuse a
   freeze across that change. Keep private6db944 fixed.
2. Expand all inherited maps plus actual new review/disposition/recipe inputs,
   create the genuine stable-context v3 manifest and obtain actual successful
   local preflight using the unchanged pinned freezer. Its argv spelling and
   retained-tool construction were inspected as text only. No placeholder may
   substitute for actual bytes or receipt.
3. Privately deploy complete authority/snapshot/history/tool/diff/bundle maps
   and create a **distinct** accepted deployed checkpoint. Derive and hash a
   separate final request. The sealed draft remains `authorized=false` with64
   zero checkpoint digits; neither this review nor source receipt6e7cfcdb fills
   that admission slot. Any launch needs separate primary authority, at most one
   attempt, and later independent actual-result review.

Keep PG10 run34691665288 as accepted10 on1c91 only; retain its raw PostgreSQL
kill9/die137. `NORMAL_ABSENT` is not graceful shutdown or zero-kill proof.
Historical45/47 and diagnostics0/2, cleanupFAIL/containersUNKNOWN,
outputs_absent=false and six retained directories remain unchanged. Prior38
unit passes are carried, not rerun; residual acceptance is compile/static only.
Strict Gradle dependency verification without verification metadata is not
transitive dependency-byte proof. Effective classpath/class-load logs are context,
not consumer or native qualification.

SQLClientInfo declaration/defaults/foreign-caller coverage, consumer/descriptor/
original-provider provenance, process-only END-TL/core-last-count probes,
foreign cancellation, opaque real-eviction/first-close/liveness and full47 remain
outside this selection. Native05 stays UNQUALIFIED; D05 PARTIAL/not import-ready;
D06 unreviewed/unexecuted; W03/App29/native/full qualification stays open.

## Review actions and preservation

Only passive source/text/JSON/hash/path/Git reads and in-memory data/diff
comparisons were performed. No candidate/helper/freezer import or evaluation,
AST/syntax/static checker, build/test/probe, network/CI/dispatch, Git/source/ref
edit, process/resource action or cleanup was performed. Only this separate private
mode0600 report was written. Packet members/external input pins were rehashed
before writing; live PG10 controller/workflow/request/helper hashes remained
unchanged. Backend and Admin status were clean at final inspection, with Backend
still at6db944. Primary owns notifications, adoption, freeze and all later results.
