# Entwicklung & lokaler Betrieb

Drei Teile: **Ollama** (Modelle), das **Backend** ("das Gehirn") und das **Outlook-Add-in** (UI).

```
addin/  (Outlook, Office.js)  ──HTTPS──▶  backend/  (FastAPI)  ──▶  Ollama (qwen2.5:3b / :7b)
```

## Funktionen (alle ohne Entra/Azure/Admin)

| Funktion | Wie | Zugriff |
|---|---|---|
| E-Mail **zusammenfassen** | aktuelle Mail via Office.js → `/summarize` | keine Sonderrechte |
| E-Mail **einordnen** + Kategorie setzen | `/triage` → `item.categories` | keine Sonderrechte |
| **Antwort entwerfen** (DSGVO-konform) | `/draft-reply` → `displayReplyForm` | keine Sonderrechte |
| **Posteingang einordnen** (Stapel, sortiert) | EWS `getRecentInbox` → `/triage/batch` | EWS (klass. Outlook) |
| **Tagesbriefing** | EWS-Kalender / geöffneter Termin / manuell → `/briefing` | EWS bzw. keine |
| Backend-Adresse merken | RoamingSettings (im Postfach) | keine Sonderrechte |

> **Der USP:** Kalender- und Posteingangs-Zugriff laufen über **EWS via `makeEwsRequestAsync`** —
> mit dem Token, das das Add-in ohnehin hat. **Keine Azure-/Entra-App, kein Admin-Consent.**
> EWS funktioniert im **klassischen Outlook (Desktop/Mac)**; im neuen/Web-Outlook greift der
> Fallback (manuelle Termineingabe, Einzel-Triage der geöffneten Mail).

## Voraussetzungen

- Ollama mit den Modellen: `ollama pull qwen2.5:3b && ollama pull qwen2.5:7b`
- Python ≥ 3.11, Node ≥ 18
- Für das Add-in: Outlook (Desktop/Web/Neu) mit Möglichkeit zum Sideloading

## 1. Backend starten

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # bei Bedarf anpassen
uvicorn app.main:app --reload --port 8000
# Health-Check:  curl http://localhost:8000/health
```

Tests und Benchmark:

```bash
pip install -r requirements-dev.txt
python -m pytest -q          # 15 Tests, ohne laufendes Modell (Modell wird gefakt)
python -m eval.run_eval      # Triage-Benchmark gegen das echte Modell (siehe eval/README.md)
```

## 2. Add-in starten

```bash
cd addin
npm install
npm run validate             # Manifest prüfen
npm run dev-server           # liefert das Task Pane unter https://localhost:3000 aus
```

Sideloading in Outlook (vereinfacht; alternativ `npm start`):

- **Neues/Web-Outlook:** Einstellungen → Add-Ins verwalten → eigenes Add-in → `addin/manifest.xml` hochladen.
- Beim ersten Start das Dev-Zertifikat akzeptieren (`npx office-addin-dev-certs install`).

Im Task Pane: **Zusammenfassen** / **Einordnen** auf der geöffneten E-Mail, **Tag vorbereiten** für das Tagesbriefing.

## Alternativ: alles per Docker (Backend + Ollama)

```bash
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama pull qwen2.5:7b
```

## Bekannte Grenzen des MVP (ehrlich)

- **Live-Test in Outlook steht aus.** Backend (inkl. echtem Modell), Eval, Add-in-Build und
  Manifest-Validierung sind verifiziert; das Verhalten *im laufenden Outlook* wurde noch nicht
  durchgespielt (kein Office-Host in der Build-Umgebung).
- **EWS-Pfade gegen echtes Exchange ungetestet.** Kalender- und Posteingang-Lesen (EWS via
  `makeEwsRequestAsync`) sind implementiert, typgeprüft und gebaut — aber mangels Exchange-Test-
  umgebung **noch nicht gegen einen echten Server** verifiziert. Erster Pilot-Test nötig (Issue #11).
- **Kalender (graph-frei):** Tagesbriefing nutzt EWS-Kalender (klass. Outlook), den aktuell
  geöffneten Termin (Office.js) **oder** manuelle Eingabe — bewusst **ohne Microsoft Graph**
  (keine Azure-App/Admin-Consent). Siehe Issue #8.
- **Eingangs-Triage:** Die *manuelle* Posteingang-Triage (Button) liest die jüngsten Mails per EWS.
  Eine *automatische* Triage beim Eingang gibt es clientseitig nicht (kein "Mail eingegangen"-Event);
  das läuft serverseitig (EWS-Benachrichtigungen/Polling, Issue #10).
- **EWS schreibend (Kategorie auf nicht-geöffnete Mails):** noch nicht umgesetzt — Kategorie wird
  nur auf der *geöffneten* Mail via Office.js gesetzt (Issue #11).
- **Kaskaden-Kalibrierung:** Die Eskalation stützt sich noch auf selbstberichtete Konfidenz
  (unzuverlässig, siehe eval/README.md). Kalibriertes Routing ist ein offener Punkt (Issue).
