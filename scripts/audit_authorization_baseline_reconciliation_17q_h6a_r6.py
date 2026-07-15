import ast
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
BACKUP_DB = ROOT / "data" / "backups" / "trustee_app_pre_role_permission_reconcile_2026-07-15.db"
MIGRATION = ROOT / "migrations" / "reconcile_role_permissions_baseline.py"
EXPECTED_SHA = "CEEDF08EAA93F1311D0E3057CD1BF84E35EADF26D40872CF7A05F5D2D560F7BA"
EXPECTED_MTIME_NS = 1784129219589180300
EXPECTED_MODIFIED = {
    "app.py",
    "database/db.py",
    "scripts/audit_compliance_review_foundation_17q_g.py",
    "scripts/audit_system_observation_foundation_17m.py",
    "services/services_compliance_reviews.py",
    "templates/ios_workspaces/compliance.html",
}
EXPECTED_UNTRACKED = {
    "migrations/reconcile_role_permissions_baseline.py",
    "scripts/audit_authorization_baseline_reconciliation_17q_h6a_r6.py",
    "scripts/audit_compliance_review_readonly_ui_17q_h.py",
    "templates/compliance_reviews/detail.html",
    "templates/compliance_reviews/registry.html",
}
failures = []


def check(name, condition, detail=""):
    prefix = "PASS" if condition else "FAIL"
    print(f"{prefix} - {name}" + (f" | {' '.join(str(detail).split())[:240]}" if detail and not condition else ""))
    if not condition:
        failures.append(name)


def run(*args, env=None, timeout=180):
    merged_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=merged_env,
    )


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def connect(path, readonly=False):
    if readonly:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    return sqlite3.connect(path)


def logical_tables(path):
    conn = connect(path, readonly=True)
    try:
        payload = []
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            rows = conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()
            payload.append((name, rows))
        return repr(payload)
    finally:
        conn.close()


def table_hashes(path):
    conn = connect(path, readonly=True)
    try:
        out = {}
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            rows = conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()
            out[name] = hashlib.sha256(repr(rows).encode("utf-8", "surrogatepass")).hexdigest()
        master = conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name,tbl_name"
        ).fetchall()
        return out, hashlib.sha256(repr(master).encode()).hexdigest()
    finally:
        conn.close()


def changed_tables(before, after):
    before_tables, before_master = before
    after_tables, after_master = after
    changed = [
        table
        for table in sorted(set(before_tables) | set(after_tables))
        if before_tables.get(table) != after_tables.get(table)
    ]
    return changed, before_master != after_master


def db_counts(path):
    conn = connect(path, readonly=True)
    try:
        return {
            "audit": tuple(conn.execute("SELECT count(*), max(id) FROM audit_log").fetchone()),
            "role_permissions": tuple(conn.execute("SELECT count(*), max(id) FROM role_permissions").fetchone()),
            "distinct_pairs": conn.execute(
                "SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)"
            ).fetchone()[0],
            "governance_relationships": conn.execute("SELECT count(*) FROM governance_relationships").fetchone()[0],
            "governance_relationship_audit_ledger": conn.execute(
                "SELECT count(*) FROM governance_relationship_audit_ledger"
            ).fetchone()[0],
            "compliance_objects": conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE lower(name) LIKE '%compliance_review%' OR lower(sql) LIKE '%compliance_review%'"
            ).fetchone()[0],
            "system_observation_objects": conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE lower(name) LIKE '%system_observation%' OR lower(sql) LIKE '%system_observation%'"
            ).fetchone()[0],
            "integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": conn.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        conn.close()


def index_columns(path):
    conn = connect(path, readonly=True)
    try:
        indexes = list(conn.execute("PRAGMA index_list(role_permissions)"))
        for index in indexes:
            if index[1] == "ux_role_permissions_role_permission":
                return index[2], [row[2] for row in conn.execute("PRAGMA index_info(ux_role_permissions_role_permission)")]
        return None, []
    finally:
        conn.close()


