from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
REL_FORM = ROOT / "templates" / "governance" / "_relationship_form.html"
REL_TABLE = ROOT / "templates" / "governance" / "_relationship_table.html"
REL_DETAIL = ROOT / "templates" / "governance" / "relationship_detail.html"
REL_LIFECYCLE = ROOT / "templates" / "governance" / "relationship_lifecycle_dashboard.html"
DIRECTIVE_DETAIL = ROOT / "templates" / "governance" / "directive_detail.html"
POLICY_DETAIL = ROOT / "templates" / "governance" / "policy_detail.html"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-10B GOVERNANCE RELATIONSHIP USABILITY PATCH"

RELATIONSHIP_VERBS = [
    "authorizes",
    "implements",
    "supersedes",
    "depends_on",
    "governs",
    "references",
]

DIRECTION_SIGNALS = [
    "Outgoing",
    "Incoming",
]

CAUTION_SIGNALS = [
    "does not by itself prove",
    "legal effect",
    "authenticity",
    "authority",
    "completion",
]

GUIDANCE_SIGNALS = [
    "Relationship Guidance",
    "connect",
    "governed connection record",
]

NAV_LINKS = [
    "/governance",
    "/admin/workspace/governance",
    "/governance/relationship-lifecycle",
    "/governance/relationship-audits",
]

RELATIONSHIP_LIFECYCLE_ROUTES = [
    "/governance/relationships/<relationship_id>/export",
    "/governance/relationships/<relationship_id>/reinstate",
    "/governance/relationships/<relationship_id>/supersede",
    "/governance/relationships/<relationship_id>/retire",
]

DETAIL_RELATIONSHIP_SIGNALS = [
    "_relationship_table",
    "_relationship_form",
]

GOV_WORKSPACE_10A_LOCKS = [
    "/governance/directives/new",
    "/governance/policies/new",
    "/governance/relationship-lifecycle",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/admin",
]

ADMIN_BACKUP_LOCKS = [
    "DOWNLOADS LIVE DATABASE COPY",
    "/admin/backup/database.zip",
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


def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " - " + detail)
    return 0 if ok else 1


def read(path):
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


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
            for continuation in lines[i + 1 : i + 8]:
                decorator_text += " " + continuation.strip()
                if ")" in continuation:
                    break

        match = re.search(r"[\"']([^\"']+)[\"']", decorator_text)
        route = match.group(1) if match else decorator_text
        routes.append(route)

    return routes


print("POST-V2-10B GOVERNANCE RELATIONSHIP USABILITY AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
rel_form_text = read(REL_FORM)
rel_table_text = read(REL_TABLE)
rel_detail_text = read(REL_DETAIL)
rel_lifecycle_text = read(REL_LIFECYCLE)
directive_text = read(DIRECTIVE_DETAIL)
policy_text = read(POLICY_DETAIL)
gov_workspace_text = read(GOV_WORKSPACE)
admin_text = read(ADMIN_TEMPLATE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("relationship form template readable", bool(rel_form_text), str(REL_FORM))
fail += check("relationship table template readable", bool(rel_table_text), str(REL_TABLE))
fail += check("relationship detail template readable", bool(rel_detail_text), str(REL_DETAIL))
fail += check("relationship lifecycle template readable", bool(rel_lifecycle_text), str(REL_LIFECYCLE))
fail += check("directive detail template readable", bool(directive_text), str(DIRECTIVE_DETAIL))
fail += check("policy detail template readable", bool(policy_text), str(POLICY_DETAIL))

combined_relationship_text = "\n".join(
    [
        rel_form_text,
        rel_table_text,
        rel_detail_text,
        rel_lifecycle_text,
        directive_text,
        policy_text,
    ]
)

routes = set(extract_routes(app_text))
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

fail += check(
    "10B marker present",
    MARKER in combined_relationship_text,
    "present" if MARKER in combined_relationship_text else "missing",
)

missing_guidance = missing_items(combined_relationship_text, GUIDANCE_SIGNALS)
fail += check(
    "relationship guidance language present",
    not missing_guidance,
    "all present" if not missing_guidance else ", ".join(missing_guidance),
)

missing_caution = missing_items(combined_relationship_text, CAUTION_SIGNALS)
fail += check(
    "relationship caution language present",
    not missing_caution,
    "all present" if not missing_caution else ", ".join(missing_caution),
)

missing_verbs = missing_items(combined_relationship_text, RELATIONSHIP_VERBS)
fail += check(
    "relationship verb explanations present",
    not missing_verbs,
    "all present" if not missing_verbs else ", ".join(missing_verbs),
)

missing_directions = missing_items(combined_relationship_text, DIRECTION_SIGNALS)
fail += check(
    "relationship direction language present",
    not missing_directions,
    "all present" if not missing_directions else ", ".join(missing_directions),
)

missing_nav = missing_items(combined_relationship_text, NAV_LINKS)
fail += check(
    "relationship navigation links present",
    not missing_nav,
    "all present" if not missing_nav else ", ".join(missing_nav),
)

missing_lifecycle_routes = [route for route in RELATIONSHIP_LIFECYCLE_ROUTES if route not in routes]
fail += check(
    "relationship lifecycle action routes retained",
    not missing_lifecycle_routes,
    "all present" if not missing_lifecycle_routes else ", ".join(missing_lifecycle_routes),
)

missing_directive_relationship_signals = missing_items(directive_text, DETAIL_RELATIONSHIP_SIGNALS)
fail += check(
    "directive detail relationship controls retained",
    not missing_directive_relationship_signals,
    "all present" if not missing_directive_relationship_signals else ", ".join(missing_directive_relationship_signals),
)

missing_policy_relationship_signals = missing_items(policy_text, DETAIL_RELATIONSHIP_SIGNALS)
fail += check(
    "policy detail relationship controls retained",
    not missing_policy_relationship_signals,
    "all present" if not missing_policy_relationship_signals else ", ".join(missing_policy_relationship_signals),
)

missing_10a_locks = missing_items(gov_workspace_text, GOV_WORKSPACE_10A_LOCKS)
fail += check(
    "POST-V2-10A governance workspace flow retained",
    not missing_10a_locks,
    "retained" if not missing_10a_locks else ", ".join(missing_10a_locks),
)

missing_admin_locks = missing_items(admin_text, ADMIN_BACKUP_LOCKS)
fail += check(
    "Admin backup warning retained",
    not missing_admin_locks,
    "retained" if not missing_admin_locks else ", ".join(missing_admin_locks),
)

missing_backup_locks = missing_items(backup_confirm_text, BACKUP_CONFIRM_LOCKS)
fail += check(
    "Admin backup confirmation gate retained",
    not missing_backup_locks,
    "retained" if not missing_backup_locks else ", ".join(missing_backup_locks),
)

diff_app, _ = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes", not diff_app, "none" if not diff_app else "app.py diff detected")

status, _ = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("GOVERNANCE RELATIONSHIP USABILITY INVENTORY")
print("-" * 72)
print("relationship_verbs_required:", len(RELATIONSHIP_VERBS))
print("navigation_links_required:", len(NAV_LINKS))
print("relationship_lifecycle_routes_required:", len(RELATIONSHIP_LIFECYCLE_ROUTES))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("missing_guidance:", missing_guidance)
print("missing_caution:", missing_caution)
print("missing_verbs:", missing_verbs)
print("missing_directions:", missing_directions)
print("missing_nav:", missing_nav)
print("missing_lifecycle_routes:", missing_lifecycle_routes)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
