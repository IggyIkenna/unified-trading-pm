---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-09), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-91ada6, slot 4). Both cefi buckets
  healthy: market-data consolidator ran fresh (produced, 11.93M rows in → 10.50M out, not locked); instruments-store
  consolidator healthy no-op (empty, not locked). Venue census unchanged from 08-08: zero orphaned canonical
  declarations (5th consecutive day all 25 UAC venues have manifest presence); M−C drift is the same four static/dormant
  populations, ALL byte-identical counts (bare-OKX 5,225, 5th day running; KALSHI_PERP 2; OKX-OPTIONS 2; BYBIT-FUTURES
  5, now flat 4 consecutive days). instrument_type=index (DERIBIT/volatility_index, 3,910 rows) persists unchanged, 4th
  consecutive day; instrument_type=spot (lowercase) absent a 4th consecutive day; chain axis still all-blank (heal
  holds, 6th day); 5 stray ohlcv_* data_types unchanged (10 rows). Investigated DERIBIT `COMBO` (29,785 rows, grown from
  13,065 on 07-24) after noticing a possible writer/reader partition mismatch in code (`symbol_rules.py` vs `reader.py`)
  — verified against REAL GCS objects (not just code) and found captured COMBO shards are flat-per-instrument with full
  canonical per-leg ids, matching the reader's expectations; no defect, ruled out after direct verification. Batch-layer
  GCS-vs-manifest spot-check (day 2026-08-08) is clean — M−G=∅, G−M=∅ across all 3 present batch pipeline_modes.
  Resolved a carried diagnostic question: `batch_aster`/`batch_extended` lanes have advanced (max captured date
  08-02→08-03 and 08-02→08-04 respectively) — confirmed still actively capturing, not stalled. **Headline finding**: the
  honest-coverage daily rollup, filed as a P2 issue on 08-08 for 2 missed cycles, has now MISSED A 3RD/4TH cycle with an
  IDENTICAL OOM signature (today's VM `measure-honest-coverage-20260809-003041` OOM'd at the same ~15.4GB anon-rss, ~2
  min after launch) — RSS is now FLAT across all 3 measured days (within ~59,000kB of each other), a new signal against
  the "organic growth" hypothesis. No remediation has been applied in the intervening day. Escalated the existing issue
  doc's priority P2→P1 and its operator-decision todo P2→P1 given the rollup is now ~86h stale across all 5 asset groups
  with zero remediation attempts recorded. Illustrative re-derivation shows the drift has grown to ~3.87 points (54.02%
  live vs 50.15% stale-published) for cefi alone. Fully read-only; no code changes shipped this run (the OOM remains a
  cross-asset-group infra issue outside a single narrowly-scoped fix; the COMBO investigation resolved as a non-finding
  after verification).
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
    deribit-combo-verification,
    chain-axis-heal,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_08,
    defi_cefi_venue_chain_axis_contamination_2026_07_28,
    cefi_bare_okx_venue_removal_2026_08_04,
    honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08,
  ]
created: 2026-08-09
resulting_plan: /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md
lib_version:
  "market-tick-data-service@HEAD (slot 4), unified-api-contracts@HEAD (audited only; no changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) + honest-coverage
  verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) — daily scheduled
  spot-check, not a full campaign. The honest-coverage re-check + COMBO investigation used only gcloud logging read /
  scheduler / run-jobs describe / GCS list+read calls (read-only, no VM launched by this run)."
date: 2026-08-09
auditor: "cefi_reconciliation_auditor (scheduled role, slot 4, dispatch agt-91ada6)"
parent_epic: security_and_cross_cutting_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-08-09
generated_at: 2026-08-09T02:35:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-09), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes (a
plan/issue doc UPDATE to the existing honest-coverage OOM issue is a report-adjacent doc edit, not a data/code
mutation). Daily scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f
distinct-value census + honest-coverage formula/freshness verification, mirroring the 2026-08-05..08 runs. This run
additionally re-verified the honest-coverage OOM (still live, escalated) and investigated a code-level DERIBIT `COMBO`
concern down to real GCS objects (resolved as a non-finding) — see §2 and §4.

