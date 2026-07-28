---
name: plan-vintage-audit
description: >-
  Audit every plans/active/*.md and plans/active/issues/*.md doc CREATED within an operator-given date range/window
  (e.g. "before 2026-06-01", "2026-06", "2026-06-01..2026-06-30") to answer: is each doc's remaining open work already
  done in the codebase but never checked off, superseded by other work, migratable into a NEWER (later-dated) active
  plan with the original then archived, genuinely still active with nothing wrong, or unclear/operator-gated? Runs the
  same canonical-archival discipline as a normal plan close-out (dated archive folder, exact-successor banner, every
  broken corpus referrer fixed) so a vintage sweep never leaves the corpus worse than it found it. Generalizes two
  one-off sessions (a pre-2026-06-01 sweep: 5 real docs + several no-frontmatter legacy directories, mostly clean; a
  2026-06 sweep: 81 docs, only 11 archivable, 52% operator-gated, 3 recurring traps found) into a repeatable,
  date-range-parameterized skill. Trigger on `/plan-vintage-audit <range>`, "audit plans from <month>", "check plans
  created before <date>", "evaluate the <month> plans — are they done or should they be archived/migrated", "what in
  this date range should be done by now", "vintage sweep for <range>".
---

# /plan-vintage-audit — date-window plan/issue closeout sweep

Generalizes two sessions of ad-hoc "everything created before/during X should be done by now — check it" requests into a
repeatable procedure. The two sessions this skill is built from differed enormously in shape — the lesson encoded
throughout is: **don't assume the shape in advance, measure it (Phase 0), then right-size the fan-out.** A window closer
to "now" will skew toward operator-gated/still-active (June 2026: 52% operator-gated, only 11/81 archivable) because
recent work hasn't had time to either ship or get picked up by the corpus's own self-auditing mechanisms yet; an older
window skews toward clean archival (pre-June-2026: nearly everything was either genuinely superseded or a small number
of real stuck items) because more time has passed for things to either ship or visibly rot. Expect the mix, don't force
one template onto both.

## Argument grammar

Accepts, as the `<range>` argument: a bare month (`2026-06` = the whole month), an explicit range
(`2026-06-01..2026-06-30`), or a `before:`/`after:` cutoff (`before:2026-06-01`). No sensible default exists (unlike
`/ag-closeout-audit`'s `all`) — a vintage sweep with no range would mean "everything," which is `/ag-closeout-audit`'s
and `/na-eligibility-audit`'s job, not this skill's; if invoked with no range, ask the operator what window they mean
rather than guessing.

## Phase 0 — scope FIRST, cheaply (no agents yet)

**Count before you design the fan-out.** Grep `created:` frontmatter across `plans/active/*.md` and
`plans/active/issues/*.md` for the range — this single measurement decided everything downstream last time (5 docs → one
Workflow phase with per-doc agents; 81 docs → 12 thematic-group agents). Skipping this and guessing a fan-out shape
wastes agents on either too-thin or too-thick batches.

**Legacy pre-frontmatter docs need git history, not just the `created:` grep.** Some directories predate the frontmatter
convention entirely and carry no `created:` field at all (confirmed hit last time: `plans/active/end-to-end-testing/`,
`plans/cicd/`, `plans/ops/`, `plans/tasks/`, `plans/handover/`). For any directory with zero `created:` hits that still
looks old, get its real creation date via `git log --diff-filter=A --format=%ad -- <path> | tail -1`, and its real
last-touch via `git log -1 --format="%ad %s" --date=short -- <file>` — **read the commit message**, because a directory
can show a suspiciously recent "last touch" that's actually a mechanical corpus-wide sweep (prettier reflow,
reference-path migration, epic-consolidation commit) rather than real content work. A file touched only by 3 different
corpus-wide-sweep commits over 4 months is exactly as stale as one touched zero times — don't let a recent SHA fool you
into "still active."

**Group thematically, not alphabetically or by arbitrary chunk size.** Batch docs by `asset_group`/topic (CeFi venues,
DeFi, sports/predictions, TradFi, data-pipeline/monitoring, manifest/fleet/VM-health, pipeline-mode canonicalisation,
strategy/execution/live, security/deps/CI, PM/plan-hygiene meta, misc) so each classify agent's cross-referencing stays
coherent — an agent auditing 6-8 DeFi docs together can check them against each other and against DeFi successor plans
efficiently; a random alphabetical mix of unrelated docs wastes an agent's context re-deriving domain knowledge per doc
instead of reusing it across the batch. Aim for ~5-9 docs per group; a doc you already know is a huge live coordinator
(a 700+-line in-flight migration catalogue, a determinism-spine plan you edited earlier this session) can go alone or
paired, since it deserves an agent's full attention.

**Check for overlapping recent audits BEFORE re-deriving verdicts from scratch — the single biggest lesson from the June
run.** 42 of 81 June docs had already been independently re-verified in the prior 1-2 days by
`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`, satellite-dispatch batches, or consolidated-closeout plans.
For every doc in scope, grep its own body for a dated audit-verdict marker (`na-eligibility-audit YYYY-MM-DD`, a
`gate_on_depends`/`depends_on` note citing a specific prior audit, a "RE-TRIAGE" section, or a companion
`{stem}_finalize_{date}.md` file already sitting next to it) before spending agent effort re-classifying it — **treat
that marker as authoritative if the doc hasn't changed since**, same incremental-skip logic `/na-eligibility-audit`'s
Phase 0 uses. Re-deriving a verdict a fresher, more-informed pass already reached is wasted work and risks silently
contradicting it.

## Phase 1 — per-group classification (the real work)

Fan out read-only classify agents (Workflow tool, one per thematic group from Phase 0; paste
`cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of every spawn; set `model=` explicitly). Each agent reads
every doc in its group END TO END — never a checkbox count alone. For every open `- [ ]` todo: grep the actual codebase
/ other plans for evidence it shipped, was superseded, or is genuinely still pending; check for a natural later-dated
successor plan before concluding "still active"; flag operator-gated blockers explicitly; flag anything genuinely
ambiguous as `unclear` rather than guessing.

**Five verdicts, not three** — the June run's schema, richer than a plain done/superseded/active split because
"partially done" is common enough to need its own bucket:

1. **genuinely-still-active** — real, unfinished, un-superseded work. No action.
2. **fully-done-needs-archive** — every open item demonstrably shipped/superseded. Archive now.
3. **superseded-needs-archive** — the doc's whole remaining scope was absorbed elsewhere. Archive now, name the
   absorber.
4. **migrate-to-newer-plan-then-archive** — a specific later-dated plan already covers (or should cover) the remainder;
   name the EXACT target doc + section, confirm the specific todo text is actually present there (not just "a
   similar-sounding plan exists" — that's the false-citation trap below), then archive the source.
5. **partially-done-rehome-remainder** — some phases/items shipped or migrated, but a genuine remainder needs either a
   named home or explicit operator scoping before it can move anywhere. Do NOT archive the whole doc; only the
   done/migrated portion closes.
6. **unclear** — genuinely ambiguous; say what would resolve it.

**Strict archival bar, unchanged from the prior pre-June sweep**: only recommend archiving a specific item if it is
demonstrably done or superseded — cite the commit SHA, the specific successor doc's line/section, or the specific code
state checked. A blind "this looks old, archive it" is not a verdict this skill accepts.

**Three recurring traps to explicitly hunt for in every batch** (all three showed up repeatedly in the June run and
would each independently produce a wrong verdict if missed):

- **(a) Checked-done-but-never-flipped checkboxes** — the work shipped in code; the doc's `- [ ]` was simply never
  ticked. Confirm via a direct grep/read of the cited module, don't take the unchecked box at face value in either
  direction.
- **(b) Zero-unchecked-boxes hiding real open work in PROSE form** — a doc can show 0 remaining `- [ ]` items by
  checkbox count and still carry live, undone work described only in prose (a "Deferred" section, a dated correction
  note, a still-open design question in running text). Read the full body; a checkbox count of zero is not proof of
  closure.
- **(c) Stale cross-references propagating FALSE closure into downstream indexes** — worse than (a)/(b) because it
  compounds: a doc with real prose-form open work gets miscounted by one aggregating index as "0 open todos/closed," and
  that false citation then propagates into MULTIPLE downstream consolidated-closeout plans (the June run found one doc
  falsely cited as closed by **four separate** AG closeout plans simultaneously). This is a **big finding** under
  CLAUDE.md's findings-triage HARD RULE (SSOT-contradiction-adjacent, cross-plan) — flag it to the operator explicitly,
  don't just quietly fix your own copy.

## Phase 2 — execute the confirmed-safe actions

Apply the standard 6-step archival ritual per item (migrate DEFERRED content → banner citing the EXACT successor →
codex-alignment check → update CLAUDE.md/codex pointers on any changed contract → **fix every corpus-wide referrer** →
clear any lock). Specifically:

- **Dated archive folder** (`plans/archive/2026_MM/`) keyed by the ARCHIVAL action's month, not the doc's original
  creation month — this is the corpus's actual convention (confirmed: a May-created doc archived in July lands in
  `2026_07/`, not `2026_05/`). Issue docs go to the flat `plans/archive/issues/` (no dated subfolder). Pre-frontmatter
  legacy docs get the same dated-folder treatment as frontmatter-era ones for consistency going forward, even though
  older archived batches used a flat undated root — that flat root is a historical artifact of pre-convention archival
  sessions, not a pattern to keep extending.
- **Exact-successor banner** on every archived doc — name the specific file, section, and commit SHA where available;
  "superseded" with no citation is not acceptable.
- **Fix every broken referrer** — grep the WHOLE corpus (`plans/`, `codex/`) for the old filename/path before archiving,
  update every hit (including `codex/00-SSOT-INDEX.md`, which is a confirmed common miss — it indexes docs by old paths
  that don't get updated when the target moves). A prek/plan-hygiene hook will catch a broken relative link in
  `plans/active/*.md` referrers at commit time — don't rely on it to catch codex-side misses too; grep both.
- **Locked docs need `[unlock-plan]`** in the commit message — only when the operator has explicitly authorized
  archiving that SPECIFIC doc in this session (never infer consent from "they asked for the general sweep"; a
  `locked_by:` doc needs its own explicit go-ahead, ask if unclear).
- **Migrate-verdict items**: actually add the todo text (with `[TAG] P<n>.` + source citation) to the named target plan
  as a real `- [ ]` checkbox — don't just write "see X" in the archived doc's banner and call it migrated. If the target
  plan doesn't have a natural home for it yet, that's the moment to say so and ask, not to skip the step.
- **Epics are NEVER archived** — `plans/epics/*_SUPERSEDED_*.md` stays in `plans/epics/` forever with its banner, per
  the "everlasting epic" model (`plans/epics/README.md`). Don't "fix" this into `plans/archive/`; it's already the
  documented correct terminal state.
- **New plans created to house rehomed/migrated scope** must pass the same frontmatter schema gate as any other plan —
  `nature` and `assigned_role` are enum-constrained (`python3 scripts/plan-hygiene/fix_frontmatter.py` or the prek
  `plan-hygiene` hook will name the exact allowed values on a mismatch; don't guess a plausible-sounding value).

**`git rm` (actual file deletion) is hard-blocked for autonomous workers by this environment's
`agent-orchestrator/scripts/hooks/block_destructive_commands.py` PreToolUse guardrail — even a single, explicitly-named
file** (confirmed: it is not a recursive-delete-only check). `git mv` (rename/relocate) is NOT blocked. When a doc audit
concludes something should be truly deleted (not archived-with-a-banner — e.g. a confirmed-dead companion script with
zero live references, not a plan/issue doc), the agent cannot do that deletion itself: **relocate what's still useful
via `git mv`, and explicitly ask the operator to run the `git rm`** for anything that should actually disappear. Don't
spend effort finding a clever workaround — the hook's own message says not to, and it's right; that class of action is a
human call in this environment. See `/codex/05-infrastructure/claude-code-settings-symlink.md` for the hook's
registration.

## Phase 3 — commit + ship

PM-repo doc edits; stage by name (never `git add -A` blind — it will pick up unrelated pre-existing untracked files in a
shared workspace, confirmed to happen); mandatory pre-commit `git status && git diff --cached --stat` (no path arg)
before every commit. Run `prek` (via the repo's `.venv-workspace/bin/prek`) and get a clean pass before committing — a
plan/doc-only change needs prek, not a full `quality-gates.sh`. **Expect branch-drift rejections on a live,
multi-agent-populated branch** (`live-defi-rollout` had 3+ concurrent pushes land mid-session last time) —
`git pull --rebase --autostash` and re-stage before every commit/push attempt, in a loop if needed; never
`SKIP_BRANCH_DRIFT=1` (human-only override, explicitly). **`quickmerge.sh` has a known bug with pure-deletion diffs**
(its `--files` path-validation treats "file no longer exists on disk" as invalid input rather than as the deletion
itself being the valid staged change — it will report "Path not found (and not tracked)" for a correctly committed
deletion and refuse to proceed) — for a PM-repo `docs(plans):`/`chore(scripts):` commit already verified clean by
`prek`, the closed direct-push carve-out (CLAUDE.md § Git discipline, carve-out 2) is the reliable path; don't loop on
quickmerge trying to make it accept a deletion-only diff. Commit prefix `docs(plans):` for archival/ migration edits,
`chore(scripts):` for companion-script relocations.

## Phase 4 — operator-gated decisions: investigate BEFORE asking

**Never ask the operator a bare multiple-choice question about something you haven't investigated.** For every
`operator_gated` finding that needs a real decision (not just "flag and move on"), do the legwork FIRST: read the actual
current code/data state, check whether some other decision already superseded this exact question elsewhere in the
corpus (a stale open issue can outlive the fix that already answered it — confirmed twice this session), and work out
the regression risk of each option against what's ALREADY in the codebase/data (which option requires a migration vs
which aligns with the current state as-is). THEN present 2-4 named, evidenced options with a recommendation via
`AskUserQuestion` — a blind ask produces a worse decision than an investigated one, and re-asking after the operator
points out you skipped the legwork costs more turns than doing it once up front. **When the operator revises a decision
mid-turn** (e.g. approves a deletion, then says "actually keep this one, it's still useful for X"), don't just
mechanically comply — relocate the kept item to its correct current-convention home (matching its actual current
siblings) and add whatever header/marker convention that location requires, rather than leaving it stranded in a
directory that's otherwise being emptied out.

## Phase 5 — report

Finish with text (never a `*_SUMMARY.md` file): total docs in window, verdict breakdown (the 6-way split above), what
got archived/migrated/rehomed this pass (with commit SHAs), every `operator_gated` item surfaced (even ones you didn't
action, so nothing silently drops), every `unclear` item and what would resolve it, and any **big finding** (the
propagating-false-closure trap especially) escalated per the findings-triage HARD RULE. Expect the operator-gated
fraction to scale with recency — call this out explicitly rather than let a high operator-gated count read as "the audit
didn't finish."

## Modes

**Interactive** (operator present, the default and only mode built out so far): batch operator-gated decisions into
`AskUserQuestion` calls (max 4 per call) after Phase 4's investigation step; apply provable verdicts without asking.
**Autonomous**: not yet exercised for this skill — if run under `/autonomous`, park every genuine judgment call as
`BLOCKED-OPERATOR-DECISION` in the Phase-5 report rather than pausing, same as the sibling audit skills.

## Codex SSOTs

- `plans/active/task_template.md` — plan-authoring rules any newly-created migration-target plan must satisfy
- `/codex/11-project-management/cross-reference-path-convention.md` — leading-slash, repo-root-relative referrer paths;
  the exact convention Phase 2's link-fixing must produce
- `/codex/12-agent-workflow/commit-push-flip-rule.md` — commit+push+flip discipline this skill's Phase 3 follows
- `/codex/05-infrastructure/per-tab-worktrees.md` — multi-agent branch-drift/rebase handling for Phase 3
- `/codex/05-infrastructure/claude-code-settings-symlink.md` — registers `block_destructive_commands.py`, the guardrail
  behind Phase 2's `git rm`-is-blocked finding
- `/codex/08-workflows/ci-cd-flow.md` — quickmerge / direct-push carve-outs referenced in Phase 3
- `cursor-configs/skills/na-eligibility-audit/SKILL.md` — sibling skill, disjoint population (`assigned_vm: NA` docs
  regardless of date) but the SAME "check for a recent overlapping audit before re-deriving" discipline this skill's
  Phase 0 borrows
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` — sibling skill, disjoint population (orphan detection by AG/topic
  regardless of date), same archival-ritual mechanics
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract + escalation format
