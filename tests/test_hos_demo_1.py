import json
import os
import secrets
import sqlite3
import subprocess
import sys
from pathlib import Path

from werkzeug.security import check_password_hash

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "hos_demo_seed.json"
SEED = ROOT / "scripts" / "hos_demo_seed.py"
RUNTIME = ROOT / "scripts" / "hos_demo_runtime.py"


def demo_env():
    env = os.environ.copy()
    env["HOS_DEMO_ADMIN_PASSWORD"] = secrets.token_urlsafe(24)
    env["HOS_DEMO_TRUSTEE_PASSWORD"] = secrets.token_urlsafe(24)
    env["HOS_DEMO_VIEWER_PASSWORD"] = secrets.token_urlsafe(24)
    return env


def run_seed(runtime_root, env, reset=False):
    command = [
        sys.executable,
        str(SEED),
        "--runtime-root",
        str(runtime_root),
    ]
    if reset:
        command.append("--reset")
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_config_is_dedicated_synthetic_scope_without_plaintext_passwords():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert data["runtime_type"] == "HOS-DEMO-1"
    assert data["firm_id"].startswith("FIRM-DEMO-")
    assert data["firm_id"] not in {"FIRM-001", "FIRM-002"}
    assert {u["role_name"] for u in data["users"]} == {
        "Admin", "Trustee", "Viewer"
    }
    text = CONFIG.read_text(encoding="utf-8")
    assert '"password":' not in text
    assert "admin123" not in text
    assert "trustee123" not in text
    assert "viewer123" not in text


def test_seed_builds_only_isolated_demo_users(tmp_path):
    runtime_root = tmp_path / "demo"
    env = demo_env()
    result = run_seed(runtime_root, env)

    assert "HOS_DEMO_SEED=PASS" in result.stdout
    db_path = runtime_root / "trustee_app_demo.db"
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT username, password_hash, role_name, status, firm_id
        FROM app_users
        ORDER BY username
        """
    ).fetchall()
    conn.close()

    assert len(rows) == 3
    assert {row[2] for row in rows} == {"Admin", "Trustee", "Viewer"}
    assert {row[4] for row in rows} == {"FIRM-DEMO-001"}

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    by_username = {u["username"]: u for u in config["users"]}

    for username, password_hash, _, _, _ in rows:
        env_name = by_username[username]["password_env"]
        assert check_password_hash(password_hash, env[env_name])


def test_reset_is_bounded_to_marked_demo_runtime(tmp_path):
    runtime_root = tmp_path / "demo"
    env = demo_env()
    run_seed(runtime_root, env)

    junk = runtime_root / "synthetic-reset-proof.txt"
    junk.write_text("synthetic only", encoding="utf-8")
    assert junk.exists()

    run_seed(runtime_root, env, reset=True)

    assert not junk.exists()
    assert (runtime_root / "trustee_app_demo.db").exists()


def test_seed_never_imports_app_and_runtime_binds_roots_before_flask_exec():
    seed_text = SEED.read_text(encoding="utf-8")
    runtime_text = RUNTIME.read_text(encoding="utf-8")

    assert "import app" not in seed_text
    assert "from app" not in seed_text

    assert 'os.environ["DB_PATH"]' in runtime_text
    assert 'os.environ["UPLOAD_FOLDER"]' in runtime_text
    assert 'os.environ["EXPORT_ROOT"]' in runtime_text
    assert 'name.startswith("ENSURE_HOSTED_")' in runtime_text
    assert "from app import app" in runtime_text
    assert "app.run(" in runtime_text
    assert runtime_text.index('os.environ["DB_PATH"]') < runtime_text.index("from app import app")
    assert "os.execvpe" not in runtime_text


def test_seed_rejects_repository_runtime_root():
    result = subprocess.run(
        [
            sys.executable,
            str(SEED),
            "--runtime-root",
            str(ROOT),
        ],
        cwd=ROOT,
        env=demo_env(),
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "RUNTIME_ROOT_REPOSITORY_OVERLAP=PROHIBITED" in combined


def test_seed_adds_one_explicitly_synthetic_demo_trust(tmp_path):
    runtime_root = tmp_path / "demo-scenario"
    env = demo_env()

    result = run_seed(runtime_root, env)

    assert "DEMO_TRUST_ID=TR-DEMO-001" in result.stdout
    assert (
        "DEMO_SCENARIO_ID=HOS-DEMO-SYNTHETIC-001"
        in result.stdout
    )

    db_path = runtime_root / "trustee_app_demo.db"

    connection = sqlite3.connect(db_path)

    row = connection.execute(
        """
        SELECT
            trust_id,
            trust_name,
            status,
            owner_id,
            firm_id
        FROM trusts
        WHERE trust_id = ?
        """,
        ("TR-DEMO-001",),
    ).fetchone()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM trusts
        WHERE firm_id = ?
        """,
        ("FIRM-DEMO-001",),
    ).fetchone()[0]

    connection.close()

    assert row == (
        "TR-DEMO-001",
        "Demonstration Family Stewardship Trust",
        "Draft",
        "demo-admin",
        "FIRM-DEMO-001",
    )

    assert count == 1

    config = json.loads(
        CONFIG.read_text(encoding="utf-8")
    )

    notice = config["synthetic_notice"]

    assert "FICTIONAL DEMONSTRATION DATA ONLY" in notice
    assert config["scenario"]["trust"]["firm_id"] == "FIRM-DEMO-001"
    assert config["scenario"]["trust"]["owner_id"] == "demo-admin"

    config_text = CONFIG.read_text(encoding="utf-8")

    assert "Mishoe" not in config_text
    assert "FIRM-001" not in config_text
    assert "FIRM-002" not in config_text


