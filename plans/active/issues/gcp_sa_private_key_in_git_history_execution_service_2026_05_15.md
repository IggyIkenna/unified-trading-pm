---
title: GCP service account private key in git history — 5 repos (execution-service, instruments-service, MTDS, UTL, strategy-service)
created: 2026-05-15
author: slot-6 (Ikenna) — discovered via Phase 0.A gitleaks scan
source:
  - api_keys_wallets_accounts_readiness_2026_05_10.md Phase 0.A gitleaks scan
  - execution-service, instruments-service, market-tick-data-service, unified-trading-library, strategy-service git history scans
locked_by: live-defi-rollout
locked_since: 2026-05-15
severity: P0 — ROTATE KEY IMMEDIATELY
---

## What I found

Running gitleaks on all repo git histories (Phase 0.A of api_keys plan), the same GCP SA private key file
`central-element-323112-e35fb0ddafe2.json` was found in **5 repos**:

| Repo | Commits with file | Example commit |
|------|-------------------|----------------|
| execution-service | 2 | `2804351950a8` (2026-01-22, "chore: add GCP service account credentials") |
| instruments-service | 9 | `71eb58b07a5a` |
| market-tick-data-service | 3 | `ae9ebcbcf136` |
| unified-trading-library | 2 | (see gitleaks-utl.json) |
| strategy-service | 1 | `2c4af3d777c2` |

The file `central-element-323112-e35fb0ddafe2.json` is a GCP service account key JSON for project
`central-element-323112` (prod). It was removed from working trees (added to `.gitignore`) but the
private key remains accessible in git history across all 4 repos via:

```bash
git show 2804351950a8:central-element-323112-e35fb0ddafe2.json  # execution-service
git show 71eb58b07a5a:central-element-323112-e35fb0ddafe2.json  # instruments-service
git show ae9ebcbcf136:central-element-323112-e35fb0ddafe2.json  # mtds
```

The file is **NOT** present in `HEAD` or `origin/live-defi-rollout` in any repo.

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

### 3. Git history rewrite — all 5 repos (ETA: ≤5h total, requires force-push authorization)

After revoking the key, rewrite history in **all 5 affected repos** to remove the file permanently.
Run sequentially — one repo at a time to control re-clone notifications.

```bash
# Install git-filter-repo if not present
pip install git-filter-repo

TARGET_FILE="central-element-323112-e35fb0ddafe2.json"

# Repeat for each repo: execution-service, instruments-service, market-tick-data-service, unified-trading-library, strategy-service
for REPO_PATH in \
  /path/to/execution-service \
  /path/to/instruments-service \
  /path/to/market-tick-data-service \
  /path/to/unified-trading-library \
  /path/to/strategy-service; do
  echo "=== Rewriting $REPO_PATH ==="
  cd "$REPO_PATH"
  git filter-repo --path "$TARGET_FILE" --invert-paths --force
  git push origin --all --force
  git push origin --tags --force
done
```

⚠️ **This rewrites all commit SHAs in each repo** — all collaborators and agent tab worktrees MUST
re-clone all 4 repos after the rewrite. Notify Harsh and all agents (Slots 1-8).

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
- [ ] Git history rewritten (execution-service) + force-pushed
- [ ] Git history rewritten (instruments-service) + force-pushed
- [ ] Git history rewritten (market-tick-data-service) + force-pushed
- [ ] Git history rewritten (unified-trading-library) + force-pushed
- [ ] Git history rewritten (strategy-service) + force-pushed
- [ ] Collaborators + all agent tab worktrees notified to re-clone all 5 repos
- [ ] `credential-probe.sh` re-runs clean
- [ ] New SA key generated + added to Secret Manager (if needed)
- [ ] Gitleaks confirm-clean scan on rewritten history (all 4 repos)

## Note on false positives in same scans

Per-repo false positive summaries:

**execution-service** (2 commits, 1 real finding):
- `generic-api-key` in `.env` (gitignored + untracked): false positive
- `generic-api-key` in `capture_golden_swaps.py`: Ethereum event topic hash, not a key
- `generic-api-key` in `kelpdao.py`/`rocket_pool.py`/`renzo.py`: Ethereum contract addresses

**instruments-service** (9 commits, 1 real finding — see also GitHub PAT issue):
- 83 `generic-api-key`: false positives (venue API keys in .env files, gitignored)
- 7 `github-pat`: **see P1 issue** `github_pat_in_instruments_service_env_2026_05_15.md`
- 3 `curl-auth-header` in `scripts/CLICKUP_GUIDE.md`: documentation example token

**market-tick-data-service** (3 commits, 1 real finding):
- 129 `generic-api-key`: false positives

**unified-trading-library** (2 commits, 1 real finding):
- 81 `generic-api-key`: false positives
- 2 `curl-auth-header` in `instruments-service/scripts/CLICKUP_GUIDE.md`: documentation example

Only the SA JSON private key finding (and instruments-service GitHub PAT — separate issue) require action.
