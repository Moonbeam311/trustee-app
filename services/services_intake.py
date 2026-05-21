from datetime import datetime
from database.db import get_connection, get_current_firm_id


INTAKE_LANES = {
    "new_planning": {
        "label": "I want to start organizing my estate, trust, or family plan.",
        "posture": "planning",
        "default_depth": "standard",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "universal_profile",
    },
    "document_review": {
        "label": "I already have documents and want them reviewed or updated.",
        "posture": "review",
        "default_depth": "document_focused",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "document_inventory",
    },
    "administration": {
        "label": "I am responsible for a trust, estate, or fiduciary role.",
        "posture": "fiduciary",
        "default_depth": "administrative",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "fiduciary_role_check",
    },
    "asset_funding": {
        "label": "I want to organize, transfer, or fund assets into a trust or structure.",
        "posture": "execution_preparation",
        "default_depth": "asset_focused",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "asset_snapshot",
    },
    "business_continuity": {
        "label": "I own or manage a business and want continuity or protection planning.",
        "posture": "business_owner",
        "default_depth": "business_focused",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "business_profile",
    },
    "urgent_triage": {
        "label": "Something urgent or complicated is happening.",
        "posture": "crisis_or_pressure",
        "default_depth": "triage",
        "risk_posture": "elevated",
        "professional_review_recommended": True,
        "automation_limits": "high",
        "next_screen": "triage_precheck",
    },
    "education": {
        "label": "I am just learning and want guidance.",
        "posture": "exploratory",
        "default_depth": "light",
        "risk_posture": "low",
        "professional_review_recommended": False,
        "automation_limits": "low",
        "next_screen": "guided_orientation",
    },
}


def ensure_intake_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            client_id TEXT,
            intake_lane TEXT NOT NULL,
            user_posture TEXT,
            default_depth TEXT,
            risk_posture TEXT,
            professional_review_recommended INTEGER DEFAULT 0,
            automation_limits TEXT,
            next_screen TEXT,
            status TEXT DEFAULT 'lane_selected',
            created_at TEXT,
            updated_at TEXT,
            completed_at TEXT,
            created_by TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_lane_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            event_type TEXT,
            event_label TEXT,
            event_value TEXT,
            created_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_intake_lanes():
    return INTAKE_LANES


def get_lane_config(lane_key):
    return INTAKE_LANES.get(lane_key)