def git_sets():
    diff = set(run("git", "diff", "--name-only").stdout.splitlines())
    untracked = set(run("git", "ls-files", "--others", "--exclude-standard").stdout.splitlines())
    staged = set(run("git", "diff", "--cached", "--name-only").stdout.splitlines())
    status = run("git", "status", "--porcelain=v1").stdout.splitlines()
    return diff, untracked, staged, status


def app_env(db_path, temp_root):
    return {
        "DB_PATH": str(db_path),
        "UPLOAD_FOLDER": str(temp_root / "uploads"),
        "EXPORT_ROOT": str(temp_root / "exports"),
        "SECRET_KEY": "r6-temp-secret-only",
        "FLASK_ENV": "testing",
        "HOSTED_BOOTSTRAP_ADMIN_ONCE": "0",
        "HOSTED_CLEAR_LOGIN_LOCKOUT_ONCE": "0",
        "HOSTED_FIRM_SCOPE_MIGRATION_ONCE": "0",
        "HOSTED_REPAIR_ADMIN_ACCESS_ONCE": "0",
        "HOSTED_RESEED_PERMISSIONS_ONCE": "0",
        "HOSTED_TRUST_DIAGNOSTIC_ONCE": "0",
    }


def import_app_changes(db_path, temp_root):
    before = table_hashes(db_path)
    result = run(sys.executable, "-B", "-c", "import app; print('imported')", env=app_env(db_path, temp_root))
    after = table_hashes(db_path)
    changed, schema_changed = changed_tables(before, after)
    return result, changed, schema_changed


REQUEST_CHILD = r'''
import hashlib, json, os, re, sqlite3
from datetime import datetime, UTC
from app import app
DB = os.environ["DB_PATH"]
def table_hashes():
    conn = sqlite3.connect(DB)
    try:
        out = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            rows = conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()
            out[name] = hashlib.sha256(repr(rows).encode("utf-8", "surrogatepass")).hexdigest()
        return out
    finally:
        conn.close()
def changed(before, after):
    return [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
client = app.test_client()
before = table_hashes()
if LOGIN:
    response = client.get("/login")
    text = response.get_data(as_text=True)
    match = re.search(r'name=["\']_csrf_token["\'][^>]*value=["\']([^"\']+)', text) or re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']_csrf_token["\']', text)
    token = match.group(1) if match else ""
    response = client.post("/login", data={"username":"admin123","password":"admin123","_csrf_token":token}, follow_redirects=False)
else:
    if AUTH:
        with client.session_transaction() as sess:
            sess.clear()
            sess["username"] = "admin123"
            sess["role"] = "Admin"
            sess["user_role"] = "Admin"
            sess["is_master_admin"] = True
            sess["firm_id"] = "FIRM-002"
            sess["user_id"] = "USR-000001"
            sess["last_activity"] = datetime.now(UTC).timestamp()
    response = client.get(URL, follow_redirects=False)
after = table_hashes()
print(json.dumps({"status": response.status_code, "location": response.headers.get("Location"), "changed": changed(before, after)}))
'''


def request_case(db_path, temp_root, url, auth=True, login=False):
    code = REQUEST_CHILD.replace("URL", repr(url)).replace("AUTH", repr(auth)).replace("LOGIN", repr(login))
    result = run(sys.executable, "-B", "-c", code, env=app_env(db_path, temp_root))
    if result.returncode != 0 or not result.stdout.strip():
        return {"status": None, "location": None, "changed": ["SUBPROCESS_FAILED"], "stderr": result.stderr[-500:]}
    return json.loads(result.stdout.splitlines()[-1])


def migration_report(path, apply=False):
    mode = "--apply" if apply else "--dry-run"
    result = run(sys.executable, str(MIGRATION), "--database", str(path), mode)
    values = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return result, values


