from pathlib import Path
path = Path("templates/admin_index.html")
text = path.read_text(encoding="utf-8", errors="ignore")
start_marker = "<!-- POST-V2-3A-R1 ADMIN OPERATOR GROUPS -->"
end_marker = "<!-- /POST-V2-3A-R1 ADMIN OPERATOR GROUPS -->"
polish_marker = "<!-- POST-V2-3B VISUAL POLISH ACTIVE -->"
if start_marker not in text or end_marker not in text:
    raise SystemExit("POST-V2-3A-R1 grouped section not found.")
start = text.index(start_marker)
end = text.index(end_marker) + len(end_marker)
section = text[start:end]
text = text[:start] + text[end:]
section = section.replace("<section class=\"admin-operator-groups\">", "<section class=\"admin-operator-groups admin-command-center\">")
section = section.replace("<h2>Admin Operator Groups</h2>", "<h2>Institutional Command Groups</h2>")
section = section.replace("Grouped operator access for administration, governance, records, continuity, security, and diagnostics. This section reorganizes navigation only.", "Primary grouped access for institutional administration. Use these cards as the main operating map before using legacy shortcuts below.")
style_lines = [
    "<style>",
    ".admin-command-center { border: 1px solid #cbd5e1; border-radius: 18px; background: #f8fafc; padding: 20px; margin: 20px 0; }",
    ".admin-command-center h2 { margin-top: 0; }",
    ".admin-command-center .workspace-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }",
    ".admin-command-center .workspace-card { border: 1px solid #d0d7de; border-radius: 14px; background: white; padding: 14px; text-decoration: none; color: inherit; }",
    ".admin-command-center .workspace-card strong { display: block; margin-bottom: 6px; }",
    ".admin-command-center .workspace-card span { display: block; color: #475569; line-height: 1.35; }",
    "</style>",
]
style = "\n".join(style_lines)
if polish_marker not in text:
    if "</head>" in text:
        text = text.replace("</head>", polish_marker + "\n" + style + "\n</head>", 1)
    else:
        text = polish_marker + "\n" + style + "\n" + text
placement_markers = ["<h2>Recommended Next Action</h2>", "<h2>Executive Home</h2>", "<h2>Institutional Command Center</h2>"]
inserted = False
for marker in placement_markers:
    if marker in text:
        text = text.replace(marker, section + "\n\n" + marker, 1)
        inserted = True
        break
if not inserted:
    text = section + "\n" + text
path.write_text(text, encoding="utf-8")
print("POST-V2-3B visual polish applied.")
