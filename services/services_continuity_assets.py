from database.db import get_connection


# ===================================================
# AC-1 CONTINUITY ASSET SERVICE HELPERS
# ===================================================

CONTINUITY_CLASSIFICATIONS = [
    "financial",
    "real_property",
    "vehicle",
    "digital_asset",
    "intellectual_property",
    "heritage_asset",
    "memorial_property",
    "sacred_family_property",
    "lineage_evidence",
    "archival_record",
    "oral_history",
    "biological_keepsake",
    "continuity_critical_system",
    "cultural_artifact",
]

CUSTODY_CLASSIFICATIONS = [
    "commercial_ownership",
    "beneficial_interest",
    "custodial_stewardship",
    "memorial_custody",
    "protected_heritage_property",
    "sacred_family_property",
    "archive_custody",
    "restricted_family_stewardship",
    "continuity_preservation",
]


def get_continuity_classifications():
    return CONTINUITY_CLASSIFICATIONS


def get_custody_classifications():
    return CUSTODY_CLASSIFICATIONS


def get_property_continuity_profile(property_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            property_id,
            trust_id,
            property_name,
            property_type,
            asset_class,
            asset_subtype,
            custodian,
            continuity_classification,
            custody_classification,
            continuity_priority,
            heritage_significance,
            preservation_requirements,
            restricted_access_level,
            lineage_association,
            memorial_status,
            sacred_status,
            continuity_notes
        FROM properties
        WHERE property_id = ?
    """, (property_id,))

    row = cur.fetchone()
    conn.close()

    return row


def update_property_continuity_profile(property_id, profile_data):
    allowed_fields = {
        "continuity_classification",
        "custody_classification",
        "continuity_priority",
        "heritage_significance",
        "preservation_requirements",
        "restricted_access_level",
        "lineage_association",
        "memorial_status",
        "sacred_status",
        "continuity_notes",
    }

    updates = {
        key: value
        for key, value in profile_data.items()
        if key in allowed_fields
    }

    if not updates:
        return False

    conn = get_connection()
    cur = conn.cursor()

    assignments = ", ".join([f"{field} = ?" for field in updates.keys()])
    values = list(updates.values()) + [property_id]

    cur.execute(
        f"""
        UPDATE properties
        SET {assignments}
        WHERE property_id = ?
        """,
        values
    )

    conn.commit()
    conn.close()

    return True


def get_continuity_assets_by_trust(trust_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM properties
        WHERE trust_id = ?
        AND (
            continuity_classification IS NOT NULL
            OR custody_classification IS NOT NULL
            OR memorial_status = 1
            OR sacred_status = 1
        )
        ORDER BY continuity_priority DESC, property_id ASC
    """, (trust_id,))

    rows = cur.fetchall()
    conn.close()

    return rows


# ===================================================
# AC-1 CONTINUITY CUSTODY LOG HELPERS
# ===================================================

def get_next_custody_event_id():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS count FROM continuity_custody_log")
    count = cur.fetchone()["count"]

    conn.close()

    return f"CCL-{count + 1:04d}"


def create_continuity_custody_event(event_data):
    event_data = dict(event_data)

    event_data.setdefault("custody_event_id", get_next_custody_event_id())

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO continuity_custody_log (
            custody_event_id,
            property_id,
            trust_id,
            event_date,
            custody_action,
            from_party,
            to_party,
            acting_capacity,
            location_reference,
            supporting_document_reference,
            notes,
            recorded_by,
            firm_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_data.get("custody_event_id"),
        event_data.get("property_id"),
        event_data.get("trust_id"),
        event_data.get("event_date"),
        event_data.get("custody_action"),
        event_data.get("from_party"),
        event_data.get("to_party"),
        event_data.get("acting_capacity"),
        event_data.get("location_reference"),
        event_data.get("supporting_document_reference"),
        event_data.get("notes"),
        event_data.get("recorded_by"),
        event_data.get("firm_id"),
    ))

    conn.commit()
    conn.close()

    return event_data.get("custody_event_id")


