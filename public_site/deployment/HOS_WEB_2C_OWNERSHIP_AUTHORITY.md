# HOS-WEB-2C Deployment Ownership and Authority Lock

Status: NON-OPERATIONAL READINESS RECORD — EXTERNAL ACTIONS NOT AUTHORIZED
Baseline: `548fab59b2374149040daeb2c2db2ae9ad0eab35`
Decision date: 2026-08-15 (America/New_York)

## Purpose and authority boundary

This record identifies the ownership and authority that must exist before acquisition, provider connection, DNS/TLS work, preview deployment, or production deployment. It does not assign provider access, create credentials, prove corporate authority, or authorize an external action.

Luna Isaac Mishoe III is recorded as the **PROVISIONAL** project owner and final business decision authority based on the approved project direction. That designation does not prove registrar, billing, DNS, Cloudflare, security, legal, or deployment authority.

Status meanings:

- **VERIFIED**: documentary evidence of the specific authority is present and approved.
- **PROVISIONAL**: a supported working assignment exists, but role-specific evidence is incomplete.
- **UNASSIGNED**: no supported assignment exists.

## Ownership and authority matrix

| # | Role | Proposed owner | Status | Required evidence | Authority granted | Authority withheld | Separation-of-duties concern | Required action before deployment |
|---|---|---|---|---|---|---|---|---|
| 1 | Brand owner / decision authority | Luna Isaac Mishoe III | PROVISIONAL | Signed brand/decision authority record | Approve business direction after evidence review | Registrar, billing, DNS, provider, legal, and security powers | Final business approval should not substitute for technical or legal review | Verify organizational ownership and record approval scope |
| 2 | Domain registrant authority | Unassigned | UNASSIGNED | Organizational authorization and registrant record | None | Registration, transfer, renewal, contact changes | Registrant control must survive individual unavailability | Assign durable organizational registrant authority |
| 3 | Domain billing contact | Unassigned | UNASSIGNED | Billing authorization and renewal method | None | Purchases and renewals | Separate payment failure alerts from registrar administration | Assign and document renewal funding |
| 4 | Registrar administrator | Unassigned | UNASSIGNED | Named account, MFA, recovery evidence, least privilege | None | Registrar account and domain changes | Avoid sole-person control | Assign primary and successor administrators |
| 5 | Cloudflare account owner | Unassigned | UNASSIGNED | Organizational account ownership and MFA record | None | Account creation, access, provider changes | Must not depend on a shared personal password | Establish organization-controlled account |
| 6 | Cloudflare billing owner | Unassigned | UNASSIGNED | Billing authorization and plan approval | None | Purchases and plan changes | Billing should not silently confer deployment authority | Assign billing owner and alerts |
| 7 | Cloudflare Pages project administrator | Unassigned | UNASSIGNED | Project role assignment and least-privilege review | None | Project creation, configuration, deletion, deployment | Separate administration from production approval | Assign after account ownership is verified |
| 8 | GitHub repository administrator | Unassigned | UNASSIGNED | Repository role evidence and branch-protection review | None | Provider authorization and repository settings | GitHub control does not prove business or provider authority | Assign and verify minimal provider permissions |
| 9 | DNS administrator | Unassigned | UNASSIGNED | DNS role assignment, MFA, change procedure | None | Nameserver and record changes | DNS change and deployment approval should be independently reviewable | Assign with reviewed change authority |
| 10 | TLS / certificate administrator | Unassigned | UNASSIGNED | Certificate/CAA policy ownership and incident procedure | None | CAA, certificate, HSTS, preload changes | Premature HSTS can affect all subdomains | Assign before certificate or HSTS work |
| 11 | Production deployment approver | Unassigned | UNASSIGNED | Written promotion authority and checklist | None | Production promotion | Should not be the sole artifact builder | Assign independent approval authority |
| 12 | Preview deployment approver | Unassigned | UNASSIGNED | Preview policy and access-list approval | None | Preview publication | Preview must remain restricted and fictional-data only | Assign before any preview deployment |
| 13 | Authenticated-application owner | Unassigned | UNASSIGNED | Application operations and security authority | None | `app.hindsfoot-os.com` activation | Must remain separate from static-site operations | Assign in a separate authenticated-host phase |
| 14 | Privacy / legal review owner | Unassigned | UNASSIGNED | Qualified review engagement and acceptance record | None | Legal/privacy acceptance | Business approval is not legal review | Assign before public activation or form processing |
| 15 | Accessibility review owner | Unassigned | UNASSIGNED | WCAG review scope and acceptance evidence | None | Accessibility acceptance | Independent review remains advisable | Assign before production promotion |
| 16 | Security review owner | Unassigned | UNASSIGNED | Security test scope, header/CSP acceptance, incident role | None | Security acceptance | Separate from deploy operator where practical | Assign before preview credentials or production |
| 17 | Monitoring / incident-response owner | Unassigned | UNASSIGNED | On-call path, alert recipients, escalation procedure | None | Incident response and monitoring changes | Alerts require successor coverage | Assign provider and recipients |
| 18 | Rollback authority | Unassigned | UNASSIGNED | Rollback decision criteria and tested procedure | None | Production rollback | Must be reachable independently of deploy operator | Assign and test before production |
| 19 | Backup / evidence custodian | Unassigned | UNASSIGNED | Retention schedule, access controls, restoration procedure | None | Evidence retention/disposal | Deployment evidence and inquiry data require different retention | Assign for permanent certification evidence |
| 20 | Successor / emergency administrator | Unassigned | UNASSIGNED | Succession designation, recovery procedure, periodic test | None | Emergency recovery | No single-person dependency | Assign before production |

## Counts and unresolved authority

- VERIFIED: **0**
- PROVISIONAL: **1**
- UNASSIGNED: **19**

No role in this matrix currently authorizes domain acquisition, provider connection, DNS/TLS mutation, preview deployment, or production deployment. At least two authorized administrators, secure MFA, preserved recovery material, least privilege, and successor access are prerequisites.
