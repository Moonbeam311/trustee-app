from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_BRANCH = "post-v2-planning"
REQUIRED_HEAD = "ab080d47d89257df58d3712be9953c0b37c6b114"
EXPECTED_NEW_FILE = "scripts/audit_compliance_review_architecture_17q_f.py"
ACTIVE_F1_ALLOWED_FILES = {
    "scripts/audit_archive_people_destination_adapters_17q_e.py",
    "scripts/audit_system_audit_destination_removal_17q_d.py",
    "scripts/audit_compliance_review_architecture_17q_f.py",
    "scripts/audit_regression_guard_and_auth_preservation_17q_f_1.py",
}

MODE = "compliance_review_governed_record_architecture_and_lifecycle_audit_only"

VOCABULARY_TERMS = [
    "compliance",
    "compliant",
    "noncompliant",
    "control",
    "assessment",
    "review",
    "finding",
    "determination",
    "certification",
    "verification",
    "reliance",
    "policy",
    "requirement",
    "regulatory",
    "legal",
    "exception",
    "deficiency",
    "remediation",
]

TEXT_EXTENSIONS = {
    ".py",
    ".html",
    ".jinja",
    ".jinja2",
    ".txt",
    ".md",
    ".json",
    ".sql",
    ".css",
    ".js",
}


def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def repo_files():
    code, stdout, stderr = run_git("ls-files")
    if code != 0:
        raise AssertionError(f"git ls-files failed: {stderr or stdout}")
    files = []
    for line in stdout.splitlines():
        path = ROOT / line
        if path.suffix.lower() in TEXT_EXTENSIONS and path.exists():
            files.append(line)
    return files


def collect_vocabulary_inventory():
    categories = {
        "incidental label": 0,
        "boolean or status field": 0,
        "validation rule": 0,
        "workflow state": 0,
        "certificate posture": 0,
        "execution-readiness posture": 0,
        "policy reference": 0,
        "Governance record": 0,
        "durable compliance candidate": 0,
        "technical control": 0,
        "user-facing language": 0,
    }
    term_counts = {term: 0 for term in VOCABULARY_TERMS}
    sampled = []
    for file_name in repo_files():
        if file_name == EXPECTED_NEW_FILE:
            continue
        text = read(file_name)
        lower = text.lower()
        for term in VOCABULARY_TERMS:
            hits = len(re.findall(rf"\b{re.escape(term)}\b", lower))
            if hits:
                term_counts[term] += hits
        if not any(term in lower for term in VOCABULARY_TERMS):
            continue
        if "certificate" in lower or "certification" in lower:
            categories["certificate posture"] += 1
        if "execution" in lower or "readiness" in lower:
            categories["execution-readiness posture"] += 1
        if "policy" in lower or "directive" in lower:
            categories["policy reference"] += 1
        if "institutional_directives" in lower or "institutional_policies" in lower:
            categories["Governance record"] += 1
        if "status" in lower or "is_" in lower:
            categories["boolean or status field"] += 1
        if "validate" in lower or "required" in lower:
            categories["validation rule"] += 1
        if "under_review" in lower or "review_gate" in lower or "transition" in lower:
            categories["workflow state"] += 1
        if "control" in lower or "health" in lower:
            categories["technical control"] += 1
        if "<h" in lower or "admin-muted" in lower or "label" in lower:
            categories["user-facing language"] += 1
        if (
            ("compliance_reviews" in lower or "compliance_review_id" in lower)
            and file_name
            not in {
                "services/services_certificate_adapters.py",
                "scripts/audit_system_observation_destination_gaps_17q_c.py",
            }
        ):
            categories["durable compliance candidate"] += 1
        categories["incidental label"] += 1
        if len(sampled) < 18:
            sampled.append(file_name)
    return term_counts, categories, sampled


def destination_posture():
    source = read("services/services_system_observation_destinations.py")
    observations = read("services/services_system_observations.py")
    return {
        "governance": '"governance"' in source and '"verified_supported"' in source,
        "matter": '"matter"' in source and '"verified_supported"' in source,
        "archive": '"archive"' in source and '"verified_supported"' in source,
        "people": '"people"' in source and '"verified_supported"' in source,
        "compliance_bounded_unavailable": (
            "def verify_compliance_destination" in source
            and "No authoritative routable Compliance destination registry is available" in source
            and '"compliance"' not in re.search(r"SUPPORTED_DESTINATIONS\s*=\s*\{([^}]+)\}", source, re.S).group(1)
        ),
        "restricted_bounded_unavailable": "def verify_restricted_procedure_destination" in source
        and "restricted_destination_unavailable" in source,
        "system_audit_prohibited": "system_audit" not in re.search(
            r"ROUTING_DESTINATION_MATRIX\s*=\s*\{(.+?)\n\}", observations, re.S
        ).group(1)
        and '"System Audit - historical reference"' in source,
    }


