import importlib
import re
import sys
import time

from werkzeug.security import generate_password_hash


def _load_isolated_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "hos-brand-test.db"))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True, SECRET_KEY="hos-brand-isolated-test")
    return module.app


def _authenticate(client, role="Trustee"):
    with client.session_transaction() as session:
        session["username"] = "brand-test-operator"
        session["firm_id"] = "FIRM-BRAND"
        session["role"] = role
        session["last_activity"] = time.time()


def _rendered_section(body, pattern):
    match = re.search(pattern, body, flags=re.DOTALL)
    assert match, f"Rendered action section not found: {pattern}"
    return match.group(0)


def _action_count(body, destination, label):
    pattern = rf'<a\b[^>]*href="{re.escape(destination)}"[^>]*>\s*{re.escape(label)}\s*</a>'
    return len(re.findall(pattern, body))


def _csrf_token(body):
    match = re.search(r'name="_csrf_token" value="([^"]+)"', body)
    assert match, "Login CSRF token not rendered"
    return match.group(1)


def test_login_password_visibility_and_authentication_contract(monkeypatch, tmp_path):
    app = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    client = app.test_client()
    temporary_password = "Isolated-HOS-Test-Only!7"
    module.create_app_user({
        "user_id": module.get_next_user_id(),
        "username": "hos-login-fixture",
        "password_hash": generate_password_hash(temporary_password),
        "role_name": "Trustee",
        "status": "Active",
        "firm_id": "FIRM-HOS-TEST",
    })

    login_page = client.get("/login")
    body = login_page.get_data(as_text=True)
    assert login_page.status_code == 200
    assert re.search(r'<input\b[^>]*id="login-password"[^>]*type="password"[^>]*name="password"', body)
    assert re.search(r'<input\b[^>]*id="show-password"[^>]*type="checkbox"[^>]*aria-controls="login-password"', body)
    assert '<label for="show-password">Show password</label>' in body
    assert 'document.getElementById("login-password")' in body
    assert 'password.type = control.checked ? "text" : "password"' in body
    assert f'value="{temporary_password}"' not in body

    rejected = client.post("/login", data={
        "_csrf_token": _csrf_token(body),
        "username": "hos-login-fixture",
        "password": "incorrect-password",
    })
    assert rejected.status_code == 200
    assert "Invalid credentials" in rejected.get_data(as_text=True)
    assert client.get("/workspace").status_code in (302, 303)

    fresh_login = client.get("/login").get_data(as_text=True)
    accepted = client.post("/login", data={
        "_csrf_token": _csrf_token(fresh_login),
        "username": "hos-login-fixture",
        "password": temporary_password,
    })
    assert accepted.status_code in (302, 303)
    assert accepted.headers["Location"].endswith("/")

    authenticated = client.get("/").get_data(as_text=True)
    header = _rendered_section(authenticated, r'<header\b[^>]*class="brand-utility".*?</header>')
    hero_actions = _rendered_section(authenticated, r'<div\b[^>]*class="brand-primary-actions".*?</div>')
    assert _action_count(header, "/guide", "User Guide") == 1
    assert _action_count(header, "/logout", "Log Out") == 1
    assert _action_count(hero_actions, "/workspace", "Enter Hindsfoot OS") == 1
    assert _action_count(hero_actions, "/guide", "User Guide") == 0
    assert _action_count(hero_actions, "/logout", "Log Out") == 0

    logout = client.get("/logout")
    assert logout.status_code in (302, 303)
    assert logout.headers["Location"].endswith("/")
    public = client.get("/").get_data(as_text=True)
    assert _action_count(public, "/login", "Log In") == 1
    assert _action_count(public, "/logout", "Log Out") == 0


def test_public_introduction_has_approved_identity_and_safe_navigation(monkeypatch, tmp_path):
    app = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()

    response = client.get("/")
    body = response.get_data(as_text=True)
    header = _rendered_section(body, r'<header\b[^>]*class="brand-utility".*?</header>')
    hero_actions = _rendered_section(body, r'<div\b[^>]*class="brand-primary-actions".*?</div>')

    assert response.status_code == 200
    assert "/static/branding/hindsfoot_os_logo.png" in body
    assert "Hindsfoot OS — Sure Footing Across Generations" in body
    assert "The Personal Institutional Operating System" in body
    assert "Govern your affairs. Preserve your record. Carry your legacy forward." in body
    assert _action_count(header, "/guide", "User Guide") == 1
    assert _action_count(header, "/login", "Log In") == 0
    assert _action_count(hero_actions, "/login", "Log In") == 1
    assert _action_count(hero_actions, "/guide", "User Guide") == 0
    assert _action_count(body, "/guide", "User Guide") == 1
    assert _action_count(body, "/login", "Log In") == 1
    assert _action_count(body, "/logout", "Log Out") == 0
    assert "Existing Trusts" not in body
    assert client.get("/login").status_code == 200
    assert client.get("/static/branding/hindsfoot_os_logo.png").status_code == 200
    assert client.get("/static/branding/hindsfoot_os.css").status_code == 200
    assert client.get("/workspace").status_code in (302, 303)
    assert client.get("/guide").status_code in (302, 303)


