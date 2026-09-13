# App29 W03 lease-dispatch Linux01 — independent static-correction review 01

2026-09-13. **PRIVATE / new review-only, non-author role.**

**Conclusion: source-equivalence concurrence for this ten-file correction only; no blocking
finding in the reviewed delta.** This is not a configured-static PASS, compilation result,
runtime approval, candidate freeze, execution admission or broader W03 acceptance.

I independently compared every correction hunk with the frozen Linux01 source and the live
files, read the surrounding ownership/finalizer boundaries, root/backend AGENTS.md and relevant
PLAN, SECURITY and COMPLAINT_DRIVER_LIFECYCLE documentation. I did not author the source,
tests, correction packet or earlier reviews. Only this new mode-0600 report was written.
No compiler, Gradle, formatter/static checker, test, JVM or workflow ran; no validation/application
workers, services, database resources or leases were created/acquired. No source, tooling,
tracker, Git history or existing evidence was edited; nothing was externally shared.

Backend HEAD remains `ccdbb28f6362117882501b4da040257be6fc1990`. Its original WIP remains
14 tracked modifications plus three untracked paths; the correction changes seven production
and three test files within that set. The author confirmed the sealed packet was stable.

## Exact review binding

Paths are relative to `/root/projects/Kira/`. `P/` below means
`review/working/app-29-lease-dispatch-linux01-static-correction-01/`.
All listed pins were passively rehashed; all 16 entries in the packet seal matched.

| Input | SHA-256 |
|---|---|
| `review/working/app-29-w03-integrated-driver-lease-dispatch-linux-01/manifest.json` | `dde01186ffb596c48207bb2ecd5564b68ce21511cf042007e15dab0bac624e2a` |
| `review/working/app-29-lease-dispatch-linux-01/result.json` | `1a1202fefb4034bf4133de572c295fd1d1d3efbbfab807e5ef9c45b5c4565d28` |
| `P/SHA256SUMS` | `30dff636b62884a1c925a1a1bb5165e3fee74dfc7cad91bc34165f6dc780db67` |
| `P/correction.diff` | `8332d30e9232ed9ed3ccefda8792f26b790bb2373aad78e0b48076af8d33c9c8` |
| `P/before.sha256` (all17) | `f71205a940318ab7b9d83ba98ec3249145b234672d0e328833a6d18784cdb861` |
| `P/after.sha256` (all17) | `5cce1bf6cd712a25fde2d9f7b9e1deb6ffb7d34d06e107092995d112200d3c59` |
| `P/source-disposition.tsv` (full before/after path mapping) | `78b828ff8c7ac8aaa6c0e932b779487c747741b2fa71b477c7bed573809fa4dc` |
| `review/remediation/app-29-lease-dispatch-linux01-static-correction-author-report-01.md` | `d6fc457a6556f69ead55367b14028e7971b61313b6bc032aaf0546ec7c2c5585` |
| `review/remediation/app-29-lease-dispatch-creator-independent-actual-diff-review-01.md` | `aa5bfc6822ca9c4330b499d322126da0cc3bb9a3954407fae3ff72875105682d` |
| `review/remediation/app-29-lease-dispatch-creator-primary-agreement-01.md` | `e082e0f991b3d472c173ebd83182dcf50ea3df87bc793de5f5507428cc3b28f7` |

`M/` expands to `kira-backend/src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`;
`T/` is the same package under `src/test/kotlin/`. These are the exact ten reviewed live files:

