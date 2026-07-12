from pathlib import Path
import ast
import json
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
CERTIFICATIONS_SERVICE = ROOT / "services" / "services_certifications.py"
CONTINUITY_SERVICE = ROOT / "services" / "services_execution_recovery.py"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTOR = "5550156"
ALLOWED_BRANCHES = {"post-v2-planning"}

STATUS_TERMS = {
    "Available",
    "Complete",
    "Incomplete",
    "Exception",
    "Protected",
    "Context Required",
    "Not Evaluated",
    "Unavailable",
}

MUTATION_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bREPLACE\b",
    r"\.commit\s*\(",
    r"\.executemany\s*\(",
    r"\bcreate_[A-Za-z0-9_]*\s*\(",
    r"\bupdate_[A-Za-z0-9_]*\s*\(",
    r"\bdelete_[A-Za-z0-9_]*\s*\(",
    r"\bseed_[A-Za-z0-9_]*\s*\(",
    r"\brepair_[A-Za-z0-9_]*\s*\(",
    r"\bbackfill_[A-Za-z0-9_]*\s*\(",
    r"\bgenerate_[A-Za-z0-9_]*\s*\(",
    r"\bfinalize[A-Za-z0-9_]*\s*\(",
    r"\bapprove[A-Za-z0-9_]*\s*\(",
    r"\bcertify[A-Za-z0-9_]*\s*\(",
    r"\bexecute[A-Za-z0-9_]*\s*\(",
    r"\bsend_file\s*\(",
    r"\bzipfile\.",
]

ARCHIVE_DUPLICATE_BUILDERS = {
    "build_governance_evidence_export_index",
    "build_governance_evidence_certification_dashboard",
    "build_governance_evidence_export_manifest",
    "build_governance_export_integrity_digest_index",
    "build_governance_evidence_exception_panel",
    "build_governance_evidence_completion_gate",
    "build_governance_export_archive_intake_preview",
}

REQUIRED_AUDITS = [
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
]

REVIEWED_ROUTES = [
    "/financial_summary",
    "/portfolio",
    "/reports/portfolio.pdf",
    "/audit",
    "/reports/audit.pdf",
    "/admin/audit-log",
    "/visualization/analytics",
    "/exports",
    "/exports/zip",
    "/exports/handoff/<filename>",
    "/exports/roadmap/<filename>",
    "/exports/package/<filename>",
    "/exports/k1/<trust_id>.csv",
    "/exports/1041/<trust_id>.txt",
    "/certificates",
    "/admin/certificates/unified",
    "/continuity/certificates/verify",
    "/certificate-studio",
    "/certificates/backfill",
    "/intake/dashboard",
    "/intake/exports",
    "/intake/modules",
    "/intake/draft-readiness",
    "/intake/review-gates",
    "/intake/final-draft-gate",
    "/intake/final-draft-approvals",
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
]

