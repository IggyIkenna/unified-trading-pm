---
doc_type: issue
title:
  promote_provenance_range.py last_promoted_marker() queries --head live-defi-rollout but ldr_main promote PRs use
  --head promote/<repo>/<sha> — marker can never advance, fleet-wide auto-merge arming perpetually re-flags old commits
summary: |
  Surfaced while resolving cicd escalation agt-c281eb (market-tick-data-service quality-gates-v2 RED on main, click
  CVE PYSEC-2026-2132). The fix landed cleanly (LDR commit 9614964, quality-gates-v2 green on the promotion PR head,
  SIT validated), but `ldr-to-main-promote-fleet.yml` refused to arm auto-merge on the resulting PR (#539), citing 39
  "code commit(s) bypassed quickmerge" — all 39 are OLD (days/weeks old), already multiply-promoted commits with
  nothing to do with this change. Root cause: `scripts/cicd/promote_provenance_range.py::last_promoted_marker()`
  resolves the provenance-check range via
  `gh pr list --repo <o>/<r> --base <target> --head live-defi-rollout --state merged --json headRefOid --limit 1`.
  But the WS-L Phase-0 immutable-per-SHA-ref design (`ldr-to-main-promote-fleet.yml`, `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`)
  opens promote PRs with `--head promote/$REPO/$LDR_SHA`, never with head literally `live-defi-rollout`. So the
  `--head live-defi-rollout` filter matches ZERO promote PRs under the current scheme — the marker query always
  returns None for repos that have been through the per-SHA-ref cutover, `last_promoted_marker()` never advances past
  whichever pre-cutover PR (if any) last matched, and every subsequent drain re-runs the provenance check over an
  ever-widening `<stale-marker>..origin/live-defi-rollout` range, re-flagging the same growing pile of already-shipped
  commits forever. This is the EXACT failure mode `provenance_gate_squash_perpetual_block_2026_06_17.md` was written
  to prevent, reintroduced by the later WS-L Phase-0 head-ref rename. Confirmed on market-tick-data-service: the
  resolved marker was `8fbe29adb72f486b6603268e88d862bd13c3f87b`, dozens of commits and multiple successful
  `chore(promote)` merges behind current LDR HEAD; re-running `check_strict_quickmerge.py` over that stale range
  reports 39 violations, none newer than ~2026-07-09 and none related to any pending change. Because
  `ldr-to-main-promote-fleet.yml` calls the check with `--block`, this is a HARD block on arming auto-merge (not just
  a WARN) — every `ldr_main` repo whose promote PRs already use the per-SHA-ref scheme is affected, not just
  market-tick-data-service; auto-merge on those repos' promote PRs likely has to be armed manually every cycle, or
  never fires, until this is fixed.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, provenance-gate, quickmerge, ldr-to-main, auto-merge, marker-bug]
