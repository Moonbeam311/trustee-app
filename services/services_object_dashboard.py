"""
Universal Institutional Object Dashboard Builder.

Initial implementation target: Matter.
This is intentionally read-only and additive.
Legacy matter routes remain preserved.
"""

from database.db import get_connection


def _empty_context(object_type, object_id):
    return {
        "object_type": object_type,
        "object_id": object_id,
        "title": f"{object_type.title()} {object_id}",
        "status": "review",
        "status_label": "Review",
        "workspace_owner": "ADMINISTER",
        "summary": "",
        "identity": {},
        "lifecycle": {
            "current_status": "review",
            "status_label": "Review",
            "allowed_transitions": [],
            "blocked": False,
            "blockers": [],
            "last_transition_event_id": "",
        },
        "relationships": [],
        "events": [],
        "tasks": [],
        "evidence": [],
        "compliance": [],
        "actions": [],
        "reports": [],
        "archive": {
            "archive_status": "Not assessed",
            "evidence_count": 0,
            "custody_events": 0,
            "exports": [],
            "integrity_alerts": [],
        },
        "history": [],
        "extensions": {},
    }


def _row_to_dict(row):
    if row is None:
        return None
    try:
        return dict(row)
    except Exception:
        return row


def build_matter_dashboard_context(matter_id):
    ctx = _empty_context("matter", matter_id)

    try:
        conn = get_connection()
        conn.row_factory = getattr(conn, "row_factory", None) or conn.row_factory
        cur = conn.cursor()

        row = cur.execute(
            "SELECT * FROM matters WHERE matter_id = ? OR id = ? LIMIT 1",
            (matter_id, matter_id),
        ).fetchone()

        matter = _row_to_dict(row)

        if not matter:
            ctx["title"] = f"Matter {matter_id}"
            ctx["summary"] = "Matter record was not found. Legacy route remains preserved."
            ctx["lifecycle"]["blocked"] = True
            ctx["lifecycle"]["blockers"].append("Matter record not found.")
            return ctx

        title = (
            matter.get("matter_title")
            or matter.get("title")
            or matter.get("name")
            or f"Matter {matter_id}"
        )

        status = (
            matter.get("status")
            or matter.get("matter_status")
            or matter.get("governance_status")
            or "active"
        )

        ctx.update({
            "title": title,
            "status": str(status).lower().replace(" ", "_"),
            "status_label": str(status).replace("_", " ").title(),
            "summary": matter.get("purpose") or matter.get("description") or "",
            "identity": {
                "name": title,
                "display_id": matter.get("matter_id") or matter.get("id") or matter_id,
                "created_at": matter.get("created_at") or "",
                "updated_at": matter.get("updated_at") or "",
                "created_by": matter.get("created_by") or "",
                "owner": matter.get("owner") or matter.get("assigned_to") or "",
                "firm_id": matter.get("firm_id") or "",
                "jurisdiction": matter.get("jurisdiction") or "",
            },
            "lifecycle": {
                "current_status": str(status).lower().replace(" ", "_"),
                "status_label": str(status).replace("_", " ").title(),
                "allowed_transitions": [],
                "blocked": False,
                "blockers": [],
                "last_transition_event_id": "",
            },
            "extensions": {
                "matter": matter,
            },
        })

        # Best-effort related event lookup. Do not fail dashboard if table differs.
        try:
            event_rows = cur.execute(
                "SELECT * FROM matter_events WHERE matter_id = ? ORDER BY created_at DESC LIMIT 20",
                (matter_id,),
            ).fetchall()
            ctx["events"] = [_row_to_dict(r) for r in event_rows]
        except Exception:
            ctx["events"] = []

        try:
            rel_rows = cur.execute(
                "SELECT * FROM matter_relationships WHERE matter_id = ? ORDER BY created_at DESC LIMIT 20",
                (matter_id,),
            ).fetchall()
            ctx["relationships"] = [_row_to_dict(r) for r in rel_rows]
        except Exception:
            ctx["relationships"] = []

        ctx["actions"] = [
            {"label": "Legacy Matter Detail", "url": f"/matters/{matter_id}", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
            {"label": "Matter Operations", "url": "/matters", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
            {"label": "ADMINISTER Workspace", "url": "/admin/workspace/administer", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
        ]

        return ctx

    except Exception as exc:
        ctx["summary"] = f"Dashboard context build failed safely: {exc}"
        ctx["lifecycle"]["blocked"] = True
        ctx["lifecycle"]["blockers"].append(str(exc))
        return ctx


def build_object_dashboard_context(object_type, object_id):
    object_type = (object_type or "").lower().strip()

    if object_type == "matter":
        return build_matter_dashboard_context(object_id)

    ctx = _empty_context(object_type or "object", object_id)
    ctx["summary"] = "Universal dashboard support for this object type has not been implemented yet."
    ctx["lifecycle"]["blocked"] = True
    ctx["lifecycle"]["blockers"].append("Object type not implemented.")
    return ctx
