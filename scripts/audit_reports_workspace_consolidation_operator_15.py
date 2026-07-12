from pathlib import Path
import ast
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
IOS_TEMPLATE = ROOT / "templates" / "ios_workspace.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTOR = "ab657dd"
ALLOWED_BRANCHES = {"post-v2-planning"}

REPORT_TERMS = [
    "report",
    "reports",
    "dashboard",
    "summary",
    "export",
    "certificate",
    "certification",
    "evidence",
    "audit",
    "manifest",
    "integrity",
    "ledger",
    "history",
    "registry",
    "snapshot",
    "analytics",
]

PROTECTED_TERMS = [
    "delete",
    "restore",
    "reseed",
    "recovery/run",
    "freeze",
    "finalize",
    "approve",
    "ratify",
    "supersede",
    "retire",
    "reinstate",
    "execute",
    "mutation",
]

CENTRAL_CANDIDATE_HINTS = [
    "report",
    "reports",
    "dashboard",
    "summary",
    "registry",
    "history",
    "audit",
    "evidence",
    "certificate",
    "certification",
    "manifest",
    "integrity",
    "analytics",
]

CONTEXTUAL_HINTS = [
    "<trust_id>",
    "<matter_id>",
    "<execution_id>",
    "<transfer_id>",
    "<property_id>",
    "<document_id>",
    "<event_id>",
    "<relationship_id>",
    "<certification_id>",
    "<object_id>",
]

checks = []
failures = []


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def record(name, passed, detail):
    checks.append((name, passed, detail))
    if not passed:
        failures.append(name)


def route_methods_from_app(text):
    tree = ast.parse(text)
    lines = text.splitlines()
    routes = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            func = decorator.func
            attr = getattr(func, "attr", None)

            if attr != "route":
                continue

            if not decorator.args:
                continue

            route_arg = decorator.args[0]

            if not isinstance(route_arg, ast.Constant):
                continue

            route = str(route_arg.value)
            methods = ["GET"]

            for keyword in decorator.keywords:
                if keyword.arg != "methods":
                    continue

                if isinstance(keyword.value, (ast.List, ast.Tuple)):
                    methods = [
                        str(item.value)
                        for item in keyword.value.elts
                        if isinstance(item, ast.Constant)
                    ]

            routes.append(
                {
                    "route": route,
                    "methods": methods,
                    "function": node.name,
                    "line": node.lineno,
                    "source": "\n".join(
                        lines[node.lineno - 1 : (node.end_lineno or node.lineno)]
                    ),
                }
            )

    return routes


print("POST-V2-15 REPORTS WORKSPACE CONSOLIDATION AND OPERATOR AUDIT")
print("=" * 88)

branch = git("branch", "--show-current")
record(
    "branch allowed",
    branch in ALLOWED_BRANCHES,
    branch or "unknown",
)

