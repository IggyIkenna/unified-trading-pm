---
doc_type: issue
title:
  "Design brief for todo 1 of mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md — MDPS candle-layer
  orphan sweep"
summary: >-
  Pre-implementation research brief for the new market-data-processing-service candle-orphan-sweep script. Covers the
  reference migration_orphan_sweep.py A-E taxonomy, the orphan-object-detection.md codex SSOT's documented blind spots,
  the candle_feature_canonical_path_divergence_2026_07_20.md todo 7 manifest-population history (relevant because a
  candle object with no manifest row today may be a pre-fix write, not a true orphan), the MDPS candle path-builder
  code, and the VM launcher category precedent (_candle_census_cmd/_candle_apply_cmd). Produced by a research sub-agent,
  verified against the live repo tree before todo 1 implementation starts.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service, instruments-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [orphan, orphan-real, mdps, candle, design-brief, tooling-gap]
related:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /codex/02-data/orphan-object-detection.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Research sub-agent dispatched 2026-07-27 (slot-13) while scoping todo 1 of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md, ahead of a host-wide disk-full incident recovery.
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# Design brief — MDPS candle-layer orphan sweep

This is supporting research for todo 1 of
[`mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`](/plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md)
("Build + validate an MDPS candle-layer orphan sweep"). It does not replace that todo's checkbox — it is cited by it.

## 1. `migration_orphan_sweep.py` A-E taxonomy

File: `instruments-service/scripts/migration_orphan_sweep.py`

The forced six-way classification, `ObjectClass` (`:94-102`):

```
CANONICAL_MANIFESTED = "A_canonical_manifested"   # :97
LEGACY_DUPLICATE     = "B_legacy_duplicate"       # :98
MANIFEST_INFRA       = "C_manifest_infra"         # :99
NON_DATA             = "C2_non_data"              # :100
JUNK                 = "D_junk"                   # :101
ORPHAN_REAL          = "E_orphan_real"             # :102
```

- **A** CANONICAL_MANIFESTED — v9-shape path, a captured manifest row resolves to it
- **B** LEGACY_DUPLICATE — legacy-shape path whose canonical cell IS manifested
- **C** MANIFEST_INFRA — `_index/` / `*.tmp` / `*.partial` / `_SUCCESS`
- **C2** NON_DATA — VM logs / run-artifacts / terraform / tarballs (kept, labelled, never deleted)
- **D** JUNK — unparseable hive-key / invalid shard shape / zero-row
- **E** ORPHAN_REAL — valid shape, rows>0, NO manifest row → `record_captured` backfill, never delete

Acceptance bar: `orphan_class_E == 0` per asset_group AND 0 `unknown` prefix labels (`:29-30`, `:35`). The codex doc
(item 2) cites `ORPHAN_REAL` at `:101` and the reason string at `:363`; current file has it at `:102` — a one-line drift
since the codex's `last_reviewed: 2026-07-24`, not material.

