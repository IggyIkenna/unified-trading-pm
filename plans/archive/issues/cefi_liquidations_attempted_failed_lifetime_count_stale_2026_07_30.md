---
doc_type: issue
title:
  DP-FETCH-009 (cefi/liquidations, 44,422 attempted_failed) — root causes already fixed; alert pages on stale lifetime
  count
summary:
  Escalation agt-029155 (data_pipeline_failure, slot 5) triaged a DP-FETCH-009 CRITICAL page for asset_group=cefi
  data_type=liquidations (44,422 attempted_failed of 749,121 attempted, abs threshold crossed — ratio 5.9% is under the
  10% ratio path). Manifest forensics (availability_index.parquet, `market-data-tick-cefi-prd-central-element-323112`)
  show 94% of the failed rows (41,771) are the documented 2026-07-03/07-15/07-16 Tardis N>1 concurrent-VM 403 storm,
  already fixed by `deployment-service/scripts/vm/tardis-concurrency-guard.sh` (cap=1, hardened through 2026-07-20);
  another 591 rows are the `Resolver requires aiodns library` crash, fixed by market-tick-data-service@6a067cf1
  (2026-07-28 10:31 UTC) — confirmed ZERO recurrence of that error after the fix landed, including on the same day. No
  live code bug was found causing the remaining ~60-row residual trickle across 2026-07-25/26/29 after a Cloud Logging
  VM-creation trace ruled out the one plausible unguarded-concurrent-launch hypothesis (`canonical-migration-cefi-fts-*`
  VMs — confirmed via their own launcher's docstring to make zero live Tardis API calls). `check_high_attempted_failed`
  (DP-FETCH-009, `deployment-service/data_pipeline_monitors/meta_watchers.py`) counts attempted_failed as a LIFETIME
  cumulative total with no recency window, so this cell will keep paging CRITICAL forever even though both root causes
  are fixed — the exact class `known_dead_cells_registry.py` exists for, except its `is_known_dead` contract requires
  literally ZERO attempted_failed activity since narrowing, which this cell does not meet (small ongoing trickle, cause
  unconfirmed). Filed per the "genuinely ambiguous, do not guess" NEEDS-A-HUMAN-DECISION path in the
  data_pipeline_failure role brief; also posted as a bounded `/blocked` question (2-min wait) to the orchestrator
  dashboard.
status: resolved
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [cefi, liquidations, tardis, attempted-failed, manifest, alerting, dp-fetch-009, data-pipeline-alerts, big-finding]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/archive/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: observability_master
priority: P2
source: ["data_pipeline_failure escalation agt-029155, slot 5, 2026-07-30"]
assigned_vm: planning
resolved_by:
  "slot 24, 2026-08-11 — all todos closed; DIAG P3 moot per operator option-A ruling, CODE P2 shipped
  deployment-service@96271280"
resolved_at: "2026-08-11"
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-02
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py,
    deployment-service/deployment_service/data_pipeline_monitors/known_dead_cells_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/attempted_failed_staleness.py,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
  ]
---

> **ARCHIVED 2026-08-11** — all todos resolved. CODE P2: trailing-window fix shipped `deployment-service@96271280`. DIAG
> P3: closed moot — operator ruled option A without the residual-trickle diagnostic. Superseded by: none (the fix is the
> terminal state; no follow-on plan).

# DP-FETCH-009 (cefi/liquidations) pages on a stale lifetime count, not a live regression

## What I found

Escalation context (agt-029155): CRITICAL `DP_RUN_MOSTLY_EMPTY` (registry_id `DP-FETCH-009`) for
`asset_group=cefi data_type=liquidations` — 44,422 `attempted_failed` cells of 749,121 attempted (ratio 5.9%, `abs>=500`
path). Labeled "Fresh — newest attempted_failed activity 0d ago" by
`attempted_failed_staleness.stale_backlog_annotation`. No issue doc was pre-filed; the alert context carried the
candidate numbers only.

Read `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` directly (read-only,
existing single-walk-compliant consolidated index, no new GCS walk) and filtered to `data_type=liquidations`:

