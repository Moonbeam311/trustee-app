from pathlib import Path
import ast
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
PRIOR_AUDIT = ROOT / "scripts" / "audit_reports_workspace_consolidation_operator_15.py"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTOR = "ab657dd"
ALLOWED_BRANCHES = {"post-v2-planning"}

CLASS_1_CENTRAL_REPORTS = {
    "/financial_summary",
    "/portfolio",
    "/reports/portfolio.pdf",
    "/audit",
    "/reports/audit.pdf",
    "/visualization/analytics",
}

CLASS_2_CENTRAL_REGISTRIES = {
    "/certificates",
    "/exports",
    "/governance/dashboard",
    "/governance/relationship-audits",
    "/governance/evidence-exports",
    "/governance/evidence-exports/certification",
    "/governance/v2-certification",
    "/governance/evidence-exports/completion-gate",
    "/governance/evidence-exports/exceptions",
    "/governance/evidence-exports/archive-intake",
    "/governance/evidence-exports/integrity",
    "/governance/evidence-exports/manifest",
    "/intake/dashboard",
    "/intake/exports",
    "/intake/modules",
    "/intake/draft-readiness",
    "/intake/review-gates",
    "/intake/final-draft-gate",
    "/intake/final-draft-approvals",
}

EXPLICITLY_EXCLUDED = {
    "/admin/certificate-object-model/CERT-000003/pdf",
    "/admin/certificate-object-model/status",
    "/admin/certificate-interface/status",
    "/admin/certificate-api/status",
    "/admin/certificate-event-bus",
    "/admin/diag/seed-execution-objects",
    "/admin/diag/execution-record/<record_id>",
    "/admin/repair/int-lifecycle-tables",
    "/hosted-repair-admin-access-once",
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
}

EXCLUDED_PREFIXES = (
    "/api/",
    "/debug/",
)

DIAGNOSTIC_TOKENS = (
    "/diag/",
    "diagnostic",
    "object-model",
    "interface/status",
    "api/status",
    "repair",
    "seed-",
)

MUTATION_TOKENS = (
    "/new",
    "/create",
    "/upload",
    "/execute",
    "/finalize",
    "/approve",
    "/ratify",
    "/resolve",
    "/toggle",
    "/run",
    "/reseed",
    "/generate",
    "/builder",
    "/edit",
    "/reset_password",
)

CONTROLLED_EXPORT_TOKENS = (
    "/export",
    ".pdf",
    ".csv",
    ".txt",
    ".zip",
    "/packet",
    "/print",
    "/download",
    "/manifest",
    "/certificate",
)

CONTEXT_PARAMETERS = (
    "<trust_id>",
    "<property_id>",
    "<execution_id>",
    "<transfer_id>",
    "<matter_id>",
    "<certificate_id>",
    "<certification_id>",
    "<instrument_id>",
    "<intake_id>",
    "<workspace_id>",
    "<export_id>",
    "<pdf_export_id>",
    "<packet_id>",
    "<event_id>",
    "<relationship_id>",
    "<audit_id>",
    "<entity_type>",
    "<entity_id>",
    "<object_type>",
    "<object_id>",
    "<path:",
)

REPORT_SIGNAL_TOKENS = (
    "report",
    "summary",
    "dashboard",
    "registry",
    "audit",
    "evidence",
    "certificate",
    "certification",
    "export",
    "manifest",
    "integrity",
    "ledger",
    "analytics",
    "portfolio",
    "financial",
)

POST_V2_15B_MARKER = (
    "POST-V2-15B REPORTS WORKSPACE OPERATOR INFORMATION ARCHITECTURE"
)

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


def extract_routes(text):
    tree = ast.parse(text)
    routes = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            if getattr(decorator.func, "attr", None) != "route":
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
                }
            )

    return routes


def report_adjacent(item):
    combined = (
        item["route"] + " " + item["function"]
    ).lower()

    return any(
        token in combined
        for token in REPORT_SIGNAL_TOKENS
    )


