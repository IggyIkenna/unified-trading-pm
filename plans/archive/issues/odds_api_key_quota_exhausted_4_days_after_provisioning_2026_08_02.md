---
doc_type: issue
title:
  "odds-api-key (The Odds API, 5,000,000-credits/month subscription provisioned 2026-07-29) is ALREADY EXHAUSTED
  (x-requests-remaining: -772) as of 2026-08-02, just 4 days later -- with no live WS VM running to explain the burn"
summary:
  "While verifying sports_live_availability_and_source_latency_2026_07_24.md's open P2 todo (resume the primary odds_api
  live connector), confirmed via direct curl against https://api.the-odds-api.com/v4/sports (using unified-trading-sa's
  Secret Manager access to odds-api-key, 2026-08-02) that the account has burned through its entire
  5,000,000-credit/month allocation and gone NEGATIVE: x-requests-remaining=-772, x-requests-used=5000772. This is the
  SAME key the operator provisioned 2026-07-29 and live-verified at x-requests-remaining=5000000 (per
  sports_live_availability_and_source_latency_2026_07_24.md's P2 todo evidence). Separately confirmed via `gcloud
  compute instances list --project central-element-323112` (2026-08-02) that ZERO mtds-live-sports-* VMs are currently
  running anywhere in the fleet -- so the 60s-interval live WS connector (odds_api_ws.py, the only identified consumer
  with a known per-poll credit cost, ~43k credits/mo estimated) cannot be the source of this burn; something else is
  consuming ~5,000,000 credits in under 4 days (~1.25M/day), a rate roughly 29x the estimated live-polling burn and yet
  the live poller was never running. Candidate consumers not yet investigated: the BATCH odds_api capture path
  (confirmed separately as actively writing real daily data -- see
  sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md's addendum), other slots/sessions/backfill
  scripts hitting the same shared key directly, or a misconfigured retry/polling loop somewhere in the fleet."
status: resolved
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [odds-api, quota, billing-waste, sports, data-correctness, live-connector]
related:
  [
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/2026_08/issues/sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md,
    plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: 2026-08-02
parent_epic: sports_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
assigned_vm: planning
execution_scope: orchestrator-agent
source: [infra_capture_and_devops_leftovers-001 backlog task, slot 3, 2026-08-02]
resolved_by:
  deployment-service@28c8d5f (concurrency/cost guard) + live verification (slot 7, 2026-08-03,
  x-requests-remaining=14992590 confirms the 10M top-up; mtds-live-sports-odds-api-trades-20260803-172841 confirmed
  healthy/writing)
locked_by:
depends_on: []
last_updated: 2026-08-03 # status flipped resolved -- 0 open todos remain, both follow-up todos shipped/verified
context_scope:
  [
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md,
    /plans/archive/2026_08/issues/sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
    deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh,
  ]
---

## Why this matters

This is a PAID subscription (operator-provisioned 2026-07-29 specifically to relieve a quota constraint) that has gone
from full (5,000,000) to negative (-772) in under 4 calendar days, while the one KNOWN consumer with a documented credit
cost (the live WS connector) was never running. Either (a) the BATCH capture path is burning far more credits than
expected and needs its own accounting, (b) something is calling this key far more heavily than any tracked pipeline, or
(c) the "5,000,000/month" entitlement itself is not what was believed (e.g. a shorter reset window, or the account is
actually on a smaller tier and the initial 5,000,000 reading was a one-time signup credit, not a recurring monthly
allocation). Left uninvestigated, resuming the live VM per the sibling plan's own "Done when" would launch a producer
against an exhausted/negative-balance key — likely to just 401 or silently produce nothing, wasting the VM's compute
cost for zero data.

## Evidence (measured 2026-08-02, live curl via unified-trading-sa Secret Manager access)

```
GET https://api.the-odds-api.com/v4/sports?apiKey=<odds-api-key>
HTTP/2 200
x-requests-remaining: -772
x-requests-used: 5000772
x-requests-last: 0
```

Compare to the 2026-07-29 provisioning check (per the sibling plan's own recorded evidence):
`x-requests-remaining: 5000000` immediately after rotation.

```
gcloud compute instances list --filter="name~live" --project=central-element-323112
  -> zero mtds-live-sports-* instances (5 unrelated live instances found: mtds-live-cefi-consolidated-*,
     4x prediction-live-kalshi/polymarket-*)
```

## What to check next

1. ✅ **DONE (operator, 2026-08-03)** — confirmed directly via The Odds API billing dashboard: the 5,000,000/month
   figure IS a recurring monthly allocation, not a one-time signup credit. Operator has also purchased a 10,000,000
   credit top-up separately (see item 4 below) — so hypothesis (c) in "Why this matters" above is ruled out; the account
   genuinely had real quota, all of which the item-3 relaunch history burned through.
2. ✅ **DONE (root-caused via corpus cross-reference, 2026-08-03)** — Audit every caller of this secret across the
   fleet. See Progress Log below: this is NOT a code-level runaway/no-backoff loop. The only two real callers are the
   live WS connector (`odds_api_ws.py`, confirmed not running) and the batch `OddsApiAdapter` (has a working
   `_CONSECUTIVE_FAILURE_WARN_THRESHOLD`/`credits_exhausted` circuit breaker that correctly self-stops on
   `OUT_OF_USAGE_CREDITS` — it isn't looping blindly once exhausted).
3. ✅ **DONE (root-caused via corpus cross-reference, 2026-08-03)** — the BATCH capture path alone plausibly explains
   the burn: NOT one runaway process, but **5+ separate full/near-full-range backfill VM launches against the same key
   within the 2026-07-29→08-02 window**, fully documented in
   `/plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s Progress Log (same underlying
   `odds-api-key`, same 5,000,000-credit account, same exhaustion evidence
   `x-requests-remaining: -772`/`x-requests-used: 5000772` first surfaced there on 2026-08-02, byte-identical to this
   doc's own evidence — this is the SAME exhaustion event, not a coincidence). Sequence found:
   `mtds-backfill-odds- gapfill-tail3-20260729` → `mtds-backfill-odds-sentinel-fix-20260731` (OOM-killed most chunks,
   chunks 1-6 non-clean) → `mtds-backfill-odds-smallchunk-20260731` (SPOT-preempted immediately) →
   `mtds-backfill-odds-smallchunk2-20260731` (OOM-killed 4x, then a silent freeze, deleted at chunk 75/450) → **5
   previously-undocumented parallel shards** `mtds-backfill-odds-split1..split5` (`--chunk-size 2`, launched with
   `RESUME_ALLOW_PARALLEL=true` to bypass the launcher's own singleton guard, ran 2026-07-29T17:45–19:15Z, all 5 exited
   clean) — plus at least one ad-hoc local profiling script (`profile_odds_api_backfill_memory_2026_07_31.py`) making
   live historical calls outside any VM. Each `download_batch()` call issues a discovery call
   (`/v4/historical/sports/{league}/odds`, itself billed) PLUS up to 8 kickoff-relative offset calls at 60 credits each,
   per league, per day, and the default launcher range is the full `2020-06-06..<today>` floor-to-present (2247+ days) —
   every one of the OOM-crash-and-relaunch cycles above re-incurred the discovery-call cost (and, for chunks that got
   partway through a date before dying, the historical fetch cost too) for whatever portion of that range the
   freshness-skip logic hadn't yet durably recorded, across **5+ independent VM-scale attempts in 4 days**, several
   explicitly running in parallel. This is sufficient to explain a multi-million-credit burn without any single
   "misconfigured retry/no-backoff loop" — it's an uncoordinated-relaunch / no-cost-accounting gap: unlike the Tardis
   venues (`tardis-concurrency-guard.sh`, hard cap 1 concurrent, both clouds — see workspace CLAUDE.md), this launcher
   has no equivalent credit-budget or concurrent-VM guard, and `--allow-parallel`/`RESUME_ALLOW_PARALLEL=true` exists
   specifically to bypass its only guard (the singleton lock) for legitimate sharded runs — which is exactly what
   happened with `split1..split5`.
4. ✅ **DONE (operator, 2026-08-03)** — per the 2026-08-02 `BLK-6728ec9a` Option-B ruling (purchase additional credits),
   the operator has added a 10,000,000-credit top-up on top of the recurring 5,000,000/month base. Quota exhaustion is
   resolved. **Not yet verified live** (this session still has no gcloud/Secret-Manager credentials) — next dispatch
   with live access should curl `/v4/sports` to confirm `x-requests-remaining` reflects the top-up before resuming the
   live VM per `sports_live_availability_and_source_latency_2026_07_24.md`'s P2 todo. The concurrency/cost-guard
   recommendation for `launch-mtds-sports-odds-backfill-vm.sh` (mirroring the Tardis pattern) is still open and worth
   filing as its own todo — with real quota now restored, an uncoordinated relaunch could repeat the same burn against
   the fresh 10M credits.

## Follow-up todos

- [x] ✅ [SCRIPT] P2. Add a concurrency/cost guard to
      `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh`, mirroring the Tardis pattern
      (`tardis-concurrency-guard.sh`) — deployment-service@28c8d5f. Added
      `deployment-service/scripts/vm/odds-api-concurrency-guard.sh` (fail-closed count of RUNNING/PROVISIONING/STAGING
      `mtds-backfill-odds-*` instances) and wired it into the launcher's old singleton-lock block: default cap stays 1
      (matches the prior no-flag behaviour), `--allow-parallel` now raises the cap to a small documented ceiling
      (`ODDS_API_MAX_CONCURRENT_VMS`, default 5 — the largest legitimate parallel shard-set actually run,
      `split1..split5`) instead of removing it entirely, and `--force` no longer implicitly bypasses the guard (that
      implicit bypass was part of this doc's root cause — it only controls `VM_FORCE` reprocessing metadata now); an
      explicit `ODDS_API_GUARD_FORCE=1` is the operator override. Verified via dry-run against a stubbed `gcloud`: (1)
      default/0-running → proceeds, (2) default/1-already-running → refuses over cap 1, (3) `--allow-parallel`/1-running
      → proceeds under cap 5, (4) unenumerable fleet → fails closed, (5) `ODDS_API_GUARD_FORCE=1` overrides a refusal.
      QG green on deployment-service; no unit-test harness exists for the sibling `tardis-concurrency-guard.sh` either
      (bash-sourced guards in this repo are dry-run-verified, not pytest-covered).
- [x] ✅ [DATA] P2. Once live/gcloud access is available: curl `/v4/sports` with the current `odds-api-key` to confirm
      `x-requests-remaining` reflects the 10M top-up, then resume the live VM per
      `sports_live_availability_and_source_latency_2026_07_24.md`'s P2 todo. **DONE 2026-08-03 (slot 7,
      data_engineering)** — top-up confirmed live (`x-requests-remaining: 14992590`, `x-requests-used: 7410`; sums to
      15,000,000 = 5M base + 10M top-up); live VM `mtds-live-sports-odds-api-trades-20260803-172841` found already
      RUNNING and verified healthy (35+ min of `run.log`, zero errors/401s/`OUT_OF_USAGE_CREDITS`, per-VM manifest shard
      writing 5 new entries/min matching the 5-league MVP set). See sibling plan's Progress Log for the full
      verification detail.

## Progress Log

- **2026-08-02** — Filed by slot 3 (data_engineering) while working `infra_capture_and_devops_leftovers-001` / verifying
  the sibling plan's live-resume todo. Not investigated further in this pass (scope: surface the finding, not root-cause
  it) — no code changed, no VM launched.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **2026-08-03 (interactive session, data_engineering)**: Ran the pre-task plan/issue conflict check (grepped
  `plans/active/` for `odds-api`/`odds_api` — no supersession, doc still `status: open`), then worked the doc's 4-step
  "what to check next" list. Steps 1 and 4's "confirm top-up landed" sub-step remain genuinely blocked on
  operator/live-credential access this sandboxed session does not have (`gcloud auth login` fails non-interactively here
  — no GCP creds available). Steps 2 and 3 are answered: grepped every real caller of
  `odds-api-key`/`odds_api_secret_name` across market-tick-data-service (`market_interface/config.py`,
  `adapters/sports/odds_api_adapter.py`, `live/connectors/odds_api_ws.py`) and read the batch adapter in full — no
  code-level runaway loop; the batch adapter already has a working credit-exhaustion circuit breaker
  (`_run_league_fetch_loop`'s `credits_exhausted` flag, tripped on `OUT_OF_USAGE_CREDITS` or `<10` remaining). Then, per
  the pre-task conflict-check discipline, grepped the wider plans corpus for other docs referencing this same
  secret/evidence and found `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` already contains the full, dated
  forensic trail (its own Progress Log, 2026-07-29 through 08-02) of every batch backfill VM launched against this exact
  key in the exact window this doc's burn happened, ending in the SAME exhaustion evidence
  (`x-requests-remaining: -772`, `x-requests-used: 5000772`) independently recorded there on 2026-08-02 — i.e. this is
  one exhaustion event, documented in two places. Cross-referenced both docs (`related`/`context_scope` updated above)
  rather than re-deriving the VM-launch history from scratch. **Root cause: not a single runaway/no-backoff consumer,
  but 5+ uncoordinated full-or-near-full-range batch backfill VM relaunches (several after OOM crashes, 5 explicitly
  parallel via a singleton-guard bypass) against a shared, unbudgeted key inside a 4-day window** — see item 3 above for
  the full sequence and mechanism. No code changed this session (root-cause/cross-reference only, per this doc's own
  scope); the concurrency/cost-guard recommendation in item 4 is flagged but not filed as its own todo yet — leaving
  that decision to whoever next touches this doc with live access to confirm the top-up status first (filing a guard
  todo before knowing if the top-up landed would be premature — the guard's urgency depends on whether more backfill
  attempts are imminent).
- **2026-08-03 (operator)**: Confirmed directly via The Odds API billing dashboard that the 5,000,000/month figure is a
  genuine recurring monthly allocation (not a one-time signup credit — closes item 1). Also purchased a
  10,000,000-credit top-up per the 2026-08-02 `BLK-6728ec9a` Option-B decision already on record in the sibling doc
  (closes item 4's credit-purchase half). Filed both remaining actions as tracked todos above (live re-verification; the
  concurrency/cost-guard fix) rather than leaving them as prose, per this workspace's follow-up discipline.
- **2026-08-03 (slot 9, data_engineering)**: Shipped the first follow-up todo — see the flipped checkbox above for the
  full change description (`deployment-service@28c8d5f`). The second todo (live re-verification of the 10M top-up +
  resuming the live VM) remains open; it still needs live gcloud/Secret-Manager access this sandboxed session does not
  have.
- **2026-08-03 (slot 7, data_engineering)**: This session HAS live gcloud/Secret-Manager access (`gcloud auth list`
  shows `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` already credentialed — the active
  `github-actions-deploy` account lacked `secretmanager.secrets.list`, so switched via
  `gcloud config set account unified-trading-sa@...`, a genuinely ambient identity per RULES.md § 5, not a self-grant).
  Fetched `odds-api-key` (Secret Manager, `central-element-323112`) and curled `https://api.the-odds-api.com/v4/sports`
  live: `HTTP/2 200`, `x-requests-remaining: 14992590`, `x-requests-used: 7410` — sums to exactly 15,000,000 (5,000,000
  recurring base + 10,000,000 top-up), confirming the top-up landed and quota exhaustion is fully resolved. Then checked
  `gcloud compute instances list` for the live VM: found `mtds-live-sports-odds-api-trades-20260803-172841` ALREADY
  RUNNING (created 2026-08-03T17:28:48Z, ~35 min prior to this check) — resumed by a different actor before this task
  picked it up (not launched this session). Verified it is genuinely healthy rather than just started: pulled its full
  `run.log` from
  `gs://deployment-scripts-central-element-323112/vm-logs/mtds-live-sports-odds-api-trades-20260803-172841/run.log` —
  zero `ERROR`/`401`/`exception`/`OUT_OF_USAGE_CREDITS`/`credits_exhausted` matches across the whole log, and its per-VM
  manifest shard
  (`market-data-tick-sports-prd-central-element-323112/_index/per_vm/mtds-live-sports-odds-api-trades-20260803-172841.parquet`)
  is updating every ~60s with "5 total entries, 5 new" — matching the 5-league MVP set (EPL/La Liga/Bundesliga/Serie
  A/Ligue 1), i.e. a genuine fresh poll cycle succeeding against the restored key in production, not merely a
  direct-API-call check. This satisfies the sibling plan's "Done when" bar for its P2 todo (see that plan's own Progress
  Log for the cross-reference). Flipped this doc's second follow-up todo above. No code shipped this session
  (verification-only task; the VM launch itself was someone else's action, not mine to take credit for).
