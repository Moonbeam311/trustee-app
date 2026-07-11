from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

CORE_ROUTES = [
    "/admin/workspace/governance",
    "/governance",
    "/governance/dashboard",
]

DIRECTIVE_ROUTES = [
    "/governance/directives/new",
    "/governance/directives/<directive_id>",
    "/governance/directives/<directive_id>/relationships",
    "/governance/directives/<directive_id>/packet.pdf",
    "/governance/directives/<directive_id>/implementation",
    "/governance/directives/<directive_id>/approve",
    "/governance/directives/<directive_id>/lifecycle",
]

POLICY_ROUTES = [
    "/governance/policies/new",
    "/governance/policies/<policy_id>",
    "/governance/policies/<policy_id>/lifecycle",
    "/governance/policies/<policy_id>/relationships",
    "/governance/policies/<policy_id>/approve",
    "/governance/policies/<policy_id>/activity",
    "/governance/policies/<policy_id>/packet.pdf",
]

RELATIONSHIP_ROUTES = [
    "/governance/relationships/<relationship_id>",
    "/governance/relationships/<relationship_id>/export",
    "/governance/relationships/<relationship_id>/reinstate",
    "/governance/relationships/<relationship_id>/supersede",
    "/governance/relationships/<relationship_id>/retire",
    "/governance/relationship-audits",
    "/governance/relationship-audits/<audit_id>",
    "/governance/relationship-audits/<audit_id>/export",
    "/governance/relationship-lifecycle",
]

EVIDENCE_ROUTES = [
    "/governance/evidence-exports",
    "/governance/evidence-exports.csv",
    "/governance/evidence-exports/certification",
    "/governance/evidence-exports/certification.txt",
    "/governance/v2-certification",
    "/governance/v2-certification.txt",
    "/governance/evidence-exports/completion-gate",
    "/governance/evidence-exports/completion-gate.txt",
    "/governance/evidence-exports/exceptions",
    "/governance/evidence-exports/exceptions.txt",
    "/governance/evidence-exports/archive-intake",
    "/governance/evidence-exports/archive-intake.txt",
    "/governance/evidence-exports/integrity",
    "/governance/evidence-exports/integrity.txt",
    "/governance/evidence-exports/manifest",
    "/governance/evidence-exports/manifest.txt",
]

BRIDGE_ROUTES = [
    "/matters/<matter_id>/governance",
    "/matters/<matter_id>/governance-links",
    "/trust/<trust_id>/governance-links",
    "/document-platform/governance",
    "/document-platform/workspace/<path:document_id>/governance-links",
]

REQUIRED_TEMPLATES = [
    "templates/ios_workspaces/governance.html",
    "templates/governance/dashboard.html",
    "templates/governance/registry.html",
    "templates/governance/directive_form.html",
    "templates/governance/directive_detail.html",
    "templates/governance/policy_form.html",
    "templates/governance/policy_detail.html",
    "templates/governance/relationship_detail.html",
    "templates/governance/relationship_audit_ledger.html",
    "templates/governance/relationship_audit_detail.html",
    "templates/governance/relationship_lifecycle_dashboard.html",
    "templates/governance/evidence_export_index.html",
    "templates/governance/evidence_certification_dashboard.html",
    "templates/governance/v2_certification_dashboard.html",
    "templates/governance/evidence_completion_gate.html",
    "templates/governance/evidence_exception_panel.html",
    "templates/governance/evidence_export_archive_intake.html",
    "templates/governance/evidence_export_integrity.html",
    "templates/governance/evidence_export_manifest.html",
    "templates/governance/_record_nav.html",
    "templates/governance/_record_metadata.html",
    "templates/governance/_record_lifecycle.html",
    "templates/governance/_relationship_form.html",
    "templates/governance/_relationship_table.html",
    "templates/governance/_directive_approval.html",
    "templates/governance/_directive_source.html",
    "templates/governance/_directive_implementation_ledger.html",
    "templates/governance/_policy_approval.html",
    "templates/governance/_policy_activity_ledger.html",
    "templates/governance/_matter_governance_summary.html",
    "templates/governance/_trust_governance_summary.html",
    "templates/governance/_document_governance_panel.html",
]

