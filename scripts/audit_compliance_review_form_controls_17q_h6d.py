from audit_compliance_review_h6d_common import run_audit


if __name__ == "__main__":
    raise SystemExit(run_audit("FORM CONTROLS AUDIT", {
        "create form includes csrf": lambda out: "'create_has_csrf': True" in out,
        "detail forms include version and confirmation controls": lambda out: "'detail_has_forms': True" in out,
        "missing csrf and confirmation fail closed": lambda out: "'missing_csrf': 400" in out and "'missing_confirm_approval': 400" in out,
        "stale update is rejected": lambda out: "'stale_update': 409" in out,
    }))
