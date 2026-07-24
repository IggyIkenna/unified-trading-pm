---
doc_type: issue
title:
  Sports odds manifest — consolidator's captured-outranks tie-break resurrects a proven-stale `captured` row on every
  cycle, blocking honest `reprocess_sports_odds.py --force` corrections
summary:
  For sports odds `venue=ODDS_API`/`data_type=odds_horizon_bucket` coarse rows on 2025-12-18/12-24/12-31, a direct
  `record_failed()` write via the real `reprocess_sports_odds.py --force` script lands successfully (log-confirmed, GCS
  generation-confirmed) but is reverted back to the stale `captured` (2026-07-14) row within ~1 minute by the live
  manifest consolidator (`instance 1-2721d221`, lock `_index/consolidator.lock`), which runs on a `*/1 * * * *` cron.
  Reproduced 3x independently across ~25 minutes. Neither per-VM shard (`_legacy_seed.parquet`,
  `sports-fixtures-job.parquet`) holds the stale row, so the resurrection source is not the documented
  `_legacy_guard`-exempted path — root cause not yet isolated.
status: open
sequential: true # real dependency chain: isolate source (DIAG -001) -> fix (CODE -002) -> re-verify (DATA -003)
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest-consolidator, captured-outranks, resurrection, sports, data-correctness, blocked]
related:
  [
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-24
parent_epic: sports_master
assigned_vm: planning
resolved_by:
source:
  [
    "sports_closeout_batch1_ao_ready_2026_07_24.md todo 3 (Run reprocess_sports_odds.py --force for
    2025-12-18/12-24/12-31)",
  ]
priority: P0
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
last_updated: 2026-07-24
---

# Sports odds manifest — consolidator resurrects stale `captured` row, blocking honest correction

## What I found

Task: run `market-data-processing-service/scripts/reprocess_sports_odds.py --force` for 2025-12-18, 2025-12-24,
2025-12-31 so the manifest's coarse row (`date`, `venue=ODDS_API`, `data_type=odds_horizon_bucket`,
`service_name=market-data-processing-service`, no `league_id`/`timeframe`) flips off the stale `captured` state (a
legacy-path capture leak, already proven contaminated by the plan's sibling P1 todo which deleted the underlying T-0
shards) to the honest verdict.

**Step 1 — dry-run confirms the honest verdict for all 3 dates is `attempted_failed`, not the plan's predicted split.**
All 3 dates read 26.7k-28.8k raw `ODDS_API` rows successfully, but
`SportsBucketAssignmentAdapter.process_to_bucketed_df` returns an empty frame for every one of them
(`ADAPTER_RETURNED_EMPTY_OUTPUT`) — i.e. raw bytes exist but are filtered to zero rows, which per the script's own
honest-absence design is `attempted_failed`, never `empty_confirmed` (that would require zero raw bytes). The plan text
predicted `empty_confirmed` for 12-24 specifically; the plan's OWN earlier P1 todo (already-completed, same plan)
already found "every other horizon returned `ADAPTER_RETURNED_EMPTY_OUTPUT` on those dates" for all 3 — so the plan's
predicted split was stale/wrong at authoring time. This part is not the bug; noting it because the done-when text needs
revision either way.

**Step 2 — the real `--force` run writes successfully (log + GCS generation confirm it), then reverts.** Ran
`reprocess_sports_odds.py --start-date <D> --end-date <D> --force` (no dry-run) for each date. Each run logged:

```
ManifestWriter: updated availability index (5526420 total entries, 1 new) in instruments-store-sports-prd-central-element-323112
```

— the generation-match CAS success log format (no retry/race-fallback suffix), confirming a clean single-attempt CAS
write. Checked the physical blob (`native_client.bucket(...).blob("_index/availability_index.parquet").reload()`)
immediately after each write: **generation and `updated` timestamp exactly match the write's completion time**, so the
write is not in doubt.

Immediate re-read after the 2025-12-18 rerun (within ~60s) DID show the correct row:

```
2025-12-18  attempted_failed  ADAPTER_RETURNED_EMPTY_OUTPUT  2026-07-24T20:25:31.804145+00:00
```

**Step 3 — within ~1-6 minutes, ALL THREE dates revert to the original stale `captured` row (2026-07-14 timestamps),
repeated across 3 independent verification passes over ~25 minutes** (20:26, 20:32, 20:44 UTC). At one point (20:27 UTC)
a DIFFERENT, non-committed error_reason string
(`legacy_captured_leak_corrected_per_sports_odds_manifest_captured_outranks_2026_07_24`, not found anywhere in the repo
via `grep -rn` — likely another agent's uncommitted ad-hoc corrector script, mirroring
`restamp_sports_odds_horizon_bucket_2026_07_22.py`'s pattern) transiently held for 12-24/12-31 — it ALSO reverted to
`captured` by the next check. So at least two independent correction attempts (mine via the sanctioned script, and one
other) both get reverted the same way.

**Step 4 — confirmed live manifest consolidator is the active writer, running on a tight cycle.**
`_index/consolidator.lock` content: `{"started_at": "2026-07-24T20:32:43.199353+00:00", "instance": "1-2721d221"}` — a
fresh lock acquired seconds after my prior write, consistent with `restamp_sports_odds_horizon_bucket_2026_07_22.py`'s
documented finding that `market-data-sports` shares the uniform `*/1 * * * *` Cloud Scheduler cron
(`uts-prod-manifest-consolidator-market-data-sports-cron`). The canonical index's generation kept advancing (new
`updated` timestamps every check) even when I made no write of my own in between, confirming an external process is
continuously rewriting it.

