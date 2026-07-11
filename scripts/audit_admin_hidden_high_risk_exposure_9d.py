from collections import defaultdict
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

POST_9C_ROUTE = "/admin/backup/database.zip"
POST_9C_CONFIRM_TEXT = "Confirm Database Backup Download"

EXPECTED_HIGH_RISK_ROUTES = [
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

CLASSIFICATION_RULES = {
    "/admin/seed-hosted-baseline": "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "/users/<username>/reset_password": "REQUIRE_CONFIRMATION_BEFORE_EXPOSURE",
    "/system/recovery/reseed-permissions": "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "/hosted-production-health": "KEEP_HIDDEN_CONTEXTUAL",
    "/bootstrap_admin_once": "DEPRECATION_REVIEW_ONLY",
    "/admin/reset_admin_once": "DEPRECATION_REVIEW_ONLY",
    "/admin/run-hosted-firm-scope-migration": "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "/admin/hosted-bootstrap-admin": "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "/hosted-bootstrap-admin-once": "DEPRECATION_REVIEW_ONLY",
    "/hosted-firm-scope-migration-once": "DEPRECATION_REVIEW_ONLY",
    "/hosted-reseed-permissions-once": "DEPRECATION_REVIEW_ONLY",
    "/hosted-clear-login-lockout-once": "DEPRECATION_REVIEW_ONLY",
    "/hosted-auth-diagnostic-once": "KEEP_HIDDEN_CONTEXTUAL",
    "/hosted-repair-admin-access-once": "DEPRECATION_REVIEW_ONLY",
    "/hosted-trust-diagnostic-once": "KEEP_HIDDEN_CONTEXTUAL",
    "/admin/repair/int-lifecycle-tables": "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "/admin/diag/seed-execution-objects": "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "/intake/<intake_id>/professional-review/issues/seed/<workflow_key>": (
        "REQUIRE_CONFIRMATION_BEFORE_EXPOSURE"
    ),
}

ALLOWED_CLASSIFICATIONS = {
    "KEEP_HIDDEN_CONTEXTUAL",
    "REQUIRE_CONFIRMATION_BEFORE_EXPOSURE",
    "PROTECTED_RECOVERY_SURFACE_CANDIDATE",
    "DEPRECATION_REVIEW_ONLY",
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
    print(("PASS" if ok else "FAIL") + ": " + name + " - " + detail)
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

        match = re.search(r"[\"']([^\"']+)[\"']", decorator_text)
        route = match.group(1) if match else decorator_text

        endpoint = ""
        methods = ""
        method_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", decorator_text)
        if method_match:
            methods = method_match.group(1).replace('"', "").replace("'", "").strip()

        for next_line in lines[i + 1:i + 10]:
            ns = next_line.strip()
            if ns.startswith("def "):
                endpoint = ns.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append(
            {
                "route": route,
                "endpoint": endpoint or "UNKNOWN_ENDPOINT",
                "methods": methods or "GET_DEFAULT",
            }
        )

    return routes


def extract_admin_links(template_text):
    pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
    links = []
    for href, label_html in pattern.findall(template_text):
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if href.startswith("/"):
            links.append((href, label))
    return links


print("POST-V2-9D HIDDEN HIGH-RISK ADMIN CONTROL EXPOSURE AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
admin_text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
confirm_text = CONFIRM_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if CONFIRM_TEMPLATE.exists() else ""

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))

routes = extract_routes(app_text)
route_map = {row["route"]: row for row in routes}

admin_links = extract_admin_links(admin_text)
admin_link_map = defaultdict(list)
for href, label in admin_links:
    admin_link_map[href].append(label)

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

missing_routes = [route for route in EXPECTED_HIGH_RISK_ROUTES if route not in route_map]
fail += check(
    "expected high-risk routes still present",
    not missing_routes,
    "all present" if not missing_routes else ", ".join(missing_routes),
)

visible_high_risk = {
    route: admin_link_map[route]
    for route in EXPECTED_HIGH_RISK_ROUTES
    if route in admin_link_map
}
fail += check(
    "hidden high-risk routes not directly visible on Admin",
    not visible_high_risk,
    "none" if not visible_high_risk else str(visible_high_risk),
)

route_body_start = app_text.find("def admin_database_backup_zip")
route_body_end = app_text.find("\n@app.route(", route_body_start + 1) if route_body_start >= 0 else -1
backup_route_body = app_text[
    route_body_start: route_body_end if route_body_end > route_body_start else len(app_text)
]

fail += check(
    "POST-V2-9C backup route still present",
    POST_9C_ROUTE in route_map,
    "present" if POST_9C_ROUTE in route_map else "missing",
)
fail += check(
    "POST-V2-9C backup warning label retained",
    "MEDIUM RISK" in admin_text and "DOWNLOADS LIVE DATABASE COPY" in admin_text,
    "present" if "MEDIUM RISK" in admin_text and "DOWNLOADS LIVE DATABASE COPY" in admin_text else "missing",
)
fail += check(
    "POST-V2-9C confirmation gate retained",
    'request.args.get("confirmed") != "1"' in backup_route_body
    and "admin_backup_database_confirm.html" in backup_route_body,
    "present" if "admin_backup_database_confirm.html" in backup_route_body else "missing",
)
fail += check(
    "POST-V2-9C confirmation template retained",
    CONFIRM_TEMPLATE.exists()
    and POST_9C_CONFIRM_TEXT in confirm_text
    and "DOWNLOADS LIVE DATABASE COPY" in confirm_text,
    "present" if CONFIRM_TEMPLATE.exists() and POST_9C_CONFIRM_TEXT in confirm_text else "missing",
)

visible_medium_gate_controls = [
    (href, label)
    for href, label in admin_links
    if href == POST_9C_ROUTE
    and "MEDIUM RISK" in label
    and "DOWNLOADS LIVE DATABASE COPY" in label
]
fail += check(
    "visible medium-risk gate control remains calibrated",
    len(visible_medium_gate_controls) == 1,
    "count=" + str(len(visible_medium_gate_controls)),
)

unclassified = [route for route in EXPECTED_HIGH_RISK_ROUTES if route not in CLASSIFICATION_RULES]
invalid_classifications = [
    route + "=" + CLASSIFICATION_RULES.get(route, "")
    for route in EXPECTED_HIGH_RISK_ROUTES
    if CLASSIFICATION_RULES.get(route) not in ALLOWED_CLASSIFICATIONS
]

fail += check(
    "all hidden high-risk routes classified",
    not unclassified,
    "all classified" if not unclassified else ", ".join(unclassified),
)
fail += check(
    "classification vocabulary valid",
    not invalid_classifications,
    "valid" if not invalid_classifications else ", ".join(invalid_classifications),
)

print("")
print("HIDDEN HIGH-RISK EXPOSURE CLASSIFICATION MATRIX")
print("-" * 72)

classification_counts = defaultdict(int)
for route in EXPECTED_HIGH_RISK_ROUTES:
    route_info = route_map.get(route, {})
    classification = CLASSIFICATION_RULES.get(route, "UNCLASSIFIED")
    classification_counts[classification] += 1
    endpoint = route_info.get("endpoint", "MISSING")
    methods = route_info.get("methods", "MISSING")
    visibility = "VISIBLE_ON_ADMIN" if route in admin_link_map else "HIDDEN_OR_CONTEXTUAL"
    print(f"{classification} | {route} | {endpoint} | {methods} | {visibility}")

print("")
print("CLASSIFICATION SUMMARY")
print("-" * 72)
for key in sorted(classification_counts):
    print(f"{key}: {classification_counts[key]}")

status, err = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("hidden_high_risk_routes_reviewed:", len(EXPECTED_HIGH_RISK_ROUTES))
print("visible_hidden_high_risk_routes:", len(visible_high_risk))
print("visible_medium_gate_controls:", len(visible_medium_gate_controls))
print("classification_types:", dict(sorted(classification_counts.items())))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
