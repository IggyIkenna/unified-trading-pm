# Slot 8 — defi_catalogue close + R-NEW-6 detector candidate (Phase 14 ownership)

**Host**: AWS VM (`/home/ubuntu/unified-trading-system-repos/.tabs/8/`) **Model**: Sonnet 4.6 · high effort **Master
coordinator**: `unified-trading-pm/plans/active/data_pipeline_master_coordination_2026_05_20.md` **Work-split row**:
`unified-trading-pm/plans/active/work_split_2026_05_20_ikenna.md` § Slot 8

---

## Phase DAG (parallel where possible — master coordinator is authoritative)

| Phase                                                                | Status (as of 2026-05-20)                        | Your role                                                     |
| -------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------- |
| **-2** Strategy/ML consolidation finish (Bucket 3 stale-ref cleanup) | 🟡 IN PROGRESS — dispatched per-slot             | **Read `ikenna_orchestrator/pings/slot_8.md` for your slice** |
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

**Two parallel themes** (both can start NOW):

(1) **R-NEW-6 detector candidate — PROTOCOL_PAUSE_WINDOWS populator** — build the detector that auto-populates
`unified_api_contracts/registry/protocol_pause_windows.py` from on-chain events (Aave V2 / Compound V2 / Curve exploit
pause windows). Per operator round 4: **detector-populated, NOT operator-typed**. Reference:
`is_protocol_paused(protocol, chain, target_date)` is the consumer; you build the populator.

(2) **defi_catalogue close** — SSOT cataloguing of every DeFi protocol/chain/asset combo.
`EMPTY_OR_DEPRECATED_DEFI_VENUES` + `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` properly typed. UAC:
`registry/capability_declarations/_defi.py`.

**Parallel: Phase -2 Bucket 3** — read `ikenna_orchestrator/pings/slot_8.md`

---

## Future phases (when Phase -2 + dependencies GREEN)

- **Phase 14** Strategy + execution topology cleanup (with slot 5) — needs Phase 13 GREEN. Your slice = defi_execution
  wiring.

**Pyth UNBANNED 2026-05-06** for Solana on-chain price feeds. Chainlink for other chains.

---

## Plans-of-record (read these in order)

1. `unified-trading-pm/cursor-configs/CLAUDE.md` — workspace HARD RULES
2. `unified-trading-pm/plans/active/data_pipeline_master_coordination_2026_05_20.md` — phase DAG + dependencies
3. `unified-trading-pm/plans/active/work_split_2026_05_20_ikenna.md` § Slot 8 — your dispatch row
4. `unified-trading-pm/ikenna_orchestrator/pings/slot_8.md` — pings from slot-1 main with detailed assignments
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
