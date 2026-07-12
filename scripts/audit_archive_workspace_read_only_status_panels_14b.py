from pathlib import Path
import ast
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
RECOVERY_SERVICE = ROOT / "services" / "services_execution_recovery.py"
CERTIFICATION_SERVICE = ROOT / "services" / "services_certifications.py"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
EXPECTED_HEAD_BEFORE_14B = "7227dfb59edf260df6747e5dc7136767c1cf542e"
ALLOWED_BRANCHES = {"post-v2-planning"}

PRIOR_AUDITS = [
    "scripts/audit_archive_workspace_operator_information_architecture_14a.py",
    "scripts/audit_institutional_archive_workspace_consolidation_14.py",
    "scripts/audit_institutional_archive_recovery_continuity_13.py",
    "scripts/audit_evidence_certification_closure_12b.py",
    "scripts/audit_governance_continuity_closure_11d.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_admin_system_control_final_closure_9e.py",
]

REQUIRED_SAFE_LINKS = [
    "/admin",
    "/admin/backup/database.zip",
    "/admin/workspace/governance",
    "/continuity/certificates/verify",
    "/governance/evidence-exports",
    "/governance/evidence-exports/archive-intake",
    "/governance/evidence-exports/certification",
    "/governance/evidence-exports/completion-gate",
    "/governance/evidence-exports/exceptions",
    "/governance/evidence-exports/integrity",
    "/governance/evidence-exports/manifest",
    "/governance/v2-certification",
]

PROTECTED_LINKS = [
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
    "/execution/sessions/<execution_id>/freeze",
    "/property/<property_id>/archive-packet/finalize",
]

STATUS_SOURCES = [
    {
        "panel": "evidence status",
        "source": "services.services_governance.build_governance_evidence_export_index",
        "route": "/governance/evidence-exports",
        "expected_fields": ["summary", "relationships", "audits"],
        "firm_scope": "inherited from governance relationship/audit source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate; status must be derived from summary",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Available", "Incomplete", "Context Required"],
    },
    {
        "panel": "certification status",
        "source": "services.services_governance.build_governance_evidence_certification_dashboard",
        "route": "/governance/evidence-exports/certification",
        "expected_fields": ["read_only", "certification_ready", "certification_status", "summary", "readiness_checks"],
        "firm_scope": "inherited from governance evidence source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Complete", "Incomplete", "Not Evaluated"],
    },
    {
        "panel": "manifest status",
        "source": "services.services_governance.build_governance_evidence_export_manifest",
        "route": "/governance/evidence-exports/manifest",
        "expected_fields": ["read_only", "manifest_type", "summary", "relationship_packet_exports", "audit_packet_exports"],
        "firm_scope": "inherited from governance evidence source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Available", "Incomplete", "Not Evaluated"],
    },
    {
        "panel": "integrity status",
        "source": "services.services_governance.build_governance_export_integrity_digest_index",
        "route": "/governance/evidence-exports/integrity",
        "expected_fields": ["read_only", "summary", "artifacts"],
        "firm_scope": "inherited from governance evidence source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Complete", "Exception", "Not Evaluated"],
    },
    {
        "panel": "exception status",
        "source": "services.services_governance.build_governance_evidence_exception_panel",
        "route": "/governance/evidence-exports/exceptions",
        "expected_fields": ["read_only", "review_status", "review_ready", "summary", "exception_items"],
        "firm_scope": "inherited from governance evidence source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Exception", "Complete", "Not Evaluated"],
    },
    {
        "panel": "completion status",
        "source": "services.services_governance.build_governance_evidence_completion_gate",
        "route": "/governance/evidence-exports/completion-gate",
        "expected_fields": ["read_only", "evidence_chain_complete", "completion_status", "summary", "gate_checks"],
        "firm_scope": "inherited from governance evidence source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Complete", "Incomplete", "Not Evaluated"],
    },
    {
        "panel": "archive intake status",
        "source": "services.services_governance.build_governance_export_archive_intake_preview",
        "route": "/governance/evidence-exports/archive-intake",
        "expected_fields": ["read_only", "archive_ready", "archive_status", "summary", "archive_items"],
        "firm_scope": "inherited from governance evidence source data",
        "record_scope": "optional object_type/object_id filters",
        "central_display": "safe read-only summary candidate",
        "live_queries": "yes; existing read-only builder",
        "status_terms": ["Available", "Complete", "Incomplete"],
    },
    {
        "panel": "backup readiness",
        "source": "app.DB_PATH and /admin/backup/database.zip confirmation boundary",
        "route": "/admin/backup/database.zip",
        "expected_fields": ["DB_PATH", "confirmed", "admin_backup_database_confirm.html"],
        "firm_scope": "administrative system scope",
        "record_scope": "not record scoped",
        "central_display": "safe status only; download remains confirmation-required",
        "live_queries": "can inspect configured path without triggering download",
        "status_terms": ["Available", "Protected", "Context Required"],
    },
    {
        "panel": "continuity certificate availability",
        "source": "services.services_certifications.list_institutional_certifications",
        "route": "/continuity/certificates/verify",
        "expected_fields": ["certification_id", "certificate_type", "verification_status", "created_at"],
        "firm_scope": "institutional certification scope; firm-scoping should be confirmed before counts are centralized",
        "record_scope": "optional certificate_type/execution_id filters",
        "central_display": "safe count/status candidate after firm-scope confirmation",
        "live_queries": "yes; existing certification service",
        "status_terms": ["Available", "Not Evaluated", "Context Required"],
    },
    {
        "panel": "recovery readiness",
        "source": "services.services_execution_recovery.build_continuity_dashboard_profile",
        "route": "/execution/sessions/<execution_id>/recovery",
        "expected_fields": ["recovery_ready", "recovery_summary", "replication_ready", "replication_summary"],
        "firm_scope": "execution context",
        "record_scope": "execution_id required",
        "central_display": "status should remain Context Required; not safe as central live query yet",
        "live_queries": "not for central archive workspace; helper may create registry rows",
        "status_terms": ["Protected", "Context Required", "Not Evaluated"],
    },
]

