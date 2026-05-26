"""Zusammenfassung einer oder mehrerer E-Mails."""

from __future__ import annotations

from ..config import Settings
from ..llm.router import CascadeRouter
from ..privacy.pii import pseudonymize
from ..prompts import SUMMARY_SYSTEM
from ..schemas import SummarizeRequest, SummarizeResponse, SummaryLLMOutput

# Ab dieser Zeichenlänge gilt der Vorgang als "lang" und wird direkt im LLM-Tier bearbeitet.
_LONG_TEXT_THRESHOLD = 4000


async def summarize(
    req: SummarizeRequest, router: CascadeRouter, settings: Settings
) -> SummarizeResponse:
    parts = []
    for i, email in enumerate(req.emails, start=1):
        parts.append(
            f"--- E-Mail {i} ---\n"
            f"Betreff: {email.subject}\n"
            f"Von: {email.sender}\n\n"
            f"{email.body}"
        )
    user = "\n\n".join(parts)
    if settings.enable_pii_pseudonymization:
        user, _ = pseudonymize(user)

    # Mehrere oder lange Mails -> Synthese gehört ins LLM-Tier; kurze Einzelmail -> Kaskade.
    force_llm = len(req.emails) > 1 or len(user) > _LONG_TEXT_THRESHOLD

    outcome = await router.structured(
        system=SUMMARY_SYSTEM,
        user=user,
        out_model=SummaryLLMOutput,
        force_llm=force_llm,
    )
    out: SummaryLLMOutput = outcome.value  # type: ignore[assignment]
    return SummarizeResponse(
        summary=out.summary,
        action_items=out.action_items,
        model_used=outcome.model_used,
        escalated=outcome.escalated,
    )
