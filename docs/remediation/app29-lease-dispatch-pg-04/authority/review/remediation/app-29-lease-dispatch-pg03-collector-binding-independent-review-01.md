# App29 PG03 — collector delta and read-only binding review 01

2026-09-13 UTC. NONAUTHOR: `w03_static_nonauthor_review`.
**SOURCE-ONLY APPROVE the mechanical collector delta; accept the recorded
PASS_TRANSPORT_BINDING_ONLY within its stated read-only scope.** No blocking
new defect found. This does not authorize request activation, commit/push or CI.

## Exact inputs

All new files below are under
`review/working/app-29-lease-dispatch-pg03-admission-01/`, regular0600.

| File | SHA-256 |
|---|---|
| `launch-and-collect-01.py` (106 lines / 7777 bytes) | `66072f539accc877392f90c29a5adc5c0175500143f36fa9e2bfb969ba56b086` |
| `collector-binding.diff` (4508 bytes) | `2d4a7efdb0434ac87cc86c8a7cf1ae071ba60620ba3bcbef5c52cc342d9411f7` |
| `read-only-binding-command-01.json` | `3c14769df042f1e176fc78c3fe4a9ec81ea9988d964b4cd49898458eb8bc2ec5` |
| `read-only-binding-exit-01.json` | `81868a6e94ffc0178bf833deb1c9013d9fab4ee95ddb876a5e8ec4f1d26376d2` |
| `read-only-binding.stdout` | `39615e0f36a5961a74c0755f6a927982a1ceb64d47c1c917abdc38c50badb21d` |
| `read-only-binding.stderr` (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `read-only-binding-result-01.json` | `8b70ec01142e553e9f6f98d6449cf4e5f9ba15343c869a362230e09ecb555199` |

Baseline is the immutable PG02 admission collector at
`review/working/app-29-lease-dispatch-pg02-admission-01/launch-and-collect-01.py`,
SHA `8266f05c1b3b7f243a767931d86df24b6a4096a3de5cf54ac76713d1ab604191`.
The prior actual-bound review remains authoritative for its completed inventory
checks: `d16debdb74b19651f21d48266ea3a9a040531c8d9a5ea03174455244a688d740`.
Its708 original/staged authority-pair checks were **not repeated** here.

## Collector findings

Reversing exactly seven mechanical substitutions reproduces the entire old
collector; independently rebuilding the unified diff reproduces the retained
patch byte-for-byte. Changes are PG03 launch/profile/payload/artifact namespaces,
current Admin parentbc17ad0e, the separate hosted lock, current tooling-map shape
and the unique commit title. No other executable behavior changes.

- The new `relative -> sha256` tooling loop matches all five entries in actual
  `transport-prepared.json` and the current request. It replaces the old nested
  tooling-record shape without dropping a per-file check.
- Locking changes only to `.kira-validation/hosted-validation.lock`; the same
  nonblocking exclusive lock spans the observer's guarded work and collection.
  This separates hosted observation from a local heavy-batch lock, not authority
  to start local builds. The8GiB floor and active-private-run refusal are retained.
- The same private Admin repository/branch, private-repository/push-permission
  check, exact local/remote parent, empty index, NUL-delimited status allowlist,
  fixed path scopes and exact staged-path equality remain. Other request files
  must still match their before-pins. No public Backend target, expanded deployment
  prefix, new workflow trigger or alternate push destination is introduced.
- One scoped commit with `[skip both]`, one private branch push and exact remote
  SHA readback remain. Discovery is by that commit and the existing workflow;
  multiple runs are refused and API observation requires the exact head and
  attempt1. There is no dispatch, rerun, retry or cancellation command.
- Collection still requires the unique nonexpired run/attempt-specific artifact,
  bounded artifact size/disk headroom, raw workflow log, per-file hashes and no
  links. The result remains `RAW_RESULT_REVIEW_REQUIRED`, even on a completed
  failed run. Fresh launch-directory creation refuses overwriting old evidence.

Existing observer limits remain: lock release is not remote completion or cleanup
proof. Timeout/uncertain push or run observation must be reconciled by primary,
not converted into permission to retry. This source review did not acquire the
lock, contact GitHub, stage files, commit, push or download artifacts.

## Actual read-only binding receipt

Recorded command/result bracket:22:08:57.233326Z–22:08:57.703246Z, timeout120s,
exit0, empty stderr. The command loads the pinned controller definitions under
`__name__='pg03_readonly_binding'`, changes only the in-memory `BACKEND` path to
the existing local checkout, reads the still-false request/profile and calls the
actual `bind_freeze`. The main guard does not run; no `request()`, Gate instance,
owner helper, command/resource method, controller execution path or v3 rerun is
called. Module-definition loading is not misrepresented as a full hosted run.

The2197-byte stdout parses exactly to the retained result's `binding_result`.
Controller pin is
`406b9fd6af8913de5ec5aa9eb1426cd9bc8eb95a0a1717deb818a9d42ec4b382`,
request pin is
`bfa7771fb1567a046d7551eacd21f065271f6186f5f17f29fc5967b3e6e9cf53`,
and manifest pin is
`0df6165f928d7a752d7a253d18078b099ca81eae9c7d5bc466bc828a74763f1f`.
These match the current bound inputs and prior review. The result reports481
sources/348 seeds/708 authority files/214 snapshots/325 provenance pairs and the
exact one-file replacement. It explicitly says local receipt adoption, not hosted
v3 reexecution, and retains Native05 UNQUALIFIED. This is real transport-binding
function evidence, not compilation, PG test, ownership or cleanup evidence.

## Remaining primary boundary

The request is still false. `transport.json`, `primary-admission.json`,
`other-requests-before.json` and `launch-01/` remain absent at review time.
The collector is therefore not admitted or ready to invoke, despite source approval.

Primary must accept this review, preserve the false-request evidence, separately
authorize the sole false→true transition and measure the real `--emit-target`
result through the normal request guards. A successful read-only `bind_freeze`
does not substitute for that authorization/emit check. Final transport/admission
records must bind the actual activated request/checkpoint/tooling and other-request
pins, with one attempt and unchanged scope. Only primary may then admit the exact
collector for one private push/run/collection. No automatic retry or wider tests.
Historical PG02/PG18 failures and all prior product/qualification limits remain.

This reviewer used only passive source/JSON/hash/stat comparisons and this new
private0600 report. No collector/binder/controller execution, syntax/AST check,
708-pair replay, v3/build/test/CI, new harness, resource control or existing-file
edit was performed.
