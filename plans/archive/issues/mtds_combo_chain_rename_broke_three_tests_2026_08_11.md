---
doc_type: issue
title: >-
  market-tick-data-service: combo→combo_chain rename (c31cfe7a) broke 3 tests — still blocking live-defi-rollout / PR
  #950 even after the file-size-cap fix
summary: >-
  While splitting `partitioned_writer.py` / `migrate_tradfi_canonical_2026_07.py` under the 900-line file-size cap
  (follow-up of `ci_reconcile_overnight_batch_2026_08_11.md` item 10), found the repo's `quality-gates.sh` full test
  suite is ALSO red for an unrelated reason: 3 tests (`test_cefi_combo_stays_bare_underlying_ticks_parquet`,
  `test_tradfi_combo_stays_bare_underlying_ticks_parquet`, `test_cme_combo_shard_itype_stays_lowercase_id_stays_empty`)
  assert that the legacy bare `instrument_type="combo"` still gets per-underlying `.../underlying={U}/ticks.parquet`
  partitioning and an empty shard-key third element — behavior that commit `c31cfe7a` ("rename combo wrapper to
  combo_chain across writer + manifest", 2026-08-11T02:03:40Z, 2 commits before HEAD `486f82ba`) removed by narrowing
  `_UNDERLYING_PARTITIONED_TYPES` / the chain-branch checks to `"combo_chain"` only, dropping bare `"combo"`. Confirmed
  via `git stash` that these 3 failures are present on the CLEAN unmodified tree (i.e. NOT introduced by this session's
  file-size-cap split) and confirmed via `gh run view` that GH Actions `quality-gates-v2` on `live-defi-rollout` has
  been failing on exactly these 3 tests since the 06:19:38Z / 06:20:13Z run — meaning `live-defi-rollout` and PR #950
  will stay red even after the file-size-cap fix lands, until this is also resolved. Whether the correct fix is "combo"
  should still get old per-underlying-partition behavior (production bug in `c31cfe7a`) or the 3 tests are simply stale
  and should assert `combo_chain` instead (test bug) is a judgment call the rename's author should make — not guessed
  under time pressure alongside an unrelated file-size-cap fix.
status: resolved
nature: issue
scope: [engineer]
asset_group: [tradfi]
stage: [meta]
repos: [market-tick-data-service]
tags: [ci-reconcile, tradfi, combo-chain, regression, quality-gates]
related:
  [
    /plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-11
parent_epic: infrastructure_master
priority: P1
source:
  discovered while shipping the file-size-cap split follow-up to ci_reconcile_overnight_batch_2026_08_11.md item 10
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# market-tick-data-service: combo→combo_chain rename broke 3 tests

> **ARCHIVED** — 2026-08-11. Both follow-ups resolved in `market-tick-data-service@b13e3a2b`, confirmed GREEN on
> `quality-gates-v2`. See the Resolution section below for the fix (tests updated to `combo_chain` per the documented
> operator ruling in `tradfi_canonical_path_migration_design_2026_07_19.md`) and the parent
> `ci_reconcile_overnight_batch_2026_08_11.md` item 10 for the file-size-cap split that landed in the same commit.

## Evidence

- Commit `c31cfe7a` (`feat(tradfi): rename combo wrapper to combo_chain across writer + manifest`, 2026-08-11T02:03:40Z)
  narrowed the chain-branch instrument_type checks (`_UNDERLYING_PARTITIONED_TYPES` in `symbol_rules.py`, the `is_chain`
  check in `partitioned_writer.py._write_group`, and the CME combo shard-key derivation in `venue_fetch.py`) to
  `"combo_chain"` only — bare `"combo"` no longer gets per-underlying partitioning.
- 3 tests still assert the OLD bare-`"combo"` behavior and now fail:
  - `tests/unit/test_partitioned_writer_cefi_chain_tail_v6.py::test_cefi_combo_stays_bare_underlying_ticks_parquet`
  - `tests/unit/test_partitioned_writer_tradfi_filename_canonical.py::test_tradfi_combo_stays_bare_underlying_ticks_parquet`
  - `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py::TestTradfiRecordVenueShardCountsCanonicalization::test_cme_combo_shard_itype_stays_lowercase_id_stays_empty`
- Verified via `git stash` (reverting this session's file-size-cap split entirely) that all 3 fail identically on the
  clean tree — NOT caused by the file-size-cap split.
- Verified via `gh run view 31464664365 --repo IggyIkenna/market-tick-data-service --log-failed` that GH Actions
  `quality-gates-v2` on `live-defi-rollout` is failing on exactly these 3 tests (in addition to the file-size-cap gate)
  as of the 06:19:38Z / 06:20:13Z run.

## Impact

`live-defi-rollout` and promote PR #950 will remain red on `quality-gates-v2` even after the file-size-cap fix (this
session's split of `partitioned_writer.py` / `migrate_tradfi_canonical_2026_07.py`, tracked in
`ci_reconcile_overnight_batch_2026_08_11.md` item 10) lands — a second, independent blocker.

## Second, independent blocker found while attempting to ship (same PR, different root cause)

`quickmerge.sh`'s own pre-commit re-gate (`bash scripts/quality-gates.sh --no-fix` against the current tree) confirmed
the 3 combo/combo_chain test failures above are a REAL, current block ("Re-gate FAILED against the current tree — this
is a REAL failure, not a lost race") — the file-size-cap split commit could not land. Separately, a standalone
`QG_SLICE=lint-codex` run on the same tree surfaced a THIRD, also-unrelated hard-gate failure that will block PR #951
(the fleet bot's current promote PR, superseding the closed #950) even once the combo regression above is fixed:

**STEP 5.101 (empty-string-fallback ratchet)**:
`market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py` (introduced by the current HEAD
commit `486f82ba`, "feat(tradfi): add focused underlying display-name migration script") has 5 new `.get("key", "")`
fallback sites (lines 129, 130, 140, 141, 142) pushing the repo's empty-string-fallback count to 71 against a baseline
of 66 (`unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml`, which the gate explicitly
forbids raising). Needs the same author/owner judgment call as the combo issue: rewrite each site to fail fast (raise or
return `None`) or annotate with `# noqa: qg-empty-fallback` + a one-line justification if the fallback is genuinely a
meaningful absent-value case.

PR #951's `statusCheckRollup` at time of writing: `QG slice (tests)` FAILURE (combo regression), `QG slice (checks)`
FAILURE (file-size cap this session is fixing, likely ALSO the empty-string-fallback ratchet once the size-cap clears it
far enough to reach STEP 5.101), `quality-gates-v2` FAILURE overall.

## Resolution (2026-08-11, `/ci-reconcile` sweep)

Both follow-ups below resolved in the same shipped commit: **`market-tick-data-service@b13e3a2b`** ("fix(tradfi):
combo_chain reader routing + split 2 files past the 900-line SRP cap"), confirmed GREEN on `quality-gates-v2`
(`gh run list --branch live-defi-rollout --repo IggyIkenna/market-tick-data-service`).

- Combo/combo_chain regression: resolved as **option (b)** — the 3 tests were stale. `c31cfe7a`'s narrowing to
  `"combo_chain"`-only was the INTENDED, documented behavior: confirmed via
  `/plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md` § "2026-08-11 update", which records the
  explicit operator ruling that the Deribit/CME bundle-wrapper sense of "combo" collided with the real
  `InstrumentType.COMBO` enum member and was renamed `combo_chain` to get the full v6 `quote=`/`margin=` chain tail
  (matching `futures_chain`/`options_chain`). The 3 tests were updated to use `"combo_chain"` and the v6-tail-aware
  assertions (verified against the actual writer output, not guessed) — not a production-code revert.
- STEP 5.101 empty-string-fallback ratchet: cleared in the same commit (the shipped tree's fallback count is now BELOW
  the baseline, not above it — confirmed via a clean local `quality-gates.sh --no-fix` run and the green CI result
  above).

## Follow-ups (original, superseded by the Resolution above — kept for the record)

- [x] [CODE] P1. Fix `migrate_tradfi_underlying_display_names_2026_08.py`'s 5 new empty-string-fallback sites (lines
      129/130/140/141/142) — rewrite to fail fast or add `# noqa: qg-empty-fallback` with a one-line reason. Re-run
      `QG_SLICE=lint-codex bash scripts/quality-gates.sh --no-fix` to confirm STEP 5.101 clears. (repo:
      market-tick-data-service) — market-tick-data-service@b13e3a2b
- [x] [CODE] P1. Decide + fix: either (a) restore bare `"combo"` to the per-underlying-partition /
      empty-shard-key-third-element behavior in `symbol_rules.py` / `venue_fetch.py` / `partitioned_writer.py` if
      `c31cfe7a`'s narrowing to `"combo_chain"`-only was unintentional for the writer-partitioning path, or (b) update
      the 3 named tests to assert `"combo_chain"` behavior instead of legacy `"combo"` if the narrowing was intentional
      (`c31cfe7a`'s own commit message says "rename", implying `"combo"` should no longer appear as a live
      instrument_type at all — check for any remaining live producer of bare `"combo"` before choosing). Verify via
      `bash scripts/quality-gates.sh --no-fix` full-green, then ship + verify
      `gh run list --branch live-defi-rollout --repo IggyIkenna/market-tick-data-service` goes green and PR #950
      auto-merges. (repo: market-tick-data-service) — market-tick-data-service@b13e3a2b, PR #950 superseded/#951+
      cleared