def get_custody_events_for_property(property_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM continuity_custody_log
        WHERE property_id = ?
        ORDER BY event_date DESC, id DESC
    """, (property_id,))

    rows = cur.fetchall()
    conn.close()

    return rows


def get_custody_event_by_id(custody_event_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM continuity_custody_log
        WHERE custody_event_id = ?
    """, (custody_event_id,))

    row = cur.fetchone()
    conn.close()

    return row


# ===================================================
# AC-1 CONTINUITY ASSET READINESS SCORING
# ===================================================

def score_continuity_asset_readiness(asset, custody_events=None, evidence_profile=None):
    asset = dict(asset)
    custody_events = custody_events or []
    evidence_profile = evidence_profile or build_property_evidence_profile(asset.get("property_id"))
    evidence_count = evidence_profile.get("evidence_count", 0)

    checks = [
        {
            "key": "continuity_classification",
            "label": "Continuity classification entered",
            "passed": bool(asset.get("continuity_classification")),
            "weight": 15,
        },
        {
            "key": "custody_classification",
            "label": "Custody classification entered",
            "passed": bool(asset.get("custody_classification")),
            "weight": 15,
        },
        {
            "key": "heritage_significance",
            "label": "Heritage significance documented",
            "passed": bool(asset.get("heritage_significance")),
            "weight": 10,
        },
        {
            "key": "preservation_requirements",
            "label": "Preservation requirements documented",
            "passed": bool(asset.get("preservation_requirements")),
            "weight": 10,
        },
        {
            "key": "custodian",
            "label": "Custodian / manager identified",
            "passed": bool(asset.get("custodian")),
            "weight": 10,
        },
        {
            "key": "responsible_party",
            "label": "Responsible party identified",
            "passed": bool(asset.get("responsible_party")),
            "weight": 10,
        },
        {
            "key": "custody_log",
            "label": "At least one custody event recorded",
            "passed": len(custody_events) > 0,
            "weight": 15,
        },
        {
            "key": "supporting_evidence",
            "label": "At least one supporting evidence document or media record linked",
            "passed": evidence_count > 0,
            "weight": 10,
        },
        {
            "key": "continuity_notes",
            "label": "Continuity notes entered",
            "passed": bool(asset.get("continuity_notes")),
            "weight": 5,
        },
        {
            "key": "lineage_or_restriction",
            "label": "Lineage or restricted-access handling addressed",
            "passed": bool(asset.get("lineage_association") or asset.get("restricted_access_level")),
            "weight": 10,
        },
    ]

    earned = sum(item["weight"] for item in checks if item["passed"])
    total = sum(item["weight"] for item in checks)

    score = round((earned / total) * 100) if total else 0

    missing = [
        item["label"]
        for item in checks
        if not item["passed"]
    ]

    if score >= 85:
        status = "Ready"
    elif score >= 60:
        status = "Needs Review"
    else:
        status = "Incomplete"

    return {
        "score": score,
        "status": status,
        "earned": earned,
        "total": total,
        "checks": checks,
        "missing": missing,
    }


# ===================================================
# AC-1 CONTINUITY ASSET EVIDENCE BRIDGE HELPERS
# ===================================================

def get_evidence_documents_for_property(property_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM documents
        WHERE property_id = ?
        ORDER BY document_id ASC
    """, (property_id,))

    rows = cur.fetchall()
    conn.close()

    return rows


def get_evidence_media_for_property(property_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM media_records
        WHERE related_entity_type = 'property'
        AND related_entity_id = ?
        ORDER BY created_at DESC
    """, (property_id,))

    rows = cur.fetchall()
    conn.close()

    return rows


