import { prepareComplaintContentEdit, type PreparedComplaintContentEdit } from './complaint-content-editor';
import { decodeComplaintMutationApplied, prepareComplaintMutationRequest, type ComplaintMutationRequest } from './complaint-mutation-wire';

export class ComplaintContentWireError extends Error {
  constructor(readonly reason: 'INVALID_CAPTURE' | 'UNCONFIRMED_RESPONSE') {
    super(`Complaint content: ${reason}.`);
    this.name = 'ComplaintContentWireError';
  }
}

export type ComplaintContentRequest = ComplaintMutationRequest;

/** Retain this exact description on ambiguity; never replace its key or base tag on retry. */
export function prepareComplaintContentRequest(
  capture: PreparedComplaintContentEdit,
  dataScopeId: string,
): ComplaintContentRequest {
  const invalid = (): never => { throw new ComplaintContentWireError('INVALID_CAPTURE'); };
  if (capture.operation !== 'content') invalid();
  try {
    const checked = capture.variant === 'ordinary'
      ? prepareComplaintContentEdit({ variant: 'ordinary', base: capture.base, content: { ...capture.content } }, capture.idempotencyKey)
      : capture.variant === 'notice-reply'
        ? prepareComplaintContentEdit({ variant: 'notice-reply', base: capture.base, content: { ...capture.content } }, capture.idempotencyKey)
        : invalid();
    // Never change the meaning of a saved intent while preparing its wire description.
    if (checked.variant !== capture.variant || checked.content.body !== capture.content.body) invalid();
    if (checked.variant === 'ordinary' && capture.variant === 'ordinary' &&
        (checked.content.type !== capture.content.type || checked.content.subject !== capture.content.subject)) invalid();
    return prepareComplaintMutationRequest('content', capture.base.id, dataScopeId, capture.idempotencyKey,
      capture.base.actionTag, JSON.stringify(checked.content));
  } catch {
    return invalid();
  }
}

/** Shared lossless numeric-Long parser; errors preserve the existing content API. */
export function decodeComplaintContentApplied(
  request: ComplaintContentRequest,
  response: Parameters<typeof decodeComplaintMutationApplied>[1],
): ReturnType<typeof decodeComplaintMutationApplied> {
  try {
    return decodeComplaintMutationApplied(request, response);
  } catch {
    throw new ComplaintContentWireError('UNCONFIRMED_RESPONSE');
  }
}
