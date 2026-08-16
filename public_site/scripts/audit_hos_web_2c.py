from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


PUBLIC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PUBLIC_ROOT.parent
DEPLOYMENT_ROOT = PUBLIC_ROOT / "deployment"
BASELINE = "548fab59b2374149040daeb2c2db2ae9ad0eab35"
DOMAIN = "hindsfoot-os.com"
MASTER_HASH = "5B2B4406D71AEDF9B74BF4BE9252FC402F80841B49874DD9E3DC3A4BD83F5A07"
NEW_PATHS = {
    "public_site/deployment/HOS_WEB_2C_OWNERSHIP_AUTHORITY.md",
    "public_site/deployment/HOS_WEB_2C_DOMAIN_NAME_RISK_EVIDENCE.md",
    "public_site/deployment/HOS_WEB_2C_PROVIDER_READINESS.md",
    "public_site/deployment/HOS_WEB_2C_PREREQUISITE_MATRIX.md",
    "public_site/scripts/audit_hos_web_2c.py",
}
PROTECTED = {
    "docs/version_3_completion_addendum_2026-08-14.md",
    "docs/version_3_locked_plan_recovery_2026-08-14.md",
}

passed = 0
failed = 0


def check(label: str, condition: bool, detail: object = "") -> None:
    global passed, failed
    passed += int(condition)
    failed += int(not condition)
    print(f"{'PASS' if condition else 'FAIL'} - {label} | {detail}")


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8"
    ).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


ownership_path = DEPLOYMENT_ROOT / "HOS_WEB_2C_OWNERSHIP_AUTHORITY.md"
domain_path = DEPLOYMENT_ROOT / "HOS_WEB_2C_DOMAIN_NAME_RISK_EVIDENCE.md"
provider_path = DEPLOYMENT_ROOT / "HOS_WEB_2C_PROVIDER_READINESS.md"
matrix_path = DEPLOYMENT_ROOT / "HOS_WEB_2C_PREREQUISITE_MATRIX.md"
manifest_path = DEPLOYMENT_ROOT / "public-artifact-manifest.json"
hosting_path = DEPLOYMENT_ROOT / "hosting-architecture.json"

paths = [ownership_path, domain_path, provider_path, matrix_path]
for path in paths:
    check(f"record exists: {path.name}", path.is_file())

texts = {path.name: path.read_text(encoding="utf-8") for path in paths}
combined = "\n".join(texts.values())
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
hosting = json.loads(hosting_path.read_text(encoding="utf-8"))

check("branch exact", git("branch", "--show-current") == "system-1-annual-evaluation")
check("HEAD remains baseline", git("rev-parse", "HEAD") == BASELINE)
check("remote aligned", git("rev-parse", "origin/system-1-annual-evaluation") == BASELINE)
check("ahead behind zero", git("rev-list", "--left-right", "--count", "HEAD...origin/system-1-annual-evaluation") == "0\t0")
check("staged files zero", git("diff", "--cached", "--name-only") == "")

expected_hostnames = {
    "canonical_public": "www.hindsfoot-os.com",
    "apex": DOMAIN,
    "authenticated_application": "app.hindsfoot-os.com",
    "protected_preview": "staging.hindsfoot-os.com",
}
check("candidate domain locked", hosting["candidate_domain"] == DOMAIN)
check("hostnames locked", hosting["hostnames"] == expected_hostnames)
check("Cloudflare preferred", hosting["preferred_provider"] == "Cloudflare Pages")
check("Vercel Pro fallback", hosting["fallback_provider"] == "Vercel Pro")
check("artifact mode locked", hosting["deployment_mode"] == "artifact-based Direct Upload through controlled CI")
check("deployment unauthorized", hosting["deployment_authorized"] is False)
check("hosting unauthorized", hosting["hosting_connection_authorized"] is False)
check("DNS unauthorized", hosting["dns_change_authorized"] is False)
check("domain activation unauthorized", hosting["domain_activation_authorized"] is False)
check("Login inactive", hosting["login_destination_active"] is False)
check("form inactive", hosting["demonstration_form_active"] is False)
check("analytics disabled", hosting["analytics_enabled"] is False)
check("public private separation", "SEPARATE_PROJECTS" in hosting["public_authenticated_separation"])

