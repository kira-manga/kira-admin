# App #29 W03 lease-dispatch Linux01 static correction — author report 01

**AUTHOR REMEDIATION ONLY — UNCOMPILED / UNVALIDATED — NOT INDEPENDENT APPROVAL.**

## Scope and provenance

This report records the narrow, parent-approved source corrections to the actual
`app-29-lease-dispatch-linux-01` static failures. No formatter, checker, compiler, Gradle,
JVM, test, service/process action, lease/lock action, freeze/preflight, commit, push or
hosted dispatch was executed by this correction author. All changes remain owner WIP.

The actual original run completed `compileKotlin`, `compileTestKotlin` and `testClasses`,
but failed Ktlint main, Ktlint test and Detekt. Its result is **FAIL**, with tests
**NOT_REQUESTED**. That compilation result applies to the original bytes, not these edits.

- Backend HEAD: `ccdbb28f6362117882501b4da040257be6fc1990`.
- Original481 manifest: [`manifest.json`](../working/app-29-w03-integrated-driver-lease-dispatch-linux-01/manifest.json),
  SHA-256 `dde01186ffb596c48207bb2ecd5564b68ce21511cf042007e15dab0bac624e2a`.
- Actual result: [`result.json`](../working/app-29-lease-dispatch-linux-01/result.json),
  SHA-256 `1a1202fefb4034bf4133de572c295fd1d1d3efbbfab807e5ef9c45b5c4565d28`.
- Actual [`validation.log`](../working/app-29-lease-dispatch-linux-01/validation.log),
  SHA-256 `f2bd2ce0f894a70d15754cbf564cbaf4d05522128d5f48bd59e22b0efa8222c4`:
  original compilation tasks at lines 5/10/13; static failures at 19/62/99.
- Original reports: [`reports/reports`](../working/app-29-lease-dispatch-linux-01/reports/reports/).
  Their exact text/XML/SARIF hashes are retained in the correction packet's `inputs.sha256`.

The [private author packet](../working/app-29-lease-dispatch-linux01-static-correction-01/)
contains the correction-only `correction.diff` against original481 retained source snapshots,
not a diff against HEAD and not a replacement freeze. The original17 WIP path set remains
exactly 14 tracked modifications plus 3 untracked source files; only 10 of those paths were
changed by this correction. No product path was added or removed by it.

| Packet evidence | SHA-256 |
|---|---|
| `correction.diff` | `8332d30e9232ed9ed3ccefda8792f26b790bb2373aad78e0b48076af8d33c9c8` |
| `before.sha256` (all17) | `f71205a940318ab7b9d83ba98ec3249145b234672d0e328833a6d18784cdb861` |
| `after.sha256` (all17) | `5cce1bf6cd712a25fde2d9f7b9e1deb6ffb7d34d06e107092995d112200d3c59` |
| `source-disposition.tsv` (exact paths and before/after hashes) | `78b828ff8c7ac8aaa6c0e932b779487c747741b2fa71b477c7bed573809fa4dc` |
| `findings.tsv` (all93 retained findings) | `17b98306e7ba0b97ae1363e5a6b0f801dede80aec7a506c74b4f92d55c9588e1` |

Passive byte readback, recorded in `passive-readback.json`, found exactly these ten live-file
differences within the unchanged481-key source inventory: the other471 live files still match
its digests. All214 retained source snapshots match their original hashes, and the unchanged
manifest retains all348 seed keys. All16 initial and2 supplemental input pins match. This is
source/artifact custody evidence, **not execution validation or a new preflight**.

## Changed files

All paths below have prefix `src/{main|test}/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`.
The machine-readable packet records full repository-relative paths and exact hashes.

