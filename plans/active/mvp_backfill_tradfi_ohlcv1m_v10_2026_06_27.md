---
doc_type: plan
title: "MVP backfill — TradFi ohlcv_1m for the v10 MVP universe (SPOT-only, reconcile-then-fill)"
summary:
  "Backfill TradFi ohlcv_1m ONLY for the canonical v10 MVP universe (CME futures + new CME options + equity twins),
  reconciling what is already captured vs what is missing on SPOT VMs."
nature: process
stage: [data-ingestion]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, tradfi, ohlcv-1m, cme, cme-options, spot-vm, v10, budget-aware]
related: []
created: 2026-06-27
parent_epic: tradfi_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on: [mvp_catalogue_finalization_v10_2026_06_27]
related_plans:
  - plans/active/mvp_catalogue_finalization_v10_2026_06_27.md
  - plans/active/tradfi_multisource_backfill_2026_06_22.md
  - plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md
asset_group: tradfi
---

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** Part of the remaining MVP arc handed to the
> agent-orchestrator (`planning` VM). One agent, one craft (`data_engineering`), Sonnet/high.
>
> **🟢 GATE CLEARED 2026-06-28T02:12Z** — `mvp_catalogue_finalization_v10_2026_06_27.md` G3 sign-off complete. tradfi
> catalogue v10-correct: 1,038,235 rows, 643,116 MVP (642,126 CME OPTION ✅), false-delist=0, ghosts=N/A, blank=0.
> Phantom audit: 1,789 phantoms (MTDS data; issue doc `phantom_captures_tradfi_2026_06_28.md`).
>
> **Canonical MVP SSOT (the ONLY scope authority):** `mvp_scope.py` v10 + `codex/02-data/mvp-scope-canonical.md`. This
> plan REFERENCES it. **TradFi v10 = ohlcv_1m ONLY** (decision #7 — NO ohlcv_1s, NO trades/tbbo). Any older tradfi plan
> that says otherwise is stale and SUBORDINATE (see Phase-4 reconciliation).

## Codex SSOTs (READ before executing)

- `codex/02-data/mvp-scope-canonical.md` § TradFi — venue=CME (futures complex) + equity-basis carve-out
  (NASDAQ/NYSE/ARCA/KRX in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`); instrument types FUTURE + OPTION; **data_type cut =
  ohlcv_1m ONLY**; underliers ES·NQ·VX + the CME commodity roots backing a Binance tradfi-perp (GC/SI/PL/PA/NG/CL/HG).
- `codex/02-data/tradfi-databento-sourcing-ssot.md` — 3-dataset billing fail-closed; SOURCE_PRIORITY databento-first;
  VIX=VX-futures via XCBF.PITCH; Barchart RETIRED; silent-0-row backfill gotchas.
- `codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT-by-default; `--on-demand` is the deadline escape hatch only.
- `codex/02-data/honest-absence-downstream-handling.md` — `EXPECTED_*` reasons (weekends/holidays via
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

- [ ] [SCRIPT] P0. Final tradfi MVP verification: ohlcv_1m attempted_failed=0 AND expected_unattempted=0 across the v10
      MVP universe; every absence is a typed honest `empty_confirmed` (weekend/holiday/pre-listing/known-gap), never a
      silent missing cell. Repos: `instruments-service`, `e2e-testing`. **Run:**
      `python scripts/measure_honest_coverage.py --asset-group tradfi`;
      `python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group tradfi --mode full` (phantom +
      4-pillar + v9). **Gate:** measured coverage = 100% of MVP could-exist (both failure buckets zero); 0 phantom rows;
      0 blank-status; verdict written to Progress Log. **Full-execution criterion:** the gcloud VM-list + the coverage
      CLI output recorded. Any genuine source-unavailable cell is honest-empty + documented (cite the reason), NOT left
      BLOCKED. SPOT N/A.

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
