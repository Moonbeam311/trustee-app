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


def get_archive_topology(execution_id):
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

    return {
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
