"""Test-Doubles: ein gefälschter Ollama-Client und ein gefälschter Router."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

from app.llm.router import StructuredOutcome


class FakeClient:
    """Liefert je Modell eine vorgegebene Antwort (oder wirft eine vorgegebene Exception)."""

    def __init__(self, by_model: dict[str, Any]) -> None:
        self.by_model = by_model
        self.seen: list[str] = []

    async def chat_json(
        self, model: str, system: str, user: str, schema: dict, *, temperature: float = 0.0
    ) -> dict:
        self.seen.append(model)
        value = self.by_model[model]
        if isinstance(value, Exception):
            raise value
        return value


class FakeRouter:
    """Gibt für jedes out_model eine vorbereitete Instanz zurück (umgeht echte Inferenz)."""

    def __init__(self, responses: dict[type[BaseModel], BaseModel]) -> None:
        self._responses = responses
        self.calls: list[dict] = []

    async def structured(
        self,
        *,
        system: str,
        user: str,
        out_model: type[BaseModel],
        confidence_of: Callable[[Any], float] = lambda _: 1.0,
        force_llm: bool = False,
    ) -> StructuredOutcome:
        self.calls.append({"out_model": out_model, "force_llm": force_llm, "user": user})
        value = self._responses[out_model]
        return StructuredOutcome(
            value=value, model_used="fake-model", escalated=force_llm
        )
