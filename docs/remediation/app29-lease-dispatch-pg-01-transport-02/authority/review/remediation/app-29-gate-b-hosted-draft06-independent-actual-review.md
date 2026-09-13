# App29 Core C2 draft06 — independent bounded source/binding review

2026-09-12 UTC · `/root/backend_05_history_hosted_review` · **NONAUTHOR**.

**CONCUR — source/binding proposal only; no material technical finding.** One
nonblocking author-attribution wording correction is recorded below. This is not
source-import, checkpoint, sensitive-staging, execution or retry authorization,
actual carrier acceptance, Core47 PASS, or packaged-JAR qualification.

## Exact reviewed packet

**P** = `review/working/app-29-gate-b-hosted-draft-06/`.
Verified the supplied `P/SHA256SUMS` seal:
`96185a8bbe6fafd42efac10d4f3f380ee07643e8fd542aaeabfa78b5c9d24f0f`.
It closes exactly26 regular files:25 listed members plus the seal, with no extra
member/link; files0600 and directories0700. Every listed SHA matches. The seal
is the exact full member/hash ledger, including retained before-images and
preservation records; those records were not rewritten.

Independently regenerated the complete seven-file unified diff from the actual
before/after bytes: exact match, **+138/−68**,31645 bytes. All six draft05 context
before-images match their originals; the seventh matches the current Backend test.

| Operative after-image, relative to P | +/− | SHA-256 |
|---|---:|---|
| `ci/app29-gate-b.py` | 65/26 | `d6d35bdfdf7c3c5914281992c68b14562dbdc5eb5f7b72724cdb2da8244209a4` |
| `.github/workflows/app29-gate-b.yml` | 5/5 | `850ee781bb7ad3dfdd8532a294bc08b3840c2fa2b4fe4b0d842058aaa8a71e2c` |
| `ci/app29-gate-b.request.json` | 8/8 | `1b023ff8ec9dec853a3b22627c212773c3201e1ad7cfcfc38484079884f12c68` |
| `profile/profile.json` | 46/15 | `e54bd9d407f7add0275c245ac6eea6e82921ff3291f264447693762d37c372df` |
| `profile/profile.init.gradle` | 7/7 | `4b1771bdb1e175691e845cda1d17c7773e90687f70bcbd687c91776a549323dc` |
| `review/checkpoint.template.json` | 5/5 | `8080f0319b94de09724a7442b8480bef6943958a7eebd575bc07e222e951f853` |
| `proposed-source/src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PersistencePgOwnedCutIntegrationTest.kt` | 2/2 | `a92f7a1bc152576c0bc2cd55d3dea49614ca073aea3868c2929e5bf1fea48017` |

| Supporting source/data record, relative to P | SHA-256 |
|---|---|
| `AUTHOR_REPORT.md` | `f978f994cc86d986ba639ab23fd2075e69b1eb2af241913488020264c2f46638` |
| `PRIMARY_PREREQUISITES.md` | `950c5df6e47f987bcd4c81187fef5ef71db869e57ec922672d846fc26e2ac1e2` |
| `README.md` | `7d82ad113dc676d279e575dea078d273afd36543ed5658ebcaf1800777967572` |
| `review/draft05-to-draft06.patch` | `4456803e0208fe309c0a9093b8707c4eb4c7cefef9ff13b3de3603d44c7b9e22` |
| `review/provenance-only-source.patch` | `91f67f5429b3411e8d18160e63d88a442532f4d6e6d07ffb056f8a46aaaf79f8` |
| `review/proposed-source-inventory.json` | `13ee0d542d571fda953c80dd1a5361ab791ee0dd07f5ab0a90987766206be461` |
| `review/freeze-prerequisites.json` | `150f38db338fe2671fc781adf4519f099e5e582fa3a4a03b975fc50f24afbec3` |
| `review/source-inspection.json` | `3328d9f75e1e8c9330c3b72a246ce6153562cbccfae4670b5d027e95f5c88acb` |
| `tests/test_failed_capture_cleanup.py` | `0437ff7cf1327b890509b7934d76b7b3e05e532cfd1f70624020c5355de41689` |

