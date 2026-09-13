# Development11 — prospective source-snapshot adaptation
2026-09-09. Recommendation only; no freezer/runner invocation or refusal experiment.

## Decision

Use a small, explicitly versioned successor to the existing inventory, with the existing
Linux runner's execution/cleanup path. Separate **Backend batch identity** from **record-only
workspace progress**. Preserve v2, old manifests,348 development07 seed bindings and failure history.
Do not just replace the old Admin constant or add a global skip-validation switch.

The actual function is `_repository_states` (plural),278–299: besides integration refs it
rejects changed HEAD/branch and staged changes for every repository. Updating one Admin ref
would leave those other stale gates. Moreover `validate_manifest` recollects all candidate
fields; unrelated progress can also cause a false failure immediately before/after Gradle.

## Smallest prospective changes

- New inventory version/schema; unchanged historical07/Timer/checkpoint identities. Keep
  `_checkpoint` as historical provenance, not the required present-day state of all five repos.
- Successor `_repository_states`: gate only Backend for this Backend batch. Record its actual
  approved HEAD/issue branch/status and integration-ref context; keep the fixed issue-diff base
  and its ancestry requirement. Validation must compare against the frozen batch identity,
  not silently refresh expected HEAD/status from whatever happens to be live.
- `prepare_candidate`: retain existing source discovery/comparison/snapshot contents, but
  make its before/after identity check Backend-only. Add one documentary workspace-context
  field from primary's already collected state, separate from executable input identity.
  Record Admin's validated merge4f43288 using its **full40-character SHA**, actual branch/local
  integration/origin-tracking values and validation reference; distinguish unobserved refs.
  Do not fabricate the full SHA, equate a merge with remote synchronization, or fetch for this batch.
- `_candidate_again` / `validate_manifest`: carry that frozen documentary context without
  querying/requiring unchanged live Admin/App/Web refs. Recompute and compare Backend sources,
  HEAD/branch/status, path membership, issue diff, exact tasks and active tooling/input hashes.
  This policy must apply to freeze finalization AND each runner preflight/postflight.
- `_summary` may expose the documentary context; keep it visibly record-only. Adjust version/
  active-tooling path declarations, not historical hashes. No new seal/exporter/collector.
- Preserve the original runner file. Use a versioned entry/copy with an explicit fixed inventory
  import to the successor; keep its existing API. Its `main` validation at600 and
  `execute_batch` checks at488/528 must all reach the same successor. Do not delete checks,
  monkeypatch Git answers, repoint old refs, or regenerate an old manifest in place.
  No execution/cleanup implementation change is needed for this identity-policy adaptation.

## Non-negotiable retained checks

Keep `_history`, `_discover`, source hash/path comparisons, reviewed-removal handling,
`issue_diff` and snapshot verification. Development11 must contain **all34807 source paths**;
a reduced set plus a count label or removal workaround is not preservation. Retain changed
tracked files, untracked inputs, the full fixed-baseline diff and explicit test/compile selectors.
A source snapshot is not coverage: compile success is not test success/full regression.
Keep the pinned18 local dependency inputs and original init, Java21, one worker/in-process
Kotlin, existing heap/resource checks, private-home lock, immediate stop/preserve/clean/stop,
owned-child barriers, nonzero failure handling and raw reports. Concurrent unrelated Admin/Web
work may proceed; no one edits Backend batch inputs during the primary-coordinated build.

Remaining risks: incomplete untracked/build-input discovery, Backend drift during compilation,
an accidental v2/v3 validator mix, treating record-only context as validated runtime state, or
claiming test coverage from compile-only output. None is solved by reattesting unrelated refs.
D13's original2000ms/queryTimeout1/Success,07 failures and W03 incomplete remain unchanged.

## Read scope

Source reads: `review/working/freeze_app29_integrated_driver_v2.py`1–459 and498–560;
runner `review/working/run_app29_integrated_driver_validation_linux.py`455–540,584–637,
plus numbered function/call-site locations. The unrelated truncated freeze-writer excerpt
was not needed for this recommendation. Admin4f43288 validation/merge is primary-supplied
context, not independently queried here. No code/test implementation, build, network,
runtime action, source edit or new framework was performed.
