"""Antwort-Entwurf für eine eingegangene E-Mail (z. B. Bürgeranfrage)."""

from __future__ import annotations

from ..config import Settings
from ..llm.router import CascadeRouter
from ..privacy.pii import pseudonymize
from ..prompts import DRAFT_REPLY_SYSTEM
from ..schemas import DraftReplyLLMOutput, DraftReplyRequest, DraftReplyResponse


async def draft_reply(
    req: DraftReplyRequest, router: CascadeRouter, settings: Settings
) -> DraftReplyResponse:
    user = (
        f"Ursprüngliche E-Mail:\n"
        f"Betreff: {req.email.subject}\n"
        f"Von: {req.email.sender}\n\n"
        f"{req.email.body}"
    )
    if req.intent.strip():
        user += f"\n\nHinweise des Sachbearbeiters für die Antwort:\n{req.intent.strip()}"
    if settings.enable_pii_pseudonymization:
        user, _ = pseudonymize(user)

    outcome = await router.structured(
        system=DRAFT_REPLY_SYSTEM,
        user=user,
        out_model=DraftReplyLLMOutput,
        force_llm=True,  # Qualität vor Tempo: Entwürfe gehören ins LLM-Tier
    )
    out: DraftReplyLLMOutput = outcome.value  # type: ignore[assignment]
    return DraftReplyResponse(
        subject=out.subject, body=out.body, model_used=outcome.model_used
    )
