"""Request-/Response-Schemata (öffentliche API) sowie die strukturierten Modell-Ausgaben."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Eingabe-Bausteine
# --------------------------------------------------------------------------- #
class EmailIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject: str = ""
    sender: str = Field(default="", alias="from")
    body: str
    received_at: datetime | None = None


class CalendarEvent(BaseModel):
    subject: str
    start: datetime
    end: datetime | None = None
    location: str = ""
    attendees: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Triage
# --------------------------------------------------------------------------- #
class TriageCategory(str, Enum):
    FRIST = "Frist"
    BUERGERANFRAGE = "Bürgeranfrage"
    INTERN = "Intern"
    NEWSLETTER = "Newsletter"
    SPAM = "Spam"
    ESKALATION = "Eskalation"


class TriageLLMOutput(BaseModel):
    """Was das Modell per Constrained Decoding emittiert (bewusst einfache Typen).

    Alle Felder sind *required* (ohne Default), damit das aus dem JSON-Schema abgeleitete
    Decoding-Grammatik-Konstrukt das Modell zwingt, jedes Feld zu erzeugen. Felder mit Default
    würden im Schema optional und vom Modell mitunter weggelassen.
    """

    category: TriageCategory
    priority: int = Field(ge=1, le=3, description="1=hoch, 2=mittel, 3=niedrig")
    deadline_iso: str = Field(
        description="Frist als YYYY-MM-DD; falls keine Frist erkennbar, leerer String"
    )
    suggested_folder: str
    reasoning: str = Field(description="Eine kurze Begründung in einem Satz")
    confidence: float = Field(ge=0.0, le=1.0)


class TriageResult(BaseModel):
    category: TriageCategory
    priority: int = Field(ge=1, le=3)
    deadline: date | None = None
    suggested_folder: str
    reasoning: str
    confidence: float


class TriageRequest(BaseModel):
    email: EmailIn


class TriageResponse(BaseModel):
    result: TriageResult
    model_used: str
    escalated: bool


# --------------------------------------------------------------------------- #
# Zusammenfassung
# --------------------------------------------------------------------------- #
class SummaryLLMOutput(BaseModel):
    # required (kein Default) -> Grammatik erzwingt beide Felder
    summary: str = Field(description="3-5 Sätze, sachlich, Verwaltungston")
    action_items: list[str] = Field(description="Konkrete nächste Schritte; leer falls keine")


class SummarizeRequest(BaseModel):
    emails: list[EmailIn] = Field(min_length=1)


class SummarizeResponse(BaseModel):
    summary: str
    action_items: list[str]
    model_used: str
    escalated: bool


# --------------------------------------------------------------------------- #
# Tagesbriefing
# --------------------------------------------------------------------------- #
class BriefingLLMOutput(BaseModel):
    # required (kein Default) -> Grammatik erzwingt alle Felder
    briefing_markdown: str = Field(description="Das Tagesbriefing in Markdown")
    deadlines: list[str] = Field(description="Heute/zeitnah fällige Fristen; leer falls keine")
    focus_blocks: list[str] = Field(description="Vorgeschlagene Fokus-Zeitfenster; leer falls keine")


class BriefingRequest(BaseModel):
    for_date: date
    events: list[CalendarEvent] = Field(default_factory=list)
    flagged_summaries: list[str] = Field(
        default_factory=list, description="Kurz-Zusammenfassungen markierter Mails"
    )


class BriefingResponse(BaseModel):
    briefing_markdown: str
    deadlines: list[str]
    focus_blocks: list[str]
    model_used: str
