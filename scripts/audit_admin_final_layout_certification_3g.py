from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"
def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.stdout.strip(), p.stderr.strip()
def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1
text = (ROOT / "templates" / "admin_index.html").read_text(encoding="utf-8", errors="ignore")
fail = 0
print("POST-V2-3G ADMIN DASHBOARD FINAL LAYOUT CERTIFICATION")
print("=" * 72)
branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)
required = ["Institutional Command Groups","Admin Layout Controls","Legacy Compatibility Center","Duplicate Entry Points","System Controls","section-governance-label","ACTIVE OPERATING SURFACE","LEGACY COMPATIBILITY","DUPLICATE ENTRY POINT","PROTECTED SYSTEM CONTROL","Certified Baseline Preserved","v2-certified-baseline-2026-07-10"]
missing = [x for x in required if x not in text]
fail += check("final layout markers present", not missing, "all present" if not missing else ", ".join(missing))
routes = ["system_health_dashboard","governance_dashboard","matters_dashboard","fiduciary_dashboard","export_center","continuity_asset_dashboard","security_dashboard","admin_audit_log"]
missing_routes = [x for x in routes if x not in text]
fail += check("grouped command routes preserved", not missing_routes, "all present" if not missing_routes else ", ".join(missing_routes))
fail += check("collapse details retained", text.count("<details") >= 3 and text.count("<summary") >= 3, "details=" + str(text.count("<details")) + "; summary=" + str(text.count("<summary")))
fail += check("active labels calibrated", text.count("ACTIVE OPERATING SURFACE") >= 6, "count=" + str(text.count("ACTIVE OPERATING SURFACE")))
fail += check("duplicate labels retained", text.count("DUPLICATE ENTRY POINT") >= 4, "count=" + str(text.count("DUPLICATE ENTRY POINT")))
fail += check("system labels retained", text.count("PROTECTED SYSTEM CONTROL") >= 3, "count=" + str(text.count("PROTECTED SYSTEM CONTROL")))
group_idx = text.find("Institutional Command Groups")
layout_idx = text.find("Admin Layout Controls")
legacy_idx = text.find("Legacy Compatibility Center")
fail += check("grouped command before legacy center", group_idx != -1 and legacy_idx != -1 and group_idx < legacy_idx, "grouped=" + str(group_idx) + "; legacy=" + str(legacy_idx))
fail += check("layout controls before legacy center", layout_idx != -1 and legacy_idx != -1 and layout_idx < legacy_idx, "layout=" + str(layout_idx) + "; legacy=" + str(legacy_idx))
status, err = git(["status", "--short"])
dirty = [x for x in status.splitlines() if x.strip() != "?? scripts/audit_admin_final_layout_certification_3g.py"]
fail += check("working tree clean or only 3G audit untracked", not dirty, "clean/self-only" if not dirty else "\\n".join(dirty))
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\\n".join(bad_db))
print("")
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
