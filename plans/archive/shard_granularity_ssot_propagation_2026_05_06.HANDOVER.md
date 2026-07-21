---
doc_type: plan
title: Shard-Granularity SSOT Propagation — Executor Handover
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    execution-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-06"
type: handover
companion_plan: shard_granularity_ssot_propagation_2026_05_06.plan.md (TBD)
locked_by: live-defi-rollout
locked_since: 2026-05-06
---

## Deferred work — migrated to: `plans/active/master_to_live_defi_2026_05_23.md`,

`plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md` — successor: master_to_live_defi_2026_05_23,
data_status_page_ux_and_canonicalisation_2026_07_16 (Cluster A — the 8-item per-service audit checklist — is the audit
task definition itself, answered in full in this same document's Phase 0 report; closure independently confirmed at
`master_to_live_defi_2026_05_23.md:2000` "Close shard-granularity propagation... DONE 2026-05-07". Cluster B — the
5-item data-status/UI checklist — is actively continued by `data_status_page_ux_and_canonicalisation_2026_07_16.md`.
NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]` cleanup.)

# Shard-Granularity SSOT Propagation — Executor Handover

**Branch:** `live-defi-rollout` **Status:** Phase 0 audit complete (2026-05-06). **Companion plan:**
`shard_granularity_ssot_propagation_2026_05_06.plan.md` (drafting next; not yet committed).

---

## Before you start — sync CLAUDE.md

This handover's principles are codified in the workspace CLAUDE.md at `unified-trading-pm/cursor-configs/CLAUDE.md`,
section **"Shard-granularity SSOT (CRITICAL)"** (between "No fire-and-forget VM launches" and "Sports GCS path SSOT").
**Copy that section into your own CLAUDE.md** so sub-agents you launch during execution inherit the rules via
`SUB_AGENT_MANDATORY_RULES.md`. If your `.claude/CLAUDE.md` is already a symlink into PM, you have it — confirm with
`grep "Shard-granularity SSOT (CRITICAL" .claude/CLAUDE.md`. If not, copy the section verbatim.

---

## Why this plan exists

Most of this is already implemented across previous plans. **This plan is a redo-and-test pass to verify end-to-end
consistency, not greenfield.**

Goal: every shard atom is identical across (a) writer atomicity, (b) manifest row key, (c) data-status display, (d)
downstream pre-flight gate, (e) deployment-UI drill-down. Drift between any two = silent correctness bug. Recent
incidents trace exactly to this drift:

- TradFi MVP partial bundles (ES.OPT 18/839 historical bundles passed manifest as captured)
- MDPS empty-placeholder bars (1440 NaN OHLC bars/day/venue for years; manifest said `captured`)
- Databento per-schema silent drop (bundled `ohlcv_1m;trades` lost ohlcv on 429; orchestrator marked complete)

---

## Your role in this plan

You're the **verifier**, not the UI builder. Walk every service's writer + manifest + data-status surface and **check
whether the existing structures match the target shapes in this brief**. Where they don't match, report findings back to
me — don't try to fix the UI/download side yourself. Specifically:

- IF a writer writes at the right shard key → ✓ note it
- IF pre-flight reads at coarser granularity than the writer → ❌ flag it
- IF `available_at` isn't stamped, or is derived rather than written → ❌ flag it
- IF a manifest on disk has drifted from v5 shape → ❌ flag it + estimate migration shape
- IF a fallback reader exists for a non-canonical shape that should have been migrated → ❌ flag it
- IF a UTL-grade utility is duplicated per-service → ❌ flag it

Your deliverable is a per-service audit report (one section per service, structured by the verify/fix/lift/build
checklist below) plus a list of confirmed migration items. Code fixes you take on directly should be the per-service
writer / pre-flight / `available_at` / write-gate work — that's where the correctness bugs live. UI download + schema
view work stays with me.

---

## Co-evolving stream — TradFi MVP follow-ups

A separate parallel stream is shipping three TradFi MVP follow-ups. Be aware so you don't step on it OR duplicate work
in your audit:

### Item 1 — Cluster-aware bundle validation (lands in UTL, affects your scope)

> **2026-05-06 update — supersedes the framing below.** Item 1 is no longer a "parallel stream"; it's mainline contract
> change inside
> [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](./writegate_honest_coverage_endtoend_2026_05_06.plan.md)
> Phase 1A + Phase 2.A/2.B. `record_captured` gets `expected_root_clusters` + `cluster_extractor` as **mandatory kwargs
> for any data_type ∈ UAC.BUNDLED_DATA_TYPES** (runtime guard + new QG STEP 5.64 static check). Single SSOT,
> plug-in-everywhere; bundles 1440-NaN MDPS fix + sports per-fixture_id sharding + sports `available_at` correctness
> into one work-package. The original framing below is kept for context.

`ManifestWriter.record_captured` gets two new params: `expected_root_clusters: dict[str, int]` +
`cluster_extractor: Callable[[str], str]`. At write-time, rows are counted per cluster; any expected-active cluster
below its `min_rows` triggers `record_failed(ClusterCoverageError(missing=..., observed=...))` instead of writing the
parquet. ES.OPT 11-cluster taxonomy is the seed; generalises to futures combos, prediction canonical-question bundles
(BTC up/down clusters), sports fixture bundles.

**For your audit:** treat this as part of the write-gate trio (row-count > 0, NaN ratio < threshold, cluster coverage ≥
expected) when verifying each service. **Don't build a parallel mechanism** — once the UTL change lands, services just
need to pass the clusters dict for any shard that's a bundle (`options_chain`, `futures_chain`, prediction canonical
groups, sports per-fixture aggregates). Flag in your audit which services need this wired.

### Item 2 — Databento 429 silent-drop fix (MTDS, overlaps your scope)

`market-tick-data-service/.../tradfi/databento_adapter.py` `download_batch_df` lines 677, 683 currently swallow
per-schema failures (`if dbn_store is None: continue`, `except Exception: continue`). Patching to return
`(df, list[_PerSchemaFailure])` so the orchestrator can `record_failed` per (date, data_type). Shard-level isolation, no
silent absence.

**For your audit:** this is exactly the partial-shard / silent-absence bug the SSOT plan exists to catch. When you walk
MTDS adapters, this one is being fixed in parallel — note that, but **DO scan every other adapter** in MTDS for the same
anti-pattern (`except: continue` swallowing per-schema or per-instrument failures inside `download_batch_df`-shaped
loops). Report findings; I'll route them.

### Item 3 — VIX 15m source layering (shipped — read before any VIX-adjacent edit)

The (CBOE, ohlcv_15m) shard has THREE distinct date regions, each with different correctness rules. Drift between any
two = silent corruption (overwrites Barchart preload OR fakes captured for the gap OR records `empty_confirmed` for a
honest gap). All write/read/validate layers must understand the layering — this is the canonical short version (full
text in the workspace `CLAUDE.md` "VIX 15m source layering" rule).

1. **Barchart historical preload** (`BARCHART_VIX_FIRST_DATE` 2020-01-02 → `BARCHART_VIX_LAST_DATE` 2025-11-12) —
   one-time bulk import already in GCS; manifest already has `captured` rows. **Never re-fetch.** MTDS
   `_fetch_yahoo_vix_15m` short-circuits to empty WITHOUT calling Yahoo when the date is in this range; manifest is left
   untouched so the existing Barchart row stands.
2. **Yahoo Finance 15m rolling window** (`get_yahoo_vix_15m_start()` ≈ today − 60d → today). UAC
   `YAHOO_VIX_15M_WINDOW_DAYS = 60` is the SSOT; if Yahoo extends to 90d, bump that constant only.
3. **Honest gap** (2025-11-13 → today − 60d) — no source covers this. UAC `is_vix_15m_gap_date(date)` returns True; MTDS
   returns empty so the orchestrator records `empty_confirmed`. Data-status must understand this is an accepted gap
   (denominator clip), not a coverage hole.

**Routing surface**: `market_tick_data_service/adapters/umi_tick_provider.py` `_fetch_yahoo_vix_15m` is wired BEFORE the
generic Databento route — Databento's GLBX.MDP3 doesn't carry the spot VIX index, so the legacy path silently emptied
the data_type via `_DATABENTO_SUPPORTED_DATA_TYPES` filtering. Pre-2020-01-02 dates return empty without a Yahoo call.

**For your audit**: any features-volatility / strategy-service / data-status work that touches VIX 15m must treat the
gap range as an honest gap (not "missing coverage") — feature backfills should NaN-fill that range cleanly, not raise
DependencyError. If you find a calculator that expects VIX 15m density without a NaN gap, file under "Reader/schema
drift" (Category 3 of honest-absence).

### Workspace principles already codified (re-use, don't re-derive)

1. **Manifest concurrency**: read-once + per-date TTL-cached freshness check (60s default) + write-time CAS. PM
   CLAUDE.md `77cd8713`. Reference impl `_refresh_captured_cache` / `_is_now_captured` in `/tmp/fill_missing_ohlcv.py`
   (mirrored at `gs://deployment-scripts-central-element-323112/audit-scripts/fill_missing_ohlcv.py`).
