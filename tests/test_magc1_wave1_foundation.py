import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from database.migrations_work_learning_magc1_wave1 import apply_magc1_wave1_schema
import services.services_work_learning_programs as p05
import services.services_work_learning_authority as p09
from services.services_work_learning_provenance import _wave1_source_context


@pytest.fixture()
def env(tmp_path):
    path = tmp_path / "magc1.db"

    def connection():
        item = sqlite3.connect(path)
        item.row_factory = sqlite3.Row
        return item

    with patch.object(p05, "get_connection", side_effect=connection):
        p05.ensure_work_learning_program_tables()
        program = p05.create_hub_program(
            workspace_id="W1", firm_id="F1", owner_id="O1", title="Program",
            purpose="test", created_by="tester",
        )
        source = p05.create_program_source_reference(
            program_id=program, firm_id="F1", owner_id="O1",
            source_type="external_reference", source_reference="citation",
            source_label="Source", source_notes=None, issue_id=None,
            created_by="tester",
        )
    apply_magc1_wave1_schema(path)

    def get_program(**kwargs):
        conn = connection()
        row = conn.execute(
            "SELECT * FROM hub_programs WHERE program_id=? AND firm_id=? AND owner_id=?",
            (kwargs["program_id"], kwargs["firm_id"], kwargs["owner_id"]),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    with patch.object(p05, "get_connection", side_effect=connection), \
         patch.object(p09, "get_connection", side_effect=connection), \
         patch.object(p09, "get_hub_program", side_effect=get_program):
        yield path, program, source


def test_p05_metadata_requires_source_and_is_append_only(env):
    path, program, source = env
    args = dict(program_id=program, firm_id="F1", owner_id="O1", actor="tester")
    with pytest.raises(ValueError, match="source_not_available"):
        p05.record_source_metadata(**args, source_reference_id="missing")
    first = p05.record_source_metadata(
        **args, source_reference_id=source, source_origin_jurisdiction="DE",
        effective_date="2025-01-02", current_as_of_date="2026-01-02",
        lifecycle_state="CURRENT",
    )
    with pytest.raises(ValueError, match="prior_metadata_required"):
        p05.record_source_metadata(**args, source_reference_id=source)
    second = p05.record_source_metadata(
        **args, source_reference_id=source, lifecycle_state="REVIEW_DUE",
        prior_metadata_id=first,
    )
    history = p05.get_source_metadata_history(
        program_id=program, firm_id="F1", owner_id="O1", source_reference_id=source,
    )
    assert [row["metadata_id"] for row in history] == [first, second]
    assert history[1]["prior_metadata_id"] == first
    with pytest.raises(ValueError, match="invalid_source_lifecycle_state"):
        p05.record_source_metadata(**args, source_reference_id=source,
                                   lifecycle_state="VALID")
    conn = sqlite3.connect(path)
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        conn.execute("UPDATE hub_program_source_metadata SET lifecycle_state='CURRENT'")
    conn.close()


def _app(source, **overrides):
    values = dict(
        firm_id="F1", context_type="PROGRAM", context_id="P-context",
        subject="May this source support the issue?", source_reference_id=source,
        legal_scope="ADMINISTRATION", applicability_basis="analysis",
        applicability_provenance="research log", decision_origin="SYSTEM_SUGGESTED",
        actor="machine", actor_capacity="research assistant",
    )
    values.update(overrides)
    return p09.record_source_applicability(**values)


def test_p09_generic_context_defaults_history_and_separate_jurisdictions(env):
    path, program, source = env
    metadata = p05.record_source_metadata(
        program_id=program, firm_id="F1", owner_id="O1", source_reference_id=source,
        source_origin_jurisdiction="DE", lifecycle_state="UNRESOLVED", actor="tester",
    )
    for context_type in p09.CONTEXT_TYPES:
        applicability = _app(source, context_type=context_type,
                             context_id=f"external-{context_type}")
        rows = p09.get_source_applicability_history(
            firm_id="F1", context_type=context_type,
            context_id=f"external-{context_type}",
            subject="May this source support the issue?", source_reference_id=source,
        )
        assert rows[0]["applicability_id"] == applicability
        assert (rows[0]["research_only"], rows[0]["generation_authorized"],
                rows[0]["independent_support_state"]) == (1, 0, "UNRESOLVED")
    first = _app(source, decision_origin="OPERATOR_OR_FIDUCIARY",
                 context_id="history", applicability_jurisdiction="NJ")
    second = _app(source, decision_origin="OPERATOR_OR_FIDUCIARY",
                  context_id="history", applicability_jurisdiction="NJ",
                  prior_applicability_id=first)
    assert second != first
    derived = _wave1_source_context(path, [source], "F1")
    assert any(row["metadata_id"] == metadata and
               row["source_origin_jurisdiction"] == "DE" for row in derived["source_metadata"])
    assert any(row["applicability_jurisdiction"] == "NJ" for row in derived["issue_applicability"])


def test_p09_safety_and_cross_firm_fail_closed(env):
    _, _, source = env
    with pytest.raises(ValueError, match="research_only_generation"):
        _app(source, generation_authorized=True)
    with pytest.raises(ValueError, match="machine_applicability_finalization"):
        _app(source, research_only=False, independent_support_state="YES",
             applicability_jurisdiction="NJ")
    with pytest.raises(ValueError, match="source_not_available"):
        _app(source, firm_id="F2")
    with pytest.raises(ValueError, match="generation_authorization_requirements"):
        _app(source, decision_origin="OPERATOR_OR_FIDUCIARY", research_only=False,
             generation_authorized=True, independent_support_state="UNRESOLVED")


def test_p08_optional_schema_reader_is_read_only_and_absence_safe(tmp_path, env):
    path, _, source = env
    before = path.read_bytes()
    _wave1_source_context(path, [source], "F1")
    assert path.read_bytes() == before
    old = tmp_path / "old.db"
    sqlite3.connect(old).close()
    assert _wave1_source_context(old, [source], "F1") == {
        "source_metadata": [], "authority_classifications": [],
        "authority_relationships": [], "issue_applicability": [],
        "authority_reviews": [], "authority_determinations": [],
    }


def test_migration_is_idempotent(env):
    path, _, _ = env
    assert apply_magc1_wave1_schema(path)["schema_complete"] is True
