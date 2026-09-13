# CoreC2 after structural corrections — bounded real-PG selection advisory

2026-09-12 UTC. Independent Backend05 advisory only; **no dispatch/admission authority**.
Read the accepted production diffs, relevant changed test/helper paths, final two residual diffs,
prior exact-PG10 selection/acceptance and existing alternative selectors. No source edits,
build/checker/test, candidate/helper execution/import, download, service or CI action. Only this
private report was written. This is not another correctness audit or a new validation framework.

## Recommendation

**Use 14 existing ordinary @Test selectors in one existing class: prior exactPG10 plus four
specific affected negative controls. Do not run full47.** ExactPG10 remains the irreducible
RETURN/tail regression block, but it does not exercise the newly extracted failed-checkout and
failed-RETURN-entry finally paths or either changed negative auto-commit guard branch. Calling
PG10 alone validation of all those changed boundaries would overstate its coverage.

All14 use the existing class's lazy database and `withOwnedCutPool(database.value)`; no new test,
fixture, process-only probe or consumer witness is proposed. This keeps the one-class/one-PG
population design. Actual container events/ownership and final absence still require verification.
Four additional cases require an explicitly reviewed profile/count/request binding amendment;
**do not put14 selectors under a still-pinned exact10 request**. This advisory does not amend any
control, count, budget or artifact. If the primary elects only10, the four negative-path gaps below
must remain explicitly unqualified rather than silently credited.

## Exact selectors: 14 methods / expected14 ordinary XML testcase identities

Prefix every method below with
`me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest.`
for its exact Gradle selector; no class wildcard and no `()` suffix in the selector. Items1–10
are the unchanged accepted PG10 set/order;11–14 are the additions. Each name occurs exactly once
in the current source; no parameter expansion is involved.

1. `throwing original RETURN override leaves F G T free and retires its exact source without a second return`
2. `blocked overriding final RETURN sample spends the same real allowance and cannot commit after expiry`
3. `actual RETURN interruption defeats a false override while outer actor custody survives held restoration`
4. `throwing RETURN interrupt restoration cannot undo retirement or erase its actor failure`
5. `RETURN override InterruptedException publishes source failure before an overriding self interrupt can block`
6. `RETURN InterruptedException adaptation throwing another InterruptedException never retries restoration after actor end`
7. `RETURN InterruptedException adaptation throwing Error preserves that error without a late restoration callback`
8. `failed post consent real Hikari tail seals actor admission but cannot retire the successor epoch`
9. `consented real Hikari recycle tail retains no successor eviction or abort authority`
10. `exact retirement sample result preserves its Throwable and does not absorb adjacent budget failure`
11. `throwing overriding original checkout sample cannot orphan its captured handle or future return right`
12. `genuine throwing RETURN TL entry restores the authentic lineage and revokes only its still unused future right`
13. `real post commit Blob work cannot silently commit through Hikari auto commit reset`
14. `real commit failure retains unknown outcome and refuses reset before native auto commit`

## Changed risks and why each group matters

| Selected group | Actual changed boundary and existing oracle |
| --- | --- |
| 1–7: RETURN7 | Five lease phase helpers and typed Error/restoration handling, exact caller/budget and retirement/incident precedence. Existing assertions pin F/G/T freedom, the same Operation/transfer budget and1000ms allowance, retained actor during blocked restoration, actual frame/TL end, source retirement, one restoration/no late callback, original Error identity and sample counts. The extracted held/ended/completion assertion phases also execute. |
| 8–9: consented failed/ordinary tail | Old Hikari tail versus successor epoch/Entry ownership, live successor SQL, duplicate-close/abort non-authority and actor incident/factory policy. Both arms of the final `assertConsentedOldTailClose` extraction execute at the original try/finally site; successor assertion extraction executes. Real acquisition, graph calls, transfer facts and driver/guard finalizers exercise the changed physical/guard helpers. |
| 10: exact sample versus adjacent budget failure | Ownership's ordered locked retirement ladder, exact Throwable identity and sample count, expiry short circuit and the distinct throwing budget recheck. This remains a direct internal-boundary discriminator on a real pool, not opaque-eviction execution. Its newly extracted assertion body executes. |
| 11: throwing checkout SAMPLE | `GuardedDataSource.cleanupUndelivered` is otherwise not reached by the successful acquisitions in PG10. The existing test withholds exposure, injects the original checkout sample failure, verifies that same Throwable, captured source retirement, genuine transfer end, restored TLs and zero acquisition/future-entry/operation counts. It exercises entitlement revoke/handoff on the newly extracted failure path. |
| 12: genuine RETURN TL-entry failure | The moved `enterReturn` failed-entry delivery/revoke finally, not later admitted RETURN faults. The existing test checks the same injected Throwable, original REFUSED frame (not fabricated ENDED), exact lineage restoration, one injection, revoked unused entitlement, no transfer/Hikari close, retirement, and duplicate-close identity/no new operation. Its assertion helper was also extracted in structural12. |
| 13–14: pending and unknown auto-commit refusals | `PersistenceJdbcTransaction.beforeConnection` changed its ordered compound guard. One existing real Blob control creates pending native work after commit and proves Hikari reset cannot silently commit it; the other produces an actual deferred-constraint commit failure and retains UNKNOWN. Both assert refusal before native autoCommit becomes true, not merely failure of a later transfer commit. PG10's ordinary SQL does not assert either negative branch. |

