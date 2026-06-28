"""
Institutional Execution Object Model Service.

IEL-5 makes execution artifacts first-class institutional objects:
signature, seal, witness, notary, certificate, recording, verification,
evidence_package, audit_trail, and execution_session.
"""

from database.db import get_connection, ensure_execution_object_model_tables


EXECUTION_OBJECT_TYPES = {
    "execution_session": "Execution Session",
    "signature": "Signature",
    "seal": "Seal",
    "witness": "Witness",
    "notary": "Notary",
    "certificate": "Certificate",
    "recording": "Recording",
    "verification": "Verification",
    "evidence_package": "Evidence Package",
    "audit_trail": "Audit Trail",
}


def _next_execution_object_id(cur, object_type):
    prefix = {
        "execution_session": "EXOBJ-SESSION",
        "signature": "EXOBJ-SIG",
        "seal": "EXOBJ-SEAL",
        "witness": "EXOBJ-WIT",
        "notary": "EXOBJ-NOT",
        "certificate": "EXOBJ-CERT",
        "recording": "EXOBJ-REC",
        "verification": "EXOBJ-VER",
        "evidence_package": "EXOBJ-EVID",
        "audit_trail": "EXOBJ-AUD",
    }.get(object_type, "EXOBJ")

    row = cur.execute(
        "SELECT COUNT(*) FROM institutional_execution_objects WHERE object_type = ?",
        (object_type,),
    ).fetchone()

    count = int(row[0] or 0) + 1
    return f"{prefix}-{count:06d}"


def create_execution_object(
    object_type,
    object_label,
    parent_execution_id=None,
    linked_object_type=None,
    linked_object_id=None,
    created_by=None,
    notes=None,
):
    ensure_execution_object_model_tables()
    conn = get_connection()
    cur = conn.cursor()

    if object_type not in EXECUTION_OBJECT_TYPES:
        raise ValueError(f"Unsupported execution object type: {object_type}")

    execution_object_id = _next_execution_object_id(cur, object_type)

    cur.execute(
        """
        INSERT INTO institutional_execution_objects (
            execution_object_id,
            object_type,
            object_label,
            parent_execution_id,
            linked_object_type,
            linked_object_id,
            created_by,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            execution_object_id,
            object_type,
            object_label,
            parent_execution_id,
            linked_object_type,
            linked_object_id,
            created_by,
            notes,
        ),
    )

    cur.execute(
        """
        INSERT INTO institutional_execution_object_events (
            execution_object_id,
            event_type,
            event_label,
            event_actor,
            event_notes
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            execution_object_id,
            "created",
            f"{EXECUTION_OBJECT_TYPES[object_type]} Created",
            created_by or "system",
            notes or "",
        ),
    )

    conn.commit()
    conn.close()
    return execution_object_id


def list_execution_objects_for_linked_object(linked_object_type, linked_object_id):
    ensure_execution_object_model_tables()
    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT execution_object_id, object_type, object_label, status, verification_status, created_at
        FROM institutional_execution_objects
        WHERE linked_object_type = ? AND linked_object_id = ?
        ORDER BY created_at DESC
        """,
        (linked_object_type, linked_object_id),
    ).fetchall()

    conn.close()

    return [
        {
            "execution_object_id": r[0],
            "object_type": r[1],
            "object_type_label": EXECUTION_OBJECT_TYPES.get(r[1], r[1]),
            "object_label": r[2],
            "status": r[3],
            "verification_status": r[4],
            "created_at": r[5],
            "url": f"/objects/execution_object/{r[0]}",
        }
        for r in rows
    ]


def get_execution_object_dashboard_context(execution_object_id):
    ensure_execution_object_model_tables()
    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()

    row = cur.execute(
        """
        SELECT execution_object_id, object_type, object_label, parent_execution_id,
               linked_object_type, linked_object_id, status, version_label,
               hash_value, verification_status, created_by, created_at, retired_at, notes
        FROM institutional_execution_objects
        WHERE execution_object_id = ?
        """,
        (execution_object_id,),
    ).fetchone()

    if not row:
        conn.close()
        return {
            "object_type": "execution_object",
            "object_id": execution_object_id,
            "title": f"Execution Object {execution_object_id}",
            "status": "missing",
            "status_label": "Missing",
            "workspace_owner": "ADMINISTER",
            "summary": "Execution object was not found.",
            "identity": {},
            "lifecycle": {"status_label": "Missing", "blocked": True},
            "relationships": [],
            "events": [],
            "tasks": [],
            "evidence": [],
            "compliance": [],
            "actions": [{"label": "Execution Center", "url": "/execution"}],
            "reports": [],
            "archive": {},
            "history": [],
            "extensions": {},
        }

    keys = [
        "execution_object_id", "object_type", "object_label", "parent_execution_id",
        "linked_object_type", "linked_object_id", "status", "version_label",
        "hash_value", "verification_status", "created_by", "created_at", "retired_at", "notes"
    ]
    data = dict(zip(keys, row))

    events = cur.execute(
        """
        SELECT event_type, event_label, event_actor, event_at, event_notes
        FROM institutional_execution_object_events
        WHERE execution_object_id = ?
        ORDER BY event_at DESC
        """,
        (execution_object_id,),
    ).fetchall()

    relationships = cur.execute(
        """
        SELECT related_object_type, related_object_id, relationship_type, relationship_status, created_at, notes
        FROM institutional_execution_object_relationships
        WHERE execution_object_id = ?
        ORDER BY created_at DESC
        """,
        (execution_object_id,),
    ).fetchall()

    conn.close()

    label = EXECUTION_OBJECT_TYPES.get(data["object_type"], data["object_type"])

    return {
        "object_type": "execution_object",
        "object_id": execution_object_id,
        "title": data["object_label"] or f"{label} {execution_object_id}",
        "status": data["status"],
        "status_label": str(data["status"]).replace("_", " ").title(),
        "workspace_owner": "ADMINISTER",
        "summary": data["notes"] or f"{label} institutional execution object.",
        "identity": {
            "Execution Object ID": data["execution_object_id"],
            "Execution Object Type": label,
            "Parent Execution Session": data["parent_execution_id"] or "",
            "Linked Object": f"{data['linked_object_type'] or ''} {data['linked_object_id'] or ''}".strip(),
            "Version": data["version_label"] or "",
            "Verification": data["verification_status"] or "",
            "Hash": data["hash_value"] or "",
            "Created By": data["created_by"] or "",
            "Created": data["created_at"] or "",
        },
        "lifecycle": {
            "status_label": str(data["status"]).replace("_", " ").title(),
            "blocked": data["status"] in ["revoked", "retired", "missing"],
            "verification_status": data["verification_status"],
            "retired_at": data["retired_at"],
        },
        "relationships": [
            {
                "type": r[2],
                "label": f"{r[0]} {r[1]}",
                "status": r[3],
                "created_at": r[4],
                "notes": r[5],
            }
            for r in relationships
        ],
        "events": [
            {
                "type": e[0],
                "label": e[1],
                "actor": e[2],
                "created_at": e[3],
                "notes": e[4],
            }
            for e in events
        ],
        "tasks": [],
        "evidence": [],
        "compliance": [],
        "actions": [
            {"label": "Execution Center", "url": "/execution"},
            {"label": "ADMINISTER Workspace", "url": "/admin/workspace/administer"},
        ],
        "reports": [],
        "archive": {},
        "history": [],
        "extensions": {"execution_object": data},
    }
