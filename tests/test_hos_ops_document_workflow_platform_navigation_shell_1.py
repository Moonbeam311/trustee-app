from pathlib import Path


DOCUMENT_WORKFLOW_TEMPLATES = [
    "document_generate_form.html",
    "document_detail.html",
]


def test_document_workflow_uses_canonical_platform_navigation():
    root = Path("templates")

    dashboard = (root / "document_dashboard.html").read_text(encoding="utf-8")
    assert '{% include "_platform_shell.html" %}' in dashboard
    assert '{% include "_hindsfoot_utility_nav.html" %}' in dashboard
    assert '{% include "_platform_nav.html" %}' in dashboard

    for filename in DOCUMENT_WORKFLOW_TEMPLATES:
        text = (root / filename).read_text(encoding="utf-8")

        assert '{% include "_platform_shell.html" %}' in text, filename
        assert '{% include "_hindsfoot_utility_nav.html" %}' in text, filename
        assert '{% include "_platform_nav.html" %}' in text, filename
        assert '<div class="page-shell">' in text, filename

        # Preserve local document-workflow navigation.
        assert 'Back to Document Generator' in text, filename
        assert 'href="/documents"' in text, filename

        # Do not reintroduce the legacy global navigation row.
        assert '{% include "_nav.html" %}' not in text, filename
        assert "{% include '_nav.html' %}" not in text, filename
