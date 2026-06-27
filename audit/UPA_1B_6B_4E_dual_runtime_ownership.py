from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "audit" else Path.cwd().resolve()
AUDIT_DIR = ROOT / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "trustee_app.db"

EXPECTED_BRANCH = "strapback/stable-661bb66"
EXPECTED_HEAD = "1cf6497598d9d294bc0453847b896316f863c241"
FIRM_1 = "FIRM-001"
FIRM_2 = "FIRM-002"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_PATH = AUDIT_DIR / f"UPA-1B-6B-4E_dual_runtime_ownership_{STAMP}.json"
MD_PATH = AUDIT_DIR / f"UPA-1B-6B-4E_dual_runtime_ownership_{STAMP}.md"

PRIVATE_MARKERS = (
    "Luna Isaac Mishoe III", "Luna I Mishoe III", "Luna Mishoe",
    "MOORE-MISHOE FAMILY TRUST", "LUNA ISAAC MISHOE III Revocable Trust",
    "MAT-000001", "MRL-000001", "TR-022",
)
IDENTITY_COLUMNS = {
    "username", "user_name", "owner_id", "user_id", "created_by", "updated_by",
    "verified_by", "reviewed_by", "performed_by", "actor", "assigned_to",
    "requested_by", "approved_by",
}
GLOBAL_TABLES = {
    "permissions", "roles", "role_permissions", "permission_matrix", "trust_types",
    "document_types", "learning_categories", "video_categories", "form_guides",
    "system_settings", "schema_migrations", "migrations",
}
SENSITIVE_TERMS = (
    "beneficiary", "asset", "property", "account", "tax", "estate", "family",
    "genealogy", "distribution", "transfer", "document", "trust", "matter",
    "intake", "workspace",
)


