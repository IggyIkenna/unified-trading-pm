---
doc_type: issue
title: >-
  Sports MDPS force-VM 4h/24h timeframe-ceiling crash (found 2026-08-10) was never converted to a tracked todo —
  likely the same tarball-freshness race already tracked for CEFI, unconfirmed
summary: >-
  `mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md` (all 3 of its own todos done,
  `archive_exempt: true`, awaiting `/done` archival) documents a force-VM crash
  (`mdps-backfill-sports-pipelinecheck-20260810-093506-d0c755`, 2026-08-10) caused by the VM enumerating all 7
  timeframes (`15s,1m,5m,15m,1h,4h,24h`) instead of the sports-scoped `{1m,15m,1h}` ceiling
  (`_TIMEFRAME_CEILING_BY_ASSET_GROUP[SPORTS]`), despite that ceiling being present in `live-defi-rollout` HEAD's
  `config.py` at the time — flagged in that doc's own Progress Log as "needs its own diagnosis" but never converted
  into a `- [ ]` todo or a standalone issue, so it fell out of tracking when the parent doc's own todos all closed.
  This doc converts that orphaned finding into tracked work and adds one new fact: the force-path bypass that could
  explain a stale-ceiling VM (`resolve_timeframes()` skipping scoping for an explicit `--timeframes`/`MDPS_TIMEFRAMES`
  list) was fixed at `market-data-processing-service@b2114d51` (2026-07-28) — i.e. it was ALREADY fixed 2 weeks before
  the 2026-08-10 crash, so a currently-live code defect is not the likely cause. The remaining, more probable
  explanation is a floating-tarball staleness race — the SAME class of bug already tracked (unresolved) as a P2 todo
  in `dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md` (`lc_verify_tarball_freshness`'s auto-mode
  republish/re-verify race under high branch churn) — meaning this sports crash may already be a duplicate symptom of
  that same open root cause, not a separate bug needing its own fix.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer]
tags: [sports, mdps, pipeline-e2e-check, timeframe-ceiling, tarball-freshness, vm-crash, orphaned-finding]
related:
  [
    /plans/active/issues/mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md,
    /plans/active/issues/dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md,
  ]
context_scope:
  [
    market-data-processing-service/market_data_processing_service/config.py,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    market-data-processing-service/scripts/pipeline_e2e_check.py,
  ]
created: "2026-08-16"
last_updated: 2026-08-16
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
source:
  [
    "mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md Progress Log (slot 29,
    2026-08-10) — prose finding, never tracked as a todo; re-surfaced by a docs-only-scoped re-check, slot-2,
    2026-08-16",
  ]
resolved_by:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
---

# Sports MDPS force-VM timeframe-ceiling crash — orphaned 2026-08-10 finding, tracked now

## What I found

Re-reading `mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md` in full: all 3 of its
own todos are `[x] ✅`, doc is `archive_exempt: true` pending `/done`. Its Progress Log (slot 29, 2026-08-10,
"VERIFIED — checker fix confirmed, VM crash is pre-existing" entry) describes a force-VM crash as a genuinely
separate, unresolved issue:

> Force VM `mdps-backfill-sports-pipelinecheck-20260810-093506-d0c755` self-deleted after ~4.5min... The VM
> enumerates `['15s','1m','5m','15m','1h','4h','24h']` — all 7 timeframes — rather than the sports-scoped
> `['1m','15m','1h']`. The floating MDPS tarball... apparently does NOT apply
> `_TIMEFRAME_CEILING_BY_ASSET_GROUP[SPORTS]` despite it being present in the current LDR HEAD of `config.py`... This
> is a SEPARATE MDPS backfill issue from the checker fix... the VM crash needs its own diagnosis.

That "needs its own diagnosis" was never converted to a `- [ ]` todo in that doc (whose own todo list only covers the
checker script fix, already shipped/verified) and no standalone issue doc was filed for it — a workspace HARD RULE
gap ("every deferral mentioned in a summary must already exist as a `- [ ]` todo", not prose in a Progress Log).

