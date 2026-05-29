---
title: "UI repos missing branch protection on main + staging"
created: 2026-05-29
source:
  - "ci_canonical_v2_migration_2026_05_29.md Phase 5 verification"
priority: P2
status: active
---

## What I found

During quality-gates-v2 migration verification, 5 repos were found with no branch protection on main or staging:

- unified-trading-system-ui
- user-management-ui
- features-service
- batch-live-reconciliation-service
- unified-trading-api

These repos accept direct pushes to main with no required CI check. The quality-gates-v2 workflow IS deployed on their
LDR branches but will never be required until branch protection is configured.

## Why it matters

Without branch protection, any push goes straight to main. The sentinel + quickmerge enforcement is the only gate, but
there's no server-side backstop.

## Recommended action

For each repo:

1. Enable quality-gates-v2 as required status check on main + staging
2. Set enforce_admins=false (for now — enable after all repos green per ci_canonical plan Phase 5)
3. Set dismiss_stale_reviews=true, required_approving_review_count=1

Command:

```bash
for repo in unified-trading-system-ui user-management-ui features-service batch-live-reconciliation-service unified-trading-api; do
  gh api repos/IggyIkenna/$repo/branches/main/protection -X PUT \
    --field required_status_checks[strict]=false \
    --field "required_status_checks[checks][][context]=quality-gates-v2" \
    --field enforce_admins=false \
    --field "required_pull_request_reviews[dismiss_stale_reviews]=true" \
    --field "required_pull_request_reviews[required_approving_review_count]=1" \
    --field restrictions=null 2>&1 && echo "$repo main: done" || echo "$repo main: failed (may not exist)"
done
```

Bootstrap the v2 workflow file onto main for each repo before enabling (same admin-merge recipe as UAC/UTL).

## Status

- [ ] [SCRIPT] P2. Bootstrap quality-gates-v2.yml onto main for each of the 5 repos
- [ ] [SCRIPT] P2. Enable branch protection on main + staging for each repo
- [ ] [VERIFY] P2. Confirm quality-gates-v2 fires cleanly on each repo
