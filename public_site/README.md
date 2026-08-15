# Hindsfoot Public Website

HOS-WEB-1/HOS-WEB-1A is a self-contained static presentation layer. It has no database, Flask import, authenticated-application import, credential, or governed-write dependency.

Locked brand language:

- Descriptor: **The Personal Institutional Operating System**
- Brand principle: **Sure Footing Across Generations.**
- Official tagline: **Govern your affairs. Preserve your record. Carry your legacy forward.**

## Architecture

- Fourteen deployable HTML pages at the site root, including the Work & Learning Hub product-architecture page
- Shared responsive presentation in `assets/css/site.css`
- Dependency-free interaction in `assets/js/site.js`
- A single public configuration object in `assets/js/config.js`
- Static output requires no build tool
- `scripts/build_shared_chrome.py` maintains shared header, footer, favicon, and social metadata across pages
- `scripts/audit_public_site.py` validates page, link, asset, metadata, safety, accessibility, and configuration boundaries
- `HOS_WEB_1B_WORK_LEARNING_HUB_ARCHITECTURE.md` records verified components, adjacent capabilities, planned gaps, claims controls, and the draft-to-governed-record boundary

## Work & Learning Hub

The public Hub page distinguishes three states: Explore and Learn, Work and Develop, and Confirm and Govern. Authenticated learning, discussion, workspace, note, task, document, and governed-review components substantiate parts of the direction. The unified working-session experience, source-linked tailored-program model, and explicit cross-module promotion workflow remain product architecture; the public site does not represent them as fully operational.

## Local preview

From the repository root:

```bash
python -m http.server 8010 --directory public_site
```

Open `http://127.0.0.1:8010/`. During local preview only, `site.js` derives the Hindsfoot OS Login destination from the preview hostname and port 5000. No localhost URL is published in HTML or deployable configuration.

## Required deployment configuration

Set these values in `assets/js/config.js` before deployment:

- `loginUrl`: reviewed authenticated Hindsfoot OS introduction URL
- `demonstrationRequestEndpoint`: remains empty until a separately reviewed collection service exists
- `contactEmail`: public demonstration contact owned and monitored by the operator
- `privacyPolicyUrl`: deployed privacy-notice URL

Also establish the actual site owner, public contact, hosting/logging disclosures, applicable final terms, and accessibility-feedback channel. The preview intentionally invents no entity, address, telephone number, privacy officer, jurisdiction, or regulatory status.

The Request a Demonstration form is preview-only. JavaScript prevents submission, and no form information is collected or transmitted.

## Logo system

Locked source: `../static/branding/hindsfoot_os_logo.png`, 1254 × 1254, SHA-256 `5B2B4406D71AEDF9B74BF4BE9252FC402F80841B49874DD9E3DC3A4BD83F5A07`.

| Asset | Transformation | Dimensions | Intended use |
|---|---|---:|---|
| `assets/images/brand/hindsfoot_os_master.png` | Byte-for-byte copy | 1254 × 1254 | Formal presentation and social fallback |
| `assets/images/brand/hindsfoot_emblem_512.png` | Deterministic crop of the existing emblem above the embedded typography, padded on ivory, then resized | 512 × 512 | Preserved square intermediary |
| `assets/images/brand/hindsfoot_emblem_circle_512.png` | Circular alpha mask applied to the faithful emblem crop; no artwork redrawn | 512 × 512 | Footer circular emblem and seal source |
| `assets/images/brand/hindsfoot_header_seal_512.png` | Faithful circular emblem inset on an ivory circular field with thin antique-gold and muted-black rings; transparent exterior; no artwork redrawn | 512 × 512 | Header institutional seal |
| `assets/images/brand/hindsfoot_os_hero_identity_no_principle.png` | Cropped from the locked master to retain the approved artwork and HINDSFOOT OS identity while omitting only the embedded principle line; connected black/gold artwork preserved while the textured ivory field is removed to transparency | 900 × 830 | Homepage editorial hero identity |
| `assets/images/brand/apple-touch-icon-180.png` | Circular resize of the faithful emblem crop with transparent exterior | 180 × 180 | Application/touch icon |
| `assets/images/brand/favicon-32.png` | Circular resize of the faithful emblem crop with transparent exterior | 32 × 32 | Standard favicon |
| `assets/images/brand/favicon-16.png` | Circular resize of the faithful emblem crop with transparent exterior | 16 × 16 | Small favicon fallback |

The master was not modified, recolored, redrawn, or overwritten. Compact wording remains accessible HTML text rather than rasterized replacement typography.

The header Log In action is deliberately outside the collapsible primary navigation. Its destination remains controlled by the single `loginUrl` configuration boundary and the documented local-preview fallback in `site.js`.

## Genealogy limitations

Genealogy is presented within Legacy and Continuity. Records may contain uncertainty or conflicting evidence. Hindsfoot organizes records and source relationships; it does not independently authenticate DNA conclusions. Genealogy alone does not establish inheritance, ownership, citizenship, legal status, or entitlement. Appropriate professional and documentary review remains necessary.

## Deployment prerequisites

- Manual visual approval at 360, 768, 1024, and 1440 CSS pixels
- Final public URLs and ownership/contact disclosures
- Hosting, caching, security-header, logging, and privacy review
- Form collection remains disabled until separately authorized
- Real screenshots remain excluded until public-use approval
- HOS-DEMO-1 remains the dependency for approved, safe demonstration assets and scenarios

## Boundaries

- Never place application configuration, credentials, databases, trust records, exported documents, personal genealogy, or disposable certification data here.
- Do not alter the locked master logo.
- Hindsfoot OS is organizational software, not legal, tax, accounting, investment, financial, genealogical-certification, cybersecurity, or other professional advice.
