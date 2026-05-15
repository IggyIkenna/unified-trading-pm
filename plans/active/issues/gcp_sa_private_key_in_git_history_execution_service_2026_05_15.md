---
title: GCP service account private key committed to execution-service git history (commit 280435195)
created: 2026-05-15
author: slot-6 (Ikenna) — discovered via Phase 0.A gitleaks scan
source:
  - api_keys_wallets_accounts_readiness_2026_05_10.md Phase 0.A gitleaks scan
  - execution-service git log (all-branch scan)
locked_by: live-defi-rollout
locked_since: 2026-05-15
severity: P0 — ROTATE KEY IMMEDIATELY
---

## What I found

Running gitleaks on `execution-service` git history (Phase 0.A of api_keys plan):

```
File: central-element-323112-e35fb0ddafe2.json
RuleID: private-key
Commits: 26150e45b3ec + 2804351950a8
Commit message: "chore: add GCP service account credentials and update gitignore" (2026-01-22)
```

The file `central-element-323112-e35fb0ddafe2.json` (GCP service account key JSON for project
`central-element-323112`) was committed to `execution-service` repo in commit `2804351950a8`
(2026-01-22 17:52 UTC). The key was subsequently removed from the working tree (added to `.gitignore` in
commit `40c2d9e8c`) but the private key remains accessible in git history via:

```bash
git show 2804351950a8:central-element-323112-e35fb0ddafe2.json
```

The file is **NOT** present in `HEAD` or `origin/live-defi-rollout`.

## Why it matters

**Severity: P0 SECURITY** — a GCP service account private key for `central-element-323112` (prod GCP project)
is accessible to anyone with read access to the `execution-service` repository's full git history.

The key format is a RSA private key inside a GCP SA JSON credential file. If this SA has IAM bindings with any
permissions (storage, compute, secrets, KMS), those permissions are exploitable via the leaked key.

**This is NOT resolved by removing the file from HEAD** — the key exists permanently in git history until history
is rewritten.

## Required actions (operator)

### 1. Immediate — revoke the SA key (ETA: ≤1h)

In GCP Console → IAM & Admin → Service Accounts → filter by `e35fb0ddafe2`:

```bash
# Find the key ID
gcloud iam service-accounts keys list \
  --iam-account=central-element-323112@central-element-323112.iam.gserviceaccount.com \
  --project=central-element-323112

# Revoke the compromised key (substitute KEY_ID from above)
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=central-element-323112@central-element-323112.iam.gserviceaccount.com \
  --project=central-element-323112
```

If the SA name differs (the file `central-element-323112-e35fb0ddafe2.json` suggests project `central-element-323112`,
key ID `e35fb0ddafe2`), find the correct SA via:

```bash
gcloud iam service-accounts list --project=central-element-323112 | grep e35fb0ddafe2
```

### 2. Audit SA permissions

Before revoking, check what this SA has access to — determine blast radius:

```bash
# List all IAM policies this SA is a member of
gcloud projects get-iam-policy central-element-323112 \
  --flatten="bindings[].members" \
  --filter="bindings.members:*e35fb0ddafe2*" \
  --format="table(bindings.role)"
```

### 3. Git history rewrite (ETA: ≤2h, requires force-push authorization)

After revoking the key, rewrite the repo history to remove the file permanently:

```bash
# Install git-filter-repo if not present
pip install git-filter-repo

# Rewrite history (removes the file from ALL commits)
git filter-repo --path central-element-323112-e35fb0ddafe2.json --invert-paths --force

# Force-push all branches
git push origin --all --force
git push origin --tags --force
```

⚠️ **This rewrites all commit SHAs** — all collaborators MUST re-clone. Notify Harsh and all agents.

⚠️ **This is in the HARD STOP list** ("force-push to main") — operator-only action per CLAUDE.md.

### 4. GitHub history (if public or any collaborator has cloned)

If the repo is public or any CI/external system has cloned it, request GitHub support to purge the cached history:
https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

### 5. Post-rotation verification

Run `credential-probe.sh --mode live` after revoking + replacing SA key to verify all downstream systems
still function (any service that loaded the old key at startup may need restart).

## Resolution tracking

- [ ] SA key revoked in GCP Console
- [ ] SA permissions audited (blast-radius determined)
- [ ] Git history rewritten (`git filter-repo`) + force-pushed
- [ ] Collaborators notified to re-clone
- [ ] `credential-probe.sh` re-runs clean
- [ ] New SA key generated + added to Secret Manager (if needed)
- [ ] Gitleaks confirm-clean scan on rewritten history

## Note on false positives in same scan

The other 110 gitleaks findings are false positives:
- 108 `generic-api-key` in `.env` (gitignored + untracked — contains real venue keys but properly excluded)
- 1 `generic-api-key` in `capture_golden_swaps.py` — Ethereum event topic hash
  (`_SWAP_TOPIC_CURVE_TOKEN_EXCHANGE`), not an API key
- 3 `generic-api-key` in `kelpdao.py`/`rocket_pool.py`/`renzo.py` — Ethereum contract addresses in docstrings

Only the SA JSON private key finding requires action.
