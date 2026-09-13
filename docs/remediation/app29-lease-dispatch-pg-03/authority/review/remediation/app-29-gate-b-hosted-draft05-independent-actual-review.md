# App29 draft05 — independent actual capture/cleanup correction review

2026-09-11 UTC · `/root/backend_04_independent_review` · NONAUTHOR.

**CONCUR — bounded SOURCE/TOOLING correction; no material finding.** This accepts only
these sealed source/test definitions against immutable draft04 and the retained first-run
failure. **Four tests remain UNEXECUTED.** Not an installable carrier, isolated-test
admission, hosted retry, corrected-driver/profile binding or runtime/Core/native acceptance.

Authority: `review/remediation/app-29-core-c2-failed-run-cleanup-primary-agreement.md`,
SHA256 `fd4b245bfb243b2a7154a28ebea9a4628942d998412c7640ff29755370bb15da`.

## Exact packet and preservation

Prefix: `review/working/app-29-gate-b-hosted-draft-05/`.
Closed14 regular files, mode0600: all13 ledger members plus the ledger independently match.

| Member | Bytes | SHA256 |
|---|---:|---|
| `SHA256SUMS` | 1218 | `6d2c599e8331850b702011d931e1c22287b955710ff56f9ea54b6b25853fd7bc` |
| `before/ci/app29-gate-b.py` | 46021 | `8bf1d55fb2ccc40a891443ae65ac281db39d4e3711fdbe75abc0ff57cfddf6a1` |
| `ci/app29-gate-b.py` | 51087 | `72fc936f5ec19c3d7256f049a3fb8647cc806c9cc0d4150787388e2386e84eaa` |
| `tests/test_failed_capture_cleanup.py` | 8969 | `0437ff7cf1327b890509b7934d76b7b3e05e532cfd1f70624020c5355de41689` |
| `review/draft04-to-draft05-source.patch` | 22387 | `2d0c0816ccb48bffe907f53540a168bcb5431cf07d084d80903189e67ff39523` |
| `AUTHOR_REPORT.md` | 9810 | `82639ef5ecaaf21e54462c11c0c30f742d63e1779efcffa4cb5aa8782decc2b7` |
| `README.md` | 5886 | `77688fd829f96dd0a8c314b4f9470f66aa816f807e88e565a6ebab082c786743` |
| `review/reference-inputs.json` | 8014 | `6d18e2905bfcb2b5b544f5e3d56aae360ab33b7d052801d58ce5cfac4a28b528` |
| `review/source-inspection.json` | 11518 | `b96d7913758f8390344c8e5943e20651a672bdd3d65439869db8dbe9acefd24b` |
| `.github/workflows/app29-gate-b.yml` | 2467 | `e41222344cf34a0964874f9199096f208106072761a3d092aefc3e94bf1af9f0` |
| `ci/app29-gate-b.request.json` | 1497 | `ecc638e744dd3687fd247117210e3714852a9633744b59974e65ccd5997c404c` |
| `review/checkpoint.template.json` | 1168 | `d28d55d78a8c510c98ca4d0b0e7d03c462bfbe129f826a55d40371a8cfb10bc2` |
| `reference/profile03.json` | 23734 | `ae027fc473d0c8c55665e23585b6508d59c0d803a8c76a66b694425fbc602b5b` |
| `reference/profile03.init.gradle` | 11186 | `2237206f53344001fa1697a02ce84f5a1b851f205d0029a22423d98acb49ee7b` |

Read the complete source/test delta and all152 test lines. Independently regenerated the
full-index/no-external-diff Git source/test patch: exact match after path-prefix normalization
only. Controller delta is **+107/−30**,667→744 lines. The before image matches both frozen
draft04 and deployed carrier6fc397a. All five context copies remain byte-identical to draft04.

