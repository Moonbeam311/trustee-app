# UPA-1B-6B-4B — Active Runtime and Database Identity Verification

Generated: 2026-06-14T12:06:54.264774
Status: **RUNTIME_IDENTITY_REVIEW_REQUIRED**

## Findings

- The declared Firm 2 application folder exists.
- The private application contains 1 populated database candidate(s).

## Warnings

- The private application's populated records are labeled FIRM-001. This may be a legacy internal label rather than proof that the folder is Firm 1.
- Clean and private applications are on different Git commits.
- The aligned snapshot differs from the clean application's Git commit.

## Blockers

- None.

## Application Runtime References

### `trustee-app-clean`

- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Environment files: `['.env.example']`
- Databases: **5**
- Runtime references: **268**
- Likely database matches: **129**

### `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`

- Branch: `strapback/stable-661bb66`
- HEAD: `4a2b5882296981c96a4c8f15339799b7bbd78ff2`
- Environment files: `['.env.example']`
- Databases: **0**
- Runtime references: **7**
- Likely database matches: **0**

### `trustee-app-private`

- Branch: `main`
- HEAD: `3d20171a529e7f9a6ae20fd616929021e6955a59`
- Environment files: `['.env.example']`
- Databases: **2**
- Runtime references: **44**
- Likely database matches: **8**

