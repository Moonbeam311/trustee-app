import ast
import importlib
import sqlite3
import sys
from pathlib import Path

import pytest

from database.startup_migrations import run_additive_startup_migrations


ROOT = Path(__file__).resolve().parent.parent
FIRM = "FIRM-CONVERGENCE"
OWNER = "OWNER-CONVERGENCE"


def _legacy_calls():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    names = {"update_trust_fields", "update_trust_fields_in_scope"}
    return [
        (node.func.id, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in names
    ]


def test_app_has_no_legacy_canonical_trust_writer_calls():
    assert _legacy_calls() == []


@pytest.fixture(scope="module")
def routed_app(tmp_path_factory):
    path = tmp_path_factory.mktemp("trust-convergence") / "app.sqlite3"
    import os

    previous = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = str(path)
    os.environ["ENSURE_HOSTED_ADMIN"] = "0"
    for name in ("app", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    module.user_has_effective_permission = lambda *_args, **_kwargs: True
    yield module, path
    if previous is None:
        os.environ.pop("DB_PATH", None)
    else:
        os.environ["DB_PATH"] = previous


def _login(client, *, firm=FIRM, owner=OWNER):
    with client.session_transaction() as session:
        session.update(
            username="operator@example.test",
            user_id="USER-CONVERGENCE",
            role="Admin",
            firm_id=firm,
            owner_id=owner,
            last_activity=4102444800.0,
            _csrf_token="csrf-convergence",
        )


def _insert_trust(path, trust_id="TR-CONVERGENCE"):
    connection = sqlite3.connect(path)
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(trusts)")
    }
    values = {
        "trust_id": trust_id,
        "firm_id": FIRM,
        "owner_id": OWNER,
        "trust_name": "Original Trust",
        "short_name": "Original",
        "jurisdiction": "VA",
        "effective_date": "2030-01-01",
        "status": "Draft",
        "accounting_method": "cash",
    }
    selected = {key: value for key, value in values.items() if key in columns}
    connection.execute(
        f"INSERT INTO trusts ({', '.join(selected)}) VALUES "
        f"({', '.join('?' for _ in selected)})",
        tuple(selected.values()),
    )
    connection.commit()
    connection.close()
    return trust_id


def _rows(path, sql, params=()):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(sql, params).fetchall()
    finally:
        connection.close()


def test_initial_insert_and_identity_route_revision_behavior(routed_app):
    module, path = routed_app
    trust_id = _insert_trust(path)
    assert _rows(path, "SELECT * FROM trust_field_revisions") == []
    client = module.app.test_client()
    _login(client)

    unchanged = client.post(
        f"/trust/{trust_id}/identity-edit",
        data={"_csrf_token": "csrf-convergence", "trust_name": "Original Trust",
              "short_name": "Original", "jurisdiction": "VA",
              "effective_date": "2030-01-01"},
    )
    assert unchanged.status_code == 302
    assert _rows(path, "SELECT * FROM trust_field_revisions") == []

    changed = client.post(
        f"/trust/{trust_id}/identity-edit",
        data={"_csrf_token": "csrf-convergence", "trust_name": "Corrected Trust",
              "short_name": "Corrected", "jurisdiction": "MD",
              "effective_date": "2031-02-03"},
    )
    assert changed.status_code == 302
    revisions = _rows(path, "SELECT * FROM trust_field_revisions")
    assert {row["field_name"] for row in revisions} == {
        "trust_name", "short_name", "jurisdiction", "effective_date"
    }
    assert {row["revision_basis"] for row in revisions} == {"trust_identity_correction"}
    assert {row["actor_id"] for row in revisions} == {"USER-CONVERGENCE"}


def test_wizard_status_is_revisioned_without_execution_or_funding_state(routed_app):
    module, path = routed_app
    trust_id = "TR-WIZARD"
    _insert_trust(path, trust_id)
    client = module.app.test_client()
    _login(client)
    response = client.post(
        f"/create_trust_step2/{trust_id}",
        data={"_csrf_token": "csrf-convergence", "trust_type": "revocable",
              "trust_purpose": "property_holding", "accounting_method": "accrual",
              "workflow_mode": "private_office"},
    )
    assert response.status_code == 302
    revisions = _rows(
        path, "SELECT field_name, resulting_value, revision_basis FROM trust_field_revisions WHERE trust_id=?",
        (trust_id,),
    )
    assert any(row["field_name"] == "trust_type" for row in revisions)
    status = next(row for row in revisions if row["field_name"] == "status")
    assert status["resulting_value"] == "Draft - Step 2 Complete"
    assert {row["revision_basis"] for row in revisions} == {"trust_formation_step2"}
    tables = {row[0] for row in _rows(path, "SELECT name FROM sqlite_master WHERE type='table'")}
    for table in ("execution_sessions", "transfers"):
        if table in tables:
            assert _rows(path, f"SELECT COUNT(*) AS count FROM {table}")[0]["count"] == 0


def test_branding_and_accounting_are_scoped_and_revisioned_with_audit(routed_app):
    module, path = routed_app
    trust_id = "TR-SETTINGS"
    _insert_trust(path, trust_id)
    client = module.app.test_client()
    _login(client)
    branding = client.post(
        f"/trust/{trust_id}/branding",
        data={"caf_number": "CAF-1", "branding_style": "v3_minimal"},
    )
    assert branding.status_code in {200, 302}
    accounting = client.post(
        f"/trust/{trust_id}/accounting-method",
        data={"_csrf_token": "csrf-convergence", "accounting_method": "accrual"},
    )
    assert accounting.status_code == 302
    revisions = _rows(path, "SELECT * FROM trust_field_revisions WHERE trust_id=?", (trust_id,))
    assert {row["revision_basis"] for row in revisions} >= {
        "trust_branding_settings", "trust_accounting_method"
    }
    assert _rows(path, "SELECT * FROM audit_log WHERE entity_id=?", (trust_id,))

    before = _rows(path, "SELECT trust_name FROM trusts WHERE trust_id=?", (trust_id,))[0][0]
    for firm, owner in (("OTHER-FIRM", OWNER), (FIRM, "OTHER-OWNER")):
        outsider = module.app.test_client()
        _login(outsider, firm=firm, owner=owner)
        assert outsider.post(
            f"/trust/{trust_id}/identity-edit",
            data={"_csrf_token": "csrf-convergence", "trust_name": "Forbidden"},
        ).status_code == 403
    assert _rows(path, "SELECT trust_name FROM trusts WHERE trust_id=?", (trust_id,))[0][0] == before


def test_startup_registration_succeeds_preserves_trust_and_defers_safely(tmp_path):
    good = tmp_path / "good.sqlite3"
    connection = sqlite3.connect(good)
    connection.execute(
        "CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, firm_id TEXT NOT NULL, owner_id TEXT NOT NULL, trust_name TEXT)"
    )
    connection.execute("INSERT INTO trusts VALUES ('TR-1', 'F-1', 'O-1', 'Untouched')")
    connection.commit()
    connection.close()
    result = run_additive_startup_migrations(good)["trust_field_revision_schema"]
    assert result["schema_complete"] is True
    assert _rows(good, "SELECT * FROM trusts")[0]["trust_name"] == "Untouched"
    assert _rows(good, "SELECT * FROM trust_field_revisions") == []

    absent = tmp_path / "absent.sqlite3"
    deferred = run_additive_startup_migrations(absent)["trust_field_revision_schema"]
    assert deferred["schema_complete"] is False
    assert deferred["deferred"] is True
    assert not _rows(absent, "SELECT name FROM sqlite_master WHERE name='trust_field_revisions'")
