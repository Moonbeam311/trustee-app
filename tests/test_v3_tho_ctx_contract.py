import sqlite3

import database.db as db
from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
from services.services_intake_trust_bridge import get_continuity_profile
import services.services_trust_contract as trust_contract
import services.services_trust_continuity_context as contract


def _database(tmp_path, monkeypatch):
    path = tmp_path / "ctx-contract.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-A")
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, trust_name TEXT, status TEXT, firm_id TEXT)"
    )
    connection.executemany(
        "INSERT INTO trusts VALUES (?,?,?,?)",
        (
            ("TR-A", "Alpha", "Active", "FIRM-A"),
            ("TR-U", "Unlinked", "Active", "FIRM-A"),
            ("TR-X", "Other Firm", "Active", "FIRM-X"),
        ),
    )
    connection.commit()
    connection.close()
    migrate_intake_trust_bridge(path)
    connection = sqlite3.connect(path)
    rows = (
        ("CP-2", "FIRM-A", "Second", "person", "successor", "draft", "continuity", "TR-A", "2026-08-20T11:00:00"),
        ("CP-1", "FIRM-A", "First", "person", "trustee", "active", "continuity", "TR-A", "2026-08-20T10:00:00"),
        ("CP-U", "FIRM-A", "Unlinked", "person", "owner", "draft", "continuity", None, "2026-08-20T09:00:00"),
        ("CP-X", "FIRM-X", "Cross Firm", "person", "owner", "draft", "continuity", "TR-X", "2026-08-20T09:00:00"),
        ("CP-BAD", "FIRM-A", "Bad Link", "person", "owner", "draft", "continuity", "TR-X", "2026-08-20T12:00:00"),
    )
    connection.executemany(
        """INSERT INTO continuity_profiles
           (continuity_profile_id,firm_id,subject_name,subject_type,subject_capacities,
            status,primary_purpose,trust_id,readiness_status,created_by,updated_by,
            created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,'needs_review','tester','tester',?,?)""",
        [row + (row[-1],) for row in rows],
    )
    connection.commit()
    connection.close()
    return path


def _snapshot(path):
    connection = sqlite3.connect(path)
    try:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in tables
        }
    finally:
        connection.close()


def allow(_identifier):
    return True


def test_trust_resolves_zero_or_many_profiles_deterministically(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    before = _snapshot(path)
    linked = contract.resolve_continuity_contexts_for_trust(
        "TR-A", db_path=path, trust_authorization_check=allow,
        continuity_authorization_check=allow,
    )
    assert linked["relationship_cardinality"] == "ZERO_OR_MANY"
    assert linked["relationship_state"] == contract.LINKED
    assert [row["continuity_profile_id"] for row in linked["continuity_profiles"]] == ["CP-1", "CP-2"]
    unlinked = contract.resolve_continuity_contexts_for_trust(
        "TR-U", db_path=path, trust_authorization_check=allow,
        continuity_authorization_check=allow,
    )
    assert unlinked["relationship_state"] == contract.UNLINKED
    assert unlinked["continuity_profiles"] == []
    assert _snapshot(path) == before


def test_missing_and_cross_firm_trusts_fail_safely(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    for trust_id in ("missing", "TR-X"):
        assert contract.resolve_continuity_contexts_for_trust(
            trust_id, db_path=path, trust_authorization_check=allow,
            continuity_authorization_check=allow,
        ) is None


def test_profile_resolves_linked_unlinked_and_inaccessible_trust(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    linked = contract.resolve_trust_context_for_continuity(
        "CP-1", db_path=path, trust_authorization_check=allow,
        continuity_authorization_check=allow,
    )
    assert linked["relationship_state"] == contract.LINKED
    assert linked["trust"]["trust_id"] == "TR-A"
    unlinked = contract.resolve_trust_context_for_continuity(
        "CP-U", db_path=path, trust_authorization_check=allow,
        continuity_authorization_check=allow,
    )
    assert unlinked["relationship_state"] == contract.UNLINKED
    assert unlinked["trust"] is None
    inaccessible = contract.resolve_trust_context_for_continuity(
        "CP-BAD", db_path=path, trust_authorization_check=allow,
        continuity_authorization_check=allow,
    )
    assert inaccessible["relationship_state"] == contract.NOT_FOUND_OR_NOT_ACCESSIBLE
    assert inaccessible["trust"] is None


def test_missing_cross_firm_and_denied_profiles_do_not_disclose(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    for profile_id in ("missing", "CP-X"):
        assert contract.resolve_trust_context_for_continuity(
            profile_id, db_path=path, trust_authorization_check=allow,
            continuity_authorization_check=allow,
        ) is None
    assert contract.resolve_trust_context_for_continuity(
        "CP-1", db_path=path, trust_authorization_check=allow,
        continuity_authorization_check=lambda _profile_id: False,
    ) is None


def test_authorization_required_and_source_contracts_remain_compatible(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    try:
        contract.resolve_continuity_contexts_for_trust(
            "TR-A", db_path=path, trust_authorization_check=None,
            continuity_authorization_check=allow,
        )
        assert False, "both authorization callbacks are required"
    except contract.TrustContinuityContextError:
        pass
    assert trust_contract.get_trust_by_id("TR-A", authorization_check=allow)["trust_id"] == "TR-A"
    assert get_continuity_profile(path, "CP-1", "FIRM-A")["profile"]["trust_id"] == "TR-A"
