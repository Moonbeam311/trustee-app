import importlib
import sys
import time

import pytest


@pytest.fixture
def isolated_app(monkeypatch, tmp_path):
    db_path = tmp_path / "governance-registry-handoff.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    module.app.config.update(
        TESTING=True,
        SECRET_KEY="governance-registry-handoff-isolated",
    )
    return module


def test_ordinary_operator_is_redirected_to_governance_registry(isolated_app):
    client = isolated_app.app.test_client()
    with client.session_transaction() as session:
        session.update(
            username="workspace-operator",
            user_id="USR-WORKSPACE-OPERATOR",
            firm_id="FIRM-001",
            role="Admin",
            last_activity=time.time(),
        )

    response = client.get("/admin/workspace/governance-registry")

    assert response.status_code == 302
    assert response.headers["Location"] == "/governance"
    assert response.headers["Location"] != "/admin/workspace/home"
    assert "governance-registry" not in isolated_app.IOS_WORKSPACE_META
