# Add-in in Outlook ausprobieren (Sideload)

Schritt-für-Schritt, um den AmtsGeist-Assistenten lokal in Outlook zu laden und zu testen.
Fokus **macOS** (klassisches Outlook), mit Kurzhinweisen für Windows/Web.

> **Wichtig für die EWS-Funktionen** (Kalender laden, Posteingang einordnen): Diese brauchen das
> **klassische Outlook**. Im **„neuen Outlook"** und in Outlook im Web funktioniert `makeEwsRequestAsync`
> **nicht** — dort greift der Fallback (manuelle Termineingabe, Einzel-Triage der geöffneten Mail).
> Auf dem Mac oben rechts den Schalter **„Neues Outlook" ausschalten**.

---

## Schritt 1 — Backend + Modelle starten

```bash
# Ollama-Modelle (einmalig)
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b

# Backend
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Prüfen: `curl http://localhost:8000/health` muss `{"status":"ok", ...}` liefern.

## Schritt 2 — Dev-Zertifikat installieren (einmalig)

Outlook lädt das Task Pane nur über **HTTPS** und muss dem lokalen Zertifikat vertrauen:

```bash
cd addin
npm install                 # falls noch nicht geschehen
npx office-addin-dev-certs install
```

→ Fügt eine lokale Zertifizierungsstelle hinzu (macOS fragt nach dem Passwort). Danach ist
`https://localhost:3000` vertrauenswürdig.

## Schritt 3 — Add-in-Dev-Server starten

```bash
cd addin
npm run dev-server          # liefert das Task Pane unter https://localhost:3000
```

Im Browser einmalig `https://localhost:3000/taskpane.html` öffnen — es sollte ohne
Zertifikatswarnung laden. (Dieses Terminal offen lassen.)

## Schritt 4 — Sideload

### Variante A (macOS, klassisches Outlook) — empfohlen für EWS

```bash
mkdir -p ~/Library/Containers/com.microsoft.Outlook/Data/Documents/wef
cp addin/manifest.xml ~/Library/Containers/com.microsoft.Outlook/Data/Documents/wef/
```

Dann **Outlook komplett beenden** (⌘Q) und neu starten. Eine **E-Mail öffnen** → in der Leiste
bzw. im **…-Menü** erscheint **„AmtsGeist · Assistent öffnen"**.

### Variante B (automatisiert)

```bash
cd addin
npm start                   # startet Dev-Server + Sideload via office-addin-debugging
# Stoppen: npm run stop
```

### Variante C (Windows / Outlook im Web) — schneller UI-Test, OHNE EWS

Outlook → **Add-Ins abrufen** → **Meine Add-Ins** → **Benutzerdefiniertes Add-In** →
**Aus Datei hinzufügen** → `addin/manifest.xml` wählen.
(EWS-Funktionen sind hier deaktiviert; Zusammenfassen/Einordnen/Antwort-Entwurf funktionieren.)

## Schritt 5 — Benutzen

1. **E-Mail öffnen** → „Assistent öffnen" → **Zusammenfassen** / **Einordnen** (+ „Kategorie übernehmen")
   / **Antwort entwerfen** (öffnet einen Entwurf im Antwortfenster).
2. **Posteingang einordnen** → liest die jüngsten Mails (EWS) und sortiert nach Priorität.
3. **Termin öffnen** → „Assistent öffnen" → **Geöffneten Termin übernehmen**; oder
   **Kalender laden** (EWS) → **Tag vorbereiten** für das Tagesbriefing.
4. **Einstellungen** → Backend-Adresse setzen (wird im Postfach gespeichert), z. B. die RZ-Adresse.

---

## Troubleshooting

- **Task Pane bleibt leer / Zertifikatsfehler:** `npx office-addin-dev-certs install` erneut
  ausführen; `https://localhost:3000/taskpane.html` im Browser testen.
- **„Backend nicht erreichbar" / Fetch blockiert:** Läuft `uvicorn` auf Port 8000? `http://localhost`
  wird von Browsern i. d. R. als sicher behandelt; falls dennoch blockiert (Mixed Content), das
  Backend mit TLS starten:
  `uvicorn app.main:app --port 8000 --ssl-keyfile ~/.office-addin-dev-certs/localhost.key --ssl-certfile ~/.office-addin-dev-certs/localhost.crt`
  und in den Add-in-Einstellungen `https://localhost:8000` eintragen.
- **EWS-Funktionen tun nichts / „nur im klassischen Outlook":** „Neues Outlook" ist aktiv →
  ausschalten. (Fußzeile des Add-ins zeigt „EWS aktiv" bzw. „EWS n/v".)
- **Add-in erscheint nicht (Mac):** wirklich der `wef`-Ordner? Outlook vollständig mit ⌘Q beendet
  und neu gestartet?
- **Modelle fehlen:** `ollama list` muss `qwen2.5:3b` und `qwen2.5:7b` zeigen.

> Hinweis: Die EWS-Pfade sind gegen echtes Exchange noch nicht verifiziert — dies ist genau der
> erste Live-Test (Issue #11). Falls EWS-Aufrufe scheitern, bitte die Fehlermeldung notieren.
