from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADMIN_TEMPLATE = ROOT / "templates" / "admin_index.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED = "607eb174354510b64804f8dd8e4b87756f25f366"

MARKER = "POST-V2-9A SYSTEM CONTROL WARNING LABEL PATCH"
BACKUP_ROUTE = "/admin/backup/database.zip"
BACKUP_TEXT = "Download Database Backup ZIP"
WARNING = "MEDIUM RISK — DOWNLOADS LIVE DATABASE COPY"

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

print("POST-V2-9A ADMIN SYSTEM CONTROL WARNING LABEL AUDIT")
print("=" * 72)

fail = 0

branch, err = git(["branch", "--show-current"])
fail += check("branch allowed", branch == "post-v2-planning", branch or err)

tag, err = git(["rev-parse", CERTIFIED_TAG + "^{commit}"])
fail += check("certified tag protected", tag == EXPECTED, tag or err)

text = ADMIN_TEMPLATE.read_text(encoding="utf-8", errors="ignore") if ADMIN_TEMPLATE.exists() else ""
fail += check("admin template readable", bool(text), str(ADMIN_TEMPLATE))

fail += check("9A marker present", MARKER in text, "present" if MARKER in text else "missing")
fail += check("backup ZIP route retained", BACKUP_ROUTE in text, "present" if BACKUP_ROUTE in text else "missing")
fail += check("backup ZIP link text retained", BACKUP_TEXT in text, "present" if BACKUP_TEXT in text else "missing")
fail += check("medium-risk warning label present", WARNING in text, "present" if WARNING in text else "missing")

warning_count = text.count(WARNING)
fail += check("warning label count calibrated", warning_count == 1, "count=" + str(warning_count))

diff_app, err = git(["diff", "--", "app.py"])
fail += check("no route logic changes in app.py", not diff_app, "none" if not diff_app else "app.py diff detected")

status, err = git(["status", "--short"])
bad_db = [x for x in status.splitlines() if "data/trustee_app.db" in x or x.endswith(".db")]
fail += check("runtime database not modified", not bad_db, "none" if not bad_db else "\n".join(bad_db))

print("")
print("WARNING LABEL INVENTORY")
print("-" * 72)
print("backup_route:", BACKUP_ROUTE)
print("warning_label:", WARNING)
print("warning_count:", warning_count)

print("")
print("SUMMARY")
print("-" * 72)
print("checks_failed:", fail)
print("RESULT: PASS" if fail == 0 else "RESULT: FAIL")

raise SystemExit(0 if fail == 0 else 1)
