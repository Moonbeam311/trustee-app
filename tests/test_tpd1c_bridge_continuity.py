import sqlite3

import pytest

from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
from services.services_intake_trust_bridge import (
    BridgeError, FORMATION_FIELD_CONTROLS, REQUIRED_FIELDS, acknowledge_source_rebase, add_continuity_record, confirm_bridge,
    create_continuity_profile, create_or_resume_trust, evaluate_eligibility,
    get_bridge, get_continuity_profile, link_continuity_profile, prepare_bridge, transition_activation_plan,
)


@pytest.fixture()
def pilot_db(tmp_path):
    path = tmp_path / "tpd1c.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE intake_sessions(id INTEGER PRIMARY KEY,intake_id TEXT,firm_id TEXT,status TEXT,updated_at TEXT);
    CREATE TABLE intake_document_recommendations(id INTEGER PRIMARY KEY AUTOINCREMENT,intake_id TEXT,firm_id TEXT,workflow_key TEXT,title TEXT,reason TEXT,status TEXT,created_at TEXT,updated_at TEXT,created_by TEXT);
    CREATE TABLE intake_final_draft_completion_gate(id INTEGER PRIMARY KEY,intake_id TEXT,firm_id TEXT,workflow_key TEXT,document_key TEXT,gate_status TEXT,updated_at TEXT);
    CREATE TABLE professional_review_issues(id INTEGER PRIMARY KEY,intake_id TEXT,firm_id TEXT,workflow_key TEXT,status TEXT,severity TEXT);
    CREATE TABLE intake_workflow_bridge_answers(id INTEGER PRIMARY KEY,intake_id TEXT,firm_id TEXT,workflow_key TEXT,question_key TEXT,answer_key TEXT,answer_label TEXT,updated_at TEXT);
    CREATE TABLE intake_answers(id INTEGER PRIMARY KEY,intake_id TEXT,firm_id TEXT,question_key TEXT,answer_key TEXT,answer_label TEXT,created_at TEXT);
    CREATE TABLE matter_intake_links(bridge_id TEXT PRIMARY KEY,firm_id TEXT,matter_id TEXT,intake_id TEXT,link_status TEXT,ended_at TEXT);
    CREATE TABLE trusts(
      trust_id TEXT PRIMARY KEY, trust_name TEXT, short_name TEXT, jurisdiction TEXT, effective_date TEXT,
      trust_type TEXT, trust_purpose TEXT, accounting_method TEXT, workflow_mode TEXT, grantor_name TEXT,
      grantor_type TEXT, grantor_contact TEXT, settlor_name TEXT, trustee_name TEXT, successor_trustee_name TEXT,
      beneficiary_name TEXT, record_visibility TEXT, workflow_mode_confirmed TEXT, ai_explanations TEXT,
      recommended_guidance TEXT, initial_corpus_description TEXT, property_mapping_timing TEXT,
      asset_categories TEXT, generate_schedule_recommendations TEXT, status TEXT, firm_id TEXT);
    INSERT INTO intake_sessions VALUES(1,'INT-1','FIRM-1','completed','v1');
    INSERT INTO intake_document_recommendations(intake_id,firm_id,workflow_key,title,reason,status,created_at,updated_at,created_by)
      VALUES('INT-1','FIRM-1','declaration_of_trust','Declaration','Planning basis','accepted','v1','v1','operator');
    INSERT INTO intake_final_draft_completion_gate VALUES(1,'INT-1','FIRM-1','declaration_of_trust','declaration','completed_preparation','v1');
    INSERT INTO intake_workflow_bridge_answers VALUES(1,'INT-1','FIRM-1','declaration_of_trust','trust_name','Family Trust','Family Trust','v1');
    INSERT INTO intake_workflow_bridge_answers VALUES(2,'INT-1','FIRM-1','declaration_of_trust','trust_type','Revocable living trust','Revocable living trust','v1');
    INSERT INTO intake_workflow_bridge_answers VALUES(3,'INT-1','FIRM-1','declaration_of_trust','trust_purpose','Family continuity','Family continuity','v1');
    INSERT INTO intake_workflow_bridge_answers VALUES(4,'INT-1','FIRM-1','declaration_of_trust','trust_parties','Narrative only','Narrative only','v1');
    INSERT INTO intake_answers VALUES(1,'INT-1','FIRM-1','asset_categories','real_estate','Real estate','v1');
    """)
    connection.commit(); connection.close()
    migrate_intake_trust_bridge(path)
    return path


def confirmed_values(bundle):
    values = {row["target_field"]: row["proposed_value"] or f"confirmed {row['target_field']}" for row in bundle["proposals"]}
    values.update({"jurisdiction": "Virginia", "effective_date": "2026-08-06", "trust_name": "Family Trust"})
    for field, control in FORMATION_FIELD_CONTROLS.items():
        if control.get("choices"):
            values[field] = control["choices"][0][0]
    return values


def test_required_values_controlled_choices_and_review_without_trust_creation(pilot_db):
    bridge = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    bundle = get_bridge(pilot_db, bridge["bridge_id"], "FIRM-1")
    values = confirmed_values(bundle)
    values.pop("workflow_mode")
    with pytest.raises(BridgeError, match="workflow_mode"):
        confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    values = confirmed_values(bundle)
    values["workflow_mode"] = "invented-mode"
    with pytest.raises(BridgeError, match="Invalid controlled formation values: workflow_mode"):
        confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    values = confirmed_values(bundle)
    result = confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    assert result["bridge"]["bridge_status"] == "confirmed"
    assert {row["target_field"]: row["confirmed_value"] for row in result["proposals"]}["workflow_mode"] == "private_office"
    connection = sqlite3.connect(pilot_db)
    assert connection.execute("SELECT COUNT(*) FROM trusts").fetchone()[0] == 0
    connection.close()


def test_eligibility_wrong_status_workflow_and_review_block(pilot_db):
    assert evaluate_eligibility(pilot_db, "FIRM-1", "INT-1")["eligible"]
    assert not evaluate_eligibility(pilot_db, "FIRM-1", "INT-1", "certificate_of_trust")["eligible"]
    connection = sqlite3.connect(pilot_db)
    connection.execute("UPDATE intake_document_recommendations SET status='recommended'"); connection.commit(); connection.close()
    assert not evaluate_eligibility(pilot_db, "FIRM-1", "INT-1")["eligible"]
    connection = sqlite3.connect(pilot_db)
    connection.execute("UPDATE intake_document_recommendations SET status='accepted'")
    connection.execute("INSERT INTO professional_review_issues VALUES(1,'INT-1','FIRM-1','declaration_of_trust','open','major')")
    connection.commit(); connection.close()
    assert not evaluate_eligibility(pilot_db, "FIRM-1", "INT-1")["eligible"]


def test_prepare_is_idempotent_parties_are_not_parsed_and_confirmation_is_explicit(pilot_db):
    first = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    second = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    assert first["bridge_id"] == second["bridge_id"]
    bundle = get_bridge(pilot_db, first["bridge_id"], "FIRM-1")
    grantor = next(row for row in bundle["proposals"] if row["target_field"] == "grantor_name")
    assert grantor["proposed_value"] == ""
    assert grantor["original_source_value"] == "Narrative only"
    with pytest.raises(BridgeError):
        create_or_resume_trust(pilot_db, first["bridge_id"], "FIRM-1", "operator")


def test_deviation_stale_detection_create_resume_collision_and_rollback(pilot_db):
    bridge = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    bundle = get_bridge(pilot_db, bridge["bridge_id"], "FIRM-1")
    values = confirmed_values(bundle)
    values["trust_name"] = "Changed Trust"
    with pytest.raises(BridgeError):
        confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator", {"trust_name": "Operator-confirmed legal name"})
    with pytest.raises(RuntimeError):
        create_or_resume_trust(pilot_db, bridge["bridge_id"], "FIRM-1", "operator", fail_after_insert=True)
    connection = sqlite3.connect(pilot_db)
    assert connection.execute("SELECT COUNT(*) FROM trusts").fetchone()[0] == 0
    first_generated_id = "TR-" + f"{1:03d}"
    connection.execute(
        "INSERT INTO trusts(trust_id,trust_name,firm_id) VALUES(?,?,?)",
        (first_generated_id, "Existing", "FIRM-1"),
    )
    connection.commit(); connection.close()
    created = create_or_resume_trust(pilot_db, bridge["bridge_id"], "FIRM-1", "operator")
    assert created == {"trust_id": "TR-002", "resumed": False}
    assert create_or_resume_trust(pilot_db, bridge["bridge_id"], "FIRM-1", "operator") == {"trust_id": "TR-002", "resumed": True}


def test_stale_recommendation_blocks_confirmation(pilot_db):
    bridge = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    connection = sqlite3.connect(pilot_db)
    connection.execute("UPDATE intake_document_recommendations SET updated_at='v2'"); connection.commit(); connection.close()
    with pytest.raises(BridgeError, match="stale"):
        confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", confirmed_values(get_bridge(pilot_db, bridge["bridge_id"], "FIRM-1")), "operator")


def test_metadata_only_source_rebase_is_firm_scoped_audited_and_confirmation_idempotent(pilot_db):
    bridge = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    values = confirmed_values(get_bridge(pilot_db, bridge["bridge_id"], "FIRM-1"))
    connection = sqlite3.connect(pilot_db)
    connection.execute("UPDATE intake_document_recommendations SET updated_at='v2'")
    connection.commit(); connection.close()
    with pytest.raises(BridgeError, match="stale"):
        confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    with pytest.raises(BridgeError, match="active firm"):
        acknowledge_source_rebase(pilot_db, bridge["bridge_id"], "FIRM-2", "outsider")
    rebased = acknowledge_source_rebase(pilot_db, bridge["bridge_id"], "FIRM-1", "operator")
    assert rebased["bridge"]["bridge_id"] == bridge["bridge_id"]
    assert rebased["bridge"]["bridge_status"] == "prepared"
    assert rebased["bridge"]["source_version"] == "v2"
    rebase_event = [event for event in rebased["events"] if event["event_type"] == "SOURCE_REBASED"]
    assert len(rebase_event) == 1
    assert rebase_event[0]["actor_id"] == "operator"
    assert 'source_fingerprint' in rebase_event[0]["previous_state_json"]
    assert 'source_fingerprint' in rebase_event[0]["new_state_json"]
    confirmed = confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    repeated = confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", values, "operator")
    assert confirmed["bridge"]["bridge_status"] == repeated["bridge"]["bridge_status"] == "confirmed"
    assert len([event for event in repeated["events"] if event["event_type"] == "BRIDGE_CONFIRMED"]) == 1
    assert {row["target_field"]: row["confirmed_value"] for row in repeated["proposals"]} == values
    connection = sqlite3.connect(pilot_db)
    assert connection.execute("SELECT COUNT(*) FROM trusts").fetchone()[0] == 0
    connection.close()


def test_material_source_change_cannot_be_rebased(pilot_db):
    bridge = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    connection = sqlite3.connect(pilot_db)
    connection.execute("UPDATE intake_document_recommendations SET reason='Materially different basis',updated_at='v2'")
    connection.commit(); connection.close()
    with pytest.raises(BridgeError, match="stale"):
        confirm_bridge(pilot_db, bridge["bridge_id"], "FIRM-1", confirmed_values(get_bridge(pilot_db, bridge["bridge_id"], "FIRM-1")), "operator")
    with pytest.raises(BridgeError, match="materially"):
        acknowledge_source_rebase(pilot_db, bridge["bridge_id"], "FIRM-1", "operator")


def test_continuity_subject_is_explicit_secret_rejected_and_profile_independent(pilot_db):
    with pytest.raises(BridgeError):
        create_continuity_profile(pilot_db, "FIRM-1", "", "person", "beneficiary", "continuity", "operator")
    profile_id = create_continuity_profile(pilot_db, "FIRM-1", "Alex Morgan", "person", "account owner", "personal continuity", "operator")
    profile = get_continuity_profile(pilot_db, profile_id, "FIRM-1")
    assert profile["profile"]["subject_name"] == "Alex Morgan"
    assert profile["profile"]["trust_id"] is None
    with pytest.raises(BridgeError, match="(?i)secret"):
        add_continuity_record(pilot_db, "continuity_digital_accounts", profile_id, "FIRM-1", "operator",
                              {"institution_service": "Email", "account_category": "email", "account_label": "Primary", "password": "forbidden"})
    add_continuity_record(pilot_db, "continuity_digital_accounts", profile_id, "FIRM-1", "operator",
                          {"institution_service": "Email", "account_category": "email", "account_label": "Primary", "vault_reference": "Vault item 42"})
    add_continuity_record(pilot_db, "continuity_responsibilities", profile_id, "FIRM-1", "operator",
                          {"category": "household", "description": "Utilities", "current_responsible_party": "Alex", "successor_responsible_party": "Jordan", "authority_source": "Written plan"})
    add_continuity_record(pilot_db, "continuity_receivables", profile_id, "FIRM-1", "operator", {"payer_debtor": "Tenant", "description": "Rent"})
    add_continuity_record(pilot_db, "continuity_payables", profile_id, "FIRM-1", "operator", {"creditor_payee": "Utility", "description": "Power"})
    plan_id = add_continuity_record(pilot_db, "continuity_activation_plans", profile_id, "FIRM-1", "operator",
                                    {"continuity_subject": "Alex Morgan", "triggering_event": "incapacity", "required_evidence": "Documented determination", "authorized_recognizer": "Named professional", "restoration_transfer_closure_procedure": "Review and restore by documented action"})
    transition_activation_plan(pilot_db, plan_id, profile_id, "FIRM-1", "operator", "plan_reviewed", "Operator review")
    assert get_continuity_profile(pilot_db, profile_id, "FIRM-1")["readiness"]["classification"] == "needs_attention"


def test_existing_continuity_profile_can_be_explicitly_linked(pilot_db):
    bridge = prepare_bridge(pilot_db, "FIRM-1", "INT-1", "operator")
    profile_id = create_continuity_profile(pilot_db, "FIRM-1", "Alex", "person", "owner", "continuity", "operator")
    link_continuity_profile(pilot_db, profile_id, bridge["bridge_id"], "FIRM-1", "operator")
    profile = get_continuity_profile(pilot_db, profile_id, "FIRM-1")["profile"]
    assert profile["bridge_id"] == bridge["bridge_id"]
    assert profile["intake_id"] == "INT-1"


def test_same_firm_isolation(pilot_db):
    assert not evaluate_eligibility(pilot_db, "FIRM-2", "INT-1")["eligible"]
    profile_id = create_continuity_profile(pilot_db, "FIRM-1", "Alex", "person", "owner", "continuity", "operator")
    assert get_continuity_profile(pilot_db, profile_id, "FIRM-2") is None


def test_schema_has_no_secret_columns_and_migration_repeats(pilot_db):
    migrate_intake_trust_bridge(pilot_db)
    connection = sqlite3.connect(pilot_db)
    columns = []
    for table in ("continuity_digital_accounts", "continuity_profiles", "intake_trust_formation_field_proposals"):
        columns.extend(row[1].lower() for row in connection.execute(f"PRAGMA table_info({table})"))
    connection.close()
    assert not {"password", "pin", "token", "recovery_code", "secret_answer", "encryption_key"}.intersection(columns)
