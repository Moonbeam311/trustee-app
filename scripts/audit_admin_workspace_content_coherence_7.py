from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT / "templates" / "ios_workspaces"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

WORKSPACES = {
    "system.html": {
        "purpose": ["system", "status", "diagnostic", "health", "operating"],
        "operator": ["operator", "admin", "administrator", "institutional"],
        "actions": ["href=", "admin-actions", "workspace", "dashboard"],
        "legacy": ["legacy", "preserved", "continuity", "existing"],
        "return": ["/admin", "Return to Admin Dashboard"],
    },
    "governance.html": {
        "purpose": ["governance", "directive", "policy", "decision", "institutional"],
        "operator": ["operator", "admin", "administrator", "institutional"],
        "actions": ["href=", "admin-actions", "governance", "dashboard"],
        "legacy": ["legacy", "preserved", "continuity", "existing"],
        "return": ["/admin", "Return to Admin Dashboard"],
    },
    "administer.html": {
        "purpose": ["administer", "administration", "matter", "trust", "intake"],
        "operator": ["operator", "admin", "administrator", "institutional"],
        "actions": ["href=", "admin-actions", "dashboard"],
        "legacy": ["legacy", "preserved", "existing", "No legacy admin dashboard route was removed"],
        "return": ["/admin", "Legacy Admin Dashboard", "Return to Admin Dashboard"],
    },
    "archive.html": {
        "purpose": ["archive", "continuity", "record", "preservation", "recovery"],
        "operator": ["operator", "admin", "administrator", "institutional"],
        "actions": ["href=", "admin-actions", "archive", "dashboard"],
        "legacy": ["legacy", "preserved", "continuity", "existing"],
        "return": ["/admin", "Return to Admin Dashboard"],
    },
    "developer.html": {
        "purpose": ["developer", "diagnostic", "repair", "migration", "system"],
        "operator": ["operator", "admin", "administrator", "institutional"],
        "actions": ["href=", "admin-actions", "diagnostic", "developer"],
        "legacy": ["legacy", "preserved", "continuity", "existing"],
        "return": ["/admin", "Return to Admin Dashboard"],
    },
}

ADMIN_ANCHORS = [
    "IOS Workspace Navigation",
    "System Workspace",
    "Governance Workspace",
    "Administer Workspace",
    "Archive Workspace",
    "Developer Workspace",
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
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

def contains_any(text, terms):
    low = text.lower()
    return any(term.lower() in low for term in terms)

def links_from_text(text):
    return re.findall(r"href=[\"']([^\"']+)[\"']", text)

print("POST-V2-7 ADMIN WORKSPACE CONTENT COHERENCE AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)

admin_text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))

missing_admin_anchors = [x for x in ADMIN_ANCHORS if x not in admin_text]
fail += check(
    "admin workspace navigation anchors present",
    not missing_admin_anchors,
    "all present" if not missing_admin_anchors else ", ".join(missing_admin_anchors),
)

print("")
print("WORKSPACE CONTENT REVIEW")
print("-" * 72)

workspace_results = {}

for filename, rules in WORKSPACES.items():
    path = WORKSPACE_DIR / filename
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    links = links_from_text(text)

    checks = {
        "exists": path.exists(),
        "purpose": contains_any(text, rules["purpose"]),
        "operator_role": contains_any(text, rules["operator"]),
        "active_actions": contains_any(text, rules["actions"]) and len(links) >= 1,
        "legacy_relationship": contains_any(text, rules["legacy"]),
        "return_path": contains_any(text, rules["return"]),
    }

    workspace_results[filename] = checks

    print("")
    print(filename)
    for key, ok in checks.items():
        print(("  PASS: " if ok else "  FAIL: ") + key)

    missing = [key for key, ok in checks.items() if not ok]
    fail += check(
        filename + " content coherent",
        not missing,
        "all required signals present" if not missing else "missing: " + ", ".join(missing),
    )

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("CONTENT COHERENCE INVENTORY")
print("-" * 72)
for filename, checks in workspace_results.items():
    passed = sum(1 for ok in checks.values() if ok)
    total = len(checks)
    print(filename + ":", str(passed) + "/" + str(total), "signals present")

print("")
print("SUMMARY")
print("-" * 72)
print("workspaces_reviewed:", len(WORKSPACES))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
