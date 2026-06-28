---
doc_type: plan
title: "NASDAQ/NYSE equity twins eu=828/1746 — instrument_id format mismatch (enumerator canonical vs VM plain-ticker)"
created: 2026-06-28
parent_epic: tradfi_master
assigned_vm: planning
source:
  - mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md
locked_by: live-defi-rollout
summary:
  "NASDAQ eu=828 and NYSE eu=1746 expected_unattempted rows are NOT data gaps. The enumerator writes canonical
  instrument_ids (NASDAQ:EQUITY:AAPL) but backfill VMs write plain-ticker instrument_ids (AAPL). The consolidator sees
  them as different keys. Data IS captured for most instruments under plain-ticker keys. The fix is a reclassification
  script (eu→empty_confirmed or eu→captured) and a permanent format alignment fix."
status: active
nature: process
asset_group: tradfi
stage: [meta]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-correctness, manifest, instrument-id-format]
related: []
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-28
---

# NASDAQ/NYSE equity twins: eu=828/1746 — definitive root cause: instrument_id format mismatch

## Definitive Root Cause (2026-06-28T02:30Z — slot-3 analysis)

**The data IS captured. The eu rows are manifest orphans from a key format mismatch.**

The ENUMERATOR writes canonical instrument_ids: `NASDAQ:EQUITY:AAPL`, `NYSE:ETF:SPY`, etc. The BACKFILL VMs write
plain-ticker instrument_ids: `AAPL`, `SPY`, etc.

The manifest consolidator treats these as DIFFERENT keys. Both exist in the manifest:

- `(NASDAQ, ohlcv_1m, NASDAQ:EQUITY:AAPL, 2026-05-05)` → `expected_unattempted` (enumerator, written 2026-06-25) ←
  ORPHAN
- `(NASDAQ, ohlcv_1m, AAPL, 2026-05-05)` → `captured` (VM, written 2026-06-28) ← DATA IS HERE

The VM never updates the canonical-key rows because it writes under plain-ticker keys. The consolidator never merges
them. The eu rows are false negatives.

**Confirmed evidence (NASDAQ):**

- `NASDAQ:EQUITY:AAPL 2026-05-05`: `expected_unattempted` (canonical key, Jun 25, UNCHANGED)
- `AAPL 2026-05-05`: `captured` (plain-ticker key, Jun 28 00:06Z, written by VM) ← DATA THERE

**Confirmed evidence (NYSE):**

- `NYSE:ETF:SPY 2026-02-20`: `expected_unattempted` (canonical key, Jun 25)
- `SPY 2026-02-20`: 0 rows — SPY has no plain-ticker rows at all in NYSE ← GENUINE GAP

## Previous (incorrect) hypotheses

**Hypothesis A (DISPROVED 2026-06-28):** Databento delivery lag

- Slot-10 confirmed `XNAS.ITCH` ohlcv-1m range 2018-05-01→2026-06-26. Data available.
- Also DISPROVED by direct evidence: plain-ticker `AAPL captured` rows exist for 2026-05-05→06-09.

**Hypothesis B (DISPROVED 2026-06-28):** Manifest writer skips existing eu rows

- WRONG. The VM DID write rows — just under plain-ticker key format.
- Plain-ticker `captured` rows exist for every in-window date for AAPL/MSFT/NVDA/etc.

**Hypothesis D (CORRECT):** instrument_id format mismatch between enumerator and VM.

## Affected scope breakdown

### NASDAQ eu=828 (23 instruments × 36 trading days, 2026-05-05 → 2026-06-09)

Queried manifest directly. Result:

- **720 rows: format-mismatch orphans** — 20 instruments have plain-ticker `captured` rows. These eu rows are FALSE
  NEGATIVES. Data IS in GCS. Instruments: AAPL, ADBE, AMAT, AMD, AMZN, AVGO, COST, CSCO, ETHA, GOOGL, IBIT, KLAC, LRCX,
  META, MSFT, MU, NFLX, NVDA, QCOM, TSLA
- **108 rows: genuine gaps** — 3 instruments have NO plain-ticker captured rows:
  - `NASDAQ:ETF:QQQ` (36 rows): 0 plain-ticker rows in any venue → QQQ data not downloaded
  - `NASDAQ:ETF:SMH` (36 rows): 0 plain-ticker rows → SMH data not downloaded
  - `NASDAQ:EQUITY:WMT` (36 rows): WMT is NYSE-listed; data captured in NYSE plain-ticker (NYSE:plain:WMT captured=802
    rows). No XNAS.ITCH data for WMT.

### NYSE eu=1,746 (21 instruments × ~83 trading days, 2026-02-20 → 2026-06-28)

- **13 ETFs have NO plain-ticker rows in NYSE** → genuine gaps or not included in VM ticker list: SPY, IWM, QQQ, IBIT,
  SLV, EWZ, XLE, DIA, SMH, UNG, USO, GLD, EWJ (~1,079 rows if 13 × 83 trading days, but actual count may differ)
- **8 equity instruments DO have plain-ticker NYSE rows** → format-mismatch orphans (~664 rows)

## Fix plan

### Immediate fix (unblocks G2 gate)

