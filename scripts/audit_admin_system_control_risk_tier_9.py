from pathlib import Path
import re
import subprocess
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

HIGH_RISK_TERMS = [
    "reset",
    "bootstrap",
    "repair",
    "migration",
    "hosted",
    "seed",
    "reseed",
]

MEDIUM_RISK_TERMS = [
    "backup",
    "database",
    "policy",
    "toggle",
    "diagnostic",
    "storage",
]

REQUIRED_SYSTEM_CONTROL_LABELS = [
    "Hosted Baseline Seed",
    "Database Backup",
    "System Policy Controls",
    "Security Layer",
]

EXPECTED_HIGH_RISK_ROUTES = [
    "/admin/seed-hosted-baseline",
    "/admin/reset_admin_once",
    "/bootstrap_admin_once",
    "/admin/run-hosted-firm-scope-migration",
    "/admin/hosted-bootstrap-admin",
    "/hosted-bootstrap-admin-once",
    "/hosted-repair-admin-access-once",
    "/admin/repair/int-lifecycle-tables",
]

EXPECTED_MEDIUM_RISK_ROUTES = [
    "/admin/backup/database",
    "/admin/backup/database.zip",
    "/admin/export-policy/toggle",
    "/admin/storage-diagnostics",
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

def extract_admin_links(text):
    pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
    links = []
    for href, label_html in pattern.findall(text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if href.startswith("/"):
            links.append((href, label))
    return links

def risk_tier(route, endpoint="", label=""):
    hay = (route + " " + endpoint + " " + label).lower()

    if any(term in hay for term in HIGH_RISK_TERMS):
        return "HIGH_RISK_CONFIRMATION_CANDIDATE"

    if any(term in hay for term in MEDIUM_RISK_TERMS):
        return "MEDIUM_RISK_WARNING_LABEL_CANDIDATE"

    return "LOW_RISK_VISIBLE_CONTROL"

print("POST-V2-9 ADMIN SYSTEM CONTROL RISK TIER AUDIT")
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
route_map = {route: endpoint for route, endpoint in routes}

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))

missing_labels = [x for x in REQUIRED_SYSTEM_CONTROL_LABELS if x not in admin_text]
fail += check(
    "system control section labels present",
    not missing_labels,
    "all present" if not missing_labels else ", ".join(missing_labels),
)

admin_links = extract_admin_links(admin_text)
admin_link_map = defaultdict(list)
for href, label in admin_links:
    admin_link_map[href].append(label)

risk_routes = []
for route, endpoint in routes:
    tier = risk_tier(route, endpoint)
    if tier != "LOW_RISK_VISIBLE_CONTROL":
        visible_labels = admin_link_map.get(route, [])
        risk_routes.append((tier, route, endpoint, visible_labels))

high_risk = [x for x in risk_routes if x[0] == "HIGH_RISK_CONFIRMATION_CANDIDATE"]
medium_risk = [x for x in risk_routes if x[0] == "MEDIUM_RISK_WARNING_LABEL_CANDIDATE"]

missing_high = [x for x in EXPECTED_HIGH_RISK_ROUTES if x not in route_set]
missing_medium = [x for x in EXPECTED_MEDIUM_RISK_ROUTES if x not in route_set]

fail += check(
    "expected high-risk routes inventoried",
    not missing_high,
    "all present" if not missing_high else ", ".join(missing_high),
)

fail += check(
    "expected medium-risk routes inventoried",
    not missing_medium,
    "all present" if not missing_medium else ", ".join(missing_medium),
)

fail += check("high-risk route inventory available", len(high_risk) >= 5, "count=" + str(len(high_risk)))
fail += check("medium-risk route inventory available", len(medium_risk) >= 3, "count=" + str(len(medium_risk)))

visible_risk_controls = []
for tier, route, endpoint, labels in risk_routes:
    if labels:
        visible_risk_controls.append((tier, route, endpoint, labels))

fail += check(
    "visible risk controls identified",
    len(visible_risk_controls) >= 1,
    "count=" + str(len(visible_risk_controls)),
)

print("")
print("SYSTEM CONTROL RISK MATRIX")
print("-" * 72)

for tier_name in [
    "HIGH_RISK_CONFIRMATION_CANDIDATE",
    "MEDIUM_RISK_WARNING_LABEL_CANDIDATE",
]:
    print("")
    print(tier_name)
    for tier, route, endpoint, labels in risk_routes:
        if tier != tier_name:
            continue
        label_text = ", ".join(labels) if labels else "[not directly visible on Admin]"
        print("  " + route + " | " + endpoint + " | " + label_text)

print("")
print("VISIBLE ADMIN RISK CONTROLS")
print("-" * 72)
for tier, route, endpoint, labels in visible_risk_controls:
    print(tier + " | " + route + " | " + ", ".join(labels))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("risk_routes_reviewed:", len(risk_routes))
print("high_risk_confirmation_candidates:", len(high_risk))
print("medium_risk_warning_candidates:", len(medium_risk))
print("visible_risk_controls:", len(visible_risk_controls))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
