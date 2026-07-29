---
doc_type: issue
title:
  "market-tick-data-service test_databento_enrichment_combo_underlying.py asserts the OLD human-name COMBO underlying
  convention — 3 tests fail against uac@b9f4b6b9's now-intentional raw-root behavior"
summary: >-
  Discovered while working tradfi_canonical_path_migration_design_2026_07_19.md's "strip Massive + fix casing" todo
  (which turned out to already be shipped elsewhere — uac@a2beed46+mtds@362a487e for Massive routing,
  utl@688e49bc+mtds@4122df13 for casing). Running market-tick-data-service's quality-gates.sh surfaced 3 PRE-EXISTING
  failures in tests/unit/test_databento_enrichment_combo_underlying.py, confirmed unrelated to any change this session
  (reproduces identically on a clean tree). Root cause: unified-api-contracts@b9f4b6b9 ("fix(tradfi): keep COMBO
  underlying as the raw short root, not human-readable name") deliberately reverted `_shared_underlying`'s prior
  human-name normalization (e.g. CL→WTI, ZN→UST-10Y) to fix a DIFFERENT bug
  (tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md — the catalog/seed side uses
  short root codes, not spelled-out names). That fix's own commit never updated this MTDS test file, which still asserts
  the OLD (now-wrong) human-name expectations.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, combo, underlying, test-drift, cross-repo, databento]
related:
  [
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
    /plans/archive/issues/tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md,
  ]
created: "2026-07-28"
parent_epic: tradfi_master
source:
  "backend/data_engineering worker, slot 8, 2026-07-28, working tradfi_canonical_path_migration_design-001 (task
  cancelled mid-flight before shipping)"
execution_scope: orchestrator-agent
assigned_vm: planning
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
  "market-tick-data-service@4fdbcb0d (+ d24437e4) — already shipped by another session; re-verified 2026-07-29 batch
  closeout pass, all 4 tests in test_databento_enrichment_combo_underlying.py green"
---

> **✅ ARCHIVED 2026-07-29** (batch closeout pass, market-tick-data-service docs batch). The exact fix this doc
> recommended (raw short-root assertions `"CL-BZ"`/`"ZN"` + docstring update) was already shipped by another session as
> `market-tick-data-service@4fdbcb0d` ("fix(tests): update combo-underlying test assertions to match UAC short-root
> convention"), landed before this doc was picked up. Re-verified live:
> `.venv/bin/python -m pytest tests/unit/test_databento_enrichment_combo_underlying.py -q` → `4 passed`. No code change
> needed this session.

# MTDS combo-underlying tests stale vs. UAC's now-intentional raw-root behavior

## What I found

Running `market-tick-data-service`'s `quality-gates.sh` (unrelated task), 3 tests in
`tests/unit/test_databento_enrichment_combo_underlying.py` fail:

- `test_named_spread_combo_kept_with_resolved_underlying` — asserts `underlying == "WTI-BZ"` for raw_symbol `CLH0-BZH0`;
  ACTUAL value is `"CL-BZ"` (raw short roots, not human names).
- `test_root_qualified_ud_combo_recovers_real_root` — asserts `underlying == "UST-10Y"` for raw_symbol
  `UD:ZN: TL 0219823765`; ACTUAL value is `"ZN"` (the raw UD-qualified root).
- `test_mixed_batch_drops_only_opaque_combo` — asserts `set(out["underlying"]) == {"WTI-BZ", "UST-10Y"}`; ACTUAL is
  `{"CL-BZ", "ZN"}`.

Confirmed PRE-EXISTING and unrelated to this session's work: reproduces identically with every other diff stashed, on a
clean `live-defi-rollout` tree.

**Root cause**: `unified-api-contracts@b9f4b6b9` ("fix(tradfi): keep COMBO underlying as the raw short root, not
human-readable name") deliberately removed `_shared_underlying`'s prior `UNDERLYING_NORMALIZATION` step (`ES`→`SP500`
style), per its own docstring:

> Previously this normalised a single shared root via `UNDERLYING_NORMALIZATION` (`ES`→`SP500`) for "human-readability"
> — that diverged from the catalog's own short-root convention for COMBO captures and broke the G1-ENUM present-set seed
> match (SSOT: `tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md`).

That fix is correct for its own purpose (aligning COMBO `underlying` with the catalog/seed's short-root vocabulary), but
its commit never touched `market-tick-data-service`'s test suite, which still encodes the pre-fix contract via hardcoded
human-name assertions (`"WTI-BZ"`, `"UST-10Y"`) and the module docstring's own examples.

## Why it matters

- These 3 tests currently FAIL on `live-defi-rollout` HEAD, which blocks a fully-clean `quality-gates.sh --no-fix` run
  for `market-tick-data-service` for anyone hitting this file (not a flake — deterministic).
- The underlying PRODUCTION behavior is correct (per the UAC fix's own stated rationale); only the MTDS test assertions
  are stale. This is test-suite drift from a cross-repo behavior change, not a live bug.

## Recommended decision

Update the 3 failing assertions (+ the module docstring's 2 examples) in
`market-tick-data-service/tests/unit/test_databento_enrichment_combo_underlying.py` to expect the raw short-root form
(`"CL-BZ"`, `"ZN"`) instead of the human-name form (`"WTI-BZ"`, `"UST-10Y"`), matching uac@b9f4b6b9's now-canonical
contract. This is a test-only, mechanical, low-risk fix — no production code change. (I drafted and verified this exact
fix locally this session — all 4 tests pass — but reverted it uncommitted when my task was cancelled mid-flight before I
could ship it; the diff is not preserved anywhere else, so redo it fresh rather than looking for a stash.)

## Todos

- [x] ✅ [DATA] P2. **DONE — already shipped, verified 2026-07-29.** `market-tick-data-service@4fdbcb0d` (+ `d24437e4`)
      updated `test_named_spread_combo_kept_with_resolved_underlying`/`test_root_qualified_ud_combo_recovers_real_root`/
      `test_mixed_batch_drops_only_opaque_combo` to the raw short-root form (`"CL-BZ"`/`"ZN"`) + the module docstring,
      exactly as recommended. Re-ran: `4 passed in 0.33s`. (repo: market-tick-data-service)
