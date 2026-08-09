---
doc_type: issue
title: dex_pools fold script — colon-embedded legacy symbols crash the shard (masked by a missing setup_events() call)
summary: >-
  A dry-run launch of fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py --only dex_pools (the final legacy
  data_type migration, singleton-locked behind dex_swaps which finished 2026-08-08 ~19:02 UTC) surfaced 15/30 worklist
  shards failing with a real ValueError: build_instrument_id rejects a symbol carrying an embedded ':' (the canonical
  id's own VENUE:TYPE:SYMBOL delimiter). Root-caused via a bounded, column-projected scan of all 14,094 raw
  ORCA/SOLANA/2022-11-09 legacy objects: only 2 distinct malformed symbol values exist ("SOL-11:11", "SOL-3:16"),
  affecting 3 files total (2 individual pools + 1 migration-artifact file combining both) -- not a systemic data-quality
  problem. A SECOND, independent bug compounded this: _safe_build_instrument_id's own error-handling path calls
  log_event(...), but the fold script never called setup_events() first, so the intended graceful degradation (log +
  skip the one bad instrument) itself crashed with RuntimeError("Event logging not initialized"), turning a 1-row
  problem into a whole-shard failure. Fixed both: generalised the fold script's existing MORPHO-specific ':' -> '-'
  symbol sanitisation (already shipped/reviewed) to apply to EVERY shard's resolved symbol column, and added an
  unconditional setup_events() call in main() (unconditional, not gated behind --apply like the sibling
  relabel_solana_dex_pools_fake_history.py precedent, since the crash hit during a dry-run). Regression test added
  exercising both fixes.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, dex_pools, canonical-naming, fold-script, colon-symbol, setup_events, migration]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-09"
author: interactive session (/autonomous)
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: interactive session (/autonomous), 2026-08-09
source: ["defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md, dex_pools dry-run launch, 2026-08-09"]
drift_direction: advance-code
context_scope:
  [
    market-tick-data-service/scripts/fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
  ]
---

## Finding

`MACHINE_TYPE=e2-standard-8 bash scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh --only dex_pools --dry-run`
(VM `backfill-defi-legacy-datatype-fold-20260809-072931`) — a deliberate dry-run before the real `--apply` launch, since
this is the LAST of the three legacy data_type folds and the singleton lock only allows one launch at a time. Worklist:
30 shards. Result:
`done (apply=False). totals={'written': 1383, 'skipped_existing': 0, 'missing_source': 0, 'manifest_registered': 0, 'shards_ok': 15}`
— exit_code=0, but only **15 of 30 shards succeeded**; the other 15 were silently dropped via the script's own per-shard
exception isolation (`logger.exception("shard failed: %s", shard); continue`), which lets the process exit 0 while
quietly losing half its work.

**Root cause 1 (real data defect)**: all 15 failures were `venue=ORCA, chain=SOLANA, data_type=dex_pools`, one per day
in November 2022. Traceback:

```
ValueError: build_instrument_id: symbol 'SOL-11:11' for instrument_type=POOL carries an embedded ':' -- the
canonical id's own VENUE:TYPE:SYMBOL delimiter. ... resolve the symbol against the catalogue/wire-map before
calling this builder, or route a genuinely-unresolvable instrument through the UAC quarantine model instead of
building a malformed double-wrapped id.
```

A bounded, column-projected, 32-way-parallel scan of ALL 14,094 raw legacy objects under
`raw_tick_data/by_date/day=2022-11-09/.../venue=ORCA/chain=SOLANA/instrument_type=pool/data_type=dex_pools/` (reading
only the `symbol` column per file, not full rows) found exactly **2 distinct malformed values** (`"SOL-11:11"`,
`"SOL-3:16"`) across **3 files** — 2 individual per-pool objects plus one
`_migrated_orca_SOLANA_20260504_234356.parquet` artifact file carrying both (itself evidence this is old,
already-known-odd legacy content from a prior migration pass, not fresh/growing corruption). Not investigated further
(out of scope): whether `"SOL-11:11"`/`"SOL-3:16"` are genuine (mis-formed) LP-pair names or a wire-parse artifact from
the original ORCA capture — the fix treats them as opaque strings and sanitises the delimiter collision, per the error
message's own guidance, rather than guessing at their semantic meaning.

**Root cause 2 (masking bug, independent)**: `_safe_build_instrument_id` (`canonical_write.py`) catches the `ValueError`
above and is SUPPOSED to degrade gracefully — log a `BUILD_INSTRUMENT_ID_FAILED` event and return `None` so the caller
skips just that one instrument. Its own `log_event(...)` call instead raised a SECOND exception:

```
RuntimeError: Event logging not initialized. Call setup_events() first.
```

`fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py` never calls `setup_events()` — so the "safe" wrapper's own
error path crashed, turning what should have been a 1-row skip into a whole-shard failure (all 30 files for that day
dropped, not just the 1-2 malformed rows within them). This is why 15/30 shards failed, not a smaller number — every
ORCA/SOLANA day in the worklist that happened to contain either bad symbol lost its ENTIRE shard, not just the offending
row.

## Fix (shipped this session)

`market-tick-data-service/scripts/fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py`:

1. Generalised the existing MORPHO-specific `':' -> '-'` symbol sanitisation (already shipped, reviewed, and in
   production for the `rate_indices` fold) to apply to **every** shard's resolved symbol column right before
   `records = legacy_df.to_dict("records")`, not just the MORPHO `instrument_key`-derived branch. Idempotent on
   already-clean symbols (checked via `.str.contains(":")` before touching anything).
2. Added an unconditional `setup_events(service_name="market-tick-data-service", mode="batch", sink=GcsEventSink(...))`
   call in `main()`, before `run(...)`. Unconditional (not gated behind `args.apply` like the sibling
   `relabel_solana_dex_pools_fake_history.py` precedent) because the crash was observed on a **dry-run**, not just
   `--apply` — any code path that can reach `log_event()` needs this regardless of mode.

Regression test:
`tests/unit/scripts/test_fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py:: test_fold_shard_sanitises_colon_embedded_symbol`
— a synthetic single-row ORCA/SOLANA shard with `symbol="SOL-11:11"`, asserting the shard succeeds (`written == 1`,
`missing_source == 0`) and the written object's symbol is sanitised to `"SOL-11-11"` with no embedded `:` (verified both
in the canonical filename's symbol segment and the written parquet's own `symbol` column).

## Impact / what's still open

- **Both fixes are scoped to this one-off migration script** — `canonical_write.py`'s shared
  `write_defi_rows`/`_safe_build_instrument_id` (used by every LIVE DeFi capture writer, not just this migration) were
  deliberately NOT touched, to keep blast radius contained to the historical-fold task. If colon-embedded symbols can
  also reach a LIVE capture path (not established here — this investigation only confirmed the 2 known bad values are
  historical, static, and file-count-bounded), that would need its own separate finding scoped to the live writer — not
  raised here, not observed anywhere else this session.
- **Nothing else open** — the fix was re-validated against the real worklist (dry-run: 30/30 shards, was 15/30 before
  the fix) and the real `--apply` run completed cleanly (30/30 shards, `written=148,758` + `skipped_existing=585` =
  149,343 total instruments, matching the dry-run's prediction exactly, `missing_source=0`, `exit_code=0`). `dex_pools`
  was the last of the three legacy data_type folds (`rate_indices`/`dex_swaps`/`dex_pools`) — all three are now
  genuinely complete. The manifest consolidator cron resume + fresh honest-coverage rollup (this epic's stated end
  state) remain gated on the still-running `canonical-migration-defi-rebuild-20260806-223130` VM reaching its own
  terminal state — tracked in the parent tracker doc, not this issue.

## Todos

- [x] [CODE] P1. Generalise colon-symbol sanitisation to all shards + add unconditional `setup_events()` —
      `market-tick-data-service@07e03736b`, QG-green, regression test passing.
- [x] [SCRIPT] P1. Re-run a dry-run `--only dex_pools` launch and confirm `shards_ok == 30` (full worklist, no failures)
      before the real `--apply` launch — confirmed 30/30, `written=149,343`, `exit_code=0`, VM
      `backfill-defi-legacy-datatype-fold-20260809-082914`.
- [x] [SCRIPT] P1. Launch the real `--apply --only dex_pools` VM once the dry-run above confirms clean, then verify
      genuine completion — confirmed 30/30, `written=148,758` + `skipped_existing=585`, `missing_source=0`,
      `exit_code=0`, `DEPLOYMENT_COMPLETED`, VM `backfill-defi-legacy-datatype-fold-20260809-090149` (self-deleted,
      404-confirmed).

## Progress Log

- **2026-08-09 (interactive session, `/autonomous`)**: dry-run launch surfaced both bugs; root-caused via a bounded
  (single-day/single-venue prefix, column-projected, 32-way-parallel) GCS scan rather than guessing or doing a broader
  corpus walk. Both fixes applied + QG-verified + regression-tested, shipped `market-tick-data-service@07e03736b`.
  Re-validated: fresh dry-run confirmed 30/30 shards clean (was 15/30). Real `--apply` launched immediately after and
  completed cleanly: 30/30 shards, `written=148,758`/`skipped_existing=585` (149,343 total, exactly matching the
  dry-run's prediction), `missing_source=0`, `exit_code=0`. `dex_pools` was the last of the three legacy data_type folds
  — `rate_indices`/`dex_swaps`/`dex_pools` are ALL now genuinely complete. Closing this issue; the remaining epic-level
  end state (consolidator cron resume + fresh rollup, gated on the still-running rebuild VM) is tracked in the parent
  tracker doc.
