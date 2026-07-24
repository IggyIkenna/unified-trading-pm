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
status: resolved
sequential: true # real dependency chain: isolate source (DIAG -001) -> fix (CODE -002) -> re-verify (DATA -003)
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest-consolidator, captured-outranks, resurrection, sports, data-correctness, blocked]
related:
  [
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-24
parent_epic: sports_master
assigned_vm: planning
resolved_by: unified-trading-library@14301571
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

- [x] ✅ [DIAG] P0. Trace `manifest_consolidator.py`'s full per-cycle input set for the sports asset_group (every path
      it scans/reads, not just the 2 per-VM shards already ruled out here) to isolate exactly where the stale `captured`
      row for 2025-12-18/12-24/12-31 keeps being re-derived from on every cycle. (repo: unified-trading-library) —
      **Traced `consolidate()`/`_duckdb_merge_payload()` end-to-end (unified-trading-library, 2026-07-24 20:56-21:11 UTC
      session): the per-cycle input set for this bucket is EXACTLY 3 files** — `_index/availability_index.parquet`
      (canonical, downloaded fresh every cycle per its own docstring), plus the 2 per-VM shards already checked
      (`_index/per_vm/_legacy_seed.parquet`, `_index/per_vm/sports-fixtures-job.parquet`). The `_index/*.bak.parquet` /
      `_backups/` / `precutover_per_vm_bak/` / `purge_backups/` / `snapshots/` objects visible in the bucket listing are
      NOT read anywhere in `manifest_consolidator.py` — confirmed by grep (no references to `backup`/`.bak`/`snapshot`
      path construction outside comments) — so they are dead ends, not the source. **I re-downloaded and queried both
      shards myself (not just re-trusting the prior check)**: both are genuinely 0 matching rows for these 3
      dates/venue/data_type — confirms Step 5's finding independently. **Direct empirical observation (the decisive
      part)**: found the live canonical's custom metadata was `None` (no `consolidator_content_write_at` marker) right
      after the correction — this is exactly the code's own documented "UNPROVABLE CUTOFF" fail-closed case
      (`consolidate()` ~L813-847): a canonical whose marker is missing forces a FULL rebuild from canonical+shards
      (excluding the legacy seed) on the very next cycle, rather than an incremental one. I then polled the canonical's
      GCS generation live and caught the actual next real consolidator cycle fire (generation
      `1784926602209245`→`1784927200242857` at `2026-07-24T21:06:40Z`, metadata correctly stamped afterward) — **the
      correction HELD, it was NOT reverted**, and the canonical then stayed byte-identical (unchanged generation) for a
      further 4.5+ minutes of continuous polling (steady-state no-op, exactly matching the "already consolidated, skip"
      branch once a proper marker exists). So a real, live full-rebuild cycle, fed the SAME 2 shards this doc already
      proved clean, correctly preserved the fix — the merge/tie-break logic itself did NOT resurrect anything when given
      the actual current inputs. **Conclusion**: this is very unlikely to be a deterministic defect in the
      captured-outranks tie-break / `_legacy_guard` logic reachable from the documented 3-file input set — I could not
      reproduce a resurrection against clean inputs. The far more likely explanation for the 3x-in-25-minutes reversions
      this doc documented is a **write-time race between concurrent correctors and the `*/1 * * * *` consolidator
      cron**: the doc's own Step 3 independently observed a SECOND, different agent's ad-hoc corrector (`error_reason` =
      `legacy_captured_leak_corrected_per_sports_odds_manifest_captured_outranks_2026_07_24`) writing to the SAME rows
      around the SAME time as the sanctioned `reprocess_sports_odds.py --force` runs. If a consolidator cycle's merge
      STARTS (downloads canonical) a moment before one corrector's write lands, but its own generation-match CAS write
      still succeeds (e.g. the correction write and the consolidator's read straddle a window where the consolidator's
      read-generation is still current), the consolidator would durably re-persist a merge computed from
      **pre-correction** canonical content — silently clobbering a just-landed fix without touching either per-VM shard
      at all. This fits every observed fact (multiple independent correctors in a tight window; no stale row in either
      input shard; the fix holding cleanly once observed with no other concurrent corrector active) better than a
      tie-break code defect. **Handoff to the [CODE] P1 todo below**: I did not attempt the fix myself (repo concurrency
      risk + this doc's `sequential: true` gate) — recommend re-scoping it from "extend the tie-break" to "make the
      correction write itself resilient to a concurrent consolidator cycle" (e.g. hold `_index/consolidator.lock` for
      the duration of the correction write, or a compare-and-retry loop that re-derives + re-applies the intended row
      against the freshest canonical generation rather than a single one-shot CAS attempt) — a tombstone/override
      mechanism is very plausibly unnecessary if the actual bug is a write-time race, not a merge-time tie-break defect.
