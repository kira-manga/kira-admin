# App29 native05 — independent actual-result review

2026-09-12T00:55:42.156702+00:00 · `/root/backend_03_native_result_review` · **NONAUTHOR**.

**ACCEPT the actual three-test getter regression and one candidate-build evidence,
within this selection only. No material blocker found in that evidence.**
The candidate remains **UNQUALIFIED**; this is not native-suite, Core47, ABI,
packaged-runtime, shipping, or publication approval. Primary owns subsequent
candidate/provenance acceptance and any separately admitted Core execution.

Reviewed only after primary reported session36611 complete/exit0 and the retained
result had finished. I did not author the getter/tests/runner and did not import or
execute candidate/runner/helper code, compile, rerun tests, launch/stop a service,
run javap, change source/history/tracker, dispatch CI, or publish anything.
Read-only file/hash/XML/ZIP-data/proc observations are not a replay.

## Bound inputs and actual outcome

All paths below are private workspace-relative paths. **E** =
`review/working/app-29-driver-cut-native-build-05/`; **P** =
`review/working/app-29-driver-cut-native-build-05-preparation/`; **S** =
`review/working/app-29-core-c2-isolation-getter-source-01/`; **U** =
`.kira-validation/pgjdbc-owned-cut/upstream/`.

| Reviewed input | SHA-256 |
|---|---|
| `review/remediation/app-29-native05-primary-admission.json` | `f52566b9899c49999326e43d8d68346abd7f35bd5bd7f584e939b4c1e7e39d00` |
| `review/working/run_app29_native_build05.py` | `2203ee5cf0334958b8b685966b80a4c849ecf32805b3c2530b2037c7e54ca8d5` |
| `review/working/app29_linux_owned_processes.py` | `ac6fb4b61186c09ab06f9b4a543cb58e65dcbcdfe6ba405f6afbe1814b7fc455` |
| P/admission-manifest.json | `32f1b6d64e43efae8997df2285f27d5221a1f3e084d699ec14e835dd962b29bc` |
| P/rerun-proposal.json | `0e48429f3c694126a37d38f2067f6b33ac41f575b34901ac692dd6f19e3eaf1b` |
| S/SEAL.sha256 | `529c90aea9e37bbf54ed9a51cab698c877b8297c4f18b7a8427fae1ad5d5755a` |
| S/source-delta.patch | `5be5cd1adb568dc796a01f7756b070cc7fead7c64d99ee925c12530ab8e772ae` |
| `review/remediation/app-29-core-c2-isolation-getter-independent-review.md` | `4f6b03f4167b12894eac04a41f67609c292803cb7c68a5c3e0ddbd260af34b9a` |
| E/result.json | `93663b4ab678b90d8e4680ec9e1a10313cbdd9d6d596f2c289accd0b35296c06` |

The actual command and recorded command agree byte-for-byte as argv data: one
`:postgresql:osgiJar` and one `:pgjdbc-mockito-test:test`, restricted by exactly the
three admitted selectors. No old73, old10, full Fault class, other native test,
Core, publication, or javap task ran. Normal compilation/build-logic prerequisites
are not additional test selection. The log records fresh `compileJava`,
`compileTestJava`, `shadowJar`, `osgiJar`, and the selected test task—not cached test
results—and **BUILD SUCCESSFUL**, **83 actionable tasks:83 executed**. The graph
ran 00:44:44.441553–00:47:14.430314 UTC; final result finished
00:47:17.717683 UTC. Graph exit0, no timeout, runner/evidence error types null.

I independently parsed the only retained `TEST-*.xml`, rather than trusting the
observer's `matches_expected` boolean. Its suite is exactly
`org.postgresql.jdbc.KiraOwnedJdbcCutFaultTest`; declared and actual counts are
**3 tests,0 failures,0 errors,0 skipped**, with no failure/error/skipped elements,
no duplicate/substituted names, and matching classname on every testcase:

