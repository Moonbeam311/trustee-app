from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def template(name):
    return (ROOT / "templates" / name).read_text(encoding="utf-8")


def test_formation_hub_has_real_shared_progress_and_edit_navigation():
    hub = template("trust_formation_preview_hub.html")
    progress = template("_trust_formation_progress.html")
    assert '_trust_formation_progress.html' in hub
    assert "Review / Edit Trust Data" in hub
    assert "trust_identity_edit" in hub
    assert "trust_packet_preview" in progress
    assert "trust_execution_dashboard" in progress
    assert "#formation-document-review" in progress


def test_packet_preview_has_progress_edit_and_existing_declaration_certificate_routes():
    packet = template("trust_packet_preview.html")
    assert '_trust_formation_progress.html' in packet
    assert "Review / Edit Trust Data" in packet
    for label in ("Declaration of Trust", "Certificate of Trust"):
        assert label in packet
    for endpoint in (
        "trust_declaration_output_surface",
        "trust_declaration_output_surface_pdf",
        "trust_certificate_of_trust_output_surface",
        "trust_certificate_of_trust_output_surface_pdf",
    ):
        assert endpoint in packet
    assert "seven formation document PDFs" in packet


def test_hub_integrates_declaration_certificate_and_safe_governance_status():
    hub = template("trust_formation_preview_hub.html")
    assert "Declaration of Trust" in hub
    assert "Certificate of Trust" in hub
    assert "Formation Record:" in hub and "Complete" in hub
    assert "Execution:</strong> Not Yet Completed" in hub
    assert "Funding:</strong> Not Yet Completed" in hub
    assert "Professional Legal Validation:</strong> Not Yet Completed" in hub
    assert "Internal Authority Review" not in hub


def test_identity_edit_updates_existing_scoped_trust_without_creation():
    start = APP.index("def trust_identity_edit(trust_id):")
    end = APP.index('@app.route("/trust/<trust_id>/successor-trustee-preview")', start)
    route = APP[start:end]
    assert "get_trust_by_id_in_scope" in route
    assert "update_trust_fields_in_scope" in route
    assert "resolve_post_save_return" in route
    assert "create_trust_record" not in route
    assert '"firm_id"' not in route.split("update_trust_fields_in_scope", 1)[1]
    assert '"owner_id"' not in route.split("update_trust_fields_in_scope", 1)[1]


def test_existing_certificate_generator_and_routes_are_reused_without_new_table():
    assert "def generate_certificate_of_trust_pdf" in APP
    assert "generate_certificate_of_trust_pdf(trust, preview_context)" in APP
    assert "def trust_certificate_of_trust_output_surface" in APP
    assert "CREATE TABLE CERTIFICATE" not in APP.upper()


def test_governing_law_never_falls_back_to_jurisdiction_on_repaired_surfaces():
    repaired = APP + template("trust_declaration_output_surface.html")
    assert "governing_law') or preview_context.get('jurisdiction')" not in repaired
    assert "governing_law or preview_context.jurisdiction" not in repaired
    assert "Not yet selected" in repaired


def test_assignment_safeguard_names_and_blank_execution_lines():
    html = template("trust_general_assignment_output_surface.html")
    assert "does not by itself establish that title, registration, custody, account ownership, or third-party control has changed" in html
    assert "preview_context.grantor_name" in html
    assert "preview_context.trustee_name" in html
    assert "Assignor Signature" in html and "Date" in html
    assert "signature_date" not in html


def test_successor_is_future_conditional_and_not_present_authority():
    html = template("trust_successor_trustee_output_surface.html")
    assert "succession-triggering event" in html
    assert "does not grant present authority" in html
    assert "authority arises only under the governing instrument" in html
    assert "preview_context.successor_trustee_name" in html


def test_internal_development_wording_removed_from_repaired_surfaces():
    names = (
        "trust_formation_preview_hub.html", "trust_packet_preview.html",
        "trust_articles_preview.html", "trust_articles_output_surface.html",
        "trust_trustee_acceptance_preview.html", "trust_trustee_acceptance_output_surface.html",
        "trust_general_assignment_preview.html", "trust_general_assignment_output_surface.html",
        "trust_organizational_minutes_preview.html", "trust_organizational_minutes_output_surface.html",
        "trust_successor_trustee_preview.html", "trust_successor_trustee_output_surface.html",
    )
    text = "\n".join(template(name).lower() for name in names)
    for phrase in (
        "bounded final", "bounded document pattern", "preview-first trust formation layer",
        "deeper wizard integration", "package-wide automation remains deferred",
        "later controlled output generation",
    ):
        assert phrase not in text


def test_missing_timestamps_are_explained():
    packet = template("trust_packet_preview.html")
    assert 'or "—"' not in packet
    assert "Not recorded" in packet
