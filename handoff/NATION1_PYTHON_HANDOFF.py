"""
TRUSTEE APP — NATION 1 PYTHON HANDOFF
====================================

Paste the content of this file into the next Nation 1 project thread.

Locked status:
- Security dashboard layer built
- Lightweight route gating built
- Session-based login/logout built
- SQLite-backed auth built
- Hashed-password support built
- Admin / Trustee / Viewer accounts seeded and tested
- Session timeout phase started
- Step 42 complete: SESSION_TIMEOUT_SECONDS = 900 added to app.py

Immediate next action:
EXECUTE SQLITE SESSION TIMEOUT ENFORCEMENT LAYER
"""

HANDOFF = {
    "project": "trustee-app",
    "branch_context": "Nation 1 project continuation",
    "status": {
        "security_dashboard": "complete",
        "true_access_gating": "complete",
        "session_authentication": "complete",
        "sqlite_user_table": "complete",
        "hashed_passwords": "complete",
        "seeded_roles": ["Admin", "Trustee", "Viewer"],
        "session_timeout_config": "started",
        "step_42": "complete"
    },
    "next_objective": "SESSION TIMEOUT ENFORCEMENT",
    "exact_next_prompt": "EXECUTE SQLITE SESSION TIMEOUT ENFORCEMENT LAYER",
    "automan_mode": {
        "rules": [
            "One step at a time only",
            "No skipping",
            "Every step must include an exact command",
            "Every step must include a verification command",
            "Wait for CONFIRMED STEP X before moving on",
            "Do not redesign working systems",
            "Prefer minimal reversible edits",
            "Always compile after code edits",
            "Always test browser behavior after auth/session changes",
            "Commit and push after each stable layer"
        ],
        "method": [
            "1. Add or update data/config structure",
            "2. Add helper functions",
            "3. Connect helpers into app.py",
            "4. Verify with py_compile",
            "5. Run browser test",
            "6. Commit locally",
            "7. Pull/push to GitHub"
        ],
        "style": "surgical, deterministic, no guessing"
    },
    "current_auth_model": {
        "login_route": "/login",
        "logout_route": "/logout",
        "session_keys": ["role", "username"],
        "db_table": "app_users",
        "roles": {
            "admin": {"username": "admin", "password": "admin123"},
            "trustee": {"username": "trustee", "password": "trustee123"},
            "viewer": {"username": "viewer", "password": "viewer123"}
        }
    },
    "timeout_phase": {
        "completed": [
            "SESSION_TIMEOUT_SECONDS = 900 added to app.py"
        ],
        "remaining": [
            "track session['last_activity']",
            "enforce timeout on each request",
            "force logout after inactivity",
            "redirect to login with timeout message",
            "test inactivity behavior"
        ]
    }
}

if __name__ == "__main__":
    import pprint
    pprint.pp(HANDOFF)
