# App29 PG03 — failed-run cleanup preparation 01

2026-09-13 UTC · author `/root/w03_connected_ownership_review`.
**Private source-only preparation; not deployed, executed, qualified or authorized to run.**
The historical PG02 attempt remains FAIL with its original retained evidence unchanged.

## Authority and exact bytes

Read the independent failure report
`review/remediation/app-29-lease-dispatch-pg02-independent-failure-review-01.md`,
SHA-256 `0b70679ea085c844bdfaaf4be981fbccd6b52646fa5c80228e5ec86180f810e4`.
The baseline is the exact executed Admin `ci/app29-gate-b.py`, not the later live file:

- Carrier commit: `b6e2a2cf7c35eca56a2478a6a1973dc8b6c94428`.
- Carrier tree: `f178ef61f2539745cf178989ac4f4aff0298da30`.
- Git blob: `ff5667fb60c6f01ee1fdb93f8b452a70d1b24d5d`.
- Baseline extracted by read-only `git show`; its SHA matches the failure report.

Paths below are relative to this private preparation directory:

| File | Bytes | SHA-256 |
|---|---:|---|
| `baseline/ci/app29-gate-b.py` | 102819 | `406febde3a67c108e987657489c6b429c3e735286aff8563a3a172dd6faf422d` |
| `ci/app29-gate-b.py` | 104979 | `30b9ab8a43b6b9277ac401569ddfa62ef44282929d6bb21badbf2f7abe5c1024` |
| `tooling-delta.patch` | 8193 | `9ebad75c13bc20a58e6e9c766624a011a48f47645f479f320aa0aa6bfd15b664` |

`tooling-delta.patch` is the complete unified baseline-to-candidate diff, labelled
`a/ci/app29-gate-b.py` and `b/ci/app29-gate-b.py`; no other source file is changed.
`SHA256SUMS` also pins this author note; `SEAL.sha256` pins that checksum file.
Files are private0600, directories0700.

Primary approved the finite design before authoring, including the explicit scope
decision: preserve only the existing `.xml`/`.txt`/`.json`/`.log` evidence under the
same two build-report roots. Command logs already live in retained reports.
HTML/CSS/JS, report binaries, compiled classes and caches are not new evidence
requirements. This is not a replacement ownership/capture framework.

## Small correction, two independent responsibilities

### 1. Empty custody can prove absence without satisfying topology

The existing clean dedicated-daemon/run binding, worker drain, bounded normal
census and event collection run before the added branch. If `created` is empty,
the branch also requires the **entire raw journal**, destroyed set and remaining
census to be empty. Thus even an otherwise ignored event action cannot enter this
new empty case. Unknown IDs, orphan destroy records, partial topology, malformed
journals and failed Docker commands do not acquire a new disposal path.

The branch records the empty `owned-containers.json`, retains a sticky
`container-required-topology` failure with guard `CONTAINER_REQUIRED_TOPOLOGY`,
and requires the existing fresh `containers-after-cleanup` census to be empty.
Only then does it return absence and record `containers=NORMAL_ABSENT`. It neither
inspects nonexistent fixture images nor issues `docker rm`. The existing later
`containers-final` census and home-cleanup conditions remain unchanged; an unknown
or nonempty final census still prevents home cleanup and resets containers UNKNOWN.

`container_topology_complete` starts false and stays false on this branch. It
becomes true only after the **unchanged nonempty** exact one-PG/one-Ryuk, labels,
session and image-identity checks. PASS explicitly requires that flag as well as
all original conditions. Nonempty journal/ownership/removal control flow is not
relaxed. Forced removal remains a sticky failure, not a passing cleanup outcome.

### 2. Capture what exists, then separately require successful-test evidence