2. **Trading-calendar SSOT**: UAC `is_non_trading_day` / `clip_dates_to_trading_days` from `venue_trading_calendar.py`.
   No naive weekday filters.
3. **Per-(venue, data_type) coverage windows**: UAC `VENUE_DATA_TYPE_COVERAGE_WINDOWS` registry — new entries here, not
   legacy `TRADFI_TICK_DATA_WINDOWS`.
4. **Multi-hour backfills run on same-region GCE VM** (asia-northeast1-c), not local Mac. Pattern
   `mtds-{operation}-{ts}` VM names with `VM_BACKFILL_CMD` metadata pulling script from GCS at boot.

### Coordination rule

If your audit surfaces a fix that overlaps Items 1 or 2, **don't ship it — ping me first.** We'll route through the
parallel stream so the change lands once, in the right layer, with the right test coverage.

---

## The cross-cutting invariant

For every (service, data type), the **shard atom** must match across:

1. Writer atomicity boundary (parquet finalize + `record_captured`)
2. Manifest row key (v5 columns:
   `asset_group, venue, chain, data_type, instrument_type, instrument_id, league_id, timeframe, feature_group, model_family, ...`)
3. Data-status page rollup
4. Downstream service pre-flight gate
5. Deployment-UI drill-down + parquet download + schema view

If pre-flight reads at `(venue, data_type, date)` while writer writes at full v5 granularity, partial captures look
"complete" upstream. Find every such mismatch.

---

## Per-asset-group shard-key matrix (UAC SSOT — Phase 0)

| Asset group              | Shard key                                                                                                                                                                                                                                                                                            | Bundling                                                                      | `empty_confirmed` triggers                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **CeFi spot/perp**       | (ag, venue, dt, IT, instrument_id, day)                                                                                                                                                                                                                                                              | per-instrument (35GB roots)                                                   | source 200+empty                                                        |
| **CeFi options/futures** | (ag, venue, dt, `options_chain`/`futures_chain`, root, day)                                                                                                                                                                                                                                          | bundled by root                                                               | per-bundle                                                              |
| **TradFi futures**       | (ag=tradfi, venue, dt, IT, root, day)                                                                                                                                                                                                                                                                | bundled by root                                                               | non-trading days via `venue_trading_calendar` (holiday + session close) |
| **TradFi ETFs**          | (ag=tradfi, venue, dt, IT, instrument_id, day)                                                                                                                                                                                                                                                       | per-instrument (IBIT, ETHA)                                                   | non-trading days                                                        |
| **TradFi options**       | (ag=tradfi, venue, dt, `options_chain`, root, day)                                                                                                                                                                                                                                                   | bundled                                                                       | non-trading + zero-vol strikes                                          |
| **DeFi**                 | (ag=defi, **chain**, venue/protocol, dt, instrument_id_or_protocol_id, day)                                                                                                                                                                                                                          | chain is first-class axis                                                     | pre-genesis dates per chain                                             |
| **Sports**               | (ag=sports, source, dt, league_id, day) — `fixture_id` NOT a shard atom (RESOLVED 2026-05-06 per `data_status_multi_axis_shard_propagation_2026_05_06.plan.md:124-126`: `(league_id, day)` already bounds the fixture set; per-fixture detail comes from parquet drill-down, not manifest expansion) | per-league-day                                                                | paused-league (`KNOWN_COVERAGE_GAPS`) + pre-`SOURCE_COVERAGE_START`     |
| **Prediction**           | (ag=prediction, venue, dt, **canonical_question_group**, day)                                                                                                                                                                                                                                        | canonical names (BTC up/down, S&P up/down) — analog of options-chain bundling | pre-launch + resolved-old                                               |

**Prediction canonical-question-grouping** is the most likely greenfield bit — verify whether UAC has a SSOT mapping raw
Polymarket market_id → canonical question group. If not, flag it as a build item.

---

## Layer discipline (CRITICAL)

Tag every plan item with placement before implementing:

- **[UAC]** — contracts, shard-key shapes, `feature_group → required_inputs` DAG, `SOURCE_COVERAGE_START` /
  `DATA_TYPE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS`, `available_at` semantics per source, prediction canonical-question
  SSOT, `venue_trading_calendar`
- **[UTL]** — cross-service runtime utilities: `ManifestWriter`, dual-vocab probe utility (lift the 5 phantom-audit
  drift axes into one shared module), write-gate helper (row count + NaN ratio + schema), `LookaheadBiasError`,
  schema-introspection helper, `run_lifecycle`
- **[per-service]** — only what genuinely differs: source-specific `available_at` stamping, calculator/adapter business
  logic
- **[deployment-api / deployment-ui]** — per-service download endpoint + schema-view route, data-status tab drill-down

**Do not duplicate cross-service utilities per-service.** If you find one inlined (e.g. NaN-ratio check copy-pasted
across calculators), lift to UTL.

---

## Per-service verify/fix/lift/build checklist

For **each** of: `instruments-service`, `market-tick-data-service`, `market-data-processing-service`,
`features-onchain-service`, `features-sports-service`, `features-delta-one-service`:

- [ ] Writer shard key matches v5 manifest columns — verify
- [ ] `record_captured` / `record_empty` / `record_failed` fires at full shard granularity — verify
- [ ] Pre-flight `_should_skip_shard` reads at full shard granularity (NOT `(venue, data_type, date)`) — verify, fix if
      coarser
- [ ] Dual-vocab probe goes through shared UTL utility, not inlined — verify, lift if duplicated
- [ ] `available_at` column stamped at write-time per source rules — verify, build if missing
- [ ] Write-gates fire on row-count==0, NaN ratio above threshold, schema mismatch — verify, lift to UTL helper
- [ ] Downstream pre-flight checks ALL DAG inputs (not just one upstream) at correct shard granularity — verify
- [ ] Per-instrument progress events emitted with row counts (`INSTRUMENT_PROCESSED` etc.) — verify

---

## Data-status + UI checklist (audit only — report findings, don't fix)

Per service, walk the data-status tab and verify against target shape. Report gaps; do not implement UI changes.

Target shape:

- [ ] Manifest read at full v5 shard granularity (NOT `(venue, data_type, date)` rollup)
- [ ] `capture_status` displayed honestly: `captured` / `empty_confirmed` / `attempted_failed` with `error_reason`
- [ ] Drill-down path: `asset_group → venue/chain → data_type → instrument_type → instrument_id → day → leaf parquet`
- [ ] Per-leaf actions exist or are stubbed: download parquet, view schema (columns, types, row count, NaN ratio per
      column, `available_at` min/max)
- [ ] `empty_confirmed` rendered distinctly from missing — non-trading days, paused leagues, pre-genesis dates show as
      expected-empty, NOT red

For each service, report: which of the above match target, which don't, and what the current shape actually is. I'll
handle the UI/download fixes separately.

### Pre-audit findings (2026-05-06 — already surfaced, fold into your audit report)

A workspace pre-audit identified 5 specific gaps in deployment-UI data-status. Verify they still hold and add to your
per-service report — they're real and actionable, not blue-sky speculation.

**Denominator gaps (silently inflate the "missing" %):**

1. **MTDS sports source-coverage missing** — `deployment-api/deployment_api/services/data_status_service.py:888-935`
   `_mtds_expected_dates_cached` doesn't call `_clip_dates_to_source_coverage` for the `SPORTS` asset_group branch.
   Pre-sports-launch dates remain in the denominator → false low %. Fix: thread `data_type` and `source_key` through and
   call `clip_dates_to_source_coverage` for sports, mirroring the sports-branch logic at lines 314-355.

