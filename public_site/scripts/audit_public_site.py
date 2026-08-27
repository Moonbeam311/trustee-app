from __future__ import annotations

import re
import struct
import sys
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html",
    "how-it-works.html",
    "who-it-helps.html",
    "capabilities.html",
    "hindsfoot-model.html",
    "security-continuity.html",
    "about.html",
    "request-demo.html",
    "genealogy-legacy.html",
    "privacy.html",
    "terms.html",
    "accessibility.html",
    "software-disclaimer.html",
    "work-learning-hub.html",
)
ASSETS = (
    "assets/css/site.css",
    "assets/js/config.js",
    "assets/js/site.js",
    "assets/images/brand/hindsfoot_os_master.png",
    "assets/images/brand/hindsfoot_emblem_512.png",
    "assets/images/brand/hindsfoot_emblem_circle_512.png",
    "assets/images/brand/hindsfoot_header_seal_512.png",
    "assets/images/brand/hindsfoot_os_hero_identity_no_principle.png",
    "assets/images/brand/hindsfoot_os_public_hero_hybrid_approved.png",
    "assets/images/brand/apple-touch-icon-180.png",
    "assets/images/brand/favicon-32.png",
    "assets/images/brand/favicon-16.png",
)
FORBIDDEN = (
    "DB_PATH",
    "sqlite3",
    "from app import",
    "import app",
    "lorem ipsum",
)
SENSITIVE_PATTERNS = (
    r"\bITFB-[A-Z0-9]{8,}\b",
    r"\bTR-[A-Z0-9]{3,}\b",
    r"BrowserOnly",
    r"disposable_admin",
)


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.assets: list[str] = []
        self.h1 = 0
        self.images: list[dict[str, str | None]] = []
        self.forms: list[dict[str, str | None]] = []
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "link" and values.get("href"):
            self.assets.append(values["href"] or "")
        if tag == "script" and values.get("src"):
            self.assets.append(values["src"] or "")
        if tag == "img":
            self.images.append(values)
            if values.get("src"):
                self.assets.append(values["src"] or "")
        if tag == "form":
            self.forms.append(values)
        if tag == "h1":
            self.h1 += 1
        if values.get("id"):
            self.ids.append(values["id"] or "")


failures: list[str] = []
passes = 0


def check(label: str, condition: bool, detail: object = "") -> None:
    global passes
    result = "PASS" if condition else "FAIL"
    print(f"{result} - {label}" + (f" | {detail}" if detail != "" else ""))
    if condition:
        passes += 1
    else:
        failures.append(label)


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


check("expected page inventory", all((ROOT / path).is_file() for path in PAGES), PAGES)
check("expected asset inventory", all((ROOT / path).is_file() for path in ASSETS), ASSETS)

all_text = ""
external_http: set[str] = set()
for page_name in PAGES:
    page = ROOT / page_name
    text = page.read_text(encoding="utf-8")
    all_text += "\n" + text
    parser = Document()
    parser.feed(text)
    check(f"{page_name}: one h1", parser.h1 == 1, parser.h1)
    check(f"{page_name}: no duplicate IDs", len(parser.ids) == len(set(parser.ids)))
    check(f"{page_name}: skip link", 'class="skip-link"' in text and 'id="main"' in text)
    check(f"{page_name}: navigation label", 'aria-label="Primary navigation"' in text)
    check(f"{page_name}: favicon metadata", 'rel="icon"' in text and 'rel="apple-touch-icon"' in text)
    check(f"{page_name}: social metadata", 'property="og:title"' in text and 'property="og:description"' in text and 'name="twitter:card"' in text)
    for reference in parser.assets:
        parts = urlsplit(reference)
        if not parts.scheme and not reference.startswith("//"):
            target = (page.parent / parts.path).resolve()
            check(f"{page_name}: asset {reference}", target.is_file())
    for href in parser.links:
        parts = urlsplit(href)
        if parts.scheme in {"http", "https"}:
            external_http.add(href)
        elif parts.scheme in {"mailto", "tel"} or href.startswith("#"):
            continue
        else:
            target = (page.parent / parts.path).resolve()
            check(f"{page_name}: link {href}", target.is_file())
    for image in parser.images:
        check(f"{page_name}: image alt declared", "alt" in image)
        check(f"{page_name}: image dimensions", bool(image.get("width") and image.get("height")))
    for form in parser.forms:
        check(f"{page_name}: form is local-only", not form.get("action") and "data-demo-form" in form)

