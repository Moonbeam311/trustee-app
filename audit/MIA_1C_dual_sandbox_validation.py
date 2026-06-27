from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# MIA-1C-R1 repository import bootstrap
# Allows direct execution from audit/ while importing project packages.
ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from typing import Any

from database.startup_migrations import (
    run_additive_startup_migrations,
)
from services.services_matter_intake import (
    create_matter_intake_link,
    get_matter_intake_link,
    list_link_events,
)


AUDIT_DIR = ROOT / "audit"
LIVE_DB = ROOT / "trustee_app.db"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

VALIDATION_ROOT = (
    AUDIT_DIR
    / "runtime_sandbox"
    / f"MIA-1C_{STAMP}"
)

FIRM1_DB = VALIDATION_ROOT / "firm1" / "trustee_app_firm1_validation.db"
FIRM2_DB = VALIDATION_ROOT / "firm2" / "trustee_app_firm2_validation.db"

REPORT_PATH = (
    AUDIT_DIR
    / f"MIA-1C_dual_sandbox_validation_{STAMP}.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def latest_corrected_sandbox_report() -> tuple[Path, dict[str, Any]]:
    reports = sorted(
        AUDIT_DIR.glob(
            "UPA-1B-6B-4P_corrected_sandbox_rebuild_*.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not reports:
        raise SystemExit(
            "ERROR: No corrected UPA-1B-6B-4P sandbox report found."
        )

    path = reports[0]

    return path, json.loads(
        path.read_text(encoding="utf-8")
    )


def find_database_path(
    report: dict[str, Any],
    firm_number: int,
) -> Path:
    candidates: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            lowered = value.lower()

            if (
                value.lower().endswith(".db")
                and (
                    f"firm{firm_number}" in lowered
                    or f"firm_{firm_number}" in lowered
                    or f"firm {firm_number}" in lowered
                )
            ):
                candidates.append(value)

    walk(report)

    existing = [
        Path(value)
        for value in candidates
        if Path(value).exists()
    ]

    if not existing:
        raise SystemExit(
            f"ERROR: Could not locate certified Firm {firm_number} "
            "sandbox database from the 4P report."
        )

    return existing[0].resolve()


def integrity(path: Path) -> str:
    connection = sqlite3.connect(path)

    try:
        return connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
    finally:
        connection.close()


def table_count(path: Path, table_name: str) -> int | None:
    connection = sqlite3.connect(path)

    try:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        if not exists:
            return None

        quoted = table_name.replace('"', '""')

        return connection.execute(
            f'SELECT COUNT(*) FROM "{quoted}"'
        ).fetchone()[0]
    finally:
        connection.close()


def find_first_record(
    path: Path,
    table_name: str,
    id_column: str,
    firm_id: str,
) -> str:
    connection = sqlite3.connect(path)

    try:
        row = connection.execute(
            f"""
            SELECT {id_column}
            FROM {table_name}
            WHERE firm_id = ?
            ORDER BY {id_column}
            LIMIT 1
            """,
            (firm_id,),
        ).fetchone()

        if row is None:
            raise SystemExit(
                f"ERROR: No {table_name} record found for {firm_id} "
                f"in {path}."
            )

        return str(row[0])
    finally:
        connection.close()


def run_startup_import(
    db_path: Path,
    firm_id: str,
    cookie_name: str,
) -> dict[str, Any]:
    child = VALIDATION_ROOT / f"startup_probe_{firm_id}.py"

    child.write_text(
        """
from __future__ import annotations

import json
import os
import sqlite3

db_path = os.environ["DB_PATH"]

def count(table_name):
    connection = sqlite3.connect(db_path)
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()

        if not exists:
            return None

        return connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
    finally:
        connection.close()

before = {
    "role_permissions": count("role_permissions"),
    "matter_intake_links": count("matter_intake_links"),
    "matter_intake_link_events": count("matter_intake_link_events"),
}

import app  # noqa: F401

after = {
    "role_permissions": count("role_permissions"),
    "matter_intake_links": count("matter_intake_links"),
    "matter_intake_link_events": count("matter_intake_link_events"),
}

print(json.dumps({
    "before": before,
    "after": after,
}))
""",
        encoding="utf-8",
    )

    environment = os.environ.copy()
    environment["DB_PATH"] = str(db_path)
    environment["ACTIVE_FIRM_ID"] = firm_id
    environment["FIRM_ID"] = firm_id
    environment["SESSION_COOKIE_NAME"] = cookie_name
    environment["SECRET_KEY"] = f"MIA-1C-{firm_id}-sandbox-secret"
    environment["PYTHONPATH"] = str(ROOT)

    result = subprocess.run(
        [sys.executable, str(child)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"ERROR: Startup import failed for {firm_id}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    json_line = None

    for line in reversed(result.stdout.splitlines()):
        stripped = line.strip()

        if stripped.startswith("{") and stripped.endswith("}"):
            json_line = stripped
            break

    if json_line is None:
        raise SystemExit(
            f"ERROR: Startup probe for {firm_id} did not return JSON.\n"
            f"STDOUT:\n{result.stdout}"
        )

    payload = json.loads(json_line)
    payload["stdout"] = result.stdout
    payload["stderr"] = result.stderr

    return payload


source_report_path, source_report = latest_corrected_sandbox_report()

firm1_source = find_database_path(source_report, 1)
firm2_source = find_database_path(source_report, 2)

VALIDATION_ROOT.mkdir(parents=True, exist_ok=True)
FIRM1_DB.parent.mkdir(parents=True, exist_ok=True)
FIRM2_DB.parent.mkdir(parents=True, exist_ok=True)

live_hash_before = sha256(LIVE_DB)
firm1_source_hash_before = sha256(firm1_source)
firm2_source_hash_before = sha256(firm2_source)

shutil.copy2(firm1_source, FIRM1_DB)
shutil.copy2(firm2_source, FIRM2_DB)

firm1_role_before = table_count(FIRM1_DB, "role_permissions")
firm2_role_before = table_count(FIRM2_DB, "role_permissions")

firm1_first = run_additive_startup_migrations(FIRM1_DB)
firm1_second = run_additive_startup_migrations(FIRM1_DB)

firm2_first = run_additive_startup_migrations(FIRM2_DB)
firm2_second = run_additive_startup_migrations(FIRM2_DB)

firm1_matter = find_first_record(
    FIRM1_DB,
    "matters",
    "matter_id",
    "FIRM-001",
)

firm1_intake = find_first_record(
    FIRM1_DB,
    "intake_sessions",
    "intake_id",
    "FIRM-001",
)

firm2_matter = find_first_record(
    FIRM2_DB,
    "matters",
    "matter_id",
    "FIRM-002",
)

firm2_intake = find_first_record(
    FIRM2_DB,
    "intake_sessions",
    "intake_id",
    "FIRM-002",
)

firm1_created = create_matter_intake_link(
    FIRM1_DB,
    firm_id="FIRM-001",
    matter_id=firm1_matter,
    intake_id=firm1_intake,
    created_by="mia1c-validator",
    link_status="ACTIVE",
    handoff_status="ACCEPTED",
    is_primary=True,
    recommendation_disposition="ACCEPTED",
    event_basis="MIA-1C isolated Firm 1 validation",
)

firm2_created = create_matter_intake_link(
    FIRM2_DB,
    firm_id="FIRM-002",
    matter_id=firm2_matter,
    intake_id=firm2_intake,
    created_by="mia1c-validator",
    link_status="ACTIVE",
    handoff_status="ACCEPTED",
    is_primary=True,
    recommendation_disposition="ACCEPTED",
    event_basis="MIA-1C isolated Firm 2 validation",
)

firm1_wrong_scope = get_matter_intake_link(
    FIRM1_DB,
    firm_id="FIRM-002",
    bridge_id=firm1_created["link"]["bridge_id"],
)

firm2_wrong_scope = get_matter_intake_link(
    FIRM2_DB,
    firm_id="FIRM-001",
    bridge_id=firm2_created["link"]["bridge_id"],
)

firm1_events = list_link_events(
    FIRM1_DB,
    firm_id="FIRM-001",
    bridge_id=firm1_created["link"]["bridge_id"],
)

firm2_events = list_link_events(
    FIRM2_DB,
    firm_id="FIRM-002",
    bridge_id=firm2_created["link"]["bridge_id"],
)

firm1_startup_cycle_1 = run_startup_import(
    FIRM1_DB,
    "FIRM-001",
    "trustee_firm1_mia1c_session",
)

firm1_startup_cycle_2 = run_startup_import(
    FIRM1_DB,
    "FIRM-001",
    "trustee_firm1_mia1c_session",
)

firm2_startup_cycle_1 = run_startup_import(
    FIRM2_DB,
    "FIRM-002",
    "trustee_firm2_mia1c_session",
)

firm2_startup_cycle_2 = run_startup_import(
    FIRM2_DB,
    "FIRM-002",
    "trustee_firm2_mia1c_session",
)

firm1_role_after = table_count(FIRM1_DB, "role_permissions")
firm2_role_after = table_count(FIRM2_DB, "role_permissions")

live_hash_after = sha256(LIVE_DB)
firm1_source_hash_after = sha256(firm1_source)
firm2_source_hash_after = sha256(firm2_source)

same_bridge_identifier = (
    firm1_created["link"]["bridge_id"]
    == "MIB-000001"
    and firm2_created["link"]["bridge_id"]
    == "MIB-000001"
)

same_event_identifier = (
    firm1_created["event"]["event_id"]
    == "MIBE-000001"
    and firm2_created["event"]["event_id"]
    == "MIBE-000001"
)

role_permissions_stable = (
    firm1_role_before == firm1_role_after
    and firm2_role_before == firm2_role_after
    and firm1_startup_cycle_1["before"]["role_permissions"]
        == firm1_startup_cycle_1["after"]["role_permissions"]
    and firm1_startup_cycle_2["before"]["role_permissions"]
        == firm1_startup_cycle_2["after"]["role_permissions"]
    and firm2_startup_cycle_1["before"]["role_permissions"]
        == firm2_startup_cycle_1["after"]["role_permissions"]
    and firm2_startup_cycle_2["before"]["role_permissions"]
        == firm2_startup_cycle_2["after"]["role_permissions"]
)

source_sandboxes_unchanged = (
    firm1_source_hash_before == firm1_source_hash_after
    and firm2_source_hash_before == firm2_source_hash_after
)

checks = {
    "live_database_unchanged": live_hash_before == live_hash_after,
    "certified_source_sandboxes_unchanged": source_sandboxes_unchanged,
    "firm1_integrity_ok": integrity(FIRM1_DB) == "ok",
    "firm2_integrity_ok": integrity(FIRM2_DB) == "ok",
    "firm1_first_schema_complete": (
        firm1_first["matter_intake_bridge"]["schema_complete"]
    ),
    "firm1_second_schema_complete": (
        firm1_second["matter_intake_bridge"]["schema_complete"]
    ),
    "firm2_first_schema_complete": (
        firm2_first["matter_intake_bridge"]["schema_complete"]
    ),
    "firm2_second_schema_complete": (
        firm2_second["matter_intake_bridge"]["schema_complete"]
    ),
    "same_bridge_identifier_isolated": same_bridge_identifier,
    "same_event_identifier_isolated": same_event_identifier,
    "firm1_wrong_scope_blocked": firm1_wrong_scope is None,
    "firm2_wrong_scope_blocked": firm2_wrong_scope is None,
    "firm1_event_recorded": len(firm1_events) == 1,
    "firm2_event_recorded": len(firm2_events) == 1,
    "role_permissions_stable": role_permissions_stable,
}

passed = all(checks.values())

report = {
    "audit_id": "MIA-1C",
    "created_at": datetime.now().isoformat(),
    "status": (
        "DUAL_SANDBOX_STARTUP_MIGRATION_VALIDATED"
        if passed
        else "MIA_1C_VALIDATION_FAILED"
    ),
    "source_report": str(source_report_path),
    "certified_firm1_source": str(firm1_source),
    "certified_firm2_source": str(firm2_source),
    "validation_firm1_database": str(FIRM1_DB),
    "validation_firm2_database": str(FIRM2_DB),
    "checks": checks,
    "firm1": {
        "matter_id": firm1_matter,
        "intake_id": firm1_intake,
        "created_link": firm1_created,
        "events": firm1_events,
        "startup_cycle_1": firm1_startup_cycle_1,
        "startup_cycle_2": firm1_startup_cycle_2,
        "role_permissions_before": firm1_role_before,
        "role_permissions_after": firm1_role_after,
    },
    "firm2": {
        "matter_id": firm2_matter,
        "intake_id": firm2_intake,
        "created_link": firm2_created,
        "events": firm2_events,
        "startup_cycle_1": firm2_startup_cycle_1,
        "startup_cycle_2": firm2_startup_cycle_2,
        "role_permissions_before": firm2_role_before,
        "role_permissions_after": firm2_role_after,
    },
    "live_database": {
        "sha256_before": live_hash_before,
        "sha256_after": live_hash_after,
    },
    "authorization": {
        "startup_registration_validated": passed,
        "live_operational_link_creation": False,
        "production_cutover": False,
        "next_phase": (
            "MIA-1D — Matter and Intake Linkage Routes, "
            "Review Gate, and Matter Event Integration"
        ),
    },
}

REPORT_PATH.write_text(
    json.dumps(report, indent=2, default=str),
    encoding="utf-8",
)

print("=== MIA-1C DUAL-SANDBOX VALIDATION ===")
print(f"Status: {report['status']}")
print(f"Live Database Unchanged: {checks['live_database_unchanged']}")
print(
    "Certified Source Sandboxes Unchanged: "
    f"{checks['certified_source_sandboxes_unchanged']}"
)
print(f"Firm 1 Integrity: {integrity(FIRM1_DB)}")
print(f"Firm 2 Integrity: {integrity(FIRM2_DB)}")
print(
    "Firm 1 Bridge/Event: "
    f"{firm1_created['link']['bridge_id']} / "
    f"{firm1_created['event']['event_id']}"
)
print(
    "Firm 2 Bridge/Event: "
    f"{firm2_created['link']['bridge_id']} / "
    f"{firm2_created['event']['event_id']}"
)
print(
    "Same Local Identifiers Safely Isolated: "
    f"{same_bridge_identifier and same_event_identifier}"
)
print(f"Firm 1 Wrong Scope Blocked: {firm1_wrong_scope is None}")
print(f"Firm 2 Wrong Scope Blocked: {firm2_wrong_scope is None}")
print(f"Role Permissions Stable: {role_permissions_stable}")
print(f"Report: {REPORT_PATH.relative_to(ROOT)}")

if not passed:
    print()
    print("FAILED CHECKS:")

    for name, value in checks.items():
        if not value:
            print(f"- {name}")

    raise SystemExit(1)
