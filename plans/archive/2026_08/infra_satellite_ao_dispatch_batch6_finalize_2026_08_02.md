---
doc_type: plan
title: Infra satellite AO dispatch batch 6 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch6_2026_08_02.md`, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24; machine-enforced by
  `scripts/quality_gates/check_finalize_plan_coverage.py`). Once both batch todos are done, reconciles the corresponding
  checkbox back into each source doc (`issues/docs_reconcile_autonomous_sweep_2026_07_30.md`'s P2-E todo,
  `issues/host_root_disk_full_transient_2026_07_13.md`'s `[INFRA] P2` todo) and checks whether either source doc is now
  an archival candidate. Neither source doc is expected to fully archive — both keep other operator/judgment-gated
  remainder work at `assigned_vm: NA` (the codex-freshness P0-A decision + dead-doctrine-ref judgment calls in the
  first; the cron-install operator-gated sub-item in the second) — so this plan's main job is to flip accurately and
  confirm neither is prematurely archived, then run the standard ritual on the batch pair itself.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, finalize, batch-6, plan-hygiene]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/active/issues/host_root_disk_full_transient_2026_07_13.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch6_2026_08_02]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch6_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch by `/ag-closeout-audit infra` (2026-08-02), per the standing
  finalize-plan-coverage rule (every ≥2-todo `assigned_vm: planning` plan needs a gated finalize twin).
---

# Infra satellite AO batch 6 — finalize

> **ARCHIVED 2026-08-09 (slot 14) — all 3 todos `[x]`, 6-step archival ritual complete for the batch pair.**

Machine-held via `depends_on` + `gate_on_depends: true` until both of
`infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s todos are done — this plan can never dispatch early, regardless of
whether the batch is `draft` or `active` at the time (the gate reads the batch's own checkboxes directly, per the
skill's no-double-gate mechanism).

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile `issues/docs_reconcile_autonomous_sweep_2026_07_30.md`'s P2-E todo.** Once batch6's
      bare-name-wording todo ships, flip that source doc's
      `- [ ] [DOC] P2. Retire the 5 bare-name unified-trading-codex mentions (P2-E)` checkbox to `[x]`, citing the
      batch6 commit SHA, and note that the doc's own P2-E section text (which already narrowed this to 2 genuinely-
      stale mentions) is now resolved. Do NOT touch any other section of this doc (P0-A, P1-C, P1-D remain open,
      operator/judgment-gated — this doc stays `assigned_vm: NA`, NOT an archival candidate). (repo: unified-trading-pm)
      — **VERIFIED 2026-08-08**: source doc's P2-E checkbox was already `[x]` before batch6 dispatched — flipped by the
      docs-reconcile 2026-08-03 sweep (`unified-trading-pm@2ae6762fc`) which fixed `act-secrets-setup.mdc:14` +
      `test-coverage-targets.mdc:80` (the 2 genuinely-stale mentions) and flipped the checkbox in-sweep. Batch6's own
      todo 1 acknowledged "RESOLVED independently 2026-08-03, before this batch was ever dispatched." Source doc
      confirmed NOT an archival candidate: 1 open todo remains (P1-C `sync-system.mdc` — human decision on DO: line, no
      successor script). No other section touched.
- [x] ✅ [REVIEW] P3. **Reconcile `issues/host_root_disk_full_transient_2026_07_13.md`'s `[INFRA] P2` todo.** Once
      batch6's hardlink-investigation todo ships (with its dated finding + fixable/not-fixable verdict recorded in that
      doc), update the source doc's own `[INFRA] P2` todo to reflect the investigation is done: if the finding is
      NOT-FIXABLE or fixable-but-out-of-scope-here, flip the checkbox `[x]` citing the batch6 commit and the recorded
      verdict; if a concrete fix was identified but not yet built (per batch6's explicit scope exclusion on
      building/deploying prune tooling), leave the checkbox open but update its text to reflect the narrowed remaining
      scope (the fix-build step only, not the whole original 3-part item) and confirm the cron-install sub-item is still
      correctly `[OPERATOR]`-gated. This source doc keeps its own operator-gated remainder either way —
      `assigned_vm: NA`, NOT an archival candidate this round. (repo: unified-trading-pm) — **DONE 2026-08-08**:
      batch6's verdict (`88668b743`) was FIXABLE-not-yet-built, so per this todo's own second branch the checkbox was
      left OPEN in the source doc and its text narrowed to the fix-build step only (add `UV_LINK_MODE`/`UV_CACHE_DIR`
      exports to `scripts/setup.sh` + single-repo `nlink>1` verification); cron-install sub-item (a) confirmed correctly
      `[OPERATOR]`-gated (already done). Source doc confirmed NOT an archival candidate — `assigned_vm: NA` unchanged.
      See `issues/host_root_disk_full_transient_2026_07_13.md` Progress Log for the full reconciliation entry.
- [x] ✅ [DOC] P3. **Archive `infra_satellite_ao_dispatch_batch6_2026_08_02.md`** once both todos above are done and
      both reconciliations are verified — run the standard 6-step archival ritual (`git mv` to `plans/archive/2026_08/`,
      fix every corpus referrer path, confirm `check_ag_closeout_linkage.py` and `regenerate_active_plan_inventory.py`
      both stay clean). Do this as a SEPARATE commit from the checkbox-flip commits above (never combine a flip +
      `git mv` in one commit — 2026-07-30 incident,
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). (repo: unified-trading-pm) — **DONE
      2026-08-09** (slot 14): both reconciliations above verified against current source-doc state; batch pair archived
      to `plans/archive/2026_08/` in the immediately following commit (this plan itself also reaches 0 open todos here,
      so it archives alongside its parent batch per the archival-discipline SSOT's archive-immediately rule — see
      `archive_exempt: true` bridge above).

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual + the
  never-combine-flip-with-git-mv rule
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-02** — Authored alongside `infra_satellite_ao_dispatch_batch6_2026_08_02.md` by `/ag-closeout-audit infra`
  (autonomous mode, scheduled daily run, slot 11).
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (2 entries), still accurate — a genuinely code-free
  finalize/gate doc.
- **2026-08-09** (slot 14): all 3 todos now `[x]` — both source-doc reconciliations were already verified done
  (2026-08-08) and confirmed still accurate against current file state; flipped todo 3 and archiving the batch pair as
  the immediately following commit.