check("manifest exact 25", manifest["exact_file_count"] == 25 and len(manifest["files"]) == 25)
for entry in manifest["files"]:
    rel = entry["repository_relative_path"]
    source = REPO_ROOT / rel
    check(f"manifest source exists: {rel}", source.is_file())
    check(f"manifest hash current: {rel}", sha256(source) == entry["sha256"])
    baseline_blob = git("rev-parse", f"{BASELINE}:{rel}")
    check(f"rendered baseline identity: {rel}", git("hash-object", "--", rel) == baseline_blob)

check("master logo unchanged", sha256(PUBLIC_ROOT / "assets/images/brand/hindsfoot_os_master.png") == MASTER_HASH)
check("domain classification exact", "APPARENTLY UNREGISTERED  REGISTRAR AVAILABILITY CHECK STILL REQUIRED" in texts[domain_path.name])
check("risk classification exact", "MODERATE PRELIMINARY CONFLICT SIGNAL  COUNSEL REVIEW REQUIRED" in texts[domain_path.name])
check("provider classification exact", "CLOUDFLARE REMAINS PREFERRED  ACCOUNT AND AUTHORITY SETUP REQUIRED" in texts[provider_path.name])
check("domain non-ownership disclaimer", "does not establish availability, ownership" in texts[domain_path.name])

ownership = texts[ownership_path.name]
for role in (
    "Brand owner / decision authority", "Domain registrant authority", "Domain billing contact",
    "Registrar administrator", "Cloudflare account owner", "Cloudflare billing owner",
    "Cloudflare Pages project administrator", "GitHub repository administrator", "DNS administrator",
    "TLS / certificate administrator", "Production deployment approver", "Preview deployment approver",
    "Authenticated-application owner", "Privacy / legal review owner", "Accessibility review owner",
    "Security review owner", "Monitoring / incident-response owner", "Rollback authority",
    "Backup / evidence custodian", "Successor / emergency administrator",
):
    check(f"ownership role: {role}", role in ownership)
check("ownership counts", "VERIFIED: **0**" in ownership and "PROVISIONAL: **1**" in ownership and "UNASSIGNED: **19**" in ownership)

matrix = texts[matrix_path.name]
gate_names = [
    "Name-risk acceptance", "Domain acquisition authorization", "Registrant and billing ownership",
    "Cloudflare account ownership", "DNS and TLS authority", "Preview-access policy",
    "Legal/privacy/accessibility acceptance", "Monitoring and rollback ownership",
    "Artifact recertification", "Deployment authorization", "Production deployment",
    "Post-deployment verification",
]
positions = [matrix.index(name) if name in matrix else -1 for name in gate_names]
check("all 12 gates present", all(position >= 0 for position in positions))
check("gate order exact", positions == sorted(positions) and len(set(positions)) == 12)
check("prerequisite counts", "SATISFIED 2; PARTIALLY SATISFIED 6; UNSATISFIED 6; NOT APPLICABLE 0" in matrix)

check("no invalid underscore domain", "hindsfoot_os.com" not in combined.lower())
check("no misspelled brand", re.search(r"\bhindfoot\b|hindsfots", combined, re.IGNORECASE) is None)
check("no local absolute path", re.search(r"[A-Za-z]:\\Users\\|/Users/|/home/", combined) is None)
check("no private key material", "BEGIN PRIVATE KEY" not in combined)
check("no token-shaped secret", re.search(r"(?:ghp_|sk-)[A-Za-z0-9]{20,}", combined) is None)
check("no protected record token", re.search(r"ITFB-[A-Z0-9]+|\bTR-\d{3,}\b", combined) is None)

status = git("status", "--porcelain=v1").splitlines()
status_paths = {line[3:].replace("\\", "/") for line in status if line}
check("authorized status only", status_paths == PROTECTED | NEW_PATHS, sorted(status_paths))
check("protected documents untracked", all(f"?? {path}" in status for path in PROTECTED))
check("new records unstaged", all(f"?? {path}" in status for path in NEW_PATHS))
check("no authenticated tracked changes", not git("diff", "--name-only"))
check("openai hosting absent", not (REPO_ROOT / ".openai" / "hosting.json").exists())

print("\nHOS-WEB-2C DEPLOYMENT PREREQUISITE READINESS AUDIT")
print(f"Assertions passed: {passed}")
print(f"Assertions failed: {failed}")
if failed:
    sys.exit(1)
print("RESULT: PASS")
