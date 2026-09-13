# App29 profile03 — independent actual-diff review

2026-09-11 UTC · `/root/backend_04_independent_review` · NONAUTHOR.

**ACCEPT only the bounded source-preparation increment:** the authorized integration-test
profile/JAR literals and fixed witness plumbing, plus the new profile03 JSON/init derivative.
No blocking finding in that diff. **Not C2/Core/native acceptance, runtime qualification,
a full source freeze, controller approval, or permission to launch.**

Backend `49da0919d9ec3091cb7bb041009dc9bd5f3e090f`, branch
`remediation/app-29-backend-complaints`, remains **PRIVATE / NEVER PUBLICLY PUSH**.
Existing owner WIP and historical packets were preserved.

## Exact inspected bytes

Packet prefix: `review/working/app-29-final-jar-consumer-profile-03/`.
Test path: `kira-backend/src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PersistencePgOwnedCutIntegrationTest.kt`.

| Item | Bytes | SHA-256 |
|---|---:|---|
| Test before image | 117449 | `2be392d5768db39dce43832be3eb12d3b6d724b60d7a569f51c8be9b704aba7a` |
| Test live/after image | 117662 | `d6dea7bad3160f0fcece9afc6d1508a8032e42a423f23ccf5ad30b62925de796` |
| `profile.json` | 23734 | `ae027fc473d0c8c55665e23585b6508d59c0d803a8c76a66b694425fbc602b5b` |
| `../app-29-final-jar-consumer-profile-03.init.gradle` | 11186 | `2237206f53344001fa1697a02ce84f5a1b851f205d0029a22423d98acb49ee7b` |
| `binding-test.patch` | 4150 | `4c6a4c496c64e1e4cb2bb04a2b9a25092699942f6e456e874dbc26575e7a0024` |
| `init03.patch` | 5690 | `0a62af02cfb14e868cfe1de757130a6a6cff71d1094c3524d630a7e9c7eee57c` |
| `profile03.patch` | 24512 | `307364a9a12139feb07c0015d7bd38a2b1ad210392a7a22f3064174b3ee772e1` |
| `change-receipt.json` | 13512 | `761839c691ab24490c62766187e1e8ebe1c39249c53fabb0323e278a525b17b4` |
| `SOURCE-ONLY-HANDOFF.md` | 6781 | `8021e5e14e8c66d54bbd6c2f281d4dd7676647d90910e7717e5e57826b0749a2` |

I independently hashed these files and inputs; before/after copies and all three complete
incremental patches match the actual bytes. These compact pins are **not a full-v3 freeze**.
Comparison bases, also independently matched:

- `review/working/app-29-gate-b-hosted-draft-03/ci/app29-gate-b.init.gradle`:
  `18043383dfa80dcae0989fa6bab1a60f4ca85921383f190f7a1995a5ecbdd966`.
- Same directory, `app29-gate-b.profile.json`:
  `8ec74a1f9b79643b6bee623611e060d972755f806be53dfeaced19eaadc591b1`.
- `review/working/app-29-real-pool-return-adaptation-c2-01/source-manifest.json`:
  `e8f783786c058b39094483488a0a49045a74f81de99733a0bad00051a54d897a`.
- Same C2 directory, `test-source-inventory.json`:
  `823f49b359b8dec60d1b024c2bfd4e3d2d6822a42fed1a8c8d0e905b5ba87650`.

Of those21 C2 source paths, only this integration test differs; the other20 match.
This is **hash integrity, not a semantic rereview/approval of those20 files or C2**.
Unchanged `PhysicalJdbcDescendantsTest.kt` remains
`0997dd22f9c2ee5f36c837559a113134c0c3a59f17b4087b0746989b331407c6`.

## Bounded findings

1. **Assertions preserved.** The complete test delta contains only the two approved
   profile/JAR literal changes, the two fixed call-site tags, helper tag parameter/whitelist,
   recorded tag, fixed sibling filename and comment. Existing descriptor, actual-Class
   loader/code-source, one-provider, Checker, MR, JDK/JVM and before/after hash assertions
   remain. Historical `all22` method name still asserts23 descriptors. No test body/lifecycle,
   C2 restoration, permanent-PENDING probe, fixture or production logic was otherwise changed.