STATUS_PROPOSALS = [
    {
        "family": "Financial and Portfolio Reporting",
        "panel": "Financial Summary Availability",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/financial_summary",
        "status_terms": ["Available", "Unavailable", "Not Evaluated"],
        "expected_fields": ["route", "methods", "source_function", "read_only", "mutation_risk"],
        "recommendation": "Link only until a non-seeding read-only financial availability helper exists.",
        "scope": "institution or firm scoped by route/session context",
    },
    {
        "family": "Financial and Portfolio Reporting",
        "panel": "Portfolio Reporting Availability",
        "source_class": "A - Safe Central Read-Only Builder",
        "route": "/portfolio",
        "status_terms": ["Available", "Incomplete", "Not Evaluated"],
        "expected_fields": ["route", "methods", "source_function", "record_count_shape"],
        "recommendation": "Central Reports summary allowed if limited to availability and coverage shape.",
        "scope": "institution or firm scoped by underlying portfolio query context",
    },
    {
        "family": "Financial and Portfolio Reporting",
        "panel": "Portfolio PDF Artifact",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/reports/portfolio.pdf",
        "status_terms": ["Available", "Protected", "Context Required"],
        "expected_fields": ["route", "methods", "artifact_link"],
        "recommendation": "Link only; PDF generation/download route should not be invoked for status.",
        "scope": "artifact surface",
    },
    {
        "family": "Audit Reporting",
        "panel": "Audit Activity Available",
        "source_class": "A - Safe Central Read-Only Builder",
        "route": "/audit",
        "status_terms": ["Available", "Exception", "Not Evaluated"],
        "expected_fields": ["route", "methods", "audit_count_shape", "exception_shape"],
        "recommendation": "Central Reports summary allowed if counts are scoped and read-only.",
        "scope": "audit ledger scope",
    },
    {
        "family": "Audit Reporting",
        "panel": "Administrative Audit Log",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/admin/audit-log",
        "status_terms": ["Available", "Protected"],
        "expected_fields": ["route", "methods", "admin_scope"],
        "recommendation": "Link only or Admin-owned; avoid duplicating Admin audit status in Reports.",
        "scope": "admin/operator scope",
    },
    {
        "family": "Audit Reporting",
        "panel": "Audit PDF Artifact",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/reports/audit.pdf",
        "status_terms": ["Available", "Protected", "Context Required"],
        "expected_fields": ["route", "methods", "artifact_link"],
        "recommendation": "Link only; do not invoke PDF route for status.",
        "scope": "artifact surface",
    },
    {
        "family": "Institutional Analytics",
        "panel": "Analytics Available",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/visualization/analytics",
        "status_terms": ["Available", "Not Evaluated"],
        "expected_fields": ["route", "methods", "analytics_surface"],
        "recommendation": "Link only until analytics scope and completeness are explicitly certified.",
        "scope": "institutional analytics scope",
    },
    {
        "family": "Export Oversight",
        "panel": "Export Registry Available",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/exports",
        "status_terms": ["Available", "Protected", "Context Required"],
        "expected_fields": ["route", "methods", "registry_available"],
        "recommendation": "Link only; central counts risk exposing paths or mixing generated artifacts.",
        "scope": "export registry scope",
    },
    {
        "family": "Export Oversight",
        "panel": "Controlled Export Artifacts",
        "source_class": "D - Protected or Mutation-Capable",
        "route": "/exports/zip",
        "status_terms": ["Protected", "Context Required"],
        "expected_fields": ["route", "methods", "download_or_generation_boundary"],
        "recommendation": "Exclude from central status invocation; do not generate ZIPs for status.",
        "scope": "artifact generation/download",
    },
    {
        "family": "Certificate Oversight",
        "panel": "Certificate Registry Available",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/certificates",
        "status_terms": ["Available", "Context Required", "Not Evaluated"],
        "expected_fields": ["route", "methods", "registry_available"],
        "recommendation": "Link only until certificate count scoping is explicitly certified.",
        "scope": "certificate registry scope",
    },
    {
        "family": "Certificate Oversight",
        "panel": "Certificate Verification Available",
        "source_class": "C - Context Required",
        "route": "/continuity/certificates/verify",
        "status_terms": ["Context Required", "Protected"],
        "expected_fields": ["route", "methods", "certification_id_required"],
        "recommendation": "Keep verification contextual; do not centralize counts yet.",
        "scope": "certificate verification context",
    },
    {
        "family": "Certificate Oversight",
        "panel": "Certificate Studio and Backfill",
        "source_class": "E - Administrative, Diagnostic, API, Test, or Implementation Surface",
        "route": "/certificate-studio",
        "status_terms": ["Protected", "Not Evaluated"],
        "expected_fields": ["route", "methods", "implementation_surface"],
        "recommendation": "Exclude builder/studio/backfill actions from Reports status.",
        "scope": "implementation surface",
    },
    {
        "family": "Intake Oversight",
        "panel": "Intake Oversight Available",
        "source_class": "A - Safe Central Read-Only Builder",
        "route": "/intake/dashboard",
        "status_terms": ["Available", "Incomplete", "Not Evaluated"],
        "expected_fields": ["route", "methods", "dashboard_summary_shape"],
        "recommendation": "Central Reports summary allowed if ledger helpers remain read-only.",
        "scope": "intake ledger scope",
    },
    {
        "family": "Intake Oversight",
        "panel": "Draft and Review Gate Status",
        "source_class": "A - Safe Central Read-Only Builder",
        "route": "/intake/draft-readiness",
        "status_terms": ["Available", "Complete", "Incomplete", "Exception", "Not Evaluated"],
        "expected_fields": ["draft_readiness", "review_gates", "final_draft_gate", "approval_status"],
        "recommendation": "Later aggregation helper justified; use existing read-only ledger surfaces only.",
        "scope": "intake ledger scope",
    },
    {
        "family": "Governance and Evidence Oversight",
        "panel": "Governance Evidence Chain",
        "source_class": "F - Duplicate of Certified Archive Status",
        "route": "/governance/evidence-exports",
        "status_terms": ["Available", "Complete", "Incomplete", "Exception", "Not Evaluated"],
        "expected_fields": ["archive_status_reference", "certified_builder_name", "route"],
        "recommendation": "Reuse Archive status context or link to Archive; do not create divergent status logic.",
        "scope": "certified archive/evidence status scope",
    },
    {
        "family": "Governance and Evidence Oversight",
        "panel": "Governance Dashboard",
        "source_class": "B - Safe Link, Unsafe or Unnecessary Central Query",
        "route": "/governance/dashboard",
        "status_terms": ["Available", "Not Evaluated"],
        "expected_fields": ["route", "methods", "governance_registry_surface"],
        "recommendation": "Link only unless a governance-owned summary helper is later certified.",
        "scope": "governance workspace scope",
    },
    {
        "family": "Governance and Evidence Oversight",
        "panel": "Relationship Audit Ledger",
        "source_class": "A - Safe Central Read-Only Builder",
        "route": "/governance/relationship-audits",
        "status_terms": ["Available", "Exception", "Not Evaluated"],
        "expected_fields": ["route", "methods", "audit_count_shape", "outcome_shape"],
        "recommendation": "Central Reports summary allowed if counts remain read-only and scoped.",
        "scope": "governance audit ledger scope",
    },
    {
        "family": "Governance and Evidence Oversight",
        "panel": "V2 Certification Record",
        "source_class": "F - Duplicate of Certified Archive Status",
        "route": "/governance/v2-certification",
        "status_terms": ["Available", "Complete", "Not Evaluated"],
        "expected_fields": ["certified_tag", "dashboard_type", "route"],
        "recommendation": "Link or reuse certified Archive/evidence status; avoid a second certification computation.",
        "scope": "certification dashboard scope",
    },
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
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")
    if not passed:
        failures.append(name)


def read(path):
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def route_methods_from_app(text):
    tree = ast.parse(text)
    lines = text.splitlines()
    routes = {}

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            if getattr(decorator.func, "attr", None) != "route":
                continue

            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue

            route = str(decorator.args[0].value)
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

            source = "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)])
            called_names = sorted(
                {
                    call.func.id
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                }
                | {
                    call.func.attr
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                }
            )

            routes[route] = {
                "route": route,
                "methods": methods,
                "function": node.name,
                "line": node.lineno,
                "source": source,
                "called_names": called_names,
            }

    return routes


def function_source(module_text, function_name):
    try:
        tree = ast.parse(module_text)
    except SyntaxError:
        return ""

    lines = module_text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)])

    return ""


