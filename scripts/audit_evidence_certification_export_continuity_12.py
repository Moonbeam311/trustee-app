from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

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

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

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

WORKSPACE_ROUTES = [
    "/admin/workspace/governance",
    "/governance",
    "/admin",
]

CONTINUITY_ROUTES = [
    "/matters/<matter_id>/governance",
    "/matters/<matter_id>/governance-links",
    "/trust/<trust_id>/governance-links",
    "/document-platform/governance",
    "/document-platform/workspace/<path:document_id>/governance-links",
]

GOV_WORKSPACE_EVIDENCE_LOCKS = [
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "Evidence",
    "Certification",
    "Export",
]

EVIDENCE_SIGNALS = [
    "Evidence",
    "Certification",
    "Export",
    "Manifest",
    "V2 Certification",
    "Governance Registry",
    "Governance Workspace",
    "Return to Admin",
    "CSV",
    "TXT",
    "institutional",
    "continuity",
]

AUDIT_CHAIN = [
    "scripts/audit_governance_continuity_closure_11d.py",
    "scripts/audit_document_to_governance_link_patch_11c.py",
    "scripts/audit_trust_to_governance_link_patch_11b.py",
    "scripts/audit_matter_to_governance_link_patch_11a.py",
    "scripts/audit_matter_governance_continuity_11.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_relationship_usability_10b.py",
    "scripts/audit_admin_system_control_final_closure_9e.py",
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
    endpoints = {}

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
        for next_line in lines[i + 1:i + 12]:
            ns = next_line.strip()
            if ns.startswith("def "):
                endpoint = ns.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append(route)
        endpoints[route] = endpoint or "UNKNOWN_ENDPOINT"

    return set(routes), endpoints


def route_present(route, routes):
    if route in routes:
        return True
    if route == "/admin/workspace/governance":
        return "/admin/workspace/<workspace_key>" in routes
    return False


def endpoint_for(route, endpoints):
    if route in endpoints:
        return endpoints[route]
    if route == "/admin/workspace/governance":
        return endpoints.get("/admin/workspace/<workspace_key>", "")
    return ""


def extract_links(template_text):
    pattern = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
    links = []
    for href, label_html in pattern.findall(template_text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if href.startswith("/"):
            links.append((href, label))
    return links


print("POST-V2-12 EVIDENCE CERTIFICATION EXPORT CONTINUITY AUDIT")
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
evidence_template_text = read_many(EVIDENCE_TEMPLATE_CANDIDATES)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("governance workspace template readable", bool(gov_workspace_text), str(GOV_WORKSPACE))
fail += check(
    "evidence/certification template candidates checked",
    bool(evidence_template_text),
    ", ".join(existing(EVIDENCE_TEMPLATE_CANDIDATES)) or "none found",
)

routes, endpoints = extract_routes(app_text)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

admin_links = extract_links(admin_text)
admin_link_hrefs = {href for href, label in admin_links}
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

missing_evidence_routes = [route for route in EVIDENCE_ROUTES if not route_present(route, routes)]
fail += check(
    "evidence/export/certification routes retained",
    not missing_evidence_routes,
    "retained" if not missing_evidence_routes else ", ".join(missing_evidence_routes),
)

missing_endpoint_routes = [
    route for route in EVIDENCE_ROUTES
    if route_present(route, routes) and not endpoint_for(route, endpoints)
]
fail += check(
    "evidence/export/certification route functions exist",
    not missing_endpoint_routes,
    "all mapped" if not missing_endpoint_routes else ", ".join(missing_endpoint_routes),
)

missing_workspace_routes = [route for route in WORKSPACE_ROUTES if not route_present(route, routes)]
fail += check(
    "workspace return routes retained",
    not missing_workspace_routes,
    "retained" if not missing_workspace_routes else ", ".join(missing_workspace_routes),
)

missing_continuity_routes = [route for route in CONTINUITY_ROUTES if not route_present(route, routes)]
fail += check(
    "Matter/Trust/Document continuity routes retained",
    not missing_continuity_routes,
    "retained" if not missing_continuity_routes else ", ".join(missing_continuity_routes),
)

missing_workspace_locks = missing_items(gov_workspace_text, GOV_WORKSPACE_EVIDENCE_LOCKS)
fail += check(
    "Governance workspace evidence/certification links retained",
    not missing_workspace_locks,
    "retained" if not missing_workspace_locks else ", ".join(missing_workspace_locks),
)

evidence_combined = "\n".join([app_text, gov_workspace_text, evidence_template_text])
missing_evidence_signals = missing_items(evidence_combined, EVIDENCE_SIGNALS)
fail += check(
    "evidence/certification export signals present",
    not missing_evidence_signals,
    "present" if not missing_evidence_signals else ", ".join(missing_evidence_signals),
)

print("")
print("POST-V2 CONTINUITY AUDIT CHAIN STATUS")
print("-" * 78)

for script in AUDIT_CHAIN:
    script_path = ROOT / script
    fail += check(script + " exists", script_path.exists(), "present" if script_path.exists() else "missing")
    if script_path.exists():
        code, stdout, stderr = run_script(script)
        ok = code == 0 and "RESULT: PASS" in stdout
        fail += check(script + " passes", ok, "PASS" if ok else "FAIL")

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
fail += check("no app.py changes in 12", not diff_app, "none" if not diff_app else "app.py diff detected")

diff_templates, err = git(["diff", "--", "templates"])
fail += check("no template changes in 12", not diff_templates, "none" if not diff_templates else "template diff detected")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("EVIDENCE / CERTIFICATION EXPORT CONTINUITY INVENTORY")
print("-" * 78)
print("evidence_routes_reviewed:", len(EVIDENCE_ROUTES))
print("workspace_routes_reviewed:", len(WORKSPACE_ROUTES))
print("continuity_routes_reviewed:", len(CONTINUITY_ROUTES))
print("audit_scripts_reviewed:", len(AUDIT_CHAIN))
print("evidence_templates_found:", existing(EVIDENCE_TEMPLATE_CANDIDATES))
print("evidence_route_endpoints:")
for route in EVIDENCE_ROUTES:
    print("  " + route + " -> " + (endpoint_for(route, endpoints) or "MISSING"))

print("")
print("SUMMARY")
print("-" * 78)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("missing_evidence_routes:", missing_evidence_routes)
print("missing_endpoint_routes:", missing_endpoint_routes)
print("missing_workspace_routes:", missing_workspace_routes)
print("missing_continuity_routes:", missing_continuity_routes)
print("missing_workspace_locks:", missing_workspace_locks)
print("missing_evidence_signals:", missing_evidence_signals)
print("visible_hidden_high_risk_controls:", visible_hidden_high_risk)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
