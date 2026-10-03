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
    assert "update_trust_fields_with_provenance_in_scope" in route
    assert 'revision_basis="trust_identity_correction"' in route
    assert 'provenance="app:trust_identity_edit"' in route
    assert 'decision_origin="OPERATOR_OR_FIDUCIARY"' in route
    assert "human_confirmed=True" in route
    assert "resolve_post_save_return" in route
    assert "create_trust_record" not in route
    assert '"firm_id"' not in route.split(
        "update_trust_fields_with_provenance_in_scope", 1
    )[1]
    assert '"owner_id"' not in route.split(
        "update_trust_fields_with_provenance_in_scope", 1
    )[1]


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


def test_controlled_packet_schedule_a_is_conditional_prospective_attachment():
    start = APP.index(
        "def build_controlled_packet_schedule_a_documents"
    )
    end = APP.index(
        "def get_support_doc_by_category",
        start,
    )
    packet_block = APP[start:end]

    route_start = APP.index(
        "def trust_controlled_packet_export(trust_id):"
    )
    route_end = APP.index(
        '@app.route("/trust/<trust_id>/controlled-export-review")',
        route_start,
    )
    export_route = APP[route_start:route_end]

    assert "get_properties_by_trust_id" in packet_block
    assert "get_property_finalization_snapshot" in packet_block
    assert "build_schedule_a_draft_text" in packet_block

    assert "DRAFT_PROSPECTIVE" in packet_block
    assert "NONE_INFERRED" in packet_block
    assert "not a formation document" in packet_block
    assert "_Schedule_A_" in packet_block

    assert (
        "schedule_a_documents = "
        "build_controlled_packet_schedule_a_documents"
        in export_route
    )
    assert (
        "schedule_a_documents=schedule_a_documents"
        in export_route
    )

    # The established formation set remains seven documents.
    assert (
        "seven formation document PDFs"
        in template("trust_packet_preview.html")
    )

    # Packet preparation must remain read-only with respect to
    # transfer / execution / funding lifecycle state.
    for forbidden in (
        "INSERT INTO transfers",
        "UPDATE transfers",
        "create_transfer",
        "finalize_transfer",
        "record_trust_asset_control_determination",
    ):
        assert forbidden not in packet_block
