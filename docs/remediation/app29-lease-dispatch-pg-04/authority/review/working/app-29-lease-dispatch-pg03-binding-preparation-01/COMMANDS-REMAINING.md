# PG03 primary-only remaining binding commands

**Documentation, not an executable helper or authorization. None of the following
adoption/freeze/preflight/deployment commands was run by this author.** Preserve
this sealed preparation and every failed historical attempt. Stop on a mismatch;
do not silently update a pin, weaken a guard, retry or invent a receipt.

## 1. Acceptance and fresh locations

Obtain primary acceptance of the independent actual-diff review for these exact
sealed bytes and the separately authorized focused cleanup synthetic report.
Include their actual paths/hashes only after they exist and are accepted. The
earlier source/cleanup source-only approvals do not substitute for either.

Use the existing finite primary PG02 binding flow as the reference, not as a
ready-to-run PG03 program:
`review/working/app-29-lease-dispatch-pg02-bind-01.py`. It contains writes, a syntax
check, real freeze/preflight and live deployment, so do not execute it unchanged.
Do not introduce a new approximate validator, binder framework or receipt writer.
Primary must inspect worktree changes and all proposed destinations before writes.

Proposed workspace-relative locations (not created by this author):

| Purpose | Path |
|---|---|
| Reviewed bound copies | `review/working/app-29-lease-dispatch-pg03-bound-01` |
| Actual fresh v3 freeze | `review/working/app-29-w03-integrated-driver-lease-dispatch-pg-03` |
| Primary command/evidence records | `review/working/app-29-lease-dispatch-pg03-admission-01` |
| Later private Admin payload | `docs/remediation/app29-lease-dispatch-pg-03` |

All must be fresh; an occupied path is not permission to overwrite prior evidence.
Keep private directories0700/files0600 and primary-owned command/exit recording.
The existing source freeze/checkpoint and separate corrected named-ref transport
remain inputs, not the new hosted freeze/deployment checkpoint.

## 2. Adopt, then finish the literal hash cycle

In separate bound copies, make only the reviewed current-stage binding changes:

1. Change profile `pg03_source_stage_status` to `BOUND_BY_PRIMARY` and its current
   scope prefix to primary-bound **without runtime acceptance**; append real
   accepted review pins to `pg03_provenance`. Preserve all historical maps and
   `pg02_*` fields. Source head/tree/manifests/checkpoint/transport pins already
   contain actual values; recheck rather than zero-rebinding or guessing them.
2. Keep `source_inventory`, `pg03_reviewed_source_diff` and existing provenance
   references pointing to this sealed preparation's selection/source patch.
   They are immutable evidence, not current deployments. Do not globally rewrite
   every preparation-path occurrence in the profile.
3. Replace the current preparation path with the bound path only in controller
   `PROFILE_FILE`, `PROFILE_INIT`, its two controller/workflow `DEPLOYMENTS`
   originals, the init `profileFile`, workflow profile paths and the false
   request's two deployed profile/init tool-map keys.
4. Seal the final profile first. Put its measured SHA in init `profileSha256` and
   controller `PROFILE_SHA`; seal init and put its measured SHA in controller
   `PROFILE_INIT_SHA`. Then seal controller and workflow. Preserve the unchanged
   owner original/deployed mapping and hash. No zero value is a wildcard.
5. Retain the actual preparation-to-bound diff and measured final file pins.
   Keep the request false and its future checkpoint/tool bindings unfinished
   until the real final manifest, genuine receipt and deployment checkpoint exist.

Use only the corrected named-ref source bundle SHA
`b606cb5ed40814dc23c5c8c61a564de07d917d4a05b6fbca4c4b73841bea63fe`
(287442 bytes) for current transport. Preserve the original full source checkpoint
and HEAD-advertised bundle separately. The transport-only receipt cannot replace
the full source checkpoint or the later deployment checkpoint schema.

## 3. Close the real, nonconflicting dependency set

Start with `dependency-pins.json`'s 355 `approved_input_candidates`, which include
the inherited approved/tooling union and current profile references. Reconcile
the final profile recursively with each predecessor manifest's approved/tooling
maps and complete diff. Add **every** file in this sealed preparation, including
baseline copies, both documents and both seal files, the final bound profile,
and actual primary-accepted source/preparation/synthetic review records. Rehash
each actual file; reject any repeated path with a different digest. Retain all
481 sources, 214 complete snapshots, 348 seed keys, removed/subject/history maps
and the fresh whole issue-baseline diff; this packet's one-call patch is not it.

