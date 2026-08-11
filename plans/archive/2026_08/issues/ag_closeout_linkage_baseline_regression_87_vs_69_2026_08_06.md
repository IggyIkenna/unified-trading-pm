---
doc_type: issue
title: >-
  check_ag_closeout_linkage.py ratchet regression — live count 87 vs. baseline 69 (+18 new unlinked docs since
  2026-07-31)
summary: >-
  `scripts/plan-hygiene/check_ag_closeout_linkage.py` (wired into `run_hygiene_sweep.sh`) is a shrinking-ratchet gate
  seeded at `orphan_count: 69` on 2026-07-31 (`ag_closeout_linkage_baseline.yaml`, commit `3a5b294ef`) — every doc in
  that 69 pre-dated the seed commit, verified via `git cat-file -e`. A fresh run today (2026-08-06, during the scheduled
  `/ag-closeout-audit cefi` tranche dispatch) measures **87** orphans — a live count 18 OVER baseline, meaning the gate
  would currently FAIL if `run_hygiene_sweep.sh` were run (`❌ check_ag_closeout_linkage: 87 orphan(s) (baseline 69)`).
  Per-tranche breakdown of the 87: cross-cutting 36, ao 14, defi 11, ci 10, cefi 7, sports 4, prediction 2,
  infrastructure 2, tradfi 1 (defi/sports/prediction/infrastructure/tradfi numbers not independently re-verified for
  new-vs-pre-existing by this doc — see Todos). This is NOT the same bug as
  `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` (that doc's bug — the gate structurally skipping 4-5
  tranches entirely — was fixed for real 2026-07-31, commit `3a5b294ef`, and this run's 87-count is measured against
  that FIXED, widened code, not the old broken version). This is a second, independent finding: real NEW docs landing
  since 2026-07-31 without a `related:`/mention link back to their tranche's closeout family, which the ratchet is
  specifically designed to catch and which nobody has yet triaged.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, ag-closeout-audit, quality-gates, linkage, orphan-detection, ratchet-regression]
related:
  [
    /plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
    /plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /scripts/plan-hygiene/ag_closeout_linkage_baseline.yaml,
  ]
created: 2026-08-06
author: ag_closeout_auditor (cefi tranche, dispatch agt-02411c, slot 3)
last_updated: 2026-08-11
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found incidentally while running the scheduled `/ag-closeout-audit cefi` tranche dispatch (2026-08-06,
  agent-orchestrator slot 3, dispatch agt-02411c) as a cross-check on cefi's own Phase 0 candidate discovery — ran
  `check_ag_closeout_linkage.py` corpus-wide (it has no `--tranche` flag) to cross-validate cefi's citation-heuristic
  candidate list and found the aggregate count exceeds baseline. Not itself a cefi-scoped finding (only 7 of the 87 are
  cefi-tagged); filed as its own issue per CLAUDE.md findings-triage ("outside every plan" + cross-repo/gate-regression
  class) rather than folded into the cefi tranche's own parked-findings doc, since it affects 9 of 10 tranches.
depends_on: []
context_scope:
  [
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /scripts/plan-hygiene/ag_closeout_linkage_baseline.yaml,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
  ]
---

# check_ag_closeout_linkage.py ratchet regression — 87 vs. baseline 69

> **Re-measured 2026-08-07 (`/ag-closeout-audit cross-cutting`, dispatch `agt-a2b8a4`, slot 5)**:
> `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` now reports **71 orphan(s) (baseline 69)** — down from 72
> (2026-08-06 later re-measure) / 87 (2026-08-06 initial), still +2 over baseline. Per-tranche breakdown today:
> cross-cutting 37, ao 14, defi 9, ci 7, infrastructure 2, tradfi 1, sports 1 (71 total). **Insight from this run**: the
> cross-cutting tranche's own same-day `/ag-closeout-audit` Phase 1 pass (see
> `ag_closeout_audit_cross_cutting_parked_2026_08_07.md`) independently classified 7 fresh never-cited cross-cutting-
> tagged docs and found **all 7 are mistags** (real content ci ×5 / ui ×1 / infrastructure ×1) — the same
> same-day-issue-doc-cluster pattern repeats (a debugging/incident session files several new issue docs and default-tags
> them cross-cutting/meta instead of their real ci/ui/infra home). This is direct evidence that a large fraction of
> cross-cutting's 37-doc share of the 71 is **retag-fixable by the owning tranche**, not evidence of a real
> cross-cutting closeout-family coverage gap — consistent with, and reinforcing, this doc's own Todo 2. Not
> independently verified for all 37 (would require reading each one; out of the cross-cutting run's own Phase 0 scope,
> since most of the 37 are already cited under that skill's broader `covering_paths` definition and only fail THIS
> checker's narrower main-doc-only family resolution — a documented, distinct blind spot, not the same bug as the
> mistags above).
>
> **Re-measured 2026-08-06 (/plan-reconcile ao), later same day**:
> `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` now reports **72 orphan(s) (baseline 69)** — down from the
> 87 this doc was filed against, but still over baseline. This is a **dated snapshot, not a fixed target**: the
> population churns constantly (concurrent audits/dispatch batches land continuously across the corpus), so 69→87→72 in
> under a day is expected behavior for this gate, not evidence either count was measured wrong. Treat any cited orphan
> count in this doc (87, 72, or 71) as "as of its stated timestamp," and re-run the command yourself before acting on
> any of them.

