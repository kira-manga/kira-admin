# W03 connected phase — independent ownership correction review01

2026-09-13 UTC · `/root/w03_connected_ownership_review` · GPT-6-Astra/max · private0600.
**SOURCE-ONLY disposition: H1 and L1 are addressed by the bounded correction. No
remaining ownership source blocker was identified in this four-file delta.** This
is not an authored-test PASS, execution admission, combined source acceptance,
W03/P3 completion or production qualification. Primary and the companion regression
review retain their separate decisions.

## Binding and scope

Private backend HEAD remains `6db944871c1584bd6a1f28263e8010cadd766fab`.
**Never publish this ancestry or private evidence.** The reviewer did not author or
edit W03 source. Read the correction-only diff, corrected four files and relevant
unchanged seams; no repeat audit of the original21-file architecture or historical
restoration. No source/Git writes, builds, tests, checkers, helpers, network or CI.
Only this private report was written for this correction review.

**E/** = `review/working/app-29-ordinary-phase-connected-correction-01/`.
The canonical handoff and E/REPORT.md are byte-identical by digest. Current four-file
bytes match E/after; E/before matches core02's retained after snapshots. The other17
core files and all three peer files retain their core02 hashes on passive reads.

| Binding | SHA-256 |
|---|---|
| Primary `app-29-ordinary-phase-connected-correction-agreement-01.md` | `c363d521fe7fa8f97fa1d6b6957d9d1cb5c7ff8f4c97a24a00c7385ecba078ec` |
| Canonical `app-29-ordinary-phase-connected-correction-handoff-01.md` / E/REPORT.md | `6b63d53a4591398389feac4b99a8beb9d45ed761a8360f544f68d40e50c6e2f5` |
| Original ownership review | `6eab917006f67dbfa50143a683233e92f2d4ab100292ae386222b0b24d2b3a09` |
| E/SEAL.sha256 | `1ebcb7bf0afbb90e0536240c405011f428c16ed42a6048aa016766eb4a32f12c` |
| E/core02-to-correction.patch | `d3c5aae0108aa17acfbf26b634bb1c103dcb5a6b2b6e05ff1041c7e75c725140` |
| E/correction-after.sha256 | `b2d1a421f985cef91e438c30a199b7950a0ef474e097449a529e1ebb39557574` |

P/ = backend `src/main/kotlin/me/manga/kira/backend/common/infrastructure/persistence/`;
Q/ = corresponding `src/test/kotlin/` package.

| Exact reviewed corrected file | SHA-256 |
|---|---|
| P/GuardedJpaTransactionManager.kt | `551e6c9295566f522f55bcafba7d54b98314c8dc34b003c940277e3d81404f00` |
| P/PersistencePhaseOwnership.kt | `19d2e91e3358316c2a369fc62e09a566b0e14fc15bdaefb44310cd36d8a5e500` |
| Q/OrdinarySourceGrantCleanupFixture.kt | `4cea94d0f27384bd16ae00f8ea0dad4f446e890412f6f1506b95497028a7d461` |
| Q/OrdinarySourceGrantCleanupOwnershipIT.kt | `0a2e78581410bc91df644acee2110fd6993f0b746efd0c93ec6cda8034dbede5` |

## H1 — corrected for the declared controlled composition

- `GuardedJpaTransactionManager.kt:17–22,74–80` requires `EntityManagerFactoryInfo`
  and exact selected GuardedDataSource identity before constructing its private
  delegate. Missing interface, null/different metadata and metadata failure refuse
  with a value-free RESOURCE_REFUSED. There is no discovery checkout, URL equivalence
  or attempt to repair/retarget a foreign provider.
- Lines31–47 now let Spring initialize first, then install the wrapper's private,
  fixed `HibernateJpaDialect` and validate effective EMF/DS/dialect identity at
  lines67–71. This directly addresses the unconditional replacements in retained
  Spring6.2.19 `spring-JpaTransactionManager.java:344–356`; no DS reset hides an
  incorrect factory. Spring's setter retains the passed EMF (`:165–166`), so the
  effective-factory identity check is appropriate for the selected fixture.
- `PersistencePhaseOwnership.kt:25–42` rechecks that pairing before acquiring a
  permit. Manager lines56–61 recheck before either scoped or unscoped dispatch/EM
  creation. Private delegate and listener/nested restrictions remain; commit/rollback
  cleanup is not newly blocked by a configuration recheck after work has begun.
  Unknown/mutable/arbitrary provider compatibility is not being certified.

**The authored controls are meaningful, but still unexecuted.**
`OwnershipIT:229–281` first calibrates a real selected-pair begin/commit with one EM
creation/begin and one acquisition-frame publication. It then calibrates a real
same-endpoint foreign-backed factory with native SELECT and rollback/close before
saving counter baselines. Foreign, metadata-unknown and null-DS constructor refusals
must preserve both factories' creation/begin counters, selected acquisition history,
foreign checkout-attempt count and zero admitted owners. This is not a refusal
obtained only through bad credentials/UNKNOWN profile or an occupancy-zero surrogate.

The foreign fixture at `Fixture:119–139,248–263` reuses the existing reader endpoint,
not a second pool/container. Both DataSource overloads count actual forwarded attempts;
EM/factory cleanup is in finally. `OwnershipIT:691–778` forwards real factory metadata
and operations; its calibrated acquisition observer delegates/restores the original
instance ThreadLocal rather than resetting physical counts. `OwnershipIT:283–301`
additionally asserts effective EMF/DS and a distinct fixed Hibernate dialect, so an
incorrect pre-autodetection assignment alone would not satisfy that assertion.

The existing failed-real-begin and post-status materialization cases remain at
`OwnershipIT:303–357`; their proxies at `:863–948` still forward
`EntityManagerFactoryInfo`. They assert actual reached fault/status/outcome/receipt,
so an early configuration refusal is not an acceptable substitute. The separate
real commit/durability/REQUIRED positives remain required runtime controls.

## L1 — bounded reason retention corrected without new refund authority

`PersistencePhaseOwnership.kt:48–55` preserves an existing bounded phase exception
only after the unused entry's cleanup returns. A null local permit is genuinely
unused; a non-null permit's false one-shot release is no longer silently ignored.
A thrown/unsuccessful cleanup produces CLEANUP_UNRESOLVED with `cleanupProven=false`.
Unexpected entry exceptions remain generic/value-free. No old quarantined phase is
released: these locals belong only to the current entry attempt, before manager begin.

The existing one-shot `LocalPersistencePermit.releaseAfterQuiescence()` and
`PersistencePhaseContext.entryPublicationFailed()` ownership paths are not replaced,
retried or relaxed. The correction does not manufacture a lease receipt or infer
physical quiescence from an entry exception. Primary expressly dropped the synthetic
L1 quarantine/sentinel test; that is respected. This source disposition does not
waive genuine runtime quarantine/custody gates or claim the later statics have run.

## New test seams and remaining gates

The other test edits introduce observation, not product ownership authority. The
PgSleep observer receives only PID/backend-start/accepted-at scalars, uses its own
reader connection, and closes/joins through finally. The commit observation delegates
and restores the existing guard ThreadLocal, records no fake outcome/receipt and
asserts its discriminator outside the expected-exception extent. The new afterCommit
case requires independent durability, retained COMMITTED, exact cleanup/refund and
restored caller interrupt; cap/successor changes read actual JDBC scalars. No new
production callback, pool, bean, SQL path, schema or peer-port change was found.

This bounded ownership review does not independently substitute for the companion
regression review's B1/B2 oracle assessment. Reflection/observer feasibility, real
failed-native-commit reachability, observer scheduling, interrupt restoration and
same-session cap restoration all remain uncompiled/unexecuted. A positive in-flight
witness and original accepted-lease-through-disposition ≤3000ms remain mandatory;
Future/model expiry or eventual cleanup is not lifetime proof. The inventory is
15 authored ownership methods +7 pure outcome +6 peer methods, not28 passes.

Preserve all348 seed members and the full retained/new source inventory in primary's
combined freeze; the four-path review is not a replacement source-membership boundary.
No historical audit or grandfathered evidence is re-required. Production/UNKNOWN,
Boot/customizers, W05 request expiry, operational incident sink, complete P3 and
native/opaque/liveness gates remain open. Primary alone selects/adopts the affected
compilation/static/runtime batch after both correction reviews.