- `capture_status` counts: `captured`=704,699, `expected_unattempted`=292,074, `empty_confirmed`=78,608,
  `attempted_failed`=44,422.
- `error_reason` breakdown of the 44,422 failed rows:
  - `Tardis HTTP 403`: 35,911
  - `Tardis HTTP 403 code=274 concurrent-IP-lock`: 5,860
  - `Tardis HTTP 500`: 1,810
  - `Resolver requires aiodns library`: 591
  - `TimeoutError`: 141
  - `Tardis HTTP 400`: 75
  - `Tardis HTTP 503`: 23
  - `404 GET https`: 7
  - `Tardis HTTP 502`: 2
  - `UNCLASSIFIED_VENUE_ERROR`: 1
  - `SCHEMA_VALIDATION_FAILED`: 1
- Venue breakdown: BITGET-FUTURES 35,822; BYBIT 3,885; OKX-SWAP 1,104; BINANCE-FUTURES 1,099; BITFINEX-FUTURES 1,045;
  KRAKEN-FUTURES 949; COINBASE-FUTURES 512; small remainders elsewhere.
- `attempted_at` (when the failure was recorded, not the `date` partition) by day, only days with activity:
  `2026-06-23`=96, `2026-06-24`=1,798, `2026-06-28`=2, `2026-07-03`=33,039, `2026-07-04`=1,602, `2026-07-12`=1,262,
  `2026-07-15`=1,600, `2026-07-16`=4,382, `2026-07-25`=26, `2026-07-26`=214, `2026-07-27`=219, `2026-07-28`=163,
  `2026-07-29`=19. Nothing recorded for `2026-07-30` (today) at read time.
- Per-day `error_reason` breakdown for the tail (last 7 distinct days with activity):
  - `2026-07-15`/`07-16`: 100% `Tardis HTTP 403 code=274 concurrent-IP-lock` (+ a few 400/500/timeout), 100%
    BITGET-FUTURES/OKX-SWAP/KRAKEN-FUTURES/BITFINEX-FUTURES — this is the exact incident documented in
    `tardis-concurrency-guard.sh`'s own header comments (measured 2026-07-16: N=3 lease-ON produced 10,300×403/912 ok on
    one VM and 15,034×403/0 ok on another, +37,212 false `attempted_failed` rows in 8h, coverage went BACKWARD
    52.13→48.38; N=1 produced zero 403s). The guard's cap was set to 1 that same day and hardened further on 2026-07-20
    (`tardis_guard_reserve_slot` binds the cap to actual VM-creation time, closing an estimator-drift race).
  - `2026-07-26`/`07-27`/`07-28`: 100% `Resolver requires aiodns library`, ~150-220/day, COINBASE-FUTURES +
    BITFINEX-FUTURES. `git log` on `market_tick_data_service/market_interface/clients/tardis_base_client.py` shows
    commit `6a067cf1` ("fix(cefi): route Tardis clients through make_resilient_connector to survive missing aiodns"),
    authored 2026-07-28T10:31:38Z, already on `live-defi-rollout` HEAD. The 2026-07-28 failures (159 in the 06:00 UTC
    hour bucket, 4 in the 09:00 bucket) all predate the 10:31 UTC fix commit. Zero `Resolver requires aiodns library`
    rows exist for `2026-07-29` or later — the fix is confirmed effective.
  - `2026-07-29`: 15× `Tardis HTTP 403 code=274 concurrent-IP-lock` (COINBASE-FUTURES) + 3× `404 GET https` + 1×
    `UNCLASSIFIED_VENUE_ERROR` — small residual trickle, not the aiodns class (already fixed) and not the
    07-03/07-16-scale mass-403 class (guard already caps VM count at 1). Checked `gcloud logging read` for
    `compute.instances.insert` events around this window (04:00-10:00 UTC) for anything matching `cefi`/`tardis`: only
    `canonical-migration-cefi-fts-{bitget-futures,okx-swap,binance-futures}-20260729-*` VMs, launched ~09:04- 09:06 UTC
    (3 VMs within 2 minutes). Read `launch-cefi-funding-timestamp-fix-vm.sh` (the launcher for that VM name shape) — its
    own header comment states it makes **zero live calls to Tardis's API** (GCS-only reprocessing of already-downloaded
    parquet via `reprocess_bulk_tardis_derivative_ticker_funding_timestamp_ 2026_07_28.py`), so it cannot be the source
    of a Tardis-side concurrent-IP-lock 403 — ruled out. No other Tardis-named VM creation event exists in that window.
    No currently-running instance matches `tardis-concurrency-guard.sh`'s `TARDIS_VM_NAME_PATTERN` or
    `VM_TARDIS_CONSUMER=1` metadata at read time either. I could not identify a live code bug behind this small trickle
    within the escalation's bounded scope.

