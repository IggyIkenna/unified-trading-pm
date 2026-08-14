---
doc_type: plan
title: ao satellite AO batch 20 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch20_2026_08_13.md — machine-held via depends_on + gate_on_depends
  until every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source doc's
  checkbox (this was an extraction batch, so the source docs' own checkboxes are the ones that go stale), archives any
  source doc that reaches zero open todos as a result, and runs the standard 6-step archival ritual on the batch plan
  itself.
status: archived
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch20_2026_08_13.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-14"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch20_2026_08_13]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch20_2026_08_13.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-sweep session. Ships
  status: active (not draft) per the /ag-closeout-audit skill's 2026-07-30 finding: gate_on_depends already
  machine-holds every task until the batch's own todos are done, so a second draft-gate is redundant.
---

# ao satellite AO batch 20 — finalize

> **ARCHIVED 2026-08-14** — all 3 todos done. The gated batch
> (`/plans/archive/2026_08/ao_satellite_ao_dispatch_batch20_2026_08_13.md`) reached zero open todos, so this finalize
> plan closed itself out via the standard 6-step archival ritual, same-commit flip+archival (single-repo mode-1,
> sanctioned per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).

> **Machine-gated on `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch20_2026_08_13.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P2. For every completed todo in `ao_satellite_ao_dispatch_batch20_2026_08_13.md`, reconcile the
      evidence back into its cited `Source:` doc's own checkbox — find the matching item in the source doc and either
      flip it `[x]` with a citation to this batch's commit, or add a note pointing at the batch todo that superseded it.
      Do not trust the batch's own checkbox alone; re-verify each cited commit sha is real. Done when: every source doc
      touched by this batch has its corresponding item's checkbox state reconciled. **DONE 2026-08-14** — reconciled all
      12 unique `Source:` docs cited across batch20's 30 todos, this commit: `ao_consolidated_closeout_2026_08_12.md` (2
      flips), `mac_slot0_base_checkout_stuck_dirty_files_2026_08_11.md` (1),
      `ao_open_issues_consolidated_close_out_2026_07_17.md` (1),
      `deepseek_claude_blended_provider_routing_2026_07_28.md` (1 flip — its second cited item, the flash-pro readout,
      was already reconciled by a prior 2026-08-14 bookkeeping pass, verified not re-touched),
      `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md` (6 items, all already `[x]` in
      source — verified, no action needed), `ag_closeout_audit_ao_parked_2026_08_10.md` (1),
      `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` (1 flip already-correct verified no-op, 1
      stale-annotation correction, **2 items — attribute `deepseek_spawn_selected` caller, and the CLI-version-vs-
      upstream-issues check — have NO matching checkbox or prose item anywhere in this doc; confirmed via full-doc
      grep + `git log --all -S` on the exact batch20 wording, zero hits. This looks like a citation error in batch20
      itself, not a reconciliation gap — the underlying commits are real and already on `live-defi-rollout`, just not
      attributable to any open item in the cited source doc**),
      `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` (already `[x]` in source — verified, no action
      needed), `forced_compact_reports_submitted_but_never_executes_2026_08_08.md` (1),
      `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` (1),
      `plan_reconciler_findings_ao_2026_08_10.md` (9 flips — the full "Once `<doc>` exits grace" follow-up block). Every
      cited SHA re-verified real via `git log` against `origin/live-defi-rollout` before citing (not trusted from the
      batch's own checkbox text alone) — caveats/discrepancies found are flagged inline at each doc rather than silently
      accepted (see the `deepseek_claude_blended_provider_routing_2026_07_28.md` Skills-CLI item's
      live-cycle-verification gap, and the 2 uncited-in-source tmux-doc items above).
- [x] ✅ [REVIEW] P2. For each source doc reconciled above, check whether it now has zero open todos. If so, run the
      standard 6-step archival ritual on it (dated archive folder, exact-successor banner if applicable, corpus-wide
      referrer-path fixup) — do not leave a now-fully-done source doc live and un-archived. Done when: every source doc
      left with zero open todos is archived, and `run_hygiene_sweep.sh` reports no orphan referrers to any of them.
      **DONE 2026-08-14** — `unified-trading-pm@daca8cb4c0`. Of the 12 unique `Source:` docs, exactly 3 had reached zero
      open todos (each was `archive_exempt: true` deliberately, per todo 1's "Drop `archive_exempt` when that todo
      runs"): `ao_open_issues_consolidated_close_out_2026_07_17.md`, `ag_closeout_audit_ao_parked_2026_08_10.md`,
      `forced_compact_reports_submitted_but_never_executes_2026_08_08.md` — all 3 archived to `plans/archive/2026_08/`
      via the 6-step ritual (banner + status flip + `git mv`). The other 9 source docs still carry open todos (1-15
      each, one also `locked_by`) and were left untouched, correctly. Verified `ao_open_issues...` is NOT itself part of
      the `ao` closeout-family (filename doesn't match the `ao_consolidated__` prefix `check_ag_closeout_linkage.py`
      resolves on) — the tranche's live coordinator (`ao_consolidated_closeout_2026_08_12.md`) is unaffected.
      Corpus-wide referrer-path fixup: repointed the 21 active-corpus/codex hits `check_reference_paths.py` flagged as
      newly- DANGLING against the 3 moved paths (dangling-ref count unchanged from pre-move baseline: 64/86 existence,
      52/81 format). **Adjacent regression caught + fixed**: archiving
      `ao_open_issues_consolidated_close_out_2026_07_17.md` dropped it out of `check_ag_closeout_linkage.py`'s
      active-doc graph, breaking indirect 2-3-hop `[ao]` linkage paths for 9 UNRELATED docs that had relied on it as a
      bridge to the live coordinator (confirmed via `git stash` A/B: 0 orphans clean, 9 orphans with just the archival
      applied) — fixed by adding a direct `related:` link to `ao_consolidated_closeout_2026_08_12.md` on each of the 9.
      Re-verified clean post-ship: `check_ag_closeout_linkage` 0 orphans (baseline 0), `check_reference_paths` at
      baseline, `regenerate_active_plan_     inventory.py` 0 orphans, `check_archive_candidates.sh` 0 candidates
      (baseline 0), `check_line_caps.sh` not a regression. `run_hygiene_sweep.sh` itself not run standalone (heavy
      full-corpus script; the 5 constituent checks this todo's done-condition depends on were run directly and are all
      clean).
- [x] ✅ [REVIEW] P2. Once `ao_satellite_ao_dispatch_batch20_2026_08_13.md` itself has zero open todos, run the standard
      6-step archival ritual on it, then archive this finalize plan too. Done when: the batch plan and this finalize
      plan are both under `plans/archive/`, and `regenerate_active_plan_inventory.py` reports zero orphan referrers to
      either. **DONE 2026-08-14** — unified-trading-pm(this commit): confirmed batch20 had 0 open todos (grep-verified),
      then ran the 6-step ritual on both docs in one commit (single-repo mode-1 finalize plan — plan-of-record is this
      worker's own PM worktree, so same-commit flip+archival is the sanctioned shape per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): ARCHIVED banner + `status: archived` on
      both docs, `git mv` both to `plans/archive/2026_08/`, mutual cross-references between the two docs repointed to
      the new archive path. Corpus-wide referrer check: `check_reference_paths.py`'s machine oracle only flags
      leading-slash `/plans/...`/`/codex/...` refs (`GOOD_REF_RE`) plus unpathed `related:`-frontmatter bare refs
      (`BARE_MD_RE`, scoped to the `related:` field only, not body prose) — a corpus grep for leading-slash refs to
      either doc's old `/plans/active/...` path found zero hits outside the two docs' own mutual references (now fixed)
      and one hit inside an already-archived doc (`plans/archive/` is excluded from the scan by design). The ~10
      active-corpus docs citing either doc by bare filename in body prose (Source: citations, evidence pointers) are out
      of the oracle's scope and were left as historical citations, per the same precedent todo 2 above already
      established for the 3 earlier source-doc archivals. `regenerate_active_plan_index.py` +
      `regenerate_active_plan_inventory.py` re-run post-move to drop both from `INDEX.md` and confirm zero orphan
      referrers.