2. **Phase 8D 50-cap on per-instrument** — `data_status_service.py:1026-1031, 1104-1106` `_per_instrument_coverage` uses
   `get_expected_instruments_for_venue(venue, dt, cap=50)` (hardcoded MVP cap, line 76). BINANCE-FUTURES has 100+
   perpetuals → real denominator is half. Fix: remove the cap or pass the actual venue instrument universe size from
   instruments-service.

3. **Prediction granularity is per-(venue, dt, day) only** — no per-`conditionId` shard tracking; POLYMARKET / KALSHI
   markets are undifferentiated. Fix: depends on the UAC `canonical_question_group` SSOT (build item in this plan); once
   that lands, thread it through the prediction denominator computation.

**Honesty rendering gaps (UI work — audit-only for you, I'll handle the UI fixes):**

4. **`empty_confirmed` rolled into "found" in the UI** — backend correctly separates `captured` / `empty_confirmed` /
   `attempted_failed` and computes `attempt_coverage_pct` / `capture_coverage_pct` / `empty_rate` (per
   `deployment-api/tests/unit/test_data_status_capture_status.py:70-78`), but the UI surfaces only aggregate
   `completion_pct`. A venue with 50 captured + 50 `empty_confirmed` reads 100% — true at the manifest level, but you
   can't tell "95% real captures" from "95% mostly empty_confirmed legitimately". Backend has the data; UI needs the
   breakdown columns.

5. **No `attempted_failed` rendering** — same surface issue. Failed shards count as missing in the UI numerator without
   being distinguished from never-attempted.

**What's correctly working (don't redo):**

- ✓ Sports denominator clips pre-`SOURCE_COVERAGE_START`, applies `KNOWN_COVERAGE_GAPS`, uses fixture calendar + cadence
  bucket-matching (2026-05-05 fix `_data_status_service.py:483-512`).
- ✓ TradFi denominator: per-(venue, data_type) coverage windows + non-trading-day exclusion via
  `venue_mapping.get_expected_trading_dates`.
- ✓ CLI / API / JSON response keys all use `asset_group` (migrated from `category` per `deployment-api f9fc472`).
  Internal Python variable naming still says `category` in places — acceptable per CLAUDE.md asset-group section, no fix
  needed.

---

## Lookahead-bias rules (features-\* + MDPS)

For every feature compute at horizon t-N:

- Every input row consumed must satisfy `input.available_at <= kickoff_or_target_ts - N`
- Raise `LookaheadBiasError` loud (currently fires for `lst_yields`; extend to every features-\* calculator)
- `feature_group → required_inputs[]` DAG SSOT in UAC drives the check

### Sports temporal availability stamping rules

| Source                                                             | `available_at`                                                                                    |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Lineups                                                            | `kickoff - 60min` (conservative; clip earlier leaks)                                              |
| Injuries                                                           | event-time of the injury report (so feature for fixture F sees only injuries from prior fixtures) |
| Pre-match odds                                                     | publication time per snapshot (opening days before, closing at kickoff)                           |
| Post-match (understat xG, fixture_stats, results, sfi_progressive) | `match_end_time` — NEVER available pre-kickoff                                                    |
| Weather forecasts                                                  | forecast-**issue** time, distinct from forecast-target time                                       |

If `available_at` is missing on disk for a source, **stamp it at backfill-replay time** before SSOT propagation
completes. Don't infer at read-time.

---

## Manifest migration (NOT fallback)

- Identify any manifest that drifted from v5 canonical shape (pre-v5 row schema, off-canonical paths, wrong row keys)
- Write a one-time migration script per drift (precedent:
  `instruments-service/scripts/migrate_local_sfi_to_canonical.py`)
- **Remove** fallback reader logic that handled the legacy shape after migration
- One documented exception that survives: hive-vocab `category=` vs `asset_group=` on-disk legacy preservation per
  CLAUDE.md asset-group section. Reader tries canonical first, falls back to legacy. **Do NOT rekey on-disk data.**
- Everything else: migrate, then delete the fallback path. Workspace rule: no try/except fallback imports, no compat
  shims.

---

## Validation gates per `record_captured`

Three checks fire at the write boundary; any failure → `attempted_failed` with `error_reason`:

1. **Row count > 0** unless source response was legitimately empty (then `record_empty`, not `record_captured`)
2. **NaN ratio per column < threshold** (per-feature-group threshold in UAC; carry-tracer pattern)
3. **Schema matches contract** (columns + types match UAC schema declaration)
4. **(when Item 1 lands)** Cluster coverage ≥ expected for bundled shards

Without these, manifest is presence-only and partial bundles / empty placeholders pass silently. This is the lesson from
MDPS 2026-05-05 (1440 empty placeholder bars) and TradFi MVP 2026-05-06 (ES.OPT 18/839 partial bundles).

---

## Anti-patterns to refuse

- Pre-flight at coarser granularity than writer
- NaN-ratio gate inlined per calculator instead of UTL helper
- `available_at` derived at read-time instead of stamped at write-time
- Fallback readers for non-canonical manifest shapes (migrate instead)
- Per-service duplicate of cross-service utility
- Empty placeholder rows masking absence (1440 NaN OHLC bars instead of `record_empty`)
- Writing fresh manifests in a coarser shape than v5
- `except: continue` swallowing per-schema or per-instrument failures inside per-shard loops

---

## Workspace rules to respect

- `bash scripts/quality-gates.sh` per-repo (uses repo `.venv`, never workspace venv)
- `bash scripts/quickmerge.sh "msg" --agent --files "p1 p2"` — never `git push` directly. Agent mode requires `--files`.
- Push manually committed branches before quickmerge if branch has commits not on origin
- Don't quickmerge while local dep repos are dirty unless explicitly approved
- Plan format: Cursor checkboxes (`- [x]` / `- [ ]`) on every todo
- Locked to `live-defi-rollout` branch (lock plan via frontmatter)
- Citadel-grade planning: pre-audit manifest, phased DAG with parallel/sequential markers, QG gates between phases,
  success criteria per phase, downstream consumer fix list
- Sub-agents launched during execution must be injected with
  `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` content at top of prompt
- Asset-group vocabulary: `asset_group` everywhere new (not `category`); dict KEYS stay lowercase
- No `os.getenv()` — `UnifiedCloudConfig`
- No `# type: ignore` for architectural violations — fix root cause
- `basedpyright` (not `pyright`), with `run_timeout 120 basedpyright <source_dir>/`

---

## Output expectations per phase