head = git("rev-parse", "HEAD")
ancestor_check = subprocess.run(
    ["git", "merge-base", "--is-ancestor", REQUIRED_ANCESTOR, "HEAD"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
record(
    "published POST-V2-14B.2 retained in ancestry",
    ancestor_check.returncode == 0,
    head or "missing",
)

certified_commit = git(
    "rev-parse",
    f"{CERTIFIED_TAG}^{{commit}}",
)
record(
    "certified V2 tag protected",
    certified_commit == EXPECTED_CERTIFIED_COMMIT,
    certified_commit or "missing",
)

record(
    "app.py readable",
    APP.exists(),
    str(APP),
)

record(
    "Reports Workspace template readable",
    REPORTS_TEMPLATE.exists(),
    str(REPORTS_TEMPLATE),
)

record(
    "IOS host template readable",
    IOS_TEMPLATE.exists(),
    str(IOS_TEMPLATE),
)

app_text = APP.read_text(encoding="utf-8") if APP.exists() else ""
reports_text = (
    REPORTS_TEMPLATE.read_text(encoding="utf-8")
    if REPORTS_TEMPLATE.exists()
    else ""
)
ios_text = (
    IOS_TEMPLATE.read_text(encoding="utf-8")
    if IOS_TEMPLATE.exists()
    else ""
)

routes = route_methods_from_app(app_text) if app_text else []

record(
    "route inventory available",
    bool(routes),
    f"count={len(routes)}",
)

report_routes = []

for item in routes:
    combined = " ".join(
        [
            item["route"],
            item["function"],
            item["source"],
        ]
    ).lower()

    if any(term in combined for term in REPORT_TERMS):
        report_routes.append(item)

literal_links = sorted(
    {
        href
        for href in re.findall(
            r'href\s*=\s*["\']([^"\']+)["\']',
            reports_text,
            flags=re.IGNORECASE,
        )
        if "{{" not in href
        and "}}" not in href
        and "{%" not in href
        and "%}" not in href
    }
)

central_candidates = []
contextual_routes = []
protected_routes = []
read_only_routes = []
write_capable_routes = []

for item in report_routes:
    route = item["route"]
    route_lower = route.lower()
    methods = set(item["methods"])
    source_lower = item["source"].lower()

    is_contextual = any(
        hint in route
        for hint in CONTEXTUAL_HINTS
    )

    is_protected = any(
        term in route_lower or term in source_lower
        for term in PROTECTED_TERMS
    )

    is_read_only = methods == {"GET"}

    if is_contextual:
        contextual_routes.append(item)

    if is_protected:
        protected_routes.append(item)

    if is_read_only:
        read_only_routes.append(item)
    else:
        write_capable_routes.append(item)

    if (
        is_read_only
        and not is_contextual
        and not is_protected
        and any(
            hint in route_lower
            for hint in CENTRAL_CANDIDATE_HINTS
        )
    ):
        central_candidates.append(item)

record(
    "Reports Workspace operator content present",
    bool(reports_text.strip()),
    "present" if reports_text.strip() else "empty",
)

record(
    "Reports Workspace route retained",
    "/admin/workspace/<workspace_key>" in app_text
    and '"reports"' in app_text,
    "present",
)

record(
    "report-family inventory found",
    bool(report_routes),
    f"count={len(report_routes)}",
)

record(
    "Reports Workspace has no POST forms",
    'method="post"' not in reports_text.lower()
    and "method='post'" not in reports_text.lower(),
    "none",
)

exposed_protected = [
    link
    for link in literal_links
    if any(
        term in link.lower()
        for term in PROTECTED_TERMS
    )
]

record(
    "protected report operations absent from Reports Workspace",
    not exposed_protected,
    "none" if not exposed_protected else str(exposed_protected),
)

record(
    "runtime database not modified",
    not any(
        "trustee_app.db" in line.replace("\\", "/")
        for line in (git("status", "--short") or "").splitlines()
    ),
    "none",
)

unexpected_status = []

allowed_status_paths = {
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "templates/ios_workspaces/reports.html",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_workspace_read_only_status_sources_15c.py",
}

for line in (git("status", "--short") or "").splitlines():
    normalized = line.replace("\\", "/")

    if not any(
        path in normalized
        for path in allowed_status_paths
    ):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2-15 Reports audit scope",
    not unexpected_status,
    "Reports audit files only"
    if not unexpected_status
    else "\n".join(unexpected_status),
)

print()
print("CURRENT REPORTS WORKSPACE CONTENT")
print("-" * 88)
print(reports_text.strip() or "[EMPTY TEMPLATE]")

print()
print("REPORTS WORKSPACE LITERAL LINK INVENTORY")
print("-" * 88)
for link in literal_links:
    print(link)
if not literal_links:
    print("[NO LITERAL LINKS]")

print()
print("REPORT / EXPORT / DASHBOARD ROUTE INVENTORY")
print("-" * 88)

for item in report_routes:
    print(
        f"{item['route']} | "
        f"methods={item['methods']} | "
        f"function={item['function']} | "
        f"line={item['line']}"
    )

print()
print("PROPOSED REPORTS CONSOLIDATION CLASSIFICATION")
print("-" * 88)

print("CENTRAL READ-ONLY CANDIDATES")
for item in central_candidates:
    print(f"  {item['route']} | {item['function']}")
if not central_candidates:
    print("  [NONE IDENTIFIED]")

print()
print("CONTEXTUAL REPORT ROUTES")
for item in contextual_routes:
    print(
        f"  {item['route']} | "
        f"methods={item['methods']} | "
        f"{item['function']}"
    )
if not contextual_routes:
    print("  [NONE IDENTIFIED]")

print()
print("WRITE-CAPABLE OR CONFIRMATION-SENSITIVE REPORT ROUTES")
for item in write_capable_routes:
    print(
        f"  {item['route']} | "
        f"methods={item['methods']} | "
        f"{item['function']}"
    )
if not write_capable_routes:
    print("  [NONE IDENTIFIED]")

print()
print("PROTECTED / HIGH-RISK REPORT-ADJACENT ROUTES")
for item in protected_routes:
    print(
        f"  {item['route']} | "
        f"methods={item['methods']} | "
        f"{item['function']}"
    )
if not protected_routes:
    print("  [NONE IDENTIFIED]")

print()
print("POST-V2-15 OPERATOR QUESTIONS")
print("-" * 88)
print("1. Can an operator identify the institution's major report families?")
print("2. Can an operator distinguish live dashboards from generated exports?")
print("3. Can an operator distinguish central reports from record-specific reports?")
print("4. Are reports grouped by institutional purpose rather than implementation history?")
print("5. Are certificates, evidence packages, audit reports, and summaries discoverable?")
print("6. Are protected generation, mutation, recovery, and destructive controls absent?")
print("7. Can the operator return to Admin, Governance, Archive, and the originating record?")
print("8. Does the workspace explain which report is authoritative versus informational?")

print()
print("SUMMARY")
print("-" * 88)
print(f"routes_total: {len(routes)}")
print(f"report_routes_reviewed: {len(report_routes)}")
print(f"central_read_only_candidates: {len(central_candidates)}")
print(f"contextual_report_routes: {len(contextual_routes)}")
print(f"write_capable_report_routes: {len(write_capable_routes)}")
print(f"protected_report_adjacent_routes: {len(protected_routes)}")
print(f"reports_workspace_literal_links: {len(literal_links)}")
print(f"checks_total: {len(checks)}")
print(
    "checks_passed:",
    sum(1 for _, passed, _ in checks if passed),
)
print(f"checks_failed: {len(failures)}")

print()
for name, passed, detail in checks:
    print(
        f"{'PASS' if passed else 'FAIL'}: "
        f"{name} — {detail}"
    )

print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
