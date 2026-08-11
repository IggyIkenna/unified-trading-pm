---
doc_type: codex-ssot
title: Plan Completion + Archival Discipline
summary:
  SSOT for two recurring observed failures — (1) a plan whose every todo is checked stays active indefinitely instead of
  being archived immediately, polluting the active corpus (part of why `/ag-closeout-audit`, `/plan-vintage-audit`, and
  `/na-eligibility-audit` exist); (2) a follow-up/deferred action gets written as PROSE (a "next steps" note, a Progress
  Log aside, a chat summary) instead of a canonical `- [ ]` todo, invisible to every mechanical hygiene/backlog check.
  States the archive-immediately rule + the 6-step ritual, and the todos-not-prose rule.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, orchestrator, frontmatter]
related:
  [
    /codex/12-agent-workflow/plan-hygiene.md,
    /codex/12-agent-workflow/canonical-plan-flow.md,
    /codex/12-agent-workflow/pre-task-plan-conflict-check.md,
    plans/PLAN_FORMAT.md,
  ]
created: 2026-07-28
authoritative_for: [plan archival-when-done ritual, todos-not-prose rule]
referenced_by: [CLAUDE.md § "Plans — format + authoring discipline"]
owner:
last_reviewed:
code_refs:
---

# Plan Completion + Archival Discipline

> Operator observation 2026-07-28 (Ikenna): both of the failures below are "happening a lot" — this doc exists so they
> stop being separately re-discovered per plan.

## 1. Archive the moment a plan is genuinely done — don't leave it sitting `active`

A plan with every top-level todo `[x]` and no `locked_by` is DONE. It must be archived in the SAME session/turn that
completes its last todo — not left for a later audit pass to notice. This is precisely the gap `/ag-closeout-audit`,
`/plan-vintage-audit`, and `/na-eligibility-audit` all have to repeatedly clean up; each one existing is evidence this
rule wasn't followed at completion time.