def build_property_evidence_profile(property_id):
    documents = [
        dict(row)
        for row in get_evidence_documents_for_property(property_id)
    ]

    media = [
        dict(row)
        for row in get_evidence_media_for_property(property_id)
    ]

    evidence_items = []

    for doc in documents:
        evidence_items.append({
            "source_type": "document",
            "evidence_id": doc.get("document_id"),
            "title": doc.get("document_title"),
            "category": doc.get("document_category"),
            "filename": doc.get("original_filename") or doc.get("stored_filename"),
            "notes": doc.get("notes"),
            "file_path": doc.get("file_path"),
        })

    for item in media:
        evidence_items.append({
            "source_type": "media",
            "evidence_id": item.get("media_id"),
            "title": item.get("description"),
            "category": item.get("category") or item.get("media_type"),
            "filename": item.get("file_path"),
            "notes": item.get("description"),
            "file_path": item.get("file_path"),
        })

    return {
        "property_id": property_id,
        "documents": documents,
        "media": media,
        "evidence_items": evidence_items,
        "evidence_count": len(evidence_items),
    }


def has_property_evidence(property_id):
    profile = build_property_evidence_profile(property_id)
    return profile["evidence_count"] > 0



# ===================================================
# AC-1 CUSTODY EVENT EVIDENCE RESOLUTION
# ===================================================

def resolve_evidence_reference(property_id, reference):
    """
    Resolve a custody event supporting_document_reference such as:
    DOCUMENT:DOC-001
    MEDIA:MED-001

    Returns a friendly evidence item dict or None.
    """
    if not reference:
        return None

    ref = str(reference).strip()

    if ":" not in ref:
        return None

    ref_type, ref_id = ref.split(":", 1)
    ref_type = ref_type.strip().lower()
    ref_id = ref_id.strip()

    profile = build_property_evidence_profile(property_id)

    for item in profile.get("evidence_items", []):
        if (
            item.get("source_type") == ref_type
            and str(item.get("evidence_id")) == ref_id
        ):
            return item

    return None


def enrich_custody_events_with_evidence(property_id, custody_events):
    enriched = []

    for event in custody_events:
        event_data = dict(event)

        evidence_item = resolve_evidence_reference(
            property_id,
            event_data.get("supporting_document_reference")
        )

        event_data["supporting_evidence"] = evidence_item

        if evidence_item:
            event_data["supporting_evidence_label"] = (
                f"{evidence_item.get('source_type', '').title()} "
                f"{evidence_item.get('evidence_id')} — "
                f"{evidence_item.get('title') or evidence_item.get('filename') or 'Untitled evidence item'}"
            )
        else:
            event_data["supporting_evidence_label"] = None

        enriched.append(event_data)

    return enriched



# ===================================================
# AC-1 EVIDENCE / CUSTODY TIMELINE HELPERS
# ===================================================

def build_property_evidence_custody_timeline(property_id):
    evidence_profile = build_property_evidence_profile(property_id)

    custody_events = enrich_custody_events_with_evidence(
        property_id,
        get_custody_events_for_property(property_id)
    )

    timeline = []

    for item in evidence_profile.get("evidence_items", []):
        timeline.append({
            "timeline_type": "evidence",
            "timeline_date": "Not dated",
            "sort_date": "",
            "title": item.get("title") or item.get("filename") or "Untitled evidence item",
            "subtitle": f"{item.get('source_type', '').title()} {item.get('evidence_id')}",
            "category": item.get("category"),
            "description": item.get("notes"),
            "reference": item.get("evidence_id"),
        })

    for event in custody_events:
        timeline.append({
            "timeline_type": "custody_event",
            "timeline_date": event.get("event_date") or "Not dated",
            "sort_date": event.get("event_date") or "",
            "title": (event.get("custody_action") or "Custody Event").replace("_", " ").title(),
            "subtitle": event.get("custody_event_id"),
            "category": event.get("acting_capacity"),
            "description": event.get("notes"),
            "reference": event.get("supporting_document_reference"),
            "resolved_evidence_label": event.get("supporting_evidence_label"),
            "from_party": event.get("from_party"),
            "to_party": event.get("to_party"),
            "location_reference": event.get("location_reference"),
            "recorded_by": event.get("recorded_by"),
        })

    timeline.sort(
        key=lambda item: (
            item.get("sort_date") or "",
            item.get("timeline_type") or "",
            item.get("subtitle") or ""
        ),
        reverse=True
    )

    return {
        "property_id": property_id,
        "timeline": timeline,
        "timeline_count": len(timeline),
        "evidence_count": evidence_profile.get("evidence_count", 0),
        "custody_event_count": len(custody_events),
    }



