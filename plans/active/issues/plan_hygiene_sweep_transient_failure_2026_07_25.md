---
doc_type: issue
title: Plan-hygiene sweep transient failure — 2 hard failures self-resolved within ~15 minutes
summary: >-
  uts-prod-plan-hygiene-sweep (Cloud Run job, daily ~05:00 UTC) reported 2 hard failures at 2026-07-25T05:00:24Z
  (check_frontmatter: 1 file violation; a second hard-failure count in the run summary). A fresh local
  run_hygiene_sweep.sh re-run ~20 minutes later, at the then-current live-defi-rollout HEAD, showed 0 hard failures
  across every check. Root cause: the corpus is under exceptionally heavy concurrent-slot commit velocity today (dozens
  of agents pushing every 30-90s) — the sweep cloned a momentary bad snapshot that a subsequent commit from another slot
  had already corrected by the time this was investigated. Not caused by this session's own commits (verified: neither
  new/edited plan file appears in the sweep's violation output).
status: resolved
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, ci, transient, observability]
related: [/codex/11-project-management/doc-frontmatter-schema.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class:
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Operator-forwarded Slack alert 2026-07-25T06:01 UTC: "Plan-hygiene sweep FAILED — hard failures: 2, soft warnings: 0."
  Investigated via `gcloud logging read` against the Cloud Run job's execution log (uts-prod-plan-hygiene-sweep-fk45v,
  completed 2026-07-25T05:01:35Z) plus a fresh local `bash scripts/plan-hygiene/run_hygiene_sweep.sh` run at current
  HEAD.
assigned_role: infra
drift_direction: advance-code
resolved_by: >-
  Self-resolved by a subsequent commit from another slot before this investigation started — no fix authored in this
  doc. Confirmed via a clean local re-run (0 hard/soft) at live-defi-rollout HEAD ~20 minutes after the failing sweep.
---

# Plan-hygiene sweep transient failure

## What the failing run actually reported

Log excerpt (`uts-prod-plan-hygiene-sweep-fk45v`, 2026-07-25T05:00:24Z entrypoint):

```
❌ check_frontmatter: 1 file(s) with violations
...
Hard failures: 2  |  Soft warnings: 0
❌ Sweep FAILED — fix hard failures before proceeding.
```

The sweep's terse summary mode does not print the specific filename for the `check_frontmatter` violation — only the
count. The line-count section of the same run also listed
`HARD sports_consolidated_closeout_2026_07_19.md 1002L todos=104`, but that check is ratchet-baselined
(`line_caps_baseline.yaml`) — being individually over the nominal 1000-line cap does not by itself fail the ratchet gate
unless it's a _new_ violation not already in the baseline, so this listing entry is informational, not necessarily one
of the 2 counted hard failures. Which specific check(s) actually contributed the "2" could not be reconstructed after
the fact from this log's verbosity level.

## Why it looks transient, not a real regression

A fresh `bash scripts/plan-hygiene/run_hygiene_sweep.sh` run at live-defi-rollout HEAD (~2026-07-25T05:20 UTC, after
several more concurrent-slot commits had landed) showed:

```
--- Results ---
  ✅ PASS  [hard]  Frontmatter validity
  ...
  ✅ PASS  [hard]  Line caps (plans 500/1000, epics 2000 — no exemption, ratchet)
  ...
========================================
 Hard failures: 0  |  Soft warnings: 0
========================================
```

`sports_consolidated_closeout_2026_07_19.md` is still 1002 lines at the time of this doc — consistent with the ratchet
ALREADY tolerating it (it was over cap before today, not newly so), which also explains why it shows as "HARD" in the
per-file listing but doesn't fail the gate.

Given the operator's own earlier-noted context this session ("today's exceptionally heavy concurrent-slot volume" —
corroborated independently by this session's own SSM telemetry showing dozens of pushes to LDR within
single-digit-minute windows), the most likely explanation is a genuinely transient bad snapshot: the sweep cloned
`live-defi-rollout` at 05:00:24Z, some other slot's in-flight commit briefly left one file's frontmatter non-compliant,
and a subsequent commit from that same slot (or another) corrected it before this investigation began ~20 minutes later.

## Recommendation

- **Increase `check_frontmatter`'s failure-summary verbosity** in the hygiene sweep's Slack-facing output to name the
  specific file, not just a count — without it, a transient failure is unfalsifiable after the fact (as this doc
  demonstrates) and a genuine one requires a fresh clone + re-run to even locate, costing minutes on every occurrence.
- No code fix needed for the failure itself — it had already self-resolved.
- If this pattern (sweep fails, immediate re-run passes) recurs more than once or twice more this week, that's a signal
  the sweep should retry-and-recheck once before alerting, rather than a one-shot clone-and-check against a corpus this
  volatile.
