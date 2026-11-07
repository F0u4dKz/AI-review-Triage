"""Load landing/transactions and landing/enrichments into raw.duckdb."""

from loader.config import LANDING_DIR, PIPELINES_DIR, RAW_DB
from loader.pipeline import load


def main() -> None:
    load(LANDING_DIR, RAW_DB, PIPELINES_DIR)


if __name__ == "__main__":
    main()
