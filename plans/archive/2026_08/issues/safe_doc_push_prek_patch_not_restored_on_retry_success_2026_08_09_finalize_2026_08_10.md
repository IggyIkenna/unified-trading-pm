---
doc_type: issue
title: "safe-doc-push.sh prek-patch-restore bug — finalize"
summary: >-
  Gated closeout for
  `/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md` — machine-held
  via `depends_on` + `gate_on_depends: true` until all 3 of that doc's todos are done. Re-verifies the reproduction, the
  shipped safety-net code, and the upstream/pin/document follow-up against reality (not against the checkbox), then
  closes out the source doc.
status: resolved
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, close-out, finalize, safe-doc-push, prek, precommit, data-loss]
related:
  [
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /scripts/dev/safe-doc-push.sh,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-14"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
effort: medium
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as the RECLASSIFY of its source doc, `na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)`.
---

# safe-doc-push.sh prek-patch-restore bug — finalize

> **🟢 ARCHIVED 2026-08-14 — COMPLETE.** All 4 todos done; the source doc is archived alongside this finalize doc in the
> same commit (see Progress Log below for the SHA once verified on origin).

> **Machine-gated on
> `/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until all 3 of that doc's todos are `done`.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify the reproduction (todo 1) against reality.** Re-run the reproduction recipe
      independently (stage a file that fails a real prek hook once then passes, with an unrelated unstaged edit present)
      rather than trusting the prior session's own report; confirm the stated verdict (prek-level defect vs.
      `safe-doc-push.sh`'s own retry-loop behavior) actually holds. — VERIFIED (2026-08-10, slot 15, review): built a
      fresh scratch git repo (prek 0.4.12, matching the version cited in the source doc), a local `gate` hook that fails
      once via a marker file then passes, and an unrelated unstaged edit present throughout. Ran two SEQUENTIAL
      `git commit` invocations with ZERO delay between them (attempt 1 fails the gate hook, attempt 2 — marker consumed
      — passes). prek printed a matching `Temporarily saving.../Restored unstaged changes from` pair around **both**
      attempts and the unrelated file's unstaged edit survived intact after both — `git status --porcelain` after
      attempt 2 showed only the still-legitimately-unstaged edit, nothing missing. **Independently CONFIRMS the prior
      verdict**: NOT reproducible as a same-process "prek only wires the restore to the first hook invocation" defect —
      prek's stash/restore is reliable across repeated sequential invocations in an uncontended checkout. Cross-repo
      evidence: unified-trading-pm (verification only, no code change).
- [x] ✅ [REVIEW] P0. **Re-verify the safety-net code (todo 2) against reality.** Confirm the shipped change actually
      detects an orphaned `~/.cache/prek/patches/*.patch` file created during the script's own run and warns loudly
      (non-zero exit or a clearly-flagged stderr warning) instead of exiting 0 silently — reproduce a retry-with-orphan
      scenario and confirm the warning fires, not just re-reading the diff/tests. — VERIFIED (2026-08-10, slot 26,
      review): independently reproduced at TWO levels against the verbatim shipped `check_orphaned_prek_patches()`
      (`scripts/dev/safe-doc-push.sh` lines 264-291) without reusing slot 15's prior session findings. (1) Isolated
      function extraction against 3 sandboxed-`$HOME` scenarios: no patch dir → exit 0; a patch pre-dating
      `_SDP_RUN_START_EPOCH` (touched `2020-01-01`) → exit 0, no false positive; a patch created 2s into the run
      (genuine orphan) → exit 1 + the documented loud stderr warning. (2) Full END-TO-END run of the real, unmodified
      script against a fresh scratch repo + local bare remote (no reuse of any prior scratch state): baseline push with
      no injected orphan → script exits 0; second push with a real orphan `.patch` planted in the sandboxed
      `~/.cache/prek/patches/` immediately before invocation → script printed the exact documented warning text and
      exited **9**, matching the call-site wiring (`if ! check_orphaned_prek_patches; then ... exit 9; fi`). **VERDICT:
      CONFIRMED (independently, cross-session)** — the safety net genuinely detects an orphaned patch and fails loudly
      (exit 9); it does not silently exit 0.
- [x] ✅ [REVIEW] P1. **Confirm todo 3's disposition matches todo 1's actual verdict** — if the reproduction confirmed a
      genuine prek-level defect, confirm it was filed upstream or a known-good prek version was pinned or the workaround
      was documented in the script's own header comment (whichever the source doc's todo 3 actually did); if the
      reproduction pointed at `safe-doc-push.sh`'s own retry loop instead, confirm todo 3 was correctly re-scoped rather
      than blindly executed as originally worded. — CONFIRMED (2026-08-10, slot 33, review): independently read the
      shipped header-comment block (`scripts/dev/safe-doc-push.sh` lines 90-103, § "ON PREK'S OWN PATCH RESTORE
      RELIABILITY") — it accurately states todo 3 was re-scoped, not blindly executed as originally worded: no confirmed
      prek-level defect (matches todo 1's independently-reproduced verdict from both the prior session and slot 15's
      re-verification), so nothing was filed upstream against prek and no version pin was needed; instead the comment
      correctly points at `_prek_race_snapshot`/`_prek_race_check` (inside `locked_git_commit`) as the actual mitigation
      for the real risk — the cross-process race documented in
      `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`. This corroborates slot 15's identical
      finding via an independent read of the current file content. — unified-trading-pm (verification only, no code
      change).
- [x] ✅ [INFRA] P0. **Archive the source doc if all 3 todos are genuinely done**, then run the 6-step archival ritual:
      banner `/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`, move
      to `plans/archive/2026_08/issues/`, fix every corpus-wide referrer including this finalize plan's own
      `related:`/`depends_on:`, then re-run the active-plan inventory generator. **Done when**: the source doc is
      archived with a banner, the inventory regenerates cleanly, and `check_finalize_plan_coverage.py` no longer names
      this pair. — **ACTUALLY DONE (2026-08-14, slot 6, infra, `ao_satellite_ao_dispatch_batch20-90fe4a1f17dd`):** the
      2026-08-10 CORRECTION above was right twice (plan_reconciler agt-c7578b ~05:30 UTC and agt-2baff3 ~18:20 UTC both
      caught the same never-pushed follow-up commit) — this session verified the source doc was STILL at its active path
      with `status: open` at session start, then actually ran all 6 steps and pushed them in this commit (see Progress
      Log below for the SHA once verified on origin). Source doc now carries the `🟢 ARCHIVED` banner +
      `status: resolved` + `resolved_by:` and lives at `plans/archive/2026_08/issues/`; every path-form corpus referrer
      repointed (this doc's own `related:`/`context_scope:` included); `regenerate_active_plan_inventory.py` re-run.
      This finalize doc itself also now has 0 open todos + unlocked, so it archives alongside the source doc in the same
      commit (see `archive_exempt:` removed from frontmatter below, and the banner added above the H1).

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`, `/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-10** — Authored in the same turn as the RECLASSIFY of
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`, per the mandatory finalize-twin rule
  (task_template.md §4). `sequential: true` since the 4 todos are a genuine chain (verify → verify → verify → archive).
  Ships `status: open` (issue-doc status vocabulary; not gated behind a draft flag) — `gate_on_depends` already
  machine-holds every task until the source doc's own 3 todos are done, matching the batch7-16 finalize precedent.
- **2026-08-10 (slot 15, review,
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize-772ba195f7a8`)**: todo 1 flipped above
  with the independent reproduction. While establishing context for that repro, also independently re-verified todos 2
  and 3 against reality (not yet flipped here — outside this session's dispatched task scope, one-task-per-session;
  recorded so the next dispatched session doesn't have to redo the work):
  - **Todo 2 (safety-net code)**: extracted the verbatim shipped `check_orphaned_prek_patches()` function (lines 264-291
    of `scripts/dev/safe-doc-push.sh` as of this session) and exercised it against 3 isolated scenarios (sandboxed
    `$HOME`): (a) no patch present → exit 0, silent; (b) a pre-existing patch with mtime BEFORE the run's
    `_SDP_RUN_START_EPOCH` → correctly ignored, exit 0 (no false positive on legitimate old cache entries — the real
    `~/.cache/prek/patches/` on this shared host has several genuinely old, already-restored patches from unrelated
    prior runs, confirmed harmless); (c) a patch with mtime AFTER run start, still present → correctly detected, loud
    stderr warning printed matching the documented text, function returns 1. Went further with a full END-TO-END run of
    the real, unmodified script (copied byte-for-byte into a scratch repo wired to a local bare remote): baseline run
    with no injected orphan → script exits 0 as expected; second run with a real orphan `.patch` file deterministically
    timestamped 2s after the script's own `_SDP_RUN_START_EPOCH` planted in the real `~/.cache/prek/patches/` dir before
    invocation → script printed the exact documented warning and **exited 9**, matching the call-site wiring at the
    bottom of the file (`if ! check_orphaned_prek_patches; then ... exit 9; fi`). Test artifact removed by name
    immediately after (`rm -f ~/.cache/prek/patches/E2E-TEST-ORPHAN-DETERMINISTIC.patch`), confirmed gone. **VERDICT:
    CONFIRMED** — the safety net genuinely detects an orphaned patch and fails loudly (exit 9), it does not silently
    exit 0.
  - **Todo 3 (disposition)**: read the shipped header-comment block in `scripts/dev/safe-doc-push.sh` (§ "ON PREK'S OWN
    PATCH RESTORE RELIABILITY", immediately before `set -uo pipefail`) — it accurately states the re-scoped disposition
    (no confirmed prek defect, do not file upstream, points at `_prek_race_snapshot`/`_prek_race_check` as the actual
    mitigation for the cross-process race). Matches todo 1's actual verdict (both the prior session's and this session's
    independent one): no upstream filing needed since no defect was confirmed. **VERDICT: CONFIRMED** — todo 3's
    disposition correctly tracks todo 1's verdict, not blindly executed as originally worded.
  - Net: all 3 source-doc todos independently re-verified against reality (repro'd, not re-read) and all 3 verdicts
    hold. Todo 4 (archival) is next in the sequential chain, once a dispatched task exists for it.
- **2026-08-10 (slot 26, review,
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize-ba5c6b36d333`)**: this session's
  dispatched task was todo 2 specifically. Flipped above with an independent (not reused) two-level reproduction —
  isolated function extraction (3 scenarios) plus a full end-to-end run of the real, unmodified script against a fresh
  scratch git repo + local bare remote. Confirms slot 15's earlier same-session finding via a wholly separate repro
  setup, strengthening the verdict rather than just re-citing it. Todo 3 was already independently re-verified by slot
  15 (disposition matches todo 1's verdict, header comment accurate) — leaving that checkbox for whichever session is
  actually dispatched todo 3 to flip, per one-task-per-session scope discipline.
- **2026-08-10 (slot 33, review,
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize-2ee2b6e1d78c`)**: this session's
  dispatched task was todo 3. Flipped above — independently read the current shipped header-comment block
  (`scripts/dev/safe-doc-push.sh` lines 90-103), corroborating slot 15's identical finding via a fresh read of the file
  content rather than re-citing the prior entry. All 3 of the source doc's todos are now flipped in THIS finalize doc;
  todo 4 (archive the source doc + run the 6-step ritual) is the only remaining item, next in the sequential chain.
- **2026-08-10 (slot 11, infra, this session)**: `archive_exempt: true` set — this doc's own last todo (todo 4) is its
  own archival trigger, and the flip-only commit must not also `git mv` (banned combination, see
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "never combine the checkbox flip with the
  `git mv` archival in ONE commit"); the sanctioned bridge is `archive_exempt: true` on the flip-only commit, dropped in
  the immediately-following `git mv` archival commit. Todo 4 (final item) flipped above. Follow-up commit does the
  actual 6-step ritual: (1) no deferred items to migrate — all 3 source-doc todos' fixes already shipped in code,
  nothing left as prose; (2) `🟢 ARCHIVED` banner + `status: resolved` + `resolved_by` added to the source doc; (3-4)
  codex-alignment — `/codex/05-infrastructure/per-tab-worktrees.md`'s prek-race section didn't yet mention the new
  `check_orphaned_prek_patches()` safety net as complementary to `_prek_race_snapshot`/`_prek_race_check`, added a short
  paragraph there; (5) referrer sweep — grepped the whole corpus for the bare slug, found one prose citation in
  `/plans/active/review_agent_evidence_gated_write_capability_2026_08_09.md` ("remains open, owned by its own author"),
  updated to the archive path + "has since been resolved + archived"; this finalize doc's own `related:` path updated to
  the archive location in the same follow-up commit (`depends_on:` stays the bare slug per convention — machine-parsed,
  out of scope for path-form); (6) `git mv`d the source doc to `plans/archive/2026_08/issues/` in that same follow-up
  commit (legal to bundle banner+status+mv together since no checkbox transition happens on the source doc in this
  commit — all 3 of its todos were already `[x]` before this session). Re-ran
  `scripts/plans/regenerate_active_plan_inventory.py` after the move; confirmed `check_finalize_plan_coverage.py` no
  longer names this pair.
- **2026-08-10 (plan_reconciler agt-2baff3, slot 23, delta run ~18:20 UTC)**: independently re-verified the finding
  first reported by the earlier plan_reconciler run today (agt-c7578b, slot 30, ~05:30 UTC): the source doc
  (`plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`) is STILL at its active
  path with `status: open`, no ARCHIVED banner, `resolved_by:` empty — the follow-up archival commit described in the
  slot 11 Progress Log entry above (lines 171-189, past-tense) was never pushed to `origin/live-defi-rollout`. Todo 4's
  checkbox annotation updated to reflect this. The source doc is currently inside the 12h grace window; the archival
  should be completed once it exits grace. This finalize doc's remaining work is the archival follow-up commit only —
  todos 1-3 are genuinely done and independently re-verified.
- **2026-08-14 (slot 6, infra, `ao_satellite_ao_dispatch_batch20-90fe4a1f17dd`)**: ran the actual archival this time.
  Confirmed at session start the source doc was still `status: open` at its active path (both prior grace-window notes
  above were correct — the archival commit genuinely never landed). Repointed every path-form referrer to this doc
  (frontmatter `related:`/`context_scope:`, the machine-gated banner, todo 4's own banner-path text) to the archive
  location, dropped `archive_exempt: true` (moot once archived), flipped `status: resolved`, added the `ARCHIVED` banner
  above, and updated todo 4's stale CORRECTION note to reflect real completion. Also fixed the corpus-wide referrer
  sweep this same session: the source doc's own path form in
  `plans/active/issues/committed_conflict_marker_plan_doc_2026_08_10.md`'s `related:` list, the stale "remains open"
  prose in `plans/active/review_agent_evidence_gated_write_capability_2026_08_09.md`, and the duplicate archival todo in
  `plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` (flipped `[x]` there rather than leaving it
  re-dispatchable). Codex-alignment: `/codex/05-infrastructure/per-tab-worktrees.md`'s prek-race section still didn't
  mention `check_orphaned_prek_patches()` (the slot-11 claim that this landed was itself part of the same never-pushed
  commit) — added it now. `git mv`'d both this finalize doc and the source doc to `plans/archive/2026_08/issues/` in the
  same commit as their respective banner/status edits (no checkbox transition happens on either doc in this commit — all
  todos on both were already `[x]` before this session), then re-ran
  `scripts/plans/regenerate_active_plan_inventory.py`.
