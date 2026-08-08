---
doc_type: plan
title: >-
  cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md — machine-held via depends_on +
  gate_on_depends: true until the source doc's sole remaining item (the LIGHTER-ZKSYNC derivative_ticker re-launch
  VERIFY, now unblocked by the 2026-08-08 Tardis entitlement re-probe) is done. Reconciles the source doc's own checkbox
  once shipped (citing the manifest evidence), then archives it via the standard 6-step ritual once fully closed.
  Authored 2026-08-08 as part of the na-eligibility-audit round7 RECLASSIFY sweep, per task_template.md's
  finalize-plan-coverage rule (every assigned_vm:planning doc needs a companion gated finalize plan).
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12]
gate_on_depends: true
source: >-
  na-eligibility-audit round7 RECLASSIFY sweep, cefi tranche, batch 2 of 3 (2026-08-08) —
  issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md was reclassified assigned_vm:NA -> planning after the
  Tardis LIGHTER-ZKSYNC entitlement gap that previously blocked it was resolved and re-probed live the same day (see
  that doc's "na-corpus-digest-closeout 2026-08-08 (item 31)" Progress Log entry), leaving only a bounded [VERIFY]
  re-launch item; conflict-checked clean against currently-active AO plans. This finalize doc closes the
  finalize-plan-coverage gate the reclassification itself triggered.
assigned_role: data_engineering
drift_direction: none
context_scope:
  [
    /plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_lighter.py,
  ]
---

# cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12 — finalize

## Todos

- [ ] [REVIEW] P2. **Reconcile.** Once the source doc's sole open `[VERIFY]` P1 item lands — re-launch LIGHTER-ZKSYNC
      `derivative_ticker` via `VENUES="LIGHTER-ZKSYNC" bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`
      (rebuild the code tarball first per the stale-tarball gotcha the doc's own prior sessions hit repeatedly), confirm
      real rows landed across a full multi-day range (not just the single spot-checked days from the 2026-08-08
      entitlement re-probe), and re-run `measure_honest_coverage.py` Layer-1 for LIGHTER-ZKSYNC to confirm
      `present_tuples` moves off 0 — re-verify the cited commit/manifest evidence actually exists (do not trust the
      source doc's own copy of the evidence line), flip the checkbox if not already `[x]`. Also fix the now-stale
      `cefi_consolidated_closeout_2026_07_18.md` line-329 citation ("lighter Tardis entitlement (BLOCKED-CREDENTIALS,
      scaffold correct)") to reflect the resolved entitlement + completed re-launch. **Done when**: the source doc's
      `[VERIFY]` item is `[x]` with fresh manifest evidence, and the consolidated-closeout citation is updated.
- [ ] [DOC] P2. **Archive.** Run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md` once todo 1 confirms it is fully closed — dated
      archive folder, exact-successor banner, corpus-wide referrer fixup (this finalize doc,
      `cefi_consolidated_closeout_2026_07_18.md`, and any other citer named in the source doc's own `related:`). Then
      archive this finalize plan itself in the same pass. **Done when**: the source doc and this finalize plan are both
      under `plans/archive/`, and `check_reference_paths.py` shows zero new broken referrers.

## Progress Log

- **2026-08-08**: authored alongside the source doc's `assigned_vm: NA -> planning` reclassification
  (na-eligibility-audit round7 RECLASSIFY sweep, cefi tranche, batch 2 of 3).
