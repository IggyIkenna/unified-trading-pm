# Slot 3 — code_freeze §2.0-2.5 + batch_live_symmetry T1-3 (Phase 1, 3, 4, 13 ownership) + Phase 11f Bucket 3

**Host**: AWS VM (`/home/ubuntu/unified-trading-system-repos/.tabs/3/`) **Model**: Sonnet 4.6 · high effort **Master
coordinator**: `unified-trading-pm/plans/active/mtds_mdps_master.md` **Work-split row**:
`unified-trading-pm/plans/active/work_split_2026_05_20_ikenna.md` § Slot 3

---

## Phase DAG (parallel where possible — master coordinator is authoritative)

| Phase                                                                | Status (as of 2026-05-20)                        | Your role                                                     |
| -------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------- |
| **-2** Strategy/ML consolidation finish (Bucket 3 stale-ref cleanup) | 🟡 IN PROGRESS — dispatched per-slot             | **Read `ikenna_orchestrator/pings/slot_3.md` for your slice** |
| **-1** Workspace-wide QG green                                       | 🟡 IN PROGRESS (slots 9-11 owning Cluster A/B/C) | — (unless your QG passes uncover new violations)              |
| 0 Pre-flight audits                                                  | ✅ DONE (mega-audit Phase A by slot-1 main)      | —                                                             |
| 1 AWS↔GCP bucket-name symmetry                                      | ⚪ READY when Phase 0 GREEN                      | —                                                             |
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

**Two things in parallel** (both unblocked NOW):

(1) **Phase -2 Bucket 3 Phase 11f** — finish strategy consolidation tail consumers per
`ikenna_orchestrator/pings/slot_3.md`:

- alerting-service: `risk_rule_event_handler.py:3`, `core/system_health_aggregator.py:26`,
  `subscribers/batch_event_reader.py:40` — rewire to strategy-service
- trading-agent-service: `config.py:126`, `adapters/risk_adapter.py:1,20` — HTTP client base URLs + adapter imports →
  strategy-service
- system-integration-tests + e2e-testing — any archived-service references
- Out-of-scope: DEPRECATION_NOTICE / CHANGELOG / migration-history / docstring headers
- Plan: `strategy_repo_consolidation_2026_05_19.md` Phase 11f
- Gate: per-repo `bash scripts/quality-gates.sh` GREEN

(2) **Phase 1** AWS↔GCP bucket-name symmetry — paired with slot 2 (split the repos; coordinate via /progress)

---

## Future phases (when Phase -2 + dependencies GREEN)

- **Phase 3** VM fleet drain (with slot 2)
- **Phase 4** GCS bucket migration (with slot 2)
- **Phase 13** Batch-live symmetry verification T1-T3 — needs Phase 12 GREEN
- Existing batch_live_symmetry T1-T3 work continues; T4-T7 owned by slot 9 post-unfreeze

---

## Plans-of-record (read these in order)

1. `unified-trading-pm/cursor-configs/CLAUDE.md` — workspace HARD RULES
2. `unified-trading-pm/plans/active/mtds_mdps_master.md` — phase DAG + dependencies
3. `unified-trading-pm/plans/active/work_split_2026_05_20_ikenna.md` § Slot 3 — your dispatch row
4. `unified-trading-pm/ikenna_orchestrator/pings/slot_3.md` — pings from slot-1 main with detailed assignments
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