# ===================================================
# AC-1 TIMELINE DASHBOARD SUMMARY HELPERS
# ===================================================

def summarize_property_evidence_custody_timeline(property_id):
    profile = build_property_evidence_custody_timeline(property_id)

    timeline = profile.get("timeline", [])

    resolved_references = 0
    unresolved_references = 0

    for item in timeline:
        if item.get("timeline_type") != "custody_event":
            continue

        reference = item.get("reference")

        if not reference:
            continue

        if item.get("resolved_evidence_label"):
            resolved_references += 1
        else:
            unresolved_references += 1

    return {
        "timeline_count": profile.get("timeline_count", 0),
        "evidence_count": profile.get("evidence_count", 0),
        "custody_event_count": profile.get("custody_event_count", 0),
        "resolved_references": resolved_references,
        "unresolved_references": unresolved_references,
    }



# ===================================================
# AC-1 CUSTODY EVENT REFERENCE UPDATE HELPER
# ===================================================

def update_custody_event_supporting_reference(custody_event_id, supporting_document_reference):
    """
    Update an existing custody event so a manual reference can be converted
    into a linked evidence reference such as DOCUMENT:DOC-001 or MEDIA:MED-001.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE continuity_custody_log
        SET supporting_document_reference = ?
        WHERE custody_event_id = ?
    """, (
        supporting_document_reference,
        custody_event_id
    ))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    return updated > 0



# ===================================================
# AC-1 RESOLUTION QUEUE HELPERS
# ===================================================

def build_property_resolution_queue(property_id):
    custody_events = enrich_custody_events_with_evidence(
        property_id,
        get_custody_events_for_property(property_id)
    )

    unresolved = []

    for event in custody_events:
        reference = event.get("supporting_document_reference")

        if not reference:
            continue

        if event.get("supporting_evidence_label"):
            continue

        unresolved.append(event)

    evidence_profile = build_property_evidence_profile(property_id)

    unresolved_count = len(unresolved)

    return {
        "property_id": property_id,
        "unresolved_events": unresolved,
        "unresolved_count": unresolved_count,
        "evidence_count": evidence_profile.get("evidence_count", 0),
        "evidence_items": evidence_profile.get("evidence_items", []),
        "resolution_status": "Clean" if unresolved_count == 0 else "Cleanup Needed",
        "archive_badge": "Resolution Archive Ready" if unresolved_count == 0 else "Resolution Cleanup Open",
    }



# ===================================================
# AC-2 ASSET CONTINUITY ARCHIVE / PACKET FOUNDATION
# ===================================================

