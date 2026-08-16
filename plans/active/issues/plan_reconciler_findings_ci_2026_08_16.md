---
doc_type: issue
title: plan_reconciler findings — ci tranche — 2026-08-16
summary: >-
  Daily deep plan-reconciliation run-findings doc for the ci topic tranche, dispatch agt-4f7ad9 (slot 9). Records
  Phase -1 predecessor-doc reconciliation, hunter-detected candidates (8 parallel batches, 47 writable docs), a
  Trust-Mode line-cap split applied inline, adversarial-verification outcomes, applied fixes, routed operator
  questions, and coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, ci, sharded-run]
related:
  [
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_10.md,
    /plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md,
    /plans/archive/2026_08/operator_ruling_record_ci_line_cap_splits_2026_08_16.md,
  ]
created: "2026-08-16"
author: plan_reconciler
source: agt-4f7ad9
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.3
calibrated_ai_days: 0.3
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_10.md,
    /plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# plan_reconciler findings — ci tranche — 2026-08-16

Dispatch `agt-4f7ad9`, slot 9, tranche `ci`. PM head at run start: `03c6604719` (before FF).

## Scope

**50 docs carry `asset_group: ci`** in `plans/active/` (incl. `issues/`), computed via
`generate_tranche_doc_inventory.py --tranche ci` (never a same-line grep, per SKILL.md). **1 of 50 is inside the
12-hour grace window** (`qg_host_adaptive_resource_governor_2026_07_14.md`, age 6h at run start) — read-only context
this run. **49 are writable.**

## Phase -1 — predecessor findings-doc reconciliation

- `plan_reconciler_ci_late_findings_2026_08_06.md` — 1 genuinely open item (P3, editorial title-rewrite judgment call
  on `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`), already re-confirmed correctly-left-open
  as recently as the 2026-08-10 predecessor run. Re-confirmed again this run — no change, no action needed.
- `plan_reconciler_findings_ci_2026_08_10.md` — 3 open Filed items as of 2026-08-15's last update:
  1. `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` over 1000L cap (was 1013L) — **RESOLVED
     THIS RUN** via a Trust-Mode line-cap split, see below.
  2. `github_actions_operator_gated_followups_2026_07_17.md` over 1000L cap (was 1006L) — **RESOLVED THIS RUN** via
     the same split action.
  3. Blocked-question answer-retrieval gap (AO-dashboard-side, not a doc fix) — re-checked, no new evidence either
     way this run; still needs an AO-dashboard-side check outside this worker's HTTP surface. Left open, unchanged.

## Trust-Mode line-cap splits (applied, not parked)

Full reasoning: `/plans/archive/2026_08/operator_ruling_record_ci_line_cap_splits_2026_08_16.md`. Per the 2026-08-15
`/plan-reconcile` Trust Mode ruling, plan-splitting is no longer a park-worthy preference call when a proven
in-corpus pattern already exists — both splits reproduce the exact `_progress_log_history_<date>.md` extraction
pattern this doc-chain's own 2026-08-03 split already validated, applied to a recommendation the 2026-08-10
predecessor run itself named "highest-leverage" and that sat unactioned for 6 days.

- `github_actions_operator_gated_followups_2026_07_17.md`: 1006-1007L → 736L (later 738L after a prettier pass).
  Extracted "Hard-won context..." + "Cost ruling 2026-07-23" (278L, zero open todos inside) to
  `/plans/archive/2026_08/github_actions_operator_gated_followups_hard_won_context_and_cost_ruling_history_2026_08_16.md`.
- `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md`: 1013L → 143L. Extracted the bulk 2026-08-03
  Progress Log (880L, ~20 escalation write-ups, zero open todos inside) to
  `/plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_continued2_progress_log_history_2026_08_16.md`,
  deliberately KEEPING the 2026-08-09 status entry + na-eligibility-audit verdict (both gate the live doc's own
  still-open todos 1/3).
