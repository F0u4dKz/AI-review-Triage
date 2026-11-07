from pathlib import Path

import duckdb
import pytest

from publisher.pipeline import discard, publish, swap, wal_path


def test_failed_build_keeps_the_live_database(tmp_path: Path) -> None:
    current = tmp_path / "analytics.duckdb"
    nxt = tmp_path / "analytics_next.duckdb"
    current.write_text("live")
    nxt.write_text("rejected")
    wal_path(nxt).write_text("wal")

    with pytest.raises(SystemExit):
        publish(nxt, current, run_build=lambda: 1)

    assert current.read_text() == "live"
    assert not nxt.exists()
    assert not wal_path(nxt).exists()


def test_passed_build_swaps_the_database(tmp_path: Path) -> None:
    current = tmp_path / "analytics.duckdb"
    nxt = tmp_path / "analytics_next.duckdb"
    current.write_bytes(b"old")
    connection = duckdb.connect(nxt.as_posix())
    connection.execute("create table ready (id integer)")
    connection.close()

    publish(nxt, current, run_build=lambda: 0)

    assert not nxt.exists()
    check = duckdb.connect(current.as_posix(), read_only=True)
    try:
        assert check.execute("select count(*) from ready").fetchone() == (0,)
    finally:
        check.close()


def test_swap_refuses_a_leftover_wal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    current = tmp_path / "analytics.duckdb"
    nxt = tmp_path / "analytics_next.duckdb"
    current.write_text("live")
    nxt.write_bytes(b"next")
    wal_path(nxt).write_bytes(b"still here")

    class OpenConnection:
        def execute(self, _sql: str) -> None:
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr("publisher.pipeline.duckdb.connect", lambda *_args, **_kwargs: OpenConnection())

    with pytest.raises(RuntimeError, match="still present"):
        swap(nxt, current)

    assert current.read_text() == "live"
    assert nxt.read_bytes() == b"next"


def test_discard_removes_the_next_database_only(tmp_path: Path) -> None:
    current = tmp_path / "analytics.duckdb"
    nxt = tmp_path / "analytics_next.duckdb"
    current.write_text("live")
    nxt.write_text("next")

    discard(nxt)

    assert current.read_text() == "live"
    assert not nxt.exists()
