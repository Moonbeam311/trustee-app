"""TPD-1C governed schema for planning-to-formation and continuity records."""

import sqlite3


BRIDGE_STATUSES = (
    "prepared", "needs_review", "ready_for_confirmation", "confirmed",
    "trust_created", "blocked", "superseded", "cancelled",
)


def migrate_intake_trust_bridge(db_path):
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS intake_trust_formation_bridges (
            bridge_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            intake_id TEXT NOT NULL,
            matter_id TEXT,
            recommendation_id INTEGER NOT NULL,
            workflow_key TEXT NOT NULL CHECK (workflow_key = 'declaration_of_trust'),
            selected_instrument TEXT NOT NULL,
            source_status TEXT NOT NULL,
            source_version TEXT NOT NULL,
            source_fingerprint TEXT NOT NULL,
            bridge_status TEXT NOT NULL DEFAULT 'prepared'
                CHECK (bridge_status IN ('prepared','needs_review','ready_for_confirmation','confirmed','trust_created','blocked','superseded','cancelled')),
            professional_review_disposition TEXT NOT NULL DEFAULT 'clear',
            confirmation_state TEXT NOT NULL DEFAULT 'pending',
            trust_id TEXT UNIQUE,
            idempotency_key TEXT NOT NULL UNIQUE,
            prepared_by TEXT NOT NULL,
            confirmed_by TEXT,
            launched_by TEXT,
            prepared_at TEXT NOT NULL,
            confirmed_at TEXT,
            launched_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (recommendation_id) REFERENCES intake_document_recommendations(id) ON DELETE RESTRICT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_active_intake_trust_bridge
        ON intake_trust_formation_bridges(firm_id, recommendation_id, workflow_key)
        WHERE bridge_status NOT IN ('superseded','cancelled');

        CREATE TABLE IF NOT EXISTS intake_trust_formation_field_proposals (
            proposal_id TEXT PRIMARY KEY,
            bridge_id TEXT NOT NULL,
            target_field TEXT NOT NULL,
            target_step INTEGER NOT NULL,
            source_record_type TEXT NOT NULL,
            source_record_id TEXT,
            source_field_id TEXT,
            source_classification TEXT NOT NULL CHECK (source_classification IN
                ('VERIFIED_FACT','USER_ASSERTED_FACT','USER_PREFERENCE','SYSTEM_RECOMMENDATION','PROFESSIONAL_REVIEW_INPUT','OPERATOR_DECISION','DERIVED_VALUE','NO_RELIABLE_SOURCE')),
            original_source_value TEXT,
            proposed_value TEXT,
            confirmation_requirement TEXT NOT NULL,
            confirmed_value TEXT,
            confirmation_status TEXT NOT NULL DEFAULT 'pending',
            deviation_indicator INTEGER NOT NULL DEFAULT 0 CHECK (deviation_indicator IN (0,1)),
            deviation_reason TEXT,
            confirmed_by TEXT,
            confirmed_at TEXT,
            source_version TEXT NOT NULL,
            stale_conflict_status TEXT NOT NULL DEFAULT 'current',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (bridge_id, target_field),
            FOREIGN KEY (bridge_id) REFERENCES intake_trust_formation_bridges(bridge_id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS intake_trust_formation_bridge_events (
            event_id TEXT PRIMARY KEY,
            bridge_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            actor_capacity TEXT,
            event_basis TEXT,
            previous_state_json TEXT,
            new_state_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (bridge_id) REFERENCES intake_trust_formation_bridges(bridge_id) ON DELETE RESTRICT
        );
        CREATE TRIGGER IF NOT EXISTS trg_bridge_events_no_update
        BEFORE UPDATE ON intake_trust_formation_bridge_events BEGIN SELECT RAISE(ABORT, 'Bridge events are immutable.'); END;
        CREATE TRIGGER IF NOT EXISTS trg_bridge_events_no_delete
        BEFORE DELETE ON intake_trust_formation_bridge_events BEGIN SELECT RAISE(ABORT, 'Bridge events are immutable.'); END;

        CREATE TABLE IF NOT EXISTS continuity_profiles (
            continuity_profile_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            subject_object_id TEXT,
            subject_capacities TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            primary_purpose TEXT NOT NULL,
            intake_id TEXT,
            matter_id TEXT,
            bridge_id TEXT,
            trust_id TEXT,
            readiness_status TEXT NOT NULL DEFAULT 'needs_review',
            last_reviewed_date TEXT,
            next_review_date TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (bridge_id) REFERENCES intake_trust_formation_bridges(bridge_id) ON DELETE RESTRICT
        );
        CREATE INDEX IF NOT EXISTS ix_continuity_profile_links ON continuity_profiles(firm_id, intake_id, bridge_id, trust_id);

        CREATE TABLE IF NOT EXISTS continuity_responsibilities (
            responsibility_id TEXT PRIMARY KEY, continuity_profile_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            category TEXT NOT NULL, description TEXT NOT NULL, related_record_type TEXT, related_record_id TEXT,
            current_responsible_party TEXT NOT NULL, successor_responsible_party TEXT, alternate_party TEXT,
            capacity TEXT, authority_source TEXT, supporting_document_reference TEXT, effective_from TEXT, effective_to TEXT,
            activation_condition TEXT, access_level TEXT NOT NULL DEFAULT 'designated_only',
            acceptance_status TEXT NOT NULL DEFAULT 'designated', restrictions_conflicts TEXT, priority TEXT,
            last_verified_date TEXT, review_date TEXT, status TEXT NOT NULL DEFAULT 'active', created_by TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY (continuity_profile_id) REFERENCES continuity_profiles(continuity_profile_id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS continuity_digital_accounts (
            digital_account_id TEXT PRIMARY KEY, continuity_profile_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            institution_service TEXT NOT NULL, account_category TEXT NOT NULL, account_label TEXT NOT NULL,
            website_application TEXT, login_identifier TEXT, vault_reference TEXT, recovery_procedure TEXT,
            mfa_method TEXT, mfa_device_custodian TEXT, emergency_access_authorization TEXT,
            responsible_party TEXT, successor_responsible_party TEXT, supporting_authority TEXT,
            access_restrictions TEXT, last_verified_date TEXT, status TEXT NOT NULL DEFAULT 'active',
            created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY (continuity_profile_id) REFERENCES continuity_profiles(continuity_profile_id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS continuity_receivables (
            receivable_id TEXT PRIMARY KEY, continuity_profile_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            payer_debtor TEXT NOT NULL, description TEXT NOT NULL, amount TEXT, currency TEXT, due_date_frequency TEXT,
            supporting_document_reference TEXT, payment_method_description TEXT, receiving_account_reference TEXT,
            current_collector TEXT, successor_collector TEXT, delinquency_instructions TEXT, escalation_instructions TEXT,
            priority TEXT, status TEXT NOT NULL DEFAULT 'active', last_verified_date TEXT, notes TEXT,
            created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY (continuity_profile_id) REFERENCES continuity_profiles(continuity_profile_id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS continuity_payables (
            payable_id TEXT PRIMARY KEY, continuity_profile_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            creditor_payee TEXT NOT NULL, description TEXT NOT NULL, account_reference TEXT, amount TEXT,
            due_date_frequency TEXT, autopay_status TEXT, payment_source_reference TEXT, current_responsible_party TEXT,
            successor_responsible_party TEXT, priority TEXT, consequence_nonpayment TEXT, continuity_instruction TEXT,
            supporting_document_reference TEXT, status TEXT NOT NULL DEFAULT 'active', last_verified_date TEXT, notes TEXT,
            created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY (continuity_profile_id) REFERENCES continuity_profiles(continuity_profile_id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS continuity_activation_plans (
            activation_plan_id TEXT PRIMARY KEY, continuity_profile_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            continuity_subject TEXT NOT NULL, triggering_event TEXT NOT NULL, required_evidence TEXT NOT NULL,
            authorized_recognizer TEXT NOT NULL, primary_successor TEXT, alternate_successors TEXT, authority_source TEXT,
            immediate_actions TEXT, affected_responsibilities TEXT, affected_accounts_obligations TEXT,
            essential_payments TEXT, expected_receivables TEXT, notifications TEXT, controlled_access_release_procedure TEXT,
            restrictions TEXT, review_escalation_procedure TEXT, restoration_transfer_closure_procedure TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'plan_drafted' CHECK (status IN ('plan_drafted','plan_reviewed','trigger_reported','evidence_pending','activation_authorized','active','suspended','restored','superseded','closed')),
            activation_basis TEXT, authorized_by TEXT, authorized_at TEXT, created_by TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY (continuity_profile_id) REFERENCES continuity_profiles(continuity_profile_id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS continuity_events (
            event_id TEXT PRIMARY KEY, continuity_profile_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            event_type TEXT NOT NULL, actor_id TEXT NOT NULL, event_basis TEXT, previous_state_json TEXT,
            new_state_json TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY (continuity_profile_id) REFERENCES continuity_profiles(continuity_profile_id) ON DELETE RESTRICT
        );
        CREATE TRIGGER IF NOT EXISTS trg_continuity_events_no_update
        BEFORE UPDATE ON continuity_events BEGIN SELECT RAISE(ABORT, 'Continuity events are immutable.'); END;
        CREATE TRIGGER IF NOT EXISTS trg_continuity_events_no_delete
        BEFORE DELETE ON continuity_events BEGIN SELECT RAISE(ABORT, 'Continuity events are immutable.'); END;
        """)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit("Import migrate_intake_trust_bridge(db_path) with an explicit isolated database path.")
