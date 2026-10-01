from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

LAUNCH = (
    ROOT / "templates" / "create_trust_launch.html"
).read_text(
    encoding="utf-8",
    errors="strict",
)

STEP6 = (
    ROOT / "templates" / "create_trust_step6.html"
).read_text(
    encoding="utf-8",
    errors="strict",
)

STEP7 = (
    ROOT / "templates" / "create_trust_step7.html"
).read_text(
    encoding="utf-8",
    errors="strict",
)

APP = (
    ROOT / "app.py"
).read_text(
    encoding="utf-8",
    errors="strict",
)


def test_step7_uses_formation_record_completion_language():
    assert "Formation Record Complete" in STEP7
    assert (
        "trust formation intake record is complete"
        in STEP7
    )

    assert "Trust Finalized" not in STEP7

    assert (
        "Your trust has been finalized"
        not in STEP7
    )


def test_step7_expressly_separates_formation_from_legal_events():
    required = (
        "internal workflow milestone only",
        "governing instrument has been executed",
        "legally final",
        "trustee authority has become operative",
        "property has been transferred",
        "accepted by the Trustee",
        "trust has been funded",
        "professional legal validation",
    )

    normalized_step7 = " ".join(STEP7.split())

    for text in required:
        assert text in normalized_step7


def test_step6_describes_completion_not_trust_finalization():
    assert (
        "completes the trust formation intake record"
        in STEP6
    )

    assert (
        "formation record is completed"
        in STEP6
    )

    assert (
        "Complete Formation Record "
        "and Open Formation Preview Hub"
        in STEP6
    )

    assert (
        "finalizes the intake record"
        not in STEP6
    )

    assert (
        "mark the trust intake as finalized"
        not in STEP6
    )


def test_launch_describes_step7_as_formation_record_completion():
    assert (
        "Review and complete the formation record"
        in LAUNCH
    )

    assert (
        "Completed formation records route "
        "into post-create review"
        in LAUNCH
    )

    assert (
        "Finalized trusts still route"
        not in LAUNCH
    )


def test_internal_finalized_status_token_remains_unchanged():
    assert APP.count('{"status": "Finalized"}') == 1
    assert 'revision_basis="trust_formation_completion"' in APP


def test_terminology_change_does_not_claim_execution_or_funding():
    misleading = (
        "Trust Executed",
        "Trust Funded",
        "Property Transferred",
        "Professional Legal Validation Complete",
    )

    combined = (
        LAUNCH
        + "\n"
        + STEP6
        + "\n"
        + STEP7
    )

    for text in misleading:
        assert text not in combined
