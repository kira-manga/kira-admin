# W03 ordinary-connected PG recipe01 — independent preparation review

2026-09-13 UTC · `/root/backend20_correction_review` · private0600.

**Conditional design concurrence.** The sealed packet is a sound inert plan for a narrow
successor of the existing private Gate B, not a runnable controller, source acceptance,
execution admission or PG result. No product/JPA/fixture change or new harness is warranted.
I authored neither this packet nor its reviewed controller. Preserve that independence for
any subsequent actual-delta review; the primary implements and binds the derivative.

## Exact binding and passive checks

Workspace = `/root/projects/Kira/`. P =
`review/working/app-29-ordinary-connected-pg-preparation-01/`.

| P file | SHA-256 |
|---|---|
| `SEAL.sha256` | `8b6c440a43568a787b7e3279264283b02a37db3f2f333c01bfc71ffc561531db` |
| `SHA256SUMS` | `62d70f6289aa82c6209eba95d38e0940b2dbc9e83aa50e82db32b9a90cd36318` |
| `README.md` | `d0664032094608162db43ed7a2688de41b1bc38f2603c4f8d9bdacb8906bc37e` |
| `recipe.json` | `8d6b4a081a868ea1b304b9b8e259c75d17d96399f9aa412b6310657ec5ef885e` |
| `selection.json` | `571c264b1f8b22e575c6fdfd7c726d9918b78b3f435d27526ed76c09e700faa9` |
| `source-transition.json` | `14c80ac290be008634cc26e3ade6b54737af05664f68c247e84dce66846291a8` |
| `inputs.sha256` | `25a09f81cc5cc46366a5e545573a589c5e2ef3fdcf9843a308897b0915841450` |

The seal's one entry, all five SHA256SUMS entries and all **57 external path/hash pairs**
in P `inputs.sha256` matched actual bytes. P is0700; its seven files are0600. This named
input manifest supplies the exact further paths/hashes below, not an unbounded workspace
attestation. Semantically read the full861-line `kira-admin/ci/app29-gate-b.py`
(`ad2d09e5dd5419ba48bc66b73ccfd502a593e88ca2362b7b277a8dfe6f759d2d`), its workflow
(`6088e8813ceafd11ade49274b12a07395cf674d39696ca1fbdb500e42f0c3ea4`), unchanged
`ci/app29_owned_children.py` (`56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385`),
PG1 profile/init, unchanged freezer and W01 init, backend build/Test configuration, all21
selected method bodies, their shared ordinary fixture, PostgreSQL fixture and owned-pool
teardown/diagnostic path. The exact lower-commit observation was also read at OwnershipIT817–899.

Source authorities:
- Target `review/working/app-29-w03-integrated-driver-ordinary-connected-03/manifest.json`:
  `171dc5c76663c7552bd064c343437bc6545394315769214354afec2295929913`.
- PG1 `review/working/app-29-w03-integrated-driver-core-c2-sqlclientinfo-pg1-01/manifest.json`:
  `2cde6562f651eb1240ba6fcc7e13d87400a993d10fa4d8b681acf2316cf2f99c`.

All478 target source hashes match current **root `kira-backend/`** bytes; all211 target and
199 PG1 snapshot hashes match. Direct JSON-map comparison confirms precisely11 replacements,
12 additions,455 unchanged and zero newly removed paths. P's23 delta rows match exactly;
the inherited removed path remains `src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/TransportBoundTestFixtures.kt`.
All348 seed **keys** remain; seed byte equality is not the rule. All102 historical pins are
unchanged. Target19 approved+8 tooling and PG1 170 approved+10 tooling form188 unique path/hash
pairs without conflicting duplicates. This is the fixed provenance union, **not** a final
future authority count. Both manifests have the same five base tools after excluding their
additional-tool lists; the proposed five deployments yield ten active tools without editing
the freezer. Current dirty/untracked target identity is documentary, not a clean-checkpoint receipt.

## Selection, containers and nonvacuous oracles

- Static literal extraction matched all21 method names **and source lines** in P selection:
  OwnershipIT15, CleanupIT6;21 distinct identities; exactly43 argv elements, equal to `test`
  plus the21 literal `--tests class.method` pairs. No parameterized/dynamic expansion is
  involved. Source pins are OwnershipIT `a1ab8749ca4bf90d03bc8716e478c5f122f3f3917b17756f02e1175868fef557`,
  CleanupIT `d95a4a06510dc7b8b63d9064c643d8e8c91b783f52203d7328f4f141d24c1167`, shared fixture
  `ce0110d46c15fefe5e152d6aa4be30d1c0539247f468c54d4cb15969db52418b`.