## 0. Phase-0 reachability + freshness

| bucket                                              | reachable | consolidator lock | last run (UTC)          | verdict                                                                 |
| --------------------------------------------------- | --------- | ----------------- | ----------------------- | ----------------------------------------------------------------------- |
| `market-data-tick-cefi-prd-central-element-323112`  | yes       | not locked        | 2026-08-09T02:08:33.91Z | produced (11,934,508 rows in → 10,504,930 out; 1,429,578 dedup-dropped) |
| `instruments-store-cefi-prd-central-element-323112` | yes       | not locked        | 2026-08-09T02:00:44.88Z | empty (0 rows, no-op — consistent with 08-05..08)                       |

Consolidator ran fresh (market-data: ~27 min before this audit; instruments-store: ~35 min before). Neither bucket holds
a `consolidator.lock` object (explicit probe). `_index/consolidator_stall_state.json`: market-data
`streak=0, baseline_shards=8` (was `baseline_shards=11` on 08-08 — a drop worth noting; `streak=0` means the
consolidator is NOT stalled either way, so this is a shard-grouping observation, not a health finding);
instruments-store `streak=0, baseline_shards=2`.

- `_index/phantom_audit_latest.json` (market-data): `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **13 days
  stale** (was 12 on 08-08). `_index/reprobe_audit_latest.json`: `generated_at=2026-07-14T06:19:32Z` — 26 days stale,
  all-zero counts, unchanged. `instruments-store-cefi` still has **no** `phantom_audit_latest.json` (H5 — standing
  declared coverage gap, unchanged).

**AWS cross-check (Phase 0(a)/(b)):** the AWS-side mirror buckets (`market-data-tick-cefi-prd-427895769566`,
`instruments-store-cefi-prd-427895769566`) both resolve and are reachable, but both are **completely empty (0 objects)**
— unchanged from 08-08. Not treated as a finding, same rationale as prior runs (dual-cloud-active write is opt-in
per-workload-promotion, not yet the live default for cefi raw-tick capture).

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`, 25 venues)

Read via pyarrow native `GcsFileSystem` + row-group predicate pushdown / column projection directly against the
consolidated `_index/availability_index.parquet` (10,504,930 rows, slim columns) — same reader shape as the
deployment-api census endpoint (`get_axis_value_census`), invoked in-process (same single-walk reader, no HTTP hop).

- **C − M (orphaned declarations)**: **empty** — all 25 UAC-declared cefi venues have manifest presence (5th consecutive
  day).
- **M − C (drift)** — same 4 entries as 08-08, **all byte-identical counts, zero new drift**:
  - `OKX` (bare) — 5,225 rows, `max_attempted_at = 2026-08-04T17:32:43.514974Z` — **byte-identical to 08-05..08**.
    Confirmed dormant, **5th consecutive day**. The 08-04 bare-OKX orchestrator-literal fix continues to hold.
  - `BYBIT-FUTURES` — **5 rows, unchanged from 08-07/08-08** — now **flat 4 consecutive days** (was 4→5 growth
    08-05→08-06, then flat since). Neither "confirmed fixed" nor "still actively growing" was concluded on a single data
    point before; 4 consecutive flat days is a stronger (though still not conclusive) signal toward "fixed" — the
    carried todo (§6, live shard launch config review) is downgraded in urgency below but not closed, since a config
    review to CONFIRM the root cause was never independently done.
  - `KALSHI_PERP` (underscore variant of canonical `KALSHI-PERP`) — 2 `attempted_failed` rows, unchanged.
  - `OKX-OPTIONS` — 2 `attempted_failed` rows, unchanged.

## 2. Census — instrument_type + data_type axes