- Shipped: `unified-trading-pm@f835f7fcc4` via `safe-doc-push.sh` (5 files: 2 trimmed live docs + 2 new history docs +
  1 new ruling-record doc). Verified `check_line_caps.sh` clean for both targets post-split (neither appears in the
  current violation list; corpus-wide count 2 vs baseline 17).

## Hunter dispatch (Phase 1)

**8 parallel read-only hunter batches** (sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted in full at each spawn),
covering all 47 writable docs not already fully read directly by me in Phase -1 (the 2 predecessor findings docs):

- Batch A — QG capacity/contention cluster (6 docs, 1 grace-context)
- Batch B — pytest-timeout flaky series + 2 misc (6 docs)
- Batch C — quickmerge/sentinel/semver cluster (6 docs)
- Batch D — workflow-template/glue-runner infra (6 docs)
- Batch E — ldr-to-main/promote/sit-gate cluster (6 docs)
- Batch F — deployment-api/service cluster (6 docs)
- Batch G — big active plans cluster (6 docs)
- Batch H — remaining misc docs (5 docs)

All 8 batches completed. Findings are summarized per-batch below (STEP 4 adversarial verification in progress —
see Verification section, appended as it completes). Raw per-batch reports are in the dispatching agent's own
context, not duplicated verbatim here; this section is the deduplicated candidate ledger.

### Candidate ledger (pre-verification, deduplicated by doc+claim)

**Flip candidates (HARD-evidence claimed by hunter, pending independent re-verification):**

1. Batch D: `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` todo (auto-deploy-sync watchdog script) — DONE,
   cites `deploy-sbin-scripts.sh` + systemd timer, self-citing header comment.
2. Batch D: same doc, monitoring-gap todo — PARTIAL flip only (wedged-detection sub-clause done, cleanly-inactive
   sub-clause still genuinely open) — do not flip wholesale.
3. Batch F: `deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md` todo — DONE, cites
   `deployment-service@71871454`, live-measured `BASEDPYRIGHT_MAX_ERRORS=1259`.
4. Batch E: `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` — 3 todos DONE (ancestor-cleanup hoist,
   dedup-key fix, re-check-after-quiet duplicate-of-already-`[x]`), each self-citing shipped commits.
5. Batch E: `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` — 2 `[~]`-marked todos DONE
   (promote-fleet-startup-failure-monitor hardening, glue-runner-crash-loop-watchdog busy-check), self-citing shas.
6. Batch E: `cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md` — sole remaining todo DONE (substitution-
   key drift guard), commit `3ec88291e2` — would zero out this doc's open todos.
7. Batch E: `codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md` — 2 todos DONE
   (yaml-parse-error distinction, retired-docs endgame via SUPERSEDED banners) — would zero out this doc's open
   todos.
8. Batch E: `ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md` todo — nuanced: cited PR #2714 never
   merged (closed/superseded), but underlying goal satisfied by 5 fresh `chore(promote)` merges today — close on
   newer evidence, not the stale cited artifact.
