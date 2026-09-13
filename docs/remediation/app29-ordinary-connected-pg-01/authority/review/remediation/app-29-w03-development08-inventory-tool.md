# App #29 W03 — successor inventory tooling (development08 preparation)

**2026-09-08; evidence-tool maintenance only. No source freeze, product edit, build, service,
acceptance, commit, push or integration is authorized by this note.** Historical development07
and Timer-A02 evidence remains immutable. The primary owns the separate Linux runner adaptation.

## Investigation and bounded change plan

Read: workspace/backend `AGENTS.md`, backend `docs/PLAN.md` architecture and hard constraints,
`review/AGENT_HANDOFF.md`, tracker `NEXT EXACT ACTION`, the committed private checkpoint ledger,
the restored repository-verification receipt, the complete old integrated freezer/runner and the
PostgreSQL wrapper's ownership/resource checks, development07 and Timer-A02 manifests.

The historical `freeze_app29_integrated_driver.py` seeds 283 Timer-A02 paths and adds only unstaged
diff/untracked paths. After checkpoint commit `98ad9ac57de3a33b80fc31079c7278c83f64e675`, that would
silently lose all 65 committed integrated additions. Its `git diff --binary` is also empty on this
clean checkpoint, not the full issue diff. The restored clones have the pinned integration refs
under `refs/remotes/origin/`, not local integration branches. Creating branches to satisfy the old
tool, changing old manifests, or weakening reference checks is unnecessary and not permitted.

Before editing new tooling, read-only verification found:

- development07 manifest SHA256 `3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`;
  all 348 live source hashes, 77 snapshots, three tooling pins and two approved-input pins match.
- Timer-A02 manifest SHA256 `e955789a8342a21c224f216147bad9190161a4c0df5d36b977622320154917f2`;
  all 15 snapshot/two tooling pins match; the expected 12 integrated source changes remain explicit.
- all five issue heads and remote-tracking integration refs match the restoration/checkpoint ledger.
  All five worktrees are clean. Remote verification was performed by the primary/restore process;
  this tooling task does not fetch, update refs or publish anything.
- The full backend baseline `c8bdff9a8acebb7c8e8ce40c65b8c7315ef9c014` to current worktree diff
  names 349 paths: all 348 frozen07 paths plus the committed `docs/REMEDIATION_HANDOFF.md`.

Create **new** paths only:

1. `review/working/freeze_app29_integrated_driver_v2.py`: import-safe, standard-library inventory,
   preflight and future fresh-directory freezer. Default CLI operation is read-only dry validation;
   no command in this task will invoke its explicit freeze operation.
2. `review/working/test_freeze_app29_integrated_driver_v2.py`: isolated Python unit/negative-control
   tests using temporary files and fake read-only Git responses, with no repository writes/builds.
3. This new scope/result note and, if useful, a separately named dry-validation result. Do not edit
   trackers, old reports, snapshots/manifests, historical freezer/runners or the new Linux runner.

## Required invariants

- Seed **every development07 source path**, plus Timer-A02 continuity and inherited removals. Add
  the full issue-baseline diff and all current untracked/nonignored paths. A clean Git status must
  never remove a previously frozen addition from inventory. Retain checkpoint documentation too;
  do not call 349 files 349 product files.
- Missing files fail closed unless the exact new removal has a separate, hash-bound review receipt;
  inherited removals remain absent. Reject traversal, symlinks, special files, unsafe extra removals
  and staged changes. Do not hide an unreviewed removal behind `is_file()` filtering.
- Keep the Timer-A02 baseline comparison explicit, distinguish changes since07 from changes since
  Timer-A02, and snapshot every Timer-relative changed/added file for an eventual candidate.
- Capture and pin a deterministic **full issue diff from c8bdff9…**, not only the uncommitted delta;
  untracked additions remain explicitly hashed/snapshotted because Git diff does not include them.
- Pin seed/baseline manifests, historical snapshots/tooling and approved inputs, current tooling,
  exact tasks, source bytes, all five repository HEAD/branch/status identities, the actual selected
  integration-ref names and their expected hashes. Ref drift must fail even on restored clones.
- Recompute discovery as well as hashes during validation. Detect added/deleted/unlisted files,
  tool/input/snapshot/task/ref drift and changes during collection. Never rewrite an existing output.
- The Linux runner will import the same read-only validator and use the same full issue-diff bytes;
  it must preserve its own 8 GiB/resource/dependency/owned-cleanup gates independently.

## Validation plan / results

Planned Python tests: committed additions on clean status, new committed/untracked paths, explicit
and unreviewed removal controls, inherited-rename reappearance, invalid paths/symlinks, Timer baseline
comparison, full-diff pinning, staged changes, repository/ref drift, snapshot/tooling/input/task drift,
and fresh-output refusal. Run real-workspace inventory dry validation without writing a candidate,
then verify the old348 source/tooling/manifest pins and five repository identities again.

Implementation/results will be recorded below after the isolated tests. This note is not an
independent review or authority to run development08; D13/Timer/static fixes, draft reconciliation,
required gates and both final independent reviews remain the primary's separate unfinished work.

## Implemented interface and review boundaries

The successor is import-safe and exports:

- `issue_diff(root) -> bytes`: deterministic, binary-capable, no-rename full diff from the pinned
  issue baseline, with external diff/text conversion disabled.
