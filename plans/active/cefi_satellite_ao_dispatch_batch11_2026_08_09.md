---
doc_type: plan
title: CeFi satellite AO batch 11 — item-level extraction from 19 non-qualifying NA docs (cefi_master group)
summary: >-
  Eleventh AO-dispatch batch for cefi. Produced by a per-item satellite-extraction pass over the 19 cefi-tranche
  `assigned_vm: NA` docs that a same-day RECLASSIFY sweep read end-to-end but did NOT whole-doc-flip (each carries at
  least one genuine judgment/design/operator-gated item). Mirrors `/ag-closeout-audit`'s carve-out pattern but applied
  per-item rather than per-doc: 4 parallel research passes (one per doc-group) classified every open item in all 19 docs
  against the bounded-outcome bar (`codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §5), found 16
  genuinely extractable items total, grouped by `parent_epic` per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2. This batch is the `parent_epic:
  cefi_master` group (10 items, 3 source docs) — sibling batches 12/13/14 (dated the same day) cover the
  `infrastructure_master`/`strategy_master`/`execution_master` groups respectively. Every item was independently
  spot-verified against live code/doc state (not just trusted from the research pass) before inclusion — see the
  Progress Log for the specific verification notes, including one item (todo 5, Barchart removal) that was
  conflict-checked against several TradFi docs mentioning "Barchart" and confirmed non-duplicative (those docs track
  data/manifest state, none claims the literal code-deletion this todo performs).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    deployment-service,
    market-tick-data-service,
    unified-api-contracts,
    e2e-testing,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-11, satellite-docs, item-level-extraction, na-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /plans/active/cefi_ml_directional_continuous_live_2026_06_20.md,
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /plans/active/cefi_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/active/cefi_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/cefi_satellite_ao_dispatch_batch14_2026_08_09.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Item-level satellite-extraction pass 2026-08-09 over the 19-doc cefi RECLASSIFY-sweep-non-qualifying candidate list,
  mirroring `/ag-closeout-audit`'s carve-out pattern applied per-item. 4 parallel general-purpose research agents each
  read a subset of the 19 docs end-to-end (including dated Progress Log sections), classified every open item against
  the bounded-outcome bar, and drafted candidate todos; the main session then independently spot-verified the
  highest-stakes items (code reads, line-number checks, conflict greps across the active-plan corpus) before drafting
  this doc. Full per-item classification detail (all 19 docs, EXTRACTABLE/STAYS-BEHIND with reasons) is retained in the
  4 research agents' transcripts, not duplicated here.
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# CeFi satellite AO batch 11 — item-level extraction (cefi_master group)

> **Status: ACTIVE.** Conflict-checked against the live corpus 2026-08-09 (see Progress Log) — no overlap found with any
> other active `assigned_vm: planning` plan in `parent_epic: cefi_master`, `cefi_satellite_ao_dispatch_batch9/10`, or
> `cefi_consolidated_closeout_2026_07_18.md`'s own content (todos 1-5 below ARE `cefi_consolidated_closeout`'s Track 0
> items, extracted from there directly — its checkbox is being replaced with a pointer to this doc in the same commit as
> this file). **Cross-todo file-collision check**: todos 1/3/7/8/9/10 are operational runs/audits with no durable
> code-file target (or a conditional one, only touched if the audit finds something); todo 2 targets
> `unified-api-contracts`' index-perp canonical-mapping registry; todo 4 targets `unified-api-contracts`' L-floor
> lookback constants (a different module from todo 2); todo 5 deletes Barchart adapter/client files in
> `unified-api-contracts` + `market-tick-data-service` (no overlap with todo 2/4's files); todo 6 extends
> `market-tick-data-service`'s live-book connectors (different code path from todo 5's deletion). No file is edited by
> more than one todo.

## Todos

- [ ] [SCRIPT] P0. **Run the IS→catalogue→enumerator→MTDS propagation-ops wave chain (B1/B3/B4) to completion** for the
      new Binance tradfi-perp cash-twin equities: instruments-service backfill → `build_instrument_catalogue` rollup →
      `enumerate_expected_universe.py` v2 tradfi → MTDS wave. Repos: deployment-service, instruments-service. Source:
      `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 136, cites source Phase 1b). **Done when**: the catalogue
      shows the new MVP tickers, the manifest shows them `expected_unattempted`, and a sample equity capture shows
      non-NaN OHLCV.
