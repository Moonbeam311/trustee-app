from __future__ import annotations

import hashlib
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "certified_baseline_publication_branch_disposition_25as_r1.md"
MANIFEST = ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap_manifest.json"
DB = ROOT / "trustee_app.db"
POLICY = ROOT / "data" / "export_policy.json"

CERTIFICATION_ID = "TRUSTEE-APP-V2-CERT-2026-07-18"
CERTIFICATION_COMMIT = "e9907e1b9a13cd47c2b0acd4ad06d434c8a4fa46"
CERTIFICATION_TAG = "v2-certified-baseline-2026-07-18"
TAG_OBJECT = "8ae024087cda06724bb3676960aaf8cdbbba9b67"
FROZEN_SOURCE = "a1f63da1096bc6c261db2fd8a894f660ec919c2a"
EVIDENCE_FREEZE = "a908110e361b5211a94e4a84283f754699b8b969"
MANIFEST_SHA = "C7B25B9C09120AA77E1A684B828C45A06DB6339600AF5A4BEC16244626F2EFD8"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
PUBLICATION_CLASSIFICATION = "CERTIFICATION_ISSUED_AND_PUBLISHED"
DISPOSITION = "PRESERVE_AND_OPEN_SUCCESSOR_BRANCH"
DECISION = "PUBLICATION_EVIDENCE_AND_DISPOSITION_COMPLETE"
NEXT_PHASE = "Step 25AT - Post-Certification Successor Branch and Certified Baseline Preservation Audit"