def _next_intake_id(cur):
    cur.execute("SELECT intake_id FROM intake_sessions ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        return "INTAKE-0001"

    last = row["intake_id"] if hasattr(row, "keys") else row[0]
    try:
        number = int(str(last).split("-")[-1])
    except Exception:
        number = 0
    return f"INTAKE-{number + 1:04d}"


def create_intake_session(lane_key, client_id=None, created_by=None):
    ensure_intake_tables()

    lane = get_lane_config(lane_key)
    if not lane:
        raise ValueError(f"Invalid intake lane: {lane_key}")

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()

    intake_id = _next_intake_id(cur)

    cur.execute("""
        INSERT INTO intake_sessions (
            intake_id, firm_id, client_id, intake_lane, user_posture,
            default_depth, risk_posture, professional_review_recommended,
            automation_limits, next_screen, status, created_at, updated_at,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        client_id,
        lane_key,
        lane["posture"],
        lane["default_depth"],
        lane["risk_posture"],
        1 if lane["professional_review_recommended"] else 0,
        lane["automation_limits"],
        lane["next_screen"],
        "lane_selected",
        now,
        now,
        created_by,
    ))

    cur.execute("""
        INSERT INTO intake_lane_events (
            intake_id, firm_id, event_type, event_label, event_value,
            created_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        "lane_selected",
        "Intake lane selected",
        lane_key,
        now,
        created_by,
    ))

    conn.commit()
    conn.close()

    return {
        "intake_id": intake_id,
        "intake_lane": lane_key,
        "user_posture": lane["posture"],
        "default_depth": lane["default_depth"],
        "risk_posture": lane["risk_posture"],
        "professional_review_recommended": lane["professional_review_recommended"],
        "automation_limits": lane["automation_limits"],
        "next_screen": lane["next_screen"],
    }


# -------------------------------------------------------------------
# INT-1B — Intake Translation Map
# -------------------------------------------------------------------

UNIVERSAL_INTAKE_QUESTIONS = {
    "planning_context": {
        "label": "Who are we planning for?",
        "input_type": "single",
        "options": {
            "just_me": "Just me",
            "me_and_spouse": "Me and my spouse or partner",
            "family": "My family",
            "parent_or_elder": "A parent or elder",
            "business": "A business",
            "existing_trust_or_estate": "A trust or estate already created",
            "other": "Other / not sure",
        },
    },
    "main_goals": {
        "label": "What are your main goals?",
        "input_type": "multi",
        "options": {
            "protect_family": "Protect family",
            "avoid_probate": "Avoid probate or court confusion",
            "organize_assets": "Organize assets",
            "reduce_conflict": "Reduce confusion or family conflict",
            "choose_decision_makers": "Choose decision-makers",
            "business_continuity": "Protect or continue a business",
            "plan_for_children": "Plan for children",
            "incapacity_planning": "Plan for incapacity",
            "privacy": "Preserve privacy",
            "legacy_charitable": "Support legacy, charitable, or community goals",
            "review_documents": "Review existing documents",
            "other_goal": "Other / not listed",
        },
    },
    "asset_snapshot": {
        "label": "Which of these do you own, manage, or expect to inherit?",
        "input_type": "multi",
        "options": {
            "home": "Home",
            "rental_property": "Rental property",
            "land": "Land",
            "bank_accounts": "Bank accounts",
            "vehicles": "Vehicles",
            "business": "Business",
            "retirement_accounts": "Retirement accounts",
            "life_insurance": "Life insurance",
            "investments": "Stocks, investments, or brokerage accounts",
            "digital_assets": "Digital assets",
            "intellectual_property": "Intellectual property",
            "collectibles_heirlooms": "Collectibles, heirlooms, or heritage property",
            "trust_estate_assets": "Trust or estate assets",
            "other_asset": "Other / not listed",
            "none_not_sure": "None / not sure",
        },
    },
    "people_dependents": {
        "label": "Who depends on you or may need to be included?",
        "input_type": "multi",
        "options": {
            "spouse_partner": "Spouse or partner",
            "minor_children": "Minor children",
            "adult_children": "Adult children",
            "parent_elder": "Parent or elder",
            "special_needs_person": "Disabled or special-needs person",
            "business_partner": "Business partner",
            "charitable_beneficiary": "Charitable, community, or legacy beneficiary",
            "other_person": "Other / not listed",
            "no_dependents": "No dependents",
            "not_sure": "Not sure",
        },
    },
    "concerns": {
        "label": "Do any of these concerns apply?",
        "input_type": "multi",
        "options": {
            "family_conflict": "Family conflict",
            "lawsuit_concern": "Lawsuit concern",
            "debt_creditor": "Debt or creditor concern",
            "tax_concern": "Tax concern",
            "business_liability": "Business liability",
            "divorce_remarriage": "Divorce or remarriage concern",
            "multi_state_property": "Property in more than one state",
            "medical_incapacity": "Medical or incapacity concern",
            "no_trusted_successor": "No trusted successor",
            "missing_documents": "Missing documents",
            "none_apply": "None of these apply",
            "not_sure": "Not sure",
        },
    },
    "existing_documents": {
        "label": "Which documents do you already have?",
        "input_type": "multi",
        "options": {
            "will": "Will",
            "trust": "Trust",
            "power_of_attorney": "Power of attorney",
            "health_directive": "Health directive",
            "deed": "Deed",
            "mortgage_statement": "Mortgage statement",
            "business_documents": "Business documents",
            "insurance_policies": "Insurance policies",
            "beneficiary_forms": "Retirement / beneficiary forms",
            "tax_filings": "Tax filings",
            "court_documents": "Court documents",
            "other_document": "Other / not listed",
            "none": "None",
            "not_sure": "Not sure",
        },
    },
}


TRANSLATION_RULES = {
    # Planning context
    "planning_context.just_me": {
        "system_category": "PERSON_PROFILE",
        "system_meaning": "individual_planning",
        "module_triggers": ["foundational_profile"],
        "document_requests": [],
        "next_sessions": ["initial_structure_review"],
        "risk_flags": [],
    },
    "planning_context.me_and_spouse": {
        "system_category": "FAMILY_STRUCTURE",
        "system_meaning": "spousal_or_partner_planning",
        "module_triggers": ["spousal_profile", "beneficiary_review"],
        "document_requests": [],
        "next_sessions": ["family_structure_review"],
        "risk_flags": [],
    },
    "planning_context.family": {
        "system_category": "FAMILY_STRUCTURE",
        "system_meaning": "family_planning",
        "module_triggers": ["family_profile", "beneficiary_review"],
        "document_requests": [],
        "next_sessions": ["family_structure_review"],
        "risk_flags": [],
    },
    "planning_context.parent_or_elder": {
        "system_category": "DEPENDENCY_PROFILE",
        "system_meaning": "elder_or_parent_planning",
        "module_triggers": ["elder_planning", "authority_document_review"],
        "document_requests": ["power_of_attorney", "health_directive", "existing_care_documents"],
        "next_sessions": ["elder_authority_review"],
        "risk_flags": ["possible_incapacity_or_care_issue"],
    },
    "planning_context.business": {
        "system_category": "BUSINESS_PROFILE",
        "system_meaning": "business_planning_context",
        "module_triggers": ["business_continuity"],
        "document_requests": ["operating_agreement", "ein_letter", "business_license"],
        "next_sessions": ["business_continuity_review"],
        "risk_flags": ["business_continuity_needed"],
    },
    "planning_context.existing_trust_or_estate": {
        "system_category": "FIDUCIARY_CONTEXT",
        "system_meaning": "existing_trust_or_estate_matter",
        "module_triggers": ["trust_audit", "fiduciary_administration"],
        "document_requests": ["trust_document", "letters_testamentary_or_authority", "asset_inventory"],
        "next_sessions": ["fiduciary_authority_review"],
        "risk_flags": ["authority_review_needed"],
    },

    # Goals
    "main_goals.protect_family": {
        "system_category": "OBJECTIVE_PROFILE",
        "system_meaning": "family_protection_objective",
        "module_triggers": ["beneficiary_planning", "successor_planning"],
        "document_requests": [],
        "next_sessions": ["beneficiary_planning_review"],
        "risk_flags": [],
    },
    "main_goals.avoid_probate": {
        "system_category": "OBJECTIVE_PROFILE",
        "system_meaning": "probate_avoidance_objective",
        "module_triggers": ["trust_planning", "funding_checklist"],
        "document_requests": ["existing_will", "deed", "beneficiary_forms"],
        "next_sessions": ["probate_avoidance_review"],
        "risk_flags": [],
    },
    "main_goals.organize_assets": {
        "system_category": "OBJECTIVE_PROFILE",
        "system_meaning": "asset_organization_objective",
        "module_triggers": ["asset_inventory"],
        "document_requests": ["asset_statements", "titles", "deeds"],
        "next_sessions": ["asset_document_deep_dive"],
        "risk_flags": [],
    },
    "main_goals.reduce_conflict": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "conflict_reduction_objective",
        "module_triggers": ["governance_controls", "decision_authority_review"],
        "document_requests": ["existing_will", "existing_trust", "family_agreements"],
        "next_sessions": ["governance_conflict_review"],
        "risk_flags": ["family_conflict_risk"],
    },
    "main_goals.choose_decision_makers": {
        "system_category": "FIDUCIARY_READINESS",
        "system_meaning": "decision_maker_selection_needed",
        "module_triggers": ["trustee_selection", "agent_selection"],
        "document_requests": [],
        "next_sessions": ["fiduciary_selection_review"],
        "risk_flags": [],
    },
    "main_goals.business_continuity": {
        "system_category": "BUSINESS_PROFILE",
        "system_meaning": "business_continuity_objective",
        "module_triggers": ["business_continuity", "succession_planning"],
        "document_requests": ["operating_agreement", "business_license", "bank_authority_records"],
        "next_sessions": ["business_continuity_review"],
        "risk_flags": ["business_continuity_needed"],
    },
    "main_goals.plan_for_children": {
        "system_category": "BENEFICIARY_PROFILE",
        "system_meaning": "children_planning_objective",
        "module_triggers": ["beneficiary_planning", "guardian_review"],
        "document_requests": [],
        "next_sessions": ["children_guardian_review"],
        "risk_flags": [],
    },
    "main_goals.incapacity_planning": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "incapacity_planning_objective",
        "module_triggers": ["poa_review", "health_directive_review"],
        "document_requests": ["power_of_attorney", "health_directive"],
        "next_sessions": ["incapacity_authority_review"],
        "risk_flags": ["incapacity_planning_needed"],
    },
    "main_goals.privacy": {
        "system_category": "OBJECTIVE_PROFILE",
        "system_meaning": "privacy_preference",
        "module_triggers": ["privacy_review", "disclosure_control"],
        "document_requests": [],
        "next_sessions": ["privacy_preferences_review"],
        "risk_flags": [],
    },
    "main_goals.legacy_charitable": {
        "system_category": "LEGACY_PROFILE",
        "system_meaning": "legacy_or_charitable_objective",
        "module_triggers": ["legacy_planning", "charitable_intent_review"],
        "document_requests": [],
        "next_sessions": ["legacy_objectives_review"],
        "risk_flags": [],
    },
    "main_goals.other_goal": {
        "system_category": "OBJECTIVE_PROFILE",
        "system_meaning": "other_goal_not_listed",
        "module_triggers": ["planning_objective_review"],
        "document_requests": ["goal_description"],
        "next_sessions": ["initial_structure_review"],
        "risk_flags": [],
    },

    "main_goals.review_documents": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "document_review_objective",
        "module_triggers": ["document_audit"],
        "document_requests": ["existing_documents"],
        "next_sessions": ["document_audit_session"],
        "risk_flags": [],
    },

    # Assets
    "asset_snapshot.home": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "primary_residence",
        "module_triggers": ["real_property_review", "funding_checklist"],
        "document_requests": ["deed", "mortgage_statement", "property_tax_bill", "homeowners_insurance"],
        "next_sessions": ["real_property_deep_dive"],
        "risk_flags": [],
    },
    "asset_snapshot.rental_property": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "rental_real_property",
        "module_triggers": ["real_property_review", "liability_review", "income_property_review"],
        "document_requests": ["deed", "lease", "insurance", "mortgage_statement"],
        "next_sessions": ["real_property_deep_dive"],
        "risk_flags": ["liability_exposure_possible"],
    },
    "asset_snapshot.land": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "land_or_real_estate",
        "module_triggers": ["real_property_review"],
        "document_requests": ["deed", "tax_bill", "survey_if_available"],
        "next_sessions": ["real_property_deep_dive"],
        "risk_flags": [],
    },
    "asset_snapshot.bank_accounts": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "financial_accounts",
        "module_triggers": ["account_inventory", "beneficiary_review"],
        "document_requests": ["bank_statement", "account_registration_info"],
        "next_sessions": ["financial_account_review"],
        "risk_flags": [],
    },
    "asset_snapshot.vehicles": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "vehicle_assets",
        "module_triggers": ["title_review", "insurance_review"],
        "document_requests": ["vehicle_title", "registration", "insurance"],
        "next_sessions": ["vehicle_title_review"],
        "risk_flags": ["liability_exposure_possible"],
    },
    "asset_snapshot.business": {
        "system_category": "BUSINESS_PROFILE",
        "system_meaning": "business_asset_or_operating_entity",
        "module_triggers": ["business_continuity", "entity_review"],
        "document_requests": ["operating_agreement", "ein_letter", "business_license", "bank_authority_records"],
        "next_sessions": ["business_continuity_review"],
        "risk_flags": ["business_liability_possible"],
    },
    "asset_snapshot.retirement_accounts": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "retirement_assets",
        "module_triggers": ["beneficiary_designation_review"],
        "document_requests": ["retirement_statement", "beneficiary_designation_form"],
        "next_sessions": ["beneficiary_designation_review"],
        "risk_flags": ["transfer_restriction_review_needed"],
    },
    "asset_snapshot.life_insurance": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "life_insurance_policy",
        "module_triggers": ["beneficiary_designation_review", "insurance_review"],
        "document_requests": ["policy_declaration_page", "beneficiary_designation_form"],
        "next_sessions": ["insurance_beneficiary_review"],
        "risk_flags": [],
    },
    "asset_snapshot.investments": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "investment_assets",
        "module_triggers": ["investment_account_review", "beneficiary_review"],
        "document_requests": ["brokerage_statement", "account_registration_info"],
        "next_sessions": ["investment_account_review"],
        "risk_flags": [],
    },
    "asset_snapshot.digital_assets": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "digital_assets",
        "module_triggers": ["digital_asset_inventory"],
        "document_requests": ["digital_asset_list"],
        "next_sessions": ["digital_asset_review"],
        "risk_flags": [],
    },
    "asset_snapshot.intellectual_property": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "intellectual_property",
        "module_triggers": ["ip_inventory"],
        "document_requests": ["ip_registration_records", "licensing_agreements"],
        "next_sessions": ["intellectual_property_review"],
        "risk_flags": [],
    },
    "asset_snapshot.collectibles_heirlooms": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "collectibles_heirlooms_heritage_property",
        "module_triggers": ["heritage_asset_ledger", "special_property_inventory"],
        "document_requests": ["photos", "appraisals", "provenance_records"],
        "next_sessions": ["heritage_asset_review"],
        "risk_flags": ["special_custody_or_heritage_flag"],
    },
    "asset_snapshot.other_asset": {
        "system_category": "ASSET_PROFILE",
        "system_meaning": "other_asset_not_listed",
        "module_triggers": ["general_asset_review"],
        "document_requests": ["asset_description"],
        "next_sessions": ["asset_document_deep_dive"],
        "risk_flags": [],
    },

    "asset_snapshot.trust_estate_assets": {
        "system_category": "FIDUCIARY_CONTEXT",
        "system_meaning": "existing_trust_or_estate_assets",
        "module_triggers": ["fiduciary_inventory", "ledger_readiness"],
        "document_requests": ["trust_document", "estate_authority_document", "asset_inventory"],
        "next_sessions": ["fiduciary_inventory_review"],
        "risk_flags": ["authority_review_needed"],
    },

    # People
    "people_dependents.spouse_partner": {
        "system_category": "FAMILY_STRUCTURE",
        "system_meaning": "spouse_or_partner_involved",
        "module_triggers": ["spousal_planning"],
        "document_requests": [],
        "next_sessions": ["family_structure_review"],
        "risk_flags": [],
    },
    "people_dependents.minor_children": {
        "system_category": "BENEFICIARY_PROFILE",
        "system_meaning": "minor_children_involved",
        "module_triggers": ["guardian_review", "minor_beneficiary_controls"],
        "document_requests": [],
        "next_sessions": ["children_guardian_review"],
        "risk_flags": ["minor_children_flag"],
    },
    "people_dependents.adult_children": {
        "system_category": "BENEFICIARY_PROFILE",
        "system_meaning": "adult_children_involved",
        "module_triggers": ["beneficiary_planning"],
        "document_requests": [],
        "next_sessions": ["beneficiary_planning_review"],
        "risk_flags": [],
    },
    "people_dependents.parent_elder": {
        "system_category": "DEPENDENCY_PROFILE",
        "system_meaning": "elder_dependency",
        "module_triggers": ["elder_planning"],
        "document_requests": ["poa_if_available", "health_directive_if_available"],
        "next_sessions": ["elder_authority_review"],
        "risk_flags": ["elder_dependency_flag"],
    },
    "people_dependents.special_needs_person": {
        "system_category": "BENEFICIARY_PROFILE",
        "system_meaning": "special_needs_person_involved",
        "module_triggers": ["special_needs_review"],
        "document_requests": ["benefits_information_if_available"],
        "next_sessions": ["special_needs_planning_review"],
        "risk_flags": ["special_needs_flag"],
    },
    "people_dependents.business_partner": {
        "system_category": "BUSINESS_PROFILE",
        "system_meaning": "business_partner_involved",
        "module_triggers": ["business_governance_review"],
        "document_requests": ["operating_agreement", "partnership_agreement"],
        "next_sessions": ["business_governance_review"],
        "risk_flags": ["co_owner_or_partner_flag"],
    },
    "people_dependents.other_person": {
        "system_category": "BENEFICIARY_PROFILE",
        "system_meaning": "other_person_or_dependent_not_listed",
        "module_triggers": ["beneficiary_planning"],
        "document_requests": ["person_or_dependent_description"],
        "next_sessions": ["beneficiary_planning_review"],
        "risk_flags": [],
    },

    "people_dependents.charitable_beneficiary": {
        "system_category": "LEGACY_PROFILE",
        "system_meaning": "charitable_or_legacy_beneficiary",
        "module_triggers": ["legacy_planning", "charitable_intent_review"],
        "document_requests": [],
        "next_sessions": ["legacy_objectives_review"],
        "risk_flags": [],
    },

    # Concerns
    "concerns.family_conflict": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "family_conflict_concern",
        "module_triggers": ["governance_controls", "conflict_review"],
        "document_requests": ["existing_will", "existing_trust", "family_agreements"],
        "next_sessions": ["governance_conflict_review"],
        "risk_flags": ["family_conflict_risk"],
    },
    "concerns.lawsuit_concern": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "lawsuit_concern",
        "module_triggers": ["risk_review"],
        "document_requests": ["court_documents", "claim_letters_if_available"],
        "next_sessions": ["risk_triage_review"],
        "risk_flags": ["urgent_or_legal_review_flag"],
    },
    "concerns.debt_creditor": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "debt_or_creditor_concern",
        "module_triggers": ["liability_review"],
        "document_requests": ["debt_statements", "creditor_letters_if_available"],
        "next_sessions": ["liability_review"],
        "risk_flags": ["creditor_pressure_flag"],
    },
    "concerns.tax_concern": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "tax_concern",
        "module_triggers": ["tax_professional_review"],
        "document_requests": ["tax_notices", "tax_filings"],
        "next_sessions": ["tax_review_referral"],
        "risk_flags": ["tax_review_flag"],
    },
    "concerns.business_liability": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "business_liability_concern",
        "module_triggers": ["business_liability_review"],
        "document_requests": ["operating_agreement", "insurance_policies"],
        "next_sessions": ["business_liability_review"],
        "risk_flags": ["business_liability_possible"],
    },
    "concerns.divorce_remarriage": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "divorce_or_remarriage_concern",
        "module_triggers": ["family_structure_review", "beneficiary_review"],
        "document_requests": ["divorce_decree_if_available", "prenuptial_or_postnuptial_if_available"],
        "next_sessions": ["family_structure_review"],
        "risk_flags": ["family_status_complexity"],
    },
    "concerns.multi_state_property": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "multi_state_property_concern",
        "module_triggers": ["multi_jurisdiction_review", "real_property_review"],
        "document_requests": ["deeds", "property_tax_bills"],
        "next_sessions": ["multi_jurisdiction_property_review"],
        "risk_flags": ["multi_jurisdiction_flag"],
    },
    "concerns.medical_incapacity": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "medical_or_incapacity_concern",
        "module_triggers": ["poa_review", "health_directive_review"],
        "document_requests": ["power_of_attorney", "health_directive", "medical_authority_documents"],
        "next_sessions": ["incapacity_authority_review"],
        "risk_flags": ["incapacity_planning_needed"],
    },
    "concerns.no_trusted_successor": {
        "system_category": "FIDUCIARY_READINESS",
        "system_meaning": "no_trusted_successor_identified",
        "module_triggers": ["successor_selection"],
        "document_requests": [],
        "next_sessions": ["fiduciary_selection_review"],
        "risk_flags": ["successor_gap_flag"],
    },
    "concerns.none_apply": {
        "system_category": "RISK_PROFILE",
        "system_meaning": "no_initial_concerns_reported",
        "module_triggers": [],
        "document_requests": [],
        "next_sessions": [],
        "risk_flags": [],
    },

    "concerns.missing_documents": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "missing_documents_concern",
        "module_triggers": ["document_collection"],
        "document_requests": ["document_checklist"],
        "next_sessions": ["document_collection_review"],
        "risk_flags": ["documentation_gap"],
    },

    # Existing docs
    "existing_documents.will": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "will_exists",
        "module_triggers": ["document_audit"],
        "document_requests": ["will"],
        "next_sessions": ["document_audit_session"],
        "risk_flags": [],
    },
    "existing_documents.trust": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "trust_exists",
        "module_triggers": ["trust_audit"],
        "document_requests": ["trust_document"],
        "next_sessions": ["trust_document_review"],
        "risk_flags": [],
    },
    "existing_documents.power_of_attorney": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "poa_exists",
        "module_triggers": ["authority_document_review"],
        "document_requests": ["power_of_attorney"],
        "next_sessions": ["authority_document_review"],
        "risk_flags": [],
    },
    "existing_documents.health_directive": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "health_directive_exists",
        "module_triggers": ["health_directive_review"],
        "document_requests": ["health_directive"],
        "next_sessions": ["authority_document_review"],
        "risk_flags": [],
    },
    "existing_documents.deed": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "deed_available",
        "module_triggers": ["real_property_review"],
        "document_requests": ["deed"],
        "next_sessions": ["real_property_deep_dive"],
        "risk_flags": [],
    },
    "existing_documents.mortgage_statement": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "mortgage_statement_available",
        "module_triggers": ["real_property_review"],
        "document_requests": ["mortgage_statement"],
        "next_sessions": ["real_property_deep_dive"],
        "risk_flags": [],
    },
    "existing_documents.business_documents": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "business_documents_exist",
        "module_triggers": ["business_document_audit"],
        "document_requests": ["business_documents"],
        "next_sessions": ["business_continuity_review"],
        "risk_flags": [],
    },
    "existing_documents.insurance_policies": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "insurance_documents_exist",
        "module_triggers": ["insurance_review"],
        "document_requests": ["insurance_policies"],
        "next_sessions": ["insurance_beneficiary_review"],
        "risk_flags": [],
    },
    "existing_documents.beneficiary_forms": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "beneficiary_forms_exist",
        "module_triggers": ["beneficiary_designation_review"],
        "document_requests": ["beneficiary_forms"],
        "next_sessions": ["beneficiary_designation_review"],
        "risk_flags": [],
    },
    "existing_documents.tax_filings": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "tax_filings_available",
        "module_triggers": ["tax_professional_review"],
        "document_requests": ["tax_filings"],
        "next_sessions": ["tax_review_referral"],
        "risk_flags": ["tax_review_flag"],
    },
    "existing_documents.court_documents": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "court_documents_available",
        "module_triggers": ["risk_review"],
        "document_requests": ["court_documents"],
        "next_sessions": ["risk_triage_review"],
        "risk_flags": ["urgent_or_legal_review_flag"],
    },
    "existing_documents.other_document": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "other_document_available",
        "module_triggers": ["document_audit"],
        "document_requests": ["other_document_description"],
        "next_sessions": ["document_audit_session"],
        "risk_flags": [],
    },

    "existing_documents.none": {
        "system_category": "DOCUMENT_STATUS",
        "system_meaning": "no_documents_available",
        "module_triggers": ["foundational_estate_package", "document_collection"],
        "document_requests": ["document_checklist"],
        "next_sessions": ["foundational_planning_review"],
        "risk_flags": ["documentation_gap"],
    },
}


