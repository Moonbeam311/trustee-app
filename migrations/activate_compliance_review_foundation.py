"""Governed Compliance Review activation migration.

H.6B defines and validates the Compliance Review activation architecture. This
module is deliberately command-line controlled and must never be imported by app
startup as an initializer. It refuses the repository normal database during this
phase and is validated only against temporary database copies.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMAL_DB = (ROOT / "trustee_app.db").resolve()
SCHEMA_VERSION = "compliance_reviews_h6b_v1"
MIGRATION_NAME = "activate_compliance_review_foundation_h6b"
MODULE_KEY = "compliance_reviews"
REQUIRED_TOKEN = "H6B-TEMPORARY-ACTIVATION"

EXPECTED_TABLES = {
    "compliance_review_number_sequences",
    "compliance_reviews",
    "compliance_review_subjects",
    "compliance_review_evidence",
    "compliance_review_findings",
    "compliance_review_remediations",
    "compliance_review_approvals",
    "compliance_review_certifications",
    "compliance_review_relationships",
    "compliance_review_audit_ledger",
    "compliance_review_events",
    "compliance_review_activation_registry",
}

CREATE_STATEMENTS = [
    """
    CREATE TABLE compliance_review_number_sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        namespace TEXT NOT NULL,
        sequence_year INTEGER NOT NULL,
        last_number INTEGER NOT NULL DEFAULT 0 CHECK(last_number >= 0),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(namespace, sequence_year)
    )
    """,
    """
    CREATE TABLE compliance_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_review_id TEXT NOT NULL UNIQUE,
        firm_id TEXT NOT NULL,
        institution_id TEXT,
        matter_id TEXT,
        trust_id TEXT,
        related_object_type TEXT NOT NULL DEFAULT 'governed_record',
        related_object_id TEXT,
        related_object_label TEXT,
        deployment_key TEXT,
        title TEXT NOT NULL,
        review_type TEXT NOT NULL,
        purpose TEXT,
        scope TEXT,
        review_standard TEXT,
        jurisdiction TEXT,
        question_presented TEXT NOT NULL,
        governing_requirement_type TEXT NOT NULL,
        governing_requirement_id TEXT,
        governing_requirement_label TEXT,
        source_type TEXT NOT NULL,
        source_id TEXT,
        source_label TEXT,
        scope_summary TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        risk_level TEXT NOT NULL DEFAULT 'moderate',
        priority TEXT NOT NULL DEFAULT 'normal',
        confidentiality_level TEXT NOT NULL DEFAULT 'internal',
        initiated_by TEXT,
        initiated_at TEXT,
        assigned_reviewer TEXT,
        review_owner TEXT,
        assigned_to TEXT,
        issuing_authority TEXT,
        authority_basis TEXT,
        approval_required INTEGER NOT NULL DEFAULT 0 CHECK(approval_required IN (0,1)),
        approved_by TEXT,
        approved_at TEXT,
        due_date TEXT,
        due_at TEXT,
        completed_at TEXT,
        closed_at TEXT,
        reopened_at TEXT,
        superseded_by TEXT,
        finding TEXT,
        disposition TEXT,
        disposition_basis TEXT,
        required_follow_up TEXT,
        opened_at TEXT,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_by TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version >= 1),
        version_number INTEGER NOT NULL DEFAULT 1 CHECK(version_number >= 1),
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        idempotency_key TEXT,
        payload_hash TEXT,
        CHECK(status IN ('draft','opened','under_review','awaiting_information','ready_for_disposition','findings_issued','remediation_required','remediation_in_progress','pending_verification','pending_approval','approved','certified','closed','reopened','superseded','archived','cancelled'))
    )
    """,
    """
    CREATE TABLE compliance_review_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_subject_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        firm_id TEXT NOT NULL,
        subject_role TEXT NOT NULL CHECK(subject_role IN ('primary','secondary','source','dependent','parent','supersedes','related_governance')),
        subject_type TEXT NOT NULL,
        subject_id TEXT,
        subject_label TEXT,
        relationship_verb TEXT,
        direction TEXT NOT NULL DEFAULT 'outbound' CHECK(direction IN ('outbound','inbound','bidirectional')),
        status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive','superseded')),
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_evidence_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT,
        source_label TEXT,
        document_id TEXT,
        upload_id TEXT,
        external_reference TEXT,
        description TEXT,
        relevance TEXT,
        evidence_status TEXT NOT NULL DEFAULT 'identified' CHECK(evidence_status IN ('identified','requested','received','reviewed','verified','rejected','superseded','withdrawn')),
        verification_status TEXT NOT NULL DEFAULT 'unverified' CHECK(verification_status IN ('unverified','authenticity_pending','integrity_pending','relevance_pending','verified','rejected')),
        verified_by TEXT,
        verified_at TEXT,
        integrity_reference TEXT,
        added_by TEXT NOT NULL,
        added_at TEXT NOT NULL,
        removed_at TEXT,
        removal_reason TEXT,
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_finding_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        finding_number INTEGER NOT NULL CHECK(finding_number >= 1),
        finding_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        requirement_or_standard TEXT,
        evidence_basis TEXT,
        severity TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('informational','low','medium','high','critical')),
        risk_level TEXT NOT NULL DEFAULT 'moderate',
        status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','issued','acknowledged','disputed','resolved','superseded','withdrawn')),
        disputed INTEGER NOT NULL DEFAULT 0 CHECK(disputed IN (0,1)),
        dispute_basis TEXT,
        issued_by TEXT,
        issued_at TEXT,
        acknowledged_by TEXT,
        acknowledged_at TEXT,
        resolved_at TEXT,
        superseded_by TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(compliance_review_id, finding_number),
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_remediations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_remediation_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        compliance_finding_id TEXT,
        action_number INTEGER NOT NULL CHECK(action_number >= 1),
        required_action TEXT NOT NULL,
        responsible_party_type TEXT,
        responsible_party_id TEXT,
        responsible_party_label TEXT,
        due_date TEXT,
        status TEXT NOT NULL DEFAULT 'proposed',
        completion_evidence TEXT,
        completed_by TEXT,
        completed_at TEXT,
        verified_by TEXT,
        verified_at TEXT,
        verification_result TEXT,
        exception_requested INTEGER NOT NULL DEFAULT 0 CHECK(exception_requested IN (0,1)),
        exception_basis TEXT,
        exception_requested_by TEXT,
        exception_requested_by_label TEXT,
        exception_requested_at TEXT,
        exception_request_basis TEXT,
        exception_request_status TEXT,
        exception_approved_by TEXT,
        exception_approved_at TEXT,
        closure_notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(compliance_review_id, action_number),
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT,
        FOREIGN KEY(compliance_finding_id) REFERENCES compliance_review_findings(compliance_finding_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_approval_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        approval_type TEXT NOT NULL,
        requested_by TEXT,
        requested_at TEXT,
        approved_by TEXT,
        approved_at TEXT,
        approval_status TEXT NOT NULL DEFAULT 'pending',
        authority_basis TEXT,
        maker_actor_id TEXT,
        checker_actor_id TEXT,
        note TEXT,
        revoked_by TEXT,
        revoked_at TEXT,
        revocation_basis TEXT,
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT,
        CHECK(checker_actor_id IS NULL OR checker_actor_id <> maker_actor_id)
    )
    """,
    """
    CREATE TABLE compliance_review_certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        certification_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        certification_type TEXT NOT NULL,
        certification_statement TEXT NOT NULL,
        certified_by TEXT NOT NULL,
        authority_basis TEXT NOT NULL,
        certified_at TEXT NOT NULL,
        effective_date TEXT,
        expiration_date TEXT,
        certification_status TEXT NOT NULL DEFAULT 'active',
        revoked_by TEXT,
        revoked_at TEXT,
        revocation_basis TEXT,
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        relationship_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        relationship_type TEXT NOT NULL,
        related_record_type TEXT NOT NULL,
        related_record_id TEXT NOT NULL,
        direction TEXT NOT NULL DEFAULT 'outbound',
        status TEXT NOT NULL DEFAULT 'active',
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT NOT NULL,
        event_sequence INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_label TEXT NOT NULL,
        prior_status TEXT,
        resulting_status TEXT,
        summary TEXT,
        reason TEXT,
        related_record_type TEXT,
        related_record_id TEXT,
        idempotency_key TEXT,
        payload_hash TEXT,
        expected_version INTEGER,
        created_at TEXT NOT NULL,
        UNIQUE(compliance_review_id, event_sequence),
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_audit_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compliance_audit_id TEXT NOT NULL UNIQUE,
        compliance_review_id TEXT,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        action TEXT NOT NULL,
        previous_state TEXT,
        new_state TEXT,
        note TEXT,
        actor_id TEXT NOT NULL,
        actor_label TEXT,
        actor_role TEXT,
        target_firm_id TEXT,
        canonical_authority TEXT,
        source_permission TEXT,
        exception_requested_by TEXT,
        exception_approved_by TEXT,
        sod_result TEXT,
        override_used INTEGER NOT NULL DEFAULT 0 CHECK(override_used IN (0,1)),
        authority_basis TEXT,
        created_at TEXT NOT NULL,
        previous_hash TEXT,
        entry_hash TEXT NOT NULL,
        hash_algorithm TEXT NOT NULL DEFAULT 'SHA-256',
        firm_id TEXT NOT NULL,
        FOREIGN KEY(compliance_review_id) REFERENCES compliance_reviews(compliance_review_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE compliance_review_activation_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activation_id TEXT NOT NULL UNIQUE,
        module_key TEXT NOT NULL,
        schema_version TEXT NOT NULL,
        migration_name TEXT NOT NULL,
        status TEXT NOT NULL,
        requested_by TEXT,
        requested_at TEXT,
        approved_by TEXT,
        approved_at TEXT,
        authority_basis TEXT NOT NULL,
        target_database_identifier TEXT NOT NULL,
        pre_migration_hash TEXT,
        post_migration_hash TEXT,
        backup_reference TEXT,
        started_at TEXT,
        completed_at TEXT,
        rollback_status TEXT,
        rollback_reference TEXT,
        verification_status TEXT,
        verified_by TEXT,
        verified_at TEXT,
        notes TEXT,
        UNIQUE(module_key, schema_version)
    )
    """,
]

INDEX_STATEMENTS = [
    "CREATE UNIQUE INDEX ux_compliance_reviews_idempotency ON compliance_reviews(idempotency_key) WHERE idempotency_key IS NOT NULL",
    "CREATE INDEX idx_compliance_reviews_firm_status ON compliance_reviews(firm_id, status)",
    "CREATE INDEX idx_compliance_reviews_subject ON compliance_reviews(related_object_type, related_object_id)",
    "CREATE INDEX idx_compliance_reviews_source ON compliance_reviews(source_type, source_id)",
    "CREATE INDEX idx_compliance_reviews_requirement ON compliance_reviews(governing_requirement_type, governing_requirement_id)",
    "CREATE INDEX idx_compliance_reviews_due ON compliance_reviews(due_date, due_at)",
    "CREATE INDEX idx_compliance_subjects_review ON compliance_review_subjects(compliance_review_id, subject_role)",
    "CREATE INDEX idx_compliance_evidence_review ON compliance_review_evidence(compliance_review_id, evidence_status)",
    "CREATE INDEX idx_compliance_findings_review ON compliance_review_findings(compliance_review_id, status)",
    "CREATE INDEX idx_compliance_remediation_review ON compliance_review_remediations(compliance_review_id, status)",
    "CREATE INDEX idx_compliance_approvals_review ON compliance_review_approvals(compliance_review_id, approval_status)",
    "CREATE INDEX idx_compliance_certifications_review ON compliance_review_certifications(compliance_review_id, certification_status)",
    "CREATE UNIQUE INDEX uq_compliance_review_relationship_active ON compliance_review_relationships(compliance_review_id, relationship_type, related_record_type, related_record_id, direction, status) WHERE status = 'active'",
    "CREATE UNIQUE INDEX uq_compliance_review_events_idempotency ON compliance_review_events(compliance_review_id, idempotency_key) WHERE idempotency_key IS NOT NULL",
    "CREATE INDEX idx_compliance_review_events_review ON compliance_review_events(compliance_review_id, event_sequence)",
    "CREATE INDEX idx_compliance_audit_review ON compliance_review_audit_ledger(compliance_review_id, created_at)",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def existing_compliance_objects(conn: sqlite3.Connection) -> dict[str, str]:
    return {
        row["name"]: row["sql"] or ""
        for row in conn.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE (type IN ('table','index','trigger','view'))
              AND lower(name) LIKE 'compliance_review%'
            ORDER BY name
            """
        )
    }


