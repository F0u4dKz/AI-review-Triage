"""Build analytics_next.duckdb, then swap it into place only if the tests pass."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import duckdb

from publisher.config import STORAGE_COMPATIBILITY_VERSION


def wal_path(database: Path) -> Path:
    return Path(str(database) + ".wal")


def discard(next_db: Path) -> None:
    next_db.unlink(missing_ok=True)
    wal_path(next_db).unlink(missing_ok=True)


def prepare(next_db: Path) -> None:
    """Close a clean checkpoint so the swap never carries a write-ahead log."""
    if wal_path(next_db).exists():
        connection = duckdb.connect(
            next_db.as_posix(),
            config={"storage_compatibility_version": STORAGE_COMPATIBILITY_VERSION},
        )
        try:
            connection.execute("CHECKPOINT")
        finally:
            connection.close()
    if wal_path(next_db).exists():
        raise RuntimeError(f"{wal_path(next_db).name} is still present, so the swap was skipped")


def swap(next_db: Path, current_db: Path) -> None:
    prepare(next_db)
    wal_path(current_db).unlink(missing_ok=True)
    os.replace(next_db, current_db)


def dbt_build() -> int:
    deps = subprocess.run(
        ["dbt", "deps", "--project-dir", "analytics", "--profiles-dir", "analytics"],
        check=False,
    )
    if deps.returncode != 0:
        return deps.returncode
    completed = subprocess.run(
        ["dbt", "build", "--project-dir", "analytics", "--profiles-dir", "analytics"],
        check=False,
    )
    return completed.returncode


def publish(next_db: Path, current_db: Path, run_build: Callable[[], int] = dbt_build) -> None:
    if run_build() != 0:
        discard(next_db)
        raise SystemExit(
            "dbt build failed. analytics.duckdb was left unchanged and analytics_next.duckdb was removed."
        )
    swap(next_db, current_db)
    print("Tests passed. analytics_next.duckdb replaced analytics.duckdb.")


def main() -> None:
    from publisher.config import CURRENT_DB, NEXT_DB

    publish(NEXT_DB, CURRENT_DB)
