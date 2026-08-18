---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-08), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-9dc091, slot 3). Both cefi buckets
  healthy: market-data consolidator ran fresh (produced, 10.89M rows in → 10.19M out, not locked); instruments-store
  consolidator healthy no-op (empty, not locked). Venue census unchanged from 08-07: zero orphaned canonical
  declarations (all 25 UAC venues have manifest presence); M−C drift is the same four static/dormant populations
  (bare-OKX 5,225, byte-identical 4th day running; KALSHI_PERP 2; OKX-OPTIONS 2; BYBIT-FUTURES 5, flat since 08-06 — no
  new alias-shard rows in the ~32h since, unlike the 4→5 growth seen 08-05→08-06). instrument_type=index
  (DERIBIT/volatility_index, 3,910 rows) persists unchanged; instrument_type=spot (lowercase) absent a 3rd consecutive
  day; chain axis still all-blank (heal holds, 5th day); 5 stray ohlcv_* data_types unchanged (10 rows). Batch-layer
  GCS-vs-manifest spot-check (day 2026-08-06) is clean — M−G=∅, G−M=∅ across
  batch_hyperliquid/batch_kalshi_perp/batch_tardis. **Headline finding, root-caused this run**: the honest-coverage
  daily rollup has now MISSED TWO consecutive cycles (08-06 AND 08-07, not just one as reported 08-07) — traced via
  gcloud logging read on the GCE VM's own serial console to a reproducible OOM-kill of the measurement Python process on
  BOTH days (anon-rss ~15.35-15.41GB on an e2-standard-4/16GiB box), nearly double the 8.20GB peak measured just 5-6
  days ago when the box was last empirically right-sized (2026-08-01). The launcher Cloud Run Job reports "success"
  every day regardless — it only launches the VM and exits, never checking the VM's own terminal state, so this failure
  was invisible to the job's own health signal. Filed as a P2 cross-asset-group issue doc (not cefi-specific — affects
  all 5 asset groups) with the next diagnostic step (the script's own `--oom-monitor` flag) rather than a blind
  machine-type bump. Fully read-only; no code changes shipped this run (the OOM is a cross-asset-group infra issue
  outside a single narrowly-scoped fix).
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    census,
    cefi,
    honest-coverage,
    honest-coverage-vm-oom,
    bare-okx-verification,
    bybit-futures-alias-shard,
    deribit-volatility-index,
    chain-axis-heal,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_07,
    defi_cefi_venue_chain_axis_contamination_2026_07_28,
    cefi_bare_okx_venue_removal_2026_08_04,
    honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08,
  ]
created: 2026-08-08
resulting_plan: /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md
lib_version:
  "market-tick-data-service@HEAD (slot 3), unified-api-contracts@HEAD (audited only; no changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) + honest-coverage
  verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) — daily scheduled
  spot-check, not a full campaign. The honest-coverage VM-OOM diagnosis used only gcloud logging read / scheduler /
  run-jobs describe (read-only GCP API calls, no VM launched by this run)."
date: 2026-08-08
auditor: "cefi_reconciliation_auditor (scheduled role, slot 3, dispatch agt-9dc091)"
parent_epic: security_and_cross_cutting_master
severity: P2
skill: data-pipeline-reconciliation
run_date: 2026-08-08
generated_at: 2026-08-08T00:36:54+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-08), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes. Daily
scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f distinct-value census

- honest-coverage formula/freshness verification, mirroring the 2026-08-05/06/07 runs. This run additionally root-caused
  the honest-coverage staleness (carried as an unexplained todo from 08-07) via read-only GCP log inspection — see §4.

## 0. Phase-0 reachability + freshness

