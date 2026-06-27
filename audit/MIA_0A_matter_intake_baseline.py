from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


print("=== MIA-0A — MATTER AND INTAKE IMPLEMENTATION BASELINE ===")

ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = ROOT / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

APP_PATH = ROOT / "app.py"
DB_MODULE_PATH = ROOT / "database" / "db.py"
TEMPLATE_DIR = ROOT / "templates"
LIVE_DB = ROOT / "trustee_app.db"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

JSON_PATH = AUDIT_DIR / f"MIA-0A_matter_intake_baseline_{STAMP}.json"
MD_PATH = AUDIT_DIR / f"MIA-0A_matter_intake_baseline_{STAMP}.md"

KEYWORDS = (
    "matter",
    "intake",
)

LINKAGE_TERMS = {
    "matter_id",
    "intake_id",
    "session_id",
    "trust_id",
    "relationship_id",
    "document_id",
    "workspace_id",
    "firm_id",
    "status",
    "risk_level",
    "governance_state",
    "priority",
    "readiness_status",
    "created_by",
    "updated_by",
    "verified_by",
    "reviewed_by",
    "created_at",
    "updated_at",
}


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def run_git(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    return {
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def read_text(path: Path) -> str:
    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def keyword_match(value: str) -> bool:
    lowered = value.lower()
    return any(keyword in lowered for keyword in KEYWORDS)


def extract_routes(app_text: str) -> list[dict[str, Any]]:
    lines = app_text.splitlines()
    routes: list[dict[str, Any]] = []

    route_pattern = re.compile(
        r"""@app\.route\(\s*["']([^"']+)["'](?:\s*,\s*methods\s*=\s*\[([^\]]*)\])?"""
    )
    def_pattern = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")

    for index, line in enumerate(lines):
        match = route_pattern.search(line)

        if not match:
            continue

        route_path = match.group(1)
        methods_raw = match.group(2) or ""
        methods = re.findall(r"""["']([A-Z]+)["']""", methods_raw)

        function_name = None
        function_line = None

        for lookahead in range(index + 1, min(index + 12, len(lines))):
            def_match = def_pattern.match(lines[lookahead])

            if def_match:
                function_name = def_match.group(1)
                function_line = lookahead + 1
                break

        combined = " ".join(
            part
            for part in (
                route_path,
                function_name or "",
                line,
            )
            if part
        )

        if not keyword_match(combined):
            continue

        routes.append(
            {
                "route": route_path,
                "methods": methods or ["GET"],
                "decorator_line": index + 1,
                "function": function_name,
                "function_line": function_line,
            }
        )

    return routes


def extract_python_functions(
    text: str,
    source_path: str,
) -> list[dict[str, Any]]:
    functions: list[dict[str, Any]] = []

    pattern = re.compile(
        r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*(?:->.*?)?:",
        re.MULTILINE | re.DOTALL,
    )

    for match in pattern.finditer(text):
        name = match.group(1)
        signature = " ".join(match.group(2).split())

        if not keyword_match(name):
            continue

        line = text.count("\n", 0, match.start()) + 1

        functions.append(
            {
                "source": source_path,
                "name": name,
                "signature": signature,
                "line": line,
            }
        )

    return functions


def inspect_templates() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    if not TEMPLATE_DIR.exists():
        return results

    for path in sorted(TEMPLATE_DIR.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".html", ".htm", ".txt", ".jinja", ".j2"}:
            continue

        relative = path.relative_to(ROOT).as_posix()
        text = read_text(path)

        if not keyword_match(relative) and not keyword_match(text):
            continue

        references = Counter()

        for keyword in KEYWORDS:
            references[keyword] = text.lower().count(keyword)

        results.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "references": dict(references),
            }
        )

    return results


def get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> list[dict[str, Any]]:
    quoted = table_name.replace('"', '""')
    rows = connection.execute(
        f'PRAGMA table_info("{quoted}")'
    ).fetchall()

    return [
        {
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "not_null": bool(row[3]),
            "default": row[4],
            "primary_key": bool(row[5]),
        }
        for row in rows
    ]


