import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
DOC = ROOT / "docs" / "compliance_review_production_activation_plan_h6e.md"
PERMISSION_MIGRATION = ROOT / "migrations" / "add_compliance_review_permissions.py"
ACTIVATION_MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
PERMISSION_TOKEN = "H6E-TEMPORARY-PERMISSION-GOVERNANCE"
ACTIVATION_TOKEN = "H6B-TEMPORARY-ACTIVATION"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"

failures = []


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:260]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def run(args, env=None):
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=240, env=merged)


def compliance_objects(path):
    con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    try:
        return con.execute("SELECT name FROM sqlite_master WHERE lower(name) LIKE 'compliance_review%' ORDER BY name").fetchall()
    finally:
        con.close()


def main():
    doc = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    for marker in (
        "Rollback Plan",
        "Rollback triggers",
        "Preserve failed database for forensic analysis",
        "Restore verified activation backup",
        "Silent retry is prohibited",
        "rollback hash mismatch",
    ):
        check("rollback document marker: " + marker, marker in doc)

    baseline_sha = sha(DB)
    temp_root = Path(tempfile.mkdtemp(prefix="trustee_h6e_rollback_"))
    print("temporary_root=" + str(temp_root))
    inventory = []
    try:
        permission_failure = temp_root / "permission_failure.db"
        shutil.copy2(DB, permission_failure)
        permission_before = sha(permission_failure)
        proc = run(
            [sys.executable, str(PERMISSION_MIGRATION), "--database", str(permission_failure), "--apply", "--authorization-token", PERMISSION_TOKEN],
            env={"H6E_FORCE_PERMISSION_MIGRATION_FAILURE": "after_inserts"},
        )
        check("forced permission migration fails", proc.returncode != 0, proc.stdout + proc.stderr)
        check("forced permission migration rolls back", sha(permission_failure) == permission_before)

        activation_failure = temp_root / "activation_failure.db"
        shutil.copy2(DB, activation_failure)
        activation_before = sha(activation_failure)
        proc = run(
            [sys.executable, str(ACTIVATION_MIGRATION), "--database", str(activation_failure), "--apply", "--activation-token", ACTIVATION_TOKEN],
            env={"H6B_FORCE_MIGRATION_FAILURE": "after_tables"},
        )
        check("forced activation migration fails", proc.returncode != 0, proc.stdout + proc.stderr)
        check("forced activation migration leaves no schema", compliance_objects(activation_failure) == [], compliance_objects(activation_failure))
        check("forced activation migration rolls back", sha(activation_failure) == activation_before)

        bad_token = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(permission_failure), "--dry-run", "--authorization-token", "wrong"])
        check("invalid permission token refused", bad_token.returncode != 0)
        normal_refused = run([sys.executable, str(ACTIVATION_MIGRATION), "--database", str(DB), "--dry-run", "--activation-token", ACTIVATION_TOKEN])
        check("activation migration refuses normal DB", normal_refused.returncode != 0 and "trustee_app.db is refused" in (normal_refused.stdout + normal_refused.stderr))

        inventory = [(p.name, p.stat().st_size, sha(p)) for p in sorted(temp_root.glob("*.db"))]
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("temporary_database_inventory=" + repr(inventory))
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))
    check("normal DB sha preserved", sha(DB) == baseline_sha == EXPECTED_SHA, sha(DB))
    staged = run(["git", "diff", "--cached", "--name-only"])
    check("staging empty", staged.stdout.strip() == "")

    print("POST-V2-17Q-H.6E ROLLBACK PLAN AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
