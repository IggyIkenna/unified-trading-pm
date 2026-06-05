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

Operator question (2026-06-05) — paraphrased: if we save batch up until midnight and decide to run live at 4am UTC
there's a 5-hour gap — what backfills it? Or do we run live concurrently from yesterday before midnight so two
pipeline*modes (same schema) run concurrently? And if live breaks, do we need another pipeline_mode (replay/recovery) —
same or different source (DeFi can replay from chain; Tardis may not allow tick replay so replay from the exchange)? The
reader must pull
`live*_`where it exists then`batch\__`as backup — and a downtime refill goes into live, batch, or a 3rd`replay*\*`/`recovery*\*`
mode?

This is the crux of going live: **feature lookback windows need continuous coverage at the flip moment**. A strategy
flipping to live at 4am whose features need a 60-day (or even intraday) lookback must read a GAP-FREE union of
batch+live(+replay) across the window — or it computes wrong / divides-by-zero / phantom-NaNs. The current model has no
defined continuity contract, no warm-up gate, and no recovery mode.

## The 4 design decisions needed (recommended + open operator fork)

### D1 — Make `pipeline_mode` source-aware for live: `live_<source>` (symmetric with batch)

**Recommend YES.** Replace the single `live_websocket` with `live_<source>` (`live_tardis`, `live_hyperliquid_ws`,
`live_pyth`, …) for every live-capable source. This (a) fixes the live multi-source path collision (#5 — each source
gets its own path key), (b) makes `source_string_for(live_X)` work → the asymmetry disappears, (c) makes the model fully
symmetric (`batch_X` ↔ `live_X`), (d) lets the slot-6 MDPS multi-source dedup work for live too. The `source` column
stays (swap-resilience + the live writer already knows its source). **Open fork**: websocket-vs-REST is a transport
detail — confirm the live axis is (mode=live × source=vendor), i.e. `live_<vendor>` not `live_<transport>`. Migration:
the live writer stamps `live_<source>` going forward; any historical `live_websocket` objects migrate by reading their
`source` column. Closed-set enum change → coordinated UAC + UTL + writers + readers + reconciliation-service + a
one-time path migration.

### D2 — Batch→live continuity: reader reads the cross-mode UNION + a warm-up coverage gate

**Recommend**: the reader resolves a logical cell from the **union across pipeline_modes**, reconciled per row-key by a
defined precedence (D4). So a feature's lookback is satisfied by whatever mode filled each day — `batch_*` for
historical, `live_*` for recent — with NO gap IF the union is complete. The midnight→4am gap is then a **coverage**
problem, solved by EITHER (a) **live started with a warm-up lead** = the max feature lookback (live + batch overlap; the
clean option — two modes, same schema, running concurrently, reader reconciles), OR (b) a catch-up `batch_*`/`replay_*`
run fills the gap. **A pre-live "warm-up coverage gate"** asserts the lookback window is gap-free (union of all modes)
BEFORE a strategy may flip to live. **Open fork**: minimum warm-up lead policy (per-archetype max-lookback, or a fixed
conservative buffer).

### D3 — Add a `replay_*` / `recovery_*` pipeline_mode for live-downtime refill (source may differ)

**Recommend YES, as a DISTINCT 3rd mode** `replay_<source>` (or `recovery_<source>`), because (a) the replay source can
DIFFER from the live source — DeFi replays from the blockchain RPC (deterministic, always available); CeFi replays from
the exchange's own REST/historical when Tardis can't tick-replay — so it must carry its own source provenance; (b) a
distinct mode preserves honesty (you KNOW a cell was recovered, not primary-live). **Where the refill goes**: into
`replay_<source>`, NOT silently into live/batch. **Open fork**: is replay a first-class `replay_<source>` family, or a
flag on the existing modes? (Recommend first-class for provenance + reconciliation clarity.)

### D4 — Reader precedence + live-readiness gates

**Recommend** the reconciliation precedence per (cell, row-key): **`live_* > replay_* > batch_*`** within the live
window (live is real-time truth; replay fills live's gaps; batch is the historical archive), and `batch_*` authoritative
pre-live. Extends today's "live > batch" rule (source_priority.py:628) to three tiers. **Live-readiness gate** (before a
strategy flips to live): (1) lookback window fully covered by the union, (2) live running ≥ warm-up lead, (3) zero
unfilled live-downtime gaps in the window. Owned by / wired through the **`batch-live-reconciliation-service`**.

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
- [ ] [DESIGN] P0. **D1 — `live_<source>` enum** (operator-ratify first): add `LIVE_<SOURCE>` members, make
      `source_string_for`/`pipeline_mode_for_source` round-trip live, migrate `live_websocket` objects + writers +
      readers + reconciliation-service. Repos: UAC + UTL + MTDS + features + batch-live-reconciliation-service.
- [ ] [DESIGN] P0. **D3 — `replay_<source>` mode** (operator-ratify): add the family + recovery-write path + provenance.
      Repos: UAC + UTL + MTDS + execution/recovery runbooks.
- [ ] [CODE] P0. **D2+D4 — cross-mode union reader + warm-up coverage gate + live-readiness gate + 3-tier precedence
      (`live > replay > batch`).** Repos: batch-live-reconciliation-service + features + strategy (the live-flip gate).
- [ ] [CODE] P1. **write-time cross-check** `source_string_for(pipeline_mode)==source` for batch (#6) — assert in UTL
      `_resolve_and_validate_source`. Repo: unified-trading-library.
- [ ] [DOCS] P1. **Doc coherence sweep** (#7) — CLAUDE.md + codex `pipeline-mode-partition.md` +
      `SUB_AGENT_MANDATORY_RULES.md`: state the (source column = vendor SSOT) vs (pipeline*mode = mode SSOT +
      batch-source path key) split, the live asymmetry → `live*<source>` target, and the source-stamping rule for
      sub-agents.

## Operator decisions needed (closed-set forks)

1. **D1**: ratify `live_<source>` (vendor, not transport) as the live pipeline_mode form? (vs keep `live_websocket` +
   rely on the source column only).
2. **D2**: warm-up policy — live-lead-≥-max-lookback (concurrent overlap) vs catch-up backfill of the gap?
3. **D3**: `replay_<source>` as a first-class pipeline_mode family vs a flag? And recovery-source policy per AG (DeFi
   chain-replay / CeFi exchange-REST / etc.).
4. **D4**: confirm 3-tier precedence `live > replay > batch` + the live-readiness gate location
   (batch-live-reconciliation-service).