def inspect_database() -> dict[str, Any]:
    if not LIVE_DB.exists():
        return {
            "exists": False,
            "path": str(LIVE_DB),
        }

    connection = sqlite3.connect(
        f"file:{LIVE_DB.as_posix()}?mode=ro",
        uri=True,
    )

    connection.row_factory = sqlite3.Row

    try:
        integrity_row = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        integrity = integrity_row[0] if integrity_row else None

        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        all_tables = [row[0] for row in table_rows]

        selected_tables: list[dict[str, Any]] = []

        for table_name in all_tables:
            columns = get_table_columns(connection, table_name)
            column_names = [column["name"] for column in columns]

            table_relevant = keyword_match(table_name)
            linkage_relevant = any(
                name.lower() in LINKAGE_TERMS
                for name in column_names
            )

            intake_or_matter_column = any(
                keyword_match(name)
                for name in column_names
            )

            if not (
                table_relevant
                or intake_or_matter_column
            ):
                continue

            quoted = table_name.replace('"', '""')

            try:
                row_count = connection.execute(
                    f'SELECT COUNT(*) FROM "{quoted}"'
                ).fetchone()[0]
            except sqlite3.Error as error:
                row_count = None
                row_count_error = str(error)
            else:
                row_count_error = None

            firm_distribution = None
            firm_error = None

            if "firm_id" in column_names:
                try:
                    firm_rows = connection.execute(
                        f"""
                        SELECT
                            COALESCE(firm_id, '[NULL]') AS firm_value,
                            COUNT(*) AS row_count
                        FROM "{quoted}"
                        GROUP BY COALESCE(firm_id, '[NULL]')
                        ORDER BY firm_value
                        """
                    ).fetchall()

                    firm_distribution = {
                        row["firm_value"]: row["row_count"]
                        for row in firm_rows
                    }
                except sqlite3.Error as error:
                    firm_error = str(error)

            selected_tables.append(
                {
                    "table": table_name,
                    "row_count": row_count,
                    "row_count_error": row_count_error,
                    "columns": columns,
                    "linkage_columns": [
                        name
                        for name in column_names
                        if (
                            name.lower() in LINKAGE_TERMS
                            or keyword_match(name)
                        )
                    ],
                    "firm_distribution": firm_distribution,
                    "firm_distribution_error": firm_error,
                    "linkage_relevant": linkage_relevant,
                }
            )

        foreign_keys: list[dict[str, Any]] = []

        for table in selected_tables:
            table_name = table["table"]
            quoted = table_name.replace('"', '""')

            try:
                rows = connection.execute(
                    f'PRAGMA foreign_key_list("{quoted}")'
                ).fetchall()
            except sqlite3.Error:
                rows = []

            for row in rows:
                foreign_keys.append(
                    {
                        "from_table": table_name,
                        "from_column": row[3],
                        "to_table": row[2],
                        "to_column": row[4],
                        "on_update": row[5],
                        "on_delete": row[6],
                    }
                )

        return {
            "exists": True,
            "path": str(LIVE_DB),
            "integrity": integrity,
            "all_table_count": len(all_tables),
            "selected_table_count": len(selected_tables),
            "tables": selected_tables,
            "foreign_keys": foreign_keys,
        }

    finally:
        connection.close()


def classify_route(route: dict[str, Any]) -> str:
    combined = " ".join(
        [
            route.get("route") or "",
            route.get("function") or "",
        ]
    ).lower()

    has_matter = "matter" in combined
    has_intake = "intake" in combined

    if has_matter and has_intake:
        return "MATTER_INTAKE_INTEGRATION"

    if has_matter:
        return "MATTER"

    if has_intake:
        return "INTAKE"

    return "OTHER"


branch = run_git("branch", "--show-current")
head = run_git("rev-parse", "HEAD")
status = run_git("status", "--short")
last_commit = run_git(
    "log",
    "-1",
    "--format=%H%n%cI%n%s",
)

db_hash_before = sha256(LIVE_DB)

app_text = read_text(APP_PATH)
db_module_text = read_text(DB_MODULE_PATH)

routes = extract_routes(app_text)

for route in routes:
    route["classification"] = classify_route(route)

app_functions = extract_python_functions(
    app_text,
    "app.py",
)

db_functions = extract_python_functions(
    db_module_text,
    "database/db.py",
)

templates = inspect_templates()
database = inspect_database()

db_hash_after = sha256(LIVE_DB)

route_counts = Counter(
    route["classification"]
    for route in routes
)

table_firm_summary: Counter[str] = Counter()

