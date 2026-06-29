import sqlite3
from datetime import datetime

from database.db import get_connection


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_execution_recovery_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_archive_repositories (
            repository_id TEXT PRIMARY KEY,
            repository_name TEXT,
            repository_type TEXT,
            storage_medium TEXT,
            geographic_region TEXT,
            repository_status TEXT DEFAULT 'pending',
            recovery_priority TEXT DEFAULT 'standard',
            replication_status TEXT DEFAULT 'not_started',
            integrity_status TEXT DEFAULT 'pending',
            last_validation_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_archive_topology (
            topology_id TEXT PRIMARY KEY,
            execution_id TEXT,
            repository_id TEXT,
            topology_role TEXT,
            current_status TEXT DEFAULT 'pending',
            last_sync_at TEXT,
            integrity_status TEXT DEFAULT 'pending',
            continuity_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_recovery_events (
            recovery_event_id TEXT PRIMARY KEY,
            execution_id TEXT,
            repository_id TEXT,
            recovery_action TEXT,
            recovery_result TEXT,
            operator TEXT,
            event_hash TEXT,
            event_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_disaster_recovery_registry (
            recovery_id TEXT PRIMARY KEY,
            execution_id TEXT,
            recovery_copy_id TEXT,
            recovery_status TEXT DEFAULT 'registered',
            recovery_repository_id TEXT,
            recovery_point_objective TEXT,
            recovery_time_objective TEXT,
            last_recovery_validation_at TEXT,
            recovery_operator TEXT,
            restore_status TEXT DEFAULT 'not_tested',
            recovery_package_hash TEXT,
            continuity_risk_level TEXT DEFAULT 'moderate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_archive_replication_ledger (
            replication_id TEXT PRIMARY KEY,
            execution_id TEXT,
            source_repository_id TEXT,
            destination_repository_id TEXT,
            replication_status TEXT DEFAULT 'registered',
            replication_result TEXT DEFAULT 'pending',
            replication_hash TEXT,
            operator TEXT,
            replicated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_integrity_revalidations (
            validation_id TEXT PRIMARY KEY,
            execution_id TEXT,
            package_id TEXT,
            validation_type TEXT,
            validation_result TEXT,
            expected_hash TEXT,
            observed_hash TEXT,
            validated_by TEXT,
            validated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def _next_id_from_cursor(cur, prefix, table, column):
    row = cur.execute(f"SELECT {column} FROM {table} ORDER BY {column} DESC LIMIT 1").fetchone()
    if not row:
        return f"{prefix}-000001"

    last = row[0] if not hasattr(row, "keys") else row[column]
    try:
        n = int(str(last).split("-")[-1]) + 1
    except Exception:
        n = 1
    return f"{prefix}-{n:06d}"


def _next_id(prefix, table, column):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(f"SELECT {column} FROM {table} ORDER BY {column} DESC LIMIT 1").fetchone()
    conn.close()

    if not row:
        return f"{prefix}-000001"

    last = row[0]
    try:
        n = int(str(last).split("-")[-1]) + 1
    except Exception:
        n = 1
    return f"{prefix}-{n:06d}"


def seed_default_archive_topology(execution_id):
    ensure_execution_recovery_tables()

    defaults = [
        ("Primary Institutional Archive", "Primary", "Digital Institutional Repository", "Institutional", "active", "critical", "current", "verified"),
        ("Secondary Digital Repository", "Secondary", "Digital Package Repository", "Institutional", "pending", "high", "not_started", "pending"),
        ("Disaster Recovery Repository", "Disaster Recovery", "Recovery Repository", "Continuity", "pending", "critical", "not_started", "pending"),
        ("Off-site Archive", "Off-site", "Geographic Redundancy Repository", "Off-site", "pending", "high", "not_started", "pending"),
        ("Cold Archive", "Cold Archive", "Cold Storage", "Long-Term", "pending", "standard", "not_started", "pending"),
        ("Air-Gapped Archive", "Air-Gapped", "Offline / Air-Gapped Storage", "Cyber Recovery", "pending", "high", "not_started", "pending"),
    ]

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for name, repo_type, medium, region, status, priority, repl, integrity in defaults:
        existing = cur.execute("""
            SELECT repository_id FROM institutional_archive_repositories
            WHERE repository_name = ? AND repository_type = ?
        """, (name, repo_type)).fetchone()

        if existing:
            repository_id = existing["repository_id"]
        else:
            repository_id = _next_id_from_cursor(cur, "REP", "institutional_archive_repositories", "repository_id")
            cur.execute("""
                INSERT INTO institutional_archive_repositories (
                    repository_id, repository_name, repository_type, storage_medium,
                    geographic_region, repository_status, recovery_priority,
                    replication_status, integrity_status, last_validation_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repository_id, name, repo_type, medium, region, status, priority,
                repl, integrity, _now() if integrity == "verified" else None,
                f"Default {repo_type} repository registered by IEL-4J-1."
            ))

        topology_exists = cur.execute("""
            SELECT topology_id FROM institutional_archive_topology
            WHERE execution_id = ? AND repository_id = ?
        """, (execution_id, repository_id)).fetchone()

        if not topology_exists:
            topology_id = _next_id_from_cursor(cur, "TOP", "institutional_archive_topology", "topology_id")
            cur.execute("""
                INSERT INTO institutional_archive_topology (
                    topology_id, execution_id, repository_id, topology_role,
                    current_status, last_sync_at, integrity_status, continuity_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topology_id, execution_id, repository_id, repo_type, status,
                _now() if status == "active" else None, integrity,
                "ready" if status == "active" and integrity == "verified" else "pending",
                f"{repo_type} archive topology record initialized."
            ))

    conn.commit()
    conn.close()


def get_archive_topology(execution_id, expected_hash=''):
    seed_default_archive_topology(execution_id)

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            t.topology_id,
            t.execution_id,
            t.repository_id,
            t.topology_role,
            t.current_status,
            t.last_sync_at,
            t.integrity_status,
            t.continuity_status,
            t.notes AS topology_notes,
            r.repository_name,
            r.repository_type,
            r.storage_medium,
            r.geographic_region,
            r.repository_status,
            r.recovery_priority,
            r.replication_status,
            r.last_validation_at,
            r.notes AS repository_notes
        FROM institutional_archive_topology t
        JOIN institutional_archive_repositories r
          ON r.repository_id = t.repository_id
        WHERE t.execution_id = ?
        ORDER BY r.repository_id
    """, (execution_id,)).fetchall()

    recovery_events = cur.execute("""
        SELECT * FROM institutional_recovery_events
        WHERE execution_id = ?
        ORDER BY event_at DESC
    """, (execution_id,)).fetchall()

    conn.close()

    topology = [dict(r) for r in rows]
    events = [dict(r) for r in recovery_events]

    total = len(topology)
    verified = sum(1 for r in topology if (r.get("integrity_status") or "").lower() == "verified")
    active = sum(1 for r in topology if (r.get("current_status") or "").lower() == "active")
    pending = sum(1 for r in topology if (r.get("current_status") or "").lower() == "pending")

    continuity_status = "Ready" if active >= 1 and total >= 3 else "Developing"
    redundancy_level = "Multi-Repository" if total >= 3 else "Single Repository"
    health_score = round((verified / total) * 100) if total else 0

    result = {
        "repositories": topology,
        "recovery_events": events,
        "summary": {
            "repositories_registered": total,
            "verified_repositories": verified,
            "active_repositories": active,
            "pending_repositories": pending,
            "continuity_status": continuity_status,
            "redundancy_level": redundancy_level,
            "repository_health_score": health_score,
            "recovery_priority": "Critical",
            "topology_status": "Registered",
        }
    }
    result["disaster_recovery"] = get_or_create_disaster_recovery_registry(execution_id, result)
    result["replication"] = get_replication_ledger(execution_id, result)
    result["revalidation"] = get_or_create_integrity_revalidation(execution_id, expected_hash=expected_hash)
    return result


def get_or_create_disaster_recovery_registry(execution_id, topology):
    ensure_execution_recovery_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    existing = cur.execute("""
        SELECT * FROM institutional_disaster_recovery_registry
        WHERE execution_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (execution_id,)).fetchone()

    if not existing:
        dr_repo = None
        for repo in topology.get("repositories", []):
            if (repo.get("topology_role") or "").lower() == "disaster recovery":
                dr_repo = repo
                break

        recovery_id = _next_id_from_cursor(cur, "DRR", "institutional_disaster_recovery_registry", "recovery_id")
        recovery_copy_id = "DRC-" + str(execution_id).replace("EXE-", "")

        cur.execute("""
            INSERT INTO institutional_disaster_recovery_registry (
                recovery_id,
                execution_id,
                recovery_copy_id,
                recovery_status,
                recovery_repository_id,
                recovery_point_objective,
                recovery_time_objective,
                last_recovery_validation_at,
                recovery_operator,
                restore_status,
                recovery_package_hash,
                continuity_risk_level,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recovery_id,
            execution_id,
            recovery_copy_id,
            "registered",
            dr_repo.get("repository_id") if dr_repo else "",
            "24 hours",
            "4 hours",
            None,
            "Institutional Operating System",
            "not_tested",
            "",
            "moderate",
            "Initial disaster recovery registry created by IEL-4J-2."
        ))
        conn.commit()

    row = cur.execute("""
        SELECT * FROM institutional_disaster_recovery_registry
        WHERE execution_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (execution_id,)).fetchone()

    events = cur.execute("""
        SELECT * FROM institutional_recovery_events
        WHERE execution_id = ?
        ORDER BY event_at DESC
    """, (execution_id,)).fetchall()

    conn.close()

    registry = dict(row) if row else {}
    event_rows = [dict(e) for e in events]

    recovery_ready = bool(registry.get("recovery_repository_id"))
    restore_tested = (registry.get("restore_status") or "").lower() in ("tested", "verified", "passed")
    risk = registry.get("continuity_risk_level") or "moderate"

    return {
        "registry": registry,
        "events": event_rows,
        "summary": {
            "recovery_ready": recovery_ready,
            "restore_tested": restore_tested,
            "recovery_status": registry.get("recovery_status") or "unregistered",
            "restore_status": registry.get("restore_status") or "not_tested",
            "continuity_risk_level": risk,
            "recovery_copy_id": registry.get("recovery_copy_id") or "",
            "recovery_point_objective": registry.get("recovery_point_objective") or "",
            "recovery_time_objective": registry.get("recovery_time_objective") or "",
        }
    }


def seed_replication_ledger(execution_id, topology):
    ensure_execution_recovery_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    repositories = topology.get("repositories", [])
    primary = None
    for repo in repositories:
        if (repo.get("topology_role") or "").lower() == "primary":
            primary = repo
            break

    if not primary:
        conn.close()
        return

    for repo in repositories:
        if repo.get("repository_id") == primary.get("repository_id"):
            continue

        existing = cur.execute("""
            SELECT replication_id
            FROM institutional_archive_replication_ledger
            WHERE execution_id = ?
              AND source_repository_id = ?
              AND destination_repository_id = ?
            LIMIT 1
        """, (
            execution_id,
            primary.get("repository_id"),
            repo.get("repository_id"),
        )).fetchone()

        if existing:
            continue

        replication_id = _next_id_from_cursor(cur, "REPLOG", "institutional_archive_replication_ledger", "replication_id")

        cur.execute("""
            INSERT INTO institutional_archive_replication_ledger (
                replication_id,
                execution_id,
                source_repository_id,
                destination_repository_id,
                replication_status,
                replication_result,
                replication_hash,
                operator,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            replication_id,
            execution_id,
            primary.get("repository_id"),
            repo.get("repository_id"),
            "registered",
            "pending",
            "",
            "Institutional Operating System",
            f"Replication path registered from {primary.get('repository_name')} to {repo.get('repository_name')}."
        ))

    conn.commit()
    conn.close()


def get_replication_ledger(execution_id, topology):
    seed_replication_ledger(execution_id, topology)

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            l.replication_id,
            l.execution_id,
            l.source_repository_id,
            src.repository_name AS source_repository_name,
            l.destination_repository_id,
            dst.repository_name AS destination_repository_name,
            dst.repository_type AS destination_repository_type,
            l.replication_status,
            l.replication_result,
            l.replication_hash,
            l.operator,
            l.replicated_at,
            l.notes
        FROM institutional_archive_replication_ledger l
        LEFT JOIN institutional_archive_repositories src
          ON src.repository_id = l.source_repository_id
        LEFT JOIN institutional_archive_repositories dst
          ON dst.repository_id = l.destination_repository_id
        WHERE l.execution_id = ?
        ORDER BY l.replication_id
    """, (execution_id,)).fetchall()

    conn.close()

    items = [dict(r) for r in rows]
    total = len(items)
    completed = sum(1 for r in items if (r.get("replication_result") or "").lower() in ("completed", "verified", "pass"))
    pending = sum(1 for r in items if (r.get("replication_result") or "").lower() == "pending")
    failed = sum(1 for r in items if (r.get("replication_result") or "").lower() in ("failed", "fail"))

    return {
        "items": items,
        "summary": {
            "replication_paths": total,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "replication_status": "Registered" if total else "Not Registered",
            "replication_readiness": "Ready" if total and failed == 0 else "Review Required",
        }
    }


def _package_id_from_execution(execution_id):
    return "PKG-" + str(execution_id).replace("EXE-", "")


def get_or_create_integrity_revalidation(execution_id, expected_hash="", observed_hash=None, validation_type="baseline"):
    ensure_execution_recovery_tables()

    if observed_hash is None:
        observed_hash = expected_hash

    package_id = _package_id_from_execution(execution_id)
    result = "pass" if expected_hash and observed_hash and expected_hash == observed_hash else "review_required"

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    existing = cur.execute("""
        SELECT *
        FROM institutional_integrity_revalidations
        WHERE execution_id = ?
          AND validation_type = ?
        ORDER BY validated_at DESC
        LIMIT 1
    """, (execution_id, validation_type)).fetchone()

    if not existing:
        validation_id = _next_id_from_cursor(cur, "VAL", "institutional_integrity_revalidations", "validation_id")
        cur.execute("""
            INSERT INTO institutional_integrity_revalidations (
                validation_id,
                execution_id,
                package_id,
                validation_type,
                validation_result,
                expected_hash,
                observed_hash,
                validated_by,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            validation_id,
            execution_id,
            package_id,
            validation_type,
            result,
            expected_hash,
            observed_hash,
            "Institutional Revalidation Engine",
            "Baseline integrity revalidation created by IEL-4J-4."
        ))
        conn.commit()

    rows = cur.execute("""
        SELECT *
        FROM institutional_integrity_revalidations
        WHERE execution_id = ?
        ORDER BY validated_at DESC
    """, (execution_id,)).fetchall()

    conn.close()

    items = [dict(r) for r in rows]
    total = len(items)
    passed = sum(1 for r in items if (r.get("validation_result") or "").lower() == "pass")
    review = sum(1 for r in items if (r.get("validation_result") or "").lower() != "pass")

    latest = items[0] if items else {}

    return {
        "items": items,
        "latest": latest,
        "summary": {
            "validations_recorded": total,
            "passed": passed,
            "review_required": review,
            "latest_result": (latest.get("validation_result") or "not_validated").replace("_", " ").title(),
            "validation_status": "Validated" if total and review == 0 else "Review Required",
            "expected_hash": expected_hash,
            "observed_hash": observed_hash,
        }
    }