| Actual XML testcase | Result / seconds |
|---|---|
| `isolationGetterExecuteFailureClosesItsStatementAndPreservesTheException()` | PASS /0.698 |
| `isolationGetterRepeatedSuccessClosesBothResourcesWithoutBeginningATransaction()` | PASS /0.037 |
| `isolationGetterReadFailureClosesBothResourcesAndPreservesTheException()` | PASS /0.021 |

XML timestamp is 00:47:13.072Z; suite time0.774s. Copied XML, xml-summary,
testcase-inventory and selected-tests-observed agree. No broader count is inferred.

## What these passing assertions establish

The exact getter patch reconstructs byte-for-byte from frozen before/after files
using GNU unified diff. Source tracing was performed before result review, not
backfilled from PASS:

- `U/pgjdbc/src/main/java/org/postgresql/jdbc/PgConnection.java:1080–1128`
  creates/owns the parent before execution, preserves SHOW/QUERY_SUPPRESS_BEGIN,
  update/result traversal, NO_DATA, warning transfer and isolation mapping; inner
  ResultSet TWR closes before outer Statement TWR. Shared execSQLQuery is unchanged.
- `U/pgjdbc-mockito-test/src/test/java/org/postgresql/jdbc/KiraOwnedJdbcCutFaultTest.java:69–185,914–965,981–1105`
  uses real Driver.connect/PgConnection/PgStatement/PgResultSet and only substitutes
  the lower QueryExecutor. `liveNativeLife` captures unique, actual factory-returned,
  first-never Lives, not synthetic closure receipts. The original executor is
  restored before every retained-state assertion, and assertions precede fixture
  retirement. Existing Owned/delegate/ExecutorFault bodies are unchanged.
- Success really traverses the getter twice, with REPEATABLE_READ and autocommit=false;
  IDLE holds before/after and the execute flags retain QUERY_SUPPRESS_BEGIN. Both
  real first-close states are2 and native children/retention are0. Warning identity
  survives actual parent close. The warning is injected through the genuine
  StatementResultHandler, not evidence of a server-generated notice.
- Execute failure asserts one actual parent and no result at injection, exact
  original SQLException identity, no suppressed exception, successful first parent
  close and zero invocation/children/retention states. Read failure delegates real
  execution/result creation first, then injects at getEncoding with both Lives still
  first-never; one injection, the same exception, and both successful first closes
  are required. Source tracing from PgResultSet.getString2505 to PgConnection1242–1243
  binds that configured read extent; XML is outcome evidence, not per-assertion trace.
- `PgStatement.java:195–210,256–273,403–425,742–758`,
  `PgResultSet.java:2324–2400,2505–2512`, and `KiraOwnedJdbcCut.java:352–399,723–724,1242–1273`
  explain result factory/warning handling, first-close bookkeeping and the real
  state oracles. A repeated parent-induced result close cannot manufacture another
  successful first-close receipt. Native retention predicates were not changed.

### Full source and input equality

I freshly hashed **all1018 current source-tree files**, checked the exact complete
file pathset with no generated roots or `.git`, and compared them with E/before,
E/after, S/upstream-after and the complete native04 map with only the admitted two
replacements. All maps agree; other1016 files match native04. The two live files
equal the frozen after-images:

| U-relative source | SHA-256 |
|---|---|
| `pgjdbc/src/main/java/org/postgresql/jdbc/PgConnection.java` | `486aba8d77f3a38b9b0b16540bf7f62010c438803bf4cc426e05bbb5c3528114` |
| `pgjdbc-mockito-test/src/test/java/org/postgresql/jdbc/KiraOwnedJdbcCutFaultTest.java` | `d8f8ba511272279f05c785beac89238836cb96f1bb374bcff17a73bbabb0242b` |

All17 E/execution-inputs members equal their bound working/historical originals;
all9 E/build-inputs files equal current pinned source bytes. I read the Mockito
SHADOWED project dependency and OSGi-from-shadowJar wiring, shared test-base/JUnit5
property forwarding, and TestUtil property priority/real connection path. The new
three tests contain no assumption/skip substitution. This is complete source
**integrity**, not a semantic re-audit of every unchanged file.

