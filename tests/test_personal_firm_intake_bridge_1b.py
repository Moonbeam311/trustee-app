import json
import sqlite3

import pytest

from database.intake_bridge_migration import (
    BRIDGE_TABLE,
    ensure_intake_bridge_table,
)
from services.services_intake_bridge import (
    IntakeBridgeError,
    attach_guided_intake,
    build_identity_carry_forward,
    create_or_reuse_guided_intake,
    establish_person_bridge,
    get_intake_bridge,
)


def make_db(tmp_path):
    db_path = tmp_path / "bridge.sqlite3"

    con = sqlite3.connect(db_path)

    con.executescript(
        """
        CREATE TABLE identity_intake (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            intake_type TEXT,
            primary_full_name TEXT,
            preferred_name TEXT,
            marital_status TEXT,
            state_jurisdiction TEXT,
            has_spouse TEXT,
            has_children TEXT,
            trustee_candidate TEXT,
            successor_trustee_candidate TEXT,
            primary_goal TEXT,
            secondary_goal TEXT,
            notes TEXT,
            completion_status TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE persons (
            person_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            sort_name TEXT,
            notes TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE intake_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            client_id TEXT,
            intake_lane TEXT NOT NULL
        );
        """
    )

    con.commit()
    con.close()

    ensure_intake_bridge_table(db_path)
    ensure_intake_bridge_table(db_path)

    return db_path


