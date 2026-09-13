# App29 PG03 cleanup seam — focused synthetic execution review 01

2026-09-13 UTC. Candidate-nonauthor reviewer / synthetic-test executor:
`w03_static_nonauthor_review`.

**PASS: all four authorized synthetic groups, 19 isolated fixture cases and three
additional false-flag probes.** This is measured finite cleanup-seam coverage,
not a real PG test PASS, ownership qualification, carrier binding or deployment.

## Exact inputs and execution

Candidate:
`review/working/app-29-lease-dispatch-pg03-failure-cleanup-preparation-01/ci/app29-gate-b.py`
— SHA-256 `30b9ab8a43b6b9277ac401569ddfa62ef44282929d6bb21badbf2f7abe5c1024`.

Governing source review:
`review/remediation/app-29-lease-dispatch-pg03-failure-cleanup-independent-review-01.md`
— SHA-256 `1907703d923d440311b720137016d420702ecfa861f87009cd53b9f2283bcbb1`.

Harness basis (read-only):
`review/working/app-29-gate-b-hosted-draft-06/tests/test_failed_capture_cleanup.py`
— SHA-256 `0437ff7cf1327b890509b7934d76b7b3e05e532cfd1f70624020c5355de41689`.
The new harness adapts its whitelisted-AST / exact-finalization-slice approach;
it does not replay the old suite. All three input pins were reverified unchanged.

Only one invocation; no retries or subsequent test runs:

```text
timeout --signal=TERM --kill-after=5s 90s python3 -I -B review/working/app-29-lease-dispatch-pg03-cleanup-synthetic-01/test_cleanup_synthetic.py
```

UTC bracket: **2026-09-13T20:49:28Z–20:49:29Z**. Exit **0**, normal completion,
no timeout. Python 3.12.3; unittest elapsed **0.114s**. Four tests ran with zero
failures, errors or skips. All 19 case receipts have `assertions_completed=true`.
Eighteen deliberately negative synthetic gate outcomes are FAIL; the one
complete positive control is PASS. These expected gate failures are not failed
harness assertions.

## Actual candidate code exercised

After checking the complete candidate SHA, the harness executes unchanged,
selected AST function nodes and exact statement slices, never imports or runs
the full candidate/controller module:

- Helpers: `require`155–157, `safe`168–177, `digest`180–183,
  `unique`186–191, `save`199–200, `remove_owned`203–207.
- Gate methods: `fail`825–834, `attempt`836–841,
  `cleanup_outputs`843–849, `output_absence`851–856,
  `census`983–986, `containers`988–1052.
- Capture functions: `capture_reports`1055–1091 and
  `required_capture_inventory`1094–1104.
- Exact `execute` slices: capture integration1261–1265,
  file-cleanup gates1273–1280, final census/home cleanup/output absence1283–1296,
  and PASS expression/status1324–1331.

Seven pure constants are selected: `CACHE_PATHS`, `CREATOR_CLASS`,
`EXPECTED_TESTS`, `GUARD_IDS`, `IMAGES`, `METHODS`, `TEST_COUNTS`.
`inputs.json` records function source-segment hashes and exact slice line ranges.

Real `Gate.__init__`, owner helpers, command execution, drain implementation,
binders and full `execute`/`main` are excluded. The command stub permits only
synthetic census/event/image bytes and rejects every removal/unknown request;
drains return synthetic success, and the synthetic clock rejects sleeps.
`diagnostics` is an explicit synthetic-success boundary, not the actual parser.
XML identities come from candidate constants; classpath/context bytes are
synthetic. Therefore the positive result proves predicate/control flow only,
not real test identities/outcomes, JDK/classpath validity or process custody.

## Four groups and observed assertions

1. **Known-empty disposal, still FAIL (one fixture).** Empty normal/raw/after/final
   observations and both absent roots permit available capture and all eleven
   candidate-owned fixture-path deletions. Required capture and topology remain
   false. The existing nonzero-child failure and missing-topology/CAPTURE_ROOT
   failures persist. The empty owned-container observation is retained; no image
   inspection or removal is requested. Overall synthetic gate FAIL.

