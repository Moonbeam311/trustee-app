import sqlite3

from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)
from database.migrations_person_role_link_schema import (
    apply_person_role_link_schema,
)
from database.migrations_genealogy_relationship_schema import (
    apply_genealogy_relationship_schema,
)
from database.migrations_genealogy_relationship_review_schema import (
    apply_genealogy_relationship_review_schema,
)
from services.services_person_identity import (
    create_person_identity,
)
from services.services_person_role_links import (
    create_person_role_link,
)
from services.services_genealogy_relationships import (
    create_genealogy_relationship_assertion,
)
from services.services_genealogy_relationship_reviews import (
    transition_genealogy_relationship_status,
)
from services.services_genealogy_legacy_read_model import (
    build_genealogy_legacy_read_model,
)


def _ready_db(tmp_path):
    db_path = tmp_path / "genealogy-read-model.db"

    apply_person_identity_schema(db_path)
    apply_person_role_link_schema(db_path)
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

        con.execute(
            """
            CREATE TABLE genealogy_records (
                genealogy_id TEXT PRIMARY KEY,
                trust_id TEXT,
                full_name TEXT,
                parent_1 TEXT,
                parent_2 TEXT,
                spouse TEXT,
                verification_status TEXT
            )
            """
        )

        con.commit()
    finally:
        con.close()

    return db_path


def _person(
    db_path,
    person_id,
    display_name,
    owner_id="OWNER-A",
    firm_id="FIRM-A",
):
    return create_person_identity(
        db_path,
        {
            "person_id": person_id,
            "owner_id": owner_id,
            "firm_id": firm_id,
            "display_name": display_name,
        },
    )


def test_empty_scope_returns_bounded_read_only_model(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    model = build_genealogy_legacy_read_model(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    assert model["workspace"] == "Genealogy & Legacy"
    assert model["read_only"] is True
    assert model["persons"] == []

    assert model["summary"] == {
        "person_count": 0,
        "relationship_assertion_count": 0,
        "source_connected_count": 0,
        "reviewed_assertion_count": 0,
        "status_counts": {},
    }

    assert model["legacy_compatibility"][
        "legacy_rows_included"
    ] is False

    assert model["governance"][
        "automatic_status_advancement"
    ] is False


def test_model_composes_explicit_identity_role_relationship_evidence_and_review(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(
        db_path,
        "PER-A",
        "Jordan Example",
    )
    _person(
        db_path,
        "PER-B",
        "Morgan Example",
    )

    create_person_role_link(
        db_path,
        {
            "link_id": "PRL-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "person_id": "PER-A",
            "role_type": "TRUSTEE",
            "role_record_id": "TRUSTEE-001",
            "capacity_label": "Trustee",
        },
    )

    create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": "GRA-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "subject_person_id": "PER-A",
            "relationship_type": "CHILD_OF",
            "related_person_id": "PER-B",
            "assertion_basis": (
                "User supplied relationship assertion"
            ),
            "created_by": "operator-a",
        },
    )

    transition_genealogy_relationship_status(
        db_path,
        {
            "review_id": "GRR-001",
            "assertion_id": "GRA-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "new_status": "REVIEW_REQUIRED",
            "review_basis": "Document review required",
            "provenance": "Operator review",
            "decision_origin": (
                "OPERATOR_OR_FIDUCIARY"
            ),
            "human_confirmed": True,
            "actor": "operator-a",
            "actor_capacity": "Trustee",
        },
    )

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
                "2026-09-14T13:00:00",
                "FIRM-A",
            ),
        )
        con.commit()
    finally:
        con.close()

    model = build_genealogy_legacy_read_model(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    assert model["summary"][
        "person_count"
    ] == 2

    assert model["summary"][
        "relationship_assertion_count"
    ] == 1

    assert model["summary"][
        "source_connected_count"
    ] == 1

    assert model["summary"][
        "reviewed_assertion_count"
    ] == 1

    assert model["summary"]["status_counts"] == {
        "REVIEW_REQUIRED": 1,
    }

    jordan = next(
        item
        for item in model["persons"]
        if item["person"]["person_id"] == "PER-A"
    )

    assert len(jordan["role_links"]) == 1
    assert len(jordan["relationships"]) == 1

    relationship = jordan["relationships"][0]

    assert relationship["direction"] == "SUBJECT"
    assert relationship[
        "counterparty_person"
    ]["person_id"] == "PER-B"

    assert relationship[
        "source_connected"
    ] is True

    assert relationship[
        "assertion_status"
    ] == "REVIEW_REQUIRED"

    assert len(relationship["evidence"]) == 1
    assert len(relationship["reviews"]) == 1


def test_source_connection_does_not_advance_user_asserted_status(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(
        db_path,
        "PER-A",
        "Jordan Example",
    )
    _person(
        db_path,
        "PER-B",
        "Morgan Example",
    )

    create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": "GRA-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "subject_person_id": "PER-A",
            "relationship_type": "CHILD_OF",
            "related_person_id": "PER-B",
        },
    )

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
                "2026-09-14T13:00:00",
                "FIRM-A",
            ),
        )
        con.commit()
    finally:
        con.close()

    model = build_genealogy_legacy_read_model(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    jordan = next(
        item
        for item in model["persons"]
        if item["person"]["person_id"] == "PER-A"
    )

    relationship = jordan["relationships"][0]

    assert relationship["source_connected"] is True
    assert relationship[
        "assertion_status"
    ] == "USER_ASSERTED"

    assert model["summary"]["status_counts"] == {
        "USER_ASSERTED": 1,
    }


def test_cross_scope_people_and_relationships_are_not_exposed(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(
        db_path,
        "PER-A",
        "Visible Person",
    )

    _person(
        db_path,
        "PER-X",
        "Other Firm Person",
        owner_id="OWNER-X",
        firm_id="FIRM-X",
    )

    model = build_genealogy_legacy_read_model(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    ids = {
        item["person"]["person_id"]
        for item in model["persons"]
    }

    assert ids == {"PER-A"}


def test_legacy_parent_spouse_text_is_not_inferred_into_canonical_model(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(
        db_path,
        "PER-A",
        "Jordan Example",
    )

    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            INSERT INTO genealogy_records (
                genealogy_id,
                full_name,
                parent_1,
                parent_2,
                spouse,
                verification_status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "GEN-LEGACY-001",
                "Jordan Example",
                "Morgan Example",
                "Taylor Example",
                "Casey Example",
                "verified",
            ),
        )
        con.commit()
    finally:
        con.close()

    model = build_genealogy_legacy_read_model(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    assert model["summary"][
        "relationship_assertion_count"
    ] == 0

    assert model["persons"][0][
        "relationships"
    ] == []

    assert model["legacy_compatibility"][
        "legacy_rows_included"
    ] is False

    assert model["legacy_compatibility"][
        "automatic_parent_spouse_conversion"
    ] is False