def mutation_hits(text):
    hits = []
    for pattern in MUTATION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def source_file_for(route, function_name):
    if function_name in ARCHIVE_DUPLICATE_BUILDERS:
        return str(GOVERNANCE_SERVICE.relative_to(ROOT))
    if route.startswith("/governance/evidence-exports") or route == "/governance/v2-certification":
        return str(GOVERNANCE_SERVICE.relative_to(ROOT))
    if "certificate" in route or "certificat" in function_name:
        return str(CERTIFICATIONS_SERVICE.relative_to(ROOT))
    return "app.py"


def derive_source_function(route_info, proposal):
    if proposal["source_class"].startswith("F"):
        if proposal["route"] == "/governance/evidence-exports":
            return "build_archive_workspace_read_only_status / certified governance evidence builders"
        if proposal["route"] == "/governance/v2-certification":
            return "build_v2_certification_dashboard"

    if not route_info:
        return "missing"

    interesting = [
        name
        for name in route_info["called_names"]
        if name.startswith(("build_", "list_", "get_", "verify_"))
    ]
    return ", ".join(interesting[:8]) or route_info["function"]


def record_context_required(route):
    return bool(re.search(r"<[^>]+>", route))


def central_safe(source_class):
    return source_class.startswith("A") or source_class.startswith("F")


