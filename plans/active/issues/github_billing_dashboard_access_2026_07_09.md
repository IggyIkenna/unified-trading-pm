---
doc_type: issue
title: Enable GitHub billing on the Cost Observability dashboard — operator token ask (fine-grained PAT, Plan:read)
summary: >-
  The /ops/costs GitHub panel is a hardcoded placeholder because GitHub billing on the personal IggyIkenna account is
  owner-only and no credential we hold can read it (fleet GH_PAT + uts-ci-poller App both lack billing scope — verified
  403 "Resource not accessible by personal access token" in the June Actions billing incident). Operator (Ikenna) mints
  a fine-grained PAT with Account "Plan: Read" (owned by IggyIkenna), handed over / stored as a new Secret Manager
  secret; then a small deployment-api change swaps the dummy github_facts provider to the enhanced-billing
  /users/{owner}/settings/billing/usage endpoint (itemised per-day / per-product / per-repo, gross/discount/net —
  matches the GCP/AWS shape the page already renders). Recommend a dedicated token, NOT extending GH_PAT.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags: [billing, cost, observability, github, credentials, deployment-ui, operator-ask]
related: [cost_observability_ui_2026_07_08.md, github_actions_billing_wall_2026_06_11.md]
created: 2026-07-09
priority: P2
parent_epic: deployment_and_user_management_master
execution_scope: local-only
drift_direction: advance-code
source:
  - "operator ask 2026-07-09 (Harsh): create a doc for Ikenna to enable GitHub billing on /ops/costs"
  - "github_actions_billing_wall_2026_06_11.md — P3 telemetry todo, blocked-on-decision awaiting a Plan:read PAT"
assigned_vm: NA
resolved_by:
locked_by:
---

# Action needed: enable GitHub billing on the Cost dashboard

**To:** Ikenna (owner of the `IggyIkenna` GitHub account) **From:** Harsh **Date:** 2026-07-09 **Time to complete:** ~5
minutes **What we need from you:** mint **one** read-only GitHub token and hand it over. That's the whole ask — no org
setup, no repo permissions, no code from you. We wire up the rest.

---

## TL;DR

The Cost Observability dashboard (`/ops/costs`) already shows **real** GCP and AWS spend. The **GitHub** panel is still
a hardcoded placeholder ("Dummy data") because **GitHub billing can only be read by a token that _you_, the account
owner, create** — nothing we already hold can read it. Mint a fine-grained PAT with a single permission (**Account →
"Plan" → Read**) and give it to us. Once it lands, GitHub spend shows up alongside GCP/AWS at full detail.

---

## Why it's blocked (context)

- All our repos live under a **personal account** (`github.com/IggyIkenna/…`), not a GitHub org. GitHub treats billing
  on a personal account as **owner-only** — only _your_ account can read it.
- The credentials we currently have — the shared fleet PAT (`GH_PAT` / `github-token` in Secret Manager) and the
  `uts-ci-poller` GitHub App — deliberately have **no billing access**. We verified this live during the June Actions
  billing incident: `GET /users/IggyIkenna/settings/billing/actions` returned **403 "Resource not accessible by personal
  access token."**
- That's also why, during that incident, every dollar figure in the post-mortem was an _estimate_ (minutes × $0.008)
  instead of ledger-true — we had no way to read the real billing ledger. **This token fixes that permanently, too.**
  (See [`github_actions_billing_wall_2026_06_11.md`](github_actions_billing_wall_2026_06_11.md), P3 telemetry todo,
  which was blocked-on-decision awaiting exactly this token.)

## What you get once it's in

GitHub's newer billing API (`/settings/billing/usage`, GA for personal accounts since Feb 2025) returns **itemized**
data that maps exactly onto what the dashboard already renders for GCP/AWS:

- **Per day**, **per product** (Actions / Packages / Storage / Copilot), and **per repository**
- Real dollars with **gross / discount / net** — no more estimating from minutes
- Early warning on runaway Actions spend (the thing that caused the June CI outage), caught in hours instead of at the
  billing wall

---

## What to do (≈5 min)

