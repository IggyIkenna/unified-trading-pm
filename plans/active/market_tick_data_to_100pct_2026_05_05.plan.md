---
title: "market-tick-data-service to 100% honest coverage across all 5 asset groups"
priority: P0
status: active
owner: harsh
created: 2026-05-05
type: deployment
epic: data-pipeline-completion
completion_gates:
  code: none
  deployment: D2
  business: none
repo_gates:
  - repo: market-tick-data-service
    deployment: D2
depends_on:
  - instruments_to_100pct_eod_2026_05_04
  - instruments_and_market_tick_data_completion_2026_05_01
isProject: false
---

## Live operations log (newest first — read this to know what's happening RIGHT NOW)

This section is the operating surface. Every audit run, finding, fix decision, and background-agent dispatch lands here
with timestamp + status. If you're checking on the work, start here. The phase scaffolding below is the framework;
this log is the ground truth.

| Timestamp (UTC) | Phase | What | Status | Output / link |
| --------------- | ----- | ---- | ------ | ------------- |
| 2026-05-05 ~current | DISCOVERY-0 | Plan restructure to live-ops format + audit cell enumeration starting | in_progress | this doc |

## Discovery audit — 2026-05-05+ (the actual current work)

**Why this exists**: Ikenna's 2026-05-05 callout (manifest/UI/GCS three-layer disagreement) + Harsh's instruction to
treat this as a **systematic discovery exercise across the whole MTDS surface** — find every disagreement, not just
the ones we already know about. The phases below (0 → 4) describe an idealised flow; this section captures what we
are actually doing day-by-day.

### Goal

Build a complete picture of where MTDS manifest, MTDS GCS-truth, and MTDS data-status UI disagree across **every**
`(asset_group, venue, data_type, instrument_type)` cell — then fix the underlying writers/readers/schemas/UIs at the
root, then rebuild manifests, then (and only then) launch paid backfills for genuinely-missing data.

### Approach (overview)

