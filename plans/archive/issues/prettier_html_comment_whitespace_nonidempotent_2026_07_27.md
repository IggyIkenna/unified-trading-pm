---
doc_type: issue
title:
  Prettier reformats a pre-existing HTML-comment block in sports_consolidated_closeout_2026_07_19.md differently on
  every run (non-idempotent)
summary: >-
  Shipping an unrelated small doc edit (a cross-link note) to sports_consolidated_closeout_2026_07_19.md triggered `npx
  prettier --write` to reformat a pre-existing, unrelated `<!-- BLOCKED-UPSTREAM evidence -->` HTML comment block (~line
  350) to a DIFFERENT whitespace-run width on 3 separate invocations this session, growing rather than converging.
  Whitespace-only, inside a non-rendered comment, but it generates unrelated diff noise and periodically trips
  quickmerge's M1 drift-check on any future commit touching this file.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, prettier, tooling, plan-hygiene, non-idempotent]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md,
  ]
created: "2026-07-27"
source: sports_closeout_track_x_hygiene_2026_07_25.md todo 1 (shipping side-effect)
resolved_by:
  unified-trading-pm doc fix, 2026-07-28 -- collapsed the offending HTML comment body onto one physical line in
  plans/active/sports_consolidated_closeout_2026_07_19.md, verified idempotent (2 consecutive `prettier --write` runs,
  zero diff)
locked_by:
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

> **🟢 RESOLVED 2026-07-28** — fixed in `unified-trading-pm` (doc-only, this repo); verified idempotent. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`.

## What I found

While shipping a small, unrelated doc edit to `plans/active/sports_consolidated_closeout_2026_07_19.md` (adding a
cross-link note in the Canonical target section, `sports_closeout_track_x_hygiene_2026_07_25.md` todo 1),
`npx prettier --write` on this file reformatted an UNRELATED, pre-existing
`<!-- BLOCKED-UPSTREAM evidence (2026-06-24 slot-23): ... -->` HTML comment block starting around line 350 — a set of
lines each containing one huge run of spaces (hundreds of columns) followed by real text. Observed the SAME block
reformatted to a DIFFERENT (larger) whitespace-run length on 3 separate `prettier --write` invocations this session (my
manual run, the pre-commit hook's auto-stage prettier run, and quickmerge Pass-2's internal drift-check prettier run) —
each pass grew the space run rather than converging to a stable width. This looks like non-idempotent behavior (possibly
interacting with `proseWrap: always` / `printWidth: 120` on an abnormally long single "line" inside an HTML comment,
which prettier does not word-wrap the way it does prose text) rather than a real content change — whitespace-only,
inside a comment, invisible in rendered markdown.

Net effect observed: quickmerge Pass-2's own M1 check ("prettier reformatted --files AFTER the Pass-1 sentinel was
certified") fired against this exact block, and the resulting auto-commit attempt failed on an (unrelated) branch-drift
race — I discarded that leftover formatting-only diff rather than ship unrelated content, since my actual task's content
was already committed + pushed cleanly (`unified-trading-pm@7b761bb37`).

## Why it matters

Every future prettier run against this file (manual, pre-commit auto-stage, or quickmerge's internal drift check) will
likely keep drifting this block, generating unrelated diff noise on every unrelated commit to this file and periodically
tripping quickmerge's M1 drift warning / auto-commit-then-branch-drift-race path for agents who have nothing to do with
this content.

## Recommended decision

Normalize the block's whitespace once (replace the huge space runs with a small fixed indent, or reflow the comment body
as normal wrapped text) so prettier converges to a stable format and stops drifting on unrelated edits. Low priority —
cosmetic, whitespace-only, inside a non-rendered HTML comment — but worth a one-line fix next time someone is already
touching this file's Track K section.

## Todos

- [x] ✅ [DOC] P3. Normalize the whitespace-run formatting of the
      `<!-- BLOCKED-UPSTREAM evidence (2026-06-24 slot-23):     ... -->` HTML comment block in
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (~line 350, inside Track K) so `npx prettier --write`
      converges to a stable, idempotent format instead of growing the whitespace run on each pass. (repo:
      unified-trading-pm, doc edit only.) **Done when**: 2 consecutive `prettier --write` runs on the file produce zero
      diff. **DONE 2026-07-28.** Root cause confirmed by direct repro: prettier (`proseWrap: always`) re-indents each
      hard-line-broken continuation line INSIDE a multi-line HTML comment by a few more spaces on every pass — a small
      fixed-indent normalization alone (6 spaces, matching the surrounding list continuation) did NOT stop the growth
      (verified: still drifted +4 spaces/pass). The actual fix was collapsing the whole comment BODY onto one physical
      line (no internal hard breaks) so there is no continuation-line indent for prettier to keep re-computing — proven
      on an isolated scratch repro first, then applied to the real file. **Verified against the "Done when" criterion**:
      ran `npx prettier --write` twice in a row on `sports_consolidated_closeout_2026_07_19.md` — the first run made one
      more (benign) adjustment (rewrapped the trailing " (FOLDED IN from ..." prose after the comment's `-->` onto its
      own line), the second run produced zero diff. Content preserved verbatim (`git diff` shows only whitespace/line-
      wrap changes, confirmed via `diff`). Prettier available locally via `npx prettier@3.9.4`.
