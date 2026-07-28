---
doc_type: issue
title: >-
  deployment-service's scheduler job-name reconstruction has the SAME live bug just fixed in unified-trading-library —
  DP_CRON_DID_NOT_FIRE PAUSED-suppression can never see a real PAUSED state
summary: >-
  While running the tradfi below-floor reclassification `--apply`
  (`tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`), `_assert_consolidator_paused` (mirrors
  `sports_manifest_remediation_safety.py`) always reported the real, confirmed-PAUSED consolidator scheduler job as "is
  None, not PAUSED" — root-caused to
  `unified_trading_library.monitors.consolidator_liveness._scheduler_job_name_for_bucket` reconstructing the job name
  via the BUCKET short-form env suffix (`prd`, from `bucket_naming._resolve_deployment_env_short`) instead of
  Terraform's actual scheduler `env_prefix` (the RAW environment word `prod`,
  `deployment-service/terraform/gcp/main.tf:47` `env_prefix = "${bucket_prefix}-${environment}"`) — producing
  `uts-prd-manifest-consolidator-market-data-tradfi-cron`, a 404, against the real live job
  `uts-prod-manifest-consolidator-market-data-tradfi-cron` (confirmed via `gcloud scheduler jobs describe` 2026-07-27).
  Fixed in `unified-trading-library@080a84a0`. **Checked whether deployment-service's OWN twin implementation
  (`data_pipeline_monitors/meta_targets.py ::scheduler_env_prefix`/`::consolidator_scheduler_job`) has the identical
  bug: it does** — same `_ENV_SHORT_FORM` table mapping `"prod"->"prd"`, same
  `f"uts-{short}-manifest-consolidator-{key}- cron"` construction. It is NOT dead code:
  `data_pipeline_monitors/cli.py:65,795` imports it as `_consolidator_scheduler_job` and passes the (wrong) name into
  the DP_CRON_DID_NOT_FIRE PAUSED-suppression path (`_down_reason_and_detail`-style KEY #2 logic, "a scheduler
  PAUSED-by-design during the manual-backfill campaign should NOT fire DP_CRON_DID_NOT_FIRE"). Since the reconstructed
  name 404s, that suppression can never actually fire on a genuinely-PAUSED consolidator — the alert would fire anyway
  during any deliberate pause (e.g. exactly the kind of remediation `--apply` this session just ran), which is the
  opposite of KEY #2's intent.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [cloud-scheduler, manifest-consolidator, alerting, dp-cron-did-not-fire, naming-bug, cross-repo]
related:
  [
    plans/archive/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md,
    plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
source: [data_engineering slot-2, 2026-07-27, discovered while running tradfi_satellite_ao_dispatch_batch2-009]
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: deployment-service@841f464
---

> **🟢 RESOLVED 2026-07-28 — `deployment-service@841f464`.** Both todos below are done: `scheduler_env_prefix()` fixed
> to use the raw Terraform environment word (mirrors `unified-trading-library@080a84a0`), live-verified against real GCP
> (job-name resolution + a real pause/suppress/resume cycle proving the DP_CRON_DID_NOT_FIRE KEY #2 PAUSED-suppression
> path). See the Todos section for full evidence. Archived per `/codex/11-project-management/issue-doc-lifecycle.md`
> trigger 2 (commit SHA fixes the issue).

## What I found

Running `instruments-service/scripts/reclassify_tradfi_below_floor_expected_unattempted_2026_07_27.py --apply`, its
`_assert_consolidator_paused` pre-flight (mirrors `sports_manifest_remediation_safety.py`) raised
`ConsolidatorNotPausedError: ... is None, not PAUSED` even immediately after I confirmed via
`gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-tradfi-cron --location=asia-northeast1` that
the job WAS genuinely `PAUSED`.

Root cause: `unified_trading_library.monitors.consolidator_liveness._scheduler_job_name_for_bucket` built the job name
as `f"uts-{env_short}-manifest-consolidator-{key}-cron"` where
`env_short = bucket_naming._resolve_deployment_env_short()` resolves to the 3-char BUCKET-NAME suffix (`"prd"`). But the
real Terraform-deployed job name uses `env_prefix = "${var.bucket_prefix}-${var.environment}"`
(`deployment-service/terraform/gcp/main.tf:47`) where `var.environment` is validated to exactly `"dev"|"staging"|"prod"`
— the FULL word, never the 3-char short form. So the function always computed
`uts-prd-manifest-consolidator-market-data-tradfi-cron`, which 404s; the real job is
`uts-prod-manifest-consolidator-market-data-tradfi-cron`. Confirmed via direct
`gcloud scheduler jobs list --location=asia-northeast1` — only the `uts-prod-...` name exists.

**Fixed in `unified-trading-library@080a84a0`**: added `bucket_naming.resolve_raw_deployment_env()` (extracted the raw
config-bootstrap env-read into a reusable function) + `consolidator_liveness._resolve_deployment_env_terraform_word()`
(maps through a Terraform-word table instead of the bucket short-form table), updated `_scheduler_job_name_for_bucket`
to use it. New/updated tests verify the corrected `uts-prod-...` name against the live-confirmed pattern. Full
`quality-gates.sh` green.

**Checked whether deployment-service has the same bug — it does, and it's live-called, not dead code**:

- `deployment_service/data_pipeline_monitors/meta_targets.py::scheduler_env_prefix()` (lines 149-158) uses the SAME
  `_ENV_SHORT_FORM` table (`"prod": "prd"`, lines 138-146) and builds `f"uts-{short}"` — i.e. `"uts-prd"`, not
  `"uts-prod"`.
- `consolidator_scheduler_job(ag)` (lines 161-166) then builds
  `f"{scheduler_env_prefix()}-manifest-consolidator-market-data-{ag}-cron"` — same wrong
  `uts-prd-manifest-consolidator-market-data-{ag}-cron` shape.
- This is imported live in `data_pipeline_monitors/cli.py:65` as `_consolidator_scheduler_job`, and called at
  `cli.py:795` to supply `scheduler_job=` into the DP_CRON_DID_NOT_FIRE PAUSED-suppression path (the KEY #2 logic: "a
  scheduler PAUSED-by-design during the manual-backfill campaign should NOT fire DP_CRON_DID_NOT_FIRE"). A 404'd job
  name means `_scheduler_job_state` there returns `None` (UNKNOWN), not `"PAUSED"` — so this suppression can never
  actually fire for a genuinely-paused consolidator; the exact opposite of its documented intent.

Did NOT fix deployment-service myself: out of scope for `tradfi_satellite_ao_dispatch_batch2-009` (a different repo, and
the DP_CRON_DID_NOT_FIRE alerting path deserves its own verification before touching it, not a drive-by edit alongside
an unrelated tradfi backfill task).

## Why it matters

- Any future remediation script that pauses a consolidator cron and relies on deployment-service's reader to
  confirm/suppress (rather than `gcloud` directly, as I did manually this session) will hit the identical
  false-not-PAUSED failure `unified-trading-library` just had.
- More importantly: the ALERTING direction is backwards from the naming-bug's usual failure mode. Here a
  genuinely-PAUSED consolidator (e.g. mid-remediation, exactly this session's scenario) would still page
  DP_CRON_DID_NOT_FIRE, because the suppression can never see the real PAUSED state — a standing false-positive-alert
  risk for every deliberate pause, not just a remediation-script inconvenience.

## Recommended decision

- [x] ✅ [BACKEND] P2. **DONE 2026-07-28 — `deployment-service@841f464`.** Fixed
      `deployment_service/data_pipeline_monitors/meta_targets.py::scheduler_env_prefix()` the same way
      `unified-trading-library@080a84a0` fixed its twin: removed the `_ENV_SHORT_FORM` short-form mapping table entirely
      and made `scheduler_env_prefix()` return `f"uts-{_deployment_env_long()}"` — the RAW Terraform environment word
      (`"prod"`), matching `deployment-service/terraform/gcp/main.tf:47`'s
      `env_prefix = lower(replace("${var.bucket_prefix}-${var.environment}", "_", "-"))` (`var.environment` validated to
      exactly `dev|staging|prod`) byte-for-byte — confirmed this is the SAME `env_prefix` local used by every scheduler/
      Cloud-Run job in this Terraform module (`manifest_consolidator_scheduler.tf`, `t1_batch_scheduler.tf`, etc.), not
      just the consolidator, so the fix corrects `consolidator_scheduler_job()`/`consolidator_cloud_run_job()`/every
      `cli.py` caller of `_scheduler_env_prefix()` in one place. **Live-verified against real GCP** (not just gcloud
      describe — the full pause/suppress/resume path): (1) `gcloud scheduler jobs list --location=asia-northeast1`
      confirms every live consolidator job uses `uts-prod-manifest-consolidator-...` naming (18 jobs, all `uts-prod-`,
      zero `uts-prd-`); (2) the fixed resolver's own output (`meta_targets.consolidator_scheduler_job("tradfi")` →
      `uts-prod-manifest-consolidator-market-data-tradfi-cron`) exactly matches a real job, confirmed via
      `gcloud scheduler jobs describe` (state ENABLED); (3) the real `cli._make_scheduler_state_reader()` (actual
      `google.cloud.scheduler_v1` SDK client, not mocked) round-trips state correctly against that job. Added
      `test_scheduler_env_prefix_uses_raw_terraform_word_not_bucket_short_form` to
      `tests/unit/test_data_pipeline_monitors.py` asserting the corrected `uts-prod-...` shape for
      `scheduler_env_prefix()`/`consolidator_scheduler_job()`/`consolidator_cloud_run_job()`. Full
      `quality-gates.sh --no-fix` green (267s, sentinel `f0ee04e8` == HEAD before ship). Repo: deployment-service.
- [x] ✅ [DATA] P2. **DONE 2026-07-28 — live-verified end-to-end, no code needed (folded into the same session as the
      todo above).** Verified the DP_CRON_DID_NOT_FIRE KEY #2 PAUSED-suppression path actually suppresses for a REAL
      paused job, using the sanctioned `deployment_service.data_pipeline_monitors.scheduler_maintenance`
      pause/resume-with-CAS-lock mechanism (never a raw `gcloud scheduler jobs pause`) against the real
      `uts-prod-manifest-consolidator-market-data-tradfi-cron` job (~13s total exposure window,
      `pause_for_maintenance(ttl_minutes=3)` → verify → `resume_after_maintenance()` in a `finally`): state read
      ENABLED→PAUSED→ENABLED (all 3 reads via the REAL `cli._make_scheduler_state_reader()` SDK client); with the job
      genuinely PAUSED, called the REAL `meta_watchers.check_cron_fired()` (not a mocked reader) against a synthetic
      stale target sharing that job's real name — log confirms
      `"DP_CRON_DID_NOT_FIRE suppressed for 'live-verify-tradfi' — scheduler job     'uts-prod-manifest-consolidator-market-data-tradfi-cron' is PAUSED"`.
      This proves both halves end-to-end: the corrected name resolves to a job whose real state the SDK reads correctly,
      AND the downstream suppression logic fires on that real state. Job confirmed resumed to ENABLED after. Repo:
      deployment-service (no code change this todo — pure live verification).