1. **Enumerate the audit matrix** — every cell from UAC's `VENUES_BY_ASSET_GROUP × DATA_TYPES_BY_ASSET_GROUP ×
   instrument_types`, with a representative instrument per cell. Output: a JSON cell list consumed by the audit
   script.
2. **Build the cell-probe audit script** — for one cell + one date, query the manifest (what API/manifest say), then
   probe GCS at every known legacy path shape (the 8 drift axes), record what's on disk, classify the disagreement.
   **Critically**: flag any path it finds that doesn't match a known axis — that's a *new* drift axis we don't know
   about.
3. **Smoke the script** on 1-2 cells manually before fanning out, to verify the probing logic.
4. **Fan out 10-15 background agents in parallel** (Opus 4.6 first while we calibrate, then Sonnet/Opus per workload).
   Each agent owns a chunk of cells, runs the audit script per cell × 15 sample dates (5 captured + 5 missing + 5
   attempted_failed), writes CSV findings.
5. **Run 6 cross-cutting structural checks** in parallel: schema-version drift, written_at chronology, bucket name
   drift, per-VM shard staleness, schema-vs-SchemaDefinition parity, empty-vs-failed classification accuracy. These
   catch failure modes that don't show up as per-cell GCS path mismatches.
6. **Aggregate findings here** — drift axes (known + new) with severity, AGs affected, root-cause repo, fix
   dependencies.
7. **Land fixes in dependency order** across UTL / UAC / MTDS / deployment-api / deployment-ui / recon script /
   rebuild scripts. Quickmerge `--agent` per repo. Cross-repo fixes get aligned commits so we don't leave the stack
   half-migrated.
8. **Re-run audit matrix** to confirm inverse-phantom rate <1% per cell and the data-status UI stops lying. Only then
   evaluate genuine gaps and launch paid backfills.

### Background-agent rate-limit hygiene

We're dispatching 10-15 parallel agents. Three rate-limit ceilings to respect:

| Ceiling | Limit | Mitigation |
| ------- | ----- | ---------- |
| GCS list ops | ~1000 list_blobs/sec per project | Each agent runs `list_blobs(prefix=...)` not full bucket scans; cap workers per agent at 4. |
| Anthropic API | per-org tokens/min | Stagger agent dispatch in waves of 5; Opus 4.6 first wave for calibration, then scale. |
| Tardis/Databento | paid quotas | **Audit phase is read-only against GCS + manifest only — no venue API calls.** |

Each background-agent prompt includes: the goal of the audit, the 8 known drift axes with provenance, the cell-probe
script path + invocation, the "if you find a new path shape NOT matching any known axis, STOP and report it" rule,
and a write-only-to-CSV-do-not-modify-anything restriction. Agents return CSVs; main session aggregates.

### Cell enumeration (TBD — fill in next)

To be populated after Step 1 of approach. Will list:

- Total cell count.
- Per-AG breakdown.
- JSON file path under `/tmp/mtds-audit-cells.json` (gitignored — just for the audit run).
- Representative instrument chosen per cell (canonical from UAC).

### Findings table (per drift axis — fill in as audit completes)

| Axis | Description | Known/New | AGs affected | Rows affected (est.) | Severity | Root-cause repo | Fix dependency | Status |
| ---- | ----------- | --------- | ------------ | -------------------- | -------- | --------------- | -------------- | ------ |
| 1 | Hive vocab `category=` ↔ `asset_group=` | known | TBD | TBD | TBD | TBD | — | TBD |
| 2 | Path prefix top-level vs `raw_tick_data/by_date/` | known | TBD | TBD | TBD | TBD | — | TBD |
| 3 | `instrument_type` casing | known | TBD | TBD | TBD | TBD | — | TBD |
| 4 | Empty `instrument_type` (schema-v4 vestige) | known | TBD | TBD | TBD | TBD | — | TBD |
| 5 | Chain-bundle equivalence (option ↔ options_chain) | known | TBD | TBD | TBD | TBD | — | TBD |
| 6 | DeFi venue overload `PROTOCOL-CHAIN/` vs split | known | DEFI | TBD | TBD | TBD | — | TBD |
| 7 | DeFi no-asset-group hive segment | known | DEFI | TBD | TBD | TBD | — | TBD |
| 8 | Polymarket 9-segment layout vs flat | known | PREDICTION | TBD | TBD | TBD | — | TBD |
| 9+ | NEW — discovered during this audit | new | TBD | TBD | TBD | TBD | TBD | TBD |

### Fix manifest (one row per fix that needs to land — fill in as findings drive it)

| # | Fix | Repo | File | Drift axis closed | Commit | PR | Status |
| - | --- | ---- | ---- | ----------------- | ------ | -- | ------ |
| — | (TBD — populated after audit) | | | | | | |

### Background-agent dispatch log

| Wave | Time (UTC) | Agents | AGs/venues covered | Model | Result | Notes |
| ---- | ---------- | ------ | ------------------ | ----- | ------ | ----- |
| — | (TBD — populated as agents are dispatched) | | | | | |

### Cross-cutting structural checks

| # | Check | Status | Output / finding |
| - | ----- | ------ | ---------------- |
| 1 | Schema-version distribution per AG | TBD | |
| 2 | `written_at` chronology vs GCS object creation | TBD | |
| 3 | Bucket name drift (manifest references vs `gsutil ls`) | TBD | |
| 4 | Per-VM shard staleness (`_index/per_vm/*.parquet` backlog) | TBD | |
| 5 | Schema columns vs registered SchemaDefinition parity | TBD | |
| 6 | empty_confirmed/attempted_failed classification accuracy | TBD | |

### Commit cadence

Every natural milestone gets a commit + push to `live-defi-rollout`. Targets in order:

- [ ] Plan restructure (this commit) — `chore: restructure MTDS plan as live-ops surface for discovery audit`
- [ ] Audit cell enumeration JSON written + script committed
- [ ] First wave of agent findings aggregated into Findings table
- [ ] Each drift-axis fix lands as its own commit/PR
- [ ] Final audit re-run + sign-off commit

PM repo doc-only fast-path: plan changes target `main` directly (per workspace CLAUDE.md PM/Codex doc-only fast-path).

---

## Context

Sibling plan to [`instruments_to_100pct_eod_2026_05_04.plan.md`](instruments_to_100pct_eod_2026_05_04.plan.md). Same
shape, different service.

- **Service**: `market-tick-data-service` only — raw tick downloads. Not instruments-service (covered by sibling), not
  market-data-processing-service (downstream candle generation, separate plan).
- **Asset groups**: all five — `cefi`, `tradfi`, `sports`, `prediction`, `defi`.
- **Target**: ≥99% `captured + empty_confirmed` for `service=market-tick-data-service` under the secondary-cutoff
  denominator. "Honest" means manifest row in `{captured, empty_confirmed}` AND parquet present at the canonical GCS
  path.
- **Batch only.** Live forward-poll is the next milestone (out of scope here). Forward-poll launchers are referenced for
  context but not driven from this plan.
- **Non-goals (this plan)**: instruments-service backfill (sibling plan owns it), MDPS candle generation, deployment-ui
  drilldown bug fixes (parent epic Phase 0), feature-service / ML re-runs.

**Why a separate plan**: instruments-service is a prerequisite for MTDS — the universe of instruments per
`(asset_group, venue, day)` is what MTDS iterates over to download ticks. Tracking MTDS as its own plan keeps the
instruments-side pacing visible (sibling plan) and gives MTDS its own EOD-style success criterion. The two plans share
Phase 0 phantom-recon mechanics but write to different buckets:

| Service                  | Manifest path                                                         |
| ------------------------ | --------------------------------------------------------------------- |
| instruments-service      | `gs://instruments-store-{ag}-{pid}/_index/availability_index.parquet` |
| market-tick-data-service | `gs://market-data-tick-{ag}-{pid}/_index/availability_index.parquet`  |

The phantom recon script (`reconcile_phantom_manifest_rows_all.py`) reads the `instruments-store-*` bucket — for MTDS
shards we need a different verification path. See Phase 0 below.

## 2026-05-05 prerequisite — read this before launching any MTDS work

Two compounding orchestrator bugs were diagnosed + fixed during the Phase 2 CeFi gap audit and they materially change
how this plan should be executed. Sibling plan with the full diagnosis:
[`cefi_phase2_gap_audit_2026_05_01.plan.md`](cefi_phase2_gap_audit_2026_05_01.plan.md) § "2026-05-05 fix landed —
BUG-X1 + BUG-X2".

### BUG-X1 — instrument_id vocabulary mismatch (Tier-3 sentinel false-positives)

**Symptom in the manifest**: ~40k DERIBIT + 3k ASTER + 2k BYBIT `attempted_failed` rows on per-instrument data_types
(`trades` / `book_snapshot_5` / `derivative_ticker`) where the `instrument_id` column was the UAC canonical form
(`BTC-PERP`, `ADA-PERP` etc.) and `error_reason` was `"OPTION row requires 'expiry_date'..."`. Pattern was identical
counts across all 10 perps per data_type — a smell that revealed they were sentinel fan-out rows, not real fetch
attempts.

**Root cause**: the orchestrator's `captured_per_instrument_shards` set was populated with the writer's wire-format
symbol (`BTC-PERPETUAL`, `BTCUSDT`, `BTC-USDT-SWAP`, `ADA_USDC-PERPETUAL`, `BTCF0:USTF0`). UAC's MVP seed table
(`_PERP_MVP_SEED_INSTRUMENTS`) emits canonical IDs (`BTC-PERP`). The set-diff at the Tier-3 sentinel comparison never
matched on perp venues — every captured shard re-emitted as a sentinel `attempted_failed` row even on dates where the
data was successfully captured.

**Fix shipped**:

- **MTDS commit `fe5cc2c`** on `live-defi-rollout`: added `_canonicalize_captured_instrument_id(venue, raw_symbol)`
  helper in `market_tick_data_service/engine/orchestrator.py`. Maps wire→canonical at the captured-side write into
  `captured_per_instrument_shards`. Driven by the existing `_VENUE_INSTRUMENT_TYPE` dict so adding a new perp venue
  updates one place. Never mutates the parquet `file_stem` or manifest `instrument_id` column — those keep wire form as
  the immutable downstream-reader contract. 28 unit tests in `tests/unit/test_orchestrator_canonicalize_captured.py`
  lock the per-venue rules. PR #106 (target staging).
- **UAC commit `82d7d50`** on `live-defi-rollout`: fixed three sub-bugs in `get_expected_instruments_for_venue`'s
  default seed path (`unified_api_contracts/registry/market_data_categories.py`):
  1. `-FUTURES` venues (BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES, OKX-FUTURES) fell through to SPOT branch and
     seeded `BTC-USDT` instead of `BTC-PERP`.
  2. `derivative_ticker` returned PERP seeds unconditionally — even for spot-only venues (BINANCE-SPOT, OKX-SPOT,
     COINBASE-SPOT, UPBIT, \*-SPOT) that physically can't publish derivative_ticker.
  3. `trades` / `book_snapshot_5` ignored the venue's `VENUE_DATA_TYPE_CAPABILITIES` entry — ASTER (no `book_snapshot_5`
     capability) seeded book sentinels anyway, creating 14 false-miss rows per day. All three closed by consulting
     `VENUE_DATA_TYPE_CAPABILITIES` as the SSOT before emitting any seed. PR #44 (target staging). 5 new tests under
     `TestSeedDispatcherVenueClassification`.

### BUG-X2 — venue-level error fanned out as if per-instrument (manifest lying)

**Symptom**: a single row in a Tardis bundle missing `expiry_date` raised `ValueError`, the exception was caught at the
venue level (`failed_shards[venue] = "OPTION row requires..."`), and the Tier-3 sentinel stamped that 80-char exception
text onto **every** per-instrument sentinel row for that (venue, date, dt). Made it look like every perp failed schema
validation when in fact one option row in the bundle did. Same pattern in the sports Tier-2 fan-out.

**Fix shipped**: MTDS commit `fe5cc2c` (same commit as X1). When `classify_venue_error` cannot bucket the exception, the
sentinel writes the generic code `VENUE_FETCH_FAILED` instead of leaking exception text. Descriptive message stays in
logs; manifest stops lying. Applied symmetrically to the CeFi Tier-3 path and the sports Tier-2 fan-out.

### What this means for execution of this plan

1. **Do NOT trust the current manifest's `attempted_failed` numbers as ground truth for which shards genuinely failed.**
   A large chunk of the 86k attempted_failed CeFi rows (39k of them — Cluster B `expiry_date` errors) are stale sentinel
   artefacts from the 2026-04-29/30 366-VM rollout, not real per-instrument failures. The corresponding parquets were
   either captured successfully (under wire-form `instrument_id`) or genuinely never attempted. Phase 0.1 inverse-audit
   catches both.
2. **Phase 1.5 manifest rebuild is the right primary tool for these stale rows.** A rebuild walks GCS and re-keys
   manifest rows under canonical IDs (post fix); sentinel scans now correctly suppress duplicates. **Re-attempting
   instead of rebuilding burns Tardis API quota for no benefit.**
3. **VM relaunches must include the fix.** Rebuild tarballs after pulling `live-defi-rollout` head (or `main` once PR
   #106 lands) so launched VMs run with the canonicalize helper. Bare `create-code-tarballs.sh` re-tars CORE only; pass
   `--all` for full coverage of UAC + MTDS changes.
4. **No CeFi venue needs to be excluded.** The capture path was always working — only the manifest accounting was wrong.
   Going forward, captured shards will register correctly against UAC seeds.
5. **ASTER is genuinely stuck.** 0 captured rows of any data_type in the manifest. Unclear whether Tardis has archive
   coverage for ASTER or the wire-symbol format passed by the launcher is wrong. **Investigate before launching ASTER
   VMs**; the X1 fix covers ASTER's vocabulary mismatch but won't help if the upstream archive is genuinely empty.
6. **BUG-X2 fix is incremental data-quality**: existing manifest rows with leaked exception text don't auto-update; new
   venue-level failures will write `VENUE_FETCH_FAILED` instead. Phase 1.5 rebuild will overwrite the stale rows.

### Affected venue list (for cross-reference with Phase 2 launches)

X1 vocabulary mismatch had non-zero blast radius on every per-instrument CeFi venue:

- DERIBIT (perp + linear perp + options chains): wire `BTC-PERPETUAL` / `ADA_USDC-PERPETUAL` etc. → canonical `BTC-PERP`
  / `ADA-PERP`.
- BINANCE-FUTURES, BYBIT, OKX-SWAP, ASTER, HYPERLIQUID: packed/wire forms → `BASE-PERP`.
- BITFINEX-FUTURES (margin pair `BTCF0:USTF0`), BITGET-FUTURES, KRAKEN-FUTURES, OKX-FUTURES: packed → `BASE-PERP`.
- BINANCE-SPOT, COINBASE-SPOT, OKX-SPOT, BITFINEX-SPOT, BITGET-SPOT, KRAKEN-SPOT, UPBIT: packed/dash → canonical
  `BASE-QUOTE`.

After the fix lands, Phase 0.1 inverse-audit per AG will quantify how many of the "missing" rows are X1 stale-sentinel
rows vs genuinely-missing.

### Cross-reference

- Diagnosis + fix detail: [`cefi_phase2_gap_audit_2026_05_01.plan.md`](cefi_phase2_gap_audit_2026_05_01.plan.md) §
  "2026-05-05 fix landed — BUG-X1 + BUG-X2".
- MTDS commit: `fe5cc2c` on `live-defi-rollout` (PR #106 to staging).
- UAC commit: `82d7d50` on `live-defi-rollout` (PR #44 to staging).

## Hard rule before launching ANY backfill: GCS truth check

**Per Ikenna 2026-05-05**: "missing in data-status UI" ≠ "actually missing in GCS". Three independent layers can
disagree, and have all drifted before:

1. **GCS truth** — parquets physically on disk.
2. **Manifest** (`_index/availability_index.parquet`) — schema has been through v3 → v4 → v5 → v6. Older runs may have
   written under older schemas / older path conventions; newer reads may not understand them.
3. **Data-status UI / API** — reads the manifest with its own caching. Built concurrently with the manifest evolving; at
   one point predated the manifest entirely. Caches: `_turbo_cache`, `_INDEX_CACHE`, `_drilldown._cache`,
   `_REF_DATA_CACHE` (5-min TTL).

When any two layers disagree, the UI shows "missing" even though data is on disk. **Re-downloading in that state is
wasted spend.** Cost ladder (most expensive first): Databento, DeFi RPCs (Alchemy/Infura/etc.), Tardis, sports odds-API.
**CeFi (Binance/Bybit/OKX/etc. public) and Prediction (Polymarket/Kalshi) are the only ~free sources** outside VM cost.

**Known drift causes seen before** (expect them again):

- **Hive vocab change** — `category=` (legacy) vs `asset_group=` (post-2026-04 rename) coexist on disk.
- **Bucket / path-prefix change** — top-level `day=*/...` (legacy Tardis writer) vs `raw_tick_data/by_date/day=*/...`
  (post-2026-04 unified writer). UAC `77abd56` + MTDS `2a479ef` standardised this; pre-existing rogue data still on disk
  at the old prefix.
- **Sharding shape change** — options moved from single-file-per-strike to bundled-per-underlying (the 2026-04-30
  combo-bundling migration: ~13M legacy files → ~36k bundled `ticks.parquet`). Old data on disk in old shape; new data
  in new shape; manifest may only know one.
- **`instrument_type` casing** — `PERPETUAL` vs `perpetual`; manifest holds either, disk only has lowercase.
- **Empty `instrument_type`** — schema-v4 manifest rows omit the segment.
- **Chain-bundle equivalence** — manifest `instrument_type=option` / `future` (row-level) vs disk `options_chain` /
  `futures_chain` (writer bundles them per `tardis_shared.finalise_rows_and_path`).
- **Interrupted runs** — example: 12-hour download cut out at 6h. Half the data is on disk; manifest never caught up
  (consolidator didn't merge, or the rebuild was abandoned). UI shows missing; disk has it.

**`reconcile_phantom_manifest_rows_all.py` only catches one direction** — manifest-claims-captured-but-no-parquet (the
forward phantom). It does NOT catch the inverse: parquet-on-disk-but-no-manifest-row (or `attempted_failed` row). The
inverse case is what causes wasted re-downloads. **Phase 0 below adds the inverse check.**

**Decision rule** for each AG after Phase 0:

| Phase 0 result                                   | Action                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------- |
| Forward phantoms only (manifest claims, no disk) | Phase 1 flip → Phase 2 backfill (existing path)                                 |
| Inverse phantoms ≥5% of "missing" sample         | **Manifest rebuild first** (`rebuild_*_manifest.py` for that AG), THEN backfill |
| Both, inverse dominant                           | Manifest rebuild first; re-run Phase 0 after rebuild settles                    |
| Genuinely missing (probed all legacy paths)      | Phase 1 flip → Phase 2 backfill                                                 |

The rebuild path is **far cheaper** than re-downloading — it scans GCS and writes canonical manifest rows; no API spend.

## Prerequisites (instruments-side gate)

MTDS download requires the instruments-service catalogue to be honest for the `(asset_group, venue, day)` shards we're
about to backfill. If the catalogue is incomplete or wrong, MTDS will either skip valid days (catalogue says no
instruments tradeable) or fan out against bad symbols (catalogue lists instruments that never traded).

- [ ] [HUMAN] P0. Confirm sibling
      [`instruments_to_100pct_eod_2026_05_04.plan.md`](instruments_to_100pct_eod_2026_05_04.plan.md) Phase 3
      verification has passed for the asset groups we're about to backfill (CEFI/TRADFI/DEFI/PREDICTION/SPORTS each ≥99%
      under secondary-cutoff). If an AG is still red on instruments-side, defer that AG's MTDS backfill until it's clean
      — running MTDS against an incomplete catalogue burns API quota for nothing.

## Cutoffs (per playbook + UAC `coverage_starts.py`)

Same cutoffs as the parent epic and sibling plan — repeated here so this plan is self-contained:

| Asset group | Start (global)          | End   | Per-shard secondary clip                                          |
| ----------- | ----------------------- | ----- | ----------------------------------------------------------------- |
| CEFI        | 2019-01-01              | today | per-venue inception (`CEFI_SOURCE_COVERAGE_START`)                |
| TRADFI      | 2019-01-01              | today | per-ticker listing (`TRADFI_TICKER_COVERAGE_START`)               |
| SPORTS      | 2020-06-01              | today | odds-API launch + per-bookmaker availability                      |
| PREDICTION  | 2020-06-12 (POLYMARKET) | today | per-venue + per-sub-category (`PREDICTION_SOURCE_COVERAGE_START`) |
| DEFI        | per-protocol launch     | today | per-protocol-per-chain (`DEFI_SOURCE_COVERAGE_START`)             |

Always pass the **global** start; adapter + manifest writer apply the secondary clip via UAC
`clip_dates_to_source_coverage`. Pre-launch days land as `empty_confirmed`, not `attempted_failed`.

## Schema + bundling invariants (do not violate)

These are MTDS-specific and have bitten us before. Carrying them inline so this plan is self-contained.

- **Single bundled file per `(day × underlying × data_type)`** for chains/combos. Options chains, futures combos land as
  one parquet keyed by underlying — never per-contract or per-strike. Combo bundling fix shipped 2026-04-30 + 5
  year-sharded migration VMs. Do not regress.
- **`record_empty(row_key=...)`** for source-returned-200-with-zero-rows.
  **`record_failed(row_key=..., error=classify_venue_error(exc))`** for exceptions. Never write empty placeholder
  parquets to mask phantoms.
- **DERIBIT v6 manifest needs `quote_asset` + `margin_type`** so inverse vs linear bundles don't collide on the same
  underlying (BTC-PERPETUAL vs BTC_USDC-PERPETUAL).
- **Per-VM manifest shards** (`MANIFEST_PER_VM_SHARDS=true`) are required for any 10+ concurrent VM fleet. The
  consolidator daemon merges per-VM shards into the canonical view every ~60s. Confirm `manifest-consolidator-*` VM is
  `RUNNING` before fanning out.
- **Hyperliquid / Aster perpetuals-only guard**: `BaseOnchainPerpAdapter` raises `UnsupportedCapabilityError` for
  `instrument_type=OPTION|FUTURE`. Do not expect option/futures shards for these venues; the UAC
  `get_expected_data_types_for_venue()` registry returns only perpetuals-compatible types — denominator is correct by
  construction.

## Execution DAG

```
Phase 0   (Diagnose — manifest read per AG)
            │
            ▼
