# PG04 remaining primary-only steps — NOT EXECUTED / NOT AUTHORIZED

This is documentation, not a binder/helper. No command here was run by the author.
Do not run the old PG03 binder unchanged: it writes live Admin, freezes, invokes
tooling and assumes PG03's different checkpoint fields/two selectors. Reuse its
existing measured one-call/authority/deployment lifecycle only after acceptance.
Reference: `review/working/app-29-lease-dispatch-pg03-bind-01.py`, SHA-256
`ee79f95b00df54c7baab8459c5da88e17f041f875f0de4155c3c3c2cb2d779c5`.
No new binder, inventory approximation, receipt writer or validation harness is
required by this packet. Primary owns scope/resource/admission decisions.

## 1. Accept exact preparation, inspect fresh destinations

Obtain independent actual-PG04 packet review and primary acceptance first. Preserve
this sealed preparation. Future locations (not created by the author):

| Purpose | Workspace-relative path |
|---|---|
| Bound tooling | `review/working/app-29-lease-dispatch-pg04-bound-01` |
| Named-ref source bundle | `review/working/app-29-lease-dispatch-pg04-transport-source-01/backend.bundle` |
| Actual final full v3 freeze | `review/working/app-29-w03-integrated-driver-lease-dispatch-pg-04` |
| Primary binding/admission/collector evidence | `review/working/app-29-lease-dispatch-pg04-admission-01` |
| Later private Admin payload | `docs/remediation/app29-lease-dispatch-pg-04` |

Refuse occupied destinations, preserve all existing worktrees/indices and old
results, and retain private0700/0600 permissions. Current Backend must still be
clean0582abc/tree d20c606 with exactly f2 as parent. The provided a5367797 source
checkpoint remains immutable; do not rewrite it into a new schema. Its one-site
pin must match the accepted915785fe source bytes. No public Backend push.

## 2. Bind actual transport and separate copies, still unauthorized

Primary must prepare/measure the real bounded named-ref bundle from current
0582abc using the existing Git-bundle flow: singleton prerequisite
`3d839130c807f6a0a9b1c896c1c6cca4b41c4538`, exact advertised
`refs/heads/remediation/app-29-backend-complaints`, and complete v2 SHA1 pack.
No `HEAD` advertisement fallback, ref wildcard, prerequisite change, new fetch
source or guessed size/hash. Keep actual command/header/list-heads/verify records.
The existing controller still verifies size/hash/header and owned import/readback.
No source freeze needs to be fabricated to form this bundle; the current source
checkpoint and actual final full freeze are distinct evidence.

In separately named bound copies, not this sealed directory:

1. Set `pg04_source_stage_status` to `BOUND_BY_PRIMARY` only after accepted source
   and preparation review. Change only the current scope prefix and append the
   actual accepted review paths/hashes to `pg04_provenance`. Keep every historical
   field (especially `pg03_*`) and the original current source-checkpoint pin.
2. Keep `source_inventory`, `pg04_reviewed_source_diff` and provenance pointing to
   sealed author originals. Replace the prep prefix with the bound prefix only
   in controller `PROFILE_FILE`/`PROFILE_INIT`/deployment originals, init's profile
   path, workflow profile paths and the false request's profile/init tool-map keys.
   Do not globally rewrite historical/original evidence references in the profile.
3. Bind current `SOURCE_BUNDLE` and the false request to the real measured bundle
   path/hash/size, preserving current head0582abc/private parent f2. Old PG03 bundle
   bindings are historical and must not be changed. No zero pin is a wildcard.
4. Seal final profile first; place its actual SHA in init and controller; seal
   init and place its actual SHA in controller. Then measure controller/workflow.
   Keep the unchanged ownership original/deployed map and digest
   `56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385`.
5. Retain actual preparation-to-bound deltas and measured pins. Request stays
   false; later deployment-checkpoint/tool bindings wait for genuine evidence.
   Collector's inert header/zero Admin parent remain unconsumed preparation,
   not permission to remove the stop or use a stale PG03 Admin parent.

## 3. Reuse the full nonconflicting authority union

Start from the actual PG03 final manifest, not a newly approximated inventory:
`review/working/app-29-w03-integrated-driver-lease-dispatch-pg-03/manifest.json`,
SHA `0df6165f928d7a752d7a253d18078b099ca81eae9c7d5bc466bc828a74763f1f`.
Its existing approved/tooling maps and inherited profile predecessors provide the
established union. The old primary `approved-inputs.json` is a pinned reference,
not a sufficient final list by itself. Preserve original contradictory-pin
rejection; never update an old path's digest to make the new candidate fit.

Retain every inherited approved/tooling input, the original PG03 manifest and
whole diff, referenced historical checkpoints/maps/results, all current profile
references and actual named-ref bundle. Add every sealed PG04 packet member
(including both documents and seals), final bound profile and real accepted
source/preparation review records. Rehash actual bytes. Current production/source
paths are governed by the real freezer; the30 readback references are not a new
source inventory or a blind `--approved-input` list.

