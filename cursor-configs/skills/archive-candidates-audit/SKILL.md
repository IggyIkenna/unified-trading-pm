---
name: archive-candidates-audit
description: >-
  Audit the `check_archive_candidates.sh` candidate set (docs with 0 open todos, unlocked, not archive_exempt, still in
  plans/active/) — per-doc content verification using the proven 4-verdict rubric from the 2026-08-06 backlog-clearing
  session. Classifies each candidate as ARCHIVE (genuinely complete → git mv + banner + referrer sweep), NEEDS_TODO
  (checkbox-vs-prose contradiction → convert deferred work to tracked `- [ ]` follow-ups), KEEP_OPEN (live incident /
  DO-NOT-ARCHIVE guard → synthesize follow-up todos), or ARCHIVE_EXEMPT (standing-reference hub → add `archive_exempt:
  true` with Progress Log justification). Mirrors `/na-eligibility-audit`'s pattern of turning a one-off CI-firefighting
  session's proven methodology into a repeatable, invocable skill. Trigger on `/archive-candidates-audit`, "audit
  archive candidates", "check for done-but-unarchived docs", "clear the archive candidates backlog".
---

# /archive-candidates-audit — done-but-unarchived doc remediation

Generalizes the 2026-08-06 slot-10 backlog-clearing session's proven methodology (121 candidates → 0: 77 archived, 38
converted to tracked follow-ups, 8 kept open as live incidents, 2 marked archive_exempt) into a repeatable,
`/`-invocable skill — the same treatment `/na-eligibility-audit` got for NA-doc reclassification. Where that skill asks
"should this NA doc be reclassified?", this skill asks a different question about a DISJOINT population: **"is this
done-but-unarchived doc genuinely complete, or does its prose tell a different story than its checkboxes?"**

The check (`scripts/plan-hygiene/check_archive_candidates.sh`) is the inventory — no separate inventory-generation step
needed. It already excludes `locked_by`, `gate_on_depends`-gated, and `archive_exempt: true` docs, so every candidate it
reports genuinely LOOKS archivable by the checkbox signal alone. The skill's job is the per-doc content read to confirm.

**Out of scope**: terminal-status-archived violations (those carry `status: resolved`/`complete` already — a mechanical
`git mv` + banner, handled by `check_terminal_status_archived.py`); AG-closeout linkage orphans (`/ag-closeout-audit`'s
corpus); NA-corpus ratchet (`/na-eligibility-audit`'s corpus); corpus-wide contradiction sweeps (`/plan-reconcile`'s
corpus).

## Prerequisites

- Fresh pull of `unified-trading-pm` to `origin/live-defi-rollout`
- Clean worktree (the skill modifies plan docs + runs `git mv`)

## Step 1 — Inventory

```bash
cd unified-trading-pm
bash scripts/plan-hygiene/check_archive_candidates.sh
```

The output lists every candidate with `done=N` and `status=<value>`. Capture the full list. The live count drifts with
concurrent AO slots — re-run immediately before starting classification, don't reuse a stale snapshot.

## Step 2 — Classify each candidate (the 4-verdict rubric)

For EACH candidate, READ the full doc — the summary, the Progress Log, every todo's wording. A doc with 0 open todos is
NOT automatically content-complete. Apply these verdicts (proven across 121 docs on 2026-08-06):

### ARCHIVE — genuinely complete

**Criteria**: every listed todo is done, the Progress Log confirms completion, no prose-only deferred work, no
DO-NOT-ARCHIVE guard, not a standing-reference hub.

**Action**:

1. Flip `status` to `resolved` (or `false-positive` / `superseded` if applicable)
2. Add the archive banner at the top of the file:
   ```
   > **ARCHIVED <YYYY-MM-DD>** — <one-line reason>. Original path: `plans/active/issues/<slug>.md`.
   ```
3. `git mv` to `plans/archive/issues/` (or `plans/archive/YYYY_MM/` for non-issue plans)
4. Fix ALL corpus referrers: `bash scripts/plan-hygiene/find_moved_doc_referrers.sh <old-path> <new-path>` and update
   each
