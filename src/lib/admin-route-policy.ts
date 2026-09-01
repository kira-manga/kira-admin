const mutatingMethods = new Set(['POST', 'PUT', 'DELETE']);

export function isMutatingMethod(method: string) {
  return mutatingMethods.has(method);
}

export function adminRouteAllowed(path: string[], method: string) {
  const joined = path.join('/');
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
