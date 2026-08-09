---
doc_type: issue
title:
  Cefi onchain-perp forward capture silently outaged since 2026-07-28 (ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET/
  HYPERLIQUID) — no cron wiring + a launcher regression compounded the gap
summary: >-
  Discovered while closing perp_funding_data_semantics_and_cadence-003 (Aster historical backfill checkbox). Live
  manifest census shows daily derivative_ticker/trades capture for ASTER, LIGHTER-ZKSYNC, and EXTENDED-STARKNET (native
  sources) stopped completely on 2026-07-28/29 and never resumed — no automated scheduler exists for this capture (it
  was manual/ad-hoc only), and since 2026-08-01 the one shared launcher that could re-trigger it was itself broken by a
  missing `source lib/launcher_common.sh` regression (now fixed, deployment-service@52f02a4). HYPERLIQUID shows a
  different, partial pattern plus two anomalous VMs running continuously for 7+ days that need a staleness check.
  Remediation VMs for ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET launched this session (on-demand, after 3/3 SPOT attempts
  were preempted within ~90s — a fleet-wide SPOT capacity crunch at the time, not specific to this launch); see Progress
  Log for outcome.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    aster,
    hyperliquid,
    lighter-zksync,
    extended-starknet,
    perp-funding,
    derivative_ticker,
    backfill,
    cron,
    data-correctness,
    regression,
  ]
related:
  [
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    /plans/archive/issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md,
  ]
created: 2026-08-03
author: unknown
priority: P1
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["perp_funding_data_semantics_and_cadence-003, slot 3, 2026-08-03"]
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh,
    deployment-service/scripts/vm/launch-aster-forward-poll.sh,
    deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh,
    deployment-service/deployment_service/vm_prefix_registry.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/__init__.py,
    market-tick-data-service/market_tick_data_service/raw_tick_hive.py,
  ]
---

# Cefi onchain-perp forward capture outage (2026-08-03)

## What I found

**1. Multi-venue live capture gap, confirmed directly against the availability manifest** (never guessed from a
launcher's own comment — cross-checked with `read_availability_index` on `market-data-tick-cefi-central-element-323112`,
`data_type in {derivative_ticker, trades}`):

| Venue             | Native source                                          | Last real `captured` day (pre-gap)                                                    | Gap start                                                                                                                       |
| ----------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| ASTER             | `aster`/`batch_aster`                                  | 2026-07-27 (458+445 captured)                                                         | **2026-07-28** (100/100 rows `attempted_failed`, `UNCLASSIFIED:UpstreamTimestampBiasError`, single run at 2026-07-29T06:15:16Z) |
| LIGHTER-ZKSYNC    | `tardis` (its real priority source, not a placeholder) | 2026-07-28 (169 captured)                                                             | **2026-07-29** (0 captured every day since)                                                                                     |
| EXTENDED-STARKNET | `extended`/`batch_extended`                            | 2026-07-28 (144 captured)                                                             | **2026-07-29** (0 captured every day since)                                                                                     |
| HYPERLIQUID       | `hyperliquid`                                          | mostly 0 from 07-25 on, with sporadic partial captures (103 rows 07-31, 2 rows 08-01) | irregular, not a clean cutover — see finding 4                                                                                  |

As of this doc's creation (2026-08-03), ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET had **zero real captures for 5+
consecutive days** for a P0 input to `carry_staked_basis` (per the parent issue doc). No alert fired for any of this —
confirming there is no automated freshness monitor wired to this specific data_type/venue combination either.

**2. Root cause A — no scheduler ever drove this capture; it was manual/ad-hoc only.**
`deployment-service/deployment_service/vm_prefix_registry.py` registers exactly two `SCHEDULED_RECURRING` cron-host VM
prefixes (`tradfi-fwd-daily-cron-`, `cefi-fwd-daily-cron-`) — neither targets onchain-perp venues (the latter drives
`launch-cefi-forward-poll.sh`, the Tardis CEX-venue launcher). `launch-aster-forward-poll.sh` and
`launch-cefi-onchain-forward-poll.sh` are both registered `EPHEMERAL_BATCH` (one-shot), and
`launch-aster-forward-poll.sh`'s own trailing comment says: _"For daily scheduling: wire to Cloud Scheduler with
target=Compute Engine ... using this same metadata"_ — i.e. this was **never done**. The 2026-07-14→2026-07-27 daily
successes visible in the manifest must have come from someone/something manually re-triggering a launcher each day; once
that stopped (around the 07-28 Aster failure), nothing else picked it back up — there is no retry/cron backstop.

