from pathlib import Path
import re


APP = Path("app.py").read_text(encoding="utf-8")

GUARD = 'if transfer.mode == "training":'
MESSAGE_FRAGMENT_1 = (
    '"Training transfers do not enter institutional archive handoff "'
)
MESSAGE_FRAGMENT_2 = (
    '"or certified archive export workflows."'
)


def function_block(name):
    marker = f"def {name}("
    start = APP.index(marker)
    end = APP.find("\n@app.route(", start)
    if end == -1:
        end = len(APP)
    return APP[start:end]


def owner_function(marker):
    pos = APP.index(marker)
    prefix = APP[:pos]
    matches = list(re.finditer(r"^def ([A-Za-z0-9_]+)\(", prefix, re.M))
    assert matches
    return matches[-1].group(1)


def test_training_is_blocked_before_transfer_archive_package_export_history():
    block = function_block("transfer_archive_handoff_export_package")
    assert GUARD in block
    assert MESSAGE_FRAGMENT_1 in block
    assert MESSAGE_FRAGMENT_2 in block
    assert block.index(GUARD) < block.index("log_archive_export_history(")


def test_training_is_blocked_before_transfer_archive_pdf_export_history():
    block = function_block("transfer_archive_handoff_audit_export_pdf")
    assert GUARD in block
    assert MESSAGE_FRAGMENT_1 in block
    assert MESSAGE_FRAGMENT_2 in block
    assert block.index(GUARD) < block.index("log_archive_export_history(")


def test_training_is_blocked_before_transfer_archive_txt_export_history():
    block = function_block("transfer_archive_handoff_audit_export_txt")
    assert GUARD in block
    assert MESSAGE_FRAGMENT_1 in block
    assert MESSAGE_FRAGMENT_2 in block
    assert block.index(GUARD) < block.index("log_archive_export_history(")


def test_training_is_blocked_before_archive_handoff_insert():
    name = owner_function("INSERT INTO transfer_archive_handoff (")
    block = function_block(name)
    assert GUARD in block
    assert MESSAGE_FRAGMENT_1 in block
    assert MESSAGE_FRAGMENT_2 in block
    assert block.index(GUARD) < block.index(
        "INSERT INTO transfer_archive_handoff ("
    )


def test_training_is_blocked_before_archive_handoff_correction_insert():
    name = owner_function(
        "INSERT INTO transfer_archive_handoff_corrections ("
    )
    block = function_block(name)
    assert GUARD in block
    assert MESSAGE_FRAGMENT_1 in block
    assert MESSAGE_FRAGMENT_2 in block
    assert block.index(GUARD) < block.index(
        "INSERT INTO transfer_archive_handoff_corrections ("
    )


def test_trust_level_export_index_remains_trust_scoped():
    # Do not globally disable the trust-level index because a trust may contain
    # legitimate institutional transfers alongside Training packets.
    block = function_block("archive_handoff_export_index_csv")
    assert "require_active_firm_trust_or_deny" in block
