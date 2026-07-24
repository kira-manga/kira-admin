export const backendUrl = (process.env.KIRA_BACKEND_URL ?? 'https://api.kiramanga.me').replace(/\/$/, '');
export const adminOrigin = process.env.KIRA_ADMIN_ORIGIN?.replace(/\/$/, '') ?? '';
export const adminTokenCookie = 'kira_admin_session';
export const adminCsrfCookie = 'kira_admin_csrf';
export const adminStepUpCookie = 'kira_admin_step_up';
