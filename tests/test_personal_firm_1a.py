import importlib
import os
import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import check_password_hash


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_FIRM = "PF-SYNTHETIC-9A7C"
SYNTHETIC_OWNER = "OWNER-SYNTHETIC-4D2E"
SYNTHETIC_USER = "synthetic_admin_1a"
SYNTHETIC_PASSWORD = "Synthetic-Only-Passphrase-1A!"


@pytest.fixture(scope="module")
def personal_firm_db(tmp_path_factory):
    target = tmp_path_factory.mktemp("personal-firm-1a") / "personal_firm.sqlite3"
    from scripts.init_personal_firm import initialize_personal_firm

    first = initialize_personal_firm(
        target, SYNTHETIC_FIRM, SYNTHETIC_USER, SYNTHETIC_PASSWORD, SYNTHETIC_OWNER
    )
    repeated = initialize_personal_firm(
        target, SYNTHETIC_FIRM, SYNTHETIC_USER, SYNTHETIC_PASSWORD, SYNTHETIC_OWNER
    )
    return target, first, repeated


def test_external_initializer_creates_explicit_hashed_admin_and_audit(personal_firm_db):
    target, first, repeated = personal_firm_db
    assert target.exists()
    assert first["status"] == "initialized"
    assert repeated["status"] == "already_initialized"

    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    try:
        users = connection.execute("SELECT * FROM app_users").fetchall()
        assert len(users) == 1
        user = users[0]
        assert user["role_name"] == "Admin"
        assert user["status"] == "active"
        assert user["firm_id"] == SYNTHETIC_FIRM
        assert user["owner_id"] == SYNTHETIC_OWNER
        assert user["password_hash"] != SYNTHETIC_PASSWORD
        assert SYNTHETIC_PASSWORD not in user["password_hash"]
        assert check_password_hash(user["password_hash"], SYNTHETIC_PASSWORD)
        assert user["firm_id"] not in {"FIRM-001", "FIRM-002", "FIRM-DEMO-001"}
        assert connection.execute("SELECT COUNT(*) FROM role_permissions WHERE role_name='Admin'").fetchone()[0] > 0
        marker = connection.execute(
            "SELECT * FROM audit_log WHERE action='personal_firm_initialized'"
        ).fetchone()
        assert marker is not None
        assert marker["firm_id"] == SYNTHETIC_FIRM
        assert SYNTHETIC_PASSWORD not in (marker["note"] or "")
        assert "trusts" not in {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        connection.close()
    assert os.environ.get("ENSURE_HOSTED_ADMIN") == "0"


def test_initializer_rejects_both_protected_repository_databases():
    from scripts.init_personal_firm import initialize_personal_firm

    for protected in (REPOSITORY_ROOT / "trustee_app.db", REPOSITORY_ROOT / "data" / "trustee_app.db"):
        with pytest.raises(ValueError, match="protected"):
            initialize_personal_firm(
                protected, SYNTHETIC_FIRM, SYNTHETIC_USER, SYNTHETIC_PASSWORD, SYNTHETIC_OWNER
            )


@pytest.fixture(scope="module")
def app_context(personal_firm_db):
    target = personal_firm_db[0]
    os.environ["DB_PATH"] = str(target)
    os.environ["ENSURE_HOSTED_ADMIN"] = "0"
    for module_name in [name for name in sys.modules if name == "app" or name == "database.db"]:
        sys.modules.pop(module_name, None)
    application_module = importlib.import_module("app")
    application_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return application_module, target


def _session_login(client, *, role="Admin", username=SYNTHETIC_USER, firm_id=SYNTHETIC_FIRM, owner_id=SYNTHETIC_OWNER):
    with client.session_transaction() as session:
        session["role"] = role
        session["username"] = username
        session["firm_id"] = firm_id
        session["owner_id"] = owner_id
        session["last_activity"] = 4102444800.0
        session["_csrf_token"] = "synthetic-csrf"


def test_login_uses_server_stored_firm_and_owner_scope(app_context):
    application_module, _ = app_context
    client = application_module.app.test_client()
    with client.session_transaction() as session:
        session["_csrf_token"] = "synthetic-login-csrf"
    response = client.post(
        "/login",
        data={"username": SYNTHETIC_USER, "password": SYNTHETIC_PASSWORD, "csrf_token": "synthetic-login-csrf"},
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["firm_id"] == SYNTHETIC_FIRM
        assert session["owner_id"] == SYNTHETIC_OWNER


def test_trust_wizard_fails_closed_and_uses_only_session_scope(app_context):
    application_module, target = app_context
    anonymous = application_module.app.test_client()
    assert anonymous.get("/create_trust_step1").status_code == 302

    denied = application_module.app.test_client()
    _session_login(denied, role="Viewer")
    assert denied.get("/create_trust_step1").status_code == 403

    missing_firm = application_module.app.test_client()
    _session_login(missing_firm, firm_id=None)
    assert missing_firm.get("/create_trust_step1").status_code == 403
    missing_owner = application_module.app.test_client()
    _session_login(missing_owner, owner_id=None)
    assert missing_owner.get("/create_trust_step1").status_code == 403

    permitted = application_module.app.test_client()
    _session_login(permitted)
    response = permitted.post(
        "/create_trust_step1",
        data={
            "_csrf_token": "synthetic-csrf",
            "trust_name": "Synthetic Trust",
            "short_name": "Synthetic",
            "jurisdiction": "Example",
            "effective_date": "2030-01-01",
            "firm_id": "ATTACKER-FIRM",
            "owner_id": "ATTACKER-OWNER",
        },
    )
    assert response.status_code == 302

    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    try:
        trust = connection.execute("SELECT * FROM trusts WHERE trust_name='Synthetic Trust'").fetchone()
        assert trust["firm_id"] == SYNTHETIC_FIRM
        assert trust["owner_id"] == SYNTHETIC_OWNER
        assert trust["firm_id"] != "ATTACKER-FIRM"
        assert trust["owner_id"] != "ATTACKER-OWNER"
        trust_id = trust["trust_id"]
    finally:
        connection.close()

    cross_firm = application_module.app.test_client()
    _session_login(cross_firm, firm_id="PF-OTHER-SYNTHETIC")
    assert cross_firm.get(f"/create_trust_step2/{trust_id}").status_code == 403


def test_required_permission_override_denies_creation(app_context):
    application_module, target = app_context
    connection = sqlite3.connect(target)
    try:
        connection.execute(
            "INSERT INTO user_permission_overrides (username, permission_name, effect) VALUES (?, 'create_trust', 'deny')",
            (SYNTHETIC_USER,),
        )
        connection.commit()
    finally:
        connection.close()
    client = application_module.app.test_client()
    _session_login(client)
    assert client.get("/create_trust_step1").status_code == 403


def test_execution_exports_honor_configured_root(tmp_path, monkeypatch):
    configured = tmp_path / "configured-exports"
    monkeypatch.setenv("EXPORT_ROOT", str(configured))
    sys.modules.pop("services.services_execution_exports", None)
    exports = importlib.import_module("services.services_execution_exports")
    exports.get_execution_session = lambda execution_id: {
        "session": {"execution_id": execution_id, "final_hash": "synthetic-hash"},
        "evidence_vault": {"package": {"package_id": "PKG-SYNTHETIC"}},
        "verification": {},
        "ledger": [],
        "signatures": [],
        "participants": [],
        "seals": [],
        "freezes": [],
    }
    package = exports.generate_execution_export_package("EXE-SYNTHETIC")
    result = Path(package["export_dir"])
    assert result.is_relative_to(configured.resolve() / "execution_packages")
    assert result.exists()
    repository_default = REPOSITORY_ROOT / "exports" / "execution_packages" / "PKG-SYNTHETIC"
    assert not repository_default.exists()
