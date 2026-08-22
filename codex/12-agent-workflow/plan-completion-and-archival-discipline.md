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
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md,
    /plans/active/issues/plan_reconciler_findings_prediction_2026_08_16.md,
  ]
created: 2026-07-28
authoritative_for: [plan archival-when-done ritual, todos-not-prose rule, finalize-plan no-double-gate rule]
referenced_by: [CLAUDE.md § "Plans — format + authoring discipline"]
owner:
last_reviewed: 2026-08-21
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
5. **Archiving a plan means its durable content moves to codex — never just moves to `plans/archive/` and stays there
   as the only home for what it knows** (sharpened 2026-08-17, generalizing the 2026-07-23/2026-07-28 versions of this
   step below). The rule, stated plainly: **if you archive a plan, its information goes into codex.** Concretely, before
   the `git mv` lands:
   - Identify what this plan established that another doc (a still-active plan, or a future reader) would need —
     a ruling, a measured number, a design decision, a recipe. If it's not ALREADY captured in a codex SSOT, write it
     there now (a new doc, or a section in an existing one). This is the SAME step 3/4 codex-alignment check above,
     restated as a hard precondition for step 6, not an optional follow-up.
   - **Grep the whole corpus for the old doc's path and fix every hit** — but the fix is "repoint at the codex doc you
     just wrote/confirmed," never "repoint at the archived plan itself." A referrer that still points at
     `plans/archive/...` after this step is exactly the failure this rule exists to close: it quietly turns an archived
     plan into a fact's only remaining home, invisible to anyone who doesn't already know to look in `plans/archive/`.
   - This is not extra ceremony for its own sake — it's a forcing function. You cannot archive cleanly without touching
     codex, which means archival becomes a recurring, low-friction trigger to keep codex actually current instead of
     letting it rot while plans silently accumulate the fleet's real institutional knowledge instead.
   - **You should still archive** — this rule is never a reason to leave a genuinely-done plan sitting `active`. Fix the
     referrers as part of the SAME archival work, don't let "I'd have to update other docs" become an excuse to skip
     § 1's archive-immediately rule.

   **Mechanically enforced, not just prose**: `scripts/plan-hygiene/check_active_refs_archived_plans.py` (a shrinking
   ratchet, wired `--only`-scoped into `quality-gates.sh` at zero added cost on a push that doesn't touch the doc trees)
   fails a commit whose OWN `related:` frontmatter cites a `/plans/archive/...` path. It does not scan document PROSE —
   citing an archived plan as historical evidence ("root-caused in `plans/archive/issues/<slug>.md`") is the CORRECT
   end-state this rule produces once a fact has been migrated to codex citing its source, not a violation; the ratchet
   targets the structural `related:` pointer specifically, the one meant to route a reader to current context. Seeded
   2026-08-17 at 925 pre-existing hits (the corpus predates this rule by months) — see
   `/plans/active/issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` for the dispatched bulk-cleanup
   effort working that baseline down; `--update-baseline` lowers it as each batch lands, never hand-raise it.

   (Prior near-miss this generalizes, kept for context: 2026-07-28, a CLAUDE.md bullet citing specific cron-delivery
   measurements almost got repointed at an archived plan instead of confirming the numbers were already recorded in
   `/codex/04-architecture/ci-alerting.md`, where they were.)

6. Clear the lock (if one existed) and confirm the move. **The destination path depends on `doc_type` (resolved
   2026-08-16 — this doc previously contradicted itself, using both forms in its own worked examples below;
   [`archive_path_convention_dated_subfolder_vs_flat_issues_contradiction_2026_08_16.md`](/plans/archive/issues/archive_path_convention_dated_subfolder_vs_flat_issues_contradiction_2026_08_16.md) has the full corpus
   measurement — 1484 issue docs already at flat `plans/archive/issues/` vs 296 at the dated form, ~83%/17%)**: a
   `doc_type: issue` doc moves to flat **`plans/archive/issues/`**, per
   [`issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md) — the authoritative, internally
   consistent SSOT for issue-doc archival path, stated unambiguously in its state-machine table. Every other
   `doc_type` (`plan`, epic finalize docs, etc.) moves to the dated **`plans/archive/<YYYY_MM>/`** shown throughout
   the rest of this section. Either way, not `plans/active/`.

`run_hygiene_sweep.sh` + `regenerate_active_plan_inventory.py` catch a stale-active-but-fully-checked plan on their own
cadence, but that is the SAME "caught later, not at completion time" pattern this doc exists to stop relying on.

### No-double-gate: a finalize plan ships `status: active` from the start (RULED 2026-07-30)

**A finalize plan — the `depends_on: [<batch>]` + `gate_on_depends: true` companion every AO-dispatched plan requires
(`plans/active/task_template.md` §4, "Every AO-dispatched plan needs a gated finalize plan") — is authored
`status: active` immediately, never `status: draft`.** `gate_on_depends: true` already machine-holds every one of its
tasks until the upstream batch plan's own todos are `done` (`_wire_gate_on_depends_prereqs` in
`regen_backlog_from_plan.py` covers both an already-`active` upstream, via `prereqs.completed_tasks`, and a
still-`draft` upstream, via a derived `gate-upstream-open:<stem>` condition read off the upstream file directly) — so a
finalize plan genuinely cannot dispatch early regardless of its own `status`. Stacking `status: draft` on top of that
machine gate creates a SECOND gate guarding the identical release condition, and unlike `gate_on_depends` it has no
automatic release: someone has to notice the upstream is done and manually flip `draft`→`active`, and nothing prompts
that flip.

**The failure this closes**: a 2026-07-30 corpus audit found 46 finalize plans stuck in `status: draft` this way, most
with their upstream batch plan already `done` and even archived weeks earlier — the manual flip was never made, so the
reconciliation/archival work the finalize plan exists to perform sat invisible to the AO backlog indefinitely. Shipped
in `unified-trading-pm@233ebd6148` ("remove redundant status:draft double-gate on finalize plans"): flipped the 43
AO-track (`assigned_vm: planning`) finalize plans found stuck in `draft` to `active` (2 `assigned_vm: NA` docs were left
untouched — NA plans aren't AO-ingested regardless of `status`, so the bug doesn't reach them); updated
`cursor-configs/skills/ag-closeout-audit/SKILL.md` to stop instructing `status: draft` on the finalize-plan sibling
(only the batch plan itself — genuinely unreviewed content — still needs `draft` + explicit operator approval); and
added `scripts/quality_gates/check_finalize_plan_coverage.py`'s ratcheted `draft_gate_violation_count` check so this
authoring mistake can't silently regress.

**The general "no-double-gate" rule, beyond finalize plans specifically**: once a plan/todo is already held by a
genuine MACHINE gate — `gate_on_depends: true` (cross-plan), `sequential: true` (intra-plan), or a documented
prerequisite condition read by the dispatcher — do not also add a second, manual gate (`status: draft`, a prose "🔴
BLOCKED, don't dispatch" banner) guarding the exact same release condition. A second manual gate stacked on a working
machine gate adds no additional safety, but does add a step a human/agent must remember to perform once the real gate
clears — and at fleet scale that step reliably gets forgotten (see the 46-plan measurement above). If two independent
conditions genuinely must both clear before dispatch, encode BOTH as real machine gates (e.g. two `depends_on`
entries, or a `gate_on_depends` plus a separately-tracked prerequisite condition) rather than one machine gate plus one
manual one.

**Worked example — the exact gap this section closes.** `/plan-reconcile`'s prediction-tranche sweep
(`/plans/active/issues/plan_reconciler_findings_prediction_2026_08_16.md`, P2 item) found that both
`/plans/active/data_pipeline_check_mdps_features_2026_07_20.md` and its finalize doc,
`/plans/active/data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md`, independently cited "the
2026-07-30 ruling that finalize plans ship `status: active` from the start" as settled convention — correctly, and in
agreement with actual fleet-wide practice (see any batch8/9/10-era finalize plan for the same pattern) — yet a
corpus-wide `codex/` grep turned up zero hits for the rule anywhere. Genuine codex gap, not staleness: this section is
the missing SSOT the two plans were already, correctly, assuming existed.

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
   incident: `/plans/archive/2026_08/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md` (archived
   2026-08-18, fully resolved). **Recurrence caught
   live 2026-08-14**: CLAUDE.md's general ship rule ("scope `--files` by name") pulls against this section's "no
   `--only` path-scoping" preference — an agent following the general habit passed `--files` naming ONLY the NEW archive
   path (the one that exists on disk after `git mv`), never the OLD active path. "Named" above means _listed in
   `--files`_, not merely known-to-exist: the deletion-propagation check only fires for a path actually passed, so
   omitting the old path silently reproduces the exact create-only duplicate this fix was meant to close — caught only
   by diffing origin's tree object for both paths after push, not by the script's own exit code. **If you scope
   `--files` for an archival `git mv`, name BOTH the old and new paths every time** (or drop scoping entirely per this
   section's original preference).
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
`unified-trading-pm/`), a single commit that flips the last todo AND `git mv`s the doc to `plans/archive/<YYYY_MM>/`
(this section covers `doc_type: plan` finalize docs — an issue doc uses flat `plans/archive/issues/` instead, per step
6 above) is now the compliant, hook-satisfying shape:

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
`/plans/archive/2026_08/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`. Regression
coverage: verified via an isolated scratch repo, not the live corpus.

### `locked_by: live-defi-rollout` was a hardcoded branch-name placeholder, not a real lock (fixed 2026-08-12/18)

**If a doc's `locked_by:` reads exactly `live-defi-rollout` (the shared branch name, not any registered actor id),
treat it as the now-fixed instance of a corpus-wide bug, not a genuine claim — but it is still a HARD-STOP until
actually cleared: do not unlock it yourself.** Root-caused 2026-08-10: a one-off frontmatter-conformity script
(`scripts/plans/fix_epic_frontmatter_2026_05_21.py:133`) hardcoded this literal string, and the pattern propagated into
96 `plans/active`/`plans/active/issues` docs via a copied doc-creation template between 2026-05-21 and 2026-07-11.
Genuine locks in this corpus always carry a real actor id (`plan_reconciler (agt-xxxxxx) since <ts>`, `harsh-fleet-audit`,
etc.) — `live-defi-rollout` never has. The operator ruled Option B (2026-08-12): a one-off script
(`scripts/plans/clear_locked_by_placeholder_2026_08_12.py`) cleared `locked_by`/`locked_since` on every doc carrying
exactly that value, shipped in 4 batched commits (2026-08-12/18), and the actual writer
(`scripts/cicd/parity_watchdog.py`) was patched the same session to stop stamping it on new docs. **Practical
consequence**: a doc found today still carrying this exact placeholder is either (a) a doc the corpus-wide clear missed
(rare — verify via `git log` whether the clear-script commits post-date the doc's own creation) or (b) a NEW
recurrence, meaning the `parity_watchdog.py` fix regressed — either way it is still `locked_by:`-set and therefore still
a HARD-STOP: an agent finding one MUST ask the operator for a targeted `[unlock-plan]` (as was done 2026-08-10 for
`deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`, the confirmed case that surfaced this bug), never
clear it autonomously just because the value is a known-bogus one. Full investigation + evidence:
`/plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`.

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
