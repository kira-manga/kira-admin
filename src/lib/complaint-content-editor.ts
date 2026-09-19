/**
 * Local content-preparation models, not wire DTOs or an HTTP/authentication boundary.
 * Callers supply structurally valid, already verified snapshots. IDs and action tags
 * stay opaque: this module neither authenticates them nor parses a numeric version.
 */
export type ComplaintContentType = 'TECHNICAL' | 'LANGUAGES' | 'SITES_ADD' | 'SITE_ERROR' | 'FEATURES' | 'CUSTOM';

type OrdinaryContent = { type: ComplaintContentType; subject: string; body: string };
type NoticeReplyContent = { body: string };

type OrdinarySnapshot = Readonly<{
  variant: 'ordinary';
  kind: 'REPORT' | 'REPLY';
  id: string;
  actionTag: string;
  content: Readonly<OrdinaryContent>;
}>;

type NoticeReplySnapshot = Readonly<{
  variant: 'notice-reply';
  kind: 'REPLY';
  id: string;
  actionTag: string;
  content: Readonly<NoticeReplyContent>;
}>;

export type ComplaintContentSnapshot =
  | OrdinarySnapshot
  | NoticeReplySnapshot
  | Readonly<{ variant: 'notice'; kind: 'NOTICE'; id: string }>
  | Readonly<{ variant: 'unsupported'; id: string }>;

/** The shell and original base are immutable; only the owned content record is editable. */
export type ComplaintContentDraft =
  | Readonly<{ variant: 'ordinary'; base: OrdinarySnapshot; content: OrdinaryContent }>
  | Readonly<{ variant: 'notice-reply'; base: NoticeReplySnapshot; content: NoticeReplyContent }>;

export type PreparedComplaintContentEdit =
  | Readonly<{
    operation: 'content';
    variant: 'ordinary';
    base: OrdinarySnapshot;
    idempotencyKey: string;
    content: Readonly<OrdinaryContent>;
  }>
  | Readonly<{
    operation: 'content';
    variant: 'notice-reply';
    base: NoticeReplySnapshot;
    idempotencyKey: string;
    content: Readonly<NoticeReplyContent>;
  }>;

export type ComplaintContentField = 'TARGET' | 'TYPE' | 'SUBJECT' | 'BODY' | 'CLOSURE_REASON' | 'IDEMPOTENCY_KEY';
export type ComplaintContentReason =
  | 'READ_ONLY'
  | 'VARIANT_MISMATCH'
  | 'UNSUPPORTED_TYPE'
  | 'REQUIRED'
  | 'TOO_LONG'
  | 'FORBIDDEN_CONTROL'
  | 'MALFORMED_UNICODE'
  | 'NON_CANONICAL_UUID'
  | 'UUID_NOT_V4';

export class ComplaintContentError extends Error {
  constructor(readonly field: ComplaintContentField, readonly reason: ComplaintContentReason) {
    super(`Complaint content ${field}: ${reason}.`);
    this.name = 'ComplaintContentError';
  }
}

/** Read-only NOTICE and unsupported snapshots deliberately have no editable draft. */
export function createComplaintContentDraft(snapshot: ComplaintContentSnapshot): ComplaintContentDraft | null {
  switch (snapshot.variant) {
    case 'ordinary': {
      const base = copyOrdinarySnapshot(snapshot);
      return Object.freeze({
        variant: 'ordinary' as const,
        base,
        content: { type: base.content.type, subject: base.content.subject, body: base.content.body },
      });
    }
    case 'notice-reply': {
      const base = copyNoticeReplySnapshot(snapshot);
      return Object.freeze({ variant: 'notice-reply' as const, base, content: { body: base.content.body } });
    }
    default:
      return null;
  }
}

/**
 * Capture copies and freezes every owned record, without changing the visible draft.
 * The supplied key is checked, never generated or replaced. This prepares no request,
 * receipt, retry, outcome, or durable recovery state.
 */
export function prepareComplaintContentEdit(
  draft: ComplaintContentDraft | null,
  idempotencyKey: string,
): PreparedComplaintContentEdit {
  if (!draft || (draft.variant !== 'ordinary' && draft.variant !== 'notice-reply')) {
    throw new ComplaintContentError('TARGET', 'READ_ONLY');
  }
  validateIdempotencyKey(idempotencyKey);
  if (draft.variant === 'ordinary') {
    const base = copyOrdinarySnapshot(draft.base);
    validateType(draft.content.type);
    const content = Object.freeze({
      type: draft.content.type,
      subject: normalizeText(draft.content.subject, 'SUBJECT', 200, 800),
      body: normalizeText(draft.content.body, 'BODY', 1_000, 4_000),
    });
    return Object.freeze({ operation: 'content' as const, variant: 'ordinary' as const, base, idempotencyKey, content });
  }
  const base = copyNoticeReplySnapshot(draft.base);
  const content = Object.freeze({ body: normalizeText(draft.content.body, 'BODY', 1_000, 4_000) });
  return Object.freeze({ operation: 'content' as const, variant: 'notice-reply' as const, base, idempotencyKey, content });
}

