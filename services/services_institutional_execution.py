import sqlite3
"""
Institutional Execution Layer service.

Additive foundation for:
- execution ceremony
- signature objects
- witness/notary records
- seal ledger
- execution ledger
- archive freeze
"""

from datetime import datetime
import hashlib
from database.db import get_connection, ensure_institutional_execution_layer_tables


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def _hash_parts(*parts):
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _next_id(prefix, table, column):
    ensure_institutional_execution_layer_tables()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
    count = row["c"] if hasattr(row, "keys") else row[0]
    conn.close()
    return f"{prefix}-{count + 1:06d}"


def create_execution_session(
    object_type,
    object_id,
    document_type,
    document_title,
    matter_id="",
    trust_id="",
    created_by="",
    execution_location="",
    notes="",
):
    ensure_institutional_execution_layer_tables()
    execution_id = _next_id("EXE", "institutional_execution_sessions", "execution_id")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO institutional_execution_sessions (
            execution_id, object_type, object_id, matter_id, trust_id,
            document_type, document_title, ceremony_status, current_step,
            execution_location, created_by, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        execution_id, object_type, object_id, matter_id, trust_id,
        document_type, document_title, "draft", "prepared",
        execution_location, created_by, notes
    ))
    conn.commit()
    conn.close()

    append_execution_ledger_event(
        execution_id,
        "session_created",
        "Execution Session Created",
        created_by,
        f"Execution session created for {object_type}:{object_id}."
    )
    return execution_id