All38 admission read-only references and both identical75-pin preservation lists
verified, including after actual completion. Source and preparation seals have
exact matching member pathsets. **Documentation correction only:** Source01 has
**17 sealed members/18 files including its seal**, not the source review's18/19
or preparation report's19 total. No member is missing relative to the actual seal;
no historical report/receipt was edited to fix that count.

## Newly observed private candidate — not qualification

Candidate ID: `app-29-driver-cut-native-build-05-isolation-getter-source-01`.

- Exact path: E/artifacts/postgresql-42.7.12-kira.1-osgi.jar
- Size: **1,200,036 bytes**
- SHA-256: **`50f7dc4a6314cc5105f4990be26ba8be65ae242e1f7e62652cc60d6a2c0e03df`**
- Recomputed all**520 non-directory entry hashes/sizes** directly from the ZIP;
  they exactly equal E/jar-entry-inventory.json, with unique file-entry names.
- Compared against preserved native03 a415: identical file-entry pathset,
  **517 byte-identical entries; only the following three entries differ**.
  These are byte comparisons, not decompilation or a claim about why bytes changed.

| Changed entry | New SHA-256 |
|---|---|
| `org/postgresql/jdbc/PgConnection.class` | `d36ba6505a678816f779208cf040f1d8ad953a040a700eb31b6debcf2f458f11` |
| `org/postgresql/jdbc/PgConnection$AbortCommand.class` | `9fbf6538aa8a270727338e7e37b0be4a100048c45d84d32045fe39b773500931` |
| `org/postgresql/jdbc/PgConnection$TransactionCommandHandler.class` | `ddc2a45cb51482b942d24a3c9bed83cf583d3a79662c0dabb79928efe35d8180` |

The manifest, JDBC service entry, Driver, KiraOwnedJdbcCut, PgStatement and PgResultSet
entries are among the517 identical entries. Same build-version string does not
identify the new candidate: bind its new private path **and exact hash**, never a415.
The tests consume the SHADOWED project variant, not the separately packaged OSGi JAR.
No compiled-getter/exception-table/loader/ABI or final-JAR runtime proof is claimed;
`artifact_method23` remains null and the staged artifact remains `qualified:false`.

Old candidate a415 is independently unchanged at1,199,855 bytes and
`a4150232fa8f30797ae67091e65417da4e8d26c98610a1bac541d953ad6403d3`.
Backend is clean at private source commit
`926927ab805a2a3b78957862f3b744d0fe399ac5`; all11 live vendor files equal the captured
and frozen expected inventory. Neither vendor nor Backend dependency contents
were replaced. Source926927/vendor/JAR remain PRIVATE, not public CI inputs or
published artifacts. E and its artifact directory are0700; the candidate is0600.

## Genuine database, admitted bounds and owned cleanup

The psql witness JSON/log, PostgreSQL version/startup/shutdown logs and actual
Gradle DB properties agree on the one private loopback primary:
PostgreSQL**17.6 /170006**, no recovery, address127.0.0.1, port32857,
UID1000, database/user `kira_native`, SCRAM role and `scram-sha-256` auth.
Cluster `/tmp/kira-native-build05-v7yc3fa5` came from the retained exact PG02 prefix.
JDK log/release identify**21.0.12**; wrapper is**9.4.1**. The current captured
JDK309/PG725/Gradle-distribution642/dependency648 file inventories equal their
admitted historical manifests as dictionaries; I did not label that comparison a
fresh rehash of those entire live toolchain/cache directories.

Actual argv retains offline/no parallel/one worker/no build or configuration cache,
no scan/toolchain acquisition, Gradle2GiB heap/768MiB metaspace, Java8 target and
JUnit nonparallelism; source test configuration gives1536MiB test heap. PG config
sets max_connections35/shared_buffers64MB and loopback-only listening. This is
Ubuntu/glibc, **not Alpine**. Offline flags are **not** an OS network sandbox.
The1200s bound is on the graph, not the whole runner; the inherited lock wait is
untimed and setup/stop phases have their separate bounds.

