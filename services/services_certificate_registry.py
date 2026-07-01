from datetime import datetime
from database.db import get_connection, ensure_certificate_type_registry_table


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _next_type_id():
    ensure_certificate_type_registry_table()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) AS count FROM certificate_type_registry").fetchone()
    conn.close()
    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CTYPE-{count + 1:06d}"


def list_certificate_types(active_only=False):
    ensure_certificate_type_registry_table()
    conn = get_connection()
    cur = conn.cursor()

    if active_only:
        rows = cur.execute("""
            SELECT *
            FROM certificate_type_registry
            WHERE active = 1
            ORDER BY display_name ASC
        """).fetchall()
    else:
        rows = cur.execute("""
            SELECT *
            FROM certificate_type_registry
            ORDER BY display_name ASC
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_certificate_type(certificate_type):
    ensure_certificate_type_registry_table()
    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT *
        FROM certificate_type_registry
        WHERE certificate_type = ?
    """, (certificate_type,)).fetchone()

    conn.close()
    return dict(row) if row else None


def certificate_type_exists(certificate_type):
    return get_certificate_type(certificate_type) is not None


def register_certificate_type(
    certificate_type,
    display_name,
    module_name=None,
    verification_engine=None,
    pdf_builder=None,
    detail_template=None,
    supports_lifecycle=1,
    supports_timeline=1,
    supports_chain=0,
    supports_pdf=1,
    supports_packet=0,
    supports_supersession=0,
    supports_relationships=0,
    supports_provenance=1,
    governance_policy="Immutable",
    retention_policy="Permanent",
    active=1,
    notes=None,
):
    ensure_certificate_type_registry_table()

    existing = get_certificate_type(certificate_type)
    if existing:
        return existing

    type_id = _next_type_id()
    now = _now()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO certificate_type_registry (
            type_id,
            certificate_type,
            display_name,
            module_name,
            verification_engine,
            pdf_builder,
            detail_template,
            supports_lifecycle,
            supports_timeline,
            supports_chain,
            supports_pdf,
            supports_packet,
            supports_supersession,
            supports_relationships,
            supports_provenance,
            governance_policy,
            retention_policy,
            active,
            notes,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        type_id,
        certificate_type,
        display_name,
        module_name,
        verification_engine,
        pdf_builder,
        detail_template,
        int(bool(supports_lifecycle)),
        int(bool(supports_timeline)),
        int(bool(supports_chain)),
        int(bool(supports_pdf)),
        int(bool(supports_packet)),
        int(bool(supports_supersession)),
        int(bool(supports_relationships)),
        int(bool(supports_provenance)),
        governance_policy,
        retention_policy,
        int(bool(active)),
        notes,
        now,
        now,
    ))

    conn.commit()
    conn.close()

    return get_certificate_type(certificate_type)


def update_certificate_type(certificate_type, **fields):
    ensure_certificate_type_registry_table()

    allowed = {
        "display_name",
        "module_name",
        "verification_engine",
        "pdf_builder",
        "detail_template",
        "supports_lifecycle",
        "supports_timeline",
        "supports_chain",
        "supports_pdf",
        "supports_packet",
        "supports_supersession",
        "supports_relationships",
        "supports_provenance",
        "governance_policy",
        "retention_policy",
        "active",
        "notes",
    }

    updates = []
    params = []

    for key, value in fields.items():
        if key not in allowed:
            continue

        if key.startswith("supports_") or key == "active":
            value = int(bool(value))

        updates.append(f"{key} = ?")
        params.append(value)

    if not updates:
        return get_certificate_type(certificate_type)

    updates.append("updated_at = ?")
    params.append(_now())
    params.append(certificate_type)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE certificate_type_registry
        SET {", ".join(updates)}
        WHERE certificate_type = ?
    """, params)

    conn.commit()
    conn.close()

    return get_certificate_type(certificate_type)


def seed_certificate_type_registry():
    ensure_certificate_type_registry_table()

    definitions = [
        {
            "certificate_type": "Continuity",
            "display_name": "Institutional Continuity Certificate",
            "module_name": "Execution Continuity",
            "verification_engine": "Institutional Certification Verification Engine",
            "pdf_builder": "continuity_certificate_pdf",
            "detail_template": "continuity_certificate_detail.html",
            "supports_chain": 1,
            "supports_packet": 1,
            "supports_supersession": 1,
            "supports_relationships": 1,
            "notes": "Mature ICP-4 continuity certificate implementation.",
        },
        {
            "certificate_type": "Trust Minute",
            "display_name": "Trust Minute Certificate",
            "module_name": "Trust Minutes",
            "verification_engine": "Trust Minute Verification Engine",
            "pdf_builder": "trust_minute_certificate_pdf",
            "detail_template": "trust_minute_detail.html",
            "supports_chain": 0,
            "supports_packet": 1,
            "supports_supersession": 0,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Transfer",
            "display_name": "Transfer Certificate",
            "module_name": "Execution Transfers",
            "verification_engine": "Transfer Verification Engine",
            "pdf_builder": "transfer_certificate_pdf",
            "supports_packet": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Archive",
            "display_name": "Archive Certificate",
            "module_name": "Archive",
            "verification_engine": "Archive Verification Engine",
            "supports_chain": 1,
            "supports_packet": 1,
            "supports_supersession": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Funding",
            "display_name": "Funding Certificate",
            "module_name": "Funding",
            "verification_engine": "Funding Verification Engine",
            "supports_packet": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Governance",
            "display_name": "Governance Certificate",
            "module_name": "Governance",
            "verification_engine": "Governance Verification Engine",
            "supports_chain": 1,
            "supports_packet": 1,
            "supports_supersession": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Compliance",
            "display_name": "Compliance Certificate",
            "module_name": "Compliance",
            "verification_engine": "Compliance Verification Engine",
            "supports_chain": 1,
            "supports_packet": 1,
            "supports_supersession": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Certificate of Trust",
            "display_name": "Certificate of Trust",
            "module_name": "Trust Output",
            "verification_engine": "Trust Output Verification Engine",
            "supports_packet": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Property",
            "display_name": "Property Archive Certificate",
            "module_name": "Property / Archive",
            "verification_engine": "Property Archive Verification Engine",
            "supports_packet": 1,
            "supports_relationships": 1,
        },
        {
            "certificate_type": "Institution",
            "display_name": "Institutional Certificate",
            "module_name": "Institution",
            "verification_engine": "Institutional Verification Engine",
            "supports_chain": 1,
            "supports_packet": 1,
            "supports_supersession": 1,
            "supports_relationships": 1,
        },
    ]

    seeded = []
    for item in definitions:
        seeded.append(register_certificate_type(**item))

    return seeded
