import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

APP = (ROOT / "app.py").read_text(encoding="utf-8")
SERVICE_PATH = ROOT / "services" / "services_work_learning_programs.py"
SERVICE = SERVICE_PATH.read_text(encoding="utf-8")


def _function_source(text, name):
    marker = f"def {name}("
    start = text.index(marker)

    next_def = text.find("\ndef ", start + len(marker))

    if next_def == -1:
        return text[start:]

    return text[start:next_def]


def _program_route_source():
    start = APP.index(
        '@app.route("/workspaces/<workspace_id>/programs")'
    )

    # Preserve the complete P03 route family without depending on
    # whichever unrelated route follows it.
    markers = [
        "\n@app.route(",
        "\n# ===",
    ]

    candidates = []

    probe = start + 1

    while True:
        nxt = APP.find("\n@app.route(", probe)
        if nxt == -1:
            break

        snippet = APP[nxt:nxt + 400]

        if "/program" not in snippet:
            candidates.append(nxt)
            break

        probe = nxt + 1

    end = candidates[0] if candidates else len(APP)

    return APP[start:end]


def test_p03c4c_authorization_role_contract():
    """P03 route authorization remains read/write role separated."""

    read_rules = (
        '"workspace_programs": {"Admin", "Trustee", "Viewer"}',
        '"workspace_program_detail": {"Admin", "Trustee", "Viewer"}',
    )

    write_rules = (
        '"workspace_program_new": {"Admin", "Trustee"}',
        '"workspace_program_edit": {"Admin", "Trustee"}',
        '"workspace_program_goal_add": {"Admin", "Trustee"}',
        '"workspace_program_alternative_add": {"Admin", "Trustee"}',
        '"workspace_program_scenario_add": {"Admin", "Trustee"}',
        '"workspace_program_revision_create": {"Admin", "Trustee"}',
    )

    for rule in read_rules + write_rules:
        assert rule in APP

    # Viewer must remain excluded from all mutation contracts.
    for rule in write_rules:
        assert "Viewer" not in rule


def test_p03c4c_authorization_contract_is_wired_to_endpoint_rules():
    """ROLE_RULES must remain part of application authorization logic."""

    assert "ROLE_RULES" in APP
    assert "request.endpoint" in APP

    # The app must consume the endpoint rule map outside its declaration.
    declaration = APP.index("ROLE_RULES =")
    later = APP.find("ROLE_RULES", declaration + len("ROLE_RULES ="))

    assert later != -1


def test_p03c4c_write_routes_preserve_csrf_regression_contract():
    """Existing P03 mutation routes continue to fail closed on CSRF."""

    section = _program_route_source()

    mutation_functions = (
        "workspace_program_new",
        "workspace_program_edit",
        "workspace_program_goal_add",
        "workspace_program_alternative_add",
        "workspace_program_scenario_add",
        "workspace_program_revision_create",
    )

    for name in mutation_functions:
        source = _function_source(APP, name)
        assert "validate_csrf_token()" in source


def test_p03c4c_browser_cannot_supply_firm_or_owner_scope():
    """Firm and owner context must come from governed workspace/session data."""

    section = _program_route_source()

    assert 'request.form.get("firm_id")' not in section
    assert "request.form.get('firm_id')" not in section
    assert 'request.args.get("firm_id")' not in section
    assert "request.args.get('firm_id')" not in section

    assert 'request.form.get("owner_id")' not in section
    assert "request.form.get('owner_id')" not in section
    assert 'request.args.get("owner_id")' not in section
    assert "request.args.get('owner_id')" not in section

    assert 'session.get("firm_id")' in section
    assert 'workspace.get("owner_id")' in section


@pytest.fixture()
def isolated_program_service(tmp_path, monkeypatch):
    """Run service regressions against a disposable SQLite database."""

    import services.services_work_learning_programs as service

    db_path = tmp_path / "p03c4c-security.db"

    def get_connection():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(service, "get_connection", get_connection)

    service.ensure_work_learning_program_tables()

    yield service, db_path


