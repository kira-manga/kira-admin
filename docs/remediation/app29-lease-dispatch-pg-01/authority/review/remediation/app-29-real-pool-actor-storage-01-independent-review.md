# App29 actor storage01 — independent prerequisite-delta review

2026-09-11 UTC · `/root/backend_04_independent_review` · **NONAUTHOR / SOURCE ONLY**.
**ACCEPT the exact one-file source prerequisite for primary binding. No new blocking
source issue found in this delta.** This does not approve not-yet-authored fault tests,
compiled reflection behavior, core C1 correction, execution or aggregate pool acceptance.

## Exact bytes and preservation

`P = review/working/app-29-real-pool-actor-storage-01/`.
Only owned path: `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLifecycleFrames.kt`.
Backend49da `49da0919d9ec3091cb7bb041009dc9bd5f3e090f` remains **PRIVATE / NEVER PUBLICLY PUSH**.

| Artifact | SHA-256 |
|---|---|
| `P/manifest.json` | `2cf95e5f04b8e4d043a213a0103d6ce197c2f1703d0b777ab7fe5613f4611517` |
| `P/AUTHOR_REPORT.md` | `deafe9ee21c07edef0f8292513b3002217d4c3347a4277c8289b9d09088bfc9c` |
| Before, 4407 bytes | `a463529fce5a770165f6f9d0673ae640ece4734942baf68b8bca4c039dd512d8` |
| After, 4530 bytes | `2cbd7a055d12000953c37301a7d08839df739d391b4fafa453e8acb62944963e` |
| `P/frame-storage.patch`, 1741 bytes | `e20ae01f5b838439fdd7d340c850d6c54d58426f01b446596afd947ed84e50ea` |
| `P/SHA256SUMS` | `43d520ce562e025bd5300e6c3eda4cf5200a86734ed8399ac7938209c505aa52` |

Independently checked declared lengths/hashes, reconstructed the single unified hunk
in memory to the exact after-image, and regenerated the labeled GNU diff byte-for-byte.
Before equals the immutable `app-29-real-pool-actors-resumed-01/source/` snapshot; after
equals the authorized current owned path. Prior manifest remains
`6776e02a52c52535ba05c92d08adac218c204866f360019bd3ec053a7ef362e1`.
All5 new and all8 prior packet checksum entries match. No packet was changed.

The other four actor paths match both their prior frozen snapshots and current files:

| Basename (same persistence package, tests under src/test) | SHA-256 |
|---|---|
| `PoolLifecycle.kt` | `def7c6ef36145b6d1dcf71342a5e6c1956f6f40055464e231e946eff05ade9f2` |
| `PoolActorCustody.kt` | `0e45d75ee8a2421b6db238ced31298b7a5012db4ad3232e8675ae0f889e8c857` |
| `PoolLifecycleTest.kt` | `f5f194f46eddb89b32ba1142fcbedd5617255abae5b3ffe0bd507b26449c0665` |
| `PoolActorCustodyTest.kt` | `7ddc9fac7597febfb42de44c041e4c2ccfdc01bc864e973346738a5ffd0209fa` |

## Bounded source assessment

- After89–96 keeps **one global PoolCallFrames singleton**, one private `Storage`
  instance and one ThreadLocal key. The holder adds one singleton-initialization
  allocation, not per-pool/per-frame/per-call storage or another lineage.
- All seven get/set/remove call sites now dereference `storage.current`. The exact
  caller/top/parent comparisons, short-circuit evaluation and absent-parent `remove`
  semantics in install/restore/restoreUnadmitted are unchanged. No key alias is cached.
- No membership, count, phase, issuance, entitlement, budget, custody or shutdown-close
  transition changes. No public setter, injection callback, constructor parameter or
  test API is added; `Storage` and `storage` remain private.
- The agreed source seam is usable for the existing ordinary-instance-field reflection
  technique: read `PoolCallFrames`' declared `storage` field, then that instance's declared
  `current` field. Tests need not write the outer static-final singleton property.
  Every production access uses that instance field. Actual compiled field access,
  interceptor delegation, genuine throwing-entry/acquisition-end behavior and exact
  restoration remain unexecuted test obligations, not established by this review.

**Execution NONE; no test source changed.** This was only the tiny prerequisite review,
not a repeated actor/core audit. Prior actor counts remain source-only; no pass credit
or new lifecycle proof follows. Core C1 and the independent core report
`41f1309fb9cd10909065cb87fa52cdf56849984e0ff620703ff2663dd0427c70` remain separate.
Only this new report was written: no product/native/test edit, build, static checker,
formatter, JVM, service, CI, artifact replacement, commit or push. Primary owns the gate.
