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

def fiduciary_report_story(trusts, fiduciaries, selected_trust_id=None):
    styles = _styles()
    story = []

    trust_lookup = {str(t.get("trust_id")): t for t in (trusts or [])}
    filtered = fiduciaries or []
    subtitle = "All Fiduciaries"

    if selected_trust_id:
        filtered = [f for f in filtered if str(f.get("trust_id")) == str(selected_trust_id)]
        trust_name = _safe((trust_lookup.get(str(selected_trust_id)) or {}).get("trust_name")) or str(selected_trust_id)
        subtitle = f"Trust-Specific Fiduciaries: {trust_name}"

    story.append(Paragraph("Fiduciary Report", styles["AppTitle"]))
    story.append(Paragraph(subtitle, styles["Meta"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Summary", styles["SectionHeader"]))
    summary_rows = [
        ["Metric", "Value"],
        ["Selected Trust", _safe(selected_trust_id) if selected_trust_id else "All Trusts"],
        ["Fiduciary Count", str(len(filtered))],
    ]
    story.append(_table(summary_rows, col_widths=[2.8 * inch, 3.2 * inch]))
    story.append(Spacer(1, 10))

    rows = [["Fiduciary ID", "Full Name", "Role", "Trust", "Status", "Effective"]]
    for f in filtered[:100]:
        trust_id = _safe(f.get("trust_id"))
        trust_name = _safe((trust_lookup.get(trust_id) or {}).get("trust_name")) or trust_id
        rows.append([
            _safe(f.get("fiduciary_id")),
            _safe(f.get("full_name")),
            _safe(f.get("role_title")),
            trust_name,
            _safe(f.get("status")),
            _safe(f.get("effective_date") or f.get("appointment_date")),
        ])
    story.append(Paragraph("Fiduciary Records", styles["SectionHeader"]))
    story.append(_table(rows, col_widths=[0.9 * inch, 1.8 * inch, 1.3 * inch, 1.7 * inch, 0.9 * inch, 1.0 * inch]))

    return story


def ledger_report_story(trust, entries):
    styles = _styles()
    story = []

    trust_name = _safe((trust or {}).get("trust_name")) or "Ledger Report"
    trust_id = _safe((trust or {}).get("trust_id"))

    story.append(Paragraph("Ledger Report", styles["AppTitle"]))
    story.append(Paragraph(f"Trust: {trust_name} &nbsp;&nbsp;&nbsp; Trust ID: {trust_id}", styles["Meta"]))
    story.append(Spacer(1, 8))

    total_amount = 0.0
    entry_count = len(entries or [])
    for e in entries or []:
        try:
            total_amount += float(e.get("amount") or 0)
        except Exception:
            pass

    summary_rows = [
        ["Metric", "Value"],
        ["Entry Count", str(entry_count)],
        ["Total Amount", _money(total_amount)],
    ]
    story.append(Paragraph("Summary", styles["SectionHeader"]))
    story.append(_table(summary_rows, col_widths=[2.8 * inch, 2.0 * inch]))
    story.append(Spacer(1, 10))

    rows = [["Entry ID", "Type", "Category", "Date", "Amount", "Description"]]
    for e in (entries or [])[:150]:
        rows.append([
            _safe(e.get("entry_id")),
            _safe(e.get("entry_type")),
            _safe(e.get("entry_category")),
            _safe(e.get("entry_date")),
            _money(e.get("amount")),
            _safe(e.get("description")),
        ])

    story.append(Paragraph("Ledger Entries", styles["SectionHeader"]))
    story.append(_table(rows, col_widths=[0.8 * inch, 0.9 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 2.3 * inch]))

    return story

def form1041_report_story(trust, tax_year, tax_logic, shares, evidence):
    styles = _styles()
    story = []

    trust_name = _safe((trust or {}).get("trust_name")) or "Form 1041 Report"
    trust_id = _safe((trust or {}).get("trust_id"))

    story.append(Paragraph("Form 1041 Report", styles["AppTitle"]))
    story.append(Paragraph(f"Trust: {trust_name} &nbsp;&nbsp;&nbsp; Trust ID: {trust_id} &nbsp;&nbsp;&nbsp; Tax Year: {_safe(tax_year)}", styles["Meta"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tax Logic", styles["SectionHeader"]))
    rows = [["Field", "Value"]]
    if isinstance(tax_logic, dict):
        for k, v in tax_logic.items():
            rows.append([_safe(k).replace("_", " ").title(), _safe(v)])
    if len(rows) == 1:
        rows.append(["Tax Logic", "No tax logic available"])
    story.append(_table(rows, col_widths=[3.0 * inch, 3.5 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Shares / Allocation", styles["SectionHeader"]))
    share_rows = [["Field", "Value"]]
    if isinstance(shares, dict):
        for k, v in shares.items():
            share_rows.append([_safe(k).replace("_", " ").title(), _safe(v)])
    elif isinstance(shares, list):
        share_rows = [["Name", "Value"]]
        for item in shares[:40]:
            if isinstance(item, dict):
                keys = list(item.keys())
                if len(keys) >= 2:
                    share_rows.append([_safe(item.get(keys[0])), _safe(item.get(keys[1]))])
                else:
                    share_rows.append([_safe(item), ""])
            else:
                share_rows.append([_safe(item), ""])
    if len(share_rows) == 1:
        share_rows.append(["Shares", "No share data available"])
    story.append(_table(share_rows, col_widths=[3.0 * inch, 3.0 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Evidence", styles["SectionHeader"]))
    evidence_rows = [["Reference", "Detail"]]
    if isinstance(evidence, list):
        for item in evidence[:50]:
            if isinstance(item, dict):
                keys = list(item.keys())
                if len(keys) >= 2:
                    evidence_rows.append([_safe(item.get(keys[0])), _safe(item.get(keys[1]))])
                elif len(keys) == 1:
                    evidence_rows.append([_safe(keys[0]), _safe(item.get(keys[0]))])
                else:
                    evidence_rows.append([_safe(item), ""])
            else:
                evidence_rows.append([_safe(item), ""])
    elif isinstance(evidence, dict):
        for k, v in evidence.items():
            evidence_rows.append([_safe(k), _safe(v)])
    if len(evidence_rows) == 1:
        evidence_rows.append(["Evidence", "No evidence data available"])
    story.append(_table(evidence_rows, col_widths=[2.2 * inch, 4.0 * inch]))

    return story


def instrument_detail_story(instrument, trust=None, history=None):
    styles = _styles()
    story = []

    instrument_number = _safe((instrument or {}).get("instrument_number")) or _safe((instrument or {}).get("instrument_id")) or "Instrument Detail"
    trust_name = _safe((trust or {}).get("trust_name")) if trust else _safe((instrument or {}).get("trust_id"))

    story.append(Paragraph("Instrument Detail Report", styles["AppTitle"]))
    story.append(Paragraph(f"Instrument: {instrument_number} &nbsp;&nbsp;&nbsp; Trust: {trust_name}", styles["Meta"]))
    story.append(Spacer(1, 8))

    rows = [["Field", "Value"]]
    if isinstance(instrument, dict):
        ordered_keys = [
            "instrument_id", "trust_id", "instrument_number", "instrument_type",
            "issue_date", "maturity_date", "face_value", "backing_type",
            "backing_reference", "status", "affidavit_reference",
            "custody_reference", "notes"
        ]
        for k in ordered_keys:
            if k in instrument:
                value = _money(instrument.get(k)) if k == "face_value" else _safe(instrument.get(k))
                rows.append([_safe(k).replace("_", " ").title(), value])
    story.append(Paragraph("Instrument Fields", styles["SectionHeader"]))
    story.append(_table(rows, col_widths=[2.2 * inch, 4.0 * inch]))
    story.append(Spacer(1, 10))

    if history:
        story.append(Paragraph("Recent History", styles["SectionHeader"]))
        hist_rows = [["Action", "Detail"]]
        for h in history[:40]:
            if isinstance(h, dict):
                hist_rows.append([
                    _safe(h.get("action") or h.get("change_type") or h.get("event_type")),
                    _safe(h.get("details") or h.get("description") or h.get("notes"))
                ])
            else:
                hist_rows.append([_safe(h), ""])
        story.append(_table(hist_rows, col_widths=[1.5 * inch, 4.7 * inch]))

    return story

def portfolio_report_story(portfolio, totals):
    styles = _styles()
    story = []

    story.append(Paragraph("Portfolio Report", styles["AppTitle"]))
    story.append(Paragraph("Aggregate trust portfolio view", styles["Meta"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Totals", styles["SectionHeader"]))
    total_rows = [["Metric", "Value"]]
    if isinstance(totals, dict):
        for k, v in totals.items():
            label = _safe(k).replace("_", " ").title()
            value = _money(v) if any(x in _safe(k).lower() for x in ["amount", "value", "total"]) else _safe(v)
            total_rows.append([label, value])
    if len(total_rows) == 1:
        total_rows.append(["Totals", "No totals available"])
    story.append(_table(total_rows, col_widths=[3.0 * inch, 2.3 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Portfolio Records", styles["SectionHeader"]))
    rows = [["Trust ID", "Trust Name", "Category", "Status", "Amount/Value"]]

    if isinstance(portfolio, list):
        for item in portfolio[:150]:
            if isinstance(item, dict):
                rows.append([
                    _safe(item.get("trust_id")),
                    _safe(item.get("trust_name")),
                    _safe(item.get("category") or item.get("asset_class") or item.get("type")),
                    _safe(item.get("status")),
                    _money(item.get("amount") or item.get("value") or item.get("total")),
                ])
            else:
                rows.append([_safe(item), "", "", "", ""])

    if len(rows) == 1:
        rows.append(["No portfolio records", "", "", "", ""])

    story.append(_table(rows, col_widths=[1.0 * inch, 2.1 * inch, 1.2 * inch, 1.0 * inch, 1.2 * inch]))
    return story


def audit_log_report_story(logs, entity_type=None, entity_id=None):
    styles = _styles()
    story = []

    subtitle = "System-wide audit log"
    if entity_type or entity_id:
        subtitle = f"Filtered audit log — Entity Type: {_safe(entity_type)}  Entity ID: {_safe(entity_id)}"

    story.append(Paragraph("Audit Log Report", styles["AppTitle"]))
    story.append(Paragraph(subtitle, styles["Meta"]))
    story.append(Spacer(1, 8))

    summary_rows = [
        ["Metric", "Value"],
        ["Entity Type Filter", _safe(entity_type) or "None"],
        ["Entity ID Filter", _safe(entity_id) or "None"],
        ["Log Count", str(len(logs or []))],
    ]
    story.append(Paragraph("Summary", styles["SectionHeader"]))
    story.append(_table(summary_rows, col_widths=[2.4 * inch, 3.2 * inch]))
    story.append(Spacer(1, 10))

    rows = [["When", "Entity Type", "Entity ID", "Action", "Details"]]
    for log in (logs or [])[:200]:
        if isinstance(log, dict):
            rows.append([
                _safe(log.get("created_at") or log.get("timestamp") or log.get("logged_at")),
                _safe(log.get("entity_type")),
                _safe(log.get("entity_id")),
                _safe(log.get("action") or log.get("change_type") or log.get("event_type")),
                _safe(log.get("details") or log.get("description") or log.get("notes")),
            ])
        else:
            rows.append(["", "", "", "", _safe(log)])

    if len(rows) == 1:
        rows.append(["", "", "", "", "No audit log records found"])

    story.append(Paragraph("Audit Entries", styles["SectionHeader"]))
    story.append(_table(rows, col_widths=[1.2 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch, 2.4 * inch]))
    return story
