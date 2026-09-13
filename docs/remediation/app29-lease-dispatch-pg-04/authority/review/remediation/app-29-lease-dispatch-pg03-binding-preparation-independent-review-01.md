# App29 PG03 binding preparation — independent actual-diff review 01

2026-09-13 UTC. NONAUTHOR: `w03_static_nonauthor_review`.
**SOURCE-ONLY APPROVE for the exact inert preparation below.** No blocking
source/binding defect found in this finite delta. This is not final-bound
approval, genuine v3 preflight, carrier admission, compilation or PG validation.

## Exact sealed input and comparison basis

Packet: `review/working/app-29-lease-dispatch-pg03-binding-preparation-01/`.
All 22 indexed content files were independently rehashed, as were both seal
files; no unlisted files. Files are0600, directories0700. The seal chain was
rechecked unchanged after review.

| File within packet | SHA-256 |
|---|---|
| `SHA256SUMS` | `47518dc19fc03c551696e2d2aaf046bd3b865f2a39435f23dd93d205c721a52b` |
| `SEAL.sha256` | `e0d42fdab3c199584a532ba5cd8c2e6074c54dbd20f8192000fc3e0886aef674` |
| `ci/app29-gate-b.py` | `47cd90483e1831f477dec7302462452d1c4e46f9d00c9531c97ca11b22589710` |
| `profile/profile.json` | `b435c0cfe1b372c443659069439a31638b7bb1c9c8875de291cff82b51d17dad` |
| `profile/profile.init.gradle` | `78c256c8e9dbe6e86eba22a386133502ed7e06dc80fcadc52b5cb1ea6b5e5a83` |
| `.github/workflows/app29-gate-b.yml` | `d66cf2e2c8c4b2ee95a22828834213d3c726328f03f8949b2bdd54a14ccc6f3c` |
| `ci/app29-gate-b.request.json` | `c6102de188b68113a2c8f534ced7cef3eb196ac280df94352e0a37e303c3f80f` |
| `selection.json` | `04bcb997c228ddc4d2c3df79f52e787e31d8773864560f7266209961d0132916` |
| `source-delta.patch` | `3462e9c7d2e94bb129be635d5d1513066bf28336f84a33c7ee9e20f537a5064d` |
| `controller-binding-delta.patch` | `16354e30a6d7216e3c461406b24db27a628e89d82218297010ed70b398433f9b` |
| `tooling-delta.patch` | `7e9d03ac29ee5a898587157cc5ec3ec7eef9c98c71e578e0237c7d75e5477970` |
| `dependency-pins.json` | `0c0cc241034eee93e5d8db710d280f816d34a86c6a439c318d7540605c5f8116` |
| `COMMANDS-REMAINING.md` | `0ed3ed29f026d1c27cb54982ceb7f81e89f8e450992b544bab619679c7e7845f` |

The five `baseline/pg02/` tooling files match their immutable original PG02
bound files byte-for-byte, rather than a moving live Admin worktree. Controller
baseline is `406febde3a67c108e987657489c6b429c3e735286aff8563a3a172dd6faf422d`.
The separate approved-cleanup baseline is
`30b9ab8a43b6b9277ac401569ddfa62ef44282929d6bb21badbf2f7abe5c1024`.
Reconstructing the complete five-file delta, cleanup-to-binding controller delta,
and selection delta independently reproduces all three retained comparison
patches byte-for-byte; no source change is hidden outside those comparisons.

## Material findings

### 1. New source follows actual PG02, without rewriting it

Controller629–784 retains the prior PG02 source/checkpoint/selection and adds its
actual frozen run manifest and raw FAIL result before the one-file PG03 stage.
All preexisting `pg02_*` profile values remain identical; the old source-inventory
object is retained verbatim under `historical_pg02_source_inventory`.
Only five existing profile keys change: ID, scope, report directory, current
selection and appended limits. New historical/current binding objects are additive.

The PG03 source manifest
`review/working/app-29-w03-integrated-driver-lease-dispatch-pg03-source-01/manifest.json`
SHA `9a13d2299b7c58e23a6aaf67e1140c0a5d0c906ec7f574bcac8f3c877f0ff786`
has all **481** source hashes matching Git blobs at
`f2e58eac0b139dca3a042c724d69c66a3d65278e`, all **214** snapshot files matching
and all **348** seed paths preserved. Actual old/new maps differ only at the
reviewed test file; removal, subject and historical maps remain equal.
Its full issue diff hashes to
`075443cf4c24f1a7e95e30915ce6043d238a65095712aa2b045d09ef2ab91a61`.

Raw no-replace Git commit reads confirm tree
`e192c9430c89e4549f1840bf7e333fed75bc290a` and sole parent
`c67ddcd30fbae2438c7b2f803f720530b598e428`, itself the unchanged PG02 child of
`8938526fd8fee2dfcb66ab3df4c85dfeb91cdee3`. Controller1031–1090 adds exactly one
existing-owned-command PG02 commit read to each before/after source census and
requires those exact parent/tree facts. No new helper or resource-control path.

The source patch is identical to the separately reviewed Java-overload
`assertThrows` correction, including the unchanged `lease.enterDispatch()` action.
The committed PG02-to-PG03 diff has only that one call replacement; this review
neither recompiles it nor claims the previous compiler failure is resolved.

