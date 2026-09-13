import os
import subprocess
import sys
import textwrap


def test_decision_rules_schema_reference_rows_and_default_engine_match(tmp_path):
    db_path = tmp_path / "finding46_decision_rules.db"

    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    code = textwrap.dedent(
        r'''
        import os
        import sqlite3

        from database.db import init_db

        init_db()

        db = os.environ["DB_PATH"]
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row

        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(decision_rules)"
            ).fetchall()
        ]

        expected_columns = [
            "rule_id",
            "goal",
            "asset_type",
            "control_level",
            "suggested_trust_type",
            "suggested_forms",
            "considerations",
            "created_at",
        ]

        assert columns == expected_columns

        rows = conn.execute(
            """
            SELECT
                rule_id,
                goal,
                asset_type,
                control_level,
                suggested_trust_type,
                suggested_forms,
                considerations
            FROM decision_rules
            ORDER BY rule_id
            """
        ).fetchall()

        assert len(rows) == 5

        expected = [
            (
                "RULE-001",
                "estate_planning",
                "general_assets",
                "high_control",
                "revocable",
                "Form 1040;Form 1041",
                "Revocable structures are often explored where flexibility and ongoing control are priorities.",
            ),
            (
                "RULE-002",
                "asset_protection",
                "real_estate",
                "reduced_personal_control",
                "irrevocable",
                "Form 1041;Form 56",
                "Irrevocable structures are often explored where stronger separation and reduced unilateral control are part of the objective.",
            ),
            (
                "RULE-003",
                "real_property_holding",
                "real_estate",
                "management_focus",
                "land",
                "Form 1041",
                "Land trust discussions often arise where title holding and real property management structure are central.",
            ),
            (
                "RULE-004",
                "insurance_planning",
                "insurance_policy",
                "reduced_personal_control",
                "insurance",
                "Form 1041",
                "Insurance trust structures are often discussed where policy ownership and insurance-related planning objectives are involved.",
            ),
            (
                "RULE-005",
                "tax_planning",
                "mixed_assets",
                "structured_control",
                "complex",
                "Form 1041;Form 1041-X;Form 8841",
                "Complex trust discussions often require careful review of distributions, retained activity, and reporting implications.",
            ),
        ]

        assert [tuple(row) for row in rows] == expected
        conn.close()

        import app

        matches = app.run_decision_engine(
            "estate_planning",
            "general_assets",
            "high_control",
        )

        assert len(matches) == 1
        assert matches[0]["rule_id"] == "RULE-001"
        assert matches[0]["suggested_trust_type"] == "revocable"
        assert matches[0]["suggested_forms"] == "Form 1040;Form 1041"

        print("FINDING_46_SUBPROCESS_CONTRACT=PASS")
        '''
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, (
        "STDOUT:\n"
        + completed.stdout
        + "\nSTDERR:\n"
        + completed.stderr
    )

    assert "FINDING_46_SUBPROCESS_CONTRACT=PASS" in completed.stdout
