from pathlib import Path
path = Path("templates/admin_index.html")
text = path.read_text(encoding="utf-8", errors="ignore")
marker = "<!-- POST-V2-3D COLLAPSE CONTROLS ACTIVE -->"
if marker in text:
    print("POST-V2-3D collapse controls already active; no change.")
    raise SystemExit(0)
style_lines = [
    "<style>",
    ".post-v2-3d-collapse-plan { border: 1px solid #cbd5e1; border-radius: 16px; padding: 16px; margin: 22px 0; background: #f8fafc; }",
    ".post-v2-3d-collapse-plan h2 { margin-top: 0; }",
    ".post-v2-3d-collapse-plan details { border: 1px solid #d0d7de; border-radius: 12px; background: #ffffff; margin: 10px 0; padding: 12px; }",
    ".post-v2-3d-collapse-plan summary { cursor: pointer; font-weight: 700; }",
    ".post-v2-3d-collapse-plan ul { margin-bottom: 0; }",
    ".post-v2-3d-badge { display: inline-block; border: 1px solid #cbd5e1; border-radius: 999px; padding: 2px 8px; margin-left: 6px; font-size: 0.85em; background: #fff; }",
    "</style>",
]
style = "\n".join(style_lines)
panel_lines = [
    marker,
    "<section class=\"post-v2-3d-collapse-plan\">",
    "  <h2>Admin Layout Controls</h2>",
    "  <p>Non-destructive containment plan for legacy, duplicate, and system-control areas. No routes or links are removed in this milestone.</p>",
    "  <details open>",
    "    <summary>Legacy Compatibility <span class=\"post-v2-3d-badge\">preserve</span></summary>",
    "    <ul><li>Legacy Compatibility Center</li><li>Legacy Quick Start</li></ul>",
    "  </details>",
    "  <details>",
    "    <summary>Duplicate Entry Points <span class=\"post-v2-3d-badge\">contain</span></summary>",
    "    <ul><li>Existing Trust Command Cards</li><li>Learning & Guidance Suite</li><li>Report Launch Area</li><li>Admin Tools</li><li>Operational Shortcuts</li></ul>",
    "  </details>",
    "  <details open>",
    "    <summary>System Controls <span class=\"post-v2-3d-badge\">protect</span></summary>",
    "    <ul><li>Hosted Baseline Seed</li><li>Database Backup</li><li>System Policy Controls</li><li>Security Layer</li></ul>",
    "  </details>",
    "  <p><strong>Certified Baseline Preserved:</strong> v2-certified-baseline-2026-07-10</p>",
    "</section>",
]
panel = "\n".join(panel_lines)
if "</head>" in text:
    text = text.replace("</head>", style + "\n</head>", 1)
else:
    text = style + "\n" + text
anchor = "Legacy Compatibility Center"
if anchor in text:
    text = text.replace(anchor, panel + "\n" + anchor, 1)
else:
    text = text + "\n" + panel
path.write_text(text, encoding="utf-8")
print("POST-V2-3D collapse controls inserted.")