All29 protected `inputs_before` records match author `protected_inputs_after` and live bytes,
including complete draft04 packet, original profile/init/helper, deployed tools/request,
authority, raw collection/result and six raw payloads. App/Backend/Admin HEAD/branch/status
also match those recorded snapshots; no whole-worktree content audit is implied. Heads:
App `a584efecb3dfb342d9a3b873bc09c132e8771cd3`, Backend
`926927ab805a2a3b78957862f3b744d0fe399ac5`, Admin
`6fc397a0569f73cc549dbc75be2ac18b31362a7b`, all on the recorded issue branch.
Owner WIP, packets, raw evidence and deployed carrier were not edited.

## Bounded findings

Line references below are to the proposed controller unless marked tests.

1. **Copy completeness no longer requires passing tests** (493–525,660–662).
   Capture remains confined to owned `w01/backend-build/{test-results,reports}` and retained
   run `reports`, with the same `.xml/.txt/.json/.log` filter and64MiB per-file bound. Safe
   roots, link refusal and explicit walk-error propagation precede completion. Each selected
   regular file records its length and source-before/source-after/destination hash equality;
   incomplete rows cannot open cleanup because capture must return literalTrue.

   Presence requires both named XML files, effective classpath, both fixed worker witnesses
   and at least one numeric-PID class-load file. Presence is not semantic provenance: extra/
   wrong inventory or malformed contents remain consumer failures. Missing required bytes,
   traversal/copy/hash/link errors retain `capture_complete=false`. HTML/binary exclusions
   are explicit; this is not a claim to capture every generated output format.

   After successful capture, consumer exceptions append failure and yield explicit consumer
   FAIL without resetting capture or clearing earlier validation/child failures. This is the
   intended failed-test cleanup transition, **not** an acceptance fallback. Absent capture
   leaves consumer `NOT_EVALUATED` and prevents output deletion.

2. **Acceptance and custody are unchanged** (528–603,346–490,653–693,721–728).
   Text-delimited comparison finds22 of25 preexisting declarations byte-identical. Only
   `Gate.__init__`, `Gate.fail` and `execute` change; added are `capture_reports`,
   `Gate.cleanup_outputs` and `Gate.output_absence`. Existing imports/globals precede the
   new literal map unchanged; no replacement controller/owner was introduced.

   Full consumer remains identical: exact47 passing unskipped identities, two CREATE_NEW
   witnesses, same actual PID/JDK/positive loader, original PgConnection association, one
   PID class-load log, pinned sole suppliers and stock removal. Positive `source: file:`
   remains distinct from cold defineClass negatives. TwoPG17.6 + oneRyuk0.12.0 custody,
   command/drain behavior, private source import/freeze and bundle checks are unchanged.
   No outer exit23 waiver; repeated historical nonzero-child failures remain sticky FAIL.

   Validation try/except, immediate stop/drain, postflight, final stop/census, retained
   inventory, complete PASS predicate and final publication tail independently compare
   byte-for-byte. The file predicate preserves its ordered short-circuit terms by factoring
   `before_file_cleanup`; home predicate and its preceding drain remain exact. Neither
   forced/unknown custody nor residual outputs can become overall PASS.

3. **All11 owned paths now have separate decision and absence receipts** (331–344,670–693).
   Deletion scope is unchanged: Backend `.gradle`, `.kotlin`, `build`, `buildSrc/build`, `out`;
   run `w01`, `project-cache`, `kotlin-cache`, `gradle`, `tmp`, `home`. Reports are not deleted.
   Every remover remains individually attempted through the existing error boundary and
   original custody predicates. Skipped paths record the first literal failed predicate;
   homes inherit an earlier file hold. These reasons are not an exhaustive later census.

   `cleanup_complete` means normal remover return, including already-absent input—not
   observed absence. Each path is subsequently checked independently via safe-path lookup;
   false/null is preserved and cannot be hidden by an earlier true. Only all11 true values
   yield `outputs_absent=true`. A safe-path failure appends failure rather than treating a
   symlink/error as absence. No unrelated recursive scan or new deletion target is added.

