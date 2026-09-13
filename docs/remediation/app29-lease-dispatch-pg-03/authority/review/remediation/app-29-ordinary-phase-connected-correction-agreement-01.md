# W03 connected phase — primary bounded correction agreement01

2026-09-13 UTC. SOURCE AUTHORING ONLY. Primary read both full actual-diff reports:
- ownership6eab917006f67dbfa50143a683233e92f2d4ab100292ae386222b0b24d2b3a09;
- regression3ccfff09f4a9f1593e4867b7e019c1b912de4359382d0e94b32f6995763438ad.
The exact Spring6.2.19 afterPropertiesSet source independently confirms unconditional
EMF DataSource/dialect replacement. The current source packet86fa8ceb remains frozen
and UNTESTED. The following bounded correction is required, not another full audit.

## Source and oracle corrections

1. H1: before any entity-manager creation/begin or phase permit, require supported
   EntityManagerFactoryInfo with exact selected GuardedDataSource identity. Unknown/null/
   different/same-URL resources are refused without discovery borrowing. A manager
   dataSource reset alone cannot validate the EMF. After Spring autodetection, pin and
   validate the private effective DS/EMF and fixed supported HibernateJpaDialect. No
   factory-supplied custom-dialect/customizer contract or new alias/Boot framework.
   Add a healthy real foreign-backed EMF negative with zero additional EM creation/
   begin/checkout after bootstrap on both resources; metadata-unknown refusal may
   share this case. Reuse existing exact-EMF real commit/join positives. Existing
   failed-begin/lazy-holder decorators must still exercise their intended fault, not
   become early configuration refusals.
2. B1: strengthen existing pg_sleep case with a bounded independent observer positively
   witnessing exact PID/backend-start in PgSleep. Observation only: never move/copy the
   business transaction or fabricate dispatch. Join/close observer in finally. Assert
   the positive witness outside expected-error extent and retain original accepted-
   lease-to-disposition <=3000ms, row/lock/session and exact-receipt assertions.
3. B2: existing UNKNOWN case must witness real lower commit invocation and failure,
   not only Spring beforeCommit or failed rollback. Reuse the test-only own-project/
   driver observation seam with real remote fault. No driver/vendor/product fault
   switch or direct assignment to outcome state. Local refund remains distinct.
4. One useful additional real afterCommit InterruptedException case jointly checks
   durable committed delete, retained COMMITTED despite framework failure, exact
   cleanup/refund and restored caller interrupt. Clear test interrupt only in finally.
   Add actual JDBC read-cap/restoration scalar assertions to existing caps/successor
   coverage, rather than new test families.
5. L1: after genuinely unused-entry cleanup succeeds preserve an existing bounded
   PersistencePhaseException code; unexpected failures remain value-free. Add one
   focused code assertion at existing quarantine refusal, no incident framework.

## Exact author scope and limits

PRIVATE root kira-backend at6db944871c1584bd6a1f28263e8010cadd766fab. Allowed product
changes: common/infrastructure/persistence/GuardedJpaTransactionManager.kt and
PersistencePhaseOwnership.kt. Allowed test changes: matching test directory's
OrdinarySourceGrantCleanupFixture.kt and OrdinarySourceGrantCleanupOwnershipIT.kt.
If one small test-only helper split is materially required, report its proposed path
and reason first. No peer SQL/port/six-test changes, no source snapshots rewritten.
All remaining core paths must keep packet02 bytes unless primary separately agrees.

No builds/checkers/helper execution/Git writes/CI/driver/live bean/schema/new pool
or public private-ancestry push is admitted. No W03/package/integration credit.
Delegate remains private, listeners/customizers/nested restrictions unchanged; W05
request expiry/Boot wiring/operational sink/full P3/native/opaque/liveness remain open.
Preserve all348 historical seed members and full current/new source inventory for the
next primary freeze. Author reports exact diff and authored/unexecuted tests; both
independent reviewers review their correction risks, not their own implementation.
Primary selects one affected compilation/static/runtime batch after correction review.
