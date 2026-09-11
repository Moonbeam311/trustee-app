from pathlib import Path


APP = Path("app.py")

GUARD = (
    'if request.method == "POST" and '
    'transfer.status in {"completed", "training_complete"}:'
)


def _function_block(name):
    text = APP.read_text(encoding="utf-8")
    marker = f"def {name}("
    start = text.index(marker)
    end = text.find("\n@app.route(", start + len(marker))
    if end == -1:
        end = len(text)
    return text[start:end]


def test_completed_packets_block_support_document_mutation():
    block = _function_block("transfer_support_doc_edit")

    assert GUARD in block
    assert "Completed transfer packets are read-only." in block
    assert block.index(GUARD) < block.index("support_doc.status =")
    assert block.index(GUARD) < block.index("ext_db.session.commit()")


def test_completed_packets_block_external_tracking_mutation():
    block = _function_block("transfer_external_tracking")

    assert GUARD in block
    assert "Completed transfer packets are read-only." in block
    assert block.index(GUARD) < block.index("transfer.external_institution =")
    assert block.index(GUARD) < block.index("transfer.external_verified =")
    assert block.index(GUARD) < block.index("ext_db.session.commit()")
