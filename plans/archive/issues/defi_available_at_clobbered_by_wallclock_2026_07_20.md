---
doc_type: issue
title:
  "DeFi `available_at` — the on-chain stamp is computed and then CLOBBERED with wall-clock `now()` on the write path
  (breaks the batch==live ε=0 determinism contract)"
summary: >-
  Several DeFi handlers call `stamp_available_at_onchain_tick(df)` (which sets `available_at` = the on-chain block /
  snapshot timestamp — the deterministic, replayable value) and then immediately overwrite that column with
  `datetime.now(UTC)` before upload. In `gas_fee_handler` the stamp and its clobber are ADJACENT lines (507→508, and
  again 592→593); in `solana_defi_handler` the stamp is applied at the call site (`:636`) and clobbered inside
  `_upload_parquet` (`:149`). Net effect on a HISTORICAL backfill: the shipped `available_at` is the wall-clock time the
  backfill happened to run, not when the data became available on-chain. That is non-deterministic across re-runs, so a
  batch re-run of window W cannot reproduce paper(W) — the ε=0 contract in
  `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — and any point-in-time / lookahead filter keyed
  on `available_at` silently uses a fabricated time. Found while designing the DeFi backfill optimization (the streaming
  write-path port would have propagated the pattern); NOT introduced by that work.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    available-at,
    lookahead,
    batch-equals-live,
    determinism,
    operator-notify,
    backfill,
    gas-fees,
    solana-defi,
  ]
related:
  - plans/active/defi_consolidated_closeout_2026_07_18.md
  - /codex/09-strategy/operational/paper-batch-live-reconciliation.md
  - /codex/02-data/live-data-persistence-and-event-log.md
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
source:
  [
    "discovered 2026-07-20 during DeFi handler review; frontmatter repaired 2026-07-20 — the plan-health-autofix bot had
    committed an unquoted multi-line summary containing ': ', which is invalid YAML and blocked PM's frontmatter-schema
    gate for every agent",
  ]
resolved_by:
  "mtds@f7af6ece (3 on-chain clobbers) + mtds@51ec9af2 (broader 17-handler follow-up, 2026-07-22 — see RESOLVED section
  below)"
---

## RESOLVED (broader follow-up, 17 handlers) 2026-07-22 — mtds@51ec9af2

Applied the same "keep the on-chain tick" policy to the ~26 remaining handlers flagged in the section below. Per-handler
investigation (parallel workflow, adversarially verified, then independently re-verified via full quality-gates.sh +
real test-suite runs) determined which handlers' fetched row data genuinely carries a deterministic on-chain/event
timestamp:

- **17 handlers fixed**: `_dex_pools_subgraph.py` (EVM subgraph site only — the Solana REST-snapshot site has no real
  timestamp, correctly left alone), `_perp_funding_gmx.py`, `_perp_funding_kalshi_polymarket.py`,
  `bridge_events_handler.py`, `dex_swaps_handler.py`, `flash_loan_events_handler.py`, `gas_fee_handler.py` (2 of its 4
  sites — the other 2 trace back to process-start wall-clock even via `stamp_available_at_explicit`, correctly left
  alone), `governance_events_handler.py`, `governance_proposals_handler.py` (`created_at` from the subgraph/Snapshot
  response), `lending_indices_handler.py` (both Solana + EVM sites), `liquidation_events_handler.py` (`ts_event`),
  `liquidations_handler.py`, `mev_events_handler.py`, `oracle_prices_handler.py`, `orca_whirlpool_state_handler.py`,
  `protocol_outage_detector_handler.py`, `raydium_classic_amm_handler.py`.
- **9 handlers investigated, left untouched** (genuinely no historical/event timestamp in the fetched payload —
  wall-clock is the honest fallback, per this doc's own carve-out): `data_manifest_handler.py`,
  `eigenlayer_rewards_handler.py`, `jupiter_quote_handler.py`, `lst_rates_handler.py` (its
  `stamp_available_at_explicit(when=attempted_at)` traces to `datetime.now(UTC)` computed at process-start, not a real
  on-chain time — same "disguised wall-clock" class as gas_fee's 2 untouched sites), `native_staking_handler.py`,
  `position_data_handler.py`, `risk_params_handler.py`, `staking_yields_handler.py`, `token_transfers_handler.py`,
  `vault_share_price_handler.py`.

Caught and fixed 3 real test-fixture bugs during verification (mock DataFrames missing the
`created_at`/`ts_event`/`timestamp` column the fix now requires — the underlying fetch functions genuinely return that
column, only the hand-built test mocks omitted it). Split `liquidations_handler.py`'s GraphQL query constants into a new
`_liquidations_queries.py` sibling module to stay under the 900-line file cap after the fix's net line addition (mirrors
the pre-existing `_dex_swaps_queries.py` pattern).

No corrective backfill of already-written parquets was scoped or run this session — this resolves the write-path only,
per Option A from "Options for the operator" below.

## RESOLVED (3 on-chain clobbers) 2026-07-21 — mtds@f7af6ece

Operator ruled 'keep the on-chain tick'. Removed the `.assign(available_at=now())` clobber at the 3 sites where a
deterministic on-chain stamp existed and was overwritten: `evm_defi_collectors._write_and_upload`,
`solana_defi_handler._upload_parquet`, `gas_fee_handler` (Solana slot path). The on-chain tick now survives to the
uploaded parquet (+regression test `TestUploadParquetPreservesAvailableAt`).

**BROADER FOLLOW-UP (still open):** ~20 other DeFi handlers
(governance/mev/dex_swaps/lst_rates/_dex_pools_subgraph/liquidations/risk_params/…) set `available_at=now()` DIRECTLY
with NO on-chain stamp, and gas_fee's Solana/Bitcoin paths use `stamp_available_at_explicit(when=now())`. Those are the
SAME determinism bug class but have no on-chain stamp to 'keep' — each needs a per-handler deterministic-timestamp
derivation (from the block/snapshot/slot time in its data). That is a separate, careful per-handler pass, not covered by
the ruled clobber fix.

---

# `available_at` is clobbered with wall-clock `now()` after the on-chain stamp

> **⚠️ OPERATOR RULING REQUIRED before any code change.** The fix direction is obvious mechanically (stop clobbering),
> but the INTENDED semantics of `available_at` for DeFi snapshot data is a modelling decision that changes what
> downstream point-in-time filtering does, and may imply a corrective backfill of already-written parquets. Do not "fix
> while porting" — that was the explicit trap this was found in.

## What the code does today (VERIFIED, not inferred)

`stamp_available_at_onchain_tick(df)` (`unified-trading-library/unified_trading_library/availability_stamping.py:745`)
sets `available_at = timestamp_col` — the on-chain block time / snapshot tick. That is the deterministic value: re-run
the same historical day a year later and you get the same answer.

The clobbers, each read directly:

| Site                                           | What happens                                                                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `cli/handlers/gas_fee_handler.py:507` → `:508` | `stamp_available_at_onchain_tick(shard_df)` then `assign(available_at=now())`                   |
| `cli/handlers/gas_fee_handler.py:592` → `:593` | `stamp_available_at_explicit(..., when=now())` then `assign(available_at=now())`                |
| `cli/handlers/solana_defi_handler.py:636`      | passes `stamp_available_at_onchain_tick(shard_df)` INTO `_upload_parquet`                       |
| `cli/handlers/solana_defi_handler.py:149`      | `_upload_parquet` body: `df.assign(available_at=datetime.now(UTC).isoformat())` — unconditional |

So in every one of these the on-chain stamp is computed, then discarded.

Additional handlers assign wall-clock `available_at` with no on-chain stamp at all — `dex_swaps_handler.py:523`,
`mev_events_handler.py:141`, `governance_events_handler.py:135`, `liquidation_events_handler.py:314`,
`risk_params_handler.py:661`, `data_manifest_handler.py:434`. **These are listed as scope, NOT asserted as bugs** — some
of these payloads may have no natural on-chain timestamp, in which case wall-clock may be the intended fallback. That
distinction is part of what needs the ruling.

## Why it matters

1. **Batch==live ε=0 is broken for these shards.** `paper(W)` must equal `batch-rerun(W)` trade-for-trade. A column
   whose value is "whenever the backfill happened to run" cannot satisfy that — re-running the same window produces
   different `available_at`, so any strategy filtering on it sees a different world.
2. **Lookahead safety is silently wrong in BOTH directions on historical days.** A 2022 row backfilled today is stamped
   2026-07-20 — far in the future relative to its own data, so a point-in-time filter would exclude data it should
   include (or, depending on comparison direction, admit data it should not).
3. **It is invisible.** Nothing errors; the parquet is well-formed and the manifest is happy. It only shows up as an
   unexplained ε≠0 in reconciliation.

## What is NOT claimed

- No claim about how many already-written objects carry a wrong stamp. Quantifying that requires reading `available_at`
  out of the DeFi corpus, which has not been done.
- No claim that wall-clock is wrong for the no-on-chain-stamp handlers listed above.
- No claim this is new. `git log` was not bisected; treat as long-standing until someone checks.

## Options for the operator

- **A (recommended)** — `available_at` = on-chain tick for anything with a block/snapshot timestamp; delete the
  clobbering `assign` at the four verified sites; make `_upload_parquet` NEVER touch `available_at` (it is a transport
  function and has no business stamping semantics). Then scope a corrective backfill separately.
- **B** — keep wall-clock deliberately and document `available_at` as "ingest time, not availability time", which means
  removing it from any ε=0 / point-in-time path and finding another column for those.
- **C** — per-data_type policy (on-chain where available, ingest otherwise), which is closest to today's accidental
  behaviour but made explicit and tested.

Whichever is chosen, add a regression test asserting that a historical-day re-run produces a byte-identical
`available_at` — that is the property that actually protects ε=0.

## Provenance

Surfaced 2026-07-20 by the adversarial-verification phase of the DeFi backfill-optimization design workflow
(`wf_c3e50e71-248`), which flagged that the proposed streaming write path was instructed to "reproduce BOTH stampings"
and would have carried the bug into the new path. Independently re-verified line-by-line before filing.
