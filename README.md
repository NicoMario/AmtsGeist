# AmtsGeist

> Souveräne KI-Infrastruktur für die deutsche öffentliche Verwaltung — lokal, datenschutzkonform, zukunftssicher.

---

## Die Idee

Deutschland digitalisiert seine Verwaltung. Doch KI-Systeme, die auf Cloud-Dienste amerikanischer oder asiatischer Anbieter angewiesen sind, widersprechen fundamentalen Anforderungen des öffentlichen Sektors: **DSGVO-Konformität, Datensouveränität und IT-Sicherheit nach BSI-Grundschutz.**

**AmtsGeist** ist ein offenes Framework, das Behörden, Kommunen und Ministerien ermöglicht, leistungsstarke KI-Assistenten vollständig **on-premise** zu betreiben — ohne dass sensible Bürger- oder Verwaltungsdaten jemals das eigene Rechenzentrum verlassen.

---

## Kernprinzipien

| Prinzip | Umsetzung |
|---|---|
| **Datensouveränität** | Alle Modelle laufen lokal — kein API-Call zu OpenAI, Google oder Azure |
| **DSGVO by Design** | Keine Telemetrie, keine Trainingsdaten-Weitergabe, vollständige Löschbarkeit |
| **Open Source First** | Nur quelloffene Modelle (Mistral, LLaMA, Phi, Gemma) und Infrastruktur |
| **BSI-konform** | Architektur orientiert sich an BSI IT-Grundschutz und NIS2 |
| **Interoperabilität** | Schnittstellen zu bestehenden Verwaltungssystemen (ELSTER, XÖV, eGov) |

---

## Anwendungsfälle

- **Dokumentenverarbeitung** — Automatisches Zusammenfassen, Klassifizieren und Weiterleiten von Schreiben und Bescheiden
- **Bürger-Kommunikation** — Entwurf datenschutzkonformer Antwortschreiben auf Bürgeranfragen
- **Wissensmanagement** — Internes RAG-System über Dienstvorschriften, Gesetze und Verwaltungsvorschriften
- **Meeting-Assistenz** — Lokale Transkription und Protokollierung von Sitzungen (via Whisper)
- **Formularausfüllung** — Intelligente Vorausfüllung von Verwaltungsformularen auf Basis von Akten

---

## Technologie-Stack

```
┌─────────────────────────────────────────────────┐
│                  Behörden-Netzwerk               │
│                                                  │
│  ┌─────────────┐    ┌──────────────────────────┐ │
│  │  Web-UI /   │    │     Ollama / vLLM         │ │
│  │  API-Gateway│───▶│  (Mistral, LLaMA, Phi)   │ │
│  └─────────────┘    └──────────────────────────┘ │
│         │                      │                 │
│  ┌──────▼──────┐    ┌──────────▼──────────────┐  │
│  │  RAG-Engine │    │   Whisper (lokal)        │  │
│  │  (ChromaDB) │    │   Spracherkennung        │  │
│  └─────────────┘    └──────────────────────────┘  │
│         │                                         │
│  ┌──────▼──────────────────────────────────────┐  │
│  │         Verwaltungs-Dokumentenstore         │  │
│  │      (eigene Infrastruktur / NAS / S3)      │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         ↕ Keine externen API-Calls
```

