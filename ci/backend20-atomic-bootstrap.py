"""Private Backend20 derivative of the mature Backend11 owner; never import as a library.

Primary-bound candidate; live admission/launch remain primary-owned. Even a later PASS is targeted bootstrap evidence, not deployment,
reconciliation/adoption, a full-suite result or issue closure. Primary holds the existing local
batch.lock across hosted launch/collection/cleanup; this VM does not claim that host-local lock.
"""
import hashlib, json, os, re, shutil, signal, subprocess, tarfile, time
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

ADMIN = Path(__file__).resolve().parent.parent
BACKEND = ADMIN.parent / 'backend'
RUN = Path(os.environ['BACKEND20_RUN'])
RUN.mkdir(mode=0o700, exist_ok=False)
REPORTS, HOME, W01, TEMP = (RUN / n for n in ('reports', 'gradle', 'w01', 'tmp'))
for directory in (REPORTS, HOME, W01, TEMP): directory.mkdir(mode=0o700)
ENV = dict(os.environ, GRADLE_USER_HOME=str(HOME), W01_RUN=str(W01), TMPDIR=str(TEMP),
           JAVA_TOOL_OPTIONS=f'-Djava.io.tmpdir={TEMP}', DOCKER_HOST='unix:///var/run/docker.sock')
TARGETS = json.loads((ADMIN / 'ci/backend20-atomic-bootstrap.request.json').read_text())
CLASSES, METHODS = TARGETS['classes'], TARGETS['methods']