def test_authenticated_introduction_exposes_continue_guide_and_logout(monkeypatch, tmp_path):
    app = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _authenticate(client)

    response = client.get("/")
    body = response.get_data(as_text=True)
    header = _rendered_section(body, r'<header\b[^>]*class="brand-utility".*?</header>')
    hero_actions = _rendered_section(body, r'<div\b[^>]*class="brand-primary-actions".*?</div>')

    assert response.status_code == 200
    assert _action_count(header, "/guide", "User Guide") == 1
    assert _action_count(header, "/logout", "Log Out") == 1
    assert _action_count(hero_actions, "/workspace", "Enter Hindsfoot OS") == 1
    assert _action_count(hero_actions, "/guide", "User Guide") == 0
    assert _action_count(hero_actions, "/logout", "Log Out") == 0
    assert _action_count(body, "/guide", "User Guide") == 1
    assert _action_count(body, "/logout", "Log Out") == 1
    assert _action_count(body, "/login", "Log In") == 0
    assert client.get("/workspace").status_code == 200
    assert client.get("/guide").status_code == 200


def test_existing_guide_policy_and_role_specific_continue_targets_are_preserved(monkeypatch, tmp_path):
    app = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    database = sys.modules["database.db"]
    client = app.test_client()

    anonymous_guide = client.get("/guide")
    assert anonymous_guide.status_code in (302, 303)
    assert "/login" in anonymous_guide.headers["Location"]

    database.ensure_role_tables()
    database.reseed_default_role_permissions()
    module.create_app_user({
        "user_id": module.get_next_user_id(),
        "username": "brand-test-operator",
        "password_hash": generate_password_hash("v3-admin-test-only"),
        "role_name": "Admin",
        "status": "Active",
        "firm_id": "FIRM-002",
    })

    _authenticate(client, "Admin")
    admin_intro = client.get("/").get_data(as_text=True)
    assert _action_count(admin_intro, "/guide", "User Guide") == 1
    assert _action_count(admin_intro, "/logout", "Log Out") == 1
    assert _action_count(admin_intro, "/admin", "Continue to Workspace") == 1
    assert _action_count(admin_intro, "/login", "Log In") == 0
    admin = client.get("/admin")
    assert admin.status_code == 200
    admin_body = admin.get_data(as_text=True)
    assert "Institutional Command Center" in admin_body
    assert _action_count(admin_body, "/", "Hindsfoot OS") == 1
    assert _action_count(admin_body, "/guide", "User Guide") == 1
    assert _action_count(admin_body, "/change_password", "Account Settings") == 1
    assert _action_count(admin_body, "/logout", "Log Out") == 1
    assert _action_count(admin_body, "/login", "Log In") == 0
    assert 'class="utility-nav"' in admin_body
    assert 'class="utility-logout" href="/logout"' in admin_body
    assert ".utility-nav { position:relative; z-index:2; display:flex; visibility:visible; opacity:1; width:100%; min-height:58px; height:auto; overflow:visible;" in admin_body
    assert ".utility-nav a { display:inline-flex; visibility:visible; opacity:1;" in admin_body
    assert ".utility-nav a:focus-visible" in admin_body
    assert ".utility-nav .utility-logout" in admin_body
    assert "flex-wrap:wrap" in admin_body
    assert "@media(max-width:640px)" in admin_body
    assert ".utility-nav a{flex:1 1 calc(50% - 10px);min-width:0}" in admin_body
    assert client.get("/").status_code == 200
    assert client.get("/admin").status_code == 200
    assert client.get("/guide").status_code == 200

    logout = client.get("/logout")
    assert logout.status_code in (302, 303)
    assert logout.headers["Location"].endswith("/")
    public = client.get("/").get_data(as_text=True)
    assert _action_count(public, "/guide", "User Guide") == 1
    assert _action_count(public, "/login", "Log In") == 1
    assert _action_count(public, "/logout", "Log Out") == 0
    assert client.get("/admin").status_code in (302, 303)
    _authenticate(client, "Trustee")
    assert client.get("/admin").status_code == 403
    client.get("/logout")
    _authenticate(client, "Viewer")
    assert 'href="/portfolio"' in client.get("/").get_data(as_text=True)