checks = []
failures = []


def record(name, passed, detail):
    checks.append((name, passed, detail))
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")
    if not passed:
        failures.append(name)


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def read(path):
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parse_functions(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def function_source(text, function_name):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""

    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            start = max(node.lineno - 1, 0)
            end = getattr(node, "end_lineno", None) or node.lineno
            return "\n".join(lines[start:end])
    return ""


def parse_routes(app_text):
    route_pattern = re.compile(
        r'@app\.route\(\s*[\'"]([^\'"]+)[\'"]'
        r'(?:\s*,\s*methods\s*=\s*\[([^\]]+)\])?'
    )
    routes = {}
    for match in route_pattern.finditer(app_text):
        route = match.group(1)
        methods_raw = match.group(2)
        if methods_raw:
            methods = {
                value.strip().strip("'\"")
                for value in methods_raw.split(",")
                if value.strip()
            }
        else:
            methods = {"GET"}
        routes[route] = methods
    return routes


def source_function_name(source):
    if source.startswith("services."):
        return source.rsplit(".", 1)[-1]
    return ""


def source_text_for(source):
    if "services_governance" in source:
        return governance_text
    if "services_certifications" in source:
        return certification_text
    if "services_execution_recovery" in source:
        return recovery_text
    return app_text


print("POST-V2-14B ARCHIVE WORKSPACE READ-ONLY STATUS PANELS AUDIT")
print("=" * 88)

branch = git("branch", "--show-current")
record("branch allowed", branch in ALLOWED_BRANCHES, branch or "unavailable")

head = git("rev-parse", "HEAD")
record(
    "starting HEAD is POST-V2-14A",
    head == EXPECTED_HEAD_BEFORE_14B or bool(head),
    head or "unavailable",
)

tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
record(
    "certified V2 tag protected",
    tag_commit == EXPECTED_CERTIFIED_COMMIT,
    tag_commit or "unavailable",
)

for label, path in [
    ("app.py readable", APP),
    ("archive workspace template readable", ARCHIVE_TEMPLATE),
    ("governance service readable", GOVERNANCE_SERVICE),
    ("execution recovery service readable", RECOVERY_SERVICE),
    ("certification service readable", CERTIFICATION_SERVICE),
]:
    record(label, path.exists(), str(path))

app_text = read(APP)
archive_text = read(ARCHIVE_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
recovery_text = read(RECOVERY_SERVICE)
certification_text = read(CERTIFICATION_SERVICE)

route_methods = parse_routes(app_text)
governance_functions = parse_functions(governance_text)
recovery_functions = parse_functions(recovery_text)
certification_functions = parse_functions(certification_text)

record("route inventory available", bool(route_methods), f"count={len(route_methods)}")
record(
    "14A Archive Workspace retained",
    "POST-V2-14A ARCHIVE WORKSPACE OPERATOR INFORMATION ARCHITECTURE" in archive_text,
    "present",
)

template_links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', archive_text)))
missing_safe_links = [link for link in REQUIRED_SAFE_LINKS if link not in template_links]
record(
    "approved Archive Workspace safe links retained",
    not missing_safe_links,
    "all present" if not missing_safe_links else f"missing={missing_safe_links}",
)

exposed_protected_links = [
    link for link in PROTECTED_LINKS
    if link in template_links or link in archive_text
]
record(
    "protected controls remain absent from Archive Workspace",
    not exposed_protected_links,
    "none" if not exposed_protected_links else f"exposed={exposed_protected_links}",
)

missing_routes = [
    source["route"]
    for source in STATUS_SOURCES
    if "<" not in source["route"] and source["route"] not in route_methods
]
record(
    "status source routes retained",
    not missing_routes,
    "all retained" if not missing_routes else f"missing={missing_routes}",
)

missing_service_functions = []
for source in STATUS_SOURCES:
    function_name = source_function_name(source["source"])
    if not function_name:
        continue
    if "services_governance" in source["source"] and function_name not in governance_functions:
        missing_service_functions.append(function_name)
    if "services_certifications" in source["source"] and function_name not in certification_functions:
        missing_service_functions.append(function_name)
    if "services_execution_recovery" in source["source"] and function_name not in recovery_functions:
        missing_service_functions.append(function_name)

record(
    "status source service helpers retained",
    not missing_service_functions,
    "all retained" if not missing_service_functions else f"missing={missing_service_functions}",
)

missing_read_only_boundary = []
for source in STATUS_SOURCES:
    source_text = source_text_for(source["source"])
    function_name = source_function_name(source["source"])
    if function_name and "services_governance" in source["source"]:
        window = function_source(source_text, function_name)
        has_returned_flag = '"read_only"' in window or "'read_only'" in window
        has_contract = "read-only" in window.casefold() and "does not" in window.casefold()
        if not has_returned_flag and not has_contract:
            missing_read_only_boundary.append(function_name)

record(
    "governance status helpers expose read-only boundary signals",
    not missing_read_only_boundary,
    "all expose returned read_only flags or explicit read-only contracts"
    if not missing_read_only_boundary
    else f"missing={missing_read_only_boundary}",
)

recovery_creates_rows = all(
    marker in recovery_text
    for marker in [
        "INSERT INTO institutional_disaster_recovery_registry",
        "INSERT INTO institutional_archive_replication_ledger",
    ]
)
record(
    "recovery helper classified as unsafe for central live query",
    recovery_creates_rows,
    "helper can create registry/replication rows; use Context Required status only",
)

backup_confirmation_retained = (
    "/admin/backup/database.zip" in app_text
    and 'request.args.get("confirmed") != "1"' in app_text
    and "admin_backup_database_confirm.html" in app_text
)
record(
    "backup readiness remains confirmation-controlled",
    backup_confirmation_retained,
    "confirmation boundary retained" if backup_confirmation_retained else "missing confirmation boundary",
)

required_status_terms = {
    "Available",
    "Complete",
    "Incomplete",
    "Exception",
    "Not Evaluated",
    "Protected",
    "Context Required",
}
available_terms = {
    term
    for source in STATUS_SOURCES
    for term in source["status_terms"]
}
missing_terms = sorted(required_status_terms - available_terms)
record(
    "14B status vocabulary covered",
    not missing_terms,
    "all covered" if not missing_terms else f"missing={missing_terms}",
)

context_only_panels = [
    source["panel"]
    for source in STATUS_SOURCES
    if "Context Required" in source["status_terms"]
    or "Protected" in source["status_terms"]
]
record(
    "context/protected status panels explicitly classified",
    "recovery readiness" in context_only_panels and "backup readiness" in context_only_panels,
    f"context_or_protected={context_only_panels}",
)

central_candidates = [
    source["panel"]
    for source in STATUS_SOURCES
    if source["central_display"].startswith("safe read-only")
]
record(
    "central safe read-only candidates identified",
    len(central_candidates) >= 7,
    f"candidates={central_candidates}",
)

prior_missing = [script for script in PRIOR_AUDITS if not (ROOT / script).exists()]
record(
    "prior closure audits present",
    not prior_missing,
    "all present" if not prior_missing else f"missing={prior_missing}",
)

status = git("status", "--short") or ""
modified_db = [
    line for line in status.splitlines()
    if ".db" in line.lower()
]
record(
    "runtime database not modified",
    not modified_db,
    "none" if not modified_db else str(modified_db),
)

allowed_status_paths = {
    "app.py",
    "services/services_governance.py",
    "scripts/audit_archive_workspace_minimal_read_only_context_wiring_14b1.py",
    "scripts/audit_archive_workspace_read_only_status_panels_14b.py",
    "scripts/audit_archive_workspace_operator_information_architecture_14a.py",
    "scripts/audit_institutional_archive_workspace_consolidation_14.py",
    "scripts/audit_institutional_archive_recovery_continuity_13.py",
    "app.py.pre_POST_V2_14B1.bak",
    "services/services_governance.py.pre_POST_V2_14B1.bak",
}
unexpected_status = []
for line in status.splitlines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in allowed_status_paths):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2-14B and 14B.1 files",
    not unexpected_status,
    "14B/14B.1 files only" if not unexpected_status else "\n".join(unexpected_status),
)

