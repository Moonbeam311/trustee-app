from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def template(name):
    return (ROOT / "templates" / name).read_text(encoding="utf-8")


def route_block(function_name, next_route):
    start = APP.index(f"def {function_name}(trust_id):")
    end = APP.index(next_route, start)
    return APP[start:end]


def test_minutes_duplicate_removed_and_purpose_is_human_facing():
    html = template("trust_organizational_minutes_output_surface.html")
    phrase = "The undersigned acknowledge review of the trust’s initial formation information"
    assert html.count(phrase) == 1
    assert "preview_context.trust_purpose_display" in html
    assert "preview_context.trust_purpose or" not in html
    assert 'replace("_", " ").strip().title()' in APP


def test_effective_metadata_is_separate_from_blank_event_dates():
    joined = "\n".join(template(name) for name in (
        "trust_articles_preview.html", "trust_articles_output_surface.html",
        "trust_trustee_acceptance_preview.html", "trust_trustee_acceptance_output_surface.html",
        "trust_general_assignment_preview.html", "trust_general_assignment_output_surface.html",
        "trust_organizational_minutes_preview.html", "trust_organizational_minutes_output_surface.html",
        "trust_successor_trustee_preview.html", "trust_successor_trustee_output_surface.html",
    ))
    assert "Trust Effective / Reference Date" in joined
    for label in ("Document Execution Date", "Acceptance Date", "Assignment / Execution Date", "Resolution / Adoption Date"):
        assert label in joined
    assert '{{ trust.created_at or "[Date]" }}' not in joined
    assert '"execution_date", "signed_date", "created_at"' not in APP


def test_articles_beneficiary_wording_is_neutral_and_qualified():
    html = template("trust_articles_output_surface.html")
    assert "Recorded Beneficiary / Destination" in html
    assert "confirmed against the governing trust instrument" in html
    assert "<strong>Primary Beneficiary:</strong>" not in html


def test_trustee_acceptance_authority_execution_and_conditional_acknowledgment():
    joined = template("trust_trustee_acceptance_preview.html") + template("trust_trustee_acceptance_output_surface.html")
    assert "Appointment Source / Governing Instrument Reference" in joined
    assert "does not itself complete or make operative the acceptance" in joined
    assert "Acknowledgment / Notary / Witness, if required by governing law, governing instrument, or intended use" in joined
    assert "Witness / Acknowledgment (if required)" not in joined


def test_assignment_preview_matches_safeguard_and_has_property_reference():
    preview = template("trust_general_assignment_preview.html")
    assert "title, registration, custody, account ownership, third-party control" in preview
    assert "does not establish that any specific asset was transferred" in preview
    assert "Property / Schedule / Record Reference" in preview


def test_assignment_and_successor_routes_render_distinct_final_surfaces():
    assignment = route_block("trust_general_assignment_output_surface", '@app.route("/trust/<trust_id>/general-assignment-output-surface/pdf")')
    successor = route_block("trust_successor_trustee_output_surface", '@app.route("/trust/<trust_id>/successor-trustee-output-surface/pdf")')
    assert '"trust_general_assignment_output_surface.html"' in assignment
    assert '"trust_general_assignment_preview.html"' not in assignment
    assert '"trust_successor_trustee_output_surface.html"' in successor
    assert '"trust_successor_trustee_preview.html"' not in successor
    for name in ("trust_general_assignment_preview.html", "trust_general_assignment_output_surface.html", "trust_successor_trustee_preview.html", "trust_successor_trustee_output_surface.html"):
        assert "trust_formation_preview_hub" in template(name)


def test_minutes_are_proposed_not_adopted_by_generation():
    joined = template("trust_organizational_minutes_preview.html") + template("trust_organizational_minutes_output_surface.html")
    assert "proposed" in joined.lower()
    assert "Generation alone does not adopt a resolution" in joined
    assert "Action Type: __________________" in joined
    assert "Resolution / Adoption Date: __________________" in joined


def test_successor_designation_is_not_present_appointment():
    joined = template("trust_successor_trustee_preview.html") + template("trust_successor_trustee_output_surface.html")
    assert "Designation / Future Conditional Acceptance" in joined
    assert "not a presently effective appointment or acceptance" in joined
    assert "does not grant present authority" in joined
    assert "preview_context.successor_trustee_name" in joined
    assert "Acceptance Date: __________________" in joined
    assert "The undersigned accepts such appointment" not in joined
    assert "does not constitute acceptance of office" in joined


def test_export_history_requires_current_firm_scope_and_preserves_history():
    start = APP.index("def get_latest_export_for_trust")
    end = APP.index("def build_export_activity_entry", start)
    lookup = APP[start:end]
    assert "firm_id=None" in lookup
    assert 'entry.get("firm_id")' in lookup
    assert "continue" in lookup
    assert '"firm_id": preview_context.get("firm_id")' in APP
    assert 'get_latest_export_for_trust(trust_id, preview_context.get("firm_id"))' in APP
    assert "No current-firm packet export recorded." in template("trust_packet_preview.html")
    assert "delete" not in lookup.lower()


def test_optional_branding_is_advisory_and_not_legal_readiness():
    packet = template("trust_packet_preview.html")
    assert "Optional Branding (Advisory Only)" in packet
    assert "does not determine trust validity, execution ability, funding status, legal readiness, or professional approval" in packet


def test_final_surfaces_put_review_and_hub_navigation_before_print():
    for name in ("trust_articles_output_surface.html", "trust_trustee_acceptance_output_surface.html", "trust_general_assignment_output_surface.html", "trust_organizational_minutes_output_surface.html", "trust_successor_trustee_output_surface.html"):
        html = template(name)
        assert html.index("Review / Edit Trust Data") < html.index("window.print()")
        assert html.index("Return to Formation Hub") < html.index("window.print()")


def test_locked_boundaries_remain_source_only_and_pending():
    repaired = APP + template("trust_declaration_output_surface.html")
    assert "governing_law') or preview_context.get('jurisdiction')" not in repaired
    assert "governing_law or preview_context.jurisdiction" not in repaired
    assert "Not yet selected" in repaired
    completion_sources = APP + "\n".join(template(name) for name in (
        "trust_articles_output_surface.html", "trust_trustee_acceptance_output_surface.html",
        "trust_general_assignment_output_surface.html", "trust_organizational_minutes_output_surface.html",
        "trust_successor_trustee_output_surface.html", "trust_packet_preview.html",
    ))
    assert "PRI-5C42BFAE8B" not in completion_sources
    assert "Task 36" not in completion_sources
    assert "signature_date" not in completion_sources