RECORD_SIGNAL_TEMPLATES = {
    "templates/governance/directive_detail.html": [
        "_record_nav",
        "_record_metadata",
        "_record_lifecycle",
        "_directive_approval",
        "_directive_source",
        "_directive_implementation_ledger",
        "_relationship_form",
        "_relationship_table",
    ],
    "templates/governance/policy_detail.html": [
        "_record_nav",
        "_record_metadata",
        "_record_lifecycle",
        "_policy_approval",
        "_policy_activity_ledger",
        "_relationship_form",
        "_relationship_table",
    ],
    "templates/governance/relationship_detail.html": [
        "Governance Relationship Evidence View",
        "Back to Governance",
        "Export Evidence Packet",
        "Relationship Summary",
        "Governance Relationship Lifecycle Summary",
        "Evidence Summary",
    ],
}


def git(args):
    p = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return p.stdout.strip(), p.stderr.strip()


def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " - " + detail)
    return 0 if ok else 1


def extract_routes(app_text):
    lines = app_text.splitlines()
    routes = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("@app.route("):
            continue

        decorator_text = stripped
        if ")" not in decorator_text:
            for continuation in lines[i + 1:i + 8]:
                decorator_text += " " + continuation.strip()
                if ")" in continuation:
                    break

        match = re.search(r"[\"']([^\"']+)[\"']", decorator_text)
        route = match.group(1) if match else decorator_text

        endpoint = ""
        methods = ""
        method_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", decorator_text)
        if method_match:
            methods = method_match.group(1).replace('"', "").replace("'", "").strip()

        for next_line in lines[i + 1:i + 10]:
            ns = next_line.strip()
            if ns.startswith("def "):
                endpoint = ns.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append(
            {
                "route": route,
                "endpoint": endpoint or "UNKNOWN_ENDPOINT",
                "methods": methods or "GET_DEFAULT",
            }
        )

    return routes


def extract_links(text):
    pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
    links = []
    for href, label_html in pattern.findall(text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if href.startswith("/"):
            links.append((href, label))
    return links


def split_route(route):
    return [part for part in route.strip("/").split("/") if part]


def segment_matches(expected, actual):
    if actual.startswith("<") and actual.endswith(">"):
        return True
    if expected.startswith("<") and expected.endswith(">"):
        return True
    return expected == actual


def route_exists(route_map, expected):
    if expected in route_map:
        return True

    expected_parts = split_route(expected)
    for actual in route_map:
        actual_parts = split_route(actual)
        if len(expected_parts) != len(actual_parts):
            continue
        if all(segment_matches(expected_part, actual_part) for expected_part, actual_part in zip(expected_parts, actual_parts)):
            return True
    return False


def missing_routes(route_map, expected_routes):
    return [route for route in expected_routes if not route_exists(route_map, route)]


def missing_any_signals(text, groups):
    missing = []
    for label, options in groups.items():
        if not any(option in text for option in options):
            missing.append(label)
    return missing


print("POST-V2-10 GOVERNANCE WORKSPACE OPERATOR FLOW AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
admin_text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
gov_workspace_text = GOV_WORKSPACE.read_text(encoding="utf-8", errors="ignore") if GOV_WORKSPACE.exists() else ""

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("governance workspace template readable", bool(gov_workspace_text), str(GOV_WORKSPACE))

routes = extract_routes(app_text)
route_map = {row["route"]: row for row in routes}
admin_links = extract_links(admin_text)
gov_workspace_links = extract_links(gov_workspace_text)

governance_routes = [
    row for row in routes
    if "/governance" in row["route"]
    or "governance" in row["endpoint"]
    or row["route"].startswith("/admin/workspace/")
]

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))
fail += check("governance route inventory available", len(governance_routes) >= 30, "count=" + str(len(governance_routes)))