def add_focused(
    db_path,
    intake_id="FOCUSED-001",
    firm_id="FIRM-SYNTHETIC",
    name="Synthetic Person",
):
    con = sqlite3.connect(db_path)

    con.execute(
        """
        INSERT INTO identity_intake (
            intake_id,
            firm_id,
            intake_type,
            primary_full_name,
            preferred_name,
            marital_status,
            state_jurisdiction,
            has_spouse,
            has_children,
            trustee_candidate,
            successor_trustee_candidate,
            primary_goal,
            secondary_goal,
            notes,
            completion_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            intake_id,
            firm_id,
            "individual",
            name,
            "Synthetic",
            "single",
            "Synthetic State",
            "no",
            "no",
            "Do Not Carry",
            "Do Not Carry",
            "Do Not Carry",
            "Do Not Carry",
            "Do Not Carry",
            "complete",
        ),
    )

    con.commit()
    con.close()


def row_snapshot(db_path, intake_id):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    row = con.execute(
        """
        SELECT *
        FROM identity_intake
        WHERE intake_id = ?
        """,
        (intake_id,),
    ).fetchone()

    con.close()

    return dict(row)


def count_rows(db_path, table):
    con = sqlite3.connect(db_path)

    count = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    con.close()

    return count


def test_migration_is_repeat_safe_and_enforces_unique_focused(tmp_path):
    db_path = make_db(tmp_path)

    con = sqlite3.connect(db_path)

    tables = {
        row[0]
        for row in con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )
    }

    assert BRIDGE_TABLE in tables

    con.execute(
        f"""
        INSERT INTO {BRIDGE_TABLE} (
            bridge_id,
            firm_id,
            focused_intake_id,
            person_id,
            bridge_status,
            provenance_json,
            created_by,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "BRIDGE-1",
            "FIRM-SYNTHETIC",
            "FOCUSED-1",
            "PERSON-1",
            "person_linked",
            "{}",
            "tester",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            f"""
            INSERT INTO {BRIDGE_TABLE} (
                bridge_id,
                firm_id,
                focused_intake_id,
                person_id,
                bridge_status,
                provenance_json,
                created_by,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "BRIDGE-2",
                "FIRM-SYNTHETIC",
                "FOCUSED-1",
                "PERSON-2",
                "person_linked",
                "{}",
                "tester",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )

    con.close()


def test_person_bridge_is_idempotent_and_preserves_focused_row(tmp_path):
    db_path = make_db(tmp_path)
    add_focused(db_path)

    before = row_snapshot(db_path, "FOCUSED-001")

    first = establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        created_by="tester",
    )

    second = establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        created_by="tester",
    )

    after = row_snapshot(db_path, "FOCUSED-001")

    assert first["bridge_id"] == second["bridge_id"]
    assert first["person_id"] == second["person_id"]
    assert count_rows(db_path, "persons") == 1
    assert count_rows(db_path, BRIDGE_TABLE) == 1
    assert before == after


def test_same_name_does_not_trigger_person_deduplication(tmp_path):
    db_path = make_db(tmp_path)

    add_focused(
        db_path,
        intake_id="FOCUSED-001",
        name="Same Synthetic Name",
    )

    add_focused(
        db_path,
        intake_id="FOCUSED-002",
        name="Same Synthetic Name",
    )

    one = establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        created_by="tester",
    )

    two = establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-002",
        created_by="tester",
    )

    assert one["person_id"] != two["person_id"]
    assert count_rows(db_path, "persons") == 2


def test_bridge_is_firm_scoped(tmp_path):
    db_path = make_db(tmp_path)
    add_focused(db_path)

    establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        created_by="tester",
    )

    assert get_intake_bridge(
        db_path,
        "OTHER-FIRM",
        "FOCUSED-001",
    ) is None

    with pytest.raises(IntakeBridgeError):
        establish_person_bridge(
            db_path,
            owner_id="OWNER-SYNTHETIC",
            firm_id="OTHER-FIRM",
            focused_intake_id="FOCUSED-001",
            created_by="tester",
        )


def test_guided_session_is_created_once_and_client_id_stays_none(tmp_path):
    db_path = make_db(tmp_path)
    add_focused(db_path)

    establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        created_by="tester",
    )

    calls = []

    def factory(*, lane_key, client_id, created_by):
        calls.append(
            {
                "lane_key": lane_key,
                "client_id": client_id,
                "created_by": created_by,
            }
        )

        con = sqlite3.connect(db_path)

        con.execute(
            """
            INSERT INTO intake_sessions (
                intake_id,
                firm_id,
                client_id,
                intake_lane
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "GUIDED-001",
                "FIRM-SYNTHETIC",
                client_id,
                lane_key,
            ),
        )

        con.commit()
        con.close()

        return {
            "intake_id": "GUIDED-001",
            "intake_lane": lane_key,
        }

    first = create_or_reuse_guided_intake(
        db_path,
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        guided_lane_key="synthetic_lane",
        created_by="tester",
        guided_session_factory=factory,
    )

    second = create_or_reuse_guided_intake(
        db_path,
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        guided_lane_key="synthetic_lane",
        created_by="tester",
        guided_session_factory=factory,
    )

    assert first["guided_intake_id"] == "GUIDED-001"
    assert second["guided_intake_id"] == "GUIDED-001"
    assert len(calls) == 1
    assert calls[0]["client_id"] is None

    with pytest.raises(IntakeBridgeError):
        create_or_reuse_guided_intake(
            db_path,
            firm_id="FIRM-SYNTHETIC",
            focused_intake_id="FOCUSED-001",
            guided_lane_key="different_lane",
            created_by="tester",
            guided_session_factory=factory,
        )


def test_conflicting_second_guided_id_is_rejected(tmp_path):
    db_path = make_db(tmp_path)
    add_focused(db_path)

    establish_person_bridge(
        db_path,
        owner_id="OWNER-SYNTHETIC",
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        created_by="tester",
    )

    con = sqlite3.connect(db_path)

    con.executemany(
        """
        INSERT INTO intake_sessions (
            intake_id,
            firm_id,
            client_id,
            intake_lane
        )
        VALUES (?, ?, NULL, ?)
        """,
        [
            (
                "GUIDED-001",
                "FIRM-SYNTHETIC",
                "synthetic_lane",
            ),
            (
                "GUIDED-002",
                "FIRM-SYNTHETIC",
                "synthetic_lane",
            ),
        ],
    )

    con.commit()
    con.close()

    attach_guided_intake(
        db_path,
        firm_id="FIRM-SYNTHETIC",
        focused_intake_id="FOCUSED-001",
        guided_intake_id="GUIDED-001",
        guided_lane_key="synthetic_lane",
    )

    with pytest.raises(IntakeBridgeError):
        attach_guided_intake(
            db_path,
            firm_id="FIRM-SYNTHETIC",
            focused_intake_id="FOCUSED-001",
            guided_intake_id="GUIDED-002",
            guided_lane_key="synthetic_lane",
        )


def test_carry_forward_is_exact_and_provenanced():
    focused = {
        "intake_id": "FOCUSED-SYNTHETIC",
        "primary_full_name": "Synthetic Person",
        "preferred_name": "Synthetic",
        "marital_status": "single",
        "state_jurisdiction": "Synthetic State",
        "has_spouse": "no",
        "has_children": "no",
        "trustee_candidate": "EXCLUDE",
        "successor_trustee_candidate": "EXCLUDE",
        "primary_goal": "EXCLUDE",
        "secondary_goal": "EXCLUDE",
        "notes": "EXCLUDE",
    }

    result = build_identity_carry_forward(
        focused,
        {
            "primary_full_name",
            "marital_status",
            "has_children",
        },
    )

    assert result["answers"] == {
        "primary_full_name": "Synthetic Person",
        "marital_status": "single",
        "has_children": "no",
    }

    assert "preferred_name" not in result["answers"]
    assert "state_jurisdiction" not in result["answers"]
    assert "trustee_candidate" not in result["answers"]

    for key in result["answers"]:
        proof = result["provenance"][key]

        assert proof["source_model"] == "identity_intake"
        assert proof["source_intake_id"] == "FOCUSED-SYNTHETIC"
        assert proof["source_field"] == key
        assert (
            proof["carry_forward_mode"]
            == "exact_semantic_equivalence"
        )


def test_synthetic_database_quick_check(tmp_path):
    db_path = make_db(tmp_path)

    con = sqlite3.connect(db_path)
    result = con.execute("PRAGMA quick_check").fetchone()[0]
    con.close()

    assert result == "ok"