### 2. Current transport and original source checkpoint stay distinct

Current transport receipt:
`review/working/app-29-lease-dispatch-pg03-transport-source-01/checkpoint.json`, SHA
`571d37796e8dbf453aa6b5869e88eed74330d190e0f22ea6be20666ec3ec6c34`.
Current bundle is its sibling `backend.bundle`, 287442 bytes, SHA
`b606cb5ed40814dc23c5c8c61a564de07d917d4a05b6fbca4c4b73841bea63fe`.
Passive header inspection confirms the exact public prerequisite
`3d839130c807f6a0a9b1c896c1c6cca4b41c4538` and singleton named ref
`refs/heads/remediation/app-29-backend-complaints` at the exact PG03 head.

Controller748–770 binds the full original source checkpoint separately from this
transport-only receipt. The original HEAD-advertised bundle
`04a50353016f2a57621e6a9810c25be6864ce42d45ea42c5d72cdb67d127052f`
is preserved and pinned only as history. The actual bundle reader/header protocol
and source-materialization command sequence are byte-identical to cleanup30b9:
no HEAD fallback, broader ref acceptance, network transport or public push is added.
No bundle import/verification command was run by this reviewer.

### 3. Same two methods and cleanup gates; no historical replay

Selection, profile and controller retain the same two literal noarg method
selectors, five task argv, one required XML file and two exact testcase identities.
The success requirement remains 2 PASS / 0 FAIL / 0 ERROR / 0 SKIP, not count-only
acceptance. Init/workflow changes are labels, current paths and inert hash guard
only: ordinary main/test compilation, one worker, parallelism restrictions,
pinned actions, private-repository restriction and all budgets remain unchanged.
The prior16, enum and former OwnershipIT are not selected for replay.

Text comparisons against cleanup30b9 prove these whole sections byte-identical:
owner fail/attempt/cleanup/output-absence/drain/command methods; census/container
logic; available/required capture; and the complete `execute` finally block through
its PASS/status assignment. Diagnostics differs only by its matched PG03 guard
label and additive historical-PG02 result field, not acceptance criteria. All
three capture/topology flags and every prior PASS prerequisite remain mandatory.

Existing focused evidence is unchanged:
`review/remediation/app-29-lease-dispatch-pg03-cleanup-synthetic-review-01.md`, SHA
`5bd2b60053e993e8d48cafe11d6e1cc67a66698bcf9d76165a3f41ba6cd0392c`:
four groups/19 fixture cases/three false-flag probes PASS against cleanup30b9.
That tests the carried cleanup seam, not this entire new binding controller or a
real PG fixture. No tests were rerun here; no additional helper/ownership or
historical-attestation test gate is recommended for this binding-only delta.

Actual PG02 result SHA
`dbd0e7635561d9d733f644d40520581b25efcfb8afb20a60d4330399d738c0df`
remains FAIL with seven sticky failures, diagnostics NOT_EVALUATED and incomplete
capture/output disposal. There was no PG02 test XML; it is not two runtime test
failures or retroactive cleanup success. PG18 and Native05 limitations remain.

### 4. Data continuity is checked; execution readiness is deliberately false

All **355** data-only dependency candidates and **33** new-stage provenance pins
match their actual files. Both SHA mirrors match their JSON maps. The unchanged
five base tools and nonconflicting **325** inherited approved/tooling union entries
are preserved, as are the actual staged complete-diff requirements and profile
provenance maps. These are not final authority counts or a v3 validator receipt.

Controller163–168/251–304 and Gate initialization refuse zero profile/init pins
before target output or owner/resource acquisition. The init independently rejects
its zero guard. The profile still says `UNBOUND_PENDING_PRIMARY_ADOPTION`; request
is `authorized=false`, attempts1, with zero checkpoint and four tooling digests.
Those are deliberate hard stops, not wildcard bindings. No runnable carrier or
source acceptance can be inferred from this template approval.

## Remaining primary-owned gates

The sealed `COMMANDS-REMAINING.md` correctly separates the work still required:

1. Accept the exact source/preparation and synthetic reviews; adopt only the
   current-stage changes into fresh bound copies, preserve historical evidence,
   and finish the actual profile -> init -> controller/workflow digest cycle.
2. Close and rehash the real nonconflicting dependency set, including sealed
   preparation, final bound originals and actual accepted reviews; retain the
   complete source/snapshot/seed inventory and fresh whole issue-baseline diff.
   Do not treat355 as a final count or overwrite contradictory old pins.
3. Use the unchanged real v3 freezer/validator
   `e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`.
   Preserve actual argv/stdout/stderr/exits and the genuine validator stdout for
   the exact new manifest; no fabricated or copied preflight JSON.
4. Only then bind the distinct deployment checkpoint, exact transported/deployed
   bytes and final false request. Independent actual-bound review and explicit
   one-attempt admission remain; primary's Apple05 serialization governs any
   later PG03 launch. This review grants no dispatch or automatic retry.

Only passive source/Git/JSON/text/hash/stat reads, in-memory byte comparisons and
this new private0600 report were used. No syntax/AST check, target/helper import,
freezer/preflight, build/PG/CI, bundle import, resource control, live Admin/Backend/
app edit, other-preparation edit, commit, deployment or push. Backendf2 remains
private and unvalidated by this review; no W03/full47/consumer/production or
integration closure is claimed.