All16 recorded resource samples stay above the8GiB root/tmp/available-memory
floors. Recorded minima in bytes: root**9,678,454,784**, tmp**33,628,033,024**,
available memory**62,771,654,656**. Largest sampled owned RSS is**2,271,260,672**
bytes. These are sampled observations, not a bound on unsampled peaks.

I inspected the actual ownership helper and runner cleanup ordering: immediate
Gradle stop, PG fast stop, joined handles and owned absence precede mutable capture;
fresh absence barriers precede disposal/cache reads and final restoration.
Unknown absence refuses mutable capture/deletion; forced/error cleanup cannot pass.
Actual receipts show:

- Both Gradle stops and PG fast stop exit0; shutdown logs agree. The single-use
  Gradle daemon reports normal runtime exit0 before the first explicit stop.
- Four generations of barriers: absent=true, forced=false, signals/reaped/errors
  empty; subreaper restored to its previous0 and active=false.
- Independent stat-only readback at **00:50:57.763859Z**: all**16 recorded process
  identities** absent (no reused/live same identity), all**16 removed paths** absent;
  no upstream build/.gradle/.kotlin directory; run-specific HOME/project/Kotlin
  cache, secret properties, cluster and owned daemon logs absent. `/proc/net/tcp*`
  shows no listener on the former32857 port. Retained runtime/cache directories
  remain present. I sent no signal and started no network/service probe.

The logs are not literally error-free. Retained nonfatal diagnostics include the
optional build.local.properties notice (explicit system DB properties take
priority), unchecked/deprecation/Gradle10/CDS/Kotlin-session warnings, and a daemon
shutdown-hook registry `IllegalStateException` **after** successful build/exit0.
Both explicit stops, four normal barriers and the independent absence readback
support normal cleanup; that hook diagnostic is not hidden or relabeled a test
failure. PG logical-replication-worker exit1 appears during its logged fast shutdown,
not as a failed test or forced ownership signal.

## Remaining limits / no inherited credit

- Three passes establish only these configured getter success/execute/read extents.
  No new compound-close-failure matrix, NO_DATA or null/unknown/default isolation
  mapping execution is claimed; preserved logic and Java TWR semantics are not
  additional runtime cases.
- Native03 remains historical**72 passed/1 failed**; native04 remains its separate
  **10 passed** helper batch. Neither was replayed or absorbed into native05.
- Hosted Core47 remains historical**20 passed/27 failed**. Cold Hikari checkout,
  reuse/RETURN/TL, hidden-Array refusal, TypeInfo positive paths and the47 preserved
  Core assertions were not executed here. The getter being fixed does not establish
  it was the only cause of those27 failures. Any Core retry needs exact fresh
  candidate/provenance bindings and separate primary admission.
- All348 historical source-seed requirements and remaining Native/Core/P3/ABI/W03/
  App29 gates remain open: native-finalizer interiors, pin/compaction, successful
  wire cancellation, shipping destructive-cut/exception-table/initialization,
  packaged runtime/OSGi/service/SCRAM/one-driver/unshaded dependencies/private POM,
  connected consumers and custody/retention limits. W06 remains excluded;
  NEW-data/installation recovery boundaries are unchanged.

Only this new0600 report was written beneath private0700 review directories.
No source, sealed packet, historical evidence or Git worktree was changed by me.

## Exact retained files reviewed

The input table, explicitly named source contexts, all1018-entry source maps,
complete17-member execution-input set and9-file build-input set above define the
input boundary. The following E-relative files were directly parsed/read or
integrity-compared for this result (archive SHA is separately bound above).
No HTML renderer or binary-results parser was used; copied HTML/binary companions
are not independent pass evidence.

