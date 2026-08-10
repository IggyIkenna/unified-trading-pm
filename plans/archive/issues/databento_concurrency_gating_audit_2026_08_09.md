---
doc_type: issue
title: Databento concurrency-gating audit — does the Tardis-style hard VM cap apply? (it does not)
summary: >-
  Operator asked whether Databento (TradFi market-data vendor) needs the same class of hard concurrent-VM cap as Tardis
  (`tardis-concurrency-guard.sh`, cap=1 both clouds). Audited codex docs, existing launcher guards, live Cloud Logging,
  and current live VM state. Finding: no-constraint-found-no-action-needed — Databento's rate limits are documented
  PER-IP (`DatabentoIPRateLimiter._RAW_LIMITS`), and every backfill VM gets its own ephemeral external IP (no shared
  NAT), so concurrent VMs do not divide a shared budget the way Tardis's single shared-IP academic key does. This is
  already correctly documented in `deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` (explicit "NOT the
  Tardis situation" comment) and already courtesy-guarded (fleet cap=150, raised from 20 -> 60 -> 150 as evidence
  accumulated that concurrency is safe). Live evidence same-day: 10 tradfi-bf-* VMs running concurrently right now with
  zero rate-limit errors; last 48h Cloud Logging shows only 10 total Databento 429s, one isolated 3-minute burst, all
  classified retryable/auto-retried, no storm, no recurrence despite the current 10-VM fleet. No new guard built —
  building a Tardis-style hard cap for Databento would be gating a vendor that measurably does not need it.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data, infra]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, databento, concurrency, rate-limit, vm-launcher, audit, tardis]
related:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md,
    /plans/active/issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md,
  ]
created: 2026-08-09
author: claude-code (interactive session, operator-asked discovery question, 2026-08-09)
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
source:
  [
    "Operator chat instruction, 2026-08-09: does the same per-data-source concurrency constraint that applies to Tardis
    (hard cap 1 concurrent VM, tardis-concurrency-guard.sh) also apply to Databento, and if so is it similarly guarded,
    or is this a gap nobody has closed for Databento specifically?",
  ]
resolved_by: self (audit concluded with a clear finding same session, no follow-up required)
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh,
    deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh,
    market-tick-data-service/market_tick_data_service/market_interface/clients/databento_key_cache.py,
  ]
drift_direction: advance-code
depends_on: []
---

# Databento concurrency-gating audit — does the Tardis-style hard VM cap apply?

> **🟢 RESOLVED (2026-08-09, same session as filing)** — audit concluded with a clear
> no-constraint-found-no-action-needed finding; no follow-up work, archived immediately per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

## The question

The workspace has a HARD, documented rule that Tardis VMs are capped at **1 concurrent VM across both clouds**, enforced
by `deployment-service/scripts/vm/tardis-concurrency-guard.sh`, because Tardis's academic key allows only **one active
IP** — every N>1 datapoint historically produced a mutual-403 storm (measured: N=3 lease-ON → 10,300×403/912 ok on one
VM, +37,212 false `attempted_failed` rows, coverage went BACKWARD). Operator asked: does the same class of constraint
apply to **Databento** (the TradFi vendor), and if so, is it guarded — or is this a gap nobody has closed?

## Answer: NO — Databento is architecturally different, and this is already correctly documented

**Databento's rate limits are per-IP, not per-account/per-key.** `DatabentoIPRateLimiter`
(`market-tick-data-service/market_tick_data_service/market_interface/clients/databento_key_cache.py` lines 130-183) is a
**process-level singleton specifically because Databento limits are per IP address, not per API key** — "All clients in
the same process share one IP and therefore one rate limit budget. Each Cloud Run instance (different IP) gets its own
limiter." The documented raw per-IP limits: `timeseries`/`symbology` = 100 calls/sec, `metadata` = 20 calls/sec,
`batch.list_jobs` = 20/sec, `batch.submit_job` = 20/60s, and `MAX_CONCURRENT` = 100 concurrent connections per IP.

**Every TradFi backfill VM gets its own ephemeral external IP** (no `--no-address`, no shared NAT) — confirmed in
`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` lines 164-193, which contains an **explicit, pre-existing
correction against exactly this reasoning**:

> "THIS IS A COURTESY CAP, NOT A SAFETY CAP — and it is emphatically NOT the Tardis situation. The Databento limits
> above are PER-IP, and `ohlcv_create_vm` gives every VM its own ephemeral external IP..., so the 100-connection /
> 100-req-s budget is spent PER VM. Adding VMs adds budget; it does not divide a shared one. Do NOT apply Tardis-style
> cap-1 reasoning here (Tardis shares ONE IP...)."

This is the opposite architecture from Tardis (one shared academic key/IP for the whole team) — Databento's constraint
scales _with_ the fleet, not against it.

## What already exists (this is NOT an unguarded gap)

Two independent courtesy/cost guards already exist in `deployment-service/scripts/vm/`, both predating this audit:

