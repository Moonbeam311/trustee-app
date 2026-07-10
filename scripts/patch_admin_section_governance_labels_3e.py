from pathlib import Path
path = Path("templates/admin_index.html")
text = path.read_text(encoding="utf-8", errors="ignore")
marker = "<!-- POST-V2-3E SECTION GOVERNANCE LABELS ACTIVE -->"
if marker in text:
    print("POST-V2-3E labels already active; no change.")
    raise SystemExit(0)
style_lines = [
    "<style>",
    ".section-governance-label { display: inline-block; border: 1px solid #cbd5e1; border-radius: 999px; padding: 2px 9px; margin-left: 8px; font-size: 0.78em; font-weight: 700; background: #ffffff; color: #334155; vertical-align: middle; }",
    ".section-governance-label.active { background: #eef6ff; }",
    ".section-governance-label.legacy { background: #fff7ed; }",
    ".section-governance-label.duplicate { background: #f8fafc; }",
    ".section-governance-label.system { background: #f0fdf4; }",
    "</style>",
]
style = "\n".join(style_lines)
if "</head>" in text:
    text = text.replace("</head>", marker + "\n" + style + "\n</head>", 1)
else:
    text = marker + "\n" + style + "\n" + text
labels = {
    "Recommended Next Action": ("ACTIVE OPERATING SURFACE", "active"),
    "Executive Home": ("ACTIVE OPERATING SURFACE", "active"),
    "Continue Where You Left Off": ("ACTIVE OPERATING SURFACE", "active"),
    "Recent Institutional Activity": ("ACTIVE OPERATING SURFACE", "active"),
    "Institutional Command Center": ("ACTIVE OPERATING SURFACE", "active"),
    "Legacy Compatibility Center": ("LEGACY COMPATIBILITY", "legacy"),
    "Intake & Lifecycle Command Center": ("ACTIVE OPERATING SURFACE", "active"),
    "Intake Command Center": ("ACTIVE OPERATING SURFACE", "active"),
    "System Snapshot": ("ACTIVE OPERATING SURFACE", "active"),
    "Existing Trust Operations": ("ACTIVE OPERATING SURFACE", "active"),
    "Existing Trust Operations Dashboard": ("ACTIVE OPERATING SURFACE", "active"),
    "Existing Trust Command Cards": ("DUPLICATE ENTRY POINT", "duplicate"),
    "Legacy Quick Start": ("LEGACY COMPATIBILITY", "legacy"),
    "Learning & Guidance Suite": ("DUPLICATE ENTRY POINT", "duplicate"),
    "Hosted Baseline Seed": ("PROTECTED SYSTEM CONTROL", "system"),
    "Database Backup": ("PROTECTED SYSTEM CONTROL", "system"),
    "System Policy Controls": ("PROTECTED SYSTEM CONTROL", "system"),
    "Report Launch Area": ("DUPLICATE ENTRY POINT", "duplicate"),
    "Admin Tools": ("DUPLICATE ENTRY POINT", "duplicate"),
    "Operational Shortcuts": ("DUPLICATE ENTRY POINT", "duplicate"),
    "Security Layer": ("PROTECTED SYSTEM CONTROL", "system"),
}
for heading, pair in labels.items():
    label_text, css = pair
    badge = heading + " <span class=\"section-governance-label " + css + "\">" + label_text + "</span>"
    if badge in text:
        continue
    text = text.replace(heading, badge, 1)
path.write_text(text, encoding="utf-8")
print("POST-V2-3E section governance labels inserted.")
