---
doc_type: issue
title: >-
  Promote-PR non-supersession after a gate-passing greeks-service re-run — 2 unconfirmed hypotheses, extracted for its
  own scoping
summary: >-
  Extraction of a single surviving open item from
  `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md` (that doc's every other todo is
  done; this was its last open item, blocking na-eligibility-audit's own RECLASSIFY bar). The underlying observation
  (2026-08-07, agt-5f8afe): after `greeks-service@f5a63a8` landed on LDR with every gate log-line reading PASS
  (`quality-gates-v2` run 31157269647 green), stale promotion PR #420 (head=`promote/greeks-service/49b92a1a7ca0`, the
  pre-fix SHA) was not superseded by a fresh per-SHA ref/PR — `process_repo` appears to have exited without reaching a
  `_done` call for the single `ONLY_REPO=greeks-service` item, a different shape from the already-hardened
  `ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md` trigger. Not verified live
  since 2026-08-07 — this doc isolates the question so it can be picked up (or closed as moot/self-resolved) without
  carrying the rest of the parent doc's now-fully-resolved content.
status: archived
superseded_by: /codex/08-workflows/ci-cd-flow.md
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, promote-pr, ldr-to-main, investigation, extracted]
related:
  [
    /plans/archive/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
assigned_role: cicd
drift_direction: advance-code
depends_on: []
supersedes:
context_scope:
  [
    /plans/archive/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    scripts/cicd/ldr_to_main_fleet_promote.sh,
  ]
source: >-
  Extracted by na-eligibility-audit (ci tranche, 2026-08-18) per that skill's own recommendation on
  workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md, 2026-08-08/09 — "split into its own
  bounded issue doc with a concrete done-when" — never executed until now. Also closes ag_closeout_audit_ci_parked_2026_08_16.md's
  Todos item 3 (same recommendation, re-filed 2026-08-16).
resolved_by:
locked_by:
---

> **🗄️ ARCHIVED 2026-08-20** — re-verified live: closed as a one-off, did not recur, no root-cause pass needed. See
> Disposition below for the evidence; read `/codex/08-workflows/ci-cd-flow.md` for current promote-pipeline guidance.

# Promote-PR non-supersession after a gate-passing greeks-service re-run

## What was observed (2026-08-07, not re-verified since)

After `greeks-service@f5a63a8` landed on `live-defi-rollout` (content/TIER-A/SIT/LABEL-CHECK all PASS per
`scripts/cicd/ldr_to_main_fleet_promote.sh --repo greeks-service` re-runs `31156978197` + `31157072912`), the stale
promotion PR #420 (head=`promote/greeks-service/49b92a1a7ca0`, the pre-fix SHA) was NOT superseded by a fresh per-SHA
ref/PR at `f5a63a8` — the run's own summary tallied `Promoted (0)`/`Blocked (0)`/`Conflicted (0)`/
`Auto-merge ARM FAILED (0)` for the single `ONLY_REPO=greeks-service` item despite every gate log-line reading PASS,
i.e. `process_repo` appears to have exited without ever reaching a `_done` call.

**Two unconfirmed hypotheses, neither investigated further**:

1. `ONLY_REPO`-mode-specific gap — the single-repo dispatch path may skip a step the full fleet sweep hits.
2. A race in the frozen-head ref-creation/PR-create path.

**Distinguished from a known, already-fixed bug**: this is NOT the
`ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md` shape — that doc's trigger (a
bare `return 0` after a failed `gh pr create` with no open PR) is already hardened at
`ldr_to_main_fleet_promote.sh:1096-1105`. This looks like a different gap.

**Not blocking at the time** — the repo's actual gate was fixed and verified green directly, and the un-scoped fleet
cron was expected to eventually pick it up regardless of this specific PR's fate.

## What this doc needs before it can be dispatched

This is a genuine open-ended investigation, not bounded/AO-eligible as-is — no confirmed root cause, no stated
done-when beyond "figure out which hypothesis (if either) is correct." Whoever picks this up next should first
re-verify live whether PR #420 (or any successor) is still open/stale on `greeks-service`, and whether this
non-supersession shape has recurred on any other repo since 2026-08-07 — an 11-day-old single occurrence that never
recurred may simply be closable as a one-off, not worth a root-cause pass.

## Todos

