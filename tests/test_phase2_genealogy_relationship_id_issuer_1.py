import re

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
    generate_genealogy_relationship_assertion_id,
)
from services.services_person_identity import (
    create_person_identity,
)


def _ready_db(tmp_path):
    db_path = tmp_path / "genealogy-relationship-id.db"

    apply_person_identity_schema(db_path)
    apply_genealogy_relationship_schema(db_path)

    create_person_identity(
        db_path,
        {
            "person_id": "PER-A",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Person A",
        },
    )
    create_person_identity(
        db_path,
        {
            "person_id": "PER-B",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Person B",
        },
    )

    return db_path


def test_generated_relationship_assertion_id_has_canonical_format():
    values = [
        generate_genealogy_relationship_assertion_id()
        for _ in range(64)
    ]

    assert all(
        re.fullmatch(r"GRA-[0-9A-F]{20}", value)
        for value in values
    )

    assert len(set(values)) == len(values)


def test_create_service_still_requires_explicit_assertion_id(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    with pytest.raises(
        GenealogyRelationshipServiceError,
        match="Assertion ID is required",
    ):
        create_genealogy_relationship_assertion(
            db_path,
            {
                "owner_id": "OWNER-A",
                "firm_id": "FIRM-A",
                "subject_person_id": "PER-A",
                "relationship_type": "PARENT_OF",
                "related_person_id": "PER-B",
            },
        )


def test_generated_assertion_id_is_accepted_by_existing_service(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    assertion_id = generate_genealogy_relationship_assertion_id()

    created = create_genealogy_relationship_assertion(
        db_path,
        {
            "assertion_id": assertion_id,
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "subject_person_id": "PER-A",
            "relationship_type": "PARENT_OF",
            "related_person_id": "PER-B",
            "assertion_basis": "Explicit operator assertion",
        },
    )

    assert created["assertion_id"] == assertion_id
    assert created["assertion_status"] == "USER_ASSERTED"
