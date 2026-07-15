import os
import shutil
import sqlite3
import sys

from audit_compliance_review_temporary_activation_17q_h6c import (
    ROOT,
    DB,
    activate,
    actor,
    base_payload,
    check,
    copy_normal,
    make_temp_root,
    run,
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
        db = copy_normal(temp_root, "auth.db")
        check(results, "temporary activation", activate(db).returncode == 0)
        os.environ["DB_PATH"] = str(db)
        from services.services_compliance_reviews import (
            add_review_evidence,
            approve_exception,
            approve_review,
            assign_remediation,
            close_review,
            create_compliance_review,
            generate_compliance_evidence_id,
            generate_compliance_finding_id,
            generate_compliance_remediation_id,
            issue_review_finding,
            reopen_review,
            transition_compliance_review,
            verify_remediation,
            verify_review_evidence,
        )

        admin = actor("admin", {"compliance_admin"}, role="Admin")
        unauthorized = actor("unauthorized", set())
        wrong_firm = actor("wrong", {"compliance_admin"}, firm_id="FIRM-003")
        reviewer = actor("reviewer", {"compliance_admin"})
        verifier = actor("verifier", {"compliance_admin"})

        missing_authority = create_compliance_review(
            payload=base_payload(authority_basis=""),
            actor_context=actor("limited", {"create_review"}),
            idempotency_key="missing-authority",
        )
        check(results, "missing authority basis rejected", missing_authority.get("status") == "invalid_input", missing_authority)
        invalid_type = create_compliance_review(
            payload=base_payload(review_type="invalid_type"),
            actor_context=admin,
            idempotency_key="invalid-type",
        )
        check(results, "invalid review type rejected", invalid_type.get("status") == "invalid_input", invalid_type)
        cross_firm_create = create_compliance_review(
            payload=base_payload(firm_id="FIRM-002"),
            actor_context=wrong_firm,
            idempotency_key="cross-firm-create",
        )
        check(results, "cross-firm create rejected", cross_firm_create.get("status") == "invalid_input", cross_firm_create)
        no_auth_create = create_compliance_review(
            payload=base_payload(source_id="NOAUTH"),
            actor_context=unauthorized,
            idempotency_key="no-auth-create",
        )
        check(results, "unauthorized create rejected", no_auth_create.get("status") == "authorization_denied", no_auth_create)

        created = create_compliance_review(payload=base_payload(), actor_context=admin, idempotency_key="auth-created")
        rid = created["review"]["compliance_review_id"]
        check(results, "authorized create succeeds", created.get("status") == "created", created)
        invalid_transition = transition_compliance_review(
            compliance_review_id=rid,
            action="certify",
            expected_version=1,
            actor_context=admin,
            reason="invalid",
            summary="invalid",
        )
        check(results, "invalid lifecycle transition rejected", invalid_transition.get("status") == "invalid_transition", invalid_transition)
        wrong_firm_read_mutation = add_review_evidence(
            compliance_review_id=rid,
            evidence_type="document",
            source_type="document",
            source_id="DOC-WRONG",
            actor_context=wrong_firm,
            authority_basis="wrong firm",
        )
        check(results, "wrong-firm mutation rejected", wrong_firm_read_mutation.get("status") == "authorization_denied", wrong_firm_read_mutation)
        missing_basis_finding = issue_review_finding(
            compliance_review_id=rid,
            finding_type="Evidence Gap",
            title="No basis",
            evidence_basis="",
            actor_context=reviewer,
            authority_basis="finding",
        )
        check(results, "missing evidence basis rejected", missing_basis_finding.get("status") == "invalid_input", missing_basis_finding)

        evidence = add_review_evidence(compliance_review_id=rid, evidence_type="document", source_type="document", source_id="DOC", actor_context=admin, authority_basis="evidence")
        eid = evidence["event"]["compliance_evidence_id"]
        check(results, "self evidence verification conflict", verify_review_evidence(compliance_review_id=rid, compliance_evidence_id=eid, verification_basis="basis", actor_context=admin, authority_basis="verify").get("status") == "authorization_denied")
        check(results, "authorized evidence verification", verify_review_evidence(compliance_review_id=rid, compliance_evidence_id=eid, verification_basis="basis", actor_context=verifier, authority_basis="verify").get("status") == "evidence_verified")
        finding = issue_review_finding(compliance_review_id=rid, finding_type="Material Deficiency", title="Deficiency", evidence_basis=eid, actor_context=reviewer, authority_basis="finding")
        fid = finding["event"]["compliance_finding_id"]
        rem = assign_remediation(compliance_review_id=rid, compliance_finding_id=fid, required_action="Fix it", responsible_party_type="person", actor_context=reviewer, authority_basis="remediation")
        remid = rem["event"]["compliance_remediation_id"]
        check(results, "remediation verification without evidence rejected", verify_remediation(compliance_review_id=rid, compliance_remediation_id=remid, actor_context=verifier, authority_basis="verify").get("status") == "invalid_input")
        check(results, "closure with open remediation rejected", close_review(compliance_review_id=rid, actor_context=admin, authority_basis="close").get("status") == "invalid_transition")
        check(results, "self exception approval rejected", approve_exception(compliance_review_id=rid, compliance_remediation_id=remid, actor_context=reviewer, authority_basis="exception").get("status") in {"authorization_denied", "invalid_input"})
        check(results, "self approval rejected", approve_review(compliance_review_id=rid, actor_context=admin, authority_basis="approval").get("status") == "authorization_denied")
        check(results, "reopen without reason rejected", reopen_review(compliance_review_id=rid, reason="", actor_context=admin, authority_basis="reopen").get("status") == "invalid_input")

        ids = set()
        for generator in (generate_compliance_evidence_id, generate_compliance_finding_id, generate_compliance_remediation_id):
            value = generator()
            check(results, f"identifier generated {value[:3]}", value not in ids and "-" in value, value)
            ids.add(value)
        con = sqlite3.connect(db)
        try:
            con.execute("INSERT INTO compliance_review_evidence (compliance_evidence_id, compliance_review_id, evidence_type, source_type, added_by, added_at) VALUES (?, ?, 'document', 'document', 'tester', 'now')", (eid, rid))
            con.commit()
            duplicate_blocked = False
        except sqlite3.IntegrityError:
            duplicate_blocked = True
        finally:
            con.close()
        check(results, "duplicate identifier blocked", duplicate_blocked)

        partial = copy_normal(temp_root, "partial.db")
        con = sqlite3.connect(partial)
        con.execute("CREATE TABLE compliance_reviews (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()
        partial_proc = activate(partial)
        check(results, "partial schema refused", partial_proc.returncode != 0 and "partial_schema_conflict" in partial_proc.stdout, partial_proc.stdout + partial_proc.stderr)
        check(results, "normal database preserved", sha(DB) == baseline_sha and sqlite_counts(DB) == baseline_counts)
        print("temporary_database_inventory=" + repr([(p.name, p.stat().st_size, sha(p)) for p in sorted(temp_root.glob("*.db"))]))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))
    print("POST-V2-17Q-H.6C LIFECYCLE AUTHORIZATION AUDIT")
    if not all(results):
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
