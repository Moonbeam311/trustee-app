"""
Institutional Identity & Branding service.

Stores reusable:
- brand packages
- seals
- watermarks
- letterhead/footer styles
- digital signature profiles
"""

from database.db import get_connection, ensure_institutional_identity_branding_tables


def _next_id(prefix, table):
    ensure_institutional_identity_branding_tables()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
    count = row["c"] if hasattr(row, "keys") else row[0]
    conn.close()
    return f"{prefix}-{count + 1:06d}"


def list_brand_packages():
    ensure_institutional_identity_branding_tables()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM institutional_brand_packages
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_signature_profiles():
    ensure_institutional_identity_branding_tables()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM institutional_signature_profiles
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_brand_package(data):
    ensure_institutional_identity_branding_tables()
    brand_package_id = _next_id("BRAND", "institutional_brand_packages")

    conn = get_connection()
    conn.execute("""
        INSERT INTO institutional_brand_packages (
            brand_package_id, package_name, institution_name, firm_id,
            logo_path, seal_path, watermark_path, letterhead_style,
            footer_style, qr_style, barcode_style, color_theme,
            status, created_by, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        brand_package_id,
        data.get("package_name", ""),
        data.get("institution_name", ""),
        data.get("firm_id", ""),
        data.get("logo_path", ""),
        data.get("seal_path", ""),
        data.get("watermark_path", ""),
        data.get("letterhead_style", "v3_minimal"),
        data.get("footer_style", "fiduciary_footer"),
        data.get("qr_style", "governance_qr"),
        data.get("barcode_style", "chain_of_custody"),
        data.get("color_theme", "gold_black"),
        data.get("status", "active"),
        data.get("created_by", ""),
        data.get("notes", ""),
    ))
    conn.commit()
    conn.close()
    return brand_package_id


def create_signature_profile(data):
    ensure_institutional_identity_branding_tables()
    signature_profile_id = _next_id("SIGPRO", "institutional_signature_profiles")

    conn = get_connection()
    conn.execute("""
        INSERT INTO institutional_signature_profiles (
            signature_profile_id, person_name, person_role, firm_id,
            signature_method, signature_image_path, initials_image_path,
            typed_signature, title_block, credential_block,
            certificate_reference, status, created_by, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signature_profile_id,
        data.get("person_name", ""),
        data.get("person_role", ""),
        data.get("firm_id", ""),
        data.get("signature_method", "stored_digital_signature"),
        data.get("signature_image_path", ""),
        data.get("initials_image_path", ""),
        data.get("typed_signature", ""),
        data.get("title_block", ""),
        data.get("credential_block", ""),
        data.get("certificate_reference", ""),
        data.get("status", "active"),
        data.get("created_by", ""),
        data.get("notes", ""),
    ))
    conn.commit()
    conn.close()
    return signature_profile_id
