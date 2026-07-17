"""Step 25AB pure Compliance authority actor fixtures."""

from __future__ import annotations

from services.services_compliance_authorization import build_test_actor_context


def unauthenticated_actor():
    return build_test_actor_context(actor_id=None, username=None, role=None, firm_id=None)


def viewer_no_compliance():
    return build_test_actor_context(actor_id="viewer-1", username="viewer", role="Viewer", firm_id="FIRM-001")


def trustee_no_compliance():
    return build_test_actor_context(actor_id="trustee-1", username="trustee", role="Trustee", firm_id="FIRM-001")


def admin_no_compliance(username="admin-user", firm_id="FIRM-001"):
    return build_test_actor_context(actor_id=username, username=username, role="Admin", firm_id=firm_id)


def admin_create_only():
    return build_test_actor_context(
        actor_id="admin-create",
        username="admin-create",
        role="Admin",
        firm_id="FIRM-001",
        effective_permissions={"create_compliance_review"},
    )


def username_admin_no_compliance():
    return build_test_actor_context(actor_id="admin", username="admin", role="Admin", firm_id="FIRM-001")


def master_admin_global_reader_no_mutation():
    return build_test_actor_context(
        actor_id="master-reader",
        username="master-reader",
        role="Admin",
        firm_id="FIRM-001",
        effective_permissions={"view_all_compliance_reviews"},
        master_admin=True,
        global_read=True,
    )


def actor_with_permission(permission, *, username="permitted", firm_id="FIRM-001"):
    return build_test_actor_context(
        actor_id=username,
        username=username,
        role="Trustee",
        firm_id=firm_id,
        effective_permissions={permission},
    )


def actor_with_unrelated_permission():
    return actor_with_permission("view_documents", username="unrelated")


def firm_one_actor(permission="create_compliance_review"):
    return actor_with_permission(permission, username="firm-one", firm_id="FIRM-001")


def firm_two_actor(permission="create_compliance_review"):
    return actor_with_permission(permission, username="firm-two", firm_id="FIRM-002")


def explicit_global_reader():
    return build_test_actor_context(
        actor_id="global-reader",
        username="global-reader",
        role="Admin",
        firm_id="FIRM-001",
        effective_permissions={"view_all_compliance_reviews"},
        global_read=True,
    )


def future_global_mutator(permission="create_compliance_review"):
    return build_test_actor_context(
        actor_id="global-mutator",
        username="global-mutator",
        role="Admin",
        firm_id="FIRM-001",
        effective_permissions={permission, "mutate_all_compliance_reviews"},
        global_mutation=True,
    )


def authority_basis_only():
    return build_test_actor_context(
        actor_id="basis-only",
        username="basis-only",
        role="Trustee",
        firm_id="FIRM-001",
        authority_basis="Basis without permission",
    )


def malformed_actor():
    return build_test_actor_context(actor_id="malformed", username=None, role="Trustee", firm_id=None)
