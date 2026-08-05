---
doc_type: plan
title: CeFi native AO extract — finalize (reconcile parent checkboxes, incl. stale-checkbox flips + archive)
summary: >-
  Gated closeout for cefi_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 12 of that plan's todos are done. Mirrors the batch1_finalize pattern, plus one extra: because the
  extraction plan's own todos ALL trace back to cefi_consolidated_closeout_2026_07_18.md itself (not other satellite
  docs), this finalize plan is also the vehicle for flipping that parent doc's 5 already-stale checkboxes identified
  during the triage (KRAKEN-SPOT Script-2 item, the 658-wire-key item, the catalogue-gap enumeration item, the DERIBIT
  combo writer-fix half, and re-verifying the _DRYRUN_COLS P0) — deliberately deferred from the extraction plan itself
  so the parent doc's edit surface is touched once, coherently.
status: complete
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, native-extraction, archival, stale-checkbox-reconciliation]
related:
  [
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  Per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan. Precedent: cefi_satellite_ao_dispatch_batch1_2026_07_25.md /
  cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# CeFi native AO extract — finalize

> **🟢 ARCHIVED 2026-08-05.** All 3 todos resolved: the 12 fresh-work checkboxes reconciled (todo 1), the 5
> stale-checkbox findings flipped with fresh re-verification (todo 2), and the parent plan archived via the standard
> 6-step ritual (todo 3). Moved to `/plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25_finalize.md`;
> corpus referrers updated. The companion `cefi_consolidated_native_ao_extract_2026_07_25.md` is co-archived in the same
> commit.
>
> **Machine-gated on `cefi_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 12 tasks in that plan are `done`. `sequential: true` because
> todo 2 (stale-checkbox flips) should follow todo 1 (fresh-work checkbox flips) to avoid two concurrent workers editing
> `cefi_consolidated_closeout_2026_07_18.md` at once, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile the 12 freshly-shipped todos' checkboxes in
      `cefi_consolidated_closeout_2026_07_18.md`.** DONE 2026-08-05 — all 12 checkboxes/sections reconciled
      (`unified-trading-pm@1ea317100`): candidates 1-9 updated in parent doc from "Dispatched"/"candidate N" to ✅ DONE
      with evidence; candidate 10 (LIGHTER-ZKSYNC) MVP table row + execution-log items 6/6 updated; candidate 11
      (BITGET-FUTURES) execution-log item 5 updated; candidate 12 (_DRYRUN_COLS) execution-log "Recommended next"
      updated. All cited commits verified extant before citing. Repo: unified-trading-pm.
- [x] ✅ [REVIEW] P1. **Flip the 5 stale-checkbox findings in `cefi_consolidated_closeout_2026_07_18.md`, each with a
      fresh re-verification (do not trust the extraction plan's citations blindly — re-confirm against live state, since
      time has passed since the triage):** DONE 2026-08-05 (`unified-trading-pm@<sha>`): (1) KRAKEN-SPOT `_PATH_RE` —
      re-verified Surface A still clean, 155,872 objects auto-renamed, execution-log checkbox stays `[x]`; 658 wire keys
      — re-verified 213/216 shipped + 3 permanent terminal state holds, execution-log checkbox stays `[x]`; ≈5,413
      catalogue-gap — flipped enumeration half to `[x]` (`instruments-service@f6f16785` shipped, 211 gap rows measured),
      OKX-SPOT/COINBASE-SPOT fix half stays open (needs operator decision), BITGET-FUTURES fix half already closed via
      todo 1 (candidate 11); (2) DERIBIT combo mispartition part (a) — `mtds@2ddc6d4a` confirmed ancestor of
      `origin/live-defi-rollout`, flipped to `[x]`, part (b) stays operator-owned; (3) `_DRYRUN_COLS` P0 — `"chain"`
      confirmed in `_DRYRUN_COLS` at
      `instruments-service/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py:220`, `1284606a` on LDR, fix
      predates triage. Repo: unified-trading-pm.
- [x] ✅ [DOC] P3. **Archive `cefi_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked (all 20 human-only classifications
      were already either cited as staying in the parent doc, or resolved by todo 2 above) → add the archive banner →
      run the codex-alignment check → grep the corpus for every referrer of
      `cefi_consolidated_native_ao_extract_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) unchanged — `_finalize` gate doc, no source-code
  paths added per the skip-source carve-out; all 5 entries confirmed resolving on disk.
