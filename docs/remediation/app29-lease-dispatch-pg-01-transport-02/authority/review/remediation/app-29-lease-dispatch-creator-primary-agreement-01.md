# App29 — lease-dispatch creator correction: primary agreement01

2026-09-13. **Authoring authority only; not execution, acceptance or integration.**

Primary read the complete source investigation (`ec9ed982cbe8325444b842e4c32cadea781ef8c65d4c770a12ee18a2c82bdc18`)
and independent concurrency review (`6ee1c1726b93b49775f33387835b79c45e04fa91da514e48bda9447b97bc83ec`),
and inspected the current exact-epoch, outer-call, lease-completion, transfer and pool-caller seams.
Both reports are under `review/remediation/`, named respectively
`app-29-ordinary-implicit-eviction-source-investigation-01.md` and
`app-29-lease-dispatch-creator-concurrency-review-01.md`.

The missing legitimate implicit-eviction creator route is a demonstrated source defect. It is
not a diagnosis of PG01's unobserved actor/queue state. PG01 remains20/21 FAIL; the original
shutdown budget and all historical source/result evidence remain unchanged.

## Agreed correction

1. A separately authored non-consuming, one-invocation creator ticket must be associated with
   the exact acquisition-bound pool/lease/epoch, authentic admitted guard and actual caller.
   The sole future RETURN/EVICTION right remains untouched. No new native/JDBC admission.
2. Establish guard cleanup before fallible ticket setup. Retain before publication/counting;
   partial setup/restoration/end failure stays sticky and outstanding, never a fabricated end.
3. The ticket covers the complete outer connection/descendant invocation, including failure
   adapters reached from finalizer failure, JDBC/core restoration, finalizers and afterJdbcCall.
4. Register its tail while the genuine guard producer is admitted in the EXISTING exact-epoch
   ledger. The obligation participates in sealedAndEnded and exact lease quiescence/transfer/
   native completion; no zero-count gap, new registry, ownership-lock-to-pool callback or scan.
5. Refuse reentrant self-wait even after original JDBC/core thread-local restoration. Use coherent
   cross-pool nesting: wrong/stale/unadmitted top lineage cannot fall back to an outer actor/ticket.
6. Separate actor-creation provenance from isAuthenticPoolCaller/lower native fallback. Preserve
   original-caller BUSINESS and the existing distinct cancellation rights, hard faults, budgets,
   actor capacity and complete Worker/replacement termination proof.

Implement only these boundaries and the focused regression families specified in the independent
review. The real Hikari connection/descendant MODEL cases must observe the zero-worker initial
state and actual close-worker/drain route, not an arbitrary factory call. Tail/identity/failure
cases must prove the load-bearing rights and completion contracts, not add trivial duplicated tests.
The eventual real-PG acceptance is the one existing failed method, unchanged assertions/budgets.

Work on the existing PRIVATE backend App29 branch at ccdbb28f6362117882501b4da040257be6fc1990.
No public push of this ancestry; no broad runtime/CI launch or source freeze until actual-diff
review and primary admission. Preserve all348 historical seed paths and the current478-source
manifest; add a new candidate rather than rewriting old evidence. W06 remains excluded;
new-backend-data and installation recovery remain required. No W03/package completion credit.
