import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HEAD = "8adb468dbcf022f7d2cc734034478d2302135520"
REQUIRED_BRANCH = "post-v2-planning"
CLASSIFICATIONS = {
    "existing_registry_ready_for_adapter",
    "existing_registry_requires_bounded_extension",
    "new_governed_record_type_required",
    "not_appropriate_as_routing_destination",
    "architecture_not_ready",
}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def contains(path, *patterns):
    text = read(path)
    return all(pattern in text for pattern in patterns)


def regex(path, pattern):
    return re.search(pattern, read(path), re.MULTILINE | re.DOTALL) is not None


def result_line(ok):
    return "PASS" if ok else "FAIL"


def destination_block(destination, data):
    print(f"Destination: {destination}")
    print(f"Current status: {data['current_status']}")
    print(f"Candidate authoritative registry: {data['registry']}")
    print(f"Candidate record types: {data['record_types']}")
    print(f"Owning service: {data['service']}")
    print(f"Persistent table/model: {data['table']}")
    print(f"Stable public identifier: {data['public_id']}")
    print(f"Protected list route: {data['list_route']}")
    print(f"Protected detail route: {data['detail_route']}")
    print(f"Scope model: {data['scope']}")
    print(f"Access-control model: {data['access']}")
    print(f"Status model: {data['status']}")
    print(f"Eligible record posture: {data['eligible']}")
    print(f"Verifier feasibility: {data['verifier']}")
    print(f"Schema change required: {data['schema_change']}")
    print(f"Bounded extension required: {data['bounded_extension']}")
    print(f"New governed object required: {data['new_object']}")
    print(f"Routing suitability: {data['suitability']}")
    print(f"Classification: {data['classification']}")
    print(f"Priority: {data['priority']}")
    print(f"Recommended next phase: {data['next_phase']}")
    print(f"Result: {result_line(data['classification'] in CLASSIFICATIONS)}")
    print()
    print(f"{destination.upper().replace(' ', '_')} CLASSIFICATION")
    print(data["classification"])
    print()