css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
config = (ROOT / "assets/js/config.js").read_text(encoding="utf-8")
check("visible keyboard focus", ":focus-visible" in css)
check("reduced motion supported", "prefers-reduced-motion" in css)
check("responsive mobile navigation", "@media (max-width: 1180px)" in css and "data-nav-toggle" in all_text)
check("narrow layout avoids horizontal clipping", "max-width: 100%" in css and "flex-wrap: wrap" in css)
responsive_harness = (ROOT / "scripts/responsive_overflow_audit.html").read_text(encoding="utf-8")
check("rendered overflow harness covers required widths", all(str(width) in responsive_harness for width in (320, 360, 640, 768, 960, 1024, 1152, 1280, 1366, 1440, 1920)))
check("rendered overflow harness covers every page", all(page in responsive_harness for page in PAGES))
check("rendered overflow harness measures document against viewport", "scrollWidth" in responsive_harness and "clientWidth" in responsive_harness)
check("rendered overflow harness checks controls, images, navigation, persistent login, circular mark, hero, journey, and previews", all(marker in responsive_harness for marker in ("clippedControls", "imagesDistorted", "navUsable", "loginVisible", "markCircular", "wordmarkReadable", "navOverlapsLogin", "heroCoherent", "descriptorFits", "journeyCoherent", "previewsAligned")))
check("dependency-free JavaScript", not re.search(r"\b(import|require)\s*\(", js))
check("single configurable login setting", config.count("loginUrl") == 1 and "js-login-link" in js)
check("one persistent header login outside navigation", all(
    text.count('class="header-login js-login-link"') == 1 and
    not re.search(r'<nav[^>]*>.*?class="header-login.*?</nav>', text, re.I | re.S)
    for text in ((ROOT / page).read_text(encoding="utf-8") for page in PAGES)
))
check("full demonstration wording in primary navigation", all(
    '<a' in text and '>Request a Demonstration</a>' in text and '>Request a Demo</a>' not in text
    for text in ((ROOT / page).read_text(encoding="utf-8") for page in PAGES)
))
check("no HTTP destination embedded in deployable markup", not external_http, sorted(external_http))
check("no localhost in HTML or deployable configuration", not re.search(r"https?://(?:127\.0\.0\.1|localhost)", all_text + config, re.I))
check("static demonstration disclosure", "no information was collected or transmitted" in js and "does not collect, store, or transmit" in all_text)
check("no prohibited records, credentials, or imports", not any(marker.lower() in all_text.lower() for marker in FORBIDDEN))
public_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in ROOT.rglob("*")
    if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".md"}
)
check("no protected or disposable identifiers", not any(re.search(pattern, public_text, re.I) for pattern in SENSITIVE_PATTERNS))
check("no database-like files", not any(path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".wal", ".shm"} for path in ROOT.rglob("*")))

logo = ROOT / "assets/images/brand/hindsfoot_os_master.png"
with logo.open("rb") as stream:
    signature = stream.read(24)
dimensions = struct.unpack(">II", signature[16:24]) if signature[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)
check("logo is a valid PNG", dimensions[0] > 0 and dimensions[1] > 0, dimensions)
check("logo alt preserves identity", "Hindsfoot OS — Sure Footing Across Generations" in all_text)
home = (ROOT / "index.html").read_text(encoding="utf-8")
check("locked homepage principle", all(fragment in home for fragment in ("Sure Footing Across", "Generations.")))
check("locked descriptor preserved", "The Personal Institutional Operating System" in home)
check("locked official tagline preserved", "Govern your affairs. Preserve your record. Carry your legacy forward." in home)
approved_hero_name = "hindsfoot_os_public_hero_hybrid_approved.png"
check(
    "approved single-hybrid hero used exactly once",
    home.count(approved_hero_name) == 1
    and "hindsfoot_os_hero_identity_no_principle.png" not in home,
)

hero_source = re.search(
    r'<section class="hero hybrid-image-hero">.*?</section>',
    home,
    re.S,
)

