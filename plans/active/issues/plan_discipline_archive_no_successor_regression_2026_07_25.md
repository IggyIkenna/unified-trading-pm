---
doc_type: issue
title:
  "check_plan_discipline.py C-archive-no-successor ratchet regressed 0->5, blocking unified-trading-pm's own
  quality-gates.sh (discovered while shipping the archival-ritual link-check hardening)"
summary: >-
  Discovered while running `bash scripts/quality-gates.sh` on unified-trading-pm to ship an unrelated fix
  (consolidated_closeout_plans_stale_archive_referrer_links_fleetwide_qg_block-001's remaining todo). The "Plan
  discipline check" post-gate step (`scripts/quality_gates/check_plan_discipline.py`) fails with 5
  `C-archive-no-successor` violations against a baseline of 0 — 5 docs already sitting in `plans/archive/` mention
  DEFERRED/post-cutover/out-of-scope language without a machine-detectable successor pointer (`MIGRATED
  TO:`/`successor:`/`→ plans/active/...`). Confirmed pre-existing (reproduces on a clean tree with my diff stashed) and
  NOT caused by my change — my diff only touches `scripts/plan-hygiene/run_hygiene_sweep.sh` and
  `scripts/validators/validate_plan_links.py`, neither of which this checker reads. Repo-scoped, not fleet-wide:
  `check_plan_discipline.py` is invoked only from unified-trading-pm's own `scripts/quality-gates.sh` (not from the
  shared `base-service.sh`/`base-library.sh` every other repo sources), so this blocks unified-trading-pm's own
  quickmerge sentinel, not every repo's.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plans, qg, plan-discipline, archive, ratchet, p1]
related: []
created: 2026-07-25
parent_epic: infrastructure_master
priority: P1
source:
  "Found 2026-07-25 (slot 8, infra) while shipping
  consolidated_closeout_plans_stale_archive_referrer_links_fleetwide_qg_block-001's remaining [SCRIPT] todo."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by: slot-6
---

# check_plan_discipline.py C-archive-no-successor ratchet regression (0->5)

## What I found

`bash scripts/quality-gates.sh` in unified-trading-pm fails its "Plan discipline check (ratchet mode)" post-gate step:

```
Scanned plans/active/ (209 plans) + issues + archive — 5 violation(s).
Per-rule: {'C-archive-no-successor': 5}
❌ Regression: 5 > baseline 0.
```

The 5 flagged files (`scripts/quality_gates/plan_discipline_baseline.yaml` `violation_count: 0`):

- `plans/archive/terminal_status_archival_backlog_sweep_2026_07_25.md`
- `plans/archive/defi_consolidated_closeout_history_2026_07_25.md`
- `plans/archive/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md`
- `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md`
- `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md`

Verified pre-existing and unrelated to my task: `git stash`'d my two-file diff, re-ran
`python3 scripts/quality_gates/check_plan_discipline.py`, got the identical 5-violation, byte-identical failure on the
clean tree; restored my diff afterward.

## Why it matters

Blocks unified-trading-pm's own `quality-gates.sh`-green sentinel, which blocks `quickmerge --agent` for ANY
unified-trading-pm code/script commit (the sentinel requires a full green run on the exact HEAD sha). Confirmed via grep
that `check_plan_discipline.py` is invoked only from unified-trading-pm's own `scripts/quality-gates.sh` (line 513), NOT
from the shared `scripts/quality-gates-base/base-service.sh`/`base-library.sh` every other repo sources — so unlike the
sibling issue doc (`consolidated_closeout_plans_stale_archive_referrer_links_fleetwide_qg_block_2026_07_25.md`), this is
PM-repo-scoped, not fleet-wide. Still P1: it stops any PM-repo script/code work (including the archival-hygiene
hardening this was found while shipping) from landing via the normal flow.

## Why this wasn't independently confirmed as a standing/known issue

