---
doc_type: plan
title: Solana ORCA/RAYDIUM dex_pool_swaps indexer — signature-walk + swap decoder + manifest write
summary: >-
  Build the genuine on-chain Solana swap-event indexer for ORCA/RAYDIUM dex_pool_swaps (operator ruling 2026-08-08 —
  prioritize now), per solana_dex_pool_swaps_indexer_scope_2026_07_12.md's own scoping + "Recommended next step"
  implementation breakdown. Multi-stage build (generalize the existing signature-index walker → per-tx fetch+decode per
  venue → manifest write), sized brand-new (~1 AI-day per the scoping doc's own estimate).
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, solana, dex-pool-swaps, indexer, orca, raydium, new-capability, whirlpool]
related:
  [
    /plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-08-08 (na-corpus-digest round5, item 74): prioritize the ORCA/RAYDIUM dex_pool_swaps indexer now.
  Filed per solana_dex_pool_swaps_indexer_scope_2026_07_12.md's own "Recommended next step" 5-step breakdown — this plan
  does not build the indexer itself in that scoping session, only converts the already-scoped design into a dispatchable
  plan.
context_scope:
  [
    /plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    market-tick-data-service/market_tick_data_service/scripts/_sig_index_walker.py,
    market-tick-data-service/market_tick_data_service/scripts/_orca_swap_decoder.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
  ]
---

# Solana ORCA/RAYDIUM dex_pool_swaps indexer

> **Scoping SSOT**: `/plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` — read it first. It
> confirmed (code-read, not inferred) that no existing MTDS path produces ORCA/RAYDIUM swap events: `SolanaDefiHandler`
> only captures `dex_pool_state` (periodic REST snapshots); `DexSwapsHandler`'s Solana routing always resolves to no
> subgraph (ORCA/RAYDIUM are REST-API venues, not subgraph-indexed); the `orca_defi_ws.py` / `raydium_defi_ws.py` live
> connectors are Jupiter-quote PRICE pollers, not swap-transaction capture. Genuinely new on-chain indexer capability is
> needed. A reusable HALF-precedent already exists in this codebase:
> `market_tick_data_service/scripts/build_drift_v2_sig_index.py` (657 lines) walks Helius RPC `getSignaturesForAddress`
> for a Solana program address from HEAD backwards, chunk-flushing to GCS parts with `--resume` support — avoids the OOM
> class this codebase hit before holding millions of signatures in RAM. It does NOT fetch/decode the actual swap
> transaction — that is this plan's net-new scope. Program addresses are already registered in UAC
> (`_defi_chain_data.py`): `raydium.program_id = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"`,
> `orca.program_id = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"`.

## Todos

- [x] ✅ [DATA] P0. **Generalize `build_drift_v2_sig_index.py`'s chunk-flush/resume signature-walk core to accept an
      arbitrary program address**, so ORCA/RAYDIUM can reuse the exact same OOM-safe walk instead of a second bespoke
      implementation. Extract the reusable core into a shared helper module (do not duplicate the walk loop). Repo:
      market-tick-data-service. Done-when: a new unit test proves the generalized walker produces an identical
      signature-index output for the Drift V2 program address as the original script did (no regression), plus a second
      test exercising it against a different (ORCA) program address. — market-tick-data-service@e1425abf. **Finding**:
      `build_drift_v2_sig_index.py` (and its test suite) no longer exist — deleted 2026-07-16 by the DRIFT/PACIFICA
      removal operator ruling (`2e674d1f`; recorded in `/codex/04-architecture/solana-defi-coverage.md`), 3+ weeks
      before this plan was authored; the scoping doc predates that removal (2026-07-12) so its "existing file" premise
      went stale. Recovered the deleted script via `git show 2e674d1f~1:...` as the design reference and extracted its
      generalized core (program_id now a parameter, not hardcoded) into new
      `market_tick_data_service/scripts/_sig_index_walker.py`, with 22 unit tests (parametrized over the old Drift V2
      program address for regression + the ORCA Whirlpool address) in `tests/unit/scripts/test_sig_index_walker.py` —
      Drift's address is used only as an inert string constant, no Drift capability restored. `quality-gates.sh` green.
- [x] ✅ [DATA] P1. **Build the per-signature transaction fetch + Whirlpool (ORCA) swap-instruction decoder.** For each
      indexed ORCA signature (from the generalized walker above), fetch the full transaction via Helius
      `getTransaction`, decode the Whirlpool swap instruction's account + data layout into
      `(pool, base_amount, quote_amount, side, price)`. Start here — Orca's swap instruction layout is
      simpler/better-documented than Raydium's CLMM/CPMM variants (per the scoping doc's own recommendation). Repo:
      market-tick-data-service. Done-when: a unit test decodes a real captured ORCA swap transaction (fixture) into the
      expected tuple, with honest-absence (skip + log, never raise) on an unparseable/unexpected instruction layout. —
      market-tick-data-service@3619f9e2. Fetch via the existing shared `solana_get_transaction` (`_solana_rpc_async.py`,
      plain `json` encoding). New `_dex_swap_tx_helpers.py` (program-agnostic: `resolve_account_keys`,
      `iter_program_instructions` incl. inner/CPI, `token_balance_delta`) + `_orca_swap_decoder.py` (Whirlpool `swap`
      Anchor-discriminator decode, executed amounts derived from real `preTokenBalances`/`postTokenBalances` vault
      deltas — NOT the instruction args, since `otherAmountThreshold` is only a slippage bound). 24 new unit tests
      (synthetic `getTransaction`-shaped fixtures, top-level + inner-CPI + honest-absence paths), `quality-gates.sh`
      green, `basedpyright` strict clean (no new suppressions).
