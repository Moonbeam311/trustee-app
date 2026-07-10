from pathlib import Path
import re

path = Path('templates/admin_index.html')
text = path.read_text(encoding='utf-8', errors='ignore')

marker = '<!-- POST-V2-3F GOVERNANCE LABEL PRECISION FIX ACTIVE -->'

if marker in text:
    print('POST-V2-3F precision fix already active; no change.')
    raise SystemExit(0)

# Remove prior governance-label spans wherever they were inserted.
text = re.sub(r'\s*<span class="section-governance-label [^"]+">[^<]+</span>', '', text)

labels = {
    'Recommended Next Action': ('ACTIVE OPERATING SURFACE', 'active'),
    'Executive Home': ('ACTIVE OPERATING SURFACE', 'active'),
    'Continue Where You Left Off': ('ACTIVE OPERATING SURFACE', 'active'),
    'Recent Institutional Activity': ('ACTIVE OPERATING SURFACE', 'active'),
    'Institutional Command Center': ('ACTIVE OPERATING SURFACE', 'active'),
    'Legacy Compatibility Center': ('LEGACY COMPATIBILITY', 'legacy'),
    'Intake & Lifecycle Command Center': ('ACTIVE OPERATING SURFACE', 'active'),
    'Intake Command Center': ('ACTIVE OPERATING SURFACE', 'active'),
    'System Snapshot': ('ACTIVE OPERATING SURFACE', 'active'),
    'Existing Trust Operations': ('ACTIVE OPERATING SURFACE', 'active'),
    'Existing Trust Operations Dashboard': ('ACTIVE OPERATING SURFACE', 'active'),
    'Existing Trust Command Cards': ('DUPLICATE ENTRY POINT', 'duplicate'),
    'Legacy Quick Start': ('LEGACY COMPATIBILITY', 'legacy'),
    'Learning & Guidance Suite': ('DUPLICATE ENTRY POINT', 'duplicate'),
    'Hosted Baseline Seed': ('PROTECTED SYSTEM CONTROL', 'system'),
    'Database Backup': ('PROTECTED SYSTEM CONTROL', 'system'),
    'System Policy Controls': ('PROTECTED SYSTEM CONTROL', 'system'),
    'Report Launch Area': ('DUPLICATE ENTRY POINT', 'duplicate'),
    'Admin Tools': ('DUPLICATE ENTRY POINT', 'duplicate'),
    'Operational Shortcuts': ('DUPLICATE ENTRY POINT', 'duplicate'),
    'Security Layer': ('PROTECTED SYSTEM CONTROL', 'system'),
}

def badge(label_text, css):
    return ' <span class="section-governance-label ' + css + '">' + label_text + '</span>'

for heading, pair in labels.items():
    label_text, css = pair
    b = badge(label_text, css)
    applied = False

    # Prefer actual HTML heading tags.
    for tag in ['h1', 'h2', 'h3', 'h4', 'summary']:
        pattern = r'(<{tag}[^>]*>\s*){heading}(\s*</{tag}>)'.format(
            tag=tag,
            heading=re.escape(heading),
        )
        replacement = r'\1' + heading + b + r'\2'
        new_text, count = re.subn(pattern, replacement, text, count=1)
        if count:
            text = new_text
            applied = True
            break

    if applied:
        continue

    # Fallback: standalone line only, not body sentence.
    pattern = r'(^\s*)' + re.escape(heading) + r'(\s*$)'
    replacement = r'\1' + heading + b + r'\2'
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)

if '</head>' in text:
    text = text.replace('</head>', marker + '\n</head>', 1)
else:
    text = marker + '\n' + text

path.write_text(text, encoding='utf-8')
print('POST-V2-3F governance label precision fix applied.')
