# App29 PG03 failed-run cleanup seam — independent actual-diff review 01

2026-09-13 UTC. NONAUTHOR: `w03_static_nonauthor_review`.
**SOURCE-ONLY APPROVE within the finite failed-run cleanup scope.** No blocking
source defect found in the actual delta. This is not measured cleanup proof,
PG03 admission/deployment, test PASS or ownership/product qualification.

## Exact input binding

Packet: `review/working/app-29-lease-dispatch-pg03-failure-cleanup-preparation-01/`.
Independently rehashed every packet file and checked the SHA256SUMS/SEAL chain;
all six files are0600 and packet directories0700.

| Packet input | SHA-256 |
|---|---|
| `baseline/ci/app29-gate-b.py` | `406febde3a67c108e987657489c6b429c3e735286aff8563a3a172dd6faf422d` |
| `ci/app29-gate-b.py` | `30b9ab8a43b6b9277ac401569ddfa62ef44282929d6bb21badbf2f7abe5c1024` |
| `tooling-delta.patch` | `9ebad75c13bc20a58e6e9c766624a011a48f47645f479f320aa0aa6bfd15b664` |
| `AUTHOR.md` | `f8084c0f87e5fc31b0d19a996c6ee2882f00826a5c730f24a276245447225bc6` |
| `SHA256SUMS` | `d461f39fea52dccf6d54948adee8184cc594654e1d055e28fe15601fb7be6450` |
| `SEAL.sha256` | `0bf924108a31e228f448d7fb4b962a96d67e4f4ba8057401030004dfa2e2d1cf` |

Baseline bytes independently match `ci/app29-gate-b.py` at the actual carrier
`b6e2a2cf7c35eca56a2478a6a1973dc8b6c94428`, tree
`f178ef61f2539745cf178989ac4f4aff0298da30`, blob
`ff5667fb60c6f01ee1fdb93f8b452a70d1b24d5d`.
Reconstructing the complete baseline/candidate unified diff reproduces the packet
patch byte-for-byte. Reversing only the reviewed import/guard/result fields,
container branch/flag, capture split/integration and added PASS flags reproduces
the entire baseline file. There is no unrelated source delta hidden outside them.

## Findings on the changed decisions

### Known-empty absence is separated from mandatory topology

Candidate988-1021 retains the clean dedicated-daemon/run prerequisite, normal
census loop and bounded event command before considering the new branch. Empty
`created` alone is insufficient: the entire raw journal, destroyed set and current
census must also be empty. An ignored-action event, orphan destroy, remaining ID,
malformed input or failed Docker command cannot use this branch as custody proof.
The branch records sticky `container-required-topology` / `CONTAINER_REQUIRED_TOPOLOGY`,
writes the empty observation and requires a fresh successful empty after-cleanup
census before returning absence/NORMAL_ABSENT. It performs no image inspection or
container removal. `container_topology_complete` remains false, so absence can
permit disposal without ever satisfying a successful PG-run topology.

The nonempty path is byte-identical except its new true topology flag after all
existing PG/Ryuk counts, labels, session and image-identity checks. Unknown or
partial nonempty custody is not relaxed. Existing known-ID-only removal,
forced-cleanup sticky failure, destroy-event and final-absence checks remain.
Final unknown/nonempty census still resets containers UNKNOWN and blocks home
cleanup; the preexisting ordering of earlier output deletion versus final census
is unchanged, not newly qualified by this review.

### Faithful available capture is separated from required-success inventory

Candidate1055-1104 keeps exactly the two original build-report roots and existing
`.xml/.txt/.json/.log` scope. Only FileNotFoundError from the initial root lstat
marks that root ABSENT; it does not prevent visiting the other root. Other root
errors propagate. A present root must be a directory and receives CAPTURED only
after its walk and in-scope copies complete. Enumerated entries use direct lstat,
reject links/non-regular/non-directory types, and do not reinterpret subsequent
entry disappearance as benign root absence. The existing walk error callback,
64-MiB per-file digest limit, recorded size and source/destination/source hash
agreement are retained. Partial copies or raised stat/walk/copy/hash errors do
not return capture success.

The new required-inventory function first requires both roots CAPTURED, then runs
the **byte-identical old required XML/effective-classpath/class-load-log check**.
It runs only after available capture succeeds; diagnostics runs only after that
required check succeeds. Thus a missing required root/XML is a sticky success-
evidence failure, never a fabricated testcase or passing diagnostic. Available
capture may correctly succeed despite that failure, allowing existing owned-path
disposal once all absence/drain gates also succeed.

