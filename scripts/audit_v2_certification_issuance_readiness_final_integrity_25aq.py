from __future__ import annotations

import hashlib
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "v2_certification_issuance_readiness_final_integrity_25aq.md"
STARTING_HEAD = "a908110e361b5211a94e4a84283f754699b8b969"
FROZEN_SOURCE = "a1f63da1096bc6c261db2fd8a894f660ec919c2a"
MANIFEST_SHA = "C7B25B9C09120AA77E1A684B828C45A06DB6339600AF5A4BEC16244626F2EFD8"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
ALLOWED_CHANGED = {
    "docs/v2_certification_issuance_readiness_final_integrity_25aq.md",
    "scripts/audit_v2_certification_issuance_readiness_final_integrity_25aq.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
    "scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "docs/v2_certification_issuance_25ar.md",
    "docs/v2_certification_issuance_25ar.json",
    "scripts/audit_v2_certification_issuance_25ar.py",
}
PRODUCTION_PREFIXES = ("app.py", "pdf_utils.py", "templates/", "services/", "models/", "migrations/", "database/")


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def check(label: str, condition: bool, detail: object = "") -> bool:
    print(("PASS" if condition else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return condition


def changed_paths() -> set[str]:
    paths: set[str] = set()
    for line in git("status", "--porcelain=v1").splitlines():
        if not line:
            continue
        path = line[2:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip('"').replace("\\", "/")
        paths.add(path)
    return paths


def staged_paths() -> set[str]:
    return {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}


def active_counts() -> dict[str, object]:
    with sqlite3.connect(f"file:{(ROOT / 'trustee_app.db').as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table'")]
        return {
            "audit_log": cur.execute("select count(*) from audit_log").fetchone()[0],
            "transfers": cur.execute("select count(*) from transfers").fetchone()[0],
            "schema_version": cur.execute("pragma schema_version").fetchone()[0],
            "table_count": len(tables),
            "compliance_objects": [t for t in tables if "compliance_review" in t.lower()],
            "system_observation_objects": [t for t in tables if "system_observation" in t.lower()],
        }


def exactly_one(text: str, phrase: str) -> bool:
    return text.count(phrase) == 1


def main() -> int:
    failures = 0
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    changed = changed_paths()
    staged = staged_paths()
    unexpected = sorted((changed | staged) - ALLOWED_CHANGED)
    production = sorted(
        path for path in changed | staged if path in {"app.py", "pdf_utils.py"} or path.startswith(PRODUCTION_PREFIXES)
    )
    counts = active_counts()
    manifest_hash = sha256(ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap_manifest.json")
    before_db = sha256(ROOT / "trustee_app.db")
    before_policy = sha256(ROOT / "data" / "export_policy.json")

    nonclaims = [
        "Certification is technical and institutional-process certification, not legal validation.",
        "Certification does not establish enforceability of any trust instrument.",
        "Certification does not establish tax compliance.",
        "Certification does not establish regulatory approval.",
        "Certification does not activate inactive modules.",
        "Certification does not certify hosted production deployment.",
        "Certification does not certify disaster-recovery execution.",
        "Certification does not erase accepted nonblocking friction.",
        "Certification does not replace operator judgment or professional review.",
        "Certification applies only to the exact frozen source and evidence commits.",
    ]

    checks = [
        ("final-integrity report exists", REPORT.exists(), REPORT.relative_to(ROOT).as_posix()),
        ("starting HEAD is a908110", STARTING_HEAD in text, STARTING_HEAD),
        ("frozen source commit is exact", FROZEN_SOURCE in text, FROZEN_SOURCE),
        ("evidence-freeze commit is exact", STARTING_HEAD in text, STARTING_HEAD),
        ("manifest SHA is exact", MANIFEST_SHA in text and manifest_hash == MANIFEST_SHA, manifest_hash),
        ("builder --check result is present", "Builder check: `PASS`" in text, "builder"),
        ("freeze audit result is present", "Freeze audit: `PASS`" in text, "freeze audit"),
        ("frozen evidence hash result is present", "FROZEN_EVIDENCE_HASHES_MATCH=True" in text, "hashes"),
        ("Git blob hash result is present", "FROZEN_GIT_BLOBS_MATCH=True" in text, "blobs"),
        ("missing frozen file count is zero", "Missing frozen files: `0`" in text, "missing"),
        ("evidence drift count is zero", "Evidence-drift count: `0`" in text, "drift"),
        ("commit-chain result is present", "FROZEN_SOURCE_COMMIT_VALID=True" in text and "EVIDENCE_FREEZE_COMMIT_VALID=True" in text, "chain"),
        ("repository integrity result is present", "REPOSITORY_INTEGRITY_PASS=True" in text, "repo"),
        ("full authoritative audit result is present", "ALL_AUTHORITATIVE_AUDITS_PASS=True" in text, "audits"),
        ("active DB SHA is exact", DB_SHA in text and before_db == DB_SHA, before_db),
        ("audit count 569 is present", counts["audit_log"] == 569 and "Audit-log count: `569`" in text, counts),
        ("transfer count 14 is present", counts["transfers"] == 14 and "Transfer count: `14`" in text, counts),
        ("schema version 404 is present", counts["schema_version"] == 404 and "Schema version: `404`" in text, counts),
        ("table count 132 is present", counts["table_count"] == 132 and "Table count: `132`" in text, counts),
        ("policy SHA is exact", POLICY_SHA in text and before_policy == POLICY_SHA, before_policy),
        ("policy size 123 is present", "Policy size: `123`" in text, "123"),
        ("critical runtime result is present", "Critical runtime result: `PASS`" in text, "runtime"),
        ("authorization result is present", "AUTHORIZATION_FINAL_PASS=True" in text, "auth"),
        ("firm-scope result is present", "FIRM_SCOPE_FINAL_PASS=True" in text, "firm"),
        ("reports result is present", "REPORTS_FINAL_PASS=True" in text, "reports"),
        ("governance result is present", "GOVERNANCE_FINAL_PASS=True" in text, "governance"),
        ("archive/continuity result is present", "ARCHIVE_CONTINUITY_FINAL_PASS=True" in text, "archive"),
        ("recovery-safety result is present", "RECOVERY_SAFETY_FINAL_PASS=True" in text, "recovery"),
        ("Compliance inactive-state nonclaim exists", "Compliance state: `ACCEPTABLE_INACTIVE_STATE`" in text, "Compliance"),
        ("System Observation inactive-state nonclaim exists", "System Observation state: `ACCEPTABLE_INACTIVE_STATE`" in text, "System Observation"),
        ("deployment nonclaims are present", "DEPLOYMENT_NONCLAIMS_PRESERVED=True" in text, "deployment"),
        ("certification scope is present", "## 15. Proposed Certification Scope" in text and FROZEN_SOURCE in text, "scope"),
        ("certification limitations are present", "## 16. Proposed Certification Limitations" in text and "Nonblocking preview navigation friction remains accepted." in text, "limitations"),
        ("all ten certification nonclaims are present", all(n in text for n in nonclaims), "nonclaims"),
        ("issuance-precondition matrix exists", "| Precondition | Evidence | Result | Blocking Effect |" in text, "matrix"),
        ("open blockers count is present", "Open blockers: `0`" in text, "blockers"),
        ("evidence gaps count is present", "Evidence gaps: `0`" in text, "gaps"),
        ("exactly one issuance-readiness decision exists", exactly_one(text, "Decision: `CERTIFICATION_ISSUANCE_READY`"), "decision"),
        ("conditions before issuance exist", "Explicit authorization to execute the separate certification-issuance phase" in text, "conditions"),
        ("exactly one next phase exists", exactly_one(text, "Recommended next phase: `Step 25AR - V2 Certification Issuance`"), "next"),
        ("no certification is claimed", "No actual certification is issued here." in text and "Step 25AQ is the final readiness gate" in text, "nonissuance"),
        ("no tag is claimed", "does not create a certification tag" in text, "tag"),
        ("no merge is claimed", "does not merge any branch" in text, "merge"),
        ("no activation is claimed", "activation is not claimed" in text and "must not imply active System Observation persistence" in text, "activation"),
        ("no machine-specific absolute path appears", not re.search(r"[A-Za-z]:\\|C:/Users/|/Users/|/home/|/tmp/", text), "portable"),
        ("no permanent invented defect ID appears", not re.search(r"\bD-\d{3,}\b|\bDEFECT-\d+\b|\bBUG-\d+\b", text), "defect ids"),
        ("no production code is modified or staged", not production, production),
        ("repository changes limited to Step 25AQ evidence/guard updates", not unexpected, unexpected),
    ]

    after_db = sha256(ROOT / "trustee_app.db")
    after_policy = sha256(ROOT / "data" / "export_policy.json")
    checks.append(("audit does not mutate state", before_db == after_db == DB_SHA and before_policy == after_policy == POLICY_SHA, "state"))

    for label, condition, detail in checks:
        if not check(label, bool(condition), detail):
            failures += 1

    print("STEP 25AQ V2 CERTIFICATION ISSUANCE READINESS FINAL INTEGRITY AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
