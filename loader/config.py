from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANDING_DIR = ROOT / "landing"
RAW_DB = ROOT / "raw.duckdb"
PIPELINES_DIR = ROOT / ".dlt" / "pipelines"

# DuckDB 2 writes a storage version the installed CLI cannot open.
# v1.5.5 is the CLI that provides `duckdb -ui`, and newer CLIs can still read it.
STORAGE_COMPATIBILITY_VERSION = "v1.5.5"

ENRICHMENT_TABLE = "reviews_enrichment"
