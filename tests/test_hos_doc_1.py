from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database.migrations_generated_document_attribution import (
    ADDITIVE_COLUMNS,
    apply_generated_document_attribution_schema,
)
import services.services_document_contract as contract


LEGACY_DDL = """
CREATE TABLE generated_documents (
    document_id TEXT PRIMARY KEY,
    workspace_id TEXT,
    trust_id TEXT,
    template_id TEXT,
    title TEXT,
    content TEXT,
    status TEXT,
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    owner_id TEXT
)
"""


def _create_legacy_db(path):
    connection = sqlite3.connect(path)
    connection.execute(LEGACY_DDL)
    connection.execute(
        """
        INSERT INTO generated_documents (
            document_id,
            workspace_id,
            trust_id,
            template_id,
            title,
            content,
            status,
            created_by,
            owner_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "DOC-LEGACY-1",
            "WS-1",
            None,
            "TPL-1",
            "Legacy",
            "Body",
            "final",
            "legacy-user",
            "legacy-owner",
        ),
    )
    connection.commit()
    connection.close()


def test_migration_is_additive_idempotent_and_preserves_legacy_row(tmp_path):
    db = tmp_path / "legacy.db"
    _create_legacy_db(db)

    before = sqlite3.connect(db)
    original = before.execute(
        """
        SELECT document_id, workspace_id, trust_id, template_id,
               title, content, status, created_by, owner_id
        FROM generated_documents
        """
    ).fetchone()
    before.close()

    first = apply_generated_document_attribution_schema(db)
    second = apply_generated_document_attribution_schema(db)

    assert first["schema_complete"] is True
    assert first["columns_added"] == 4
    assert first["legacy_rows_preserved"] == 1
    assert first["legacy_rows_updated"] == 0
    assert first["records_created"] == 0

    assert second["schema_complete"] is True
    assert second["columns_added"] == 0

    connection = sqlite3.connect(db)

    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(generated_documents)"
        )
    }

    assert set(ADDITIVE_COLUMNS) == {
        "firm_id",
        "source_record_type",
        "source_record_id",
        "generation_basis",
    }
    assert set(ADDITIVE_COLUMNS).issubset(columns)

    preserved = connection.execute(
        """
        SELECT document_id, workspace_id, trust_id, template_id,
               title, content, status, created_by, owner_id
        FROM generated_documents
        """
    ).fetchone()

    attribution = connection.execute(
        """
        SELECT firm_id, source_record_type,
               source_record_id, generation_basis
        FROM generated_documents
        WHERE document_id = 'DOC-LEGACY-1'
        """
    ).fetchone()

    connection.close()

    assert preserved == original
    assert attribution == (None, None, None, None)


def test_migration_defers_when_legacy_table_is_absent(tmp_path):
    db = tmp_path / "fresh.db"

    result = apply_generated_document_attribution_schema(db)

    assert result["schema_complete"] is False
    assert result["deferred"] is True
    assert result["columns_added"] == 0
    assert result["records_created"] == 0

    connection = sqlite3.connect(db)

    exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'generated_documents'
        """
    ).fetchone()

    connection.close()

    assert exists is None


def test_unsourced_attribution_does_not_invent_governed_source(monkeypatch):
    monkeypatch.setattr(
        contract.document_db,
        "get_current_firm_id",
        lambda: "FIRM-1",
    )

    result = contract._build_persistent_generated_document_attribution(
        "",
        authorization_check=None,
        generated_by="operator-1",
    )

    assert result == {
        "firm_id": "FIRM-1",
        "source_record_type": None,
        "source_record_id": None,
        "generation_basis": "SOURCE_ATTRIBUTION_NOT_ESTABLISHED",
        "generated_by": "operator-1",
    }


def test_authorized_trust_resolves_canonical_attribution(monkeypatch):
    monkeypatch.setattr(
        contract.document_db,
        "get_current_firm_id",
        lambda: "FIRM-1",
    )

    monkeypatch.setattr(
        contract,
        "produce_trust_document_context",
        lambda *args, **kwargs: {
            "source": {
                "object_type": "trust",
                "object_id": "TR-001",
                "firm_id": "FIRM-1",
                "authoritative_record": True,
            }
        },
    )

    result = contract._build_persistent_generated_document_attribution(
        "TR-001",
        authorization_check=lambda trust_id: trust_id == "TR-001",
        generated_by="operator-1",
    )

    assert result == {
        "firm_id": "FIRM-1",
        "source_record_type": "trust",
        "source_record_id": "TR-001",
        "generation_basis": "CANONICAL_TRUST_CONTEXT",
        "generated_by": "operator-1",
    }


