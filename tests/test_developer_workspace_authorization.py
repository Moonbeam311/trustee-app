import importlib
import sys
import time

import pytest


@pytest.fixture
def isolated_app(monkeypatch, tmp_path):
    db_path = tmp_path / "developer-workspace-authorization.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    module.app.config.update(
        TESTING=True,
        SECRET_KEY="developer-workspace-authorization-isolated",
    )
    return module.app


def _authenticate(client, *, username, role="Admin", firm_id="FIRM-001"):
    with client.session_transaction() as session:
        session.update(
            username=username,
            user_id=f"USR-{username.upper()}",
            firm_id=firm_id,
            role=role,
            last_activity=time.time(),
        )


def test_developer_workspace_denies_authenticated_non_master(isolated_app):
    client = isolated_app.test_client()
    _authenticate(client, username="workspace-operator")

    response = client.get("/admin/workspace/developer")

    assert response.status_code == 403
    assert b"Only the master admin may access this page." in response.data


def test_developer_workspace_allows_master_admin(isolated_app):
    client = isolated_app.test_client()
    _authenticate(client, username="admin")

    response = client.get("/admin/workspace/developer")

    assert response.status_code == 200


def test_ordinary_workspace_does_not_require_master_admin(isolated_app):
    client = isolated_app.test_client()
    _authenticate(client, username="workspace-operator")

    response = client.get("/admin/workspace/home")

    assert response.status_code == 200
