from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def template(name):
    return (ROOT / "templates" / name).read_text(encoding="utf-8")


def route_block(function_name, next_route):
    start = APP.index(f"def {function_name}(trust_id):")
    end = APP.index(next_route, start)
    return APP[start:end]


def test_six_visible_stages_are_navigation_controls_with_required_routes():
    progress = template("_trust_formation_progress.html")
    assert progress.count('class="formation-stage ') == 6
    for number, label in enumerate((
        "Review / Edit Data", "Review Documents", "Final Document Surfaces",
        "Packet Preview", "Controlled Export", "Execution / Funding",
    ), start=1):
        assert f"{number}. {label}" in progress
    assert "trust_identity_edit" in progress
    assert "return_to='formation_hub'" in progress
    assert "#formation-document-review" in progress
    assert "trust_articles_output_surface" in progress
    assert "trust_packet_preview" in progress
    assert "trust_controlled_export_review" in progress
    assert "trust_execution_dashboard" in progress
    assert "trust_controlled_packet_export" not in progress


def test_controlled_export_review_route_is_get_only_scoped_and_readiness_driven():
    route = route_block(
        "trust_controlled_export_review",
        '@app.route("/trust/<trust_id>/packet-preview")',
    )
    assert '@app.route("/trust/<trust_id>/controlled-export-review")' in APP
    assert "methods=" not in APP[APP.rfind("@app.route", 0, APP.index("def trust_controlled_export_review")):APP.index("def trust_controlled_export_review")]
    assert "require_active_firm_trust_or_deny" in route
    assert '"trust_controlled_export_review": {"Admin", "Trustee"}' in APP
    assert "build_trust_preview_context" in route
    assert "build_trust_document_readiness" in route
    assert "build_trust_packet_readiness" in route
    assert '"trust_controlled_export_review.html"' in route
    assert "generate_controlled_trust_packet_zip" not in route
    assert "send_file" not in route


def test_review_page_requires_deliberate_confirmation_before_existing_zip_endpoint():
    review = template("trust_controlled_export_review.html")
    assert "Controlled Export Review / Confirmation" in review
    assert "trust_controlled_packet_export" in review
    assert 'type="checkbox"' in review
    assert "required" in review
    assert "I have reviewed the packet contents" in review
    assert review.index('type="checkbox"') < review.index("Confirm and Download Controlled Trust Packet")
    assert "Return to Packet Preview" in review
    assert "Return to Formation Hub" in review


def test_review_page_preserves_execution_funding_and_professional_boundaries():
    review = template("trust_controlled_export_review.html")
    assert "Export creates a controlled review packet." in review
    assert "Export does not itself execute the trust." in review
    assert "Export does not itself fund the trust or transfer property." in review
    assert "Export does not establish professional or legal validation." in review
    assert "Unresolved authority and professional-review matters remain governed separately." in review
    assert "Execution:</strong> Not Yet Completed" in review
    assert "Funding:</strong> Not Yet Completed" in review
    assert "Professional Legal Validation:</strong> Not Yet Completed" in review


def test_all_seven_packet_documents_use_existing_context_and_readiness():
    review = template("trust_controlled_export_review.html")
    for document in (
        "Declaration of Trust", "Certificate of Trust", "Articles of Trust",
        "Trustee Acceptance", "General Assignment", "Organizational Minutes",
        "Successor Trustee",
    ):
        assert document in review
    for key in (
        "articles", "trustee_acceptance", "general_assignment",
        "organizational_minutes", "successor_trustee",
    ):
        assert f"document_readiness.{key}.ready" in review
    assert "preview_context.trust_name" in review
    assert "preview_context.trust_id" in review
    assert "preview_context.trust_type" in review
    assert "packet_readiness.status_label" in review


def test_document_readiness_detail_matrix_contains_all_seven_documents_and_routes():
    hub = template("trust_formation_preview_hub.html")
    matrix = hub.split('<div class="section" id="formation-document-review">', 1)[1]
    matrix = matrix.split('<div class="section">', 1)[0]
    documents = (
        "Declaration of Trust", "Certificate of Trust", "Articles of Trust",
        "Trustee Acceptance", "General Assignment", "Organizational Minutes",
        "Successor Trustee",
    )
    assert "Document Readiness Detail Matrix" in matrix
    assert matrix.count("<tr>") - 1 == 7
    assert sum(matrix.count(f"<strong>{document}</strong>") for document in documents) == 7
    for document in documents:
        assert matrix.count(f"<strong>{document}</strong>") == 1
    assert "url_for('trust_declaration_output_surface', trust_id=trust.trust_id)" in matrix
    assert "url_for('trust_certificate_of_trust_output_surface', trust_id=trust.trust_id)" in matrix


def test_packet_preview_and_hub_are_review_first_not_direct_download():
    packet = template("trust_packet_preview.html")
    hub = template("trust_formation_preview_hub.html")
    assert "Review Controlled Export" in packet
    assert "trust_controlled_export_review" in packet
    assert "trust_controlled_packet_export" not in packet
    assert "Review Controlled Export" in hub
    assert "trust_controlled_export_review" in hub


def test_locked_completion_and_date_boundaries_are_unchanged():
    repaired = "\n".join((
        APP,
        template("_trust_formation_progress.html"),
        template("trust_controlled_export_review.html"),
        template("trust_packet_preview.html"),
        template("trust_formation_preview_hub.html"),
    ))
    assert "Task 36" not in repaired
    assert "PRI-5C42BFAE8B" not in repaired
    assert "governing_law') or preview_context.get('jurisdiction')" not in repaired
    assert "governing_law or preview_context.jurisdiction" not in repaired
    assert "1990-02-21" not in repaired
    assert "signature_date" not in repaired
