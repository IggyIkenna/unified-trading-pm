---
doc_type: issue
title: unified-trading-pm QG red — evidence-backed-completion sub-rule C (96>93) + agent-orchestrator swallowed-credential-fetch (4>2) regressions
summary: >-
  quality-gates.sh for unified-trading-pm currently fails two independent baselined-ratchet
  regressions, neither touching any file this session's task diff modified: (1) prod-data-mutation
  "- [x]" claims without Evidence: citations rose to 96 (baseline 93, +3); (2)
  agent-orchestrator/scripts/orchestrator-liveness-guard.sh:74,78 introduced 2 new
  swallowed-credential-fetch sites (4 vs baseline 2, that repo's own count was 0 before). Both block
  ANY unified-trading-pm ship right now, regardless of the shipping diff's own content.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [quality-gates, ratchet-regression, evidence-backed-completion, swallowed-credential-fetch, repo-blocker]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md,
  ]
created: 2026-08-22
author: agent
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source: [interactive session slot 10, 2026-08-22, discovered while shipping bare_root_repo_agent_writes_unenforced_2026_08_21.md's P1 item]
resolved_by:
locked_by:
context_scope:
  [
    unified-trading-pm/scripts/quality_gates/check_evidence_backed_completion.py,
    unified-trading-pm/scripts/quality_gates/check_no_swallowed_credential_fetch.py,
    agent-orchestrator/scripts/orchestrator-liveness-guard.sh,
  ]
---

## What I found

Running `bash scripts/quality-gates.sh` for `unified-trading-pm` on a clean `live-defi-rollout` HEAD
(`9a04be1e56` — an unrelated dev-scripts change, see below) fails 2 post-gate checks:

1. **Evidence-backed-completion, sub-rule C** (`check_evidence_backed_completion.py`): 96
   prod-data-mutation `- [x]` claims lack a verifiable `Evidence:` artifact ref, vs baseline 93 —
   a +3 regression. Reproduce: `python3 scripts/quality_gates/check_evidence_backed_completion.py
   --workspace-root <ws>` (from `unified-trading-pm/`). Sub-rule B (runtime-green claims) is fine
   (5, well under its baseline of 10) — only sub-rule C regressed.
2. **Swallowed-credential-fetch** (`check_no_swallowed_credential_fetch.py`): `agent-orchestrator`
   has 4 sites vs baseline 2 — a +2 regression, both new sites cited at
   `scripts/orchestrator-liveness-guard.sh:74` and `:78`. Every other repo, including
   unified-trading-pm itself (11 == baseline), is clean. Reproduce:
   `python3 scripts/quality_gates/check_no_swallowed_credential_fetch.py --workspace-root <ws>`.

## Why it matters

Both are ratchet-baselined ("NEVER raise a count") post-gate checks inside unified-trading-pm's OWN
`quality-gates.sh` — a repo-wide corpus/fleet scan, not a diff-scoped one. Because both are
currently over baseline, **quality-gates.sh exits non-zero for EVERY unified-trading-pm ship attempt
right now**, regardless of what that ship's own diff touches — this blocks the whole fleet's PM
shipping, not just this session. Confirmed via direct inspection that neither regression overlaps
this session's own diff (`scripts/dev/slot-git-status-report.sh` +
`tests/test_slot_git_status_root_dirty_watchdog.bats`, commit `9a04be1e56`): the evidence-completion
hits are all in `plans/active/*.md` files this diff never touched, and the swallowed-credential-fetch
hits are in a different repo's script this diff never touched — so this is genuinely pre-existing on
the tree, not introduced by shipping through it.

## Recommended decision

- [ ] [BACKEND] P1. **Root-cause + fix the 2 new swallowed-credential-fetch sites** in
      `agent-orchestrator/scripts/orchestrator-liveness-guard.sh:74,78` — surface the real error
      (log it, exit non-zero) instead of degrading to an empty string via `2>/dev/null || true`,
      per `plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`'s
      SSOT rule (or add `# noqa: swallowed-credential-fetch` with a one-line reason if the
      degrade-silently behavior is genuinely intentional there). Re-run
      `python3 unified-trading-pm/scripts/quality_gates/check_no_swallowed_credential_fetch.py
      --workspace-root <ws>` to confirm `agent-orchestrator: 2 (== baseline)` afterward. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P1. **Isolate + resolve the 3 new sub-rule-C evidence-less prod-data-mutation
      claims** — the checker prints all 96 current violations but not a diff against the prior
      baseline; correlate by recent commit timestamps on `plans/active/*.md` (files touched by
      commits landed since the check's baseline was last written) to find the 3 new ones. For each:
      add a real `Evidence: manifest-delta=<path>|vm-log=<path>|gcs-op=<id>|state-list=<before>,<after>`
      citation if the claim is genuinely verifiable, or downgrade it from `- [x] ✅` back to an open
      `- [ ]` with a note if it isn't — do NOT blind `--baseline-write` to just accept the debt
      without checking each claim first. (repo: unified-trading-pm)
- [ ] [AGENT] P2. Once both are fixed and `quality-gates.sh` is green on a clean unified-trading-pm
      tree, confirm the repo-blocker this issue's declaration opens actually auto-resolves
      (RepoHealthWatcher polls CI state) rather than needing a manual close.

## Progress Log

- 2026-08-22, slot 10 (task `bare_root_repo_agent_writes_unenforced-c77574a3f999`): discovered while
  attempting to ship an unrelated dev-scripts change (commit `9a04be1e56`, the slot-0 dirty-repo
  watchdog for `bare_root_repo_agent_writes_unenforced_2026_08_21.md`). Verified both regressions
  predate and are disjoint from that diff (see "Why it matters"). Filed this issue, then declared a
  `qg_red` repo-blocker for `unified-trading-pm` citing this doc — will resume shipping once the
  backend signals green.
