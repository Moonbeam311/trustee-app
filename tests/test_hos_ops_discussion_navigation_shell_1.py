from pathlib import Path


def test_discussion_subpages_use_shared_platform_navigation():
    repo = Path(__file__).resolve().parents[1]

    targets = {
        "discussion_form.html": "Back to Discussions",
        "discussion_thread.html": "Back to Discussions",
        "discussion_reply_form.html": "Back to Thread",
        "workspace_discussions.html": "Back to Workspace",
    }

    for filename, local_navigation in targets.items():
        text = (repo / "templates" / filename).read_text(encoding="utf-8")

        assert '{% include "_platform_shell.html" %}' in text
        assert '{% include "_hindsfoot_utility_nav.html" %}' in text
        assert '{% include "_platform_nav.html" %}' in text

        # Global platform navigation must not replace contextual return links.
        assert local_navigation in text


def test_platform_nav_retains_decision_destination():
    repo = Path(__file__).resolve().parents[1]
    text = (repo / "templates" / "_platform_nav.html").read_text(
        encoding="utf-8"
    )

    assert 'href="/decision"' in text
    assert ">Decision</a>" in text
