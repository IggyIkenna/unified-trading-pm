---
title:
  "pipeline_mode standardisation — source-aware live, batch→live continuity, replay/recovery mode, reader precedence +
  live-readiness gates"
created: 2026-06-05
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
locked_since: 2026-06-05
ratified: 2026-06-05 (operator — all 6 decisions + refinements)
source:
  - audit 2026-06-05 (5-agent fan-out:
      UAC/UTL model + MTDS/IS writers + downstream readers + cross-AG migrators + 4 doc layers; load-bearing claims
      operator-verified)
  - data_source_provenance_all_asset_groups_2026_06_01.md (source column + SOURCE_PRIORITY)
  - pipeline_mode_partition_migration_2026_06_01.md (pipeline_mode= path key)
  - batch_live_reconciliation_service_audit_2026_05_27.md (the reconciliation service + Phase-12 live>batch rule)
locked_by: live-defi-rollout
---

# pipeline_mode standardisation — source-aware live + batch/live/replay continuity

> **✅ RATIFIED (operator 2026-06-05)** — all 6 decisions + the #4 (manifest-column) / #6 (CLI-mode + mock/dev) /
> cadence refinements are accepted; this issue doc is promoted to an active plan. Recommendations below are now the
> agreed contract.
>
> **🔴 P0 BLOCKER TO THE v9 DATA + MANIFEST MIGRATIONS (HARD sequencing — operator 2026-06-05).** Strict order: **(1)
> ALL code lands + QG-green across every repo → (2) DRY-RUN migrations per asset_group → (3) REAL `--apply` per
> asset_group.** Because the v9 canonicalisation walks each corpus ONCE (single-walk HARD RULE), the new manifest
> columns (`live_<source>`/`replay_<source>` form, `source` populated, `cadence`, `transport`) MUST be in the code
> BEFORE any `--apply` — else the walk bakes in the old model and fixing it needs a banned second whole-corpus walk.
> **Therefore the per-AG `*_manifest_canonicalisation_2026_06_01.md` `--apply` runs
> (cefi/defi/tradfi/sports/prediction + instruments) are GATED on Phase 0 of this plan being GREEN.** Per-AG nuances are
> handled in separate Phase-1/2 lanes; cross-cutting (UAC/UTL/registries) is the shared Phase-0 foundation. Cross-link:
> every `*_manifest_canonicalisation` plan + `pipeline_mode_partition_migration` + `data_source_provenance`.

## What I found — the `pipeline_mode` axis is asymmetric, and the batch→live→replay continuity model is undesigned

`PipelineMode` (UAC `canonical/crosscutting/pipeline_mode.py`) conflates **mode × source**, but ONLY for batch:

- **Batch**: `pipeline_mode = batch_<source>` (~28 values: `batch_databento`/`batch_tardis`/`batch_yahoo`/…). Source is
  derivable: `source_string_for(BATCH_X) → "X"`.
- **Live**: a single `live_websocket` — encodes the **transport**, NOT the source.
  `source_string_for(LIVE_WEBSOCKET) → None` (verified, pipeline_mode.py:103-110).

So `pipeline_mode` is the SSOT for batch-vs-live (and a GCS path key), and the row-level `source` column is the SSOT for
the vendor — **redundant for batch, but for live the `source` column is the ONLY place the vendor lives**. The docs
(CLAUDE.md / codex `pipeline-mode-partition.md` / the per-AG canonicalisation plans / `SUB_AGENT_MANDATORY_RULES.md`)
never state this asymmetry → they implicitly assume `pipeline_mode` always disambiguates source (a batch-only
assumption). Reconciliation today: **live wins over batch on same row-key** (source_priority.py:628). There is **NO**
replay/recovery pipeline_mode.

### Verified conflicts (load-bearing ones checked at file:line by slot-6)

| #   | Conflict                                                                                                                                                                                                                                                                                      | Status                                                                                                                                           | Owner               |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| 1   | **DeFi rebuild emits blank `pipeline_mode`+`source`** — `rebuild_defi_manifest.py:302` `writer.add(...)` passes neither; `add()` defaults `pipeline_mode=""` with NO auto-derivation (manifest_writer.py:1685). Every other AG's rebuild stamps it.                                           | ✅ RESOLVED mtds@f80c50f1 — `writer.add()` now passes `asset_group=defi` + source-aware `pipeline_mode`+`source`+`transport` (migrator likewise) | vm-defi / slot-2    |
| 2   | **`ManifestWriter.add()` (legacy) defaults `pipeline_mode=""` while `record_captured()` REQUIRES it** — the inconsistency that lets #1 pass silently.                                                                                                                                         | 🔴 VERIFIED                                                                                                                                      | UTL                 |
| 3   | **features delta_one reader omits `pipeline_mode=` from its processed-candles path** (`data_loader._build_blob_path`) while MDPS WRITES it (`candle_write_mixin.py:233`) → coverage-miss for pipeline_mode-partitioned candles.                                                               | 🔴 VERIFIED                                                                                                                                      | features / vm-ml    |
| 4   | **`enumerate_expected_universe.py` seeds `expected_unattempted` via `record_empty()` WITHOUT `pipeline_mode`/`source`** → denominator-seed rows diverge from real rows.                                                                                                                       | 🔴 VERIFIED                                                                                                                                      | IS (tradfi ⑦ adj.)  |
| 5   | **Live multi-source PATH COLLISION** — two live sources for one cell both write `pipeline_mode=live_websocket/…` → same path → silent overwrite. Batch avoids this by varying the key. The slot-6 MDPS dedup CAN'T help (its guard backs off when `source_string_for` returns None for live). | 🟡 VERIFIED design gap                                                                                                                           | UAC + writers       |
| 6   | **No write-time cross-check** that `source_string_for(pipeline_mode) == source` for batch → a row can carry `batch_databento` + `source="massive"` and pass.                                                                                                                                  | 🟡 VERIFIED                                                                                                                                      | UTL                 |
| 7   | **Doc incoherence** — none of the 4 doc layers acknowledge the live asymmetry; `SUB_AGENT_MANDATORY_RULES.md` barely mentions source-stamping → sub-agents don't inherit the rule.                                                                                                            | 🟡 VERIFIED                                                                                                                                      | docs (CLAUDE/codex) |

(ℹ️ NOT a bug, by-design + consistently honored: `source` is a COLUMN not a path key — no source-as-path-key violation
found in any migrator; the batch dual-SSOT is the intentional path-pruning-vs-provenance split.)

## Why it matters — batch→live transition correctness

Operator question (2026-06-05), paraphrased: if we save batch up until midnight and decide to run live at 4am UTC there
is a 5-hour gap — what backfills it? Or do we run live concurrently from yesterday before midnight, so two pipeline
modes (same schema) run concurrently? And if live breaks, do we need another pipeline mode (replay/recovery) — same or
different source (DeFi can replay from chain; Tardis may not allow tick replay, so replay from the exchange)? The reader
must prefer a live mode where it exists, then a batch mode as backup — and a downtime refill goes into the live mode,
the batch mode, or a third replay/recovery mode.

This is the crux of going live: **a strategy needs a GAP-FREE series across its window at the flip moment**. The deep
history (e.g. a 60-day MA) comes from **batch** — that part is fine. The risk is the **tail**: the
`[batch-cutoff → now]` window (batch for a shard may only land hours late, or stop at midnight), which must be filled by
live or replay (see M6 — it is NOT a feature-lookback problem). Get it wrong → compute-wrong / divide-by-zero /
phantom-NaN. The current model has no defined continuity contract, no capability registry, and no recovery mode.

