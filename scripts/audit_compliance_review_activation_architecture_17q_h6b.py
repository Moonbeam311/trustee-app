import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "compliance_review_activation_architecture_h6b.md"
SERVICE = ROOT / "services" / "services_compliance_reviews.py"
MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
APP = ROOT / "app.py"

failures = []

def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:220]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def run(*args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=120)


def main():
    doc = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    service = SERVICE.read_text(encoding="utf-8") if SERVICE.exists() else ""
    migration = MIGRATION.read_text(encoding="utf-8") if MIGRATION.exists() else ""
    app = APP.read_text(encoding="utf-8") if APP.exists() else ""

    check("architecture document exists", DOC.exists())
    for heading in (
        "Object Model", "Lifecycle", "Subject And Relationship Model", "Evidence Architecture",
        "Findings Architecture", "Remediation Architecture", "Approval And Certification",
        "Audit Ledger", "Database Schema", "Identifiers", "Authorization Boundary",
        "Response Semantics", "Activation Registry", "Migration Boundary", "Service Boundary",
        "Temporary Validation", "Normal `trustee_app.db` must remain free",
    ):
        check("document covers " + heading, heading in doc)

    required_tables = [
        "compliance_reviews", "compliance_review_subjects", "compliance_review_evidence",
        "compliance_review_findings", "compliance_review_remediations", "compliance_review_approvals",
        "compliance_review_certifications", "compliance_review_relationships",
        "compliance_review_audit_ledger", "compliance_review_activation_registry",
    ]
    for table in required_tables:
        check("table documented: " + table, table in doc and table in migration)

    for term in ("Foundation unavailable", "Authorization denied", "Record not found", "Invalid lifecycle transition", "Activation not authorized", "Migration failure"):
        check("response semantic distinct: " + term, term in doc)

    for field in ("previous_hash", "entry_hash", "hash_algorithm", "firm_id"):
        check("audit ledger field: " + field, field in doc and field in migration)

    for identifier in ("CMP-YYYY-000001", "CEV-YYYY-000001", "CFN-YYYY-000001", "CRM-YYYY-000001", "CAP-YYYY-000001", "CCT-YYYY-000001", "CRL-YYYY-000001", "CAL-YYYY-000001", "CAR-YYYY-000001"):
        check("identifier family: " + identifier, identifier in doc)

    for function_name in (
        "foundation_available", "activation_status", "validate_review_transition", "generate_compliance_review_id",
        "list_compliance_reviews", "get_compliance_review", "create_compliance_review", "transition_compliance_review",
    ):
        check("service function present: " + function_name, f"def {function_name}" in service)

    create_block = service[service.index("def create_compliance_review"):service.index("def validate_review_transition")]
    transition_block = service[service.index("def transition_compliance_review"):service.index("__all__")]
    check("create fails closed before activation", "foundation_unavailable" in create_block and "ensure_compliance_review_foundation" not in create_block)
    check("transition fails closed before activation", "foundation_unavailable" in transition_block and "ensure_compliance_review_foundation" not in transition_block)
    check("service does not import activation migration", "activate_compliance_review_foundation" not in service)

    tree = ast.parse(migration)
    top_calls = [node for node in tree.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)]
    check("migration has no top-level execution call", not top_calls)
    check("migration requires explicit database", "required=True" in migration and "--database" in migration)
    check("migration requires explicit mode", "add_mutually_exclusive_group(required=True)" in migration)
    check("migration requires activation token", "--activation-token" in migration and "REQUIRED_TOKEN" in migration)
    check("migration refuses trustee_app.db", "NORMAL_DB" in migration and "trustee_app.db is refused" in migration)
    check("migration refuses repository target", "target must be outside the repository" in migration)
    check("migration has rollback path", "conn.rollback()" in migration and "BEGIN IMMEDIATE" in migration)
    check("migration has partial-schema conflict detection", "partial_schema_conflict" in migration)
    check("migration inserts no sample records", "sample_records=0" in migration)

    route_block = app[app.index("def _compliance_review_read_scope"):app.index("def _system_observation_read_scope")]
    check("current compliance routes remain bounded", '@app.route("/compliance/reviews", methods=["GET", "POST"])' in route_block and '"/compliance/reviews/<compliance_review_id>"' in route_block)
    check("no browser activation route", "activate_compliance_review" not in app and "activation-token" not in app)

    status = run("git", "diff", "--cached", "--name-only")
    check("staging empty", status.stdout.strip() == "")

    print("POST-V2-17Q-H.6B ARCHITECTURE AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