def read_only_label(route_info, source_class, hits):
    if source_class.startswith(("D", "E")):
        return "No"
    if hits and not source_class.startswith(("B", "C", "F")):
        return "Review"
    if route_info and set(route_info["methods"]) != {"GET"}:
        return "No"
    return "Yes"


print("POST-V2-15C REPORTS WORKSPACE READ-ONLY STATUS SOURCE AUDIT")
print("=" * 96)

branch = git("branch", "--show-current")
record("branch allowed", branch in ALLOWED_BRANCHES, branch or "unknown")

head = git("rev-parse", "HEAD")
ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", REQUIRED_ANCESTOR, "HEAD"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
record("required POST-V2-15B commit retained in ancestry", ancestor.returncode == 0, head or "missing")

certified_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
record(
    "certified V2 tag protected",
    certified_commit == EXPECTED_CERTIFIED_COMMIT,
    certified_commit or "missing",
)

record("app.py readable", APP.exists(), str(APP))
record("Reports Workspace template readable", REPORTS_TEMPLATE.exists(), str(REPORTS_TEMPLATE))
record("governance service readable", GOVERNANCE_SERVICE.exists(), str(GOVERNANCE_SERVICE))

app_text = read(APP)
reports_text = read(REPORTS_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
routes = route_methods_from_app(app_text) if app_text else {}

record("route inventory available", bool(routes), f"count={len(routes)}")

missing_routes = [route for route in REVIEWED_ROUTES if route not in routes]
record(
    "required reviewed routes retained",
    not missing_routes,
    "all present" if not missing_routes else str(missing_routes),
)

missing_audits = [script for script in REQUIRED_AUDITS if not (ROOT / script).exists()]
record(
    "POST-V2-15 audit chain retained",
    not missing_audits,
    "all present" if not missing_audits else str(missing_audits),
)

matrix = []
for proposal in STATUS_PROPOSALS:
    route = proposal["route"]
    route_info = routes.get(route)
    source_function = derive_source_function(route_info, proposal)
    source_file = source_file_for(route, source_function)
    source_text = route_info["source"] if route_info else ""

    if proposal["source_class"].startswith("F"):
        for builder in ARCHIVE_DUPLICATE_BUILDERS:
            source_text += "\n" + function_source(governance_text, builder)

    hits = mutation_hits(source_text)
    methods = route_info["methods"] if route_info else []
    source_class = proposal["source_class"]
    read_only = read_only_label(route_info, source_class, hits)
    duplicate_archive = "Yes" if source_class.startswith("F") else "No"
    mutation_risk = (
        "Protected/generated/excluded"
        if source_class.startswith(("D", "E"))
        else (
            "Static mutation indicators: " + ", ".join(hits[:5])
            if hits and not source_class.startswith("F")
            else "None identified by static inspection"
        )
    )
    central_query_safe = (
        "Yes" if source_class.startswith("A")
        else "Reuse certified Archive source" if source_class.startswith("F")
        else "No"
    )

    matrix.append(
        {
            "family": proposal["family"],
            "panel": proposal["panel"],
            "source_class": source_class,
            "source_function": source_function,
            "source_file": source_file,
            "route": route,
            "methods": ",".join(methods) if methods else "missing",
            "scope": proposal["scope"],
            "record_context_required": "Yes" if record_context_required(route) or source_class.startswith("C") else "No",
            "read_only": read_only,
            "mutation_risk": mutation_risk,
            "central_query_safe": central_query_safe,
            "duplicate_archive_status": duplicate_archive,
            "status_terms": ", ".join(proposal["status_terms"]),
            "expected_fields": ", ".join(proposal["expected_fields"]),
            "recommendation": proposal["recommendation"],
        }
    )

invalid_terms = sorted(
    {
        term
        for proposal in STATUS_PROPOSALS
        for term in proposal["status_terms"]
        if term not in STATUS_TERMS
    }
)
record(
    "status vocabulary limited to approved terms",
    not invalid_terms,
    "approved vocabulary only" if not invalid_terms else str(invalid_terms),
)

unsafe_safe_candidates = [
    row for row in matrix
    if row["source_class"].startswith("A")
    and row["read_only"] != "Yes"
]
record(
    "safe central candidates have no unresolved mutation risk",
    not unsafe_safe_candidates,
    "all safe candidates statically read-only"
    if not unsafe_safe_candidates
    else str([row["panel"] for row in unsafe_safe_candidates]),
)

protected_misclassified = [
    row for row in matrix
    if row["source_class"].startswith("A")
    and row["mutation_risk"] != "None identified by static inspection"
]
record(
    "protected sources not classified as central-safe",
    not protected_misclassified,
    "none" if not protected_misclassified else str([row["panel"] for row in protected_misclassified]),
)

runtime_database_changed = any(
    "trustee_app.db" in line.replace("\\", "/")
    or line.lower().endswith(".db")
    for line in (git("status", "--short") or "").splitlines()
)
record("runtime database not modified", not runtime_database_changed, "none")

allowed_status_paths = {
    "templates/ios_workspaces/reports.html",
    "app.py",
    "services/services_governance.py",
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_workspace_read_only_status_sources_15c.py",
    "scripts/audit_reports_workspace_minimal_read_only_context_wiring_15c1.py",
    "scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py",
    "scripts/audit_reports_workspace_consolidation_certification_15d.py",
}
unexpected_status = []
for line in (git("status", "--short") or "").splitlines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in allowed_status_paths):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2 Reports audit files",
    not unexpected_status,
    "Reports audit files only" if not unexpected_status else "\n".join(unexpected_status),
)