def ensure_intake_translation_tables():
    ensure_intake_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            question_key TEXT NOT NULL,
            answer_key TEXT NOT NULL,
            answer_label TEXT,
            created_at TEXT,
            created_by TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            source_key TEXT NOT NULL,
            system_category TEXT,
            system_meaning TEXT,
            module_trigger TEXT,
            document_request TEXT,
            next_session TEXT,
            risk_flag TEXT,
            created_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_universal_intake_questions():
    return UNIVERSAL_INTAKE_QUESTIONS


def get_translation_rules():
    return TRANSLATION_RULES


def _normalize_answer_values(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v) for v in value if str(v).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def translate_answer(question_key, answer_key):
    source_key = f"{question_key}.{answer_key}"
    return TRANSLATION_RULES.get(source_key)


def save_universal_profile_answers(intake_id, form_data, created_by=None):
    ensure_intake_translation_tables()

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    saved_answers = []
    translations = []

    for question_key, question in UNIVERSAL_INTAKE_QUESTIONS.items():
        if question["input_type"] == "multi":
            values = form_data.getlist(question_key) if hasattr(form_data, "getlist") else _normalize_answer_values(form_data.get(question_key))
        else:
            values = _normalize_answer_values(form_data.get(question_key))

        for answer_key in values:
            answer_label = question["options"].get(answer_key, answer_key)
            source_key = f"{question_key}.{answer_key}"
            rule = TRANSLATION_RULES.get(source_key)

            cur.execute("""
                INSERT INTO intake_answers (
                    intake_id, firm_id, question_key, answer_key, answer_label,
                    created_at, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                intake_id,
                firm_id,
                question_key,
                answer_key,
                answer_label,
                now,
                created_by,
            ))

            saved_answers.append({
                "question_key": question_key,
                "answer_key": answer_key,
                "answer_label": answer_label,
            })

            if rule:
                module_triggers = rule.get("module_triggers") or [None]
                document_requests = rule.get("document_requests") or [None]
                next_sessions = rule.get("next_sessions") or [None]
                risk_flags = rule.get("risk_flags") or [None]

                max_len = max(len(module_triggers), len(document_requests), len(next_sessions), len(risk_flags))

                for idx in range(max_len):
                    module_trigger = module_triggers[idx] if idx < len(module_triggers) else None
                    document_request = document_requests[idx] if idx < len(document_requests) else None
                    next_session = next_sessions[idx] if idx < len(next_sessions) else None
                    risk_flag = risk_flags[idx] if idx < len(risk_flags) else None

                    cur.execute("""
                        INSERT INTO intake_translations (
                            intake_id, firm_id, source_key, system_category,
                            system_meaning, module_trigger, document_request,
                            next_session, risk_flag, created_at, created_by
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        intake_id,
                        firm_id,
                        source_key,
                        rule.get("system_category"),
                        rule.get("system_meaning"),
                        module_trigger,
                        document_request,
                        next_session,
                        risk_flag,
                        now,
                        created_by,
                    ))

                    translations.append({
                        "source_key": source_key,
                        "system_category": rule.get("system_category"),
                        "system_meaning": rule.get("system_meaning"),
                        "module_trigger": module_trigger,
                        "document_request": document_request,
                        "next_session": next_session,
                        "risk_flag": risk_flag,
                    })

    cur.execute("""
        UPDATE intake_sessions
        SET status = ?, updated_at = ?
        WHERE intake_id = ?
    """, ("universal_profile_completed", now, intake_id))

    conn.commit()
    conn.close()

    scores = score_and_save_intake(intake_id, translations, created_by=created_by)

    return {
        "intake_id": intake_id,
        "answers": saved_answers,
        "translations": translations,
        "summary": summarize_intake_translations(translations),
        "scores": scores,
    }


def summarize_intake_translations(translations):
    def ordered_unique(values):
        seen = set()
        output = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                output.append(value)
        return output

    return {
        "system_categories": ordered_unique(t.get("system_category") for t in translations),
        "system_meanings": ordered_unique(t.get("system_meaning") for t in translations),
        "module_triggers": ordered_unique(t.get("module_trigger") for t in translations),
        "document_requests": ordered_unique(t.get("document_request") for t in translations),
        "next_sessions": ordered_unique(t.get("next_session") for t in translations),
        "risk_flags": ordered_unique(t.get("risk_flag") for t in translations),
    }


