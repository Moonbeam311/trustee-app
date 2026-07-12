#!/usr/bin/env python3
"""
POST-V2-16C.2

Audit People Workspace read-only status-panel rendering.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP_PATH = ROOT / "app.py"
SERVICE_PATH = ROOT / "services" / "services_governance.py"
TEMPLATE_PATH = ROOT / "templates" / "ios_workspaces" / "people.html"

EXPECTED_PANEL_KEYS = [
    "fiduciaries",
    "institutional_identity",
    "contextual_people",
    "governance_authorities",
    "execution_participants",
    "system_accounts",
    "people_reporting",
]

EXPECTED_PANEL_LABELS = [
    "Fiduciary Registry",
    "Institutional Identity",
    "Contextual People Records",
    "Governance Authorities",
    "Execution Participants",
    "Protected System Accounts",
    "People Reports",
]

ALLOWED_RUNTIME_ROUTES = {
    "/fiduciaries",
    "/institutional-identity",
    "/admin/workspace/administer",
    "/admin/workspace/governance",
    "/execution/sessions",
    "/admin/workspace/system",
    "/reports/fiduciaries.pdf",
}

PROHIBITED_TEMPLATE_ROUTES = {
    "/users",
    "/users/new",
    "/roles",
    "/roles/new",
    "/permissions",
    "/fiduciaries/new",
    "/institutional-identity/signature-profile/new",
    "/institutional-identity/brand-package/new",
    "/execution/sessions/<execution_id>/participant",
    "/execution/sessions/<execution_id>/signature",
}

PROHIBITED_RUNTIME_KEYS = {
    "username",
    "usernames",
    "password",
    "password_hash",
    "permission_matrix",
    "permission_overrides",
    "typed_signature",
    "signature_image_path",
    "initials_image_path",
    "signature_hash",
    "credential_block",
    "certificate_reference",
    "participant_name",
    "signer_name",
    "full_name",
    "primary_person",
    "trustee_candidate",
    "successor_trustee_candidate",
    "notes",
}

PROHIBITED_RENDERED_MARKERS = {
    "Reset Password",
    "Create User",
    "Manage Permissions",
    "Add Execution Participant",
    "Add Execution Signature",
    "Create Signature Profile",
    "Create Brand Package",
    "Add Fiduciary Role",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"PASS — {message}")


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk_keys(child)

    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def main() -> None:
    app_source = APP_PATH.read_text(encoding="utf-8")
    service_source = SERVICE_PATH.read_text(encoding="utf-8")
    template_source = TEMPLATE_PATH.read_text(encoding="utf-8")

    ast.parse(app_source)
    ast.parse(service_source)

    require(
        "def build_people_workspace_read_only_status():"
        in service_source,
        "POST-V2-16C.1 People status builder remains present.",
    )

    require(
        "people_status = build_people_workspace_read_only_status()"
        in app_source,
        "POST-V2-16C.1 People route wiring remains present.",
    )

    require(
        'data-post-v2-16c2="people-read-only-status-panels"'
        in template_source,
        "People template declares the POST-V2-16C.2 rendering boundary.",
    )

    require(
        "ADR-9B placeholder" not in template_source,
        "People ADR-9B placeholder has been replaced.",
    )

    require(
        "people_status.context_type == \"people_workspace_status\""
        in template_source,
        "Template verifies the bounded People context type.",
    )

    require(
        "people_status.read_only" in template_source,
        "Template requires read-only status context.",
    )

    require(
        "people_status.panel_order" in template_source,
        "Template renders panels using the locked panel order.",
    )

    require(
        "people_status.panels" in template_source,
        "Template reads the approved panel dictionary.",
    )

    require(
        "<form" not in template_source.lower(),
        "People template contains no forms.",
    )

    require(
        'method="post"' not in template_source.lower(),
        "People template contains no POST action.",
    )

    require(
        "url_for(" not in template_source,
        "People template does not reconstruct mutation routes dynamically.",
    )

    for prohibited_route in sorted(PROHIBITED_TEMPLATE_ROUTES):
        require(
            prohibited_route not in template_source,
            f"Template excludes prohibited route {prohibited_route}.",
        )

    require(
        'href="{{ panel.route }}"' in template_source,
        "Panel links use builder-approved bounded routes.",
    )

    require(
        'data-people-section="protected-boundary"'
        in template_source,
        "Protected and contextual boundary is visible.",
    )

    require(
        'data-people-section="operator-navigation"'
        in template_source,
        "Operator navigation section is visible.",
    )

    require(
        "@media (max-width: 560px)" in template_source,
        "People status panels include mobile rendering support.",
    )

    from services.services_governance import (
        build_people_workspace_read_only_status,
    )

    context = build_people_workspace_read_only_status()

    require(
        context.get("context_type") == "people_workspace_status",
        "Runtime People context type is correct.",
    )

    require(
        context.get("read_only") is True,
        "Runtime People context remains read-only.",
    )

    require(
        context.get("panel_order") == EXPECTED_PANEL_KEYS,
        "Runtime panel order matches the locked seven-panel order.",
    )

    panels = context.get("panels") or {}

    require(
        list(panels.keys()) == EXPECTED_PANEL_KEYS,
        "Runtime panel dictionary contains exactly seven approved panels.",
    )

    runtime_routes = {
        panel.get("route")
        for panel in panels.values()
        if panel.get("route")
    }

    require(
        runtime_routes == ALLOWED_RUNTIME_ROUTES,
        "Runtime panel routes match the approved exposure boundary.",
    )

    exposed_keys = {
        key.lower()
        for key in walk_keys(context)
    }

    prohibited_keys_found = sorted(
        exposed_keys.intersection(PROHIBITED_RUNTIME_KEYS)
    )

    require(
        not prohibited_keys_found,
        (
            "Runtime context exposes no prohibited sensitive keys"
            if not prohibited_keys_found
            else (
                "Prohibited runtime keys exposed: "
                + ", ".join(prohibited_keys_found)
            )
        ),
    )

    environment = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=True,
        undefined=StrictUndefined,
    )

    template = environment.get_template(
        "ios_workspaces/people.html"
    )

    rendered = template.render(people_status=context)

    require(
        'data-post-v2-16c2="people-read-only-status-panels"'
        in rendered,
        "Rendered HTML contains the POST-V2-16C.2 marker.",
    )

    rendered_panel_positions = []

    for panel_key in EXPECTED_PANEL_KEYS:
        marker = f'data-people-panel="{panel_key}"'

        require(
            marker in rendered,
            f"Rendered HTML contains {panel_key} panel.",
        )

        rendered_panel_positions.append(rendered.index(marker))

    require(
        rendered_panel_positions == sorted(rendered_panel_positions),
        "Rendered panels follow the locked institutional order.",
    )

    for label in EXPECTED_PANEL_LABELS:
        require(
            label in rendered,
            f"Rendered HTML contains panel label: {label}.",
        )

    for prohibited_marker in sorted(PROHIBITED_RENDERED_MARKERS):
        require(
            prohibited_marker not in rendered,
            f"Rendered HTML excludes action: {prohibited_marker}.",
        )

    require(
        "/users" not in rendered,
        "Rendered HTML does not link directly to user administration.",
    )

    require(
        "/roles" not in rendered,
        "Rendered HTML does not link directly to role administration.",
    )

    require(
        "/permissions" not in rendered,
        "Rendered HTML does not link directly to permission administration.",
    )

    require(
        "/execution/sessions/<execution_id>" not in rendered,
        "Rendered HTML contains no unscoped execution mutation route.",
    )

    require(
        "<form" not in rendered.lower(),
        "Rendered HTML remains form-free.",
    )

    require(
        "Institutional People Overview" in rendered,
        "Rendered HTML includes the People overview heading.",
    )

    require(
        "Protected and Contextual Boundary" in rendered,
        "Rendered HTML includes the protected-boundary warning.",
    )

    require(
        "Operator Navigation" in rendered,
        "Rendered HTML includes continuity navigation.",
    )

    print("\nPEOPLE STATUS CONTEXT")
    print(json.dumps(context, indent=2, sort_keys=True))

    print("\nPOST-V2-16C.2 RESULT")
    print(
        "PASS — People Workspace renders exactly seven bounded, "
        "read-only, aggregate status panels without exposing protected "
        "mutations or sensitive person data."
    )


if __name__ == "__main__":
    main()
