from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

GROUPS = {
    "Security / Access": ["bootstrap_admin", "reset_admin", "repair_admin_access", "reseed_permissions", "hosted_reseed", "permissions", "roles", "users", "security"],
    "Developer / Diagnostics": ["diag", "diagnostic", "storage", "repair", "migration", "run_hosted", "certificate_event_bus"],
    "System Status": ["backup", "seed_hosted", "hosted_bootstrap", "system", "status", "health", "certificate_api", "certificate_interface", "certificate_object_model"],
    "Documents / Exports": ["document", "draft", "approval", "articles", "forms", "certificate_packet", "certificate_registry", "unified_certificate"],
    "Governance": ["governance", "policy", "certificate_policies", "certificate_types"],
    "Archive / Continuity": ["archive", "continuity", "final_archive"],
}

def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

def classify(endpoint, route):
    hay = (endpoint + " " + route).lower()
    for group, markers in GROUPS.items():
        if any(m in hay for m in markers):
            return group
    return "Unclassified / Review"

text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
routes = []
pattern = re.compile(r"@app\\.route\\(([^\\n]+)\\)\\s*\\ndef\\s+([a-zA-Z0-9_]+)\\(", re.MULTILINE)
for match in pattern.finditer(text):
    raw_route = match.group(1)
    endpoint = match.group(2)
    route_match = re.search(r"[\"']([^\"']+)[\"']", raw_route)
    route = route_match.group(1) if route_match else raw_route
    if "/admin" in route or "admin" in endpoint or "bootstrap" in endpoint or "certificate" in endpoint:
        routes.append((route, endpoint, classify(endpoint, route)))

unclassified = [(r, e, g) for r, e, g in routes if g == "Unclassified / Review"]
classified = [(r, e, g) for r, e, g in routes if g != "Unclassified / Review"]

fail = 0
print("POST-V2-4 ADMIN ROUTE CLASSIFICATION AUDIT")
print("=" * 72)
branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)
fail += check("app.py readable", bool(text), str(APP))
fail += check("admin route inventory detected", len(routes) >= 25, "count=" + str(len(routes)))

print("")
print("CLASSIFIED ADMIN ROUTES")
print("-" * 72)
for route, endpoint, group in sorted(classified, key=lambda x: (x[2], x[0], x[1])):
    print(group + " | " + route + " | " + endpoint)

print("")
print("REMAINING UNCLASSIFIED / REVIEW")
print("-" * 72)
if unclassified:
    for route, endpoint, group in sorted(unclassified):
        print(group + " | " + route + " | " + endpoint)
else:
    print("None")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("admin_routes_reviewed:", len(routes))
print("classified_routes:", len(classified))
print("remaining_unclassified:", len(unclassified))
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
