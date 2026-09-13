# CoreC2 SQLClientInfo PG1 — private preparation01

2026-09-12 UTC, Admin04. **SOURCE-ONLY PREPARATION FOR INDEPENDENT REVIEW.**
The new one-method selection is **UNEXECUTED**. No live source/carrier edit, new
source commit/bundle, fresh v3 freeze, preflight, deployed acceptance checkpoint or
execution admission was performed. Request remains `authorized=false` with64 zeroes
for its **new deployed checkpoint** hash. Primary owns all subsequent admissions.

Authority is `review/remediation/app-29-post-pg14-next-delivery-proposal.md`, SHA256
`b330c65b268cd6d6a0540b6a105a206ef2cf37dd55d6ddbe95d3cf4f28305dcb`.
Nearest root/Admin/Backend AGENTS, current tracker/handoff and checkpoint/proposal
were reread. The initial reconciliation105 PG14-review-pending status is superseded
by the newly read primary **ACCEPT_FOCUSED_PG14_ONLY** receipt:
`review/working/app-29-core-c2-product-lifecycle-pg14-admission-01/primary-acceptance.json`,
SHA256 `265d9443479871281367a38d29700814c60d475554d76fd75e105522728b6485`.
It adopts independent result review `a4e4462f...`, exact14 on private6db944, not the
new selection. No new PG14 audit or rerun was undertaken here.

## Exact five-file derivative, not another harness

`carrier.patch` is the actual five-file unified text diff against matching `before/`
copies, SHA256 `c3b90d5a6e8e47ffe3a5f9ce72130caa39f419f1b60879f0973916ae78189142`.
Controller845 ->861 lines. No helper, fixture or product file is changed.

| Packet-relative candidate | PG14 before SHA256 | PG1 candidate SHA256 |
| --- | --- | --- |
| `ci/app29-gate-b.py` | `7fce9fae743a4d235350d2c93610142fc7a0177f2b7d7e44031b56b8315f0576` | `ad2d09e5dd5419ba48bc66b73ccfd502a593e88ca2362b7b277a8dfe6f759d2d` |
| `.github/workflows/app29-gate-b.yml` | `790377568f065d1e2f64bad1a796a3d17f4a32cea224204adda25465c5d3a328` | `6088e8813ceafd11ade49274b12a07395cf674d39696ca1fbdb500e42f0c3ea4` |
| `ci/app29-gate-b.request.json` | `14c5b4a48388e3f9318e8b2742a2ef21e7b072173bbe5f1df0c0ba76b75aabd7` | `a80f7c2618ab201bd6b08fa86ed851cd4b3e29b031b991c1b29b20a584ba8c9b` |
| `profile/profile.json` | `36c3637229efbe08186014f4c60684aa0569430b26bae9d13f8b811917e82225` | `173b4f5131cacd7b89b8bd24b1700eac34218969b7921c80a6beb9dee72c0d37` |
| `profile/profile.init.gradle` | `61fb92e47baa8dcabcd6a7521e01872984e196d16cfd643776f3a50b25a81964` | `f4d6c74702278adc8224ee834da7735884281bd83b977da40d5e111bfe70568d` |

