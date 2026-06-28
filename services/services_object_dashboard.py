from services.services_execution_objects import get_execution_object_dashboard_context, list_execution_objects_for_linked_object
"""
Universal Institutional Object Dashboard Builder.

Initial implementation target: Matter.
This is intentionally read-only and additive.
Legacy matter routes remain preserved.
"""

from database.db import get_connection
from services.services_object_presentation import present_context


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

        relationship_count = len(ctx.get("relationships", []))
        verified_relationships = sum(
            1 for r in ctx.get("relationships", [])
            if str(r.get("verification_status", "")).lower() == "verified"
        )
        active_relationships = sum(
            1 for r in ctx.get("relationships", [])
            if str(r.get("status", "")).lower() == "active"
        )

        recent_event = ctx["events"][0] if ctx.get("events") else {}
        risk_events = [
            e for e in ctx.get("events", [])
            if "risk" in str(e.get("event_type", "")).lower()
        ]
        governance_events = [
            e for e in ctx.get("events", [])
            if "governance" in str(e.get("event_type", "")).lower()
        ]

        risk_status = "Not Assessed"
        if risk_events:
            risk_status = risk_events[0].get("description", "Risk event recorded.")

        governance_status = "No governance events loaded."
        if governance_events:
            governance_status = governance_events[0].get("event_type", "Governance event recorded.")

        relationship_status = "No relationships loaded."
        if relationship_count:
            relationship_status = f"{active_relationships}/{relationship_count} active; {verified_relationships}/{relationship_count} verified."

        recommended_next_action = "Continue matter administration."
        urgency = "normal"

        if relationship_count and verified_relationships < relationship_count:
            recommended_next_action = "Review unverified matter relationships."
            urgency = "high"
        elif risk_events:
            recommended_next_action = "Review matter risk and readiness before execution."
            urgency = "medium"
        elif recent_event:
            recommended_next_action = f"Review latest event: {recent_event.get('event_type', 'Recent Event')}."
            urgency = "normal"

        ctx["extensions"]["executive_panels"] = {
            "matter_health": {
                "label": "Matter Health",
                "value": ctx.get("status_label") or "Unknown",
                "detail": ctx.get("summary") or "No matter summary available.",
            },
            "relationship_status": {
                "label": "Relationship Status",
                "value": relationship_status,
                "detail": "Matter relationship verification and link validation summary.",
            },
            "governance_status": {
                "label": "Governance Status",
                "value": governance_status,
                "detail": "Derived from matter governance events.",
            },
            "risk_readiness": {
                "label": "Risk / Readiness",
                "value": risk_status,
                "detail": "Derived from matter risk events.",
            },
            "archive_evidence": {
                "label": "Archive / Evidence",
                "value": ctx.get("archive", {}).get("archive_status", "Not assessed"),
                "detail": "Evidence and archive state will be expanded in a later integration pass.",
            },
            "recommended_next_action": {
                "label": "Recommended Next Action",
                "value": recommended_next_action,
                "detail": f"Urgency: {urgency}",
            },
        }

        ctx["execution_sessions"] = list_execution_sessions_for_object("matter", matter_id)
        ctx["execution_sessions"] = list_execution_sessions_for_object("trust", trust_id)
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



