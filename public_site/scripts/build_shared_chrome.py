from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = tuple(ROOT.glob("*.html"))
PRIMARY = (
    ("Why Hindsfoot", "who-it-helps.html"),
    ("How It Works", "how-it-works.html"),
    ("Capabilities", "capabilities.html"),
    ("About", "about.html"),
    ("Request a Demonstration", "request-demo.html"),
)


def header(current: str) -> str:
    links = []
    for label, href in PRIMARY:
        marker = ' aria-current="page"' if current == href else ""
        links.append(f'<a{marker} href="{href}">{label}</a>')
    return (
        '<header class="site-header"><div class="container header-inner">'
        '<a class="wordmark" href="index.html" aria-label="Hindsfoot OS home">'
        '<img class="header-seal" src="assets/images/brand/hindsfoot_header_seal_512.png" width="44" height="44" alt="">'
        '<span>HINDSFOOT <b>OS</b></span></a>'
        '<nav class="site-nav" id="site-nav" aria-label="Primary navigation" data-site-nav>'
        + "".join(links)
        + '</nav><div class="header-actions">'
        '<a class="header-login js-login-link" href="#login-not-configured">Log In</a>'
        '<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" data-nav-toggle>Menu</button>'
        '</div></div></header>'
    )


FOOTER = (
    '<footer class="site-footer"><div class="container"><div class="footer-grid">'
    '<div class="footer-brand"><img src="assets/images/brand/hindsfoot_emblem_circle_512.png" width="60" height="60" alt="">'
    '<div><h2>Hindsfoot OS</h2><p>Built upon the Hindsfoot Model.<br>Sure Footing Across Generations.</p></div></div>'
    '<div class="footer-links"><a href="hindsfoot-model.html">The Hindsfoot Model</a>'
    '<a href="work-learning-hub.html">Work &amp; Learning Hub</a>'
    '<a href="security-continuity.html">Security and Continuity</a><a href="genealogy-legacy.html">Genealogy and Legacy</a>'
    '<a href="who-it-helps.html">Who It Helps</a></div>'
    '<div class="footer-links"><a href="request-demo.html">Request a Demonstration</a>'
    '<a class="js-login-link" href="#login-not-configured">Log In</a><a href="privacy.html">Privacy</a>'
    '<a href="terms.html">Terms</a><a href="accessibility.html">Accessibility</a>'
    '<a href="software-disclaimer.html">Software Disclaimer</a></div></div>'
    '<p class="legal-note">© 2026 Hindsfoot. Hindsfoot OS is organizational software. It is not a law firm and does not provide legal, tax, accounting, investment, financial, genealogical-certification, or other professional advice.</p>'
    '</div></footer>'
)


for page in PAGES:
    text = page.read_text(encoding="utf-8")
    title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    description_match = re.search(r'<meta name="description" content="([^"]*)">', text, re.I)
    title = html.unescape(title_match.group(1).strip()) if title_match else "Hindsfoot OS"
    description = html.unescape(description_match.group(1).strip()) if description_match else "The Personal Institutional Operating System."
    metadata = (
        '<link rel="icon" type="image/png" sizes="32x32" href="assets/images/brand/favicon-32.png">'
        '<link rel="icon" type="image/png" sizes="16x16" href="assets/images/brand/favicon-16.png">'
        '<link rel="apple-touch-icon" sizes="180x180" href="assets/images/brand/apple-touch-icon-180.png">'
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">'
        f'<meta property="og:description" content="{html.escape(description, quote=True)}">'
        '<meta property="og:type" content="website">'
        '<meta property="og:image" content="assets/images/brand/hindsfoot_os_master.png">'
        '<meta name="twitter:card" content="summary_large_image">'
    )
    if 'property="og:title"' not in text:
        text = text.replace('<link rel="stylesheet"', metadata + '<link rel="stylesheet"', 1)
    text = re.sub(r'<header class="site-header">.*?</header>', header(page.name), text, count=1, flags=re.S)
    text = re.sub(r'<footer class="site-footer">.*?</footer>', FOOTER, text, count=1, flags=re.S)
    text = text.rstrip() + "\n"
    page.write_text(text, encoding="utf-8")

print(f"Updated shared chrome and metadata for {len(PAGES)} pages.")