def test_trust_attribution_requires_explicit_authorization(monkeypatch):
    monkeypatch.setattr(
        contract.document_db,
        "get_current_firm_id",
        lambda: "FIRM-1",
    )

    with pytest.raises(
        contract.DocumentContractError,
        match="authorization check",
    ):
        contract._build_persistent_generated_document_attribution(
            "TR-001",
            authorization_check=None,
            generated_by="operator-1",
        )


def test_cross_firm_trust_fails_closed(monkeypatch):
    monkeypatch.setattr(
        contract.document_db,
        "get_current_firm_id",
        lambda: "FIRM-1",
    )

    monkeypatch.setattr(
        contract,
        "produce_trust_document_context",
        lambda *args, **kwargs: {
            "source": {
                "object_type": "trust",
                "object_id": "TR-002",
                "firm_id": "FIRM-OTHER",
                "authoritative_record": True,
            }
        },
    )

    with pytest.raises(
        contract.DocumentContractError,
        match="unavailable or not authorized",
    ):
        contract._build_persistent_generated_document_attribution(
            "TR-002",
            authorization_check=lambda trust_id: True,
            generated_by="operator-1",
        )


def _create_attributed_generated_documents_table(path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE generated_documents (
            document_id TEXT PRIMARY KEY,
            workspace_id TEXT,
            trust_id TEXT,
            template_id TEXT,
            title TEXT,
            content TEXT,
            status TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            owner_id TEXT,
            firm_id TEXT,
            source_record_type TEXT,
            source_record_id TEXT,
            generation_basis TEXT
        );
        """
    )
    connection.commit()
    connection.close()


def _load_document_lane_from_app(
    monkeypatch,
    db_path,
    *,
    owner_id="OWNER-A",
    firm_id="FIRM-A",
    username="server-user",
):
    """Load only generated-document helpers; do not import Flask app."""
    import ast
    import database.db as database_db

    wanted = {
        "_current_generated_document_scope",
        "get_generated_documents",
        "get_generated_documents_by_workspace",
        "get_generated_document_by_id",
        "create_generated_document",
    }

    source = Path("app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in wanted
    ]

    names = {node.name for node in nodes}
    assert names == wanted

    module = ast.Module(body=nodes, type_ignores=[])
    ast.fix_missing_locations(module)

    def learning_conn():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    namespace = {
        "_learning_conn": learning_conn,
        "get_current_owner": lambda: owner_id,
        "session": {"username": username},
        "deny_unassigned_trust_access": lambda trust_id: None,
    }

    monkeypatch.setattr(
        database_db,
        "get_current_firm_id",
        lambda: firm_id,
    )

    exec(
        compile(module, "app.py::generated_document_lane", "exec"),
        namespace,
    )

    return namespace


def test_new_write_uses_server_derived_scope_and_actor(
    tmp_path,
    monkeypatch,
):
    db = tmp_path / "generated-write.db"
    _create_attributed_generated_documents_table(db)

    lane = _load_document_lane_from_app(
        monkeypatch,
        db,
        owner_id="SERVER-OWNER",
        firm_id="SERVER-FIRM",
        username="SERVER-ACTOR",
    )

    monkeypatch.setattr(
        contract,
        "_build_persistent_generated_document_attribution",
        lambda trust_id, **kwargs: {
            "firm_id": "SERVER-FIRM",
            "source_record_type": None,
            "source_record_id": None,
            "generation_basis":
                "SOURCE_ATTRIBUTION_NOT_ESTABLISHED",
            "generated_by": "SERVER-ACTOR",
        },
    )

    lane["create_generated_document"](
        {
            "document_id": "DOC-NEW-1",
            "workspace_id": "WS-1",
            "trust_id": "",
            "template_id": "TPL-1",
            "title": "Generated",
            "content": "Body",
            "status": "final",

            # Deliberately hostile/client-controlled values.
            # The persistence lane must ignore them.
            "owner_id": "CLIENT-OWNER",
            "firm_id": "CLIENT-FIRM",
            "created_by": "CLIENT-ACTOR",
        }
    )

    connection = sqlite3.connect(db)

    row = connection.execute(
        """
        SELECT owner_id,
               firm_id,
               created_by,
               trust_id,
               source_record_type,
               source_record_id,
               generation_basis,
               status
        FROM generated_documents
        WHERE document_id = 'DOC-NEW-1'
        """
    ).fetchone()

    connection.close()

    assert row == (
        "SERVER-OWNER",
        "SERVER-FIRM",
        "SERVER-ACTOR",
        None,
        None,
        None,
        "SOURCE_ATTRIBUTION_NOT_ESTABLISHED",
        "final",
    )


def test_reads_require_matching_owner_and_firm_and_hide_legacy_null(
    tmp_path,
    monkeypatch,
):
    db = tmp_path / "generated-read.db"
    _create_attributed_generated_documents_table(db)

    connection = sqlite3.connect(db)

    rows = [
        (
            "DOC-GOOD",
            "WS-1",
            "OWNER-A",
            "FIRM-A",
        ),
        (
            "DOC-WRONG-OWNER",
            "WS-1",
            "OWNER-B",
            "FIRM-A",
        ),
        (
            "DOC-WRONG-FIRM",
            "WS-1",
            "OWNER-A",
            "FIRM-B",
        ),
        (
            "DOC-LEGACY-NULL-FIRM",
            "WS-1",
            "OWNER-A",
            None,
        ),
    ]

    for document_id, workspace_id, owner_id, firm_id in rows:
        connection.execute(
            """
            INSERT INTO generated_documents (
                document_id,
                workspace_id,
                title,
                content,
                status,
                created_by,
                owner_id,
                firm_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                workspace_id,
                document_id,
                "Body",
                "draft",
                "actor",
                owner_id,
                firm_id,
            ),
        )

    connection.commit()
    connection.close()

    lane = _load_document_lane_from_app(
        monkeypatch,
        db,
        owner_id="OWNER-A",
        firm_id="FIRM-A",
    )

    listed = lane["get_generated_documents"]()
    workspace = lane[
        "get_generated_documents_by_workspace"
    ]("WS-1")

    assert {row["document_id"] for row in listed} == {
        "DOC-GOOD"
    }

    assert {row["document_id"] for row in workspace} == {
        "DOC-GOOD"
    }

    assert (
        lane["get_generated_document_by_id"]("DOC-GOOD")
        is not None
    )

    for denied in (
        "DOC-WRONG-OWNER",
        "DOC-WRONG-FIRM",
        "DOC-LEGACY-NULL-FIRM",
    ):
        assert (
            lane["get_generated_document_by_id"](denied)
            is None
        )