safe_central = [row for row in matrix if row["source_class"].startswith("A")]
link_only = [row for row in matrix if row["source_class"].startswith("B")]
context_required = [row for row in matrix if row["source_class"].startswith("C")]
protected_or_excluded = [row for row in matrix if row["source_class"].startswith(("D", "E"))]
archive_duplicate = [row for row in matrix if row["source_class"].startswith("F")]

print()
print("STRUCTURED SOURCE MATRIX")
print("-" * 96)
headers = [
    "family",
    "panel",
    "source_class",
    "source_function",
    "source_file",
    "route",
    "methods",
    "scope",
    "record_context_required",
    "read_only",
    "mutation_risk",
    "central_query_safe",
    "duplicate_archive_status",
    "status_terms",
    "expected_fields",
    "recommendation",
]
for row in matrix:
    print()
    for header in headers:
        print(f"{header}: {row[header]}")


def print_group(title, rows):
    print()
    print(title)
    print("-" * 96)
    if not rows:
        print("[NONE]")
        return
    for row in rows:
        print(f"{row['panel']} | {row['route']} | {row['source_class']} | {row['recommendation']}")


print_group("SAFE CENTRAL CANDIDATES", safe_central)
print_group("LINK-ONLY CANDIDATES", link_only)
print_group("CONTEXT-REQUIRED SOURCES", context_required)
print_group("PROTECTED OR EXCLUDED SOURCES", protected_or_excluded)
print_group("ARCHIVE-DUPLICATE SOURCES", archive_duplicate)