| bucket                                              | reachable | consolidator lock | last run (UTC)          | verdict                                                               |
| --------------------------------------------------- | --------- | ----------------- | ----------------------- | --------------------------------------------------------------------- |
| `market-data-tick-cefi-prd-central-element-323112`  | yes       | not locked        | 2026-08-08T00:08:18.80Z | produced (10,885,994 rows in → 10,186,659 out; 699,335 dedup-dropped) |
| `instruments-store-cefi-prd-central-element-323112` | yes       | not locked        | 2026-08-08T00:00:47.65Z | empty (0 rows, no-op — consistent with 08-05/06/07)                   |

Consolidator ran fresh (market-data: ~28 min before this audit; instruments-store: ~36 min before). Neither bucket holds
a `consolidator.lock` object (explicit probe). `_index/consolidator_stall_state.json`: `streak=0, baseline_shards=11`
for market-data — healthy.

- `_index/phantom_audit_latest.json` (market-data): `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **12 days
  stale** (was 11 on 08-07). `_index/reprobe_audit_latest.json`: `generated_at=2026-07-14T06:19:32Z` — 25 days stale,
  all-zero counts, unchanged. `instruments-store-cefi` still has **no** `phantom_audit_latest.json` (H5 — standing
  declared coverage gap, unchanged).

**AWS cross-check (new this run, Phase 0(a)/(b)):** the AWS-side mirror buckets
(`market-data-tick-cefi-prd-427895769566`, `instruments-store-cefi-prd-427895769566`) both resolve and are reachable,
but both are **completely empty (0 objects)**. Not treated as a finding — per
`/codex/05-infrastructure/cloud-agnostic-script-pattern.md` §Tier-4, dual-cloud-active write is opt-in
per-workload-promotion (checklist items "Tier-3 services... CLOUD_PROVIDER=aws smoke-pass" and "Dual-write enabled on
writers" are both still unchecked there), not yet the live default for cefi raw-tick capture. Noted as a declared
observation, not re-litigated further this run.

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`, 25 venues)

Read via pyarrow native `GcsFileSystem` + row-group predicate pushdown / column projection directly against the
consolidated `_index/availability_index.parquet` (10,186,659 rows, slim columns) — same reader shape as the
deployment-api census endpoint.

- **C − M (orphaned declarations)**: **empty** — all 25 UAC-declared cefi venues have manifest presence (4th consecutive
  day).
- **M − C (drift)** — same 4 entries as 08-07, **all static or flat, zero new drift**:
  - `OKX` (bare) — 5,225 rows, all `attempted_failed` `batch_tardis`, `max_attempted_at = 2026-08-04T17:32:43.514974Z` —
    **byte-identical to 08-05/06/07**. Confirmed dormant, **4th consecutive day**. The 08-04 bare-OKX
    orchestrator-literal fix continues to hold.
  - `BYBIT-FUTURES` — **5 rows, unchanged from 08-07** (was 4→5 growth 08-05→08-06; `max_attempted_at` is still
    `2026-08-06T16:36:43.983380Z`, now ~32h old at this audit). **No new alias-shard rows in the ~32h since the 08-07
    report** — the live-lane alias-shard growth observed 08-05→08-06 did not repeat 08-06→08-07/08. Neither "confirmed
    fixed" nor "still actively growing" on this single data point; the existing carried todo (§6, live shard launch
    config review) stands unchanged.
  - `KALSHI_PERP` (underscore variant of canonical `KALSHI-PERP`) — 2 `attempted_failed` rows,
    `max_attempted_at = 2026-07-28T01:16:06Z`. Unchanged.
  - `OKX-OPTIONS` — 2 `attempted_failed` rows, `max_attempted_at = 2026-07-26T14:14:45Z`. Unchanged.

## 2. Census — instrument_type + data_type axes

- **Case-only variants (`perpetual`:16,848 / `future`:1,191 / `spot_pair`:12)** are the ruled C2a `migration_pending`
  casing axis — suppressed, not findings (§5.1). Counts continue climbing (`perpetual` 15,517→16,848, `future`
  1,119→1,191), consistent with the ongoing C2a-adjacent relabeling noted 08-06/08-07 — no new behavior.
