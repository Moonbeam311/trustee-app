from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "templates" / "work_learning_hub.html").read_text(encoding="utf-8")
NAV = (ROOT / "templates" / "_platform_nav.html").read_text(encoding="utf-8")


def test_p01_route_exists():
    assert '@app.route("/work-learning-hub")' in APP
    assert "def work_learning_hub():" in APP
    assert 'render_template("work_learning_hub.html", context=context)' in APP


def test_p01_role_contract():
    assert '"work_learning_hub": {"Admin", "Trustee", "Viewer"}' in APP


def test_p01_context_builder_reuses_firm_scoped_workspaces():
    assert "def build_work_learning_hub_context():" in APP
    assert '"workspaces": get_all_workspaces()' in APP
    assert 'firm_id = session.get("firm_id") or "FIRM-001"' in APP
    assert "WHERE firm_id = ?" in APP


def test_p01_three_state_model():
    for state in (
        "Explore and Learn",
        "Work and Develop",
        "Confirm and Govern",
    ):
        assert state in APP
        assert state in TEMPLATE


def test_p01_governance_boundary():
    assert "does not automatically become" in APP
    assert "a governed institutional record." in APP
    assert "Governance boundary:" in TEMPLATE


def test_p01_navigation_entry():
    assert '<a href="/work-learning-hub">Work & Learning Hub</a>' in NAV


def test_p01_preserves_existing_workspace_entry():
    assert '@app.route("/workspaces")' in APP
    assert "def workspace_dashboard():" in APP


def test_p01_template_has_no_mutation_or_promotion_form():
    lowered = TEMPLATE.lower()
    assert "<form" not in lowered
    assert 'method="post"' not in lowered
    assert "promote" not in lowered
    assert "approve" not in lowered
