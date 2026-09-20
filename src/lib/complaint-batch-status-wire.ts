/** Strict compatibility entrypoints: importing STATUS never admits DELETE bodies or ACKs. */
export {
  complaintBatchStatuses,
  captureComplaintBatchStatusRequest,
  prepareComplaintBatchStatusRequest,
  complaintBatchStatusDestination,
  decodeComplaintBatchStatusOutcome,
  isCompleteComplaintBatchStatusResult,
  ComplaintBatchBodyError as ComplaintBatchStatusBodyError,
  type ComplaintBatchStatusRequest,
  type ComplaintBatchStatusOutcome,
} from './complaint-batch-wire';
