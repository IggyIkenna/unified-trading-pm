---
doc_type: issue
title:
  'check_archive_candidates.sh AND check-locked-plan-deletion.sh both mis-read locked_by: "" (literal quoted-empty) as a
  real lock — silently masks archive candidates + blocks legitimate archival'
summary: >-
  Found while verifying a plan_reconciler hunter finding during the 2026-08-07 defi-tranche run. Two independent
  corpus-hygiene scripts extract the YAML `locked_by:` frontmatter value via naive grep+sed/grep -oP rather than a real
  YAML parser, so when a doc's `locked_by:` value is the literal two-character string `""` (quoted-empty, produced by
  some prior automated lock-clearing pass instead of leaving the value bare), the extracted shell variable is the
  non-empty 2-char string `""` — `[ -n "$locked_by" ]` / `[[ -n "$LOCKED_BY" ]]` both read that as "locked" even though
  the doc is genuinely unlocked. Confirmed exactly 4 corpus docs currently carry this literal pattern (`grep -rn
  '^locked_by: ""' plans/active/*.md plans/active/issues/*.md`):
  `dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md` (resolved+archived this run, see below),
  `mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md` (done=16/open=1 — not itself an archive candidate right
  now, but will be silently masked once its last todo closes, same bug),
  `sports_index_recency_masked_captured_atoms_2026_07_13.md` (done=7/open=0 — genuine masked archive candidate),
  `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` (done=5/open=0 — genuine masked archive candidate). The
  second, independently-discovered instance of the same bug class: `check-locked-plan-deletion.sh`'s commit-msg hook
  (`LOCKED_BY=$(git show "HEAD:$plan_file" | grep -oP '^\s*locked_by:\s*\K.*')`) hit this live during this run —
  attempting to archive `dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md` in the same commit as
  clearing its `locked_by: ""` field triggered `❌ BLOCKED: ... is locked by '""'.` even though the doc was never
  actually locked. Worked around this run by splitting into two commits (clear `locked_by:` first, archive in a separate
  follow-up commit, matching the existing "never combine checkbox-flip with git-mv" precedent) — but the next agent to
  hit a *genuinely* quoted-empty `locked_by:` won't know that workaround exists unless they read this doc.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, tooling-bug, locked_by, yaml-parsing, archive-candidates, quoting, shell-script]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md,
  ]
created: 2026-08-07
author: plan_reconciler
last_updated: 2026-08-07
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: script
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
source: [plan_reconciler dispatch agt-a2268a, 2026-08-07, defi tranche run]
---

# `locked_by: ""` (literal quoted-empty) masks archive candidates + blocks legitimate archival

## Root cause (verified by reading both scripts directly, not inferred)

**`scripts/plan-hygiene/check_archive_candidates.sh:163-164`**:

```bash
locked_by="$(grep -E '^locked_by:' "$f" 2>/dev/null | head -1 | sed -E 's/^locked_by:[[:space:]]*//')"
[ -n "$locked_by" ] && continue
```

For a doc with `locked_by: ""` in frontmatter, `sed` strips the `locked_by:` prefix + whitespace, leaving the shell
variable holding the 2-character string `""` — non-empty, so `[ -n "$locked_by" ]` is true and the doc is silently
skipped as "locked," never surfacing as an archive candidate even when it has 0 open todos and is genuinely unlocked.

**`scripts/hooks/check-locked-plan-deletion.sh:58-59`** (commit-msg stage hook):

```bash
LOCKED_BY=$(git show "HEAD:$plan_file" 2>/dev/null | grep -oP '^\s*locked_by:\s*\K.*' | head -1 || :)
if [[ -n "$LOCKED_BY" ]] && ! grep -q '\[unlock-plan\]' <<<"$COMMIT_MSG"; then
    echo "❌ BLOCKED: $plan_file is locked by '$LOCKED_BY'."
```

Same bug, same root cause (naive text extraction instead of real YAML parsing), independent implementation. Hit live
this run: a commit that both cleared `locked_by: ""` → `locked_by:` (empty) AND `git mv`'d the doc to
`plans/archive/issues/` in the same commit was blocked with `is locked by '""'.` even though the doc was never a real
lock — this hook reads `HEAD:$plan_file` (the state _before_ the commit being validated), so even a same-commit clear
doesn't help; only a prior, separate commit that already cleared the field resolves it.

## Corpus population affected (verified live, 2026-08-07)

```
$ grep -rn '^locked_by: ""' plans/active/*.md plans/active/issues/*.md
plans/archive/issues/dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md  (was active, resolved+archived this run)
plans/active/issues/mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md         (done=16 open=1, not yet a candidate)
plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md            (done=7 open=0, MASKED candidate)
plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md         (done=5 open=0, MASKED candidate)
```

`dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md` was resolved + archived directly by this
plan_reconciler run (both todos independently verified with hard sha evidence) — see
`/plans/archive/issues/dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`. The other two genuine
candidates (`sports_index_recency_masked_captured_atoms_2026_07_13.md`,
`mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`) are OUTSIDE the defi tranche (sports/cross-cutting) —
left for their own tranche's `/plan-reconcile` or `/archive-candidates-audit` pass, or a future `all`-scoped run, per
this run's topic-scoped mandate.

## Todos

- [ ] [SCRIPT] P2. Fix `check_archive_candidates.sh`'s `locked_by` extraction to treat a literal quoted-empty value
      (`""` or `''`) the same as a bare-empty value — strip a leading/trailing matching quote pair before the
      `[ -n ... ]` test, or switch to a real YAML frontmatter parser (several already exist in
      `scripts/plan-hygiene/*.py`, e.g. the line-based parser pattern used by `check_frontmatter_schema.py`) rather than
      hand-rolled grep+sed. Done when: a doc with `locked_by: ""` is correctly treated as unlocked by the script (add a
      fixture/test case if the script has a test harness; if not, verify manually against
      `mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md` once its `done=` count reaches its `open=` count).
- [ ] [SCRIPT] P2. Apply the same fix to `check-locked-plan-deletion.sh`'s `LOCKED_BY` extraction (the `grep -oP`
      pattern). Done when: a commit that clears `locked_by: ""` → `locked_by:` (empty) and archives the same doc in ONE
      commit is no longer blocked (currently requires the two-commit workaround this run used).
- [ ] [SCRIPT] P3. Grep-audit `scripts/plan-hygiene/*.sh` + `scripts/hooks/*.sh` for other hand-rolled
      `grep '^field:'`/`sed`-based frontmatter-field extractors (not just `locked_by`) that could hit the same
      literal-quoted-empty-string class on any other field (`superseded_by`, `resolved_by`, etc.) — this specific bug
      was found by accident while chasing an unrelated finding, not from a systematic sweep; the true scope could be
      larger. Done when: every such extractor in both directories is either confirmed quote-safe or listed here as a
      follow-up.
- [ ] [SCRIPT] P3. Once the frontmatter seeding/lock-clearing tooling that PRODUCES `locked_by: ""` (rather than
      bare-empty `locked_by:`) is identified, fix it at the source too — the two docs above with `done > open` (not yet
      masked candidates) will otherwise keep landing in this same trap as their remaining todos close.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the archival ritual + `locked_by:` semantics
  this bug undermines.
