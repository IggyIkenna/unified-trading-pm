---
doc_type: issue
title:
  AO dispatch-visibility gate regressed (26 > baseline 24) — sports_all_vendor_honest_coverage_convergence's combined
  [SCRIPT][BLOCKED-UPSTREAM-OUTAGE] tag reads as an undeclared exclusion
summary: >-
  While shipping an unrelated docs-only fix, `check_ao_dispatch_visibility_gate.py`'s zero_dispatchable_docs axis failed
  (26 > baseline 24) due to concurrent, unrelated sports-capture-session commits that landed via a routine fresh-pull
  mid-task. Root-caused one concrete new regression: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s
  todo tags `[SCRIPT][BLOCKED-UPSTREAM-OUTAGE]` back-to-back with no separating space, and the parser's marker-detection
  apparently expects the BLOCKED-token to open its own bracket in isolation (or at least be independently matched),
  reading the combined form as an undeclared/accidental exclusion. Re-baselined to the measured 26 to unblock unrelated
  shipping per this gate's own documented remedy ("only --update-baseline after fixing or filing the newly-found
  accidental exclusions") — did not attempt the parser fix itself (agent-orchestrator code change, outside this
  session's docs-only task scope).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, dispatch-visibility, ratchet, sports, false-positive]
related:
  [
    /plans/archive/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    scripts/quality_gates/check_ao_dispatch_visibility_gate.py,
    scripts/quality_gates/ao_dispatch_visibility_baseline.yaml,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
source: >-
  Surfaced 2026-08-08 while shipping ao_satellite_ao_dispatch_batch5-003 (unrelated docs-only §3/§4 closure) — the QG's
  post-gate check failed on unrelated corpus drift that landed via a routine mid-task fresh-pull.
---

# AO dispatch-visibility gate regressed on an unrelated, concurrent sports-capture commit

## What I found

`bash scripts/quality-gates.sh` failed its `ao-dispatch-visibility` post-gate check
(`check_ao_dispatch_visibility_gate.py`) with `zero_dispatchable_docs=26 > baseline 24`. My own staged diff (5 docs-only
files, none of them AO-dispatch-related) did not touch any of the 26 flagged docs — confirmed via
`git diff --cached --stat` before running QG. Root-caused at least one of the +2 new regressions:
`plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` line 175 —

```
- [ ] [SCRIPT][BLOCKED-UPSTREAM-OUTAGE] P2. **Retry Transfermarkt's 8 attempted_failed PLAYER_VALUES rows** ...
```

— landed by `085fabcac` (2026-08-08 22:23Z, a live sports-capture session ticking through unrelated smallchunk progress,
pulled into my worktree by an ordinary `git pull --rebase --autostash` mid-task). The
`[SCRIPT][BLOCKED-UPSTREAM-OUTAGE]` combined bracket (no separating space between the two tags) reads to
`_parse_open_todos` (agent-orchestrator's `server/regen_backlog_from_plan.py`) as an undeclared/accidental exclusion —
`excluded: [{"declared": false}]` in the gate's own `--json` output — even though the BLOCKED marker visually looks like
it opens its own bracket. Not independently traced into the actual `_STALE_MARKER_*_RE` regex (that's a real
agent-orchestrator code investigation, out of scope for the docs-only task this was found under).

## Why it matters

This is the exact bug class `ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md` (now archived)
was built to catch: a plan renders a live `- [ ]`, the operator sees tracked work, and AO silently never dispatches it.
If the `[TAG][BLOCKED-<token>]` no-space-combined form is systematically mis-parsed, every existing todo using that
exact authoring style (not just this one sports doc) is silently non-dispatchable — worth a grep across the corpus once
root-caused, not assumed to be a single-doc fluke.

## Recommended decision

Re-baselined `max_zero_dispatchable_docs: 24` → `26` in the same commit as the unrelated fix that surfaced this, per the
gate script's own documented remedy (file + re-baseline, don't hand-raise silently). This is NOT a fix — it just stops
an unrelated, pre-existing regression from blocking every other agent's shipping. A real fix needs: (a) confirm the
exact regex in `regen_backlog_from_plan.py` that decides "declared" vs "accidental" for a `[TAG][MARKER]`-combined
bracket (vs. `[TAG] [MARKER]` with a space, or `[MARKER]` alone) — likely a missing alternative in `_STALE_MARKER_*_RE`;
(b) grep the corpus for other `]\[BLOCKED-`/`]\[DEFERRED-BY-DESIGN`/`]\[stretch` no-space combos to size the blast
radius before fixing; (c) fix the regex + add a regression test; (d) re-run this gate and lower
`max_zero_dispatchable_docs` back down once confirmed clean.

## Todos

- [x] ✅ [BACKEND] P3. **Root-cause + fix the `[TAG][BLOCKED-<token>]` no-space-combined-bracket parse gap in
      `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_parse_open_todos`/`_STALE_MARKER_*_RE`.** Confirm via a
      unit test reproducing `sports_all_vendor_honest_coverage_convergence_2026_08_07.md:175`'s exact tag ordering.
      Repo: agent-orchestrator. — agent-orchestrator@a0eb343. Root cause was actually in
      `server/dispatch_visibility_report.py`'s `_is_declared` (the reporting classifier, not `_parse_open_todos` itself
      — exclusion was already correct via `_has_live_blocked_token`/`_is_non_dispatchable`, which scan the whole todo
      block and were unaffected): `_OPERATOR_TAG_PREFIX_RE`'s greedy `(?:[TAG]|P<n>.)+` repeat matches
      `[BLOCKED-UPSTREAM-OUTAGE]` as just another category-tag-shaped bracket (same `\[[A-Z][A-Z_-]*\]` alternative as
      `[SCRIPT]`), so a combined `[SCRIPT][BLOCKED-UPSTREAM-OUTAGE]` prefix got fully stripped before `_is_declared`'s
      post-strip `head` check ever saw the marker — misclassifying a plainly-declared marker as accidental. Fixed by
      scanning the matched tag-cluster's individual bracket groups for a declared-prefix marker first (mirrors the
      existing `[OPERATOR]`-bracket-cluster scan technique in `regen_backlog_from_plan.py`'s backlog sync). Added
      `test_shape5_combined_bracket_no_space_marker_is_declared` reproducing the exact sports doc line's tag ordering —
      passes, plus all 8 pre-existing `test_dispatch_visibility_report.py` cases still pass. Verified against the live
      corpus: the sports doc's Transfermarkt todo now reports `declared: True`, and
      `check_ao_dispatch_visibility_gate.py` measures 24 accidental exclusions post-fix (was 26) — still ≤ baseline 26,
      so no re-baseline needed for this todo (todo 3 below still applies once the corpus grep in todo 2 is done).
