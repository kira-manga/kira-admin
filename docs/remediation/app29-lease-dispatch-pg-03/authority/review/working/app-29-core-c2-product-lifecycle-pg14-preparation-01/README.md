# CoreC2 post-structural PG14 — private preparation01

2026-09-12 UTC, Admin04. **SOURCE-ONLY REVIEW PACKET; NOT A FRESH V3 FREEZE,
DEPLOYED ACCEPTANCE CHECKPOINT, EXECUTION ADMISSION OR RESULT.** No live files changed.
The request is `authorized=false`; its deployed-checkpoint hash deliberately remains
64 zeroes. Primary alone owns review acceptance, fresh freeze/preflight, deployment,
final request and any one-attempt launch. Keep this packet immutable during review.

Authority: `review/remediation/app-29-core-c2-post-structural-pg-selection-advisory.md`,
SHA256 `d934676c715da7aaef8e008c264e0b5e5e7cb30e4a909103878f521a44bc4f64`.
This implements its exact prior10 + four existing same-class negative controls;
it neither adds tests nor proposes another validation framework.

## Exact five-file derivative

`carrier.patch` is the actual unified diff of all five candidate files against the
matching `before/` copies (labels are packet-relative, not a command to edit live
Admin). SHA256 `16e46e7f4615db69d367369f50215cbea0a0e7186fcd68e6383d330f94fb2e06`.
The controller grows806 to845 lines. `before.sha256` and `after.sha256` bind both
sides. There is no second runner, new helper, fixture, source snapshot or harness.

| Packet-relative file | Accepted PG10 before SHA256 | PG14 candidate SHA256 |
| --- | --- | --- |
| `ci/app29-gate-b.py` | `230140399aa9353ef6f3628c1c961aa1cda96f52bbfa5b97c8245fa9f2b3b301` | `7fce9fae743a4d235350d2c93610142fc7a0177f2b7d7e44031b56b8315f0576` |
| `.github/workflows/app29-gate-b.yml` | `7822bd6fb67d1916977520ceb5e77adf1949a2ae774ac5e9b8917a99e72da625` | `790377568f065d1e2f64bad1a796a3d17f4a32cea224204adda25465c5d3a328` |
| `ci/app29-gate-b.request.json` | `b44e501172be7960b58ccff72f548e790de5a6929c47251e16af4bd54ec21f16` | `2934820e9714dff3bd2fc1cdf013b611db03cabb238b2ef6676456e982a837fb` |
| `profile/profile.json` | `f721c8d972206b973b2d3aefa4246bbd2d768c66f6f2908c470b3f896526b339` | `36c3637229efbe08186014f4c60684aa0569430b26bae9d13f8b811917e82225` |
| `profile/profile.init.gradle` | `09742b6796f0fe3d65f2b172272ab8a697ea5a07dadad7298bed1c062ee61ada` | `61fb92e47baa8dcabcd6a7521e01872984e196d16cfd643776f3a50b25a81964` |

The first three before-images are the live accepted PG10 carrier/workflow/authorized
request. The last two are the immutable PG10 preparation profile/init. The old
preparation's unauthorized request is a different historical file and is not replaced.
The shared helper stays `56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385`.

- New gate/request schema: `app-29-core-c2-product-lifecycle-pg14-01`.
- New profile: `app-29-core-c2-product-lifecycle-pg14-profile-01`.
- One `test` task, exactly29 task argv elements,14 literal method selectors and
  one expected XML suite with14 ordinary `method()` identities. The first10 retain
  their exact PG10 order. No wildcard, backtick or parentheses in CLI selectors.
- Four additions, all in the existing `PersistencePgOwnedCutIntegrationTest`:
  1. `throwing overriding original checkout sample cannot orphan its captured handle or future return right`
  2. `genuine throwing RETURN TL entry restores the authentic lineage and revokes only its still unused future right`
  3. `real post commit Blob work cannot silently commit through Hikari auto commit reset`
  4. `real commit failure retains unknown outcome and refuses reset before native auto commit`
- Profile/init/CLI/XML/classpath-count checks and run/report/artifact labels are
  explicitly rebound toPG14; never run14 under PG10 controls. `expected_witnesses=[]`.
  Normal compilation through existing task dependencies is not narrowed.

## Source ladder, not historical-result relabelling

Private source is already checkpointed at
`6db944871c1584bd6a1f28263e8010cadd766fab`, tree
`3558d08d9dfc826c6c1c4a79d26265f7cdee54cb`. The accepted source transport receipt is
`review/working/app-29-core-c2-post-structural-private-checkpoint-01/checkpoint.json`,
SHA256 `6e7cfcdb0598531092750a122b3cae985fe06f629455ee030773ba2242992556`.
Its bundle is217809 bytes, SHA256
`2506c18cc5e40f089cc1176a65a79d449ff02b13f4c08e0719c24d359e9882da`.
**That receipt is not the future deployed acceptance checkpoint.**

Required single-parent chain, checked before and after by the derivative:

```
6db944871c1584bd6a1f28263e8010cadd766fab
-> 1c91f0c2d1a4d797e83a0e33b871b417ebcfaae1
-> eb8fed8b6b620a0c7448c223bf49c1683f8eaadc
-> 989a8c07b90d956a5f2484f223be41b5d99a8a3c
-> 926927ab805a2a3b78957862f3b744d0fe399ac5
-> 49da0919d9ec3091cb7bb041009dc9bd5f3e090f
-> 3d839130c807f6a0a9b1c896c1c6cca4b41c4538
```

Only the last public prerequisite is checked out from public Backend. The bounded
private bundle supplies the frozen private chain. No merge, rebase, extra child or
public push of6db944/private ancestry is authorized by this preparation.

