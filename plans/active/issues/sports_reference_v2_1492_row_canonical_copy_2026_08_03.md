---
doc_type: issue
title: Copy 1,492 pre-floor-only sports_reference_v2/by_date/ rows to canonical storage before the by_date cull
summary: >-
  Operator ruling (plan_reconcile_parked_operator_decisions_2026_08_02.md § 1b, option B, confirmed 2026-08-03 over a
  conflicting concurrent-session ruling of option A): before the two sports_reference_v2/by_date/ delete todos can
  revert to self-justified, the 1,492 rows sports_satellite_ao_dispatch_batch5_2026_07_26.md proved are the SOLE
  surviving copy of real pre-floor data (no canonical twin) must be copied to canonical storage.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [sports, delete-safety, canonical-copy, data-migration]
related:
  [
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Operator ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md § 1b, option B, 2026-08-03."
---

# Copy the 1,492 sole-surviving-copy sports_reference_v2/by_date/ rows to canonical storage

## Why this doc exists

`sports_satellite_ao_dispatch_batch5_2026_07_26.md:184-217` proved 1,492 rows under `sports_reference_v2/by_date/` are
the SOLE surviving copy of real pre-floor data with no canonical twin. The two open `sports_reference_v2/by_date/` cull
todos in `sports_consolidated_closeout_2026_07_19.md:552-553` and
`sports_consolidated_native_ao_extract_2026_07_25.md:204-210` are currently `[OPERATOR]`-gated + delete-safety §3a-cited
pending exactly this migration.

## Todos

- [ ] [DATA] P1. Identify the exact 1,492 rows (re-run the census from
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md` to confirm the count is still current — the corpus has moved
      since 2026-07-26).
- [ ] [DATA] P1. Copy the confirmed rows to canonical storage (the same target path/schema the rest of the sports corpus
      already uses), verified row-count-conservation + content-identical.
- [ ] [VERIFY] P1. Re-run the canonical-twin check against the copied rows — confirm 100% now have a canonical twin.
- [ ] [OPERATOR] P2. Once verified, retag the two `sports_reference_v2/by_date/` cull todos back to self-justified (drop
      the `[OPERATOR]` + delete-safety §3a citation added 2026-08-02) — this is the reversion B's ruling specified, not
      an independent decision.

## Progress Log

- **2026-08-03** — Filed per operator ruling resolving the § 1b A-vs-B conflict in favor of B.