- QG green per repo touched
- All affected downstream consumers updated in the same plan (no "fix later")
- Manifest reads + writes use same shard key
- Data-status surfaces match writer granularity (audit report, not UI fix)
- UI drill-down works for the service touched (audit report only)
- No fallback paths remain for migrated manifests
- Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud
- `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
  `available_at > kickoff - 24h`

---

## Final deliverable from this audit

A per-service report (one markdown section per service) with:

1. ✓ items that match target shape
2. ❌ items that don't match (writer/pre-flight/available_at/write-gate/migration/UI)
3. 🔀 items implemented in the wrong layer
4. ❓ items where you couldn't verify (need clarification or codex pointer)

Plus a consolidated migration list (manifest drift instances + estimated migration shape) and a consolidated lift list
(UTL-grade utilities currently duplicated per-service).

I'll fold your report into the plan's pre-audit manifest and we'll phase the actual fix work from there.

---

# Phase 0 Audit Report (2026-05-06)

Seven parallel Sonnet audits ran against the verify/fix/lift/build checklist. Findings below are file:line specific.
Sections are ordered by service then UTL-lift scan; severity prefixes ✓ matches / ❌ mismatches / 🔀 wrong layer / ❓
unverified are in each section.

## Cross-cutting themes (read this first)

These show up in 3+ services — fix in UTL/UAC, not per-service:

1. **v6 columns `combo_type` / `leg_weights` are dead** — defined in `manifest_writer.py:516,519` but no service writes
   them. MTDS chain bundles, MDPS chain-bundle outputs, instruments-service combo discovery all leave them at `""`.
2. **Pre-flight is coarser than writer in 4 of 6 services** — MTDS skip-if-exists at `(venue, data_type, date)` but
   writer at v6 7-tuple; MDPS pre-flight lacks `timeframe`; features-delta-one and features-sports lack
   per-fixture/per-instrument granularity entirely; only instruments-service `_should_skip_shard` reads at full
   granularity.
3. **Bundle / partial-shard detection is not wired anywhere** — every chain-bundle adapter (Tardis options/futures,
   Databento options/futures, perp_funding, sports per-(bookmaker, league)) accepts row_count > 0 as success. The TradFi
   MVP cluster-aware bundle gate (Item 1, parallel stream) lands in UTL `record_captured`; once it ships, every bundle
   adapter must pass `expected_root_clusters` + `cluster_extractor`. Audit confirms zero adapters do this today.
4. **`available_at` stamping is partial and inconsistent** — instruments-service stamps `data_available_at` correctly
   per-source for sports; MDPS+features-delta-one use `timestamp + 500ms` synthetic; features-onchain doesn't stamp at
   all; features-sports uses processing-date midnight via `_ensure_timestamp` (defeats the PIT enforcer). Not the
   SSOT-prescribed stamping (kickoff−60min for lineups, event-time for injuries, match_end_time for post-match,
   forecast-issue-time for weather).
5. **`record_empty` / `record_failed` adoption is partial** — instruments-service (✓), MTDS DeFi handlers (✓),
   features-sports batch_handler (✓). MDPS, features-delta-one, features-onchain only call `manifest.add()` (or its v6
   equivalent) on success; missing/failed shards are invisible to the manifest. Phantom audit cannot detect "never
   attempted" vs "attempted and failed" for these services.
6. **Empty placeholder bug class still latent in MDPS** — `_create_empty_output` returns n_candles-row NaN DataFrames in
   15 adapters; the upstream `tick_data.empty` guard catches the common path, but adapter-internal "no ticks within
   valid intervals" branches (e.g. `swap_adapter.py:106`) can still feed 1440-row all-NaN DataFrames to the writer. The
   2026-05-05 fix was data_type partition gating; the placeholder return shape itself was not changed.
7. **Prediction `canonical_question_group` SSOT does not exist** — confirmed across instruments-service, MTDS, UAC.
   Polymarket and Kalshi shard at individual `condition_id` / `ticker` granularity. The shard key in the handover brief
   is greenfield; UAC needs a new symbol before any service can adopt it.
8. **DAG SSOT `feature_group → required_inputs[]` is not in UAC** — features-onchain has it in `cli/parser.py` +
   `feature_builder_registry.py`; features-sports has it in `tracking/feature_builder_registry.py`; features-delta-one
   has it inlined locally. Three services, three DAGs, no UAC SSOT.
9. **Dual-vocab probe is duplicated 7+ times** — features-onchain (2 places), features-cross-instrument,
   deployment-service, MDPS reprocess scripts, instruments-service migration scripts, execution-service. SSOT keys exist
   (`RAW_TICK_ASSET_GROUP_HIVE_KEY` / `_LEGACY` in `raw_tick_hive.py`); the probe utility does not.
10. **Phantom audit is a script, not a UTL utility** —
    `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (with its 5 drift axes + ASSET_GROUP_CONFIG
    dict) is the canonical impl but not callable from other services without shelling out.

---

## instruments-service

### ✓ Matches

- `_should_skip_shard` reads at full shard granularity — `engine/orchestrator.py:467–487`. Per-league sport pre-flight
  `_should_skip_date_for_per_league` iterates every expected canonical league before returning True (line 490–527; fixed
  2026-05-05 regression).
- `record_empty` / `record_failed` used consistently across all sources (FootyStats, Understat, Transfermarkt, SFI,
  etc.); no `record_captured` call site for zero-row paths.
- `data_available_at` stamped at write-time per source: predictions T−72h from `kickoff_utc` (3918), fixtures T−7d
  (3271), per-fixture stats date+17:00 UTC (3446), FootyStats matches T+3h (4207), SFI kickoff+timer (5283).
- `InstrumentsWriteGate` wraps every `sink.write()` via `_gated_sink_write` (257–286).
- Shard-level isolation respected throughout; `classify_venue_error` used.
- Phantom audit `reconcile_phantom_manifest_rows_all.py:64–154` correctly probes both `category=` and `asset_group=`
  across four path shapes per asset_group.

### ❌ Mismatches

- **Prediction shard key deviates** — POLYMARKET writer uses `data_type=<base_asset>` (BTC, ETH, SPX…) at
  `orchestrator.py:1990–1995`; brief specifies `canonical_question_group`. UAC has no such symbol. **Greenfield build
  needed in UAC first.**
- **Bulk pre-flight `check_shard_freshness` coarser than per-league skip** — UTL `check_shard_freshness` at line
  2259–2267 doesn't include `league_id` in match unless explicitly passed; orchestrator line 1224 calls without it.
  Per-league skip is recovered downstream by `_should_skip_date_for_per_league` but bulk gate gives false-positive
  freshness.
- **Stale comment** — `orchestrator.py:4933` says "ManifestWriter v5 tolerates extra kwargs"; current schema is v6
  (functionally harmless but misleading).
- **`_validate_predictions_null_rates`** at `orchestrator.py:4064–4112` inlines NaN-ratio gate with hardcoded
  thresholds; should be UTL helper (lift candidate).

### 🔀 Wrong layer

- `_validate_predictions_null_rates` NaN-ratio gate (4064–4112) — lift to UTL.
- `reconcile_phantom_manifest_rows_all.py` 5-axis drift probe + `ASSET_GROUP_CONFIG` (64–391) — lift to UTL.
- `_extract_prediction_shard` / `_compute_prediction_shards` (2497–2524) — belongs in UAC once
  `canonical_question_group` lands.

### ❓ Unverified

- Existence of UAC `canonical_question_group` SSOT (confirmed absent; needs build item).
- Whether `INSTRUMENT_PROCESSED` per-instrument progress events are emitted at a lower layer (URDI / UTL
  `DomainValidationService`) or are genuinely absent. CLAUDE.md cites them as CRITICAL post-2026-05-05; no emission
  found in instruments-service source.
- Whether instruments-service manifest rows should carry v6 `quote_asset` / `margin_type` / `combo_type` / `leg_weights`
  (likely MTDS-only — needs UAC owner confirmation).

### Migration items

- 5 phantom-audit drift axes still on disk (per `reconcile_phantom_manifest_rows_all.py`).
- Pre-v5 manifest rows still present; `dedupe_manifest_schema_drift.py` + `purge_legacy_unsharded_manifest_rows.py`
  exist but not in orchestrator path.

### `except: continue` — none found inside per-shard loops (all paths route through `classify_and_emit_error` + `record_failed`).

---

## market-tick-data-service

### ✓ Matches

- Hive SSOT via `raw_tick_hive.py:15` (`asset_group=` canonical, `category=` legacy fallback).
- CeFi spot/perp per-instrument shard at `orchestrator.py:864–867`; options/futures bundle by underlying.
- v6 `quote_asset` / `margin_type` wired through orchestrator (1616–1641, 1922–1928) and
  `PartitionedTickWriter.record_shard_count` (1058–1059). **Only service that writes these v6 columns.**
- TradFi `tradfi_shared.py:260` uses canonical key.
- DeFi chain as first-class manifest axis (`_defi_manifest.py:120–162`); `canonical_write.py` separates venue from chain
  (14, 53–59, 235).
- All three manifest paths wired across DeFi handlers (`record_captured` / `record_empty` / `record_failed`).
- Honest-coverage Tier-2/Tier-3 fan-out at `orchestrator.py:2012–2251`.
- Sports shards at `(bookmaker, league_id)` (1739–1772).
- Databento `except + continue` fix shipped (`databento_adapter.py:30–48`); `_PerSchemaFailure` propagates per-schema
  failures correctly.
- Pre-flight at `(venue, data_type)` granularity (1383–1435).
- `DefiManifestRecorder` context manager flushes on exit (95–115), batch_size=1.

### ❌ Mismatches

- **Prediction `canonical_question_group` not implemented** — `polymarket_adapter.py:454–602` and
  `kalshi_adapter.py:242–269` shard per `condition_id` / `ticker`. No grouping logic, no UAC reference.