def get_intake_session(intake_id):
    ensure_intake_tables()
    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()

    cur.execute("""
        SELECT intake_id, intake_lane, user_posture, default_depth, risk_posture,
               professional_review_recommended, automation_limits, next_screen,
               status, created_at, updated_at
        FROM intake_sessions
        WHERE intake_id = ?
    """, (intake_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    keys = [
        "intake_id", "intake_lane", "user_posture", "default_depth",
        "risk_posture", "professional_review_recommended", "automation_limits",
        "next_screen", "status", "created_at", "updated_at"
    ]
    return dict(zip(keys, row))


# -------------------------------------------------------------------
# INT-1C — Intake Scoring Engine
# -------------------------------------------------------------------

COMPLEXITY_WEIGHTS = {
    # Asset / structure complexity
    "real_property_review": 2,
    "funding_checklist": 2,
    "income_property_review": 3,
    "business_continuity": 3,
    "entity_review": 3,
    "business_governance_review": 3,
    "multi_jurisdiction_review": 4,
    "fiduciary_administration": 3,
    "trust_audit": 2,
    "fiduciary_inventory": 3,
    "ledger_readiness": 2,
    "special_needs_review": 4,
    "heritage_asset_ledger": 2,
    "ip_inventory": 2,
    "digital_asset_inventory": 1,

    # Family/governance complexity
    "guardian_review": 2,
    "minor_beneficiary_controls": 2,
    "governance_controls": 3,
    "conflict_review": 3,
    "successor_selection": 2,
    "elder_planning": 3,
}

URGENCY_WEIGHTS = {
    # Strong urgency flags
    "urgent_or_legal_review_flag": 5,
    "creditor_pressure_flag": 4,
    "tax_review_flag": 4,
    "incapacity_planning_needed": 4,
    "authority_review_needed": 3,
    "family_conflict_risk": 3,

    # Moderate urgency flags
    "business_continuity_needed": 3,
    "business_liability_possible": 3,
    "successor_gap_flag": 3,
    "documentation_gap": 3,
    "minor_children_flag": 2,
    "special_needs_flag": 4,
    "elder_dependency_flag": 3,
    "multi_jurisdiction_flag": 3,
    "liability_exposure_possible": 2,
    "transfer_restriction_review_needed": 2,
    "co_owner_or_partner_flag": 2,
    "family_status_complexity": 2,
    "special_custody_or_heritage_flag": 1,
}

READINESS_WEIGHTS = {
    # Existing documents increase readiness
    "will_exists": 1,
    "trust_exists": 2,
    "poa_exists": 1,
    "health_directive_exists": 1,
    "deed_available": 2,
    "mortgage_statement_available": 1,
    "business_documents_exist": 2,
    "insurance_documents_exist": 1,
    "beneficiary_forms_exist": 1,
    "tax_filings_available": 1,
    "court_documents_available": 1,

    # Available document requests can also indicate partial readiness
    "will": 1,
    "trust_document": 2,
    "power_of_attorney": 1,
    "health_directive": 1,
    "deed": 2,
    "mortgage_statement": 1,
    "business_documents": 2,
    "insurance_policies": 1,
    "beneficiary_forms": 1,
    "tax_filings": 1,
    "court_documents": 1,
}


def ensure_intake_scoring_tables():
    ensure_intake_translation_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            complexity_score INTEGER DEFAULT 0,
            complexity_level TEXT,
            urgency_score INTEGER DEFAULT 0,
            urgency_level TEXT,
            readiness_score INTEGER DEFAULT 0,
            readiness_level TEXT,
            scoring_notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def classify_complexity(score):
    if score <= 4:
        return "Simple"
    if score <= 9:
        return "Moderate"
    if score <= 15:
        return "Advanced"
    return "Complex"


def classify_urgency(score):
    if score <= 3:
        return "Low"
    if score <= 7:
        return "Medium"
    return "High"


def classify_readiness(score):
    if score <= 2:
        return "Not Ready"
    if score <= 6:
        return "Partially Ready"
    return "Ready for Deep Review"


def calculate_intake_scores(translations):
    complexity_score = 0
    urgency_score = 0
    readiness_score = 0

    complexity_hits = []
    urgency_hits = []
    readiness_hits = []

    for item in translations:
        module_trigger = item.get("module_trigger")
        risk_flag = item.get("risk_flag")
        system_meaning = item.get("system_meaning")
        document_request = item.get("document_request")

        if module_trigger in COMPLEXITY_WEIGHTS:
            value = COMPLEXITY_WEIGHTS[module_trigger]
            complexity_score += value
            complexity_hits.append(f"{module_trigger}+{value}")

        if risk_flag in URGENCY_WEIGHTS:
            value = URGENCY_WEIGHTS[risk_flag]
            urgency_score += value
            urgency_hits.append(f"{risk_flag}+{value}")

        if system_meaning in READINESS_WEIGHTS:
            value = READINESS_WEIGHTS[system_meaning]
            readiness_score += value
            readiness_hits.append(f"{system_meaning}+{value}")

        if document_request in READINESS_WEIGHTS:
            value = READINESS_WEIGHTS[document_request]
            readiness_score += value
            readiness_hits.append(f"{document_request}+{value}")

    return {
        "complexity_score": complexity_score,
        "complexity_level": classify_complexity(complexity_score),
        "urgency_score": urgency_score,
        "urgency_level": classify_urgency(urgency_score),
        "readiness_score": readiness_score,
        "readiness_level": classify_readiness(readiness_score),
        "scoring_notes": {
            "complexity_hits": complexity_hits,
            "urgency_hits": urgency_hits,
            "readiness_hits": readiness_hits,
        }
    }


def save_intake_scores(intake_id, scores, created_by=None):
    ensure_intake_scoring_tables()

    import json
    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO intake_scores (
            intake_id, firm_id, complexity_score, complexity_level,
            urgency_score, urgency_level, readiness_score, readiness_level,
            scoring_notes, created_at, updated_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        scores["complexity_score"],
        scores["complexity_level"],
        scores["urgency_score"],
        scores["urgency_level"],
        scores["readiness_score"],
        scores["readiness_level"],
        json.dumps(scores.get("scoring_notes", {})),
        now,
        now,
        created_by,
    ))

    cur.execute("""
        UPDATE intake_sessions
        SET status = ?, updated_at = ?
        WHERE intake_id = ?
    """, ("scored", now, intake_id))

    conn.commit()
    conn.close()

    return scores


def score_and_save_intake(intake_id, translations, created_by=None):
    scores = calculate_intake_scores(translations)
    save_intake_scores(intake_id, scores, created_by=created_by)
    return scores


# -------------------------------------------------------------------
# INT-1D — Client-Facing Initial Fiduciary Snapshot
# -------------------------------------------------------------------

CLIENT_PRIORITY_LABELS = {
    "family_structure_review": "Review family structure and decision-maker roles",
    "initial_structure_review": "Review the stated planning goal and place it into the right follow-up path",
    "fiduciary_selection_review": "Choose or confirm trusted decision-makers",
    "real_property_deep_dive": "Review real property ownership and supporting documents",
    "financial_account_review": "Review financial accounts and how they are titled",
    "business_continuity_review": "Review business continuity and operating authority",
    "beneficiary_planning_review": "Review beneficiary planning and distribution intentions",
    "business_governance_review": "Review business ownership, partners, and governance",
    "governance_conflict_review": "Address family conflict or governance concerns early",
    "risk_triage_review": "Complete a risk-focused review before taking major action",
    "tax_review_referral": "Gather tax records for qualified tax review",
    "foundational_planning_review": "Begin foundational estate and trust planning",
    "children_guardian_review": "Review minor child planning and guardian choices",
    "elder_authority_review": "Review elder, parent, or incapacity authority documents",
    "special_needs_planning_review": "Review special-needs planning before final documents",
    "insurance_beneficiary_review": "Review insurance ownership and beneficiary designations",
    "beneficiary_designation_review": "Review beneficiary designations on non-trust assets",
    "investment_account_review": "Review investment accounts and registration details",
    "digital_asset_review": "Prepare a digital asset inventory",
    "intellectual_property_review": "Review intellectual property ownership and records",
    "heritage_asset_review": "Document heritage, heirloom, or special family property",
    "fiduciary_inventory_review": "Build or verify trust/estate inventory records",
    "document_collection_review": "Gather missing documents before deeper review",
    "authority_document_review": "Review authority documents such as POA or health directive",
    "privacy_preferences_review": "Clarify privacy and disclosure preferences",
    "legacy_objectives_review": "Clarify legacy, charitable, or community goals",
    "probate_avoidance_review": "Review probate-avoidance objectives and document gaps",
    "asset_document_deep_dive": "Organize assets and supporting records",
    "general_asset_review": "Review other assets not listed in the standard intake",
    "planning_objective_review": "Review other planning goals not listed in the standard intake",
    "multi_jurisdiction_property_review": "Review property located in more than one state",
    "business_liability_review": "Review business liability and insurance concerns",
    "liability_review": "Review debt, creditor, or liability concerns",
    "incapacity_authority_review": "Review incapacity planning and authority documents",
    "document_audit_session": "Audit existing estate, trust, or authority documents",
    "trust_document_review": "Review existing trust documents",
}

CLIENT_DOCUMENT_LABELS = {
    "deed": "Deed or title record",
    "deeds": "Deeds or title records",
    "mortgage_statement": "Mortgage statement",
    "property_tax_bill": "Property tax bill",
    "tax_bill": "Property tax bill",
    "survey_if_available": "Survey, if available",
    "homeowners_insurance": "Homeowners insurance declarations",
    "insurance": "Insurance policy or declarations",
    "insurance_policies": "Insurance policies",
    "policy_declaration_page": "Insurance policy declaration page",
    "beneficiary_designation_form": "Beneficiary designation form",
    "beneficiary_forms": "Beneficiary designation forms",
    "bank_statement": "Bank or financial account statement",
    "asset_statements": "Asset statements",
    "account_registration_info": "Account registration information",
    "retirement_statement": "Retirement account statement",
    "brokerage_statement": "Brokerage or investment statement",
    "operating_agreement": "Operating agreement",
    "partnership_agreement": "Partnership agreement",
    "ein_letter": "EIN letter",
    "business_license": "Business license",
    "business_documents": "Business documents",
    "bank_authority_records": "Business bank authority records",
    "existing_will": "Existing will",
    "will": "Will",
    "existing_trust": "Existing trust",
    "trust_document": "Trust document",
    "power_of_attorney": "Power of attorney",
    "poa_if_available": "Power of attorney, if available",
    "health_directive": "Health directive",
    "health_directive_if_available": "Health directive, if available",
    "medical_authority_documents": "Medical authority documents",
    "family_agreements": "Family agreements, if any",
    "court_documents": "Court documents",
    "claim_letters_if_available": "Claim letters, if available",
    "tax_notices": "Tax notices",
    "tax_filings": "Tax filings",
    "debt_statements": "Debt statements",
    "creditor_letters_if_available": "Creditor letters, if available",
    "divorce_decree_if_available": "Divorce decree, if available",
    "prenuptial_or_postnuptial_if_available": "Prenuptial or postnuptial agreement, if available",
    "document_checklist": "Basic document checklist",
    "goal_description": "Description of other planning goal not listed",
    "asset_description": "Description of other asset not listed",
    "person_or_dependent_description": "Description of other person, dependent, or role not listed",
    "other_document_description": "Description or copy of other document not listed",
    "digital_asset_list": "Digital asset list",
    "ip_registration_records": "IP registration records",
    "licensing_agreements": "Licensing agreements",
    "photos": "Photos or visual inventory",
    "appraisals": "Appraisals",
    "provenance_records": "Provenance or history records",
    "trust_document": "Trust document",
    "estate_authority_document": "Estate authority document",
    "letters_testamentary_or_authority": "Letters testamentary or authority document",
    "asset_inventory": "Asset inventory",
    "existing_documents": "Existing documents",
    "existing_care_documents": "Existing care documents",
    "benefits_information_if_available": "Benefits information, if available",
}

CLIENT_RISK_LABELS = {
    "urgent_or_legal_review_flag": "Legal, court, or urgent review may be needed",
    "creditor_pressure_flag": "Debt or creditor pressure may require careful review",
    "tax_review_flag": "Tax records should be reviewed by a qualified professional",
    "incapacity_planning_needed": "Incapacity planning may need attention",
    "authority_review_needed": "Authority documents should be verified",
    "family_conflict_risk": "Family conflict risk should be addressed early",
    "business_continuity_needed": "Business continuity planning should be prioritized",
    "business_liability_possible": "Business liability should be reviewed",
    "successor_gap_flag": "A successor decision-maker gap may exist",
    "documentation_gap": "Important documents may be missing",
    "minor_children_flag": "Minor child planning should be reviewed",
    "special_needs_flag": "Special-needs planning should be reviewed carefully",
    "elder_dependency_flag": "Elder or parent support planning may be involved",
    "multi_jurisdiction_flag": "Property in multiple jurisdictions may need extra review",
    "liability_exposure_possible": "Possible liability exposure should be reviewed",
    "transfer_restriction_review_needed": "Some assets may have transfer restrictions",
    "co_owner_or_partner_flag": "Co-owner or partner interests should be reviewed",
    "family_status_complexity": "Family status changes may affect planning",
    "special_custody_or_heritage_flag": "Special custody or heritage property should be documented",
}

PLANNING_TYPE_LABELS = {
    "FAMILY_STRUCTURE": "Family Planning",
    "ASSET_PROFILE": "Asset Organization",
    "BUSINESS_PROFILE": "Business Continuity",
    "BENEFICIARY_PROFILE": "Beneficiary Planning",
    "FIDUCIARY_READINESS": "Decision-Maker Planning",
    "FIDUCIARY_CONTEXT": "Trust or Estate Administration",
    "RISK_PROFILE": "Risk Review",
    "DOCUMENT_STATUS": "Document Readiness",
    "DEPENDENCY_PROFILE": "Elder / Dependency Planning",
    "LEGACY_PROFILE": "Legacy or Charitable Planning",
    "PERSON_PROFILE": "Individual Planning",
    "OBJECTIVE_PROFILE": "Planning Objectives",
}


def _client_unique(values, limit=None):
    seen = set()
    output = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    if limit:
        return output[:limit]
    return output


def _label_items(values, labels, limit=None):
    labeled = []
    for value in values:
        if not value:
            continue
        labeled.append(labels.get(value, value.replace("_", " ").title()))
    return _client_unique(labeled, limit=limit)


def determine_primary_next_session(summary):
    sessions = summary.get("next_sessions", []) or []
    priority_order = [
        "risk_triage_review",
        "tax_review_referral",
        "governance_conflict_review",
        "business_continuity_review",
        "real_property_deep_dive",
        "asset_document_deep_dive",
        "fiduciary_selection_review",
        "children_guardian_review",
        "beneficiary_planning_review",
        "document_collection_review",
        "foundational_planning_review",
    ]

    for item in priority_order:
        if item in sessions:
            return CLIENT_PRIORITY_LABELS.get(item, item.replace("_", " ").title())

    if sessions:
        first = sessions[0]
        return CLIENT_PRIORITY_LABELS.get(first, first.replace("_", " ").title())

    return "Initial structure review"


def build_client_snapshot(result):
    summary = result.get("summary", {}) or {}
    scores = result.get("scores", {}) or {}

    categories = summary.get("system_categories", []) or []
    next_sessions = summary.get("next_sessions", []) or []
    document_requests = summary.get("document_requests", []) or []
    risk_flags = summary.get("risk_flags", []) or []

    planning_types = _label_items(categories, PLANNING_TYPE_LABELS, limit=5)
    top_priorities = _label_items(next_sessions, CLIENT_PRIORITY_LABELS, limit=6)
    documents_to_gather = _label_items(document_requests, CLIENT_DOCUMENT_LABELS, limit=12)
    review_flags = _label_items(risk_flags, CLIENT_RISK_LABELS, limit=6)

    if not top_priorities:
        top_priorities = ["Complete a deeper review of family, assets, documents, and decision-makers"]

    if not documents_to_gather:
        documents_to_gather = ["Any existing estate, trust, property, business, insurance, or account documents"]

    next_session = determine_primary_next_session(summary)

    complexity_level = scores.get("complexity_level", "Not Yet Rated")
    urgency_level = scores.get("urgency_level", "Not Yet Rated")
    readiness_level = scores.get("readiness_level", "Not Yet Rated")

    if urgency_level == "High":
        review_priority = "High"
    elif complexity_level in ["Advanced", "Complex"]:
        review_priority = "Elevated"
    elif urgency_level == "Medium":
        review_priority = "Moderate"
    else:
        review_priority = "Standard"

    return {
        "intake_id": result.get("intake_id"),
        "planning_types": planning_types,
        "complexity_level": complexity_level,
        "urgency_level": urgency_level,
        "readiness_level": readiness_level,
        "review_priority": review_priority,
        "top_priorities": top_priorities,
        "documents_to_gather": documents_to_gather,
        "review_flags": review_flags,
        "recommended_next_session": next_session,
        "technical_result": result,
    }


# -------------------------------------------------------------------
# INT-1E — Save Snapshot + Intake Dashboard List
# -------------------------------------------------------------------

def ensure_intake_snapshot_tables():
    ensure_intake_scoring_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            snapshot_json TEXT,
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_client_snapshot(intake_id, snapshot, created_by=None):
    ensure_intake_snapshot_tables()

    import json
    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    # Keep stored JSON compact and avoid recursive technical payload bloat.
    stored_snapshot = dict(snapshot)
    stored_snapshot.pop("technical_result", None)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO intake_snapshots (
            intake_id, firm_id, snapshot_json, created_at, updated_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(intake_id) DO UPDATE SET
            snapshot_json = excluded.snapshot_json,
            updated_at = excluded.updated_at,
            created_by = excluded.created_by
    """, (
        intake_id,
        firm_id,
        json.dumps(stored_snapshot),
        now,
        now,
        created_by,
    ))

    cur.execute("""
        UPDATE intake_sessions
        SET status = ?, updated_at = ?
        WHERE intake_id = ?
    """, ("snapshot_saved", now, intake_id))

    conn.commit()
    conn.close()

    return stored_snapshot


def get_latest_intake_score_map():
    ensure_intake_scoring_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s1.intake_id,
               s1.complexity_score, s1.complexity_level,
               s1.urgency_score, s1.urgency_level,
               s1.readiness_score, s1.readiness_level
        FROM intake_scores s1
        INNER JOIN (
            SELECT intake_id, MAX(id) AS max_id
            FROM intake_scores
            GROUP BY intake_id
        ) latest
        ON s1.id = latest.max_id
    """)

    rows = cur.fetchall()
    conn.close()

    score_map = {}
    for row in rows:
        score_map[row[0]] = {
            "complexity_score": row[1],
            "complexity_level": row[2],
            "urgency_score": row[3],
            "urgency_level": row[4],
            "readiness_score": row[5],
            "readiness_level": row[6],
        }
    return score_map


def list_intake_dashboard(limit=50):
    ensure_intake_snapshot_tables()
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT intake_id, intake_lane, user_posture, default_depth, risk_posture,
               professional_review_recommended, automation_limits, next_screen,
               status, created_at, updated_at
        FROM intake_sessions
        WHERE firm_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (firm_id, limit))

    rows = cur.fetchall()
    conn.close()

    scores = get_latest_intake_score_map()

    items = []
    for row in rows:
        intake_id = row[0]
        score = scores.get(intake_id, {})

        items.append({
            "intake_id": intake_id,
            "intake_lane": row[1],
            "user_posture": row[2],
            "default_depth": row[3],
            "risk_posture": row[4],
            "professional_review_recommended": bool(row[5]),
            "automation_limits": row[6],
            "next_screen": row[7],
            "status": row[8],
            "created_at": row[9],
            "updated_at": row[10],
            "complexity_level": score.get("complexity_level", "—"),
            "urgency_level": score.get("urgency_level", "—"),
            "readiness_level": score.get("readiness_level", "—"),
        })

    return items


