# Kira remediation — resume here

**Owner-requested stop/checkpoint, 2026-09-08. NOT READY FOR PRODUCTION.**
This handoff preserves unfinished work; it does not approve a release, merge or issue closure.
The current agent finished development07, collected its failures, stopped its workers and is
publishing WIP branches. Resume implementation only when the owner asks the next agent to continue.

## 1. Authoritative state and progress

Read in this order; do not reconstruct the campaign from chat or restart completed investigations:

1. This file and `REMEDIATION_TRACKER.md` (especially `NEXT EXACT ACTION`).
2. `REMEDIATION_DECISION_GUIDE.md` and `working/final-live-issue-bodies-20260904.json`.
3. `REMEDIATION_PROGRESS_REPORT.md` for the nine selected App #29 packages.
4. `remediation/app-29-clean-start-owner-amendment-20260908.md`.
5. Current integrated plan/agreement, development07 manifest/results and the supplemental independent
   review listed below. Historical reports are dated evidence, not approval of later trees.

| Work | Verified status | Remaining |
|---|---|---|
| Historical audit | 2,233/2,233 files, 100% | New final audit after remediation |
| Historical issue second pass | 154/154, 100% | Reverify changed code/fixes |
| Integration branches created | 5/5, 100% | Issue fixes have not been integrated |
| Selected issues delivered/merged | **0/152, 0%** | **152** |
| App #29 locally accepted packages | **2/9, 22.2% (unequal packages)** | W03 active; W04/W05/W07/W08/W09/W10 unstarted |

W01 domain rules and W02 additive V14 schema have historical local acceptance. W03 has substantial
unused persistence/driver work but **no accepted complete package**. There are **no complaint backend
APIs, mobile replacement, Admin moderation replacement, Firebase retirement or production migration**.
The WIP checkpoint commits are transfer/durability, not additional delivery credit.

Issue queue: App106 (one active), Backend29, Admin6, Source Engine5, Web6. All selected LOW issues
remain implementation work. Original GitHub issue references, severity and closure proof are retained
in the decision guide and tracker. Check live issue state before acting; do not duplicate findings.

## 2. Binding owner decisions

- App #29: backend-owned authenticated complaints/feedback/moderation; Android/iOS consume the new
  backend contract. Remove old complaint Firebase code only after verified replacement/retirement.
- **W06 SKIPPED:** start the backend with empty complaint history. No Firestore export/import,
  reconciliation, adoption, recovery or replay of old complaints. No authority to read/delete old
  production records. New-backend-data backup/recovery and installation recovery remain required.
- App #2: explicitly accepted risk; leave unchanged, no disguised architectural fix.
- App #46: zero active sources may warn but **must not independently block a Store release**.
- All47 disproved candidates stay untouched unless new concrete evidence is reported first.
- Per-issue branches, primary investigation, written plan, independent authoritative research and
  regression review, agreement, implementation, meaningful tests, independent actual-diff reviews,
  integration merge and post-merge checks remain mandatory. Approved delegated model: GPT-6-Astra/max.
- No deployment, Store upload, signing operation, main merge or issue closure was authorized by this
  checkpoint. Never expose the workspace root `.p12`, `.env`, Firebase configs or signing material.

## 3. GitHub storage and repository branches

The workspace root is **not a Git repository**. App/backend/web are public, Admin/source-engine
private. Complete cross-repository evidence is therefore stored **only in private `kira-admin`**:

`docs/remediation/checkpoint-2026-09-08/`

That directory contains this handoff, a source/branch ledger, a compressed review evidence archive,
per-file hashes, explicit exclusions and a non-overwriting restore/verify script. Every repository
has `docs/REMEDIATION_HANDOFF.md` pointing there. Do not copy the private archive into a public repo.
The archive retains trackers, all issue decisions, plans/reviews, research, failed and passing raw
results, exact source snapshots, validation tools and unfinished drafts. Excluded secrets/signing,
caches, generated outputs and disposable duplicate worktrees are inventoried; exclusions are not
newly waived audit gates. Required pinned local source-engine dependency artifacts are retained.

