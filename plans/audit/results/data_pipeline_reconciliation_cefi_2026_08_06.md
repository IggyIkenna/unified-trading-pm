---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-06), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role). Both cefi buckets healthy: market-data
  consolidator ran fresh 6h before this audit (produced, no lock), instruments-store empty-but-healthy (no-op, no
  lock). Venue census: zero orphaned canonical-DECLARATIONS (all 25 UAC venues have manifest presence); the same 4
  non-canonical M-C venue values from 2026-08-05 persist UNCHANGED (identical counts, identical max attempted_at) —
  confirming they are dormant/stale, not active. Independently VERIFIED the 2026-08-05 bare-OKX orchestrator-literal fix
  (market-tick-data-service@ff2e9d66) is not only shipped but empirically live: 498,083 batch_tardis rows attempted
  across 24 venues since the fix commit, ZERO bare "OKX" among them. NEW finding: DERIBIT's `volatility_index` shard has
  written 3,910 legitimately-captured rows under `instrument_type=index` since 2021-03-24, but "index" is not declared
  anywhere in cefi's instrument-type registry (`INSTRUMENT_TYPES_BY_VENUE["DERIBIT"]`,
  `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("cefi", ...)]`) — independently corroborated by the honest-coverage
  Layer-1 enumerator's own `stray_tuples` list, which names this exact `(DERIBIT, index, volatility_index)` tuple. Also
  surfaced via the same Layer-1 payload: 5 declared-but-never-captured tuples (BITGET-FUTURES x3, OKX-FUTURES x2) — a
  gap distinct from both the DERIBIT/index case (captured-but-undeclared) and the already-tracked BINANCE-DELIVERY case
  (undeclared-and-never-captured). GCS-vs-manifest vocabulary spot-check (one sampled recent captured day) is clean, no
  desync. Honest-coverage formula independently re-derived from raw counts and matches the published rollup byte-exact
  for both `reachable_coverage` (50.15%) and `all_shards_coverage` (41.74%); rollup is 6h old
  (generated 2026-08-05T22:19:11Z vs audit time 2026-08-06T04:2x), normal freshness for a once-daily job, not stale.
  `phantom_audit_latest.json` is now 10 days stale (generated 2026-07-27), one day more than 2026-08-05's report. No
  code changes shipped this run — read-only confirmation + census only.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    census,
    cefi,
    honest-coverage,
    bare-okx-verification,
    orphaned-instrument-type,
    deribit-volatility-index,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_05,
    cefi_bare_okx_venue_removal_2026_08_04,
  ]
created: 2026-08-06
resulting_plan:
lib_version: "market-tick-data-service@202bacc9, unified-api-contracts@f2214c09 (audited only, no changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) only per the
  cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) — daily scheduled spot-check, not a full
  campaign"
date: 2026-08-06
auditor: "cefi_reconciliation_auditor (scheduled role, slot 4, dispatch agt-d019d3)"
parent_epic: security_and_cross_cutting_master
severity: P3
skill: data-pipeline-reconciliation
run_date: 2026-08-06
generated_at: 2026-08-06T04:26:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-06), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes. This is
the daily scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f
distinct-value census + an honest-coverage formula verification, mirroring the 2026-08-05 origin run's scope.

## 0. Phase-0 reachability + freshness

| bucket                                               | reachable | consolidator lock | last run (UTC)          | verdict                                                              |
| ----------------------------------------------------- | --------- | ------------------ | ------------------------ | --------------------------------------------------------------------- |
| `market-data-tick-cefi-prd-central-element-323112`   | yes       | not locked         | 2026-08-06T04:08:11.23Z | produced (10,517,229 rows in → 9,838,219 out; 679,010 dedup-dropped) |
| `instruments-store-cefi-prd-central-element-323112`  | yes       | not locked         | 2026-08-06T04:01:13.65Z | empty (0 rows this cycle, no-op — consistent with 2026-08-05)        |

`_index/phantom_audit_latest.json` (market-data bucket): `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **10
days stale** relative to this run (was 9 days in the 2026-08-05 report; not re-run here, single-walk discipline).
`_index/reprobe_audit_latest.json`: `generated_at=2026-07-14T06:19:32Z` — 23 days stale, zero new/disagreement/ambiguous
counts recorded at that time; not independently notable this run. `instruments-store-cefi-prd` still has **no**
`phantom_audit_latest.json` at all (H5 — never phantom-checked), a standing declared coverage gap, not assessed here.
Neither bucket has a `consolidator.lock` object — both consolidators confirmed NOT locked (explicit probe, not
inferred from absence-of-mention).

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`)

Read via the same column-pruned, single-walk-exempt `read_availability_index` reader the deployment-api census
endpoint uses (9,838,219 rows, all 9 census columns).

