# HOS-WEB-2B Deployment Configuration and Destination Decision Lock

## 1. Purpose

This record locks a future, nonactive deployment architecture for the certified Hindsfoot public site. It authorizes no domain purchase, account connection, DNS mutation, hosting project, destination activation, deployment, or publication.

## 2. Certified baseline

- Repository branch: `system-1-annual-evaluation`
- Certified source commit: `db051e2ba45d5cf1b9f163e653e7ba5d2443d3fc`
- Deployable boundary: the exact 25-file allowlist in `deployment/public-artifact-manifest.json`
- Repository-only records, scripts, audits, and documentation are excluded from the artifact.

## 3. Approved domain candidate

The approved candidate spelling is `hindsfoot-os.com`.

## 4. Domain-ownership disclaimer

Domain availability, registration, ownership, trademark clearance, DNS, certificates, and email service are unverified and incomplete. This record must not be represented as evidence that the candidate is owned, registered, active, available, or legally cleared.

## 5. Hostname architecture

- Canonical public site: `https://www.hindsfoot-os.com/`
- Apex: `https://hindsfoot-os.com/`, intended to redirect permanently to the canonical public host
- Authenticated application: `https://app.hindsfoot-os.com/`
- Protected preview: `https://staging.hindsfoot-os.com/`

These are inactive architecture decisions, not live destinations.

## 6. Preferred host

Cloudflare Pages is preferred for the static public site.

## 7. Fallback host

Vercel Pro is the approved fallback subject to a separate provider, privacy, billing, security, and configuration review.

## 8. Deployment mode

Use artifact-based Direct Upload through controlled CI. The reviewed immutable artifact must be promoted without rebuilding. Automatic production deployment on every push is prohibited.

## 9. Public/authenticated separation

Public hosting and authenticated Hindsfoot OS must remain separate projects, runtimes, credentials, hostnames, databases, and security boundaries. The public host imports no Flask code, configuration, session data, or protected record.

## 10. Deployment artifact boundary

Deploy only the deterministic 25-file allowlist: 14 root HTML pages, one CSS file, two JavaScript files, and eight PNG branding assets. Repository root, audits, scripts, architecture records, tests, databases, migrations, private evidence, and Git metadata are prohibited.

## 11. Login architecture

The future destination is `https://app.hindsfoot-os.com/` with state `CONFIGURED_ARCHITECTURALLY_NOT_ACTIVE`. The public host never collects or proxies credentials, embeds Login in an iframe, or accepts an open redirect. Authenticated cookies remain narrowly scoped to the application. Return navigation must use an allowlisted public destination. Activation requires ownership, DNS, TLS, deployed application, and security testing. Existing public HTML remains unchanged.

## 12. Demonstration/contact architecture

The form remains inactive and the processor is `UNSELECTED`. Future minimum fields are name, optional organization, business email, general area of interest, preferred contact method, and consent acknowledgment. Trust, estate, tax, financial, health, genealogy, identity, credential, account-number, legal-evidence, and attachment collection is prohibited.

Future role-address patterns are `inquiries@`, `privacy@`, `accessibility@`, and `security@` on the candidate domain. They do not exist until separately configured and verified. Any processor must be isolated from authenticated data and provide abuse control, least-data collection, consent, delivery verification, retention, deletion, authorized recipients, and incident ownership. Promotion into governed records requires deliberate review.

## 13. Analytics decision

Analytics are disabled. No analytics, cookies, pixels, session replay, advertising tags, fingerprinting, or user-level tracking may be introduced without a separate privacy, processor, consent, disclosure, and CSP phase.

## 14. Privacy and legal boundaries

- Privacy: `PRESENT_PREVIEW_REQUIRES_PRODUCTION_REVIEW`
- Terms: `PRESENT_PREVIEW_REQUIRES_QUALIFIED_REVIEW`
- Accessibility: `PRACTICES_PRESENT_FEEDBACK_CHANNEL_PENDING`
- Software disclaimer: `PRESENT_REQUIRES_FINAL_PRODUCTION_REVIEW`
- Current static-site cookies: `NONE_REQUIRED_BY_CURRENT_STATIC_SITE`
- Contact-form privacy: `BLOCKED_UNTIL_PROCESSOR_AND_RETENTION_APPROVED`

No legal text is revised by this phase.

## 15. Accessibility-feedback architecture

