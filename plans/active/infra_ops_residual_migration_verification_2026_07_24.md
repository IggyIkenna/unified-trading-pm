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
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
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
last_updated: "2026-08-01"
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/manifest-migration-coordination.md,
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    market-tick-data-service/market_tick_data_service/scripts/migrate_cefi_flat_to_v9_canonical.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (its own main body A2/B
  sections + Progress Log entries dated 2026-06-12 through 2026-06-22) as part of the 2026-07-24 plan line-cap
  remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's
  durable protocol (CF-15…CF-21) had already migrated to codex; these 9 items were the last genuinely-open items that
  didn't fit the prediction-cqg / sports pre-launch+CF-5 / defi-venue+lst-rates residual buckets and are tracked here
  going forward.
---

# Infra/ops residual tail

> **Origin.** All 9 todos below are moved **verbatim** from
> `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; full historical Progress
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
- [x] [DATA] P1. **RESUME runbook (48 paused GCP schedulers + 26 AWS rules) un-pause** — runs ONLY after TradFi G4 also
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
      operator OK between each. **na-eligibility-audit 2026-08-03 (blocker-currency check): the named gate has cleared
      and the runbook has already been EXECUTED.** `tradfi_v9_stage1_finish_2026_07_06.md` is now archived
      (`plans/archive/2026_07/`); its own Progress Log records task 10 (v9 schema_version tail re-stamp) + task 4 (E5
      rebuild gate) both CLOSED 2026-07-16 (tradfi corpus-wide 100% `schema_version=9`, independently verified), and a
      separate 2026-07-16 entry: "Task -003 (RESUME runbook) EXECUTED — operator-authorized... Net: the resume runbook
      is DONE — driven for real, every item verified or correctly flagged." Caveats recorded there, not re-derived here:
      the 3 `defi-fwd-*` live-poll crons resumed clean; 11 `uts-prod-mtds-collect-*` daily-batch crons hit an unrelated
      shared-UTL date-default bug and were re-paused (tracked in
      `defi_scheduled_collection_outage_paused_crons_2026_07_16.md`); all 26 AWS EventBridge rules failed instantly on a
      shared IAM `logs:CreateLogStream` gap and were disabled again
      (`aws_consolidator_batch_logstream_iam_gap_2026_07_16.md`). This todo's own text still frames the runbook as
      not-yet-run — it should be re-verified against current cron/rule state (not re-executed blind) rather than treated
      as still pending from scratch. **round5-cross-cutting-audit 2026-08-08**: no operator input needed — the runbook
      already ran with operator authorization (2026-07-16), both caveats above are independently closed/tracked. Live
      re-check (`gcloud scheduler jobs list`, 2026-08-08): 4 of 11 mtds-collect crons currently paused again, but this
      is a SEPARATE, already-tracked, deliberate pause pending an in-flight migration VM
      (`defi_consolidated_closeout_2026_07_18.md` Track 8), not a runbook regression.

      **CLOSED 2026-08-08 (na-eligibility-audit round7)**: the runbook itself was executed 2026-07-16 (operator-authorized) and this doc's own 2026-08-08 round5-cross-cutting-audit entry live-re-checked current cron/rule state today -- no regression beyond the separately-tracked deliberate mtds-collect pause. Flipping to match the already-gathered evidence; nothing newly run here.

- [x] ✅ [INFRA] P2. **DONE — ALREADY FIXED, stale checkbox.** **DONE 2026-08-01 (satellite-batch1 reconciliation):**
      `deployment-service@c04d4562` (2026-06-15) already added the `gcloud run jobs update --image` + async `execute`
      sync step to `deploy-shared.sh` ("[3/3] Sync data-status rollup Job to the new image") — landed 3 days after this
      item's own report, never checked off. Full evidence: `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`
      sub-item (A). **Rollup Cloud Run Job image lags the API deploy** — `uts-prod-data-status-rollup` (the data-status
      rollup `*/5` cron Job) is pinned to a fixed `deployment-api:<tag>`, INDEPENDENT of the `uts-shared-deployment-api`
      service `:latest`. A code deploy does NOT refresh the rollup (had to `gcloud run jobs update --image` + execute
      manually this time). Make `deployment-service/scripts/cloud-run/deploy-shared.sh` (or the cloud-build-router
      deploy dispatch) ALSO bump the rollup Job image (or pin both to the same digest) so live data-status auto-reflects
      new code.
- [x] ✅ [UI] P2. **DONE 2026-08-01 — `deployment-ui@727298b`.** `HonestCoverageCard.tsx` showed only 2 "of attempted"
      values; added `completion_pct_shards_weighted` (could-exist, hidden not faked when absent) + `out_of_window` (now
      an explicit labelled count, not just a bar segment) as 2 new distinct rows. Regression spec
      `tests/smoke/data_status_coverage_labels.spec.ts` extended + passing (`pw:L2 ✓`, 4/4). Full evidence:
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` sub-item (B). **deployment-ui — surface the could-exist
      vs manifest-capture distinction** — the headline operator-chosen metric is shards-weighted could-exist
      (`completion_pct` now = shards-weighted on the `/manifest` drilldown), but the coverage CARD shows the
      manifest-capture ratio (~95–98%). Surface both clearly + `out_of_window` as the non-counting bucket, so the two
      surfaces don't read as contradictory. (deployment-ui `DataStatusTab` + `HonestCoverageCard`; needs `[UI]` pw:L2
      gate.)