- [ ] [DATA] P1. **Build the per-signature transaction fetch + Raydium swap-instruction decoder** — same shape as the
      ORCA decoder above, branching on AMM version (legacy AMM vs CLMM vs CPMM, each with a different swap instruction
      shape per the scoping doc). Repo: market-tick-data-service. Done-when: a unit test decodes a real captured Raydium
      swap transaction fixture per AMM version into the expected tuple, honest-absence on an unrecognized
      version/layout.
- [ ] [DATA] P1. **Wire both decoders' output through
      `ManifestWriter.record_captured(..., data_type="dex_pool_swaps")`** following the same
      `pipeline_mode`/honest-absence conventions the rest of this asset_group already uses (mirror `dex_pool_state`'s
      existing `EXPECTED_PRE_VENUE_LAUNCH` pre-genesis handling). New CLI operation (e.g.
      `--operation collect-solana-dex-pool-swaps`) or extend `SolanaDefiHandler` — follow the existing handler
      registration pattern (`cli/main.py`). Repo: market-tick-data-service. Done-when: a full unit-test pass (walker +
      decoders + manifest write, mocked Helius responses) writes a real `dex_pool_swaps` shard for at least one ORCA and
      one RAYDIUM pool with correct schema, and `quality-gates.sh` is green.
- [ ] [DATA] P2. **Backfill VM launch + G2 re-verification** — once the indexer is unit-tested green, launch a bounded SPOT-VM smoke run (a few days, NOT full history) to prove the walker+decoder+write path against real on-chain data.
      Then re-verify `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s G2 gate now covers ORCA/RAYDIUM `dex_pool_swaps`
      (that gate's own text currently excludes this as a known, separately-tracked gap — this todo is what lets that
      gate's language become accurate). **No `[OPERATOR]` tag needed** (task_template.md §3 findings O/Q/U): this is a
      bounded, write-only SPOT-VM smoke run that adds NEW `dex_pool_swaps` rows and deletes/overwrites nothing existing
      in the corpus, matching the standard reversible SPOT-backfill pattern this asset_group already uses
      (`/codex/05-infrastructure/spot-vms-for-backfill.md`) — register the launcher via `VM_PREFIX_TO_BUCKET` per
      `/codex/05-infrastructure/vm-launcher-runbook.md`, never hand-roll. Repo: market-tick-data-service +
      deployment-service (VM launch). Done-when: real `dex_pool_swaps` manifest rows exist for ORCA and RAYDIUM on at
      least one live day, manifest-counted (not log-activity), and the G2 gate text is updated to drop the exclusion.

## Progress Log

- **plan-reconcile 2026-08-19 (mtds_mdps_master, hunter batch B)**: fixed the todo-5 (Backfill VM launch + G2
  re-verification) AO-dispatch-readiness gap flagged by 3 prior `/plan-reconcile` passes through 2026-08-18 (most
  recently `plan_reconciler_findings_defi_master_epic_2026_08_18.md` item 4) — a VM-launch/data todo on an
  `assigned_vm: planning` doc with no `[OPERATOR]` tag and no inline safe-idempotent justification (task_template.md §3
  findings O/T/U). Applied finding Q/U's self-justifying path: added an inline note that this is a bounded, write-only
  SPOT-VM smoke run (a few days, not full history) that adds NEW `dex_pool_swaps` rows and deletes/overwrites nothing
  existing, matching the standard reversible SPOT-backfill pattern already used elsewhere in this asset_group, plus a
  `VM_PREFIX_TO_BUCKET` registration reminder per the vm-launcher-runbook. Also moved the todo's hard constraint
  ("SPOT-VM... a few days, NOT full history") fully onto the todo's first physical line — the pre-fix wrap split it
  across lines 1-2, invisible to `regen_backlog_from_plan.py`'s line-1-only brief parser. No code changed; docs-only.
- **2026-08-08 (slot-33, item 2)**: shipped the ORCA Whirlpool per-signature fetch + swap decoder —
  market-tick-data-service@3619f9e2. Note: this exact task (`solana_dex_pool_swaps_indexer-002`) had wedged 4 other
  slots (11, 9, 33-earlier-incarnation, 7) via the fleet-wide post-compact respawn crash-loop in the ~17:31Z-18:02Z
  window and was durably `park`ed by main-agent at ~18:02Z pending root-cause
  (`/plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md`) — this session's dispatch
  landed just before that park took effect and completed a clean boot->work->done cycle with no wedge, which is direct
  evidence for that issue doc's REVIEW todo 4. Noted in that doc's own Progress Log rather than duplicated here.
- **2026-08-08 (round5-na-digest-defi apply pass, item 74)**: authored this plan per operator ruling ("prioritize it
  now") and the source scoping doc's own 5-step implementation breakdown. `sequential: true` — the todos are a real
  dependency chain (the generalized walker must land before either decoder can be built against it; the manifest-write
  wiring needs both decoders; the backfill VM needs the wired write path). No indexer code built in this session, per
  the operator's own scope for this todo (file/flip the plan, don't build the indexer inline).
- **context-scout 2026-08-17**: refreshed context_scope (5 entries) — `build_drift_v2_sig_index.py` no longer exists
  on disk (deleted 2026-07-16, per the doc's own todo-1 finding); replaced with its generalized successor
  `_sig_index_walker.py` and added `_orca_swap_decoder.py` (the shipped ORCA decoder the sole open Raydium-decoder
  todo is explicitly modeled on). Both handler files kept — todo 4 (manifest-write wiring) names
  `SolanaDefiHandler` as a candidate integration point alongside a new CLI operation.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