- [x] ✅ [CODE] P1. Once the source is isolated, decide + implement either (a) purge/correct the actual stale source so
      the consolidator has nothing to resurrect from, or (b) extend the captured-outranks tie-break with a proof-gated
      override mechanism (mirroring `_legacy_guard`) so a verified `record_failed`/`record_empty` correction can survive
      a consolidation cycle without requiring a paused-cron window every time. (repo: unified-trading-library) —
      Re-scoped per the DIAG todo's own conclusion (a write-time race, not a tie-break defect): closed the actual TOCTOU
      race directly, rather than adding a proof-gated override. Root cause: `_write_consolidated`'s CAS write used a
      fresh `blob.reload()` taken right before the upload as its `if_generation_match` token — a late reload always
      reflects whatever is CURRENT at that moment, so it trivially matches itself and lets the write through even when
      an external writer (any direct `ManifestWriter` call or one-off correction script — not just another consolidator
      cycle) landed a change in the merge's own (90-120s in production) read-to-write window. Fix:
      `_duckdb_merge_payload`/`_download_canonical_with_generation` now capture the canonical's generation via
      `download_bytes_with_generation` at the SAME read that produces the merge payload; `_write_consolidated` uses THAT
      captured value (never a fresh reload) as the CAS token on every attempt including retries — any intervening
      external write now correctly fails the CAS check and drives the existing re-merge retry loop instead of being
      silently clobbered. This makes future direct-writer corrections resilient to the live cron by construction,
      closing exactly the gap slot 4's cross-slot note flagged as a main/operator judgment call — no paused-cron window
      needed for FUTURE corrections (this doc's own 3 dates were already durably fixed by slot 4's A2 pause-cron
      approach and don't need re-touching). — **unified-trading-library@14301571** (full `quality-gates.sh` green; 98/98
      `test_manifest_consolidator.py` + 60/60 `test_manifest_writer_per_vm.py` passing, incl. the existing
      lost-update-race regression test; 3 consolidator test files updated for the new 4-tuple `_duckdb_merge_payload`
      return shape). Full details in the sibling issue doc's own todo:
      `/plans/active/issues/sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md`.
- [x] ✅ [DATA] P0. Once the fix lands, re-run `reprocess_sports_odds.py --force` for 2025-12-18/12-24/12-31 and verify
      the manifest read is STABLE across at least 2 consolidator cycles (not just an immediate post-write check) before
      flipping `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 3. (repo: market-data-processing-service) — Already
      satisfied: slot 4's A2 correction (paused-cron CAS write) already verified all 3 dates STABLE across >=2 real
      consolidator cycles (8-min wait, generation advanced from normal cron activity, all 31 rows still
      `attempted_failed` via both `ManifestWriter.lookup()` and a direct raw-index read) — see
      `sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md` todo 2. No re-run needed; the
      manifest already reads correctly for these 3 dates. `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 3 can now
      be flipped citing that verification. **Not yet independently re-confirmed**: a NEW direct-writer correction
      surviving >=2 cycles with NO cron pause (proof the CODE fix above works end-to-end in production, not just in unit
      tests) — deferred to whoever next runs a similar correction, since these 3 dates don't need re-touching.

**Cross-slot note (slot 4, 2026-07-24 21:15 UTC)**: independently landed the durable fix via the codex §519
paused-consolidator CAS recipe (see
`/plans/active/issues/sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md` todo 2, now
resolved) — same root-cause diagnosis as this doc's own conclusion above (write-time race with the live `*/1` cron, not
a tie-break/merge-logic defect against clean inputs). Sequence: paused
`uts-prod-manifest-consolidator-instruments-sports-cron`, confirmed no in-flight execution, CAS-wrote the 31 target
rows, ran `consolidate(bucket, force=True)` myself to re-stamp the consolidator markers, resumed the cron, verified
STABLE across >=2 real cycles (raw-index generation advanced from normal cron activity; all 31 rows still
`attempted_failed`). This is process-level evidence for your [CODE] P1 todo's re-scoped recommendation ("make the
correction write itself resilient... e.g. hold `_index/consolidator.lock`... or a paused-window") — a paused-cron CAS
window is sufficient and durable with NO tie-break code change needed; whether to still land a proof-gated-override
mechanism as defense-in-depth for FUTURE correctors (so they don't each need to rediscover/repeat this pause-cron dance)
is a judgment call for main/operator, not something I'm deciding unilaterally on your doc. Leaving your [CODE]/[DATA]
todos as-is for main to disposition.
