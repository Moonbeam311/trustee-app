from pathlib import Path


APP = Path("app.py").read_text(encoding="utf-8")
TEMPLATE = Path(
    "templates/transfer_execution_dashboard.html"
).read_text(encoding="utf-8")


def test_training_complete_has_distinct_terminal_dashboard_state():
    assert '"training_complete": sum(' in APP
    assert 'if getattr(t, "status", "") == "training_complete"' in APP
    assert 'return t.status == "training_complete"' in APP
    assert 'return t.status not in {"completed", "training_complete"}' in APP


def test_institutional_metrics_exclude_training_packets():
    assert "institutional_transfers = [" in APP
    assert '"total": len(institutional_transfers)' in APP
    assert APP.count("for t in institutional_transfers:") >= 3
    assert 'if getattr(t, "mode", "") == "training":' in APP


def test_dashboard_summary_exposes_training_completion():
    assert "transfer_status_summary=transfer_status_summary" in APP
    assert "Training Complete:" in TEMPLATE
    assert "transfer_status_summary.training_complete" in TEMPLATE
    assert "transfer_status_summary.open" in TEMPLATE


def test_training_complete_filter_is_visible():
    assert "transfer_filter=training_complete" in TEMPLATE
    assert ">Training Complete</a>" in TEMPLATE


def test_old_open_count_contract_is_removed():
    old = (
        "Open: {{ transfers|rejectattr('status', 'equalto', "
        "'completed')|list|length }}"
    )
    assert old not in TEMPLATE
