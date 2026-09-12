# App29 permanent-PENDING probes01 — independent source-only review

2026-09-11 UTC · `/root/backend_04_independent_review` · **NONAUTHOR / REPORT ONLY**.

**Disposition: no new source-level blocker found in the four-test-file negative-probe delta.**
This is narrow source acceptance of the proposed discriminators, not evidence that either test
compiles, reaches its cut, passes, or disposes product resources. **Both runtime proofs remain
unproved.** The unchanged resume02 production C2 blocker remains open in this packet; its separately
sealed successor is not reviewed by this report. No aggregate connected-core/actor/native approval.

## Exact reviewed bytes and independent integrity

Packet: `review/working/app-29-real-pool-pending-probes-01/`, not the moving checkout.
Backend baseline `49da0919d9ec3091cb7bb041009dc9bd5f3e090f` is **PRIVATE / NEVER PUBLICLY PUSH**.

| Packet output | Bytes | SHA-256 |
|---|---:|---|
| `SOURCE-ONLY-HANDOFF.md` | 12174 | `bc8d6c8ac79cc0fac846367d13a256372999110f9e5eabca8f3ec8ae30d9ef6e` |
| `source-manifest.json` | 24946 | `46edb1d622b7a532ebb1511bb765d50184a8d0d2e844c30479f4134234972d9a` |
| `before-manifest.json` | 10939 | `5acaefa001593ae293dd19bab657f4df6e6ac9fe1897450dae9693bb4953174d` |
| `owned-core-and-probes.patch` | 194301 | `06c83638ef7629f6957ec23eb304474f8b53693763c40dc1bf8b56d47739f796` |
| `pending-probes-delta.patch` | 31794 | `a74752a3610d914c4782959d4d1343d68901939c377860f88042814c3179004f` |
| `test-source-inventory.json` | 13185 | `d802ee28b4efa2a23d0b0fc628dc0cd74464c83f3b98762900ba0c4ffad455f8` |
| `SHA256SUMS` | 7821 | `e2dbf96a404cf998afcc43b3df0f166efc1d0a496118afae7e101473a778f033` |

The handoff's actual pin contains `...f9e5eab...`; a transcription omitting that second `e` is not
the reviewed hash. All four changed paths are backend persistence tests/test support:

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `PersistencePgOwnedCutIntegrationTest.kt` | `e457920fdce6f774bc25f933c05aa2b45704dfcf4e36133b2cd5c05381d427a9` | `d2deb0973b6bcf98e62e19c244bdd69b0f0d756cf43ac952855e0aaf50aae9e6` |
| `PgLifecycleDatabaseRecipe.kt` | `71f29a6cc5d2b79ce304cf67b767676cfd7caca5cc191d9f2a3233c0449c7c0f` | `59c151faec761164dae849abc8b408fd6dd956ca43a368bcbfadfc8d07ce734f` |
| `PgLifecycleDatabaseProbe.kt` | `1fa4607c24104344eb6af548250a2a9030328368f0f272505f50d92fc0a632cc` | `b7d0df49b6d27c7d2f21ca801ba80b419dcf9a46277705cd4c609bd66a10a424` |
| `PgLifecycleDatabaseProbeProcess.kt` | `3c88f52aa69d943679956fa86eda2fa05ba0ed874053a6dc7960c9daf3972618` | `b115bbde5d83873d0dfa63a88571a2da601a0dbaf91c4db9c7cac1c73b09cf3a` |

Read-only byte/Git inspection independently established:

- All21 before/after lengths and hashes match both manifests. The18 original before-images match
  frozen resume02; the three added support before-images match private49da. All16 production
  after-images and `PhysicalJdbcDescendantsTest.kt` remain unchanged from resume02.
- Full patch reconstruction: **15 tracked private49da images +6 absent/new images,63 hunks**,
  including every full-index Git blob identity. Incremental reconstruction: **four paths,12
  hunks**, yielding the exact after-images. All per-path full/incremental hashes agree.
- All48 `SHA256SUMS` entries agree and cover every other packet file; all four packet-output
  records and seven read-only reference records agree.
- The six control pins (Handshake, ControlsTest, DatabaseLifecycleTest, Cases, Scenario,
  TestScope) match private49da and the unchanged worktree bytes. These are source pins, not
  executed control results.
- Existing Hikari6.3.3 input:171931 bytes, SHA-256
  `709f378c05756280939ce50fc1b1f1a53bb8e1899dc1b249f21f12703640b48b`; archive manifest bytes agree.
  The archive was read only, not loaded, replaced, downloaded or qualified.
- Independent textual test inventory: private49da20 → resume0243 → candidate45, comprising
  Descendants16 and Integration29. Both added names match the inventory; no prior name is lost.
  This is **not discovery, an all348 audit, or45 passing tests**.

## Genuine retained cuts, not healed fixture models

Line references below use the frozen after-images. Actor dependency reads use accepted storage
after-image `2cbd7a055d12000953c37301a7d08839df739d391b4fafa453e8acb62944963e` and resumed
`PoolLifecycle.kt` `def7c6ef36145b6d1dcf71342a5e6c1956f6f40055464e231e946eff05ade9f2`.

**Acquisition end:** Integration940–951/1063–1123 intercept the ordinary Storage instance's
`current`, select the exact real borrower Thread and ACQUISITION frame, and throw the exact
sentinel only after observing ENDING and genuine consented/ended checkout. Actor `endFrame`
claims ENDING before TL restore; a failed restore cannot call `finishRestoredFrame` or drop the
count. `GuardedDataSource`70–92 withholds the facade and executes genuine delivery-failure
retirement/sealing, unused-entitlement revocation and handoff without retrying that end.

