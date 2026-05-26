"""Modell-Kaskade: kleines Modell zuerst, Eskalation nur bei niedriger Konfidenz.

Hinweis: Die Eskalations-Entscheidung stützt sich derzeit auf die *selbstberichtete* Konfidenz
des Modells (grob, schlecht kalibriert) sowie auf Parse-/Validierungsfehler. Das ist bewusst der
einfachste tragfähige Mechanismus und der Platzhalter für ein später kalibriertes Routing
(Token-Margin + isotonische Regression, vgl. UCCI). Siehe GitHub-Issue zum Eval-/Kalibrierungs-Thema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from ..config import Settings
from .client import OllamaClient, OllamaError

T = TypeVar("T", bound=BaseModel)


@dataclass(slots=True)
class StructuredOutcome:
    value: BaseModel
    model_used: str
    escalated: bool


class CascadeRouter:
    def __init__(self, client: OllamaClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def structured(
        self,
        *,
        system: str,
        user: str,
        out_model: type[T],
        confidence_of: Callable[[T], float] = lambda _: 1.0,
        force_llm: bool = False,
    ) -> StructuredOutcome:
        """Strukturierte Ausgabe gemäß `out_model` mit optionaler Kaskade.

        - force_llm oder deaktivierte Kaskade -> direkt LLM-Tier.
        - sonst: SLM-Tier; bei Konfidenz < Schwelle oder Parse-/Validierungsfehler -> LLM-Tier.
        """
        schema = out_model.model_json_schema()
        s = self._settings

        if force_llm or not s.enable_cascade:
            value = await self._try(s.llm_model, system, user, schema, out_model)
            if value is None:  # auch das LLM kann scheitern -> sauberer Fehler
                raise OllamaError("LLM-Tier lieferte keine schema-valide Ausgabe.")
            return StructuredOutcome(value, s.llm_model, escalated=False)

        slm_value = await self._try(s.slm_model, system, user, schema, out_model)
        if (
            slm_value is not None
            and confidence_of(slm_value) >= s.escalation_confidence_threshold
        ):
            return StructuredOutcome(slm_value, s.slm_model, escalated=False)

        llm_value = await self._try(s.llm_model, system, user, schema, out_model)
        if llm_value is not None:
            return StructuredOutcome(llm_value, s.llm_model, escalated=True)

        # Letzter Rückfall: das (ggf. unsichere) SLM-Ergebnis ist besser als ein Fehler.
        if slm_value is not None:
            return StructuredOutcome(slm_value, s.slm_model, escalated=False)
        raise OllamaError("Weder SLM- noch LLM-Tier lieferten eine schema-valide Ausgabe.")

    async def _try(
        self,
        model: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        out_model: type[T],
    ) -> T | None:
        try:
            raw = await self._client.chat_json(model, system, user, schema)
            return out_model.model_validate(raw)
        except (json.JSONDecodeError, ValidationError, KeyError):
            return None