### Step 1 — Mint a fine-grained token

1. Go to **https://github.com/settings/personal-access-tokens/new** (Settings → Developer settings → Fine-grained tokens
   → _Generate new token_).
2. **Token name:** `uts-cost-dashboard-billing` (or anything memorable).
3. **Resource owner:** your personal account — **IggyIkenna**.
4. **Expiration:** your call — 1 year with a calendar reminder to rotate is fine (or per your policy). Avoid "no
   expiration."
5. **Repository access:** leave at **"Public Repositories (read-only)"** or "No repositories" — billing is
   account-level, it needs **zero** repo access.
6. **Permissions → Account permissions:** find **"Plan"** and set it to **Read-only**. This is the _only_ permission
   required. Leave everything else "No access."
7. Generate, and **copy the token** (`github_pat_…`) — GitHub shows it only once.

### Step 2 — Hand it over securely

Pick whichever is easier:

- **Easiest:** send the token to **Harsh** over a secure channel (1Password / a secret note — **not** plaintext Slack or
  email), and Harsh stores it in Google Secret Manager.
- **Or store it yourself** in GCP project `central-element-323112`:
  ```bash
  printf %s "github_pat_YOUR_TOKEN_HERE" | \
    gcloud secrets create github-billing-token \
      --project=central-element-323112 --replication-policy=automatic --data-file=-
  ```
  (Harsh will grant the deployment-api service account read access — the same identity that already reads the
  `github-token` secret.)

**That's it.** No org role, no repo scopes, no further action.

---

## Why a _new_ token instead of adding this to our existing `GH_PAT`?

Fair question — our `GH_PAT` is already a fine-grained token, so we _could_ just add "Plan: Read" to it. We're
recommending a separate token on purpose:

- **Blast radius.** `GH_PAT` is our most widely-copied credential — it has repo + workflow + PR write across all ~25
  repos and is written to disk on every dev slot, worktree, and VM for CI. Adding _financial_ read to it would let all
  those places read our spend. Billing stays on a token with a tiny footprint (one secret, read by one backend service).
- **Independent rotation.** `GH_PAT` gets rotated/revoked during CI incidents; billing shouldn't break when that
  happens, and vice-versa.
- **Least privilege.** The billing read needs **no** repo access at all, so bundling it with a write-capable fleet token
  would be over-provisioned in both directions.

Net: one dedicated, read-only, minimal token is the safe and clean choice.

---

## Security summary (for peace of mind)

- **Read-only, financial-only.** The token can read your billing usage and **nothing else** — no code, no repo writes,
  no ability to change anything.
- **Stored in Secret Manager**, access limited to the deployment-api service identity; never in the frontend, never in
  git.
- **Consumed by one backend endpoint** (the cost dashboard), cached daily.

## References (for verification)

- Billing usage endpoint: https://docs.github.com/en/rest/billing/usage — `GET /users/{username}/settings/billing/usage`
- Required permission ("Plan" read):
  https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens
- Enhanced billing GA for personal accounts (2025-02-25):
  https://github.blog/changelog/2025-02-25-enhanced-billing-platform-is-now-available-for-personal-accounts/

---

## Resolution checklist

- [ ] [OPERATOR] P2. Ikenna mints the fine-grained PAT (Account → "Plan" → Read, resource owner `IggyIkenna`) and hands
      it over.
- [ ] [INFRA] P2. Token stored in Secret Manager as `github-billing-token` (project `central-element-323112`) +
      deployment-api SA granted `secretmanager.secretAccessor`.
- [ ] [BACKEND] P2. `deployment-api` `github_facts()` swapped from the dummy provider to
      `GET /users/IggyIkenna/settings/billing/usage`; map line items → `CostRecord` (day/product/repo, net→cost,
      gross→gross, discount→credit); drop `is_placeholder=True`.
- [ ] [UI] P2. Remove the "Dummy data" panel note + "pending PAT" source-footer once real data flows.

---

**Once you've handed over the token, ping Harsh — wiring it into the dashboard is a small backend change on our side and
the GitHub panel goes live with real numbers.**
