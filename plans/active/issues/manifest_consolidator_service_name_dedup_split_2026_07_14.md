---
doc_type: issue
title:
  'manifest_consolidator: the TEAMS `expected_unattempted`-won''t-drop symptom is a `service_name` dedup-key split, NOT
  the plan''s diagnosed optional-column NULL/`""`-normalization gap (that normalization has been complete + correct
  since unified-trading-library@f5ec2291, 2026-07-06) — reproduced locally'
summary:
  'data_engineering investigation (slot-5, 2026-07-14) of sports_data_sources_canonical_completion task -016. The
  plan''s P1 todo attributes the TEAMS `expected_unattempted` count not dropping after the 61-league backfill to a
  NULL-vs-empty dedup-key normalization gap across optional dimension columns
  (chain/instrument_type/instrument_id/quote_asset/ margin_type/combo_type/fixture_id/job_id). VERIFIED FALSE:
  `manifest_consolidator._dedup_key_sql` already collapses NULL == '''' for every dedup-key column via the `part_norm`
  used in EVERY `PARTITION BY` (incl. the `--force` full-rebuild path at line 2324), and it landed 2026-07-06 (f5ec2291)
  — BEFORE the 2026-07-13 observation. The REAL, reproduced root cause: the backfill script writes
  `service_name="backfill-teams-61-leagues"` (backfill_teams_61_leagues_2026_07_13.py:212,230) while the enumerator
  `expected_unattempted` seed writes `service_name="instruments-service"`. `service_name` is a BASE dedup key
  (consolidator SSOT line 152), so the two twin rows land in DIFFERENT dedup groups and the captured row can never
  supersede its seed. The plan''s own aggregate proof (165,148 TEAMS `(source,data_type,league_id,date,venue)` keys with
  >1 distinct capture_status — a key that EXCLUDES service_name) is exactly the signature of a service_name-only split.
  Fixing this is a fleet-wide dedup-key semantics decision (does service_name belong to cell IDENTITY or to PROVENANCE,
  like `source` which was already excluded from the key?) and needs an operator ruling before any code lands.'
status: resolved
nature: notes
asset_group: [cross-cutting, defi, cefi, tradfi, prediction, sports, meta]
stage: [meta]
repos: [unified-trading-library, instruments-service]
scope: [engineer, admin]
tags:
  [manifest-consolidator, dedup-key, service_name, expected_unattempted, sports, teams, data-correctness, misdiagnosis]
related: [../sports_data_sources_canonical_completion_2026_07_13.md, ../understat_bulk_download_backfill_2026_06_29.md]
created: 2026-07-14
parent_epic: infrastructure_master
priority: P1
source:
  "data_engineering worker (slot-5, planning VM), 2026-07-14, executing AO task
  sports_data_sources_canonical_completion-016. Static code read + git-blame of unified_trading_library/
  manifest_consolidator.py + a local DuckDB reproduction of the exact `part_norm` PARTITION BY over the AUSTRALIA_CUP/
  2020-05-15 twin row-pair, plus confirmation of the two service_name values in source."
assigned_vm: planning
locked_by:
resolved_by:
  "Option B (operator ruling BLK-17603e1f) shipped in unified-trading-library manifest_consolidator, 2026-07-14 slot-5"
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
depends_on: []
---

## What I found

The plan `sports_data_sources_canonical_completion_2026_07_13.md` P1 todo -016 ("manifest_consolidator dedup-key
NULL/`""`-normalization gap") states that TEAMS `expected_unattempted` didn't drop after the 61-league backfill because
several optional dimension columns (`chain`/`instrument_type`/`instrument_id`/`quote_asset`/`margin_type`/`combo_type`/
`fixture_id`/`job_id`) differ between `None` (enumerator seed) and `""` (captured backfill rows), so DuckDB's dedup
`PARTITION BY` never groups the captured row with its `expected_unattempted` seed twin.

**This diagnosis is incorrect.** Two independent proofs:

1. **The NULL/`""` normalization already exists and is complete.** `manifest_consolidator._dedup_key_sql(col)` =
   `coalesce(nullif(cast(col AS VARCHAR), ''), '<sentinel>')` collapses BOTH NULL and `""` to one sentinel. It is
   applied to EVERY dedup-key column via `part_norm = ", ".join(_dedup_key_sql(c) for c in dedup)`
   (manifest_consolidator.py:2049), and `part_norm` is used in EVERY `PARTITION BY` in the file — the incremental
   anti-join AND the `--force` full-rebuild window (line 2324, which is the path the plan's `--force` rebuild took). It
   landed in `f5ec2291` on **2026-07-06**, a week BEFORE the 2026-07-13 observation. So at observation time, optional
   columns already collapsed NULL == "".

2. **Local reproduction of the exact partition.** Replaying the consolidator's `_dedup_key_sql` + `_resolve_dedup_cols`
   - `part_norm` over the AUSTRALIA_CUP/2020-05-15 twin row-pair the plan cites: the optional columns
     (chain/instrument_type/instrument_id) with NULL vs `""` BOTH normalize to `__UTL_CONSOLIDATOR_NULL_4e8a2__` — they
     do NOT split. The rows split into 2 dedup groups **solely because of `service_name`**: `backfill-teams-61-leagues`
     (captured) vs `instruments-service` (seed). Dropping `service_name` from the key collapses them to 1 group.

**The real root cause:** `service_name` is a BASE dedup key
(`_BASE_DEDUP_COLS = (date, venue, data_type, service_name)`; consolidator SSOT line 152). The backfill script
deliberately instantiates `ManifestWriter(service_name="backfill-teams-61-leagues")`
(`instruments-service/scripts/ backfill_teams_61_leagues_2026_07_13.py:212,230`), a different value from the enumerator
seed's `instruments-service`. Two genuinely-distinct, non-empty `service_name` values → different dedup groups → the
captured row never enters the same group as its `expected_unattempted` seed, so the existing "captured outranks recency"
tie-break (unified-trading-library@a05d69c7) never fires. The plan's own aggregate metric — 165,148 TEAMS
`(source,data_type,league_id,date,venue)` keys with >1 distinct capture_status, on a key that EXCLUDES `service_name` —
is precisely the fingerprint of a service_name-only split.

## Why it matters

- **The task as written cannot succeed.** Extending `_dedup_key_sql`/`_OPTIONAL_DEDUP_COLS` to the remaining optional
  columns (the plan's prescribed fix) is a no-op for this symptom (those columns are not the splitter) and is
  directionally counter-productive: adding a column to the dedup key can only ADD split axes, never remove the
  `service_name` one. Shipping it would flip the checkbox on false progress while `expected_unattempted` stays inflated.
- **Fleet-wide data-correctness.** Any backfill/one-off that writes a distinct `service_name` for a cell already seeded
  by the main service will leave permanent non-collapsing `expected_unattempted` twins across EVERY asset_group, not
  just sports. This understates real captured coverage on every coverage gate/UI that reads the manifest.

## Reproduction

`scratchpad/repro_dedup.py` (local, no GCS needed) — builds the two twin rows, applies the current `part_norm`, prints:
`distinct dedup groups: 2 => SPLIT`; and with `service_name` removed from the key: `1 => COLLAPSE`. The optional-column
sentinels are identical across both rows (proving they are not the splitter).

## Recommended decision (operator ruling required — fleet-wide dedup semantics)

The core question: **is `service_name` cell IDENTITY or PROVENANCE?** The consolidator already treats `source` (vendor)
as provenance and deliberately EXCLUDES it from the dedup key (manifest_consolidator.py:2106-2108: "source is vendor
provenance, not venue identity — collapsing two vendors' rows for one cell is CORRECT for coverage purposes"). By the
same logic `service_name` = which service/script wrote the row = provenance, and two services capturing the same
`(date, venue, data_type, +optional dims)` cell should collapse for coverage.

- **Option A: exclude `service_name` from the consolidator dedup key** (drop it from `_BASE_DEDUP_COLS`, and from the
  writer's mirror), exactly as `source` already is. The status-aware tie-break then keeps the captured survivor; its
  `service_name` provenance is preserved on the winning row. Cleanest/most principled if `service_name` is purely
  provenance — BUT the rule-11 live proof below found this is NOT a no-op: it collapses **607 defi captured-vs-captured
  dual-source atoms** (MTDS-subgraph ✕ MDPS-rpc, distinct row_counts) in addition to the sports captured-vs-EU twins,
  dropping one source's captured record. That collapse is a second, separate coverage-accounting decision A forces.
- **Option B (now the safer lean per the rule-11 proof): status-aware cross-`service_name` collapse only.** Keep
  `service_name` in the key for the general case, but when a `captured` row and a NON-captured row (e.g.
  `expected_unattempted`) are identical on all OTHER dedup dims, collapse them keeping the captured one (mirrors the
  existing source-aware `row_count` collapse). Fixes the sports EU-twin bug (165,148 TEAMS) WITHOUT collapsing the 607
  defi captured-vs-captured dual-source rows (both captured → B leaves them alone). More surgical; more complex SQL.
- **Option C: data remediation only.** Rewrite the 165,148 backfill rows' `service_name` to `instruments-service` so
  they collapse under the current key. One-off, does NOT prevent recurrence, and contradicts the plan's own ruling
  (lines 120-128) that the custom `service_name` is "honest provenance… NOT a service_name-drift bug."

## Blast-radius scan (static, code-side — 2026-07-14 slot-5)

`rg` of all `service_name=` writer/`setup_events` call sites fleet-wide shows `service_name` is dominated by REAL,
distinct services — `features-service` / `instruments-service` / `market-tick-data-service` (`mtds`) /
`market-data-processing-service` / `strategy-service` / `execution-service` / `ml-service` — each of which owns a
DIFFERENT `data_type` set, so a `(date, venue, data_type)` atom is normally owned by exactly one service (Option A's
collapse would be a no-op for them). Two findings this hands the operator:

1. **The bug class RECURS.** Custom one-off `service_name`s are a standing pattern: `migrate-cefi-v2`,
   `dr-drill-cutover`, `backfill-teams-61-leagues`, etc. Every such one-off that captures cells previously seeded by the
   main service re-creates the non-collapsing-twin bug. This argues for a GENERAL fix (A or B) over the one-off data
   remediation (C).
2. **Option A's residual risk is a live-only question — NOW ANSWERED (see the rule-11 LIVE proof section below).**
   Static code could not prove whether two service_names ever write the SAME `(date, venue, data_type, +optional dims)`
   atom with distinct real coverage. The live GCS proof found they DO: 607 defi atoms carry MTDS-subgraph ✕ MDPS-rpc
   captured pairs with distinct row_counts. So Option A's collapse is real, not a no-op — this is what shifts the lean
   to Option B.

## 🔬 Rule-11 LIVE blast-radius proof (2026-07-14 slot-5) — Option A is NOT a no-op; Option B is safer

The rule-11 GCS proof owed above (finding #2) is now DONE. ADC works via the Python SDK on this slot (only the `gcloud`
CLI was broken — the earlier "no ADC" note was a CLI artifact). Read the CONSOLIDATED canonical index
(`_index/availability_index.parquet`) for all four non-sports asset_groups — one bounded download each, no corpus walk —
and ran, per AG, the exact query owed: over the atom
`(date, venue, data_type + present optional dedup dims, normalized with the consolidator's own `_dedup_key_sql`, EXCLUDING `service_name`)`,
how many atoms have ≥2 DISTINCT `service_name` values that EACH carry a `capture_status='captured'` row? (Repro:
`scratchpad/rule11_service_name_blast_radius.py` + `scratchpad/rule11_defi_deepdive.py`.)

| asset_group | captured rows | Option-A collapse-risk atoms | who splits                                                                              |
| ----------- | ------------- | ---------------------------- | --------------------------------------------------------------------------------------- |
| cefi        | 3,123,369     | **0**                        | — (only `market-tick-data-service` + a NULL-service legacy set; no two-service overlap) |
| defi        | 3,010,913     | **607**                      | `market-tick-data-service` (subgraph) ✕ `market-data-processing-service` (rpc)          |
| tradfi      | 1,608,390     | **1**                        | one-off `migrate-tradfi-canonical` + mtds + is + mdps                                   |
| prediction  | 45,988        | **1**                        | one-off `migrate-polymarket-canonical` + mtds + is + mdps                               |

**Fleet total: 609 collapse-risk atoms.** The tradfi/prediction 1-each involve one-off migration `service_name`s (the
same recurrence pattern as sports' `backfill-teams-61-leagues`). The **607 defi atoms are the material finding** and
they are NOT phantom duplicates:

- data_types: `swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d}` (606 each), `dex_pool_state` (598), `dex_pool_swaps` (593), + a
  long tail of 1-atom onchain types.
- The two captured rows are genuine **dual-source captures of the same cell**: the MTDS row is `source=onchain_subgraph`
  / `pipeline_mode=batch_onchain_subgraph`; the MDPS row is `source=onchain_rpc` / `pipeline_mode=batch_onchain_rpc`.
- Redundant-vs-distinct test (do the MTDS and MDPS `row_count`s match on the same atom?): **0 of 607 match** — 465 have
  DIFFERENT row_counts, 142 have one side NULL. So each source row carries distinct measured coverage, not an identical
  duplicate.
- Because `source` is ALREADY excluded from the dedup key, these rows are currently kept apart **solely by
  `service_name`**. Excluding `service_name` too (Option A) would collapse all 607 defi dual-source captured pairs into
  one survivor and DROP the other source's captured record from the consolidated manifest — a real change to defi
  dual-source coverage accounting, not a cosmetic dedup.

**What this does to the recommendation:** it flips the lean from A to **B**. Option B (collapse a `captured` row only
against a NON-captured twin — the sports captured-vs-`expected_unattempted` case — while leaving captured-vs-captured
rows untouched) fixes the sports bug (165,148 TEAMS EU twins) WITHOUT touching the 607 defi captured-vs-captured
dual-source rows. Option A fixes sports but simultaneously collapses the defi dual-source pairs; whether that is
desirable (the cell is "covered", period) or lossy (downstream wants to see subgraph AND rpc coverage separately) is a
second operator judgment Option A forces and Option B avoids. **The operator ruling should now be A-vs-B with this defi
dual-source consequence explicit, not "A recommended".**

## 🟡 2026-07-14 (slot-3) — corroborating evidence from TradFi/CME, but a DIFFERENT specific splitter column

Found independently while verifying a TradFi CME `options_chain` migration
(`tradfi_cme_options_chain_legacy_layout_2026_07_10.md`): the live TradFi manifest also has non-collapsing duplicate
rows for the same real object — `date=2024-07-11 venue=CME data_type=options_chain underlying=NQU4_C20000` has 2
`capture_status=captured` rows. This is the SAME bug family (dedup key fails to collapse a legitimate re-capture of an
already-captured cell) but a **different specific splitter column** than this doc's `service_name` finding — worth
recording since it broadens the "bug class RECURS" claim (§ Blast-radius scan) to a second mechanism, not just a second
asset_group.

Full column diff between the two real rows (all other columns, including `service_name`, are identical —
`market-tick-data-service` on both):

```
written_at:        2026-07-07T09:28:32Z        | 2026-07-07T09:31:03Z
instrument_type:    "options_chain"             | None
attempted_at:       2026-07-07T09:28:32Z        | 2026-07-07T09:31:03Z
pipeline_mode:       batch_databento             | batch_massive
source:              databento                   | massive
```

`source` differing is fine per this doc's own precedent (already excluded from the dedup key,
`manifest_consolidator.py :2106-2108`). The likely real splitter is **`instrument_type`: a real, non-empty value
(`"options_chain"`) vs `None`** — NOT the NULL-vs-`""` case this doc's Proof 1 already confirmed is fixed (`f5ec2291`);
this is NULL vs a genuinely different non-empty value, which the dedup key correctly treats as distinct (that part isn't
a bug). The actual gap is upstream: the `massive`-sourced capture (older `attempted_at`, presumably an earlier/different
writer path) never stamped `instrument_type`, so it can never collapse with the later `databento` capture that did. Did
not investigate the `massive` writer path itself (out of scope for the CME migration this was found during) — flagging
for whoever picks up the operator ruling above, since Option A/B's fix design should account for this second splitter
axis too, not just `service_name`.

**Not blocking**: the CME migration this was found during lists real objects directly via bounded GCS prefix listing
(not manifest row-count arithmetic), so it is unaffected by this duplication — it correctly processed the real,
de-duplicated set of files (confirmed: this exact underlying's 2 manifest rows correspond to exactly 1 real GCS object,
which the migration found and bundled once). This DOES mean the manifest's summed `row_count` (used for scale estimates
in the CME migration's own issue doc) overstates real unique row count by roughly 2x for at least this data_type — noted
there, not re-litigated here.

## Todos (gated on the operator ruling above)

- [x] [DATA] P1. Rule-11 blast-radius DISCOVERY proof — DONE 2026-07-14 (slot-5). Ran the owed live GCS query over all
      four non-sports canonical indexes (cefi/defi/tradfi/prediction). Result: 609 fleet collapse-risk atoms, 607 of
      them defi MTDS-subgraph ✕ MDPS-rpc captured-vs-captured with distinct row_counts → Option A is NOT a no-op; lean
      shifts to Option B. Full numbers in the "🔬 Rule-11 LIVE blast-radius proof" section above. Repro:
      `scratchpad/rule11_service_name_blast_radius.py` + `rule11_defi_deepdive.py`.
- [x] [DATA] P1. **Operator ruled Option B** (2026-07-14, BLK-17603e1f) and it is IMPLEMENTED + live-verified.
      `unified_trading_library/manifest_consolidator.py` now runs a status-aware cross-`service_name` collapse
      (`_option_b_collapse_ctes`) as a bounded second-level post-pass in BOTH dedup paths (incremental + `--force`
      full-rebuild): a `captured` row supersedes a NON-captured row identical on all dedup dims EXCEPT `service_name`;
      captured-vs-captured pairs are left intact. `service_name` STAYS a dedup key, so **no writer-mirror change** was
      needed. 3 new unit tests (full-rebuild collapse, incremental collapse, dual-source preservation) + the full
      75-test consolidator suite green.

## ✅ Option B live-data verification (2026-07-14 slot-5)

Ran the exact Option B collapse over the live canonicals (`scratchpad/rule11_option_b_verify_fast.py`,
`sports_teams_twin_diag.py`):

- **Invariant — captured never dropped**: captured-row count identical before/after in both AGs (defi 3,010,913; sports
  1,648,070). Option B only ever removes NON-captured rows.
- **defi**: 35,557 cross-service conflict atoms → 35,557 non-captured rows collapse (real coverage understatement
  fixed); the 607 MTDS-subgraph ✕ MDPS-rpc dual-source captured pairs are OUTSIDE the conflict set (noncap=0) → both
  survive.
- **sports**: 1,038 non-captured rows collapse (on `odds_horizon_bucket`/`ODDS`/`FIXTURE_LINEUPS`-class cells with a
  cross-service captured sibling).
- **The plan's original 165,148 TEAMS EU twins are ALREADY GONE from the live manifest**: TEAMS now has 165,148
  `backfill-teams-61-leagues` captured + 269,727 `instruments-service` captured, and only 26,385 `instruments-service`
  `expected_unattempted` with **0** coexisting captured/EU twins under either the plan's coarse key
  (`data_type,league_id,date,venue`) OR the true dedup key. They resolved between 2026-07-13 and 2026-07-14 by other
  means (most likely an enumerator reseed that skips already-captured cells). So the ORIGINAL symptom no longer
  reproduces on TEAMS, but the **bug CLASS is live elsewhere** (the 35,557 defi + 1,038 sports rows above) — Option B
  fixes those and PREVENTS RECURRENCE for every future backfill/one-off that captures a pre-seeded cell under a distinct
  `service_name`.

Status flipped to RESOLVED for this issue's code deliverable; the fix ships with task -016.
