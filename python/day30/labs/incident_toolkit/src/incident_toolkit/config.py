"""Application settings."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PKG_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INCIDENT_")

    api_token: str = "handbook-lab"
    log_json: bool = True
    metrics_port: int = 8080
    default_concurrency: int = 30
    hosts_registry: Path = PKG_ROOT / "hosts_registry.json"
    approved_playbook_dir: Path = PKG_ROOT.parent.parent.parent / "day21" / "labs" / "playbooks"


settings = Settings()
