from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

SERVICE = ROOT / "services" / "guide_foundation.py"
PAGE = ROOT / "templates" / "guide_page.html"
PARTIAL = ROOT / "templates" / "_guide_ai_foundation.html"
TEST = ROOT / "tests" / "test_v3_aig_guide_foundation.py"

checks = []


def check(label, condition):
    checks.append((label, bool(condition)))
    print(f"{'PASS' if condition else 'FAIL'} - {label}")


for path in (SERVICE, PAGE, PARTIAL, TEST):
    check(f"exists: {path.relative_to(ROOT)}", path.is_file())

service = SERVICE.read_text(encoding="utf-8")
page = PAGE.read_text(encoding="utf-8")
partial = PARTIAL.read_text(encoding="utf-8")

check(
    "locked Guide principle",
    "The Guide interprets the governed institutional record" in service,
)

check(
    "no silent mutation rule",
    "must not silently mutate" in service,
)

for token in (
    "recorded_fact",
    "system_status",
    "source_supported_relationship",
    "inference",
    "conflict",
    "recommendation",
    "proposed_action",
    "operator_authorized_institutional_action",
):
    check(f"classification: {token}", token in service)

for token in (
    "documented",
    "corroborated",
    "inferred",
    "disputed",
    "unresolved",
):
    check(f"genealogy evidence state: {token}", token in service)

for token in (
    "Conflict detected",
    "Supporting evidence",
    "Proposed interpretation or correction",
    "Operator review",
    "Governed action",
    "Permanent audit record",
):
    check(f"conflict flow: {token}", token in service)

check(
    "Guide page includes foundation",
    '{% include "_guide_ai_foundation.html" %}' in page,
)

check(
    "foundation identifies governance boundary",
    "Governance boundary" in partial,
)

check(
    "foundation contains no form",
    "<form" not in partial.lower(),
)

check(
    "foundation contains no mutation control",
    all(
        token not in partial.lower()
        for token in (
            'type="submit"',
            "delete",
            "approve action",
            "execute action",
        )
    ),
)

passed = sum(ok for _, ok in checks)
failed = len(checks) - passed

print()
print("V3-AIG GUIDE FOUNDATION AUDIT")
print(f"Assertions passed: {passed}")
print(f"Assertions failed: {failed}")

if failed:
    print("RESULT: FAIL")
    sys.exit(1)

print("RESULT: PASS")
