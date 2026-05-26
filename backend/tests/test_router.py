import pytest

from app.config import Settings
from app.llm.router import CascadeRouter
from app.schemas import TriageLLMOutput
from tests.helpers import FakeClient

SLM = {
    "category": "Intern",
    "priority": 2,
    "deadline_iso": "",
    "suggested_folder": "Intern",
    "reasoning": "Dienstinterne Mail.",
    "confidence": 0.9,
}
SLM_UNSURE = {**SLM, "confidence": 0.4}
LLM = {**SLM, "category": "Eskalation", "priority": 1, "confidence": 0.95}


def _settings(**kw) -> Settings:
    base = dict(
        slm_model="slm",
        llm_model="llm",
        enable_cascade=True,
        escalation_confidence_threshold=0.75,
    )
    base.update(kw)
    return Settings(**base)


@pytest.mark.asyncio
async def test_slm_handles_when_confident():
    client = FakeClient({"slm": SLM, "llm": LLM})
    router = CascadeRouter(client, _settings())
    out = await router.structured(
        system="s", user="u", out_model=TriageLLMOutput, confidence_of=lambda o: o.confidence
    )
    assert out.model_used == "slm"
    assert out.escalated is False
    assert client.seen == ["slm"]


@pytest.mark.asyncio
async def test_escalates_when_unsure():
    client = FakeClient({"slm": SLM_UNSURE, "llm": LLM})
    router = CascadeRouter(client, _settings())
    out = await router.structured(
        system="s", user="u", out_model=TriageLLMOutput, confidence_of=lambda o: o.confidence
    )
    assert out.model_used == "llm"
    assert out.escalated is True
    assert client.seen == ["slm", "llm"]
    assert out.value.category.value == "Eskalation"


@pytest.mark.asyncio
async def test_force_llm_skips_slm():
    client = FakeClient({"slm": SLM, "llm": LLM})
    router = CascadeRouter(client, _settings())
    out = await router.structured(
        system="s", user="u", out_model=TriageLLMOutput, force_llm=True
    )
    assert client.seen == ["llm"]
    assert out.escalated is False


@pytest.mark.asyncio
async def test_escalates_on_invalid_slm_output():
    client = FakeClient({"slm": {"garbage": True}, "llm": LLM})
    router = CascadeRouter(client, _settings())
    out = await router.structured(
        system="s", user="u", out_model=TriageLLMOutput, confidence_of=lambda o: o.confidence
    )
    assert out.model_used == "llm"
    assert out.escalated is True
