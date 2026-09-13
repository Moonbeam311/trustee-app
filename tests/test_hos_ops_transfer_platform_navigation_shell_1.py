from pathlib import Path


TRANSFER_TEMPLATES = [
    "transfer_archive_handoff.html",
    "transfer_archive_handoff_audit_trail.html",
    "transfer_archive_handoff_correction.html",
    "transfer_archive_handoff_correction_detail.html",
    "transfer_archive_handoff_detail.html",
    "transfer_asset.html",
    "transfer_assignment.html",
    "transfer_classification.html",
    "transfer_control_evidence.html",
    "transfer_execution_dashboard.html",
    "transfer_external_tracking.html",
    "transfer_records.html",
    "transfer_review.html",
    "transfer_start.html",
    "transfer_trustee_acceptance.html",
]


def test_transfer_pages_use_canonical_platform_navigation_base():
    root = Path("templates")

    base = (root / "base.html").read_text(encoding="utf-8")
    assert "{% block primary_navigation %}" in base
    assert '{% include "_nav.html" %}' in base

    transfer_base = (root / "transfer_base.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in transfer_base
    assert '{% block primary_navigation %}' in transfer_base
    assert '{% include "_platform_nav.html" %}' in transfer_base
    assert '{% include "_nav.html" %}' not in transfer_base
    assert "hindsfoot-operator-context" in transfer_base

    for filename in TRANSFER_TEMPLATES:
        text = (root / filename).read_text(encoding="utf-8")
        assert text.startswith('{% extends "transfer_base.html" %}'), filename

    remaining = []
    for path in root.glob("transfer_*.html"):
        if path.name == "transfer_base.html":
            continue

        text = path.read_text(encoding="utf-8")
        if '{% extends "base.html" %}' in text:
            remaining.append(path.name)

    assert remaining == []