def get_intake_answers(intake_id):
    ensure_intake_translation_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT question_key, answer_key, answer_label
        FROM intake_answers
        WHERE intake_id = ?
        ORDER BY id ASC
    """, (intake_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "question_key": row[0],
            "answer_key": row[1],
            "answer_label": row[2],
        }
        for row in rows
    ]


def get_intake_translations_for_snapshot(intake_id):
    ensure_intake_translation_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT source_key, system_category, system_meaning,
               module_trigger, document_request, next_session, risk_flag
        FROM intake_translations
        WHERE intake_id = ?
        ORDER BY id ASC
    """, (intake_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "source_key": row[0],
            "system_category": row[1],
            "system_meaning": row[2],
            "module_trigger": row[3],
            "document_request": row[4],
            "next_session": row[5],
            "risk_flag": row[6],
        }
        for row in rows
    ]


def get_latest_intake_scores(intake_id):
    ensure_intake_scoring_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT complexity_score, complexity_level,
               urgency_score, urgency_level,
               readiness_score, readiness_level,
               scoring_notes
        FROM intake_scores
        WHERE intake_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (intake_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return {}

    return {
        "complexity_score": row[0],
        "complexity_level": row[1],
        "urgency_score": row[2],
        "urgency_level": row[3],
        "readiness_score": row[4],
        "readiness_level": row[5],
        "scoring_notes": row[6],
    }


def rebuild_intake_result(intake_id):
    translations = get_intake_translations_for_snapshot(intake_id)
    scores = get_latest_intake_scores(intake_id)

    return {
        "intake_id": intake_id,
        "answers": get_intake_answers(intake_id),
        "translations": translations,
        "summary": summarize_intake_translations(translations),
        "scores": scores,
    }


def get_saved_client_snapshot(intake_id):
    ensure_intake_snapshot_tables()

    import json

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT snapshot_json
        FROM intake_snapshots
        WHERE intake_id = ?
        LIMIT 1
    """, (intake_id,))

    row = cur.fetchone()
    conn.close()

    if row and row[0]:
        saved = json.loads(row[0])
        technical_result = rebuild_intake_result(intake_id)
        saved["technical_result"] = technical_result
        return saved, technical_result

    # Fallback: rebuild from stored translations/scores if no snapshot row exists.
    technical_result = rebuild_intake_result(intake_id)
    if not technical_result.get("translations"):
        return None, None

    snapshot = build_client_snapshot(technical_result)
    snapshot["technical_result"] = technical_result
    return snapshot, technical_result


# -------------------------------------------------------------------
# INT-1F — Intake Resume + Completion Status Controls
# -------------------------------------------------------------------

COMPLETED_INTAKE_STATUSES = {
    "scored",
    "snapshot_saved",
    "completed",
}

INCOMPLETE_INTAKE_STATUSES = {
    "lane_selected",
    "started",
    "universal_profile_started",
}


def intake_is_completed(status):
    return status in COMPLETED_INTAKE_STATUSES


def intake_is_incomplete(status):
    return not intake_is_completed(status)


def get_intake_resume_target(intake_id):
    """
    Decide where an intake should resume.
    V1 resumes incomplete lane-selected sessions at universal profile.
    Later versions can resume at lane-specific screens.
    """
    intake = get_intake_session(intake_id)
    if not intake:
        return None

    status = intake.get("status")

    if intake_is_completed(status):
        return {
            "route": "intake_saved_snapshot",
            "intake_id": intake_id,
            "label": "View snapshot",
        }

    return {
        "route": "intake_universal_profile",
        "intake_id": intake_id,
        "label": "Continue intake",
    }


def list_intake_dashboard_with_controls(limit=100):
    items = list_intake_dashboard(limit=limit)

    for item in items:
        status = item.get("status")
        completed = intake_is_completed(status)

        item["is_completed"] = completed
        item["is_incomplete"] = not completed
        item["status_label"] = "Completed" if completed else "Incomplete"

        if completed:
            item["primary_action"] = "View snapshot"
            item["primary_route"] = "snapshot"
        else:
            item["primary_action"] = "Continue intake"
            item["primary_route"] = "continue"

        if item.get("complexity_level") == "—" and not completed:
            item["complexity_level"] = "Pending"

        if item.get("urgency_level") == "—" and not completed:
            item["urgency_level"] = "Pending"

        if item.get("readiness_level") == "—" and not completed:
            item["readiness_level"] = "Pending"

    return items


# -------------------------------------------------------------------
# INT-1G — Dashboard Polish + Snapshot Print/Export Prep
# -------------------------------------------------------------------

def format_intake_timestamp(value):
    if not value:
        return "—"

    try:
        raw = str(value).replace("T", " ")
        if "." in raw:
            raw = raw.split(".")[0]
        return raw
    except Exception:
        return str(value)


def decorate_intake_dashboard_items(items, status_filter="all"):
    decorated = []

    for item in items:
        item = dict(item)

        item["updated_display"] = format_intake_timestamp(
            item.get("updated_at") or item.get("created_at")
        )

        urgency = item.get("urgency_level") or "Pending"
        readiness = item.get("readiness_level") or "Pending"
        complexity = item.get("complexity_level") or "Pending"

        item["urgency_badge"] = urgency
        item["readiness_badge"] = readiness
        item["complexity_badge"] = complexity

        item["urgency_class"] = "badge-high" if urgency == "High" else "badge-medium" if urgency == "Medium" else "badge-low" if urgency == "Low" else "badge-pending"
        item["readiness_class"] = "badge-ready" if readiness == "Ready for Deep Review" else "badge-medium" if readiness == "Partially Ready" else "badge-pending"
        item["complexity_class"] = "badge-high" if complexity in ["Advanced", "Complex"] else "badge-medium" if complexity == "Moderate" else "badge-low" if complexity == "Simple" else "badge-pending"

        if status_filter == "completed" and not item.get("is_completed"):
            continue
        if status_filter == "incomplete" and not item.get("is_incomplete"):
            continue
        if status_filter == "high_urgency" and item.get("urgency_level") != "High":
            continue

        decorated.append(item)

    return decorated


def list_intake_dashboard_polished(limit=100, status_filter="all"):
    items = list_intake_dashboard_with_controls(limit=limit)
    return decorate_intake_dashboard_items(items, status_filter=status_filter)


def prepare_snapshot_export_metadata(intake_id):
    snapshot, result = get_saved_client_snapshot(intake_id)
    if not snapshot:
        return None

    return {
        "intake_id": intake_id,
        "snapshot": snapshot,
        "result": result,
        "export_ready": True,
        "available_exports": [
            "print_view",
            "future_pdf_export",
            "future_docx_export",
        ],
        "note": "Export preparation is ready. PDF/DOCX generation is intentionally not activated in INT-1G.",
    }


# -------------------------------------------------------------------
# INT-1H — Intake Review Notes + Internal Staff Comments
# -------------------------------------------------------------------

VALID_REVIEW_NOTE_TYPES = {
    "general": "General Note",
    "risk": "Risk / Review Concern",
    "document": "Document Follow-Up",
    "client_followup": "Client Follow-Up",
    "professional_review": "Professional Review",
    "admin": "Administrative Note",
}

VALID_REVIEW_PRIORITIES = {
    "low": "Low",
    "normal": "Normal",
    "high": "High",
    "urgent": "Urgent",
}

VALID_FOLLOWUP_STATUSES = {
    "open": "Open",
    "pending_client": "Pending Client",
    "pending_review": "Pending Review",
    "resolved": "Resolved",
}


def ensure_intake_review_note_tables():
    ensure_intake_snapshot_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_review_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            note_type TEXT DEFAULT 'general',
            priority TEXT DEFAULT 'normal',
            followup_status TEXT DEFAULT 'open',
            note_body TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_intake_review_note(
    intake_id,
    note_body,
    note_type="general",
    priority="normal",
    followup_status="open",
    created_by=None
):
    ensure_intake_review_note_tables()

    note_body = (note_body or "").strip()
    if not note_body:
        raise ValueError("Review note cannot be blank.")

    if note_type not in VALID_REVIEW_NOTE_TYPES:
        note_type = "general"

    if priority not in VALID_REVIEW_PRIORITIES:
        priority = "normal"

    if followup_status not in VALID_FOLLOWUP_STATUSES:
        followup_status = "open"

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO intake_review_notes (
            intake_id, firm_id, note_type, priority, followup_status,
            note_body, created_at, updated_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        note_type,
        priority,
        followup_status,
        note_body,
        now,
        now,
        created_by,
    ))

    cur.execute("""
        UPDATE intake_sessions
        SET updated_at = ?
        WHERE intake_id = ?
    """, (now, intake_id))

    conn.commit()
    conn.close()

    return {
        "intake_id": intake_id,
        "note_type": note_type,
        "priority": priority,
        "followup_status": followup_status,
        "note_body": note_body,
        "created_at": now,
        "created_by": created_by,
    }


def list_intake_review_notes(intake_id):
    ensure_intake_review_note_tables()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, intake_id, note_type, priority, followup_status,
               note_body, created_at, updated_at, created_by
        FROM intake_review_notes
        WHERE intake_id = ?
        ORDER BY id DESC
    """, (intake_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "intake_id": row[1],
            "note_type": row[2],
            "note_type_label": VALID_REVIEW_NOTE_TYPES.get(row[2], row[2]),
            "priority": row[3],
            "priority_label": VALID_REVIEW_PRIORITIES.get(row[3], row[3]),
            "followup_status": row[4],
            "followup_status_label": VALID_FOLLOWUP_STATUSES.get(row[4], row[4]),
            "note_body": row[5],
            "created_at": format_intake_timestamp(row[6]),
            "updated_at": format_intake_timestamp(row[7]),
            "created_by": row[8] or "—",
        }
        for row in rows
    ]