- Normal `test` dependencies still compile all main/test sources. Filters must not become
  source-set excludes, compile skips or a local five-class/PG1 rerun. Keep512MiB Test heap
  inherited from W01 init72–75, maxParallelForks1/forkEvery0 and always-run Test. Add the
  explicit Test system property `junit.jupiter.execution.parallel.enabled=false`.
- Both classes are PER_CLASS/SAME_THREAD with separate lazy started database fields and
  AfterAll closes (Ownership49–56; Cleanup21–28). Ordinary fixture31–55 and117–136 reuse the
  passed database for every owned/foreign EMF; they do not create a second server per method.
  Therefore successful complete selection requires **two PostgreSQL17.6-alpine and one
  Ryuk0.12.0 in one Testcontainers session**. This is a required future count, not an observation.
- Neither selected class nor ordinary fixture assigns `shutdownDiagnosticCase`; the new
  OwnedCutPool starts it null and emission returns immediately (1395,1448). PG14 scalar
  status must be **NOT_APPLICABLE / zero**, tested across both suites; retain actual pool/EMF/
  database closes and all teardown assertions. Do not lower population/identity expectations
  after an early initialization failure or infer CAPTURED from an empty record set.
- The advertised selected controls are present: calibrated selected/healthy foreign EMFs;
  true begin and retained-status faults; accepted late acquisition/RETURN tails; actual
  clipped JDBC/server caps versus separately labelled MODEL budget checks; independently
  observed active Timeout/PgSleep and accepted-lease-through-session/row-lock/receipt1..3000ms;
  exact armed lower BUSINESS commit failure before later rollback; independently durable
  afterCommit COMMITTED plus original caller interrupt; same-PID/new-epoch read-cap restoration;
  and six independent row-set/clock/lock/rollback controls. Preserve them without timing,
  fixture, retry or outcome relaxation. Their source presence is **not PG execution evidence**.

## Concrete refinements / actual-delta acceptance checklist

1. **XML ordering trap, small but real.** P `expected_xml_files` is OwnershipIT then
   CleanupIT, not lexical order. README asks to sort the observed inventory. Compare
   **sorted observed to sorted expected** (or an exact set plus cardinality), never sorted
   observed to that raw array. Keep profile's expected_tests as the exact three-field
   class/method/display_name projection. Multi-suite `diagnostics` must validate each
   suite's15/6 identities/counts, then aggregate21 unique outcomes with zero fail/error/skip;
   do not simply change the old singleton total. Preserve raw XML even if validation fails.

2. **Do not let a historical6db944 assertion become a new-tip assertion.** Controller
   `bind_freeze`275–283 currently equates the old structural checkpoint/head/bundle to the
   request,293–300 equates PG14's head to the request, and369–376 equates old C2+8+19 results
   to the new manifest. These will reject a correct W03 checkpoint, or invite an unsafe
   relaxation, if only constants/counts/selectors change. Keep those historical stages
   bound to their own immutable PG1/PG14/PG10 identities/maps/bundles. Establish the complete
   PG1 466-map first; apply exactly P's23 transition rows; require exact target478 equality,
   target211 subjects/fresh snapshots and inherited removals/history. Apply original-C2
   checks to the historical stage, not unmodified expected hashes against W03 replacements.
   Remove stale returned `snapshots:199` / `selection_source_delta_count:0` meanings.

   In `source_bundle_binding`131–163 and `sources`503–549, add exactly one new direct-parent
   stage: **new tip ->6db944 ->1c91 ->eb8fed8 ->989a ->926927 ->49da ->public prerequisite**.
   Reject6db944 itself as the new tip; retain no-merge/extra-descendant refusal, bounded
   singleton SHA1-v2 header/pack/ref/prerequisite/hash/size, public-only initial checkout,
   clean tracked-versus-actual inventory, and full before/after hashes. The old217809-byte
   bundle is historical only. Full478 is the governed source inventory, not the entire
   tracked repository inventory; measure the latter afresh rather than reuse851.

3. **Finish authority binding without a hash cycle or invented receipt.** The recipe's
   unchanged-freezer CLI matches its actual parser563–593 and collection364–445. Preserve
   the188 fixed provenance pairs, predecessor manifests/profile and accepted-review evidence;
   add the sealed packet, independent/source dispositions, actual new source checkpoint/bundle
   and final derivative. Use the real fresh clean freeze and complete issue diff; committing
   former untracked files changes diff membership even when all478 bytes stay equal. Transport
   every final manifest/snapshot/history/approved/tool/diff pin, then bind genuine local-v3
   stdout separately in the later deployed checkpoint. Do not put that later checkpoint,
   its receipt or final request back into its own manifest's inputs. No old local receipt,
   smaller inventory, copied manifest or fabricated output replaces the actual preflight.
   The recipe's13 `new_bindings` are all null and must remain so until primary evidence exists.