def append_execution_ledger_event(execution_id, event_type, event_label, actor="", notes=""):
    ensure_institutional_execution_layer_tables()
    ledger_id = _next_id("LED", "institutional_execution_ledger", "ledger_id")

    conn = get_connection()
    cur = conn.cursor()

    prev = cur.execute("""
        SELECT provenance_hash, event_sequence
        FROM institutional_execution_ledger
        WHERE execution_id = ?
        ORDER BY event_sequence DESC
        LIMIT 1
    """, (execution_id,)).fetchone()

    previous_hash = ""
    next_sequence = 1
    if prev:
        previous_hash = prev["provenance_hash"] if hasattr(prev, "keys") else prev[0]
        last_seq = prev["event_sequence"] if hasattr(prev, "keys") else prev[1]
        next_sequence = int(last_seq or 0) + 1

    event_at = _now()
    provenance_hash = _hash_parts(execution_id, event_type, event_label, actor, event_at, next_sequence, previous_hash, notes)

    cur.execute("""
        INSERT INTO institutional_execution_ledger (
            ledger_id, execution_id, event_type, event_label, event_actor,
            event_at, event_sequence, provenance_hash, previous_hash, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ledger_id, execution_id, event_type, event_label, actor,
        event_at, next_sequence, provenance_hash, previous_hash, notes
    ))

    conn.commit()
    conn.close()
    return ledger_id


def add_signature_record(execution_id, signer_name, signer_role, signer_capacity="", method="wet_signature", actor=""):
    ensure_institutional_execution_layer_tables()
    signature_id = _next_id("SIG", "institutional_signature_records", "signature_id")
    signed_at = _now()
    signature_hash = _hash_parts(execution_id, signature_id, signer_name, signer_role, signer_capacity, method, signed_at)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO institutional_signature_records (
            signature_id, execution_id, signer_name, signer_role, signer_capacity,
            signature_status, signature_method, signed_at, identity_verified, signature_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signature_id, execution_id, signer_name, signer_role, signer_capacity,
        "signed", method, signed_at, "not_checked", signature_hash
    ))
    conn.commit()
    conn.close()

    append_execution_ledger_event(execution_id, "signature_recorded", "Signature Recorded", actor or signer_name, f"{signer_role}: {signer_name}")
    return signature_id


def add_witness_or_notary_record(execution_id, participant_type, participant_name, participant_role="", actor="", notes=""):
    ensure_institutional_execution_layer_tables()
    record_id = _next_id("WNR", "institutional_witness_notary_records", "record_id")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO institutional_witness_notary_records (
            record_id, execution_id, participant_type, participant_name,
            participant_role, verification_status, signed_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_id, execution_id, participant_type, participant_name,
        participant_role, "recorded", _now(), notes
    ))
    conn.commit()
    conn.close()

    append_execution_ledger_event(execution_id, f"{participant_type}_recorded", f"{participant_type.title()} Recorded", actor or participant_name, notes)
    return record_id


def apply_institutional_seal(execution_id, seal_id, seal_style, applied_to, applied_by="", notes=""):
    ensure_institutional_execution_layer_tables()
    seal_event_id = _next_id("SEL", "institutional_seal_ledger", "seal_event_id")
    seal_hash = _hash_parts(execution_id, seal_event_id, seal_id, seal_style, applied_to, applied_by)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO institutional_seal_ledger (
            seal_event_id, execution_id, seal_id, seal_style, applied_to,
            applied_by, seal_hash, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        seal_event_id, execution_id, seal_id, seal_style, applied_to,
        applied_by, seal_hash, notes
    ))
    conn.commit()
    conn.close()

    append_execution_ledger_event(execution_id, "seal_applied", "Institutional Seal Applied", applied_by, f"{seal_style} applied to {applied_to}.")
    return seal_event_id


def freeze_execution_archive(execution_id, object_type, object_id, frozen_by="", package_path="", notes=""):
    ensure_institutional_execution_layer_tables()
    freeze_id = _next_id("FRZ", "institutional_archive_freezes", "freeze_id")
    freeze_hash = _hash_parts(execution_id, object_type, object_id, frozen_by, package_path, _now(), notes)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO institutional_archive_freezes (
            freeze_id, execution_id, object_type, object_id, archive_status,
            freeze_hash, frozen_by, package_path, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        freeze_id, execution_id, object_type, object_id, "frozen",
        freeze_hash, frozen_by, package_path, notes
    ))
    cur.execute("""
        UPDATE institutional_execution_sessions
        SET archive_freeze_status = ?,
            ceremony_status = ?,
            current_step = ?,
            final_hash = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE execution_id = ?
    """, ("frozen", "finalized", "archive_frozen", freeze_hash, execution_id))
    conn.commit()
    conn.close()

    append_execution_ledger_event(execution_id, "archive_frozen", "Immutable Archive Frozen", frozen_by, f"Freeze ID: {freeze_id}")
    return freeze_id


def get_execution_session(execution_id):
    ensure_institutional_execution_layer_tables()
    conn = get_connection()
    cur = conn.cursor()

    session = cur.execute("SELECT * FROM institutional_execution_sessions WHERE execution_id = ?", (execution_id,)).fetchone()
    signatures = cur.execute("SELECT * FROM institutional_signature_records WHERE execution_id = ? ORDER BY created_at", (execution_id,)).fetchall()
    participants = cur.execute("SELECT * FROM institutional_witness_notary_records WHERE execution_id = ? ORDER BY created_at", (execution_id,)).fetchall()
    seals = cur.execute("SELECT * FROM institutional_seal_ledger WHERE execution_id = ? ORDER BY applied_at", (execution_id,)).fetchall()
    ledger = cur.execute("SELECT * FROM institutional_execution_ledger WHERE execution_id = ? ORDER BY event_sequence", (execution_id,)).fetchall()
    freezes = cur.execute("SELECT * FROM institutional_archive_freezes WHERE execution_id = ? ORDER BY frozen_at", (execution_id,)).fetchall()

    def d(row):
        return dict(row) if row else None

    result = {
        "session": d(session),
        "signatures": [d(r) for r in signatures],
        "participants": [d(r) for r in participants],
        "seals": [d(r) for r in seals],
        "ledger": [d(r) for r in ledger],
        "freezes": [d(r) for r in freezes],
    }
    conn.close()
    result["evidence_vault"] = get_or_create_evidence_package(execution_id, result)
    return result


def ensure_evidence_vault_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_evidence_packages (
            package_id TEXT PRIMARY KEY,
            execution_id TEXT,
            vault_id TEXT,
            vault_name TEXT,
            archive_tier TEXT,
            archive_policy TEXT,
            retention_schedule TEXT,
            custodian TEXT,
            transfer_status TEXT,
            classification TEXT,
            integrity_status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_custody_transfers (
            transfer_id TEXT PRIMARY KEY,
            package_id TEXT,
            execution_id TEXT,
            custodian TEXT,
            action TEXT,
            transfer_status TEXT,
            transfer_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_or_create_evidence_package(execution_id, context):
    ensure_evidence_vault_tables()

    session = context.get("session") or {}
    package_id = "PKG-" + str(execution_id).replace("EXE-", "")
    vault_id = "VLT-" + str(execution_id).replace("EXE-", "")

    ceremony_finalized = session.get("ceremony_status") == "finalized"
    archive_frozen = session.get("archive_freeze_status") == "frozen"
    has_hash = bool(session.get("final_hash"))
    has_ledger = bool(context.get("ledger"))
    has_freeze = bool(context.get("freezes"))
    integrity_status = "Verified" if ceremony_finalized and archive_frozen and has_hash and has_ledger and has_freeze else "Pending"

    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT package_id FROM institutional_evidence_packages WHERE package_id = ?",
        (package_id,)
    ).fetchone()

    if not existing:
        cur.execute("""
            INSERT INTO institutional_evidence_packages (
                package_id, execution_id, vault_id, vault_name, archive_tier,
                archive_policy, retention_schedule, custodian, transfer_status,
                classification, integrity_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            package_id, execution_id, vault_id, "Institutional Execution Vault",
            "Permanent", "Immutable Institutional Archive", "Permanent",
            "Institutional Archive", "No Transfers Recorded",
            "Institutional Record", integrity_status,
            "Auto-created from finalized institutional execution session."
        ))

        transfer_id = "CUST-" + str(execution_id).replace("EXE-", "")
        cur.execute("""
            INSERT OR IGNORE INTO institutional_custody_transfers (
                transfer_id, package_id, execution_id, custodian, action,
                transfer_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transfer_id, package_id, execution_id, session.get("created_by") or "admin123",
            "Archive Accepted", "Active",
            "Initial evidence package accepted into institutional archive."
        ))
    else:
        cur.execute("""
            UPDATE institutional_evidence_packages
            SET integrity_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE package_id = ?
        """, (integrity_status, package_id))

    conn.commit()
    conn.row_factory = sqlite3.Row
    pkg = cur.execute(
        "SELECT * FROM institutional_evidence_packages WHERE package_id = ?",
        (package_id,)
    ).fetchone()
    transfers = cur.execute(
        "SELECT * FROM institutional_custody_transfers WHERE package_id = ? ORDER BY transfer_at",
        (package_id,)
    ).fetchall()

    result = {
        "package": dict(pkg) if pkg else {},
        "transfers": [dict(r) for r in transfers],
    }

    conn.close()
    return result