- **LLM-Runtime:** [Ollama](https://ollama.ai) oder [vLLM](https://github.com/vllm-project/vllm)
- **Empfohlene Modelle:** Mistral 7B/22B, LLaMA 3.1, Phi-3 Medium, Gemma 2
- **RAG:** ChromaDB + LangChain / LlamaIndex
- **Spracherkennung:** OpenAI Whisper (lokal)
- **Deployment:** Docker Compose / Kubernetes (on-premise)
- **Schnittstellen:** REST-API, OpenAI-kompatibles API-Format

---

## Zielgruppen

- Bundesministerien und Landesbehörden
- Kommunalverwaltungen und Landratsämter
- Öffentliche Schulen, Universitäten und Forschungseinrichtungen
- IT-Dienstleister im öffentlichen Sektor (AKDB, Dataport, DVZ, etc.)

---

## Outlook-Assistent (MVP)

Ein erster lauffähiger vertikaler Schnitt des Produkts liegt im Repo:

- **`backend/`** — FastAPI-Inferenzdienst ("das Gehirn" fürs Rechenzentrum): `/summarize`,
  `/triage`, `/triage/batch`, `/draft-reply`, `/briefing`, Modell-Kaskade (qwen2.5:3b → :7b),
  Constrained-Decoding-Klassifikation, PII-Schicht, datensparsames Audit-Log. Tests grün, gegen
  lokales Ollama verifiziert.
- **`addin/`** — Outlook-Add-in (Office.js): *Zusammenfassen*, *Einordnen* (+ Kategorie setzen),
  *Antwort entwerfen* (DSGVO-konform), *Posteingang einordnen* und *Tagesbriefing*. Kalender &
  Posteingang werden **graph-frei via EWS** gelesen (`makeEwsRequestAsync`, kein Azure/Admin);
  die Backend-Adresse wird ohne Datenbank in den **RoamingSettings** des Postfachs gespeichert.
  Build, Typecheck und Manifest-Validierung bestanden.
- **`backend/eval/`** — Benchmark-Harness mit Golden-Set (dokumentierte Evaluation, EU-AI-Act-tauglich).
- Start- und Testanleitung: [**docs/ENTWICKLUNG.md**](docs/ENTWICKLUNG.md);
  Outlook-Sideload Schritt für Schritt: [**docs/SIDELOAD.md**](docs/SIDELOAD.md).

Offene organisatorische/rechtliche Punkte (Vergaberecht, BSI, EU AI Act, DSGVO, Pilotbehörde …)
sind als [GitHub-Issues](https://github.com/NicoMario/AmtsGeist/issues) erfasst.

## Konzeptdokumente

- [**Architektur-Konzept: Souveräner KI-Assistent für Outlook**](docs/ARCHITEKTUR-Outlook-Assistent.md) — tiefes Design für Mail-Zusammenfassung, Triage/Markierung und Tagesbriefing, angepasst an reale Verwaltungs-Hardware (Thin Client/VDI), mit Modell-Kaskade, Deployment-Profilen und Mermaid-Diagrammen.
- [**Recherche: Lokale-KI-Assistenten für Outlook (Prior Art)**](docs/recherche-outlook-lokale-ki.md) — Wettbewerbs- und Vorarbeiten-Analyse (GitHub, Produkte, deutscher DSGVO-Kontext).

---

## Roadmap

- [ ] **v0.1** — Docker-Compose-Stack mit Ollama + Open WebUI
- [ ] **v0.2** — RAG-Pipeline für Verwaltungsdokumente
- [ ] **v0.3** — Whisper-Integration für Sitzungsprotokolle
- [ ] **v0.4** — API-Gateway mit RBAC und Audit-Log
- [ ] **v0.5** — Pilotbetrieb mit einer deutschen Kommunalverwaltung
- [ ] **v1.0** — BSI-Grundschutz-Dokumentation + Zertifizierungsvorbereitung

---

## Warum jetzt?

- Das **OZG (Onlinezugangsgesetz)** erzwingt digitale Verwaltungsleistungen bis 2025+
- Die **EU AI Act**-Anforderungen für Hochrisikosysteme im öffentlichen Sektor treten in Kraft
- Open-Source-Modelle haben 2024/2025 die Qualitätsschwelle für Verwaltungsaufgaben überschritten
- Souveräne KI ist politisch gewollt: **Gaia-X, IPCEI-CIS, Deutsche Verwaltungscloud**

---

## Mitmachen

Dieses Projekt steht am Anfang. Wenn du in der öffentlichen Verwaltung arbeitest, KI-Infrastruktur für Behörden entwickelst oder einfach glaubst, dass souveräne KI für Deutschland wichtig ist — **Issues und PRs sind willkommen.**

---

## Lizenz

MIT License — frei nutzbar, auch für Behörden und öffentliche Einrichtungen.

---

*AmtsGeist ist kein offizielles Regierungsprojekt. Es ist eine offene Initiative für souveräne KI in der deutschen Verwaltung.*
