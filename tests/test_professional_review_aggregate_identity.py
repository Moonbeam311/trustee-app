import sqlite3

import pytest

import database.db as db
from services.services_intake import build_draft_packet_open_issue_records


INTAKE_ID = "INT-AGGREGATE-1"
FIRM_ID = "FIRM-TEST"
WORKFLOW_KEY = "estate_plan"
SOURCE = "draft_packet_open_issue"
IDENTITY_KEY = "open_followup_tasks_remaining"


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    path = tmp_path / "professional-review-aggregate.sqlite3"
    monkeypatch.setattr(db, "get_connection", lambda: sqlite3.connect(path))
    db.ensure_professional_review_issue_tables()
    return path


def _aggregate_record(count):
    title = f"{count} open follow-up task(s) remain before final drafting."
    return {
        "issue_title": title,
        "issue_description": title,
        "issue_identity_key": IDENTITY_KEY,
    }


def _seed(packet):
    return db.seed_professional_review_issues_from_packet(
        INTAKE_ID, FIRM_ID, WORKFLOW_KEY, packet, actor="sync-actor"
    )


def _rows(path, table="professional_review_issues"):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY id")]


def test_builder_marks_aggregate_with_stable_semantic_identity_and_visible_count():
    records = build_draft_packet_open_issue_records(
        WORKFLOW_KEY,
        {"launch": {"open_tasks": [{"id": index} for index in range(24)]}},
    )

    aggregate = records[0]
    assert aggregate["issue_identity_key"] == IDENTITY_KEY
    assert aggregate["issue_title"] == "24 open follow-up task(s) remain before final drafting."
    assert aggregate["issue_description"] == aggregate["issue_title"]