## Bounded findings

1. **The Backend proposal is exactly two provenance literals.** Full-file
   substitution reconstructs the117662-byte after-image from current test SHA
   `d6dea7bad3160f0fcece9afc6d1508a8032e42a423f23ccf5ad30b62925de796`:
   profile03 becomes profile04, and JARa415 becomes
   `50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`.
   Each old/new literal occurs once. The dedicated +2/−2 patch also regenerates
   exactly. No test body/name/assertion or provider compatibility scalar changes.
   Independent textual selection matches exactly16+31 distinct profile methods;
   this is not runtime discovery. Both witness definitions, class sets, Checker,
   removed-stock, original init, JDK and task fields equal profile03. The entire
   init reverses to its predecessor using only identity/path/hash/comment labels.

2. **Full source continuity is enforced, not approximated by counts.** The pinned
   current manifest
   `review/working/app-29-w03-integrated-driver-core-c2-hosted-01/manifest.json`
   is SHA `7722db657ae06cfbc8a0dfa90975b9e355660653c157c940fabe66e9720ad6c1`.
   Fresh read-only hashes matched all466 current declared Backend sources and all199
   existing snapshots; the sole removed path remains absent. Proposal data equals
   that exact466-key map with465 unchanged hashes and only the test replacement;
   all348 seed identities are included, not348 additional sources. Its199 snapshot
   subjects are identical, with exact proposed hashes under fresh02 paths.

   `bind_freeze`218–317 requires these equalities, the unchanged102 historical-input
   map, all21 original approved inputs, the original21-source C2 binding, and exact
   default5+deployed5 tooling. The original C2 test SHA2be remains separate from
   currentd6 and proposeda92. Recipe hashes/sizes matched all44 known approved
   inputs; all21 original approved pins are retained and the ten Native05 evidence
   pins agree. These are integrity checks, not another whole-source/native audit.

3. **The private chain is tightened correctly without moving its original base.**
   `CORE_BASELINE` remains49da for the original C2 authority;
   `PRIVATE_PARENT` becomes926927. `sources`437–467 reads raw headers with
   `--no-replace-objects` and requires each sole immediate parent:

   ```text
   ACTUAL_NEW_PRIVATE_TIP
     -> 926927ab805a2a3b78957862f3b744d0fe399ac5
       -> 49da0919d9ec3091cb7bb041009dc9bd5f3e090f
         -> 3d839130c807f6a0a9b1c896c1c6cca4b41c4538 (public prerequisite)
   ```

   Read-only local headers corroborate the existing last two arrows; Backend was
   clean on926927/the recorded issue branch. No new tip exists in this proposal.
   The request rejects using any fixed ancestor as the new tip. Import mechanics
   remain byte-identical: clean detached public prerequisite, bounded complete
   SHA1-v2 singleton bundle, verified local-file transport and exact branch checkout.
   Original private bundle80cb remains197481 bytes, SHA
   `80cb7bdd3be021bed65b67b1890913192d7c06baf9c725865727c9e02c452fe7`.
   None of this authorizes publishing926927, its descendants, private source/history,
   vendor content or candidate JAR to public Backend/public CI.

4. **The primary prerequisite model is acyclic and still unbound.** Reviewed the
   fixed freezer source at `review/working/freeze_app29_integrated_driver_v3.py`,
   SHA `e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`,
   without importing/executing it. The documented order is feasible:
   source/bundle/review/tools → manifest → genuine local-v3 receipt → accepted
   checkpoint → bound request → carrier/staging receipt. The new generated
   manifest/receipt/checkpoint/request are excluded as inputs to their own freeze;
   immutable historical manifests are legitimate earlier inputs. The recipe's44
   known inputs, two pending primary inputs and missing actual-review entry do
   not invent authority. The pending02 bundle/receipt and new manifest were absent.

   All five actual `DEPLOYMENTS` origins/destinations match request/recipe hashes:
   controller/workflow and both profile files now originate in draft06; owner helper
   stays unchanged at SHA56b66cfe. No draft04 executable is hidden under a new pin.
   Request `authorized:false`, checkpoint `source_accepted:false`, future tip/hash/
   size fields unbound: flipping authorization alone cannot satisfy admission.
   Workflow private-repository guard, actions, resources, serialization and steps
   remain; budgets stay25m/1200s/120s/900s/180s and attempts1. Primary still owns
   actual one-file staged diff, checkpoint/bundle verification, fresh freeze, closed
   authority union, sensitive staging and subsequent actual binding review.