- **Sports per-fixture_id shard granularity collapsed** — `orchestrator.py:1739` groups by `(bookmaker, league)` only;
  per-fixture sub-grouping silently dropped. Brief spec is `(ag, source, dt, league_id, fixture_id|day-aggregate, day)`.
- **GMX multi-chain sentinel coarse** — `perp_funding_handler.py:225` writes `chain=""` for GMX (Hyperliquid/Aster get
  `chain = protocol.upper()`). Comment on 223 acknowledges per-chain Tier-2 fan-out is a follow-up.
- **`combo_type` / `leg_weights` v6 columns never written** — `orchestrator.py:1918–1928` calls `writer_manifest.add()`
  without either. No MTDS adapter populates them. UTL schema supports them.
- **Skip-if-exists granularity** — `tick_data_handler.py:166` calls `check_shard_freshness()` at
  `(venue, data_type, date)`. For DERIBIT inverse vs linear (same `underlying`, different `quote_asset`/`margin_type`),
  captured linear suppresses re-download of missing inverse at the pre-flight gate. Tier-2/3 sentinel at 1857–1876 does
  use full v6 key, but pre-flight does not.
- **Orchestrator DeFi venue-split list is hardcoded** — `orchestrator.py:1880–1908` has inline tuple of 27 protocol
  prefixes; will silently fail to split any new protocol. Duplicate check at 2093 uses
  `venue in _VENUE_MAPPING.all_defi_venues` — inconsistent. Rationalize on the mapping.
- **Bundle row-count gate absent** — Tardis & Databento options/futures chain writers (`tardis_shared.py:596–702`,
  `databento_adapter.py:869–985`) accept partial bundles silently. ES.OPT 18/839 incident class.
- Docstring drift: 9 DeFi handler docstrings still show `category=defi/` paths (actual writes use canonical
  `asset_group=defi`). Documentation drift only, not runtime.

### 🔀 Wrong layer

- `umi_tick_provider.py:225` calls `get_adapter(category="prediction_market")` — should use `asset_group=` vocabulary.
- Docstring `category=` paths across 10 handlers — lift to a shared `CANONICAL_DEFI_PATH_EXAMPLE` constant.

### ❓ Unverified

- UAC `canonical_question_group` SSOT (absent in MTDS; absent in UAC per other audits).
- `check_shard_freshness()` internals (probes full v6 key or only `(venue, data_type, date)`).
- On-disk migration status of `category=*` legacy objects (migration scripts exist for
  cefi/defi/tradfi/sports/prediction; run status unknown).

### Migration items

- `category=` → `asset_group=` GCS objects across all asset groups; migration scripts exist; run status unknown.
- Polymarket residual `category=prediction` objects per `migrate_polymarket_canonical.py`.

### `except: continue` — **none new found.** Exhaustive scan across all adapter dirs returned zero hits beyond the now-fixed Databento path.

### Bundle / partial-shard status — **not wired anywhere.** No row-count, NaN-ratio, or cluster-coverage gate on any bundle adapter. Item 1 (cluster-aware bundle validation) needs to land in UTL before this can be resolved.

---

## market-data-processing-service

### ✓ Matches

- `_data_type_requires_partition` gate covers 22 canonical types (`orchestration_scanner.py:75–82`).
- `dex_swaps` canonical registration fixed (`swap_adapter.py:24`) — 2026-05-05 root cause closed.
- Chain-bundle `ticks.parquet` legacy detection routes to streaming split before eager download
  (`live_workers.py:531–601`) — both 2026-05-05 cross-symbol corruption and 2026-05-06 OOM addressed.
- **Per-instrument `INSTRUMENT_PROCESSED` events with row counts + per-column non-null counts** at
  `live_workers.py:112–162` (`_TRACKED_NON_NULL_COLUMNS`). Directly closes the silent-success-with-zero-output gap.
- `ManifestWriter.add()` in canonical path stamps `processing_date`, `venue`, `chain`, `instrument_type`, `data_type`,
  `timeframe`, `league_id`, `underlying`, `instrument_id`, `row_count` (`canonical_writer.py:309–335`). Explicit
  per-shard `flush()` prevents SIGKILL/OOM losing records.
- Two-stage schema gate before GCS upload (`candle_write_mixin.py:262–286`, `canonical_writer.write_candle_parquet`
  `strict=True`).
- Empty tick data routes to `_handle_empty_tick_data` (no placeholder parquet).

### ❌ Mismatches

- **`canonical_writer.add()` missing v6 `quote_asset` / `margin_type` / `combo_type` / `leg_weights`**
  (`canonical_writer.py:313–326`). UTL accepts them; MDPS doesn't pass them. DERIBIT inverse vs linear collide at the
  same row-key.
- **`orchestration_service._write_manifest_records` is v3-shaped** (`orchestration_service.py:329–388`). Parallel
  manifest write per (venue, data_type, timeframe) summary, lacking `instrument_type`, `chain`, `league_id`,
  `instrument_id`, `quote_asset`, `margin_type`. Same `ManifestWriter` buffer → row-key collisions with the canonical v6
  write. Docstring still says "v4 shard tuple."
- **`_create_empty_output` placeholder pattern still latent** — 15 adapters return n_candles-row NaN DataFrames
  (cefi/trades, derivative, book_snapshot, liquidations, futures_chain, options_chain; defi/swap, liquidity,
  market_state; tradfi/trades, tbbo; sports/odds_snapshot, odds_movement, arbitrage). Upstream `tick_data.empty` guard
  catches the common path, but adapter-internal "no ticks within valid intervals" branches (e.g. `swap_adapter.py:106`)
  can reach `_write_candles` with 1440 NaN rows. **The fix is to return 0-row CandleOutput, not n_candles-row NaN.**
- **Pre-flight missing `timeframe` axis** — `dependency_checker.py:313–397`, `process_handler.py:256–293` probe
  `(date, venue, data_type)` only. Incremental timeframe backfill blocked by freshness check.
- **Scanner data_type set incomplete** — `_CEFI_TRADFI_DEFI_DATA_TYPES` (orchestration_scanner.py:46–72) missing
  `dex_pool_swaps`, `evm_defi_lending`, `evm_defi_amm`, `staking_yields` (all in `_DATA_TYPE_TO_MDPS_PREFIX`). Falls
  back to "all parquets" branch for unknown types.
- **Adapter registry mismatch** — DEFI `liquidity`, `market_state`, `fx_rates` registered in their adapter files but
  **not imported in `adapters/__init__.py`**. Decorator never fires → registry has no entry → "<1s, 0/0 succeeded"
  symptom. Same class as 2026-05-05 `dex_swaps`.

### 🔀 Wrong layer

- **No NaN-ratio threshold gate at write-time anywhere in MDPS.** `ParquetSchemaEnforcer` only checks presence/types.
  Lift to UTL `StreamingParquetWriter` so MDPS / MTDS / features-\* share threshold semantics.
- Dual-vocab probe duplicated in `orchestration_scanner.py:75–95` and `process_handler.py:256–277`.
- `_normalise_timeframe("24h" → "1d")` in `canonical_writer.py:59–67` — should be UTL.

### ❓ Unverified

- Whether `INSTRUMENT_PROCESSED` events fire on the streaming-bundle path (`_process_chain_bundle_streaming` →
  `_streaming_write_per_tf` → `_write_candles` → `canonical_writer.write_candle_parquet`; emission lives in
  `_process_all_timeframes` only).
- Whether `_write_manifest_records` is invoked for SPORTS / PREDICTION asset groups (would corrupt `league_id` /
  canonical_question_group axes).

### `except: continue` — multiple silent-drop instances flagged

- `live_workers.py:512–519` — per-symbol streaming failure swallowed in `_iter_chain_symbol_dfs`; symbol silently
  dropped from candle output, no `record_failed`.
- `live_workers.py:773–779`, `835–841` — per-instrument exception in `_process_chain_timeframe(_by_symbol)` calls
  `classify_and_emit_error` but doesn't append to caller's error accumulator → looks like success.
- `dependency_checker.py:461`, `515` — pre-flight storage errors classified but caller treats as "data unavailable"
  (False) or "assume available" (True), no event distinguishing "check failed" from "data absent."
- `candle_write_mixin.py:141–143` — write failure logged, returns None, **no `record_failed` row** → shard permanently
  invisible to manifest.

### Migration items