def get_intake_review_note_counts():
    ensure_intake_review_note_tables()
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT intake_id, COUNT(*) AS note_count
        FROM intake_review_notes
        WHERE firm_id = ?
        GROUP BY intake_id
    """, (firm_id,))

    rows = cur.fetchall()
    conn.close()

    return {row[0]: row[1] for row in rows}


def list_intake_dashboard_with_review_notes(limit=100, status_filter="all"):
    items = list_intake_dashboard_polished(limit=limit, status_filter=status_filter)
    counts = get_intake_review_note_counts()

    for item in items:
        count = counts.get(item["intake_id"], 0)
        item["review_note_count"] = count
        item["has_review_notes"] = count > 0

    return items


def get_review_note_form_options():
    return {
        "note_types": VALID_REVIEW_NOTE_TYPES,
        "priorities": VALID_REVIEW_PRIORITIES,
        "followup_statuses": VALID_FOLLOWUP_STATUSES,
    }


# -------------------------------------------------------------------
# INT-1I — Intake Follow-Up Task Builder
# -------------------------------------------------------------------

VALID_FOLLOWUP_TASK_TYPES = {
    "document": "Document Request",
    "client_followup": "Client Follow-Up",
    "professional_review": "Professional Review",
    "staff_action": "Staff Action",
    "next_session": "Next Session Prep",
}

VALID_FOLLOWUP_TASK_PRIORITIES = {
    "low": "Low",
    "normal": "Normal",
    "high": "High",
    "urgent": "Urgent",
}

VALID_FOLLOWUP_TASK_STATUSES = {
    "open": "Open",
    "pending_client": "Pending Client",
    "pending_staff": "Pending Staff",
    "pending_professional": "Pending Professional Review",
    "completed": "Completed",
    "deferred": "Deferred",
}


def ensure_intake_followup_task_tables():
    ensure_intake_review_note_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_followup_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            task_type TEXT DEFAULT 'staff_action',
            priority TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'open',
            title TEXT NOT NULL,
            description TEXT,
            source TEXT DEFAULT 'manual',
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT,
            completed_at TEXT,
            completed_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_intake_followup_task(
    intake_id,
    title,
    description="",
    task_type="staff_action",
    priority="normal",
    status="open",
    source="manual",
    created_by=None
):
    ensure_intake_followup_task_tables()

    title = (title or "").strip()
    description = (description or "").strip()

    if not title:
        raise ValueError("Task title cannot be blank.")

    if task_type not in VALID_FOLLOWUP_TASK_TYPES:
        task_type = "staff_action"

    if priority not in VALID_FOLLOWUP_TASK_PRIORITIES:
        priority = "normal"

    if status not in VALID_FOLLOWUP_TASK_STATUSES:
        status = "open"

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO intake_followup_tasks (
            intake_id, firm_id, task_type, priority, status, title,
            description, source, created_at, updated_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        task_type,
        priority,
        status,
        title,
        description,
        source,
        now,
        now,
        created_by,
    ))

    cur.execute("""
        UPDATE intake_sessions
        SET updated_at = ?
        WHERE intake_id = ?
    """, (now, intake_id))

    conn.commit()
    conn.close()

    return {
        "intake_id": intake_id,
        "task_type": task_type,
        "priority": priority,
        "status": status,
        "title": title,
        "description": description,
        "source": source,
        "created_at": now,
        "created_by": created_by,
    }


def list_intake_followup_tasks(intake_id):
    ensure_intake_followup_task_tables()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, intake_id, task_type, priority, status, title,
               description, source, created_at, updated_at, created_by,
               completed_at, completed_by
        FROM intake_followup_tasks
        WHERE intake_id = ?
        ORDER BY
            CASE status
                WHEN 'open' THEN 1
                WHEN 'pending_client' THEN 2
                WHEN 'pending_staff' THEN 3
                WHEN 'pending_professional' THEN 4
                WHEN 'deferred' THEN 5
                WHEN 'completed' THEN 6
                ELSE 7
            END,
            CASE priority
                WHEN 'urgent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END,
            id ASC
    """, (intake_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "intake_id": row[1],
            "task_type": row[2],
            "task_type_label": VALID_FOLLOWUP_TASK_TYPES.get(row[2], row[2]),
            "priority": row[3],
            "priority_label": VALID_FOLLOWUP_TASK_PRIORITIES.get(row[3], row[3]),
            "status": row[4],
            "status_label": VALID_FOLLOWUP_TASK_STATUSES.get(row[4], row[4]),
            "title": row[5],
            "description": row[6],
            "source": row[7],
            "created_at": format_intake_timestamp(row[8]),
            "updated_at": format_intake_timestamp(row[9]),
            "created_by": row[10] or "—",
            "completed_at": format_intake_timestamp(row[11]) if row[11] else "",
            "completed_by": row[12] or "",
        }
        for row in rows
    ]


