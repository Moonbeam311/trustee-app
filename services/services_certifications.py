from database.db import get_connection, ensure_institutional_certifications_table, ensure_certificate_lifecycle_events_table
from datetime import datetime
import hashlib
import json


def _next_certification_id():
    ensure_institutional_certifications_table()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT COUNT(*) AS count FROM institutional_certifications"
    ).fetchone()
    conn.close()

    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CERT-{count + 1:06d}"


def calculate_certificate_hash(payload):
    """
    ICP-3B:
    Deterministic tamper-evident hash for certification payload.
    """
    normalized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def create_institutional_certification(data):
    """
    General immutable certification creator.
    Used first by continuity certification.
    """
    ensure_institutional_certifications_table()

    certification_id = data.get("certification_id") or _next_certification_id()
    certified_at = data.get("certified_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    hash_payload = {
        "certification_id": certification_id,
        "certificate_type": data.get("certificate_type"),
        "execution_id": data.get("execution_id"),
        "continuity_score": data.get("continuity_score"),
        "certification_status": data.get("certification_status"),
        "validation_id": data.get("validation_id"),
        "expected_hash": data.get("expected_hash"),
        "observed_hash": data.get("observed_hash"),
        "dashboard_hash": data.get("dashboard_hash"),
        "certificate_version": data.get("certificate_version") or "1.0",
        "certified_at": certified_at,
    }

    certificate_hash = data.get("certificate_hash") or calculate_certificate_hash(hash_payload)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO institutional_certifications (
            certification_id,
            certificate_type,
            execution_id,
            source_record_id,
            continuity_score,
            certification_status,
            validation_id,
            expected_hash,
            observed_hash,
            dashboard_hash,
            certificate_hash,
            certificate_version,
            certified_by,
            certified_at,
            verification_status,
            supersedes_certification_id,
            superseded_by_certification_id,
            revocation_status,
            revocation_reason,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        certification_id,
        data.get("certificate_type"),
        data.get("execution_id"),
        data.get("source_record_id"),
        data.get("continuity_score"),
        data.get("certification_status"),
        data.get("validation_id"),
        data.get("expected_hash"),
        data.get("observed_hash"),
        data.get("dashboard_hash"),
        certificate_hash,
        data.get("certificate_version") or "1.0",
        data.get("certified_by") or "Institutional Certification Engine",
        certified_at,
        data.get("verification_status") or "verified",
        data.get("supersedes_certification_id"),
        data.get("superseded_by_certification_id"),
        data.get("revocation_status") or "active",
        data.get("revocation_reason"),
        data.get("notes"),
    ))

    conn.commit()

    row = cur.execute(
        "SELECT * FROM institutional_certifications WHERE certification_id = ?",
        (certification_id,)
    ).fetchone()

    conn.close()

    return dict(row)


def get_institutional_certification(certification_id):
    ensure_institutional_certifications_table()
    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT * FROM institutional_certifications WHERE certification_id = ?",
        (certification_id,)
    ).fetchone()

    conn.close()
    return dict(row) if row else None


def list_institutional_certifications(certificate_type=None, execution_id=None):
    ensure_institutional_certifications_table()
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM institutional_certifications WHERE 1=1"
    params = []

    if certificate_type:
        query += " AND certificate_type = ?"
        params.append(certificate_type)

    if execution_id:
        query += " AND execution_id = ?"
        params.append(execution_id)

    query += " ORDER BY certified_at DESC, certification_id DESC"

    rows = cur.execute(query, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]


def verify_institutional_certification(certification_id):
    cert = get_institutional_certification(certification_id)
    if not cert:
        return {
            "verified": False,
            "verification_status": "missing",
            "message": "Certification record not found.",
        }

    payload = {
        "certification_id": cert.get("certification_id"),
        "certificate_type": cert.get("certificate_type"),
        "execution_id": cert.get("execution_id"),
        "continuity_score": cert.get("continuity_score"),
        "certification_status": cert.get("certification_status"),
        "validation_id": cert.get("validation_id"),
        "expected_hash": cert.get("expected_hash"),
        "observed_hash": cert.get("observed_hash"),
        "dashboard_hash": cert.get("dashboard_hash"),
        "certificate_version": cert.get("certificate_version"),
        "certified_at": cert.get("certified_at"),
    }

    recalculated = calculate_certificate_hash(payload)
    stored = cert.get("certificate_hash")

    return {
        "verified": recalculated == stored,
        "verification_status": "verified" if recalculated == stored else "hash_mismatch",
        "stored_hash": stored,
        "recalculated_hash": recalculated,
        "certification_id": certification_id,
    }


