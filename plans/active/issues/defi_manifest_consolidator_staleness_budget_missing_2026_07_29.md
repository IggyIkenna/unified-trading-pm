---
doc_type: issue
title:
  DeFi manifest reads fall back to the expensive per-VM-shard-merge path almost constantly — `AG_STALENESS_BUDGET_SEC`
  has no `defi` entry despite defi's own real merge cadence (~31-32min) being documented elsewhere in the SAME file
summary: >-
  While re-verifying whether `data_pipeline_check_mdps_features_2026_07_20.md`'s `DEFI:onchain` gate ("MTDS has never
  ingested vault_share_price/lst_rates/lending_indices/oracle_prices/perp_funding") was a genuine structural gap or a
  stale/false-negative claim (per
  `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`), a live re-check against
  `market-data-tick-defi-prd-central-element-323112` hit
  `unified_trading_library.manifest_writer._read_index._read_consolidated_if_fresh` logging "consolidated blob age
  537.3s > 120s threshold — falling back to per-VM shards", then never completed a single `(date, data_type)`
  `read_manifest_rows()` lookup within 90s. Root cause: `AG_STALENESS_BUDGET_SEC` (`unified_trading_library/
  manifest_writer/_staleness_budget.py`) only overrides `{"cefi": 86400, "sports": 1800}` — `defi` falls through to the
  generic 120s default. But the SAME file's `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"] = 4200` entry is commented as
  covering defi's real merge duration ("live defi merges actually run ~31-32min ... with ~40% margin") — i.e. the
  people who tuned the in-flight horizon for defi already knew its real cadence is ~30x the 120s staleness budget, but
  never added the matching `AG_STALENESS_BUDGET_SEC["defi"]` entry. This is the IDENTICAL bug class already found +
  fixed for sports (`sports_manifest_read_staleness_budget_missing_2026_07_15.md`, sports given a 1800s override for
  its ~11min cadence) — defi has the same missing-override shape, just never caught because defi merges are unusually
  long (~31-32min) rather than the ~11min that made sports' false trips frequent enough to notice quickly. Net effect:
  essentially EVERY reader of the defi tick manifest (dependency checkers, dashboards, audits) that doesn't happen to
  set `MANIFEST_CONSOLIDATED_STALENESS_SEC` itself falls into the expensive per-VM-shard-merge fallback almost every
  time, which for this bucket did not complete within 90s in direct testing — a severe read-path performance/
  reliability defect, and a highly plausible contributor to (though not independently proven as the sole cause of) the
  2026-07-27 `DEFI:onchain` dependency-check "no MTDS manifest ... has not run" false-negative this session was
  originally investigating.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, deployment-api]
scope: [engineer]
tags: [defi, manifest, consolidator, staleness-budget, performance, dependency-checker, per-vm-shard-fallback]
related:
  [
    /plans/active/issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md,
    /plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md,
    /plans/active/issues/manifest_consolidator_cadence_cost_audit_2026_07_20.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
drift_direction: advance-code
source:
  [
    "slot-11, data_engineering, 2026-07-29, discovered while re-verifying data_pipeline_check_mdps_features-054's
    DEFI:onchain gate",
  ]
resolved_by:
locked_by:
locked_since:
---

# DeFi manifest consolidator staleness budget missing — same bug class as the sports fix, unfixed for defi

## What I found

Investigating `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`'s open question (is
`DEFI:onchain`'s "MTDS has never ingested [5 data_types]" dependency-check failure a real structural gap or a
day-selection/freshness-lag false negative?), I tried a direct, lightweight re-check:
`DependencyChecker(project_id="central-element-323112").check_dependencies("2026-07-27", "DEFI")` (no VM launch — just
the manifest read the real dependency checker uses). It logged:

```
2026-07-29 03:59:44,698 INFO ManifestReader: consolidated blob age 537.3s > 120s threshold — falling back to per-VM shards
```

and did not return within 5 minutes (killed at that point, my own PID, per the VM-delete-guardrail spirit applied to my
own runaway process). A follow-up isolated single-lookup test
(`read_manifest_rows("market-data-tick-defi-prd-central-element-323112", "2026-06-14", "lst_rates")`, a day
`data_completion_defi_2026_07_15.md` shows as having a real captured `lst_rates` canary write) also did not complete
within a 90s hard timeout.

Root cause, confirmed by direct code read:

- `_read_consolidated_if_fresh()` (`unified_trading_library/manifest_writer/_read_index.py:807-868`) serves the fast
  consolidated index only when its blob age is under `_resolve_consolidated_staleness_sec(bucket)`. Past that budget it
  returns `None`, and the caller falls back to `_read_and_merge_per_vm_shards` — a per-VM-shard list+download+merge,
  materially slower than one consolidated-blob read.
