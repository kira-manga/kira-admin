# Integrated lifecycle — in-cycle corrections

2026-09-08. Corrections to the approved integrated design, not another helper acceptance.

Development01 compiled and ran 45 tests: 44 passed, one ordinary/deletion coexistence case failed
with CREATE_FAILED. Four formatting and 22 Detekt findings also failed; they are not waived.
All stop/preserve/clean/stop steps passed. The precise cause of that one runtime failure is not
yet attributed; fixture exceptions are now preserved rather than hidden during failure cleanup.

Independent implementation review exposed three concrete integrated defects:

1. Managed F1's already-admitted opening and PRIMARY G cuts can fail purely because the scanner
   holds G briefly. Keep unbound/AUX/foreign fail-fast behavior. Only the authentic managed F1 may
   wait for G with no F/G/T preheld; revalidate the exact entry, closure, original budget and actual
   trusted interruption after acquisition. Never wait for T under G or retry a refused ticket.
2. Scanner exit can race a contended final reclamation pass. After permanent shutdown and genuine
   participant work/thread drain, require both final reconciliation/reclamation passes to finish.
   Empty and positively failed-ended slots count as examined; contended/pending work does not.
   A completed scan is not successful resource disposal; UNKNOWN records remain owned.
3. Managed deletion inherited the ordinary caller budget rather than its derived 2000ms policy.
   Share one inert deletion policy between settings derivation, F1 and request construction,
   before the original caller budget starts. Do not reset budgets or change ordinary settings.

Primary traced both sides of each correction. Both GPT-6-Astra/max reviewers accepted this direction
with the above safeguards. Their messages and the development regression/matrix reports are
implementation advice, not final actual-diff acceptance. Scope remains within the approved plan.

Required evidence: deterministic held-G claim and both PRIMARY cuts (including expiry/seal), final
scan contention and failed-ended controls, a deletion progress/heartbeat timeout that cannot be
mistaken for socket idle expiry, actual PostgreSQL/TLS/constructor cases, full baseline-plus-new
tests, unfiltered statics, and both final actual-diff reviews. Preserve failed runs. W03 incomplete;
W06 excluded; 2/9 unequal packages and 0/152 delivered issues remain unchanged.

## Executed red regression

Red02 (finished06:20:41 EEST) compiled and ran31 lifecycle tests. The three new deterministic
held-G cases failed at the intended assertion for claim, PRIMARY prepare and PRIMARY install;
all28 earlier lifecycle cases passed. Unfiltered Ktlint/Detekt passed. Every cleanup command
passed, source hashes stayed fixed, both output paths were removed and no owned JVM remained.
Evidence: `../working/app-29-w03-integrated-driver-development-red-cycle-02/`.
This proves those three contention defects; it does not retroactively attribute the earlier
coexistence failure. The agreed corrections are now implemented and require fresh validation.
