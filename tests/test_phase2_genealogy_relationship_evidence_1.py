import sqlite3

import pytest

from database.migrations_genealogy_relationship_schema import (
    apply_genealogy_relationship_schema,
)
from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)
from services.services_genealogy_relationship_evidence import (
    GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE,
    GenealogyRelationshipEvidenceServiceError,
    build_genealogy_relationship_media_link,
    list_genealogy_relationship_media_evidence,
)
from services.services_genealogy_relationships import (
    create_genealogy_relationship_assertion,
)
from services.services_person_identity import (
    create_person_identity,
)


def _ready_db(tmp_path):
    db_path = tmp_path / "genealogy-evidence.db"

    apply_person_identity_schema(db_path)
    apply_genealogy_relationship_schema(db_path)

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


def _person(
    db_path,
    person_id,
    owner_id="OWNER-A",
    firm_id="FIRM-A",
):
    create_person_identity(
        db_path,
        {
            "person_id": person_id,
            "owner_id": owner_id,
            "firm_id": firm_id,
            "display_name": f"Person {person_id}",
        },
    )


def _assertion(
    db_path,
    assertion_id="GRA-001",
    owner_id="OWNER-A",
    firm_id="FIRM-A",
    trust_id="TR-001",
):
    _person(
        db_path,
        f"{assertion_id}-SUBJECT",
        owner_id,
        firm_id,
    )
    _person(
        db_path,
        f"{assertion_id}-RELATED",
        owner_id,
        firm_id,
    )

    return create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": assertion_id,
            "owner_id": owner_id,
            "firm_id": firm_id,
            "subject_person_id": (
                f"{assertion_id}-SUBJECT"
            ),
            "relationship_type": "PARENT_OF",
            "related_person_id": (
                f"{assertion_id}-RELATED"
            ),
            "trust_id": trust_id,
        },
    )


def test_adapter_uses_one_canonical_existing_media_entity_type(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    payload = build_genealogy_relationship_media_link(
        db_path,
        "GRA-001",
        "OWNER-A",
        "FIRM-A",
    )

    assert (
        GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE
        == "genealogy_relationship_assertion"
    )

    assert payload == {
        "related_entity_type":
            "genealogy_relationship_assertion",
        "related_entity_id": "GRA-001",
        "firm_id": "FIRM-A",
        "trust_id": "TR-001",
    }


def test_adapter_rejects_missing_or_cross_scope_assertion(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    with pytest.raises(
        GenealogyRelationshipEvidenceServiceError,
        match=(
            "Scoped genealogy relationship assertion "
            "not found"
        ),
    ):
        build_genealogy_relationship_media_link(
            db_path,
            "GRA-001",
            "OWNER-B",
            "FIRM-A",
        )

    with pytest.raises(
        GenealogyRelationshipEvidenceServiceError,
        match=(
            "Scoped genealogy relationship assertion "
            "not found"
        ),
    ):
        build_genealogy_relationship_media_link(
            db_path,
            "GRA-001",
            "OWNER-A",
            "FIRM-B",
        )


def test_adapter_does_not_create_media_record(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    build_genealogy_relationship_media_link(
        db_path,
        "GRA-001",
        "OWNER-A",
        "FIRM-A",
    )

    con = sqlite3.connect(db_path)
    try:
        count = con.execute(
            """
            SELECT COUNT(*)
            FROM media_records
            """
        ).fetchone()[0]
    finally:
        con.close()

    assert count == 0


def test_evidence_listing_reads_existing_media_store_only(
    tmp_path,
):
    db_path = _ready_db(tmp_path)
    _assertion(db_path)

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO media_records (
                media_id,
                trust_id,
                related_entity_type,
                related_entity_id,
                media_type,
                file_path,
                category,
                description,
                created_at,
                firm_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MED-001",
                "TR-001",
                "genealogy_relationship_assertion",
                "GRA-001",
                "document",
                "/tmp/example.pdf",
                "source",
                "Example source",
                "2026-09-14T12:00:00",
                "FIRM-A",
            ),
        )
        con.commit()
    finally:
        con.close()

    records = list_genealogy_relationship_media_evidence(
        db_path,
        "GRA-001",
        "OWNER-A",
        "FIRM-A",
    )

    assert len(records) == 1
    assert records[0]["media_id"] == "MED-001"
    assert (
        records[0]["related_entity_type"]
        == "genealogy_relationship_assertion"
    )
    assert records[0]["related_entity_id"] == "GRA-001"


def test_evidence_listing_does_not_cross_firm_scope(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _assertion(
        db_path,
        assertion_id="GRA-A",
        owner_id="OWNER-A",
        firm_id="FIRM-A",
        trust_id="TR-A",
    )

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO media_records (
                media_id,
                trust_id,
                related_entity_type,
                related_entity_id,
                media_type,
                file_path,
                category,
                description,
                created_at,
                firm_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MED-A",
                "TR-A",
                "genealogy_relationship_assertion",
                "GRA-A",
                "document",
                "/tmp/a.pdf",
                "source",
                "Correct firm",
                "2026-09-14T12:00:00",
                "FIRM-A",
            ),
        )

        con.execute(
            """
            INSERT INTO media_records (
                media_id,
                trust_id,
                related_entity_type,
                related_entity_id,
                media_type,
                file_path,
                category,
                description,
                created_at,
                firm_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MED-B",
                "TR-B",
                "genealogy_relationship_assertion",
                "GRA-A",
                "document",
                "/tmp/b.pdf",
                "source",
                "Wrong firm",
                "2026-09-14T12:01:00",
                "FIRM-B",
            ),
        )

        con.commit()
    finally:
        con.close()

    records = list_genealogy_relationship_media_evidence(
        db_path,
        "GRA-A",
        "OWNER-A",
        "FIRM-A",
    )

    assert [row["media_id"] for row in records] == [
        "MED-A",
    ]
