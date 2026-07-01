"""
ICP-5D — Unified Certificate PDF Builder

Reusable ReportLab builder for institutional certificates.
Continuity remains the reference implementation.
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _table(data, col_widths=(150, 330), font_size=8):
    table = Table(data, colWidths=list(col_widths))
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2),
    ]))
    return table


def build_unified_certificate_pdf(certificate_object):
    """
    Build a governance-ready certificate PDF from the ICP-5C object model.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "UnifiedCertificateTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=1,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "UnifiedCertificateSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "UnifiedCertificateBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    )

    small_style = ParagraphStyle(
        "UnifiedCertificateSmall",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9,
    )

    identity = certificate_object.get("identity", {})
    status = certificate_object.get("status", {})
    governance = certificate_object.get("governance", {})
    verification = certificate_object.get("verification", {})
    chain = certificate_object.get("chain", {})
    timeline = certificate_object.get("timeline", {})
    events = timeline.get("events", [])

    certificate_id = identity.get("certificate_id")
    certificate_type = identity.get("certificate_type")
    verification_text = "VERIFIED" if verification.get("verified") else "REVIEW REQUIRED"

    chain_status = status.get("chain_status") or "Current"
    is_superseded = str(chain_status).lower() == "superseded"

    governance_status = (
        "SUPERSEDED — HISTORICAL RECORD — DO NOT USE AS CURRENT CERTIFICATE"
        if is_superseded
        else "CURRENT ACTIVE CERTIFICATE — VERIFIED — IMMUTABLE"
    )

    story = []

    story.append(Paragraph(f"INSTITUTIONAL {certificate_type.upper()} CERTIFICATE", title_style))
    story.append(Paragraph("Institutional Operating System", body_style))
    story.append(Spacer(1, 8))

    banner_table = Table([[governance_status]], colWidths=[480])
    banner_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 12))

    summary_data = [
        ["Certification ID", certificate_id],
        ["Certificate Type", certificate_type],
        ["Display Name", identity.get("display_name") or "—"],
        ["Module", identity.get("module_name") or "—"],
        ["Execution Session", identity.get("execution_id") or "—"],
        ["Certification Status", status.get("certification_status") or "—"],
        ["Verification Status", verification_text],
        ["Certificate Version", identity.get("certificate_version") or "—"],
    ]

    story.append(_table(summary_data))

    story.append(Paragraph("Institutional Governance Status", section_style))
    story.append(Paragraph(governance_status, body_style))

    lifecycle_data = [
        ["Lifecycle Status", status.get("lifecycle_status") or "Issued"],
        ["Issuance Authority", governance.get("issuance_authority") or "—"],
        ["Generation Engine", governance.get("generation_engine") or "—"],
        ["Issuance Reason", governance.get("issuance_reason") or "—"],
        ["Governance Policy", governance.get("governance_policy") or "—"],
        ["Retention Policy", governance.get("retention_policy") or "—"],
    ]

    story.append(Paragraph("Institutional Lifecycle", section_style))
    story.append(_table(lifecycle_data))

    chain_data = [
        ["Current Certificate", certificate_id],
        ["Supersedes", chain.get("supersedes_certification_id") or "—"],
        ["Superseded By", chain.get("superseded_by_certification_id") or "—"],
        ["Chain Status", str(chain_status).upper()],
    ]

    story.append(Paragraph("Certificate Chain", section_style))
    story.append(_table(chain_data))

    story.append(Paragraph("Lifecycle Event Summary", section_style))
    if events:
        for event in events:
            reason = event.get("event_reason") or event.get("event_notes") or "Recorded"
            story.append(Paragraph(f"• {event.get('event_type', 'Event')} — {reason}", body_style))
    else:
        story.append(Paragraph("No lifecycle events recorded.", body_style))

    provenance_data = [
        ["Generated By", "Institutional Operating System"],
        ["Generation Engine", governance.get("generation_engine") or "—"],
        ["Execution Session", identity.get("execution_id") or "—"],
        ["Hash Algorithm", verification.get("hash_algorithm") or "SHA-256"],
        ["Institution Status", verification_text],
        ["Certificate ID", certificate_id],
    ]

    story.append(Paragraph("Institutional Provenance", section_style))
    story.append(_table(provenance_data))

    validation_data = [
        ["Validation ID", verification.get("validation_id") or "—"],
        ["Expected Hash", verification.get("expected_hash") or "—"],
        ["Observed Hash", verification.get("observed_hash") or "—"],
    ]

    story.append(Paragraph("Validation Record", section_style))
    story.append(_table(validation_data, font_size=7))

    hash_data = [
        ["Dashboard Hash", verification.get("dashboard_hash") or "—"],
        ["Certificate Hash", verification.get("certificate_hash") or "—"],
        ["Stored Hash", verification.get("stored_hash") or "—"],
        ["Recalculated Hash", verification.get("recalculated_hash") or "—"],
    ]

    story.append(Paragraph("Tamper-Evident Certification Hashes", section_style))
    story.append(_table(hash_data, font_size=7))

    story.append(Paragraph("Certification Statement", section_style))
    story.append(Paragraph(
        "This certificate records an institutional certification generated from the "
        "Institutional Operating System. The certificate is append-only, lifecycle-governed, "
        "and subject to registry verification. Later institutional states require a successor "
        "certificate rather than alteration of this record.",
        body_style,
    ))

    story.append(Paragraph("Institutional Verification Notice", section_style))
    story.append(Paragraph(
        "This certificate remains immutable after issuance. If a successor certificate exists, "
        "this document remains part of the permanent institutional record and should be verified "
        "through the Institutional Certificate Registry.",
        body_style,
    ))

    story.append(Spacer(1, 12))

    seal_data = [
        ["Institutional Seal", "QR / Verification Placeholder", "Authorized Signature"],
        ["[ SEAL ]", "[ QR ]", "______________________________"],
    ]

    seal_table = Table(seal_data, colWidths=[160, 160, 160])
    seal_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 24),
        ("TOPPADDING", (0, 1), (-1, 1), 24),
    ]))

    story.append(seal_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Certificate ID: {certificate_id} | Verification: {verification_text}",
        small_style,
    ))

    doc.build(story)
    buffer.seek(0)

    return buffer
