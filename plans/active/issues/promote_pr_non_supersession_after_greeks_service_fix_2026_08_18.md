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
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, promote-pr, ldr-to-main, investigation, extracted]
related:
  [
    /plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
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
    /plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
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

- [ ] [DEVOPS] P3. **Re-verify live whether this is still relevant** — check `gh pr list --repo IggyIkenna/greeks-service
      --search "chore(promote)"` for any stale/superseded promote PR, and grep recent `ldr_to_main_fleet_promote.sh`
      run logs for the same `Promoted (0)/Blocked (0)/Conflicted (0)` shape on any repo since 2026-08-07. If it never
      recurred and no stale PR remains, close this doc as a one-off, not investigated further. If it has recurred,
      root-cause between the two named hypotheses above.

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