## Why it matters

Two distinct, already-shipped fixes fully explain 94%+ of this cell's cumulative `attempted_failed` count (41,771 of
44,422 rows: the Tardis N>1 concurrency storm + the aiodns resolver crash). `check_high_attempted_failed`
(`deployment-service/data_pipeline_monitors/meta_watchers.py:540`) computes `attempted_failed` as a **lifetime
cumulative count** over the whole consolidated manifest, with no recency window — so once a cell crosses
`ATTEMPTED_FAILED_ABS_THRESHOLD` (500) from a NOW-FIXED historical incident, it stays HIGH and re-pages
`DP_RUN_MOSTLY_EMPTY` CRITICAL forever, even with zero new failures. This is exactly the failure mode
`known_dead_cells_registry.py` was built to close (see its own docstring + the `tradfi/ohlcv_15m` precedent entry) — but
that registry's `is_known_dead` deliberately requires **zero** attempted_failed activity newer than the registered
`narrowed_at` date ("any row with `attempted_at > narrowed_at` ... is a genuinely new signal and MUST page"). This cell
does not meet that bar: a small trickle (≈15-26 rows/day, ~0.003% of captured volume) continued through 2026-07-29, and
I could not root-cause it to a specific live code defect after a bounded investigation (VM-creation audit-log trace +
launcher-doc read ruled out the one plausible unguarded-concurrent- launch hypothesis).

This is the same open question `attempted_failed_staleness.py`'s own module docstring flags: "this module only makes the
distinction VISIBLE, deliberately leaving delivery behavior untouched. That is a separate, still-open policy question
for the operator/alerting-service owner." Forcing a `known_dead_cells_registry.py` entry here would mean either (a)
violating the registry's own documented zero-tolerance safety invariant by registering a cell with live (if tiny)
ongoing activity, or (b) waiting for the trickle to hit literally zero — which may never happen if it is inherent
low-rate noise (e.g. an unavoidable few-second VM-boot-window overlap already narrowed by the guard's 2026-07-16/07-20
hardening) rather than a fixable bug. Deciding how to handle a cell whose detector-classification is dominated by
resolved history is a policy call the codebase explicitly reserves for the operator, not something this escalation
should decide unilaterally.

## Recommended decision

Also posted as a bounded (2-min) `/blocked` question from slot 5 with the same options. Recording here so the finding is
not lost if the bound expires unanswered.

- **A [RECOMMENDED]**: Change `check_high_attempted_failed` to compute the abs/ratio thresholds over a TRAILING window
  (e.g. last 7 or 14 days of `attempted_at`) instead of the full lifetime manifest, so a cell whose root cause is fixed
  stops paging once the fixed-era failures age out — closes this alert CLASS generally (every AG/ data_type cell), not
  just this one instance. Bigger, more invasive change to shared alerting code; needs operator sign-off per
  `attempted_failed_staleness.py`'s explicit "still-open policy question" framing.
- **B**: Loosen `known_dead_cells_registry.is_known_dead` to tolerate a small residual-noise floor (e.g. <N rows/day)
  instead of requiring literally zero new activity, then register `(cefi, liquidations)` narrowed at `2026-07-28` (the
  aiodns fix date). Smaller, more surgical change, but weakens a deliberately conservative safety invariant the
  registry's own docstring calls out — risks silently reintroducing exactly the "quietly stops paging on a live
  regression" failure mode the registry was designed to prevent.
