---
doc_type: plan
title: plans-workspace-organization-2026-05-08
summary:
status: complete
nature: record
asset_group: cross-cutting
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: [epics/cross_cutting_may_23_2026]
created: 2026-05-08
plan_type: docs+infra
owner: ikenna
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
overview: 'Workspace-organization sweep covering two related cleanups: (1) extension rename `.plan.md` → `.md` for native markdown-preview support across IDEs (Cursor, VS Code) without losing git history — **scoped to `plans/active/` and `plans/epics/` only** (archive + ai + other dirs left untouched per operator direction 2026-05-08); (2) per-domain epic consolidation where a master plan + a May-23 epic live in the same domain (tradfi_master + sp_prediction_may_23_2026 etc.). Both are doc-only changes; both compose with the 9-master move to plans/epics/ shipped 2026-05-08.'
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
depends_on: []
isProject: false
---

# Plans Workspace Organization — Plan

> **Doc-only sweep.** No code paths change. Touches: every `*.plan.md` filename, ~thousands of cross-references in
> markdown bodies, ~10 governance files (CLAUDE.md / PLAN_FORMAT.md / task_template.md / prompts/ / INDEX.md /
> MEMORY.md), codex docs that reference plans, and workflow YAMLs that reference plan paths. Git history preserved via
> `git mv` (rename detection is content-similarity-based; identical content = 100% match = traced through
> `git log --follow`).

---

## Phase A — `.plan.md` → `.md` extension rename

> **Why.** `.plan.md` is rendered as plain text by most IDEs because the second extension confuses MIME detection.
> Renaming to `.md` lights up native markdown preview in Cursor + VS Code + GitHub web UI without changing rigour or
> style. The format itself stays canonical (frontmatter + Cursor checkboxes + 3-tier readiness).

### A1. Rename mechanics + git history preservation

> **Scope: `plans/active/` + `plans/epics/` only.** `plans/archive/` + `plans/ai/` + any other plan-housing dirs stay on
> `.plan.md` (archived plans are frozen historical state; renaming risks breaking historical references in commit
> messages, codex archaeology, and external links).

todos:

- [ ] [SCRIPT] P0. **Single-commit rename via `git mv` for every `*.plan.md` file in `plans/active/` and
      `plans/epics/`.** Use a script that walks each of the two directories, runs `git mv X.plan.md X.md` per file. All
      renames committed in ONE commit so `git log --follow plans/active/<new>.md` traces cleanly through the boundary.
      **Critical:** the rename itself must NOT modify file content — content modifications belong in subsequent commits,
      otherwise git's similarity heuristic might fall below 100% threshold for some files.

- [ ] [SCRIPT] P0. **Verify every renamed file's history traces back to the .plan.md original**. Smoke check: pick 3
      random renamed files in `plans/active/`, run `git log --follow <new-name>` and assert at least 5 commits show.
      Pick 3 from `plans/epics/` (these were just moved 2026-05-08; history short but should still trace through both
      the move + the rename).

- [ ] [SCRIPT] P0. **Sanity check — no `.plan.md` files left in `plans/active/` or `plans/epics/`**.
      `find plans/active plans/epics -name "*.plan.md"` returns zero hits post-rename. `plans/archive/` + `plans/ai/`
      retain their `.plan.md` files unchanged.

### A2. Cross-reference rewrite (workspace-wide)

todos:

- [ ] [SCRIPT] P0. **Markdown link rewrite across all plans + codex + governance docs**. Pattern: rewrite ONLY
      references to renamed files (those that lived in `plans/active/` or `plans/epics/`). References to
      `plans/archive/X.plan.md` or `plans/ai/X.plan.md` stay unchanged. Build the renamed-file allowlist first (output
      of `git mv` from A1), then sed-rewrite each `[...](path/X.plan.md)` → `[...](path/X.md)` only when X is in the
      allowlist. Workspace scope: `unified-trading-pm/plans/**/*.md` + `unified-trading-pm/codex/**/*.md` + per-repo
      CLAUDE.md mirrors. Ship in ONE follow-up commit so the diff is auditable.

- [ ] [SCRIPT] P0. **Frontmatter rewrite**. `folds_in:` / `parent_plan:` / `companion_handover:` / `supersedes_phases:`
      / `related:` / `depends_on:` lists currently use kebab-case slugs (no extension) so most are unaffected. But a few
      plans use full paths in `companion_handover:` etc. — sweep for any frontmatter value matching `*\.plan\.md` and
      rewrite.