- **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index/batch_deribit/captured) — unchanged 3rd consecutive
  day.** The 08-06 P2 registry under-declaration persists (carried todo, §6).
- **`instrument_type=spot` (lowercase) — absent a 3rd consecutive day.** Still not independently root-caused.
- **5 stray `ohlcv_{5m,1h,1d,15s,15m}` data_type values, 2 rows each (10 total) — unchanged.**
  `futures_chain`/`options_chain` instrument_types correctly suppressed as accepted exceptions.
- **`chain` axis: 0 non-blank values — the 2026-07-28 chain-axis heal holds a 5th day.** Not re-litigated (see 08-07 §2
  for the full explanation); reported once for the record per the report contract.
- **§6c cefi chain-tail v6 spot-check**: per `canonical-cutover-register.md` §6c, 0 v5-or-v6 chain objects have ever
  been captured (`options_chain`/`futures_chain` capture_status is 100% `attempted_failed`/`empty_confirmed`, 0
  `captured` — matches this run's own §1 `OKX` bare-venue breakdown, which is itself entirely
  `options_chain`/`trades`/`book_snapshot_5`/`derivative_ticker`/`liquidations` under `attempted_failed`). Consistent
  with the register's "migration is a confirmed no-op" finding — no new chain objects to classify.
- `quote_asset`/`margin_type` (USDT 499,658 / USD 5,646 / USDC 709; linear 500,549 / inverse 5,464) grew materially
  since 08-07 (USDT +99,572, linear +100,063) — consistent with ongoing MDPS candle-row capture (`timeframe`-bearing
  rows), not investigated further as no vocabulary drift accompanies the growth (same value set, just more rows).

## 3. GCS-vs-manifest vocabulary spot-check (M △ G) — batch layer clean

Sampled the most recent batch-captured day (**2026-08-06**, max captured batch day in the manifest; 08-07 rows still
landing, expected ≤1-day consolidation lag), per pipeline_mode (delimiter descent, native `storage.Client`, iterator
advanced before reading `.prefixes` per the known empty-prefixes gotcha):

| pipeline_mode       | manifest venues (captured)                      | GCS venue=\* prefixes                           | M − G | G − M |
| ------------------- | ----------------------------------------------- | ----------------------------------------------- | ----- | ----- |
| `batch_hyperliquid` | HYPERLIQUID                                     | HYPERLIQUID                                     | ∅     | ∅     |
| `batch_kalshi_perp` | KALSHI-PERP                                     | KALSHI-PERP                                     | ∅     | ∅     |
| `batch_tardis`      | BYBIT, COINBASE-FUTURES, COINBASE-SPOT, DERIBIT | BYBIT, COINBASE-FUTURES, COINBASE-SPOT, DERIBIT | ∅     | ∅     |

**No `shard_atom_vocab_desync` at the batch layer.** Only 3 pipeline_mode day-dirs exist on GCS for 2026-08-06 (no live
dirs) — consistent with 08-07's finding that the live lane persists via the warm-sink event-log path, not
`raw_tick_data`, so its absence there is architecture, not loss (see 08-07 §4 for the full explanation; not re-derived
this run).

## 4. Honest-coverage — MISSED TWO consecutive cycles, root-caused this run

**08-07 reported one missed cycle (08-06) with cause unknown, filed as a P3 "confirm job health" todo. This run found a
SECOND consecutive miss (08-07 also missing) and root-caused both via read-only `gcloud logging read` /
`gcloud scheduler` / `gcloud run jobs` / `gcloud compute instances` inspection — no VM launched by this audit.**

- **Bucket state**: `gs://central-element-323112-honest-coverage/` still has no `2026-08-06/` or `2026-08-07/` dir;
  latest is `2026-08-05T22:19:12Z` — **~50h stale** at this audit (2026-08-08T00:36Z), for **all 5 asset groups**, not
  cefi-specific.