def build_asset_continuity_archive_packet(property_id):
    evidence_profile = build_property_evidence_profile(property_id)
    timeline_profile = build_property_evidence_custody_timeline(property_id)
    timeline_summary = summarize_property_evidence_custody_timeline(property_id)
    queue_profile = build_property_resolution_queue(property_id)

    custody_events = [
        dict(event)
        for event in get_custody_events_for_property(property_id)
    ]

    packet_items = [
        {
            "packet_item_id": "AC2-001",
            "title": "Continuity Asset Detail Report",
            "description": "Continuity classification, custody classification, preservation notes, and readiness audit.",
            "route": f"/property/{property_id}/continuity/pdf",
            "status": "available",
            "packet_section": "Core Reports",
        },
        {
            "packet_item_id": "AC2-002",
            "title": "Continuity Chain-of-Custody Report",
            "description": "Custody event history and evidence resolution details.",
            "route": f"/property/{property_id}/custody-log/pdf",
            "status": "available",
            "packet_section": "Core Reports",
        },
        {
            "packet_item_id": "AC2-003",
            "title": "Evidence / Custody Timeline Report",
            "description": "Combined timeline of evidence records and custody events.",
            "route": f"/property/{property_id}/timeline/pdf",
            "status": "available",
            "packet_section": "Core Reports",
        },
        {
            "packet_item_id": "AC2-004",
            "title": "Evidence Resolution Queue Report",
            "description": "Unresolved/manual custody references and available evidence options.",
            "route": f"/property/{property_id}/resolution-queue/pdf",
            "status": "available",
            "packet_section": "Resolution Reports",
        },
        {
            "packet_item_id": "AC2-005",
            "title": "AC-1 Final Audit Snapshot / Completion Report",
            "description": "Final AC-1 readiness, evidence, custody, timeline, and completion assessment.",
            "route": f"/property/{property_id}/ac1-completion-report/pdf",
            "status": "available",
            "packet_section": "Final Audit",
        },
    ]

    evidence_items = []

    for item in evidence_profile.get("evidence_items", []):
        evidence_items.append({
            "evidence_id": item.get("evidence_id"),
            "source_type": item.get("source_type"),
            "title": item.get("title") or item.get("filename") or "Untitled evidence item",
            "category": item.get("category"),
            "notes": item.get("notes"),
            "file_path": item.get("file_path"),
        })

    unresolved_count = queue_profile.get("unresolved_count", 0)

    return {
        "property_id": property_id,
        "packet_status": "Archive Ready" if unresolved_count == 0 else "Archive Pending Cleanup",
        "archive_badge": "Ready for AC-2 Packet Assembly" if unresolved_count == 0 else "Cleanup Required Before Final Archive",
        "packet_items": packet_items,
        "packet_item_count": len(packet_items),
        "evidence_items": evidence_items,
        "evidence_count": evidence_profile.get("evidence_count", 0),
        "custody_event_count": len(custody_events),
        "timeline_count": timeline_summary.get("timeline_count", 0),
        "resolved_references": timeline_summary.get("resolved_references", 0),
        "unresolved_references": timeline_summary.get("unresolved_references", 0),
        "resolution_status": queue_profile.get("resolution_status"),
        "resolution_archive_badge": queue_profile.get("archive_badge"),
    }



# ===================================================
# AC-2 ARCHIVE ZIP INTEGRITY HELPERS
# ===================================================

def build_archive_zip_integrity_profile(archive_packet, zip_file_names):
    zip_file_names = set(zip_file_names or [])

    expected_reports = [
        "reports/AC2_Archive_Packet_Manifest.pdf",
        "reports/AC1_Completion_Report.pdf",
        "reports/Continuity_Asset_Detail_Report.pdf",
        "reports/Continuity_Custody_Log_Report.pdf",
        "reports/Evidence_Custody_Timeline_Report.pdf",
        "reports/Evidence_Resolution_Queue_Report.pdf",
    ]

    expected_manifest_files = [
        "manifest/AC2_archive_manifest.json",
        "manifest/AC2_archive_manifest.txt",
    ]

    expected_evidence = []

    for item in archive_packet.get("evidence_items") or []:
        evidence_id = item.get("evidence_id")
        file_path = item.get("file_path")

        if not evidence_id or not file_path:
            continue

        from pathlib import Path
        source_name = Path(file_path).name
        expected_evidence.append(f"evidence/{evidence_id}_{source_name}")

    checks = []

    for expected in expected_manifest_files:
        checks.append({
            "category": "Manifest",
            "path": expected,
            "present": expected in zip_file_names,
        })

    for expected in expected_reports:
        checks.append({
            "category": "Report",
            "path": expected,
            "present": expected in zip_file_names,
        })

    for expected in expected_evidence:
        checks.append({
            "category": "Evidence",
            "path": expected,
            "present": expected in zip_file_names,
        })

    missing_items = [
        check
        for check in checks
        if not check.get("present")
    ]

    included_items = [
        check
        for check in checks
        if check.get("present")
    ]

    extra_items = sorted([
        name for name in zip_file_names
        if name not in {check.get("path") for check in checks}
    ])

    return {
        "expected_count": len(checks),
        "included_count": len(included_items),
        "missing_count": len(missing_items),
        "extra_count": len(extra_items),
        "integrity_status": "Complete" if not missing_items else "Incomplete",
        "checks": checks,
        "missing_items": missing_items,
        "included_items": included_items,
        "extra_items": extra_items,
        "zip_file_names": sorted(zip_file_names),
    }
