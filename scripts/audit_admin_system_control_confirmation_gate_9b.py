from pathlib import Path
import re
import subprocess
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

VISIBLE_MEDIUM_RISK_CONTROL = "/admin/backup/database.zip"
VISIBLE_WARNING = "MEDIUM RISK — DOWNLOADS LIVE DATABASE COPY"

CONFIRMATION_REQUIRED_TERMS = [
    "reset",
    "bootstrap",
    "repair",
    "migration",
    "hosted",
    "seed",
    "reseed",
    "clear-login-lockout",
]

WARNING_GATE_CANDIDATE_TERMS = [
    "backup",
    "database",
    "export-policy",
    "toggle",
]

EXPECTED_CONFIRMATION_CANDIDATES = [
    "/admin/seed-hosted-baseline",
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
]

EXPECTED_WARNING_CANDIDATES = [
    "/admin/backup/database.zip",
    "/admin/backup/database",
    "/admin/export-policy/toggle",
    "/admin/storage-diagnostics",
]

FORBIDDEN_IMPLEMENTATION_MARKERS = [
    "POST-V2-9B CONFIRMATION GATE IMPLEMENTATION",
    "data-confirmation-gate",
    "admin-confirmation-gate",
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
        methods = ""
        method_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", decorator_text)
        if method_match:
            methods = method_match.group(1).replace('"', '').replace("'", "").strip()

        for next_line in lines[i + 1:i + 10]:
            ns = next_line.strip()
            if ns.startswith("def "):
                endpoint = ns.split("def ", 1)[1].split("(", 1)[0].strip()
                break

        routes.append({
            "route": route,
            "endpoint": endpoint or "UNKNOWN_ENDPOINT",
            "methods": methods or "GET_DEFAULT",
        })

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

def gate_tier(route, endpoint):
    hay = (route + " " + endpoint).lower()

    if any(term in hay for term in CONFIRMATION_REQUIRED_TERMS):
        return "FUTURE_CONFIRMATION_GATE_REQUIRED"

    if any(term in hay for term in WARNING_GATE_CANDIDATE_TERMS):
        return "WARNING_LABEL_NOW_CONFIRMATION_GATE_REVIEW"

    return "NO_GATE_RECOMMENDED"

print("POST-V2-9B ADMIN SYSTEM CONTROL CONFIRMATION GATE AUDIT")
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
route_set = {r["route"] for r in routes}
endpoint_by_route = {r["route"]: r["endpoint"] for r in routes}

admin_links = extract_admin_links(admin_text)
admin_link_map = defaultdict(list)
for href, label in admin_links:
    admin_link_map[href].append(label)

fail += check("route inventory available", len(routes) >= 100, "count=" + str(len(routes)))
fail += check("admin link inventory available", len(admin_links) >= 20, "count=" + str(len(admin_links)))

fail += check(
    "visible database backup route retained",
    VISIBLE_MEDIUM_RISK_CONTROL in admin_text,
    "present" if VISIBLE_MEDIUM_RISK_CONTROL in admin_text else "missing",
)

fail += check(
    "visible database backup warning retained",
    VISIBLE_WARNING in admin_text,
    "present" if VISIBLE_WARNING in admin_text else "missing",
)

missing_confirm = [x for x in EXPECTED_CONFIRMATION_CANDIDATES if x not in route_set]
missing_warning = [x for x in EXPECTED_WARNING_CANDIDATES if x not in route_set]

fail += check(
    "expected future confirmation candidates inventoried",
    not missing_confirm,
    "all present" if not missing_confirm else ", ".join(missing_confirm),
)

fail += check(
    "expected warning/gate review candidates inventoried",
    not missing_warning,
    "all present" if not missing_warning else ", ".join(missing_warning),
)

gate_rows = []
for r in routes:
    tier = gate_tier(r["route"], r["endpoint"])
    if tier == "NO_GATE_RECOMMENDED":
        continue

    labels = admin_link_map.get(r["route"], [])
    visible = "VISIBLE_ON_ADMIN" if labels else "HIDDEN_OR_CONTEXTUAL"
    gate_rows.append({
        "tier": tier,
        "route": r["route"],
        "endpoint": r["endpoint"],
        "methods": r["methods"],
        "visibility": visible,
        "labels": labels,
    })

confirmation_rows = [x for x in gate_rows if x["tier"] == "FUTURE_CONFIRMATION_GATE_REQUIRED"]
warning_rows = [x for x in gate_rows if x["tier"] == "WARNING_LABEL_NOW_CONFIRMATION_GATE_REVIEW"]
visible_rows = [x for x in gate_rows if x["visibility"] == "VISIBLE_ON_ADMIN"]

fail += check("future confirmation candidates available", len(confirmation_rows) >= 10, "count=" + str(len(confirmation_rows)))
fail += check("warning/gate review candidates available", len(warning_rows) >= 3, "count=" + str(len(warning_rows)))
fail += check("visible gate review controls identified", len(visible_rows) >= 1, "count=" + str(len(visible_rows)))

unexpected_implemented = []
combined_text = app_text + "\n" + admin_text
for marker in FORBIDDEN_IMPLEMENTATION_MARKERS:
    if marker in combined_text:
        unexpected_implemented.append(marker)

fail += check(
    "confirmation gate not implemented yet",
    not unexpected_implemented,
    "none" if not unexpected_implemented else ", ".join(unexpected_implemented),
)

print("")
print("CONFIRMATION GATE DECISION RULES")
print("-" * 72)
print("HIGH RISK: future confirmation gate required before execution.")
print("MEDIUM RISK: warning label now; confirmation gate review before expanding visibility.")
print("VISIBLE MEDIUM RISK: preserve link but label clearly until gate patch is approved.")
print("HIDDEN HIGH RISK: keep hidden/contextual; gate before promoting to Admin surface.")

print("")
print("CONFIRMATION GATE CANDIDATE MATRIX")
print("-" * 72)

for tier_name in [
    "FUTURE_CONFIRMATION_GATE_REQUIRED",
    "WARNING_LABEL_NOW_CONFIRMATION_GATE_REVIEW",
]:
    print("")
    print(tier_name)
    for row in gate_rows:
        if row["tier"] != tier_name:
            continue
        label_text = ", ".join(row["labels"]) if row["labels"] else "[not directly visible on Admin]"
        print(
            "  "
            + row["route"]
            + " | "
            + row["endpoint"]
            + " | "
            + row["methods"]
            + " | "
            + row["visibility"]
            + " | "
            + label_text
        )

print("")
print("VISIBLE CONTROLS REQUIRING GATE REVIEW")
print("-" * 72)
for row in visible_rows:
    print(row["tier"] + " | " + row["route"] + " | " + ", ".join(row["labels"]))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("routes_total:", len(routes))
print("admin_links_reviewed:", len(admin_links))
print("gate_candidates_reviewed:", len(gate_rows))
print("future_confirmation_gate_required:", len(confirmation_rows))
print("warning_label_now_confirmation_gate_review:", len(warning_rows))
print("visible_controls_requiring_gate_review:", len(visible_rows))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
