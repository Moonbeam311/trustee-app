"""TPD-1C service boundary for the governed formation bridge and continuity pilot."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import UTC, datetime

from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge

WORKFLOW = "declaration_of_trust"
COMPLETE_INTAKE_STATUSES = {"scored", "snapshot_saved", "completed"}
BLOCKING_REVIEW_STATUSES = {"open", "escalated"}
BLOCKING_REVIEW_SEVERITIES = {"critical", "major"}
REQUIRED_FIELDS = (
    "trust_name", "short_name", "jurisdiction", "effective_date", "trust_type",
    "trust_purpose", "accounting_method", "workflow_mode", "grantor_name",
    "grantor_type", "settlor_name", "trustee_name", "successor_trustee_name",
    "beneficiary_name", "record_visibility", "workflow_mode_confirmed",
    "ai_explanations", "recommended_guidance", "initial_corpus_description",
    "property_mapping_timing", "asset_categories", "generate_schedule_recommendations",
)
FORMATION_FIELD_CONTROLS = {
    "trust_name": {"label": "Trust name", "type": "text"},
    "short_name": {"label": "Short name", "type": "text"},
    "jurisdiction": {"label": "Jurisdiction", "type": "text"},
    "effective_date": {"label": "Effective date", "type": "date"},
    "trust_type": {"label": "Trust type", "type": "text"},
    "trust_purpose": {"label": "Trust purpose", "type": "text"},
    "accounting_method": {"label": "Accounting method", "type": "select", "choices": (("cash", "Cash method"), ("accrual", "Accrual method"))},
    "workflow_mode": {"label": "Workflow mode", "type": "select", "choices": (("private_office", "Private Office Mode"), ("public_filing", "Public Filing / External Mode"))},
    "grantor_name": {"label": "Grantor name", "type": "text"},
    "grantor_type": {"label": "Grantor type", "type": "text"},
    "grantor_contact": {"label": "Grantor contact", "type": "text"},
    "settlor_name": {"label": "Settlor name", "type": "text"},
    "trustee_name": {"label": "Trustee name", "type": "text"},
    "successor_trustee_name": {"label": "Successor trustee name", "type": "text"},
    "beneficiary_name": {"label": "Beneficiary name", "type": "text"},
    "record_visibility": {"label": "Default record visibility", "type": "select", "choices": (("private", "Private"), ("internal", "Internal"), ("public_facing", "Public-facing"))},
    "workflow_mode_confirmed": {"label": "Workflow mode confirmation", "type": "select", "choices": (("private_office", "Private Office Mode"), ("public_filing", "Public Filing / External Mode"))},
    "ai_explanations": {"label": "AI explanation layer", "type": "select", "choices": (("enabled", "Enabled"), ("disabled", "Disabled"))},
    "recommended_guidance": {"label": "Recommended administrative/tax guidance", "type": "select", "choices": (("enabled", "Enabled"), ("disabled", "Disabled"))},
    "initial_corpus_description": {"label": "Initial corpus description", "type": "text"},
    "property_mapping_timing": {"label": "Property mapping timing", "type": "select", "choices": (("now", "Map property now"), ("later", "Map property later"))},
    "asset_categories": {"label": "Asset categories", "type": "text"},
    "generate_schedule_recommendations": {"label": "Generate initial schedule recommendations", "type": "select", "choices": (("yes", "Yes"), ("no", "No"))},
}
PROHIBITED_SECRET_NAMES = {
    "password", "password_value", "pin", "token", "recovery_code", "secret_answer",
    "encryption_key", "card_number", "cvv",
}
SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)\b(password|passcode|recovery code|secret answer|private key)\s*[:=]"),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
)


class BridgeError(ValueError):
    pass


def _now():
    return datetime.now(UTC).isoformat()


def _id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _connect(db_path):
    connection = sqlite3.connect(str(db_path), timeout=30, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _event(conn, bridge, event_type, actor, basis="", previous=None, new=None):
    conn.execute("""
        INSERT INTO intake_trust_formation_bridge_events
        (event_id, bridge_id, firm_id, event_type, actor_id, event_basis,
         previous_state_json, new_state_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (_id("BFE"), bridge["bridge_id"], bridge["firm_id"], event_type, actor,
          basis, _json(previous) if previous is not None else None,
          _json(new) if new is not None else None, _now()))