- [ ] [UAC] P0. **Map the index perps** (`SPXUSDT`/`NAS100`/`SPYUSDT`/`XAUUSDT`) to their CME index-future + Databento
      index canonical equivalents in unified-api-contracts, carrying the scale/multiplier (Binance SPX-perp is a SCALED
      micro unit — sizing MUST use the multiplier for the ES hedge ratio). Repo: unified-api-contracts. Source:
      `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 158, cites source Phase 1c). **Done when**: all 4 index
      perps have a canonical mapping + multiplier committed, `quality-gates.sh` green.
- [ ] [SCRIPT] P1. **Backfill the 3 KRX stocks** (HYUNDAI/SAMSUNG/SK-Hynix cash-twins) **via guardrailed Yahoo**: 1d
      since 2019-01-01 + 1h trailing 730d + 15m trailing 89d (range=60d) + 1m 28-day-chunked. Repos: deployment-service,
      market-tick-data-service. Source: `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 168, cites source Phase
      5). **Done when**: the manifest shows captured, non-NaN rows for all 4 windows across all 3 symbols.
- [ ] [UAC] P1. **Measure the exact Databento lookback-floor boundary per level** (L0/L1/L2/L3) live and update
      `LEVEL_MAX_LOOKBACK_DAYS`/`earliest_allowed_start`/`assert_lookback_allowed` in unified-api-contracts to the
      measured values. Repo: unified-api-contracts. Source: `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line
      170, cites source Phase 5). **Done when**: each level's floor is measured and the 3 named constants/functions
      match the measured values, `quality-gates.sh` green.
- [ ] [REFACTOR] P2. **Deprecate and remove all Barchart code** (superseded by VX-futures-via-Databento for the VIX
      preload; CLAUDE.md: "VIX=VX-futures via XCBF.PITCH, Barchart RETIRED"): delete the adapter/client/source-registry
      entries in unified-api-contracts and market-tick-data-service, no shim. **Conflict-checked 2026-08-09**: grepped
      "Barchart" across the full active-plan corpus — several TradFi docs (`tradfi_registry_coverage_and_ao_readiness`,
      `tradfi_manifest_content_recovery_completion`, `tradfi_sp500_ml_and_arb_backtest_readiness`,
      `instruments_tradfi_g1_g5_gate_execution`) reference Barchart as an already-retired DATA source in
      manifest/docstring contexts — none claims the literal adapter-code deletion this todo performs; no conflict.
      Repos: unified-api-contracts, market-tick-data-service. Source: `cefi_consolidated_closeout_2026_07_18.md` Track 0
      (line 173, cites source Phase 5). **Done when**: no Barchart code/test references remain in either repo,
      `quality-gates.sh` green.
- [ ] [DATA] P2. **Extend market-tick-data-service's existing CeFi live-ws order-book connectors to also record live
      BBO+depth for the crypto-venue equity-perp instruments** (Binance/OKX/Bybit), for basis-arb slippage calibration.
      Repo: market-tick-data-service. Source: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 175.
      **Done when**: live BBO+depth is captured and persisted for at least one equity-perp instrument per venue,
      mirroring the existing non-equity-perp live-book capture shape, `quality-gates.sh` green.
- [ ] [DATA] P1. **Query OKX/Bybit/Hyperliquid's public instrument-listing endpoints for a WTI or Brent crude-oil
      perpetual contract**; if one exists, add it to the CeFi instrument universe (unified-api-contracts) mirroring how
      the existing commodity perps (XAU/XAG/COPPER) are registered. Repo: unified-api-contracts. Source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 795. **Done when**: the check result
      (found/not-found, per venue) is recorded; if found, the new perp is added with a passing unit test; if not found,
      the todo closes citing the negative-result evidence (endpoint responses showing no oil-perp symbol).
- [ ] [DATA] P1. **Re-run e2e-testing's NET-basis backtest with dividend yield priced into the long cash-stock leg** for
      each of the 12 net-profitable single-stock pairs (holding the stock earns dividends, adding to NET; the current
      +5-24% figures are a floor without it) — identify and use an already-available dividend-yield data source (check
      Databento DBEQ.BASIC corporate-actions coverage first). Repo: e2e-testing. Source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 820. **Done when**: an updated NET-basis table
      including dividend yield is produced for all 12 pairs and posted to that doc's Progress Log.
- [ ] [DATA] P1. **For each commodity/index perp currently NET-negative or NET-slim** (XAU/XAG/COPPER/SPX/SPY/NDX),
      check how far back its Binance listing/trade history goes, and cross-reference that window against the known
      contango/backwardation regime shifts already documented in that doc's NET-basis backtest (e.g. CL's -20%
      backwardation) to determine whether each perp's short history means the net-negative verdict is regime-conditional
      rather than permanent. Repo: instruments-service (read-only research). Source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 823. **Done when**: a per-symbol table of
      (listing date, history length, regime-window coverage) is produced and posted to that doc's Progress Log — no
      universe add/remove decision is made by this todo.
- [ ] [DATA] P1. **Run a window-scoped honest-coverage measurement**
      (`instruments-service/scripts/measure_honest_coverage.py     --asset-group cefi`, or a targeted
      `/data-pipeline-check-mtds` day-sample) restricted to OKX-SPOT/-SWAP/-FUTURES, BINANCE-SPOT/-FUTURES, BYBIT over
      2024-01-01→present — this is the blocking prerequisite the source doc's own P0 live-capital backtest-fidelity gate
      needs before it becomes schedulable (deliberately narrower/faster than the unrelated full-history 2019-2026
      chronological backfill tracked elsewhere). Repo: instruments-service. Source:
      `cefi_ml_directional_continuous_live_2026_06_20.md` line 180. **Done when**: a coverage % for exactly this venue
      set + window is cited in that plan's Progress Log with an `attempted_failed`/`expected_unattempted` breakdown; if
      materially below complete, the specific gap (venue/data_type/date range) is filed as its own blocking issue.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  this batch's authoring ran (§3), and the `parent_epic` grouping rule (§2) that split this extraction into 4 sibling
  batches (11/12/13/14) instead of one mixed-`parent_epic` doc.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded/checkable test applied to every item in all 19 source docs.
- `/plans/active/task_template.md` §3 finding U — the `[OPERATOR]`-tag positive test applied when deciding an item was
  NOT genuinely operator-gated (relevant to sibling batch12's mdps_features_deadcode item, cited here for the shared
  methodology).

## Progress Log

- **2026-08-09** — drafted from a 4-agent parallel item-level classification pass over the 19-doc cefi RECLASSIFY-sweep
  non-qualifying candidate list (candidate list: `/private/tmp/.../scratchpad/satellite_extract_cefi.txt`, not
  corpus-resident). 16 extractable items found across all 19 docs; this doc carries the 10 whose source doc's
  `parent_epic: cefi_master`. Every item independently re-verified against live code/doc state before inclusion: (1)
  todos 1-5 confirmed as the literal, currently-open checkboxes at `cefi_consolidated_closeout_2026_07_18.md` lines
  136/158/168/170/173 (direct `grep -n` read); (2) todos 6-9 confirmed as literal open checkboxes at
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` lines 175/795/820/823, and cross-checked that the OTHER
  ~8 open items in that same doc duplicating `cefi_consolidated_closeout` Track 0 content (lines
  108/219/234/241/622/644/648/673) were correctly NOT re-extracted here (already covered by todos 1-5 above, sourced
  from the closer/canonical Track 0 copy — extracting both would double-dispatch identical work); (3) todo 10 confirmed
  as the literal open checkbox at `cefi_ml_directional_continuous_live_2026_06_20.md` line 180, filed 2026-08-08 as the
  named blocking prerequisite for that doc's P0 backtest-fidelity gate (which itself correctly stays behind —
  dependency-blocked on this todo). **Conflict-check (per the shared protocol, §3)**: grepped the full `plans/active/`
  corpus for each todo's real target (Barchart, KRX/HYUNDAI, SPXUSDT/NAS100, LEVEL_MAX_LOOKBACK) — zero
  verbatim-duplicate claims found on any currently-active `assigned_vm: planning` plan; the many TradFi-doc "Barchart"
  hits are data/manifest-state references, not code-deletion claims (see todo 5's inline note). No sibling
  batch/finalize doc in `parent_epic: cefi_master` (batch9, batch10, their finalize twins) claims any of these 10 items
  — verified via direct grep of both docs' full text. `cefi_consolidated_closeout_2026_07_18.md`'s own checkbox for
  todos 1-5 replaced with a pointer to this doc in the same commit (see that doc's Track 0 section);
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`'s checkboxes for todos 6-9 replaced with pointers
  likewise; `cefi_ml_directional_continuous_live_2026_06_20.md`'s checkbox for todo 10 replaced with a pointer likewise
  — every non-extracted item in all 3 source docs left untouched.
