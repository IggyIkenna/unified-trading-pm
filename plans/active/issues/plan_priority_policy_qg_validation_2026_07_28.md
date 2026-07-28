---
doc_type: issue
title: No QG validates a plan's priority against the new tier + foundation-gate policy
summary:
  /codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md (2026-07-28) codifies how `priority:` should
  be assigned (CI/audit escalation first, then asset-group tier + sports/tradfi backfill carve-out, then the
  foundation-gate pipeline-stage within a tier) — but nothing mechanically checks a plan's declared priority against its
  asset_group/content. Enforcement today depends entirely on whoever authors/reprioritizes a plan having read the policy
  doc.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, priority, quality-gate, orchestrator]
related:
  [
    /codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md,
    /codex/11-project-management/foundation-completion-gate-discipline.md,
  ]
created: "2026-07-28"
parent_epic: agent_operating_framework_master
source:
  Operator ruling 2026-07-28 (Ikenna) — priority policy should be "canonical... so new tasks come into the flow as
  expected," which needs mechanical enforcement, not just a doc, to actually hold over time.
assigned_vm: NA
execution_scope: local-only
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# No QG validates a plan's priority against the new tier + foundation-gate policy

## Todos

- [ ] [SCRIPT] P2. Write a `scripts/plan-hygiene/check_priority_tier_policy.py` (or extend `run_hygiene_sweep.sh`) that
      reads every `status: active` plan's `asset_group` + `priority`, and flags (soft-warn to start, ratchet to hard
      later per this workspace's usual pattern) any plan whose priority looks inconsistent with
      `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md` — e.g. a bare `sports`/`tradfi`-tagged
      plan sitting at `P0`/`P1` with no title/content signal of backfill-completion-critical work (title/summary keyword
      heuristic is enough for a first pass; this is advisory, not a hard block, since "is this really backfill-critical"
      is a judgment call the doc itself says needs reading, not just regexing). Definition of done: the script runs
      cleanly over the current active-plan corpus, reports its own false-positive rate on a manual spot-check of ~10
      flagged plans, and is wired into the daily hygiene sweep as a SOFT (warn-only) check.
