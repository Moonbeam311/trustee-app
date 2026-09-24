from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
TPL = ROOT / "templates" / "create_trust_step6.html"


def _read(path):
    return path.read_text(
        encoding="utf-8",
        errors="strict",
    )


def test_final_review_uses_explicit_settlor_then_grantor_fallback():
    html = _read(TPL)

    assert (
        '<strong>Grantor / Settlor:</strong>'
        in html
    )

    assert (
        'trust.settlor_name or trust.grantor_name or "Not entered"'
        in html
    )


def test_final_review_no_longer_displays_bare_settlor_only():
    html = _read(TPL)

    assert (
        '<strong>Settlor:</strong> {{ trust.settlor_name }}'
        not in html
    )


def test_grantor_settlor_wizard_step_stores_grantor_name():
    source = _read(APP)

    start = source.index(
        "def create_trust_step2_grantor"
    )

    end = source.index(
        "\ndef create_trust_step2(",
        start,
    )

    section = source[start:end]

    assert (
        '"grantor_name": request.form.get("grantor_name")'
        in section
    )


def test_display_repair_does_not_rewrite_settlor_field():
    source = _read(APP)

    start = source.index(
        "def create_trust_step6"
    )

    end = source.index(
        "def create_trust_step7",
        start,
    )

    section = source[start:end]

    assert '"settlor_name"' not in section
    assert '"grantor_name"' not in section
