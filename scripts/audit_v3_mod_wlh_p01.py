from pathlib import Path

root = Path(__file__).resolve().parents[1]

checks = []

def record(name, ok):
    checks.append((name, bool(ok)))
    print(("PASS" if ok else "FAIL") + " - " + name)

app = (root / "app.py").read_text(encoding="utf-8")
nav = (root / "templates" / "_platform_nav.html").read_text(encoding="utf-8")
tpl = (root / "templates" / "work_learning_hub.html").read_text(encoding="utf-8")

record("hub route", '@app.route("/work-learning-hub")' in app)
record("hub context builder", "def build_work_learning_hub_context():" in app)
record("hub role rule", '"work_learning_hub": {"Admin", "Trustee", "Viewer"}' in app)
record("firm-scoped workspace reuse", '"workspaces": get_all_workspaces()' in app)
record("Explore and Learn", "Explore and Learn" in tpl)
record("Work and Develop", "Work and Develop" in tpl)
record("Confirm and Govern", "Confirm and Govern" in tpl)
record("governance boundary", "Governance boundary:" in tpl)
record("hub navigation", '<a href="/work-learning-hub">Work & Learning Hub</a>' in nav)
record("existing /workspaces preserved", '@app.route("/workspaces")' in app)
record("no form in hub template", "<form" not in tpl.lower())
record("no POST control in hub template", 'method="post"' not in tpl.lower())
record("no promotion control in hub template", "promote" not in tpl.lower())

passed = sum(ok for _, ok in checks)
failed = len(checks) - passed

print()
print("V3-MOD-WLH P-01 STATIC AUDIT")
print(f"Assertions passed: {passed}")
print(f"Assertions failed: {failed}")
print("RESULT:", "PASS" if failed == 0 else "FAIL")
raise SystemExit(0 if failed == 0 else 1)
