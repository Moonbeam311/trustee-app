from pathlib import Path


def test_draft_readiness_ledger_uses_precise_document_checklist_label():
    template = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "intake"
        / "draft_readiness_ledger.html"
    ).read_text(encoding="utf-8")

    assert "<th>Document Checklist Items</th>" in template
    assert "<th>Documents</th>" not in template

    # Preserve the existing derived field. This repair changes
    # presentation semantics only, not document-count derivation.
    assert "{{ row.document_count }}" in template
