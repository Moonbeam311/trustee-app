from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path


REQUIRED_HEAD = "0047fc053c4dfecaa4103af9b20c3811a0f564ad"
REQUIRED_DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
REQUIRED_DB_SIZE = 3_096_576
REQUIRED_POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
REQUIRED_POLICY_SIZE = 123
REQUIRED_BACKUP_SHA = "CEEDF08EAA93F1311D0E3057CD1BF84E35EADF26D40872CF7A05F5D2D560F7BA"
REQUIRED_BACKUP_SIZE = 3_096_576
REQUIRED_SCHEMA = 404
REQUIRED_TABLES = 132
REQUIRED_AUDIT_LOG = 569
REQUIRED_TRANSFERS = 14
BACKUP_RELATIVE = Path("data/backups/trustee_app_pre_role_permission_reconcile_2026-07-15.db")


class OperationalAuthorityError(RuntimeError):
    pass


@dataclass(frozen=True)
class OperationalAuthority:
    mode: str
    repository_root: Path
    database_path: Path
    policy_path: Path
    backup_path: Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _resolve_path(raw_path: str) -> Path:
    try:
        return Path(raw_path).expanduser().resolve(strict=False)
    except OSError as exc:
        raise OperationalAuthorityError(f"TRUSTEE_OPERATIONAL_REPO cannot be resolved: {exc}") from exc


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise OperationalAuthorityError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def _require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise OperationalAuthorityError(f"{label} missing: {path}")
    if not path.is_file():
        raise OperationalAuthorityError(f"{label} is not a file: {path}")


def resolve_operational_authority(current_root: Path) -> OperationalAuthority:
    source_root = current_root.resolve()
    local_db = source_root / "trustee_app.db"
    if local_db.exists():
        local_authority = OperationalAuthority(
            mode="LOCAL_OPERATIONAL",
            repository_root=source_root,
            database_path=local_db,
            policy_path=source_root / "data" / "export_policy.json",
            backup_path=source_root / BACKUP_RELATIVE,
        )
        try:
            _require_file(local_authority.database_path, "operational DB")
            _require_file(local_authority.policy_path, "operational policy")
            _require_file(local_authority.backup_path, "required operational backup")
            validate_operational_authority(local_authority)
            return local_authority
        except OperationalAuthorityError:
            if not os.environ.get("TRUSTEE_OPERATIONAL_REPO"):
                raise

    raw_authority = os.environ.get("TRUSTEE_OPERATIONAL_REPO")
    if not raw_authority:
            raise OperationalAuthorityError(
                "local operational DB absent and TRUSTEE_OPERATIONAL_REPO not supplied"
            )
    external_root = _resolve_path(raw_authority)
    if external_root == source_root:
        raise OperationalAuthorityError("TRUSTEE_OPERATIONAL_REPO resolves to the current source repository")
    if not external_root.exists():
        raise OperationalAuthorityError(f"TRUSTEE_OPERATIONAL_REPO does not exist: {external_root}")
    if not external_root.is_dir():
        raise OperationalAuthorityError(f"TRUSTEE_OPERATIONAL_REPO is not a directory: {external_root}")
    authority = OperationalAuthority(
        mode="EXTERNAL_OPERATIONAL",
        repository_root=external_root,
        database_path=external_root / "trustee_app.db",
        policy_path=external_root / "data" / "export_policy.json",
        backup_path=external_root / BACKUP_RELATIVE,
    )

    _require_file(authority.database_path, "operational DB")
    _require_file(authority.policy_path, "operational policy")
    _require_file(authority.backup_path, "required operational backup")
    validate_operational_authority(authority)
    return authority


def sqlite_sidecars(root: Path) -> list[str]:
    sidecars: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and (path.name.endswith("-journal") or path.name.endswith("-wal") or path.name.endswith("-shm")):
            sidecars.append(path.relative_to(root).as_posix())
    return sorted(sidecars)


