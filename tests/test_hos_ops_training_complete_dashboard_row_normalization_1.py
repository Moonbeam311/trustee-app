from pathlib import Path


TEMPLATE = Path(
    "templates/transfer_execution_dashboard.html"
).read_text(encoding="utf-8")


def test_training_complete_has_distinct_card_badge():
    assert '{% elif t.status == "training_complete" %}' in TEMPLATE
    assert "Training Complete</span>" in TEMPLATE


def test_training_complete_has_noninstitutional_terminal_message():
    assert "Training Packet Complete" in TEMPLATE
    assert (
        "Institutional finalization,\n"
        "              ledger posting, external verification, archive readiness,\n"
        "              and archive handoff are not applicable to this Training packet."
        in TEMPLATE
    )
    assert (
        "No institutional completion or archive deficiency is asserted."
        in TEMPLATE
    )


def test_training_complete_action_branch_is_read_only_navigation():
    marker = "View Training Record"
    marker_pos = TEMPLATE.index(marker)

    start = TEMPLATE.rfind(
        '{% if t.status == "training_complete" %}',
        0,
        marker_pos,
    )
    end = TEMPLATE.index(
        '{% elif t.status in ["draft", "in_progress"] %}',
        marker_pos,
    )

    assert start != -1

    branch = TEMPLATE[start:end]

    assert "View Training Record" in branch
    assert ">Detail</a>" in branch
    assert ">Print</a>" in branch

    assert "Resume" not in branch
    assert "Manage Docs" not in branch
    assert "External Tracking" not in branch
    assert "Optional Docs" not in branch
    assert "Recommended Docs" not in branch
    assert "Bank Docs" not in branch
    assert "Property Docs" not in branch
    assert "Document Docs" not in branch


def test_editable_transfer_branch_retains_existing_operator_controls():
    start = TEMPLATE.index(
        '{% elif t.status in ["draft", "in_progress"] %}'
    )
    end = TEMPLATE.index("{% else %}", start)

    branch = TEMPLATE[start:end]

    assert "Resume" in branch
    assert "Manage Docs" in branch
    assert "External Tracking" in branch
    assert "Optional Docs" in branch
    assert "Print" in branch


def test_training_complete_is_not_presented_with_institutional_metrics():
    marker = (
        "{# Finding-24B.2: terminal Training packets are instructional,"
    )
    start = TEMPLATE.index(marker)

    training_start = TEMPLATE.index(
        '{% if t.status == "training_complete" %}',
        start,
    )
    training_end = TEMPLATE.index("{% else %}", training_start)

    branch = TEMPLATE[training_start:training_end]

    assert "Training Packet Complete" in branch
    assert "Ledger Readiness" not in branch
    assert "External Pending" not in branch
    assert "Hybrid Not Started" not in branch
    assert "Archive Gate" not in branch
    assert "Blockers:" not in branch
    assert "Archive Handoff:" not in branch
