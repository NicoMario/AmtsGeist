"""Dünner Client für die native Ollama-Chat-API mit JSON-Schema-Constrained-Decoding.

Bewusst über die native /api/chat-Schnittstelle, weil deren `format`-Feld ein JSON-Schema
annimmt und so strukturierte, schema-valide Ausgaben erzwingt. Ein vLLM-/IONOS-Backend ließe
sich analog über den OpenAI-kompatiblen Endpunkt anbinden.
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, timeout_s: float) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_s

    async def chat(
        self,
        model: str,
        system: str,
        user: str,
        *,
        fmt: dict[str, Any] | str | None = None,
        temperature: float = 0.1,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if fmt is not None:
            payload["format"] = fmt
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:  # Netzwerk / HTTP
            raise OllamaError(f"Ollama-Anfrage fehlgeschlagen: {exc}") from exc
        return data["message"]["content"]

    async def chat_json(
        self,
        model: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        *,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        content = await self.chat(
            model, system, user, fmt=schema, temperature=temperature
        )
        return json.loads(content)
