from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
GOV_WORKSPACE = ROOT / "templates" / "ios_workspaces" / "governance.html"
GOV_REGISTRY = ROOT / "templates" / "governance" / "registry.html"
DIRECTIVE_DETAIL = ROOT / "templates" / "governance" / "directive_detail.html"
POLICY_DETAIL = ROOT / "templates" / "governance" / "policy_detail.html"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-10A GOVERNANCE CREATE REVIEW APPROVE FLOW PATCH"

REQUIRED_WORKSPACE_LINKS = [
    "/governance",
    "/governance/dashboard",
    "/governance/directives/new",
    "/governance/policies/new",
    "/governance/relationship-lifecycle",
    "/governance/evidence-exports",
    "/governance/v2-certification",
    "/admin",
]

REQUIRED_WORKSPACE_SIGNALS = [
    "Create",
    "Review",
    "Approve",
    "Ratify",
    "Relate",
    "Certify",
    "Evidence",
    "Return",
]

DIRECTIVE_SIGNALS = [
    "_record_nav",
    "_record_metadata",
    "_record_lifecycle",
    "_directive_approval",
    "_relationship_table",
]

POLICY_SIGNALS = [
    "_record_nav",
    "_record_metadata",
    "_record_lifecycle",
    "_policy_approval",
    "_relationship_table",
]

ADMIN_SYSTEM_CONTROL_LOCKS = [
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


def missing_items(text, items):
    return [item for item in items if item not in text]


print("POST-V2-10A GOVERNANCE CREATE REVIEW APPROVE FLOW AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = read(APP)
workspace_text = read(GOV_WORKSPACE)
registry_text = read(GOV_REGISTRY)
directive_text = read(DIRECTIVE_DETAIL)
policy_text = read(POLICY_DETAIL)
admin_text = read(ADMIN_TEMPLATE)
backup_confirm_text = read(BACKUP_CONFIRM_TEMPLATE)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("governance workspace template readable", bool(workspace_text), str(GOV_WORKSPACE))
fail += check("governance registry template readable", bool(registry_text), str(GOV_REGISTRY))
fail += check("directive detail template readable", bool(directive_text), str(DIRECTIVE_DETAIL))
fail += check("policy detail template readable", bool(policy_text), str(POLICY_DETAIL))

routes = set(extract_routes(app_text))
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

marker_present = any(
    MARKER in text
    for text in [workspace_text, registry_text, directive_text, policy_text]
)
fail += check(
    "10A marker present",
    marker_present,
    "present" if marker_present else "missing",
)

missing_links = missing_items(workspace_text, REQUIRED_WORKSPACE_LINKS)
fail += check(
    "governance workspace required links present",
    not missing_links,
    "all present" if not missing_links else ", ".join(missing_links),
)

missing_workspace_signals = missing_items(workspace_text, REQUIRED_WORKSPACE_SIGNALS)
fail += check(
    "governance workspace create/review/approve signals present",
    not missing_workspace_signals,
    "all present" if not missing_workspace_signals else ", ".join(missing_workspace_signals),
)

missing_routes = [
    route for route in REQUIRED_WORKSPACE_LINKS if route != "/admin" and route not in routes
]
fail += check(
    "required governance routes retained",
    not missing_routes,
    "all present" if not missing_routes else ", ".join(missing_routes),
)

missing_directive_signals = missing_items(directive_text, DIRECTIVE_SIGNALS)
fail += check(
    "directive detail record controls retained",
    not missing_directive_signals,
    "all present" if not missing_directive_signals else ", ".join(missing_directive_signals),
)

missing_policy_signals = missing_items(policy_text, POLICY_SIGNALS)
fail += check(
    "policy detail record controls retained",
    not missing_policy_signals,
    "all present" if not missing_policy_signals else ", ".join(missing_policy_signals),
)

missing_admin_locks = missing_items(admin_text, ADMIN_SYSTEM_CONTROL_LOCKS)
fail += check(
    "Admin system-control locks retained",
    not missing_admin_locks,
    "retained" if not missing_admin_locks else ", ".join(missing_admin_locks),
)

missing_backup_locks = missing_items(backup_confirm_text, BACKUP_CONFIRM_LOCKS)
fail += check(
    "backup confirmation gate retained",
    not missing_backup_locks,
    "retained" if not missing_backup_locks else ", ".join(missing_backup_locks),
)

diff_app, _ = git(["diff", "--", "app.py"])
fail += check("no app.py behavior changes", not diff_app, "none" if not diff_app else "app.py diff detected")

status, _ = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("GOVERNANCE CREATE / REVIEW / APPROVE FLOW INVENTORY")
print("-" * 72)
print("workspace_links_required:", len(REQUIRED_WORKSPACE_LINKS))
print("workspace_signals_required:", len(REQUIRED_WORKSPACE_SIGNALS))
print("directive_controls_required:", len(DIRECTIVE_SIGNALS))
print("policy_controls_required:", len(POLICY_SIGNALS))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("missing_workspace_links:", missing_links)
print("missing_workspace_signals:", missing_workspace_signals)
print("missing_required_routes:", missing_routes)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
