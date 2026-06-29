from datetime import datetime


def _package_id(execution_id):
    return "PKG-" + str(execution_id).replace("EXE-", "")


def _verification_id(execution_id):
    return "VRF-" + str(execution_id).replace("EXE-", "")


def _check(name, source, passed, detail=""):
    return {
        "name": name,
        "source": source,
        "result": "PASS" if passed else "FAIL",
        "passed": bool(passed),
        "detail": detail,
    }


def verify_execution_package(execution_id, context):
    session = context.get("session") or {}
    signatures = context.get("signatures") or []
    participants = context.get("participants") or []
    seals = context.get("seals") or []
    ledger = context.get("ledger") or []
    freezes = context.get("freezes") or []
    vault = context.get("evidence_vault") or {}
    package = vault.get("package") or {}

    ledger_sequences = [int(e.get("event_sequence") or 0) for e in ledger]
    expected_sequence = list(range(1, len(ledger_sequences) + 1))

    checks = [
        _check("Execution Session Exists", "Execution Session", bool(session), session.get("execution_id", "")),
        _check("Ceremony Finalized", "Execution Session", session.get("ceremony_status") == "finalized", session.get("ceremony_status", "")),
        _check("Archive Frozen", "Archive Layer", session.get("archive_freeze_status") == "frozen", session.get("archive_freeze_status", "")),
        _check("Final Provenance Hash Exists", "Provenance Layer", bool(session.get("final_hash")), session.get("final_hash", "")),
        _check("Signature Records Present", "Signature Ledger", len(signatures) > 0, f"{len(signatures)} signature records"),
        _check("Witness / Notary Records Present", "Witness Ledger", len(participants) > 0, f"{len(participants)} participant records"),
        _check("Institutional Seal Present", "Seal Ledger", len(seals) > 0, f"{len(seals)} seal records"),
        _check("Ledger Events Present", "Execution Ledger", len(ledger) > 0, f"{len(ledger)} ledger events"),
        _check("Ledger Sequence Continuous", "Execution Ledger", ledger_sequences == expected_sequence, f"{ledger_sequences}"),
        _check("Archive Freeze Record Present", "Archive Freeze", len(freezes) > 0, f"{len(freezes)} freeze records"),
        _check("Evidence Package Registered", "Evidence Vault", bool(package.get("package_id")), package.get("package_id", "")),
        _check("Vault Custodian Assigned", "Evidence Vault", bool(package.get("custodian")), package.get("custodian", "")),
    ]

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    verified = passed == total
    score = round((passed / total) * 100) if total else 0

    return {
        "verification_id": _verification_id(execution_id),
        "package_id": package.get("package_id") or _package_id(execution_id),
        "execution_id": execution_id,
        "verified": verified,
        "result": "PASS" if verified else "FAIL",
        "score": score,
        "checks_passed": passed,
        "checks_total": total,
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "verified_by": "Institutional Verification Engine",
        "verification_standard": "Institutional Execution Integrity Standard v1",
        "checks": checks,
    }