def classify(item):
    route = item["route"]
    route_lower = route.lower()
    function_lower = item["function"].lower()
    methods = set(item["methods"])

    if route in CLASS_1_CENTRAL_REPORTS:
        return "CLASS 1 — CENTRAL OPERATOR REPORT"

    if route in CLASS_2_CENTRAL_REGISTRIES:
        return "CLASS 2 — CENTRAL REGISTRY / OVERSIGHT"

    if (
        route in EXPLICITLY_EXCLUDED
        or route.startswith(EXCLUDED_PREFIXES)
        or any(
            token in route_lower or token in function_lower
            for token in DIAGNOSTIC_TOKENS
        )
    ):
        return "CLASS 5 — EXCLUDED / PROTECTED"

    if methods != {"GET"}:
        return "CLASS 5 — EXCLUDED / PROTECTED"

    if any(
        token in route_lower or token in function_lower
        for token in MUTATION_TOKENS
    ):
        return "CLASS 5 — EXCLUDED / PROTECTED"

    if any(
        parameter in route
        for parameter in CONTEXT_PARAMETERS
    ):
        if any(
            token in route_lower
            for token in CONTROLLED_EXPORT_TOKENS
        ):
            return "CLASS 4 — CONTROLLED EXPORT / ARTIFACT"

        return "CLASS 3 — CONTEXTUAL RECORD REPORT"

    if any(
        token in route_lower
        for token in CONTROLLED_EXPORT_TOKENS
    ):
        return "CLASS 4 — CONTROLLED EXPORT / ARTIFACT"

    return "CLASS 5 — EXCLUDED / UNRESOLVED"


print("POST-V2-15A REPORTS ROUTE CLASSIFICATION AND EXPOSURE BOUNDARY")
print("=" * 92)

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
    "POST-V2-15 discovery audit retained",
    PRIOR_AUDIT.exists(),
    str(PRIOR_AUDIT),
)

app_text = APP.read_text(encoding="utf-8") if APP.exists() else ""
template_text = (
    REPORTS_TEMPLATE.read_text(encoding="utf-8")
    if REPORTS_TEMPLATE.exists()
    else ""
)

routes = extract_routes(app_text) if app_text else []
report_routes = [
    item
    for item in routes
    if report_adjacent(item)
]

classified = {
    "CLASS 1 — CENTRAL OPERATOR REPORT": [],
    "CLASS 2 — CENTRAL REGISTRY / OVERSIGHT": [],
    "CLASS 3 — CONTEXTUAL RECORD REPORT": [],
    "CLASS 4 — CONTROLLED EXPORT / ARTIFACT": [],
    "CLASS 5 — EXCLUDED / PROTECTED": [],
    "CLASS 5 — EXCLUDED / UNRESOLVED": [],
}

for item in report_routes:
    classified[classify(item)].append(item)

route_map = {
    item["route"]: item
    for item in routes
}

missing_class_1 = sorted(
    route
    for route in CLASS_1_CENTRAL_REPORTS
    if route not in route_map
)

missing_class_2 = sorted(
    route
    for route in CLASS_2_CENTRAL_REGISTRIES
    if route not in route_map
)

non_get_central = []

for route in sorted(
    CLASS_1_CENTRAL_REPORTS | CLASS_2_CENTRAL_REGISTRIES
):
    item = route_map.get(route)

    if item and set(item["methods"]) != {"GET"}:
        non_get_central.append(
            f"{route}: {item['methods']}"
        )

record(
    "route inventory available",
    bool(routes),
    f"count={len(routes)}",
)

record(
    "report-adjacent route inventory available",
    bool(report_routes),
    f"count={len(report_routes)}",
)

record(
    "all proposed Class 1 routes exist",
    not missing_class_1,
    "all present"
    if not missing_class_1
    else str(missing_class_1),
)

