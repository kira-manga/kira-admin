# App29 lease dispatch PG02 — independent actual-failure review 01

2026-09-13 UTC. NONAUTHOR reviewer: `w03_static_nonauthor_review`.
**Disposition: retain FAIL; no executed-test, PG, cleanup or qualification acceptance.**
This is a bounded failure diagnosis and correction recommendation, not a source
repair, harness redesign or authorization to repeat the run.

## Actual attempt and immutable evidence

- Private run `34774646772`, attempt 1, concluded failure; carrier
  `b6e2a2cf7c35eca56a2478a6a1973dc8b6c94428`.
- Backend source `c67ddcd30fbae2438c7b2f803f720530b598e428`, tree
  `6fd90f08e176233688927b51cfde8fad5e8f003f`.
- Evidence root:
  `review/working/app-29-lease-dispatch-pg02-admission-01/launch-01/artifacts/`.
- Independently recomputed all 46 collected file hashes/sizes against
  `collection.json`, and all 45 non-result files against the result's retained
  inventory: exact sets, no mismatch; all collected files mode0600.
- All 14 before/after pairs are byte-identical, including the 866-entry source
  hash maps, tracked inventories, clean status, branch and commit records.
  The target test, version catalog, lockfile, build script and wrapper pins also
  match their actual source-commit blobs. Source bundle/binding before and after
  agree; `inputs_preserved=true` is supported by these retained observations.

Key SHA-256 pins:

| Artifact | SHA-256 |
|---|---|
| `artifacts/result.json` | `dbd0e7635561d9d733f644d40520581b25efcfb8afb20a60d4330399d738c0df` |
| `artifacts/gradle-test.log` | `2ed3742d72a6cdd037099eb1f8b0a3332adbb54b9e1e3315b73b5300b1738b8f` |
| both `artifacts/*-source-hashes.json` | `db19d2eacd5fe8bdccf51c5ba243c438afcad92ce674abd5f51584c283528596` |
| `collection.json` | `ee1f34ed79f9c97c23bc929d9fd2e1aaff4b002a90d5a5dcb78abf8601ceb293` |
| executed `ci/app29-gate-b.py` | `406febde3a67c108e987657489c6b429c3e735286aff8563a3a172dd6faf422d` |
| executed `profile/profile.init.gradle` | `aabf7d914402249cdf23d0c868455a5a8bee30160c18ecfcd2b93e030be4791d` |
| executed `profile/profile.json` | `7e80b5d51e7c521d0df72a8b0ce968ac0f50e1c761b03b16c553fbb1ef1a2895` |

The locally bound runner, workflow, init and profile match their exact carrier
blobs byte-for-byte. The actual request differs from the bound preparation only
by `authorized: false -> true`; actual request SHA-256 is
`37675440d9be50aedba8989da67c6f09d73686d3daacf836d49be8667649dc2d`.

## Command and observed failure boundary

Reviewed the actual argv/cwd/exit in `result.commands`, not a reconstructed run.
One `./gradlew` validation invocation, from the backend checkout, used the bound
init and exactly the profile's five task arguments: `test` and the two literal
`--tests` selectors for `mixed pool creator nesting ...` and `MODEL work expiry
inside actual afterJdbcCall ...`. These were independently compared to the full
pinned profile strings. Normal main/test source compilation remained enabled.
Flags include no daemon/parallel/build cache/configuration cache, strict dependency
verification, max-workers1, in-process Kotlin, fixed Temurin21 installation and
private output/cache/home paths; no compiler source exclusion was used.

`gradle-test.log` records Gradle8.14.5, successful `:compileKotlin` and resource
processing, Java NO-SOURCE, then failure in `:compileTestKotlin` while emitting one
class file. Gradle pid2443 exited1; the command wrapper retained outcome UNKNOWN.
There was no `:test` execution, no test XML, no effective Test-worker classpath
receipt, no MODEL stdout and no PG/Ryuk creation in the retained container journal.
**Two selected cases were unexecuted, not two runtime FAIL results.**

## Compile cause: measured filename evidence, not a permissions assumption

The reported failing basename is:

```text
PoolLeaseDispatchCreatorIntegrationTest$MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement$1$1$1$store$1$deleteEligibleSourceGrants$1$shim$1$getClientInfo$lambda$8$lambda$7$lambda$6$$inlined$assertThrows$1.class
```

It is **263 UTF-8 bytes, all ASCII**; the complete path is422 bytes. The basename
alone is8 bytes beyond the usual Linux255-byte component limit. Shortening the
scratch-directory prefix cannot fix that component. This is concrete evidence
for a generated-name portability failure, not ordinary full-path exhaustion.
The raw message is exactly `(Permission denied)`: the collection does not contain
a remote mount/NAME_MAX measurement, syscall errno or parent permission/ACL stat,
so the underlying remote I/O cause is not conclusively measured. Do not convert
that wording into a chmod/chown diagnosis, or claim an independently observed
ENAMETOOLONG. The oversized emitted name plus its source mechanism is the strong,
actionable explanation; a later normal compile must verify the proposed repair.

