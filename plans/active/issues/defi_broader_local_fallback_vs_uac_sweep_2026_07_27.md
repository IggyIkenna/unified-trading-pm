---
doc_type: issue
title:
  Broader sweep needed for local dicts that duplicate/shadow UAC Category-A data (token decimals, chain genesis, factory
  addresses) beyond the one concretely-fixed LENDING_PROTOCOL_DEPLOY_DATES precedent
summary: >-
  Working defi_onchain_derivable_values_and_date_drift_2026_06_20.md's P1 "Latent Bug-class-3 local fallback drift
  sweep" todo, traced the concrete precedent (case-2: UAC PROTOCOL_LAUNCH_DATES vs instruments-service's
  LENDING_PROTOCOL_DEPLOY_DATES) and fixed it fully — every entry except aave_v3/GNOSIS was dead/stale duplicate data
  now removed (instruments-service@<sha>, see plan flip). The todo's own wording was broader than that one dict though:
  "Sweep for ANY local fallback that overrides a UAC value without an explicit comment." A systematic search for other
  local dicts shadowing UAC's other Category-A domains (token decimals, chain genesis dates, factory addresses — not
  just protocol launch dates) across every DeFi-touching repo is a genuinely separate, larger audit that this dispatched
  todo did not have budget/scope for. Filing it as its own properly-scoped follow-up so it isn't lost.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service, features-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, uac, data-correctness, ssot-drift, local-fallback, audit-scope]
related:
  [
    /plans/archive/2026_07/defi_onchain_derivable_values_and_date_drift_2026_06_20.md,
    /plans/archive/issues/defi_fork1_prep_audit_2026_05_08.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
parent_epic: defi_master
priority: P3
source:
  [
    "defi_onchain_derivable_values_and_date_drift_2026_06_20.md P1 todo (Latent Bug-class-3 local fallback drift sweep),
    dispatched task defi_onchain_derivable_values_and_date_drift-002, slot-6 2026-07-27",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# Broader local-fallback-vs-UAC sweep (beyond the LENDING_PROTOCOL_DEPLOY_DATES precedent)

## What I found

`defi_onchain_derivable_values_and_date_drift_2026_06_20.md`'s P1 todo named ONE concrete precedent ("case-2": UAC
`PROTOCOL_LAUNCH_DATES` vs the instruments-service `LENDING_PROTOCOL_DEPLOY_DATES` local fallback dict in
`instruments_service/reference_data/utils/evm_creation_resolver.py`). I traced that precedent fully via
`plans/archive/issues/defi_fork1_prep_audit_2026_05_08.md` §"Bug class 3 — launch-date floor handling" and fixed it
completely:

- Every `LENDING_PROTOCOL_DEPLOY_DATES` entry except `aave_v3`/`GNOSIS` is now ALSO present in UAC
  `PROTOCOL_LAUNCH_DATES` (verified pair-by-pair against `unified_api_contracts/registry/chain_env.py`), meaning
  `get_protocol_floor_date()`'s UAC-first cascade never reaches them — pure dead weight in the local dict.
- Several were silently STALE relative to UAC's corrected values (e.g. `spark`/`ETHEREUM` still carried the exact
  pre-2026-05-08 `2023-05-09` over-clip value the original audit flagged as a bug — never actually fixed in the local
  dict even though UAC's own entry landed with the correct `2023-03-07`).
- `compound_v3`/`POLYGON` was worse than stale — UAC's own comment confirms Compound V3 isn't even deployed on Polygon
  (subgraph returns 0 markets), so that local entry was pure fiction.
- Trimmed the dict to the one genuine remaining fallback (`aave_v3`/`GNOSIS`, the sole pair UAC doesn't track), added a
  shape-lock regression test (`test_no_dead_redundant_local_entries`) that fails if a future local entry duplicates a
  UAC-tracked pair, plus explicit resolve-via-UAC regression tests for every formerly-local-only protocol.

**What's NOT covered by that fix**: the todo's own wording is broader — "Sweep for ANY local fallback that overrides a
UAC value without an explicit comment." The 3-category model this plan operates under (Category A = immutable historical
facts) spans FOUR distinct kinds of UAC data, not just launch dates:

1. Protocol launch dates (`PROTOCOL_LAUNCH_DATES`) — **covered by this fix**.
2. Token decimals (`TOKEN_DECIMALS`).
3. Chain genesis dates (`CHAIN_GENESIS_DATES`).
4. Factory addresses (Uniswap, SushiSwap, PancakeSwap, Curve, Aave, Compound, etc.).

The Cat-A audit (`Phase 2` of the parent plan, `unified-api-contracts@37926cb`,
`unified-api-contracts/audits/defi_cat_a_audit_2026_05_08_report.md`) probed UAC's OWN declared values against on-chain
sources for drift — it did NOT search for OTHER repos maintaining their own competing local copies of these values the
way `LENDING_PROTOCOL_DEPLOY_DATES` did for launch dates. A quick grep during this task turned up ~80 files across
`instruments-service` and `market-tick-data-service` containing `LAUNCH_DATE`/`DEPLOY_DATE`/ `_GENESIS_DATES`-shaped
strings, but the overwhelming majority are function parameters, docstring references, or per-adapter comments — not
actual duplicate SSOT dicts. Distinguishing genuine local-fallback-dict drift from that noise needs a real per-file
read, which is out of scope for the dispatched todo (a scoped, checkable fix) and belongs in its own audit-shaped task.

## Why it matters

The `LENDING_PROTOCOL_DEPLOY_DATES` precedent proves the failure mode is real and has already caused production impact
once (the Spark 63-day over-clip, the AAVE V3 11-month mis-clip before the 2026-05-08 fix). The SAME class of bug — a
local dict silently shadowing/duplicating a UAC value, drifting stale because nobody re-syncs it when UAC's entry is
corrected — could exist for token decimals, chain genesis, or factory addresses in any of the DeFi-touching repos. Not
urgent (no known active drift found yet, unlike the launch-dates case), but worth a real audit pass.

## Recommended decision

- [ ] [SCRIPT] P3. **data_engineering** — grep every DeFi-touching repo (instruments-service, market-tick-data-service,
      features-service, market-data-processing-service) for local dict/constant declarations whose KEYS look like
      `(chain, protocol)` or `(chain, token)` pairs and whose VALUES are decimals, dates, or hex addresses — i.e.
      candidate shadow-copies of UAC `TOKEN_DECIMALS` / `CHAIN_GENESIS_DATES` / the various factory-address registries.
      For each candidate, read the consuming code to determine: (a) is UAC actually consulted first (a real cascade,
      like `get_protocol_floor_date`'s pattern), or does the local value win outright (a real override, not just a
      fallback)? (b) does the local value currently MATCH UAC, or has it drifted? Mirror the
      `LENDING_PROTOCOL_DEPLOY_DATES` fix pattern for anything found: remove dead-code entries UAC now covers, keep +
      comment-justify genuinely-still-needed ones, add a shape-lock regression test per dict fixed.
- [ ] [DATA] P3. **operator** — after the P0 script above lands, re-run the parent plan's
      `derive_protocol_launch_dates.py`-style drift check (or a token-decimals/chain-genesis equivalent if one doesn't
      exist yet) against any newly-found local dict to confirm no ACTIVE production drift is currently hiding behind a
      shadow copy the way Spark/AAVE V3 were.