hero_text = (
    re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", hero_source.group(0))).strip()
    if hero_source
    else ""
)

check(
    "approved hybrid hero semantic principle appears once",
    hero_text.count("Sure Footing Across Generations.") == 1,
)

check(
    "approved hybrid hero semantic descriptor appears once",
    hero_text.count("The Personal Institutional Operating System") == 1,
)

check(
    "approved hybrid hero semantic tagline appears once",
    hero_text.count(
        "Govern your affairs. Preserve your record. Carry your legacy forward."
    ) == 1,
)

check(
    "approved hybrid hero responsive image contract",
    all(
        marker in css
        for marker in (
            ".hybrid-hero-image",
            "width: 100%",
            "height: auto",
            ".hybrid-hero-container",
        )
    ),
)

check(
    "approved hybrid hero preserves both CTA hotspots",
    all(
        marker in home
        for marker in (
            "hybrid-hero-hotspot-how",
            'href="how-it-works.html"',
            "hybrid-hero-hotspot-demo",
            'href="request-demo.html"',
        )
    ),
)

approved_hero = ROOT / "assets/images/brand/hindsfoot_os_public_hero_hybrid_approved.png"
with approved_hero.open("rb") as stream:
    approved_signature = stream.read(24)

approved_dimensions = (
    struct.unpack(">II", approved_signature[16:24])
    if approved_signature[:8] == b"\x89PNG\r\n\x1a\n"
    else (0, 0)
)

check(
    "approved hybrid hero dimensions locked",
    approved_dimensions == (1672, 941),
    approved_dimensions,
)

approved_hash = hashlib.sha256(approved_hero.read_bytes()).hexdigest()

check(
    "approved hybrid hero hash locked",
    approved_hash
    == "4028b8d9b50706b103a30a306b2f343a0a2d9c7b2de1d8e26fee59a10e0242d3",
    approved_hash,
)
check("journey preserves six ordered steps", all(home.find(label) < home.find(next_label) for label, next_label in zip(
    ("Intake</h3>", "Guided proposal</h3>", "Explicit confirmation</h3>", "Governed record</h3>", "Administration</h3>"),
    ("Guided proposal</h3>", "Explicit confirmation</h3>", "Governed record</h3>", "Administration</h3>", "Continuity</h3>"),
)) and home.count('class="path-item"') == 6)
check("journey uses responsive three-two-one grid", all(marker in css for marker in (
    ".path { display: grid; grid-template-columns: repeat(3", ".path { grid-template-columns: repeat(2", ".path { grid-template-columns: 1fr"
)))
check("polished fictional preview windows present", home.count('class="preview-window') == 3 and all(marker in home for marker in (
    "Core information", "Readiness review", "Decision preserved"
)))
check("repeated preview labels removed", 'class="preview-label"' not in home and home.count('<p class="eyebrow">Product preview</p>') == 1)
callout_default_contrast = contrast_ratio("#fffdf8", "#173f67")
callout_hover_contrast = contrast_ratio("#11100e", "#c69a3a")
check("model action default contrast meets WCAG AA", callout_default_contrast >= 4.5 and ".callout .button.secondary" in css, f"{callout_default_contrast:.2f}:1")
check("model action hover contrast meets WCAG AA", callout_hover_contrast >= 4.5 and ".callout .button.secondary:hover" in css, f"{callout_hover_contrast:.2f}:1")
critical_contrasts = {
    "black/ivory": contrast_ratio("#11100e", "#f5f0e5"),
    "muted/ivory": contrast_ratio("#625e55", "#f5f0e5"),
    "gold-dark/ivory": contrast_ratio("#8b6825", "#f5f0e5"),
    "white/blue": contrast_ratio("#ffffff", "#173f67"),
    "paper/blue": contrast_ratio("#fffdf8", "#173f67"),
    "legal-note/black": contrast_ratio("#cfc8ba", "#11100e"),
}
check("critical text palette meets WCAG AA", all(value >= 4.5 for value in critical_contrasts.values()), ", ".join(f"{name} {value:.2f}:1" for name, value in critical_contrasts.items()))
check("unapproved official variants absent", not re.search(r"Give (?:your )?legacy(?: sure)? footing", all_text, re.I))
master_hash = hashlib.sha256(logo.read_bytes()).hexdigest()
source_hash = hashlib.sha256((ROOT.parent / "static/branding/hindsfoot_os_logo.png").read_bytes()).hexdigest()
check("public master is byte-identical to locked source", master_hash == source_hash, master_hash.upper())
seal = ROOT / "assets/images/brand/hindsfoot_header_seal_512.png"
with seal.open("rb") as stream:
    seal_signature = stream.read(24)
