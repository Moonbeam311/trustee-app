"""
V2-HARDEN-2 — Governance Evidence Permission / Access Review

Script-only hardening audit.

Purpose:
- Verify governance evidence HTML routes are protected by require_master_admin().
- Verify governance evidence TXT export routes are protected by require_master_admin().
- Verify governance evidence CSV export route is protected by require_master_admin().
- Verify route handlers do not return evidence content before the gate check.
- Verify route handlers use the expected admin gate pattern:
    gate = require_master_admin()
    if gate:
        return gate

This script does not import Flask, does not open the database, does not mutate records,
does not create certification records, and does not tag Version 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


@dataclass
class RouteSpec:
    route: str
    expected_function: str | None = None
    route_type: str = "html"


@dataclass
class Check:
    key: str
    status: str
    detail: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def add(checks: list[Check], key: str, ok: bool, detail: str) -> None:
    checks.append(Check(key=key, status="PASS" if ok else "FAIL", detail=detail))


def find_route_function(app_text: str, route: str) -> tuple[str | None, str]:
    """
    Return (function_name, function_body_block) for a Flask @app.route block.
    """
    escaped = re.escape(route)
    pattern = (
        rf"@app\.route\([\"']{escaped}[\"']\)\s*\n"
        rf"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\):"
    )
    match = re.search(pattern, app_text)
    if not match:
        return None, ""

    fn_name = match.group(1)
    start = match.start()

    # Capture until the next app route or end of file.
    next_match = re.search(r"\n@app\.route\(", app_text[match.end():])
    if next_match:
        end = match.end() + next_match.start()
    else:
        end = len(app_text)

    return fn_name, app_text[start:end]


def has_gate_pattern(block: str) -> bool:
    return (
        "require_master_admin()" in block
        and re.search(r"\bgate\s*=\s*require_master_admin\(\)", block) is not None
        and re.search(r"if\s+gate\s*:\s*\n\s*return\s+gate", block) is not None
    )


def route_body_only(block: str) -> str:
    """
    Return only the executable function body after the def line.

    The route decorator and function name may contain words like export/csv before
    the gate appears. Those should not count as pre-gate content.
    """
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("def "):
            return "\n".join(lines[i + 1 :])
    return block


def gate_appears_before_content(block: str) -> bool:
    body = route_body_only(block)

    gate_pos = body.find("require_master_admin()")
    if gate_pos == -1:
        return False

    content_markers = [
        "render_template(",
        "Response(",
        "send_file(",
        "send_from_directory(",
        "make_response(",
        "jsonify(",
        "build_governance_",
        "build_governance_export_",
        "build_governance_evidence_",
    ]

    positions = [
        body.find(marker)
        for marker in content_markers
        if body.find(marker) != -1
    ]

    if not positions:
        return True

    return gate_pos < min(positions)


def main() -> int:
    checks: list[Check] = []

    print("V2-HARDEN-2 GOVERNANCE EVIDENCE ACCESS CONTROL AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print("Mode: read-only script audit")
    print("")

    add(checks, "app_py_exists", APP.exists(), str(APP))
    if not APP.exists():
        for check in checks:
            print(f"{check.status}: {check.key} — {check.detail}")
        return 1

    app_text = read(APP)

    route_specs = [
        RouteSpec("/governance/evidence-exports", "governance_evidence_export_index", "html"),
        RouteSpec("/governance/evidence-exports.csv", None, "csv"),
        RouteSpec("/governance/evidence-exports/manifest", "governance_evidence_export_manifest", "html"),
        RouteSpec("/governance/evidence-exports/manifest.txt", "governance_evidence_export_manifest_text", "txt"),
        RouteSpec("/governance/evidence-exports/integrity", "governance_export_integrity_digest", "html"),
        RouteSpec("/governance/evidence-exports/integrity.txt", "governance_export_integrity_digest_text", "txt"),
        RouteSpec("/governance/evidence-exports/archive-intake", "governance_export_archive_intake_preview", "html"),
        RouteSpec("/governance/evidence-exports/archive-intake.txt", "governance_export_archive_intake_preview_text", "txt"),
        RouteSpec("/governance/evidence-exports/certification", "governance_evidence_certification_dashboard", "html"),
        RouteSpec("/governance/evidence-exports/certification.txt", "governance_evidence_certification_dashboard_text", "txt"),
        RouteSpec("/governance/evidence-exports/exceptions", "governance_evidence_exception_panel", "html"),
        RouteSpec("/governance/evidence-exports/exceptions.txt", "governance_evidence_exception_panel_text", "txt"),
        RouteSpec("/governance/evidence-exports/completion-gate", "governance_evidence_completion_gate", "html"),
        RouteSpec("/governance/evidence-exports/completion-gate.txt", "governance_evidence_completion_gate_text", "txt"),
    ]

    print("ROUTE ACCESS INVENTORY")
    print("-" * 76)

    discovered_functions: dict[str, str] = {}

    for spec in route_specs:
        fn_name, block = find_route_function(app_text, spec.route)
        discovered_functions[spec.route] = fn_name or "-"

        add(checks, f"route_exists:{spec.route}", fn_name is not None, spec.route)

        if spec.expected_function:
            add(
                checks,
                f"route_function_expected:{spec.route}",
                fn_name == spec.expected_function,
                f"expected={spec.expected_function}, actual={fn_name}",
            )
        else:
            add(
                checks,
                f"route_function_detected:{spec.route}",
                fn_name is not None,
                f"actual={fn_name}",
            )

        add(
            checks,
            f"route_has_master_admin_gate:{spec.route}",
            has_gate_pattern(block),
            f"{spec.route} -> {fn_name}",
        )

        add(
            checks,
            f"gate_before_content:{spec.route}",
            gate_appears_before_content(block),
            f"{spec.route} -> {fn_name}",
        )

        if spec.route_type in {"txt", "csv"}:
            add(
                checks,
                f"export_route_protected:{spec.route}",
                has_gate_pattern(block) and gate_appears_before_content(block),
                f"{spec.route} ({spec.route_type}) -> {fn_name}",
            )

    print("")
    print("DISCOVERED FUNCTIONS")
    print("-" * 76)
    for route, fn in discovered_functions.items():
        print(f"{route}: {fn}")

    print("")
    print("SUMMARY")
    print("-" * 76)

    pass_count = sum(1 for c in checks if c.status == "PASS")
    fail_count = sum(1 for c in checks if c.status == "FAIL")

    for check in checks:
        print(f"{check.status}: {check.key} — {check.detail}")

    print("")
    print(f"checks_total: {len(checks)}")
    print(f"checks_passed: {pass_count}")
    print(f"checks_failed: {fail_count}")

    if fail_count:
        print("")
        print("RESULT: FAIL")
        return 1

    print("")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
