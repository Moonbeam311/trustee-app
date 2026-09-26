"""Canonical, non-dispositive property attestations and identification history."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path


class PropertyFactServiceError(RuntimeError):
    pass


def _connection(db_path):
    connection = sqlite3.connect(str(Path(db_path)))
    connection.row_factory = sqlite3.Row
    return connection


def _required(data, names):
    missing = [name for name in names if data.get(name) in (None, "")]
    if missing:
        raise PropertyFactServiceError("Required property fact fields: " + ", ".join(missing))


def _validate_property_scope(connection, property_id, trust_id, firm_id):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(properties)")}
    if not {"property_id", "trust_id", "firm_id"}.issubset(columns):
        raise PropertyFactServiceError("Properties schema does not support firm/trust scoping.")
    row = connection.execute(
        "SELECT 1 FROM properties WHERE property_id=? AND trust_id=? AND firm_id=?",
        (property_id, trust_id, firm_id),
    ).fetchone()
    if row is None:
        raise PropertyFactServiceError("Property is not in the supplied firm/trust scope.")


def create_property_attestation(db_path, payload):
    data = dict(payload or {})
    data.setdefault("attestation_id", f"PAT-{uuid.uuid4().hex.upper()}")
    data.setdefault("status", "recorded")
    required = ("attestation_id", "property_id", "trust_id", "firm_id", "attestation_type",
                "subject_field_or_fact", "attested_value", "actor_id", "actor_capacity", "basis", "attested_at", "status")
    _required(data, required)
    if data["attestation_type"] not in {"possession", "ownership"}:
        raise PropertyFactServiceError("Attestation type must be possession or ownership.")
    connection = _connection(db_path)
    try:
        _validate_property_scope(connection, data["property_id"], data["trust_id"], data["firm_id"])
        supersedes_id = data.get("supersedes_attestation_id")
        if supersedes_id:
            prior = connection.execute(
                """SELECT property_id, trust_id, firm_id, attestation_type, subject_field_or_fact
                   FROM property_attestations WHERE attestation_id=?""",
                (supersedes_id,),
            ).fetchone()
            if prior is None:
                raise PropertyFactServiceError("Superseded attestation does not exist.")
            dimensions = (
                "property_id", "trust_id", "firm_id", "attestation_type", "subject_field_or_fact"
            )
            if any(prior[name] != data[name] for name in dimensions):
                raise PropertyFactServiceError(
                    "Superseded attestation must have the same property, trust, firm, type, and subject."
                )
        connection.execute(
            """INSERT INTO property_attestations
            (attestation_id,property_id,trust_id,firm_id,attestation_type,subject_field_or_fact,
             attested_value,actor_id,actor_capacity,basis,attested_at,status,supersedes_attestation_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(data.get(name) for name in required) + (supersedes_id,),
        )
        connection.commit()
        return dict(connection.execute("SELECT * FROM property_attestations WHERE attestation_id=?", (data["attestation_id"],)).fetchone())
    except sqlite3.Error as exc:
        connection.rollback()
        raise PropertyFactServiceError(str(exc)) from exc
    finally:
        connection.close()


def list_property_attestations(db_path, property_id, trust_id, firm_id, attestation_type=None):
    connection = _connection(db_path)
    try:
        _validate_property_scope(connection, property_id, trust_id, firm_id)
        sql = "SELECT * FROM property_attestations WHERE property_id=? AND trust_id=? AND firm_id=?"
        params = [property_id, trust_id, firm_id]
        if attestation_type:
            sql += " AND attestation_type=?"
            params.append(attestation_type)
        return [dict(row) for row in connection.execute(sql + " ORDER BY created_at, attestation_id", params)]
    finally:
        connection.close()


def list_current_property_attestations(
    db_path, property_id, trust_id, firm_id, attestation_type=None
):
    connection = _connection(db_path)
    try:
        _validate_property_scope(connection, property_id, trust_id, firm_id)
        sql = """SELECT current.* FROM property_attestations AS current
                 WHERE current.property_id=? AND current.trust_id=? AND current.firm_id=?
                   AND NOT EXISTS (
                       SELECT 1 FROM property_attestations AS later
                       WHERE later.supersedes_attestation_id=current.attestation_id
                   )"""
        params = [property_id, trust_id, firm_id]
        if attestation_type:
            sql += " AND current.attestation_type=?"
            params.append(attestation_type)
        return [
            dict(row)
            for row in connection.execute(sql + " ORDER BY current.created_at, current.attestation_id", params)
        ]
    finally:
        connection.close()


def create_property_identification_revision(db_path, payload):
    data = dict(payload or {})
    data.setdefault("revision_id", f"PIR-{uuid.uuid4().hex.upper()}")
    data.setdefault("status", "recorded")
    required = ("revision_id", "property_id", "trust_id", "firm_id", "prior_identification_json",
                "resulting_identification_json", "revision_basis", "actor_id", "actor_capacity", "status")
    _required(data, required)
    for field in ("prior_identification_json", "resulting_identification_json"):
        if not isinstance(data[field], str):
            data[field] = json.dumps(data[field], sort_keys=True)
        try:
            json.loads(data[field])
        except (TypeError, ValueError) as exc:
            raise PropertyFactServiceError(f"{field} must contain valid JSON.") from exc
    connection = _connection(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _validate_property_scope(connection, data["property_id"], data["trust_id"], data["firm_id"])
        number = connection.execute(
            """SELECT COALESCE(MAX(revision_number),0)+1
               FROM property_identification_revisions
               WHERE property_id=? AND trust_id=? AND firm_id=?""",
            (data["property_id"], data["trust_id"], data["firm_id"]),
        ).fetchone()[0]
        values = (data["revision_id"], data["property_id"], data["trust_id"], data["firm_id"], number,
                  data["prior_identification_json"], data["resulting_identification_json"], data["revision_basis"],
                  data["actor_id"], data["actor_capacity"], data["status"])
        connection.execute("""INSERT INTO property_identification_revisions
            (revision_id,property_id,trust_id,firm_id,revision_number,prior_identification_json,
             resulting_identification_json,revision_basis,actor_id,actor_capacity,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", values)
        connection.commit()
        return dict(connection.execute("SELECT * FROM property_identification_revisions WHERE revision_id=?", (data["revision_id"],)).fetchone())
    except sqlite3.Error as exc:
        connection.rollback()
        raise PropertyFactServiceError(str(exc)) from exc
    finally:
        connection.close()


def list_property_identification_revisions(db_path, property_id, trust_id, firm_id):
    connection = _connection(db_path)
    try:
        _validate_property_scope(connection, property_id, trust_id, firm_id)
        return [dict(row) for row in connection.execute(
            """SELECT * FROM property_identification_revisions
               WHERE property_id=? AND trust_id=? AND firm_id=? ORDER BY revision_number""",
            (property_id, trust_id, firm_id),
        )]
    finally:
        connection.close()


def get_latest_property_identification_revision(db_path, property_id, trust_id, firm_id):
    connection = _connection(db_path)
    try:
        _validate_property_scope(connection, property_id, trust_id, firm_id)
        row = connection.execute(
            """SELECT * FROM property_identification_revisions
               WHERE property_id=? AND trust_id=? AND firm_id=?
               ORDER BY revision_number DESC LIMIT 1""",
            (property_id, trust_id, firm_id),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        connection.close()