| File | Corrected SHA-256 |
|---|---|
| `M/PersistenceJdbcGuardCall.kt` | `8f01ed4e07207701fe9a7ed999e8cbe854633902fe1153e5e0fe376918f44457` |
| `M/PersistenceJdbcLease.kt` | `e22262871a9ad7e35f12b99d8c17615827e8e31294b7d2f7bb272b6bcc524693` |
| `M/PersistenceJdbcLeaseInvocation.kt` | `467ce125c4732f785ef0924a3474c64909f267a3922de446326bb0c43b05a1e6` |
| `M/PersistenceLeaseCompletion.kt` | `87ed0ed516ec98b8c9e86ceef1b264997cf127c4d084c4386ad1851019f1fb66` |
| `M/PersistenceProducerEpoch.kt` | `db0cea829ce45998d824eab1acbd67154217acac5bee532f8aa3261cbee73959` |
| `M/PoolLifecycle.kt` | `ca8ea5d15b8935d62564c9257abb6cd32340f995c535d5f40e4c4fea85c07ecf` |
| `M/PoolLifecycleFrames.kt` | `9230a12733c13823366adb833b28e4783f19d8426da774fffaea7b53646bc12f` |
| `T/PgLifecycleDatabaseProbe.kt` | `93b43e3bb48c0c7f1ea4f2e5588b7b81009592cf2546f074ab2b152eb6ba423f` |
| `T/OwnedPoolLeaseCreatorPendingProbe.kt` | `8b27c8c4a33da10b9675eb07b3634ca8a6e0ada8a7bef599c9024bef2b227764` |
| `T/PoolLeaseDispatchCreatorIntegrationTest.kt` | `db140c4c0e93a349608b6e05e80033fd07e298aee4c272932e78b6d69564ce4a` |

The generated in-memory baseline-to-live unified diff exactly matched `P/correction.diff`.
All17 before pins match the original manifest, and all17 after pins match live files.

## Material source-equivalence findings

1. **Five bodies move, not their authority.** `PoolLifecycle:576–609,668–766` moves only the
   five new outer bridges into existing `LeaseEntitlement`/`LeaseDispatchCreator` methods.
   Old outer `this` maps to the same retained `pool`; authority is explicitly **`pool.issuance`**,
   not the entitlement's possibly forged issuer. Exact acquisition, lease, epoch, guard,
   dispatch, caller and frame checks remain. Every admission/count mutation still uses the
   identical `pool.gate`. The outer declared-function count falls 44→39; no existing older
   helper is displaced and no new class/state/monitor/registry is introduced.

2. **Entry, restoration and completion cuts keep their order.** The creator's cached frame,
   guard/entitlement checks, entry claim, setup flag, call/dispatch retention, tail assignment,
   registration, pool-TL installation and counted activation retain their sequence. The new
   `restoreRefusedEntry(frame, setupReturned)` at709 receives the **already-read frame and
   original setup result**, from the same inner finally. Failure marking still precedes
   restoration; a throwing failure mark still reaches restoration. `restored=true` follows
   only a returned `refuseEntry`; its finally preserves failure/assignment precedence and
   never turns failed setup into a successful end. Counted end still restores TL before the
   same-gate positive-count check and exact tail end; only the existing scalar/frame
   publications follow that epoch cut. The uncounted refusal branch and sticky failed-tail
   path retain their checks, CAS claims, exception behavior and outstanding obligations.
   No terminal RETURN/EVICTION right is reserved or consumed by these movements.

3. **Short-circuit reads and outer adapters are preserved.** The split binding/failure/dispatch
   predicates preserve operand order and early refusal. `PersistenceJdbcLease:405–407`
   refuses the issuer before ended/caller/TL reads. `PersistenceLeaseCompletion:88` evaluates
   the epoch-tail term only after a successful checkout check, exactly as the old adjacent
   early returns. `PersistenceJdbcLeaseInvocation:36–40` merely braces the same conditional
   declared throw; Error propagation, existing outer-failure preference and retained failure
   are unchanged. GuardCall/Epoch/Frames changes are signatures/layout only. The unchanged
   connection/descendant outer finally scopes still enclose the guard and failure adapters;
   the exact epoch ledger and lower-native refusal/actor boundaries are not widened.

