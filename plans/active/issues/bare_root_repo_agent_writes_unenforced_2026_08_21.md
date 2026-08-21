---
doc_type: issue
title: Bare root repo checkouts (slot 0) accumulate agent writes undetected — monitoring is passive, not enforced
summary: >-
  Three bare root repo checkouts (agent-orchestrator, execution-service, unified-trading-system-ui) sat
  dirty/untracked for up to ~20h before being found by hand. slot-git-status-report.sh's slot-0 branch
  reports DIRTY state every 5 min but never pages — CLAUDE.md's "cron-checked" wording overstated this
  as enforcement. Cleaned all three; the alerting gap itself is unfixed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, execution-service, unified-trading-system-ui, unified-trading-pm]
scope: [engineer]
tags: [multi-agent-safety, per-slot-worktrees, monitoring-gap, slot-0]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
author: agent
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [operator report, interactive session slot 13, 2026-08-21]
resolved_by:
locked_by:
context_scope:
  [
    unified-trading-pm/scripts/dev/slot-git-status-report.sh,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
---

## What I found

Operator reported unpushed changes sitting in three bare root repo checkouts
(`/home/ubuntu/unified-trading-system-repos/<repo>/`, i.e. "slot 0" — NOT any `.tabs/<N>/<repo>/` slot worktree):

- `agent-orchestrator/instruments-service/scripts/size_sports_taxonomy_p4_backfill_2026_08_20.py` (+ its test) and
  `agent-orchestrator/strategy-service/strategy_service/engine/strategies/v2/liquidation_candidate_context.py` —
  two untracked directory trees holding files that belong to SIBLING repos, nested inside AO's own checkout.
- `execution-service` — 5 files (`order_adapter.py`, `order_recovery.py`, `oms.py`, 2 test files) with real,
  substantial uncommitted diffs.
- `unified-trading-system-ui` — `lib/architecture-v2/coverage.ts`, one file with a diff.

## Root cause

All three are the same failure class: a write landed in the bare root checkout instead of the writer's assigned
`.tabs/<N>/<repo>/` slot worktree. For the two AO-nested trees specifically, the path shape
(`agent-orchestrator/instruments-service/...`, `agent-orchestrator/strategy-service/...`) is consistent with a
relative-path file write issued while CWD was `agent-orchestrator/` instead of the intended sibling repo or slot —
the write "succeeded" one level inside the wrong repo, silently.

**Why nothing caught it before ~20h passed**: `slot-git-status-report.sh` (cron, every 5 min, offset
`2,7,12,17,...`) DOES classify slot 0 (the bare `${WORKSPACE_PATH}/<repo>/` checkouts — in scope every run since the
installed cron passes no `--slots` filter) and posts a snapshot to the orchestrator dashboard. But the slot-0 branch
calls only `classify_repo` — unlike the numbered-slot loop, it never calls
`check_starvation_for_slot`/`check_stash_pile_for_slot`/any alert path. A DIRTY verdict for a bare root repo is
therefore passive telemetry: no Slack page, no inbox ping, no auto-quarantine. CLAUDE.md's prior wording
("cron-checked every 5 min", attached to the "a bare `<repo>` path... is NEVER your slot" warning) overstated this as
an enforcement mechanism — it reads as a safety net that isn't one. Full detail + exact line citations:
`/codex/05-infrastructure/per-tab-worktrees.md` § "Slot-0 (bare-root checkout) dirty/untracked state is reported, not
enforced".

## Disposition (done this session, in slot 13)

- **agent-orchestrator**: both orphaned trees confirmed STALE before deletion — the sports-P4 sizing script's own
  owning todo (`sports_taxonomy_p4_backfill_2026_08_08.md`) was already closed same-day with "no valid standalone
  sizing exists yet"; the strategy-service file was a losing duplicate of work `slot-8·planning` already shipped
  under different names (`strategy-service@ac240dbd`, "add LIQUIDATION_CAPTURE candidate-context injection seam").
  Backed up to scratch, then deleted (`rm` on the 3 named files + `rmdir` on the now-empty dirs — no recursive
  delete). Repo is clean.
- **execution-service**: verified via `git diff origin/live-defi-rollout -- <files>` that the diff PREDATED three
  commits already on origin (`005b5f52` OrderStatus dedup, `7d6b909e` amend-persist, `f4cb199b` OMS-inject) —
  applying it as-is would have regressed all three (resurrected a deleted duplicate `OrderStatus` enum, deleted a
  method origin still calls, dropped ~300 lines of tests origin already has). Quarantined via
  `git stash push -u -m "quarantine 2026-08-21: ..."` (not discarded — recoverable) with a saved
  `execution_service_stale_wip_vs_origin_2026_08_21.patch`, then `git pull --ff-only` caught the checkout up 33
  commits. Repo is clean and current.
- **unified-trading-system-ui**: `coverage.ts` diff was pure reformatting (multi-line arrays collapsed to one line,
  zero content change) — the signature of a bare `prettier`/`npx prettier` run instead of `prettier-autostage.sh`,
  already a banned pattern (`coding-standards`). Quarantined via `git stash push` for the same reversibility reason,
  though it is effectively safe to drop. Repo is clean.

## What's still open

The monitoring gap itself is unfixed: `slot-git-status-report.sh`'s slot-0 branch still only reports, never alerts.

## Recommended fix

- [ ] [BACKEND] P1. Wire the same alert path the numbered-slot loop already has
      (`check_starvation_for_slot`/`check_stash_pile_for_slot`'s dedup-per-episode pattern) into the slot-0 branch
      of `unified-trading-pm/scripts/dev/slot-git-status-report.sh` (around the `if slot_in_filter "0"` block) — a
      DIRTY or untracked-files verdict on a bare root repo should page the same way FF-pull-starvation or stash-pile
      regrowth already does. Extend `classify_repo`'s slot-0 call site, not the numbered-slot one.
- [ ] [AGENT] P2. Once the alert lands, re-verify CLAUDE.md's slot-0 line (already corrected this session to
      "reported not enforced every 5 min") reads as accurate again — flip back to describing real enforcement only
      after the alert path is live and proven (at least one real DIRTY-slot-0 page observed).
