from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"

def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

template = ROOT / "templates" / "admin_index.html"
text = template.read_text(encoding="utf-8", errors="ignore") if template.exists() else ""
fail = 0
print("POST-V2-3A-R1 ADMIN GROUPED LANDING SAFE AUDIT")
print("=" * 72)
code, branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
code, tag_commit, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag resolves", code == 0, tag_commit or err)
fail += check("admin template exists", template.exists(), str(template))
required = ["Admin Operator Groups","System Status","Governance","Matters / Trusts","People / Fiduciaries","Documents / Exports","Archive / Continuity","Security / Access","Developer / Diagnostics",CERTIFIED_TAG]
missing = [x for x in required if x not in text]
fail += check("required grouped labels present", not missing, "all present" if not missing else ", ".join(missing))
routes = ["system_health_dashboard","governance_dashboard","matters_dashboard","fiduciary_dashboard","export_center","continuity_asset_dashboard","security_dashboard","admin_audit_log"]
missing_routes = [x for x in routes if x not in text]
fail += check("required url_for route names present", not missing_routes, "all present" if not missing_routes else ", ".join(missing_routes))
code, status, err = git(["status", "--short"])
bad = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad, "none" if not bad else "\\n".join(bad))
print("")
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
