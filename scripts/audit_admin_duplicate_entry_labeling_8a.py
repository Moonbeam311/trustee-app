from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-8A DUPLICATE ENTRY POINT LABELING PATCH"

REQUIRED_LABELS = {
    "Existing Trust Command Cards": "GOVERNED COMPATIBILITY SURFACE",
    "Learning & Guidance Suite": "GOVERNED COMPATIBILITY SURFACE",
    "Report Launch Area": "RELABEL / REDIRECT CANDIDATE",
    "Admin Tools": "RELABEL / REDIRECT CANDIDATE",
    "Operational Shortcuts": "RELABEL / REDIRECT CANDIDATE",
}

FORBIDDEN_ROUTE_CHANGES = [
    "redirect(",
    "url_for(",
    "@app.route",
]

def git(args):
    p = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

print("POST-V2-8A ADMIN DUPLICATE ENTRY POINT LABELING AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)

text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
fail += check("admin template readable", bool(text), str(ADMIN_TEMPLATE))

fail += check("8A marker present", MARKER in text, "present" if MARKER in text else "missing")

missing = []
for heading, label in REQUIRED_LABELS.items():
    if heading not in text or label not in text:
        missing.append(heading + " -> " + label)

fail += check(
    "duplicate entry point labels present",
    not missing,
    "all present" if not missing else ", ".join(missing),
)

compatibility_count = text.count("GOVERNED COMPATIBILITY SURFACE")
candidate_count = text.count("RELABEL / REDIRECT CANDIDATE")

fail += check("compatibility labels count", compatibility_count >= 2, "count=" + str(compatibility_count))
fail += check("candidate labels count", candidate_count >= 3, "count=" + str(candidate_count))

diff, err = git(["diff", "--", "app.py"])
forbidden_found = [x for x in FORBIDDEN_ROUTE_CHANGES if x in diff]
fail += check(
    "no route logic changes in app.py",
    not diff and not forbidden_found,
    "none" if not diff and not forbidden_found else "app.py diff detected",
)

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("LABELING INVENTORY")
print("-" * 72)
print("compatibility_labels:", compatibility_count)
print("candidate_labels:", candidate_count)
print("required_labels_reviewed:", len(REQUIRED_LABELS))

print("")
print("SUMMARY")
print("-" * 72)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
