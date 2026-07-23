---
doc_type: issue
title:
  "sports availability_index read-path staleness budget is the 120s generic default (no per-AG override) while the
  sports consolidator cadence is ~11 min — every caller without a MANIFEST_CONSOLIDATED_STALENESS_SEC env override
  false-raises ManifestConsolidatorStaleError on a healthy consolidator"
summary:
  "data_engineering (slot-11, 2026-07-15, executing AO task sports_data_sources_canonical_completion-023) hit a
  ManifestConsolidatorStaleError reading instruments-store-sports-prd _index/availability_index.parquet. Root-caused:
  the sports consolidated blob refreshes on a ~11-min cadence (observed 17:00:41 -> 17:11:42; merges take ~7-8 min per
  AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC['sports']=2400) so it routinely ages past the 120s generic read-path staleness
  budget, but sports has NO entry in AG_STALENESS_BUDGET_SEC (only cefi=86400 does). The read path then either raises
  (default, shards present) or, with MANIFEST_ALLOW_STALE_FALLBACK=true, silently falls back to a per-VM-shard-only
  merge that OMITS the 5.3M-row consolidated corpus (the sports bucket has only 2 tiny per-VM shards). This is the exact
  false-stale class the cefi override already fixed. Any caller that does not set MANIFEST_CONSOLIDATED_STALENESS_SEC by
  hand (audit scripts, the /data-freshness skill, downstream reads, the deployment-api cockpit consolidator-health view)
  sees false outages on a perfectly healthy sports consolidator."
status: open
priority: P1
nature: notes
asset_group: [sports, meta]
stage: [meta]
repos: [unified-trading-library, deployment-api]
scope: [engineer, admin]
tags: [manifest, consolidator, staleness, sports, data-correctness, false-stale, read-path]
related: [../sports_data_sources_canonical_completion_2026_07_13.md]
created: 2026-07-15
parent_epic: infrastructure_master
source:
  "data_engineering worker (slot-11, planning VM), 2026-07-15, executing AO task
  sports_data_sources_canonical_completion-023 (CF11 backfill). Observed against
  instruments-store-sports-prd-central-element-323112: consolidated _index/availability_index.parquet refreshed 17:00:41
  -> 17:11:42 UTC (~11 min cadence, 119 MB / ~5.3M rows, healthy); 120s default staleness budget trips
  ManifestConsolidatorStaleError. Workaround used for the CF11 run: MANIFEST_CONSOLIDATED_STALENESS_SEC=3600 env
  (mirrors cefi launchers) so the healthy consolidated blob is served."
locked_by:
resolved_by:
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: NA
depends_on: []
---

## What I found

Reading the sports availability index (`read_availability_index("instruments-store-sports-prd-<project>")`) raises
`ManifestConsolidatorStaleError` on a **healthy** consolidator, because the read-path staleness budget for sports is the
generic 120s default while the sports consolidator's real cadence is ~11 min.

- **Read-path gate** (`unified_trading_library/manifest_writer/_read_index.py::_read_consolidated_if_fresh` via
  `_state.py::_resolve_consolidated_staleness_sec`): the consolidated blob is treated as stale once its GCS `updated`
  mtime is older than `MANIFEST_CONSOLIDATED_STALENESS_SEC`. When stale AND per-VM shards exist, `_read_slow_path`
  loud-fails (`ManifestConsolidatorStaleError`) by default.
- **Budget resolution** (`unified_trading_library/manifest_writer/_staleness_budget.py`):
  `AG_STALENESS_BUDGET_SEC = {"cefi": 86400}` — **sports has no override**, so it falls back to
  `UnifiedCloudConfig.manifest_consolidated_staleness_sec` (default **120s**).
- **Observed reality**: the sports consolidated blob refreshed `2026-07-15 17:00:41 -> 17:11:42 UTC` (~11 min apart, 119
  MB / ~5.3M rows). `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["sports"] = 2400` documents ~7-8 min merges. So the blob is
  healthy but its age swings to ~11 min between merges — ~5x the 120s budget.
- **The fallback is worse than the raise here**: `_read_and_merge_per_vm_shards` reads ONLY `_index/per_vm/*.parquet`,
  NOT the consolidated blob. The sports bucket has just 2 tiny per-VM shards (`_legacy_seed` 18 KB +
  `sports-fixtures-job` 34 KB). So `MANIFEST_ALLOW_STALE_FALLBACK=true` would return a few-hundred-row frame instead of
  the 5.3M-row corpus — a silent-undercount trap for any audit/backfill that flips that env to "get past" the raise.
