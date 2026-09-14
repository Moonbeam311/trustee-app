import re

import pytest

from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)
from services.services_person_identity import (
    PersonIdentityServiceError,
    create_person_identity,
    generate_person_identity_id,
)


def test_person_identity_id_is_system_format():
    person_id = generate_person_identity_id()

    assert re.fullmatch(
        r"PER-[0-9A-F]{20}",
        person_id,
    )


def test_person_identity_ids_are_not_count_sequences():
    first = generate_person_identity_id()
    second = generate_person_identity_id()

    assert first != second
    assert not re.fullmatch(r"PER-\d{3}", first)
    assert not re.fullmatch(r"PER-\d{3}", second)


def test_person_identity_service_still_requires_explicit_id(tmp_path):
    db_path = tmp_path / "person-id-contract.db"
    apply_person_identity_schema(db_path)

    with pytest.raises(
        PersonIdentityServiceError,
        match="Person ID is required",
    ):
        create_person_identity(
            db_path,
            {
                "owner_id": "OWNER-A",
                "firm_id": "FIRM-A",
                "display_name": "Example Person",
            },
        )


def test_issued_person_id_can_be_used_by_existing_service(tmp_path):
    db_path = tmp_path / "person-id-use.db"
    apply_person_identity_schema(db_path)

    person_id = generate_person_identity_id()

    created = create_person_identity(
        db_path,
        {
            "person_id": person_id,
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Example Person",
            "created_by": "tester",
        },
    )

    assert created["person_id"] == person_id
    assert created["display_name"] == "Example Person"
