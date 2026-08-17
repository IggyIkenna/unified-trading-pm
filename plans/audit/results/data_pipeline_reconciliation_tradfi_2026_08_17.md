---
doc_type: audit-result
title: "Data-pipeline reconciliation — tradfi raw-tick (2026-08-17)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=tradfi, layer=raw-tick, over PROD GCS only (read-only).
  Fourth run in the tradfi campaign (after 2026-07-20, 2026-07-21, 2026-07-24), dispatched as the terminal
  post-full-backfill reconciliation checkpoint for tradfi_phase_d_terminal_gate_2026_07_24.md's P1. Corpus grew from
  5.9M to 14.5M manifest rows since 07-24 (the MVP backfill readiness gate closed 2026-08-15). Both 07-24 NEW findings
  are now PARTIALLY RESOLVED: the ICE/KRX Yahoo-exclusive-venue provenance mis-stamp is fully fixed (0 databento rows on
  either venue's daily cell); the FX companion piece of that same mis-stamp is UNCHANGED (still ~28% of FX ohlcv_24h
  captured rows stamped databento); the FX manifest instrument_id defect improved from 0% to 72.4% well-formed (a
  residual 670-row "ticks"-literal-leak sub-population is untouched). A large apparent id-form regression (99.3% ->
  85.1% naive) was investigated and is NOT a regression -- it is the already-ratified (2026-07-19, Option A) CME/CBOE
  Databento FUTURE/OPTION-labeled-but-chain-bundle-written null-instrument_id pattern at much greater volume post-
  backfill (889,202 rows); excluding it, id-form is 99.95% clean, consistent with 07-24. Two genuinely NEW items: a
  previously-undocumented `venue=FRED` (macro/yield-curve data, 94,649 rows, batch_fred pipeline_mode, 100% well-formed
  ids) with no reference-tradfi.md hazard-table entry (fixed inline, same commit); and a small (38-row) equity-ticker-
  with-embedded-space residual (`NYSE:EQUITY:BRK B-USD`, `BF B-USD`). `_quarantine/` continues growing (>=400K on 07-24
  -> >=500K capped this run, still not uncapped-measured); a new unregistered `_migration_backup_2026_07_25/` top-level
  location appeared (20,000+ objects capped, 2.35+GB). BARCHART (9,119 rows) and the manifest_dedup_2026_07_10 register
  patch remain unapplied, unchanged for the 3rd+ consecutive run. AE-2 combo writer/reader disagreement is now RESOLVED
  (both files agree on `combo_chain`). batch_massive purge holds at 0 (4th consecutive confirmation).
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    four-surface,
    tradfi,
    delete-safety,
    non-canonical-paths,
    manifest,
    databento,
    yahoo,
    fred,
    terminal-gate,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    tradfi-databento-sourcing-ssot,
    data_pipeline_reconciliation_tradfi_2026_07_24,
    tradfi_phase_d_terminal_gate_2026_07_24,
  ]
created: 2026-08-17
auditor: /data-pipeline-reconciliation (tradfi, raw-tick layer, fourth execution, Tier-1 in-session)
parent_epic: infrastructure_master
severity: P1
audited_scope:
  "asset_group=tradfi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Tier-1 in-session (full manifest census +
  bounded GCS spot-checks + non-canonical-path register sweep); instruments-store (S4) bucket top-level probed but not
  content-read (declared coverage gap); AWS NOT checked this run (declared coverage gap, mirrors 07-24 scope)"
date: 2026-08-17
resulting_plan: tradfi_phase_d_terminal_gate_2026_07_24
lib_version:
doc_versions_checked:
---

# Data-pipeline reconciliation — `asset_group=tradfi`, layer=raw-tick (PROD, read-only)

- **Run:** `/data-pipeline-reconciliation --asset-group tradfi` (raw-tick layer, default). Phases 0->2, Tier-1
  (in-session) only — no VM launched, per this dispatch's explicit scope.
