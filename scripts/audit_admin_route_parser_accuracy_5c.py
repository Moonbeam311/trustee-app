from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER = ROOT / "scripts" / "audit_admin_route_classification_4.py"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"
MARKER = "POST-V2-5C ROUTE PARSER ACCURACY REPAIR"

def git(args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + ": " + name + " — " + detail)
    return 0 if ok else 1

print("POST-V2-5C ADMIN ROUTE PARSER ACCURACY AUDIT")
print("=" * 72)

fail = 0
branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)
tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)
text = CLASSIFIER.read_text(encoding="utf-8", errors="ignore") if CLASSIFIER.exists() else ""
fail += check("classifier readable", bool(text), str(CLASSIFIER))
fail += check("5C marker present", MARKER in text, "present" if MARKER in text else "missing")
fail += check("inline multiline decorator repair present", "decorator_text = stripped" in text and "for continuation in lines[i+1:i+8]" in text, "present" if "decorator_text = stripped" in text and "for continuation in lines[i+1:i+8]" in text else "missing")

run = subprocess.run(["python", str(CLASSIFIER)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
output = run.stdout
bad = "@app.route( | certificate_workspace_governance_link_create" in output
fail += check("multiline route no longer misreported", not bad, "clean" if not bad else "misreported @app.route(")
fail += check("route classifier still passes", run.returncode == 0 and "RESULT: PASS" in output, "pass" if run.returncode == 0 and "RESULT: PASS" in output else "classifier failed")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\\n".join(bad_db))

print("")
print("SUMMARY")
print("-" * 72)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")
raise SystemExit(0 if fail == 0 else 1)