- **C − M (orphaned declarations)**: **empty**, same as 2026-08-05. Every one of the 25 UAC-declared cefi venues has at
  least one real manifest row.
- **M − C (drift)** — **identical to 2026-08-05, byte-for-byte, including `max_attempted_at`**:
  - `OKX` (bare) — 5,225 rows, all `attempted_failed`, all `pipeline_mode=batch_tardis`, `max_attempted_at =
    2026-08-04T17:32:43.514974Z` — **unchanged count and unchanged timestamp** since yesterday's report. See §3 — this
    is now confirmed dormant, not merely unchanged-by-coincidence.
  - `BYBIT-FUTURES` — 4 `empty_confirmed` rows, `max_attempted_at = 2026-08-04T10:16:04Z`. Unchanged.
  - `KALSHI_PERP` (underscore variant of canonical `KALSHI-PERP`) — 2 `attempted_failed` rows, `max_attempted_at =
    2026-07-28T01:16:06Z`. Unchanged.
  - `OKX-OPTIONS` — 2 `attempted_failed` rows, `max_attempted_at = 2026-07-26T14:14:45Z`. Unchanged.

  **Zero new M-C venue drift appeared in the 24h since the last audit.** All four populations are static — none grew,
  none shrank, none gained a fresh `attempted_at`. Not actioned (same disposition as 2026-08-05: low-volume, stale,
  non-recurring, except bare-OKX which is addressed in §3).

## 2. Census — instrument_type + data_type axes

- **Case-only variants (`perpetual`:13,237 / `future`:910 / `spot_pair`:12) are the already-ruled C2a
  `migration_pending` casing axis** — correctly suppressed, not a fresh finding (`reconciliation-finding-taxonomy.md`
  §5.1).
- **`instrument_type=spot` (lowercase) — the 4,923-row population flagged in the 2026-07-30 first-census (H8) is NO
  LONGER PRESENT** in today's manifest census. Not independently root-caused this run (would need to confirm a
  relabel/migration landed vs. this being a read artifact) — flagged for the next investigator rather than asserted.
- **5 stray `ohlcv_{5m,1h,1d,15s,15m}` data_type values, 2 rows each (10 total) — unchanged from 2026-07-30's H8
  finding**, exact same per-value counts. Static residue, consistent with the existing "pre-MDPS-candle-layer
  historical/test artifact" framing. `futures_chain`/`options_chain` instrument_type values remain correctly suppressed
  as accepted exceptions (`CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`).