panel_contract = {
    "read_only": True,
    "context_type": "reports_workspace_status",
    "panels": {
        "financial": {
            "status": "Protected",
            "label": "Financial Summary Availability",
            "detail": "Link only until the route-local seeding path is separated from read-only status.",
            "route": "/financial_summary",
        },
        "portfolio": {
            "status": "Not Evaluated",
            "label": "Portfolio Reporting Availability",
            "detail": "Coverage shape may be summarized after read-only aggregation is wired.",
            "route": "/portfolio",
        },
        "audit": {
            "status": "Not Evaluated",
            "label": "Audit Activity Available",
            "detail": "Use scoped read-only audit counts only.",
            "route": "/audit",
        },
        "intake": {
            "status": "Not Evaluated",
            "label": "Intake Oversight Available",
            "detail": "Aggregate read-only ledger status across dashboard, exports, modules, gates, and approvals.",
            "route": "/intake/dashboard",
        },
        "governance_audits": {
            "status": "Not Evaluated",
            "label": "Relationship Audit Ledger",
            "detail": "Use governance-owned read-only audit ledger summary.",
            "route": "/governance/relationship-audits",
        },
        "evidence_archive": {
            "status": "Not Evaluated",
            "label": "Governance Evidence Chain",
            "detail": "Reuse certified Archive Workspace status context; do not duplicate evidence computation.",
            "route": "/governance/evidence-exports",
        },
        "exports": {
            "status": "Protected",
            "label": "Controlled Export Artifacts",
            "detail": "Navigation only; do not generate or download files for status.",
            "route": "/exports",
        },
        "certificates": {
            "status": "Context Required",
            "label": "Certificate Registry Available",
            "detail": "Counts require separate firm-scope certification before central display.",
            "route": "/certificates",
        },
    },
}

print()
print("RECOMMENDED REPORTS STATUS PANEL CONTRACT - PROPOSAL ONLY")
print("-" * 96)
print(json.dumps(panel_contract, indent=2))

print()
print("REVIEW ANSWERS")
print("-" * 96)
print("Safely centralizable now: portfolio availability, audit activity, intake oversight ledgers, governance relationship-audit ledger.")
print("Link-only: financial summary until a non-seeding helper exists, PDFs, analytics, exports registry, certificate registry, admin audit log, governance dashboard.")
print("Duplicate Archive status: governance evidence chain and V2 certification surfaces.")
print("Context required: continuity certificate verification and certificate counts until firm-scope certification exists.")
print("Protected/excluded: ZIP/download generation, certificate backfill, studio/builder surfaces, APIs, diagnostics, recovery, repair, approval, execution, and finalization actions.")
print("Later wiring: POST-V2-15C.1 is justified only as a new read-only aggregation helper that reuses existing safe builders and certified Archive status.")

print()
print("SUMMARY")
print("-" * 96)
print(f"routes_reviewed: {len(REVIEWED_ROUTES)}")
print(f"matrix_rows: {len(matrix)}")
print(f"safe_central_candidates: {len(safe_central)}")
print(f"link_only_candidates: {len(link_only)}")
print(f"context_required_sources: {len(context_required)}")
print(f"protected_or_excluded_sources: {len(protected_or_excluded)}")
print(f"archive_duplicate_sources: {len(archive_duplicate)}")
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {sum(1 for _, passed, _ in checks if passed)}")
print(f"checks_failed: {len(failures)}")
print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