record(
    "all proposed Class 2 routes exist",
    not missing_class_2,
    "all present"
    if not missing_class_2
    else str(missing_class_2),
)

record(
    "central exposure candidates are GET-only",
    not non_get_central,
    "all GET-only"
    if not non_get_central
    else str(non_get_central),
)

record(
    "Reports Workspace still contains no POST form",
    'method="post"' not in template_text.lower()
    and "method='post'" not in template_text.lower(),
    "none",
)

record(
    "Reports Workspace classification boundary inherited",
    "ADR-9B placeholder" in template_text
    or POST_V2_15B_MARKER in template_text,
    (
        "POST-V2-15B architecture retained"
        if POST_V2_15B_MARKER in template_text
        else "ADR-9B placeholder retained"
    ),
)

if POST_V2_15B_MARKER in template_text:
    literal_links = sorted(
        {
            href
            for href in re.findall(
                r'href\s*=\s*["\']([^"\']+)["\']',
                template_text,
                flags=re.IGNORECASE,
            )
            if "{{" not in href
            and "}}" not in href
            and "{%" not in href
            and "%}" not in href
        }
    )

    central_class_routes = CLASS_1_CENTRAL_REPORTS | CLASS_2_CENTRAL_REGISTRIES
    central_exposure_links = [
        link for link in literal_links
        if link in central_class_routes
    ]
    protected_central_links = [
        link for link in central_exposure_links
        if link in EXPLICITLY_EXCLUDED
    ]
    parameterized_central_links = [
        link for link in central_exposure_links
        if "<" in link or ">" in link
    ]
    write_capable_central_links = [
        link for link in central_exposure_links
        if route_map.get(link)
        and set(route_map[link]["methods"]) != {"GET"}
    ]
    api_links = [
        link for link in literal_links
        if link.startswith("/api/")
    ]
    mutation_links = [
        link for link in literal_links
        if any(token in link.lower() for token in MUTATION_TOKENS)
    ]

    record(
        "15B rendered Reports Workspace contains no API links",
        not api_links,
        "none" if not api_links else str(api_links),
    )

    record(
        "15B rendered Reports Workspace contains no parameterized central links",
        not parameterized_central_links,
        "none" if not parameterized_central_links else str(parameterized_central_links),
    )

    record(
        "15B rendered Reports Workspace central links remain GET-only",
        not write_capable_central_links,
        "all GET-only" if not write_capable_central_links else str(write_capable_central_links),
    )

    record(
        "15B rendered Reports Workspace keeps protected routes out of central classes",
        not protected_central_links,
        "none" if not protected_central_links else str(protected_central_links),
    )

    record(
        "15B rendered Reports Workspace contains no mutation-capable links",
        not mutation_links,
        "none" if not mutation_links else str(mutation_links),
    )

api_central_exposure = [
    item["route"]
    for class_name in (
        "CLASS 1 — CENTRAL OPERATOR REPORT",
        "CLASS 2 — CENTRAL REGISTRY / OVERSIGHT",
    )
    for item in classified[class_name]
    if item["route"].startswith("/api/")
]

record(
    "API routes excluded from central exposure",
    not api_central_exposure,
    "none"
    if not api_central_exposure
    else str(api_central_exposure),
)

parameterized_central = [
    item["route"]
    for class_name in (
        "CLASS 1 — CENTRAL OPERATOR REPORT",
        "CLASS 2 — CENTRAL REGISTRY / OVERSIGHT",
    )
    for item in classified[class_name]
    if "<" in item["route"]
]

record(
    "central exposure candidates are not parameterized",
    not parameterized_central,
    "none"
    if not parameterized_central
    else str(parameterized_central),
)

write_capable_central = [
    item["route"]
    for class_name in (
        "CLASS 1 — CENTRAL OPERATOR REPORT",
        "CLASS 2 — CENTRAL REGISTRY / OVERSIGHT",
    )
    for item in classified[class_name]
    if set(item["methods"]) != {"GET"}
]