- **NEW — `instrument_type=index` (3,910 rows), a genuine registry under-declaration, not a defect in the data
  itself.** Drilled into this population (was not named in any prior cefi census report, including 2026-07-30's H8 or
  2026-08-05's report):
  - 100% `venue=DERIBIT`, `data_type=volatility_index`, `pipeline_mode=batch_deribit`, `capture_status=captured` (every
    row genuinely captured, none `attempted_failed`/`empty_confirmed`).
  - Spans `date` 2021-03-24 → 2026-07-30 — a multi-year-old, stable production population, not a recent regression.
  - `INSTRUMENT_TYPES_BY_VENUE["DERIBIT"]` declares only `{PERPETUAL, OPTION, FUTURE, SPOT_PAIR}` — "index" is absent.
    `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` has no `("cefi", "index")` key at all (only `("tradfi", "index")` —
    "index" is a real, live enum value elsewhere in the system, just never declared for cefi).
  - **Independently corroborated by a second surface**: the honest-coverage rollup's own Layer-1 enumerator
    (`layer_1.by_asset_group.cefi.stray_tuples`, 2026-08-05 rollup) separately lists
    `{"venue": "DERIBIT", "instrument_type": "index", "data_type": "volatility_index"}` as a stray (real-but-undeclared)
    tuple — the same finding, reached via a completely different code path (Layer-1 expected-tuple enumeration vs. this
    run's raw manifest census). Two independent surfaces agreeing rules out a one-off read artifact.
  - This is the mirror-image of 2026-08-05's `COINBASE-FUTURES`/`EXTENDED-STARKNET`/`LIGHTER-ZKSYNC` under-declared
    `ohlcv_1m` finding — real, multi-year production capability the registry doesn't know about — but on the
    `instrument_type` axis instead of the `(venue, data_type)` capability axis. Filed as a todo (§7), not fixed inline:
    adding a new legal instrument_type to a per-venue registry has validation-path implications beyond what a Tier-1
    in-session census can verify (unlike the bare-OKX literal removal, which was a self-contained, already-tested
    deletion).
  - Smaller, likely-related residue on the same `data_type=volatility_index`: 158 rows with blank `instrument_type`,
    96 rows `BINANCE-DELIVERY`/`futures_chain`, 5 rows `PERPETUAL` — not separately investigated this run (each is
    small, and the blank case is consistent with the standing H6 `source=`/blank-axis wiring-gap pattern already known
    for cefi); noted for whoever picks up the DERIBIT/index todo.
- **The same honest-coverage Layer-1 payload also lists ~70 total `stray_tuples`** beyond the DERIBIT/index entry
  above, and **5 `missing_tuples`** (declared-but-never-captured: `BITGET-FUTURES`/`future` × 3 data_types,
  `OKX-FUTURES`/`perpetual` × 2 data_types) — `layer1_completeness_pct=93.15%` (68/73 expected tuples present). Most of
  the stray-tuple list is explained by the same C2a case-migration pattern already suppressed above (e.g.
  `ASTER/PERPETUAL/...` uppercase vs. a lowercase-declared expectation) plus the chain-bundle instrument types; **not
  individually triaged this run** — that full reconciliation is the Layer-1 enumeration matrix's own audit lane (CK2),
  distinct from this skill's §3f census. Recorded here only because it happened to corroborate the DERIBIT/index
  finding and surface the 5 missing-tuples gap as a byproduct of fetching that one entry.

## 3. Verified — 2026-08-05's bare-OKX orchestrator-literal fix is shipped AND confirmed live (no code change this run)

2026-08-05's report left `market-tick-data-service`'s `venues.extend(["OKX", "COINBASE-CDE"])` fix
(`engine/orchestrator/__init__.py:365`) code-complete but **not yet committed** (blocked on a clean `quality-gates.sh`
run in a heavily-contended shared checkout). This run confirms it has since shipped and verified it is genuinely
effective in production, not merely present in the tree:

- `git log` on this slot's `market-tick-data-service` clone shows `ff2e9d66` ("remove hardcoded bare-OKX venue
  injection...") on `live-defi-rollout`, committed `2026-08-05T22:34:47+01:00` (`2026-08-05T21:34:47Z`). The live
  source at `engine/orchestrator/__init__.py:377` now reads `venues.extend(["COINBASE-CDE"])` — bare `"OKX"` is gone.
- **Empirical confirmation, not just a code read**: queried the manifest for `batch_tardis` rows with
  `attempted_at` after the fix's commit timestamp. Found **498,083 rows across 24 distinct venues** (including the
  correctly-registered `OKX-FUTURES`/`OKX-SPOT`/`OKX-SWAP`) attempted since the fix landed — real, substantial
  post-fix venue-enumeration activity — and **zero** of them are bare `"OKX"`. This is the evidence the 2026-08-05
  report couldn't yet produce (the fix hadn't shipped at write time): the code path that used to inject bare OKX has
  actually run hundreds of thousands of times since the fix, and bare OKX has not reappeared.
- The residual 5,225 `attempted_failed` OKX rows (§1) are therefore now **confirmed-dormant historical residue**, not
  an active or latent regression — a manifest-hygiene cleanup candidate (§7), not a code-correctness question.
- Cross-checked `plans/active/issues/cefi_bare_okx_venue_removal_2026_08_04.md` (the separate, earlier UAC-registry-side
  fix for bare OKX): `status: resolved`, both its own todos closed 2026-08-04. That issue and yesterday's
  orchestrator-literal fix were two independent defects with the same symptom (per yesterday's report, the orchestrator
  literal was "independent of and never updated when the UAC fix shipped") — both are now confirmed resolved.

## 4. GCS-vs-manifest vocabulary spot-check (M △ G)

