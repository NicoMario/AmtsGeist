# Entwicklung & lokaler Betrieb

Drei Teile: **Ollama** (Modelle), das **Backend** ("das Gehirn") und das **Outlook-Add-in** (UI).

```
addin/  (Outlook, Office.js)  ──HTTPS──▶  backend/  (FastAPI)  ──▶  Ollama (qwen2.5:3b / :7b)
```

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
python -m pytest -q          # 13 Tests, ohne laufendes Modell (Modell wird gefakt)
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
- **Kalender (graph-frei):** Das Tagesbriefing nutzt (a) den **aktuell geöffneten Termin** —
  übernommen via Office.js ohne jede Sonderberechtigung — und (b) manuell eingetragene Termine,
  dazu die in der Sitzung gesammelten Mail-Zusammenfassungen. Der **vollständige Tageskalender** ist
  als nächster Schritt über **EWS mit Exchange-Dienstkonto (on-prem)** geplant — bewusst **ohne
  Microsoft Graph** (keine Azure-App-Registrierung/Admin-Consent nötig). Siehe Issue #8.
- **Eingangs-Triage:** Outlook bietet clientseitig **kein** "neue Mail eingegangen"-Event; echte
  Auto-Triage beim Eingang läuft serverseitig (EWS-Benachrichtigungen/Polling, Issue #10).
- **Kaskaden-Kalibrierung:** Die Eskalation stützt sich noch auf selbstberichtete Konfidenz
  (unzuverlässig, siehe eval/README.md). Kalibriertes Routing ist ein offener Punkt (Issue).
