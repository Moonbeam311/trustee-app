from dataclasses import dataclass


OBSERVATION_TYPES = {
    "account_posture",
    "permission_posture",
    "authentication_session_posture",
    "audit_integrity_posture",
    "backup_preservation_posture",
    "deployment_health_posture",
    "database_migration_posture",
    "operating_policy_posture",
    "institutional_role_posture",
    "recovery_repair_posture",
}

PANEL_TYPE_MAP = {
    "protected_user_accounts": "account_posture",
    "application_permission_controls": "permission_posture",
    "authentication_session_security": "authentication_session_posture",
    "audit_security_oversight": "audit_integrity_posture",
    "backup_data_preservation": "backup_preservation_posture",
    "deployment_production_health": "deployment_health_posture",
    "database_migration_posture": "database_migration_posture",
    "feature_flags_operating_policy": "operating_policy_posture",
    "institutional_role_assignments": "institutional_role_posture",
    "recovery_repair_controls": "recovery_repair_posture",
}

CONTEXT_SCOPES = {
    "platform_scoped",
    "deployment_scoped",
    "firm_scoped",
    "institution_scoped",
    "trust_scoped",
    "matter_scoped",
}

PERSISTENCE_TRIGGERS = {
    "authorized_acknowledgement",
    "investigation_start",
    "routing_preparation",
    "restricted_governance_initiation",
    "separately_governed_source",
    "continuing_condition_review",
}

LIFECYCLE_STATES = {
    "acknowledged",
    "under_review",
    "deferred",
    "routed",
    "closed_no_action",
    "closed_resolved",
    "superseded",
}

OPEN_STATES = {
    "acknowledged",
    "under_review",
    "deferred",
    "routed",
}

CLOSED_STATES = {
    "closed_no_action",
    "closed_resolved",
    "superseded",
}

EVENT_TYPES = {
    "observation_created",
    "acknowledged",
    "investigation_started",
    "deferred",
    "routing_prepared",
    "destination_linked",
    "institutional_determination_recorded",
    "technical_action_recorded",
    "verification_recorded",
    "closed_no_action",
    "closed_resolved",
    "reopened",
    "recurrence_linked",
    "superseded",
    "note_recorded",
}

CONDITION_CODE_REGISTRY = {
    "account_registry_unavailable": {
        "observation_type": "account_posture",
        "context_scopes": {"firm_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "investigation_start"},
        "restricted_governance": False,
    },
    "inactive_accounts_detected": {
        "observation_type": "account_posture",
        "context_scopes": {"firm_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "continuing_condition_review"},
        "restricted_governance": False,
    },
    "permission_boundary_missing": {
        "observation_type": "permission_posture",
        "context_scopes": {"platform_scoped", "firm_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "csrf_boundary_missing": {
        "observation_type": "permission_posture",
        "context_scopes": {"platform_scoped", "firm_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "authentication_runtime_not_assessed": {
        "observation_type": "authentication_session_posture",
        "context_scopes": {"platform_scoped", "deployment_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "continuing_condition_review"},
        "restricted_governance": False,
    },
    "authentication_structural_control_missing": {
        "observation_type": "authentication_session_posture",
        "context_scopes": {"platform_scoped", "deployment_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "audit_integrity_attention": {
        "observation_type": "audit_integrity_posture",
        "context_scopes": {"firm_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "audit_verification_unavailable": {
        "observation_type": "audit_integrity_posture",
        "context_scopes": {"firm_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "backup_route_unavailable": {
        "observation_type": "backup_preservation_posture",
        "context_scopes": {"firm_scoped", "deployment_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "investigation_start"},
        "restricted_governance": False,
    },
    "backup_recoverability_not_assessed": {
        "observation_type": "backup_preservation_posture",
        "context_scopes": {"firm_scoped", "deployment_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "continuing_condition_review"},
        "restricted_governance": False,
    },
    "hosted_runtime_not_assessed": {
        "observation_type": "deployment_health_posture",
        "context_scopes": {"deployment_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "continuing_condition_review"},
        "restricted_governance": False,
    },
    "hosted_health_attention": {
        "observation_type": "deployment_health_posture",
        "context_scopes": {"deployment_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "hosted_health_failure": {
        "observation_type": "deployment_health_posture",
        "context_scopes": {"deployment_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "database_unreadable": {
        "observation_type": "database_migration_posture",
        "context_scopes": {"platform_scoped", "deployment_scoped"},
        "persistence_triggers": {"investigation_start", "restricted_governance_initiation"},
        "restricted_governance": True,
    },
    "required_table_missing": {
        "observation_type": "database_migration_posture",
        "context_scopes": {"platform_scoped", "deployment_scoped"},
        "persistence_triggers": {"investigation_start", "restricted_governance_initiation"},
        "restricted_governance": True,
    },
    "migration_posture_not_assessed": {
        "observation_type": "database_migration_posture",
        "context_scopes": {"platform_scoped", "deployment_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "continuing_condition_review"},
        "restricted_governance": False,
    },
    "read_only_mode_enabled": {
        "observation_type": "operating_policy_posture",
        "context_scopes": {"institution_scoped", "firm_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "routing_preparation"},
        "restricted_governance": False,
    },
    "exports_disabled": {
        "observation_type": "operating_policy_posture",
        "context_scopes": {"institution_scoped", "firm_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "routing_preparation"},
        "restricted_governance": False,
    },
    "user_creation_disabled": {
        "observation_type": "operating_policy_posture",
        "context_scopes": {"institution_scoped", "firm_scoped"},
        "persistence_triggers": {"authorized_acknowledgement", "routing_preparation"},
        "restricted_governance": False,
    },
    "operating_policy_unavailable": {
        "observation_type": "operating_policy_posture",
        "context_scopes": {"institution_scoped", "firm_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "institutional_role_registry_unavailable": {
        "observation_type": "institutional_role_posture",
        "context_scopes": {"institution_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "institutional_role_ambiguity": {
        "observation_type": "institutional_role_posture",
        "context_scopes": {"institution_scoped", "trust_scoped", "matter_scoped"},
        "persistence_triggers": {"investigation_start", "routing_preparation"},
        "restricted_governance": False,
    },
    "restricted_procedure_required": {
        "observation_type": "recovery_repair_posture",
        "context_scopes": {"platform_scoped", "deployment_scoped"},
        "persistence_triggers": {"restricted_governance_initiation"},
        "restricted_governance": True,
    },
}


@dataclass(frozen=True)
class SystemObservationResult:
    ok: bool
    status: str
    message: str = ""
    observation: dict | None = None
    event: dict | None = None
    events: list | None = None
