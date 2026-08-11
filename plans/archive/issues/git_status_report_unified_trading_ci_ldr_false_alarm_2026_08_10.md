---
doc_type: issue
title:
  "unified-trading-ci (single_branch, main-only) compared against live-defi-rollout in 3 separate consumers — false
  LDR≠main warnings"
summary:
  "unified-trading-ci (extracted 2026-08-06, promotion_model: single_branch, integration_branch: main — no LDR/staging
  pipeline, live-defi-rollout is a retired ref) was still being diffed against live-defi-rollout by three independent
  consumers that each computed the comparison themselves instead of reading the manifest: (1) the agent-orchestrator
  Git-Health dashboard panel (server/worktree_clean_check/_branch_state.py, fixed 2026-08-08 — pre-existing, not part of
  this doc's fix set); (2) two local fleet-hygiene scripts, unified-trading-pm/scripts/dev/slot-git-status-report.sh and
  scripts/verify-slot-host-symmetry.sh, both hardcoded to live-defi-rollout with no manifest-aware fallback; (3)
  deployment-ui's Repo-CI dashboard stall classifier (src/lib/repoCi.ts classifyStall), which read an LDR-vs-main git
  delta and classified any nonzero delta as a promotion stall — permanent by design for a single_branch repo, so it read
  as a stuck/lagging promotion forever. Operator report 2026-08-11: 'still seeing ldr not equal to main message for
  unified trading ci which we know isnt supposed to be on ldr anyway so its a no-op warning.'"
status: resolved
nature: notes
asset_group: [ao, infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-ui, agent-orchestrator]
scope: [engineer, admin]
tags: [git-health, unified-trading-ci, single-branch, promotion-model, false-positive, dashboard]
related:
  [/plans/archive/issues/git_health_scan_exclusion_infra_routing_2026_08_10.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-08-11
last_updated: 2026-08-11
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: [unified-trading-pm@7a9f1a272d, deployment-ui@f6c4c59991]
source: operator report, 2026-08-11 session
archive_exempt:
---

# unified-trading-ci LDR-vs-main false alarm — 3 consumers, now fixed

## What I found

`unified-trading-ci`'s `workspace-manifest.json` entry declares `promotion_model: single_branch`,
`integration_branch: main` (it has no LDR/staging promotion pipeline at all — `live-defi-rollout` is a retired ref that
still technically exists on the remote but is not a live target). `promotion_lag_monitor.py` already had the correct
exemption (`_single_branch_repos()`, skips the repo entirely). Three OTHER consumers each independently re-implemented
an LDR-vs-something comparison without that exemption:

1. `agent-orchestrator/server/worktree_clean_check/_branch_state.py` — `_REPO_INTEGRATION_BRANCH` dict was empty,
   defaulting every repo (including this one) to `live-defi-rollout`. **Already fixed 2026-08-08**, pre-dates this
   session — noted here only for the full picture, not part of this doc's `resolved_by` set.
2. `unified-trading-pm/scripts/dev/slot-git-status-report.sh` + `scripts/verify-slot-host-symmetry.sh` — both hardcoded
   `INTEGRATION_BRANCH`/`WANT_UPSTREAM` to `live-defi-rollout` with only a "ref doesn't exist at all" fallback (which
   never fired here, since `live-defi-rollout` DOES still exist for this repo, just retired). Fixed by adding a
   `base_branch_for_repo()`/`want_upstream_for_repo()` manifest lookup to both scripts, mirroring the pattern already
   proven in `setup-tab-worktrees.sh` and the Python fix above.
3. `deployment-ui/src/lib/repoCi.ts` `classifyStall()` — computed
   `ldrMain = findDelta(row, "main", "live-defi-rollout")` and treated any nonzero `files_changed` as a genuine
   promotion stall, with no exemption for a repo that has no promotion pipeline at all. Fixed by adding an
   `isSingleBranch()` predicate (`promotion_model === "single_branch"`) checked first in `classifyStall`, returning
   `{kind: "none"}` immediately — mirrors `isStagingDormant`'s existing `ldr_main` pattern. 3 new tests added
   (`repoCi.test.ts`).

## Why three independent re-implementations existed

No shared library for "what's this repo's real integration base" across the Python backend, the bash fleet-hygiene
scripts, and the TypeScript dashboard — each consumer computes it itself, reading the same `workspace-manifest.json` but
via three different code paths in three different languages/repos. This doc doesn't propose consolidating them (a bigger
design question, not a `- [ ]` off this issue) — just notes the pattern for whoever next hits a 4th consumer with the
same gap.

## Resolution

- `unified-trading-pm@7a9f1a272d` — manifest-aware branch lookup in both fleet-hygiene scripts.
- `deployment-ui@f6c4c59991` — `isSingleBranch()` exemption in the Repo-CI stall classifier, with tests.

No open todos — filed as a resolved record for provenance (the shipped commits' own comments cite this doc's slug).
