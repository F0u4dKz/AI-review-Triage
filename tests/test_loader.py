import json
from pathlib import Path

import duckdb
import pandas as pd

from loader.config import ENRICHMENT_TABLE
from loader.pipeline import load


def write_transactions(folder: Path, products: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"product_id": list(range(1, products + 1)), "name": ["Mug"] * products}).to_parquet(
        folder / "product.parquet",
        index=False,
    )
    pd.DataFrame({"client_id": [1], "name": ["Ada"]}).to_parquet(folder / "clients.parquet", index=False)


def write_enrichment(folder: Path, name: str, review_id: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "review_id": [review_id],
        "key_issues": [["overpriced"]],
        "sentiment_score": [-0.4],
    }).to_parquet(folder / name, index=False)


def table_names(db_path: Path) -> set[str]:
    connection = duckdb.connect(db_path.as_posix(), read_only=True)
    try:
        rows = connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    finally:
        connection.close()
    return {row[0] for row in rows}


def test_load_replaces_transactions_and_appends_new_enrichment_files(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    db_path = tmp_path / "raw.duckdb"
    pipelines = tmp_path / "pipelines"
    write_transactions(landing / "transactions", products=2)
    write_enrichment(landing / "enrichments", "batch1.parquet", "a")

    load(landing, db_path, pipelines)

    connection = duckdb.connect(db_path.as_posix(), read_only=True)
    assert connection.execute("SELECT COUNT(*) FROM product").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 1
    issues = connection.execute(f'SELECT key_issues FROM "{ENRICHMENT_TABLE}"').fetchone()[0]
    connection.close()
    assert json.loads(issues) == ["overpriced"]
    assert f"{ENRICHMENT_TABLE}__key_issues" not in table_names(db_path)

    write_transactions(landing / "transactions", products=3)
    write_enrichment(landing / "enrichments", "batch2.parquet", "b")
    load(landing, db_path, pipelines)

    connection = duckdb.connect(db_path.as_posix(), read_only=True)
    assert connection.execute("SELECT COUNT(*) FROM product").fetchone()[0] == 3
    assert connection.execute(f'SELECT COUNT(*) FROM "{ENRICHMENT_TABLE}"').fetchone()[0] == 2
    connection.close()

    load(landing, db_path, pipelines)
    connection = duckdb.connect(db_path.as_posix(), read_only=True)
    assert connection.execute(f'SELECT COUNT(*) FROM "{ENRICHMENT_TABLE}"').fetchone()[0] == 2
    connection.close()