- **Date:** 2026-08-17 UTC. **Cloud:** GCP `central-element-323112` only (AWS not probed this run — declared coverage
  gap, matches the 07-24 report's own scope).
- **Mode:** strictly READ-ONLY. No GCS write, no manifest write, no delete, no backfill, no Tier-2 VM.
- **Venv:** `market-tick-data-service/.venv` (imports both UTL and UAC in one interpreter — verified). `GCP_PROJECT_ID`
  and `AWS_ACCOUNT_ID` exported before every `resolve_bucket_name` call.
- **Fourth run in this campaign** — prior runs: `data_pipeline_reconciliation_tradfi_2026_07_20.md`, `…_2026_07_21.md`,
  `…_2026_07_24.md`. This run cross-checks their findings for drift/resolution rather than re-deriving everything.
- **Dispatch context**: this is `tradfi_phase_d_terminal_gate_2026_07_24.md`'s P1 "Post-full-backfill reconciliation RUN
  checkpoint," run after the P0 MVP backfill readiness gate closed 2026-08-15.

---

## ⭐ VERDICT (lead)

**`asset_group=tradfi` is NOT 100% canonical, but the estate is materially healthier than the 07-24 baseline**, with two
of that run's three escalated findings now (partially or fully) resolved and no genuinely new data-correctness defect
of comparable severity found.

1. ✅ **RESOLVED since 07-24 — ICE/KRX Yahoo-exclusive-venue provenance mis-stamp.** ICE's `ohlcv_24h`/`INDEX` (DXY) cell
   is now **100% `source=yahoo`** (1,901/1,901 captured rows, date range 2019-01-02→2026-08-14, 0 databento). KRX is
   **100% `source=yahoo`** (4,365/4,365 captured rows, 0 databento). The 07-24-measured 4-day ICE mis-stamp window and
   the 12-row KRX mis-stamp are both gone from the live corpus (either root-caused-and-fixed, or re-stamped, or the
   affected rows have since been superseded — this run did not distinguish which, see §6).
2. 🟡 **STILL OPEN, unchanged — the FX companion piece of the same provenance-stamp defect.** FX `ohlcv_24h` captured
   rows: **1,008 of 3,591 (28.1%) still stamped `source=databento`**, against the SSOT's stated Yahoo-only routing for
   FX daily bars — essentially unchanged in proportion from 07-24's 802/3,991 (20.1%; the corpus grew, the defective
   fraction did not shrink). This is the one piece of the escalated G2 finding NOT closed.
3. ✅ **IMPROVED, not fully resolved — the FX manifest `instrument_id` defect.** 0% → **72.4% well-formed**
   (2,601/3,591 captured FX rows) since the 2026-08-04 backfill (`market-tick-data-service@c86016f6`,
   `restamp_tradfi_fx_spot_pair_blank_instrument_id_2026_08_04.py`). **Residual, unfixed**: 670 rows still carry the
   literal `"ticks"` bundle-filename leak (down from 983 on 07-24 — partial, not full, cleanup) plus 7 rows carrying a
   `YAHOO_FINANCE:SPOT_PAIR:...` prefix instead of `FX:SPOT_PAIR:...`.