| Source set | File | Narrow correction |
|---|---|---|
| main | `PoolLifecycle.kt` | Move five new bridge bodies into their existing nested methods; split three predicates; extract only failed-entry restoration; wrap long syntax. |
| main | `PersistenceJdbcLease.kt` | Separate issuer refusal from the existing three-condition dispatch-selection guard. |
| main | `PersistenceLeaseCompletion.kt` | Combine two adjacent false-return guards with lazy OR. |
| main | `PersistenceJdbcGuardCall.kt` | Signature wrapping only. |
| main | `PersistenceJdbcLeaseInvocation.kt` | Braces around the existing conditional adapted throw. |
| main | `PersistenceProducerEpoch.kt` | Constructor layout only. |
| main | `PoolLifecycleFrames.kt` | Signature/expression layout only. |
| test | `OwnedPoolLeaseCreatorPendingProbe.kt` | Extract caller-thread verification body; split two injection predicates without read reordering. |
| test | `PoolLeaseDispatchCreatorIntegrationTest.kt` | Extract twelve initial read-only assertions; remaining edits are report-directed layout only. |
| test | `PgLifecycleDatabaseProbe.kt` | Braces around the two existing dispatch branches. |

The other seven original17 files are byte-unchanged: `GuardedDataSource.kt`, `LeaseJdbcFacade.kt`,
`PersistenceJdbcGuardProtocol.kt`, `PersistenceJdbcPoolTransfer.kt`, `PhysicalJdbcDescendants.kt`,
`PgLifecycleDatabaseProbeProcess.kt` and `PgLifecycleDatabaseRecipe.kt`.

## All reported findings: author dispositions, not new results

Every entry in `findings.tsv` has status **EDIT_AUTHORED_NOT_RERUN**. None is waived, suppressed,
filtered or accepted as passing. Old locations below refer to the immutable actual reports;
new locations refer to the `after.sha256` bytes. Static configuration remains unchanged:
Ktlint1.8.0 / IntelliJ style /160 columns; Detekt1.23.8, LongMethod100,
Cyclomatic25, NestedBlockDepth5, functions/class40, ReturnCount6 and maxIssues0.
No suppression or baseline entry was added, removed or expanded.

### Detekt: all19, including all7 MaxLineLength findings

| ID | Original finding/location | Source correction and current locus |
|---|---|---|
| D001 | NestedBlockDepth5/5, `PoolLifecycle:462` | Existing creator `enter` at668; only deepest refusal-restoration block extracted at709. |
| D002 | TooManyFunctions44/40, `PoolLifecycle:9` | Remove five outer bridge declarations; retain their bodies in the pre-existing nested methods. Source-level outer count is39, its HEAD baseline count; no older helper relocated. |
| D003 | ComplexCondition4/4, `PoolLifecycle:441` | `bindLease` at576; same-gate adjacent guards at582–583. |
| D004 | ComplexCondition4/4, `PoolLifecycle:543` | `failBeforeEnd` at755; adjacent guards at756–757. |
| D005 | ComplexCondition4/4, `PoolLifecycle:701` | `bindLeaseLocked` at601; issuer/phase guard then prepared/lease guard. |
| D006 | ComplexCondition4/4, `PersistenceJdbcLease:405` | Issuer-only first guard at405, original ended/caller/TL guard at406. |
| D007 | LongMethod103/100, pending probe `verify:16` | Caller-thread body extracted to `verifyCaller:101`; publication remains in caller's original try at32. |
| D008 | Cyclomatic33/25, pending probe `verify:16` | Same extraction removes both caller mode switches, the conditional input and associated nested branching from `verify`. |
| D009 | ComplexCondition4/4, pending probe `remove:261` | Pool-TL predicate at273–274, original evaluation order preserved. |
| D010 | ComplexCondition4/4, pending probe `remove:284` | Core-TL predicate at297–298, original evaluation order preserved. |
| D011 | LongMethod108/100, integration `fatalRoute:56` | Twelve original assertions replaced by one call at69; helper179–192. Expected logical reduction11, not a measured new Detekt result. |
| D012 | ReturnCount7/6, `PersistenceLeaseCompletion:85` | Checkout/epoch guards combined at88; six source return statements remain. |
| D013 | MaxLineLength, `PoolLifecycleFrames:96` | Signature wrapped at96–102. |
| D014 | MaxLineLength, `PoolLifecycle:464` | Moved creator-enter guard wrapped at670–675. |
| D015 | MaxLineLength, `PoolLifecycle:543` | Moved failure guard split at756–757. |
| D016 | MaxLineLength, `PoolLifecycle:697` | Nested `prepareDispatch` signature/body at588–599. |
| D017 | MaxLineLength, `PersistenceJdbcGuardCall:95` | Signature wrapped at95–99. |
| D018 | MaxLineLength, integration:274 | Same forged-token arguments wrapped at278–284. |
| D019 | MaxLineLength, integration:349 | Same named test expression starts on next line at359–360. |

