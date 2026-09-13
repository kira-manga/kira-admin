# W03 tiny test-compile correction — independent note

2026-09-13 UTC · `/root/w03_connected_ownership_review` · private0600.
**No blocking finding; source concurrence for this two-file +7/-5 correction only.**

Reviewed author report `15196f2502215cf465858e45813b824e61a4c5c36eda11e4403f7dd790fc85f9`
and the actual1,978-byte incremental patch
`771bd1533698e196ea726c4db821b4f7ed3ce0159ef6ff5d09983611baf4f22e`.
Both files are under backend `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`:

| Current file | Independently verified after SHA-256 |
|---|---|
| `OrdinarySourceGrantCleanupFixture.kt` | `ce0110d46c15fefe5e152d6aa4be30d1c0539247f468c54d4cb15969db52418b` |
| `OrdinarySourceGrantCleanupOwnershipIT.kt` | `a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557` |

Both preimages equal the Linux02 freeze; the passive preimage→current diff equals the patch.
All other476 retained paths, including every retained production file, remain byte-identical;
none missing. No full W03 re-review or Git observation was performed.

- Fixture's concrete `DriverManagerDataSource` receiver requires non-null credential arguments
  under the selected strict Spring/Kotlin contract, as the retained compiler diagnostics show.
  Changing the anonymous override to `String, String` matches that supported contract. Both
  overloads still increment the same counter once and forward to the same reader overload with
  the original arguments. No cast, `!!`, substituted/default credentials or null-credential
  oracle was introduced/removed. This does not claim support for null credential calls.
- OwnershipIT changes only argument-list wrapping. Body flag/zero result, dispatch, catches,
  real tail/latch/thread custody, assertions and time limits are unchanged. No new suppression,
  behavioral branch, test selection or production change.

**Approve the proposed reuse scope:** rerun normal compilation, the same five still-unrun
nonDB classes and aggregate `ktlintCheck`; omit another Detekt invocation for this exact
nullability/layout-only test delta. Linux02's successful Detekt observation is retained prior
byte-set evidence, **not a fresh Detekt PASS for these changed test bytes**. No Detekt rule,
configuration, baseline or suppression change is authorized; further relevant edits invalidate
this narrow reuse decision. No runner edit or unsupported single-Ktlint-task selection is needed.

Verified Linux02 raw result SHA-256
`5cc6b123fa3f88ce8adba7e1a67873ba67f07334c7f494dd374059fa8a6b3fac`, its retained reports
(including empty Detekt results), and primary investigation
`ec1bbfd8f953d645a823f0e5adc92d96b2c3875b3476b64d32320b88d43cb952`.
Linux02 executed **zero tests**; neither the five classes nor connected real-DB oracles gain
execution credit here. Reviewer ran no build/test/static tool, helper, Git/CI, service or agent;
only passive reads/comparisons and this report. Primary owns refreeze/admission/execution.
No W03/P3/runtime acceptance; keep private backend ancestry/evidence unpublished.
