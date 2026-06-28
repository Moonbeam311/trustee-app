"""
Institutional Asset Vault service.

Stores reusable institutional identity assets:
- seal images
- signature images
- initials
- logos
- watermarks
- letterhead assets
"""

from pathlib import Path
from datetime import datetime
import hashlib
from werkzeug.utils import secure_filename

from database.db import get_connection, ensure_institutional_asset_vault_tables


ASSET_ROOT = Path("storage/institutional_assets")


def _next_id(prefix, table):
    ensure_institutional_asset_vault_tables()
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
    count = row["c"] if hasattr(row, "keys") else row[0]
    conn.close()
    return f"{prefix}-{count + 1:06d}"


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def allowed_asset_type(asset_type):
    allowed = {
        "seal",
        "signature",
        "initials",
        "logo",
        "watermark",
        "letterhead",
        "footer",
        "certificate_border",
        "qr_style",
        "barcode_style",
        "other",
    }
    return asset_type if asset_type in allowed else "other"


def save_identity_asset(file_storage, data):
    ensure_institutional_asset_vault_tables()

    asset_type = allowed_asset_type((data.get("asset_type") or "other").strip())
    asset_id = _next_id("ASSET", "institutional_identity_assets")

    original_name = secure_filename(file_storage.filename or "uploaded_asset")
    safe_name = f"{asset_id}_{original_name}"

    dest_dir = ASSET_ROOT / asset_type
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / safe_name
    file_storage.save(dest)

    file_hash = _hash_file(dest)
    file_size = dest.stat().st_size

    conn = get_connection()
    conn.execute("""
        INSERT INTO institutional_identity_assets (
            asset_id, asset_type, asset_label, firm_id,
            related_object_type, related_object_id,
            file_name, file_path, mime_type, file_size,
            asset_status, asset_hash, uploaded_by, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        asset_id,
        asset_type,
        data.get("asset_label") or original_name,
        data.get("firm_id") or "FIRM-002",
        data.get("related_object_type") or "",
        data.get("related_object_id") or "",
        original_name,
        str(dest).replace("\\\\", "/"),
        file_storage.mimetype or "",
        file_size,
        "active",
        file_hash,
        data.get("uploaded_by") or "",
        data.get("notes") or "",
    ))
    conn.commit()
    conn.close()

    return asset_id


def list_identity_assets(asset_type=None):
    ensure_institutional_asset_vault_tables()
    conn = get_connection()

    if asset_type:
        rows = conn.execute("""
            SELECT * FROM institutional_identity_assets
            WHERE asset_type = ?
            ORDER BY uploaded_at DESC
        """, (asset_type,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM institutional_identity_assets
            ORDER BY uploaded_at DESC
        """).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_identity_asset(asset_id):
    ensure_institutional_asset_vault_tables()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM institutional_identity_assets WHERE asset_id = ?",
        (asset_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
