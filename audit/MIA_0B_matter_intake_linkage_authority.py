from __future__ import annotations

import ast
import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


print("=== MIA-0B — MATTER–INTAKE LINKAGE AND AUTHORITY TRACE ===")

ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = ROOT / "audit"
APP_PATH = ROOT / "app.py"
DB_MODULE_PATH = ROOT / "database" / "db.py"
TEMPLATE_DIR = ROOT / "templates"
LIVE_DB = ROOT / "trustee_app.db"

EXPECTED_BRANCH = "strapback/stable-661bb66"
EXPECTED_HEAD = "1cf6497598d9d294bc0453847b896316f863c241"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

JSON_PATH = AUDIT_DIR / f"MIA-0B_matter_intake_linkage_authority_{STAMP}.json"
MD_PATH = AUDIT_DIR / f"MIA-0B_matter_intake_linkage_authority_{STAMP}.md"

AUTHORITY_TERMS = {
    "status",
    "matter_status",
    "intake_status",
    "governance_state",
    "risk_level",
    "risk",
    "priority",
    "complexity",
    "readiness",
    "readiness_status",
    "review_status",
    "drafting_status",
    "execution_status",
    "archive_status",
    "completion_status",
    "finalization_status",
    "approval_status",
    "verification_status",
    "stage",
    "state",
}

LINKAGE_TERMS = {
    "matter_id",
    "intake_id",
    "session_id",
    "trust_id",
    "relationship_id",
    "workspace_id",
    "document_id",
    "task_id",
    "event_id",
    "firm_id",
}

MATTER_TERMS = (
    "matter",
    "matter_id",
    "matter_events",
    "matter_relationships",
)

INTAKE_TERMS = (
    "intake",
    "intake_id",
    "intake_sessions",
    "intake_answers",
)

HANDOFF_TERMS = (
    "create_matter",
    "new_matter",
    "matter_id",
    "intake_id",
    "relationship",
    "risk",
    "priority",
    "readiness",
    "governance",
    "event",
    "task",
    "recommendation",
    "draft",
    "execution",
    "archive",
)

ID_COLUMNS = (
    "id",
    "matter_id",
    "intake_id",
    "session_id",
    "trust_id",
    "relationship_id",
    "workspace_id",
    "document_id",
    "task_id",
    "event_id",
)

