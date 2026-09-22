"""Contract #9: read-only composition of existing professional-review facts."""

import sqlite3


LANES = (
    "INTAKE_PROFESSIONAL_REVIEW",
    "P09_AUTHORITY_PROFESSIONAL_REVIEW",
    "COMPLIANCE_REVIEW",
)


def _result(lane, state, evidence=None, missing=None, blockers=None):
    return {"lane": lane, "state": state, "evidence": evidence or [],
            "missing_evidence": missing or [], "blockers": blockers or []}


def evaluate_professional_review_boundary(
    db_path, *, firm_id, intake_id=None, program_id=None,
    compliance_review_id=None, required_lanes=None,
):
    """Compose review evidence without creating schema or changing records."""
    requested = list(dict.fromkeys(required_lanes or []))
    invalid = [lane for lane in requested if lane not in LANES]
    if invalid: raise ValueError("invalid_professional_review_lane")
    if not requested:
        return {"overall_state": "UNRESOLVED", "requested_lanes": [], "lane_results": [],
                "blockers": [], "evidence": [], "missing_evidence": ["required_lanes"]}
    connection = sqlite3.connect(str(db_path)); connection.row_factory = sqlite3.Row
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        results = []
        for lane in requested:
            if lane == "INTAKE_PROFESSIONAL_REVIEW":
                if "professional_review_issues" not in tables:
                    results.append(_result(lane, "UNRESOLVED", missing=["professional_review_issues_table"])); continue
                if not intake_id:
                    results.append(_result(lane, "UNRESOLVED", missing=["intake_id"])); continue
                rows = [dict(r) for r in connection.execute("SELECT * FROM professional_review_issues WHERE firm_id=? AND intake_id=? ORDER BY id", (firm_id,intake_id))]
                if not rows:
                    results.append(_result(lane, "UNRESOLVED", missing=["professional_review_issue"])); continue
                open_rows = [r for r in rows if r.get("status") in ("open", "escalated") or r.get("disposition") in (None, "", "escalated", "reopened", "source_reopened")]
                if open_rows:
                    results.append(_result(lane, "BLOCKED", evidence=rows, blockers=[r.get("issue_id") for r in open_rows])); continue
                completed = all(r.get("status") == "resolved" and r.get("disposition") in ("resolved", "accepted_risk") and r.get("resolved_at") and r.get("resolved_by") and r.get("resolved_capacity") not in (None, "", "System", "SYSTEM", "Source-Derived") for r in rows)
                results.append(_result(lane, "SATISFIED" if completed else "UNRESOLVED", evidence=rows, missing=[] if completed else ["explicit_human_professional_resolution"]))
            elif lane == "P09_AUTHORITY_PROFESSIONAL_REVIEW":
                if "hub_program_authority_reviews" not in tables:
                    results.append(_result(lane, "UNRESOLVED", missing=["hub_program_authority_reviews_table"])); continue
                if not program_id:
                    results.append(_result(lane, "UNRESOLVED", missing=["program_id"])); continue
                rows = [dict(r) for r in connection.execute("SELECT * FROM hub_program_authority_reviews WHERE program_id=? AND review_lane='PROFESSIONAL_REVIEW' ORDER BY created_at,review_id", (program_id,))]
                if not rows:
                    results.append(_result(lane, "UNRESOLVED", missing=["professional_authority_review"])); continue
                latest = {}
                for row in rows: latest[row["claim_id"]] = row
                current = list(latest.values())
                blocking = [r for r in current if r["review_state"] in ("DETECTED", "REVIEW_REQUIRED", "UNDER_REVIEW", "UNRESOLVED")]
                if blocking:
                    state = "REVIEW_REQUIRED" if all(r["review_state"] in ("DETECTED", "REVIEW_REQUIRED") for r in blocking) else "BLOCKED"
                    results.append(_result(lane, state, evidence=current, blockers=[r["review_id"] for r in blocking])); continue
                completed = all(r["review_state"] in ("RESOLVED", "CLOSED_NO_CONFLICT") and not r["machine_generated"] and str(r.get("professional_authority") or "").strip() for r in current)
                results.append(_result(lane, "SATISFIED" if completed else "UNRESOLVED", evidence=current, missing=[] if completed else ["explicit_non_machine_professional_completion"]))
            else:
                if "compliance_reviews" not in tables:
                    results.append(_result(lane, "UNRESOLVED", missing=["compliance_reviews_table"])); continue
                if not compliance_review_id:
                    results.append(_result(lane, "UNRESOLVED", missing=["compliance_review_id"])); continue
                row = connection.execute("SELECT * FROM compliance_reviews WHERE compliance_review_id=? AND firm_id=?", (compliance_review_id,firm_id)).fetchone()
                if not row:
                    results.append(_result(lane, "UNRESOLVED", missing=["compliance_review"])); continue
                review = dict(row); status = review.get("status")
                if status in ("draft", "opened", "under_review", "findings_issued", "remediation_required", "remediation_in_progress", "pending_verification", "pending_approval", "reopened"):
                    results.append(_result(lane, "REVIEW_REQUIRED", evidence=[review], blockers=[compliance_review_id])); continue
                # The existing workflow makes certification explicit. Approval alone is
                # not completion, and archival/supersession/cancellation are not guessed.
                if status in ("certified", "closed") and "compliance_review_certifications" in tables:
                    cert = connection.execute("SELECT * FROM compliance_review_certifications WHERE compliance_review_id=? AND certification_status='active' ORDER BY certified_at DESC,id DESC LIMIT 1", (compliance_review_id,)).fetchone()
                    if cert:
                        results.append(_result(lane, "SATISFIED", evidence=[review, dict(cert)])); continue
                results.append(_result(lane, "UNRESOLVED", evidence=[review], missing=["explicit_compliance_certification_completion"]))
        states = {r["state"] for r in results}
        overall = "BLOCKED" if "BLOCKED" in states else "REVIEW_REQUIRED" if "REVIEW_REQUIRED" in states else "UNRESOLVED" if "UNRESOLVED" in states else "SATISFIED"
        return {"overall_state": overall, "requested_lanes": requested, "lane_results": results,
                "blockers": [b for r in results for b in r["blockers"]],
                "evidence": [e for r in results for e in r["evidence"]],
                "missing_evidence": [m for r in results for m in r["missing_evidence"]]}
    finally:
        connection.close()
