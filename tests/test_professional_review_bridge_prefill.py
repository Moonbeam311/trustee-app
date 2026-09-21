import re

import app as app_module


WORKFLOW_KEY = "professional_review_checklist"
INTAKE_ID = "INT-PREFILL-TEST"


def _checked(html, question_key, answer_key):
    match = re.search(
        rf'<input[^>]*name="{re.escape(question_key)}"[^>]*value="{re.escape(answer_key)}"[^>]*>',
        html,
    )
    assert match, f"missing control {question_key}/{answer_key}"
    return "checked" in match.group(0)


def _configure_generic_bridge(monkeypatch, rows):
    definition = app_module.get_workflow_bridge_definition(WORKFLOW_KEY)
    assert definition
    monkeypatch.setattr(app_module, "is_trust_instrument_workflow", lambda _key: False)
    monkeypatch.setattr(app_module, "ensure_workflow_bridge_tables", lambda: None)
    monkeypatch.setattr(app_module, "get_workflow_bridge_definition", lambda _key: definition)
    monkeypatch.setattr(app_module, "build_workflow_launch_prep", lambda *_args: {"workflow_key": WORKFLOW_KEY})
    monkeypatch.setattr(app_module, "list_workflow_bridge_answers", lambda *_args: [dict(row) for row in rows])


def _render_generic_bridge():
    with app_module.app.test_request_context(
        f"/intake/{INTAKE_ID}/recommendations/{WORKFLOW_KEY}/bridge"
    ):
        app_module.session["username"] = "bridge-prefill-test"
        return app_module.intake_workflow_bridge(INTAKE_ID, WORKFLOW_KEY)


def test_generic_bridge_get_prefills_saved_answers_without_mutating_rows(monkeypatch):
    rows = [
        {"question_key": "review_issue_type", "answer_key": "not_sure"},
        {"question_key": "deadline_pressure", "answer_key": "not_sure"},
        {"question_key": "documents_available", "answer_key": "claim_letter"},
    ]
    original_rows = [dict(row) for row in rows]
    _configure_generic_bridge(monkeypatch, rows)
    save_calls = []
    monkeypatch.setattr(app_module, "save_workflow_bridge_answers", lambda *args, **kwargs: save_calls.append((args, kwargs)))

    html = _render_generic_bridge()
    assert isinstance(html, str)
    assert _checked(html, "review_issue_type", "not_sure")
    assert _checked(html, "deadline_pressure", "not_sure")
    assert _checked(html, "documents_available", "claim_letter")
    assert not _checked(html, "review_issue_type", "tax")
    assert not _checked(html, "deadline_pressure", "yes")
    assert not _checked(html, "documents_available", "tax_notice")
    assert rows == original_rows
    assert save_calls == []


def test_generic_bridge_get_without_saved_rows_has_no_false_selections(monkeypatch):
    _configure_generic_bridge(monkeypatch, [])

    html = _render_generic_bridge()
    assert isinstance(html, str)
    assert re.search(r'<input[^>]+name="review_issue_type"', html)
    assert not re.search(r'<input[^>]+checked', html)


def test_shared_template_keeps_trust_instrument_answers_contract():
    with app_module.app.test_request_context():
        html = app_module.render_template(
            "intake/workflow_bridge.html",
            intake_id="INT-TRUST-COMPAT",
            workflow_key="declaration_of_trust",
            definition={"title": "Trust bridge", "purpose": "Test", "questions": []},
            launch={
                "bridge_questions": [
                    {"key": "trust_type", "label": "Trust type", "type": "radio", "options": ["revocable", "irrevocable"]},
                    {"key": "trust_parties", "label": "Trust parties", "type": "checkbox", "options": ["grantor", "trustee"]},
                ]
            },
            answers={"trust_type": "revocable", "trust_parties": ["grantor"]},
        )

    assert _checked(html, "trust_type", "revocable")
    assert not _checked(html, "trust_type", "irrevocable")
    assert _checked(html, "trust_parties", "grantor")
    assert not _checked(html, "trust_parties", "trustee")
