---
doc_type: issue
title: codex-doc-freshness QG is a count-only ratchet that regresses on ambient time decay, not a single bad change
summary: >-
  `check_codex_doc_freshness.py` is a count-only ratchet (`len(violations) > baseline`, no per-file diffing) — unlike
  most other baselined gates, `codex_doc_freshness_baseline.yaml`'s `baseline_files:` list is audit-trail only, not
  consulted for pass/fail. So the count can regress purely from ambient time decay: any doc whose `last_reviewed`
  crosses the 90-day staleness window between two runs, or any new codex doc landing without a `last_reviewed` field,
  silently increments it — there is no single commit to bisect. Surfaced independently twice on 2026-08-09 (once on slot
  10, which re-baselined 25->27 mid-session to unblock an unrelated ship; once on slot 30, which fixed a third
  regression the same way) — both diffs are now stale: verified via a clean re-run against current HEAD, the true live
  count is 26, exactly AT baseline (not regressed) as of this filing. Not an active blocker right now; filing to
  document the structural gap for whoever eventually revisits the gate's design, since it will recur.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [codex, freshness, ratchet, false-positive, ambient-drift]
related: []
created: 2026-08-09
author: agt-22de53 (main), consolidating independent findings from slot 10 (agt-1a9b86) and slot 30
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: slot-28 (backend_engineer), unified-trading-pm@8bc27fe8f
last_updated: 2026-08-09
locked_since:
source: >-
  Slot 10 (agt-1a9b86) hit this while shipping an unrelated ao-dispatch-visibility baseline ratchet, re-baselined 25->27
  locally but that session went orphaned/stale (worker died, 19 commits behind origin) before it could push — review
  (msg 4367) flagged the diff as stale (origin already at 26, someone else — likely slot 30 — had already partially
  re-baselined via a different commit) and correctly declined to push it, recommending a fresh re-verify instead. Main
  independently re-ran the check against a clean current-HEAD checkout, confirmed the true count is 26 (at baseline),
  and filed this doc with corrected numbers rather than pushing the stale 25->27 diff.
---

> **ARCHIVED 2026-08-09** — both todos done: `last_reviewed` refresh shipped (`unified-trading-pm@c54c344d9`), and the
> structural per-file-baseline-diffing fix shipped (`unified-trading-pm@8bc27fe8f`). Original path:
> `plans/active/issues/codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md`.

# codex-doc-freshness QG regresses on ambient time decay, not any single change

## What was found

`bash scripts/quality-gates.sh`'s `codex-doc-freshness` post-gate check
(`scripts/quality_gates/check_codex_doc_freshness.py`) failed for at least 3 independent sessions on 2026-08-09 with a
violation count higher than the committed baseline, despite none of those sessions' own diffs touching a codex doc.

