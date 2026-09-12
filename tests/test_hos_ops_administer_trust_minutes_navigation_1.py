from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "ios_workspaces" / "administer.html"


def test_administer_trust_minutes_uses_real_dashboard_endpoint():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert (
        '<a href="{{ url_for(\'trust_minutes_dashboard\') }}">Trust Minutes</a>'
        in text
    )


def test_administer_trust_minutes_dead_fragment_is_removed():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert '<a href="#trust-minutes">Trust Minutes</a>' not in text