function copyOrdinarySnapshot(snapshot: OrdinarySnapshot): OrdinarySnapshot {
  if (snapshot.variant !== 'ordinary' || (snapshot.kind !== 'REPORT' && snapshot.kind !== 'REPLY')) {
    throw new ComplaintContentError('TARGET', 'VARIANT_MISMATCH');
  }
  validateType(snapshot.content.type);
  return Object.freeze({
    variant: 'ordinary' as const,
    kind: snapshot.kind,
    id: snapshot.id,
    actionTag: snapshot.actionTag,
    content: Object.freeze({ type: snapshot.content.type, subject: snapshot.content.subject, body: snapshot.content.body }),
  });
}

function copyNoticeReplySnapshot(snapshot: NoticeReplySnapshot): NoticeReplySnapshot {
  if (snapshot.variant !== 'notice-reply' || snapshot.kind !== 'REPLY') {
    throw new ComplaintContentError('TARGET', 'VARIANT_MISMATCH');
  }
  return Object.freeze({
    variant: 'notice-reply' as const,
    kind: 'REPLY' as const,
    id: snapshot.id,
    actionTag: snapshot.actionTag,
    content: Object.freeze({ body: snapshot.content.body }),
  });
}

function validateType(value: ComplaintContentType): void {
  switch (value) {
    case 'TECHNICAL':
    case 'LANGUAGES':
    case 'SITES_ADD':
    case 'SITE_ERROR':
    case 'FEATURES':
    case 'CUSTOM':
      return;
    default:
      throw new ComplaintContentError('TYPE', 'UNSUPPORTED_TYPE');
  }
}

function validateIdempotencyKey(value: string): void {
  // The length check also excludes a final newline accepted by JavaScript's $ anchor.
  if (value.length !== 36 || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value)) {
    throw new ComplaintContentError('IDEMPOTENCY_KEY', 'NON_CANONICAL_UUID');
  }
  if (value[14] !== '4' || !'89ab'.includes(value[19])) {
    throw new ComplaintContentError('IDEMPOTENCY_KEY', 'UUID_NOT_V4');
  }
}

/** Same normalization as backend ComplaintTextRules.closureReason; no request or authority. */
export function prepareComplaintClosureReason(value: string): string {
  return normalizeText(value, 'CLOSURE_REASON', 500, 2_000);
}

function normalizeText(value: string, field: 'SUBJECT' | 'BODY' | 'CLOSURE_REASON', maximum: number, maximumBytes: number): string {
  const lineNormalized = value.replace(/\r\n/g, '\n');
  // Match backend ComplaintTextRules: validation precedes trimming and UTF-8 measurement.
  for (let index = 0; index < lineNormalized.length; index++) {
    const unit = lineNormalized.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = lineNormalized.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) {
        throw new ComplaintContentError(field, 'MALFORMED_UNICODE');
      }
      index++;
    } else {
      if (unit >= 0xdc00 && unit <= 0xdfff) {
        throw new ComplaintContentError(field, 'MALFORMED_UNICODE');
      }
      if ((unit <= 0x1f || (unit >= 0x7f && unit <= 0x9f)) && unit !== 0x09 && unit !== 0x0a) {
        throw new ComplaintContentError(field, 'FORBIDDEN_CONTROL');
      }
    }
  }

  let start = 0;
  let end = lineNormalized.length;
  while (start < end && isOuterWhitespace(lineNormalized.charCodeAt(start))) start++;
  while (end > start && isOuterWhitespace(lineNormalized.charCodeAt(end - 1))) end--;
  const normalized = lineNormalized.slice(start, end);
  if (normalized.length === 0) throw new ComplaintContentError(field, 'REQUIRED');

  let codePoints = 0;
  let bytes = 0;
  for (const character of normalized) {
    codePoints++;
    const unit = character.charCodeAt(0);
    bytes += character.length === 2 ? 4 : unit <= 0x7f ? 1 : unit <= 0x7ff ? 2 : 3;
  }
  if (codePoints > maximum || bytes > maximumBytes) throw new ComplaintContentError(field, 'TOO_LONG');
  return normalized;
}

function isOuterWhitespace(unit: number): boolean {
  // Kotlin/JVM Char.isWhitespace = Character.isWhitespace || Character.isSpaceChar.
  // These are its code points remaining AFTER control validation. U+FEFF is not one.
  return unit === 0x09 || unit === 0x0a || unit === 0x20 || unit === 0x00a0 || unit === 0x1680
    || (unit >= 0x2000 && unit <= 0x200a) || unit === 0x2028 || unit === 0x2029
    || unit === 0x202f || unit === 0x205f || unit === 0x3000;
}
