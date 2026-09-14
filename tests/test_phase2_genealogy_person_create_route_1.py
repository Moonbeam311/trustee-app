import re
import sqlite3
import time
from pathlib import Path

import app as app_module
from database import db as database_db
from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def _authenticated_client(monkeypatch, role="Admin"):
    app_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    monkeypatch.setattr(
        app_module,
        "get_export_policy",
        lambda: {
            "allow_exports": True,
            "read_only_mode": False,
        },
    )

    client = app_module.app.test_client()

    with client.session_transaction() as session:
        session["username"] = "p5n-route-admin"
        session["role"] = role
        session["firm_id"] = "FIRM-P5N"
        session["last_activity"] = time.time()

    return client


def test_person_create_route_is_admin_trustee_scoped():
    source = _read("app.py")

    assert (
        '"genealogy_person_new": {"Admin", "Trustee"}'
        in source
    )

    assert (
        '@app.route(\n'
        '    "/genealogy/legacy-workspace/person/new",\n'
        '    methods=["GET", "POST"],\n'
        ')'
        in source
    )


def test_person_create_route_is_not_bridge_draft_trust_form():
    source = _read("app.py")

    start = source.index(
        "BRIDGE_DRAFT_FORM_TRUST_ENDPOINTS = {"
    )
    end = source.index(
        "BRIDGE_DRAFT_BRIDGE_ENDPOINTS = {",
        start,
    )

    bridge_form_block = source[start:end]

    assert '"genealogy_new"' in bridge_form_block
    assert '"genealogy_person_new"' not in bridge_form_block


def test_person_form_hides_infrastructure_scope_and_uses_wtf_csrf():
    template = _read("templates/genealogy_person_form.html")

    assert 'name="display_name"' in template
    assert 'name="sort_name"' in template
    assert 'name="notes"' in template

    assert 'name="person_id"' not in template
    assert 'name="owner_id"' not in template
    assert 'name="firm_id"' not in template
    assert 'name="trust_id"' not in template

    assert "wtf_csrf_token()" in template


def test_canonical_workspace_exposes_add_person():
    template = _read(
        "templates/genealogy_legacy_workspace.html"
    )

    assert "url_for('genealogy_person_new')" in template
    assert "Add Person" in template


def test_admin_can_get_canonical_person_form(monkeypatch):
    client = _authenticated_client(monkeypatch, role="Admin")

    response = client.get(
        "/genealogy/legacy-workspace/person/new"
    )

    assert response.status_code == 200
    assert b"Add Person" in response.data
    assert b"Person ID automatically" in response.data


def test_viewer_cannot_get_canonical_person_form(monkeypatch):
    client = _authenticated_client(monkeypatch, role="Viewer")

    response = client.get(
        "/genealogy/legacy-workspace/person/new"
    )

    assert response.status_code == 403


def test_admin_post_creates_scoped_system_id_person(monkeypatch):
    apply_person_identity_schema(database_db.DB_PATH)

    client = _authenticated_client(monkeypatch, role="Admin")

    response = client.post(
        "/genealogy/legacy-workspace/person/new",
        data={
            "display_name": "P5N Browser Test Person",
            "sort_name": "Test Person, P5N Browser",
            "notes": "Disposable route certification record.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/genealogy/legacy-workspace"
    )

    con = sqlite3.connect(str(database_db.DB_PATH))
    con.row_factory = sqlite3.Row

    try:
        row = con.execute(
            """
            SELECT *
            FROM persons
            WHERE owner_id = ?
              AND firm_id = ?
              AND display_name = ?
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """,
            (
                "p5n-route-admin",
                "FIRM-P5N",
                "P5N Browser Test Person",
            ),
        ).fetchone()
    finally:
        con.close()

    assert row is not None
    assert re.fullmatch(
        r"PER-[0-9A-F]{20}",
        row["person_id"],
    )
    assert row["created_by"] == "p5n-route-admin"


def test_missing_display_name_does_not_create_person(monkeypatch):
    apply_person_identity_schema(database_db.DB_PATH)

    client = _authenticated_client(monkeypatch, role="Admin")

    response = client.post(
        "/genealogy/legacy-workspace/person/new",
        data={
            "display_name": "",
            "sort_name": "",
            "notes": "",
        },
    )

    assert response.status_code == 400
    assert b"Person display name is required." in response.data