5. Re-run `check_archive_candidates.sh` to confirm the count dropped

### NEEDS_TODO — checkbox-vs-prose contradiction

**Criteria**: all listed checkboxes are done, but the doc's own summary/Progress Log/prose describes work that was never
converted to a tracked `- [ ]` todo (the exact anti-pattern
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2 names).

**Action**:

1. Add a `## Follow-ups` section with concrete `- [ ] [TAG] P<n>. <description> (repo: <target>)` todos for each piece
   of deferred work
2. Add a Progress Log entry documenting what was converted
3. Do NOT archive — the new todos keep the doc in the active corpus
4. The doc will naturally fall off the candidate list (now has open todos)

### KEEP_OPEN — live incident / DO-NOT-ARCHIVE

**Criteria**: the doc describes an unresolved, ongoing issue (e.g. a recurring production outage, a still-open
investigation) despite having 0 open checkboxes. Often carries an explicit DO-NOT-ARCHIVE guard in its prose.

**Action**:

1. Synthesize any undocumented follow-up work into tracked `- [ ]` todos (same as NEEDS_TODO)
2. Add a Progress Log entry confirming the doc stays open with justification
3. Do NOT archive — the doc describes a live concern

### ARCHIVE_EXEMPT — standing-reference hub

**Criteria**: the doc is intentionally kept in `plans/active/` as a coordination/reference/index hub — it carries 0
native todos by design, not because work was forgotten. Examples from 2026-08-06:
`defi_strategy_pnl_axis_index_2026_07_24.md` (entry-point hub for strategy/PnL/backtest axis),
`tradfi_consolidated_closeout_2026_07_18.md` (umbrella coordination index with active child plans).

**Action**:

1. Add `archive_exempt: true` to the doc's frontmatter
2. Add a Progress Log entry citing WHY it's exempt (the specific hub/reference role it serves)
3. Do NOT archive — the exempt flag permanently excludes it from future candidate scans

## Step 3 — Verify

```bash
bash scripts/plan-hygiene/check_archive_candidates.sh
```

Should report 0 candidates (or only the KEEP_OPEN + NEEDS_TODO docs you intentionally left). If the baseline is >0 and
you've cleared everything, run `--update-baseline` to persist the new lower count.

## Step 4 — Ship

Commit each archived doc + its referrer fixes as a batch, using the standard archival commit format. For the PM repo:

```bash
git add <all touched files>
git commit -m "docs(plans): archive-candidates-audit — <summary of verdicts>"
bash scripts/quickmerge.sh "docs(plans): archive-candidates-audit — <summary>" --agent --files '<paths>'
```

## Batches — when the candidate set is large

The 2026-08-06 session used 10 parallel read-only classification sub-agents batched by `asset_group`. For sets >~20
candidates, batch the same way:

1. Split the candidate list by `asset_group` (cefi, defi, sports, tradfi, cross-cutting, meta)
2. For each batch, launch a read-only sub-agent that reads each doc and emits verdicts (ARCHIVE / NEEDS_TODO / KEEP_OPEN
   / ARCHIVE_EXEMPT with evidence for each)
3. Collect verdicts, then execute the actions (archival, todo-synthesis, exempt-flagging) sequentially to avoid git
   conflicts

## Idempotency

Re-running this skill against the same candidate set is safe: already-archived docs are gone from `plans/active/` (the
check won't flag them), already-exempted docs are excluded by the check's `archive_exempt: true` filter, and
already-todo'd docs have open checkboxes (the check requires `open_count=0`). The skill converges to 0 candidates with
repeated runs.

## Relation to other skills

- **`/ag-closeout-audit`**: finds orphaned docs with NO active covering plan. This skill's population is the INVERSE —
  docs that ARE in an active plan but the plan's own work is done and never got archived.
- **`/na-eligibility-audit`**: audits `assigned_vm: NA` docs for reclassification eligibility. Orthogonal population.
- **`/plan-reconcile`**: corpus-wide contradiction/false-unchecked sweep. Broader scope; this skill is narrowly scoped
  to the `check_archive_candidates.sh` candidate set.
