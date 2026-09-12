from pathlib import Path


TEMPLATE = Path(
    "templates/transfer_detail.html"
).read_text(encoding="utf-8")


def region(start, end):
    s = TEMPLATE.index(start)
    e = TEMPLATE.index(end, s)
    return TEMPLATE[s:e]


def training_branch(block):
    assert '{% if transfer.status == "training_complete" %}' in block
    assert "{% else %}" in block
    return block.split("{% else %}", 1)[0]


def test_training_top_actions_are_review_only():
    block = region(
        "Finding-25C: terminal Training records expose review-only actions.",
        "<h1>Transfer Detail</h1>",
    )
    branch = training_branch(block)

    assert "View Training Record" in branch
    assert "Print Training Packet" in branch
    assert "transfer_external_tracking" not in branch
    assert "transfer_template_center" not in branch
    assert "transfer_support_doc_edit" not in branch


def test_training_execution_status_does_not_assert_institutional_deficiencies():
    block = region(
        "Finding-25C: Training completion is terminal instructional state.",
        "INT-40A: final archive UX consolidated action panel",
    )
    branch = training_branch(block)

    assert "Training Packet: Complete" in branch
    assert "Institutional Finalization: Not Applicable" in branch
    assert "Archive Readiness: Not Applicable" in branch
    assert "Transfer Status: Pending" not in branch
    assert "Ledger Posted:" not in branch
    assert "Minute Generated:" not in branch


def test_training_archive_actions_do_not_expose_certified_archive_controls():
    block = region(
        "Finding-25C: institutional archive controls are not a Training action surface.",
        "INT-19A: transfer archive readiness gate panel",
    )
    branch = training_branch(block)

    assert "Training Record Actions" in branch
    assert "View Training Record" in branch
    assert "Print Training Packet" in branch
    assert "transfer_archive_handoff" not in branch
    assert "Export TXT" not in branch
    assert "Export PDF" not in branch
    assert "Export Package ZIP" not in branch
    assert "Export Index" not in branch


def test_training_archive_readiness_is_not_blocked_or_missing():
    block = region(
        "Finding-25C: Training does not carry institutional archive deficiencies.",
        '<p><strong>Status:</strong> {{ transfer.status }}</p>',
    )
    branch = training_branch(block)

    assert "Archive Gate: Not Applicable" in branch
    assert "Finalization: Not Applicable" in branch
    assert "Ledger: Not Applicable" in branch
    assert "Minute Verification: Not Applicable" in branch
    assert "Blocked" not in branch
    assert "Missing" not in branch
    assert "Archive Blockers" not in branch


def test_training_hybrid_status_is_not_not_started():
    block = region(
        "Finding-25C: hybrid institutional completion is not a Training metric.",
        "Finding-25C: external institutional tracking is not required for Training.",
    )
    branch = training_branch(block)

    assert "Overall Hybrid Status:</strong> Not Applicable — Training" in branch
    assert "Not Started" not in branch
    assert "No / Pending" not in branch


def test_training_external_tracking_is_not_pending_or_mutable():
    block = region(
        "Finding-25C: external institutional tracking is not required for Training.",
        "<h2>Assignment</h2>",
    )
    branch = training_branch(block)

    assert "Status:</strong> Not Applicable — Training" in branch
    assert "No / Pending" not in branch
    assert "Update External Tracking" not in branch
    assert "transfer_external_tracking" not in branch


def test_training_support_document_actions_are_read_only():
    block = region(
        "<h2>Support Document Tracking</h2>",
        "<h2>Action History</h2>",
    )

    assert '{% if transfer.status == "training_complete" %}' in block
    assert '<span class="muted">Read-only</span>' in block
    assert "transfer_support_doc_edit" in block


def test_institutional_surfaces_are_preserved_in_else_paths():
    # Finding-25C changes presentation branching only; institutional
    # capabilities remain present in the template.
    for token in (
        "Archive Handoff",
        "Export TXT",
        "Export PDF",
        "Export Package ZIP",
        "Archive Gate:",
        "Transfer Status:",
        "Overall Hybrid Status:",
        "Update External Tracking",
    ):
        assert token in TEMPLATE
