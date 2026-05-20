# Slot 6 — A3 DeFi MISSING_EXPECTED remediation (current) + Phase 9 + Phase 11 (post-unfreeze)

**Host**: AWS VM (`/home/ubuntu/unified-trading-system-repos/.tabs/6/`) **Model**: Sonnet 4.6 · high effort **Master
coordinator**: `unified-trading-pm/plans/active/data_pipeline_master_coordination_2026_05_20.md` **Work-split row**:
`unified-trading-pm/plans/active/work_split_2026_05_20_ikenna.md` § Slot 6

---

## Phase DAG (parallel where possible — master coordinator is authoritative)

| Phase                                                                | Status (as of 2026-05-20)                        | Your role                                                     |
| -------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------- |
| **-2** Strategy/ML consolidation finish (Bucket 3 stale-ref cleanup) | 🟡 IN PROGRESS — dispatched per-slot             | **Read `ikenna_orchestrator/pings/slot_6.md` for your slice** |
| **-1** Workspace-wide QG green                                       | 🟡 IN PROGRESS (slots 9-11 owning Cluster A/B/C) | — (unless your QG passes uncover new violations)              |
| 0 Pre-flight audits                                                  | ✅ DONE (mega-audit Phase A by slot-1 main)      | —                                                             |
| 1 AWS↔GCP bucket-name symmetry                                       | ⚪ READY when Phase 0 GREEN                      | —                                                             |
| 2 CODE FREEZE WINDOW                                                 | ⚪ TRIGGERED by operator after Phase 1           | —                                                             |
| 3 VM fleet drain                                                     | ⚪ Needs Phase 2 active                          | —                                                             |
| 4 GCS bucket migration                                               | ⚪ Needs Phase 3 GREEN                           | —                                                             |
| 5 AWS bucket migration                                               | ⚪ Needs Phase 4 GREEN                           | —                                                             |
| 6 Docker rebuild + redeploy                                          | ⚪ Needs Phase 5 GREEN                           | —                                                             |
| 7 Manifest v8 backfill + label-flip                                  | ⚪ Needs Phase 6 GREEN                           | —                                                             |
| 8 Code-freeze release                                                | ⚪ Needs Phase 7 GREEN                           | —                                                             |
| 9 Denominator/numerator UI fix                                       | ⚪ Post-Phase 8 unfreeze                         | —                                                             |
| 10 QG enforcement upgrade                                            | ⚪ Parallel with Phase 9                         | —                                                             |
| 11 Operational backfill to 100% per asset_group                      | ⚪ Needs Phase 10 GREEN                          | —                                                             |
| 12 Live-data adapter completion                                      | ⚪ Needs Phase 11 batch-side                     | —                                                             |
| 13 Batch-live symmetry verification                                  | ⚪ Needs Phase 12                                | —                                                             |
| 14 Strategy + execution topology cleanup                             | ⚪ Needs Phase 13 GREEN                          | —                                                             |

**Your phase ownership** (filled per slot below).

---

## START HERE — current actionable work

**A3 DeFi MISSING_EXPECTED remediation** — original theme `deployment_ui_lifecycle_tabs` is FROZEN until Phase 8
unfreeze. Until then, your work is closing every DeFi `MISSING_EXPECTED` cell from Phase A audit:

- Plan: `plans/audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md` § A3 DeFi rows
- For each `(venue, data_type, time-range)` MISSING_EXPECTED cell:
  - If data SHOULD have been captured: re-run adapter, backfill
  - If genuinely unavailable: record `empty_confirmed(reason=<typed EmptyConfirmedReason>)`
- NO silent placeholders. NO scope cuts (Data Pipeline Correctness HARD RULE).
- Credential-blockers → file `BLOCKED-CREDENTIALS` ping per CLAUDE.md § "External Data Is Always Available"

**Parallel: Phase -2 Bucket 3** — read `ikenna_orchestrator/pings/slot_6.md`

---

## Future phases (when Phase -2 + dependencies GREEN)

- **Phase 9** Denominator/numerator UI fix — needs Phase 8 (code-freeze release) GREEN
- **Phase 11** Operational backfill (with slots 7, 9) — needs Phase 10 GREEN

---

## Plans-of-record (read these in order)

1. `unified-trading-pm/cursor-configs/CLAUDE.md` — workspace HARD RULES
2. `unified-trading-pm/plans/active/data_pipeline_master_coordination_2026_05_20.md` — phase DAG + dependencies
3. `unified-trading-pm/plans/active/work_split_2026_05_20_ikenna.md` § Slot 6 — your dispatch row
4. `unified-trading-pm/ikenna_orchestrator/pings/slot_6.md` — pings from slot-1 main with detailed assignments
5. (slot-specific plan-refs listed under "future phases" above)

---

## Workspace HARD RULES (non-negotiable)

- **Data Pipeline Correctness Is The Heartbeat** — no scope cuts without operator-acked `BLOCKED-*`
- **Quality Gates Are A Merge Prerequisite** — `bash scripts/quality-gates.sh` exit 0 before push
- **Commit + Push + Flip plan checkbox SAME agent turn** (Half-1 + Half-2)
- **Strategy-LOGIC freeze gate** — surface fixes only on `strategy_service/engine/strategies/v2/`, `engine/allocator/`,
  collateral/liquidation/cross-venue/venue-restriction/deployment-topology-dynamic-config code
- **Foreign-files** — never `git checkout HEAD -- <file>` on dirty foreign files; stash by name
- **Sub-agents** — paste `SUB_AGENT_MANDATORY_RULES.md` at top of every Task spawn

---

## Auto-resolve via main agent

If you /blocked, main agent (`agt-7eb095` on VM) is FIRST responder per `agent-orchestrator/agents/main.md` §
"Auto-resolve worker /blocked questions". It applies the CLAUDE.md + plan-of-record rubric and answers autonomously when
the workspace SSOT is clear.

**Default expectation: the fuller solution** (operator preference 2026-05-20). When asked "do this properly or half-ass
it?", the answer is always properly.
