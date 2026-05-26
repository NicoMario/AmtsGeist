import "./taskpane.css";
import { BACKEND_URL } from "../config";
import { api, CalendarEvent, EmailIn } from "../lib/api";

// In dieser Sitzung gesammelte Kurz-Zusammenfassungen markierter Mails -> fließen ins Tagesbriefing.
const sessionSummaries: string[] = [];
// Aus geöffneten Terminen übernommene Kalendereinträge (graph-frei via Office.js).
const collectedEvents: CalendarEvent[] = [];

Office.onReady((info) => {
  if (info.host !== Office.HostType.Outlook) {
    return;
  }
  (document.getElementById("btn-summarize") as HTMLButtonElement).onclick = onSummarize;
  (document.getElementById("btn-triage") as HTMLButtonElement).onclick = onTriage;
  (document.getElementById("btn-briefing") as HTMLButtonElement).onclick = onBriefing;
  (document.getElementById("btn-add-appt") as HTMLButtonElement).onclick = onAddAppointment;
  (document.getElementById("backend-note") as HTMLElement).textContent = `Backend: ${BACKEND_URL}`;
});

// --------------------------------------------------------------------------- //
// Office.js-Hilfsfunktionen
// --------------------------------------------------------------------------- //
function getItemBody(): Promise<string> {
  return new Promise((resolve, reject) => {
    const item = Office.context.mailbox.item;
    if (!item) {
      reject(new Error("Keine E-Mail ausgewählt."));
      return;
    }
    item.body.getAsync(Office.CoercionType.Text, (res) => {
      if (res.status === Office.AsyncResultStatus.Succeeded) {
        resolve(res.value);
      } else {
        reject(new Error(res.error.message));
      }
    });
  });
}

async function currentEmail(): Promise<EmailIn> {
  const item = Office.context.mailbox.item as Office.MessageRead;
  const body = await getItemBody();
  return {
    subject: item.subject ?? "",
    from: item.from?.emailAddress ?? "",
    body,
  };
}