- [x] ✅ [DEVOPS] P3. **Re-verified live 2026-08-20 — one-off, did not recur, closed.** `gh pr list --repo
      IggyIkenna/greeks-service --search "chore(promote)" --state all` returns 0 open matches; PR #420 itself is
      `CLOSED` (never merged, `updatedAt=2026-08-07T08:10:33Z`), i.e. no stale PR remains. `gh pr list --state all
      --limit 20` on the same repo shows 20 consecutive `chore(promote)` PRs #484-#503 spanning 2026-08-17→2026-08-20,
      19 `MERGED` cleanly and 1 (`#485`) `CLOSED` as an expected same-head duplicate-supersession six seconds after its
      twin `#484` merged (not the `Promoted(0)/Blocked(0)/Conflicted(0)` shape) — the promote pipeline has run
      continuously and cleanly for this repo since. `gh api repos/IggyIkenna/greeks-service/compare/main...live-defi-rollout`
      shows `ahead_by:386, behind_by:0` — a clean fast-forward relationship, no divergence/stuck state. Fleet-wide,
      `ldr-to-main-promote-fleet.yml` and `promote-fleet-startup-failure-monitor.yml` runs sampled from 2026-08-20 are
      all `conclusion: success`. Corpus-wide grep of `plans/active/issues/` + `plans/archive/issues/` for the same
      failure shape ("Promoted (0)", "non-supersession", "process_repo"/"_done call", "stale promote PR") since
      2026-08-07 turns up no other occurrence on any repo. Several unrelated-but-adjacent hardening fixes landed in
      `ldr_to_main_fleet_promote.sh` within days of the observation (`dbaa7b463a` 2026-08-08 — sweep of orphaned
      `promote/<repo>/*` refs left by manual PR close; `c2f499d082` — auto-recheck of a terminally-red PR instead of
      sitting stuck; `23499c954f` — staggered per-repo fan-out) that plausibly cover this gap's symptom class even
      though neither of the doc's two named hypotheses was directly confirmed/refuted. Per the todo's own stated
      closing criterion ("if it never recurred and no stale PR remains, close this doc as a one-off, not investigated
      further"): closed. No code change required or shipped — this was a pure re-verification, no repo touched.

## Disposition

**Closed as a one-off, 2026-08-20.** The 2026-08-07 non-supersession observed on greeks-service PR #420 never
recurred on this repo or any other in the 13 days since, no stale ref/PR remains, and the promote pipeline has run
cleanly and continuously for greeks-service (20 consecutive promote PRs, 19 merges + 1 expected duplicate-close) and
fleet-wide since. Neither of the doc's two hypotheses (`ONLY_REPO`-mode-specific gap vs. a frozen-head ref-creation
race) was root-caused — both remain unconfirmed — but per the doc's own stated bar, an 11+-day-old single occurrence
with zero recurrence does not warrant a root-cause pass. If this shape recurs again, re-open referencing this doc's
evidence trail rather than re-deriving it from scratch.

## Progress Log

- **2026-08-18 (na-eligibility-audit, ci tranche)**: extracted verbatim from
  `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`'s last open item, per that doc's
  own 2026-08-08/09 na-eligibility-audit recommendation ("split into its own bounded issue doc with a concrete
  done-when") and `ag_closeout_audit_ci_parked_2026_08_16.md` Todos item 3 (same ask, re-filed). No new investigation
  performed this pass — content is a verbatim carry-forward; the parent doc's todo is flipped `[x]` citing this
  extraction.
- **na-eligibility-audit 2026-08-18 (ci tranche)**: KEEP-NA, valid — 1 open todo (verified via `grep -nE
  '^[[:space:]]*[-*] \[ \]'`, matches). The todo bundles a bounded read-only re-verify step with an unbounded
  conditional tail ("if it has recurred, root-cause between the two named hypotheses above") that names no
  worker-determinable stopping criterion — does not clear the RECLASSIFY bounded-outcome bar as a whole, matching
  the doc's own "What this doc needs before it can be dispatched" self-assessment, confirmed on independent review
  rather than trusted blind. Tagged `GENUINE_WORK` (unblocked investigation; not an operator business/value
  judgment, no credential gap, no dependency block). No conflict-check needed (no RECLASSIFY candidate). No
  stale-checkbox correction needed (todo accurately reflects zero investigation done since extraction).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries).
- **T4-execution-settlement (2026-08-20)**: re-verified live per the open todo's own instructions (see evidence in the
  flipped todo above) — no stale PR, no recurrence anywhere in the corpus or fleet since 2026-08-07. Closed as a
  one-off; todo flipped `[x]`, doc archived per the CLAUDE.md "archive the moment a plan/issue is genuinely done" hard
  rule (0 open todos, unlocked). `superseded_by: /codex/08-workflows/ci-cd-flow.md` (no new durable contract was
  established by this closure — nothing to add to codex beyond what that SSOT already governs). Moved
  `plans/active/issues/` → `plans/archive/issues/` (flat, per `issue-doc-lifecycle.md`). Referrer check: 3 docs
  mention this path in body prose (`plan_reconciler_findings_ci_2026_08_19.md:184`,
  `plan_reconciler_findings_prediction_2026_08_18.md:297`) or in `context_scope:` (`ag_closeout_audit_ci_parked_2026_08_16.md:56`)
  — none has it in the mechanically-ratcheted `related:` frontmatter field (`check_active_refs_archived_plans.py`'s
  actual enforcement scope), verified directly via `sed -n '/^related:/,/^[a-z_]*:/p'` on each of the 3, so nothing
  required fixing for the archival ratchet; the body-prose mentions are correct as dated historical audit record and
  were left as-is.