1. **`_tradfi-ohlcv-launcher-lib.sh::ohlcv_check_singleton_lock`** — fleet concurrency cap on `^tradfi-bf-*` VMs,
   `OHLCV_FLEET_CONCURRENCY_CAP` (env-overridable). History: 20 (initial) → 60 (2026-07-20, equity ticker-group
   re-shard) → **150 (2026-07-25, current)**, raised each time as measured evidence accumulated that concurrency is safe
   (18 concurrent VMs measured with **zero 429s**, `instruments_foundation_completeness_2026_06_24.md`). This is a
   cost/waste courtesy cap (avoid redundant compute), explicitly NOT framed as vendor-storm protection.
2. **`launch-tradfi-backfill-vm.sh::_check_singleton_lock`** — an older, stricter cap=1 singleton on the same
   `^tradfi-bf-*` prefix, used only by the ES/BTC/ETH/ES_OPT root-symbol launcher family. Rationale given: "the
   Databento account is shared; concurrent VMs on wide windows risk contract-exceeded errors" — a team/account-sharing
   courtesy, not a documented technical rate-limit (no citation of `DatabentoIPRateLimiter` or a measured storm, unlike
   the Tardis guard's incident trail). `--force` bypasses it "for legitimate parallel investigations."

**Neither is a gap** — both existed before this audit and both fail closed (refuse-by-default, override via
`--force`/env). They are inconsistent with each other (cap=1 vs cap=150 on the same VM-name prefix) but that
inconsistency is a **pre-existing, already-tracked operational-friction issue**, not a missing safety guard — see
"Related, NOT duplicated" below.

## Live evidence gathered this session (2026-08-09)

- **Current live state**: 10 `tradfi-bf-*` VMs RUNNING concurrently right now in `asia-northeast1-c`
  (`tradfi-bf-cme-ohlcv-1m-*` ×2, `tradfi-bf-ice-idx-ohlcv-24h-*` ×6 covering years 2019-2026, `tradfi-bf-fred-full-*`
  ×1) — well under the cap-150 fleet guard, zero issues observed.
- **Cloud Logging, last 48h** (`gcloud logging read`, project `central-element-323112`): exactly **10** Databento
  `429 Too Many Requests` log lines total, all in a single **~3-minute burst** (2026-08-09T00:10:52Z–00:13:14Z), all on
  `URDI[NYSE|NASDAQ|CME]` instrument-definition fetches (DBEQ.BASIC/GLBX.MDP3), every one classified
  `RATE_LIMIT (retryable)` / `action: retry` by the adapter's `classify_venue_error()` path — i.e. the existing
  self-healing retry logic handled every one; **no recurrence** since, despite the 10-VM fleet running the whole time.
  No `DP_SOURCE_RATE_LIMITED` events fired at all in the last 30 days (the IP-limiter's own preemptive throttle never
  even needed to engage). A separate, unrelated, recurring `504 gateway timeout` (`classified: UNKNOWN, action: fail`)
  on one specific `GLBX.MDP3 symbols=78` job appears both yesterday and today at ~1.5min intervals — a vendor-side
  gateway issue, not a rate-limit/concurrency signature (no 403/429, no burst-then-storm shape); out of scope for this
  audit, flagged here only for completeness in case it warrants its own follow-up later.
- **Conclusion**: this is a **theoretical-risk-that-doesn't-materialize**, not an actual, already- happening problem.
  The vendor's own architecture (per-IP budget, VM-count-scaling headroom) plus the adapter's existing
  retry-classification already absorb the rare 429 without operator action.

## Related, NOT duplicated — do not confuse with this audit's finding

Two OPEN issue docs describe a **real, currently-active operational problem** that superficially looks related (both
mention "singleton lock" and "rate-limit collision") but is a **different failure class**:
`/plans/active/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` and
`/plans/active/issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` describe a stray
`wave_launcher.py` cron/timer on the orchestrator VM that keeps re-launching duplicate and out-of-scope `tradfi-bf-*`
VMs, which (a) wastes VM-minutes/API calls on already-complete years and (b) queues up against the cap=1
`_check_singleton_lock`, blocking a legitimate operator-authorized ES_OPT relaunch for >1hr. **This is a
waste/coordination bug in a cron job, not evidence of a Databento rate-limit constraint** — the cited "rate-limit
collision" risk in those docs is the operator/agent being appropriately cautious about an UNVERIFIED risk while
investigating, not a measured storm (this audit's Cloud Logging pull found none). Those docs already carry their own P1
action item (find + fix the cron/timer mechanism) — not duplicated here. If that fix later normalizes the two singleton
mechanisms (cap=1 vs cap=150) for consistency, that is their scope to do, informed by this audit's finding that
concurrency itself is safe up to at least 18 VMs (measured) / currently running 10 clean.

## Disposition

**no-constraint-found-no-action-needed.** No code changed, no new guard built. Databento does not need a Tardis-style
hard concurrency cap — building one would gate a vendor that measurably does not require it, contradicting the existing,
correct `_tradfi-ohlcv-launcher-lib.sh` documentation and the live evidence gathered here. The two pre-existing courtesy
guards (cap=150 fleet, legacy cap=1 singleton) remain in place unchanged; their cross-launcher inconsistency is real but
belongs to the two open issue docs above, not this one.