4. **Diagnostics remain bounded and non-disclosing** (53–81,313–322).
   All18 unchanged explicit consumer require messages map to fixed IDs in the27-entry
   literal table, alongside relevant capture/path/file guards. Only exact built-in ValueError
   with one exact string argument is looked up; only the mapped ID is retained. Consumer
   ET.ParseError gets literal `XML_PARSE`. Unknown exceptions keep existing stage/type only:
   no arbitrary message, argument, traceback or source payload is added or guessed.

5. **Four narrowly isolated tests are authored, not evidence of execution** (tests27–148).
   Static inspection confirms selection of eight data helpers, four Gate methods, six
   constants and the actual capture/file/home/PASS statements. Real Gate initialization,
   owner, command, source binding and main are excluded. All filesystem paths derive from
   a fresh temporary fixture; actual custody predicates are explicitly stubbed, not proved.

   - Tests116–134: retained synthetic failed XML admits cleanup, preserves the prior
     nonzero-child row and consumer `XML_SUITE_PASS` failure, verifies six retained copies
     and all11 absence receipts, and still requires final FAIL.
   - Tests136–139: a missing required witness holds cleanup and consumer evaluation.
   - Tests141–144: corrupt copied bytes hold cleanup with `CAPTURE_COPY_DRIFT`.
   - Tests146–148: arbitrary exception text is omitted from the receipt.

   Synthetic witness bytes intentionally prove capture presence only; no valid-provenance
   or successful47-case claim follows. The tests' proposed AST slicing/compile/exec has
   **not been performed by this reviewer**, nor have discovery or any test methods run.
   They do not establish real ownership, timing, filesystem-error coverage or hosted cleanup.

## Historical failure and remaining gates

Reuse the immutable draft04 actual review:
`review/remediation/app-29-gate-b-hosted-draft04-independent-actual-review.md`,
SHA256 `ba93c5f794cedcc41cd955ee99db7f4a80aff853497d9e76f7058fbe4f629624`.
My independent first-run raw investigation remains bounded by collection
`c612a34aa47387aa91a15140a6aea4005cb402ac5b62690c6d3e2e2efa6342ef` and result
`7d33b08f0e76f5258b3af28b795f22b236fc09d5226a2a8a21eb8c863d8c81c4` under
`review/working/app-29-core-c2-hosted-result-01/`.

Run34639408970 remains47 completed/27 failed, `capture_complete=false`,
`outputs_absent=false`; its normal child/container absence is a separate observation.
Both provenance witnesses and all six required raw payloads were retained. The old type-only
failure cannot conclusively identify its throwing frame; demonstrably failed XML does not
justify rewriting the historical receipt. Draft05 neither reruns nor retroactively repairs it.

**Deliberately non-installable binding is not a hidden acceptance.** Context request remains
`authorized:false`, attempts1, zero new tip/checkpoint/bundle hashes and bundle bytes0;
checkpoint remains `source_accepted:false`. Request still pins controller8bf1/draft04, and
`DEPLOYMENTS`47–48 still names draft04. This source-only review accepts that explicit limit,
not installation by flipping old authorization or mutating frozen04. Budgets remain25m/
1200s/120s/900s/180s, without new feasibility or launch approval.

Primary must separately admit any isolated tests, review their actual results, and accept
future corrected driver/source/profile/full-v3/bundle/controller/request/private-carrier
bindings before any fresh hosted attempt. Candidatea415 stays **UNQUALIFIED**; product
correction, exact47 success, output cleanup and Core/native/W03/full qualification remain
open. Private49da/926927 or successor source/vendor/JAR must never be publicly pushed.

**Reviewer actions:** read-only source/text/JSON/hash/Git-diff inspection and only this new
private mode0600 report. No AST/project parser, controller/helper/main/project import or
execution, test discovery/run, checkers/builds/JVM/Gradle/Docker, source checkout, dependency
operation, lock/admission, staging, commit/push, CI, retry or subdelegation. One initial
textual inventory overcounted nested `scan_error`; constraining the class region corrected
that metadata-only comparison (25→28 declarations), without evaluating candidate code.