Key structural facts (load-bearing for item 2's blind-spot analysis):

- `_DATA_PREFIXES: tuple[str, ...] = ("raw_tick_data/", "day=")` at `:114` — the sweep only classifies the raw-tick
  corpus into A/B/D/E; everything else is either label-excluded or (blind spot) silently passed through.
- Bucket prefix taxonomy / `_taxonomy_label` at `:956` — the separate "0 unknown" pass.

## 2. `orphan-object-detection.md` codex SSOT

File: `unified-trading-pm/codex/02-data/orphan-object-detection.md`

Core definition (§1): an orphan is present on GCS + parquet-content, **absent** from the manifest shard atom, and
**absent** from the UAC catalogue/oracle expected-coverage set. Both absences required — drop either and it's a
different, already-named finding (`MISSING_EXPECTED`, a phantom, or a `true_gap`).

`migration_orphan_sweep.py` class-E **is** an orphan detector — the only one in the estate — but with three verified
blind spots (§2):

- **Blind spot 1** (§2b): `classify_object` resolves the top-level prefix label FIRST and short-circuits to
  `NON_DATA`/`MANIFEST_INFRA` before any manifest lookup (`:312-316`). Anything in `_NON_DATA_TOP_LEVEL_LABELS` (e.g.
  `dex_pools/`, `lending_indices/`, `:137-145`) is structurally incapable of ever being reported as an orphan — tied to
  the R5 near-miss in §4 (a batch-DELETE of those prefixes as "dead" was nearly authorized; a content-verify later found
  32 legacy-only high-TVL pools and two venues where the legacy object was the only copy in existence).
- **Blind spot 1-bis** (§2b-bis): the opposite gap — an unlabelled top-level prefix is not excluded at all, flows
  straight through to A/B/D/E as ordinary service data. Found 2026-07-23/24
  (`defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md`): 8 objects under a leaked test prefix were misclassified
  as genuine `E_orphan_real`. Fixed in `backfill_orphan_class_e.py` via `split_unknown_prefix_rows()` — closes the
  _backfill_ path only, not the sweep's own classification output.
- **Blind spot 2** (§2c): the classified corpus is raw-tick only; `processed_candles/`, `processed_data/`, `features/`
  are label-excluded. The source comment claims those corpora "have their own re-runnable sweep" — **UNVERIFIED**; the
  codex author grepped and found only migration/rebuild scripts, no dedicated orphan sweep, recorded as an open question
  (§5), not a finding.
- **Blind spot 3** (§2d): `JUNK` absorbs unattributable real data — an unparseable hive key returns `JUNK` before
  `row_count` is consulted, so a real rows>0 parquet with a missing/unparseable `data_type=` segment is
  indistinguishable from a zero-row shell.

§3's operative rule for the new candle sweep: orphan **enumeration** cannot be manifest-driven (an orphan has no
manifest row to enumerate from) — it can only ride **route 3, reuse of the existing single walk**. Never report "0
orphans" from a manifest-driven pass — the honest verdict absent a walk is `NOT ASSESSED`.

§5 open questions (unresolved, relevant to scoping): does `processed_candles/`/`features/` have its own orphan sweep
(no); should the label table gain a third "excluded but unmanifested" state (not decided); is class D splittable (not
decided, real footer-read cost).

## 3. `candle_feature_canonical_path_divergence_2026_07_20.md` todo 7

File: `unified-trading-pm/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md:376-421`

**Status: closed** (`- [x] ✅ 7.`). Chain of events:

- **2026-07-20**: direct pyarrow read of cefi's consolidated availability index (10.36M rows) showed
  `service_name=="market-data-processing-service"` = **6 rows total**, all degenerate, against 20,734 real candle
  objects on a single day — a ~3,400× object↔manifest disconnect. Root cause at the time: candle writes weren't calling
  `record_captured` per shard at all.
- **2026-07-23**: cross-AG confirmation — defi 0/23.5M, cefi 6/10.58M (unchanged), tradfi 73/5.88M (all
  `instrument_type=''`), prediction 168/758,961. Confirmed genuine, pre-existing, cross-AG, not touched by the P6-P8
  path migration.
- **2026-07-27 (slot-12) correction**: the todo's own measurement made the SAME "wrong vocabulary" mistake root-caused
  for cefi elsewhere — querying the aggregated `ohlcv_*` family instead of MDPS's real `data_type=<SOURCE>` + real
  timeframe axis. Re-verified DEFI with correct vocabulary: **7,913 real candle-manifest rows exist**, not 0. Flagged
  that cefi/tradfi/prediction were not re-verified.
- **2026-07-27 (slot-10) resolution**: root cause is the `ohlcv_1m` emission-policy gate's **self-referential
  upstream-completeness check** (`_build_ohlcv_1m_upstream_window` keyed at the SAME shard tuple as the row being
  written) — permanently STRICT_FAIL-locks every `trades`-sourced `ohlcv_1m:current`/`ohlcv_1h:current`/
  `book_snapshot_5` shard's first-ever write. Confirmed via `canonical_writer_stamping.py`. Fixed + shipped
  `market-data-processing-service@caa995c`, plus `record_failed_for_shard` now fires on manifest-write failure instead
  of a swallowed exception.
- **Scope boundary**: this fix targets the TRADES-sourced gated path only (primarily cefi, plus tradfi/prediction if
  their candle source_data_type is `trades`) — does NOT touch DEFI's `dex_pool_swaps` candle path (policy resolver
  returns `None`, skips the gate entirely — consistent with the 7,913 real DEFI rows). Historical-corpus backfill and
  full live-prod verification tracked separately on `mdps_candle_manifest_population_disconnect_2026_07_25.md` todos
  3-6.

