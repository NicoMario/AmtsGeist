"""Tagesbriefing aus Kalenderterminen und markierten E-Mail-Zusammenfassungen."""

from __future__ import annotations

from ..config import Settings
from ..llm.router import CascadeRouter
from ..privacy.pii import pseudonymize
from ..prompts import briefing_system
from ..schemas import BriefingLLMOutput, BriefingRequest, BriefingResponse


def _render_input(req: BriefingRequest) -> str:
    lines: list[str] = [f"Datum: {req.for_date.isoformat()}", "", "Termine:"]
    if req.events:
        for ev in sorted(req.events, key=lambda e: e.start):
            start = ev.start.strftime("%H:%M")
            end = f"-{ev.end.strftime('%H:%M')}" if ev.end else ""
            loc = f" @ {ev.location}" if ev.location else ""
            atts = f" (mit {', '.join(ev.attendees)})" if ev.attendees else ""
            lines.append(f"- {start}{end} {ev.subject}{loc}{atts}")
    else:
        lines.append("- (keine Termine)")

    lines += ["", "Markierte E-Mails (Zusammenfassungen):"]
    if req.flagged_summaries:
        lines += [f"- {s}" for s in req.flagged_summaries]
    else:
        lines.append("- (keine)")
    return "\n".join(lines)


async def briefing(
    req: BriefingRequest, router: CascadeRouter, settings: Settings
) -> BriefingResponse:
    user = _render_input(req)
    if settings.enable_pii_pseudonymization:
        user, _ = pseudonymize(user)

    outcome = await router.structured(
        system=briefing_system(req.for_date),
        user=user,
        out_model=BriefingLLMOutput,
        force_llm=True,  # Synthese gehört immer ins LLM-Tier
    )
    out: BriefingLLMOutput = outcome.value  # type: ignore[assignment]
    return BriefingResponse(
        briefing_markdown=out.briefing_markdown,
        deadlines=out.deadlines,
        focus_blocks=out.focus_blocks,
        model_used=outcome.model_used,
    )
