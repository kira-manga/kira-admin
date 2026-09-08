# Kira remediation checkpoint — start here

**Owner-requested stop, 2026-09-08. WIP, NOT READY FOR PRODUCTION.**

Read [AGENT_HANDOFF.md](AGENT_HANDOFF.md) before doing anything else. It gives exact next actions,
owner exceptions, all remaining packages, current failures, draft readiness, review independence,
branch strategy, fresh-host setup and mandatory resource cleanup. **0/152 fixes merged (0%);
App #29 has2/9 unequal packages locally accepted (22.2%).** No complaint cutover is implemented.

## Contents

- [Repository checkpoint](repository-checkpoint.json): exact four published source checkpoint SHAs,
  all five integration baselines, and the identity rule for this containing Admin commit.
- [Complete handoff](AGENT_HANDOFF.md): do not repeat completed audit/helper cycles or skip gates.
- `review-evidence.tar.gz`: **10,113 files / 421,471,148 uncompressed bytes**,
  including authoritative trackers,154 issue decisions, approved plans/reviews, research, frozen
  source snapshots, raw failed/passing test/static/cleanup evidence, validation tools and both
  unfinished supplemental drafts. This PRIVATE archive must not be copied into public repos.
- [Archive manifest](review-manifest.json): per-file SHA256/size/mode and archive digest.
- [Exclusions](review-exclusions.json): 7,756 explicit key-shaped/generated/cache/disposable-worktree
  exclusions; no source or owner work deleted. Required pinned local source-engine inputs included.
- [Restore tool](restore-review.py): streaming verification, strict regular-file paths/hashes,
  no overwrite of different existing work, no archive symlinks, bounded per-file memory.
- [Transfer verification](TRANSFER_VERIFICATION.json): actual archive and restore controls, Admin
  precommit verification and cleanup; added outside its own immutable archive to avoid self-reference.
- [Final cleanup verification](CLEANUP_VERIFICATION.json): temporary transfer/scanner staging removed;
  required deliverables preserved and owned validation workers/generated outputs confirmed absent.
- [Workspace instructions](workspace-AGENTS.md): exact original root instructions. Never overwrite
  an existing `AGENTS.md`; on a fresh workspace only, copy this if needed. It is historical workspace
  guidance; the actual five-repository scope/roles are recorded in the handoff.

## Verify / restore

Use a workspace with sibling directories `Kira manga`, `kira-backend`, `kira-admin`,
`kira-source-engine` and `kira-web`, checked out as specified in the repository ledger.

```sh
python3 kira-admin/docs/remediation/checkpoint-2026-09-08/restore-review.py \
  --workspace "$PWD" --verify-only
# Fresh workspace only; preserves identical files and refuses different existing content:
python3 kira-admin/docs/remediation/checkpoint-2026-09-08/restore-review.py \
  --workspace "$PWD" --restore
```

Archive SHA256: `da94218f74eb0f5831241c8606c8f82142e49b818acfaff027a78f2efe77faab`. Compressed size: **67,457,187 bytes**.
Both the archive digest and every member are verified before any review file is restored.
Existing local `review/` may contain newer work: read it directly rather than forcing extraction.

The next implementation step is the exact development07 failure/static investigation, followed by
reviewed completion of D05/D06 and a **new** source freeze (the handoff documents a post-commit
inventory-tool seam). Do not rerun07 unchanged, import the partial D05 patch, mark W03 accepted,
implement skipped W06, merge integration/main or close any issue based on this checkpoint.
