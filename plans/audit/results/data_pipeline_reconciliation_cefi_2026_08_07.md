---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-07), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-13e51a, slot 13). Both cefi buckets
  healthy: market-data consolidator ran 13 minutes before this audit (produced, 10.70M rows in → 9.99M out, not locked);
  instruments-store consolidator healthy no-op (empty, not locked). Venue census: zero orphaned canonical declarations
  (all 25 UAC venues have manifest presence); M−C drift shrinks to three static populations (bare-OKX 5,225 dormant 3rd
  day, KALSHI_PERP 2, OKX-OPTIONS 2) PLUS one ACTIVE new-entrant: BYBIT-FUTURES grew 4→5 rows with a fresh attempted_at
  2026-08-06T16:36:43Z — a live-lane shard running under the pre-canonicalization alias key (root-caused to MTDS
  connector dual-registration + the live shard launcher enumerating the alias; bybit_ws.py registers both BYBIT and
  BYBIT-FUTURES while canonical instrument keys are BYBIT:). The 08-06 DERIBIT instrument_type=index under-declaration
  persists unchanged (3,910 rows; corroborated a 3rd time by the honest- coverage Layer-1 stray_tuples list).
  instrument_type=spot (lowercase, 4,923 rows on 07-30) absent for a 2nd consecutive day. Batch-layer GCS-vs-manifest
  spot-check (day 2026-08-05, per pipeline_mode) is clean — M−G = ∅, G−M = ∅ across
  batch_hyperliquid/batch_kalshi_perp/batch_tardis. Honest-coverage rollup now 26h old with the 08-06 daily cycle MISSED
  (plus 08-03 absent) — first missed cycle since these reports began; formula re-derived byte-exact (reachable 50.1518%
  → 50.15, all_shards 41.7428% → 41.74). chain axis all-blank in the consolidated index (was ~2,528 rows on the 07-30
  census) — verified as the 2026-07-28 chain-axis heal's ruling target (cefi has no chain shard axis; heal blanks
  contamination at consolidation), NOT data loss. phantom_audit now 11 days stale. Fully read-only; no code changes
  shipped this run.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    census,
    cefi,
    honest-coverage,
    bare-okx-verification,
    bybit-futures-alias-live-shard,
    deribit-volatility-index,
    chain-axis-heal,
    honest-coverage-staleness,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_06,
    defi_cefi_venue_chain_axis_contamination_2026_07_28,
    cefi_bare_okx_venue_removal_2026_08_04,
  ]
created: 2026-08-07
resulting_plan:
lib_version:
  "market-tick-data-service@HEAD (slot 13), unified-api-contracts@HEAD (audited only; no changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) + honest-coverage
  verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) — daily scheduled
  spot-check, not a full campaign. All analysis ran memory-bounded (run-bounded-analysis.sh, 16G cap); no OOM- eligible
  processes launched from this slot (operator directive 2026-08-07 acknowledged)."
date: 2026-08-07
auditor: "cefi_reconciliation_auditor (scheduled role, slot 13, dispatch agt-13e51a)"
parent_epic: security_and_cross_cutting_master
severity: P3
skill: data-pipeline-reconciliation
run_date: 2026-08-07
generated_at: 2026-08-07T00:21:38+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-07), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes. Daily
scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f distinct-value census +
honest-coverage formula/freshness verification, mirroring the 2026-08-05 origin and 2026-08-06 runs.

## 0. Phase-0 reachability + freshness

| bucket                                              | reachable | consolidator lock | last run (UTC)          | verdict                                                              |
| --------------------------------------------------- | --------- | ----------------- | ----------------------- | -------------------------------------------------------------------- |
| `market-data-tick-cefi-prd-central-element-323112`  | yes       | not locked        | 2026-08-07T00:08:09.52Z | produced (10,699,640 rows in → 9,988,973 out; 710,667 dedup-dropped) |
| `instruments-store-cefi-prd-central-element-323112` | yes       | not locked        | 2026-08-07T00:00:51.34Z | empty (0 rows, no-op — consistent with 08-05/08-06)                  |

