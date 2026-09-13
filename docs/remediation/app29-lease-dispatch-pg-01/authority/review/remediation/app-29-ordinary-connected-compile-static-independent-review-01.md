# W03 connected compile/static correction — independent actual-diff review01

2026-09-13 UTC · `/root/w03_connected_ownership_review` · private0600.

**Disposition: no blocking finding in this exact correction. Source concurrence for
primary-owned focused validation only; NOT a compile/static/test PASS or W03/P3 acceptance.**

## Scope and byte binding

Reviewed all839 lines of the incremental **12-existing-path, +223/-117, 45,769-byte**
patch and the corrected declarations' surrounding source. This is pre-correction WIP →
corrected WIP, **not HEAD → worktree**. Prior accepted ownership/source research was not
reopened; this review tests whether the compile/static correction preserves it.

Paths below are relative to `/root/projects/Kira/`; E =
`review/working/app-29-ordinary-connected-compile-static-correction-01/`.

| Reviewed input | SHA-256 |
|---|---|
| `review/remediation/app-29-ordinary-connected-compile-static-correction-01.md` | `943b0809b5fbfc13c5b7a472ca2a697851595e5925a08327dcabc2e220e13d59` |
| Matching incremental `.patch` | `1480fc3e3ed99b9b63c172a34491171811c59b4e40937fb3f3c6b31bf681506d` |
| E `before.json` | `0011c1bd5cd1cc8ffd55818f896bda406540170003bb95724dd5bd2b51dc9c82` |
| E `after.json` | `528e22069dcc33051b50f9823e4bc5982b70d38d36849b19ae1582e64ecc8fff` |
| E `retained-source-before.json` | `f71e442c2fcbaf102e50be9851fb19d1fa09051709b01d53e959ff66f09b6f3e` |
| `review/working/app-29-w03-integrated-driver-ordinary-connected-01/manifest.json` | `064ec427d6dda2acb7027487cc5279bfb1e8ff8578cb3c8ef0ecc6deadd2766e` |
| `review/working/app-29-ordinary-connected-linux-01/result.json` | `44ae613363dbbe9bd11e5873c1da14f565ba717bbcb7ef08b24c118c773e3bb3` |

Independent passive observations: all12 current backend files equal E's after images and
metadata; all12 before images equal the actual Linux01 source snapshots and frozen manifest.
The in-memory before/after textual diff equals the reviewed patch byte-for-byte, including
all12 per-file patch hashes in `after.json`. The478-path retained inventory equals the frozen
manifest; only these12 current paths differ, the other466 remain byte-identical, none missing.
This is a bounded inventory observation, not a claim about every workspace file. No Git
command was used or ancestry independently re-certified. Keep backend ancestry/evidence private.

## Findings and preservation assessment

**No correction-specific source blocker identified.** References below use corrected lines;
P is the main `common/infrastructure/persistence` package, Q its test counterpart.

- **Explicit Java setters:** P `GuardedJpaTransactionManager:41` pins the same dialect
  after autodetection, before the unchanged exact effective-resource validation. P
  `PersistencePhaseContext:64` and Q `OrdinarySourceGrantCleanupOwnershipIT:216` set the
  same transaction names; REQUIRED/timeout2 and the positive name assertion are unchanged.
  No Kotlin owner `val` became mutable; no DataSource reassignment concealed a provider
  mismatch; no new resource lookup/borrow was introduced. These narrowly correct the two reported
  main read-only-property assignments plus the identical source-discovered test occurrence;
  Linux01 did not reach test compilation. Actual compiler compatibility remains unverified.
- **Declaration-local suppressions:** inspected their bodies, not just the new rationale
  comments. The acquisition/holder/completion gates, JDBC capability table, all return-reuse
  vetoes, no-status EM-closure proof, invocation output custody, and dispatch/finally boundaries
  keep their original predicates, short-circuit order and extent. Class-only `TooManyFunctions`
  exemptions cover the existing cohesive phase and graph owners (46/40 and42/40); other new
  exemptions are rule-specific method annotations. No file-wide suppression, Ktlint suppression,
  baseline/config change or guard removal is in the delta. Preserving these accepted extents
  is preferable here to a metric-driven custody refactor; exemption is not correctness evidence.
- **Exception/interrupt/refund custody:** broad-catch coverage is unchanged. Entry still
  settles only genuinely unused current-entry custody and retains bounded refusal reasons;
  scoped manager failures retain outcome/interrupt state before the original finally,
  while unscoped failures rethrow unchanged. `finish:422–425` merely renames an unused catch
  parameter to `_`: restoration failure still sets CLEANUP_UNRESOLVED and clears
  `springSettled`, preventing a settlement/refund claim on that path. No raw exception/log
  was added. COMMITTED/UNKNOWN remains independent of local cleanup/refund.
- **Test oracles:** Q ownership observer `get:840–869` still requires the same live armed
  lower failed BUSINESS commit, excludes preparation/wrapping/later-rollback failure, and
  delegates original TL storage. Return barrier `remove:1085–1098` retains caller/RETURN/
  consent/one-shot ordering and genuine end delegation. Same-session read-cap assertion
  `643–647` only wraps arguments. Exact-PID/backend-start positive PgSleep witness and the
  original accepted-lease-through-disposition1..3000ms bound, durable afterCommit COMMITTED
  plus restored caller interrupt, successor epoch/stale old close checks, and peer
  scope/cutoff/first50/SKIP LOCKED/rollback assertions are not weakened. The15 ownership
  and6 peer real-database methods remain present, unchanged in their tested obligations.

## Execution limits and next gate

Retained Linux01 failed main compilation on two `'val' cannot be reassigned` diagnostics,
with24 main/61 test Ktlint and27 Detekt findings. **ZERO TESTS EXECUTED**; missing
`test_evidence` is not a discovered JUnit failure. The local suppression/layout mapping
addresses those locations in source, but no configured static tool has accepted these bytes.

Reviewer ran **no** build/compiler/test/static tool, project helper/runner, Git command,
service/container/worker, CI, network operation or subagent. Only passive reads/hash/textual
comparison and this report creation occurred. Primary owns notifications, refreezing and
the next normal main/test compilation, Ktlint/Detekt and selected five-class nonDB batch.
Previously unreachable test-compiler diagnostics may still emerge; no test family receives
execution credit from this review or Linux01. The21 connected real-DB methods also remain
unexecuted, including actual failed-commit reachability, PgSleep witness/budget, afterCommit
interrupt and real same-session restoration behavior.

Dormant/non-bean restrictions and production/UNKNOWN, Boot/customizers, full-P3/W03,
W05 request expiry, operational incident sink, native/opaque/liveness and new-data recovery
gates remain open. PG1 unchanged; W06 excluded. No integration, deployment, issue closure
or public publication is authorized by this review.