def test_missing_server_scope_fails_closed(
    tmp_path,
    monkeypatch,
):
    db = tmp_path / "generated-missing-scope.db"
    _create_attributed_generated_documents_table(db)

    no_owner = _load_document_lane_from_app(
        monkeypatch,
        db,
        owner_id="",
        firm_id="FIRM-A",
    )

    assert no_owner["get_generated_documents"]() == []
    assert (
        no_owner["get_generated_document_by_id"]("ANY")
        is None
    )

    no_firm = _load_document_lane_from_app(
        monkeypatch,
        db,
        owner_id="OWNER-A",
        firm_id="",
    )

    assert no_firm["get_generated_documents"]() == []
    assert (
        no_firm["get_generated_document_by_id"]("ANY")
        is None
    )

def test_generated_document_scope_prefers_authenticated_session_firm(
    monkeypatch,
):
    import ast
    import database.db as database_db
    from flask import Flask
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "_current_generated_document_scope"
    )

    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {
        "get_current_owner": lambda: "OWNER-A",
    }

    exec(
        compile(module, "app.py", "exec"),
        namespace,
    )

    monkeypatch.setattr(
        database_db,
        "get_current_firm_id",
        lambda: "FIRM-002",
    )

    flask_app = Flask("hos-doc-firm-scope-test")
    flask_app.secret_key = "hos-doc-test-only"

    with flask_app.test_request_context("/"):
        from flask import session

        session["firm_id"] = "FIRM-001"

        assert namespace[
            "_current_generated_document_scope"
        ]() == (
            "OWNER-A",
            "FIRM-001",
        )

    with flask_app.test_request_context("/"):
        assert namespace[
            "_current_generated_document_scope"
        ]() == (
            "OWNER-A",
            "FIRM-002",
        )


def test_persistent_attribution_explicit_firm_overrides_hosted_fallback(
    monkeypatch,
):
    import services.services_document_contract as contract

    monkeypatch.setattr(
        contract.document_db,
        "get_current_firm_id",
        lambda: "FIRM-002",
    )

    attribution = (
        contract._build_persistent_generated_document_attribution(
            "",
            authorization_check=None,
            generated_by="admin",
            firm_id="FIRM-001",
        )
    )

    assert attribution == {
        "firm_id": "FIRM-001",
        "source_record_type": None,
        "source_record_id": None,
        "generation_basis":
            "SOURCE_ATTRIBUTION_NOT_ESTABLISHED",
        "generated_by": "admin",
    }
