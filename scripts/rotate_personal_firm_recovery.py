"""Provision or rotate one recovery credential in an external Personal Firm DB."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_DATABASES = {
    (REPOSITORY_ROOT / "trustee_app.db").resolve(),
    (REPOSITORY_ROOT / "data" / "trustee_app.db").resolve(),
}


def _external_database(raw_path: str) -> Path:
    if not raw_path or not raw_path.strip():
        raise ValueError("--db-path is required")
    target = Path(raw_path).expanduser().resolve()
    if target in PROTECTED_DATABASES:
        raise ValueError("refusing a protected repository database path")
    try:
        target.relative_to(REPOSITORY_ROOT)
    except ValueError:
        pass
    else:
        raise ValueError("Personal Firm database must be outside the Git repository")
    if not target.is_file():
        raise ValueError("external Personal Firm database file does not exist")
    return target


def rotate_recovery(db_path, username, firm_id):
    target = _external_database(str(db_path))
    username = str(username or "").strip()
    firm_id = str(firm_id or "").strip()
    if not username or not firm_id:
        raise ValueError("explicit --username and --firm-id values are required")

    connection = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if "app_users" not in tables:
            raise ValueError("target is not a recognized Personal Firm database")
        user = connection.execute("""
            SELECT user_id, username, firm_id, status
            FROM app_users
            WHERE username = ? AND firm_id = ?
            LIMIT 1
        """, (username, firm_id)).fetchone()
        if not user or (user["status"] or "").lower() != "active":
            raise ValueError("active target user was not found in the specified firm")
        user_id = user["user_id"]
    finally:
        connection.close()

    os.environ["DB_PATH"] = str(target)
    sys.path.insert(0, str(REPOSITORY_ROOT))
    from database import db

    db.DB_PATH = target
    db.ensure_personal_firm_recovery_table()
    return db.provision_personal_firm_recovery_credential(user_id, firm_id)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Provision or rotate a local Personal Firm recovery credential."
    )
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--firm-id", required=True)
    args = parser.parse_args(argv)
    try:
        credential = rotate_recovery(args.db_path, args.username, args.firm_id)
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"Recovery credential rotation refused: {exc}", file=sys.stderr)
        return 2

    print("SECRET: RECORD THIS RECOVERY CREDENTIAL PRIVATELY. IT IS SHOWN ONCE.")
    print("Do not paste it into chat, tickets, logs, or source control.")
    print(f"Recovery identifier: {credential['recovery_id']}")
    print(f"Recovery secret: {credential['recovery_secret']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