def test_legacy_aggregate_refreshes_in_place_and_preserves_governed_fields(isolated_db):
    _seed({"open_issues": ["A separate stable issue"]})
    before_other = _rows(isolated_db)[0]
    with sqlite3.connect(isolated_db) as connection:
        connection.execute(
            """
            INSERT INTO professional_review_issues (
                issue_id, intake_id, firm_id, workflow_key, issue_source,
                issue_category, severity, issue_title, issue_description,
                linked_record_type, linked_record_id, recommended_action,
                status, disposition, reviewer_notes, resolved_by,
                resolved_capacity, resolved_at, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "PRI-FEA57BEA0A", INTAKE_ID, FIRM_ID, WORKFLOW_KEY, SOURCE,
                "Legacy category", "critical",
                "26 open follow-up task(s) remain before final drafting.",
                "26 open follow-up task(s) remain before final drafting.",
                "legacy_record", "LEGACY-7", "Preserve this action",
                "escalated", "accepted_risk", "Human review notes",
                "reviewer-1", "Attorney", "2025-01-02 03:04:05",
                "creator-1", "2025-01-01 01:02:03", "2025-01-03 04:05:06",
            ),
        )
    legacy_before = next(
        row for row in _rows(isolated_db) if row["issue_id"] == "PRI-FEA57BEA0A"
    )

    result = _seed({"open_issue_records": [
        _aggregate_record(24),
        {"issue_title": "A separate stable issue"},
    ]})
    rows = _rows(isolated_db)
    aggregate = next(row for row in rows if row["issue_id"] == "PRI-FEA57BEA0A")
    after_other = next(row for row in rows if row["issue_id"] == before_other["issue_id"])

    assert result["semantic_updated"] == 1
    assert len(rows) == 2
    assert sum("open follow-up task(s)" in row["issue_title"] for row in rows) == 1
    assert aggregate["issue_title"] == "24 open follow-up task(s) remain before final drafting."
    assert aggregate["issue_description"] == aggregate["issue_title"]
    assert aggregate["issue_id"] == "PRI-FEA57BEA0A"
    immutable_fields = set(aggregate) - {"issue_title", "issue_description", "updated_at"}
    assert {key: aggregate[key] for key in immutable_fields} == {
        key: legacy_before[key] for key in immutable_fields
    }
    assert {
        key: aggregate[key]
        for key in (
            "status", "disposition", "reviewer_notes", "resolved_by",
            "resolved_capacity", "resolved_at", "created_by", "created_at",
            "linked_record_type", "linked_record_id", "issue_source",
            "issue_category", "severity", "recommended_action",
        )
    } == {
        "status": "escalated", "disposition": "accepted_risk",
        "reviewer_notes": "Human review notes", "resolved_by": "reviewer-1",
        "resolved_capacity": "Attorney", "resolved_at": "2025-01-02 03:04:05",
        "created_by": "creator-1", "created_at": "2025-01-01 01:02:03",
        "linked_record_type": "legacy_record", "linked_record_id": "LEGACY-7",
        "issue_source": SOURCE, "issue_category": "Legacy category",
        "severity": "critical", "recommended_action": "Preserve this action",
    }
    assert after_other == before_other
    assert _rows(isolated_db, "professional_review_issue_events") == []

    unchanged = dict(aggregate)
    repeated = _seed({"open_issue_records": [
        _aggregate_record(24),
        {"issue_title": "A separate stable issue"},
    ]})
    assert repeated["semantic_updated"] == 0
    assert next(row for row in _rows(isolated_db) if row["issue_id"] == "PRI-FEA57BEA0A") == unchanged


def test_fresh_aggregate_identity_is_stable_across_count_changes(isolated_db):
    first = _seed({"open_issue_records": [_aggregate_record(26)]})
    original = _rows(isolated_db)[0]
    second = _seed({"open_issue_records": [_aggregate_record(24)]})
    current = _rows(isolated_db)

    assert first["created"] == 1
    assert second["semantic_updated"] == 1
    assert len(current) == 1
    assert current[0]["issue_id"] == original["issue_id"]
    assert current[0]["issue_title"].startswith("24 ")


def test_legacy_string_form_uses_stable_aggregate_identity(isolated_db):
    _seed({"open_issues": ["26 open follow-up task(s) remain before final drafting."]})
    original_id = _rows(isolated_db)[0]["issue_id"]
    result = _seed({"open_issues": ["24 open follow-up task(s) remain before final drafting."]})

    assert result["semantic_updated"] == 1
    assert [row["issue_id"] for row in _rows(isolated_db)] == [original_id]


def test_multiple_semantic_candidates_fail_closed_without_mutation(isolated_db):
    with sqlite3.connect(isolated_db) as connection:
        for issue_id, count in (("PRI-LEGACY-A", 26), ("PRI-LEGACY-B", 25)):
            title = f"{count} open follow-up task(s) remain before final drafting."
            connection.execute(
                """
                INSERT INTO professional_review_issues (
                    issue_id, intake_id, firm_id, workflow_key, issue_source,
                    issue_title, issue_description, status, reviewer_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (issue_id, INTAKE_ID, FIRM_ID, WORKFLOW_KEY, SOURCE,
                 title, title, "escalated", f"notes-{count}"),
            )
    before = _rows(isolated_db)

    with pytest.raises(ValueError, match="Multiple Professional Review aggregate issue candidates"):
        _seed({"open_issue_records": [_aggregate_record(24)]})

    assert _rows(isolated_db) == before


def test_nonaggregate_title_identity_and_provenance_semantics_are_unchanged(isolated_db):
    first_title = "Review flag: Stable title"
    second_title = "Review flag: Changed title"
    first = _seed({"open_issue_records": [{"issue_title": first_title}]})
    original_id = _rows(isolated_db)[0]["issue_id"]
    enriched = _seed({"open_issue_records": [{
        "issue_title": first_title,
        "linked_record_type": "intake_followup_task",
        "linked_record_id": "TASK-1",
    }]})
    conflicting = _seed({"open_issue_records": [{
        "issue_title": first_title,
        "linked_record_type": "other_type",
        "linked_record_id": "OTHER-2",
    }]})
    changed_title = _seed({"open_issue_records": [{"issue_title": second_title}]})
    rows = _rows(isolated_db)
    original = next(row for row in rows if row["issue_id"] == original_id)

    assert first["created"] == 1
    assert enriched["provenance_enriched"] == 1
    assert conflicting["provenance_enriched"] == 0
    assert changed_title["created"] == 1
    assert len(rows) == 2
    assert (original["linked_record_type"], original["linked_record_id"]) == (
        "intake_followup_task", "TASK-1"
    )