// Lokales ISO ohne Zeitzonenversatz, damit das Briefing die korrekte Uhrzeit anzeigt.
function toLocalIso(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:00`
  );
}

// Liest den aktuell GEÖFFNETEN Termin (Lesemodus) — ohne Graph, ohne Sonderberechtigung.
// Liefert null, wenn keine Mail/kein Termin oder ein Termin im Bearbeiten-Modus geöffnet ist.
function readCurrentAppointment(): CalendarEvent | null {
  const item = Office.context.mailbox.item;
  if (!item || item.itemType !== Office.MailboxEnums.ItemType.Appointment) {
    return null;
  }
  const appt = item as Office.AppointmentRead;
  if (!(appt.start instanceof Date)) {
    return null; // Bearbeiten-Modus (Time-Objekt) wird im MVP nicht unterstützt
  }
  return {
    subject: appt.subject ?? "",
    start: toLocalIso(appt.start),
    end: appt.end instanceof Date ? toLocalIso(appt.end) : null,
    location: typeof appt.location === "string" ? appt.location : "",
  };
}

function applyCategory(displayName: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const item = Office.context.mailbox.item as Office.MessageRead;
    // Kategorie zuerst in der Master-Liste anlegen (Fehler ignorieren, falls vorhanden) ...
    Office.context.mailbox.masterCategories.addAsync(
      [{ displayName, color: Office.MailboxEnums.CategoryColor.Preset0 }],
      () => {
        // ... dann der aktuellen E-Mail zuweisen.
        item.categories.addAsync([displayName], (res) => {
          if (res.status === Office.AsyncResultStatus.Succeeded) {
            resolve();
          } else {
            reject(new Error(res.error.message));
          }
        });
      }
    );
  });
}

// --------------------------------------------------------------------------- //
// UI-Helfer
// --------------------------------------------------------------------------- //
function setStatus(msg: string): void {
  (document.getElementById("status") as HTMLElement).textContent = msg;
}

function showResult(id: string, html: string): void {
  const el = document.getElementById(id) as HTMLElement;
  el.innerHTML = html;
  el.hidden = false;
}

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function setBusy(busy: boolean): void {
  document.querySelectorAll<HTMLButtonElement>("button").forEach((b) => (b.disabled = busy));
}

// --------------------------------------------------------------------------- //
// Aktionen
// --------------------------------------------------------------------------- //
async function onSummarize(): Promise<void> {
  setBusy(true);
  setStatus("Fasse zusammen …");
  try {
    const email = await currentEmail();
    const resp = await api.summarize([email]);
    const items =
      resp.action_items.length > 0
        ? `<h3>Aufgaben</h3><ul>${resp.action_items
            .map((a) => `<li>${escapeHtml(a)}</li>`)
            .join("")}</ul>`
        : "";
    showResult(
      "mail-result",
      `<h3>Zusammenfassung</h3>${escapeHtml(resp.summary)}${items}` +
        `<div class="meta">Modell: ${resp.model_used}${resp.escalated ? " (eskaliert)" : ""}</div>`
    );
    sessionSummaries.push(resp.summary);
    setStatus("");
  } catch (err) {
    setStatus(`Fehler: ${(err as Error).message}`);
  } finally {
    setBusy(false);
  }
}

async function onTriage(): Promise<void> {
  setBusy(true);
  setStatus("Ordne ein …");
  try {
    const email = await currentEmail();
    const resp = await api.triage(email);
    const r = resp.result;
    const deadline = r.deadline ? `<div><b>Frist:</b> ${escapeHtml(r.deadline)}</div>` : "";
    showResult(
      "mail-result",
      `<h3>Einordnung</h3>` +
        `<span class="badge">${escapeHtml(r.category)}</span>` +
        `<span class="badge prio-${r.priority}">Priorität ${r.priority}</span>` +
        `${deadline}` +
        `<div><b>Ordner-Vorschlag:</b> ${escapeHtml(r.suggested_folder)}</div>` +
        `<div>${escapeHtml(r.reasoning)}</div>` +
        `<button id="btn-apply" type="button">Kategorie übernehmen</button>` +
        `<div class="meta">Modell: ${resp.model_used}${resp.escalated ? " (eskaliert)" : ""}</div>`
    );
    (document.getElementById("btn-apply") as HTMLButtonElement).onclick = async () => {
      setStatus("Setze Kategorie …");
      try {
        await applyCategory(`AmtsGeist: ${r.category}`);
        setStatus("Kategorie gesetzt.");
      } catch (err) {
        setStatus(`Kategorie konnte nicht gesetzt werden: ${(err as Error).message}`);
      }
    };
    sessionSummaries.push(`${r.category}: ${email.subject ?? ""}`.trim());
    setStatus("");
  } catch (err) {
    setStatus(`Fehler: ${(err as Error).message}`);
  } finally {
    setBusy(false);
  }
}

function onAddAppointment(): void {
  const note = document.getElementById("appt-note") as HTMLElement;
  const event = readCurrentAppointment();
  if (!event) {
    note.textContent =
      "Kein geöffneter Termin gefunden. Öffnen Sie einen Termin (Lesemodus) und versuchen Sie es erneut.";
    return;
  }
  collectedEvents.push(event);
  const time = event.start.slice(11, 16);
  note.textContent = `Übernommen: ${time} ${event.subject} · gesammelt: ${collectedEvents.length}`;
}

function parseEvents(raw: string): CalendarEvent[] {
  const today = new Date().toISOString().slice(0, 10);
  const events: CalendarEvent[] = [];
  for (const line of raw.split("\n")) {
    const match = line.trim().match(/^(\d{1,2}:\d{2})\s+(.+)$/);
    if (match) {
      const [, time, subject] = match;
      const hhmm = time.padStart(5, "0");
      events.push({ subject: subject.trim(), start: `${today}T${hhmm}:00` });
    }
  }
  return events;
}

async function onBriefing(): Promise<void> {
  setBusy(true);
  setStatus("Erstelle Tagesbriefing …");
  try {
    const raw = (document.getElementById("events-input") as HTMLTextAreaElement).value;
    const events = [...collectedEvents, ...parseEvents(raw)];
    const today = new Date().toISOString().slice(0, 10);
    const resp = await api.briefing(today, events, sessionSummaries);

    const deadlines =
      resp.deadlines.length > 0
        ? `<h3>Fristen</h3><ul>${resp.deadlines
            .map((d) => `<li>${escapeHtml(d)}</li>`)
            .join("")}</ul>`
        : "";
    const focus =
      resp.focus_blocks.length > 0
        ? `<h3>Fokus-Blöcke</h3><ul>${resp.focus_blocks
            .map((f) => `<li>${escapeHtml(f)}</li>`)
            .join("")}</ul>`
        : "";
    showResult(
      "briefing-result",
      `${escapeHtml(resp.briefing_markdown)}${deadlines}${focus}` +
        `<div class="meta">Modell: ${resp.model_used}</div>`
    );
    setStatus("");
  } catch (err) {
    setStatus(`Fehler: ${(err as Error).message}`);
  } finally {
    setBusy(false);
  }
}