- [x] ✅ [SCRIPT] P3. **Grep the corpus for other `]\[BLOCKED-`/`]\[DEFERRED-BY-DESIGN`/`]\[stretch` no-space combos**
      once the regex root cause is confirmed, to size how many other docs share this same silent-exclusion bug. Repo:
      unified-trading-pm. — `rg -Eon '\]\[(BLOCKED-[A-Z-]+|DEFERRED-BY-DESIGN|stretch)\]' plans/ --include=*.md` (incl.
      archive, for completeness) found exactly 3 no-space occurrences total, ALL in active docs, all `[BLOCKED-*]` shape
      (zero `DEFERRED-BY-DESIGN`/`stretch` no-space hits anywhere in the corpus):
      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md:175` (`[SCRIPT][BLOCKED-UPSTREAM-OUTAGE]`, the
      original find), `sports_satellite_ao_dispatch_batch9_2026_08_04.md:129` (`[DATA][BLOCKED-UPSTREAM-OUTAGE]`), and
      `issues/upbit_cefi_data_gap_may_2026_2026_08_04.md:119` (`[DATA][BLOCKED-CREDENTIALS]`). Re-ran
      `check_ao_dispatch_visibility_gate.py --json` against live HEAD (agent-orchestrator@dd01255, which contains the
      todo-1 fix a0eb343) and confirmed all 3 now report `"declared": true` in the gate's per-doc `excluded[]` — the fix
      is corpus-wide-clean for this exact bug shape, no third instance needs a separate follow-up.
- [x] ✅ [SCRIPT] P3. **Once fixed, re-run `check_ao_dispatch_visibility_gate.py --update-baseline` to ratchet
      `max_zero_dispatchable_docs` back down** from 26 to the newly-clean measured count. Repo: unified-trading-pm. —
      Re-ran live: `zero_dispatchable_docs` measures **26**, exactly at the current baseline (unchanged) — no lower
      count to ratchet to. Root cause: `zero_dispatchable_docs` counts any `disk_open>0 and backlog_open==0` doc
      (`check_ao_dispatch_visibility_gate.py:123`) **regardless of whether its exclusion is `declared` or `accidental`**
      — a doc whose sole open todo is a _correctly_-declared `BLOCKED-*` hold still counts on this axis by design (it's
      the "active plan AO will never touch at all" signal, not the accidental-exclusion bug-class signal — that's
      `max_accidental_exclusions`, a separate axis). Confirmed via the live JSON: the sports doc
      (`disk_open:1, backlog_open:0, excluded:[{declared:true}]`) and the upbit doc (same shape) both still land in the
      26 — correctly, since each really does have zero dispatchable work right now, todo-1's fix or not. So this todo's
      premise (fixing the parser lowers this axis) doesn't hold for THIS bug class; **no `--update-baseline` run
      performed, baseline correctly left at 26**. (Separately, `max_accidental_exclusions` was already re-baselined
      26→34 today by a different agent/commit for an unrelated corpus-drift regression — see
      `scripts/quality_gates/ao_dispatch_visibility_baseline.yaml` git history @6ec2599f6 — not touched here, out of
      this issue's scope.)

## Progress Log

- **2026-08-08**: filed during `ao_satellite_ao_dispatch_batch5-003` (unrelated docs-only §3/§4 closure task) — the
  regression blocked shipping via the standard Pass-1 QG flow; re-baselined in the same commit per this doc's own
  Recommended decision.
- **2026-08-09**: todo 1 shipped — agent-orchestrator@a0eb343. Root cause was in `dispatch_visibility_report.py`'s
  `_is_declared` classifier, not `_parse_open_todos`/`_STALE_MARKER_*_RE` as originally guessed (the exclusion decision
  itself was always correct). See todo 1's own note for the full root-cause + fix summary.
- **2026-08-09**: todos 2+3 closed out — corpus grep found no further `[BLOCKED-*]`/`DEFERRED-BY-DESIGN`/`stretch`
  no-space-combo instances beyond the 2 already-confirmed-fixed docs; `zero_dispatchable_docs` re-measured at 26 (same
  as baseline) with no lower count available to ratchet to, since that axis counts declared exclusions too — see todo
  3's evidence for the full explanation. All todos done, no lock — archiving per the 6-step ritual
  (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).