Consolidator ran **13 minutes before this audit** — fresh, healthy (`stall_state`: streak 0 both buckets). Neither
bucket holds a `consolidator.lock` object (explicit probe).

- `_index/phantom_audit_latest.json` (market-data): `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **11 days
  stale** (was 10 in the 08-06 report; still not re-run daily). `_index/reprobe_audit_latest.json`:
  `generated_at=2026-07-14T06:19:32Z` — 24 days stale, all-zero counts. `instruments-store-cefi` still has **no**
  `phantom_audit_latest.json` at all (H5 — never phantom-checked; standing declared coverage gap).

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`)

Read via the same column-pruned, single-walk-exempt `read_availability_index` reader the deployment-api census endpoint
uses (9,988,973 rows, slim columns, pyarrow pushdown on `asset_group=cefi`).

- **C − M (orphaned declarations)**: **empty** — all 25 UAC-declared cefi venues have manifest presence (3rd consecutive
  day).
- **M − C (drift)** — 4 entries, of which **three are confirmed static and one is NEW-ACTIVE**:
  - `OKX` (bare) — 5,225 rows, all `attempted_failed` `batch_tardis`, `max_attempted_at = 2026-08-04T17:32:43.514974Z` —
    **byte-identical to 08-05 and 08-06** (count, distribution, timestamp). **Confirmed dormant 3rd day.** The 08-05
    bare-OKX orchestrator-literal fix continues to hold: no new bare-OKX rows in the 3 days since.
  - `BYBIT-FUTURES` — **5 rows now (was 4 in the 08-06 report)**, all `empty_confirmed`, `pipeline_mode=live_bybit`,
    `max_attempted_at = 2026-08-06T16:36:43.983380Z` (fresh — was 2026-08-04T10:16:04Z yesterday), dates 2026-07-31 →
    2026-08-06. **This population is ACTIVE, not dormant — see §3.**
  - `KALSHI_PERP` (underscore variant of canonical `KALSHI-PERP`) — 2 `attempted_failed` rows,
    `max_attempted_at = 2026-07-28T01:16:06Z`. Unchanged.
  - `OKX-OPTIONS` — 2 `attempted_failed` rows, `max_attempted_at = 2026-07-26T14:14:45Z`. Unchanged.

## 2. Census — instrument_type + data_type axes

- **Case-only variants (`perpetual`:15,517 / `future`:1,119 / `spot_pair`:12) are the ruled C2a `migration_pending`
  casing axis** — suppressed, not findings (§5.1). Counts shifted slightly since 08-06 (perpetual 13,237 → 15,517),
  consistent with ongoing C2a-adjacent relabeling.