def build_trust_dashboard_context(trust_id):
    ctx = _empty_context("trust", trust_id)
    ctx["workspace_owner"] = "ADMINISTER"

    try:
        conn = get_connection()
        cur = conn.cursor()

        row = cur.execute(
            "SELECT * FROM trusts WHERE trust_id = ? LIMIT 1",
            (trust_id,),
        ).fetchone()

        trust = _row_to_dict(row)

        if not trust:
            ctx["title"] = f"Trust {trust_id}"
            ctx["summary"] = "Trust record was not found. Legacy routes remain preserved."
            ctx["lifecycle"]["blocked"] = True
            ctx["lifecycle"]["blockers"].append("Trust record not found.")
            ctx["actions"] = [
                {"label": "ADMINISTER Workspace", "url": "/admin/workspace/administer", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
            ]
            return ctx

        title = (
            trust.get("trust_name")
            or trust.get("name")
            or trust.get("title")
            or f"Trust {trust_id}"
        )

        status = (
            trust.get("status")
            or trust.get("trust_status")
            or trust.get("lifecycle_status")
            or "active"
        )

        ctx.update({
            "title": title,
            "status": str(status).lower().replace(" ", "_"),
            "status_label": str(status).replace("_", " ").title(),
            "summary": (
                trust.get("purpose")
                or trust.get("description")
                or trust.get("trust_purpose")
                or trust.get("trust_type")
                or ""
            ),
            "identity": {
                "name": title,
                "display_id": trust.get("trust_id") or trust.get("id") or trust_id,
                "created_at": trust.get("created_at") or "",
                "updated_at": trust.get("updated_at") or "",
                "created_by": trust.get("created_by") or "",
                "owner": trust.get("owner") or trust.get("trustee") or "",
                "firm_id": trust.get("firm_id") or "",
                "jurisdiction": trust.get("jurisdiction") or "",
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
                "trust": trust,
            },
        })

        # Best-effort matter relationships where this trust is linked.
        try:
            rel_rows = cur.execute(
                "SELECT * FROM matter_relationships WHERE linked_record_id = ? ORDER BY created_at DESC LIMIT 20",
                (trust_id,),
            ).fetchall()
            ctx["relationships"] = [_row_to_dict(r) for r in rel_rows]
        except Exception:
            ctx["relationships"] = []

        # Best-effort matter events where this trust is referenced.
        try:
            event_rows = cur.execute(
                "SELECT * FROM matter_events WHERE linked_record_id = ? OR linked_record_type = 'trust' ORDER BY created_at DESC LIMIT 20",
                (trust_id,),
            ).fetchall()
            ctx["events"] = [_row_to_dict(r) for r in event_rows]
        except Exception:
            ctx["events"] = []

        relationship_count = len(ctx.get("relationships", []))
        verified_relationships = sum(
            1 for r in ctx.get("relationships", [])
            if str(r.get("verification_status", "")).lower() == "verified"
        )

        recent_event = ctx["events"][0] if ctx.get("events") else {}

        recommended_next_action = "Continue trust administration."
        urgency = "normal"

        if relationship_count and verified_relationships < relationship_count:
            recommended_next_action = "Review unverified trust relationships."
            urgency = "high"
        elif not ctx.get("summary"):
            recommended_next_action = "Review trust purpose and summary fields."
            urgency = "medium"
        elif recent_event:
            recommended_next_action = f"Review latest trust-linked event: {recent_event.get('event_type', 'Recent Event')}."

        ctx["extensions"]["executive_panels"] = {
            "trust_health": {
                "label": "Trust Health",
                "value": ctx.get("status_label") or "Unknown",
                "detail": ctx.get("summary") or "No trust summary available.",
            },
            "relationship_status": {
                "label": "Relationship Status",
                "value": f"{verified_relationships}/{relationship_count} verified." if relationship_count else "No linked relationships loaded.",
                "detail": "Trust relationship verification summary.",
            },
            "funding_status": {
                "label": "Funding Status",
                "value": trust.get("funding_status") or "Not assessed",
                "detail": "Funding state will be expanded in a later integration pass.",
            },
            "execution_status": {
                "label": "Execution Status",
                "value": trust.get("execution_status") or trust.get("status") or "Not assessed",
                "detail": "Execution readiness will be expanded in a later integration pass.",
            },
            "archive_evidence": {
                "label": "Archive / Evidence",
                "value": ctx.get("archive", {}).get("archive_status", "Not assessed"),
                "detail": "Evidence and archive state will be expanded in a later integration pass.",
            },
            "recommended_next_action": {
                "label": "Recommended Next Action",
                "value": recommended_next_action,
                "detail": f"Urgency: {urgency}",
            },
        }

        ctx["actions"] = [
            {"label": "Legacy Trust Detail", "url": f"/trust/{trust_id}", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
            {"label": "Legacy Admin Dashboard", "url": "/admin", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
            {"label": "ADMINISTER Workspace", "url": "/admin/workspace/administer", "method": "GET", "requires_confirmation": False, "permission": "", "disabled": False, "disabled_reason": ""},
        ]

        return ctx

    except Exception as exc:
        ctx["summary"] = f"Trust dashboard context build failed safely: {exc}"
        ctx["lifecycle"]["blocked"] = True
        ctx["lifecycle"]["blockers"].append(str(exc))
        return ctx


def list_execution_sessions_for_object(object_type, object_id):
    try:
        from database.db import get_connection, ensure_institutional_execution_layer_tables
        ensure_institutional_execution_layer_tables()
        conn = get_connection()
        conn.row_factory = None
        cur = conn.cursor()

        rows = cur.execute("""
            SELECT execution_id, document_type, execution_status, signer_name, signer_capacity, created_at
            FROM institutional_execution_sessions
            WHERE object_type = ? AND object_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (object_type, object_id)).fetchall()

        return [
            {
                "execution_id": r[0],
                "document_type": r[1],
                "status": r[2],
                "signer_name": r[3],
                "signer_capacity": r[4],
                "created_at": r[5],
                "url": f"/execution/sessions/{r[0]}",
            }
            for r in rows
        ]
    except Exception as exc:
        return [{"execution_id": "ERROR", "document_type": "Execution lookup failed", "status": str(exc), "url": ""}]


def build_object_dashboard_context(object_type, object_id):
    if object_type == "execution_object":
        return get_execution_object_dashboard_context(object_id)

    object_type = (object_type or "").lower().strip()

    if object_type == "matter":
        return present_context(build_matter_dashboard_context(object_id))

    if object_type == "trust":
        return present_context(build_trust_dashboard_context(object_id))

    ctx = _empty_context(object_type or "object", object_id)
    ctx["summary"] = "Universal dashboard support for this object type has not been implemented yet."
    ctx["lifecycle"]["blocked"] = True
    ctx["lifecycle"]["blockers"].append("Object type not implemented.")
    return ctx