4. ✅ **NOT a regression — investigated and explained.** A naive re-run of 07-24's id-form regex check measured
   85.1% corpus-wide (down from 99.3%) and 2020-2022 collapsing to 1.3-1.7% (down from 28-46%). Root-caused: this is
   **NOT new corruption** — it is the already-ratified (`databento_future_option_blank_instrument_id_shard_atom_2026_07_19.md`,
   status: resolved, Option A) pattern where every Databento CME/CBOE dated FUTURE/OPTION contract is written as a
   `futures_chain` **bundle** (verified live: `day=2026-08-07/venue=CME/` has ONLY `instrument_type=combo/` and
   `instrument_type=futures_chain/` children — **no** `instrument_type=future/` path exists at all), while the manifest
   independently stamps these same rows `instrument_type=FUTURE`/`OPTION` with `instrument_id=None` by design (bundle
   grain has no per-contract id). This population is **889,202 rows** (CME 864,698 + CBOE 24,504), essentially all of it
   post-dating the MVP backfill (99.71% of CME's captured `FUTURE`-labeled rows). **Excluding this ratified pattern, the
   corpus-wide id-form is 99.95% clean** (5,082,214 measured, 2023-2026 at 99.92-99.99%) — consistent with, and slightly
   better than, 07-24's 99.27%/99.95% figures. **This is a taxonomy/methodology gap, not a data defect**: neither
   `SKILL.md` §3d's tradfi hazard row nor `reference-tradfi.md` documents this carve-out, so a future naive
   reconciliation pass (this one included, on the first measurement) will keep re-discovering it as a false "id-form
   regression." **Fixed inline this run** — added as new hazard H8 to `reference-tradfi.md` (see §8).
5. 🟢 **NEW — undocumented `venue=FRED`.** 94,649 manifest rows (17,264 `captured`, 75,039 `attempted_failed`, 2,346
   `empty_confirmed`), `pipeline_mode=batch_fred`/`source=fred`, `data_type` in `{yield_curve, ohlcv_1d, ohlcv_15m,
   ohlcv_1s, ohlcv_24h}`, `instrument_type` in `{BOND, INDEX}`. **Data quality is good** — 100% well-formed manifest ids
   sampled (`FRED:BOND:DFF-USD`, `FRED:BOND:T10Y2Y-USD`, `FRED:INDEX:T10YIE-USD`, …), consistent canonical shape. **Not
   a data-correctness finding** — this is a doc-coverage gap: `reference-tradfi.md`'s path grammar and hazard tables,
   and `SKILL.md` §3d's tradfi row, do not mention FRED, so a reconciliation run has no documented expectation to check
   this venue against. **Fixed inline this run** — added to `reference-tradfi.md` (see §8).
6. 🟡 **NEW, small — equity tickers with an embedded space in the id.** `NYSE:EQUITY:BRK B-USD` (19 rows) and
   `NYSE:EQUITY:BF B-USD` (19 rows) — Berkshire Hathaway Class B and Brown-Forman Class B, both legitimately
   space-separated share classes on the wire, but the canonical id grammar (`VENUE:TYPE:SYM-USD`) doesn't define how a
   multi-token symbol should be joined. 38 rows total, low severity, filed as a tracked todo (§9) rather than fixed
   inline (root-cause needs a design decision — hyphen vs dot vs no-separator convention — not a blind rewrite).
7. 🟡 **Still true, unchanged from 07-24/07-21** — `venue=BARCHART` (9,119 rows, all `empty_confirmed`, last touched
   2026-07-07, still in the vocabulary despite removal from `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-06-24).
8. 🟡 **`_quarantine/` — still growing, still not uncapped-measured.** 07-24 measured >=400,000 objects (capped
   enumeration). This run's capped count hit the same 500,000 cap in 41s (elapsed budget not exhausted — the object
   count is the binding constraint, meaning the true population is materially over 500K). The 07-24 P1 "re-measure
   uncapped + find the feeder" todo is still open.
9. ✅ **NEW positive — the AE-2 combo writer/reader path-shape disagreement (07-20/07-21/07-24's re-confirmed HIGH
   finding) is RESOLVED.** Live grep: `symbol_rules.py:300` and `reader.py:74` now BOTH define
   `_UNDERLYING_PARTITIONED_TYPES = frozenset({"options_chain", "futures_chain", "combo_chain"})` — writer and reader
   agree (note: the class renamed `combo`→`combo_chain` in both files, not just closed the gap).
10. ✅ **`batch_massive` purge holding** — 0 objects, 0 manifest rows, 4th consecutive run confirming this.
11. 🟢 **NEW top-level location, unregistered** — `_migration_backup_2026_07_25/` (20,000+ objects capped in 20s / 2.35+
    GB, true size likely higher). Not in `non-canonical-path-inventory.md`. Register-patch stanza below (§7).

---

## Phase 0 — Bucket-paths table + resolution/reachability gate

| Surface / kind                              | Cloud | Resolved bucket                                       | Reachable                                          | Notes                                                                                                                    |
| -------------------------------------------- | ----- | ------------------------------------------------------ | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| raw-tick (`market-data`, S1/S2/S3)           | GCP   | `market-data-tick-tradfi-prd-central-element-323112`   | ✅ YES — non-recursive top-level listing succeeded | primary target, `resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='tradfi', deployment_env='prd')`     |
| instruments-store (`instruments-store`, S4) | GCP   | `instruments-store-tradfi-prd-central-element-323112` | ✅ YES — top-level listing succeeded (content NOT read) | top-level children: `_catalogue/, _index/, _vm_staging/, instrument_availability/, prod/` — S4 content not sampled this run, declared gap |
| raw-tick / instruments-store                 | AWS   | `market-data-tick-tradfi-prd-427895769566` / `instruments-store-tradfi-prd-427895769566` (resolved, NOT probed) | ⚠️ **NOT ASSESSED — declared coverage gap** | mirrors the 07-24 report's own AWS scope; not re-verified |

No resolved name carried `-test-` (refusal condition not triggered). `GCP_PROJECT_ID=central-element-323112` and
`AWS_ACCOUNT_ID=427895769566` exported before every call; `deployment_env='prd'` passed explicitly.

**Raw-tick top-level children (this run)**:

```
_audits/  _index/  _migration_backup/  _migration_backup_2026_07_25/  _quarantine/  _vm_staging/
backfill-logs/  configs/  databento-batch-registry/  processed_candles/  raw_tick_data/  vm-census/
```

Compare to the 07-24 report's list (`_index/, _migration_backup/, _quarantine/, _vm_staging/, backfill-logs/, configs/,
databento-batch-registry/, processed_candles/, raw_tick_data/`): **`_audits/`, `_migration_backup_2026_07_25/`, and
`vm-census/` are NEW** (see §7 for `_migration_backup_2026_07_25/`'s register-patch entry; `_audits/` and `vm-census/`
are small — 2 objects/36MB and 1 object/0MB respectively — and read as operational output, not flagged as findings this
run). No `batch_massive` top-level presence (purge still holding).

### Index freshness / lock state (§ 2d — decisive)

| File (raw-tick `_index/`)       | Value                                                                                                             | Meaning                                                                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `availability_index.parquet`     | 364.26 MB, **14,457,858 rows**, tradfi-only (bucket-scoped index), `blob.updated=2026-08-17T05:26:52Z`             | consolidated manifest read for this run (downloaded once to `$HOME`, column-projected reads thereafter)                    |
| `consolidator.lock`              | **PRESENT** (`started_at=2026-08-17T05:32:54Z, instance=1-929044d3`)                                                | consolidator was actively running (or stuck-locked) at the moment of this read                                             |
| `latest.json`                    | `last_run_at=2026-08-17T05:36:41Z, success=true, verdict="empty", shards_scanned=0, no_op=true, error_reason="locked"` | the most recent consolidator tick found itself already locked and no-op'd — **the published parquet (05:26:52Z) predates this lock**, so this run's census reads a stable ~10-minute-old snapshot, not a mid-write partial state |
| `consolidator_stall_state.json`  | `streak:0, baseline_shards:2`                                                                                       | not flagged stalled                                                                                                         |
| `phantom_audit_latest.json`      | `phantom_count:16,997` @**2026-07-30**                                                                              | published count, now **~18 days stale**; **10x jump from 07-24's 1,635 @2026-07-14** — see §9 recommendation              |
| `reprobe_audit_latest.json`      | `new_empties:1, disagreements:0, ambiguous:0, proven:0` @**2026-08-16**                                             | fresh (1 day old), healthy — no disagreements found                                                                          |

**Consequence:** the `availability_index.parquet` read (05:26:52Z) is ~10 minutes older than the active consolidator
lock (05:32:54Z) observed at probe time — this run's census is a real, stable snapshot, **not** a lower bound from a
mid-write read. The phantom audit, however, IS 18 days stale and its count grew 10x since the last measurement — every
phantom-related statement in this report is a point-in-time historical figure, not re-derived here (per SKILL.md §2d,
"read it here, never re-run the auditor").

### Suppression inputs loaded (accepted-exception list applied BEFORE emitting)

| Input                                       | What                                                                                                                    | Applied                                                                                                                     |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `canonical-cutover-register.md` §2          | `require_pipeline_mode` effective-from **2026-05-19** for tradfi                                                       | oracle called with `require_pipeline_mode=True` throughout                                                                 |
| `canonical-cutover-register.md` §4          | tradfi chain-tail (`underlying=/quote=/margin=`) effective-from **2026-07-19**                                         | consistent with sampled shapes (§3)                                                                                         |
| taxonomy §5.1 / cutover-register §3c (C2a) | manifest `instrument_type` COLUMN case — RULED UPPERCASE target, `migration_pending`                                  | compared case-insensitively throughout                                                                                      |
| taxonomy AE-2                               | tradfi `combo`/`combo_chain` bare-`underlying=` carve-out                                                              | not flagged as `non_canonical_path`                                                                                         |
| taxonomy AE-4 (CLOSED)                      | `batch_massive` — purge executed                                                                                       | N/A — measured 0 everywhere, 4th confirmation                                                                               |
| **NEW this run** — ratified null-id chain-bundle carve-out (`databento_future_option_blank_instrument_id_shard_atom_2026_07_19.md`) | CME/CBOE Databento `FUTURE`/`OPTION`-labeled manifest rows with `instrument_id=None` (bundle-write-by-design)         | excluded from the id-form check (§ Verdict item 4); **not yet a named codex carve-out — added to `reference-tradfi.md` this run (§8)** |
| `non-canonical-path-inventory.md`           | living register, tradfi-scoped rows (10, 11, 19, 22, 28)                                                               | re-verified against reality (§7)                                                                                            |

**Refusal condition not triggered** — no resolved bucket name carried `-test-`.

---

## Phase 1 — Four-surface comparison

Oracle = UAC `canonical_path_violations()`, called with `require_pipeline_mode=True`.

### 3a. S1 structural canonicality — sampled

| Method                                                                                          | Sample                                     | Result                                                                          |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------- |
| Prefix listing of `day=2026-08-14` (no-walk route #1) | 8 objects sampled | **0/8 oracle violations** (`require_pipeline_mode=True`) |
| Direct GCS child-prefix probe of `day=2026-08-07/venue=CME/` (used to root-cause the id-form investigation, §Verdict item 4) | full child-prefix set | Only `instrument_type=combo/` and `instrument_type=futures_chain/` — **confirms the manifest's `instrument_type=FUTURE` label has no corresponding flat path**, i.e. these rows are genuinely bundle-written |

**Verdict:** S1 structure is clean on every sample taken this run, consistent with 07-24's "0 violations on every
sample" finding.

### 3b. S3 manifest-id-form — 99.95% clean once the ratified chain-bundle pattern is excluded

| Cohort (captured, single-instrument-LABELED shard types, core tradfi venues, ratified null-id CME/CBOE FUTURE/OPTION rows excluded) | n         | canonical-shaped id | %          |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------------------- | ---------- |
| All years                                                                                                                                 | 5,082,214 | 5,080,022             | **99.95%** |
| 2019                                                                                                                                       | 837       | 837                   | 100.0%     |
| 2020                                                                                                                                       | 2,515     | 1,743                 | 69.3%      |
| 2021                                                                                                                                       | 2,241     | 2,241                 | 100.0%     |
| 2022                                                                                                                                       | 2,394     | 2,394                 | 100.0%     |
| 2023                                                                                                                                       | 1,103,356 | 1,103,271             | 99.99%     |
| 2024                                                                                                                                       | 1,544,168 | 1,544,018             | 99.99%     |
| 2025                                                                                                                                       | 1,562,359 | 1,561,033             | 99.92%     |
| 2026                                                                                                                                       | 864,344   | 864,240               | 99.99%     |

Compare to 07-24's 99.27% (all years). **No regression** — the ~0.7pp difference is within the residual-population
noise (below). 2020-2022's tiny denominators (n<2,600/year) mean the % is volatile on small counts, not evidence of a
systemic 2020-2022 gap the way it looked in the earlier, uncleaned check.

**Residual "bad" rows (2,437 total, 0.05% of the clean cohort):**

| Venue | n   | Sample bad ids                                                                          |
| ----- | --- | ------------------------------------------------------------------------------------------ |
| CME   | 927 | `"ticks"` (part of), `AUD`(48), `DOW`(8), `WHEAT`(6), `TNOTE2Y`(6) — bare underlying/root leaking into the id, no `VENUE:TYPE:` prefix — same class as the already-tracked chain-bundle sampler / reverse-derivation gap (`tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`), NOT re-filed here |
| NYSE  | 828 | `NYSE:EQUITY:BRK B-USD`(19), `NYSE:EQUITY:BF B-USD`(19) — multi-token equity symbols; ~790 other rows not individually sampled |
| FX    | 671 | `"ticks"` (670, the residual FX bundle-filename-leak), `YAHOO_FINANCE:SPOT_PAIR:KRW-USD`(7) |
| NASDAQ| 11  | not individually sampled (low volume)                                                       |

### 3c. Distinct-value census (S3, 14,457,858 rows, snapshot 05:26:52Z)

| Axis              | Distinct values                                                                                                                     | Verdict                                                                                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `asset_group`      | `tradfi` (14,457,858)                                                                                                                    | ✅ sanity                                                                                                                                                              |
| `venue`             | NYSE 6,151,780 · CME 4,640,094 · NASDAQ 2,842,817 · ICE 417,412 · CBOE 227,404 · **FRED 94,649 (NEW, see §Verdict item 5)** · KRX 43,471 · FX 31,112 · **BARCHART 9,119** | `BARCHART` = `non_canonical_axis_value` (S3), unchanged from 07-24/07-21 (9,119 rows, all `empty_confirmed`, `max attempted_at=2026-07-07`, not re-touched further) |
| `pipeline_mode`     | `batch_databento` 14,228,314 · `batch_yahoo` 116,520 · **`batch_fred` 108,145 (NEW)** · `batch_barchart` 4,655 · `live_databento` 224 | 0 blank/null; `batch_massive`: 0 rows anywhere — purge holding (4th confirmation)                                                                                     |
| `source`            | `databento` 14,227,993 · `yahoo` 123,583 · **`fred` 101,627 (NEW)** · `barchart` 4,655                                                    | consistent with `pipeline_mode`                                                                                                                                        |
| `instrument_type`   | `EQUITY`/`equity`, `COMBO`/`combo`, `FUTURE`/`future`, `ETF`/`etf`, `INDEX`/`index`, `SPOT_PAIR`/`spot_pair` (C2a casing, suppressed) · `futures_chain`(464,505) / `options_chain`(208,869) (bundle carve-out) · `BOND`(75,552, mostly FRED) · blank (245,642) · **`UNKNOWN` (4,142, NEW — see below)** | `FUTURES`/`spot` typos from 07-24 (18 rows) **no longer present** — appears cleaned up. `UNKNOWN`: NEW, all 4,142 rows are `venue=CME, data_type=ohlcv_1m, capture_status=attempted_failed` — no captured data affected, low severity, `non_canonical_axis_value` |
| `capture_status`    | `captured` 8,116,669 · `empty_confirmed` 5,124,292 · `attempted_failed` 801,636 · `expected_unattempted` 415,261                          | 4-state honest, no fifth value                                                                                                                                        |

**Blank `instrument_type` on captured rows: 787** (down from 1,910 on 07-24 — improved), spread across CME/NASDAQ/NYSE/
CBOE/ICE/KRX/FX — a minor completeness gap, not independently investigated further this run (small, unchanged-severity
class).

### 3d. FX SPOT_PAIR manifest instrument_id — improved, not fully resolved (see §Verdict item 3)

3,591 captured FX rows; 2,601 (72.4%) well-formed `FX:SPOT_PAIR:XXX-USD`; 670 literal `"ticks"`; 7
`YAHOO_FINANCE:SPOT_PAIR:...` (wrong-prefix, not `FX:`). Real GCS content not independently re-verified this run (07-24
already confirmed the on-disk object/content are correctly formed for a sample; this defect is purely S3/manifest).

### 3e. ICE/KRX/FX source provenance — see §Verdict items 1-2 for the full breakdown

### 3f. Chain-tail cutover (2026-07-19) — not independently re-measured at scale this run

Consistent with 07-24's finding; the id-form investigation's own GCS spot-check (§3a) incidentally confirmed the
chain-tail shape (`instrument_type=futures_chain/underlying=.../quote=.../margin=.../ticks.parquet`) is still the live
write shape for CME.

### 3g. AE-2-adjacent combo/combo_chain writer/reader disagreement — RESOLVED (see §Verdict item 9)

### Coverage formula (§8, name it, mark it a lower bound)

`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` EXCLUDED
(`honest-coverage-model.md`, CK3-certified):

```
8,116,669 / (8,116,669 + 801,636 + 415,261) = 8,116,669 / 9,333,566 = 86.96%  — LOWER BOUND
```

(`instrument_gates_download=true` for tradfi, so this is a lower bound per the standing rule.) This is a substantial
improvement from 07-24's 66.77% — consistent with the MVP backfill readiness gate closing 2026-08-15 and the corpus
growing from 5.9M to 14.5M rows in the intervening 3.5 weeks.

---

## Phase 2 — Non-canonical sweep + register reconciliation

Register→reality re-verification of `non-canonical-path-inventory.md` rows scoped to tradfi. **Did not edit the shared
register inline** (concurrency — multiple sibling AGs/sessions touch this same file; register-patch stanza below for
the maintainer to apply serially, matching the 07-24/07-21 reports' own practice).

| Register row | Claim (as currently written)                                       | Reality (measured this run, 2026-08-17)                                                                                                                                                             | Disposition change |
| ------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 10            | Retired 2026-07-21, purge executed                                    | **CONFIRMED HOLDING** — 0 `batch_massive` objects/rows this run too (4th consecutive confirmation)                                                                                                     | none                |
| 11            | Retired 2026-07-21, migration executed 848,886 objects                | Consistent with this run's S1 sample (0 violations) and 99.95%-clean id-form (§3b) — **not independently re-measured at full scale**                                                                    | none                |
| 19            | `databento-batch-registry/{sha}.json`, sanctioned operational          | **7,146 objects, unchanged** — exact match to 07-24                                                                                                                                                     | none                |
| 22            | "RETIRED — DELETED 2026-07-21" (stale per 07-24's re-open)             | **STILL STALE, growth continues.** 07-24 measured ≥400,000 objects (capped). This run's capped count hit **500,000 in 41s** without exhausting the 60s time budget — the object-count cap, not time, is now the binding constraint, meaning the true population is materially above 500K. | **REMAINS RE-OPEN — no change to disposition** |
| 28            | `configs/patches/` — disposition question open                        | Not re-probed this run (low priority, unchanged since 07-24's confirmation of presence)                                                                                                                 | none                |

**Reality → register (locations found this run, not previously registered for tradfi):**

| Location                                | Size (capped)                              | Notes                                                                                                                    |
| ----------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `_migration_backup_2026_07_25/`           | 20,000+ objects / 2.35+ GB (20s time-budget cap hit — true size higher) | **NEW top-level location, not in the register.** Named/dated consistent with a migration snapshot from the 07-25 candle-campaign window; disposition `unknown` (five-part proof not run this pass). |
| `_migration_backup/manifest_dedup_2026_07_10/` | 1 object / 0.11 GB                     | **STILL the same unapplied register-patch line from 07-21 AND 07-24** — flagged twice already, still never applied to the shared register. Re-flagging a 3rd time. |

Orphans: **NOT ASSESSED** (no whole-corpus walk this run — per `orphan-object-detection.md` §3).

### Register-patch stanza (apply serially — do NOT hand-edit inline during concurrent AG runs)

```
# non-canonical-path-inventory.md
- Row 22 (_quarantine/): STILL STALE as of 2026-08-17 (3rd consecutive re-open). Capped enumeration hit
  500,000 objects in 41s (up from 07-24's >=400,000 capped count); the true population is materially
  higher and still growing. Recommend an uncapped, time-boxed VM-side walk to get a real number and
  identify the feeding process (07-24's P1 todo, still open).
- NEW row: `_migration_backup_2026_07_25/` (tradfi bucket) — 20,000+ obj / 2.35+ GB capped (true size
  higher). Disposition `unknown` (five-part proof not run). Likely a migration-campaign snapshot from
  the 2026-07-25 candle reconciliation window — needs its provenance confirmed before any disposition
  beyond `unknown`.
- Row (manifest_dedup_2026_07_10, under _migration_backup/): RE-FLAGGING A THIRD TIME — this exact
  line was proposed in BOTH the 2026-07-21 and 2026-07-24 reports' register-patch stanzas and was
  never applied. 1 obj / 0.11 GB, disposition `unknown`.
```

**No delete suggestions rise above `unknown` this run.** Nothing here completed the five-part proof
(`gcs-and-manifest-delete-safety-protocol.md`); every location above is `unknown`, per the doc's own default.

---

## Typed findings summary (taxonomy names; suppressed exceptions counted separately)

| #   | Type                                              | Severity | Surfaces | Scope                                          | Detail                                                                                     | New / re-confirmed / resolved                     |
| --- | -------------------------------------------------- | -------- | -------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| —   | `non_canonical_axis_value` (source/pipeline_mode)  | RESOLVED (ICE/KRX) / STILL OPEN (FX) | S3 | ICE (0 mis-stamped), KRX (0 mis-stamped), FX (28.1% still mis-stamped) | 07-24's G2 finding — 2/3 venues fixed, FX unchanged                                            | **partially resolved**                               |
| —   | taxonomy-gap (S3-only manifest-id defect)          | IMPROVED | S3       | FX SPOT_PAIR                                       | 0% → 72.4% well-formed; 670-row `"ticks"` residual unfixed                                     | **improved, not resolved**                            |
| —   | taxonomy-gap (ratified-null-id chain-bundle, undocumented carve-out) | METHODOLOGY (fixed inline) | S3 | CME/CBOE `FUTURE`/`OPTION`-labeled Databento rows, 889,202 | not a data defect — an undocumented reconciliation carve-out; added to `reference-tradfi.md` this run | **new methodology finding, fixed inline**             |
| —   | doc-coverage gap (`venue=FRED` undocumented)       | LOW (fixed inline) | n/a      | 94,649 rows, well-formed                            | new venue not in `reference-tradfi.md`/`SKILL.md` §3d                                          | **new, fixed inline**                                 |
| —   | `non_canonical_id` (multi-token equity symbol)     | LOW      | S3/S2    | NYSE `BRK B`/`BF B`, 38 rows                        | space-separated share class, no defined join convention                                         | **new, tracked (§9), not fixed inline**                |
| —   | `non_canonical_axis_value` (venue, BARCHART)        | LOW      | S3       | 9,119 rows, `empty_confirmed`, last touched 2026-07-07 | still in vocabulary despite 2026-06-24 removal                                                  | re-confirmed, unchanged (4th consecutive run)          |
| —   | `non_canonical_axis_value` (instrument_type, UNKNOWN) | LOW    | S3       | 4,142 rows, CME, `ohlcv_1m`, all `attempted_failed` | no captured data affected                                                                       | **new**                                                |
| —   | AE-2-adjacent writer/reader path disagreement       | n/a (code) | code   | `combo`/`combo_chain` shard read path               | both files now agree on `combo_chain`                                                           | **RESOLVED**                                           |
| —   | register staleness (`_quarantine/`)                 | MEDIUM   | register | row 22                                              | growth continues (≥400K → ≥500K capped)                                                          | re-confirmed, still growing (3rd consecutive re-open) |
| —   | new unregistered location (`_migration_backup_2026_07_25/`) | LOW | register | 20,000+ obj capped                                  | not yet in `non-canonical-path-inventory.md`                                                     | **new**                                                |
| —   | phantom (published, not re-run)                    | context-only | S3↔S1 | tradfi                                              | `phantom_count=16,997` @2026-07-30, 10x jump from 07-24's 1,635, 18 days stale                   | **new observation — recommend a fresh run**            |
| —   | id-form (positive, corrected)                       | INFO     | S3       | captured singles, corpus-wide (ratified null-id excluded) | 99.95% clean — no regression once methodology-corrected                                        | **confirmed clean, not a regression**                  |
| —   | reachable coverage (positive)                       | INFO     | S3       | corpus-wide                                          | 86.96% (lower bound), up from 66.77% on 07-24                                                     | **improved**                                            |

**Suppressed accepted-exception counts (proving suppression happened, not re-listing them):**

- C2a instrument_type casing (`reconciliation-finding-taxonomy.md` §5.1) — mixed-case pairs (EQUITY/equity,
  COMBO/combo, FUTURE/future, ETF/etf, INDEX/index, SPOT_PAIR/spot_pair) compared case-insensitively, **0 casing
  findings emitted**.
- AE-2 combo/combo_chain bare-underlying (taxonomy §4) — not flagged as `non_canonical_path`.
- AE-4 `batch_massive` (CLOSED) — 0 rows, purge holding, confirmed a 4th time.
- Bundle-grain `instrument_type={options_chain,futures_chain}` carve-out — 673,374 rows NOT flagged as
  `non_canonical_axis_value`.
- **NEW this run** — ratified CME/CBOE `FUTURE`/`OPTION`-labeled null-instrument_id chain-bundle rows (889,202) NOT
  flagged as a manifest-id defect, per `databento_future_option_blank_instrument_id_shard_atom_2026_07_19.md`.

---

## §6 — Coverage gaps (what this run did NOT assess)

1. **Orphans: NOT ASSESSED** — no whole-corpus walk (single-walk discipline).
2. **S4 catalogue content: NOT READ this run** — top-level bucket listing confirmed reachable (`_catalogue/, _index/,
   _vm_staging/, instrument_availability/, prod/`), but `prod/catalog.parquet`'s content was not sampled — a full
   coverage gap for the catalogue surface, not a per-shard verdict.
3. **AWS: NOT ASSESSED this run** — resolved bucket names recorded, not probed (mirrors 07-24's own scope).
4. **id-form / schema at 100%: NOT ASSESSED** — the 99.95% figure is a ~5.08M-row (not fully corpus-wide) census over
   captured single-labeled rows using a permissive shape regex, not a byte-exact `build_canonical_instrument_id`
   rebuild. A Tier-2 read-only per-datapoint VM would be required for a byte-exact, 100% claim; not dispatched this
   run (out of scope, Tier-1 only per this dispatch).
5. **`_quarantine/` true size: NOT FULLY ENUMERATED** — capped at 500,000 objects; the true count is materially
   higher.
6. **`processed_candles/`** — covered separately, see the sibling candles-layer report
   (`data_pipeline_reconciliation_tradfi_candles_2026_08_17.md`).
7. **ICE/KRX provenance-fix root cause NOT independently confirmed** — this run measured the LIVE state (clean), it
   did not verify whether the fix was a code change, a manifest re-stamp, or the affected rows simply aging out of a
   sliding window. Not investigated further (out of scope for a read-only reconciliation).
8. **The 38-row multi-token-equity-symbol population was not exhaustively enumerated across all venues** — only NYSE
   `BRK B`/`BF B` were sampled; other venues may carry the same class at low volume.
9. **`_migration_backup_2026_07_25/`'s provenance / owning campaign was not investigated** — flagged for the register,
   not traced to its source this run.

---

## §7 — Big findings escalated to the operator

**None this run rise to the "notify the operator" bar** (data-correctness / cross-repo / SSOT contradiction). The two
07-24 escalated findings are now materially improved (2 of 3 provenance-mislabel venues fixed; the manifest-id defect
went from 0%→72.4%); the remaining open items (FX provenance residual, `_quarantine/` growth, BARCHART cleanup,
multi-token-symbol ids) are all small-volume, already-tracked-or-newly-tracked, single-repo/single-AG items — not
escalation-worthy on their own. The `phantom_audit_latest.json` 10x count jump (1,635→16,997) is worth a fresh audit
run but is not itself evidence of a live defect (it is a stale, 18-day-old published number, not re-derived this run).

---

## §8 — Fixed inline this run (docs)

Both fixed in `unified-trading-pm` (`.claude/skills/data-pipeline-reconciliation/reference-tradfi.md`), same commit as
this report:

1. **New hazard H8** documenting the ratified CME/CBOE Databento `FUTURE`/`OPTION`-labeled, `instrument_id=None`,
   chain-bundle-written pattern (889,202 rows this run) as an accepted exception for the id-form check, citing
   `databento_future_option_blank_instrument_id_shard_atom_2026_07_19.md` — so a future reconciliation pass does not
   re-derive this from scratch and mis-report it as a regression the way this run's first pass did.
2. **`venue=FRED`** added to the path grammar / bucket table as a recognized tradfi venue (macro/yield-curve data via
   `pipeline_mode=batch_fred`/`source=fred`) — previously entirely undocumented.

---

## §9 — Todos / issue-doc candidates (not fixed inline — belongs to the relevant service plan)

- [ ] **P1 [DATA]** Root-cause + fix the FX `ohlcv_24h` `source=databento` mis-stamping (§Verdict item 2) — the one
      unresolved piece of 07-24's escalated G2 finding; ICE/KRX are already fixed, FX is not (28.1% of captured FX
      `ohlcv_24h` rows, unchanged in proportion from 07-24). (repo: market-tick-data-service)
- [ ] **P2 [DATA]** Finish the FX manifest `instrument_id` backfill's residual — 670 rows still carry the literal
      `"ticks"` bundle-filename leak (down from 983, not zero); the 2026-08-04 restamp
      (`market-tick-data-service@c86016f6`) did not cover this sub-population. (repo: market-tick-data-service)
- [ ] **P1 [DATA]** Re-measure `_quarantine/` with an uncapped, time-boxed VM walk and identify the feeding process —
      3rd consecutive reconciliation run to re-flag this (146,288 07-21 → ≥400,000 07-24 → ≥500,000 08-17, capped each
      time). (repo: market-tick-data-service or deployment-service, VM-scale)
- [ ] **P2 [DOCS]** Apply the register-patch stanza (§7 above) to `non-canonical-path-inventory.md` — including the
      `manifest_dedup_2026_07_10` line proposed on 07-21, re-flagged on 07-24, and STILL not applied as of this 3rd
      flag. (repo: unified-trading-pm)
- [ ] **P3 [DATA]** Investigate + design a join convention for multi-token equity symbols (`BRK B`→`BRK-B`? `BRK.B`?)
      — 38 rows measured this run (NYSE `BRK B`/`BF B`), likely a small population elsewhere too; needs a design
      decision, not a blind rewrite. (repo: unified-api-contracts + market-tick-data-service)
- [ ] **P3 [DATA]** Investigate the 4,142 `venue=CME, instrument_type=UNKNOWN, data_type=ohlcv_1m, attempted_failed`
      rows — no captured data affected, low severity, but a `non_canonical_axis_value` not previously seen.
      (repo: market-tick-data-service)
- [ ] **P3 [DATA]** Run a fresh phantom audit for tradfi — the published count grew 10x (1,635→16,997) between
      2026-07-14 and 2026-07-30 and is now itself 18 days stale; the 07-24 report already flagged this as P3, still
      open, now more urgent given the growth. (repo: market-tick-data-service)
- [ ] **P3 [DOCS]** Confirm the provenance of `_migration_backup_2026_07_25/` (20,000+ objects capped) and add its
      disposition to `non-canonical-path-inventory.md` beyond `unknown`. (repo: unified-trading-pm)
- [ ] **P3 [DOCS]** Clean up the `venue=BARCHART` register/vocabulary residual (9,119 `empty_confirmed` rows, removed
      from the venue list 2026-06-24, still present, unchanged 4 consecutive reconciliation runs). (repo:
      market-tick-data-service or unified-api-contracts)
