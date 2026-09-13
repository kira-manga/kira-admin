# App29 RETURN adaptation C2-01 — independent source-only review

2026-09-11 UTC · `/root/backend_04_independent_review` · **NONAUTHOR / REPORT ONLY**.

**Disposition: the reported C2 restoration-tail source defect is corrected in this successor;
no new source-level blocker found in its two-file delta.** This does not convert an authored
discriminator into a passing test or approve connected-core/native/actor composition. **47 textual
declarations; ZERO executed.** Runtime qualification and all wider co-gates remain open.

## Exact reviewed scope and independent integrity

Packet: `review/working/app-29-real-pool-return-adaptation-c2-01/`, not the live checkout.
Baseline `49da0919d9ec3091cb7bb041009dc9bd5f3e090f` remains **PRIVATE / NEVER PUBLICLY PUSH**.
Review authority is the minimal Lease/Integration C2 correction, not other author-owned work.

| Packet output | Bytes | SHA-256 |
|---|---:|---|
| `SOURCE-ONLY-HANDOFF.md` | 10041 | `0ee8615d43bcde77a2ec4fc795ffe95fddb6f4c303db5d05df80652d7f8e90a4` |
| `source-manifest.json` | 25698 | `e8f783786c058b39094483488a0a49045a74f81de99733a0bad00051a54d897a` |
| `before-manifest.json` | 13522 | `13872ecd0ef3e37d7d18209886f7847fcbb3d976c544173163fe98decfa82953` |
| `c2-delta.patch` | 13666 | `f9606bc8d4edb1ed0adf9e7169e3784c99f1d6bd8430cdc23132151446ae8e35` |
| `owned-core-and-probes.patch` | 197810 | `46e3d100706abe1f3e74f83d5635203f3fd570a635a8eaf384c699b55180a3df` |
| `test-source-inventory.json` | 18581 | `823f49b359b8dec60d1b024c2bfd4e3d2d6822a42fed1a8c8d0e905b5ba87650` |
| `SHA256SUMS` | 7809 | `be592b90b4b057f20b7651ecc3c34c9cf24e819857be9dfe0dcf8991bb5713fa` |

Exactly one product and one test path change, under the backend persistence package:

| File | Before SHA-256 | After SHA-256 / bytes |
|---|---|---|
| `src/main/.../PersistenceJdbcLease.kt` | `f486b296d822d7bdbe39a69474a5537a6b0de85958b7be4be8be04c2ec91e043` | `dd73ba8b486e285ac76c16e56d98bdac475027c86fed9eb5ffe3f7c1a5a820fd` / 13504 |
| `src/test/.../PersistencePgOwnedCutIntegrationTest.kt` | `d2deb0973b6bcf98e62e19c244bdd69b0f0d756cf43ac952855e0aaf50aae9e6` | `2be392d5768db39dce43832be3eb12d3b6d724b60d7a569f51c8be9b704aba7a` / 117449 |

Independently verified by read-only file/Git inspection:

- All21 before/after hashes and lengths agree with both manifests. Every before-image equals
  frozen pending-probes01; the other19 after-images are unchanged.
- Full patch reconstructs **15 tracked private49da blobs +6 absent/new paths,63 hunks**, with
  all full-index Git blob identities exact. The **two-path/12-hunk** C2 delta reconstructs the
  two after-images. Every per-path full/incremental size/hash agrees.
- All48 current checksums match and cover every other packet file. The immutable predecessor
  checksum sets also match completely: resume0163, resume0242, pending-probes0148 entries.
  All four packet-output and11 reference records match.
- Ten read-only control pins match: nine private49da sources, plus the separately accepted actor
  Storage image. Their worktree bytes also matched at inspection. The SafeJdbcFailure/C5 policy
  and fixture are not edited.
- Independent textual lists match private49da20 → resume0243 → pending-probes0145 → candidate47:
  Descendants16 and Integration31. Exactly the two declared C2 names are added; no old name is
  removed. This is not test discovery, compilation, all348 preservation or a passing count.
- The negative probe parent helper and entire `OwnedPoolPendingProbe` object remain byte-identical
  to independently reviewed probes01, as do all three process/recipe support files. Their separate
  review is `app-29-real-pool-pending-probes-01-independent-review.md`, SHA-256
  `a1cf24d7c4c6cbf698044f622c932e9a9afe14e7d944e3a3f6ce936bef48c87b`.

## C2 chain and correction

The original finding remains accurately recorded against immutable resume02/probes01 in
`app-29-real-pool-connected-core-resume-02-independent-review.md`, SHA-256
`705cb53e8369d20abadeb826cbff1b40ae83fb4bac7eebc9df01c8c84e47c320`.
Those bytes restored an original InterruptedException explicitly, ended RETURN, then submitted
the original IE to the global SQL adapter, which interrupted again after end. This report accepts
the correction only in the exact new Lease after-image above; it does not rewrite that history.

Line references below use frozen C2 after-images. The complete Lease76–200 tail, unchanged
GuardProtocol162 forwarding, private49da SafeJdbcFailure28–29/76–87, C5 helper, actor end and
outer Lease facade were inspected together:

1. **Disposition still precedes callback.** Lease115–134 retains sampling/consented-tail actor
   failure and requests exact unconsented-source retirement/seal before owned eviction. The same
   caller and original budget survive. No consented old tail gains successor retirement rights.
