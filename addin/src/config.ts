// Adresse des AmtsGeist-Backends ("das Gehirn" im Rechenzentrum).
// Im Behörden-Betrieb auf die interne RZ-Adresse setzen (z. B. via window.AMTSGEIST_BACKEND).
export const BACKEND_URL =
  (window as unknown as { AMTSGEIST_BACKEND?: string }).AMTSGEIST_BACKEND ??
  "http://localhost:8000";
