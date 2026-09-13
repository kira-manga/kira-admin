# Core C2 getter — independent actual-source review

2026-09-11 UTC · `/root/app_02_independent_review` · **NONAUTHOR**.

**ACCEPT — exact two-file source correction only. No material finding.**
The actual delta conforms to primary agreement
`322ac807f43a3c69011f0ae0978136853cc4fccc9dffbbc43ce2ab03da36833d`.
This is not execution admission, three passing tests, native qualification, or a
prediction that the next Core47 will pass. Reviewer executed no candidate code,
compiler, checker, test, build, import, CI, or runtime probe.

## Exact reviewed bytes

Packet **P** = `review/working/app-29-core-c2-isolation-getter-source-01/`.
Private source root **U** = `.kira-validation/pgjdbc-owned-cut/upstream/`.

| Input | SHA-256 |
|---|---|
| P/AUTHOR_REPORT.md | `f5f4289549c7d393379b0da4298c3b549edb879d42374d837a03d6b9d0c00e6e` |
| P/SEAL.sha256 | `529c90aea9e37bbf54ed9a51cab698c877b8297c4f18b7a8427fae1ad5d5755a` |
| P/source-delta.patch | `5be5cd1adb568dc796a01f7756b070cc7fead7c64d99ee925c12530ab8e772ae` |
| U/pgjdbc/src/main/java/org/postgresql/jdbc/PgConnection.java (**N**) | `486aba8d77f3a38b9b0b16540bf7f62010c438803bf4cc426e05bbb5c3528114` |
| U/pgjdbc-mockito-test/src/test/java/org/postgresql/jdbc/KiraOwnedJdbcCutFaultTest.java (**F**) | `d8f8ba511272279f05c785beac89238836cb96f1bb374bcff17a73bbabb0242b` |

Independently verified all18 sealed members (19 packet files including seal), both
live files equal frozen after-images, and reconstructed the complete patch from
before/after bytes. Before-images match my prior inspected getter `05b4b69f…` and
native04 Fault source `da6acff1…`. N is **+22/-4, getter only**; F is **+135/-0**:
three imports, three ordinary test groups, and a14-line actual-Life helper.

Both1018-entry source maps have identical pathsets and only those two hash
replacements. All1018 current file hashes and the matching non-build/non-.gradle/
non-.git file inventory were independently checked. All17 protected pins match,
including candidate a415, native03/native04 receipts and immutable Core freeze/
private-checkpoint inputs. Backend is clean at
`926927ab805a2a3b78957862f3b744d0fe399ac5`, matching the packet. No historical
manifest, Core47 source, or existing test/helper byte was changed.

## Actual getter and failure semantics

N1085 owns the genuine BaseStatement before execution. Inner ResultSet TWR at1101
closes the acquired result before outer parent closure, on normal or exceptional
exit. The pre-result execution failure therefore still closes the parent. Normal
Java nested TWR preserves an initializer/body failure, suppresses later close
failures and attempts remaining resource closures; no bespoke catch, swallow,
retry, synthetic first-close receipt, or native retention change was introduced.
This agrees with [JLS21 §14.20.3](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.20.3),
already consulted during plan review.

The exact SHOW, QUERY_SUPPRESS_BEGIN, result/update traversal, NO_DATA exception,
result nonnull check, and single next/getString traversal are preserved. The
existing null/unknown fallback, Locale.US conversion and all four isolation
mappings are unchanged. Shared execSQLQuery overloads remain byte-identical.
Warnings transfer at1097–1099 precedes parent closure, whose unchanged
PgStatement.closeForNextExecution403–406 clears its warning storage.

Unchanged native first-close bookkeeping still distinguishes successful first
return from repeated close and sticky failure. Parent closure may revisit its
already closed result; that is not a second first-close receipt. This bounded
repair does not promise successful closure of a partially constructed/unpublished
resource that the getter never acquired, or excuse its existing fail-closed state.

## Three authored tests — source-credible, not executed

All selectors have prefix `org.postgresql.jdbc.KiraOwnedJdbcCutFaultTest.`:

1. **isolationGetterRepeatedSuccessClosesBothResourcesWithoutBeginningATransaction**
   (F70): two genuine calls, explicit REPEATABLE_READ, autocommit=false and IDLE
   before/after. The flags assertion masks QUERY_SUPPRESS_BEGIN rather than
   rejecting other legitimate flags. It captures both real factory-returned
   Lives and requires their first-returned states plus zero retained state before
   fixture retirement. Its injected warning uses the actual StatementResultHandler
   (PgStatement272–273); exact warning identity after parent close discriminates
   warning transfer. This is injected-warning coverage, not a server-notice claim.
2. **isolationGetterExecuteFailureClosesItsStatementAndPreservesTheException**
   (F116): injection precedes real execute delegation/result creation. Exactly one
   genuine native child exists; the original SQLException must escape, with no
   incidental suppression, and the parent's actual first close must return.
   No ResultSet receipt is fabricated.
3. **isolationGetterReadFailureClosesBothResourcesAndPreservesTheException**
   (F148): real query/result creation precedes arming getEncoding. Source tracing
   through PgStatement result installation and PgResultSet.next/getString supports
   the intended read extent: PgResultSet2505 calls N1242–1243. Both Lives must still
   be first-never at injection, and first-returned after the same marker escapes.
   Exactly one injection, no incidental suppression, zero invocation failure bits,
   zero native children and zero retention remain hard assertions.

F915 captures unique exact-class, factory-returned, first-never receivers from the
actual native graph, retaining Lives before actualEnd compaction. No new reflection
or production hook is used. Every retention assertion occurs after the original
executor is restored; otherwise the unchanged reader correctly refuses the mock.
Owned, ExecutorFault, getRawArguments delegation and all existing first-close/
stickiness assertions are byte-preserved. No additional matrix is justified here.

## Remaining gates and handoff

Only source credibility is accepted: compilation, actual fault reachability and
three runtime outcomes remain unverified. No new compound-close-failure execution
is claimed; normal TWR and preserved existing boundary coverage are distinct from
such a test. NO_DATA and null/unknown mappings were preserved, not newly exercised.

Primary owns the smallest changed-source validation, newly identified candidate,
exact private provenance and subsequent genuine Core47 execution. Keep a415,
native03 **72 passed/1 failed**, native04's separate ten-case acceptance, and hosted
Core47 **20 passed/27 failed** immutable. All348 historical seed requirements and
remaining Native/Core/P3/W03/App29 gates remain open. Nothing was published.

Only this new report was written, mode0600 beneath private0700 review directories;
source, sealed packet, history and Git state were not edited by the reviewer.