- v3-shaped summary rows from `orchestration_service._write_manifest_records` co-exist with v6 canonical rows.
- Stale comment in `canonical_writer.py:7` says "v4 manifest row."

---

## features-onchain-service

### ✓ Matches

- `FeatureWriteGate` with `nan_threshold=0.95` + row-count==0 guard + `PointInTimeEnforcer`
  (`feature_writer.py:52–66, 119–133, 270–324`). Gate evaluates on every write path (154–180).
- `LookaheadBiasError` imported from UTL (no local re-declare); raised in production (strict=True) for **all**
  feature_groups (`macro_sentiment`, `lending_rates`, `lst_yields`, `onchain_perps`). Handover claim that it fires only
  for `lst_yields` is no longer true.
- Per-day write isolation in `_process_daily_feature_group` and `_process_lst_yields` (1087–1177, 482–567) — fixes the
  prior concat-then-write-once bug.
- Dual-vocab probe in MTDS canonical reader (`mtds_canonical_reader.py:116–135`) — but inlined, not via UTL helper.
- `FEATURE_GROUP_WINDOW_SUMMARY` event emits `rows_total`, `days_written`, `days_attempted` per feature_group
  (`orchestrator.py:1161–1172`); `LST_DAY_PROCESSED` per-day with row count + token list (654–666).
- Schema validation in `onchain_writer.py:41` via `BaseGCSWriter` + local `ONCHAIN_FEATURES_SCHEMA`.
- Shard-level failure isolation in batch_handler (113–136).

### ❌ Mismatches

- **Manifest `writer.add()` missing `chain`, `timeframe`, `instrument_id` for all feature_groups**
  (`orchestrator.py:167–171`). Single call passes only `processing_date`, `row_count`, `feature_group`. v6 shard key
  requires `chain` (DeFi first-class), `timeframe`, `instrument_id_or_protocol_id`. **Primary manifest-drift gap.**
- **`record_empty` / `record_failed` never called** — when feature_group returns False or raises, no manifest row is
  emitted. Neither symbol exists anywhere in service source. Empty/failed shards invisible to manifest.
- **`output_schemas.py:60` has `chain` column nullable** but calculators don't populate it. `lending_rates` strips chain
  at calculator layer.
- **Primary writer (`feature_writer.py`) doesn't validate against UAC contract** — only `validate_feature_dataframe`
  (timestamp checks). Secondary `OnChainWriter` validates schema but is not on the primary code path.

### 🔀 Wrong layer

- `FEATURE_GROUPS` list + per-group `_metadata` in `cli/parser.py:9–22` and `feature_builder_registry.py:59–76` — should
  be UAC SSOT for `feature_group → required_inputs[]`.
- `nan_threshold=0.95` hardcoded inline (`feature_writer.py:61`) — should be UTL `WriteGateConfig` per-domain default or
  UAC contract.
- `ONCHAIN_FEATURES_SCHEMA` defined locally (`output_schemas.py:34–63`) — overlaps UAC manifest shard dimensions; no UAC
  contract validates output shape pre-`record_captured`.

### ❓ Unverified

- `available_at` per UTL manifest SSOT semantics — service stamps `timestamp_out = timestamp + 500ms` synthetic delay
  (255–257) but no `available_at` in output schema or manifest row.
- Whether downstream pre-flight reads UAC `feature_group → required_inputs[]` table — `DependencyChecker.UPSTREAM_DEPS`
  (41–63) is bucket-level only; UAC import path for the registry not found.

### `except: continue` — typed and classified, acceptable

- `mtds_canonical_reader.py:128–130` — typed exceptions, logged, isolated.
- `mock_data_provider.py:291,311`, `service.py:89` — broad catch but at boundaries with `classify_and_emit_error()`.
- No bare `except:` anywhere.

### Migration items

- Add `chain`, `timeframe`, `instrument_id` to `writer.add()` (`orchestrator.py:167–171`).
- Add `record_empty` / `record_failed` paths.
- Propagate `chain` from MTDS shard into output parquet for `lending_rates` / `lst_yields` / `onchain_perps`.
- Move `FEATURE_GROUPS` + per-group sources into UAC.

---

## features-sports-service

### ✓ Matches

- Shard-level isolation: per-table/per-feature_group catches typed exceptions, NEVER raises
  (`batch_handler.py:369,456,519,589`).
- `record_empty` / `record_failed` distinction honoured (`batch_handler.py:356,378,449,464,512,527,582,597`).
- `ManifestWriter` from UTL imported once per batch (286).
- Pre-flight `manifest.lookup()` checks `capture_status in ("captured", "empty_confirmed")` (291–320).
- `FeatureWriteGate` applied at write (NaN 50%, alignment 90%, leakage on) (`writer.py:33–40, 125`).
- `PointInTimeViolation` re-raises in live mode after `LOOKAHEAD_BIAS_VIOLATION` log (`orchestrator.py:140–151`).
- Dual-vocab read in `gcs_reader.py:39–41,902–904`.
- HT-odds PIT gate using per-fixture `ht_break_minutes` from SFI (`odds_features_exporter.py:43–116`).
- `validate_batch_no_leakage` in strict mode raises `LeakageError` (156–212).
- `asof_lookup` `timestamp_col <= as_of` filter (`pipeline/_asof.py:81`).

### ❌ Mismatches (MAJOR)

- **Shard key missing `timeframe` everywhere** — every `record_empty` / `record_failed` / `add` row_key uses only
  `{date, feature_group}` ± `league_id`. Brief target REVISED 2026-05-06: `(feature_group, timeframe, league_id, day)`.
  **`fixture_id` REMOVED from target shard key per `data_status_multi_axis_shard_propagation_2026_05_06.plan.md:124-126`
  decision** — `(league_id, day)` already bounds fixture set; per-fixture drilldown comes from reading the parquet, not
  from manifest expansion.
- **`manifest.add` instead of `record_captured`** for captured rows (`batch_handler.py:614–627`). v6 SSOT method
  explicitly sets `capture_status="captured"`; legacy `add` may not — needs UTL verification.
- **`export_derived_features` called without `horizon=` in batch mode** (`batch_handler.py:491`). Horizon gate +
  `validate_pit_compliance` therefore dead in batch (`derived_features_exporter.py:583–594`). Single flat parquet mixes
  all horizons, post-match actuals (home_goals, away_xg) leak freely.
- **`_FEATURE_GROUP_TO_DATA_TYPE` covers only 3 of 14+ groups** (`batch_handler.py:29–33`). 11 raw groups
  (`fixture_stats`, `injuries`, `fixture_lineups`, `player_stats`, `standings`, etc.) write `data_type=""` → invisible
  to data-status reader.
- **No per-`(feature_group, horizon)` shard writes** — single daily parquet per feature_group; no `record_empty` for
  invalid combos.

### 🔀 Wrong layer

- `_ensure_timestamp` synthesises midnight-UTC for missing `timestamp` (`batch_handler.py:145–150`) — defeats PIT
  enforcer (`writer.py:101`); should derive from kickoff/match_end per source.
- `HORIZON_SCHEMA_FILENAME` sidecar best-effort with bare `except Exception` (`writer.py:155–207`) — silent failure
  means downstream ml-training has no horizon gate.
- `tracking/feature_builder_registry.py` `required_inputs` DAG should be in UAC.

### ❓ Unverified

- Whether `ManifestWriter.add()` sets `capture_status="captured"` (UTL read needed).
- Whether data-status reader falls back to scanning by `feature_group` when `data_type=""`.
- UAC `SPORTS_DATA_TYPE_META` contents (3 vs 14+ groups expected at data-status layer).

### available_at stamping per source — **all wrong**

| Source                                          | Spec                          | Actual                                                                                            |
| ----------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------- |
| Lineups                                         | `kickoff − 60min`             | midnight via `_ensure_timestamp` (no kickoff-relative clip)                                       |
| Injuries                                        | event-time of injury report   | midnight; `injury_impact_calculator.py:98–172` includes ALL injuries regardless of fixture timing |
| Pre-match odds                                  | publication time per snapshot | implicit via MDPS `bm_time`, no explicit `publication_time` column                                |
| Post-match (xG, fixture_stats, sfi_progressive) | `match_end_time`              | midnight; horizon gate dead in batch (no `horizon=` arg) → **post-match leaks freely**            |
| Weather                                         | forecast-issue time           | midnight via `_ensure_timestamp` (forecast-target time used for API only)                         |

