#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_DATABASES = {
    (ROOT / "data" / "trustee_app.db").resolve(),
    (ROOT / "trustee_app.db").resolve(),
}


def stop(message):
    raise SystemExit(message)


def safe_runtime_root(raw):
    root = Path(raw).expanduser().resolve()
    repo = ROOT.resolve()
    home = Path.home().resolve()

    if root == repo or repo in root.parents or root in repo.parents:
        stop("RUNTIME_ROOT_REPOSITORY_OVERLAP=PROHIBITED")
    if root == home:
        stop("RUNTIME_ROOT_HOME=PROHIBITED")
    if root == Path(root.anchor):
        stop("RUNTIME_ROOT_FILESYSTEM_ROOT=PROHIBITED")
    return root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "hos_demo_seed.json"),
    )
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    firm_id = config["firm_id"]

    if firm_id in {"FIRM-001", "FIRM-002"}:
        stop("PRODUCTION_OR_HOSTED_FIRM_SCOPE=PROHIBITED")
    if not firm_id.startswith("FIRM-DEMO-"):
        stop("DEDICATED_DEMO_FIRM_REQUIRED")

    runtime_root = safe_runtime_root(args.runtime_root)
    marker = runtime_root / ".hos_demo_runtime.json"

    if runtime_root.exists() and any(runtime_root.iterdir()):
        if not args.reset:
            stop("NONEMPTY_RUNTIME_ROOT_REQUIRES_RESET")
        if not marker.exists():
            stop("RESET_MARKER_REQUIRED")
        old = json.loads(marker.read_text(encoding="utf-8"))
        if old.get("runtime_type") != "HOS-DEMO-1":
            stop("RESET_FOREIGN_RUNTIME=PROHIBITED")
        shutil.rmtree(runtime_root)

    runtime_root.mkdir(parents=True, exist_ok=True)

    db_path = (runtime_root / "trustee_app_demo.db").resolve()
    uploads = (runtime_root / "uploads").resolve()
    exports = (runtime_root / "exports").resolve()

    if db_path in LIVE_DATABASES:
        stop("LIVE_DATABASE_TARGET=PROHIBITED")

    uploads.mkdir()
    exports.mkdir()

    marker.write_text(
        json.dumps(
            {
                "runtime_type": "HOS-DEMO-1",
                "state": "BUILDING",
                "firm_id": firm_id,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    passwords = {}
    for user in config["users"]:
        env_name = user["password_env"]
        value = os.environ.get(env_name, "")
        if len(value) < 12:
            stop(f"REQUIRED_RUNTIME_SECRET_MISSING={env_name}")
        passwords[user["user_id"]] = value

    os.environ["DB_PATH"] = str(db_path)
    os.environ["HOSTED_BOOTSTRAP_FIRM_ID"] = firm_id

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from database import db as canonical_db
    from werkzeug.security import generate_password_hash

    canonical_db.init_db()
    canonical_db.init_audit_table()
    canonical_db.ensure_role_tables()
    canonical_db.ensure_user_tables()
    canonical_db.ensure_user_permission_override_tables()
    canonical_db.ensure_firm_columns()

    conn = sqlite3.connect(str(db_path))
    try:
        for user in config["users"]:
            conn.execute(
                """
                INSERT INTO app_users
                    (user_id, username, password_hash, role_name, status, firm_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user["user_id"],
                    user["username"],
                    generate_password_hash(passwords[user["user_id"]]),
                    user["role_name"],
                    user["status"],
                    firm_id,
                ),
            )
        scenario = config["scenario"]
        trust = scenario["trust"]

        if trust["firm_id"] != firm_id:
            stop("DEMO_TRUST_FIRM_SCOPE=FAIL")

        if trust["owner_id"] != "demo-admin":
            stop("DEMO_TRUST_OWNER_SCOPE=FAIL")

        table_columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(trusts)"
            ).fetchall()
        }

        required_columns = {
            "trust_id",
            "trust_name",
            "status",
            "owner_id",
            "firm_id",
        }

        if not required_columns.issubset(table_columns):
            stop("DEMO_TRUST_SCHEMA=FAIL")

        values = {
            key: value
            for key, value in trust.items()
            if key in table_columns
        }

        columns = list(values)
        placeholders = ", ".join("?" for _ in columns)

        conn.execute(
            "INSERT INTO trusts ("
            + ", ".join(columns)
            + ") VALUES ("
            + placeholders
            + ")",
            [values[column] for column in columns],
        )

        conn.commit()

        rows = conn.execute(
            """
            SELECT username, role_name, status, firm_id
            FROM app_users
            ORDER BY username
            """
        ).fetchall()

        permission_count = conn.execute(
            "SELECT COUNT(*) FROM role_permissions"
        ).fetchone()[0]
    finally:
        conn.close()

    if len(rows) != 3:
        stop("DEMO_USER_COUNT=FAIL")
    if any(row[3] != firm_id for row in rows):
        stop("DEMO_USER_FIRM_SCOPE=FAIL")
    if {row[1] for row in rows} != {"Admin", "Trustee", "Viewer"}:
        stop("DEMO_ROLE_SET=FAIL")
    if permission_count < 1:
        stop("CANONICAL_ROLE_PERMISSION_SEED=FAIL")

    marker.write_text(
        json.dumps(
            {
                "runtime_type": "HOS-DEMO-1",
                "state": "READY",
                "firm_id": firm_id,
                "database": str(db_path),
                "uploads": str(uploads),
                "exports": str(exports),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("HOS_DEMO_SEED=PASS")
    print(f"DEMO_FIRM_ID={firm_id}")
    print("DEMO_USER_COUNT=3")
    print("DEMO_ROLE_SET=Admin,Trustee,Viewer")
    print("DEMO_TRUST_ID=" + trust["trust_id"])
    print("DEMO_SCENARIO_ID=" + scenario["scenario_id"])
    print("LIVE_DATABASE_ACCESS=NO")


if __name__ == "__main__":
    main()
