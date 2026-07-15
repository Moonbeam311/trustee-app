from audit_compliance_review_h6d_common import run_audit


if __name__ == "__main__":
    raise SystemExit(run_audit("WRITE ROUTES AUDIT", {
        "all material write routes exercised": lambda out: all(
            token in out for token in (
                "'valid_create': 201", "'valid_update': 302", "'assign': 302",
                "'open': 302", "'add_subject': 302", "'add_relationship': 302",
                "'add_evidence': 302", "'verify_evidence': 302",
                "'issue_finding': 302", "'assign_remediation': 302",
                "'submit_remediation': 302", "'verify_remediation': 302",
                "'approve': 302", "'certify': 302", "'close': 302",
                "'reopen': 302", "'supersede': 302",
            )
        ),
        "normal unavailable and missing paths bounded": lambda out: "'missing_csrf': 400" in out and "'invalid_create': 400" in out,
    }))
