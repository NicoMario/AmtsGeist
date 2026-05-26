# Eval-Harness — Triage-Benchmark

Der ehrliche Weg zu „Benchmark-Qualität": jede Modell-/Prompt-Änderung wird gegen ein
Golden-Set anonymisierter Verwaltungs-Mails gemessen. Das ist zugleich die nach EU AI Act
geforderte **dokumentierte Evaluation** für Hochrisiko-KI im öffentlichen Sektor.

## Ausführen

```bash
# Ollama muss laufen und die Modelle vorhalten (ollama pull qwen2.5:3b qwen2.5:7b)
cd backend
. .venv/bin/activate
python -m eval.run_eval

# Anderes Tier-1-Modell testen:
AMTSGEIST_SLM_MODEL=qwen2.5:7b python -m eval.run_eval
```

## Metriken

- **Precision/Recall/F1 pro Kategorie** — Recall auf `Frist` und `Eskalation` ist am wichtigsten:
  ein übersehener Eskalations- oder Fristfall ist der teuerste Fehler in der Verwaltung.
- **Fristen-Genauigkeit** — exakte Datums-Extraktion.
- **Eskalationsrate** — wie oft die Kaskade ans LLM-Tier eskaliert.
- **JSON-Fehler** — Anteil nicht schema-valider Ausgaben (sollte dank Constrained Decoding 0 sein).
- **Latenz p50**.

## Baseline (12 Beispiele, lokales Ollama, Stand Mai 2026)

| Modell-Tier | Accuracy | Macro-F1 | Fristen | Eskalation erkannt | Latenz p50 |
|---|---|---|---|---|---|
| **qwen2.5:3b** (SLM) | 58 % | 0.57 | 50 % | nein (R=0.0) | ~2.4 s |
| **qwen2.5:7b** (LLM) | 75 % | 0.76 | 100 % | teils (R=0.5) | ~4.6 s |

## Wichtigste Erkenntnis (und offener Punkt)

Die Kaskade eskalierte im Test **nie** (0 %), obwohl das 3B-Modell mehrere `Eskalation`- und
`Frist`-Fälle verfehlte. Grund: Das kleine Modell meldet durchgehend `confidence = 1.0` — die
**selbstberichtete Konfidenz ist nicht kalibriert** und taugt allein nicht als Eskalations-Signal.

→ Genau dafür ist der Harness da. Der nächste Schritt ist ein **kalibriertes Routing-Signal**
(Token-Margin/Logprobs + isotonische Regression, vgl. UCCI) statt der Selbstauskunft. Bis dahin ist
für hohe Qualität das **7B-Tier als Default** sinnvoll; die Kaskaden-Infrastruktur bleibt bestehen
und greift, sobald ein verlässliches Konfidenz-Signal oder ein stärkeres kleines Modell verdrahtet ist.
Dieser Punkt ist als GitHub-Issue erfasst.

> Hinweis: Das Golden-Set ist klein und synthetisch (anonymisiert). Für belastbare Zahlen muss es
> mit echten, datenschutzkonform anonymisierten Verwaltungs-Mails erweitert werden.