### Ktlint:39 main +35 test =74

These grouped ranges account for every individual finding retained in `findings.tsv`.

| IDs | Count | Original locus | Authored correction |
|---|---:|---|---|
| K001–005 | 5 | GuardCall:95 | Multiline signature. |
| K006 | 1 | LeaseInvocation:36 | Braced conditional throw. |
| K007–010 | 4 | ProducerEpoch:303–305 | Single-line constructor. |
| K011–019 | 9 | PoolLifecycle:464 | Relocated, wrapped guard; identical operand order. |
| K020–025 | 6 | PoolLifecycle:543 | Relocated, split guard; identical operand order. |
| K026–031 | 6 | PoolLifecycle:697 | Wrapped signature with existing forwarding method now owning its body. |
| K032–039 | 8 | PoolLifecycleFrames:96 | Wrapped signature, expression follows closing signature line. |
| K040–041 | 2 | PgLifecycleDatabaseProbe:51–52 | Both branches braced. |
| K042–048 | 7 | Integration:274 | Multiline forged-token arguments. |
| K049–054 | 6 | Integration:349 | Next-line expression, same lambda body reindented. |
| K055–056 | 2 | Integration:562/571 | Wrapped `requireNotNull` around same `newThread` lambda. |
| K057–059 | 3 | Integration:594 | Same two `runCatching` statements on separate lines. |
| K060–063 | 4 | Integration:656–658 | Collapsed short `withCreatorCall` signature. |
| K064–068 | 5 | Integration:677–680 | Collapsed constructor; supertype on following line. |
| K069–073 | 5 | Integration:709–712 | Collapsed constructor; same ordered supertypes on following lines. |
| K074 | 1 | Integration:757 | Same expression on signature line. |

## Semantic/read-order proof for the material edits

This is the author's source comparison, not an independent concurrency verdict or bytecode proof.
All body references to old outer `this` become the pre-existing nested `pool` receiver; old outer
`issuance` becomes **`pool.issuance`**, never the entitlement's possibly forged stored issuer.
Old `creator` becomes the same nested creator `this`; old `entitlement` becomes the same nested
entitlement `this`. Removing a forwarder changes call stacks/immutable receiver loads; identical
bytecode or stack traces are not claimed. The issuer, mutable-state, counter and ThreadLocal
checks/publications below retain their ordering and lazy evaluation.

### Five moved bodies

1. **`bindLease` (old435–448 → nested576–586).** Authentication against the actual pool issuer
   still precedes `owner.ownershipLockHeld()`, the nullable acquisition read, and
   `candidate.preparedForAcquisition(pool, acquisition)`. Under the **same `pool.gate`**, the
   acquisition frame is read, then acquisition-entitlement identity, frame authentication,
   frame activity, and current pool-TL identity are evaluated in that order. The two adjacent
   guards have the same short-circuit refusal as the original four-way OR. Binding still
   calls `bindLeaseLocked(pool.issuance, candidate)` inside that monitor. Its issuer/phase
   guard remains before prepared/lease reads, and assignment is still last. No publication,
   terminal preparation, issuer strengthening-by-self-comparison or count change was added.

