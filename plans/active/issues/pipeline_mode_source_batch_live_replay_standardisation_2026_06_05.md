---
title:
  "pipeline_mode standardisation — source-aware live, batch→live continuity, replay/recovery mode, reader precedence +
  live-readiness gates"
created: 2026-06-05
author: ikenna [slot-6·laptop]
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

| #   | Conflict                                                                                                                                                                                                                                                                                      | Status                 | Owner               |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------- |
| 1   | **DeFi rebuild emits blank `pipeline_mode`+`source`** — `rebuild_defi_manifest.py:302` `writer.add(...)` passes neither; `add()` defaults `pipeline_mode=""` with NO auto-derivation (manifest_writer.py:1685). Every other AG's rebuild stamps it.                                           | 🔴 VERIFIED bug        | vm-defi / slot-2    |
| 2   | **`ManifestWriter.add()` (legacy) defaults `pipeline_mode=""` while `record_captured()` REQUIRES it** — the inconsistency that lets #1 pass silently.                                                                                                                                         | 🔴 VERIFIED            | UTL                 |
| 3   | **features delta_one reader omits `pipeline_mode=` from its processed-candles path** (`data_loader._build_blob_path`) while MDPS WRITES it (`candle_write_mixin.py:233`) → coverage-miss for pipeline_mode-partitioned candles.                                                               | 🔴 VERIFIED            | features / vm-ml    |
| 4   | **`enumerate_expected_universe.py` seeds `expected_unattempted` via `record_empty()` WITHOUT `pipeline_mode`/`source`** → denominator-seed rows diverge from real rows.                                                                                                                       | 🔴 VERIFIED            | IS (tradfi ⑦ adj.)  |
| 5   | **Live multi-source PATH COLLISION** — two live sources for one cell both write `pipeline_mode=live_websocket/…` → same path → silent overwrite. Batch avoids this by varying the key. The slot-6 MDPS dedup CAN'T help (its guard backs off when `source_string_for` returns None for live). | 🟡 VERIFIED design gap | UAC + writers       |
| 6   | **No write-time cross-check** that `source_string_for(pipeline_mode) == source` for batch → a row can carry `batch_databento` + `source="massive"` and pass.                                                                                                                                  | 🟡 VERIFIED            | UTL                 |
| 7   | **Doc incoherence** — none of the 4 doc layers acknowledge the live asymmetry; `SUB_AGENT_MANDATORY_RULES.md` barely mentions source-stamping → sub-agents don't inherit the rule.                                                                                                            | 🟡 VERIFIED            | docs (CLAUDE/codex) |

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

Per `data_source`: the set of modes it CAN run `{batch, live, replay}` (+ transports). E.g. `databento {batch}` ·
`massive {batch}` · `tardis {batch, live}` · chain RPC `{batch, live, replay}` · exchange REST `{batch, replay}`. This
is a NEW registry axis alongside `SOURCE_PRIORITY`.

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

## Proposed plan items (route to owners on ack)