def main():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    protected = {
        "size": DB.stat().st_size,
        "mtime_ns": DB.stat().st_mtime_ns,
        "sha": digest(DB),
        "counts": db_counts(DB),
        "logical": logical_tables(DB),
    }
    modified, untracked, staged, _ = git_sets()
    check("phase dirty modified set bounded", modified == EXPECTED_MODIFIED, modified)
    check("phase dirty untracked set bounded", untracked == EXPECTED_UNTRACKED, untracked)
    check("staging empty", not staged, staged)
    pre_migration_normal = protected["size"] == 3096576 and protected["mtime_ns"] == EXPECTED_MTIME_NS and protected["sha"] == EXPECTED_SHA and protected["counts"]["audit"] == (513, 513) and protected["counts"]["role_permissions"][0] == 48381 and protected["counts"]["distinct_pairs"] == 25
    post_migration_normal = protected["counts"]["audit"] == (513, 513) and protected["counts"]["role_permissions"][0] == 25 and protected["counts"]["distinct_pairs"] == 25 and protected["counts"]["integrity"] == "ok" and protected["counts"]["fk"] == []
    source_db = BACKUP_DB if post_migration_normal else DB
    source_counts = db_counts(source_db) if source_db.exists() else {}
    check("protected database baseline", pre_migration_normal or post_migration_normal, protected["counts"])
    check("duplicate-heavy reconciliation source available", source_counts.get("role_permissions", (0,))[0] == 48381 and source_counts.get("distinct_pairs") == 25, source_counts)

    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    top_level_calls = [
        node for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and getattr(node.value.func, "id", None) == "ensure_role_tables"
    ]
    check("no import-time ensure_role_tables call", not top_level_calls)
    check("migration requires database argument", run(sys.executable, str(MIGRATION), "--dry-run").returncode != 0)
    check("migration requires exactly one mode", run(sys.executable, str(MIGRATION), "--database", "x").returncode != 0)

    with tempfile.TemporaryDirectory(prefix="r6_auth_audit_") as temp_name:
        temp_root = Path(temp_name)
        dry_db = temp_root / "dry_run.db"
        apply_db = temp_root / "apply.db"
        repeat_db = temp_root / "repeat.db"
        rollback_db = temp_root / "rollback.db"
        unreconciled_import_db = temp_root / "unreconciled_import.db"
        reconciled_import_db = temp_root / "reconciled_import.db"
        init_unreconciled_db = temp_root / "init_unreconciled.db"
        init_reconciled_db = temp_root / "init_reconciled.db"
        for path in [dry_db, apply_db, rollback_db, unreconciled_import_db, init_unreconciled_db]:
            shutil.copy2(source_db, path)

        before_dry = (dry_db.stat().st_size, dry_db.stat().st_mtime_ns, digest(dry_db), logical_tables(dry_db))
        dry_result, dry_values = migration_report(dry_db, apply=False)
        after_dry = (dry_db.stat().st_size, dry_db.stat().st_mtime_ns, digest(dry_db), logical_tables(dry_db))
        check("dry-run produces no changes", dry_result.returncode == 0 and before_dry == after_dry and dry_values.get("original_rows") == "48381" and dry_values.get("deletions") == "48356", dry_result.stderr)

        with closing(connect(apply_db, readonly=True)) as conn:
            original_pairs = set(conn.execute("SELECT role_name, permission_name FROM role_permissions GROUP BY role_name, permission_name"))
            original_lowest_ids = dict(conn.execute("SELECT role_name || char(31) || permission_name, min(id) FROM role_permissions GROUP BY role_name, permission_name"))
        before_apply_tables = table_hashes(apply_db)
        apply_result, _ = migration_report(apply_db, apply=True)
        after_apply_tables = table_hashes(apply_db)
        apply_changed, apply_schema_changed = changed_tables(before_apply_tables, after_apply_tables)
        with closing(connect(apply_db, readonly=True)) as conn:
            kept_pairs = set(conn.execute("SELECT role_name, permission_name FROM role_permissions"))
            kept_ids = dict(conn.execute("SELECT role_name || char(31) || permission_name, id FROM role_permissions"))
        unique_flag, unique_cols = index_columns(apply_db)
        check("apply reduces to 25 preserved pairs", apply_result.returncode == 0 and db_counts(apply_db)["role_permissions"][0] == 25 and kept_pairs == original_pairs)
        check("apply retains lowest IDs", kept_ids == original_lowest_ids)
        check("apply only changes role_permissions/schema", apply_changed == ["role_permissions"] and apply_schema_changed)
        check("unique role-permission index created", unique_flag == 1 and unique_cols == ["role_name", "permission_name"])

        shutil.copy2(apply_db, repeat_db)
        before_repeat = logical_tables(repeat_db)
        repeat_result, repeat_values = migration_report(repeat_db, apply=True)
        check("repeat apply idempotent", repeat_result.returncode == 0 and before_repeat == logical_tables(repeat_db) and repeat_values.get("deletions") == "0")

        with closing(connect(rollback_db, readonly=False)) as conn:
            conn.execute("CREATE INDEX ux_role_permissions_role_permission ON role_permissions(role_name, permission_name)")
            conn.commit()
        before_rollback = logical_tables(rollback_db)
        rollback_result, _ = migration_report(rollback_db, apply=True)
        check("rollback leaves no partial changes", rollback_result.returncode != 0 and before_rollback == logical_tables(rollback_db) and db_counts(rollback_db)["role_permissions"][0] == 48381)

        import_result, import_changed, import_schema = import_app_changes(unreconciled_import_db, temp_root)
        check("import read-only on unreconciled copy", import_result.returncode == 0 and import_changed == [] and not import_schema)
        shutil.copy2(apply_db, reconciled_import_db)
        import_result_2, import_changed_2, import_schema_2 = import_app_changes(reconciled_import_db, temp_root)
        check("import read-only on reconciled copy", import_result_2.returncode == 0 and import_changed_2 == [] and not import_schema_2)

        unsafe_init = run(
            sys.executable,
            "-B",
            "-c",
            "from database.db import ensure_role_tables; ensure_role_tables()",
            env=app_env(init_unreconciled_db, temp_root),
        )
        check("initializer fails safely on unreconciled schema", unsafe_init.returncode != 0 and db_counts(init_unreconciled_db)["role_permissions"][0] == 48381)
        shutil.copy2(apply_db, init_reconciled_db)
        init_code = "from database.db import ensure_role_tables; print(ensure_role_tables())"
        first_init = run(sys.executable, "-B", "-c", init_code, env=app_env(init_reconciled_db, temp_root))
        mid_init = logical_tables(init_reconciled_db)
        second_init = run(sys.executable, "-B", "-c", init_code, env=app_env(init_reconciled_db, temp_root))
        check("initializer idempotent on reconciled schema", first_init.returncode == 0 and second_init.returncode == 0 and mid_init == logical_tables(init_reconciled_db) and "'changes': 0" in second_init.stdout)

        route_cases = [
            ("GET /admin/workspace/compliance", "/admin/workspace/compliance", True, False, 200, []),
            ("GET /compliance/reviews", "/compliance/reviews", True, False, 503, []),
            ("GET /compliance/reviews/CMP-2026-0001", "/compliance/reviews/CMP-2026-0001", True, False, 503, []),
            ("GET /system/observations", "/system/observations", True, False, 503, []),
            ("GET /admin/workspace/system", "/admin/workspace/system", True, False, 200, []),
            ("GET /logout", "/logout", True, False, 302, []),
            ("unauth GET /compliance/reviews", "/compliance/reviews", False, False, 302, []),
            ("POST /login", "/login", False, True, 302, ["audit_log"]),
        ]
        for label, url, auth, login, status, changed in route_cases:
            case_db = temp_root / (hashlib.sha1(label.encode()).hexdigest() + ".db")
            shutil.copy2(DB, case_db)
            result = request_case(case_db, temp_root, url, auth=auth, login=login)
            check(f"request regression: {label}", result.get("status") == status and result.get("changed") == changed, result)

    final = {
        "size": DB.stat().st_size,
        "mtime_ns": DB.stat().st_mtime_ns,
        "sha": digest(DB),
        "counts": db_counts(DB),
        "logical": logical_tables(DB),
    }
    check("protected trustee_app.db unchanged", final == protected)
    _, _, staged_final, _ = git_sets()
    check("staging remains empty", not staged_final, staged_final)
    print("POST-V2-17Q-H.6A-R6 AUTHORIZATION AUDIT")
    print("RESULT: " + ("FAIL" if failures else "PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
