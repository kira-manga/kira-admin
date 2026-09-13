# CoreC2 Linux01 — existing-v3 recipe only

2026-09-12 UTC. **PREPARED, NOT ADMITTED/FROZEN/EXECUTED.** No source or tooling edits.

Authority: primary validation selection
`review/remediation/app-29-core-c2-product-lifecycle-validation-selection.md`, SHA
`0582e4ac646996f9595e9d2d062a9a07f3a1c216aad83b1ffaa822a8a29c6372`;
independent bounded source approval `79842f030ba4b70991e805fe969c1d0d1c250e2720f69bc91725c0d2d8b5ed7e`.
Primary alone freezes, admits and launches. Admin01 owns separate private PG10 preparation.

## Minimal batch and exact declarations

`recipe.json` contains literal existing-tool freeze/validate/run argv, no new script.
The one Gradle batch is:

```text
testClasses test
  --tests me.manga.kira.backend.common.infrastructure.persistence.PoolLifecycleTest
  --tests me.manga.kira.backend.common.infrastructure.persistence.PoolActorCustodyTest
  ktlintCheck detekt --continue
```

`testClasses` preserves normal main/all-test compilation; no source filtering,
alternate compiler, import probe or compile exclusion. Only the two entire classes
execute. Ktlint/Detekt are the normal owning project tasks with existing rules; no
file-only bypass or new baseline. The normal JaCoCo report finalizer is unchanged;
`check` and its broader coverage/suite gates are not requested.

| Class | Test methods | Declared cases |
|---|---:|---:|
| PoolLifecycleTest | 10 ordinary + 4 parameterized | 10 + 2 + 2 + 3 + 2 = **19** |
| PoolActorCustodyTest | 10 ordinary + 3 parameterized | 10 + 4 + 3 + 2 = **19** |
| Total | **27** | **38** |

`declared-cases.json` lists every exact method and each ValueSource value. All34
old declared cases remain, plus the four new MODEL cases. These are manual source
declarations, **not** discovery or execution. A later result needs both exact XML
classes,19 each,38 total, no failure/error/skip, no extra class, and matched protected
method/parameter identities. The unchanged runner's aggregate discovery check alone
does not prove that comparison. PG10 is not executed by this local selection.

## Protected bytes and historical continuity

`protected-source-pins.json` defines the exact prospective source map: the frozen
diagnostics01 manifest `2e6ba4a28bdc628d42937c3ed0f7f435c835b61d4e6f73702b50e6a2edd85511`
with **only** the accepted product5/test3 replacements. Same466 paths, other458
hashes unchanged, all348 development07 seed paths retained, same199 snapshot subjects,
same inherited removal and no new removal. This is a derived expectation, not an
executed full-inventory check or a source freeze. It also records unchanged fixture
and normal build/config/wrapper pins for primary readback.

The fixed freezer remains `e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`;
the Linux v3 runner remains `bec0d6b5ebf63a68fc9d93aab0dca9dff828c9136baeda7066dd02af85e372cf`.
All five required tools and the existing three Linux ownership/helper-control files
are pinned. Old hosted carrier tools are retained as approved provenance, **not**
executed locally. The prospective freeze carries all63 prior approved inputs plus
new authority/bindings (**87 total**), unchanged102 historical hashes, and8 active
tool pins. The actual freezer must prove those counts **and exact memberships/bytes**;
counts are not substitutes. Timer-A02 and development07 remain immutable anchors.

No fixed inventory implementation is changed or replaced. No prior freeze, snapshot,
bundle, request, ref, result or Ktlint preparation is changed. Current private root
was read at `eb8fed8b6b620a0c7448c223bf49c1683f8eaadc` with exactly eight unstaged source
changes. Local execution need not create a checkpoint. A primary-authorized checkpoint
or any source/ref/status change requires a new matching identity before freeze, not
rewriting old history or relabeling the old diagnostics manifest.

## Later primary execution and cleanup

Use fresh named directories from the recipe; do not precreate the freezer's candidate
directory as a log destination. Replace the fresh-manifest SHA placeholder only in
the invoked argv (or a separate command receipt), using the actually generated hash;
never modify this approved recipe after freeze. Retain genuine v3 preflight output.
There is no executable tool in this packet, and preparation is not admission.

The existing runner is selected **offline**, with its fixed18 local dependency
inputs and unchanged init script. No Java/cache/disk/build availability was probed
here. Primary must satisfy Java21,8GiB free, private-home owner/lock, no prior outputs
or private daemon, and the original dependency checks. Missing prerequisites are a
real setup failure, not authority for acquisition, online fallback or unchanged retry.

Serialize the batch. Preserve raw commands, compile/static/test results and required
bytecode before only owned output cleanup. Keep the unchanged immediate stop,
anchored quietness/capture/scoped-clean/final-stop, all five quiet descendant barriers,
unforced disposal, restored child scope, source/dependency postflight and output-absence
requirements. Never kill by guessed PID, delete unrelated outputs, or clean before
capture/quietness. A failure stays a failure and retains recoverable evidence.

This author only read source/evidence, hashed bytes and serialized prospective JSON
and this report. **No candidate/helper import, freezer/dry-run/preflight, compiler,
checker, build/test, service, network, CI, checkpoint or Git mutation occurred.**
No owned process remains. Historical exact-two0/2+cleanup FAIL, full47=45/47, W03
incomplete and App29=2/9 are unchanged. Local38 success would still not prove real
opaque-eviction/queue liveness or substitute for the separately prepared PG10.