2. **`prepareLeaseDispatch` (old450–460 → existing `prepareDispatch:588–599`).** Same ownership-lock
   check, same `call.admitsCreator`, same entitlement recheck under **`pool.gate`**, then outside
   it the same frame construction arguments in order: pool, pool issuer, current Thread,
   `call.budget`, `lease.state.epoch`. The creator receives the same frame, this entitlement,
   lease, dispatch and call. That exact frame retains that exact creator with the pool issuer
   before returning. No new monitor, ticket type, allowance or validation branch appears.

3. **`enterLeaseDispatch` (old462–509 → existing `enter:668–707`).** `val frame = this.frame`
   preserves the original first body read/snapshot. Owner-lock check → authentic creator →
   guard admission remain ordered. The first same-gate entitlement check still precedes
   refusal publication, entry claim with `PoolCallFrames.current()`, and `setupStarted=true`.
   `call.retainCreator(this, lease, dispatch)` returns the same tail, explicitly assigned to
   **`this.tail`** before `tail.register()`, then the same pool-TL installation. Under the
   second **same `pool.gate`**, the entitlement is rechecked before `Math.addExact`, operations
   assignment, `counted=true`, and frame activation with the pool issuer. `setupReturned=true`
   still occurs only after that gated setup returns. The unchanged guard retains the same
   creator in its dispatch before preparing the same token's tail; the outer invocation
   holder still retains the prepared creator before calling `enter`. No holder/tail identity
   is substituted and no new registry is allocated.

4. **`endLeaseDispatch` (old511–540 → existing `end:720–753`).** Same initial frame snapshot,
   owner/authenticity/failed checks, dispatch-ended check, then guard-ended check. The
   uncounted branch still checks refusal then claims this creator's same CAS, ends its
   nullable tail, finishes its frame with the pool issuer, and marks the local ended flag;
   the same finally retains failure. The counted branch still checks current pool TL,
   frame-end claim, then creator-end claim. **`PoolCallFrames.restore(frame)` remains outside
   the monitor**, before the same-gate operations-positive check and `requireNotNull(tail).end()`.
   After that final epoch cut, only the existing operations decrement, same frame finish,
   local ended publication, monitor exit and return remain. No new allocation, callback,
   profile check or TL operation was inserted after that cut. Failure still invokes the
   same creator's failure path only when local `ended` is false.

5. **`failLeaseDispatch` (old542–552 → existing `failBeforeEnd:755–767`).** Guard order remains
   owner-lock → authentic creator → setup-started → frame-ended. Splitting after authentication
   cannot evaluate a later operand on an earlier refusal. `failed=true` still precedes the
   unchanged `pool.recordBookkeepingFailure()` (which uses the same gate). Only then does
   the original try attempt this tail's `fail`; its finally still tests
   `call.retainedCreator(this)` before `call.creatorFailed(this)`. This try was not broadened
   to cover the preceding bookkeeping call. No end, counter decrement or successful receipt
   can be manufactured by the refactor.

### Failed-entry restoration extraction

Only the original deepest `if (!counted)` body moved to private
`restoreRefusedEntry(frame, setupReturned):709–718` on the **existing** creator class.
The already-read local frame is explicitly forwarded, avoiding a replacement frame read.
It is called from the same inner finally; `if (!setupReturned) failBeforeEnd()` remains in
the enclosing try, so even its exception still reaches restoration.

The extracted sequence is unchanged: local `restored=false`; try the unchanged
`pool.refuseEntry(frame)`; set `restored=true` only on its return; finally call failure only
if not restored, then assign `refusedBeforeEntry = setupReturned && restored`. The assignment
is still skipped if that failure call throws. No exception catch/aggregation/return was
added; competing finally failures keep the same precedence. `refuseEntry` itself, including
TL restoration and frame refusal, is byte-unchanged. This helper adds no lock, async work,
shared state, successful end or recovery path and is not on the counted-success end tail.

### Other guard and test edits

- `Frame.select`: the unchanged issuer check still refuses before reading ended/caller/TL;
  the original three-condition tail and final `lease.select(lower, ownership, returning, kind)`
  retain their order, values and same refusal function.