Not investigated per-file: for each of the 5, whether the DEFERRED/post-cutover/out-of-scope regex hit is a genuine
missing-successor gap (the archived doc really does describe work now living in a different, unreferenced plan) or a
check false-positive (the phrase is ordinary in-document scoping prose — e.g. "out of scope for a single-line path fix"
— not a claim that the WHOLE archived doc's remaining work moved elsewhere). A skim of the grep hits leans
false-positive for most of the 5 (see `## Recommended fix` below), but this needs a per-file read before acting, not a
bulk re-baseline.

## Recommended fix

Per file, read the flagged DEFERRED/post-cutover/out-of-scope mention(s) in context and either:

- (a) it genuinely names a successor plan in prose already → add the exact machine-matched marker
  (`**MIGRATED TO:** <path>` / `successor: <path>` / `→ plans/active/<path>`) pointing at it, or
- (b) the archived doc's overall remaining/deferred work truly has no successor yet → file the missing successor work as
  a fresh plan/issue-doc todo, then add the marker pointing at it, or
- (c) it's a check false-positive (ordinary prose, not a whole-doc deferral claim) → do NOT hand-edit the checker's
  regex to route around it case-by-case; instead flag it to the operator/main agent for a `--baseline-write` call
  (re-baselining is a human/main-agent judgment call per the checker's own remedy line, not a routine worker fix — a
  worker silently baseline-writing away violations defeats the ratchet's purpose).

## Todos

- [x] ✅ [DOCS] P1. Resolve the `C-archive-no-successor` flag on
      `plans/archive/terminal_status_archival_backlog_sweep_2026_07_25.md` (line ~319 `## Deferred` / ~335 "out of scope
      for a single-line path fix") per the (a)/(b)/(c) triage above. **Case (a)**: the genuinely-open referrer-fix gap
      it describes was already tracked as a P3 todo in `plans/active/issues/reference_path_convention_2026_07_23.md`
      (found by grepping the exact referrer filename) — added a `**MIGRATED TO:**` marker pointing there. —
      unified-trading-pm (this commit)
- [x] ✅ [DOCS] P1. Resolve the `C-archive-no-successor` flag on
      `plans/archive/defi_consolidated_closeout_history_2026_07_25.md` (line ~459 "out of scope" re: Track 6 of
      `cefi_consolidated_closeout_2026_07_18.md` — likely case (a), the successor is already named in prose, just not in
      a machine-matched form) per the (a)/(b)/(c) triage above. **Case (a) confirmed** — added a
      `**MIGRATED TO:**     plans/active/cefi_consolidated_closeout_2026_07_18.md` (Track 6) marker at the existing
      prose mention. — unified-trading-pm (this commit)
- [x] ✅ [DOCS] P1. Resolve the `C-archive-no-successor` flag on
      `plans/archive/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (line ~311 "out of scope here") per
      the (a)/(b)/(c) triage above. **Case (a)**: the doc's own SUPERSEDED banner already named the successor
      (`sports_consolidated_closeout_2026_07_19.md`) in prose; added a `**MIGRATED TO:**` marker into that same banner
      pointing at its `plans/active/` path. — unified-trading-pm (this commit)
- [x] ✅ [DOCS] P1. Resolve the `C-archive-no-successor` flag on
      `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md` (line ~281 "out of scope for a
      launcher task") per the (a)/(b)/(c) triage above. **Case (a)**: the "filed as its own P2 todo" claim resolved to
      `plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` (found by grepping "swap-event indexer");
      also pointed at this log's still-active parent `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md` (Part 1
      of 6 of its extracted history — any other open thread continues there). — unified-trading-pm (this commit)
- [x] ✅ [DOCS] P1. Resolve the `C-archive-no-successor` flag on
      `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md` (line ~590/~745 "out of scope")
      per the (a)/(b)/(c) triage above. **Case (a)**: both mentions (the perp_funding 429-fix todo and the
      not-yet-diagnosed drift-walker stall) trace to the same still-active parent
      `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md` (Part 3 of 6 of its extracted history; the perp_funding
      issue doc itself is `status: resolved` and already lists that same parent as its `related:`) — added a
      `**MIGRATED TO:**` marker. — unified-trading-pm (this commit)
- [x] ✅ [SCRIPT] P2. Once all 5 above are resolved, re-run `python3 scripts/quality_gates/check_plan_discipline.py` to
      confirm 0 violations, then decide with the operator/main agent whether any surviving false-positive class warrants
      a regex refinement in `check_plan_discipline.py` (vs. per-doc markers) so this doesn't recur every time an
      operational log gets archived with ordinary "out of scope" scoping prose. **Re-ran: 0 violations, at baseline
      (0).** No surviving false-positive class — all 5 had a genuine, locatable successor already in the corpus (4 were
      already named in the flagged prose itself, just not in the checker's machine-matched shape; the 5th was findable
      by grepping the "filed as its own... todo" claim), so **no regex refinement is warranted** — this was an archival
      ritual completeness gap (missing `## Deferred work — migrated to:`-style markers), not a checker bug. Sample of
      201 other `plans/archive/*.md` docs matching the same `out of scope`/`post-cutover` tokens: 196 already pass via
      an existing successor reference somewhere in the doc, consistent with "add the marker" being the right fix, not
      "loosen the regex." — unified-trading-pm (this commit)

## Codex SSOTs

No dedicated SSOT; the checker's own docstring cites `governance_qg_automation_gaps_post_cutover_2026_05_12.md` § Group
A as its origin. The archival ritual itself is in workspace `CLAUDE.md` § "Plans — format + authoring discipline".