2. **Current mandatory input, no fallback.** Both provenance calls require profile03 and
   native03 JAR `a4150232fa8f30797ae67091e65417da4e8d26c98610a1bac541d953ad6403d3`
   (1199855 bytes, at the profile's native-build-03 path), still **UNQUALIFIED**. Checker
   remains `857658c8bdcbff794949a8d9922f88d63ee3751c203c7cd7d21ea97f9e745288`
   (241885 bytes, existing profile01 input). The unchanged historical
   `app-29-gate-b-hosted-01` scalar satisfies only the original-provider assertion; it cannot
   supply historical Gate B credit or substitute for the new global profile/JAR pins.

3. **Thin Test-only replacement retained.** Full init comparison preserves bound backend,
   hosted context and original local-source init
   `429961b98254b89f7ce1d7ba1efa61b8cba28a3bae35353bf3a8ba85f4a1c839`.
   Only the named Test task's classpath replaces the exactly pinned stock PostgreSQL with
   the explicit JAR/Checker; stock configurations/locks/BOM remain unchanged. Complete
   effective classpath supplier scanning, MR-aware names, one service provider, Checker
   deduplication, manifest-Class-Path refusal and uninstrumented JDK21/loader/agent/MR
   override guards remain. Jacoco report disabling remains a sibling task configuration,
   not the previously forbidden nested-provider pattern. No runner/controller is added.

4. **Exact47 declaration selection, one Test task.** Independently compared all live textual
   `@Test` names with C2 `candidate_names` and profile `expected_tests`, in order:
   **PhysicalJdbcDescendantsTest16 + PersistencePgOwnedCutIntegrationTest31**;47 unique
   identities and exact `method + "()"` expected display names. These are ordinary source
   declarations, **not discovery or executions**. Proposed vector:

   ```text
   test
   --tests me.manga.kira.backend.common.infrastructure.persistence.PhysicalJdbcDescendantsTest
   --tests me.manga.kira.backend.common.infrastructure.persistence.PersistencePgOwnedCutIntegrationTest
   ```

   Init independently checks profile identity/count/uniqueness, installs all47 exact
   programmatic method filters, and retains fail-on-no-match, maxParallelForks1/forkEvery0
   and no up-to-date shortcut. The two CLI class selectors do not widen those filters.
   No separate Test invocation, duplicate admission run or new static selector was added.

5. **Noncolliding, same-worker evidence preparation — not an observed pair.** The only
   tags are literal `required`/`original`; the helper rejects anything else. They produce
   `reports/final-jar-profile-03/worker-runtime-required.txt` and
   `reports/final-jar-profile-03/worker-runtime-original.txt`, each with the matching tag.
   `CREATE_NEW` is unchanged: duplicate same-tag invocation fails instead of overwriting.
   Both record actual ProcessHandle PID/executable/JDK and positive Class loader identity;
   helper assertions still tie Driver, test and context loader together. Required records
   Driver/helper/marker/five opaque types plus metadata/MR/SCRAM; original additionally
   records actual PgConnection. The original-provider witness must supply that association.

   **Cross-file PID/JDK/positive-loader equality is a future controller/result obligation**,
   not a new comparison implemented by this helper/init. One planned worker alone is not
   observed proof. The controller must require both fixed files/tags, the matching single
   `class-load-<pid>.txt`, effective classpath and exactly47 passing XML cases once each,
   without extras/failure/skip substitution. Witness `provenance=PASS` alone does not prove
   either test finished. Retain the existing positive `source: file:` class-load rule:
   intentional cold defineClass negatives do not justify another positive supplier.

## Remaining gates / zero execution

- Primary must create the fresh full-v3 freeze retaining **all348 seed paths plus current
  WIP**, exact successor source/artifact/private-transport bindings and fresh checkpoint.
  Historical Gate B source/freeze/evidence is not current Core authority.
- Independently review the narrow hosted-controller derivative and exact47/two-witness
  result/ownership bindings before any separately authorized attempt. The unchanged Gate B
  controller still accepts only its old one-case/one-witness profile and cannot run or
  accept this profile as-is. No controller or resource/cleanup acceptance is given here.
- Compilation, static checks, JUnit discovery, all47 C2/probe cases, packaged/native
  qualification and required full regressions remain open. Native03 remains historical
  72pass/1fail. The handoff's native04 ten-case receipt is not independently reviewed here
  and yields no new JAR or aggregate73 credit. Permanent-PENDING probe exit23 remains
  **PROCESS_ONLY / product_end=false**, not product lifecycle disposal.
- D05/D06 and DB03 raw73/83 FAIL boundaries remain; W03/P3/downstream open, W06 excluded,
  NEW-data/installation-recovery requirements preserved.

**Performed only source/data reading, hashing, text/JSON comparison and this new private
report. Zero builds/tests/static tools/formatters, project-code parser/import/execution,
JVMs/services, runner/freezer invocations, network/CI, source edits, commits or pushes.**
