# W03 Linux03 — independent actual-result review

2026-09-13 UTC · `/root/w03_connected_ownership_review` · private0600.

**Concur: the selected five-class nonDB batch passed, with56 actual invocations, normal
main/test compilation and fresh aggregate Ktlint. No runner-versus-retained-evidence discrepancy
identified. This is NOT W03/PG1/native/full47/full-P3 or production acceptance.**

R = `review/working/app-29-ordinary-connected-linux-03/`; F =
`review/working/app-29-w03-integrated-driver-ordinary-connected-03/`, workspace-relative.
Primary reports outer session36966 reaped exit0; reviewer did not wait/reap/relaunch it.

## Result binding and exact executed tests

| Input | SHA-256 |
|---|---|
| R `result.json` | `c9787405e0fa2f75c1d006b42eb695fc4fbad7653de1393597d7de08c0472c83` |
| F `manifest.json` | `171dc5c76663c7552bd064c343437bc6545394315769214354afec2295929913` |
| R `validation.log` | `ec4fa0b467bfbb4f1626d3bdbb4f97b4de3990421818fc6e96166f60268a0c57` |
| R `input.patch` / F `issue-baseline.patch` | `d1611039f10b12263b2de9066cbc6f66256fcfd8907c53677924a97eb4a4ee5a` |

Exactly five XML files exist under R `reports/test-results/test/`, each named
`TEST-me.manga.kira.backend.common.infrastructure.persistence.<Class>.xml`:

| Class | Actual passed cases | XML SHA-256 |
|---|---:|---|
| `PersistenceJdbcTransactionTest` | 7 | `573290c1c309b22eb69e7be8f31c0e0e8560c7e88953e08d380d7719f4d91869` |
| `PersistenceJdbcGuardProtocolTest` | 11 | `53417a3684395563dbce0153984803f91f12c275e25dc1aaa2a942dcdd10c8d0` |
| `PhysicalJdbcFacadeTest` | 11 | `1df2bab7b7b2614c5bb3ecb6312e75fd84f1ba05b9c0fb834a64a52114f5eecf` |
| `PersistenceOwnershipTest` | 8 | `f644b1ace56f52775b5732d1d0fc695f4c13c7dc5765af4cc41e25baf9ccfecd` |
| `PoolLifecycleTest` | 19 | `082c90bacb514680969291a2e761edf493ea7100e2193920e854f38e87f26d8f` |
| **Total** | **56** | **0 failures, 0 errors, 0 skipped** |

Independently parsed every testcase:56 unique class/name identities, no failure/error/skipped
child nodes, exact equality with `result.test_evidence.identities`, and no unselected class.
Suite timestamps fall inside this validation command. Source declarations in the five pinned
files account for49 methods expanding to56 cases through their six `@ValueSource` methods;
parameter values/counts match the XML. This is execution evidence, not the earlier annotation
count. The seven pure transaction-outcome tests now have passing execution credit, not proof
of real Spring/JPA/PostgreSQL commit behavior.

## Compile/static observations and retained failures

- Actual command requests exactly the frozen five whole-class selectors, `ktlintCheck` and
  `--continue`, offline, one worker, no build/configuration cache. Log shows `compileKotlin`
  and `compileTestKotlin` executing without UP-TO-DATE/FROM-CACHE substitution, followed by
  `test`, JaCoCo and all script/main/test Ktlint tasks. BUILD SUCCESSFUL,14 actionable tasks
  executed; validation command joined exit0. NO-SOURCE Java compilation and skipped jar/
  configuration-error probe are not failed Kotlin compilations.
- The three exact Ktlint receipts at R `reports/reports/ktlint/` are
  `ktlintKotlinScriptCheck/ktlintKotlinScriptCheck.txt`,
  `ktlintMainSourceSetCheck/ktlintMainSourceSetCheck.txt`, and
  `ktlintTestSourceSetCheck/ktlintTestSourceSetCheck.txt`; all are empty and hash to
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- **Detekt was not run in Linux03:** no task, retained report or Detekt coverage claim exists.
  Reuse remains exactly the approved two-test-file type/layout delta in independent note
  `ba5b6ec6c268dda62230abb6530ca581faef1428560d482d13a28b67dcbb45dc` and primary selection
  `683291612d4c4b6312201aa312f3a76d40745cfb45be260a273f742bae95c7ce`.
  Linux02→03 frozen source differs only at those two files; all476 other paths and all eight
  tooling pins match. Rehashed Linux02's three successful Detekt reports. This is prior-byte-set
  evidence, **not a fresh Detekt PASS for the changed test bytes**.
