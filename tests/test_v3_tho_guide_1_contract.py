import copy

from services import services_guide_handoff_interpretation as guide


def package(*, acceptance="ACCEPTANCE RECORDED", gaps=None, profiles=True):
    trust_id = "TR-A"
    return {
        "descriptor_id": "successor-handoff-package-descriptor:TR-A",
        "root_trust_id": trust_id,
        "source_aggregate": {"aggregate_id": "trust-successor-handoff:TR-A"},
        "sections": {
            "trust_identity": {"classification": "INCLUDED", "content": {
                "trust": {"trust_id": trust_id, "trust_name": "Alpha Trust", "status": "Active"}}},
            "fiduciary_authority": {"classification": "INCLUDED", "content": {
                "state": "AVAILABLE", "records": [{"fiduciary_id": "FID-A"}]}},
            "successor_acceptance": {"classification": "INCLUDED", "content": {
                "state": "AVAILABLE", "display_state": acceptance,
                "records": ([{"acceptance_id": "ACC-A"}] if acceptance != "DESIGNATED / ACCEPTANCE NOT RECORDED" else [])}},
            "continuity": {"classification": "INCLUDED", "content": {
                "state": "AVAILABLE" if profiles else "UNLINKED",
                "profiles": ([{"continuity_profile_id": "CP-A", "readiness": {
                    "classification": "ready_for_review"}}] if profiles else [])}},
            "governance": {"classification": "INCLUDED", "content": {"state": "AVAILABLE"}},
            "execution": {"classification": "REFERENCE ONLY", "content": {"state": "NOT APPLICABLE"}},
            "documents": {"classification": "REFERENCE ONLY", "content": {"state": "AVAILABLE"}},
            "archive": {"classification": "REFERENCE ONLY", "content": {"state": "AVAILABLE"}},
            "provenance": {"classification": "REFERENCE ONLY", "content": [
                {"source_domain": "Trust", "source_record_id": "TR-A"},
                {"source_domain": "SuccessorAcceptance", "source_record_id": "ACC-A"},
            ]},
        },
        "readiness": {"status": "needs_attention", "gaps": gaps or []},
    }


def build(monkeypatch, value=None):
    source = package() if value is None else value
    monkeypatch.setattr(guide, "build_successor_handoff_package_descriptor",
                        lambda *_args, **_kwargs: copy.deepcopy(source))
    return guide.build_successor_handoff_guide_interpretation(
        "TR-A", db_path="unused", trust_authorization_check=lambda *_: True,
        continuity_authorization_check=lambda *_: True,
        fiduciary_authorization_check=lambda *_: True,
        governance_authorization_check=lambda *_: True,
        acceptance_authorization_check=lambda *_: True)


def items(result, classification=None):
    return [item for item in result["items"]
            if classification is None or item["classification"] == classification]


def test_trust_acceptance_and_relationship_are_classified_and_sourced(monkeypatch):
    result = build(monkeypatch)
    assert items(result)[0]["classification"] == "recorded_fact"
    assert items(result)[0]["source_reference"] == "Trust:TR-A"
    accepted = [item for item in items(result) if "Acceptance status" in item["summary"]][0]
    assert accepted["classification"] == "recorded_fact"
    assert accepted["source_reference"] == "SuccessorAcceptance:ACC-A"
    assert any(item["classification"] == "source_supported_relationship" and
               "CP-A" in item["summary"] for item in items(result))


def test_pending_missing_and_legacy_acceptance_are_not_promoted(monkeypatch):
    for state in ("ACCEPTANCE PENDING REVIEW", "DESIGNATED / ACCEPTANCE NOT RECORDED",
                  "LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED"):
        result = build(monkeypatch, package(acceptance=state))
        item = [value for value in items(result) if "Acceptance status" in value["summary"]][0]
        assert item["classification"] == "system_status"
        assert item["status"] == state
        assert "legal authority" not in item["summary"].lower()


def test_continuity_readiness_is_status_not_validity_or_activation(monkeypatch):
    result = build(monkeypatch)
    readiness = [item for item in items(result) if item["summary"].startswith("Continuity readiness")][0]
    assert readiness["classification"] == "system_status"
    assert "not legal validity" in readiness["basis"].lower()
    assert result["boundaries"]["continuity_activated"] is False
    assert result["boundaries"]["responsibility_assigned"] is False


def test_gap_emits_labeled_inference_recommendation_and_proposed_action(monkeypatch):
    value = package(gaps=[{"code": "unresolved_authority_source",
                           "source_domain": "Fiduciary", "source_record_id": "FID-A"}])
    result = build(monkeypatch, value)
    for classification in ("system_status", "inference", "recommendation", "proposed_action"):
        assert any(item["classification"] == classification and
                   item["source_reference"] == "Fiduciary:FID-A" for item in items(result))
    assert "legal-authority conclusion" in items(result, "inference")[0]["basis"]


def test_conflict_is_exposed_without_selecting_a_source(monkeypatch):
    value = package(gaps=[{"code": "conflicting_authority_sources",
                           "source_domain": "Fiduciary", "source_record_id": "FID-A"}])
    result = build(monkeypatch, value)
    conflict = items(result, "conflict")[0]
    assert "does not select" in conflict["basis"]
    assert conflict["source_reference"] == "Fiduciary:FID-A"


def test_package_archive_statuses_are_interpreted_not_owned(monkeypatch):
    result = build(monkeypatch)
    for owner in ("Document", "Archive", "Execution", "Governance"):
        status = [item for item in items(result) if item["source_owner"] == owner][0]
        assert status["classification"] == "system_status"
        assert "does not own or mutate" in status["basis"]


def test_denied_or_cross_firm_root_fails_closed(monkeypatch):
    monkeypatch.setattr(guide, "build_successor_handoff_package_descriptor",
                        lambda *_args, **_kwargs: None)
    assert guide.build_successor_handoff_guide_interpretation(
        "TR-X", db_path="unused", trust_authorization_check=lambda *_: False,
        continuity_authorization_check=lambda *_: False,
        fiduciary_authorization_check=lambda *_: False,
        governance_authorization_check=lambda *_: False) is None


def test_output_is_deterministic_read_only_and_never_emits_class_eight(monkeypatch):
    first = build(monkeypatch, package(gaps=[{"code": "missing_document_evidence"}]))
    second = build(monkeypatch, package(gaps=[{"code": "missing_document_evidence"}]))
    assert first == second
    assert first["mutation_performed"] is False
    assert all(value is False for value in first["boundaries"].values())
    assert "operator_authorized_institutional_action" not in first["classifications_emitted"]
    assert set(first["classifications_emitted"]) <= set(guide.GUIDE_OUTPUT_CLASSES)


def test_unlinked_continuity_remains_explicit_without_fabricated_relationship(monkeypatch):
    result = build(monkeypatch, package(profiles=False))
    assert any(item["summary"] == "No linked Continuity Profile is documented."
               for item in items(result))
    assert not items(result, "source_supported_relationship")
