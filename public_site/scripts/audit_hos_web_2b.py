from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


PUBLIC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PUBLIC_ROOT.parent
DEPLOYMENT_ROOT = PUBLIC_ROOT / "deployment"
DECISION_PATH = PUBLIC_ROOT / "HOS_WEB_2B_DEPLOYMENT_CONFIGURATION_DECISION_LOCK.md"
MANIFEST_PATH = DEPLOYMENT_ROOT / "public-artifact-manifest.json"
HOSTING_PATH = DEPLOYMENT_ROOT / "hosting-architecture.json"
HEADERS_PATH = DEPLOYMENT_ROOT / "security-headers-blueprint.json"
EXPECTED_COMMIT = "db051e2ba45d5cf1b9f163e653e7ba5d2443d3fc"
EXPECTED_DOMAIN = "hindsfoot-os.com"
EXPECTED_MASTER_HASH = "5B2B4406D71AEDF9B74BF4BE9252FC402F80841B49874DD9E3DC3A4BD83F5A07"
PROTECTED_PATHS = {
    "docs/version_3_completion_addendum_2026-08-14.md",
    "docs/version_3_locked_plan_recovery_2026-08-14.md",
}
EXPECTED_DEPLOYABLE = {
    "about.html",
    "accessibility.html",
    "assets/css/site.css",
    "assets/images/brand/apple-touch-icon-180.png",
    "assets/images/brand/favicon-16.png",
    "assets/images/brand/favicon-32.png",
    "assets/images/brand/hindsfoot_emblem_512.png",
    "assets/images/brand/hindsfoot_emblem_circle_512.png",
    "assets/images/brand/hindsfoot_header_seal_512.png",
    "assets/images/brand/hindsfoot_os_hero_identity_no_principle.png",
    "assets/images/brand/hindsfoot_os_master.png",
    "assets/js/config.js",
    "assets/js/site.js",
    "capabilities.html",
    "genealogy-legacy.html",
    "hindsfoot-model.html",
    "how-it-works.html",
    "index.html",
    "privacy.html",
    "request-demo.html",
    "security-continuity.html",
    "software-disclaimer.html",
    "terms.html",
    "who-it-helps.html",
    "work-learning-hub.html",
}


passed = 0
failed = 0


def check(label: str, condition: bool, detail: object = "") -> None:
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"{'PASS' if condition else 'FAIL'} - {label} | {detail}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8"
    ).strip()


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
hosting = json.loads(HOSTING_PATH.read_text(encoding="utf-8"))
headers = json.loads(HEADERS_PATH.read_text(encoding="utf-8"))
decision = DECISION_PATH.read_text(encoding="utf-8")

check("repository branch", git("branch", "--show-current") == "system-1-annual-evaluation")
check("certified HEAD", git("rev-parse", "HEAD") == EXPECTED_COMMIT)
check("manifest exact count declaration", manifest["exact_file_count"] == 25)
check("manifest file count", len(manifest["files"]) == 25)

artifact_paths = [entry["artifact_relative_path"] for entry in manifest["files"]]
repository_paths = [entry["repository_relative_path"] for entry in manifest["files"]]
check("manifest paths unique", len(artifact_paths) == len(set(artifact_paths)))
check("repository paths unique", len(repository_paths) == len(set(repository_paths)))
check("no artifact-path case collision", len(artifact_paths) == len({path.casefold() for path in artifact_paths}))
check("no repository-path case collision", len(repository_paths) == len({path.casefold() for path in repository_paths}))
check("exact deployable allowlist", set(artifact_paths) == EXPECTED_DEPLOYABLE)
categories = [entry["category"] for entry in manifest["files"]]
check("14 HTML entries", categories.count("HTML") == 14)
check("one CSS entry", categories.count("CSS") == 1)
check("two JavaScript entries", categories.count("JAVASCRIPT") == 2)
check("eight image entries", categories.count("IMAGE") == 8)

actual_candidates: set[str] = set()
for path in PUBLIC_ROOT.rglob("*"):
    if not path.is_file():
        continue
    relative = path.relative_to(PUBLIC_ROOT).as_posix()
    if (
        (path.parent == PUBLIC_ROOT and path.suffix == ".html")
        or relative == "assets/css/site.css"
        or relative in {"assets/js/config.js", "assets/js/site.js"}
        or (relative.startswith("assets/images/brand/") and path.suffix == ".png")
    ):
        actual_candidates.add(relative)
check("certified candidate inventory remains exact", actual_candidates == EXPECTED_DEPLOYABLE)

allowed_extensions = {".html", ".css", ".js", ".png"}
for entry in manifest["files"]:
    artifact = entry["artifact_relative_path"]
    repository = entry["repository_relative_path"]
    pure = PurePosixPath(artifact)
    source = REPO_ROOT / repository
    check(f"safe relative path: {artifact}", not pure.is_absolute() and ".." not in pure.parts)
    check(f"nonhidden path: {artifact}", all(not part.startswith(".") for part in pure.parts))
    check(f"allowed extension: {artifact}", pure.suffix in allowed_extensions)
    check(f"source exists: {artifact}", source.is_file())
    check(f"source is not symlink: {artifact}", not source.is_symlink())
    check(f"byte size: {artifact}", source.stat().st_size == entry["byte_size"])
    check(f"SHA-256: {artifact}", sha256(source) == entry["sha256"])
    check(f"repository boundary: {artifact}", repository == f"public_site/{artifact}")

