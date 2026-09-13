# App29 PG03 — exact JVM stack-witness correction, author report 01

Status: **one-site test-source correction only; uncommitted and unexecuted.**
Author: `/root/w03_core_author_resume`. Primary retains source-review, freeze,
static/build/test, CI, commit and push decisions. App107 source was not touched.

## Scope and source identity

Repository: `kira-backend`, branch `remediation/app-29-backend-complaints`.
HEAD remains `f2e58eac0b139dca3a042c724d69c66a3d65278e`; initial backend worktree
was clean. The sole backend change is unstaged, in:

`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLeaseDispatchCreatorIntegrationTest.kt`

Workspace/backend AGENTS, backend README, relevant PLAN constraints/testing,
COMPLAINT_DRIVER_LIFECYCLE, LOCAL_DEV and security logging/privacy guidance were
read before editing. Existing sibling-app owner work was observed and untouched.

## Evidence and finite correction

Inspected the full raw XML, its factual MODEL stage line, implicated class-load
origins, full affected test method, production `internal fun afterJdbcCall`, and
independent PG03 actual-result review. Retained run **34786407104**, attempt 1,
on Backend f2 has **2 cases: 1 PASS / 1 FAIL**. Its original assertion fails at
old test line 564 while the retained exception stack includes exactly:

`me.manga.kira.backend.common.infrastructure.persistence.PersistencePhaseContext.afterJdbcCall$kira_backend`

The old predicate compared only `methodName == "afterJdbcCall"`, the Kotlin source
name, not the actual internal-member JVM name. The replacement keeps the real
current-thread stack witness, binding both components exactly:

```kotlin
// The normal kira-backend JVM build mangles this internal method with its module name.
assertTrue(
    Thread.currentThread().stackTrace.any {
        it.className == PersistencePhaseContext::class.java.name &&
            it.methodName == "afterJdbcCall\$kira_backend"
    },
)
```

The declaring-class name comes from the existing product class literal; no method
discovery, reflection invocation, harness, alternate compiler or build-mode
fallback was added. There is no substring/prefix acceptance, no unmangled-name
alternative, and no production visibility change. The exact module-mangled name
is intentionally bound to the observed normal build, not guessed by matching
synthetic/test method names that themselves contain `afterJdbcCall`.

The full diff is one hunk: seven added lines replace one assertion line. All other
bytes in the test remain unchanged. This preserves every diagnostic stage/capture,
first-failure and restoration path, identity/budget/dispatch/count assertion,
MODEL clock advance, retirement assertion, authentic-actor assertion, final
quiescence/admission/expected-expiry check, and failure/recovery cleanup. Production,
build files, baselines and historical evidence were not edited.

## Pins

All values are SHA-256. Paths below are relative to the workspace unless stated.

| Item | SHA-256 |
|---|---|
| Target test before (Backend f2 / PG03) | `f8583ac5daef026d2e691e2c42d14be93573dfbe442bee8c5f5d3188482eca1a` |
| Target test after this uncommitted correction | `915785fe0ddefa5444ba088792345e9141c129529d518ff3e525658cf9e6132e` |
| Unchanged production `PersistencePhaseContext.kt` | `2ce0328657f28541b93ba6b568f477070d09d9070ffdf902e29ac42da63b6237` |
| `review/remediation/app-29-lease-dispatch-pg03-stack-witness-correction-author-01.patch` | `71903d644d18e2aa7325e3805a804fa8f3b46c8be4db2ee96574c47304eb8964` |
| `review/remediation/app-29-lease-dispatch-pg03-independent-result-review-01.md` | `12823d278830ee5e52c22e935d0949aa62bf59a25f1e6830cf39876d4b60e0ac` |
| PG03 raw test XML (path below) | `7b9e31356522d9c22dac2e79839c65f5f5e80d456fa52e855eafdab74e41a943` |

Raw XML: `review/working/app-29-lease-dispatch-pg03-admission-01/launch-01/artifacts/test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.xml`.

## Verification and unchanged limits

Only passive source/Git/evidence reads, hashes, the authorized one-site edit and
private report/patch writes were performed. Readback and full Git diff show only
this site changed; index diff remains empty, HEAD unchanged. No lint/static tool,
compiler, Gradle/JVM, test, runner/collector/helper, process/lock/cache action,
network/CI, staging, source freeze, commit or push was performed. This report is
not independent approval and does not certify that the corrected guard passes.

PG03 ended at `STORE_ENTERED,LEASE_OBTAINED,SETUP_OBTAINED,LOWER_RETURNED,
CLOCK_ARMED,CLOCK_ENTERED`. The exception stack is retained, not the separately
sampled `Thread.stackTrace` array. Later identity assertions, TAIL_WITNESSED,
MODEL expiry, retirement, actor dispatch and recovery assertions have **not** been
shown to pass by that run or by this edit. `actor_ran=false` is not an actor defect
finding. Historical PG03 remains FAIL with its six sticky failure records; its
cleanup evidence is not aggregate PASS or graceful/zero-kill proof. PG02, PG18,
Native05 and all broader qualification/production/recovery limits in the cited
independent report remain unchanged. No rerun authorization is implied.