seal_dimensions = struct.unpack(">II", seal_signature[16:24]) if seal_signature[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)
check("derived header seal has 1:1 dimensions", seal_dimensions[0] == seal_dimensions[1] == 512, seal_dimensions)
check("header uses distinct seal derivative exactly once", all(
    (ROOT / page).read_text(encoding="utf-8").count("hindsfoot_header_seal_512.png") == 1
    for page in PAGES
))
check("header seal has circular CSS treatment", all(marker in css for marker in (
    ".wordmark .header-seal", "aspect-ratio: 1", "object-fit: contain", "background: transparent"
)))
hero_derivative = ROOT / "assets/images/brand/hindsfoot_os_hero_identity_no_principle.png"
with hero_derivative.open("rb") as stream:
    hero_signature = stream.read(26)
hero_dimensions = struct.unpack(">II", hero_signature[16:24]) if hero_signature[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)
check("hero derivative is alpha PNG with expected dimensions", hero_dimensions == (900, 830) and len(hero_signature) == 26 and hero_signature[25] == 6, hero_dimensions)
check("genealogy page and required limitation language", all(phrase in all_text for phrase in (
    "A family tree shows connection.",
    "does not independently authenticate DNA conclusions",
    "does not establish inheritance, ownership, citizenship, legal status, or entitlement",
)))
genealogy = (ROOT / "genealogy-legacy.html").read_text(encoding="utf-8")
check("genealogy locked title", "<h1>Genealogy, Relationships, and Legacy</h1>" in genealogy)
check("genealogy four capability headings", all(heading in genealogy for heading in (
    "Connect people across generations", "Record succession and stewardship",
    "Preserve source records", "Make uncertainty visible",
)))
check("genealogy five-stage progression", 'aria-label="Five-stage governed relationship-evidence path"' in genealogy and all(
    stage in genealogy for stage in ("Source</h3>", "Relationship assertion</h3>", "Evidence review</h3>", "Human confirmation</h3>", "Continuity record</h3>")
))
check("genealogy assertion boundary locked", "A relationship assertion remains an assertion until its supporting evidence is reviewed and its status is explicitly recorded." in genealogy)
check("fictional genealogy preview labeled", "Fictional Genealogy Workspace Preview" in genealogy and "contains no authenticated or personal record" in genealogy)
check("genealogy conceptual map labeled", 'role="img"' in genealogy and "Conceptual relationship-evidence map" in genealogy and "Connections retain their evidence status" in genealogy)
check("genealogy map has six ordered grid nodes", genealogy.count('class="relationship-node ') == 6 and all(
    genealogy.find(marker) < genealogy.find(next_marker) for marker, next_marker in zip(
        ("map-person", "map-family", "map-source", "map-role", "map-property"),
        ("map-family", "map-source", "map-role", "map-property", "map-successor"),
    )
))
check("genealogy connectors are separate and behind nodes", all(marker in genealogy + css for marker in (
    'class="map-connectors"', ".map-connectors { position: absolute", "z-index: 0", ".relationship-node { position: relative; z-index: 1",
)))
check("genealogy mobile map removes collision-prone connectors", ".map-connectors { display: none; }" in css and ".relationship-diagram { grid-template-columns: 1fr" in css)
check("genealogy status is not color-only", all(label in genealogy for label in (
    "Confirmed", "User asserted", "Conflicting", "Unresolved", "Source connected", "Review required",
)))
check("genealogy closing phrase locked", "Legacy is connection made usable." in genealogy)
check("genealogy login and required footer links", all(fragment in genealogy for fragment in (
    'class="header-login js-login-link"', 'href="work-learning-hub.html">Work &amp; Learning Hub</a>',
    'href="genealogy-legacy.html">Genealogy and Legacy</a>', 'href="accessibility.html">Accessibility</a>',
    'href="privacy.html">Privacy</a>', 'href="terms.html">Terms</a>', 'href="software-disclaimer.html">Software Disclaimer</a>',
)))
check("genealogy responsive structures", all(marker in css for marker in (
    ".genealogy-hero-grid", ".genealogy-card-grid", ".genealogy-path", ".genealogy-preview-grid",
    "@media (max-width: 1023px)", "@media (max-width: 767px)",
)))
check("genealogy prohibited claims absent", not any(phrase in genealogy.lower() for phrase in (
    "certifies ancestry", "authenticates dna", "determines inheritance", "establishes ownership",
    "determines citizenship", "establishes legal entitlement", "guaranteed succession", "verified ancestry",
)))
check("public trust pages linked", all(f'href="{name}"' in all_text for name in ("privacy.html", "terms.html", "accessibility.html", "software-disclaimer.html")))
check("product preview section remains explicitly labeled", '<p class="eyebrow">Product preview</p>' in home and "See Hindsfoot in action" in home)

