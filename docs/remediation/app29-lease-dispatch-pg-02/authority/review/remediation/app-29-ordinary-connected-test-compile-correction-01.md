# W03 connected phase — bounded test-compile correction01

2026-09-13 UTC · `/root/backend20_correction_review` · private0600.
**AUTHORED / UNCOMPILED / UNEXECUTED. Independent review required; no self-approval.**

## Exact feedback and scope

Only these two existing test files changed, both under backend
`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`:
`OrdinarySourceGrantCleanupFixture.kt` and `OrdinarySourceGrantCleanupOwnershipIT.kt`.
Private branch `remediation/app-29-backend-complaints`, HEAD
`6db944871c1584bd6a1f28263e8010cadd766fab`. Do not publicly publish this ancestry/evidence.
Root/backend AGENTS were reread; existing applicable owner/connected handoff constraints
remain unchanged. Existing app/backend WIP was preserved.

Actual `review/working/app-29-ordinary-connected-linux-02/` evidence:

- `result.json` SHA256 **`5cc6b123fa3f88ce8adba7e1a67873ba67f07334c7f494dd374059fa8a6b3fac`**.
- `validation.log` SHA256 `001039af7d3a9ea6f206300fa84f54769cf2763effbd0a054027321e182c8e3f`.
- Main compilation, main/script Ktlint and Detekt completed. Newly reached test compilation
  failed at Fixture **127:45,127:55**: nullable String arguments forwarded to non-null String
  parameters. Test Ktlint reported only OwnershipIT **382:35,385:21**, missing newlines at
  the `newExecutor` argument-list parentheses.
- **ZERO tests executed**; `test_evidence=null`. Validation exit1; retained result reports
  both stops0, five natural barriers,10 retained main classfiles, no test classfiles and
  outputs absent. This is retained evidence, not an author cleanup/build rerun.

## Diagnosed correction

1. Fixture's `reader` is concretely **DriverManagerDataSource**. Read-only Java21 `javap`
   metadata inspection of the existing Spring JDBC6.2.19 artifact confirmed that its
   credential overload is inherited from **AbstractDriverBasedDataSource**, whose package
   has `@NonNullApi`; that public overload has no nullable parameter override.
   `build.gradle.kts:102` enables `-Xjsr305=strict`. In contrast, JDK `javax.sql.DataSource`
   has unannotated/platform credential parameters, which let the anonymous override be
   written with `String?`; that does not make the concrete Spring receiver accept nullable
   arguments in Kotlin.

   Change only the override signature to
   `getConnection(username: String, password: String): Connection`, matching the supported
   delegate's declared contract. Keep **both overloads**, each original acquisition-counter
   increment, and the exact forwarded `reader.getConnection(username, password)` call.
   No interface cast, `!!`, replacement/default credentials, no-arg substitution, dropped
   call or new helper was used. The existing tests have no null-credential oracle; the
   foreign-factory observation and real positive/refusal paths are retained.

   Local inspected `spring-jdbc-6.2.19.jar` SHA256:
   `c81fd8aca952aac243d9327af12596c2058012c9d3784f1313477a6d2cc56306`.
   This is API/nullability inspection of the selected local artifact, not new dependency
   publication authority or runtime proof.

2. OwnershipIT's existing accepted-but-undelivered test now lays out `newExecutor(`,
   its existing `cleanupPort { body.set(true); 0 }` argument, and `)` on separate lines.
   The body flag, zero return, outer cleanup call, catch, thread/latch/tail ownership and
   every assertion/timing bound remain unchanged. No source suppression was added.

## Exact incremental packet

Patch: `review/remediation/app-29-ordinary-connected-test-compile-correction-01.patch`.
**2 paths, +7/-5, 1978 bytes**;
SHA256 **`771bd1533698e196ea726c4db821b4f7ed3ce0159ef6ff5d09983611baf4f22e`**.
This is Linux02/current-WIP preimages → current WIP, not HEAD → worktree. Earlier packets
and the previous12-path patch were not rewritten.

| Test file | Before SHA256 | After SHA256 |
|---|---|---|
| `OrdinarySourceGrantCleanupFixture.kt` | `2ff79b0a4058cd30be1f9b298210c9d5fd28d6fc3ee2eac32e28b11c3c594ed9` | `ce0110d46c15fefe5e152d6aa4be30d1c0539247f468c54d4cb15969db52418b` |
| `OrdinarySourceGrantCleanupOwnershipIT.kt` | `0dd13453b6242db6f95cbcd961e6c19fde46b07db48a2b53221280cb006e0902` | `a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557` |

Two private0600 before images are at
`review/working/app-29-ordinary-connected-test-compile-correction-01/before/` followed by
each full backend-relative path above. The packet's `before.json`/`after.json` bind exact
source bytes and per-file diff hashes. Both preimages matched the Linux02 freeze:
`review/working/app-29-w03-integrated-driver-ordinary-connected-02/manifest.json`, SHA256
`0c9b72484e6513005bd99dd675045e569cde1ad3bde9c11b87fd65885d593ab2`.

Passive source comparison: only these two paths differ from that478-path freeze; the
other476 retained paths, including **all production files**, remain byte-identical.
No assertions, test names, SQL, reflection/observation targets, control paths or time
limits were changed. No product/configuration/baseline, new helper or new suppression.

## Verification boundary

Author performed source/report reads, read-only Git and API metadata inspection, two-file
editing and passive snapshots/diffs/hashes only. **No build, compiler, test, Ktlint/Detekt,
formatter/checker, CI, Git mutation/push or helper launch.** No frozen evidence or previous
handoff was modified. No subagent was spawned. Primary retains execution/cleanup/tracker
and notification ownership.

Neither the new test compilation nor formatting has been rerun by this author. Independent
review of this small delta and primary-owned configured validation are still required.
All unexecuted five selected regression families and connected real-DB oracles remain
uncredited; no W03/P3, production, integration or issue-closure acceptance is claimed.
