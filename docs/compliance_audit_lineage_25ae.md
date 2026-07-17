# Step 25AE Compliance Audit Lineage

## Purpose

Step 25AE separates historical H6 Compliance certification evidence from the
current least-privilege Compliance successor suite.

Historical H6 audits are preserved as evidence of the former pre-25AB/25AC/25AD
architecture. They should not be rewritten merely to pass the current contract.
Current Compliance validation should use the successor suite below.

## Current Successor Suite

| Current audit | Purpose | Status |
| --- | --- | --- |
| `scripts/audit_compliance_authority_test_harness_25ab.py` | Canonical permission-to-authority registry and pure least-privilege decisions | Current |
| `scripts/audit_compliance_live_authority_integration_25ac.py` | Live route/service authority integration against temporary activated database | Current |
| `scripts/audit_compliance_attribution_persistence_and_audit_modernization_25ad.py` | Exception attribution persistence, requester/approver SOD, and audit metadata | Current |
| `scripts/audit_compliance_current_successor_suite_25ae.py` | Runs and certifies the current successor suite without historical H6 rewrites | Current |

## Historical H6 Evidence

These files remain historical evidence unless a future milestone creates an
explicit successor or archival copy. Several intentionally reference older
active database hashes or the prior `compliance_admin`/Admin bypass contract.

| Historical audit | Classification | Current successor |
| --- | --- | --- |
| `scripts/audit_authorization_baseline_reconciliation_17q_h6a_r6.py` | Historical fixed-baseline authorization reconciliation | 25AB/25AC/25AD |
| `scripts/audit_compliance_review_temporary_activation_17q_h6c.py` | Historical temporary activation smoke with fixed SHA | 25AC/25AD |
| `scripts/audit_compliance_review_service_workflow_17q_h6c.py` | Historical service workflow using `compliance_admin` | 25AC/25AD |
| `scripts/audit_compliance_review_lifecycle_authorization_17q_h6c.py` | Historical lifecycle authorization using `compliance_admin` | 25AC |
| `scripts/audit_compliance_review_audit_ledger_17q_h6c.py` | Historical audit-ledger coverage using `compliance_admin` | 25AD |
| `scripts/audit_compliance_review_h6d_common.py` | Historical H6D shared route harness using `compliance_admin` | 25AC/25AD |
| `scripts/audit_compliance_review_write_routes_17q_h6d.py` | Historical H6D wrapper | 25AC/25AD |
| `scripts/audit_compliance_review_route_authorization_17q_h6d.py` | Historical H6D wrapper | 25AC |
| `scripts/audit_compliance_review_operator_ui_17q_h6d.py` | Historical H6D wrapper | 25AC |
| `scripts/audit_compliance_review_form_controls_17q_h6d.py` | Historical H6D wrapper | 25AC |
| `scripts/audit_compliance_review_concurrency_idempotency_17q_h6d.py` | Historical H6D wrapper | 25AC |
| `scripts/audit_compliance_review_permission_governance_17q_h6e.py` | Historical fixed-SHA permission governance | 25AB/25AC |
| `scripts/audit_compliance_review_production_migration_plan_17q_h6e.py` | Historical fixed-SHA production plan rehearsal | 25AC/25AD |
| `scripts/audit_compliance_review_activation_readiness_17q_h6e.py` | Historical fixed-SHA activation readiness | 25AE successor suite |
| `scripts/audit_compliance_review_rollback_plan_17q_h6e.py` | Historical rollback plan rehearsal with fixed SHA | 25AE successor suite |
| `scripts/audit_compliance_review_go_no_go_17q_h6e.py` | Historical fixed-SHA go/no-go audit | 25AE successor suite |
| `scripts/audit_compliance_review_pre_activation_certification_17q_h6f.py` | Historical pre-activation certification bundle | 25AE successor suite |
| `scripts/audit_compliance_review_h6b_h6f_publication_scope.py` | Historical wrapper for H6F publication scope | 25AE successor suite |

## Current But Static/Architecture Audits

These can remain readable as architectural checks. If they conflict with the
least-privilege contract later, add a successor rather than rewriting the
historical meaning.

| Audit | Classification |
| --- | --- |
| `scripts/audit_compliance_review_activation_architecture_17q_h6b.py` | Static architecture check |
| `scripts/audit_compliance_review_governed_migration_17q_h6b.py` | Historical temporary migration check |
| `scripts/audit_compliance_review_foundation_17q_g.py` | Historical foundation closure check |
| `scripts/audit_compliance_review_architecture_17q_f.py` | Static architecture check |
| `scripts/audit_compliance_review_readonly_ui_17q_h.py` | Historical fixed-SHA read-only UI check |

## Operating Rule

For current Compliance authorization certification, run:

```text
python scripts/audit_compliance_current_successor_suite_25ae.py
```

This runner executes the current successor suite and verifies that the active
database and export policy remain unchanged.