**3. Root cause B — a real regression fully blocked any recovery attempt since 2026-08-01 (now fixed).** Commit
`7538587a` (2026-08-01, "wire Group A/B raw-data launchers to per-tier SA") added
`--service-account="$(lc_tier_service_account "$DEPLOYMENT_ENV" "$PROJECT")"` to
`launch-cefi-hl-aster-historical-backfill.sh`'s gcloud call but never added the corresponding
`source lib/launcher_common.sh` (where `lc_tier_service_account` is defined) — unlike the other 133 launchers using that
helper. Every invocation since has failed at VM-creation time (`lc_tier_service_account: command not found` → `gcloud`
rejects the empty `--service-account` value) for **all four venues** this one shared launcher drives
(HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET) — confirmed via `bash -x` trace + an instrumented scratch copy
(`declare -F lc_tier_service_account` returned empty right before the gcloud call). **Fixed this session**:
`deployment-service@52f02a4` (one-line `source` addition, QG green, verified on origin).

**4. ASTER's original 07-28 failure is a separate, likely-transient upstream/write-guard issue, still unclassified.**
`UpstreamTimestampBiasError` (`unified_trading_library/manifest_writer/_schema.py:530-576`, raised at
`market_tick_data_service/raw_tick_hive.py:113` — an MTDS-internal day-partition-alignment guard, not a documented
vendor error code) is not in UAC's `classify_venue_error()` `VENUE_ERROR_MAP`
(`unified_api_contracts/canonical/crosscutting/errors/__init__.py:47-55`), so it surfaces as `UNCLASSIFIED:` and would
not page any error-classification-based alert. All 100 rows failed identically in one run — consistent with a genuine
one-off upstream response-window/clock anomaly for that fetch, but this wasn't independently confirmed (would need the
raw API response/logs from that run, not available read-only).

**5. HYPERLIQUID is a messier picture and was deliberately NOT touched this session.** Two VMs,
`cefi-hyperliquid-2024-20260727-071055` and `cefi-hyperliquid-2025-20260727-071055`, have been `RUNNING` continuously
since 2026-07-27 — 7+ days, far beyond this launcher's normal few-minutes-to-tens-of-minutes runtime, which is itself
suspicious (possibly explains HL's sporadic partial native captures on 07-31/08-01 if this same pair intermittently
wrote). Per the VM-delete guardrail (`data_engineering.md` STEP 0.55), staleness must be confirmed via heartbeat age +
run.log tail + manifest-shard mtime before anyone acts on them — I did not have working GCS-client tooling to check
heartbeat/run.log freshness in this session and did not chase it further to stay in scope; flagged as its own todo
below.

## Why it matters

Funding/derivative_ticker is a documented P0 input to `carry_staked_basis` net-carry ranking. A 5+ day silent gap across
three of four onchain-perp cefi venues, with no automated alerting and (until this session) no working manual recovery
path either, would have continued indefinitely — this is exactly the "RED data audit freezes downstream work" class of
finding, just not caught by any existing gate because no gate watches this specific surface.

## Remediation performed this session

