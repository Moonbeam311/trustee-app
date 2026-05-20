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