The final guard residual only moves the same traversal with explicit context/TL object; real SQL,
return, terminal and descendant work above traverses the same guard. The final PG residual changes
one helper call and comments, covered by both tail modes plus the existing RETURN variants. These
two mechanical follow-ups do not justify repeating the already observed38 lifecycle/actor units.
They do require the primary's pending compile/static linkage check. The prior38 result is not a
replacement for this first post-structural real-PG run.

## Uncovered gates — do not turn this into full/native acceptance

- **Direct SQLClientInfo declaration/defaults/foreign-caller coverage is not supplied by these14.**
  The precise existing real-PG selector is
  `me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest.real lease preserves Properties client info defaults and declared stale and foreign failure shapes`.
  It is relevant to the lease facade's typed exception arms but belongs to a second class with
  its own lazy PostgreSQL fixture. Adding it would mean15 selectors/two PG-owning classes and
  require a different explicitly reviewed container envelope; it must not be smuggled under the
  accepted one-PG guard. Keep this narrower declaration-specific runtime gate open unless primary
  separately decides it is required for the claimed scope. The typed-catch source equivalence
  review is not a fresh execution of that control.
- The two existing process-only acquisition-END-TL/core-last-count probes, foreign native-stream
  cancellation and all opaque native hard-fault/first-close/liveness branches are not proposed.
  They remain distinct gates; an ordinary failed-checkout control does not prove post-facade
  ENDING failure cleanup or product completion after a process-only exit. No new failure is
  injected and no old negative oracle/budget is weakened to expand this selection.
- Moved descriptor/original-provider/consumer-provenance assertions are outside this RETURN/pool
  follow-up. Their consumer/loader/witness qualification remains open under its own profile.
  Do not treat ordinary use of the retained Native05 JAR as consumer or native qualification.

## Source/version and evidence pins

The structural adoption receipt records layout18 + structural12 across19 changed live paths.
A bounded read of those19 paths found only the two accepted residual successors relative to that
adoption map; no new freeze/inventory operation was performed.

- Current guard residual source: `f45890e53648b8e4abb30fdc9ff6250de6927413a9f510cc672babef1b43462c`.
- Current PG test residual source: `b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322`.
- Guard5 diff: `9e1c4acfada304890a5e16952874d1167202cb41d2ef633086068154d817d014`.
- Lease4 diff: `e3b915d96dcf1596f653df89cd6bdd84ec7884fe089f2184407e722a1870a421`.
- Test3 diff: `00467f58835636bd90c7f87ed3c6fed41d55a6d228f8c9142ff3bc235cf18226`.
- Guard residual diff: `e900a0730b39144e235f7e2d81687641c3597283c91dccca10aac45e030cc6dd`.
- PG residual diff: `20ed9c4e60173a816564e6e70fe39ef312d7ce39dcba1fa629a0fd056f769cd1`.
- Prior PG10 profile: `f721c8d972206b973b2d3aefa4246bbd2d768c66f6f2908c470b3f896526b339`.
- Prior PG10 primary acceptance: `c08b0f8ad69d674bedcb9edad54c99f51d34ccc7802c9272c53de3b81e56935a`.

Run34691665288's accepted10/10 binds source1c91 before layout/structural changes, and explicitly
excludes them. It cannot be silently carried forward. Require a newly matched source freeze,
normal source compilation/origins, exact selected XML identities, the same four original raw
BEFORE/AFTER diagnostic rows and their non-atomic limitation, plus original ownership/process/
container/output cleanup evidence. Keep existing timing/cleanup budgets; do not add prewarming beyond the existing test bodies,
stretch an allowance or retry unchanged failure as progress. Retained PostgreSQL kill9/die137 means prior
NORMAL_ABSENT was not graceful-shutdown or zero-kill proof; apply the same honest evidence reading
to any new run.

Historical full45/47 and original run34678157417's0 PASS/2 FAIL, cleanupFAIL, containersUNKNOWN,
outputs_absent=false and six retained directories remain unchanged. Native05 UNQUALIFIED;
D05 PARTIAL/not import-ready; D06 unreviewed/unexecuted; native/full/W03/App29 gates stay open.
Primary alone owns final selection/admission/dispatch and any explicit narrower risk acceptance.