def _table_exists(conn, table):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _recommendation(conn, firm_id, intake_id, workflow_key):
    return conn.execute("""
        SELECT id, intake_id, firm_id, workflow_key, title, reason, status,
               created_at, updated_at, created_by
        FROM intake_document_recommendations
        WHERE firm_id=? AND intake_id=? AND workflow_key=? LIMIT 1
    """, (firm_id, intake_id, workflow_key)).fetchone()


def evaluate_eligibility(db_path, firm_id, intake_id, workflow_key=WORKFLOW):
    conn = _connect(db_path)
    try:
        if workflow_key != WORKFLOW:
            return {"eligible": False, "reasons": ["Unsupported workflow."], "blocking_issue_count": 0}
        recommendation = _recommendation(conn, firm_id, intake_id, workflow_key)
        intake = conn.execute(
            "SELECT intake_id, status, updated_at FROM intake_sessions WHERE firm_id=? AND intake_id=?",
            (firm_id, intake_id),
        ).fetchone()
        reasons = []
        if not recommendation:
            reasons.append("Recommendation not found in the current firm.")
        elif recommendation["status"] != "accepted":
            reasons.append("Recommendation must be accepted.")
        if not intake:
            reasons.append("Intake not found in the current firm.")
        elif intake["status"] not in COMPLETE_INTAKE_STATUSES:
            reasons.append("Intake is not in an evidence-supported completed state.")
        completion = None
        if _table_exists(conn, "intake_final_draft_completion_gate"):
            completion = conn.execute("""
                SELECT gate_status, document_key FROM intake_final_draft_completion_gate
                WHERE firm_id=? AND intake_id=? AND workflow_key=?
                ORDER BY updated_at DESC LIMIT 1
            """, (firm_id, intake_id, workflow_key)).fetchone()
        if not completion or completion["gate_status"] != "completed_preparation":
            reasons.append("Final-draft preparation must be completed; this is not legal or execution approval.")
        blocking = 0
        if _table_exists(conn, "professional_review_issues"):
            blocking = conn.execute("""
                SELECT COUNT(*) FROM professional_review_issues
                WHERE firm_id=? AND intake_id=? AND workflow_key=?
                  AND status IN ('open','escalated') AND severity IN ('critical','major')
            """, (firm_id, intake_id, workflow_key)).fetchone()[0]
        if blocking:
            reasons.append("Blocking professional-review issues remain unresolved.")
        return {"eligible": not reasons, "reasons": reasons, "recommendation": dict(recommendation) if recommendation else None,
                "intake": dict(intake) if intake else None, "completion": dict(completion) if completion else None,
                "blocking_issue_count": blocking}
    finally:
        conn.close()


def _source_values(conn, firm_id, intake_id):
    bridge_answers = {}
    if _table_exists(conn, "intake_workflow_bridge_answers"):
        rows = conn.execute("""
            SELECT question_key, answer_key, answer_label, updated_at
            FROM intake_workflow_bridge_answers
            WHERE firm_id=? AND intake_id=? AND workflow_key=? ORDER BY id
        """, (firm_id, intake_id, WORKFLOW)).fetchall()
        for row in rows:
            bridge_answers.setdefault(row["question_key"], []).append(row["answer_label"] or row["answer_key"] or "")
    intake_answers = {}
    if _table_exists(conn, "intake_answers"):
        rows = conn.execute("""
            SELECT question_key, answer_key, answer_label, created_at
            FROM intake_answers WHERE firm_id=? AND intake_id=? ORDER BY id
        """, (firm_id, intake_id)).fetchall()
        for row in rows:
            intake_answers.setdefault(row["question_key"], []).append(row["answer_label"] or row["answer_key"] or "")
    return bridge_answers, intake_answers


