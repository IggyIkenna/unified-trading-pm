---
doc_type: issue
title:
  "CeFi margin model misclassifies healthy positions as WARNING/CRITICAL — hyphenated instrument ids (BTC-USD-PERP)
  never resolve a real MMR tier, so the fallback silently substitutes mmr_warning_pct itself as the assumed MMR rate"
summary: >-
  Discovered while adding emit_live_cefi_margin_events (capability_wizard_gap_discovery_2026_06_11.md P1 todo, slot-10,
  2026-07-27). A $40,000 BTC position with $1,000 debt (2.5% real margin usage, comfortably healthy) graded as 71.8%
  "usage" -> WARNING via _CefiMarginModelBase.compute() (unified-trading-library/.../margin_model.py:190-203). Root
  cause: the asset-symbol extraction (line 193) only strips a colon-delimited prefix (`"BTC:PERP:USDT".split(":")[0]` ->
  `"BTC"`), but AccountQueryClient / UPI adapters (strategy-service) return hyphenated instrument ids ("BTC-USD-PERP"),
  so the whole mangled string becomes "asset" and never matches CEFI_MARGIN_TIERS[(venue, "BTC"|"ETH")]
  (unified-api-contracts/.../cefi_margin_tiers.py). The tier-miss fallback (margin_model.py:196-198) then sets tier_mmr
  = mmr_warning_pct (e.g. 70 for BINANCE_CROSS) AS IF it were the position's real MMR rate — a self-referential fallback
  that makes usage_pct land at/above the warning threshold for almost any non-trivial position, regardless of actual
  risk. This affects every live CeFi margin computation through CefiVenueBalanceReader (both the pre-existing
  margin_health.py read path and the new emit_live_cefi_margin_events push path) — not introduced by this session, but
  newly surfaced by its tests.