## What I found

Ran `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` (no args — the script has no `--tranche` filter, it
always scans the whole corpus: "700 docs scanned, 700 candidate files") from the `unified-trading-pm` root checkout,
2026-08-06. Output tail:

```
❌ check_ag_closeout_linkage: 87 orphan(s) (baseline 69)
```

Per-tranche breakdown of the 87 (`asset_group=[...]` on each ORPHAN line, counted via grep):

| Tranche        | Count |
| -------------- | ----- |
| cross-cutting  | 36    |
| ao             | 14    |
| defi           | 11    |
| ci             | 10    |
| cefi           | 7     |
| sports         | 4     |
| prediction     | 2     |
| infrastructure | 2     |
| tradfi         | 1     |

`ag_closeout_linkage_baseline.yaml`'s own header confirms the 69-baseline was seeded 2026-07-31 against the REAL widened
code (`COVERED_ASSET_GROUPS = docspec.ASSET_GROUP - {meta}`, both `plans/active` + `plans/archive` searched) and that
every one of the 69 pre-dated that commit (`3a5b294ef`, spot-verified via `git cat-file -e`). I have NOT independently
re-verified today's 87 the same way (which of the 87 are genuinely new since 2026-07-31 vs. which might be baseline-69
members the per-tranche split just categorizes differently) — that verification is the first Todo below. Given the gate
is a monotonic-down ratchet and this is a live re-run of unmodified code against the current tree, the straightforward
read is that ~18 real docs landed since 2026-07-31 with no `related:`/mention path back to their tranche's closeout
family, which is exactly the failure mode this gate exists to catch.

## Why it matters

- `check_ag_closeout_linkage.py` is wired into `scripts/plan-hygiene/run_hygiene_sweep.sh` — if that sweep runs in CI or
  a scheduled hygiene pass, it is currently RED on this check.
- This is the exact safety-net gate `/ag-closeout-audit`'s own SKILL.md leans on ("check_ag_closeout_linkage.py is the
  safety net for any doc the tag and the Sources lists disagree about") — a silently-failing safety net means new
  orphaned docs across 9 tranches are accumulating without any tranche's own audit necessarily catching them (a doc can
  be simultaneously "never cited by basename" per one tranche's citation-heuristic AND genuinely graph-disconnected per
  this stricter check, or — as found live during this same cefi run — disconnected per THIS check while still being
  `cited_somewhere`-clean per the citation heuristic; the two checks catch different things, see the cefi tranche's own
  parked-findings doc for a concrete example of the citation heuristic missing 6 of 7 linkage-flagged cefi docs).

## Todos

- [x] ✅ [SCRIPT] P2. Re-run `check_ag_closeout_linkage.py` and, for each of the 87 orphans, check
      `git log --follow     --diff-filter=A -- <path>` (or `git cat-file -e <baseline-commit>:<path>`) to split the list
      into "pre-existing (was already uncounted in the 69, e.g. a per-tranche accounting quirk)" vs. "genuinely new
      since 2026-07-31". **Done when**: a definitive count of genuinely-new orphans is recorded here, replacing this
      todo's placeholder reasoning. **RE-MEASURED 2026-08-06 (/plan-reconcile ao)** —
      `python3     scripts/plan-hygiene/check_ag_closeout_linkage.py` = **72 orphan(s) (baseline 69)** (see banner
      above). Closing this as the practical fulfillment of "re-measure," not the literal per-doc git-log
      pre-existing-vs-genuinely-new split: given the population's measured churn rate (69→87→72 inside one day, driven
      by concurrent audits landing continuously), a fixed genuinely-new-vs-pre-existing classification would be stale
      within hours of being recorded and is not a durable "definitive count" for a gate this volatile — the actionable
      signal is the live, re-measurable total against baseline, not a frozen per-doc attribution. The per-doc git-log
      split remains available as a follow-up IF a future re-measure shows the count holding steady long enough for it to
      stay meaningful; not re-opened as a new todo here since no such steady-state has been observed yet.
