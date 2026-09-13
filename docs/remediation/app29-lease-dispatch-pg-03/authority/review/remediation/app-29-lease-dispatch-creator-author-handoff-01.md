# App29 — lease-dispatch creator author handoff 01

2026-09-13. **PRIVATE; authored source only, UNCOMPILED / UNEXECUTED.**
Backend HEAD `ccdbb28f6362117882501b4da040257be6fc1990`, branch
`remediation/app-29-backend-complaints`. This records author observations, not an
execution admission, source freeze, independent approval or W03 completion.
**PG01 remains 20 PASS / 1 FAIL; its actual actor/queue mechanism is unmeasured.**

## Scope and custody

The correction binds one non-consuming upper-invocation creator to the authentic
pre-exposure pool/lease/epoch association, admitted guard and actual dispatch.
Its retained outer adapter/finalizer tail participates in the existing exact-epoch
ledger and lease proof. It does not spend the sole RETURN/EVICTION right, grant
lower/native fallback, reopen admission or replace a budget. Common pool lineage
supplies creator precedence and post-core self-wait refusal. Worker custody is
unchanged and retains scalar completion, not a lease graph.

The final passive pass tightened four corners: sticky failure before fallback
exception allocation; producer retention after creator setup loses its tail
pointer; nonnullable local statement-delegate references; and caller-bound MODEL
clock interception so the scanner cannot consume the `afterJdbcCall` hook.

No build, compiler, checker, test, CI, service, network, process-control, commit,
push or source freeze was performed. App owner-WIP and historical evidence were
not edited. No further W03 source changes are authorized absent returned findings.

## Exact current path pins

Paths below are exact relative to `kira-backend/` after expanding:

- `M/` = `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`
- `T/` = `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`

These are passive SHA-256 observations, **not a candidate freeze**. There are
14 modified tracked paths and 3 new paths; no other backend author changes.

| Path | State | SHA-256 |
|---|---|---|
| `M/GuardedDataSource.kt` | modified | `7395aa04bfbb6702043dddf1a6393cf94b2abd67128bf669ee81ff39df2ca448` |
| `M/LeaseJdbcFacade.kt` | modified | `28e63d187150a4768661ee7fb257cf4d5e29d99b7a0e642619abfb2661705afd` |
| `M/PersistenceJdbcGuardCall.kt` | modified | `bcc7385e7ba6f2fcb08a21804357cc00901297fba14c603f10e8588fdd309a70` |
| `M/PersistenceJdbcGuardProtocol.kt` | modified | `f0209738f66ed56298799a1b58d1f8e67e518d8a5d3f5bc591f944224cd43063` |
| `M/PersistenceJdbcLease.kt` | modified | `52adf32aef2bb2651cfedabd076785a585a6ac3549d1d0fcf160c11022affc1f` |
| `M/PersistenceJdbcLeaseInvocation.kt` | new | `d4a41dc996bc34604b380a073606e4ddf699bb27d9c30036f414c2c0f6e67c28` |
| `M/PersistenceJdbcPoolTransfer.kt` | modified | `d77f0b6c32d970e6bc121dd3c87d5b81fbf2cc43632fe02bc8160833155ca8bf` |
| `M/PersistenceLeaseCompletion.kt` | modified | `72b28bb29e2eb3e173aa129691f7217ce7fd431bbed4bfdce66ebe506e6d7955` |
| `M/PersistenceProducerEpoch.kt` | modified | `ceba65cea2616a82f0e6614bfda229ecf7221e77c5209ff6bbaf33ea1c270cba` |
| `M/PhysicalJdbcDescendants.kt` | modified | `70aa9d92b96ad0595b321ed30dcc05cd73cc370c921fd05dfc87f370a1868220` |
| `M/PoolLifecycle.kt` | modified | `1a4f606b75dea09e2f3d6897fe9170007ed9bae5449c609e12961ea6e28a2564` |
| `M/PoolLifecycleFrames.kt` | modified | `8dff17640c0c242c8243364d0bd6490dadc61c0eda46c637405e8431eda90367` |
| `T/PgLifecycleDatabaseProbe.kt` | modified | `de5190a19261b63a009b830912896297ea291c1fa6d155e723fc3c59760b0859` |
| `T/PgLifecycleDatabaseProbeProcess.kt` | modified | `f8dd59a17d0334a5d8cc9c9b577b26e5ecead537a7f30180c975d0a25b88264a` |
| `T/PgLifecycleDatabaseRecipe.kt` | modified | `e405d48f71463bd8512a9433311509e92b387807f1b4c6682843dc9708ac128e` |
| `T/OwnedPoolLeaseCreatorPendingProbe.kt` | new | `e2e62c2fd4fd36d54f9c6a900c277a2c961e3238384bfd1220d83daa38fd333f` |
| `T/PoolLeaseDispatchCreatorIntegrationTest.kt` | new | `da4ead51ebdded37bc6b97e88b2c1d9f43ec6b28d36da25775ca74db601d7e9b` |