status: resolved
nature: issue
asset_group: [cefi]
stage: [strategy]
repos: [unified-trading-library, unified-api-contracts, strategy-service]
scope: [engineer]
tags: [cefi, margin, risk, correctness, bug]
related:
  [
    /plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-28"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
source:
  "slot-10, 2026-07-27, discovered while testing emit_live_cefi_margin_events
  (capability_wizard_gap_discovery_2026_06_11.md P1 todo)"
resolved_by: unified-trading-library@3b13b69e, unified-trading-library@71970a2f
locked_by:
locked_since:
depends_on: []
---

# CeFi margin model misclassifies healthy positions as WARNING (hyphenated instrument-id parsing bug)

## What I found

`_CefiMarginModelBase.compute()`
(`unified-trading-library/unified_trading_library/margin_and_liquidation/margin_model.py:190-203`) extracts the base
asset from an instrument id to look up its maintenance-margin tier:

```python
asset = inst_id.split(":")[0].upper() if ":" in inst_id else inst_id.upper()   # line 193
...
tier_mmr = maintenance_margin_for(self._venue_slug, asset, notional)           # line 195
if tier_mmr is None:
    tier_mmr = self.params().mmr_warning_pct or Decimal("0.05")               # line 197
    tier_mmr = tier_mmr / Decimal("100") if tier_mmr > 1 else tier_mmr        # line 198
```

This only strips a **colon**-delimited prefix. But `AccountQueryClient` (strategy-service) and its real per-venue mock
data return **hyphenated** instrument ids — `"BTC-USD-PERP"`, `"ETH-USD-PERP"`
(`strategy_service/position/core/account_query_client.py:252,258`) — and `CefiVenueBalanceReader.build_portfolio` passes
that exact string straight through as the `PortfolioInputs` instrument id
(`strategy_service/position/core/venue_balance_tracker.py:689`). For a hyphenated id, `":" in inst_id` is `False`, so
`asset` becomes the **entire mangled string** (`"BTC-USD-PERP"`), which never matches
`CEFI_MARGIN_TIERS[(venue, "BTC")]` / `[(venue, "ETH")]`
(`unified-api-contracts/unified_api_contracts/registry/cefi_margin_tiers.py` — `get_margin_schedule` does an exact
`(venue.lower(), asset.upper())` dict lookup). `maintenance_margin_for` returns `None`, every time, for every real CeFi
position.

The fallback (line 197-198) then sets `tier_mmr = mmr_warning_pct` (e.g. `Decimal("70")` for `BINANCE_CROSS`,
`unified-api-contracts/unified_api_contracts/internal/risk.py:814`) **as if it were the tier's actual MMR rate**,
converted to a fraction (`70/100 = 0.7`). This is a 70%-of-notional "maintenance margin" — wildly larger than any real
tier (0.4%-50% across the configured schedules, overwhelmingly small for realistic notional sizes). The result:
`usage_pct = (notional * 0.7) / equity

- 100` lands at or above the venue's own warning threshold for almost any position with material size, **regardless of
  actual risk**.

Measured: a $40,000 BTC position with $1,000 debt (real margin usage ~2.5%, comfortably healthy) via a hyphenated
instrument id computes `usage_pct ≈ 71.8%` → graded `WARNING` (threshold 70) for `BINANCE_CROSS`. The identical position
with a colon-delimited id (`"BTC:PERP:USDT"`) resolves the real Binance BTC tier-1 MMR (0.4%) and correctly grades
`INFO` (~0.4% usage).

## Why it matters

Both live consumers of `CefiVenueBalanceReader` are affected, unconditionally, for every real venue position:

- `strategy_service/position/api/margin_health.py` (`compute_live_cefi_snapshots` / `get_margin_health`) — the existing
  pull-based margin-health query API.
- `strategy_service/position/core/venue_balance_tracker.py::emit_live_cefi_margin_events` — the new push path this
  session added, which now pushes a `MarginEvent` to `alerting-service` / `risk-and-exposure-service` on every non-INFO
  grade.

Since the bug pushes classifications toward WARNING/CRITICAL regardless of real risk, the practical failure mode is
**false-positive margin alerts** (noise, alert fatigue, possible unnecessary deleveraging if anything automated reacts
to `MarginEvent.margin_severity`) rather than a missed real breach — but a mis-scaled tier could in principle also
under-count risk for some notional/threshold combinations, so this should not be assumed safe-by-default in either
direction.

## Why I didn't fix it inline

- **Two independent design decisions, not a mechanical fix**: (1) should the asset-extraction accept both colon- and
  hyphen-delimited instrument ids (and any other venue-adapter shape), or should `AccountQueryClient`/UPI adapters be
  changed to always emit colon-delimited ids (a much larger, cross-cutting rename with unknown fan-out to other
  consumers of `ExchangePositionDict.instrument`)? (2) the fallback's use of `mmr_warning_pct` as a stand-in MMR rate
  needs a real default (e.g. a fixed conservative tier-0 rate per venue), not just a parsing fix — even a
  correctly-parsed UNLISTED asset (anything beyond BTC/ETH) hits the same fallback today.
- **Outside this task's scope**: `capability_wizard_gap_discovery_2026_06_11.md`'s P1 todo is "wire live balances into
  the emitter" (done) — not "fix the margin-tier resolution formula," a pre-existing gap in
  `unified-trading-library`/`unified-api-contracts` this session doesn't own.
- **Not obviously a "≤30 min" outside-plan fix**: touches 2 other repos' shared margin-model library code (consumed by
  strategy-service, risk-and-exposure-service, and any other margin-model caller), so a fix needs its own review, not a
  drive-by patch bundled into an unrelated commit.

## Recommended decision / Open work

- [x] 1. ✅ [BACKEND] P1. **Fix the asset-symbol extraction** in `_CefiMarginModelBase.compute()`
      (`unified-trading-library/unified_trading_library/margin_and_liquidation/margin_model.py:193`) to also handle
      hyphen-delimited instrument ids (e.g. take the first `-`-or-`:`-delimited segment, or add a shared canonical
      instrument-id parser if one already exists elsewhere in UAC/UTL — check before inventing a new one). Repo:
      unified-trading-library. Add a regression test asserting `"BTC-USD-PERP"` and `"BTC:PERP:USDT"` both resolve
      `asset="BTC"`. — unified-trading-library@3b13b69e. Checked `unified_trading_library/ml/models.py`'s
      `extract_base_asset()` first — it expects a different 3-part `VENUE:TYPE:BASE-QUOTE` shape and returns `None` for
      both our inputs, so it wasn't reusable; used `re.split(r"[:-]", inst_id, maxsplit=1)[0]` instead. Added
      `test_cefi_hyphenated_instrument_id_resolves_same_tier_as_colon` asserting `"BTC-USD-PERP"` and `"BTC:PERP:USDT"`
      compute identical `usage_pct` and both grade `OK`. Full quality-gates.sh green.
