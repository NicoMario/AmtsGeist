// Graph-freier Zugriff auf das eigene Postfach via Exchange Web Services (EWS).
//
// Kernidee des USP: `makeEwsRequestAsync` nutzt das Token, das das Add-in ohnehin hat —
// KEINE Azure-/Entra-App-Registrierung, KEIN Admin-Consent, KEINE Sonderrechte des Beamten.
//
// Einschränkung: makeEwsRequestAsync funktioniert im klassischen Outlook (Desktop/Mac),
// NICHT im neuen Outlook / Outlook im Web. Daher überall Feature-Detection + Fallback.
// Hinweis: Die EWS-Pfade sind gegen echtes Exchange noch ungetestet (keine Testumgebung).

import { CalendarEvent, EmailIn } from "./api";
import { toLocalIso, truncate } from "./util";

const T_NS = "http://schemas.microsoft.com/exchange/services/2006/types";

const SOAP_HEAD = `<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:t="http://schemas.microsoft.com/exchange/services/2006/types" xmlns:m="http://schemas.microsoft.com/exchange/services/2006/messages">
  <soap:Header><t:RequestServerVersion Version="Exchange2013"/></soap:Header>
  <soap:Body>`;
const SOAP_TAIL = `  </soap:Body>
</soap:Envelope>`;

export function ewsAvailable(): boolean {
  return !!(
    Office.context.mailbox &&
    typeof Office.context.mailbox.makeEwsRequestAsync === "function"
  );
}

function makeEws(soap: string): Promise<Document> {
  return new Promise((resolve, reject) => {
    try {
      Office.context.mailbox.makeEwsRequestAsync(soap, (res) => {
        if (res.status !== Office.AsyncResultStatus.Succeeded) {
          reject(new Error(res.error?.message ?? "EWS-Anfrage fehlgeschlagen"));
          return;
        }
        resolve(new DOMParser().parseFromString(res.value, "text/xml"));
      });
    } catch (err) {
      reject(err as Error);
    }
  });
}

function firstText(el: Element, name: string): string {
  return el.getElementsByTagNameNS(T_NS, name)[0]?.textContent ?? "";
}

function dayBoundsUtc(): { start: string; end: string } {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const end = new Date(start.getTime() + 24 * 3600 * 1000);
  return { start: start.toISOString(), end: end.toISOString() };
}

// Heutige Termine aus dem eigenen Kalender (EWS FindItem / CalendarView).
export async function getTodaysAppointments(): Promise<CalendarEvent[]> {
  const { start, end } = dayBoundsUtc();
  const soap = `${SOAP_HEAD}
    <m:FindItem Traversal="Shallow">
      <m:ItemShape>
        <t:BaseShape>IdOnly</t:BaseShape>
        <t:AdditionalProperties>
          <t:FieldURI FieldURI="item:Subject"/>
          <t:FieldURI FieldURI="calendar:Start"/>
          <t:FieldURI FieldURI="calendar:End"/>
          <t:FieldURI FieldURI="calendar:Location"/>
        </t:AdditionalProperties>
      </m:ItemShape>
      <m:CalendarView StartDate="${start}" EndDate="${end}"/>
      <m:ParentFolderIds><t:DistinguishedFolderId Id="calendar"/></m:ParentFolderIds>
    </m:FindItem>
${SOAP_TAIL}`;

  const doc = await makeEws(soap);
  const items = doc.getElementsByTagNameNS(T_NS, "CalendarItem");
  const events: CalendarEvent[] = [];
  for (let i = 0; i < items.length; i++) {
    const el = items[i];
    const startStr = firstText(el, "Start");
    if (!startStr) continue;
    const endStr = firstText(el, "End");
    events.push({
      subject: firstText(el, "Subject"),
      start: toLocalIso(new Date(startStr)),
      end: endStr ? toLocalIso(new Date(endStr)) : null,
      location: firstText(el, "Location"),
    });
  }
  return events;
}

// Die jüngsten Posteingangs-Mails (EWS FindItem -> GetItem für Textkörper).
export async function getRecentInbox(max = 12): Promise<EmailIn[]> {
  const findSoap = `${SOAP_HEAD}
    <m:FindItem Traversal="Shallow">
      <m:ItemShape><t:BaseShape>IdOnly</t:BaseShape></m:ItemShape>
      <m:IndexedPageItemView MaxEntriesReturned="${max}" Offset="0" BasePoint="Beginning"/>
      <m:ParentFolderIds><t:DistinguishedFolderId Id="inbox"/></m:ParentFolderIds>
    </m:FindItem>
${SOAP_TAIL}`;

  const findDoc = await makeEws(findSoap);
  const found = findDoc.getElementsByTagNameNS(T_NS, "Message");
  const ids: { id: string; changeKey: string }[] = [];
  for (let i = 0; i < found.length; i++) {
    const idEl = found[i].getElementsByTagNameNS(T_NS, "ItemId")[0];
    if (idEl) {
      ids.push({
        id: idEl.getAttribute("Id") ?? "",
        changeKey: idEl.getAttribute("ChangeKey") ?? "",
      });
    }
  }
  if (ids.length === 0) return [];

  const itemIdsXml = ids
    .map((x) => `<t:ItemId Id="${x.id}" ChangeKey="${x.changeKey}"/>`)
    .join("");
  const getSoap = `${SOAP_HEAD}
    <m:GetItem>
      <m:ItemShape>
        <t:BaseShape>IdOnly</t:BaseShape>
        <t:BodyType>Text</t:BodyType>
        <t:AdditionalProperties>
          <t:FieldURI FieldURI="item:Subject"/>
          <t:FieldURI FieldURI="message:From"/>
          <t:FieldURI FieldURI="item:Body"/>
        </t:AdditionalProperties>
      </m:ItemShape>
      <m:ItemIds>${itemIdsXml}</m:ItemIds>
    </m:GetItem>
${SOAP_TAIL}`;

  const getDoc = await makeEws(getSoap);
  const msgs = getDoc.getElementsByTagNameNS(T_NS, "Message");
  const emails: EmailIn[] = [];
  for (let i = 0; i < msgs.length; i++) {
    const el = msgs[i];
    emails.push({
      subject: firstText(el, "Subject"),
      from: firstText(el, "EmailAddress"),
      body: truncate(firstText(el, "Body"), 4000),
    });
  }
  return emails;
}
