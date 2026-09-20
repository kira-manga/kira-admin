const mutatingMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
const canonicalUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

/** Notice resource IDs need canonical spelling, but need not be UUIDv4. */
export function isComplaintDetailPath(path: readonly string[]) {
  return path.length === 2 && path[0] === 'complaints' && path[1].length === 36 && canonicalUuid.test(path[1]);
}

export function isComplaintMutationPath(path: readonly string[]) {
  return path.length === 3 && isComplaintDetailPath(path.slice(0, 2)) && ['content', 'status', 'closure'].includes(path[2]);
}

export function isComplaintSearchPath(path: readonly string[]) {
  return path.length === 2 && path[0] === 'complaints' && path[1] === 'search';
}

export function isComplaintStatsPath(path: readonly string[]) {
  return path.length === 2 && path[0] === 'complaints' && path[1] === 'stats';
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
  if (path[0] === 'complaints') return method === 'GET' && (isComplaintDetailPath(path) || isComplaintStatsPath(path))
    || method === 'POST' && isComplaintSearchPath(path)
    || method === 'PATCH' && isComplaintMutationPath(path)
    || method === 'DELETE' && isComplaintDetailPath(path);
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

export function routeNeedsStepUp(path: string[], method: string) {
  if (method === 'POST' && path.length === 3 && path[0] === 'source-changesets' && path[1].length === 36 && canonicalUuid.test(path[1]) && path[2] === 'apply') return true;
  if (path[0] !== 'sources' || !path[1] || path[1].includes('/')) return false;
  return method === 'POST' && path.length === 4 && path[2] === 'editor-draft' && path[3] === 'publish'
    || method === 'PUT' && path.length === 3 && path[2] === 'operational-mode';
}
