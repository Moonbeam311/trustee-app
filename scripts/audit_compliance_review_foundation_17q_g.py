from html.parser import HTMLParser
from pathlib import Path
import importlib
import inspect
import os
import re
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TEMP_DB = Path(tempfile.gettempdir()) / "trustee_post_v2_17q_g_compliance_review.db"
os.environ["DB_PATH"] = str(TEMP_DB)
sys.path.insert(0, str(ROOT))

from migrations.add_compliance_review_foundation import ensure_compliance_review_foundation
from services.services_compliance_reviews import (
    create_compliance_review,
    get_compliance_review,
    get_compliance_review_by_id,
    get_compliance_review_by_public_id,
    list_compliance_review_events,
    transition_compliance_review,
)
from services.services_system_observation_destinations import verify_destination_record


EXPECTED_TABLES = {
    "compliance_review_number_sequences",
    "compliance_reviews",
    "compliance_review_events",
    "compliance_review_relationships",
}
ALLOWED_MODIFIED_FILES = {
    "app.py",
    "database/db.py",
    "services/services_compliance_reviews.py",
    "templates/ios_workspaces/compliance.html",
    "scripts/audit_compliance_review_foundation_17q_g.py",
    "scripts/audit_system_observation_foundation_17m.py",
}
ALLOWED_UNTRACKED_FILES = {
    "migrations/reconcile_role_permissions_baseline.py",
    "scripts/audit_authorization_baseline_reconciliation_17q_h6a_r6.py",
    "scripts/audit_compliance_review_readonly_ui_17q_h.py",
    "templates/compliance_reviews/registry.html",
    "templates/compliance_reviews/detail.html",
}
AUTHORIZED_ACTOR = {
    "actor_id": "admin",
    "actor_label": "Admin Operator",
    "firm_id": "FIRM-002",
    "scope": {"firm_id": "FIRM-002"},
}
OTHER_FIRM_ACTOR = {
    "actor_id": "other",
    "actor_label": "Other Firm Operator",
    "firm_id": "FIRM-003",
    "scope": {"firm_id": "FIRM-003"},
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


def connect():
    conn = sqlite3.connect(TEMP_DB)
    conn.row_factory = sqlite3.Row
    return conn


def table_names(path):
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    try:
        return sorted(
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'compliance%'"
            ).fetchall()
        )
    finally:
        conn.close()


