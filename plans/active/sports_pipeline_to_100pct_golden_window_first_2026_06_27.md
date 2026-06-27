---
doc_type: plan
title: "Sports pipeline to 100% — golden-window-first (sports automation coordinator)"
parent_epic: sports_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
execution_scope: local-only # COORDINATOR / tracker — NOT ingested; the 10 child plans carry the dispatchable work
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-06-27
related_plans:
  # --- the 10 dispatchable children (this coordinator's DAG) ---
  - plans/active/sports_p0_spot_vm_launchers_2026_06_27.md
  - plans/active/sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md
  - plans/active/sports_p1_golden_window_apifootball_2026_06_27.md
  - plans/active/sports_p1_golden_window_reference_sources_2026_06_27.md
  - plans/active/sports_p1_golden_window_mtds_odds_2026_06_27.md
  - plans/active/sports_p1_golden_window_features_2026_06_27.md
  - plans/active/sports_p1_golden_window_e2e_gate_2026_06_27.md
  - plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md
  - plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md
  - plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md
  - plans/active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md
  # --- existing plans this set LEANS ON / re-homes from (do not duplicate) ---
  - plans/active/sports_manifest_canonicalisation_2026_06_01.md
  - plans/active/sports_reference_backfill_oom_2026_06_22.md
  - plans/active/instruments_foundation_completeness_2026_06_24.md
  - plans/active/data_completion_to_100_all_ag_2026_06_21.md
  - plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md
  - plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md
summary: | #      | Requirement                                                                                                        | Definition of done                                                   ...
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-27
depends_on: []
last_updated: 2026-06-27
---

> **🟢 COORDINATOR (read-only map). This file is `execution_scope: local-only` — the orchestrator does NOT ingest it.**
> All dispatchable work lives in the 10 child plans listed in `related_plans` (each `assigned_vm: NA` +
> `assigned_role` + `execution_scope: orchestrator-agent`, `status: active` — role-based dispatch, no epic VM). This doc
> is the DAG + R1–R5 map + re-homed-work inventory + operator runbook. Update it (flip the child-status table) as
> children land; it is the R1–R5 burn-down tracker.

# Sports pipeline to 100% — golden-window-first

## What this delivers (the operator's 5 requirements)

| #      | Requirement                                                                                                        | Definition of done                                                                                                                                                                                                                                                                                                                                                                 |
| ------ | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R1** | Every API-Football **fixture** since 2015, **zero expected-missing**                                               | `expected_unattempted_pending_fetch == 0` for `(asset_group=sports, source=api_football, FIXTURES)` and the AF enrichment/core `data_types`, for `date ≥ each (source,data_type) coverage_start`, over the **94-league** canonical universe — every non-captured cell carries a typed `EXPECTED_*` reason (off-season / no-fixture / no-provider-coverage), never a blank/pending. |
| **R2** | API-Football **derived features** at the same completeness                                                         | features-service sports feature matrix is ML-ready (one row per `fixture × bucket`; NaN only where honest-absence) for the same window/history; feature manifest shows the same 4-state cleanliness.                                                                                                                                                                               |
| **R3** | **weather, SFI, transfer-market** + the other reference sources, **done daily** + backfilled                       | each non-AF source (open_meteo / soccerfootball_info / transfermarkt / understat / footystats) is zero-missing within its `coverage_start`, AND its daily-forward poll (sports-scheduler tier) is firing + verified.                                                                                                                                                               |
| **R4** | **catalogue daily rollup** scheduled daily + run-once-validated                                                    | `build_instrument_catalogue.py --asset-group sports` runs clean once (monotonic guard OK, non-zero rows, `catalog.parquet` written), AND the `lifecycle-catalogue-regen-sports` Cloud-Scheduler→Cloud-Run job fires daily (verified execution `SUCCEEDED`), AND `DP_CATALOG_NOT_RUNNING(sports)` is cleared.                                                                       |
| **R5** | **All backfill / manifest-consolidation / data-pipeline Slack alerts EMPTY** — no false errors, no unsolved errors | the sports-tagged `DP_*` active-alert state is zero across ≥2 consecutive monitor sweeps: `vm-census/active-dp-alerts*.json` has 0 sports entries; `catalog.parquet` <24h, sports `_index` <180min; `#data-pipeline-alerts` shows no unresolved sports WARN/CRITICAL — every real alert root-caused-closed (not muted), every false positive fixed.                                |

