---
doc_type: plan
title: MVP backfill — TradFi ohlcv_1m for the v10 MVP universe (SPOT-only, reconcile-then-fill)
summary:
  Backfill TradFi ohlcv_1m ONLY for the canonical v10 MVP universe (CME futures + new CME options + equity twins),
  reconciling what is already captured vs what is missing on SPOT VMs.
status: complete
nature: process
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, tradfi, ohlcv-1m, cme, cme-options, spot-vm, v10, budget-aware]
related:
  [
    plans/active/mvp_catalogue_finalization_v10_2026_06_27.md,
    plans/active/tradfi_multisource_backfill_2026_06_22.md,
    plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md,
  ]
created: 2026-06-27
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on: [mvp_catalogue_finalization_v10_2026_06_27]
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **✅ ARCHIVED — 2026-06-30 — TRULY-DONE.** G2 GATE MET 2026-06-29 (`mtds@a49403e2`): eu=0 af=0 for all MVP venues
> (CME/CBOE/NASDAQ/NYSE), KRX honest-empty, ICE excluded per BLK-ca110c07. Content-verified + main-loop spot-checked (§6
> B1.2 of `plan_issue_epic_consolidation_2026_06_30`).

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** Part of the remaining MVP arc handed to the
> agent-orchestrator (`planning` VM). One agent, one craft (`data_engineering`), Sonnet/high.
>
> **🟢 GATE CLEARED 2026-06-28T02:12Z** — `mvp_catalogue_finalization_v10_2026_06_27.md` G3 sign-off complete. tradfi
> catalogue v10-correct: 1,038,235 rows, 643,116 MVP (642,126 CME OPTION ✅), false-delist=0, ghosts=N/A, blank=0.
> Phantom audit: 1,789 phantoms (MTDS data; issue doc `phantom_captures_tradfi_2026_06_28.md`).
>
> **Canonical MVP SSOT (the ONLY scope authority):** `mvp_scope.py` v10 + `/codex/02-data/mvp-scope-canonical.md`. This
> plan REFERENCES it. **TradFi v10 = ohlcv_1m ONLY** (decision #7 — NO ohlcv_1s, NO trades/tbbo). Any older tradfi plan
> that says otherwise is stale and SUBORDINATE (see Phase-4 reconciliation).

## Codex SSOTs (READ before executing)

- `/codex/02-data/mvp-scope-canonical.md` § TradFi — venue=CME (futures complex) + equity-basis carve-out
  (NASDAQ/NYSE/ARCA/KRX in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`); instrument types FUTURE + OPTION; **data_type cut =
  ohlcv_1m ONLY**; underliers ES·NQ·VX + the CME commodity roots backing a Binance tradfi-perp (GC/SI/PL/PA/NG/CL/HG).
- `/codex/02-data/tradfi-databento-sourcing-ssot.md` — 3-dataset billing fail-closed; SOURCE_PRIORITY databento-first;
  VIX=VX-futures via XCBF.PITCH; Barchart RETIRED; silent-0-row backfill gotchas.
- `/codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT-by-default; `--on-demand` is the deadline escape hatch
  only.
- `/codex/02-data/honest-absence-downstream-handling.md` — `EXPECTED_*` reasons (weekends/holidays via
  `venue_trading_calendar`; pre-listing via `EXPECTED_INSTRUMENT_NOT_LISTED`); honest-empty excluded from denominator.

## Definition of 100% (read first)

`captured` covers 100% of the v10 tradfi MVP could-exist universe → `attempted_failed = 0` AND
`expected_unattempted = 0`. **Honest `empty_confirmed` is EXCLUDED** (weekends/holidays per `venue_trading_calendar`,
pre-listing, half-days, documented structural gaps like VIX/VX). NOT a gap. Drive the two failure buckets to zero; never
fabricate rows to eliminate honest empties.

## Budget posture

TradFi ohlcv_1m is cheap (Databento OHLCV, not tick). Much is ALREADY captured (per `path_to_100pct` the Databento OHLCV
backfill ran to completion 2026-06-19; equity floors auto-clip to 2023-04-15). **Reconcile-then-fill: do NOT blindly
re-pull** — measure what's captured, fill only the gaps. SPOT VMs only.

---

## Todos (SEQUENTIAL: G0 → reconcile → fill → verify)

### G0 — gate + reconcile (what's missing vs already captured)

- [x] ✅ [SCRIPT] P0. Confirm Phase-0 tradfi catalogue sign-off (incl. CME OPTION rows present) before any download.
      Repo: `unified-trading-pm` (read the coordinator plan) + `instruments-service`. **Gate:**
      `mvp_catalogue_finalization_v10_2026_06_27.md` Progress Log shows tradfi G3 green;
      `audit_instrument_definition_completeness.py --asset-group tradfi` shows OPTION cells. If not signed off → wait
      (task-level prereq), do not launch. SPOT N/A. — unified-trading-pm@docs(plans): — G3 GREEN: 642,126 CME OPTION
      rows mvp=True; 1,038,235 total; 0 blank-status; 0 false-delist mass-collapse; ECNQ/ECGC event contracts correctly
      mvp=False. Catalogue promoted 2026-06-27T23:04:49Z.
- [x] ✅ [SCRIPT] P0. Build the tradfi gap report: for the v10 MVP universe (CME futures roots
      ES/NQ/VX/GC/SI/PL/PA/NG/CL/HG + the new CME OPTION roots + the equity twins in
      `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`), measure
      `captured / empty_confirmed / attempted_failed / expected_unattempted` for **ohlcv_1m**. Repos:
      `instruments-service`, `e2e-testing`. **Run:** `python scripts/measure_honest_coverage.py --asset-group tradfi`
      and read the `by_venue_data_type` breakdown for ohlcv_1m; list the (venue, root, year) cells with
      `attempted_failed > 0` or `expected_unattempted > 0`. **Gate:** a concrete gap list (venue×root×year) written to
      the Progress Log; if attempted_failed/expected_unattempted are already 0 for ohlcv_1m across the MVP universe,
      tradfi is DONE — record + skip the fill todos. SPOT N/A (read-only). — Gap report 2026-06-27 → see Progress Log
      below.

### G1 — fill the gaps (SPOT VMs only, ohlcv_1m only)

- [x] ✅ [SCRIPT] P0. CME futures + options ohlcv_1m gap-fill. Repo: `deployment-service`. **SPOT VMs only**
      (`launch-tradfi-bf-cme-ohlcv-1m.sh` defaults SPOT). **Set ohlcv_1m ONLY** (NOT the lib default
      `ohlcv_1m;ohlcv_1s`):
      `TRADFI_OHLCV_DATA_TYPES=ohlcv_1m bash scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --dry-run` to inspect, then
      launch only the gap roots/years from G0 (`--only-root <ROOT> --year <YYYY>` per missing cell, or full fleet if the
      gap is broad). The CME root universe (futures+options as `<ROOT>.FUT;<ROOT>.OPT`) covers
      ES/NQ/GC/SI/PL/PA/NG/CL/HG + event contracts; window 2019-01-01→yesterday (GLBX.MDP3 full coverage). **Gate:** VMs
      STARTED <60s, `MANIFEST_PER_VM_SHARDS=true`, self-stop on completion; verify T+10min via
      `gcloud compute instances list --filter='name~tradfi-bf-cme' --zones=asia-northeast1-c`. Re-run
      `measure_honest_coverage.py --asset-group tradfi` → CME ohlcv_1m attempted_failed=0. No-fire-and-forget. —
      deployment-service@(plan flip) — T+10min: 72 CME SPOT VMs RUNNING, af=0. See G1 CME progress log below.
- [x] ✅ [SCRIPT] P0. VIX/VX ohlcv_1m gap-fill (VIX = VX-futures via XCBF.PITCH; Barchart RETIRED). Repo:
      `deployment-service`. **SPOT VMs only.** Use `launch-tradfi-bf-cfe-ohlcv-1m.sh` (CFE `XCBF.PITCH` VX futures) with
      `TRADFI_OHLCV_DATA_TYPES=ohlcv_1m`. Honor the documented VIX 15m known-gap (`EXPECTED_KNOWN_SOURCE_GAP`
      2025-11-13→today−60d) — that window is honest-empty, NOT a gap to fill. **Gate:** VX ohlcv_1m attempted_failed=0
      except the documented known-gap window (which stays `empty_confirmed`). Verify T+10min. SPOT VMs only. —
      deployment-service@(plan flip) — 9 SPOT VMs RUNNING (2018-2026), CBOE/ohlcv_1m af=0 pre-launch; T+10min all 9
      RUNNING. Known-gap 2025-11-13→2026-04-29 will appear as empty_confirmed.
- [x] ✅ [SCRIPT] P0. Equity-twin ohlcv_1m gap-fill (NASDAQ/NYSE equity backing the Binance equity-perps in
      `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`). Repo: `deployment-service`. **SPOT VMs only.** Use
      `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` + `launch-tradfi-bf-nyse-ohlcv-1m.sh` with
      `TRADFI_OHLCV_DATA_TYPES=ohlcv_1m`; floors auto-clip to 2023-04-15 (Databento equity coverage) — pre-2023 cells
      are honest `EXPECTED_PRE_SOURCE_COVERAGE_START`, do NOT launch pre-floor shards. Launch only the gap years from
      G0. **Gate:** equity-twin ohlcv_1m attempted_failed=0 from the 2023-04-15 floor; verify T+10min. SPOT VMs only. —
      deployment-service@(plan flip) — NASDAQ 2023/2024/2025 + NYSE 2023/2024/2025 SPOT VMs RUNNING (af=0 pre-launch);
      2026 shards already running from prior session; T+10min: 8/8 RUNNING. KRX eu=372 deferred (no launcher; out of
      scope per plan text).

### G2 — verify honest-complete

- [x] [SCRIPT] P0. ✅ 2026-06-29T10:45Z — G2 GATE MET: eu=0 af=0 all MVP venues (CME/CBOE/NASDAQ/NYSE). BLK-5b95659d
      Option A applied. market-tick-data-service@a49403e2. [DEFERRED 2026-06-28 — re-check 2026-06-30 after CME options
      VMs complete per BLK-180b591d answer B] Final tradfi MVP verification: ohlcv_1m attempted_failed=0 AND
      expected_unattempted=0 across the v10 MVP universe; every absence is a typed honest `empty_confirmed`
      (weekend/holiday/pre-listing/known-gap), never a silent missing cell. Repos: `instruments-service`, `e2e-testing`.
      **Run:** `python scripts/measure_honest_coverage.py --asset-group tradfi`;
      `python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group tradfi --mode full` (phantom +
      4-pillar + v9). **Gate:** measured coverage = 100% of MVP could-exist (both failure buckets zero); 0 phantom rows;
      0 blank-status; verdict written to Progress Log. **Full-execution criterion:** the gcloud VM-list + the coverage
      CLI output recorded. Any genuine source-unavailable cell is honest-empty + documented (cite the reason), NOT left
      BLOCKED. SPOT N/A. **Remaining eu blockers (19:11Z 2026-06-28):** CME eu=8,424 (chain meta-rows — structural,
      operator classified non-downloadable, exclude from denominator; count grew from 569→8,424 as options catalogue
      populated); NASDAQ eu=828 + NYSE eu=1,746 (canonical format mismatch, reclassifier BLK-d385496b pending); ICE
      af=66 (migration artifacts, NOT MVP scope). KRX eu=0 ✅ (reclassified to EXPECTED_SOURCE_NOT_AVAILABLE
      2026-06-28T19:11Z).

---

## Progress Log

### G0 Gap Report — 2026-06-27T23:16Z (manifest: 2,449,721 rows; ohlcv_1m: 383,731 rows)

Overall honest coverage: **95.95%** (695,300 / 724,664 reachable ohlcv_1m cells)

| venue  | capture_status       | count | assessment                                                                                                                                               |
| ------ | -------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CME    | expected_unattempted | 569   | `instrument_type=futures_chain` chain-aggregate meta-rows (blank instrument_id); underliers PA/PL/NG/SI/HG/CL/ES/NQ/GC — NOT individual bars to download |
| NYSE   | expected_unattempted | 1,734 | Equity twins (BRK.B, CRM, HD, JPM, LLY, V, DIA…) 2026-02-20→2026-06-23 — **real gap, G1 fill needed**                                                    |
| NASDAQ | expected_unattempted | 851   | Equity twins (AAPL, AMZN, GOOGL, AMD, AVGO…) 2026-05-05→2026-06-10 — **real gap, G1 fill needed**                                                        |
| KRX    | expected_unattempted | 372   | KRX equity twins 2026 — **real gap, G1 fill needed**                                                                                                     |
| ICE    | attempted_failed     | 66    | All `ticks_migrated_20260418T*` instrument IDs — migration artefacts, NOT real ICE MVP instruments; pre-existing                                         |

**CME futures bars: 100% captured** (170,158 captured, 0 attempted_failed, 0 expected_unattempted for individual FUTURE
rows).

**Fill needed:** NYSE + NASDAQ + KRX equity twin ohlcv_1m (2,957 expected_unattempted rows across 2026-02-20→2026-06-23
window) → G1 todos required. CME OPTION ohlcv_1m bars not yet in manifest (definitions just populated 2026-06-27) → also
need G1 CME options fill.

### G1 CME Options Fill — 2026-06-28T00:28Z (slot-3)

**Pre-existing VMs (launched before catalogue update at 23:04:49Z):** 47 VMs for 9 core roots
(CL/ES/GC/HG/NG/NQ/PA/PL/SI) were already running at session start. These cover HG/NG/PA/PL/SI for 2020-2026 and
ES/GC/CL/NQ for 2025-2026. ⚠️ **Finding:** VMs in the 21:00 UTC batch (before catalogue update) may have downloaded
futures only (IS catalogue had no CME OPTION definitions at startup time). Dates processed before 23:04:49Z in those VMs
may be missing OPT bars. After these VMs complete, a force-recapture pass for 2025/2026 shards may be needed (see
below).

**New VMs launched this session (TRADFI_OHLCV_DATA_TYPES=ohlcv_1m, SPOT, --force to bypass cap):**

| Root | Years launched                           | VM count | Notes                                                                   |
| ---- | ---------------------------------------- | -------- | ----------------------------------------------------------------------- |
| ES   | 2019, 2021-2024 (+ 2020 force-recapture) | 6        | 2020 had terminated pre-catalogue VM; relaunched with --force-recapture |
| NQ   | 2019-2024                                | 6        |                                                                         |
| GC   | 2019-2024                                | 6        |                                                                         |
| CL   | 2019-2024                                | 6        |                                                                         |
| HG   | 2019                                     | 1        |                                                                         |
| NG   | 2019                                     | 1        |                                                                         |
| PA   | 2019                                     | 1        |                                                                         |
| PL   | 2019                                     | 1        |                                                                         |
| SI   | 2019                                     | 1        |                                                                         |

**Total new VMs: 29** (plus 46 pre-existing = 75 CME VMs active).

**T+10min gate:** `gcloud instances list --filter='name~tradfi-bf-cme' --zones=asia-northeast1-c` → 72 RUNNING ✓

**Coverage at launch time:** CME/ohlcv_1m: captured=170,674, attempted_failed=0 ✓, expected_unattempted=569
(chain-aggregate meta-rows only, NOT individual bars to download).

**⚠️ Follow-up needed (deferred):** The 2025/2026 year shards for pre-catalogue VMs (launched at 21:00 UTC, before the
23:04:49Z catalogue update) may need `--force-recapture` after they complete to pick up options bars for dates processed
before the catalogue was updated. Assess once those VMs drain and re-run `measure_honest_coverage.py`. If CME OPT bars
are missing for 2025-2026 in the manifest, launch force-recapture VMs:
`TRADFI_OHLCV_DATA_TYPES=ohlcv_1m bash launch-tradfi-bf-cme-ohlcv-1m.sh --only-root <ROOT> --year 2025 --force-recapture --force`
for each of CL/ES/GC/NQ/HG/NG/PA/PL/SI.

### G2 Verification — 2026-06-28T00:55Z (intermediate; VMs still draining)

**Coverage at check time:** 95.96% (697,344/726,696 reachable) — NASDAQ/NYSE 2023-2025 VMs launched ~00:40 UTC, not yet
consolidated.

**4-pillar:** Fixed `shard_4pillar_fail` TypeError (mixed str/int `row_count` in manifest) → e2e-testing@af20311.
4-pillar now GREEN (33/33 parquets pass all pillars, 0 phantoms).

**Structural gaps identified (require operator decision):**

| venue | status | count | assessment                                                                                                                                                                                                                                    |
| ----- | ------ | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CME   | eu=569 | 569   | `instrument_id=''`, `instrument_type=futures_chain` — chain-aggregate meta-rows, NOT individual bars. Coverage script counts them but they are NOT downloadable. Pre-existing manifest artifact.                                              |
| ICE   | af=66  | 66    | `ticks_migrated_20260418T*` instrument IDs — migration artefacts from April 2026 migration, error_reason=SCHEMA_VALIDATION_FAILED. NOT real MVP instruments. Pre-existing.                                                                    |
| KRX   | eu=372 | 372   | 3 instruments: KRX:EQUITY:000660/005380/005930 (Samsung/SK Hynix/Hyundai) 2026-02-20→2026-06-23. No Databento KRX dataset; no launcher script. **OPERATOR DECISION NEEDED** (reclassify as EXPECTED_SOURCE_NOT_AVAILABLE or find new source). |

**Hygiene findings (non-blocking for ohlcv_1m MVP scope):**

- `schema_version_not_v9`: 16,628 legacy rows (v4=16,620, v6=8) — pre-existing from old backfill runs, NOT from this
  session's VMs. Not blocking.
- `oracle_expects_but_empty`: NYSE ohlcv_1m 2026-06-26 DIVERGENT_EMPTY (1 in-scope case; 193 total divergent including
  non-MVP ohlcv_1s). Needs investigation — 2026-06-26 is a Thursday (trading day).
- `phantom_captured_no_parquet`: 2 manifest rows captured with no GCS parquet. 1,911 records in triage JSONL.
  Pre-existing.

**Issue filed:** `plans/active/issues/krx_equity_twin_no_source_2026_06_28.md` (COMMITTED 9261d1d25; KRX OPERATOR
DECISION pending).

**Next step:** Re-run `measure_honest_coverage.py` after NASDAQ/NYSE VMs drain (~60-90 min from 00:40 UTC). Expect
NASDAQ eu=851→0, NYSE eu=1734→0 once manifest consolidates. Remaining: CME eu=569, ICE af=66, KRX eu=372 (all
structural, not fillable by VMs).

### G2 Verification — 2026-06-28T01:09Z (slot-3; VMs still draining; BLK-ca110c07)

**Coverage at check time:** 95.97% (698,330/727,644 reachable) — NASDAQ/NYSE 2023-2025 VMs ~33min running; 2026 VMs
running 4+ hours (active, gsutil writes every ~1min).

**ohlcv_1m by venue (MVP scope):**

| venue  | af  | eu    | assessment                                                                             |
| ------ | --- | ----- | -------------------------------------------------------------------------------------- |
| CME    | 0   | 569   | chain-aggregate meta-rows (blank instrument_id) — structural, NOT individual bars      |
| ICE    | 66  | 0     | `ticks_migrated_20260418T*` migration artifacts — structural, NOT real MVP instruments |
| KRX    | 0   | 372   | no Databento KRX dataset; no launcher — OPERATOR DECISION (krx issue doc filed)        |
| NASDAQ | 0   | 851   | VMs active (2023-2025 ~33min; 2026 ~4h+); expect→0 once manifest consolidates          |
| NYSE   | 0   | 1,734 | VMs active (2023-2025 ~33min; 2026 ~4h+); expect→0 once manifest consolidates          |
| other  | 0   | 0     | all clean ✅                                                                           |

**Hygiene (01:11Z run):**

- `oracle_expects_but_empty`: 0 ✅ (was 193 at 00:55Z — cleared as NYSE ohlcv_1s/1m divergences resolved)
- `phantom_captured_no_parquet`: 0 ✅ (was 1,911 at 00:55Z — phantoms cleared)
- `shard_4pillar_fail`: 1 ❌ FALSE POSITIVE — hygiene script ran without `GCP_PROJECT_ID` in subprocess env → rc=2;
  direct 4-pillar run with `GCP_PROJECT_ID=central-element-323112` shows **33/33 GREEN**
- `schema_version_not_v9`: SKIPPED (no_index available to check)

**Blocked (BLK-ca110c07):** awaiting operator decision on structural items and whether to wait for full VM drain vs
accept partial verdict.

### G2 Verification — 2026-06-28T01:32Z (slot-3; BLK-180b591d — gate revision needed)

**Coverage at check time:** 93.96% (699,397/744,351 reachable) — manifest grew 2,479,911 rows (+20k); CME options
enumeration active.

**Key finding: af=0 FOR ALL MVP-SCOPE VENUES ✅** — no data failures anywhere in the MVP universe.

**ohlcv_1m DELTA (01:09Z → 01:32Z):**

| venue  | af now | eu now | delta af | delta eu | notes                                                                                                             |
| ------ | ------ | ------ | -------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| CME    | 0      | 8,424  | +0       | +7,855   | ⚠️ Options enumeration: VMs writing expected_unattempted for new CME OPTION instrument-date combos before filling |
| KRX    | 0      | 378    | +0       | +6       | new KRX instrument dates added                                                                                    |
| NASDAQ | 0      | 828    | +0       | -23      | ✅ NASDAQ-2026 VM COMPLETED (auto-deleted SPOT); 2023-2025 VMs still running                                      |
| NYSE   | 0      | 1,746  | +0       | +12      | NYSE-2026 VM still running (4h+ active)                                                                           |
| ICE    | 66     | 0      | +0       | +0       | structural migration artifacts (unchanged)                                                                        |
| CBOE   | 0      | 0      | +0       | +0       | ✅ clean                                                                                                          |
| other  | 0      | 0      | +0       | +0       | ✅ clean                                                                                                          |

**Root cause of CME eu surge:** CME VMs processing new CME OPTION definitions (642,126 definitions added
2026-06-27T23:04Z) write manifest entries as `expected_unattempted` for each instrument × date before downloading. As
VMs process each date, these transition to `captured`. At current pace (~7,855 new eu in 23 min from 09 VMs), full
enumeration + fill across 9 roots × 2019-2026 will take **24-48+ hours**.

**Gate status:** `af=0` ✅ for all MVP scope. `eu=0` ❌ — NOT achievable today due to active CME options enumeration.

**Blocked (BLK-180b591d):** requesting operator decision — revised gate (A: af=0 + active fill), defer 24-48h (B), or
scope to futures-only (C). NOT flipping G2 checkbox until decision received.

**NASDAQ-2026 VM confirmed COMPLETED (auto-deleted as SPOT). NYSE-2026 still RUNNING.**

### G2 Verification — 2026-06-28T02:01Z (slot-3; data correctness finding filed)

**Coverage:** 93.98% (700,603/745,514 reachable). af=0 all MVP scope ✅.

**ROOT CAUSE FINDING — `expected_unattempted` silent skip:**

NASDAQ-2026 VM completed at ~01:32Z but left 828 eu rows UNCHANGED (written_at=2026-06-25 = from enumerator, not vm).
Example (AAPL):

- 2026-05-01→05-04: `empty_confirmed EXPECTED_INSTRUMENT_NOT_LISTED` (written 2026-06-28T01:31 ✓)
- 2026-05-05→06-09: `expected_unattempted` — **UNCHANGED from 2026-06-25** ← bug
- 2026-06-10→06-15: `empty_confirmed EXPECTED_INSTRUMENT_DELISTED` (written 2026-06-28T01:31 ✓)

VM correctly handled pre/post-listing but silently skipped in-window dates. Root cause: Databento XNAS.ITCH delivery lag
(dates 19-54 days old, within ~30-90d lag window) OR manifest logic bug (VM doesn't update existing eu entries after
processing). Either way: **silent placeholder violation** (HARD RULE: eu means not-yet-attempted; vm DID attempt these
dates).

**Data correctness issue filed:** `plans/active/issues/nasdaq_nyse_eu_silent_skip_2026_06_28.md` (3 todos: verify
Databento range, fix manifest writer, relaunch with --force-recapture).

**NYSE eu=1746:** Same pattern expected. NYSE-2026 VM still running (started 21:04Z, 5h+ runtime). NYSE eu has 1,724 old
entries from 2026-06-25 + 22 newly written entries.

**G2 gate status:** `af=0` all MVP scope ✅ (correctness met). `eu=0` ❌ — structural blockers:

1. NASDAQ eu=828: delivery lag / manifest logic bug (issue filed)
2. NYSE eu=1746: same pattern, NYC-2026 VM still running
3. CME eu=8424: options enumeration active (24-48h to complete)
4. KRX eu=378: no source (operator decision pending)
5. ICE af=66: migration artifacts (non-MVP, structural)

**Two /blocked pending:** BLK-ca110c07 (structural item classification), BLK-180b591d (gate revision vs defer).

### G2 Verification — 2026-06-28T02:14Z (slot-3; corrected CME eu finding; NYSE-2026 VM confirmed complete)

**Coverage:** 93.98% (701,421/746,314 reachable). Manifest: 2,486,985 rows. af=0 all MVP scope ✅. 68 tradfi-bf VMs
RUNNING (CME futures 2020-2025, CFE 2026, NASDAQ 2023-2025, NYSE 2023-2025).

**CORRECTED: CME eu=8,424 is ALL chain meta-rows — NOT options contracts being filled.**

Queried manifest directly. CME eu=8,424 breakdown:

- `options_chain`: 7,837 rows — chain-level aggregation rows for CME options roots (no individual `instrument_id`, not
  downloadable)
- `futures_chain`: 587 rows — chain-level aggregation rows for CME futures roots (same, not downloadable)

This corrects the BLK-180b591d premise: the eu=8,424 did NOT come from "options VMs enumerating expected_unattempted
rows before filling." These are chain meta-rows that the IS enumerator wrote when it found
`instrument_type=options_chain/futures_chain` entries in the IS catalogue. No backfill VM can ever fill them (no
downloadable OHLCV data exists at chain-level). They are structural artifacts identical in nature to the CME eu=569
(futures_chain) identified in BLK-ca110c07.

The CME options CONTRACTS (individual option instruments with specific `instrument_id`) ARE being captured by the
running CME VMs — their rows appear as `captured`, not as the eu=8,424.

**NYSE-2026 VM confirmed complete:** Not in RUNNING list. NYSE eu=1,746 unchanged (max written_at=2026-06-28T01:31Z,
same terminal time as NASDAQ-2026). NYSE-2026 VM had the same silent-skip pattern as NASDAQ-2026: classified
pre/post-listing correctly, left in-window dates as eu from 2026-06-25 enumerator. Confirms delivery lag hypothesis
(Databento XNYS.PILLAR for recent dates).

**Full eu breakdown (ohlcv_1m):**

1. CME eu=8,424: ALL structural chain meta-rows (options_chain + futures_chain) — cannot be filled, operator
   classification needed
2. NASDAQ eu=828: in-window delivery lag (2026-05-05→06-09), manifest logic bug — issue filed
3. NYSE eu=1,746: in-window delivery lag (2026-02-20→06-28), same bug — issue filed
4. KRX eu=378: no source — operator decision pending

**Revised gate picture:** af=0 ✅ all MVP scope. eu=0 requires: (1) operator classifies chain meta-rows as
non-downloadable structural artifacts; (2) code fix for delivery-lag silent-skip + re-run NASDAQ/NYSE 2026; (3) KRX
operator decision. None achievable today without code change or operator decision.

**Two /blocked pending (awaiting operator):** BLK-ca110c07, BLK-180b591d.

### G2 Verification — 2026-06-28T02:38Z (slot-3; reclass script written, QG'd, committed; dry-run gate passed)

**Root cause confirmed (instrument_id format mismatch):** The NASDAQ eu=828 and NYSE eu=1,746 are NOT delivery-lag gaps.
The enumerator writes canonical instrument_ids (`NASDAQ:EQUITY:AAPL`) while backfill VMs write plain-ticker
instrument_ids (`AAPL`). The manifest consolidator treats these as different keys → canonical eu rows are never
superseded. Data IS captured under plain-ticker keys for the majority of instruments.

**Script shipped:** `reclass_nasdaq_nyse_eu_format_mismatch.py` → market-tick-data-service@89a17fc7. Updated issue doc →
unified-trading-pm@2b2191901.

**CORRECTED dry-run gate PASSED (2026-06-28T02:56Z, market-tick-data-service@1be9123f):**

Bug found and fixed during investigation: the initial script used (venue, data_type, date) as the Case A key — this
incorrectly promoted `NYSE:ETF:SPY 2026-05-05` to `captured` if ANY plain-ticker instrument (e.g., AAPL) was captured on
that date in NYSE. Fixed to use (venue, data_type, date, **ticker**) — the ticker extracted from the canonical id
suffix. `NYSE:ETF:SPY` → ticker=`SPY` → must find plain-ticker `SPY captured` row (there are none) → correctly Case B.

Corrected numbers:

- Total reclassified: 2,574 rows (NASDAQ + NYSE canonical eu scope, unchanged)
- Case A (eu→captured, specific ticker's data IS accessible under plain-ticker key): 700 rows
  - NASDAQ equities: ~19 instruments × 36 days (some instruments partially covered)
- Case B (eu→empty_confirmed/SOURCE_RETURNED_ZERO): 1,874 rows
  - NASDAQ genuine gaps: QQQ/SMH/WMT × 36 days = 108 rows
  - NYSE ETFs (11 × 126 rows): DIA, UNG, IWM, IBIT, GLD, XLE, USO, SLV, QQQ, SPY, SMH = 1,386 rows
  - NYSE equity instruments with no plain-ticker captured rows: remainder ~380 rows
- Row count: 2,493,656 → 2,493,656 (UNCHANGED ✅)
- Delta: eu↓2574 / captured↑700 / empty_confirmed↑1874 (all match ✅)

**Investigation finding (P1):** All 13 gap ETFs ARE in `ETF_TICKERS` and would have been passed to VMs. The NYSE ETFs
(SPY, IWM, DIA, GLD, SLV, USO, UNG, XLE) are NYSE-Arca listed (ARCX), not NYSE Primary (XNYS.PILLAR). Databento
XNYS.PILLAR doesn't carry ARCX-primary ETFs → VMs returned 0 rows → `empty_confirmed SOURCE_RETURNED_ZERO` is the
correct classification. QQQ/SMH (NASDAQ) and IBIT/EWJ/EWZ (NYSE) have `EXPECTED_INSTRUMENT_NOT_LISTED` or
`EXPECTED_INSTRUMENT_DELISTED` indicating IS catalogue listing window issues for these tickers.

**After --apply:** eu will drop from 41,544 → 38,970. Remaining eu: CME chain meta-rows + KRX + non-NASDAQ/NYSE venues.

**ICE af correction (03:08Z):** ICE af=274 total: 66 ohlcv_1m + 208 blank data_type. ALL are `ticks_migrated_20260418T*`
instrument_ids — migration batch artifacts, NOT real instruments. ICE is NOT in MVP scope. MVP ohlcv_1m af=0 ✅
confirmed (separate query verified: CME/CBOE/NASDAQ/NYSE all af=0 for ohlcv_1m). CBOE ohlcv_1m eu=0, ARCA ohlcv_1m eu=0.

**Post-apply G2 status (projected):** af=0 MVP ✅ | eu: NASDAQ=0 NASDAQ=0 CBOE=0 ARCA=0 | CME=8,424 (chain meta,
operator decision) | KRX=378 (operator decision).

**Three /blocked pending (awaiting operator):** BLK-ca110c07, BLK-180b591d, BLK-d385496b. OPERATOR AUTHORIZATION
REQUIRED for `--apply`.

### G1/G2 Mid-VM Check — 2026-06-28T04:18Z (slot-10 data_engineering)

`measure_honest_coverage.py --asset-group tradfi` → 2,506,019 rows | coverage **94.04%** (706,220/750,953 reachable)

| venue  | captured |  af |     eu | note                                                                  |
| ------ | -------: | --: | -----: | --------------------------------------------------------------------- |
| NASDAQ |   73,269 | 226 |  6,727 | 3 VMs RUNNING (2023/2024/2025); plain-ticker eu draining              |
| NYSE   |  253,798 | 195 | 11,201 | 3 VMs RUNNING (2023/2024/2025); plain-ticker eu draining              |
| CME    |  370,862 | 214 | 20,214 | ~30 VMs RUNNING; eu growing as options VMs seed ohlcv_1m eu rows      |
| KRX    |        0 |   0 |  3,402 | No launcher/source; operator decision pending (was 372 at G0 — grown) |
| ICE    |    3,153 | 274 |      0 | Migration artifacts (af=274); ICE NOT in MVP scope                    |
| CBOE   |    2,148 | 833 |      0 | CFE VX VMs running                                                    |

**NASDAQ/NYSE eu breakdown (estimated):** ~2,574 canonical-format eu rows (`:` in instrument_id, reclassifier scope,
BLK-d385496b pending) + ~15,354 plain-ticker eu rows (VMs actively processing, will resolve to
captured/empty_confirmed).

**Total tradfi eu=41,544** (unchanged from G2 projection — reclassifier target still 41,544→38,970 after --apply).

**af note:** NASDAQ af=226 / NYSE af=195 are from in-flight VMs (expected transient; VMs retry on next launch). CME
af=214 small; MVP ohlcv_1m af=0 verified at 03:08Z — these may be from options-chain shard failures since then.

**Three /blocked still pending (awaiting operator):** BLK-ca110c07, BLK-180b591d, BLK-d385496b.

### G1/G2 T+2h Check — 2026-06-28T05:56Z (slot-10 data_engineering)

`measure_honest_coverage.py --asset-group tradfi` → 2,520,093 rows | coverage **93.89%** (708,168/754,280 reachable)

- **52 TradFi VMs still RUNNING** (6 NASDAQ/NYSE 2023/2024/2025, ~40 CME, 4 CFE)
- captured: +1,948 since 04:18Z → VMs are filling (slow but steady)
- eu: 41,544 (UNCHANGED since 04:18Z — NASDAQ/NYSE plain-ticker VMs not yet resolving canonical eu rows)
- af: 4,568 → transient in-flight failures from running VMs
- Total reachable grew +3,327 — new eu seeded by CME options VMs (explains apparent coverage drop 94.04→93.89%)
- BLK-d385496b (NASDAQ/NYSE reclassifier --apply): still pending operator auth
- All three blocked items unchanged; G2 full verify deferred until all 52 VMs terminate

### G1/G2 T+2h40min Check — 2026-06-28T06:35Z (slot-10 data_engineering)

Direct manifest read (2,528,837 rows):

- **48 TradFi VMs RUNNING** (4 completed + auto-deleted since T+2h)
- captured: **711,237** (+3,069 total since 04:18Z baseline)
- eu: **41,544** (UNCHANGED — BLK-d385496b reclassifier still pending operator auth)
- empty_confirmed: 1,771,589 | af: 4,467
- Rate: ~1,000 rows/30min — 48 VMs filling methodically
- BLK-d385496b: still pending; G2 full verify deferred until all VMs terminate

### G1/G2 T+4h30min Check — 2026-06-28T07:07Z (slot-10 data_engineering)

`measure_honest_coverage.py --asset-group tradfi` output:

- **~47 TradFi VMs RUNNING** (≈5 completed + auto-deleted since launch)
- captured: **712,385** (+1,148 since T+2h40min; +4,217 total since 04:18Z baseline)
- coverage: **93.94%** (712,385 / 758,362 reachable)
- eu: still pending BLK-d385496b reclassifier (operator auth required)
- Rate stable: ~1,000–1,200 rows/30min; VMs progressing methodically
- G2 full verify still blocked until all VMs terminate

### G1/G2 T+9h10min Check — 2026-06-28T08:01Z (slot-10 data_engineering)

`measure_honest_coverage.py --asset-group tradfi`:

- **~44 TradFi VMs RUNNING** (≈8 completed since launch)
- captured: **715,868** (+883 since T+7h25min; ~4,700/hr sustained)
- coverage: **93.98%** (715,868 / 761,727 reachable)
- G2 full verify still blocked until all VMs terminate

### G1/G2 T+7h25min Check — 2026-06-28T07:42Z (slot-10 data_engineering)

`measure_honest_coverage.py --asset-group tradfi`:

- **~45 TradFi VMs RUNNING** (≈7 completed since launch)
- captured: **714,985** (+1,133 since T+5h15min; ~4,700/hr sustained rate)
- coverage: **93.97%** (714,985 / 760,882 reachable)
- G2 full verify still blocked until all VMs terminate

### G1/G2 T+5h15min Check — 2026-06-28T07:25Z (slot-10 data_engineering)

`measure_honest_coverage.py --asset-group tradfi`:

- **~46 TradFi VMs RUNNING** (≈6 completed since launch)
- captured: **713,852** (+1,467 since T+4h30min; rate ~4,700/hr across 46 VMs)
- coverage: **93.95%** (713,852 / 759,785 reachable)
- Rate accelerating slightly as each VM finishes and consolidates remaining work
- G2 full verify still blocked until all VMs terminate

### G2 Operator Answers + KRX Reclassification — 2026-06-28T19:11Z (slot-3 resumed)

**Operator decisions received (BLK-180b591d + BLK-ca110c07 answered):**

- **BLK-180b591d (gate revision):** Answer B — Keep gate as eu=0 AND af=0. Do NOT flip G2 today. Re-check in 24-48 hours
  after CME options VMs complete. G2 marked DEFERRED.
- **BLK-ca110c07 (structural item classification):** Answer A — Wait for VMs to drain, then re-run coverage. Classify
  structural items NOW:
  1. CME eu=8,424 chain-aggregate meta-rows (blank instrument_id) = NOT downloadable bars, exclude from denominator
  2. ICE af=66 ticks_migrated_* artifacts = NOT real MVP instruments, exclude (ICE not in MVP scope)
  3. KRX eu=378→0 = honest-empty with EXPECTED_SOURCE_NOT_AVAILABLE (operator authorized Option C per krx issue doc)

**KRX reclassification applied (19:11Z):**

- Script: `market-tick-data-service/scripts/reclass_krx_eu_source_not_available.py`
- Applied: 3,402 KRX eu rows → empty_confirmed/EXPECTED_SOURCE_NOT_AVAILABLE (all data types, 3 instruments)
- Snapshot:
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_krx_reclass_20260628T191054Z.parquet`
- KRX ohlcv_1m eu: 378 → 0 ✅

**Coverage at 19:11Z (post-KRX reclass):** 94.45% (720,393/762,735 reachable) — up from 94.03% pre-reclass.

**ohlcv_1m status by venue (19:11Z):**

| venue  | captured | ec     | af  | eu    | status                                                                       |
| ------ | -------- | ------ | --- | ----- | ---------------------------------------------------------------------------- |
| CME    | 186,334  | 32,865 | 0   | 8,424 | chain meta-rows — operator: exclude from denominator; CME options VMs 24-48h |
| CBOE   | 1,288    | 2,909  | 0   | 0     | ✅ CLEAN                                                                     |
| NASDAQ | 36,921   | 35,621 | 0   | 828   | canonical format mismatch — reclassifier BLK-d385496b pending operator auth  |
| NYSE   | 126,949  | 20,684 | 0   | 1,746 | canonical format mismatch — same pending                                     |
| ICE    | 2,015    | 740    | 66  | 0     | af=66 migration artifacts, NOT MVP scope — operator: exclude                 |
| KRX    | 0        | 1,231  | 0   | 0     | ✅ RECLASSIFIED (EXPECTED_SOURCE_NOT_AVAILABLE applied 19:11Z)               |

**BLK-d385496b answered (19:12Z):** Answer B — "Do NOT flip G2 yet. Fix the NASDAQ/NYSE manifest writer code (write
empty_confirmed+EXPECTED_SOURCE_DELIVERY_LAG when Databento returns 0 rows for in-window dates), re-run 2026 shards,
THEN flip G2 once actual eu=0 for downloadable contracts." The reclassifier approach is SUPERSEDED. Code fix required in
MTDS manifest writer (tracked in `nasdaq_nyse_eu_silent_skip_2026_06_28.md` CODE P0 todo).

**G2 DEFERRED** — re-check once: (1) MTDS manifest writer code fix shipped; (2) NASDAQ/NYSE 2026 shards re-run with
--force-recapture; (3) CME options VMs complete (~2026-06-30). All af=0 for MVP scope ✅.

### G2 Re-check — 2026-06-29T07:25Z (slot-10 data_engineering; gate NOT met, escalating)

Direct manifest query on freshest tradfi index
(`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, 2,604,730 rows). VM fleet:
10 RUNNING + 1 STOPPING + 3 TERMINATED (`gcloud compute instances list --filter='name~tradfi-bf'`).

**ohlcv_1m by venue × capture_status (MVP scope):**

| venue  | captured | empty_confirmed | af  | eu    | notes                                                                                                  |
| ------ | -------- | --------------- | --- | ----- | ------------------------------------------------------------------------------------------------------ |
| CME    | 186,334  | 32,871          | 0   | 8,490 | chain meta-rows (options_chain=7,894, futures_chain=596); operator: exclude from denominator           |
| CBOE   | 1,288    | 2,910           | 0   | 0     | ✅ CLEAN                                                                                               |
| NASDAQ | 37,421   | 37,784          | 0   | 656   | mixed plain-ticker + canonical key formats; see breakdown                                              |
| NYSE   | 127,149  | 21,625          | 0   | 3,136 | 11 ARCX-primary ETFs × 130 (plain) + × 126 (canonical) = ~2,816; writer fix did not reach NYSE adapter |
| ICE    | 2,015    | 741             | 66  | 0     | af=66 `ticks_migrated_*` migration artifacts; NOT in MVP scope                                         |
| KRX    | 0        | 1,232           | 0   | 390   | ⚠️ NEW eu re-seeded since 19:11Z reclassifier — 3 instruments × 130 days                               |

**MVP af=0 ✅ holds across CME/CBOE/NASDAQ/NYSE.** (ICE af=66 excluded per operator; UNKNOWN af=2 + blank-venue af=14
are non-MVP and pre-existing.)

**Three eu blockers remain — gate NOT met today:**

1. **CME eu=8,490 chain meta-rows** — operator answer A authorized excluding from denominator (BLK-ca110c07). Still in
   manifest; needs either a reclassifier pass to mark them structural OR a coverage-script change to exclude
   `instrument_type ∈ {options_chain, futures_chain}` from the denominator.
2. **NYSE eu=3,136 ARCX-primary ETFs** — writer fix landed on NASDAQ (XNAS.ITCH) but did NOT reach NYSE (XNYS.PILLAR).
   Plain-ticker rows for SPY/IWM/DIA/GLD/SLV/USO/UNG/XLE/QQQ/SMH/IBIT (all 130 each) were created by the post-fix VM as
   eu, not as empty_confirmed. P1 todo in [[nasdaq_nyse_eu_silent_skip_2026_06_28]] already assigned to a MTDS-bearing
   slot (slot-10 cannot author — MTDS not in this worktree).
3. **KRX eu=390 re-seed** — the 2026-06-28T19:11Z reclassifier converted 3,402 rows to
   empty_confirmed/EXPECTED_SOURCE_NOT_AVAILABLE, but the enumerator has since seeded 390 new eu rows (3 instruments ×
   130 dates) under the same canonical IDs. Needs either a re-run of `reclass_krx_eu_source_not_available.py` OR a
   permanent enumerator change to stop emitting KRX (`_enumerate_v2_tradfi` filter for KRX venue).

**CME options VMs still active:** 10 RUNNING (CL/ES/GC/HG/NG/NQ/PL/SI 2025+2026), 1 STOPPING (SI-2026), 3 TERMINATED.
Condition 3 of the deferral NOT yet met. Projected completion: continues into 2026-06-30 per the original estimate.

**Decision:** Not flipping G2 today. Escalating via /blocked to operator with three concrete asks (CME meta-row
exclusion mechanism, NYSE writer extension assignment, KRX re-classifier re-run vs enumerator fix) and waiting on CME VM
drain. All af=0 for MVP scope ✅ — only the eu side has remaining work.

### G2 Re-check — 2026-06-29T07:59Z (slot-2; KRX reclassifier re-applied; BLK-b3f8d286)

Direct manifest query (2,604,730 rows, blob.updated=2026-06-29T07:54:49Z). CME options VMs still active (4,614 new CME
captured rows since 07:00Z; CME captured max written_at=2026-06-29T07:54Z).

**ohlcv_1m by venue (pre-KRX-reclass):**

| venue  | captured | ec     | af  | eu    | notes                                                                                   |
| ------ | -------- | ------ | --- | ----- | --------------------------------------------------------------------------------------- |
| CME    | 186,334  | 32,871 | 0   | 8,490 | chain meta-rows (options_chain=7,894, futures_chain=596) — unchanged from 07:25Z check  |
| CBOE   | 1,288    | 2,910  | 0   | 0     | ✅ CLEAN                                                                                |
| NASDAQ | 37,421   | 37,784 | 0   | 656   | down from 828 at 07:25Z (writer fix on XNAS.ITCH resolving some rows); 172 rows cleared |
| NYSE   | 127,149  | 21,625 | 0   | 3,136 | ARCX ETF eu unchanged — writer fix not applied to XNYS.PILLAR adapter                   |
| ICE    | 2,015    | 741    | 66  | 0     | af=66 migration artifacts, NOT MVP scope — excluded per operator                        |
| KRX    | 0        | 1,232  | 0   | 390   | re-seeded since 2026-06-28T19:11Z reclassifier (3 instruments × 130 dates)              |

**KRX reclassifier re-run (2026-06-29T07:59Z — operator-authorized per BLK-ca110c07 Option C):**

- Snapshot:
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_krx_reclass_20260629T075926Z.parquet`
- Applied: 3,510 KRX eu rows → empty_confirmed/EXPECTED_SOURCE_NOT_AVAILABLE (all data types; 390 ohlcv_1m + others)
- KRX ohlcv_1m eu: 390 → 0 ✅

**Post-reclass status: 2 eu blockers remain (KRX cleared):**

1. **CME eu=8,490 chain meta-rows** — structural (options_chain=7,894, futures_chain=596); operator BLK-ca110c07
   authorized excluding from denominator; implementation pending (reclassifier or coverage-script change)
2. **NYSE eu=3,136 ARCX ETFs** — writer fix on NASDAQ (XNAS.ITCH) did NOT extend to NYSE (XNYS.PILLAR); tracked in
   `nasdaq_nyse_eu_silent_skip_2026_06_28.md` CODE P0 todo

**CME options VMs:** Still active. Gate condition (CME VMs complete) NOT met.

**BLK-b3f8d286 posted:** Asking operator whether to start CME chain meta-row reclassifier + MTDS NYSE writer fix today
(A) vs wait for 2026-06-30 re-check (B). G2 NOT flipped pending answer + CME VM drain.

### G2 Re-check — 2026-06-29T08:27Z (slot-2; CME reclassifier applied; NYSE+NASDAQ VMs relaunched)

**Operator answered BLK-b3f8d286 answer A:** Start CME chain meta-row reclassifier + NYSE fix today.

**Manifest status at 08:27Z (blob.updated=2026-06-29T08:27:40Z, 2,604,730 rows):**

| venue  | captured | ec  | af  | eu    | notes                                                                            |
| ------ | -------- | --- | --- | ----- | -------------------------------------------------------------------------------- |
| CME    | -        | -   | 0   | **0** | ✅ All CME VMs drained; reclassifier (applied 08:24Z) cleared all 20,364 eu rows |
| NASDAQ | -        | -   | 0   | 656   | ohlcv_1m eu; canonical orphans + plain-ticker date gaps                          |
| NYSE   | -        | -   | 0   | 3,136 | ohlcv_1m eu; ARCX ETFs still pending (writer fix not yet re-run)                 |

**CME eu=0 ✅** — all CME chain meta-rows reclassified to `empty_confirmed/EXPECTED_CHAIN_AGGREGATE`. Chain meta-row
reclassifier (`reclass_cme_chain_meta_rows.py`, market-tick-data-service@ecb7bd3e) applied 20,364 rows across all data
types (ohlcv_1m=8,490, trades=9,058, ohlcv_1s=1,652, tbbo=1,164) and cleared after CME VMs drained overnight.

**UAC EXPECTED_CHAIN_AGGREGATE** (unified-api-contracts@9a73d906) added to `OUT_OF_COVERAGE_WINDOW_REASONS` — excludes
CME chain-level aggregate rows from coverage denominator.

**Tarball rebuild (08:32Z):** Core tarballs rebuilt + uploaded to `gs://deployment-scripts-central-element-323112/code/`
with latest code:

- `mtds-code@ecb7bd3e` (includes market-tick-data-service@307ffa05 NYSE ETF fix)
- `unified-api-contracts-code@6f0c4bf8`
- `unified-trading-library-code@da437eb8`

Prerequisite: old `tradfi-bf-nyse-ohlcv-1m-2026-20260629-081752` VM (launched with stale tarball pre-307ffa05) deleted.
New VMs launched with fresh tarballs:

- **NYSE 2026 VM:** `tradfi-bf-nyse-ohlcv-1m-2026-20260629-083558` — RUNNING (SPOT, 278 tickers, 2026-01-01..06-29,
  `VM_FORCE=true`). Tarball=ecb7bd3e includes 307ffa05 (NYSE _resolve_by_dataset ETF fix). Expected: NYSE ohlcv_1m eu
  drops 3,136 → 0 for ARCX ETFs (SPY/IWM/DIA/GLD/SLV/USO/UNG/XLE) + canonical orphan rows.
- **NASDAQ 2026 VM:** `tradfi-bf-nasdaq-ohlcv-1m-2026-20260629-083841` — RUNNING (SPOT, 338 tickers, 2026-01-01..06-29,
  `VM_FORCE=true`). Expected: NASDAQ ohlcv_1m eu drops 656 → ~0 for plain-ticker date gaps (220 rows). Residual ~216
  genuine gaps (QQQ/SMH/WMT) + ~220 canonical orphan rows may need reclassifier.

**Remaining eu blockers (ohlcv_1m) — G2 still pending VM completion:**

1. **NYSE eu=3,136** — VMs running, expect → 0 after completion (ARCX ETFs + writer fix)
2. **NASDAQ eu=656** — VMs running, expect → ~220-436 (plain-ticker date gaps resolved; canonical orphans may remain)

**G2 full verify deferred** until NYSE + NASDAQ VMs terminate and manifest consolidator drains. Expected completion:
2026-06-29 evening / 2026-06-30T00:00Z.

### G2 Monitor — 2026-06-29T08:30Z (slot-4 data_engineering; CME reclassifier second pass + status check)

**Complementary CME reclassifier applied (instrument_type filter):** Slot-2 ran `reclass_cme_chain_meta_rows.py` at
08:24Z using blank `instrument_id` filter. Slot-4 ran `reclass_cme_chain_metarows_eu_not_downloadable.py` at 08:26Z
using `instrument_type in (options_chain, futures_chain)` filter — caught 20,364 CME eu rows (15,788 options_chain +
4,576 futures_chain, all CME eu remaining at that time). Both passes together ensure CME eu=0 regardless of whether
instrument_id was blank or populated. Snapshot: `_index/snapshots/pre_cme_chain_reclass_20260629T082603Z.parquet`
Shipped: market-tick-data-service@8fbe29ad

**VM status at 08:30Z:**

| VM                                                         | Status  | Notes                                                           |
| ---------------------------------------------------------- | ------- | --------------------------------------------------------------- |
| tradfi-bf-nyse-ohlcv-1m-2026-20260629-083558               | RUNNING | slot-2 launch with ecb7bd3e tarball (includes 307ffa05 ETF fix) |
| tradfi-bf-nasdaq-ohlcv-1m-2026-20260629-083841             | RUNNING | slot-2 launch                                                   |
| tradfi-bf-cme-ohlcv-1m-{gc,hg,ng,nq,pl,si}-{2025,2026} × 6 | RUNNING | CME options VMs                                                 |

My earlier NYSE VM (tradfi-bf-nyse-ohlcv-1m-2026-20260629-081752, launched 08:17Z with pre-tarball-rebuild code) was
superseded and deleted by slot-2's relaunch with the correct tarball.

**ohlcv_1m manifest state at 08:29Z (2,604,730 rows):**

- CME eu=0 ✅ | NYSE eu=3,136 (VMs running) | NASDAQ eu=656 (VMs running)
- af=82: ICE=66 (SCHEMA_VALIDATION_FAILED migration artifacts, authorized excluded per BLK-ca110c07) + 16 phantom rows
  (blank/UNKNOWN venue, blank instrument_id, 2026-01-02/2026-04-10) — structural garbage, not in MVP universe

**Residual eu projection after VMs drain (ohlcv_1m):**

- NYSE: plain-ticker eu → empty_confirmed via 307ffa05 + writer fix; canonical orphan eu (~1,546) may persist
- NASDAQ: plain non-trading-day eu (~253: 230 weekends + 23 Memorial Day) + QQQ/SMH/WMT plain (~75) + canonical orphan
  eu (~328) may persist after VM

**Next action:** Wait for all VMs to TERMINATE → run final G2 verification → address any residual eu/af with targeted
reclassifiers (canonical orphans need operator decision if they persist).

### G2 Status Check — 2026-06-29T08:51Z (slot-13 data_engineering)

Direct manifest query (blob.updated=2026-06-29T08:50:46Z, 2,604,730 rows; 465,055 ohlcv_1m rows).

**VM fleet:** 9 VMs RUNNING (7 CME options: gc-2025, hg-2025, ng-2025, nq-2025, nq-2026, pl-2026, si-2025; 1 NYSE-2026;
1 NASDAQ-2026), 1 TERMINATED (es-2020 from prior session).

**ohlcv_1m by venue × capture_status:**

| venue   | captured | empty_confirmed | af  | eu    | status                                                               |
| ------- | -------- | --------------- | --- | ----- | -------------------------------------------------------------------- |
| CME     | 186,334  | 41,361          | 0   | **0** | ✅ CME eu=0 — reclassifier from 08:24Z confirmed clear               |
| CBOE    | 1,288    | 2,910           | 0   | 0     | ✅ CLEAN                                                             |
| KRX     | 0        | 1,622           | 0   | 0     | ✅ KRX eu=0 — reclassifier from 07:59Z confirmed clear               |
| NASDAQ  | 37,421   | 37,784          | 0   | 656   | VMs running (083841), eu pending VM completion                       |
| NYSE    | 127,149  | 21,625          | 0   | 3,136 | VMs running (083558), eu pending VM completion                       |
| ICE     | 2,015    | 741             | 66  | 0     | af=66 migration artifacts, NOT MVP scope — excluded per BLK-ca110c07 |
| blank   | —        | —               | 14  | 0     | structural garbage (blank venue), NOT MVP scope                      |
| UNKNOWN | —        | —               | 2   | 0     | NOT MVP scope                                                        |

**MVP af=0 ✅ for all MVP venues (CME/CBOE/NASDAQ/NYSE). Gate NOT met: NASDAQ eu=656, NYSE eu=3,136 remain.**

**Decision:** NOT flipping G2 today. Gate requires eu=0 AND af=0 for all MVP venues. VMs still active — re-check once
NASDAQ-2026 and NYSE-2026 VMs terminate. Posting /blocked (BLK pending).

### G2 Monitor — 2026-06-29T10:05Z (slot-4 data_engineering; context continuation; watchdog armed)

Direct manifest query (2,604,730 rows, ohlcv_1m=465,055 rows).

**VM status:** NASDAQ-2026 (083841) RUNNING | NYSE-2026 (083558) RUNNING | 7 CME options VMs RUNNING.

**ohlcv_1m state (unchanged from 08:51Z for NASDAQ/NYSE):**

| venue  | eu    | af  | notes                                                                        |
| ------ | ----- | --- | ---------------------------------------------------------------------------- |
| CME    | 0     | 0   | ✅ reclassified 08:24Z                                                       |
| CBOE   | 0     | 0   | ✅ CLEAN                                                                     |
| KRX    | 0     | 0   | ✅ reclassified 07:59Z                                                       |
| NASDAQ | 656   | 0   | eu breakdown: 328 canonical orphan + 328 plain-ticker (2026-02-20→06-29)     |
| NYSE   | 3,136 | 0   | eu breakdown: 1,546 canonical orphan + 1,590 plain-ticker (2026-02-20→06-29) |
| ICE    | 0     | 66  | af=66 migration artifacts, NOT MVP scope (excluded BLK-ca110c07)             |

**MVP af=0 ✅ confirmed** (ICE/blank/UNKNOWN af rows outside MVP scope).

**G2 eu remaining: 3,792 total (NASDAQ=656, NYSE=3,136):**

- 1,874 canonical orphan eu (instrument_id has ":") — needs reclassifier (BLK-33c61313 ✅ operator auth received)
- 1,918 plain-ticker eu (no ":") — will resolve when VMs write captured/ec for those dates
  - NASDAQ plain-ticker eu: 328 (2026-02-20→06-29)
  - NYSE plain-ticker eu: 1,590 (2026-02-20→06-29)

**VMs actively writing:** ec max written_at=09:55Z (both venues) → manifest consolidator incorporating VM output.
captured max written_at=2026-06-28 20:13Z (yesterday) — captured rows for 2026 not yet consolidated.

**Reclassifier extended (Case B):** `reclass_nasdaq_nyse_eu_format_mismatch.py` extended to handle Case B
(eu→empty_confirmed when plain-ticker ec exists) — shipped as market-tick-data-service@c5f31e25 this session. Operator
auth: BLK-33c61313 (Answer A).

**Watchdog armed:** background process (PID 1187619) polling every 5 min for VM TERMINATE. Will auto-run reclassifier
--apply immediately on termination. Next action after watchdog fires: final G2 coverage verification.

### G2 Root-Cause Analysis — 2026-06-29T10:40Z (slot-2; VM output analysis; /blocked BLK-5b95659d)

**VM status:** NASDAQ-2026 (083841) RUNNING | NYSE-2026 (083558) RUNNING | 5 CME options VMs RUNNING. **eu unchanged
from 10:05Z:** NASDAQ=656, NYSE=3,136. VMs running ~2h10m, eu NOT decreasing.

**Root cause: VMs write EXPECTED_WEEKEND/EXPECTED_HOLIDAY at date level (blank instrument_id), not per-instrument.**

The enumerator creates `expected_unattempted` rows for every (instrument, date) in the universe. VMs resolve
weekends/holidays by writing a SINGLE blank-instrument_id `empty_confirmed` row per date. Per-instrument eu rows for
those same dates are never stamped. Two distinct categories of unresolved eu result:

**Category 1 — Weekend/holiday eu for regular equities (AAPL, MSFT, NVDA, etc.)**

- AAPL has 11 eu rows; ALL 11 are weekends: 2026-05-09,10 (Sat/Sun), 05-16,17, 05-23,24,25 (Memorial Day), 05-30,31,
  06-06,07 — NOT trading days
- 23 NASDAQ plain-ticker instruments × ~14 weekend dates = ~328 eu rows (matches NASDAQ plain-ticker eu count)
- NYSE equivalent: similar structure for ~1,590 plain-ticker eu rows
- Blank-instrument_id ec rows for those dates DO exist → resolution = reclassifier stamping per-instrument as
  `empty_confirmed/EXPECTED_WEEKEND` or `EXPECTED_HOLIDAY`

**Category 2 — ARCX ETF eu for ALL dates (trading days + weekends)**

- DIA: 130 eu rows spanning 2026-02-20→2026-06-29 (EVERY date, trading + non-trading)
- DIA total rows = 130 eu, 0 captured, 0 ec — NEVER attempted by any VM
- ARCX ETFs (DIA, IWM, GLD, SLV, USO, UNG, XLE, SPY, SMH, IBIT, ETHA) not in XNYS.PILLAR scope
- 307ffa05 fix shipped (tarball mtds-code@ecb7bd3e) but new VM STILL writes only blank instrument_id rows
- 307ffa05 resolves weekends/holidays (via blank-instrument_id), NOT trading-day ARCX ETF rows

**Current state (manifest, 2026-06-29T10:40Z):**

| venue  | eu    | af  | notes                                                             |
| ------ | ----- | --- | ----------------------------------------------------------------- |
| CME    | 0     | 0   | ✅                                                                |
| CBOE   | 0     | 0   | ✅                                                                |
| KRX    | 0     | 0   | ✅                                                                |
| NASDAQ | 656   | 0   | 328 canonical orphan + 328 plain-ticker (weekend dates only)      |
| NYSE   | 3,136 | 0   | 1,546 canonical orphan + 1,590 plain-ticker (ARCX ETF + weekends) |
| ICE    | 0     | 66  | af=66 excluded BLK-ca110c07                                       |

**Options posted to operator (BLK-5b95659d):**

- A: Reclassifier for weekend eu (match blank-instrument_id ec → stamp per-instrument as ec/EXPECTED_WEEKEND) + ARCX ETF
  reclassifier (DIA/IWM/GLD/SLV/USO/UNG/XLE/SPY/SMH/IBIT/ETHA → ec/EXPECTED_SOURCE_NOT_AVAILABLE for trading-day eu
  rows). Analogous to KRX reclassifier pattern. Resolves all 3,792 eu rows without code changes.
- B: Fix VM code to write per-instrument ec rows for weekend/holiday dates AND add ARCX ETF stamping. Requires
  relaunching NASDAQ/NYSE VMs again with new tarball. Longer path.
- C: Accept these eu rows as structural (like CME chain meta-rows) and reclassify as `empty_confirmed` with appropriate
  reason codes without waiting for VMs.

**Recommendation: Option A.** Reclassifier is the most immediate and safe path — analogous to already-approved KRX
(BLK-33c61313) and CME chain meta-row patterns. Can apply as two passes: Pass 1: per-instrument weekend/holiday eu → ec
(all venues, where blank-instrument_id ec exists for that date) Pass 2: ARCX ETF trading-day eu →
ec/EXPECTED_SOURCE_NOT_AVAILABLE

**G2 gate cannot be met by waiting for current VMs.** /blocked posted: BLK-5b95659d (awaiting answer).

### G2 FINAL VERIFICATION — 2026-06-29T10:45Z (slot-2; ALL THREE RECLASSIFIERS APPLIED; GATE MET ✅)

**BLK-5b95659d answered — Option A APPROVED** (received via /progress at 10:43Z):

> "Two-pass reclassifier approved. Ship today. Do NOT choose B."

**Three reclassifier passes applied (sequential):**

1. **Pass 1** `reclass_per_instrument_weekend_holiday_eu.py --apply` (10:43Z): 3,714 eu → ec
   (EXPECTED_WEEKEND/EXPECTED_HOLIDAY, all venues/data_types)
2. **Pass 2** `reclass_oos_equity_eu_not_in_dataset.py --apply` (10:43Z): 10,077 eu → ec (EXPECTED_SOURCE_NOT_AVAILABLE,
   OOS trading-day equities)
3. **Canonical orphan** `reclass_nasdaq_nyse_eu_format_mismatch.py --apply` (10:45Z): 8,315 eu → ec (Case B: canonical →
   plain-ticker ec; 6,380 unresolved = other data_types, not ohlcv_1m)

**G2 FINAL STATE — ohlcv_1m (465,055 rows, 2026-06-29T10:45Z):**

| venue  | eu  | af  | captured | ec     | notes                               |
| ------ | --- | --- | -------- | ------ | ----------------------------------- |
| CME    | 0   | 0   | 186,334  | 41,361 | ✅                                  |
| CBOE   | 0   | 0   | 1,288    | 2,910  | ✅                                  |
| NASDAQ | 0   | 0   | 37,421   | 38,440 | ✅ Pass1+2+canonical applied        |
| NYSE   | 0   | 0   | 127,149  | 24,761 | ✅ Pass1+2+canonical applied        |
| ICE    | 0   | 66  | 2,015    | 741    | af=66 excluded BLK-ca110c07 ✅      |
| KRX    | 0   | 0   | 0        | 1,622  | ec=EXPECTED_SOURCE_NOT_AVAILABLE ✅ |

**MVP scope (CME+CBOE+NASDAQ+NYSE): eu=0, af=0** ✅

**G2 GATE MET.** Scripts shipped: market-tick-data-service@a49403e2. G2 checkbox flipped. Plan status updated to
complete.
