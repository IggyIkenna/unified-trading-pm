---
doc_type: issue
title:
  migrate_onchain_perp_perpetual_canonical_2026_07_08.py mis-handles an already-decomposed BASE-QUOTE@MARKER bare shape
  -- produces a corrupted double-suffixed rename target (fix written + tested, not yet shipped)
summary: >-
  Live dry-run (2026-07-27, twice, reproducible) of market-tick-data-service's HL/ASTER PERP->PERPETUAL rename script
  found a real bug: ~1,496 ASTER objects on gs://market-data-tick-cefi-prd/raw_tick_data/by_date/ are named
  {BASE}-{QUOTE}@LIN.parquet (already dash-split + margin-marked, just missing the VENUE:PERPETUAL: prefix) -- a THIRD
  bare shape the script's legacy_bare_symbol_canonical_id() doesn't recognize. It falls through to canonical_symbol()'s
  bare-undelimited-symbol branch, which re-appends -{quote}@LIN, producing ASTER:PERPETUAL:0G-USDT@LIN@LIN.parquet -- a
  corrupted double-suffixed target. A fix was written + verified with 9 passing unit tests in-session, but the
  dispatched task got cancelled mid-work before shipping, so BOTH the fix and the finding were reverted/lost from disk
  -- this doc preserves them. A DIFFERENT sub-agent closed the sibling todo
  (cefi_migration_cutover_and_track8_completion_2026_07_25.md todo 2, the PERP-rename Track-8 item) the SAME day using a
  different tool ("Script 2/3" + a 9-shard dry-run), and its evidence never mentions this bare-decomposed shape or these
  specific ASTER objects -- it is UNCONFIRMED whether that closure's tooling covers this shape at all, since it appears
  to be a different code path than the one this doc's fix targets.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, perp-perpetual, migration, bug, aster, hyperliquid, canonicalisation]