5. **Consumer and custody predicates are preserved.** AST/text comparison finds
   all28 existing declarations,22 byte-identical; only `source_bundle_binding`,
   `request`, `bind_freeze`, `Gate.__init__`, `Gate.sources` and `execute` change.
   `consumer`, capture, diagnostics, owner/command/drain/container functions and
   the entire cleanup-through-final-PASS section are byte-identical. Runtime scope
   remains exactly47 passing unskipped identities, two CREATE_NEW witnesses from
   one actual PID/JDK/positive loader, actual class-source association, one pinned
   supplier/stock removal, twoPG17.6+oneRyuk0.12.0 and11 owned cleanup paths.
   Old profile03 diagnostic strings are fixed labels, not fallback predicates.
   Capture-complete/test-failure may allow cleanup but never PASS; nonzero/forced/
   unknown outcomes stay sticky, with no outer exit23 waiver or retry expansion.

6. **Provenance wording note, not a fabricated security failure.**
   `AUTHOR_REPORT.md:3` incorrectly names `/root/backend_04_engine_product` as
   author. Primary identifies Admin01 as the actual preparer. Record that correction
   in primary collection/an external erratum; do not silently rewrite the sealed
   packet or imply Backend04 authored/reviewed it. This misattribution does not
   change the verified bytes or supply missing execution authority.

## Reused evidence and unrun gates

These existing references were checked/read only for their narrower scope; their
raw historical result audits were not repeated:

| Existing reference | SHA-256 |
|---|---|
| `review/remediation/app-29-gate-b-hosted-draft05-independent-actual-review.md` | `1986c0caeeb262bf268179065c081858a6c1b694c7257e568a6201d9ed5334c6` |
| `review/working/app-29-gate-b-cleanup-unit-01/result.json` | `eb7ead753cd02324105b297d5ecc5743cf3ab42a5b7c3c7ecff12f581b24d6b5` |
| `review/remediation/app-29-native05-independent-result-review.md` | `7fc76ba1751a3db51f268449457be8ae1140711e31f1e92874facef637d5cb1c` |
| `review/working/app-29-driver-cut-native-build-05/result.json` | `93663b4ab678b90d8e4680ec9e1a10313cbdd9d6d596f2c289accd0b35296c06` |

Cleanup **PASS_ISOLATED4** covers synthetic capture/guard/file disposition only;
its copied test remains byte-identical and was not rerun. Native05 **getter3 plus
one build** used the SHADOWED project variant, not the separately packaged OSGi
JAR. The actual original Native05 JAR hash/1200036-byte size matches profile04;
this is integrity, not consumer/ABI qualification. No Backend vendor replacement
is proposed. Native05 does not prove every prior Core failure solved.

Still unrun/unaccepted here: source import/new private commit and bundle; genuine
full-v3 freeze and199 newly emitted snapshots; genuinely invoked local preflight
bound to the actual manifest SHA (never copied because receipt bytes coincide);
actual private-carrier staging/inventory review and one-attempt admission; Core47
execution with both witnesses/provenance and normal complete capture/custody/output
cleanup. Candidate remains **UNQUALIFIED**, **D05 PARTIAL / D06 unreviewed** and
W03/native/ABI/full qualification/release remain open. Historical hosted
run34639408970 remains20 PASS/27 FAIL with capture_complete=false and
outputs_absent=false; normal child/container absence is separate.

This review used only local reads/hashes/JSON/text/AST metadata and read-only Git
inspection. No target import/evaluation, runner/freezer/test/build/checker execution,
network/CI, service action, Git mutation, source/carrier/history edit or retry.
Only this separate report was written. No owned temporary workers remain. The
packet's2011-file preservation audit was retained, not replicated or promoted to
a whole-worktree audit. Primary retains all integration and operational decisions.