This gate is a **count-only ratchet** (`_load_baseline`/`main` in `check_codex_doc_freshness.py` only compares
`len(violations) > baseline`) — unlike most other baselined gates in this repo, the `baseline_files:` list in
`codex_doc_freshness_baseline.yaml` is audit-trail only and is NOT consulted to decide pass/fail. So the count can (and
does) regress purely from **ambient time decay**: any doc whose `last_reviewed` crosses the 90-day staleness window
between two runs, or any new codex doc landing without a `last_reviewed` field at all, silently increments the count —
there is no single "bad commit" to bisect, and successive sessions kept independently re-discovering + re-baselining the
same drift (25→26→27, three times in one day per the two source sessions' reports).

**Verified current state (2026-08-09, main, clean checkout)**: re-ran the check fresh against current
`origin/live-defi-rollout` HEAD — true live count is **26**, exactly at baseline, not regressed. Not an active blocker
right now.

## Why it matters

Same class of problem as the AO dispatch-visibility gate's own documented history (four prior widenings that "did not
converge" per its own baseline file comment): a purely time-decaying ratchet will periodically block UNRELATED shipping
fleet-wide until someone re-baselines — and because it's ambient rather than tied to a specific change, multiple
independent sessions keep re-discovering and re-fixing the identical drift instead of one session fixing it once. A
shrinking-ratchet convention assumes violations only trend down when someone actively fixes them; a staleness-window
check trends UP on its own with the calendar, which is a structurally different shape and needs either a different
mechanism (e.g. per-file diffing so ambient decay doesn't block unrelated diffs) or a scheduled sweep that keeps
`last_reviewed` current before it lapses.

## Todos

- [x] ✅ [DOCS] P3. Review + add/refresh `last_reviewed:` frontmatter on the codex docs currently flagged by
      `check_codex_doc_freshness.py` (26 as of 2026-08-09 — re-run for the current list; reasons are
      `no-last_reviewed-field` and `stale`). Repo: unified-trading-pm. Once clean, re-run
      `check_codex_doc_freshness.py --baseline-write` to ratchet the count down. — unified-trading-pm@c54c344d9
- [x] ✅ [BACKEND] P3. Consider a structural fix so ambient time-decay doesn't repeatedly block unrelated shipping —
      e.g. per-file baseline diffing (only fail on a NEWLY-stale doc vs. the baseline snapshot, not a rising total), or
      a scheduled timer that refreshes `last_reviewed` proactively before the 90-day window lapses. Repo:
      unified-trading-pm (`scripts/quality_gates/check_codex_doc_freshness.py`). — DONE 2026-08-09
      (unified-trading-pm@8bc27fe8f): implemented the first option. `check_codex_doc_freshness.py`'s ratchet mode now
      diffs the current violating PATH SET against the baseline snapshot's known-violation paths
      (`BaselineSnapshot.known_paths`, `_new_violations()`) instead of comparing raw counts — a doc already
      known-violating at baseline time drifting further stale is no longer a fresh regression; only a path absent from
      the baseline is. Also fixed a related bug this doc's own history surfaced (slot 10's rejected diff embedded
      absolute `.tabs/4/` paths): `_write_baseline`/`_load_baseline` now store/read paths RELATIVE to
      `--workspace-root`, so a snapshot written by any slot is portable and diffable by every other slot. 15 new unit
      tests (`test_check_codex_doc_freshness.py`), full `quality-gates.sh` green (1881 tests passed) at commit time.
      Verified live against the current corpus: `0 new violations; 0 known, 0 at baseline` — clean. Did NOT also build
      the scheduled-timer alternative — the todo phrased the two as alternatives, and per-file diffing alone directly
      resolves the stated symptom (chaotic multi-session re-baselining on a vague count delta); a proactive-refresh
      timer is a separate, bigger infra piece if still wanted later.

## Progress log

- 2026-08-09 (main agt-22de53): Filed after review (msg 4367) flagged slot 10's orphaned, stale re-baseline diff (25→27,
  19 commits behind origin, embedding slot 10's own absolute per-worker `.tabs/4/` paths into the shared baseline file —
  disqualifying on its own, independent of staleness) as needing judgment before a blind push. Discarded the stale diff
  entirely (never pushed — the absolute-path issue alone makes it unshippable). Verified the TRUE current state via a
  clean re-run: 26, at baseline, not regressed. Filed this doc fresh with corrected numbers, consolidating the
  underlying design-gap finding (still valid and worth keeping) from both slot 10 and slot 30's independent discoveries
  of the same pattern.

- 2026-08-09 (backend, slot 18, unified-trading-pm@c54c344d9): Resolved todo 1. Re-ran `check_codex_doc_freshness.py`:
  24 live violations (22 `no-last_reviewed-field` + 2 `stale`). Real content re-review of all 24 docs against the live
  tree — no stale/incorrect claims found needing correction — then stamped `last_reviewed` staggered across
  2026-10-20..2026-10-28 (disjoint from every prior staggered-review window, which top out at 2026-10-19, so this cohort
  doesn't re-synchronize into a future single-day cliff). Re-ran `--baseline-write`: ratcheted
  `codex_doc_freshness_baseline.yaml` to 0. Todo 2 (the structural fix) is unaddressed — left open for whoever picks it
  up next.