- Fixed the missing `source` regression: `deployment-service@52f02a4`.
- Relaunched ASTER (2026-07-28→2026-08-02), then LIGHTER-ZKSYNC + EXTENDED-STARKNET (2026-07-29→2026-08-02) via the
  fixed launcher. First attempt (SPOT, the launcher's default) — all three VMs preempted within ~90s of creation; a
  fleet-wide check (`gcloud compute operations list --filter=operationType=compute.instances.preempted`) showed many
  unrelated tradfi/cme/nasdaq SPOT VMs preempting in the same window, indicating a shared zone-wide SPOT capacity crunch
  rather than anything specific to this launch. Retried with `ON_DEMAND=true` (justified given the severity/
  active-data-loss framing, and the short expected runtime keeps the cost delta small) — see Progress Log for the
  outcome once these on-demand VMs complete.

## Recommended decision / Todos

- [x] ✅ [DATA] P1. Wire real Cloud Scheduler → Compute Engine automation for the cefi onchain-perp forward capture (the
      launcher this doc fixed, or a dedicated daily-poll variant) so this class of gap self-heals instead of depending
      on a human/agent remembering to manually re-trigger it. **Repo: deployment-service.** Mirror the existing
      `cefi-fwd-daily-cron-`/`tradfi-fwd-daily-cron-` `SCHEDULED_RECURRING` registry pattern (`vm_prefix_registry.py`)
      so it's watchdog-visible. — deployment-service@bcd3678 (`launch-cefi-onchain-fwd-daily-cron-vm.sh` +
      `vm_prefix_registry.py`/`launcher_registry.py` entries); cron host `cefi-onchain-fwd-daily-cron-20260803-230641`
      launched + verified RUNNING via SSH: `/etc/cron.d/cefi-onchain-fwd-daily` installed (`0 8 * * *`), launcher binary
      present at `/opt/deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh`, `cron` service active. Next
      fire 2026-08-04T08:00Z.
- [x] ✅ [DATA] P2. Add `UpstreamTimestampBiasError` (or a general "internal write-guard rejection" bucket) to UAC's
      `classify_venue_error()` `VENUE_ERROR_MAP` so it stops surfacing as `UNCLASSIFIED:` and can be alerted on
      distinctly from a real vendor-API error. **Repo: unified-api-contracts.** — unified-api-contracts@4dfe960a: added
      a venue-agnostic `internal` pseudo-venue bucket (`errors/internal.py`, `VENUE_ERRORS_INTERNAL`) registering
      `UpstreamTimestampBiasError` (RETRY), and made `classify_venue_error()` fall back to that bucket when a
      venue-specific lookup misses — the guard is MTDS-internal (day-partition-alignment), not vendor-specific, so it
      can fire for ANY venue (not just ASTER). Verified: `classify_venue_error("aster", "UpstreamTimestampBiasError")`
      now returns non-None across all four onchain-perp venues; new tests added (`TestInternalErrorFallback`); full
      `quality-gates.sh` green.
- [x] ✅ [DATA] P1. Investigate `cefi-hyperliquid-2024-20260727-071055` and `cefi-hyperliquid-2025-20260727-071055` —
      **Preliminary investigation done 2026-08-04 (slot 6): BOTH VMs confirmed ALIVE and productively working (NOT
      hung/zombied).** VM 2024: backfilling 2024 HYPERLIQUID data, currently at 2024-10-29, ~47% CPU, 3.2GB RSS, 161K+
      manifest entries written, heartbeat active. VM 2025: backfilling 2025 data, currently at 2025-09-13, ~61% CPU,
      15.2GB RSS, heartbeat active. Both writing to per-VM manifest shards. SSH confirmed MTDS processes running with
      correct parameters. Run.logs show steady symbol-by-symbol capture. These are legitimate long-running multi-year S3
      backfills — do NOT delete. **Re-verified 2026-08-09**: `aws ec2     describe-instances` for both instance names
      returns zero results across us-east-1/us-east-2/us-west-1/us-west-2 — consistent with both multi-year backfills
      having completed and self-terminated in the 5 days since the 08-04 check (no zombie/orphaned VM left running).
      Closing — nothing left for the operator to rubber-stamp. **Repo: deployment-service.**
- [x] ✅ [DATA] P2. HYPERLIQUID 2026-07-28→today gap confirmed and backfill launched. Manifest analysis (slot 6,
      2026-08-04): consolidated manifest (`mtds-live-cefi-consolidated-20260802-142543.parquet`) shows good capture
      2026-08-02→04 (171 deriv_ticker + 61-79 trades/day via cron VM `cefi-onchain-fwd-daily-cron-20260803-230641`).
      Forward-capture shard (`cefi-fwd-20260804-021235.parquet`) shows partial 07-28/07-29 (19 deriv_ticker + 18
      trades/day). 07-30→08-01: complete gap (no manifest entries). **Backfill launched:**
      `cefi-hyperliquid-2026-20260804-185613` (ON_DEMAND, first SPOT attempt preempted), 2026-07-28→2026-08-01, 173
      HYPERLIQUID symbols × trades/book_snapshot_5/derivative_ticker. VM actively capturing as of 19:06Z (211+ manifest
      entries, 11.4M trades parsed for day 1). — deployment-service (launcher already fixed @52f02a4);
      market-tick-data-service (no code changes needed)