check("candidate domain exact", hosting["candidate_domain"] == EXPECTED_DOMAIN)
check("domain registration inactive", hosting["domain_registration"] == "UNVERIFIED_NOT_PURCHASED")
check("trademark incomplete", hosting["trademark_clearance"] == "NOT_COMPLETED")
check("preferred host", hosting["preferred_provider"] == "Cloudflare Pages")
check("fallback host", hosting["fallback_provider"] == "Vercel Pro")
check(
    "controlled artifact Direct Upload mode",
    hosting["deployment_mode"] == "artifact-based Direct Upload through controlled CI",
)
check(
    "public/authenticated separation",
    hosting["public_authenticated_separation"]
    == "SEPARATE_PROJECTS_RUNTIMES_CREDENTIALS_HOSTNAMES_AND_SECURITY_BOUNDARIES",
)
check("deployment unauthorized", hosting["deployment_authorized"] is False)
check("DNS unauthorized", hosting["dns_change_authorized"] is False)
check("hosting connection unauthorized", hosting["hosting_connection_authorized"] is False)
check("domain activation unauthorized", hosting["domain_activation_authorized"] is False)
check("Login inactive", hosting["login_destination_active"] is False)
check("demonstration form inactive", hosting["demonstration_form_active"] is False)
check("analytics disabled", hosting["analytics_enabled"] is False)
check("canonical public hostname", hosting["hostnames"]["canonical_public"] == "www.hindsfoot-os.com")
check("apex hostname", hosting["hostnames"]["apex"] == EXPECTED_DOMAIN)
check("authenticated hostname", hosting["hostnames"]["authenticated_application"] == "app.hindsfoot-os.com")
check("staging hostname", hosting["hostnames"]["protected_preview"] == "staging.hindsfoot-os.com")
check("preview access control required", "Staging requires access control" in decision)
check("preview indexing prohibited", "noindex, nofollow, noarchive" in decision)
check("manual production promotion", "Human approval" in decision)
check("repository-root deployment prohibited", "Direct repository-root" in decision)
check("automatic production deployment prohibited", "Automatic production deployment" in decision)
check("public host does not collect credentials", "public host never collects or proxies credentials" in decision)
check("contact processor unselected", "processor is `UNSELECTED`" in decision)
check("sensitive form fields prohibited", "Trust, estate, tax, financial" in decision)
check("legal review remains required", "REQUIRES_PRODUCTION_REVIEW" in decision)
check("deployment evidence required", "artifact manifest and hashes" in decision)
check("responsible assignments unresolved", "Unresolved assignments" in decision)
check("header activation unauthorized", headers["activation_authorized"] is False)
check("CSP preview report-only", "Content-Security-Policy-Report-Only" in headers["preview"])
check("HSTS subdomains deferred", headers["strict_transport_security"]["includeSubDomains"] is False)
check("HSTS preload deferred", headers["strict_transport_security"]["preload"] is False)

record_text = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (DECISION_PATH, MANIFEST_PATH, HOSTING_PATH, HEADERS_PATH)
)
underscore_variant = "hindsfoot" + "_os.com"
check("no underscore domain variant", underscore_variant not in record_text.lower())
check("no brand misspelling", re.search(r"\bhindfoot\b", record_text, re.IGNORECASE) is None)
check("no absolute local path", re.search(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)", record_text) is None)
protected_reference_pattern = "|".join(("ITFB-" + "FAAB240E00C2", "TR-" + "001"))
check("no protected reference", re.search(protected_reference_pattern, record_text) is None)
private_key_marker = "BEGIN " + "PRIVATE KEY"
check("no private key", private_key_marker not in record_text)
check("no token-shaped value", re.search(r"(?:ghp_|sk-)[A-Za-z0-9]{20,}", record_text) is None)
check("no live provider identifiers", re.search(r'"(?:account|zone|project)_id"\s*:', record_text) is None)
check("domain disclaimer present", "unverified and incomplete" in decision.lower())
ownership_claim = "domain is " + "owned"
check("no domain ownership claim", ownership_claim not in record_text.lower())

master = PUBLIC_ROOT / "assets/images/brand/hindsfoot_os_master.png"
check("locked master-logo hash", sha256(master) == EXPECTED_MASTER_HASH)

status_lines = git("status", "--short").splitlines()
status_paths = {line[3:].replace("\\", "/") for line in status_lines if line}
check("protected paths remain untracked", PROTECTED_PATHS <= status_paths)
check(
    "tracked/authenticated scope unchanged",
    all(path.startswith("public_site/") or path in PROTECTED_PATHS for path in status_paths),
    sorted(status_paths),
)
check("staged files absent", not git("diff", "--cached", "--name-only"))
check(
    "repository-only records excluded",
    not any(path.startswith("deployment/") or path.endswith(".md") or path.startswith("scripts/") for path in artifact_paths),
)

print("\nHOS-WEB-2B DEPLOYMENT CONFIGURATION AUDIT")
print(f"Assertions passed: {passed}")
print(f"Assertions failed: {failed}")
if failed:
    sys.exit(1)
print("RESULT: PASS")
