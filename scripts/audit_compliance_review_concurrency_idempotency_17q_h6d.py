from audit_compliance_review_h6d_common import run_audit


if __name__ == "__main__":
    raise SystemExit(run_audit("CONCURRENCY IDEMPOTENCY AUDIT", {
        "stale form conflict detected": lambda out: "'stale_update': 409" in out,
        "duplicate workflow does not break audit chain": lambda out: "'audit_chain': True" in out,
        "archived or terminal mutation rejected": lambda out: "'archived_mutation': 302" in out or "'archived_mutation': 409" in out or "'archived_mutation': 400" in out,
        "temporary database was the only changed database": lambda out: "'db_changed': True" in out,
    }))
