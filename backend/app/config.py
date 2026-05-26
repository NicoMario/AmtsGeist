"""Konfiguration. Alles per Umgebungsvariable (Prefix AMTSGEIST_) oder .env überschreibbar."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AMTSGEIST_", env_file=".env", extra="ignore"
    )

    # --- Inferenz-Backend (Ollama nativ; vLLM/IONOS via OpenAI-kompatibel ebenso anbindbar) ---
    ollama_base_url: str = "http://localhost:11434"
    request_timeout_s: float = 120.0

    # --- Modell-Kaskade ---
    # Tier 1: klein/günstig (CPU/NPU-fähig). Tier 2: Eskalation (GPU).
    slm_model: str = "qwen2.5:3b"
    llm_model: str = "qwen2.5:7b"
    # Souveräne Alternative (self-host oder IONOS AI Model Hub): z. B. "teuken-7b".

    enable_cascade: bool = True
    # Selbstberichtete Konfidenz ist nur eine grobe Näherung (Platzhalter für kalibriertes
    # Routing à la UCCI). Unter dieser Schwelle wird an das LLM-Tier eskaliert.
    escalation_confidence_threshold: float = 0.75

    # --- Datenschutz ---
    # Datensparsamkeit: bei rein on-prem-Betrieb nicht nötig (Daten bleiben lokal).
    # Für das Cloud-Burst-Profil (Daten verlassen die Vertrauensgrenze) einschalten.
    enable_pii_pseudonymization: bool = False

    # --- Generierung ---
    temperature: float = 0.1

    # --- Audit (datensparsam: niemals Inhalte) ---
    audit_log_path: str = "./audit.log.jsonl"

    # --- CORS: Ursprung des Outlook-Add-ins ---
    allowed_origins: list[str] = ["https://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
