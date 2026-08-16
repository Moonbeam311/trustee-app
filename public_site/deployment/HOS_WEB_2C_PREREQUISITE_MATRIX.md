# HOS-WEB-2C Legal, Privacy, Accessibility, Operations, and Authorization Gates

Status: PREREQUISITE LOCK — EXTERNAL ACTIONS NOT AUTHORIZED

## Locked hostname and security policy

- Canonical public URL: `https://www.hindsfoot-os.com/`
- Apex: `https://hindsfoot-os.com/`, permanently redirected to canonical `www` only after authorization
- Authenticated application: `https://app.hindsfoot-os.com/`
- Restricted staging: `https://staging.hindsfoot-os.com/`
- Production and staging are distinct; staging is access-controlled and `noindex, nofollow, noarchive`.
- Public deployment receives no application secrets, database, private record, authenticated code, or trust document.
- HTTPS is required. HSTS `includeSubDomains` and preload remain deferred until every subdomain is ready.
- Production promotion requires explicit approval of an immutable tested artifact. Artifact hashes, source commit, deployment ID, logs, and rollback target are retained.
- Login may point to the authenticated hostname only after that destination is separately deployed, secured, tested, and authorized. No public link may falsely imply current availability.

## Prerequisite matrix

| Item | Status | Evidence | Required next action |
|---|---|---|---|
| Public privacy notice | PARTIALLY SATISFIED | Preview notice exists; production review remains recorded | Qualified privacy review and owner acceptance |
| Terms / acceptable use | PARTIALLY SATISFIED | Preview terms exist; production legal review remains recorded | Qualified review before launch |
| Contact/demo data handling | UNSATISFIED | Form inactive; processor, recipients, retention, deletion, and incident owner unselected | Approve processor and minimum-data workflow in a separate phase |
| Cookie/analytics policy | SATISFIED | Current static site requires no analytics cookies; analytics locked disabled | Reassess only if tracking is separately proposed |
| Accessibility review | PARTIALLY SATISFIED | Practices and static assertions exist; feedback channel and final acceptance owner absent | Assign reviewer and feedback channel; run final review |
| WCAG target | PARTIALLY SATISFIED | WCAG AA contrast/focus requirements are recorded | Define final conformance scope and acceptance evidence |
| Trademark/name clearance | UNSATISFIED | Moderate preliminary conflict signal; no legal clearance | Counsel review and documented risk acceptance |
| Public claims/disclaimers | PARTIALLY SATISFIED | Claims audits and software/professional boundaries exist | Final production content/legal acceptance |
| Security contact | UNSATISFIED | Role-based future address is not active; owner absent | Assign owner and verified channel |
| Incident-response procedure | UNSATISFIED | Ownership and escalation path absent | Approve response, notification, and recovery procedure |
| Records-retention policy | PARTIALLY SATISFIED | Permanent deployment evidence retention is locked; inquiry retention unset because form inactive | Assign custodian and schedule provider logs; set inquiry retention before activation |
| Monitoring | UNSATISFIED | Required checks listed; provider and recipients unresolved | Select provider, thresholds, recipients, and escalation |
| Rollback | PARTIALLY SATISFIED | Immutable artifact/last-certified target required; authority and tested procedure absent | Assign authority and test rollback before production |
| Public/authenticated boundary | SATISFIED | Separate hostname, project, runtime, credentials, and artifact boundary certified | Reverify at deployment and post-deployment |

Counts: **SATISFIED 2; PARTIALLY SATISFIED 6; UNSATISFIED 6; NOT APPLICABLE 0.**

## Ordered external-action authorization gates

Passing HOS-WEB-2C does not pass any external-action gate.

