import importlib
import sqlite3
import sys


def _load_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "visualization-row-access.db"))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True, SECRET_KEY="visualization-row-access-test")
    return module


def _row(sql, params=()):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row


def test_visualization_summary_handles_mixed_provider_row_contracts(monkeypatch, tmp_path):
    module = _load_app(monkeypatch, tmp_path)

    trust = _row(
        "SELECT 'TR-VIZ-001' AS trust_id, "
        "'Visualization Test Trust' AS trust_name, "
        "'Revocable Living Trust' AS trust_type"
    )
    matching = _row("SELECT ? AS trust_id", ("TR-VIZ-001",))
    other = _row("SELECT ? AS trust_id", ("TR-OTHER",))

    monkeypatch.setattr(module, "get_all_trusts", lambda: [trust])
    monkeypatch.setattr(module, "get_all_fiduciaries", lambda: [matching, other])
    monkeypatch.setattr(module, "get_all_instruments", lambda: [matching, other])
    monkeypatch.setattr(
        module,
        "get_generated_documents",
        lambda: [{"trust_id": "TR-VIZ-001"}, {"trust_id": "TR-OTHER"}],
    )
    monkeypatch.setattr(
        module,
        "get_all_execution_tasks",
        lambda: [{"trust_id": "TR-VIZ-001"}, {"trust_id": "TR-OTHER"}],
    )
    monkeypatch.setattr(
        module,
        "get_all_workspaces",
        lambda: [
            {"trust_type_focus": "living trust"},
            {"trust_type_focus": "charitable trust"},
        ],
    )

    assert module.get_trust_relationship_summary() == [
        {
            "trust_id": "TR-VIZ-001",
            "trust_name": "Visualization Test Trust",
            "fiduciaries": 1,
            "instruments": 1,
            "documents": 1,
            "workspace_links": 1,
            "tasks": 1,
        }
    ]


def test_visualization_summary_preserves_dict_provider_compatibility(monkeypatch, tmp_path):
    module = _load_app(monkeypatch, tmp_path)

    monkeypatch.setattr(
        module,
        "get_all_trusts",
        lambda: [
            {
                "trust_id": "TR-DICT-001",
                "trust_name": "Dict Provider Trust",
                "trust_type": "Irrevocable Trust",
            }
        ],
    )
    monkeypatch.setattr(
        module,
        "get_all_fiduciaries",
        lambda: [{"trust_id": "TR-DICT-001"}, {"trust_id": "TR-OTHER"}],
    )
    monkeypatch.setattr(
        module,
        "get_all_instruments",
        lambda: [{"trust_id": "TR-DICT-001"}],
    )
    monkeypatch.setattr(module, "get_generated_documents", lambda: [])
    monkeypatch.setattr(module, "get_all_execution_tasks", lambda: [])
    monkeypatch.setattr(
        module,
        "get_all_workspaces",
        lambda: [{"trust_type_focus": "irrevocable"}],
    )

    assert module.get_trust_relationship_summary() == [
        {
            "trust_id": "TR-DICT-001",
            "trust_name": "Dict Provider Trust",
            "fiduciaries": 1,
            "instruments": 1,
            "documents": 0,
            "workspace_links": 1,
            "tasks": 0,
        }
    ]