def get_intake_followup_task_counts():
    ensure_intake_followup_task_tables()
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT intake_id,
               COUNT(*) AS total_count,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
               SUM(CASE WHEN status != 'completed' THEN 1 ELSE 0 END) AS open_count
        FROM intake_followup_tasks
        WHERE firm_id = ?
        GROUP BY intake_id
    """, (firm_id,))

    rows = cur.fetchall()
    conn.close()

    output = {}
    for row in rows:
        output[row[0]] = {
            "task_count": row[1] or 0,
            "completed_task_count": row[2] or 0,
            "open_task_count": row[3] or 0,
        }
    return output


def task_exists(intake_id, title, task_type=None, source=None):
    ensure_intake_followup_task_tables()

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT COUNT(*)
        FROM intake_followup_tasks
        WHERE intake_id = ? AND title = ?
    """
    params = [intake_id, title]

    if task_type:
        query += " AND task_type = ?"
        params.append(task_type)

    if source:
        query += " AND source = ?"
        params.append(source)

    cur.execute(query, tuple(params))
    row = cur.fetchone()
    conn.close()

    return bool(row and row[0])


def auto_generate_followup_tasks_from_snapshot(intake_id, snapshot, created_by=None):
    """
    Idempotently generates follow-up tasks from the client snapshot.
    It will not duplicate the same generated task title/source pair.
    """
    ensure_intake_followup_task_tables()

    created = []

    # Document requests become client-facing document tasks.
    for doc in snapshot.get("documents_to_gather", []) or []:
        title = f"Gather document: {doc}"
        if not task_exists(intake_id, title, task_type="document", source="auto_snapshot"):
            created.append(create_intake_followup_task(
                intake_id=intake_id,
                title=title,
                description="Client or staff should gather this item before the deeper review session.",
                task_type="document",
                priority="normal",
                status="pending_client",
                source="auto_snapshot",
                created_by=created_by,
            ))

    # Review flags become review tasks.
    for flag in snapshot.get("review_flags", []) or []:
        title = f"Review flag: {flag}"
        priority = "high" if "tax" in flag.lower() or "legal" in flag.lower() or "liability" in flag.lower() else "normal"
        status = "pending_professional" if "tax" in flag.lower() or "legal" in flag.lower() else "pending_staff"

        if not task_exists(intake_id, title, source="auto_snapshot"):
            created.append(create_intake_followup_task(
                intake_id=intake_id,
                title=title,
                description="This item was flagged by the intake translation/scoring engine and should be reviewed before final action.",
                task_type="professional_review" if status == "pending_professional" else "staff_action",
                priority=priority,
                status=status,
                source="auto_snapshot",
                created_by=created_by,
            ))

    # Recommended next session becomes a next-session prep task.
    next_session = snapshot.get("recommended_next_session")
    if next_session:
        title = f"Prepare next session: {next_session}"
        if not task_exists(intake_id, title, task_type="next_session", source="auto_snapshot"):
            created.append(create_intake_followup_task(
                intake_id=intake_id,
                title=title,
                description="Prepare agenda, documents, and follow-up questions for the recommended next review session.",
                task_type="next_session",
                priority="high" if snapshot.get("review_priority") in ["High", "Elevated"] else "normal",
                status="pending_staff",
                source="auto_snapshot",
                created_by=created_by,
            ))

    return created


def update_intake_followup_task_status(task_id, status, updated_by=None):
    ensure_intake_followup_task_tables()

    if status not in VALID_FOLLOWUP_TASK_STATUSES:
        raise ValueError("Invalid task status.")

    now = datetime.utcnow().isoformat(timespec="seconds")
    completed_at = now if status == "completed" else None
    completed_by = updated_by if status == "completed" else None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE intake_followup_tasks
        SET status = ?,
            updated_at = ?,
            completed_at = ?,
            completed_by = ?
        WHERE id = ?
    """, (
        status,
        now,
        completed_at,
        completed_by,
        task_id,
    ))

    conn.commit()
    conn.close()


def get_followup_task_form_options():
    return {
        "task_types": VALID_FOLLOWUP_TASK_TYPES,
        "priorities": VALID_FOLLOWUP_TASK_PRIORITIES,
        "statuses": VALID_FOLLOWUP_TASK_STATUSES,
    }


def list_intake_dashboard_with_tasks(limit=100, status_filter="all"):
    items = list_intake_dashboard_with_review_notes(limit=limit, status_filter=status_filter)
    counts = get_intake_followup_task_counts()

    for item in items:
        data = counts.get(item["intake_id"], {})
        item["task_count"] = data.get("task_count", 0)
        item["open_task_count"] = data.get("open_task_count", 0)
        item["completed_task_count"] = data.get("completed_task_count", 0)
        item["has_tasks"] = item["task_count"] > 0

    return items


# -------------------------------------------------------------------
# INT-1J — Intake Task Filters + Follow-Up Workflow Polish
# -------------------------------------------------------------------

def summarize_followup_tasks(tasks):
    summary = {
        "total": len(tasks or []),
        "open": 0,
        "pending_client": 0,
        "pending_staff": 0,
        "pending_professional": 0,
        "completed": 0,
        "deferred": 0,
    }

    for task in tasks or []:
        status = task.get("status")
        if status in summary:
            summary[status] += 1

        if status != "completed":
            summary["open"] += 1

    return summary


def group_followup_tasks(tasks):
    groups = {
        "pending_client": [],
        "pending_staff": [],
        "pending_professional": [],
        "open": [],
        "deferred": [],
        "completed": [],
    }

    for task in tasks or []:
        status = task.get("status") or "open"
        if status in groups:
            groups[status].append(task)
        else:
            groups["open"].append(task)

    return groups


# -------------------------------------------------------------------
# INT-1K — Intake Follow-Up Packet / Checklist Export Prep
# -------------------------------------------------------------------

def build_intake_followup_packet(intake_id):
    snapshot, result = get_saved_client_snapshot(intake_id)
    if not snapshot:
        return None

    tasks = list_intake_followup_tasks(intake_id)
    notes = list_intake_review_notes(intake_id)
    task_summary = summarize_followup_tasks(tasks)
    task_groups = group_followup_tasks(tasks)

    documents = snapshot.get("documents_to_gather", []) or []
    priorities = snapshot.get("top_priorities", []) or []
    review_flags = snapshot.get("review_flags", []) or []

    packet = {
        "intake_id": intake_id,
        "snapshot": snapshot,
        "result": result,
        "documents": documents,
        "priorities": priorities,
        "review_flags": review_flags,
        "recommended_next_session": snapshot.get("recommended_next_session"),
        "tasks": tasks,
        "task_summary": task_summary,
        "task_groups": task_groups,
        "notes": notes,
        "packet_status": "Prepared",
        "packet_type": "Initial Follow-Up Packet",
        "export_ready": True,
    }

    return packet


def get_packet_readiness_label(packet):
    if not packet:
        return "Not Available"

    task_summary = packet.get("task_summary", {}) or {}
    open_count = task_summary.get("open", 0)
    documents = packet.get("documents", []) or []

    if open_count == 0 and documents:
        return "Ready for Review"
    if open_count > 0:
        return "Action Items Open"
    return "Prepared"


# -------------------------------------------------------------------
# INT-1L — Follow-Up Packet PDF/DOCX Export
# -------------------------------------------------------------------

def ensure_intake_export_dir():
    from pathlib import Path

    export_dir = Path("exports/intake_packets")
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def safe_export_filename(value):
    value = str(value or "intake").strip()
    keep = []
    for ch in value:
        if ch.isalnum() or ch in ["-", "_"]:
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def generate_followup_packet_docx(intake_id):
    from pathlib import Path
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    packet = build_intake_followup_packet(intake_id)
    if not packet:
        return None

    export_dir = ensure_intake_export_dir()
    filename = f"{safe_export_filename(intake_id)}_Follow_Up_Packet.docx"
    out_path = export_dir / filename

    doc = Document()

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Initial Intake Follow-Up Packet")
    run.bold = True
    run.font.size = Pt(16)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run(f"Intake ID: {packet['intake_id']} | Packet Status: {packet['packet_status']}")

    doc.add_paragraph("")

    def add_heading(text):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(13)
        return p

    def add_bullet(text):
        p = doc.add_paragraph(style=None)
        p.style = doc.styles["Normal"]
        p.paragraph_format.left_indent = Pt(18)
        p.add_run(f"- {text}")

    add_heading("Snapshot Summary")
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"

    rows = [
        ("Planning Type", " + ".join(packet["snapshot"].get("planning_types", [])) or "Initial Planning"),
        ("Complexity", packet["snapshot"].get("complexity_level", "")),
        ("Priority", packet["snapshot"].get("review_priority", "")),
        ("Readiness", packet["snapshot"].get("readiness_level", "")),
        ("Recommended Next Session", packet.get("recommended_next_session") or "Initial structure review"),
    ]

    for label, value in rows:
        cells = table.add_row().cells
        cells[0].text = label
        cells[1].text = str(value)

    doc.add_paragraph("")

    add_heading("Top Priorities")
    for idx, item in enumerate(packet.get("priorities", []) or [], start=1):
        add_bullet(f"{idx}. {item}")
    if not packet.get("priorities"):
        add_bullet("No priorities generated.")

    add_heading("Document Checklist")
    for item in packet.get("documents", []) or []:
        add_bullet(f"[ ] {item}")
    if not packet.get("documents"):
        add_bullet("No document checklist generated.")

    if packet.get("review_flags"):
        add_heading("Review Flags")
        for item in packet.get("review_flags", []):
            add_bullet(item)

    add_heading("Follow-Up Task Summary")
    task_summary = packet.get("task_summary", {}) or {}
    summary_rows = [
        ("Total", task_summary.get("total", 0)),
        ("Open", task_summary.get("open", 0)),
        ("Pending Client", task_summary.get("pending_client", 0)),
        ("Pending Staff", task_summary.get("pending_staff", 0)),
        ("Pending Professional", task_summary.get("pending_professional", 0)),
        ("Completed", task_summary.get("completed", 0)),
    ]

    task_table = doc.add_table(rows=0, cols=2)
    task_table.style = "Table Grid"

    for label, value in summary_rows:
        cells = task_table.add_row().cells
        cells[0].text = label
        cells[1].text = str(value)

    doc.add_paragraph("")

    add_heading("Follow-Up Task Checklist")
    for task in packet.get("tasks", []) or []:
        check = "[x]" if task.get("status") == "completed" else "[ ]"
        add_bullet(f"{check} {task.get('title')}")
        meta = f"{task.get('task_type_label')} | Priority: {task.get('priority_label')} | Status: {task.get('status_label')} | Source: {task.get('source')}"
        add_bullet(f"    {meta}")
        if task.get("description"):
            add_bullet(f"    {task.get('description')}")

    if not packet.get("tasks"):
        add_bullet("No follow-up tasks generated.")

    add_heading("Internal Review Notes")
    for note in packet.get("notes", []) or []:
        meta = f"{note.get('note_type_label')} | Priority: {note.get('priority_label')} | Status: {note.get('followup_status_label')} | By: {note.get('created_by')} | {note.get('created_at')}"
        add_bullet(meta)
        add_bullet(f"    {note.get('note_body')}")
    if not packet.get("notes"):
        add_bullet("No internal review notes added.")

    add_heading("Important Notice")
    doc.add_paragraph(
        "This follow-up packet is an intake preparation tool. It does not finalize legal, tax, fiduciary, "
        "or asset-transfer decisions. Additional review may be needed before documents are signed, assets are "
        "transferred, or formal action is taken."
    )

    doc.save(out_path)
    return str(out_path)


def generate_followup_packet_pdf(intake_id):
    """
    Generate a PDF version of the follow-up packet.

    Windows-safe fallback order:
    1. Generate DOCX.
    2. Try LibreOffice/soffice if installed.
    3. Try Microsoft Word COM automation if pywin32 + Word are available.
    4. Return None if unavailable so the route can fail gracefully.
    """
    import os
    import shutil
    import subprocess
    from pathlib import Path

    docx_path = generate_followup_packet_docx(intake_id)
    if not docx_path:
        return None

    docx_path = Path(docx_path).resolve()
    export_dir = docx_path.parent
    pdf_path = export_dir / f"{docx_path.stem}.pdf"

    try:
        if pdf_path.exists():
            pdf_path.unlink()
    except Exception:
        pass

    soffice_candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for soffice in soffice_candidates:
        if not soffice:
            continue

        try:
            soffice_path = Path(soffice)
            if not soffice_path.exists() and not shutil.which(str(soffice)):
                continue

            cmd = [
                str(soffice),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(export_dir),
                str(docx_path),
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if pdf_path.exists():
                return str(pdf_path)

        except Exception:
            continue

    if os.name == "nt":
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0

            try:
                doc = word.Documents.Open(str(docx_path))
                doc.ExportAsFixedFormat(str(pdf_path), 17)
                doc.Close(False)
            finally:
                word.Quit()
                pythoncom.CoUninitialize()

            if pdf_path.exists():
                return str(pdf_path)

        except Exception:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            return None

    return None


# -------------------------------------------------------------------
# INT-1M — Export Folder Gitignore + Export Audit Record
# -------------------------------------------------------------------

def ensure_intake_export_log_tables():
    ensure_intake_snapshot_tables()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_export_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            export_type TEXT,
            export_status TEXT,
            file_path TEXT,
            message TEXT,
            created_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def log_intake_export(intake_id, export_type, export_status, file_path=None, message=None, created_by=None):
    ensure_intake_export_log_tables()

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO intake_export_logs (
            intake_id, firm_id, export_type, export_status,
            file_path, message, created_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        export_type,
        export_status,
        file_path,
        message,
        now,
        created_by,
    ))

    conn.commit()
    conn.close()

    return {
        "intake_id": intake_id,
        "export_type": export_type,
        "export_status": export_status,
        "file_path": file_path,
        "message": message,
        "created_at": now,
        "created_by": created_by,
    }


def list_intake_export_logs(intake_id):
    ensure_intake_export_log_tables()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT export_type, export_status, file_path, message, created_at, created_by
        FROM intake_export_logs
        WHERE intake_id = ?
        ORDER BY id DESC
        LIMIT 25
    """, (intake_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "export_type": row[0],
            "export_status": row[1],
            "file_path": row[2],
            "message": row[3],
            "created_at": format_intake_timestamp(row[4]),
            "created_by": row[5] or "—",
        }
        for row in rows
    ]


