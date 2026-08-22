---
doc_type: issue
title: Databento ICE + OPRA datasets — explicitly not subscribed (BLOCKED-CREDENTIALS, partial)
summary: >-
  Databento's CORE subscription (GLBX.MDP3, DBEQ.BASIC, XCBF.PITCH) already has a live `databento-api-key` in Secret
  Manager and is wired into production (17 backfill VMs across CME/NASDAQ/NYSE/CBOE launched
  `deployment-service@f243eb4`) — Databento is NOT a Step-4 credential-gated vendor in the general sense the original
  2026-06-21 line implied. What IS genuinely still gated: `/codex/02-data/tradfi-databento-sourcing-ssot.md`
  §"Explicitly NOT subscribed" documents that ICE feeds (`IFEU.IMPACT` Brent/Gasoil, `IFUS.IMPACT` ICE Dollar-Index +
  softs) and `OPRA` (listed options) are deliberately EXCLUDED from the current 3-dataset lockdown — querying them
  raises `DatabentoDatasetNotAllowedError` by design (the `assert_*` allowlist gate, fail-closed). This is a real,
  narrower ask than the Step-4 line's blanket framing: the fail-closed gate mechanism already exists and needs no new
  code — only an explicit subscription decision + an `ALLOWED_DATABENTO_DATASETS` allowlist addition once approved.
status: open
nature: issue
asset_group:
  [tradfi] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is squarely
  # TradFi (Databento ICE = Brent/Gasoil/softs futures; OPRA = US listed options); own tags: already include
  # `tradfi` and cite tradfi-databento-sourcing-ssot.md -- classic fork-inherited-tag trap from the cross-AG
  # coordinator data_completion_to_100_all_ag_2026_06_21.md, narrowed to single-AG but keeping the parent tag.
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer, admin]
tags: [credential-ask, databento, ice, opra, tradfi, blocked-credentials, subscription]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-08-09
last_updated: 2026-08-21
author: agent (slot-19)
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [/plans/active/data_completion_to_100_all_ag_2026_06_21.md, /codex/02-data/tradfi-databento-sourcing-ssot.md:87-117]
---

# Databento ICE + OPRA subscription ask

## What I found

Re-verifying Step 4's 2026-06-21 line ("Helius/Alchemy, Glassnode/Kaiko, Tardis, Databento, Sportradar/Odds-API") before
filing a blanket Databento ask, per the pre-task plan/issue conflict-check rule: Databento's core subscription is NOT
actually blocked — `databento-api-key` exists in Secret Manager and backs a live, already-running 17-VM backfill fleet
across CME Globex, DBEQ US Equities, and XCBF/CFE futures (the exact 3 subscribed datasets documented in
`tradfi-databento-sourcing-ssot.md` §"Subscribed datasets"). Filing a generic "Databento is credential-gated" ask would
misrepresent working infrastructure as broken.

What genuinely remains gated, per that same SSOT doc (§"Explicitly NOT subscribed", §"Consequences of the 3-dataset
choice"): **ICE feeds** (`IFEU.IMPACT` — Brent crude, Gasoil; `IFUS.IMPACT` — ICE Dollar-Index, softs: cotton/cocoa/
coffee/sugar/OJ) and **OPRA** (US listed options) are deliberately excluded from the current subscription. The code
already fails closed correctly here — every Databento call routes through `assert_*` allowlist helpers that RAISE
`DatabentoDatasetNotAllowedError` rather than risk a silent metered bill, so there is no correctness bug, only an unmet
data-coverage gap the SSOT doc itself flags as "re-adding requires an explicit ICE / OPRA subscription."

**Exact capability blocked:** Brent crude, Gasoil, ICE-listed softs (cotton/cocoa/coffee/sugar/OJ), and US listed
options (OPRA) — none of which are currently backfilled or live-captured anywhere in the pipeline. WTI crude, natural
gas, and major-currency futures remain covered via the existing CME Globex subscription (no gap there).

