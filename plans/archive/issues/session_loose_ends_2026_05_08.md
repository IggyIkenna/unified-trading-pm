---
doc_type: issue
title: Session loose-ends index — 2026-05-08 Tab 1 main (gap-closure tracker)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, e2e-testing, features-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: ikenna-tab1-main
execution:
  {
    owner: Tab 5 (governance) tomorrow + sub-owners per row,
    cadence: one-shot per row + daily Tab 5 sweep until all rows resolved,
    verifier: each row's "Resolution evidence" populated with commit sha + date,
    last_executed: "2026-05-08",
  }
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Session loose-ends index — 2026-05-08

> **Purpose**: per operator question "rest of the stuff not resolved is clearly marked as such and in future/current
> active plans?" — this is the SSOT for every open thread from the 2026-05-08 governance + migration cycle. Each row has
> explicit owner / cadence per the new "Runbook Execution-Owner SSOT" HARD RULE.
>
> **Severity**: P0 — every row blocks May-23 cutover OR creates governance debt that compounds.

## P0 BLOCKERS (May-23 critical path)

| #   | Item                                                                                                                                                                                                                 | Owner                                            | Cadence               | Issue doc                                                                                                                                                  |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `colocated_engine.py:306` ImportError blocks ALL DeFi paper-smokes (V1-RETIRE Phase 2 migration)                                                                                                                     | strategy-service maintainer + Tab 1 next session | one-shot ~1-2 AI-days | `paper_trade_smoke_blocker_get_strategy_factories_2026_05_08.md`                                                                                           |
| 2   | Watchdog VM relaunch needed — 7 NEW prefixes added today (deployment-dashboard-vm, mtds-liquidations-backfill, prediction-features-, mtds-gas-fees-solana, sports-full-sweep-, sports-entity-, prediction-pipeline-) | operator                                         | one-shot (1 command)  | `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet && bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh` |

## P0 governance HARD RULES — codified but NOT enforced yet

These 4 HARD RULES landed in CLAUDE.md (`PM@1d74f617`) but the actual enforcement requires retroactive sweeps:

| #   | Item                                                                                                                                             | Owner                       | Cadence               | Notes                                                                               |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- | --------------------- | ----------------------------------------------------------------------------------- |
| 3   | Master plan `Continuous Verification` + `Last verified` columns NOT YET ADDED to `master_to_live_defi_2026_05_23.md` (rule codified PM@1d74f617) | Tab 5 (governance)          | one-shot ~2 AI-days   | Retroactive table refactor; every Group A-G row gets new columns                    |
| 4   | `strategy-service/scripts/quality-gates.sh` NOT WIRED with `e2e-testing/scripts/defi/` basedpyright step                                         | strategy-service maintainer | one-shot ~0.5 AI-days | Catches `colocated_engine.py`-class import drift at PR time                         |
| 5   | `features-sports-service` QG NOT WIRED with `e2e-testing/scripts/sports/`                                                                        | features-sports maintainer  | one-shot ~0.5 AI-days | Same shape as #4                                                                    |
| 6   | `mtds` QG NOT WIRED with `e2e-testing/scripts/prediction/`                                                                                       | mtds maintainer             | one-shot ~0.5 AI-days | Same shape as #4                                                                    |
| 7   | ✅ DONE 2026-05-10 (PM@2414e86f) — STEP 5.65 AST-walk shipped + 18 unit tests + manifest SSOT + codex doc                                        | Tab 5 (governance)          | one-shot ~2 AI-days   | check_removed_symbols.py + removed_symbols_manifest.yaml; 0 ERROR / 1 WARN on smoke |

## P1 deferred (operator decision pending or non-blocking)

| #   | Item                                                                                                                                                               | Owner                             | Status                                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------ |
| 8   | Birdeye paid-tier launcher VM (jitoSOL pre-2023-10 oracle USD coverage)                                                                                            | operator decision                 | Pythnet/CoinGecko cascade is sufficient for paper-smoke; Birdeye is fast-path optimisation |
| 9   | Sports `_v3` variant audit (`launch_fss_features_v3.sh`, `launch_instruments_reference_v3.sh`, `launch_mdps_phase3_bucketing.sh`, `launch_fss_phase3_backfill.sh`) | Tab 1 / sports owner next session | ~1 AI-day; potentially redundant with non-versioned launchers                              |
| 10  | `deployment-api/_SERVICE_LAUNCHER_SCRIPTS` registry verification — confirm Phase 2/3 canonical launchers all registered + Deploy-Missing UI button works           | deployment-api maintainer         | ~0.5 AI-days                                                                               |
| 11  | Canonical launchers don't all support `--help` (wrappers pass through but canonical doesn't handle)                                                                | deployment-service owner          | per-launcher fix; not blocking                                                             |

