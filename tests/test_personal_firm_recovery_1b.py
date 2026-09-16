import importlib
import re
import sqlite3
import sys
import time

import pytest
from werkzeug.security import check_password_hash, generate_password_hash


FIRM_ID = "PF-RECOVERY-TEST"
USERNAME = "recovery_owner"
OLD_PASSWORD = "Old-Recovery-Test-Password!1"
NEW_PASSWORD = "New-Recovery-Test-Password!2"


def _token(response):
    match = re.search(r'name="_csrf_token" value="([^"]+)"', response.get_data(as_text=True))
    assert match
    return match.group(1)


@pytest.fixture()
def recovery_app(monkeypatch, tmp_path):
    db_path = tmp_path / "personal-firm-recovery.sqlite3"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    monkeypatch.setenv("ENSURE_HOSTED_ADMIN", "0")
    monkeypatch.setenv("PERSONAL_FIRM_RECOVERY_ENABLED", "true")
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True, SECRET_KEY="recovery-test-secret")
    module.ensure_user_tables()
    module.ensure_role_tables()
    module.ensure_user_permission_override_tables()
    module.init_audit_table()
    module.ensure_personal_firm_recovery_table()
    module.create_app_user({
        "user_id": "USER-RECOVERY-1",
        "username": USERNAME,
        "password_hash": generate_password_hash(OLD_PASSWORD),
        "role_name": "Admin",
        "status": "active",
        "firm_id": FIRM_ID,
        "owner_id": "OWNER-RECOVERY-1",
    })
    credential = importlib.import_module("database.db").provision_personal_firm_recovery_credential(
        "USER-RECOVERY-1", FIRM_ID
    )
    return module, db_path, credential


def _post_with_csrf(client, path, data):
    page = client.get(path)
    return client.post(path, data={**data, "_csrf_token": _token(page)})


def test_recovery_table_is_additive_and_raw_secret_is_not_stored(recovery_app):
    module, db_path, credential = recovery_app
    module.ensure_personal_firm_recovery_table()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        user_count = connection.execute("SELECT COUNT(*) FROM app_users").fetchone()[0]
        row = connection.execute("SELECT * FROM personal_firm_recovery_credentials").fetchone()
    finally:
        connection.close()
    assert user_count == 1
    assert row["recovery_id"] == credential["recovery_id"]
    assert credential["recovery_secret"] not in row["recovery_secret_hash"]


def test_recovery_secret_verification_and_generic_failure(recovery_app):
    module, _, credential = recovery_app
    assert module.verify_personal_firm_recovery_credential(
        credential["recovery_id"], credential["recovery_secret"]
    )
    assert module.verify_personal_firm_recovery_credential(
        credential["recovery_id"], "incorrect"
    ) is None
    client = module.app.test_client()
    response = _post_with_csrf(client, "/account-recovery/forgot-username", {
        "recovery_id": credential["recovery_id"], "recovery_secret": "incorrect"
    })
    body = response.get_data(as_text=True)
    assert module.RECOVERY_FAILURE_MESSAGE in body
    assert USERNAME not in body


def test_recovery_locks_after_five_failures_and_success_clears_bucket(recovery_app):
    module, _, credential = recovery_app
    client = module.app.test_client()
    path = "/account-recovery/forgot-username"
    for _ in range(5):
        _post_with_csrf(client, path, {
            "recovery_id": credential["recovery_id"], "recovery_secret": "incorrect"
        })
    bucket = module._recovery_attempt_bucket("forgot_username", credential["recovery_id"])
    assert module._recovery_bucket_locked(bucket)
    locked = _post_with_csrf(client, path, {
        "recovery_id": credential["recovery_id"],
        "recovery_secret": credential["recovery_secret"],
    })
    assert USERNAME not in locked.get_data(as_text=True)
    module.recovery_attempts[bucket]["locked_until"] = time.time() - 1
    successful = _post_with_csrf(client, path, {
        "recovery_id": credential["recovery_id"],
        "recovery_secret": credential["recovery_secret"],
    })
    assert USERNAME in successful.get_data(as_text=True)
    assert bucket not in module.recovery_attempts


def test_reset_changes_password_and_rotates_recovery_secret(recovery_app):
    module, db_path, credential = recovery_app
    client = module.app.test_client()
    response = _post_with_csrf(client, "/account-recovery/reset-password", {
        "username": USERNAME,
        "recovery_id": credential["recovery_id"],
        "recovery_secret": credential["recovery_secret"],
        "new_password": NEW_PASSWORD,
        "confirm_password": NEW_PASSWORD,
    })
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Record this new recovery credential privately now" in body
    new_id = re.search(r"Recovery identifier: <strong>([^<]+)", body).group(1)
    new_secret = re.search(r"Recovery secret: <strong>([^<]+)", body).group(1)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        user = connection.execute("SELECT * FROM app_users WHERE username = ?", (USERNAME,)).fetchone()
    finally:
        connection.close()
    assert not check_password_hash(user["password_hash"], OLD_PASSWORD)
    assert check_password_hash(user["password_hash"], NEW_PASSWORD)
    assert module.verify_personal_firm_recovery_credential(
        credential["recovery_id"], credential["recovery_secret"]
    ) is None
    assert module.verify_personal_firm_recovery_credential(new_id, new_secret)

    old_login_page = client.get("/login")
    old_login = client.post("/login", data={
        "_csrf_token": _token(old_login_page), "username": USERNAME, "password": OLD_PASSWORD
    })
    assert old_login.status_code == 200
    assert "Invalid credentials" in old_login.get_data(as_text=True)
    new_login_page = client.get("/login")
    new_login = client.post("/login", data={
        "_csrf_token": _token(new_login_page), "username": USERNAME, "password": NEW_PASSWORD
    })
    assert new_login.status_code == 302