Per §3f's third comparison, sampled one recent fully-captured day rather than a full multi-day sweep (Tier-1 budget):
most recent `capture_status=captured` `batch_tardis` day in the manifest is **2026-07-31→2026-08-04 range**, with
**2026-08-04** the latest — manifest shows `{COINBASE-FUTURES, COINBASE-SPOT}` captured that day (consistent with
reference-cefi's H1 "Tardis N=1" hazard — only one/two venues captured on any given recent day). Delimiter-descended
`raw_tick_data/by_date/day=2026-08-04/pipeline_mode=batch_tardis/asset_group=cefi/` on GCS directly (native-handle
route, not the UTL facade which drops `.prefixes` per the skill's own warning): GCS returned the exact same
`{COINBASE-FUTURES, COINBASE-SPOT}` set. **M − G = ∅, G − M = ∅** for this sample — no `shard_atom_vocab_desync`
detected. This is a one-day spot-check, not a corpus-wide sweep; a full G1 GCS-side census across all days remains
last-run 2026-07-30 (H8), not re-run here.

## 5. Honest-coverage formula + freshness

Read the live rollup directly from `gs://central-element-323112-honest-coverage/2026-08-05/coverage.json` (most recent
available; no `2026-08-06` entry yet at audit time `2026-08-06T04:2xZ` — expected, the job runs once daily and had not
fired yet for today. Note `2026-08-03` is also absent from the last-10-dates listing between `2026-08-02` and
`2026-08-04`; not investigated further this run, out of cefi-specific scope).

- `generated_at=2026-08-05T22:19:11Z` — **~6 hours old at audit time, normal freshness for a once-daily job, not
  stale.**
- `by_asset_group.cefi` raw counts: `captured=3,747,467`, `empty_confirmed=1,505,275`, `attempted_failed=545,029`,
  `expected_unattempted=3,179,750`, `total=8,977,521`.
- **Independently re-derived both formulas from those raw counts** (not just read the published percentage) —
  matches the SSOT (`honest-coverage-model.md` § Coverage formula) **byte-exact**:
  - `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)` = 3,747,467 / 7,472,246 =
    **50.1518%** → published `coverage_pct: 50.15` ✅.
  - `all_shards_coverage = captured / total` = 3,747,467 / 8,977,521 = **41.7428%** → published
    `all_shards_coverage_pct: 41.74` ✅.
- `by_chain.cefi` still shows exactly one entry keyed by the blank string, confirming the `unified-trading-library@
  7684a102` chain-axis heal (verified 2026-08-05) continues to hold — no chain-axis contamination on a second day.
- `layer1_completeness_pct=93.15%`, `denominator_status=INCOMPLETE` (68/73 expected tuples present) — see §2 for the 5
  named missing tuples and the stray-tuple cross-reference.

## 6. What this run does NOT cover (declared, per the role's Tier-1 scope)

- **No machine-oracle path-structure sweep** (`canonical_path_violations()` over real GCS objects) — this role never
  runs it (does_not, role frontmatter); the daily Hygiene-vs-GCS digest covers path structure on its own cadence.
- **No id-form / schema Tier-1 sampled check** (§3g) or Tier-2 100%-corpus VM validation (§7) — out of this role's
  scope entirely.
- **No orphan-object sweep** (§4a) and **no delete suggestions** — this role never proposes deletes, unconditionally.
- **No full multi-day GCS-side census** — §4 above is a one-day spot-check, not a corpus sweep; the last full G1
  census remains 2026-07-30 (H8).
- **`instruments-store-cefi` bucket** — Phase 0 only (reachability + freshness); still empty/near-zero volume, still
  not phantom-checked (H5), no census run against it this cycle (same disposition as 2026-08-05).
- **The ~70-entry honest-coverage `stray_tuples` list (§2) was not individually triaged** beyond the one entry
  (DERIBIT/index) this run's own census independently surfaced — that full reconciliation belongs to the Layer-1
  enumeration matrix's own audit lane.
- **No new code changes** — this run is pure verification + census; the one code-adjacent action was confirming (not
  authoring) 2026-08-05's already-shipped fix.

## 7. Todos

- [ ] [DATA] P2. **Registry under-declaration (NEW this run)**: `DERIBIT` has captured 3,910 legitimate
      `volatility_index` rows under `instrument_type=index` since 2021-03-24, but "index" is not declared in
      `INSTRUMENT_TYPES_BY_VENUE["DERIBIT"]` or `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` for cefi anywhere.
      Corroborated independently by the honest-coverage Layer-1 `stray_tuples` list. Decide whether to add `INDEX` to
      DERIBIT's declared instrument types (and to cefi's valid-data-types-by-instrument-type map) or document why it's
      deliberately excluded. Repo: unified-api-contracts.
- [ ] [DATA] P3. **Layer-1 missing tuples**: `BITGET-FUTURES`/`future` (book_snapshot_5, derivative_ticker, trades) and
      `OKX-FUTURES`/`perpetual` (book_snapshot_5, derivative_ticker) are declared-expected but have never been
      captured (per the 2026-08-05 honest-coverage rollup's Layer-1 `missing_tuples`). Confirm whether these
      (venue, instrument_type, data_type) combinations are still in-scope and root-cause the zero-capture, or
      deregister them. Repo: unified-api-contracts / market-tick-data-service.
- [ ] [INFRA] P3. **Manifest hygiene**: purge the 5,225 stale bare-`OKX` `attempted_failed` rows (all dated on/before
      2026-08-04, confirmed dormant — see §3) now that the root-cause fix is shipped and empirically verified live.
      Low urgency (they don't affect `reachable_coverage`'s numerator, only pollute the venue census). Repo:
      market-tick-data-service or instruments-service (whichever owns the cefi manifest-purge tooling).
- [ ] [INFRA] P3. Re-run (or schedule) a fresh `phantom_audit` for cefi — now 10 days stale (was 9 yesterday, growing
      by design since it's not re-run daily). Repo: instruments-service.
- [ ] [DIAG] P4. Confirm whether the 2026-07-30 `instrument_type=spot` (lowercase, 4,923 rows) population noted in H8
      was migrated/relabeled — it is no longer present in today's census, and no relabeling event was independently
      confirmed this run. Repo: market-tick-data-service / unified-api-contracts.
