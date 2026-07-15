import os
import shutil
import sqlite3
import sys

from audit_compliance_review_temporary_activation_17q_h6c import (
    DB,
    activate,
    actor,
    base_payload,
    check,
    copy_normal,
    make_temp_root,
    sha,
    sqlite_counts,
)


def main():
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    results = []
    baseline_sha = sha(DB)
    baseline_counts = sqlite_counts(DB)
    temp_root = make_temp_root()
    print(f"temporary_root={temp_root}")
    try:
        db = copy_normal(temp_root, "audit.db")
        check(results, "temporary activation", activate(db).returncode == 0)
        os.environ["DB_PATH"] = str(db)
        from services.services_compliance_reviews import (
            add_review_evidence,
            append_compliance_audit_entry,
            approve_review,
            assign_reviewer,
            certify_review,
            close_review,
            create_compliance_review,
            issue_review_finding,
            list_compliance_audit_entries,
            transition_compliance_review,
            verify_compliance_audit_chain,
            verify_review_evidence,
        )
        admin = actor("admin", {"compliance_admin"}, role="Admin")
        reviewer = actor("reviewer", {"compliance_admin"})
        verifier = actor("verifier", {"compliance_admin"})
        certifier = actor("certifier", {"compliance_admin"})

        created = create_compliance_review(payload=base_payload(), actor_context=admin, idempotency_key="audit-create")
        rid = created["review"]["compliance_review_id"]
        assign_reviewer(compliance_review_id=rid, assigned_reviewer="reviewer", actor_context=admin, authority_basis="audit")
        transition_compliance_review(compliance_review_id=rid, action="open", expected_version=2, actor_context=admin, reason="audit", summary="open")
        evidence = add_review_evidence(compliance_review_id=rid, evidence_type="document", source_type="document", source_id="DOC-AUDIT", description="bounded note", actor_context=admin, authority_basis="audit")
        verify_review_evidence(compliance_review_id=rid, compliance_evidence_id=evidence["event"]["compliance_evidence_id"], verification_basis="hash checked", actor_context=verifier, authority_basis="audit")
        issue_review_finding(compliance_review_id=rid, finding_type="Observation", title="Audit observation", evidence_basis=evidence["event"]["compliance_evidence_id"], actor_context=reviewer, authority_basis="audit")
        approve_review(compliance_review_id=rid, actor_context=verifier, authority_basis="audit")
        certify_review(compliance_review_id=rid, certification_statement="Audit cert", actor_context=certifier, authority_basis="audit")
        close_review(compliance_review_id=rid, actor_context=certifier, authority_basis="audit")
        append_compliance_audit_entry(compliance_review_id=rid, entity_type="compliance_review", entity_id=rid, action="unauthorized_action_attempted", actor_context=admin, authority_basis="audit", note="Unauthorized attempt recorded without sensitive body.")
        transition_compliance_review(compliance_review_id=rid, action="certify", expected_version=999, actor_context=admin, reason="audit", summary="invalid")

        entries = list_compliance_audit_entries(rid, scope={"firm_id": "FIRM-002"})
        actions = {entry["action"] for entry in entries}
        required = {
            "review_created",
            "reviewer_assigned",
            "compliance_review_opened",
            "evidence_added",
            "evidence_verified",
            "finding_issued",
            "approval_granted",
            "certification_issued",
            "compliance_review_closed",
            "unauthorized_action_attempted",
        }
        check(results, "required audit events present", required <= actions, sorted(actions))
        check(results, "audit chain verified", verify_compliance_audit_chain(firm_id="FIRM-002").get("status") == "verified")
        check(results, "no sensitive note material", not any("password" in (entry.get("note") or "").lower() or "token" in (entry.get("note") or "").lower() for entry in entries))
        check(results, "chronological ordering", [entry["id"] for entry in entries] == sorted(entry["id"] for entry in entries))

        con = sqlite3.connect(db)
        try:
            first = con.execute("SELECT id, note FROM compliance_review_audit_ledger ORDER BY id LIMIT 1").fetchone()
            con.execute("UPDATE compliance_review_audit_ledger SET note = ? WHERE id = ?", ("tampered", first[0]))
            con.commit()
        finally:
            con.close()
        check(results, "audit tampering detected", verify_compliance_audit_chain(firm_id="FIRM-002").get("status") == "entry_hash_mismatch")
        check(results, "normal database preserved", sha(DB) == baseline_sha and sqlite_counts(DB) == baseline_counts)
        print("temporary_database_inventory=" + repr([(db.name, db.stat().st_size, sha(db))]))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))
    print("POST-V2-17Q-H.6C AUDIT LEDGER AUDIT")
    if not all(results):
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