- `prepare_candidate(root, tasks, ...)`: read-only, two-pass membership/byte/ref collection in memory.
- `validate_manifest(root, manifest_path, tasks, expected_manifest_sha256=None) -> dict`: read-only
  v2-only preflight. It recomputes membership, not just the existing manifest's listed hashes, and
  checks every approved input as well as snapshots/tools/tasks/refs. The Linux runner requires the
  caller's explicit manifest SHA256 and passes it here. Historical07 is rejected for execution.
- `freeze_candidate(...)`: explicit future opt-in, fresh-directory-only writer, tested exclusively
  with tiny synthetic temporary fixtures in this task. It retains `issue-baseline.patch`, writes
  the manifest last after rechecks, and never overwrites or cleans a partial/existing directory.

Read-only use, with no freeze/build:

```sh
python3 -B review/working/freeze_app29_integrated_driver_v2.py --dry-run
python3 -B -m unittest discover -s review/working \
  -p test_freeze_app29_integrated_driver_v2.py -v
```

For a later authorized freeze, pass **explicit** exact tasks after `--`. Repeated `--approved-input
review/...` adds finalized diagnostic/correction/review/draft-import approvals; repeated `--tooling
review/working/...` pins any additional executed helper. Mandatory tooling includes both separate
Linux runners, this v2 freezer, its tests and the historical explicit dependency init script. Missing
Linux tools are listed only by dry mode; an actual freeze/preflight refuses them. Default dry-mode
tasks are the historical07 four filtered suites plus statics, not a new execution authorization.

Any new removal requires `--reviewed-removals review/working/<new-receipt>.json`, schema1, binding
`seed_manifest_sha256` and an exact `removals` list. Each entry names `path`, `previous_sha256`,
`reason`, `review_document` and `review_document_sha256`. The prior hash must match07 or, for a
non-seed issue deletion, the regular baseline Git blob. The file must actually be absent and the
separate review must match; extra/present/duplicate removals fail. No new removal is approved by
this tool or this note. The inherited `TransportBoundTestFixtures.kt` rename remains absent.

The immutable checkpoint ledger is additionally pinned at
`0b80c2e78ac1ee2a5a4287c8749cbdef6f9c7c6dade627cca756a128c5181d54`.
The Admin containing commit is resolved read-only from the ledger's committing revision, not
invented or replaced by the pre-checkpoint Admin product baseline. All five checkpoint heads must
still match. Local integration branches and origin-tracking aliases, if both present, must both
match the baseline; their exact names/existence are frozen and rechecked. The primary created the
matching local integration aliases separately during this task; this inventory task wrote no refs.

## Test and dry-validation results

**42/42 isolated Python tests passed**, with fake Git responses only. Synthetic freeze/preflight
tests create and clean only their own temporary fixtures; no real candidate directory or product
file is written. Covered controls include the original clean-status committed-addition omission,
new committed/untracked files, malicious manifest omission, Timer comparison, current/historical
snapshot drift, full diff vs empty uncommitted diff, staged changes in another repo, checkpoint
HEAD/branch/ref drift, alias creation after freezing, source/ref/discovery drift during collection,
reviewed/unreviewed/rematerialized removals, changed review/tool/input/task pins, unsafe paths,
symlinks, non-regular files, duplicate JSON and fresh-output refusal.

The first real dry attempt **refused** the historical `changed_previous_paths` ordering:07 retains
Timer's insertion order rather than lexical order. Inspection confirmed exactly the same12 paths.
Only the new comparator was corrected to compare duplicate-free membership; a dedicated positive/
duplicate negative-control test was added. No historical list/hash was changed. The next real
dry run passed:349 paths, all348 seed members retained, committed handoff document added,12 explicit
Timer changes plus66 Timer additions/78 prospective snapshots, no new removals. It correctly listed
four concurrently authored peer test corrections and the then-missing Linux PostgreSQL wrapper;
that incomplete tooling state could not be frozen. No source freeze or historical cycle was run.

Fresh retained test/dry receipts (created without a candidate) are:

- `review/working/app-29-w03-development08-inventory-tests-01.log`
- `review/working/app-29-w03-development08-inventory-dry-01.json`
- `review/working/app-29-w03-development08-inventory-verification-01.json`

The JSON dry/verification receipts are authoritative for the exact later timestamp, code hashes,
peer edits, source count, full issue-diff hash, missing tools and repository identities. Source bytes
can differ from07 because other authorized contributors are editing them; this task made **no**
product/source/test changes. It verified348/348 before those edits and separately accounts for
subsequent differences rather than claiming the old failed candidate remains current.

### Remaining limits / primary handoff

- No independent approval or real development08 freeze/execution is claimed. The primary must
  finalize/pin the separate Linux runtime wrapper and any new review inputs, stop concurrent
  writers, perform a fresh dry check, then use a new candidate. Collection/revalidation is not an
  atomic filesystem lock or a waiver of live preflight checks.
- This successor intentionally refuses later checkpoint-HEAD or ledger changes. Another reviewed
  checkpoint transition needs explicit new tooling/pins, not edits to these frozen assumptions.
- The full Git patch includes tracked committed/working-tree changes. Git cannot include untracked
  file content in that patch; those paths' bytes are explicitly present in source hashes and the
  Timer-relative snapshots. No omitted untracked content is represented as being in the patch.
- Python tests/dry inventory are evidence-tool verification only: they add no lifecycle/database
  runtime coverage, acceptance, package or issue-delivery credit. 8 GiB/dependency/runtime ownership
  and stop/capture/clean/stop remain the Linux runner's separately required gates.