- **Case-only variants (`perpetual`:37,391 / `future`:1,191 / `spot_pair`:12)** are the ruled C2a `migration_pending`
  casing axis — suppressed, not findings (§5.1). **`perpetual` jumped 16,848→37,391 (+20,543, ~2.2×)** — a much larger
  single-day jump than the ~1,300/day trend seen 08-07→08-08; `future` and `spot_pair` are BYTE-IDENTICAL to 08-08
  (1,191 and 12). Reported as an INFO observation (not investigated further — C2a is a suppressed axis by rule, and the
  growth is on the ACCEPTED-casing side of the migration, not a new value), but flagged because the magnitude is out of
  trend and worth a glance on tomorrow's run.
- **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index/batch_deribit/captured) — unchanged, 4th consecutive
  day.** The 08-06 P2 registry under-declaration persists (carried todo, §6).
- **`instrument_type=spot` (lowercase) — absent, 4th consecutive day.** Still not independently root-caused.
- **5 stray `ohlcv_{5m,1h,1d,15s,15m}` data_type values, 2 rows each (10 total) — unchanged.**
  `futures_chain`/`options_chain` instrument_types correctly suppressed as accepted exceptions.
- **`chain` axis: 0 non-blank values — the 2026-07-28 chain-axis heal holds a 6th day.** Not re-litigated (see 08-07 §2
  for the full explanation); reported once for the record per the report contract.
- `quote_asset`/`margin_type` (USDT 593,124 / USD 6,356 / USDC 734; linear 594,202 / inverse 6,012) grew materially
  since 08-08 (USDT +93,466, linear +94,653) — consistent with ongoing MDPS candle-row capture, not investigated further
  as no vocabulary drift accompanies the growth (same value set, more rows).

### 2a. DERIBIT `COMBO` — investigated, verified NOT a defect (new this run)

Noticed `COMBO` (29,785 total census rows — 22,113 `captured`) in the instrument_type census, not mentioned in the
08-06/07/08 report prose. Traced it: `COMBO` is a KNOWN, taxonomy-accepted exception (AE-2, "bare-underlying combo
carve-out"; applied to cefi's DERIBIT rows since at least the 2026-07-24 cefi report, which measured 662→13,065 rows
growth and explicitly suppressed it) — growth to 29,785 today continues that same organic trend, not new drift.

While confirming AE-2's applicability, a code-only read raised a possible concern: `market-tick-data-service`'s
`symbol_rules.py:266` (`_UNDERLYING_PARTITIONED_TYPES`) includes `"combo"` alongside `options_chain`/`futures_chain`
(implying WRITE as an `underlying=.../ticks.parquet` bundle), while `reader.py:74`'s own `_UNDERLYING_PARTITIONED_TYPES`
does **NOT** include `combo` (implying READ as a flat per-instrument shard) — a naive read of just these two constants
suggests a writer/reader disagreement that could make captured COMBO shards unreadable.

**Verified against real GCS objects before concluding anything** (per this workspace's own "grep-then-READ, not
grep-then-conclude" rule): probed a captured COMBO shard directly —
`raw_tick_data/by_date/day=2026-06-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=combo/data_type=derivative_ticker/`
contains 312 objects, each named `DERIBIT:COMBO:<full-leg-spec>.parquet` (e.g.
`DERIBIT:COMBO:BTC-CS-31JUL26-83000_90000.parquet`) — **flat-per-instrument with a full canonical id, NOT bundled under
`underlying=`**. This matches the reader's actual expectation (`reader.py`'s omission of `combo` from the
underlying-partitioned set is CORRECT for what's really on disk) and is consistent with `manifest_finalize.py`'s
`_write_bundle_shard_row` gate (`itype_key != "combo"`, found via the same grep) explicitly excluding `combo` from the
bundle-write path despite `symbol_rules.py`'s constant nominally including it — `symbol_rules.py`'s inclusion appears
unused for cefi's actual combo write decision (not independently confirmed which OTHER call site consumes it, or whether
it's live for tradfi's combo, which per AE-2's own text still uses the bare-`underlying=` tail with an unsettled
leg-aware id).