`capture_reports(gate)` now concerns faithful available evidence only. Each of
the existing `w01/backend-build/{test-results,reports}` roots starts UNKNOWN.
Only `FileNotFoundError` from that root's direct `lstat()` records ABSENT and
continues to the other root. A present directory becomes CAPTURED only after its
walk and every in-scope evidence copy finish. A missing `test-results` therefore
does not prevent capture of existing report logs/context. Both absent roots are
recorded explicitly rather than inferred from an empty file inventory.

Existing path/link guards, bounded digest, byte count, copy and before/destination/
after hash equality are retained. Direct `lstat()` plus standard-library `stat`
mode checks prevent enumerated-entry stat errors from being hidden by `is_file()`;
links and non-directory/non-regular entries fail closed. The only caught absence
is the initial root probe: walk/entry disappearance, permission/type, copy, size,
hash/drift and other raised errors still leave `capture_complete=false` through
the existing `attempt('capture-reports', ...)` failure path. Partial retained
copies are not a cleanup grant.

The small separate `required_capture_inventory(gate, profile)` retains both
required roots and the **unchanged** expected XML, effective classpath and matching
class-load-log presence gate. It runs only after available capture succeeds.
Missing success evidence records `required-capture-inventory` FAIL, leaves
`required_capture_complete=false`, and does not invoke diagnostics. An absent
required XML is never interpreted as a passing or executed testcase.

The existing file-cleanup gate still requires worker/container absence, the
before-file drain and `capture_complete`; it intentionally does not require
successful tests or `required_capture_complete`. PASS now explicitly requires
both capture flags and the topology flag, in addition to every old prerequisite.
This separates resource-disposal authority from success without swallowing a
capture error or weakening a passing-run requirement.

## Finite source-inspection cases — NOT executed tests

| Condition | Intended consequence of the authored control flow |
|---|---|
| Empty bound before/normal/raw-event/after/final Docker observations; both report roots positively absent | Absence and available capture can permit the existing owned-path cleanup, conditional on all existing drains/deletion checks. Required topology and required evidence remain FAIL; no test execution credit. |
| Missing `test-results`, existing report TXT/JSON/LOG/XML | Record first-root ABSENT, finish the second-root capture, keep required-evidence FAIL. |
| Present roots but missing XML/classpath/class-load log | Available capture may finish; unchanged required inventory fails; diagnostics stays unevaluated and overall FAIL. |
| Any capture stat/walk/link/type/copy/digest/drift error | Capture incomplete; no owned backend/private file or home deletion. Existing partial evidence remains retained. |
| Empty created set but any raw event, destroy record or remaining ID | New empty branch refuses authority; no container removal or owned-file cleanup. |
| Nonempty valid or invalid topology | Original checks/removal gates retained. Full valid evidence must still pass the original XML/identity/outcome/context and final-state requirements. |

## Unchanged boundaries and verification limits

- No edits to live Admin, Backend, App96 or any other worktree. Initial passive
  Admin observation was clean at `ecb1739cb216de12d0aa6c0e7c63d4b6f488140a`.
- No owner helper, process drain, kill target, container-removal target, cleanup
  path, budget, workflow, profile, init, request, dependency or source binding is
  changed. The same nonzero child still records its original sticky failures on
  subsequent drains; no deduplication or relabelling of historical failures.
- All PG02 constants/pins intentionally remain baseline values. This packet is
  a source delta for later separately reviewed PG03 preparation/binding, **not**
  a deployable new carrier or a request grant. No request/workflow is included.
- Original command logs and retained-inventory checking remain unchanged.
  `NORMAL_ABSENT` is absence only, not graceful shutdown, zero-kill or topology
  success. Native05 stays UNQUALIFIED; old PG18/PG02 results and limits remain.
- Only passive source/Git/text/hash/stat reads, these private source/document
  writes and byte-diff/checksum construction were performed. No target/helper
  execution or import, syntax/AST/static checker, mock test, build, CI, dependency
  acquisition, resource control, deployment or commit was performed.
- Independent actual-diff review and any authorized future verification remain
  primary-owned. The case table is source reasoning, not measured cleanup proof.
