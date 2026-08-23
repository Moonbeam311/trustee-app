import importlib
import re
import sqlite3
import sys
import time

import pytest

from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
from services.services_intake_trust_bridge import (
    BridgeError,
    create_continuity_profile,
    get_continuity_profile,
)


def _prepare_database(db_path):
    connection = sqlite3.connect(db_path)
    connection.execute(
        """CREATE TABLE trusts(
               trust_id TEXT PRIMARY KEY, trust_name TEXT NOT NULL, firm_id TEXT
           )"""
    )
    connection.execute(
        """CREATE TABLE intake_document_recommendations(
               id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT, firm_id TEXT,
               workflow_key TEXT, title TEXT, reason TEXT, status TEXT,
               created_at TEXT, updated_at TEXT, created_by TEXT
           )"""
    )
    connection.executemany(
        "INSERT INTO trusts(trust_id,trust_name,firm_id) VALUES(?,?,?)",
        (
            ("TR-A", "Firm A Trust", "FIRM-A"),
            ("TR-B", "Second Firm A Trust", "FIRM-A"),
            ("TR-X", "Firm X Trust", "FIRM-X"),
        ),
    )
    connection.commit()
    connection.close()
    migrate_intake_trust_bridge(db_path)


def _add_bridge(db_path, bridge_id="BRG-A", trust_id="TR-A"):
    connection = sqlite3.connect(db_path)
    recommendation_id = connection.execute(
        """INSERT INTO intake_document_recommendations(
               intake_id,firm_id,workflow_key,title,reason,status,created_at,updated_at,created_by
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        ("INT-A", "FIRM-A", "declaration_of_trust", "Declaration", "Test", "accepted", "v1", "v1", "operator"),
    ).lastrowid
    connection.execute(
        """INSERT INTO intake_trust_formation_bridges(
               bridge_id,firm_id,intake_id,recommendation_id,workflow_key,selected_instrument,
               source_status,source_version,source_fingerprint,bridge_status,
               professional_review_disposition,confirmation_state,trust_id,idempotency_key,
               prepared_by,confirmed_by,launched_by,prepared_at,confirmed_at,launched_at,created_at,updated_at
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            bridge_id, "FIRM-A", "INT-A", recommendation_id, "declaration_of_trust",
            "declaration_of_trust", "accepted", "v1", "fingerprint", "trust_created",
            "clear", "confirmed", trust_id, f"{bridge_id}-key", "operator", "operator",
            "operator", "v1", "v1", "v1", "v1", "v1",
        ),
    )
    connection.commit()
    connection.close()


def _create(db_path, **overrides):
    values = {
        "firm_id": "FIRM-A",
        "subject_name": "Alex Example",
        "subject_type": "person",
        "capacities": "trustee",
        "purpose": "Continuity planning",
        "actor": "operator",
    }
    values.update(overrides)
    return create_continuity_profile(db_path, **values)


def _counts(db_path):
    connection = sqlite3.connect(db_path)
    result = tuple(
        connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("continuity_profiles", "continuity_events")
    )
    connection.close()
    return result


def test_same_firm_trust_binding_is_returned_by_profile_read(tmp_path):
    db_path = tmp_path / "same-firm.db"
    _prepare_database(db_path)
    profile_id = _create(db_path, trust_id="TR-A")

    bundle = get_continuity_profile(db_path, profile_id, "FIRM-A")

    assert bundle["profile"]["trust_id"] == "TR-A"
    assert bundle["profile"]["bridge_id"] is None
    assert get_continuity_profile(db_path, profile_id, "FIRM-X") is None


@pytest.mark.parametrize("trust_id", ["TR-MISSING", "TR-X"])
def test_missing_or_cross_firm_trust_is_rejected_without_mutation(tmp_path, trust_id):
    db_path = tmp_path / f"rejected-{trust_id}.db"
    _prepare_database(db_path)

    with pytest.raises(BridgeError, match="Trust is not available in this firm"):
        _create(db_path, trust_id=trust_id)

    assert _counts(db_path) == (0, 0)


def test_bridge_and_trust_provenance_must_match(tmp_path):
    db_path = tmp_path / "bridge-provenance.db"
    _prepare_database(db_path)
    _add_bridge(db_path)

    profile_id = _create(db_path, bridge_id="BRG-A", trust_id="TR-A", intake_id="INT-A")
    profile = get_continuity_profile(db_path, profile_id, "FIRM-A")["profile"]
    assert (profile["bridge_id"], profile["trust_id"], profile["intake_id"]) == ("BRG-A", "TR-A", "INT-A")
    before = _counts(db_path)

    with pytest.raises(BridgeError, match="governed Trust provenance"):
        _create(db_path, bridge_id="BRG-A", trust_id="TR-B")

    assert _counts(db_path) == before


def test_unbound_profile_remains_supported(tmp_path):
    db_path = tmp_path / "unbound.db"
    _prepare_database(db_path)
    profile_id = _create(db_path)
    profile = get_continuity_profile(db_path, profile_id, "FIRM-A")["profile"]
    assert profile["trust_id"] is None
    assert profile["bridge_id"] is None


def _load_isolated_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "route.db"))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    routes = importlib.import_module("routes_tpd1c")
    module.app.config.update(TESTING=True, SECRET_KEY="r1-route-test")
    return module.app, routes, tmp_path / "route.db"


def test_route_rejects_cross_firm_trust_without_profile_or_event(monkeypatch, tmp_path):
    app, routes, db_path = _load_isolated_app(monkeypatch, tmp_path)
    connection = sqlite3.connect(db_path)
    trust_columns = {row[1] for row in connection.execute("PRAGMA table_info(trusts)")}
    if "firm_id" not in trust_columns:
        connection.execute("ALTER TABLE trusts ADD COLUMN firm_id TEXT")
    connection.execute(
        "INSERT INTO trusts(trust_id,trust_name,firm_id) VALUES(?,?,?)",
        ("TR-X", "Firm X Trust", "FIRM-X"),
    )
    connection.commit()
    connection.close()
    migrate_intake_trust_bridge(db_path)

    client = app.test_client()
    with client.session_transaction() as session:
        session.update(
            username="operator", user_id="USR-1", firm_id="FIRM-A",
            role="Admin", last_activity=time.time(),
        )
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda _user, permission: permission == "edit_trust")
    page = client.get("/continuity-profiles/new")
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', page.data).group(1).decode()

    response = client.post(
        "/continuity-profiles/new",
        data={
            "_csrf_token": token,
            "subject_name": "Alex Example",
            "subject_type": "person",
            "subject_capacities": "trustee",
            "primary_purpose": "Continuity planning",
            "trust_id": "TR-X",
        },
    )

    assert response.status_code in (200, 403)
    if response.status_code == 200:
        assert b"Trust is not available in this firm" in response.data
    assert _counts(db_path) == (0, 0)
