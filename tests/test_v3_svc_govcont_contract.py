import sqlite3

import pytest

import database.db as database_db
import services.services_governance as governance
from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
from services.services_intake_trust_bridge import (
    BridgeError,
    add_continuity_record,
    create_continuity_profile,
    get_continuity_profile,
    transition_activation_plan,
    validate_no_secret_material,
)


def test_governance_public_contract_entry_points_remain_callable():
    names = {
        "create_governance_record",
        "list_governance_records",
        "get_governance_record",
        "approve_governance_directive",
        "transition_governance_record",
        "create_directive_implementation_entry",
        "list_directive_implementation_entries",
        "create_governance_relationship",
        "get_governance_relationship",
        "record_governance_relationship_audit",
        "build_governance_evidence_export_index",
        "build_governance_evidence_export_manifest",
    }
    assert all(callable(getattr(governance, name, None)) for name in names)


def test_governance_firm_lifecycle_approval_relationship_and_audit_contract(
    monkeypatch, tmp_path
):
    db_path = tmp_path / "governance-contract.db"
    active_firm = {"id": "FIRM-GOV-A"}
    monkeypatch.setattr(database_db, "DB_PATH", db_path)
    monkeypatch.setattr(governance, "get_current_firm_id", lambda: active_firm["id"])

    created, directive_id = governance.create_governance_record(
        "directive",
        {
            "title": "Preserve explicit contract",
            "authority_basis": "Recorded governance authority",
            "created_by": "contract-test",
        },
    )
    assert created
    assert governance.get_governance_record("directive", directive_id)["status"] == "Draft"

    approved, approved_id = governance.approve_governance_directive(
        directive_id, "contract-approver"
    )
    assert (approved, approved_id) == (True, directive_id)
    directive = governance.get_governance_record("directive", directive_id)
    assert directive["approved_by"] == "contract-approver"
    assert directive["approved_at"]

    transitioned, status = governance.transition_governance_record(
        "directive", directive_id, "Issued", actor="contract-test"
    )
    assert (transitioned, status) == (True, "Issued")
    rejected, message = governance.transition_governance_record(
        "directive", directive_id, "Completed", actor="contract-test"
    )
    assert not rejected
    assert "cannot move" in message
    assert governance.get_governance_record("directive", directive_id)["status"] == "Issued"

    related, relationship_id = governance.create_governance_relationship(
        {
            "source_object_type": "Directive",
            "source_object_id": directive_id,
            "relationship_type": "governs",
            "target_object_type": "Trust",
            "target_object_id": "TR-CONTRACT-1",
            "authority": "Recorded governance authority",
            "reason": "Compatibility evidence",
            "created_by": "contract-test",
        }
    )
    assert related
    assert governance.get_governance_relationship(relationship_id)[
        "source_object_id"
    ] == directive_id
    audits = governance.list_audits_for_governance_relationship(relationship_id)
    assert any(row["outcome"] == "created" for row in audits)

    active_firm["id"] = "FIRM-GOV-B"
    assert governance.get_governance_record("directive", directive_id) is None
    assert governance.get_governance_relationship(relationship_id) is None
    assert governance.list_governance_records("directive") == []


@pytest.fixture()
def continuity_db(tmp_path):
    path = tmp_path / "continuity-contract.db"
    migrate_intake_trust_bridge(path)
    return path


def _profile(continuity_db, firm_id="FIRM-CONT-A"):
    return create_continuity_profile(
        continuity_db,
        firm_id,
        "Continuity Subject",
        "person",
        "account owner",
        "Operational continuity",
        "contract-test",
    )


