from datetime import datetime
import json

from database.db import get_connection, ensure_certificate_event_bus_table


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _next_bus_event_id():
    ensure_certificate_event_bus_table()

    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute("SELECT COUNT(*) AS count FROM certificate_event_bus").fetchone()

    conn.close()

    count = row["count"] if hasattr(row, "keys") else row[0]
    return f"CBUS-{count + 1:06d}"


def emit_certificate_event(
    event_name,
    certification_id=None,
    certificate_type=None,
    event_category="certificate",
    event_status=None,
    event_summary=None,
    event_payload=None,
    related_object_type=None,
    related_object_id=None,
    actor="system",
    authority=None,
    source_engine="Institutional Certificate API",
    source_route=None,
    severity="info",
):
    """
    Append-only event emission for institutional certificate activity.
    """
    ensure_certificate_event_bus_table()

    bus_event_id = _next_bus_event_id()
    now = _now()

    payload_text = None
    if event_payload is not None:
        payload_text = json.dumps(event_payload, default=str)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO certificate_event_bus (
            bus_event_id,
            certification_id,
            certificate_type,
            event_category,
            event_name,
            event_status,
            event_summary,
            event_payload,
            related_object_type,
            related_object_id,
            actor,
            authority,
            source_engine,
            source_route,
            severity,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bus_event_id,
        certification_id,
        certificate_type,
        event_category,
        event_name,
        event_status,
        event_summary,
        payload_text,
        related_object_type,
        related_object_id,
        actor,
        authority,
        source_engine,
        source_route,
        severity,
        now,
    ))

    conn.commit()

    row = cur.execute("""
        SELECT *
        FROM certificate_event_bus
        WHERE bus_event_id = ?
    """, (bus_event_id,)).fetchone()

    conn.close()

    return dict(row) if row else None


def list_certificate_bus_events(certification_id=None, certificate_type=None, limit=200):
    ensure_certificate_event_bus_table()

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM certificate_event_bus WHERE 1=1"
    params = []

    if certification_id:
        query += " AND certification_id = ?"
        params.append(certification_id)

    if certificate_type:
        query += " AND certificate_type = ?"
        params.append(certificate_type)

    query += " ORDER BY created_at DESC, bus_event_id DESC LIMIT ?"
    params.append(limit)

    rows = cur.execute(query, params).fetchall()

    conn.close()

    output = []
    for row in rows:
        d = dict(row)
        if d.get("event_payload"):
            try:
                d["event_payload"] = json.loads(d["event_payload"])
            except Exception:
                pass
        output.append(d)

    return output


def certificate_event_bus_summary():
    ensure_certificate_event_bus_table()

    conn = get_connection()
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) AS count FROM certificate_event_bus").fetchone()["count"]
    warnings = cur.execute("SELECT COUNT(*) AS count FROM certificate_event_bus WHERE severity = 'warning'").fetchone()["count"]
    errors = cur.execute("SELECT COUNT(*) AS count FROM certificate_event_bus WHERE severity = 'error'").fetchone()["count"]

    by_type_rows = cur.execute("""
        SELECT COALESCE(certificate_type, 'Unknown') AS certificate_type, COUNT(*) AS count
        FROM certificate_event_bus
        GROUP BY COALESCE(certificate_type, 'Unknown')
        ORDER BY count DESC
    """).fetchall()

    by_event_rows = cur.execute("""
        SELECT event_name, COUNT(*) AS count
        FROM certificate_event_bus
        GROUP BY event_name
        ORDER BY count DESC, event_name ASC
    """).fetchall()

    conn.close()

    return {
        "total": total,
        "warnings": warnings,
        "errors": errors,
        "by_type": [dict(row) for row in by_type_rows],
        "by_event": [dict(row) for row in by_event_rows],
    }


def backfill_certificate_event_bus(actor="system"):
    """
    Seeds event bus from existing unified certificate objects.
    Idempotent enough for development: avoids duplicate seed marker events
    for same certificate/event_name pair.
    """
    from services.services_certificate_interface import list_unified_certificate_objects

    ensure_certificate_event_bus_table()

    created = []

    conn = get_connection()
    cur = conn.cursor()

    for obj in list_unified_certificate_objects():
        cert_id = obj["identity"]["certificate_id"]
        cert_type = obj["identity"]["certificate_type"]

        seed_events = [
            ("Certificate Object Indexed", obj["status"].get("certification_status"), "Certificate object indexed by ICP-5K event bus."),
            ("Certificate Verification Observed", obj["status"].get("verification_status"), "Certificate verification state observed by ICP-5K event bus."),
            ("Certificate Chain Observed", obj["status"].get("chain_status"), "Certificate chain state observed by ICP-5K event bus."),
            ("Certificate Relationships Observed", str(obj["relationships"].get("count")), "Certificate relationship graph observed by ICP-5K event bus."),
            ("Certificate Policy Observed", obj["policy"].get("policy_name"), "Certificate governance policy observed by ICP-5K event bus."),
        ]

        for event_name, event_status, summary in seed_events:
            existing = cur.execute("""
                SELECT bus_event_id
                FROM certificate_event_bus
                WHERE certification_id = ?
                  AND certificate_type = ?
                  AND event_name = ?
            """, (cert_id, cert_type, event_name)).fetchone()

            if existing:
                continue

            created.append(emit_certificate_event(
                certification_id=cert_id,
                certificate_type=cert_type,
                event_category="backfill",
                event_name=event_name,
                event_status=event_status,
                event_summary=summary,
                event_payload={
                    "certificate_id": cert_id,
                    "certificate_type": cert_type,
                    "status": obj.get("status"),
                    "policy": obj.get("policy"),
                    "relationship_count": obj.get("relationships", {}).get("count"),
                    "timeline_event_count": obj.get("timeline", {}).get("event_count"),
                },
                actor=actor,
                authority=actor,
                source_engine="ICP-5K Certificate Event Bus Backfill",
                severity="info",
            ))

    conn.close()

    return created
