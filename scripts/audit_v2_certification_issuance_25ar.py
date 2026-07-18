from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "docs" / "v2_certification_issuance_25ar.md"
JSON_RECORD = ROOT / "docs" / "v2_certification_issuance_25ar.json"
MANIFEST = ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap_manifest.json"
TAG_NAME = "v2-certified-baseline-2026-07-18"
CERTIFICATION_ID = "TRUSTEE-APP-V2-CERT-2026-07-18"
CERTIFICATION_DATE = "2026-07-18"
BRANCH = "post-v2-planning"
FROZEN_SOURCE = "a1f63da1096bc6c261db2fd8a894f660ec919c2a"
EVIDENCE_FREEZE = "a908110e361b5211a94e4a84283f754699b8b969"
ISSUANCE_READINESS = "774775b34f26627223a7308f6e476b99405697e3"
FINAL_INTEGRITY = "dda6f96f2b4e4a6400dcd656cf9d149efbca5ff7"
MANIFEST_SHA = "C7B25B9C09120AA77E1A684B828C45A06DB6339600AF5A4BEC16244626F2EFD8"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
NEXT_PHASE = "Step 25AS - Certified Baseline Publication and Branch Disposition Audit"

NONCLAIMS = [
    "This is a technical and institutional-process certification, not legal validation.",
    "It does not establish enforceability of any trust instrument.",
    "It does not establish tax compliance.",
    "It does not establish regulatory approval.",
    "It does not activate intentionally inactive modules.",
    "It does not certify hosted production deployment.",
    "It does not certify disaster-recovery execution.",
    "It does not erase accepted nonblocking operator friction.",
    "It does not replace operator judgment or professional review.",
    "It applies only to the exact identified source, evidence, readiness, certification commit, and annotated tag.",
]

ALLOWED_CHANGED = {
    "docs/v2_certification_issuance_25ar.md",
    "docs/v2_certification_issuance_25ar.json",
    "scripts/audit_v2_certification_issuance_25ar.py",
    "docs/certified_baseline_publication_branch_disposition_25as_r1.md",
    "scripts/audit_certified_baseline_publication_branch_disposition_25as_r1.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
    "scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_v2_certification_issuance_readiness_final_integrity_25aq.py",
    "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
}
PRODUCTION_PREFIXES = ("templates/", "services/", "models/", "migrations/", "database/")
PRODUCTION_FILES = {"app.py", "pdf_utils.py"}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


