import pytest

from app.config import Settings
from app.schemas import (
    BriefingLLMOutput,
    BriefingRequest,
    CalendarEvent,
    DraftReplyLLMOutput,
    DraftReplyRequest,
    EmailIn,
    SummarizeRequest,
    SummaryLLMOutput,
    TriageLLMOutput,
    TriageRequest,
)
from app.services import briefing as briefing_service
from app.services import draft as draft_service
from app.services import summarize as summarize_service
from app.services import triage as triage_service
from tests.helpers import FakeRouter


def _settings() -> Settings:
    return Settings(enable_pii_pseudonymization=False)


@pytest.mark.asyncio
async def test_triage_parses_deadline():
    router = FakeRouter(
        {
            TriageLLMOutput: TriageLLMOutput(
                category="Frist",
                priority=1,
                deadline_iso="2026-06-15",
                suggested_folder="Fristen",
                reasoning="Enthält eine Abgabefrist.",
                confidence=0.88,
            )
        }
    )
    req = TriageRequest(email=EmailIn(subject="Widerspruch", **{"from": "b@x.de"}, body="..."))
    resp = await triage_service.triage(req, router, _settings())
    assert resp.result.category.value == "Frist"
    assert resp.result.deadline is not None
    assert resp.result.deadline.isoformat() == "2026-06-15"


@pytest.mark.asyncio
async def test_triage_parses_german_date_format():
    router = FakeRouter(
        {
            TriageLLMOutput: TriageLLMOutput(
                category="Frist",
                priority=1,
                deadline_iso="15.06.2026",  # deutsches Format statt ISO
                suggested_folder="Fristen",
                reasoning="Frist genannt.",
                confidence=0.8,
            )
        }
    )
    req = TriageRequest(email=EmailIn(body="..."))
    resp = await triage_service.triage(req, router, _settings())
    assert resp.result.deadline is not None
    assert resp.result.deadline.isoformat() == "2026-06-15"


@pytest.mark.asyncio
async def test_triage_empty_deadline_is_none():
    router = FakeRouter(
        {
            TriageLLMOutput: TriageLLMOutput(
                category="Newsletter",
                priority=3,
                deadline_iso="",
                suggested_folder="Newsletter",
                reasoning="Rundschreiben.",
                confidence=0.92,
            )
        }
    )
    req = TriageRequest(email=EmailIn(body="Infodienst Mai"))
    resp = await triage_service.triage(req, router, _settings())
    assert resp.result.deadline is None


@pytest.mark.asyncio
async def test_summarize_multiple_forces_llm():
    router = FakeRouter(
        {SummaryLLMOutput: SummaryLLMOutput(summary="Zusammenfassung.", action_items=["A", "B"])}
    )
    req = SummarizeRequest(
        emails=[EmailIn(body="Mail eins"), EmailIn(body="Mail zwei")]
    )
    resp = await summarize_service.summarize(req, router, _settings())
    assert resp.action_items == ["A", "B"]
    assert router.calls[0]["force_llm"] is True  # mehrere Mails -> LLM-Tier


@pytest.mark.asyncio
async def test_draft_reply_includes_intent_in_prompt():
    router = FakeRouter(
        {
            DraftReplyLLMOutput: DraftReplyLLMOutput(
                subject="AW: Ummeldung", body="Sehr geehrte Frau [Name], ..."
            )
        }
    )
    req = DraftReplyRequest(
        email=EmailIn(subject="Ummeldung", body="Welche Unterlagen brauche ich?"),
        intent="Hinweis auf Online-Terminbuchung geben",
    )
    resp = await draft_service.draft_reply(req, router, _settings())
    assert resp.subject == "AW: Ummeldung"
    assert router.calls[0]["force_llm"] is True
    assert "Online-Terminbuchung" in router.calls[0]["user"]


@pytest.mark.asyncio
async def test_triage_many_returns_one_per_email():
    router = FakeRouter(
        {
            TriageLLMOutput: TriageLLMOutput(
                category="Intern",
                priority=2,
                deadline_iso="",
                suggested_folder="Intern",
                reasoning="x",
                confidence=0.9,
            )
        }
    )
    emails = [EmailIn(body="a"), EmailIn(body="b"), EmailIn(body="c")]
    results = await triage_service.triage_many(emails, router, _settings())
    assert len(results) == 3
    assert all(r.result.category.value == "Intern" for r in results)


@pytest.mark.asyncio
async def test_briefing_builds_and_calls_llm():
    router = FakeRouter(
        {
            BriefingLLMOutput: BriefingLLMOutput(
                briefing_markdown="# Tag", deadlines=["Frist X"], focus_blocks=["09-11 Uhr"]
            )
        }
    )
    req = BriefingRequest(
        for_date="2026-05-26",
        events=[CalendarEvent(subject="Teamrunde", start="2026-05-26T09:00:00")],
        flagged_summaries=["Bürgeranfrage Bauantrag"],
    )
    resp = await briefing_service.briefing(req, router, _settings())
    assert resp.briefing_markdown == "# Tag"
    assert router.calls[0]["force_llm"] is True
    # Termin- und Mail-Kontext landen im Prompt
    assert "Teamrunde" in router.calls[0]["user"]
    assert "Bauantrag" in router.calls[0]["user"]