`unified_trading_library/manifest_consolidator.py`'s merge `ORDER BY` (lines ~2582-2588) makes
`capture_status = 'captured'` **always outrank any non-captured status, regardless of recency**, for the same dedup-key
group — a deliberate 2026-07-12 fix ("a later failed/empty/unattempted row must never silently erase an earlier real
capture"). A 2026-07-15 follow-up (`legacy_seed_captured_outranks_resurrection_risk_2026_07_15`) added a `_legacy_guard`
that demotes this outranking ONLY for rows sourced from the frozen `_index/per_vm/_legacy_seed.parquet` shard
specifically — not for a stale `captured` row surviving anywhere else.

**Step 5 — checked both live per-VM shards in the manifest bucket; neither holds the stale row**, so the `_legacy_guard`
exemption doesn't apply and isn't the mechanism at play here:

- `_index/per_vm/_legacy_seed.parquet` (18,771 bytes) — 0 rows for these 3 dates.
- `_index/per_vm/sports-fixtures-job.parquet` (24,600 bytes) — 92 rows, none matching these 3 dates/venue/data_type.

So the resurrection source is NOT one of the two currently-participating per-VM shards. Root cause of exactly where the
consolidator re-derives the `captured` claim from on every cycle (a stale backup file it might also scan, the
canonical's own pre-write snapshot read at merge time, or something else) is **not yet isolated** — this needs someone
with consolidator internals context to trace `manifest_consolidator.py`'s full cycle input set (I only verified the 2
per-VM shard paths + the 2 backup-naming patterns visible in the bucket listing).

## Why it matters

- **Blocks this exact task's done-when** ("a manifest read for those 3 dates shows the stated verdicts, not `captured`")
  — not achievable via the documented single mechanism (running the real script), because any writer's correction is
  silently reverted by the automated consolidator within about a minute, every time, regardless of how many times it's
  retried.
- **Cross-cutting**: `manifest_consolidator.py`'s captured-outranks tie-break is shared infrastructure used by every
  asset_group's manifest (`unified-trading-library`), not sports-specific. If the resurrection source turns out to be
  systemic (not sports-specific per-VM-shard content), any other asset_group correcting a stale legacy `captured` claim
  via `record_failed`/`record_empty` could hit the exact same silent-revert failure mode.
- **Silent**: the writer-side log ("updated availability index... 1 new") reports success with no indication the row
  will be reverted moments later — an agent (or operator) trusting the log alone would wrongly believe the correction
  landed.
- Two independent correction attempts (mine + at least one other, evidenced by the transient differently-worded
  `error_reason`) both failed the same way — this is not a one-off race, it reproduced 3x over ~25 minutes.

## Recommended decision

Mirroring the precedent already established by `restamp_sports_odds_horizon_bucket_2026_07_22.py` (same bucket, same
consolidator cron, explicitly documented "CONTENTION VERDICT: CONTENDED — do not `--apply` without a paused writer
window"): this class of correction (overriding a captured-outranks tie-break on a proven-stale legacy capture) likely
requires an **operator-authorized paused-consolidator-cron window** to hold durably, OR a code-level fix to
`manifest_consolidator.py` that lets a genuinely-verified correction (not just any non-captured write) survive the
tie-break — e.g. an explicit override/tombstone mechanism analogous to the existing `_legacy_guard`, gated on proof
rather than shard provenance.

- [ ] [DIAG] P0. Trace `manifest_consolidator.py`'s full per-cycle input set for the sports asset_group (every path it
      scans/reads, not just the 2 per-VM shards already ruled out here) to isolate exactly where the stale `captured`
      row for 2025-12-18/12-24/12-31 keeps being re-derived from on every cycle. (repo: unified-trading-library)
- [ ] [CODE] P1. Once the source is isolated, decide + implement either (a) purge/correct the actual stale source so the
      consolidator has nothing to resurrect from, or (b) extend the captured-outranks tie-break with a proof-gated
      override mechanism (mirroring `_legacy_guard`) so a verified `record_failed`/`record_empty` correction can survive
      a consolidation cycle without requiring a paused-cron window every time. (repo: unified-trading-library)
- [ ] [DATA] P0. Once the fix lands, re-run `reprocess_sports_odds.py --force` for 2025-12-18/12-24/12-31 and verify the
      manifest read is STABLE across at least 2 consolidator cycles (not just an immediate post-write check) before
      flipping `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 3. (repo: market-data-processing-service)
