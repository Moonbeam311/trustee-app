from collections import defaultdict
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MATTER_ROUTES = [
    "/matters",
    "/matters/<matter_id>/governance",
    "/matters/<matter_id>/governance-links",
]

TRUST_ROUTES = [
    "/trust/<trust_id>/governance-links",
    "/trust/<trust_id>/execution",
]

GOVERNANCE_ROUTES = [
    "/governance",
    "/governance/dashboard",
    "/governance/directives/new",
    "/governance/directives/<directive_id>",
    "/governance/directives/<directive_id>/relationships",
    "/governance/policies/new",
    "/governance/policies/<policy_id>",
    "/governance/policies/<policy_id>/relationships",
    "/governance/relationships/<relationship_id>",
    "/governance/relationship-lifecycle",
    "/governance/relationship-audits",
]

DOCUMENT_ROUTES = [
    "/document-platform/governance",
    "/document-platform/workspace/<path:document_id>/governance-links",
]

EVIDENCE_ROUTES = [
    "/governance/evidence-exports",
    "/governance/evidence-exports.csv",
    "/governance/evidence-exports/certification",
    "/governance/evidence-exports/certification.txt",
    "/governance/v2-certification",
    "/governance/v2-certification.txt",
    "/governance/evidence-exports/manifest",
    "/governance/evidence-exports/manifest.txt",
]

WORKSPACE_RETURN_ROUTES = [
    "/admin",
    "/admin/workspace/governance",
    "/admin/workspace/administer",
]

REQUIRED_TEMPLATES = [
    "templates/matters_dashboard.html",
    "templates/governance/_matter_governance_summary.html",
    "templates/governance/_matter_governance_timeline.html",
    "templates/governance/_trust_governance_panel.html",
    "templates/governance/_trust_governance_summary.html",
    "templates/governance/_trust_governance_timeline.html",
    "templates/governance/_document_governance_panel.html",
    "templates/governance/_relationship_form.html",
    "templates/governance/_relationship_table.html",
    "templates/governance/registry.html",
    "templates/governance/relationship_detail.html",
    "templates/governance/evidence_export_index.html",
    "templates/ios_workspaces/governance.html",
    "templates/admin_index.html",
]

PANEL_SIGNAL_REQUIREMENTS = {
    "templates/governance/_matter_governance_summary.html": ["Matter", "Governance", "Summary"],
    "templates/governance/_matter_governance_timeline.html": ["Matter", "Governance", "Timeline"],
    "templates/governance/_trust_governance_panel.html": ["Trust", "Governance"],
    "templates/governance/_trust_governance_summary.html": ["Trust", "Governance", "Summary"],
    "templates/governance/_trust_governance_timeline.html": ["Trust", "Governance", "Timeline"],
    "templates/governance/_document_governance_panel.html": ["Document", "Governance"],
}

GOV_WORKSPACE_LOCKS = [
    "/governance/directives/new",
    "/governance/policies/new",
    "/governance/relationship-lifecycle",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/admin",
]

RELATIONSHIP_USABILITY_LOCKS = [
    "Relationship Guidance",
    "does not by itself prove",
    "legal effect",
    "authenticity",
    "authority",
    "completion",
    "authorizes",
    "implements",
    "supersedes",
    "depends_on",
    "governs",
    "references",
    "Outgoing",
    "Incoming",
]

ADMIN_SYSTEM_CONTROL_LOCKS = [
    "/admin/backup/database.zip",
    "DOWNLOADS LIVE DATABASE COPY",
    "MEDIUM RISK",
]

BACKUP_CONFIRM_LOCKS = [
    "Confirm Database Backup Download",
    "admin_database_backup_zip",
    "confirmed=1",
    "MEDIUM RISK",
]