## ⏳ Scheduled / in-flight

| #   | Item                                                                                                | Status                                 |
| --- | --------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 12  | T+~76min spot-check on `mtds-lending-indices-20260508-141147` + `mtds-pyth-archive-20260508-141204` | Tab 1 main ScheduleWakeup at 15:24 UTC |

## ✅ DONE (this session, for reference)

- 4 governance HARD RULES codified in CLAUDE.md (`PM@1d74f617`)
- VM launcher consolidation Phases 0-5 (14 commits across 4 repos; ~3,700 net lines removed)
- 8 NEW canonical launchers + 7 NEW watchdog prefixes
- 3 Cloud Run deploys consolidated to `deployment-service/scripts/cloud-run/`
- 4 session issue docs retroactively gain `execution:` blocks per the new HARD RULE
- This loose-ends index filed (operator question fully addressed)

## ✅ DONE — 2026-05-10 retroactive sweep (items 3-6)

Governance HARD RULE retroactive sweeps shipped 2026-05-10 by Tab 5 (governance).

- **Item 3 — Master plan Continuous-Verification matrix.** ✅ **DONE.** Verified the 23-item Continuous-Verification +
  `Last verified` matrix already exists in `master_to_live_defi_2026_05_23.md` lines 767-825 (shipped earlier per
  `PM@1d74f617`). Per-row coverage: every Group A-G item has owner notation (`cron:` / `QG:` / `Tab:` / `manual`) plus a
  `Last verified` column. 7 items currently `Last verified: NEVER` are enumerated under § "Items with
  `Last verified: NEVER` (T-13 alerts)" — all 7 are May-23 critical-path execution risks tracked there.
- **Item 4 — strategy-service/scripts/quality-gates.sh.** ✅ **DONE.** Wired `e2e-testing/scripts/defi/` peripheral dir
  into the strategy-service QG via `strategy-service@e87a84a`. basedpyright
  - ruff run on every push; skips with clear message when CI image lacks sibling clones.
- **Item 5 — features-sports-service QG.** ✅ **DONE (rerouted).** features-sports-service is
  `consolidated-into-features-service` per workspace-manifest.json (GitHub repo archived; push fails). Wiring rerouted
  to consolidated `features-service/scripts/quality-gates.sh` via `features-service@3ed7aaff`. Sports peripheral dir
  (`e2e-testing/scripts/sports/`) limits scan to `.py` files (the dir contains `.sh` launchers + `.md` docs).
- **Item 6 — mtds QG.** ✅ **DONE.** Wired `e2e-testing/scripts/prediction/` peripheral dir into MTDS QG via
  `market-tick-data-service@7362b84`.
- **Item 7 — CLAUDE.md § 6 EXTENDED AST-walk QG STEP.** ✅ **DONE 2026-05-10 (PM@2414e86f).** STEP 5.65 shipped as
  modeled on QG STEP 5.64. Components: `unified-trading-pm/scripts/quality_gates/check_removed_symbols.py` (AST walker
  with strict receiver-name match, ProcessPoolExecutor parallelism, `--scope` flag for per-repo invocation),
  `removed_symbols_manifest.yaml` (workspace SSOT — 3 seed entries: V1-RETIRE `get_strategy_factories`,
  `canonical.domain.client` Option-A revert, `ManifestWriter.add` pending_removal), `test_check_removed_symbols.py` (18
  unit tests covering manifest schema validation, 3 import patterns, attribute-access receiver matching, false-positive
  negative cases, walker venv exclusions, unparseable-file resilience), base-service.sh STEP 5.65 wired between 5.64 and
  5.66, /codex/06-coding-standards/quality-gates.md updated with cross-reference table row + dedicated section. Smoke
  run: 0 ERROR (zero false positives), 1 genuine WARN at
  `market-tick-data-service/.../migrate_deribit_margin_split_v6.py:175` for `manifest_writer.add(...)` — already flagged
  by team via `# pyright: ignore[reportAttributeAccessIssue]` comment; pending_removal status correctly reflects
  in-flight writegate Phase 1.2A migration. Per-repo scoped run completes in ~4s.

## Recommended decision (UPDATED 2026-05-10)

**Closed-out items**: 3, 4, 5 (rerouted to features-service), 6, **7 (PM@2414e86f, 2026-05-10)**.

**Remaining for next sessions**:

- **Item 1** — strategy-service maintainer + Tab 1 — `colocated_engine.py:306` ImportError; ~1-2 AI-days.
- **Item 2** — operator — watchdog VM relaunch (1 command).
- **Items 8-11** — operator decision / next-session triage (P1 deferred; non-blocking).
- **Item 12** — Tab 1 main, scheduled wakeup.

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