Construct the existing command's `APPROVED_ARGS` as repeated separate argv pairs
`--approved-input <workspace-relative-path>` for the final sorted unique union.
Its exact final list/count cannot truthfully be fixed before the real reviews and
bound bytes. Do not substitute the number355 for the final approved/authority count.
The five final tooling originals are listed explicitly in the command below.
Preserve manifest-self, genuine-receipt and later checkpoint/request exclusion
from the earlier frozen input set; avoid a hash cycle. Sealed author originals
and final bound paths are distinct inputs, not conflicting versions of one path.

## 4. Invoke the unchanged real v3 freezer, then its real validator

The existing freezer source must still hash to
`e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`.
Run only through primary's existing measured one-call path, retaining exact argv,
stdout, stderr and exit status with its existing 120s bound. The following is the
actual CLI shape after primary has constructed `APPROVED_ARGS`; it is not a new
helper or permission to run from this preparation task:

```bash
python3 -B /root/projects/Kira/review/working/freeze_app29_integrated_driver_v3.py \
  --workspace /root/projects/Kira \
  --freeze app-29-w03-integrated-driver-lease-dispatch-pg-03 \
  "${APPROVED_ARGS[@]}" \
  --tooling review/working/app-29-lease-dispatch-pg03-bound-01/ci/app29-gate-b.py \
  --tooling review/working/app-29-lease-dispatch-pg03-bound-01/.github/workflows/app29-gate-b.yml \
  --tooling review/working/app-29-lease-dispatch-pg03-bound-01/profile/profile.json \
  --tooling review/working/app-29-lease-dispatch-pg03-bound-01/profile/profile.init.gradle \
  --tooling review/working/app-29-targeted-private-ci-draft-v2/ci/app29_owned_children.py \
  -- test \
  --tests 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.mixed pool creator nesting refuses wrong top fallback and unrelated lease use' \
  --tests 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement'
```

After a successful real freeze, measure the actual final manifest SHA as
`MANIFEST_SHA` and retain it with the command record. The separately measured
validation command must use that exact digest and the same five task argv:

```bash
python3 -B /root/projects/Kira/review/working/freeze_app29_integrated_driver_v3.py \
  --workspace /root/projects/Kira \
  --validate-manifest /root/projects/Kira/review/working/app-29-w03-integrated-driver-lease-dispatch-pg-03/manifest.json \
  --manifest-sha256 "$MANIFEST_SHA" \
  -- test \
  --tests 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.mixed pool creator nesting refuses wrong top fallback and unrelated lease use' \
  --tests 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement'
```

Only a successful actual validator call producing
`READ_ONLY_V3_PREFLIGHT_PASSED` with `source_paths=481` supplies the receipt.
Preserve its exact stdout bytes as the new freeze's `hosted-local-preflight.json`;
do not render a similar JSON object, copy an older receipt or treat passive hashes
as preflight. Preserve any failure and stop; no automatic retry. Final source map
must equal the approved PG03 source freeze, with all 214 snapshots and 348 seeds.

## 5. Later checkpoint, false request and independent actual binding

Only after the genuine receipt may primary prepare the distinct accepted
deployment checkpoint using the unchanged
`app29-lease-dispatch-clean-checkpoint-v1` schema. It must bind the real manifest,
receipt and unchanged verifier digests, exact f2e58eac source and named-ref bundle,
with source/transport-only scope and no invented runtime acceptance.

The existing authority flow must nonconflictingly include the actual manifest,
receipt, all snapshots/historical/approved/tooling maps and complete diff. Measure
real authority counts/bytes. Private deployment must exactly match all five
original/deployed tooling pins and the approved bundle. Only then fill the final
false request's checkpoint and tooling digests and retain its exact bytes.

Distinct independent **actual-bound** review and explicit primary one-attempt
admission remain required before any execution. This document grants no build,
test, controller/helper run, CI/push/dispatch, public Backend push, private-vendor
disclosure or integration authority. No launch command is provided here.