HIDDEN_HIGH_RISK_ROUTES = [
    "/admin/seed-hosted-baseline",
    "/users/<username>/reset_password",
    "/system/recovery/reseed-permissions",
    "/hosted-production-health",
    "/bootstrap_admin_once",
    "/admin/reset_admin_once",
    "/admin/run-hosted-firm-scope-migration",
    "/admin/hosted-bootstrap-admin",
    "/hosted-bootstrap-admin-once",
    "/hosted-firm-scope-migration-once",
    "/hosted-reseed-permissions-once",
    "/hosted-clear-login-lockout-once",
    "/hosted-auth-diagnostic-once",
    "/hosted-repair-admin-access-once",
    "/hosted-trust-diagnostic-once",
    "/admin/repair/int-lifecycle-tables",
    "/admin/diag/seed-execution-objects",
    "/intake/<intake_id>/professional-review/issues/seed/<workflow_key>",
]


def git(args):
    process = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return process.stdout.strip(), process.stderr.strip()


def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " - " + detail)
    return 0 if ok else 1


def read(path):
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def missing_items(text, items):
    lowered = text.lower()
    return [item for item in items if item.lower() not in lowered]


def extract_routes(app_text):
    lines = app_text.splitlines()
    routes = []
    endpoint_by_route = {}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("@app.route("):
            continue

        decorator_text = stripped
        if ")" not in decorator_text:
            for continuation in lines[i + 1 : i + 8]:
                decorator_text += " " + continuation.strip()
                if ")" in continuation:
                    break

        match = re.search(r"[\"']([^\"']+)[\"']", decorator_text)
        route = match.group(1) if match else decorator_text

        endpoint = ""
        for next_line in lines[i + 1 : i + 10]:
            next_stripped = next_line.strip()
            if next_stripped.startswith("def "):
                endpoint = next_stripped.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append(route)
        endpoint_by_route[route] = endpoint or "UNKNOWN_ENDPOINT"

    return routes, endpoint_by_route


def route_parts_match(candidate, required):
    candidate_parts = candidate.strip("/").split("/")
    required_parts = required.strip("/").split("/")

    if len(candidate_parts) != len(required_parts):
        return False

    for candidate_part, required_part in zip(candidate_parts, required_parts):
        if candidate_part.startswith("<path:") and candidate_part.endswith(">"):
            continue
        if required_part.startswith("<path:") and required_part.endswith(">"):
            continue
        if candidate_part.startswith("<") and candidate_part.endswith(">"):
            continue
        if required_part.startswith("<") and required_part.endswith(">"):
            continue
        if candidate_part != required_part:
            return False

    return True


def route_exists(required_route, route_set):
    if required_route in route_set:
        return True
    return any(route_parts_match(candidate, required_route) for candidate in route_set)