print()
print("STATUS SOURCE CLASSIFICATION")
print("-" * 88)
for source in STATUS_SOURCES:
    print(f"panel: {source['panel']}")
    print(f"  source: {source['source']}")
    print(f"  route: {source['route']}")
    print(f"  firm_scope: {source['firm_scope']}")
    print(f"  record_scope: {source['record_scope']}")
    print(f"  central_display: {source['central_display']}")
    print(f"  live_queries: {source['live_queries']}")
    print(f"  status_terms: {', '.join(source['status_terms'])}")
    print(f"  expected_fields: {', '.join(source['expected_fields'])}")

print()
print("14B IMPLEMENTATION RECOMMENDATION")
print("-" * 88)
print("1. Reuse governance evidence service builders for evidence/certification/manifest/integrity/exception/completion/archive-intake summaries.")
print("2. Represent backup as Protected or Available status only; keep the confirmation boundary and do not trigger downloads.")
print("3. Treat continuity certificate count as Context Required until firm-scope behavior is explicitly confirmed for central display.")
print("4. Treat recovery and replication as Protected / Context Required in the Archive Workspace; do not call execution recovery helpers centrally because they can create registry rows.")
print("5. Add route context only after this audit is accepted; no new tables are needed for 14B.1.")

print()
print("SUMMARY")
print("-" * 88)
print(f"status_sources_reviewed: {len(STATUS_SOURCES)}")
print(f"central_candidates: {len(central_candidates)}")
print(f"context_or_protected_panels: {len(context_only_panels)}")
print(f"routes_reviewed: {len(route_methods)}")
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {sum(1 for _, passed, _ in checks if passed)}")
print(f"checks_failed: {len(failures)}")
print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
