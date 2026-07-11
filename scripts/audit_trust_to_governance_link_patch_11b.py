from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"

TRUST_DETAIL = ROOT / "templates" / "trust_detail.html"
TRUST_EXECUTION = ROOT / "templates" / "transfer_execution_dashboard.html"
TRUST_PANEL = ROOT / "templates" / "governance" / "_trust_governance_panel.html"
TRUST_SUMMARY = ROOT / "templates" / "governance" / "_trust_governance_summary.html"
TRUST_TIMELINE = ROOT / "templates" / "governance" / "_trust_governance_timeline.html"

MATTERS_DASHBOARD = ROOT / "templates" / "matters_dashboard.html"
MATTER_DETAIL = ROOT / "templates" / "matter_detail.html"
MATTER_SUMMARY = ROOT / "templates" / "governance" / "_matter_governance_summary.html"
MATTER_TIMELINE = ROOT / "templates" / "governance" / "_matter_governance_timeline.html"

GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-11B TRUST TO GOVERNANCE LINK PATCH"

REQUIRED_ROUTES = [
    "/trust/<trust_id>/governance-links",
    "/trust/<trust_id>/execution",
    "/admin/workspace/governance",
    "/governance",
    "/admin",
]

TRUST_GUIDANCE_SIGNALS = [
    "Trust Governance Continuity",
    "connects this trust",
    "directives",
    "policies",
    "relationships",
    "evidence",
    "execution sessions",
    "governed institutional records",
]

TRUST_CAUTION_SIGNALS = [
    "does not by itself prove",
    "legal effect",
    "authenticity",
    "authority",
    "execution",
    "funding",
    "completion",
    "Verification",
    "approval",
    "lifecycle",
    "evidence review",
]

TRUST_ACTION_SIGNALS = [
    "Review Trust Governance Links",
    "Return to Trust Execution",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
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
    "DOWNLOADS LIVE DATABASE COPY",
    "MEDIUM RISK",
]

BACKUP_CONFIRM_LOCKS = [
    "Confirm Database Backup Download",
    "admin_database_backup_zip",
    "confirmed=1",
    "MEDIUM RISK",
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
        routes.append(route)
    return set(routes)


def route_parts_match(candidate, required):
    candidate_parts = candidate.strip("/").split("/")
    required_parts = required.strip("/").split("/")
    if len(candidate_parts) != len(required_parts):
        return False
    for candidate_part, required_part in zip(candidate_parts, required_parts):
        if candidate_part.startswith("<") and candidate_part.endswith(">"):
            continue
        if required_part.startswith("<") and required_part.endswith(">"):
            continue
        if candidate_part != required_part:
            return False
    return True


def route_exists(required_route, routes):
    if required_route in routes:
        return True
    return any(route_parts_match(candidate, required_route) for candidate in routes)


print("POST-V2-11B TRUST TO GOVERNANCE LINK PATCH AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)

trust_detail_text = read(TRUST_DETAIL)
trust_execution_text = read(TRUST_EXECUTION)
trust_panel_text = read(TRUST_PANEL)
trust_summary_text = read(TRUST_SUMMARY)
trust_timeline_text = read(TRUST_TIMELINE)

matter_text = "\n".join(
    [
        read(MATTERS_DASHBOARD),
        read(MATTER_DETAIL),
        read(MATTER_SUMMARY),
        read(MATTER_TIMELINE),
    ]
)

gov_workspace_text = read(GOV_WORKSPACE)
admin_text = read(ADMIN_TEMPLATE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("trust detail template readable", bool(trust_detail_text), str(TRUST_DETAIL))
fail += check("trust execution template readable", bool(trust_execution_text), str(TRUST_EXECUTION))
fail += check("trust governance panel readable", bool(trust_panel_text), str(TRUST_PANEL))
fail += check("trust governance summary readable", bool(trust_summary_text), str(TRUST_SUMMARY))
fail += check("trust governance timeline readable", bool(trust_timeline_text), str(TRUST_TIMELINE))

routes = extract_routes(app_text)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

trust_combined = "\n".join(
    [
        trust_detail_text,
        trust_execution_text,
        trust_panel_text,
        trust_summary_text,
        trust_timeline_text,
    ]
)

fail += check(
    "11B marker present",
    MARKER in trust_combined,
    "present" if MARKER in trust_combined else "missing",
)

missing_routes = [route for route in REQUIRED_ROUTES if not route_exists(route, routes)]
fail += check(
    "Trust-to-Governance routes retained",
    not missing_routes,
    "all present" if not missing_routes else ", ".join(missing_routes),
)

missing_guidance = missing_items(trust_combined, TRUST_GUIDANCE_SIGNALS)
fail += check(
    "Trust governance guidance present",
    not missing_guidance,
    "all present" if not missing_guidance else ", ".join(missing_guidance),
)

missing_caution = missing_items(trust_combined, TRUST_CAUTION_SIGNALS)
fail += check(
    "Trust governance caution present",
    not missing_caution,
    "all present" if not missing_caution else ", ".join(missing_caution),
)

missing_actions = missing_items(trust_combined, TRUST_ACTION_SIGNALS)
fail += check(
    "Trust governance action links/signals present",
    not missing_actions,
    "all present" if not missing_actions else ", ".join(missing_actions),
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

for script in [
    "scripts/audit_matter_to_governance_link_patch_11a.py",
    "scripts/audit_matter_governance_continuity_11.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_relationship_usability_10b.py",
]:
    code, stdout, stderr = run_script(script)
    ok = code == 0 and "RESULT: PASS" in stdout
    fail += check(script + " still passes", ok, "PASS" if ok else "FAIL")

diff_app, err = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes", not diff_app, "none" if not diff_app else "app.py diff detected")

status, err = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("TRUST TO GOVERNANCE LINK PATCH INVENTORY")
print("-" * 72)
print("required_routes:", len(REQUIRED_ROUTES))
print("guidance_signals:", len(TRUST_GUIDANCE_SIGNALS))
print("caution_signals:", len(TRUST_CAUTION_SIGNALS))
print("action_signals:", len(TRUST_ACTION_SIGNALS))

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