This is the owner's approved narrow evidence scope: HTML/CSS/JS, compiled classes,
caches and report binaries are not newly required captures. CAPTURED means the
walk and allowed evidence copies completed, not that every file format was saved.
The preexisting per-file bound and drained-owned-tree/path assumptions are not a
new aggregate I/O bound or hostile-concurrent-filesystem proof.

### Capture errors still block deletion; every prior PASS prerequisite remains

The exact file/home cleanup expressions, deletion paths, final census and drains
are byte-identical. `capture_complete=false` after any raised capture error still
prevents all backend/private output and home deletion, preserving partial copied
evidence. An expected missing *success* inventory is intentionally distinct from
an inability to read/copy available evidence. No missing-topology or required-
inventory failure is removed from the sticky failure list.

Independent byte comparisons also confirm:
- `fail`, `attempt`, cleanup/output-absence, drain and command methods unchanged.
- Full diagnostics function unchanged, including exact test identities/counts,
  outcomes and classpath/source/JDK context requirements.
- Removing only the three new capture/required-capture/topology conjuncts makes
  the candidate PASS expression byte-identical to the old expression. Every
  previous failure/cancellation/time/output/input/inventory/diagnostic/container/
  command/final-census prerequisite remains present. The added flags are positive
  extra requirements, not substitutes for old requirements.
- No owner helper, budget, target, test filter, source binding, workflow, init,
  request, dependency, process or container-control program is changed here.

## Smallest meaningful synthetic coverage recommendation

No new test source is included in this packet; the author's case table is reasoning,
not execution. The existing draft05/draft06
`tests/test_failed_capture_cleanup.py` files are byte-identical (SHA-256
`0437ff7cf1327b890509b7934d76b7b3e05e532cfd1f70624020c5355de41689`).
Their four old cases cover failed XML retention, copy drift and failure-text
sanitization, but load old capture/consumer logic. In particular, their missing-
required-file case expects capture failure and retained outputs, which is the
behavior deliberately being split here. They do not cover this candidate's empty
Docker branch, root states, required-capture flag or added PASS requirements.

Recommend only these finite seam controls, in separately reviewed/admitted test
source; reuse the existing synthetic-temp-tree/copy-drift approach rather than
create a new ownership qualification program:

1. **Known-empty compile-failure route:** fake bound empty normal/raw/after/final
   observations, both roots positively absent and synthetic drains successful.
   Assert no image/rm call, topology false, required capture false, available
   capture true, both sticky missing-success failures retained, exact owned-path
   cleanup permitted and overall FAIL. Preserve an existing nonzero-child failure.
2. **Capture split:** missing first root plus present second-root allowed evidence
   must copy/hash those bytes, record ABSENT/CAPTURED, skip diagnostics and remain
   FAIL despite disposal eligibility. Also cover present roots with one required
   item missing; available capture must not be confused with required success.
3. **Negative boundaries:** a small parameter table for initial-root PermissionError,
   enumerated-entry FileNotFoundError, walk/copy/hash failure (reuse copy-drift),
   empty-created but nonempty raw event/current census, and failed/nonempty fresh
   after-census. Capture errors must hold all file/home deletions; custody errors
   must grant neither container removal nor file cleanup. Do not stub these errors
   into successful absence or silently reclassify them as missing roots.
4. **One positive control / PASS guard:** complete expected available+required
   evidence and the unchanged valid nonempty topology path can reach all three
   true flags; independently false new flags must prevent synthetic PASS even if
   other fields are preset successful. This is predicate/branch testing only,
   not evidence of a real PG fixture or process/container absence.

No full historical test replay, PID acquisition/kill exercise, real Docker/JVM
execution or broader ownership acceptance is recommended for this finite seam.
These tests have not been authored or run by this reviewer.

## Limits and handoff

Only passive source/Git/hash/stat/text reads, byte/diff comparisons and this new
private0600 report were used. No target/helper import or execution, syntax/AST/
static checker, test/CI, dependency/network acquisition, resource control,
source/tooling/Admin edit, commit or deployment occurred.

The packet retains old PG02 constants/pins and is not a newly bound PG03 carrier.
Primary's later `f2e58eac` source checkpoint is neither validated nor public by
virtue of this review. Historical PG02 remains FAIL with its original263-byte
compiler-error and retained-cleanup receipts unchanged. Native05 UNQUALIFIED and
all external/product limits remain. Primary owns any synthetic-test admission,
new binding and actual run; source-only approval is not a retry authorization.
