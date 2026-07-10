from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()
def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1
template = ROOT / "templates" / "admin_index.html"
text = template.read_text(encoding="utf-8", errors="ignore") if template.exists() else ""
fail = 0
print("POST-V2-3B ADMIN VISUAL POLISH AUDIT")
print("=" * 72)
code, branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
code, tag_commit, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag matches expected commit", tag_commit == EXPECTED_COMMIT, tag_commit or err)
required = ["Institutional Command Groups","admin-command-center","System Status","Governance","Matters / Trusts","People / Fiduciaries","Documents / Exports","Archive / Continuity","Security / Access","Developer / Diagnostics",CERTIFIED_TAG]
missing = [x for x in required if x not in text]
fail += check("visual polish labels present", not missing, "all present" if not missing else ", ".join(missing))
group_idx = text.find("Institutional Command Groups")
legacy_idx = text.find("Legacy Compatibility Center")
fail += check("grouped command section appears before legacy compatibility center", group_idx != -1 and (legacy_idx == -1 or group_idx < legacy_idx), "grouped_index=" + str(group_idx) + "; legacy_index=" + str(legacy_idx))
code, status, err = git(["status", "--short"])
bad = [line for line in status.splitlines() if "data/trustee_app.db" in line or line.endswith(".db")]
fail += check("runtime database not modified", not bad, "none" if not bad else "\\n".join(bad))
print("")
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