| Directory | GitHub repository | Resume branch | Pre-checkpoint source HEAD |
|---|---|---|---|
| `Kira manga/` | `kira-manga/kira-app` | `remediation/app-29-backend-complaints` | `c0db2f63c916932dbed1a3314c9a06d30c1696b5` |
| `kira-backend/` | `kira-manga/Kira-backend` | `remediation/app-29-backend-complaints` | `c8bdff9a8acebb7c8e8ce40c65b8c7315ef9c014` |
| `kira-admin/` | `kira-manga/kira-admin` | `remediation/app-29-backend-complaints` | `d4b8e6b33a1fc1f209dc8faf8eb4bdd7615459e2` |
| `kira-source-engine/` | `kira-manga/kira-source-engine` | `remediation/campaign-handoff-2026-09-08` | `fc55c149398068d1f47c2fb08597dbc08f0bf28a` |
| `kira-web/` | `kira-manga/kira-web` | `remediation/app-29-backend-complaints` | `b8a632c1a19c3370b66728d1e31dbade9687782e` |

All five integration refs are `remediation/production-readiness-2026-09-04`. They retain the starting
baseline and are **not advanced to incomplete WIP**. The source-engine handoff branch is docs-only;
no App #29 engine implementation is implied. The App baseline commit preserves prior owner WIP,
not a remediation fix. Admin's two pre-existing `.DS_Store` files stay local and untouched.

Use the committed `repository-checkpoint.json` for published source/checkpoint identities. For its
own containing Admin commit, use `git rev-parse HEAD` and the archive digest, not a fictitious self-
referential SHA. Verify `git ls-remote` against local heads before continuing. Never force-push/reset
owner changes or merge a checkpoint merely because it exists on GitHub.

## 4. Exact completed development07 cycle

Manifest: `working/app-29-w03-integrated-driver-development-07/manifest.json`
SHA256: `3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`

Results: `working/app-29-w03-integrated-driver-development-cycle-07/` and sibling `-runtime/`.
Primary collection verifies348 source hashes,77 snapshots,10 reports,11 retained classfiles and all
five pre-checkpoint repository identities. **138 tests:136 passed,2 failed,0 errors/skips.**
Lifecycle62/63, real PostgreSQL47/48, Timer17/17, oracle controls10/10. All10 newly added cases and
all8 existing TLS cases nominally pass. These four filtered suites are **not full regression**.

All115 child-cleanup receipts (including negative-control children),64 keytool exit/join receipts,
ephemeral material deletion and immediate stop/capture/clean/stop were collected. Both build output
paths are absent; the dedicated disposable PostgreSQL containers and Colima profile stopped.
Do not poll/repeat development05/06/07 or report a failed cycle as a pass.

### Failures the successor must investigate/fix

All Kotlin paths below are under backend
`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`.

1. **D13 `QUALIFIED_NONBINARY_BOX`, queryTimeout1, deletion:** fails at
   `PgLifecycleDatabaseCases.resultReceipt:56` after retained-primary evidence, before the parent
   first-server gate completes. The actual returned variant/reason was not captured. Record safe
   sealed result/reason/receipt plus actual opening/gate state and trace the original request.
   Do not infer BUSY/timeout/server failure, add retries, reset the2000ms budget, suppress queryTimeout
   or relax expected Success. Exact run cause remains **UNDIAGNOSED**.
2. **`QUEUED_AND_CANCELED_BOUNDARIES`:** `PgLifecycleTimerCases.boundaries:65` treats nullable,
   best-effort retained counts from two mixed snapshots as conclusive1. Production
   `PersistencePhysicalCompletion.retainedCount:145–151` legitimately returns null on G contention.
   Boundedly obtain conclusive/exact-entry evidence while the genuine same-Timer hold remains;
   retain queued/canceled tasks, pre-release PENDING and all post-release disposal assertions.
   This is a proven source-level false-failure opportunity, not a uniquely proven cause of07.
