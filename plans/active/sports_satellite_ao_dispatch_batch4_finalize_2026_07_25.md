---
doc_type: plan
title: Sports satellite AO batch 4 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch4_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 3 of that plan's todos are done. Mirrors sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md's
  pattern (reconcile each distinct source doc's checkboxes independently), plus the same batch3-style addition: re-check
  the 4 conflict-gated Deferred items once the operator has ruled on entries #5-8 in
  autonomous_session_operator_decisions_2026_07_25.md — some may become dispatchable as a batch5 once the operator
  confirms which side (the narrow batch-style fix vs. the master closeout's broader claim) should execute first, or how
  the ambiguous phantom-audit/decision-16 overlap should be sequenced.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch4_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan, mirroring the batch2/batch3 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 4 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch4_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because
> todo 2 (source-doc archival) needs todo 1's reconciliation done first (a doc can only be archived once its status is
> genuinely flipped to `resolved`), todo 3 (conflict-gated re-check) needs todo 1's reconciliation too, and todo 4
> (archival of this batch's own plan) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-13, review craft).** Reconcile all 3 distinct source docs' checkboxes. For
      each of `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s 3 now-done todos: flip the corresponding
      checkbox/section in its named source doc, citing the batch-4 commit(s) that shipped it — verify the actual shipped
      commit exists before citing it. The 3 source docs:
      `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`,
      `issues/fixtures_manifest_legacy_backfill_2026_07_24.md`,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`. For each: after flipping, re-check whether it now
      has 0 open todos remaining (checkbox AND prose-form — do not trust checkbox count alone). Only flip a doc's
      `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 3 source docs' corresponding
      checkboxes/sections are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped
      to `status: resolved`.

      **Evidence per doc**:
          1. `footystats_matches_predictions_fetch_gaps_2026_07_08.md` — batch4 todo 1 was diagnosis-only (found a genuine
             REGRESSION, not a fix) and its own worker (slot, 2026-07-27) already wrote the reconciling Progress Log entry
             directly into this doc at execution time (self-reconciling — no new edit needed). Verified current state: 1
             genuinely open todo (#4, `BLOCKED-PREREQUISITES` on the 2026-07-27 regression doc); `status: open` correctly
             unchanged — NOT 0 open todos, no resolved-flip warranted.
          2. `fixtures_manifest_legacy_backfill_2026_07_24.md` — batch4 todo 2 (slot-5/review, 2026-07-26) already edited
             this doc directly at execution time (the "Update (2026-07-26, slot-5/review — sports_satellite_ao_dispatch_
             batch4-002)" section is the reconciliation itself, self-reconciling). Verified current state: 1 genuinely open
             todo (the 55,233-row collision-residual delete-vs-leave decision); `status: open` correctly unchanged.
          3. `sports_odds_stale_fixture_reinjection_2026_07_14.md` — batch4 todo 3's read-only DIAG sweep
             (`market-tick-data-service@76ca401f`, verified ancestor of `origin/live-defi-rollout`) had NOT been reconciled
             into this doc yet. Updated todo 2's entry with the actual findings (RUSSIA_PREMIER_LEAGUE zombie confirmed
             still live across 18 `day=` partitions / 20 shards / 54 rows; AUSTRALIA_ALEAGUE resolved; CHINA_SUPER_LEAGUE
             correctly excluded) and filed the still-open purge/re-derive work as a new tracked `- [ ]` todo (batch4's DIAG
             scope was deliberately read-only — per the HARD RULE that every follow-up is a tracked todo, never left as
             prose). Verified current state: 2 genuinely open todos (the new purge todo + the pre-existing P3 gate-
             reassessment todo); `status: open` correctly unchanged.

          **Net**: none of the 3 source docs reached 0 open todos, so none was flipped to `status: resolved` — all 3
          genuinely still carry open work, verified per-doc rather than trusting checkbox counts. `unified-trading-pm`
          commit (this same commit).

- [ ] [DOC] P1. **Archive every source doc todo 1 drives to `status: resolved`/`complete` — in the same commit as the
      flip, never left sitting in `plans/active/`.** `check_terminal_status_archived.py` HARD-fails on any doc whose
      frontmatter reads a terminal status while it still lives under `plans/active/` (including `plans/active/issues/`)
      — the omission of this exact step across the sports finalize-plan family already forced one such HARD-fail: the
      `plan_health` gate's own remediation (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545)
      auto-archived 11 docs nobody's plan owned. For every one of the 3 source docs todo 1 flips to `resolved` with 0
      open todos: re-verify the 0-open-todos count and the resolution banner one more time, then archive it to
      `plans/archive/2026_07/` IN THE SAME COMMIT as the status flip — fix every corpus referrer of the archived doc's
      pre-archive path (grep for the basename). If todo 1 already ran before this todo existed in the plan, archive any
      already-`resolved`-but-still-active doc now, noting the flip predated this rule. **Done when**: no source doc this
      plan drives to a terminal status remains under `plans/active/`,
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and every corpus referrer resolves
      to the archived path. Source: `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
- [ ] [REVIEW] P1. **Resolve the 4 conflict-gated Deferred items from batch4's own doc**, now that the operator has
      (presumably) ruled on entries #5-8 in `autonomous_session_operator_decisions_2026_07_25.md`. For each of the 4
      items (`data_completion_sports_2026_07_24.md` Transfermarkt re-attempt [entry #5],
      `data_completion_sports_2026_07_24.md` ODDS+PREDICTIONS blank-reason measurement [entry #6],
      `sports_legacy_fixtures_path_migration_2026_07_24.md` fixtures-path census [entry #7],
      `issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` phantom spot-check [entry #8]): re-read the
      specific conflicting todo in `sports_consolidated_closeout_2026_07_19.md` to check if it has since shipped (which
      would resolve the conflict by making the narrower item redundant/already-covered) or if the operator's ruling
      clarified which side should execute — if either, either mark the item covered (cite the shipped commit) or extract
      it as a new tracked todo in a follow-up `batch5`. If still genuinely unresolved (operator hasn't answered yet),
      leave it explicitly deferred (not speculative) — do not re-surface it as a fresh operator-decision entry a second
      time, just note the re-check happened and it's still awaiting an answer. **Done when**: each of the 4 items has
      either (a) a new tracked todo/plan created because the conflict cleared, or (b) an explicit re-verified
      confirmation the conflict/decision is still open.
- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch4_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 3 above
      should have already resolved all 4 or confirmed them still-open — verify none silently vanish) → add the archive
      banner → run the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the
      corpus for every referrer of `sports_satellite_ao_dispatch_batch4_2026_07_25` and fix each path to point at the
      archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
