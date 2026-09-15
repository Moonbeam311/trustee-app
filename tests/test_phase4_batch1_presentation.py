"""Static regression coverage for Phase 4 Batch 1 presentation cleanup."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT / "templates" / "ios_workspaces"
WORKSPACES = (
    "library",
    "administer",
    "home",
    "legacy",
    "create",
    "governance",
    "compliance",
    "archive",
    "reports",
    "developer",
)

PRESERVED_DESTINATIONS = {
    "administer": (
        'href="#trust-registry"',
        'href="/matters"',
        'href="/assets"',
        'href="#funding"',
        'href="/execution"',
        "href=\"{{ url_for('trust_minutes_dashboard') }}\"",
        'href="/certificates"',
        'href="#relationships"',
        'href="/admin"',
    ),
    "home": (
        'href="/resume"',
        "href=\"{{ url_for('intake_dashboard') }}\"",
        "href=\"{{ url_for('create_trust_launch') }}\"",
        "href=\"{{ url_for('system_health_dashboard') }}\"",
        'href="/admin"',
        'href="/admin/workspace/create"',
        'href="/admin/workspace/administer"',
        'href="/admin/workspace/reports"',
        'href="/admin/workspace/system"',
    ),
    "create": (
        "href=\"{{ url_for('create_trust_launch') }}\"",
        "href=\"{{ url_for('intake_dashboard') }}\"",
        'href="/intake"',
        'href="/instruments"',
        'href="/documents/generate"',
        'href="/admin/workspace/home"',
        'href="/admin/workspace/create"',
        'href="/admin/workspace/administer"',
        'href="/admin"',
    ),
    "governance": (
        'href="/governance/directives/new"',
        'href="/governance/policies/new"',
        'href="/governance"',
        'href="/governance/dashboard"',
        'href="/governance/relationship-lifecycle"',
        'href="/governance/evidence-exports"',
        'href="/governance/v2-certification"',
        'href="/governance/v2-certification.txt"',
        'href="/admin"',
    ),
    "compliance": ('href="{{ url_for("compliance_review_registry") }}"',),
    "archive": (
        'href="/governance/evidence-exports"',
        'href="/governance/v2-certification"',
        'href="/continuity/certificates/verify"',
        'href="/admin/backup/database.zip"',
        'href="/admin"',
    ),
    "reports": (
        'href="/financial_summary"',
        'href="/portfolio"',
        'href="/reports/portfolio.pdf"',
        'href="/audit"',
        'href="/reports/audit.pdf"',
        'href="/visualization/analytics"',
        'href="/exports"',
        'href="/certificates"',
        'href="/governance/v2-certification"',
    ),
    "developer": ('href="/admin"',),
}


def workspace(name):
    return (WORKSPACE_DIR / f"{name}.html").read_text(encoding="utf-8")


def test_batch1_workspace_templates_exist():
    assert all((WORKSPACE_DIR / f"{name}.html").is_file() for name in WORKSPACES)


def test_stale_batch1_presentation_wording_is_absent():
    combined = "\n".join(workspace(name) for name in WORKSPACES)
    stale_phrases = (
        "ADR-9B placeholder",
        "Existing routes remain active while this workspace is migrated",
        "V2 Certification Record",
        "Legacy Admin Dashboard",
        "route spine",
        "grouped here for migration",
        "Activity feed placeholder",
        "IIA-1 through IIA-4 architecture approved",
        "IOS-2 workspace migration engine started",
        "HOME workspace migrated",
        "IOS-3A governance records begin here",
        "Future Creation Modules",
        "Queued",
        "not activated in this milestone",
        "no migration occurred",
    )
    for phrase in stale_phrases:
        assert phrase not in combined


def test_critical_destinations_remain_present():
    for name, destinations in PRESERVED_DESTINATIONS.items():
        content = workspace(name)
        for destination in destinations:
            assert destination in content


def test_planned_creation_modules_remain_inactive_without_links():
    content = workspace("create")
    planned = content.split("Planned Creation Modules", 1)[1].split("</section>", 1)[0]
    for module in ("ILIT", "Dynasty", "Pet Trust", "Firearms"):
        assert module in planned
    assert planned.count("Planned — Not Active") == 4
    assert "<a " not in planned
    assert "href=" not in planned


def test_compliance_remains_read_only_and_inactive():
    content = workspace("compliance")
    lowered = content.lower()
    assert "read-only" in lowered
    assert "not active" in lowered
    assert "does not provide a control to create or activate" in lowered
    assert "<form" not in lowered
    assert 'method="post"' not in lowered
    assert lowered.count("href=") == 1


def test_developer_remains_restricted_by_shared_master_admin_gate():
    developer = workspace("developer")
    assert "restricted developer and diagnostic information" in developer.lower()
    assert "authorized master administrators" in developer.lower()
    assert developer.count("href=") == 1

    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    gate = 'if workspace_key == "developer":\n        gate = require_master_admin()'
    assert gate in app_source
