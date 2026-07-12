from pathlib import Path
import ast
import subprocess
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTOR = "22ca47f"
ALLOWED_BRANCHES = {"post-v2-planning"}

REQUIRED_PANEL_KEYS = {
    "portfolio",
    "audit",
    "intake",
    "draft_review",
    "governance_audits",
    "financial",
    "certificate_verification",
    "controlled_exports",
    "governance_evidence",
    "v2_certification",
}

APPROVED_SAFE_CALLS = {
    "_reports_portfolio_status",
    "_reports_audit_status",
    "_reports_intake_status",
    "_reports_draft_review_status",
    "_reports_governance_audits_status",
    "_reports_status_panel",
    "get_portfolio_summary",
    "get_audit_log",
    "get_current_firm_id",
    "get_connection",
    "list_governance_relationship_audits",
    "_reports_count",
    "_reports_table_exists",
    "int",
    "len",
    "sum",
    "max",
    "dict",
}

PROHIBITED_CALL_PREFIXES = (
    "seed_",
    "repair_",
    "backfill_",
    "generate_",
    "finalize_",
    "approve_",
    "certify_",
    "execute_",
    "insert",
    "update",
    "delete",
    "replace",
    "commit",
)

ALLOWED_STATUS_PATHS = {
    "templates/ios_workspaces/reports.html",
    "app.py",
    "services/services_governance.py",
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_workspace_read_only_status_sources_15c.py",
    "scripts/audit_reports_workspace_minimal_read_only_context_wiring_15c1.py",
    "scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py",
}


checks = []


def git(*args):
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


def read(path):
    return path.read_text(encoding="utf-8")


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def find_function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


branch = git("branch", "--show-current")
head = git("rev-parse", "HEAD")
tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", REQUIRED_ANCESTOR, "HEAD"],
    cwd=ROOT,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

record("correct branch", branch in ALLOWED_BRANCHES, branch)
record("POST-V2-15C retained in ancestry", ancestor.returncode == 0, head)
record("certified V2 tag unchanged", tag_commit == EXPECTED_CERTIFIED_COMMIT, tag_commit)

app_text = read(APP)
service_text = read(GOVERNANCE_SERVICE)
template_current = read(REPORTS_TEMPLATE)
template_changes = git("diff", "--name-only", "HEAD", "--", "templates/ios_workspaces/reports.html")
approved_15c2_rendering = (
    "Reports Oversight Status" in template_current
    and "reports-status-grid" in template_current
    and 'reports_status.get("context_type") == "reports_workspace_status"' in template_current
)

app_tree = ast.parse(app_text)
service_tree = ast.parse(service_text)
helper = find_function(service_tree, "build_reports_workspace_read_only_status")

record("aggregation helper exists", helper is not None, "build_reports_workspace_read_only_status")
record(
    "helper is explicitly read-only",
    helper is not None and '"read_only": True' in ast.get_source_segment(service_text, helper),
    "read_only true",
)
record(
    "required top-level contract exists",
    helper is not None
    and '"context_type": "reports_workspace_status"' in ast.get_source_segment(service_text, helper)
    and '"panels":' in ast.get_source_segment(service_text, helper),
    "contract present",
)

helper_source = ast.get_source_segment(service_text, helper) if helper else ""
panel_keys_present = {key for key in REQUIRED_PANEL_KEYS if f'"{key}"' in helper_source}
record("required ten panel keys exist", panel_keys_present == REQUIRED_PANEL_KEYS, sorted(REQUIRED_PANEL_KEYS - panel_keys_present))

call_names = [call_name(node.func) for node in ast.walk(ast.parse(helper_source or "pass")) if isinstance(node, ast.Call)]
unsafe_calls = [
    name
    for name in call_names
    if name and any(name.lower().startswith(prefix) for prefix in PROHIBITED_CALL_PREFIXES)
]
unknown_direct_calls = [
    name
    for name in call_names
    if name
    and not name.startswith("_reports_")
    and name not in APPROVED_SAFE_CALLS
]
record("only approved safe central sources are queried", not unknown_direct_calls, ", ".join(sorted(set(unknown_direct_calls))))
record("no mutation-capable helper is invoked", not unsafe_calls, ", ".join(sorted(set(unsafe_calls))))
record("no record-specific identifier is required", "intake_id" not in helper_source and "trust_id" not in helper_source and "certificate_id" not in helper_source, "no identifiers")

record(
    "financial summary remains link-only",
    '"financial"' in helper_source
    and '"Not Evaluated"' in helper_source
    and "Central status computation is not enabled" in helper_source
    and "get_trust_financial_summary" not in helper_source,
    "financial not computed",
)
record(
    "certificate verification remains Context Required",
    '"certificate_verification"' in helper_source
    and '"Context Required"' in helper_source
    and "backfill" not in helper_source.lower(),
    "certificate context required",
)
record(
    "controlled exports remain Protected",
    '"controlled_exports"' in helper_source and '"Protected"' in helper_source and "send_file" not in helper_source,
    "exports protected",
)
record(
    "governance evidence remains archive duplicate or link-only",
    '"governance_evidence"' in helper_source
    and '"/admin/workspace/archive"' in helper_source
    and "build_archive_workspace_read_only_status" not in helper_source,
    "archive link only",
)
record(
    "V2 certification is not independently recomputed",
    '"v2_certification"' in helper_source
    and "governed certification surface" in helper_source
    and "build_v2" not in helper_source.lower(),
    "certification not recomputed",
)

workspace_function = find_function(app_tree, "admin_ios_workspace")
workspace_source = ast.get_source_segment(app_text, workspace_function) if workspace_function else ""
record(
    "Reports route conditionally builds context only for reports",
    'if workspace_key == "reports"' in workspace_source
    and "build_reports_workspace_read_only_status()" in workspace_source,
    "conditional reports branch",
)
record(
    "reports_status is passed to the template context",
    "reports_status=reports_status" in workspace_source,
    "template context",
)
record(
    "non-Reports workspaces receive no live Reports context",
    "reports_status = None" in workspace_source
    and workspace_source.find("reports_status = None") < workspace_source.find('if workspace_key == "reports"'),
    "default none",
)
record(
    "Reports template unchanged from POST-V2-15B or limited to POST-V2-15C.2 rendering",
    not template_changes or approved_15c2_rendering,
    "unchanged" if not template_changes else "approved 15C.2 rendering",
)

migration_or_db_changes = [
    line
    for line in (git("status", "--short") or "").splitlines()
    if "migration" in line.lower()
    or line.lower().endswith(".db")
    or "trustee_app.db" in line.replace("\\", "/")
]
record("no migration or database change", not migration_or_db_changes, "\n".join(migration_or_db_changes) or "none")

unexpected_status = []
for line in (git("status", "--short") or "").splitlines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected_status.append(line)
record(
    "working tree limited to approved POST-V2-15C.1 files",
    not unexpected_status,
    "\n".join(unexpected_status) if unexpected_status else "approved files only",
)

print("POST-V2-15C.1 REPORTS WORKSPACE MINIMAL READ-ONLY CONTEXT WIRING AUDIT")
print("-" * 88)
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")

failed = [check for check in checks if not check[1]]
print()
print("SUMMARY")
print("-" * 88)
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")
print("RESULT: PASS" if not failed else "RESULT: FAIL")

if failed:
    raise SystemExit(1)
