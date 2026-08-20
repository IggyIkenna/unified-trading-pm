---
doc_type: plan
title: Anthropic per-task spend calibration — operator-gated items (forked per finding Y)
summary: >-
  Companion NA doc for anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md, forked per
  task_template.md §3 finding Y — the source AO plan carries 27 plain dispatchable todos plus one genuinely
  operator-only item; interleaving them blocks the AO plan's own archival on a human-gated line long after every
  worker-dispatchable todo is done. This doc holds that one item so the source plan can reach zero open todos
  independently.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, operator-items, finding-y, billing, anthropic]
related:
  [
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md,
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_finalize_2026_08_10.md,
    /plans/active/task_template.md,
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
effort: low
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
context_scope:
  [
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md,
    /plans/active/task_template.md,
    scripts/dev/log-laptop-login-identity.py,
  ]
source: >-
  Forked 2026-08-19 out of anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md's own open todo
  (line ~354 as of the fork), per task_template.md §3 finding Y and the Track-A/B classification pass run from
  ao_open_work_consolidated_tracker_2026_08_14.md Track 7. Classification: GENUINE, not a mis-tag — the action
  structurally requires the operator's own laptop (`~/.claude.json`), unreachable from an AO VM worker. A prior
  2026-08-18 re-check (Track 7 Progress Log) already confirmed this same item is not a mis-tag but stopped short of
  forking it out; this doc completes that step.
---

# Anthropic per-task spend calibration — operator-gated items

> **LOCAL / human plan** (`assigned_vm: NA`) — forked out of
> `/plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md` so that AO plan's 27 plain
> dispatchable todos are never blocked from archival by this one human-only line. Not a delete/downgrade of the
> item — it stays tracked here, exactly as before.

## Todo

- [ ] [OPERATOR] P2. **LAPTOP-ONLY — log the laptop's login identity on change, as ASSURANCE that the reservation held
      (no longer time-critical, and no longer for attribution).** Downgraded from P0 on 2026-08-10 evening: its
      original purpose was to attribute laptop turns to the right account for calibration, and the reservation makes
      that unnecessary — the calibrated accounts are AO-exclusive, so laptop turns land on a DIFFERENT account
      entirely and cannot enter their windows. What remains is genuinely useful but smaller: a log of
      `(timestamp, accountUuid, emailAddress)` from `~/.claude.json`'s `oauthAccount` is the only way to EVIDENCE that
      the laptop never logged into `sub-a` or `sub-e`, which is exactly what the reservation-verification todo needs
      to check rather than assume. No longer time-critical because nothing is being lost hour by hour: the windows
      that matter start Wednesday. **Script now exists (2026-08-16)**: `scripts/dev/log-laptop-login-identity.py` —
      operator runs `python3 scripts/dev/log-laptop-login-identity.py` on the laptop itself (appends only on identity
      change, idempotent no-op otherwise); log lands at `~/.claude/laptop_login_identity_log.jsonl`. **Done when**:
      the log exists and covers the first post-reset window.

## Progress Log

- **2026-08-19 (Track-A/B classification pass, ao_open_work_consolidated_tracker_2026_08_14.md Track 7)**: Forked
  verbatim out of the source plan's line ~354. Source plan's checkbox replaced with a bold pointer digest line
  (task_template.md §3 finding H convention) + `related:` cross-link added both directions.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