def create_continuity_certification(execution_id, certified_by="Institutional Certification Engine", notes=""):
    """
    ICP-3C:
    Creates immutable Continuity certification from ICP-2 dashboard profile.
    Requires full continuity readiness.
    """
    from services.services_execution_recovery import build_continuity_dashboard_profile

    dashboard = build_continuity_dashboard_profile(execution_id)

    eligible = (
        dashboard.get("continuity_score") == 100
        and dashboard.get("topology_ready")
        and dashboard.get("recovery_ready")
        and dashboard.get("replication_ready")
        and dashboard.get("revalidation_ready")
    )

    latest_validation = dashboard.get("revalidation_latest") or {}

    dashboard_hash = calculate_certificate_hash({
        "execution_id": execution_id,
        "continuity_score": dashboard.get("continuity_score"),
        "overall_status": dashboard.get("overall_status"),
        "validation_id": latest_validation.get("validation_id"),
        "expected_hash": latest_validation.get("expected_hash"),
        "observed_hash": latest_validation.get("observed_hash"),
    })

    certification_status = "Certified" if eligible else "Not Eligible"

    cert = create_institutional_certification({
        "certificate_type": "Continuity",
        "execution_id": execution_id,
        "source_record_id": latest_validation.get("package_id"),
        "continuity_score": dashboard.get("continuity_score"),
        "certification_status": certification_status,
        "validation_id": latest_validation.get("validation_id"),
        "expected_hash": latest_validation.get("expected_hash"),
        "observed_hash": latest_validation.get("observed_hash"),
        "dashboard_hash": dashboard_hash,
        "certificate_version": "1.0",
        "certified_by": certified_by,
        "verification_status": "verified" if eligible else "review_required",
        "notes": notes or "Continuity certification generated from ICP-2 dashboard profile.",
    })

    return cert



def get_latest_active_certification(certificate_type=None, execution_id=None):
    """
    ICP-3I:
    Returns latest active certificate for a type/execution pair.
    """
    rows = list_institutional_certifications(
        certificate_type=certificate_type,
        execution_id=execution_id,
    )

    for row in rows:
        if (row.get("revocation_status") or "active").lower() == "active":
            return row

    return None


def create_successor_institutional_certification(data, supersedes_certification_id=None):
    """
    ICP-3I:
    Creates a new immutable certificate and links it to the prior certificate.
    Existing certificates are not edited except for controlled supersession pointer.
    """
    prior = None

    if supersedes_certification_id:
        prior = get_institutional_certification(supersedes_certification_id)

    cert = create_institutional_certification({
        **data,
        "supersedes_certification_id": supersedes_certification_id,
    })

    if prior:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE institutional_certifications
            SET superseded_by_certification_id = ?
            WHERE certification_id = ?
        """, (
            cert.get("certification_id"),
            prior.get("certification_id"),
        ))

        conn.commit()
        conn.close()

    return cert


def create_successor_continuity_certification(execution_id, certified_by="Institutional Certification Engine", notes=""):
    """
    ICP-3I:
    Issues the next continuity certificate and links it to the latest active
    prior continuity certificate for this execution session.
    """
    prior = get_latest_active_certification(
        certificate_type="Continuity",
        execution_id=execution_id,
    )

    new_cert = create_continuity_certification(
        execution_id=execution_id,
        certified_by=certified_by,
        notes=notes or "Successor continuity certification issued under ICP-3I immutable certificate policy.",
    )

    if prior:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE institutional_certifications
            SET supersedes_certification_id = ?
            WHERE certification_id = ?
        """, (
            prior.get("certification_id"),
            new_cert.get("certification_id"),
        ))

        cur.execute("""
            UPDATE institutional_certifications
            SET superseded_by_certification_id = ?
            WHERE certification_id = ?
        """, (
            new_cert.get("certification_id"),
            prior.get("certification_id"),
        ))

        conn.commit()
        conn.close()

        new_cert = get_institutional_certification(new_cert.get("certification_id"))

    return new_cert


def get_certificate_chain(certification_id):
    """
    ICP-3I:
    Returns current certificate, direct predecessor, and direct successor.
    """
    cert = get_institutional_certification(certification_id)

    if not cert:
        return {
            "certificate": None,
            "supersedes": None,
            "superseded_by": None,
        }

    supersedes = (
        get_institutional_certification(cert.get("supersedes_certification_id"))
        if cert.get("supersedes_certification_id")
        else None
    )

    superseded_by = (
        get_institutional_certification(cert.get("superseded_by_certification_id"))
        if cert.get("superseded_by_certification_id")
        else None
    )

    return {
        "certificate": cert,
        "supersedes": supersedes,
        "superseded_by": superseded_by,
    }



