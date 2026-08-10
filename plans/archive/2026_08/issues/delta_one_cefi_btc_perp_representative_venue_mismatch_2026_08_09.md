---
doc_type: issue
title:
  "features-service delta_one: MVP-universe perp-representative selection now picks COINBASE-FUTURES for CEFI/BTC, not
  BITGET-FUTURES — conflicts with the already-established legacy delta_one BTC corpus"
created: 2026-08-09
author: slot-29
assigned_vm: planning
status: resolved
tags: [data-correctness, features-service, delta_one, cefi, btc, universe-filter, perp-collapse, instrument-id]
source:
  [
    'plans/active/issues/delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md P2 re-run todo
    ("features-service: recompute the corpus for the intraday BTC mean-reversion cs-ML feature")',
  ]
summary:
  "After both the id-form-translation fix (features-service@d2e32548) and the venue-volume reference-date fix
  (features-service@1cd9f819) landed, features-service delta_one's MVP-universe perp-representative collapse for
  CEFI/BTC now correctly avoids the DERIBIT zero-coverage bug — but selects COINBASE-FUTURES, not BITGET-FUTURES, as
  BTC's representative venue for the 2026-05-03 backfill window. The existing partial delta_one BTC corpus (momentum
  feature group, same window) was computed against BITGET-FUTURES via a pre-perp-collapse legacy code path, so the two
  disagree on which venue IS 'cefi/BTC' for delta_one purposes."
nature: process
asset_group: cefi
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
related: [delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09]
parent_epic: cefi_master
resolved_by: >-
  delta_one_cefi_btc_perp_representative_venue_mismatch-d8b052488b6e (slot 17, infra/data_engineering, 2026-08-10) —
  features-service@2ea0c8cb, see Progress Log
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
sequential: false
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-10 — RESOLVED** (status: resolved, 0 open todos, unlocked). `features-service@2ea0c8cb` threaded
> an `explicit_instrument_override` flag from `BatchHandler._resolve_instrument_list` through
> `filter_instruments_for_family`, skipping `_collapse_to_perp_representative` whenever the caller named specific
> `--instruments` — per the operator ruling in this doc's own "Operator ruling (2026-08-10)" section. Archived by task
> `delta_one_cefi_btc_perp_representative_venue_mismatch-d8b052488b6e` (slot 17, 2026-08-10).

## What I found

Continuing `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`'s P2 re-run todo ("features-service:
recompute the corpus for the intraday BTC mean-reversion cs-ML feature") after BOTH of that issue's fixes had landed
(`features-service@d2e32548` id-form translation, `features-service@1cd9f819` venue-volume reference-date fix), the
`returns`/`statistical_anomaly` backfill for cefi/BTC still cannot complete — for a NEW, distinct reason:

Re-running the exact repro from the parent issue
(`--asset-group CEFI --start-date 2026-05-03 --end-date 2026-05-03 --feature-group returns --instruments "BITGET-FUTURES:PERPETUAL:BTCUSDT"`)
now PASSES lookback validation (the id-form fix works), but the MVP-universe filter's perp-representative collapse
(`mvp_universe_filter._collapse_to_perp_representative`) still drops the instrument:
`perp_collapse: retained 0/1 (bases=1; dropped non-rep-venue=1, no-rep=0, unparseable=0)` →
`WARNING No instruments remain after MVP universe filter for group=returns asset_group=CEFI (started with 1)`.

Root cause: `_collapse_to_perp_representative` computes the representative venue for BTC from the FULL global
`venue_volumes` snapshot (`aggregate_cefi_manifest_volume`, trailing-30-day `instrument_count` ending at the backfill's
own `start_date`), independent of which candidate instruments were actually passed via `--instruments`. Querying that
same aggregator directly for `reference_date=2026-05-03`:

```
COINBASE-FUTURES BTC-USD@LIN   50,580,751
BITGET-FUTURES   BTC-USDT@LIN  28,503,533
OKX-SWAP         BTC-USDT@LIN  14,958,040
...
DERIBIT          BTC-USD@INV      302,816   (the venue the 1cd9f819 fix correctly stopped selecting)
```