def test_real_app_authentication_uses_demo_firm_scope(tmp_path):
    import textwrap

    runtime_root = tmp_path / "auth-runtime"
    env = demo_env()
    run_seed(runtime_root, env)

    db_path = runtime_root / "trustee_app_demo.db"

    # Synthetic negative fixture used only to prove cross-firm denial.
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        INSERT INTO trusts (
            trust_id,
            trust_name,
            status,
            owner_id,
            firm_id
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            "TR-DEMO-XFIRM",
            "Synthetic Cross-Firm Negative Fixture",
            "Draft",
            "synthetic-other-owner",
            "FIRM-DEMO-OTHER",
        ),
    )
    connection.commit()
    connection.close()

    probe_env = env.copy()
    probe_env["DB_PATH"] = str(db_path)
    probe_env["UPLOAD_FOLDER"] = str(runtime_root / "uploads")
    probe_env["EXPORT_ROOT"] = str(runtime_root / "exports")
    probe_env["SECRET_KEY"] = secrets.token_urlsafe(32)
    probe_env["HOSTED_BOOTSTRAP_FIRM_ID"] = "FIRM-DEMO-001"
    probe_env["ENSURE_HOSTED_ADMIN"] = "0"
    probe_env["ENSURE_HOSTED_TEST_TRUST"] = "0"
    probe_env["ENSURE_HOSTED_PORTFOLIO"] = "0"

    probe = textwrap.dedent(
        r"""
        import os
        from html.parser import HTMLParser

        import app as app_module

        app = app_module.app
        app.config["TESTING"] = True

        assert str(app_module.DB_PATH) == os.environ["DB_PATH"]
        assert str(app_module.UPLOAD_FOLDER) == os.environ["UPLOAD_FOLDER"]
        assert str(app_module.EXPORT_ROOT) == os.environ["EXPORT_ROOT"]

        class TokenParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.token = None

            def handle_starttag(self, tag, attrs):
                if tag != "input":
                    return
                values = dict(attrs)
                if values.get("name") == "_csrf_token":
                    self.token = values.get("value")

        cases = [
            (
                "demo-admin",
                os.environ["HOS_DEMO_ADMIN_PASSWORD"],
                "Admin",
            ),
            (
                "demo-trustee",
                os.environ["HOS_DEMO_TRUSTEE_PASSWORD"],
                "Trustee",
            ),
            (
                "demo-viewer",
                os.environ["HOS_DEMO_VIEWER_PASSWORD"],
                "Viewer",
            ),
        ]

        clients = {}

        for username, password, role in cases:
            client = app.test_client()

            login_page = client.get("/login")
            assert login_page.status_code == 200

            parser = TokenParser()
            parser.feed(login_page.get_data(as_text=True))
            assert parser.token

            response = client.post(
                "/login",
                data={
                    "username": username,
                    "password": password,
                    "_csrf_token": parser.token,
                },
                follow_redirects=False,
            )

            assert response.status_code in (302, 303)

            with client.session_transaction() as session:
                assert session.get("username") == username
                assert session.get("role") == role
                assert session.get("firm_id") == "FIRM-DEMO-001"

            clients[role] = client

        own = clients["Admin"].get("/trust/TR-DEMO-001")
        assert own.status_code == 200

        cross = clients["Admin"].get("/trust/TR-DEMO-XFIRM")
        assert cross.status_code in (403, 404)

        viewer_denied = clients["Viewer"].get("/admin/audit-log")
        assert viewer_denied.status_code == 403

        print("REAL_LOGIN_ADMIN=PASS")
        print("REAL_LOGIN_TRUSTEE=PASS")
        print("REAL_LOGIN_VIEWER=PASS")
        print("SESSION_FIRM_SCOPE=FIRM-DEMO-001")
        print("CROSS_FIRM_TRUST_DENIAL=PASS")
        print("VIEWER_RESTRICTED_ADMIN_ROUTE=PASS")
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=ROOT,
        env=probe_env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, (
        result.stdout + "\n" + result.stderr
    )

    assert "REAL_LOGIN_ADMIN=PASS" in result.stdout
    assert "REAL_LOGIN_TRUSTEE=PASS" in result.stdout
    assert "REAL_LOGIN_VIEWER=PASS" in result.stdout
    assert "SESSION_FIRM_SCOPE=FIRM-DEMO-001" in result.stdout
    assert "CROSS_FIRM_TRUST_DENIAL=PASS" in result.stdout
    assert "VIEWER_RESTRICTED_ADMIN_ROUTE=PASS" in result.stdout


def test_demo_runtime_launcher_boots_real_flask_app(tmp_path):
    import socket
    import time
    import urllib.request

    runtime_root = tmp_path / "launcher-runtime"
    env = demo_env()
    run_seed(runtime_root, env)

    runtime_env = env.copy()
    runtime_env["HOS_DEMO_SECRET_KEY"] = secrets.token_urlsafe(32)

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    log_path = tmp_path / "launcher-runtime.log"
    log_handle = log_path.open(
        "w",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [
            sys.executable,
            str(RUNTIME),
            "--runtime-root",
            str(runtime_root),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=runtime_env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )

    status = None

    try:
        url = f"http://127.0.0.1:{port}/login"

        # Bounded maximum wait: approximately 60 seconds.
        for _ in range(80):
            if process.poll() is not None:
                break

            try:
                with urllib.request.urlopen(
                    url,
                    timeout=0.5,
                ) as response:
                    status = response.status
                    break
            except Exception:
                time.sleep(0.25)

    finally:
        if process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

        log_handle.close()

    if status != 200:
        output = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        raise AssertionError(
            "runtime did not become ready; "
            f"status={status}; output={output}"
        )

    assert status == 200
