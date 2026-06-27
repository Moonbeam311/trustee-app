
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

root = Path(
    os.environ["UPA_ROOT"]
).resolve()

database_path = Path(
    os.environ["UPA_DATABASE_PATH"]
).resolve()

firm_id = os.environ[
    "UPA_FIRM_ID"
]

result = {
    "firm_id": firm_id,
    "database_path": str(
        database_path
    ),
    "import_success": False,
    "binding_verified": False,
    "configured_cookie_name": None,
    "error": None,
}

try:
    sys.path.insert(
        0,
        str(root),
    )

    import app as app_module
    import database.db as db_module

    flask_app = getattr(
        app_module,
        "app",
        None,
    )

    if flask_app is None:
        raise RuntimeError(
            "app.py did not expose `app`."
        )

    result["import_success"] = True

    resolved = Path(
        str(db_module.DB_PATH)
    ).resolve()

    result[
        "resolved_database_path"
    ] = str(resolved)

    result["binding_verified"] = (
        resolved == database_path
    )

    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": os.environ[
            "SECRET_KEY"
        ],
        "SESSION_COOKIE_NAME": os.environ[
            "SESSION_COOKIE_NAME"
        ],
        "WTF_CSRF_ENABLED": False,
    })

    result[
        "configured_cookie_name"
    ] = flask_app.config.get(
        "SESSION_COOKIE_NAME"
    )

    # Create the test client and session only.
    # Do not request any routes.
    client = flask_app.test_client()

    with client.session_transaction() as session:
        session["firm_id"] = firm_id
        session["active_firm_id"] = (
            firm_id
        )
        session["username"] = (
            "admin123"
        )
        session["user_id"] = (
            "admin123"
        )
        session["role"] = "admin"
        session["logged_in"] = True
        session["authenticated"] = True
        session["is_admin"] = True

except Exception as exc:
    result["error"] = (
        f"{type(exc).__name__}: {exc}"
    )

    result["traceback"] = (
        traceback.format_exc()
    )

print(
    json.dumps(
        result,
        default=str,
    )
)
