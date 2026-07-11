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

AUDIT_CHAIN = [
    "scripts/audit_document_to_governance_link_patch_11c.py",
    "scripts/audit_trust_to_governance_link_patch_11b.py",
    "scripts/audit_matter_to_governance_link_patch_11a.py",
    "scripts/audit_matter_governance_continuity_11.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_relationship_usability_10b.py",
    "scripts/audit_admin_system_control_final_closure_9e.py",
]

MATTER_FILES = [
    ROOT / "templates" / "matters_dashboard.html",
    ROOT / "templates" / "matter_detail.html",
    ROOT / "templates" / "governance" / "_matter_governance_summary.html",
    ROOT / "templates" / "governance" / "_matter_governance_timeline.html",
]

TRUST_FILES = [
    ROOT / "templates" / "trust_detail.html",
    ROOT / "templates" / "transfer_execution_dashboard.html",
    ROOT / "templates" / "governance" / "_trust_governance_panel.html",
    ROOT / "templates" / "governance" / "_trust_governance_summary.html",
    ROOT / "templates" / "governance" / "_trust_governance_timeline.html",
]

DOCUMENT_FILES = [
    ROOT / "templates" / "document_platform_governance.html",
    ROOT / "templates" / "document_platform_workspace.html",
    ROOT / "templates" / "governance" / "_document_governance_panel.html",
]

RELATIONSHIP_FILES = [
    ROOT / "templates" / "governance" / "_relationship_form.html",
    ROOT / "templates" / "governance" / "_relationship_table.html",
    ROOT / "templates" / "governance" / "relationship_detail.html",
    ROOT / "templates" / "governance" / "relationship_lifecycle_dashboard.html",
]

EVIDENCE_TEMPLATE_CANDIDATES = [
    ROOT / "templates" / "governance" / "evidence_export_index.html",
    ROOT / "templates" / "governance" / "evidence_export_manifest.html",
    ROOT / "templates" / "governance" / "evidence_export_integrity.html",
    ROOT / "templates" / "governance" / "evidence_export_archive_intake.html",
    ROOT / "templates" / "governance" / "evidence_exception_panel.html",
    ROOT / "templates" / "governance" / "evidence_completion_gate.html",
    ROOT / "templates" / "governance" / "evidence_certification_dashboard.html",
    ROOT / "templates" / "governance" / "v2_certification_dashboard.html",
]

MATTER_LOCKS = [
    "Matter Governance Continuity",
    "connects this matter",
    "does not by itself prove",
    "Review Matter Governance",
    "Create Governance Link",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
]

TRUST_LOCKS = [
    "Trust Governance Continuity",
    "connects this trust",
    "does not by itself prove",
    "Review Trust Governance Links",
    "Return to Trust Execution",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
]

DOCUMENT_LOCKS = [
    "Document Governance Continuity",
    "connects this document",
    "does not by itself prove",
    "Document Governance Registry",
    "Review Document Governance Links",
    "Return to Document Workspace",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
]

RELATIONSHIP_LOCKS = [
    "Relationship Guidance",
    "does not by itself prove",
    "authorizes",
    "implements",
    "supersedes",
    "depends_on",
    "governs",
    "references",
    "Outgoing",
    "Incoming",
]

GOV_WORKSPACE_LOCKS = [
    "/governance/directives/new",
    "/governance/policies/new",
    "/governance/relationship-lifecycle",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/admin",
]

CORE_BRIDGE_ROUTES = [
    "/matters/<matter_id>/governance",
    "/matters/<matter_id>/governance-links",
    "/trust/<trust_id>/governance-links",
    "/trust/<trust_id>/execution",
    "/document-platform/governance",
    "/document-platform/workspace/<path:document_id>/governance-links",
    "/admin/workspace/governance",
    "/governance",
    "/governance/relationship-lifecycle",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/admin",
]

