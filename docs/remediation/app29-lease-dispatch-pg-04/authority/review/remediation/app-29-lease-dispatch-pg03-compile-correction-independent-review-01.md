# App29 PG03 compile correction — independent actual-diff review 01

2026-09-13 UTC. NONAUTHOR: `w03_static_nonauthor_review`.
**SOURCE-ONLY APPROVE: exact one-call Java-overload correction.**
No compilation, runtime, PG, cleanup or qualification PASS is implied.

## Exact inspected binding

Backend HEAD remains `c67ddcd30fbae2438c7b2f803f720530b598e428`.
Only dirty path (unstaged; cached diff empty):
`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLeaseDispatchCreatorIntegrationTest.kt`.
Full HEAD changed-path set and Git status both contain exactly that path.

Packet: `review/working/app-29-lease-dispatch-pg03-compile-correction-01/`.
Independently recomputed pins:

| Input | SHA-256 |
|---|---|
| `source.json` | `74f55a3ebb3373e47c1bd1a96751479499f7267ce138c2b01ea6d0938d0e9397` |
| `source.patch` | `3462e9c7d2e94bb129be635d5d1513066bf28336f84a33c7ee9e20f537a5064d` |
| Original commit file | `3c0010170b07b1edef3f87894dac6833f2ae2f02e841609cd5e3e15d9ce489d5` |
| Current corrected file | `f8583ac5daef026d2e691e2c42d14be93573dfbe442bee8c5f5d3188482eca1a` |

Actual `git diff --full-index` matches the packet byte-for-byte. Replacing only
the new three-line block at579-581 with its original single-line assertion
reproduces the complete original commit file byte-for-byte. No extra edit exists.

## Semantics and manual format review

The fully qualified `org.junit.jupiter.api.Assertions.assertThrows` receives
`SQLException::class.java` and the unchanged sole action `lease.enterDispatch()`.
It resolves intentionally to the noninline Java overload instead of the imported
Kotlin wrapper. Reuse the version-specific JUnit5.12.2 analysis in the unchanged
PG02 failure review (SHA-256
`0b70679ea085c844bdfaaf4be981fbccd6b52646fa5c80228e5ec86180f810e4`, rehashed).

Both forms execute that action once and require SQLException or a subtype;
no/wrong exception still fails. No nonlocal return or consumed exception result
is involved. The Java evaluation/rethrow stack shape differs as previously noted,
not the asserted refusal. Placement remains immediately after retirement
observation, inside the same diagnostics capture and before the same subsequent
authenticity/quiescence/owner checks. Lease identity, logical timing/order,
clock/budgets, diagnostic stages, first-failure handling and restoration are
unchanged. All test names, annotations, filter expectations, remaining assertions,
fixtures and production bytes remain unchanged; no selector renaming is needed.

The three new lines retain LF and44/48/44-space indentation, have lengths117/69/45
bytes, and introduce no tabs or trailing spaces. No manual formatting hazard was
found; no formatter/static checker was run. Existing Kotlin assertThrows imports
and other calls were not altered.

## Limits / handoff

Only passive source/Git/hash/stat/JSON/byte comparisons and this new private0600
report. No source/tooling/Admin edit, helper execution/import, compile/test/CI,
network/dependency acquisition, resource operation, commit or repeat run.
The generated-name repair still requires primary's authorized normal compilation;
PG02 remains the preserved zero-test failure. The separately authored failed-run
cleanup carrier is outside this review and awaits its own handoff.