| Gate | Current status | Approving authority | Required evidence | Permitted action after pass | Prohibited before pass | Pass condition | Stop condition |
|---|---|---|---|---|---|---|---|
| 1 Name-risk acceptance | PENDING | Verified brand authority plus qualified counsel | Authoritative trademark/business-name review and written risk advice | Advance to acquisition decision | Acquisition, public use, deployment | Written acceptance of counsel-reviewed risk | High/unaccepted risk or ambiguous authority |
| 2 Domain acquisition authorization | BLOCKED BY GATE 1 | Verified brand and financial authority | Current registrar availability, approved price/term, registrant plan | One bounded acquisition phase | Checkout, reservation, purchase | Exact candidate and transaction authority approved | Domain unavailable, altered spelling, or unapproved terms |
| 3 Registrant and billing ownership | UNASSIGNED | Organizational authority | Registrant, billing, renewal, MFA, recovery, successor evidence | Establish controlled registrar ownership | Personal/shared credentials or unsupported registrant | Durable ownership and renewal controls verified | Sole-person dependency or missing recovery |
| 4 Cloudflare account ownership | UNASSIGNED | Organizational/provider authority | Account owner, billing, MFA, two admins, recovery, least privilege | One bounded account/project setup phase | Account/project connection | Organization-controlled account accepted | Personal/shared control or unapproved cost |
| 5 DNS and TLS authority | UNASSIGNED | Domain owner and security reviewer | DNS admin, change plan, CAA/TLS/HSTS sequence, rollback | Bounded DNS/TLS configuration after later approval | Nameserver, record, certificate, HSTS changes | Reviewed authority and reversible plan | Unknown subdomain readiness or authority |
| 6 Preview-access policy | PARTIALLY LOCKED | Preview approver and security owner | Identity/access design, generated-URL coverage, noindex proof, recovery | Restricted fictional-data preview after explicit approval | Public preview or real data | Access tests and preview policy accepted | Any public discovery or access bypass |
| 7 Legal/privacy/accessibility acceptance | PENDING | Qualified reviewers and business authority | Accepted privacy, terms, claims, accessibility, feedback process | Advance toward production authorization | Production activation or data collection | All production reviews signed | Material unresolved legal/privacy/accessibility issue |
| 8 Monitoring and rollback ownership | UNASSIGNED | Operations/security authority | Owners, alerts, incident path, tested rollback, last artifact | Operate approved monitoring and rollback | Production without coverage | Monitoring and rollback test accepted | Missing recipient, authority, or restore proof |
| 9 Artifact recertification | REQUIRED BEFORE DEPLOYMENT | Certification reviewer | Fresh 25-file manifest/hash, secret/link/accessibility/header checks | Identify immutable deployment candidate | Rebuild at provider or repository-root upload | All audits pass on exact artifact | Hash drift, extra file, or audit failure |
| 10 Deployment authorization | NOT AUTHORIZED | Production approver and business authority | Gates 1–9 evidence, deployment/rollback plan | One bounded preview/production action as separately specified | Any provider mutation or deploy | Explicit written authorization naming artifact and target | Missing gate or ambiguous destination |
| 11 Production deployment | NOT REACHED | Production deploy operator under approver authority | Authorized immutable artifact, DNS/TLS readiness, change window | Deploy exact artifact once | Rebuild, scope expansion, app deployment | Provider result matches artifact and target | Unexpected provider behavior or hash mismatch |
| 12 Post-deployment verification | NOT REACHED | Independent verifier / incident owner | DNS, TLS, redirects, headers, links, accessibility, robots, canonical, login boundary, monitoring | Accept production or invoke rollback | Silent acceptance after failed check | All checks pass and evidence retained | Any safety, privacy, access, or integrity discrepancy |

## Acceptance and stop conditions

This readiness lock passes when classifications, unresolved roles, policies, and ordered gates are explicit and deterministic audits pass without external action. Stop any later phase on repository divergence, unexpected artifact change, credential exposure, unauthorized provider access, name-risk rejection, role ambiguity, public preview exposure, or failure of an artifact/security/legal/accessibility gate.
