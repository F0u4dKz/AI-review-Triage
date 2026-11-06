from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime settings. Environment variables override the defaults (API_KEY, LANDING_DIR)."""

    model_config = SettingsConfigDict(extra="ignore")

    api_key: str = "dev-key"
    landing_dir: Path = ROOT / "landing"
