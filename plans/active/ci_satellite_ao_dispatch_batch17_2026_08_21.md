---
doc_type: plan
title: ci satellite — glue-runner cleanly-inactive/hung-job monitoring-gap extension (batch 17)
summary: >-
  One-todo extraction from /ag-closeout-audit's 2026-08-21 ci-tranche Phase 3 pass, sourced from
  glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md's sole remaining open todo (line ~147, [INFRA] P2). That
  doc's own history flagged this item `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` twice (2026-08-07, 2026-08-18) without
  extracting it, citing only the missing threshold-N as the blocker. Fresh read this pass: the doc already names
  the target script, target host, and both concrete failure signatures in full log-line detail — the missing N is
  a reasonable-default choice, not an open design fork, so this batch extracts it with a stated starting default.
status: draft
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, ao-dispatch, satellite, batch-17, ag-closeout-audit, glue-runner, monitoring-gap]
related:
  [
    /plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_ci_parked_2026_08_21.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
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
    /plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md,
    scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/04-architecture/ci-alerting.md,
  ]
source:
  [
    "ag-closeout-audit ci tranche, 2026-08-21 Phase 3 — extracted verbatim from
    glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md's sole remaining open todo (line ~147, [INFRA] P2).",
  ]
---

# ci satellite — glue-runner cleanly-inactive/hung-job monitoring-gap extension (batch 17)

> **Fresh carve-out, single-todo, no finalize twin** (small-batch, no-finalize-twin precedent — infra batch1/batch4/
> batch5/batch19/batch20, ao batch4). `status: draft` / `assigned_vm: NA` pending operator review before dispatch.

## Todo 1 — extend the crash-loop watchdog to catch cleanly-inactive AND hung-mid-job runners

- [ ] [INFRA] P2. **Extend `scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh`** (target host:
      `i-042a6332509482556`, the CI-runner VM — NOT the old orchestrator VM `i-0c9b283b31d6b5ca7`, per this doc's
      own 2026-08-15 VM-naming-disambiguation fix) to catch two failure shapes the existing crash-loop check
      structurally misses — extracted verbatim from `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`'s
      sole remaining open todo:
      1. **Cleanly-inactive/stopped**: alert when any expected `github-glue-runner-<repo>@glue-1.service` (or
         `@writer-N`) unit is `inactive`/`dead`/`failed` for more than a threshold while peer runners on the same
         host are active — this is the doc's own original 2026-08-04 incident class (`Restart=always` suppressed by
         an explicit external `systemctl stop`, so the unit sits silently stopped, never crash-looping, and the
         existing watchdog's `NRestarts`/`SubState=auto-restart` check never fires on it).
      2. **Active-but-hung mid-job**: alert on a runner whose `journalctl` shows a "Running job: ..." line with no
         matching completion line for more than a threshold, independent of systemd's `ACTIVE` state (which stays
         green throughout this failure mode) — the doc's own 2026-08-05 addendum, a THIRD failure shape found live
         (`writer-1/2/3` stuck mid-job ~2h with GH-API `offline`+`busy` simultaneously).
      **Threshold default** (not previously stated by the source doc — pick a reasonable starting value, not an
      open design fork): 15 minutes for both signatures, matching the ~15-30min SLA already used elsewhere in this
      workspace for CI promotion/drain cadences (`/codex/08-workflows/ci-cd-flow.md`) — tune later if it proves too
      noisy or too slow against real fleet behavior; state the chosen value explicitly in the shipped script's
      header comment so a future tuning pass has a documented starting point to diff against. Wire the new checks
      into the SAME existing watchdog service/timer (`github-glue-runner-crash-loop-watchdog.service`) rather than
      a new standalone unit, consistent with the doc's own "extend the watchdog (or add a sibling check)" framing.
      Done-when: a synthetic/dry-run test against a unit forced `inactive` (peer active) alerts; a synthetic hung-
      job journal fixture (a "Running job" line with no completion line past the threshold) alerts; the existing
      crash-loop detection (`Result != success`) is unaffected (0 false positives on a healthy fleet, matching the
      existing `879e3e109` fix's own verification bar); `quality-gates.sh`-green, shipped via `quickmerge.sh --agent
      --files`. Repo: unified-trading-pm.
      **Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
      `glue-runner-crash-loop-watchdog.sh` — only the source doc's own text and the CI/infra parked-audit docs
      (which flag this item, not claim it) reference the file; no other active plan is building this extension.
      Re-verified the doc's own repeated `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` self-flag (2026-08-07, 2026-08-18,
      2026-08-21) — every prior pass declined to extract solely because the doc didn't state a threshold N; this
      pass supplies one rather than treating the missing default as a permanent blocker.

## Progress Log

- **ag-closeout-audit 2026-08-21 (ci tranche, Phase 3)**: drafted. Extracted from
  `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`'s sole remaining open todo after re-reading the doc
  fresh (458 lines, full history) rather than trusting the parked-audit doc's one-line taxonomy alone. Judgment
  call made explicit: the doc's own 3 prior audits treated the missing threshold-N as disqualifying; this pass
  treats a stated reasonable default as sufficient to extract, since the rest of the spec (script, host, both
  failure signatures, wiring target) was already fully bounded. Source doc's own todo annotated `➡️ EXTRACTED` in
  the same pass.
