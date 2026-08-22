---
doc_type: issue
title: >-
  defi_cefi_venue_chain_axis_contamination_2026_07_28.md is over the 1000-line hard cap AND prettier-dirty, blocking
  routine Progress Log appends (marker-append carve-out unreachable)
summary: >-
  `plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md` is 1008 lines (over the 1000L hard cap
  enforced by `check_line_caps.sh` in the prek plan-hygiene gate) AND not prettier-clean (pinned prettier 3.9.5 wants to
  reformat 121 lines across the line-25 frontmatter `repos:` list + the line-245-298 ADDITIVE-FALLBACK prose block).
  Discovered 2026-08-10 (slot-6) while trying to land a routine gate-assessment Progress Log append: the
  small-marker-append carve-out (ADDED<=10, DELETED=0 on an already-over-cap doc) is UNREACHABLE for this doc because
  the pre-commit prettier-autostage hook always re-stages a ~121-line reformat of pre-existing content, blowing ADDED
  past 10 on every staged diff. Same root-cause CLASS as
  `tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` (that doc's closeout is 1005L and
  blocks a same-line table-cell substitution); this doc adds the prettier-churn dimension on top of the pure over-cap
  one.
status: open
nature: issue
asset_group: [defi, cefi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, prettier, tooling-gap, defi]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md,
    /plans/archive/2026_08/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md,
  ]
created: "2026-08-10"
author: slot-6
last_updated: "2026-08-10"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
source: >-
  Discovered live 2026-08-10 (slot-6) while landing a routine gate-assessment Progress Log append on
  defi_cefi_venue_chain_axis_contamination_2026_07_28.md — safe-doc-push.sh's prek plan-hygiene gate refused (HARD
  line-cap, 1008L at HEAD), and direct measurements (npx prettier@3.9.5 --check/--write on the HEAD file) showed the
  marker-append carve-out unreachable due to 121 lines of pre-existing prettier churn.
context_scope:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/archive/2026_08/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md,
    unified-trading-pm/scripts/plan-hygiene/check_line_caps.sh,
    unified-trading-pm/scripts/hooks/prettier-autostage.sh,
  ]
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: fix
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — both todos done 2026-08-10 (line-cap+prettier fix shipped,
> `unified-trading-pm@74366a0e00`); the `archive_exempt: true` bridge asked for a human-reviewed follow-on
> archival pass rather than immediate auto-archive — this dispatch is that pass. Kept as a historical record.
# defi_cefi_venue_chain_axis_contamination doc is over-cap + prettier-dirty — routine edits blocked

## What I found

While attempting to append a routine gate-assessment Progress Log entry (2026-08-10, slot-6) to
`plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md`, `safe-doc-push.sh`'s prek plan-hygiene
gate refused with:

```
❌ check_line_caps: 1 staged plan(s)/epic(s) over cap — split before committing
  HARD  defi_cefi_venue_chain_axis_contamination_2026_07_28.md  1030L  todos=13
```

Two compounding pre-existing blockers, both verified empirically this session:

1. **Over the 1000-line hard cap**: the doc is 1008 lines at HEAD (the slot-8 2026-08-10 corpus-recompute flip was the
   last commit). Any staged touch to an already-over-cap file trips the gate. The `check_line_caps.sh` SCOPED-mode
   small-marker-append carve-out (operator ruling 2026-08-02) exists to let a bounded non-checkbox append through — but
   its conditions (ADDED<=10, DELETED=0) are only reachable if the staged diff is a PURE append.

2. **Not prettier-clean — the carve-out is UNREACHABLE**: pinned prettier 3.9.5 (`prettier-autostage.sh`) wants to
   reformat **121 lines** of pre-existing committed content: (a) the frontmatter `repos:` YAML list (line 25,
   single-line → multi-line), and (b) the `session continuation 2026-08-04` ADDITIVE-FALLBACK prose block (lines
   245-298, deep leading-whitespace padding). The pre-commit `prettier-autostage` hook runs `prettier --write` on every
   staged markdown file and re-stages the result — so ANY commit touching this doc first re-stages ~121 lines of churn,
   making the staged diff's ADDED ~131 (my 10-line entry + the reformat), blowing the ADDED<=10 carve-out condition
   every time. A pure 10/0 append at staging time becomes ~131/121 after prettier re-stages, before plan-hygiene runs.
   Measured directly: `npx -y prettier@3.9.5 --write` on the HEAD file changes exactly line 25 + lines 245-298 (`diff` =
   121 changed lines).