def extract_links(template_text):
    pattern = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
    links = []
    for href, label_html in pattern.findall(template_text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if href.startswith("/"):
            links.append((href, label))
    return links


def classify_panel(path_str, signals):
    path = ROOT / path_str
    text = read(path)
    if not path.exists() or not text:
        return "MISSING_OR_BROKEN", signals

    missing = missing_items(text, signals)
    if not missing:
        return "PRESENT_AND_COHERENT", []

    return "PRESENT_BUT_NEEDS_OPERATOR_CLARITY", missing


print("POST-V2-11 MATTER GOVERNANCE CONTINUITY AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
admin_text = read(ADMIN_TEMPLATE)
gov_workspace_text = read(GOV_WORKSPACE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("governance workspace readable", bool(gov_workspace_text), str(GOV_WORKSPACE))

routes, endpoint_by_route = extract_routes(app_text)
route_set = set(routes)
admin_links = extract_links(admin_text)
admin_link_hrefs = {href for href, _label in admin_links}

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

route_groups = {
    "matter governance routes": MATTER_ROUTES,
    "trust governance routes": TRUST_ROUTES,
    "governance bridge routes": GOVERNANCE_ROUTES,
    "document platform governance routes": DOCUMENT_ROUTES,
    "evidence/certification routes": EVIDENCE_ROUTES,
    "workspace return routes": WORKSPACE_RETURN_ROUTES,
}

print("")
print("MATTER / TRUST / GOVERNANCE CONTINUITY ROUTE REVIEW")
print("-" * 72)

missing_route_groups = {}
for group_name, expected in route_groups.items():
    missing = [route for route in expected if not route_exists(route, route_set)]
    if missing:
        missing_route_groups[group_name] = missing
    fail += check(
        group_name + " present",
        not missing,
        "all present" if not missing else ", ".join(missing),
    )

missing_templates = [template for template in REQUIRED_TEMPLATES if not (ROOT / template).exists()]
fail += check(
    "required continuity templates present",
    not missing_templates,
    "all present" if not missing_templates else ", ".join(missing_templates),
)

print("")
print("CONTINUITY PANEL CLASSIFICATION")
print("-" * 72)

panel_classifications = defaultdict(int)
panel_clarity_gaps = {}

for template_path, signals in PANEL_SIGNAL_REQUIREMENTS.items():
    classification, missing = classify_panel(template_path, signals)
    panel_classifications[classification] += 1
    if missing:
        panel_clarity_gaps[template_path] = missing
    suffix = "" if not missing else " | missing: " + ", ".join(missing)
    print(f"{classification} | {template_path}{suffix}")

if panel_classifications["MISSING_OR_BROKEN"]:
    fail += check(
        "governance continuity panels not broken",
        False,
        "missing/broken count=" + str(panel_classifications["MISSING_OR_BROKEN"]),
    )
else:
    fail += check("governance continuity panels not broken", True, "none missing or broken")

missing_workspace_locks = missing_items(gov_workspace_text, GOV_WORKSPACE_LOCKS)
fail += check(
    "POST-V2-10A/10C Governance workspace flow retained",
    not missing_workspace_locks,
    "retained" if not missing_workspace_locks else ", ".join(missing_workspace_locks),
)

relationship_text = "\n".join(
    [
        read(ROOT / "templates/governance/_relationship_form.html"),
        read(ROOT / "templates/governance/_relationship_table.html"),
        read(ROOT / "templates/governance/relationship_detail.html"),
        read(ROOT / "templates/governance/relationship_lifecycle_dashboard.html"),
    ]
)

missing_relationship_locks = missing_items(relationship_text, RELATIONSHIP_USABILITY_LOCKS)
fail += check(
    "POST-V2-10B relationship usability retained",
    not missing_relationship_locks,
    "retained" if not missing_relationship_locks else ", ".join(missing_relationship_locks),
)

missing_admin_locks = missing_items(admin_text, ADMIN_SYSTEM_CONTROL_LOCKS)
fail += check(
    "Admin system-control closure retained",
    not missing_admin_locks,
    "retained" if not missing_admin_locks else ", ".join(missing_admin_locks),
)

missing_backup_locks = missing_items(backup_confirm_text, BACKUP_CONFIRM_LOCKS)
fail += check(
    "Admin backup confirmation gate retained",
    not missing_backup_locks,
    "retained" if not missing_backup_locks else ", ".join(missing_backup_locks),
)

visible_hidden_high_risk = [route for route in HIDDEN_HIGH_RISK_ROUTES if route in admin_link_hrefs]
fail += check(
    "hidden high-risk Admin controls remain hidden",
    not visible_hidden_high_risk,
    "none" if not visible_hidden_high_risk else ", ".join(visible_hidden_high_risk),
)

status, _ = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("CONTINUITY SUMMARY")
print("-" * 72)
for key in sorted(panel_classifications):
    print(f"{key}: {panel_classifications[key]}")

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("matter_routes_reviewed:", len(MATTER_ROUTES))
print("trust_routes_reviewed:", len(TRUST_ROUTES))
print("governance_routes_reviewed:", len(GOVERNANCE_ROUTES))
print("document_routes_reviewed:", len(DOCUMENT_ROUTES))
print("evidence_routes_reviewed:", len(EVIDENCE_ROUTES))
print("workspace_return_routes_reviewed:", len(WORKSPACE_RETURN_ROUTES))
print("templates_reviewed:", len(REQUIRED_TEMPLATES))
print("panel_classifications:", dict(sorted(panel_classifications.items())))
print("panel_clarity_gaps:", dict(panel_clarity_gaps))
print("missing_route_groups:", missing_route_groups)
print("missing_templates:", missing_templates)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