def _proposal_specs(bridge_answers, intake_answers):
    one = lambda values, key: "; ".join(values.get(key, []))
    assets = one(intake_answers, "asset_categories") or one(intake_answers, "assets_owned")
    return {
        "trust_name": (1, "intake_workflow_bridge_answers", "trust_name", "USER_ASSERTED_FACT", one(bridge_answers, "trust_name"), "PREFILL_EDITABLE"),
        "short_name": (1, "operator", "short_name", "NO_RELIABLE_SOURCE", "", "REQUIRE_NEW_ENTRY"),
        "jurisdiction": (1, "operator", "jurisdiction", "NO_RELIABLE_SOURCE", "", "REQUIRE_NEW_ENTRY"),
        "effective_date": (1, "operator", "effective_date", "NO_RELIABLE_SOURCE", "", "REQUIRE_NEW_ENTRY"),
        "trust_type": (2, "intake_workflow_bridge_answers", "trust_type", "USER_PREFERENCE", one(bridge_answers, "trust_type"), "PREFILL_LOCKED_PENDING_OVERRIDE"),
        "trust_purpose": (2, "intake_workflow_bridge_answers", "trust_purpose", "USER_PREFERENCE", one(bridge_answers, "trust_purpose"), "PREFILL_EDITABLE"),
        "accounting_method": (2, "operator", "accounting_method", "NO_RELIABLE_SOURCE", "", "REQUIRE_NEW_ENTRY"),
        "workflow_mode": (2, "operator", "workflow_mode", "OPERATOR_DECISION", "", "REQUIRE_NEW_ENTRY"),
        "grantor_name": (2, "intake_workflow_bridge_answers", "trust_parties", "USER_ASSERTED_FACT", "", "REQUIRE_NEW_ENTRY"),
        "grantor_type": (2, "operator", "grantor_type", "NO_RELIABLE_SOURCE", "", "REQUIRE_NEW_ENTRY"),
        "grantor_contact": (2, "operator", "grantor_contact", "NO_RELIABLE_SOURCE", "", "REQUIRE_NEW_ENTRY"),
        "settlor_name": (3, "intake_workflow_bridge_answers", "trust_parties", "USER_ASSERTED_FACT", "", "REQUIRE_NEW_ENTRY"),
        "trustee_name": (3, "intake_workflow_bridge_answers", "trust_parties", "USER_ASSERTED_FACT", "", "REQUIRE_NEW_ENTRY"),
        "successor_trustee_name": (3, "intake_workflow_bridge_answers", "trust_parties", "USER_ASSERTED_FACT", "", "REQUIRE_NEW_ENTRY"),
        "beneficiary_name": (3, "intake_workflow_bridge_answers", "trust_parties", "USER_ASSERTED_FACT", "", "REQUIRE_NEW_ENTRY"),
        "record_visibility": (4, "operator", "record_visibility", "OPERATOR_DECISION", "", "REQUIRE_NEW_ENTRY"),
        "workflow_mode_confirmed": (4, "operator", "workflow_mode_confirmed", "OPERATOR_DECISION", "", "REQUIRE_CONFIRMATION"),
        "ai_explanations": (4, "operator", "ai_explanations", "USER_PREFERENCE", "", "REQUIRE_NEW_ENTRY"),
        "recommended_guidance": (4, "operator", "recommended_guidance", "USER_PREFERENCE", "", "REQUIRE_NEW_ENTRY"),
        "initial_corpus_description": (5, "intake_workflow_bridge_answers", "initial_property", "DERIVED_VALUE", "", "REQUIRE_NEW_ENTRY"),
        "property_mapping_timing": (5, "operator", "property_mapping_timing", "OPERATOR_DECISION", "", "REQUIRE_NEW_ENTRY"),
        "asset_categories": (5, "intake_answers", "asset_categories", "USER_ASSERTED_FACT", assets, "PREFILL_EDITABLE"),
        "generate_schedule_recommendations": (5, "operator", "generate_schedule_recommendations", "USER_PREFERENCE", "", "REQUIRE_CONFIRMATION"),
    }


