# OPEN DECISIONS

1. Should `home` (`/`) be explicitly allowed for Viewer in `ROLE_RULES`?
   - Recommended: yes, if it remains a general safe landing page.

2. Should `workflow_hub` (`/workflow`) be Viewer-visible?
   - Recommended: no by default; keep Admin/Trustee unless reviewed.

3. Should `portfolio_dashboard` be explicitly Viewer-allowed?
   - Recommended: yes, because login already uses it as Viewer redirect target.

4. Should Audit remain permanently Admin-only?
   - Recommended: yes, unless a limited Trustee audit view is intentionally designed later.

5. Which historic notes from earlier project threads should be imported into this continuity package?
   - Requires targeted enrichment later from prior handoff summaries or pasted notes.

6. Should the nav conditionals later be refactored into a shared helper rather than inline Jinja role checks?
   - Recommended later, not now.