**New fact this session** (`market-data-processing-service`, read-only `git log`/`Read` this session, current HEAD):
`resolve_timeframes()` (`config.py:572`) has, since **`b2114d51` (2026-07-28)** — 2 weeks before the 2026-08-10
crash — always intersected an explicit `requested` timeframe list (the CLI `--timeframes`/`MDPS_TIMEFRAMES`
env-bridge path a VM launcher uses) against `_TIMEFRAME_CEILING_BY_ASSET_GROUP`, closing exactly the
"explicit-list-bypasses-scoping" class of bug that would otherwise explain a VM enumerating all 7 timeframes. Since
this fix predates the crash by 2 weeks and is still present at current HEAD, **a currently-live code defect is not
the likely explanation** — this rules out one candidate root cause the original finding left open, without
concluding the underlying question either way.

## Why it matters

If this is genuinely a duplicate symptom of the tarball-freshness race already tracked in
`dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`'s P2 todo (capture `expected_sha` once before
republish instead of re-reading a fast-moving branch HEAD), fixing that ONE todo closes both. If it is not — if sports
MDPS backfill VMs have some OTHER, sports-specific staleness path — that is a distinct gap nobody has verified is
fixed, and the original checker doc will get archived via `/done` with this thread silently dropped, exactly the
failure mode the pre-compact ritual's Step 3 exists to prevent.

## Recommended decision

**A (recommended, cheapest)**: Do nothing further until the CEFI tarball-freshness P2 todo ships, then re-run
`pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket --legs force,skip` once
(a fresh VM launch) to confirm the force VM no longer crashes and enumerates only `{15m,1h}`. If it passes, close both
this doc and the "needs its own diagnosis" thread as the same root cause; if it still crashes with all 7 timeframes,
that's positive evidence of a sports-specific bug distinct from the tarball race, worth its own dedicated diagnosis at
that point.
**B**: Diagnose now, independently of the CEFI fix — would require a fresh VM launch + log read, which is an infra
action (VM launch, real spend) outside a docs-only session's scope; flagging as the alternative rather than doing it
here.

## Todos

- [ ] [DIAG] P3. Once `dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`'s
      `lc_verify_tarball_freshness` P2 fix ships, re-run
      `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket --legs force,skip`
      (fresh VM) to confirm the force leg no longer crashes / no longer enumerates 4h/24h. Close this doc and
      cross-reference the checker doc if it passes; open a dedicated sports-specific diagnosis if it still crashes.
      (repo: market-data-processing-service)

## Progress Log

- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session): Filed while sweeping unread sports-domain
  issue docs for orphaned/stale findings (checking whether
  `mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md`'s non-empty `resolved_by` +
  `status: open` was a stale-status bug — it was NOT, that doc's own state is correctly `archive_exempt` pending
  `/done`; but its Progress Log surfaced this genuinely untracked VM-crash finding in the process). Confirmed via
  read-only `git log`/`Read` on `market-data-processing-service` (no edits) that the explicit-timeframe-list scoping
  bypass was already fixed at `b2114d51` (2026-07-28), predating the 2026-08-10 crash by 2 weeks — ruling out that
  specific code-defect explanation, not concluding the root cause. No VM launched, no code changed, no fix attempted
  this session — pure docs-only conversion of orphaned prose into a tracked P3 todo per workspace discipline.
- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session, second check same session): Re-checked this
  doc's sole todo's gate — `dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`'s
  `lc_verify_tarball_freshness` P2 todo is still `status: open` / unchecked `- [ ]` (confirmed via grep, read-only). The
  gate has not cleared, so this doc's own P3 todo (re-run `pipeline_e2e_check.py` force leg) remains correctly
  un-actionable. No VM launched, no fix attempted this session.
- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session, third check same session): **Gate cleared** —
  `dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`'s P2 (`lc_verify_tarball_freshness` auto mode)
  and P3 (final "still stale" error message) todos both flipped `- [x] ✅` via a foreign session's
  `c6ab276b40` ("docs(plans): flip P2+P3 tarball-freshness race todos", evidence: `deployment-service@fb55e8ac35`),
  confirmed via read-only grep. This doc's sole P3 todo (re-run
  `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket --legs force,skip`
  on a fresh VM) is now **actionable-now** for the first time — but the re-run itself is a VM launch (real infra
  spend), which is outside this "docs only, no writes" session's scope. Not executed this session; flagging as the
  top-priority next action for the next session with infra-write authorization. No VM launched, no code changed this
  session.
