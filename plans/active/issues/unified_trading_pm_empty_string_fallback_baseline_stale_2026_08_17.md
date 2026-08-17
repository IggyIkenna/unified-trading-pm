---
doc_type: issue
title:
  unified-trading-pm's STEP 5.101 no_empty_string_fallback ratchet is red (322 sites > baseline 319) on 3
  pre-existing files unrelated to any in-flight diff — QG-blocking every push to the repo
summary: >-
  quality-gates.sh STEP 5.101 (check_no_empty_string_fallback.py) fails on a clean rebase of
  live-defi-rollout with zero relation to the diff being shipped: 322 `.get(key, "")` empty-string-fallback
  sites workspace-wide vs a committed baseline of 319 for unified-trading-pm, naming 3 pre-existing sites
  (scripts/quality_gates/check_xfail_skip_tracked.py:177, scripts/quality_gates/detect_template_drift.py:581,
  scripts/sports/migrate_player_mappings_to_canonical.py:63) that a `git diff` against the pre-session base
  commit confirms are untouched by my session's own commits. Blocks EVERY worker trying to ship to
  unified-trading-pm right now, not just this task.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, quality-gates, ratchet, empty-string-fallback, repo-blocker, qg-red]
related:
  [
    /plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/active/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md,
  ]
created: 2026-08-17
author: backend_engineer (slot-1, interactive)
priority: P1
parent_epic: infrastructure_master
source: >-
  Discovered while shipping ci_satellite_ao_dispatch_batch15's rollout-ratchet-panel-backend follow-up
  (detect_template_drift.py wiring, unified-trading-pm@16ce1d7065 + b8833445c8) — Pass-1 quality-gates.sh
  failed STEP 5.101 on files this session never touched.
assigned_vm: planning
execution_scope: orchestrator-agent
resolved_by:
locked_by:
context_scope:
  [
    scripts/quality_gates/check_no_empty_string_fallback.py,
    scripts/quality_gates/no_empty_string_fallback_baseline.yaml,
    /plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
  ]
depends_on: []
---

# unified-trading-pm's no_empty_string_fallback ratchet is red on pre-existing, unrelated files

## What I found

Running Pass-1 `quality-gates.sh` on a fresh, clean rebase of `origin/live-defi-rollout` (no relation to my
own in-flight diff — verified below), STEP 5.101 failed:

```
[FAIL] unified-trading-pm: 322 empty-string-fallback site(s) > baseline 319. New/over-baseline site(s)
(positional tail-slice — no baseline commit on record for this repo yet):
scripts/quality_gates/check_xfail_skip_tracked.py:177; scripts/quality_gates/detect_template_drift.py:581;
scripts/sports/migrate_player_mappings_to_canonical.py:63
```

Verified this is genuinely unrelated to my session's own commits (`unified-trading-pm@16ce1d7065` +
`@b8833445c8`, the `detect_template_drift.py`-wiring follow-up from
`rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md`):

```
git diff <pre-session-base>..HEAD -- scripts/quality_gates/check_xfail_skip_tracked.py \
  scripts/quality_gates/detect_template_drift.py scripts/sports/migrate_player_mappings_to_canonical.py
```

returns EMPTY — none of the 3 flagged files appear anywhere in my diff. Also directly confirmed my own new
file (`scripts/cicd/write_template_drift_verdicts.py`, which does contain one `.get('message', '')`
call) is NOT among the checker's flagged sites (grepped the checker's full output for the filename — zero
hits), so the checker isn't even counting my own addition against the ratchet in this run.

The message's own wording — "positional tail-slice — no baseline commit on record for this repo yet" —
combined with the baseline YAML's last touch being a DIFFERENT repo's entry
(`chore(qg): ratchet agent-orchestrator no_empty_string_fallback baseline 25 -> 21`, `2503ead58f`,
2026-08-16) suggests `unified-trading-pm`'s own baseline entry (319) may simply be stale/never properly
re-ratcheted against the repo's real current count (322), rather than any single recent commit having
"introduced" exactly these 3 sites. I did not dig further into WHEN each of the 3 sites' `.get(key, "")`
calls actually landed (out of scope for a same-session diagnosis) — that's the fix-doer's first step below.

**This is a RECURRING pattern, not a one-off** — at least 3 prior archived issue docs cover the exact same
"empty-string-fallback baseline breach blocks all pushes" shape for this repo:
`mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`,
`mtds_empty_string_fallback_baseline_drift_2026_07_30.md`,
`mtds_empty_string_fallback_baseline_breach_blocks_all_pushes_2026_08_08.md`,
`mtds_empty_string_fallback_baseline_exceeded_scripts_2026_08_08.md` (all `plans/archive/issues/`). Did not
read all 4 in full this session (out of scope for a same-session diagnosis while blocked) — whoever picks
up the fix todos below should check whether the recurrence itself (not just this instance) needs a
different remedy (e.g. a pre-push local check, or fixing whatever keeps letting new un-annotated
`.get(key, "")` sites land) rather than just clearing the count again.

## Why it matters

This is a **hard QG gate** (`quality-gates.sh` STEP 5.101) — it blocks `git commit` for EVERY worker
shipping to `unified-trading-pm`, not just this task. Per the CLAUDE.md HARD RULE, ratchet baselines may
only go DOWN (no laundering a real drift by bumping the baseline up), so the fix is either (a) add
`# noqa: qg-empty-fallback` with a one-line reason to each of the 3 sites if the empty-string fallback is
genuinely safe there (mirrors the precedent in `write_version_coherence_verdicts.py`/my own
`write_template_drift_verdicts.py` fix), or (b) rewrite each site to fail fast if it isn't. Per the SSOT
issue doc's own guidance (`mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`), this is a
per-site judgment call, not something safe to bulk-annotate without reading each call site.

## Recommended decision

Fix the 3 named sites per the SSOT's own guidance (fail-fast rewrite, or a justified `# noqa:
qg-empty-fallback`), verify the count returns to ≤319, and confirm no OTHER sites crept in between now and
the fix (re-run `check_no_empty_string_fallback.py` fresh, don't trust this doc's snapshot).

## Todos

- [ ] [CODE] P1. Fix `scripts/quality_gates/check_xfail_skip_tracked.py:177`'s `.get(key, "")` site — read
      the call site, either rewrite to fail fast or add a justified `# noqa: qg-empty-fallback`. Repo:
      unified-trading-pm.
- [ ] [CODE] P1. Fix `scripts/quality_gates/detect_template_drift.py:581`'s `.get(key, "")` site — read the
      call site, either rewrite to fail fast or add a justified `# noqa: qg-empty-fallback`. Repo:
      unified-trading-pm.
- [ ] [CODE] P1. Fix `scripts/sports/migrate_player_mappings_to_canonical.py:63`'s `.get(key, "")` site —
      read the call site, either rewrite to fail fast or add a justified `# noqa: qg-empty-fallback`. Repo:
      unified-trading-pm.
- [ ] [CODE] P1. Once all 3 sites are fixed, re-run `check_no_empty_string_fallback.py` fresh (not this
      doc's snapshot) to confirm the count is back at or below the committed baseline (319), and ratchet the
      baseline file DOWN if the true clean count differs from 319. Repo: unified-trading-pm.

## Progress Log

- **2026-08-17 (slot-1, interactive)**: filed while blocked shipping the `detect_template_drift.py`-wiring
  follow-up (`rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md`). Declared repo-blocker
  RB (kind: qg_red) via `POST /api/repo-blockers`; my own 2 local commits (`16ce1d7065`, `b8833445c8`) stay
  queued locally, unpushed, until this resolves.