**Specific credential/decision needed:** this is a SUBSCRIPTION decision (billing commitment), not a missing API key —
the existing `databento-api-key` would cover ICE/OPRA too once Databento's account-level subscription is upgraded. No
new Secret Manager entry is needed; the ask is an operator billing decision + a resulting `ALLOWED_DATABENTO_DATASETS`
allowlist addition.

## Why it matters

Per the external-data-always-available HARD RULE, this is scoped correctly as a subscription ask rather than either (a)
silently treating ICE/OPRA as permanently out of scope, or (b) incorrectly implying the whole Databento integration is
broken/credential-less when it demonstrably isn't. No adapter scaffold work is needed here (unlike Glassnode/Kaiko/
Sportradar) — the allowlist + fail-closed assert mechanism the todo would otherwise ask to "scaffold" already exists and
is exactly the correct shape; it just isn't populated with ICE/OPRA dataset codes.

## Recommended decision

File a `CREDENTIAL APPROVAL REQUEST`-equivalent billing ask: does the operator want to add an ICE and/or OPRA
subscription to the existing Databento account? This is a cost decision (each is a separate paid subscription on top of
the current 3-dataset plan), not a mechanical implementation step — do not add either to `ALLOWED_DATABENTO_DATASETS`
without the operator's explicit go-ahead, since doing so would let the `assert_*` gate start ALLOWING calls that would
incur real metered billing the moment they're queried.

- [ ] [DATA] P3. DEFERRED-BY-DESIGN — per D25 ruling (OPERATOR-RULED 2026-08-21): Databento ICE/OPRA subscription
      DECLINED for now — no ICE (`IFEU.IMPACT`/`IFUS.IMPACT`) or OPRA add-ons; both stay deliberately fail-closed
      via the existing `assert_*` allowlist gate. Re-ask only on a named product need. See
      `/codex/02-data/tradfi-databento-sourcing-ssot.md` §"Consequences of the 3-dataset choice".
- [ ] [CODE] P3. Once approved: add the subscribed dataset code(s) to `ALLOWED_DATABENTO_DATASETS` in
      `unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py` (confirmed live at
      this path 2026-08-18, plan_reconciler — already named in this doc's own `context_scope`) + verify the
      corresponding `assert_*` gate now permits (rather than raises on) the newly-subscribed dataset via a real
      Databento call in a dry-run/smoke test.

## Progress Log

- 2026-08-09 (slot-19): Filed as a scoped subscription ask (ICE + OPRA only), not a blanket Databento credential ask —
  re-verified the core 3-dataset subscription is already live and working before filing, per the pre-task plan/issue
  conflict-check rule (Step 4's original framing was too broad for Databento specifically).
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:069d64e66684fa12]: **KEEP-NA,
  valid -- first audit pass.** A well-scoped, self-correcting credential/subscription ask -- the doc explicitly
  re-verified before filing that Databento's core subscription is NOT actually blocked (live `databento-api-key`, 17
  running backfill VMs), narrowing the ask to only the genuinely-excluded ICE/OPRA datasets. This is a real
  billing/subscription commitment decision (`CREDENTIAL_BLOCKED`), not a missing key -- correctly `assigned_vm: NA`.
- **context-scout 2026-08-14**: populated context_scope (1 entry).
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — reaffirmed.** Both
  todos remain a billing/subscription decision (`CREDENTIAL_BLOCKED`) plus its contingent code follow-up; only
  intervening change was plan_reconciler's 2026-08-18 citation fix to todo 2 (now names
  `unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py` directly). `assigned_vm`
  unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries) — added the tradfi-databento-sourcing-ssot codex SSOT this ask is gated on; normalized to bracket format
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Both todos remain a billing/subscription decision
  (`CREDENTIAL_BLOCKED`) plus its contingent code follow-up; no content change since the 08-18 pass. `assigned_vm`
  unchanged.

- **2026-08-21 — ruling D25 (Databento ICE/OPRA subscriptions)**: OPERATOR-RULED 2026-08-21 — DECLINED for now: no
  Databento ICE/OPRA add-ons; both stay deliberately fail-closed (dated ruling recorded on the docs). Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
