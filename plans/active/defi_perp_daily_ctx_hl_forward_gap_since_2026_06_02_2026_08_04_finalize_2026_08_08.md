---
doc_type: plan
title: Finalize — HYPERLIQUID perp_daily_ctx forward-write gap close-out
summary: >-
  Gated finalize companion for issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md (reclassified
  NA→planning, na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08) — re-verifies the forward-write build's
  evidence (the new HL `/info` mark-price fetch, the CeFi partition-path write, the manifest registration, and the
  follow-up CeFi Tardis writer diagnostic), then archives both docs per plan-completion-and-archival-discipline once
  every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, perp-daily-ctx, hyperliquid, finalize, archival, ao-build]
related:
  [
    /plans/active/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md,
    /plans/archive/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: [defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep) — every AO-dispatched plan/reclassified issue doc needs a
  gated finalize companion (/plans/active/task_template.md §4).
context_scope:
  [
    /plans/active/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_hyperliquid.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
  ]
---

# Finalize — HYPERLIQUID perp_daily_ctx forward-write gap close-out

Machine-held (`gate_on_depends: true`) until every todo in
`issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` is done. Do not start manually before then.

## Todos

- [ ] [REVIEW] P2. Re-verify the build's evidence: (1) the `[CODE] P2` todo's cited commit shipping the new HL `/info`
      mark-price/volume/OI fetch in `_perp_funding_hyperliquid.py`, wired into `_collect_hyperliquid()`'s existing
      per-coin loop — confirm via `git log`/`git show` against a fresh `git pull --ff-only origin live-defi-rollout` on
      `market-tick-data-service` (don't trust the build todo's own evidence line uncritically); (2) confirm the write
      path used the CeFi partition shape (`build_cefi_partition_path`, `get_write_bucket_name("market_data", "cefi")`,
      `DefiManifestRecorder(asset_group="cefi")`) and NOT the old dead-bucket convention; (3) confirm a live/backfill
      run produced real `perp_daily_ctx` manifest rows for HYPERLIQUID on a fresh date (a bounded manifest read,
      `venue=HYPERLIQUID, data_type=perp_daily_ctx`, date > 2026-06-01 — no whole-corpus walk) and that existing
      `perp_funding` tests stayed green; (4) confirm the `[DIAG] P3` follow-up (CeFi Tardis `perp_funding_corpus.py`
      writer re-check) was actually run and its finding recorded, not left as an open question. Done-when: all 4 points
      independently re-verified with cited evidence; any mis-citation found is corrected in the source doc directly.
- [ ] [DOC] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` and this finalize doc itself: archive
      both to `plans/archive/2026_08/issues/` (or `plans/archive/2026_08/` for this finalize doc, matching this corpus's
      existing split convention), and fix every corpus referrer path (grep the repo for the old paths —
      `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` and `defi_satellite_ao_dispatch_batch6_2026_07_30.md`
      both cite the source doc — and update each hit). Done-when: `regenerate_active_plan_inventory.py` shows zero
      orphan referrers to the archived paths.

## Progress Log

- **2026-08-08 (na-eligibility-audit round7 RECLASSIFY sweep)**: finalize plan authored alongside the RECLASSIFY flip of
  the source issue doc, per `task_template.md`'s finalize-plan-coverage rule.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (4 entries).