3. Ktlint `PgLifecycleScannerGate:13:22`: class-signature formatting.
4. Detekt `PgLifecycleDeadlineCases:8:9`: NestedBlockDepth.
5. Detekt `PgLifecycleDatabaseAssertions:18:21`: ComplexCondition. Preserve the essential
   **rawReturned AND construction RETURNED** readiness conjunction and original bounded wait.

Use narrow formatting/helper extraction, no suppressions or weakened assertions. Development06's
raw-return/construction race was a proven fixture error and is corrected in07. Its different
DELETION_PROGRESS_DEADLINE failure remains historically undiagnosed; a07 pass does not explain it.

### Independent review and approved design

- `remediation/app-29-w03-integrated-actual-regression-review.md`
  SHA256 `cb586d1165a99c6776c734d39d92ae2b1d70f1ced923888ce5ecc5c86ca32852`.
  The separate07 supplement reviews all6 new/5 modified tests and raw outcomes. No additional
  confirmed production defect/false-pass found; this is **not final acceptance**.
- `remediation/app-29-w03-integrated-technical-source-review.md`: source review; its author wrote
  the15 database test files and explicitly excludes those from independent approval.
- `remediation/app-29-w03-integrated-driver-completion-plan-v1.md`, SHA256
  `48bbd5582ca369e0bb0aa5d7d6970d40e9634267a8a0439209e095ab912daf92`.
- `remediation/app-29-w03-integrated-driver-v1-agreement.md`.
- Frozen D1 revision2 and C6 plans referenced by those documents. **Keep ALL D01–D15/C6-01–12 gates.**

No new helper-plan loop is needed for already approved lifecycle work. Timer-A02 component acceptance
and its2749/89 test evidence are preserved; do not repeat unchanged helper gates as new progress.
Full baseline-plus-increment regression and both final independent actual reviews remain unfinished.

## 5. Two saved supplemental drafts — do not confuse their readiness

### D05/database: PARTIAL — DO NOT APPLY

`working/app-29-w03-integrated-database-fault-draft/`
Manifest SHA256 `063f3785d29430b66307a8ce97576d97081b2fdbc272fb2e391625ac1cd14a33`.
Read `HANDOFF.md`, `manifest.json` (`import_allowed=false`) and the deliberately named
`primary-import-PARTIAL-DO-NOT-APPLY.patch`.

Seven partially edited files plus exact15-file baseline are preserved.35 proposed identities/
70 prescribed attempts are **zero completed new vectors**. Parent relay/protocol/fault coordination,
role-query/observer evidence and weak no-raw cleanup are unfinished. The draft handoff gives exact
functions/steps. Do not import the incomplete patch, copy baseline files over newer fixes, or claim
that authored test declarations add coverage. Finish and independently review it before refreezing.

### D06/negotiation: authored draft, unreviewed and unexecuted

`working/app-29-w03-integrated-negotiation-test-draft/`
Read `DRAFT.md`, `text-checks.json`, `import.patch`, research pins and `PRIMARY_TRANSFER_MANIFEST.json`.
Primary transfer-manifest SHA256 `f0ed266e7228d01a024b8152c9943e61a90ce330144d02047ee0b39ecac7fc24`.

The author reports7 new files,3 minimal imports and26 lane cases; only text inventory/dry patch
checks ran. No compiler/runtime or independent approval. The final author response did not finish;
primary created an explicit transfer inventory, **not import authorization**. Inspect all actual
files and reconcile the3 hunks against the newer backend before review/import/new freeze. This is
not a completed package or an executed D06 gate. Do not restart the entire earlier TLS investigation.

All delegated tasks are stopped. Another agent must use these files, not depend on old agent IDs.

## 6. Remaining implementation, not optional scope

After lifecycle gates: finish private Hikari/JDBC/Spring transaction ownership and atomic capacity
SQL/audit/scoped-step-up; full W03 regression/reviews. Then W04 durable operations/new-data recovery,
W05 authenticated APIs, W07 mobile credentials/transport, W08 screens/lifecycle/accessibility,
W09 Admin/disclosures, W10 verified replacement/retirement/removal and whole-issue validation.

