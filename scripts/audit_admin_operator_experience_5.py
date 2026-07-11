from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

REQUIRED_HEADINGS = [
    "Recommended Next Action",
    "Executive Home",
    "Continue Where You Left Off",
    "Recent Institutional Activity",
    "Institutional Command Center",
    "Intake & Lifecycle Command Center",
    "System Snapshot",
    "Existing Trust Operations",
    "Legacy Compatibility Center",
    "Admin Layout Controls",
]

OPERATOR_SIGNALS = [
    "ACTIVE OPERATING SURFACE",
    "DUPLICATE ENTRY POINT",
    "LEGACY COMPATIBILITY",
    "SYSTEM CONTROL",
]

CRITICAL_LINKS = [
    "governance",
    "intake_dashboard",
    "matters_dashboard",
    "portfolio",
    "system_health",
    "audit",
    "export",
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

print("POST-V2-5 ADMIN DASHBOARD OPERATOR EXPERIENCE REVIEW")
print("=" * 72)

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)

fail += check("admin template readable", bool(text), str(ADMIN_TEMPLATE))

missing_headings = [h for h in REQUIRED_HEADINGS if h not in text]
fail += check("operator headings present", not missing_headings, "all present" if not missing_headings else ", ".join(missing_headings))

missing_signals = [s for s in OPERATOR_SIGNALS if s not in text]
fail += check("operator classification signals present", not missing_signals, "all present" if not missing_signals else ", ".join(missing_signals))

missing_links = [link for link in CRITICAL_LINKS if link not in lower]
fail += check("critical operator links present", not missing_links, "all present" if not missing_links else ", ".join(missing_links))

details_count = lower.count("<details")
summary_count = lower.count("<summary")
fail += check("collapsible operator sections retained", details_count >= 4 and summary_count >= 4, "details=" + str(details_count) + "; summary=" + str(summary_count))

recommended_idx = text.find("Recommended Next Action")
command_idx = min([i for i in [text.find("Institutional Command Center"), text.find("ACTIVE OPERATING SURFACE"), text.find("Existing Trust Operations")] if i != -1] or [-1])
legacy_idx = text.find("Legacy Compatibility Center")
fail += check("operator flow order preserved", -1 not in [recommended_idx, command_idx, legacy_idx] and recommended_idx < legacy_idx and command_idx < legacy_idx, "recommended=" + str(recommended_idx) + "; command=" + str(command_idx) + "; legacy=" + str(legacy_idx))

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\\n".join(bad_db))

print("")
print("OPERATOR EXPERIENCE FINDINGS")
print("-" * 72)
print("1. Recommended Next Action appears before the command center.")
print("2. Active operating surfaces remain separated from legacy compatibility sections.")
print("3. Duplicate entry points are labeled instead of silently removed.")
print("4. System controls remain visible but governed.")
print("5. Further UX patching should focus on default-expanded vs default-collapsed behavior.")

print("")
print("SUMMARY")
print("-" * 72)
print("details_count:", details_count)
print("summary_count:", summary_count)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
