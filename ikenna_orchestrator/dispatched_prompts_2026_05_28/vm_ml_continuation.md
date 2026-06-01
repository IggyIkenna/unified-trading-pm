You are an orchestrator worker on vm-ml (epic VM owning mtds_mdps_master + features_and_ml_master). Model tier:
sonnet-doable, thinking: medium. AUTONOMOUS background run — commit/push/flip as you ship each unit. The operator's
laptop is offline; you complete the remaining bundle alone.

STEP 0 — MANDATORY BEFORE ANY ACTION:

1. Read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` AND `unified-trading-pm/CLAUDE.md`
   Commit+Push+Flip HARD RULE, QG-merge-prerequisite, Grep-Then-Read-Not-Conclude.
2. The slot you're on is the worktree you booted into; treat your worktree CWD as the slot root.

STEP 1 — SYNC FRESH inside every repo you'll touch — `market-tick-data-service`, `instruments-service`,
`features-service`, `unified-trading-library`, `unified-api-contracts`, `deployment-service`, `unified-trading-pm`: git
fetch origin live-defi-rollout && git rebase origin/live-defi-rollout Abort on autostash conflict (CLAUDE.md
per-tab-worktrees rule). Never stomp foreign dirty files.

STEP 2 — BUNDLE OF WORK (continuation of laptop slots 2 + 5 + 9 — all the same vm-ml epic):

Plan A — `plans/active/cefi_venue_backfill_coverage_remediation_2026_05_27.md`: §2 P0 — honest-absence vs
blocked-credentials. Out-of-window (Tardis code 140) → expected_unattempted; 401 → distinct pending/blocked state (NOT
empty_confirmed). Audit existing rows wrongly stamped empty_confirmed during 401 windows; re-flag. §3 P1 — persist
per-venue free-vs-paid coverage map SSOT (Tardis free = 1st-of-month + recent rolling window; paid = other historical
dates). §6I item 1 P0 — env-tiered bucket cutover (dual-write fix). 0 callsites of `resolve_bucket_name(...)`; consumers
use legacy `cloud_constants.get_bucket_name`. See escalated issue
`plans/active/issues/cefi_bucket_ssot_drift_workspace_wide_2026_05_28.md` (filed by harsh) — execute the workspace-wide
migration path. §6I item 5 P1 — instrument_type case drift normalization (DERIBIT PERPETUAL vs perpetual). Normalize at
write/enumerate boundary + reconcile rows. §6I item 6 P2 — loose unpartitioned `*.parquet` at `raw_tick_data/by_date/`
root — reconcile into partition or delete. §6I item 7 (just added) P0 — one-off sweep of ~355K phantom rows (the slot-9
enumerator fix is preventive only). Write a sweep job (or `--sweep-phantoms` consolidator mode) deleting rows matching:
(a) `data_type IN ('options_chain','futures_chain') AND instrument_type IS NULL/''`, (b)
`(venue, data_type) NOT IN VENUE_DATA_TYPE_CAPABILITIES`. Run on both cefi indexes.

Plan B — `plans/active/features_calc_efficiency_and_correctness_2026_05_27.md` Phase 1 remaining (1.3 batch writes, 1.4
dependency DAG, 1.5 idempotent skip + column pruning) + Phase 2.6/2.7 sanity items (P2/P3).

Tardis key context: paid Tardis subscription is EXPIRED (operator-verified 2026-05-28). Do NOT propose
paid-Tardis-dependent work; "Plans Run To Actual Completion" exempts BLOCKED-OPERATOR-DECISION items. Stay on
code-fixable work.

STEP 3 — SHIP DISCIPLINE (HARD RULE):

- QG green per touched repo before merge.
- Per shippable unit: stage YOUR files by name (never `git add -A`) → commit → `git push origin HEAD:live-defi-rollout`
  (rebase first; other VMs push here too) → IMMEDIATELY same-turn flip the plan checkbox with a `docs(plans):` commit +
  `<repo>@<sha>` evidence.
- Side-discoveries → `- [ ]` plan todo immediately. Operator gates → ping
  `unified-trading-pm/ikenna_orchestrator/_agent_pings.md` (cross-side ledger). Do NOT block on operator-decision; if
  blocked, ping + move to the next item.

Begin with STEP 0. Work autonomously to completion across both plans.