- **C**: Leave the alert/registry mechanism unchanged; accept that this cell keeps CRITICAL-paging on every sweep until
  the residual trickle also hits zero. Lowest risk, but the alert stays noisy/misleading (paging as if fresh when 94% of
  its weight is dead history) for however long the trickle persists.

## Todos

- [x] [CODE] P2. **RULED 2026-08-06 (operator), option A: approved.** `[CODE]` tag (was `[OPERATOR]`), AO-dispatchable —
      change `check_high_attempted_failed` to compute thresholds over a trailing window (7-14 days) instead of the full
      lifetime manifest, closing this alert class generally. Decide among options A/B/C above (or another approach) for
      how `DP-FETCH-009` should treat a cell whose `attempted_failed` classification is dominated by already-fixed
      historical incidents. Repo: deployment-service. ✅ deployment-service@96271280 — added
      `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` constant; `_read_attempted_failed_cells` now filters attempted_failed
      rows to the 14-day trailing window (NaT rows treated as recent, conservative); `check_high_attempted_failed`
      accepts injectable `now=` for deterministic testing; 3 existing tests updated + 3 new trailing-window tests added;
      QG green.
- [x] ✅ [DIAG] P3. ~~If the operator wants the residual trickle root-caused before deciding: pull Cloud Logging /
      Tardis-side request logs for the exact process that produced the 2026-07-29 09:00 UTC
      `Tardis HTTP 403 code=274 concurrent-IP-lock` COINBASE-FUTURES rows~~ **MOOT** — operator ruled option A on
      2026-08-06 without this diagnostic; trailing-window fix (deployment-service@96271280) makes the residual trickle
      irrelevant for alerting. The DIAG was conditional on operator wanting it before deciding, and the decision was
      made without it. Slot 24, 2026-08-11.

## Progress log

- 2026-07-30: Filed by `data_pipeline_failure` escalation `agt-029155` (slot 5). Root-caused 94% of the
  `attempted_failed` volume to two already-fixed issues (Tardis concurrency guard + aiodns resolver crash, commit
  `6a067cf1`); ruled out one hypothesis for the residual trickle via Cloud Logging + launcher-doc read; no code changed
  (nothing left to fix — both major root causes are already shipped). Escalated the alert-design question
  (lifetime-count vs recency-window) via `/blocked` per the role's genuinely-ambiguous-decision path.