Legacy-only W01/W02 placeholders need a separately reviewed compatibility cleanup. **Do not rewrite
accepted V14, renumber persisted counter positions or remove new-data recovery** just to implement
clean-start. No old Firestore data may be imported. See both clean-start impact reviews/collection.
Other selected issues keep independent branches/reviews; App #29 does not silently close Backend
#28/#29 or App #30/#31. Follow with full five-repository regression and a fresh final audit.
External Store/device/APNs/FCM/production DB/Redis/storage/DNS/TLS/organization/legal gates remain
explicitly unverified; never substitute localhost fixtures or compilation for those results.

## 7. Restore and verify without repeating/skipping work

On the existing workspace, read current `review/` directly; **do not overwrite newer files** with
an archive. On a fresh machine clone all five repositories at the branches in section3, preserving
these directory names. Fetch the integration refs without merging. Read each nearest `AGENTS.md`.

From workspace root:

```sh
python3 kira-admin/docs/remediation/checkpoint-2026-09-08/restore-review.py \
  --workspace "$PWD" --verify-only
# Fresh workspace only; refuses symlinks, traversal and differing existing files:
python3 kira-admin/docs/remediation/checkpoint-2026-09-08/restore-review.py \
  --workspace "$PWD" --restore
```

Compare all348 backend hashes from07 before editing. Later commits contain documentation/checkpoint
metadata but no post07 Kotlin fix; changed HEADs do not invalidate identical frozen file evidence.
**Historical validation wrappers reject changed Git HEAD/status by design. Do not rerun07 or alter
its immutable manifest.**

Important tooling seam after checkpoint: `freeze_app29_integrated_driver.py` historically discovers
Timer-A02 paths plus **uncommitted** paths. Once WIP is committed this misses65 integrated additions.
Before the NEXT freeze, adapt inventory discovery to seed **all348 development07 source paths plus
new changes/explicit removals**, or enumerate the full issue diff from backend baselinec8bdff9…,
then verify no committed integrated file disappeared. Keep Timer-A02 baseline comparison and all
snapshot/task/tooling/repository-ref checks. This is evidence-tool maintenance, not a waiver.

Use a **new** candidate and result directory (08 or next unused), after fixes/draft reviews. Preserve
old failure reports. The07 exact tasks are recorded in its manifest: four selected suites plus
unfiltered `ktlintCheck detekt --continue`. Full later regression is additional, not replaced by them.

Original tooling uses Java21, macOS `/usr/libexec/java_home`, `/usr/bin/python3 -B`, Colima and a
private Gradle home/explicit pinned source-engine dependency route. Homebrew Python's XML extension
was broken on the original host. Cached Gradle/toolchain downloads are not uploaded; provision them
on a new machine rather than weakening dependency verification or falsely claiming offline success.
Required small `working/app-29-w01-local-dependencies-20260905/repository/` artifacts and their hash
manifest are included. Never substitute broad unpinned mavenLocal resolution.

Historical Colima ownership receipts describe the original host only. On another host, first verify
that the profile/socket is absent or owned by this task; create/record a new dedicated runtime if
needed. Never stop/delete an unrelated same-named profile/container. Retain the wrapper's **8GiB
free-space prerequisite** and bounded CPU/RAM; do not lower it to force another batch through.

## 8. Permanent build/resource hygiene

After every owned Gradle output-generating batch: finish verification, **immediately stop its own
Gradle home with `./gradlew --stop`**, retain required logs/reports/artifacts, scoped clean (or
`./gradlew clean` where safe), stop the clean-task daemon and verify output/process absence. Use
isolated ownership; no global process kill, cache purge or deletion of foreign tasks' files.
Preserve source, dependency verification metadata, signing/configuration and required deliverables.
Stop owned Node/test/service/VM workers and delete only unneeded outputs after their tasks too.

The next agent's first implementation action is section4's failure/static investigation, with the
freeze-inventory adaptation before its new build—not a repeated full historical audit, not a W06
import, not a package acceptance and not an integration merge.
