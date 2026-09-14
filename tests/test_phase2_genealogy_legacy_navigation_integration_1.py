from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_platform_navigation_exposes_canonical_genealogy_legacy_workspace():
    text = _read("templates/_platform_nav.html")

    assert "url_for('genealogy_legacy_workspace')" in text
    assert "Genealogy &amp; Legacy" in text


def test_admin_primary_genealogy_entry_uses_canonical_workspace():
    text = _read("templates/admin_index.html")

    assert (
        '<a href="{{ url_for(\'genealogy_legacy_workspace\') }}">'
        "Genealogy &amp; Legacy</a>"
    ) in text

    assert (
        '<a href="{{ url_for(\'genealogy_dashboard\') }}">Genealogy</a>'
        not in text
    )


def test_legacy_navigation_remains_legacy_compatibility_surface():
    text = _read("templates/_nav.html")

    assert '<a href="/genealogy">Genealogy</a>' in text


def test_all_three_genealogy_routes_remain_registered():
    text = _read("app.py")

    assert '@app.route("/genealogy/legacy-workspace")' in text
    assert '@app.route("/genealogy")' in text
    assert '@app.route("/genealogy/new", methods=["GET", "POST"])' in text


def test_navigation_integration_does_not_redirect_legacy_genealogy_routes():
    text = _read("app.py")

    legacy_start = text.index('@app.route("/genealogy")')
    legacy_end = text.index("TRUST_TYPE_LABELS", legacy_start)
    legacy_block = text[legacy_start:legacy_end]

    assert 'redirect(url_for("genealogy_legacy_workspace"))' not in legacy_block
    assert "create_genealogy_record" in legacy_block
