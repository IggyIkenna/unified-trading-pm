---
doc_type: plan
title: Infra/ops residual tail — forked from migration_verification_orphan_safety_2026_06_10
summary: >-
  9 residual todos forked verbatim out of the archived migration-verification/orphan-safety harness plan (2026-07-24
  plan line-cap remediation split) — the catch-all infra/ops/audit tail that didn't fit the other 3 named residual
  buckets (prediction-cqg, sports pre-launch+CF-5, defi-venue+lst-rates): the standing non-operator-gated full audit,
  the RESUME runbook un-pause, the rollup Cloud Run Job image-lag + unique_instruments precompute, the deployment-ui
  could-exist-vs-capture surfacing, local-dev flakiness, the legacy schema_version re-stamp, and 2 pointer-only items
  (MVP Phase 2-3, execution-config pre-flight) that the source explicitly said belong elsewhere.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [infra, ops, audit, manifest, migration, plan-split, residual]
related:
  [
    /plans/active/migration_verification_orphan_safety_2026_06_10.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: infra
drift_direction: advance-code
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/active/migration_verification_orphan_safety_2026_06_10.md` (its own main body A2/B
  sections + Progress Log entries dated 2026-06-12 through 2026-06-22) as part of the 2026-07-24 plan line-cap
  remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's
  durable protocol (CF-15…CF-21) had already migrated to codex; these 9 items were the last genuinely-open items that
  didn't fit the prediction-cqg / sports pre-launch+CF-5 / defi-venue+lst-rates residual buckets and are tracked here
  going forward.
---

# Infra/ops residual tail

> **Origin.** All 9 todos below are moved **verbatim** from
> `plans/active/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; full historical Progress
> Log archived to `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md` as an Appendix). 2
> of the 9 (`MVP Phase 2-3`, `Execution-config compatibility pre-flight`) came from the parent's `## A2`/`## B` sections
> rather than its Progress Log — both are **pointer-only** items whose own text says they belong to a different
> plan/epic; they are carried here unmodified rather than silently dropped, per the lossless-relocation requirement, but
> are NOT primary work for this plan (see the note on each todo).
>
> **This bucket is bigger than the other 3 residual plans** (9 todos vs 2 each) because it is the explicit catch-all
> ("infra/ops residuals") for everything that didn't fit a topical bucket — it was not sub-split further to stay within
> the operator-approved 4-plan fork.

## Todos

- [ ] [VERIFY] P0. **FULL AUDIT — after the prediction cqg work, verify what is actually shipped vs left across ALL the
      non-operator-gated code work** for: data migration, manifest code changes across every service, the data pipeline,
      `pipeline_mode` standardisation (GATE 0), instrument-catalogue services, and the data-status tab/downloads — then
      **finish anything non-operator-gated that remains** (operator believes it is "pretty much all shipped"; confirm).
      Source plans to sweep: `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`,
      `master_data_canonicalisation_migration_catalogue_2026_06_07.md`,
      `migration_verification_orphan_safety_2026_06_10.md` (the now-trimmed parent of this fork),
      `data_status_tab_and_downloads_remediation_2026_06_16.md`, the per-AG `*_manifest_canonicalisation_*` plans, and
      the instrument-catalogue lifecycle plan. **Operator-gated items stay parked** (V6 eyeball, G4 `--apply`, decision
      424; decision 338 cqg classifier is DONE — uac@d52217f+e0035fd+8e3108d). **Repo hygiene first**: several agents
      are on OTHER machines, so clones may be stale/diverged — clean + `pull --rebase` / fetch FRESH remote state per
      repo BEFORE auditing (incidents this session: UAC + PM version promotion-lag, PM regen churn, a staging backmerge
      landing a foreign over-limit `databento_classifier.py`). Run as `/autonomous` to completion. Owner: this slot
      (operator: "do it all here"). Provenance: operator message 2026-06-16.
