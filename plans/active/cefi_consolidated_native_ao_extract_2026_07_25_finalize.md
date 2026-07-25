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
status: draft
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
last_updated: "2026-07-25"
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
---

# CeFi native AO extract — finalize

> **Machine-gated on `cefi_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 12 tasks in that plan are `done`. `sequential: true` because
> todo 2 (stale-checkbox flips) should follow todo 1 (fresh-work checkbox flips) to avoid two concurrent workers editing
> `cefi_consolidated_closeout_2026_07_18.md` at once, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P2. **Reconcile the 12 freshly-shipped todos' checkboxes in `cefi_consolidated_closeout_2026_07_18.md`.**
      For each of `cefi_consolidated_native_ao_extract_2026_07_25.md`'s 12 now-done todos, flip the corresponding
      checkbox/section in the parent doc (each drafted todo's text cites its parent-doc Track/section as "Source"),
      citing the extraction plan's shipped commit(s) — verify each cited commit actually exists before citing it. Repo:
      unified-trading-pm. **Done when**: all 12 corresponding checkboxes/sections in
      `cefi_consolidated_closeout_2026_07_18.md` are flipped with verified evidence.
- [ ] [REVIEW] P1. **Flip the 5 stale-checkbox findings in `cefi_consolidated_closeout_2026_07_18.md`, each with a fresh
      re-verification (do not trust the extraction plan's citations blindly — re-confirm against live state, since time
      has passed since the triage):** (1) the "Open todos surfaced in the execution log" carryover section — the
      KRAKEN-SPOT `_PATH_RE` item (re-confirm KRAKEN-SPOT Surface A is still clean, no regression since), the
      658-ambiguous-wire-key item (re-confirm the 213/216-fixed + 3-permanent terminal state still holds), and the
      ≈5,413 catalogue-gap item (flip the "enumerate" half as done, leave the OKX-SPOT/COINBASE-SPOT fix half open, note
      the BITGET-FUTURES fix half's disposition per todo 1 above); (2) the DERIBIT combo mispartition todo's part (a)
      writer-fix half (re-confirm `mtds@2ddc6d4a` is still on `live-defi-rollout`, part (b) stays open); (3) the
      `_DRYRUN_COLS` P0 — re-confirm todo 1's grep-check result is accurate against current HEAD, not stale by the time
      this finalize runs. Repo: unified-trading-pm. **Done when**: all 5 items have an updated, freshly-re-verified
      status in `cefi_consolidated_closeout_2026_07_18.md` (checkbox flipped where genuinely resolved, left open with an
      accurate current-state note where not).
- [ ] [DOC] P3. **Archive `cefi_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked (all 20 human-only classifications
      were already either cited as staying in the parent doc, or resolved by todo 2 above) → add the archive banner →
      run the codex-alignment check → grep the corpus for every referrer of
      `cefi_consolidated_native_ao_extract_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
