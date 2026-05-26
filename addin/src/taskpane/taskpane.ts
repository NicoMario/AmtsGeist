import "./taskpane.css";
import { getBackendUrl, setBackendUrl } from "../config";
import { api, CalendarEvent, EmailIn } from "../lib/api";
import { ewsAvailable, getRecentInbox, getTodaysAppointments } from "../lib/ews";
import { toLocalIso } from "../lib/util";

// Sitzungs-Status: Kurz-Zusammenfassungen markierter Mails + gesammelte Termine -> Tagesbriefing.
const sessionSummaries: string[] = [];
const collectedEvents: CalendarEvent[] = [];

Office.onReady((info) => {
  if (info.host !== Office.HostType.Outlook) {
    return;
  }
  wire("btn-summarize", onSummarize);
  wire("btn-triage", onTriage);
  wire("btn-draft", onDraftReply);
  wire("btn-inbox", onInboxTriage);
  wire("btn-load-cal", onLoadCalendar);
  wire("btn-add-appt", onAddAppointment);
  wire("btn-briefing", onBriefing);
  wire("btn-save-settings", onSaveSettings);

  (document.getElementById("backend-url") as HTMLInputElement).value = getBackendUrl();
  (document.getElementById("backend-note") as HTMLElement).textContent =
    `Backend: ${getBackendUrl()}${ewsAvailable() ? " · EWS aktiv" : " · EWS n/v"}`;
});

function wire(id: string, handler: () => void): void {
  (document.getElementById(id) as HTMLButtonElement).onclick = handler;
}

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

