# CoreC2 product lifecycle product01 — Backend03 authorship handoff

2026-09-12 UTC. **Source-only candidate; not compiled, executed or qualified.**

## Authority and scope

Implemented the five product files authorized by
`review/remediation/app-29-core-c2-product-lifecycle-primary-agreement.md`
(`0dfc179ee33f5349283aeb2876e850d0c13f5cbbcc3edebbb15c570e736403dc`).
Accepted plan remains `d42458d346727c947313db631f4f2ad710a45fad6fa31b2a8599e65309b791dc`;
independent plan review remains `70ba9317eeef7491056b4598f63c1ff2337f3a69e7fc83d155f24be3c1050555`.

The pre-edit backend worktree was clean and all five live hashes matched the saved
before-images. This packet is product-only, against the primary's private App29
baseline `eb8fed8b6b620a0c7448c223bf49c1683f8eaadc`; no ref/history operation was performed.
The product diff is **5 files, 70 insertions, 16 deletions**. No tests, harnesses,
native/ABI/dependencies, frozen evidence or historical seeds were edited by Backend03.

## Actual changes and source review

- **PoolActorCustody:** separate incident recording makes BOOKKEEPING_FAILED and
  business refusal sticky without writing factorySealed. Existing hard failure still
  seals unconditionally, including after an incident. Empty/closed population proof
  now seals before sticky UNKNOWN; construction/live/NEW refusal ordering is unchanged.
- **PoolLifecycle:** `Operation.recordReturnIncidentBeforeEnd()` checks ownership-lock
  refusal, then exact pool/issuer/original Thread, ACTIVE current RETURN frame,
  authentic entitlement and its exact prepared Operation under the existing gate.
  Foreign/fabricated/ended/ENDING calls reject unchanged. Only after exact identity,
  broken consumed phase/count hard-fails without ending anything. A valid incident
  changes neither retained counts/phase nor budget/native/epoch state. Existing
  failBeforeEnd APIs, observation-before-expiry prohibition and owner observation remain.
- **PersistenceOwnership:** the closed internal `PersistenceLeaseRetirementClaim`
  contains Refused, Claimed and CallerSampleFailed(original Throwable). Only the
  exact `caller.sampleOutsideLocks()` invocation is caught into the last result.
  Original budget → actual flag → outside-lock sample → same budget order and
  G-tryLock/rechecks/mutations are preserved. Result-construction and every other
  invariant/lock/budget failure remain outside this catch. Failure toString is redacted.
- **GuardedDataSource:** obtains the claim itself; only its returned Claimed invokes
  the existing Hikari eviction. Refused/sample failure returns before Hikari. Claimed
  is a source-retirement claim, not a Hikari or native completion receipt.
- **PersistenceJdbcLease:** changes only the existing sample/consented-tail predicate
  to incident recording and handles the positive retirement-sample result separately.
  Generic eviction/submit/authentication errors stay in the unchanged hard catch,
  irrespective of an earlier sample-failure flag. Exact owner/handle/original Thread/
  RETURNING/no-consent/current-source/one-CAS claim checks, original failure precedence
  and all holder/dispatch/Operation finalizers remain.

Manually read the complete scoped diff and the directly implicated source/callers.
No compiler, build, test, formatter, checker, candidate/helper, service, CI or network
execution was performed. File copying/hashing and read-only status/diff are packet
provenance, not runtime verification.

## Regression ownership / deferred selectors

Backend02 owns the three existing test files, separately: PoolLifecycleTest,
PoolActorCustodyTest and PersistencePgOwnedCutIntegrationTest. API/result names and
forged Operation identity rejection were coordinated before editing. Their bounded
authorship covers incident authority and accounting, hard dominance, authentic
post-incident actor creation and the empty sealed UNKNOWN cut; exact retirement
sample origin and a distinct later eviction-authentication failure; plus preservation
of the original two real fault fixtures and seven RETURN variants. No authored or
executed test result is claimed by this report; Backend02 supplies exact test selectors.
Backend05 remains the independent reviewer of the actual stable product/test candidate.
Primary chooses and authorizes any later Linux/static/unit/real-PG execution.

## Remaining concerns / retained evidence

- This preserves the **existing authenticated creator closure**, not cleanup-task-only
  authority, a new borrower capability, a no-internal-physical-attempt cut or a liveness
  guarantee. C64 still bounds retained unretired generations, not lifetime creations.
- An unresolved NEW/live actor or failed end remains unresolved. An arbitrary UNKNOWN
  is not proof of empty actor/native custody. Original budgets and expiry-first
  observation remain; no retry, prewarm, additional cleanup actor or early native
  shutdown/successor retirement was introduced.
- Compile/static conformance and behavioral sufficiency remain unverified. The
  original diagnostics remain **0 PASS / 2 FAIL**, cleanup FAIL; historical full47
  remains **45/47**. No native/W03/App29 qualification changes follow from authorship.

## Stable packet

All paths below are relative to this directory. `before/` and `after/` each retain
the exact five product files. The two manifests bind their bytes; `product.patch`
contains only these five changes (paths relative to kira-backend).

| Artifact | SHA-256 |
|---|---|
| before.sha256 | dd5442611ae712b284d2c8fdb9fe25b73ebf3c6d91e10eefd7980eca05cec3e5 |
| after.sha256 | daa73d5b0bd6275feac48edb94216a99fc388f6f08f64477b14ff5122326390e |
| product.patch | 072ebf2eaa07f9fd109d9056d2000add7cba5b25dd451cab0c86c14a876fbfda |

No owned background work remains. Product5 are stable pending independent review;
any requested revision requires a separately identified after-image/patch binding.
