from datetime import datetime
from database.db import get_connection, ensure_certificate_templates_table


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _next_template_id():
    ensure_certificate_templates_table()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) AS count FROM certificate_templates").fetchone()
    conn.close()
    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CTPL-{count + 1:06d}"


def get_certificate_template(template_name):
    ensure_certificate_templates_table()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("""
        SELECT *
        FROM certificate_templates
        WHERE template_name = ?
    """, (template_name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def register_certificate_template(
    template_name,
    display_name,
    template_category=None,
    description=None,
    layout_engine="Unified PDF Builder",
    page_size="Letter",
    supports_seal=1,
    supports_signature=1,
    supports_qr=1,
    supports_watermark=1,
    supports_packet_cover=1,
    default_for_type=None,
    active=1,
):
    ensure_certificate_templates_table()

    existing = get_certificate_template(template_name)
    if existing:
        return existing

    template_id = _next_template_id()
    now = _now()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO certificate_templates (
            template_id,
            template_name,
            display_name,
            template_category,
            description,
            layout_engine,
            page_size,
            supports_seal,
            supports_signature,
            supports_qr,
            supports_watermark,
            supports_packet_cover,
            default_for_type,
            active,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        template_id,
        template_name,
        display_name,
        template_category,
        description,
        layout_engine,
        page_size,
        int(bool(supports_seal)),
        int(bool(supports_signature)),
        int(bool(supports_qr)),
        int(bool(supports_watermark)),
        int(bool(supports_packet_cover)),
        default_for_type,
        int(bool(active)),
        now,
        now,
    ))

    conn.commit()
    conn.close()

    return get_certificate_template(template_name)


def list_certificate_templates(active_only=False):
    ensure_certificate_templates_table()
    conn = get_connection()
    cur = conn.cursor()

    if active_only:
        rows = cur.execute("""
            SELECT *
            FROM certificate_templates
            WHERE active = 1
            ORDER BY template_category ASC, display_name ASC
        """).fetchall()
    else:
        rows = cur.execute("""
            SELECT *
            FROM certificate_templates
            ORDER BY template_category ASC, display_name ASC
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def seed_certificate_templates():
    templates = [
        {
            "template_name": "institutional_standard",
            "display_name": "Institutional Standard Certificate",
            "template_category": "Core",
            "description": "Default institutional certificate layout with governance banner, verification notice, hash evidence, seal, QR placeholder, and signature block.",
            "layout_engine": "Unified PDF Builder",
            "default_for_type": "Continuity",
        },
        {
            "template_name": "historical_superseded",
            "display_name": "Historical Superseded Certificate",
            "template_category": "Lifecycle",
            "description": "Layout for superseded certificates with historical record disclosure and no-current-use warning.",
            "layout_engine": "Unified PDF Builder",
        },
        {
            "template_name": "packet_cover",
            "display_name": "Evidence Packet Cover",
            "template_category": "Packet",
            "description": "Cover sheet template for institutional evidence packets.",
            "layout_engine": "Packet Engine",
        },
        {
            "template_name": "public_verification",
            "display_name": "Public Verification Certificate",
            "template_category": "Verification",
            "description": "Externally shareable verification layout for public-facing certificate confirmations.",
            "layout_engine": "Unified PDF Builder",
            "supports_signature": 0,
            "supports_watermark": 0,
        },
        {
            "template_name": "private_internal",
            "display_name": "Private Internal Certificate",
            "template_category": "Visibility",
            "description": "Internal/private certificate layout for firm or trustee-only review.",
            "layout_engine": "Unified PDF Builder",
        },
    ]

    return [register_certificate_template(**tpl) for tpl in templates]


def resolve_template_for_certificate_object(certificate_object):
    cert_type = certificate_object.get("identity", {}).get("certificate_type")

    for tpl in list_certificate_templates(active_only=True):
        if tpl.get("default_for_type") == cert_type:
            return tpl

    return get_certificate_template("institutional_standard")