SENSITIVE_TERMS = (
    "password",
    "secret",
    "token",
    "hash",
    "ssn",
    "tax_id",
    "ein",
)


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


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def latest_report(pattern: str) -> tuple[Path | None, dict[str, Any] | None]:
    reports = sorted(
        AUDIT_DIR.glob(pattern),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not reports:
        return None, None

    path = reports[0]

    try:
        return path, json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return path, None


def get_table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    return [row[0] for row in rows]


def table_columns(
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


def foreign_keys(
    connection: sqlite3.Connection,
    table_name: str,
) -> list[dict[str, Any]]:
    quoted = table_name.replace('"', '""')

    rows = connection.execute(
        f'PRAGMA foreign_key_list("{quoted}")'
    ).fetchall()

    return [
        {
            "id": row[0],
            "seq": row[1],
            "to_table": row[2],
            "from_column": row[3],
            "to_column": row[4],
            "on_update": row[5],
            "on_delete": row[6],
        }
        for row in rows
    ]


def safe_row_sample(
    connection: sqlite3.Connection,
    table_name: str,
    columns: list[str],
    limit: int = 5,
) -> list[dict[str, Any]]:
    safe_columns = [
        column
        for column in columns
        if not any(term in column.lower() for term in SENSITIVE_TERMS)
    ]

    if not safe_columns:
        return []

    quoted_table = table_name.replace('"', '""')
    quoted_columns = ", ".join(
        f'"{column.replace(chr(34), chr(34) * 2)}"'
        for column in safe_columns[:12]
    )

    try:
        rows = connection.execute(
            f'''
            SELECT {quoted_columns}
            FROM "{quoted_table}"
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
    except sqlite3.Error:
        return []

    return [
        {
            safe_columns[index]: row[index]
            for index in range(min(len(safe_columns), len(row)))
        }
        for row in rows
    ]


def identify_relevant_tables(
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for table_name in get_table_names(connection):
        columns = table_columns(connection, table_name)
        names = [column["name"] for column in columns]
        lowered = [name.lower() for name in names]

        is_matter = (
            "matter" in table_name.lower()
            or any("matter" in name for name in lowered)
        )

        is_intake = (
            "intake" in table_name.lower()
            or any("intake" in name for name in lowered)
        )

        authority_columns = [
            name
            for name in names
            if (
                name.lower() in AUTHORITY_TERMS
                or any(
                    term in name.lower()
                    for term in (
                        "status",
                        "risk",
                        "priority",
                        "readiness",
                        "complexity",
                        "governance",
                        "approval",
                        "verification",
                        "completion",
                        "finalization",
                    )
                )
            )
        ]

        linkage_columns = [
            name
            for name in names
            if (
                name.lower() in LINKAGE_TERMS
                or any(
                    term in name.lower()
                    for term in (
                        "matter_id",
                        "intake_id",
                        "session_id",
                        "trust_id",
                        "relationship_id",
                        "workspace_id",
                        "document_id",
                        "task_id",
                        "event_id",
                    )
                )
            )
        ]

        if not (
            is_matter
            or is_intake
            or authority_columns
            or (
                "matter_id" in lowered
                and "intake_id" in lowered
            )
        ):
            continue

        quoted = table_name.replace('"', '""')

        try:
            row_count = connection.execute(
                f'SELECT COUNT(*) FROM "{quoted}"'
            ).fetchone()[0]
        except sqlite3.Error:
            row_count = None

        firm_distribution = None

        if "firm_id" in lowered:
            try:
                rows = connection.execute(
                    f'''
                    SELECT
                        COALESCE(firm_id, '[NULL]') AS firm_value,
                        COUNT(*)
                    FROM "{quoted}"
                    GROUP BY COALESCE(firm_id, '[NULL]')
                    ORDER BY firm_value
                    '''
                ).fetchall()

                firm_distribution = {
                    row[0]: row[1]
                    for row in rows
                }
            except sqlite3.Error:
                firm_distribution = None

        results.append(
            {
                "table": table_name,
                "classification": (
                    "MATTER_INTAKE_BRIDGE"
                    if is_matter and is_intake
                    else "MATTER"
                    if is_matter
                    else "INTAKE"
                    if is_intake
                    else "AUTHORITY_SUPPORT"
                ),
                "row_count": row_count,
                "columns": columns,
                "linkage_columns": linkage_columns,
                "authority_columns": authority_columns,
                "foreign_keys": foreign_keys(connection, table_name),
                "firm_distribution": firm_distribution,
                "sample": safe_row_sample(
                    connection,
                    table_name,
                    [
                        name
                        for name in names
                        if (
                            name.lower() in ID_COLUMNS
                            or name in linkage_columns
                            or name in authority_columns
                            or name.lower()
                            in {
                                "title",
                                "name",
                                "created_at",
                                "updated_at",
                                "created_by",
                                "reviewed_by",
                            }
                        )
                    ],
                ),
            }
        )

    return results


def extract_route_blocks(app_text: str) -> list[dict[str, Any]]:
    lines = app_text.splitlines()
    route_pattern = re.compile(
        r'''@app\.route\(\s*["']([^"']+)["'](?:\s*,\s*methods\s*=\s*\[([^\]]*)\])?'''
    )
    def_pattern = re.compile(
        r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
    )

    routes: list[dict[str, Any]] = []

    for index, line in enumerate(lines):
        route_match = route_pattern.search(line)

        if not route_match:
            continue

        route_path = route_match.group(1)
        methods = re.findall(
            r'''["']([A-Z]+)["']''',
            route_match.group(2) or "",
        ) or ["GET"]

        function_name = None
        function_line = None
        block_start = None

        for lookahead in range(index + 1, min(index + 20, len(lines))):
            match = def_pattern.match(lines[lookahead])

            if match:
                function_name = match.group(1)
                function_line = lookahead + 1
                block_start = lookahead
                break

        if function_name is None or block_start is None:
            continue

        block_end = len(lines)

        for lookahead in range(block_start + 1, len(lines)):
            if (
                lines[lookahead].startswith("@app.route")
                or re.match(
                    r"^def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(",
                    lines[lookahead],
                )
            ):
                block_end = lookahead
                break

        block_text = "\n".join(lines[block_start:block_end])
        combined = f"{route_path}\n{function_name}\n{block_text}".lower()

        has_matter = any(term in combined for term in MATTER_TERMS)
        has_intake = any(term in combined for term in INTAKE_TERMS)

        if not has_matter and not has_intake:
            continue

        routes.append(
            {
                "route": route_path,
                "methods": methods,
                "function": function_name,
                "decorator_line": index + 1,
                "function_line": function_line,
                "classification": (
                    "MATTER_INTAKE_INTEGRATION"
                    if has_matter and has_intake
                    else "MATTER"
                    if has_matter
                    else "INTAKE"
                ),
                "matter_references": sorted(
                    {
                        term
                        for term in MATTER_TERMS
                        if term in combined
                    }
                ),
                "intake_references": sorted(
                    {
                        term
                        for term in INTAKE_TERMS
                        if term in combined
                    }
                ),
                "handoff_references": sorted(
                    {
                        term
                        for term in HANDOFF_TERMS
                        if term in combined
                    }
                ),
                "db_function_calls": sorted(
                    set(
                        re.findall(
                            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                            block_text,
                        )
                    )
                ),
            }
        )

    return routes


def function_inventory(
    source_text: str,
    source_name: str,
) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return []

    lines = source_text.splitlines()
    results: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        start = node.lineno
        end = getattr(node, "end_lineno", node.lineno)
        block_text = "\n".join(lines[start - 1:end])
        lowered = block_text.lower()

        has_matter = any(term in lowered for term in MATTER_TERMS)
        has_intake = any(term in lowered for term in INTAKE_TERMS)

        if not has_matter and not has_intake:
            continue

        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)

        results.append(
            {
                "source": source_name,
                "name": node.name,
                "line_start": start,
                "line_end": end,
                "classification": (
                    "MATTER_INTAKE_INTEGRATION"
                    if has_matter and has_intake
                    else "MATTER"
                    if has_matter
                    else "INTAKE"
                ),
                "calls": sorted(set(calls)),
                "authority_terms": sorted(
                    {
                        term
                        for term in AUTHORITY_TERMS
                        if term in lowered
                    }
                ),
                "handoff_terms": sorted(
                    {
                        term
                        for term in HANDOFF_TERMS
                        if term in lowered
                    }
                ),
            }
        )

    return results


def template_inventory() -> list[dict[str, Any]]:
    results = []

    if not TEMPLATE_DIR.exists():
        return results

    for path in sorted(TEMPLATE_DIR.rglob("*.html")):
        text = read_text(path)
        lowered = text.lower()
        relative = path.relative_to(ROOT).as_posix()

        has_matter = any(term in lowered for term in MATTER_TERMS)
        has_intake = any(term in lowered for term in INTAKE_TERMS)

        if not (
            has_matter
            or has_intake
            or "matter" in relative.lower()
            or "intake" in relative.lower()
        ):
            continue

        results.append(
            {
                "path": relative,
                "classification": (
                    "MATTER_INTAKE_INTEGRATION"
                    if has_matter and has_intake
                    else "MATTER"
                    if has_matter or "matter" in relative.lower()
                    else "INTAKE"
                ),
                "matter_references": sum(
                    lowered.count(term)
                    for term in MATTER_TERMS
                ),
                "intake_references": sum(
                    lowered.count(term)
                    for term in INTAKE_TERMS
                ),
                "authority_terms": sorted(
                    {
                        term
                        for term in AUTHORITY_TERMS
                        if term in lowered
                    }
                ),
                "linked_routes": sorted(
                    set(
                        re.findall(
                            r'''url_for\(\s*["']([^"']+)["']''',
                            text,
                        )
                    )
                ),
            }
        )

    return results


def build_authority_map(
    tables: list[dict[str, Any]],
    functions: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> dict[str, Any]:
    authority_map: dict[str, Any] = {}

    concepts = (
        "status",
        "risk",
        "priority",
        "complexity",
        "readiness",
        "governance",
        "review",
        "drafting",
        "execution",
        "archive",
        "completion",
        "verification",
        "finalization",
        "approval",
    )

    for concept in concepts:
        matter_tables = []
        intake_tables = []
        support_tables = []
        function_hits = []
        route_hits = []

        for table in tables:
            matching_columns = [
                column
                for column in table["authority_columns"]
                if concept in column.lower()
            ]

            if not matching_columns:
                continue

            entry = {
                "table": table["table"],
                "columns": matching_columns,
            }

            if table["classification"] == "MATTER":
                matter_tables.append(entry)
            elif table["classification"] == "INTAKE":
                intake_tables.append(entry)
            else:
                support_tables.append(entry)

        for function in functions:
            matching = [
                term
                for term in function["authority_terms"]
                if concept in term
            ]

            if matching:
                function_hits.append(
                    {
                        "source": function["source"],
                        "name": function["name"],
                        "line": function["line_start"],
                        "classification": function["classification"],
                        "terms": matching,
                    }
                )

        for route in routes:
            combined = " ".join(
                route["handoff_references"]
                + route["matter_references"]
                + route["intake_references"]
            ).lower()

            if concept in combined:
                route_hits.append(
                    {
                        "route": route["route"],
                        "function": route["function"],
                        "classification": route["classification"],
                    }
                )

        if matter_tables and intake_tables:
            ownership_assessment = "DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED"
        elif matter_tables:
            ownership_assessment = "MATTER_APPEARS_PRIMARY"
        elif intake_tables:
            ownership_assessment = "INTAKE_APPEARS_PRIMARY"
        elif support_tables:
            ownership_assessment = "SUPPORT_TABLE_AUTHORITY_REVIEW_REQUIRED"
        else:
            ownership_assessment = "NO_STRUCTURED_AUTHORITY_DETECTED"

        authority_map[concept] = {
            "assessment": ownership_assessment,
            "matter_tables": matter_tables,
            "intake_tables": intake_tables,
            "support_tables": support_tables,
            "function_hits": function_hits,
            "route_hits": route_hits,
        }

    return authority_map


branch = run_git("branch", "--show-current")
head = run_git("rev-parse", "HEAD")
status = run_git("status", "--short")

if branch["stdout"] != EXPECTED_BRANCH:
    raise SystemExit(
        f"ERROR: Expected branch {EXPECTED_BRANCH}, found {branch['stdout']}"
    )

if head["stdout"] != EXPECTED_HEAD:
    raise SystemExit(
        f"ERROR: Expected HEAD {EXPECTED_HEAD}, found {head['stdout']}"
    )

db_hash_before = sha256(LIVE_DB)

mia0a_path, mia0a_report = latest_report(
    "MIA-0A_matter_intake_baseline_*.json"
)

if mia0a_path is None:
    raise SystemExit(
        "ERROR: No MIA-0A JSON report found. "
        "MIA-0A must exist before MIA-0B."
    )

connection = sqlite3.connect(
    f"file:{LIVE_DB.as_posix()}?mode=ro",
    uri=True,
)

try:
    integrity_row = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()

    integrity = integrity_row[0] if integrity_row else None

    tables = identify_relevant_tables(connection)

finally:
    connection.close()

app_text = read_text(APP_PATH)
db_text = read_text(DB_MODULE_PATH)

routes = extract_route_blocks(app_text)

functions = (
    function_inventory(app_text, "app.py")
    + function_inventory(db_text, "database/db.py")
)

templates = template_inventory()

authority_map = build_authority_map(
    tables,
    functions,
    routes,
)

direct_bridge_tables = [
    table
    for table in tables
    if (
        any(
            column["name"].lower() == "matter_id"
            for column in table["columns"]
        )
        and any(
            column["name"].lower() == "intake_id"
            for column in table["columns"]
        )
    )
]

integration_routes = [
    route
    for route in routes
    if route["classification"] == "MATTER_INTAKE_INTEGRATION"
]

integration_functions = [
    function
    for function in functions
    if function["classification"] == "MATTER_INTAKE_INTEGRATION"
]

integration_templates = [
    template
    for template in templates
    if template["classification"] == "MATTER_INTAKE_INTEGRATION"
]

matter_tables = [
    table["table"]
    for table in tables
    if table["classification"] == "MATTER"
]

intake_tables = [
    table["table"]
    for table in tables
    if table["classification"] == "INTAKE"
]

bridge_tables = [
    table["table"]
    for table in direct_bridge_tables
]

mixed_firm_tables = []

for table in tables:
    distribution = table.get("firm_distribution") or {}

    nonzero = [
        firm
        for firm, count in distribution.items()
        if count
    ]

    if len(nonzero) > 1:
        mixed_firm_tables.append(
            {
                "table": table["table"],
                "distribution": distribution,
            }
        )

findings: list[str] = []
warnings: list[str] = []
blockers: list[str] = []

if integrity == "ok":
    findings.append("SQLite integrity check returned ok.")
else:
    blockers.append("SQLite integrity check did not return ok.")

if direct_bridge_tables:
    findings.append(
        f"{len(direct_bridge_tables)} table(s) contain both matter_id and intake_id."
    )
else:
    warnings.append(
        "No relevant table contains both matter_id and intake_id."
    )

if integration_routes:
    findings.append(
        f"{len(integration_routes)} route(s) contain both Matter and Intake references."
    )
else:
    warnings.append(
        "No route block contains both Matter and Intake references."
    )

if integration_functions:
    findings.append(
        f"{len(integration_functions)} function(s) contain both Matter and Intake references."
    )
else:
    warnings.append(
        "No Python function contains both Matter and Intake references."
    )

if integration_templates:
    findings.append(
        f"{len(integration_templates)} template(s) contain both Matter and Intake references."
    )
else:
    warnings.append(
        "No template contains both Matter and Intake references."
    )

duplicated_authority = [
    concept
    for concept, data in authority_map.items()
    if data["assessment"]
    == "DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED"
]

if duplicated_authority:
    blockers.append(
        "Potential duplicated/shared authority detected for: "
        + ", ".join(sorted(duplicated_authority))
    )

if mixed_firm_tables:
    blockers.append(
        f"{len(mixed_firm_tables)} relevant table(s) contain mixed firm scopes."
    )

db_hash_after = sha256(LIVE_DB)

if db_hash_before != db_hash_after:
    blockers.append(
        "Live database hash changed during the read-only trace."
    )
else:
    findings.append(
        "Live database hash remained unchanged."
    )

architecture_assessment: str

if (
    direct_bridge_tables
    and integration_functions
    and not duplicated_authority
):
    architecture_assessment = (
        "MATTER_INTAKE_INTEGRATION_PRESENT_AUTHORITY_APPEARS_SEPARABLE"
    )
elif (
    direct_bridge_tables
    or integration_routes
    or integration_functions
    or integration_templates
):
    architecture_assessment = (
        "PARTIAL_MATTER_INTAKE_INTEGRATION_REPAIR_REQUIRED"
    )
else:
    architecture_assessment = (
        "MATTER_AND_INTAKE_APPEAR_ADJACENT_NOT_INTEGRATED"
    )

report = {
    "audit": {
        "id": "MIA-0B",
        "title": "Matter–Intake Linkage and Authority Trace",
        "created_at": datetime.now().isoformat(),
        "status": "TRACE_COMPLETE_REVIEW_REQUIRED",
        "architecture_assessment": architecture_assessment,
    },
    "repository": {
        "root": str(ROOT),
        "branch": branch["stdout"],
        "head": head["stdout"],
        "git_status": status["stdout"],
    },
    "source_report": {
        "mia0a_path": str(mia0a_path.relative_to(ROOT)),
        "mia0a_loaded": mia0a_report is not None,
    },
    "database_safety": {
        "path": str(LIVE_DB),
        "integrity": integrity,
        "sha256_before": db_hash_before,
        "sha256_after": db_hash_after,
        "unchanged": db_hash_before == db_hash_after,
    },
    "table_summary": {
        "matter_tables": matter_tables,
        "intake_tables": intake_tables,
        "direct_bridge_tables": bridge_tables,
        "mixed_firm_tables": mixed_firm_tables,
    },
    "tables": tables,
    "routes": {
        "total_relevant": len(routes),
        "integration_count": len(integration_routes),
        "integration_routes": integration_routes,
        "items": routes,
    },
    "functions": {
        "total_relevant": len(functions),
        "integration_count": len(integration_functions),
        "integration_functions": integration_functions,
        "items": functions,
    },
    "templates": {
        "total_relevant": len(templates),
        "integration_count": len(integration_templates),
        "integration_templates": integration_templates,
        "items": templates,
    },
    "authority_map": authority_map,
    "duplicated_or_shared_authority": duplicated_authority,
    "findings": findings,
    "warnings": warnings,
    "blockers": blockers,
    "next_gate": (
        "MIA-0C — Matter–Intake Architectural Adoption and Repair Decision"
    ),
}

JSON_PATH.write_text(
    json.dumps(report, indent=2, default=str),
    encoding="utf-8",
)

md: list[str] = []

md.append("# MIA-0B — Matter–Intake Linkage and Authority Trace")
md.append("")
md.append(f"**Status:** `{report['audit']['status']}`")
md.append(
    f"**Architecture Assessment:** "
    f"`{architecture_assessment}`"
)
md.append(f"**Created:** `{report['audit']['created_at']}`")
md.append("")
md.append("## Repository")
md.append("")
md.append(f"- Branch: `{branch['stdout']}`")
md.append(f"- HEAD: `{head['stdout']}`")
md.append(f"- Source MIA-0A: `{mia0a_path.relative_to(ROOT)}`")
md.append("")
md.append("## Database Safety")
md.append("")
md.append(f"- Integrity: `{integrity}`")
md.append(f"- SHA-256 before: `{db_hash_before}`")
md.append(f"- SHA-256 after: `{db_hash_after}`")
md.append(f"- Database unchanged: `{db_hash_before == db_hash_after}`")
md.append("")
md.append("## Linkage Summary")
md.append("")
md.append(f"- Matter tables: **{len(matter_tables)}**")
md.append(f"- Intake tables: **{len(intake_tables)}**")
md.append(
    f"- Tables containing both matter_id and intake_id: "
    f"**{len(direct_bridge_tables)}**"
)
md.append(
    f"- Integration routes: **{len(integration_routes)}**"
)
md.append(
    f"- Integration functions: **{len(integration_functions)}**"
)
md.append(
    f"- Integration templates: **{len(integration_templates)}**"
)
md.append("")
md.append("## Direct Bridge Tables")
md.append("")

if direct_bridge_tables:
    for table in direct_bridge_tables:
        md.append(
            f"- `{table['table']}` "
            f"rows={table['row_count']} "
            f"firm_distribution={table['firm_distribution']}"
        )
else:
    md.append("- None detected.")

md.append("")
md.append("## Matter–Intake Integration Routes")
md.append("")

if integration_routes:
    for route in integration_routes:
        md.append(
            f"- `{','.join(route['methods'])} {route['route']}` "
            f"→ `{route['function']}` at `app.py:{route['function_line']}`"
        )
else:
    md.append("- None detected.")

md.append("")
md.append("## Matter–Intake Integration Functions")
md.append("")

if integration_functions:
    for function in integration_functions:
        md.append(
            f"- `{function['source']}:{function['line_start']}` "
            f"`{function['name']}`"
        )
else:
    md.append("- None detected.")

md.append("")
md.append("## Authority Map")
md.append("")

for concept, data in authority_map.items():
    md.append(f"### {concept.title()}")
    md.append("")
    md.append(f"- Assessment: `{data['assessment']}`")

    if data["matter_tables"]:
        md.append("- Matter tables:")

        for entry in data["matter_tables"]:
            md.append(
                f"  - `{entry['table']}` → "
                f"`{', '.join(entry['columns'])}`"
            )

    if data["intake_tables"]:
        md.append("- Intake tables:")

        for entry in data["intake_tables"]:
            md.append(
                f"  - `{entry['table']}` → "
                f"`{', '.join(entry['columns'])}`"
            )

    if data["support_tables"]:
        md.append("- Support tables:")

        for entry in data["support_tables"]:
            md.append(
                f"  - `{entry['table']}` → "
                f"`{', '.join(entry['columns'])}`"
            )

    md.append("")

md.append("## Mixed-Firm Relevant Tables")
md.append("")

if mixed_firm_tables:
    for table in mixed_firm_tables:
        md.append(
            f"- `{table['table']}` → `{table['distribution']}`"
        )
else:
    md.append("- None detected.")

md.append("")
md.append("## Findings")
md.append("")

for finding in findings:
    md.append(f"- {finding}")

if not findings:
    md.append("- None.")

md.append("")
md.append("## Warnings")
md.append("")

for warning in warnings:
    md.append(f"- {warning}")

if not warnings:
    md.append("- None.")

md.append("")
md.append("## Blockers")
md.append("")

for blocker in blockers:
    md.append(f"- {blocker}")

if not blockers:
    md.append("- None detected by this trace.")

md.append("")
md.append("## Next Gate")
md.append("")
md.append(
    "**MIA-0C — Matter–Intake Architectural Adoption and Repair Decision**"
)

MD_PATH.write_text(
    "\n".join(md) + "\n",
    encoding="utf-8",
)

print()
print("MIA-0B TRACE COMPLETE")
print(f"Status: {report['audit']['status']}")
print(f"Architecture Assessment: {architecture_assessment}")
print(f"Database Integrity: {integrity}")
print(f"Live Database Unchanged: {db_hash_before == db_hash_after}")
print(f"Matter Tables: {len(matter_tables)}")
print(f"Intake Tables: {len(intake_tables)}")
print(f"Direct Bridge Tables: {len(direct_bridge_tables)}")
print(f"Integration Routes: {len(integration_routes)}")
print(f"Integration Functions: {len(integration_functions)}")
print(f"Integration Templates: {len(integration_templates)}")
print(f"Duplicated/Shared Authority Areas: {len(duplicated_authority)}")
print(f"Mixed-Firm Relevant Tables: {len(mixed_firm_tables)}")

if direct_bridge_tables:
    print()
    print("DIRECT BRIDGE TABLES:")

    for table in direct_bridge_tables:
        print(
            f"- {table['table']} | "
            f"rows={table['row_count']} | "
            f"firms={table['firm_distribution']}"
        )

if integration_routes:
    print()
    print("INTEGRATION ROUTES:")

    for route in integration_routes:
        print(
            f"- {','.join(route['methods'])} "
            f"{route['route']} | "
            f"{route['function']} | "
            f"app.py:{route['function_line']}"
        )

if duplicated_authority:
    print()
    print("DUPLICATED OR SHARED AUTHORITY:")

    for concept in duplicated_authority:
        print(f"- {concept}")

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
print("NEXT: MIA-0C — MATTER–INTAKE ARCHITECTURAL ADOPTION AND REPAIR DECISION")
print("=== MIA-0B COMPLETE ===")