- [x] ✅ [INFRA] P3. **DONE — ALREADY FIXED, stale checkbox.** **DONE 2026-08-01 (satellite-batch1 reconciliation):**
      `unified-trading-pm@678188510` (2026-06-15) already added a deterministic `stop_port()` free-wait (lsof + `ss`
      LISTEN both clear, ~10s bounded, `kill -9` fallback) to `restart-deployment-stack.sh` — functionally equivalent to
      (more robust than) the suggested `fuser -k`. Full evidence:
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` sub-item (C). **Local-dev uvicorn restart flakiness** —
      repeated `:8004` bind/port races on `restart-deployment-stack`-style restarts (worked around with explicit
      `fuser -k` + harness background launch). Make the dev restart helper port-clear deterministically.
- [x] ✅ [SCRIPT] P2. **DONE — ALREADY FIXED, stale checkbox.** **DONE 2026-08-01 (satellite-batch1 reconciliation):**
      `deployment-api@5938b3e` (2026-06-12, same day as this item's own provenance date) already wired
      `read_unique_instrument_count()` into `coverage.py::_assemble_coverage_entry`, which the rollup worker's
      `_build_one_service_coverage` calls directly — a live rollup's `coverage.json.gz` already includes
      `unique_instruments` with no recompute fallback. Full evidence:
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` sub-item (D). **Rollup worker: precompute
      `unique_instruments`** — the Cloud Run data-status rollup (deployment_api/scripts/data_status_rollup_worker.py)
      predates the field; in LIVE (non-beta) mode the rollup fast-path serves coverage summaries WITHOUT
      unique_instruments until it recomputes them. Add the catalogue read to the worker + redeploy the Cloud Run job.
      Repo: deployment-api. Provenance: operator ask 2026-06-12.
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
- [x] [SCRIPT] P1. MVP Phase 2-3 — already in `mvp_scope_catalogue_tagging_2026_06_08.md` (deployment-api
      `scope=mvp|could_exist|all` + UI tick + features/strategy/model sections). Schedule, do not re-file. **(Pointer
      item — the actual work lives in `mvp_scope_catalogue_tagging_2026_06_08.md`; carried here unmodified from the
      parent rather than dropped, per lossless-relocation.)** -- CLOSED (na-eligibility-audit 2026-08-01): duplicate of
      the actively-progressing owner `plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md` (most recent update
      2026-07-28, `unified-api-contracts@0fb9821b`, ModelsMvpRule P2b, with an open P2b-2 follow-on already tracked
      there) — this was a lossless-relocation pointer, not primary work for this plan, so closing here is a
      citation-fix, not a scope drop.
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
3. ✅ DONE 2026-08-01 — Rollup Cloud Run Job image auto-tracks the API deploy; `unique_instruments` precomputed in the
   rollup worker (both already fixed pre-2026-07-24, see items 3 + 6 above).
4. ✅ DONE 2026-08-01 — deployment-ui surfaces could-exist vs manifest-capture distinctly (`[UI]` pw:L2 gate, see item 4
   above).
5. ✅ DONE 2026-08-01 — Local-dev uvicorn restart is deterministic (already fixed pre-2026-07-24, see item 5 above).
6. Legacy schema_version tails re-stamped once the backfill fleet quiet-window opens (operator sign-off required,
   irreversible).
7. MVP Phase 2-3 + execution-config pre-flight items re-homed to their named owning plans/epics (not executed here).

## Progress Log

- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  further work done yet beyond what the parent's archived Progress Log already recorded.
- 2026-08-01 — satellite-batch1 dispatch (`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` sub-items A-D)
  reconciled items 3-6: 3 of 4 were already fixed months earlier (`deployment-service@c04d4562` 2026-06-15,
  `unified-trading-pm@678188510` 2026-06-15, `deployment-api@5938b3e` 2026-06-12) but never checked off across this
  doc's own fork chain — a real instance of the stale-carry-forward pattern this doc itself exists to catch. Only item 4
  (deployment-ui could-exist/out_of_window surfacing) was genuinely open; fixed via `deployment-ui@727298b`. All 4
  flipped `[x]` with citations; full evidence in the satellite batch1 plan.
