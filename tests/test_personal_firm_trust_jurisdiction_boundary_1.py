from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
STEP1 = ROOT / "templates" / "create_trust_step1.html"
DECLARATION = ROOT / "templates" / "trust_declaration_output_surface.html"


def _read(path):
    return path.read_text(encoding="utf-8", errors="strict")


def test_step1_does_not_require_jurisdiction_before_trust_identity():
    html = _read(STEP1)

    required_jurisdiction = re.search(
        r"<input\b[^>]*\bname=[\"']jurisdiction[\"'][^>]*\brequired\b",
        html,
        flags=re.IGNORECASE,
    )

    assert required_jurisdiction is None
    assert "If governing jurisdiction has not yet been determined" in html
    assert "Hindsfoot will not infer a state" in html


def test_step1_preserves_blank_jurisdiction_as_unresolved():
    source = _read(APP)

    assert (
        '"jurisdiction": str(\n'
        '                request.form.get("jurisdiction") or ""\n'
        '            ).strip(),'
        in source
    )

    # Do not introduce a guessed or pseudo-jurisdiction into Step 1.
    step1_start = source.index("def create_trust_step1():")
    step1_end = source.index(
        "def create_trust_step2_grantor",
        step1_start,
    )
    step1_source = source[step1_start:step1_end]

    forbidden_assignments = (
        '"jurisdiction": "New Jersey"',
        '"jurisdiction": "NJ"',
        '"jurisdiction": "UNRESOLVED"',
        '"jurisdiction": "Not Yet Selected"',
        '"jurisdiction": "Pending Professional Review"',
    )

    for value in forbidden_assignments:
        assert value not in step1_source


def test_blank_jurisdiction_does_not_create_governing_law_value():
    html = _read(DECLARATION)

    # Existing downstream contract:
    # an empty jurisdiction produces no fallback governing-law value.
    assert (
        "preview_context.governing_law "
        "or preview_context.jurisdiction or \"\""
        in html
    )


def test_step1_still_creates_only_a_draft_shell():
    source = _read(APP)

    step1_start = source.index("def create_trust_step1():")
    step1_end = source.index(
        "def create_trust_step2_grantor",
        step1_start,
    )
    step1_source = source[step1_start:step1_end]

    assert '"status": "Draft"' in step1_source
    assert '"trust_type": "Not Yet Selected"' in step1_source
    assert '"trust_purpose": "Not Yet Selected"' in step1_source
