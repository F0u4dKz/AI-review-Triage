from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class WorkerSettings(BaseSettings):
    """Runtime settings. Environment variables override the defaults."""

    model_config = SettingsConfigDict(extra="ignore")

    landing_dir: Path = ROOT / "landing"
    ollama_url: str = "http://127.0.0.1:11434/api/chat"
    model_name: str = "llama3"
    batch_size: int = 10
    max_tries: int = 3
    poll_seconds: float = 2.0
    request_timeout: float = 120.0
