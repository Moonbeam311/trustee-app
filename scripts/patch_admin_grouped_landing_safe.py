from pathlib import Path

path = Path("templates/admin_index.html")
text = path.read_text(encoding="utf-8", errors="ignore")

marker = "<!-- POST-V2-3A-R1 ADMIN OPERATOR GROUPS -->"
if marker in text:
    print("POST-V2-3A-R1 grouped section already present; no change.")
    raise SystemExit(0)

section = """
<!-- POST-V2-3A-R1 ADMIN OPERATOR GROUPS -->
<section class="admin-operator-groups">
  <h2>Admin Operator Groups</h2>
  <p>Grouped operator access for administration, governance, records, continuity, security, and diagnostics. This section reorganizes navigation only.</p>
  <div class="workspace-grid">
    <a class="workspace-card" href="{{ url_for('system_health_dashboard') }}"><strong>System Status</strong><span>Health, system checks, and operating condition.</span></a>
    <a class="workspace-card" href="{{ url_for('governance_dashboard') }}"><strong>Governance</strong><span>Directives, policies, relationships, evidence, and V2 certification.</span></a>
    <a class="workspace-card" href="{{ url_for('matters_dashboard') }}"><strong>Matters / Trusts</strong><span>Matter records, trust operations, intake, and execution.</span></a>
    <a class="workspace-card" href="{{ url_for('fiduciary_dashboard') }}"><strong>People / Fiduciaries</strong><span>Fiduciaries, users, roles, and institutional actors.</span></a>
    <a class="workspace-card" href="{{ url_for('export_center') }}"><strong>Documents / Exports</strong><span>Generated records, documents, exports, media, and forms.</span></a>
    <a class="workspace-card" href="{{ url_for('continuity_asset_dashboard') }}"><strong>Archive / Continuity</strong><span>Continuity assets, archive readiness, and recovery support.</span></a>
    <a class="workspace-card" href="{{ url_for('security_dashboard') }}"><strong>Security / Access</strong><span>Security, permissions, roles, and user access.</span></a>
    <a class="workspace-card" href="{{ url_for('admin_audit_log') }}"><strong>Developer / Diagnostics</strong><span>Audit log, diagnostics, storage checks, and developer review.</span></a>
  </div>
  <p><strong>Certified Baseline Preserved:</strong> v2-certified-baseline-2026-07-10</p>
</section>
<!-- /POST-V2-3A-R1 ADMIN OPERATOR GROUPS -->
"""

if "<body>" in text:
    text = text.replace("<body>", "<body>\n" + section, 1)
else:
    text = section + "\n" + text

path.write_text(text, encoding="utf-8")
print("POST-V2-3A-R1 grouped Admin operator section inserted.")
