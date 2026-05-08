---
title: "Session loose-ends index — 2026-05-08 Tab 1 main (gap-closure tracker)"
created: 2026-05-08
author: ikenna-tab1-main
execution:
  owner: Tab 5 (governance) tomorrow + sub-owners per row
  cadence: one-shot per row + daily Tab 5 sweep until all rows resolved
  verifier: each row's "Resolution evidence" populated with commit sha + date
  last_executed: "2026-05-08"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Session loose-ends index — 2026-05-08

> **Purpose**: per operator question "rest of the stuff not resolved is clearly marked as such and in future/current
> active plans?" — this is the SSOT for every open thread from the 2026-05-08 governance + migration cycle. Each row
> has explicit owner / cadence per the new "Runbook Execution-Owner SSOT" HARD RULE.
>
> **Severity**: P0 — every row blocks May-23 cutover OR creates governance debt that compounds.

## P0 BLOCKERS (May-23 critical path)

| # | Item | Owner | Cadence | Issue doc |
|---|------|-------|---------|-----------|
| 1 | `colocated_engine.py:306` ImportError blocks ALL DeFi paper-smokes (V1-RETIRE Phase 2 migration) | strategy-service maintainer + Tab 1 next session | one-shot ~1-2 AI-days | `paper_trade_smoke_blocker_get_strategy_factories_2026_05_08.md` |
| 2 | Watchdog VM relaunch needed — 7 NEW prefixes added today (deployment-dashboard-vm, mtds-liquidations-backfill, prediction-features-, mtds-gas-fees-solana, sports-full-sweep-, sports-entity-, prediction-pipeline-) | operator | one-shot (1 command) | `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet && bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh` |

## P0 governance HARD RULES — codified but NOT enforced yet

These 4 HARD RULES landed in CLAUDE.md (`PM@1d74f617`) but the actual enforcement requires retroactive sweeps:

| # | Item | Owner | Cadence | Notes |
|---|------|-------|---------|-------|
| 3 | Master plan `Continuous Verification` + `Last verified` columns NOT YET ADDED to `master_to_live_defi_2026_05_23.md` (rule codified PM@1d74f617) | Tab 5 (governance) | one-shot ~2 AI-days | Retroactive table refactor; every Group A-G row gets new columns |
| 4 | `strategy-service/scripts/quality-gates.sh` NOT WIRED with `e2e-testing/scripts/defi/` basedpyright step | strategy-service maintainer | one-shot ~0.5 AI-days | Catches `colocated_engine.py`-class import drift at PR time |
| 5 | `features-sports-service` QG NOT WIRED with `e2e-testing/scripts/sports/` | features-sports maintainer | one-shot ~0.5 AI-days | Same shape as #4 |
| 6 | `mtds` QG NOT WIRED with `e2e-testing/scripts/prediction/` | mtds maintainer | one-shot ~0.5 AI-days | Same shape as #4 |
| 7 | CLAUDE.md § 6 EXTENDED has NO QG STEP (today: reviewer-enforced; need AST-walk like QG STEP 5.64) | Tab 5 (governance) | one-shot ~2 AI-days | base-service.sh AST-walk for removed public symbols |

## P1 deferred (operator decision pending or non-blocking)

| # | Item | Owner | Status |
|---|------|-------|--------|
| 8 | Birdeye paid-tier launcher VM (jitoSOL pre-2023-10 oracle USD coverage) | operator decision | Pythnet/CoinGecko cascade is sufficient for paper-smoke; Birdeye is fast-path optimisation |
| 9 | Sports `_v3` variant audit (`launch_fss_features_v3.sh`, `launch_instruments_reference_v3.sh`, `launch_mdps_phase3_bucketing.sh`, `launch_fss_phase3_backfill.sh`) | Tab 1 / sports owner next session | ~1 AI-day; potentially redundant with non-versioned launchers |
| 10 | `deployment-api/_SERVICE_LAUNCHER_SCRIPTS` registry verification — confirm Phase 2/3 canonical launchers all registered + Deploy-Missing UI button works | deployment-api maintainer | ~0.5 AI-days |
| 11 | Canonical launchers don't all support `--help` (wrappers pass through but canonical doesn't handle) | deployment-service owner | per-launcher fix; not blocking |

## ⏳ Scheduled / in-flight

| # | Item | Status |
|---|------|--------|
| 12 | T+~76min spot-check on `mtds-lending-indices-20260508-141147` + `mtds-pyth-archive-20260508-141204` | Tab 1 main ScheduleWakeup at 15:24 UTC |

## ✅ DONE (this session, for reference)

- 4 governance HARD RULES codified in CLAUDE.md (`PM@1d74f617`)
- VM launcher consolidation Phases 0-5 (14 commits across 4 repos; ~3,700 net lines removed)
- 8 NEW canonical launchers + 7 NEW watchdog prefixes
- 3 Cloud Run deploys consolidated to `deployment-service/scripts/cloud-run/`
- 4 session issue docs retroactively gain `execution:` blocks per the new HARD RULE
- This loose-ends index filed (operator question fully addressed)

## Recommended decision

**Tomorrow's `work_split_2026_05_09_ikenna.md` Tab assignments**:

- **Tab 5 (governance)** — items 3 + 7 (~4 AI-days)
- **strategy-service maintainer** — items 1 + 4 (~2 AI-days)
- **features-sports maintainer** — item 5 (~0.5 AI-days)
- **mtds maintainer** — item 6 (~0.5 AI-days)
- **Tab 1 next session** — item 9 sports `_v3` audit (~1 AI-day)
- **deployment-api maintainer** — item 10 (~0.5 AI-days)
- **Operator** — item 2 watchdog relaunch (1 command) + item 8 Birdeye decision (5 min)

**Total tomorrow scope: ~10 AI-days** distributed across 6+ owners (highly parallel).

## Cross-references

- `cursor-configs/CLAUDE.md` PM@1d74f617 — 4 governance HARD RULES driving items 3-7
- `plans/active/defi_master_2026_05_07.md` § "Runbook execution-owner assignments" — companion table
- `plans/active/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "ALL PHASES COMPLETE" — items 9, 10, 11
- `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md` — original governance-gaps doc
- `plans/active/issues/paper_trade_smoke_blocker_get_strategy_factories_2026_05_08.md` — item 1
