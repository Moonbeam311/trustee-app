import shutil
import sqlite3
import sys
import os
from pathlib import Path

from audit_compliance_review_temporary_activation_17q_h6c import (
    ROOT,
    DB,
    activate,
    actor,
    base_payload,
    check,
    make_temp_root,
    sha,
    sqlite_counts,
)


def main():
    sys.path.insert(0, str(ROOT))
    results = []
    baseline_sha = sha(DB)
    baseline_counts = sqlite_counts(DB)
    temp_root = make_temp_root()
    print(f"temporary_root={temp_root}")
    try:
        db = temp_root / "workflow.db"
        shutil.copy2(DB, db)
        proc = activate(db)
        check(results, "temporary activation succeeds", proc.returncode == 0, proc.stdout + proc.stderr)
        os.environ["DB_PATH"] = str(db)
        from services.services_compliance_reviews import (
            acknowledge_review_finding,
            add_review_evidence,
            add_review_relationship,
            add_review_subject,
            approve_exception,
            approve_review,
            archive_review,
            assign_remediation,
            assign_reviewer,
            certify_review,
            close_review,
            create_compliance_review,
            issue_review_finding,
            reopen_review,
            request_exception,
            submit_remediation,
            supersede_review,
            update_compliance_review,
            verify_compliance_audit_chain,
            verify_remediation,
            verify_review_evidence,
        )

        admin = actor("admin", {"compliance_admin"}, role="Admin")
        reviewer = actor("reviewer", {"compliance_admin"})
        submitter = actor("submitter", {"submit_remediation", "request_exception"})
        verifier = actor("verifier", {"compliance_admin"})
        approver = actor("approver", {"compliance_admin"})
        certifier = actor("certifier", {"compliance_admin"})

        created = create_compliance_review(payload=base_payload(), actor_context=admin, idempotency_key="h6c-e2e-create")
        check(results, "create draft review", created.get("status") == "created", created)
        review_id = created["review"]["compliance_review_id"]
        check(results, "update draft review", update_compliance_review(compliance_review_id=review_id, payload={"purpose": "Temporary workflow validation", "scope": "Trust administration controls", "review_standard": "Institutional temporary standard", "confidentiality_level": "internal"}, actor_context=admin, authority_basis="H.6C update").get("status") == "updated")
        check(results, "assign reviewer", assign_reviewer(compliance_review_id=review_id, assigned_reviewer="reviewer", actor_context=admin, authority_basis="H.6C assignment").get("status") == "assigned")
        from services.services_compliance_reviews import transition_compliance_review, get_compliance_review
        version = get_compliance_review(review_id, scope={"firm_id": "FIRM-002"})["version"]
        check(results, "open review", transition_compliance_review(compliance_review_id=review_id, action="open", expected_version=version, actor_context=admin, reason="H.6C open", summary="Opened for review.").get("status") == "transitioned")
        check(results, "add secondary subject", add_review_subject(compliance_review_id=review_id, subject_type="matter", subject_id="MAT-H6C", subject_label="Temporary Matter", actor_context=reviewer, authority_basis="H.6C subject").get("status") == "subject_added")
        check(results, "add relationship", add_review_relationship(compliance_review_id=review_id, related_record_type="governance_record", related_record_id="GOV-H6C-2", actor_context=reviewer, authority_basis="H.6C relationship").get("status") == "relationship_added")

        evidence = add_review_evidence(compliance_review_id=review_id, evidence_type="document", source_type="document", source_id="DOC-H6C", source_label="Temporary Policy", description="Policy evidence", relevance="Relevant to trust administration.", actor_context=reviewer, authority_basis="H.6C evidence")
        check(results, "add evidence", evidence.get("status") == "evidence_added", evidence)
        evidence_id = evidence["event"]["compliance_evidence_id"]
        check(results, "self evidence verification rejected", verify_review_evidence(compliance_review_id=review_id, compliance_evidence_id=evidence_id, verification_basis="basis", actor_context=reviewer, authority_basis="H.6C evidence").get("status") == "authorization_denied")
        check(results, "verify evidence", verify_review_evidence(compliance_review_id=review_id, compliance_evidence_id=evidence_id, verification_basis="Hash and source checked.", actor_context=verifier, authority_basis="H.6C verification").get("status") == "evidence_verified")

        finding_ids = []
        for finding_type in ("Compliant", "Observation", "Advisory", "Deficiency", "Material Deficiency", "Documentation Gap", "Evidence Gap", "Procedural Failure", "Authority Failure", "Timing Failure", "Integrity Concern", "Exception", "Not Applicable"):
            finding = issue_review_finding(compliance_review_id=review_id, finding_type=finding_type, title=f"{finding_type} finding", evidence_basis=evidence_id, severity="medium", risk_level="moderate", actor_context=reviewer, authority_basis="H.6C finding")
            check(results, f"issue finding {finding_type}", finding.get("status") == "finding_issued", finding)
            finding_ids.append(finding["event"]["compliance_finding_id"])
        check(results, "acknowledge finding", acknowledge_review_finding(compliance_review_id=review_id, compliance_finding_id=finding_ids[0], actor_context=admin, authority_basis="H.6C acknowledge").get("status") == "acknowledged")
        check(results, "dispute finding retains issuance", acknowledge_review_finding(compliance_review_id=review_id, compliance_finding_id=finding_ids[1], dispute_basis="Temporary dispute", actor_context=admin, authority_basis="H.6C dispute").get("status") == "disputed")

        rem1 = assign_remediation(compliance_review_id=review_id, compliance_finding_id=finding_ids[5], required_action="Upload missing policy evidence.", responsible_party_type="person", responsible_party_id="submitter", responsible_party_label="Submitter", due_date="2026-08-01", actor_context=reviewer, authority_basis="H.6C remediation")
        rem2 = assign_remediation(compliance_review_id=review_id, compliance_finding_id=finding_ids[4], required_action="Document exception rationale.", responsible_party_type="person", responsible_party_id="submitter", responsible_party_label="Submitter", due_date="2026-08-01", actor_context=reviewer, authority_basis="H.6C remediation")
        check(results, "assign multiple remediation actions", rem1.get("status") == "remediation_assigned" and rem2.get("status") == "remediation_assigned")
        rem1_id = rem1["event"]["compliance_remediation_id"]
        rem2_id = rem2["event"]["compliance_remediation_id"]
        check(results, "submit remediation", submit_remediation(compliance_review_id=review_id, compliance_remediation_id=rem1_id, completion_evidence="Submitted evidence.", actor_context=submitter, authority_basis="H.6C submit").get("status") == "remediation_submitted")
        check(results, "self remediation verification rejected", verify_remediation(compliance_review_id=review_id, compliance_remediation_id=rem1_id, actor_context=submitter, authority_basis="H.6C verify").get("status") == "authorization_denied")
        check(results, "reject remediation once", verify_remediation(compliance_review_id=review_id, compliance_remediation_id=rem1_id, verification_result="rejected", actor_context=verifier, authority_basis="H.6C reject").get("status") == "rejected")
        check(results, "resubmit remediation", submit_remediation(compliance_review_id=review_id, compliance_remediation_id=rem1_id, completion_evidence="Corrected evidence.", actor_context=submitter, authority_basis="H.6C resubmit").get("status") == "remediation_submitted")
        check(results, "verify remediation", verify_remediation(compliance_review_id=review_id, compliance_remediation_id=rem1_id, actor_context=verifier, authority_basis="H.6C verify").get("status") == "verified")
        check(results, "request exception", request_exception(compliance_review_id=review_id, compliance_remediation_id=rem2_id, exception_basis="Exception requested for temporary control.", actor_context=submitter, authority_basis="H.6C exception").get("status") == "exception_requested")
        check(results, "approve exception", approve_exception(compliance_review_id=review_id, compliance_remediation_id=rem2_id, actor_context=approver, authority_basis="H.6C exception approval").get("status") == "exception_approved")
        check(results, "creator self approval rejected", approve_review(compliance_review_id=review_id, actor_context=admin, authority_basis="H.6C approval").get("status") == "authorization_denied")
        check(results, "approve review", approve_review(compliance_review_id=review_id, actor_context=approver, authority_basis="H.6C approval").get("status") == "approved")
        check(results, "certify review", certify_review(compliance_review_id=review_id, certification_statement="Temporary review certified.", actor_context=certifier, authority_basis="H.6C certification", effective_date="2026-07-15", expiration_date="2027-07-15").get("status") == "certified")
        check(results, "close review", close_review(compliance_review_id=review_id, actor_context=certifier, authority_basis="H.6C close").get("status") == "transitioned")
        check(results, "reopen requires reason", reopen_review(compliance_review_id=review_id, reason="", actor_context=certifier, authority_basis="H.6C reopen").get("status") == "invalid_input")
        check(results, "reopen review", reopen_review(compliance_review_id=review_id, reason="Temporary follow-up.", actor_context=certifier, authority_basis="H.6C reopen").get("status") == "transitioned")
        amended = issue_review_finding(compliance_review_id=review_id, finding_type="Observation", title="Amended observation", evidence_basis=evidence_id, severity="low", risk_level="low", actor_context=reviewer, authority_basis="H.6C amended finding")
        check(results, "amended finding through governed history", amended.get("status") == "finding_issued", amended)
        check(results, "approve reclosed review", approve_review(compliance_review_id=review_id, actor_context=approver, authority_basis="H.6C reapproval").get("status") == "approved")
        check(results, "recertify review", certify_review(compliance_review_id=review_id, certification_statement="Temporary review recertified.", actor_context=certifier, authority_basis="H.6C recertification").get("status") == "certified")
        check(results, "reclose review", close_review(compliance_review_id=review_id, actor_context=certifier, authority_basis="H.6C reclose").get("status") == "transitioned")
        check(results, "archive review", archive_review(compliance_review_id=review_id, actor_context=certifier, authority_basis="H.6C archive").get("status") == "transitioned")
        check(results, "archived immutability", add_review_evidence(compliance_review_id=review_id, evidence_type="document", source_type="document", source_id="DOC-LATE", actor_context=reviewer, authority_basis="H.6C late").get("status") == "invalid_input")
        check(results, "audit chain verified", verify_compliance_audit_chain(firm_id="FIRM-002").get("status") == "verified")

        successor = create_compliance_review(payload=base_payload(title="Successor Review", source_id="GOV-H6C-S"), actor_context=admin, idempotency_key="h6c-successor")
        superseded = create_compliance_review(payload=base_payload(title="Superseded Review", source_id="GOV-H6C-P"), actor_context=admin, idempotency_key="h6c-superseded")
        check(results, "supersede active review", supersede_review(compliance_review_id=superseded["review"]["compliance_review_id"], successor_review_id=successor["review"]["compliance_review_id"], actor_context=admin, authority_basis="H.6C supersession").get("status") == "superseded")

        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            audit_count = con.execute("SELECT count(*) FROM compliance_review_audit_ledger").fetchone()[0]
            system_objects = con.execute("SELECT name FROM sqlite_master WHERE lower(name) LIKE '%system_observation%'").fetchall()
        finally:
            con.close()
        check(results, "audit ledger populated", audit_count >= 30, audit_count)
        check(results, "no system observation activation", system_objects == [], system_objects)
        check(results, "normal database preserved", sha(DB) == baseline_sha and sqlite_counts(DB) == baseline_counts)
        print("temporary_database_inventory=" + repr([(db.name, db.stat().st_size, sha(db))]))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))
    print("POST-V2-17Q-H.6C SERVICE WORKFLOW AUDIT")
    if not all(results):
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