- **context-scout 2026-08-03**: re-scouted; refreshed context_scope (5 entries) — added the v9 re-stamp source script.

- **na-eligibility-audit 2026-08-17** [body-hash:4fc17ae72e7a34ce]: KEEP-NA, valid -- 3 remaining items each independently cited by NEVER-RE-LITIGATE rules. The FULL AUDIT item is a broad multi-plan judgment call reaffirmed as such by 4 prior audit rounds (2026-07-30, 08-01, 08-03, 08-08 round7). The schema_version re-stamp item carries an explicit dated operator ruling in its own text ('DEFERRED -- operator 2026-06-22: wait for the active backfill fleet to finish, then run in a quiet window') plus a HARD gate on irreversible --apply sign-off -- rule (a). The execution-config pre-flight item is explicitly a pointer whose own text says 'File under the execution epic' and the doc's own success criteria confirms 'not executed here' -- rule (c).
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 3 residual todos, each independently NEVER-RE-LITIGATE-citable: a broad FULL AUDIT judgment call, an irreversible schema_version re-stamp explicitly DEFERRED by operator 2026-06-22, and an execution-config pre-flight pointer item. Reaffirmed KEEP-NA 5x (2026-07-30 through 08-17).

## Deferred work — migrated to:

- P3 (re-stamp legacy schema_version tails): N/A — no migration, still owned + open in this plan. Deferred per operator
  2026-06-22 pending the active backfill fleet finishing; trigger-to-resume condition documented inline.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the RESUME runbook needs operator OK between each AG, the
  schema_version re-stamp needs operator sign-off on an irreversible `--apply`, and 2 of the 9 todos are pointer-only
  items the doc itself says belong elsewhere.

- **na-eligibility-audit 2026-08-01**: KEEP-NA-STALE (duplicated elsewhere) -- 1 item(s) closed as stale/duplicated (see
  checkboxes above), doc stays assigned_vm: NA. Full audit rationale: 4 of 5 remaining open items are genuine judgment/
  operator-gated work (broad multi-plan audit requiring a "confirm" judgment call; a production scheduler/rule un-pause
  explicitly requiring "operator OK between each" AG; an irreversible-`--apply` schema re-stamp explicitly deferred
  pending operator sign-off + a quiet backfill-fleet window; a pointer-only composite-function design task not yet even
  filed under its named owning epic). The 5th (MVP Phase 2-3) is a verbatim pointer whose own text says "already in
  `mvp_scope_catalogue_tagging_2026_06_08.md` ... Schedule, do not re-file" — that target doc is the real,
  actively-progressing owner of this scope (most recent update 2026-07-28, `unified-api-contracts@0fb9821b`), so this
  item is a citation-fix duplicate, not new dispatchable content. Since it is a genuine mix (4 KEEP_JUDGMENT + 1
  duplicate), this is NOT a RECLASSIFY case.

- **na-eligibility-audit 2026-08-03 (reclassify pass)**: KEEP-NA, valid (blocker-currency only) — the RESUME-runbook
  todo's cited blocker (`tradfi_v9_stage1_finish_2026_07_06.md`'s fleet-drain + re-stamp) is now archived-DONE
  (2026-07-16) and that doc's own Progress Log records the runbook itself as already EXECUTED the same day, with named
  caveats (some crons re-paused for an unrelated bug, all 26 AWS rules disabled again on an IAM gap) — annotated in
  place. Remaining open items (FULL AUDIT confirm-judgment call; RESUME-runbook still needs per-AG operator OK even
  post-execution for any re-run; schema_version re-stamp irreversible-`--apply` sign-off; 2 pointer-only items) are
  unchanged judgment/operator-gated work. Not a RECLASSIFY case. `assigned_vm` untouched.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, stale item closed -- flipped the
  RESUME-runbook checkbox (executed 2026-07-16, re-verified live today per this doc's own round5-cross-cutting- audit
  entry). Remaining open items are a genuine multi-plan audit judgment call (FULL AUDIT), an irreversible `--apply`
  schema re-stamp explicitly deferred pending an operator-authorized quiet backfill-fleet window, and a pointer-only
  design task not yet filed under its owning epic -- genuine mix, whole doc stays NA.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
- **context-scout 2026-08-17**: re-verified context_scope, no change needed (5 entries).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche): KEEP-NA, valid — reaffirms the chain of 5 prior audit passes (2026-07-30 through 08-19), unchanged: 3 residual todos, each independently NEVER-RE-LITIGATE-citable — a broad multi-plan FULL AUDIT judgment call, an irreversible schema_version re-stamp explicitly DEFERRED by operator 2026-06-22 pending a quiet backfill-fleet window, and an execution-config pre-flight pointer item whose own text says 'File under the execution epic'.
