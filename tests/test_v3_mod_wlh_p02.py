from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP = (ROOT / "app.py").read_text(encoding="utf-8")
SERVICE = (
    ROOT / "services" / "services_work_learning_questions.py"
).read_text(encoding="utf-8")

WORKSPACE = (
    ROOT / "templates" / "workspace_detail.html"
).read_text(encoding="utf-8")

QUESTION_LIST = (
    ROOT / "templates" / "workspace_questions.html"
).read_text(encoding="utf-8")

QUESTION_FORM = (
    ROOT / "templates" / "workspace_question_form.html"
).read_text(encoding="utf-8")

QUESTION_DETAIL = (
    ROOT / "templates" / "workspace_question_detail.html"
).read_text(encoding="utf-8")


def test_p02_service_foundation_exists():
    assert "def ensure_work_learning_question_tables" in SERVICE
    assert "hub_questions" in SERVICE
    assert "hub_question_learning_resources" in SERVICE


def test_p02_question_status_contract():
    assert "QUESTION_STATUSES" in SERVICE
    for status in ("open", "researching", "resolved", "closed"):
        assert status in SERVICE


def test_p02_learning_resource_contract():
    for resource_type in (
        "learning_article",
        "trust_type",
        "form_guide",
    ):
        assert resource_type in SERVICE


def test_p02_question_scope_is_explicit():
    for field in (
        "workspace_id",
        "firm_id",
        "owner_id",
        "question_text",
        "created_by",
    ):
        assert field in SERVICE


def test_p02_duplicate_resource_identity_is_stable():
    assert "INSERT OR IGNORE" in SERVICE
    assert "candidate_relationship_id" in SERVICE
    assert "SELECT relationship_id" in SERVICE
    assert "question_learning_resource_identity_not_found" in SERVICE


def test_p02_routes_exist():
    required = (
        "/workspaces/<workspace_id>/questions",
        "/workspaces/<workspace_id>/questions/new",
        "/workspaces/<workspace_id>/questions/<question_id>",
        "/workspaces/<workspace_id>/questions/<question_id>/status",
        "/workspaces/<workspace_id>/questions/<question_id>/resources/add",
        "/resources/<relationship_id>/remove",
    )

    for route in required:
        assert route in APP


def test_p02_role_contract():
    assert '"workspace_questions": {"Admin", "Trustee", "Viewer"}' in APP
    assert '"workspace_question_new": {"Admin", "Trustee"}' in APP
    assert '"workspace_question_detail": {"Admin", "Trustee", "Viewer"}' in APP
    assert '"workspace_question_status": {"Admin", "Trustee"}' in APP
    assert '"workspace_question_resource_add": {"Admin", "Trustee"}' in APP
    assert '"workspace_question_resource_remove": {"Admin", "Trustee"}' in APP


def test_p02_parent_workspace_controls_firm_context():
    assert "workspace = get_workspace_by_id(workspace_id)" in APP
    assert 'firm_id = session.get("firm_id") or "FIRM-001"' in APP
    assert 'owner_id = workspace.get("owner_id") or get_current_owner()' in APP


def test_p02_does_not_accept_browser_firm_or_owner_scope():
    assert 'request.form.get("firm_id")' not in APP[
        APP.find("def workspace_questions"):
        APP.find("def discussion_dashboard")
    ]
    assert 'request.form.get("owner_id")' not in APP[
        APP.find("def workspace_questions"):
        APP.find("def discussion_dashboard")
    ]


def test_p02_write_routes_require_csrf():
    section = APP[
        APP.find("def workspace_question_new"):
        APP.find("def discussion_dashboard")
    ]
    assert section.count("validate_csrf_token()") >= 4


def test_p02_resource_existence_validation_is_present():
    section = APP[
        APP.find("def workspace_question_resource_add"):
        APP.find("def workspace_question_resource_remove")
    ]
    assert "get_learning_article_by_id" in section
    assert "get_trust_type_detail" in section
    assert "get_form_guide_by_name" in section


def test_workspace_exposes_questions():
    assert "View Questions" in WORKSPACE
    assert "New Question" in WORKSPACE
    assert "workspace_questions" in WORKSPACE
    assert "workspace_question_new" in WORKSPACE


def test_question_ui_preserves_working_artifact_boundary():
    combined = QUESTION_LIST + QUESTION_FORM + QUESTION_DETAIL

    assert "working" in combined.lower()
    assert "governed fact" in combined.lower()
    assert "resolved" in combined.lower()


def test_learning_resources_preserve_non_authoritative_boundary():
    lowered = QUESTION_DETAIL.lower()
    assert "learning" in lowered
    assert "governed fact" in lowered


def test_p02_does_not_implement_governed_promotion():
    combined = (
        SERVICE
        + QUESTION_LIST
        + QUESTION_FORM
        + QUESTION_DETAIL
    ).lower()

    assert "automatic promotion" not in combined
    assert "promote to governed" not in combined
    assert "approve governed" not in combined


def test_p02_does_not_create_ai_definitive_answer_engine():
    combined = (SERVICE + QUESTION_DETAIL).lower()

    assert "definitive answer" not in combined
    assert "automated answer" not in combined
    assert "ai answer" not in combined
