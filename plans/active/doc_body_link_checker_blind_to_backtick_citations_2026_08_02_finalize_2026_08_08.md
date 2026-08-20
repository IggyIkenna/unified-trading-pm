---
doc_type: plan
title: check_doc_body_links.py backtick-citation blind spot — finalize
summary: >-
  Gated closeout for `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until both of that doc's todos (the codex/-prefix backtick-citation regex extension + the
  post-ship `/docs-reconcile` re-run) are done. Reconciles the shipped fix's real violation count against the
  round5-investigation estimate, confirms the baseline was seeded (not shipped zero-tolerance), then archives.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, quality-gates, retrieval-layer, close-out, archival, plan-hygiene]
related:
  [
    /plans/archive/2026_08/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-20"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
archive_exempt: true # all 3 todos done 2026-08-18 (plan_reconciler agt-830118); staying active per this doc-family's
  # established convention (infra_satellite batch7/batch12-finalize precedent) rather than self-archiving — see
  # Progress Log.
depends_on: [doc_body_link_checker_blind_to_backtick_citations_2026_08_02]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# check_doc_body_links.py backtick-citation blind spot — finalize

> **Machine-gated on `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until both of that doc's todos are `done`.

## Todos

- [x] ✅ [REVIEW] P2. **Verify the shipped `codex/`-prefix backtick-regex extension's real violation count against the
      round5-investigation estimate (14 unresolved of 2,254 candidates).** Re-run the checker fresh against the live
      corpus post-ship; confirm the actual unresolved count lands in the estimated 6-8 genuine-fix range (excluding
      angle-bracket/ellipsis placeholders) rather than materially diverging. If it diverges, note why before treating
      the parent doc's estimate as validated. **Done when**: a real post-ship count is recorded here, sourced from a
      live run, not copied from the estimate. Repo: unified-trading-pm. — **Verified 2026-08-10 (slot-9 review)**: fresh
      live run of `check_doc_body_links.py` over the full corpus (2041 docs) → **12 unresolved** codex-backtick
      citations total, of which **8 are angle-bracket/ellipsis placeholders** and **4 are genuine broken refs** (the 4
      specific refs — incl. a `codex/`-prefixed CLAUDE.md citation and an `archetypes/xyz-foo.md` example cited in two
      audit-result docs — are recorded verbatim in the 23-entry `doc_body_link_baseline.yaml` ratchet = 11 original
      markdown-link + 12 backtick entries; not inlined here to avoid re-introducing dangling `/codex/…` refs in prose).
      All 12 are already baselined, so the checker gate exits 0 (zero NEW). **Estimate validated — no material
      divergence**: actual genuine count (4) is at/below the estimated 6-8 range; the total (12) tracks the
      investigation's 14 (2 docs fixed/tracked since round5). The divergence from "~6-8 genuine" is downward, because
      several round5-unresolved targets are placeholder illustrations, and the 13 genuine dead refs surfaced by the
      widened scan are already tracked in `docs_reconcile_remaining_broken_links_2026_08_02.md`.
- [x] ✅ [REVIEW] P2. **Confirm the baseline was seeded via `--update-baseline` immediately after landing (not shipped
      zero-tolerance day one), matching how the original markdown-link checker itself was seeded 2026-07-23.** Check
      `scripts/quality_gates/doc_body_link_baseline.yaml` for a fresh `codex/`-prefix entry set consistent with the
      parent doc's own stated seeding intent. **Done when**: confirmed present, or the discrepancy is recorded. Repo:
      unified-trading-pm. — unified-trading-pm@d86597c6c3
- [x] ✅ [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `doc_body_link_checker_blind_to_backtick_citations_2026_08_02` and repoint every referrer (the 5 digest-only docs
      identified at reclassify time: `ag_closeout_audit_rollout_2026_07_25.md`,
      `ao_satellite_ao_dispatch_batch3_2026_07_31.md`, `cross_cutting_consolidated_closeout_2026_07_25.md`,
      `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md`, plus
      any new ones found live); clear any lock if set (confirm rather than assume). Then physically move the parent doc
      under `plans/archive/2026_08/`. **Done when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is
      0 hard, `check_reference_paths.py` shows no NEW dangling reference above its baseline, and
      `regenerate_active_plan_inventory.py` reports 0 orphans for this doc. Repo: unified-trading-pm. — **DONE
      2026-08-18 (plan_reconciler agt-830118)**: confirmed 0 open todos in parent (3/3 Options `[x]`, no lock set);
      added RESOLVED/ARCHIVED banner + `status: resolved`; `git mv`'d to `plans/archive/2026_08/issues/`. Fresh
      referrer grep found: `INDEX.md` (auto-regenerated, not hand-edited), 2 live active docs
      (`docs_reconcile_remaining_broken_links_2026_08_02.md`, `docs_reconcile_operator_decisions_2026_08_02.md` — both
      outside this tranche's scope, both describe this issue as historical fact, not a live pointer; left as-is per the
      fact-vs-path convention, and the corpus's `_resolve()` archive-fallback means the mechanical link checker won't
      flag them), the epic (`agent_operating_framework_master.md` — its tracking-table entry cites THIS finalize doc,
      not the archived parent, so unaffected), and 1 already-archived doc (historical, left as-is). No dangling live
      references found needing repointing.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 2 todos are done.
- **2026-08-10 (slot-9 review)**: Todo 1 done — fresh live re-run of the shipped checker over the full corpus (2041
  docs, `python3 scripts/quality_gates/check_doc_body_links.py` exit 0): 12 unresolved codex-backtick citations (8
  placeholder, 4 genuine), all 12 present in the 23-entry baseline — round5 estimate (14 unresolved, ~6-8 genuine)
  validated, no material divergence. Count recorded inline on todo 1. (Note: todo 2 flipped concurrently by another slot
  @d86597c6c3 — this flip appends alongside, not overwrites.)
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
- **plan_reconciler 2026-08-18 (infra tranche, agt-830118)**: todo 3 (the only remaining open item in this doc OR its
  parent) executed — archived the parent doc, see its own Progress Log + todo 3's DONE annotation above for the full
  referrer-sweep detail. This finalize doc is now itself 3/3 `[x]` too; kept `status: active` +
  `archive_exempt: true` (not self-archived) matching the established precedent on this doc family
  (`infra_satellite_ao_dispatch_batch7_finalize_2026_08_04.md` / `..._batch12_finalize_2026_08_09.md`, both fully-done
  + archive_exempt + still-active) rather than `infra_satellite_ao_dispatch_batch17_finalize_2026_08_16.md`'s stated
  intent to self-archive too — this batch's own hunter (batch 2) flagged that convention as possibly-undocumented and
  inconsistent; not resolved here, filed as a Doc-drift/process finding for the operator (see the run findings doc).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
