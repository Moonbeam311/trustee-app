"""One-time, non-HTTP Personal Firm initializer.

The target database must be provided with --db-path and must live outside this
Git repository. The Admin password is read without echo, or from the environment
variable named by --password-env (default: PERSONAL_FIRM_ADMIN_PASSWORD).
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_DATABASES = {
    (REPOSITORY_ROOT / "trustee_app.db").resolve(),
    (REPOSITORY_ROOT / "data" / "trustee_app.db").resolve(),
}
FORBIDDEN_PERSONAL_FIRM_IDS = {"FIRM-001", "FIRM-002", "FIRM-DEMO-001"}
AUDIT_ACTION = "personal_firm_initialized"


def _resolved_external_path(raw_path: str) -> Path:
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
    if target.exists() and not target.is_file():
        raise ValueError("database path is not a regular file")
    return target


def _existing_identity(target: Path):
    if not target.exists() or target.stat().st_size == 0:
        return None
    try:
        connection = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"app_users", "audit_log"}.issubset(tables):
            raise ValueError("refusing an existing nonempty unrecognized database")
        users = connection.execute("SELECT * FROM app_users").fetchall()
        marker = connection.execute(
            "SELECT * FROM audit_log WHERE action = ? ORDER BY id LIMIT 1", (AUDIT_ACTION,)
        ).fetchone()
        if len(users) != 1 or marker is None:
            raise ValueError("refusing an existing nonempty database without a Personal Firm marker")
        return dict(users[0])
    except sqlite3.DatabaseError as exc:
        raise ValueError("refusing an unsafe existing nonempty database") from exc
    finally:
        if "connection" in locals():
            connection.close()


def initialize_personal_firm(db_path, firm_id, username, password, owner_id=None):
    target = _resolved_external_path(str(db_path))
    firm_id = str(firm_id or "").strip()
    username = str(username or "").strip()
    owner_id = str(owner_id or "").strip()
    password = str(password or "")

    if not firm_id or firm_id in FORBIDDEN_PERSONAL_FIRM_IDS:
        raise ValueError("an explicit non-demo Personal Firm ID is required")
    if not username:
        raise ValueError("first Admin username is required")
    if not password:
        raise ValueError("Admin password must not be empty")

    existing = _existing_identity(target)
    if existing:
        existing_owner = str(existing.get("owner_id") or "").strip()
        if (
            existing.get("firm_id") != firm_id
            or existing.get("username") != username
            or (owner_id and owner_id != existing_owner)
        ):
            raise ValueError("existing Personal Firm identity does not match this invocation")
        from werkzeug.security import check_password_hash

        if not check_password_hash(existing.get("password_hash") or "", password):
            raise ValueError("existing Personal Firm credentials do not match this invocation")
        os.environ["DB_PATH"] = str(target)
        os.environ["ENSURE_HOSTED_ADMIN"] = "0"
        os.environ.pop("HOSTED_BOOTSTRAP_PASSWORD", None)
        from database import db
        db.DB_PATH = target
        db.ensure_personal_firm_recovery_table()
        return {
            "status": "already_initialized",
            "db_path": str(target),
            "owner_id": existing_owner,
            "recovery_schema_ready": True,
        }

    target.parent.mkdir(parents=True, exist_ok=True)
    owner_id = owner_id or f"OWNER-{uuid.uuid4().hex.upper()}"

    # These values are fixed before importing application database helpers so
    # hosted/demo bootstrap cannot be activated against the target.
    os.environ["DB_PATH"] = str(target)
    os.environ["ENSURE_HOSTED_ADMIN"] = "0"
    os.environ.pop("HOSTED_BOOTSTRAP_PASSWORD", None)

    from werkzeug.security import generate_password_hash
    from database import db
    db.DB_PATH = target

    db.ensure_role_tables()
    db.ensure_user_tables()
    db.ensure_user_permission_override_tables()
    db.init_audit_table()
    db.ensure_personal_firm_recovery_table()

    connection = sqlite3.connect(target)
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(audit_log)")}
        if "firm_id" not in columns:
            connection.execute("ALTER TABLE audit_log ADD COLUMN firm_id TEXT")
        connection.execute(
            """INSERT INTO app_users
               (user_id, username, password_hash, role_name, status, firm_id, owner_id)
               VALUES (?, ?, ?, 'Admin', 'active', ?, ?)""",
            (f"USER-{uuid.uuid4().hex.upper()}", username, generate_password_hash(password), firm_id, owner_id),
        )
        note = json.dumps(
            {"initializer": "personal_firm_v1", "firm_id": firm_id, "username": username, "owner_id": owner_id},
            sort_keys=True,
        )
        connection.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, note, firm_id) VALUES (?, ?, ?, ?, ?)",
            ("personal_firm", firm_id, AUDIT_ACTION, note, firm_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "status": "initialized",
        "db_path": str(target),
        "owner_id": owner_id,
        "recovery_schema_ready": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Initialize one external Personal Firm database.")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--firm-id", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--owner-id", help="Optional existing owner identity; otherwise generated safely.")
    parser.add_argument("--password-env", default="PERSONAL_FIRM_ADMIN_PASSWORD")
    args = parser.parse_args(argv)

    password = os.getenv(args.password_env)
    if password is None:
        password = getpass.getpass("First Admin password: ")
    try:
        result = initialize_personal_firm(
            args.db_path, args.firm_id, args.username, password, args.owner_id
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"Initialization refused: {exc}", file=sys.stderr)
        return 2
    print(f"Personal Firm {result['status']} at {result['db_path']}")
    print("Recovery schema ready; provision a credential separately with rotate_personal_firm_recovery.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