**Why this matters for the new sweep**: a candle object with no manifest row today is very plausibly a **pre-fix
write**, not a true orphan (see Design recommendation 3 below).

## 4. MDPS candle path-builder code

Single-derivation chain, UTL → MDPS:

- `unified-trading-library/unified_trading_library/config_interface/paths/registry.py:364-402` —
  `build_canonical_candle_path()`. Delegates the prefix to `build_path("processed_candles", ...)`, then appends
  `filename`. Callers pass the SOURCE `data_type` (operator-ruled 2026-07-21), normalised `timeframe`, canonical
  `instrument_type`, pre-resolved leaf filename. Docstring example at `:384-391` still shows the superseded aggregated
  `data_type="deriv_ohlcv_15m"` form — stale-docstring gap, tracked as todo 15 of the divergence issue doc (item 3).
- `market-data-processing-service/market_data_processing_service/app/core/output_path_helpers.py` — MDPS-side leaf-
  filename SSOT, consumed by 3 call sites (`candle_write_mixin`, `data_sink`, `orchestration_writer`):
  - `candle_leaf_filename()` (`:41-61`) — `ticks.parquet` (bundle) vs `{instrument_id}.parquet` (per-instrument).
    Primary signal: bundled-by-underlying; chain-bundle `data_type` membership kept only as legacy safety net.
  - `build_canonical_candle_object_path()` (`:102-138`) — the actual builder MDPS calls; delegates to UTL, passes the
    SOURCE data type through unchanged.
  - `is_chain_bundle_data_type()` (`:32-38`) — set membership against `CEFI_CHAIN_INSTRUMENT_TYPES` (UAC SSOT, applies
    to TradFi too despite the name).

Locked canonical shape:
`processed_candles/by_date/day={date}/pipeline_mode={pm}/timeframe={tf}/data_type={SOURCE}/instrument_type={it}/venue={v}/{canonical_id}.parquet`

**Per-AG path order still needs empirical spot-check before coding** — the parent issue doc's own claim (defi order
`timeframe/data_type/instrument_type/venue` vs cefi-analog `venue/instrument_type/data_type`) was not independently
re-verified against a live GCS listing in this research pass; verify per-AG before assuming one shape (per the parent
issue's own instruction).

## 5. VM launcher pattern

File: `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (1,411 lines)

Directly relevant precedent — the candle-census/candle-apply category pair, purpose-built 2026-07-22 for this exact
corpus:

- **`_candle_census_cmd()`** (`:765-788`) — READ-ONLY, dry-run-only census of ONE asset_group's `processed_candles/`
  corpus. `$MODE` deliberately ignored — no reachable `--apply` path. Single `&&`-chained command: fresh
  `gcloud storage ls -r "gs://<bucket>/processed_candles/**"` → one dry-run pass of
  `migrate_candle_canonical_2026_07.py` → copy mapping TSV + reconcile report to
  `gs://${CODE_BUCKET}/canonical-migration-candle-census/`. Scoped strictly to `processed_candles/**`. Per-AG bucket
  resolution at `:769-779` — documented bugfix: prediction's real bucket abbreviation is `pred` not `prediction`
  (2026-07-22 review; wrong spelling produced a 404/zero census).
- **`_candle_apply_cmd()`** (`:806-834`) — real migration+purge pass, same enumeration/wiring shape, `$MODE` honored:
  `full` → `--apply --quarantine --content-repair`; `dry` → `--dry-run` reclassify-only. `--shard-of`/`--shard-index`
  fan-out baked from globals directly (not `MIGRATION_EXTRA_ARGS`, which would land on the trailing `gcloud storage cp`
  rather than the python invocation in this compound-chain shape).
- Dispatch wiring: `*-candle-census` branch `:1107-1118`, `*-candle-apply` branch `:1119-1128`. VM-name abbreviation fix
  for `*-candle-apply` at `:1012-1013` (`cdlap` suffix — GCE 63-char name limit; worst case `prediction-candle-apply` →
  71 chars would be rejected). Service selection `:1200-1203` forces `VM_SERVICE=market_data_processing_service` for
  both categories.
- Provisioning: SPOT with `--instance-termination-action=DELETE` (not STOP) unless `ON_DEMAND=true` (`:239-252`) — a
  documented fix (`vm_fleet_preemption_autorecovery_gap_2026_07_23.md`) so a SPOT-preemption relaunch reusing the same
  `VM_NAME_OVERRIDE` doesn't collide with a merely-stopped instance holding that name.
- Boot disk 50GB default (`:162-163`), raised from a 10GB default that caused disk-pressure OOMs on long ranges.
- Security precedent: `WORKERS`/`TRADFI_TICK_BUCKET` validated as bare positive-integer/RFC-bucket-name regexes _before_
  any `_*_cmd()` builder embeds them into a VM-side `bash -c` string (`:265-319`) — closes a shell-injection path found
  2026-07-22. Any new candle-sweep command builder accepting an operator-supplied env var must go through the same
  host-side validation gate before string-embedding.

## Design recommendations for the new candle sweep

1. **Do not build a new whole-corpus walk.** Per the codex SSOT §3, orphan enumeration for `processed_candles/` can only
   ride "route 3" — reuse of a single existing walk. `_candle_census_cmd()` already performs exactly one
   `gcloud storage ls -r` walk per AG; new orphan-detection logic should be bundled as an additional pass over that same
   enumeration output, not a second independent listing.
2. **Extend `migration_orphan_sweep.py`'s A-E model, don't reinvent it — but adapt class-E semantics.** The current
   sweep's `_DATA_PREFIXES` deliberately excludes `processed_candles/` (blind spot 2, after an earlier smoke mis-read
   7,946 processed-candle objects as class-E). A candle-scoped sweep needs its own manifest-coverage join (SOURCE
   `data_type` + `pipeline_mode`/`timeframe` shape) — it can't just flip the exclusion off; the coverage grain and key
   differ from raw-tick.