### LookaheadBiasError coverage

- orchestrator (live mode): correct.
- writer.py (batch mode): `except LookaheadBiasError: pass` because `strict=False` — silently downgrades to warning.
  Future-timestamped observations never block writes (`writer.py:65–66`).
- All 14+ calculators: zero raises, zero `available_at <= kickoff − N` guards. Horizon enforcement post-hoc
  (`apply_horizon_gate` after compute), not per-input.

### Horizon × feature_group validity matrix

Service produces **flat daily parquet per feature_group**, no per-horizon shards. Effectively every (post-match group ×
every horizon) silently writes FT-data into pre-kickoff horizons. The horizon gate exists only inside `derived_features`
when `horizon=` is passed — which batch handler never does.

### `except: continue` — multiple, mostly low-impact

- `derived_features_exporter.py:229–230` — bare `except Exception: pass` in dtype coercion loop.
- `writer.py:65–66` — `except LookaheadBiasError: pass` in `strict=False` mode (the bug above).
- `batch_handler.py:629–630` — manifest write failure non-fatal; **if it fires, no manifest row written for entire day's
  batch.**
- `batch_handler.py:171–172` — `_table_exists_in_gcs` GCS auth failure silently treated as "doesn't exist" → unnecessary
  recompute.
- `bucketed_features_calculator.py:149,163,177,193,201,211,225,243` — 8× swallowed bucketing failures, no metric.

### Migration items

- Add `timeframe` + `fixture_id` to all manifest row_keys.
- Extend `_FEATURE_GROUP_TO_DATA_TYPE` to all 14 raw groups.
- Replace `manifest.add(processing_date=...)` with `record_captured(row_key=...)`.
- Add per-`(feature_group, timeframe, league_id, fixture_id, day)` fan-out write loop.

---

## features-delta-one-service

### ✓ Matches

- Shard key `(feature_group, timeframe)` in every `writer.add()` (`orchestrator.py:316–327`); `_write_parquet`
  partitions by `{day, feature_group, timeframe}` (`feature_writer.py:535–545`).
- `timestamp_out = timestamp + 500ms` synthetic delay applied universally (`feature_writer.py:558–563`);
  `PointInTimeViolation` raised on `timestamp_out <= timestamp` (577–590).
- Dual-layer NaN-ratio gate: `NaNHandler.validate_nan_ratio` (50%) pre-persist (`orchestrator.py:525–535`);
  `FeatureWriteGate` re-checked in writer (264–279).
- Schema gate via `ParquetSchemaEnforcer` + `validate_feature_columns_not_null` (`feature_writer.py:598–632`).
- Timestamp-alignment gate (100% threshold).
- Sports excluded from valid set (correct).
- `EXPECTED_SPARSE_COLUMNS` (`constants.py:60–71`) excludes structurally-sparse swing outcome columns from NaN check.
- Progress events: `INSTRUMENT_DAY_PROCESSED` etc. emitted with row counts.
- `MANIFEST_SCHEMA_VERSION=v6` stamped automatically inside UTL.

### ❌ Mismatches

- **Manifest row key missing `venue`, `instrument_type`, `instrument_id`** (`orchestrator.py:316–326`). Canonical:
  `(ag, service, feature_group, timeframe, venue, instrument_type, instrument_id, day)`. Every venue collapses into a
  single row per `(date, feature_group, timeframe)`. Per-venue coverage rollup broken.
- **Second `writer.add()` call drops `timeframe`** (322–326), creating timeless duplicate rows. No spec justification.
- **`DependencyError` raised without `fail_fast=True`** (`batch_handler.py:121–124`). UTL `DependencyError`
  (`dependency_checker.py:32`) is plain `Exception` subclass — `fail_fast` kwarg doesn't exist. Class needs the
  attribute.
- **Multi-timeframe loop absent from DAG driver** — `_process_one_group` calls `process_feature_group` once with single
  timeframe (`batch_handler.py:513–536`). CLI default `--timeframe 15s` (parser.py:77–81) is outside the audit-mandated
  `{1m, 5m, 1h}` set. Operator must invoke CLI three times.
- **`available_at` not passed to `writer.add()` explicitly** — service uses `.add()` not
  `.record_captured(row_key=...)`. `record_empty` / `record_failed` never called. Only successful shards in manifest.

### 🔀 Wrong layer

- `FEATURE_GROUP_DATA_TYPES`, `TRADFI_DATA_TYPE_OVERRIDES`, `DEFI_DATA_TYPE_OVERRIDES`, `PREDICTION_DATA_TYPE_OVERRIDES`
  redeclared locally (`orchestrator.py:64–129`) with comment saying UAC is now SSOT — **dead drift-risk code, delete**.
- `ExpectedCandleCalculator`, `LookbackValidator`, `calculate_buffer_days` (`dependency_checker.py:205–616`) —
  service-local market-hours logic; should live in UTL `BaseDependencyChecker` or a UTL calendar utility.

### ❓ Unverified

- Whether MDPS manifest is probed before loading candles. `DataLoader._collect_daily_frames` reads GCS blob paths
  directly (`data_loader.py:212–247`) with `FileNotFoundError: continue`. No per-shard manifest pre-flight;
  `DependencyError(fail_fast=True)` only raised for upstream service bucket entirely absent, not
  per-`(venue, data_type, instrument_type, instrument_id, timeframe)` shard.
- Shard-level DAG test coverage — `test_shard_combinatorics.py` defers to `unified-trading-deployment-v2` (auto-skipped
  via `pytest.importorskip`).

### `except: continue` — both acceptable

- `data_loader.py:197–198` — `except FileNotFoundError: continue` inside candidate-path loop (intentional fallback
  chain).
- `app/calculators/base.py:144–145` — typed exceptions inside `normalize_distribution` transform-selection loop.
  Includes `RuntimeWarning` catch which is unusual (only fires under `simplefilter("error")`).

### Migration items

- Add `venue`, `instrument_type`, `instrument_id` to `writer.add()`. Switch to `record_captured(row_key=...)` to enable
  `record_empty` / `record_failed`.
- Remove second timeless `writer.add()` (322–326).
- Add `fail_fast: bool = True` to UTL `DependencyError.__init__`; update batch_handler raise site.
- Add MDPS per-shard manifest pre-flight before candle load.
- Add `for timeframe in target_timeframes` loop or document multi-CLI-invocation requirement.
- Delete dead local data-type override dicts.

---

## UTL-lift candidates summary

### Already in UTL (✓)

- `LookaheadBiasError` (`point_in_time.py:36`).
- `LookaheadBiasGuard` (`feature_calculator/liquidation_bands.py:322`).
- `FeatureWriteGate` / `WriteGateConfig` (`feature_service_base/write_gate.py`) — adopted by features-onchain,
  features-cross-instrument, features-volatility, features-delta-one, features-sports.
- `check_nan_ratio` / `find_excessive_nan_cols` (`feature_calculator/base_validation.py:42, 32`).
- `run_lifecycle` (`events/run_lifecycle.py`).
- `columns_available_at_horizon` (`feature_service_base/horizon_gate.py:76`).
- `InstrumentsWriteGate` (`instruments_write_gate.py`).

### Lift candidates (duplicated per-service)

**1. Dual-vocab probe** → `unified_trading_library/hive_vocab.py` (proposed)

- features-onchain `mtds_canonical_reader.py:53–55` + `eigen_rewards_calculator.py:46–55`
- features-cross-instrument `batch_handler.py:65–100`
- deployment-service `shard_builder.py:254`
- MDPS `reprocess_sports_odds.py:89–92`
- instruments-service migration scripts
- execution-service `defi_arbitrage_dispersion_decision_trace.py:274`
- 7+ inlined copies; SSOT keys exist (`RAW_TICK_ASSET_GROUP_HIVE_KEY` / `_LEGACY`) but probe utility doesn't.

**2. Write-gate helper extension** → `unified_trading_library/write_gates.py` (extend
`feature_service_base/write_gate.py`)

- (a) Row-count==0 standalone gate — currently inlined at `features-cross-instrument/base_calculator.py:166`,
  `features-delta-one/base_calculator.py:152`, `microstructure.py:43`, `funding_oi.py:43`, `futures_basis.py:44`.
