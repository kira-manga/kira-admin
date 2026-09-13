# App #29 W03 — integrated driver lifecycle completion

**Primary plan, 2026-09-08. REVIEW REQUIRED BEFORE PRODUCT EDITS.**

## Deliverable and scope

Finish the existing D1 runtime as **one working connection lifecycle**: a retained owner starts the
ordinary factory, explicitly prepares the cold deletion factory, opens real pgjdbc candidates,
handles rejection/late return, retires resources, and shuts down its own actors. Do not accept more
disconnected helper milestones. This is not a complaint API, a pool lease or completion of W03.

The authoritative requirements remain W03/P3, frozen D1 revision2 and its C6 amendment, except for
the explicit integration refinements below. Timer-A02 is the accepted baseline (283 campaign files,
2749 focused tests; `app-29-w03-d1-timer-a-02-primary-acceptance.json`, `c401e13f…`). Its completed
tests/reviews are not rerun before changes. All existing unbound kernels and their tests survive.
Runtime authority remains UNKNOWN. W06 stays excluded; no schema, legacy-data, app, Admin, website,
source-engine, dependency, TLS/auth-policy, release or signing changes belong to this deliverable.

## Investigation and integration gaps

The current code has real owned F1/G1/T1 opening/rotation and standalone timer operations, but no
managed root or genuine terminal-completion producer. `PersistencePhysicalFactoryBinding` can
admit and reconcile requests; it cannot reclaim dispatched records. `PersistenceFactoryWorker.owned`
still requires concrete create/discard/failure-retirement operations. Tests use explicitly MODEL
readiness and terminal adapters. Those facts cannot be promoted into runtime admission.

Two concrete interface gaps need coordinated changes rather than another isolated patch:

1. `PersistencePgDriverOpening.prepare()` constructs a Driver per prepared opening. The integrated
   root must retain the common guarded Driver and use that same object for ordinary/deletion
   templates and its matching timer metadata.
2. `PersistencePgTimerAccess.bind()` requires a NEW controller, whereas D1 starts the retained timer
   controller before ordinary bootstrap produces access. Preserve that existing cold binding API;
   add an exact-active-controller binding used only from the already retained timer controller's
   own body. Construct and publish its complete calls/cells/task before any acquisition or schedule.
   Failure before publication has started no timer operation; the already started actor stays owned.

The second change refines the standalone Timer-A construction order, not D1's start order. No
arbitrary running thread, replacement controller or unowned timer operation gains access.

## Concrete composition

### Retained owner and startup

- `PersistenceJdbcLifecycleOwner` retains one private `PersistenceJdbcDriverRoot`; the root retains
  both participants, their fixed ledgers/factory/terminal slots, one scanner and one timer controller.
  Construction is inert. No Thread.start, bootstrap, driver/timer invocation or I/O in constructors.
- Owner publication precedes the separate one-use `start()`. All actor references and start extents
  exist before start. Shared startup orders scanner, timer controller, then ordinary controller.
  Preserve `PersistenceRetainedPlatformThread`'s real start/body/termination distinctions.
- Ordinary controller performs common bootstrap once, retains its Driver immediately, prepares
  optional native bridge/timer access and publishes that preparation to the timer controller.
  Failed common guards close ordinary admission; optional native-only unavailability does not.
  The timer controller waits on retained state, binds from its authentic body, then acquires and
  captures once. Ordinary opening never waits for acquisition/capture or deletion preparation.
- Start all of a participant's fixed terminal runners, require their genuine READY entries, then
  start its retained F1 worker and require actual start return plus WAITING. Scanner startup must
  have actually succeeded. Only that concrete controller opens its candidate admission.
- `prepareDeletion()` is the separate one-use activation path. It starts no second root and changes
  no ordinary endpoint. Its controller requires common preparation, successful reviewed derivation,
  bridge identity and the READY timer generation before starting deletion factory/terminal actors.
  A separate non-I/O preparation observer uses one original 10s budget. Activation/start is not
  smuggled into that observer. Cold metadata/request/health reads cannot start deletion.
- Every start/admission/LIVE gate checks permanent shutdown. Actor failure closes relevant admission,
  records a safe fixed outcome and retains its references. No executor replacement or retry-start.

### Prepared openings and caller admission

- Add a retained-Driver preparation route, called only after common guarded construction. Preserve
  the old preparation path for existing tests. Validate the same prepared Driver class/loader and
  login policy; do not accept a general application-supplied Driver/provider callback.