First three before-images copy the live PG14 carrier/workflow/**authorized** request.
The two profile before-images copy immutable PG14 preparation bytes. That older
preparation's separate unauthorized request (`2934820e...`) remains unchanged.
`before.sha256` and `after.sha256` bind exactly those five pairs.

The only extra documentary copy is `before/pg14-deployed-checkpoint.json`, identical
to `kira-admin/docs/remediation/app29-core-c2-product-lifecycle-pg14-01/checkpoint.json`
(`b977d7836997e0da2866ee440dad5140452a108731f6d740b68c43032b3fe5bb`).
It keeps this historical input under `review/`, as required by the unchanged v3
freezer. It is **not** the new checkpoint or a sixth candidate. The source transport
receipt (`6e7cfcdb...`) is a third distinct, also historical, object.

The shared ownership helper remains
`56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385`.
There are still five additional active deployments: carrier, workflow, profile,
init and that unchanged helper. Existing run/cleanup/dependency routing is reused.

## One selector / one XML case / one PostgreSQL plus Ryuk

New gate/request schema: `app-29-core-c2-sqlclientinfo-pg1-01`.
New profile: `app-29-core-c2-sqlclientinfo-pg1-profile-01`.
Exact task argv is these **three** strings, with no extra task or class:

```json
[
  "test",
  "--tests",
  "me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest.real lease preserves Properties client info defaults and declared stale and foreign failure shapes"
]
```

Expected raw XML file:
`test-results/test/TEST-me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest.xml`.
One ordinary suite/case of that class, display name exactly
`real lease preserves Properties client info defaults and declared stale and foreign failure shapes()`.
No wildcard/backtick/parentheses in the CLI selector, parameterized expansion or
positive worker witness. Profile/init/CLI/XML/classpath/count/result labels are all
rebound to1; failures/errors/skips, extra/missing/duplicate identities remain failure.
Normal compilation dependencies are unchanged; there is no standalone compile/static
batch or unchanged38-unit replay.

Source facts are already documented in the pinned proposal and reread here:

- `PhysicalJdbcDescendantsTest.kt:40–48,211–238`, SHA
  `a2e3ce055fcb98c350c49fff7522b959f223369568220312d5b1761c9369f2a9`:
  PER_CLASS/SAME_THREAD, one lazy fixture and AfterAll close; one existing @Test.
- Top-level `withOwnedCutPool` in `PersistencePgOwnedCutIntegrationTest.kt:1370–1387`,
  SHA `b87e92bb9d78fb8f37afed414bd07899c59606536b972c6a444dda1cbc677322`,
  uses the **passed database**. One Hikari slot/two physical custody cells are not
  two PostgreSQL containers; calling this helper does not instantiate/select PG14.
- `PgLifecycleDatabaseFixture.kt`, SHA
  `f9708f4a7aa4ec011ce13d4f850df485832ec341a536d02741b80178abc92bb7`,
  owns one non-reused PostgreSQL17.6-alpine. Expected separately owned population
  remains **2 total /1 PostgreSQL /1 Ryuk0.12.0**; no guard or budget is loosened.
- The named method covers defaults-backed Properties strings, non-String same-key
  fallback without mutating caller Properties, both foreign-thread setClientInfo
  overloads yielding SQLClientInfoException, and stale Properties-overload refusal.
  It does **not** inject every finally failure or assert the stale String overload.

## Explicit diagnostic nonapplicability — never vacuous CAPTURED

The method never sets `OwnedCutPool.shutdownDiagnosticCase` (default null). The
same helper's ordinary assertions still require actual shutdown observation,
zero future lease entries/active operations/constructing, sealed factory and real
retired generations. Those assertions emit **none** of PG14's fixed scalar rows.

- New profile binds `shutdown_diagnostics = {"status":"NOT_APPLICABLE", "expected_record_count":0}`.
  The carrier requires exactly that scope and **no diagnostic rows**, reports empty
  coverage and `fixed_scalar_capture=NOT_APPLICABLE`, and requires this explicit
  state separately from actual one-case PASS in its final gate. Empty collections
  cannot manufacture CAPTURED. The old row-syntax parser is retained only to reject
  malformed/unexpected rows; even a syntactically valid PG14 row refuses this scope.
- The original PG14 profile/carrier remain byte-identical (`36c36372...`/`7fce9fae...`):
  **RETURN_SAMPLE and FAILED_POST_CONSENT_TAIL each require CAPTURED BEFORE/AFTER,
  all four rows**. Missing/duplicate/UNAVAILABLE required rows cannot pass that gate.
  Their original accepted XML/result/primary acceptance are pinned as history,
  not rewritten, synthesized, rerun or blended into the one-case outcome.
- Historical PG14 scalar non-atomicity and `observation=NOT_OBSERVED` are not
  completion/causal/consumer proof. New nonapplicability says nothing about those
  historical scalars and does not waive real cleanup or source/capture gates.

## Zero new source delta, complete private ancestry

Backend remains clean private `6db944871c1584bd6a1f28263e8010cadd766fab`, tree
`3558d08d9dfc826c6c1c4a79d26265f7cdee54cb`, parent1c91. Reuse the existing
217809-byte bundle, SHA
`2506c18cc5e40f089cc1176a65a79d449ff02b13f4c08e0719c24d359e9882da`,
from `review/working/app-29-core-c2-post-structural-private-checkpoint-01/backend.bundle`.
Do not create another source commit or expose private ancestry publicly.

The carrier preserves before/after source/bundle/clean-tree checks and the exact chain:

```
6db944871c1584bd6a1f28263e8010cadd766fab
->1c91f0c2d1a4d797e83a0e33b871b417ebcfaae1
->eb8fed8b6b620a0c7448c223bf49c1683f8eaadc
->989a8c07b90d956a5f2484f223be41b5d99a8a3c
->926927ab805a2a3b78957862f3b744d0fe399ac5
->49da0919d9ec3091cb7bb041009dc9bd5f3e090f
->3d839130c807f6a0a9b1c896c1c6cca4b41c4538
```

The diagnostics466 ->original8 replacements ->PG10 ->structural19 ->PG14 ladder
is retained. **PG10 argv now binds its own immutable profile's21 argv**, not
`TASKS[:21]` from the new3-argv selection. The new PG14 predecessor check requires
its own profile's29 argv, exact source/removal/review-subject/history equality and
`selection_source_delta={}`. All466 current source hashes must stay identical to
PG14 manifest `fc979ee558b53d18337b0a5104f2b574e0bde2147a52f5ac96585a779c56a121`.
Original8 provenance and structural19 are not relabelled as a new product delta.

All143 PG14 approved-input and10 tooling pairs are required as approved provenance,
in addition to original history. Active tooling remains original5 +new5 =10,
not every prior carrier. All348 seeds,199 snapshot subjects,102 historical inputs
and complete source map/removals stay bound. Fresh snapshots must use a fresh
new-selection path; a matching old source map does not authorize old context reuse.

## Primary-only next handoff

`recipe.json` is inert full-input/argv/transport data; not a runner or result.
It requires **expansion of every predecessor approved-input/tooling pair**, all
specified profile maps, exact new candidates/before request, primary/reviewer
adoption pins and this finished packet's real hashes. Only `review/` inputs go to
the unchanged freezer (`e8c6a48f...`); original5 +new5 is enforced by the carrier.

1. Obtain independent source-only review of this sealed five-file derivative and
   primary disposition. This author supplies no independent approval.
2. Recheck actual clean6db and stable local/origin integration refs. Backend11 is
   already settled at `b2324508dd7c3c11d894e4c9a815f5e30387369a`; do not preserve
   any stale Backend11 pending hold or copy old context across later changes.
3. Primary creates a genuinely fresh full-v3 one-method manifest at
   `review/working/app-29-w03-integrated-driver-core-c2-sqlclientinfo-pg1-01/manifest.json`,
   then saves genuine local preflight stdout for that manifest and exact3 task argv.
   No preparation hash or historical receipt substitutes for either operation.
4. Transport the complete authority maps/199 snapshots/actual receipt/diff, exact
  5 deployments and existing bundle privately under the new payload
   `docs/remediation/app29-core-c2-sqlclientinfo-pg1-01`. Preserve PG14 payload/history.
5. Only primary creates a new deployed acceptance checkpoint, hashes it into a
   **separate final request**, and separately authorizes at most one attempt.
   Keep this sealed unauthorized request unchanged. Neither historical b977d783
   nor source-transport6e7cfcdb can fill its unresolved64 zeroes.

Any drift stops for primary disposition; no broadened selector, changed profile
under the same hash, PG14 rerun, additional fixture or public private-source push.

## Unchanged resources and remaining product gates

Same25min job /1200s controller /120s preflight /900s validation /180s cleanup;
same Gradle2GiB heap/512MiB metaspace, max-workers1, one512MiB fork, forkEvery0;
minimum8GiB free and max8MiB source bundle. Existing operation budgets stay unchanged.
Same original18 dependency route, bounded paths/files/archive, duplicate-key/XML
protection, environment isolation, JDK/classpath/hash capture, no agents/loader
overrides, owned subreaper/session drains, sticky nonzero/forced cleanup,
capture-before-delete and honest UNKNOWN. No acquisition or new safety harness.
Strict dependency mode without verification metadata remains **not** transitive-byte proof.

Carry acceptedPG14/PG10/38 units/normal compile/statics in their exact separate scopes.
Preserve **CURRENT PG14** PostgreSQL kill9/die137 as well as earlier journals:
NORMAL_ABSENT is not graceful shutdown or zero-kill proof. Keep original45/47 and0/2
cleanupFAIL/containersUNKNOWN/outputs_absentfalse/six retained directories unchanged.
Native05 remains UNQUALIFIED; opaque/native-finalizer/pin/compaction/liveness/full/
consumer/P3/W03/App29 gates stay open. No shipping enablement or issue completion.
Original D05 PARTIAL and original D06 unreviewed/unexecuted artifacts remain, while
already-reviewed/imported D05/D06-v2 successors are preserved and **not restarted**.
Their full runtime acceptance remains separate.

Optional next product slice, **outline only**: one private ordinary named phase
through the selected guarded Spring resource/manager to real scalar JDBC write and
rollback, then genuine lease/quiescence/permit release. Refuse ambient/foreign/second
lease before borrow while preserving same-resource REQUIRED; no public profile
activation. Primary must choose the named phase/resource contract before source
implementation. Existing composition is not rebuilt; checked capacity/audit/scoped
step-up connections remain subsequent work as in the pinned proposal.

## Verification scope and report seal

Only private text copies/edits/diffs, JSON-as-data reads, filesystem/Git readback and
SHA256 byte inspection were performed. No carrier/helper/freezer import or execution,
AST/compile/checker/test/build, freeze/preflight, Docker/network probe/download,
dispatch, Git write or live source/carrier edit. All new writes are confined to this
new preparation directory; no owned background worker was started.

`inputs.sha256` pins52 direct/inherited authority/source/tool observations (workspace
relative), not a fresh source inventory. Its live-request pin is the observed PG14
before-image, not a requirement to keep that live path PG14 after future deployment;
the sealed before copy carries those bytes. All52 input hashes and the five before/
after pairs matched passive readback. Both repositories were still clean; new
one-method freeze and payload directories were absent. `packet.json` records the
five pairs plus one historical checkpoint copy. `SHA256SUMS` binds18 packet members;
`SEAL.sha256` binds that sum file. These source-only seals are not runtime evidence.
