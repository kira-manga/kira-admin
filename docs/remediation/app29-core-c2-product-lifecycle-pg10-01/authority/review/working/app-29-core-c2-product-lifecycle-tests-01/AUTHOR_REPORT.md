# CoreC2 test lifecycle tests01 — Backend02 authorship handoff

2026-09-12 UTC. **Stable source-only candidate. Not compiled, checked, executed or qualified.**

## Authority, scope and binding

Only the three existing tests authorized by primary agreement
`review/remediation/app-29-core-c2-product-lifecycle-primary-agreement.md`
(`0dfc179ee33f5349283aeb2876e850d0c13f5cbbcc3edebbb15c570e736403dc`) were edited:
`PoolLifecycleTest.kt`, `PoolActorCustodyTest.kt`, and
`PersistencePgOwnedCutIntegrationTest.kt`. Paths are under
`kira-backend/src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`.

Baseline is private `eb8fed8b6b620a0c7448c223bf49c1683f8eaadc`. Before-images/pins were
saved before authorship. The final scoped diff is **255 insertions / 1 deletion**;
the deletion replaces an ignored stale-eviction return value with an explicit
`Refused` assertion. Three new test methods declare five invocations, including
the three MODEL hard-dominance variants. No new suite, runner or qualification
harness was authored. Read-only status shows exactly the authorized product5/test3.

`authorship-binding.json` binds the agreement, accepted plan, independent plan review,
stable Backend03 product01 report/patch/after manifest and unchanged fixture pins.
`before/` and `after/` retain the three source images; `source-pins-*.sha256` name
repository-relative source paths. `tests.patch` is test-only against the baseline.

## Focused authored coverage

- **Exact incident authority and clean final cut:** one MODEL test uses an uninstalled
  inert pool so an unrelated `INITIALIZATION_FAILED` cannot pre-seal the factory.
  It refuses PREPARED, foreign-thread, wrong-pool, wrong-kind, non-top and ended
  calls. The fabricated Operation reuses the **genuine current ACTIVE RETURN frame
  and consumed entitlement** but lacks exact prepared-Operation identity; refusal
  leaves the genuine and other pool unchanged, before and after the real incident.
  Authentic recording keeps the exact budget/frame/count/right, denies new business,
  records sticky BOOKKEEPING_FAILED and leaves the factory open. A duplicate incident
  cannot add authority or end the frame. Only genuine end/one inert close/observation
  yields the empty sealed UNKNOWN cut: future0, operations0, constructing0,
  retainedGenerations0, sticky failure and identical repeat UNKNOWN snapshot.
  This is MODEL state coverage, not connected-pool/native completion evidence.
- **Hard dominance:** one parameterized MODEL test covers incident→null-factory hard,
  null-factory hard→incident, and incident→the exact generic
  `Operation.failBeforeEnd()` API. Each decisive cut precedes the enclosing inert
  acquisition's later startup failure. The incident-first factory variant emits and
  genuinely starts/ends an authenticated platform actor while business is denied.
  A hard fault seals despite an existing firstFailure; repeated incident cannot reopen
  it. The authentic RETURN remains counted and its completion unpublished until its
  actual finally. Existing C64/NEW/96-generation/replacement/caller-runs tests are untouched.
- **Exact retirement-result origin:** one real owned-pool test directly probes
  `retireLeasedState` with the existing overriding original-caller fixture. It checks
  original Throwable identity, exactly one callback, unchanged live source and
  unconsumed future entitlement. Original expiry returns Refused without another
  callback. A distinct exception from the post-sample budget read propagates unchanged,
  not as CallerSampleFailed. A separate valid direct claim returns Claimed and seals
  its exact source. These are explicitly internal-boundary probes, **not** a fabricated
  admitted RETURN or Hikari completion receipt. The one subsequent real close retains
  its own fixed1s Operation allowance, actually ends it, refuses a second ingress,
  and requires exact Entry absence plus real caller termination and ordinary fixture teardown.
- **Existing real incident regressions:** both original test bodies/selectors are
  unchanged. Existing helper assertions preserve the original faults, old-tail
  same-Entry/PID fresh-root/nonretirement checks, holder/dispatch/Operation custody,
  interruption/restoration behavior, actual Entry absence and native cleanup. Added
  assertions require the original repeated retirement sample exactly once and an
  unsealed factory before shutdown; the failed old tail similarly leaves the authentic
  successor's creation rights intact before its RETURN. The stale old-tail eviction
  now explicitly returns Refused. Only the original two diagnostic-tagged clean
  incident final cuts add retainedGenerations0, sticky BOOKKEEPING_FAILED and repeat
  UNKNOWN/identical snapshot to the existing future0/operations0/constructing0/sealed
  obligations. Deliberately unresolved NEW/process-only negatives are untouched.

## Deliberate coverage boundary: no new opaque real-PG hard-catch oracle

During authorship, an extra draft fixture would have thrown at the eviction caller
lookup **after** the original sample incident and before Hikari. Source review with
Backend03 identified that its mandatory hard seal could recreate the cold-closer
queue obstruction during ordinary shutdown. Native Entry absence does not discharge
that queue. There is no asserted existing-worker/scheduling guarantee.

Primary explicitly concurred with dropping **only that unexecuted extra draft** and
substituting the MODEL generic-hard API variant plus exact sample/adjacent-budget
discrimination. Its temporary enum/seam/test were removed before this packet was
frozen; neither original real fault was removed, changed to process-only, or weakened.
The product's generic eviction catch still calls the unconditional hard API; that
statement is manual source review, **not execution of a later opaque eviction error**.
This decomposed coverage cannot establish clean in-process teardown for arbitrary
Hikari/submit/bookkeeping failure after an incident. Backend05 must independently
assess adequacy and primary retains execution/acceptance authority.

This final selector disposition supersedes the anticipatory phrase about a distinct
later eviction-authentication test in the already-frozen product01 report's deferred
selectors section. That product packet is unchanged. No early cleanup, worker
prewarming, native shutdown/epoch retirement workaround, widened budget, extra cleanup actor,
start-of-NEW during cleanup or process-only harness was substituted to force a pass.

## Review performed, deferred work and retained history

Manually reread the scoped diff and directly implicated lifecycle/result/caller/
budget/fixture code; copied and hashed source/evidence. No build, test, checker,
formatter, compiler/import probe, candidate/helper execution, service, CI/network,
Git mutation/ref change, tracker change or prepared Ktlint execution was performed.
No product or shared helper source was edited by this author. Telegram updates remain
primary-owned. No owned background work remains.

`SELECTORS.md` is a coverage menu, not a runner, source freeze or admitted selection.
Backend05 reviews the combined actual product5/test3; primary chooses the smallest
meaningful Linux/static/unit and targeted real-PG follow-up, retaining unaffected
successful evidence rather than automatically replaying full47. No runtime pass is
claimed here. Original exact-two **0/2, cleanup FAIL**, full47 **45/47**, W03 incomplete
and App29 **2/9** remain. All348 historical development07 seeds/manifests/evidence stay
immutable and must remain covered at the next primary freeze; W06 remains excluded.

## Stable artifact pins

| Artifact | SHA-256 |
|---|---|
| source-pins-after.sha256 | b5eed778684969fbf3e8e3afd41a316be62f4dd5cbeb1b595de00aadfe578754 |
| tests.patch | c5ec7b34ee75390c9e0f4c1443e7a5e69112a124023ee20c2cbf2ffb434f7d6b |

`SHA256SUMS` binds all packet files except itself, including this report. Any requested
revision after this handoff needs a distinctly identified successor binding.
