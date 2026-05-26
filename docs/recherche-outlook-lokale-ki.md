# Recherche: Lokale-KI-Assistenten für Outlook (Prior Art)

> Stand: Mai 2026 — Wettbewerbs- und Vorarbeiten-Analyse für ein DSGVO-konformes,
> auf lokalen Modellen basierendes Outlook-Add-in (Zusammenfassen, Sortieren/Markieren,
> Kalender- und Tagesvorbereitung).

## Fragestellung

Gibt es bereits Initiativen (GitHub, Reddit, Produkte) für **Outlook-Add-ins**, die
**lokale Modelle** (auf dem Gerät oder einer VM) nutzen, um datenschutzkonform
E-Mails zusammenzufassen, zu sortieren/markieren, den Kalender zu prüfen und den
Arbeitstag vorzubereiten?

**Kurzfazit:** Die E-Mail-Seite ist gut erprobt — es existieren mehrere Open-Source-Projekte
und ein Forschungsprojekt. Die **Kalender-/Tagesbriefing-Seite mit lokalen Modellen** ist
weitgehend **unbesetzt**. Ein Add-in, das speziell für die **deutsche Verwaltung**
(souverän, on-device/on-prem, Mail **und** Kalender) gebaut ist, existiert nicht.

---

## 1. Direkte Treffer — Outlook + lokales Modell