The source catalog/lockfile pins **Kotlin2.1.21**, **JUnit Jupiter API5.12.2**;
actual captured JDK release is Temurin21.0.12.1+1. The test imports the Kotlin
`org.junit.jupiter.api.assertThrows`, not the Java static method. The failing
suffix identifies the deeply nested `assertThrows<SQLException>` at source
`PoolLeaseDispatchCreatorIntegrationTest.kt:579`, inside the shim's getClientInfo
clock callback and diagnostics capture. The new diagnostics wrapping increases
nesting; the source still has the long descriptive method name.

Version-specific JUnit source was read from the already retained, unmodified
`review/working/app-29-w03-d1-c6-wip-19-research-review/authority/junit-jupiter-api-5.12.2-sources.jar`
(SHA-256 `babbccb7ae82e7ed4f14c140fb11f21fc6ac595c60e8cafe445fbc84d938adab`).
Its `org/junit/jupiter/api/Assertions.kt:270-284` defines this overload inline:
it executes/catches the supplied action, then passes a captured-throwable rethrow
lambda to Java `Assertions.assertThrows(T::class.java)`. That extra inline SAM
body explains the observed `$$inlined$assertThrows$1` class, rather than merely
assuming every source lambda needs a separately written class.

### Smallest recommended source correction

Change **only the assertion at579** to the noninline Java overload, for example:

```kotlin
org.junit.jupiter.api.Assertions.assertThrows(SQLException::class.java) {
    lease.enterDispatch()
}
```

This bypasses the imported inline rethrow wrapper that generated the oversized
class; no selected method rename, new helper, selector change, compiler flag,
dependency change, permission change or broad assertion replacement is needed.
The actual new emitted output remains unverified until primary's authorized
normal compilation; this source-level recommendation is not a compile PASS.

JUnit5.12.2 `Assertions.java:3127-3128` and `AssertThrows.java:49-73` show the direct
overload calls the action once, accepts SQLException or its subtype, returns the
same thrown instance, and fails for no/wrong exception (preserving the wrong
exception as cause). At this site there is no nonlocal return and the return value
is ignored. The direct form changes evaluation/rethrow stack shape, not the
asserted refusal; the earlier afterJdbcCall stack-presence assertion is untouched.
Retain the same lease/action at the same point after retirement observation,
inside the same diagnostics capture. Keep every budget, identity/tail/actor
assertion, diagnostic stage, first-failure handling and restoration unchanged.
Do not use this compile repair to alter the MODEL expectation or replay/rename
other tests. A short noninline extraction is a fallback design only if separately
needed, not part of this recommended one-call repair.

## Separate cleanup failure chain

Line references below are to the exact executed runner pinned above.

1. `command():883-889` retains actual exit1, then raises its nonzero-command
   guard and drains. `drain():854-863` proves absence but additionally records
   any retained nonzero leader. Hence the four `*-nonzero-child` failures at
   interrupted-gradle-test, after-immediate-stop, after-final-stop and
   before-home-cleanup all refer to **the same pid2443 exit1**, not four new
   failures to reap processes. All four receipts have `ok=true`, empty remaining/
   active/adopted lists, no TERM/KILL and no errors. Both Gradle stops exit0 and
   say no daemons are running.
2. `containers():1010-1013` requires exactly one PG plus one Ryuk creation even
   when compilation never reached tests. The before/normal0/final censuses and
   bounded event journal are all empty, each command exit0. With `created={}`,
   the exact-two topology guard throws before owned-containers/image checks or
   the final NORMAL_ABSENT assignment. `attempt('containers', ...)` returns None;
   the result stays UNKNOWN. This is a missing-success-topology condition, not
   evidence of an actual leftover container or a failed docker removal.
3. Independently, `capture_reports():1048-1050` requires `test-results` before
   walking `reports`; the missing first root raises `CAPTURE_ROOT`. Captured
   inventory is empty and `capture_complete=false`; diagnostics never runs.
   Even bypassing the topology failure would leave this separate capture gate
   preventing file cleanup. No XML absence was mislabeled as a passing test.
4. `execute():1240-1262` requires workers, containers and complete capture before
   deletion. `containers_gone=None` short-circuits the before-file drain and wins
   skip-reason precedence: **CONTAINER_CLEANUP_NOT_ABSENT** for all11 paths.
   No removal was attempted. Five backend paths were already absent; six private
   paths `w01`, `project-cache`, `kotlin-cache`, `gradle`, `tmp`, `home` were retained
   at controller finalization. No filesystem deletion-permission failure occurred.
5. The later final census independently records `final_containers_absent=true`
   and drains record `final_children_absent=true`, but neither retroactively sets
   `containers_gone` nor restores capture completeness. UNKNOWN, retained outputs,
   all seven sticky failures and overall FAIL are therefore consistent with the
   runner's decision chain. `outputs_absent=false` and `capture_complete=false`
   must not be erased merely because final children/containers were absent.

This identifies the two cleanup-policy blockers without proposing a broad new
harness or weakening the existing successful-run XML/topology requirements.
Remote final observations are retained receipts, not a new live-host census.

## Independence and limits

Only passive source/Git/hash/stat/archive-source reads, JSON decoding and byte/text
comparisons were used, plus this new private0600 report. No source/tooling edit,
helper import/execution, syntax/static checker, build/test/CI, dependency/network
acquisition, resource control, commit, ownership change or repeat run occurred.
All old failure evidence remains unmodified. The earlier PG18/PG01 failures,
Native05 UNQUALIFIED and existing external/product-proof limits remain intact.
Primary owns any separate source correction, rebinding, admission and validation.