// Aktuell GEÖFFNETER Termin (Lesemodus) — ohne Graph, ohne Sonderberechtigung.
function readCurrentAppointment(): CalendarEvent | null {
  const item = Office.context.mailbox.item;
  if (!item || item.itemType !== Office.MailboxEnums.ItemType.Appointment) {
    return null;
  }
  const appt = item as Office.AppointmentRead;
  if (!(appt.start instanceof Date)) {
    return null;
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
    Office.context.mailbox.masterCategories.addAsync(
      [{ displayName, color: Office.MailboxEnums.CategoryColor.Preset0 }],
      () => {
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

function triageBadges(category: string, priority: number, deadline: string | null): string {
  const dl = deadline ? `<span class="badge prio-2">Frist ${escapeHtml(deadline)}</span>` : "";
  return (
    `<span class="badge">${escapeHtml(category)}</span>` +
    `<span class="badge prio-${priority}">Prio ${priority}</span>${dl}`
  );
}

// --------------------------------------------------------------------------- //
// Aktionen: aktuelle E-Mail
// --------------------------------------------------------------------------- //
async function onSummarize(): Promise<void> {
  await run("Fasse zusammen …", async () => {
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
  });
}

async function onTriage(): Promise<void> {
  await run("Ordne ein …", async () => {
    const email = await currentEmail();
    const resp = await api.triage(email);
    const r = resp.result;
    showResult(
      "mail-result",
      `<h3>Einordnung</h3>${triageBadges(r.category, r.priority, r.deadline)}` +
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
  });
}

async function onDraftReply(): Promise<void> {
  await run("Entwerfe Antwort …", async () => {
    const email = await currentEmail();
    const intent = (document.getElementById("reply-intent") as HTMLInputElement).value;
    const resp = await api.draftReply(email, intent);
    showResult(
      "mail-result",
      `<h3>Antwort-Entwurf</h3><div><b>${escapeHtml(resp.subject)}</b></div>` +
        `<div>${escapeHtml(resp.body)}</div>` +
        `<div class="meta">Modell: ${resp.model_used} · Entwurf im Antwortfenster geöffnet</div>`
    );
    try {
      (Office.context.mailbox.item as Office.MessageRead).displayReplyForm(resp.body);
    } catch {
      // displayReplyForm nicht verfügbar -> Text steht im Ergebnisfeld zur Übernahme bereit
    }
  });
}

// --------------------------------------------------------------------------- //
// Aktionen: Posteingang (EWS, graph-frei)
// --------------------------------------------------------------------------- //
async function onInboxTriage(): Promise<void> {
  if (!ewsAvailable()) {
    setStatus("Posteingang-Triage benötigt klassisches Outlook (EWS nicht verfügbar).");
    return;
  }
  await run("Lese Posteingang & ordne ein …", async () => {
    const emails = await getRecentInbox(12);
    if (emails.length === 0) {
      showResult("inbox-result", "Keine Mails im Posteingang gefunden.");
      return;
    }
    const resp = await api.triageBatch(emails);
    const rows = resp.items
      .map((it, i) => ({ subject: emails[i].subject ?? "(ohne Betreff)", r: it.result }))
      .sort((a, b) => a.r.priority - b.r.priority)
      .map(
        (x) =>
          `<div class="inbox-item">${triageBadges(x.r.category, x.r.priority, x.r.deadline)}` +
          `<div>${escapeHtml(x.subject)}</div></div>`
      )
      .join("");
    showResult("inbox-result", `<h3>${resp.items.length} Mails eingeordnet</h3>${rows}`);
  });
}

// --------------------------------------------------------------------------- //
// Aktionen: Kalender / Tagesbriefing
// --------------------------------------------------------------------------- //
async function onLoadCalendar(): Promise<void> {
  const note = document.getElementById("appt-note") as HTMLElement;
  if (!ewsAvailable()) {
    note.textContent =
      "Automatischer Kalender benötigt klassisches Outlook. Bitte Termine manuell eintragen.";
    return;
  }
  setBusy(true);
  setStatus("Lade Kalender …");
  try {
    const appts = await getTodaysAppointments();
    collectedEvents.length = 0;
    collectedEvents.push(...appts);
    (document.getElementById("events-input") as HTMLTextAreaElement).value = "";
    note.textContent = `${appts.length} Termine aus dem Kalender geladen.`;
    setStatus("");
  } catch (err) {
    note.textContent = `Kalender konnte nicht geladen werden: ${(err as Error).message}`;
    setStatus("");
  } finally {
    setBusy(false);
  }
}

function onAddAppointment(): void {
  const note = document.getElementById("appt-note") as HTMLElement;
  const event = readCurrentAppointment();
  if (!event) {
    note.textContent =
      "Kein geöffneter Termin (Lesemodus) gefunden. Termin öffnen und erneut versuchen.";
    return;
  }
  collectedEvents.push(event);
  note.textContent = `Übernommen: ${event.start.slice(11, 16)} ${event.subject} · gesammelt: ${collectedEvents.length}`;
}

function parseEvents(raw: string): CalendarEvent[] {
  const today = new Date().toISOString().slice(0, 10);
  const events: CalendarEvent[] = [];
  for (const line of raw.split("\n")) {
    const match = line.trim().match(/^(\d{1,2}:\d{2})\s+(.+)$/);
    if (match) {
      const [, time, subject] = match;
      events.push({ subject: subject.trim(), start: `${today}T${time.padStart(5, "0")}:00` });
    }
  }
  return events;
}

async function onBriefing(): Promise<void> {
  await run("Erstelle Tagesbriefing …", async () => {
    const raw = (document.getElementById("events-input") as HTMLTextAreaElement).value;
    const events = [...collectedEvents, ...parseEvents(raw)];
    const today = new Date().toISOString().slice(0, 10);
    const resp = await api.briefing(today, events, sessionSummaries);
    const deadlines =
      resp.deadlines.length > 0
        ? `<h3>Fristen</h3><ul>${resp.deadlines.map((d) => `<li>${escapeHtml(d)}</li>`).join("")}</ul>`
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
  });
}

// --------------------------------------------------------------------------- //
// Einstellungen
// --------------------------------------------------------------------------- //
async function onSaveSettings(): Promise<void> {
  const url = (document.getElementById("backend-url") as HTMLInputElement).value;
  try {
    await setBackendUrl(url);
    (document.getElementById("backend-note") as HTMLElement).textContent =
      `Backend: ${getBackendUrl()}${ewsAvailable() ? " · EWS aktiv" : " · EWS n/v"}`;
    setStatus("Einstellungen gespeichert.");
  } catch (err) {
    setStatus(`Speichern fehlgeschlagen: ${(err as Error).message}`);
  }
}

// Gemeinsamer Wrapper: Busy-State + Fehlerbehandlung.
async function run(busyMsg: string, fn: () => Promise<void>): Promise<void> {
  setBusy(true);
  setStatus(busyMsg);
  try {
    await fn();
    setStatus("");
  } catch (err) {
    setStatus(`Fehler: ${(err as Error).message}`);
  } finally {
    setBusy(false);
  }
}