| Projekt | Was es macht | Laufzeit/Modell | Relevanz |
|---|---|---|---|
| **[outlook-agents](https://github.com/bearded-impala/outlook-agents)** (`bearded-impala`) | Multi-Agent-Orchestrierung, überwacht Postfach, Agenten für Klassifikation, Zusammenfassung, Dringlichkeits- und Tonanalyse, Antwortentwürfe | **Ollama (lokal) + CrewAI** | ★★★ Am nächsten an „Zusammenfassen + Sortieren/Markieren" |
| **[OutlookLLM](https://github.com/fgblanch/OutlookLLM)** (`fgblanch`) | Echtes **Outlook-Add-in** (Task Pane): Verfassen, Zusammenfassen, Q&A | Lokales LLM via **Nvidia TensorRT-LLM** (Mistral 7B, Llama2 7B, Gemma 7B) | ★★★ Produktreifste Add-in-Architektur |
| **[outlook-bob](https://github.com/haesleinhuepf/outlook-bob)** (`haesleinhuepf`) | Antwort-Assistent, explizit Datenschutz-Forschungsprojekt — „nichts verlässt das Gerät" | **Lokale LLMs via Ollama** | ★★ Gute Referenz für transparenten, datenschutzorientierten Ansatz |
| **[AnythingLLM Outlook Agent](https://docs.anythingllm.com/agent/usage/outlook-agent)** | Desktop-App-Skill: E-Mails suchen, Threads lesen, verfassen/Entwürfe, Postfach-Statistik | Beliebige lokale Modelle | ★★ Breite Funktionalität, generischer Agent |
| **[SummaryAddIn](https://github.com/freistli/SummaryAddIn)** (`freistli`) | Outlook-Add-in für Zusammenfassung | **Backend-LLM-Service** (nicht zwingend lokal!) | ★ Souveränität vor Einsatz prüfen |

## 2. Angrenzend — gleiche Idee, Gmail oder generisch (übertragbare Muster)

| Projekt | Hinweis |
|---|---|
| **[Local-LLaMA-Email-Agent](https://github.com/isaiahshall/Local-LLaMA-Email-Agent)** (`isaiahshall`) | LLaMA3, on-device, Zusammenfassung + Aufgaben-Extraktion. Aktuell nur Gmail. |
| **[n8n + Ollama Workflows](https://n8n.io/workflows/2729-private-and-local-ollama-self-hosted-ai-assistant/)** | Mehrere self-hosted Templates für Inbox-Triage, Phishing-/Spam-Filter. Direkt auf dem Homelab prototypisierbar. |
| **[Ollama-LM-Studio-Gmail](https://github.com/nikaskeba/Ollama-LM-Studio-GPT-Gmail-Summarize-and-AI-Email-Writer)** | Flask + lokales GPT, Gmail prüfen + Auto-Antworten. |

## 3. Die Lücke: Kalender / Tagesbriefing

**Kein** reifes, lokal-first, Outlook-spezifisches Projekt gefunden. Die E-Mail-Seite ist
abgedeckt, die „Kalender prüfen und Tag vorbereiten"-Seite nicht. Bausteine existieren,
sind aber für souveräne Outlook-Nutzung nicht zusammengesetzt:

- **Microsoft Graph API** für Kalenderzugriff
- **Jan.ai** (lokal, MCP-fähig), **CrewAI** / **LangGraph** für die Agenten-Schicht
- **[Meetily](https://meetily.ai/)** macht private Meeting-Zusammenfassungen (Kalender-Integration „coming soon")

→ Ein lokales „Morgenbriefing", das Outlook-Kalender **und** Mail verknüpft, ist eine
**offene Nische**.

## 4. Deutscher / DSGVO-Kontext (Behörden)

- **[DSGPT](https://dsgpt.de/)** und **[patris.ai](https://patris.ai/en/)** vermarkten DSGVO-konforme,
  On-Premise-LLM-Lösungen; DSGPT nennt Behörden-Einsatz — aber als generischer Chat, **nicht** als
  Outlook-E-Mail-Triage.
- Aktive deutsche Presse-Warnungen zu **Microsoft 365 Copilot / neuen Outlook-KI-Agenten** und DSGVO
  (Datenspeicherung, Cloud-Zugriff der den lokalen IT-Schutz umgeht) — siehe
  [borncity](https://borncity.com/news/microsoft-outlook-neue-ki-agenten-schueren-datenschutz-alarm/).
  Genau dieser Schmerzpunkt rechtfertigt den lokal-first-Ansatz.
- **[Teuken-7B](https://huggingface.co/openGPT-X/Teuken-7B-instruct-v0.6)** (OpenGPT-X, Fraunhofer):
  EU-finanziertes, in allen 24 EU-Sprachen trainiertes, **Apache-2.0**-Modell — souverän schon
  durch Herkunft. Hochrelevant als Modellbasis für AmtsGeist.

## 5. Einordnung für AmtsGeist

Die **E-Mail-Triage-Hälfte** ist gut erprobt → Architektur von `outlook-agents` / `OutlookLLM`
übernehmen statt bei null beginnen. Aber **(a)** ein echtes Outlook-Add-in **für die deutsche
Verwaltung** und **(b)** lokal-modellbasierte Kalender-/Tagesvorbereitung sind beide unbesetzt.
Die Kombination — souverän, on-device/on-prem, Mail **und** Kalender, zugeschnitten auf die
öffentliche Verwaltung — ist offenbar **noch nicht adressiert**.

---

## Quellen

- [outlook-agents (Ollama + CrewAI)](https://github.com/bearded-impala/outlook-agents)
- [OutlookLLM (lokales LLM via TensorRT-LLM)](https://github.com/fgblanch/OutlookLLM)
- [outlook-bob (lokales Ollama, Datenschutz-Forschung)](https://github.com/haesleinhuepf/outlook-bob)
- [AnythingLLM Outlook Agent](https://docs.anythingllm.com/agent/usage/outlook-agent)
- [freistli/SummaryAddIn](https://github.com/freistli/SummaryAddIn)
- [Local-LLaMA-Email-Agent (Gmail, on-device)](https://github.com/isaiahshall/Local-LLaMA-Email-Agent)
- [Privates & lokales Ollama-Assistent-Template (n8n)](https://n8n.io/workflows/2729-private-and-local-ollama-self-hosted-ai-assistant/)
- [Outlook-Add-in mit LLM — GDPR/Compliance Q&A (Microsoft)](https://learn.microsoft.com/en-us/answers/questions/2126267/developing-an-outlook-add-in-with-llm-functionalit)
- [DSGPT — DSGVO-konformes GPT, On-Premise](https://dsgpt.de/)
- [patris.ai — DSGVO-konforme KI, Made in Germany](https://patris.ai/en/)
- [Microsoft Outlook KI-Agenten / Datenschutz-Alarm (borncity)](https://borncity.com/news/microsoft-outlook-neue-ki-agenten-schueren-datenschutz-alarm/)
- [Teuken-7B-instruct (OpenGPT-X, Hugging Face)](https://huggingface.co/openGPT-X/Teuken-7B-instruct-v0.6)
- [Meetily — privacy-first Meeting-Assistent](https://meetily.ai/)
