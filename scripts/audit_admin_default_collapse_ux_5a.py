from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"
MARKER = "POST-V2-5A DEFAULT EXPANSION / COLLAPSE UX PATCH"

ACTIVE_SURFACES = [
    "Recommended Next Action",
    "Executive Home",
    "Continue Where You Left Off",
    "Recent Institutional Activity",
    "Institutional Command Center",
    "Intake & Lifecycle Command Center",
    "Intake Command Center",
    "System Snapshot",
    "Existing Trust Operations",
    "Existing Trust Operations Dashboard",
]

COLLAPSED_GOVERNED = [
    "Legacy Compatibility Center",
    "Legacy Quick Start",
    "Existing Trust Command Cards",
    "Learning & Guidance Suite",
    "Report Launch Area",
    "Admin Tools",
    "Operational Shortcuts",
    "Hosted Baseline Seed",
    "Database Backup",
    "System Policy Controls",
    "Security Layer",
]

def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

def nearest_details_tag(text, label):
    idx = text.find(label)
    if idx == -1:
        return None
    d = text.rfind("<details", 0, idx)
    e = text.find(">", d)
    if d == -1 or e == -1:
        return None
    return text[d:e+1]

text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
lower = text.lower()
fail = 0

print("POST-V2-5A ADMIN DEFAULT EXPANSION / COLLAPSE UX AUDIT")
print("=" * 72)

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)
fail += check("admin template readable", bool(text), str(ADMIN_TEMPLATE))
fail += check("5A marker present", MARKER in text, "present" if MARKER in text else "missing")

missing_active = [x for x in ACTIVE_SURFACES if x not in text]
fail += check("active operator surfaces preserved", not missing_active, "all present" if not missing_active else ", ".join(missing_active))
missing_governed = [x for x in COLLAPSED_GOVERNED if x not in text]
fail += check("governed collapsed surfaces preserved", not missing_governed, "all present" if not missing_governed else ", ".join(missing_governed))

details_count = lower.count("<details")
summary_count = lower.count("<summary")
open_count = len(re.findall(r"<details\s+open", lower))
closed_count = details_count - open_count
fail += check("details controls retained", details_count >= 4 and summary_count >= 4, "details=" + str(details_count) + "; summary=" + str(summary_count))
fail += check("governed default collapse state present", closed_count >= 1, "open=" + str(open_count) + "; closed=" + str(closed_count))

legacy_tag = nearest_details_tag(text, "Legacy Compatibility Center")
fail += check("legacy center collapsed by default", legacy_tag is not None and "open" not in legacy_tag.lower(), str(legacy_tag))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("details_count:", details_count)
print("open_details:", open_count)
print("closed_details:", closed_count)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
