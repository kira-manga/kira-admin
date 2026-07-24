type Problem = { detail?: string; title?: string; message?: string; fieldErrors?: Array<{ message?: string }> };
export type UploadProgress = { loaded: number; total: number; percent: number };

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function readError(response: Response) {
  try {
    const problem = await response.json() as Problem;
    return problem.detail ?? problem.fieldErrors?.[0]?.message ?? problem.message ?? problem.title ?? `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

function readUploadError(request: XMLHttpRequest) {
  try {
    const problem = JSON.parse(request.responseText) as Problem;
    return problem.detail ?? problem.fieldErrors?.[0]?.message ?? problem.message ?? problem.title ?? `Request failed (${request.status})`;
  } catch {
    return `Request failed (${request.status})`;
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`/api/backend/${path.replace(/^\//, '')}`, { ...init, headers, cache: 'no-store' });
  if (!response.ok) throw new ApiError(await readError(response), response.status);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiUpload<T>(endpoint: string, body: FormData, onProgress: (progress: UploadProgress) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open('POST', endpoint);
    request.timeout = 70_000;
    request.setRequestHeader('Accept', 'application/json, application/problem+json');
    request.upload.addEventListener('progress', (event) => {
      if (!event.lengthComputable || event.total <= 0) return;
      onProgress({ loaded: event.loaded, total: event.total, percent: Math.min(100, Math.round((event.loaded / event.total) * 100)) });
    });
    request.addEventListener('load', () => {
      if (request.status < 200 || request.status >= 300) {
        reject(new ApiError(readUploadError(request), request.status));
        return;
      }
      onProgress({ loaded: body.get('file') instanceof File ? (body.get('file') as File).size : 1, total: body.get('file') instanceof File ? (body.get('file') as File).size : 1, percent: 100 });
      if (request.status === 204 || !request.responseText) {
        resolve(undefined as T);
        return;
      }
      try {
        resolve(JSON.parse(request.responseText) as T);
      } catch {
        reject(new ApiError('The server returned an invalid response.', request.status));
      }
    });
    request.addEventListener('error', () => reject(new ApiError('Upload failed because the server could not be reached.', 0)));
    request.addEventListener('abort', () => reject(new ApiError('Upload was cancelled.', 0)));
    request.addEventListener('timeout', () => reject(new ApiError('The production API timed out while processing the upload.', 504)));
    request.send(body);
  });
}

export async function sessionFetch() {
  const response = await fetch('/api/auth/session', { cache: 'no-store' });
  if (!response.ok) return null;
  return response.json();
}
