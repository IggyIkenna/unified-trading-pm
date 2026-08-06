---
doc_type: issue
title: >-
  Manually closing a superseded LDR→main promote PR orphans its immutable per-SHA ref — fleet bot's superseded-ref
  cleanup only sweeps PR-backed refs
summary: >-
  Closing an LDR→main promote PR outside the fleet bot's superseded-ref cleanup leaves its immutable
  `promote/<repo>/<sha12>` ref on the remote with no open PR. `ldr_to_main_fleet_promote.sh`'s superseded-ref cleanup
  iterates `gh pr list --state open` (PR-backed refs only), so an orphan ref (closed PR, never-swept) accumulates
  indefinitely. Confirmed live 2026-08-06: conflict_resolver agt-7e7e2c closed execution-service PR #552 (head
  `promote/execution-service/2ff643b4f60c`) — the ref stayed on the remote until manually deleted via `gh api -X
  DELETE`. Many other `promote/execution-service/*` orphan refs (no open PR) predate this and remain. Low severity (no
  functional impact; orphan refs don't affect promotion or GitHub branch listing by default) but accumulates over the
  fleet bot's high per-repo promote cadence.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, ldr-to-main-promote, fleet-bot, ref-hygiene]
related: [/plans/archive/2026_06/cicd_consolidated_remaining_2026_06_24.md]
created: 2026-08-06
parent_epic: infrastructure_master
source: conflict_resolver escalation agt-7e7e2c (fleet-bot promotion-conflict dispatch, 2026-08-06)
assigned_vm: NA
execution_scope: local-only
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Promote ref orphaned on manual PR close

## Finding

The LDR→main fleet bot cleans up stale promote refs only as a side effect of closing an **open** promote PR
(`scripts/cicd/ldr_to_main_fleet_promote.sh` — "Superseded ref cleanup": `STALE_HEADS` from `gh pr list --state open`,
then `gh api -X DELETE git/refs/heads/$_STALE_HEAD`). A ref whose PR is closed by any OTHER path (conflict_resolver
closing a superseded PR manually, an operator, a stale-check close) is never swept — it stays on the remote as an orphan
`promote/<repo>/<sha12>` ref.

Confirmed 2026-08-06: conflict_resolver agt-7e7e2c closed execution-service PR #552 (head
`promote/execution-service/2ff643b4f60c`) as superseded after backmerging main into LDR (f0774705) and draining via
fresh PR #553. The old ref remained; deleted manually
(`gh api -X DELETE repos/IggyIkenna/execution-service/git/refs/heads/promote/execution-service/2ff643b4f60c`).
Pre-existing orphans for many prior SHAs remain on the remote.

## Impact

Low. Orphan refs don't block promotion or CI; they're inert pointers to already-promoted (or superseded) content. Main
risk is accumulation (cosmetic clutter in `git ls-remote`, potential confusion in ref-scoped tooling) plus the repeated
manual step for anyone who closes a promote PR outside the fleet bot.

## Resolution options

- **A (recommended): fleet-bot orphan sweep** — in `ldr_to_main_fleet_promote.sh` (or the PM-only
  `ldr-to-main-promote.yml` twin), after the superseded-ref cleanup, list `promote/<repo>/*` refs and delete those with
  no open PR and not equal to the current `PROMOTE_HEAD`. Owner: LDR→main fleet bot maintainer.
- **B: document the manual step** — note in the conflict_resolver role / ci-cd codex that manually closing a promote PR
  must also delete its ref. Cheaper, but leaves accumulation to memory.

- [ ] [P3] fleet-bot orphan-ref sweep: delete `promote/<repo>/*` refs with no open PR (and not current PROMOTE_HEAD) in
      `ldr_to_main_fleet_promote.sh` — owner: LDR→main fleet bot maintainer (unified-trading-pm).
