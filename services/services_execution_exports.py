import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime

from services.services_institutional_execution import get_execution_session


EXPORT_ROOT = Path("exports/execution_packages")


def _safe_write_json(path, data):
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _write_csv(path, rows):
    rows = rows or []
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    keys = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_execution_export_package(execution_id, generated_by="Institutional Operating System"):
    context = get_execution_session(execution_id)
    if not context or not context.get("session"):
        raise ValueError(f"Execution session not found: {execution_id}")

    session = context["session"]
    package_id = context.get("evidence_vault", {}).get("package", {}).get("package_id") or "PKG-" + execution_id.replace("EXE-", "")
    export_id = "EXP-" + execution_id.replace("EXE-", "")

    export_dir = EXPORT_ROOT / package_id / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "export_id": export_id,
        "package_id": package_id,
        "execution_id": execution_id,
        "generated_by": generated_by,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "export_version": "1.0",
        "export_status": "generated",
        "final_provenance_hash": session.get("final_hash"),
        "verification": context.get("verification"),
        "session": session,
        "evidence_vault": context.get("evidence_vault"),
    }

    files = {
        "metadata.json": metadata,
        "execution_session.json": session,
        "verification_report.json": context.get("verification") or {},
        "evidence_vault.json": context.get("evidence_vault") or {},
    }

    for filename, data in files.items():
        _safe_write_json(export_dir / filename, data)

    _write_csv(export_dir / "ledger.csv", context.get("ledger"))
    _write_csv(export_dir / "signatures.csv", context.get("signatures"))
    _write_csv(export_dir / "witness_notary_records.csv", context.get("participants"))
    _write_csv(export_dir / "seal_ledger.csv", context.get("seals"))
    _write_csv(export_dir / "archive_freezes.csv", context.get("freezes"))

    manifest_lines = [
        "INSTITUTIONAL EXECUTION EXPORT PACKAGE",
        f"Export ID: {export_id}",
        f"Package ID: {package_id}",
        f"Execution ID: {execution_id}",
        f"Generated: {metadata['generated_at']}",
        "",
        "FILES:",
    ]

    checksum_rows = []
    for path in sorted(export_dir.iterdir()):
        if path.is_file():
            digest = _sha256_file(path)
            checksum_rows.append((path.name, digest))
            manifest_lines.append(f"{path.name} | {digest}")

    (export_dir / "checksums.sha256").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in checksum_rows),
        encoding="utf-8"
    )

    (export_dir / "export_manifest.txt").write_text("\n".join(manifest_lines), encoding="utf-8")

    package_hash = _sha256_file(export_dir / "checksums.sha256")
    (export_dir / "package_hash.txt").write_text(package_hash, encoding="utf-8")

    return {
        "export_id": export_id,
        "package_id": package_id,
        "execution_id": execution_id,
        "export_dir": str(export_dir),
        "package_hash": package_hash,
        "file_count": len([p for p in export_dir.iterdir() if p.is_file()]),
        "generated_at": metadata["generated_at"],
        "status": "generated",
    }