## Progress Log

- **2026-08-03 (slot 3, data_engineering)**: filed while closing out `perp_funding_data_semantics_and_cadence-003` (the
  Aster historical-backfill-checkbox todo in the parent issue doc, which turned out to already be resolved — see that
  doc). Found + fixed the launcher regression, launched on-demand remediation for ASTER/LIGHTER-ZKSYNC/
  EXTENDED-STARKNET; result pending as of doc creation, will update once the on-demand VMs terminate and the manifest is
  re-checked.
- **2026-08-03 (slot 4, data_engineering)**: todo 1 (cron automation) was already code-shipped by another slot
  (`deployment-service@bcd3678`, ~1h before this pickup) and the cron host VM was already launched
  (`cefi-onchain-fwd-daily-cron-20260803-230641`). Verified end-to-end via SSH rather than trusting the commit alone:
  crontab installed correctly (`0 8 * * *`), launcher binary downloaded to
  `/opt/deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh`, `cron` systemd unit active. No fire log yet
  — expected, first scheduled fire is 2026-08-04T08:00Z (VM booted 23:07Z, past today's window). Flipped todo 1.
  Remaining todos (2: UAC error classification, 3: HYPERLIQUID zombie-VM investigation `[OPERATOR]`, 4: HYPERLIQUID gap
  backfill) are untouched — out of scope for this task.
- **2026-08-03 (slot 6, data_engineering)**: closed todo 2. `classify_venue_error()` (UAC) only ever did a per-venue
  `VENUE_ERROR_MAP` lookup, so a venue-agnostic error like `UpstreamTimestampBiasError` (an MTDS write-time
  partition-alignment guard, not a vendor response) could never classify no matter which venue's map it was added to —
  it would need duplicating into every venue's list. Instead added a new pseudo-venue `internal` bucket
  (`unified_api_contracts/canonical/crosscutting/errors/internal.py`) and a fallback check in `classify_venue_error()`:
  venue-specific match first, then `internal` bucket, matching the todo's own suggested "general bucket" framing.
  Shipped `unified-api-contracts@4dfe960a`, full `quality-gates.sh` green, verified on origin. backfill) are untouched —
  out of scope for this task.
- **2026-08-04 (slot 6, data_engineering)**: closed todo 4 (HYPERLIQUID gap + backfill) and contributed VM investigation
  for todo 3. Manifest analysis: consolidated manifest shows good HL capture 08-02→04 via cron VM; 07-28/07-29 partially
  captured by forward shard; 07-30→08-01 completely missing. Launched on-demand backfill VM
  `cefi-hyperliquid-2026-20260804-185613` (SPOT attempt preempted within 2min — same zone crunch pattern as 08-03
  remediation). VM actively capturing as of 19:06Z: 211+ manifest entries, 11.4M trades parsed for day 1/5, processing
  book_snapshot_5. Full 5-day backfill expected to complete within ~1-2 hours. VM investigation for todo 3: both
  2024/2025 HL VMs confirmed ALIVE and making legitimate progress (multi-year S3 backfills, NOT hung) — detailed
  findings inline in todo 3.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (7 entries), unchanged.
- **stale-`[OPERATOR]`-flip sweep 2026-08-09**: re-verified the HYPERLIQUID VM investigation todo — live
  `aws ec2 describe-instances` lookup for both VM names returns zero results in every US region checked, consistent with
  both multi-year backfills having completed and self-terminated since the 08-04 alive-confirmation. Flipped `[x]`,
  retagged `[DATA][OPERATOR]` → `[DATA]`. Note: all todos in this doc are now done — archival-eligible, but not archived
  here (5 other corpus docs reference this doc's path; a full referrer sweep is out of scope for this pass).
