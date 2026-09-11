from types import SimpleNamespace

import services.services_transfer as transfer_service


def _transfer(**overrides):
    data = {
        "id": 1,
        "transfer_id": "T-TRAINING-001",
        "mode": "training",
        "status": "in_progress",
        "asset_name": "Synthetic Training Asset",
        "transfer_type": "gift",
        "assignment_confirmed": True,
        "trustee_decision": "approve",
        "control_change_status": "intent_only",
        "records_complete": True,
        "external_verified": False,
        "finalized_at": None,
        "finalized_by": None,
        "finalized_capacity": None,
        "current_capacity": "trustee",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_training_packet_can_complete_without_external_execution_proof(monkeypatch):
    monkeypatch.setattr(
        transfer_service,
        "get_media_by_entity",
        lambda *args, **kwargs: [],
    )

    transfer = _transfer()

    allowed, missing = transfer_service.can_complete_training_transfer(transfer)

    assert allowed is True
    assert missing == []


def test_training_packet_cannot_cross_institutional_finalize_boundary(monkeypatch):
    monkeypatch.setattr(
        transfer_service,
        "get_media_by_entity",
        lambda *args, **kwargs: [object()],
    )

    transfer = _transfer(external_verified=True)

    allowed, missing = transfer_service.can_finalize_transfer(transfer)

    assert allowed is False
    assert missing == ["training_context_requires_training_completion"]


def test_training_completion_uses_distinct_state_and_no_finalization_metadata(monkeypatch):
    actions = []

    def capture_action(**kwargs):
        actions.append(kwargs)
        return object()

    monkeypatch.setattr(
        transfer_service,
        "add_transfer_action",
        capture_action,
    )

    transfer = _transfer()

    success, missing = transfer_service.complete_training_transfer(
        transfer,
        performed_by="demo-admin",
        capacity_used="trustee",
        commit=False,
    )

    assert success is True
    assert missing == []
    assert transfer.status == "training_complete"

    assert transfer.finalized_at is None
    assert transfer.finalized_by is None
    assert transfer.finalized_capacity is None

    assert len(actions) == 1
    assert actions[0]["action_type"] == "training_completed"
    assert actions[0]["performed_by"] == "demo-admin"
    assert actions[0]["capacity_used"] == "trustee"


def test_institutional_finalization_still_requires_external_proof(monkeypatch):
    monkeypatch.setattr(
        transfer_service,
        "get_media_by_entity",
        lambda *args, **kwargs: [],
    )

    transfer = _transfer(
        transfer_id="T-REAL-001",
        mode="real",
        external_verified=False,
    )

    allowed, missing = transfer_service.can_finalize_transfer(transfer)

    assert allowed is False
    assert missing == ["external_verification_or_proof"]

    transfer.external_verified = True

    allowed, missing = transfer_service.can_finalize_transfer(transfer)

    assert allowed is True
    assert missing == []
