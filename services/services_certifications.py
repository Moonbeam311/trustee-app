from database.db import get_connection, ensure_institutional_certifications_table
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

