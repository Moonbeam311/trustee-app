from datetime import datetime
from database.db import get_connection, ensure_certificate_governance_policies_table


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _next_policy_id():
    ensure_certificate_governance_policies_table()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) AS count FROM certificate_governance_policies").fetchone()
    conn.close()
    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CPOL-{count + 1:06d}"


def register_certificate_policy(
    policy_name,
    display_name,
    policy_category=None,
    description=None,
    allows_edit=0,
    allows_delete=0,
    allows_supersession=1,
    allows_revocation=0,
    requires_lifecycle_event=1,
    requires_reason=1,
    requires_authority=1,
    retention_rule="Permanent",
    active=1,
):
    ensure_certificate_governance_policies_table()

    existing = get_certificate_policy(policy_name)
    if existing:
        return existing

    policy_id = _next_policy_id()
    now = _now()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO certificate_governance_policies (
            policy_id,
            policy_name,
            display_name,
            policy_category,
            description,
            allows_edit,
            allows_delete,
            allows_supersession,
            allows_revocation,
            requires_lifecycle_event,
            requires_reason,
            requires_authority,
            retention_rule,
            active,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        policy_id,
        policy_name,
        display_name,
        policy_category,
        description,
        int(bool(allows_edit)),
        int(bool(allows_delete)),
        int(bool(allows_supersession)),
        int(bool(allows_revocation)),
        int(bool(requires_lifecycle_event)),
        int(bool(requires_reason)),
        int(bool(requires_authority)),
        retention_rule,
        int(bool(active)),
        now,
        now,
    ))

    conn.commit()
    conn.close()

    return get_certificate_policy(policy_name)


def get_certificate_policy(policy_name):
    ensure_certificate_governance_policies_table()

    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT *
        FROM certificate_governance_policies
        WHERE policy_name = ?
    """, (policy_name,)).fetchone()

    conn.close()
    return dict(row) if row else None


def list_certificate_policies(active_only=False):
    ensure_certificate_governance_policies_table()

    conn = get_connection()
    cur = conn.cursor()

    if active_only:
        rows = cur.execute("""
            SELECT *
            FROM certificate_governance_policies
            WHERE active = 1
            ORDER BY policy_category ASC, display_name ASC
        """).fetchall()
    else:
        rows = cur.execute("""
            SELECT *
            FROM certificate_governance_policies
            ORDER BY policy_category ASC, display_name ASC
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def seed_certificate_governance_policies():
    definitions = [
        {
            "policy_name": "Immutable",
            "display_name": "Immutable Certificate",
            "policy_category": "Core",
            "description": "Certificate cannot be edited or deleted after issuance. Later changes require a successor certificate.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 0,
            "retention_rule": "Permanent",
        },
        {
            "policy_name": "Append Only",
            "display_name": "Append-Only Certificate",
            "policy_category": "Core",
            "description": "Certificate content remains fixed; lifecycle events may be appended.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 0,
            "retention_rule": "Permanent",
        },
        {
            "policy_name": "Supersedable",
            "display_name": "Supersedable Certificate",
            "policy_category": "Lifecycle",
            "description": "Certificate may be replaced by a successor while preserving the prior record.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 0,
            "retention_rule": "Permanent Historical",
        },
        {
            "policy_name": "Revocable",
            "display_name": "Revocable Certificate",
            "policy_category": "Lifecycle",
            "description": "Certificate may be marked revoked by authorized governance action.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 1,
            "retention_rule": "Permanent Historical",
        },
        {
            "policy_name": "Historical",
            "display_name": "Historical Certificate",
            "policy_category": "Retention",
            "description": "Certificate remains preserved as historical evidence and should not be treated as current.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 0,
            "allows_revocation": 0,
            "retention_rule": "Permanent Historical",
        },
        {
            "policy_name": "Evidence Only",
            "display_name": "Evidence-Only Certificate",
            "policy_category": "Use",
            "description": "Certificate is evidentiary and does not independently authorize action.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 0,
            "retention_rule": "Permanent",
        },
        {
            "policy_name": "Private",
            "display_name": "Private Certificate",
            "policy_category": "Visibility",
            "description": "Certificate is internal/private and should not be publicly exposed without authorization.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 0,
            "retention_rule": "Permanent",
        },
        {
            "policy_name": "Public",
            "display_name": "Public Certificate",
            "policy_category": "Visibility",
            "description": "Certificate may be shared externally when properly verified and authorized.",
            "allows_edit": 0,
            "allows_delete": 0,
            "allows_supersession": 1,
            "allows_revocation": 0,
            "retention_rule": "Permanent",
        },
    ]

    seeded = []
    for item in definitions:
        seeded.append(register_certificate_policy(**item))

    return seeded


def get_certificate_type_policy(certificate_type_definition):
    """
    Resolves the governance policy attached to a certificate type definition.
    """
    policy_name = None

    if certificate_type_definition:
        policy_name = certificate_type_definition.get("governance_policy")

    if not policy_name:
        policy_name = "Immutable"

    return get_certificate_policy(policy_name)