hub = (ROOT / "work-learning-hub.html").read_text(encoding="utf-8")
capabilities = (ROOT / "capabilities.html").read_text(encoding="utf-8")
how = (ROOT / "how-it-works.html").read_text(encoding="utf-8")
locked_hub_description = "A guided workspace for asking questions, learning the system, developing a tailored program, and preparing work for deliberate review and confirmation."
check("hub architecture record exists", (ROOT / "HOS_WEB_1B_WORK_LEARNING_HUB_ARCHITECTURE.md").is_file())
check("hub canonical is local and valid", '<link rel="canonical" href="work-learning-hub.html">' in hub)
check("hub title and metadata", "<title>Work &amp; Learning Hub" in hub and 'name="description"' in hub and 'property="og:title"' in hub)
check("locked hub description is consistent", all(locked_hub_description in text for text in (hub, home, capabilities)))
check("hub three states are exact", all(state in hub for state in ("Explore and Learn", "Work and Develop", "Confirm and Govern")))
check("hub promotion is explicitly nonautomatic", "Movement is never automatic." in hub and "requires explicit confirmation" in hub)
check("hub public claims are qualified", "Product architecture" in hub and "planned" in hub and "Existing authenticated components support parts" in hub)
check("hub links integrated", all('href="work-learning-hub.html"' in text for text in (home, capabilities, how)))
check("hub footer link synchronized", all(
    text.count('<a href="work-learning-hub.html">Work &amp; Learning Hub</a>') == 1
    for text in ((ROOT / page).read_text(encoding="utf-8") for page in PAGES)
))
check("how-it-works preserves exact six stages", 'aria-label="Six stages"' in how and how.count('class="path-item"') == 6 and all(
    how.find(label) < how.find(next_label) for label, next_label in zip(
        ("Intake</h3>", "Guided proposal</h3>", "Explicit confirmation</h3>", "Governed record</h3>", "Administration</h3>"),
        ("Guided proposal</h3>", "Explicit confirmation</h3>", "Governed record</h3>", "Administration</h3>", "Continuity</h3>"),
    )
))
journey_source = re.search(r'<div class="path" aria-label="Six stages">.*?</div></div><div class="actions">', how, re.S)
journey_text = journey_source.group(0) if journey_source else ""
check("how-it-works displays one explicit number per journey card", journey_text.count('class="step-number"') == 6 and ".path-item::before" not in css and "counter(path, decimal-leading-zero)" not in css)
check("how-it-works journey numerals occur once in region", all(journey_text.count(f'>{number:02d}</span>') == 1 for number in range(1, 7)))
check("hub is a lane, not a numbered stage", "Supporting lane" in how and "Step 00" not in how and "Step 07" not in how)
check("unsupported public claims absent", not any(phrase.lower() in all_text.lower() for phrase in (
    "ai-powered", "personalized legal advice", "guaranteed outcome", "definitive answer to every question"
)))

print(f"\nPUBLIC SITE AUDIT: {'PASS' if not failures else 'FAIL'}")
print(f"Assertions passed: {passes}")
print(f"Assertions failed: {len(failures)}")
if failures:
    print("Failures: " + "; ".join(failures))
    sys.exit(1)