The public accessibility practices remain present. A verified feedback channel, responsible recipient, response process, retention rule, and escalation owner must be approved before production.

## 16. Security headers

The provider-neutral blueprint locks `nosniff`, strict-origin referrer policy, least-privilege Permissions Policy, denial of framing, and CSP directives limiting base, object, frame ancestors, scripts, styles, fonts, images, connections, and forms. It contains no provider secret.

## 17. CSP staging

Preview begins with `Content-Security-Policy-Report-Only`. Enforcement follows successful preview verification. HSTS, `includeSubDomains`, and preload remain deferred until every required subdomain is HTTPS-ready and explicitly approved. Cross-origin isolation is not enabled without demonstrated need.

## 18. Preview controls

Staging requires access control, `noindex, nofollow, noarchive`, no public discovery, no production credentials, no real records or inquiries, fictional data only, and manual promotion approval. No access control is configured here.

## 19. Production promotion

Production uses the exact tested artifact without rebuilding. Human approval, source commit, manifest hashes, deployment ID, rollback target, and preserved evidence are required. Direct repository-root and unreviewed-branch deployment are prohibited.

## 20. Robots and indexing

Preview indexing is prohibited. Production may use index/follow only after legal, destination, header, canonical, accessibility, and operational gates pass.

## 21. Canonical and social URLs

The future canonical base is `https://www.hindsfoot-os.com/`. Each public page requires one canonical URL, HTTPS, the approved apex redirect, a decided trailing-slash rule, matching Open Graph URLs, and an approved public social image. Production metadata may contain no preview, localhost, or authenticated hostname. Metadata remains unchanged here.

## 22. Rollback

Every release must record an immutable prior deployment and one-action provider rollback. DNS fallback and TTLs require separate approval. Rollback authority is unresolved.

## 23. Monitoring

Future monitoring covers uptime, TLS, renewal, DNS changes, links, Login availability, form delivery if enabled, headers, CSP reports, robots, sitemap, canonical redirects, deployment failures, provider incidents, and artifact-hash drift. Provider and recipients are unresolved.

## 24. Credentials and least privilege

MFA and least privilege are required. Shared personal passwords are prohibited. Recovery codes require secure institutional preservation. At least two authorized administrators are required before production. No token, account ID, zone ID, password, or recovery code belongs in this repository.

## 25. Successor access

Primary and successor administrators, registrar owner, renewal owner, DNS administrator, deployment approver, rollback authority, monitoring recipients, and inquiry/privacy/accessibility/security contacts must be assigned without embedding personal credentials.

## 26. Evidence retention

Permanently preserve the source commit, artifact manifest and hashes, deployment ID, project identifier, hostname, timestamp, approver, audits, header/link/accessibility results, rollback target, DNS-state reference, and incident/rollback events as institutional certification records. Provider logs and inquiry data require separately approved shorter retention rules.

## 27. Unresolved assignments

- Registrar; DNS provider; organizational domain owner
- Primary and successor administrators; renewal-payment owner
- Login deployment owner; production approver; rollback authority
- Demonstration processor; inquiry recipients and retention owner
- Privacy, accessibility, security, legal, trademark, and domain-availability reviewers
- Monitoring provider and recipients

No unresolved assignment constitutes deployment authorization.

## 28. Stop conditions

Stop on a domain conflict, trademark concern, unapproved provider, missing responsible owner, secret requirement, manifest/hash mismatch, new deployable file, public/authenticated boundary violation, legal or accessibility blocker, insecure header requirement, unavailable rollback, remote source mismatch, or any request to expose protected records.

## 29. Acceptance criteria

Acceptance requires valid nonsecret blueprints, an exact hash-verified 25-file manifest, unchanged deployable bytes, passing certified and HOS-WEB-2B audits, zero secret/local-path/protected-reference findings, clean Git scope, and explicit false authorization states.

## 30. Subsequent phase sequence

Recommended HOS-WEB-2C scope: review and approve this decision lock, assign responsible roles, independently verify domain availability and trademark posture, select accounts/providers, and prepare a dry-run artifact and preview configuration. It must still prohibit production deployment, DNS activation, Login activation, form activation, and analytics until their individual gates pass.

## Decision state

`DEPLOYMENT_CONFIGURATION_LOCKED_NOT_AUTHORIZED_FOR_ACTIVATION`