2. **Fallback is prepared while RETURN is retained.** Lease141–145 calls the unchanged adapter
   with a fresh fixed non-IE marker, yielding a detached SQLException without the original cause.
   This executes outside ownership locks and before holder/dispatch/actor end. It is also prepared
   on a successful RETURN; this is added bounded allocation, not a new budget or admission.
3. **Original IE gets one restoration.** Lease146–157 skips C5 restoration only for the original IE
   and adapts that IE here. SafeJdbcFailure78 supplies the single overriding `interrupt()`.
   Nothing in this block ends RETURN; a held callback still has ACTIVE/count1/creator-unended
   custody. The former separate original-IE interrupt and post-end adapter are both absent.
4. **Adapter failure is not recursively adapted.** If that overriding restoration throws another
   IE, Lease158–160 records actor failure and selects the already detached fallback. An Error
   thrown by the adapter/restoration is selected unchanged. There is no attempt to restore or
   adapt that nested IE again. The throwing override has unwound; it has not necessarily set the
   actual interrupt flag. Fallback-preparation failure itself is retained without a retry.
5. **Other primaries keep C5 policy and primary precedence.** For non-IE primaries, the existing
   C5 helper restores only a consumed actual flag. Its throwing callback records actor failure;
   an existing primary remains primary. With no primary, restoration failure selects the fallback
   or its Error. Any remaining primary is adapted inside this retained block, not afterward.
6. **Actual end ordering is preserved.** Lease162–195 then performs real transfer/dispatch ends.
   Their uncertainty still prevents operation end; an ENDING/TL failure is not manually retried.
   Later bookkeeping failures select the prebuilt envelope, or their Error when no earlier
   outcome exists, without starting a new interrupting adapter. Phase/count/completion writes
   remain with their authentic owners.
7. **No late adapter remains on this RETURN route.** Lease200 only throws the selected outcome.
   `LeaseConnectionCalls.invoke` does not adapt Connection.close SQLExceptions again and propagates
   Error unchanged. Thus the original IE cannot reach another self-interrupt after RETURN end.

The unchanged dependencies are explicitly pinned:

| Source | SHA-256 |
|---|---|
| `SafeJdbcFailure.kt` | `03b502ed83f9b323f7278273eb8b2dcb6fb22b8003f52310470170cd24cb63a0` |
| `PersistenceOwnedFactoryCaller.kt` | `b43a7c3251c9f84762a1befb65b5e531fe0052598b5f1a894eae53474dd9f28b` |
| `OwnedCallerTestScope.kt` | `0c77a20900256ef113d4b22ba1d38e4cbbc346a6851c262cd64d06ff779b4ee5` |

This is not a global weakening of SafeJdbcFailure, a blanket guarantee of successful interrupt
restoration, or a claim that arbitrary allocation/end faults have been exercised.

## Authored discriminators, not executed results

Integration739 preserves the original IE declaration. New declarations743/747 use the same
real warmed-Hikari/original-borrower helper1406–1530 for a restoration throwing a second IE and
one throwing Error. No detached MODEL actor or replacement process runner is introduced.

- The original RETURN sample is held only after authentic acquisition; its exact source/holder,
  original1s allowance, preissued Operation, future0 and activeOperations1 are observed.
- At the overriding restoration,1492–1499 requires retirement already visible, no consent,
  actual frame/completion unended, phase ACTIVE and **restores exactly1**. F/G/T availability is
  independently checked while the real callback is held.
- The original IE still yields a detached SQLException and an actually set flag after a returning
  override. Nested IE requires a cause-free SQLException; nested Error requires the exact injected
  Error identity. Neither throwing override is mislabelled a successful flag restoration.
- `caller.value()` waits for the actual caller to exit;1510 requires TERMINATED. Final1525 still
  requires exactly1 restoration for these cases, rejecting a second callback before or after
  actual RETURN end. Existing sample/actual-flag/restore/expiry cases retain their expectations.
- Exact Operation/budget identity, real end, no second future ingress, BOOKKEEPING_FAILED where
  expected and genuine Entry retirement remain required. The unchanged successful fixture's
  actor/native cleanup contract is not relaxed to accommodate the new Error case.

## Remaining gates and work boundaries

**C2 source correction is accepted, not runtime-qualified.** Compilation, reflection, actual
sample/restoration/adapter-failure cuts, timing, all old assertions and strict cleanup still need
explicit authorization and evidence. The two permanent-PENDING process probes retain their
separate source-only disposition; exit23 remains PROCESS_ONLY/product_end=false and is rejected
by the ordinary positive oracle. No47-test or all348 aggregate pass is claimed.

The existing native JAR `f1a6dad0aa9ee3288c1a57cb230336fab96ca183b648976d68012caf9413395c`
cannot implement method23. Exact native successor artifact/provenance remains required; no
replacement/relabel/skip/stock fallback is authorized. Native actual-finalizer interior,
pin/compaction release, successful wire cancellation, broader reset/native/ending failure matrix,
shipping destructive-cut/exception-table/initialization, immutable launch, all348 preservation,
P3/W03 and downstream co-gates remain. W06 excluded; NEW-data/installation recovery preserved;
no Firebase retirement, tracker closure, public push or aggregate acceptance.

Reviewer activity was read-only source/docs/Git/hash/diff inspection and this new report.
**Zero product/test/native edits, builds, tests, static checkers, formatters, JVMs, services,
downloads, CI, artifact replacements, tracker edits, commits, pushes or spawned workers.**
