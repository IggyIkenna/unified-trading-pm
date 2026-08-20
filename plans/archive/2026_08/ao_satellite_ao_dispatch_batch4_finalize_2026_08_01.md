---
doc_type: plan
title: AO satellite AO batch 4 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch4_2026_08_01.md — machine-held via depends_on + gate_on_depends until
  the batch's sole todo is done. Reconciles the completed todo's evidence back into its TRUE source issue doc (the batch
  was an extraction, so the source doc's own checkbox is the one that goes stale), archives the source doc if it reaches
  zero open todos, and runs the standard 6-step archival ritual on the batch plan itself.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-4, finalize]
related:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch4_2026_08_01]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  2026-08-01 alongside the batch4 rename/correction (this pair was originally missing — the doc that became batch4 was
  drafted without its finalize twin during the prior session's finalize pass). Ships `status: active` (not draft) per
  the same 2026-07-30 finding batch3_finalize applied: `gate_on_depends` already machine-holds every task until the
  batch's own todo is done, so a second draft-gate is a redundant, easy-to-forget manual flip.
---

# AO satellite AO batch 4 — finalize

> **🟢 ARCHIVED 2026-08-10** — all 5 todos `[x]`, `locked_by:` empty. Batch 4's sole todo re-verified + evidence
> reconciled into its true source doc, source doc confirmed correctly NOT archived (2 open todos remain outside this
> pair's scope), file-adjacency caution against batch3 confirmed respected, and batch4 itself archived alongside this
> plan — verified by plan_reconciler agt-c7578b.

> **Machine-gated on `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until that plan's sole todo is `done`. No separate `status` flip needed
> either way (mirrors batch3_finalize's convention).

## Todos

- [x] [REVIEW] P0. **Re-verify batch-4's done-claim against reality, not against its checkbox** — for the sole todo in
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md`, re-run `git show --stat <sha>` for the
      cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run the todo's
      own stated done-when check (the silent-but-alive-owner simulation test). **Done when**: verified, and if the
      evidence does not hold up, re-opened as a new tracked todo in this doc's Progress Log with the discrepancy stated.
      — **Verified, holds up.** `agent-orchestrator@7911083` — `git show --stat` confirms the cited commit exists on
      `live-defi-rollout` HEAD (`3c93cf7`) touching exactly `server/worker_liveness_watchdog.py` (+42/-4) and
      `tests/test_worker_liveness_watchdog.py` (+138); diff-read confirms `_reconcile_unacked_dispatches` now requires
      `_pane_is_dead(sess)` (fail-closed on exception) before releasing, matching the commit message's claim. Re-ran the
      3 named tests directly
      (`.venv/bin/python -m pytest tests/test_worker_liveness_watchdog.py -k     "test_reconcile_unacked_silent_but_alive_owner_keeps_lease or test_reconcile_unacked_dead_owner_still_released or     test_reconcile_unacked_no_session_still_released"`)
      — 3 passed, including the todo's own stated done-when check
      (`test_reconcile_unacked_silent_but_alive_owner_keeps_lease`, the silent-but-alive-owner simulation). Full
      `tests/test_worker_liveness_watchdog.py` also re-run clean (96 passed, 0 failed — no regression in the touched
      file). `basedpyright server/worker_liveness_watchdog.py` — 0 errors, 0 warnings, 0 notes. No discrepancy found;
      nothing re-opened.
- [x] [REVIEW] P0. **Reconcile the verified todo's evidence back into its TRUE source doc's own checkbox** — batch 4 was
      an extraction, so `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`'s `[BACKEND] P2` item is
      the one that goes stale, not the batch's. Flip it with the real commit sha. **Done when**: the flip is committed
      with the `docs(plans):` prefix and cites the real commit sha. — **Already done, independently re-verified.** The
      reconciliation landed in `unified-trading-pm@04a11439d` ("docs(plans): flip ao_satellite_ao_dispatch_batch4 sole
      todo — failover double-dispatch fix shipped"), which flipped the source doc's `[BACKEND] P2` item to `[x]` citing
      `agent-orchestrator@7911083` with full root-cause + test evidence, and added a matching Progress Log entry. Both
      commits independently re-verified this pass: `04a11439d` is on `origin/live-defi-rollout` and touches exactly the
      source issue doc (+ the batch4 plan); `agent-orchestrator@7911083`
      (`fix(dispatch): require positive liveness     re-check before releasing an un-ACKed task`) is also on
      `origin/live-defi-rollout`, touching `server/worker_liveness_watchdog.py` (+42/-4) and
      `tests/test_worker_liveness_watchdog.py` (+138) — matches the cited diff exactly. No further flip needed.
- [x] [INFRA] P0. **Confirm the file-adjacency caution against `batch3_2026_07_31.md`'s todo 2 was actually respected**
      — check whether batch 4's todo landed before or after batch3's todo 2, and whether the two diffs conflicted in
      `agent-orchestrator/server/worker_liveness_watchdog.py` (or wherever they actually landed). If a real collision
      occurred despite the sequencing note, record what happened and whether a follow-up cleanup is needed. **Done
      when**: the actual landing order and any conflict outcome is recorded here. — **Respected; verified via
      `git show --stat` + `git log --reverse` against `origin/live-defi-rollout`.** Landing order: batch3's todo 2
      (`agent-orchestrator@af98fcd`, 2026-08-01 13:31:26+05:30) landed **before** batch4's sole todo
      (`agent-orchestrator@7911083`, 2026-08-01 14:09:29+05:30) — confirmed both by commit timestamp and by position in
      `git log origin/live-defi-rollout --oneline --reverse` (af98fcd precedes 7911083). No conflict occurred: `af98fcd`
      touched exactly `server/config.py`, `server/dedup_state.py`, `server/dispatch_priority_inversion_watchdog.py` (new
      file), `server/notifications/slack.py`, `server/server.py`, `tests/test_dispatch_priority_inversion_watchdog.py`
      (new file) — it never touched `server/worker_liveness_watchdog.py` at all, per its own commit message's stated
      intent ("Deliberately a standalone module ... to avoid the file-adjacency collision flagged for the sibling batch4
      ... todo"). `7911083` touched only `server/worker_liveness_watchdog.py` and
      `tests/test_worker_liveness_watchdog.py`. `comm -12` on the two commits' changed-file lists returns empty — zero
      file overlap. So batch3 satisfied the caution by sidestepping the shared file entirely (not merely by sequencing),
      and batch4's todo landed into an otherwise-untouched `worker_liveness_watchdog.py`. No follow-up cleanup needed.
- [x] [REVIEW] P0. **Archive the source doc if it has reached zero open todos, and repoint any referrer.** Check
      `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` — its P3 `/done`-idempotency sibling is
      separately file-collision-held (not part of this batch), so do NOT archive if that item is still open there. Run
      the standard 6-step archival ritual (banner → codex-alignment check → fix every referrer's path corpus-wide →
      clear the lock) only if the doc is genuinely fully done. **Done when**: `grep -rl <slug> plans/ codex/` returns
      only the archived copy's own path if archived, or a stated reason it wasn't. — **Not archived; genuinely NOT fully
      done.** Read the source doc's Todos section directly (not a checkbox count): only the `[BACKEND] P2`
      release-signal/liveness item is `[x]` — TWO `[BACKEND] P3` items are still `[ ]` open: (1) "clear/curl-invalidate
      the prior owner's slot-side `current_task` on re-dispatch" and (2) the `/done`-idempotency item named in this
      todo's own caution (still separately file-collision-held against `server/routes/slots_worker.py`, per the source
      doc's own 2026-08-01 Progress Log entry). Since 2 of 3 todos remain open, the doc fails the "zero open todos"
      archival bar regardless of the P3-idempotency caution alone. No archival ritual run; no referrer repointing needed
      since nothing moved. Verified via
      `grep -rl orchestrator_failover_double_dispatch_duplicate_work_2026_07_25 plans/ codex/` — 13 referrer hits, all
      still pointing at the live `plans/active/issues/` path (no archived copy exists to repoint to).
- [x] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md`, move the file to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py`. **Done when**: the batch plan is archived
      with a banner, the inventory regenerates with an orphan count of 0, and `check_finalize_plan_coverage.py` no
      longer names this pair. — verified by plan_reconciler agt-c7578b 2026-08-10: file confirmed at the archived path
      (this doc's own `related:`/banner already cite it correctly); corpus-wide grep for the stale active path found 0
      live referrers (2 hits are both inside already-archived historical docs, correctly describing history);
      `check_finalize_plan_coverage.py` run live — 0 violations, pair not named. Corpus-wide inventory orphan count is
      currently 2, but both are unrelated `tradfi_satellite_ao_dispatch_batch12_2026_08_10`(`_finalize`) docs, not this
      pair — not a blocker for this specific archival.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-01** — Authored alongside the batch2→batch4 rename/correction. This pair was originally missing its finalize
  twin (the prior session's finalize pass drafted the batch but not its gate); added now to close that gap before
  dispatch, mirroring batch3_finalize's `sequential: true` / `status: active` (not draft) convention. Only 4 todos, not
  5, since batch4 carries a single todo (the dirty-sweep item was dropped as moot before this pair was even finalized) —
  no separate "re-check Deferred gates" todo is needed since this batch's own Deferred-derivation chain ends here
  (batch4 was itself already a Deferred-gate re-check of batch1; it named no further Deferred items of its own to
  re-check).
- **context-scout 2026-08-01**: verified the 3 pre-existing context_scope entries still resolve and are relevant (kept
  in place), added the gated parent batch plan as a 4th entry — refreshed (4 entries).
- **2026-08-01 (todo 3)** — Verified via `git show --stat` on both commits +
  `git log origin/live-defi-rollout --oneline --reverse` position: batch3 todo 2 (`agent-orchestrator@af98fcd`) landed
  2026-08-01 13:31:26+05:30, batch4's sole todo (`agent-orchestrator@7911083`) landed 2026-08-01 14:09:29+05:30 — batch3
  first, as the file-adjacency rule required. `af98fcd` deliberately never touched `server/worker_liveness_watchdog.py`
  (kept the priority-inversion watchdog a standalone module instead), so `comm -12` on the two commits' changed-file
  lists is empty — zero overlap, no collision. No follow-up cleanup needed.
- **2026-08-01 (todo 4)** — Source doc `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` NOT
  archived: it still carries 2 open `[BACKEND] P3` todos (the current_task-clearing observability item, and the
  `/done`-idempotency item file-collision-held against `server/routes/slots_worker.py`), not just the one P3 caution
  named in this todo's own text. Only the `[BACKEND] P2` item is done. No archival ritual run; referrer grep (13 hits,
  all still on the live path) confirms nothing needed repointing.

- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still the correct archival SSOT + batch pointer;
  no change needed. Gated finalize doc, no source path.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (4 entries), still accurate — sole open todo (5) is
  the archival ritual itself, no source path applies.