- **`instrument_type=index` (3,910 rows, 100% DERIBIT / `volatility_index` / `batch_deribit` / `captured`, dates
  2021-03-24 → 2026-07-30) — the 08-06 P2 registry under-declaration persists unchanged.** No registry fix landed
  (deribit_declared_it still `{FUTURE, OPTION, PERPETUAL, SPOT_PAIR}`; no `("cefi","index")` valid-data-type key).
  **Corroborated a 3rd time** by the honest-coverage Layer-1 `stray_tuples` (72 entries), which names exactly
  `{"venue": "DERIBIT", "instrument_type": "index", "data_type": "volatility_index"}` — three independent surfaces
  (07-30 census / 08-06 census / this run's census + Layer-1) agree. Todo §7.1 (carried).
- **`instrument_type=spot` (lowercase, 4,923 rows on 07-30) — absent for a 2nd consecutive day.** Still not
  independently root-caused (no relabel event confirmed); the P4 DIAG todo stays open.
- **5 stray `ohlcv_{5m,1h,1d,15s,15m}` data_type values, 2 rows each (10 total) — unchanged** from 07-30 H8, the only
  `data_type` M−C entries. `futures_chain`/`options_chain` instrument_types correctly suppressed as accepted exceptions
  (`CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`).
- **`chain` axis: 0 non-blank values in the consolidated index (was ~2,528 rows at the 07-30 census: STARKNET 2,513 /
  ZKSYNC 1 / FUTURES 8 / POLYMARKET_PERP 3 / KALSHI_PERP 3). Verified NOT a data-loss finding:** the parquet schema
  still declares `chain` (string field, 42 fields total); the blanking is the **2026-07-28 chain-axis heal**
  (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`, status open) — cefi has no chain shard axis per UAC
  `SHARD_AXIS_MATRIX` (defi is the only chain-axis AG), and the consolidator blanks chain contamination at merge. The
  H7/H7-refinement chain-value population was contamination by ruling; its disappearance is the heal's target state, not
  a regression. Reported once for the record; the open issue owns the remaining work.
- `timeframe` (1m/5m/15m/15s/1h/4h/1d ≈ 70k rows each) + `quote_asset`/`margin_type` (USDT 400,086 / USD 5,319 / USDC
  245; linear 400,486 / inverse 5,164) — the MDPS candle rows (490,777 `service_name=market-data-processing- service`)
  and chain-bundle dimensions; vocabulary normal, no finding.

## 3. NEW finding — BYBIT-FUTURES live-lane alias shard is ACTIVE (venue-axis drift, not dormant)

The 08-05/08-06 reports treated venue=BYBIT-FUTURES (4 rows) as static residue. **This run shows it is live:**

- **5 rows (grew +1 since 08-06), all `empty_confirmed`, `pipeline_mode=live_bybit`**, data_types
  `{book_snapshot_5: 2, derivative_ticker: 2, trades: 1}`, dates 2026-07-31 → 2026-08-06, and a **fresh `attempted_at`
  2026-08-06T16:36:43Z** (~8h before this audit). The live lane is writing this shard on an ongoing basis — it is not
  stale residue.
- **Root cause (grep-then-READ, this run):** `bybit_ws.py` registers the connector under BOTH `"BYBIT-FUTURES"` (line
  388, the pre-canonicalization alias) and `"BYBIT"` (line 395), and its own docstring (lines 56-63) states the alias is
  "only the MTDS connector-registry key" — canonical instrument keys are `BYBIT:...`, never `BYBIT-FUTURES:...`. The
  manifest rows come from the live runner recording zero-row windows per `(venue, data_type)` shard
  (`websocket_runner._record_empty_window` → `manifest_recorder.record_zero_rows`, which uses the shard venue verbatim).
  Therefore **something in the live shard launch config enumerates the alias-keyed shard** (a
  `--shard-spec cefi:BYBIT-FUTURES:*` launch), while the canonical `BYBIT` shard is ALSO running (45 `live_bybit` rows
  at venue=BYBIT, captured). The alias shard has no IS universe (no subscriptions) → zero rows → daily
  `empty_confirmed`.
- **Why not fixed inline this run:** unlike the bare-OKX case (a hardcoded literal inside the orchestrator's venue
  enumeration, unambiguous one-line deletion), the dual registration is deliberate alias design, and the fix is in the
  **live shard launch configuration** (deployment-service live launcher), whose enumeration source is not unambiguous
  from an in-session Tier-1 read. Needs the live-deployment owner to confirm the alias shard is not intentional before
  the launcher config is corrected. Filed as todo §7.2.

## 4. GCS-vs-manifest vocabulary spot-check (M △ G) — batch layer clean

Sampled the most recent batch-captured day (**2026-08-05**, max captured batch day in the manifest; 2026-08-06 manifest
rows are still landing, expected ≤1-day consolidation lag), per pipeline_mode (delimiter descent, native handle,
iterator advanced — the v1 probe that silently returned empty prefixes is fixed this run):

| pipeline_mode       | manifest venues (captured)      | GCS venue=* prefixes            | M − G | G − M |
| ------------------- | ------------------------------- | ------------------------------- | ----- | ----- |
| `batch_hyperliquid` | HYPERLIQUID                     | HYPERLIQUID                     | ∅     | ∅     |
| `batch_kalshi_perp` | KALSHI-PERP                     | KALSHI-PERP                     | ∅     | ∅     |
| `batch_tardis`      | COINBASE-FUTURES, COINBASE-SPOT | COINBASE-FUTURES, COINBASE-SPOT | ∅     | ∅     |

**No `shard_atom_vocab_desync` at the batch layer** — same verdict as 08-06. GCS day-level listing for 2026-08-05
confirms only the three batch modes have object dirs (no live dirs — see below).

**Live lane — declared non-covered estate, not a phantom finding:** the manifest records captured rows under `live_*`
modes for days up to 2026-08-07 (lane recency: live_aster captured 2,995 / live_binance 10,787 / live_hyperliquid 3,893
/ live_kraken 6,671 / live_okx 534 / live_bybit 45; live_deribit 31,913 rows, 0 captured), while **no
`pipeline_mode=live_*` day-dirs exist on GCS for ANY day 07-31 → 08-06**. Verified by code read: the live runner's
default sink is `LiveEventFacadeSink` (event-log spine) — it publishes `CanonicalPersistEnvelope`s to Pub/Sub; warm GCS
persistence is provided by the `live_event_log` Terraform Cloud-Storage subscriptions (`warm_sink.tf`, cefi topics →
`var.warm_gcs_bucket`, prefix `live-events/warm/cefi/<data_type>/`, ~5-min batches) — a **different bucket and prefix
from the raw_tick_data tree**, not resolvable in-tree (Terraform-applied value). So live objects' absence under
`raw_tick_data` is architecture, not loss. Verifying the warm-sink estate is the live-event-log lane's own audit (tool:
`deployment-service/scripts/verify_warm_sink_subscription_paths.py`), out of this role's Tier-1 scope — noted, plus a P4
todo.

## 5. Honest-coverage formula + freshness

Read the live rollup from `gs://central-element-323112-honest-coverage/` (bucket probed; latest date dir `2026-08-05`).

- **Freshness: 26h old at audit (generated 2026-08-05T22:19:11Z vs 2026-08-07T00:21Z) and the 2026-08-06 daily cycle is
  MISSING** (due ~2026-08-06T22:19Z, never produced; `2026-08-03` also absent from the available-date series — 08-01,
  08-02, 08-04, 08-05 present). First full-cycle miss since these reports began (08-06's audit called the then-6h-old
  rollup normal). Not root-caused this run — the job is once-daily and its schedule/failure surface is outside the cefi
  bucket estate; filed as todo §7.3.
- **Formula re-derived from raw counts — byte-exact both, 2nd consecutive day:**
  - `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)` = 3,747,467 / 7,472,246 =
    **50.1518%** → published `50.15` ✅ (`empty_confirmed` correctly EXCLUDED per honest-coverage-model.md).
  - `all_shards_coverage = captured / total` = 3,747,467 / 8,977,521 = **41.7428%** → published `41.74` ✅.
- `denominator_status=INCOMPLETE`; Layer-1: **72 `stray_tuples`** (incl. the DERIBIT/index/volatility_index entry —
  corroboration §2) and **5 `missing_tuples` unchanged** (BITGET-FUTURES/future × book_snapshot_5/derivative_ticker/
  trades, OKX-FUTURES/perpetual × book_snapshot_5/derivative_ticker); completeness ~93.15% (68/73, same rollup file as
  08-06).
- `by_chain.cefi` still exactly one blank-key entry — the chain-axis heal (and the `unified-trading-library@7684a102`
  heal) holds on a 3rd day.

## 6. What this run does NOT cover (declared, per the role's Tier-1 scope)

- **No machine-oracle path-structure sweep** (`canonical_path_violations()` over real GCS objects) — never this role;
  the daily Hygiene-vs-GCS digest covers path structure.
- **No id-form / schema Tier-1 sampled check or Tier-2 VM validation** — out of scope entirely.
- **No orphan-object sweep / delete suggestions** — this role never proposes deletes, unconditionally.
- **No full multi-day GCS-side census** — §4 is a one-day, per-mode spot-check; the last full G1 census remains
  2026-07-30 (H8).
- **Live lane warm-sink estate** (`live-events/warm/cefi/*` in `var.warm_gcs_bucket`) — not probed (Terraform-applied
  bucket unknown in-tree); the live-event-log lane's own audit. Also `batch_aster`/`batch_extended` last captured
  2026-08-02 (5 days) — a completed-drain vs stalled-fleet question, P4 todo §7.6.
- **The 72-entry Layer-1 `stray_tuples` list** not individually triaged (belongs to the Layer-1 enumeration lane, CK2) —
  only the DERIBIT/index entry cross-corroborated.
- **No code changes** — pure verification + census. The one code-adjacent activity was root-causing §3's alias shard
  (read-only) and confirming §2's chain-axis heal explains the blank census.

## 7. Todos

- [ ] [DATA] P2. **Registry under-declaration (carried from 08-06; persists unchanged)**: `DERIBIT` has captured 3,910
      legitimate `volatility_index` rows under `instrument_type=index` since 2021-03-24; "index" is declared nowhere in
      cefi's registries (`INSTRUMENT_TYPES_BY_VENUE["DERIBIT"]`, `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`).
      Corroborated by the honest-coverage Layer-1 `stray_tuples` on a 3rd surface. Decide add-vs-document. Repo:
      unified-api-contracts.
- [ ] [DATA] P2. **NEW — live lane writes non-canonical venue=BYBIT-FUTURES manifest rows (ACTIVE)**: 5
      `empty_confirmed` `live_bybit` rows (grew 4→5, fresh attempted_at 2026-08-06T16:36:43Z), shards
      book_snapshot_5/derivative_ticker/trades. Root cause: live shard launcher enumerates the pre-canonicalization
      alias key (`bybit_ws.py` registers BYBIT-FUTURES:388 + BYBIT:395; canonical instrument keys are `BYBIT:`). Fix the
      live shard launch config to use `BYBIT` (confirm with the live-deployment owner that the alias shard isn't
      intentional first). Repo: market-tick-data-service / deployment-service.
- [ ] [INFRA] P3. **NEW — honest-coverage daily rollup missed the 2026-08-06 cycle** (rollup 26h old; 08-03 also absent
      from the date series). Confirm the job's schedule + last-run health and re-run the missed cycle. Repo: owner of
      the honest-coverage job (deployment-service / instruments-service).
- [ ] [INFRA] P3. **Manifest hygiene (carried)**: purge the 5,225 stale bare-`OKX` `attempted_failed` rows — dormant a
      3rd day, count and timestamp unchanged. Repo: market-tick-data-service / instruments-service.
- [ ] [INFRA] P3. **Re-run (or schedule) `phantom_audit` for cefi** — now 11 days stale. Repo: instruments-service.
- [ ] [DATA] P3. **Layer-1 missing tuples (carried)**: BITGET-FUTURES/future × 3 data_types + OKX-FUTURES/perpetual × 2
      — declared-expected, never captured; confirm in-scope or deregister. Repo: unified-api-contracts /
      market-tick-data-service.
- [ ] [DIAG] P4. Confirm `instrument_type=spot` (lowercase, 4,923 rows on 07-30) relabel — absent 2nd consecutive day,
      no relabel event independently confirmed. Repo: market-tick-data-service / unified-api-contracts.
- [ ] [DIAG] P4. **batch_aster / batch_extended lanes last captured 2026-08-02** (5 days) — completed backfill vs
      stalled fleet? Check the ASTER/EXTENDED batch VMs' fleet state. Repo: market-tick-data-service.
- [ ] [DIAG] P4. Verify the live lane's warm-sink estate (`live-events/warm/cefi/*` objects in `warm_gcs_bucket`)
      actually materializes — manifest records live captured rows through 2026-08-07 with zero objects in the
      raw_tick_data tree (expected by design; the warm-sink verification script is
      `deployment-service/scripts/verify_warm_sink_subscription_paths.py`). Repo: deployment-service.
