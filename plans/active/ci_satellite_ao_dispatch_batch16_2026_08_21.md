---
doc_type: plan
title: ci satellite AO dispatch batch 16 — 2026-08-21
summary: >-
  Third extraction batch from the ci-tranche `/na-eligibility-audit` wave-2 pass (2026-08-21, 27 docs re-checked
  end-to-end) — 3 bounded, previously-unextracted items surfaced this pass, each conflict-checked clear against
  batch13/batch15 and each other via basename-citation cross-reference before drafting. Source docs are NOT touched
  by this batch except where the todo IS itself the checkbox-reconciliation (explicitly marked); each source doc's
  own Progress Log carries a citation back to this batch.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md,
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
    /plans/active/issues/ci_alert_failure_resolution_linkage_2026_08_16.md,
    /plans/active/issues/ag_closeout_audit_ci_parked_2026_08_16.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md,
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
    /plans/active/issues/ci_alert_failure_resolution_linkage_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted from the 2026-08-21 `/na-eligibility-audit` ci-tranche wave-2 pass (27 docs, incremental-skip filtered).
  Each todo below is a bounded/deterministic slice split out of a doc that otherwise stays `assigned_vm: NA` for its
  remaining operator-/design-gated items. Ships `status: active` directly — mirrors batch14/batch15's confirmed
  fast-ship precedent for this tranche.
---

# ci satellite AO dispatch batch 16 — 2026-08-21

## Todos — bounded new work

- [ ] [SCRIPT] P2. **Have `scripts/dev/safe-doc-push.sh` self-set `GITHUB_REF_NAME`/`GITHUB_REF` when it detects
      it is committing to `live-defi-rollout` locally**, so a plain local LDR commit gets the correct
      baseline+buffer `check_na_corpus_ratchet` mode automatically instead of requiring every caller to know and
      manually pass these vars. Confirmed recurring 3x (2026-08-16, 2026-08-19) — each time a local invocation with
      no `GITHUB_REF_NAME` set defaulted the guard to `--diff-base origin/main` and produced a false-positive
      ratchet failure. Detect via `git rev-parse --abbrev-ref HEAD == live-defi-rollout` (or equivalent) before
      invoking `run_hygiene_sweep.sh`'s prek hook, and set both vars in the subshell that actually runs the check.
      **Second, related sub-item**: the 2026-08-19 occurrence found that `export GITHUB_REF_NAME=... && bash
      scripts/dev/safe-doc-push.sh ...` did NOT reliably propagate the var through to the check — only an
      `env VAR=val bash scripts/dev/safe-doc-push.sh ...` prefix worked reliably. Root-cause this (likely a
      subprocess/hook boundary that resets or doesn't inherit the exported var) and either fix the propagation, or
      — if this todo's self-set fix above makes the manual-export path moot — just document the finding in the
      script's own usage text so a future caller isn't tripped by it. Source:
      `/plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` (line
      ~193). Gate: a local `bash scripts/dev/safe-doc-push.sh` commit to `live-defi-rollout`, run with a clean env
      (no `GITHUB_REF_NAME` pre-set by the caller), correctly selects baseline+buffer mode — verified via the
      script's own diagnostic output, not inferred.

- [ ] [SCRIPT] P3. **`ldr_to_main_fleet_promote.sh:638`'s `gh api repos/$OWNER/$REPO/commits/live-defi-rollout
      2>/dev/null || echo '{}'` silently swallows the real error**, making a live GitHub platform outage
      indistinguishable from a genuine per-repo API regression in the workflow's own log (found diagnosing a
      2026-08-17 `ERR_LDR` occurrence — required an out-of-band `githubstatus.com` check purely because the step
      log carried no error text). Echo the captured stderr (or at minimum the HTTP status) to the step log before
      falling back to `{}`. Check whether `ldr_to_staging_promote.sh` shares this same helper/pattern and fix both
      call sites in the same change if so. Source:
      `/plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` (line ~176). Gate: a
      simulated `gh api` failure (bad token / 5xx) on this call site produces a non-empty error string in the step
      log instead of a bare `{}` fallback.

- [ ] [BACKEND] P2. **Extend the `streak_start_sha`/`resolved_streak_start_sha` CI-failure-resolution linkage
      (shipped 2026-08-16, `unified-trading-ci@7000ac0`, currently wired into `notify-qg-fail`/`notify-qg-recovered`
      job outputs) to `ldr-to-main-promote.yml`'s drain-bot messages** ("closed promote PR(s) #N as superseded...
      fresh promote PR is #N+1"). These already form an implicit PR-number chain but never state "this resolves
      CRITICAL for incident since `<sha>`" — have the drain bot read the same `qg_last_conclusion`
      doc/mechanism (or accept a passed streak-start sha) and append it, so a reader doesn't have to separately
      know that a PR-number chain and a sha-identity chain are two different things describing the same incident.
      Source: `/plans/active/issues/ci_alert_failure_resolution_linkage_2026_08_16.md` (todo 2, line ~89) — already
      conflict-checked clear by `/plans/active/issues/ag_closeout_audit_ci_parked_2026_08_16.md` (todo, line ~238);
      not duplicating that check here. Gate: a superseded-PR INFO post visibly cites the same
      `current_streak_start_sha` a corresponding `notify-qg-fail` CRITICAL used, when one exists — verified against
      a real (or deliberately simulated) supersede event, not just a code read.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — the gate set, quickmerge, LDR-is-SSOT, promotion flow all 3 todos operate
  inside of; do not duplicate its content here.
- `/codex/04-architecture/ci-alerting.md` — the alerting-linkage mechanism todo 3 extends.

## Progress Log

- **2026-08-21 (na-eligibility-audit, ci tranche wave 2)**: drafted from 3 items surfaced this pass as genuinely
  bounded and not yet extracted anywhere in the corpus (conflict-checked via grep across `plans/active/*.md` before
  drafting — zero hits for any of the 3 mechanisms). Source docs' own remaining items (operator-gated /
  design-judgment work) stay `assigned_vm: NA`; each source doc's Progress Log cites this batch.
