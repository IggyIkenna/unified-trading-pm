---
doc_type: plan
title: AO satellite AO batch 9 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch9_2026_08_08.md — machine-held via depends_on + gate_on_depends until
  that batch's single todo is done. Reconciles the verified todo's evidence back into
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s own checkboxes, archives that doc once fully closed (it
  has no other open items beyond the 2 this batch covers), and runs the standard 6-step archival ritual on the batch
  plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-9, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: review
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch9_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s own todo 3. Ships `status:
  active` (not draft) per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the
  batch's own todo is done, so a second draft-gate is redundant — only the batch itself needs `status: draft` + explicit
  operator approval.
---

# AO satellite AO batch 9 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until that batch's sole todo is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify batch9's done-claim against reality, not against its checkbox** — re-run
      `git show --stat <sha>` for the cited commit(s), re-run the specific named regression test, and re-check the
      14:30-16:30Z recurrence-timing question was actually answered (not left as a TODO inside the todo). **Done when**:
      the claim is verified, and any discrepancy is re-opened as a new tracked todo here with the discrepancy stated.
      **VERIFIED (2026-08-09, slot-24, review craft)** — see Progress Log below for the full evidence chain; every
      substantive claim held, one wrong SHA citation found + fixed (see the new todo below).
- [x] ✅ [REVIEW] P1. **Discrepancy found during the re-verify above, fixed in the same pass (small, well-evidenced,
      same-doc — not a redesign).** `ao_satellite_ao_dispatch_batch9_2026_08_08.md`'s own `summary:` frontmatter field
      cited `agent-orchestrator@41da3e578` as part of "that fix's code" for the composer-guard/one-shot-routing fix
      (paired with `@6166269`) — but `41da3e578`'s actual content (`git show --stat`) is a completely unrelated commit,
      `fix(slots_worker): reject /done with empty sha`, touching `server/routes/slots_worker.py` and
      `tests/test_done_empty_sha_gate.py`, nothing to do with `server/prompts.py` or one-shot/register-poll routing. The
      correct SHA for that half of the claim — already used correctly elsewhere in the SAME document's body text ("one-
      shot lifecycle roles via `@0a8ed16`") — is `0a8ed16` (confirmed:
      `fix(prompts): plan_health-family one-shot     dispatches skip generic /boot`, 2026-08-02T21:44:39Z, touches
      `server/prompts.py`). **Fixed**: corrected the `summary:` field's citation from `@41da3e578` to `@0a8ed16`. **Done
      when**: the wrong SHA is corrected — done, see Progress Log for the commit.
- [x] ✅ [REVIEW] P0. **Reconcile the verified todo's evidence into
      `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s own 2 remaining checkboxes** (`[DOCS] P1` and
      `[BACKEND] P2`), flipping both with the real commit sha(s). **Done when**: both flips are committed with the
      `docs(plans):` prefix and cite the real commit sha. **DONE (2026-08-09, slot-24, review craft)** — independently
      re-verified `agent-orchestrator@5353b6b` and `unified-trading-pm@6f7ed49c2` via `git show --stat` against their
      claimed content (both matched) and re-ran the named regression test fresh (38/38 passed) before flipping; both
      checkboxes flipped in the same commit as this one. See that doc's Progress Log for the full evidence chain.
- [x] ✅ [REVIEW] P0. **Archive `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`** once both its checkboxes
      are flipped (it has no other open items) — run the standard 6-step archival ritual (banner, codex-alignment check,
      fix every referrer's path corpus-wide, clear the lock). **Done when**:
      `grep -rl review_role_boot_read_unconfirmed_stuck_loop plans/ codex/` returns only the archived copy's own path.
      **DONE (2026-08-10, slot-11, review craft)** — see Progress Log below for the full ritual + a scope-driven second
      archival (`ag_closeout_audit_cross_cutting_parked_2026_08_02.md`) this pass also closed out.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md`, move to `plans/archive/2026_08/`, fix every
      corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py --commit` (verify the exact entrypoint name at
      execution time). **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips).

## Progress Log

- **2026-08-08** — Authored in the same turn as its batch by `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s
  own todo 3 (dispatch `ao_satellite_ao_dispatch_batch6_finalize-002`, slot 27, infra craft). `sequential: true` since
  the 4 todos are a genuine chain (verify → reconcile → archive source → archive self). Ships `status: active` per the
  skill's 2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).