3. **Treat "no manifest row" as ambiguous, not automatically E_orphan_real, for candles specifically.** Todo 7 just
   proved candle-manifest population itself was broken for the trades-sourced path (fixed `caa995c`) and is still
   unverified for the historical corpus and for tradfi/prediction/cefi beyond the DEFI spot-check. A candle object with
   no row today is plausibly a pre-fix write, not a true orphan — distinguish "no row, written before `caa995c`" from
   "no row, written after" wherever a write timestamp is recoverable, to avoid re-litigating todo 7's closed root cause
   as a false new finding.
4. **Reuse the label-exclusion caution from blind spot 1/1-bis directly.** Any new prefix this sweep excludes (e.g.
   `_quarantine/`, migration-in-flight sentinels) must be recorded in the same turn per the codex's §6 maintenance rule,
   with an explicit statement of whether its contents are known-manifested — an unrecorded exclusion is exactly how the
   `dex_pools/`/`lending_indices/` near-miss happened.
5. **Follow the `_candle_census_cmd`/`_candle_apply_cmd` split precedent for the launcher.** A read-only,
   `$MODE`-ignoring `<ag>-candle-orphan-sweep` category with no `--apply` path, paired with a separately-gated
   apply/backfill category if a `record_captured` backfill is needed later — mirroring how class-E backfill is already
   separate (`backfill_orphan_class_e.py`) from the sweep itself. Reuse the existing per-AG bucket resolution (including
   the `prediction`→`pred` fix) and the WORKERS/bucket-name validation gates.
6. **Report `NOT ASSESSED`, never an unmeasured `0 orphans`,** for any candle-orphan run that isn't manifest+walk-
   joined — the codex's explicit, named correctness rule (§3 corollary, §6), directly enforceable given todo 7's fresh
   evidence that candle-manifest coverage cannot yet be trusted as complete even where rows exist.

## Open items before implementation starts

- Per-AG candle path segment order (defi vs cefi vs tradfi/sports/prediction) needs a live GCS spot-check, not just the
  parent issue doc's claim — not independently re-verified in this research pass.
- Whether `unified_api_contracts.canonical_path_templates`/`is_valid_shard_key` already has a defined `ShardKey` shape
  for candles (vs raw-tick) was not confirmed — check before hand-rolling a new shard-key dataclass.

## Todos

- [ ] [DATA] P1. **Build the MDPS candle-layer orphan sweep (todo 1 of the parent tooling-gap doc)** — this doc is a
      pre-implementation research brief only; the actual sweep tool has not been built, and its own "Open items before
      implementation starts" (per-AG path segment order spot-check, ShardKey shape confirmation) remain unresolved.
