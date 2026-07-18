"""POST-V2-19-R1 transfer helper contract audit."""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DB = REPO / "trustee_app.db"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
APP = REPO / "app.py"


class AuditFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AuditFailure(message)


def pass_line(label: str, detail: object = "") -> None:
    print(f"PASS - {label}" + (f" | {detail}" if detail != "" else ""))


def direct_callers() -> list[dict[str, object]]:
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    callers: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Assign):
                continue
            if not isinstance(child.value, ast.Call):
                continue
            func = child.value.func
            if not isinstance(func, ast.Name) or func.id != "get_transfer_for_active_firm_or_404":
                continue
            target = child.targets[0] if child.targets else None
            if isinstance(target, ast.Tuple):
                names = [elt.id if isinstance(elt, ast.Name) else ast.dump(elt) for elt in target.elts]
            else:
                names = [ast.dump(target)] if target is not None else []
            callers.append({
                "function": node.name,
                "line": child.lineno,
                "expected_tuple_length": len(names),
                "variables": names,
            })
    return callers


def run_route_contract() -> None:
    before_sha = sha256(DB)
    with tempfile.TemporaryDirectory(prefix="post_v2_19_r1_transfer_", ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        db_copy = tmp_path / "transfer_contract.db"
        shutil.copy2(DB, db_copy)
        env = os.environ.copy()
        env["DB_PATH"] = str(db_copy)
        env["PYTHONPATH"] = str(REPO)
        env["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")
        code = r"""
from datetime import datetime, UTC
from app import app, get_transfer_for_active_firm_or_404

def set_session(client, firm_id):
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "admin" if firm_id == "FIRM-001" else "admin123"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["is_master_admin"] = True
        session["firm_id"] = firm_id
        session["last_activity"] = datetime.now(UTC).timestamp()

client = app.test_client()
unauth = client.get("/execution/transfers/T-0001")
assert unauth.status_code in {302, 303, 401, 403}, unauth.status_code

set_session(client, "FIRM-001")
with app.test_request_context("/execution/transfers/T-0001"):
    with client.session_transaction() as current:
        for key, value in current.items():
            from flask import session
            session[key] = value
    success = get_transfer_for_active_firm_or_404("T-0001")
assert isinstance(success, tuple) and len(success) == 2, success
assert success[0] is not None and success[1] is None, success
correct = client.get("/execution/transfers/T-0001")
assert correct.status_code == 200, correct.status_code
body = correct.get_data(as_text=True)
assert "T-0001" in body, "transfer identifier missing"

set_session(client, "FIRM-002")
with app.test_request_context("/execution/transfers/T-0001"):
    with client.session_transaction() as current:
        for key, value in current.items():
            from flask import session
            session[key] = value
    denied = get_transfer_for_active_firm_or_404("T-0001")
assert isinstance(denied, tuple) and len(denied) == 2, denied
assert denied[0] is None and isinstance(denied[1], tuple) and denied[1][1] == 403, denied
wrong = client.get("/execution/transfers/T-0001")
assert wrong.status_code == 403, wrong.status_code
assert "T-0001" not in wrong.get_data(as_text=True), "wrong-firm response leaked transfer ID"

missing = client.get("/execution/transfers/NO-SUCH-TRANSFER")
assert missing.status_code == 404, missing.status_code
print("transfer route contract PASS")
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=env, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise AuditFailure(result.stderr.strip() or result.stdout.strip())
        with sqlite3.connect(f"file:{db_copy}?mode=ro", uri=True) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check")
            fail_if(cur.fetchone()[0] != "ok", "temporary DB integrity failed")
        pass_line("temporary transfer route contract", result.stdout.strip())
    fail_if(sha256(DB) != before_sha or before_sha != DB_SHA, "normal database changed")
    pass_line("normal database unchanged")


def main() -> int:
    try:
        callers = direct_callers()
        fail_if(not callers, "no direct helper callers found")
        bad = [caller for caller in callers if caller["expected_tuple_length"] != 2]
        fail_if(bad, f"callers with non-two-value unpacking: {bad}")
        pass_line("direct helper callers", callers)
        pass_line("authoritative helper contract", "transfer, gate")
        run_route_contract()
        print("TRANSFER_DETAIL_ROUTE_PASS=True")
        print("TRANSFER_HELPER_CONTRACT_PASS=True")
        print("POST-V2-19-R1 TRANSFER HELPER CONTRACT AUDIT")
        print("RESULT: PASS")
    except AuditFailure as exc:
        print(f"FAIL - {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
