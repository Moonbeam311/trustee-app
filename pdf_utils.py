from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from flask import make_response

PAGE_WIDTH, PAGE_HEIGHT = LETTER

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="AppTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    ))
    return styles

def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#111827"))
    canvas.drawString(doc.leftMargin, PAGE_HEIGHT - 0.55 * inch, "Trustee App Report")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 0.45 * inch, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

def _safe(v):
    if v is None:
        return ""
    return str(v)

def _money(v):
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return _safe(v)

def _table(data, col_widths=None, header_bg="#e5e7eb", body_bg="#ffffff"):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor(body_bg)),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t

def build_pdf_response(filename, story):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.7 * inch,
        title=filename,
        author="Trustee App",
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return response

def trust_summary_story(trust, properties, accounts, documents, entries):
    styles = _styles()
    story = []

    trust_name = _safe((trust or {}).get("trust_name")) or "Trust Summary"
    trust_id = _safe((trust or {}).get("trust_id"))

    story.append(Paragraph(f"{trust_name}", styles["AppTitle"]))
    story.append(Paragraph(
        f"Trust ID: {trust_id} &nbsp;&nbsp;&nbsp; Status: {_safe((trust or {}).get('status'))} &nbsp;&nbsp;&nbsp; Effective Date: {_safe((trust or {}).get('effective_date'))}",
        styles["Meta"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Overview", styles["SectionHeader"]))
    overview_rows = [
        ["Field", "Value"],
        ["Short Name", _safe((trust or {}).get("short_name"))],
        ["Jurisdiction", _safe((trust or {}).get("jurisdiction"))],
        ["Trust Type", _safe((trust or {}).get("trust_type"))],
        ["Trust Purpose", _safe((trust or {}).get("trust_purpose"))],
        ["Accounting Method", _safe((trust or {}).get("accounting_method"))],
        ["Workflow Mode", _safe((trust or {}).get("workflow_mode"))],
        ["Settlor", _safe((trust or {}).get("settlor_name"))],
        ["Trustee", _safe((trust or {}).get("trustee_name"))],
        ["Successor Trustee", _safe((trust or {}).get("successor_trustee_name"))],
        ["Beneficiary", _safe((trust or {}).get("beneficiary_name"))],
    ]
    story.append(_table(overview_rows, col_widths=[2.0 * inch, 4.7 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Portfolio Snapshot", styles["SectionHeader"]))
    snapshot_rows = [
        ["Metric", "Count"],
        ["Properties", str(len(properties or []))],
        ["Accounts", str(len(accounts or []))],
        ["Documents", str(len(documents or []))],
        ["Ledger Entries", str(len(entries or []))],
    ]
    story.append(_table(snapshot_rows, col_widths=[3.0 * inch, 1.3 * inch]))
    story.append(Spacer(1, 10))

    if properties:
        story.append(Paragraph("Properties", styles["SectionHeader"]))
        prop_rows = [["Property ID", "Name", "Type", "Status"]]
        for p in properties[:20]:
            prop_rows.append([
                _safe(p.get("property_id")),
                _safe(p.get("property_name")),
                _safe(p.get("property_type") or p.get("asset_class")),
                _safe(p.get("status")),
            ])
        story.append(_table(prop_rows, col_widths=[1.0 * inch, 2.9 * inch, 1.4 * inch, 1.3 * inch]))
        story.append(Spacer(1, 10))

    if accounts:
        story.append(Paragraph("Accounts", styles["SectionHeader"]))
        acct_rows = [["Account ID", "Institution", "Type", "Label"]]
        for a in accounts[:20]:
            acct_rows.append([
                _safe(a.get("account_id")),
                _safe(a.get("institution")),
                _safe(a.get("account_type")),
                _safe(a.get("account_label")),
            ])
        story.append(_table(acct_rows, col_widths=[1.0 * inch, 2.4 * inch, 1.4 * inch, 1.8 * inch]))
        story.append(Spacer(1, 10))

    if documents:
        story.append(Paragraph("Documents", styles["SectionHeader"]))
        doc_rows = [["Document ID", "Category", "Title", "Filename"]]
        for d in documents[:20]:
            doc_rows.append([
                _safe(d.get("document_id")),
                _safe(d.get("document_category")),
                _safe(d.get("document_title")),
                _safe(d.get("original_filename")),
            ])
        story.append(_table(doc_rows, col_widths=[0.9 * inch, 1.4 * inch, 2.2 * inch, 2.2 * inch]))
        story.append(Spacer(1, 10))

    if entries:
        story.append(Paragraph("Recent Ledger Entries", styles["SectionHeader"]))
        entry_rows = [["Entry ID", "Type", "Date", "Amount", "Description"]]
        for e in entries[:20]:
            entry_rows.append([
                _safe(e.get("entry_id")),
                _safe(e.get("entry_type")),
                _safe(e.get("entry_date")),
                _money(e.get("amount")),
                _safe(e.get("description")),
            ])
        story.append(_table(entry_rows, col_widths=[0.8 * inch, 1.1 * inch, 1.1 * inch, 1.0 * inch, 2.7 * inch]))

    return story

def k1_readiness_story(trust, tax_year, summary, totals, beneficiary_totals, beneficiaries, distributions):
    styles = _styles()
    story = []

    trust_name = _safe((trust or {}).get("trust_name")) or "K-1 Readiness Report"
    trust_id = _safe((trust or {}).get("trust_id"))

    story.append(Paragraph(f"K-1 Readiness Report", styles["AppTitle"]))
    story.append(Paragraph(
        f"Trust: {trust_name} &nbsp;&nbsp;&nbsp; Trust ID: {trust_id} &nbsp;&nbsp;&nbsp; Tax Year: {_safe(tax_year)}",
        styles["Meta"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Readiness Summary", styles["SectionHeader"]))
    summary_rows = [["Field", "Value"]]
    if isinstance(summary, dict):
        for k, v in summary.items():
            summary_rows.append([_safe(k).replace("_", " ").title(), _safe(v)])
    if len(summary_rows) == 1:
        summary_rows.append(["Status", "No readiness summary available"])
    story.append(_table(summary_rows, col_widths=[3.0 * inch, 3.7 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Totals", styles["SectionHeader"]))
    totals_rows = [["Metric", "Value"]]
    if isinstance(totals, dict):
        for k, v in totals.items():
            label = _safe(k).replace("_", " ").title()
            value = _money(v) if "amount" in _safe(k).lower() or "total" in _safe(k).lower() else _safe(v)
            totals_rows.append([label, value])
    if len(totals_rows) == 1:
        totals_rows.append(["Totals", "No totals available"])
    story.append(_table(totals_rows, col_widths=[3.0 * inch, 2.0 * inch]))
    story.append(Spacer(1, 10))

    if beneficiary_totals:
        story.append(Paragraph("Beneficiary Totals", styles["SectionHeader"]))
        bt_rows = [["Beneficiary", "Gross", "Taxable", "Principal"]]
        for row in beneficiary_totals[:30]:
            bt_rows.append([
                _safe(row.get("full_name") or row.get("beneficiary_name") or row.get("beneficiary_id")),
                _money(row.get("gross_total")),
                _money(row.get("taxable_total")),
                _money(row.get("principal_total")),
            ])
        story.append(_table(bt_rows, col_widths=[2.8 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch]))
        story.append(Spacer(1, 10))

    if beneficiaries:
        story.append(Paragraph("Beneficiaries", styles["SectionHeader"]))
        b_rows = [["Beneficiary ID", "Name", "Type", "Active"]]
        for b in beneficiaries[:30]:
            b_rows.append([
                _safe(b.get("beneficiary_id")),
                _safe(b.get("full_name")),
                _safe(b.get("beneficiary_type")),
                _safe(b.get("is_active")),
            ])
        story.append(_table(b_rows, col_widths=[1.2 * inch, 2.8 * inch, 1.3 * inch, 0.8 * inch]))
        story.append(Spacer(1, 10))

    if distributions:
        story.append(Paragraph("Recent Distributions", styles["SectionHeader"]))
        d_rows = [["Distribution ID", "Beneficiary", "Date", "Gross", "Type"]]
        for d in distributions[:30]:
            d_rows.append([
                _safe(d.get("distribution_id")),
                _safe(d.get("beneficiary_id")),
                _safe(d.get("distribution_date")),
                _money(d.get("gross_amount")),
                _safe(d.get("distribution_type")),
            ])
        story.append(_table(d_rows, col_widths=[1.1 * inch, 2.0 * inch, 1.1 * inch, 1.0 * inch, 1.6 * inch]))

    return story
