from collections import defaultdict
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
BACKUP_CONFIRM_TEMPLATE = ROOT / "templates" / "admin_backup_database_confirm.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_TAG_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

BACKUP_ROUTE = "/admin/backup/database.zip"
BACKUP_ENDPOINT = "admin_database_backup_zip"
BACKUP_CONFIRM_TITLE = "Confirm Database Backup Download"

EXPECTED_AUDIT_SCRIPTS = [
    "scripts/audit_admin_system_control_risk_tier_9.py",
    "scripts/audit_admin_system_control_warning_label_9a.py",
    "scripts/audit_admin_system_control_confirmation_gate_9b.py",
    "scripts/audit_admin_database_backup_confirmation_gate_9c.py",
    "scripts/audit_admin_hidden_high_risk_exposure_9d.py",
]

EXPECTED_HIDDEN_HIGH_RISK_ROUTES = [
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

EXPECTED_CLASSIFICATION_TOTALS = {
    "KEEP_HIDDEN_CONTEXTUAL": 3,
    "REQUIRE_CONFIRMATION_BEFORE_EXPOSURE": 2,
    "PROTECTED_RECOVERY_SURFACE_CANDIDATE": 6,
    "DEPRECATION_REVIEW_ONLY": 7,
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


def parse_9d_classification_totals(script_text):
    totals = defaultdict(int)
    marker = "CLASSIFICATION_RULES = {"
    start = script_text.find(marker)
    if start == -1:
        return totals

    end = script_text.find("\n}\n", start)
    if end == -1:
        return totals

    block = script_text[start:end]
    for classification in EXPECTED_CLASSIFICATION_TOTALS:
        totals[classification] = block.count('"' + classification + '"')
    return totals


print("POST-V2-9E ADMIN SYSTEM CONTROL FINAL CLOSURE CERTIFICATION")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified V2 tag protected", tag == EXPECTED_TAG_COMMIT, tag or err)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
admin_text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
backup_confirm_text = (
    BACKUP_CONFIRM_TEMPLATE.read_text(encoding="utf-8", errors="ignore")
    if BACKUP_CONFIRM_TEMPLATE.exists()
    else ""
)

fail += check("app.py readable", bool(app_text), str(APP))
fail += check("admin template readable", bool(admin_text), str(ADMIN_TEMPLATE))
fail += check("backup confirmation template readable", bool(backup_confirm_text), str(BACKUP_CONFIRM_TEMPLATE))

routes = extract_routes(app_text)
route_map = {row["route"]: row for row in routes}
endpoint_routes = defaultdict(list)
for route in routes:
    endpoint_routes[route["endpoint"]].append(route["route"])

admin_links = extract_admin_links(admin_text)
admin_link_map = defaultdict(list)
for href, label in admin_links:
    admin_link_map[href].append(label)

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

missing_audit_scripts = [script for script in EXPECTED_AUDIT_SCRIPTS if not (ROOT / script).exists()]
fail += check(
    "POST-V2-9 series audit scripts present",
    not missing_audit_scripts,
    "all present" if not missing_audit_scripts else ", ".join(missing_audit_scripts),
)

fail += check(
    "backup ZIP route retained",
    BACKUP_ROUTE in route_map,
    "present" if BACKUP_ROUTE in route_map else "missing",
)
fail += check(
    "backup ZIP endpoint retained",
    BACKUP_ENDPOINT in endpoint_routes,
    "present" if BACKUP_ENDPOINT in endpoint_routes else "missing",
)
fail += check(
    "backup warning label retained",
    "MEDIUM RISK" in admin_text and "DOWNLOADS LIVE DATABASE COPY" in admin_text,
    "present" if "MEDIUM RISK" in admin_text and "DOWNLOADS LIVE DATABASE COPY" in admin_text else "missing",
)

confirm_requirements = {
    BACKUP_CONFIRM_TITLE: BACKUP_CONFIRM_TITLE in backup_confirm_text,
    "MEDIUM RISK": "MEDIUM RISK" in backup_confirm_text,
    "DOWNLOADS LIVE DATABASE COPY": "DOWNLOADS LIVE DATABASE COPY" in backup_confirm_text,
    "live copy of the application database": "live copy of the application database" in backup_confirm_text,
    BACKUP_ROUTE + "?confirmed=1": (
        BACKUP_ROUTE + "?confirmed=1" in backup_confirm_text
        or "url_for('admin_database_backup_zip', confirmed=1)" in backup_confirm_text
    ),
    "/admin": "/admin" in backup_confirm_text or "url_for('admin_index')" in backup_confirm_text,
}
missing_confirm_text = [name for name, ok in confirm_requirements.items() if not ok]
fail += check(
    "backup confirmation template content complete",
    not missing_confirm_text,
    "complete" if not missing_confirm_text else ", ".join(missing_confirm_text),
)

visible_backup_controls = [
    (href, label)
    for href, label in admin_links
    if href == BACKUP_ROUTE and "MEDIUM RISK" in label and "DOWNLOADS LIVE DATABASE COPY" in label
]
fail += check(
    "exactly one visible medium-risk backup control",
    len(visible_backup_controls) == 1,
    "count=" + str(len(visible_backup_controls)),
)

visible_hidden_high_risk = {
    route: admin_link_map[route]
    for route in EXPECTED_HIDDEN_HIGH_RISK_ROUTES
    if route in admin_link_map
}
fail += check(
    "hidden high-risk controls remain hidden from Admin",
    not visible_hidden_high_risk,
    "none" if not visible_hidden_high_risk else str(visible_hidden_high_risk),
)

missing_hidden_routes = [route for route in EXPECTED_HIDDEN_HIGH_RISK_ROUTES if route not in route_map]
fail += check(
    "hidden high-risk routes retained for controlled governance",
    not missing_hidden_routes,
    "all present" if not missing_hidden_routes else ", ".join(missing_hidden_routes),
)

nine_d_path = ROOT / "scripts" / "audit_admin_hidden_high_risk_exposure_9d.py"
nine_d_text = nine_d_path.read_text(encoding="utf-8", errors="ignore") if nine_d_path.exists() else ""
classification_totals = parse_9d_classification_totals(nine_d_text)

classification_mismatch = []
for key, expected_count in EXPECTED_CLASSIFICATION_TOTALS.items():
    actual = classification_totals.get(key, 0)
    if actual != expected_count:
        classification_mismatch.append(f"{key}: expected {expected_count}, actual {actual}")

fail += check(
    "9D classification totals retained",
    not classification_mismatch,
    "retained" if not classification_mismatch else "; ".join(classification_mismatch),
)

print("")
print("POST-V2-9 SERIES AUDIT SCRIPT STATUS")
print("-" * 72)
for script in EXPECTED_AUDIT_SCRIPTS:
    path = ROOT / script
    if not path.exists():
        print("MISSING | " + script)
        continue

    code, stdout, stderr = run_script(script)
    result = "PASS" if code == 0 and "RESULT: PASS" in stdout else "FAIL"
    print(result + " | " + script)
    if result != "PASS":
        fail += 1

print("")
print("SYSTEM CONTROL FINAL POSTURE")
print("-" * 72)
print("visible_medium_risk_backup_controls:", len(visible_backup_controls))
print("visible_hidden_high_risk_controls:", len(visible_hidden_high_risk))
print("hidden_high_risk_routes_retained:", len(EXPECTED_HIDDEN_HIGH_RISK_ROUTES) - len(missing_hidden_routes))
print("backup_confirmation_template:", "present" if BACKUP_CONFIRM_TEMPLATE.exists() else "missing")

print("")
print("9D CLASSIFICATION TOTALS")
print("-" * 72)
for key in sorted(EXPECTED_CLASSIFICATION_TOTALS):
    print(f"{key}: {classification_totals.get(key, 0)}")

status, err = git(["status", "--short"])
bad_db = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("post_v2_9_audits_reviewed:", len(EXPECTED_AUDIT_SCRIPTS))
print("visible_medium_risk_backup_controls:", len(visible_backup_controls))
print("visible_hidden_high_risk_controls:", len(visible_hidden_high_risk))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