for table in database.get("tables", []):
    distribution = table.get("firm_distribution")

    if distribution is None:
        table_firm_summary["NO_FIRM_COLUMN"] += 1
        continue

    nonzero_firms = [
        firm
        for firm, count in distribution.items()
        if count
    ]

    if nonzero_firms == ["FIRM-001"]:
        table_firm_summary["FIRM1_ONLY"] += 1
    elif nonzero_firms == ["FIRM-002"]:
        table_firm_summary["FIRM2_ONLY"] += 1
    elif len(nonzero_firms) > 1:
        table_firm_summary["MIXED_OR_NULL"] += 1
    else:
        table_firm_summary["EMPTY"] += 1

findings: list[str] = []
warnings: list[str] = []
blockers: list[str] = []

if branch["stdout"]:
    findings.append(
        f"Active branch is {branch['stdout']}."
    )

if head["stdout"]:
    findings.append(
        f"Active HEAD is {head['stdout']}."
    )

if database.get("integrity") == "ok":
    findings.append(
        "SQLite integrity check returned ok."
    )
else:
    blockers.append(
        "SQLite integrity check did not return ok."
    )

if db_hash_before == db_hash_after:
    findings.append(
        "Live database hash remained unchanged during the audit."
    )
else:
    blockers.append(
        "Live database hash changed during a read-only audit."
    )

if not routes:
    warnings.append(
        "No Matter or Intake routes were identified by the route scanner."
    )

if route_counts.get("MATTER_INTAKE_INTEGRATION", 0) == 0:
    warnings.append(
        "No route name or endpoint was automatically classified as an explicit "
        "Matter–Intake integration route."
    )

mixed_tables = [
    table["table"]
    for table in database.get("tables", [])
    if table.get("firm_distribution")
    and len(
        [
            firm
            for firm, count in table["firm_distribution"].items()
            if count
        ]
    ) > 1
]

if mixed_tables:
    blockers.append(
        f"{len(mixed_tables)} relevant table(s) contain multiple firm/null scopes."
    )

null_firm_tables = []

for table in database.get("tables", []):
    distribution = table.get("firm_distribution") or {}

    if distribution.get("[NULL]", 0):
        null_firm_tables.append(
            {
                "table": table["table"],
                "null_rows": distribution["[NULL]"],
            }
        )

if null_firm_tables:
    blockers.append(
        f"{sum(item['null_rows'] for item in null_firm_tables)} null-firm row(s) "
        f"exist across {len(null_firm_tables)} relevant table(s)."
    )

report = {
    "audit": {
        "id": "MIA-0A",
        "title": "Matter and Intake Implementation Baseline",
        "created_at": datetime.now().isoformat(),
        "root": str(ROOT),
        "status": (
            "BASELINE_COMPLETE_REVIEW_REQUIRED"
            if not blockers
            else "BASELINE_COMPLETE_BLOCKERS_IDENTIFIED"
        ),
    },
    "repository": {
        "branch": branch,
        "head": head,
        "last_commit": last_commit,
        "git_status": status,
    },
    "database_safety": {
        "path": str(LIVE_DB),
        "sha256_before": db_hash_before,
        "sha256_after": db_hash_after,
        "unchanged": db_hash_before == db_hash_after,
    },
    "routes": {
        "count": len(routes),
        "classification_counts": dict(route_counts),
        "items": routes,
    },
    "python_functions": {
        "app_py": app_functions,
        "database_db_py": db_functions,
    },
    "templates": {
        "count": len(templates),
        "items": templates,
    },
    "database": database,
    "relevant_table_firm_summary": dict(table_firm_summary),
    "mixed_relevant_tables": mixed_tables,
    "null_firm_relevant_tables": null_firm_tables,
    "findings": findings,
    "warnings": warnings,
    "blockers": blockers,
    "next_gate": (
        "MIA-0B — Matter–Intake linkage and authority trace"
    ),
}

JSON_PATH.write_text(
    json.dumps(report, indent=2, default=str),
    encoding="utf-8",
)

md: list[str] = []