related:
  [
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
created: 2026-07-27
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  [
    "found + fixed + reverted (task cancellation) 2026-07-27, slot-4 -- session on
    cefi_migration_cutover_and_track8_completion-002",
  ]
resolved_by:
locked_by:
locked_since:
---

# HL/ASTER PERP rename script — already-decomposed bare-shape bug (fix ready, not shipped)

## What I found

Running `market-tick-data-service/scripts/migrate_onchain_perp_perpetual_canonical_2026_07_08.py` (dry-run, the default)
against real prod GCS (`market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`, 4,511,202 objects
scanned, ~10 min) surfaced:

```
GCS rename plan: 1496 to rename. Shape breakdown: {'skipped_not_in_scope_or_already_canonical': 341077,
  'skipped_bundled_legacy': 471, 'planned_from_bare_legacy_shape': 1496}
  [DRY] 0G-USDT@LIN.parquet -> ASTER:PERPETUAL:0G-USDT@LIN@LIN.parquet
  [DRY] 2Z-USDT@LIN.parquet -> ASTER:PERPETUAL:2Z-USDT@LIN@LIN.parquet
  [DRY] AAPL-USDT@LIN.parquet -> ASTER:PERPETUAL:AAPL-USDT@LIN@LIN.parquet
  ...
```

Every one of the 1,496 planned renames doubles the `@LIN` margin-marker suffix. Reproduced identically on a second,
independent dry-run run (same 1496 count, same shape).

**Root cause**: the script's docstring assumes only two bare (no `VENUE:` prefix) legacy shapes exist — HL's
`{SYM}-PERP` and ASTER's raw-concatenated `{SYM}{QUOTE}` (e.g. `BTCUSDT`) — both handled by
`legacy_bare_symbol_canonical_id()` → `canonical_symbol()`. But live prod GCS has a THIRD bare shape never documented:
ASTER objects already dash-split with the margin marker baked in, `{BASE}-{QUOTE}@LIN` (e.g. `0G-USDT@LIN`) — just
missing the `VENUE:PERPETUAL:` prefix. `canonical_symbol()` assumes a fully-bare, undelimited symbol; fed
`"0G-USDT@LIN"`, none of `_ASTER_QUOTE_SUFFIXES` (`USDT/USDC/BUSD/USDP/USD1/USD/U`) match the string's actual suffix
(`"LIN"`), so it falls to `return f"{symbol}@{_MARGIN_MARKER}"` = `"0G-USDT@LIN@LIN"`.

Confirmed via manifest audit (separately, `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`,
read-only) that the MANIFEST side has 0 `:PERP:`-shaped instrument_id rows corpus-wide (8,806,763 rows read) — this bug
is purely an ON-DISK GCS OBJECT NAMING issue, invisible to a manifest-only audit.

## The fix (written + unit-tested in-session, NOT currently on disk — task was cancelled before shipping)

In `legacy_bare_symbol_canonical_id()`, detect the already-decomposed shape and pass it through untouched but for the
venue prefix, instead of routing it through `canonical_symbol()`:

```python
# A THIRD bare shape found live 2026-07-27 (dry-run on the real corpus): some ASTER objects are
# already dash-split with the margin marker baked in -- `{BASE}-{QUOTE}@LIN` (e.g. `0G-USDT@LIN`),
# just missing the `VENUE:PERPETUAL:` prefix. Passing this straight through canonical_symbol()
# (which assumes a fully bare, undelimited symbol) mis-detects no ASTER quote suffix matches (the
# stem ends in "LIN", not a quote) and falls through to its bare-symbol branch, producing a
# corrupted double-suffixed name (`...@LIN@LIN`). Detected here and passed through untouched but
# for the venue prefix.
_already_decomposed_symbol_re = re.compile(r"^[A-Z0-9]+-[A-Z0-9]+@(LIN|INV)$")


def legacy_bare_symbol_canonical_id(venue: str, stem: str) -> str | None:
    if not stem or stem in _BUNDLED_LEGACY_STEMS or ":" in stem:
        return None
    sym = _legacy_perp_suffix_re.sub("", stem)
    if not sym:
        return None
    if _already_decomposed_symbol_re.match(sym):
        return f"{venue}:PERPETUAL:{sym}"
    return f"{venue}:PERPETUAL:{canonical_symbol(venue, sym)}"
```

Verified with 9 passing unit tests (loaded via `importlib.util.spec_from_file_location`, mirroring this codebase's
`tests/unit/test_pipeline_e2e_check.py` convention for testing root `scripts/` one-offs — this script has no existing
test file) covering: HL `{SYM}-PERP`, ASTER raw-concatenated, the NEW already-decomposed shape for both ASTER and HL,
out-of-scope inputs, and a full `plan_rename()` blob-name round-trip asserting no `@LIN@LIN` in the output. Re-ran the
real dry-run after applying the fix — process was interrupted by the task cancellation before it finished, so the
fixed-output dry-run was NOT re-confirmed end-to-end this session.

## Why it matters

If `--apply` is ever run against the CURRENT (unfixed) script, all 1,496 ASTER objects get renamed to a corrupted
`...@LIN@LIN` id — silently wrong data going forward (any reader keying on canonical instrument_id would miss these, or
a strict-format assertion downstream could start failing on these specific ids).

**Open question, not resolved this session**: `cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s todo 2 (the
PERP-on-disk-rename Track-8 item) was independently closed the same day by a different sub-agent, citing "a fresh
9-shard `--dry-run` re-verification (full corpus)... confirms 0 further planned changes on every shard" — but that
entry's evidence never mentions this script by name, the `0G-USDT`-style objects, or a 1,496 count; it appears to
describe a DIFFERENT tool ("Script 2/3", a sharded corpus-wide resolver keyed on the `:PERP:`-prefixed manifest shape)
rather than THIS script (`migrate_onchain_perp_perpetual_canonical_2026_07_08.py`, which handles bare NO-prefix
filenames specifically). It is UNCONFIRMED whether that closure's tooling actually covers this bare shape — do not
assume it does just because the sibling todo reads `[x]`.

## Recommended decision

- [ ] [SCRIPT] P1. Re-apply the fix above to
      `market-tick-data-service/scripts/migrate_onchain_perp_perpetual_canonical_2026_07_08.py`'s
      `legacy_bare_symbol_canonical_id()`, add the regression test file (pattern given above), ship via the normal QG +
      quickmerge flow.
- [ ] [SCRIPT] P1. Re-run the dry-run
      (`GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp     DEPLOYMENT_ENV=prod CLOUD_MOCK_MODE=false .venv/bin/python     scripts/migrate_onchain_perp_perpetual_canonical_2026_07_08.py`,
      ~10 min, read-only) to confirm all 1,496 previously-buggy renames now target the CORRECT (non-double-suffixed)
      canonical shape, and cross-check whether the sibling `cefi_migration_cutover_and_track8_completion_2026_07_25.md`
      todo 2's "Script 2/3" closure already independently covers/resolves these same 1,496 objects (if so, this todo may
      already be moot — verify before running `--apply`, do not assume either way).
- [ ] [SCRIPT] P2. Once confirmed fixed + no double-suffix + cross-checked against the sibling closure, execute
      `--apply --stamp <stamp>` for the 1,496 real renames (small, bounded scale — a direct execution, not a VM launch)
      with the standard idempotent copy→verify→delete safety this script already implements.