- **The scheduler and its launcher both report "success"**: `honest-coverage-daily` (cron `30 0 * * *`, ENABLED) fired
  on time both days; `honest-coverage-daily-launcher` Cloud Run Job executions both show `Completed / True` (08-06:
  41.1s, 08-07: 53.1s). **This job's own success signal is blind to the real failure** — its log shows it only calls
  `gcloud compute instances create` for a `measure-honest-coverage-<date>` VM and exits; it never checks whether that
  VM's payload actually completes.
- **The VM itself was OOM-killed both days**, confirmed via GCE serial-console kernel logs
  (`labels."compute.googleapis.com/resource_name"=<vm-name>`):
  - 08-06 (`measure-honest-coverage-20260806-003030`):
    `Out of memory: Killed process 7176 (python) ... anon-rss:15352788kB` at 00:35:35Z (process started ~00:33:2x, VM
    launched 00:30:44Z).
  - 08-07 (`measure-honest-coverage-20260807-003039`):
    `Out of memory: Killed process 4841 (python) ... anon-rss:15411360kB` at 00:35:29Z (process started 00:33:33Z, VM
    launched 00:30:54Z).
  - Both running `measure_honest_coverage.py --asset-group all` on `e2-standard-4` (4 vCPU / 16 GiB), both dying ~2
    minutes after the Python process starts, both within ~60MB of each other on anon-rss — reproducible, not a one-off
    blip.
