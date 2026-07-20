from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def load_harness():
    path = ROOT / "scripts" / "audit_reports_pdf_runtime_repair_25am.py"
    spec = importlib.util.spec_from_file_location("system1c_r4a_step25am", path)
    if spec is None or spec.loader is None:
        raise AuditFailure(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_fixture(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(
            """
            CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, trust_name TEXT NOT NULL);
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                entity_type TEXT,
                entity_id TEXT,
                action TEXT,
                details BLOB
            );
            CREATE TABLE transfers (
                id INTEGER PRIMARY KEY,
                trust_id TEXT NOT NULL REFERENCES trusts(trust_id),
                amount REAL
            );
            CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
            CREATE VIEW active_transfers AS SELECT id, trust_id, amount FROM transfers;
            CREATE TRIGGER audit_transfer_insert
            AFTER INSERT ON transfers
            BEGIN
                INSERT INTO audit_log(entity_type, entity_id, action, details)
                VALUES ('transfer', NEW.id, 'created', NULL);
            END;
            """
        )
        connection.execute("INSERT INTO trusts VALUES (?, ?)", ("TR-001", "Fixture Trust"))
        connection.execute("INSERT INTO transfers VALUES (?, ?, ?)", (1, "TR-001", 12.5))
        connection.execute("PRAGMA schema_version=404")
        connection.commit()


def expect_failure(harness, source: dict[str, object], candidate: dict[str, object], key: str) -> None:
    failures = harness.logical_equivalence_failures(source, candidate)
    require(key in failures, f"negative contract not rejected: {key}; failures={failures}")


def main() -> int:
    harness = load_harness()
    with tempfile.TemporaryDirectory(prefix="system1c_r4a_logical_") as tmp:
        temporary_root = Path(tmp)
        source = temporary_root / "source.db"
        clone = temporary_root / "clone.db"
        make_fixture(source)
        harness.sqlite_read_only_backup(source, clone)

        with closing(sqlite3.connect(clone)) as connection:
            connection.execute("PRAGMA schema_version=1")

        source_snapshot = harness.logical_equivalence_snapshot(source)
        clone_snapshot = harness.logical_equivalence_snapshot(clone)
        require(source_snapshot["sha"] != clone_snapshot["sha"], "fixture did not produce byte-SHA difference")
        require(source_snapshot["schema_version"] != clone_snapshot["schema_version"], "fixture schema_version did not differ")
        require(not harness.logical_equivalence_failures(source_snapshot, clone_snapshot), "equivalent clone rejected")
        require(not harness.clone_preservation_failures(clone_snapshot, harness.logical_equivalence_snapshot(clone)), "read-only snapshot mutated clone")

        try:
            harness.logical_equivalence_snapshot(temporary_root / "missing.db")
        except FileNotFoundError:
            pass
        else:
            raise AuditFailure("missing clone accepted")

        bad_fk = temporary_root / "bad_fk.db"
        harness.sqlite_read_only_backup(source, bad_fk)
        with closing(sqlite3.connect(bad_fk)) as connection:
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute("INSERT INTO transfers VALUES (?, ?, ?)", (2, "TR-MISSING", 1.0))
            connection.commit()
        expect_failure(harness, source_snapshot, harness.logical_equivalence_snapshot(bad_fk), "foreign_keys")

        missing_table = temporary_root / "missing_table.db"
        harness.sqlite_read_only_backup(source, missing_table)
        with closing(sqlite3.connect(missing_table)) as connection:
            connection.execute("DROP VIEW active_transfers")
            connection.execute("DROP TRIGGER audit_transfer_insert")
            connection.execute("DROP TABLE transfers")
            connection.commit()
        candidate = harness.logical_equivalence_snapshot(missing_table)
        expect_failure(harness, source_snapshot, candidate, "schema_fingerprint")
        expect_failure(harness, source_snapshot, candidate, "user_table_counts")
        expect_failure(harness, source_snapshot, candidate, "transfers")

        changed_schema = temporary_root / "changed_schema.db"
        harness.sqlite_read_only_backup(source, changed_schema)
        with closing(sqlite3.connect(changed_schema)) as connection:
            connection.execute("CREATE INDEX idx_audit_action ON audit_log(action)")
            connection.commit()
        expect_failure(harness, source_snapshot, harness.logical_equivalence_snapshot(changed_schema), "schema_fingerprint")

        changed_count = temporary_root / "changed_count.db"
        harness.sqlite_read_only_backup(source, changed_count)
        with closing(sqlite3.connect(changed_count)) as connection:
            connection.execute("INSERT INTO audit_log(entity_type, action) VALUES ('auth', 'login')")
            connection.commit()
        candidate = harness.logical_equivalence_snapshot(changed_count)
        expect_failure(harness, source_snapshot, candidate, "user_table_counts")
        expect_failure(harness, source_snapshot, candidate, "audit_log")

        changed_digest = temporary_root / "changed_digest.db"
        harness.sqlite_read_only_backup(source, changed_digest)
        with closing(sqlite3.connect(changed_digest)) as connection:
            connection.execute("UPDATE trusts SET trust_name='Changed' WHERE trust_id='TR-001'")
            connection.commit()
        expect_failure(harness, source_snapshot, harness.logical_equivalence_snapshot(changed_digest), "critical_table_digests")

        corrupted = temporary_root / "corrupted.db"
        corrupted.write_bytes(source.read_bytes()[:512])
        try:
            harness.logical_equivalence_snapshot(corrupted)
        except sqlite3.DatabaseError:
            pass
        else:
            raise AuditFailure("integrity failure accepted")

        before = harness.logical_equivalence_snapshot(clone)
        with closing(sqlite3.connect(clone)) as connection:
            connection.execute("UPDATE trusts SET trust_name='Mutated' WHERE trust_id='TR-001'")
            connection.commit()
        changes = harness.clone_preservation_failures(before, harness.logical_equivalence_snapshot(clone))
        require("critical_table_digests" in changes, f"clone mutation not detected: {changes}")

    print("SYSTEM-1C-R4A STEP 25AM LOGICAL-EQUIVALENCE REGRESSION")
    print("Positive contracts: 8/8 PASS")
    print("Negative contracts: 10/10 rejected")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as exc:
        print(f"FAIL - {exc}")
        raise SystemExit(1)