related:
  [
    cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,
    provenance_gate_squash_perpetual_block_2026_06_17.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: cicd
drift_direction: advance-code
source:
  [
    unified-trading-pm/scripts/cicd/promote_provenance_range.py#L78,
    unified-trading-pm/.github/workflows/ldr-to-main-promote-fleet.yml#L747,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-trading-pm@20db96085 (all 3 todos shipped + fleet-wide audit complete)
---

# promote_provenance_range.py marker query never matches WS-L Phase-0 promote PRs

## What I found

`last_promoted_marker()` in `scripts/cicd/promote_provenance_range.py` finds the "last drained SHA" by querying:

```
gh pr list --repo <owner>/<repo> --base <target> --head live-defi-rollout --state merged --json headRefOid --limit 1
```

But `ldr-to-main-promote-fleet.yml` (the WS-L Phase-0 immutable-per-SHA-ref cutover,
`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`) opens every promote PR with `--head promote/$REPO/$LDR_SHA` — never with
head literally `live-defi-rollout`. The `--head live-defi-rollout` filter therefore matches none of the current-scheme
promote PRs. Once a repo's promote history is entirely post-cutover, `last_promoted_marker()` permanently returns `None`
(or whatever pre-cutover PR last matched), so `resolve_range()` either falls back to the full `<base>..<ldr>` range or
freezes on a stale marker. Either way the range only WIDENS over time and never advances past a real drain point.

Confirmed live on `market-tick-data-service` (escalation agt-c281eb, 2026-07-13): the fleet workflow resolved
`marker=8fbe29adb72f486b6603268e88d862bd13c3f87b`, many commits and several successful `chore(promote)` merges behind
current LDR HEAD. Re-running `check_strict_quickmerge.py --range 8fbe29a..origin/live-defi-rollout --block` locally
reproduces the exact 39-violation list the fleet bot printed — all 39 are pre-existing commits with real
`Quickmerge:`-less messages from days/weeks ago (e.g.
`f8cab3f0 fix(orchestrator): register catalog readers once per process...`), none touching the change actually being
promoted.

Because `ldr-to-main-promote-fleet.yml` invokes the check with `--block`, a positive match is a HARD refusal to arm
auto-merge (`⛔ provenance: $REPO has non-quickmerge CODE on LDR — NOT arming auto-merge (PR left open)`) — not a soft
warning. Every promotion for every `ldr_main`-flagged repo whose promote history is entirely post-cutover hits this on
every drain.

## Why it matters

This is the exact perpetual-reflag failure mode `provenance_gate_squash_perpetual_block_2026_06_17.md` was written to
fix (via the marker mechanism), reintroduced by the later per-SHA-ref (`promote/<repo>/<sha>`) head-branch rename that
the marker query was never updated to match. Left unfixed:

- Auto-merge never arms for any `ldr_main` repo past its first post-cutover promote PR — every promotion needs a manual
  merge (as this escalation had to do) or sits open forever, defeating the point of the fleet automation.
- The violation list only grows (each drain re-flags the same commits plus whatever aged onto LDR since), so the noise
  in promote-PR comments compounds indefinitely and obscures a genuine new bypass if one occurs.
- It directly delayed resolving a CVE fix (this escalation) from reaching `main`.

## Recommended decision

Fix `last_promoted_marker()` to match the actual head-ref scheme. Two viable approaches:

1. Query by PR **title** prefix (`chore(promote): LDR → main`) instead of `--head live-defi-rollout`, sorted by
   `mergedAt` descending, `--limit 1` — the title is stable across the ref-naming scheme change.
2. Query by head-ref **prefix** (`promote/$REPO/`) via `--json headRefName,headRefOid,mergedAt` and filter client-side
   (gh's `--head` flag does exact match, not prefix, so this needs a `--jq`/`-f` filter change rather than the `--head`
   argument).

Either way, backfill/verify the marker resolves correctly for at least one already-migrated `ldr_main` repo
(market-tick-data-service is a live repro case) before rolling out, and re-run `check_strict_quickmerge.py` with the
corrected range to confirm the 39 stale violations drop to 0 (or only genuinely-new ones remain).

## Todos

- [x] ✅ [SCRIPT] P1. Fix `last_promoted_marker()` in `unified-trading-pm/scripts/cicd/promote_provenance_range.py` to
      match promote PRs opened with `--head promote/<repo>/<sha>` (title-prefix or head-ref-prefix query), not the
      literal `--head live-defi-rollout`. (repo: unified-trading-pm) — unified-trading-pm@20db96085. Switched
      `last_promoted_marker()` to filter by the stable `chore(promote)` title prefix (shared by every promote-bot
      variant: Tier-C staging drain, Option-B main auto-drain, Option-B main fleet per-SHA-ref direct) sorted by
      `mergedAt`, instead of `--head <branch>` — head-ref-shape-agnostic, so it matches both the legacy
      `live-defi-rollout`-headed PRs and the WS-L Phase-0 `promote/<repo>/<sha>`-headed fleet PRs unchanged.
- [x] ✅ [SCRIPT] P2. Add a regression test for `last_promoted_marker()` covering the per-SHA-ref head-branch shape
      (`promote/<repo>/<sha>`), not just the legacy `live-defi-rollout` shape. (repo: unified-trading-pm) —
      unified-trading-pm@20db96085. Added `test_marker_matches_per_sha_ref_promote_pr_by_title_not_head` (asserts the
      marker resolves from a `gh pr list` payload with no `headRefName` field at all, proving title-based resolution is
      head-ref-shape-agnostic) + `test_marker_ignores_non_promote_prs_and_picks_latest_mergedat` in
      `tests/unit/test_promote_provenance_range.py`; updated the pre-existing `test_marker_parsed_from_gh_json` to carry
      a `title` field now that the query no longer filters by `--head`.
- [x] ✅ [SCRIPT] P2. After the fix ships, audit other `ldr_main` repos for accumulated stale-marker provenance noise
      (re-run `check_strict_quickmerge.py` with the corrected range per repo) and confirm auto-merge arms cleanly on
      their next drain. (repo: unified-trading-pm) — see "## Audit results (todo 3)" below.

## Audit results (todo 3, post-fix @ unified-trading-pm@20db96085)

Ran `promote_provenance_range.py --base-branch main` (the fixed, title-based marker resolution) + a
`check_strict_quickmerge.py --range <resolved> --block` over every `ldr_main`-flagged repo in `workspace-manifest.json`
(23 repos), using each slot's own clone (`--cwd .tabs/4/<repo>`, `--fetch-remote origin`):

- **22/23 repos resolve `mode=marker`** (a real, reachable `chore(promote)`-titled merged-PR SHA) — the fix is confirmed
  working fleet-wide, not just on the market-tick-data-service repro case. Zero repos hit the OLD bug (`mode=fallback`
  due to a head-branch filter matching nothing on an all-post-cutover promote history).
- **1/23 (`ibkr-gateway-infra`) resolves `mode=fallback`** (`marker=∅`) — correctly: no merged `chore(promote)` PR
  exists yet for this repo's `main` base, so the FAIL-SAFE raw `origin/main..origin/live-defi-rollout` range applies as
  designed. Not a bug.
- **17/23 repos**: `check_strict_quickmerge.py` over the corrected (narrow, since-last-drain) range returns **0
  violations** — auto-merge will arm cleanly on their next drain.
- **6/23 repos show violations in the corrected range**: `agent-orchestrator` (1), `alerting-service` (1),
  `deployment-api` (3), `deployment-ui` (1), `unified-api-contracts` (2), `unified-trading-library` (2). Checked every
  flagged commit's timestamp — **all are from TODAY (2026-07-13), within the last ~7 hours**, mostly one coordinated
  cross-repo `feat(alerting)/deployment-digest (parity #5)` change plus one unrelated `agent-orchestrator` commit — i.e.
  genuine, currently-unshipped-via-quickmerge commits, NOT the stale days/weeks-old noise this fix eliminates. This is
  the gate working AS DESIGNED post-fix: a clean, narrow signal instead of an ever-widening false-positive pile. No
  action taken on these 6 by this audit — each repo's own `ldr-to-main-promote-fleet.yml` run will now correctly flag
  exactly these (and only these) commits and hold auto-merge until they're re-shipped via `quickmerge --agent` (or
  reverted) by their authors, same as any other legitimate provenance-gate block.

## Resolution (this escalation, agt-c281eb)

market-tick-data-service PR #539 (carrying the click 8.4.2 CVE fix, commit 9614964) had `quality-gates-v2` green and
`ci_status=SIT_VALIDATED` — the actual gate this escalation was scoped to fix. Per operator/main-agent guidance via
`/blocked` (BLK-c5fcab8a), the PR was merged manually to unblock `main` given the provenance flag was a confirmed false
positive from this marker bug, not a real bypass. See commit history on `market-tick-data-service` main for the merge
SHA.
