# HOS-WEB-2C Provider Readiness and Decision Record

Status: ARCHITECTURE REVIEW ONLY — NO ACCOUNT OR DEPLOYMENT ACTION AUTHORIZED
Reviewed: 2026-08-15 (America/New_York)

## Locked architecture

- Preferred provider: **Cloudflare Pages**
- Mode: **artifact-based Direct Upload through controlled CI**
- Fallback: **Vercel Pro**, only if Cloudflare later fails a verified requirement
- Deployable source: the exact 25-file allowlist in `public_site/deployment/public-artifact-manifest.json`
- Public, staging, and authenticated application surfaces remain separate projects, hostnames, credentials, runtimes, and security boundaries.
- `.openai/hosting.json` is not present.
- The repository contains no provider credential or live project configuration, and nothing reviewed implies an authorized automatic production deployment.

## Evidence-based comparison

| Requirement | Cloudflare Pages | Vercel Pro fallback | Readiness consequence |
|---|---|---|---|
| Prebuilt artifact upload | Direct Upload supports a folder of prebuilt assets through Wrangler | CLI supports prebuilt deployments | Both technically viable; only manifest-derived artifacts are permitted |
| Controlled CI | Official guidance supports Direct Upload from CI using scoped credentials | CLI/CI deployment supported | Workflow must require explicit promotion; push-triggered production is prohibited |
| Custom domains and TLS | Pages supports apex/subdomain custom domains and managed certificate issuance subject to DNS/CAA readiness | Custom domains and managed TLS supported | Domain ownership, DNS authority, and CAA/TLS review remain prerequisites |
| Apex-to-www redirect | Available through provider redirect/rules mechanisms; Pages `_redirects` does not provide general domain-level redirect by itself | Redirect/routing configuration available | Exact redirect mechanism must be approved later and tested; no rendered artifact change is authorized now |
| Preview deployments | Branch/hash previews supported; preview URLs are noindex by default | Preview deployments supported | Generated preview URLs must also be access-restricted and inventoried |
| Preview access | Cloudflare Access can restrict preview deployments; custom preview hostname requires a verified Access design | Vercel Authentication available; some protection options depend on plan/add-on | Access design, identity source, owner, cost, and recovery procedure are unresolved |
| GitHub permissions | Direct Upload avoids Cloudflare Git integration, but controlled CI still requires scoped repository/workflow and provider-token authority | Integration or CLI credentials require scoped access | No GitHub authorization or token may be created until roles are assigned |
| Environment variables | Not needed by the static artifact; provider secrets must never enter it | Same | Public project receives no application secrets |
| Build isolation | Prebuilt immutable artifact avoids provider rebuilding | Prebuilt mode available | Production must promote the tested artifact without rebuilding |
| Logs and auditability | Deployment IDs and lists are available through provider tooling | Deployment history and logs available | Source SHA, artifact hashes, deployment ID, approver, and results must be preserved institutionally |
| Rollback/recovery | Prior immutable deployments can support rollback; exact operational procedure must be tested | Rollback/redeployment facilities available | Last certified artifact and authority must be recorded before launch |
| Cost dependency | Pages/Access/account features and operational limits require plan confirmation | Pro is a paid fallback; advanced protection can add cost | Provider plan, billing owner, and access-control cost require explicit approval |
| Deletion and successor control | Project/deployment administration requires organization-controlled account and recovery | Same | Two administrators, MFA, recovery evidence, and deletion controls required |
| Authenticated Flask separation | Suitable when Pages receives only static allowlisted files | Suitable when maintained as separate project | Flask, databases, credentials, and private records are excluded categorically |

## Primary-source documentation reviewed

- Cloudflare Pages Direct Upload: `https://developers.cloudflare.com/pages/get-started/direct-upload/`
- Cloudflare Direct Upload with CI: `https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/`
- Cloudflare custom domains: `https://developers.cloudflare.com/pages/configuration/custom-domains/`
- Cloudflare preview deployments and Access: `https://developers.cloudflare.com/pages/configuration/preview-deployments/`
- Cloudflare redirects: `https://developers.cloudflare.com/pages/configuration/redirects/`
- Vercel CLI prebuilt deployment: `https://vercel.com/docs/cli/deploy`
- Vercel deployment protection: `https://vercel.com/docs/deployment-protection`

## Classification and conditions

Provider classification:

**CLOUDFLARE REMAINS PREFERRED  ACCOUNT AND AUTHORITY SETUP REQUIRED**

Cloudflare remains technically suitable for the 25-file static artifact. This does not authorize account creation, Direct Upload, CI credentials, custom-domain attachment, Access configuration, DNS/TLS changes, preview publication, or production deployment.

Open conditions:

1. Establish organization-controlled Cloudflare ownership, billing, MFA, recovery, and successor administration.
2. Select a least-privilege CI credential design and prevent deployment on every push.
3. Prove staging/custom-domain access restrictions, including generated preview URLs.
4. Select and test the apex-to-www mechanism.
5. Verify DNS, CAA, TLS, and HSTS sequencing across all required subdomains.
6. Record monitoring, incident, rollback, deletion, and evidence-retention ownership.
7. Confirm plan limits and costs before account or project action.