def update_certificate_lifecycle(
    certification_id,
    lifecycle_status=None,
    issuance_reason=None,
    issuance_authority=None,
    generation_engine=None,
    lifecycle_notes=None,
):
    """
    ICP-4B-2:
    Updates governance metadata only.
    Does not modify certificate_hash or immutable certification facts.
    """
    ensure_institutional_certifications_table()

    conn = get_connection()
    cur = conn.cursor()

    cert = get_institutional_certification(certification_id)
    if not cert:
        conn.close()
        return None

    updates = []
    params = []

    allowed = {
        "lifecycle_status": lifecycle_status,
        "issuance_reason": issuance_reason,
        "issuance_authority": issuance_authority,
        "generation_engine": generation_engine,
        "lifecycle_notes": lifecycle_notes,
    }

    for field, value in allowed.items():
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        conn.close()
        return cert

    params.append(certification_id)

    cur.execute(
        f"""
        UPDATE institutional_certifications
        SET {", ".join(updates)}
        WHERE certification_id = ?
        """,
        params,
    )

    conn.commit()
    conn.close()

    return get_institutional_certification(certification_id)


def get_certificate_lifecycle(certification_id):
    """
    ICP-4B-2:
    Returns lifecycle metadata and chain state for one certificate.
    """
    cert = get_institutional_certification(certification_id)

    if not cert:
        return None

    chain_status = "Superseded" if cert.get("superseded_by_certification_id") else "Current"

    return {
        "certification_id": cert.get("certification_id"),
        "lifecycle_status": cert.get("lifecycle_status") or "Issued",
        "issuance_reason": cert.get("issuance_reason"),
        "issuance_authority": cert.get("issuance_authority"),
        "generation_engine": cert.get("generation_engine"),
        "lifecycle_notes": cert.get("lifecycle_notes"),
        "chain_status": chain_status,
        "supersedes_certification_id": cert.get("supersedes_certification_id"),
        "superseded_by_certification_id": cert.get("superseded_by_certification_id"),
    }


def backfill_certificate_lifecycle_defaults():
    """
    ICP-4B-2:
    Adds default lifecycle governance metadata to existing certificates.
    Safe metadata-only backfill.
    """
    ensure_institutional_certifications_table()

    rows = list_institutional_certifications()
    updated = []

    for row in rows:
        lifecycle_status = row.get("lifecycle_status") or "Issued"

        generation_engine = row.get("generation_engine")
        if not generation_engine:
            if row.get("certificate_type") == "Continuity":
                generation_engine = "Continuity Certification Engine"
            else:
                generation_engine = "Institutional Certification Engine"

        issuance_reason = row.get("issuance_reason") or "Initial lifecycle governance backfill."
        issuance_authority = row.get("issuance_authority") or row.get("certified_by") or "Institutional Operator"

        cert = update_certificate_lifecycle(
            row.get("certification_id"),
            lifecycle_status=lifecycle_status,
            issuance_reason=issuance_reason,
            issuance_authority=issuance_authority,
            generation_engine=generation_engine,
            lifecycle_notes=row.get("lifecycle_notes") or "Lifecycle metadata added under ICP-4B-2.",
        )

        updated.append(cert)

    return updated



def _next_lifecycle_event_id():
    ensure_certificate_lifecycle_events_table()

    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT COUNT(*) AS count FROM certificate_lifecycle_events"
    ).fetchone()

    conn.close()

    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CEVT-{count + 1:06d}"


def record_certificate_lifecycle_event(
    certification_id,
    event_type,
    event_status=None,
    event_reason=None,
    event_authority=None,
    generation_engine=None,
    event_notes=None,
    actor=None,
):
    """
    ICP-4B-3:
    Appends immutable lifecycle event for a certificate.
    """
    ensure_certificate_lifecycle_events_table()

    cert = get_institutional_certification(certification_id)
    if not cert:
        return None

    event_id = _next_lifecycle_event_id()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO certificate_lifecycle_events (
            event_id,
            certification_id,
            event_type,
            event_status,
            event_reason,
            event_authority,
            generation_engine,
            event_notes,
            actor,
            event_at,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        certification_id,
        event_type,
        event_status,
        event_reason,
        event_authority,
        generation_engine,
        event_notes,
        actor,
        now,
        now,
    ))

    conn.commit()

    row = cur.execute("""
        SELECT *
        FROM certificate_lifecycle_events
        WHERE event_id = ?
    """, (event_id,)).fetchone()

    conn.close()

    return dict(row) if row else None


