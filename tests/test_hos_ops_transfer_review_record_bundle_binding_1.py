from pathlib import Path


TEMPLATE = Path("templates/transfer_review.html")


def test_transfer_review_generated_records_use_record_bundle():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "{{ record_bundle.schedule_a_text if record_bundle else '' }}" in text
    assert "{{ record_bundle.transfer_log_text if record_bundle else '' }}" in text
    assert "{{ record_bundle.minutes_text if record_bundle else '' }}" in text


def test_transfer_review_generated_records_do_not_bind_to_transfer_row():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "{{ transfer.schedule_a_text or '' }}" not in text
    assert "{{ transfer.transfer_log_text or '' }}" not in text
    assert "{{ transfer.minutes_text or '' }}" not in text