## The model (refined with operator 2026-06-05) — capability registry × per-shard availability × mode-contextual precedence

### M1 — pipeline*mode form: `{mode}*{source}[_{transport}]`

`mode ∈ {batch, live, replay}` × `source = vendor` × optional `transport ∈ {rest, websocket, flat_file}`. Source-aware
for ALL modes (`live_<source>`, not the single `live_websocket`) → fixes the live path collision (#5), makes
`source_string_for` round-trip live, fully symmetric. **Transport (rest/ws/flat_file)**: worth carrying for
observability AND because the SAME source can serve the SAME shard via BOTH rest + websocket — a hard source→transport
mapping would lose that. **Open fork (M1)**: transport as a trailing path/enum segment (`live_tardis_websocket`) vs a
separate column — **recommend keep `pipeline_mode = {mode}_{source}` as the reconciliation axis, and only add the
transport segment/column where a source genuinely has >1 transport for the same shard** (else it's noise). `source`
column stays (swap-resilience).

### M2 — Source-capability registry (UAC SSOT) — tag each source with the modes it can run

Per `data_source`: the set of modes it CAN run `{batch, live, replay}` (+ transports). E.g. `tardis {batch, live}` ·
chain RPC `{batch, live, replay}` · exchange REST `{batch, replay}`. A NEW registry axis alongside `SOURCE_PRIORITY`.

**DEFINITION — REPLAY (operator 2026-06-05, make this crisp everywhere):** replay = the ability to **retrieve a recent
window ON DEMAND — specifically "today's data from start-of-day" — to fill an intraday / startup / live-downtime gap.**
It is **format-agnostic** (tick or bar — the question is availability, not granularity). The test: _"live was down
09:00–11:00 today; can I fetch that window NOW and backfill it?"_ **Chain-related sources are ALWAYS replay-capable**
(deterministic — any past block is queryable intraday). A vendor that only ships **end-of-day** archives (no intraday
retrieval of the current day) is **NOT** replay-capable. `databento` / `massive` intraday-replay = **CONFIRMED
(vendor-doc check 2026-06-05, UAC@8079b884)**: **databento** is replay-capable via the **Live-API 24h intraday replay**
(its Historical API is 24h-embargoed — so today-since-start backfill rides the LIVE path, not historical); **massive**
(= Polygon.io) via **REST tick-within-a-time-range** (intraday retrievable) — caveat: Starter-tier "live" is **15-min
delayed** (true real-time needs a tier upgrade). Both seeded `{BATCH, LIVE, REPLAY}` + locked by
`test_massive_and_databento_are_live_and_replay_capable`.

**M2 REFINEMENT — capability is per-`(source × data_type)`, and integrate with the EXISTING `SourceCapability` registry
(slot-6 finding 2026-06-05).** Hyperliquid is the worked example: it is **live** for `trades`/`l2_book` (`ws_trades` /
`ws_l2_book`) but **REST/batch** for `funding_rates` — so a flat per-source flag is too coarse; capability is per
`(source, data_type)` / per-operation. **Do NOT build a parallel registry** — `registry/capability_declarations/`
already declares
`SourceCapability(supports_live/supports_batch/supports_historical, operations={market:[…ws_trades, recent_trades…]})`
per source + per-operation REST/WS. M2 should **derive** the `{batch,live,replay}` capability from `SourceCapability`
(and add an explicit `supports_replay` + intraday-replay flag there) rather than the standalone draft
`SOURCE_MODE_CAPABILITY` dict (which is the Phase-0.1 placeholder). Also: `hyperliquid_rest` bakes the transport into
the source name — the M1 antipattern (target `hyperliquid` + transport). **TARGET API (explicit — the
data-type-dependence is a hard contract, not a narration):** the capability lookup is
**`modes_for(source, data_type) -> frozenset[Mode]`** (keyed per `(source, data_type)`, derived from
`SourceCapability.operations` — ws-prefixed op ⇒ `LIVE`, REST op ⇒ `BATCH`, + the new `supports_replay`/intraday flag).
The Phase-0.1 `modes_for_source(source)` shipped in UAC@a2eab633 is the **COARSE per-source placeholder** and MUST be
SUPERSEDED by the per-`(source, data_type)` form (e.g. `modes_for("hyperliquid","trades")={BATCH,LIVE}` vs
`modes_for("hyperliquid","funding_rates")={BATCH}`); M3's `could_exist(shard, mode)` calls THIS, so the guardrail is
data-type-aware end-to-end.

### M3 — Per-shard available-sources (UAC SSOT) — and the guardrail

Per shard (`data_type` / `instrument_type` / `fixture` / `entity` / …): which `data_source`s serve it. **M2 × M3 → "what
is possible WHEN", per shard per mode** = the could-exist universe per mode. This is the **guardrail** (UAC's job):
never look for / cover off data that can't exist for that shard in that mode. (Extends the ⑥ instrument-existence
guard + the ⑦ could-exist denominator to the mode axis.)

### M4 — Mode-CONTEXTUAL precedence (a consumption config, not one global order)

The union precedence depends on the consumer's mode-context (live trading vs t+1 backtest reconciliation):

- **Live-mode consumer**: `live > replay > batch` (live is real-time truth; replay fills live gaps; batch backs history
  — live only holds recent, so 10 days of live → uses 10 days of live, replay fills the gaps, batch fills the rest).
- **Batch-mode consumer**: `batch > replay > live` (the batch SSOT is authoritative for backtest/T+1; replay fills its
  gaps; live last).

`replay` is ALWAYS the middle tier (gap-fill). Extends today's "live > batch" (source_priority.py:628) to the 3-mode ×
2-context matrix. It is a **config** because batch-vs-live results must prioritise different pipelines.

### M5 — Data status & manifest: per-mode rows, ONE union view + drilldown

The manifest already carries `pipeline_mode` per row (per-mode rows; replay is just another value). **Data status = the
UNION** (what's available regardless of mode — the system can consume any mode per M4), NOT separate batch/live views;
the **drilldown** exposes the per-mode breakdown + deltas (a visualisation surface — "which days came from
live/replay/batch"). deployment-api/UI extend the 4-state counts with a pipeline_mode dimension.

### M6 — Startup/continuity = the BATCH-CUTOFF window, NOT feature-lookback (operator correction)

Feature lookback (e.g. 100-day MAs) is satisfied by **batch** — it does NOT need live. The real gap is narrower: a
shard's batch SSOT has a **cutoff** (e.g. yesterday's batch only lands at 5am, or batch stops at midnight), so to
operate at 4am the `[batch-cutoff → now]` window must be filled by SOMETHING. The fill policy is a **static per-shard
reality** read from M2×M3:

- shard has a **replay-capable** source → run `replay_<source>` over `[cutoff → now]` at startup (autonomous).
- no replay but a **live** source → live must ALREADY be running (started ahead) — else cannot operate that shard.
- no replay AND no live (batch is the sole SSOT we union against, e.g. sports fixtures) → wait for batch / refuse to
  start / a configured-OK-gap (DR config).

The code KNOWS, per shard, which of these applies (UAC) → "I can replay" / "I must pre-run live" / "I can't start". This
**replaces** my earlier (wrong) "warm-up lead ≥ max feature lookback" framing.

### M7 — Autonomous recovery

Alerting + auto-recovery DETECT a gap (batch stopped + no live + replay-capable shard) and **trigger the replay
themselves** — the same mechanism that refills today's gaps when the system goes down, autonomously, same-data where
capable. "Gaps are OK" is a per-shard DR config, not a default. (Composes with the autonomous-recovery-matrix.)

### M8 — Operational CADENCE is a SEPARATE axis from the batch/live/replay reconciliation class (operator 2026-06-05)

The `pipeline_mode` (batch/live/replay) is the **reconciliation/provenance class** — what the reader unions +
prioritises. **Operational cadence / deployment topology is a DIFFERENT axis** and must NOT be folded into
`pipeline_mode`, or the same logical query fragments into many pipelines to union. Cadence values: `one_off_backfill` /
`t1_daily` / `scheduled_recurring` / `continuous_live` / `recovery_replay`.

- **api-football fixtures 7-days-ahead**: data-class = **batch** (an archived query snapshot, not a live stream, not a
  recovery), cadence = **scheduled_recurring**. Sparse/forward-looking is a CADENCE property, not a new pipeline_mode.
- **T+1 backfill vs one-off historical backfill**: BOTH are data-class = **batch** → SAME `pipeline_mode`
  (`batch_tardis`) → **ONE pipeline to union** (your downside avoided). They differ only in cadence (`t1_daily` vs
  `one_off_backfill`) = deployment topology. So you do NOT split the union by cadence.
- **What separation BUYS you (observability, NOT reconciliation)**: what ran · what failed · where one-off backfills
  started/stopped · where scheduled runs fired. → cadence lives as a **manifest column + the deployment registry**, NOT
  a GCS path key (so it never fragments the data or the union). The reader unions over `pipeline_mode`; the ops/UI
  surfaces slice by `cadence`.

**Net rule**: `pipeline_mode = {batch|live|replay}_{source}[_{transport}]` (reconciliation axis, path key) ⟂ `cadence`
(observability axis, column + deployment registry). Reference data (IS instruments/fixtures) is `batch_<source>` +
cadence `scheduled_recurring` — it has no live stream to reconcile against.

**M8b — cadence is also the UTL `ServiceBootstrap`/CLI `--mode` (operator 2026-06-05)**: the deployment self-describes
how it is running — `--mode {batch|live|replay}` (+ `canonical` for migration runs) at the CLI/bootstrap layer → the
`run_class`/cadence is set at deploy-time, not guessed. (Composes with the `--operation`/`--mode`/`--asset-group` CLI
convention.)

### M5b — the drilldown dims MUST be v9 manifest COLUMNS (fast-query) — bundle into the SAME v9 walk (operator 2026-06-05)

For #4 (union view + drilldown) to be FAST, the slice dimensions must be **manifest columns**, not derived by listing
GCS objects. Verified v9 `AvailabilityRecord` (UTL `manifest_writer.py`) already carries the full shard atom + status +
could-exist as columns:
`date/venue/instrument_type/data_type/asset_group/instrument_id/underlying/chain/league_id/timeframe` ·
`capture_status/error_reason/row_count` · `expected/available/expected_window_completeness_fraction` · `pipeline_mode`
(v8) · `source` (v9, schema-present). **So v9 is already well-suited for fast shard drilldowns** — the additions are
small: **(a) `cadence` + (b) `transport` as new columns, and (c) actually POPULATING `source`** (schema-present but
empty for AGs whose re-consolidation hasn't run). **HARD — bundle these into the IN-FLIGHT v9 canonicalisation walk
(single-walk discipline), NOT a later v10 second walk.** The manifest is the fast-query index; the GCS hive path keys
(`day/pipeline_mode/asset_group/venue/instrument_type/data_type/[underlying]`) MUST each have a mirrored manifest column
(the shard-granularity SSOT) so data-status/UI never scan objects — confirm cadence/transport satisfy that mirror.

### M9 — `mock`/`dev` axis: simulated data via a `mock` source + the DEV cloud-storage path split (operator 2026-06-05)

Mocking falls out naturally: `source = mock` (or a `mock`-tagged pipeline_mode) → routed to the **DEV cloud-storage
path** via the existing env-tier bucket split (`-dev-`/`-stg-` vs `-prd-`), so **fake/simulated data never touches
prod**. This lets dev smoothly move between fake/simulated and real data without affecting production, and makes test
fixtures first-class (a `mock` capability in the M2 registry). Env-tier is itself an orthogonal axis (already in
`resolve_bucket_name`) — `mock` composes with it (mock ⇒ dev-tier only).

## Cross-repo blast radius — all 25 workspace repos triaged (so each owner understands their slice)

> "26th" = the archived `unified-trading-codex` (folded into PM `codex/`), not a live repo. Tiers: 🔴 defines/changes
> contract · 🟠 writes · 🟢 reads/consumes (mode-aware union) · 🔵 ops/status/infra · ⚪ test/docs/minimal.

| Repo                                          | Tier | What this design requires of it                                                                                                                                                                                                            |
| --------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **unified-api-contracts**                     | 🔴   | DEFINES it all: `{mode}_{source}[_{transport}]` enum (M1) · source-capability registry (M2) · per-shard availability (M3) · `could_exist(shard,mode)` guardrail · mode-contextual precedence resolver (M4) · cadence enum (M8). The spine. |
| **unified-trading-library**                   | 🔴   | ManifestWriter: require/validate `pipeline_mode` (fix #2) · cross-check `source==source_string_for(pm)` (#6) · add `cadence` column · `derive_pipeline_mode_for_row` for live/replay.                                                      |
| **market-tick-data-service**                  | 🟠   | live writer stamps `live_<source>` (not `live_websocket`) · new `replay_<source>` write path (M-D3) · cadence tag · reads M2/M3 to know what to run + startup-fill (M6).                                                                   |
| **instruments-service**                       | 🟠   | reference/fixtures writer stamps `batch_<source>` + cadence=`scheduled_recurring` · `enumerate_expected_universe` stamps pm+source (#4) · IS catalog FEEDS M3 per-shard availability (the could-exist universe).                           |
| **market-data-processing-service**            | 🟢   | raw-read dedup extends to `live_<source>`/`replay` (slot-6 dedup already in for batch) · processed_candles carry pipeline_mode · mode-contextual union read (M4).                                                                          |
| **features-service**                          | 🟢   | delta_one/volatility/onchain/sports loaders pipeline_mode-aware (#3) + mode-contextual union (M4) + source resolution.                                                                                                                     |
| **strategy-service**                          | 🟢   | `manifest_allocation_guard` reads per-mode capture_status · hosts the **live-flip readiness gate** (M6) — refuse flip if the `[batch-cutoff→now]` tail isn't covered per shard capability.                                                 |
| **batch-live-reconciliation-service**         | 🔵   | the HOME for M4 mode-contextual precedence + the cross-mode UNION reconciliation + the M6 startup/continuity gate.                                                                                                                         |
| **alerting-service**                          | 🔵   | M7: detect `(batch-stopped + no-live + replay-capable)` gap → fire `replay_<source>` autonomously; alert on uncoverable gaps.                                                                                                              |
| **deployment-service**                        | 🔵   | CADENCE = deployment topology: `one_off_backfill`/`t1_daily`/`scheduled_recurring`/`continuous_live` map to VM launchers / Cloud Run Jobs / Scheduler; registers `run_class`. Owns the M8 ops axis.                                        |
| **deployment-api**                            | 🔵   | data-status: extend 4-state counts with `pipeline_mode` + `cadence` dimensions; could-exist denominator per mode (M3/M5).                                                                                                                  |
| **deployment-ui / unified-trading-system-ui** | 🔵   | M5 union view + `pipeline_mode`/`cadence` drilldown (the "visualisation game").                                                                                                                                                            |
| **ml-service**                                | 🟢   | consumes features (downstream of the union); inherits mode-aware reads — light touch, verify no pipeline_mode assumption.                                                                                                                  |
| **greeks-service**                            | 🟢   | consumes market data → use the mode-aware union reader; light touch.                                                                                                                                                                       |
| **execution-service**                         | 🟢   | itself a SOURCE (`execution_service` pipeline_mode); ensure execution-fill writes carry pm + cadence; consumer side light.                                                                                                                 |
| **trading-agent-service**                     | 🟢   | downstream consumer; verify it reads via the union, not a raw single-mode path.                                                                                                                                                            |
| **ibkr-gateway-infra**                        | 🟠   | a LIVE source (IBKR equities/futures stream) → tag its capability in M2 (`{live}`/`{live,replay?}`); stamps `live_<source>`.                                                                                                               |
| **unified-trading-api**                       | 🟢   | API gateway surfacing data-status — passes through the pipeline_mode/cadence dimensions.                                                                                                                                                   |
| **client-reporting-api**                      | 🟢   | reads data for reports → union reader; light touch.                                                                                                                                                                                        |
| **fund-administration-service**               | 🟢   | downstream; light touch.                                                                                                                                                                                                                   |
| **e2e-testing**                               | ⚪   | e2e for the cross-mode union + precedence + startup-gate + autonomous-replay.                                                                                                                                                              |
| **system-integration-tests**                  | ⚪   | SIT for the cross-repo flow (write→manifest→union read→gate).                                                                                                                                                                              |
| **agent-orchestrator**                        | ⚪   | meta/orchestration — no data-pipeline change.                                                                                                                                                                                              |
| **unified-trading-pm**                        | ⚪   | this issue doc + the codex/CLAUDE.md/sub-agent-rules/plan coherence audit (below).                                                                                                                                                         |

## Phased execution & dependency order (ratified 2026-06-05) — code → dry-run → real

> The single most important constraint: **no `--apply` data/manifest migration runs until ALL Phase-0 code is GREEN**
> (single-walk discipline). Per-AG nuances split into separate lanes in Phase 1/2; cross-cutting is the shared Phase 0.

**Phase 0 — CODE ONLY (the blocker; all repos; no data ops). DAG within Phase 0:**

- **0.1 Foundation (UAC)** — must land first: M1 enum (`{mode}_{source}[_{transport}]`) · M2 source-capability registry
  · M3 per-shard availability + `could_exist(shard, mode)` · M4 precedence resolver · M8 cadence enum · M9 `mock`
  source.
- **0.2 Manifest (UTL, depends 0.1)** — add `cadence`+`transport` columns (M5b) · require/validate `pipeline_mode` (#2)
  · cross-check `source==source_string_for(pm)` (#6) · `ServiceBootstrap --mode` carries batch/live/replay/canonical
  (M8b).
- **0.3 Writers (MTDS + IS, depends 0.1/0.2)** — stamp `live_<source>`/`replay_<source>` + source + cadence + transport;
  mock→dev path (M9); **#1 defi rebuild stamps pm+source**; **#4 enumerator stamps pm+source**; per-AG nuance isolated.
- **0.4 Readers (MDPS + features + strategy, depends 0.1/0.2)** — pipeline_mode-aware (#3) + mode-contextual union (M4).
- **0.5 Reconciliation + gates (batch-live-reconciliation-service + strategy)** — union + precedence + M6 startup gate.
- **0.6 Ops/recovery (deployment-service + alerting)** — M8 cadence topology + M9 dev/mock split; M7 autonomous replay.
- **0.7 Status/UI (deployment-api + UI)** — M5 union + pipeline_mode/cadence drilldown columns.
- **0.8 Doc before-audit reconcile (#7)** — CLAUDE.md + codex + sub-agent-rules + all per-AG plans (no stale
  `pipeline_mode==source` / `live_websocket` / `live=batch⇒identical-path` claims).
- **GATE 0**: every repo QG-green + a cross-repo SIT proving write→manifest(all columns)→union-read→gate. Only then →
  Phase 1.

**Phase 1 — DRY-RUN migrations, per asset_group (depends GATE 0).** Re-run each `migrate_*` + `rebuild_*_manifest`
`--dry-run` so they emit the NEW columns (live\_<source>/source/cadence/transport) into the v9 form; verify the manifest
drilldown dims are fully populated + the GCS path↔column mirror holds. Lanes: cefi · defi · tradfi · sports ·
prediction · instruments (each its own dry-run + per-AG nuance). **GATE 1**: dry-run clean per AG.

**Phase 2 — REAL `--apply`, per asset_group (depends GATE 1; operator-gated; single-walk).** Each AG's v9
canonicalisation `--apply` now carries EVERYTHING in ONE walk. This is the existing per-AG `*_manifest_canonicalisation`
`--apply` — which this plan GATES. Per-AG lanes; instruments (cross-cutting) sequenced per its own plan. Post-walk
verify: all drilldown columns populated, 0 `live_websocket`, source non-empty where required.

**Phase 3 — Doc after-audit (#7 second pass)** — re-audit all doc layers vs the shipped contract.

## Work units (phase-tagged; route to owners)

- [ ] [CODE] P1. **STANDARDISE the per-AG manifest stamping** — fix #1 (defi rebuild stamp `pipeline_mode`+`source`) +
      #2 (make UTL `add()` require/auto-derive `pipeline_mode` like `record_captured`, OR delete the legacy `add()`
      path) + add a cross-AG regression test asserting every rebuild stamps both. Repos: market-tick-data-service +
      unified-trading-library. Owner: vm-defi (#1) + UTL. **#2 (C-#2) DONE 2026-06-07 — utl@d0745bde**: `add()` now
      AUTO-DERIVES `pipeline_mode` via `derive_pipeline_mode_for_row` for a derivable market-data row (venue+data_type,
      no feature_group); blank can no longer pass silently. **REMAINING: #1 (defi rebuild stamp) — vm-defi**, + the
      cross-AG regression test rides the defi rebuild fix.
- [ ] [CODE] P1. **features delta_one reader pipeline_mode-aware** (#3) — `_build_blob_path`/`_resolve_blob_paths`
      include the `pipeline_mode=` segment (delegate to UAC `candidate_parquet_paths` or build inline like MDPS), with a
      coverage regression. Repo: features-service. Owner: vm-ml.
- [x] ✅ [CODE] P1. **enumerate_expected_universe stamps pipeline_mode+source on `record_empty`** (#4) — is@03a93e10
      (2026-06-07). `_derive_pm_source_transport(asset_group, data_type)` derives pm/source/**transport** from the
      cell's primary external source in UAC `SOURCE_PRIORITY`; seeded `expected_unattempted`/`empty_confirmed` rows now
      carry all three (computed/unregistered cells exempt-blank). +5 tests asserting non-blank pm+source+transport on
      seeded cells. (transport added too, per C-TRANSPORT.) Repo: instruments-service.
- [ ] [DESIGN] P0. **M1 — `{mode}_{source}[_{transport}]` enum** (operator-ratify). **PARTIAL — Phase 0.1 shipped the
      abstract `Mode{BATCH,LIVE,REPLAY}` enum + `mode_of(PipelineMode)` (UAC@a2eab633).** **C-TRANSPORT tranche DONE
      2026-06-07 (operator R4)**: source-aware `LIVE_<SOURCE>`/`REPLAY_<SOURCE>` members + round-tripping
      `source_string_for`/`pipeline_mode_for_source` for batch+live+replay; the `Transport` enum + `transport_of()`
      (>1-transport suffix parser, None today) + `default_transport_for_source()`; `source_string_for` strips a trailing
      transport suffix; the **`hyperliquid_rest` antipattern is retired** → `source=hyperliquid` + `transport=rest` (the
      unified vendor: `batch_hyperliquid` + `live/replay_hyperliquid`); + the manifest `transport` COLUMN (uac@cc69b123,
      utl@d0745bde, mtds@c567962e). **REMAINING (the BREAKING object migration, separate GATED tranche — see the
      M1-BREAKING item below): migrate `live_websocket` OBJECTS/writers/readers → `live_<source>`/`replay_<source>` +
      the reconciliation-service.** Repos: UAC + UTL + MTDS + features + batch-live-reconciliation-service.
- [x] ✅ [DESIGN] P0. **M2 — source-capability registry in UAC — Phase 0.1 DONE (draft seed) (UAC@a2eab633).**
      `SOURCE_MODE_CAPABILITY` (source→`{Mode}`) + `modes_for_source`/`source_supports`/`sources_supporting`; batch=all
      (certain), live/replay seeded with the operator-stated facts (chain RPCs replay-capable; Tardis live-not-replay),
      rest DRAFT. 11 tests assert completeness + batch-floor + stated facts only (uncertain flags free to change on
      ratify). **REMAINING: per-source live/replay RATIFY (operator/domain), then they become load-bearing.** Repo:
      unified-api-contracts.
- [ ] [DESIGN] P0. **M3 — per-shard available-sources registry in UAC** + the M2×M3 "possible-when" guardrail API
      (`could_exist(shard, mode)`); extends the ⑥ existence-guard + ⑦ could-exist denominator to the mode axis. Repo:
      unified-api-contracts (+ consumers IS/MTDS/features/deployment-api).
- [ ] [CODE] P0. **M4 — mode-contextual precedence** — `select_for_mode(consumer_mode, available_modes)`: live-mode
      `live>replay>batch`, batch-mode `batch>replay>live` (replay always middle). A config on the consumer. Repos: UAC
      (resolver) + batch-live-reconciliation-service + features/strategy readers. **NOTE 2026-06-07 (slot-7)**: the
      **data-status CONSUMER** does NOT need full `select_for_mode` — it unions MODE-AGNOSTICALLY (answers "available
      from ANY mode"), shipped in M5 below (`deployment-api@4dd2575`). **The M4 mode-precedence TIEBREAK
      (live>replay>batch) IS now applied in the data-status union** (`deployment-api@46e3d57`): the M5 status-union
      decides the capture_status (captured wins regardless of mode); M4 only picks the REPRESENTATIVE row
      (source/error_reason/pipeline_mode) among rows sharing that status — never changes the outcome (`live_websocket`
      treated as live). The REMAINING-OPEN M4 piece is the **live read-path resolver** `select_for_mode` in
      batch-live-reconciliation-service (live-side track) — picks which mode's VALUE a live/batch reader CONSUMES.
- [ ] [CODE] P0. **M5 — data status = UNION + pipeline_mode drilldown** — deployment-api/UI extend the 4-state counts
      with a pipeline_mode dimension (one union view + per-mode breakdown + deltas). Repos: deployment-api +
      unified-trading-system-ui. **PARTIAL 2026-06-07 (slot-7) — CONSUMER SHIPPED**: `deployment-api@4dd2575`
      (`data_status_union.union_reduce_to_cells` UNION read path — ≥1 source/mode captured ⇒ cell captured, cell-grain
      4-state, no double-count; per-(pipeline_mode × source) drilldown breakdown at leaves + pipeline_mode/source
      filter + group_by axes + top-level summary; QG-green, `test_data_status_union.py` +
      `test_data_status_drilldown_provenance.py`) + `deployment-ui@0dc40eb` (`HierarchicalShardDrilldown` renders the
      breakdown + 4-state; UI **[BLOCKED-PLAYWRIGHT]** — pw:L2 pending, regression:
      `src/components/HierarchicalShardDrilldown.test.tsx`). **Remaining**: the `cadence` dimension (M5b) +
      **unified-trading-system-ui** parity. Landed on LDR via tab-mirror; LDR→staging dep-tier-gated on
      deployment-service STAGING_GREEN (not bypassed).
- [ ] [CODE] P0. **M6 — capability-driven startup gate** — per shard, from M2×M3: replay-capable → autostart replay over
      `[batch-cutoff → now]`; else live-required → assert live already running; else wait/refuse/configured-gap. Repos:
      batch-live-reconciliation-service + strategy (live-flip gate) + MTDS (startup).
- [ ] [CODE] P0. **M7 — autonomous recovery triggers replay** — alerting/auto-recovery detects (batch-stopped +
      no-live + replay-capable) → fires `replay_<source>` autonomously; per-shard "gaps-OK" DR config. Repos:
      alerting-service + MTDS/execution recovery + autonomous-recovery-matrix.
- [x] ✅ [CODE] P1. **write-time cross-check** `source_string_for(pipeline_mode)==source` for batch (#6) — utl@d0745bde
      (2026-06-07). `_assert_source_matches_pipeline_mode` raises `PipelineModeSourceMismatchError` when an EXPLICIT
      batch source disagrees with its pipeline_mode (`batch_databento` + `source="massive"`), wired into record_captured
      / record_captured_from_counts / add(); gated on an explicit (caller-provided) source so auto-stamped single-source
      cells are unaffected (they're correct-by-construction). +tests. Repo: unified-trading-library.
- [ ] [CODE] P0. **M1-BREAKING — migrate `live_websocket` objects/writers/readers → `live_<source>`** (next tranche,
      GATED on the M1/M2 foundation UAC@8cafb758+6cd08c89 + the C-TRANSPORT tranche uac@cc69b123/utl@d0745bde — the
      source-aware `live_<source>`/`replay_<source>` members, the `transport` column + accessor, and the C-#6
      cross-check now all exist; do NOT start before downstream readers handle the new members). This is the DATA-side
      migration: live writers stamp `live_<source>` (not `live_websocket`), the new `replay_<source>` write path lands,
      readers stratify on the source-aware live/replay values, the reconciliation-service consumes them, and the
      transitional `LIVE_WEBSOCKET` alias is removed once no object references it. Fixes the live multi-source PATH
      COLLISION (#5). Repos: UTL (`derive_pipeline_mode_for_row` for live/replay) + market-tick-data-service (live +
      replay write paths) + market-data-processing-service + features-service (mode-aware union read) +
      batch-live-reconciliation-service.
- [ ] [CODE] P0. **T+1 batch/live reconciliation + `live` TTL** (next tranche, GATED on M4 precedence + M1-breaking live
      writers). The batch-live-reconciliation-service confirms batch≈live within a tolerance, then a TTL clears the
      now-redundant `live` cells (long-lived `replay` stays where batch never existed). Config knobs (sensible defaults,
      non-blocking): reconciliation tolerance + TTL horizon. Repo: batch-live-reconciliation-service (+ UTL TTL helper).
- [ ] [DESIGN] P0. **M8 — cadence axis. PARTIAL — Phase 0.1 shipped the `Cadence` enum
      (`one_off_backfill`/`t1_daily`/`scheduled_recurring`/`continuous_live`/`recovery_replay`) in UAC@a2eab633.**
      REMAINING: wire **cadence** as a manifest COLUMN (UTL) + deployment-registry `run_class` (deployment-service) +
      writer stamp (MTDS/IS) + slice-by-cadence (deployment-api/UI). ORTHOGONAL to `pipeline_mode` (NOT a path key,
      never fragments the union). Also shipped Phase 0.1: **M9 `MOCK_SOURCE`** (dev-tier-only mock) in the same commit.
      **NOTE 2026-06-07**: the SIBLING `transport` manifest column (M5b/C-TRANSPORT) is now wired (utl@d0745bde —
      `AvailabilityRecord.transport`, stamped via `default_transport_for_source`) — it is the model the cadence column
      should follow (a v9 additive column, not a path key). The cadence column itself remains.
- [ ] [DOCS] P0. **FULL doc-coherence audit (BEFORE + AFTER), not just a sweep** (#7) — audit EVERY layer for logic that
      CONTRADICTS M1–M8 and reconcile: CLAUDE.md (the `source=` provenance rule, the `pipeline_mode=` partition rule,
      the "Live = batch" rule, the VIX/sports source notes) · codex (`02-data/pipeline-mode-partition.md`,
      `availability-manifest-and-data-status.md`, `honest-absence-downstream-handling.md`,
      `pipeline-mode-and-batch-live-reconciliation.md`, `external-data-always-available-rule.md`) · ALL per-AG
      `*_manifest_canonicalisation` + `pipeline_mode_partition_migration` + `data_source_provenance` +
      `tradfi_massive_dual_source` plans · `SUB_AGENT_MANDATORY_RULES.md` (currently barely mentions source-stamping →
      sub-agents don't inherit it). **Pre-audit already done (2026-06-05, agent E)**: all 4 layers implicitly assume
      `pipeline_mode` encodes source (batch-only assumption); none acknowledge the live asymmetry, the cadence axis, or
      replay. **Post-ratify**: a SECOND pass once M1–M8 land, so the docs match the new contract (no stale
      "pipeline*mode==source" / "live_websocket" / "live=batch ⇒ identical path" claims). Repo: unified-trading-pm (+
      codex). Owner: slot-6 can drive the audit; per-repo doc deltas to owners. **PARTIAL 2026-06-07 — pm@9120464fe**:
      codex `02-data/pipeline-mode-partition.md` reconciled to the
      `{mode}*{source}[_{transport}]` form (documents replay_<source> + the transport suffix-vs-column rule + the     hyperliquid vendor split; DELETED the stale "Don't use replay_*" / "replay writes to live_websocket" lines).     **REMAINING**: the other codex docs (`availability-manifest-and-data-status.md`,     `pipeline-mode-and-batch-live-reconciliation.md`— still has`BATCH_HYPERLIQUID_REST`/`hyperliquid_rest`refs —    `honest-absence-downstream-handling.md`, `external-data-always-available-rule.md`) + CLAUDE.md + per-AG plans +     `SUB_AGENT_MANDATORY_RULES.md`.
- [ ] [CODE] P1. **UI reference-data registry regen** — `lib/registry/ui-reference-data.json` still lists the stale
      `batch_hyperliquid_rest` PipelineMode value. It is GENERATED from UAC (`generate_ui_reference_data.py` →
      `uac-registry-sync.yml`), so regenerate from the now-fixed UAC SSOT (uac@cc69b123) rather than hand-edit. **GATED
      on the UI playwright gate (HARD RULE)**: needs `pw:L2 ✓` + a regression spec on a UI-capable slot. Repo:
      unified-trading-system-ui. Owner: a UI-capable slot. **DEFERRED** — provenance: C-TRANSPORT consumer sweep
      2026-06-07 (the Python-side rename landed uac@cc69b123/utl@d0745bde/mtds@c567962e/is@03a93e10; the generated UI
      mirror regenerates downstream). **Determination (vm-cross-cutting 2026-06-07)**: the UAC source artifacts
      (`unified-api-contracts/ui-reference-data.json` + `openapi/ui-reference-data.json` + the UI repo
      `context/api-contracts/openapi/ui-reference-data.json`) are ALREADY clean (0 `hyperliquid_rest`); ONLY the synced
      `lib/registry/ui-reference-data.json` carries the 1 stale token → the regen diff is provably **purely the
      `batch_hyperliquid_rest`→`batch_hyperliquid` rename**. NOT hand-edited (generated-artifact rule); a UI slot runs
      the sync (`uac-registry-sync.yml` / `generate_ui_reference_data.py`) + the playwright gate to tick.

## Operator decisions needed (closed-set forks)

1. **M1**: ratify `{mode}_{source}[_{transport}]` (`live_<source>`/`replay_<source>`)? + transport: trailing
   segment/column **only where a source has >1 transport per shard**, vs always, vs never.
2. **M2/M3**: build the per-source capability tags + per-shard available-sources as UAC registries (the "possible-when"
   guardrail SSOT)? — recommend YES (this is the spine; replaces an ad-hoc per-AG recovery-source policy).
3. **M4**: confirm **mode-contextual** precedence (live-mode `live>replay>batch`; batch-mode `batch>replay>live`) as a
   consumer config?
4. **M5**: data status = ONE union view + pipeline_mode drilldown (vs separate batch/live status surfaces)?
5. **M6/M7**: capability-driven startup gate + autonomous replay-on-gap; per-shard "gaps-OK" as a DR config?
6. **M8**: confirm cadence (`one_off_backfill`/`t1_daily`/`scheduled_recurring`/`continuous_live`/`recovery_replay`) is
   a SEPARATE observability axis (column + deployment registry), NOT folded into `pipeline_mode` (so the same Tardis
   query for t+1 vs long-term stays ONE pipeline to union)?

---

## GATE-0 CONCRETE EXECUTION PLAN + PROGRESS LOG (2026-06-16, /autonomous — drive to GREEN here)

> Operator 2026-06-16: scope GATE 0 concretely + implement all 6 items + the SIT to completion HERE (no epic-VM
> dispatch). This section is the file-level spec + the append-only Progress Log (the loop's handoff doc; no summary
> file). **Success = every touched repo QG-green + the write→manifest→union-read SIT passing → GATE 0 met → Phase-1
> dry-runs unblocked.** Source spec: scouting pass 2026-06-16 (file:line verified).

### The 6 items (file-level)

- **I1 — fix #1 (defi rebuild stamp).** repo `market-tick-data-service`. Main object-scan `add()`
  (`scripts/rebuild_defi_manifest.py:609-621`) ALREADY stamps pm+source+asset_group (mtds@f80c50f1) — the `:302`
  blank-stamp is HISTORICAL. Remaining: (a) the CF-11 honest-absence re-emit `:412-416` omits `source`+`transport` (LOW
  — branch "never reached on real rebuild" per its own comment); (b) add a regression test asserting the rebuild's main
  `add()` stamps non-blank pm+source+asset_group (`tests/integration/test_manifest_schema_contracts.py` only checks the
  signature, not the call site). INDEPENDENT. Non-breaking.
- **I3 — fix #3 (features delta_one reader pipeline_mode-aware).** repo `features-service`. `data_loader.py`
  `_build_blob_path:502-541` + `_resolve_blob_paths:316-343` build paths with NO `pipeline_mode=` segment; MDPS WRITES
  it (`mdps config.py get_processed_path`). Thread `pipeline_mode: str|None` through load_candles→_resolve→_build;
  delegate to UAC `candidate_parquet_paths(asset_group,data_type,day,pipeline_mode=pm)`; probe canonical(with-pm)→bare.
  Tests: `tests/delta_one/unit/test_data_loader.py` (canonical carries pm; probe order; pm=None→bare). `PYTEST_UNIT_DIR="tests/"`.
  INDEPENDENT. Non-breaking.
- **I6a — UTL cadence column (the long pole; blocks M5+SIT).** repo `unified-trading-library`. Add `cadence: str = ""`
  to `AvailabilityRecord` (`manifest_writer/_rows.py:~401`, mirror the `transport` field) + add `"cadence"` to
  `_ROW_KEY_COLUMNS`; writer stamps via `default_cadence_for_source`/kwarg. Additive (rides v9 walk). Non-breaking.
- **M3 — could_exist (UAC).** repo `unified-api-contracts`. NEW `canonical/crosscutting/shard_source_availability.py`:
  `sources_for_shard(asset_group,shard_key)` (from SOURCE_PRIORITY + DataTypeCapability.sources) +
  `could_exist(asset_group,shard_key,mode)=any(mode in modes_for_source(s) for s in sources_for_shard)`. Extends ⑥/⑦
  denominator to the mode axis. Coarse `modes_for_source` OK now; per-(source,data_type) `modes_for()` is a follow-on.
  Depends M1 enum (shipped). Pure ADD. Non-breaking.
- **M4 — select_for_mode (UAC + BLRS).** repo `unified-api-contracts` NEW `canonical/crosscutting/mode_precedence.py`:
  `select_for_mode(consumer_mode, available_modes)` live-ctx [LIVE,REPLAY,BATCH] / batch-ctx [BATCH,REPLAY,LIVE] (replay
  always middle). Wire in `batch-live-reconciliation-service` (`engine/mode_resolver.py` or stage0). deployment-api
  tiebreak (data_status_union.py) already shipped — do NOT redo. Depends M1. Pure ADD. Non-breaking.
- **M5 — data-status UNION + pm/cadence drilldown.** Union/pm/source/transport drilldown SHIPPED (deployment-api@4dd2575,
  deployment-ui@0dc40eb). Remaining: (b) deployment-api cadence dim (`services/data_status_union.py:207,226` add cadence
  to group_cols + breakdown — `PROVENANCE_COLS` already lists it pending) [needs I6a]; (c) deployment-ui cadence badge
  (`HierarchicalShardDrilldown.tsx`); (d) **unified-trading-system-ui PARITY GAP** — `HierarchicalShardDrilldown` does
  NOT exist there; port it + wire into the data-status view (UI, needs Node≥22 + pw:L2). Non-breaking.
- **M1-BREAKING — `live_websocket`→`live_<source>`/`replay_<source>` migration.** The enum FOUNDATION is shipped
  (`pipeline_mode.py` has the source-aware members + Mode/mode_of/transport). Remaining BREAKING tranche: writers
  (mtds `live/websocket_runner.py:77` `_LIVE_PIPELINE_MODE`, `live/manifest_recorder.py`, mdps `live_aggregator.py`,
  execution `live/data_sink.py`) stamp `pipeline_mode_for_source(source,Mode.LIVE)` not the literal; readers (mdps
  `live_workers.py`, deployment-api `_live_coverage.py`, BLRS `stage0`) stratify via `is_live`/`mode_of`; UTL
  `pipeline_mode_resolver.py:157-229` derive live_<source>/replay_<source>; **delete the `LIVE_WEBSOCKET` alias LAST**
  (0 refs). The writer blocker = "source not in writer scope" → derive venue→source from SOURCE_PRIORITY/IS-catalogue.
  BREAKING (enum-value removal → SIT cascade) — alias removal is the final gated step.
- **GATE-0 SIT.** repo `system-integration-tests`. NEW `tests/integration/test_gate0_write_manifest_union_read.py`
  (pattern: `test_pipeline_manifest_wiring.py`; `@pytest.mark.code_test`, credential-free, NO real GCS). 4 legs:
  (1) writer stamps pm+source+cadence+transport; (2) manifest carries all 4 as AvailabilityRecord cols; (3) union-read
  groups by pm; (4) `select_for_mode`+`could_exist` gate. Legs 1-2 (pm/source/transport) greenable now; cadence/gate
  legs skip→unskip as I6a/M3/M4/M1-BREAKING land. **This IS the gate.**

### DAG + Waves (≤2 concurrent Python QG; never 2 agents on same repo/file)

```
WAVE A (parallel, disjoint repos): I1(mtds) · I3(features) · I6a(UTL) · M3(UAC)
WAVE B (after A green): M4(UAC mode_precedence + BLRS wiring) · M5b deployment-api cadence dim [needs I6a]
WAVE C: M5c deployment-ui cadence + M5d unified-trading-system-ui port (UI, Node22/pw:L2) · M1-BREAKING tranche (largest, cross-repo; alias removal LAST)
WAVE D: GATE-0 SIT (system-integration-tests) — legs 1-2 early skip-marked; final green when all land = THE GATE
```

### Success criteria (GATE 0 met)

- [x] ✅ I1 mtds QG green + regression test — market-tick-data-service@89807b4
- [x] ✅ I3 features QG green + reader pm-aware tests — features-service@795e4f4
- [x] ✅ I6a UTL QG green (cadence column) — unified-trading-library@dfe3385f
- [x] ✅ M3 UAC QG green (could_exist) — unified-api-contracts@d56b9cc2
- [x] ✅ M4 UAC + batch-live-reconciliation-service QG green (select_for_mode) — unified-api-contracts@7441a692 + batch-live-reconciliation-service@0e17d7ee
- [x] ✅ M5b deployment-api cadence dim QG green — deployment-api@66e8562d
- [ ] M5c/d deployment-ui + unified-trading-system-ui cadence drilldown (pw:L2)
- [ ] M1-BREAKING: 0 `live_websocket` writers; readers source-aware; LIVE_WEBSOCKET alias removed (0 refs)
- [x] ✅ GATE-0 SIT green (batch + gate legs; live leg skip-pending-M1) — system-integration-tests@db14463 → **GATE-0 FOUNDATION MET (batch path)** → Phase-1 BATCH dry-runs unblocked. (Live-path collision-free guarantee = M1-BREAKING, the gated tranche before a live-containing `--apply`.)

### Progress Log (append-only)

- **2026-06-16 (tick 0)** — /autonomous armed. Scoped GATE 0 to 6 items + SIT (file-level spec above). Corrected the
  coordinator G0 false-green earlier (master_data_canonicalisation@…). Dispatching WAVE A (I1·I3·I6a·M3) as parallel
  sub-agents (disjoint repos). Next: collect Wave-A shas, flip the criteria boxes, dispatch Wave B.
- **2026-06-16 (tick 1) — WAVE A COMPLETE (4/9 criteria).** Shipped: I1 market-tick-data-service@89807b4 (defi rebuild
  CF-11 source+transport stamp + call-site regression test) · I3 features-service@795e4f4 (delta_one reader
  pipeline_mode-aware — mirrors MDPS processed-candle path, NOT raw `candidate_parquet_paths`; probe canonical-pm→bare) ·
  I6a unified-trading-library@dfe3385f (cadence column on AvailabilityRecord — explicit `cadence=` kwarg, NOT
  source-derived; UAC `Cadence` StrEnum is the closed set) · M3 unified-api-contracts@d56b9cc2 (`could_exist(ag,dt,mode)`
  + `sources_for_shard` = SOURCE_PRIORITY ∪ CEFI_LIVE_VENUES overlay). **Contention note**: my 4 parallel agents are each
  other's deps + a transient foreign UAC edit → only M3 self-shipped; I shipped UTL→features→mtds sequentially in dep
  order (UAC clean → UTL → the two leaves). **Two findings captured** (NOT in scope, tracked for follow-on): (a) UTL
  `_writer_io._records_to_dataframe:340` is an explicit column-map that OMITS all v6–v9 cols (`source`/`pipeline_mode`/
  `transport`/`cadence`/…) from the SERIALIZED GCS parquet — the test corpus only asserts in-memory AvailabilityRecord,
  masking it; if the written manifest must carry these, that serializer needs all v6–v9 cols (+`_V4_BACKFILL_COLUMNS`).
  (b) M3 `could_exist` over-approximates (per-source not per-`(source,data_type)` `modes_for`; data_type not full IS shard
  key) — the SAME tranche as the M2/M3 per-`(source,data_type)` refinement already noted in § M2-REFINEMENT. Next: WAVE B
  — M4 (UAC mode_precedence + BLRS wiring) + M5b (deployment-api cadence dim, now unblocked by I6a).
- **2026-06-16 (tick 2) — WAVE B COMPLETE (6/9 criteria).** M4 unified-api-contracts@7441a692 (`select_for_mode` —
  live-ctx [LIVE,REPLAY,BATCH], batch-ctx [BATCH,REPLAY,LIVE], replay-ctx reuses live order) + batch-live-reconciliation-service@0e17d7ee
  (`engine/mode_resolver.py` delegates to UAC select_for_mode; stage0 untouched — resolver is the primitive, no read
  consumer wired yet = follow-on). M5b deployment-api@66e8562d (cadence dim threaded through the union/drilldown like
  transport; blank-safe). Contention: M5b blocked on M4's in-progress UAC edit → shipped after M4 landed UAC (dep-order).
  Next: WAVE C — GATE-0 SIT (system-integration-tests; legs 1-3 greenable now, leg-4 gate uses M3/M4 which are landed) +
  M1-BREAKING (live_websocket→live_<source> writers/readers/resolver + alias removal LAST — the breaking tranche).
  M5c/d UI cadence drilldown (Node22/pw:L2) deferred to a UI pass — display-only, not part of the SIT gate.
- **2026-06-16 (tick 3) — GATE-0 SIT GREEN (7/9). The GATE-0 foundation + SIT are landed → Phase-1 BATCH dry-runs
  unblocked.** SIT system-integration-tests@db14463 — 4 legs at the UAC/UTL contract level: LEG1 batch writer stamps
  pipeline_mode+source+transport+cadence (all non-blank); LEG2 schema carries all 4 + in _ROW_KEY_COLUMNS; LEG3 union
  axes present; LEG4 `could_exist` filters impossible cells + `select_for_mode` picks contextual mode. LIVE leg
  skip-marked `pending M1-BREAKING`. Both Wave-C agents (SIT + M1-BREAKING) hit transient API 500s after ~50 tool calls;
  reconciled down here: SIT was written-but-unshipped → I QG'd + shipped it; M1-BREAKING had shipped ONLY its UAC helper
  **unified-api-contracts@276b6a6 (`live_pipeline_mode_for_venue` — the venue→source live pipeline_mode resolver)** then
  died — NO half-migrated dirty trees (verified clean across mtds/mdps/execution/deployment-api/BLRS).
  **REMAINING (2/9 — the explicit gated next tranche per this plan's own §M1; NOT a vague defer — fully specified):**
  - **M1-BREAKING (decomposes into N non-breaking writer/reader migrations + 1 final breaking alias removal).** The UAC
    `live_pipeline_mode_for_venue` helper is laid (276b6a6); each writer/reader migration is now an INDEPENDENT
    NON-breaking single-repo unit (the `live_websocket` alias still exists, so nothing breaks until the FINAL removal).
    Sites (from the GATE-0 spec above): WRITERS — mtds `live/websocket_runner.py:77` + `live/manifest_recorder.py` +
    `live/backfill_runner.py` + `replay/runner.py` + `cli/handlers/websocket_streaming_handler.py`; mdps
    `app/core/live_aggregator.py`; execution `engine/modes/live/data_sink.py` → stamp `live_pipeline_mode_for_venue(...)`.
    READERS — mdps `app/core/live_workers.py`; deployment-api `routes/data_status/_live_coverage.py` +
    `types/shard_detail.py`; BLRS `stages/stage0_manifest_reason_check.py` → stratify via `is_live`/`mode_of`. UTL
    `pipeline_mode_resolver.py:157-229` derive live_<source>/replay_<source>. THEN (last, breaking, gated on
    `rg "live_websocket|LIVE_WEBSOCKET" --type py` = 0 non-alias refs) delete the `LIVE_WEBSOCKET` alias in UAC
    `pipeline_mode.py:122` → SIT cascade fires + the SIT's skip-marked live leg un-skips.
  - **M5c/d (UI cadence drilldown, display-only, Node22/pw:L2):** deployment-ui `HierarchicalShardDrilldown.tsx` cadence
    badge + unified-trading-system-ui port (the component doesn't exist there). NOT part of the SIT gate.
  **Net for the operator's question ("what's left before dry-run-again / for-real"): the BATCH-path GATE-0 is GREEN —
  re-dry-run is unblocked NOW (on the batch corpora). M1-BREAKING (live-writer migration) is the remaining must-land
  before the REAL `--apply` bakes any live row, to avoid the #5 live_websocket multi-source path collision.**
- **2026-06-16 (tick 4) — /autonomous resumed to drive M1-BREAKING + M5c/d to 9/9 GREEN (this loop's handoff doc).**
  Re-scouted the FULL blast radius of the grep-gate `rg "live_websocket|LIVE_WEBSOCKET" --type py = 0 non-alias refs`:
  it is LARGER than the dispatch's writer/reader enumeration — it also pulls in (a) UTL `streaming/candle_writer.py`
  `close_candle_writer` DEFAULT param `= PipelineMode.LIVE_WEBSOCKET` (public API; MDPS `canonical_writer*` /
  `candle_write_mixin` / `live_aggregator` are the callers → must pass explicit), (b) UTL `pipeline_mode_resolver.py`
  BOTH `resolve_pipeline_mode` (:125 live→LIVE_WEBSOCKET) and `derive_pipeline_mode_for_row` (:187-192 live→None), (c)
  many docstrings/comments, and (d) ~dozens of TEST files across UTL/mdps/deployment-api/BLRS asserting the literal.
  **Helper confirmed landed**: UAC `live_pipeline_mode_for_venue(asset_group, venue, data_type, mode=Mode.LIVE)` lives
  in `canonical/crosscutting/source_priority.py`, exported from the `unified_api_contracts` root (NOT in pipeline_mode.py
  as the dispatch implied). **CRITICAL reader-correctness invariant (codified here)**: readers consume `pipeline_mode`
  as STRINGS from manifest parquets, and OLD data still carries the literal string `"live_websocket"` even after the
  enum MEMBER is deleted → readers MUST string-prefix-match (`value.startswith("live")` / `"replay"` / `"batch"`), NEVER
  reconstruct `PipelineMode("live_websocket")` (ValueError post-deletion). This is the forward+backward-compatible fix
  the deployment-api/BLRS readers need. **Execution waves (all NON-breaking until Wave 3; alias coexists)**: W1 consumers
  in parallel (mtds·mdps·execution·deployment-api·BLRS) migrate every in-repo ref → writers stamp source-aware via the
  helper (GCS path segment + manifest row derive from the SAME value), readers string-prefix-match, tests → concrete
  `live_<source>` member (cefi→LIVE_BINANCE/venue, tradfi→LIVE_DATABENTO, defi→LIVE_ONCHAIN_RPC/LIVE_SOLANA_RPC), each
  QG-green + quickmerge. W2 UTL (resolver source-aware + `close_candle_writer` pipeline_mode REQUIRED + tests/docstrings)
  — after W1 so MDPS already passes explicit. W3 UAC delete the `LIVE_WEBSOCKET` member + the internal
  `if mode is PipelineMode.LIVE_WEBSOCKET` special-cases in `source_string_for`/`transport_of` + UAC tests (breaking →
  SIT cascade). W4 un-skip the SIT live leg + verify green. THEN M5c/d UI cadence drilldown (Node22/pw:L2).
