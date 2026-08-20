---
doc_type: issue
title: DeFi strategy_ids carry a banned _SCE_1H suffix — an identity migration, not a rename
summary: >-
  Several DeFi strategy configs carry `_SCE_1H` in their `strategy_id`, but
  /codex/09-strategy/architecture-v2/axes/hold-policy.md rules that "DeFi strategies are NEVER SCE (gas +
  confirmation latency)". The runtime behaviour is correct — carry_staked_basis sets `execution_mode: continuous`,
  held rather than round-tripped — so this is a naming defect, not a behavioural one. It matters because
  `strategy_id` is an identity that lands in stored ledger and manifest data, so correcting it is a migration with
  downstream consumers, not a find-and-replace.
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [strategy-service]
scope: [engineer, admin]
tags: [defi, strategy-id, naming, hold-policy, identity-migration, entity-rename]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/09-strategy/architecture-v2/axes/hold-policy.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
  ]
context_scope:
  [
    /codex/09-strategy/architecture-v2/axes/hold-policy.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    strategy-service/strategy_service/close_all/carry_staked_basis.py,
    strategy-service/strategy_service/configs/carry_staked_basis.yaml,
    strategy-service/scripts/dump_legacy_mapping_to_yaml.py,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Operator reviewing the carry_staked_basis config example in the client artefacts — "we certainly wouldn't do same
  candle exit, not in and out of the basis, we're just IN the basis". A sub-agent verified the behaviour is correct
  and the suffix is stale; the orchestrating session confirmed the spread across files.
drift_direction: advance-code
depends_on: []
---

# `_SCE_1H` on DeFi strategy_ids contradicts the hold-policy rule

## The nuance that matters

**The behaviour is right.** `strategy_service/configs/carry_staked_basis.yaml` sets `execution_mode: continuous` —
the position is held, not round-tripped intraday, exactly as a staked-basis carry should be. Nobody is doing
same-candle exits on a DeFi basis.

**The identity is wrong.** The `strategy_id` carries a stale `_SCE_1H` suffix, against
[hold-policy](/codex/09-strategy/architecture-v2/axes/hold-policy.md): *"DeFi strategies are NEVER SCE (gas +
confirmation latency). SCE is only for CeFi/TradFi."*

A reader — including the operator, which is how this surfaced — reasonably reads the id as a declaration of intent
and concludes we are same-candle-exiting a basis position. The artefacts inherited that confusion.

## Measured spread 2026-08-19

`SCE_1H` appears in strategy-service across at least: `configs/liquidation_capture_eth.yaml`,
`docs/CONFIG_SCHEMA.md`, `scripts/backfill_strategy_instructions_orphan_class_e.py`,
`scripts/dump_legacy_mapping_to_yaml.py`, `strategy_service/close_all/carry_staked_basis.py`,
`strategy_service/close_all/__init__.py`, `tests/unit/risk/test_smoke_liquidation.py`,
`tests/unit/risk/test_smoke_drawdown.py`.

## Why this is a migration, not a rename

`strategy_id` is an **identity that is written into stored data** — ledgers, manifests, instruction records,
backtest outputs. Per
[entity-rename-and-split-consumer-migration-rule](/codex/02-data/entity-rename-and-split-consumer-migration-rule.md),
renaming an entity must enumerate and migrate **every consumer in the same change**, and a token grep misses
path-prefix, filename and registry-membership binders. Changing the yaml alone would orphan every historical row
keyed to the old id.

## Todos

- [ ] [AGENT] P1. **Enumerate every consumer of the affected `strategy_id` values** before changing anything —
      stored GCS rows, manifest entries, ledger records, backtest artefacts, registry memberships, and the two
      scripts that appear to map legacy ids. A rename that leaves historical data keyed to the old id is worse than
      the stale suffix.
- [x] [OPERATOR] P1. ✅ **RULED 2026-08-19: MIGRATE the strategy_id properly.** Document-and-leave was offered and
      declined. The migration is therefore in scope and governed by the entity-rename consumer-migration rule.
- [ ] [BACKEND] P1. **Execute the migration** (ruling landed 2026-08-19): change the id and migrate every consumer
      in the SAME change, with no shim. Gate this behind the enumeration todo above — starting the rename before
      the consumer list is complete is how historical rows get orphaned.
- [ ] [DOC] P2. **Check the sibling DeFi configs** for the same suffix and for any other axis token in a
      `strategy_id` that contradicts its own config body — this was found by reading one example, so the sample is
      one.

## Related correction already applied

`timeframe: 1h` on these configs is a **feature/backtest bar resolution**, not a risk-check or exit cadence
(`cli/handlers/batch_handler.py`). The artefacts previously implied it was an evaluation cadence; that has been
corrected. Liquidation response is event-triggered and tracked separately in
[health_factor_monitor_no_production_entrypoint](/plans/active/issues/health_factor_monitor_no_production_entrypoint_liquidation_unprotected_2026_08_19.md).

## Progress Log

**2026-08-19 — filed.** No code touched. Behaviour verified correct; only the identity string is wrong.
- **context-scout 2026-08-20**: populated context_scope (5 entries)
