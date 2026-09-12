from pathlib import Path

TEMPLATE = Path("templates/transfer_execution_dashboard.html")


def template_text():
    return TEMPLATE.read_text(encoding="utf-8")


def test_execution_chain_panel_is_explicitly_institutional():
    text = template_text()

    assert "Institutional Execution Chain Health Summary" in text
    assert "Institutional Transfers: {{ execution_chain_health.total }}" in text


def test_training_exclusion_is_explained():
    text = template_text()

    assert (
        "Training packets are excluded because institutional completion "
        "requirements do not apply to them."
    ) in text


def test_ambiguous_total_transfers_label_is_removed_from_health_panel():
    text = template_text()

    start = text.index("Institutional Execution Chain Health Summary")
    end = text.index("{% endif %}", start)
    panel = text[start:end]

    assert "Total Transfers: {{ execution_chain_health.total }}" not in panel


def test_lower_execution_summary_still_preserves_all_transfer_scope():
    text = template_text()

    assert "Execution Summary" in text
    assert "Total: {{ transfer_status_summary.total if transfer_status_summary else 0 }}" in text
    assert "Training: {{ transfer_status_summary.training if transfer_status_summary else 0 }}" in text
    assert "Training Complete: {{ transfer_status_summary.training_complete if transfer_status_summary else 0 }}" in text
    assert "Institutional: {{ transfer_status_summary.institutional if transfer_status_summary else 0 }}" in text