def normalized_status_paths() -> set[str]:
    paths: set[str] = set()
    for line in git("status", "--porcelain=v1").stdout.splitlines():
        if not line:
            continue
        path = line[2:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip('"').replace("\\", "/")
        paths.add(path)
    return paths


def staged_paths() -> set[str]:
    return {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").stdout.splitlines() if line}


def active_snapshot() -> dict[str, object]:
    db = ROOT / "trustee_app.db"
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table' order by name")]

        def count(table: str) -> int | str:
            try:
                return cur.execute(f"select count(*) from {table}").fetchone()[0]
            except sqlite3.Error:
                return "MISSING"

        objects = [
            row[0]
            for row in cur.execute(
                "select name from sqlite_master where type='table' "
                "and (lower(name) like '%compliance%' or lower(name) like '%system_observation%') order by name"
            )
        ]
        return {
            "sha256": sha256(db),
            "size_bytes": db.stat().st_size,
            "mtime_ns": db.stat().st_mtime_ns,
            "schema_version": cur.execute("pragma schema_version").fetchone()[0],
            "table_count": len(tables),
            "audit_log_count": count("audit_log"),
            "transfer_count": count("transfers"),
            "trust_count": count("trusts"),
            "matter_count": count("matters"),
            "user_count": count("app_users"),
            "certificate_count": count("certificates"),
            "compliance_system_objects": objects,
        }


def load_records() -> tuple[str, dict[str, object]]:
    text = MARKDOWN.read_text(encoding="utf-8") if MARKDOWN.exists() else ""
    data = json.loads(JSON_RECORD.read_text(encoding="utf-8")) if JSON_RECORD.exists() else {}
    return text, data


def pre_tag_checks() -> int:
    failures = 0
    before_db = sha256(ROOT / "trustee_app.db")
    before_policy = sha256(ROOT / "data" / "export_policy.json")
    text, data = load_records()
    changed = normalized_status_paths()
    staged = staged_paths()
    production_changed = sorted(
        p for p in changed | staged if p in PRODUCTION_FILES or p.startswith(PRODUCTION_PREFIXES)
    )
    unexpected = sorted((changed | staged) - ALLOWED_CHANGED)
    active = active_snapshot()
    aq_text = (ROOT / "docs" / "v2_certification_issuance_readiness_final_integrity_25aq.md").read_text(
        encoding="utf-8"
    )

    checks = [
        ("Markdown certification record exists", MARKDOWN.exists(), MARKDOWN.relative_to(ROOT).as_posix()),
        ("JSON certification record exists", JSON_RECORD.exists(), JSON_RECORD.relative_to(ROOT).as_posix()),
        ("Certification ID is exact", data.get("certification_id") == CERTIFICATION_ID and CERTIFICATION_ID in text, data.get("certification_id")),
        ("Certification date is exact", data.get("certification_date") == CERTIFICATION_DATE and CERTIFICATION_DATE in text, data.get("certification_date")),
        ("Decision is exactly V2_CERTIFIED", data.get("decision") == "V2_CERTIFIED" and text.count("V2_CERTIFIED") == 1, data.get("decision")),
        ("Frozen source commit is exact", data.get("frozen_source_commit") == FROZEN_SOURCE and FROZEN_SOURCE in text, data.get("frozen_source_commit")),
        ("Evidence-freeze commit is exact", data.get("evidence_freeze_commit") == EVIDENCE_FREEZE and EVIDENCE_FREEZE in text, data.get("evidence_freeze_commit")),
        ("Issuance-readiness commit is exact", data.get("issuance_readiness_commit") == ISSUANCE_READINESS and ISSUANCE_READINESS in text, data.get("issuance_readiness_commit")),
        ("Final-integrity commit is exact", data.get("final_integrity_commit") == FINAL_INTEGRITY and FINAL_INTEGRITY in text, data.get("final_integrity_commit")),
        ("Manifest SHA is exact", data.get("evidence_manifest", {}).get("sha256") == MANIFEST_SHA and sha256(MANIFEST) == MANIFEST_SHA, sha256(MANIFEST) if MANIFEST.exists() else "missing"),
        ("Source branch is exact", data.get("source_branch") == BRANCH and git("branch", "--show-current").stdout.strip() == BRANCH, data.get("source_branch")),
        ("Intended tag name is exact", data.get("certification_tag") == TAG_NAME and TAG_NAME in text, data.get("certification_tag")),
        ("Open blockers are zero", data.get("open_blockers") == 0 and "Open blockers" not in text or data.get("open_blockers") == 0, data.get("open_blockers")),
        ("Evidence gaps are zero", data.get("evidence_gaps") == 0, data.get("evidence_gaps")),
        ("Active DB SHA is exact", data.get("active_db_reference", {}).get("sha256") == DB_SHA and active["sha256"] == DB_SHA, active["sha256"]),
        ("Audit count 569 is present", data.get("active_db_reference", {}).get("audit_log_count") == 569 and active["audit_log_count"] == 569, active["audit_log_count"]),
        ("Transfers 14 is present", data.get("active_db_reference", {}).get("transfer_count") == 14 and active["transfer_count"] == 14, active["transfer_count"]),
        ("Schema 404 is present", data.get("active_db_reference", {}).get("schema_version") == 404 and active["schema_version"] == 404, active["schema_version"]),
        ("Table count 132 is present", data.get("active_db_reference", {}).get("table_count") == 132 and active["table_count"] == 132, active["table_count"]),
        ("Policy SHA is exact", data.get("policy_reference", {}).get("sha256") == POLICY_SHA and sha256(ROOT / "data" / "export_policy.json") == POLICY_SHA, POLICY_SHA),
        ("Certified-capability section exists", len(data.get("certified_capabilities", [])) >= 17 and "## 5. Certified Capabilities" in text, len(data.get("certified_capabilities", []))),
        ("Accepted limitations exist", len(data.get("accepted_limitations", [])) >= 8 and "## 6. Accepted Limitations" in text, len(data.get("accepted_limitations", []))),
        ("Compliance inactive state is explicit", "Compliance is not operationally active." in text, "Compliance"),
        ("System Observation inactive state is explicit", "System Observation persistence is not operationally active." in text, "System Observation"),
        ("Deployment exclusions exist", len(data.get("deployment_exclusions", [])) >= 21 and "## 8. Deployment Exclusions" in text, len(data.get("deployment_exclusions", []))),
        ("All ten nonclaims exist", data.get("nonclaims") == NONCLAIMS and all(item in text for item in NONCLAIMS), len(data.get("nonclaims", []))),
        ("Certification validity boundary exists", "Certification remains attributable only to the exact annotated tag" in text, "boundary"),
        ("Issuance statement requires annotated tag", "Certification is formally issued upon creation and verification of the annotated tag" in text, "annotated tag"),
        ("No lightweight tag is authorized", "No lightweight tag is authorized." in text, "lightweight excluded"),
        ("No merge is claimed", "no merge" in text and "merge automatically" not in text.lower(), "merge"),
        ("No deployment is claimed", "no deployment" in text and "Deployment is not represented as complete" in text, "deployment"),
        ("No activation is claimed", "no activation" in text and "not operationally active" in text, "activation"),
        ("No machine-specific path appears", not re.search(r"[A-Za-z]:\\|C:/Users/|/Users/|/home/|/tmp/", text + json.dumps(data)), "portable"),
        ("No permanent invented defect ID appears", not re.search(r"\b(?:DEFECT|BUG|ISSUE)-\d+\b", text), "defect ids"),
        ("Exactly one next phase exists", data.get("next_phase") == NEXT_PHASE and text.count(NEXT_PHASE) == 1, data.get("next_phase")),
        ("JSON parses successfully", bool(data), "json"),
        ("Markdown and JSON identities agree", all(value in text for value in [CERTIFICATION_ID, CERTIFICATION_DATE, TAG_NAME]), "identity"),
        ("Step 25AP manifest remains unchanged", sha256(MANIFEST) == MANIFEST_SHA, sha256(MANIFEST) if MANIFEST.exists() else "missing"),
        ("Step 25AQ decision remains CERTIFICATION_ISSUANCE_READY", "CERTIFICATION_ISSUANCE_READY" in aq_text, "25AQ"),
        ("No production code is modified or staged", not production_changed, production_changed),
        ("Repository changes limited to Step 25AR evidence/guard updates", not unexpected, unexpected),
    ]

    after_db = sha256(ROOT / "trustee_app.db")
    after_policy = sha256(ROOT / "data" / "export_policy.json")
    checks.append(("Audit does not mutate active state", before_db == after_db == DB_SHA and before_policy == after_policy == POLICY_SHA, "state"))

    for label, ok, detail in checks:
        if not record(label, bool(ok), detail):
            failures += 1

    print("STEP 25AR V2 CERTIFICATION ISSUANCE AUDIT")
    print("RESULT:", "PASS_PRE_TAG" if failures == 0 else "FAIL")
    return failures


def verify_tag() -> int:
    failures = 0
    text, _data = load_records()
    tag_type = git("cat-file", "-t", TAG_NAME, check=False)
    tag_object = git("rev-parse", TAG_NAME, check=False)
    peeled = git("rev-parse", f"{TAG_NAME}^{{}}", check=False)
    tag_body = git("cat-file", "-p", TAG_NAME, check=False)
    head = git("rev-parse", "HEAD").stdout.strip()
    tree_paths = [
        "docs/v2_certification_issuance_25ar.md",
        "docs/v2_certification_issuance_25ar.json",
        "scripts/audit_v2_certification_issuance_25ar.py",
    ]
    contains_paths = []
    if peeled.returncode == 0:
        for path in tree_paths:
            contains_paths.append(git("cat-file", "-e", f"{peeled.stdout.strip()}^{{tree}}:{path}", check=False).returncode == 0)

    checks = [
        ("tag exists locally", tag_type.returncode == 0, TAG_NAME),
        ("tag is annotated", tag_type.stdout.strip() == "tag", tag_type.stdout.strip()),
        ("tag name is exact", TAG_NAME in git("tag", "--list", TAG_NAME).stdout.splitlines(), TAG_NAME),
        ("tag message contains certification ID", CERTIFICATION_ID in tag_body.stdout, CERTIFICATION_ID),
        ("tag message contains frozen source commit", FROZEN_SOURCE in tag_body.stdout, FROZEN_SOURCE),
        ("tag message contains evidence-freeze commit", EVIDENCE_FREEZE in tag_body.stdout, EVIDENCE_FREEZE),
        ("tag message contains manifest SHA", MANIFEST_SHA in tag_body.stdout, MANIFEST_SHA),
        ("tag peels to the Step 25AR certification issuance commit", peeled.returncode == 0 and peeled.stdout.strip() == head, peeled.stdout.strip() if peeled.returncode == 0 else peeled.stderr.strip()),
        ("peeled commit contains the certification record and audit", all(contains_paths), contains_paths),
        ("tag does not point to a prior readiness or freeze commit", peeled.returncode == 0 and peeled.stdout.strip() not in {FROZEN_SOURCE, EVIDENCE_FREEZE, ISSUANCE_READINESS, FINAL_INTEGRITY}, peeled.stdout.strip() if peeled.returncode == 0 else ""),
        ("Markdown still requires annotated tag", "annotated tag" in text and "No lightweight tag is authorized." in text, "tag boundary"),
        ("tag object SHA is present", tag_object.returncode == 0 and bool(tag_object.stdout.strip()), tag_object.stdout.strip() if tag_object.returncode == 0 else ""),
    ]
    for label, ok, detail in checks:
        if not record(label, bool(ok), detail):
            failures += 1
    print("STEP 25AR V2 CERTIFICATION TAG AUDIT")
    print("RESULT:", "PASS_TAG" if failures == 0 else "FAIL")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-tag", action="store_true")
    args = parser.parse_args()
    failures = verify_tag() if args.verify_tag else pre_tag_checks()
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