- [ ] [SCRIPT] P0. **CLAUDE.md sweep (PM canonical + symlinked workspace-wide)**. `cursor-configs/CLAUDE.md` references
      `*.plan.md` paths in many sections. Rewrite all occurrences. Symlinks at per-repo `.claude/CLAUDE.md`
      auto-propagate.

- [ ] [SCRIPT] P0. **PLAN_FORMAT.md + task_template.md + prompts/\* updates**. Anywhere these documents describe
      filenames as `<slug>.plan.md`, change to `<slug>.md`. Keep the rest of the format spec untouched (frontmatter
      schema, Cursor checkboxes, 3-tier readiness — none of these change).

- [ ] [SCRIPT] P0. **INDEX.md / ACTIVE_INDEX.md regeneration**. These index files list plan paths. Re-run their
      generator or sed-rewrite the entries. Also any per-epic README that lists sub-plans.

- [ ] [SCRIPT] P0. **MEMORY.md references**. The `MEMORY.md` index in this user's auto-memory + the topical files under
      `memory/` reference plan paths in body text. Sweep + rewrite. Stale memory entries ok to leave as-is if they
      reference plans now archived.

- [ ] [SCRIPT] P0. **Codex doc references**. Codex (`unified-trading-pm/codex/**/*.md`) references plans in many places
      (cross-plan blockers, "see also", deliverable lists). Sweep + rewrite.

- [ ] [SCRIPT] P0. **GitHub Actions workflow templates**. `.github/workflows/*.yml` may reference plan paths. Search +
      rewrite. Also `unified-trading-pm/scripts/workflow-templates/`.

- [ ] [SCRIPT] P0. **Source-code reference audit**. Some Python utilities (instruments-service / UAC / UTL) reference
      plan paths in docstrings or test fixtures. Run `git grep -l "\.plan\.md"` across all sibling repos in
      workspace-manifest.json; sweep + rewrite. Estimated near-zero hits but verify before declaring done.

- [ ] [SCRIPT] P0. **Per-repo CLAUDE.md mirrors**. Some repos may have non-symlinked CLAUDE.md copies.
      `find /Users/.../Code/unified-trading-system-repos -name CLAUDE.md -not -path "*/.git/*"` enumerates; check each
      file is symlink or contains `.plan.md` references.

### A3. Forward-going convention enforcement

todos:

- [ ] [SCRIPT] P1. **PLAN_FORMAT.md "Filename convention" section**. Add explicit rule: `<slug>.md` is canonical;
      `<slug>.plan.md` is legacy and rejected by reviewer. Cite the 2026-05-08 sweep commit hash for archaeological
      reference.

- [ ] [SCRIPT] P1. **CLAUDE.md filename convention rule**. Mirror the PLAN_FORMAT.md addition into the Workspace Configs
      / Plan Format sections of CLAUDE.md. Symlinks propagate to per-repo mirrors.

- [ ] [SCRIPT] P2. **`scripts/quality-gates.sh` STEP — reject `.plan.md` filenames in PR diffs**. Light sweep at PM repo
      PR-time: if any newly-added file matches `*.plan.md`, fail. Mirrors the directory-rule precedent. Optional polish;
      the convention rule above + reviewer discipline cover the same ground.

---

## Phase B — Per-domain epic consolidation

> **Why.** The 9-master move to `plans/epics/` (commit 174224d1, 2026-05-08) intentionally placed 9 master plans
> alongside 7 May-23 epics. Several pairs share a domain — the master is the granular umbrella; the epic is the May-23
> deadline wrapper. Where the deadline epic's content is fully covered by the master plus a small "May-23 deliverable"
> section, consolidation removes one indirection layer. Each pair is an operator decision (some epics may have unique
> scope worth preserving).

### B1. Consolidation candidates (per-domain audit)

todos:

- [ ] [AGENT] P1. **Audit: tradfi_master + sp_prediction_may_23_2026.epic + price_arbitrage_may_23_2026.epic**.
      tradfi_master is the umbrella; sp_prediction is "S&P swing high/low ML model"; price_arbitrage is "CME futures
      same-day-expiry arb + ETF↔future arb". Both epics are 100% TradFi-asset_group. Audit: can sp_prediction's content
      fold into tradfi_master under a "## May-23 deliverables" section? Same for price_arbitrage. Output: per-pair
      recommendation (fold | keep separate | split scope). Operator decides per pair.