def prepare_bridge(db_path, firm_id, intake_id, actor, matter_id=None):
    eligibility = evaluate_eligibility(db_path, firm_id, intake_id, WORKFLOW)
    if not eligibility["eligible"]:
        raise BridgeError("; ".join(eligibility["reasons"]))
    migrate_intake_trust_bridge(db_path)
    conn = _connect(db_path)
    try:
        recommendation = _recommendation(conn, firm_id, intake_id, WORKFLOW)
        existing = conn.execute("""
            SELECT * FROM intake_trust_formation_bridges
            WHERE firm_id=? AND recommendation_id=? AND workflow_key=?
              AND bridge_status NOT IN ('superseded','cancelled') LIMIT 1
        """, (firm_id, recommendation["id"], WORKFLOW)).fetchone()
        if existing:
            return dict(existing)
        if matter_id:
            matter_link = conn.execute("""
                SELECT 1 FROM matter_intake_links WHERE firm_id=? AND matter_id=? AND intake_id=?
                  AND link_status='ACTIVE' AND ended_at IS NULL
            """, (firm_id, matter_id, intake_id)).fetchone()
            if not matter_link:
                raise BridgeError("Matter must be an active same-firm link for this intake.")
        bridge_answers, intake_answers = _source_values(conn, firm_id, intake_id)
        source = {"recommendation": dict(recommendation), "bridge_answers": bridge_answers, "intake_answers": intake_answers}
        now, bridge_id = _now(), _id("ITFB")
        source_version = recommendation["updated_at"] or recommendation["created_at"] or now
        idempotency = _fingerprint([firm_id, recommendation["id"], WORKFLOW])
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            INSERT INTO intake_trust_formation_bridges
            (bridge_id,firm_id,intake_id,matter_id,recommendation_id,workflow_key,selected_instrument,
             source_status,source_version,source_fingerprint,bridge_status,professional_review_disposition,
             confirmation_state,idempotency_key,prepared_by,prepared_at,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (bridge_id, firm_id, intake_id, matter_id, recommendation["id"], WORKFLOW, WORKFLOW,
              recommendation["status"], source_version, _fingerprint(source), "prepared", "clear", "pending",
              idempotency, actor, now, now, now))
        bridge = conn.execute("SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=?", (bridge_id,)).fetchone()
        for field, spec in _proposal_specs(bridge_answers, intake_answers).items():
            step, source_type, source_field, classification, value, requirement = spec
            reference = one = "; ".join(bridge_answers.get("trust_parties", [])) if source_field == "trust_parties" else value
            proposed = "" if source_field == "trust_parties" else value
            conn.execute("""
                INSERT INTO intake_trust_formation_field_proposals
                (proposal_id,bridge_id,target_field,target_step,source_record_type,source_record_id,source_field_id,
                 source_classification,original_source_value,proposed_value,confirmation_requirement,
                 source_version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (_id("ITFP"), bridge_id, field, step, source_type, intake_id, source_field,
                  classification, reference, proposed, requirement, source_version, now, now))
        _event(conn, bridge, "BRIDGE_PREPARED", actor, "Accepted declaration recommendation and completed preparation.", new={"status": "prepared"})
        conn.commit()
        return dict(conn.execute("SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=?", (bridge_id,)).fetchone())
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


def get_bridge(db_path, bridge_id, firm_id):
    conn = _connect(db_path)
    try:
        bridge = conn.execute("SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=? AND firm_id=?", (bridge_id, firm_id)).fetchone()
        if not bridge:
            return None
        proposals = conn.execute("SELECT * FROM intake_trust_formation_field_proposals WHERE bridge_id=? ORDER BY target_step,target_field", (bridge_id,)).fetchall()
        events = conn.execute("SELECT * FROM intake_trust_formation_bridge_events WHERE bridge_id=? ORDER BY created_at", (bridge_id,)).fetchall()
        return {"bridge": dict(bridge), "proposals": [dict(row) for row in proposals], "events": [dict(row) for row in events]}
    finally:
        conn.close()


def acknowledge_source_rebase(db_path, bridge_id, firm_id, actor):
    """Explicitly rebase a stale bridge only when the source changed by version metadata alone."""
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        bridge = conn.execute(
            "SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=? AND firm_id=?",
            (bridge_id, firm_id),
        ).fetchone()
        if not bridge:
            raise BridgeError("Bridge not found in the active firm context.")
        if bridge["bridge_status"] != "needs_review":
            raise BridgeError("Only a needs-review bridge may acknowledge a stale source.")
        recommendation = conn.execute(
            """SELECT id,intake_id,firm_id,workflow_key,title,reason,status,
                      created_at,updated_at,created_by
               FROM intake_document_recommendations
               WHERE id=? AND firm_id=? AND intake_id=? AND workflow_key=?""",
            (bridge["recommendation_id"], firm_id, bridge["intake_id"], bridge["workflow_key"]),
        ).fetchone()
        if not recommendation or recommendation["status"] != "accepted":
            raise BridgeError("The originating recommendation is missing or no longer accepted.")
        bridge_answers, intake_answers = _source_values(conn, firm_id, bridge["intake_id"])
        current_source = {
            "recommendation": dict(recommendation),
            "bridge_answers": bridge_answers,
            "intake_answers": intake_answers,
        }
        old_compatible_source = {
            "recommendation": dict(recommendation),
            "bridge_answers": bridge_answers,
            "intake_answers": intake_answers,
        }
        old_compatible_source["recommendation"]["updated_at"] = bridge["source_version"]
        reconstructed_old_fingerprint = _fingerprint(old_compatible_source)
        if reconstructed_old_fingerprint != bridge["source_fingerprint"]:
            raise BridgeError("Source changed materially; explicit re-review is required before confirmation.")
        current_version = recommendation["updated_at"] or recommendation["created_at"]
        current_fingerprint = _fingerprint(current_source)
        previous = {
            "status": bridge["bridge_status"],
            "source_version": bridge["source_version"],
            "source_fingerprint": bridge["source_fingerprint"],
        }
        new = {
            "status": "prepared",
            "source_version": current_version,
            "source_fingerprint": current_fingerprint,
        }
        now = _now()
        conn.execute(
            """UPDATE intake_trust_formation_bridges
               SET source_status=?,source_version=?,source_fingerprint=?,
                   bridge_status='prepared',updated_at=? WHERE bridge_id=?""",
            (recommendation["status"], current_version, current_fingerprint, now, bridge_id),
        )
        conn.execute(
            """UPDATE intake_trust_formation_field_proposals
               SET source_version=?,stale_conflict_status='current',updated_at=?
               WHERE bridge_id=?""",
            (current_version, now, bridge_id),
        )
        _event(
            conn, bridge, "SOURCE_REBASED", actor,
            "Operator acknowledged a metadata-only source-version change after fingerprint verification.",
            previous=previous, new=new,
        )
        conn.commit()
        return get_bridge(db_path, bridge_id, firm_id)
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


def confirm_bridge(db_path, bridge_id, firm_id, values, actor, deviation_reasons=None):
    deviation_reasons = deviation_reasons or {}
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        bridge = conn.execute("SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=? AND firm_id=?", (bridge_id, firm_id)).fetchone()
        if not bridge or bridge["bridge_status"] in ("cancelled", "superseded", "blocked"):
            raise BridgeError("Bridge is unavailable for confirmation.")
        if bridge["bridge_status"] == "confirmed" and bridge["confirmation_state"] == "confirmed":
            existing = {
                row["target_field"]: row
                for row in conn.execute(
                    "SELECT target_field,confirmed_value,deviation_reason FROM intake_trust_formation_field_proposals WHERE bridge_id=?",
                    (bridge_id,),
                )
            }
            same_values = all(
                str(values.get(field, "")).strip() == str(row["confirmed_value"] or "")
                and str(deviation_reasons.get(field, "")).strip() == str(row["deviation_reason"] or "")
                for field, row in existing.items()
            )
            if not same_values:
                raise BridgeError("Bridge is already confirmed; reopen review before changing confirmed values.")
            conn.commit()
            return get_bridge(db_path, bridge_id, firm_id)
        current = _recommendation(conn, firm_id, bridge["intake_id"], bridge["workflow_key"])
        if not current or current["status"] != "accepted" or (current["updated_at"] or current["created_at"]) != bridge["source_version"]:
            conn.execute("UPDATE intake_trust_formation_bridges SET bridge_status='needs_review',updated_at=? WHERE bridge_id=?", (_now(), bridge_id))
            conn.commit()
            raise BridgeError("Source recommendation is stale, replaced, or no longer accepted.")
        blocking = conn.execute("""
            SELECT COUNT(*) FROM professional_review_issues WHERE firm_id=? AND intake_id=? AND workflow_key=?
            AND status IN ('open','escalated') AND severity IN ('critical','major')
        """, (firm_id, bridge["intake_id"], bridge["workflow_key"])).fetchone()[0] if _table_exists(conn, "professional_review_issues") else 0
        if blocking:
            raise BridgeError("Blocking professional-review issues remain unresolved.")
        proposals = conn.execute("SELECT * FROM intake_trust_formation_field_proposals WHERE bridge_id=?", (bridge_id,)).fetchall()
        missing = [f for f in REQUIRED_FIELDS if not str(values.get(f, "")).strip()]
        if missing:
            raise BridgeError("Required formation values are missing: " + ", ".join(missing))
        invalid_choices = []
        for field, control in FORMATION_FIELD_CONTROLS.items():
            choices = control.get("choices")
            if choices and str(values.get(field, "")).strip() not in {value for value, _label in choices}:
                invalid_choices.append(field)
        if invalid_choices:
            raise BridgeError("Invalid controlled formation values: " + ", ".join(invalid_choices))
        now = _now()
        for proposal in proposals:
            field, confirmed = proposal["target_field"], str(values.get(proposal["target_field"], "")).strip()
            proposed = str(proposal["proposed_value"] or "")
            deviated = int(bool(proposed) and proposed != confirmed)
            reason = str(deviation_reasons.get(field, "")).strip()
            if deviated and not reason:
                raise BridgeError(f"Deviation reason required for {field}.")
            conn.execute("""
                UPDATE intake_trust_formation_field_proposals SET confirmed_value=?,confirmation_status='confirmed',
                deviation_indicator=?,deviation_reason=?,confirmed_by=?,confirmed_at=?,updated_at=? WHERE proposal_id=?
            """, (confirmed, deviated, reason or None, actor, now, now, proposal["proposal_id"]))
        conn.execute("""
            UPDATE intake_trust_formation_bridges SET bridge_status='confirmed',confirmation_state='confirmed',
            confirmed_by=?,confirmed_at=?,updated_at=? WHERE bridge_id=?
        """, (actor, now, now, bridge_id))
        _event(conn, bridge, "BRIDGE_CONFIRMED", actor, "Explicit operator confirmation.", previous={"status": bridge["bridge_status"]}, new={"status": "confirmed"})
        conn.commit()
        return get_bridge(db_path, bridge_id, firm_id)
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


def _allocate_trust_id(conn):
    existing = {row[0] for row in conn.execute("SELECT trust_id FROM trusts")}
    numeric = [int(match.group(1)) for value in existing if (match := re.fullmatch(r"TR-(\d+)", value or ""))]
    candidate = max(numeric, default=0) + 1
    while f"TR-{candidate:03d}" in existing:
        candidate += 1
    return f"TR-{candidate:03d}"


def create_or_resume_trust(db_path, bridge_id, firm_id, actor, fail_after_insert=False):
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        bridge = conn.execute("SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=? AND firm_id=?", (bridge_id, firm_id)).fetchone()
        if not bridge:
            raise BridgeError("Bridge not found.")
        if bridge["trust_id"]:
            conn.commit()
            return {"trust_id": bridge["trust_id"], "resumed": True}
        if bridge["bridge_status"] != "confirmed":
            raise BridgeError("Explicit bridge confirmation is required before trust creation.")
        values = {row["target_field"]: row["confirmed_value"] for row in conn.execute(
            "SELECT target_field,confirmed_value FROM intake_trust_formation_field_proposals WHERE bridge_id=?", (bridge_id,))}
        trust_id = _allocate_trust_id(conn)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(trusts)")}
        payload = dict(values)
        payload.update({"trust_id": trust_id, "status": "Draft - Bridge Created", "firm_id": firm_id})
        insert_columns = [name for name in payload if name in columns]
        conn.execute(f"INSERT INTO trusts ({','.join(insert_columns)}) VALUES ({','.join('?' for _ in insert_columns)})",
                     [payload[name] for name in insert_columns])
        if fail_after_insert:
            raise RuntimeError("Injected failure after trust insert")
        now = _now()
        conn.execute("""
            UPDATE intake_trust_formation_bridges SET trust_id=?,bridge_status='trust_created',launched_by=?,
            launched_at=?,updated_at=? WHERE bridge_id=? AND trust_id IS NULL
        """, (trust_id, actor, now, now, bridge_id))
        conn.execute("UPDATE continuity_profiles SET trust_id=?,updated_by=?,updated_at=? WHERE firm_id=? AND bridge_id=? AND trust_id IS NULL",
                     (trust_id, actor, now, firm_id, bridge_id))
        _event(conn, bridge, "TRUST_CREATED", actor, "Atomic collision-safe bridge launch.", new={"trust_id": trust_id})
        conn.commit()
        return {"trust_id": trust_id, "resumed": False}
    except sqlite3.IntegrityError as exc:
        if conn.in_transaction:
            conn.rollback()
        raise BridgeError(f"Trust creation collision prevented: {exc}") from exc
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


def validate_no_secret_material(values):
    for name, value in values.items():
        if name.lower() in PROHIBITED_SECRET_NAMES:
            raise BridgeError("Secret fields are prohibited; store only a secure-vault reference.")
        text = str(value or "")
        if any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS):
            raise BridgeError("Possible secret material rejected; store only metadata and a secure-vault reference.")


def create_continuity_profile(db_path, firm_id, subject_name, subject_type, capacities, purpose, actor,
                              intake_id=None, matter_id=None, bridge_id=None, trust_id=None, subject_object_id=None):
    if not subject_name.strip() or not capacities.strip():
        raise BridgeError("The continuity subject and capacity must be explicitly selected.")
    migrate_intake_trust_bridge(db_path)
    conn = _connect(db_path)
    try:
        if bridge_id and not conn.execute("SELECT 1 FROM intake_trust_formation_bridges WHERE bridge_id=? AND firm_id=?", (bridge_id, firm_id)).fetchone():
            raise BridgeError("Bridge is not available in this firm.")
        now, profile_id = _now(), _id("CP")
        conn.execute("""
            INSERT INTO continuity_profiles
            (continuity_profile_id,firm_id,subject_name,subject_type,subject_object_id,subject_capacities,status,
             primary_purpose,intake_id,matter_id,bridge_id,trust_id,readiness_status,created_by,updated_by,created_at,updated_at)
            VALUES (?,?,?,?,?,?,'draft',?,?,?,?,?,'needs_review',?,?,?,?)
        """, (profile_id, firm_id, subject_name.strip(), subject_type, subject_object_id, capacities.strip(), purpose.strip(),
              intake_id, matter_id, bridge_id, trust_id, actor, actor, now, now))
        conn.execute("INSERT INTO continuity_events VALUES (?,?,?,?,?,?,?,?,?)",
                     (_id("CPE"), profile_id, firm_id, "PROFILE_CREATED", actor, "Explicit subject selection", None,
                      _json({"subject_name": subject_name, "subject_type": subject_type}), now))
        conn.commit()
        return profile_id
    finally:
        conn.close()


def get_continuity_profile(db_path, profile_id, firm_id):
    conn = _connect(db_path)
    try:
        profile = conn.execute("SELECT * FROM continuity_profiles WHERE continuity_profile_id=? AND firm_id=?", (profile_id, firm_id)).fetchone()
        if not profile:
            return None
        result = {"profile": dict(profile)}
        for key, table in (("responsibilities","continuity_responsibilities"),("digital_accounts","continuity_digital_accounts"),
                           ("receivables","continuity_receivables"),("payables","continuity_payables"),("activation_plans","continuity_activation_plans")):
            result[key] = [dict(row) for row in conn.execute(f"SELECT * FROM {table} WHERE continuity_profile_id=? AND firm_id=? ORDER BY created_at", (profile_id, firm_id))]
        result["readiness"] = continuity_readiness(result)
        return result
    finally:
        conn.close()


def link_continuity_profile(db_path, profile_id, bridge_id, firm_id, actor):
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        profile = conn.execute("SELECT * FROM continuity_profiles WHERE continuity_profile_id=? AND firm_id=?", (profile_id, firm_id)).fetchone()
        bridge = conn.execute("SELECT * FROM intake_trust_formation_bridges WHERE bridge_id=? AND firm_id=?", (bridge_id, firm_id)).fetchone()
        if not profile or not bridge:
            raise BridgeError("Profile and bridge must both exist in the current firm.")
        now = _now()
        previous = {key: profile[key] for key in ("intake_id", "matter_id", "bridge_id", "trust_id")}
        conn.execute("""UPDATE continuity_profiles SET intake_id=?,matter_id=?,bridge_id=?,trust_id=?,updated_by=?,updated_at=?
            WHERE continuity_profile_id=? AND firm_id=?""",
            (bridge["intake_id"], bridge["matter_id"], bridge_id, bridge["trust_id"], actor, now, profile_id, firm_id))
        conn.execute("INSERT INTO continuity_events VALUES (?,?,?,?,?,?,?,?,?)",
                     (_id("CPE"), profile_id, firm_id, "PROFILE_LINKED_TO_BRIDGE", actor, "Explicit same-firm link",
                      _json(previous), _json({"intake_id": bridge["intake_id"], "matter_id": bridge["matter_id"], "bridge_id": bridge_id, "trust_id": bridge["trust_id"]}), now))
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


def add_continuity_record(db_path, table, profile_id, firm_id, actor, values):
    allowed = {
        "continuity_responsibilities": ("responsibility_id", "RESP"),
        "continuity_digital_accounts": ("digital_account_id", "DAC"),
        "continuity_receivables": ("receivable_id", "REC"),
        "continuity_payables": ("payable_id", "PAY"),
        "continuity_activation_plans": ("activation_plan_id", "ACT"),
    }
    if table not in allowed:
        raise BridgeError("Unsupported continuity record type.")
    validate_no_secret_material(values)
    conn = _connect(db_path)
    try:
        if not conn.execute("SELECT 1 FROM continuity_profiles WHERE continuity_profile_id=? AND firm_id=?", (profile_id, firm_id)).fetchone():
            raise BridgeError("Continuity profile not found in this firm.")
        table_columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        id_column, prefix = allowed[table]
        now = _now()
        payload = {id_column: _id(prefix), "continuity_profile_id": profile_id, "firm_id": firm_id,
                   "created_by": actor, "created_at": now, "updated_at": now}
        payload.update({key: value for key, value in values.items() if key in table_columns})
        columns = [key for key in payload if key in table_columns]
        conn.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", [payload[key] for key in columns])
        conn.execute("INSERT INTO continuity_events VALUES (?,?,?,?,?,?,?,?,?)",
                     (_id("CPE"), profile_id, firm_id, "RECORD_ADDED", actor, table, None, _json({id_column: payload[id_column]}), now))
        conn.commit()
        return payload[id_column]
    finally:
        conn.close()


def transition_activation_plan(db_path, plan_id, profile_id, firm_id, actor, new_status, basis):
    allowed = {
        "plan_drafted": {"plan_reviewed", "superseded", "closed"}, "plan_reviewed": {"trigger_reported", "superseded", "closed"},
        "trigger_reported": {"evidence_pending", "activation_authorized", "closed"}, "evidence_pending": {"activation_authorized", "closed"},
        "activation_authorized": {"active", "suspended"}, "active": {"suspended", "restored", "superseded", "closed"},
        "suspended": {"active", "restored", "closed"}, "restored": {"closed", "superseded"}, "superseded": set(), "closed": set(),
    }
    if not basis.strip():
        raise BridgeError("A documented transition basis is required.")
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM continuity_activation_plans WHERE activation_plan_id=? AND continuity_profile_id=? AND firm_id=?", (plan_id, profile_id, firm_id)).fetchone()
        if not row or new_status not in allowed.get(row["status"], set()):
            raise BridgeError("Invalid activation-plan transition.")
        now = _now()
        conn.execute("UPDATE continuity_activation_plans SET status=?,activation_basis=?,authorized_by=?,authorized_at=?,updated_at=? WHERE activation_plan_id=?",
                     (new_status, basis, actor, now if new_status == "activation_authorized" else row["authorized_at"], now, plan_id))
        conn.execute("INSERT INTO continuity_events VALUES (?,?,?,?,?,?,?,?,?)",
                     (_id("CPE"), profile_id, firm_id, "ACTIVATION_STATUS_CHANGED", actor, basis,
                      _json({"status": row["status"]}), _json({"status": new_status}), now))
        conn.commit()
    finally:
        conn.close()


def continuity_readiness(bundle):
    profile = bundle["profile"]
    responsibilities = bundle.get("responsibilities", [])
    digital = bundle.get("digital_accounts", [])
    activations = bundle.get("activation_plans", [])
    missing_current = sum(not row.get("current_responsible_party") for row in responsibilities)
    missing_successors = sum(not row.get("successor_responsible_party") for row in responsibilities)
    missing_authority = sum(not row.get("authority_source") for row in responsibilities)
    missing_access = sum(not row.get("vault_reference") and not row.get("recovery_procedure") for row in digital)
    unreviewed_activation = sum(row.get("status") == "plan_drafted" for row in activations)
    missing_documents = sum(not row.get("supporting_document_reference") for row in responsibilities)
    unverified_accounts = sum(not row.get("last_verified_date") for row in digital)
    gaps = missing_current + missing_successors + missing_authority + missing_documents + missing_access + unverified_accounts + unreviewed_activation
    return {"classification": "ready_for_review" if gaps == 0 else "needs_attention", "gap_count": gaps,
            "missing_current_responsible_parties": missing_current, "missing_successors": missing_successors,
            "missing_authority_sources": missing_authority, "missing_controlled_access_instructions": missing_access,
            "missing_supporting_documents": missing_documents, "unverified_account_records": unverified_accounts,
            "unreviewed_activation_instructions": unreviewed_activation, "last_reviewed_date": profile.get("last_reviewed_date"),
            "next_review_date": profile.get("next_review_date"),
            "disclaimer": "Readiness is not legal validity, appointment, financial certification, or proof of incapacity."}
