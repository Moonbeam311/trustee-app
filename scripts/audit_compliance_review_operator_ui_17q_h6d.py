from audit_compliance_review_h6d_common import run_audit


if __name__ == "__main__":
    raise SystemExit(run_audit("OPERATOR UI AUDIT", {
        "registry and create screens render": lambda out: "'registry_get': 200" in out and "'new_get': 200" in out,
        "detail screen renders controls": lambda out: "'detail_get': 200" in out and "'detail_has_forms': True" in out,
        "operator end-to-end flow reaches closure": lambda out: "'close': 302" in out and "'reopen': 302" in out,
    }))