- Prepare immutable ordinary-original, eligible ordinary-tracked-weak/strong and derived deletion
  openings around the retained Driver. Assess configured properties before adding the private
  bridge. Unsupported ordinary settings/bridge keep original provider behavior, not a global veto.
- Select the D1 §4.3 policy before dispatch. READY timer permits the strong ordinary route; pending
  or unavailable timer selects a new weak ordinary attempt. Deletion requires the strong route.
  A selected attempt never upgrades/downgrades afterward. Strong records retain the exact timer
  generation. One original system-clock request budget and the C6 F→G caller handshake remain.
- Concrete factory operations invoke `PersistencePgDriverOpening.invoke()` directly, obtain only
  the already prepackaged opaque candidate, and leave the capture scope before waiting for cleanup.
  No raw Connection, callback-based raw escape, pool lease or complaint capability is exposed.
- Record opening outcome/fatality and actual scope-call exit separately from success. A dispatched
  create that never invokes opening remains a proven before-driver case, not a guessed null result.

### Record boundary and terminal resource phase

- Each Entry preowns one terminal work identity and detached result cells. The fixed scanner performs
  C6 reconciliation and timeout/candidate/shutdown retirement, then dispatches that exact work to its
  physical-slot runner. Each runner has one mailbox, one retained platform thread, no submission API
  for arbitrary Runnable and no replacement. A LIVE candidate does not expire merely because its
  establishment budget later elapses; that budget governs attached establishment only.
- Keep F→G→T ordering. Concrete bookkeeping under those locks only; native calls, constructors,
  start, parking and timer scheduling are outside them. Contention retains pending work.
- Extend the concrete transport binding/owner with terminal operations: fence all further allocation
  and calls, request first close for every retained/late raw transport outside locks, and inspect
  exact constructor/close/call/outer-extent facts under T. Snapshot counts are never disposal authority.
  Failed close is not repaired by a no-op. Unknown constructor/native outcomes remain UNKNOWN.
- Terminal order is transport-close → stable raw decision → direct-executor abort → actual producer/
  opening/scope drain → exact timer boundary scheduling → first final Connection.close → applicable
  boundary/transport drain. Abort failure does not skip final close; no raw means no invented abort
  or JDBC-close success. Continue closing late transports while waiting for required boundary ACK.
- The raw grant is exact-once and retains raw in G. A still-active opening is WAITING, not NO_RAW.
  Do not consume the final cleanable before admitted timer-producing/finally scopes end.
- Extend timer calls with a private fresh-boundary constructor; no Timer/task escapes. A record's
  one-shot task holds only a detached exact-thread/ACK cell, not a root, record, callback or raw
  resource. Publish the cell before scheduling. Scheduling actual exit, return/throw, exact-thread
  ACK and producer fence are separate. ACK before scheduling exit cannot certify the boundary.
  No retry/cancel/replacement on failure or timeout; at most one pending boundary per record.
- Terminal resource phase becomes ended only when all required actual invocations for its fixed
  policy have ended. Failed-but-ended is distinct from successful disposal; pending cannot ACK.
  Apply **every D1 §8.1 row unchanged**, including ordinary NO_RAW_DRIVER_RETURN_ONLY after nonfatal
  no-raw return, weak close-failed UNKNOWN, known tracked-resource requirements, and no strong-to-weak
  escape. Preserve bounded sticky weak/unproved-provider evidence at root level, not history lists.
- Discard/create-failure waits only for this resource phase, then F1 can settle. Terminal body then
  observes F1 disposition and returns. Its runner clears mailbox/current payload before its final
  record-specific body-exit publication. No later old-record callback may touch a reused slot.
- Reclaim under the concrete F→G→T conjunction only after all fixed-policy resource facts, scope,
  processing receipt, resource phase and actual terminal-body exit agree for this exact identity.
  Broken/unresolved F1, failed unproved disposal or pending work retains the record. Resource-phase
  ACK alone, Future cancellation, Thread body flags and public snapshots cannot release capacity.

### Shutdown and observations

- `requestShutdown()` first sets permanent no-new-start/admission. Controllers seal/drain both
  participants; unprepared deletion becomes conclusively inert. All pending start/call/record facts
  survive. Fixed scanner exits only after no further possible completion/reconciliation remains.
- Failed-but-ended UNKNOWN records remain owned data, not an obligation to park otherwise idle
  runners forever. Genuine pending native/start/scheduling work keeps its actor/generation retained.