4. **Test assertions and real caller placement survive extraction.** Pending-probe
   `verifyCaller:101–140` executes inside the same original Thread's try/catch; result
   publication still follows all original assertions and `fault.use` cleanup. Selected-fault
   publication, release/join finally, retained-state checks and RETAINED/EXIT protocol remain.
   At273–298 the pool predicate still reads caller→real TL→selected frame→null guard→mode;
   the core predicate still reads caller→null guard→real TL→creator call→mode. Neither adds
   a TL read or eagerly evaluates a formerly skipped operand. Integration-test helper179–192
   contains exactly the original twelve assertions, in order, at the old call position69
   before scope/gate/shim creation. All actual Worker/drain, terminal-right, epoch-tail,
   adapter, cleanup and negative-oracle assertions remain. Other test edits are layout or
   braces; named methods, nine ordinary tests and eight enum rows are unchanged. The earlier
   review's visibility correction was already in the frozen baseline and remains intact.

No waiver, new/expanded suppression, deadline change, configuration relaxation or weaker oracle
appears in this delta. `build.gradle.kts`, `.editorconfig` and `config/detekt/detekt.yml` remain
at `8b6116173f5a5fd76de7c9654685754631e2df1a480a692082995b3122fb7aa0`,
`ecc589d2ee57adaacd3e951b625a6f4ad31f6ebc41f354e332cf0b9b39f2c6cd` and
`509eb13c3915934d49a3de84dcb5332ff372deee0326c6aaceeed4c2a0b38760` respectively.

## Preservation and minimum next checks — primary-owned, not authorized here

- Independently rehashed **all481 live inventory paths**: none missing, exactly ten changed,
  471 original hashes retained. All214 retained original source snapshots still match.
  Development07 manifest `3effe74b4b9daa5198a7ce24347e195da495bf26aeed3aa9519820dd917e4a6a`
  has all348 keys retained in the unchanged original manifest. Any new candidate must retain
  **all481 original keys and all348 seed keys** and preserve historical source/result bytes;
  do not reduce inventory to this correction or rewrite previous evidence. Seed-key retention
  is not a claim that historical seed bodies equal the current implementation.
- Minimum local validation: fresh normal complete `testClasses ktlintCheck detekt --continue`
  with the existing pinned configuration and primary-admitted private tooling. No rule waiver,
  filter, baseline, formatter shortcut or relaxed limits. The actual original result remains
  main+test compilation PASS, **Ktlint39+35=74 / Detekt19 FAIL**, tests0 **NOT_REQUESTED**;
  none of those compilation results validates the corrected bytes.
- Separately admitted private real-PostgreSQL verification: **creator17 + unchanged acceptance1**.
  Run the nine ordinary methods and eight enum rows of `PoolLeaseDispatchCreatorIntegrationTest`,
  plus only `OrdinarySourceGrantCleanupOwnershipIT.native commit failure stays unknown after
  Spring cleanup while authentic local quiescence permits only refund`. The latter file remains
  `a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557`; the existing owned-pool
  teardown file remains `b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322`.
  Preserve their assertions/budgets, actual JUnit identities and process closure oracles.
  The inert hosted preparation is not a launch authorization; binding/admission/results and
  acceptance remain with primary.

## Limits

This is source equivalence, **not identical bytecode, stack traces or runtime scheduling**;
forwarder removal/helper extraction necessarily changes call stacks. Corrected compilation,
configured metric/format acceptance, JUnit discovery, reflective seams, race timing and process
cleanup remain unverified. Existing stack assertions were preserved, not executed.

The earlier review's gaps remain: no separate retained-creator/null-tail-before-registration
injection; SQLClientInfo is a per-instance MODEL substitution; declared-stream failure is held
at its prerequisite finalizer, not inside the converter; not every mixed-top/Worker permutation
is tested. Registered-tail process rows must not be relabeled as absent-tail coverage. MODEL
fatal delegates are not native-commit evidence. PROCESS_ONLY/exit23/product_end=false never
becomes product completion. **PG01 remains20 PASS/1 FAIL**, with its actor/queue cause unmeasured.

No broad creator redesign, W03/full-P3/Native05/package/release completion, merge, deployment or
public push approval follows. W06 remains excluded; new-backend-data and installation recovery
remain required. Primary retains validation and acceptance ownership.
