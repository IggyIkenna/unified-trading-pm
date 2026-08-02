---
doc_type: issue
title: Corpus-wide sweep of plans/active/issues/ for status:open docs with zero checkboxes (prose-only deferrals)
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §7 sampled 10 issue docs referenced by the 5 asset-group
  consolidated closeouts — 8/10 passed (had real bounded todos), 2/10 failed (prose-only "suggested next steps" with no
  real `- [ ]` checkbox). One of the two, `plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`, is
  now fixed (a real todo added). The second named FAIL,
  `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`, now also fixed (4 real todos added). The full corpus
  beyond the original 10-doc sample still needs a sweep.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-quality, issue-docs, todo-format, hygiene-sweep]
related:
  [
    /plans/archive/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md,
    /plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md,
    /plans/active/task_template.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "unified-trading-pm (this session) — full-corpus sweep complete, zero genuine prose-only-deferral gaps found beyond
  the 2 already fixed by todos 1-2"
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §7
depends_on: []
---

> **🟢 ARCHIVED 2026-07-30** — status=resolved, all 3 todos done, no lock, archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule. Todos 1-2 fixed the 2 real gaps the
> original 10-doc sample found; todo 3 swept the full remaining corpus (96 `status: open` docs referenced by the 5
> asset-group consolidated closeouts) and found zero further gaps.

# Zero-checkbox issue-doc sweep

## Todos

- [x] 1. [DOCS] P2. ✅ **DONE 2026-07-24** — `plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`
      converted its prose-only "Suggested fix direction" into a real bounded `- [ ] [CODE] P2.` todo with a stated
      definition-of-done.
- [x] 2. [DOCS] P2. ✅ **DONE 2026-07-24** — `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`'s
      prose-only "Suggested next steps" converted into 4 real bounded todos, splitting the undecided "Decide
      fold-vs-migrate" judgment call into a fact-gathering todo + a separate `[OPERATOR]`-tagged decision todo per
      task_template.md's bounded-outcome rule.
- [x] 3. [DOCS] P2. ✅ **DONE 2026-07-30 (slot 7) — full corpus swept, zero genuine gaps found.** Extracted every
      `plans/active/issues/*.md` reference (full-path links + bare-filename mentions, cross-matched against the real
      directory listing) from all 5 asset-group consolidated closeouts
      (`cefi`/`defi`/`tradfi_consolidated_closeout_2026_07_18.md`, `sports_consolidated_closeout_2026_07_19.md`,
      `prediction_consolidated_closeout_2026_07_18.md`) PLUS the one satellite discoverability doc that exists
      (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` — no defi/tradfi/sports/prediction equivalent
      exists, confirmed via `find`) — **110 distinct referenced issue-doc filenames**. 13 have since archived
      (`status: resolved`, correctly out of scope); 1 has no status frontmatter
      (`_cefi_canonical_blueprint_2026_07_17.md`, a supplementary blueprint, not a tracked issue); **96 are
      `status: open`**. Grepped all 96 for real checkbox syntax (`- [ ]`/`- [x]`, anchored AND unanchored patterns, to
      catch nonstandard indentation/casing) — **95/96 have at least one real checkbox somewhere in the body**. The one
      zero-checkbox hit, `plans/archive/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`, uses a numbered
      `~~item~~ **DONE**` remediation-list format instead of checkbox syntax — read it directly: all 3 items are
      genuinely done (commit hashes cited, `resolved_by` frontmatter filled), it stays `status: open` only because
      `locked_by: live-defi-rollout` blocks archival (an unrelated, out-of-scope lock — not this todo's to touch; the
      tradfi closeout doc itself already correctly characterizes it as "0 open todos"). **No prose-only "remaining work"
      gap exists anywhere in the referenced corpus** — todos 1-2's two fixes were the only real gaps this sweep family
      was ever going to find. Every todo in this issue doc is now done, no lock — archived per `issue-doc-lifecycle.md`
      case 2/3 (the audit's own findings are fully resolved: 2 real fixes shipped, the remaining scope swept clean). 4
      corpus referrers fixed to the archived path (see commit).
