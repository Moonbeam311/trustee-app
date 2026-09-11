from pathlib import Path


APP = Path("app.py")
REVIEW = Path("templates/transfer_review.html")


def test_app_routes_training_review_to_training_completion_contract():
    text = APP.read_text(encoding="utf-8")

    assert "can_complete_training_transfer," in text
    assert "complete_training_transfer," in text

    assert """if transfer.mode == "training":
        allowed, missing = can_complete_training_transfer(transfer)
    else:
        allowed, missing = can_finalize_transfer(transfer)""" in text

    assert "success, missing = complete_training_transfer(" in text

    assert (
        'transfer.status in {"completed", "training_complete"}'
        in text
    )


def test_training_review_ui_uses_non_institutional_completion_language():
    text = REVIEW.read_text(encoding="utf-8")

    assert "Training Packet Complete" in text
    assert "Complete Training Packet" in text
    assert "Cannot Complete Training Yet" in text
    assert "No institutional transfer finalization" in text


def test_institutional_missing_external_proof_has_operator_handoff():
    text = REVIEW.read_text(encoding="utf-8")

    assert 'item == "external_verification_or_proof"' in text
    assert "Update External Tracking" in text
    assert "Attach External Proof" in text
    assert "View Linked Proof" in text