ADMIN_SYSTEM_CONTROL_LOCKS = [
    "/admin/backup/database.zip",
    "MEDIUM RISK",
    "DOWNLOADS LIVE DATABASE COPY",
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
    p = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return p.stdout.strip(), p.stderr.strip()


def run_script(script_path):
    p = subprocess.run(
        ["python", script_path],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return p.returncode, p.stdout, p.stderr


def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " - " + detail)
    return 0 if ok else 1


def read(path):
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def read_many(paths):
    return "\n".join(read(path) for path in paths)


def existing(paths):
    return [str(path.relative_to(ROOT)) for path in paths if path.exists()]


def missing_items(text, items):
    low = text.lower()
    missing = []
    for item in items:
        if item.lower() not in low:
            missing.append(item)
    return missing


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
        routes.append(route)
    return set(routes)


def route_present(route, routes):
    if route in routes:
        return True
    if route == "/admin/workspace/governance":
        return "/admin/workspace/<workspace_key>" in routes
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


print("POST-V2-11D GOVERNANCE CONTINUITY CLOSURE CERTIFICATION")
print("=" * 78)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
admin_text = read(ADMIN_TEMPLATE)
gov_workspace_text = read(GOV_WORKSPACE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

matter_text = read_many(MATTER_FILES)
trust_text = read_many(TRUST_FILES)
document_text = read_many(DOCUMENT_FILES)
relationship_text = read_many(RELATIONSHIP_FILES)
evidence_text = read_many(EVIDENCE_TEMPLATE_CANDIDATES)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("governance workspace template readable", bool(gov_workspace_text), str(GOV_WORKSPACE))
fail += check("matter templates/partials readable", bool(matter_text), ", ".join(existing(MATTER_FILES)))
fail += check("trust templates/partials readable", bool(trust_text), ", ".join(existing(TRUST_FILES)))
fail += check("document templates/partials readable", bool(document_text), ", ".join(existing(DOCUMENT_FILES)))
fail += check("relationship templates readable", bool(relationship_text), ", ".join(existing(RELATIONSHIP_FILES)))
fail += check(
    "evidence/certification templates readable",
    bool(evidence_text),
    ", ".join(existing(EVIDENCE_TEMPLATE_CANDIDATES)) or "none found",
)

routes = extract_routes(app_text)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

admin_links = extract_links(admin_text)
admin_link_hrefs = {href for href, label in admin_links}
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

print("")
print("POST-V2-11 SERIES AUDIT SCRIPT STATUS")
print("-" * 78)

for script in AUDIT_CHAIN:
    script_path = ROOT / script
    fail += check(script + " exists", script_path.exists(), "present" if script_path.exists() else "missing")
    if script_path.exists():
        code, stdout, stderr = run_script(script)
        ok = code == 0 and "RESULT: PASS" in stdout
        fail += check(script + " passes", ok, "PASS" if ok else "FAIL")

missing_matter = missing_items(matter_text, MATTER_LOCKS)
fail += check(
    "Matter-to-Governance continuity retained",
    not missing_matter,
    "retained" if not missing_matter else ", ".join(missing_matter),
)

missing_trust = missing_items(trust_text, TRUST_LOCKS)
fail += check(
    "Trust-to-Governance continuity retained",
    not missing_trust,
    "retained" if not missing_trust else ", ".join(missing_trust),
)

missing_document = missing_items(document_text, DOCUMENT_LOCKS)
fail += check(
    "Document-to-Governance continuity retained",
    not missing_document,
    "retained" if not missing_document else ", ".join(missing_document),
)

missing_relationship = missing_items(relationship_text, RELATIONSHIP_LOCKS)
fail += check(
    "Governance relationship usability retained",
    not missing_relationship,
    "retained" if not missing_relationship else ", ".join(missing_relationship),
)

missing_workspace = missing_items(gov_workspace_text, GOV_WORKSPACE_LOCKS)
fail += check(
    "Governance workspace controls retained",
    not missing_workspace,
    "retained" if not missing_workspace else ", ".join(missing_workspace),
)

missing_routes = [route for route in CORE_BRIDGE_ROUTES if not route_present(route, routes)]
fail += check(
    "Core governance continuity bridge routes retained",
    not missing_routes,
    "retained" if not missing_routes else ", ".join(missing_routes),
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

visible_hidden_high_risk = [
    route for route in HIDDEN_HIGH_RISK_ROUTES
    if route in admin_link_hrefs
]

fail += check(
    "hidden high-risk Admin controls remain hidden",
    not visible_hidden_high_risk,
    "none" if not visible_hidden_high_risk else ", ".join(visible_hidden_high_risk),
)

diff_app, err = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes in 11D", not diff_app, "none" if not diff_app else "app.py diff detected")

diff_templates, err = git(["diff", "--", "templates"])
fail += check("no template behavior changes in 11D", not diff_templates, "none" if not diff_templates else "template diff detected")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("GOVERNANCE CONTINUITY CLOSURE INVENTORY")
print("-" * 78)
print("matter_files_found:", existing(MATTER_FILES))
print("trust_files_found:", existing(TRUST_FILES))
print("document_files_found:", existing(DOCUMENT_FILES))
print("relationship_files_found:", existing(RELATIONSHIP_FILES))
print("evidence_templates_found:", existing(EVIDENCE_TEMPLATE_CANDIDATES))
print("core_bridge_routes_required:", len(CORE_BRIDGE_ROUTES))
print("audit_scripts_reviewed:", len(AUDIT_CHAIN))

print("")
print("SUMMARY")
print("-" * 78)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("missing_matter_locks:", missing_matter)
print("missing_trust_locks:", missing_trust)
print("missing_document_locks:", missing_document)
print("missing_relationship_locks:", missing_relationship)
print("missing_workspace_locks:", missing_workspace)
print("missing_bridge_routes:", missing_routes)
print("visible_hidden_high_risk_controls:", visible_hidden_high_risk)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