Phase 0.1 (GCS-truth check — inverse phantom detection per AG)
   ├── sample N "missing" rows from manifest
   ├── probe ALL legacy GCS paths for each
   └── classify: forward-phantom / inverse-phantom / genuinely-missing
            │
            ▼  (decision branch)
            ├──────────────────────────────────────────┐
            │ inverse phantoms ≥5% of sample           │ inverse phantoms <5% of sample
            ▼                                          ▼
Phase 1.5 (Manifest rebuild for affected AG)   Phase 0.5 (Cross-checks — consolidator alive,
   ├── rebuild_*_manifest.py for AG               in-flight VM scan, tarball freshness)
   ├── consolidator merges per_vm shards                  │
   └── re-run Phase 0 + 0.1 to confirm                    ▼
            │                                  Phase 1 (Flip forward phantoms, parallel by AG)
            └──────────────────────────────────────────┐
                                                       │
                                                       ▼
                              Phase 2 (Launch MTDS backfills, parallel by asset_group)
                                 ├── CEFI       — launch-cefi-sharded-backfill.sh
                                 ├── TRADFI     — launch-tradfi-backfill-vm.sh (singleton-locked)
                                 ├── DEFI       — launch-mtds-{gas-fees,lst-rates,vault-share-price}-backfill-vm.sh
                                 ├── PREDICTION — launch-mtds-prediction-backfill-vm.sh (singleton-locked)
                                 └── SPORTS     — mostly MDPS-side (separate plan); fetch only if raw GCS empty
                                                       │
                                                       ▼  (wait — VMs run hours/days)
                              Phase 3 (Verify, parallel — manifest re-scan + drilldown spot-check)
                                                       │
                                                       ▼
                              Phase 4 (Sign-off + plan close)
