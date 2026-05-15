---
title: GitHub PAT committed in instruments-service .env and .env.example (multiple commits)
created: 2026-05-15
author: slot-6 (Ikenna) — discovered via Phase 0.A gitleaks scan
source:
  - api_keys_wallets_accounts_readiness_2026_05_10.md Phase 0.A gitleaks scan
  - instruments-service git history scan (/tmp/gitleaks-instruments.json)
locked_by: live-defi-rollout
locked_since: 2026-05-15
severity: P1 — revoke PAT; lower priority than GCP SA key (P0)
---

## What I found

Gitleaks scan of `instruments-service` git history found a real GitHub Personal Access Token committed across multiple
files and commits:

```
RuleID: github-pat
Token: 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 (7 chars shown — full token in git history)
```

Affected files and commits:

| File           | Commits                                        |
| -------------- | ---------------------------------------------- |
| `.env.example` | `a2121e4f2bc1`, `f2d904a43a57`, `42e589c71147` |
| `.env copy`    | `a2121e4f2bc1`, `f2d904a43a57`, `42e589c71147` |
| `.env`         | `42e589c71147`                                 |

The `.env.example` file (normally committed as template with placeholder values) contained a real PAT value starting
with `ghp_`. The `.env` file (gitignored in current HEAD) was also committed in commit `42e589c71147` with the same real
PAT.

Verified via:

```bash
git -C instruments-service show a2121e4f2bc1:.env.example | grep "^GH_PAT="
# Output: GH_PAT=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
```

## Why it matters

**Severity: P1 SECURITY** — a GitHub PAT is accessible to anyone with read access to the `instruments-service`
repository's git history.

GitHub PATs grant API access to the GitHub account that created them. Depending on the token's scope:

- **repo** scope: read/write access to all private repos in the account
- **packages:read** scope: download private GitHub packages (used in this workspace for `unified-trading-library`)
- **workflow** scope: trigger GitHub Actions workflows

If the token owner account is the `IggyIkenna` GitHub account (likely, given this is workspace code), this could grant
unauthorized access to all private repos across the unified trading system.

**Lower priority than the GCP SA key (P0)** because GitHub PATs can be quickly listed + revoked in GitHub UI, and GitHub
sends automatic expiry notifications. The GCP SA key has no automatic expiry.

## Required actions (operator)

### 1. Revoke the GitHub PAT (ETA: ≤15 min)

1. Go to `https://github.com/settings/tokens` (GitHub account that owns instruments-service)
2. Find the token `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` (or filter by name if labeled)
3. Click **Delete** / **Revoke**

GitHub also provides a `gh` CLI path:

```bash
# List tokens (requires OAuth, cannot revoke by name via CLI — use UI)
gh auth status
```

### 2. Check if token is already expired

GitHub classic PATs expire after the duration set at creation (30/60/90/no-expiry). If the token was created in 2026-01,
it may already be expired. Confirm in GitHub UI under Settings → Developer settings → Personal access tokens → Tokens
(classic).

### 3. Audit access logs (if token is/was active)

In GitHub organization audit log (`https://github.com/organizations/IggyIkenna/settings/audit-log`), filter by the token
to check if it was used by unauthorized parties.

### 4. Git history rewrite — instruments-service

After revoking, remove from git history (can be batched with the GCP SA key rewrite per P0 issue):

```bash
pip install git-filter-repo
cd instruments-service

# Remove .env.example PAT line (harder — file still needed as template)
# Option A: git filter-repo to replace PAT value with placeholder
git filter-repo --replace-text <(echo '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==>GH_PAT_PLACEHOLDER') --force

# Option B: remove .env copy entirely (it should never have been committed)
git filter-repo --path ".env copy" --invert-paths --force

git push origin --all --force
git push origin --tags --force
```

### 5. Fix .env.example going forward

After the rewrite, update `.env.example` to use a placeholder value:

```
GH_PAT=ghp_YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE
```

## Resolution tracking

- [ ] GitHub PAT revoked in GitHub UI
- [ ] Confirmed token is expired or never had broad scope
- [ ] GitHub organization audit log checked for unauthorized use
- [ ] Git history rewritten (instruments-service) — coordinate with P0 GCP SA key rewrite
- [ ] `.env.example` updated with placeholder value (not real token)
- [ ] Collaborators notified to re-clone instruments-service (if history rewritten separately from P0)

---

## RESOLUTION UPDATE 2026-05-15 ~03:30 UTC (ikenna-main)

**Revocation status: ALREADY DONE** — the leaked PAT returns HTTP 401 on auth:

```
$ curl -s -o /dev/null -w "HTTP %{http_code}" -H "Authorization: token ghp_QJOtg6NX..." \
    https://api.github.com/user
HTTP 401
```

The token is dead. The leaked credential in git history is invalid + grants no access. Security incident resolved on the
credential side.

**Remaining work — BFG history scrub** demoted to P3-hygiene per same rationale as the GCP SA key issue. Both will be
batched into the same maintenance-window scrub successor task.