- **Cockpit mirror** (`deployment-api/deployment_api/routes/health_consolidator.py::_AG_STALENESS_BUDGET_SEC`) is the
  same `{"cefi": 86400}` — so the deployment-api consolidator-health display shows sports as false-DOWN on the same
  cadence.

This is the identical class the cefi override already fixed (see the `_staleness_budget.py` module docstring: "a caller
without cefi's own env override (e.g. an audit script) previously saw false ManifestConsolidatorStaleError refusals on a
perfectly healthy consolidator").

## Why it matters

- **False data-outage signal on a healthy pipeline.** Any sports manifest reader that does not manually export
  `MANIFEST_CONSOLIDATED_STALENESS_SEC` — the `/data-freshness` skill, one-off audit/backfill scripts, downstream
  services, the deployment-api cockpit — intermittently sees the sports consolidator as stale/DOWN when it is fine.
- **Silent-undercount hazard.** The natural "unblock" (`MANIFEST_ALLOW_STALE_FALLBACK=true`) does NOT read the
  consolidated blob for this bucket, so it returns a near-empty frame — a data-correctness landmine (an audit could
  conclude "0 attempted_failed" / "0 coverage" and be badly wrong).
- **Per-script env workarounds are drift.** The CF11 backfill this session had to hardcode
  `MANIFEST_CONSOLIDATED_STALENESS_SEC=3600`; every future sports caller must remember to do the same. The SSOT fix is a
  per-AG override so no caller needs the env at all.

## Recommended decision

Add a `sports` entry to the per-AG staleness budget in BOTH mirrored SSOTs (they are intentionally duplicated, not
imported). A value comfortably above the observed ~11-min cadence with margin — proposed **1800s (30 min)** — mirrors
cefi's "generous enough to never false-trip a healthy consolidator" intent while staying well under a value that would
mask a genuine multi-hour outage (a truly-dead consolidator holds no fresh lock, so `assert_consolidator_healthy`'s
in-flight-horizon check still catches real death independently). Operator may prefer to match cefi's 86400 for
uniformity — either is defensible; 1800s is the tighter, still-safe choice.

- [ ] [DATA] P1. Add `"sports": 1800` to `AG_STALENESS_BUDGET_SEC` in
      `unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py` (repo:
      unified-trading-library). Update the module docstring to note sports' ~11-min cadence alongside the cefi note.
      Add/extend a unit test asserting `staleness_budget_for_bucket("instruments-store-sports-prd-x") == 1800`.
- [ ] [DATA] P1. Mirror the same `"sports": 1800` into `_AG_STALENESS_BUDGET_SEC` in
      `deployment-api/deployment_api/routes/health_consolidator.py` (repo: deployment-api) so the cockpit
      consolidator-health view stops false-flagging sports as DOWN. Keep the two dicts in sync (they are duplicated by
      design — deployment-api depends on UTL, not vice versa).
- [ ] [DATA] P2. Grep the fleet for scripts that hardcode `MANIFEST_CONSOLIDATED_STALENESS_SEC` for the sports bucket as
      a workaround (e.g. `instruments-service/scripts/backfill/api_football_cf11_guaranteed_type_closer_2026_07_15.py`)
      and drop the per-script env once the per-AG override lands (repo: instruments-service).

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE.** Nothing has changed — re-read both SSOTs the doc names and neither has a `sports`
entry.

Evidence (current code, re-read 2026-07-23):

- `unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py:23` —
  `AG_STALENESS_BUDGET_SEC: dict[str, int] = {"cefi": 86400}`. Still only `cefi`.
- `deployment-api/deployment_api/routes/health_consolidator.py:94` —
  `_AG_STALENESS_BUDGET_SEC: dict[str, int] = {"cefi": 86400}`. Still only `cefi`, still mirrored (not imported), still
  in sync with each other (both wrong in the same way).
- No commit in either repo's recent history touches these dicts for `sports`.

The finding stands exactly as written. Not touched by any of the K1/K2 casing work, the pre-floor registry fix, the
api_football wrong-source wipe, or the shard-enumeration/honest-coverage remediation — this is an orthogonal read-path
gate, unaffected by any of those. No conflicting doc found.
