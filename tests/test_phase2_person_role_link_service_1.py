import pytest

from database.migrations_person_identity_schema import (
    apply_person_identity_schema,
)
from database.migrations_person_role_link_schema import (
    apply_person_role_link_schema,
)
from services.services_person_identity import (
    create_person_identity,
)
from services.services_person_role_links import (
    PersonRoleLinkServiceError,
    create_person_role_link,
    get_person_role_link,
    list_person_role_links,
    list_role_person_links,
)


def _ready_db(tmp_path):
    db_path = tmp_path / "role-link-service.db"

    apply_person_identity_schema(db_path)
    apply_person_role_link_schema(db_path)

    return db_path


def _create_person(
    db_path,
    person_id="PER-001",
    owner_id="OWNER-A",
    firm_id="FIRM-A",
    display_name="Example Person",
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


def test_role_link_requires_explicit_scope_and_fields(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    with pytest.raises(
        PersonRoleLinkServiceError,
        match="Owner scope is required",
    ):
        create_person_role_link(
            db_path,
            {
                "link_id": "PRL-001",
                "firm_id": "FIRM-A",
                "person_id": "PER-001",
                "role_type": "fiduciary",
                "role_record_id": "FID-001",
            },
        )

    with pytest.raises(
        PersonRoleLinkServiceError,
        match="Role type is required",
    ):
        create_person_role_link(
            db_path,
            {
                "link_id": "PRL-001",
                "owner_id": "OWNER-A",
                "firm_id": "FIRM-A",
                "person_id": "PER-001",
                "role_record_id": "FID-001",
            },
        )


def test_role_link_requires_existing_person_in_same_scope(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _create_person(db_path)

    with pytest.raises(
        PersonRoleLinkServiceError,
        match="Scoped Person identity not found",
    ):
        create_person_role_link(
            db_path,
            {
                "link_id": "PRL-001",
                "owner_id": "OWNER-B",
                "firm_id": "FIRM-A",
                "person_id": "PER-001",
                "role_type": "fiduciary",
                "role_record_id": "FID-001",
            },
        )


def test_explicit_role_link_creation_and_scoped_read(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _create_person(db_path)

    created = create_person_role_link(
        db_path,
        {
            "link_id": "PRL-001",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "person_id": "PER-001",
            "role_type": "fiduciary",
            "role_record_id": "FID-001",
            "trust_id": "TR-001",
            "capacity_label": "Trustee",
            "created_by": "tester",
        },
    )

    assert created["link_id"] == "PRL-001"
    assert created["person_id"] == "PER-001"
    assert created["role_type"] == "fiduciary"
    assert created["role_record_id"] == "FID-001"

    assert get_person_role_link(
        db_path,
        "PRL-001",
        "OWNER-A",
        "FIRM-A",
    ) is not None

    assert get_person_role_link(
        db_path,
        "PRL-001",
        "OWNER-B",
        "FIRM-A",
    ) is None


def test_duplicate_explicit_role_pointer_is_rejected(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _create_person(db_path)

    payload = {
        "link_id": "PRL-001",
        "owner_id": "OWNER-A",
        "firm_id": "FIRM-A",
        "person_id": "PER-001",
        "role_type": "beneficiary",
        "role_record_id": "BEN-001",
    }

    create_person_role_link(db_path, payload)

    duplicate = dict(payload)
    duplicate["link_id"] = "PRL-002"

    with pytest.raises(
        PersonRoleLinkServiceError,
        match="already exists",
    ):
        create_person_role_link(
            db_path,
            duplicate,
        )


def test_matching_names_do_not_create_role_links(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _create_person(
        db_path,
        display_name="Same Name",
    )

    assert list_person_role_links(
        db_path,
        "PER-001",
        "OWNER-A",
        "FIRM-A",
    ) == []

    assert list_role_person_links(
        db_path,
        "fiduciary",
        "FID-SAME-NAME",
        "OWNER-A",
        "FIRM-A",
    ) == []


def test_role_link_lists_do_not_cross_scope(
    tmp_path,
):
    db_path = _ready_db(tmp_path)

    _create_person(
        db_path,
        person_id="PER-A",
        owner_id="OWNER-A",
        firm_id="FIRM-A",
    )

    _create_person(
        db_path,
        person_id="PER-B",
        owner_id="OWNER-B",
        firm_id="FIRM-B",
    )

    create_person_role_link(
        db_path,
        {
            "link_id": "PRL-A",
            "owner_id": "OWNER-A",
            "firm_id": "FIRM-A",
            "person_id": "PER-A",
            "role_type": "fiduciary",
            "role_record_id": "FID-A",
        },
    )

    create_person_role_link(
        db_path,
        {
            "link_id": "PRL-B",
            "owner_id": "OWNER-B",
            "firm_id": "FIRM-B",
            "person_id": "PER-B",
            "role_type": "fiduciary",
            "role_record_id": "FID-B",
        },
    )

    rows_a = list_person_role_links(
        db_path,
        "PER-A",
        "OWNER-A",
        "FIRM-A",
    )

    rows_b = list_person_role_links(
        db_path,
        "PER-B",
        "OWNER-B",
        "FIRM-B",
    )

    assert [row["link_id"] for row in rows_a] == [
        "PRL-A",
    ]

    assert [row["link_id"] for row in rows_b] == [
        "PRL-B",
    ]

    assert list_person_role_links(
        db_path,
        "PER-A",
        "OWNER-B",
        "FIRM-B",
    ) == []
