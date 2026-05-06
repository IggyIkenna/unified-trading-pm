---
type: plan
companion_handover: shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
locked_by: live-defi-rollout
locked_since: 2026-05-06
status: phase-0-audit-in-progress
owner: harsh
auditor: claude
---

# Shard-Granularity SSOT Propagation — Plan

**Branch:** `live-defi-rollout` **Status:** Phase 0 audit in progress (started 2026-05-06).
**Companion handover:** `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`

---

## Context

Most of the v5 manifest + shard-granularity work already shipped across prior plans. **This plan is a redo-and-test
verification pass to confirm end-to-end consistency, not greenfield.** Goal: every shard atom is identical across
(a) writer atomicity, (b) manifest row key, (c) data-status display, (d) downstream pre-flight gate, (e) deployment-UI
drill-down. Drift between any two = silent correctness bug.

Triggering incidents (see handover for detail):

- TradFi MVP partial bundles (ES.OPT 18/839 historical bundles passed manifest as captured)
- MDPS empty-placeholder bars (1440 NaN OHLC bars/day/venue for years)
- Databento per-schema silent drop on 429

Co-evolving streams (do NOT duplicate — handover Items 1/2/3):

1. Cluster-aware bundle validation (lands in UTL `ManifestWriter.record_captured`)
2. Databento 429 silent-drop fix (MTDS `databento_adapter.download_batch_df`)
3. VIX forward-poll wiring (`umi_tick_provider.py`)

**Coordination rule:** if audit findings overlap Items 1 or 2, comment in this plan + continue auditing — don't ship a
parallel fix.

---

## Phase 0 — Per-Service Audit (in progress)

Audit only. No code changes in this phase. Findings appended to `## Audit Findings` below as each service completes.
Format per service:

- ✓ items that match target shape
- ❌ items that don't match (writer / pre-flight / available_at / write-gate / migration / UI)
- 🔀 items implemented in the wrong layer
- ❓ items where verification needs codex pointer or clarification

### Audit DAG

```
Phase 0.1 (sequential, anchors row-key shape)
    └── instruments-service

Phase 0.2 (parallel after 0.1 establishes baseline)
    ├── market-tick-data-service (MTDS)
    ├── market-data-processing-service (MDPS)
    └── features-onchain-service / features-sports-service / features-delta-one-service

Phase 0.3 (synthesis)
    ├── Consolidated migration list (manifest drift instances + estimated shape)
    ├── Consolidated UTL-lift list (utilities currently duplicated per-service)
    └── Prediction canonical-question-group SSOT check in UAC
```

### Phase 0 Todos

- [ ] [AUDIT] P0. instruments-service — writer / pre-flight / available_at / write-gates / dual-vocab probe / per-instrument
      progress events
- [ ] [AUDIT] P0. market-tick-data-service — same checklist + scan every adapter for `except: continue` swallowing
      per-schema/per-instrument failures (skip databento_adapter.py — being fixed in parallel)
- [ ] [AUDIT] P0. market-data-processing-service — same + reader-vs-writer drift (1440-empty-bars incident pattern)
- [ ] [AUDIT] P0. features-onchain-service — same + LookaheadBiasError coverage + DAG-input pre-flight granularity
- [ ] [AUDIT] P0. features-sports-service — same + sports temporal availability stamping rules (lineups / injuries /
      pre-match odds / post-match / weather)
- [ ] [AUDIT] P0. features-delta-one-service — same + LookaheadBiasError coverage
- [ ] [AUDIT] P0. UAC prediction canonical-question-group SSOT — verify mapping raw Polymarket market_id →
      canonical question group exists; flag as build item if missing
- [ ] [AUDIT] P0. Consolidated migration list — manifest drift instances per service + estimated migration shape
- [ ] [AUDIT] P0. Consolidated UTL-lift list — cross-service utilities currently inlined per-service

### QG between phases

- [ ] Phase 0 → Phase 1: handover sign-off on audit findings; user converts findings into per-service fix todos in
      Phase 1 below.

---

## Phase 1 — Per-Service Fixes (TBD pending audit)

Phased fix work derived from Phase 0 findings. Each fix is tagged with placement layer (`[UAC]`, `[UTL]`,
`[per-service]`, `[deployment-api]`, `[deployment-ui]`). Items overlapping co-evolving Items 1/2 stay in the parallel
stream — not added here.

_To be populated after audit completes. Owner: harsh routes findings into ordered fix DAG._

---

## Phase 2 — Validation (TBD)

