from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

paths = {
    "app": ROOT / "app.py",
    "service": ROOT / "services" / "services_work_learning_questions.py",
    "workspace": ROOT / "templates" / "workspace_detail.html",
    "list": ROOT / "templates" / "workspace_questions.html",
    "form": ROOT / "templates" / "workspace_question_form.html",
    "detail": ROOT / "templates" / "workspace_question_detail.html",
    "test": ROOT / "tests" / "test_v3_mod_wlh_p02.py",
}

checks = []


def check(label, condition):
    checks.append((label, bool(condition)))
    print(f"{'PASS' if condition else 'FAIL'} - {label}")


for label, path in paths.items():
    check(f"exists: {label}", path.is_file())

app = paths["app"].read_text(encoding="utf-8")
service = paths["service"].read_text(encoding="utf-8")
workspace = paths["workspace"].read_text(encoding="utf-8")
question_list = paths["list"].read_text(encoding="utf-8")
question_form = paths["form"].read_text(encoding="utf-8")
question_detail = paths["detail"].read_text(encoding="utf-8")

check(
    "question table",
    "CREATE TABLE IF NOT EXISTS hub_questions" in service,
)

check(
    "learning-resource relationship table",
    "CREATE TABLE IF NOT EXISTS hub_question_learning_resources" in service,
)

check(
    "question statuses",
    all(
        token in service
        for token in ("open", "researching", "resolved", "closed")
    ),
)

check(
    "resource types",
    all(
        token in service
        for token in ("learning_article", "trust_type", "form_guide")
    ),
)

check(
    "question firm scope",
    "firm_id" in service,
)

check(
    "question owner scope",
    "owner_id" in service,
)

check(
    "duplicate identity recovery",
    "candidate_relationship_id" in service
    and "SELECT relationship_id" in service,
)

for endpoint in (
    "workspace_questions",
    "workspace_question_new",
    "workspace_question_detail",
    "workspace_question_status",
    "workspace_question_resource_add",
    "workspace_question_resource_remove",
):
    check(f"route function: {endpoint}", f"def {endpoint}" in app)

check(
    "viewer read role",
    '"workspace_questions": {"Admin", "Trustee", "Viewer"}' in app,
)

check(
    "write role restriction",
    '"workspace_question_new": {"Admin", "Trustee"}' in app
    and '"workspace_question_status": {"Admin", "Trustee"}' in app
    and '"workspace_question_resource_add": {"Admin", "Trustee"}' in app
    and '"workspace_question_resource_remove": {"Admin", "Trustee"}' in app,
)

p02_routes = app[
    app.find("def workspace_questions"):
    app.find("def discussion_dashboard")
]

check(
    "no browser supplied firm scope",
    'request.form.get("firm_id")' not in p02_routes,
)

check(
    "no browser supplied owner scope",
    'request.form.get("owner_id")' not in p02_routes,
)

check(
    "CSRF on P-02 writes",
    p02_routes.count("validate_csrf_token()") >= 4,
)

check(
    "learning article validation",
    "get_learning_article_by_id" in p02_routes,
)

check(
    "trust type validation",
    "get_trust_type_detail" in p02_routes,
)

check(
    "form guide validation",
    "get_form_guide_by_name" in p02_routes,
)

check(
    "workspace question entry",
    "View Questions" in workspace
    and "New Question" in workspace,
)

combined = question_list + question_form + question_detail

check(
    "working artifact language",
    "working" in combined.lower(),
)

check(
    "governed-fact boundary",
    "governed fact" in combined.lower(),
)

check(
    "learning resources preserve non-authoritative boundary",
    "learning" in question_detail.lower()
    and "governed fact" in question_detail.lower(),
)

check(
    "no P-07 promotion control",
    "promote to governed" not in combined.lower(),
)

check(
    "no definitive-answer engine",
    "definitive answer" not in (
        service + question_detail
    ).lower(),
)

passed = sum(ok for _, ok in checks)
failed = len(checks) - passed

print()
print("V3-MOD-WLH P-02 STATIC AUDIT")
print(f"Assertions passed: {passed}")
print(f"Assertions failed: {failed}")
print("RESULT:", "PASS" if failed == 0 else "FAIL")

sys.exit(0 if failed == 0 else 1)