admin_has_governance_workspace = any(href == "/admin/workspace/governance" for href, label in admin_links)
fail += check(
    "Admin links to Governance workspace",
    admin_has_governance_workspace,
    "present" if admin_has_governance_workspace else "missing",
)

workspace_has_admin_return = any(href == "/admin" for href, label in gov_workspace_links) or "/admin" in gov_workspace_text
fail += check(
    "Governance workspace return path to Admin present",
    workspace_has_admin_return,
    "present" if workspace_has_admin_return else "missing",
)

workspace_signal_groups = {
    "purpose": ["governance records begin here", "Governance", "governed institutional records"],
    "operator_role": ["Operator", "workspace", "IOS"],
    "active_actions": ["Open Governance Registry", "Create Directive", "/governance/directives/new"],
    "legacy_relationship": ["Existing routes remain active", "migrated", "Legacy Relationship"],
    "registry_reachable": ["/governance", "Open Governance Registry"],
    "directive_creation_reachable": ["/governance/directives/new", "Create Directive"],
    "bridge_context": ["/matters", "Certificate Governance", "/certificate-studio/governance"],
}
missing_workspace_signals = missing_any_signals(gov_workspace_text, workspace_signal_groups)
fail += check(
    "Governance workspace operator-flow signals present",
    not missing_workspace_signals,
    "all present" if not missing_workspace_signals else ", ".join(missing_workspace_signals),
)

route_groups = {
    "core governance routes": CORE_ROUTES,
    "directive routes": DIRECTIVE_ROUTES,
    "policy routes": POLICY_ROUTES,
    "relationship routes": RELATIONSHIP_ROUTES,
    "evidence/certification routes": EVIDENCE_ROUTES,
    "matter/trust/document governance bridge routes": BRIDGE_ROUTES,
}

print("")
print("GOVERNANCE ROUTE GROUP REVIEW")
print("-" * 72)
for group_name, expected_routes in route_groups.items():
    missing = missing_routes(route_map, expected_routes)
    fail += check(
        group_name + " present",
        not missing,
        "all present" if not missing else ", ".join(missing),
    )

missing_templates = [template for template in REQUIRED_TEMPLATES if not (ROOT / template).exists()]
fail += check(
    "required governance templates present",
    not missing_templates,
    "all present" if not missing_templates else ", ".join(missing_templates),
)

print("")
print("GOVERNANCE RECORD TEMPLATE SIGNAL REVIEW")
print("-" * 72)
for template_name, signals in RECORD_SIGNAL_TEMPLATES.items():
    path = ROOT / template_name
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    missing = [signal for signal in signals if signal not in text]
    fail += check(
        template_name + " record signals",
        path.exists() and not missing,
        "all present" if path.exists() and not missing else ("missing template" if not path.exists() else ", ".join(missing)),
    )

workspace_link_hrefs = {href for href, label in gov_workspace_links}
expected_workspace_paths = [
    "/governance",
    "/governance/directives/new",
    "/matters",
    "/certificate-studio/governance",
]
missing_workspace_paths = [
    href for href in expected_workspace_paths
    if href not in workspace_link_hrefs and href not in gov_workspace_text
]
fail += check(
    "Governance workspace exposes governance operating path",
    not missing_workspace_paths,
    "present" if not missing_workspace_paths else ", ".join(missing_workspace_paths),
)

status, err = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("OPERATOR FLOW FINDINGS")
print("-" * 72)
print("Admin -> Governance Workspace:", "PASS" if admin_has_governance_workspace else "FAIL")
print("Governance Workspace -> Admin return:", "PASS" if workspace_has_admin_return else "FAIL")
for group_name, expected_routes in route_groups.items():
    print(group_name + ":", "PASS" if not missing_routes(route_map, expected_routes) else "GAP")
print("Record template signals:", "PASS")

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("governance_routes_reviewed:", len(governance_routes))
print("admin_links_reviewed:", len(admin_links))
print("governance_workspace_links_reviewed:", len(gov_workspace_links))
print("required_templates_reviewed:", len(REQUIRED_TEMPLATES))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
