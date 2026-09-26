from pathlib import Path
import ast

import pytest

import services.services_account_asset_contract as asset_contract
import services.services_tr001_property_finalization as finalization
import database.db as db_module


def _authorized(value):
    return str(value) == "TR-001"


def test_trust_summary_reuses_canonical_enumerator_and_property_snapshots(
    monkeypatch,
):
    seen = {
        "enumerator": [],
        "snapshots": [],
    }

    monkeypatch.setattr(
        db_module,
        "get_current_firm_id",
        lambda: "FIRM-002",
    )

    def fake_list_trust_assets(
        trust_id,
        *,
        authorization_check,
    ):
        seen["enumerator"].append(
            (
                trust_id,
                authorization_check(
                    trust_id
                ),
            )
        )

        return [
            {
                "property_id": "PROP-1",
                "trust_id": "TR-001",
                "firm_id": "FIRM-002",
                "property_name": "Property One",
                "property_type": "tangible_property",
            },
            {
                "property_id": "PROP-2",
                "trust_id": "TR-001",
                "firm_id": "FIRM-002",
                "property_name": "Property Two",
                "property_type": "financial_property",
            },
        ]

    monkeypatch.setattr(
        asset_contract,
        "list_trust_assets",
        fake_list_trust_assets,
    )

    snapshots = {
        "PROP-1": {
            "derived_workflow_state": "IDENTIFIED",
            "schedule_a_draft_context": {
                "schedule_a_draft_eligible": "NO",
            },
            "transfer_complete": False,
            "trustee_acceptance_complete": False,
            "funding_complete": False,
            "blocker_reasons": [
                {
                    "type": "DOCUMENT_EXECUTION",
                    "reason": "AWAITING_EXECUTION",
                }
            ],
        },
        "PROP-2": {
            "derived_workflow_state":
                "FUNDED_ACTIVE_TRUST_PROPERTY",
            "schedule_a_draft_context": {
                "schedule_a_draft_eligible": "YES",
            },
            "transfer_complete": True,
            "trustee_acceptance_complete": True,
            "funding_complete": True,
            "blocker_reasons": [],
        },
    }

    def fake_snapshot(
        db_path,
        firm_id,
        trust_id,
        property_id,
    ):
        seen["snapshots"].append(
            (
                db_path,
                firm_id,
                trust_id,
                property_id,
            )
        )

        return snapshots[
            property_id
        ]

    monkeypatch.setattr(
        finalization,
        "get_property_finalization_snapshot",
        fake_snapshot,
    )

    summary = (
        finalization
        .get_trust_property_finalization_summary(
            "fixture.sqlite3",
            "FIRM-002",
            "TR-001",
            authorization_check=_authorized,
        )
    )

    assert seen["enumerator"] == [
        (
            "TR-001",
            True,
        )
    ]

    assert [
        item[3]
        for item in seen["snapshots"]
    ] == [
        "PROP-1",
        "PROP-2",
    ]

    assert summary[
        "property_count"
    ] == 2

    assert summary[
        "schedule_a_draft_eligible_count"
    ] == 1

    assert summary[
        "transfer_complete_count"
    ] == 1

    assert summary[
        "trustee_acceptance_complete_count"
    ] == 1

    assert summary[
        "funding_complete_count"
    ] == 1

    assert summary[
        "workflow_state_counts"
    ] == {
        "FUNDED_ACTIVE_TRUST_PROPERTY": 1,
        "IDENTIFIED": 1,
    }

    assert summary[
        "derived_read_model_only"
    ] is True

    assert summary[
        "source_provenance"
    ][
        "canonical_property_ids"
    ] == [
        "PROP-1",
        "PROP-2",
    ]


def test_trust_summary_requires_authorization_check(
    monkeypatch,
):
    monkeypatch.setattr(
        db_module,
        "get_current_firm_id",
        lambda: "FIRM-002",
    )

    with pytest.raises(
        finalization.PropertyFinalizationReadError,
        match="Authorization check is required",
    ):
        finalization.get_trust_property_finalization_summary(
            "fixture.sqlite3",
            "FIRM-002",
            "TR-001",
            authorization_check=None,
        )