- [x] 2. ✅ [BACKEND] P1. **Replace the `mmr_warning_pct`-as-MMR-rate fallback**
      (`unified-trading-library/unified_trading_library/margin_and_liquidation/margin_model.py:196-198`) with a real
      conservative default MMR (e.g. the venue's own worst-case/highest configured tier rate, or a small fixed
      conservative constant like 1-2%) — never the warning _threshold_ itself, which guarantees near-warning-band
      results for any unresolved asset. Repo: unified-trading-library. Cross-check against
      `unified-api-contracts/.../cefi_margin_tiers.py`'s documented venues to confirm BTC/ETH are the only ones with
      real tiers today (any other asset hits this same fallback even once todo 1 lands). —
      unified-trading-library@71970a2f. Cross-checked `CEFI_MARGIN_TIERS`: only
      `("<venue>", "BTC")`/`("<venue>",     "ETH")` entries exist across binance/bybit/okx/deribit/hyperliquid/aster —
      every other asset, on every venue, hits the fallback. Chose the small fixed conservative constant (2%) over the
      venue's worst-case/highest tier rate: the highest tiers (25-50%) only apply at very large notional and would
      reproduce the same near-warning-band overshoot for typical positions the bug report flagged; 2% sits at the upper
      end of the tier-1 (smallest-notional) MMR rates actually observed across every configured venue/asset (0.4%-2%),
      so an unresolved asset is now treated like a typical small-tier position instead of an assumed near-liquidation
      one. Added `_DEFAULT_UNLISTED_ASSET_MMR` constant + regression test asserting a $40k/$1k-debt position with an
      unresolved asset (`SOL-USD-PERP`) now grades `OK` (~2.05% usage) instead of `WARNING` (~71.8%). Full
      quality-gates.sh green.
- [x] 3. ✅ [BACKEND] P2. **Audit whether any live/paper trading already ran through this path** since the
      margin-cluster remediation shipped (2026-06-15) — if `margin_health.py`'s live query API or alerting-service has
      actually consumed a misclassified `MarginEvent`/`MarginHealthSnapshot` in production, note it for the operator
      (informational — no automated recovery action without a human decision on backfill/notification). Repo:
      strategy-service + alerting-service. — **Verdict: no live/paper trading was exposed.** Evidence (all UTC, via
      `git log`/`git show -s --format=%ai`): - **Pull path** (`margin_health.py`'s
      `compute_live_cefi_snapshots`/`get_margin_health`, added strategy-service@b9b26433, 2026-06-15 14:04:35) has
      **zero callers anywhere in the codebase** outside its own tests — not wired to any FastAPI route
      (`position/api/routes/*.py`), CLI handler, scheduler, or UI; `grep -rln "get_margin_health"` workspace-wide hits
      only the two test files. It's a live-compute function with no persistence layer (its own docstring: "no GCS read —
      that is the Phase-2 historical layer"), so it never wrote a `MarginHealthSnapshot` anywhere. - **Push path**
      (`emit_live_cefi_margin_events`, `venue_balance_tracker.py:704`, wired into `cli/handlers/monitor_handler.py:95`
      reachable only via `--operation monitor --mode live`) did not exist until strategy-service@3c14639d, 2026-07-27
      13:24:45 — the **first-ever** production caller of `emit_margin_event_for_cefi` (confirmed via
      `grep -rn "emit_margin_event_for_cefi("` outside tests). That same commit's message already flags the
      hyphenated-id bug. The two fix commits (unified-trading-library@3b13b69e 13:57:56, @71970a2f 14:24:19) landed
      33–60 min later, same session. No evidence in this checkout of an actually-deployed `--mode live` monitor process
      invoking the emitter in that narrow window (no Cloud Run/VM deployment-log access from this sandbox). -
      `MarginEvent` (`unified-api-contracts/.../inter_service_events.py:90`) has no found GCS/BigQuery/Firestore sink in
      this repo checkout — it flows transport→alerting-service rules, not into a queryable historical table. **For the
      operator**: if independent confirmation is wanted, check alerting-service Cloud Logging for `MarginEvent` with
      `venue_type=cefi` + grade WARNING/CRITICAL between 2026-06-15 and 2026-07-27 14:24 UTC (or the `margin-events`
      Pub/Sub topic's subscription metrics for that window) — strong prior is this is empty, since no code path
      published such events before 2026-07-27 13:24:45. - The underlying parsing bug itself predates the margin-cluster
      commit (present since unified-trading-library@cbe74911/@117261fd, 2026-05-01) but was inert until the push path
      existed — caught same-session before any real exposure, not "ran live for weeks with bad data."