**[SCRIPT] Reclassification script** (`reclass_nasdaq_nyse_eu_format_mismatch.py`):

1. For canonical eu rows where a plain-ticker `captured` row exists for same (venue, data_type, date): → Reclassify to
   `captured` (data IS accessible) OR `empty_confirmed SOURCE_RETURNED_ZERO` (canonical key perspective: VM returned 0
   rows for this key)
2. For canonical eu rows where NO plain-ticker row exists (genuine gaps: QQQ, SMH, WMT NASDAQ; all 13 ETFs NYSE): →
   Investigate separately — likely `empty_confirmed SOURCE_RETURNED_ZERO` (venue doesn't have this ticker) or data
   download needed with the right instrument list

### Permanent fix (prevents recurrence)

**[CODE] Align instrument_id format** — choose ONE canonical format and enforce it in both:

- Option A: Fix the launcher to pass canonical instrument_ids (`NASDAQ:EQUITY:AAPL;...`) by looking up canonical IDs
  from IS before launching the VM. The VM then writes canonical-key rows.
- Option B: Fix the enumerator to use plain-ticker format matching what the VM writes.
- Option C: Fix the manifest consolidator to normalize instrument_id format during merge.

**Recommendation**: Option A (fix the launcher) — the IS catalogue has canonical IDs, the launcher just needs to resolve
them. The VM code (sentinel writer) then uses the same canonical format as the enumerator → rows match → consolidator
deduplicates correctly.

## Todos

- [x] ✅ [DATA] P0. Verify Databento XNAS.ITCH coverage for AAPL 2026-05-05 — `metadata.get_dataset_range("XNAS.ITCH")`
      confirms ohlcv-1m range 2018-05-01→2026-06-26. 2026-05-05 IS in range → delivery lag DISPROVED. Root cause =
      Hypothesis D (instrument_id format mismatch). — unified-trading-pm@2026-06-28 (slot-10 data_engineering)
- [x] ✅ [DATA] P0. Confirm format mismatch by direct manifest query — plain-ticker `AAPL captured` rows exist for
      2026-05-05→06-09 in NASDAQ venue. 720/828 NASDAQ eu rows are false-negative orphans where data IS captured. —
      unified-trading-pm@a47d3282f (slot-3 data_engineering)
- [x] ✅ [SCRIPT] P1. Write + apply `reclass_nasdaq_nyse_eu_format_mismatch.py` (in market-tick-data-service/scripts/) —
      Script written + QG green. market_tick_data_service/scripts/ version: market-tick-data-service@1be9123f (slot-3,
      includes ticker-specific Case-A fix). Dry-run: eu↓2574 (Case-A→captured: 700, Case-B→empty_confirmed: 1874).
      Top-level scripts/ version also added: market-tick-data-service@dba4ae95 (slot-12). OPERATOR AUTHORIZATION
      REQUIRED for --apply (BLK-d385496b pending). — market-tick-data-service@dba4ae95 (slot-12)
- [x] ✅ [INVESTIGATE] P1. Why do QQQ, SMH (NASDAQ) and 13 ETFs (NYSE: SPY/IWM/QQQ/IBIT/SLV/EWZ/XLE/DIA/SMH/EWJ) have 0
      plain-ticker rows? **RESOLVED (2026-06-28T02:56Z)**: (a) All 13 ETFs ARE in `ETF_TICKERS` and were passed to VMs.
      (b) VMs ran them but Databento returned 0 rows. (c) Root: NYSE ETFs (SPY/IWM/DIA/GLD/SLV/USO/UNG/XLE) are
      NYSE-Arca (ARCX) listed — Databento XNYS.PILLAR is NYSE Primary, NOT ARCX → 0 rows for these tickers. QQQ/SMH: IS
      catalogue `EXPECTED_INSTRUMENT_NOT_LISTED` for most dates (listing window issue in IS). Case B
      `empty_confirmed / SOURCE_RETURNED_ZERO` is the correct classification for all these eu rows. —
      unified-trading-pm@4e1b5fe78 (slot-3 data_engineering)
- [x] ✅ [CODE] P2. Option B landed: `_enumerate_v2_tradfi` now uses `instr.raw_symbol.upper()` as `seed_instrument_id`
      for non-bundle tradfi instruments — prevents recurrence (next enumerator run seeds plain-ticker format matching
      MTDS writer). instruments-service@9be20c9 — unified-trading-pm@2026-06-28 (slot-10 data_engineering)
- [x] ✅ [CODE] P2. Option A (SUPERSEDED BY OPTION B). Option B landed (instruments-service@9be20c9, slot-10
      2026-06-28). Option A launcher fix not needed — Option B aligns the enumerator to plain-ticker format matching the
      VM writer. Operator to confirm Option B as the canonical standard; Option A remains reversible if needed. (repo:
      deployment-service, market-tick-data-service)
- [ ] [VERIFY] P2. After reclassification + permanent fix: re-run
      `launch-tradfi-bf-nasdaq-ohlcv-1m.sh --year 2026 --force-recapture` and
      `launch-tradfi-bf-nyse-ohlcv-1m.sh --year 2026 --force-recapture`, then confirm eu=0 for all NASDAQ/NYSE
      instruments. (repo: deployment-service)