def test_trust_summary_rejects_active_firm_mismatch(
    monkeypatch,
):
    monkeypatch.setattr(
        db_module,
        "get_current_firm_id",
        lambda: "FIRM-OTHER",
    )

    with pytest.raises(
        finalization.PropertyFinalizationReadError,
        match="does not match the active firm scope",
    ):
        finalization.get_trust_property_finalization_summary(
            "fixture.sqlite3",
            "FIRM-002",
            "TR-001",
            authorization_check=_authorized,
        )


def test_trust_summary_rejects_out_of_scope_enumerator_record(
    monkeypatch,
):
    monkeypatch.setattr(
        db_module,
        "get_current_firm_id",
        lambda: "FIRM-002",
    )

    monkeypatch.setattr(
        asset_contract,
        "list_trust_assets",
        lambda trust_id, *, authorization_check: [
            {
                "property_id": "PROP-X",
                "trust_id": "TR-001",
                "firm_id": "FIRM-OTHER",
                "property_name": "Wrong Firm Property",
            }
        ],
    )

    def should_not_run(*args, **kwargs):
        raise AssertionError(
            "Property snapshot must not run for an out-of-scope asset."
        )

    monkeypatch.setattr(
        finalization,
        "get_property_finalization_snapshot",
        should_not_run,
    )

    with pytest.raises(
        finalization.PropertyFinalizationReadError,
        match="out-of-scope property",
    ):
        finalization.get_trust_property_finalization_summary(
            "fixture.sqlite3",
            "FIRM-002",
            "TR-001",
            authorization_check=_authorized,
        )


def test_empty_authorized_trust_summary_is_read_only_zero_state(
    monkeypatch,
):
    monkeypatch.setattr(
        db_module,
        "get_current_firm_id",
        lambda: "FIRM-002",
    )

    monkeypatch.setattr(
        asset_contract,
        "list_trust_assets",
        lambda trust_id, *, authorization_check: [],
    )

    summary = (
        finalization
        .get_trust_property_finalization_summary(
            "fixture.sqlite3",
            "FIRM-002",
            "TR-001",
            authorization_check=_authorized,
        )
    )

    assert summary[
        "property_count"
    ] == 0

    assert summary[
        "properties"
    ] == []

    assert summary[
        "schedule_a_draft_eligible_count"
    ] == 0

    assert summary[
        "funding_complete_count"
    ] == 0


def test_formation_hub_route_guards_scope_before_summary():
    source = Path(
        "app.py"
    ).read_text(
        encoding="utf-8",
        errors="strict",
    )

    tree = ast.parse(
        source
    )

    route = next(
        node
        for node in tree.body
        if isinstance(
            node,
            ast.FunctionDef,
        )
        and node.name
        == "trust_formation_preview_hub"
    )

    route_source = (
        ast.get_source_segment(
            source,
            route,
        )
        or ""
    )

    guard_pos = route_source.index(
        "require_active_firm_trust_or_deny"
    )

    summary_pos = route_source.index(
        "get_trust_property_finalization_summary"
    )

    assert guard_pos < summary_pos

    assert (
        "from database.db import DB_PATH"
        in route_source
    )

    assert (
        "authorization_check="
        in route_source
    )

    assert (
        "property_finalization_summary="
        in route_source
    )

    assert (
        "property_finalization_summary_error="
        in route_source
    )


def test_formation_hub_property_summary_is_read_only_handoff():
    text = Path(
        "templates/trust_formation_preview_hub.html"
    ).read_text(
        encoding="utf-8",
        errors="strict",
    )

    assert (
        'id="property-finalization-summary"'
        in text
    )

    block = text.split(
        'id="property-finalization-summary"',
        1,
    )[1].split(
        'id="trust-record-context"',
        1,
    )[0]

    # Template indentation and line wrapping are presentation details.
    # Normalize whitespace once so this test verifies semantic boundary
    # language rather than source formatting.
    normalized_block = " ".join(
        block.split()
    )

    required_semantic_boundaries = (
        "Trust Property Finalization Context",
        "does not transfer property",
        "Schedule A eligibility shown here is preparation status only",
        "Property selection is not transfer",
        "transfer is not trustee property acceptance",
        "trustee property acceptance is not funding",
        "document generation is not execution",
        "internal workflow certification is not professional legal validation",
    )

    for phrase in required_semantic_boundaries:
        assert phrase in normalized_block

    assert (
        "url_for('property_detail'"
        in block
    )

    assert "<form" not in block.lower()