**Locked plans are the one exception, and it's a human-only unlock**: `locked_by:` blocks archival even with all todos
done (see `plans/PLAN_FORMAT.md` § "Plan Locking" for the frontmatter fields and the plan-health-agent's
done/unlocked/no-dependents check). Agents MAY ask a human to unlock a genuinely-complete locked plan ("Plan X is locked
but all todos are done — should I unlock it?") but MUST NEVER unlock autonomously.

**The 6-step archival ritual** (every step required, none optional):

1. Migrate any DEFERRED item into a real tracked `- [ ]` todo somewhere (never let a deferral evaporate with the
   archived plan — see § 2 below on why a prose deferral is itself already a defect).
2. Add the archived-banner + `superseded_by`/pointer per this workspace's archival convention.
3. Run a codex-alignment check — does this plan's completion change or newly establish any contract a codex SSOT should
   reflect? Update the codex doc(s), or stub a new one, before the plan disappears from `plans/active/`.
4. Update `CLAUDE.md`/codex on any genuinely new contract the plan shipped (not just "it happened," but "here's the rule
   going forward").
5. **Update every referrer's path corpus-wide** — grep the whole corpus for the old doc's path and fix each hit (added
   2026-07-23: the prior four steps never actually named this explicitly, so a plan could archive cleanly by its own 4
   steps while every OTHER doc that linked to it silently broke — not a regression to fix, a gap that was simply missing
   from the ritual until then). **If a referrer cites a specific fact or number from the doc being archived (not just
   its path), confirm that fact already lives in a codex SSOT before the archive lands — migrate it there if it doesn't.
   Never just repoint the citation at the archived plan itself**, which quietly turns a plan into the fact's only home
   (near-miss 2026-07-28: a CLAUDE.md bullet citing specific cron-delivery measurements almost got repointed at an
   archived plan instead of confirming the numbers were already recorded in `/codex/04-architecture/ci-alerting.md`,
   where they were).
6. Clear the lock (if one existed) and confirm the move — the doc should now live under `plans/archive/<YYYY_MM>/`, not
   `plans/active/`.

`run_hygiene_sweep.sh` + `regenerate_active_plan_inventory.py` catch a stale-active-but-fully-checked plan on their own
cadence, but that is the SAME "caught later, not at completion time" pattern this doc exists to stop relying on.

### The archival commit itself must not drop the rename's delete side (RULED 2026-08-08)

`git commit --only -m "<msg>" -- <new-path>` after a `git mv` commits the ADD side of the rename but silently **excludes
the DELETE side** — a partial commit builds its temp index from HEAD + staged changes to only the listed paths, so the
deletion at the old path never lands in the commit. The old-path file stays gone from the working tree and the deletion
stays staged in the index, but nothing downstream notices: the result is a **create-only commit** that leaves a live
duplicate at the old `plans/active/...` path, which the rest of the fleet (including the AO dispatch backlog, derived
from `plans/active/**` todos) still reads as open/unresolved. The two copies then diverge on the next unrelated edit to
either one. Root-caused and reproduced prek-independently in
`/plans/archive/issues/git_commit_only_drops_rename_deletions_create_only_archive_2026_08_06.md` (5 live diverged
duplicate pairs found and reconciled from this exact mechanism).

**Step 6 of the ritual above ("`git mv` ... confirm the move") MUST use one of these two commit shapes** — never a bare
`git commit --only -- <new-path>` naming only the destination:

1. **Preferred**: route the commit through `scripts/dev/safe-doc-push.sh` — a plain, full-staged-set `git commit` (no
   `--only` path-scoping), which always lands both sides of the rename correctly. **Isolation caveat (2026-08-10):**
   `safe-doc-push.sh`'s isolated-worktree mode (default on `laptop`, gated by `_sdp_isolation_default`) builds its
   commit in a private worktree and populates it by **copying** each `--files` entry from the caller tree. Before the
   fix at `unified-trading-pm@18ae9a4312`, a deleted file (the old side of a `git mv`) had nothing to copy and was
   silently skipped — the commit landed create-only, leaving a live duplicate at the old `plans/active/` path. That fix
   now propagates deletions: when a named file is absent from the caller tree but present at `origin/$BRANCH`, it is
   `rm`'d from the isolated worktree so `git add` stages the deletion. **If you are on a checkout that predates the fix,
   set `SDP_ISOLATED=0`** to use the shared-index fallback for any archival commit that includes a rename. Full
   incident: `/plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md`.
2. If a bare `git commit --only` is genuinely needed (e.g. staging alongside unrelated in-flight WIP you don't want to
   commit yet), the `--only` path list MUST name **both** the old and new paths:
   `git commit --only -m "<msg>" -- plans/active/issues/<slug>.md plans/archive/issues/<slug>.md`.

**Then verify before moving on**: run `git status --porcelain` immediately after the archival commit and confirm it
shows no staged deletion left at the old path — a lingering `D` entry there means the commit just repeated the
create-only hazard and must be fixed (amend, or a corrective follow-up commit) before the archival counts as done.
`scripts/plan-hygiene/check_create_only_archive_commits.py` (wired into `run_hygiene_sweep.sh`) is the mechanical
backstop that catches this shape if it slips through — but don't rely on the sweep catching it later; verify at commit
time.

### Never combine the checkbox flip with the `git mv` archival in ONE commit — CROSS-REPO (mode 2) only (2026-07-30 incident; migrated here 2026-08-09; narrowed 2026-08-10)

**This rule applies ONLY to the cross-repo (mode-2) case** — the plan-of-record lives in the sibling PM worktree
(`.tabs/<N>/unified-trading-pm/`) while the worker commits code in a service-repo worktree, so the flip lands as a
cross-repo PM commit. If a todo's own completion there also makes its doc archival-eligible (all todos done, no lock), a
single commit that both edits the checkbox AND `git mv`s the file to `plans/archive/...` makes the diff AT THE ORIGINAL
`plan_ref` PATH show only a file deletion — no `[ ] → [x]` transition is visible there (git's rename pairing isn't
applied when a path-scoped `git show`/`git log` query is run against just the old path), so `/done`'s M3 check
(`cross_repo_pm_flip_verified`) rejects it with `cross_repo_pm_file_touched_no_checkbox_flip` even though the flip
genuinely happened. **Fix: commit the flip FIRST as a plain edit at the still-active path, THEN `git mv` to the archive
location as a separate follow-up commit.** This is a distinct, earlier failure mode from the `git commit --only`
rename-deletion hazard above (that section's guidance governs the SHAPE of the archival commit once you're doing steps
5-6 as a combined move; this rule governs whether the flip and the move should even be in the same commit at all — they
should not be, in the cross-repo case).

**Single-repo (mode-1) finalize plans: same-commit flip+archival is the SANCTIONED path (narrowed 2026-08-10).** When
the plan-of-record lives directly inside the worker's own worktree (e.g. a worker whose worktree IS
`unified-trading-pm/`), a single commit that flips the last todo AND `git mv`s the doc to `plans/archive/<YYYY_MM>/` is
now the compliant, hook-satisfying shape:

- `check_archive_candidates.sh --only` DEMANDS it: a flip-only commit that leaves the doc 0-open/some-done/unlocked/
  not-exempt is rejected, while the combined commit passes (the old-path deletion is skipped, the archive-path add is
  out of scope).
- The AO `/done` M3 check resolves it: `_flips_at_path_or_rename`/`_resolve_current_plan_text`, and for the
  annotated-line shape `_archival_rename_disposition`, accept the bundled flip+mv with
  `reason="plan_ref_self_archived_with_marker"` — the 2026-07-30 combined-commit M3 gap is closed for this case.
  Verified live 2026-08-10 via a direct `verify.check_plan_flip` trial (slot 17, scratch-repo simulation —
  `_archival_rename_disposition` returns True on a same-commit flip+`git mv`) + the existing regression test
  (`agent-orchestrator/tests/test_done_gate_plan_flip_hard_reject.py:: test_done_accepts_cross_repo_self_archived_with_annotated_checked_line`
  — exercises the same `_archival_rename_disposition` → `plan_ref_self_archived_with_marker` path, confirmed PASSING
  2026-08-10).

So: do NOT reach for the `archive_exempt: true` bridge (next section) on a single-repo finalize plan — the combined
commit is the correct shape. The bridge remains the sanctioned path for the mode-2 (cross-repo) two-commit split.

### `archive_exempt: true` is the sanctioned bridge when a doc's own last todo IS its archival trigger (RULED 2026-08-09; scoped to the cross-repo two-commit case 2026-08-10)

> **Scope note (2026-08-10):** this bridge serves the **cross-repo (mode-2)** two-commit split above. For a
> **single-repo (mode-1) finalize plan** — plan-of-record in the worker's own worktree — the combined same-commit
> flip+archival (previous section) is now the sanctioned shape and the bridge is NOT needed there.

The two-commit split above conflicts with `check_archive_candidates.sh`'s `--only` precommit mode (added 2026-08-09):
that mode unconditionally flags ANY staged `plans/active/*.md` doc that reaches 0 open todos + some done + unlocked +
not `archive_exempt`, regardless of whether THIS commit is what brought it there. For a cross-repo doc whose own LAST
open todo is its own archival trigger, that leaves no legal single commit — the flip-only commit (correct per the rule
above) trips `--only`'s immediate-archival demand, but doing the `git mv` in that same commit is exactly the banned
combination. Found live 2026-08-09 archiving `sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize.md` — see
`/plans/archive/2026_08/issues/check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md`.

**Fix: set `archive_exempt: true` in frontmatter on the flip-only commit, then drop it as part of the immediately
following `git mv` archival commit.** No new mechanism — `--only` mode already treats `archive_exempt: true` as a skip
(the same field § 1's `locked_by`/`gate_on_depends` neighbours use for a different false-positive class); this just
names the field as the sanctioned bridge for this specific two-commit shape so future agents don't have to re-derive the
workaround. The field is moot once the doc is archived (an archived doc is outside `--only`'s scanned population
entirely), so drop it as routine hygiene in the archival commit rather than leaving a dead frontmatter line behind. If
the follow-up `git mv` is ever forgotten, the doc is still caught — just not at commit time: the corpus-wide baseline /
`--diff-base` modes (run in the full `quality-gates.sh`, the daily hygiene cron, and the LDR→main promote gate) re-scan
and flag it as a NEW candidate above baseline the next time either runs. Regression coverage:
`tests/test_check_archive_candidates_flip_then_mv.bats`.

### The line-cap does NOT block archival of an already-done doc (RULED 2026-07-30)

**A doc with ZERO open todos archives via the normal 6-step ritual regardless of how far over the line-cap it is.**
`check_line_caps.sh`'s two-tier cap (plans 500 soft / 1000 hard; epics 2000 hard) exists to stop a LIVE plan growing
into an unreadable hub — it has no purpose on a doc whose work is finished and which is on its way out of
`plans/active/` entirely. Archiving it is the very thing that removes it from the capped corpus.

**The failure this closes**: on 2026-07-30 the gate refused a completion marker on a 1509-line, zero-open-todo doc. The
practical consequence is the exact opposite of what the cap is for — the doc stays `active`, so every `/plan-reconcile`,
`/ag-closeout-audit` and `/na-eligibility-audit` run re-reads all 1509 lines of it, forever, to re-derive the same "yes,
this is done" verdict. A cap meant to reduce read cost was instead permanently maximising it.

Mechanics: the cap fires in `check_line_caps.sh`'s SCOPED mode (the prek hook, called with the staged file list), which
by design has no baseline and refuses any staged over-cap file. Two things keep this exception honest rather than a
loophole:

- **It is gated on ZERO OPEN TODOS, verified — not on "looks done".** Every `- [ ]` must be genuinely closed against the
  `/plan-reconcile` Phase-2 HARD-evidence bar first. A doc with even one open todo is a live plan and the cap applies
  normally: split it, or fold the remnant (see `/plan-reconcile`'s near-complete-plan handling).
- **The commit must be the archival move itself** (the `git mv` into `plans/archive/<YYYY_MM>/` plus the 6 ritual
  steps), not a content edit that happens to leave the over-cap doc sitting in `plans/active/`. Once archived, the doc
  is outside the checked globs (`plans/active/*.md` + `plans/epics/*.md`) and the question is moot — `nature: record`
  archive docs are unbounded by design, which the script already documents for the neighbouring
  extract-history-into-archive case.
- Practically: if the hook still blocks the staged move, that is the gate mis-scoping an archive-bound path (the same
  class it already special-cases at `check_line_caps.sh`'s `plans/active/`+`plans/epics/` path filter) — fix the
  scoping, do not shrink a finished doc to appease it, and never delete content from a done plan just to get under a
  cap.

### The line-cap does NOT block a small audit-marker append to a live over-cap doc (RULED 2026-08-02)

**A commit whose diff to an already-over-cap `plans/active/*.md` is confined to appending a small dated audit verdict
marker (and/or a `last_updated` bump) passes through SCOPED mode.** The carve-out is narrow — it cannot be used to add
real content to an over-cap plan:

- The file must **already** be over the hard cap before this commit (a doc newly crossing the cap is NOT covered — that
  is a real regression, blocked as before).
- **Zero deleted lines**: a marker-only append has `DELETED=0` in `git diff --numstat`. Any edit (modify, reformat,
  remove) that produces deletions is treated as real content change and the cap applies normally.
- **≤ 10 added lines**: a dated Progress Log / verdict marker fits in 3-8 lines; a 10+ line addition is not a marker.
- **No added checkbox lines**: none of the added lines match `- [ ]` or `- [x]`. This ensures the carve-out cannot sneak
  new tracked work onto an over-cap doc.

**The failure this closes**: once a live plan with open todos crosses 1000 L, EVERY future commit to it — including a
4-line `na-eligibility-audit` verdict marker with zero content change — was permanently blocked, forcing every future
audit run to skip writing its incremental-skip anchor onto the largest, most expensive-to-re-read docs in the corpus.
The 2026-07-30 zero-open-todo ruling did not reach this case because the live-plan exception is different: the doc is
not archival-eligible, so blocking archival is moot, but blocking the audit marker still defeats incremental mode.

**Caution: mandatory prettier reformatting can defeat this exception.** If the file carries pre-existing long-whitespace
formatting debt, `prettier-autostage`'s unconditional `--write` pass (triggered by any staged touch) may reflow those
regions as a side effect, adding deletions to an otherwise marker-only diff and pushing `DELETED` above zero. When this
happens the exception correctly refuses (a reformatting diff is not a marker-only append) — the actual fix is to land a
standalone formatting commit on the file first, bringing it to prettier-clean, before adding the marker.

### The line-cap does NOT block a bounded same-line link-repoint on a live over-cap doc (RULED 2026-08-09)

**A commit whose diff to an already-over-cap `plans/active/*.md` is confined to repointing a dangling reference (e.g. a
`/plans/active/...` path that moved to `/plans/archive/<YYYY_MM>/...`) passes through SCOPED mode**, alongside the
marker-append carve-out above — same motivating problem (an over-cap doc gets permanently frozen against even a trivial,
necessary fix), different shape of edit. Bounded the same way, via `check_line_caps.sh`'s SCOPED-mode diff inspection:

- The file must **already** be over the hard cap before this commit (a doc newly crossing the cap is NOT covered).
- **`ADDED <= DELETED`** in `git diff --numstat` — a link-repoint replaces text, it does not grow the doc.
- **Every changed (+/-) content line is textually identical between the removed and added sides, after normalizing an
  `/plans/active/...` or `/plans/archive/<YYYY_MM>/...` path segment to a common token** — this is what distinguishes a
  pure path-token substitution from a sneaky content edit riding along with it (verified against 2 negative cases: a
  same-line prose addition alongside the path fix, and a file newly crossing the cap in the same commit — both still
  correctly fail HARD).

**The failure this closes**: `cross_cutting_consolidated_closeout_2026_07_25.md` (then 1007L, over cap) needed a single
dangling-link repoint to unblock a downstream archival — SCOPED mode refused it, deadlocking against the archival
discipline's own referrer-fixup requirement (a stale ref must be fixed before the target can safely archive). Full
incident + the shipped fix (`unified-trading-pm@d765b4cfb1`, `scripts/plan-hygiene/check_line_caps.sh`):
`/plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`. Regression coverage:
verified via an isolated scratch repo, not the live corpus.

### The line-cap does NOT block a bounded non-growing content substitution on a live over-cap doc (RULED 2026-08-11)

**A commit whose diff to an already-over-cap `plans/active/*.md` is a bounded, non-growing content subtraction
(`ADDED<=DELETED`, `DELETED>=1`, `ADDED>=1`) that mutates NO checkbox lines passes through SCOPED mode**, alongside the
marker-append and link-repoint carve-outs above — same motivating problem (an over-cap doc gets permanently frozen
against even a routine accuracy fix), different shape of edit. Bounded the same way, via `check_line_caps.sh`'s
SCOPED-mode diff inspection:

- The file must **already** be over the hard cap before this commit (automatically implied: `ADDED<=DELETED` means the
  pre-commit line count `lines-ADDED+DELETED >= lines > 1000` — same reasoning as the link-repoint branch, no separate
  `PRE_COMMIT_LINES` check needed).
- **`DELETED >= 1` AND `ADDED >= 1`** — a real substitution, not the marker-append case (which requires `DELETED=0`) and
  not a pure deletion.
- **`ADDED <= DELETED`** in `git diff --numstat` — the substitution does not grow the doc.
- **No added or removed line matches a checkbox pattern** (`- [ ]` or `- [x]`) — as diffed, both sides checked. The
  tracked-work set (`todos=`) is never mutated, so this carve-out cannot be used to sneak new work onto or silently drop
  pre-existing tracked work from an over-cap doc.

**Why this is a separate carve-out from the link-repoint carve-out**: the link-repoint carve-out requires every changed
line's content to be textually identical after normalizing a `plans/active/...` ↔ `plans/archive/<YYYY_MM>/...` path
token — a pure path-token substitution. That cannot express a line whose actual content genuinely changes (e.g.
correcting a stale MVP-cell table row with accurate manifest count data, the real-world case that drove this).

**The failure this closes**: `tradfi_consolidated_closeout_2026_07_18.md`'s "S&P index options" MVP-cell row carried
stale text ("66% attempted_failed... not yet launched") even after the doc had been split below cap. A net-zero-line
table-cell accuracy update (substituting corrected text within the same row) would have been permanently blocked under
the two prior carve-outs because neither expressed "same-line content substitution, not path-repoint." Full incident +
fix (`unified-trading-pm@<this-sha>`, `scripts/plan-hygiene/check_line_caps.sh`):
`/plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md`. Regression
coverage: `tests/test_check_line_caps_marker_carveout.bats` net-zero-substitution tests.

## 2. Every follow-up is a canonical `- [ ]` todo — never prose

A "next steps" paragraph, a Progress Log aside that only describes future work in prose, or a chat-summary bullet that
mentions something still to do — none of these are visible to `check_todo_format.sh`, `regen_backlog_from_plan.py`, or
any orphan/hygiene audit. They are invisible follow-ups: real intent that silently never becomes trackable work.

**The rule**: the moment you notice a follow-up/deferred action — while executing a todo, reviewing a plan, or wrapping
a session — write it as a real `- [ ]` [TAG] P<n>. todo in the plan it belongs to (or a new
`plans/active/issues/<slug>_<date>.md` if it fits no existing plan), in the same turn you noticed it. Do not write it as
prose "for later," do not put it only in a chat response, and do not write it to agent memory (memory writes are
separately banned entirely, per `CLAUDE.md`'s memory rules). If you catch yourself typing "we should also…" or "a
follow-up would be…" in prose, stop and add the real todo instead of finishing the sentence.

This is the same principle `plans/active/task_template.md` §3 already states for capturing discoveries mid-plan
("Capture discoveries as plan todos immediately… never auto-memory/chat-summary; every deferral in a summary must
already be a `- [ ]` todo") — this doc exists because that rule, while written down, keeps not being followed in
practice, so it's restated here as its own named failure mode alongside archival, not left as one clause buried in a
plan-authoring template.
