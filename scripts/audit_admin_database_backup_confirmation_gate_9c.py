from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

BACKUP_ROUTE = "/admin/backup/database.zip"
BACKUP_ENDPOINT = "admin_database_backup_zip"

HIDDEN_HIGH_RISK_ROUTES = [
    "/users/<username>/reset_password",
    "/system/recovery/reseed-permissions",
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
        for next_line in lines[i + 1:i + 10]:
            ns = next_line.strip()
            if ns.startswith("def "):
                endpoint = ns.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append({"route": route, "endpoint": endpoint or "UNKNOWN_ENDPOINT"})

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


print("POST-V2-9C ADMIN DATABASE BACKUP CONFIRMATION GATE AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
admin_text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
confirm_text = CONFIRM_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if CONFIRM_TEMPLATE.exists() else ""

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("confirmation template readable", bool(confirm_text), str(CONFIRM_TEMPLATE))

routes = extract_routes(app_text)
route_map = {row["route"]: row["endpoint"] for row in routes}
admin_links = extract_admin_links(admin_text)
admin_link_map = {}
for href, label in admin_links:
    admin_link_map.setdefault(href, []).append(label)

fail += check(
    "backup ZIP route retained",
    BACKUP_ROUTE in route_map,
    "present" if BACKUP_ROUTE in route_map else "missing",
)
fail += check(
    "backup ZIP endpoint retained",
    route_map.get(BACKUP_ROUTE) == BACKUP_ENDPOINT,
    route_map.get(BACKUP_ROUTE, "missing"),
)

backup_labels = admin_link_map.get(BACKUP_ROUTE, [])
backup_label_text = " ".join(backup_labels)
fail += check(
    "admin backup ZIP link retained",
    bool(backup_labels),
    backup_label_text or "missing",
)
fail += check(
    "admin warning label retained",
    "MEDIUM RISK" in backup_label_text and "DOWNLOADS LIVE DATABASE COPY" in backup_label_text,
    backup_label_text or "missing",
)

route_start = app_text.find("def " + BACKUP_ENDPOINT)
next_route = app_text.find("\n@app.route(", route_start + 1) if route_start >= 0 else -1
route_body = app_text[route_start: next_route if next_route > route_start else len(app_text)]

fail += check(
    "confirmation gate exists for backup ZIP route",
    "admin_backup_database_confirm.html" in route_body and "confirmed" in route_body,
    "present" if "admin_backup_database_confirm.html" in route_body else "missing",
)
fail += check(
    "confirmation uses explicit confirmed=1",
    'request.args.get("confirmed") != "1"' in route_body
    or "request.args.get('confirmed') != '1'" in route_body,
    "confirmed=1 required" if "confirmed" in route_body else "missing",
)
fail += check(
    "existing ZIP behavior preserved after confirmation",
    "zipfile.ZipFile" in route_body
    and "send_file" in route_body
    and "database_backup_zip_downloaded" in route_body,
    "zip generation and send_file retained",
)

confirm_required = [
    "Confirm Database Backup Download",
    "MEDIUM RISK",
    "DOWNLOADS LIVE DATABASE COPY",
    "downloads a live copy of the application database",
    "url_for('admin_database_backup_zip', confirmed=1)",
    "url_for('admin_index')",
]
missing_confirm = [item for item in confirm_required if item not in confirm_text]
fail += check(
    "confirmation page required content present",
    not missing_confirm,
    "all present" if not missing_confirm else ", ".join(missing_confirm),
)

visible_hidden_routes = [
    route
    for route in HIDDEN_HIGH_RISK_ROUTES
    if route in admin_link_map
]
fail += check(
    "hidden high-risk controls not exposed as admin links",
    not visible_hidden_routes,
    "none" if not visible_hidden_routes else ", ".join(visible_hidden_routes),
)

missing_hidden_routes = [route for route in HIDDEN_HIGH_RISK_ROUTES if route not in route_map]
fail += check(
    "hidden high-risk routes retained",
    not missing_hidden_routes,
    "all present" if not missing_hidden_routes else ", ".join(missing_hidden_routes),
)

status, err = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check(
    "runtime database not modified",
    not bad_db,
    "none" if not bad_db else "\n".join(bad_db),
)

print("")
print("CONFIRMATION GATE SUMMARY")
print("-" * 72)
print("backup_route:", BACKUP_ROUTE)
print("backup_endpoint:", route_map.get(BACKUP_ROUTE, "missing"))
print("admin_labels:", len(backup_labels))
print("hidden_high_risk_routes_reviewed:", len(HIDDEN_HIGH_RISK_ROUTES))
print("hidden_high_risk_admin_links:", len(visible_hidden_routes))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