Integration996–1019 requires the authentic terminated borrower, unended frame/completion,
same lease/handle/original caller, retired/sealed epoch, REVOKED/unprepared right, no RETURN,
same checkout budget, acquisition1/future0/operations0 and BOOKKEEPING_FAILED. Real `closePool`
must refuse INITIALIZATION_PENDING, leave `firstClose` unclaimed and expose a PENDING receipt.
Restoring the intercepted field does not clear the caller's original TL value or edit a count.
Possible independent native retirement is explicitly not acquisition/pool completion.

**Final RETURN core count:** Integration954–976/1126–1191 captures the actual lower
clearWarnings Invocation before it disappears, then fails the real context TL removal after
the driver slot clears and the saved invocation's ended bit is true. `GuardCall.finish` executes
native disarm/actualEnd/reconciliation before `finishProducer`; its TL failure precedes
`token.finish` and retains bookkeeping failure/unresolved custody. No frame, producer or native
ended bit is written by the probe. The fixed sentinel and retained-state checks discriminate
the intended cut rather than accepting any SQLException alone.

Integration1032–1059 rechecks the exact call/caller/token, null outcome, sealed/poisoned active
foreground, unresolved custody and retained Entry. The separate real RETURN Operation actually
ends with its single right CONSUMED and transfer unconsented; a duplicate facade close neither
reprepares nor repairs it. Actual Hikari shutdown must return; actual terminal abort must have
returned/thrown, while producerDrain remains false, final physical close NOT_INVOKED and terminal
body unended/PENDING. The private49da terminal loop waits on producers after abort; caller death
or a completed outer pool close does not supply that missing core receipt.

This is **after native actualEnd**, not a native-finalizer-interior, pin-release or compaction proof.
Both fault wrappers restore only their intercepted instance field and record the unhealed caller
TL before the genuine caller terminates. No manual finish/ENDING retry, artificial receipt,
raw close, counter edit or success-only scope cleanup appears in the child path.

## Process-only oracle and preserved positive controls

- Recipe45–74 closes the additions to DEFAULT/queryTimeout0/ORDINARY/one attempt and marks them
  non-success. Historical recipe/lane/timeout grids, ESTABLISHMENT set and explicit negative
  EnumSource identities remain. Inspected baseline enum consumers do not indiscriminately add
  the new modes to the historical grids.
- Integration876–937 warms the real private pool, runs/joins the exact borrower, checks the live
  retained state, emits/flushes its exact nonce/case witness, publishes RETAINED, awaits EXIT,
  then **rechecks the same state**. It does not use `OwnedCutPool.close`/`PgLifecycleTestScope.close`.
- Probe28/47–59 dispatches only these cases before the old routes. Failed verification emits the
  bounded diagnostic and failure marker/exit1. Only successful negative verification after EXIT
  emits `PG_POOL_PENDING_EXIT_REQUESTED ... cleanup=PROCESS_ONLY product_end=false` and exits23.
- ProbeProcess79–129 requires a live child/healthy bounded capture and a complete exact retained
  line before EXIT acknowledgement. The unchanged handshake verifies exact nonce, case, phase,
  ordinal, bounded file bytes and single use. The final oracle requires actual exit23, complete
  EOF/terminated reader, final newline and the exact ordered witness pair. Wrong/duplicate/unknown
  pending markers and known normal-success/failure markers cannot qualify. Missing witness,
  timeout, premature death, another exit or incomplete capture fails closed.
- `awaitVerified`62–76, `close`141–191 and the output reader237–298 are byte-unchanged routines.
  Integration803–809 deliberately submits exit23 to that positive oracle and requires its
  original nonzero-exit rejection, then independently checks actual unforced process/stream/
  reader cleanup. Forced emergency cleanup still throws; it is never a negative-cut success.
- Only the two new modes add the exact-name/bounded-size/hash-checked Hikari location to the
  existing closed child classpath. No whole test runtime/JUnit/fallback is added. Invoked child
  checks and reflection helpers are source-level JUnit-free; runtime linking remains unproved.
  A nonlocal fixture host is refused rather than guessed or silently routed elsewhere.

**Negative discriminator satisfaction and process cleanup are distinct prospective results.**
Neither exit23 nor OS cleanup means product_end=true, native drain, actor end, S+F+T or successful
owned lifecycle disposal. The parent database owner's unchanged teardown must also succeed.

## Open gates / boundaries

Resume02 C2 is unchanged: original InterruptedException adaptation can call overriding interrupt
again after RETURN end. Report
`app-29-real-pool-connected-core-resume-02-independent-review.md`, SHA-256
`705cb53e8369d20abadeb826cbff1b40ae83fb4bac7eebc9df01c8c84e47c320`, still applies to these product bytes.

Both new real fault cuts, reflection on the selected Java21 runtime, child linking/timing,
negative/positive oracle controls, EOF/unforced cleanup and owner teardown still require explicitly
authorized qualification. The retained old native JAR
`f1a6dad0aa9ee3288c1a57cb230336fab96ca183b648976d68012caf9413395c` cannot implement method23;
no relabelling, replacement, skip or fallback is authorized by this review. Exact successor native
artifact/provenance, native-finalizer interior, successful wire cancellation, broader reset/native
matrix, shipping destructive-cut/exception-table/initialization, immutable launch, all348
preservation and P3/W03 co-gates remain. W06 excluded; NEW-data/installation recovery preserved;
no Firebase retirement or downstream acceptance.

Reviewer work: read-only source/docs/Git/hash/diff/archive inspection and this new report only.
**Zero builds, tests, static checkers, formatters, JVMs, services, downloads, CI, artifact
replacements, product/test/native edits, tracker edits, commits or pushes.**