def count_rows(path, table):
    if not path.exists():
        return 0
    conn = sqlite3.connect(path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def record(results, label, condition, detail=""):
    results.append((label, bool(condition), detail))


def base_payload(**overrides):
    payload = {
        "firm_id": "FIRM-002",
        "title": "Access control policy review",
        "review_type": "access_control_compliance",
        "question_presented": "Does the access control condition satisfy the governing policy?",
        "governing_requirement_type": "institutional_policy",
        "governing_requirement_id": "POL-2026-0001",
        "governing_requirement_label": "Access Control Policy",
        "source_type": "system_observation",
        "source_id": "SYSOBS-2026-000001",
        "source_label": "Permission posture observation",
        "scope_summary": "Firm-scoped access-control compliance review.",
        "priority": "high",
        "risk_level": "high",
        "review_owner": "Compliance Team",
        "authority_basis": "Authorized institutional compliance review.",
    }
    payload.update(overrides)
    return payload


class _TemplateTagGuard(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag.lower())

    def handle_startendtag(self, tag, attrs):
        self.tags.append(tag.lower())


def _route_and_ui_compatibility():
    app_module = importlib.import_module("app")
    flask_app = app_module.app
    rules = list(flask_app.url_map.iter_rules())
    review_rules = [rule for rule in rules if rule.rule.startswith("/compliance/reviews")]
    registry_rules = [rule for rule in rules if rule.endpoint == "compliance_review_registry"]
    detail_rules = [rule for rule in rules if rule.endpoint == "compliance_review_detail"]
    expected_methods = {"GET", "HEAD", "OPTIONS"}

    route_parts_present = bool(review_rules or registry_rules or detail_rules)
    if route_parts_present:
        route_ok = (
            len(registry_rules) == 1
            and len(detail_rules) == 1
            and registry_rules[0].rule == "/compliance/reviews"
            and detail_rules[0].rule == "/compliance/reviews/<compliance_review_id>"
            and set(registry_rules[0].methods) == expected_methods
            and set(detail_rules[0].methods) == expected_methods
            and len(review_rules) == 2
            and {(rule.endpoint, rule.rule) for rule in review_rules} == {
                (registry_rules[0].endpoint, registry_rules[0].rule),
                (detail_rules[0].endpoint, detail_rules[0].rule),
            }
            and all("POST" not in rule.methods for rule in review_rules)
        )
        forbidden_calls = (
            "create_compliance_review",
            "transition_compliance_review",
            "ensure_compliance_review_foundation",
            "db.create_all",
            "ext_db.create_all",
            "subprocess",
            "os.system",
            "log_change",
        )
        route_sources = "\n".join(
            inspect.getsource(flask_app.view_functions[endpoint])
            for endpoint in ("compliance_review_registry", "compliance_review_detail")
            if endpoint in flask_app.view_functions
        )
        route_ok = route_ok and all(
            not re.search(rf"(?<![A-Za-z0-9_]){re.escape(call)}\s*\(", route_sources)
            for call in forbidden_calls
        )
    else:
        route_ok = True

    registry_path = ROOT / "templates/compliance_reviews/registry.html"
    detail_path = ROOT / "templates/compliance_reviews/detail.html"
    template_presence = (registry_path.exists(), detail_path.exists())
    if any(template_presence):
        templates_ok = all(template_presence) and registry_path.is_file() and detail_path.is_file()
        sources = {}
        if templates_ok:
            try:
                for name, template_path in (
                    ("compliance_reviews/registry.html", registry_path),
                    ("compliance_reviews/detail.html", detail_path),
                ):
                    flask_app.jinja_env.get_template(name)
                    sources[name] = template_path.read_text(encoding="utf-8")
            except Exception:
                templates_ok = False
        if templates_ok:
            forbidden_tags = {"form", "input", "textarea", "select", "button", "script"}
            forbidden_fields = {
                "payload_hash",
                "idempotency_key",
                "approved_by",
                "approved_at",
            }
            mutation_terms = (
                "create", "transition", "acknowledge", "assign", "finding",
                "recommendation", "evidence_determination", "disposition",
                "approval", "reject", "defer", "closure", "reopen",
                "recurrence", "supersession", "routing", "remediation",
                "migration", "repair",
            )
            for source in sources.values():
                parser = _TemplateTagGuard()
                parser.feed(source)
                lowered = source.lower()
                templates_ok = templates_ok and not (set(parser.tags) & forbidden_tags)
                templates_ok = templates_ok and "|safe" not in re.sub(r"\s+", "", lowered)
                templates_ok = templates_ok and not any(field in lowered for field in forbidden_fields)
                templates_ok = templates_ok and not re.search(
                    r"\b(?:review|event|relationship)\s*(?:\.\s*id\b|\[\s*['\"]id['\"]\s*\])",
                    source,
                )
                url_endpoints = re.findall(r"url_for\(\s*['\"]([^'\"]+)", source)
                templates_ok = templates_ok and not any(
                    endpoint.startswith("compliance_review_")
                    and any(term in endpoint.lower() for term in mutation_terms)
                    for endpoint in url_endpoints
                )
            registry_endpoints = re.findall(
                r"url_for\(\s*['\"]([^'\"]+)",
                sources["compliance_reviews/registry.html"],
            )
            templates_ok = templates_ok and set(registry_endpoints) <= {"compliance_review_detail"}
    else:
        templates_ok = True

    workspace_source = read("templates/ios_workspaces/compliance.html")
    registry_link_present = "Compliance Review Registry" in workspace_source
    if registry_link_present:
        parser = _TemplateTagGuard()
        parser.feed(workspace_source)
        workspace_endpoints = re.findall(
            r"url_for\(\s*['\"]([^'\"]+)", workspace_source
        )
        mutation_controls = {"form", "input", "textarea", "select", "button"}
        workspace_ok = (
            "compliance_review_registry" in workspace_endpoints
            and not (set(parser.tags) & mutation_controls)
            and not any(
                endpoint.startswith("compliance_review_")
                and endpoint != "compliance_review_registry"
                for endpoint in workspace_endpoints
            )
        )
    else:
        workspace_ok = True

    complete_h_surface = route_parts_present and all(template_presence) and registry_link_present
    foundation_only_surface = not route_parts_present and not any(template_presence) and not registry_link_present
    consistent_surface = complete_h_surface or foundation_only_surface
    return route_ok and consistent_surface, templates_ok and workspace_ok and consistent_surface


def source_guard_results():
    service = read("services/services_compliance_reviews.py")
    model = read("models/models_compliance_reviews.py")
    combined = f"{model}\n{service}"
    destination = read("services/services_system_observation_destinations.py")
    route_ok, ui_ok = _route_and_ui_compatibility()
    return {
        "reserved_workflows": all(
            token in combined
            for token in [
                "reserved_workflow_not_active",
                "record_disposition",
                "approve_disposition",
                "supersede",
            ]
        ),
        "no_compliance_destination_activation": (
            "No authoritative routable Compliance destination registry is available" in destination
            and '"compliance"' not in re.search(r"SUPPORTED_DESTINATIONS\s*=\s*\{([^}]+)\}", destination, re.S).group(1)
        ),
        "readonly_route_compatibility": route_ok,
        "readonly_template_and_workspace_compatibility": ui_ok,
    }


def changed_files_ok():
    code, stdout, stderr = run_git("diff", "--name-only")
    if code != 0:
        raise AssertionError(stderr or stdout)
    modified = {line.strip() for line in stdout.splitlines() if line.strip()}
    code, stdout, stderr = run_git("ls-files", "--others", "--exclude-standard")
    if code != 0:
        raise AssertionError(stderr or stdout)
    untracked = {line.strip() for line in stdout.splitlines() if line.strip()}
    code, staged_stdout, stderr = run_git("diff", "--cached", "--name-only")
    if code != 0:
        raise AssertionError(stderr or staged_stdout)
    staged = {line.strip() for line in staged_stdout.splitlines() if line.strip()}
    unexpected = (
        (modified - ALLOWED_MODIFIED_FILES)
        | (untracked - ALLOWED_UNTRACKED_FILES)
        | staged
    )
    return modified | untracked, unexpected


def main():
    results = []
    if TEMP_DB.exists():
        TEMP_DB.unlink()

    normal_db = ROOT / "trustee_app.db"
    normal_before_tables = table_names(normal_db)
    normal_before_count = sum(count_rows(normal_db, table) for table in normal_before_tables)

    migration_result = ensure_compliance_review_foundation()
    record(results, "migration returns verified", migration_result.get("ok") and migration_result.get("status") == "verified")
    second_migration = ensure_compliance_review_foundation()
    record(results, "migration is idempotent", second_migration.get("ok"))

    conn = connect()
    try:
        tables = table_names(TEMP_DB)
        record(results, "expected compliance tables exist", EXPECTED_TABLES.issubset(set(tables)), ", ".join(tables))
        index_names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE '%compliance%'"
            ).fetchall()
        }
        record(results, "firm/source/event indexes exist", {
            "idx_compliance_reviews_firm_status",
            "idx_compliance_reviews_source",
            "idx_compliance_review_events_review",
        }.issubset(index_names))
    finally:
        conn.close()

    first = create_compliance_review(
        payload=base_payload(),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-create-1",
    )
    record(results, "create compliance review", first.get("ok") and first.get("status") == "created", first.get("status"))
    review_id = first.get("review", {}).get("compliance_review_id")
    record(results, "public ID is canonical", bool(review_id and re.fullmatch(r"CMP-\d{4}-\d{4}", review_id)), str(review_id))
    record(results, "initial event created", first.get("event", {}).get("event_type") == "compliance_review_created")

    replay = create_compliance_review(
        payload=base_payload(),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-create-1",
    )
    record(results, "create idempotent replay", replay.get("ok") and replay.get("status") == "idempotent_replay")
    conflict = create_compliance_review(
        payload=base_payload(title="Changed title"),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-create-1",
    )
    record(results, "create idempotency conflict", not conflict.get("ok") and conflict.get("status") == "conflict")
    duplicate = create_compliance_review(
        payload=base_payload(source_label="Same source duplicate"),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-create-duplicate",
    )
    record(results, "duplicate active review blocked", not duplicate.get("ok") and duplicate.get("status") == "duplicate_active_review")

    second = create_compliance_review(
        payload=base_payload(
            title="Archive custody review",
            review_type="archive_and_continuity_compliance",
            governing_requirement_id="POL-2026-0002",
            source_type="archive_record",
            source_id="CCL-2026",
        ),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-create-2",
    )
    record(results, "second public ID increments", second.get("ok") and second.get("review", {}).get("compliance_review_id", "").endswith("-0002"))

    cross_firm = create_compliance_review(
        payload=base_payload(firm_id="FIRM-002", source_id="SYSOBS-2026-000003"),
        actor_context=OTHER_FIRM_ACTOR,
        idempotency_key="17qg-cross-firm",
    )
    record(results, "cross-firm create denied", not cross_firm.get("ok") and "firm_scope_denied" in cross_firm.get("message", ""))
    bad_scope = create_compliance_review(
        payload=base_payload(trust_id="TRUST-001", matter_id="MAT-000001", source_id="SYSOBS-2026-000004"),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-bad-scope",
    )
    record(results, "ambiguous matter/trust scope blocked", not bad_scope.get("ok") and "trust_matter_scope" in bad_scope.get("message", ""))
    prohibited = create_compliance_review(
        payload=base_payload(disposition="compliant", source_id="SYSOBS-2026-000005"),
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-prohibited",
    )
    record(results, "create cannot smuggle disposition", not prohibited.get("ok") and "prohibited_create_fields" in prohibited.get("message", ""))

    opened = transition_compliance_review(
        compliance_review_id=review_id,
        action="open",
        expected_version=1,
        reason="Review authorized for institutional assessment.",
        summary="Open the review for controlled compliance assessment.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-open",
    )
    record(results, "draft opens", opened.get("ok") and opened.get("review", {}).get("status") == "opened", opened.get("status"))
    opened_replay = transition_compliance_review(
        compliance_review_id=review_id,
        action="open",
        expected_version=1,
        reason="Review authorized for institutional assessment.",
        summary="Open the review for controlled compliance assessment.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-open",
    )
    record(results, "transition idempotent replay", opened_replay.get("ok") and opened_replay.get("status") == "idempotent_replay")
    stale = transition_compliance_review(
        compliance_review_id=review_id,
        action="start_review",
        expected_version=1,
        reason="Start review.",
        summary="Begin review.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-stale",
    )
    record(results, "stale transition blocked", not stale.get("ok") and stale.get("status") == "stale_version")
    started = transition_compliance_review(
        compliance_review_id=review_id,
        action="start_review",
        expected_version=2,
        reason="Reviewer is ready to assess evidence.",
        summary="Begin active compliance review.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-start",
    )
    record(results, "opened starts under review", started.get("ok") and started.get("review", {}).get("status") == "under_review")
    requested = transition_compliance_review(
        compliance_review_id=review_id,
        action="request_information",
        expected_version=3,
        reason="More evidence is needed before determination.",
        summary="Request source documentation from the owning workspace.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-request-info",
        related_record_type="Matter",
        related_record_id="MAT-000001",
    )
    record(results, "information request transition", requested.get("ok") and requested.get("review", {}).get("status") == "awaiting_information")
    resumed = transition_compliance_review(
        compliance_review_id=review_id,
        action="resume_review",
        expected_version=4,
        reason="Requested information has been received.",
        summary="Resume review after evidence receipt.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-resume",
    )
    record(results, "resume transition", resumed.get("ok") and resumed.get("review", {}).get("status") == "under_review")
    ready = transition_compliance_review(
        compliance_review_id=review_id,
        action="mark_ready_for_disposition",
        expected_version=5,
        reason="Analysis is complete enough for later disposition workflow.",
        summary="Mark ready for future disposition workflow.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-ready",
    )
    record(results, "ready-for-disposition transition", ready.get("ok") and ready.get("review", {}).get("status") == "ready_for_disposition")

    reserved = transition_compliance_review(
        compliance_review_id=review_id,
        action="record_disposition",
        expected_version=6,
        reason="Reserved action attempt.",
        summary="Should not execute.",
        actor_context=AUTHORIZED_ACTOR,
        idempotency_key="17qg-reserved",
        disposition="compliant",
    )
    record(results, "future disposition workflow blocked", not reserved.get("ok") and reserved.get("status") == "reserved_workflow_not_active")
    other_read = get_compliance_review(review_id, scope={"firm_id": "FIRM-003"})
    record(results, "cross-firm read hidden", other_read is None)
    public_read = get_compliance_review_by_public_id(review_id, scope={"firm_id": "FIRM-002"})
    internal_read = get_compliance_review_by_id(first["review"]["id"], scope={"firm_id": "FIRM-002"})
    record(results, "read services return scoped review", public_read and internal_read and public_read["compliance_review_id"] == internal_read["compliance_review_id"])
    events = list_compliance_review_events(review_id, scope={"firm_id": "FIRM-002"})
    record(results, "event sequence append-only", [event["event_sequence"] for event in events] == list(range(1, len(events) + 1)) and len(events) == 6)

    source_guards = source_guard_results()
    for label, value in source_guards.items():
        record(results, label.replace("_", " "), value)
    destination = verify_destination_record("compliance", review_id, actor_context=AUTHORIZED_ACTOR)
    record(results, "compliance destination remains unavailable", destination.get("status") == "destination_unavailable")

    changed, unexpected = changed_files_ok()
    record(results, "changed files bounded", not unexpected, ", ".join(sorted(changed)))
    normal_after_tables = table_names(normal_db)
    normal_after_count = sum(count_rows(normal_db, table) for table in normal_after_tables)
    record(
        results,
        "normal database preserved",
        normal_after_tables == normal_before_tables and normal_after_count == normal_before_count,
        f"{normal_before_tables} -> {normal_after_tables}",
    )

    print("POST-V2-17Q-G Compliance Review Foundation Audit")
    print(f"Temp DB: {TEMP_DB}")
    print(f"Changed files: {', '.join(sorted(changed))}")
    print()
    for label, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        suffix = f" | {detail}" if detail else ""
        print(f"{status} - {label}{suffix}")

    failures = [label for label, passed, _detail in results if not passed]
    if failures:
        print()
        print("RESULT: FAIL")
        print()
        print("POST-V2-17Q-G MODE")
        print("compliance_review_data_model_lifecycle_and_event_foundation")
        print()
        print("POST-V2-17Q-G RESULT")
        print("FAIL - The Compliance Review foundation is incomplete or improperly exposed.")
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)
    print()
    print("RESULT: PASS")
    print()
    print("POST-V2-17Q-G MODE")
    print("compliance_review_data_model_lifecycle_and_event_foundation")
    print()
    print("POST-V2-17Q-G RESULT")
    print(
        "PASS - Compliance Review now has a durable numbered, scope-aware, versioned data model "
        "with explicit lifecycle controls, append-only event history, duplicate and idempotency "
        "protection, and atomic service operations, while disposition, approval, closure, remediation, "
        "verifier, mutation UI, and System Observation routing capabilities remain unavailable; only "
        "the compatible later GET-only registry and detail interface may be present."
    )


if __name__ == "__main__":
    main()
