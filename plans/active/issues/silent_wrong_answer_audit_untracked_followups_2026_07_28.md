---
doc_type: issue
title: >-
  2 findings from silent_wrong_answer_audit_candidates_2026_07_20.md never got their own tracked todo — filed here so
  archiving the parent audit doc doesn't bury them
summary: >-
  While closing silent_wrong_answer_audit_candidates_2026_07_20.md's one remaining todo (the 2 stashed features-service
  fixes — both resolved, see that doc's Progress Log), found its "Recommended handling" section named 2 more
  genuinely-open findings only as prose, never as a tracked `- [ ]` todo anywhere: (1) P0 finding 2 — strategy-service's
  `pnl_input_builder.py` reads a `gas_fees/chain_id=…/` prefix that exists in no bucket, hardcoding every DeFi fill's
  gas cost to 1 gwei; MTDS's real gas-fee data DOES exist (confirmed via
  `defi_gas_fees_historical_venue_path_migration_2026_07_28.md`, under `venue=ALCHEMY`/`chain=<X>` — not `chain_id=`),
  so this is a reader-path fix, not a "does the data exist" question anymore, but no strategy-service doc tracks fixing
  the READER. (2) P1 finding 9 — e2e-testing's `validate_shards_4pillar.py` pillar-2/3 (schema/NaN) checks are vacuous
  for 51 of 61 (asset_group, data_type) pairs; the audit doc explicitly said it "needs a schema-contract decision" and
  left it for a follow-up that was never filed.
status: open
nature: issue
asset_group: [defi, cross-cutting]
stage: [strategy, data]
repos: [strategy-service, e2e-testing]
scope: [engineer, admin]
tags: [silent-failure, gas-fees, pnl-correctness, 4-pillar, schema-contract, follow-up]
related:
  [
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend
drift_direction: neutral
depends_on: []
source: >-
  Surfaced 2026-07-28 while closing silent_wrong_answer_audit_candidates_2026_07_20.md's stashed-fixes todo (the audit
  doc's own "Recommended handling" #2/#4 prose, never converted to todos).
resolved_by:
locked_by:
locked_since:
---

# Silent-wrong-answer audit — 2 untracked follow-ups

## Todos

- [ ] [BACKEND] P0. **strategy-service** — fix `pnl_input_builder.py`'s `_load_gas_fee_data`
      (`_get_gas_price_at_timestamp` caller) to read MTDS's REAL gas-fee path
      (`venue=ALCHEMY`/`chain=<CHAIN>`/`data_type=gas_fees`, per
      `defi_gas_fees_historical_venue_path_migration_2026_07_28.md`'s confirmed shape — NOT the non-existent
      `gas_fees/chain_id=…/` this reader currently probes). `gas_cost_usd` is a real cash outflow subtracted in
      `compute_pnl_breakdown`; every DeFi fill's gas cost is currently hardcoded to 1 gwei, systematically overstating
      realised PnL. Note both pre-fix (`venue=<CHAINNAME>`) and post-fix (`venue=ALCHEMY`, 2026-07-22 commit
      `market-tick-data-service@522185a6`) historical shapes may need dual-read until the path-migration doc resolves.
      Source: silent_wrong_answer_audit_candidates_2026_07_20.md P0 finding 2.
- [ ] [BACKEND] P2. **e2e-testing** — resolve the schema-contract decision `validate_shards_4pillar.py`'s pillar-2 (NaN)
      / pillar-3 (schema) checks need: they are vacuous (degrade to `row_count > 0`) for 51 of 61
      `(asset_group, data_type)` pairs because no per-pair schema/NaN-tolerance contract exists to check against. This
      is the harness MTDS quality-gates STEP 5.88 runs and the batch+live matrix delegates its batch verdict to, so the
      gap is load-bearing, not cosmetic. Source: silent_wrong_answer_audit_candidates_2026_07_20.md P1 finding 9 (the
      7th "safe survivor" — flagged as needing this decision, never actioned).

## Why these weren't fixed inline

Both are cross-repo (strategy-service / e2e-testing) — outside this session's assigned repo (features-service) and its
narrow mandate (reconcile 2 stashed features-service fixes). Filed per the "every follow-up is a `- [ ]` todo, never
prose" HARD RULE so archiving the parent audit doc doesn't silently drop them.
