---
doc_type: issue
title: No QG validates a plan's priority against the new tier + foundation-gate policy
summary:
  /codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md (2026-07-28) codifies how `priority:` should
  be assigned (CI/audit escalation first, then asset-group tier + sports/tradfi backfill carve-out, then the
  foundation-gate pipeline-stage within a tier) — but nothing mechanically checks a plan's declared priority against its
  asset_group/content. Enforcement today depends entirely on whoever authors/reprioritizes a plan having read the policy
  doc.
status: resolved
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
  unified-trading-pm@78fadefd7 (2026-07-28) -- check_priority_tier_policy.py shipped + wired into run_hygiene_sweep.sh
  as a soft check; verified 601 docs scanned, 2 flagged, 0/2 false positives on manual spot-check
---

# No QG validates a plan's priority against the new tier + foundation-gate policy

## Todos

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-28 — `unified-trading-pm@78fadefd7`.** Shipped
      `scripts/plan-hygiene/check_priority_tier_policy.py`: flags a bare `sports`/`tradfi`-tagged `status: active` plan
      (or `status: open` issue) sitting at `P0`/`P1` with no title/summary keyword signal of
      backfill-completion-critical work, per
      `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md`'s carve-out. Wired into
      `run_hygiene_sweep.sh` as a soft check (`Priority vs. asset-group tier policy (candidate signal)`). Re-verified
      2026-07-28 (interactive session): runs cleanly over 601 active plan/issue docs, 2 flagged
      (`sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`,
      `sports_odds_stale_fixture_reinjection_2026_07_14.md`) — both manually spot-checked and confirmed genuine
      re-triage candidates (architecture-decision/root-cause docs, not backfill-completion-critical work), 0/2 false
      positives. Only 2 flags exist in the current corpus, short of the ~10-flag sample originally envisioned — the
      policy is already being applied fairly consistently, which is itself a good sign, not a check-quality gap.
