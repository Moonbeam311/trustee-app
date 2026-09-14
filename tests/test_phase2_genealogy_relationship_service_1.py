import sqlite3

import pytest

from database.migrations_genealogy_relationship_schema import (
    apply_genealogy_relationship_schema,
)
from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)
from services.services_genealogy_relationships import (
    GenealogyRelationshipServiceError,
    create_genealogy_relationship_assertion,
    get_genealogy_relationship_assertion,
    list_genealogy_relationship_assertions_for_person,
)
from services.services_person_identity import (
    create_person_identity,
)


def _ready_db(tmp_path):
    db_path = tmp_path / "genealogy-service.db"

    apply_person_identity_schema(db_path)
    apply_genealogy_relationship_schema(db_path)

    return db_path


def _person(
    db_path,
    person_id,
    owner_id="OWNER-A",
    firm_id="FIRM-A",
    display_name=None,
):
    return create_person_identity(
        db_path,
        {
            "person_id": person_id,
            "owner_id": owner_id,
            "firm_id": firm_id,
            "display_name": (
                display_name
                or f"Person {person_id}"
            ),
        },
    )


def _count_assertions(db_path):
    con = sqlite3.connect(db_path)

    try:
        return con.execute(
            """
            SELECT COUNT(*)
            FROM genealogy_relationship_assertions
            """
        ).fetchone()[0]
    finally:
        con.close()


def test_relationship_assertion_requires_explicit_scope_and_fields(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    with pytest.raises(
        GenealogyRelationshipServiceError,
        match="Owner scope is required",
    ):
        create_genealogy_relationship_assertion(
            db_path,
            {
                "assertion_id": "GRA-001",
                "firm_id": "FIRM-A",
                "subject_person_id": "PER-A",
                "relationship_type": "PARENT_OF",
                "related_person_id": "PER-B",
            },
        )

    with pytest.raises(
        GenealogyRelationshipServiceError,
        match="Relationship type is required",
    ):
        create_genealogy_relationship_assertion(
            db_path,
            {
                "assertion_id": "GRA-001",
                "owner_id": "OWNER-A",
                "firm_id": "FIRM-A",
                "subject_person_id": "PER-A",
                "related_person_id": "PER-B",
            },
        )


def test_relationship_assertion_requires_two_people_in_same_scope(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(
        db_path,
        "PER-A",
        owner_id="OWNER-A",
        firm_id="FIRM-A",
    )

    _person(
        db_path,
        "PER-B",
        owner_id="OWNER-B",
        firm_id="FIRM-A",
    )

    with pytest.raises(
        GenealogyRelationshipServiceError,
        match="Scoped Related Person identity not found",
    ):
        create_genealogy_relationship_assertion(
            db_path,
            {
                "assertion_id": "GRA-001",
                "owner_id": "OWNER-A",
                "firm_id": "FIRM-A",
                "subject_person_id": "PER-A",
                "relationship_type": "PARENT_OF",
                "related_person_id": "PER-B",
            },
        )

    assert _count_assertions(db_path) == 0


def test_new_relationship_assertion_must_begin_user_asserted(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(db_path, "PER-A")
    _person(db_path, "PER-B")

    with pytest.raises(
        GenealogyRelationshipServiceError,
        match="must begin as USER_ASSERTED",
    ):
        create_genealogy_relationship_assertion(
            db_path,
            {
                "assertion_id": "GRA-001",
                "owner_id": "OWNER-A",
                "firm_id": "FIRM-A",
                "subject_person_id": "PER-A",
                "relationship_type": "PARENT_OF",
                "related_person_id": "PER-B",
                "assertion_status": "CONFIRMED",
            },
        )

    created = create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": "GRA-002",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "subject_person_id": "PER-A",
            "relationship_type": "PARENT_OF",
            "related_person_id": "PER-B",
            "assertion_basis": "Operator assertion",
        },
    )

    assert created["assertion_status"] == "USER_ASSERTED"


def test_relationship_assertion_is_directional_without_auto_reciprocal(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(db_path, "PER-A")
    _person(db_path, "PER-B")

    created = create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": "GRA-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "subject_person_id": "PER-A",
            "relationship_type": "PARENT_OF",
            "related_person_id": "PER-B",
        },
    )

    assert created["subject_person_id"] == "PER-A"
    assert created["related_person_id"] == "PER-B"
    assert _count_assertions(db_path) == 1

    for person_id in ("PER-A", "PER-B"):
        rows = (
            list_genealogy_relationship_assertions_for_person(
                db_path,
                person_id,
                "OWNER-A",
                "FIRM-A",
            )
        )

        assert len(rows) == 1
        assert rows[0]["assertion_id"] == "GRA-001"
        assert rows[0]["subject_person_id"] == "PER-A"
        assert rows[0]["related_person_id"] == "PER-B"

    con = sqlite3.connect(db_path)

    try:
        reverse_count = con.execute(
            """
            SELECT COUNT(*)
            FROM genealogy_relationship_assertions
            WHERE subject_person_id='PER-B'
              AND related_person_id='PER-A'
            """
        ).fetchone()[0]
    finally:
        con.close()

    assert reverse_count == 0


def test_duplicate_explicit_directional_assertion_is_rejected(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(db_path, "PER-A")
    _person(db_path, "PER-B")

    payload = {
        "assertion_id": "GRA-001",
        "owner_id": "OWNER-A",
        "firm_id": "FIRM-A",
        "subject_person_id": "PER-A",
        "relationship_type": "PARENT_OF",
        "related_person_id": "PER-B",
    }

    create_genealogy_relationship_assertion(
        db_path,
        payload,
    )

    duplicate = dict(payload)
    duplicate["assertion_id"] = "GRA-002"

    with pytest.raises(
        GenealogyRelationshipServiceError,
        match="already exists",
    ):
        create_genealogy_relationship_assertion(
            db_path,
            duplicate,
        )

    assert _count_assertions(db_path) == 1


def test_relationship_reads_do_not_cross_owner_firm_scope(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _person(
        db_path,
        "PER-A1",
        owner_id="OWNER-A",
        firm_id="FIRM-A",
    )
    _person(
        db_path,
        "PER-A2",
        owner_id="OWNER-A",
        firm_id="FIRM-A",
    )

    _person(
        db_path,
        "PER-B1",
        owner_id="OWNER-B",
        firm_id="FIRM-B",
    )
    _person(
        db_path,
        "PER-B2",
        owner_id="OWNER-B",
        firm_id="FIRM-B",
    )

    create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": "GRA-A",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "subject_person_id": "PER-A1",
            "relationship_type": "PARENT_OF",
            "related_person_id": "PER-A2",
        },
    )

    create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": "GRA-B",
            "owner_id": "OWNER-B",
            "firm_id": "FIRM-B",
            "subject_person_id": "PER-B1",
            "relationship_type": "PARENT_OF",
            "related_person_id": "PER-B2",
        },
    )

    assert get_genealogy_relationship_assertion(
        db_path,
        "GRA-A",
        "OWNER-A",
        "FIRM-A",
    ) is not None

    assert get_genealogy_relationship_assertion(
        db_path,
        "GRA-A",
        "OWNER-B",
        "FIRM-B",
    ) is None

    rows = list_genealogy_relationship_assertions_for_person(
        db_path,
        "PER-A1",
        "OWNER-A",
        "FIRM-A",
    )

    assert [row["assertion_id"] for row in rows] == [
        "GRA-A",
    ]

    assert (
        list_genealogy_relationship_assertions_for_person(
            db_path,
            "PER-A1",
            "OWNER-B",
            "FIRM-B",
        )
        == []
    )