- (b) NaN ratio — already in UTL via `FeatureWriteGate`; carry-tracer pattern is lifted.
- (c) Schema-match against UAC contract — `features-delta-one/feature_writer.py:603` (`_validate_schema`), MDPS
  `orchestration_writer.py:242` (`_validate_alignment_and_schema`), MDPS `output_writer_service.py:182`
  (`_validate_candles_schema`). None call a shared UTL contract enforcer.
- (d) **Cluster-aware bundle gate (TradFi MVP Item 1)** — confirmed absent. Lands as the 4th gate;
  `expected_root_clusters` + `cluster_extractor` params on `record_captured`.

**3. LookaheadBiasError adoption coverage**

- Defined in UTL (`point_in_time.py:36`); raised in `PointInTimeEnforcer.check_observation_timestamp` (71).
- Consumed correctly: features-onchain `feature_writer.py:22, 320`; ml-training
  `leverage_distribution_trainer.py:21, 370`; features-delta-one (via `FeatureWriteGate` strict mode); features-sports
  orchestrator (live mode).
- **Coverage gap:** features-sports batch mode swallows it (`writer.py:65–66`) due to `strict=False`. features-delta-one
  and features-volatility/multi-timeframe/cross-instrument: PIT enforcement depends on service-config `strict` setting
  (not all default to True).

**4. `available_at` stamping helpers** → `unified_trading_library/availability_stamping.py` (proposed)

- All sports per-source stamping rules inlined in `instruments-service/orchestrator.py` (lineups 3918, post-match
  4207/4597, weather 5781–5785, transfer 3135, FX 3446, SFI 5283).
- features-sports re-uses `data_available_at` propagated through but doesn't have its own stamping helper.
- New service writing sports features will silently get this wrong without a UTL helper.

**5. Schema-introspection helper** → `unified_trading_library/schema_introspection.py` (proposed — **does not exist**)

- deployment-api `data_status_drilldown.py` serves contract-registry metadata only (declared schema from UAC).
- No utility reads an actual parquet on disk and returns
  `{columns, dtypes, row_count, nan_ratio_per_column, available_at_min/max}`.
- Required for deployment-UI schema view; flag as build item.

**6. Phantom-audit utility** → `unified_trading_library/phantom_audit.py` (proposed)

- Currently `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`.
- 5 drift axes (hive-vocab, IT casing, empty IT, path-prefix, chain-bundle equiv) + `ASSET_GROUP_CONFIG` +
  `_venue_level_prefixes()` + `_audit_generic()` + HTTP-pool sizing fix.
- Lift pure functions to UTL; keep CLI wrapper in instruments-service.

### Build items (don't exist)

1. UAC `canonical_question_group` SSOT for prediction markets (Polymarket / Kalshi).
2. UAC `feature_group → required_inputs[]` DAG SSOT (currently scattered across features-onchain, features-sports,
   features-delta-one).
3. UTL `hive_vocab.py` (dual-vocab probe).
4. UTL `availability_stamping.py` (per-source `available_at` rules).
5. UTL `schema_introspection.py` (real-parquet introspection for UI).
6. UTL `phantom_audit.py` (lifted from instruments-service script).
7. UTL `write_gates.py` extension with cluster-aware bundle gate (Item 1, parallel stream — coordinate before shipping).
8. UTL `DependencyError(fail_fast: bool = True)` — class needs the kwarg.
9. UAC `INSTRUMENT_PROCESSED` event taxonomy + adapter adoption (CLAUDE.md says CRITICAL post-2026-05-05;
   instruments-service doesn't emit it).

---

## Coordination flags (ping before shipping)

- **Item 1 (cluster-aware bundle validation):** any audit fix that touches `record_captured` signature blocks on this.
  MDPS bundles, MTDS Tardis/Databento options/futures, sports per-(bookmaker,league) all need it.
- **Item 2 (Databento `except: continue`):** confirmed fixed; no other MTDS adapters have the same anti-pattern. Safe to
  scope out.
- **Prediction `canonical_question_group`:** UAC build-item before any service can adopt; confirm with UAC owner before
  drafting plan.
- **`fail_fast` on `DependencyError`:** features-delta-one already uses the spelling but UTL doesn't accept the kwarg.
  Either lift to UTL (preferred) or remove the call site.

---

## Suggested phasing for the companion plan

1. **Phase 0 — UAC/UTL foundations (sequential, blocks rest)**
   - UAC `canonical_question_group` SSOT
   - UAC `feature_group → required_inputs[]` DAG
   - UTL `hive_vocab.py`, `availability_stamping.py`, `phantom_audit.py`, `schema_introspection.py`
   - UTL `write_gates.py` cluster-aware extension (coordinated with parallel stream)
   - UTL `DependencyError(fail_fast=True)` kwarg

2. **Phase 1 — per-service writer fixes (parallel, all 6 services)**
   - Add missing v6 columns to manifest row_keys per service (especially features-onchain, features-sports,
     features-delta-one, MDPS).
   - Switch `manifest.add()` → `record_captured(row_key=...)` everywhere.
   - Wire `record_empty` / `record_failed` paths in features-onchain, features-delta-one, MDPS.
   - Stamp `available_at` per source rules in features-sports (use UTL helper from Phase 0).

3. **Phase 2 — pre-flight granularity fixes (parallel, MTDS + MDPS + features-delta-one)**
   - MTDS `check_shard_freshness` to read full v6 key including `quote_asset` / `margin_type`.
   - MDPS pre-flight to include `timeframe`.
   - features-delta-one MDPS per-shard manifest pre-flight before candle load.

4. **Phase 3 — bundle / partial-shard detection (sequential, after Phase 0 cluster gate)**
   - MTDS Tardis/Databento options/futures bundles.
   - MDPS chain-bundle outputs.
   - Sports per-(bookmaker, league_id, fixture_id) fan-out.
   - GMX per-chain Tier-2 fan-out.

5. **Phase 4 — placeholder-row class fix (MDPS)**
   - Adapter `_create_empty_output` returns 0-row CandleOutput, not n_candles-row NaN.
   - DEFI `liquidity` / `market_state` / `fx_rates` import in `adapters/__init__.py`.
   - Scanner `_CEFI_TRADFI_DEFI_DATA_TYPES` to include all `_DATA_TYPE_TO_MDPS_PREFIX` entries.
   - Delete v3-shaped `_write_manifest_records` summary writes.

6. **Phase 5 — silent-drop & dead-code cleanup (parallel)**
   - MDPS per-symbol streaming `record_failed` for swallowed symbols.
   - features-sports horizon enforcement in batch (`export_derived_features(horizon=...)`).
   - features-sports `_FEATURE_GROUP_TO_DATA_TYPE` to cover all 14 groups.
   - features-delta-one delete dead local data-type override dicts.

7. **Phase 6 — UI/download (out of scope for executor; user's stream)**
   - Data-status drilldown to full v6 granularity.
   - Per-leaf parquet download + schema view (uses UTL `schema_introspection.py` from Phase 0).

QG gates between every phase. Phase 1 can branch off Phase 0 individual UTL deliverables (don't wait for all). Phases 2
and 3 strictly require Phase 0 complete.

## Absorbed from sibling plans (2026-05-06)

This HANDOVER is the canonical SSOT for shard granularity + manifest write-gate work. The following plans had
overlapping scope and have been folded:

- `manifest_schema_v6_quote_margin_combo_2026_04_23` (archived) — schema v6 dimensions (quote_asset / margin_type /
  combo_type / leg_weights) ARE the multi-axis story. Open todos covered by Phase 0 + Phase 1 of this HANDOVER. Design
  rationale on the v6 dimension set survives in archive as background.
- `mtds_canonical_sharding_alignment_2026_03_31` (archived) — 8 open todos on MTDS shard-key alignment. Covered by Phase
  1 layer-discipline rules + the per-asset-group shard atom matrix.
- `combo_bundle_aggregation_2026_04_30` (archived) — combo bundling is a `BUNDLED_DATA_TYPES` member with cluster
  validation per `record_captured` (Item 1 cluster validation primitive). 2026-04-30 writer fix + ~13M legacy per-combo
  parquet compaction shipped per session memory; residual Phase 5 verification belongs in Phase 1 cluster validation
  rollout.