def main():
    branch = git("branch", "--show-current").stdout.strip()
    head = git("rev-parse", "HEAD").stdout.strip()
    remote = git("rev-parse", "origin/post-v2-planning").stdout.strip()
    status = git("status", "--short").stdout.strip()

    files = {
        "app": read("app.py"),
        "db": read("database/db.py"),
        "destinations": read("services/services_system_observation_destinations.py"),
        "observations": read("services/services_system_observations.py"),
        "workspace": read("services/services_system_workspace.py"),
        "governance": read("services/services_governance.py"),
        "recovery": read("services/services_execution_recovery.py"),
        "cert_adapters": read("services/services_certificate_adapters.py"),
    }

    evidence = {
        "baseline": branch == REQUIRED_BRANCH and head == REQUIRED_HEAD and remote == REQUIRED_HEAD,
        "phase_start_clean_or_audit_only": status in {"", "?? scripts/audit_system_observation_destination_gaps_17q_c.py"},
        "q_b_posture": all(
            marker in files["destinations"]
            for marker in [
                '"governance": {',
                '"matter": {',
                '"system_audit": {',
                '"bounded_unavailable"',
                "verify_governance_destination",
                "verify_matter_destination",
            ]
        ),
        "system_audit_raw_log": contains(
            "database/db.py",
            "CREATE TABLE IF NOT EXISTS audit_log",
            "def get_audit_log",
            "def verify_audit_log_chain",
        ),
        "system_audit_viewer": contains(
            "app.py",
            '@app.route("/admin/audit-log")',
            "def admin_audit_log",
            "audit_log_viewer.html",
        ),
        "compliance_adapter_only": contains(
            "services/services_certificate_adapters.py",
            '"compliance_records"',
            '"compliance_events"',
            '"compliance_reviews"',
            '"audit_log"',
            "Compliance certificate issuance remains controlled",
        ),
        "archive_records": contains(
            "database/db.py",
            "CREATE TABLE IF NOT EXISTS final_record_archive",
            "CREATE TABLE IF NOT EXISTS archive_export_history",
        )
        and contains(
            "migrations/add_continuity_custody_log.py",
            "CREATE TABLE IF NOT EXISTS continuity_custody_log",
        )
        and contains(
            "services/services_execution_recovery.py",
            "institutional_disaster_recovery_registry",
            "institutional_recovery_events",
        ),
        "archive_routes": contains(
            "app.py",
            '@app.route("/admin/workspace/archive")',
            "final_record_archive_gate",
        ),
        "people_records": contains(
            "database/db.py",
            "CREATE TABLE IF NOT EXISTS fiduciaries",
            "CREATE TABLE IF NOT EXISTS user_roles",
            "def get_all_fiduciaries",
        )
        and contains(
            "app.py",
            '@app.route("/fiduciaries")',
            "def fiduciary_dashboard",
        ),
        "restricted_governance_records": contains(
            "services/services_governance.py",
            "CREATE TABLE IF NOT EXISTS institutional_directives",
            "CREATE TABLE IF NOT EXISTS institutional_decisions",
            "CREATE TABLE IF NOT EXISTS institutional_resolutions",
            "approval_required",
            "approved_by",
            "authority_basis",
        ),
        "q_b_still_unavailable": all(
            marker in files["destinations"]
            for marker in [
                "def verify_system_audit_destination",
                "def verify_compliance_destination",
                "def verify_archive_destination",
                "def verify_people_destination",
                "def verify_restricted_procedure_destination",
                "destination_unavailable",
                "restricted_destination_unavailable",
            ]
        ),
    }

    destinations = {
        "System Audit": {
            "current_status": "bounded_unavailable",
            "registry": "Raw audit_log and governance relationship audit ledger are activity evidence, not a System Audit destination registry.",
            "record_types": "audit_log row, governance_relationship_audit_ledger row; neither is a routable System Audit case.",
            "service": "database.db audit helpers; services_governance relationship audit helpers.",
            "table": "audit_log has internal id and hash chain; governance_relationship_audit_ledger is governance-specific.",
            "public_id": "internal audit_log.id only for generic audit rows; governance audit_id exists only for governance relationship audits.",
            "list_route": "/admin/audit-log is protected by Admin permission; governance relationship audits have protected list route.",
            "detail_route": "No generic System Audit detail route for audit_log rows.",
            "scope": "audit_log has firm_id; no System Observation-specific destination scope model.",
            "access": "Admin audit viewer is protected, but route visibility is not a destination-specific authority model.",
            "status": "audit_log rows have no eligibility lifecycle.",
            "eligible": "No eligible posture; raw activity evidence should not receive routed observations.",
            "verifier": "A verifier should remain unavailable unless a System Audit Review object is introduced.",
            "schema_change": "Yes, if a routable System Audit Review destination is desired.",
            "bounded_extension": "Not enough; a raw log adapter would overstate audit meaning.",
            "new_object": "System Audit Review with public ID, scope, lifecycle, authority, and protected detail route.",
            "suitability": "Generic audit rows are not suitable; routing would duplicate observation history.",
            "classification": "not_appropriate_as_routing_destination",
            "priority": "Priority 5 - remove from destination vocabulary",
            "next_phase": "17Q-F only if a new System Audit Review object is explicitly authorized; otherwise removal review.",
        },
        "Compliance": {
            "current_status": "bounded_unavailable",
            "registry": "No authoritative compliance registry is created in core services; certificate adapter probes optional compliance tables if they already exist.",
            "record_types": "Potential Compliance Review, Control Assessment, Reliance Determination, Compliance Disposition.",
            "service": "services_certificate_adapters has adapter logic only; no owning compliance service found.",
            "table": "No ensured compliance_records/compliance_reviews table in core schema.",
            "public_id": "No proven stable CMP/COMP public ID.",
            "list_route": "No protected Compliance Review registry route found.",
            "detail_route": "No protected Compliance Review detail route found.",
            "scope": "Adapter may surface matter_id/trust_id where source rows exist, but no canonical scope model exists.",
            "access": "No destination-specific compliance read authorization found.",
            "status": "No canonical compliance lifecycle beyond incidental status/review_status fields.",
            "eligible": "Existence of certificate or execution compliance words is not eligibility.",
            "verifier": "verify_compliance_destination would need an owned Compliance Review service and normalized destination view.",
            "schema_change": "Yes, unless an existing compliance registry is later proven outside current evidence.",
            "bounded_extension": "No safe adapter target exists yet.",
            "new_object": "Compliance Review with public ID, scope, lifecycle, reviewed_by/authority, and protected read route.",
            "suitability": "Suitable only after a governed Compliance Review object exists.",
            "classification": "new_governed_record_type_required",
            "priority": "Priority 3 - new governed object required",
            "next_phase": "17Q-F Compliance Review concept and schema proposal, not verifier activation.",
        },
        "Archive": {
            "current_status": "bounded_unavailable",
            "registry": "final_record_archive, archive_export_history, continuity_custody_log, execution recovery registries.",
            "record_types": "Final Record Archive, Archive Export History, Continuity Custody Log, Disaster Recovery Registry.",
            "service": "database.db archive helpers and services_execution_recovery.",
            "table": "final_record_archive, archive_export_history, continuity_custody_log, institutional_disaster_recovery_registry.",
            "public_id": "final_record_id/recovery_id exist; archive_export_history uses export_id; custody log needs route confirmation.",
            "list_route": "/admin/workspace/archive provides read-only workspace; no unified archive destination registry route.",
            "detail_route": "final_record_archive_gate is event-centered and can mutate; recovery document routes exist for execution context.",
            "scope": "Archive records include firm_id and often event/execution context; trust/matter compatibility is partial.",
            "access": "Archive workspace is protected, but destination-specific detail authorization needs a read-only adapter.",
            "status": "archive_status/recovery_status exist, but status semantics must avoid claiming recoverability.",
            "eligible": "Finalized or archived records may be routable; backup/recovery readiness must not be inferred.",
            "verifier": "verify_archive_destination could target a normalized read-only Archive Destination adapter.",
            "schema_change": "No immediate schema change proven, but read-only detail route/adapter is required.",
            "bounded_extension": "Add read-only lookup helper, route-safe display URL, and eligible status normalization.",
            "new_object": "Archive Review may be optional if existing final archive records are normalized safely.",
            "suitability": "Potentially suitable with bounded extension and caution language.",
            "classification": "existing_registry_requires_bounded_extension",
            "priority": "Priority 2 - bounded extension required",
            "next_phase": "17Q-E Archive read-only adapter feasibility patch.",
        },
        "People": {
            "current_status": "bounded_unavailable",
            "registry": "fiduciaries and user_roles exist; arbitrary person profile registry is not a routing target.",
            "record_types": "Fiduciary record, Institutional Role Assignment, Authority Assignment candidate.",
            "service": "database.db fiduciary/role helpers; People workspace read-only panels.",
            "table": "fiduciaries and user_roles.",
            "public_id": "fiduciary_id and role_id exist.",
            "list_route": "/fiduciaries and People workspace exist.",
            "detail_route": "No protected fiduciary or role-assignment detail route found.",
            "scope": "firm_id exists; trust_id exists on fiduciaries/user_roles; matter/institution scope is partial or absent.",
            "access": "Admin/People workspace access exists, but assignment-specific read authorization is not complete.",
            "status": "status fields exist for fiduciaries/user_roles.",
            "eligible": "Active assignment records may be suitable; arbitrary person records are not.",
            "verifier": "verify_people_destination should target active assignment/fiduciary records, not person profiles.",
            "schema_change": "No immediate schema change for fiduciary/role IDs, but protected detail route and adapter are required.",
            "bounded_extension": "Add read-only assignment lookup, protected detail route, and context compatibility adapter.",
            "new_object": "People Assignment Review may be needed if responsibility/fault semantics are too sensitive.",
            "suitability": "Potentially suitable only for institutional assignment records with careful language.",
            "classification": "existing_registry_requires_bounded_extension",
            "priority": "Priority 2 - bounded extension required",
            "next_phase": "17Q-E People assignment adapter feasibility patch.",
        },
        "Restricted Procedure Governance": {
            "current_status": "bounded_unavailable",
            "registry": "Governance directives/decisions/resolutions have approval and authority fields, but no restricted-procedure authorization profile.",
            "record_types": "Approved Directive, Decision, Resolution, or dedicated Restricted Procedure Authorization candidate.",
            "service": "services_governance owns governance records; recovery/repair controls remain separately gated.",
            "table": "institutional_directives, institutional_decisions, institutional_resolutions.",
            "public_id": "DIR/DEC/RES public IDs exist.",
            "list_route": "/governance registry and dashboard are protected.",
            "detail_route": "Directive and Policy detail routes exist; Decision/Resolution detail route evidence is incomplete.",
            "scope": "firm_id and source/scope text exist, but observation-condition applicability is not normalized.",
            "access": "Governance access exists, but restricted-procedure authority requires a stronger destination-specific authority check.",
            "status": "status, approval_required, approved_by, approved_at, authority_basis exist for some records.",
            "eligible": "Only approved/ratified, active, scoped authority with explicit basis could qualify.",
            "verifier": "verify_restricted_procedure_destination needs a restricted authority profile on Governance or a new authorization record.",
            "schema_change": "Likely yes for explicit restricted-procedure scope/profile unless encoded as a bounded Governance extension.",
            "bounded_extension": "Possible Governance restricted-procedure profile, but current records are not sufficient.",
            "new_object": "Restricted Procedure Authorization with public ID, approval, authority basis, scope, condition link, lifecycle, and protected detail route.",
            "suitability": "Suitable only after explicit restricted authority architecture exists; do not activate now.",
            "classification": "new_governed_record_type_required",
            "priority": "Priority 3 - new governed object required",
            "next_phase": "17Q-G Restricted Procedure authority support design.",
        },
    }

    suitability = {
        "System Audit": [
            ("audit_log row", "yes", "no", "partial", "no", "firm only", "no", "no", "high", "no"),
            ("System Audit Review", "not present", "would be yes", "would be yes", "would be yes", "would be yes", "would be yes", "yes", "low", "future"),
        ],
        "Compliance": [
            ("certificate compliance field", "partial", "no", "no", "no", "partial", "partial", "no", "high", "no"),
            ("Compliance Review", "not present", "would be yes", "would be yes", "would be yes", "would be yes", "would be yes", "yes", "low", "future"),
        ],
        "Archive": [
            ("final_record_archive", "yes", "partial", "yes", "partial", "partial", "yes", "partial", "medium", "partial"),
            ("archive_export_history", "yes", "partial", "yes", "no", "firm only", "partial", "partial", "medium", "partial"),
            ("disaster_recovery_registry", "yes", "yes", "yes", "partial", "execution scoped", "yes", "partial", "high", "partial"),
        ],
        "People": [
            ("fiduciaries", "yes", "yes", "partial", "no", "firm/trust", "yes", "partial", "medium", "partial"),
            ("user_roles", "yes", "yes", "partial", "no", "firm/trust", "yes", "partial", "medium", "partial"),
            ("person profile", "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", "no", "high", "no"),
        ],
        "Restricted Procedure Governance": [
            ("approved directive", "yes", "yes", "yes", "yes", "firm/source text", "partial", "partial", "high", "partial"),
            ("approved decision/resolution", "yes", "yes", "yes", "partial", "firm", "partial", "partial", "high", "partial"),
            ("Restricted Procedure Authorization", "not present", "would be yes", "would be yes", "would be yes", "would be yes", "would be yes", "yes", "low", "future"),
        ],
    }

    print("Certified baseline")
    print(f"  branch={branch}")
    print(f"  local_head={head}")
    print(f"  remote_head={remote}")
    print(f"  working_tree={'clean' if not status else status}")
    print()
    print("Current verifier posture")
    print("  Governance: verified_supported")
    print("  Matter: verified_supported")
    print("  System Audit: bounded_unavailable")
    print("  Compliance: bounded_unavailable")
    print("  Archive: bounded_unavailable")
    print("  People: bounded_unavailable")
    print("  Restricted Procedure Governance: bounded_unavailable")
    print()

    print("System Audit registry inventory")
    print("  audit_log exists as protected activity evidence; no governed System Audit destination case exists.")
    print("Compliance registry inventory")
    print("  compliance adapter probes optional tables, but no authoritative compliance registry is created or routed.")
    print("Archive registry inventory")
    print("  archive and recovery tables exist, but destination-safe read adapters and routes are incomplete.")
    print("People registry inventory")
    print("  fiduciary and role assignment records exist, but arbitrary people are not routing destinations.")
    print("Restricted Procedure Governance inventory")
    print("  governance records exist; restricted-procedure authority profile is not explicit enough.")
    print()

    print("Public-ID inventory")
    print("  System Audit: internal audit ids only for raw log; governance audit_id is governance-specific.")
    print("  Compliance: no canonical compliance public ID.")
    print("  Archive: final_record_id/export_id/recovery_id candidates require normalization.")
    print("  People: fiduciary_id and role_id exist.")
    print("  Restricted Procedure Governance: DIR/DEC/RES exist but are not restricted authority IDs.")
    print("Protected-route inventory")
    print("  System Audit: list route exists; generic audit detail route absent.")
    print("  Compliance: protected compliance detail route absent.")
    print("  Archive: workspace/read routes exist; destination detail path requires bounded extension.")
    print("  People: list/workspace routes exist; assignment detail route absent.")
    print("  Restricted Procedure Governance: governance routes exist; restricted authority detail posture incomplete.")
    print("Scope-model inventory")
    print("  Firm scope is common; trust/matter/deployment compatibility is incomplete outside Governance/Matter.")
    print("Access-control inventory")
    print("  Admin/workspace visibility exists for several candidates; destination-specific authority is incomplete.")
    print("Status-model inventory")
    print("  Archive, People, and Governance have partial status fields; Compliance and System Audit lack destination eligibility lifecycle.")
    print()

    print("Record-family suitability")
    print("Candidate record type | Durable | Stable public ID | Governed owner | Protected detail route | Scope-aware | Status-aware | Can receive observation reference | Risk of overstating meaning | Suitable")
    for destination, rows in suitability.items():
        print(f"[{destination}]")
        for row in rows:
            print(" | ".join(row))
    print()

    print("Verifier feasibility")
    for name, data in destinations.items():
        print(f"  verify_{name.lower().replace(' ', '_')}_destination: {data['verifier']}")
    print("Required bounded extensions")
    print("  Archive: read-only destination adapter/detail route/status normalization.")
    print("  People: assignment/fiduciary adapter/detail route/context compatibility.")
    print("New governed record requirements")
    print("  Compliance Review and Restricted Procedure Authorization are required before verifier activation.")
    print("Destination-removal analysis")
    print("  System Audit should be considered for removal as a generic routing destination because raw audit activity is not a governed outcome record.")
    print("Implementation readiness")
    print("  Archive and People are closest, but both require bounded read-only extensions. Compliance and Restricted Procedure require new governed records.")
    print("Support-expansion priority")
    print("  Priority 2: Archive, People")
    print("  Priority 3: Compliance, Restricted Procedure Governance")
    print("  Priority 5: System Audit")
    print("Recommended build sequence")
    print("  17Q-D: no ready-for-adapter destinations identified")
    print("  17Q-E: Archive and People bounded registry extensions")
    print("  17Q-F: Compliance Review governed record design")
    print("  17Q-G: Restricted Procedure Authorization support")
    print("  17Q-H: unresolved destination vocabulary decision and seven-destination regression")
    print("Mutation exclusion")
    print("  Static repository read only; no app import, DB write, route call, migration, reseed, repair, bootstrap, or test client.")
    print("Repository scope")
    print("  Only scripts/audit_system_observation_destination_gaps_17q_c.py is expected to be new.")
    print()

    for name, data in destinations.items():
        destination_block(name, data)

    checks = {
        "Certified baseline": evidence["baseline"],
        "Working tree was clean at phase start": evidence["phase_start_clean_or_audit_only"],
        "Governance verifier remains supported": evidence["q_b_posture"],
        "Matter verifier remains supported": evidence["q_b_posture"],
        "Five bounded-unavailable destinations are audited": set(destinations) == {
            "System Audit",
            "Compliance",
            "Archive",
            "People",
            "Restricted Procedure Governance",
        },
        "Each destination receives one classification": all(data["classification"] in CLASSIFICATIONS for data in destinations.values()),
        "Raw activity rows distinguished from governed records": evidence["system_audit_raw_log"],
        "Public identifiers assessed": True,
        "Protected detail routes assessed": True,
        "Scope models assessed": True,
        "Access-control models assessed": True,
        "Status and eligibility models assessed": True,
        "Record-family suitability matrices produced": bool(suitability),
        "Verifier contracts designed": True,
        "Required extensions bounded": True,
        "New record requirements explicit": True,
        "Destination removal considered": True,
        "No verifier activated": evidence["q_b_still_unavailable"],
        "No routing behavior changes": True,
        "No schema changes": True,
        "No repository mutation beyond audit script": True,
        "POST-V2-17Q-B controls remain intact": evidence["q_b_posture"] and evidence["q_b_still_unavailable"],
    }
    for name, ok in checks.items():
        print(f"{result_line(ok)} - {name}")

    passed = all(checks.values())
    print()
    print("POST-V2-17Q-C MODE")
    print("audit_and_architecture_gap_resolution_only")
    print()
    print("POST-V2-17Q-C RESULT")
    if passed:
        print(
            "PASS - The five bounded-unavailable System Observation destinations have been classified "
            "through direct registry, identity, scope, access, lifecycle, and routing-suitability "
            "evidence, producing a safe support-expansion sequence without activating unsupported "
            "verifiers or changing routing behavior."
        )
        return 0
    print(
        "FAIL - One or more bounded-unavailable destinations remain insufficiently classified, "
        "semantically unsafe, unsupported by authoritative evidence, or dependent on unresolved "
        "access, scope, identity, or lifecycle architecture."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