- [ ] All affected downstream consumers updated in this plan (no "fix later")
- [ ] Manifest reads + writes use same shard key for every (service, data_type)
- [ ] Data-status surfaces match writer granularity (audit report only — UI fix tracked separately)
- [ ] No fallback paths remain for migrated manifests
- [ ] Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud
- [ ] `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
      `available_at > kickoff - 24h`
- [ ] QG green per repo touched

---

## Audit Findings

_Findings appended per service as audit progresses. Each section follows the ✓ / ❌ / 🔀 / ❓ structure._

### instruments-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06. Source files: `instruments_service/engine/orchestrator.py` (6107 lines),
`instruments_service/cli/instruments_handler.py` (214 lines), plus 14 manifest-touching scripts under `scripts/`.

#### ✓ Matches target

- **v5 row-key API exists in UTL** — `ManifestWriter.record_captured` / `record_empty` / `record_failed` accept full
  v5+ row_key shape including `chain`, `instrument_type`, `instrument_id`, `league_id`, `feature_group`, `model_family`,
  `quote_asset`, `margin_type`, `combo_type`, `leg_weights` (`unified_trading_library/manifest_writer.py:1048-1188`,
  `_ROW_KEY_COLUMNS` at line 383).
- **Pre-launch guard is built into `add()`** — UAC `is_pre_launch_date(data_type, date)` short-circuits writes for
  pre-`SOURCE_COVERAGE_START` / pre-`DATA_TYPE_COVERAGE_START` rows (`manifest_writer.py:708-720`). Comment cites the
  2026-05-04 incident (229,224 pre-launch rows purged).
- **Honest-coverage trio used** — orchestrator distinguishes `record_empty` (legitimate empty,
  e.g. `orchestrator.py:4032`, `4475`, `5206-5218`) from `record_failed` (exception, e.g. `4053`, `4496`, `5395-5409`).
  Failure routes through `_classify_adapter_failure → classify_venue_error` (line 530-543).
- **`_should_skip_date_for_per_league` helper exists and is correctly used in some sites** — solves the per-league
  honest-coverage gap for FOOTYSTATS PREDICTIONS (line 3897) and FOOTYSTATS MATCHES (line 4258 area). Comment at
  line 506 documents the 2026-05-05 MATCHES 18%-coverage incident this fixes.
- **Sports per-league `record_empty` for in-season-but-zero-fixtures** — API_FOOTBALL FIXTURES
  (`orchestrator.py:1956-1970`), SFI_PROGRESSIVE_STATS (5335-5343, 5352-5360, 5368-5376) — leagues whose season covers
  the date but had zero output get explicit `record_empty(row_key={..., league_id=lid})` rows. Without this, mid-week
  per-league gaps render as red `missing` instead of `empty_confirmed`.
- **`_classify_adapter_failure` routes through UAC `classify_venue_error`** — error reasons are categorical, not raw
  exception strings (`orchestrator.py:530-543`).
- **TradFi non-trading-day handling is honest** — `is_non_trading_day(venue, date)` from
  `venue_trading_calendar` produces 0-count manifest rows for weekends/holidays
  (`orchestrator.py:1799-1830`, `2010-2028`). No naive weekday filters.
- **PIT `data_available_at` stamped at write-time per source** for sports adapters. Examples:
  - FootyStats predictions: `kickoff_utc - 72h` (line 3918) — verified against 2026-04-17 probe
  - FootyStats odds: `kickoff_utc - 72h` (line 4377)
  - API Football injuries/fixtures: `date + 12h` / `kickoff + 17h` (line 3135, 3271, 3325, 3446)
  - SFI progressive: `kickoff_15:00 + timer_seconds` (line 5283)
  - Pred (Polymarket UP_DOWN): `kickoff_utc - 72h` (line 3918)

#### ❌ Mismatches

- **[pre-flight]** `orchestrator.py:5013-5018` — SFI_PROGRESSIVE_STATS pre-flight reads coarse
  `row_key={"date": date, "data_type": "SFI_PROGRESSIVE_STATS"}` but the writer at `5293-5313` (and the per-league
  `record_empty` at `5210-5218`, `5335-5343`, `5352-5360`, `5368-5376`) writes per-league rows including
  `league_id=...`. Result: if the coarse date-row is captured but a league is missing, the date-level skip permanently
  locks out per-league re-fetch. Same pattern as the 2026-05-05 MATCHES 18%-coverage incident; should use
  `_should_skip_date_for_per_league` like FOOTYSTATS PREDICTIONS (line 3897) does. Fix layer: **[per-service]**.
- **[pre-flight]** `orchestrator.py:5183` — SFI_STANDINGS pre-flight at coarse `(date, data_type)` only. Same bug
  shape. Fix layer: **[per-service]**.
- **[pre-flight]** `orchestrator.py:4747-4750` — PLAYER_VALUES (Transfermarkt) pre-flight at coarse
  `row_key={"date": date, "data_type": "PLAYER_VALUES"}`; writer at `4946-4951` records `record_empty` per-league. Fix
  layer: **[per-service]**.
- **[write-gate]** `orchestrator.py:3946-3952` + `4064-4112` — `_validate_predictions_null_rates` is inlined per-data-
  type with hardcoded thresholds (5% for core cols, 20% for potentials). Violations emit a `logger.warning(...)` but
  the parquet is **written anyway** ("writing anyway" comment line 3949). This is the carry-tracer pattern; threshold
  source-of-truth should be UAC per `feature_group`, and violations should produce `attempted_failed` not silent warn.
  Fix layer: **[UTL]** (lift to shared write-gate helper) + **[UAC]** (per-feature_group thresholds).
- **[write-gate]** Workspace-wide gap — no row-count==0 / NaN-ratio / schema-match gate fires at the write boundary.
  `record_captured`'s `_maybe_validate` does schema-only check (warn-only by default; strict mode is opt-in via
  `MANIFEST_STRICT_SCHEMA_VALIDATION=true`). Row-count and NaN-ratio gates absent. Fix layer: **[UTL]** (extend
  `_maybe_validate` or add sibling gate) + **[UAC]** (per-feature_group NaN thresholds).
- **[available_at]** `orchestrator.py:5279-5285` — SFI progressive PIT stamp uses `15:00 UTC` as a **hardcoded common
  match hour** because no per-match kickoff lookup is wired in. This is approximation, not stamping-at-write-time. Late
  matches (e.g. 21:00 UTC kickoff) get `available_at` 6h too early — potential look-ahead leak for downstream features.
  Fix layer: **[per-service]** (lookup `kickoff_utc` from API_FOOTBALL fixtures bucket) or **[UAC]** (sports temporal
  availability helper that fetches kickoff_utc).
- **[available_at]** `orchestrator.py:1990-1995` — Polymarket per-market manifest write uses
  `data_type=_mkt_str` (e.g. `"BTC"`, `"FOOTBALL"`) which **overloads `data_type` with shard-name**. The handover
  explicitly forbids overloading dimensions. The shard-name should be `instrument_id` or a new `canonical_question_group`
  column, not `data_type`. Fix layer: **[UAC]** + **[per-service]**.
- **[migration]** `orchestrator.py:1988-1995` Polymarket manifest write uses `_extract_prediction_shard` (line 2497)
  which does inline `base_asset.split(":")` parsing with hardcoded shard patterns (`UP_DOWN`, `FOOTBALL`). This is the
  canonical-question-group SSOT gap the handover flagged. **No UAC SSOT exists** for raw Polymarket market_id →
  canonical question group (verified by grep). Fix layer: **[UAC build]**.

#### 🔀 Wrong layer

- **[UTL → per-service drift]** `_validate_predictions_null_rates` (orchestrator.py:4064) is a service-local NaN-ratio
  gate that should live in UTL alongside `ManifestWriter` write-gates. Other services likely have a similar inlined
  gate (audit pending — flagged for synthesis phase).
- **[UTL → per-service drift]** `_classify_adapter_failure` (orchestrator.py:530-543) is small but is exactly the
  kind of cross-service utility that should be a shared UTL helper since EVERY adapter does this same try/UAC-classify/
  fallback dance. Verify other services aren't duplicating; if they are, lift.
- **[per-service → UAC]** `_extract_prediction_shard` (orchestrator.py:2497) — the canonical-question-group taxonomy
  is a UAC SSOT concern, not per-service parsing logic.

#### ❓ Couldn't verify

- Whether downstream consumers (MTDS prediction adapter, features-* prediction calculators) read the Polymarket per-
  market manifest at the same `data_type=_mkt_str` shape, or whether they expect a different column. If they expect
  `instrument_id`, the writer is silently writing rows the readers don't find — phantom equivalent.
  Cross-check pending in MTDS audit.
- Whether the 14 scripts under `instruments-service/scripts/` (rebuild_sports_manifest, rescan_*, fill_missing_*,
  patch_prediction_shards, fix_manifest_venue_casing, etc.) follow the manifest concurrency principle (read-once + TTL
  freshness check + write-time CAS). Backfill scripts that bypass it can mass-overwrite concurrent worker writes. Spot-
  check pending.
- Per-instrument progress events (`INSTRUMENT_PROCESSED` with row_count) — orchestrator emits `PROCESSING_COMPLETED`
  per date and `ADAPTER_FETCH_FAILED` on errors, but I did not verify whether per-instrument or per-shard events with
  row counts exist for the silent-success-with-zero-output detection pattern. Pending.
- Manifest drift on disk — would need to actually list a few canonical bucket prefixes to confirm v5 column shape
  in production parquet. Audit only inspected source-code writers, not on-disk artifacts.

#### Migration items (instruments-service contribution)

- **MIG-1**: Add `canonical_question_group` column to v5 manifest schema (UAC + UTL); migrate Polymarket on-disk rows
  from `data_type=BTC|ETH|...` overload to `canonical_question_group=BTC|ETH|...` + `data_type=PREDICTION_INSTRUMENTS`
  (or similar). Migration script precedent: `instruments-service/scripts/migrate_local_sfi_to_canonical.py`.
- **MIG-2**: SFI_PROGRESSIVE `available_at` rows currently stamped against `kickoff = 15:00 UTC` placeholder need a
  one-time migration to back-fill from `kickoff_utc` once the per-match lookup is wired in. Mark old rows with a
  `available_at_quality=approximate` flag or re-stamp.

#### UTL-lift items (instruments-service contribution)

- **LIFT-1**: NaN-ratio + row-count==0 + schema-match write-gate trio. Single helper
  `validate_shard_or_fail(df, *, feature_group, data_type, threshold_source=UAC) → ValidationResult` lifted to UTL.
  Replaces inlined `_validate_predictions_null_rates` and equivalent logic in other services.
- **LIFT-2**: `_classify_adapter_failure` (orchestrator.py:530-543) — try `classify_venue_error` then fall back to
  exception class name. Probably duplicated across MTDS/features-*.
- **LIFT-3**: `_should_skip_date_for_per_league` (orchestrator.py:490-527) is service-local but the per-league-skip
  pattern applies anywhere a writer produces per-leaf rows under a coarser key. Generalise to
  `_should_skip_date_for_per_leaf(manifest, date, data_type, expected_leaf_dim, expected_leaf_values, force)`.

### features-delta-one-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06. Source files: `features_delta_one_service/engine/orchestrator.py` (733 lines),
`features_delta_one_service/engine/delta_one_validity_engine.py` (269 lines), 30+ calculators under
`features_delta_one_service/app/calculators/`.

#### ✓ Matches target

- **Shard-level failure isolation** — `_safe_process_instrument` (orchestrator.py:341+) catches errors per-instrument,
  doesn't raise inside the per-instrument loop.
- **`resolve_data_type_for_feature_group`** uses UAC SSOT (`orchestrator.py:339`) with per-asset-group overrides.
- **`validate_batch_completeness`** is called pre-write (orchestrator.py:295) — at least one cross-instrument
  completeness check exists.

#### ❌ Mismatches

- **[writer]** `orchestrator.py:316-326` — `writer.add()` is called **TWICE** with the same payload (lines 316-321 with
  `timeframe=`, lines 322-326 without). Writes **2 manifest rows per processing cycle** for the same shard. Almost
  certainly a refactor leftover. One of these is a bug; either `timeframe=` is required everywhere (delete 322-326) or
  not used (delete 316-321). Fix layer: **[per-service]**.
- **[writer]** Service uses **only `manifest.add()`**. No `record_captured` / `record_empty` / `record_failed` calls
  anywhere in the source tree. The honest-coverage trio is not implemented for delta-one features. So:
  - Failed shards → no manifest row at all (silently absent — line 292 conditions write on `success_count > 0`).
  - Empty/sparse shards → no `record_empty` distinction; if `success_count == 0`, no row written.
  - The 4-pillar write-gate (row=0 / NaN / schema / cluster) does NOT fire — `add()` skips schema validation.
  Fix layer: **[per-service]** (rewrite write-path) + **[UTL]** (the `record_captured` API exists already).
- **[pre-flight]** No `_should_skip_shard` lookup anywhere. Recompute happens unconditionally per-instrument — only
  `force_reprocess` flag governs (same as no skip). Means concurrent backfill / re-run will redo all work since manifest
  isn't consulted. Fix layer: **[per-service]**.
- **[write-gate]** `validate_batch_completeness` returns `(is_complete, missing)`. On incomplete: code logs warning at
  line 303 then **skips manifest write entirely** (line 309 — `else` branch wrapping the writer). So a 50%-complete
  batch leaves **zero manifest rows** for both completed AND missing shards. Anti-pattern. Should `record_captured`
  per-completed-shard + `record_failed` per-missing-shard. Fix layer: **[per-service]**.
- **[write-gate]** `orchestrator.py:328-329` — manifest write failure caught with bare
  `except (ConnectionError, TimeoutError, OSError, ValueError, RuntimeError)` and warning-logged. If GCS hiccups, the
  whole shard becomes invisible to data-status. Should be fatal or `record_failed` route. Fix layer: **[per-service]**.
- **[lookahead] CRITICAL** — `grep -rn LookaheadBiasError` in features-delta-one returned **zero hits**. The 30+
  calculators (`moving_averages.py`, `momentum.py`, `vwap.py`, `economic_events.py`, `kurtosis.py`, etc.) do NOT raise
  `LookaheadBiasError`. The only `available_at` check in the workspace lives in features-onchain `feature_writer.py`.
  Per the handover: "extend to every features-\* calculator." This is the largest single lookahead-bias gap in the
  workspace. Fix layer: **[per-service]** (per-calculator) + **[UTL/UAC]** (mandatory `LookaheadBiasError` extension
  via shared base-class + `feature_group → required_inputs` DAG SSOT).
- **[available_at]** No service-level write of `available_at` column observed in the orchestrator write-path. Need to
  spot-check one calculator (e.g. `vwap.py`) to confirm whether each writes its own `available_at` — high probability
  it doesn't, given the LookaheadBiasError gap. Fix layer: **[per-service]**.

#### 🔀 Wrong layer

- **[per-service]** `validate_batch_completeness` (used at orchestrator.py:295, imported from somewhere — likely
  `unified_trading_library`) sounds like the right utility for completeness validation, but its current usage drops the
  manifest write on incomplete which is the wrong action. The action on incomplete should be `record_failed` per-missing
  shard, not "skip the manifest entirely" — that policy decision is encoded at the call site, not in the helper. Tag as
  per-service rewrite.

#### ❓ Couldn't verify

- Whether ANY of the 30+ calculators stamp `available_at` at write-time. Would need spot-check 3-5 calculators
  (vwap, moving_averages, momentum, kurtosis, economic_events) to confirm or contradict. Listed under per-calculator
  fix items in Phase 1.
- Whether `delta_one_validity_engine.py` (269 lines, not yet read) does any PIT or lookahead enforcement that
  wraps the calculator outputs. If yes, the LookaheadBiasError gap might be partially closed. If no, the gap is total.
- Per-instrument progress events (`INSTRUMENT_PROCESSED`) — orchestrator emits a `BATCH_COMPLETED`-style event after
  the full batch (the `log_event(...)` at line 273-289 includes counts); per-instrument granular events with row counts
  not confirmed. Pending.

#### Migration items (features-delta-one-service contribution)

- **MIG-DO1**: Switch `writer.add()` calls (orchestrator.py:316-326) to `record_captured` / `record_empty` /
  `record_failed`. Delete the duplicate `add()` call.
- **MIG-DO2**: All 30+ calculators need `available_at` stamping at write-time. Per-calculator review + add `available_at
  = compute_input.timestamp + calc_horizon` (or per-source rule).

#### UTL-lift items (features-delta-one-service contribution)

- **LIFT-DO1**: Mandatory `LookaheadBiasError` enforcement across all features-\* calculators — UTL helper that wraps
  every calculator's compute call with PIT enforcement. Currently only features-onchain `feature_writer.py` does this.
  This needs to lift to a shared `feature_calculator_base.py` in UTL that all features-\* services inherit, so
  LookaheadBiasError raises become structural rather than per-service additions.
- **LIFT-DO2**: Manifest write-on-incomplete-batch policy — a UTL helper `record_partial_batch(manifest, completed,
  failed)` that does the right thing (record_captured for completed + record_failed for missing), instead of services
  re-implementing the conditional + dropping the manifest entirely on incomplete.

### UAC prediction canonical-question-group SSOT — Audit Finding

Audit pass 2026-05-06. Files inspected: `unified_api_contracts/canonical/domain/prediction/prediction_mapping.py`,
`unified_api_contracts/external/polymarket/`.

#### ❌ Greenfield gap (confirmed)

- **Existing module is a different abstraction**: `prediction_mapping.py` defines `CanonicalPredictionMarket` (per-
  market `PRED:{category}:{hash12}` IDs) and `PredictionMarketCrossVenueMapping` (cross-venue event linking with
  `underlying`, `timeframe`, `strike`). Categories are 7 coarse buckets:
  POLITICS / FINANCIAL / SPORTS / CRYPTO / WEATHER / ENTERTAINMENT / OTHER. Useful but **NOT the shard-atom SSOT
  the handover specifies**.
- **Missing**: A function `polymarket_market_id_to_canonical_question_group(market_id) → str` returning a stable
  identifier like `BTC_UP_DOWN_1D`, `SPX_UP_DOWN_1D`, `EPL_MATCH_ODDS`, etc. This is the bundling axis equivalent to
  `options_chain` for derivatives. Service-side proxy (`instruments-service/orchestrator.py:_extract_prediction_shard`,
  line 2497) does inline parsing with hardcoded patterns (`UP_DOWN`, `FOOTBALL`).
- **Missing**: A registry of expected `canonical_question_group` values per (venue, day) so write-gates can detect
  partial bundles (e.g. "expected 6 BTC UP_DOWN strikes, only got 4" → `record_failed(ClusterCoverageError)`).
- **Missing**: Cross-venue normalization — Polymarket BTC up/down vs Kalshi BTC up/down should map to the SAME
  `canonical_question_group_id` for downstream cross-venue alpha capture.

#### Build items (UAC prediction SSOT)

- **BUILD-PRED1**: New module `unified_api_contracts/canonical/domain/prediction/canonical_question_group.py` with:
  - `CanonicalQuestionGroup` dataclass: `(group_id, underlying, instrument_type, timeframe, expiry_class)` —
    parallel to `options_chain` shape.
  - `polymarket_market_to_canonical_group(condition_id, question_text, resolution_date) → CanonicalQuestionGroup`.
  - `kalshi_market_to_canonical_group(market_ticker, ...) → CanonicalQuestionGroup`.
  - `EXPECTED_QUESTION_GROUPS_PER_DAY[(venue, date)] → set[group_id]` for cluster-coverage validation.
  - Migration helper to back-fill `canonical_question_group` column on existing on-disk manifest rows, mapping from
    the legacy `data_type` overload (e.g. `data_type=BTC` → `canonical_question_group=BTC_UP_DOWN_1D`).
- **BUILD-PRED2**: Wire `canonical_question_group` as a v6 manifest column (UTL `_ROW_KEY_COLUMNS` already accepts
  optional dimensions; add via plan's manifest schema migration).
- **BUILD-PRED3**: Update `instruments-service/scripts/aggregate_processed_options_to_chain_bundle.py` precedent
  pattern to a sibling `aggregate_polymarket_to_canonical_group_bundle.py` for prediction.
- **BUILD-PRED4**: Update MTDS prediction adapter (`polymarket_adapter.py`, `kalshi_adapter.py`) to read at
  `canonical_question_group` granularity, not `data_type=_mkt_str`.

### features-onchain-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06 by Sonnet sub-agent. Source files: `features_onchain_service/engine/orchestrator.py`,
`features_onchain_service/app/core/feature_writer.py`, `dependency_checker.py`, `mtds_canonical_reader.py`,
`schemas/feature_builder_registry.py`, 25+ calculators under `app/calculators/`.

#### ✓ Matches target

- **Write-gate trio fires** — `OnChainFeatureWriter.write_features` (`feature_writer.py:119-133`) returns False on empty
  DataFrame; `FeatureWriteGate` from UTL evaluated at every write (`feature_writer.py:154-178`); timestamp-date
  alignment validated at 99% (`feature_writer.py:326-348`). Three of the four pillars are honored at the writer.
- **`LookaheadBiasError` from UTL** — imported and raised via `_enforce_point_in_time` (`feature_writer.py:270-324`).
  Strict in production, warn-only in mock mode. The currently-firing case for `lst_yields` is here.
- **Per-day write isolation** — `_process_daily_feature_group` writes one parquet per day with `date=cur` so a single
  bad day doesn't poison the whole window. The pre-2026-05 concat-all-write-once anti-pattern has been fixed.
- **Shard-level failure isolation** — `batch_handler.py:112-136` per-feature-group try/except.
- **Honest progress events** — `LST_DAY_PROCESSED` per-day row counts (`orchestrator.py:654-665`),
  `FEATURE_GROUP_WINDOW_SUMMARY` aggregates, `PERSISTENCE_STARTED/COMPLETED` from actual write site.
- **Domain types from UAC** — `models.py` is a re-export facade over `unified_api_contracts.internal`.
- **Canonical MTDS path probe + dual-vocab fallback** — `mtds_canonical_reader.py` uses `build_defi_partition_path` from
  UAC; legacy `category=defi/` fallback limited to that single substitution.

#### ❌ Mismatches

- **[writer]** `orchestrator.py:163-172` — `ManifestWriter.add` called with only `(processing_date, row_count,
  feature_group)`. **No `chain`, no `venue`, no `instrument_id`, no `data_type`.** DeFi target shard is
  `(asset_group=defi, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)`. Current writer collapses
  every `(feature_group, day)` to a single row regardless of how many chains × protocols were processed. Same
  partial-bundle bug class as the handover incidents. Fix layer: **[per-service]**.
- **[pre-flight]** `orchestrator.py:108-113` — `check_shard_freshness(bucket, date, service_name,
  expected_venues=[feature_group])` is at `(date, feature_group)` only. If `lending_rates` was previously written for
  ETHEREUM and Arbitrum data arrives later, skip-if-fresh **incorrectly reports the shard as fresh**. Pre-flight
  coarser than writer = silent partial coverage. Fix layer: **[per-service]**.
- **[record_empty / record_failed]** — Never called anywhere. Empty-loader days silently `continue`
  (`orchestrator.py:1119-1121`, `_process_lst_yields` at `510-513`). The honest-coverage trio is unused.
  Fix layer: **[per-service]**.
- **[available_at]** — `_add_timestamp_out` (`feature_writer.py:238-268`) adds `timestamp_out` (observation +
  synthetic 500ms delay), NOT `available_at`. No calculator stamps `available_at` on output. Downstream consumers
  reading these parquets have no column to check `<= kickoff_or_target_ts - N`. Fix layer: **[per-service]** + **[UAC]**
  (semantics).
- **[lookahead]** — `LookaheadBiasError` only checks **output observation timestamps vs `as_of_date + 1 day`**, not
  **input rows' `available_at` vs `target_ts - N`**. Structural gap: no calculator can input-check because
  `available_at` is absent from upstream MTDS parquets. The currently-passing lst_yields case is the writer's
  output-side guard, not the input-side rule the handover requires. Fix layer: **[per-service]** + **[UTL]** +
  upstream **MTDS** must stamp `available_at`.
- **[NaN threshold]** `feature_writer.py:61` — `nan_threshold=0.95` hardcoded. Per-feature-group thresholds belong in
  UAC. Fix layer: **[UAC]** + **[UTL]** (`FeatureWriteGate` accept per-group lookup).
- **[feature_group → required_inputs DAG]** `feature_builder_registry.py:59-76` — service-local `_metadata` dict
  declares deps (`aave_rate_impact: [aave_lending_rates, aave_utilization]`, etc.). DAG belongs in UAC SSOT so
  downstream pre-flight checks can also import without duplication. Fix layer: **[UAC]**.
- **[downstream pre-flight checks one upstream bucket, not all DAG inputs]** `dependency_checker.py:41-63` —
  `UPSTREAM_DEPS` is a fixed dict checking MDPS bucket existence + 3 optional MTDS buckets. Does NOT consult the
  feature_group DAG. `rate_impact` can run even if `lending_rates` produced zero rows that day. Fix layer:
  **[per-service]**.
- **[CanonicalDefiShard service-local]** `mtds_canonical_reader.py:39-51` — used by 5 calculators. Cross-cutting shard
  identity descriptor, belongs in `unified_api_contracts.defi` or UTL. Fix layer: **[UAC]**.
- **[manifest concurrency]** No TTL-cached per-date freshness check. Multi-day window processing has no per-day
  re-check. Concurrent workers will duplicate work. Fix layer: **[per-service]** (apply the
  `_refresh_captured_cache + _is_now_captured` pattern from PM CLAUDE.md).
- **[classify_venue_error / ADAPTER_FETCH_FAILED absent]** `data_loader.py` and adapters wrap exceptions with
  `EnhancedError` but never call `classify_venue_error()` or emit `ADAPTER_FETCH_FAILED`. Workspace rule violation.
  Fix layer: **[per-service]**.
- **[CLI/registry inconsistency]** `parser.py:24` `CATEGORIES = ["CEFI", "DEFI"]` but `dependency_checker.py:76`
  references `"TRADFI": "features-onchain-{project_id}"`. Either dead code or missing CLI choice. Fix layer:
  **[per-service]** trim or extend.

#### 🔀 Wrong layer

- `CanonicalDefiShard` (`mtds_canonical_reader.py:39-51`) → UAC.
- `FEATURE_GROUPS` list (`cli/parser.py:9-22`) + `_metadata` DAG (`feature_builder_registry.py:58-76`) → UAC.
- `_MTDS_OUTPUT_BUCKET_DOMAINS` + `_PATH_DATA_TYPE` (`mtds_output_config.py:33-53`) — module docstring acknowledges
  pending UAC migration. Lift.
- `WRITE_GATE_CONFIG` `nan_threshold=0.95` (`feature_writer.py:52-65`) — per-group thresholds → UAC.

#### ❓ Couldn't verify

- Whether UTL `check_shard_freshness` accepts a `chain=` filter argument (currently supports `league_id=` only).
  Even after writer fix, pre-flight would need API change.
- Whether `add()` path sets `capture_status="captured"` vs leaving blank — affects data-status rendering.
- Whether downstream strategy-service pre-flight reads features-onchain manifest at the right granularity.
- Whether Phase 8 calculators (`block_priority_gas_distribution`, `concentrated_liquidity_il_realised`,
  `vault_share_price_apy`, `pool_invariant_drift`) have actual MTDS partitions on disk — they currently silently produce
  zero-row outputs when partitions don't exist (no `record_empty`).

#### Lookahead-bias coverage matrix (features-onchain)

| Calculator | LookaheadBiasError raised | available_at checked | Notes |
|---|---|---|---|
| `lst_yields` (orchestrator inline) | ✓ via writer | ❌ | Output-observation check vs as_of+1d, NOT input.available_at vs target-N |
| `lending_rates`, `utilization`, `rewards`, `risk_params`, `flash_loan_availability`, `health_factor`, `liquidation_events`, `onchain_perps`, `macro_sentiment`, `rate_impact` | ✓ via writer (same path) | ❌ | Same: output-side only |
| `aave_*_calculator.py` (lending/rate_impact/risk/utilization) | ❌ | ❌ | Calculator's `calculate_features` doesn't check lookahead at all |
| Phase 8: `block_priority_gas_distribution`, `concentrated_liquidity_il_realised`, `vault_share_price_apy`, `pool_invariant_drift` | ❌ | ❌ | Not yet wired to dispatch; no guard |
| `defillama_tvl`, `fear_greed`, `macro_sentiment_calculator`, `cryptoquant_exchange_flow`, `eigen_rewards`, `protocol_rewards`, `flash_loan_calculator`, `lst_staking`, `onchain_regime_calculator` | ❌ | ❌ | No lookahead guard in any |

**Summary**: 11 feature_groups go through the shared writer's `_enforce_point_in_time` (output-side check only,
not the input-side rule). 14+ calculators have no lookahead guard at all. The structural gap is missing `available_at`
on MTDS upstream parquets — until that lands, calculators can't input-check.

#### Migration items (features-onchain-service contribution)

- None for this service's own historical writes — manifest rows are at `(feature_group, day)` granularity, which is
  too coarse but not a v4-vs-v5 schema-version drift. **Corrective action is to expand the writer key, not migrate
  existing rows.** Once writer is fixed, on-disk multi-chain coverage will be visible immediately.

#### UTL-lift items (features-onchain-service contribution)

- **LIFT-OC1**: `CanonicalDefiShard` (mtds_canonical_reader.py) → UAC `unified_api_contracts.defi`.
- **LIFT-OC2**: `_MTDS_OUTPUT_BUCKET_DOMAINS` + `_PATH_DATA_TYPE` (mtds_output_config.py) → UAC.
- **LIFT-OC3**: `feature_group → required_inputs` DAG (`_metadata` dict in feature_builder_registry.py) → UAC
  `ONCHAIN_FEATURE_GROUP_DEPS`.
- **LIFT-OC4**: NaN threshold from per-group UAC lookup, not service-hardcoded.

### features-sports-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06 by Sonnet sub-agent. Source files: `features_sports_service/engine/batch_handler.py`,
`writer.py`, `orchestrator.py`, `data/gcs_reader.py`, exporters, calculators, `compute/coverage_gate.py`,
`tracking/feature_builder_registry.py`.

#### ✓ Matches target

- **Shard-level failure isolation** — per-table/per-feature-group try/except never raises in `batch_handler.py:370,
  457, 520, 590`.
- **Honest-coverage trio used** — `record_empty` for legitimately-empty (`batch_handler.py:357, 450, 513, 583`),
  `record_failed` for exceptions (`379, 465, 528, 598`), `manifest.add()` for captured.
- **`FeatureWriteGate`** applied (`writer.py:125`) with NaN 50%, alignment 90%, leakage check.
- **`PointInTimeEnforcer`** + `LookaheadBiasError` imported (`writer.py:17, 53`).
- **Live-mode lookahead re-raise** — `orchestrator.py:140-151` re-raises `PointInTimeViolation` after
  `LOOKAHEAD_BIAS_VIOLATION` event.
- **HT-odds PIT gate** — `odds_features_exporter.py:43-116` drops post-HT-break odds rows.
- **Dual-vocab read** — `gcs_reader.py:39-41, 940-941` tries `asset_group=sports` canonical first then
  `category=sports` legacy.
- **`validate_batch_no_leakage`** strict=True (`orchestrator.py:156-212`).
- **`asof_lookup`** filters `timestamp_col <= as_of` (`pipeline/_asof.py:81`).
- **UAC `FEATURE_UPSTREAM_REQUIREMENTS` / `in_coverage`** imported in `compute/coverage_gate.py:44-48`.
- **Per-league GCS write sharding** — `_write_per_league` (`batch_handler.py:176-231`) groups by league_id.
- **`manifest.add(league_id=...)`** — captured rows at `batch_handler.py:615-628`.

#### ❌ Mismatches

- **[writer]** `batch_handler.py:615-628` — captured rows use legacy `manifest.add()` not `record_captured(row_key=...)`.
  `add()` capture_status default is unclear (need to read manifest_writer.py:636-685 fully). v6 SSOT method is
  `record_captured`. All 3 feature groups + all 14+ raw tables go through this path. Fix layer: **[per-service]**.
- **[pre-flight]** `batch_handler.py:304-308` — pre-flight `manifest.lookup` row_key = `{date, feature_group}` only.
  Missing `fixture_id`, `league_id`, `timeframe`. Day-level captured-status will skip recompute for ALL leagues even
  if individual leagues failed. Coarser than writer's per-league sharding. Fix layer: **[per-service]**.
- **[writer]** `manifest.add()` for captured rows does NOT include `timeframe` or `fixture_id` even when writer
  shards by league_id. Per-fixture drill-down impossible. Fix layer: **[per-service]**.
- **[writer]** `batch_handler.py:40-44` `_FEATURE_GROUP_TO_DATA_TYPE` maps **only 3 of 14+ feature groups** to canonical
  data_type. Remaining 11 raw table groups (fixture_stats, fixture_events, lineups, player_stats, injuries, players,
  venues, fixtures, leagues, teams, referees, coaches, standings, rounds) write `data_type=""` — invisible to data-
  status reader filtered by data_type. Fix layer: **[per-service]**.
- **[available_at] CRITICAL** — `_ensure_timestamp` (`batch_handler.py:146-151`) sets `timestamp = datetime(year, month,
  day, tzinfo=UTC)` (midnight UTC) for any DataFrame lacking timestamp. Midnight passes the 23:59:59 PIT enforcer
  silently → every output table's `available_at` is artificial midnight, NOT source-specific availability. Specifically:
  - **Lineups**: should be `kickoff - 60min`; actual midnight. ❌
  - **Injuries**: should be event-time of injury report; actual midnight. `injury_impact_calculator.py` does not
    filter by prior-fixture timing. ❌
  - **Pre-match odds**: `bm_time` / `bm_minutes_to_kickoff` used for HT-gate filtering only, NOT propagated as
    `available_at` column on output. ❌
  - **Post-match (xG, fixture_stats, sfi_progressive, results)**: should be `match_end_time`; actual midnight.
    Midnight is BEFORE kickoff for same-day post-match data → leak risk. ❌
  - **Weather**: should be forecast-issue time; no `forecast_issue_time` column in output. ❌
  Fix layer: **[per-service]** + **[UTL]** (per-source availability stamping helper).
- **[writer]** `writer.py:65-66` — `except LookaheadBiasError: pass` in `_enforce_pit_sports` with `strict=False`. The
  enforcer warns then raises; writer's `pass` eats it. **Future-timestamped observations never block batch writes.**
  `strict=False` is intentional per comment but means PIT enforcer is informational-only in batch. Fix layer:
  **[per-service]**.
- **[writer]** `batch_handler.py:492` — `export_derived_features(date_str)` called **without `horizon=`**. The horizon
  gate (`apply_horizon_gate`) and `validate_pit_compliance` at `584-594` are never called. Post-match actuals
  (home_goals, away_xg) are included in flat daily parquet without horizon gating. Downstream ML training reading
  this can access post-match data for same-day fixtures. Fix layer: **[per-service]**.
- **[pre-flight]** `_table_exists_in_gcs` (`batch_handler.py:154-173`) — `except Exception: return False` swallows
  GCS auth failure → unnecessary recompute. Fix layer: **[per-service]**.
- **[writer]** `batch_handler.py:629-631` — `manifest.write()` failure caught with `except Exception`, only warning.
  If it fires for the whole batch day, **no manifest rows for any table** — entire day invisible to data-status. Fix
  layer: **[per-service]**.
- **[path-SSOT]** `gcs_reader.py:651, 675, 697, 1186, 1192` — hardcodes `sports_reference/by_date/day=.../entity=...`
  paths inline (5+ sites). CLAUDE.md SSOT requires `from unified_api_contracts.sports import candidate_parquet_paths`
  — no such import anywhere. Per-league fallback at line 697 partially re-implements UAC `SportsPathLayout.PER_DAY_PER_LEAGUE`.
  Fix layer: **[per-service]**.
- **[coverage_gate not wired]** `compute/coverage_gate.py` exists, imports UAC correctly, but
  `check_calculator_coverage()` is **never called** in `derived_features_exporter.py` or `batch_handler.py`. Dispatch
  uses only `if not data.empty:` guards. Module is dead code. Fix layer: **[per-service]**.
- **[direct google.cloud import]** `gcs_reader.py:662, 946, 1082, 1179` — `from google.cloud import storage as
  gcs_storage` directly. UCI `get_storage_client()` exists and is imported at line 34 but bypassed for bulk reference
  reads. Fix layer: **[per-service]**.
- **[progress events]** No `INSTRUMENT_PROCESSED` / `FIXTURE_PROCESSED` structured events with row counts. SSE
  `emit_feature_ready` exists at `batch_handler.py:198, 221` but isn't `log_event` to the events bucket. Silent-success-
  with-zero-output detection from event stream impossible. Fix layer: **[per-service]**.

#### 🔀 Wrong layer

- `_ensure_timestamp` (`batch_handler.py:146-151`) — midnight UTC fallback workaround for missing `available_at`. Should
  not exist; replace with per-source stamping. **[UTL lift]**.
- `_validate_feature_quality` (`batch_handler.py:94-143`) — inline all-NaN counter + classify_and_emit_error. Subset
  of `FeatureWriteGate` already used in writer.py. Duplicate inline gate; delete. **[UTL]**.
- `tracking/feature_builder_registry.py` `BuilderEntry` `required_inputs` DAG → UAC. **[UAC]**.
- Dual-vocab `_MTDS_RAW_ODDS_ASSET_GROUP_SEGMENT` / `_MTDS_RAW_ODDS_LEGACY_HIVE_CATEGORY_SEGMENT`
  (`gcs_reader.py:939-941`) → 7th+ inlined copy of dual-vocab probe across workspace. **[UTL]**.
- Horizon sidecar `_write_horizon_schema_sidecar` (`writer.py:164-207`) — bare `except Exception` swallows failures.
  Horizon metadata should be parquet schema or UTL-backed contract, not best-effort JSON sidecar. **[UTL/UAC]**.

#### ❓ Couldn't verify

- Whether `add()` defaults `capture_status="captured"` or leaves blank.
- Whether UAC `FEATURE_UPSTREAM_REQUIREMENTS` covers all calc names (e.g. `elo`, `injury_impact`) or falls through
  to `READY` for uncatalogued calcs.
- Whether `compute_sfi_progressive_only.py` (`features_sports_service/scripts/`) is on canonical code path or one-off.
  Uses finer per-league granularity than `batch_handler.py`.

#### available_at stamping per source (features-sports)

| Source | Calculator | Stamping rule | Matches handover? |
|---|---|---|---|
| Lineups | derived_features via `compute_player_lineup_batch` | `_ensure_timestamp` → midnight UTC | NO — should be `kickoff - 60min` |
| Injuries | derived_features via `compute_injury_impact_batch` | midnight; not filtered by prior-fixture timing | NO — should be event-time |
| Pre-match odds | odds_features_exporter | `bm_time` used for HT filter only, NOT on output | NO — `publication_time` not stamped |
| Post-match (xG/fixture_stats/results/sfi_progressive) | derived_features | midnight; `_filter_completed_before` correct for history but stamps midnight not match_end | NO — CRITICAL leak risk |
| Weather | `compute_weather_for_fixtures` | midnight; no `forecast_issue_time` | NO — distinction not maintained |

#### Lookahead-bias coverage matrix (features-sports)

| Calculator / context | LookaheadBiasError raised | Notes |
|---|---|---|
| `orchestrator.py` live mode | ✓ (re-raises PointInTimeViolation) | Correct |
| `writer.py` batch mode `_enforce_pit_sports` | ❌ (`except LookaheadBiasError: pass`, strict=False) | Silently downgrades all to warning |
| `derived_features_exporter.py` (22+ calcs) | ❌ | No per-input `available_at <= kickoff - N` guard |
| `odds_features_exporter.py` | PARTIAL — HT break only | Other horizons not gated |
| `export_derived_features` horizon gate | DEAD IN BATCH | `validate_pit_compliance` only fires when `horizon` arg passed; `batch_handler.py:492` calls without |

#### Hardcoded sports paths (path-SSOT violations)

All in `features_sports_service/data/gcs_reader.py`:
- Line 651: `sports_reference/by_date/day={date}/entity={entity}/{entity}.parquet`
- Line 675: same template (inside 7-day lookback loop)
- Line 697: `sports_reference/by_date/day={date}/entity={entity}/league=` — partially re-implements UAC layout
- Line 1186: `prefix = "sports_reference/by_date/day="`
- Line 1192: `if "/entity=fixtures/fixtures.parquet" not in path:`

#### Migration items (features-sports-service contribution)

1. **MIG-FS1**: All `manifest.add()` calls for captured rows (`batch_handler.py:615-628`) → `record_captured`.
2. **MIG-FS2**: Add `timeframe` + `fixture_id` to all manifest row_keys.
3. **MIG-FS3**: Extend `_FEATURE_GROUP_TO_DATA_TYPE` to all 14 raw table groups.
4. **MIG-FS4**: Replace hardcoded sports paths with `candidate_parquet_paths()`.
5. **MIG-FS5**: Stamp `available_at` per source rules at write-time (needs UTL `availability_stamping.py`).
6. **MIG-FS6**: Pass `horizon=` to `export_derived_features` in batch.
7. **MIG-FS7**: Wire `coverage_gate.check_calculator_coverage()` into dispatch.
8. **MIG-FS8**: Replace direct `from google.cloud import storage` with `get_storage_client()`.
9. **MIG-FS9**: Make `manifest.write()` failure fatal or emit FAILED event.

#### UTL-lift items (features-sports-service contribution)

- **LIFT-FS1**: `_validate_feature_quality` (batch_handler.py:94-143) — duplicate of `FeatureWriteGate`; delete.
- **LIFT-FS2**: `tracking/feature_builder_registry.py` `required_inputs` DAG → UAC.
- **LIFT-FS3**: `_ensure_timestamp` (batch_handler.py:146-151) → delete; replace with per-source `available_at`
  stamping from UTL `availability_stamping.py`.
- **LIFT-FS4**: Dual-vocab `_MTDS_RAW_ODDS_*_SEGMENT` (gcs_reader.py:939-941) → UTL `hive_vocab.py` (7th workspace copy).

<!-- AUDIT_FINDINGS_INSERT_BELOW -->
