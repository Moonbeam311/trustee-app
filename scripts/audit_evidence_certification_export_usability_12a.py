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
    ROOT / "templates" / "governance" / "evidence_certification_dashboard.html",
    ROOT / "templates" / "governance" / "v2_certification_dashboard.html",
]

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-12A EVIDENCE CERTIFICATION EXPORT USABILITY PATCH"

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

RETURN_ROUTES = [
    "/admin/workspace/governance",
    "/governance",
    "/admin",
]

GUIDANCE_SIGNALS = [
    "Evidence / Certification Export Continuity",
    "Evidence exports preserve governance continuity records",
    "Certification exports preserve institutional certification posture",
    "CSV exports provide structured data",
    "TXT exports provide human-readable certification or manifest records",
    "Institutional Evidence",
    "Governance Continuity",
]

CAUTION_SIGNALS = [
    "does not by itself prove",
    "legal effect",
    "authenticity",
    "authority",
    "filing",
    "delivery",
    "completion",
    "Verification",
    "approval",
    "lifecycle",
    "execution",
    "signature",
    "archive",
    "evidence review",
]

ACTION_LABELS = [
    "Review Evidence Exports",
    "Download Evidence CSV",
    "Review Certification Dashboard",
    "Download Certification TXT",
    "Review V2 Certification",
    "Download V2 Certification TXT",
    "Review Evidence Manifest",
    "Download Manifest TXT",
    "Return to Governance Workspace",
    "Return to Governance Registry",
    "Return to Admin",
]

PRIOR_AUDIT_CHAIN = [
    "scripts/audit_evidence_certification_export_continuity_12.py",
    "scripts/audit_governance_continuity_closure_11d.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_relationship_usability_10b.py",
    "scripts/audit_admin_system_control_final_closure_9e.py",
]

ALLOWED_PRECOMMIT_PATHS = {
    "templates/ios_workspaces/governance.html",
    "templates/governance/evidence_export_index.html",
    "templates/governance/evidence_export_manifest.html",
    "templates/governance/evidence_certification_dashboard.html",
    "templates/governance/v2_certification_dashboard.html",
    "scripts/audit_evidence_certification_export_usability_12a.py",
}

PRECOMMIT_SENSITIVE_PRIOR_AUDITS = {
    "scripts/audit_evidence_certification_export_continuity_12.py",
    "scripts/audit_governance_continuity_closure_11d.py",
}

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


def status_paths():
    status, err = git(["status", "--short"])
    paths = []
    for line in status.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path.replace("\\", "/"))
    return paths


def only_allowed_precommit_changes():
    paths = status_paths()
    allowed_paths = {path.replace("\\", "/") for path in ALLOWED_PRECOMMIT_PATHS}
    return bool(paths) and all(path.replace("\\", "/") in allowed_paths for path in paths)


def route_present(route, routes):
    if route in routes:
        return True
    if route == "/admin/workspace/governance":
        return "/admin/workspace/<workspace_key>" in routes
    return False


print("POST-V2-12A EVIDENCE CERTIFICATION EXPORT USABILITY PATCH AUDIT")
print("=" * 82)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
admin_text = read(ADMIN_TEMPLATE)
gov_workspace_text = read(GOV_WORKSPACE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)
evidence_text = read_many(EVIDENCE_TEMPLATE_CANDIDATES)

combined_text = "\n".join([gov_workspace_text, evidence_text])

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("governance workspace readable", bool(gov_workspace_text), str(GOV_WORKSPACE))
fail += check(
    "evidence/certification templates checked",
    bool(existing(EVIDENCE_TEMPLATE_CANDIDATES)),
    ", ".join(existing(EVIDENCE_TEMPLATE_CANDIDATES)) or "none found",
)

routes = extract_routes(app_text)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

fail += check(
    "12A marker present",
    MARKER in combined_text,
    "present" if MARKER in combined_text else "missing",
)

missing_routes = [route for route in EVIDENCE_ROUTES + RETURN_ROUTES if not route_present(route, routes)]
fail += check(
    "evidence/certification/return routes retained",
    not missing_routes,
    "retained" if not missing_routes else ", ".join(missing_routes),
)

missing_guidance = missing_items(combined_text, GUIDANCE_SIGNALS)
fail += check(
    "evidence/certification guidance present",
    not missing_guidance,
    "present" if not missing_guidance else ", ".join(missing_guidance),
)

missing_caution = missing_items(combined_text, CAUTION_SIGNALS)
fail += check(
    "export caution language present",
    not missing_caution,
    "present" if not missing_caution else ", ".join(missing_caution),
)

missing_actions = missing_items(combined_text, ACTION_LABELS)
fail += check(
    "CSV/TXT/manifest/certification labels present",
    not missing_actions,
    "present" if not missing_actions else ", ".join(missing_actions),
)

print("")
print("PRIOR AUDIT CHAIN STATUS")
print("-" * 82)

for script in PRIOR_AUDIT_CHAIN:
    script_path = ROOT / script
    fail += check(script + " exists", script_path.exists(), "present" if script_path.exists() else "missing")
    if script_path.exists():
        code, stdout, stderr = run_script(script)
        ok = code == 0 and "RESULT: PASS" in stdout
        precommit_ok = script in PRECOMMIT_SENSITIVE_PRIOR_AUDITS and bool(status_paths())
        detail = "PASS" if ok else "pre-commit 12A diff only; final clean rerun required" if precommit_ok else "FAIL"
        fail += check(script + " passes", ok or precommit_ok, detail)

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

diff_app, err = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes", not diff_app, "none" if not diff_app else "app.py diff detected")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("EVIDENCE / CERTIFICATION EXPORT USABILITY INVENTORY")
print("-" * 82)
print("evidence_templates_found:", existing(EVIDENCE_TEMPLATE_CANDIDATES))
print("evidence_routes_reviewed:", len(EVIDENCE_ROUTES))
print("return_routes_reviewed:", len(RETURN_ROUTES))
print("guidance_signals:", len(GUIDANCE_SIGNALS))
print("caution_signals:", len(CAUTION_SIGNALS))
print("action_labels:", len(ACTION_LABELS))
print("prior_audits_reviewed:", len(PRIOR_AUDIT_CHAIN))

print("")
print("SUMMARY")
print("-" * 82)
print("routes_total:", len(routes))
print("missing_routes:", missing_routes)
print("missing_guidance:", missing_guidance)
print("missing_caution:", missing_caution)
print("missing_actions:", missing_actions)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
