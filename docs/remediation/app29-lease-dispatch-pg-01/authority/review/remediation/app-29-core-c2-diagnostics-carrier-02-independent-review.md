# Core C2 exact-two diagnostic carrier — independent actual-delta review

Backend05 (`/root/backend_05_history_hosted_review`), NONAUTHOR, 2026-09-12 UTC.

**ACCEPT SOURCE-ONLY: final controller3922 with limited bundle02. No remaining material delta blocker. Not adopted/executed/qualified by this review; primary binding and authorization remain required.**

`P1` = `review/working/app-29-core-c2-diagnostics-preparation-01/`; `P2` = corresponding `…preparation-02/`.

## Exact pins

| Reviewed input/result | SHA-256 |
|---|---|
| `P1/carrier.patch` | `650aaa0a38029d141d2f27eaa097d726ba19d74c639be76de6a8de9a8a98858b` |
| `P2/pin-successor.patch` | `9611b1cb2663d9c81adb460a13a94a929f83e9ea88add37fe4925d561816fb0c` |
| Reconstructed final `ci/app29-gate-b.py` | `39224054c4bd61bbf665568c982302c12f84fa5df3e293c568f338a9cbeae9ca` |
| Reconstructed `.github/workflows/app29-gate-b.yml` | `da12c5352baf0b3dcc1127d4e2042b9ea95159086ee72d34133f1962e6b717dd` |
| `P1/profile/profile.json` | `a5e6cf435dd0457cfd24f8cefa2cbe4fa90445bf884d028fe67bca07ec6664b7` |
| `P1/profile/profile.init.gradle` | `8e7bd86077e4a3a9b817ef6014514598264f4bcc3d416e9543d93c11b7615b8a` |
| **Final request:** `P2/ci/app29-gate-b.request.json` | `e78edee842301e109725c1b0b6bb7d7d7fb55ba78f5a32c8b63922725c7dc6ba` |
| `review/working/app-29-core-c2-diagnostics-private-checkpoint-02/backend.bundle` (200,148 bytes) | `36e84a965720f325ac0b91b3807f9dcc95793268a4e7a2f6a802a5b333f25e41` |
| Same checkpoint02 directory, `checkpoint.json` | `73227afa3d4daf625ad7131ed78bffc04ab7d39d4b4904e4cc5e1f47b14cbaf1` |
| `P2/README.md` | `b1013a76b0efa092bad7540219b4b91e67b48c16d675858d67b0a424107744b9` |

Both patches were reconstructed and hashed **in memory**, not applied to live files. P1 matches the existing controller base `d6d35bdfdf7c3c5914281992c68b14562dbdc5eb5f7b72724cdb2da8244209a4` and workflow base `850ee781bb7ad3dfdd8532a294bc08b3840c2fa2b4fe4b0d842058aaa8a71e2c`. Its controller result is `fd76b88c78f47c6b72a557e02fc13e4f8a528e66a19e061619e6c95faead2ba7`; P2 changes exactly two data lines to produce final3922: bundle source path01→02 and controller/workflow freezer-snapshot prefix P1→P2. All reviewed semantic blocks, profile/init and resulting workflow stay unchanged.

## Material finding — resolved without relaxing the gate

The originally supplied full bundle01 (`fe24a5aa…`, 2,223,216 bytes) has only a v2 marker and tip/ref header. The retained controller requires **three** lines, including the exact singleton public prerequisite; it would reject that original binding before bundle verification/import and tests. I reported this blocker; the primary chose a new prerequisite-limited bundle, not a permissive header change.

Independent byte inspection now confirms bundle02's exact v2 marker, single `-3d839130c807f6a0a9b1c896c1c6cca4b41c4538` prerequisite, single `eb8fed8b6b620a0c7448c223bf49c1683f8eaadc refs/heads/remediation/app-29-backend-complaints`, bounded size, PACK prefix and pinned digest. These agree with the new request/receipt. **Full bundle01 and all P1 files remain unchanged; P1's old request is not the final request.** No Git verification/import was rerun by this reviewer.

## Remaining actual-delta checks

- **Exact two only:** controller argv, profile and Gradle include filters select the two fully qualified failed method names, with literal spaces and no backticks, parentheses or wildcards. One Test task/worker and fail-on-no-match remain. Compilation is not claimed to be narrowed. Source09ff's accepted two-case-only diagnostic change was not reopened.
- **Honest result recording:** the reader requires one expected XML suite and exactly the two identities; it records actual PASS/FAIL/ERROR/SKIP with matching suite counts. `RECORDED` is distinct from `test_status`. Required BEFORE/AFTER captures must each occur exactly once per fixed case, with no UNAVAILABLE record, to obtain `fixed_scalar_capture=CAPTURED`. Optional failed-observation records are preserved, not invented. Fixed-field/scalar syntax and raw records are retained; semantic meaning remains manual diagnosis, not causality/completion proof. Raw XML/capture hashes survive independently of reader acceptance.
- **Failure/ownership preserved:** `attempt`, command ownership, sticky nonzero drains, container handling, output cleanup, dependency extraction and source materialization implementations are byte-identical to the reviewed base. The validation command is identical apart from the fixed TASKS values. Cleanup/postflight/retained-inventory sequencing is identical except the diagnostic-reader assignment. Overall PASS still requires both actual tests passing, required scalar captures, no sticky failures, input preservation and successful outer cleanup. No nonzero-exit, timeout or cleanup waiver was added.
- **Bindings retained:** before/after source checks enforce `eb8fed8… → 989a8c07… → 926927ab… → 49da0919… → public3d839130…`, with sole parents. Fresh-v3 checks require all466 source paths (only the accepted test hash09ff substituted), all348 seed paths, all199 snapshot subjects, unchanged removals/historical pins and preservation of prior approved inputs. The seven diagnostic-authority and ten Native05-authority file hashes match locally. Native05/Checker/stock-removal inputs, JDK constraints, helper SHA `56b66cfe…`, budgets and one-attempt restriction remain unchanged.
- **No qualification widening:** expected positive witnesses are empty; `consumer` stays `NOT_EVALUATED / OUTSIDE_TWO_CASE_DIAGNOSTICS`. Classpath/class-load material is context, not positive consumer-loader proof. The workflow remains private-Admin-only, read-only permissions, exact-carrier/public-prerequisite checkout and private evidence upload. Run/artifact paths agree with the new diagnostic identity.

## Primary-only prerequisites / limits

The reviewed final request is still **authorized=false**, with the deployed acceptance-checkpoint SHA placeholder. Before any separately authorized attempt, the primary must materialize exact controller3922/workflowda12 snapshots under **P2**, keep profile/init and accepted proposal bindings under **P1**, add bundle02/**checkpoint02 receipt** to fresh approved inputs, complete the genuine 466/348/199 v3 freeze/local preflight, and bind the resulting deployed acceptance checkpoint. The private checkpoint02 receipt is **not** that acceptance checkpoint; old checkpoint01 remains historical source authority only.

Review performed local read/hash/text/JSON analysis only, plus this separate report: no live/history edits, Git, candidate imports/compilation, test/controller/checker/runner execution, CI/network/service operations or freezer/adoption. Actual compile/run/capture/cleanup remain unverified. No full47 run is authorized. Historical20/27 and hosted02 **45 PASS / 2 FAIL** remain separate; Native05 **UNQUALIFIED**, D05 **PARTIAL**, D06 **unreviewed**, W03/full/native qualification unchanged.
