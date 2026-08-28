"""V3-MOD-WLH-P03 — Work & Learning Hub tailored-program foundation.

Tailored programs, goals, alternatives, scenarios, and revisions are protected
working artifacts. They do not become governed institutional records merely
because they are created, edited, compared, revised, or displayed.

V3-MOD-WLH-P03B.1 locks:
- one workspace may contain multiple tailored programs;
- current program state is editable working material;
- revision snapshots are explicit and append-only;
- a revision snapshot does not mean approved, verified, governed, promoted,
  or authoritative.
"""

from database.db import get_connection
from datetime import datetime, timezone
import json
import uuid

from services.guide_foundation import GENEALOGY_EVIDENCE_STATES


PROGRAM_STATUSES = (
    "draft",
    "developing",
    "ready_for_review",
    "closed",
)

ITEM_STATUSES = (
    "active",
    "inactive",
)

SCENARIO_STATUSES = (
    "draft",
    "tested",
    "retired",
)

# P04 owns working issue records inside the Work & Learning Hub.
# The evidence-state vocabulary is reused from the Guide foundation while
# persistence and lifecycle ownership remain with the tailored program.
ISSUE_TYPES = (
    "assumption",
    "gap",
    "conflict",
    "unresolved_issue",
)

ISSUE_STATUSES = (
    "open",
    "resolved",
    "dismissed",
)

ISSUE_EVIDENCE_STATES = tuple(GENEALOGY_EVIDENCE_STATES)