- [ ] [AGENT] P1. **Audit: sports_master + sports_ml_may_23_2026.epic**. sports_master is the umbrella; sports_ml is
      "Sports ML prediction (odds + features → strategy → execution, all backtest)". Same-domain pair. Audit +
      recommendation.

- [ ] [AGENT] P1. **Audit: predictions_master + prediction_markets_may_23_2026.epic**. Same-domain pair. Audit +
      recommendation.

- [ ] [AGENT] P1. **Audit: live_defi_rollout_may_23_2026.epic vs the master_to_live_defi_2026_05_23 master +
      defi_master**. The live_defi epic is the May-23 LIVE wrapper; the master plan is the umbrella-of-epics;
      defi_master is the granular asset_group umbrella. Three layers — possibly two collapse. Audit + recommendation.

- [ ] [AGENT] P1. **Audit: cefi_master + cefi_ml_may_23_2026.epic**. Same-domain pair. Audit + recommendation.

- [ ] [AGENT] P1. **Audit: cross_cutting_may_23_2026.epic stays standalone**. Workspace-wide concerns spanning all
      domains; explicitly cross-cutting, not foldable. Document the keep-decision in the audit output for completeness.

### B2. Consolidation execution (operator-greenlit only)

todos:

- [ ] [SCRIPT] P2. **For each operator-greenlit fold**: copy the epic's unique content (May-23 end-state criteria,
      IN/OUT scope, cross-epic handshakes) into a "## May-23 deliverable" section of the master plan; archive the epic
      with a `> SUPERSEDED 2026-05-XX by <master-plan> § May-23 deliverable` banner; update
      `cross_cutting_may_23_2026.epic.md` consumed-table + `master_to_live_defi_2026_05_23` references.

- [ ] [SCRIPT] P2. **Verify post-fold the granular sub-plans referenced by the now-archived epic still link correctly**.
      Each fold may have orphaned sub-plan references; sweep each merged master to verify all consumed sub-plans
      resolve.

---

## Phase C — Convention propagation

todos:

- [ ] [SCRIPT] P1. **Update `plans/PLAN_FORMAT.md`**. Add: filename convention (`<slug>.md` not `<slug>.plan.md`);
      3-layer plan model (May-23 epic at `plans/epics/` + granular master at `plans/epics/` or `plans/active/` +
      sub-plan at `plans/active/`). Reference the 9-master move + this rename as the codifying commits.

- [ ] [SCRIPT] P1. **Update `cursor-configs/CLAUDE.md` "Plan Locking" + "Plan Format" sections**. Reference the new
      filename convention + 3-layer model. Symlinks propagate.

- [ ] [SCRIPT] P1. **Update `task_template.md` + `prompts/*`**. Reflect new filename convention.

- [ ] [SCRIPT] P2. **Add a "How to add a new plan" section** to `plans/PLAN_FORMAT.md` codifying: pick layer (epic vs
      master vs sub-plan), filename = `<slug>.md`, frontmatter required fields, Cursor checkbox format, lifecycle
      (active → archive). Single-file reference for new contributors.

---

## Cross-plan coordination

- This plan does NOT touch existing plan content (only filename + cross-references). Compose with all in-flight plans
  without collision.
- Phase A is mechanical + scriptable + reversible (`git revert <rename-commit>`). Run as a single big workspace-wide
  commit batch when the workspace is quiet.
- Phase B is per-pair operator-driven. No urgency; ship over weeks if needed.

---

## Success criteria

- **Phase A**: zero `*.plan.md` filenames in workspace; `git log --follow <renamed>.md` traces history cleanly; markdown
  previews work in Cursor / VS Code / GitHub web UI.
- **Phase B**: each per-domain pair has an operator decision recorded; greenlit folds executed; archived plans carry
  `SUPERSEDED` banners.
- **Phase C**: PLAN_FORMAT.md + CLAUDE.md + task_template.md + prompts reflect new conventions; new plans onboarded in
  the new shape.

---

## Notes for executing agents

- **Phase A is a single workspace-quiet window.** Lots of files renamed at once + thousands of cross-ref rewrites.
  Coordinate so nobody else is mid-edit; otherwise sed sweeps generate noise.
- **`git mv` preserves history.** Any agent who sees "this file's history starts at the rename commit" forgot the
  `--follow` flag — `git log --follow <path>` traces through.
- **No content changes during the rename commit.** Mixing rename + content edit confuses similarity heuristic on edge
  cases. Keep the rename commit content-clean; ship content edits in follow-ups.
- **Phase B requires operator decisions per pair.** Don't auto-fold. Audit, present, await call.
