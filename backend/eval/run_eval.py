"""Eval-Harness für die Triage — der ehrliche Weg zu 'Benchmark'.

Lädt ein Golden-Set anonymisierter Verwaltungs-Mails, lässt sie durch den Triage-Dienst laufen
und berechnet pro Kategorie Precision/Recall/F1 sowie Fristen-Genauigkeit, JSON-Validität,
Eskalationsrate und Latenz. So wird jede Modell-/Prompt-Änderung messbar (Qualitäts-Gate, vgl.
EU-AI-Act-Pflicht zur dokumentierten Evaluation).

Ausführen (laufendes Ollama vorausgesetzt):
    python -m eval.run_eval
    python -m eval.run_eval --golden eval/golden_set.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path

from app.config import Settings
from app.llm.client import OllamaClient
from app.llm.router import CascadeRouter
from app.schemas import EmailIn, TriageRequest
from app.services import triage as triage_service

CATEGORIES = ["Frist", "Bürgeranfrage", "Intern", "Newsletter", "Spam", "Eskalation"]


def load_golden(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="eval/golden_set.jsonl")
    args = parser.parse_args()

    settings = Settings()
    router = CascadeRouter(
        OllamaClient(settings.ollama_base_url, settings.request_timeout_s), settings
    )
    rows = load_golden(Path(args.golden))

    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)

    deadline_total = 0
    deadline_correct = 0
    escalations = 0
    errors = 0
    latencies: list[float] = []

    print(f"Golden-Set: {len(rows)} Beispiele | SLM={settings.slm_model} LLM={settings.llm_model}\n")

    for row in rows:
        req = TriageRequest(
            email=EmailIn(
                subject=row.get("subject", ""),
                **{"from": row.get("from", "")},
                body=row["body"],
            )
        )
        t0 = time.perf_counter()
        try:
            resp = await triage_service.triage(req, router, settings)
        except Exception as exc:  # noqa: BLE001 — Eval soll robust durchlaufen
            errors += 1
            print(f"  FEHLER bei '{row.get('subject', '')[:40]}': {exc}")
            continue
        latencies.append((time.perf_counter() - t0) * 1000)

        gold = row["expected_category"]
        pred = resp.result.category.value
        if pred == gold:
            tp[gold] += 1
        else:
            fp[pred] += 1
            fn[gold] += 1

        if resp.escalated:
            escalations += 1

        exp_dl = row.get("expected_deadline")
        if exp_dl:
            deadline_total += 1
            got = resp.result.deadline.isoformat() if resp.result.deadline else None
            if got == exp_dl:
                deadline_correct += 1

        mark = "✓" if pred == gold else "✗"
        print(f"  {mark} erwartet={gold:<14} erkannt={pred:<14} ({resp.model_used})")

    # ---- Bericht ----
    print("\n--- Pro Kategorie (Precision / Recall / F1) ---")
    f1s = []
    for cat in CATEGORIES:
        p, r, f1 = _prf(tp[cat], fp[cat], fn[cat])
        f1s.append(f1)
        print(f"  {cat:<14} P={p:0.2f}  R={r:0.2f}  F1={f1:0.2f}")

    n = len(rows)
    correct = sum(tp.values())
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0.0

    print("\n--- Gesamt ---")
    print(f"  Accuracy:            {correct}/{n} = {correct / n:0.1%}")
    print(f"  Macro-F1:            {macro_f1:0.2f}")
    if deadline_total:
        print(f"  Fristen-Genauigkeit: {deadline_correct}/{deadline_total} = {deadline_correct / deadline_total:0.1%}")
    print(f"  Eskalationsrate:     {escalations}/{n} = {escalations / n:0.1%}")
    print(f"  JSON-Fehler:         {errors}")
    print(f"  Latenz p50:          {p50:0.0f} ms")


if __name__ == "__main__":
    asyncio.run(main())
