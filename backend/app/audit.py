"""Datensparsames Audit-Log: protokolliert WAS getan wurde, niemals den INHALT."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import Settings


def write_audit(
    settings: Settings,
    *,
    endpoint: str,
    model_used: str,
    escalated: bool,
    latency_ms: float,
    **extra: Any,
) -> str:
    request_id = str(uuid.uuid4())
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "endpoint": endpoint,
        "model_used": model_used,
        "escalated": escalated,
        "latency_ms": round(latency_ms),
        **extra,
    }
    try:
        with open(settings.audit_log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Ein fehlschlagendes Audit darf den fachlichen Request niemals blockieren.
        pass
    return request_id
