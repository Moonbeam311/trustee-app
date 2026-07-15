from audit_compliance_review_h6d_common import run_audit


if __name__ == "__main__":
    raise SystemExit(run_audit("ROUTE AUTHORIZATION AUDIT", {
        "unauthorized create blocked": lambda out: "'invalid_create': 400" in out and "'valid_create': 201" in out,
        "wrong-firm detail concealed": lambda out: "'wrong_firm': 404" in out or "'wrong_firm': 403" in out,
        "maker checker conflicts blocked": lambda out: "'self_evidence_verify': 403" in out and "'self_remediation_verify': 403" in out,
        "normal route authorization remains service-owned": lambda out: "'audit_chain': True" in out,
    }))
