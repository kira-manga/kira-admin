# W03 source-grant cleanup — resumed source-only handoff 01

2026-09-13 UTC · `/root/w03_cleanup_author_resume` (former Backend02 slice).
**AUTHORED / UNEXECUTED; not independent acceptance, W03 completion or execution admission.**

Private root: `kira-backend/`, primary-bound HEAD
`6db944871c1584bd6a1f28263e8010cadd766fab`. Never publish this ancestry.
This handoff binds only the three cleanup-owned files, not the concurrent core worktree.
No fresh HEAD assertion or whole-root freeze is claimed.

## Resume disposition

The two main files and six cleanup tests were already complete in the retained packet
`review/working/app-29-ordinary-source-grant-cleanup-implementation-01/` (**E** below).
Read the actual files, selected owner docs, primary plan, both plan reviews and admission;
reconciled the consumed fixture API with the resumed core author.

**No product source was changed on resume.** Current bytes exactly match E's authored
snapshots and source manifest. E is preserved unchanged; this requested handoff is the only
new file written by this resume. No tracker, core-owned path or unrelated WIP was edited.

Binding documents under `review/remediation/`:

| Document | SHA-256 |
|---|---|
| `app-29-ordinary-phase-connected-primary-plan-01.md` | `caa1cd86a8598c0b03ee96f7e1832e5eeedfd4aab1f92bf830aefe3a85c2717e` |
| `app-29-ordinary-phase-connected-technical-plan-review-01.md` | `977b0a9810e28fce60a4ef4120c420f849f3ce25471fa67aa7ed364dcc460490` |
| `app-29-ordinary-phase-connected-regression-plan-review-01.md` | `31d3af5dcda1d8abdbb18c099c3d3835f2350b44df942b111682c26e492e2ea2` |
| `app-29-ordinary-phase-connected-implementation-admission-01.md` | `ebf90de2a6759371f82fc94abd77410e4c3e8c8bae69938cecc0b23c827e8458` |

P3 `app-29-w03-plan-p3-frozen.md` remains normative; E's `inputs.sha256` retains
its binding and the existing source/service/schema inputs.

## Exact path and diff evidence

Paths below are relative to `kira-backend/`. All three remain untracked additions;
read-only `git status`/`ls-files` observations did not mutate Git. E's `before.json`
retains the original absent-at-admitted-commit observation. Resume-before and resume-after
hashes are identical, so the resume product diff is empty. The original slice is exactly
three added files / 231 added lines, with no changed existing file:

| Path | Lines | SHA-256, current and retained `E/after/` snapshot |
|---|---:|---|
| `src/main/kotlin/me/manga/kira/backend/security/SourceGrantCleanup.kt` | 12 | `020a40ee44d38611bdaed358519472ebbb7e29a18eb58be411c184fa0086eaa0` |
| `src/main/kotlin/me/manga/kira/backend/security/JdbcSourceGrantCleanupStore.kt` | 46 | `3521657245fd5922718c21e703120bae9bac9664bdab331564170f53714ce689` |
| `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/OrdinarySourceGrantCleanupIT.kt` | 173 | `4c265dbc8e073896f395f5140be1ad96906bf89749a751d3452e144d67fdad31` |

| Retained artifact in E | SHA-256 |
|---|---|
| `owned-new-files.patch` — exact complete three-file diff | `e3c72ff1b28ce5a45ad740aa3991056ab94b066de2513769e0a374071dbfa23f` |
| `before.json` — original baseline absence | `0ee5852ef00bbaa0834276d77b1187c9f841dd74ceea136afbf25d46806edde5` |
| `source.sha256` — exact product path manifest | `64e60c60cdf8ad1f74918a7c46540263cd543d1c0bbd72d1b6d42561a2986b47` |
| `tests.json` — exact six method identities, authored/unexecuted | `72ff12b955e514b29a7b05fe9a61fbdc66bbe08d0afa001313506adadfe46299` |
| `SEAL.sha256` — original packet member manifest | `f84fb92f278d51528fe90f7e4c7a75f93a0c4ab0ade6fbd625f3265a78709c6e` |

## Fixed primitive and shared contract

- Internal `SourceGrantCleanup` exposes only
  `deleteEligibleSourceGrants(cutoff: Instant): Int`.
- Internal, non-bean `JdbcSourceGrantCleanupStore` first invokes the core-owned
  `requireSourceGrantCleanup(jdbc: JdbcTemplate)`. No alternate manager, authority,
  resource lookup/fallback, or physical owner is introduced by the store.
- One fixed CTE selects source-scope AND (expired at/before cutoff OR used), orders
  by UUID, and takes at most 50 with `FOR UPDATE SKIP LOCKED`. DELETE joins only those
  IDs and repeats both source scope and the parenthesized eligibility predicate.
  Both predicates bind the existing `SOURCE_ADMIN_MUTATION_SCOPE` and the same
  `Timestamp.from(cutoff)` value. There is no exhaustion loop or caller-selected SQL/scope.
- Only a count checked in `0..50` escapes. No proof/ID result, production test table,
  fault switch, user/counter/fence lock, scheduler, controller or schema edit is added.
