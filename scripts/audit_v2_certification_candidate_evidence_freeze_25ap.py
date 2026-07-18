from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap.md"
MANIFEST = ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap_manifest.json"
BUILDER = ROOT / "scripts" / "build_v2_certification_candidate_evidence_freeze_25ap.py"
SOURCE_COMMIT = "a1f63da1096bc6c261db2fd8a894f660ec919c2a"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
ALLOWED_CHANGED = {
    "docs/v2_certification_candidate_evidence_freeze_25ap.md",
    "docs/v2_certification_candidate_evidence_freeze_25ap_manifest.json",
    "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
}
PRODUCTION_PREFIXES = ("app.py", "pdf_utils.py", "templates/", "services/", "models/", "migrations/", "database/")
EXCLUDED_PREFIXES = ("audit/runtime_sandbox/", "test_artifacts/", "uploads/", "exports/", "data/backups/", "config/local/")
SECRET_MARKERS = ("secret", "token", "credential", "cookie", ".env")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


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
            "compliance_objects": [table for table in tables if "compliance_review" in table.lower()],
            "system_observation_objects": [table for table in tables if "system_observation" in table.lower()],
        }


def run_builder_check() -> bool:
    result = subprocess.run(
        [sys.executable, "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
    return result.returncode == 0


def main() -> int:
    failures = 0
    report_text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    evidence = manifest.get("evidence_files", [])
    paths = [entry.get("path", "") for entry in evidence]
    changed = changed_paths()
    staged = staged_paths()
    production_changed = sorted(
        path for path in changed | staged if path in {"app.py", "pdf_utils.py"} or path.startswith(PRODUCTION_PREFIXES)
    )

    checks = [
        ("freeze report exists", REPORT.exists(), REPORT.relative_to(ROOT).as_posix()),
        ("manifest exists", MANIFEST.exists(), MANIFEST.relative_to(ROOT).as_posix()),
        ("builder exists", BUILDER.exists(), BUILDER.relative_to(ROOT).as_posix()),
        ("starting source commit is a1f63da", manifest.get("source_commit") == SOURCE_COMMIT, manifest.get("source_commit")),
        ("candidate decision is CERTIFICATION_CANDIDATE_READY", manifest.get("candidate_status") == "CERTIFICATION_CANDIDATE_READY", manifest.get("candidate_status")),
        ("freeze is explicitly not certification", "does not issue certification" in report_text, "certification boundary"),
        ("no tag is claimed", "create a tag" in report_text and "does not issue certification" in report_text, "tag boundary"),
        ("no merge is claimed", "merge branches" in report_text, "merge boundary"),
        ("active DB SHA is present", DB_SHA in report_text and manifest.get("active_db_reference", {}).get("sha256") == DB_SHA, DB_SHA),
        ("audit count 569 is present", manifest.get("active_db_reference", {}).get("audit_log_count") == 569, "569"),
        ("transfer count 14 is present", manifest.get("active_db_reference", {}).get("transfer_count") == 14, "14"),
        ("policy SHA is present", POLICY_SHA in report_text and manifest.get("policy_reference", {}).get("sha256") == POLICY_SHA, POLICY_SHA),
        ("policy size 123 is present", manifest.get("policy_reference", {}).get("size_bytes") == 123, "123"),
        ("commit chain includes 8e6318c", any(item.get("short") == "8e6318c" for item in manifest.get("commit_chain", [])), "8e6318c"),
        ("commit chain includes 7b20ef7", any(item.get("short") == "7b20ef7" for item in manifest.get("commit_chain", [])), "7b20ef7"),
        ("commit chain includes 7524a3b", any(item.get("short") == "7524a3b" for item in manifest.get("commit_chain", [])), "7524a3b"),
        ("commit chain includes f70a89f", any(item.get("short") == "f70a89f" for item in manifest.get("commit_chain", [])), "f70a89f"),
        ("commit chain includes a1f63da", any(item.get("short") == "a1f63da" for item in manifest.get("commit_chain", [])), "a1f63da"),
        ("evidence inventory exists", bool(evidence), len(evidence)),
        ("audit inventory exists", bool(manifest.get("authoritative_audits")), len(manifest.get("authoritative_audits", []))),
        ("every evidence file has SHA-256", all(re.fullmatch(r"[A-F0-9]{64}", entry.get("sha256", "")) for entry in evidence), "sha256"),
        ("every evidence file has Git blob SHA", all(re.fullmatch(r"[a-f0-9]{40}", entry.get("git_blob_sha", "")) for entry in evidence), "blob"),
        ("paths are sorted deterministically", paths == sorted(paths), paths[:3]),
        ("no duplicate evidence paths exist", len(paths) == len(set(paths)), len(paths)),
        ("no excluded path is included", not any(path.startswith(EXCLUDED_PREFIXES) for path in paths), "excluded"),
        ("no absolute Windows path appears", not re.search(r"[A-Za-z]:\\|C:/Users/|/Users/|/home/|/tmp/", report_text + json.dumps(manifest)), "portable"),
        ("no secret-like file is included", not any(any(marker in path.lower() for marker in SECRET_MARKERS) for path in paths), "secrets"),
        ("known limitations are preserved", len(manifest.get("known_limitations", [])) == 7, manifest.get("known_limitations", [])),
        ("inactive modules are preserved", len(manifest.get("inactive_modules", [])) == 2, manifest.get("inactive_modules", [])),
        ("deployment-only items remain separate", len(manifest.get("deployment_only_items", [])) == 7, manifest.get("deployment_only_items", [])),
        ("exactly one freeze decision exists", report_text.count("Freeze decision: `EVIDENCE_FREEZE_PASS`") == 1, "decision"),
        ("conditions before certification exist", "None beyond execution of the separately authorized certification phase" in report_text, "conditions"),
        ("exactly one next phase exists", report_text.count("Recommended next phase: `Step 25AQ - V2 Certification Issuance Readiness and Final Integrity Gate`") == 1, "next"),
        ("builder --check passes", run_builder_check(), "--check"),
    ]

    before_db = sha256(ROOT / "trustee_app.db")
    before_policy = sha256(ROOT / "data" / "export_policy.json")
    first_manifest = MANIFEST.read_bytes() if MANIFEST.exists() else b""
    first_report = REPORT.read_bytes() if REPORT.exists() else b""
    result1 = subprocess.run([sys.executable, str(BUILDER.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    second_manifest = MANIFEST.read_bytes() if MANIFEST.exists() else b""
    second_report = REPORT.read_bytes() if REPORT.exists() else b""
    result2 = subprocess.run([sys.executable, str(BUILDER.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    third_manifest = MANIFEST.read_bytes() if MANIFEST.exists() else b""
    third_report = REPORT.read_bytes() if REPORT.exists() else b""
    after_db = sha256(ROOT / "trustee_app.db")
    after_policy = sha256(ROOT / "data" / "export_policy.json")
    counts = active_counts()

    checks.extend(
        [
            ("manifest is deterministic across two generations", result1.returncode == 0 and result2.returncode == 0 and first_manifest == second_manifest == third_manifest and first_report == second_report == third_report, "deterministic"),
            ("active state is not mutated", before_db == after_db == DB_SHA and counts["audit_log"] == 569 and counts["transfers"] == 14, counts),
            ("policy is not mutated", before_policy == after_policy == POLICY_SHA, POLICY_SHA),
            ("no production code is modified or staged", not production_changed, production_changed),
            ("repository changes limited to Step 25AP evidence/guard updates", not sorted((changed | staged) - ALLOWED_CHANGED), sorted((changed | staged) - ALLOWED_CHANGED)),
        ]
    )

    for label, ok, detail in checks:
        if not record(label, bool(ok), detail):
            failures += 1

    print("STEP 25AP V2 CERTIFICATION CANDIDATE EVIDENCE FREEZE AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
