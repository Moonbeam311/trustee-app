from pathlib import Path
import hashlib
import json
import sqlite3
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_BRANCH = "post-v2-planning"
CURRENT_CERTIFIED_HEAD = "ab080d47d89257df58d3712be9953c0b37c6b114"
CERTIFIED_17Q_D = "2aaf5b61e0323aa0aed3ebb582954105a57ed7b8"
CERTIFIED_17Q_E = "ab080d47d89257df58d3712be9953c0b37c6b114"
AUTHORIZED_FILES = {
    "scripts/audit_archive_people_destination_adapters_17q_e.py",
    "scripts/audit_system_audit_destination_removal_17q_d.py",
    "scripts/audit_compliance_review_architecture_17q_f.py",
    "scripts/audit_regression_guard_and_auth_preservation_17q_f_1.py",
}
MODE = "regression_guard_modernization_and_bounded_authentication_audit_preservation"


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def git(*args):
    result = run(["git", *args])
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def record(results, label, passed, details=""):
    results.append((label, bool(passed), details))


def status_paths():
    code, stdout, _ = git("status", "--short", "--untracked-files=all")
    paths = set()
    if code != 0:
        return paths
    for line in stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:] if line.startswith("?? ") else line[2:].strip()
        paths.add(path.replace("\\", "/"))
    return paths


def ancestry(commit):
    return git("merge-base", "--is-ancestor", commit, "HEAD")[0] == 0


def script_passes(path):
    result = run([sys.executable, path])
    tail = "\n".join((result.stdout + result.stderr).splitlines()[-8:])
    return result.returncode == 0, tail


def db_snapshot():
    path = ROOT / "trustee_app.db"
    snapshot = {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else None,
        "mtime": path.stat().st_mtime if path.exists() else None,
        "audit_log_count": "MISSING",
        "audit_log_max_id": None,
        "latest_audit_rows": [],
        "system_observations": "MISSING",
        "system_observation_events": "MISSING",
        "governance_relationships": "MISSING",
        "continuity_custody_log": "MISSING",
        "fiduciaries": "MISSING",
        "compliance_tables": [],
        "compliance_record_count": 0,
        "schema_hash": None,
    }
    if not path.exists():
        return snapshot
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        schema_rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        schema_text = "\n".join(f"{row['type']}|{row['name']}|{row['sql'] or ''}" for row in schema_rows)
        snapshot["schema_hash"] = hashlib.sha256(schema_text.encode("utf-8")).hexdigest()
        table_names = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for table in (
            "audit_log",
            "system_observations",
            "system_observation_events",
            "governance_relationships",
            "continuity_custody_log",
            "fiduciaries",
        ):
            if table in table_names:
                snapshot[table if table != "audit_log" else "audit_log_count"] = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
        if "audit_log" in table_names:
            snapshot["audit_log_max_id"] = conn.execute("SELECT COALESCE(MAX(id), 0) FROM audit_log").fetchone()[0]
            snapshot["latest_audit_rows"] = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM audit_log ORDER BY id DESC LIMIT 5"
                ).fetchall()
            ]
        compliance_tables = sorted(name for name in table_names if name.startswith("compliance"))
        snapshot["compliance_tables"] = compliance_tables
        total = 0
        for table in compliance_tables:
            total += conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        snapshot["compliance_record_count"] = total
        return snapshot
    finally:
        conn.close()


def audit_delta(before, after):
    before_id = before.get("audit_log_max_id") or 0
    after_id = after.get("audit_log_max_id") or 0
    path = Path(after["path"])
    new_rows = []
    if path.exists() and after_id > before_id:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            new_rows = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM audit_log WHERE id > ? ORDER BY id",
                    (before_id,),
                ).fetchall()
            ]
        finally:
            conn.close()
    expected_login = [
        row
        for row in new_rows
        if row.get("entity_type") == "auth"
        and row.get("action") == "login_success"
        and row.get("entity_id") in {"admin", "admin123"}
    ]
    unexpected = [row for row in new_rows if row not in expected_login]
    return new_rows, expected_login, unexpected


