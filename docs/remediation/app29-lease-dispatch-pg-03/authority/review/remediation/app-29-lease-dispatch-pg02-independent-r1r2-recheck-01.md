# W03 PG02 — finite independent R1/R2 recheck

2026-09-13 UTC · `w03_static_nonauthor_review` · NONAUTHOR.

**ACCEPT SOURCE ONLY. R1 and R2 are resolved; the prior actual-diff HOLD is lifted
for the exact source below.** No execution, static-analysis result or fresh run authority
is implied. This rechecks only the tiny helper correction and unchanged two-file scope.

## Exact binding

Backend HEAD remains private `8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3`.
Prior review: `app-29-lease-dispatch-pg02-independent-actual-diff-review-01.md`,
SHA256 `20aa2d84cb1733042c5524e99c322b43558875a333ecde52150d3fff66f13a1c`.

Under `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`:

- `PoolLeaseDispatchCreatorIntegrationTest.kt`:
  **`3c0010170b07b1edef3f87894dac6833f2ae2f02e841609cd5e3e15d9ce489d5`**.
- `PersistencePgOwnedCutIntegrationTest.kt`, unchanged from prior review:
  `7a0d78b74ab590d5fc270b4a274b38dfadd2ce38a2880f951758f101d0441465`.
- Full two-file full-index diff against HEAD, independently hashed:
  **`5863c74f412084188effed1ef519ce1ff77030ba7c20a9abd6f0b0d6893ff663`**,
  +262/-84. Git still reports only these two modified test paths.

In-memory reversal of exactly the three reviewed helper edits reproduces the previous
whole-file SHA `901e29adf7b81bfcbd3f0358b3f61edf86268f83ed459a5d576bb04f4f791fa2`.
Thus the incremental source delta is bounded to those edits, not inferred from a summary.
My independent unified-diff rendering hashes
`09d0345e9951e4997ba94e89e0e71f3663fa0d4872d00891924fb029466b75b7`.
The supplied author-rendering hash `fc5fb26cfe5f182f187ff54f98d79a05c75b0e5498acaa69b2626cca91f2bdca`
was not separately reproducible from an available file; acceptance binds the verified
whole-file and full Git diff hashes, not an assumed formatting identity.

## Findings

- **R1 resolved:** `retain` now preserves each distinct later observed error on the
  stable first Throwable, using the existing self/duplicate guard. The prior F → C → E
  path keeps C before EMF destruction can replace its escape. Expected-expiry exclusion
  is unchanged. Removing restore's redundant preservation call is consistent with this
  centralized behavior and does not remove restoration or rethrow.
- **R2 resolved:** final `describe`/`println` is inside a catch. With a saved first
  error, reporting failure is secondary and that first error is still thrown. If
  reporting is the only failure, it is rethrown rather than silently passing.

No further fixture, assertion, stage, budget, clock, actor, source-selection or cleanup
change occurred. Prior paired-lifetime/default-path review and348-path scope assessment
stand. Suppression-disabled Throwable behavior and pre-callback EMF-init masking remain
explicit limitations; no production exception change or broader fixture claim is made.

Next: primary's changed-Kotlin statics under existing baselines, exact checkpoint/fresh
freeze retaining all348 seeds, then separately authorized **failed2 only** with normal
required compilation. No additional default controls are justified by this helper delta.
Prior16PASS remain historical; no runtime correctness or acceptance credit is granted.

Only passive source/Git/hash/textual-diff reads and this new private0600 report were used.
No edits to source, target/helper execution/import, checker/build/test, freeze, commit,
CI, acquisition or resource-control operation occurred.
