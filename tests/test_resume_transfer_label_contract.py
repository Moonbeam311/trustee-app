from pathlib import Path


EXPECTED = {
    "templates/admin_index.html": 2,
    "templates/execution_dashboard.html": 1,
    "templates/ios_shell.html": 1,
    "templates/ios_workspaces/home.html": 1,
}


def test_resume_route_is_labeled_as_transfer_specific():
    root = Path(__file__).resolve().parents[1]

    total = 0

    for relative_path, expected_count in EXPECTED.items():
        text = (root / relative_path).read_text(
            encoding="utf-8"
        )

        new_count = text.count(
            'href="/resume">Resume Transfer</a>'
        )

        assert new_count == expected_count
        assert 'href="/resume">Resume Process</a>' not in text

        total += new_count

    assert total == 5


def test_resume_route_href_is_preserved():
    root = Path(__file__).resolve().parents[1]

    for relative_path in EXPECTED:
        text = (root / relative_path).read_text(
            encoding="utf-8"
        )

        assert 'href="/resume"' in text
