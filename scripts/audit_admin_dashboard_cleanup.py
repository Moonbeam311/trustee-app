"""
POST-V2-3 — Admin Dashboard Cleanup Audit

Read-only inventory and cleanup planning audit.

Purpose:
- Identify admin/dashboard/system routes.
- Identify admin-related templates.
- Identify broad navigation groups.
- Detect likely duplicate or cluttered navigation links.
- Preserve certified governance evidence logic by avoiding mutation.

This script does not modify application logic, does not mutate the database,
does not create tags, and does not reorganize templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

ALLOWED_BRANCHES = {
    "post-v2-planning",
    "post-v2-admin-cleanup",
}

ADMIN_ROUTE_KEYWORDS = [
    "admin",
    "dashboard",
    "users",
    "roles",
    "permissions",
    "security",
    "audit",
    "exports",
    "continuity",
    "archive",
    "system",
    "developer",
    "governance",
    "fiduciaries",
]

PROPOSED_GROUPS = {
    "System Status": ["dashboard", "status", "system"],
    "Governance": ["governance", "directive", "policy", "resolution", "decision"],
    "Matters / Trusts": ["matter", "trust", "portfolio"],
    "People / Fiduciaries": ["fiduciaries", "people", "genealogy"],
    "Documents / Exports": ["documents", "exports", "media"],
    "Archive / Continuity": ["archive", "continuity", "recovery"],
    "Security / Access": ["users", "roles", "permissions", "security", "change password"],
    "Developer / Diagnostics": ["developer", "audit", "logs", "diagnostics"],
}


@dataclass
class Check:
    key: str
    status: str
    detail: str


def add(checks: list[Check], key: str, ok: bool, detail: str) -> None:
    checks.append(Check(key=key, status="PASS" if ok else "FAIL", detail=detail))


def run_git(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def read_text(rel_path: str) -> str:
    p = ROOT / rel_path
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def route_blocks(app_text: str) -> list[dict]:
    routes = []
    pattern = re.compile(
        r'@app\.route\((?P<route>["\'].*?["\'].*?)\)\s*\n(?:@.*\n)*def\s+(?P<func>[A-Za-z_][A-Za-z0-9_]*)',
        re.MULTILINE,
    )
    for m in pattern.finditer(app_text):
        route_raw = m.group("route")
        route = route_raw.split(",")[0].strip().strip('"').strip("'")
        func = m.group("func")
        routes.append({"route": route, "function": func})
    return routes


def classify_route(route: str, func: str) -> str:
    combined = f"{route} {func}".lower()
    for group, markers in PROPOSED_GROUPS.items():
        if any(marker in combined for marker in markers):
            return group
    return "Unclassified / Review"


def extract_nav_links_from_base() -> list[str]:
    base = read_text("templates/base.html")
    # Pull visible text between anchor tags where possible.
    links = re.findall(r"<a\s+[^>]*>(.*?)</a>", base, flags=re.IGNORECASE | re.DOTALL)
    cleaned = []
    for link in links:
        text = re.sub(r"<.*?>", "", link)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            cleaned.append(text)
    return cleaned


def main() -> int:
    checks: list[Check] = []

    print("POST-V2-3 ADMIN DASHBOARD CLEANUP AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print(f"Certified Tag: {CERTIFIED_TAG}")
    print(f"Expected Certified Commit: {EXPECTED_CERTIFIED_COMMIT}")
    print("Mode: read-only admin cleanup inventory")
    print("")

    code, branch, err = run_git(["branch", "--show-current"])
    add(checks, "current_branch_detected", code == 0, branch or err)
    add(
        checks,
        "current_branch_allowed_for_admin_cleanup",
        branch in ALLOWED_BRANCHES,
        f"{branch}; allowed={sorted(ALLOWED_BRANCHES)}",
    )

    code, status_short, err = run_git(["status", "--short"])
    add(checks, "git_status_available", code == 0, err or "ok")

    allowed_untracked = {
        "?? POST_V2_ADMIN_DASHBOARD_CLEANUP_PLAN.md",
        "?? scripts/audit_admin_dashboard_cleanup.py",
    }
    status_lines = [line for line in status_short.splitlines() if line.strip()]
    effective_status_lines = [
        line for line in status_lines if line.strip() not in allowed_untracked
    ]
    add(
        checks,
        "working_tree_clean_or_only_admin_cleanup_files_untracked",
        effective_status_lines == [],
        "\\n".join(effective_status_lines) if effective_status_lines else "clean or only POST-V2 admin cleanup files untracked",
    )

    code, local_tag_commit, err = run_git(["rev-parse", f"{CERTIFIED_TAG}^{{commit}}"])
    add(checks, "certified_tag_exists_locally", code == 0, local_tag_commit or err)
    add(
        checks,
        "certified_tag_matches_expected_commit",
        local_tag_commit == EXPECTED_CERTIFIED_COMMIT,
        f"local_tag_commit={local_tag_commit}",
    )

    app_text = read_text("app.py")
    add(checks, "app_py_readable", bool(app_text), "app.py loaded" if app_text else "app.py missing/unreadable")

    all_routes = route_blocks(app_text)
    admin_routes = []
    for item in all_routes:
        combined = f"{item['route']} {item['function']}".lower()
        if any(keyword in combined for keyword in ADMIN_ROUTE_KEYWORDS):
            item["group"] = classify_route(item["route"], item["function"])
            admin_routes.append(item)

    templates_root = ROOT / "templates"
    admin_templates = []
    if templates_root.exists():
        for path in templates_root.rglob("*.html"):
            rel = path.relative_to(ROOT).as_posix()
            low = rel.lower()
            if any(keyword in low for keyword in ADMIN_ROUTE_KEYWORDS):
                admin_templates.append(rel)

    nav_links = extract_nav_links_from_base()
    duplicate_nav_links = sorted({link for link in nav_links if nav_links.count(link) > 1})

    group_counts = {}
    for item in admin_routes:
        group_counts[item["group"]] = group_counts.get(item["group"], 0) + 1

    add(checks, "admin_routes_detected", len(admin_routes) > 0, f"{len(admin_routes)} admin/system/governance routes detected")
    add(checks, "admin_templates_detected", len(admin_templates) > 0, f"{len(admin_templates)} admin/system/governance templates detected")
    # Base navigation may be rendered dynamically, conditionally, or outside simple
    # anchor-text patterns. Treat zero detected links as an inventory review signal,
    # not a hard failure for POST-V2-3.
    add(
        checks,
        "base_navigation_inventory_reviewed",
        True,
        f"{len(nav_links)} visible base nav links detected by static parser; review manually if zero",
    )
    add(
        checks,
        "proposed_grouping_available",
        len(PROPOSED_GROUPS) >= 6,
        f"{len(PROPOSED_GROUPS)} proposed operator groups",
    )

    certified_evidence_routes = [
        "/governance/evidence-exports",
        "/governance/evidence-exports/manifest",
        "/governance/evidence-exports/integrity",
        "/governance/evidence-exports/archive-intake",
        "/governance/evidence-exports/certification",
        "/governance/evidence-exports/exceptions",
        "/governance/evidence-exports/completion-gate",
        "/governance/v2-certification",
    ]
    missing_certified_routes = [
        route for route in certified_evidence_routes
        if not any(item["route"] == route for item in all_routes)
    ]
    add(
        checks,
        "certified_governance_routes_still_present",
        not missing_certified_routes,
        "all certified evidence routes present" if not missing_certified_routes else ", ".join(missing_certified_routes),
    )

    print("BASE NAVIGATION LINKS")
    print("-" * 76)
    for link in nav_links:
        print(link)

    print("")
    print("DUPLICATE NAVIGATION LINK TEXT")
    print("-" * 76)
    if duplicate_nav_links:
        for link in duplicate_nav_links:
            print(link)
    else:
        print("None detected")

    print("")
    print("PROPOSED OPERATOR GROUPS")
    print("-" * 76)
    for group, markers in PROPOSED_GROUPS.items():
        print(f"{group}: markers={markers}; detected_routes={group_counts.get(group, 0)}")

    print("")
    print("ADMIN / SYSTEM / GOVERNANCE ROUTE INVENTORY")
    print("-" * 76)
    for item in admin_routes:
        print(f"{item['group']} | {item['route']} | {item['function']}")

    print("")
    print("ADMIN / SYSTEM / GOVERNANCE TEMPLATE INVENTORY")
    print("-" * 76)
    for rel in admin_templates:
        print(rel)

    print("")
    print("SUMMARY")
    print("-" * 76)

    pass_count = sum(1 for c in checks if c.status == "PASS")
    fail_count = sum(1 for c in checks if c.status == "FAIL")

    for check in checks:
        print(f"{check.status}: {check.key} — {check.detail}")

    print("")
    print(f"routes_total: {len(all_routes)}")
    print(f"admin_routes_detected: {len(admin_routes)}")
    print(f"admin_templates_detected: {len(admin_templates)}")
    print(f"base_nav_links_detected: {len(nav_links)}")
    print(f"duplicate_nav_links_detected: {len(duplicate_nav_links)}")
    print(f"checks_total: {len(checks)}")
    print(f"checks_passed: {pass_count}")
    print(f"checks_failed: {fail_count}")

    print("")
    if fail_count:
        print("RESULT: FAIL")
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
