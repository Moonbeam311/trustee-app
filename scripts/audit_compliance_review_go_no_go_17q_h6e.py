import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
DOC = ROOT / "docs" / "compliance_review_production_activation_plan_h6e.md"
MANIFEST = ROOT / "config" / "compliance_review_activation_manifest.example.json"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"

failures = []


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:260]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    doc = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}

    for gate in (
        "REPOSITORY READY", "DATABASE READY", "BACKUP READY", "PERMISSIONS READY",
        "AUTHORITY READY", "MIGRATION READY", "ROLLBACK READY", "DEPLOYMENT READY",
        "AUDITS READY", "OPERATOR READY", "CERTIFICATION READY",
    ):
        check("go/no-go gate present: " + gate, gate in doc)
    for phrase in (
        "No production activation may occur unless every mandatory gate is PASS",
        "Required evidence",
        "Responsible role",
        "Blocking conditions",
        "Sign-off",
    ):
        check("go/no-go phrase: " + phrase, phrase in doc)

    check("manifest exists", MANIFEST.exists())
    check("manifest module key", manifest.get("module_key") == "compliance_reviews", manifest)
    check("manifest separates permission migration", manifest.get("permission_migration", {}).get("path") == "migrations/add_compliance_review_permissions.py", manifest)
    check("manifest separates activation migration", manifest.get("activation_migration", {}).get("path") == "migrations/activate_compliance_review_foundation.py", manifest)
    check("manifest no live token", manifest.get("token_reference") == "REFERENCE_ONLY_NO_SECRET_VALUE", manifest)

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        compliance_permissions = con.execute("SELECT permission_name FROM permissions WHERE permission_name LIKE '%compliance%'").fetchall()
        objects = con.execute("SELECT type,name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' OR lower(name) LIKE '%system_observation%'").fetchall()
    finally:
        con.close()
    check("normal DB has no compliance permissions", compliance_permissions == [], compliance_permissions)
    check("normal DB unactivated", objects == [], objects)
    check("normal DB sha preserved", sha(DB) == EXPECTED_SHA, sha(DB))
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True)
    check("staging empty", staged.stdout.strip() == "")

    print("POST-V2-17Q-H.6E GO/NO-GO AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