def main():
    results = []
    branch = git("branch", "--show-current")[1]
    head = git("rev-parse", "HEAD")[1]
    remote = git("rev-parse", "origin/post-v2-planning")[1]
    staged = set(git("diff", "--cached", "--name-only")[1].splitlines())
    changed = status_paths()
    before = db_snapshot()

    d_source = read("scripts/audit_system_audit_destination_removal_17q_d.py")
    e_source = read("scripts/audit_archive_people_destination_adapters_17q_e.py")
    f_source = read("scripts/audit_compliance_review_architecture_17q_f.py")

    d_exact_head_removed = "head == REQUIRED_HEAD" not in d_source and "REQUIRED_HEAD" not in d_source
    e_exact_head_removed = "head == REQUIRED_HEAD" not in e_source and "REQUIRED_HEAD" not in e_source
    d_corrected_guard = "merge-base" in d_source and CERTIFIED_17Q_D in d_source
    e_corrected_guard = "merge-base" in e_source and CERTIFIED_17Q_E in e_source

    d_pass, d_tail = script_passes("scripts/audit_system_audit_destination_removal_17q_d.py")
    e_pass, e_tail = script_passes("scripts/audit_archive_people_destination_adapters_17q_e.py")
    f_pass, f_tail = script_passes("scripts/audit_compliance_review_architecture_17q_f.py")
    after = db_snapshot()
    new_audit_rows, expected_login_rows, unexpected_audit_rows = audit_delta(before, after)

    record(results, "baseline branch", branch == REQUIRED_BRANCH)
    record(results, "current certified HEAD", head == CURRENT_CERTIFIED_HEAD and remote == CURRENT_CERTIFIED_HEAD)
    record(results, "17Q-D certified commit ancestry", ancestry(CERTIFIED_17Q_D))
    record(results, "17Q-E certified commit ancestry", ancestry(CERTIFIED_17Q_E))
    record(results, "17Q-D exact-HEAD dependency removed", d_exact_head_removed)
    record(results, "17Q-D corrected guard", d_corrected_guard)
    record(results, "17Q-E exact-HEAD dependency removed", e_exact_head_removed)
    record(results, "17Q-E corrected guard", e_corrected_guard)
    record(results, "Historical audit future-commit compatibility", d_corrected_guard and e_corrected_guard)
    record(results, "17Q-D behavioral regression", d_pass, d_tail)
    record(results, "17Q-E behavioral regression", e_pass, e_tail)
    record(results, "17Q-F architecture preservation", f_pass, f_tail)
    record(results, "Compliance verifier posture", "Compliance: bounded_unavailable" in f_source or "compliance_bounded_unavailable" in f_source)
    record(results, "System Audit posture", "System Audit remains prohibited" in f_source or "system_audit_prohibited" in f_source)
    record(results, "authentication audit delta is bounded", len(new_audit_rows) == len(expected_login_rows) and len(expected_login_rows) <= 1)
    record(results, "unexpected audit delta is zero", not unexpected_audit_rows)
    record(results, "Compliance mutation is zero", before["compliance_tables"] == after["compliance_tables"] and after["compliance_record_count"] == before["compliance_record_count"])
    record(results, "System Observation mutation is zero", before["system_observations"] == after["system_observations"] and before["system_observation_events"] == after["system_observation_events"])
    record(results, "destination mutation is zero", before["governance_relationships"] == after["governance_relationships"] and before["continuity_custody_log"] == after["continuity_custody_log"] and before["fiduciaries"] == after["fiduciaries"])
    record(results, "schema mutation is zero", before["schema_hash"] == after["schema_hash"])
    record(results, "working-tree scope is bounded", changed <= AUTHORIZED_FILES)
    record(results, "staged files are absent", not staged)

    print("Current branch")
    print(f"  {branch}")
    print("Current HEAD")
    print(f"  {head}")
    print("Remote HEAD")
    print(f"  {remote}")
    print("17Q-D certified commit ancestry")
    print(f"  {CERTIFIED_17Q_D}: {'PASS' if ancestry(CERTIFIED_17Q_D) else 'FAIL'}")
    print("17Q-E certified commit ancestry")
    print(f"  {CERTIFIED_17Q_E}: {'PASS' if ancestry(CERTIFIED_17Q_E) else 'FAIL'}")
    print("17Q-D old guard defect")
    print("  prior exact-HEAD guard replaced")
    print("17Q-D corrected guard")
    print("  branch plus certified commit ancestry")
    print("17Q-E old guard defect")
    print("  prior exact-HEAD guard replaced")
    print("17Q-E corrected guard")
    print("  branch plus certified commit ancestry")
    print("Historical audit future-commit compatibility")
    print("  later active audit files are bounded by current phase scope instead of treated as behavioral regressions")
    print("17Q-D behavioral regression")
    print(f"  {'PASS' if d_pass else 'FAIL'}")
    print("17Q-E behavioral regression")
    print(f"  {'PASS' if e_pass else 'FAIL'}")
    print("17Q-F architecture preservation")
    print(f"  {'PASS' if f_pass else 'FAIL'}")
    print("Compliance verifier posture")
    print("  bounded_unavailable")
    print("System Audit posture")
    print("  prohibited")
    print("Authentication audit rows before")
    print(f"  count={before['audit_log_count']} max_id={before['audit_log_max_id']}")
    print("Authentication audit rows after")
    print(f"  count={after['audit_log_count']} max_id={after['audit_log_max_id']}")
    print("New audit actions")
    print(f"  {json.dumps(new_audit_rows, sort_keys=True, default=str)}")
    print("Expected authentication rows")
    print(f"  {json.dumps(expected_login_rows, sort_keys=True, default=str)}")
    print("Unexpected audit rows")
    print(f"  {json.dumps(unexpected_audit_rows, sort_keys=True, default=str)}")
    print("System Observation count delta")
    print(f"  observations={before['system_observations']} -> {after['system_observations']}")
    print("System Observation event delta")
    print(f"  events={before['system_observation_events']} -> {after['system_observation_events']}")
    print("Destination relationship delta")
    print(f"  governance_relationships={before['governance_relationships']} -> {after['governance_relationships']}")
    print("Compliance table delta")
    print(f"  {before['compliance_tables']} -> {after['compliance_tables']}")
    print("Compliance record delta")
    print(f"  {before['compliance_record_count']} -> {after['compliance_record_count']}")
    print("Schema delta")
    print(f"  {'unchanged' if before['schema_hash'] == after['schema_hash'] else 'changed'}")
    print("Database file size delta")
    print(f"  {before['size']} -> {after['size']}")
    print("Database mtime explanation")
    if after["mtime"] != before["mtime"] and expected_login_rows and not unexpected_audit_rows:
        print("  database mtime changed due to verified login_success attribution")
    elif after["mtime"] == before["mtime"]:
        print("  database mtime unchanged")
    else:
        print("  database mtime changed without a permitted authentication-only explanation")
    print("Working-tree scope")
    print(f"  {sorted(changed)}")
    print("Staged-file status")
    print(f"  {sorted(staged)}")
    print()

    for label, ok, details in results:
        print(f"{'PASS' if ok else 'FAIL'} - {label}")
        if details and not ok:
            print(details)

    print()
    print("POST-V2-17Q-F.1 MODE")
    print(MODE)
    print()
    print("POST-V2-17Q-F.1 RESULT")
    if all(ok for _, ok, _ in results):
        print(
            "PASS - Historical 17Q-D and 17Q-E audits now validate certified ancestry and current behavioral integrity without requiring obsolete exact-HEAD baselines, while 17Q-F database preservation distinguishes bounded login attribution from prohibited Compliance, routing, destination, observation, render-side, or schema mutation."
        )
        return 0
    print(
        "FAIL - Historical regression audits remain tied to obsolete baselines, behavioral checks were weakened, authentication attribution is unbounded, or prohibited application/database mutation occurred."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
