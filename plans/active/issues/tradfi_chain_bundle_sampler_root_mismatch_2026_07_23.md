---
doc_type: issue
title:
  "TradFi chain-bundle (futures_chain/options_chain) Phase-D smoke failures are NOT a day-selection bug — they're a
  canonical-root vs raw-Databento-symbol sampler mismatch, plus a distinct garbage-`underlying` manifest bug, plus a
  disagreeing-SSOT finding"
summary: >-
  The Phase-D full-surface MTDS run's 3 chain-bundle failures (CME futures_chain/options_chain, ICE futures_chain)
  looked like a day-selection problem (`--auto-day` substituted `2024-03-25`, no parquet found there) but direct GCS
  verification proved BOTH the auto-picked day and a known-good day (2023-06-08) have real backing objects for CME
  futures_chain/AUD. The real cause: `sample_live_instrument()` samples the manifest's `underlying` column, which the
  recent tradfi-manifest-cas migration canonicalized to English product names (AUD, GOLD, SP500...), and passes that
  straight to `--instrument-ids` — but CME/GLBX.MDP3's curated Databento symbol list uses raw exchange codes (6A, GC,
  ES...). The live run.log proves it: `instrument_ids filter ['AUD'] matched nothing ... 154 curated symbol(s) available
  (['6A','6A.FUT',...])`. Day-pinning does NOT fix this — it is day-independent and will recur for nearly every CME
  options_chain/futures_chain underlying now that canonicalization has landed broadly (live census: AUD, COPPER,
  TNOTE2Y, EUR, TBOND, RUSSELL2000, CRUDE, GBP, SP500, GOLD all hit the same mismatch). ICE re-tested clean (its
  Databento dataset curates by product name, no mismatch there) — this is CME/GLBX.MDP3-specific, not universal.
  Separately, CME options_chain's skip leg sampled `underlying=TICKS` — confirmed via direct manifest query: 29 real
  `capture_status=captured` rows dated 2025-11 through 2026-01-30 carry this garbage value (a leaked path
  segment/filename, not a product root), sitting alongside other known-garbage values (`CC__FMZ0023!` etc.) already
  named in the chain-manifest recovery script's own docstring but never filtered from sampling. FIXED 2026-07-23
  (mtds@98a81c26): the sampler now skips a garbage `underlying` (via `is_recognized_tradfi_underlying`,
  TRADFI-chain-only) in favor of a recognized product root when one exists in the matching set. NOT fixed: the
  canonical-root -> raw-Databento-symbol reverse translation — this needs a real design decision (see § open question)
  because `EXCHANGE_CODE_TO_NAME` is NOT cleanly invertible (multiple raw codes -> one canonical name, e.g. `6A`+`M6A`
  both -> `AUD`) AND two DIFFERENT UAC files define `EXCHANGE_CODE_TO_NAME` with disagreeing values for the same codes
  (`tradfi_symbology.py`'s `HO`->`HEATINGOIL` vs `tradfi_instrument_universe.py`'s `HO`->`HEATING_OIL`; `ZS`->`SOYBEAN`
  vs `SOYBEANS`) — an SSOT contradiction that predates this investigation and should be resolved before anyone builds a
  reverse mapping off either one.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags:
  [
    data-correctness,
    tradfi,
    databento,
    chain-bundle,
    canonical-id,
    sampler-bug,
    ssot-contradiction,
    operator-notify,
    phase-d-smoke,
  ]
related: [tradfi_consolidated_closeout_2026_07_18]
created: 2026-07-23
priority: P1
parent_epic: infrastructure_master
source:
  "Operator-directed follow-up investigation, 2026-07-23 continuation of tradfi_consolidated_closeout_2026_07_18's Phase
  D full-surface run: 'investigate further, do we have action items/issues/plans around this, or can't we just point the
  force leg to a day we do have data.' Root-caused via a general-purpose research agent given full context (JSON
  evidence + the recovery script's own COCOA/AUD-on-2023-06-08 finding) — day-pinning does NOT fix it, per the agent's
  direct GCS/run.log/manifest verification."
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
  "mtds@98a81c26 fixes the garbage-underlying (TICKS) half only. The canonical-root -> raw-symbol reverse-translation
  half and the EXCHANGE_CODE_TO_NAME SSOT-contradiction finding remain open — see § open question."