4. **Successor status, not sealed-history rewrite.** Linux03 is now accepted, superseding
   the packet's explicitly attributed ACTIVE-at-assignment text. Pin its actual acceptance
   in the successor; leave the sealed packet unchanged. Read/rehash bindings are:
   - `review/working/app-29-ordinary-connected-linux-03/result.json`:
     `c9787405e0fa2f75c1d006b42eb695fc4fbad7653de1393597d7de08c0472c83`;
   - `review/remediation/app-29-ordinary-connected-linux03-independent-actual-result.md`:
     `d7322dc3304c150ca5378a3a2d390928bffb7dbc7936298fd60a2fb264859caf`;
   - `review/working/app-29-ordinary-connected-linux-03/primary-acceptance.md`:
     `e1ca7e62c46e51c5b55efc1c49044f860cf4060d604132ee55e3777b5154cca3`.
   Reuse only its accepted56/56 nonDB invocations, normal compilation and fresh Ktlint;
   Detekt is bounded prior-byte-set reuse, not a fresh result. I did not re-audit its56 XML
   cases or rerun anything. PG1's accepted one case remains separate and is not rerun.

## Smallest actual edit / binding set

Under proposed fresh `review/working/app-29-ordinary-connected-pg-carrier-01/`:
1. `ci/app29-gate-b.py`: namespace/profile/selection and guard/result wording; the bounded
   source-stage changes above; fixed container population3/2/1; two-suite aggregation;
   expected classpath count21. Keep existing command owner/deadline/capture/cleanup mechanics.
2. `.github/workflows/app29-gate-b.yml`: labels, profile trigger paths, run/artifact prefix
   only. Retain private repo guard, read-only token, exact carrier/public prerequisite
   checkouts, pinned actions, Ubuntu24.04/Temurin21, shared concurrency/no cancellation,
   umask077, always-retained reports,3-day retention and missing-artifact failure.
3. `profile/profile.json`: exact21 projection/43 argv, new IDs/paths and source inventory;
   distinguish target/PG1 source-transition authority from retained historical provenance.
4. `profile/profile.init.gradle`: profile path/hash/ID/count/scope updates and explicit JUnit
   parallel=false; preserve original overlay/loader/JDK checks, ordinary compilation,
   JaCoCo/report disablement, worker heap and exact include-set checks.

The fifth deployment (`ci/app29_owned_children.py`) remains byte-identical. No freezer,
local wrapper, inventory helper, source/test/build/dependency artifact edit is required.
Separately, primary-only **actual data** must supply the clean source checkpoint/new bundle,
full fresh freeze and local receipt, accepted deployed checkpoint, final request/carrier
hashes and one-attempt admission. Do not deploy over the existing authorized PG1 request
while these remain unbound. A material source/ancestry change requires new disposition.

Retain controller556–610 custody/UUID/image/create/destroy gates and raw kill/die events;
unknown custody never permits removal. Preserve four measured drains,11 output-absence
obligations, capture-before-delete, full retained-file inventory and source/input rechecks.
Forced/nonzero cleanup, cancellation, incomplete capture or budget failure stays FAIL even
if later absence is proven. NORMAL_ABSENT is only controller-unforced absence, not graceful
PostgreSQL shutdown. Keep25min/1200s total,120s preflight/900s validation/180s cleanup,8GiB floor,
8MiB bundle bound,2GiB Gradle/512MiB metaspace, one512MiB worker; no retry/timeout enlargement.

## Limits

Only passive file/source/JSON/text/digest inspection, read-only Git status and this new report
were performed. No controller/helper import, product/tool execution, test/build/checker/freezer,
acquisition/network, Git/index/branch mutation, CI/service/process-control action or subagent.
No new executable derivative, commit, bundle, freeze, receipt or runtime artifact is asserted
by this review. Actual derivative/source/data review and primary admission remain required.
Classpath/log context is not Native05 qualification or complete transitive-byte proof.
All21 ordinary PG results remain pending; UNKNOWN database outcome is not success or retry
permission. Native05, W03/full-P3/production/native/full47/consumer/opaque/liveness/recovery and
other excluded gates remain open. Lead owns notifications and any subsequent dispatch.
