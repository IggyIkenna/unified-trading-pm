---
doc_type: plan
title: Review agent gets evidence-gated write capability — revert false-done claims + patch small fixes
summary:
  Review is currently pure-advisory (chat-only) even when its own LIGHT-tier PR review concludes a claimed-done task
  does NOT satisfy its done_definition — today the only action is a conversational ping. This plan gives review two
  narrow, evidence-gated write powers — revert a false-done checkbox/backlog row, and patch a small well-scoped
  remaining fix — both routed through the SAME quality gates a worker uses, with clear commit attribution so the audit
  trail still distinguishes review-authored from worker-authored changes. Built + tested locally in one session —
  operator direction 2026-08-09, local/human track, not AO-dispatched.
status: active
nature: design
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [role, review, write-capability, evidence-gated, plan-flip, backlog]
related: [/agents/review.md, /agents/worker.md, /agents/RULES.md, /plans/active/ao_consolidated_closeout_2026_08_12.md]
created: "2026-08-09"
last_updated: "2026-08-20" # was 2026-08-09 -- stale vs the 2026-08-17 na-eligibility-audit + context-scout entries; corrected (plan_reconciler ao)
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
effort: high
locked_by:
locked_since:
context_scope:
  [
    /agents/review.md,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/server/routes/slots_worker.py,
    scripts/dev/safe-doc-push.sh,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
supersedes:
superseded_by:
depends_on:
source: operator (interactive session, 2026-08-09)
assigned_role: review
drift_direction: advance-code
---

# Review agent gets evidence-gated write capability

## Background

A 2026-08-09 audit of the last ~25h of `/done` hard-409 rejections (26 unique slot+task incidents) found the plan-flip
gate itself working correctly — 62% self-heal via same-session retry, the rest legitimately parked behind real
prerequisites. The actual gap was narrower: review.md's watched-event list never included the hard-reject event family
at all (fixed same day, `unified-trading-pm@684dd4f8d0`).

That fix closed the visibility gap. This plan answers the follow-up question the operator raised: if review can only
ever flip a checkbox when a task is _already_ fully verified done, that's nearly a no-op — the 62% that self-heals
already does this via ordinary retry. The two things that would make review worth being a stateful, judgment-bearing
agent (rather than a polling script) are the two things "checkbox-flip-only" explicitly excludes:

1. **Reverse a false claim.** Review's existing evidence-backed-completion duty (review.md §"Evidence-backed
   completion") already tells it, today, when a `- [x]` is an over-claim — it just can't act, only ask.
2. **Patch the small remaining piece itself** when the gap is trivial and well-evidenced, instead of paying a full
   ping-worker-and-wait round trip.

Key discovery during design: `agent-orchestrator`'s `POST /api/backlog/{task_id}/reopen` endpoint already exists and its
own docstring explicitly names this exact caller — _"an operator or an **audit script** confirms the plan's checkbox is
still unflipped, then calls this to honestly requeue the task."_ No new orchestrator-side endpoint is needed for the
backlog-correction half; review just needs to become that audit script.

## Design

**Trigger**: review's existing LIGHT-tier review step (diff vs. `done_definition`) concludes a claimed-done task does
NOT actually satisfy its done_definition — i.e. a genuine over-claim, not a style nitpick.

**Guardrails (apply to both capabilities below)**:

- Only ever acts on a verdict it has independently verified with evidence (re-reads the diff, re-runs the cited
  build/check) — never on an unverified hunch.
- Every commit review makes runs through the SAME gate a worker would: `quality-gates.sh` + `quickmerge --agent --files`
  for code, `safe-doc-push.sh` for docs-only. No shortcut path.
- Every review-authored commit message is prefixed `review-revert:` or `review-fix:` so it is grep-distinguishable from
  worker commits in history — this is the "who reviews the reviewer" answer: visibility, not a blocking gate.
- Never acts on a task that is currently `dispatched` (a live worker owns it) or `blocked`/`queued` with an unmet
  prerequisite (§ the 2026-08-09 audit's "legitimately parked" class) — only on a task the backlog shows as `done`
  (capability 1) or where review is about to leave its OWN light-review finding as the terminal action (capability 2).
- "Patch the small remaining piece" is bounded to a fix directly implied by review's own finding (e.g. "done_definition
  says X, the diff does everything but X, X is a 1-3 line change") — never open-ended/redesign work. If review is not
  confident the fix is small and obviously correct, it pings the worker instead, same as today.

### Capability 1 — revert a false-done claim

1. Detect: LIGHT-tier review finds the diff does not satisfy done_definition, AND the backlog shows `status: done` for
   that task_id (`GET /api/backlog` filtered by id).
2. If the plan checkbox is already `[x]` (the commit DID touch it, satisfying the mechanical gate, but the substance is
   wrong): edit the plan file, flip `- [x] N. ✅ ...` back to `- [ ] ...`, strip/annotate the false evidence citation,
   add one inline note (`REVERTED by review <date> — <one-line reason>, see chat msg <id>`). Commit via
   `safe-doc-push.sh`, message prefixed `review-revert:`.
3. Call `POST /api/backlog/{task_id}/reopen` with `{"reason": "<one-line reason>", "requested_by": "review:<agent_id>"}`
   — resets the backlog row to `queued` (refuses cleanly with 409 if the task is currently `dispatched`, which is the
   correct behavior: don't yank work from a live worker).
4. Ping the worker (existing mechanism, unchanged) with the same reason, PLUS note explicitly that the task has been
   reopened so they know to re-pick it up rather than think it's still theirs.
5. Chat-to-main note only if this is a repeat pattern (same shape as the existing `slot_dual_flip_pattern_violation`
   escalation) — a single revert is routine, not an incident.

### Capability 2 — patch a small, well-evidenced remaining fix

1. Same detection as above, but review judges the gap is small/obvious (see guardrail).
2. Make the fix in review's OWN slot worktree, run `bash scripts/quality-gates.sh`, ship via
   `quickmerge.sh "review-fix: <what + why>" --agent --files '<paths>'` (bundle the plan-checkbox flip in the SAME
   commit if it owns the checkbox — matches the existing "Half 1 + Half 2 same turn" rule everyone else follows).
3. If the task's backlog row already shows `done` (worker's commit landed, checkbox was the only real gap and review is
   now closing it for real) — no `/reopen` call needed, the checkbox commit itself is the fix. If the row was never
   marked done (worker never called `/done`, task still `dispatched`/stuck) — do NOT touch it; that's a live worker's
   task, ping them instead (this capability is for closing a review-discovered gap on an already-claimed-done task,
   never for taking over someone else's in-flight work).

## Testing plan (this session, before shipping to the live review.md)

Do NOT test against the live orchestrator backlog or the shared `live-defi-rollout` branch — this is new,
security-relevant behavior on a role that ~30 live agents boot from continuously. Validate the mechanism in a fully
local sandbox first:

1. Synthesize a "badly done" fixture: a throwaway plan file (NOT under `plans/active/`, so `PlanRegenLoop`/regen never
   ingests it) with a `- [x]` checkbox whose cited evidence is fabricated/insufficient.
2. Walk through the new review.md procedure by hand against the fixture exactly as written (detect → verify evidence
   fails → revert checkbox → note the `/reopen` call that WOULD fire, without hitting the live API).
3. Confirm the checkbox-revert mechanics (file edit + local git commit, not pushed) work correctly and are reversible.
4. Only after that passes: ship the review.md update via `safe-doc-push.sh` to the real repo.

## Todos

- [x] 1. ✅ [DESIGN] P1. Investigate available backlog-mutation APIs for undoing a false-done claim — found
      `POST /api/backlog/{task_id}/reopen` already exists, purpose-built for this exact use case. No new
      orchestrator-side code needed. — read `agent-orchestrator/server/routes/backlog.py:369-433`.
- [x] 2. ✅ [DOC] P1. Author this plan doc capturing scope + guardrails + testing plan (local/human track per operator
      direction this session). — unified-trading-pm (this file).
- [x] 3. ✅ [DOC] P1. Write the concrete review.md additions for Capability 1 (revert false-done) and Capability 2
      (patch small fix) — bash/curl snippets in the same style as the rest of the file, guardrails inline, plus
      frontmatter (`does`/`does_not`) and the two other "never commits code" mentions updated for consistency. —
      unified-trading-pm/agents/review.md (shipped in todo 6).
- [x] 4. ✅ [SCRIPT] P1. Built the synthetic false-done fixture in an isolated scratch git repo (outside the real
      unified-trading-pm tree, never pushed) — a fake plan todo citing a fabricated cloudbuild evidence id. Ran the REAL
      verification command against it (`gcloud builds describe`, same region/project review's evidence-backed-
      completion duty already uses) — returned `NOT_FOUND`, confirming the over-claim. Reverted the checkbox `[x]`→`[ ]`
      with an annotation, committed locally as `review-revert: ...` (sha `962dbed`, scratch repo, not pushed). Mechanics
      confirmed working end-to-end.
- [x] 5. ✅ [SCRIPT] P1. Dry-ran capability 2 against a trivial but REAL gap in the same scratch repo:
      `classify_outage(408)` returned `"unknown"` when done_definition required `"timeout"` — verified failing first
      (`python3` direct call), applied the 2-line fix, re-verified it now passes, then bundled the fix + checkbox
      evidence update into one `review-fix: ...` commit (sha `f31844a`, scratch repo, not pushed) — same
      Half-1+Half-2-same-turn shape a worker follows. The live `POST /api/backlog/{id}/reopen` call itself was verified
      against source (`agent-orchestrator/server/routes/backlog.py:369-433`: 409s cleanly if `dispatched`, else resets
      to `queued` + clears done_* fields) rather than fired against a real task — there's no safe way to synthesize a
      genuine `done` row to reopen without mutating live production state for no benefit.
- [x] 6. ✅ [DOC] P1. Ship the real review.md update via `scripts/dev/safe-doc-push.sh` (docs-only path, same as
      `684dd4f8d0`) — unified-trading-pm@bc03ef55d3 (main change), + follow-up unified-trading-pm@4fec7b5b5c (one stale
      "review agents don't commit" mention in the STEP 0 boot-read paragraph missed on the first pass).
- [ ] [DOC] P2. 7. Run the standard plan-completion check on this doc once 3-6 are done — no archival needed yet (leave
      `active` for a burn-in period so real review-agent usage can be observed before calling this settled).

## Progress Log

- **2026-08-09 (interactive session, slot 3)**: Plan authored. Audit + endpoint discovery done (todos 1-2). Proceeding
  to todo 3 (review.md instructions) then the local sandbox test (todos 4-5) before shipping (todo 6).
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — first audit pass on this doc. Not a RECLASSIFY
  candidate despite items 3-7 looking individually bounded: the doc's own summary and Testing-plan section explicitly
  state this is "operator direction 2026-08-09, local/human track, not AO-dispatched" and describe the work as "new,
  security-relevant behavior on a role that ~30 live agents boot from continuously," requiring local-sandbox validation
  before shipping to the live `review.md`. Explicit operator scoping overrides the individual items' apparent
  boundedness.
- **2026-08-09 (interactive session, slot 3) — shipped**: All 6 todos done. Sandbox test results: (1) revert path —
  fabricated `Evidence: cloudbuild=fake-build-id-does-not-exist-00000` correctly resolved `NOT_FOUND` via the real
  `gcloud builds describe` command review already uses, checkbox correctly reverted `[x]`→`[ ]` with an annotation,
  committed `review-revert:`-prefixed (scratch sha `962dbed`, never pushed anywhere real); (2) patch path — a
  genuinely-failing `classify_outage(408) == "unknown"` vs. a stated `done_definition` of `"timeout"` was verified
  failing, fixed with a 2-line change, re-verified passing, then bundled fix + evidence update into one
  `review-fix:`-prefixed commit (scratch sha `f31844a`, never pushed). The `/reopen` API call itself was verified
  against source rather than fired live — no safe way to synthesize a real `done` row to reopen without mutating
  production state for no benefit. Shipped review.md: unified-trading-pm@bc03ef55d3 + follow-up @4fec7b5b5c (missed
  stale mention). Leaving this plan `active` for a burn-in period (todo 7) rather than archiving immediately — want to
  see a real review agent exercise this live before calling the design settled.
- **2026-08-09 (interactive session, slot 3) — this todo-3-6 flip took several attempts to actually land**: hit the live
  prek stash-restore silent-revert class twice (this exact edit reverted back to unchanged HEAD while the push script
  reported clean success both times — caught only by independently diffing `git show origin/live-defi- rollout:<path>`,
  never by trusting the script's exit code or `git status`). Root cause + fix already tracked and since fully resolved
  by its actual owner: `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md` (archived 2026-08-09, all 4
  todos done, including the scratchpad-backup SSOT rule this session independently reached for on its own before knowing
  that rule existed). A related-but-distinct facet of the same bug class (safe-doc-push.sh's own retry loop failing to
  restore an intermediate prek patch) was filed separately and has since been resolved + archived
  (`/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`) — not pursued
  further from this session. On top of that: a REAL 3-way git-stash conflict (not just the silent-revert class) landed
  literal open/close/base/ divider conflict-marker lines into this very file mid-session, against a concurrent
  `na-eligibility-audit` entry from another session — caught by `scripts/plan-hygiene/check_conflict_markers.sh` (which
  scans the WHOLE `plans/active/` corpus on disk when run with no explicit file args, so a conflict-marker failure is
  not necessarily about the file you're committing) and hand-resolved, preserving both sides. Content preserved via a
  session-scratchpad backup between attempts per exactly the scratchpad-backup rule referenced above. Final landing
  succeeded once branch contention settled.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — explicit dated operator-ruling
  citation ('operator direction 2026-08-09, local/human track, not AO-dispatched') on a doc adding new write capability
  to the review role — a role ~30 live agents boot from continuously. Never re-litigate hard rule applies directly;
  round9 (same day as authoring) already reached this verdict.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:6d60dfbea309fdbf]: KEEP-NA, valid — explicit dated operator direction ('local/human track, not AO-dispatched') on new write-capability behavior for the review role; sole remaining item is a deliberate burn-in observation gate.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