def test_login_link_gate_and_disabled_routes(recovery_app):
    module, _, _ = recovery_app
    client = module.app.test_client()
    assert "Can’t access your account?" in client.get("/login").get_data(as_text=True)
    module.app.config["PERSONAL_FIRM_RECOVERY_ENABLED"] = False
    assert "Can’t access your account?" not in client.get("/login").get_data(as_text=True)
    for path in (
        "/account-recovery",
        "/account-recovery/forgot-username",
        "/account-recovery/reset-password",
    ):
        assert client.get(path).status_code == 404


def test_recovery_posts_require_csrf(recovery_app):
    module, _, credential = recovery_app
    client = module.app.test_client()
    for path, data in (
        ("/account-recovery/forgot-username", {
            "recovery_id": credential["recovery_id"], "recovery_secret": credential["recovery_secret"]
        }),
        ("/account-recovery/reset-password", {
            "username": USERNAME, "recovery_id": credential["recovery_id"],
            "recovery_secret": credential["recovery_secret"], "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        }),
    ):
        assert client.post(path, data=data).status_code == 400


def _admin_session(client, username, firm_id):
    with client.session_transaction() as session:
        session["username"] = username
        session["role"] = "Admin"
        session["firm_id"] = firm_id
        session["last_activity"] = time.time()


def test_admin_reset_is_firm_bounded(recovery_app):
    module, db_path, _ = recovery_app
    other_hash = generate_password_hash("Other-Old!1")
    same_hash = generate_password_hash("Same-Old!1")
    module.create_app_user({
        "user_id": "USER-OTHER", "username": "other_user", "password_hash": other_hash,
        "role_name": "Viewer", "status": "active", "firm_id": "PF-OTHER", "owner_id": None,
    })
    module.create_app_user({
        "user_id": "USER-SAME", "username": "same_user", "password_hash": same_hash,
        "role_name": "Viewer", "status": "active", "firm_id": FIRM_ID, "owner_id": None,
    })
    client = module.app.test_client()
    _admin_session(client, USERNAME, FIRM_ID)
    assert client.get("/users/other_user/reset_password").status_code == 404
    page = client.get("/users/same_user/reset_password")
    response = client.post("/users/same_user/reset_password", data={
        "_csrf_token": _token(page), "password": "Same-New!2", "confirm_password": "Same-New!2"
    })
    assert response.status_code == 302
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        other = connection.execute("SELECT password_hash FROM app_users WHERE username='other_user'").fetchone()
        same = connection.execute("SELECT password_hash FROM app_users WHERE username='same_user'").fetchone()
    finally:
        connection.close()
    assert other["password_hash"] == other_hash
    assert check_password_hash(same["password_hash"], "Same-New!2")



def test_recovery_forms_do_not_request_saved_login_credentials(recovery_app):
    module, _, _ = recovery_app
    client = module.app.test_client()

    forgot = client.get(
        "/account-recovery/forgot-username"
    ).get_data(as_text=True)
    reset = client.get(
        "/account-recovery/reset-password"
    ).get_data(as_text=True)

    assert '<form method="POST" autocomplete="off">' in forgot
    assert '<form method="POST" autocomplete="off">' in reset

    assert (
        'name="recovery_id" type="text" '
        'autocomplete="one-time-code"'
    ) in forgot
    assert (
        'name="recovery_secret" type="password" '
        'autocomplete="one-time-code"'
    ) in forgot

    assert (
        'name="recovery_id" type="text" '
        'autocomplete="one-time-code"'
    ) in reset
    assert (
        'name="recovery_secret" type="password" '
        'autocomplete="one-time-code"'
    ) in reset

    assert "Do not enter your normal login password here." in forgot
    assert "Your normal login password does not belong" in reset



def test_recovery_scope_uses_no_external_identity_channel(recovery_app):
    module, _, _ = recovery_app
    routes = {rule.rule for rule in module.app.url_map.iter_rules() if "account-recovery" in rule.rule}
    assert routes == {
        "/account-recovery",
        "/account-recovery/forgot-username",
        "/account-recovery/reset-password",
    }
    source = " ".join(routes).lower()
    assert all(term not in source for term in ("email", "sms", "security-question"))