def verify_schema(conn: sqlite3.Connection) -> tuple[bool, list[str]]:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'compliance_review%'"
        )
    }
    missing = sorted(EXPECTED_TABLES - tables)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    activation = conn.execute(
        """
        SELECT status, verification_status
        FROM compliance_review_activation_registry
        WHERE module_key = ? AND schema_version = ?
        """,
        (MODULE_KEY, SCHEMA_VERSION),
    ).fetchone()
    errors = []
    if missing:
        errors.append("missing_tables=" + ",".join(missing))
    if integrity != "ok":
        errors.append("integrity=" + str(integrity))
    if fk:
        errors.append("foreign_key_failures=" + str(len(fk)))
    if not activation or activation["status"] != "activation_verified":
        errors.append("activation_registry_not_verified")
    return not errors, errors


def preflight(path: Path, token: str) -> None:
    if not path:
        raise SystemExit("ERROR explicit --database PATH is required")
    resolved = path.resolve()
    if resolved == NORMAL_DB:
        raise SystemExit("ERROR trustee_app.db is refused during H.6B")
    if ROOT in resolved.parents:
        raise SystemExit("ERROR H.6B migration target must be outside the repository")
    if token != REQUIRED_TOKEN:
        raise SystemExit("ERROR explicit H.6B activation authorization token is required")
    if not resolved.exists():
        raise SystemExit("ERROR database path does not exist")


