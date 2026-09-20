const configuredBackendUrl = process.env.KIRA_BACKEND_URL ?? 'https://api.kiramanga.me';
const trustedIngressSetting = process.env.KIRA_ADMIN_TRUSTED_INGRESS;

if (trustedIngressSetting !== undefined && trustedIngressSetting !== 'true' && trustedIngressSetting !== 'false') {
  throw new Error('KIRA_ADMIN_TRUSTED_INGRESS must be true or false when set.');
}

export const adminTrustedIngress = trustedIngressSetting === 'true';
if (adminTrustedIngress && configuredBackendUrl !== 'http://backend:8080') {
  throw new Error('Trusted admin ingress requires KIRA_BACKEND_URL=http://backend:8080.');
}

export const backendUrl = configuredBackendUrl.replace(/\/$/, '');
export const adminOrigin = process.env.KIRA_ADMIN_ORIGIN?.replace(/\/$/, '') ?? '';
