---
name: predictions_master_audit_instructions
type: audit-instructions
epic: predictions_master
assigned_vm: vm-prediction
tier: L0
last_updated: 2026-06-01
---

# Predictions Master — Audit Instructions

## Epic Scope

Prediction market adapters (Polymarket, Kalshi), binary-outcome archetype definitions, and the Polymarket vs Kalshi
spread strategy. Key invariant: binary resolution events handled correctly; no hardcoded market IDs.

## Triggers

- Weekly (minimum cadence)
- After major prediction market events (US elections, macro events)
- When UAC binary-outcome schema changes
- When new prediction market venues are considered for universe expansion

## Checklist

- [ ] (a) **Polymarket adapter handles binary resolution**: adapter correctly processes `resolved: true/false` events
      and emits manifest rows with `capture_status=captured` or `empty_confirmed[reason=SOURCE_RETURNED_ZERO]`. Read:
      Polymarket adapter + verify resolution event handling

- [ ] (b) **Kalshi adapter covers REST + WebSocket**: both polling (batch) and streaming (live) modes implemented. Find:
      `rg "kalshi" market-tick-data-service/ --include="*.py" -l` Verify: `--mode batch` and `--mode live` both present
      in adapter

- [ ] (c) **Polymarket vs Kalshi spread archetype**: archetype produces valid signals when market exists on both venues.
      Read: strategy-service archetype for predictions — verify it handles the case where only one venue has the market

- [ ] (d) **UAC binary-outcome schema completeness**: all fields needed by the spread archetype are present in UAC.
      Read: `unified_api_contracts/canonical/domain/predictions/` — verify schema covers outcome probability, settlement
      time, market liquidity, and resolution status

- [ ] (e) **Manifest rows with asset_group=prediction**: archetypes emit rows with correct hive key. Check: A3 manifest
      divergence scan for `asset_group=prediction` — zero `MISSING_EXPECTED`

- [ ] (f) **No hardcoded market IDs**: archetype logic does not reference specific Polymarket/Kalshi market IDs. Grep:
      `rg "0x[a-f0-9]{40}|market_id.*=.*\"[A-Z]" strategy-service/ --include="*.py"` — should be 0 hits in archetype
      business logic (only in test fixtures is acceptable)

- [ ] (g) **Credential asks filed**: if Polymarket or Kalshi API keys not provisioned, `BLOCKED-CREDENTIALS` ping filed
      with account type, cost, and unblocks.

### Data-source provenance — stamp source NOW; venue ≠ source still holds

> Codified 2026-06-01 (crosscutting plan: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`). **TWO
> distinct facts, both true:** (1) **provenance is universal** — every prediction cell stamps its `source`
> (`polymarket_clob` / `polymarket_gamma_api` / `kalshi_*`) NOW, even though each venue has one source today, for
> swap-resilience (a future Polymarket data-provider change is "the same issue"); a blank `source` is RED. (2) **venue ≠
> source** — Polymarket and Kalshi are separate **venues**, NOT two sources of one shard; the
> `arbitrage_price_dispersion` model compares across venues at the feature layer, never via per-row source merge.
> Stamping each venue-cell's own `source` (fact 1) does NOT collapse venues into sources (fact 2).

- [ ] (h) **Writers stamp `source` on every prediction cell now**: pass `source=` (the venue's data source string from
      `SOURCE_PRIORITY`) at every prediction write. Read ACTUAL prod rows — RED on any blank `source`.
      `market-tick-data-service/.../engine/orchestrator.py` (`record_captured_from_counts`).
- [ ] (i) **Venue ≠ source invariant holds**: prediction shards are keyed by `venue` (POLYMARKET / KALSHI); the
      dispersion strategy consumes separate per-venue rows. No code path merges two venues into one shard via source
      resolution. Trace: strategy-service prediction archetype → features-service spread calc.
- [ ] (j) **Kalshi lands as a venue, not a source**: when Kalshi capture ships, it is a `venue=KALSHI` addition (with
      its own `source` stamped) — NOT a second source of a Polymarket shard.

### E2E Batch, Paper, and Live Verification

- (e2e-batch) **Batch e2e**: For the MVP archetypes of this domain, run a dry-run batch audit using mock upstream
  fixtures (`CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`) — confirm signals are generated end-to-end from adapter output
  through strategy. If real upstream unavailable, synthetic fixtures from `tests/e2e/fixtures/` suffice; the test MUST
  exercise the downstream code regardless of upstream readiness.
- (e2e-paper) **Paper trading audit** (once paper is running): confirm paper PnL events flow from strategy → execution →
  PnL calculator for ≥1 MVP archetype in this domain. Check manifest for strategy_output rows with
  `capture_status=captured` for the date range. If paper not yet running, verify the code path is wired (not
  BLOCKED-CREDENTIALS level — code exists, paper not started).
- (e2e-live) **Live trading audit** (once live is running): verify live execution produces execution_record rows in
  manifest with no DIVERGENT_EMPTY. Alert thresholds fire within SLA. PnL reported correctly.
- (mock-upstream) **Mock upstream pattern**: this domain's audit MUST be runnable WITHOUT live upstream data. Document
  the exact `pytest` fixtures or `CLOUD_MOCK_MODE=true` invocation in `## Output Format` so any slot can run the
  downstream-only audit independently.

- [ ] (consolidation-health) **Per-group manifest consolidation health**: this asset_group's consolidated
      `_index/availability_index.parquet` (resolve the bucket via `resolve_bucket_name(...)` — never hardcode `gs://`)
      is fresh (mtime advances ~per consolidator cycle) and its per-VM shards consolidate without OOM. Cross-ref the
      shared engine + 24h OOM/freshness recipe in `manifest_master_audit_instructions.md` (h2/h3) +
      `manifest_consolidator_duckdb_memory_fix_2026_05_26.md` (the DuckDB memory-bound merge is UTL Tier-0, shared by
      every asset_group).

## Success Criteria

- All 7 checklist items GREEN
- `a6_batch_live_adapter_parity.py` shows parity for `asset_group=prediction` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for prediction asset_group
- QG exits 0 for features-service (predictions family)
- e2e batch audit produces signals for ≥1 MVP archetype using mock upstream data (CLOUD_MOCK_MODE=true green)
- Paper trading goal post: ≥1 archetype runs ≥7 continuous paper days without silent failures

## Output Format

Result file at `plans/audit/results/predictions_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