Construct `APPROVED_ARGS` using the existing binding flow as repeated separate
argv pairs `--approved-input <workspace-relative-review-path>` for that final
sorted unique union. Do not invent an authority count before final inputs exist.
Keep the unchanged five base tools and exactly the five explicit tools below.
The fresh manifest, genuine receipt, later deployment checkpoint and current
request must be excluded from their own earlier input maps to avoid hash cycles.
Sealed author originals and final bound files are distinct paths/byte identities.

## 4. Genuine unchanged v3 freeze and real preflight, exactly one selector

The existing tool must still hash to
`e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`.
It hard-binds development07 seed manifest
`review/working/app-29-w03-integrated-driver-development-07/manifest.json`, SHA
`3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`,
and explicitly refuses loss of any of its348 source keys. Do not change its
EvidenceSpec, invoke an alternate inventory, add a seed-removal waiver or prune
sources to the selected method.

Use primary's existing measured one-call path with120s bound, exact argv and
separate raw stdout/stderr/exit records. After `APPROVED_ARGS` really exists, the
actual existing CLI shape is:

```bash
python3 -B /root/projects/Kira/review/working/freeze_app29_integrated_driver_v3.py \
  --workspace /root/projects/Kira \
  --freeze app-29-w03-integrated-driver-lease-dispatch-pg-04 \
  "${APPROVED_ARGS[@]}" \
  --tooling review/working/app-29-lease-dispatch-pg04-bound-01/ci/app29-gate-b.py \
  --tooling review/working/app-29-lease-dispatch-pg04-bound-01/.github/workflows/app29-gate-b.yml \
  --tooling review/working/app-29-lease-dispatch-pg04-bound-01/profile/profile.json \
  --tooling review/working/app-29-lease-dispatch-pg04-bound-01/profile/profile.init.gradle \
  --tooling review/working/app-29-targeted-private-ci-draft-v2/ci/app29_owned_children.py \
  -- test \
  --tests 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement'
```

Require the resulting complete source map to equal actual PG03 plus only the
reviewed f8583ac5→915785fe test replacement, with no new/removal/production delta,
all481 paths/214 actual fresh snapshots/all348 seed keys and102 historical pins.
Check every actual snapshot and the new complete issue-baseline diff. The small
`source-delta.patch` is not a replacement for that full diff or genuine freeze.

Only after successful real freeze measure the actual manifest SHA as
`MANIFEST_SHA`. Then use the unchanged real validator, with exactly the same
three task argv (not PG03's old five):

```bash
python3 -B /root/projects/Kira/review/working/freeze_app29_integrated_driver_v3.py \
  --workspace /root/projects/Kira \
  --validate-manifest /root/projects/Kira/review/working/app-29-w03-integrated-driver-lease-dispatch-pg-04/manifest.json \
  --manifest-sha256 "$MANIFEST_SHA" \
  -- test \
  --tests 'me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement'
```

Only successful actual validation supplies `READ_ONLY_V3_PREFLIGHT_PASSED` with
`source_paths=481`. Preserve the actual stdout bytes as this new freeze's
`hosted-local-preflight.json`; do not write a lookalike JSON receipt, copy PG03's
receipt or claim passive readback is preflight. Preserve any failure and stop;
no automatic retry. This documentation grants no execution authority.

## 5. Later transport, independent actual binding, admission and collector

After the genuine receipt, reuse the unchanged later deployment checkpoint schema
`app29-lease-dispatch-clean-checkpoint-v1`: actual current head/bundle, final
manifest and genuine receipt hashes, unchanged verifier digest, and source/
transport-only acceptance. This is not the provided source-only checkpoint and
not runtime acceptance. Transport the same full actual authority union/snapshots/
historical/approved/tooling maps/diff, with contradiction refusal and measured
counts/bytes. Deploy only the five matching original/deployed tools and exact
bundle after separate primary authority; no live Admin edits are authorized here.

Only then finish the still-false request's checkpoint and tool digests. Obtain
independent actual-bound review. Existing actual read-only `bind_freeze` and
separately authorized normal `--emit-target` checks remain primary decisions,
not this author's imports or substitute preflight. No request activation is
requested or authorized by this packet.

The collector draft remains stopped before imports/writes/locks/network and has
zero actual Admin parent. Primary may later prepare a distinct bound copy against
fresh actual private Admin state, retain the finite delta, have that copy reviewed,
and only after explicit one-attempt admission remove the inert preparation stop.
Retain the same hosted-validation lock through raw collection, private repository/
parent/index/status/request checks, scoped one commit/push, exact run/attempt
observation, unique artifact, raw logs/hashes and RAW_RESULT_REVIEW_REQUIRED.
Uncertain push/run/timeout must be reconciled, never retried automatically.

No launch command, new helper or request grant is supplied. Do not replay mixed
PASS/prior16, push private Backend ancestry publicly, broaden tests, start local
heavy work or conflate successful capture/absence with test/production PASS.
