import copy

import pytest

from services import services_handoff_package_adapter as package_adapter
from services.services_intake_trust_bridge import BridgeError


def aggregate(acceptance_state="ACCEPTANCE RECORDED"):
    return {
        "contract_version": "V3-THO-AGG-1",
        "aggregate_id": "trust-successor-handoff:TR-A",
        "root_trust_id": "TR-A",
        "identity": {"state": "AVAILABLE", "trust": {"trust_id": "TR-A", "trust_name": "Trust A"}},
        "fiduciary_authority": {"state": "AVAILABLE", "records": [{"fiduciary_id": "FID-A"}]},
        "successor_acceptance": {"state": "AVAILABLE", "display_state": acceptance_state,
                                 "records": [{"acceptance_id": "ACC-A"}]},
        "continuity": {"state": "AVAILABLE", "profiles": [{"continuity_profile_id": "CP-A"}]},
        "accounts_assets": {"accounts": [{"account_id": "ACT-A"}], "assets": []},
        "governance": {"state": "AVAILABLE", "links": [{"governance_id": "GOV-A"}]},
        "execution": {"state": "AVAILABLE", "execution_id": "EX-A", "orchestration": {}},
        "documents": {"state": "AVAILABLE", "references": [{"document_id": "DOC-A"}]},
        "archive": {"state": "AVAILABLE", "descriptors": [{"package_id": "HO-A"}]},
        "readiness": {"status": "needs_attention", "gap_count": 1,
                      "gaps": [{"code": "authority_source_missing"}]},
        "provenance": [
            {"source_domain": "Trust", "source_record_id": "TR-A"},
            {"source_domain": "Fiduciary", "source_record_id": "FID-A"},
            {"source_domain": "SuccessorAcceptance", "source_record_id": "ACC-A"},
            {"source_domain": "Continuity", "source_record_id": "CP-A"},
            {"source_domain": "AccountAsset", "source_record_id": "TR-A"},
            {"source_domain": "Governance", "source_record_id": "GOV-A"},
            {"source_domain": "Execution", "source_record_id": "EX-A"},
            {"source_domain": "Document", "source_record_id": "DOC-A"},
            {"source_domain": "Archive", "source_record_id": "HO-A"},
        ],
    }


def build(monkeypatch, value=None):
    supplied = aggregate() if value is None else value
    monkeypatch.setattr(package_adapter, "build_trust_successor_handoff_context",
                        lambda *_args, **_kwargs: copy.deepcopy(supplied))
    return package_adapter.build_successor_handoff_package_descriptor(
        "TR-A", db_path="unused", trust_authorization_check=lambda *_: True,
        continuity_authorization_check=lambda *_: True,
        fiduciary_authorization_check=lambda *_: True,
        governance_authorization_check=lambda *_: True,
        acceptance_authorization_check=lambda *_: True,
        execution_id="EX-A")


def test_descriptor_assembles_canonical_sections_and_references(monkeypatch):
    result = build(monkeypatch)
    assert result["descriptor_id"] == "successor-handoff-package-descriptor:TR-A"
    assert result["sections"]["trust_identity"]["source_owner"] == "Trust"
    assert result["sections"]["successor_acceptance"]["content"]["display_state"] == "ACCEPTANCE RECORDED"
    assert result["sections"]["documents"]["classification"] == "REFERENCE ONLY"
    assert result["sections"]["archive"]["classification"] == "REFERENCE ONLY"
    assert result["sections"]["execution"]["classification"] == "REFERENCE ONLY"


def test_content_index_is_deterministic_and_canonical(monkeypatch):
    first = build(monkeypatch)
    second = build(monkeypatch)
    assert first == second
    assert [item["source_owner"] for item in first["content_index"]] == sorted(
        item["source_owner"] for item in first["content_index"])
    assert all(item["canonical_object_id"] for item in first["content_index"])


@pytest.mark.parametrize("state", [
    "ACCEPTANCE PENDING REVIEW", "DESIGNATED / ACCEPTANCE NOT RECORDED",
    "DECLINED_RECORDED", "WITHDRAWN_RECORDED", "SUPERSEDED",
])
def test_acceptance_semantics_are_preserved_without_inference(monkeypatch, state):
    result = build(monkeypatch, aggregate(state))
    assert result["sections"]["successor_acceptance"]["content"]["display_state"] == state
    assert result["institutional_effects"]["acceptance_changed"] is False


def test_missing_sections_and_gaps_remain_explicit(monkeypatch):
    value = aggregate("DESIGNATED / ACCEPTANCE NOT RECORDED")
    value["successor_acceptance"].update(state="MISSING", records=[])
    value["continuity"].update(state="UNLINKED", profiles=[])
    value["documents"].update(state="MISSING", references=[])
    value["archive"].update(state="MISSING", descriptors=[])
    result = build(monkeypatch, value)
    assert result["sections"]["successor_acceptance"]["classification"] == "NOT AVAILABLE"
    assert result["sections"]["continuity"]["classification"] == "NOT AVAILABLE"
    assert result["sections"]["documents"]["classification"] == "NOT AVAILABLE"
    assert result["readiness"]["gaps"] == [{"code": "authority_source_missing"}]
    assert result["readiness"]["package_complete"] is False


def test_descriptor_has_no_generation_archive_or_institutional_side_effect(monkeypatch):
    result = build(monkeypatch)
    assert result["mutation_performed"] is False
    assert result["generation"]["generated_at"] == "NOT DOCUMENTED"
    assert all(value is False for key, value in result["generation"].items()
               if key != "generated_at")
    assert all(value is False for value in result["institutional_effects"].values())


def test_denied_or_cross_scope_root_fails_closed(monkeypatch):
    monkeypatch.setattr(package_adapter, "build_trust_successor_handoff_context",
                        lambda *_args, **_kwargs: None)
    assert package_adapter.build_successor_handoff_package_descriptor(
        "TR-X", db_path="unused", trust_authorization_check=lambda *_: False,
        continuity_authorization_check=lambda *_: False,
        fiduciary_authorization_check=lambda *_: False,
        governance_authorization_check=lambda *_: False) is None


def test_secret_material_is_rejected_even_from_a_broken_upstream(monkeypatch):
    value = aggregate()
    value["documents"]["references"][0]["password"] = "should-never-flow"
    with pytest.raises(BridgeError, match="[Ss]ecret"):
        build(monkeypatch, value)
