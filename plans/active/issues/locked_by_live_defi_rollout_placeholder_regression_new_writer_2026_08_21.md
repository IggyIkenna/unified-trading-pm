---
doc_type: issue
title: "locked_by: live-defi-rollout placeholder is STILL being stamped on new docs, 2026-08-20/21 — a different writer than the one already fixed"
summary: >-
  The corpus-wide `locked_by: live-defi-rollout` placeholder bug (root-caused + cleared 2026-08-12/18,
  `scripts/plans/fix_epic_frontmatter_2026_05_21.py` identified as the origin, `scripts/cicd/parity_watchdog.py`
  patched 2026-08-20 17:47 UTC — `unified-trading-pm@de854a729f`, "fix(plans): stop parity watchdog fake lock
  stamping" — to stop stamping it going forward) is RECURRING on docs created AFTER that fix landed. Found while
  executing the ARCHIVE lane (chunk 4): `manifest_hygiene_red_all_2026_08_19.md` and
  `manifest_hygiene_red_cefi_2026_08_16.md` both carry the exact placeholder and both had to be SKIPPED per the
  hard-stop rule in `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` ("locked_by:
  live-defi-rollout... still a HARD-STOP until actually cleared: do not unlock it yourself"). A corpus grep found
  11 currently-active docs still carrying the placeholder, several created on or after 2026-08-20 (the fix date)
  — `manifest_hygiene_red_changed_all_2026_08_20.md` (created 2026-08-20, same day as the fix commit but the fix
  landed 17:47 UTC so ordering is ambiguous), `dp_live_004_odds_api_unproductive_2026_08_21.md` (created
  2026-08-21, unambiguously AFTER the fix), `dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`
  (2026-08-21), `dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md`,
  `dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md`. `parity_watchdog.py` itself no longer contains the
  string `live-defi-rollout` at all (confirmed via grep), so the fixed script is not the one still stamping it —
  some OTHER filer/escalation script (most likely in `e2e-testing` or `deployment-service`, the repos that own the
  `manifest_hygiene_daily.py`/`dp_live_004`/`dp_fetch_009` doc families — neither checked out in this PM-only
  worktree) independently hardcodes the same placeholder and was never touched by the 2026-08-12/2026-08-20 fix
  effort.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [locked_by, placeholder, regression, plan-hygiene, archival, escalation-filer]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
resolved_by:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
source: >-
  Surfaced while executing the ARCHIVE_RESOLVED archival lane (chunk 4 of N) against
  `manifest_hygiene_red_all_2026_08_19.md` and `manifest_hygiene_red_cefi_2026_08_16.md` — both blocked from
  archival by this exact placeholder, prompting a corpus-wide re-check of whether the documented fix actually
  stopped new occurrences.
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
    scripts/cicd/parity_watchdog.py,
  ]
---

# locked_by: live-defi-rollout placeholder is still being stamped — a different writer than the one already fixed

## What I found

Per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, the `locked_by: live-defi-rollout`
placeholder bug was root-caused (a one-off frontmatter-conformity script hardcoding the shared branch name instead
of a real actor id, propagated into 96 docs 2026-05-21..2026-07-11), cleared corpus-wide in 4 batched commits
2026-08-12/18, and the actual writer (`scripts/cicd/parity_watchdog.py`) was patched the same window to stop
stamping it on new docs (confirmed via `git log`: `unified-trading-pm@de854a729f`, "fix(plans): stop parity
watchdog fake lock stamping", 2026-08-20 17:47:10 UTC — `rg -n "live-defi-rollout"
scripts/cicd/parity_watchdog.py` now returns zero hits).

Despite that, a corpus grep for `^locked_by: live-defi-rollout` today (2026-08-21) still finds it on 11 active
docs, several created on/after the fix date:

- `manifest_hygiene_red_all_2026_08_19.md`, `manifest_hygiene_red_cefi_2026_08_16.md` (blocked this chunk's
  archival — both otherwise fully resolved, 0 open todos)
- `manifest_hygiene_red_all_2026_08_18.md`, `empty_reprobe_disagreement_all_2026_08_17/18/19.md` (pre-fix window,
  expected under the "clear script missed it" branch)
- `manifest_hygiene_red_changed_all_2026_08_20.md`, `dp_live_004_odds_api_unproductive_2026_08_21.md`,
  `dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`,
  `dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md`,
  `dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md` — created 2026-08-20/21, i.e. on or after the fix
  commit's timestamp.

Since `parity_watchdog.py` no longer contains the placeholder string at all, it cannot be the writer of the
2026-08-20/21 recurrences. These doc families (`manifest_hygiene_*`, `dp_live_004_*`, `dp_fetch_009_*`) are filed
by daily audit/escalation scripts living in `e2e-testing` and `deployment-service` — neither repo is checked out
in this PM-only worktree, so I could not grep their filer scripts directly this session. Per the codex doc's own
guidance ("either (a) a doc the corpus-wide clear missed... or (b) a NEW recurrence, meaning the
`parity_watchdog.py` fix regressed"), the 2026-08-20/21-dated docs are option (b)'s shape but from a DIFFERENT
writer than the one already fixed — the corpus-wide fix effort evidently patched only `parity_watchdog.py` and
did not find/patch this second writer.

## Why it matters

Every doc carrying this placeholder is a HARD-STOP on archival (cannot self-unlock per the codex rule) regardless
of how resolved its own content is — `manifest_hygiene_red_all_2026_08_19.md` and
`manifest_hygiene_red_cefi_2026_08_16.md` are both fully resolved (0 open todos, evidence-backed fixes shipped)
but sit stuck in `plans/active/issues/` indefinitely until this is cleared. If left unfixed, every future daily
`manifest_hygiene_*`/`dp_live_004_*`/`dp_fetch_009_*` doc will keep inheriting the same fake lock, compounding the
archive backlog these auto-filed daily docs already contribute heavily to.

## Recommended decision

1. Identify the actual writer in `e2e-testing`/`deployment-service` (likely a shared escalation-filer helper
   analogous to `_dp_common.py::file_escalation_issue`, given the hardcoded-default pattern already documented for
   the `repos:` field in `manifest_hygiene_red_all_2026_08_19.md`'s own Progress Log) and patch it the same way
   `parity_watchdog.py` was patched — stop stamping a branch name as `locked_by`.
2. Re-run (or extend) `scripts/plans/clear_locked_by_placeholder_2026_08_12.py` against the currently-affected
   docs once the writer is fixed, so the backlog doesn't require a manual per-doc `[unlock-plan]` ask for each one.
3. Until then, any doc found carrying this placeholder stays a HARD-STOP — do not self-clear; ask the operator for
   a targeted `[unlock-plan]` per doc, or batch-ask once the writer fix lands.

## Todos

- [ ] [BACKEND] P2. Find and patch the actual writer of `locked_by: live-defi-rollout` for the
      `manifest_hygiene_*`/`dp_live_004_*`/`dp_fetch_009_*` doc families (in `e2e-testing` or `deployment-service`
      — check each repo's escalation-filer helper for a hardcoded branch-name default analogous to the
      already-fixed `parity_watchdog.py` case), mirroring the 2026-08-20 fix shape. Add a regression test
      asserting a newly-filed doc never carries a literal branch name as `locked_by`.
- [ ] [SCRIPT] P3. Once the writer is fixed, re-run `scripts/plans/clear_locked_by_placeholder_2026_08_12.py` (or a
      narrow follow-up) against the currently-affected docs listed above so they stop blocking archival, then
      archive `manifest_hygiene_red_all_2026_08_19.md` and `manifest_hygiene_red_cefi_2026_08_16.md` (both
      otherwise fully resolved, 0 open todos, confirmed by this doc's own investigation 2026-08-21).

## Progress Log

- **2026-08-21 (archival lane, chunk 4)**: Filed after `manifest_hygiene_red_all_2026_08_19.md` and
  `manifest_hygiene_red_cefi_2026_08_16.md` both had to be SKIPPED from an otherwise-clean archival pass solely due
  to this placeholder. Confirmed via `git log -1 --format='%H %ci' de854a729f` (2026-08-20 17:47:10 UTC) and `rg -n
  "live-defi-rollout" scripts/cicd/parity_watchdog.py` (zero hits) that the documented fix is live but does not
  explain the 2026-08-20/21-dated recurrences. Cross-repo investigation to find the actual second writer is out of
  scope for this PM-only worktree session — filed as a tracked P2 rather than left as a chat finding.