## Exact 17 UNEXECUTED invocation selectors

All belong to class
`me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest`.
Names below identify source methods/enum rows, **not observed JUnit results or a
claim that a particular CLI filters individual parameterized rows**.

Nine `@Test` methods:

1. `MODEL fatal connection commit creates the first real Hikari close Worker and drains its task`
2. `MODEL fatal Hikari statement execution creates the first real close Worker and drains its task`
3. `repeated nested admitted dispatches retain one future RETURN and no lower native fallback`
4. `only exact admitted guard dispatch lease epoch and issuer can enter a creator`
5. `mixed pool creator nesting refuses wrong top fallback and unrelated lease use`
6. `present returned dispatch cannot upgrade through pool authority and a revoked lease cannot enter a prepared creator`
7. `foreign actual statement cancellation keeps only its own outer tail while original RETURN waits for it`
8. `real post core outer tail refuses reentrant self wait and remains in exact terminal and loan proofs`
9. `MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement`

Eight rows of `@ParameterizedTest` method
`actual creator publication restoration and outer adapter faults retain exact obligations through process only exit`
with `PgLifecycleDatabaseMode`:

10. `POOL_LEASE_CREATOR_ENTRY_BEFORE_TL`
11. `POOL_LEASE_CREATOR_ENTRY_AFTER_TL`
12. `POOL_LEASE_CREATOR_END_BEFORE_TL`
13. `POOL_LEASE_CREATOR_END_AFTER_TL`
14. `POOL_LEASE_CREATOR_CORE_BEFORE_TL`
15. `POOL_LEASE_CREATOR_CORE_AFTER_TL`
16. `POOL_LEASE_CREATOR_CLIENT_INFO_TAIL`
17. `POOL_LEASE_CREATOR_DECLARED_TAIL`

The process rows use the existing negative lane, original deadlines, exact
RETAINED/EXIT handshake and exit23 `PROCESS_ONLY product_end=false`; its unchanged
positive oracle must reject that exit. The first two tests observe the actual
stock-Hikari closer's initial zero Workers and actual Worker/task drain, not an
arbitrary factory call or global generation count. None has run.

## Independent-review priorities / limitations

- Scrutinize pre-registration partial failure custody and the final epoch cut:
  only prevalidated scalar pool publications may follow it. The final missing-tail
  producer guard has no separately injected regression among the 17 cases.
- AVAILABLE entitlement checks can refuse setup before creator admission. Active
  creator end/recognition does not recheck availability, retirement or budget.
  Multiple internally prepared candidates may exist before one enters; only one
  can retain/admit per actual guard/dispatch. Review this against one-invocation
  issuance requirements rather than assuming stricter single-preparation proof.
- SQLClientInfo lifetime uses the expressly approved test-held **per-instance**
  MODEL substitution of private `SafeJdbcFailure.postgresExceptionClass`. The real
  outer converter is held after actual core TL restoration; the original field is
  restored in finally and the held caller released/joined on assertion paths.
  Production preparation deliberately rejects overridden PG scalar getters; this
  is not stock-PG failure/profile evidence and changes no production allowlist.
- Declared-stream mode holds the prerequisite failing finally **after its actual
  core TL write**, then checks outer IOException conversion. It does not suspend
  inside that converter. Other actual tail cases include completed producer/core
  restoration and concurrent cancellation/original RETURN within the original
  one-second RETURN budget.
- Compilation, JVM reflection behavior, timing and actual result oracles remain
  unverified. This author report is not self-approval.

## Preserved evidence

Rehashed unchanged: original acceptance `T/OrdinarySourceGrantCleanupOwnershipIT.kt`
`a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557`;
original owned teardown and old two pending cases `T/PersistencePgOwnedCutIntegrationTest.kt`
`b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322`.
`M/PhysicalJdbcFacade.kt`, `M/PoolActorCustody.kt` and `M/SafeJdbcFailure.kt` match
the prior review's pins. The frozen478 manifest remains
`7c5e775dc0250948ead0ba20aff89cb38e2565fdbb82751575291fa96a80d63c` and PG01's
OrdinarySourceGrantCleanupOwnershipIT result XML remains
`de0a3b68933690ca5309411057b164575c4b2b51f759c8da32a9e425b2177835`.
No historical348/frozen478 evidence or original acceptance assertion/budget was rewritten.