- [ ] [DATA] P1. **RESUME runbook (48 paused GCP schedulers + 26 AWS rules) un-pause** — runs ONLY after TradFi G4 also
      verified; that precondition is now MET (2026-07-12). **CORRECTED 2026-07-14 (doc-reconciliation verify-rerun-2,
      finding 154): the runbook's own precondition text
      (`master_data_canonicalisation_migration_catalogue_2026_06_07.md` §"RESUME runbook") requires TWO conditions, not
      one — "every AG `--apply` complete + verified" AND "the new manifests are consolidated". Only the FIRST is met (G4
      verified all 5 AGs); the SECOND is NOT met for tradfi** (a 13,971-row / 0.27% v4 schema/`pipeline_mode`/`source`
      tail from an actively-running backfill fleet — see `tradfi_v9_stage1_finish_2026_07_06.md`'s own RESUME-runbook
      todo, which stays `BLOCKED-PREREQUISITES` for exactly this reason, sequenced after the fleet-drain + re-stamp
      task). (was: "that precondition is now MET (2026-07-12)" without qualification — accurate for the G4-verified
      precondition alone, but read in isolation it overstates overall runbook readiness.) **Do not run the RESUME
      runbook until tradfi's fleet-drain + re-stamp closes** — cefi/defi/sports/pred are not separately confirmed clean
      on the "consolidated" precondition either (no fresh audit found either way beyond tradfi's), so treat fleet-wide
      readiness as unconfirmed, not just tradfi-gated. Owning todo tracked in `tradfi_v9_stage1_finish_2026_07_06.md`
      (added this edit, plan-reconciliation finding 128). Fleet drained + `pre_migration` snapshot in place; AG-by-AG,
      operator OK between each.
- [ ] [INFRA] P2. **Rollup Cloud Run Job image lags the API deploy** — `uts-prod-data-status-rollup` (the data-status
      rollup `*/5` cron Job) is pinned to a fixed `deployment-api:<tag>`, INDEPENDENT of the `uts-shared-deployment-api`
      service `:latest`. A code deploy does NOT refresh the rollup (had to `gcloud run jobs update --image` + execute
      manually this time). Make `deployment-service/scripts/cloud-run/deploy-shared.sh` (or the cloud-build-router
      deploy dispatch) ALSO bump the rollup Job image (or pin both to the same digest) so live data-status auto-reflects
      new code.
- [ ] [UI] P2. **deployment-ui — surface the could-exist vs manifest-capture distinction** — the headline
      operator-chosen metric is shards-weighted could-exist (`completion_pct` now = shards-weighted on the `/manifest`
      drilldown), but the coverage CARD shows the manifest-capture ratio (~95–98%). Surface both clearly +
      `out_of_window` as the non-counting bucket, so the two surfaces don't read as contradictory. (deployment-ui
      `DataStatusTab` + `HonestCoverageCard`; needs `[UI]` pw:L2 gate.)
- [ ] [INFRA] P3. **Local-dev uvicorn restart flakiness** — repeated `:8004` bind/port races on
      `restart-deployment-stack`-style restarts (worked around with explicit `fuser -k` + harness background launch).
      Make the dev restart helper port-clear deterministically.
- [ ] [SCRIPT] P2. **Rollup worker: precompute `unique_instruments`** — the Cloud Run data-status rollup
      (deployment_api/scripts/data_status_rollup_worker.py) predates the field; in LIVE (non-beta) mode the rollup
      fast-path serves coverage summaries WITHOUT unique_instruments until it recomputes them. Add the catalogue read to
      the worker + redeploy the Cloud Run job. Repo: deployment-api. Provenance: operator ask 2026-06-12.
