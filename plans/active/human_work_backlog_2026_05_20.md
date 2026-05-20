---
title: Human-work backlog 2026-05-20 — operator + Harsh interactive tasks
type: organizing-plan
status: active
created: 2026-05-20
operator: ikenna
co-operators: [harsh]
related:
  - cursor-configs/CLAUDE.md § "Human-vs-Agent work split"
  - plans/active/data_pipeline_master_coordination_2026_05_20.md
  - plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md
---

# Human-work backlog — slots 1 (Ikenna) + 2 (Harsh) — 2026-05-20

> Operator 2026-05-20: "audit pm active plans and assign outside the slots to ikenna and harsh as human tasks on slot 1,
> that way we can still track them and they are expected to be claude opus interactive tasks. slots 2-18 (was 22) remain
> centralised work load for the central vm."
>
> The principle: **human judgment work** (audits, architectural decisions, archetype design, plan curation, operator UX)
> ≠ **agent work** (QG sweeps, Phase X execution, code cleanup, doc rollout). Both are tracked in backlog.yaml, but
> human work goes to slot 1 (Ikenna's mac) or slot 2 (Harsh's pc) where Claude Opus interactive sessions claim them. The
> dashboard shows them with the same accountability as agent work.

## Slot allocation (2026-05-20 reorganisation)

| Slot range | Host             | Operator                             | Work type                                                                            |
| ---------- | ---------------- | ------------------------------------ | ------------------------------------------------------------------------------------ |
| **1**      | Ikenna local mac | Ikenna interactive (Claude Opus 4.7) | Human judgment: orchestration, audits, plan curation, archetype design               |
| **2**      | Harsh local pc   | Harsh interactive (Claude Opus 4.7)  | Human judgment: testing, performance work, paper-trade validation                    |
| **3-20**   | Centralized (VM) | Spawned Sonnet 4.6 workers           | Agent execution: QG sweeps, Phase X tasks, code cleanup, doc rollout                 |
| (separate) | VM               | Main agent `agt-7eb095` (Opus 4.7)   | Auto-resolve /blocked, dispatch phase progression. NO slot — lives in `/api/agents/` |

**Tier marker**: human-work items use `tier: human-task` in backlog.yaml. The dispatcher does NOT auto-dispatch these
(target_slot ∈ {1, 2} is operator-claimed only). They appear in the dashboard's slot-1/slot-2 panel.

## Curated human-work items (initial seed)

Audited from `plans/active/issues/*.md` and `plans/active/*.md` files. Each item ships as a backlog.yaml entry with
`target_slot: 1` or `2`, `tier: human-task`, `affinity: high`.

### Ikenna (slot 1) — orchestration / architecture / archetype work

1. **HUMAN-IKENNA-ARCHETYPE-AUDIT** — `strategy_archetype_logic_audit_2026_05_20.md` D1-D14 dimensions. Operator-acked
   tonight to run in parallel with consolidation. **Status: in-progress (operator session).** Est: 8 cal-AI-days.

2. **HUMAN-IKENNA-MEGA-AUDIT-PROGRESSION** — `mega_audit_and_plan_beefup_progression_2026_05_20.md`. Master audit
   tracker; needs ongoing curation as items close. Est: 1 cal-AI-day rolling.

3. **HUMAN-IKENNA-DATA-PIPELINE-COORDINATION** — `data_pipeline_master_coordination_2026_05_20.md`. Phase sequencing
   decisions when blockers surface. Est: 0.5 cal-AI-day rolling.

4. **HUMAN-IKENNA-CROSS-CLIENT-ISOLATION-AUDIT** —
   `issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md`. HARD RULE codified 2026-05-20; needs
   validation pass across existing code. Est: 1 cal-AI-day.

5. **HUMAN-IKENNA-PROMOTE-WORKFLOW-REVIEW** — review the promote workflow architecture before May-23 cutover.
   Critical-path call: paper_1d → live_early tonight, live_full post-cutover. Est: 0.5 cal-AI-day.

### Harsh (slot 2) — testing / performance / paper-trade

6. **HUMAN-HARSH-E2E-PAPER-TRADE-DRY-RUN** — operator instruction: "e2e paper trading stuff like that". Drive the
   paper-trade scenarios end-to-end with mocked + real data, validate the promote flow. Est: 2 cal-AI-days.

7. **HUMAN-HARSH-MDPS-FEATURES-PERF-MOCK** — operator instruction: "performance improvements for MDPS and features vm
   using mock data that kinda stuff". Drive perf benchmarking + optimization pass with mock data fixtures. Est: 2
   cal-AI-days.

8. **HUMAN-HARSH-LIVE-PIPELINE-VALIDATION** — `live_pipeline_mtds_mdps_features_2026_05_08.md` exit criteria. Validate
   live-mode adapter behavior matches batch-mode (per the live=batch HARD RULE). Est: 1 cal-AI-day.

9. **HUMAN-HARSH-DEPLOYMENT-FLOW-VALIDATION** — `codex/08-workflows/deployment-flow.md` LDR → staging → main path. Drive
   a full promote → live cycle on a non-critical service to validate the flow before May-23. Est: 0.5 cal-AI-day.

10. **HUMAN-HARSH-LAPTOP-MIGRATION-COMPLETE** — `codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md` Steps
    1-8. Self-onboarding to the shared agent-orchestrator from `orch.epiphanytechnologies.com`. Est: 0.5 cal-AI-day.

## How these flow through the dashboard

- Each item lands in `backlog.yaml` with `tier: human-task`, `target_slot: 1` or `2`, `affinity: high`
- Dispatcher does NOT auto-dispatch them (treats them as operator-claimed)
- Dashboard Fleet tab shows slot 1 with the queued list + slot 2 the same
- Operator/Harsh interactive session reads the slot's current_task on /boot OR queries the backlog manually
- /done flow same as agent workers: SHA + evidence

## When to add new human-work items

Any plan/issue that surfaces with one of these signals:

- Frontmatter `locked_by` + decision needed
- `BLOCKED-OPERATOR-DECISION` in body
- Master coordinator phase that says `operator-acked` or `human-only`
- Architectural call (cross-repo design, new module, breaking interface)
- Audit work requiring full-context Opus reasoning (Mega Audit, archetype audit, etc.)

Filing recipe: edit `unified-trading-pm/harsh_orchestrator/backlog.yaml` with a new entry; POST `/api/backlog/reload`;
the new task appears in slot 1's queue on next dashboard refresh.

## Slot 2 takeover plan (next session)

Slot 2 currently has a worker doing Phase 1 bucket symmetry. Migration:

1. Wait for worker to /done current commit (or operator-graceful /reassign-park)
2. POST `/api/slots/2/pause` — orchestrator stops dispatching
3. Worker tmux session stays alive — operator/Harsh can attach + claim human tasks from backlog
4. New centralised workers spawn into slots 12-20 to replace the slot-2 worker's capacity

Slot 1 already paused (2026-05-20 evening).