| E-relative file | SHA-256 |
|---|---|
| `actual-command.json` | `6f487eba166a0e493c4904319a359e5c477272b8b58d0f1a5268bec5962ec1f8` |
| `gradle.log` | `24ba640d581c085ba5584464162abbbb205637c6ad88d4791df633216ca0b3c5` |
| `pgjdbc-mockito-test/test-results/test/TEST-org.postgresql.jdbc.KiraOwnedJdbcCutFaultTest.xml` | `8937dea1655e52876f7994168d7fac7b3de06c4598bbbe0b8236c58b8f5149d8` |
| `xml-summary.json` | `7b0a2ab7d36a3ae8dc674307cdb2d9b62a6050cb1e0e23bff0a0d779602ec8e4` |
| `testcase-inventory.json` | `a24d28a779c449b2ac2634cce79ee7183d7cbd4c670e2fd9c8e64128a882172f` |
| `selected-tests-observed.json` | `7a05ee738532367bdd5bb082e5dd3420a34d2eabf4244aa6480f774eef1912b2` |
| `expected-selected-tests.json` | `7d55c3ecc76c468d57600d3dbe685fa38dab9098119c4405095956fcd472c61e` |
| `database-witness.json` | `d13cc02865a2c5240b27dfdaa3fec3187aa225c3caa1ed845108e6ebbb018e80` |
| `database-witness.log` | `0350fa8f3825cfb609221e7d1df966f3979f7465ff0296b7d716c8f7c95df3d6` |
| `environment.json` | `18b033a6aa96ec509b828c7552f35f0c9fe3978f341ea63d34c5d2ed466fa102` |
| `java-version.log` | `4ddd49e5058130107f252eea6f03fa4dd2eb39ccbfe1d9a0176694e9624eb69c` |
| `jdk-release.txt` | `97b8b1dd371b52855704fea5875a78cf3289d06b7f51c2155c43acadb9ff6f6c` |
| `postgres-version.log` | `28ecc1592a6bd9e76ec836b15000d1acb03222a44502a478584d4d783ca4cd96` |
| `initdb.log` | `08fcaf8b3607f5812ddfa3dc786053db225c13553b37574bdedafd667cb556db` |
| `postgres.log` | `91a109fe5d3269e046d88272723457c7d51e2b7ca8ab75dd19e5eb11a9bbcb5f` |
| `pg_hba.conf` | `b061836dd7ca38cc8426c744d7e90dbb9acd83d699ead2101cf99e5abce2b620` |
| `postgresql.conf` | `f9512f2187ee3e8285541764b7745532ee3284c473e5f68cfeea01715d194b76` |
| `postgres-stop.log` | `ca19178a35ab4153b75b494963b66ce8243e1b94c173107c87b44d09db23652d` |
| `stop-immediate.log` | `9bb9c19238f3fdde3213f2be84912b0c7e87b3e2295ec372ec245deab200d46d` |
| `stop-final.log` | `9bb9c19238f3fdde3213f2be84912b0c7e87b3e2295ec372ec245deab200d46d` |
| `daemon-logs/9.4.1/daemon-19234.out.log` | `57ec95c7e709bd00791e930d273d1311b08dced3e10dec78653334fda9cbf392` |
| `resources.json` | `3a051c222c1524d2400774bd8147234d2826b772b4696a4e665ecd190d897b0a` |
| `sources-before.json` | `e3ae4b1579c4e46a7571f7d0c80fd15f9ff946d4056e0089c204a70cbac0d57e` |
| `sources-after.json` | `e3ae4b1579c4e46a7571f7d0c80fd15f9ff946d4056e0089c204a70cbac0d57e` |
| `vendor-inputs.json` | `45893288a3ca0d820b134e54c670b9a85175ea43930c9e9d8544ed3fd7a7bcbe` |
| `jdk-inputs.json` | `2c22960fa53f4121a4c173aba9ce2936270ca6e2725fa246b757b27011b4afeb` |
| `pg-prefix-inputs.json` | `56095ac4bd1c72099381efa09e9430ea8cd1c410b26968cea791a19dc7adda39` |
| `gradle-distribution-inputs.json` | `02da0d716fa7fdc439c318c281441978aca215125be91959318a1c1f4b554099` |
| `resolved-dependency-inputs.json` | `27cf5905966bf13de318ddc8a3f83183d5d20f48aed479cb888ca552d041843b` |
| `jar-entry-inventory.json` | `8a98b77220a88a63f914d39b2fc6114f1262bafc5f30ea8d4a2ade99a5bbe287` |