def run(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    return {"returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip()}


def git_text(*args: str) -> str:
    result = run(["git", *args])
    return result["stdout"] or result["stderr"]


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def columns(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [{"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3],
             "default": r[4], "pk": r[5]}
            for r in conn.execute(f"PRAGMA table_info({q(table)})").fetchall()]


def fks(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [{"id": r[0], "seq": r[1], "parent_table": r[2], "from_column": r[3],
             "to_column": r[4], "on_update": r[5], "on_delete": r[6]}
            for r in conn.execute(f"PRAGMA foreign_key_list({q(table)})").fetchall()]


def sample_identifiers(conn: sqlite3.Connection, table: str,
                       cols: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    names = [c["name"] for c in cols]
    lower = {n.lower(): n for n in names}
    selected: list[str] = []
    for candidate in ("id", "matter_id", "trust_id", "intake_id", "workspace_id",
                      "document_id", "transfer_id", "username", "name", "title", "firm_id"):
        if candidate in lower:
            selected.append(lower[candidate])
    selected = list(dict.fromkeys(selected)) or names[:4]
    if not selected:
        return []
    select_sql = ", ".join(q(c) for c in selected)
    try:
        rows = conn.execute(f"SELECT {select_sql} FROM {q(table)} LIMIT ?", (limit,)).fetchall()
    except sqlite3.Error:
        return []
    return [{selected[i]: row[i] for i in range(len(selected))} for row in rows]


def marker_matches(conn: sqlite3.Connection, table: str,
                   cols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for col in cols:
        name = col["name"]
        dtype = (col["type"] or "").upper()
        if dtype and not any(t in dtype for t in ("CHAR", "TEXT", "CLOB")):
            continue
        for marker in PRIVATE_MARKERS:
            try:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {q(table)} WHERE LOWER(CAST({q(name)} AS TEXT)) LIKE LOWER(?)",
                    (f"%{marker}%",),
                ).fetchone()[0]
            except sqlite3.Error:
                continue
            if count:
                out.append({"column": name, "marker": marker, "count": int(count)})
    return out


def admin_distribution(conn: sqlite3.Connection, table: str,
                       cols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = [c["name"] for c in cols]
    lower = {n.lower(): n for n in names}
    identities = [orig for low, orig in lower.items() if low in IDENTITY_COLUMNS]
    firm_col = lower.get("firm_id")
    out: list[dict[str, Any]] = []
    for col in identities:
        try:
            if firm_col:
                rows = conn.execute(
                    f"SELECT COALESCE(CAST({q(firm_col)} AS TEXT), '[NULL]') AS firm_value, COUNT(*) AS row_count "
                    f"FROM {q(table)} WHERE LOWER(TRIM(CAST({q(col)} AS TEXT)))='admin123' GROUP BY {q(firm_col)}"
                ).fetchall()
            else:
                rows = conn.execute(
                    f"SELECT '[NO_FIRM_COLUMN]' AS firm_value, COUNT(*) AS row_count "
                    f"FROM {q(table)} WHERE LOWER(TRIM(CAST({q(col)} AS TEXT)))='admin123'"
                ).fetchall()
        except sqlite3.Error:
            continue
        for row in rows:
            count = int(row["row_count"] or 0)
            if count:
                out.append({"column": col, "firm_id": row["firm_value"], "count": count})
    return out


def classify(table: str, row_count: int, has_firm: bool, firm_counts: dict[str, int],
             fk_list: list[dict[str, Any]], markers: list[dict[str, Any]],
             admin_dist: list[dict[str, Any]]) -> tuple[str, str]:
    lower = table.lower()
    firms = {k for k, v in firm_counts.items() if k not in {"[NULL]", ""} and v > 0}
    null_count = firm_counts.get("[NULL]", 0)
    if row_count == 0:
        return (("GLOBAL_COPY_BOTH_EMPTY", "COPY_SCHEMA_AND_SEED_POLICY_REVIEW")
                if lower in GLOBAL_TABLES else
                ("EMPTY_SCHEMA_REVIEW", "COPY_SCHEMA_ONLY_PENDING_POLICY"))
    if has_firm:
        if firms == {FIRM_1} and null_count == 0:
            return "FIRM1_EXPLICIT", "FIRM1_ONLY"
        if firms == {FIRM_2} and null_count == 0:
            return "FIRM2_EXPLICIT", "FIRM2_ONLY"
        if FIRM_1 in firms and FIRM_2 in firms:
            return "MIXED_EXPLICIT", "FILTER_BY_FIRM_AND_REVIEW_NULL_ROWS"
        if not firms and null_count == row_count:
            return "ALL_NULL_FIRM", "OWNERSHIP_REVIEW_REQUIRED"
        return "PARTIAL_OR_UNKNOWN_FIRM_SCOPE", "OWNERSHIP_REVIEW_REQUIRED"
    if lower in GLOBAL_TABLES:
        return "PROBABLE_GLOBAL", "COPY_TO_BOTH_AFTER_GLOBAL_POLICY_REVIEW"
    if markers:
        return "PROBABLE_FIRM2_PRIVATE", "FIRM2_PENDING_PARENT_VALIDATION"
    if fk_list:
        return "DEPENDENT_PARENT_SCOPE", "INHERIT_FROM_PARENT_AFTER_GRAPH_VALIDATION"
    if any(term in lower for term in SENSITIVE_TERMS):
        return "UNSCOPED_SENSITIVE_TENANT_DATA", "MANUAL_OR_PARENT_OWNERSHIP_REVIEW"
    if admin_dist:
        return "UNSCOPED_USER_ASSOCIATED", "DO_NOT_CLASSIFY_BY_USERNAME_ALONE"
    return "UNCLASSIFIED_UNSCOPED", "MANUAL_CLASSIFICATION_REQUIRED"


def main() -> None:
    print("=== UPA-1B-6B-4E — DUAL-RUNTIME OWNERSHIP AND CONTINUITY MAP ===")
    branch = git_text("branch", "--show-current")
    head = git_text("rev-parse", "HEAD")
    status = git_text("status", "--short")
    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"ERROR: Expected branch {EXPECTED_BRANCH}, found {branch}.")
    if head != EXPECTED_HEAD:
        raise SystemExit(f"ERROR: Expected HEAD {EXPECTED_HEAD}, found {head}.")
    if not DB_PATH.exists():
        raise SystemExit(f"ERROR: Active database not found: {DB_PATH}")

    before = sha256_file(DB_PATH)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()]

    table_map: dict[str, Any] = {}
    class_counts: Counter[str] = Counter()
    elig_counts: Counter[str] = Counter()
    reverse_graph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    admin_summary: Counter[str] = Counter()

    for table in tables:
        cols = columns(conn, table)
        names = [c["name"] for c in cols]
        lower = {n.lower(): n for n in names}
        row_count = int(conn.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0])
        has_firm = "firm_id" in lower
        firm_counts: dict[str, int] = {}
        if has_firm:
            firm_col = lower["firm_id"]
            for row in conn.execute(
                f"SELECT {q(firm_col)} AS firm_value, COUNT(*) AS row_count FROM {q(table)} GROUP BY {q(firm_col)}"
            ).fetchall():
                key = str(row["firm_value"]).strip() if row["firm_value"] is not None else "[NULL]"
                firm_counts[key] = int(row["row_count"])

        fk_list = fks(conn, table)
        for fk in fk_list:
            reverse_graph[fk["parent_table"]].append({"child_table": table, **fk})
        markers = marker_matches(conn, table, cols)
        admin_dist = admin_distribution(conn, table, cols)
        for item in admin_dist:
            admin_summary[item["firm_id"]] += item["count"]
        classification, eligibility = classify(
            table, row_count, has_firm, firm_counts, fk_list, markers, admin_dist
        )
        class_counts[classification] += 1
        elig_counts[eligibility] += 1
        primary_keys = [c["name"] for c in sorted(cols, key=lambda x: x["pk"]) if c["pk"]]
        table_map[table] = {
            "row_count": row_count,
            "columns": names,
            "primary_key_columns": primary_keys,
            "has_firm_id": has_firm,
            "firm_counts": firm_counts,
            "foreign_keys": fk_list,
            "children": [],
            "private_marker_matches": markers,
            "admin123_distribution": admin_dist,
            "sample_identifiers": sample_identifiers(conn, table, cols),
            "classification": classification,
            "extraction_eligibility": eligibility,
        }

    for parent, children in reverse_graph.items():
        if parent in table_map:
            table_map[parent]["children"] = children
    conn.close()
    after = sha256_file(DB_PATH)
    if before != after:
        raise SystemExit("ERROR: Live database hash changed during read-only audit.")

    explicit_firm1 = [t for t, x in table_map.items() if x["classification"] == "FIRM1_EXPLICIT"]
    explicit_firm2 = [t for t, x in table_map.items() if x["classification"] == "FIRM2_EXPLICIT"]
    mixed = [t for t, x in table_map.items() if x["classification"] == "MIXED_EXPLICIT"]
    probable_global = [t for t, x in table_map.items() if x["classification"] in {"PROBABLE_GLOBAL", "GLOBAL_COPY_BOTH_EMPTY"}]
    dependent = [t for t, x in table_map.items() if x["classification"] == "DEPENDENT_PARENT_SCOPE"]
    probable_private = [t for t, x in table_map.items() if x["classification"] == "PROBABLE_FIRM2_PRIVATE"]
    ambiguous = [t for t, x in table_map.items() if x["extraction_eligibility"] in {
        "OWNERSHIP_REVIEW_REQUIRED", "MANUAL_OR_PARENT_OWNERSHIP_REVIEW",
        "DO_NOT_CLASSIFY_BY_USERNAME_ALONE", "MANUAL_CLASSIFICATION_REQUIRED",
    }]
    null_firm = {t: x["firm_counts"].get("[NULL]", 0) for t, x in table_map.items()
                 if x["firm_counts"].get("[NULL]", 0)}

    blockers: list[str] = []
    warnings: list[str] = []
    if mixed:
        blockers.append(f"{len(mixed)} table(s) contain explicit Firm 1 and Firm 2 records.")
    if ambiguous:
        blockers.append(f"{len(ambiguous)} table(s) remain ambiguous or require parent/manual review.")
    if null_firm:
        blockers.append(f"{sum(null_firm.values())} null-firm row(s) exist across {len(null_firm)} table(s).")
    if probable_global:
        warnings.append("Probable global tables require policy review before copying to both runtimes.")
    if admin_summary:
        warnings.append("admin123 must become independent account records in Firm 1 and Firm 2.")
    if probable_private:
        warnings.append("Private marker matches are strong Firm 2 evidence but still require parent validation.")

    result_status = ("OWNERSHIP_MAP_COMPLETE_EXTRACTION_NOT_YET_AUTHORIZED"
                     if blockers else "OWNERSHIP_MAP_COMPLETE_READY_FOR_SANDBOX_EXTRACTION")
    output = {
        "generated_at": datetime.now().isoformat(),
        "status": result_status,
        "repository": {"path": str(ROOT), "branch": branch, "head": head, "git_status": status},
        "database": {"path": str(DB_PATH), "sha256_before": before, "sha256_after": after,
                     "unchanged": before == after, "integrity_check": integrity, "table_count": len(tables)},
        "classification_summary": dict(sorted(class_counts.items())),
        "eligibility_summary": dict(sorted(elig_counts.items())),
        "explicit_firm1_tables": explicit_firm1,
        "explicit_firm2_tables": explicit_firm2,
        "mixed_tables": mixed,
        "probable_global_tables": probable_global,
        "dependent_tables": dependent,
        "probable_private_tables": probable_private,
        "ambiguous_tables": ambiguous,
        "null_firm_tables": null_firm,
        "admin123_summary": dict(sorted(admin_summary.items())),
        "table_map": table_map,
        "continuity_model": {
            "firm1": "Master/general trust platform",
            "firm2": "Private personal trust platform",
            "shared_codebase": True,
            "separate_databases": True,
            "separate_users": True,
            "separate_sessions": True,
            "separate_storage": True,
        },
        "warnings": warnings,
        "blockers": blockers,
    }
    JSON_PATH.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")

    lines = [
        "# UPA-1B-6B-4E — Dual-Runtime Ownership and Continuity Map", "",
        f"Generated: {output['generated_at']}", f"Status: **{result_status}**", "",
        "## Safety", "", f"- Integrity: `{integrity}`", f"- Database unchanged: **{before == after}**", "",
        "## Classification Summary", "",
    ]
    lines += [f"- {k}: **{v}**" for k, v in sorted(class_counts.items())]
    lines += ["", "## Extraction Eligibility", ""]
    lines += [f"- {k}: **{v}**" for k, v in sorted(elig_counts.items())]
    lines += ["", "## Key Groups", "",
              f"- Explicit Firm 1: `{explicit_firm1}`",
              f"- Explicit Firm 2: `{explicit_firm2}`",
              f"- Mixed: `{mixed}`",
              f"- Probable global: `{probable_global}`",
              f"- Dependent parent scope: `{dependent}`",
              f"- Probable Firm 2 private: `{probable_private}`",
              f"- Ambiguous: `{ambiguous}`",
              f"- Null-firm: `{null_firm}`", "",
              "## admin123", "", f"- Distribution: `{dict(sorted(admin_summary.items()))}`",
              "- Policy: independent user record in each runtime.", "", "## Warnings", ""]
    lines += [f"- {x}" for x in warnings] or ["- None."]
    lines += ["", "## Blockers", ""]
    lines += [f"- {x}" for x in blockers] or ["- None."]
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\nUPA-1B-6B-4E OWNERSHIP AND CONTINUITY MAP COMPLETE")
    print(f"Status: {result_status}")
    print("\nDATABASE SAFETY:")
    print(f"- Integrity: {integrity}")
    print(f"- Live Database Unchanged: {before == after}")
    print("\nTABLE CLASSIFICATIONS:")
    for k, v in sorted(class_counts.items()):
        print(f"- {k}: {v}")
    print("\nEXTRACTION ELIGIBILITY:")
    for k, v in sorted(elig_counts.items()):
        print(f"- {k}: {v}")
    print("\nKEY TABLE GROUPS:")
    print(f"- Explicit Firm 1: {explicit_firm1}")
    print(f"- Explicit Firm 2: {explicit_firm2}")
    print(f"- Mixed: {mixed}")
    print(f"- Probable Global: {probable_global}")
    print(f"- Dependent Parent Scope: {dependent}")
    print(f"- Probable Firm 2 Private: {probable_private}")
    print(f"- Ambiguous: {ambiguous}")
    print(f"- Null Firm: {null_firm}")
    print("\nADMIN123:")
    print(f"- Distribution: {dict(sorted(admin_summary.items()))}")
    print("- Policy: independent user record in each runtime")
    print("\nWARNINGS:")
    for item in warnings or ["None"]:
        print(f"- {item}")
    print("\nBLOCKERS:")
    for item in blockers or ["None"]:
        print(f"- {item}")
    print(f"\nJSON REPORT: {JSON_PATH}")
    print(f"MARKDOWN REPORT: {MD_PATH}")
    print("=== UPA-1B-6B-4E COMPLETE ===")


if __name__ == "__main__":
    main()
