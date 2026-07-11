from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"

DOCUMENT_TEMPLATE_CANDIDATES = [
    ROOT / "templates" / "document_platform_governance.html",
    ROOT / "templates" / "document_platform_workspace.html",
    ROOT / "templates" / "governance" / "_document_governance_panel.html",
]

TRUST_FILES = [
    ROOT / "templates" / "trust_detail.html",
    ROOT / "templates" / "transfer_execution_dashboard.html",
    ROOT / "templates" / "governance" / "_trust_governance_panel.html",
    ROOT / "templates" / "governance" / "_trust_governance_summary.html",
    ROOT / "templates" / "governance" / "_trust_governance_timeline.html",
]

MATTER_FILES = [
    ROOT / "templates" / "matters_dashboard.html",
    ROOT / "templates" / "matter_detail.html",
    ROOT / "templates" / "governance" / "_matter_governance_summary.html",
    ROOT / "templates" / "governance" / "_matter_governance_timeline.html",
]

GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-11C DOCUMENT TO GOVERNANCE LINK PATCH"

REQUIRED_ROUTES = [
    "/document-platform/governance",
    "/document-platform/workspace/<path:document_id>",
    "/document-platform/workspace/<path:document_id>/governance-links",
    "/admin/workspace/governance",
    "/governance",
    "/admin",
]

DOCUMENT_GUIDANCE_SIGNALS = [
    "Document Governance Continuity",
    "connects this document",
    "connects a document",
    "directives",
    "policies",
    "relationships",
    "evidence",
    "execution sessions",
    "document packets",
    "governed institutional records",
    "Governance State",
    "Continuity",
]

DOCUMENT_CAUTION_SIGNALS = [
    "does not by itself prove",
    "legal effect",
    "authenticity",
    "authority",
    "execution",
    "signature",
    "delivery",
    "filing",
    "completion",
    "Verification",
    "approval",
    "lifecycle",
    "evidence review",
]

DOCUMENT_ACTION_SIGNALS = [
    "Document Governance Registry",
    "Review Document Governance Links",
    "Return to Document Workspace",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
    "/document-platform/governance",
    "/admin/workspace/governance",
    "/governance",
    "/admin",
]

TRUST_11B_LOCKS = [
    "Trust Governance Continuity",
    "Review Trust Governance Links",
    "Return to Trust Execution",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
    "does not by itself prove",
]

MATTER_11A_LOCKS = [
    "Matter Governance Continuity",
    "Review Matter Governance",
    "Create Governance Link",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
    "does not by itself prove",
]

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
    "MEDIUM RISK",
    "DOWNLOADS LIVE DATABASE COPY",
]

BACKUP_CONFIRM_LOCKS = [
    "Confirm Database Backup Download",
    "admin_database_backup_zip",
    "confirmed=1",
    "MEDIUM RISK",
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


print("POST-V2-11C DOCUMENT TO GOVERNANCE LINK PATCH AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
document_text = read_many(DOCUMENT_TEMPLATE_CANDIDATES)
trust_text = read_many(TRUST_FILES)
matter_text = read_many(MATTER_FILES)
gov_workspace_text = read(GOV_WORKSPACE)
admin_text = read(ADMIN_TEMPLATE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))

existing_document_templates = existing(DOCUMENT_TEMPLATE_CANDIDATES)
fail += check(
    "document governance templates readable",
    len(existing_document_templates) == len(DOCUMENT_TEMPLATE_CANDIDATES),
    ", ".join(existing_document_templates) if existing_document_templates else "none found",
)

routes = extract_routes(app_text)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

fail += check(
    "11C marker present",
    MARKER in document_text,
    "present" if MARKER in document_text else "missing",
)

missing_routes = [route for route in REQUIRED_ROUTES if not route_present(route, routes)]
fail += check(
    "Document-to-Governance routes retained",
    not missing_routes,
    "all present" if not missing_routes else ", ".join(missing_routes),
)

missing_guidance = [
    item for item in DOCUMENT_GUIDANCE_SIGNALS
    if item.lower() not in document_text.lower()
]
if "connects this document" in missing_guidance and "connects a document" in document_text.lower():
    missing_guidance.remove("connects this document")
if "connects a document" in missing_guidance and "connects this document" in document_text.lower():
    missing_guidance.remove("connects a document")
fail += check(
    "Document governance guidance present",
    not missing_guidance,
    "all present" if not missing_guidance else ", ".join(missing_guidance),
)

missing_caution = missing_items(document_text, DOCUMENT_CAUTION_SIGNALS)
fail += check(
    "Document governance caution present",
    not missing_caution,
    "all present" if not missing_caution else ", ".join(missing_caution),
)

missing_actions = missing_items(document_text, DOCUMENT_ACTION_SIGNALS)
fail += check(
    "Document governance action links/signals present",
    not missing_actions,
    "all present" if not missing_actions else ", ".join(missing_actions),
)

missing_trust_locks = missing_items(trust_text, TRUST_11B_LOCKS)
fail += check(
    "POST-V2-11B Trust-to-Governance patch retained",
    not missing_trust_locks,
    "retained" if not missing_trust_locks else ", ".join(missing_trust_locks),
)

missing_matter_locks = missing_items(matter_text, MATTER_11A_LOCKS)
fail += check(
    "POST-V2-11A Matter-to-Governance patch retained",
    not missing_matter_locks,
    "retained" if not missing_matter_locks else ", ".join(missing_matter_locks),
)

missing_workspace_locks = missing_items(gov_workspace_text, GOV_WORKSPACE_LOCKS)
fail += check(
    "POST-V2-10C Governance workspace certification retained",
    not missing_workspace_locks,
    "retained" if not missing_workspace_locks else ", ".join(missing_workspace_locks),
)

relationship_text = "\n".join([
    read(ROOT / "templates/governance/_relationship_form.html"),
    read(ROOT / "templates/governance/_relationship_table.html"),
    read(ROOT / "templates/governance/relationship_detail.html"),
    read(ROOT / "templates/governance/relationship_lifecycle_dashboard.html"),
])

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

for script in [
    "scripts/audit_trust_to_governance_link_patch_11b.py",
    "scripts/audit_matter_to_governance_link_patch_11a.py",
    "scripts/audit_matter_governance_continuity_11.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_relationship_usability_10b.py",
]:
    code, stdout, stderr = run_script(script)
    fail += check(
        script + " still passes",
        code == 0 and "RESULT: PASS" in stdout,
        "PASS" if code == 0 and "RESULT: PASS" in stdout else "FAIL",
    )

diff_app, err = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes", not diff_app, "none" if not diff_app else "app.py diff detected")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("DOCUMENT TO GOVERNANCE LINK PATCH INVENTORY")
print("-" * 72)
print("document_templates_found:", existing_document_templates)
print("required_routes:", len(REQUIRED_ROUTES))
print("guidance_signals:", len(DOCUMENT_GUIDANCE_SIGNALS))
print("caution_signals:", len(DOCUMENT_CAUTION_SIGNALS))
print("action_signals:", len(DOCUMENT_ACTION_SIGNALS))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("missing_routes:", missing_routes)
print("missing_guidance:", missing_guidance)
print("missing_caution:", missing_caution)
print("missing_actions:", missing_actions)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
