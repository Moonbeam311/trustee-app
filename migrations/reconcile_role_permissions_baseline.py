"""Explicit, operator-invoked reconciliation of exact authorization duplicates."""
import argparse
import sqlite3
from pathlib import Path

INDEX_NAME = "ux_role_permissions_role_permission"

def inspect(conn):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='role_permissions'").fetchone():
        raise RuntimeError("role_permissions table is absent")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(role_permissions)")}
    if not {"id", "role_name", "permission_name"} <= cols:
        raise RuntimeError("role_permissions lacks required columns")
    if conn.execute("SELECT 1 FROM role_permissions WHERE role_name IS NULL OR permission_name IS NULL LIMIT 1").fetchone():
        raise RuntimeError("NULL values require separate operator review")
    if conn.execute("SELECT 1 FROM role_permissions WHERE role_name != trim(role_name) OR permission_name != trim(permission_name) LIMIT 1").fetchone():
        raise RuntimeError("whitespace variants require separate operator review")
    pairs = set(conn.execute("SELECT role_name,permission_name FROM role_permissions GROUP BY role_name,permission_name"))
    return conn.execute("SELECT count(*) FROM role_permissions").fetchone()[0], pairs

def reconcile(database, apply=False):
    path = Path(database).expanduser().resolve(strict=True)
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        rows, pairs = inspect(conn)
        report = dict(database=str(path), mode="apply" if apply else "dry-run",
                      original_rows=rows, distinct_pairs=len(pairs),
                      deletions=rows-len(pairs), final_rows=len(pairs), unique_index=INDEX_NAME)
        if not apply:
            return report
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("DELETE FROM role_permissions WHERE id NOT IN (SELECT min(id) FROM role_permissions GROUP BY role_name,permission_name)")
            conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME} ON role_permissions(role_name,permission_name)")
            final_rows, final_pairs = inspect(conn)
            index = next((r for r in conn.execute("PRAGMA index_list(role_permissions)") if r[1] == INDEX_NAME), None)
            index_cols = [r[2] for r in conn.execute(f"PRAGMA index_info({INDEX_NAME})")]
            if final_rows != len(pairs) or final_pairs != pairs:
                raise RuntimeError("logical-pair preservation failed")
            if index is None or index[2] != 1 or index_cols != ["role_name", "permission_name"]:
                raise RuntimeError("required unique index verification failed")
            if conn.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise RuntimeError("integrity_check failed")
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("foreign_key_check failed")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return report
    finally:
        conn.close()

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = reconcile(args.database, args.apply)
    except Exception as exc:
        print(f"role_permissions_reconciliation: FAILED ({exc})")
        return 1
    for key, value in report.items():
        print(f"{key}={value}")
    print("role_permissions_reconciliation: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