The original diagnostics466 baseline, historical `binding_test`, original8 product
replacements and original21-source checks are retained. A separate structural stage
requires that diagnostics + historical8 exactly equal the accepted PG10 manifest
`f44346d3f76072b62c61e72fa8231e318650ec0cd0da8d976f2ef043f16dbb3d`.
Only then are the19 `post_structural_source_delta` before/after pairs applied, each
matching the new source receipt. From PG10 this is19 replacements and447 unchanged
source hashes; all466 keys, exact removals,348 seed paths,199 snapshot subjects and
102 historical inputs remain. Old8 provenance is not renamed as new19 evidence.

All PG10 approved-input **and tooling** pairs must be preserved as fresh approved-input
provenance, in addition to the original63 diagnostics inputs. Active tooling remains
the original5 plus the new5 deployments; old carrier copies are not extra active
tools. The profile adds only seven post-structural authority pins, with the bundle
separately approved. `inputs.sha256` hashes the directly inspected authority/tool
files; it does not replace expansion of the complete inherited maps in `recipe.json`.

## Primary-only handoff and context hold

`recipe.json` is inert input/argv/deployment data. It is not a runner, manifest,
preflight receipt or acceptance. The unchanged v3 tool is
`e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`.

1. Obtain Web03's independent source-only review of these sealed bytes; primary
   dispositions it. This packet supplies no independent acceptance.
2. **Finish the Backend11 integration-ref decision first. Do not freeze now and
   reuse that context across the ref change.** Keep CoreC2 private source6db944
   fixed. Historical residual-static manifest `7a486206...` has matching source
   bytes but historical Git context, not a fresh PG14 freeze. Its compile/static
   disposition is `ACCEPT_COMPILE_STATIC_ONLY`; prior38 units are carried, not rerun.
3. After the context is stable, primary uses the original full-v3 inventory/freezer
   with all inherited approved inputs/tool provenance, new authority/bundle/review
   pins, exact new5 tooling and the profile's29 task argv. Fresh manifest path:
   `review/working/app-29-w03-integrated-driver-core-c2-product-lifecycle-pg14-01/manifest.json`.
   Require all466 sources/199 fresh snapshots/348 seed paths and truthful current
   Git/ref context; never invent a smaller selected-source inventory.
4. Primary obtains a genuine local v3 preflight for that actual manifest, then
   privately transports the complete manifest/snapshot/history/input/tool/diff maps
   and receipt under `docs/remediation/app29-core-c2-product-lifecycle-pg14-01/authority`.
   Existing dependency/JAR/bundle transport is reused without a new acquisition lane.
5. Primary creates the distinct deployed `app29-core-c2-clean-checkpoint-v1`
   acceptance checkpoint from that actual evidence. Hash it into a **separate final
   request**, then separately authorize at most one attempt. Never substitute the
   private source receipt's hash for the unresolved request checkpoint hash. Keep
   this sealed unauthorized request unchanged; record the final request's own hash.

Any source/pin/context/selection/container drift is a stop for primary disposition,
not a reason to silently broaden the gate or reuse an old receipt.

## Unchanged limits and unproved gates

- Same25min job /1200s controller /120s preflight /900s validation /180s cleanup.
  Same1s/operation and test-body budgets; no prewarm, extra hard fault or separate
  compile/static replay. Same2GiB Gradle heap/512MiB metaspace, max-workers1 and
  one512MiB test fork, `forkEvery=0`; at least8GiB free; source bundle at most8MiB.
- Same one-class PER_CLASS/SAME_THREAD lazy PostgreSQL17.6-alpine fixture and
  Ryuk0.12.0: exactly2 total /1 PostgreSQL /1 Ryuk. The existing accepted cleanup
  envelope is already in the before-image, not a newly loosened method-count rule.
- Same original18 dependency route, strict bounded archive/path/file handling,
  environment/JDK/classpath/hash capture, no agents or loader overrides, duplicate
  JSON/XML guards, owned subreaper/session drains, sticky forced cleanup,
  capture-before-delete and truthful UNKNOWN. No security/cleanup budgets changed.
- `--dependency-verification=strict` remains, but absent verification metadata is
  **not transitive dependency-byte proof**.
- Raw scalar reader is unchanged: only `RETURN_SAMPLE` and
  `FAILED_POST_CONSENT_TAIL`, each requiring one CAPTURED BEFORE/AFTER row (four
  required rows total). Other12 cases add no labels or positive witnesses. Missing,
  duplicate or UNAVAILABLE required rows cannot pass. Scalars remain non-atomic,
  best-effort and not causal, lifecycle-completion or consumer proof.
- Historical PG10 run34691665288 is accepted10 on1c91 only. Preserve raw PostgreSQL
  kill9/die137; `NORMAL_ABSENT` is not graceful-shutdown or zero-kill proof.
- Historical45/47 and original0/2 remain unchanged, including cleanupFAIL,
  containersUNKNOWN, `outputs_absent=false` and six retained private directories.
- Direct SQLClientInfo declaration/defaults/foreign-caller runtime coverage is
  outside this one-class selection. No second PG-owning class, process-only probe
  or consumer witness is added. Opaque real-eviction/first-close/liveness gates open.
- Native05 UNQUALIFIED; D05 PARTIAL/not import-ready; D06 unreviewed/unexecuted;
  W03/App29/native/full47/consumer qualification remains open.

## What was actually done

Only private text edits/copies/diffs and read/hash inspection. No candidate, helper
or freezer imports; no AST/compile/checker/test/build, freeze/preflight, Docker or
network probe, download, dispatch, Git write or live carrier/product edit. No owned
background work was started. Live accepted PG10 files and historical inputs were
read back by hash. `packet.json`, `SHA256SUMS` and `SEAL.sha256` seal source-only
preparation bytes; their existence is not runtime evidence.
