from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
GOV_REGISTRY = ROOT / "templates" / "governance" / "registry.html"
DIRECTIVE_DETAIL = ROOT / "templates" / "governance" / "directive_detail.html"
POLICY_DETAIL = ROOT / "templates" / "governance" / "policy_detail.html"
REL_FORM = ROOT / "templates" / "governance" / "_relationship_form.html"
REL_TABLE = ROOT / "templates" / "governance" / "_relationship_table.html"
REL_DETAIL = ROOT / "templates" / "governance" / "relationship_detail.html"
REL_LIFECYCLE = ROOT / "templates" / "governance" / "relationship_lifecycle_dashboard.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

EXPECTED_AUDIT_SCRIPTS = [
    "scripts/audit_governance_workspace_operator_flow_10.py",
    "scripts/audit_governance_create_review_approve_flow_10a.py",
    "scripts/audit_governance_relationship_usability_10b.py",
]

GOV_WORKSPACE_LINKS = [
    "/governance",
    "/governance/dashboard",
    "/governance/directives/new",
    "/governance/policies/new",
    "/governance/relationship-lifecycle",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/admin",
]

GOV_WORKSPACE_SIGNALS = [
    "Create",
    "Review",
    "Approve",
    "Ratify",
    "Relate",
    "Certify",
    "Evidence",
    "Return",
]

RELATIONSHIP_SIGNALS = [
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

CERTIFICATION_ROUTES = [
    "/admin/workspace/governance",
    "/governance",
    "/governance/dashboard",
    "/governance/directives/new",
    "/governance/policies/new",
    "/governance/relationship-lifecycle",
    "/governance/relationship-audits",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/matters/<matter_id>/governance",
    "/matters/<matter_id>/governance-links",
    "/trust/<trust_id>/governance-links",
    "/document-platform/governance",
    "/document-platform/workspace/<path:document_id>/governance-links",
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


def run_script(script_path):
    process = subprocess.run(
        ["python", script_path],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return process.returncode, process.stdout, process.stderr


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


def route_exists(required_route, route_set):
    if required_route in route_set:
        return True

    required_parts = required_route.strip("/").split("/")
    for candidate in route_set:
        candidate_parts = candidate.strip("/").split("/")
        if len(candidate_parts) != len(required_parts):
            continue

        matched = True
        for candidate_part, required_part in zip(candidate_parts, required_parts):
            if candidate_part.startswith("<path:") and candidate_part.endswith(">"):
                continue
            if candidate_part.startswith("<") and candidate_part.endswith(">"):
                continue
            if candidate_part != required_part:
                matched = False
                break

        if matched:
            return True

    return False


def extract_links(template_text):
    pattern = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
    links = []
    for href, label_html in pattern.findall(template_text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if href.startswith("/"):
            links.append((href, label))
    return links


print("POST-V2-10C GOVERNANCE WORKSPACE CERTIFICATION")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
admin_text = read(ADMIN_TEMPLATE)
gov_workspace_text = read(GOV_WORKSPACE)
gov_registry_text = read(GOV_REGISTRY)
directive_text = read(DIRECTIVE_DETAIL)
policy_text = read(POLICY_DETAIL)
rel_form_text = read(REL_FORM)
rel_table_text = read(REL_TABLE)
rel_detail_text = read(REL_DETAIL)
rel_lifecycle_text = read(REL_LIFECYCLE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("governance workspace readable", bool(gov_workspace_text), str(GOV_WORKSPACE))
fail += check("governance registry readable", bool(gov_registry_text), str(GOV_REGISTRY))
fail += check("directive detail readable", bool(directive_text), str(DIRECTIVE_DETAIL))
fail += check("policy detail readable", bool(policy_text), str(POLICY_DETAIL))
fail += check(
    "relationship templates readable",
    all([rel_form_text, rel_table_text, rel_detail_text, rel_lifecycle_text]),
    "readable",
)

routes, endpoint_by_route = extract_routes(app_text)
route_set = set(routes)
admin_links = extract_links(admin_text)
admin_link_hrefs = {href for href, _label in admin_links}

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

missing_scripts = [script for script in EXPECTED_AUDIT_SCRIPTS if not (ROOT / script).exists()]
fail += check(
    "POST-V2-10 series audit scripts present",
    not missing_scripts,
    "all present" if not missing_scripts else ", ".join(missing_scripts),
)

print("")
print("POST-V2-10 SERIES AUDIT SCRIPT STATUS")
print("-" * 72)

for script in EXPECTED_AUDIT_SCRIPTS:
    if not (ROOT / script).exists():
        print("MISSING | " + script)
        fail += 1
        continue

    code, stdout, stderr = run_script(script)
    result = "PASS" if code == 0 and "RESULT: PASS" in stdout else "FAIL"
    print(result + " | " + script)
    if result != "PASS":
        fail += 1

missing_workspace_links = missing_items(gov_workspace_text, GOV_WORKSPACE_LINKS)
fail += check(
    "Governance workspace required links retained",
    not missing_workspace_links,
    "retained" if not missing_workspace_links else ", ".join(missing_workspace_links),
)

missing_workspace_signals = missing_items(gov_workspace_text, GOV_WORKSPACE_SIGNALS)
fail += check(
    "Governance workspace operator signals retained",
    not missing_workspace_signals,
    "retained" if not missing_workspace_signals else ", ".join(missing_workspace_signals),
)

relationship_text = "\n".join([rel_form_text, rel_table_text, rel_detail_text, rel_lifecycle_text])
missing_relationship_signals = missing_items(relationship_text, RELATIONSHIP_SIGNALS)
fail += check(
    "Governance relationship usability retained",
    not missing_relationship_signals,
    "retained" if not missing_relationship_signals else ", ".join(missing_relationship_signals),
)

missing_certification_routes = [
    route for route in CERTIFICATION_ROUTES if not route_exists(route, route_set)
]
fail += check(
    "Governance certification route set retained",
    not missing_certification_routes,
    "retained" if not missing_certification_routes else ", ".join(missing_certification_routes),
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

diff_app, _ = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes in 10C", not diff_app, "none" if not diff_app else "app.py diff detected")

status, _ = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("GOVERNANCE WORKSPACE CERTIFICATION POSTURE")
print("-" * 72)
print("governance_workspace_links_required:", len(GOV_WORKSPACE_LINKS))
print("governance_workspace_signals_required:", len(GOV_WORKSPACE_SIGNALS))
print("relationship_signals_required:", len(RELATIONSHIP_SIGNALS))
print("certification_routes_required:", len(CERTIFICATION_ROUTES))
print("visible_hidden_high_risk_controls:", len(visible_hidden_high_risk))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("post_v2_10_audits_reviewed:", len(EXPECTED_AUDIT_SCRIPTS))
print("missing_workspace_links:", missing_workspace_links)
print("missing_workspace_signals:", missing_workspace_signals)
print("missing_relationship_signals:", missing_relationship_signals)
print("missing_certification_routes:", missing_certification_routes)
print("visible_hidden_high_risk_controls:", visible_hidden_high_risk)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