md.append("# MIA-0A — Matter and Intake Implementation Baseline")
md.append("")
md.append(f"**Status:** {report['audit']['status']}")
md.append(f"**Created:** {report['audit']['created_at']}")
md.append("")
md.append("## Repository")
md.append("")
md.append(f"- Branch: `{branch['stdout'] or 'UNKNOWN'}`")
md.append(f"- HEAD: `{head['stdout'] or 'UNKNOWN'}`")
md.append("- Last commit:")
md.append("")
md.append("```text")
md.append(last_commit["stdout"] or last_commit["stderr"] or "UNKNOWN")
md.append("```")
md.append("")
md.append("## Database Safety")
md.append("")
md.append(f"- Database: `{LIVE_DB}`")
md.append(f"- Integrity: `{database.get('integrity')}`")
md.append(f"- SHA-256 before: `{db_hash_before}`")
md.append(f"- SHA-256 after: `{db_hash_after}`")
md.append(f"- Live database unchanged: `{db_hash_before == db_hash_after}`")
md.append("")
md.append("## Route Summary")
md.append("")
md.append(f"- Total relevant routes: **{len(routes)}**")

for classification, count in sorted(route_counts.items()):
    md.append(f"- {classification}: **{count}**")

md.append("")
md.append("## Relevant Routes")
md.append("")

for route in routes:
    methods = ",".join(route["methods"])

    md.append(
        f"- `{methods} {route['route']}` "
        f"→ `{route['function']}` "
        f"at `app.py:{route['function_line'] or route['decorator_line']}` "
        f"[{route['classification']}]"
    )

md.append("")
md.append("## Database Tables")
md.append("")
md.append(
    f"- Total database tables: **{database.get('all_table_count', 0)}**"
)
md.append(
    f"- Matter/Intake relevant tables: "
    f"**{database.get('selected_table_count', 0)}**"
)
md.append("")

for table in database.get("tables", []):
    md.append(f"### `{table['table']}`")
    md.append("")
    md.append(f"- Rows: **{table['row_count']}**")
    md.append(
        f"- Linkage columns: "
        f"`{', '.join(table['linkage_columns']) or 'None detected'}`"
    )
    md.append(
        f"- Firm distribution: "
        f"`{table['firm_distribution']}`"
    )
    md.append("")

md.append("## Relevant Python Functions")
md.append("")

for function in app_functions + db_functions:
    md.append(
        f"- `{function['source']}:{function['line']}` "
        f"`{function['name']}({function['signature']})`"
    )

md.append("")
md.append("## Relevant Templates")
md.append("")

for template in templates:
    md.append(
        f"- `{template['path']}` "
        f"references={template['references']}"
    )

md.append("")
md.append("## Findings")
md.append("")

for item in findings:
    md.append(f"- {item}")

if not findings:
    md.append("- None recorded.")

md.append("")
md.append("## Warnings")
md.append("")

for item in warnings:
    md.append(f"- {item}")

if not warnings:
    md.append("- None recorded.")

md.append("")
md.append("## Blockers")
md.append("")

for item in blockers:
    md.append(f"- {item}")

if not blockers:
    md.append("- None identified by this baseline audit.")

md.append("")
md.append("## Next Gate")
md.append("")
md.append(
    "**MIA-0B — Matter–Intake linkage and authority trace**"
)

MD_PATH.write_text(
    "\n".join(md) + "\n",
    encoding="utf-8",
)

print()
print("MIA-0A BASELINE COMPLETE")
print(f"Status: {report['audit']['status']}")
print(f"Branch: {branch['stdout'] or 'UNKNOWN'}")
print(f"HEAD: {head['stdout'] or 'UNKNOWN'}")
print(f"Database Integrity: {database.get('integrity')}")
print(f"Live Database Unchanged: {db_hash_before == db_hash_after}")
print(f"Relevant Routes: {len(routes)}")
print(f"Relevant Templates: {len(templates)}")
print(
    f"Relevant Database Tables: "
    f"{database.get('selected_table_count', 0)}"
)
print(
    f"Explicit Matter–Intake Integration Routes: "
    f"{route_counts.get('MATTER_INTAKE_INTEGRATION', 0)}"
)
print(f"Mixed Relevant Tables: {len(mixed_tables)}")
print(
    f"Null-Firm Relevant Rows: "
    f"{sum(item['null_rows'] for item in null_firm_tables)}"
)

if blockers:
    print()
    print("BLOCKERS:")

    for blocker in blockers:
        print(f"- {blocker}")

if warnings:
    print()
    print("WARNINGS:")

    for warning in warnings:
        print(f"- {warning}")

print()
print(f"JSON REPORT: {JSON_PATH.relative_to(ROOT)}")
print(f"MARKDOWN REPORT: {MD_PATH.relative_to(ROOT)}")
print("=== MIA-0A COMPLETE ===")