- `quiescent`: `checkout?.actualEnded() != true || lease?.state?.epoch?.outerTailsEnded() == false`
  reads the epoch only if the checkout check passed, exactly as the two prior early returns.
  Acquisition, operation/dispatch/return, entitlement and consent/reclamation tests are unchanged.
- `verifyCaller`: copies the original connection acquisition, facade check, exact lease/entry
  lookup, conditional checked input, fault construction and selected publication, complete
  `fault.use` body and final evidence construction in their original order. It runs in the
  **same existing unstarted Thread's original try/catch**, not before Thread start or on another
  executor. Result publication still follows all caller checks and `use` cleanup. The original
  failure AtomicReference, gate-release/join finally, shutdown/abort observation, eight exact
  cut strings, retained checks and RETAINED/EXIT handshake remain in `verify`, unchanged.
- Pool-TL injection predicate: current Thread comparison → real `poolDelegate.get()` →
  `selected?.frame` → `selected != null` → `!entryFailure`, lazily and in that order.
  The null guard was deliberately **not** moved before the TL read. Core-TL predicate:
  Thread comparison → selected-null check → real `coreDelegate.get()` → `creator.call` →
  `coreFailure`. Local Boolean splits introduce no extra TL read or removal, and no injection
  or delegation body changed.
- `fatalRoute`: exactly twelve read-only initial assertions moved to helper179–192, called
  at the old location69, after lower/pool-entry identity checks and **before**
  `OwnedCallerTestScope`, gates or shims are created. Order remains: zero acquisitions;
  no pool frame; no actor frame; core1; max1; keepalive5 seconds; core timeout allowed;
  pool size0; largest0; active0; queue empty; completed0. Same lifecycle/closer references,
  no new receiver lookup inside the helper. All real-worker witnesses, route assertions,
  shim installation, release/restoration and finally boundaries remain untouched.
- Remaining edits only change braces/layout around identical expressions, parameters,
  argument order, statements, supertypes and named-test bodies. The existing stack assertions
  concerning `clientInfo`, `invoke`/`invokeClosed`, `invokeConnection`/`invokeGuarded`, and
  `afterJdbcCall` were not changed to accommodate the extraction.

## Preserved boundaries and next authority

No new class, field, lock, shared holder, registry, callback, retry, recovery, terminal authority,
producer count or epoch policy was introduced. No source-config contract or application repository
was changed. The earlier failed `OrdinarySourceGrantCleanupOwnershipIT` source and the existing
`OwnedCutPool` teardown in `PersistencePgOwnedCutIntegrationTest.kt` are byte-unchanged under the
original481 comparison; neither was repaired or weakened here.

All17 focused hosted invocations still require real PostgreSQL, including MODEL-labelled cases.
There is no new absent/unregistered-tail or retained-creator injection. PROCESS_ONLY,
`product_end=false`, child exit23, rejection of the positive success oracle, original gates,
deadlines and cleanup assertions are preserved. PG01 remains20 PASS/1 FAIL; its actor/queue
cause remains unmeasured by this author work.

The original freeze/result/reports and prior independent actual-diff review were not rewritten.
The earlier inert hosted-preparation directory remains unchanged: its eight artifacts match
its `SHA256SUMS`, whose hash remains
`0fb51c0338e95e97e509b4f50a018b9cc1bddf3692901a6e6dc69ae8e4fae686`.
It remains UNBOUND/inert, not authorization to run anything.

**Remaining:** primary-controlled fresh compilation and unfiltered Ktlint/Detekt, then any
separately authorized focused runtime/fixture verification and independent review. No current
static pass is asserted, and resulting complexity metrics, Kotlin compilation and exact formatter
acceptance have not been measured. The author found no additional source-level semantic concern
in the bounded diff; that is not a waiver of verification or an independent approval. No W03,
full-P3, Native05, consumer, production, new-data or recovery credit is earned; W06 is excluded.
