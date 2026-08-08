---
doc_type: plan
title:
  TRADFI mbp_10 / corporate_action_confirmed / earnings_result / Yahoo-Finance-CBOE-treasury history (2026-07-15
  through 2026-07-31, extracted from the mbp10/ohlcv-coarse-calendar issue doc)
summary: >-
  Line-cap remediation extraction from
  plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md's "Resolution —
  mbp_10", "Resolution — corporate_action_confirmed / earnings_result", "Verdict — Yahoo Finance source-vs-venue
  investigation", "Resolution — CBOE US Treasury-yield tenors routing", "Resolution — YAHOO_FINANCE phantom-venue
  seeding stopped + orphan rows cleaned" sections plus their corresponding Progress Log entries, moved verbatim so the
  live doc stays under the 500-line soft cap. All 5 findings this history covers (mbp_10, corporate_action_confirmed,
  earnings_result, the Yahoo-source/CBOE-venue investigation, the YAHOO_FINANCE phantom-venue cleanup) are FULLY CLOSED
  and unrelated to the source doc's sole remaining open todo (the ohlcv_15m/ohlcv_24h MDPS-owned aggregation build,
  2026-08-07 ruling) — no currently-open todo depends on this narrative. The source doc's still-relevant
  "Resolution — ohlcv_15m/ohlcv_24h audit" and "Verification addendum" sections were deliberately LEFT IN PLACE (not
  extracted) because the open todo's context depends on them.
status: complete
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service, features-service]
scope: [engineer, admin]
tags:
  [
    tradfi,
    databento,
    mbp_10,
    corporate_action_confirmed,
    earnings_result,
    yahoo_finance,
    cboe,
    history,
    line-cap-remediation,
  ]
