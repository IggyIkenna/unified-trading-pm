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
> **🟡 GATED on Phase 0** — does NOT begin until `mvp_catalogue_finalization_v10_2026_06_27.md` has signed off a
> v10-correct, honest-coverage-clean **tradfi** catalogue (incl. the CME OPTION definitions). A tradfi MTDS download
> against a stale catalog writes ~0 rows. Confirm Phase-0 G3 sign-off before launching.
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

- [ ] [SCRIPT] P0. Confirm Phase-0 tradfi catalogue sign-off (incl. CME OPTION rows present) before any download. Repo:
      `unified-trading-pm` (read the coordinator plan) + `instruments-service`. **Gate:**
      `mvp_catalogue_finalization_v10_2026_06_27.md` Progress Log shows tradfi G3 green;
      `audit_instrument_definition_completeness.py --asset-group tradfi` shows OPTION cells. If not signed off → wait
      (task-level prereq), do not launch. SPOT N/A.
- [ ] [SCRIPT] P0. Build the tradfi gap report: for the v10 MVP universe (CME futures roots
      ES/NQ/VX/GC/SI/PL/PA/NG/CL/HG + the new CME OPTION roots + the equity twins in
      `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`), measure
      `captured / empty_confirmed / attempted_failed / expected_unattempted` for **ohlcv_1m**. Repos:
      `instruments-service`, `e2e-testing`. **Run:** `python scripts/measure_honest_coverage.py --asset-group tradfi`
      and read the `by_venue_data_type` breakdown for ohlcv_1m; list the (venue, root, year) cells with
      `attempted_failed > 0` or `expected_unattempted > 0`. **Gate:** a concrete gap list (venue×root×year) written to
      the Progress Log; if attempted_failed/expected_unattempted are already 0 for ohlcv_1m across the MVP universe,
      tradfi is DONE — record + skip the fill todos. SPOT N/A (read-only).

### G1 — fill the gaps (SPOT VMs only, ohlcv_1m only)

- [ ] [SCRIPT] P0. CME futures + options ohlcv_1m gap-fill. Repo: `deployment-service`. **SPOT VMs only**
      (`launch-tradfi-bf-cme-ohlcv-1m.sh` defaults SPOT). **Set ohlcv_1m ONLY** (NOT the lib default
      `ohlcv_1m;ohlcv_1s`):
      `TRADFI_OHLCV_DATA_TYPES=ohlcv_1m bash scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --dry-run` to inspect, then
      launch only the gap roots/years from G0 (`--only-root <ROOT> --year <YYYY>` per missing cell, or full fleet if the
      gap is broad). The CME root universe (futures+options as `<ROOT>.FUT;<ROOT>.OPT`) covers
      ES/NQ/GC/SI/PL/PA/NG/CL/HG + event contracts; window 2019-01-01→yesterday (GLBX.MDP3 full coverage). **Gate:** VMs
      STARTED <60s, `MANIFEST_PER_VM_SHARDS=true`, self-stop on completion; verify T+10min via
      `gcloud compute instances list --filter='name~tradfi-bf-cme' --zones=asia-northeast1-c`. Re-run
      `measure_honest_coverage.py --asset-group tradfi` → CME ohlcv_1m attempted_failed=0. No-fire-and-forget.
- [ ] [SCRIPT] P0. VIX/VX ohlcv_1m gap-fill (VIX = VX-futures via XCBF.PITCH; Barchart RETIRED). Repo:
      `deployment-service`. **SPOT VMs only.** Use `launch-tradfi-bf-cfe-ohlcv-1m.sh` (CFE `XCBF.PITCH` VX futures) with
      `TRADFI_OHLCV_DATA_TYPES=ohlcv_1m`. Honor the documented VIX 15m known-gap (`EXPECTED_KNOWN_SOURCE_GAP`
      2025-11-13→today−60d) — that window is honest-empty, NOT a gap to fill. **Gate:** VX ohlcv_1m attempted_failed=0
      except the documented known-gap window (which stays `empty_confirmed`). Verify T+10min. SPOT VMs only.
- [ ] [SCRIPT] P0. Equity-twin ohlcv_1m gap-fill (NASDAQ/NYSE equity backing the Binance equity-perps in
      `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`). Repo: `deployment-service`. **SPOT VMs only.** Use
      `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` + `launch-tradfi-bf-nyse-ohlcv-1m.sh` with
      `TRADFI_OHLCV_DATA_TYPES=ohlcv_1m`; floors auto-clip to 2023-04-15 (Databento equity coverage) — pre-2023 cells
      are honest `EXPECTED_PRE_SOURCE_COVERAGE_START`, do NOT launch pre-floor shards. Launch only the gap years from
      G0. **Gate:** equity-twin ohlcv_1m attempted_failed=0 from the 2023-04-15 floor; verify T+10min. SPOT VMs only.

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

_(append gap report + per-step verification here)_
