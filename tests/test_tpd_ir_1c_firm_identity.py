import importlib
import re
import sqlite3
import sys
import time

from database import db
from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge


def columns(path, table="trusts"):
    connection = sqlite3.connect(path)
    result = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    connection.close()
    return result


def test_fresh_database_creates_trust_firm_identity(monkeypatch, tmp_path):
    path = tmp_path / "fresh-firm-identity.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    assert "firm_id" in columns(path)


def test_legacy_migration_is_additive_idempotent_and_does_not_invent_firm(monkeypatch, tmp_path):
    path = tmp_path / "legacy-firm-identity.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE trusts(trust_id TEXT PRIMARY KEY, trust_name TEXT)")
    connection.execute("INSERT INTO trusts VALUES('TR-LEGACY-UNSCOPED','Legacy unscoped trust')")
    connection.commit()
    connection.close()

    migrate_intake_trust_bridge(path)
    migrate_intake_trust_bridge(path)
    assert "firm_id" in columns(path)
    connection = sqlite3.connect(path)
    assert connection.execute(
        "SELECT trust_id,firm_id FROM trusts WHERE trust_id='TR-LEGACY-UNSCOPED'"
    ).fetchone() == ("TR-LEGACY-UNSCOPED", None)
    connection.close()

    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-NOT-AUTHORITATIVE")
    assert db.get_trust_by_id("TR-LEGACY-UNSCOPED") is None


def test_trust_retrieval_and_mutation_are_firm_scoped(monkeypatch, tmp_path):
    path = tmp_path / "scoped-trust.db"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE trusts(trust_id TEXT PRIMARY KEY,trust_name TEXT,status TEXT,firm_id TEXT)"
    )
    connection.execute(
        "INSERT INTO trusts VALUES('TR-DISPOSABLE-FIRM-SCOPE','Scoped trust','Draft','FIRM-A')"
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(db, "DB_PATH", path)

    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-B")
    assert db.get_trust_by_id("TR-DISPOSABLE-FIRM-SCOPE") is None
    assert not db.update_trust_fields("TR-DISPOSABLE-FIRM-SCOPE", {"status": "Finalized", "firm_id": "FIRM-B"})

    connection = sqlite3.connect(path)
    assert connection.execute(
        "SELECT status,firm_id FROM trusts WHERE trust_id='TR-DISPOSABLE-FIRM-SCOPE'"
    ).fetchone() == ("Draft", "FIRM-A")
    connection.close()

    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-A")
    assert db.get_trust_by_id("TR-DISPOSABLE-FIRM-SCOPE")["firm_id"] == "FIRM-A"
    assert db.update_trust_fields("TR-DISPOSABLE-FIRM-SCOPE", {"status": "Reviewed", "firm_id": "FIRM-B"})
    connection = sqlite3.connect(path)
    assert connection.execute(
        "SELECT status,firm_id FROM trusts WHERE trust_id='TR-DISPOSABLE-FIRM-SCOPE'"
    ).fetchone() == ("Reviewed", "FIRM-A")
    connection.close()


def _load_isolated_app(monkeypatch, tmp_path):
    path = tmp_path / "route-continuity.db"
    monkeypatch.setenv("DB_PATH", str(path))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    sys.modules["database.db"].ensure_role_tables()
    module.app.config.update(TESTING=True, SECRET_KEY="tpd-ir-1c-route-test")
    monkeypatch.setattr(module, "user_has_effective_permission", lambda *_args: True)
    return module, path


def _session(client, *, firm_id="FIRM-ROUTE-A", role="Admin"):
    with client.session_transaction() as session:
        session["username"] = "route-test-operator"
        session["user_id"] = "USR-ROUTE"
        session["firm_id"] = firm_id
        session["role"] = role
        session["last_activity"] = time.time()


def _insert_route_trust(path, trust_id, trust_name, firm_id="FIRM-ROUTE-A"):
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO trusts(
               trust_id,trust_name,short_name,jurisdiction,effective_date,
               trust_type,trust_purpose,status,firm_id
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            trust_id, trust_name, trust_name, "Virginia", "2026-08-14",
            "Disposable route trust", "Route continuity validation",
            "Active", firm_id,
        ),
    )
    connection.commit()
    connection.close()


def _trust_state(path):
    connection = sqlite3.connect(path)
    rows = connection.execute(
        "SELECT trust_id,trust_name,status,firm_id FROM trusts ORDER BY trust_id"
    ).fetchall()
    connection.close()
    return rows


def test_admin_visible_count_rows_and_public_string_link_share_scope(monkeypatch, tmp_path):
    module, path = _load_isolated_app(monkeypatch, tmp_path)
    _insert_route_trust(path, "TR-ROUTE-STRING", "String Identifier Trust")
    client = module.app.test_client()
    _session(client)

    response = client.get("/admin")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Visible trusts</h3><strong>1</strong>" in body
    assert body.count('href="/trust/TR-ROUTE-STRING"') == 1
    assert "String Identifier Trust" in body
    assert "No trust records are visible in the current firm context." not in body
    rendered_rows = len(re.findall(r'<tr><td><strong><a href="/trust/', body))
    assert rendered_rows == 1

    detail = client.get("/trust/TR-ROUTE-STRING")
    assert detail.status_code == 200
    detail_body = detail.get_data(as_text=True)
    assert "String Identifier Trust" in detail_body
    assert "TR-ROUTE-STRING" in detail_body


def test_legacy_numeric_reference_remains_compatible(monkeypatch, tmp_path):
    module, path = _load_isolated_app(monkeypatch, tmp_path)
    _insert_route_trust(path, "101", "Legacy Numeric Reference Trust")
    client = module.app.test_client()
    _session(client)

    detail = client.get("/trust/101")
    assert detail.status_code == 200
    assert "Legacy Numeric Reference Trust" in detail.get_data(as_text=True)


def test_cross_firm_unauthorized_and_invalid_access_fail_without_trust_mutation(monkeypatch, tmp_path):
    module, path = _load_isolated_app(monkeypatch, tmp_path)
    _insert_route_trust(path, "TR-ROUTE-SCOPED", "Firm Scoped Route Trust")
    client = module.app.test_client()
    before = _trust_state(path)

    _session(client, firm_id="FIRM-ROUTE-B")
    cross_firm = client.get("/trust/TR-ROUTE-SCOPED")
    assert cross_firm.status_code == 403
    assert "Firm Scoped Route Trust" not in cross_firm.get_data(as_text=True)
    cross_admin = client.get("/admin")
    assert cross_admin.status_code == 200
    assert "Visible trusts</h3><strong>0</strong>" in cross_admin.get_data(as_text=True)

    _session(client, role="Trustee")
    assert client.get("/trust/TR-ROUTE-SCOPED").status_code == 403
    assert client.get("/admin").status_code == 403

    _session(client)
    invalid = client.get("/trust/TR-NOT-PRESENT")
    assert invalid.status_code == 403
    assert "TR-NOT-PRESENT" not in invalid.get_data(as_text=True)
    assert _trust_state(path) == before
