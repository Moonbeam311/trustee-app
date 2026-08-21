import sqlite3

import pytest

import database.db as database_db
from database.migrations_successor_acceptance import apply_successor_acceptance_schema
import services.services_successor_acceptance as acceptance_read
import services.services_successor_acceptance_lifecycle as lifecycle


def allow_trust(_trust_id):
    return True


def allow_fiduciary(_fiduciary_id, _trust_id):
    return True


@pytest.fixture()
def lifecycle_database(monkeypatch, tmp_path):
    path = tmp_path / "acceptance-lifecycle.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE trusts (
            trust_id TEXT PRIMARY KEY, trust_name TEXT,
            successor_trustee_name TEXT, firm_id TEXT NOT NULL
        );
        CREATE TABLE fiduciaries (
            fiduciary_id TEXT PRIMARY KEY, full_name TEXT, role_title TEXT,
            authority_scope TEXT, trust_id TEXT, appointment_date TEXT,
            effective_date TEXT, status TEXT, notes TEXT, firm_id TEXT NOT NULL
        );
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY, trust_id TEXT, document_title TEXT,
            firm_id TEXT NOT NULL
        );
        CREATE TABLE app_users (
            user_id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT,
            role_name TEXT, status TEXT, firm_id TEXT, owner_id TEXT
        );
        CREATE TABLE continuity_profiles (
            continuity_profile_id TEXT PRIMARY KEY, firm_id TEXT, trust_id TEXT,
            readiness_status TEXT, status TEXT
        );
        CREATE TABLE continuity_responsibilities (
            responsibility_id TEXT PRIMARY KEY, continuity_profile_id TEXT,
            firm_id TEXT, current_responsible_party TEXT,
            successor_responsible_party TEXT, acceptance_status TEXT
        );
        """
    )
    connection.executemany(
        "INSERT INTO trusts VALUES (?,?,?,?)",
        [
            ("TR-A", "Trust A", "Alex Successor", "FIRM-A"),
            ("TR-B", "Trust B", "Blair Successor", "FIRM-A"),
            ("TR-X", "Trust X", "Xavier Successor", "FIRM-X"),
        ],
    )
    connection.executemany(
        "INSERT INTO fiduciaries VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            ("FID-A", "Alex Successor", "Successor Trustee", "Scope A", "TR-A", None, None, "Appointed", None, "FIRM-A"),
            ("FID-B", "Blair Successor", "Successor Trustee", "Scope B", "TR-B", None, None, "Appointed", None, "FIRM-A"),
            ("FID-X", "Xavier Successor", "Successor Trustee", "Scope X", "TR-X", None, None, "Appointed", None, "FIRM-X"),
        ],
    )
    connection.executemany(
        "INSERT INTO documents VALUES (?,?,?,?)",
        [
            ("DOC-A", "TR-A", "Executed acceptance evidence", "FIRM-A"),
            ("DOC-B", "TR-B", "Other Trust evidence", "FIRM-A"),
            ("DOC-X", "TR-X", "Other firm evidence", "FIRM-X"),
            ("DOC-LEGACY", "TR-A", "Generated legacy acceptance", "FIRM-A"),
        ],
    )
    connection.executemany(
        "INSERT INTO app_users VALUES (?,?,?,?,?,?,?)",
        [
            ("USR-M", "maker", "x", "Admin", "Active", "FIRM-A", None),
            ("USR-R", "reviewer", "x", "Admin", "Active", "FIRM-A", None),
            ("USR-V", "viewer", "x", "Viewer", "Active", "FIRM-A", None),
            ("USR-X", "otherfirm", "x", "Admin", "Active", "FIRM-X", None),
        ],
    )
    connection.execute(
        "INSERT INTO continuity_profiles VALUES (?,?,?,?,?)",
        ("CP-A", "FIRM-A", "TR-A", "needs_review", "draft"),
    )
    connection.execute(
        "INSERT INTO continuity_responsibilities VALUES (?,?,?,?,?,?)",
        ("RESP-A", "CP-A", "FIRM-A", "Current Trustee", "Alex Successor", "designated"),
    )
    connection.commit()
    connection.close()

    active_firm = {"id": "FIRM-A"}
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: active_firm["id"])
    database_db.ensure_role_tables()
    database_db.ensure_user_permission_override_tables()
    apply_successor_acceptance_schema(path)
    return path, active_firm


def propose(
    *,
    trust="TR-A",
    fiduciary="FID-A",
    appointment="APT-A",
    actor="maker",
    target="ACCEPTED_RECORDED",
    evidence="DOC-A",
    external=None,
    capacity="Successor Trustee",
):
    return lifecycle.propose_successor_acceptance(
        trust_id=trust,
        fiduciary_id=fiduciary,
        appointment_reference=appointment,
        role_capacity=capacity,
        appointment_source_reference=f"Instrument:{trust}",
        proposed_status=target,
        maker_actor_id=actor,
        provenance_source="OPERATOR_RECORDED",
        evidence_document_id=evidence,
        external_evidence_reference=external,
        reason="Reported decision",
        trust_authorization_check=allow_trust,
        fiduciary_authorization_check=allow_fiduciary,
        document_authorization_check=allow_trust,
    )


def snapshot_unrelated(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in (
                "trusts", "fiduciaries", "documents", "app_users", "permissions",
                "role_permissions", "user_permission_overrides",
                "continuity_profiles", "continuity_responsibilities",
            )
        }
    finally:
        connection.close()


def events(path, acceptance_id):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM successor_acceptance_events WHERE acceptance_id=? ORDER BY created_at,event_id",
                (acceptance_id,),
            )
        ]
    finally:
        connection.close()


def test_minimum_permissions_and_default_role_mapping(lifecycle_database):
    path, _active_firm = lifecycle_database
    connection = sqlite3.connect(path)
    try:
        permissions = {
            row[0]
            for row in connection.execute(
                "SELECT permission_name FROM permissions WHERE permission_name LIKE '%successor_acceptance'"
            )
        }
        mappings = connection.execute(
            """SELECT role_name, permission_name FROM role_permissions
               WHERE permission_name LIKE '%successor_acceptance' ORDER BY 1,2"""
        ).fetchall()
    finally:
        connection.close()
    assert permissions == {lifecycle.MAKER_PERMISSION, lifecycle.REVIEWER_PERMISSION}
    assert mappings == [
        ("Admin", "record_successor_acceptance"),
        ("Admin", "verify_successor_acceptance"),
    ]


def test_authorized_maker_proposes_and_evidence_attachment_does_not_finalize(lifecycle_database):
    path, _active_firm = lifecycle_database
    result = propose(evidence=None, external=None)
    assert result["created"] is True
    assert result["acceptance_status"] == "PENDING_EVIDENCE"
    attachment = lifecycle.attach_acceptance_evidence(
        result["acceptance_id"], maker_actor_id="maker",
        evidence_document_id="DOC-A", reason="Executed evidence received",
        document_authorization_check=allow_trust,
    )
    assert attachment["finalized"] is False
    record = acceptance_read.get_successor_acceptance(
        result["acceptance_id"], authorization_check=lambda *_: True
    )
    assert record["acceptance_status"] == "PENDING_EVIDENCE"
    assert [event["event_type"] for event in events(path, result["acceptance_id"])] == [
        "TRANSITION_PROPOSED", "EVIDENCE_ATTACHED"
    ]


def test_unauthorized_and_cross_firm_actors_cannot_record(lifecycle_database):
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="permission"):
        propose(actor="viewer")
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="active firm"):
        propose(actor="otherfirm")


def test_independent_reviewer_finalizes_and_same_actor_is_rejected(lifecycle_database):
    result = propose()
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="different actors"):
        lifecycle.review_acceptance_transition(
            result["acceptance_id"], proposal_event_id=result["proposal_event_id"],
            reviewer_actor_id="maker", approve=True, reason="Maker cannot verify",
        )
    reviewed = lifecycle.review_acceptance_transition(
        result["acceptance_id"], proposal_event_id=result["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Evidence verified",
    )
    assert reviewed["prior_status"] == "PENDING_EVIDENCE"
    assert reviewed["acceptance_status"] == "ACCEPTED_RECORDED"


def test_unauthorized_reviewer_and_rejected_review_preserve_state(lifecycle_database):
    path, _active_firm = lifecycle_database
    result = propose()
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="permission"):
        lifecycle.review_acceptance_transition(
            result["acceptance_id"], proposal_event_id=result["proposal_event_id"],
            reviewer_actor_id="viewer", approve=True, reason="Not authorized",
        )
    rejected = lifecycle.review_acceptance_transition(
        result["acceptance_id"], proposal_event_id=result["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=False, reason="Evidence insufficient",
    )
    assert rejected["approved"] is False
    assert rejected["acceptance_status"] == "PENDING_EVIDENCE"
    assert events(path, result["acceptance_id"])[-1]["reviewer_actor_id"] == "reviewer"


def test_decline_withdrawal_and_supersession_require_two_actors_and_preserve_history(lifecycle_database):
    path, _active_firm = lifecycle_database
    declined = propose(target="DECLINED_RECORDED", external="EXT-DECLINE", evidence=None)
    lifecycle.review_acceptance_transition(
        declined["acceptance_id"], proposal_event_id=declined["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Decline evidence verified",
    )
    assert acceptance_read.get_successor_acceptance(
        declined["acceptance_id"], authorization_check=lambda *_: True
    )["acceptance_status"] == "DECLINED_RECORDED"

    accepted = propose(appointment="APT-WITHDRAW")
    lifecycle.review_acceptance_transition(
        accepted["acceptance_id"], proposal_event_id=accepted["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Acceptance verified",
    )
    withdrawal = lifecycle.propose_acceptance_transition(
        accepted["acceptance_id"], proposed_status="WITHDRAWN_RECORDED",
        maker_actor_id="maker", external_evidence_reference="EXT-WITHDRAW",
        reason="Reported withdrawal",
    )
    lifecycle.review_acceptance_transition(
        accepted["acceptance_id"], proposal_event_id=withdrawal["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Withdrawal verified",
    )
    supersession = lifecycle.propose_acceptance_transition(
        accepted["acceptance_id"], proposed_status="SUPERSEDED",
        maker_actor_id="maker", external_evidence_reference="EXT-SUPERSEDE",
        reason="Replacement appointment context recorded",
    )
    lifecycle.review_acceptance_transition(
        accepted["acceptance_id"], proposal_event_id=supersession["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Supersession verified",
    )
    record = acceptance_read.get_successor_acceptance(
        accepted["acceptance_id"], authorization_check=lambda *_: True
    )
    assert record["acceptance_status"] == "SUPERSEDED"
    record_events = events(path, accepted["acceptance_id"])
    assert [event["resulting_state"] for event in record_events if event["event_type"] == "TRANSITION_FINALIZED"] == [
        "ACCEPTED_RECORDED", "WITHDRAWN_RECORDED", "SUPERSEDED"
    ]
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="Invalid"):
        lifecycle.propose_acceptance_transition(
            accepted["acceptance_id"], proposed_status="WITHDRAWN_RECORDED",
            maker_actor_id="maker", external_evidence_reference="EXT-LATE",
            reason="Invalid after supersession",
        )


def test_idempotent_replay_and_distinct_context(lifecycle_database):
    first = propose()
    replay = propose()
    distinct = propose(appointment="APT-DISTINCT")
    assert replay == {
        "created": False,
        "idempotent_replay": True,
        "acceptance_id": first["acceptance_id"],
        "acceptance_status": "PENDING_EVIDENCE",
        "context_fingerprint": first["context_fingerprint"],
    }
    assert distinct["acceptance_id"] != first["acceptance_id"]
    assert distinct["context_fingerprint"] != first["context_fingerprint"]
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="different lifecycle"):
        propose(target="DECLINED_RECORDED")


def test_context_and_evidence_scope_fail_closed(lifecycle_database):
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="scoped"):
        propose(trust="TR-A", fiduciary="FID-B", evidence=None, external="EXT")
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="capacity"):
        propose(capacity="Current Trustee", evidence=None, external="EXT")
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="Document evidence"):
        propose(evidence="DOC-B")
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="Trust context"):
        propose(trust="TR-X", fiduciary="FID-X", evidence=None, external="EXT")


def test_writes_do_not_mutate_related_domains_or_create_access(lifecycle_database):
    path, _active_firm = lifecycle_database
    before = snapshot_unrelated(path)
    result = propose()
    lifecycle.review_acceptance_transition(
        result["acceptance_id"], proposal_event_id=result["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Evidence verified",
    )
    assert snapshot_unrelated(path) == before
    record = acceptance_read.get_successor_acceptance(
        result["acceptance_id"], authorization_check=lambda *_: True
    )
    assert all(value is False for value in record["institutional_effects"].values())


def test_generated_or_legacy_document_alone_never_records_acceptance(lifecycle_database):
    path, _active_firm = lifecycle_database
    connection = sqlite3.connect(path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM successor_acceptances").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 4
    finally:
        connection.close()
    assert acceptance_read.LEGACY_DOCUMENT_CLASSIFICATION == (
        "LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED"
    )
