import { request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { timingSafeEqual } from 'node:crypto';
import { TLSSocket } from 'node:tls';

import type { NextApiRequest, NextApiResponse } from 'next';

import { adminOrigin, backendUrl } from '@/lib/server-config';
import { readAdminSession, SessionBoundaryError } from '@/lib/server-session';
import { sessionGenerationHeader } from '@/lib/session-contract';

const maxRequestBytes = 5 * 1024 * 1024;
const upstreamTimeoutMs = 65_000;

export const config = {
  api: {
    bodyParser: false,
  },
};

export default function handler(request: NextApiRequest, response: NextApiResponse) {
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    response.status(405).json({ detail: 'Method not allowed.' });
    return;
  }

  const host = request.headers['x-forwarded-host'] ?? request.headers.host;
  const protocol = request.headers['x-forwarded-proto'] ?? (request.socket instanceof TLSSocket ? 'https' : 'http');
  const expectedOrigin = adminOrigin || (host ? `${protocol}://${host}` : '');
  const origin = request.headers.origin;
  if (
    !origin || origin !== expectedOrigin ||
    request.headers['sec-fetch-site'] === 'cross-site'
  ) {
    response.status(403).json({ detail: 'Invalid cross-site request token.' });
    return;
  }

  let session;
  try {
    const headers = new Headers();
    // Keep duplicate-valued fields ambiguous instead of trusting the Pages cookie map.
    for (const name of ['cookie', sessionGenerationHeader.toLowerCase()]) {
      const value = request.headers[name];
      if (Array.isArray(value)) value.forEach((part) => headers.append(name, part));
      else if (value !== undefined) headers.set(name, value);
    }
    session = readAdminSession(headers);
  } catch (error) {
    response.status(error instanceof SessionBoundaryError ? error.status : 503).json({
      detail: error instanceof SessionBoundaryError ? error.message : 'Admin authentication is temporarily unavailable.',
    });
    return;
  }
  const suppliedCsrf = request.headers['x-kira-csrf'];
  if (typeof suppliedCsrf !== 'string' || !constantTimeEqual(session.csrfToken, suppliedCsrf)) {
    response.status(403).json({ detail: 'Invalid cross-site request token.' });
    return;
  }

  const contentType = request.headers['content-type'];
  if (!contentType?.toLowerCase().startsWith('multipart/form-data;')) {
    response.status(415).json({ detail: 'A multipart media upload is required.' });
    return;
  }

  const contentLength = Number(request.headers['content-length']);
  if (!Number.isSafeInteger(contentLength) || contentLength <= 0) {
    response.status(411).json({ detail: 'A valid Content-Length header is required.' });
    return;
  }
  if (contentLength > maxRequestBytes) {
    response.status(413).json({ detail: 'Tutorial media requests must not exceed 5 MiB.' });
    return;
  }

  return new Promise<void>((resolve) => {
    const upstreamUrl = new URL('/api/v1/admin/tutorial-media', backendUrl);
    const transport = upstreamUrl.protocol === 'https:' ? httpsRequest : httpRequest;
    let timedOut = false;
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      resolve();
    };
    response.once('finish', finish);
    response.once('close', finish);

    const upstreamRequest = transport(upstreamUrl, {
      method: 'POST',
      headers: {
        Accept: 'application/json, application/problem+json',
        Authorization: `Bearer ${session.token}`,
        'Content-Type': contentType,
        'Content-Length': contentLength,
      },
    }, (upstreamResponse) => {
      response.statusCode = upstreamResponse.statusCode ?? 502;
      for (const header of ['content-type', 'content-length', 'retry-after', 'x-request-id']) {
        const value = upstreamResponse.headers[header];
        if (value !== undefined) response.setHeader(header, value);
      }
      upstreamResponse.on('error', () => response.destroy());
      upstreamResponse.pipe(response);
    });

    upstreamRequest.setTimeout(upstreamTimeoutMs, () => {
      timedOut = true;
      upstreamRequest.destroy(new Error('Production API upload timed out.'));
    });
    upstreamRequest.on('error', () => {
      if (response.headersSent) {
        response.destroy();
        return;
      }
      response.status(timedOut ? 504 : 502).json({
        detail: timedOut ? 'The production API timed out while processing the upload.' : 'The production API could not be reached.',
      });
    });
    request.on('aborted', () => upstreamRequest.destroy());
    request.pipe(upstreamRequest);
  });
}

function constantTimeEqual(left: string, right: string) {
  if (left.length !== right.length) return false;
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}