```

Realistic ETA caveat: Phase 2 wall-time is dominated by CEFI (Tardis archive, 2019-→today × 9 venues × multiple
data_types per venue). Even with 100 concurrent VMs at ~20 min/shard, full re-run is days. **This is a multi-day push,
not EOD.** Ratchet the scope to the worst-covered slice first; full sweep can run in the background.

## Phase 0 — Diagnose (read-only, parallel)

For each asset group, query the MTDS manifest to learn baseline coverage. Two paths:

**Path A — direct manifest read** (cheapest, runs locally with ADC):

```bash
gsutil cp gs://market-data-tick-{ag}-central-element-323112/_index/availability_index.parquet /tmp/mtds-{ag}.parquet
.venv/bin/python -c "
import pandas as pd
df = pd.read_parquet('/tmp/mtds-{ag}.parquet')
print('total rows:', len(df))
print(df.groupby(['venue','data_type','capture_status']).size().head(50))
"
```

**Path B — deployment-api `/api/data-status/manifest`** (when the API is up — gives the same view the UI uses):

```bash
curl -sS "http://localhost:8004/api/data-status/manifest?service=market-tick-data-service&asset_group=cefi" | jq
```

- [ ] [SCRIPT] P0. Path A read for cefi MTDS bucket → log to `/tmp/mtds-recon-cefi.log`. Capture per-venue,
      per-data_type breakdown of `capture_status` counts.
- [ ] [SCRIPT] P0. Same for tradfi → `/tmp/mtds-recon-tradfi.log`.
- [ ] [SCRIPT] P0. Same for sports → `/tmp/mtds-recon-sports.log`. **Note**: sports MTDS rows are per-bookmaker
      (PINNACLE, BETFAIR_EX, DRAFTKINGS, …), not per-source. The bookmaker is the venue.
- [ ] [SCRIPT] P0. Same for prediction → `/tmp/mtds-recon-prediction.log`.
- [ ] [SCRIPT] P0. Same for defi → `/tmp/mtds-recon-defi.log`. DeFi MTDS data_types include
      `swaps, liquidity, rate_indices, oracle_prices, utilization, rewards, risk_params, gas_fees, lst_rates, perp_funding, tvl`
      — expect long-tail per `(protocol × chain × data_type)`.
- [ ] [HUMAN] P0. **Phantom audit on MTDS buckets**. The reconciler script
      (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`) was originally designed for
      `instruments-store-*` buckets but `ASSET_GROUP_CONFIG` covers MTDS-style hive layouts too — verify by reading the
      script and confirming the prefix template targets `market-data-tick-{ag}-{pid}` for MTDS, or whether a separate
      bucket flag is needed. If the script does NOT cover MTDS buckets, add a `--bucket` override and run it on the MTDS
      bucket before claiming Phase 0 is done. (Path SSOT cross-ref:
      [`02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      § "Phantom audit — re-runnable recipe".)
- [ ] [HUMAN] P0. Review the five `/tmp/mtds-recon-*.log` snapshots. Capture the per-AG counts in the **Notes** section
      below. **Do NOT decide on Phase 2 yet** — Phase 0.1 below must run first. The decision is forward-phantom vs
      inverse-phantom vs genuinely-missing, and Phase 0 only sees one of those three.

## Phase 0.1 — GCS truth check (inverse phantom detection — MANDATORY before Phase 2)

This is the new gate Ikenna asked us to add (2026-05-05). For each AG, we sample rows the manifest claims are missing or
`attempted_failed`, and physically check GCS at every known legacy path shape. If parquets exist, the AG needs a
manifest rebuild — NOT a backfill. Skipping this phase risks paying Databento / Tardis / DeFi RPC / odds-API to re-fetch
data we already have on disk.

**Cost ladder (most expensive first)** — informs how aggressively to sample per AG:

| AG         | API cost                         | Sample size recommendation          |
| ---------- | -------------------------------- | ----------------------------------- |
| TRADFI     | Databento (paid)                 | ≥200 missing rows per venue         |
| DEFI       | RPC + The Graph                  | ≥200 missing rows per (proto,chain) |
| CEFI       | Tardis (paid)                    | ≥200 missing rows per venue         |
| SPORTS     | odds-API (paid)                  | ≥100 missing rows per bookmaker     |
| PREDICTION | ~free (Polymarket/Kalshi public) | ≥50 missing rows per venue          |

CeFi public endpoints (Binance/Bybit/OKX/etc. raw) are free, but Tardis (which we use for the historical archive) is
paid — so CeFi's cost row is "Tardis", not "venue". Treat all 5 AGs as paid for sampling purposes.

### Legacy path shapes to probe per `(ag, venue, data_type, day)` tuple

For every "missing" row sampled, probe ALL of these GCS path shapes before classifying as genuinely-missing. Five known
drift axes (already encoded in `reconcile_phantom_manifest_rows_all.py` in the forward direction; need them encoded in
inverse direction too):

1. **Hive vocab** — `category={ag}/...` (legacy) AND `asset_group={ag}/...` (canonical).
2. **Path prefix** — top-level `day=YYYY-MM-DD/...` AND `raw_tick_data/by_date/day=YYYY-MM-DD/...`.
3. **`instrument_type` casing** — both upper (`PERPETUAL`) and lower (`perpetual`).
4. **Empty `instrument_type`** — schema-v4 rows with no segment.
5. **Chain-bundle equivalence** — manifest `instrument_type=option`/`future` (per-row) vs disk
   `instrument_type=options_chain`/`futures_chain` (bundled per-underlying). For the bundled case, the path is
   `instrument_type=options_chain/data_type={dt}/underlying={base}/ticks.parquet` regardless of how the manifest names
   the per-row instrument_type.

Plus DeFi-specific:

6. **Legacy DeFi venue overload** — `venue=PROTOCOL-CHAIN/` (e.g. `venue=AAVEV3-ETHEREUM/`) where canonical splits to
   `venue=AAVE_V3/chain=ETHEREUM/`.
7. **No-asset-group hive segment** — old DeFi writes that omit the AG segment entirely.

Plus prediction-specific:

8. **Polymarket 9-segment layout** — `venue=POLYMARKET/sub_category=.../market=.../...` vs flat venue path.

### Tooling

Two paths — pick one, both are acceptable:

**Path A — extend `reconcile_phantom_manifest_rows_all.py`** to support `--mode inverse` that walks GCS and reports
parquets without manifest rows. Cleaner long-term — same drift axes are already encoded for the forward direction. The
script lives in `instruments-service/scripts/`.

**Path B — one-off audit script** under `market-tick-data-service/scripts/audit_inverse_phantoms.py` that reads a sample
of "missing" rows from the manifest, builds the legacy-path probe list per drift axis, runs `gsutil ls` (or
`storage_client.list_blobs(prefix=...)`) per probe, and emits a CSV of
`(ag, venue, data_type, day, found_at_path, classification)`. Faster to ship for this one-time gate; Path A is the
proper fix to land afterwards.

- [ ] [HUMAN] P0. Pick Path A or Path B with Ikenna. **Default**: Path B for this push (faster), Path A as a follow-up
      todo to land the inverse mode in the canonical reconciler.
- [ ] [HUMAN] P0. **MUST run on a same-region GCE VM** — cross-region GCS listing is 18× slower (~12 prefixes/sec from
      laptop vs 222/sec on `asia-northeast1-c`). Spin up `e2-standard-4` in `asia-northeast1-c` for the audit. Same
      pattern as the phantom audit recipe in
      [`02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      § "Phantom audit — re-runnable recipe".
- [ ] [SCRIPT] P0. Run the inverse audit per AG, with sample size from the cost-ladder table above. Output:
      `/tmp/mtds-inverse-cefi.csv /tmp/mtds-inverse-tradfi.csv /tmp/mtds-inverse-sports.csv /tmp/mtds-inverse-prediction.csv /tmp/mtds-inverse-defi.csv`
      Each CSV row: `ag, venue, data_type, day, classification, found_at_path`. Classifications:
      `inverse_phantom_axis_<N>` (parquet found at one of the 8 legacy paths), `genuinely_missing` (no parquet at any
      probed path).
- [ ] [HUMAN] P0. **Per AG, compute inverse-phantom rate** = inverse_phantom rows ÷ sample size. Apply the decision
      rule:
  - **<5%** → drift is noise. Proceed to Phase 0.5 → Phase 1 → Phase 2 (existing flow).
  - **≥5%** → AG needs Phase 1.5 manifest rebuild BEFORE backfill. Capture which drift axis dominates (axis 1, 2, 5,
    etc.) — that tells us which rebuild script flag to use.
  - **≥20%** → escalate to Ikenna before any further action. Suggests a recent path/schema change wasn't migrated;
    flagging early avoids re-running the rebuild on shifting ground.
- [ ] [HUMAN] P0. Capture the per-AG decision in the Notes section: rebuild-first vs backfill-first.
- [ ] [HUMAN] P1. **Sanity-check sampling**: pick 5 random `inverse_phantom` rows per AG and manually `gsutil ls` the
      reported `found_at_path` to confirm the parquet really exists and isn't a 0-byte placeholder or directory-marker.
      Audit script bugs are more dangerous than backfill VMs — a false-positive inverse phantom sends us down a rebuild
      path that never lands.

## Phase 0.5 — Cross-checks before fanning out

Before launching any new MTDS backfill VM:

- [ ] [HUMAN] P0. **Manifest consolidator alive.** Per-VM manifest shards aren't mergeable without it.
      `bash gcloud compute instances list --filter='name~"^manifest-consolidator-"' --format='table(name,status,zone)' `
      Should be exactly one `RUNNING`. If absent, launch via
      `bash deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh` before Phase 2.
- [ ] [HUMAN] P0. **In-flight MTDS VM scan.** Don't collide with VMs already running.
      `bash gcloud compute instances list \ --filter='name~"^(cefi-|tradfi-|mtds-|mdps-)"' \ --format='table(name,status,zone,creationTimestamp)' `
      For any RUNNING shard that overlaps the scope you're about to launch, let it finish (or coordinate with the
      operator). Singleton-locked launchers (`launch-tradfi-backfill-vm.sh`, `launch-mtds-prediction-backfill-vm.sh`,
      `launch-sfi-forward-poll.sh`) will refuse to start; non-locked launchers will race.
- [ ] [HUMAN] P0. **Tarball freshness.** If MTDS / UAC / UTL code changed since last backfill run, refresh tarballs:
      `bash bash deployment-service/scripts/vm/create-code-tarballs.sh --all ` Bare invocation only re-tars CORE;
      `--all` is safest for any cross-repo state. Verify with
      `gsutil ls -l gs://deployment-scripts-central-element-323112/code/` — timestamps should be post your last relevant
      commit.
- [ ] [HUMAN] P0. **Zombie-watchdog dict check.** Before launching any new VM-name prefix, confirm the prefix is in
      `VM_PREFIX_TO_BUCKET` in `deployment-service/scripts/vm/vm_zombie_watchdog.py`. New prefix → add it + relaunch the
      watchdog VM (the running watchdog only fetches the Python at boot). Reference incident: 2026-05-05 — 5 prefixes
      silently zombied because launchers were added without dict updates.
- [ ] [HUMAN] P0. **Secret Manager check.** For any venue whose API key isn't in `central-element-323112` SM, ping
      Ikenna before launching. Common ones for MTDS: `tardis-api-key`, `databento-api-key`, `polymarket-api-key`,
      `kalshi-api-key`. `ApiKeyReloader` (UTL) fetches at runtime — missing key = silent failure (validates as empty
      dict if venue-name typo, see Known Gotchas below).

## Phase 1 — Flip phantoms / re-attempt failed shards (parallel by AG)

Run only for asset groups where Phase 0 found phantoms or where `attempted_failed` rows are stuck across runs.

**Critical**: phantoms (`captured` claim, no parquet on disk) must be flipped to `attempted_failed` so the
orchestrator's `_should_skip_shard` lets the next backfill VM retry them. Do NOT write empty placeholder parquets to
mask phantoms — that fudges data quality. Per CLAUDE.md manifest-phantom-audit rule: `record_empty()` is for
legitimately-empty source responses only.

- [ ] [SCRIPT] P0. For each AG with phantoms > 0, run the reconciler against the MTDS bucket (assumes the script
      supports a `--bucket` override or `--service market-tick-data-service` flag — confirm in Phase 0):
      `bash cd ~/unified-trading-system-repos/instruments-service .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \ --asset-group <ag> --service market-tick-data-service \ 2>&1 | tee /tmp/mtds-flip-<ag>.log `
      No `--dry-run` — actually flip phantoms.
- [ ] [SCRIPT] P0. Re-run the dry-run to confirm phantom count → 0 for each flipped AG.

## Phase 1.5 — Manifest rebuild (only for AGs flagged in Phase 0.1)

Run only for AGs where Phase 0.1 found inverse-phantom rate ≥5%. The rebuild script re-scans canonical GCS paths and
writes manifest rows for parquets that exist on disk but have no `captured` manifest row. **Cheaper and faster than a
backfill** — no API spend, just GCS list operations.

**Per-service rebuild scripts** (the right one depends on which manifest needs the rebuild — these target the MTDS
manifest at `market-data-tick-{ag}-{pid}/_index/availability_index.parquet`):

| AG         | Rebuild script (verify before running — paths drift)                        |
| ---------- | --------------------------------------------------------------------------- |
| CEFI       | `market-tick-data-service/scripts/rebuild_cefi_manifest.py` (or equivalent) |
| TRADFI     | `market-tick-data-service/scripts/rebuild_tradfi_manifest.py`               |
| SPORTS     | `market-tick-data-service/scripts/rebuild_sports_manifest.py`               |
| PREDICTION | `market-tick-data-service/scripts/rebuild_prediction_manifest.py`           |
| DEFI       | `market-tick-data-service/scripts/rebuild_defi_manifest.py`                 |

If any of these don't exist, the alternative is a generic UTL rebuild via the manifest_consolidator's full re-scan mode
— confirm with Ikenna which is canonical for MTDS today before running.

- [ ] [HUMAN] P0. Verify the right rebuild script exists for each affected AG. If absent, **stop and ping Ikenna** — do
      not improvise a rebuild script for production manifests.
- [ ] [HUMAN] P0. **Pre-flight**: tarball refresh + run on same-region VM. Rebuilds list every parquet in the bucket —
      same 18× perf cliff as the audit. Use the phantom-audit recipe pattern from the codex doc.
- [ ] [HUMAN] P0. **Pass `per_vm_shards=True`** when running rebuild — without it, the rebuild's writes fight the
      consolidator daemon's CAS retries and most rebuild output gets dropped. Reference incident: 2026-05-02 DeFi
      rebuild lost 80k rows compacted to 12k canonical because of CAS contention. SSOT:
      [`02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      § "Per-VM shard layout".
- [ ] [SCRIPT] P0. Run the rebuild for each affected AG:
      `bash cd ~/unified-trading-system-repos/market-tick-data-service VM_NAME=rebuild-mtds-{ag}-$(date +%Y%m%d-%H%M%S) MANIFEST_PER_VM_SHARDS=true \ .venv/bin/python scripts/rebuild_{ag}_manifest.py 2>&1 | tee /tmp/mtds-rebuild-{ag}.log `
      Each unique `VM_NAME` writes its own per-VM shard so concurrent runs don't collide.
- [ ] [SCRIPT] P0. **Force-merge** after each rebuild so readers see the canonical view immediately:
      `bash .venv/bin/python -m unified_trading_library.manifest_consolidator \ --bucket market-data-tick-{ag}-central-element-323112 `
      Idempotent + safe to run concurrently with the scheduled cycle.
- [ ] [HUMAN] P0. **Re-run Phase 0 + 0.1 for the rebuilt AG.** Verify:
  - Forward phantoms (claim-no-disk) ≈ 0.
  - Inverse phantoms (disk-no-claim) ≈ 0.
  - "Missing" denominator dropped by roughly the inverse-phantom count from Phase 0.1. Capture the delta in the Notes
    section. If the inverse-phantom rate stays ≥5%, the rebuild script doesn't cover the dominant drift axis — escalate
    to Ikenna; do NOT proceed to Phase 2 for that AG.
- [ ] [HUMAN] P0. Only after the rebuilt AG's Phase 0/0.1 numbers are clean does it become eligible for Phase 2.

## Phase 2 — Launch MTDS backfills (parallel by asset group)

**Gate**: each AG must have completed Phase 0.1 (and Phase 1.5 if it was flagged) before its Phase 2 launches. AGs in
different states proceed independently — e.g. PREDICTION can backfill while CEFI is mid-rebuild, since they hit
different buckets.

This is where the actual MTDS download work happens. Unlike instruments-service, MTDS **does have dedicated VM launchers
per asset_group** (instruments-service falls back to a local-driver script — that asymmetry caused confusion in the
sibling plan). All MTDS launchers route through `setup-data-pipeline-vm.sh` with `VM_TASK=cefi-backfill` /
`tradfi-backfill` / etc. and write per-VM manifest shards (consolidator merges).

**Force-flag warning**: every launcher accepts `--force`. With `force=true`, the orchestrator re-fetches every shard
regardless of `_should_skip_shard` — billable Tardis/Databento API cost. **Use `force=false` for gap-fill.** Reserve
`force=true` for retesting one specific shard or after a code-fix that requires re-running known-bad data.

### CEFI

Tardis-backed venues + Hyperliquid/Aster on-chain. The 2026-04-29 366-VM rollout (`run-ts=20260429-154202`) covered most
of the space; gap-fill is what's left.

- [ ] [HUMAN] P0. Confirm Phase 0 cefi MTDS gap (review `/tmp/mtds-recon-cefi.log`).
- [ ] [HUMAN] P0. For any year × venue × instrument_type slice still showing `attempted_failed`, re-launch via:
      `bash bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh \ --venues BINANCE-SPOT,BINANCE-FUTURES,BYBIT,OKX,DERIBIT,COINBASE,UPBIT,HYPERLIQUID,ASTER \ --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \ --data-types trades,book_snapshot_5,derivative_ticker,liquidations \ --shard-by year `
      Verify the launcher's flag names by reading the script header before running — flag names drift; `--shard-by` and
      `--data-types` may be `--shard-strategy` and `--data-type` depending on commit.
- [ ] [HUMAN] P0. **DERIBIT options chain** — bundled per-underlying, not per-strike. Verify by sampling any captured
      day: should be `instrument_type=options_chain/data_type=trades/underlying=BTC/ticks.parquet` (bundled), no
      per-contract files. If you see per-contract files post-2026-04-30, that's a regression — flag to Ikenna.
- [ ] [HUMAN] P1. **DERIBIT v6 inverse/linear split** — manifest must populate `quote_asset` + `margin_type` for DERIBIT
      chain shards. Verify by sampling a DERIBIT row: both columns non-empty (e.g.
      `quote_asset=USD, margin_type=inverse` for BTC-PERPETUAL; `quote_asset=USDC, margin_type=linear` for
      BTC_USDC-PERPETUAL).
- [ ] [HUMAN] P1. **OOM watch** — CeFi VMs occasionally `rc=137` (SIGKILL by systemd OOM-killer) on heavy
      instrument_types (DERIBIT options chain especially). No `EXIT_STATUS` written for rc=137. Diagnose via Cloud
      Logging kernel OOM query (see
      [`05-infrastructure/vm-tarball-deployment.md`](../../codex/05-infrastructure/vm-tarball-deployment.md) § "Exit
      codes"). Bump machine type or shard year-by-year.

### TRADFI

CME futures + ES options + ETFs + VIX index — most of this landed 2026-04-30. Only gap-fill is expected.

- [ ] [HUMAN] P0. Confirm Phase 0 tradfi MTDS gap (review `/tmp/mtds-recon-tradfi.log`).
- [ ] [HUMAN] P0. For ES options chain or ETF gaps, re-launch via the singleton-locked launcher:
      `bash bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh \ --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \ --instrument-ids 'CME:FUTURE:ES.FUT;CME:OPTION:ES.OPT;NYSE:ETF:IBIT;...' \ --data-types ohlcv_1m,trades,tbbo `
      The singleton lock will refuse to launch if any `tradfi-bf-*` VM is RUNNING. Use `--force` only if you've
      confirmed the prior VM is genuinely zombied.
- [ ] [HUMAN] P1. **VIX index already done** — do not re-fetch. 1,585 days at
      `asset_group=tradfi/venue=CBOE/instrument_type=index/data_type=ohlcv_15m/VIX.parquet`. If a strategy needs <15m
      granularity, that's a separate sourcing question — flag to Ikenna.
- [ ] [HUMAN] P2. **VIX futures full-tick chain — deferred**. UAC `_CBOE_INSTRUMENTS = []` placeholder. Out of scope for
      this plan; needs separate plan + declarative VX contract calendar.

### DEFI

Per-protocol-per-chain inception dates from `DEFI_SOURCE_COVERAGE_START`. DeFi MTDS uses `collect-evm-defi` /
`collect-dex-swaps` CLI handlers (NOT the `download` operation — DeFi venues are in `VENUE_TO_ASSET_GROUP['defi']`).

- [ ] [HUMAN] P0. Confirm Phase 0 defi MTDS gap (review `/tmp/mtds-recon-defi.log`).
- [ ] [HUMAN] P0. **Cloud Run DeFi collection job** is the canonical batch path for swaps/liquidity (NOT a VM). Verify
      it's healthy + re-trigger any failed runs. Cross-check with the consolidated DeFi pipeline plan
      ([`consolidated_defi_data_pipeline_2026_04_15.plan.md`](consolidated_defi_data_pipeline_2026_04_15.plan.md)) for
      the canonical operations workflow.
- [ ] [HUMAN] P0. Specialised MTDS launchers for the long-tail DeFi data_types:
      `bash bash deployment-service/scripts/vm/launch-mtds-gas-fees-backfill-vm.sh         --start-date <protocol-launch> bash deployment-service/scripts/vm/launch-mtds-lst-rates-backfill-vm.sh         --start-date <protocol-launch> bash deployment-service/scripts/vm/launch-mtds-vault-share-price-backfill-vm.sh --start-date <protocol-launch> `
      One per data_type per protocol — verify launcher flags before running.
- [ ] [HUMAN] P1. **`validate_api_keys_for_venues` venue-name gotcha** — passes canonical venue names
      (`UNISWAPV3-ETHEREUM`, `AAVEV3-ETHEREUM`), NOT data-source slugs (`thegraph`, `databento`). Returns empty dict
      silently on wrong shape; downstream adapters silently fail. If a DeFi VM logs "missing key" on a venue you know
      has the secret, suspect this first.

### PREDICTION

POLYMARKET (from 2020-06-12) + KALSHI (from 2021-07-19). Singleton-locked because Polymarket gamma rate-limits per-IP
and the project egress NAT is shared.

- [ ] [HUMAN] P0. Confirm Phase 0 prediction MTDS gap (review `/tmp/mtds-recon-prediction.log`).
- [ ] [HUMAN] P0. Launch via the singleton-locked launcher:
      `bash bash deployment-service/scripts/vm/launch-mtds-prediction-backfill-vm.sh \ --venue POLYMARKET --start-date 2020-06-12 --end-date $(date -u +%Y-%m-%d) \ --data-types prediction_trades,prediction_book_snapshot,prediction_market_metadata bash deployment-service/scripts/vm/launch-mtds-prediction-backfill-vm.sh \ --venue KALSHI --start-date 2021-07-19 --end-date $(date -u +%Y-%m-%d) \ --data-types prediction_trades,prediction_book_snapshot,prediction_market_metadata `
      Singleton lock will refuse a second VM in the zone — wait for the first to finish before launching the next.
- [ ] [HUMAN] P1. **Polymarket cursor-sharding** — if instruments-side prediction work surfaced cursor bands per (year,
      month) (sibling plan Day 2), MTDS may want the same trick if download throughput is timeout-bound. Defer until
      Phase 0 numbers come in; bare launcher is the first attempt.

### SPORTS

**Mostly downstream of MDPS, not a fresh fetch.** Per the playbook: "a large fraction of the missing manifest rows for
`ODDS_HORIZON_BUCKET` and similar are already fetched into raw GCS but not yet processed through MDPS into the canonical
per-league partitions. The lift is mostly MDPS-side, not fetch-side."

- [ ] [HUMAN] P0. Confirm Phase 0 sports MTDS gap (review `/tmp/mtds-recon-sports.log`). The "venue" axis here is
      bookmaker (PINNACLE, BETFAIR_EX, DRAFTKINGS, …), not source.
- [ ] [HUMAN] P0. **Sample raw odds-API GCS bucket** for any date the manifest claims missing. If raw data exists, this
      is an MDPS processing gap (out of scope here, separate MDPS plan). If raw data is genuinely missing, then a fresh
      odds-API fetch is needed.
- [ ] [HUMAN] P1. For genuine fetch gaps, the odds-API has its own backfill path — coordinate with the sports-side agent
      / sibling plan. **Do not** launch parallel sports VMs while
      [`instruments_to_100pct_eod_2026_05_04.plan.md`](instruments_to_100pct_eod_2026_05_04.plan.md) sports work is
      mid-flight; partition collisions will cause manifest noise.

## Phase 3 — Verify (parallel)

Verification has to cover **both directions** now, not just forward phantoms:

- [ ] [SCRIPT] P0. **Forward phantom check** — for each AG, re-read the MTDS manifest and confirm forward-phantom count
      is 0 + `attempted_failed` count has dropped substantially since Phase 0 baseline.
- [ ] [SCRIPT] P0. **Inverse phantom check** — for each AG, re-run the Phase 0.1 inverse audit on a fresh sample.
      Inverse-phantom rate should be <1% (down from whatever Phase 0.1 found). If it ticks back up post-backfill, the
      backfill writer is producing parquets without manifest rows — flag immediately, don't claim done.
- [ ] [HUMAN] P0. Snapshot the deployment-ui drilldown for `service=market-tick-data-service` per asset_group. Each
      should show ≥99% `captured + empty_confirmed` under the secondary-cutoff denominator.
- [ ] [HUMAN] P0. **Cache-clear the deployment-api before reading the drilldown** — UI is backed by 4 cache layers
      (`_turbo_cache`, `_INDEX_CACHE`, `_drilldown._cache`, `_REF_DATA_CACHE`, all 5-min TTL). Hit
      `/api/data-status/turbo/clear` (sibling-plan Day 2 fix landed all 4 clears) before sampling, else you may read
      stale numbers from before Phase 1.5 / Phase 2.
- [ ] [HUMAN] P1. Spot-check 5 random `(asset_group, day, venue, instrument_type, data_type)` rows per AG: follow each
      to the canonical GCS path and confirm the parquet exists. Specifically check chain-bundled cases: DERIBIT options
      chain (`underlying=BTC|ETH`), CME ES options chain (`underlying=ES`), futures combos.
- [ ] [HUMAN] P1. Schema validation parity — the View Schema modal in the UI for any MTDS data_type returns the same
      columns as the registered `SchemaDefinition` in the service code. Sibling plan / parent epic Phase 0 covers
      drilldown bug fixes; this verifies write-time validation actually fired.

## Phase 4 — Sign-off + plan close

- [ ] [HUMAN] P0. Update parent epic
      ([`instruments_and_market_tick_data_completion_2026_05_01.plan.md`](instruments_and_market_tick_data_completion_2026_05_01.plan.md))
      progress notes: mark MTDS slice ≥99% under secondary-cutoff. Link to this plan.
- [ ] [HUMAN] P0. Brief Ikenna on results + any gotchas surfaced (likely candidates: new phantom drift axes, schema
      mismatches, missing SM secrets, launcher flag drift).
- [ ] [HUMAN] P1. If any per-AG gap remained at <99% for legitimate reasons (provider outage, bookmaker shutdown, etc.),
      document it in
      [`02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      under "Known coverage gaps" so future runs don't chase it.
- [ ] [AGENT] P2. Mark this plan complete and move to `plans/archive/`.

## Files / commands referenced

| Repo                     | File / command                                                                                 | Phase         |
| ------------------------ | ---------------------------------------------------------------------------------------------- | ------------- |
| instruments-service      | `scripts/reconcile_phantom_manifest_rows_all.py` (with `--bucket` / `--service`)               | 0,1,3         |
| instruments-service      | `scripts/reconcile_phantom_manifest_rows_all.py --mode inverse` (Path A — to be added)         | 0.1,3         |
| market-tick-data-service | `scripts/audit_inverse_phantoms.py` (Path B — one-off audit script)                            | 0.1,3         |
| market-tick-data-service | `scripts/rebuild_{cefi,tradfi,sports,prediction,defi}_manifest.py` (verify exists per AG)      | 1.5           |
| unified-trading-library  | `python -m unified_trading_library.manifest_consolidator --bucket <X>` (force-merge)           | 1.5           |
| deployment-service       | `scripts/vm/launch-cefi-sharded-backfill.sh`                                                   | 2-CEFI        |
| deployment-service       | `scripts/vm/launch-tradfi-backfill-vm.sh` (singleton-locked)                                   | 2-TRADFI      |
| deployment-service       | `scripts/vm/launch-mtds-prediction-backfill-vm.sh` (singleton-locked)                          | 2-PRED        |
| deployment-service       | `scripts/vm/launch-mtds-gas-fees-backfill-vm.sh`                                               | 2-DEFI        |
| deployment-service       | `scripts/vm/launch-mtds-lst-rates-backfill-vm.sh`                                              | 2-DEFI        |
| deployment-service       | `scripts/vm/launch-mtds-vault-share-price-backfill-vm.sh`                                      | 2-DEFI        |
| deployment-service       | `scripts/vm/launch-manifest-consolidator-vm.sh`                                                | 0.5           |
| deployment-service       | `scripts/vm/create-code-tarballs.sh --all`                                                     | 0.5           |
| deployment-service       | `scripts/vm/vm_zombie_watchdog.py` (`VM_PREFIX_TO_BUCKET` dict)                                | 0.5           |
| deployment-api           | `POST /api/data-status/turbo/clear` (drops all 4 cache layers)                                 | 3             |
| unified-api-contracts    | `unified_api_contracts/canonical/coverage_starts.py`                                           | ref           |
| unified-trading-pm       | `codex/14-playbooks/backfill-completion-playbook.md`                                           | ref           |
| unified-trading-pm       | `codex/02-data/availability-manifest-and-data-status.md` § Phantom audit + Per-VM shard layout | 0,0.1,1,1.5,3 |
| unified-trading-pm       | `codex/05-infrastructure/vm-tarball-deployment.md`                                             | 0.5,1.5,2     |

**Explicitly NOT used** (these run instruments-service or MDPS, not MTDS):
`launch-{api-football,transfermarkt,sfi, footystats,understat,openmeteo}-backfill-vm.sh` (instruments-side, sibling plan
owns), `launch-mdps-backfill-vm.sh` / `launch-mdps-sharded-backfill.sh` (downstream candle generation).

## Success criteria

- All 5 asset groups: ≥99% `captured + empty_confirmed` for `service=market-tick-data-service`, scoped to the
  secondary-cutoff denominator.
- Forward phantom recon dry-run on each MTDS bucket reports 0 phantoms (manifest-claims-no-disk).
- **Inverse phantom audit reports <1% rate per AG** (disk-no-manifest-row). This is the new criterion from Ikenna's
  2026-05-05 callout — proves we didn't waste API spend re-downloading data already on disk.
- Drilldown spot-check: 5 random `(asset_group, day, venue, instrument_type, data_type)` rows per AG resolve to actual
  parquets in GCS, including chain-bundled cases (DERIBIT options, ES options, futures combos).
- DERIBIT v6 manifest rows have `quote_asset` + `margin_type` populated.
- No `manifest-consolidator-*` zombie / outage observed during the backfill window.
- **Cost discipline check**: total API spend during this push (Tardis + Databento + DeFi RPC + odds-API) reported back
  to Ikenna with a per-AG breakdown. Phase 0.1 manifests as a line item — "rows we did NOT re-download because the
  inverse audit caught them" — so we have evidence that the gate worked.

## Out of scope (for _this_ plan — covered by sibling plans / parent epic)

- instruments-service backfill
  ([`instruments_to_100pct_eod_2026_05_04.plan.md`](instruments_to_100pct_eod_2026_05_04.plan.md)).
- MDPS candle generation / odds-horizon-bucket processing (separate plan; many sports gaps live there).
- deployment-ui drilldown bug fixes (parent epic Phase 0 — CSV download, day-shard scroll, schema modal, unified
  MTDS+MDPS view).
- VIX futures full-tick chain — deferred (separate plan + UAC declarative VX contract calendar needed).
- mbp_10 deep book for tradfi — deferred (microstructure strategy not yet requesting it).
- Live forward-poll for any AG — next milestone, not part of this work. Forward-poll launchers
  (`launch-cefi-forward-poll.sh`, `launch-tradfi-forward-poll.sh`, `launch-sfi-forward-poll.sh`,
  `launch-footystats-forward-poll.sh`) are referenced for context only.

## Known gotchas (from playbook + handoff doc — re-stated for self-containment)

- `validate_api_keys_for_venues` wants canonical venue names (`UNISWAPV3-ETHEREUM`), not data-source slugs (`thegraph`).
  Returns empty dict silently on wrong shape.
- CeFi VM `rc=137` (OOM-kill) writes no `EXIT_STATUS` and no `DEPLOYMENT_FAILED` event — atexit handlers don't fire on
  SIGKILL. Diagnose via Cloud Logging kernel OOM query.
- Tardis bulk grouped `FUTURES` request returns empty silently. Adapter must enumerate per-instrument and fan out.
- Concurrent VM boots can race the deadsnakes PPA (~3 of N hang at python3.13 install). Stagger boots ≥30s if launching
  many at once.
- Tarball install pins the VM to local `pyproject.toml` floors via `uv pip install --no-sources -e <local-dir>`. Version
  floors in dependent repos' pyproject.toml are irrelevant for VM-deployed services. After a UTL change, refresh
  tarballs (`--all`); after a Cloud Run code change (consolidator, DeFi collection, deployment-api), rebuild the Docker
  image instead.
- GCS sentinel-lock needs proactive stale cleanup. `if_generation_match=0` deadlocks against any preexisting blob; if
  you're copying the consolidator pattern, ensure the freshness check `blob.delete()`s before falling through to
  acquire.

## Notes (Phase 0 + 0.1 baseline — TBD)

Capture per-AG baseline + decision here so the team can see what each AG's path through the DAG was.

### Per-AG state table (fill in as Phase 0 + 0.1 runs)

| AG         | Phase 0: forward phantoms | Phase 0: missing rows | Phase 0.1: inverse-phantom rate | Decision (rebuild-first vs backfill-first) | Dominant drift axis |
| ---------- | ------------------------- | --------------------- | ------------------------------- | ------------------------------------------ | ------------------- |
| CEFI       | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| TRADFI     | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| SPORTS     | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| PREDICTION | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| DEFI       | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |

### Phase 0 raw logs

```
# CEFI MTDS — /tmp/mtds-recon-cefi.log    (TBD — fill in after Phase 0 runs)
# TRADFI MTDS — /tmp/mtds-recon-tradfi.log (TBD)
# SPORTS MTDS — /tmp/mtds-recon-sports.log (TBD)
# PREDICTION MTDS — /tmp/mtds-recon-prediction.log (TBD)
# DEFI MTDS — /tmp/mtds-recon-defi.log    (TBD)
```

### Phase 0.1 inverse-audit CSVs

```
# /tmp/mtds-inverse-cefi.csv       (TBD)
# /tmp/mtds-inverse-tradfi.csv     (TBD)
# /tmp/mtds-inverse-sports.csv     (TBD)
# /tmp/mtds-inverse-prediction.csv (TBD)
# /tmp/mtds-inverse-defi.csv       (TBD)
```

### Phase 1.5 rebuild deltas (only if any AG was flagged)

| AG  | Pre-rebuild missing | Post-rebuild missing | Delta (rows recovered without download) | API spend avoided ($) |
| --- | ------------------- | -------------------- | --------------------------------------- | --------------------- |
| TBD | TBD                 | TBD                  | TBD                                     | TBD                   |

## Risks / blockers

- **Tardis quota** — heavy backfills can exhaust Tardis daily quota. Adapter pacing helps; avoid `--force` on large
  windows.
- **Databento contract-exceeded** — TRADFI singleton lock exists for this reason. Don't bypass.
- **Polymarket per-IP rate limit** — singleton lock + cursor-sharding (sibling plan Day 2) are the mitigations.
- **systemd-oomd on local machine** — if any phase ends up running locally instead of on VMs, watch RAM (cap ~80 GB).
  See sibling plan execution log for the 2026-05-04 incident.
- **Manifest consolidator outage** — per-VM shards stay un-merged; reader's 120s freshness fallback truncates to per-VM
  view. Daemon has a singleton lock; if it dies, relaunch ASAP.
- **Phantom drift axes not yet covered by `reconcile_phantom_manifest_rows_all.py`** — five known axes are encoded
  (hive-vocab, casing, empty instrument_type, path-prefix, chain-bundle equivalence). New axis = false-positive phantom
  flips. If post-flip phantom count is anomalous (>5% of captured), suspect a new drift axis and stop before re-running.
- **Inverse-audit (Phase 0.1) script has its own bug surface.** A false-positive inverse phantom sends an AG down a
  rebuild path that never lands; a false-negative leaves us re-downloading. Sanity-check via the [HUMAN] P1 step in
  Phase 0.1 (manually `gsutil ls` 5 random `inverse_phantom` rows) before trusting the numbers at scale.
- **Rebuild output silently dropped without `per_vm_shards=True`** — 2026-05-02 DeFi rebuild lost 80k rows compacted to
  12k canonical because of CAS contention with the consolidator. Always set `MANIFEST_PER_VM_SHARDS=true` on rebuild
  runs and force-merge after.
- **Cost-of-rebuild vs cost-of-redownload** — rebuilds list every parquet in the bucket; for buckets at scale that's
  millions of objects. Same-region VM keeps it tractable (~222 prefixes/sec), cross-region from laptop is 18× slower.
  Don't run rebuilds from a laptop on a non-trivial AG.