- Timer controller releases only its successfully acquired reference, once, after both participants,
  required record boundaries and actual factory/terminal/controller/scanner thread drain. It does
  not release an uncertain acquisition, retry a thrown release, cancel a shared Timer or touch a
  foreign ref. Captured Timer-thread termination remains a separate actual `isAlive` observation.
- Implement C6's trusted-platform non-I/O observers: budget before classification, no join/monitor/
  Condition/timed lock, no override calls, clear/restore only the trusted caller outside locks, and
  bounded positive parks using that same budget. Virtual candidate callers remain supported.
  Completion requires exact monotone no-future-start and termination/resource facts, not a mixed
  snapshot treated as linearizable. Return distinct pending/unknown/weak/strong-local evidence;
  no local result certifies the production runtime or remote session disappearance.

## Files/components to change

All Kotlin files below are in backend `common/infrastructure/persistence/` and matching test packages.

- New concrete owner/root, participant controller, terminal runner/work/completion, timer-boundary
  and managed-observer components. Split only by these responsibilities and existing static limits.
- Extend `PersistencePgDriverOpening`, `PersistencePgTimerAccess`, `PersistenceTimerReferenceCalls`,
  `PersistencePhysicalEntry`, `PersistencePhysicalFactoryBinding`, `PersistencePhysicalTransportBinding`,
  `PersistenceTransportOwner` and their closed protocol types for the integrated path.
- Narrow F1 worker/rendezvous changes only if required for actual binding/settlement; preserve all
  existing unbound behavior. No application bean wiring or generic callback/lock framework.
- Add integrated lifecycle tests and accurate `docs/COMPLAINT_DRIVER_LIFECYCLE.md`. Existing accepted
  tests and harness oracles remain; additions use separate fixture files where practical.

## Verification, compatibility and rollback

Retain D1 D01–D15 and C6-01–12; a smaller new test count is not a reduced gate list. Test the actual
owner, not fabricated `admissionOpen`/resource ACK assignments. Cover inert/cold startup, ordinary
success while timer is unavailable/pending, deletion refusal/activation, virtual callers, fail-fast
contention, late raw/abandonment, stable no-raw cases, each terminal policy, reuse without stale work,
root shutdown orders, actual timer pin/release and monitor-held observer timeout. Deterministic
own-project MODEL cuts remain explicitly distinct from real driver/native execution.

Use fresh sanitized child JVMs with the real pinned pgjdbc/Java21, loopback protocol/TLS fixtures and
disposable PostgreSQL17.6 for D05/D06/D13 session/constructor cases. Observer SQL uses a separate
owned process/identity, never a candidate raw getter. Exercise queryTimeout/readOnly/type-lookup
variants without changing them to make tests pass. Preserve real same-Timer held/queued/canceled
task tests and the unfenced negative control. Missing feasible local evidence remains unfinished,
not an external-only waiver. Full later JDBC/lease/return gates still belong to the next W03 capability.

Before actual acceptance: freeze the complete changed source/test diff, run focused tests plus
unfiltered Ktlint/Detekt, review every failure, then obtain both independent actual-diff reviews.
Use the existing isolated Gradle home and dependency route; no global cache deletion or additional
concurrent builds. Every batch: immediate owned stop → retain required evidence → scoped clean →
stop → verify owned processes/output absence. Preserve required synthetic artifacts until consumed.

This unused issue-branch slice has no data/API migration. Rollback removes only this attributable
integration increment, not W01/W02, existing accepted foundations or owner WIP. Do not deploy/merge
App #29 until its complete packages and post-merge requirements pass. External production image,
provider/DNS/TLS/native timing, remote-session, storage/device/store gates remain UNVERIFIED.

## Alternatives and review decision

Do not solve the NEW-controller mismatch by starting a second timer controller, constructing a
Driver on the Timer thread, gating ordinary availability on timer readiness or starting during a
bounded observer. The authentic active-controller binding preserves the retained root's start order
without any timer operation before calls publication. Reusing one guarded Driver is simpler and
avoids parallel bootstrap identities. Do not replace the chosen architecture with an unguarded
Hikari/raw-JDBC shortcut to move the percentage.

Both independent reviewers must challenge these concrete refinements, terminal deadlock/reuse
conditions and runtime API contracts. Use version-specific authoritative sources; reuse verified
source research where unchanged rather than creating repetitive provenance work. Report blockers
and required changes concisely. Implementation begins only after both approve and primary records
agreement. Acceptance applies to the integrated lifecycle, never another helper-only checkpoint.
