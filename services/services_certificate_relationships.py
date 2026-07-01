from datetime import datetime
from database.db import get_connection, ensure_certificate_relationships_table


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _next_relationship_id():
    ensure_certificate_relationships_table()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) AS count FROM certificate_relationships").fetchone()
    conn.close()
    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CREL-{count + 1:06d}"


def create_certificate_relationship(
    certification_id,
    certificate_type,
    related_object_type,
    related_object_id,
    relationship_type="governs",
    relationship_label=None,
    relationship_basis=None,
    created_by="system",
):
    ensure_certificate_relationships_table()

    conn = get_connection()
    cur = conn.cursor()

    existing = cur.execute("""
        SELECT *
        FROM certificate_relationships
        WHERE certification_id = ?
          AND related_object_type = ?
          AND related_object_id = ?
          AND relationship_type = ?
    """, (
        certification_id,
        related_object_type,
        related_object_id,
        relationship_type,
    )).fetchone()

    if existing:
        conn.close()
        return dict(existing)

    relationship_id = _next_relationship_id()
    now = _now()

    cur.execute("""
        INSERT INTO certificate_relationships (
            relationship_id,
            certification_id,
            certificate_type,
            related_object_type,
            related_object_id,
            relationship_type,
            relationship_label,
            relationship_basis,
            relationship_status,
            created_by,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
    """, (
        relationship_id,
        certification_id,
        certificate_type,
        related_object_type,
        related_object_id,
        relationship_type,
        relationship_label,
        relationship_basis,
        created_by,
        now,
        now,
    ))

    conn.commit()

    row = cur.execute("""
        SELECT *
        FROM certificate_relationships
        WHERE relationship_id = ?
    """, (relationship_id,)).fetchone()

    conn.close()
    return dict(row) if row else None


def list_certificate_relationships(certification_id):
    ensure_certificate_relationships_table()

    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT *
        FROM certificate_relationships
        WHERE certification_id = ?
        ORDER BY related_object_type ASC, related_object_id ASC
    """, (certification_id,)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def list_all_certificate_relationships():
    ensure_certificate_relationships_table()

    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT *
        FROM certificate_relationships
        ORDER BY certification_id ASC, related_object_type ASC
    """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def backfill_continuity_certificate_relationships(actor="system"):
    """
    ICP-5G:
    Seed relationships for existing continuity certificates.
    """
    from services.services_certifications import list_institutional_certifications

    created = []

    for cert in list_institutional_certifications(certificate_type="Continuity"):
        cert_id = cert.get("certification_id")
        execution_id = cert.get("execution_id")

        if execution_id:
            created.append(create_certificate_relationship(
                certification_id=cert_id,
                certificate_type="Continuity",
                related_object_type="execution_session",
                related_object_id=execution_id,
                relationship_type="certifies",
                relationship_label=f"Continuity certification for {execution_id}",
                relationship_basis="Continuity certificate was generated from the execution session continuity dashboard.",
                created_by=actor,
            ))

        validation_id = cert.get("validation_id")
        if validation_id:
            created.append(create_certificate_relationship(
                certification_id=cert_id,
                certificate_type="Continuity",
                related_object_type="validation_record",
                related_object_id=validation_id,
                relationship_type="validates",
                relationship_label=f"Validation record {validation_id}",
                relationship_basis="Certificate references expected and observed hash validation records.",
                created_by=actor,
            ))

        created.append(create_certificate_relationship(
            certification_id=cert_id,
            certificate_type="Continuity",
            related_object_type="institution",
            related_object_id="IOS",
            relationship_type="issued_by",
            relationship_label="Institutional Operating System",
            relationship_basis="Certificate issued by the Institutional Operating System framework.",
            created_by=actor,
        ))

    return created
