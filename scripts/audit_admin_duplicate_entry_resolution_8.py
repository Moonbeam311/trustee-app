from pathlib import Path
import re
import subprocess
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
WORKSPACE_DIR = ROOT / "templates" / "ios_workspaces"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

DUPLICATE_LABELS = [
    "Existing Trust Command Cards",
    "Learning & Guidance Suite",
    "Report Launch Area",
    "Admin Tools",
    "Operational Shortcuts",
]

LEGACY_COMPATIBILITY_LABELS = [
    "Legacy Compatibility Center",
    "Legacy Quick Start",
]

SYSTEM_CONTROL_LABELS = [
    "Hosted Baseline Seed",
    "Database Backup",
    "System Policy Controls",
    "Security Layer",
]

IOS_WORKSPACE_LINKS = [
    "/admin/workspace/system",
    "/admin/workspace/governance",
    "/admin/workspace/administer",
    "/admin/workspace/archive",
    "/admin/workspace/developer",
]

RESOLUTION_RULES = {
    "Existing Trust Command Cards": "RETAIN_AS_GOVERNED_COMPATIBILITY_SURFACE",
    "Learning & Guidance Suite": "RETAIN_AS_GOVERNED_COMPATIBILITY_SURFACE",
    "Report Launch Area": "RELABEL_OR_REDIRECT_CANDIDATE",
    "Admin Tools": "RELABEL_OR_REDIRECT_CANDIDATE",
    "Operational Shortcuts": "RELABEL_OR_REDIRECT_CANDIDATE",
}

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

        m = re.search(r"[\"']([^\"']+)[\"']", decorator_text)
        route = m.group(1) if m else decorator_text

        endpoint = ""
        for next_line in lines[i + 1:i + 10]:
            ns = next_line.strip()
            if ns.startswith("def "):
                endpoint = ns.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append((route, endpoint or "UNKNOWN_ENDPOINT"))

    return routes

def extract_links_with_labels(text):
    pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
    links = []
    for href, label_html in pattern.findall(text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        links.append((href, label))
    return links

def classify_link(href, label):
    hay = (href + " " + label).lower()

    if href in IOS_WORKSPACE_LINKS or "/admin/workspace/" in href:
        return "IOS_WORKSPACE_ROUTE"

    if any(term in hay for term in ["backup", "policy", "security", "bootstrap", "reset", "repair"]):
        return "SYSTEM_CONTROL"

    if any(term in hay for term in ["legacy", "existing trust", "learning", "guidance"]):
        return "GOVERNED_COMPATIBILITY"

    if any(term in hay for term in ["report", "shortcut", "tool", "admin"]):
        return "DUPLICATE_REVIEW"

    return "ACTIVE_OR_CONTEXTUAL"

print("POST-V2-8 ADMIN DUPLICATE ENTRY POINT RESOLUTION AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
admin_text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))

routes = extract_routes(app_text)
route_set = set(route for route, endpoint in routes)
fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

missing_duplicate_labels = [x for x in DUPLICATE_LABELS if x not in admin_text]
fail += check(
    "known duplicate entry labels present",
    not missing_duplicate_labels,
    "all present" if not missing_duplicate_labels else ", ".join(missing_duplicate_labels),
)

missing_legacy_labels = [x for x in LEGACY_COMPATIBILITY_LABELS if x not in admin_text]
fail += check(
    "legacy compatibility labels present",
    not missing_legacy_labels,
    "all present" if not missing_legacy_labels else ", ".join(missing_legacy_labels),
)

missing_system_labels = [x for x in SYSTEM_CONTROL_LABELS if x not in admin_text]
fail += check(
    "system control labels present",
    not missing_system_labels,
    "all present" if not missing_system_labels else ", ".join(missing_system_labels),
)

missing_workspace_links = [x for x in IOS_WORKSPACE_LINKS if x not in admin_text]
fail += check(
    "ios workspace links remain present",
    not missing_workspace_links,
    "all present" if not missing_workspace_links else ", ".join(missing_workspace_links),
)

links = extract_links_with_labels(admin_text)
admin_links = [(href, label, classify_link(href, label)) for href, label in links if href.startswith("/")]

by_class = defaultdict(list)
for href, label, cls in admin_links:
    by_class[cls].append((href, label))

duplicate_review_items = by_class.get("DUPLICATE_REVIEW", [])
compatibility_items = by_class.get("GOVERNED_COMPATIBILITY", [])
system_items = by_class.get("SYSTEM_CONTROL", [])
workspace_items = by_class.get("IOS_WORKSPACE_ROUTE", [])

fail += check("duplicate review inventory available", len(duplicate_review_items) >= 1, "count=" + str(len(duplicate_review_items)))
fail += check("compatibility inventory available", len(compatibility_items) >= 1, "count=" + str(len(compatibility_items)))
fail += check("system control inventory available", len(system_items) >= 1, "count=" + str(len(system_items)))
fail += check("workspace inventory available", len(workspace_items) >= 5, "count=" + str(len(workspace_items)))

print("")
print("DUPLICATE LABEL RESOLUTION MATRIX")
print("-" * 72)
for label in DUPLICATE_LABELS:
    print(label + " | " + RESOLUTION_RULES.get(label, "REVIEW_REQUIRED"))

print("")
print("ADMIN LINK CLASSIFICATION INVENTORY")
print("-" * 72)
for cls in sorted(by_class):
    print("")
    print(cls)
    for href, label in by_class[cls]:
        print("  " + href + " | " + (label or "[no visible label]"))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("ios_workspace_links:", len(workspace_items))
print("governed_compatibility_links:", len(compatibility_items))
print("duplicate_review_links:", len(duplicate_review_items))
print("system_control_links:", len(system_items))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