# Primary-bound exact source checkpoint; live admission/launch remain primary-owned.
EXPECTED_BACKEND_SHA = '1b5803aa08a3a50c005eae6c904349c7e7bb6ada'
# Corrected-source selection:124 unchanged methods/cases in42 previously blocked JPA PostgreSQL classes.
# Retain115 old-source passes separately; no corrected-source239-case claim.
EXPECTED_CLASSES = {
    'me.manga.kira.backend.sourceconfig.FlywayMigrationIT': 3,
    'me.manga.kira.backend.sourceconfig.StartupConsistencyIT': 12,
    'me.manga.kira.backend.sourceconfig.admin.AuditLogIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.BootstrapConcurrencyIT': 4,
    'me.manga.kira.backend.sourceconfig.admin.BootstrapEndpointIT': 4,
    'me.manga.kira.backend.sourceconfig.admin.BootstrapLateRollbackIT': 2,
    'me.manga.kira.backend.sourceconfig.admin.BootstrapPublicationGuardIT': 5,
    'me.manga.kira.backend.sourceconfig.admin.BootstrapReplayIT': 2,
    'me.manga.kira.backend.sourceconfig.admin.ConcurrentDifferentSourcePublishIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.ConcurrentSameSourcePublishIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.DisableRemoveVisibilityIT': 3,
    'me.manga.kira.backend.sourceconfig.admin.DocumentOrderDeterminismIT': 2,
    'me.manga.kira.backend.sourceconfig.admin.EmptyDocumentPublishIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.EndpointCompletenessIT': 4,
    'me.manga.kira.backend.sourceconfig.admin.FullBundledParityIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.ImportBundledIT': 11,
    'me.manga.kira.backend.sourceconfig.admin.ImportCreatesSingleSnapshotIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.ImportNoChangesIsNoOpIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.LifecycleNeutralStorageIT': 2,
    'me.manga.kira.backend.sourceconfig.admin.PublicConfigSecretsRejectedIT': 7,
    'me.manga.kira.backend.sourceconfig.admin.PublicationFailureRollbackIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.PublishInvalidFailsIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.PublishStateRulesIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.RemovedCannotReturnIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.RetiredSourceVisibilityIT': 2,
    'me.manga.kira.backend.sourceconfig.admin.RollbackIT': 3,
    'me.manga.kira.backend.sourceconfig.admin.ServerManagedLifecycleIT': 2,
    'me.manga.kira.backend.sourceconfig.admin.SnapshotTimestampConsistencyIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.SourceChangesetIT': 3,
    'me.manga.kira.backend.sourceconfig.admin.SourceEditorDraftIT': 6,
    'me.manga.kira.backend.sourceconfig.admin.SourceOperationalModeIT': 4,
    'me.manga.kira.backend.sourceconfig.admin.SourcePublishFlowIT': 1,
    'me.manga.kira.backend.sourceconfig.admin.StrictAdminParserIT': 2,
    'me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT': 3,
    'me.manga.kira.backend.sourceconfig.public.ETagIT': 2,
    'me.manga.kira.backend.sourceconfig.public.IfNoneMatchVariantsIT': 1,
    'me.manga.kira.backend.sourceconfig.public.PublicSourceSummaryConsistencyIT': 2,
    'me.manga.kira.backend.sourceconfig.public.PublicSourcesIT': 13,
    'me.manga.kira.backend.sourceconfig.public.RawBytesChecksumIT': 1,
    'me.manga.kira.backend.sourceconfig.public.SourceCatalogV2IT': 3,
    'me.manga.kira.backend.sourceconfig.signing.SignedDocumentIT': 1,
    'me.manga.kira.backend.user.SecurityMatrixIT': 2,
}
EXPECTED_METHODS = {
    'me.manga.kira.backend.sourceconfig.FlywayMigrationIT': [
        'bootstrap constraints reject incomplete completion partial receipts and invalid phases',
        'flyway history is exactly V1 through V13 then V13_1 and V13_2 in version order',
        'fresh schema defaults credential version to zero and rejects negative and null versions',
    ],
    'me.manga.kira.backend.sourceconfig.StartupConsistencyIT': [
        'COMPLETE requires every real origin receipt field and a nonnull pointer',
        'a missing singleton fails closed rather than looking like an empty catalog',
        'coherent reads reject receipt or retained origin metadata corruption after latest advances',
        'existing snapshots with a consistent pointer pass',
        'fresh empty DB passes both checks',
        'minimum-server-revision not greater than bundled-revision-floor fails fast',
        'origin foreign keys protect real history after latest advances',
        'pointer NULL while snapshots exist fails fast',
        'pointer not equal to MAX document revision fails fast',
        'sequence gaps above the real completed origin remain valid',
        'sequence-next below minimum-server-revision fails fast',
        'sequence-next not greater than the latest revision fails fast',
    ],
    'me.manga.kira.backend.sourceconfig.admin.AuditLogIT': [
        'publish and disable write hygienic audit rows',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapConcurrencyIT': [
        'bootstrap owning G makes a creator wait and append only a later draft',
        'creator owning G after insertion makes bootstrap wait then reject its retained extra head',
        'normal COMPLETE materialization acquires G even when its transactional caller did not',
        'overlapping identical raw requests serialize to one publication and the same immutable receipt',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapEndpointIT': [
        'anonymous and USER cannot bootstrap and ADMIN still needs exact confirmation',
        'exactly five MiB is accepted but one byte more is rejected before PENDING or COMPLETE dispatch',
        'malformed UTF8 in an otherwise admissible provenance string is not replacement decoded',
        'valid padded UTF8 JSON crosses the default body cap without charset transcoding',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapLateRollbackIT': [
        'a completion update affecting zero rows is not success and rolls back its staged publication',
        'late completion update failure rolls back source history publication receipt and audit',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapPublicationGuardIT': [
        'PENDING permits a draft but publish editor publish and republish roll back at the shared guard',
        'PENDING rejects ordinary import including no-op and direct empty materialization',
        'RECONCILIATION retains public bytes but refuses import bootstrap and alternate publication',
        'bootstrap cannot adopt an expected draft even when its content matches the approved payload',
        'old confirmation-only POST is a nonmutating conflict before and after completion',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapReplayIT': [
        'same bytes return the origin receipt after content addition lifecycle and policy changes',
        'unavailable current initial policy fails a new PENDING attempt without staging',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ConcurrentDifferentSourcePublishIT': [
        'two concurrent publishes to different sources both survive in the final snapshot',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ConcurrentSameSourcePublishIT': [
        'two concurrent publishes of the same source never violate the one-published index',
    ],
    'me.manga.kira.backend.sourceconfig.admin.DisableRemoveVisibilityIT': [
        'a direct active to removed is 409',
        'a direct active to retired is 409',
        'disable then retire then remove walk the stanza through the document',
    ],
    'me.manga.kira.backend.sourceconfig.admin.DocumentOrderDeterminismIT': [
        'a bundled import serves stanzas in payload order',
        'shuffled repository orders assemble to byte-identical canonical documents',
    ],
    'me.manga.kira.backend.sourceconfig.admin.EmptyDocumentPublishIT': [
        'removing the last source publishes a valid empty document',
    ],
    'me.manga.kira.backend.sourceconfig.admin.EndpointCompletenessIT': [
        'a generic source missing a required verb cannot publish',
        'a generic source missing both home and featured cannot publish',
        'a generic source without chapters publishes fine',
        'a legacy source is not publicly publishable',
    ],
    'me.manga.kira.backend.sourceconfig.admin.FullBundledParityIT': [
        'the full bundled document parses, validates, canonicalizes, imports, serves and re-checksums',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ImportBundledIT': [
        'a body over the 5 MiB import limit is rejected with 413',
        'a terminally removed source is not revived by import',
        'changed content for a retired source is skippedRetired and nothing is stored',
        'database failure after the first stanza rolls back the complete import',
        'import of the trimmed document creates + publishes + serves the sources in payload order',
        'incoming revision and generatedAt do not drive server revision allocation',
        'one bad stanza fails the whole import with 422 and nothing is persisted',
        'partial catalog import adopts payload order and publishes one reordered snapshot',
        're-import never publishes or replaces a draft-only source',
        're-import of the identical payload is a no-op - zero new revisions and zero new snapshots',
        'unsafe header filters reject a mixed create and update import before any public mutation',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ImportCreatesSingleSnapshotIT': [
        'importing four sources creates exactly one published document row',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ImportNoChangesIsNoOpIT': [
        're-importing an identical document with explicit lifecycle values is a no-op',
    ],
    'me.manga.kira.backend.sourceconfig.admin.LifecycleNeutralStorageIT': [
        'importing a disabled stanza stores neutral content with initial status disabled, and re-import is a no-op',
        'stored content is lifecycle-neutral while the assembled document injects the served value',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublicConfigSecretsRejectedIT': [
        'a forbidden Cookie header is rejected',
        'a real bearer token on authorization is rejected as secret-like',
        'a url with user-info is rejected',
        'a whitespace-padded authorization header cannot bypass publication validation',
        'the Bearer null placeholder is accepted',
        'the full real bundled document passes all secret-safety rules',
        'unsafe header drafts retain content and safe diagnostics but cannot change public v1 or v2',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublicationFailureRollbackIT': [
        'interrupted snapshot publication leaves no partial state',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublishInvalidFailsIT': [
        'publishing an invalid revision is 422 and leaves the document unchanged',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublishStateRulesIT': [
        'publishable-revision-states rules hold and there is always one published revision',
    ],
    'me.manga.kira.backend.sourceconfig.admin.RemovedCannotReturnIT': [
        'a removed source refuses every transition and never reappears',
    ],
    'me.manga.kira.backend.sourceconfig.admin.RetiredSourceVisibilityIT': [
        'a retired generic stanza is served as removed and can be un-retired',
        'a retired legacy stanza cannot be un-retired',
    ],
    'me.manga.kira.backend.sourceconfig.admin.RollbackIT': [
        'a never-published draft cannot use rollback as a disguised first publish',
        'rollback copies old content into a new published revision',
        'rollback of a disabled source leaves it disabled',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ServerManagedLifecycleIT': [
        'authoring a non-neutral lifecycle is 400 on create and on revision',
        'rollback does not restore a prior server lifecycle',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SnapshotTimestampConsistencyIT': [
        'generatedAt equals the snapshot created_at and the audit detail instant',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourceChangesetIT': [
        'changesets autosave with etags and apply two sources in one snapshot',
        'failed changeset makes no partial lifecycle or catalog change',
        'stale changeset write fails and apply requires one-time step-up',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourceEditorDraftIT': [
        'autosave uses optimistic etags and keeps invalid JSON outside immutable history',
        'finalize is strict and atomically advances the editor baseline',
        'invalid draft fails strict finalization and discard is compare and swap',
        'oversized autosave fails without changing the draft',
        'quick publish is atomic and requires one-time password step-up',
        'unsafe header quick publish rolls back its new revision and preserves editor and public state',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourceOperationalModeIT': [
        'enabled and disabled reuse working content while publishing lifecycle changes',
        'proof is one time and invalid mode does not consume it',
        'states outside the quick control are rejected without publishing',
        'three-state mode is protected idempotent and publishes one atomic catalog revision',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourcePublishFlowIT': [
        'create validate publish then the stanza is served with a matching checksum',
    ],
    'me.manga.kira.backend.sourceconfig.admin.StrictAdminParserIT': [
        'the compatibility import parser accepts an unknown field and surfaces a warning',
        'the compatibility import parser rejects genuinely malformed json',
    ],
    'me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT': [
        'gapped older traversal survives a newer insert and ends without duplicate or lost rows',
        'growing TOAST histories keep query columns row consumption and deep seek bounded',
        'real authentication still gates bounded array history reads',
    ],
    'me.manga.kira.backend.sourceconfig.public.ETagIT': [
        'document serves a strong quoted etag and honors conditional GET',
        'historical snapshots are admin-only and the public route has no revision param',
    ],
    'me.manga.kira.backend.sourceconfig.public.IfNoneMatchVariantsIT': [
        'if-none-match variants follow weak comparison',
    ],
    'me.manga.kira.backend.sourceconfig.public.PublicSourceSummaryConsistencyIT': [
        'new revision after document selection cannot relabel old content with new metadata',
        'removal after document selection preserves the complete old summary generation',
    ],
    'me.manga.kira.backend.sourceconfig.public.PublicSourcesIT': [
        'a draft-only source never appears in the list',
        'a single source summary exposes every field',
        'an unknown lifecycle or engine filter value is 400',
        'by-api active serves the stanza with no lifecycle key',
        'by-api disabled and retired carry the app lifecycle value',
        'by-api removed is 410 and unknown or draft-only is 404',
        'document 404 when nothing is published',
        'document appVersion is validated',
        'document meta reports the latest shape and 404 when none',
        'legacy sources are never exposed even through the engine filter',
        'no document ever published yields an empty array',
        'the lifecycle filter maps retired to removed and filters correctly',
        'the list is ordered by document position not by api',
    ],
    'me.manga.kira.backend.sourceconfig.public.RawBytesChecksumIT': [
        'hashing the raw public document bytes reproduces the etag and checksum header',
    ],
    'me.manga.kira.backend.sourceconfig.public.SourceCatalogV2IT': [
        'cutover apply rejects unexpected inventory without partial lifecycle changes',
        'cutover is dry-run first atomic exact 12 and idempotent',
        'signed manifest and immutable source revisions are conditional and verifiable',
    ],
    'me.manga.kira.backend.sourceconfig.signing.SignedDocumentIT': [
        'published documents expose verifiable immutable signature chain and conditional GET metadata',
    ],
    'me.manga.kira.backend.user.SecurityMatrixIT': [
        'ADMIN token is allowed on admin endpoints',
        'anonymous gets 200 on the public document and sources once one is published',
    ],
}
# Ordinary methods keep (); parameterized XML display names are exact and unique.
EXPECTED_CASES = {
    'me.manga.kira.backend.sourceconfig.FlywayMigrationIT': [
        'bootstrap constraints reject incomplete completion partial receipts and invalid phases()',
        'flyway history is exactly V1 through V13 then V13_1 and V13_2 in version order()',
        'fresh schema defaults credential version to zero and rejects negative and null versions()',
    ],
    'me.manga.kira.backend.sourceconfig.StartupConsistencyIT': [
        'COMPLETE requires every real origin receipt field and a nonnull pointer()',
        'a missing singleton fails closed rather than looking like an empty catalog()',
        'coherent reads reject receipt or retained origin metadata corruption after latest advances()',
        'existing snapshots with a consistent pointer pass()',
        'fresh empty DB passes both checks()',
        'minimum-server-revision not greater than bundled-revision-floor fails fast()',
        'origin foreign keys protect real history after latest advances()',
        'pointer NULL while snapshots exist fails fast()',
        'pointer not equal to MAX document revision fails fast()',
        'sequence gaps above the real completed origin remain valid()',
        'sequence-next below minimum-server-revision fails fast()',
        'sequence-next not greater than the latest revision fails fast()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.AuditLogIT': [
        'publish and disable write hygienic audit rows()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapConcurrencyIT': [
        'bootstrap owning G makes a creator wait and append only a later draft()',
        'creator owning G after insertion makes bootstrap wait then reject its retained extra head()',
        'normal COMPLETE materialization acquires G even when its transactional caller did not()',
        'overlapping identical raw requests serialize to one publication and the same immutable receipt()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapEndpointIT': [
        'anonymous and USER cannot bootstrap and ADMIN still needs exact confirmation()',
        'exactly five MiB is accepted but one byte more is rejected before PENDING or COMPLETE dispatch()',
        'malformed UTF8 in an otherwise admissible provenance string is not replacement decoded()',
        'valid padded UTF8 JSON crosses the default body cap without charset transcoding()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapLateRollbackIT': [
        'a completion update affecting zero rows is not success and rolls back its staged publication()',
        'late completion update failure rolls back source history publication receipt and audit()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapPublicationGuardIT': [
        'PENDING permits a draft but publish editor publish and republish roll back at the shared guard()',
        'PENDING rejects ordinary import including no-op and direct empty materialization()',
        'RECONCILIATION retains public bytes but refuses import bootstrap and alternate publication()',
        'bootstrap cannot adopt an expected draft even when its content matches the approved payload()',
        'old confirmation-only POST is a nonmutating conflict before and after completion()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.BootstrapReplayIT': [
        'same bytes return the origin receipt after content addition lifecycle and policy changes()',
        'unavailable current initial policy fails a new PENDING attempt without staging()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ConcurrentDifferentSourcePublishIT': [
        'two concurrent publishes to different sources both survive in the final snapshot()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ConcurrentSameSourcePublishIT': [
        'two concurrent publishes of the same source never violate the one-published index()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.DisableRemoveVisibilityIT': [
        'a direct active to removed is 409()',
        'a direct active to retired is 409()',
        'disable then retire then remove walk the stanza through the document()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.DocumentOrderDeterminismIT': [
        'a bundled import serves stanzas in payload order()',
        'shuffled repository orders assemble to byte-identical canonical documents()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.EmptyDocumentPublishIT': [
        'removing the last source publishes a valid empty document()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.EndpointCompletenessIT': [
        'a generic source missing a required verb cannot publish()',
        'a generic source missing both home and featured cannot publish()',
        'a generic source without chapters publishes fine()',
        'a legacy source is not publicly publishable()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.FullBundledParityIT': [
        'the full bundled document parses, validates, canonicalizes, imports, serves and re-checksums()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ImportBundledIT': [
        'a body over the 5 MiB import limit is rejected with 413()',
        'a terminally removed source is not revived by import()',
        'changed content for a retired source is skippedRetired and nothing is stored()',
        'database failure after the first stanza rolls back the complete import()',
        'import of the trimmed document creates + publishes + serves the sources in payload order()',
        'incoming revision and generatedAt do not drive server revision allocation()',
        'one bad stanza fails the whole import with 422 and nothing is persisted()',
        'partial catalog import adopts payload order and publishes one reordered snapshot()',
        're-import never publishes or replaces a draft-only source()',
        're-import of the identical payload is a no-op - zero new revisions and zero new snapshots()',
        'unsafe header filters reject a mixed create and update import before any public mutation()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ImportCreatesSingleSnapshotIT': [
        'importing four sources creates exactly one published document row()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ImportNoChangesIsNoOpIT': [
        're-importing an identical document with explicit lifecycle values is a no-op()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.LifecycleNeutralStorageIT': [
        'importing a disabled stanza stores neutral content with initial status disabled, and re-import is a no-op()',
        'stored content is lifecycle-neutral while the assembled document injects the served value()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublicConfigSecretsRejectedIT': [
        'a forbidden Cookie header is rejected()',
        'a real bearer token on authorization is rejected as secret-like()',
        'a url with user-info is rejected()',
        'a whitespace-padded authorization header cannot bypass publication validation()',
        'the Bearer null placeholder is accepted()',
        'the full real bundled document passes all secret-safety rules()',
        'unsafe header drafts retain content and safe diagnostics but cannot change public v1 or v2()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublicationFailureRollbackIT': [
        'interrupted snapshot publication leaves no partial state()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublishInvalidFailsIT': [
        'publishing an invalid revision is 422 and leaves the document unchanged()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.PublishStateRulesIT': [
        'publishable-revision-states rules hold and there is always one published revision()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.RemovedCannotReturnIT': [
        'a removed source refuses every transition and never reappears()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.RetiredSourceVisibilityIT': [
        'a retired generic stanza is served as removed and can be un-retired()',
        'a retired legacy stanza cannot be un-retired()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.RollbackIT': [
        'a never-published draft cannot use rollback as a disguised first publish()',
        'rollback copies old content into a new published revision()',
        'rollback of a disabled source leaves it disabled()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.ServerManagedLifecycleIT': [
        'authoring a non-neutral lifecycle is 400 on create and on revision()',
        'rollback does not restore a prior server lifecycle()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SnapshotTimestampConsistencyIT': [
        'generatedAt equals the snapshot created_at and the audit detail instant()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourceChangesetIT': [
        'changesets autosave with etags and apply two sources in one snapshot()',
        'failed changeset makes no partial lifecycle or catalog change()',
        'stale changeset write fails and apply requires one-time step-up()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourceEditorDraftIT': [
        'autosave uses optimistic etags and keeps invalid JSON outside immutable history()',
        'finalize is strict and atomically advances the editor baseline()',
        'invalid draft fails strict finalization and discard is compare and swap()',
        'oversized autosave fails without changing the draft()',
        'quick publish is atomic and requires one-time password step-up()',
        'unsafe header quick publish rolls back its new revision and preserves editor and public state()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourceOperationalModeIT': [
        'enabled and disabled reuse working content while publishing lifecycle changes()',
        'proof is one time and invalid mode does not consume it()',
        'states outside the quick control are rejected without publishing()',
        'three-state mode is protected idempotent and publishes one atomic catalog revision()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.SourcePublishFlowIT': [
        'create validate publish then the stanza is served with a matching checksum()',
    ],
    'me.manga.kira.backend.sourceconfig.admin.StrictAdminParserIT': [
        'the compatibility import parser accepts an unknown field and surfaces a warning()',
        'the compatibility import parser rejects genuinely malformed json()',
    ],
    'me.manga.kira.backend.sourceconfig.infrastructure.AdminHistoryRepositoryIT': [
        'gapped older traversal survives a newer insert and ends without duplicate or lost rows()',
        'growing TOAST histories keep query columns row consumption and deep seek bounded()',
        'real authentication still gates bounded array history reads()',
    ],
    'me.manga.kira.backend.sourceconfig.public.ETagIT': [
        'document serves a strong quoted etag and honors conditional GET()',
        'historical snapshots are admin-only and the public route has no revision param()',
    ],
    'me.manga.kira.backend.sourceconfig.public.IfNoneMatchVariantsIT': [
        'if-none-match variants follow weak comparison()',
    ],
    'me.manga.kira.backend.sourceconfig.public.PublicSourceSummaryConsistencyIT': [
        'new revision after document selection cannot relabel old content with new metadata()',
        'removal after document selection preserves the complete old summary generation()',
    ],
    'me.manga.kira.backend.sourceconfig.public.PublicSourcesIT': [
        'a draft-only source never appears in the list()',
        'a single source summary exposes every field()',
        'an unknown lifecycle or engine filter value is 400()',
        'by-api active serves the stanza with no lifecycle key()',
        'by-api disabled and retired carry the app lifecycle value()',
        'by-api removed is 410 and unknown or draft-only is 404()',
        'document 404 when nothing is published()',
        'document appVersion is validated()',
        'document meta reports the latest shape and 404 when none()',
        'legacy sources are never exposed even through the engine filter()',
        'no document ever published yields an empty array()',
        'the lifecycle filter maps retired to removed and filters correctly()',
        'the list is ordered by document position not by api()',
    ],
    'me.manga.kira.backend.sourceconfig.public.RawBytesChecksumIT': [
        'hashing the raw public document bytes reproduces the etag and checksum header()',
    ],
    'me.manga.kira.backend.sourceconfig.public.SourceCatalogV2IT': [
        'cutover apply rejects unexpected inventory without partial lifecycle changes()',
        'cutover is dry-run first atomic exact 12 and idempotent()',
        'signed manifest and immutable source revisions are conditional and verifiable()',
    ],
    'me.manga.kira.backend.sourceconfig.signing.SignedDocumentIT': [
        'published documents expose verifiable immutable signature chain and conditional GET metadata()',
    ],
    'me.manga.kira.backend.user.SecurityMatrixIT': [
        'ADMIN token is allowed on admin endpoints()',
        'anonymous gets 200 on the public document and sources once one is published()',
    ],
}
# Current66 source bytes, including the authorized12 annotation-name-only corrections.
EXPECTED_SOURCE_SHA256 = {
    'src/main/kotlin/me/manga/kira/backend/common/web/RequestBodySizeLimitFilter.kt': '0b78a3e8a368de063f715a3b55d0b61344dba1eddb7b0ac6268a5b0d281d20e4',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/api/GenericV2CutoverController.kt': '76b203af5028c0207aaa5cea69917672ac42545a40a9c9d86ac0aec2e0b058ce',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/api/dto/InitialSourceCatalogReceiptResponse.kt': 'ea1077fa34aed836f40689e82c637347524302c0dab9052b281553b3d16988a2',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/application/BundledImportService.kt': '7ca4e4896b9138df41ed7681705fe0d47103d697b80543df9d76dbec8379b1b6',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/application/DocumentAssemblyService.kt': '1dce418396abe743a70a2a1156cb843978883a6629e3030cf73aadd3a85e885f',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/application/GenericV2CutoverService.kt': '33c118e558fdd8ab8230e068c5445dd1ca0527bdf3059ab51cf65433631d6f01',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/application/SourceAdminService.kt': '7bed1600540175d0cb3dbd355c5d975b37a35e3890a9278d04e22b676222cedd',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/domain/InitialSourceCatalogPolicy.kt': '23d53cc1ee42ef25c31f1a887938c269076416ff9839ae7b9919fbb3fea46966',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/domain/InitialSourceCatalogState.kt': 'e9743c5043705f3dc71891961635034d62a379f23daa1ac5be0f28f2b2ef5319',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/domain/PublishedDocumentRepository.kt': 'b5a86110acca52c8c37d9cf2b9fac424c69461246f14c870a585e968afe0453c',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/ClasspathInitialSourceCatalogPolicy.kt': '78d3767b580c3df392f8a54654b9ed5442a92da40d6e2a3c5026110915a40e60',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/DocumentPublicationStateEntity.kt': '89829545f064e80d0efa7ce37aec78b346717b9263f6b759cb0b61e74f5771ef',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/JpaPublishedDocumentRepositoryAdapter.kt': 'f3a9341cec57e54fc6f8a9fe5a4e0831b943a9f32d50fb07972ddff41e5b1409',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/PublicationStateStartupValidator.kt': 'dc1f72dbe2605714ccf582bb9cae8c55dde1bf14603011f48d1d4db8d1af8313',
    'src/main/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/SpringDataDocumentPublicationStateRepository.kt': 'fc17599298b36371faa644c6529b7259156c55a8da6067de21f9d381dec5230f',
    'src/main/resources/db/migration/V13_2__source_catalog_bootstrap_state.sql': 'f3b283507efe057ff15516060c02b27908449f60ab7a03f757a2747d75930045',
    'src/main/resources/source-config/bootstrap/app-bundle-v6-generic.json': '42a26ca29182a0c8c1150196ff55979fc41a8d828ed60556e9dcf6062b8b9095',
    'src/test/kotlin/me/manga/kira/backend/common/web/RequestBodySizeLimitFilterTest.kt': 'e01a0073e70bdc391aa476548bd19546add85a7d70f35ffa0dcbbeaaf3425b09',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/FlywayIncrementalOrderIT.kt': '43ead5ba258d45e3cdcfbe804d33aab6ff181beba7cd457b22730b25eabea476',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/FlywayMigrationIT.kt': 'b58412530ff4130d9563202d5419437ed62a557a0198d7b5e2fc9562848d1d13',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/InitialSourceCatalogFixtures.kt': '9ffa510f535e7361b1f28eb3a118823004f9e72d33a36ea437691f5f7a5863d3',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/StartupConsistencyIT.kt': '5e06db961ddd35c5c55720c799e6be8c0a12e517b4472bddb2d04efb2f1de34b',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/AbstractAdminSourceIT.kt': '757ca4c2c54b59365259340f245c8ddef523bea6aa9a728c09d35b6dc875f212',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/AuditLogIT.kt': 'f06196caaa7d99c91d585cd513ba9538f05f35aecf43c4c2bbe0cc927050d519',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/BootstrapConcurrencyIT.kt': 'f54345069b0c2099c491f2816adb636471b59ca173833869e1f92f21acf0c5ae',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/BootstrapEndpointIT.kt': 'c9a75f08230a464b5e8bfa67ed0ed32b09a1dffa5bbbb146429fcef348491f44',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/BootstrapLateRollbackIT.kt': '01b0a7b769b3b67f6e7820cdcec9bb2ecc5b07d976f54aa7981058ef2ba2581b',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/BootstrapPublicationGuardIT.kt': '3ed1c1cf5abe622a93189b52b8bd61e5752981b43afec9e750ba90dd84bc7d1e',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/BootstrapReplayIT.kt': '3073f0bf57ac546110c6f460c361a92cb460d37da323cc202cc5fbe6d8541008',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/ConcurrentDifferentSourcePublishIT.kt': '9c94cf3f082a087f6ce509d8451044f31286113afa93f542fde8f142bf8c7385',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/ConcurrentSameSourcePublishIT.kt': '88ed6aeb19bd0476d41776cf10172662f2369ffe517be333f88fe74ce113fefd',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/DisableRemoveVisibilityIT.kt': '2100d6eb53b6d4142bbaee4e30d098999f036841bafa9f873e15069a55573db6',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/DocumentOrderDeterminismIT.kt': '6ab5c46e1eb0f8b73414e1629183a9d98214f5db6c29185dd49489cea853982e',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/EmptyDocumentPublishIT.kt': 'd90eaf8819f23490f9f9c0094a257bf1be4989fca0328e31b9ab74e57fa09e19',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/EndpointCompletenessIT.kt': '8e0c1f5d221929cfaa4d06ebc90c5219c4fc72bc863690324f45c397a356aff5',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/FullBundledParityIT.kt': '35c1a00ae1359ba64ae90feb4ce4c3269786c1186759369258abf8b6dc3e84e7',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/ImportBundledIT.kt': '1bc6a6406619facba5454fbc52d252846dcbcfbbeb03ba327ccbba7b3b1eaf01',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/ImportCreatesSingleSnapshotIT.kt': '279a19ec00a9f6c48af0cb08ea3ab388b3fd034027932bb9f1f10df466532771',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/ImportNoChangesIsNoOpIT.kt': '02ae637387b85f7e64ff121037392d5d4fe2f99042d07a0b74982ff839d92d97',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/LifecycleNeutralStorageIT.kt': '361e7c5a718fdc1302d19d981884d48d0ce152619344715b1ec3e61cedf32022',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/PublicConfigSecretsRejectedIT.kt': 'c1646d0eb17fcc781038bee44dd6837a9665adfe17bc303e924f933ae40a19da',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/PublicationFailureRollbackIT.kt': '0a9c8c585274264df766fcf2e6f4b76dba06c329e18dadfa97298fd5eb78e59e',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/PublishInvalidFailsIT.kt': 'bcfea31adcc76410828bfbf4a7befcb4b8c9e052e1197bdf28e014253d27bff0',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/PublishStateRulesIT.kt': '1a77ab51e4a0ce31eb4ccb62dd2ac953d0658f6a08fa0a1f3606cae6df684b22',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/RemovedCannotReturnIT.kt': 'a7e3f612a227ec9ba826b5387fb38c53ac13186de5802c2314f5ed236c4f4bf4',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/RetiredSourceVisibilityIT.kt': 'd52af4a7c653910e6692be522cf1d7bdb25b40602d53bb7523835799ac34b651',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/RollbackIT.kt': '0955d55d4f6280b71283f60a627237ac24de5e5e498d152f04d41199ed54269f',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/ServerManagedLifecycleIT.kt': 'c60f9a818513cfb36e814b06fd77097f9fb070e82ac5dafb0f9390195e99d893',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/SnapshotTimestampConsistencyIT.kt': '1d339de4a9b7ead1b0ac3649f5e976cc8a9a9fe023275770d44e77feaa9ca5a5',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/SourceChangesetIT.kt': '427f7eda67a55df068688abc73c41366e638d5aaf08b7062e21c42d743e1e7a6',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/SourceEditorDraftIT.kt': 'a26764c204b98fe78221ddbdaed55d810c487256ecb1d3effd6858fb3e5595d6',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/SourceOperationalModeIT.kt': 'f0fd722742abc297b25d1e8ffdf2ba9cbdb8a2d3b1b06b41823c1e71ed3b57d7',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/SourcePublishFlowIT.kt': '2f1d50b6cfee2128d9b48cb8671254af7f281356b06cb9e573cb00de6fd23c10',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/admin/StrictAdminParserIT.kt': '780ba482d3bb92d46a41167adf38bca8446d48a2ede15862ce0b1b1dba0fbd27',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/api/GenericV2CutoverControllerTest.kt': '5463c7cf1fcba65a24186259511d5103ed2c64469fa91b152906cd1bda1bbe2b',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/domain/InitialSourceCatalogPolicyTest.kt': '1cef40d03932ada4fa61d85c6f77524c48d991e612a8e97220c7b824bf1c4b9a',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/infrastructure/AdminHistoryRepositoryIT.kt': '786bac5a93a345a6c5d764ca740c797a7f882f86119952815fbaf0a3935c8f94',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/ETagIT.kt': '6d33e2702a5c74da8aa7c606915bb8196a134af8086d3a418e87aa367641c317',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/IfNoneMatchVariantsIT.kt': 'cbec6825b348256556cfca5bd4742bc74f743cc7ba8f2ab2cde2c17027b3e34f',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/PublicSourceSummaryConsistencyIT.kt': '9bcb7727fd0064a32814ba0c1a6afc814809576edf45f10e1b10f5732aa90699',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/PublicSourcesIT.kt': 'fa3fd72b7f8aabbc8592e3f2271ef8d1e4773c01a2d5e7e3631c3b9608e962f2',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/RawBytesChecksumIT.kt': 'd0dcb4d9cffc2ca54d881081374db384ef72a38fa23bae5355efd93b20272a5a',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/public/SourceCatalogV2IT.kt': 'a1053ba8636947d3ffb69cd3da34af233ea544e9301b47b699f6bd8fe1cb8d93',
    'src/test/kotlin/me/manga/kira/backend/sourceconfig/signing/SignedDocumentIT.kt': 'f99e5bffe90d329b7f945a437f47690f27461b8c85b295e486fe30257e3e6f05',
    'src/test/kotlin/me/manga/kira/backend/support/AbstractIntegrationTest.kt': 'b39a14d78dcfe1385b03e69d56b7aa7f4b45b7a3c48b0b5e6970154231a21496',
    'src/test/kotlin/me/manga/kira/backend/user/SecurityMatrixIT.kt': '65eca9e5da8e2174916de2bf631d365e65bb7322dd5e2066a1efe25404505539',
}
REFERENCE_RESOURCE = 'source-config/bootstrap/app-bundle-v6-generic.json'
REFERENCE_SHA = '42a26ca29182a0c8c1150196ff55979fc41a8d828ed60556e9dcf6062b8b9095'
# This small extra init leaves the pinned dependency/ownership helper unchanged. It witnesses
# the actual test task's classpath before its selected tests, not a Boot jar or provider run.
REFERENCE_INIT = r'''import groovy.json.JsonOutput
import java.net.URLClassLoader
import java.security.MessageDigest
import org.gradle.api.tasks.testing.Test
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension

gradle.projectsEvaluated {
    def p = gradle.rootProject
    p.tasks.named('test', Test).configure {
        extensions.getByType(JacocoTaskExtension).enabled = false
        doFirst {
            def resource = '@REFERENCE_RESOURCE@'
            def expected = '@REFERENCE_SHA@'
            def source = p.file('src/main/resources/' + resource).canonicalFile
            def processed = new File(p.layout.buildDirectory.get().asFile, 'resources/main/' + resource).canonicalFile
            def urls = classpath.files.collect { it.toURI().toURL() } as URL[]
            def digest = { bytes -> MessageDigest.getInstance('SHA-256').digest(bytes).encodeHex().toString() }
            def receipt = [test_task: path, resource: resource, expected_sha256: expected,
                source_path: source.path, processed_path: processed.path,
                classpath: urls.collect { it.toExternalForm() }, accepted: false]
            def loader = new URLClassLoader(urls, (ClassLoader) null)
            try {
                receipt.source_sha256 = digest(source.bytes)
                receipt.processed_sha256 = digest(processed.bytes)
                def resources = Collections.list(loader.getResources(resource))
                receipt.resolved_resources = resources.collect { it.toExternalForm() }
                if (resources.size() == 1) {
                    receipt.loaded_sha256 = resources[0].openStream().withCloseable { digest(it.bytes) }
                }
                receipt.accepted = receipt.source_sha256 == expected && receipt.processed_sha256 == expected &&
                    receipt.loaded_sha256 == expected && receipt.resolved_resources == [processed.toURI().toURL().toExternalForm()]
                if (!receipt.accepted) throw new GradleException('Backend20 bootstrap reference source/processed/classpath loading mismatch')
            } finally {
                try { loader.close() } finally {
                    new File(System.getenv('W01_RUN'), 'bootstrap-reference-resource.json').text = JsonOutput.prettyPrint(JsonOutput.toJson(receipt)) + '\n'
                    println('BACKEND20_BOOTSTRAP_REFERENCE ' + JsonOutput.toJson(receipt))
                }
            }
        }
    }
}
'''.replace('@REFERENCE_RESOURCE@', REFERENCE_RESOURCE).replace('@REFERENCE_SHA@', REFERENCE_SHA)
OWNED_CHILDREN_SHA = '56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385'
PREFIX = 'review/working/app-29-w01-local-dependencies-20260905/'
ARCHIVE_SHA = 'da94218f74eb0f5831241c8606c8f82142e49b818acfaff027a78f2efe77faab'
MANIFEST_SHA = 'c67fcc5fe64a9a795373c4683c7c1edd6407146e3cd07609fa7018a8a98db79a'
INIT_SHA = '429961b98254b89f7ce1d7ba1efa61b8cba28a3bae35353bf3a8ba85f4a1c839'

def note(message):
    print(message, flush=True)
    with (REPORTS / 'result.log').open('a') as log: log.write(message + '\n')

OWNER, CANCELLED, DRAINS = None, False, []
def interrupted(signum, frame):
    global CANCELLED
    CANCELLED = True  # Do not interrupt Popen construction/registration or the finite cleanup phase.
signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)

# Observe actual available bytes, not total capacity or a guessed alternate Docker daemon.
MIN_FREE_BYTES, SPACE_POLL_SECONDS = 8 * 1024**3, 1.0
SPACE_PATHS = [BACKEND, RUN, REPORTS, HOME, W01, TEMP]
SPACE_FAILURE, SPACE_CHECKS, SPACE_NEXT = None, 0, 0.0
SPACE_MINIMUM = {}

def space_ok(phase, force=False):
    global CANCELLED, SPACE_FAILURE, SPACE_CHECKS, SPACE_NEXT
    if SPACE_FAILURE is not None: return False  # Failure stays sticky through cleanup.
    now = time.monotonic()
    if not force and now < SPACE_NEXT: return True
    SPACE_NEXT = now + SPACE_POLL_SECONDS
    observation = {'phase': phase, 'monotonic': now, 'floor_bytes': MIN_FREE_BYTES, 'devices': {}}
    failure = None
    try:
        for path in SPACE_PATHS:
            info = path.stat()
            if not path.is_dir(): raise OSError('Space-observation path is not a directory')
            device = str(info.st_dev)
            if device not in observation['devices']:
                fs = os.statvfs(path)
                free = fs.f_bavail * fs.f_frsize
                observation['devices'][device] = {'available_bytes': free, 'paths': []}
                SPACE_MINIMUM[device] = min(SPACE_MINIMUM.get(device, free), free)
                if free < MIN_FREE_BYTES:
                    failure = {'reason': 'below-eight-GiB', 'phase': phase, 'device': device, 'available_bytes': free}
            observation['devices'][device]['paths'].append(str(path))
    except OSError as problem:
        failure = {'reason': 'space-measurement-unavailable', 'phase': phase, 'error_type': type(problem).__name__, 'errno': problem.errno}
    SPACE_CHECKS += 1
    observation['failure'] = failure
    try:
        with (REPORTS / 'disk-space.jsonl').open('a') as log: log.write(json.dumps(observation, sort_keys=True) + '\n')
    except OSError as problem:
        failure = {'reason': 'space-evidence-unavailable', 'phase': phase, 'error_type': type(problem).__name__, 'errno': problem.errno}
    if failure is not None:
        SPACE_FAILURE, CANCELLED = failure, True  # Existing cancellation/drain/finally path owns stopping.
    return SPACE_FAILURE is None

def drain(name):
    global cleanup_failed
    try: receipt = OWNER.drain() if OWNER is not None else {'ok': False, 'spawned': False, 'reason': 'subreaper/child-list capability not established'}
    except (Exception, KeyboardInterrupt) as failure: receipt = {'ok': False, 'error': str(failure)}
    DRAINS.append({'phase': name, **receipt})
    note(name + ': ' + json.dumps(receipt, sort_keys=True))
    # Successful forced cleanup is not proof that a validation worker ended normally.
    normal = receipt['ok'] and not receipt.get('term') and not receipt.get('kill')
    cleanup_failed |= not normal
    return receipt['ok']  # Actual absence still permits safe scoped deletion on a failed batch.

def command(argv, name, seconds=30, extra=None, cleaning=False):
    global started
    with (REPORTS / 'commands.log').open('a') as log: log.write(json.dumps({'argv': argv, 'cwd': str(BACKEND), 'seconds': seconds, 'env_overrides': extra}) + '\n')
    # Refuse a new workload before Popen; cleanup remains possible after cancellation/low space.
    if not cleaning and (not space_ok('prelaunch-' + name, force=True) or CANCELLED):
        reason = 'disk_floor' if SPACE_FAILURE is not None else 'cancelled'
        result = 125 if reason == 'disk_floor' else 124
        (REPORTS / (name + '.log')).write_text('NOT SPAWNED: ' + reason + '\n')
        with (REPORTS / 'commands.log').open('a') as log:
            log.write(json.dumps({'log': name, 'pid': None, 'actual_exit': None, 'policy_result': result, 'terminal_reason': reason}) + '\n')
        return result
    with (REPORTS / (name + '.log')).open('wb') as log:
        process = OWNER.track(subprocess.Popen(argv, cwd=BACKEND, env=ENV | (extra or {}), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        if name == 'gradle-test': started = True  # Stops/container cleanup are owed only after an actual launch.
        deadline = time.monotonic() + seconds
        while process.poll() is None and time.monotonic() < deadline and (cleaning or not CANCELLED):
            if not cleaning and not space_ok('inflight-' + name): break
            time.sleep(0.05)
        if not cleaning: space_ok('postwait-' + name, force=True)
        terminal_reason = ('disk_floor' if SPACE_FAILURE is not None and not cleaning else
                           ('cancelled' if CANCELLED and not cleaning else
                            ('deadline' if time.monotonic() >= deadline or process.returncode is None else None)))
        if terminal_reason is not None: drain('interrupted-' + name)
        result = 125 if terminal_reason == 'disk_floor' else (124 if terminal_reason is not None else process.returncode)
    with (REPORTS / 'commands.log').open('a') as log: log.write(json.dumps({'log': name, 'pid': process.pid, 'actual_exit': process.returncode, 'policy_result': result, 'terminal_reason': terminal_reason}) + '\n')
    return result

def require(condition, message):
    if not condition: raise RuntimeError(message)

def verify_source_pins(phase):
    observed = {}
    try:
        for relative in EXPECTED_SOURCE_SHA256:
            path = BACKEND / relative
            observed[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else None
    finally:
        (REPORTS / ('source-pins-' + phase + '.json')).write_text(json.dumps(observed, indent=2) + '\n')
    require(observed == EXPECTED_SOURCE_SHA256, 'Backend20 source pins differ: ' + phase)

result, started, before, cleanup_failed, project_caches = 1, False, None, False, []
gradle_exit, xml_verified, sources_clean, preserved, containers_absent = None, False, False, False, None
container_force_requested = False
xml_observations, static_reports = [], {}
reference_source_sha, reference_observation, reference_verified = None, {}, False
source_pins_before_verified, source_pins_after_verified = False, False
try:
    require(set(TARGETS) == {'authorization', 'authorized', 'runAllowed', 'backend_sha', 'classes', 'methods', 'status'}, 'Unexpected request fields')
    require(TARGETS['authorization'] == 'BACKEND20_ONE_TARGETED_BATCH_AUTHORIZED', 'Draft is not authorized')
    require(TARGETS['authorized'] is True and TARGETS['runAllowed'] is True, 'Execution is explicitly disabled')
    require(os.environ.get('GITHUB_REPOSITORY') == 'kira-manga/kira-admin' and
            os.environ.get('GITHUB_REF') == 'refs/heads/remediation/app-29-backend-complaints' and
            os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Wrong carrier/event or rerun')
    require(hashlib.sha256((ADMIN / 'ci/app29_owned_children.py').read_bytes()).hexdigest() == OWNED_CHILDREN_SHA, 'Owned-child utility changed')
    from app29_owned_children import OwnedChildren
    OWNER = OwnedChildren()  # Refuse unavailable subreaping before the first command.
    target = TARGETS['backend_sha']
    require(CLASSES == EXPECTED_CLASSES and all(type(count) is int for count in CLASSES.values()) and
            METHODS == EXPECTED_METHODS, 'Invalid exact Backend20 class/count/method selection')
    note('Primary-bound request: ' + json.dumps(TARGETS, sort_keys=True))
    require(isinstance(target, str) and re.fullmatch('[0-9a-f]{40}', target) and target != '0' * 40 and
            target == EXPECTED_BACKEND_SHA, 'Unbound or unexpected backend target')
    require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha') == 0, 'Cannot read backend SHA')
    require((REPORTS / 'backend-sha.log').read_text().strip() == target, 'Backend checkout SHA mismatch')
    require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-before') == 0 and
            not (REPORTS / 'source-before.log').read_text().strip(), 'Backend checkout is not clean')
    require(command(['git', '-C', str(ADMIN), 'rev-parse', 'HEAD'], 'admin-sha') == 0, 'Cannot read Admin SHA')
    require((REPORTS / 'admin-sha.log').read_text().strip() == os.environ.get('GITHUB_SHA'), 'Carrier checkout SHA mismatch')
    verify_source_pins('before')
    source_pins_before_verified = True
    reference_source_sha = hashlib.sha256((BACKEND / 'src/main/resources' / REFERENCE_RESOURCE).read_bytes()).hexdigest()
    note('Source bootstrap reference SHA256: ' + reference_source_sha)
    require(reference_source_sha == REFERENCE_SHA, 'Backend20 source bootstrap reference differs from the reviewed bytes')
    for name in ('.gradle', '.kotlin'): require(not (BACKEND / name).exists(), 'Unexpected preexisting project cache: ' + name)
    project_caches = [BACKEND / '.gradle', BACKEND / '.kotlin']
    require(space_ok('before-private-inputs', force=True), 'Insufficient or unknown free space before private inputs')
    archive = ADMIN / 'docs/remediation/checkpoint-2026-09-08/review-evidence.tar.gz'
    with archive.open('rb') as stream: require(hashlib.file_digest(stream, 'sha256').hexdigest() == ARCHIVE_SHA, 'Private archive hash mismatch')
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()  # Headers only; never extractall, links, or unrelated payloads.
        def member(name, digest, limit=16 * 1024 * 1024):
            matches = [m for m in members if m.name == name]
            require(len(matches) == 1 and matches[0].isfile() and 0 <= matches[0].size <= limit, 'Invalid allowlisted archive member: ' + name)
            data = bundle.extractfile(matches[0]).read(limit + 1)
            require(len(data) == matches[0].size and hashlib.sha256(data).hexdigest() == digest, 'Archive member hash mismatch: ' + name)
            return data
        manifest = member(PREFIX + 'local-inputs.sha256', MANIFEST_SHA, 16384)
        entries = [line.split('  ', 1) for line in manifest.decode('ascii').splitlines()]
        require(len(entries) == 18 and all(len(e) == 2 for e in entries), 'Expected exactly 18 input records')
        require(len({e[1] for e in entries}) == 18, 'Duplicate local input')
        (W01 / 'local-inputs.sha256').write_bytes(manifest)
        (W01 / 'original.init.gradle').write_bytes(member('review/working/app-29-w01-local-dependencies.init.gradle', INIT_SHA, 16384))
        for digest, relative in entries:
            path = PurePosixPath(relative)
            require(re.fullmatch('[0-9a-f]{64}', digest) and not path.is_absolute() and '..' not in path.parts and '\\' not in relative and relative.startswith('me/manga/kira/source/'), 'Unsafe input path')
            require(space_ok('private-input-' + relative, force=True), 'Free-space floor failed during input preparation')
            destination = W01 / 'repository' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(member(PREFIX + 'repository/' + relative, digest))
    note(f'Private inputs verified: archive={ARCHIVE_SHA} manifest={MANIFEST_SHA} init={INIT_SHA}; 18 inputs')
    (W01 / 'bootstrap-reference.init.gradle').write_text(REFERENCE_INIT)
    require(command(['java', '-XshowSettings:properties', '-version'], 'java-version') == 0, 'JDK settings/version command failed')
    java_tmp = re.findall(r'^\s*java\.io\.tmpdir\s*=\s*(.*?)\s*$', (REPORTS / 'java-version.log').read_text(), re.MULTILINE)
    require(java_tmp == [str(TEMP)], 'JVM temp escaped the owned directory; no batch started')
    require(not ENV.get('DOCKER_CONTEXT'), 'Docker context override would invalidate local storage observation')
    require(command(['docker', 'version'], 'docker-version') == 0, 'Docker unavailable; no runtime installation attempted')
    require(command(['docker', 'info', '--format', '{{json .DockerRootDir}}'], 'docker-storage-root') == 0, 'Cannot identify actual Docker storage')
    docker_storage = json.loads((REPORTS / 'docker-storage-root.log').read_text())
    require(isinstance(docker_storage, str) and Path(docker_storage).is_absolute(), 'Invalid Docker storage root')
    SPACE_PATHS.append(Path(docker_storage))
    require(space_ok('actual-docker-storage', force=True), 'Docker storage free space is insufficient or unknown')
    require(command(['docker', 'ps', '-aq', '--no-trunc'], 'preexisting-containers', extra={'DOCKER_API_VERSION': '1.32'}) == 0, 'Docker API 1.32 unsupported/unavailable; refusing without adaptation')
    before = set((REPORTS / 'preexisting-containers.log').read_text().splitlines())
    require(not before, 'Expected a dedicated clean hosted runner; do not touch preexisting containers')
    require(not CANCELLED, 'Cancelled before validation')
    selectors = [name + '.' + method for name in CLASSES for method in METHODS[name]]
    tasks = ['compileKotlin', 'compileTestKotlin', 'test'] + [part for name in selectors for part in ('--tests', name)] + ['ktlintMainSourceSetCheck', 'detekt', '--continue', '-x', 'jacocoTestReport']
    gradle_exit = command(['./gradlew', '--no-daemon', '--no-parallel', '--no-configuration-cache', '--console=plain', '--max-workers=1', '--no-build-cache', '-Dorg.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m', '-Dorg.gradle.vfs.watch=false', '-Pkotlin.compiler.execution.strategy=in-process', '--init-script', str(W01 / 'original.init.gradle'), '--init-script', str(W01 / 'bootstrap-reference.init.gradle'), *tasks], 'gradle-test', 18 * 60)
    result = gradle_exit
except (Exception, KeyboardInterrupt) as failure:
    note('FAIL: ' + str(failure))
    result = 1
finally:
    def cleanup_command(argv, name):
        global cleanup_failed
        try:
            ok = command(argv, name, seconds=60 if argv == ['./gradlew', '--stop'] else 30, cleaning=True) == 0
            cleanup_failed |= not ok
            return ok
        except (Exception, KeyboardInterrupt) as failure:
            cleanup_failed = True
            note('CLEANUP FAIL: ' + str(failure))
            return False
    if started: cleanup_command(['./gradlew', '--stop'], 'gradle-stop-immediate')
    workers_gone = drain('after-immediate-stop')
    try:
        xmls = list((W01 / 'backend-build/test-results/test').glob('*.xml'))
        for xml in xmls: shutil.copyfile(xml, REPORTS / xml.name)
        for tool in ('ktlint', 'detekt'):
            directory = W01 / 'backend-build/reports' / tool
            files = [p for p in directory.rglob('*') if p.is_file()] if directory.exists() else []
            files += list((W01 / 'backend-build/reports').glob(tool + '.*'))
            static_reports[tool] = []
            for path in files:
                if path.suffix in ('.xml', '.txt', '.html'):
                    destination = REPORTS / ('static-' + tool + '-' + path.name)
                    require(not destination.exists(), 'Ambiguous static report filename')
                    shutil.copyfile(path, destination)
                    static_reports[tool].append(destination.name)
        for filename in ('bootstrap-reference.init.gradle', 'bootstrap-reference-resource.json'):
            if (W01 / filename).is_file(): shutil.copyfile(W01 / filename, REPORTS / filename)
        preserved = True  # Missing output is reported below; a failed copy forbids its deletion.
        processed_reference = W01 / 'backend-build/resources/main' / REFERENCE_RESOURCE
        source_reference = BACKEND / 'src/main/resources' / REFERENCE_RESOURCE
        reference_observation = {'settled': workers_gone, 'expected_sha256': REFERENCE_SHA, 'source_before_sha256': reference_source_sha,
                           'source_after_sha256': hashlib.sha256(source_reference.read_bytes()).hexdigest() if source_reference.is_file() else None,
                           'processed_sha256': hashlib.sha256(processed_reference.read_bytes()).hexdigest() if processed_reference.is_file() else None}
        resource_receipt = REPORTS / 'bootstrap-reference-resource.json'
        try: reference_observation['witness'] = json.loads(resource_receipt.read_text()) if resource_receipt.is_file() else None
        except Exception as failure: reference_observation['witness_error'] = str(failure)
        note('Raw bootstrap reference observation: ' + json.dumps(reference_observation, sort_keys=True))
        for xml in xmls:
            try:
                suite = ET.parse(REPORTS / xml.name).getroot()
                cases = suite.findall('testcase')
                observation = {'file': xml.name, 'suite': suite.attrib, 'settled': workers_gone, 'cases': []}
                for case in cases:
                    status = 'UNKNOWN_UNSETTLED' if not workers_gone else next((tag.upper() for tag in ('failure', 'error', 'skipped') if case.find(tag) is not None), 'PASS')
                    observation['cases'].append({'classname': case.get('classname'), 'name': case.get('name'), 'status': status})
                xml_observations.append(observation)
                note('Raw XML observation: ' + json.dumps(observation, sort_keys=True))
            except Exception as failure:
                xml_observations.append({'file': xml.name, 'status': 'UNREADABLE', 'error': str(failure)})
        require(workers_gone, 'XML/source results are unsettled; owned workers remain or absence is unknown')
        require({p.name for p in xmls} == {'TEST-' + name + '.xml' for name in CLASSES}, 'Missing/unexpected focused XML')
        for name, expected in CLASSES.items():
            suite = ET.parse(REPORTS / ('TEST-' + name + '.xml')).getroot()
            cases = suite.findall('testcase')
            require(suite.tag == 'testsuite' and suite.get('name') == name and int(suite.get('tests', '-1')) == len(cases) == expected and all(int(suite.get(k, '-1')) == 0 for k in ('failures', 'errors', 'skipped')), 'Focused XML totals differ: ' + name)
            identities = [(case.get('classname'), case.get('name')) for case in cases]
            require(len(set(identities)) == expected and all(cls == name and method for cls, method in identities), 'Wrong/duplicate testcase identity')
            require(not any(node.tag in ('failure', 'error', 'skipped') for node in suite.iter()), 'Failure/error/skip in focused XML')
            require({method for _, method in identities} == set(EXPECTED_CASES[name]), 'Wrong Backend20 testcase identities: ' + name)
        xml_verified = True
        witness = reference_observation.get('witness') or {}
        # java.io.File.toURI().toURL() spells local URLs file:/..., not pathlib's file:///....
        processed_url = processed_reference.resolve().as_uri().replace('file:///', 'file:/', 1)
        require(reference_source_sha == REFERENCE_SHA and reference_observation['source_after_sha256'] == REFERENCE_SHA and
                reference_observation['processed_sha256'] == REFERENCE_SHA and witness.get('accepted') is True and
                witness.get('test_task') == ':test' and witness.get('resource') == REFERENCE_RESOURCE and
                all(witness.get(field) == REFERENCE_SHA for field in ('expected_sha256', 'source_sha256', 'processed_sha256', 'loaded_sha256')) and
                witness.get('resolved_resources') == [processed_url], 'Missing/mismatched source, processed or loaded bootstrap reference evidence')
        reference_verified = True
        require(all(static_reports.get(tool) for tool in ('ktlint', 'detekt')), 'Missing static reports')
        require(command(['git', 'rev-parse', 'HEAD'], 'backend-sha-after', cleaning=True) == 0 and
                (REPORTS / 'backend-sha-after.log').read_text().strip() == TARGETS['backend_sha'], 'Backend SHA changed during validation')
        require(command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'source-after', cleaning=True) == 0 and
                not (REPORTS / 'source-after.log').read_text().strip(), 'Backend source changed during validation')
        verify_source_pins('after')
        source_pins_after_verified = True
        sources_clean = True
    except Exception as failure:
        note('REPORT FAIL: ' + str(failure))
        result = result or 1
    if started and before is not None and workers_gone:
        if cleanup_command(['docker', 'ps', '-aq', '--no-trunc', '--filter', 'label=org.testcontainers=true'], 'remaining-testcontainers'):
            owned = sorted(set((REPORTS / 'remaining-testcontainers.log').read_text().splitlines()) - before)
            if all(re.fullmatch('[0-9a-f]{64}', cid) for cid in owned) and drain('before-owned-container-delete'):
                if owned:
                    container_force_requested = cleanup_failed = True
                    note('FORCED container cleanup requested; proved absence will not qualify as normal completion')
                    cleanup_command(['docker', 'rm', '-fv', *owned], 'remove-owned-testcontainers')
                if cleanup_command(['docker', 'ps', '-aq', '--no-trunc', '--filter', 'label=org.testcontainers=true'], 'testcontainers-after-cleanup'):
                    containers_absent = not bool(set((REPORTS / 'testcontainers-after-cleanup.log').read_text().splitlines()) - before)
                    cleanup_failed |= not containers_absent
            else:
                cleanup_failed = True
                note('CLEANUP FAIL: invalid container ID or unsettled ownership; no container deletion')
    containers_safe = not started or containers_absent is True
    files_safe = workers_gone and drain('after-docker-before-files') and preserved and containers_safe
    if not containers_safe: note('RETAINING owned outputs/home/temp/project caches: container absence not proved')
    elif not files_safe: note('RETAINING owned outputs/home/temp/project caches: process absence or report preservation not proved')
    for directory in ((W01, TEMP, *(project_caches if started else [])) if files_safe else ()):
        try:
            if directory.exists(): shutil.rmtree(directory)
        except Exception as failure:
            cleanup_failed = True
            note('SCOPED CLEANUP FAIL: ' + str(failure))
    try: TEMP.mkdir(mode=0o700, exist_ok=True)  # Keep an empty owned temp path for the final JVM stop.
    except Exception as failure:
        cleanup_failed = True
        note('FINAL STOP TEMP FAIL: ' + str(failure))
    if started: cleanup_command(['./gradlew', '--stop'], 'gradle-stop-final')
    home_safe = drain('after-final-stop-before-home')
    try:
        if files_safe and home_safe:
            shutil.rmtree(HOME)
            shutil.rmtree(TEMP)
        else: note('RETAINING private home/temp: combined ownership or report preservation not proved; runner disposal is not a join claim')
    except Exception as failure:
        cleanup_failed = True
        note('GRADLE HOME CLEANUP FAIL: ' + str(failure))
    outputs_absent = not any(path.exists() for path in (W01, HOME, TEMP, *project_caches))
    cleanup_failed |= not outputs_absent or (started and containers_absent is not True)
    process_status = 'UNKNOWN_OR_INCOMPLETE' if any(not item['ok'] for item in DRAINS) else ('FORCED' if any(item.get('term') or item.get('kill') for item in DRAINS) else 'COMPLETE')
    container_status = 'NOT_STARTED' if not started else ('UNKNOWN' if containers_absent is None else ('PRESENT' if not containers_absent else ('FORCED' if container_force_requested else 'COMPLETE')))
    ownership_status = 'UNKNOWN_OR_INCOMPLETE' if process_status == 'UNKNOWN_OR_INCOMPLETE' or container_status in ('UNKNOWN', 'PRESENT') else ('FORCED' if process_status == 'FORCED' or container_status == 'FORCED' else 'COMPLETE')
    passed = result == 0 and gradle_exit == 0 and xml_verified and reference_verified and sources_clean and preserved and ownership_status == 'COMPLETE' and not cleanup_failed and not CANCELLED and source_pins_before_verified and source_pins_after_verified and SPACE_CHECKS > 0 and SPACE_FAILURE is None
    note(f'validation_result={result}; process_ownership={process_status}; container_ownership={container_status}; ownership={ownership_status}; cleanup_failed={cleanup_failed}; cancelled={CANCELLED}; job_exit={0 if passed else 1}')
    (REPORTS / 'result.json').write_text(json.dumps({'backend_sha': TARGETS['backend_sha'], 'carrier_sha': os.environ.get('GITHUB_SHA'), 'classes': CLASSES, 'methods': METHODS, 'gradle_exit': gradle_exit, 'validation_exit': result, 'xml_verified': xml_verified, 'xml': xml_observations, 'static_reports': static_reports, 'reference_verified': reference_verified, 'reference': reference_observation, 'scope': 'TARGETED_BOOTSTRAP_TEST_EVIDENCE_ONLY; not deployment, reconciliation/adoption or full Backend20 acceptance', 'sources_clean': sources_clean, 'source_pins_before_verified': source_pins_before_verified, 'source_pins_after_verified': source_pins_after_verified, 'disk_space': {'floor_bytes': MIN_FREE_BYTES, 'poll_seconds': SPACE_POLL_SECONDS, 'observations': SPACE_CHECKS, 'minimum_available_by_device': SPACE_MINIMUM, 'failure': SPACE_FAILURE, 'receipt': 'disk-space.jsonl'}, 'serialization': {'hosted_concurrency_group': 'backend11-private-completion-leases', 'primary_host_lock': 'PRIMARY_OWNED_EXTERNAL_PREREQUISITE; not observed by this VM'}, 'reports_preserved': preserved, 'drains': DRAINS, 'process_ownership_status': process_status, 'container_ownership_status': container_status, 'ownership_status': ownership_status, 'cleanup_failed': cleanup_failed, 'containers_absent': containers_absent, 'container_force_requested': container_force_requested, 'cancelled': CANCELLED, 'outputs_absent': outputs_absent, 'status': 'PASS' if passed else 'FAIL'}, indent=2) + '\n')
raise SystemExit(0 if passed else 1)
