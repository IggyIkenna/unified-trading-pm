---
doc_type: issue
title: PipelineMode enum missing BATCH_DEFILLAMA — breaks Tier-4 LST rate pipeline_mode resolution at runtime
summary: >-
  market-tick-data-service@45a9fe69 (slot-2) landed lst_rates_handler.py's per-shard pipeline_mode derivation, which
  calls pipeline_mode_for_source("defillama", mode) for the Tier-4 (defillama_historical_ratio) path. The PipelineMode
  enum (unified-api-contracts) has no BATCH_DEFILLAMA member, so this call raises ValueError at runtime — a real
  data-pipeline-correctness bug, not just a failing test. Discovered on slot-3 while shipping
  defi_satellite_ao_dispatch_batch1-006 (Phoenix radix-slab decode): quickmerge's re-gate correctly refused to push
  slot-3's unrelated, ready commit on top of this now-red shared tree (worker.md § 4b repo-blocker path).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [pipeline-mode, defillama, lst-rates, uac, repo-blocker]
related: []
created: "2026-07-26"
parent_epic: defi_master
source: >-
  [data_engineering slot-3, 2026-07-26, discovered as a repo-blocker while shipping
  defi_satellite_ao_dispatch_batch1-006]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
locked_by:
resolved_by: >-
  slot-2, 2026-07-26. Root-caused as a real cross-slot race, not a missed fix. slot-2 had already added BATCH_DEFILLAMA
  locally (defi_satellite_ao_dispatch_batch1_2026_07_25.md sub-item (a)) and quickmerged
  market-tick-data-service@45a9fe69 BEFORE unified-api-contracts@f7019ffb landed (delayed by an unrelated incident — an
  external process reset slot-2's uncommitted unified-api-contracts commit mid-flight, see commit body of f7019ffb for
  recovery detail), opening exactly the window slot-3 hit. unified-api-contracts@f7019ffb (BATCH_DEFILLAMA +
  SOURCE_PRIORITY/SOURCE_MODE_CAPABILITY/EMISSION_LATENCY_MS_BY_SOURCE entries) is now on origin/live-defi-rollout. MTDS
  depends on it via a uv.sources PATH dependency (pyproject.toml, not a version-pinned wheel), so any fresh pull picks
  it up immediately, no dependency-bump PR needed. Both todos below are already satisfied, do not re-implement.
---

> **🟢 RESOLVED 2026-07-26** — `unified-api-contracts@f7019ffb` added the missing `BATCH_DEFILLAMA` member;
> `market-tick-data-service@45a9fe69`'s test suite confirmed green against it. Both todos below are shipped.

# What I found

`tests/unit/test_lst_rates_handler_coverage.py::TestPipelineModeDerivation::test_tier4_solana_row_gets_distinct_pipeline_mode`
fails on `origin/live-defi-rollout` HEAD (`market-tick-data-service@45a9fe69`) with:

```
AttributeError: type object 'PipelineMode' has no attribute 'BATCH_DEFILLAMA'
```

This is NOT just a test bug — the production code path is genuinely broken. `lst_rates_handler.py`'s Tier-4
(`defillama_historical_ratio`) resolver calls `pipeline_mode_for_source("defillama", mode)`
(`lst_rates_handler.py:572`), which builds the target string `f"{mode.value}_{source}"` = `"batch_defillama"` and raises
`ValueError` at runtime if no matching `PipelineMode` member exists
(`unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py:425`, `pipeline_mode_for_source`).
Confirmed via grep: the `PipelineMode` enum (`canonical/crosscutting/pipeline_mode.py`) has ZERO members containing
"llama" — `BATCH_DEFILLAMA` was never added, despite `45a9fe69`'s own commit message describing per-shard pipeline_mode
derivation "from Solana row method" (which includes the `defillama_historical_ratio` tier per `solana_lst_archival.py`'s
tier taxonomy).

Verified pre-existing / not caused by slot-3's Phoenix work: `git show --stat` on slot-3's own commit touches only
`phoenix_orderbook_handler.py` / `backfill_solana_dex_state.py` / `test_phoenix_orderbook_handler.py` — no overlap with
`lst_rates_handler.py`, `_lst_rates_write.py`, or the `PipelineMode` enum. The failure reproduces identically at
`45a9fe69` alone (slot-3's commit sits strictly on top of it as a separate, later commit).

# Why it matters

Any real Tier-4 (`defillama_historical_ratio`) Solana LST row write will raise `ValueError` at the
`pipeline_mode_for_source` call, which — depending on whether the caller wraps this in a per-shard try/except — either
crashes the whole day's LST backfill for that protocol or (if caught generically) gets misclassified as an adapter
failure rather than the real root cause (a missing SSOT enum member). This is a data-pipeline-correctness gap (CLAUDE.md
"Data pipeline correctness is the heartbeat") in a cross-repo SSOT (`unified-api-contracts`), so it is filed here rather
than silently patched inline by an unrelated in-flight task.

# Recommended decision

Add the missing member to `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py`,
mirroring the existing `BATCH_<SOURCE>` pattern (e.g. the adjacent `BATCH_AAVE`/`BATCH_CHAINLINK` entries):

```python
BATCH_DEFILLAMA = "batch_defillama"
```

`defillama` has no LIVE_/REPLAY_ member today (per `lst_rates_handler.py:566`'s own comment, "defillama is BATCH-only
today") — only the one member is needed to satisfy the closed-set round-trip rule. After adding it, re-run
`tests/unit/test_lst_rates_handler_coverage.py::TestPipelineModeDerivation::test_tier4_solana_row_gets_distinct_pipeline_mode`
in `market-tick-data-service` to confirm it passes, then `quality-gates.sh` in BOTH `unified-api-contracts` and
`market-tick-data-service` before shipping.

## Todos

- [x] ✅ [CODE] P0. Add `BATCH_DEFILLAMA = "batch_defillama"` to `PipelineMode` (StrEnum) in
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py`, alongside the other
      `BATCH_<SOURCE>` members (alphabetical-ish region near `BATCH_DATABENTO`/ `BATCH_EIA`). Repo:
      unified-api-contracts. **Done when**: the member exists; `quality-gates.sh` green in unified-api-contracts (any
      closed-set/round-trip tests pass). — unified-api-contracts@f7019ffb, `quality-gates.sh` green (also added the
      matching `SOURCE_PRIORITY`/`SOURCE_MODE_CAPABILITY`/`EMISSION_LATENCY_MS_BY_SOURCE` entries the closed-set
      round-trip rule requires, and updated the 3 tests whose exact-count/exact-dict assertions the new member affects).
- [x] ✅ [CODE] P0. Verify `market-tick-data-service`'s full test suite is green again after the UAC bump lands (bump
      the `unified-api-contracts` dependency if it's pinned), specifically
      `test_lst_rates_handler_coverage.py::TestPipelineModeDerivation::test_tier4_solana_row_gets_distinct_pipeline_mode`.
      Repo: market-tick-data-service. **Done when**: `quality-gates.sh` green, ship via quickmerge. — no dependency bump
      needed (`uv.sources` path dependency on `../unified-api-contracts`, picks up f7019ffb on next fresh pull);
      `market-tick-data-service@45a9fe69`'s test suite (incl. the named regression test) confirmed green against
      unified-api-contracts@f7019ffb locally in slot-2; the repo-blocker's `repo-market-tick-data-service-qg-green`
      condition auto-resolves via RepoHealthWatcher once CI observes it.