# P05 owns source/reference attribution for tailored-program working
# material. These values classify the reference relationship only.
# They do not verify the referenced material or change P04 evidence
# state.
SOURCE_REFERENCE_TYPES = (
    "document_reference",
    "governance_reference",
    "external_reference",
    "other_reference",
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id(prefix):
    return prefix + "-" + uuid.uuid4().hex[:10].upper()


def ensure_work_learning_program_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_programs (
            program_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            title TEXT NOT NULL,
            purpose TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_programs_workspace
        ON hub_programs (workspace_id, firm_id, owner_id)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_program_goals (
            goal_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            goal_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_program_goals_program
        ON hub_program_goals (program_id)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_program_alternatives (
            alternative_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_program_alternatives_program
        ON hub_program_alternatives (program_id)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_program_scenarios (
            scenario_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            title TEXT NOT NULL,
            scenario_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_program_scenarios_program
        ON hub_program_scenarios (program_id)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_program_issues (
            issue_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            statement TEXT NOT NULL,
            evidence_state TEXT NOT NULL DEFAULT 'unresolved',
            status TEXT NOT NULL DEFAULT 'open',
            resolution_note TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_program_issues_program
        ON hub_program_issues (program_id, status, created_at)
    """)

    # P05 source/reference attribution is a relationship layer owned
    # by the tailored Program. Firm and owner scope remain canonical
    # on hub_programs rather than being duplicated here.
    #
    # issue_id == "" means the reference applies to the Program root.
    # A non-empty issue_id identifies one P04 working issue inside the
    # same scoped Program.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_program_source_references (
            source_reference_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            issue_id TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL,
            source_reference TEXT NOT NULL,
            source_label TEXT,
            source_notes TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(
                program_id,
                issue_id,
                source_type,
                source_reference
            )
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
            idx_hub_program_source_references_program
        ON hub_program_source_references (
            program_id,
            issue_id,
            created_at
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hub_program_revisions (
            revision_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            revision_number INTEGER NOT NULL,
            snapshot_json TEXT NOT NULL,
            revision_note TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(program_id, revision_number)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_hub_program_revisions_program
        ON hub_program_revisions (program_id, revision_number)
    """)

    conn.commit()
    conn.close()


def create_hub_program(
    *,
    workspace_id,
    firm_id,
    owner_id,
    title,
    purpose,
    created_by,
):
    title = (title or "").strip()
    if not title:
        raise ValueError("program_title_required")

    now = _now()
    program_id = _id("PRG")

    conn = get_connection()
    conn.execute("""
        INSERT INTO hub_programs (
            program_id, workspace_id, firm_id, owner_id,
            title, purpose, status,
            created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
    """, (
        program_id,
        workspace_id,
        firm_id,
        owner_id,
        title,
        (purpose or "").strip() or None,
        created_by,
        now,
        now,
    ))
    conn.commit()
    conn.close()
    return program_id


def get_hub_program(*, program_id, firm_id, owner_id):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    row = conn.execute("""
        SELECT *
        FROM hub_programs
        WHERE program_id = ?
          AND firm_id = ?
          AND owner_id = ?
    """, (
        program_id,
        firm_id,
        owner_id,
    )).fetchone()
    conn.close()
    return dict(row) if row else None


def get_hub_programs_for_workspace(*, workspace_id, firm_id, owner_id):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_programs
        WHERE workspace_id = ?
          AND firm_id = ?
          AND owner_id = ?
        ORDER BY created_at, program_id
    """, (
        workspace_id,
        firm_id,
        owner_id,
    )).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_hub_program(
    *,
    program_id,
    firm_id,
    owner_id,
    title,
    purpose,
    status,
):
    if status not in PROGRAM_STATUSES:
        raise ValueError("invalid_program_status")

    title = (title or "").strip()
    if not title:
        raise ValueError("program_title_required")

    conn = get_connection()
    cur = conn.execute("""
        UPDATE hub_programs
        SET title = ?,
            purpose = ?,
            status = ?,
            updated_at = ?
        WHERE program_id = ?
          AND firm_id = ?
          AND owner_id = ?
    """, (
        title,
        (purpose or "").strip() or None,
        status,
        _now(),
        program_id,
        firm_id,
        owner_id,
    ))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return bool(changed)


def _program_available(*, program_id, firm_id, owner_id):
    return bool(get_hub_program(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ))


def create_program_goal(
    *,
    program_id,
    firm_id,
    owner_id,
    goal_text,
    created_by,
):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        raise ValueError("program_not_available_in_context")

    goal_text = (goal_text or "").strip()
    if not goal_text:
        raise ValueError("goal_text_required")

    goal_id = _id("GOAL")
    now = _now()

    conn = get_connection()
    conn.execute("""
        INSERT INTO hub_program_goals (
            goal_id, program_id, goal_text, status,
            created_by, created_at, updated_at
        ) VALUES (?, ?, ?, 'active', ?, ?, ?)
    """, (
        goal_id,
        program_id,
        goal_text,
        created_by,
        now,
        now,
    ))
    conn.commit()
    conn.close()
    return goal_id


def get_program_goals(*, program_id, firm_id, owner_id):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_program_goals
        WHERE program_id = ?
        ORDER BY created_at, goal_id
    """, (program_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_program_alternative(
    *,
    program_id,
    firm_id,
    owner_id,
    title,
    description,
    created_by,
):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        raise ValueError("program_not_available_in_context")

    title = (title or "").strip()
    if not title:
        raise ValueError("alternative_title_required")

    alternative_id = _id("ALT")
    now = _now()

    conn = get_connection()
    conn.execute("""
        INSERT INTO hub_program_alternatives (
            alternative_id, program_id, title, description,
            status, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?)
    """, (
        alternative_id,
        program_id,
        title,
        (description or "").strip() or None,
        created_by,
        now,
        now,
    ))
    conn.commit()
    conn.close()
    return alternative_id


def get_program_alternatives(*, program_id, firm_id, owner_id):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_program_alternatives
        WHERE program_id = ?
        ORDER BY created_at, alternative_id
    """, (program_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_program_scenario(
    *,
    program_id,
    firm_id,
    owner_id,
    title,
    scenario_text,
    created_by,
):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        raise ValueError("program_not_available_in_context")

    title = (title or "").strip()
    scenario_text = (scenario_text or "").strip()

    if not title:
        raise ValueError("scenario_title_required")
    if not scenario_text:
        raise ValueError("scenario_text_required")

    scenario_id = _id("SCN")
    now = _now()

    conn = get_connection()
    conn.execute("""
        INSERT INTO hub_program_scenarios (
            scenario_id, program_id, title, scenario_text,
            status, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'draft', ?, ?, ?)
    """, (
        scenario_id,
        program_id,
        title,
        scenario_text,
        created_by,
        now,
        now,
    ))
    conn.commit()
    conn.close()
    return scenario_id


def get_program_scenarios(*, program_id, firm_id, owner_id):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_program_scenarios
        WHERE program_id = ?
        ORDER BY created_at, scenario_id
    """, (program_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]



def create_program_issue(
    *,
    program_id,
    firm_id,
    owner_id,
    issue_type,
    statement,
    evidence_state,
    created_by,
):
    """Create one non-authoritative P04 working issue."""

    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        raise ValueError("program_not_available_in_context")

    issue_type = (issue_type or "").strip().lower()
    statement = (statement or "").strip()
    evidence_state = (
        (evidence_state or "unresolved").strip().lower()
    )

    if issue_type not in ISSUE_TYPES:
        raise ValueError("invalid_program_issue_type")

    if not statement:
        raise ValueError("program_issue_statement_required")

    if evidence_state not in ISSUE_EVIDENCE_STATES:
        raise ValueError("invalid_program_issue_evidence_state")

    issue_id = _id("ISS")
    now = _now()

    conn = get_connection()
    conn.execute("""
        INSERT INTO hub_program_issues (
            issue_id,
            program_id,
            issue_type,
            statement,
            evidence_state,
            status,
            resolution_note,
            created_by,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, 'open', NULL, ?, ?, ?)
    """, (
        issue_id,
        program_id,
        issue_type,
        statement,
        evidence_state,
        created_by,
        now,
        now,
    ))
    conn.commit()
    conn.close()
    return issue_id


def get_program_issues(*, program_id, firm_id, owner_id):
    """Return P04 working issues only after canonical parent scope resolves."""

    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_program_issues
        WHERE program_id = ?
        ORDER BY
            CASE status
                WHEN 'open' THEN 1
                WHEN 'resolved' THEN 2
                ELSE 3
            END,
            created_at,
            issue_id
    """, (program_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_program_issue(
    *,
    issue_id,
    program_id,
    firm_id,
    owner_id,
    evidence_state,
    status,
    resolution_note,
):
    """Update only the working classification/disposition of a scoped issue."""

    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return False

    evidence_state = (
        (evidence_state or "unresolved").strip().lower()
    )
    status = (status or "").strip().lower()

    if evidence_state not in ISSUE_EVIDENCE_STATES:
        raise ValueError("invalid_program_issue_evidence_state")

    if status not in ISSUE_STATUSES:
        raise ValueError("invalid_program_issue_status")

    conn = get_connection()
    cur = conn.execute("""
        UPDATE hub_program_issues
        SET evidence_state = ?,
            status = ?,
            resolution_note = ?,
            updated_at = ?
        WHERE issue_id = ?
          AND program_id = ?
    """, (
        evidence_state,
        status,
        (resolution_note or "").strip() or None,
        _now(),
        issue_id,
        program_id,
    ))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return bool(changed)



def create_program_source_reference(
    *,
    program_id,
    firm_id,
    owner_id,
    source_type,
    source_reference,
    source_label,
    source_notes,
    issue_id,
    created_by,
):
    """Record one P05 attribution relationship.

    The tailored Program remains the canonical root. An optional P04
    issue may be identified as the working child target. Recording a
    reference does not verify the source, alter issue evidence state,
    create a governed fact, or perform promotion.
    """

    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        raise ValueError("program_not_available_in_context")

    source_type = (source_type or "").strip().lower()
    source_reference = (source_reference or "").strip()
    source_label = (source_label or "").strip() or None
    source_notes = (source_notes or "").strip() or None
    issue_id = (issue_id or "").strip()

    if source_type not in SOURCE_REFERENCE_TYPES:
        raise ValueError(
            "invalid_program_source_reference_type"
        )

    if not source_reference:
        raise ValueError(
            "program_source_reference_required"
        )

    if issue_id:
        issue_ids = {
            row["issue_id"]
            for row in get_program_issues(
                program_id=program_id,
                firm_id=firm_id,
                owner_id=owner_id,
            )
        }

        if issue_id not in issue_ids:
            raise ValueError(
                "program_source_reference_issue_not_available"
            )

    candidate_id = _id("SRC")
    now = _now()

    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO hub_program_source_references (
            source_reference_id,
            program_id,
            issue_id,
            source_type,
            source_reference,
            source_label,
            source_notes,
            created_by,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        program_id,
        issue_id,
        source_type,
        source_reference,
        source_label,
        source_notes,
        created_by,
        now,
    ))

    row = conn.execute("""
        SELECT source_reference_id
        FROM hub_program_source_references
        WHERE program_id = ?
          AND issue_id = ?
          AND source_type = ?
          AND source_reference = ?
        LIMIT 1
    """, (
        program_id,
        issue_id,
        source_type,
        source_reference,
    )).fetchone()

    conn.commit()
    conn.close()

    if not row:
        raise RuntimeError(
            "program_source_reference_identity_not_found"
        )

    return row[0]


def get_program_source_references(
    *,
    program_id,
    firm_id,
    owner_id,
):
    """Return P05 references only after canonical Program scope resolves."""

    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    rows = conn.execute("""
        SELECT
            r.source_reference_id,
            r.program_id,
            r.issue_id,
            r.source_type,
            r.source_reference,
            r.source_label,
            r.source_notes,
            r.created_by,
            r.created_at,
            i.issue_type,
            i.statement AS issue_statement
        FROM hub_program_source_references AS r
        LEFT JOIN hub_program_issues AS i
          ON i.issue_id = r.issue_id
         AND i.program_id = r.program_id
        WHERE r.program_id = ?
        ORDER BY
            r.created_at,
            r.source_reference_id
    """, (program_id,)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def build_program_snapshot(*, program_id, firm_id, owner_id):
    program = get_hub_program(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    )
    if not program:
        raise ValueError("program_not_available_in_context")

    return {
        "program": program,
        "goals": get_program_goals(
            program_id=program_id,
            firm_id=firm_id,
            owner_id=owner_id,
        ),
        "alternatives": get_program_alternatives(
            program_id=program_id,
            firm_id=firm_id,
            owner_id=owner_id,
        ),
        "scenarios": get_program_scenarios(
            program_id=program_id,
            firm_id=firm_id,
            owner_id=owner_id,
        ),
        "issues": get_program_issues(
            program_id=program_id,
            firm_id=firm_id,
            owner_id=owner_id,
        ),
        "source_references": get_program_source_references(
            program_id=program_id,
            firm_id=firm_id,
            owner_id=owner_id,
        ),
    }


def create_program_revision(
    *,
    program_id,
    firm_id,
    owner_id,
    revision_note,
    created_by,
):
    snapshot = build_program_snapshot(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    )

    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(MAX(revision_number), 0)
        FROM hub_program_revisions
        WHERE program_id = ?
    """, (program_id,)).fetchone()

    revision_number = int(row[0] or 0) + 1
    revision_id = _id("REV")

    conn.execute("""
        INSERT INTO hub_program_revisions (
            revision_id,
            program_id,
            revision_number,
            snapshot_json,
            revision_note,
            created_by,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        revision_id,
        program_id,
        revision_number,
        json.dumps(snapshot, sort_keys=True),
        (revision_note or "").strip() or None,
        created_by,
        _now(),
    ))
    conn.commit()
    conn.close()
    return revision_id


def get_program_revisions(*, program_id, firm_id, owner_id):
    if not _program_available(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    ):
        return []

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT *
        FROM hub_program_revisions
        WHERE program_id = ?
        ORDER BY revision_number
    """, (program_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
