---
doc_type: plan
title:
  Infra satellite AO batch 6 — 2 conflict-clear extractions from newly-surfaced ex-meta tranche members (bare-name
  doctrine wording fix + hardlink-dedup investigation)
summary: >-
  Sixth AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-02). Batch3's 2026-07-30 audit had concluded the tranche reached its stop-iterating condition (every remaining
  orphan purely non-batchable); this run's membership sweep grew 39→43 mid-run when a same-day corpus-wide `asset_group:
  meta`→real-tranche retag sweep (`unified-trading-pm@0409fa053` region) landed 4 new members that had never been
  evaluated by any infra covering doc. All 4 were read end-to-end: 2 carry conflict-clear, bounded, worker-determinable
  work (both partial carve-outs — each source doc keeps its own operator/judgment-gated remainder at `assigned_vm: NA`),
  and 2 are fully non-batchable (both already carry an explicit `/na-eligibility-audit` KEEP-NA verdict from 2026-07-30
  on their own sole todo). Both extracted todos touch different files and were checked for file-level collision against
  all 11 existing infra batch/finalize/closeout plans plus a corpus-wide grep — zero found.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-6, plan-hygiene, meta-fold-in]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/active/issues/host_root_disk_full_transient_2026_07_13.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/ag_closeout_audit_infra_parked_2026_08_02.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/host_root_disk_full_transient_2026_07_13.md,
    scripts/quality-gates-base/base-service.sh,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-02 (ag_closeout_auditor scheduled worker, slot 11). Phase 0 re-derived the
  covering set (11 covering docs, 39→43 members after a mid-run corpus meta-retag sweep). Phase 1 classified all 4
  net-new members via direct full-text read; Phase 3 applied the dispatch-scope eligibility test + the HARD conflict
  check (grepped all 11 existing infra covering docs + a corpus-wide filename/keyword grep) before drafting anything
  here. See `issues/ag_closeout_audit_infra_parked_2026_08_02.md` finding 9 for the full per-doc classification.
---

# Infra satellite docs — AO dispatch batch 6

> **ARCHIVED 2026-08-09 (slot 14) — both todos `[x]`, finalize-pair ritual complete.** Both source-doc reconciliations
> (`issues/docs_reconcile_autonomous_sweep_2026_07_30.md`'s P2-E, `issues/host_root_disk_full_transient_2026_07_13.md`'s
> `[INFRA] P2`) were verified 2026-08-08 by the finalize plan; neither source doc archived (both keep other
> operator/judgment-gated remainder work). See
> `/plans/archive/2026_08/infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md` for the finalize-side record.

## Why this plan exists

A same-day corpus-wide "meta fold-in" sweep retagged 4 previously-`asset_group: [meta]` docs to their real tranches; 4
landed in `infra` (this run's `generate_ag_closeout_audit_candidates.py --tranche infra` count moved 39→43, never-cited
0→4 mid-run). None had ever been evaluated by any infra covering doc before this run. Reading all 4 in full:

- `issues/docs_reconcile_autonomous_sweep_2026_07_30.md` — a prior `/docs-reconcile` run's parking register. Most of its
  remaining content is operator-gated (a date-bound P0 decision, 2026-08-15) or human-judgment-gated (dead-doctrine- ref
  repoints, a bold-span fix that routes to `/plan-reconcile`). ONE item is conflict-clear and bounded: its own Todos
  section already carries `- [ ] [DOC] P2. Retire the 5 bare-name unified-trading-codex mentions (P2-E)` — its own body
  narrows this to exactly 2 genuinely-stale mentions (`.cursor/rules/ci-cd/act-secrets-setup.mdc:14`,
  `.cursor/rules/testing/test-coverage-targets.mdc:80`; a third is already correct, two more were fixed in-place by that
  same run).
- `issues/host_root_disk_full_transient_2026_07_13.md` — one open `[INFRA] P2` todo bundling an operator-permission-
  gated cron install (confirmed blocked: no crontab-write for this account on at least one fleet host) with two
  investigation sub-items that are NOT themselves permission-gated: root-causing why `UV_LINK_MODE=hardlink` isn't
  deduping `.venv` across the 16 slots, and (only if a fix is found) building a liveness-aware prune. Extracting the
  investigation half alone (never the cron install, never any prune-tool build/deploy) is conflict-clear and bounded.
- `issues/plan_reconcile_autonomous_sweep_2026_07_30.md` — its sole todo was already conflict-checked and deliberately
  held `assigned_vm: NA` by `/na-eligibility-audit` on 2026-07-30 (a genuine judgment call already made by that skill,
  not re-litigated here). NOT extracted.
- `issues/production_readiness_checklist_file_missing_2026_07_24.md` — its sole todo is explicitly and correctly
  human-judgment-gated (which of 5 disagreeing item-counts is authoritative has no mechanical answer);
  `/na-eligibility-audit` already confirmed KEEP-NA valid 2026-07-30. NOT extracted.

## Conflict check (before drafting)

Grepped all 11 existing infra covering docs (hub + batch1-5 + their finalize twins) and the whole active corpus for both
target file sets — zero hits outside the two source docs themselves:

- `.cursor/rules/ci-cd/act-secrets-setup.mdc` / `.cursor/rules/testing/test-coverage-targets.mdc` — mentioned only in
  `issues/docs_reconcile_autonomous_sweep_2026_07_30.md` corpus-wide.
- `UV_LINK_MODE` / hardlink-dedup / cross-slot `.venv` — mentioned only in
  `issues/host_root_disk_full_transient_2026_07_13.md` corpus-wide.

No competing claim on either file set. Both todos below touch entirely different files from each other — safe to run
concurrently (no `sequential: true`).

## Todos

- [x] ✅ [DOCS] P2. **Retire the 2 genuinely-stale bare-name `unified-trading-codex` mentions** in
      `.cursor/rules/ci-cd/act-secrets-setup.mdc:14` and `.cursor/rules/testing/test-coverage-targets.mdc:80` (per
      `issues/docs_reconcile_autonomous_sweep_2026_07_30.md`'s P2-E finding + its own `- [ ] [DOC] P2` todo) — replace
      the bare `unified-trading-codex` name with the current convention already used elsewhere in these same rule trees
      (pointing at PM's folded `codex/`, matching how `codex-maintenance.mdc`/`codex-no-absolute-paths.mdc` were already
      fixed in the same source sweep). Wording-only change, no functional rule-logic edit. Done when: neither file
      bare-names the archived repo, and
      `grep -rn "unified-trading-codex" .cursor/rules/ cursor-rules/ | grep -v "unified-trading-pm/codex"` returns no
      new bare-name hits beyond the already-known-correct `pipeline-mode-partition-structure.mdc:79` mention. (repo:
      unified-trading-pm) — **RESOLVED independently 2026-08-03, before this batch was ever dispatched** (batch is still
      `status: draft`): the `docs_reconciler` autonomous sweep fixed the SAME two lines directly at their source doc
      (`issues/docs_reconcile_autonomous_sweep_2026_07_30.md`'s own P2-E item, now `[x]` there too) —
      `act-secrets-setup.mdc:14` now reads `unified-api-contracts`, `test-coverage-targets.mdc`'s exempt-repo table now
      correctly says "three". Live-verified this run (`/ag-closeout-audit infra`, 2026-08-03): both files confirmed
      fixed, corpus-wide bare-name grep shows no new hits beyond the already-known-correct
      `pipeline-mode-partition-structure.mdc:79` mention (4 pre-existing unrelated bare-name hits remain in
      `sync-system.mdc` (x2), `provider-api-version-manifest.mdc`, `ui-quality-gates-typescript.mdc` — outside this
      todo's named scope, not touched). Marking done rather than dispatching a redundant worker onto an already-closed
      item.
- [x] ✅ [INFRA] P3. **DONE 2026-08-08 (infra)** — **Root-cause why `UV_LINK_MODE=hardlink` is not actually deduping
      `.venv` files across slots.** Confirmed a genuine fleet-wide REGRESSION, not the two originally-suspected causes:
      sampled 1,800 large `.so` files across all 16 slots — 1,800/1,800 `nlink=1` (zero cache→venv hardlinks exist
      anywhere today); the shared cache's own copy of the exact file from the original finding is ALSO `nlink=1` despite
      existing 11 days before the 7 venv copies compared against it — refuting "distinct cache entry per slot" (there is
      exactly one, confirmed shared). Cache-internal hardlinking still works (a few `nlink>1` hits inside
      `.uv-cache/archive-v0` itself), isolating the break to the install-into-venv step specifically. The 2026-06-29
      fix's code (`tmux_spawn.py`'s env export, `base-service.sh`'s derivation, `vm-disk-guard.sh`'s safe
      `uv cache prune`) is unchanged and still present — this isn't a reverted fix, and the mechanism is proven feasible
      (2026-07-17 `links=81` re-proof). **Verdict: FIXABLE, not yet fixed** — leading candidate is `scripts/setup.sh`
      never exporting `UV_LINK_MODE`/`UV_CACHE_DIR` itself (relies entirely on inherited env), but the exact regression
      trigger needs a live-tracing follow-up (out of this read-only investigation's scope) before a fix can be written.
      Full evidence + recommended next step in the dated finding. Source:
      `issues/host_root_disk_full_transient_2026_07_13.md` (todo's sub-item (b); (c) stays open, gated on the
      follow-up's outcome).

## Deferred — non-batchable this round

- **`docs_reconcile_autonomous_sweep_2026_07_30.md`'s P0-A (`check_codex_doc_freshness.py` 2026-08-15 cliff)** —
  OPERATOR-GATED (authority call among 4 stated options, `codex/**` edit). Not re-triageable; needs a ruling, then
  becomes normal batch material. Time-sensitive (13 days from this run's date) — flagged prominently in this run's
  parked-findings doc, not silently parked here.
- **`docs_reconcile_autonomous_sweep_2026_07_30.md`'s 4 dead codex doctrine refs + unterminated bold span** —
  human-judgment-gated (repoint-vs-delete call) / routes to `/plan-reconcile` per the source doc's own text
  respectively. Not extracted.
- **`plan_reconcile_autonomous_sweep_2026_07_30.md`'s sole todo** — already conflict-checked and deliberately held
  `assigned_vm: NA` by `/na-eligibility-audit` 2026-07-30. GENUINELY-HUMAN-BY-PRIOR-DECISION — not re-litigated by this
  skill (out of scope per its own "Also NOT `/na-eligibility-audit`" section). If the operator wants to overrule that
  hold, that is `/na-eligibility-audit`'s or the operator's call directly, not this batch's.
- **`production_readiness_checklist_file_missing_2026_07_24.md`'s sole todo** — GENUINELY HUMAN-ONLY (no mechanical way
  to determine the correct checklist item-count from repo state alone, per the source doc's own analysis). Will keep
  reporting orphaned until a human picks it up — an accurate signal, not a stuck audit.
- **`host_root_disk_full_transient_2026_07_13.md`'s cron-install sub-item** — OPERATOR-GATED (no crontab-write
  permission for this account on the affected host(s); the doc's own prior session confirmed `Permission denied`). Not
  extracted; the todo above extracts only the non-gated investigation portion.

## Operator approval gate

**This plan is `status: active` — operator-approved 2026-08-06, dispatching.** Flipped from `draft` (its finalize twin,
already `status: active` per the no-double-gate ruling) to `status: active` is the operator's call. Both todos above are
read-only/wording-only with no `[OPERATOR]` tag needed on their own merits (finding U: read-only investigation +
mechanical wording fix never carry `[OPERATOR]`) — the draft gate here is solely the standing "a skill-drafted AO batch
needs explicit operator sign-off before dispatch" rule, not a signal either todo itself is risky.

## Codex SSOTs (read before touching a todo)

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the procedure this batch was produced by
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol applied
  above
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule, dispatch-scope eligibility test

## Progress Log

- **2026-08-02** — Drafted by `/ag-closeout-audit infra` (autonomous mode, scheduled daily run, slot 11) after the 4
  net-new ex-meta tranche members were classified. Paired with
  `infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md` in the same run per the finalize-plan-coverage rule.
- **2026-08-03** — `/ag-closeout-audit infra` daily run (slot 12), iterative-drain step 1 (re-checking the prior batch's
  own content before fresh triage): todo 1 flipped `[x]` — its target was independently resolved by the
  `docs_reconciler` autonomous sweep earlier today, live-verified against the real files. Todo 2 (hardlink-dedup
  investigation) re-checked against `issues/host_root_disk_full_transient_2026_07_13.md`'s current state — still open,
  unchanged, still conflict-clear. This batch is still `status: draft`, still awaiting operator approval; only todo 2
  remains live if/when it is flipped to active.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — swapped the archived 2026-08-02 parked-findings
  doc for the sole remaining open todo's real targets: `host_root_disk_full_transient_2026_07_13.md` (where the
  investigation's finding must be recorded) and `base-service.sh` (the `UV_LINK_MODE` config site named in the todo's
  own text).