- Linux01 result `44ae613363dbbe9bd11e5873c1da14f565ba717bbcb7ef08b24c118c773e3bb3`
  remains the main-compile/static failure; Linux02 result
  `5cc6b123fa3f88ce8adba7e1a67873ba67f07334c7f494dd374059fa8a6b3fac` remains the
  test-compile/test-Ktlint failure. Both executed zero tests. Linux03 does not rewrite those
  failures into historical test passes or describe them as previously failing JUnit cases.

## Frozen inputs and owned cleanup

Independent passive rehashes found **no mismatch/missing file** in all478 current backend
source paths,211 frozen snapshots,19 approved inputs,8 validation-tooling entries,102 historical
input entries, the two referenced seed/previous manifests, all9 retained reports and11 retained
classfiles. The18 local dependency files and their manifest, plus recorded JDK java/modules
hashes, also match. These are the exact enumerations in pinned F `manifest.json` and R
`result.json`, not a whole-workspace/ancestry or full-transitive-dependency attestation.
The source-engine/contract hashes in all three actual classpath receipts match the local pins.
The issue patch omits untracked bytes by its declared scope; separate source hashes/snapshots
bind those bytes. No discrepancy is inferred from that tracked-diff limitation.

All six recorded commands joined exit0. Both stop logs say no Gradle daemons are running
(shared SHA `9bb9c19238f3fdde3213f2be84912b0c7e87b3e2295ec372ec245deab200d46d`).
Five retained barriers, generations1–5, returned normally: absent=true, forced=false, no
signals/errors, including absence **before output deletion** and the unconditional final cut.
Owned groups after stop/cleanup/final postflight are empty; child-subreaper setting restored0.
The `observed` S/R/Z records are historical acquisition identities, not surviving workers.
R `jps-after.log` contains only its own Jps process; SHA
`4d6f34b5e31d221a38db34cc0f7b38225f895c5cb2d9907e3656a516bca3151e`.

At review time, passive filesystem checks also found all three declared output paths absent
and not symlinks: `.kira-validation/backend-linux/backend-build`, `kira-backend/build`,
`kira-backend/buildSrc/build`. Only the first is listed as deleted by this run. All seven
recorded parent/command identities (31029,31107,32408,32528,32560,32677,32678) were absent
from `/proc`; no stop/signal or unrelated-process search was performed. Together with the
retained descendant/group barriers, no owned-worker remainder is evidenced. This says nothing
about unrelated later jobs; no host-wide no-Java claim is made.

## Inspected files/checks and limits

Read/parsed R result, validation, both stop, empty git-diff-check and Jps logs; all five XML
suites; the three Ktlint receipts; F manifest; the named primary/reuse decisions; and the five
selected source files' declarations/parameterization. Also rehashed R `input.patch`, JaCoCo
XML, all11 classfiles and `inspect-retained-bytecode.log` (SHA
`f6d031229a0c70fd41623b0432975797984f62438dace2d52eea1f2a94c34d31`) without a new bytecode
semantics audit. `PgRequireErrorHandlerTest.class` is compile evidence only, **not a sixth
executed suite**. Inventory hashing above specifies every further file checked by exact pinned
map membership. No helper was imported, validator/build/test/static tool rerun, Git command,
service, acquisition, network operation or product edit performed; only this report is written.

No full protected-baseline oracle audit or wider47-class credit is added. The21 connected
real-database methods, PG1/native/opaque/liveness, ordinary real failed-commit/PgSleep/interrupt/
same-session restoration gates, W05 expiry/incident handling and full W03/P3 acceptance remain
open. Runtime authority remains UNKNOWN; W06 excluded. Private ancestry/evidence must not be
publicly published. Primary owns subsequent admission and notification decisions.
