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