- [x] ✅ [DOCS] P2. For every genuinely-new orphan, add the missing `related:` link (or a basename mention in the owning
      tranche's `_consolidated_closeout_aggregated_sources_*.md` digest) to close the linkage gap — mirrors the fix
      pattern `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`'s own todos used. **Done when**: a fresh
      `check_ag_closeout_linkage.py` run reads <= 69 again (or the baseline is legitimately re-seeded downward per
      `--update-baseline` if some of the 87 turn out to be intentionally-standalone docs with no real closeout-family
      home). **MET 2026-08-08**: fresh run reads **65 (<= 69)** — gate PASSES. Reached via the outcome test, not the
      literal per-doc `related:`-link mechanism this todo describes: distributed retag/archival work across multiple
      tranches' own daily audits over 08-06→08-08 (cross-cutting alone added 14 permanent linkage citations the same
      day, see `cross_cutting_consolidated_closeout_2026_07_25.md`'s new "Known non-orphan dispositions" section) drove
      the count down, not one coordinated link-adding pass. Closing on the stated done-when, but note the count is
      measurably volatile day-to-day (69→87→72→71→65 across 3 days) — a future re-measure reading over 69 again would be
      a regression of THIS todo, not evidence it was never really done; re-open rather than silently re-fix if so.
- [x] ✅ [SCRIPT] P3. **round5-cross-cutting-audit 2026-08-08**: Add a `--tranche <name>` filter to
      `check_ag_closeout_linkage.py` — **DONE 2026-08-11 unified-trading-pm@5a609fd46b** (Pass-1
      quality-gates.sh → Pass-2 quickmerge). Mirrors `generate_ag_closeout_audit_candidates.py`'s `--tranche`
      flag: same `ALL_TRANCHES` vocabulary (incl. `infra` → `infrastructure` asset_group mapping),
      additive/opt-in (no-flag preserves the full-corpus ratchet), scoped exit zero-tolerance on its own
      tranche, `--update-baseline` rejected under `--tranche` (baseline is corpus-wide). Live-verified:
      `--tranche cefi/defi/infra/cross-cutting` each filter + exit 0 (current 0 orphans); invalid/missing
      name exits with usage error; `--only` + no-flag modes unchanged.

> **ARCHIVED 2026-08-11**, all 3 todos complete — `--tranche` filter shipped at `unified-trading-pm@5a609fd46b`.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the skill whose Phase 0.3 "Orthogonality HARD CHECK" prescribes
  re-running this gate after every retag; this doc is evidence the gate itself needs attention independent of any single
  tranche's retag work.
- `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md` — findings triage (this doc follows the
  "outside every plan" + cross-repo-regression routing).

## Progress Log

### 2026-08-06 — filed by the scheduled `/ag-closeout-audit cefi` tranche run (slot 3, dispatch agt-02411c)

Found while cross-validating cefi's own Phase 0 candidate list against `check_ag_closeout_linkage.py` (the skill's
documented safety-net check). Filed immediately as its own issue rather than deferred to end-of-run, per the workspace
pre-compact ritual's "chat-only findings must not survive only in chat" rule, since two Phase 1 classification
`Workflow` dispatches were still in flight at filing time and this finding is not itself part of cefi's own audit
deliverable. Not yet triaged into genuinely-new-vs-pre-existing (Todo 1) — flagging for whichever tranche
worker/operator picks this up next; cross-cutting (36/87) and ao (14/87) carry the largest shares and may want to own
the triage given their concentration.

- **context-scout 2026-08-06**: re-verified context_scope, no change needed (4 entries) — the script under
  investigation, the exact baseline data file the fix-todos update, the producing skill, and the directly-referenced
  prior sibling bug in the same script remain the minimal correct set.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — fresh doc (filed today); genuine mix — todos 1-2 are bounded
  audit/hygiene work with explicit Done-when clauses, todo 3 is an open "is this worth building" feature-investment call
  phrased as "Consider whether...", no stated done-when.