---

# TradFi chain-bundle sampler: canonical-root mismatch, garbage-underlying data, and a disagreeing SSOT

> **🟡 OPERATOR-NOTIFY (SSOT-contradiction sub-finding).** Two files in `unified-api-contracts` both define a module-
> level `EXCHANGE_CODE_TO_NAME: dict[str, str]` and disagree on at least two entries:
> `unified_api_contracts/registry/tradfi_instrument_universe.py:552` has `"HO": "HEATING_OIL"` / `"NG": "NATGAS"` while
> `unified_api_contracts/registry/tradfi_symbology.py:166` has `"HO": "HEATINGOIL"` (no underscore) / `"NG": "NATGAS"` —
> spot-checked, not exhaustively diffed. Whichever one is authoritative should absorb the other (or both should delegate
> to one real SSOT) before either is used to build a reverse mapping, or a reverse translation will silently pick the
> wrong dict's convention depending on which import path a caller happens to use.

## 1. This is NOT a day-selection bug

The Phase-D full-surface run's 3 chain-bundle failures all showed `--auto-day` substituting a historical day
(`2024-03-25`) with `no_parquet_under` at that day. The obvious read is "auto-day picked a bad day, pin it to a known-
good one instead" (2023-06-08, per the chain-manifest recovery script's own docstring: _"Sample evidence: COCOA/AUD on
2023-06-08 confirmed real GCS data, zero manifest registration"_). **Direct GCS verification disproves this**:

```
gs://.../day=2024-03-25/.../venue=CME/instrument_type=futures_chain/data_type=futures_chain/underlying=AUD/quote=USD/margin=linear/ticks.parquet  → EXISTS
gs://.../day=2023-06-08/.../venue=CME/instrument_type=futures_chain/data_type=futures_chain/underlying=AUD/quote=USD/margin=linear/ticks.parquet  → EXISTS
```

Both days have real backing objects. `--auto-day`'s selection (`_captured_days_by_cell()` / `_resolve_shard_day()`,
`market-tick-data-service/scripts/pipeline_e2e_check.py` L892-944) is working correctly — it reads the PROD
`availability_index` filtered to `capture_status==CAPTURED` and picks the most recent qualifying day, with zero GCS
cross-check (pure manifest trust, which is fine — the manifest row is real).

## 2. The real cause: canonical-root vs raw-Databento-symbol mismatch

`sample_live_instrument()` (L1071-1074 pre-fix, now guarded per § 3) samples the manifest's `underlying` column verbatim
for bundled-chain shards and passes it straight to `--instrument-ids`. The recent tradfi-manifest-cas migration
canonicalized ~4,898 bundle underlyings to English product names (AUD, GOLD, SP500, EUR, ...). But CME/`GLBX.MDP3`'s
curated Databento symbol list uses **raw exchange codes** (6A, GC, ES, 6E, ...), not English names. Live VM run.log
proof (`gs://deployment-scripts-.../vm-logs/mtds-backfill-tradfi-pipelinecheck-20260723-121226-6db06d/run.log`):

```
DatabentoAdapter: instrument_ids filter ['AUD'] matched nothing for venue=CME dataset(s)=['GLBX.MDP3'] — 154 curated
symbol(s) available (['6A','6A.FUT',...]) ... this shard will silently write 0 records
DatabentoAdapter.download_batch_df: CME 2024-03-25 — 0 records
```

This is the exact same bug class already named (for a single shard) in the plan's own P2 note for `CME:ohlcv_1m`
NAT-GAS-MNG ("sampler picks the now-canonical underlying name, but Databento's adapter needs the raw exchange code NG")
— it is now confirmed to hit chain-bundle shards **broadly**, not as an isolated case: a live manifest census shows CME
options_chain's top underlying values are almost entirely canonical English names (AUD, COPPER, TNOTE2Y, EUR, TBOND,
RUSSELL2000, CRUDE, GBP, SP500, GOLD) — every one of these will hit the same mismatch on any day.

