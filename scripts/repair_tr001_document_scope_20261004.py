import sqlite3
from pathlib import Path

DB = Path.home() / "HindsfootOS" / "PersonalFirm" / "database" / "personal_firm.sqlite3"
TRUST_ID = "TR-001"
DOCUMENT_IDS = ("DOC-001", "DOC-002")

con = sqlite3.connect(str(DB))
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"SQLite integrity failed: {integrity}")

    con.execute("BEGIN IMMEDIATE")

    trust = con.execute("""
        SELECT trust_id, firm_id, owner_id
        FROM trusts
        WHERE trust_id = ?
    """, (TRUST_ID,)).fetchone()

    if not trust:
        raise RuntimeError("TR-001 not found")

    firm_id = trust["firm_id"]
    owner_id = trust["owner_id"]

    if not firm_id or not owner_id:
        raise RuntimeError("TR-001 canonical scope is incomplete")

    rows = con.execute("""
        SELECT document_id, trust_id, firm_id, owner_id, file_path
        FROM documents
        WHERE document_id IN (?, ?)
        ORDER BY document_id
    """, DOCUMENT_IDS).fetchall()

    if tuple(r["document_id"] for r in rows) != DOCUMENT_IDS:
        raise RuntimeError("Expected DOC-001 and DOC-002 exactly")

    updated = 0

    for row in rows:
        if row["trust_id"] != TRUST_ID:
            raise RuntimeError(
                f'{row["document_id"]} is not linked to TR-001'
            )

        if row["firm_id"] not in (None, "", firm_id):
            raise RuntimeError(
                f'{row["document_id"]} has conflicting firm scope'
            )

        if row["owner_id"] not in (None, "", owner_id):
            raise RuntimeError(
                f'{row["document_id"]} has conflicting owner scope'
            )

        if not Path(row["file_path"]).exists():
            raise RuntimeError(
                f'{row["document_id"]} backing file is missing'
            )

        if row["firm_id"] != firm_id or row["owner_id"] != owner_id:
            con.execute("""
                UPDATE documents
                SET firm_id = ?, owner_id = ?
                WHERE document_id = ?
                  AND trust_id = ?
            """, (firm_id, owner_id, row["document_id"], TRUST_ID))
            updated += 1

    verify = con.execute("""
        SELECT document_id, trust_id, firm_id, owner_id
        FROM documents
        WHERE document_id IN (?, ?)
        ORDER BY document_id
    """, DOCUMENT_IDS).fetchall()

    for row in verify:
        if (
            row["trust_id"] != TRUST_ID
            or row["firm_id"] != firm_id
            or row["owner_id"] != owner_id
        ):
            raise RuntimeError(
                f'Post-repair verification failed for {row["document_id"]}'
            )

    con.commit()

    print("DOCUMENT_SCOPE_REPAIR=PASS")
    print("UPDATED_DOCUMENTS =", updated)
    print("CANONICAL_FIRM_ID =", firm_id)
    print("CANONICAL_OWNER_ID =", owner_id)

    for row in verify:
        print(dict(row))

except Exception:
    con.rollback()
    raise
finally:
    con.close()