- Core retains the sole named `cleanupSourceGrants(): Int` entry, sampling its
  injected trusted Clock once. The store's Instant is internal expiry plumbing,
  not caller authority and not the monotonic work/cleanup clock.

On this resume the core author `/root/w03_core_author_resume` explicitly confirmed
the consumed fixture subset API frozen: `withOrdinarySourceGrantCleanup`, `cutoff`,
`sourceStore`, `newExecutor(store, clock)`, `seedGrant`, `grantIds`, and `lockGrant`.
Names and semantics stay; separate optional ownership-test helpers may be added.

Observed fixture hash remains
`24c953c71eab95982ee9a035f38b68820ec253e4a3460e32c275d26a0c09b47a` for
`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/OrdinarySourceGrantCleanupFixture.kt`.
It supplies the existing owned PG pool, real ordinary JPA EMF/manager, committed
Flyway schema and independent reader/lock connections. No fixture was duplicated.
The now-present executor was observed at
`3234ea5e809f5f26432ac70d383ae96bf2633921385583230c13e6d2e1b9afa8` for
`src/main/kotlin/me/manga/kira/backend/complaint/infrastructure/transaction/OrdinaryPersistencePhaseExecutor.kt`.
These are API observations, **not the core author's final source freeze**; the old E
packet's note that the executor was absent is historical, not this resume's status.

## Exact authored test methods — all UNEXECUTED

Class: `me.manga.kira.backend.common.infrastructure.persistence.OrdinarySourceGrantCleanupIT`.
Every method uses the shared ordinary-JPA fixture and independent row-set readback:

1. `source expiry includes the cutoff and used unexpired grants without deleting the next microsecond`
   — cutoff−1µs/equal/used-unexpired delete; cutoff+1µs unused survives; next call returns zero.
2. `mixed scope cleanup preserves active source grants and every complaint lifecycle`
   — only the two eligible source rows delete; active source and all five complaint variants survive.
3. `one invocation commits only the first fifty eligible UUIDs and leaves the remaining batch`
   — reverse-insert 70 eligible IDs; exact first 50 delete, remaining 20 and protected low IDs survive.
4. `an independently locked earliest eligible grant is skipped while fifty other rows commit`
   — hold a real independent row lock throughout the call/readback; IDs 1/52 survive among 52;
   a separate post-release invocation removes the last two. No worker/Future/sleep oracle.
5. `the trusted Clock is sampled once and its committed cutoff is durable to an independent reader`
   — counting/advancing Clock and narrow-port observer assert the original cutoff, one sample,
   real count 1, and the independently durable protected future row.
6. `a decorator failure after the real delete rolls back and preserves independently readable rows`
   — real count 2 and an independent pre-abort read precede a test-only deliberate failure;
   assert the abort marker, no dirty read, all rows restored after return, then successful continuation.
   Assertions stay outside the decorator so value-free core wrapping cannot hide a failed oracle.

These are authored oracles, not observations that transactions committed/rolled back or that
locks, sessions and ownership were reclaimed. No discovery/execution count or PASS is claimed.

## Remaining regression risks and handoff limits

1. The core must still establish exact phase/path/resource/holder/lease/operation checks,
   real ordinary JPA with one selected-manager acquisition authority, legal REQUIRED
   participation and pre-dispatch refusals. The adapter's gate call alone proves none of these.
2. Actual lower COMMITTED/ROLLED_BACK/UNKNOWN facts must remain separate from cleanup and
   generation-bound real lease/tail completion/refund. A returned count, logical close,
   afterCompletion, global-zero count or timeout is not that evidence. Shared 2s work/1s
   emergency budgets, accepted-but-undelivered/begin-failure custody, late/stale completion,
   and real blocking lifetime tests remain core-owned and independently reviewable.
3. SQL predicate/UUID/locked-row/precision semantics and real JPA/JdbcTemplate atomicity are
   still runtime-unverified. Final core/fixture bytes must be rebound before validation;
   API freeze is not compile, fixture teardown, native-profile or live-bean compatibility proof.
4. The live `JdbcAdminStepUpGrantRepository.deleteExpiredOrUsed` remains unbounded and
   all-scope; neither it nor `AdminStepUpService` was rerouted. Their hashes and V12/V14
   still match E's original inputs. No token/TTL/one-time-consumption/status/API change is
   selected. Full password/step-up/audit/complaint-capacity work and the existing
   `AdminStepUpIT` compatibility sentry remain for their separately admitted lanes.
5. Production/UNKNOWN remain inert. W06/history work is excluded and NEWdata recovery is
   untouched. PG1 and existing 14+1/38 evidence remain separate; no native/liveness/full47,
   full-P3, deployment, consumer or Store qualification follows.

Only source/document reads, read-only Git observations, passive digests and this handoff
were performed on resume. **No build/compiler, tests/checkers, DB/container, CI, dependency
resolution, Git mutation/commit/push, network publication, worker or subagent was started.**
Primary owns the combined freeze and later execution admission; independent actual-diff
review remains required. This is an author handoff, not self-approval.
