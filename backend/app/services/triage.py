"""Triage: eingehende E-Mail klassifizieren, priorisieren, Frist erkennen, Ordner vorschlagen."""

from __future__ import annotations

import asyncio
from datetime import date, datetime

from ..config import Settings
from ..llm.router import CascadeRouter
from ..privacy.pii import pseudonymize
from ..prompts import TRIAGE_SYSTEM
from ..schemas import EmailIn, TriageLLMOutput, TriageRequest, TriageResponse, TriageResult


def _parse_deadline(raw: str) -> date | None:
    """Robust gegenüber ISO (YYYY-MM-DD) und deutschem Format (TT.MM.JJJJ).

    Kleinere Modelle halten sich nicht zuverlässig an ISO; daher parsen wir beide Varianten.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def email_to_prompt(email: EmailIn) -> str:
    return f"Betreff: {email.subject}\nVon: {email.sender}\n\n{email.body}"


async def triage(
    req: TriageRequest, router: CascadeRouter, settings: Settings
) -> TriageResponse:
    user = email_to_prompt(req.email)
    if settings.enable_pii_pseudonymization:
        user, _ = pseudonymize(user)

    outcome = await router.structured(
        system=TRIAGE_SYSTEM,
        user=user,
        out_model=TriageLLMOutput,
        confidence_of=lambda o: o.confidence,
    )
    out: TriageLLMOutput = outcome.value  # type: ignore[assignment]

    result = TriageResult(
        category=out.category,
        priority=out.priority,
        deadline=_parse_deadline(out.deadline_iso),
        suggested_folder=out.suggested_folder,
        reasoning=out.reasoning,
        confidence=out.confidence,
    )
    return TriageResponse(
        result=result, model_used=outcome.model_used, escalated=outcome.escalated
    )


async def triage_many(
    emails: list[EmailIn], router: CascadeRouter, settings: Settings
) -> list[TriageResponse]:
    """Stapel-Triage (z. B. Posteingang). Begrenzte Nebenläufigkeit schont das Modell."""
    semaphore = asyncio.Semaphore(4)

    async def _one(email: EmailIn) -> TriageResponse:
        async with semaphore:
            return await triage(TriageRequest(email=email), router, settings)

    return await asyncio.gather(*(_one(e) for e in emails))