def list_certificate_lifecycle_events(certification_id):
    """
    ICP-4B-3:
    Lists lifecycle events for a certificate in chronological order.
    """
    ensure_certificate_lifecycle_events_table()

    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT *
        FROM certificate_lifecycle_events
        WHERE certification_id = ?
        ORDER BY event_at ASC, event_id ASC
    """, (certification_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def backfill_certificate_lifecycle_events(actor="system"):
    """
    ICP-4B-3:
    Seeds lifecycle event history for existing certificates.
    Idempotent by certification_id + event_type.
    """
    ensure_certificate_lifecycle_events_table()

    rows = list_institutional_certifications()
    created = []

    conn = get_connection()
    cur = conn.cursor()

    for cert in rows:
        certification_id = cert.get("certification_id")

        existing_types = {
            row["event_type"]
            for row in cur.execute("""
                SELECT event_type
                FROM certificate_lifecycle_events
                WHERE certification_id = ?
            """, (certification_id,)).fetchall()
        }

        planned = [
            (
                "Created",
                cert.get("certification_status") or "Certified",
                cert.get("issuance_reason") or "Certificate record created.",
                cert.get("issuance_authority") or cert.get("certified_by"),
                cert.get("generation_engine") or "Institutional Certification Engine",
                "Backfilled certificate creation lifecycle event.",
            ),
            (
                "Issued",
                cert.get("lifecycle_status") or "Issued",
                cert.get("issuance_reason") or "Certificate issued.",
                cert.get("issuance_authority") or cert.get("certified_by"),
                cert.get("generation_engine") or "Institutional Certification Engine",
                "Backfilled certificate issuance lifecycle event.",
            ),
            (
                "Verified",
                cert.get("verification_status") or "verified",
                "Certificate hash verification recorded.",
                cert.get("issuance_authority") or cert.get("certified_by"),
                cert.get("generation_engine") or "Institutional Certification Engine",
                "Backfilled certificate verification lifecycle event.",
            ),
        ]

        if cert.get("superseded_by_certification_id"):
            planned.append((
                "Superseded",
                "Superseded",
                f"Certificate superseded by {cert.get('superseded_by_certification_id')}.",
                cert.get("issuance_authority") or cert.get("certified_by"),
                cert.get("generation_engine") or "Institutional Certification Engine",
                "Backfilled supersession lifecycle event.",
            ))

        for event_type, event_status, reason, authority, engine, notes in planned:
            if event_type in existing_types:
                continue

            event = record_certificate_lifecycle_event(
                certification_id,
                event_type=event_type,
                event_status=event_status,
                event_reason=reason,
                event_authority=authority,
                generation_engine=engine,
                event_notes=notes,
                actor=actor,
            )

            if event:
                created.append(event)

    conn.close()
    return created



def set_certificate_supersession_reason(
    certification_id,
    reason,
    authority=None,
    actor=None,
    notes=None,
):
    """
    ICP-4B-4:
    Captures why a certificate was superseded or why a successor certificate
    was issued. Metadata-only update. Certificate hash remains unchanged.
    """
    cert = get_institutional_certification(certification_id)
    if not cert:
        return None

    updated = update_certificate_lifecycle(
        certification_id,
        issuance_reason=reason,
        issuance_authority=authority or cert.get("issuance_authority") or cert.get("certified_by"),
        lifecycle_notes=notes or "Supersession reason captured under ICP-4B-4.",
    )

    record_certificate_lifecycle_event(
        certification_id,
        event_type="Supersession Reason Captured",
        event_status=updated.get("lifecycle_status") or "Issued",
        event_reason=reason,
        event_authority=authority or updated.get("issuance_authority"),
        generation_engine=updated.get("generation_engine") or "Institutional Certification Engine",
        event_notes=notes or "Supersession reason captured.",
        actor=actor or authority or updated.get("certified_by") or "system",
    )

    return updated


def backfill_supersession_reasons(
    execution_id="EXE-000001",
    certificate_type="Continuity",
    authority="admin123",
):
    """
    ICP-4B-4:
    Backfills explanation metadata for an existing supersession chain.
    """
    rows = list_institutional_certifications(
        certificate_type=certificate_type,
        execution_id=execution_id,
    )

    updated = []

    for row in rows:
        cert_id = row.get("certification_id")
        supersedes = row.get("supersedes_certification_id")
        superseded_by = row.get("superseded_by_certification_id")

        if supersedes:
            reason = (
                f"Successor certificate issued to supersede {supersedes} "
                f"after continuity certification refresh."
            )
            notes = (
                f"{cert_id} is part of the continuity certification chain and "
                f"supersedes {supersedes}."
            )
        elif superseded_by:
            reason = (
                f"Certificate superseded by {superseded_by} during continuity "
                f"certification chain update."
            )
            notes = (
                f"{cert_id} remains an immutable historical certificate and is "
                f"superseded by {superseded_by}."
            )
        else:
            reason = "Initial continuity certificate issuance."
            notes = f"{cert_id} is the current active certificate in its chain."

        updated_cert = set_certificate_supersession_reason(
            cert_id,
            reason=reason,
            authority=authority,
            actor=authority,
            notes=notes,
        )

        updated.append(updated_cert)

    return updated

