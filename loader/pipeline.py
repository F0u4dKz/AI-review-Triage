"""Copy landing parquet into raw.duckdb.

Transaction files are full snapshots, so each run replaces those tables.
Enrichment files arrive as new batches, so only files changed since the last
run are appended to reviews_enrichment.
"""

import duckdb
import dlt
from dlt.destinations.impl.duckdb.configuration import DuckDbCredentials
from dlt.sources.filesystem import filesystem, read_parquet
from pathlib import Path

from loader.config import ENRICHMENT_TABLE, STORAGE_COMPATIBILITY_VERSION


def ensure_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return
    connection = duckdb.connect(
        db_path.as_posix(),
        config={"storage_compatibility_version": STORAGE_COMPATIBILITY_VERSION},
    )
    connection.close()


def transaction_resources(transactions_dir: Path) -> list:
    resources = []
    for path in sorted(transactions_dir.glob("*.parquet")):
        files = filesystem(bucket_url=transactions_dir.as_posix(), file_glob=path.name)
        resources.append((files | read_parquet()).with_name(path.stem))
    return resources


def enrichment_resource(enrichments_dir: Path):
    files = filesystem(
        bucket_url=enrichments_dir.as_posix(),
        file_glob="*.parquet",
        incremental=dlt.sources.incremental("modification_date"),
    )
    resource = (files | read_parquet()).with_name(ENRICHMENT_TABLE)
    # Keep the list on the review row. dlt would otherwise split it into a child table.
    resource.apply_hints(columns={"key_issues": {"data_type": "json"}})
    return resource


def load(landing_dir: Path, db_path: Path, pipelines_dir: Path) -> None:
    transactions_dir = landing_dir / "transactions"
    enrichments_dir = landing_dir / "enrichments"
    names = [path.stem for path in sorted(transactions_dir.glob("*.parquet"))]
    if not names:
        raise SystemExit(f"No parquet files in {transactions_dir}. Run `make mock-transactions` first.")

    ensure_database(db_path)
    pipelines_dir.mkdir(parents=True, exist_ok=True)
    pipeline = dlt.pipeline(
        pipeline_name="raw",
        destination=dlt.destinations.duckdb(
            DuckDbCredentials(
                db_path.as_posix(),
                global_config={"storage_compatibility_version": STORAGE_COMPATIBILITY_VERSION},
            )
        ),
        dataset_name="main",
        pipelines_dir=pipelines_dir.as_posix(),
    )
    pipeline.run(transaction_resources(transactions_dir), write_disposition="replace")

    if any(enrichments_dir.glob("*.parquet")):
        pipeline.run(enrichment_resource(enrichments_dir), write_disposition="append")
        names.append(ENRICHMENT_TABLE)
    else:
        print(f"No enrichment parquet in {enrichments_dir}. Skipped {ENRICHMENT_TABLE}.")

    print_counts(pipeline, names)


def print_counts(pipeline: dlt.Pipeline, names: list[str]) -> None:
    with pipeline.sql_client() as client:
        for name in names:
            count = client.execute_sql(f'SELECT COUNT(*) FROM "{name}"')[0][0]
            print(f"{name:<24} {count:>6} rows")