def dry_run(path: Path) -> int:
    before = sha256(path)
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as conn:
        existing = existing_compliance_objects(conn)
    after = sha256(path)
    print("mode=dry-run")
    print(f"database={path}")
    print(f"schema_version={SCHEMA_VERSION}")
    print(f"expected_tables={','.join(sorted(EXPECTED_TABLES))}")
    print(f"existing_compliance_objects={len(existing)}")
    print(f"read_only={before == after}")
    if existing:
        missing = sorted(EXPECTED_TABLES - set(existing))
        print(f"would_refuse_partial_schema={bool(missing)}")
    else:
        print("would_apply=True")
    return 0 if before == after else 1


def apply(path: Path) -> int:
    before_hash = sha256(path)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    conn = connect(path)
    try:
        existing = existing_compliance_objects(conn)
        table_existing = {name for name in existing if name in EXPECTED_TABLES}
        if existing and table_existing != EXPECTED_TABLES:
            print("status=partial_schema_conflict")
            print("existing=" + ",".join(sorted(existing)))
            return 2
        if table_existing == EXPECTED_TABLES:
            ok, errors = verify_schema(conn)
            print("status=already_activated" if ok else "status=activation_invalid")
            if errors:
                print("errors=" + ";".join(errors))
            return 0 if ok else 3

        conn.execute("BEGIN IMMEDIATE")
        try:
            for statement in CREATE_STATEMENTS:
                conn.execute(statement)
            if os.environ.get("H6B_FORCE_MIGRATION_FAILURE") == "after_tables":
                raise RuntimeError("forced_h6b_failure_after_tables")
            for statement in INDEX_STATEMENTS:
                conn.execute(statement)
            post_schema_hash = hashlib.sha256("|".join(sorted(EXPECTED_TABLES)).encode()).hexdigest().upper()
            activation_id = f"CAR-{datetime.now(UTC).year}-000001"
            conn.execute(
                """
                INSERT INTO compliance_review_activation_registry (
                    activation_id, module_key, schema_version, migration_name, status,
                    requested_by, requested_at, approved_by, approved_at, authority_basis,
                    target_database_identifier, pre_migration_hash, post_migration_hash,
                    started_at, completed_at, rollback_status, verification_status,
                    verified_by, verified_at, notes
                ) VALUES (?, ?, ?, ?, 'activation_verified', 'h6b-temp-validation', ?,
                          'h6b-temp-approval', ?, ?, ?, ?, ?, ?, ?, 'not_required',
                          'verified', 'h6b-migration', ?, ?)
                """,
                (
                    activation_id,
                    MODULE_KEY,
                    SCHEMA_VERSION,
                    MIGRATION_NAME,
                    now,
                    now,
                    "H.6B temporary-copy validation only; normal database activation prohibited.",
                    str(path.resolve()),
                    before_hash,
                    post_schema_hash,
                    now,
                    now,
                    now,
                    "No sample Compliance Review records inserted.",
                ),
            )
            ok, errors = verify_schema(conn)
            if not ok:
                raise RuntimeError("schema_verification_failed:" + ";".join(errors))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        after_hash = sha256(path)
        print("status=activated")
        print(f"schema_version={SCHEMA_VERSION}")
        print(f"pre_migration_hash={before_hash}")
        print(f"post_migration_hash={after_hash}")
        print("sample_records=0")
        return 0
    except Exception as exc:
        print("status=failed")
        print("error=" + exc.__class__.__name__)
        return 1
    finally:
        conn.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Activate Compliance Review foundation on an explicitly authorized temporary database copy.")
    parser.add_argument("--database", required=True, help="Explicit SQLite database path. H.6B refuses trustee_app.db.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--activation-token", required=True, help="Explicit H.6B temporary activation token.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    path = Path(args.database)
    preflight(path, args.activation_token)
    if args.dry_run:
        return dry_run(path)
    return apply(path)


if __name__ == "__main__":
    raise SystemExit(main())
