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
