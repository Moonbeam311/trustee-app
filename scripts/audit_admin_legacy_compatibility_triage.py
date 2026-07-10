from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

SECTIONS = {
    "Recommended Next Action": "ACTIVE OPERATING SURFACE",
    "Executive Home": "ACTIVE OPERATING SURFACE",
    "Continue Where You Left Off": "ACTIVE OPERATING SURFACE",
    "Recent Institutional Activity": "ACTIVE OPERATING SURFACE",
    "Institutional Command Center": "ACTIVE OPERATING SURFACE",
    "Legacy Compatibility Center": "LEGACY COMPATIBILITY",
    "Intake & Lifecycle Command Center": "ACTIVE OPERATING SURFACE",
    "Intake Command Center": "ACTIVE OPERATING SURFACE",
    "System Snapshot": "ACTIVE OPERATING SURFACE",
    "Existing Trust Operations": "ACTIVE OPERATING SURFACE",
    "Existing Trust Operations Dashboard": "ACTIVE OPERATING SURFACE",
    "Existing Trust Command Cards": "DUPLICATE ENTRY POINT",
    "Legacy Quick Start": "LEGACY COMPATIBILITY",
    "Learning & Guidance Suite": "DUPLICATE ENTRY POINT",
    "Hosted Baseline Seed": "SYSTEM CONTROL",
    "Database Backup": "SYSTEM CONTROL",
    "System Policy Controls": "SYSTEM CONTROL",
    "Report Launch Area": "DUPLICATE ENTRY POINT",
    "Admin Tools": "DUPLICATE ENTRY POINT",
    "Operational Shortcuts": "DUPLICATE ENTRY POINT",
    "Security Layer": "SYSTEM CONTROL",
}

def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

template = ROOT / "templates" / "admin_index.html"
text = template.read_text(encoding="utf-8", errors="ignore") if template.exists() else ""
fail = 0

print("POST-V2-3C ADMIN LEGACY COMPATIBILITY TRIAGE AUDIT")
print("=" * 72)

code, branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

code, tag_commit, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag matches expected commit", tag_commit == EXPECTED_COMMIT, tag_commit or err)

fail += check("admin template exists", template.exists(), str(template))
fail += check("institutional command groups retained", "Institutional Command Groups" in text, "present" if "Institutional Command Groups" in text else "missing")
fail += check("legacy compatibility center present", "Legacy Compatibility Center" in text, "present" if "Legacy Compatibility Center" in text else "missing")

print("")
print("TRIAGE CLASSIFICATION")
print("-" * 72)

missing = []
present = []
for label, classification in SECTIONS.items():
    found = label in text
    print(("PRESENT" if found else "MISSING") + " | " + classification + " | " + label)
    if found:
        present.append((label, classification))
    else:
        missing.append(label)

fail += check("triage labels mostly present", len(present) >= 15, "present=" + str(len(present)) + "; missing=" + str(len(missing)))

duplicate_labels = [label for label, cls in present if cls == "DUPLICATE ENTRY POINT"]
system_controls = [label for label, cls in present if cls == "SYSTEM CONTROL"]
legacy_labels = [label for label, cls in present if cls == "LEGACY COMPATIBILITY"]
active_labels = [label for label, cls in present if cls == "ACTIVE OPERATING SURFACE"]

print("")
print("TRIAGE SUMMARY")
print("-" * 72)
print("active_operating_surfaces:", len(active_labels), active_labels)
print("legacy_compatibility_sections:", len(legacy_labels), legacy_labels)
print("duplicate_entry_points:", len(duplicate_labels), duplicate_labels)
print("system_controls:", len(system_controls), system_controls)
print("missing_labels:", missing)

fail += check("duplicate entry points identified", len(duplicate_labels) >= 3, str(duplicate_labels))
fail += check("system controls identified", len(system_controls) >= 3, str(system_controls))
fail += check("legacy compatibility sections identified", len(legacy_labels) >= 1, str(legacy_labels))

code, status, err = git(["status", "--short"])
bad = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad, "none" if not bad else "\\n".join(bad))

print("")
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
