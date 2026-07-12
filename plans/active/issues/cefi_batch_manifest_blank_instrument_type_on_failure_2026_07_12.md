---
doc_type: issue
title:
  Tardis per-symbol batch failures write manifest rows with instrument_type="" — masks Layer-1 completeness for ANY
  venue with per-symbol capture failures, not just BITGET-FUTURES
summary:
  'market-tick-data-service''s generic per-symbol Tardis fan-out (`tardis_batch_download.py::_run_per_symbol_batch` /
  `_emit_per_symbol_manifest`) builds `PerSymbolTask.row_key` with only `venue`/`data_type`/`instrument_id`/`date` — no
  `instrument_type`. `instrument_type` is only derived from the FETCHED response (`_classify_row_instrument_type`, which
  runs after a successful CSV parse), so the FAILURE path (`record_failed`) always writes `instrument_type=""`.
  Confirmed live: BITGET-FUTURES alone carries 41,027/4,063/40,845/75,466 blank-instrument_type `attempted_failed` rows
  across book5/derivative_ticker/trades/liquidations — none of which can ever satisfy a Layer-1 completeness check
  requiring an exact (venue, instrument_type, data_type) match. This is the generic per-symbol path used by EVERY
  CeFi/Tardis venue going through `download_batch`, so any venue/itype whose fetches fail before parsing (auth,
  rate-limit — see the sibling `tardis_concurrent_ip_lockout_2026_07_12.md` finding, network, 4xx/5xx) is affected, not
  just BITGET-FUTURES.'
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, manifest, mvp-backfill-v10]
related:
  [
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    tardis_concurrent_ip_lockout_2026_07_12.md,
    cefi_layer1_denominator_gaps_2026_07_03.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source:
  mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T13:00-13:35Z session (data_engineering slot-2)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on: []
---

## What I found

Live-queried the cefi prd manifest for `(venue=BITGET-FUTURES)` grouped by
`(instrument_type, data_type, capture_status)`:

```
BITGET-FUTURES  (blank itype)  book_snapshot_5    attempted_failed   41,027
BITGET-FUTURES  (blank itype)  derivative_ticker   attempted_failed    4,063
BITGET-FUTURES  (blank itype)  trades              attempted_failed   40,845
BITGET-FUTURES  (blank itype)  liquidations         attempted_failed  75,466
BITGET-FUTURES  PERPETUAL       book_snapshot_5    captured           23,532   (correctly tagged, success path)
BITGET-FUTURES  PERPETUAL       trades              captured          23,956   (correctly tagged, success path)
BITGET-FUTURES  perpetual       book_snapshot_5    empty_confirmed       800   (lowercase — separate casing drift)
```

Dispatched a code-read sub-agent to trace why. Confirmed:

1. **Row-key construction never includes `instrument_type`** — `tardis_batch_download.py:116-123`, inside
   `_run_per_symbol_batch`, `PerSymbolTask.row_key` is built from `venue`/`data_type`/`instrument_id`/`date` only, on
   EVERY task (success or failure).
2. **Failure-path write** — `_emit_per_symbol_manifest`, `record_failed(row_key=_rk, ...)` (line 208) uses the same
   incomplete `_rk` — `instrument_type` absent.
3. **Success-path type derivation happens too late to help failures** — `instrument_type` is derived from the _parsed_
   response (`_classify_row_instrument_type`, `tardis_cefi_shards.py:87,420` / `tardis_shared.py:668-684`), which only
   runs after a successful fetch produces a DataFrame. Both failure branches
   (`_download_one_perp_symbol_legacy`/`_streaming`) raise before that classification step ever runs.
4. **Downstream default → `""`** — `unified-trading-library`'s `_coerce_row_key` (`manifest_writer/_rows.py:252,270`)
   initializes every row-key column (including `instrument_type`) to `""`, only overwriting keys present in the caller's
   `row_key` dict. Since `instrument_type` is never in `row_key` on the failure path, `""` lands in the manifest.
5. **Contrast with the LIVE recorder** — `market_tick_data_service/live/manifest_recorder.py`'s `record_failed`
   (`_resolve_row_key`, lines 209-244) DOES thread `instrument_type` through on failure. This is the codebase's own
   established convention; the batch/Tardis per-symbol path simply never implements it.

**Fix is cheap, per the follow-up fixability check (same session)**: `_resolve_symbols` (`tardis_symbol_resolution.py`)
already loads a GCS parquet with an `instrument_type` column for its catalogue-driven symbol resolution, but discards
it, returning bare symbol strings only. Cheaper still: `download_batch` already calls
`TardisAdapter._classify_row_instrument_type(symbol, venue)` — a pure regex/string classifier, no I/O — PRE-fetch for
its Deribit option/future symbol-stripping logic. Plumb: (1) add `canonical_venue: str | None` to
`_run_per_symbol_batch`, passed from `download_batch` (already computed there); (2) inside the `PerSymbolTask` loop, add
`"instrument_type": TardisAdapter._classify_row_instrument_type(sym, canonical_venue).value` to `row_key`. Small,
same-session-sized change — one function signature, one call site, one dict literal.

## Why it matters

Blast radius is EVERY CeFi/Tardis venue, not just BITGET-FUTURES — `_run_per_symbol_batch`/`_emit_per_symbol_manifest`
is the generic per-symbol fan-out for the whole `download_batch` path (only Deribit gets special option/future symbol
stripping upstream; the row-key/record_failed logic itself is venue-agnostic). Combined with the sibling
`tardis_concurrent_ip_lockout_2026_07_12.md` finding (which explains WHY so many per-symbol fetches are failing in the
first place — Tardis 403 lockouts, not genuine absence), this bug means a large fraction of this plan's attempted_failed
volume is BOTH (a) caused by a self-inflicted concurrency conflict AND (b) invisible to Layer-1 completeness checks even
after the underlying lockout is fixed and captures succeed on retry, because the interim failure rows can never evidence
"this (venue, itype, data_type) triple was attempted." Every venue currently blocked on a Layer-1 "genuine capture gap"
diagnosis in this plan's history should be re-examined once this fix lands, in case the true state was "attempted many
times, always mis-tagged blank" rather than "never attempted."

## Recommended decision

Route to `data_engineering` — implement the `_classify_row_instrument_type` pre-fetch plumbing described above, add a
regression test asserting a simulated per-symbol failure writes a non-blank `instrument_type` matching the symbol's
classification, run `quality-gates.sh`, ship via quickmerge. No architecture decision needed (unlike the concurrent-IP
finding) — this is a self-contained, in-craft code fix.

## Todos

- [x] ✅ [SCRIPT] P1. Thread `instrument_type` through `_run_per_symbol_batch`'s `PerSymbolTask.row_key` via
      `TardisAdapter._classify_row_instrument_type(sym, canonical_venue)` (pre-fetch, pure classifier — no I/O), so BOTH
      success and failure manifest writes carry a real instrument_type. Add a regression test for the failure path
      specifically (a mocked per-symbol exception should still produce a correctly-classified `instrument_type` in the
      resulting `attempted_failed` row). (repo: market-tick-data-service) — market-tick-data-service@91ac1caa.
      `download_batch` now resolves `canonical_venue` via `self._resolve_canonical_venue(exchange, canonical_venue)`
      before calling `_run_per_symbol_batch` (so DERIBIT-COMBO doesn't collapse onto bare DERIBIT), and
      `_run_per_symbol_batch` adds
      `"instrument_type": TardisAdapter._classify_row_instrument_type(sym,     canonical_venue).value` to every
      `PerSymbolTask.row_key`. Two regression tests added in
      `tests/unit/test_tardis_batch_download_failure_instrument_type.py`: a mocked per-symbol failure on BITGET-FUTURES
      asserts `record_failed`'s `row_key["instrument_type"] == "PERPETUAL"` (not blank), and a DERIBIT-COMBO
      combo-symbol failure asserts `"OPTION"` (proving the resolved-canonical-venue path, not the raw Tardis exchange
      slug, drives classification). quality-gates.sh green (10/10 targeted tests + full suite pass,
      sentinel=91ac1caa63ef67188b702cb195f15fa45576b05d).
- [x] ✅ [DATA] P2. After the fix lands, re-classify or leave-as-legacy the existing blank-`instrument_type`
      `attempted_failed` rows already in the manifest (this doc's BITGET-FUTURES numbers plus whatever other venues
      carry the same pattern) — decide whether a one-time backfill re-tag (matching `instrument_id` against the same
      classifier) is worth it or whether they should just age out as new attempts supersede them. (repo:
      instruments-service) — **DECISION: leave-as-legacy now; defer any active re-tag to a gated post-recapture audit.
      Full reasoning + evidence in "## P2 Decision" below.** The todo's assumed "age out as new attempts supersede them"
      mechanism is DISPROVEN (manifest dedup keys a populated `instrument_type` distinct from blank/None, so a post-P1
      successor never collapses the legacy blank row), but active re-tag is NOT worth building now — the residual rows
      become harmless Layer-1 strays once re-capture lands, and no canonical low-risk tool re-tags `attempted_failed`
      rows. (decision-only, no code — recorded 2026-07-12 by slot-11 data_engineering)
- [ ] [DATA] P3. GATED on the P1-corrected cefi backfill re-capture sweep (which itself is gated on the sibling
      `tardis_concurrent_ip_lockout_2026_07_12.md` lockout fix): run a Layer-1 completeness audit over the affected
      Tardis/cefi venues. ONLY if it shows residual blank-`instrument_type` `attempted_failed` rows for (venue,
      instrument_type, data_type) triples that genuinely never re-captured (delisted / permanent gap) — and are
      therefore real Layer-1 holes rather than harmless strays — build a scoped, consolidator-coordinated reconciler
      re-tag for exactly those rows. Do NOT in-place-mutate the consolidated `_index/availability_index.parquet` (breaks
      the write-time CAS + consolidator-coordination contract; see `## P2 Decision`). (repo: instruments-service)

## P2 Decision (2026-07-12, slot-11 data_engineering)

**Decision: leave the existing blank-`instrument_type` `attempted_failed` rows as legacy for now; do NOT build a
one-time re-tag backfill. Defer a scoped re-tag to a GATED post-recapture Layer-1 audit (new P3 todo above).**

Prerequisite check: P1 (`-001`) landed while this was being decided — `market-tick-data-service@91ac1caa` threads
`instrument_type` into every `PerSymbolTask.row_key` (success AND failure paths), so from now on the writer stops
producing blank-itype rows. The decision below therefore governs only the pre-91ac1caa legacy rows.

Three independent lines of evidence drove the call:

1. **The todo's assumed "age out as new attempts supersede them" is mechanically IMPOSSIBLE.** The manifest reader and
   consolidator dedup on `(date, venue, data_type, service_name)` + present optional dims (which include both
   `instrument_id` and `instrument_type`). Their key-normaliser collapses `""` and `None` to a single NULL sentinel but
   keeps any _populated_ value distinct —
   `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:725-732` (`_dedup_key_series`),
   mirrored in `manifest_consolidator._dedup_key_sql`. P1 classifies BITGET-FUTURES perps as the populated string
   `"PERPETUAL"`, so a post-P1 successor row carries `instrument_type="PERPETUAL"` while the legacy row carries
   `instrument_type=""` → **different dedup keys → they never collapse → the legacy blank row survives forever**
   alongside its successor. (Contrast the one case that DOES age out: a successor written with `instrument_type=None`
   dedups against a blank predecessor — the understat regression in
   `tests/unit/test_manifest_writer_per_vm.py::test_reader_dedups_optional_dim_null_vs_empty_string`. That does not
   apply here because the CeFi successor itype is a populated value, not None.)

2. **Post-recapture the residual blank rows are harmless Layer-1 STRAYS, not holes.** Per
   `codex/02-data/honest-coverage-model.md`, Layer-1 completeness = `|EXPECTED ∩ ENUMERATED| / |EXPECTED|`;
   `missing_tuples = EXPECTED − ENUMERATED` are holes, whereas a tuple present in ENUMERATED but absent from EXPECTED is
   a **stray** — "logged as a Layer-1 warning, not a hole." Once the P1-corrected pipeline re-captures the affected
   `(venue, PERPETUAL, data_type)` triples, EXPECTED is satisfied by real `captured` rows and the leftover
   `(venue, ""/blank, data_type)` `attempted_failed` rows fall into ENUMERATED-only → they downgrade from Layer-1 holes
   to logged strays and stop blocking completeness. So the completeness signal self-heals on re-capture without any
   mutation.

3. **There is no canonical, low-risk tool to re-tag `attempted_failed` rows, and the obvious cheap paths don't work.**
   - `ManifestWriter` exposes no bulk-mutate API _by design_ — manifest mutation goes through
     `record_captured`/`record_empty`/`record_failed` to preserve write-time CAS + consolidator coordination (documented
     in `market-tick-data-service/scripts/cleanup_kraken_spot_empty_confirmed.py`). In-place editing the consolidated
     `_index/availability_index.parquet` (the sports XG one-off `reclassify_xg_blank_league_phantoms.py` did this) races
     the consolidator daemon and can be reverted on the next consolidation.
   - The canonical bulk-mutation path, the phantom-audit reconciler
     (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`), **skips `attempted_failed` rows by design**
     — it only touches `captured`/`empty_confirmed` phantoms — so it will not re-tag these.
   - Re-emitting via `record_failed` with the correct `instrument_type` writes a NEW row with a populated-itype dedup
     key (newer `attempted_at`) — it does not remove the blank row; it just adds a sibling. So it fails to clean up.
   - A correct re-tag would therefore require _new_ code: a consolidator-coordinated reconciler extended to re-tag
     `attempted_failed` rows (with a captured-wins collision guard so a re-tagged failed row can never mask a real
     capture on the same key). That is disproportionate to the benefit given (2).

**Net:** the correctness cost of leaving these rows is bounded (harmless strays after re-capture), while an eager re-tag
is genuinely risky (prod manifest mutation, consolidator coordination, no existing tool) — so the right sequencing is
writer-fix (P1 ✅) → lockout-fix (sibling issue) → re-capture sweep → Layer-1 audit → **conditional** scoped re-tag only
for triples that provably never re-capture. That conditional work is tracked as the P3 todo above; it stays a real
Layer-1 concern (blank `instrument_type` is a genuine hole per honest-coverage-model.md) for exactly the
never-recaptured subset, which is why it is gated rather than dropped.

No code shipped for this decision by design — the deliverable is the decision itself plus the gated P3 follow-up; the
`## What I found` counts (BITGET-FUTURES 41,027 / 4,063 / 40,845 / 75,466) remain the scale reference for the future
audit.