related:
  [/plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "line-cap remediation extraction, 2026-08-08, per
    plans/active/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md todo 1"
---

# TRADFI mbp_10 / corporate_action_confirmed / earnings_result / Yahoo-Finance-CBOE-treasury history

Extracted verbatim from
`plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` on 2026-08-08,
to bring the live doc back under the workspace's 500-line soft cap
(`scripts/plan-hygiene/check_line_caps.sh`). No content changed — only relocated. The live doc's own `## Open work
(tracked todos)` checklist (unchanged, all checkbox text preserved) is the authoritative decision/evidence-SHA record
for these 5 findings; this file is the full narrative trail behind those checkboxes and their Progress Log entries —
read it only if a deeper citation on a specific finding's reasoning is needed.

## Resolution — mbp_10 (2026-07-15)

Fixed the mechanical adapter-wiring gap exactly as recommended: `market-tick-data-service@e2018167` adds `"mbp_10"` to
`_DATABENTO_SUPPORTED_DATA_TYPES` (`umi_tick_provider.py:143`).

**Fetch path verified genuinely end-to-end before shipping** (not just the schema-map line cited in the original
diagnosis) — read `databento_fetch.py` in full: `_resolve_databento_schema` maps `mbp_10` → `db.Schema.MBP_10` AND calls
UAC's `assert_schema_allowed("mbp_10")`, which passes (`mbp-10` is in `ALLOWED_DATABENTO_SCHEMAS`, billing level L2, not
in the banned-OHLCV set). Downstream, `_fetch_timeseries_range` calls
`assert_databento_request_allowed(dataset, schema, start)` — dataset `GLBX.MDP3` (CME) is in
`ALLOWED_DATABENTO_DATASETS`, and the L2 30-day free-lookback window is enforced (`LEVEL_MAX_LOOKBACK_DAYS["L2"] = 30`).
So a real, correctly-billing-gated Databento request now flows for any `mbp_10` request that reaches `_route_databento`
— no further gap in the fetch mechanics themselves.

**Important scope caveat found during this pass (not identified in the original diagnosis) — my fix alone does NOT yet
cause CME `mbp_10` capture to start flowing in production.** `venue_fetch.py`'s per-shard dispatch (lines ~444-459)
intersects EVERY `data_types` request — both the default path and any explicit `--data-types` CLI override — against
`get_expected_data_types_for_venue("CME")` (UAC, backed by `VENUE_DATA_TYPE_CAPABILITIES`) BEFORE it ever reaches
`fetch_tick_data_for_venue`/`_route_databento`. As of this fix, `VENUE_DATA_TYPE_CAPABILITIES["CME"]` in UAC's
`market_data_categories.py` only declares `{"ohlcv_1s", "ohlcv_1m"}` — the 2026-05-15 "OHLCV-only MVP" operator scope
(`tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`). `trades`/`tbbo`/`mbp_10` were deliberately deferred to a named
successor plan, `plans/archive/2026_05/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` — archived
`status: complete`, but its own body shows Phases 1-2 (the actual `VENUE_DATA_TYPE_CAPABILITIES` re-merge) marked
`[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]` and migrated to the `tradfi_master` epic, gated on an operator Databento
PAYG-spend sign-off (its own Phase 8) — i.e. the registry-level restoration was never actually re-applied to UAC. One
sub-item of that same plan (Phase 6 P1, "Add `mbp_10` to MTDS DatabentoAdapter supported schemas") carries real evidence
(`uac@9f8373f + mtds@020442b`) but only the lower `_resolve_databento_schema` mapping shipped then — the
`umi_tick_provider.py` pre-flight allowlist this issue's finding (1) named was never actually fixed until today, despite
that plan's checkbox reading ✅. **So**: this fix completes the adapter-layer half of that stalled 2026-06 restoration
and is correct/necessary regardless of what happens next, but a live default or explicit-`--data-types` MTDS
orchestrator run for CME will still filter `mbp_10` out at the UAC-intersection step in `venue_fetch.py` until
`VENUE_DATA_TYPE_CAPABILITIES["CME"]` is separately restored — that registry change is UAC-repo, operator-PAYG-gated,
and out of this task's scope (touch only `market-tick-data-service` per this issue's brief). **Flagging for whoever
picks up `tradfi_master`'s post-cutover residual**: re-running `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`
Phases 1-2 against current UAC would fully close the loop this fix opened.

This also means the historical 1186/1186 100% `attempted_failed` `mbp_10` manifest rows the alert batch surfaced are
most likely a fixed historical count (residue from before the 2026-05-15 MVP narrowing, or from whatever partial
pre-narrowing live run originally hit the fetch path) rather than actively-growing — not independently re-verified
against a live manifest query in this pass (would require the P3 VERIFY trace below).


## Resolution — corporate_action_confirmed / earnings_result (2026-07-15)

Fixed exactly as scoped in the dispatch: `instruments-service/scripts/enumerate_expected_universe.py` is confirmed
(re-verified fresh, not just trusted from the original diagnosis) to be the ONLY seeding site — its `enumerate_v2()`
default-resolution branch and `main()`'s CLI-default branch both resolved TRADFI's `data_types` list from UAC
`DATA_TYPES_BY_ASSET_GROUP["tradfi"]` unfiltered, which is what fed both the per-instrument lifecycle pass
(`_enumerate_v2_tradfi`) and the venue-grain non-trading-day pass (`_yield_v2_tradfi_non_trading_day_rows`) — i.e. every
row class this enumerator seeds into the MTDS tick manifest for tradfi.

**Scope precision (the exact risk the dispatch flagged):** `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` itself is a UAC
cross-cutting registry consumed by several OTHER modules unrelated to MTDS (`market_data_categories.py` validity
matrices, `expected_coverage.py`, `mvp_scope.py`, `scripts/generate_ui_reference_data.py`, …) — editing it directly
would have de-registered `corporate_action_confirmed`/`earnings_result` as valid tradfi data_types system-wide,
including for whatever features-service's own manifest tracking eventually wants to do with that same "what data_types
are expected" knowledge. **Did not touch UAC.** Instead added a new tradfi-only helper,
`_tradfi_mtds_tick_manifest_data_types()` (+ `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` frozenset), and wired it
into the two `data_types` resolution sites in place of the raw `DATA_TYPES_BY_ASSET_GROUP.get("tradfi", [])` call — a
narrow, two-item exclusion scoped to this ONE enumerator's MTDS-tick-manifest seeding path only. UAC's registry is
regression-tested to remain untouched (`test_uac_data_types_by_asset_group_registry_itself_is_untouched`).

**Regression tests** (`tests/unit/scripts/test_enumerate_expected_universe_v2.py`, new
`TestTradfiMtdsTickManifestDataTypeExclusion` class, 4 tests): both types are confirmed present in UAC's registry
(fixture sanity-check, so the test isn't trivially-passing for the wrong reason); the new helper excludes exactly these
two and nothing else; `enumerate_v2(asset_group="tradfi")`'s default-resolution path (no explicit `--data-types`
override — the production default, mirroring `main()`'s CLI default) never emits either data_type across an
EQUITY@NASDAQ fixture (deliberately chosen because the G1-ENUM validity matrix already considers both VALID for that
shape, so the test actually exercises the exclusion rather than passing for an unrelated reason); UAC's own registry
constant is unchanged. Full suite: 165 tests passed in the touched test file, 14/14 golden-fixture tests passed,
`quality-gates.sh --no-fix` ALL PASSED (177s). Shipped `instruments-service@03f71c81`.

**Unrelated blocker hit + resolved while shipping**: the local `quality-gates.sh` run was red on
`test_expected_universe_golden.py::test_expected_matches_golden[tradfi]` for a reason wholly unrelated to this fix
(verified via a stash-isolated re-run: byte-identical failure with my diff stashed out) — a concurrent agent's
in-flight, uncommitted UAC edit (`unified-api-contracts@78b9e899`, the CBOE `ohlcv_15m` narrowing = this same doc's
finding (2), see the resolution section above) was live via the editable path-dependency, and once it landed as a commit
the checked-in `tradfi.json` golden fixture needed a resync. Waited for UAC to go clean, then regenerated ONLY the
tradfi golden via the sanctioned `scripts/regenerate_expected_universe_golden.py` (refuses while UAC/UTL are dirty — ran
only after confirming both clean) and reverted the script's unwanted cefi/defi/sports/prediction.json touches (pure
`json.dumps` formatting noise vs. the checked-in prettier-compacted style, zero content delta — those 4 asset_groups
were already passing) back to HEAD; prettier-formatted the tradfi fixture to match the checked-in convention so the
shipped diff is the true minimal 3-line delta (`captured_at`, `tuple_count` 41→40, removed
`["CBOE", "index", "ohlcv_15m"]`). Included in the same `instruments-service@03f71c81` commit since it was required to
get MY tradfi-scoped test green — did not touch any other finding's logic.

**Historical already-seeded rows — ✅ DONE 2026-07-28 (slot-7, data_engineering), the deferred follow-up below.**
Originally deferred (decision: defer, do not touch in this pass) — the alert batch's own numbers (807/807
`corporate_action_confirmed`, 799/799 `earnings_result`, both against `market-data-tick-tradfi-prd`) were the only
counts available at the time; not independently re-verified against a live manifest query in this pass. Considered
cleaning these up then (mirroring the cefi-orphan-rows precedent elsewhere in this remediation wave) but chose to leave
them as a documented follow-up rather than force it, for the same reason the `mbp_10` resolution above did: this is
PRODUCTION DATA MUTATION (deleting/reclassifying live manifest rows) that deserves its own carefully-scoped pass —
precisely identifying the predicate, picking the sanctioned rewrite mechanism (this repo has several
`reconcile_*`/`purge_*`/ `delete_phantom_rows_from_shards.py`-style precedents for exactly this shape of cleanup), a
scan-only dry run, and review — not something to bolt onto a code-scoping fix under the same commit.

**Resolution (2026-07-28, `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` todo,
`market-tick-data-service@c24db4cf`).** Re-querying the live manifest ahead of the cleanup found the 807/799 figures
badly stale — the alert batch had only ever counted the narrower `attempted_failed` slice of a much larger
already-misclassified population: **420,803 rows** in `_index/availability_index.parquet` (`corporate_action_confirmed`
210,446 + `earnings_result` 210,357, all `empty_confirmed`/`expected_unattempted`, **0 `attempted_failed`, 0
`captured`**) and **7,540 rows** in `_index/expected_universe_ranges.parquet`. STOP-ON-SURPRISE cleared (0 `captured`
rows for either data_type — no real data would be lost). Followed the exact snapshot / STOP-ON-SURPRISE /
predicate-filter / write-back / verify-HOLD playbook already used for the YAHOO_FINANCE phantom-venue cleanup above,
plus a fresh same-run `gcs_bucket_soft_delete_retention_seconds()` check (604800s, qualifies per delete-safety codex
§3a) ahead of the overwrite: paused `uts-prod-manifest-consolidator-market-data-tradfi-cron`, snapshotted both files to
`_index/snapshots/`, deleted all target rows from both, verified 0 residual rows in both immediately after write,
resumed the scheduler, then proved HOLD across **6 real consolidator merge cycles** (target rows stayed 0 every check —
no resurrection). Scripts:
`market-tick-data-service/scripts/{query,delete}_tradfi_corporate_action_earnings_orphans_2026_07_28.py`. The
`corporate_action_confirmed`/`earnings_result` follow-up flagged to
`macro_micro_econ_data_capture_audit_2026_06_05.md`'s owner (measuring this data correctly in features-service's own
manifest) remains open and OUT OF SCOPE for this cleanup — this resolution only removes the misclassified MTDS-side
rows.

## Verdict — Yahoo Finance source-vs-venue investigation (2026-07-15, operator-directed re-check)

**Background**: an earlier pass this session (finding (C) above) framed `"YAHOO_FINANCE"` as a "phantom `NO_ADAPTER_YET`
venue... likely the DOMINANT contributor" to the `ohlcv_15m`/`ohlcv_24h` failure counts (later corrected by the
Verification addendum: NYSE/CBOE dominate `ohlcv_15m`, YAHOO_FINANCE is real-but-not-dominant for `ohlcv_24h`). The
operator (interactive session, 2026-07-15) pushed back on the "no adapter" framing itself: Yahoo Finance is a real,
intended DATA SOURCE already used for DXY, US treasuries, and KRW/USD daily OHLCV — the registry conflates "venue" with
"source" and should be corrected to reflect reality, not treated as a missing-adapter gap. Dispatched to re-investigate
for real rather than take either side's framing at face value. **Full workspace grep** (`yfinance`, `Yahoo`,
`YAHOO_FINANCE` across market-tick-data-service, instruments-service, features-service, market-data-processing-service,
unified-api-contracts) plus direct reads, not assumed.

**Verdict: (c) — partially correct on both sides, more nuanced than either framing.** The operator is RIGHT that Yahoo
Finance is a real, live, precedented data SOURCE and that the registry conflates source with venue — but WRONG that all
3 named instrument classes are "already the way". 2 of 3 already work; 1 of 3 is a genuine, never-built gap.

**(1) DXY — WORKING (operator correct).**
`market-tick-data-service/market_tick_data_service/market_interface/adapters/ tradfi/yahoo_finance_adapter.py`
(`YahooFinanceAdapter`, 361 lines, live `yfinance`-backed) is registered in `factory.py:153`
(`"yahoo_finance": ("tradfi", YahooFinanceAdapter)`) and is called by
`market_tick_data_service/adapters/_umi_yahoo.py::fetch_yahoo_indices("ICE", ...)`, itself dispatched from
`umi_tick_provider.py`'s `route_yahoo_tradfi()` for `venue_upper == "ICE"`. DXY ticker `DX-Y.NYB` is registered in UAC's
`YAHOO_INDICES` (`tradfi_instrument_universe.py:511`, `YahooIndexDef("DXY", "ICE", "DXY", "DX-Y.NYB", ...)`). This path
was wired 2026-07-13 (`tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`) — real, tested, live.

**(2) KRW/USD — WORKING (operator correct).** `FX_SPOT_PAIRS` (UAC `tradfi_instrument_universe.py:430`,
`FxSpotPairDef("KRW", "USD", "KRWUSD=X")`, comment: "for kimchi-premium basis computation") is fetched by
`_umi_yahoo.py::fetch_yahoo_fx()`, dispatched from `route_yahoo_tradfi()` for `venue_upper == "FX"`. Live, tested.

**(3) US Treasuries — NOT WORKING, genuine gap (operator's belief is wrong here, though the intent is real and declared
everywhere else).** The CBOE fixed-income tenors (`US3M`/`US2Y`/`US5Y`/`US10Y`/`US30Y` — tickers
`^IRX`/`2YY=F`/`^FVX`/`^TNX`/`^TYX`) ARE registered in `YAHOO_INDICES` (`tradfi_instrument_universe.py:521-525`, venue
tagged `"CBOE"`), AND the intent is independently declared in 3 more places: `SOURCE_PRIORITY`
(`_source_priority_data.py:328-331`: `("tradfi", "ohlcv_24h"): ["yahoo"]`, comment "FX KRW/USD, KRX single stocks, the
DXY + treasury-yield indices"), the per-instrument `data_source_continuity.py` (`get_us_treasury_yield_daily_source()`
returns the string `"YAHOO_FINANCE"` for covered dates, and
`get_source_for_instrument("CBOE:INDEX:US10Y-USD", "ohlcv_24h", ...)` resolves through it — regression-tested in
`test_yahoo_indices_and_dxy_source.py:97-116`), and
`features-service/features_service/volatility/calculators/treasury_yields_calculator.py` (a pure formula module awaiting
a `yields_daily` DataFrame with `us3m`/`us5y`/`us10y`/`us30y` columns — no fetch/loader code for it exists anywhere in
features-service). **But `route_yahoo_tradfi()`'s venue tuple is `("FX", "KRX", "ICE")` — `"CBOE"` was never added**, so
`fetch_yahoo_indices("CBOE", ...)` (a function whose own docstring anticipates exactly this: "reusable for other
YAHOO_INDICES venues (CBOE tenors, KRX KOSPI/KOSPI200) without a new copy, though only ICE calls it today") is never
invoked in production. This is confirmed independently missing from `SOURCE_PRIORITY`'s own comment describing CBOE's
Databento-only role for `ohlcv_1s`, and from `expected_coverage.py:173`, `"CBOE": ["ohlcv_1s", "ohlcv_1m"]` — no
`ohlcv_24h` entry at all for CBOE, so even if the fetch route existed, `venue_fetch.py`'s per-shard UAC-intersection
would filter the request out before it reached routing (the same 2-layer gating shape as the `mbp_10` finding above).

**Why not a mechanical one-line fix (unlike the ICE DXY precedent)**: naively adding `"CBOE"` to `route_yahoo_tradfi`'s
tuple is UNSAFE — CBOE already routes live VX-futures `ohlcv_1s`/`ohlcv_1m` through Databento via the SAME dispatch
chain (this function sits upstream of the Databento fallthrough in `umi_tick_provider.py`). The function's current
all-or-nothing per-venue branch (`if data_types and "ohlcv_24h" not in data_types: return pd.DataFrame()`) would
short-circuit any non-`ohlcv_24h` CBOE request straight to an empty frame instead of falling through to Databento below
it — silently breaking live VX-futures capture, a real, actively-used, high-value feed. A correct fix needs
instrument-type-aware (index vs future) or explicit-data_type routing, not a blind tuple addition. **Not built here** —
flagged as a new scoped todo above rather than rushed under this investigation's time-box.

**On the "phantom venue" registry-modeling question** (does `VENUE_DATA_TYPE_CAPABILITIES`/`expected_coverage.py`
structurally conflate venue with source): **yes, confirmed** — `"YAHOO_FINANCE"` is declared as a literal VENUE with its
own `ohlcv_15m`/`ohlcv_24h` expected-coverage entry that no fetch code ever satisfies (real Yahoo-sourced rows are
correctly stamped under venue=ICE/FX/KRX, source=yahoo — `data_source_continuity.py` already models this correctly as a
per-instrument SOURCE resolver returning the string `"YAHOO_FINANCE"`, a genuinely cleaner place than the venue-level
capability dicts). `instruments-service` already partially corrects for this on its OWN producer path
(`_TRADFI_NON_VENUE_KEYS` excludes `"YAHOO_FINANCE"` from `get_venues_for_asset_groups`, `venue_core.py:164`) — the
UAC-registry-level capability/expected-coverage entries were simply never brought into line with that same exclusion.
**Not blind-fixed here either**: `get_expected_data_types_for_venue()` (`market_data_categories.py:1881-1884`) falls
through to a blanket ALL-10-tradfi-datatypes list whenever a venue's capability dict is empty or absent — the exact
footgun `test_data_status_registries.py`'s KRX docstring already documents for a different venue. Naively deleting the
`YAHOO_FINANCE` capability entries would turn a 2-datatype phantom into a WORSE 10-datatype one. The correct fix is
almost certainly a manifest-SEEDING-site exclusion (mirroring the `_tradfi_mtds_tick_manifest_data_types()` pattern
already shipped for `corporate_action_confirmed`/`earnings_result` in this same doc), not a raw UAC registry deletion —
flagged as the corrected version of the pre-existing todo above, still open, still needs its own scoped pass.

**Bottom line**: the operator's core architectural claim (Yahoo Finance is a real source, modeled at the wrong layer) is
correct and evidenced. The specific factual claim ("we get... us treasuries... from there") is not currently true in
production — the registry/intent layers all agree it SHOULD be, but no fetch code path exists for it. No code shipped by
this pass (both candidate fixes carry real regression/footgun risk that deserves its own careful, tested pass, not a
rushed change under this investigation's scope) — this section replaces the "phantom venue, no adapter, likely dominant
contributor" framing with the evidence-backed picture above; the original framing is left in place above (not deleted)
per this workspace's correct-don't-silently-rewrite convention.

## Resolution — CBOE US Treasury-yield tenors routing (2026-07-15)

Fixed the MTDS-side routing gap exactly as scoped: `market-tick-data-service@764e7170` makes `route_yahoo_tradfi()`
(`market_tick_data_service/adapters/_umi_yahoo.py`) discriminate CBOE requests by `data_type` instead of a blanket
venue-level flip, per this doc's own "do not naively add CBOE to that tuple" warning above.

**The discriminator (file:line)**: `_umi_yahoo.py:300`, a new
`_CBOE_YAHOO_TREASURY_DATA_TYPES: frozenset[str] = frozenset({"ohlcv_24h"})` constant, consumed at
`_umi_yahoo.py:325-329` inside `route_yahoo_tradfi()`:

```python
if venue_upper == "CBOE":
    if data_types and set(data_types) <= _CBOE_YAHOO_TREASURY_DATA_TYPES:
        return await fetch_yahoo_indices("CBOE", date=date, writer=writer, failed_per_instrument=failed_per_instrument)
    return None
```

CBOE is handled as a case SEPARATE from the pre-existing FX/KRX/ICE blanket-venue tuple (which is untouched). The
discriminator is `data_types`: only when the caller's requested `data_types` is explicitly non-empty AND is an exact
subset of `{"ohlcv_24h"}` (Yahoo's only servable granularity here, and the one granularity CBOE's Databento VX-futures
path never serves) does the request route to `fetch_yahoo_indices("CBOE", ...)` — which internally filters UAC's
`YAHOO_INDICES` registry to `venue == "CBOE"`, naturally resolving to exactly the 5 Treasury tenors (US3M/US2Y/US5Y/
US10Y/US30Y) with no separate ticker allowlist needed in MTDS. Every other shape — `data_types=None` (the
default/no-override production path), or `data_types` containing any Databento data_type (`ohlcv_1s`, `ohlcv_1m`,
`trades`, `tbbo`, `mbp_10`, or a mix including `ohlcv_24h`) — returns `None` from this branch, so
`fetch_tick_data_for_venue`'s dispatch chain (`umi_tick_provider.py:637-659`) falls through UNCHANGED to the existing
`_route_massive`/`_route_databento` path (CBOE is in `_umi_massive.MASSIVE_INCAPABLE_VENUES`, so it always lands on
`_route_databento` specifically, exactly as before this fix).

**Regression tests** (`tests/unit/test_umi_tick_provider_routes.py`, new `TestYahooCboeTreasuryRouting` class, 4 tests)
— both halves the dispatching task required, plus 2 more:

1. `test_cboe_ohlcv24h_routes_to_yahoo_treasury_tenors` — **(a) proves the fix**: `venue=CBOE, data_types=["ohlcv_24h"]`
   now reaches `fetch_yahoo_indices("CBOE", ...)`.
2. `test_cboe_vx_futures_data_types_still_reach_databento` — **(b) THE regression-proving test**:
   `venue=CBOE, data_types=["ohlcv_1s"]` and `["ohlcv_1m"]` (VX-futures shapes) both still reach
   `DatabentoAdapter.download_batch_df` unaffected, and the Yahoo fetch (`fetch_yahoo_indices`) is asserted `not_called`
   — proves neither side broke the other.
3. `test_cboe_default_data_types_none_still_falls_through_to_databento` — `data_types=None` (the production default
   shape) still falls through to Databento exactly as pre-fix, confirming CBOE does NOT get the FX/KRX/ICE
   default-to-Yahoo behavior.
4. `test_cboe_mixed_data_types_including_databento_type_falls_through` — a mixed request (`["ohlcv_24h", "ohlcv_1m"]`)
   is not an exact subset of `{"ohlcv_24h"}`, so it correctly falls through rather than silently serving only the Yahoo
   half.

All 4 new tests pass; full existing `test_umi_tick_provider_routes.py` suite (including `TestYahooFxRouting`,
`TestYahooKrxRouting`, `TestYahooIceRouting`, `TestDatabentoRouting`) and the full repo `quality-gates.sh --no-fix` both
green (sentinel `.qg_last_passed_sha` verified == HEAD before shipping).

**Scope caveat (mirrors the mbp_10/CME precedent above)**: this fix alone does NOT yet cause live CBOE Treasury-yield
capture to start flowing in production. `venue_fetch.py`'s per-shard UAC-intersection step filters every `data_types`
request against `get_expected_data_types_for_venue("CBOE")` BEFORE it reaches this routing code, and UAC's
`VENUE_DATA_TYPE_CAPABILITIES["CBOE"]`/`expected_coverage.py` currently declare only `{"ohlcv_1s", "ohlcv_1m"}` — no
`ohlcv_24h` entry — so a live/default orchestrator run for CBOE still never constructs an `ohlcv_24h` request in the
first place. **Deliberately not touched here** — out of this task's scope (touch only market-tick-data-service per the
dispatch), and per this doc's own warning about `get_expected_data_types_for_venue()`'s undocumented
fall-through-to-ALL-10-datatypes footgun on an EMPTY capability dict (CBOE's dict is non-empty, so a straightforward
addition should be safe, but it needs its own careful UAC-repo pass + QG run, not a bolt-on here). Filed as a new
`[DATA] P3` todo above (`unified-api-contracts`: add `ohlcv_24h` to CBOE's capability + expected-coverage entries).

## Resolution — YAHOO_FINANCE phantom-venue seeding stopped + orphan rows cleaned (2026-07-16)

Operationalized the `unified-api-contracts@fec3f110` YAHOO_FINANCE venue removal on real infra: **stop the nightly
re-seeding first, then clean the orphaned rows so they HOLD** (the ordering matters — a clean-first would have been
resurrected by the next nightly enum). All steps were live prod actions on GCP `central-element-323112`.

**The seeder (identified, not assumed).** `enumerate_expected_universe.py`'s `_yield_v2_tradfi_non_trading_day_rows`
walks `VENUES_BY_ASSET_GROUP["tradfi"]` and seeds `empty_confirmed` `EXPECTED_WEEKEND`/`EXPECTED_HOLIDAY` rows into the
MTDS tradfi tick manifest (`resolve_bucket_name(kind="market-data", asset_group="tradfi")` → `_index/…`). The nightly
runner is Cloud Run job **`expected-universe-v2-tradfi`**
(`MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-universe-v2-tradfi`, `--apply-write`), Cloud Scheduler
**`expected-universe-v2-tradfi-daily` = `30 1 * * *`** — matching the manifest's max `attempted_at` of
`2026-07-15T01:31:30Z`. `is-daily-enum-tradfi` (`30 13 * * *`) runs
`-m instruments_service --operation instruments --mode batch` (instrument-catalogue enumeration, a different bucket) and
does NOT seed the tick manifest — so it is NOT a YAHOO seeder. The catalogue jobs (`lifecycle-catalogue-*-tradfi`,
`build_instrument_catalogue.py`) write instruments-store, not the tick manifest.

**Big finding — the base bump `instruments-service@6d33b9d5` was premature.** It pinned UTL base `sha256:b7c57243`
(built `2026-07-15 17:54:46Z`), which had YAHOO removed but predated `unified-api-contracts@7754661a` (`18:14:29Z`, adds
`venue_data_type_has_batch_source`) that the current enumerator imports at module load — so an enum run on that image
died at `ImportError: cannot import name 'venue_data_type_has_batch_source' from 'unified_api_contracts'` (exec
`expected-universe-v2-tradfi-959bv` failed). Corrected by re-bumping the IS Dockerfile base to the newer UTL
`0.55.0/latest` `sha256:be51b33f` (built `23:27:01Z`), verified in-image to bundle all of {YAHOO removed, CBOE
`ohlcv_24h` declared, `venue_data_type_has_batch_source` present} via
`Evidence: cloudbuild=70dbc75f-c8db-4245-b3bb-fd175829f6b3` (SUCCESS). Shipped `instruments-service@3e5b1039` (QG-green,
quickmerge); built it `Evidence: cloudbuild=d00de7ec-8272-49d5-ab9d-f0ded059b0e6` (SUCCESS) → IS image digest
`sha256:d569a6548d4dde511a994c5e35f0dd043aa6f1b67c9375d1f51f3793bddee98d`; re-pinned `expected-universe-v2-tradfi` to
that digest (`gcloud run jobs update … --image <digest>`). (The `d00de7ec` build also restored a working `:latest`,
which an interim `b7c57243`-based build had transiently overwritten.)

**Seeding-stopped verification (deploy-first proof).** Executed `expected-universe-v2-tradfi` on the fixed image (exec
`expected-universe-v2-tradfi-lwsqs`, SUCCEEDED). Its fresh per-VM shard `_index/per_vm/enum-universe-v2-tradfi.parquet`
(written `23:09:34Z`) carried **5,709 rows, YAHOO_FINANCE = 0**, and still seeded the real tradfi venues (CME 2244 /
NYSE 1122 / NASDAQ 871 / ICE 368 / CBOE 368 / KRX 368 / FX 368). Post-consolidation the canonical index had **zero**
YAHOO rows with `attempted_at` after the run (max stayed `2026-07-15T01:31:30Z`).

**Cleanup (source-addressed).** Resurrection-surface audit: `_index/per_vm/_legacy_seed.parquet` (the permanent seed the
consolidator always merges) carried **0** YAHOO rows, so the only live YAHOO population was the canonical itself
(inherited from the pre-fix enum shard, since consumed+pruned). To avoid a write race with the every-minute consolidator
(`uts-prod-manifest-consolidator-market-data-tradfi`, DuckDB UNION-ALL merge of canonical + per-VM shards), the cleanup:
(a) paused scheduler `uts-prod-manifest-consolidator-market-data-tradfi-cron` and drained the in-flight run; (b)
snapshotted then deleted `venue==YAHOO_FINANCE` from **`_index/availability_index.parquet`** (11,676 → 0; 5,564,746 →
5,553,070 rows; breakdown 10,108 `EXPECTED_WEEKEND` + 737 `EXPECTED_HOLIDAY` `empty_confirmed` + 831
`attempted_failed`/`LegacyBlankErrorReasonError`) and **`_index/expected_universe_ranges.parquet`** (the honest-coverage
full-history denominator, which a `--start-date` enum run does NOT regenerate: 5,080 → 0; 63,514 → 58,434); (c) resumed
the scheduler. STOP-ON-SURPRISE guarded against deleting any `capture_status=="captured"` row (there were none — all
pure enumeration artifacts, consistent with "no live fetch writes venue=YAHOO_FINANCE"). Snapshots for rollback:
`_index/snapshots/pre_yahoo_phantom_venue_delete_20260715T231453Z_{availability_index,expected_universe_ranges}.parquet`.
Predicate/pattern mirrors `market-tick-data-service/scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py`
(download → STOP-ON-SURPRISE → snapshot → filter → write-back → verify gate). The deletion was run as a scoped
operational one-off (fully reproducible from the snapshots + this predicate); it was not committed to `scripts/` to
avoid entangling with two pre-existing, unrelated MTDS adapter-contract-baseline regressions
(`_onchain_perp_batch_live_only.py`, `solana_defi_drift.py`) that are outside this task.

**HOLD proven (not a point-in-time check).** After resume, forced one consolidator merge (exec
`…-market-data-tradfi-8txgh`, SUCCEEDED) then watched **≥5 real merge cycles** (canonical rewritten `23:17:55` →
`23:19:39` → `23:20:44` → `23:21:39` → `23:22:41Z`). Final state across every resurrection surface: canonical
`availability_index.parquet` YAHOO=0 (5,553,070 rows), `expected_universe_ranges.parquet` YAHOO=0 (58,434 rows),
`_legacy_seed.parquet` YAHOO=0 (18,149 rows). The rows are gone and stayed gone — no resurrection. Consolidator
scheduler confirmed `ENABLED` (not left paused); enum job confirmed pinned to the working digest.

**CBOE note (task sanity check).** UAC now declares CBOE `ohlcv_24h`: `VENUE_DATA_TYPE_CAPABILITIES["CBOE"]` contains
`ohlcv_24h` → `True` (confirmed both in the workspace UAC and inside the deployed base image), and `YAHOO_FINANCE` is no
longer a `VENUE_DATA_TYPE_CAPABILITIES` key (`False`). CBOE `ohlcv_24h` capture rides the MTDS image (already on the new
UAC) — no separate deploy needed here.


## Progress Log (extracted entries, chronological)

- 2026-07-15 (later same day): Finding (1) `mbp_10` fixed at the adapter layer — `market-tick-data-service@e2018167`.
  Verified the full Databento fetch mechanics (schema map + UAC subscription/billing allowlist) were already sound
  end-to-end; the pre-flight allowlist was the one remaining gap and is now closed, with a regression test class pinning
  the "registry-declared ⊆ adapter-supported" invariant so this drift class can't silently recur. Also discovered — NOT
  part of the original diagnosis — that UAC's `VENUE_DATA_TYPE_CAPABILITIES["CME"]` still scopes CME to
  `{ohlcv_1s, ohlcv_1m}` only (2026-05-15 OHLCV-only MVP), so this fix does not by itself cause live `mbp_10` capture to
  start; see "Resolution — mbp_10" above for the full trace and the already-existing (but stalled) successor plan that
  owns closing that gap. Findings (2) and (3) untouched — still open, still need the operator/architecture calls the
  recommendation section above describes.
- 2026-07-15 (operator decision, interactive reconciliation): presented the UAC-registry-restoration option ("restore
  `mbp_10` to `VENUE_DATA_TYPE_CAPABILITIES["CME"]` now, since the adapter-layer fix is shipped and tested") vs. leaving
  the 2026-05-15 MVP-scope restriction in place. **Operator chose to leave the restriction in place** — the scope
  narrowing is still deliberate, not stale. Reclassifying: the 1186/1186 historical `attempted_failed` `mbp_10` rows and
  the ongoing `DP_RUN_MOSTLY_EMPTY` alert for this cell should be treated as **expected-per-scope-decision**, not an
  open gap — this issue's finding (1) is closed at the adapter layer (correct, necessary, done) but the live-capture
  activation is explicitly NOT happening right now by operator choice, not by oversight. **Follow-up not yet done**:
  whether the manifest/alerting layer has a clean mechanism to mark an operator-scope-deferred cell as
  `expected_unattempted`-with-reason (vs. `attempted_failed`) so it stops presenting as an active failure in
  `DP_RUN_MOSTLY_EMPTY`'s ratio math — worth a small follow-up if this cell keeps contributing to future alert noise;
  not pursued in this pass to avoid scope creep into the alert-classification system beyond what was asked.
- 2026-07-15 (later same day, dispatched agent — finding (3) `corporate_action_confirmed`/`earnings_result`): operator
  decided option (a) (stop seeding both as MTDS-tick-manifest expected cells) in an interactive session. Re-verified
  `instruments-service/scripts/enumerate_expected_universe.py` as the sole seeding site, added a tradfi-scoped exclusion
  helper (`_tradfi_mtds_tick_manifest_data_types()`) wired into both `data_types`-resolution call sites, confirmed UAC's
  own `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` registry is untouched (regression-tested), added 4 new regression tests,
  full suite + `quality-gates.sh --no-fix` green. Shipped `instruments-service@03f71c81`. Also resynced the
  `tradfi.json` golden fixture (3-line delta) to a since-committed, unrelated finding-(2) UAC change
  (`unified-api-contracts@78b9e899`, CBOE `ohlcv_15m` narrowing) that was blocking the local quality gate — see
  "Resolution — corporate_action_confirmed / earnings_result" above for the full trace, including why the other 4
  asset_groups' golden fixtures were deliberately reverted (pure formatting noise, no content delta). Historical
  807/807 + 799/799 already-seeded manifest rows deliberately left untouched — documented as a follow-up (production
  data mutation, deserves its own scoped pass), not forced into this commit. This doc's finding (3) is now closed;
  findings (2)'s sub-items (B) downstream aggregation writer and (C) phantom `YAHOO_FINANCE` venue remain open per their
  own todos above.
- 2026-07-15 (independent second audit pass on finding (3) `corporate_action_confirmed`/`earnings_result`, dispatched
  from the same `data_pipeline_alerts_batch_remediation_2026_07_15.md` todo): found the fix already shipped by a
  concurrent agent (`instruments-service@03f71c81`) and the resolution write-up above already landed
  (`unified-trading-pm@24ee65c3a`) before this pass reached the shipping step. Independently re-verified rather than
  duplicating: re-confirmed via fresh grep that `enumerate_expected_universe.py` is the sole non-test/non-restamp-script
  seeding site across instruments-service + market-tick-data-service + UAC; re-read the shipped diff line-by-line and
  confirmed the exclusion is scoped correctly (both `enumerate_v2()` and `main()`'s CLI-default resolution branches
  patched; UAC's `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` registry itself untouched, per the shipped
  `test_uac_data_types_by_asset_group_registry_itself_is_untouched` regression test); confirmed features-service's
  calendar module has zero dependency on `DATA_TYPES_BY_ASSET_GROUP` (grep, zero hits) so the legitimate seeding path is
  provably unaffected. No discrepancies found — the shipped fix matches this doc's own recommendation exactly. Only gap
  closed by this pass: the plan's own `data_pipeline_alerts_batch_remediation_2026_07_15.md` "New todos" checkbox for
  this item was still unflipped despite the underlying work being complete — flipped it with full evidence
  (`unified-trading-pm` commit to follow this entry). **Cross-referencing the "independent second audit pass on finding
  (2)" entry directly above**: its DP-FETCH-009 finding (deployment-service's `_read_attempted_failed_cells` counts
  `attempted_failed` over the WHOLE manifest, no date-recency window) applies equally to finding (3)'s deferred 807/799
  historical rows — i.e. leaving those rows in place is NOT expected to self-resolve the `DP_RUN_MOSTLY_EMPTY` alert for
  this cell even though future seeding has stopped; the alert will keep re-firing off the stale historical rows alone
  until either the rows are explicitly cleaned up or the alert-counting mechanism gains a recency window. Flagging this
  explicitly so the "forward-only, historical rows deferred" decision above is not mistaken for "the alert is now fixed"
  — it is not, by itself.
- 2026-07-15 (operator-directed re-check, dispatched after an interactive pushback on the finding-(C) "phantom venue, no
  adapter" framing above — operator: Yahoo Finance is a real intended data SOURCE for DXY/treasuries/KRW-USD, not a
  missing-adapter gap; the registry conflates source with venue): full workspace grep + direct read across
  market-tick-data-service/instruments-service/features-service/unified-api-contracts, no code changes. **Verdict: the
  operator was RIGHT about DXY and KRW/USD (both fetch successfully today via `YahooFinanceAdapter` +
  `route_yahoo_ tradfi`, venue=ICE and venue=FX respectively — real, live, tested) but WRONG that US Treasury yields
  already work** — `route_yahoo_tradfi()` never routes venue="CBOE" (only FX/KRX/ICE), so the CBOE fixed-income tenors
  registered in `YAHOO_INDICES` + declared in `SOURCE_PRIORITY`/`data_source_continuity.py`/features-service's
  `treasury_yields_calculator.py` have no working fetch path anywhere — a genuine, never-built gap, not a modeling
  error. Also confirmed the operator's broader architectural point (source vs. venue conflation) is correct: the
  `"YAHOO_FINANCE"` phantom-venue registry entries duplicate/shadow the correctly-modeled real venues, and
  `data_source_continuity.py` already has the right shape (a per-instrument SOURCE resolver). **No code shipped** — both
  candidate fixes (CBOE Yahoo-routing addition; YAHOO_FINANCE capability-entry removal) carry real regression/footgun
  risk found during this pass (CBOE fix risks silently breaking live VX-futures Databento capture via the same dispatch
  function; the capability-entry removal risks tripping `get_expected_data_types_for_venue()`'s undocumented
  fall-through-to-ALL-10-datatypes footgun, making the phantom WORSE not better) — both correctly scoped as new todos
  above rather than rushed. See "Verdict — Yahoo Finance source-vs-venue investigation (2026-07-15, operator-directed
  re-check)" above for full citations and the corrected finding-(C) todo annotation.
- 2026-07-15 (later same day, dispatched agent — CBOE US Treasury-yield tenor routing, the last open `[CODE]` todo from
  the "Verdict — Yahoo Finance source-vs-venue investigation" section above): read `route_yahoo_tradfi()` and its full
  caller chain in `umi_tick_provider.py` first — confirmed `data_types` (and `instrument_ids`, unused by this branch) is
  already in scope at the exact call site, so no branch-point relocation was needed. Confirmed CBOE's VX-futures
  Databento path is identified structurally (venue=CBOE, `_umi_massive.MASSIVE_INCAPABLE_VENUES` forces it onto
  `_route_databento`, requested `data_types` drawn from `{ohlcv_1s, ohlcv_1m, trades, tbbo, mbp_10}` per
  `_DATABENTO_SUPPORTED_DATA_TYPES`/`expected_coverage.py:173`) versus the 5 Treasury tenors (venue=CBOE in UAC's
  `YAHOO_INDICES`, `ohlcv_24h`-only). Implemented the narrow, explicit `data_types`-based discriminator recommended by
  the dispatch (not a ticker allowlist duplicated in MTDS — `fetch_yahoo_indices("CBOE", ...)` already IS that allowlist
  via its own `YAHOO_INDICES` venue-filter): CBOE routes to Yahoo ONLY when `data_types` is explicit and an exact subset
  of `{"ohlcv_24h"}`; `data_types=None` (default/no-override) or anything containing a Databento data_type falls through
  unchanged. Shipped `market-tick-data-service@764e7170` (3 files: `_umi_yahoo.py`, `umi_tick_provider.py` comment-only
  accuracy updates, `tests/unit/test_umi_tick_provider_routes.py` +4 tests). Both regression halves the dispatch
  required pass: (a) `ohlcv_24h` reaches `fetch_yahoo_indices("CBOE", ...)`, (b) `ohlcv_1s`/`ohlcv_1m` (VX-futures
  shapes) still reach `DatabentoAdapter.download_batch_df` with the Yahoo fetch asserted never-called — plus 2 extra
  tests for the `data_types=None` default-path and a mixed-data_types request. Full `quality-gates.sh --no-fix` green
  (sentinel `.qg_last_passed_sha` == HEAD verified before quickmerge). **Left open, new `[DATA] P3` todo filed above**:
  UAC's `VENUE_DATA_TYPE_CAPABILITIES["CBOE"]`/`expected_coverage.py` still only declare `{ohlcv_1s, ohlcv_1m}` (no
  `ohlcv_24h`), so `venue_fetch.py`'s per-shard UAC-intersection step still filters an `ohlcv_24h` CBOE request out
  before it reaches this new routing code on a live/default orchestrator run — same "routing fixed, registry restoration
  deferred" shape as the mbp_10/CME resolution above; deliberately not touched here (UAC-repo, out of this task's scope)
  and explicitly checked-and-cleared against the `get_expected_data_types_for_venue()` ALL-10-datatypes footgun the
  dispatch warned about (CBOE's capability dict is non-empty, so that specific footgun does not apply to this follow-up
  — re-verify at UAC-shipping time regardless). See "Resolution — CBOE US Treasury-yield tenors routing (2026-07-15)"
  above for the full discriminator writeup.
- 2026-07-16 (operational — dispatched agent, LIVE deploy + LIVE prod data mutation): operationalized the
  `unified-api-contracts@fec3f110` YAHOO_FINANCE phantom-venue removal (the P3 `[DATA]` todo above). **Deploy-first,
  then clean.** Identified the sole nightly seeder into the tradfi tick manifest as Cloud Run job
  `expected-universe-v2-tradfi` (scheduler `30 1 * * *`, matching the `01:31:30Z` `attempted_at`). **Found + fixed a
  premature-base-bump blocker**: `instruments-service@6d33b9d5`'s UTL base `b7c57243` (17:54Z) predated
  `unified-api-contracts@7754661a` (18:14Z, `venue_data_type_has_batch_source`), so the enum crashed at runtime import;
  re-bumped IS to UTL base `be51b33f` (`instruments-service@3e5b1039`, QG-green; base verified `cloudbuild=70dbc75f`),
  built `cloudbuild=d00de7ec` → digest `d569a654`, re-pinned the job. Verified seeding stops (enum exec `…-lwsqs`
  SUCCESS, fresh shard 5,709 rows / YAHOO=0, real venues seeded; canonical gained 0 new YAHOO rows). Cleaned at the
  source: drained+paused the tradfi consolidator, snapshotted, deleted `venue==YAHOO_FINANCE` from the canonical index
  (11,676→0) and the ranges denominator (5,080→0), resumed. Proved HOLD across ≥5 consolidator merge cycles (all
  surfaces YAHOO=0; `_legacy_seed` never had any). Confirmed CBOE `ohlcv_24h`=True in UAC. Full evidence + before/after
  counts + snapshot paths in "Resolution — YAHOO_FINANCE phantom-venue seeding stopped + orphan rows cleaned
  (2026-07-16)" above. No leftover: the seeding is stopped for good (durable Dockerfile fix on LDR) and the rows are
  cleaned and verified to stay gone.
- 2026-07-28 (slot 7, data_engineering): Closed the deferred `corporate_action_confirmed`/`earnings_result` historical
  orphan-row cleanup (`tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` todo). Live re-query found the population far
  larger than the 807/799 alert-batch figures (420,803 rows in `availability_index.parquet` + 7,540 in
  `expected_universe_ranges.parquet`, 0 `captured`) — deleted via the same snapshot/STOP-ON-SURPRISE/predicate-filter/
  write-back/verify-HOLD playbook as the YAHOO_FINANCE cleanup, HOLD proven across 6 real consolidator merge cycles.
  `market-tick-data-service@c24db4cf`. Full evidence in "Resolution — corporate_action_confirmed / earnings_result"
  above.
- **2026-07-31 (slot 4, review — `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 2,
  audit-only, no code change)**: live-verified CME `VENUE_DATA_TYPE_CAPABILITIES` billing-gating for
  `mbp_10`/`trades`/`tbbo` per the operator's 2026-07-18 "1-month L3 + 1-year L1" note. **Clean pass, no finding.** (1)
  `market_data_categories.py`'s `VENUE_DATA_TYPE_CAPABILITIES["CME"]` still declares ONLY `{ohlcv_1s, ohlcv_1m}` — the 3
  datatypes are absent entirely (neither billing-gated nor unrestricted), matching the still-standing 2026-05-15
  MVP-scope decision above; `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` preserves their pre-narrowing windows for the
  stalled post-cutover restoration. (2) The actual enforcement mechanism IS live + correct:
  `databento_subscription_allowlist.py`'s `LEVEL_MAX_LOOKBACK_DAYS = {L1: 365, L2: 30, L3: 30}` +
  `assert_databento_request_allowed()` fail-closed (`DatabentoLookbackExceededError`) past each level's free window
  (`trades`/`tbbo`→L1, `mbp-10`→L2) — live-tested in `tests/unit/test_databento_subscription_allowlist.py`. No path
  declares these unrestricted for CME. No code shipped (repo: unified-api-contracts, read-only).