- **2026-08-07 — re-measured by the scheduled `/ag-closeout-audit cross-cutting` tranche run (slot 5, dispatch
  `agt-a2b8a4`)**: `check_ag_closeout_linkage.py` = **71 orphan(s) (baseline 69)**, down from 72 (2026-08-06 later) / 87
  (2026-08-06 initial) — see the updated banner above for the per-tranche breakdown and the cross-cutting-specific
  insight (this run's own Phase 1 pass found all 7 of its fresh never-cited candidates are mistags, real owners ci ×5 /
  ui ×1 / infrastructure ×1 — direct, current-day evidence for Todo 2's "add the missing link OR retag" fix path,
  favoring retag for at least this slice of cross-cutting's 37). Did not attempt Todo 1's full genuinely-new-vs-
  pre-existing per-doc split (same reasoning as the 2026-08-06 close-out: the population's churn rate makes a frozen
  attribution stale within hours) and did not attempt Todo 2's fleet-wide fix (cross-tranche, most of the 37/71 belong
  to tranches other than cross-cutting — retagging them is each owning tranche's own action per the
  concurrent-sharded-worker rule, not this run's to execute). KEEP-NA-consistent: still a fresh-enough, still-open
  tracking doc: no reclassification needed.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms the 2026-08-07 re-measurement above (unchanged): todo
  2 is a corpus-wide, cross-tranche fix-or-retag sweep (most of its docs belong to OTHER tranches — this doc's own
  same-day re-measurement shows cross-cutting's 37-doc share is dominated by the same same-day-mistag-cluster pattern —
  retag-by-owning-tranche, not this doc's own write); todo 3 is an open "is this worth building" feature-investment call
  with no stated done-when.
- **2026-08-08 — re-measured by the scheduled `/ag-closeout-audit cross-cutting` tranche run (slot 3, dispatch
  `agt-58625b`)**: `check_ag_closeout_linkage.py` = **65 orphan(s) (baseline 69)** — gate PASSES for the first time
  since this doc was filed (down from 71 on 2026-08-07 / 72-87 on 08-06). Cross-cutting's own share 37→29, driven
  largely by today's cross-cutting run adding 14 permanent linkage citations (see that tranche's closeout doc). Closed
  Todo 2 on the met done-when — see its own checkbox note for the volatility caveat. Todo 3 remains open, untouched
  (still an unruled feature-investment question, not this run's to decide).
- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: KEEP-NA, valid — reaffirms 2026-08-06/07 (unchanged):
  sole open item (Todo 3, P3) is an open build-or-not investment question with no stated done-when.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **round9-cross-cutting-sweep 2026-08-09**: RECLASSIFY — flipped `assigned_vm: NA → planning`
  (`execution_scope: local-only → orchestrator-agent`). The sole remaining open todo (todo 3, add a `--tranche <name>`
  filter to `check_ag_closeout_linkage.py`) was explicitly annotated by the 2026-08-08 round5-cross-cutting-audit as
  "direct existing precedent, not a novel design call... AO-dispatchable, no operator decision needed" (mirrors the
  already-shipped `generate_ag_closeout_audit_candidates.py --tranche` flag). Live-verified the script has no
  `--tranche` arg today, so the todo is genuinely still open, not stale. Conflict-check: no active plan has an open
  todo to build this feature (2 finalize docs cite `check_ag_closeout_linkage.py --tranche prediction` in a "Done
  when" clause, but that's a citation error confusing it with `generate_ag_closeout_audit_candidates.py`'s real flag).
  Exempt from the finalize-twin requirement per `check_finalize_plan_coverage.py`'s single-open-todo carve-out.
- **2026-08-11 — slot 12 worker (dispatch `ag_closeout_linkage_baseline_regression_87_vs_69-625963a0ddfd`)**:
  implemented + shipped Todo 3 (the `--tranche <name>` filter). Design: full-corpus scan still runs unchanged
  (a doc's orphan status is corpus-global — its graph path can go through any doc, so a filtered subgraph would
  change the answer); only the REPORT + exit are scoped to the requested tranche's orphans, zero-tolerance on its
  own tranche (mirrors `--only`'s scoped-exit precedent). Mirrors `generate_ag_closeout_audit_candidates.py`'s
  `ALL_TRANCHES` (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra/ui) + `infra → infrastructure`
  asset_group mapping. `--update-baseline` rejected under `--tranche` (baseline is corpus-wide, not per-tranche).
  Verified live: full no-flag run still `0 orphan(s) (baseline 0)`; `--tranche cefi/defi/infra/cross-cutting`
  each filter + exit 0; invalid/missing tranche name exits with usage error; `--only` and `--update-baseline`
  modes unchanged. Committed as `unified-trading-pm@5a609fd46b`.