COINBASE-FUTURES now wins on trailing tick-count (`instrument_count`) — the 1cd9f819 fix correctly eliminated the
zero-coverage DERIBIT pick, but the venue that wins instead is still not BITGET-FUTURES, the venue the EXISTING partial
delta_one corpus for this exact base/date already used. Confirmed COINBASE-FUTURES DOES have genuine
`capture_status=captured` MTDS tick data for BTC-USD@LIN on all 4 of the P2 todo's target days (2026-04-22, 2026-05-01,
2026-05-02, 2026-05-03) — this is not a coverage gap on COINBASE's side. However, COINBASE-FUTURES has NEVER been
computed for ANY delta_one feature_group for BTC — no GCS object exists at
`gs://features-cefi-prd-central-element-323112/delta_one/by_date/day=2026-05-03/feature_group=<any>/timeframe=15s/COINBASE-FUTURES:PERPETUAL:BTCUSD.parquet`
for momentum or any other already-shipped group — while `BITGET-FUTURES:PERPETUAL:BTCUSDT.parquet` DOES exist for
momentum on the same day. That corpus was written via the LEGACY pre-perp-collapse code path (per
`filter_instruments_for_family`'s own docstring: "When [venue_volumes is] None, the legacy per-family base+type filter
applies unchanged (back-compat for callers that have not wired the volume aggregator yet)") — i.e. before
`features-service@48911e87` ("wire real venue-volume observations into the perp collapse") existed at all.

So there are now two disagreeing notions of "cefi/BTC" for delta_one: the LEGACY corpus (BITGET-FUTURES, all
already-shipped feature groups) and the CURRENT volume-based selector (COINBASE-FUTURES, as of the fixed reference-date
logic). Passing `--instruments BITGET-FUTURES:PERPETUAL:BTCUSDT` explicitly does NOT override the collapse — the
collapse always wins over an explicit caller instrument choice for any delta-one (non-roll, non-options) family, by
design (`filter_instruments_for_family`'s docstring: only roll/spread/options families skip the collapse; "the
instrument the caller asked for" is not itself a skip condition).

### Repro (features-service repo, `.tabs/29/features-service`, fix commits already applied)

```bash
ENVIRONMENT=production uv run python -m features_service.delta_one \
  --operation compute --mode batch --asset-group CEFI \
  --start-date 2026-05-03 --end-date 2026-05-03 \
  --feature-group returns --instruments "BITGET-FUTURES:PERPETUAL:BTCUSDT" --preflight-only
# Lookback validation PASSED: 1/1 instruments OK
# perp_collapse: retained 0/1 (bases=1; dropped non-rep-venue=1, no-rep=0, unparseable=0)
# WARNING No instruments remain after MVP universe filter for group=returns asset_group=CEFI (started with 1)
```

## Why it matters

Blocks the SAME two P2 todos `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md` already tracks (the
"recompute the corpus for the intraday BTC mean-reversion cs-ML feature" todo and its sibling "BTC trend feature corpus
recompute" P2.11.16 todo) — both need a `returns`/`statistical_anomaly`/`volatility_realized` backfill for
`BITGET-FUTURES:PERPETUAL:BTCUSDT` specifically (matching the existing partial corpus), and neither can reach done-when
while the collapse keeps dropping that exact instrument. It is also a LATENT blocker for every other CEFI base whose
current 30-day-trailing tick-volume representative differs from whichever venue an earlier, pre-`48911e87` legacy run
already used — this is very plausibly not BTC-specific, just the first base anyone has hit it on since the collapse
landed.

This is NOT the same bug as the parent issue (id-form translation) or `1cd9f819`'s reference-date bug — both of those
are now confirmed fixed and working correctly. This is a genuinely NEW question: which venue represents a given CEFI
base for delta_one, when the volume-based selector's current answer disagrees with what was already computed under the
legacy pre-collapse path.

## Recommended decision

Three candidate resolutions, in my order of preference, all requiring an operator/plan-author call rather than a
worker's unilateral pick (this determines what "cefi/BTC" means across delta_one going forward, not a bounded mechanical
fix):

**(a) Explicit `--instruments` should bypass `_collapse_to_perp_representative` entirely.** When the caller names a
specific instrument (not doing full-universe auto-discovery), the collapse's job — picking ONE representative out of
MANY candidates — is moot; the caller already picked one. This is the smallest, most semantically obvious change
(mirrors how `_resolve_instrument_list` already skips `record_out_of_scope_instruments` for the same "explicit override"
case), lets the existing BITGET-based corpus continue uninterrupted, and doesn't require deciding anything about
COINBASE. Blast radius: changes behavior for every CEFI delta_one CLI invocation that passes `--instruments`, not just
BTC — needs its own regression tests (both the "still collapses on full-universe auto-discovery" case and the "override
bypasses collapse" case) and should land as its own properly-scoped change per the same reasoning the parent issue used
for the id-form fix ("too broad a blast radius to patch inline under a single P2 corpus-recompute todo").

**(b) Switch cefi/BTC delta_one to COINBASE-FUTURES going forward**, matching current volume-based selection. Requires
recomputing the ALREADY-SHIPPED momentum feature group (and any other already-computed BTC delta_one groups) for
consistency — a bigger, cross-group recompute than either P2 todo's stated scope, and changes which instrument any
downstream consumer (e.g. the cs-ML feature this was filed to unblock) actually reads for "BTC".

**(c) Pin BITGET-FUTURES as CEFI/BTC's delta_one representative** (a base-specific override table, or exclude BTC from
the volume-based collapse and fall back to the legacy per-family filter for it specifically). Keeps existing corpus
continuity without a blanket CLI-semantics change, but is a special-case exception that needs its own documented
justification (why BTC, why BITGET) and doesn't generalize to the next base that hits the same disagreement.

## Operator ruling (2026-08-10)

Option **(a)** — explicit `--instruments` bypasses `_collapse_to_perp_representative` entirely — ruled via `/blocked`
(`BLK-13405a35`, answered by main). Rationale: silently dropping an explicitly-named instrument is itself the bug; this
preserves the existing BITGET-based corpus without a cross-group recompute (rules out (b)) and avoids a BTC-only special
case that wouldn't generalize (rules out (c)). Scope as its own change with regression tests, filed as its own todo
below — NOT bundled into either P2 corpus-recompute todo in the parent issue.

- [x] ✅ [DATA] P2. Make an explicit `--instruments` override bypass `_collapse_to_perp_representative` in —
      features-service@2ea0c8cb `features_service/delta_one/universe/mvp_universe_filter.py`'s
      `filter_instruments_for_family` — thread a caller-explicit flag (mirroring how
      `BatchHandler._resolve_instrument_list`, `features_service/delta_one/cli/handlers/batch_handler.py:476`, already
      distinguishes `instruments is None` auto-discovery from an explicit caller-provided list via its
      `record_out_of_scope_instruments` gate) from `_resolve_instrument_list` through `_process_one_group`
      (`batch_handler.py:733`'s `filter_instruments_for_family(...)` call site) into `filter_instruments_for_family`,
      and skip the `_collapse_to_perp_representative` call (mvp_universe_filter.py:182) when set. Add regression tests
      in `tests/delta_one/unit/test_mvp_universe_filter.py`: (1) full-universe auto-discovery (no explicit override)
      still collapses to one representative venue per base — unchanged behavior; (2) an explicit `--instruments`
      override bypasses the collapse entirely and the named instrument(s) survive the filter regardless of
      trailing-volume ranking. Repo: features-service. Unblocks both P2 re-run todos in
      `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`.

## Progress Log

- 2026-08-09 (slot-29, task delta_one_cefi_lookback_instrument_id_form_mismatch-53a0d8ce974a): Resumed the "recompute
  the corpus for the intraday BTC mean-reversion cs-ML feature" P2 re-run todo after confirming both
  `features-service@d2e32548` (P1 id-form fix, slot-14) and `features-service@1cd9f819` (venue-volume reference-date
  fix, slot-10 — found while working this same P2 re-run todo, not yet logged in the parent issue's own Progress Log)
  were live on `origin/live-defi-rollout`. Re-ran the parent issue's repro command and confirmed lookback validation now
  PASSES, but hit this NEW blocker (perp_collapse dropping BITGET in favor of COINBASE). Directly queried
  `aggregate_cefi_manifest_volume` to confirm the venue ordering and confirmed via `gcs_describe_object` that
  COINBASE-FUTURES has never been computed for any delta_one BTC feature group (no existing output), while
  BITGET-FUTURES has (momentum, same day) — ruling out an honest-absence explanation on COINBASE's side and confirming
  this is a genuine representative-selection disagreement, not a data gap. Filed this issue (unified-trading-pm, this
  commit) rather than picking a resolution unilaterally — dispatch-scope eligibility requires the outcome be
  worker-determinable, and "which venue is cefi/BTC" is a judgment call. Also found + fixed an INDEPENDENT bug while
  diagnosing: `--preflight-only`/`--skip-preflight` were dead CLI flags in `BatchHandler.run()`
  (`features_service/delta_one/cli/handlers/batch_handler.py`) — both are named parameters of `run()`'s own signature,
  so they never reached the `**kwargs` dict forwarded to `_run_batch_pipeline`/ `_run_preflight`, which read them via
  `kwargs.get(...)`. This meant every `--preflight-only` invocation (including the parent issue's own documented repro
  commands) silently ran the FULL batch pipeline instead of stopping after the lookback check — confirmed live: my own
  first diagnostic `--preflight-only` run wrote a real `capture_status=attempted_failed` manifest row for
  CEFI/returns/2026-05-03 to the PROD features-cefi manifest (honest failure record, not corrupted data — the run
  genuinely produced 0 output that attempt — but not the intended dry-run side-effect-free check). Fixed in
  `features-service@<pending>` by forwarding both flags into the kwargs dict; added regression tests
  (`TestRunForwardsPreflightFlags` in `tests/delta_one/unit/test_batch_handler_expected_unattempted.py`) asserting
  `run()` forwards `preflight_only`/`skip_preflight` through to `_run_batch_pipeline`. Escalating this issue's
  venue-representative question via `/blocked` before continuing.
- 2026-08-10 (slot-6, resumed task `delta_one_cefi_lookback_instrument_id_form_mismatch-53a0d8ce974a`): Resumed after a
  slot restart. The prior session's `/blocked` escalation above was never actually registered via the orchestrator API
  (confirmed by querying `GET /api/state`'s `blocked_queue` — no entry existed for this question, despite the Progress
  Log text claiming it was filed; likely the session ended before the API call landed) — filed it for real now
  (`blocked_id: BLK-13405a35`, same 3 options/recommendation as the "Recommended decision" section above). Repos all
  clean (no uncommitted WIP from the prior session survived). Waiting on the operator/main ruling; no other in-scope
  work remains on this P2 todo until the venue-representative decision lands.
- 2026-08-10 (slot-6): Main answered `BLK-13405a35` — option (a) ruled. Added the "Operator ruling" section above + a
  scoped `- [ ]` fix todo (explicit `--instruments` bypasses `_collapse_to_perp_representative`, with the exact
  thread-through path from `_resolve_instrument_list` to `filter_instruments_for_family`, plus the two required
  regression tests) per main's explicit instruction to file it as its own todo rather than bundle it into either P2
  re-run todo. Did NOT implement the fix in this session — main's ruling text says to file it, not do it inline, and
  this task's own craft/scope is the P2 re-run, not this shared-core dependency-checker-adjacent change. Note:
  `depends_on`/`sequential` only gate ordering/archival WITHIN a doc and do not affect cross-doc dispatch (per
  CLAUDE.md), so they can't gate the parent issue's P2 todos on this doc's new fix todo — the actual backstop is the
  `GATED`-reason_code skip on this session's own dispatched instance below.
  `delta_one_cefi_lookback_instrument_id_form_mismatch-53a0d8ce974a` (this session's actual dispatched task) stays
  blocked on this new todo landing — skipping it with `reason_code: GATED` rather than holding the slot idle.
- 2026-08-10 (slot-17, task `delta_one_cefi_btc_perp_representative_venue_mismatch-d8b052488b6e`): Implemented the P2
  fix todo per the operator ruling. Added `explicit_instrument_override: bool = False` to
  `filter_instruments_for_family` (`mvp_universe_filter.py`) — when True, the perp-representative collapse
  (`_collapse_to_perp_representative`) is skipped entirely; the base-asset/type gate in `_apply_cefi_filter` still
  applies unchanged. Computed the flag in `BatchHandler._execute_batch` as `instruments is not None` (mirroring
  `_resolve_instrument_list`'s own `record_out_of_scope_instruments` gate) and threaded it through `_process_groups` →
  `_process_one_group` → the `filter_instruments_for_family` call site. Added 4 regression tests in
  `tests/delta_one/unit/test_mvp_universe_filter.py` (`TestExplicitInstrumentOverrideBypassesCollapse`): (1)
  full-universe auto-discovery (no override) still collapses unchanged, (2) an explicit override survives even when it
  names the non-representative (lower-volume) venue, (3) multiple explicitly-named venues for the same base all survive,
  (4) the override only skips the collapse — the base-asset/type gate still excludes out-of-universe instruments.
  Updated the unrelated `fake_process_groups` mock signature in `tests/delta_one/unit/test_persistence_event_details.py`
  to accept the new positional param. Full `quality-gates.sh` green (both pre-commit and post-commit Pass-1 runs,
  sentinel matched committed HEAD). Shipped: features-service@2ea0c8cb, verified as ancestor of
  `origin/live-defi-rollout`.