## Strategy — golden-window-first, then expand (operator directive)

> **Operator (`data_completion_to_100_all_ag_2026_06_21.md:2779`, and Directive B in
> `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:339-366`)**: _"pick a 3-month window
> where all leagues were viable + all data sources were available, and drive EVERY source × data_type to 100% for that
> window — proving the honest-coverage philosophy end-to-end (ironing out every code/manifest/GCS-path migration
> needed). THEN generalize the proven recipe to the rest of history. … Get the golden window down. If the golden window
> is not already done, then get API football going for the rest for those 94 leagues. Fixtures should be fairly quick,
> then get the enrichment stats going."_

- **Golden window (SSOT)** = **2025-09-01 .. 2025-11-30** (91 days; all 94 EU leagues in-season; all 8 sources past
  their `coverage_start`). Hard-coded in `instruments-service/scripts/reclassify_xg_blank_league_phantoms.py`
  (`_GOLDEN_WINDOW_START/END`) + audited by `instruments-service/scripts/run_fixture_completeness_audit_2026_06_25.py`.
- **94-league universe** = the canonical active set (`unified_api_contracts.sports` `LEAGUE_CLASSIFICATION_DATA` /
  `LEAGUE_REGISTRY`). The curated ~300-league **reference** expansion (burning the 6M AF credits) is **SEPARATE and OUT
  OF SCOPE here** — it stays in `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (Directive
  B/C). These plans drive the **94** to 100%; 94 remains the universe every downstream source/service cares about.
- **Smart-skip / season-aware (HARD)**: backfills fetch ONLY `(league, day)` cells that are not already honest-complete.
  Off-season days, no-fixture days, and pre-`coverage_start` days resolve to typed `EXPECTED_*` reasons via the UAC
  season calendar (`transfer_windows.py` `SEASON_BY_COUNTRY` + `get_league_fixture_calendar()` + `SOURCE_COVERAGE_START`
  / `DATA_TYPE_COVERAGE_START` in `league_data.py`) — NEVER blanket re-fetch, never label a legitimate no-fixture day as
  missing. Any league missing from the season calendar is a **fill-the-calendar** task, not a fetch.

## The DAG (10 child plans)

```
                ┌─────────────────────────────────────────────────────────────┐
   PHASE 0      │ P0  sports_p0_sourcing_and_honest_coverage_correctness        │  (code/data cleanup; makes
   (foundation) │     understat-404 #2 · path-shapes #5 · IS-ODDS-wipe #6 ·     │   coverage numbers trustworthy)
                │     phantom --unphantom re-run                                │
                └───────────────┬─────────────────────────────────────────────┘
                                │ prereq
   PHASE 1      ┌───────────────▼──────────┐ ┌──────────────────────────┐ ┌─────────────────────────┐
   (golden      │ P1a apifootball → 100%   │ │ P1b reference sources    │ │ P1c MTDS odds → 100%    │
    window      │     (fixtures+enrich+core)│ │     → 100% (wx/sfi/tm/   │ │     (odds-api + 3-league│
    2025-09..11)│                          │ │      understat/footystats)│ │      honest-absence)    │
                └───────────────┬──────────┘ └─────────────┬────────────┘ └────────────┬────────────┘
                                └──────────────┬───────────┴────────────────────────────┘
                                ┌──────────────▼───────────┐
                                │ P1d features → ML-ready   │
                                └──────────────┬───────────┘
                                ┌──────────────▼──────────────────────────────────────┐
                                │ P1e GOLDEN-WINDOW e2e GATE                           │  ◄── climbing metric:
                                │   manifest-clean + catalogue-run + alerts-zero       │      window 100% before expand
                                └──────────────┬──────────────────────────────────────┘
                                               │ prereq (window proven)
   PHASE 2      ┌────────────────────┐ ┌───────▼────────────────────────┐
   (expand to   │ P2a AF 2015→present│ │ P2b reference + odds 2015→pres │   (season-aware smart-skip;
    full history│   + G1 noise-wipe  │ │     within each coverage window │    re-uses the proven window recipe)
    + daily)    │   + G2 2015-17 dx  │ └───────────────┬─────────────────┘
                └─────────┬──────────┘                 │
                          └──────────────┬─────────────┘
                                ┌─────────▼──────────────┐
                                │ P2c features history    │
                                └─────────┬──────────────┘
                                ┌─────────▼───────────────────────────────────────────┐
                                │ P2d daily-forward + catalogue-daily + FINAL e2e GATE │  ◄── R3-daily + R4 + R5
                                │   (sports-scheduler tiers · catalogue scheduler ·    │      steady-state 100%/clean
                                │    zero-missing 2015→present · alerts-empty)         │
                                └──────────────────────────────────────────────────────┘
```

**Parallelism**: P1a/P1b/P1c run concurrently (3 agents) after P0; P2a/P2b concurrent after P1e. Each plan is ONE
agent's worth (one `quality-gates.sh`-green quickmerge unit); the DAG edges are expressed per-plan via `depends_on` +
the body `## Dependencies` note (the orchestrator gates dispatch via task-level `prereqs`).

## Child-plan status (flip as they land — this is the burn-down)

| Plan                                       | Phase | R-covers | depends_on  | status         |
| ------------------------------------------ | ----- | -------- | ----------- | -------------- |
| P0 sourcing+honest-coverage correctness    | 0     | R1,R5    | —           | ⬜ not started |
| P1a golden-window apifootball              | 1     | R1       | P0          | ⬜ not started |
| P1b golden-window reference sources        | 1     | R1,R3    | P0          | ⬜ not started |
| P1c golden-window MTDS odds                | 1     | R1,R5    | P0          | ⬜ not started |
| P1d golden-window features                 | 1     | R2       | P1a,P1b,P1c | ⬜ not started |
| P1e golden-window e2e gate                 | 1     | R4,R5    | P1a-d       | 🟡 partial — catalogue ✅ alerts=0 ✅ IS/MTDS 0/0/0 ✅; BLOCKED on P1d (features manifest empty; re-audit when P1d done) |
| P2a AF history 2015→present                | 2     | R1       | P1e         | ⬜ not started |
| P2b reference+odds history 2015→present    | 2     | R1,R3    | P1e         | ⬜ not started |
| P2c features history                       | 2     | R2       | P2a,P2b     | ⬜ not started |
| P2d daily-forward + catalogue + final gate | 2     | R3,R4,R5 | P2a,P2b,P2c | 🟡 partial — R4 ✅ (catalogue daily COMPLETED x5, catalog.parquet <24h) · R5 ✅ (alerts=0 across 2 sweeps, _index <180min) · R3-daily ✅ (scheduler RUNNING, TIER-1 fired); R1/R2/R3-history BLOCKED P2a/P2b/P2c not started; STAMP DONE deferred until P2a+P2b+P2c+task004 pass |

## Re-homed-work inventory (the "fold the dependencies back in" map)

Every open sports item below is **stranded on a non-vm-sports plan** and is re-homed into a child plan so it actually
gets dispatched + done. The source plans are annotated with a redirect banner pointing here (do NOT also dispatch them
there → double-dispatch).

| Stranded item                                                                             | Source plan (current owner)                                        | Re-homed into |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------- |
| understat per-league 404 scoping (#2 — built, pending ship)                               | `issues/sports_golden_window_attempted_failed_remediation` (no VM) | **P0**        |
| `candidate_parquet_paths` forward path-shape gap (#5 — blocks forward `--apply`)          | same issue doc (no VM)                                             | **P0**        |
| footystats odds KEPT in IS (#6 REVERSED — operator: predictive) + their #5 path-shape     | same issue doc + `instruments_foundation_completeness` (vm-cefi)   | **P0**        |
| phantom `--unphantom-only --apply` re-run (258 false phantoms)                            | same issue doc (no VM)                                             | **P0**        |
| AF enrichment golden-window gap (LINEUPS/EVENTS/STATS/INJURIES)                           | `data_completion_to_100_all_ag` (NA, local-only)                   | **P1a**       |
| TM PLAYER_VALUES 256 failures + ODDS/PREDICTIONS blank-reason relabel                     | `data_completion_to_100_all_ag` (NA) + issue doc                   | **P1b / P1c** |
| odds-api 3-league honest-absence (UEFA CL / China SL / Russia PL)                         | issue doc (no VM)                                                  | **P1c**       |
| G1 non-canonical-league NOISE wipe (1,437 leagues, ~106k rows)                            | `instruments_foundation_completeness` (vm-cefi)                    | **P2a**       |
| G2 2015–2017 zero-captured diagnosis (subscription-limit vs backfill-bug)                 | `instruments_foundation_completeness` (vm-cefi)                    | **P2a**       |
| G2 40,041 FIXTURES `attempted_failed` re-run (2018/2021/2023)                             | `instruments_foundation_completeness` (vm-cefi)                    | **P2a**       |
| catalogue all-AG producer crash (`instruments_handler.py:367`) → no sports daily producer | `instruments_foundation_completeness` (vm-cefi)                    | **P2d**       |
| daily forward-feed matrix (all data_types × sources)                                      | `data_completion_to_100_all_ag` (NA)                               | **P2d**       |

**Pre-existing sports plans (in-DAG nodes; still carry the deprecated `vm-sports` — the operator's frontmatter migration
re-tags them `NA` + role; do not re-home):** `sports_manifest_canonicalisation_2026_06_01` (manifest canonical E-walk;
its E3–E8 production `--apply` is gated on the cross-AG `master_data_canonicalisation` G4 operator hard-stop) and
`sports_reference_backfill_oom_2026_06_22` (the OOM single-index-read fix that every P1b/P2b reference backfill depends
on being shipped).

## Constraints + operator hard-stops (apply to every child)

- **SPOT VMs (HARD).** Every VM this plan set launches (all backfill VMs · the features VMs · the sports-scheduler) MUST
  be **spot/preemptible** — the cheap instances the cloud can reclaim and kill at any moment. Enforced by
  `sports_p0_spot_vm_launchers_2026_06_27.md` (Phase 0), which makes SPOT the forced default in the sports launchers
  (currently NONE support it). Safe because backfills are idempotent/skip-existing (a reclaimed VM relaunches + resumes)
  and the monitors are made preemption-aware so a reclaim is NOT a false `DP_VM_GONE_NO_CAPTURE` (preserves R5).
- **Role-based dispatch — NO epic VM (single-VM architecture, 2026-06-27).** Each child carries `assigned_vm: NA` +
  `assigned_role` (data_engineering / infra) + `execution_scope: orchestrator-agent` — the central orchestrator
  dispatches them **by ROLE, not VM** (epic VMs deprecated per CLAUDE.md; there is no `vm-sports` to start).
  `status: active` (already set) = the green-light; they ingest on the next role-based regen tick.
- **ODDS = MTDS for RAW bookmaker tick odds (odds-api).** EXCEPTION (operator 2026-06-27): footystats' own _predictive_
  odds + `PREDICTIONS` stay in IS (least-code, predictive reference — not raw market ticks). P0 KEEPS footystats `ODDS`
  (the earlier #6 removal is reversed).
- **Do NOT run forward phantom `--apply` on sports until P0 #5 ships** (`candidate_parquet_paths` must emit every real
  on-disk shape or the forward pass false-flags ~145k captured rows → `attempted_failed`). The reverse
  `--unphantom-only --apply` heal IS safe pre-#5.
- **Snapshot-first for every wipe/relabel** (`_index/snapshots/…` before delete) — reversible; consolidator paused
  during, resumed after.
- **Drop live sports trading while fixing** (operator): data-pipeline daily-forward is fine + wanted; live _trading_
  re-enable is a separate operator decision — do NOT re-arm sports live trading.
- **Operator hard-stops (human-only)**: the cross-AG `master_data_canonicalisation` G4 corpus `--apply`; any
  IRREVERSIBLE legacy-bucket delete; live ODDS quota-tier / second-source spend decision; live-trading re-enable. Agents
  prepare dry-run-green + STOP at these (structured `/blocked` with options).
- **Data-pipeline correctness is the heartbeat**: no asset-group/data-type skipped, no deadline descopes; the only
  legitimate deferral is operator-gated `BLOCKED-CREDENTIALS` / `-OPERATOR-DECISION` / `-UPSTREAM-OUTAGE`.

## Model / agent tier (answering "complexity → which agent")

The orchestrator picks the worker model from **plan frontmatter** at regen
(`agent-orchestrator/server/regen_backlog_from_plan.py`): `assigned_role:` → that role's model+thinking;
`model_tier: opus-required` → Opus override. Every child here is `assigned_role: data_engineering` = **Sonnet 4.6 /
thinking: high** — the maximum-reasoning Sonnet config ("Sonnet + literal `max` thinking" is not a legal combo:
`thinking: max` ⇒ Opus per `codex/06-coding-standards/model-tier-selection.md`; the legal max for Sonnet is `high`).
Tasks are broken finely so each is Sonnet/high-doable. **Escalation lever**: if a child hits a genuine
context/complexity wall (e.g. a cross-repo schema redesign), add `model_tier: opus-required` to THAT plan and push —
regen re-stamps its tasks to Opus next tick. `data_engineering` IS the backfill/pipeline-code executor role (its def:
"manifests, `capture_status`, … backfills + daily availability audits"); the alert-triage health-overseer the operator
described is the **separate** `data_pipeline_failure` role (`DP_*` escalation, Sonnet/medium) — not used to build these
plans.

## Codex SSOTs (read the one your child touches)

- `codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status` (v9), shard atom,
  `expected_unattempted` writer-materialised
- `codex/02-data/honest-absence-downstream-handling.md` — typed `EXPECTED_*` reasons, season/coverage clips, the
  golden-window effect
- `codex/02-data/sports-gcs-path-ssot.md` — sports layouts + `candidate_parquet_paths()`
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — Cloud-Run/Fargate consolidator, loud-fail-on-stale
- `codex/05-infrastructure/data-pipeline-alerts.md` (+ `.registry.yaml`) — DP\_\* taxonomy + "drive the alert count to
  zero"
- `codex/05-infrastructure/deployment-observability.md` — RESOLVED bookend, active-dp-alerts blobs
- `codex/02-data/data-pipeline-correctness-hard-rule.md`, `…/external-data-always-available-rule.md`

## References (lean on, do not duplicate)

- `sports_manifest_canonicalisation_2026_06_01.md` — manifest canonical CF-1…CF-14 E-walk (vm-sports)
- `sports_reference_backfill_oom_2026_06_22.md` — OOM single-index-read fix (vm-sports)
- `instruments_foundation_completeness_2026_06_24.md` — G0→G5 foundation gates (vm-cefi; sports slice re-homed here)
- `data_completion_to_100_all_ag_2026_06_21.md` — the 3-month golden-window execution strategy (NA/local-only)
- `issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` — the golden-window triage (#1-#6)
- `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — the curated ~300-league reference
  expansion (SEPARATE; out of scope here)

## Progress Log

- **2026-06-27** — Coordinator + 10 child plans authored (this set). Golden-window-first structure locked; stranded
  sports work re-homed off the deprecated epic VMs. Reassigned to `assigned_vm: NA` + `assigned_role` (role-based
  dispatch, single-VM architecture 2026-06-27) — no epic VM to start; children dispatch by role on the next regen tick.
