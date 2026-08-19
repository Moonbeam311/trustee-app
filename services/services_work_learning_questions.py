"""V3-MOD-WLH-P02 — Work & Learning Hub question organizer.

Questions are protected working artifacts. They do not become governed
institutional facts merely because they are created, linked to educational
material, marked resolved, or displayed by Hindsfoot OS.
"""

from database.db import get_connection
from datetime import datetime, timezone
import uuid


QUESTION_STATUSES = (
    "open",
    "researching",
    "resolved",
    "closed",
)

LEARNING_RESOURCE_TYPES = (
    "learning_article",
    "trust_type",
    "form_guide",
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def ensure_work_learning_question_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_questions (
            question_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_questions_workspace
        ON hub_questions (workspace_id, firm_id, owner_id)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_question_learning_resources (
            relationship_id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_key TEXT NOT NULL,
            added_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(question_id, resource_type, resource_key)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_question_resources_question
        ON hub_question_learning_resources (question_id)
    """)

    conn.commit()
    conn.close()


def create_hub_question(
    *,
    workspace_id,
    firm_id,
    owner_id,
    question_text,
    created_by,
):
    question_text = (question_text or "").strip()
    if not question_text:
        raise ValueError("question_text_required")

    question_id = "Q-" + uuid.uuid4().hex[:10].upper()
    now = _now()

    conn = get_connection()
    conn.execute("""
        INSERT INTO hub_questions (
            question_id, workspace_id, firm_id, owner_id,
            question_text, status, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
    """, (
        question_id,
        workspace_id,
        firm_id,
        owner_id,
        question_text,
        created_by,
        now,
        now,
    ))
    conn.commit()
    conn.close()
    return question_id


def get_hub_questions_for_workspace(*, workspace_id, firm_id, owner_id):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_questions
        WHERE workspace_id = ?
          AND firm_id = ?
          AND owner_id = ?
        ORDER BY created_at DESC, question_id
    """, (workspace_id, firm_id, owner_id)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_hub_question(*, question_id, firm_id, owner_id):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    row = conn.execute("""
        SELECT *
        FROM hub_questions
        WHERE question_id = ?
          AND firm_id = ?
          AND owner_id = ?
    """, (question_id, firm_id, owner_id)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_hub_question_status(
    *,
    question_id,
    firm_id,
    owner_id,
    status,
):
    if status not in QUESTION_STATUSES:
        raise ValueError("invalid_question_status")

    conn = get_connection()
    cur = conn.execute("""
        UPDATE hub_questions
        SET status = ?, updated_at = ?
        WHERE question_id = ?
          AND firm_id = ?
          AND owner_id = ?
    """, (
        status,
        _now(),
        question_id,
        firm_id,
        owner_id,
    ))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return bool(changed)


def add_question_learning_resource(
    *,
    question_id,
    firm_id,
    owner_id,
    resource_type,
    resource_key,
    added_by,
):
    if resource_type not in LEARNING_RESOURCE_TYPES:
        raise ValueError("invalid_learning_resource_type")

    resource_key = (resource_key or "").strip()
    if not resource_key:
        raise ValueError("resource_key_required")

    question = get_hub_question(
        question_id=question_id,
        firm_id=firm_id,
        owner_id=owner_id,
    )
    if not question:
        raise ValueError("question_not_available_in_context")

    candidate_relationship_id = "QLR-" + uuid.uuid4().hex[:10].upper()

    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO hub_question_learning_resources (
            relationship_id, question_id, resource_type,
            resource_key, added_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        candidate_relationship_id,
        question_id,
        resource_type,
        resource_key,
        added_by,
        _now(),
    ))
    conn.commit()

    row = conn.execute("""
        SELECT relationship_id
        FROM hub_question_learning_resources
        WHERE question_id = ?
          AND resource_type = ?
          AND resource_key = ?
        LIMIT 1
    """, (
        question_id,
        resource_type,
        resource_key,
    )).fetchone()

    conn.close()

    if not row:
        raise RuntimeError("question_learning_resource_identity_not_found")

    return row[0]


def get_question_learning_resources(*, question_id, firm_id, owner_id):
    question = get_hub_question(
        question_id=question_id,
        firm_id=firm_id,
        owner_id=owner_id,
    )
    if not question:
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_question_learning_resources
        WHERE question_id = ?
        ORDER BY created_at, relationship_id
    """, (question_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def remove_question_learning_resource(
    *,
    relationship_id,
    question_id,
    firm_id,
    owner_id,
):
    question = get_hub_question(
        question_id=question_id,
        firm_id=firm_id,
        owner_id=owner_id,
    )
    if not question:
        return False

    conn = get_connection()
    cur = conn.execute("""
        DELETE FROM hub_question_learning_resources
        WHERE relationship_id = ?
          AND question_id = ?
    """, (relationship_id, question_id))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return bool(changed)
