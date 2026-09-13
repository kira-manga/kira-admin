# W03 lease creator — primary bounded PG02 correction/diagnostic plan

2026-09-13 UTC. Test-only next slice on the existing PRIVATE App29 issue branch.
No production lifecycle/JAR change, execution, freeze or retry is authorized by this plan alone.

## Actual input and non-conclusions

Read complete independent actual-result review
`app-29-lease-dispatch-pg01-transport02-independent-actual-result-review-01.md`
SHA256 `0cd81ef933388b61e3f512bcd915962e9eced17ede60f32a6ce0698b76a1f8d4`,
its two test methods, clock, authentic pool/phase and close fixture seams.
Run34762007741/carrier6794795/source8938526 is **16PASS/2FAIL**, not accepted.
The nested pool test returned from its body but failed in inner pool full-end observation;
SharedTimer pin/teardown ordering is structurally supported, not measured actor attribution.
MODEL line613 proves only a false conjunction. Its broad sanitized phase exception hid
which setup/lower/callback assertion failed. Neither failure permits a production fix by guess.
All old raw failures and all348 development07 seeds remain evidence, unchanged.

## A. Paired test fixture lifetime (correction, not a timeout change)

Only the mixed-pool test needs two simultaneously live roots. Request shutdown and invoke
actual shutdown for both owned pools before demanding full termination of either shared-Timer
root. Preserve every existing body assertion, receipt/actor/root end check and budget.
The ordinary one-pool fixture must remain semantically equivalent by default.

Preferred bounded seam: split the existing OwnedCutPool request/actual invocation from its
unchanged await/assert phase; provide paired-use glue or a test-only before-close companion
hook with standard `use` failure suppression. Author chooses the smallest clear form.

Required exceptional behavior: startup/body failure cannot omit either owned pool's shutdown;
request/invocation failure for one must still attempt the other before waiting. Keep original
body/setup failure primary and cleanup failures suppressed in deterministic order. Do not
introduce a new thread/executor, release another root's timer pin, write counts/tokens/receipts,
change polling/budgets, synthesize termination, or delete any existing oracle. No peer lifetime
change may leak into the one-pool default path. Avoid broad refactoring of the large fixture.

## B. Preserve the MODEL first failure (diagnostic, not a speculative correction)

Retain test-local first unexpected setup/shim/lower/callback failure before the production phase
sanitizes it. Capture a finite set of factual stages: store entered, lease/setup obtained,
lower call returned, clock armed/entered, original budget/guard/tail witnessed, MODEL expiry,
retirement observed, actor constructed/started/terminated, final witness completed. Record only
facts actually reached. Retain the expected phase `code`, `databaseOutcome`, `cleanupProven`.

Preserve the deliberately expected JDBC/phase expiry separately from unexpected assertion/setup
failures; simply rethrowing every caught JDBC timeout would make the successful oracle impossible.
Restore the actual delegate/clock and perform authentic phase/fixture cleanup even after failure.
Surface the first unexpected original Throwable outside sanitization, preserving its identity
and suppressed later restoration/cleanup errors. If no unexpected failure is captured, missing
witnesses must still fail with bounded factual diagnostics and the separately retained call/phase
outcome. Split `witnessed && actorRan` into named assertions; do not weaken either requirement.
Retain remaining tail/quiescence/admission assertions. Keep MODEL labeling and the real
`afterJdbcCall` route; never substitute a fake creator, actor, dispatcher or final receipt.

Prefer one small test-only diagnostic helper (if needed) over long repetitive catch blocks.
No raw production credential/payload logging; synthetic test stack evidence stays private.

## Review and smallest validation

A distinct nonauthor reviews this plan and the actual delta, including exception precedence,
startup failure, peer shutdown order, original-budget use and finite stage attribution.
The correction author must not approve their own changes. Check only changed Kotlin files with
existing static baselines; no suppression/config expansion. No build/test/acquisition by authors.

After exact source review/checkpoint/fresh freeze retaining all348 seed paths, primary will bind
a new profile derived from the existing admitted PG lane: **only the two failed methods** first.
Normal test compilation/required main dependencies are permitted; carry prior unaffected16
separately, not as fresh18. If a shared fixture change materially affects default behavior,
add only affected existing controls justified by actual diff review. No full47/old-suite replay
for reassurance. The MODEL diagnostic attempt may still FAIL; report its actual outcome and
then fix only the demonstrated cause. No correctness credit for merely better diagnostics.

Existing finite controller/ownership/transport machinery must be reused rather than recreated.
Keep private backend8938526 ancestry and any successor bundle private; never push it publicly.
Immediate owned stops, preserved raw evidence, scoped cleanup, final stops and8GiB floor apply.
Native05/consumer/full-P3/new-data recovery/W03 and App29 package acceptance remain incomplete.