9. Batch C: `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` sole open todo — functionally DONE via
   `ci_satellite_ao_dispatch_batch13_2026_08_13.md`'s classification pass + a live `reconcile_release_tags.py
   --dry-run` re-run (0 STALLED) — but batch13's finalize plan never reconciled the checkbox back to this doc, and a
   NEW latent misconfig (e2e-testing `source_dir` mismatch) surfaced and needs its own tracked todo before this doc
   can be considered fully closed.

**Contradictions:**

1. Batch A (P1): `qg_sentinel_environment_blind_2026_07_23.md` na-eligibility-audit entry cites 2 blocker docs as
   "open" that are actually `status: resolved` and physically archived.
2. Batch A (P1): `qg_host_adaptive_resource_governor_2026_07_14.md` open todo (ledgers un-unified) contradicts live
   code + codex (already unified 2026-08-10) — GRACE WINDOW doc, flagged not fixed.
3. Batch A (P3): priority mismatch, same task, P1 in one doc vs P2 in a sibling.
4. Batch D (P2): `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`'s open design question
   partially mooted by doc1's now-complete dedup (blast radius much smaller than when written).
5. Batch G (P1): stale `[OPERATOR]` framing on the trading-kill-switch F1 row in
   `github_actions_operator_gated_followups_2026_07_17.md` — the SSOT issue doc retagged this away from `[OPERATOR]`
   on 2026-07-28, never propagated here.
6. Batch G (P2): `monitoring_control_plane_master_2026_06_10.md` self-contradicts on whether `ORCHESTRATOR_API_TOKEN`
   is still needed (banner says the feature it gated is deleted; Deferred-work table still asks for the credential).
7. Batch E (P2): `cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md` frontmatter `resolved_by:` names 1
   commit; body documents ≥5 shipped commits across 2 repos.
8. Batch E (P1): `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` — near-verbatim duplicate todo,
   one `[x]` one `[ ]`, same question.

**Codex-alignment drift:** (11 findings across batches A/B/C/D/E/F/G/H — mostly P2/P3 stale line-number citations,
missing SSOT coverage for shipped mechanisms, or one genuinely stale wiring-mechanism line in `ci-cd-flow.md:687`.
Full list in Verification section as each is adjudicated.)

**Zero-checkbox / archive candidates:**

1. Batch B: `archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md` — both todos `[x]`,
   gating condition (wrapping batch12 pair archived) now satisfied, never archived. Also now mode-1-eligible under
   the narrowed codex rule (no longer even needs `archive_exempt: true`).
2. Batch F: `deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` — both todos `[x]`, `archive_exempt:
   true` sitting well past its intended bridge-only lifetime (~6-8 days).
3. Batch E (conditional): 3 docs (`sit_gate_treadmill...`, `cloudbuild_template_drift...`,
   `codex_freshness_ratchet...`) become fully-`[x]` once their flip candidates above land.
4. Batch H (conditional): `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` — functionally resolved,
   only 2 permanently-struck SUPERSEDED items remain; needs the CANCELLED-disposition-format conversion first.

**Mechanical/hygiene issues:** truncated Progress Log entries (2, batch B), stale `last_updated` frontmatter (5+
docs, batch B/C), a wrong evidence-citation sha (batch H), stale frontmatter summary text overstating remaining work
(batch D), non-standard `[~]` checkbox markers (batch E, now resolvable per flip candidates).

## Verification (STEP 4 — adversarial, in progress)

_(To be appended as each candidate is verified. Nothing above this line has been applied except the line-cap splits,
which are independently evidenced by direct line-count + hygiene-gate re-measurement, not hunter testimony.)_

## Flips verified

_(pending)_

## Contradictions (confirmed)

_(pending)_

## Codex corrections applied (mechanical, evidence-cited)

_(pending)_

## Filed

_(pending)_

## Archive candidates (operator review)

_(pending)_

## Refuted (dropped by verify)

_(pending)_

## Coverage (hunters / batches / docs)

8 hunter batches, 47 writable docs covered (+ 2 read directly by me in Phase -1, + 1 grace-window doc read as
context-only by batch A) = all 50 tranche docs accounted for. Approx combined hunter token spend: ~1.7M tokens across
8 batches, ~180 tool calls, wall-clock ~10-19 min per batch (parallel).

## Plans not reached

None — full tranche coverage achieved this run.

## Progress Log

- **2026-08-16 (dispatch agt-4f7ad9, slot 9)**: Run started. FF'd PM + all 31 sibling repo clones (all clean). Ran
  `run_hygiene_sweep.sh --ci` (2 corpus-wide hard failures, neither ci-tranche-attributable per direct re-check:
  reference-path-convention ratchet has 0 ci-tranche hits; assigned_vm:NA corpus size is `/na-eligibility-audit`'s
  disjoint remit). Phase -1 reconciled both prior ci findings docs. Computed grace set (1 doc). Dispatched 8 parallel
  hunter batches over the 47-doc writable set. While hunters ran, read + designed + applied 2 Trust-Mode line-cap
  splits (see above), shipped `unified-trading-pm@f835f7fcc4`. All 8 hunter batches returned; this doc created to
  capture the candidate ledger before starting STEP 4 adversarial verification.
