#!/usr/bin/env python3
"""
POST-V2-16C.1

Audit minimal, read-only People Workspace status-context wiring.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP_PATH = ROOT / "app.py"
SERVICE_PATH = ROOT / "services" / "services_governance.py"
PEOPLE_TEMPLATE_PATH = (
    ROOT / "templates" / "ios_workspaces" / "people.html"
)

EXPECTED_PANEL_KEYS = [
    "fiduciaries",
    "institutional_identity",
    "contextual_people",
    "governance_authorities",
    "execution_participants",
    "system_accounts",
    "people_reporting",
]

ALLOWED_STATUSES = {
    "Available",
    "Empty",
    "Incomplete",
    "Context Required",
    "Protected",
    "Unavailable",
    "Exception",
    "Not Evaluated",
}

PROHIBITED_KEYS = {
    "username",
    "usernames",
    "password",
    "password_hash",
    "passwords",
    "permission_matrix",
    "permission_overrides",
    "typed_signature",
    "signature_image_path",
    "initials_image_path",
    "signature_hash",
    "credential_block",
    "certificate_reference",
    "notes",
    "participant_name",
    "signer_name",
    "full_name",
    "primary_person",
    "trustee_candidate",
    "successor_trustee_candidate",
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
    people_template_before = PEOPLE_TEMPLATE_PATH.read_text(
        encoding="utf-8"
    )

    ast.parse(app_source)
    ast.parse(service_source)

    require(
        "def build_people_workspace_read_only_status():" in service_source,
        "People read-only status builder exists.",
    )

    require(
        '"context_type": "people_workspace_status"' in service_source,
        "People context type is explicit.",
    )

    require(
        '"read_only": True' in service_source,
        "People status context is explicitly read-only.",
    )

    require(
        "people_status = build_people_workspace_read_only_status()"
        in app_source,
        "People workspace route invokes the status builder.",
    )

    require(
        "people_status=people_status" in app_source,
        "People status is passed to ios_workspace.html.",
    )

    require(
        'if workspace_key == "people":' in app_source,
        "People status is built only for the People workspace.",
    )

    if "ADR-9B placeholder" in people_template_before:
        require(
            "people_status" not in people_template_before,
            (
                "Pre-rendering People placeholder does not consume "
                "People status context."
            ),
        )
    else:
        require(
            "people_status" in people_template_before,
            (
                "Post-C.1 People rendering remains connected to the "
                "approved People status context."
            ),
        )

        require(
            'people_status.context_type == "people_workspace_status"'
            in people_template_before,
            (
                "Post-C.1 rendering verifies the bounded People "
                "context type."
            ),
        )

        require(
            "people_status.read_only" in people_template_before,
            (
                "Post-C.1 rendering requires the read-only People "
                "status contract."
            ),
        )

        require(
            "<form" not in people_template_before.lower(),
            (
                "Post-C.1 People rendering remains free of forms "
                "and mutation controls."
            ),
        )

    require(
        "INSERT INTO" not in service_source[
            service_source.index(
                "def build_people_workspace_read_only_status():"
            ):
        ],
        "People status builder contains no INSERT statement.",
    )

    require(
        "UPDATE " not in service_source[
            service_source.index(
                "def build_people_workspace_read_only_status():"
            ):
        ],
        "People status builder contains no UPDATE statement.",
    )

    require(
        "DELETE FROM" not in service_source[
            service_source.index(
                "def build_people_workspace_read_only_status():"
            ):
        ],
        "People status builder contains no DELETE statement.",
    )

    require(
        "CREATE TABLE" not in service_source[
            service_source.index(
                "def build_people_workspace_read_only_status():"
            ):
        ],
        "People status builder creates no database tables.",
    )

    from services.services_governance import (
        build_people_workspace_read_only_status,
    )

    context = build_people_workspace_read_only_status()

    require(
        isinstance(context, dict),
        "People status builder returns a dictionary.",
    )

    require(
        context.get("context_type") == "people_workspace_status",
        "Runtime context type is correct.",
    )

    require(
        context.get("read_only") is True,
        "Runtime context remains read-only.",
    )

    require(
        isinstance(context.get("panels"), dict),
        "Runtime context contains a panel dictionary.",
    )

    require(
        context.get("panel_order") == EXPECTED_PANEL_KEYS,
        "Runtime panel order matches the locked POST-V2-16B IA.",
    )

    require(
        list(context.get("panels", {}).keys()) == EXPECTED_PANEL_KEYS,
        "Runtime panels contain exactly the approved seven keys.",
    )

    for panel_key in EXPECTED_PANEL_KEYS:
        panel = context["panels"][panel_key]

        require(
            panel.get("read_only") is True,
            f"{panel_key} panel is read-only.",
        )

        require(
            panel.get("status") in ALLOWED_STATUSES,
            f"{panel_key} panel uses an allowed status.",
        )

        require(
            isinstance(panel.get("summary"), dict),
            f"{panel_key} panel summary is aggregate data.",
        )

        require(
            isinstance(panel.get("route"), str)
            and panel.get("route", "").startswith("/"),
            f"{panel_key} panel has a bounded destination route.",
        )

    exposed_keys = {
        key.lower()
        for key in walk_keys(context)
    }

    prohibited_exposed = sorted(
        exposed_keys.intersection(PROHIBITED_KEYS)
    )

    require(
        not prohibited_exposed,
        (
            "Runtime status context exposes no prohibited sensitive keys"
            if not prohibited_exposed
            else (
                "Prohibited keys exposed: "
                + ", ".join(prohibited_exposed)
            )
        ),
    )

    print("\nPEOPLE STATUS CONTEXT")
    print(json.dumps(context, indent=2, sort_keys=True))

    print("\nPOST-V2-16C.1 RESULT")
    print(
        "PASS — Minimal read-only People status context wiring is bounded, "
        "aggregate-only, and non-mutating."
    )


if __name__ == "__main__":
    main()