**ICE re-tested and currently PASSES** (`.../124515-55fb5a` + `.../124932-55fb5a`:
`Processed date=2024-03-25: 1 venues ok, ... 1 total records`) — ICE's Databento dataset apparently curates by product
name already, so this is a **CME/GLBX.MDP3-specific** mismatch, not universal across TradFi venues.

## 3. A distinct bug: garbage `underlying` values get sampled — FIXED

Independently, CME options_chain's skip leg sampled `underlying=TICKS` at day=2026-01-30 — not a real product root.
Direct query of the live `availability_index.parquet` confirmed **29 real rows**,
`venue=CME data_type=options_chain underlying==TICKS`, all `capture_status=captured`, dated 2025-11 through 2026-01-30
(the exact day auto-day picked — it genuinely is the newest such row). This is the same "legacy garbage `underlying`"
class the chain-manifest recovery script's own docstring already names (`CC__FMZ0023!`, `CC__FMU0024!`, `CC__FMZ0024!`,
...) — visible alongside "TICKS" in the same census — just never filtered out of the checker's sampling path.

**Fixed 2026-07-23** (`mtds@98a81c26`, `scripts/pipeline_e2e_check.py::sample_live_instrument`): for TRADFI
bundled-chain shards only, prefer the first matching row whose `underlying` passes `is_recognized_tradfi_underlying()`
over an unrecognized one; falls back to the old `iloc[0]` behavior only when none qualify (still surfaces a failure,
just not a misleading one). Guarded to TRADFI-only — the validator is TradFi-specific and would wrongly reject valid
CEFI chain underlyings (e.g. Deribit) that don't happen to overlap CME's root list.

## 4. Open question — the canonical-root → raw-symbol reverse translation (NOT fixed)

Section 2's mismatch needs a real fix: before passing a chain-bundle shard's sampled (now-canonical) `underlying` as
`--instrument-ids` to a CME/GLBX.MDP3 fetch, translate it BACK to the raw exchange code the Databento adapter's curated
list actually indexes on. This is genuinely harder than a simple dict-invert:

- `EXCHANGE_CODE_TO_NAME` is **not injective** — `"6A"` and `"M6A"` both map to `"AUD"` (standard vs micro contract). A
  naive `{v: k for k, v in d.items()}` silently keeps whichever key iterates last, which is an arbitrary, undocumented
  choice between two economically different contracts.
- **Two disagreeing copies of `EXCHANGE_CODE_TO_NAME` exist** (see the operator-notify banner above) — reversing off the
  wrong one, or off both inconsistently, compounds the problem.
- The fix likely needs venue-scoped context (which raw code family CME's checker/backfill actually wants — standard vs
  micro) rather than a single global reverse map.

**Recommendation**: resolve the SSOT contradiction first (pick or merge the two `EXCHANGE_CODE_TO_NAME`s), then design
the reverse-translation step deliberately (probably scoped inside
`market-tick-data-service/scripts/pipeline_e2e_check.py`'s sampler, CME/GLBX.MDP3-only, defaulting to the standard
(non-micro) contract code) rather than a blind dict inversion. Not attempted in this session — flagged for operator
input on which registry wins and which contract family the checker should prefer.

## Evidence trail

- Full-surface MTDS report: `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_13.json` (results for
  `TRADFI:CME:futures_chain`, `TRADFI:CME:options_chain`, `TRADFI:ICE:futures_chain`).
- Recovery script's own COCOA/AUD real-GCS-data note:
  `market-tick-data-service/market_tick_data_service/scripts/recover_tradfi_chain_manifest_registration_2026_07_22.py`.
- `EXCHANGE_CODE_TO_NAME` disagreement:
  `unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:552` vs
  `unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py:166`.
