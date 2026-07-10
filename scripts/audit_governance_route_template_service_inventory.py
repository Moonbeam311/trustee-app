"""
V2-HARDEN-1 — Governance Route / Template / Service Inventory Audit

Script-only hardening audit.

Purpose:
- Verify governance evidence routes exist in app.py.
- Verify route handler functions exist.
- Verify route handlers reference expected service builders and templates.
- Verify service builders exist in services/services_governance.py.
- Verify governance evidence templates exist.
- Verify HTML templates extend base.html.
- Verify HTML templates do not directly duplicate institutional custody/footer text.
- Verify Evidence Export Index links reference expected endpoint names.
- Verify TXT export builders preserve custody notice output in service text builders.

This script does not import the Flask app, does not open the database, does not mutate records,
does not create certification records, and does not tag Version 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SERVICES = ROOT / "services" / "services_governance.py"
TEMPLATE_DIR = ROOT / "templates" / "governance"


@dataclass
class Check:
    key: str
    status: str
    detail: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def add(checks: list[Check], key: str, ok: bool, detail: str) -> None:
    checks.append(Check(key=key, status="PASS" if ok else "FAIL", detail=detail))


def route_exists(app_text: str, route: str) -> bool:
    return f'@app.route("{route}")' in app_text or f"@app.route('{route}')" in app_text


def function_exists(text: str, fn_name: str) -> bool:
    return re.search(rf"^def\s+{re.escape(fn_name)}\s*\(", text, re.MULTILINE) is not None


def endpoint_link_exists(template_text: str, endpoint: str) -> bool:
    return f"url_for('{endpoint}'" in template_text or f'url_for("{endpoint}"' in template_text


def main() -> int:
    checks: list[Check] = []

    print("V2-HARDEN-1 GOVERNANCE ROUTE / TEMPLATE / SERVICE INVENTORY AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print("Mode: read-only script audit")
    print("")

    add(checks, "app_py_exists", APP.exists(), str(APP))
    add(checks, "services_governance_exists", SERVICES.exists(), str(SERVICES))
    add(checks, "template_dir_exists", TEMPLATE_DIR.exists(), str(TEMPLATE_DIR))

    if not APP.exists() or not SERVICES.exists() or not TEMPLATE_DIR.exists():
        for check in checks:
            print(f"{check.status}: {check.key} — {check.detail}")
        return 1

    app_text = read(APP)
    services_text = read(SERVICES)

    expected_routes = [
        ("/governance/evidence-exports", "governance_evidence_export_index"),
        ("/governance/evidence-exports.csv", "governance_evidence_export_index_csv"),
        ("/governance/evidence-exports/manifest", "governance_evidence_export_manifest"),
        ("/governance/evidence-exports/manifest.txt", "governance_evidence_export_manifest_text"),
        ("/governance/evidence-exports/integrity", "governance_export_integrity_digest"),
        ("/governance/evidence-exports/integrity.txt", "governance_export_integrity_digest_text"),
        ("/governance/evidence-exports/archive-intake", "governance_export_archive_intake_preview"),
        ("/governance/evidence-exports/archive-intake.txt", "governance_export_archive_intake_preview_text"),
        ("/governance/evidence-exports/certification", "governance_evidence_certification_dashboard"),
        ("/governance/evidence-exports/certification.txt", "governance_evidence_certification_dashboard_text"),
        ("/governance/evidence-exports/exceptions", "governance_evidence_exception_panel"),
        ("/governance/evidence-exports/exceptions.txt", "governance_evidence_exception_panel_text"),
        ("/governance/evidence-exports/completion-gate", "governance_evidence_completion_gate"),
        ("/governance/evidence-exports/completion-gate.txt", "governance_evidence_completion_gate_text"),
    ]

    print("ROUTE INVENTORY")
    print("-" * 76)
    for route, fn_name in expected_routes:
        add(checks, f"route_exists:{route}", route_exists(app_text, route), route)
        add(checks, f"route_function_exists:{fn_name}", function_exists(app_text, fn_name), fn_name)

    expected_builders = [
        "build_governance_evidence_export_index",
        "build_governance_evidence_export_manifest",
        "build_governance_evidence_export_manifest_text",
        "build_governance_export_integrity_digest_index",
        "build_governance_export_integrity_digest_text",
        "build_governance_export_archive_intake_preview",
        "build_governance_export_archive_intake_preview_text",
        "build_governance_evidence_certification_dashboard",
        "build_governance_evidence_certification_dashboard_text",
        "build_governance_evidence_exception_panel",
        "build_governance_evidence_exception_panel_text",
        "build_governance_evidence_completion_gate",
        "build_governance_evidence_completion_gate_text",
    ]

    print("")
    print("SERVICE BUILDER INVENTORY")
    print("-" * 76)
    for builder in expected_builders:
        add(checks, f"service_builder_exists:{builder}", function_exists(services_text, builder), builder)
        add(checks, f"app_references_builder:{builder}", builder in app_text or builder.endswith("_text"), builder)

    expected_templates = [
        "evidence_export_index.html",
        "evidence_export_manifest.html",
        "evidence_export_integrity.html",
        "evidence_export_archive_intake.html",
        "evidence_certification_dashboard.html",
        "evidence_exception_panel.html",
        "evidence_completion_gate.html",
    ]

    print("")
    print("TEMPLATE INVENTORY")
    print("-" * 76)
    template_texts: dict[str, str] = {}
    for name in expected_templates:
        path = TEMPLATE_DIR / name
        exists = path.exists()
        add(checks, f"template_exists:{name}", exists, str(path))
        if exists:
            t = read(path)
            template_texts[name] = t
            add(checks, f"template_extends_base:{name}", "{% extends \"base.html\" %}" in t or "{% extends 'base.html' %}" in t, name)
            add(checks, f"template_no_direct_property_footer:{name}", "Institutional Property of Luna Isaac III Mishoe" not in t, name)
            add(checks, f"template_no_direct_custody_notice_render:{name}", "custody_notice" not in t, name)

    render_template_expectations = [
        ("governance/evidence_export_index.html", "evidence_export_index.html"),
        ("governance/evidence_export_manifest.html", "evidence_export_manifest.html"),
        ("governance/evidence_export_integrity.html", "evidence_export_integrity.html"),
        ("governance/evidence_export_archive_intake.html", "evidence_export_archive_intake.html"),
        ("governance/evidence_certification_dashboard.html", "evidence_certification_dashboard.html"),
        ("governance/evidence_exception_panel.html", "evidence_exception_panel.html"),
        ("governance/evidence_completion_gate.html", "evidence_completion_gate.html"),
    ]

    print("")
    print("ROUTE → TEMPLATE WIRING")
    print("-" * 76)
    for render_ref, template_name in render_template_expectations:
        add(checks, f"app_renders_template:{render_ref}", render_ref in app_text, render_ref)
        add(checks, f"rendered_template_file_exists:{template_name}", (TEMPLATE_DIR / template_name).exists(), template_name)

    index_text = template_texts.get("evidence_export_index.html", "")
    index_endpoint_expectations = [
        "governance_evidence_export_manifest",
        "governance_evidence_export_manifest_text",
        "governance_export_integrity_digest",
        "governance_export_integrity_digest_text",
        "governance_export_archive_intake_preview",
        "governance_export_archive_intake_preview_text",
        "governance_evidence_certification_dashboard",
        "governance_evidence_certification_dashboard_text",
        "governance_evidence_exception_panel",
        "governance_evidence_exception_panel_text",
        "governance_evidence_completion_gate",
        "governance_evidence_completion_gate_text",
    ]

    print("")
    print("EVIDENCE EXPORT INDEX LINK INVENTORY")
    print("-" * 76)
    add(checks, "evidence_export_index_loaded", bool(index_text), "templates/governance/evidence_export_index.html")
    for endpoint in index_endpoint_expectations:
        add(checks, f"index_links_endpoint:{endpoint}", endpoint_link_exists(index_text, endpoint), endpoint)

    text_builder_expectations = [
        "build_governance_evidence_export_manifest_text",
        "build_governance_export_integrity_digest_text",
        "build_governance_export_archive_intake_preview_text",
        "build_governance_evidence_certification_dashboard_text",
        "build_governance_evidence_exception_panel_text",
        "build_governance_evidence_completion_gate_text",
    ]

    print("")
    print("TXT EXPORT CUSTODY PRESERVATION")
    print("-" * 76)
    for builder in text_builder_expectations:
        builder_match = re.search(
            rf"def\s+{re.escape(builder)}\s*\(.*?(?=^def\s+|\Z)",
            services_text,
            flags=re.MULTILINE | re.DOTALL,
        )
        body = builder_match.group(0) if builder_match else ""
        add(checks, f"text_builder_exists:{builder}", bool(builder_match), builder)
        add(checks, f"text_builder_has_custody_notice:{builder}", "CUSTODY NOTICE" in body or "custody_notice" in body, builder)

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
