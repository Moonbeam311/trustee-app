# UPA-1B-6B-4C — UTF-8-Safe Repository Provenance Audit

Generated: 2026-06-14T13:36:25.339674
Status: **PROVENANCE_REVIEW_REQUIRED**

## Repository Summary

### `trustee-app-clean`

- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Commit count: **644**
- Merge commits: **14**
- Root commits: `['78aadbc7eec27aa9dcc46f0bbfe5135a43459056']`
- Tracked files at HEAD: **452**

### `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`

- Branch: `strapback/stable-661bb66`
- HEAD: `4a2b5882296981c96a4c8f15339799b7bbd78ff2`
- Commit count: **267**
- Merge commits: **14**
- Root commits: `['78aadbc7eec27aa9dcc46f0bbfe5135a43459056']`
- Tracked files at HEAD: **333**

### `trustee-app-private`

- Branch: `main`
- HEAD: `3d20171a529e7f9a6ae20fd616929021e6955a59`
- Commit count: **361**
- Merge commits: **14**
- Root commits: `['78aadbc7eec27aa9dcc46f0bbfe5135a43459056']`
- Tracked files at HEAD: **357**

## Pair Comparisons

### `trustee-app-clean` vs `trustee-app-private`

- Shared commits: **360**
- Left-only commits: **284**
- Right-only commits: **1**
- Same root commit: **True**
- Merge base: `None`
- Relationship: **DIVERGED_FROM_SHARED_HISTORY**
- Shared tracked files: **356**
- Left-only tracked files: **96**
- Right-only tracked files: **1**

### `trustee-app-clean` vs `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`

- Shared commits: **267**
- Left-only commits: **377**
- Right-only commits: **0**
- Same root commit: **True**
- Merge base: `4a2b5882296981c96a4c8f15339799b7bbd78ff2`
- Relationship: **trustee-app-clean_ALIGNED_PHASE8E_20260429_072701 HEAD is an ancestor of trustee-app-clean HEAD**
- Shared tracked files: **333**
- Left-only tracked files: **119**
- Right-only tracked files: **0**

### `trustee-app-private` vs `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`

- Shared commits: **266**
- Left-only commits: **95**
- Right-only commits: **1**
- Same root commit: **True**
- Merge base: `4a2b5882296981c96a4c8f15339799b7bbd78ff2`
- Relationship: **trustee-app-clean_ALIGNED_PHASE8E_20260429_072701 HEAD is an ancestor of trustee-app-private HEAD**
- Shared tracked files: **333**
- Left-only tracked files: **24**
- Right-only tracked files: **0**

## Findings

- trustee-app-clean: 644 commits, 14 merge commits, 452 tracked files at HEAD.
- trustee-app-clean_ALIGNED_PHASE8E_20260429_072701: 267 commits, 14 merge commits, 333 tracked files at HEAD.
- trustee-app-private: 361 commits, 14 merge commits, 357 tracked files at HEAD.
- trustee-app-clean and trustee-app-private share 360 commits.
- trustee-app-clean and trustee-app-clean_ALIGNED_PHASE8E_20260429_072701 share 267 commits.
- trustee-app-private and trustee-app-clean_ALIGNED_PHASE8E_20260429_072701 share 266 commits.

## Warnings

- The aligned repository still has extensive working-tree deletions. Only its committed HEAD state is safe for provenance comparison.
