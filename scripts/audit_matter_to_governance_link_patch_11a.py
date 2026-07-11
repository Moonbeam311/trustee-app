from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
MATTERS_DASHBOARD = ROOT / "templates" / "matters_dashboard.html"
MATTER_DETAIL = ROOT / "templates" / "matter_detail.html"
MATTER_SUMMARY = ROOT / "templates" / "governance" / "_matter_governance_summary.html"
MATTER_TIMELINE = ROOT / "templates" / "governance" / "_matter_governance_timeline.html"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-11A MATTER TO GOVERNANCE LINK PATCH"

REQUIRED_ROUTES = [
    "/matters",
    "/matters/<matter_id>/governance",
    "/matters/<matter_id>/governance-links",
    "/admin/workspace/governance",
    "/governance",
    "/admin",
]

MATTER_GUIDANCE_SIGNALS = [
    "Matter Governance Continuity",
    "connects this matter",
    "directives",
    "policies",
    "relationships",
    "evidence",
    "governed institutional records",
]

MATTER_CAUTION_SIGNALS = [
    "does not by itself prove",
    "legal effect",
    "authenticity",
    "authority",
    "completion",
    "Verification",
    "approval",
    "lifecycle",
    "evidence review",
]

MATTER_ACTION_SIGNALS = [
    "Review Matter Governance",
    "Create Governance Link",
    "Governance Workspace",
    "Governance Registry",
    "Return to Admin",
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


def route_exists(required_route, route_set):
    if required_route in route_set:
        return True
    return any(route_parts_match(candidate, required_route) for candidate in route_set)


print("POST-V2-11A MATTER TO GOVERNANCE LINK PATCH AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
matters_text = read(MATTERS_DASHBOARD)
matter_detail_text = read(MATTER_DETAIL)
summary_text = read(MATTER_SUMMARY)
timeline_text = read(MATTER_TIMELINE)
gov_workspace_text = read(GOV_WORKSPACE)
admin_text = read(ADMIN_TEMPLATE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("matters dashboard readable", bool(matters_text), str(MATTERS_DASHBOARD))
fail += check("matter detail readable", bool(matter_detail_text), str(MATTER_DETAIL))
fail += check("matter governance summary readable", bool(summary_text), str(MATTER_SUMMARY))
fail += check("matter governance timeline readable", bool(timeline_text), str(MATTER_TIMELINE))

routes = extract_routes(app_text)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

matter_combined = "\n".join([matters_text, matter_detail_text, summary_text, timeline_text])

fail += check(
    "11A marker present",
    MARKER in matter_combined,
    "present" if MARKER in matter_combined else "missing",
)

missing_routes = [route for route in REQUIRED_ROUTES if not route_exists(route, routes)]
fail += check(
    "Matter-to-Governance routes retained",
    not missing_routes,
    "all present" if not missing_routes else ", ".join(missing_routes),
)

missing_guidance = missing_items(matter_combined, MATTER_GUIDANCE_SIGNALS)
fail += check(
    "Matter governance guidance present",
    not missing_guidance,
    "all present" if not missing_guidance else ", ".join(missing_guidance),
)

missing_caution = missing_items(matter_combined, MATTER_CAUTION_SIGNALS)
fail += check(
    "Matter governance caution present",
    not missing_caution,
    "all present" if not missing_caution else ", ".join(missing_caution),
)

missing_actions = missing_items(matter_combined, MATTER_ACTION_SIGNALS)
fail += check(
    "Matter governance action links/signals present",
    not missing_actions,
    "all present" if not missing_actions else ", ".join(missing_actions),
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
    "scripts/audit_matter_governance_continuity_11.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_relationship_usability_10b.py",
]:
    code, stdout, stderr = run_script(script)
    ok = code == 0 and "RESULT: PASS" in stdout
    fail += check(script + " still passes", ok, "PASS" if ok else "FAIL")

diff_app, _ = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes", not diff_app, "none" if not diff_app else "app.py diff detected")

status, _ = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("MATTER TO GOVERNANCE LINK PATCH INVENTORY")
print("-" * 72)
print("required_routes:", len(REQUIRED_ROUTES))
print("guidance_signals:", len(MATTER_GUIDANCE_SIGNALS))
print("caution_signals:", len(MATTER_CAUTION_SIGNALS))
print("action_signals:", len(MATTER_ACTION_SIGNALS))

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
