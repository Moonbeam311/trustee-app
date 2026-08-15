# HOS-WEB-1C Static Site Audit

Date: 2026-08-15

Command:

`python public_site/scripts/audit_public_site.py`

Result: **PASS**

- Assertions passed: 578
- Assertions failed: 0
- Fourteen required pages present, including the Work & Learning Hub, genealogy/legacy, and four public trust pages
- Shared CSS, dependency-free JavaScript, deployment configuration, and documented locked-logo system present
- All internal links and local asset references resolve
- No HTTP destination embedded in deployable markup and no localhost URL in deployable configuration
- No database dependency, application import, credentials, protected identifiers, or database-like files
- One H1 per page, skip links, navigation labels, image alternative text, and declared image dimensions
- Visible keyboard focus, responsive navigation, narrow-width wrapping, and reduced-motion support
- Static demonstration form performs no submission and clearly reports its local-only state
- Locked-logo source and public master copy SHA-256: `5B2B4406D71AEDF9B74BF4BE9252FC402F80841B49874DD9E3DC3A4BD83F5A07`
- Transparent hero derivative SHA-256: `12D94C64A489DCB57C70FF3DD9724D990D40BE95E45FB61C41AD7BFC1855DD76`
- Circular header seal SHA-256: `1CE4355B30A48C3A08388A55A3E11990512926721CF6C23BC38EC6786CE36FFD`
- Compact emblem and favicon assets are present and linked; compact wording remains accessible HTML text
- Required genealogy evidence-status and legal limitations are present
- Three nonpersonal HTML/CSS product-preview frames are explicitly labeled Product preview
- Homepage, Work & Learning Hub, Capabilities, and How It Works returned HTTP 200 from the isolated port-8010 preview
- Core contrast ratios: black/ivory 16.73:1; blue/ivory 9.51:1; gold-dark/ivory 4.50:1; white/blue 10.81:1; white/black 19.02:1
- No protected or disposable identifiers occur in deployable public-site content
- Homepage heading, title, description, social title, logo alternative text, and README use the locked principle `Sure Footing Across Generations.`; unapproved hero variants are absent
- Responsive overflow repair: the non-wrapping desktop header remained active below its intrinsic content width; the responsive navigation transition now occurs at 1180px
- Three-column pathway row-end connectors are suppressed so their decorative extension cannot cross the container edge
- `scripts/responsive_overflow_audit.html` is configured to render all 14 pages at 320, 360, 640, 768, 960, 1024, 1152, 1180, 1280, 1366, 1440, and 1920px (168 rendered cases) and measure `scrollWidth` against `clientWidth`, clipped controls, image aspect ratio, navigation usability, persistent Log In visibility, circular-mark geometry, wordmark readability, navigation/login overlap, and two-column/stacked hero coherence. The in-app browser was unavailable during this run, so those rendered cases remain part of manual visual review rather than an automated PASS claim.
- Header Log In appears exactly once per page outside the collapsible navigation and continues to use the single configured destination
- Header uses the distinct 512×512 institutional seal derivative with transparent exterior, an ivory circular field, and restrained gold/black rings; footer, favicon, and touch treatments remain unchanged
- Homepage uses the separate 900×830 artwork-forward alpha-PNG derivative; it preserves the approved connected black/gold artwork and HINDSFOOT OS identity, omits only the embedded principle line, and removes the textured ivory field without a frame or shadow
- Editorial hero retains two columns at 960px and above, centers its stacked composition below 960px, and renders the locked descriptor with local serif small caps and fine gold rules
- Homepage journey uses a clear 3/2/1-column progression; preview windows use fictional static content with aligned navy/gold/ivory presentation and no repeated card-level Product preview labels
- Hindsfoot Model action contrast: ivory on navy 10.63:1; black on gold hover/focus 7.32:1; both exceed WCAG AA for normal text
- Primary navigation consistently uses Request a Demonstration; persistent Log In and its single configuration boundary are unchanged
- Authenticated application changes after candidate freeze: none
- Work & Learning Hub claims are governed by a dedicated architecture record: 9 verified implemented capabilities, 6 verified adjacent capabilities, 8 architecturally planned gaps, and 5 expressly unsupported claims.
- The Hub is presented as a supporting lane rather than a seventh stage; How It Works retains exactly Intake, Guided proposal, Explicit confirmation, Governed record, Administration, and Continuity.
- Draft questions, notes, assumptions, and unfinished plans remain explicitly distinct from institutional facts and require authorized human confirmation before promotion.
- Genealogy now presents an accessible conceptual relationship-evidence map, four compact capability panels, a five-stage governed progression, and a fictional nonpersonal review workspace.
- Relationship assertions remain explicitly unconfirmed until evidence is reviewed and status is recorded; the page states that no stage advances automatically.
- Genealogy limitations concerning uncertainty, DNA conclusions, inheritance, ownership, citizenship, legal status, entitlement, and professional review remain intact.
- The genealogy hero map uses six non-overlapping CSS Grid nodes, a separate lower connector layer, and a connector-free single-column mobile sequence.
- How It Works contains six journey cards with one explicit gold step-number element per card and no generated pseudo-counter.

Manual rendered review is complete for desktop and narrow layouts, including the Work & Learning Hub integrations, six-step journey and number correction, responsive Menu and persistent Log In, Genealogy and Legacy relationship map and progression, fictional previews, and the absence of visible overlap or horizontal overflow. HOS-WEB-1D.1 accepts that operator evidence as the rendered-browser certification component.