def generate_followup_packet_docx_logged(intake_id, created_by=None):
    try:
        path = generate_followup_packet_docx(intake_id)
        if path:
            log_intake_export(
                intake_id=intake_id,
                export_type="docx",
                export_status="success",
                file_path=path,
                message="DOCX follow-up packet generated successfully.",
                created_by=created_by,
            )
            return path

        log_intake_export(
            intake_id=intake_id,
            export_type="docx",
            export_status="failed",
            file_path=None,
            message="DOCX follow-up packet could not be generated.",
            created_by=created_by,
        )
        return None

    except Exception as exc:
        log_intake_export(
            intake_id=intake_id,
            export_type="docx",
            export_status="error",
            file_path=None,
            message=str(exc),
            created_by=created_by,
        )
        return None


def generate_followup_packet_pdf_logged(intake_id, created_by=None):
    try:
        path = generate_followup_packet_pdf(intake_id)
        if path:
            log_intake_export(
                intake_id=intake_id,
                export_type="pdf",
                export_status="success",
                file_path=path,
                message="PDF follow-up packet generated successfully.",
                created_by=created_by,
            )
            return path

        log_intake_export(
            intake_id=intake_id,
            export_type="pdf",
            export_status="failed",
            file_path=None,
            message="Automatic PDF generation unavailable. Use Print packet → Save as PDF or install LibreOffice / pywin32 + Word.",
            created_by=created_by,
        )
        return None

    except Exception as exc:
        log_intake_export(
            intake_id=intake_id,
            export_type="pdf",
            export_status="error",
            file_path=None,
            message=str(exc),
            created_by=created_by,
        )
        return None


# -------------------------------------------------------------------
# INT-1N — Intake Export History Dashboard + Packet Versioning
# -------------------------------------------------------------------

def ensure_intake_export_version_columns():
    ensure_intake_export_log_tables()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(intake_export_logs)")
    columns = {row[1] for row in cur.fetchall()}

    if "version_number" not in columns:
        cur.execute("ALTER TABLE intake_export_logs ADD COLUMN version_number INTEGER DEFAULT 1")

    if "packet_type" not in columns:
        cur.execute("ALTER TABLE intake_export_logs ADD COLUMN packet_type TEXT DEFAULT 'follow_up_packet'")

    conn.commit()
    conn.close()


def get_next_export_version(intake_id, export_type, packet_type="follow_up_packet"):
    ensure_intake_export_version_columns()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(MAX(version_number), 0)
        FROM intake_export_logs
        WHERE intake_id = ?
          AND export_type = ?
          AND packet_type = ?
          AND export_status IN ('success', 'failed', 'error')
    """, (intake_id, export_type, packet_type))

    row = cur.fetchone()
    conn.close()

    current = row[0] if row and row[0] is not None else 0
    return int(current) + 1


def log_intake_export_versioned(
    intake_id,
    export_type,
    export_status,
    file_path=None,
    message=None,
    created_by=None,
    packet_type="follow_up_packet",
    version_number=None
):
    ensure_intake_export_version_columns()

    if version_number is None:
        version_number = get_next_export_version(intake_id, export_type, packet_type)

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO intake_export_logs (
            intake_id, firm_id, export_type, export_status,
            file_path, message, created_at, created_by,
            version_number, packet_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        export_type,
        export_status,
        file_path,
        message,
        now,
        created_by,
        version_number,
        packet_type,
    ))

    conn.commit()
    conn.close()

    return {
        "intake_id": intake_id,
        "export_type": export_type,
        "export_status": export_status,
        "file_path": file_path,
        "message": message,
        "created_at": now,
        "created_by": created_by,
        "version_number": version_number,
        "packet_type": packet_type,
    }


def list_all_intake_export_logs(limit=100):
    ensure_intake_export_version_columns()
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT intake_id, export_type, export_status, file_path, message,
               created_at, created_by, version_number, packet_type
        FROM intake_export_logs
        WHERE firm_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (firm_id, limit))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "intake_id": row[0],
            "export_type": row[1],
            "export_status": row[2],
            "file_path": row[3],
            "message": row[4],
            "created_at": format_intake_timestamp(row[5]),
            "created_by": row[6] or "—",
            "version_number": row[7] or 1,
            "packet_type": row[8] or "follow_up_packet",
        }
        for row in rows
    ]


def list_intake_export_logs_versioned(intake_id):
    ensure_intake_export_version_columns()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT export_type, export_status, file_path, message,
               created_at, created_by, version_number, packet_type
        FROM intake_export_logs
        WHERE intake_id = ?
        ORDER BY id DESC
        LIMIT 100
    """, (intake_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "intake_id": intake_id,
            "export_type": row[0],
            "export_status": row[1],
            "file_path": row[2],
            "message": row[3],
            "created_at": format_intake_timestamp(row[4]),
            "created_by": row[5] or "—",
            "version_number": row[6] or 1,
            "packet_type": row[7] or "follow_up_packet",
        }
        for row in rows
    ]


def get_intake_export_summary(limit=100):
    logs = list_all_intake_export_logs(limit=limit)

    summary = {
        "total": len(logs),
        "success": 0,
        "failed": 0,
        "error": 0,
        "docx": 0,
        "pdf": 0,
        "other": 0,
    }

    for log in logs:
        status = log.get("export_status")
        export_type = log.get("export_type")

        if status in summary:
            summary[status] += 1

        if export_type == "docx":
            summary["docx"] += 1
        elif export_type == "pdf":
            summary["pdf"] += 1
        else:
            summary["other"] += 1

    return summary


def generate_followup_packet_docx_logged_versioned(intake_id, created_by=None):
    version = get_next_export_version(intake_id, "docx", "follow_up_packet")

    try:
        path = generate_followup_packet_docx(intake_id)
        if path:
            log_intake_export_versioned(
                intake_id=intake_id,
                export_type="docx",
                export_status="success",
                file_path=path,
                message=f"DOCX follow-up packet generated successfully. Version {version}.",
                created_by=created_by,
                packet_type="follow_up_packet",
                version_number=version,
            )
            return path

        log_intake_export_versioned(
            intake_id=intake_id,
            export_type="docx",
            export_status="failed",
            file_path=None,
            message=f"DOCX follow-up packet could not be generated. Version {version}.",
            created_by=created_by,
            packet_type="follow_up_packet",
            version_number=version,
        )
        return None

    except Exception as exc:
        log_intake_export_versioned(
            intake_id=intake_id,
            export_type="docx",
            export_status="error",
            file_path=None,
            message=f"{exc} Version {version}.",
            created_by=created_by,
            packet_type="follow_up_packet",
            version_number=version,
        )
        return None


def generate_followup_packet_pdf_logged_versioned(intake_id, created_by=None):
    version = get_next_export_version(intake_id, "pdf", "follow_up_packet")

    try:
        path = generate_followup_packet_pdf(intake_id)
        if path:
            log_intake_export_versioned(
                intake_id=intake_id,
                export_type="pdf",
                export_status="success",
                file_path=path,
                message=f"PDF follow-up packet generated successfully. Version {version}.",
                created_by=created_by,
                packet_type="follow_up_packet",
                version_number=version,
            )
            return path

        log_intake_export_versioned(
            intake_id=intake_id,
            export_type="pdf",
            export_status="failed",
            file_path=None,
            message=f"Automatic PDF generation unavailable. Use Print packet → Save as PDF or install LibreOffice / pywin32 + Word. Version {version}.",
            created_by=created_by,
            packet_type="follow_up_packet",
            version_number=version,
        )
        return None

    except Exception as exc:
        log_intake_export_versioned(
            intake_id=intake_id,
            export_type="pdf",
            export_status="error",
            file_path=None,
            message=f"{exc} Version {version}.",
            created_by=created_by,
            packet_type="follow_up_packet",
            version_number=version,
        )
        return None

