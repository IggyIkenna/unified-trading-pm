---
title: "Sports phantom-recon diagnosis (SFI_STANDINGS / open-meteo) + coverage-window reconciliation"
parent_epic: sports_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/sports_master.md
  - ./sports_manifest_canonicalisation_2026_06_01.md
  - ../archive/2026_05/d2_uac_continuity_2026_05_20.md
---

> **Provenance**: extracted 2026-06-20 from the inline `sports_master` epic body during the asset-group-umbrella
> restructure (the L0 umbrellas carried stale May-07 inline todos the backlog regen never dispatched — it scans
> `plans/active/*.md`, never `plans/epics/`). Migrated from the epic's "Phantom recon + failure triage
> (`sports_phantom_recon_and_failure_triage`)" section (originally folded from
> `sports_phantom_recon_and_failure_triage_2026_05_01.md`).
>
> **Coverage-window note (d2 overlap check)**: the api-football (2015-vs-2018) + understat (2014-vs-2015)
> `SOURCE_COVERAGE_START` reconciliations are the SAME failure class d2 (`d2_uac_continuity_2026_05_20`, now ARCHIVED)
> built the general `SourceCapability.coverage_start` / `KNOWN_COVERAGE_GAPS` framework for. d2 wired the MECHANISM
> (oracle `is_before_source_coverage_start()`, cefi venue coverage_start) but did **not** reconcile these two specific
> sports per-(source,data_type) date-range mismatches — so the concrete reconciliation is unowned and extracted here.
> Use d2's `DATA_TYPE_COVERAGE_START` per-(source,data_type) override pattern as the canonical fix shape; do NOT rebuild
> the framework.

## Context

Sports phantom-recon is partly blocked on two silent-failure diagnoses and two coverage-window mismatches. The bulk
phantom-audit (slot-6 re-ran 2026-05-11) reported **16.8% phantom rate** for sports — WAY above the <0.5% bar, but
**almost certainly mostly false-positive** (the 2026-04-29 stale-sports-path-SSOT class: a stale `entity=odds/` vs
`entity=footystats_odds/` probe produced a false 26% ODDS phantom). The sports phantom dispatcher in
`reconcile_phantom_manifest_rows_all.py` must (a) use the CURRENT `candidate_parquet_paths` layout and (b) apply the UAC
`SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS` date-range clips before flagging. The
STANDINGS/SFI_LEAGUES/INJURIES clusters smell exactly like un-clipped pre-launch-date rows. **Do NOT `--apply` the
current 115,524 flagged rows** (would corrupt the manifest, 2026-04-29-class).

## P0 — silent-failure diagnosis

- [ ] [AGENT] P0. **SFI_STANDINGS 100% failed** (42/42 rows phantom 2026-04-29; all have empty `error_reason`). Diagnose
      whether the adapter or the upstream data is the cause; fix the side that's wrong (read both). Repo:
      instruments-service.
- [ ] [AGENT] P0. **open-meteo silent ≥2 days** (last `written_at` 2026-04-29 13:22 UTC). Diagnose the forward-poll
      path. Repo: instruments-service.

## P0 — coverage-window reconciliation (d2 override-pattern shape)

- [ ] [AGENT] P0. **api-football date-range starts 2015-01-01** but UAC declares `SOURCE_COVERAGE_START` 2018-01-01.
      Reconcile UAC vs reality using the `DATA_TYPE_COVERAGE_START` per-(source, data_type) override pattern (the
      canonical fix shape per CLAUDE.md + d2). Repo: unified-api-contracts.
- [ ] [AGENT] P0. **understat date-range starts 2014-01-01** but UAC declares `SOURCE_COVERAGE_START` 2015-01-16. Same
      per-(source, data_type) override reconciliation. Repo: unified-api-contracts.

## P0 — scoped recon run + drain wait

- [ ] [AGENT] P0. After the dispatcher + date-range-clip fixes land, run real recon **scoped to footystats first**
      (smallest, fastest to validate the clip logic against the current `candidate_parquet_paths` SSOT). Repo:
      instruments-service.
- [ ] [AGENT] P0. Wait for any in-flight `sfi-backfill-*` recon VMs to drain before the full re-run; verify STOPPED via
      `gcloud compute instances list` per the no-fire-and-forget rule. Then re-run
      `reconcile_phantom_manifest_rows_all.py --asset-group sports --dry-run` and `--apply`-flip ONLY the genuinely-real
      residual (never blanket-flip the current 115,524 — the 2026-04-29 false-positive class is the cautionary
      precedent).

## Success criteria

- SFI_STANDINGS + open-meteo silent-failures diagnosed (adapter-vs-upstream determined) and the wrong side fixed.
- api-football + understat `SOURCE_COVERAGE_START` reconciled to reality via the `DATA_TYPE_COVERAGE_START` per-(source,
  data_type) override; `KNOWN_COVERAGE_GAPS` reflects every probed gap.
- `reconcile_phantom_manifest_rows_all.py --asset-group sports --dry-run` reports <0.5% phantom rate after the
  dispatcher uses the current `candidate_parquet_paths` layout + applies the coverage-start/known-gap clips; the
  residual is classified by drift axis (zero unclassified); only the genuinely-real subset is `--apply`'d.
- `bash scripts/quality-gates.sh` green on `unified-api-contracts` + `instruments-service` before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the diagnoses are confirmed against real
adapter/upstream behaviour; the coverage-start reconciliation is validated against the real GCS earliest-data dates; the
scoped + full phantom-recon re-runs execute on a same-region VM and report the post-fix rate (<0.5%) with the residual
classified by drift axis.