- `AG_STALENESS_BUDGET_SEC` (`unified_trading_library/manifest_writer/_staleness_budget.py:31`) is
  `{"cefi": 86400, "sports": 1800}`. `defi` has no entry, so `staleness_budget_for_bucket()` returns `None` and the
  caller falls through to the generic Pydantic field default of **120 seconds**.
- The SAME file's `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"] = 4200` (line 49) carries this comment (lines 44-48):
  _"live defi merges actually run ~31-32min — defi (TTL 4200s) covers ~32min merges with ~40% margin"_. That is, the
  defi consolidator's OWN real merge duration (~1860-1920s) is already documented in this exact file — nearly 16-32x
  the 120s staleness budget every defi-bucket reader is held to.
- This is the identical bug class `issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md` found and fixed
  for sports (~11min real cadence routinely aging past the 120s default, false-tripping staleness); the fix there added
  `"sports": 1800` to the same dict. `defi`'s cadence is ~3x longer than sports' was, so the SAME failure mode should be
  even more pronounced for defi — it just wasn't caught yet because nobody had filed the equivalent doc.
- `deployment-api/deployment_api/routes/health_consolidator.py:102`'s `_AG_STALENESS_BUDGET_SEC` is a deliberately
  duplicated mirror of the UTL dict (not imported — deployment-api depends on UTL, not vice versa) and has the same gap.

## Why it matters

Every consumer of the DeFi tick manifest that does not happen to set `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`/similar
itself (dependency checkers, ad-hoc audits, dashboards, this session's own re-verification attempt) falls into the
expensive per-VM-shard-merge fallback on almost every read — not an occasional edge case, but the DEFAULT experience
for this bucket, given the consolidator's own real cadence structurally exceeds the 120s budget nearly every cycle. This
directly blocked this session's attempt to re-verify whether `DEFI:onchain`'s "never ingested" framing in
`data_pipeline_check_mdps_features_2026_07_20.md` (line ~906) is accurate, and is a plausible (not yet independently
proven) contributor to the original 2026-07-27 dependency-check failure itself. It also means any FUTURE quick
manifest-driven check against defi (not just this investigation) will hit the same wall.

## Recommended fix

Mirror the sports fix exactly: add a `defi` entry to `AG_STALENESS_BUDGET_SEC` (UTL) and `_AG_STALENESS_BUDGET_SEC`
(deployment-api), sized with real margin over the ~31-32min (~1860-1920s) documented real merge cadence — the sports
fix used roughly a 2.7x margin over its ~11min cadence (1800s budget); a comparable margin for defi lands around
3600-5000s. This doc does not mandate an exact number — whoever ships it should pick one with clear margin over the
documented ~32min cycle while staying well under a horizon that would mask a genuine multi-hour consolidator outage
(same philosophy as the existing `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"] = 4200` choice).

## Todos

- [x] [DATA] P1. ✅ Add `"defi"` to `AG_STALENESS_BUDGET_SEC` in
      `unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py` (mirroring the sports
      precedent) + the duplicated `_AG_STALENESS_BUDGET_SEC` in
      `deployment-api/deployment_api/routes/health_consolidator.py` + a unit test asserting the new value comfortably
      exceeds the documented ~32min real cadence. — DONE 2026-07-29 (slot-11): set both to 3600s (1h), fixed 3
      pre-existing tests that used a defi bucket as their "non-overridden asset_group" negative control (now genuinely
      non-overridden via tradfi instead) — shipped `unified-trading-library@13d3daef` (QG green, 6835 tests) +
      `deployment-api@9b3e35e` (QG green, 5046 tests).
- [ ] [DATA] P2. Once the fix above is live, re-attempt the `DEFI:onchain` dependency-check re-verify from
      `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md` (pick a benchmark day from
      `data_completion_defi`'s densely-captured window) now that manifest reads for this bucket should resolve quickly
      via the consolidated index instead of the per-VM-shard fallback — confirms or refutes the "never ingested"
      framing with an actually-completing check. Repo: features-service.

## Progress Log

- 2026-07-29 (slot-11, data_engineering): Filed while investigating `data_pipeline_check_mdps_features-054`'s
  CEFI/TRADFI/DEFI gating todo. Root-caused via direct code read (not guessed) + a live reproduction (killed my own
  hung PID after ~5min, then confirmed the same non-completion with a 90s hard-timeout single-lookup test on a
  known-good day). Shipping the fix same-session — see plan Progress Log for the SHA.