record(
    "write-capable routes excluded from central exposure",
    not write_capable_central,
    "none"
    if not write_capable_central
    else str(write_capable_central),
)

protected_routes_central = sorted(
    (
        CLASS_1_CENTRAL_REPORTS
        | CLASS_2_CENTRAL_REGISTRIES
    )
    & EXPLICITLY_EXCLUDED
)

record(
    "explicitly protected routes absent from central classes",
    not protected_routes_central,
    "none"
    if not protected_routes_central
    else str(protected_routes_central),
)

runtime_database_changed = any(
    "trustee_app.db" in line.replace("\\", "/")
    for line in (git("status", "--short") or "").splitlines()
)

record(
    "runtime database not modified",
    not runtime_database_changed,
    "none",
)

allowed_status_paths = {
    "app.py",
    "services/services_governance.py",
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "templates/ios_workspaces/reports.html",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_workspace_read_only_status_sources_15c.py",
    "scripts/audit_reports_workspace_minimal_read_only_context_wiring_15c1.py",
    "scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py",
    "scripts/audit_reports_workspace_consolidation_certification_15d.py",
}

unexpected_status = []

for line in (git("status", "--short") or "").splitlines():
    normalized = line.replace("\\", "/")

    if not any(
        path in normalized
        for path in allowed_status_paths
    ):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2-15 and 15A audits",
    not unexpected_status,
    "audit files only"
    if not unexpected_status
    else "\n".join(unexpected_status),
)

print()
print("LOCKED CENTRAL EXPOSURE CANDIDATES")
print("-" * 92)

for class_name in (
    "CLASS 1 — CENTRAL OPERATOR REPORT",
    "CLASS 2 — CENTRAL REGISTRY / OVERSIGHT",
):
    print()
    print(class_name)

    for item in classified[class_name]:
        print(
            f"  {item['route']} | "
            f"methods={item['methods']} | "
            f"{item['function']}"
        )

print()
print("CONTEXTUAL AND CONTROLLED ROUTES")
print("-" * 92)

for class_name in (
    "CLASS 3 — CONTEXTUAL RECORD REPORT",
    "CLASS 4 — CONTROLLED EXPORT / ARTIFACT",
):
    print()
    print(class_name)

    for item in classified[class_name]:
        print(
            f"  {item['route']} | "
            f"methods={item['methods']} | "
            f"{item['function']}"
        )

print()
print("EXCLUDED AND UNRESOLVED ROUTES")
print("-" * 92)

for class_name in (
    "CLASS 5 — EXCLUDED / PROTECTED",
    "CLASS 5 — EXCLUDED / UNRESOLVED",
):
    print()
    print(class_name)

    for item in classified[class_name]:
        print(
            f"  {item['route']} | "
            f"methods={item['methods']} | "
            f"{item['function']}"
        )

print()
print("EXPOSURE BOUNDARY")
print("-" * 92)
print("Class 1: may be directly linked from the Reports Workspace.")
print("Class 2: may be linked as registries or oversight dashboards.")
print("Class 3: remain attached to originating records; describe only.")
print("Class 4: remain controlled/contextual; do not expose as generic actions.")
print("Class 5: do not expose from the Reports Workspace.")
print()
print("The Reports Workspace must remain read-only.")
print("No route generation, mutation, approval, execution, or recovery controls.")
print("No APIs, diagnostics, tests, repairs, builders, or implementation status pages.")
print("No parameterized link may be rendered without an originating record ID.")

print()
print("SUMMARY")
print("-" * 92)
print(f"routes_total: {len(routes)}")
print(f"report_adjacent_routes: {len(report_routes)}")

for class_name, items in classified.items():
    print(
        f"{class_name.lower().replace(' ', '_').replace('—', '').replace('/', '_')}: "
        f"{len(items)}"
    )

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
