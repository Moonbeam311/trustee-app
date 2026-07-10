from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CERTIFIED_TAG = 'v2-certified-baseline-2026-07-10'
EXPECTED_COMMIT = '607eb174354510b64804f8dd8e4b87756f25f366'

def git(args):
    p = subprocess.run(['git', *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def check(name, ok, detail):
    print(('PASS' if ok else 'FAIL') + ': ' + name + ' — ' + detail)
    return 0 if ok else 1

template = ROOT / 'templates' / 'admin_index.html'
text = template.read_text(encoding='utf-8', errors='ignore') if template.exists() else ''
plain = re.sub(r'<[^>]+>', '', text)

fail = 0

print('POST-V2-3F ADMIN GOVERNANCE LABEL PRECISION AUDIT')
print('=' * 72)

code, branch, err = git(['branch', '--show-current'])
fail += check('branch allowed', branch == 'post-v2-planning', branch or err)

code, tag_commit, err = git(['rev-parse', CERTIFIED_TAG + '^{commit}'])
fail += check('certified tag matches expected commit', tag_commit == EXPECTED_COMMIT, tag_commit or err)

fail += check('precision marker present', 'POST-V2-3F GOVERNANCE LABEL PRECISION FIX ACTIVE' in text, 'present' if 'POST-V2-3F GOVERNANCE LABEL PRECISION FIX ACTIVE' in text else 'missing')

fail += check('governance label spans retained', text.count('section-governance-label') >= 20, 'count=' + str(text.count('section-governance-label')))

bad_phrases = [
    'Existing trust? Use Existing Trust Operations ACTIVE OPERATING SURFACE',
    'Need proof, review, or audit trail? Open the Lifecycle Ledger',
    'No routes or links are removed in this milestone. Legacy Compatibility',
]

bad_found = [x for x in bad_phrases if x in plain]
fail += check('labels not injected into known body sentences', not bad_found, 'none' if not bad_found else '; '.join(bad_found))

fail += check('active labels still present', text.count('ACTIVE OPERATING SURFACE') >= 8, 'count=' + str(text.count('ACTIVE OPERATING SURFACE')))
fail += check('duplicate labels still present', text.count('DUPLICATE ENTRY POINT') >= 4, 'count=' + str(text.count('DUPLICATE ENTRY POINT')))
fail += check('system control labels still present', text.count('PROTECTED SYSTEM CONTROL') >= 3, 'count=' + str(text.count('PROTECTED SYSTEM CONTROL')))

code, status, err = git(['status', '--short'])
bad_db = [line for line in status.splitlines() if 'data/trustee_app.db' in line or line.endswith('.db')]
fail += check('runtime database not modified', not bad_db, 'none' if not bad_db else '\n'.join(bad_db))

print('')
print('checks_failed:', fail)
print('RESULT: PASS' if fail == 0 else 'RESULT: FAIL')
raise SystemExit(0 if fail == 0 else 1)