- **2026-08-09 (slot-24, review craft) — todo 1 DONE, 1 discrepancy found + fixed**: re-verified every claim in batch9's
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` re-check against reality, not against its own checkbox
  text.
  - `agent-orchestrator@5353b6b` — `git show --stat` confirmed: touches `server/prompts.py`,
    `tests/test_role_file_worker_md_read_sync.py`, + 2 cefi fixture files. Content matches the claim exactly (cefi roles
    added to `_ONE_SHOT_ESCALATION_ROLES`, new regression test).
  - Named regression test `agent-orchestrator/tests/test_role_file_worker_md_read_sync.py` — re-ran fresh: **38/38
    passed**.
  - `agent-orchestrator@6166269` — confirmed real, timestamp `2026-08-08T19:35:33Z` matches the claim, diff matches
    (`_REGISTER_POLL_ROLES` guard for review/main/monitor).
  - **Discrepancy found**: `ao_satellite_ao_dispatch_batch9_2026_08_08.md`'s own `summary:` field cited
    `agent-orchestrator@41da3e578` alongside `@6166269` as "that fix's code" — but `41da3e578`'s real content
    (`git show --stat`) is `fix(slots_worker): reject /done with empty sha`, unrelated to `server/prompts.py` or
    one-shot/register-poll routing entirely. The correct SHA — already used correctly elsewhere in the SAME document's
    body ("one-shot lifecycle roles via `@0a8ed16`") — is `0a8ed16`, confirmed real and on-topic
    (`fix(prompts): plan_health-family one-shot dispatches skip generic /boot`, 2026-08-02T21:44:39Z). This reads as an
    innocent same-day-multi-commit citation slip, not fabricated evidence — the SUBSTANTIVE claim (composer-guard fix is
    live) is independently true and correctly cited elsewhere in the same doc — but a wrong commit-SHA citation is
    exactly the pattern this corpus has previously flagged as a real defect class
    (`mtds_plan_flip_fabricated_commit_sha_ evidence`, batch6). **Fixed same pass** (small, same-doc, well-evidenced —
    not a redesign): corrected the `summary:` field's `@41da3e578` → `@0a8ed16` in
    `ao_satellite_ao_dispatch_batch9_2026_08_08.md`.
  - Cross-checked the two named tests batch9's body claims batch6-finalize todo 1 re-ran
    (`test_register_poll_role_gets_slotless_shape_even_with_slot_id`,
    `test_one_shot_lifecycle_role_unaffected_by_ register_poll_guard`) — both exist in `tests/test_prompts.py`, re-ran
    fresh: **4 passed** (3 role-parametrized + 1 unaffected-check), 2 skipped (unrelated params).
  - `unified-trading-pm@6f7ed49c2` — confirmed real, touches `agents/review.md` + both this batch's plan +
    `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`, matching the claimed scope. Independently confirmed
    `review.md`'s current text (line 88) now reads "the gate described above no longer applies to this role" — the
    corrected historical-note framing, not a live-enforced claim.
  - **14:30-16:30Z 2026-08-08 recurrence-timing question** — re-checked, not left as a TODO-inside-the-todo: `6166269`
    landed `19:35:33Z` the same day, 3-5h AFTER the reported 14:30-16:30Z window, confirming the claim (recurrence
    PREDATES the fix, not a live regression). Question was genuinely answered, not deferred.
  - **Net verdict**: every substantive claim in batch9's done-claim holds under independent re-verification. One wrong
    commit-SHA citation found and fixed in the same pass (new todo above, closed inline). No other discrepancies.

- **2026-08-09 (slot-24, review craft) — todo 3 DONE**: flipped
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s remaining `[DOCS] P1` and `[BACKEND] P2` checkboxes,
  independently re-verifying `agent-orchestrator@5353b6b` and `unified-trading-pm@6f7ed49c2` (`git show --stat`, content
  matched claims) and re-running `agent-orchestrator/tests/test_role_file_worker_md_read_sync.py` fresh (38/38 passed)
  before flipping. That issue doc now has zero open checkboxes — todo 4 (archive it) is next.

- **2026-08-10 (slot-11, review craft) — todo 4 DONE**: ran the standard 6-step archival ritual on
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`. No DEFERRED item to migrate (both todos already closed
  with evidence, its own A/B/C options section was superseded by the doc reaching zero open work). While fixing
  referrers, found `ag_closeout_audit_cross_cutting_parked_2026_08_02.md`'s sole open `[DOCS] P3` todo (an `assigned_vm`
  reclassify) had gone moot — its target is now fully resolved, so there is nothing left to reclassify-and-dispatch —
  closed that todo as moot and archived that doc too in the same pass (its own zero-open- todos state is a direct,
  well-evidenced consequence of this archival, not a redesign). Two-commit flip-then-mv split per the archival ritual's
  own rule (never combine the checkbox flip with `git mv` in one commit): flip-only commit with `archive_exempt: true`
  as the sanctioned bridge (`b26e65ffe2`), then the actual `git mv` + banner + status flip (`f346b0c462`), then the
  corpus-wide referrer repoint (`75d519148a`) — `plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md`,
  `plans/active/issues/ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md`,
  `plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_06.md`, and
  `plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_07.md`'s `/plans/...` path citations now resolve
  to `plans/archive/2026_08/issues/`. No codex-alignment update needed — the mechanism fix (composer-guard routing +
  regression test) already landed in prior todos and codex has no SSOT describing this specific docs-drift incident.
  Verified: `grep -rl review_role_boot_read_unconfirmed_stuck_loop plans/ codex/` now returns only bare-slug prose
  mentions (no leading-slash path, out of `check_reference_paths.py`'s scope by design) plus the two archived docs' own
  paths — zero active-corpus `/plans/...` citations remain dangling.
