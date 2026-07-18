from __future__ import annotations

import hashlib
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "v2_certification_candidate_readiness_25ao.md"
STARTING_HEAD = "f70a89f0c9592fb48064f481a34d49ae3de5d8a1"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
ALLOWED_CHANGED = {
    "docs/v2_certification_candidate_readiness_25ao.md",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "docs/v2_certification_candidate_evidence_freeze_25ap.md",
    "docs/v2_certification_candidate_evidence_freeze_25ap_manifest.json",
    "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",
    "docs/v2_certification_issuance_readiness_final_integrity_25aq.md",
    "scripts/audit_v2_certification_issuance_readiness_final_integrity_25aq.py",
}
PRODUCTION_PREFIXES = (
    "app.py",
    "pdf_utils.py",
    "templates/",
    "services/",
    "models/",
    "migrations/",
    "database/",
)


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
    status = git("status", "--porcelain=v1")
    paths: set[str] = set()
    for line in status.splitlines():
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
    db = ROOT / "trustee_app.db"
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table'")]
        return {
            "audit_log": cur.execute("select count(*) from audit_log").fetchone()[0],
            "transfers": cur.execute("select count(*) from transfers").fetchone()[0],
            "compliance_objects": [
                table for table in tables if "compliance" in table.lower()
            ],
            "system_observation_objects": [
                table
                for table in tables
                if "system_observation" in table.lower() or "observation" in table.lower()
            ],
        }


def exactly_one(text: str, pattern: str) -> bool:
    return len(re.findall(pattern, text)) == 1


def has_all(text: str, terms: list[str]) -> bool:
    return all(term in text for term in terms)


def main() -> int:
    failures = 0
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    changed = changed_paths()
    staged = staged_paths()
    unauthorized = sorted((changed | staged) - ALLOWED_CHANGED)
    production_changed = sorted(
        path
        for path in changed | staged
        if path.startswith(PRODUCTION_PREFIXES) or path in {"app.py", "pdf_utils.py"}
    )
    counts = active_counts()

    checks = [
        ("readiness report exists", REPORT.exists(), REPORT.relative_to(ROOT).as_posix()),
        ("starting HEAD is f70a89f", STARTING_HEAD in text, STARTING_HEAD),
        ("active DB SHA present", DB_SHA in text, DB_SHA),
        ("audit count 569 present", "audit-log count: `569`" in text or "audit-log count: `569`" in text, "569"),
        ("transfer count 14 present", "transfer count: `14`" in text, "14"),
        ("policy SHA present", POLICY_SHA in text, POLICY_SHA),
        (
            "authoritative evidence set present",
            has_all(
                text,
                [
                    "## 3. Authoritative Evidence Set",
                    "docs/post_v2_gap_closure_prioritization_25ak.md",
                    "docs/core_product_manual_operator_acceptance_25al.md",
                    "docs/operator_friction_acceptance_closure_25an.md",
                ],
            ),
            "evidence set",
        ),
        ("readiness inventory exists", "## 5. Readiness Inventory" in text and "Inventory counts: total `31`" in text, "inventory"),
        ("gate matrix exists", "## 6. Gate Matrix" in text and "Gate count: `24`" in text, "gates"),
        ("repository integrity result exists", "Repository integrity result: `PASS`" in text, "repository"),
        ("audit-suite result exists", "Full regression-suite result: `PASS`" in text, "audits"),
        ("critical route verification exists", "Critical route verification result: `PASS`" in text, "routes"),
        ("authorization result exists", "Authorization result: `PASS`" in text, "authorization"),
        ("firm-scope result exists", "Firm-scope result: `PASS`" in text, "firm scope"),
        ("reports readiness exists", "REPORTS_READY=True" in text, "reports"),
        ("governance readiness exists", "GOVERNANCE_READY=True" in text, "governance"),
        ("archive/continuity readiness exists", "ARCHIVE_CONTINUITY_READY=True" in text, "archive"),
        ("Compliance inactive-state classification exists", "Compliance classification: `ACCEPTABLE_INACTIVE_STATE`" in text, "Compliance"),
        ("System Observation inactive-state classification exists", "System Observation classification: `ACCEPTABLE_INACTIVE_STATE`" in text, "System Observation"),
        ("operator acceptance result exists", "OPERATOR_ACCEPTANCE_READY=True" in text, "operator"),
        ("deployment-only requirements separated", "Deployment/certification separation: `PASS`" in text, "deployment"),
        ("known limitations classified", "Known limitations classification: `PASS`" in text, "limitations"),
        (
            "exactly one certification-candidate decision exists",
            exactly_one(text, r"Decision: `CERTIFICATION_CANDIDATE_READY`")
            and "CERTIFICATION_CANDIDATE_BLOCKED" not in text
            and "CERTIFICATION_CANDIDATE_INCOMPLETE" not in text
            and "CERTIFICATION_CANDIDATE_READY_WITH_CONDITIONS" not in text,
            "decision",
        ),
        ("conditions before actual certification present", "None beyond the separately authorized certification phase." in text, "conditions"),
        (
            "exactly one next phase exists",
            exactly_one(text, r"Recommended next phase: `Step 25AP - V2 Certification Candidate Evidence Freeze`"),
            "next phase",
        ),
        ("no certification tag is claimed", "create a tag" in text and "This is not an actual V2 certification." in text, "tag boundary"),
        (
            "no merge is claimed",
            "merge branches" in text and "No merge, tag, or release performed" in text,
            "merge boundary",
        ),
        ("no module activation is claimed", "activate deferred modules" in text and "Accept inactive state" in text, "activation boundary"),
        ("no permanent invented defect IDs appear", not re.search(r"\bD-\d{3,}\b|\bDEFECT-\d+\b|\bBUG-\d+\b", text), "defect ids"),
        ("no machine-specific absolute paths appear", not re.search(r"[A-Za-z]:\\|C:/Users/|/Users/|/home/|/tmp/", text), "portable"),
        ("no production code is modified or staged", not production_changed, production_changed),
        ("repository changes limited to Step 25AO evidence/guard updates", not unauthorized, unauthorized),
        ("active DB hash unchanged", sha256(ROOT / "trustee_app.db") == DB_SHA, sha256(ROOT / "trustee_app.db")),
        ("active audit count unchanged", counts["audit_log"] == 569, counts),
        ("active transfer count unchanged", counts["transfers"] == 14, counts),
        ("active Compliance objects absent", counts["compliance_objects"] == [], counts["compliance_objects"]),
        ("active System Observation objects absent", counts["system_observation_objects"] == [], counts["system_observation_objects"]),
        ("policy hash unchanged", sha256(ROOT / "data" / "export_policy.json") == POLICY_SHA, POLICY_SHA),
    ]

    for label, condition, detail in checks:
        if not check(label, condition, detail):
            failures += 1

    print("STEP 25AO V2 CERTIFICATION CANDIDATE READINESS AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
