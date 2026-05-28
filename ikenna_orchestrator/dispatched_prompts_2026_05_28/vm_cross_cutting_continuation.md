You are an orchestrator worker on vm-cross-cutting (epic VM owning infrastructure_master + batch_live_symmetry_master +
observability_master + client_isolation_and_governance_master). Model tier: sonnet-doable, thinking: medium. AUTONOMOUS
background run — operator's laptop is offline; you complete the bundle alone.

STEP 0 — read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` + `unified-trading-pm/CLAUDE.md` HARD
RULES (Commit+Push+Flip, QG, Single-walk discipline).

STEP 1 — SYNC FRESH in every repo you'll touch — `unified-api-contracts`, `unified-trading-library`,
`market-tick-data-service`, `instruments-service`, `features-service`, `strategy-service`, `execution-service`,
`batch-live-reconciliation-service`, `deployment-ui`, `unified-trading-pm`: git fetch origin live-defi-rollout && git
rebase origin/live-defi-rollout

STEP 2 — BUNDLE (continuation of laptop slot 10):

Plan — `plans/active/pipeline_mode_implementation_2026_05_28.md` (P1, refactor class, ~2.4 cal AI-days, parent_epic
batch_live_symmetry_master).

Operator decided 2026-05-28: IMPLEMENT (vs REMOVE). Do NOT re-propose REMOVE. CLAUDE.md "Single-walk discipline" —
partition is DEFERRED Phase 5; named successor only.

Execute Phases 0 → 6 in order. Phase 0 audit doc → `plans/active/pipeline_mode_audit_2026_05_28.md`. Phase 3 backfill
uses `unified_trading_library.cloud_interface.gcs_*_object` (NEVER subprocess gsutil).

After completion: edit `plans/active/cefi_venue_backfill_coverage_remediation_2026_05_27.md` §6I pipeline_mode item to
`[x] ✅ — resolved by pipeline_mode_implementation_2026_05_28.md`.

STEP 3 — SHIP DISCIPLINE (HARD RULE): QG green per repo before merge; commit + push HEAD:live-defi-rollout per shippable
unit; flip plan checkbox same-turn with `docs(plans):` commit + evidence. Side-discoveries → todos. Operator gates →
ping.

Begin with STEP 0.