def test_p03c4c_same_firm_program_access_succeeds(
    isolated_program_service,
):
    service, _db = isolated_program_service

    program_id = service.create_hub_program(
        workspace_id="WS-A",
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        title="Same Firm Program",
        purpose="Security regression",
        created_by="tester",
    )

    row = service.get_hub_program(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    assert row is not None
    assert row["program_id"] == program_id
    assert row["firm_id"] == "FIRM-A"
    assert row["owner_id"] == "OWNER-A"


def test_p03c4c_cross_firm_scope_is_fail_closed_by_service_contract(
    isolated_program_service,
):
    """A valid program ID cannot cross its governed firm boundary."""

    service, _db = isolated_program_service

    program_id = service.create_hub_program(
        workspace_id="WS-A",
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        title="Firm Scoped Program",
        purpose="Cross-firm regression",
        created_by="tester",
    )

    assert service.get_hub_program(
        program_id=program_id,
        firm_id="FIRM-X",
        owner_id="OWNER-A",
    ) is None

    assert service.get_hub_program(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-X",
    ) is None


def test_p03c4c_workspace_program_listing_is_firm_scoped(
    isolated_program_service,
):
    service, _db = isolated_program_service

    service.create_hub_program(
        workspace_id="WS-SHARED",
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        title="Firm A Program",
        purpose="Firm A",
        created_by="tester",
    )

    service.create_hub_program(
        workspace_id="WS-SHARED",
        firm_id="FIRM-X",
        owner_id="OWNER-X",
        title="Firm X Program",
        purpose="Firm X",
        created_by="tester",
    )

    rows_a = service.get_hub_programs_for_workspace(
        workspace_id="WS-SHARED",
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    rows_x = service.get_hub_programs_for_workspace(
        workspace_id="WS-SHARED",
        firm_id="FIRM-X",
        owner_id="OWNER-X",
    )

    assert len(rows_a) == 1
    assert rows_a[0]["firm_id"] == "FIRM-A"
    assert rows_a[0]["owner_id"] == "OWNER-A"

    assert len(rows_x) == 1
    assert rows_x[0]["firm_id"] == "FIRM-X"
    assert rows_x[0]["owner_id"] == "OWNER-X"


def test_p03c4c_child_contracts_require_program_scope_precondition():
    """Child reads/writes must resolve the parent program in governed scope."""

    wrapper_guarded = (
        "create_program_goal",
        "get_program_goals",
        "create_program_alternative",
        "get_program_alternatives",
        "create_program_scenario",
        "get_program_scenarios",
        "get_program_revisions",
    )

    for name in wrapper_guarded:
        source = _function_source(SERVICE, name)
        assert "_program_available(" in source

    snapshot_source = _function_source(
        SERVICE,
        "build_program_snapshot",
    )

    # Snapshot resolution may use the canonical scoped lookup directly.
    assert "get_hub_program(" in snapshot_source
    assert "firm_id=firm_id" in snapshot_source
    assert "owner_id=owner_id" in snapshot_source

    revision_source = _function_source(
        SERVICE,
        "create_program_revision",
    )

    # Revision creation is scoped through its governed snapshot builder.
    assert "build_program_snapshot(" in revision_source


def test_p03c4c_program_availability_checks_firm_and_owner():
    """The parent availability predicate delegates to canonical scoped lookup."""

    source = _function_source(SERVICE, "_program_available")

    assert "get_hub_program(" in source
    assert "program_id=program_id" in source
    assert "firm_id=firm_id" in source
    assert "owner_id=owner_id" in source

    lookup = _function_source(SERVICE, "get_hub_program")

    assert "WHERE program_id = ?" in lookup
    assert "AND firm_id = ?" in lookup
    assert "AND owner_id = ?" in lookup