- [ ] [CODE] P1. **STANDARDISE the per-AG manifest stamping** — fix #1 (defi rebuild stamp `pipeline_mode`+`source`) +
      #2 (make UTL `add()` require/auto-derive `pipeline_mode` like `record_captured`, OR delete the legacy `add()`
      path) + add a cross-AG regression test asserting every rebuild stamps both. Repos: market-tick-data-service +
      unified-trading-library. Owner: vm-defi (#1) + UTL.
- [ ] [CODE] P1. **features delta_one reader pipeline_mode-aware** (#3) — `_build_blob_path`/`_resolve_blob_paths`
      include the `pipeline_mode=` segment (delegate to UAC `candidate_parquet_paths` or build inline like MDPS), with a
      coverage regression. Repo: features-service. Owner: vm-ml.
- [ ] [CODE] P1. **enumerate_expected_universe stamps pipeline_mode+source on `record_empty`** (#4) — derive pm/source
      per seeded cell (the seeded universe is for a known source per (ag,dt)). Repo: instruments-service. Adjacent to
      the tradfi ⑦ denominator item (slot-6 in-lane).
- [ ] [DESIGN] P0. **M1 — `{mode}_{source}[_{transport}]` enum** (operator-ratify): add `LIVE_<SOURCE>` (+
      `REPLAY_<SOURCE>`, M-D3) members; round-trip `source_string_for`/`pipeline_mode_for_source` for live+replay;
      optional transport segment only where a source has >1 transport per shard; migrate `live_websocket` objects +
      writers + readers + reconciliation-service. Repos: UAC + UTL + MTDS + features +
      batch-live-reconciliation-service.
- [ ] [DESIGN] P0. **M2 — source-capability registry in UAC** — tag each `data_source` with `{batch, live, replay}` (+
      transports) it can run. New axis alongside `SOURCE_PRIORITY`. Repo: unified-api-contracts.
- [ ] [DESIGN] P0. **M3 — per-shard available-sources registry in UAC** + the M2×M3 "possible-when" guardrail API
      (`could_exist(shard, mode)`); extends the ⑥ existence-guard + ⑦ could-exist denominator to the mode axis. Repo:
      unified-api-contracts (+ consumers IS/MTDS/features/deployment-api).
- [ ] [CODE] P0. **M4 — mode-contextual precedence** — `select_for_mode(consumer_mode, available_modes)`: live-mode
      `live>replay>batch`, batch-mode `batch>replay>live` (replay always middle). A config on the consumer. Repos: UAC
      (resolver) + batch-live-reconciliation-service + features/strategy readers.
- [ ] [CODE] P0. **M5 — data status = UNION + pipeline_mode drilldown** — deployment-api/UI extend the 4-state counts
      with a pipeline_mode dimension (one union view + per-mode breakdown + deltas). Repos: deployment-api +
      unified-trading-system-ui.
- [ ] [CODE] P0. **M6 — capability-driven startup gate** — per shard, from M2×M3: replay-capable → autostart replay over
      `[batch-cutoff → now]`; else live-required → assert live already running; else wait/refuse/configured-gap. Repos:
      batch-live-reconciliation-service + strategy (live-flip gate) + MTDS (startup).
- [ ] [CODE] P0. **M7 — autonomous recovery triggers replay** — alerting/auto-recovery detects (batch-stopped +
      no-live + replay-capable) → fires `replay_<source>` autonomously; per-shard "gaps-OK" DR config. Repos:
      alerting-service + MTDS/execution recovery + autonomous-recovery-matrix.
- [ ] [CODE] P1. **write-time cross-check** `source_string_for(pipeline_mode)==source` for batch (#6) — assert in UTL
      `_resolve_and_validate_source`. Repo: unified-trading-library.
- [ ] [DOCS] P1. **Doc coherence sweep** (#7) — CLAUDE.md + codex `pipeline-mode-partition.md` +
      `SUB_AGENT_MANDATORY_RULES.md`: the (source column = vendor SSOT) vs (pipeline*mode = mode SSOT + source/transport
      path key) split, the `{mode}*{source}[_{transport}]` form, the M2/M3 capability×availability SSOT, mode-contextual
      precedence, and the source-stamping rule for sub-agents.

## Operator decisions needed (closed-set forks)

1. **M1**: ratify `{mode}_{source}[_{transport}]` (`live_<source>`/`replay_<source>`)? + transport: trailing
   segment/column **only where a source has >1 transport per shard**, vs always, vs never.
2. **M2/M3**: build the per-source capability tags + per-shard available-sources as UAC registries (the "possible-when"
   guardrail SSOT)? — recommend YES (this is the spine; replaces an ad-hoc per-AG recovery-source policy).
3. **M4**: confirm **mode-contextual** precedence (live-mode `live>replay>batch`; batch-mode `batch>replay>live`) as a
   consumer config?
4. **M5**: data status = ONE union view + pipeline_mode drilldown (vs separate batch/live status surfaces)?
5. **M6/M7**: capability-driven startup gate + autonomous replay-on-gap; per-shard "gaps-OK" as a DR config?
