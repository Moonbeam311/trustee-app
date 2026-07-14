import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import get_connection


def ensure_compliance_review_foundation(connection=None):
    owns_connection = connection is None
    conn = connection or get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS compliance_review_number_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT NOT NULL,
                sequence_year INTEGER NOT NULL,
                last_number INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(namespace, sequence_year)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS compliance_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compliance_review_id TEXT NOT NULL UNIQUE,
                firm_id TEXT NOT NULL,
                institution_id TEXT,
                trust_id TEXT,
                matter_id TEXT,
                deployment_key TEXT,
                title TEXT NOT NULL,
                review_type TEXT NOT NULL,
                question_presented TEXT NOT NULL,
                governing_requirement_type TEXT NOT NULL,
                governing_requirement_id TEXT,
                governing_requirement_label TEXT,
                source_type TEXT NOT NULL,
                source_id TEXT,
                source_label TEXT,
                scope_summary TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                priority TEXT NOT NULL DEFAULT 'normal',
                risk_level TEXT NOT NULL DEFAULT 'moderate',
                review_owner TEXT,
                assigned_to TEXT,
                authority_basis TEXT,
                approval_required INTEGER NOT NULL DEFAULT 0,
                approved_by TEXT,
                approved_at TEXT,
                finding TEXT,
                disposition TEXT,
                disposition_basis TEXT,
                required_follow_up TEXT,
                opened_at TEXT,
                due_at TEXT,
                completed_at TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                idempotency_key TEXT,
                payload_hash TEXT,
                CHECK(version >= 1)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS compliance_review_events (
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
                FOREIGN KEY(compliance_review_id)
                    REFERENCES compliance_reviews(compliance_review_id)
                    ON DELETE RESTRICT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS compliance_review_relationships (
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
                FOREIGN KEY(compliance_review_id)
                    REFERENCES compliance_reviews(compliance_review_id)
                    ON DELETE RESTRICT
            )
            """
        )
        statements = [
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_compliance_reviews_idempotency
            ON compliance_reviews(idempotency_key)
            WHERE idempotency_key IS NOT NULL
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_compliance_review_events_idempotency
            ON compliance_review_events(compliance_review_id, idempotency_key)
            WHERE idempotency_key IS NOT NULL
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_compliance_review_relationship_active
            ON compliance_review_relationships(
                compliance_review_id,
                relationship_type,
                related_record_type,
                related_record_id,
                direction,
                status
            )
            WHERE status = 'active'
            """,
            "CREATE INDEX IF NOT EXISTS idx_compliance_reviews_firm_status ON compliance_reviews(firm_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_reviews_review_type ON compliance_reviews(review_type)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_reviews_requirement ON compliance_reviews(governing_requirement_type, governing_requirement_id)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_reviews_source ON compliance_reviews(source_type, source_id)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_reviews_context ON compliance_reviews(firm_id, institution_id, trust_id, matter_id, deployment_key)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_review_events_review ON compliance_review_events(compliance_review_id, event_sequence)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_review_events_type ON compliance_review_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_review_events_created ON compliance_review_events(created_at)",
        ]
        for statement in statements:
            cur.execute(statement)
        if owns_connection:
            conn.commit()
        return {"ok": True, "status": "verified"}
    except Exception as exc:
        if owns_connection:
            conn.rollback()
        return {"ok": False, "status": "failed", "message": exc.__class__.__name__}
    finally:
        if owns_connection:
            conn.close()


if __name__ == "__main__":
    result = ensure_compliance_review_foundation()
    print(f"compliance_review_foundation: {result['status']}")
    if not result.get("ok"):
        raise SystemExit(1)