def authority_snapshot(authority: OperationalAuthority) -> dict[str, object]:
    db_stat = authority.database_path.stat()
    policy_stat = authority.policy_path.stat()
    backup_stat = authority.backup_path.stat()
    with sqlite3.connect(f"file:{authority.database_path.as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table' order by name")]
        snapshot: dict[str, object] = {
            "mode": authority.mode,
            "repository_root": authority.repository_root.as_posix(),
            "git_head": _git(authority.repository_root, "rev-parse", "HEAD"),
            "git_status": _git(authority.repository_root, "status", "--porcelain=v1"),
            "db_sha": sha256(authority.database_path),
            "db_size": db_stat.st_size,
            "db_mtime_ns": db_stat.st_mtime_ns,
            "policy_sha": sha256(authority.policy_path),
            "policy_size": policy_stat.st_size,
            "policy_mtime_ns": policy_stat.st_mtime_ns,
            "backup_sha": sha256(authority.backup_path),
            "backup_size": backup_stat.st_size,
            "backup_mtime_ns": backup_stat.st_mtime_ns,
            "schema_version": cur.execute("pragma schema_version").fetchone()[0],
            "table_count": len(tables),
            "audit_log": cur.execute("select count(*) from audit_log").fetchone()[0],
            "transfers": cur.execute("select count(*) from transfers").fetchone()[0],
            "integrity": cur.execute("pragma integrity_check").fetchone()[0],
            "foreign_key_rows": len(cur.execute("pragma foreign_key_check").fetchall()),
            "compliance_objects": [table for table in tables if "compliance_review" in table.lower()],
            "system_observation_objects": [table for table in tables if "system_observation" in table.lower()],
            "sidecars": sqlite_sidecars(authority.repository_root),
        }
    return snapshot


def validate_operational_snapshot(snapshot: dict[str, object]) -> None:
    expected = {
        "git_head": REQUIRED_HEAD,
        "git_status": "",
        "db_sha": REQUIRED_DB_SHA,
        "db_size": REQUIRED_DB_SIZE,
        "policy_sha": REQUIRED_POLICY_SHA,
        "policy_size": REQUIRED_POLICY_SIZE,
        "backup_sha": REQUIRED_BACKUP_SHA,
        "backup_size": REQUIRED_BACKUP_SIZE,
        "schema_version": REQUIRED_SCHEMA,
        "table_count": REQUIRED_TABLES,
        "audit_log": REQUIRED_AUDIT_LOG,
        "transfers": REQUIRED_TRANSFERS,
        "integrity": "ok",
        "foreign_key_rows": 0,
        "sidecars": [],
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            raise OperationalAuthorityError(f"operational authority {key} mismatch: {snapshot.get(key)!r}")


def validate_operational_authority(authority: OperationalAuthority) -> dict[str, object]:
    snapshot = authority_snapshot(authority)
    validate_operational_snapshot(snapshot)
    return snapshot


def active_counts(authority: OperationalAuthority) -> dict[str, object]:
    snapshot = authority_snapshot(authority)
    return {
        "audit_log": snapshot["audit_log"],
        "transfers": snapshot["transfers"],
        "schema_version": snapshot["schema_version"],
        "table_count": snapshot["table_count"],
        "compliance_objects": snapshot["compliance_objects"],
        "system_observation_objects": snapshot["system_observation_objects"],
    }


def assert_snapshot_unchanged(before: dict[str, object], after: dict[str, object]) -> None:
    keys = (
        "git_head",
        "git_status",
        "db_sha",
        "db_size",
        "db_mtime_ns",
        "policy_sha",
        "policy_size",
        "policy_mtime_ns",
        "backup_sha",
        "backup_size",
        "backup_mtime_ns",
        "schema_version",
        "table_count",
        "audit_log",
        "transfers",
        "integrity",
        "foreign_key_rows",
        "sidecars",
    )
    changed = [key for key in keys if before.get(key) != after.get(key)]
    if changed:
        raise OperationalAuthorityError(f"operational authority mutated: {changed}")
