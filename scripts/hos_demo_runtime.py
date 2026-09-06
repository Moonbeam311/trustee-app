#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5060)
    args = parser.parse_args()

    runtime_root = Path(args.runtime_root).expanduser().resolve()
    marker_path = runtime_root / ".hos_demo_runtime.json"

    if not marker_path.exists():
        raise SystemExit("HOS_DEMO_RUNTIME_MARKER=NOT_FOUND")

    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker.get("runtime_type") != "HOS-DEMO-1":
        raise SystemExit("HOS_DEMO_RUNTIME_TYPE=INVALID")
    if marker.get("state") != "READY":
        raise SystemExit("HOS_DEMO_RUNTIME_STATE=NOT_READY")

    db_path = Path(marker["database"]).resolve()
    uploads = Path(marker["uploads"]).resolve()
    exports = Path(marker["exports"]).resolve()

    if runtime_root not in db_path.parents:
        raise SystemExit("HOS_DEMO_DATABASE_ISOLATION=FAIL")

    secret = os.environ.get("HOS_DEMO_SECRET_KEY", "")
    if len(secret) < 24:
        raise SystemExit("HOS_DEMO_SECRET_KEY=REQUIRED")

    os.environ["DB_PATH"] = str(db_path)
    os.environ["UPLOAD_FOLDER"] = str(uploads)
    os.environ["EXPORT_ROOT"] = str(exports)
    os.environ["SECRET_KEY"] = secret

    # Bind every canonical non-request firm fallback to the isolated
    # demonstration firm before the Flask application is imported.
    os.environ["HOSTED_BOOTSTRAP_FIRM_ID"] = marker["firm_id"]

    # Hosted bootstrap/seed features stay off in the isolated demonstration process.
    for name in list(os.environ):
        if name.startswith("ENSURE_HOSTED_"):
            os.environ[name] = "0"

    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from app import app

    app.run(
        host=args.host,
        port=args.port,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
