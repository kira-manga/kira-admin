export const backendUrl = (process.env.KIRA_BACKEND_URL ?? 'https://api.kiramanga.me').replace(/\/$/, '');
export const adminTokenCookie = 'kira_admin_session';
