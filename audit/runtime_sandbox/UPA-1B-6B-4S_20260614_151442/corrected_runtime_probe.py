
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

routes = json.loads(
    os.environ[
        "UPA_ROUTES_JSON"
    ]
)

own_markers = json.loads(
    os.environ[
        "UPA_OWN_MARKERS_JSON"
    ]
)

opposite_markers = json.loads(
    os.environ[
        "UPA_OPPOSITE_MARKERS_JSON"
    ]
)

result = {
    "firm_id": firm_id,
    "database_path": str(
        database_path
    ),
    "import_success": False,
    "binding_verified": False,
    "configured_cookie_name": None,
    "startup_error": None,
    "route_results": [],
    "opposite_marker_events": [],
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

    resolved_database_path = Path(
        str(db_module.DB_PATH)
    ).resolve()

    result["resolved_database_path"] = str(
        resolved_database_path
    )

    result["binding_verified"] = (
        resolved_database_path
        == database_path
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

    result["configured_cookie_name"] = (
        flask_app.config.get(
            "SESSION_COOKIE_NAME"
        )
    )

    client = flask_app.test_client()

    with client.session_transaction() as session:
        session["firm_id"] = firm_id
        session["active_firm_id"] = firm_id
        session["username"] = "admin123"
        session["user_id"] = "admin123"
        session["role"] = "admin"
        session["logged_in"] = True
        session["authenticated"] = True
        session["is_admin"] = True

    for route in routes:
        route_result = {
            "route": route,
            "status_code": None,
            "response_length": 0,
            "own_markers": [],
            "opposite_markers": [],
            "exception": None,
        }

        try:
            response = client.get(
                route,
                follow_redirects=True,
            )

            # Correct Flask/Werkzeug-compatible call.
            body = response.get_data(
                as_text=True
            )

            body_lower = body.lower()

            own_hits = [
                marker
                for marker in own_markers
                if marker.lower()
                in body_lower
            ]

            opposite_hits = [
                marker
                for marker in opposite_markers
                if marker.lower()
                in body_lower
            ]

            route_result.update({
                "status_code": (
                    response.status_code
                ),
                "response_length": len(
                    body
                ),
                "own_markers": own_hits,
                "opposite_markers": (
                    opposite_hits
                ),
            })

            if opposite_hits:
                result[
                    "opposite_marker_events"
                ].append({
                    "route": route,
                    "markers": opposite_hits,
                })

        except Exception as exc:
            route_result[
                "exception"
            ] = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

        result["route_results"].append(
            route_result
        )

except Exception as exc:
    result["startup_error"] = (
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
