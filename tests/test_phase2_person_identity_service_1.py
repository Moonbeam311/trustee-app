import pytest

from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)
from services.services_person_identity import (
    PersonIdentityServiceError,
    create_person_identity,
    get_person_identity,
    list_person_identities,
)


def _ready_db(tmp_path, name="persons.db"):
    db_path = tmp_path / name
    apply_person_identity_schema(db_path)
    return db_path


def test_person_creation_requires_explicit_scope(tmp_path):
    db_path = _ready_db(tmp_path)

    with pytest.raises(
        PersonIdentityServiceError,
        match="owner scope is required",
    ):
        create_person_identity(
            db_path,
            {
                "person_id": "PER-001",
                "firm_id": "FIRM-001",
                "display_name": "Example Person",
            },
        )

    with pytest.raises(
        PersonIdentityServiceError,
        match="firm scope is required",
    ):
        create_person_identity(
            db_path,
            {
                "person_id": "PER-001",
                "owner_id": "OWNER-001",
                "display_name": "Example Person",
            },
        )


def test_person_reads_are_owner_and_firm_scoped(tmp_path):
    db_path = _ready_db(tmp_path)

    created = create_person_identity(
        db_path,
        {
            "person_id": "PER-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Jordan Example",
            "created_by": "tester",
        },
    )

    assert created["person_id"] == "PER-001"

    assert get_person_identity(
        db_path,
        "PER-001",
        "OWNER-A",
        "FIRM-A",
    ) is not None

    assert get_person_identity(
        db_path,
        "PER-001",
        "OWNER-B",
        "FIRM-A",
    ) is None

    assert get_person_identity(
        db_path,
        "PER-001",
        "OWNER-A",
        "FIRM-B",
    ) is None


def test_matching_names_do_not_merge_people(tmp_path):
    db_path = _ready_db(tmp_path)

    first = create_person_identity(
        db_path,
        {
            "person_id": "PER-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Same Name",
        },
    )

    second = create_person_identity(
        db_path,
        {
            "person_id": "PER-002",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Same Name",
        },
    )

    assert first["person_id"] == "PER-001"
    assert second["person_id"] == "PER-002"

    rows = list_person_identities(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    assert [row["person_id"] for row in rows] == [
        "PER-001",
        "PER-002",
    ]


def test_person_id_is_not_reused_across_scopes(tmp_path):
    db_path = _ready_db(tmp_path)

    create_person_identity(
        db_path,
        {
            "person_id": "PER-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "First Person",
        },
    )

    with pytest.raises(
        PersonIdentityServiceError,
        match="could not be created",
    ):
        create_person_identity(
            db_path,
            {
                "person_id": "PER-001",
                "owner_id": "OWNER-B",
                "firm_id": "FIRM-B",
                "display_name": "Different Person",
            },
        )


def test_person_list_does_not_cross_scope(tmp_path):
    db_path = _ready_db(tmp_path)

    create_person_identity(
        db_path,
        {
            "person_id": "PER-A",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "display_name": "Alpha Person",
        },
    )

    create_person_identity(
        db_path,
        {
            "person_id": "PER-B",
            "owner_id": "OWNER-B",
            "firm_id": "FIRM-B",
            "display_name": "Beta Person",
        },
    )

    rows_a = list_person_identities(
        db_path,
        "OWNER-A",
        "FIRM-A",
    )

    rows_b = list_person_identities(
        db_path,
        "OWNER-B",
        "FIRM-B",
    )

    assert [row["person_id"] for row in rows_a] == ["PER-A"]
    assert [row["person_id"] for row in rows_b] == ["PER-B"]
