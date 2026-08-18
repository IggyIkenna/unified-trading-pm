---
doc_type: issue
title:
  Odds backfill VM stuck on ManifestConsolidatorStaleError for 40+ minutes and growing — sports-manifest-rescan direct
  writes reset the reader's staleness clock with nothing to reconsolidate
summary: >-
  mtds-backfill-odds-20260817-062648 hit unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError
  at 01:53:46 UTC 2026-08-18 (age=3725s > MANIFEST_CONSOLIDATED_STALENESS_SEC=1800s for
  instruments-store-sports-prd-central-element-323112) and has NOT recovered — staleness age grew to 6285s by 02:36:25
  UTC (confirmed still growing, not a transient blip), with the VM cycling the SAME 5 dates (2020-12-18..2020-12-22) via
  shard-level failure isolation without any forward progress. Root cause: two sports-manifest-rescan-vm.sh runs
  (FIXTURES then WEATHER, same session) write DIRECTLY to the canonical index, bypassing per-VM shards entirely — the
  consolidator Cloud Run Job is confirmed healthy (gcloud run jobs executions list: 100% success, firing every 60s) but
  has nothing new to consolidate in the window after a direct write, so the file's own last-modified/staleness marker
  never advances even though the job itself is fine. The rescan launcher already got a --consolidator-staleness-sec
  override for this exact class of false positive; the odds launcher never did.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [deployment-service, unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [manifest, consolidator, staleness, sports, odds, backfill, infra]
related: [plans/archive/issues/manifest_consolidator_stale_sports_bucket_2026_07_21.md, plans/active/issues/sports_honest_coverage_gap_closure_2026_08_14.md]
created: "2026-08-18"
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [interactive-autonomous-session-2026-08-18]
resolved_by: []
locked_by:
depends_on: []
---

# What I found

While live-verifying a `merge_into_canonical()` OOM fix this session (`sports_honest_coverage_gap_closure_2026_08_14.md`),
I ran two `launch-sports-manifest-rescan-vm.sh` rescans back-to-back against
`instruments-store-sports-prd-central-element-323112` — a FIXTURES rescan (completed 00:51:39 UTC, wrote 63,100,561
rows directly to `_index/availability_index.parquet`) followed by a WEATHER rescan attempt.

At 01:53:46 UTC, the standing odds backfill VM `mtds-backfill-odds-20260817-062648` (unrelated, already running since
2026-08-16) hit:

```
unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError: Consolidated availability_index for
bucket='instruments-store-sports-prd-central-element-323112' is stale (age=3725s, staleness threshold
MANIFEST_CONSOLIDATED_STALENESS_SEC=1800s) while per-VM shards exist — the staleness budget may be too tight for this
bucket's real consolidator cadence (the consolidator Cloud Run Job may still be healthy). Refusing to fall back to the
per-VM shard merge (can OOM on large buckets).
```

Checked back at 02:36:25 UTC (43 minutes later, past the reader's own documented 2400s bounded-wait horizon): **the
staleness age had GROWN to 6285s, not shrunk** — confirming this is an ongoing stall, not a transient blip self-healing
within its documented wait window. The VM has been cycling the SAME five dates (2020-12-18 through 2020-12-22) the
entire time, each hitting the same error, caught by shard-level failure isolation (correct resilience behavior — no
crash, no data corruption), then retried on the next pass. Zero forward progress since 01:53:46 UTC.

**Confirmed the consolidator itself is healthy**, not down: `gcloud run jobs executions list --job=uts-prod-manifest-
consolidator-instruments-sports` showed 10 consecutive executions (01:32-01:41 UTC), every one `SUCCEEDED_COUNT=1`,
zero failures, firing on its `*/1` cron exactly as designed.

**Root cause**: `launch-sports-manifest-rescan-vm.sh`'s rescan script writes the canonical index DIRECTLY
(`ManifestMigrator.merge_into_canonical`), bypassing per-VM shards entirely — after my FIXTURES write at 00:51:39 UTC,
there was nothing NEW for the consolidator to merge (no odds-VM shards had accumulated a large-enough backlog, or the
consolidator's no-op cycles simply don't touch the file's metadata), so the canonical index's own "last consolidated"
marker never advanced past 00:51:39 despite the consolidator job running clean every 60 seconds. Confirmed directly:
`_index/availability_index.parquet`'s `last_modified` was still `2026-08-18T00:51:39.818000+00:00` when checked ~50
minutes later.

This is a **different flavor** of the false-positive class already fixed once this session for
`launch-sports-manifest-rescan-vm.sh` itself (added `--consolidator-staleness-sec`, default 1800 unchanged, override to
86400 for sequential-rescan sessions) — but the ODDS backfill launcher
(`launch-mtds-sports-odds-backfill-vm.sh`) reads the SAME bucket via `market-tick-data-service`'s manifest reader path
and has no equivalent override; it's still hardcoded to the fleet-wide 1800s default from the 2026-07-21 audit
(`manifest_consolidator_stale_sports_bucket_2026_07_21.md`), which was calibrated for the ORIGINAL scenario (consolidator
genuinely catching up on a real per-VM-shard backlog) — not this one (a direct-write migration tool leaving nothing new
to consolidate at all).

# Why it matters

- The odds backfill (`mtds-backfill-odds-20260817-062648`, running since 2026-08-16, currently around 2020-11/12) is
  making ZERO progress while stuck — every date in the 2020-12-18..22 window is being lost to this error on every
  retry pass, and per the 2026-07-21 precedent, an affected date needs a LATER re-fetch to ever get captured (shard
  isolation prevents a crash but does not recover the lost date on its own).
- Any OTHER long-running reader of `instruments-store-sports-prd-central-element-323112` (not just this one odds VM)
  is equally exposed the next time a direct-write rescan runs while it's active — this is a structural gap, not a
  one-off.
- My own currently-in-flight WEATHER rescan (`sports-manifest-rescan-20260818-033228`) will likely reset this specific
  staleness clock the moment it writes successfully (any write refreshes `last_modified`), which may self-resolve THIS
  particular stall as a side effect — but that's incidental, not a fix, and the next sequential-rescan session will
  hit the identical odds-VM (or similarly-launched reader) stall again without a code change.

# Recommended decision

Extend the same `--consolidator-staleness-sec`-style override already added to `launch-sports-manifest-rescan-vm.sh`
(`deployment-service@76991b62e9`) to `launch-mtds-sports-odds-backfill-vm.sh`, OR set
`MANIFEST_ALLOW_STALE_FALLBACK=true` for that launcher specifically (per the error's own remediation hint) if a
narrower per-run override isn't easily plumbed through the MTDS CLI. Do NOT raise the fleet-wide
`MANIFEST_CONSOLIDATED_STALENESS_SEC=1800` default shared by the other 13 sports launchers from the 2026-07-21 audit —
that calibration is still correct for their genuinely shard-dependent scenario; this is a distinct trigger (direct-write
migration tools running concurrently with other bucket readers) that needs its own opt-in, same reasoning as the
rescan-launcher fix.

Did NOT restart or kill `mtds-backfill-odds-20260817-062648` — it is a live, actively-owned standing backfill; per
workspace rule, a confirmed-stuck-but-not-crashed process gets diagnosed and flagged, not unilaterally restarted absent
an actual host-endangering condition.

## Todos

- [ ] [SCRIPT] P2. Add a `MANIFEST_CONSOLIDATED_STALENESS_SEC` (or equivalent) override mechanism to
      `launch-mtds-sports-odds-backfill-vm.sh` (or the shared MTDS launcher path it uses), mirroring the
      `--consolidator-staleness-sec` flag added to `launch-sports-manifest-rescan-vm.sh`
      (`deployment-service@76991b62e9`), so a future sequential-rescan session doesn't stall this launcher's readers
      the same way. Verify the odds VM (or its successor after any preemption) resumes forward date progress past
      2020-12-22 once either this fix lands or the stall self-resolves.
- [ ] [SCRIPT] P3. Consider whether `ManifestMigrator.merge_into_canonical()`'s direct-write completion should also
      touch a "last known good" marker/metadata field that OTHER readers' staleness checks could recognize as
      equivalent to a fresh consolidator cycle (rather than requiring every possible reader launcher to carry its own
      override) — a more structural fix than per-launcher overrides, but bigger scope; not attempted here.

## Codex SSOTs

`/codex/05-infrastructure/manifest-consolidator-ssot.md`, `/codex/04-architecture/shard-level-failure-isolation.md`.