**Verdict: no defect.** DERIBIT's COMBO capture is healthy, growing, and correctly readable. Filed as a verified
non-finding rather than an issue doc — no todo needed, but noting the investigation so it isn't silently re-walked
tomorrow.

## 3. GCS-vs-manifest vocabulary spot-check (M △ G) — batch layer clean

Sampled the most recent batch-captured day (**2026-08-08**, max captured batch day in the manifest; 08-09 rows still
landing, expected ≤1-day consolidation lag), per pipeline_mode (delimiter descent, native `storage.Client`, iterator
advanced before reading `.prefixes` per the known empty-prefixes gotcha):

| pipeline_mode           | manifest venues (captured) | GCS venue=\* prefixes | M − G | G − M |
| ----------------------- | -------------------------- | --------------------- | ----- | ----- |
| `batch_hyperliquid`     | HYPERLIQUID                | HYPERLIQUID           | ∅     | ∅     |
| `batch_kalshi_perp`     | KALSHI-PERP                | KALSHI-PERP           | ∅     | ∅     |
| `batch_polymarket_perp` | POLYMARKET-PERP            | POLYMARKET-PERP       | ∅     | ∅     |

**No `shard_atom_vocab_desync` at the batch layer.** Only 3 pipeline_mode day-dirs exist on GCS for 2026-08-08 (no
`batch_tardis`/`batch_aster`/`batch_deribit`/`batch_lighter_api` — consistent with Tardis's own N=1-per-day capture
pattern documented in reference-cefi.md). 5 `live_*` modes (aster/binance/hyperliquid/kraken/okx) are present in the
manifest for this day but have zero `raw_tick_data/` GCS presence — **expected architecture, not loss**: the live lane
persists via the warm-sink event-log path, not `raw_tick_data/` (see 08-07 §4 for the full explanation; not re-derived
this run).

### 3a. Resolved carried diagnostic — `batch_aster` / `batch_extended` lane status

Carried from 08-07/08-08 as an open question ("still last-captured 2026-08-02 or check for resumption"). Checked
directly this run: `batch_aster` max captured date is now **2026-08-03** (row count 256,296), `batch_extended` max
captured date is now **2026-08-04** (row count 25,745) — **both have advanced since the 08-02 baseline**, confirming
these lanes are still actively capturing (with several days of normal consolidation/backfill lag), not stalled. Closing
this carried question — no fleet resumption action needed.

## 4. Honest-coverage — STILL MISSING, now a 3rd/4th consecutive cycle, ESCALATED

**08-08 filed a P2 issue for 2 missed cycles (08-06, 08-07), root-caused as a GCE VM OOM during
`measure_honest_coverage.py --asset-group all`. Re-checked live this run: the condition is unchanged and has gotten
worse — no remediation has landed.**

- **Bucket state**: `gs://central-element-323112-honest-coverage/` still has no `2026-08-06/`, `2026-08-07/`, or
  `2026-08-08/` dir; latest is still `2026-08-05T22:19:11Z` — **~86h stale** at this audit (2026-08-09T02:35Z), for all
  5 asset groups, up from ~50h on 08-08.
- **The scheduler and launcher fired again today and again reported blind success**: `honest-coverage-daily-launcher`
  execution `honest-coverage-daily-launcher-54j5c`, `2026-08-09T00:30:07Z → 00:30:55Z`, `Completed / True`, "Execution
  completed successfully in 48.52s" — the same structurally-blind "VM launched ⇒ success" pattern.
- **Today's VM OOM-killed with the IDENTICAL signature**: `measure-honest-coverage-20260809-003041`, confirmed via GCE
  serial-console kernel logs: `Out of memory: Killed process 4857 (python) total-vm:22012596kB, anon-rss:15396828kB` at
  00:35:41Z (VM created 00:30:41Z, python process killed ~5 min after launch — same shape as 08-06/08-07).
