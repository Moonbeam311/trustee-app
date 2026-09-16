import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IOS_WORKSPACE = ROOT / "templates" / "ios_workspace.html"
IOS_SHELL = ROOT / "templates" / "_ios_shell.html"
PLATFORM_NAV = ROOT / "templates" / "_platform_nav.html"

def read(path):
    return path.read_text(encoding="utf-8")


def test_ios_workspace_uses_only_the_ios_navigation_presentation():
    workspace = read(IOS_WORKSPACE)

    assert '{% include "_platform_nav.html" %}' not in workspace
    assert '{% include "_ios_shell.html" %}' in workspace
    assert "Platform Navigation" not in workspace


def test_platform_navigation_partial_is_present_and_unchanged():
    assert PLATFORM_NAV.is_file()
    assert subprocess.run(
        ["git", "diff", "--quiet", "--", "templates/_platform_nav.html"],
        cwd=ROOT,
    ).returncode == 0


def test_ios_shell_preserves_all_ios_destinations():
    shell = read(IOS_SHELL)
    expected = {
        "HOME": "/admin/workspace/home",
        "CREATE": "/admin/workspace/create",
        "PEOPLE": "/admin/workspace/people",
        "GOVERNANCE": "/admin/workspace/governance",
        "GOVERNANCE REGISTRY": "/governance",
        "COMPLIANCE": "/admin/workspace/compliance",
        "LIBRARY": "/admin/workspace/library",
        "RESEARCH": "/admin/workspace/research",
        "ARCHIVE": "/admin/workspace/archive",
        "SYSTEM": "/admin/workspace/system",
        "DEVELOPER": "/admin/workspace/developer",
        "LOGOUT": "/logout",
    }

    for label, href in expected.items():
        assert f'<a href="{href}">{label}</a>' in shell


def test_ios_shell_preserves_platform_destinations_and_conditionals():
    shell = read(IOS_SHELL)
    expected = {
        "Work &amp; Learning Hub": "/work-learning-hub",
        "Learning": "/learning",
        "Videos": "/videos",
        "Workspace": "/workspaces",
        "Discussions": "/discussions",
        "Decision": "/decision",
        "Documents": "/documents",
        "Visualization": "/visualization",
    }

    for label, href in expected.items():
        assert f'<a href="{href}">{label}</a>' in shell

    assert 'session.get("role") == "Admin"' in shell
    assert 'session.get("role") in ["Admin", "Trustee"]' in shell
    assert 'session.get("role") in ["Admin", "Trustee", "Viewer"]' in shell
    assert "url_for('trust_execution_dashboard', trust_id=trust.trust_id)" in shell
    assert "url_for('trust_execution_dashboard', trust_id=trust_id)" in shell
    assert '<a href="/execution">Execution</a>' in shell


def test_semantically_overlapping_routes_remain_distinct():
    shell = read(IOS_SHELL)

    assert '<a href="/admin/workspace/administer">ADMINISTER</a>' in shell
    assert '<a href="/admin">Admin</a>' in shell
    assert '<a href="/admin/workspace/reports">REPORTS</a>' in shell
    assert '<a href="/reports">Reports</a>' in shell
    assert '<a href="/admin/workspace/legacy">LEGACY</a>' in shell
    assert "url_for('genealogy_legacy_workspace')" in shell
    assert "Genealogy &amp; Legacy" in shell


def test_ios_shell_is_one_navigation_container_without_platform_block():
    shell = read(IOS_SHELL)

    assert shell.count('class="admin-actions ios-workspace-nav"') == 1
    assert shell.count("<nav") == 0
    assert "Platform Navigation" not in shell


def test_governance_registry_handoff_remains_unchanged():
    shell = read(IOS_SHELL)

    assert '<a href="/governance">GOVERNANCE REGISTRY</a>' in shell