- **This is a capacity regression, not a fresh bug**: per
  `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh:48-66` (the launcher's own documented right-sizing
  history), a 2026-08-01 fix (`instruments-service@12825e81`) made the script stream one asset_group's manifest at a
  time (bounding peak RSS to the single largest AG's read) and was empirically re-verified the SAME day at **8.20 GB RSS
  peak** on this exact `e2-standard-4` box — safely under the 16 GiB ceiling, which is why it was downsized back to this
  machine type then. Five to six days later, the measured peak is **~15.35-15.41 GB — nearly double**, consuming almost
  the entire ceiling. **Not established this run** whether that is organic manifest growth outpacing the 08-01
  measurement, a memory-release regression in the per-AG loop (`del`+`gc.collect()` not fully returning memory between
  AGs), or a data-shape burst in one asset_group (most likely `defi`, the AG with the largest known manifest elsewhere
  in this codebase's own documentation, though not confirmed — no per-AG progress marker reached the serial console
  before the kill).
- **Illustrative-only re-derivation** (NOT a replacement for the official job, which may apply additional MVP-gating
  this ad hoc check doesn't replicate): re-computing `reachable_coverage` from TODAY's live cefi manifest via the same
  named formula (`captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` excluded) gives
  4,409,615 / 8,501,549 = **51.87%**, vs the stale published **50.15%** — a ~1.7-point undercount just for cefi,
  illustrating the magnitude of drift the 2 missed cycles have introduced. Not cross-checked against the other 4 asset
  groups (out of this role's cefi-only scope).
- **Filed**: `/plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (P2, cross-cutting — not
  cefi-specific, so not fixed inline this run; the sanctioned next step is the script's own `--oom-monitor`
  right-sizing-verification flag, not a blind machine-type bump, per this codebase's own established practice of
  empirically re-verifying sizing before changing it).
- **Layer-1 detail unchanged where re-checked**: re-read the stale 2026-08-05 rollup's `layer_1.by_asset_group.cefi` —
  72 `stray_tuples` (incl. the DERIBIT/index/volatility_index entry, still corroborating §2's 3rd finding), 5
  `missing_tuples` (BITGET-FUTURES/future × 3 data_types, OKX-FUTURES/perpetual × 2), `completeness_pct=93.15` — all
  byte-identical to 08-07, confirming this is genuinely the same unchanged snapshot, not new data coincidentally
  matching.

## 5. What this run does NOT cover (declared, per the role's Tier-1 scope)

- **No machine-oracle path-structure sweep** (`canonical_path_violations()` over real GCS objects) — never this role;
  the daily Hygiene-vs-GCS digest covers path structure.
- **No id-form / schema Tier-1 sampled check or Tier-2 VM validation** — out of scope entirely.
- **No orphan-object sweep / delete suggestions** — this role never proposes deletes, unconditionally.
- **No full multi-day GCS-side census** — §3 is a one-day, per-mode spot-check; the last full G1 census remains
  2026-07-30 (H8).
- **No fix shipped for the honest-coverage OOM** — cross-asset-group, needs the `--oom-monitor` diagnostic first; filed
  as an issue doc instead (§4).
- **Live lane warm-sink estate** — not re-probed this run (unchanged since 08-07's explanation).
- **The other 4 asset groups' honest-coverage staleness** — this role is cefi-only; the OOM affects all 5, but only
  cefi's manifest was independently re-derived (§4's illustrative check).

## 6. Todos

- [ ] [OPERATOR] P2. **NEW — honest-coverage-daily VM OOM'd 2 consecutive days (08-06, 08-07), rollup ~50h stale for ALL
      5 asset groups.** Root-caused this run (see
      `/plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`): peak RSS grew from a measured
      8.20GB (2026-08-01) to ~15.35-15.41GB (08-06/07) against a 16GiB e2-standard-4 ceiling. Decide: immediate unblock
      via `--machine-type e2-highmem-4` re-launch, and/or run `--oom-monitor` for a fresh right-sizing diagnostic to
      find which AG's read grew and why. Repo: deployment-service / instruments-service.
- [ ] [INFRA] P3. **NEW — harden `honest-coverage-daily-launcher` to verify VM terminal state**, not just that the
      `instances.create` API call succeeded — the current design is structurally blind to an OOM/crash inside the VM.
      Repo: deployment-service.
- [ ] [DATA] P2. **Registry under-declaration (carried, unchanged 3rd day)**: `DERIBIT` has captured 3,910 legitimate
      `volatility_index` rows under `instrument_type=index` since 2021-03-24; "index" is declared nowhere in cefi's
      registries. Decide add-vs-document. Repo: unified-api-contracts.
- [ ] [DATA] P2. **Live lane writes non-canonical venue=BYBIT-FUTURES manifest rows (carried; flat this cycle, not
      confirmed fixed)**: 5 `empty_confirmed` `live_bybit` rows, unchanged since 08-06's growth to 5 (no new rows in the
      ~32h to this audit). Root cause (per 08-07): `bybit_ws.py` dual-registers BYBIT-FUTURES (pre-canon alias) + BYBIT
      (canonical); live shard launcher enumerates the alias. Confirm with the live-deployment owner before correcting
      the launch config. Repo: market-tick-data-service / deployment-service.
- [ ] [INFRA] P3. **Re-run (or schedule) `phantom_audit` for cefi** — now 12 days stale. Repo: instruments-service.
- [ ] [DATA] P3. **Layer-1 missing tuples (carried)**: BITGET-FUTURES/future × 3 data_types + OKX-FUTURES/perpetual × 2
      — declared-expected, never captured; confirm in-scope or deregister. Repo: unified-api-contracts /
      market-tick-data-service.
- [ ] [INFRA] P3. **Manifest hygiene (carried)**: purge the 5,225 stale bare-`OKX` `attempted_failed` rows — dormant a
      4th day, count and timestamp unchanged. Repo: market-tick-data-service / instruments-service.
- [ ] [DIAG] P4. Confirm `instrument_type=spot` (lowercase) relabel — absent a 3rd consecutive day, no relabel event
      independently confirmed. Repo: market-tick-data-service / unified-api-contracts.
- [ ] [DIAG] P4. **batch_aster / batch_extended lanes** — confirm still last-captured 2026-08-02 or check for
      resumption; completed-drain vs stalled-fleet question carried from 08-07. Repo: market-tick-data-service.