- **New signal this run: anon-rss is now FLAT across all 3 measured days, not climbing** — 08-06: 15,352,788kB; 08-07:
  15,411,360kB; 08-09: 15,396,828kB — all within **~59,000kB (~0.06GB) of each other**. This is evidence AGAINST the
  "organic manifest growth" hypothesis (which would show a continuing upward trend across days) and favours either a
  deterministic ceiling (the peak AG's read has stopped growing) or a leak that maxes out independent of daily data
  volume. Still not established which — the `--oom-monitor` diagnostic run remains the right next step.
- **No remediation applied**: machine type is still inferred `e2-standard-4` (an `e2-highmem-4` 32GiB box would not OOM
  at ~15.4GB) — not independently confirmed via an `instances.insert` audit-log read this run (the log query used didn't
  resolve; not re-attempted given the OOM ceiling itself is strong indirect evidence). The `[OPERATOR]` todo from 08-08
  (decide immediate unblock) is still open, unresolved 1+ day later.
- **Escalated**: updated `/plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` in place
  with today's evidence (new dated section + Progress Log entry), bumped its `priority: P2 → P1` and its `[OPERATOR]`
  todo `P2 → P1`, given the rollup is now 4 consecutive cycles missed (was 2) with zero remediation attempts recorded
  since diagnosis. Not fixed inline this run either — same reasoning as 08-08: cross-asset-group scope, and the
  remediation choice (bump vs. diagnose-first) is an operator decision already correctly gated, not a mechanical fix
  this role should apply unilaterally.
- **Illustrative-only re-derivation** (NOT a replacement for the official job): re-computing `reachable_coverage` from
  TODAY's live cefi manifest via the named formula (`captured / (captured + attempted_failed + expected_unattempted)`,
  `empty_confirmed` excluded) gives 4,672,059 / 8,649,129 = **54.02%**, vs the stale published **50.15%** — the drift
  has grown to **~3.87 points** (was ~1.7 points on 08-08), illustrating the staleness cost compounding daily. Not
  cross-checked against the other 4 asset groups (out of this role's cefi-only scope).
- **Layer-1 detail unchanged where re-checked**: re-read the still-stale 2026-08-05 rollup's
  `layer_1.by_asset_group.cefi` — `completeness_pct=93.15`, 68/73 present tuples, same 5 missing tuples
  (BITGET-FUTURES/future × 3 data_types, OKX-FUTURES/perpetual × 2) — byte-identical to 08-07/08-08, confirming this is
  genuinely the same unchanged snapshot, not new data coincidentally matching.

## 5. What this run does NOT cover (declared, per the role's Tier-1 scope)

- **No machine-oracle path-structure sweep** (`canonical_path_violations()` over real GCS objects) — never this role;
  the daily Hygiene-vs-GCS digest covers path structure.
- **No id-form / schema Tier-1 sampled check or Tier-2 VM validation** — out of scope entirely.
- **No orphan-object sweep / delete suggestions** — this role never proposes deletes, unconditionally.
- **No full multi-day GCS-side census** — §3 is a one-day, per-mode spot-check; the last full G1 census remains
  2026-07-30 (H8).
- **No fix shipped for the honest-coverage OOM** — cross-asset-group, needs the `--oom-monitor` diagnostic first; the
  existing issue doc was updated in place rather than fixed (§4).
- **Live lane warm-sink estate** — not re-probed this run (unchanged since 08-07's explanation).
- **The other 4 asset groups' honest-coverage staleness** — this role is cefi-only; the OOM affects all 5, but only
  cefi's manifest was independently re-derived (§4's illustrative check).
- **`symbol_rules.py`'s other consumers of `_UNDERLYING_PARTITIONED_TYPES`** (§2a) — confirmed cefi's actual DERIBIT
  combo write/read behavior is healthy via direct object inspection, but did NOT exhaustively grep every call site of
  that constant (e.g., whether it affects tradfi's own combo writes, which per AE-2 still use the bare-`underlying=`
  tail) — out of this role's cefi-only scope.

## 6. Todos

- [ ] [OPERATOR] P1. **ESCALATED (was P2) — honest-coverage-daily VM OOM'd a 3rd/4th consecutive day (08-06, 08-07,
      08-09; 08-08 had no VM per the once-daily schedule), rollup ~86h stale for ALL 5 asset groups, ZERO remediation
      attempts recorded since the 08-08 diagnosis.** anon-rss now FLAT across measured days (~15.35-15.41GB, within 59MB
      of each other) — evidence against organic growth, favours a deterministic ceiling or a leak that maxes out.
      Decide: immediate unblock via `--machine-type e2-highmem-4` re-launch, and/or run `--oom-monitor` for a fresh
      right-sizing diagnostic. See `/plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`
      (updated this run). Repo: deployment-service / instruments-service.