- [ ] [DATA] P3. **Re-stamp the legacy schema_version tails** (target: mtds `migrate_*_to_v9_canonical.py` +
      ManifestWriter rebuild). **DEFERRED — operator 2026-06-22: wait for the active backfill fleet to finish, then run
      in a quiet window** (NOT a force-drain for a small mostly-empty tail). **Trigger to resume:** the
      `cefi-hyperliquid-2023..2026`, `mdps-backfill-tradfi`, `mdps-sports`, and ~30 `mtds-dex-pools-*` backfill VMs have
      STOPPED (`gcloud compute instances list --filter=status=RUNNING`). **Characterised 2026-06-22** (read-only over
      the live `-prd-` consolidated `_index`): cefi **131,034** pre-v9 rows (v6=78,944 / v5=40,142 / v4=11,948 = 3.35%),
      tradfi **6,415** (v4, 0.25%), prediction **1,454** (v4, 1.93%); defi/sports are 100% v9. All carry
      `pipeline_mode=None` + `source=None`, all written **2026-04-05..04-24** (before the June canonicalisation walk),
      and **none are stale duplicates** of a v9 row (0 v9-twins) — they are genuine unique cells the June walk missed.
      **KEY SUBTLETY:** cefi's tail is **118,292 `empty_confirmed`** (no data object) + 12,618 captured; the
      `migrate_cefi_flat_to_v9_canonical.py` data-walk fixes object PATHS only (v9 manifest cols are added by the
      ManifestWriter rebuild that derives from DATA objects), so it **cannot reach the empty cells** — they need a
      separate **manifest-only re-stamp** (derive `pipeline_mode`/`source` per venue+data_type via the UAC canonical
      rules, set `schema_version=9`, write back the SOURCE per-VM shard, then re-consolidate). **Gating (HARD):**
      pre-migration VM drain + operator sign-off on `--apply` (irreversible); the manifest-only re-stamp must NOT race
      the live consolidator (`*/1` re-derives the consolidated index) or live writers → also needs the quiet window. Run
      order when resumed: drain → consolidate+snapshot → mtds `--apply` (captured cells) + manifest-only re-stamp (empty
      cells) → re-consolidate → re-verify the distribution is uniform v9.
- [ ] [SCRIPT] P1. MVP Phase 2-3 — already in `mvp_scope_catalogue_tagging_2026_06_08.md` (deployment-api
      `scope=mvp|could_exist|all` + UI tick + features/strategy/model sections). Schedule, do not re-file. **(Pointer
      item — the actual work lives in `mvp_scope_catalogue_tagging_2026_06_08.md`; carried here unmodified from the
      parent rather than dropped, per lossless-relocation.)**
- [ ] [DESIGN] P1. **Execution-config compatibility pre-flight** (audit-and-enhance, NOT a new catalogue) — composite
      `assert_execution_config_compatible(archetype × venue × instrument × required-matching-fidelity)` joining the
      existing `archetype_capability` (SUPPORTED/BLOCKED — "staked_basis can't bet") + `archetype_capability_matrix`
      (venue actions / fill-margin-settlement) + `data_type_capability` (L1/L2/trades/ohlcv granularity → matchability).
      **Post-G4** (consumes the post-migration honest granularity). File under the **execution epic**. slot-2.
      **(Pointer item — the source text says "File under the execution epic"; carried here unmodified from the parent
      rather than dropped, per lossless-relocation — re-file under the execution epic when picked up.)**

## Success criteria

1. A2 full audit run to completion (or explicitly re-scoped) — non-operator-gated data-pipeline code work confirmed
   shipped or finished.
2. RESUME runbook un-paused once tradfi's fleet-drain + re-stamp closes (tracked jointly with
   `tradfi_v9_stage1_finish_2026_07_06.md`).
3. Rollup Cloud Run Job image auto-tracks the API deploy; `unique_instruments` precomputed in the rollup worker.
4. deployment-ui surfaces could-exist vs manifest-capture distinctly (`[UI]` pw:L2 gate required).
5. Local-dev uvicorn restart is deterministic.
6. Legacy schema_version tails re-stamped once the backfill fleet quiet-window opens (operator sign-off required,
   irreversible).
7. MVP Phase 2-3 + execution-config pre-flight items re-homed to their named owning plans/epics (not executed here).

## Progress Log

- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  further work done yet beyond what the parent's archived Progress Log already recorded.

## Deferred work — migrated to:

- P3 (re-stamp legacy schema_version tails): N/A — no migration, still owned + open in this plan. Deferred per operator
  2026-06-22 pending the active backfill fleet finishing; trigger-to-resume condition documented inline.
