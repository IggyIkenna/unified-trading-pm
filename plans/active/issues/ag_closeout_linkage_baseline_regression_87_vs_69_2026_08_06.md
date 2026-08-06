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
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, ag-closeout-audit, quality-gates, linkage, orphan-detection, ratchet-regression]
related:
  [
    /plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
    /plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /scripts/plan-hygiene/ag_closeout_linkage_baseline.yaml,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-06
author: ag_closeout_auditor (cefi tranche, dispatch agt-02411c, slot 3)
last_updated: 2026-08-06
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
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
    /plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
  ]
---

# check_ag_closeout_linkage.py ratchet regression — 87 vs. baseline 69

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

- [ ] [SCRIPT] P2. Re-run `check_ag_closeout_linkage.py` and, for each of the 87 orphans, check
      `git log --follow     --diff-filter=A -- <path>` (or `git cat-file -e <baseline-commit>:<path>`) to split the list
      into "pre-existing (was already uncounted in the 69, e.g. a per-tranche accounting quirk)" vs. "genuinely new
      since 2026-07-31". **Done when**: a definitive count of genuinely-new orphans is recorded here, replacing this
      todo's placeholder reasoning.
- [ ] [DOCS] P2. For every genuinely-new orphan, add the missing `related:` link (or a basename mention in the owning
      tranche's `_consolidated_closeout_aggregated_sources_*.md` digest) to close the linkage gap — mirrors the fix
      pattern `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`'s own todos used. **Done when**: a fresh
      `check_ag_closeout_linkage.py` run reads <= 69 again (or the baseline is legitimately re-seeded downward per
      `--update-baseline` if some of the 87 turn out to be intentionally-standalone docs with no real closeout-family
      home).
- [ ] [SCRIPT] P3. Consider whether `check_ag_closeout_linkage.py` should gain a `--tranche <name>` filter (mirroring
      `generate_ag_closeout_audit_candidates.py`'s own flag) so a single-tranche `/ag-closeout-audit` dispatch can
      cheaply cross-check just its own tranche instead of paying the full 700-doc corpus-wide scan cost every run — a
      real, measured cost this run incurred (the scan surfaced 80 non-cefi orphans irrelevant to a cefi-scoped
      dispatch).

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