def test_continuity_profile_children_readiness_and_firm_isolation(continuity_db):
    profile_id = _profile(continuity_db)
    responsibility_id = add_continuity_record(
        continuity_db,
        "continuity_responsibilities",
        profile_id,
        "FIRM-CONT-A",
        "contract-test",
        {
            "category": "trust administration",
            "description": "Maintain governed records",
            "current_responsible_party": "Current fiduciary",
            "successor_responsible_party": "Named successor",
            "authority_source": "Recorded instrument",
            "supporting_document_reference": "DOC-1",
        },
    )
    digital_id = add_continuity_record(
        continuity_db,
        "continuity_digital_accounts",
        profile_id,
        "FIRM-CONT-A",
        "contract-test",
        {
            "institution_service": "Email provider",
            "account_category": "email",
            "account_label": "Primary operational email",
            "vault_reference": "VAULT-ITEM-42",
            "last_verified_date": "2026-08-20",
        },
    )
    receivable_id = add_continuity_record(
        continuity_db,
        "continuity_receivables",
        profile_id,
        "FIRM-CONT-A",
        "contract-test",
        {"payer_debtor": "Tenant", "description": "Monthly rent"},
    )
    payable_id = add_continuity_record(
        continuity_db,
        "continuity_payables",
        profile_id,
        "FIRM-CONT-A",
        "contract-test",
        {"creditor_payee": "Utility", "description": "Electric service"},
    )

    bundle = get_continuity_profile(continuity_db, profile_id, "FIRM-CONT-A")
    assert bundle["profile"]["continuity_profile_id"] == profile_id
    assert bundle["responsibilities"][0]["responsibility_id"] == responsibility_id
    assert bundle["digital_accounts"][0]["digital_account_id"] == digital_id
    assert bundle["digital_accounts"][0]["vault_reference"] == "VAULT-ITEM-42"
    assert bundle["receivables"][0]["receivable_id"] == receivable_id
    assert bundle["payables"][0]["payable_id"] == payable_id
    assert bundle["readiness"]["classification"] == "ready_for_review"
    assert get_continuity_profile(continuity_db, profile_id, "FIRM-CONT-B") is None


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "forbidden"},
        {"pin": "1234"},
        {"recovery_code": "backup-code"},
        {"security_answer": "answer"},
        {"token": "secret-token"},
        {"private_key": "private-key"},
        {"cvv": "123"},
        {"notes": "password: forbidden"},
    ],
)
def test_continuity_rejects_secret_material(payload):
    with pytest.raises(BridgeError, match="Secret|secret"):
        validate_no_secret_material(payload)


def test_continuity_activation_transitions_and_event_history_are_preserved(
    continuity_db,
):
    profile_id = _profile(continuity_db)
    plan_id = add_continuity_record(
        continuity_db,
        "continuity_activation_plans",
        profile_id,
        "FIRM-CONT-A",
        "contract-test",
        {
            "continuity_subject": "Continuity Subject",
            "triggering_event": "Documented incapacity",
            "required_evidence": "Recorded determination",
            "authorized_recognizer": "Named professional",
            "restoration_transfer_closure_procedure": "Document review and closure",
        },
    )

    with pytest.raises(BridgeError, match="Invalid activation-plan transition"):
        transition_activation_plan(
            continuity_db,
            plan_id,
            profile_id,
            "FIRM-CONT-A",
            "contract-test",
            "active",
            "Unsupported jump",
        )
    with pytest.raises(BridgeError, match="basis"):
        transition_activation_plan(
            continuity_db,
            plan_id,
            profile_id,
            "FIRM-CONT-A",
            "contract-test",
            "plan_reviewed",
            "",
        )

    transition_activation_plan(
        continuity_db,
        plan_id,
        profile_id,
        "FIRM-CONT-A",
        "contract-test",
        "plan_reviewed",
        "Operator review completed",
    )
    bundle = get_continuity_profile(continuity_db, profile_id, "FIRM-CONT-A")
    assert bundle["activation_plans"][0]["status"] == "plan_reviewed"

    connection = sqlite3.connect(continuity_db)
    event = connection.execute(
        """SELECT event_id,previous_state_json,new_state_json
           FROM continuity_events
           WHERE continuity_profile_id=? AND event_type='ACTIVATION_STATUS_CHANGED'""",
        (profile_id,),
    ).fetchone()
    assert "plan_drafted" in event[1]
    assert "plan_reviewed" in event[2]
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute(
            "UPDATE continuity_events SET event_basis='changed' WHERE event_id=?",
            (event[0],),
        )
    connection.rollback()
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM continuity_events WHERE event_id=?", (event[0],))
    connection.rollback()
    connection.close()
