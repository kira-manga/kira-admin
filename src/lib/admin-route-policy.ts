const mutatingMethods = new Set(['POST', 'PUT', 'DELETE']);
const canonicalUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

/** Notice resource IDs need canonical spelling, but need not be UUIDv4. */
export function isComplaintDetailPath(path: readonly string[]) {
  return path.length === 2 && path[0] === 'complaints' && path[1].length === 36 && canonicalUuid.test(path[1]);
}

/** Exact raw query only. A TEST scope's syntax never establishes activation or authority. */
export function isComplaintDetailQuery(search: string) {
  const scope = search.slice('?dataScopeId='.length);
  return search.length === 49 && search.startsWith('?dataScopeId=') && canonicalUuid.test(scope)
    && scope[14] === '4' && '89ab'.includes(scope[19]);
}

export function isMutatingMethod(method: string) {
  return mutatingMethods.has(method);
}

export function adminRouteAllowed(path: string[], method: string) {
  const joined = path.join('/');
  if (path[0] === 'complaints') return method === 'GET' && isComplaintDetailPath(path);
  if (['tutorials', 'tutorial-categories', 'tutorial-media'].includes(path[0] ?? '')) {
    return ['GET', 'POST', 'DELETE'].includes(method) && !(method === 'POST' && path[0] === 'tutorial-media');
  }
  if (joined === 'source-studio/capabilities') return method === 'GET';
  if (joined === 'source-preview') return method === 'POST';
  if (path[0] === 'audit' || path[0] === 'documents') return method === 'GET';
  if (path[0] === 'source-changesets') return ['GET', 'POST', 'PUT', 'DELETE'].includes(method);
  if (path[0] !== 'sources') return false;
  if (method === 'GET') return true;
  if (joined === 'sources') return method === 'POST';
  if (/^sources\/[^/]+\/revisions$/.test(joined)) return method === 'POST';
  if (/^sources\/[^/]+\/revisions\/[1-9][0-9]*\/validate$/.test(joined)) return method === 'POST';
  if (/^sources\/[^/]+\/operational-mode$/.test(joined)) return method === 'PUT';
  if (/^sources\/[^/]+\/editor-draft(?:\/(?:validate|finalize|publish))?$/.test(joined)) {
    return ['POST', 'PUT', 'DELETE'].includes(method);
  }
  return false;
}

export function routeNeedsStepUp(path: string[]) {
  const joined = path.join('/');
  return joined.endsWith('/apply') || joined.endsWith('/editor-draft/publish') || /^sources\/[^/]+\/operational-mode$/.test(joined);
}
