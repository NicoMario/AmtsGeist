"""Leichtgewichtige PII-Pseudonymisierung (regelbasiert).

MVP-Stand: deckt strukturierte Identifikatoren (E-Mail, Telefon, IBAN) ab. Für den
Produktivbetrieb sollte dies durch eine deutsch-trainierte NER-Lösung (z. B. Presidio) ersetzt
werden, die auch Personennamen und Adressen erkennt. Siehe GitHub-Issue zum Datenschutz.

Wichtig: Bei rein on-prem-Betrieb ist Pseudonymisierung nicht erforderlich (die Daten verlassen
die Vertrauensgrenze nicht). Sie ist für das Cloud-Burst-Profil gedacht und daher per Default aus.
"""

from __future__ import annotations

import re

_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "IBAN": re.compile(r"\bDE\d{2}[ ]?(?:\d{4}[ ]?){4}\d{2}\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+49|0)[\d \-/()]{6,}\d"),
}


def pseudonymize(text: str) -> tuple[str, dict[str, str]]:
    """Ersetzt erkannte PII durch stabile Platzhalter.

    Gibt den maskierten Text und eine Mapping-Tabelle {Platzhalter: Original} zurück, mit der
    sich die Ausgabe bei Bedarf wieder rehydrieren lässt.
    """
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}

    def make_repl(kind: str):
        def repl(match: re.Match[str]) -> str:
            counters[kind] = counters.get(kind, 0) + 1
            token = f"[{kind}_{counters[kind]}]"
            mapping[token] = match.group(0)
            return token

        return repl

    for kind, pattern in _PATTERNS.items():
        text = pattern.sub(make_repl(kind), text)
    return text, mapping


def rehydrate(text: str, mapping: dict[str, str]) -> str:
    """Macht die Pseudonymisierung in einer Modell-Ausgabe rückgängig."""
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text
