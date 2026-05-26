// Adresse des AmtsGeist-Backends ("das Gehirn" im Rechenzentrum).
//
// Persistenz ohne Datenbank/Admin: die Backend-URL wird in den Outlook-RoamingSettings des
// Nutzers gespeichert (liegt im eigenen Postfach, roamt über Geräte). Reihenfolge:
//   1. window.AMTSGEIST_BACKEND (Build-/Deploy-Override)
//   2. RoamingSettings (vom Nutzer in den Einstellungen gesetzt)
//   3. Default (lokale Entwicklung)
const DEFAULT_BACKEND_URL =
  (window as unknown as { AMTSGEIST_BACKEND?: string }).AMTSGEIST_BACKEND ??
  "http://localhost:8000";

export function getBackendUrl(): string {
  try {
    const stored = Office.context.roamingSettings?.get("backendUrl");
    if (typeof stored === "string" && stored.trim()) {
      return stored.trim();
    }
  } catch {
    // RoamingSettings noch nicht bereit -> Default
  }
  return DEFAULT_BACKEND_URL;
}

export function setBackendUrl(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    Office.context.roamingSettings.set("backendUrl", url.trim());
    Office.context.roamingSettings.saveAsync((res) => {
      if (res.status === Office.AsyncResultStatus.Succeeded) {
        resolve();
      } else {
        reject(new Error(res.error?.message ?? "Speichern fehlgeschlagen"));
      }
    });
  });
}
