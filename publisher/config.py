from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CURRENT_DB = ROOT / "analytics.duckdb"
NEXT_DB = ROOT / "analytics_next.duckdb"
STORAGE_COMPATIBILITY_VERSION = "v1.5.5"