- **2026-07-30 (data_pipeline_failure escalation worker, `agt-d36d2a`, slot 2) — 2nd dispatch, re-fire confirmed
  static.** Re-page carried `44,422 attempted_failed of 749,123 attempted` (ratio 5.9%) vs this doc's original reading
  of `44,422 / 749,121` — the `attempted_failed` numerator is byte-identical; only `attempted` (denominator) grew by 2,
  consistent with the boot context's own `attempted_failed_staleness` label "no new attempted_failed activity in 1d".
  Per the skip-condition this corpus has converged on (see
  `/plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s 2026-07-30 entries — "no new
  activity since the doc's last verified reading", not a fresh full manifest read every time), did a cheap git-ancestor
  check instead of re-deriving the diagnosis: `market-tick-data-service@6a067cf1` (aiodns fix) is still an ancestor of
  `origin/live-defi-rollout`, and `deployment-service/scripts/vm/tardis-concurrency-guard.sh` still caps
  `TARDIS_MAX_CONCURRENT_VMS=1`. Both root-cause fixes remain in place; no new failure class observed; the operator
  decision on lifetime-count-vs-trailing-window (options A/B/C above) is still open and unaffected by this re-fire. No
  code changed. Also filed `/plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` (if
  not already cross-linked) as the standing meta-issue this repeat dispatch itself is an instance of.
- **na-eligibility-audit 2026-07-31** (tranche=cefi, autonomous): KEEP-NA, valid — both open todos are explicitly
  `[OPERATOR]`/operator-conditional (decide among options A/B/C; the DIAG follow-up is gated on that decision). Not
  worker-determinable.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **2026-08-02 (data_pipeline_failure escalation worker, `agt-4255c7`, slot 2) — 3rd dispatch, re-fire confirmed
  static.** Re-page carried `44,425 attempted_failed of 749,139 attempted` (ratio 5.9%) vs the 2nd dispatch's
  `44,422 / 749,123` — `attempted_failed` grew by only 3 rows and `attempted` by 16 over the intervening period,
  matching the boot context's own `attempted_failed_staleness` label ("only 3 attempted_failed row(s) in the last 1d —
  below the 500-row materiality floor; a decaying trickle on already-tracked backlog, not a fresh regression"). Per the
  established skip-condition (`/plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`),
  did a cheap verification instead of re-deriving the diagnosis: confirmed `market-tick-data-service@6a067cf1` (aiodns
  fix) is still an ancestor of `origin/live-defi-rollout`, and
  `deployment-service/scripts/vm/tardis-concurrency-guard.sh` still caps `TARDIS_MAX_CONCURRENT_VMS=1`. Both root-cause
  fixes remain in place; no new failure class observed; the operator decision on lifetime-count-vs-trailing-window
  (options A/B/C above) is still open and unaffected. No code changed.
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): KEEP-NA, valid — re-verdicted because the 2026-08-02
  3rd-dispatch entry above postdates the 07-31 marker, but that entry records a static-backlog re-confirmation only (+3
  `attempted_failed` rows, both root-cause fixes still ancestors of LDR), adding no new work. Verdict unchanged: the
  `[OPERATOR] P2` todo is an explicit A/B/C policy choice over shared alerting code, and the `[DIAG] P3` follow-up is
  gated on that choice. Neither is worker-determinable.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — body unchanged since 2026-08-01, existing list
  still accurate.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (governance-sweep reclassification pass)**: RECLASSIFY,
  `assigned_vm: NA -> planning`. Todo 1's A/B/C policy choice was resolved this same session ("RULED 2026-08-06
  (operator), option A: approved", retagged `[OPERATOR] -> [CODE]`) — the remaining work (trailing-window threshold
  instead of lifetime count in `check_high_attempted_failed`,
  `deployment-service/data_pipeline_monitors/meta_watchers.py`) is a bounded, single-file change; todo 2's `[DIAG]`
  follow-up is a bounded log-pull conditional on the same decision. Conflict-check cleared (no overlapping claim in
  `parent_epic: observability_master`). `assigned_role` was unset in this doc; filled `data_engineering` per the corpus
  convention for `data_pipeline_monitors`-touching docs.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-07 (batch11 independent re-verify)**: all 5 entries confirmed resolving on disk; content
  unchanged.
- **slot-6 2026-08-08 (todo-1 SHIPPED)**: Implemented option A — 14-day trailing window for
  `check_high_attempted_failed`. Added `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` constant;
  `_read_attempted_failed_cells` now counts only `attempted_failed` rows where `attempted_at >= (now - 14d)` (NaT rows
  treated as "recent" to avoid silencing genuine failures with missing timestamps); `max_attempted_at` + staleness
  metadata still use the lifetime set for diagnostic value. `check_high_attempted_failed` accepts
  `now: datetime | None = None` for testing. Updated 3 tests that used hardcoded 2026-07-07 timestamps (now outside the
  window) to inject `now=datetime(2026,7,20,UTC)`. Added 3 new tests: old-outside-window no-page, cefi/liquidations
  exact-scenario (44k old + 26 fresh = no page), recent-within-window still-pages. QG green (952 lines < 960 cap).
  Shipped: `deployment-service@96271280`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate -- the shipped fix
  landed in `meta_watchers.py`, already covered.
- **slot-24 2026-08-11 (todo-2 CLOSED MOOT)**: The DIAG P3 follow-up was conditional on the operator wanting the
  residual trickle root-caused before deciding among options A/B/C. Operator ruled option A on 2026-08-06 without this
  diagnostic; the trailing-window fix (`deployment-service@96271280`) is confirmed on LDR and makes the residual trickle
  irrelevant for alerting purposes. Todo closed as moot — no code change needed.
