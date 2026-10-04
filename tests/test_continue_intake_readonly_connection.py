import sqlite3

import pytest

import database.db as db


def _create_database(path):
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE proof (id INTEGER PRIMARY KEY, value TEXT)"
    )
    connection.execute(
        "INSERT INTO proof (value) VALUES ('readable')"
    )
    connection.commit()
    connection.close()


def test_readonly_connection_can_read_existing_database(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "readonly.db"
    _create_database(path)

    monkeypatch.setattr(db, "DB_PATH", str(path))

    connection = db.get_readonly_connection()
    try:
        row = connection.execute(
            "SELECT value FROM proof WHERE id = 1"
        ).fetchone()
    finally:
        connection.close()

    assert row["value"] == "readable"


def test_readonly_connection_rejects_database_writes(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "readonly.db"
    _create_database(path)

    monkeypatch.setattr(db, "DB_PATH", str(path))

    connection = db.get_readonly_connection()
    try:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute(
                "INSERT INTO proof (value) VALUES ('blocked')"
            )
    finally:
        connection.close()

    verification = sqlite3.connect(path)
    try:
        count = verification.execute(
            "SELECT COUNT(*) FROM proof"
        ).fetchone()[0]
    finally:
        verification.close()

    assert count == 1


def test_readonly_connection_does_not_create_missing_database(
    tmp_path,
    monkeypatch,
):
    missing_parent = tmp_path / "missing-parent"
    path = missing_parent / "missing.db"

    monkeypatch.setattr(db, "DB_PATH", str(path))

    with pytest.raises(sqlite3.OperationalError):
        db.get_readonly_connection()

    assert not path.exists()
    assert not missing_parent.exists()