- [ ] [INFRA] P3. **Harden `honest-coverage-daily-launcher` to verify VM terminal state** (carried, unchanged) — not
      just that the `instances.create` API call succeeded. Repo: deployment-service.
- [ ] [DATA] P2. **Registry under-declaration (carried, unchanged 4th day)**: `DERIBIT` has captured 3,910 legitimate
      `volatility_index` rows under `instrument_type=index` since 2021-03-24; "index" is declared nowhere in cefi's
      registries (confirmed again this run — unlike `COMBO`, which IS covered by taxonomy AE-2, "index" has no
      equivalent accepted-exception entry). Decide add-vs-document. Repo: unified-api-contracts.
- [ ] [DATA] P3. **Live lane BYBIT-FUTURES alias-shard (carried, DOWNGRADED from P2 — now flat 4 consecutive days)**: 5
      `empty_confirmed` `live_bybit` rows, unchanged since 08-06. 4 consecutive flat days is a stronger (not yet
      conclusive) signal toward "fixed" than the single flat day known at 08-08's writing — downgrading urgency, but the
      root-cause config review (per 08-07: `bybit_ws.py` dual-registers BYBIT-FUTURES alias + canonical BYBIT) was never
      independently confirmed, so not closing outright. Repo: market-tick-data-service / deployment-service.
- [ ] [INFRA] P3. **Re-run (or schedule) `phantom_audit` for cefi** — now 13 days stale. Repo: instruments-service.
- [ ] [DATA] P3. **Layer-1 missing tuples (carried)**: BITGET-FUTURES/future × 3 data_types + OKX-FUTURES/perpetual × 2
      — declared-expected, never captured; confirm in-scope or deregister. Repo: unified-api-contracts /
      market-tick-data-service.
- [ ] [INFRA] P3. **Manifest hygiene (carried)**: purge the 5,225 stale bare-`OKX` `attempted_failed` rows — dormant a
      5th day, count and timestamp unchanged. Repo: market-tick-data-service / instruments-service.
- [ ] [DIAG] P4. Confirm `instrument_type=spot` (lowercase) relabel — absent a 4th consecutive day, no relabel event
      independently confirmed. Repo: market-tick-data-service / unified-api-contracts.
- [x] [DIAG] P4. ✅ **RESOLVED this run — `batch_aster` / `batch_extended` lanes confirmed still actively capturing**
      (max captured date advanced 08-02→08-03 and 08-02→08-04 respectively), not a stalled fleet. Carried question from
      08-07/08-08, closed via direct manifest check §3a.
- [ ] [DIAG] P4. **NEW — `instrument_type=perpetual` (lowercase, C2a-suppressed) grew +20,543 (~2.2×) in one day**
      (16,848→37,391), well outside the ~1,300/day trend seen 08-07→08-08, while `future`/`spot_pair` (lowercase) stayed
      byte-identical. Not itself a finding (C2a is suppressed by rule), but worth a glance on tomorrow's run to see if
      it's a one-off burst or a new sustained rate. Repo: market-tick-data-service (no action needed yet, observation
      only).
