"""
Universal Object Presentation Engine.
"""

VALUE_LABELS = {
    "business_operations": "Business Operations Trust",
    "revocable": "Revocable Trust",
    "private_office": "Private Office Workflow",
    "v3_minimal": "V3 Minimal Seal / Letterhead Style",
    "finalized": "Finalized",
    "not_assessed": "Not Assessed",
}


def humanize_value(value):
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    key = text.lower().replace(" ", "_")
    return VALUE_LABELS.get(key, text.replace("_", " ").title())


def present_context(ctx):
    if not ctx:
        return ctx

    ctx["summary"] = humanize_value(ctx.get("summary"))
    ctx["status_label"] = humanize_value(ctx.get("status_label"))

    lifecycle = ctx.get("lifecycle") or {}
    lifecycle["status_label"] = humanize_value(lifecycle.get("status_label"))

    panels = (ctx.get("extensions") or {}).get("executive_panels") or {}
    for panel in panels.values():
        panel["value"] = humanize_value(panel.get("value"))
        panel["detail"] = humanize_value(panel.get("detail"))

    return ctx