2. **Available versus required capture (two fixtures).** With the first root
   absent, the second root's `.xml/.txt/.json/.log` bytes and hashes are copied;
   HTML is intentionally outside scope. Root states are ABSENT/CAPTURED and the
   CAPTURE_ROOT failure remains. With both roots present but required XML missing,
   available capture succeeds and CAPTURE_REQUIRED_INVENTORY fails. Both cases
   skip diagnostics, preserve copies through eleven-path disposal and remain FAIL.

3. **Fail-closed boundaries (fifteen fixtures).** Seven custody cases cover an
   ignored raw `die` event, unknown current ID, orphan destroy, partial topology,
   unknown image, nonempty fresh after-census and failed fresh after-census.
   None grants absence/removal: topology stays false, containers UNKNOWN, and
   all eleven paths are held with zero candidate cleanup attempts. Eight capture
   cases cover initial-root PermissionError, regular-file root, nested link,
   nested FIFO, walk PermissionError, enumerated-entry FileNotFoundError, copy
   hash drift and a sparse file of 64MiB+1 rejected before read/copy. Available
   and required capture remain false, diagnostics is skipped, expected failures
   persist, and all eleven paths are held with zero candidate cleanup attempts.
   Partial valid copies survive the disappearing-entry case. Every case is FAIL.

4. **Complete inventory / mandatory flags (one fixture, three extra probes).**
   Synthetic valid PG/Ryuk create/destroy/session/image records and all three
   required raw evidence files reach true available-capture, required-capture
   and topology flags. Copies survive eleven-path disposal; no failures remain
   and the synthetic predicate reaches PASS. Independently falsifying each of
   `capture_complete`, `required_capture_complete` and
   `container_topology_complete` forces FAIL; restoring all true restores PASS.
   Two synthetic image inspections occur, no removal request.

## Cleanup and retained evidence

Packet: `review/working/app-29-lease-dispatch-pg03-cleanup-synthetic-01/`.
Each of the 19 fixtures was a separate TemporaryDirectory directly inside this
packet. Each immediate teardown receipt records removal. Passive verification
confirmed every fixture path absent, no residual directories/bytecode, and the
recorded Python PID23590 absent from `/proc`. In the fifteen hold-output cases,
only fixture teardown later removes the paths; that is not candidate cleanup.
These local fixture/process checks are not remote PG resource-cleanup proof.

The packet directory is0700 and exactly these nine retained files are0600;
size/hash/mode and evidence summaries were independently read back. Existing
packets, source and candidate were not rewritten.

| Retained file | Bytes | SHA-256 |
|---|---:|---|
| `test_cleanup_synthetic.py` | 29212 | `f0358214820ad2d03ba9e1d05825513961212a26e25ca00b3954cc46f1fdb367` |
| `inputs.json` | 4765 | `440f7bfb5207e17901a17df494b7f84c7a79c52e5ced31b8a18dac7382266180` |
| `result.json` | 135241 | `978822da1dd75c34eff1ded7b7fe542bcdddc453e8a0c17626b04e8ab81857d6` |
| `tests.log` | 608 | `63171750c3fa3ae816c6b45f6c7132d1bcfe8497c9c197c35f88e3978efc2dd6` |
| `command.log` | 160 | `8cc80e96700b8da6967da7a8c058e7964f598251f620f370f4984e5db15b4942` |
| `invocation.txt` | 145 | `e2d226d5e729feaa0b37585f1685d6e671e400b45edf9f83341c63cc8327d842` |
| `exit-code.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `started-utc.txt` | 21 | `edb3d674edcf1e23e72e79c3704057444f1d85589601f015356cd81fc116258e` |
| `finished-utc.txt` | 21 | `f576d82a48527c22ff5ea491484c40f14531a2511c6b5e3c9a850401408bb9c9` |

## Limits and handoff

No real Docker, Gradle, JVM or CI run, credential access, ownership helper,
resource qualification, spawned child, full controller execution, live
Admin/Backend/app change, commit or deployment occurred. Only the new private
test packet and this private0600 completion report were created; disposable test
fixtures were removed. No broader tests were rerun or added after completion.

This task does not bind or deploy the prepared candidate as a PG03 carrier and
authorizes no automatic integration or retry. Historical PG02 remains FAIL with
its original evidence untouched. Primary's Backend checkpoint `f2e58eac` is not
validated or made public by these synthetic results. Native05 UNQUALIFIED and
all product/external limitations remain. Primary owns any separate binding,
integration decision and real run.