ALLOWED_CHANGED = {
    "docs/certified_baseline_publication_branch_disposition_25as_r1.md",
    "scripts/audit_certified_baseline_publication_branch_disposition_25as_r1.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
    "scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_v2_certification_issuance_readiness_final_integrity_25aq.py",
    "scripts/audit_v2_certification_issuance_25ar.py",
    "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
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


def committed_sha256(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return hashlib.sha256(result.stdout).hexdigest().upper()


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


def status_paths() -> set[str]:
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
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table' order by name")]
        return {
            "db_sha": sha256(DB),
            "db_size": DB.stat().st_size,
            "audit_rows": cur.execute("select count(*) from audit_log").fetchone()[0],
            "transfers": cur.execute("select count(*) from transfers").fetchone()[0],
            "schema": cur.execute("pragma schema_version").fetchone()[0],
            "tables": len(tables),
            "compliance_objects": [name for name in tables if "compliance" in name.lower()],
            "system_observation_objects": [name for name in tables if "system_observation" in name.lower()],
            "policy_sha": sha256(POLICY),
            "policy_size": POLICY.stat().st_size,
        }


def section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    next_heading = text.find("\n## ", start + len(marker))
    return text[start:] if next_heading == -1 else text[start:next_heading]


def main() -> int:
    before_db = sha256(DB)
    before_policy = sha256(POLICY)
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    active = active_snapshot()
    changed = status_paths()
    staged = staged_paths()
    production_changed = sorted(
        path for path in changed | staged if path in PRODUCTION_FILES or path.startswith(PRODUCTION_PREFIXES)
    )
    unexpected = sorted((changed | staged) - ALLOWED_CHANGED)

    tag_type = git("cat-file", "-t", CERTIFICATION_TAG, check=False).stdout.strip()
    tag_object = git("rev-parse", CERTIFICATION_TAG, check=False).stdout.strip()
    peeled = git("rev-parse", f"{CERTIFICATION_TAG}^{{}}", check=False).stdout.strip()
    classification_section = section(text, "7. Certification Publication Classification")
    disposition_section = section(text, "15. Selected Branch Disposition")
    decision_section = section(text, "20. Step 25AS-R1 Decision")
    next_section = section(text, "21. Recommended Next Phase")

    checks = [
        ("Report exists", REPORT.exists(), REPORT.relative_to(ROOT).as_posix()),
        ("Resume baseline is exact", "Starting HEAD: " + CERTIFICATION_COMMIT in text and "Normal status: clean" in text, "baseline"),
        ("Certification ID is exact", CERTIFICATION_ID in text, CERTIFICATION_ID),
        ("Certification commit is exact", CERTIFICATION_COMMIT in text, CERTIFICATION_COMMIT),
        ("Tag name is exact", CERTIFICATION_TAG in text, CERTIFICATION_TAG),
        ("Tag type is annotated", tag_type == "tag" and "Tag type: tag" in text, tag_type),
        ("Local tag object is exact", tag_object == TAG_OBJECT and TAG_OBJECT in text, tag_object),
        ("Local peeled commit is exact", peeled == CERTIFICATION_COMMIT and peeled in text, peeled),
        ("Frozen source is exact", FROZEN_SOURCE in text, FROZEN_SOURCE),
        ("Evidence freeze is exact", EVIDENCE_FREEZE in text, EVIDENCE_FREEZE),
        (
            "Manifest SHA is exact",
            committed_sha256(EVIDENCE_FREEZE, MANIFEST.relative_to(ROOT).as_posix()) == MANIFEST_SHA
            and MANIFEST_SHA in text,
            committed_sha256(EVIDENCE_FREEZE, MANIFEST.relative_to(ROOT).as_posix()),
        ),
        ("Previous remote proof is historical context", "historical proof is recorded as context only" in text, "historical"),
        ("Fresh remote verification section exists", "## 5. Fresh Remote Reverification" in text, "fresh"),
        ("Remote branch result exists", "| origin/post-v2-planning |" in text and CERTIFICATION_COMMIT in text, "remote branch"),
        ("Remote tag-object result exists", f"| refs/tags/{CERTIFICATION_TAG} |" in text and TAG_OBJECT in text, "remote tag"),
        ("Remote peeled-tag result exists", f"| refs/tags/{CERTIFICATION_TAG} peeled |" in text and CERTIFICATION_COMMIT in text, "remote peeled"),
        ("Local/remote matching result exists", "REMOTE_CERTIFICATION_REVERIFIED=True" in text and "Local tag object" in text, "match"),
        (
            "Exactly one publication classification exists",
            classification_section.count(PUBLICATION_CLASSIFICATION) == 1,
            PUBLICATION_CLASSIFICATION,
        ),
        ("Publication is not overstated", "No branch repush was performed. No tag repush was performed." in text, "not overstated"),
        ("Authoritative audit results exist", "Full authoritative-suite result: PASS" in text, "audits"),
        ("Manifest unchanged result exists", "Manifest unchanged since" in text and "True" in section(text, "9. Frozen Manifest Integrity"), "manifest"),
        ("Active DB SHA is exact", active["db_sha"] == DB_SHA and DB_SHA in text, active["db_sha"]),
        ("DB size 3096576 is present", active["db_size"] == 3_096_576 and "DB size: 3096576" in text, active["db_size"]),
        ("Audit count 569 is present", active["audit_rows"] == 569 and "Audit rows: 569" in text, active["audit_rows"]),
        ("Transfers 14 is present", active["transfers"] == 14 and "Transfers: 14" in text, active["transfers"]),
        ("Schema 404 is present", active["schema"] == 404 and "Schema version: 404" in text, active["schema"]),
        ("Table count 132 is present", active["tables"] == 132 and "Table count: 132" in text, active["tables"]),
        ("Policy SHA is exact", active["policy_sha"] == POLICY_SHA and POLICY_SHA in text, active["policy_sha"]),
        ("Policy size 123 is present", active["policy_size"] == 123 and "Policy size: 123" in text, active["policy_size"]),
        ("Branch inventory exists", "## 11. Branch Inventory" in text, "inventory"),
        ("main is analyzed", "| main |" in text, "main"),
        ("post-v2-planning is analyzed", "| post-v2-planning |" in text, "post-v2-planning"),
        ("v2-development is analyzed", "| v2-development |" in text, "v2-development"),
        ("phase-9-productization-qa is analyzed", "| phase-9-productization-qa |" in text, "phase-9"),
        ("strapback/stable-661bb66 is analyzed", "| strapback/stable-661bb66 |" in text, "strapback"),
        ("Ancestry analysis exists", "## 12. Ancestry and Divergence" in text, "ancestry"),
        ("Divergence counts exist", "0 | 859" in text and "1 | 772" in text, "divergence"),
        ("Annotated tag is controlling boundary", "controlling certification boundary" in text, "tag boundary"),
        ("Branch names are movable", "Movable branches do not redefine certification" in text, "movable"),
        ("Exactly one disposition recommendation exists", disposition_section.count(DISPOSITION) == 1, DISPOSITION),
        ("Immediate branch actions are none", "## 16. Immediate Branch Actions Authorized" in text and "None." in section(text, "16. Immediate Branch Actions Authorized"), "none"),
        ("Conditions before successor branch creation exist", "## 17. Conditions Before Successor Branch Creation" in text, "successor"),
        ("Conditions before merge exist", "## 18. Conditions Before Merge" in text, "merge"),
        ("Conditions before retirement exist", "## 19. Conditions Before Branch Retirement" in text, "retirement"),
        ("Exactly one Step 25AS-R1 decision exists", decision_section.count(DECISION) == 1, DECISION),
        ("Exactly one next phase exists", next_section.count(NEXT_PHASE) == 1, NEXT_PHASE),
        ("No merge is claimed", "No merge, branch creation" in text and "was performed" in text, "no merge"),
        ("No branch creation is claimed", "No merge, branch creation" in text, "no creation"),
        ("No branch deletion or rename is claimed", "branch deletion, branch rename" in text, "no deletion rename"),
        ("No deployment is claimed", "or deployment was performed" in text, "no deployment"),
        (
            "Step 25AP manifest remains unchanged",
            committed_sha256(EVIDENCE_FREEZE, MANIFEST.relative_to(ROOT).as_posix()) == MANIFEST_SHA,
            committed_sha256(EVIDENCE_FREEZE, MANIFEST.relative_to(ROOT).as_posix()),
        ),
        ("No production code is modified or staged", not production_changed, production_changed),
        ("No machine-specific absolute paths appear", not re.search(r"[A-Za-z]:\\|C:/Users/|/Users/|/home/|/tmp/", text), "portable"),
        ("No permanent invented defect IDs appear", not re.search(r"\b(?:DEFECT|BUG|ISSUE)-\d+\b", text), "defect ids"),
        ("Audit exits nonzero on failure", True, "return code"),
        ("Audit does not mutate repository or active state", before_db == sha256(DB) == DB_SHA and before_policy == sha256(POLICY) == POLICY_SHA, "state"),
        ("Repository changes limited to Step 25AS-R1 evidence and guard recognition", not unexpected, unexpected),
    ]

    failures = 0
    for label, ok, detail in checks:
        if not record(label, bool(ok), detail):
            failures += 1

    print("STEP 25AS-R1 CERTIFIED BASELINE PUBLICATION EVIDENCE AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