Same root-cause class as the tradfi closeout blocker, with the prettier-churn dimension added. The shared
`check_line_caps.sh` net-zero-length-content-substitution consideration in
`plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` would NOT help here (my append genuinely grows
the file by 10 lines, and the prettier churn is not a content substitution).

## Why it matters

This doc is the SSOT for a live, operator-ruled P1 data-correctness effort (DeFi/CeFi venue+chain axis contamination).
It must keep receiving Progress Log entries from every worker that touches the gated P1 todo (corpus freshness → GCS
duplicate cleanup) — but it currently CANNOT accept ANY routine append, so gate assessments, hold notes, and evidence
are forced into sibling docs (or lost). The doc also cannot be archived (P1 todo still `- [ ]`, gated). The 2026-08-10
gate-assessment evidence from slot-6 is recorded in this doc's Progress Log below rather than the contamination doc
(which is blocked).

## Recommended decision

- [x] ✅ [DOCS] P2. **Bring `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` under the 1000L hard cap AND
      prettier-clean it in one commit** — done 2026-08-10 (slot-9, `unified-trading-pm@74366a0e00`). Moved Progress Log
      entries (2026-07-30 through 2026-08-10, 56 entries, 407 lines) + the ADDITIVE-FALLBACK investigation block
      verbatim to `plans/archive/2026_08/defi_cefi_venue_chain_axis_contamination_history_2026_07_28.md` (507L,
      prettier-clean). Parent now 553L (was 1008L), `prettier --check` clean, `check_line_caps.sh` SOFT only. All
      `- [ ]`/`- [x]` todos preserved in parent; only history/prose moved.
- [x] ✅ [DATA] P1. **2026-08-10 gate re-check on the contamination P1 operator-ruling todo — recorded here because the
      contamination doc is blocked.** (1) Step-1 gate NOT MET:
      `probe_cefi_perp_funding_raw_coverage.py --start 2026-08-06 --end 2026-08-10` (fresh, list-only) = **0 objects for
      all 6 CARRY_BASIS_PERP venues on every forward day**; the single Tardis slot is still held by
      `cefi-queue-heavy-binancefutu-x17-20260809-083733` (RUNNING), so the forward-gap backfill `- [ ] [INFRA] P1` in
      `/plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` remains blocked →
      `CanonicalPerpFundingProvider.funding_window()` for CURRENT days would return empty (corpus = slot-8's partial
      15/82 days). (2) Step-2 manifest fix CONFIRMED HELD: bounded column-projected + filtered `read_availability_index`
      on `market-data-tick-defi-prd-central-element-323112` = **0 `chain=='FUTURES'` rows** (slot-9's 42-row drop +
      splitter/heal fixes holding). (3) Step-3 physical GCS duplicate cleanup GATED on step 1 — no delete attempted. (4)
      Step-4 HYPERLIQUID resolved (no-touch, archived `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`). Checkbox
      NOT flipped — correctly gated on forward-gap backfill landing + corpus recompute + funding_window() re-verified
      for CURRENT days, THEN a fresh 5-part proof before step-3 delete.

## Progress Log

- **slot-6 2026-08-10 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-783eda8294a7`)**: Filed this doc
  after `safe-doc-push.sh`'s prek plan-hygiene gate refused a routine Progress Log append to the contamination doc (HARD
  line-cap, 1008L at HEAD). Root-caused both compounding blockers (over-cap + prettier-dirty, 121-line churn making the
  marker-append carve-out unreachable) with direct measurements (`git show HEAD:... | wc -l` = 1008;
  `npx prettier@3.9.5 --check` warns; `--write` on a copy changes line 25 + 245-298). Recorded the contamination P1 gate
  re-check evidence here (see the `- [x]` above) since the SSOT doc cannot accept it. Contamination doc's P1 checkbox
  stays `- [ ]`; the gated task was released with reason_code GATED pending the forward-gap backfill.
- **slot-9 2026-08-10 (data_engineering, task
  `defi_contamination_doc_over_cap_and_prettier_dirty_blocks_routine_edits-70fea8f1625b`)**: Flipped the P2 todo —
  line-cap + prettier fix shipped `unified-trading-pm@74366a0e00`. Parent doc 1008L→553L, prettier-clean. Set
  `archive_exempt: true` on this doc: both todos now done, but the doc should be user-archived (not auto-archived by the
  next worker) so the operator can review the resolution before closing. The archive step (`git mv` + banner + referrer
  sweep) is trivial and deterministic — a P3 archive-candidates cleanup.
- **context-scout 2026-08-14**: populated context_scope (4 entries).
