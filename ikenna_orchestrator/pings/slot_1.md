# Slot 1 — Main Orchestrator Intra-Side Ledger

## [slot 1 main] Operator decisions locked + coordination ledger filed — 2026-05-13

**Status**: ✅ DECISIONS LOCKED; 🟡 AWAITING HARSH-MAIN PHASE 6.x STATUS

**What filed**:

### Phase 6.3 Orphaning Decision

- **Decision**: CHOSEN Option B (Ikenna spawns emergency Slot 6+ tab post-Slot-7/8 close)
- **Rationale**: Single-operator coordination preferred; Ikenna proven at sub-agent fan-out; Harsh-side at capacity with manifest + codex work
- **Timeline**: 3–4 calibrated AI-days within cycle margin (estimated Day 3 AM start)
- **Scope**: `features-service/features_service/volatility/` module emission semantics
  - Add `_check_emission_policy()` call in cross-module orchestrator
  - Add `_apply_emission_policy()` logic to volatility writer
  - Wire `publish_with_policy()` on output
  - Add 4–6 unit tests (STRICT_FAIL, NAN_FILL × full, partial completeness)
  - QG check (lint/format/basedpyright/codex/import-patterns)
- **Reference pattern**: Slot 7 commits `features-service@5e24a18c` (cross_instrument) + `@6cbf50ff` (delta_one) show exact pattern
- **Documentation**: `plans/active/issues/writegate_phase_6_3_features_volatility_orphaned_2026_05_13.md` (Decision section updated; locked by live-defi-rollout)

### Wallet Treasury Design Decisions Acked (Q1–Q5)

- **Q1** ✅ Slot 4 Phase 3.D `/api/treasury/rollup` endpoint ready by Day 1 EOD — **confirmed**
- **Q2** ✅ Require backend Phase 6.A live before wallet UI — **confirmed**
- **Q3** 🔄 DEFERRED: Simple button-click stub for May-23 cutover; real HMAC-signed approval chain post-cutover
- **Q4** ✅ Daily HWM crystallization confirmed — **confirmed**
- **Q5** 🔄 DEFERRED: Stubs (Cloud-KMS-only signing) for May-23; real Copper + CEFFU integration June-1+

**Successor plan filed**: `wallet_treasury_post_cutover_custody_signing_2026_06_01.md`
- **Scope**: Q3 + Q5 deferred work (real signing + real custody + audit immutability)
- **Phases**: 
  - Phase 1: Real withdrawal approval chain (HMAC-SHA256 + 2-of-N multisig) — 3.2 cal days, June 3 milestone
  - Phase 2: Real Copper + CEFFU integrations — 4.8 cal days, June 10 milestone
  - Phase 3: Compliance + GCS audit log immutability (7-year retention lock) — 1.6 cal days, June 12 milestone
- **Total**: 9.6 calibrated AI-days across 15-day post-cutover window
- **Handoff trigger**: May-23 cutover completion + 48-hour live smoke green; operator signals go-ahead for Phase 1

### Coordination Artifacts Filed

- **PM Coordination Ledger** (pm_coordination_ledger_2026_05_13.md): Consolidated view of 2 cross-side pings + 8 slot status + 7 active issues + blocker matrix + operator-pending decisions (P0/P1/P2 triage targets)
- **Cross-side pings** (2 filed):
  1. Phase 6.3 orphaning (11:30 UTC) — OPTIONS A/B/C, CHOSEN Option B, awaiting Harsh-main ack
  2. Phase 6.x status request (11:45 UTC) — Gate 1 fired; requesting Harsh confirmation on Phase 6.6/6.7/6.9 status

---

## [main ↔ slot] Open Questions

| Question | Status | Blocker? | Notes |
|----------|--------|----------|-------|
| **Harsh-main Phase 6.6/6.7/6.9 status** | 🟡 AWAITING RESPONSE | ✅ YES (Gate 4) | 2h response target; affects Gate 4 fire timing |
| **Gate 3 phantom audit runbook ownership** | ✅ ASSIGNED | ❌ NO | Ikenna Slot 1 main = operational owner; runbook ready (`gate_3_phantom_audit_runbook_2026_05_13.md`) |
| **Non-blocking issue routing** | 🟡 IN PROGRESS | ❌ NO | 4 issues to route (sports, strategy, audit, blank-reason); 1 to archive (bookmaker_registry) |

---

## [main → slots] Status Update + Upcoming Milestones

**Current tab registry** (as of 2026-05-13 ~15:00 UTC):
- Slot 2: defi_catalogue Phases 1–3 (status: UNKNOWN, awaiting update)
- Slot 3: code_freeze Phase 1 audit + apply-flips (status: ✅ COMPLETE, ready for Phase 2)
- Slot 4: api_keys_wallets scope-contracted (status: UNKNOWN, Phase 3.D Treasury.rollup due Day 1 EOD)
- Slot 5: defi_recursive_borrow Phase 1–2 design (status: ⏸ GATED ON SLOT 2)
- Slot 6: defi_simulation_realism Phase 1–3 design (status: UNKNOWN, AMM matrix due Day 2 noon)
- Slot 7: simulation_scenarios Phase 1–2 (status: ✅ SHIPPED, ready for Phase 3 scenario runner integration)
- Slot 8: cross_cutting #4 + manifest Phase 3 (status: ✅ SHIPPING D1+D4 HELPERS, manifest Phase 3 ready to start)
- **Slot 6+** (TBD): Phase 6.3 volatility emission semantics (FUTURE SPAWN — estimated Day 3 AM, after Slot 7+8 close)

**Upcoming critical milestones**:
1. **TODAY (2026-05-13) by 15:00 UTC**: Harsh-main must ack Phase 6.3 Option B decision
2. **TODAY by 18:00 UTC**: Harsh-main must confirm Phase 6.6/6.7/6.9 status + Ikenna-main route non-blocking issues + archive resolved issues
3. **EOD (2026-05-13)**: Master plan inventory refresh (active-plan-inventory-tracker.py regenerate)
4. **Day 2 AM**: Expect Slot 6+ spawn (Phase 6.3 volatility) if Day 1 evening Slot 7+8 completions hold

---

## Notes

**Why this structure**: Per CLAUDE.md "Daily Work-Split Process," Slot 1 main files intra-side pings for coordination with spawned slots. Cross-side coordination goes through `plans/active/_agent_pings.md` (workspace-shared with Harsh-side). This file (Slot 1 ledger) documents main-orchestrator status + pending decisions + upcoming spawns.

**Commit**: unified-trading-pm@490c96a0 (docs(decisions): Phase 6.3 Option B + wallet_treasury post-cutover plan)
