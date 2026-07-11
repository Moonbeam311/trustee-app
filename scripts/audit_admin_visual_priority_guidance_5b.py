from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"
MARKER = "POST-V2-5B ADMIN VISUAL PRIORITY / OPERATOR GUIDANCE PATCH"

REQUIRED_TEXT = [
    "Operator Guidance",
    "Recommended Next Action",
    "active Institutional Command Center",
    "Active operating surfaces are prioritized",
    "Legacy compatibility, duplicate entry points, and system controls remain preserved",
    "No legacy access has been removed",
]

PRESERVED_SECTIONS = [
    "Recommended Next Action",
    "Institutional Command Center",
    "Legacy Compatibility Center",
    "Existing Trust Command Cards",
    "Learning & Guidance Suite",
    "System Policy Controls",
    "Security Layer",
]

def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
lower = text.lower()
fail = 0

print("POST-V2-5B ADMIN VISUAL PRIORITY / OPERATOR GUIDANCE AUDIT")
print("=" * 72)

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)
fail += check("admin template readable", bool(text), str(ADMIN_TEMPLATE))
fail += check("5B marker present", MARKER in text, "present" if MARKER in text else "missing")

missing_text = [x for x in REQUIRED_TEXT if x not in text]
fail += check("operator guidance language present", not missing_text, "all present" if not missing_text else ", ".join(missing_text))

missing_sections = [x for x in PRESERVED_SECTIONS if x not in text]
fail += check("existing admin sections preserved", not missing_sections, "all present" if not missing_sections else ", ".join(missing_sections))

guidance_idx = text.find("Operator Guidance")
recommended_idx = text.find("Recommended Next Action")
legacy_idx = text.find("Legacy Compatibility Center")
fail += check("guidance appears before legacy center", guidance_idx != -1 and legacy_idx != -1 and guidance_idx < legacy_idx, "guidance=" + str(guidance_idx) + "; legacy=" + str(legacy_idx))
fail += check("recommended action still precedes legacy center", recommended_idx != -1 and legacy_idx != -1 and recommended_idx < legacy_idx, "recommended=" + str(recommended_idx) + "; legacy=" + str(legacy_idx))

details_count = lower.count("<details")
summary_count = lower.count("<summary")
fail += check("collapse controls retained", details_count >= 4 and summary_count >= 4, "details=" + str(details_count) + "; summary=" + str(summary_count))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("details_count:", details_count)
print("summary_count:", summary_count)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