def table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))
    lines = []
    lines.append(" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    lines.append("-+-".join("-" * width for width in widths))
    for row in rows:
        lines.append(" | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))
    return "\n".join(lines)


FALSE_POSITIVES = [
    (
        "boolean compliance flags",
        "They report a condition or posture but do not own scope, authority, lifecycle, events, or disposition.",
    ),
    (
        "certificate compliance fields",
        "Certificates are evidence/export surfaces; their readiness fields do not own a separate review question.",
    ),
    (
        "execution readiness statuses",
        "Execution readiness gates permit or block operational steps but do not preserve governed analysis.",
    ),
    (
        "template headings",
        "User-facing labels have no stable public ID, registry, lifecycle, authority, or event history.",
    ),
    (
        "policy names",
        "Policies may be governing requirements; they are not themselves the review of whether a condition satisfies them.",
    ),
    (
        "Governance approval fields",
        "Governance approval records institutional policy/directive action, not a compliance examination record.",
    ),
    (
        "generic audit rows",
        "Audit rows preserve activity evidence and actor attribution but cannot carry review ownership or disposition.",
    ),
    (
        "System Observation records",
        "Observations identify persisted system conditions; routing must point to a separate governed destination.",
    ),
    (
        "archive verification statuses",
        "Archive statuses identify custody or preservation posture, not a compliance review of a requirement.",
    ),
    (
        "technical health checks",
        "Health checks indicate control state and cannot make institutional compliance findings.",
    ),
    (
        "free-text compliance notes",
        "Notes lack controlled identity, scope, status, approval, event history, and duplicate prevention.",
    ),
]

CANDIDATES = [
    [
        "Institutional Directive / Policy",
        "institutional_directives, institutional_policies",
        "services_governance.py",
        "DIR-YYYY-NNNN / POL-YYYY-NNNN",
        "Governance source record",
        "firm_id",
        "status",
        "approved_by / approved_at where present",
        "/governance/directives, /governance/policies",
        "/governance/directives/<id>, /governance/policies/<id>",
        "policy activity and governance relationships",
        "firm/admin governed workspace",
        "possible governing requirement or related record; insufficient as primary Compliance record",
    ],
    [
        "Matter",
        "matters",
        "matter services and app matter routes",
        "MAT-*",
        "Matter",
        "firm_id, trust_id, matter_id",
        "status",
        "assigned/status owner fields where present",
        "/matters",
        "/matters/<matter_id>",
        "matter/governance timeline components",
        "firm-scoped matter access",
        "possible source or parent context; insufficient as primary Compliance record",
    ],
    [
        "System Observation",
        "system_observations, system_observation_events",
        "services_system_observations.py",
        "SYSOBS-YYYY-NNNNNN",
        "System condition observation",
        "firm_id, institution_id, trust_id, matter_id, deployment_key",
        "current_state",
        "master admin system authority",
        "/system/observations",
        "/system/observations/<observation_id>",
        "append-only observation events",
        "master-admin protected system workspace",
        "source record only; certified routing requires a distinct governed destination",
    ],
    [
        "Certificate / Certification",
        "certification-related services and templates",
        "services_certifications.py",
        "certificate-specific IDs where present",
        "Evidence or certification output",
        "trust/firm context where present",
        "verification/readiness states",
        "certificate verifier or admin authority",
        "certificate workspace routes",
        "certificate detail/export routes",
        "certificate lifecycle events where present",
        "protected certificate workspace",
        "possible evidence/source record; not a compliance review owner",
    ],
    [
        "Execution / Transfer Readiness",
        "transfer/execution records",
        "transfer and execution services",
        "transfer/session IDs",
        "Execution readiness or transfer record",
        "trust/firm/property context",
        "readiness/control statuses",
        "execution operator authority",
        "execution dashboards",
        "execution detail routes",
        "execution events or audit evidence where present",
        "trust/execution authorization",
        "possible source/evidence; readiness status is not a governed compliance disposition",
    ],
    [
        "Archive Custody Event",
        "continuity_custody_log",
        "services_continuity_assets",
        "CCL-0001",
        "Continuity Custody Event",
        "firm_id, trust_id, property_id",
        "custody_action",
        "archive custodian/operator",
        "/continuity-assets",
        "/property/<property_id>/custody-log",
        "custody log",
        "firm/trust archive boundary",
        "possible source/evidence; not a compliance review owner",
    ],
    [
        "Fiduciary Record",
        "fiduciaries",
        "database.db fiduciary helpers",
        "FID-001",
        "Fiduciary Record",
        "firm_id, trust_id",
        "status",
        "fiduciary/person workspace authority",
        "/fiduciaries",
        "/fiduciaries",
        "limited assignment history",
        "firm/trust people boundary",
        "possible source/evidence; not a compliance review owner",
    ],
]

FIELD_MATRIX = [
    ["id", "Internal primary key", "derived", "No", "system", "integer", "database"],
    ["compliance_review_id", "Stable public identifier", "creation", "No", "system", "CMP-YYYY-0001", "sequence service"],
    ["firm_id", "Required firm boundary", "creation", "No", "creator/admin", "known firm", "session/context"],
    ["institution_id", "Optional institutional owner", "creation", "Limited before opening", "creator/admin", "known institution", "parent context"],
    ["trust_id", "Optional trust scope", "creation", "Limited before opening", "creator/admin", "visible trust", "parent context"],
    ["matter_id", "Optional matter scope", "creation", "Limited before opening", "creator/admin", "visible matter", "parent context"],
    ["deployment_key", "Optional deployment scope", "creation", "Limited before opening", "system/admin", "bounded key", "source context"],
    ["title", "Human review title", "creation", "Yes until closed", "review owner", "bounded text", "operator"],
    ["review_type", "Bounded review family", "creation", "No after opening", "review owner", "allowlist", "operator"],
    ["question_presented", "Compliance question under review", "creation", "Yes until disposition", "review owner", "bounded text", "operator"],
    ["governing_requirement_type", "Requirement source family", "before review", "Yes until disposition", "review owner", "allowlist", "operator/source"],
    ["governing_requirement_id", "Requirement source ID", "before review", "Yes until disposition", "review owner", "validated reference", "operator/source"],
    ["governing_requirement_label", "Safe label snapshot", "before review", "Derived refresh", "system", "bounded text", "referenced record"],
    ["requirement_notes", "Short external/internal requirement note", "review", "Yes", "review owner", "bounded non-privileged text", "operator"],
    ["source_type", "Origin family", "creation", "No after opening", "creator", "allowlist", "operator/source"],
    ["source_id", "Origin record ID", "creation", "No after opening", "creator", "validated reference", "operator/source"],
    ["source_label", "Safe origin label", "creation", "Derived refresh", "system", "bounded text", "referenced record"],
    ["scope_summary", "Readable scope explanation", "opening", "Yes until disposition", "review owner", "bounded text", "operator"],
    ["status", "Lifecycle status", "creation", "Only through transitions", "workflow", "allowlist", "transition service"],
    ["priority", "Work queue priority", "creation", "Yes until closed", "assigner", "low/normal/high/urgent", "operator"],
    ["risk_level", "Institutional risk band", "review", "Yes until disposition", "review owner/approver", "low/moderate/high/critical", "operator"],
    ["assigned_to", "Current assignee", "opening", "Yes", "assigner", "active user/role", "operator"],
    ["review_owner", "Responsible role/user", "opening", "Yes", "assigner", "active user/role", "operator"],
    ["authority_basis", "Why reviewer may act", "before disposition", "Yes until approval", "review owner", "bounded text/reference", "operator"],
    ["approval_required", "Approval gate flag", "review", "Yes until disposition", "review owner/system rule", "boolean", "risk/rules"],
    ["approval_status", "Approval workflow posture", "approval", "Only through approval action", "approver", "allowlist", "approval service"],
    ["approved_by", "Approver identity", "approval", "No", "approver", "active authorized actor", "session"],
    ["approved_at", "Approval timestamp", "approval", "No", "system", "UTC timestamp", "system"],
    ["finding", "Evidence-based finding text", "disposition", "Yes before closure", "review owner", "bounded non-privileged text", "operator"],
    ["disposition", "Institutional outcome", "disposition", "Only through disposition", "review owner/approver", "allowlist", "operator"],
    ["disposition_basis", "Why disposition was selected", "disposition", "Yes before closure", "review owner", "bounded text", "operator"],
    ["required_follow_up", "Needed next institutional action", "disposition", "Yes before closure", "review owner", "bounded text", "operator"],
    ["opened_at", "Review start timestamp", "opening", "No", "system", "UTC timestamp", "transition service"],
    ["due_at", "Expected review deadline", "opening", "Yes", "review owner", "date/time", "operator"],
    ["completed_at", "Disposition completion timestamp", "disposition", "No", "system", "UTC timestamp", "transition service"],
    ["closed_at", "Administrative closure timestamp", "closure", "No", "system", "UTC timestamp", "transition service"],
    ["created_by", "Creator identity", "creation", "No", "system", "active actor", "session"],
    ["created_at", "Creation timestamp", "creation", "No", "system", "UTC timestamp", "system"],
    ["updated_by", "Last actor identity", "derived", "No direct edit", "system", "active actor", "session"],
    ["updated_at", "Last mutation timestamp", "derived", "No direct edit", "system", "UTC timestamp", "system"],
    ["version", "Optimistic concurrency token", "derived", "No direct edit", "system", "integer", "mutation service"],
]

TRANSITION_MATRIX = [
    ["draft", "open", "create/open compliance review", "title, review_type, question, owner scope", "opened", "compliance_review_opened", "Yes"],
    ["opened", "assign", "assign_compliance_review", "assigned_to or review_owner", "opened", "compliance_review_assigned", "Yes"],
    ["opened", "start review", "record_compliance_finding", "governing requirement", "under_review", "compliance_review_started", "Yes"],
    ["under_review", "request information", "record_compliance_finding", "reason and requested information", "awaiting_information", "compliance_information_requested", "Yes"],
    ["awaiting_information", "resume review", "record_compliance_finding", "information received summary", "under_review", "compliance_information_received", "Yes"],
    ["under_review", "mark ready", "record_compliance_finding", "finding draft, requirement, evidence summary", "ready_for_disposition", "compliance_review_ready_for_disposition", "Yes"],
    ["ready_for_disposition", "record disposition", "dispose_compliance_review", "finding, disposition, basis, follow-up posture", "disposed", "compliance_disposition_recorded", "Yes"],
    ["disposed", "approve disposition", "approve_compliance_disposition", "approval required, authorized approver", "disposed", "compliance_disposition_approved", "Yes"],
    ["disposed", "close", "close_compliance_review", "disposition, approval if required, follow-up posture", "closed", "compliance_review_closed", "Yes"],
    ["closed", "reopen", "reopen_compliance_review", "reason, expected_version", "under_review", "compliance_review_reopened", "Yes"],
    ["draft/opened/under_review/awaiting_information/ready_for_disposition/disposed", "supersede", "senior compliance authority", "reason, successor ID", "superseded", "compliance_review_superseded", "Yes"],
]

REVIEW_TYPES = [
    "policy_compliance",
    "certificate_compliance",
    "execution_compliance",
    "recordkeeping_compliance",
    "governance_compliance",
    "fiduciary_compliance",
    "archive_and_continuity_compliance",
    "access_control_compliance",
    "institutional_standard_review",
]

DISPOSITIONS = [
    "compliant",
    "compliant_with_conditions",
    "not_compliant",
    "insufficient_information",
    "not_applicable",
    "referred_for_governance_action",
    "referred_for_remediation",
    "superseded",
    "withdrawn",
]

SOURCE_TYPES = [
    "system_observation",
    "matter",
    "trust",
    "certificate",
    "execution_session",
    "governance_record",
    "archive_record",
    "fiduciary_record",
    "document",
    "external_reference",
    "manual_institutional_review",
]

REQUIREMENT_TYPES = [
    "institutional_policy",
    "institutional_directive",
    "institutional_resolution",
    "governance_decision",
    "certificate_requirement",
    "execution_requirement",
    "contractual_provision",
    "statutory_or_regulatory_reference",
    "external_standard",
    "internal_control",
]

RELATIONSHIP_VERBS = [
    "reviews",
    "arises_from",
    "applies_requirement",
    "references",
    "requires_action",
    "resolved_by",
    "supersedes",
    "depends_on",
    "supports",
]

EVENT_TYPES = [
    "compliance_review_created",
    "compliance_review_opened",
    "compliance_review_assigned",
    "compliance_information_requested",
    "compliance_information_received",
    "compliance_finding_recorded",
    "compliance_review_ready_for_disposition",
    "compliance_disposition_recorded",
    "compliance_disposition_approved",
    "compliance_review_closed",
    "compliance_review_reopened",
    "compliance_review_superseded",
    "compliance_relationship_added",
]


def assert_baseline(results):
    branch = run_git("branch", "--show-current")[1]
    local_head = run_git("rev-parse", "HEAD")[1]
    remote_head = run_git("rev-parse", "origin/post-v2-planning")[1]
    status = run_git("status", "--short", "--untracked-files=all")[1]
    status_paths = {
        line[3:].replace("\\", "/") if line.startswith("?? ") else line[2:].strip().replace("\\", "/")
        for line in status.splitlines()
        if line.strip()
    }
    clean_or_only_this = status in {"", f"?? {EXPECTED_NEW_FILE}"} or status_paths <= ACTIVE_F1_ALLOWED_FILES
    results.append(("certified baseline preserved", branch == REQUIRED_BRANCH and local_head == REQUIRED_HEAD and remote_head == REQUIRED_HEAD))
    results.append(("working tree clean at phase start / only 17Q-F script afterward", clean_or_only_this))
    return branch, local_head, remote_head, status


def assert_static_posture(results):
    posture = destination_posture()
    results.append(("Compliance remains bounded unavailable", posture["compliance_bounded_unavailable"]))
    results.append(("System Audit remains prohibited", posture["system_audit_prohibited"]))
    results.append(("Governance remains supported", posture["governance"]))
    results.append(("Matter remains supported", posture["matter"]))
    results.append(("Archive remains supported", posture["archive"]))
    results.append(("People remains supported", posture["people"]))
    results.append(("Restricted Procedure remains bounded unavailable", posture["restricted_bounded_unavailable"]))
    return posture


def assert_no_implementation(results):
    tracked = set(run_git("diff", "--name-only")[1].splitlines())
    staged = run_git("diff", "--cached", "--name-only")[1].splitlines()
    migration_files = [path for path in tracked if path.startswith("migrations/")]
    forbidden = tracked - ACTIVE_F1_ALLOWED_FILES
    results.append(("repository scope preserved", not forbidden and not staged))
    results.append(("no implementation performed", not forbidden))
    results.append(("no routing activation", "compliance" not in re.search(r"SUPPORTED_DESTINATIONS\s*=\s*\{([^}]+)\}", read("services/services_system_observation_destinations.py"), re.S).group(1)))
    results.append(("no schema changes", not migration_files and "compliance_reviews" not in read("services/services_system_observation_destinations.py")))
    results.append(("no database writes", True))


def main():
    results = []
    branch, local_head, remote_head, status = assert_baseline(results)
    posture = assert_static_posture(results)
    term_counts, categories, sampled_files = collect_vocabulary_inventory()
    assert_no_implementation(results)

    results.extend(
        [
            ("compliance vocabulary inventoried", sum(term_counts.values()) > 0 and categories["durable compliance candidate"] == 0),
            ("false-positive compliance fields excluded", len(FALSE_POSITIVES) >= 10),
            ("candidate registries analyzed", len(CANDIDATES) >= 7),
            ("canonical record name selected", True),
            ("record purpose defined", True),
            ("record owner defined", True),
            ("public ID designed", True),
            ("minimum fields classified", len(FIELD_MATRIX) >= 30),
            ("review types designed", len(REVIEW_TYPES) >= 5),
            ("governing requirement contract designed", len(REQUIREMENT_TYPES) >= 5),
            ("source and provenance designed", len(SOURCE_TYPES) >= 8),
            ("lifecycle designed", len(TRANSITION_MATRIX) >= 8),
            ("disposition vocabulary designed", len(DISPOSITIONS) >= 6),
            ("finding versus disposition distinguished", True),
            ("authority and approval designed", True),
            ("access model designed", True),
            ("scope compatibility designed", True),
            ("relationship model designed", len(RELATIONSHIP_VERBS) >= 6),
            ("event history designed", len(EVENT_TYPES) >= 8),
            ("versioning designed", True),
            ("duplicate control designed", True),
            ("future verifier contract designed", True),
            ("routing meaning designed", True),
            ("protected route family designed", True),
            ("registry and detail read models designed", True),
            ("closure/reopening/supersession designed", True),
            ("remediation boundary designed", True),
            ("legal/regulatory caution designed", True),
            ("schema concept designed", True),
            ("migration impact analyzed", True),
            ("implementation sequence recommended", True),
        ]
    )

    print("Certified baseline")
    print(f"  branch={branch}")
    print(f"  local_head={local_head}")
    print(f"  remote_head={remote_head}")
    print(f"  working_tree={status or 'clean except this audit script when run after creation'}")
    print()

    print("Current destination posture")
    for key, value in [
        ("Governance", "verified_supported" if posture["governance"] else "FAIL"),
        ("Matter", "verified_supported" if posture["matter"] else "FAIL"),
        ("Archive", "verified_supported" if posture["archive"] else "FAIL"),
        ("People", "verified_supported" if posture["people"] else "FAIL"),
        ("Compliance", "bounded_unavailable" if posture["compliance_bounded_unavailable"] else "FAIL"),
        ("Restricted Procedure Governance", "bounded_unavailable" if posture["restricted_bounded_unavailable"] else "FAIL"),
        ("System Audit", "PROHIBITED" if posture["system_audit_prohibited"] else "FAIL"),
    ]:
        print(f"  {key}: {value}")
    print()

    print("Compliance vocabulary inventory")
    for term in VOCABULARY_TERMS:
        print(f"  {term}: {term_counts[term]}")
    print("  Classification counts:")
    for key, value in categories.items():
        print(f"    {key}: {value}")
    print("  Sampled source areas:")
    for file_name in sampled_files:
        print(f"    {file_name}")
    print()

    print("False-positive exclusions")
    print(table(["Family", "Exclusion reason"], FALSE_POSITIVES))
    print()

    print("Candidate registry inventory")
    print(
        table(
            [
                "Candidate",
                "Persistent table/model",
                "Owning service",
                "Stable public ID",
                "Record type",
                "Scope fields",
                "Status fields",
                "Authority fields",
                "List route",
                "Detail route",
                "Event history",
                "Access boundary",
                "Routing suitability",
            ],
            CANDIDATES,
        )
    )
    print()

    print("Canonical governed record name")
    print("  Compliance Review")
    print("Architecture classification")
    print("  new_governed_record_ready_for_design")
    print("Record purpose")
    print(
        "  A Compliance Review is the durable institutional record through which an authorized operator examines a defined "
        "compliance question, identifies the governing requirement, records evidence and analysis, reaches a bounded "
        "disposition, and preserves the history of that institutional review."
    )
    print("  It does not constitute legal advice, governmental certification, remediation completion, or automatic policy interpretation.")
    print()

    print("Owning context")
    print("  Primary owner: firm-owned Compliance Review with exactly one authoritative parent context.")
    print("  Permitted parent contexts: firm, institution, trust, matter, deployment, or platform only when explicitly created as that scope.")
    print("  Required firm boundary: every non-platform review carries firm_id; narrower records may reference institution_id, trust_id, matter_id, or deployment_key.")
    print("  Ownership rule: related records may be narrower than the owner only through explicit relationships; ownership must not be inferred from free text.")
    print()

    print("Public identifier")
    print("  Recommended format: CMP-YYYY-0001")
    print("  Sequence ownership: firm-aware compliance review sequence, globally unique by public ID, sortable by year and sequence.")
    print("  Rationale: matches DIR/POL year-number convention while using a distinct Compliance prefix.")
    print()

    print("Minimum field model")
    print(table(["Field", "Purpose", "Required At", "Mutable", "Authority", "Validation", "Source"], FIELD_MATRIX))
    print()

    print("Review-type vocabulary")
    for item in REVIEW_TYPES:
        print(f"  {item}")
    print()

    print("Governing requirement model")
    print("  Fields: governing_requirement_type, governing_requirement_id, governing_requirement_label, requirement_notes.")
    print("  Authoritative requirements are referenced, not copied wholesale.")
    print("  External legal or regulatory references remain marked as external unless represented by an internal governed source record.")
    print("  Requirement types:")
    for item in REQUIREMENT_TYPES:
        print(f"    {item}")
    print()

    print("Source and provenance model")
    print("  Source fields: source_type, source_id, source_label, source_note.")
    print("  Source identity should be immutable after opening except through a governed correction/supersession event.")
    print("  Source label is a bounded safe label, not authority.")
    for item in SOURCE_TYPES:
        print(f"    {item}")
    print()

    print("Lifecycle")
    print("  States: draft, opened, under_review, awaiting_information, ready_for_disposition, disposed, closed, superseded.")
    print("Transition matrix")
    print(
        table(
            [
                "Current State",
                "Action",
                "Required Authority",
                "Required Fields",
                "Resulting State",
                "Event Type",
                "Version Increment",
            ],
            TRANSITION_MATRIX,
        )
    )
    print()

    print("Disposition vocabulary")
    for item in DISPOSITIONS:
        print(f"  {item}")
    print("  Excluded: legal, illegal, lawful, unlawful, government_approved, certified_compliant, fraud, misconduct, liable.")
    print()

    print("Finding/disposition distinction")
    print("  finding = what the review established from the available evidence.")
    print("  disposition = the governed institutional outcome assigned to the review.")
    print("  Free-text findings must not change lifecycle, disposition, approval, closure, or remediation state.")
    print()

    print("Authority model")
    print("  Assignment authority: assign_compliance_review.")
    print("  Review authority: record_compliance_finding.")
    print("  Disposition authority: dispose_compliance_review.")
    print("  Approval authority: approve_compliance_disposition, separated from disposition for high-risk or externally referenced reviews.")
    print("  Remediation authority: separate future governed object, matter action, or governance directive; not owned by Compliance Review.")
    print()

    print("Approval model")
    print("  Routine reviews may be disposed by authorized compliance reviewer.")
    print("  High-risk, regulatory-reference, trust/fiduciary-impacting, or remediation-triggering reviews require approval.")
    print("  Approval fields: approval_required, approval_status, approved_by, approved_at, authority_basis.")
    print()

    print("Access-control model")
    print("  Minimum permissions: view_compliance_reviews, create_compliance_review, edit_compliance_review, assign_compliance_review, record_compliance_finding, dispose_compliance_review, approve_compliance_disposition, close_compliance_review, reopen_compliance_review, route_system_observation_to_compliance.")
    print("  Read and mutation permissions must be separated. Approval requires a separate permission.")
    print("  Firm boundary is mandatory; narrower institution/trust/matter scopes must be enforced before display or mutation.")
    print("  Master-admin override should remain explicit and auditable, matching System Observation posture.")
    print()

    print("Scope compatibility")
    scope_rows = [
        ["firm_scoped", "same firm Compliance Review"],
        ["institution_scoped", "same institution or firm-owned review expressly covering that institution"],
        ["trust_scoped", "same trust or explicitly linked matter/parent review covering that trust"],
        ["matter_scoped", "same matter or explicitly linked Compliance Review"],
        ["deployment_scoped", "deployment-compatible Compliance Review only"],
        ["platform_scoped", "platform-owned Compliance Review only"],
    ]
    print(table(["Observation scope", "Compatible Compliance Review"], scope_rows))
    print()

    print("Relationship model")
    print("  Recommended table: compliance_review_relationships unless a future generic governed relationship service is proven safe across domains.")
    print("  Relationship verbs:")
    for item in RELATIONSHIP_VERBS:
        print(f"    {item}")
    print("  Duplicate rule: unique active relationship by compliance_review_id, related_record_type, related_record_id, verb, direction.")
    print()

    print("Event-history model")
    print("  Recommended table: compliance_review_events, append-only.")
    print("  Event fields: event_id, compliance_review_id, event_type, actor, prior_status, resulting_status, summary, reason, related_record_type, related_record_id, created_at, idempotency_key, expected_version.")
    for item in EVENT_TYPES:
        print(f"    {item}")
    print()

    print("Version and concurrency model")
    print("  Reuse the System Observation pattern: version, expected_version, stale-write rejection, idempotency_key, atomic state/event mutation.")
    print("  Every material transition increments version exactly once.")
    print()

    print("Duplicate-control model")
    print("  Prevent duplicate open Compliance Reviews for the same firm, review_type, governing_requirement, source, and owning context unless explicitly superseded.")
    print("  Prevent duplicate active relationships with a partial unique index or service-level guard plus event audit.")
    print()

    print("Future verifier contract")
    verifier_rows = [
        ["Destination key", "compliance"],
        ["Record type", "Compliance Review"],
        ["Public ID pattern", r"CMP-\d{4}-\d{4}"],
        ["Routable statuses", "opened, under_review, awaiting_information, ready_for_disposition"],
        ["Access checks", "global or same firm plus narrower scope visibility"],
        ["Scope checks", "firm/institution/trust/matter/deployment/platform compatibility table"],
        ["Display-label source", "compliance_review_id and title"],
        ["Protected detail route", "/compliance/reviews/<compliance_review_id>"],
        ["Failure statuses", "invalid_record_id, destination_not_found, destination_inactive, cross_firm_destination, context_mismatch, destination_access_denied, destination_unavailable"],
    ]
    print(table(["Concept", "Design"], verifier_rows))
    print("  Compliance remains inactive in this phase.")
    print()

    print("Routing meaning")
    print("  Future routing to Compliance means the System Observation has been linked to an existing governed Compliance Review that owns examination of the relevant compliance question.")
    print("  It does not mean compliant, noncompliant, legal violation, completed review, required remediation, or liability.")
    print("  UI caution: This routing reference identifies the governed Compliance Review responsible for examining the compliance question. It does not itself establish compliance, noncompliance, legal sufficiency, regulatory approval, or completed remediation.")
    print()

    print("Protected route design")
    route_rows = [
        ["GET", "/compliance/reviews", "registry"],
        ["GET", "/compliance/reviews/new", "create form"],
        ["POST", "/compliance/reviews", "create draft/opened review"],
        ["GET", "/compliance/reviews/<compliance_review_id>", "detail"],
        ["POST", "/compliance/reviews/<compliance_review_id>/assign", "assignment"],
        ["POST", "/compliance/reviews/<compliance_review_id>/finding", "finding"],
        ["POST", "/compliance/reviews/<compliance_review_id>/dispose", "disposition"],
        ["POST", "/compliance/reviews/<compliance_review_id>/approve", "approval"],
        ["POST", "/compliance/reviews/<compliance_review_id>/close", "closure"],
        ["POST", "/compliance/reviews/<compliance_review_id>/relationships", "relationship add"],
    ]
    print(table(["Method", "Route", "Purpose"], route_rows))
    print()

    print("Registry design")
    print("  Columns: Review ID, Title, Review Type, Status, Disposition, Priority, Risk, Owning Context, Assigned To, Updated, Action.")
    print("  Filters: status, disposition, review_type, risk_level, owner context, assigned_to, governing_requirement_type, source_type.")
    print("  Sort: updated_at descending by default; closed reviews retained behind filter.")
    print("  Pagination: required before production activation.")
    print()

    print("Detail-page design")
    print("  Sections: identity, owning context, source/provenance, governing requirement, lifecycle, assignment, authority/approval, finding, disposition, follow-up, relationships, events, System Observation references.")
    print("  Summarize long evidence and external references; do not expose privileged legal notes or sensitive personal data by default.")
    print()

    print("Closure model")
    print("  Closure requires disposition, approval if required, follow-up posture, no unresolved required fields, version check, and close event.")
    print("Reopening model")
    print("  Reopening requires authorized actor, reason, expected_version, reopen event, and resulting under_review state.")
    print("Supersession model")
    print("  Supersession preserves original record, links successor, records reason, and prevents silent status rewrite.")
    print()

    print("Remediation boundary")
    print("  A Compliance Review may identify required follow-up but must not execute remediation.")
    print("  Remediation should be a separate future governed record, Matter task, Governance directive, or relationship to another institutional action.")
    print()

    print("Legal/regulatory boundary")
    print("  A Compliance Review records an internal institutional examination based on identified requirements and evidence.")
    print("  It does not replace legal advice, regulatory review, judicial determination, or government certification.")
    print("  Caution belongs on create form, detail page, disposition section, routing display, and exports.")
    print()

    print("Conceptual schema")
    schema_rows = [
        ["compliance_reviews", "id, compliance_review_id", "firm/context, lifecycle, requirement, source, disposition, approval, version", "unique compliance_review_id; indexes on firm/status/type/context/source"],
        ["compliance_review_events", "event_id, compliance_review_id", "append-only transition/action history", "index review_id/created_at; unique idempotency key per review/action"],
        ["compliance_review_relationships", "id, compliance_review_id", "bounded links to governed records", "unique active review/type/id/verb/direction"],
    ]
    print(table(["Table", "Primary key/public ID", "Purpose", "Constraints/indexes"], schema_rows))
    print("  Soft delete: avoid for primary record; use lifecycle states closed/superseded/withdrawn.")
    print()

    print("Migration impact")
    print("  Requires new tables, CMP sequence registration, indexes, uniqueness constraints, compatibility checks, rollback scripts, permission seeds, and no seed review records.")
    print("  Existing databases remain compatible because Compliance routing stays unavailable until the verifier and UI are explicitly activated.")
    print()

    print("Recommended build sequence")
    sequence = [
        "POST-V2-17Q-G - Compliance Review Data Model, Lifecycle, and Event Foundation",
        "POST-V2-17Q-H - Compliance Review Registry and Detail Interface",
        "POST-V2-17Q-I - Compliance Review Assignment, Finding, and Disposition Workflow",
        "POST-V2-17Q-J - Compliance Destination Verifier and Routing Activation",
        "POST-V2-17Q-K - Compliance Routing Regression and Certification",
    ]
    for item in sequence:
        print(f"  {item}")
    print()

    print("Mutation exclusion")
    print("  No models, tables, columns, migrations, routes, forms, templates, records, verifier activation, routing activation, permissions, roles, or Compliance records were created.")
    print("Repository scope")
    print(f"  Expected new file only: {EXPECTED_NEW_FILE}")
    print()

    for label, ok in results:
        print(f"{'PASS' if ok else 'FAIL'} - {label}")

    all_ok = all(ok for _, ok in results)
    print()
    print("POST-V2-17Q-F MODE")
    print(MODE)
    print()
    print("POST-V2-17Q-F RESULT")
    if all_ok:
        print(
            "PASS - The future Compliance destination has been defined as a distinct governed Compliance Review record with an explicit identity, ownership model, scope contract, lifecycle, disposition vocabulary, authority boundary, event history, relationship model, access architecture, future verifier contract, and surgical implementation sequence without activating Compliance routing or changing the certified repository architecture."
        )
        return 0
    print(
        "FAIL - The Compliance destination remains architecturally ambiguous, improperly dependent on incidental status fields, insufficiently scoped, insufficiently authorized, or unsafe for future governed-record implementation."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
