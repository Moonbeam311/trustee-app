from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
WORKSPACE_DIR = ROOT / "templates" / "ios_workspaces"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

REQUIRED_ADMIN_LINKS = [
    "/admin",
    "/admin/workspace/system",
    "/admin/workspace/governance",
    "/admin/workspace/administer",
    "/admin/workspace/archive",
    "/admin/workspace/developer",
]

WORKSPACE_FILES = [
    "system.html",
    "governance.html",
    "administer.html",
    "archive.html",
    "developer.html",
]

ANCHOR_LABELS = [
    "Operator Guidance",
    "Recommended Next Action",
    "Institutional Command Center",
    "Legacy Compatibility Center",
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

def links_from_text(text):
    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", text)
    return [h for h in hrefs if h.startswith("/") and not h.startswith("//")]

def static_route_matches(link, route_set):
    if link in route_set:
        return True

    for route in route_set:
        if "<" in route:
            prefix = route.split("<", 1)[0].rstrip("/")
            if prefix and link.startswith(prefix):
                return True

    return False

print("POST-V2-6 ADMIN WORKSPACE NAVIGATION COHERENCE AUDIT")
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

missing_admin_links = [x for x in REQUIRED_ADMIN_LINKS if x not in admin_text]
fail += check(
    "admin workspace links present",
    not missing_admin_links,
    "all present" if not missing_admin_links else ", ".join(missing_admin_links),
)

missing_anchor_labels = [x for x in ANCHOR_LABELS if x not in admin_text]
fail += check(
    "operator navigation anchor labels present",
    not missing_anchor_labels,
    "all present" if not missing_anchor_labels else ", ".join(missing_anchor_labels),
)

workspace_paths = [WORKSPACE_DIR / x for x in WORKSPACE_FILES]
missing_workspace_files = [str(x.relative_to(ROOT)) for x in workspace_paths if not x.exists()]
fail += check(
    "ios workspace templates present",
    not missing_workspace_files,
    "all present" if not missing_workspace_files else ", ".join(missing_workspace_files),
)

workspace_texts = {}
for path in workspace_paths:
    workspace_texts[path.name] = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

missing_back_to_admin = [
    name for name, txt in workspace_texts.items()
    if "/admin" not in txt and "admin_index" not in txt
]
fail += check(
    "workspace return paths to admin present",
    not missing_back_to_admin,
    "all present" if not missing_back_to_admin else ", ".join(missing_back_to_admin),
)

all_links = links_from_text(admin_text)
for txt in workspace_texts.values():
    all_links.extend(links_from_text(txt))

unique_links = sorted(set(all_links))
dead_static_links = [x for x in unique_links if not static_route_matches(x, route_set)]

fail += check(
    "static admin/workspace links resolve to known routes",
    not dead_static_links,
    "all resolved" if not dead_static_links else ", ".join(dead_static_links[:20]),
)

workspace_route_count = sum(1 for route in route_set if route.startswith("/admin/workspace"))
fail += check("workspace route family available", workspace_route_count >= 1, "count=" + str(workspace_route_count))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("NAVIGATION INVENTORY")
print("-" * 72)
print("routes_total:", len(routes))
print("workspace_route_count:", workspace_route_count)
print("template_static_links_reviewed:", len(unique_links))
print("dead_static_links:", dead_static_links)
print("workspace_files_reviewed:", [x.name for x in workspace_paths])

print("")
print("SUMMARY")
print("-" * 72)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
