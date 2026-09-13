# App29 — resumed-01 actor-only independent actual-diff review

2026-09-11 UTC · reviewer `/root/backend_04_independent_review` · **NONAUTHOR / SOURCE ONLY**.

**Disposition: no additional blocking finding in the assigned five-file actor diff.**
Source-level concurrence is limited to these exact bytes under agreement `f9046e74`.
This is **not** connected core/native approval, whole-tree movement authority, compilation,
runtime qualification, execution authority, delivery completion or W03 acceptance.

## 1. Exact scope and independent byte binding

Packet `P = review/working/app-29-real-pool-actors-resumed-01/`.
Source paths below are relative to `kira-backend/`, mirrored beneath `P/source/`.
Baseline `49da0919d9ec3091cb7bb041009dc9bd5f3e090f` remains **PRIVATE / NEVER PUBLICLY PUSH**.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLifecycle.kt` | 27810 | `def7c6ef36145b6d1dcf71342a5e6c1956f6f40055464e231e946eff05ade9f2` |
| `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolActorCustody.kt` | 11187 | `0e45d75ee8a2421b6db238ced31298b7a5012db4ad3232e8675ae0f889e8c857` |
| `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLifecycleFrames.kt` | 4407 | `a463529fce5a770165f6f9d0673ae640ece4734942baf68b8bca4c039dd512d8` |
| `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLifecycleTest.kt` | 25447 | `f5f194f46eddb89b32ba1142fcbedd5617255abae5b3ffe0bd507b26449c0665` |
| `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolActorCustodyTest.kt` | 22929 | `7ddc9fac7597febfb42de44c041e4c2ccfdc01bc864e973346738a5ffd0209fa` |

Packet authorities independently matched:

- `manifest.json`: `6776e02a52c52535ba05c92d08adac218c204866f360019bd3ec053a7ef362e1`.
- `AUTHOR_REPORT.md`: `0e56262daadc1dd9d43bada0b4507be3d666ad9ecacae564ba2676e0689249f1`.
- `actor-five-path.patch`: **95,906 bytes**, `ac23247f19b554c8c5103a2e7ff8ddd21c871f72fce428e2977d95099981c8a6`.
- `SHA256SUMS`: `08fc39d05ecf2260f7f89b4dada90f5259a170f3577701d760cd67bc24e8649c`; all eight listed files match.

Read all five after-images, the tracked patch hunks and the paused-to-sealed five-file delta.
Independently reconstructed the entire patch **in memory** against pinned Git before-images:
the two tracked before-blob IDs match; all three additions are absent at baseline; every hunk
context/count and after-blob ID matches; all five reconstructed after-images equal the snapshots.
All four patch-part lengths/hashes also match the manifest. No patch was applied to a checkout,
index or packet. Immutable packet files remain untouched.

Review authorities: implementation agreement
`f9046e74cd2a38b0a16ee55de1058c6bcc95dbd14f34e965e0b22ae510302138`, prior actor architecture
review `0c16b70b893e05c73e81ab1794001844de5ea465e8beae8d1f75e8ae61a636c1`, and paused connected
findings `4908b782e85c15d1ba1c3d783cb07868f75df609328f668b14bb7b457675499a`.
Supplementary caller/budget/test-support reads used private49da Git objects, not mutable core.

## 2. Actor-source assessment

**Sticky failures and caller-local restoration.** `PoolLifecycle.kt:265–318` records failed
entry setup before propagation and restores only the exact installed/prior lineage.
`PoolLifecycleFrames.kt:94–110` does not overwrite an unrelated current frame. Acquisition/
operation end claims ENDING, attempts restoration even after startup sampling fails, and
does not release its count on failed restoration (`PoolLifecycle.kt:322–372`). Successful
restoration with another failure still leaves the sticky fault. Frame completion and parent
clearing precede ENDED (`PoolLifecycleFrames.kt:68–73`).

The shutdown path separately retains the actual first RETURNED/THREW outcome, attempts flag
sampling/restoration and final frame restoration through nested finally blocks, and claims
ENDING before restoring its frame (`PoolLifecycle.kt:165–220`). Failed restoration does not
publish `attempt.ended`. The actor wrapper likewise records setup/body/restoration faults;
its scalar creator completion is **not** physical termination (`PoolActorCustody.kt:156–203`).
Moving pre-construction termination observation inside the guarded creation extent also
prevents its exception from being the sole failure record (`94–102`). These are source-path
observations, not an executed allocation/ThreadLocal-failure proof.

**Startup, shutdown and original budgets.** Factory installation is restricted to the exact
inert supported profile and failures seal business readiness (`PoolLifecycle.kt:28–80`).
All counted acquisitions/potential lazy initialization must end before the one physical
close claim; an early close returns INITIALIZATION_PENDING without consuming it (`119–163`).
Failed initialization cannot authorize a replacement constructor generation (`358–365`).
Handoff now supplies its acquisition's original budget (`94–100`); the first installed
shutdown budget survives duplicate requests and observations (`106–117,425–432`). This is
not a new bounded-disposal promise for synchronous stock Hikari close. The coordinated
`owner.observeShutdown(budget)` implementation is outside these five files and still needs
connected binding/review.

**C64, NEW and future rights remain conservative.** Reservation precedes ordinary unstarted
platform-Thread construction; admission/publication/sealing share one protocol. No inherited
application ThreadLocals, public start override, replacement executor or second physical
registry is introduced (`PoolActorCustody.kt:94–153`). Complete supplied Worker execution,
including its replacement finally, is authenticated by exact emitted Thread and one entry.
Only actual TERMINATED plus !isAlive, observed outside ownership/admission locks and followed
by an exact-generation recheck, frees a cell (`54–69`). Scalar completion summaries avoid a
chain of retired Worker graphs. C64 is the agreed custody allocation, not a throughput or
universal Hikari population bound.

Published NEW remains pending while its creator can act, then unproved rather than inert;
an earlier publication can still start after either seal. Termination does not clear a
previous fault (`72–85`). Business shutdown admission is deliberately distinct from final
factory sealing, preserving late authentic shutdown work; containment refusal is not normal
shutdown. Closed-population readiness requires zero acquisitions, operations **and future
lease entries**, plus the actual close tail (`PoolLifecycle.kt:247–250`). A prepared but refused
return/eviction operation retains its future right until explicit safe revocation, never
timeout-based erasure or re-preparation (`380–407,506–545`).

**Actor authority is not canonical native Life or successor authority.** Pool frames and
entitlements retain exact pool/issuer/original-Thread provenance. An incompatible nonnull
caller frame does not fall back to actor authority (`PoolLifecycle.kt:240–245`). However,
`isAuthenticPoolCaller` is only positive pool provenance (`82–86`): the connected core must
reject a stale lease credential first. The five files neither establish nor replace the
canonical `Life.cell` exposure/own-first-close ledger, retentionState facts or atomic epoch
transfer. A counted post-consent RETURN tail must not acquire successor native/abort/eviction
rights from actor membership. Those remain explicit core/native co-gates.

## 3. Prior connected findings are not closed by this packet

1. **Paused P1: post-commit Blob/large-object writes and auto-commit reset.** No transaction
   classifier/reset correction is in these files. The real LO regression and exact corrected
   core/native source still require independent connected review and execution.
2. **Paused P2: failed pre-entry RETURN disposition.** Actor retention of the unused future
   right is correctly conservative. The core must close business access, retain/request
   exact owned retirement, then safely revoke the unused entitlement on refused/throwing
   entry. It must not lose the prepared operation, strand an OPEN lease, erase the count,
   reprepare or restart the original budget. The actor API/model test is not proof that the
   connected lease now performs this correction.

These are remaining connected obligations, not newly discovered actor defects or a request
to broaden the actor author's five-file scope. Mutable core/native repair reports have not
been promoted to independent approval here.

## 4. Tests authored versus evidence

| Source | Methods | Expected invocations | Executed here |
|---|---:|---:|---:|
| `PoolLifecycleTest.kt` | 13 | 18 | 0 |
| `PoolActorCustodyTest.kt` | 12 | 16 | 0 |
| Total | 25 | 34 | **0** |

Source counts agree with the author: 18 new methods / 24 expected new invocations versus
private49da. No compilation or passing-test claim follows from those counts.

- Lifecycle tests explicitly cover original request/handoff budgets, future-right accounting,
  enclosing-frame restoration after a throwing model clock, and real overriding-caller flag
  sample/restore failures without replacing the first physical close outcome (`117–297`).
- Actor tests distinguish late creation after admission seal (`162–186`) from publication
  **before** seal followed by real start **after creator end** (`189–226`). The C64 NEW-retention
  and 96-generation tests require different custody facts, including positive actual
  termination before cell reuse (`111–159`).
- Stock Worker replacement and direct CallerRunsPolicy/discard anchors remain narrow stock/
  MODEL cases. The actual Hikari invalid-configuration startup test (`296–324`) does not prove
  successful pgjdbc initialization, partial-constructor cleanup, return or late assassin work.
- Revised cleanup ends/releases owned callers before pool close and supplements executor
  termination with actual actor/Thread termination checks. NEW is never started merely for
  cleanup. This is inspection of cleanup code, not an observed cleanup result.
- Forced ThreadLocal allocation/restoration exceptions were **not injected or exercised**.
  The author states this correctly; the new flag/clock tests do not substitute for that proof.

## 5. Remaining qualification and limits

Primary still owns the immutable connected core/native/actor assignment, source linkage,
affected real-Hikari/pgjdbc qualification and final acceptance. Real startup/return/assassin
behavior, safe unused-entitlement disposition, original observer-budget propagation,
canonical own-first-close obligations, transaction/reset outcomes and post-consent successor
protection remain to be connected and verified. Method23 requires its actual successor
native artifact/descriptor qualification; the old JAR cannot be relabelled as implementing it.
Existing native/core/custody/P3/W03 and historical evidence limits remain unchanged; W06 stays
excluded and NEW-data/installation recovery is preserved.

Only this report was written. **No product/test/native edit, build, test, static checker,
formatter, JVM, service, dependency download, CI, tracker edit, commit or push.** App29/
Backend11 WIP and immutable packets were preserved. This bounded manual actor review is not
an exhaustive audit or authorization to move the whole changing worktree.
