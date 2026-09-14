import sqlite3

import pytest

from database.migrations_genealogy_relationship_review_schema import (
    apply_genealogy_relationship_review_schema,
)
from database.migrations_genealogy_relationship_schema import (
    apply_genealogy_relationship_schema,
)
from services.services_genealogy_relationship_reviews import (
    GenealogyRelationshipReviewServiceError,
    list_genealogy_relationship_reviews,
    transition_genealogy_relationship_status,
)


def _ready_db(tmp_path):
    db_path = tmp_path / "genealogy-review-service.db"

    apply_genealogy_relationship_schema(db_path)
    apply_genealogy_relationship_review_schema(
        db_path
    )

    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            CREATE TABLE media_records (
                media_id TEXT PRIMARY KEY,
                trust_id TEXT,
                related_entity_type TEXT,
                related_entity_id TEXT,
                media_type TEXT,
                file_path TEXT,
                category TEXT,
                description TEXT,
                created_at TEXT,
                firm_id TEXT
            )
            """
        )
        con.commit()
    finally:
        con.close()

    return db_path


def _assertion(
    db_path,
    assertion_id="GRA-001",
    owner_id="OWNER-A",
    firm_id="FIRM-A",
    status="USER_ASSERTED",
):
    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            INSERT INTO genealogy_relationship_assertions (
                assertion_id,
                owner_id,
                firm_id,
                subject_person_id,
                relationship_type,
                related_person_id,
                assertion_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assertion_id,
                owner_id,
                firm_id,
                f"{assertion_id}-SUBJECT",
                "PARENT_OF",
                f"{assertion_id}-RELATED",
                status,
            ),
        )
        con.commit()
    finally:
        con.close()


def _transition(
    db_path,
    review_id,
    new_status,
    **overrides,
):
    payload = {
        "review_id": review_id,
        "assertion_id": "GRA-001",
        "owner_id": "OWNER-A",
        "firm_id": "FIRM-A",
        "new_status": new_status,
        "review_basis": "Human review",
        "provenance": "Reviewed genealogy record",
        "decision_origin": "OPERATOR_OR_FIDUCIARY",
        "human_confirmed": True,
        "actor": "operator-a",
        "actor_capacity": "Trustee",
    }

    payload.update(overrides)

    return transition_genealogy_relationship_status(
        db_path,
        payload,
    )


def _status(db_path):
    con = sqlite3.connect(db_path)

    try:
        return con.execute(
            """
            SELECT assertion_status
            FROM genealogy_relationship_assertions
            WHERE assertion_id='GRA-001'
            """
        ).fetchone()[0]
    finally:
        con.close()


def test_human_governed_review_required_transition_is_atomic(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    review = _transition(
        db_path,
        "GRR-001",
        "REVIEW_REQUIRED",
    )

    assert review["prior_status"] == "USER_ASSERTED"
    assert review["new_status"] == "REVIEW_REQUIRED"
    assert review["human_confirmed"] == 1
    assert review["prior_review_id"] is None
    assert _status(db_path) == "REVIEW_REQUIRED"

    rows = list_genealogy_relationship_reviews(
        db_path,
        "GRA-001",
        "OWNER-A",
        "FIRM-A",
    )

    assert [row["review_id"] for row in rows] == [
        "GRR-001",
    ]


def test_system_suggested_cannot_mutate_assertion_status(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    with pytest.raises(
        GenealogyRelationshipReviewServiceError,
        match="SYSTEM_SUGGESTED",
    ):
        _transition(
            db_path,
            "GRR-SYSTEM",
            "REVIEW_REQUIRED",
            decision_origin="SYSTEM_SUGGESTED",
        )

    assert _status(db_path) == "USER_ASSERTED"

    assert list_genealogy_relationship_reviews(
        db_path,
        "GRA-001",
        "OWNER-A",
        "FIRM-A",
    ) == []


def test_direct_user_asserted_to_confirmed_is_prohibited(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    with pytest.raises(
        GenealogyRelationshipReviewServiceError,
        match="Invalid governed genealogy status transition",
    ):
        _transition(
            db_path,
            "GRR-BAD",
            "CONFIRMED",
        )

    assert _status(db_path) == "USER_ASSERTED"


def test_confirmed_requires_linked_media_evidence_and_chains_review(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    first = _transition(
        db_path,
        "GRR-001",
        "REVIEW_REQUIRED",
    )

    assert first["prior_review_id"] is None

    with pytest.raises(
        GenealogyRelationshipReviewServiceError,
        match="linked Media Evidence",
    ):
        _transition(
            db_path,
            "GRR-002",
            "CONFIRMED",
        )

    assert _status(db_path) == "REVIEW_REQUIRED"

    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            INSERT INTO media_records (
                media_id,
                related_entity_type,
                related_entity_id,
                media_type,
                file_path,
                created_at,
                firm_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MED-001",
                "genealogy_relationship_assertion",
                "GRA-001",
                "document",
                "/tmp/source.pdf",
                "2026-09-14T12:00:00",
                "FIRM-A",
            ),
        )
        con.commit()
    finally:
        con.close()

    second = _transition(
        db_path,
        "GRR-002",
        "CONFIRMED",
    )

    assert second["prior_review_id"] == "GRR-001"
    assert second["prior_status"] == "REVIEW_REQUIRED"
    assert second["new_status"] == "CONFIRMED"
    assert _status(db_path) == "CONFIRMED"


def test_professional_transition_requires_authority(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    with pytest.raises(
        GenealogyRelationshipReviewServiceError,
        match="Professional authority",
    ):
        _transition(
            db_path,
            "GRR-PRO",
            "REVIEW_REQUIRED",
            decision_origin="PROFESSIONAL",
        )

    review = _transition(
        db_path,
        "GRR-PRO-2",
        "REVIEW_REQUIRED",
        decision_origin="PROFESSIONAL",
        professional_authority="Licensed genealogist",
        actor_capacity="Professional reviewer",
    )

    assert review["decision_origin"] == "PROFESSIONAL"
    assert (
        review["professional_authority"]
        == "Licensed genealogist"
    )


def test_final_state_must_reopen_through_review_required(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _assertion(
        db_path,
        status="UNRESOLVED",
    )

    reopened = _transition(
        db_path,
        "GRR-REOPEN",
        "REVIEW_REQUIRED",
    )

    assert reopened["prior_status"] == "UNRESOLVED"
    assert reopened["new_status"] == "REVIEW_REQUIRED"
    assert _status(db_path) == "REVIEW_REQUIRED"


def test_cross_scope_review_is_denied_without_history_or_mutation(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    with pytest.raises(
        GenealogyRelationshipReviewServiceError,
        match="Scoped genealogy relationship assertion not found",
    ):
        _transition(
            db_path,
            "GRR-CROSS",
            "REVIEW_REQUIRED",
            owner_id="OWNER-B",
        )

    with pytest.raises(
        GenealogyRelationshipReviewServiceError,
        match="Scoped genealogy relationship assertion not found",
    ):
        _transition(
            db_path,
            "GRR-CROSS-2",
            "REVIEW_REQUIRED",
            firm_id="FIRM-B",
        )

    assert _status(db_path) == "USER_ASSERTED"

    assert list_genealogy_relationship_reviews(
        db_path,
        "GRA-001",
        "OWNER-A",
        "FIRM-A",
    ) == []
