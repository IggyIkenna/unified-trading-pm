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
status: resolved
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/archive/2026_08/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md,
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
effort: high
drift_direction: none
context_scope:
  [
    /plans/archive/2026_08/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_lighter.py,
  ]
---

> **🗄️ ARCHIVED 2026-08-12 (/plan-reconcile)** — both todos closed (reconcile + archive). Source doc
> `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md` fully resolved and archived alongside this plan in
> the same pass.

# cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12 — finalize

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile — DONE 2026-08-09 (slot 28, review craft).** The source doc's sole `[VERIFY]` P1 item
      was already `[x]` (closed 2026-08-08 by worker slot-12) — independently re-verified its manifest evidence rather
      than trusting the doc's own copy: fresh `read_availability_index_safe` read against
      `market-data-tick-cefi-prd-central-element-323112` (`venue=LIGHTER-ZKSYNC, data_type=derivative_ticker`) shows
      **16,491 `capture_status=captured` rows, 2026-04-17..2026-08-02, 100%
      `source=tardis`/`pipeline_mode=batch_tardis`** (doc cited 16,484 — the +7 delta is normal ongoing consolidation,
      not a discrepancy). Re-ran `measure_honest_coverage.py --asset-group cefi` (`run-bounded-analysis.sh`, RSS-poll
      cap): Layer-1 shows `matched=68/73`, **5 missing tuples = BITGET-FUTURES/OKX-FUTURES only — LIGHTER-ZKSYNC
      confirmed NOT among them**, matching the source doc's claim exactly. Fixed the stale
      `cefi_consolidated_closeout_2026_07_18.md` line-334 citation (was still "BLOCKED-CREDENTIALS, scaffold correct")
      to reflect the resolved entitlement + verified re-launch. No code change needed — this was a verification-only
      reconcile, the source doc's checkbox was already correctly `[x]`. (repo: unified-trading-pm)
- [x] ✅ [DOC] P2. **Archive.** Run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md` once todo 1 confirms it is fully closed — dated
      archive folder, exact-successor banner, corpus-wide referrer fixup (this finalize doc,
      `cefi_consolidated_closeout_2026_07_18.md`, and any other citer named in the source doc's own `related:`). Then
      archive this finalize plan itself in the same pass. **Done when**: the source doc and this finalize plan are both
      under `plans/archive/`, and `check_reference_paths.py` shows zero new broken referrers. **DONE 2026-08-12
      (/plan-reconcile)**: source doc banner added + `status: resolved` + `git mv` to
      `plans/archive/2026_08/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`; this finalize plan
      banner added + `git mv` to `plans/archive/2026_08/`. Live-corpus referrer repoint (excluding already-archived docs
      and other agents' isolated `.claude/worktrees/*` checkouts, out of scope):
      `cefi_consolidated_closeout_2026_07_18.md`, `ag_closeout_audit_rollout_2026_07_25.md`, `plans/active/INDEX.md`,
      `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`, `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`,
      `plans/epics/cefi_master.md` — see each doc's own edit for the repointed path.

## Progress Log

- **2026-08-08**: authored alongside the source doc's `assigned_vm: NA -> planning` reclassification
  (na-eligibility-audit round7 RECLASSIFY sweep, cefi tranche, batch 2 of 3).
- **2026-08-09 (slot 28, review craft, task
  `cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize-515548833c3b`)**: Todo 1 done — independently
  re-verified the source doc's already-`[x]` VERIFY evidence (fresh manifest read + Layer-1 re-run, both confirm) and
  fixed the stale `cefi_consolidated_closeout_2026_07_18.md` citation. See todo 1 for full detail. Todo 2 (archive) is
  next — out of scope for this dispatch, left for a follow-up `[DOC]`-tagged task.
