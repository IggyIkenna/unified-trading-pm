---
doc_type: issue
title:
  MDPS SPORTS honest-absence candle writes always fail the manifest's FetchEvidence gate — silently degrade to WARNING,
  never actually recorded
summary: >-
  Both MDPS candle-derivation callers that route a SPORTS empty timeframe to `record_empty_for_shard` pass
  `league_id=""` (documented as structurally unresolvable at this layer), which forces `classify_sports_empty_reason()`
  to fall back to `EmptyConfirmedReason.SOURCE_RETURNED_ZERO`. The manifest writer's honest-absence gate (DP-FETCH-001)
  hard-requires `FetchEvidence` for that reason, which a derivation layer reading already-captured raw tick parquet
  structurally cannot supply — so the write always raises, is caught by shard-level-failure-isolation, and degrades to a
  WARNING log with NO manifest row ever written. Every SPORTS honest-absence candle-timeframe is therefore invisible to
  the manifest (looks like "never attempted", not "tried, genuinely empty") — the exact class of gap DP-FETCH-001 was
  built to catch, now recurring one layer downstream of where it was fixed.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
created: 2026-08-01
assigned_vm: NA
parent_epic: infrastructure_master
resolved_by:
locked_by:
source: [DP-VM-001 escalation agt-f5ddd4]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
tags: [data-pipeline, mdps, sports, honest-absence, manifest, dp-fetch-001]
priority: P2
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_chain.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_streaming.py,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_manifest.py,
  ]
---

# MDPS SPORTS honest-absence candle writes always fail the manifest's FetchEvidence gate

## What I found

Investigating a DP-VM-001 escalation (`agt-f5ddd4`, VM `mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067`,
`exit_code=1`), I root-caused the VM's fatal exit to a separate bug (fixed same-session:
`market-data-processing-service` `live_workers.py::_run_adapter_and_write`'s `success` formula misclassified
honest-absence timeframes as failures). While tracing that, the VM's `run.log` also showed a second, independent
finding:

```
WARNING MDPS canonical_writer: empty_confirmed manifest write failed for
FOOTBALL:williamhill:h2h:soccer_uefa_champs_league:2025/2026:FC Kairat-Club Brugge::DRAW day=2025-12-24 tf=15m:
record_empty(reason=SOURCE_RETURNED_ZERO) requires FetchEvidence proving a clean 200+empty fetch (http_status in 2xx
AND response_received AND rows_in_response == 0 AND error_signal == ""). The supplied evidence does NOT prove honest
absence (no FetchEvidence supplied). ...
```

Tracing the call path:

1. `live_workers_chain.py::_write_or_record_empty_timeframe` (Path A, the standard non-chain candle path) and
   `live_workers_streaming.py::_record_streaming_empty_timeframe` (the chain-bundle streaming path) both call
   `record_empty_for_shard(..., reason=classify_sports_empty_reason(league_id="", ...))` for SPORTS when an adapter
   legitimately produces zero candles for a timeframe. Both call sites' own comments say `league_id` is "genuinely
   UNRESOLVABLE at this candle-worker layer" — i.e. this is not an occasional gap, it is the **permanent** state for
   every call from these two sites.
2. `canonical_writer_manifest.py::classify_sports_empty_reason` —
   `if not league_id: return EmptyConfirmedReason.SOURCE_RETURNED_ZERO` (line 249-250) — so every one of these calls
   resolves to `SOURCE_RETURNED_ZERO`, never a calendar-derived `EXPECTED_*` reason.
3. `_emit_status_for_shard` → `ManifestWriter.record_empty(reason="SOURCE_RETURNED_ZERO", ...)` — the UTL writer's
   honest-absence gate (DP-FETCH-001, `codex/05-infrastructure/data-pipeline-alerts.md`) hard-requires `FetchEvidence`
   for `SOURCE_RETURNED_ZERO` (a post-_fetch_ honest-empty signal). This derivation layer only reads already-captured
   raw tick parquet — no live fetch happens here — so it structurally cannot supply that evidence. The write raises.
4. `_emit_status_for_shard`'s `except Exception` (shard-level-failure-isolation, correctly) catches this and degrades to
   a `logger.warning(...)` — so the run doesn't crash, but **no manifest row is ever written** for the shard.

This is precedented: `batch_workers.py::_handle_empty_tick_data` already made the equivalent fix for CEFI/DEFI/TRADFI —
those asset_groups route to `record_failed_for_shard` instead of `record_empty_for_shard` specifically _because_ "no
live fetch happened at this derivation layer... so there is no FetchEvidence to supply" (operator decision 2026-06-22,
cited in that file). SPORTS was deliberately left on `record_empty_for_shard` because a sports instrument-day empty CAN
be a legitimate calendar absence (`EXPECTED_NO_FIXTURE` etc.) — but that typed-reason path only actually resolves when
`league_id` is available, and at these two call sites it never is.

## Why it matters

Every SPORTS honest-absence candle-timeframe from these two call sites is invisible to the manifest — indistinguishable
from "never attempted" rather than "tried, genuinely empty". This is the exact silent-gap class DP-FETCH-001's
FetchEvidence gate and the 2026-07-27 "Chain-bundle streaming produced 0 candles" fix (finding 2, referenced in both
call sites' docstrings) were built to close — it has recurred one layer downstream, at the manifest-write boundary
itself, for SPORTS specifically. Downstream coverage rollups / re-probe audits that trust the manifest as SSOT will
never re-visit these shards as "confirmed empty", and will also never flag them as attempted_failed for someone to
investigate — they simply vanish.

## Recommended decision

This needs an operator/architecture call, not a guess — two plausible paths, not obviously equivalent:

- **A**: Mirror the CEFI/DEFI/TRADFI fix — when `classify_sports_empty_reason` resolves to (falls back to)
  `SOURCE_RETURNED_ZERO` specifically (i.e. no calendar-typed reason was available), route to `record_failed_for_shard`
  instead, same as the other asset_groups. Loses the "legitimate calendar absence" framing for the _specific_ case where
  league_id truly is unresolvable, but makes the shard visible + re-attemptable instead of silently lost.
- **B**: Thread real `league_id` context down to these two call sites (it IS available on the tick-data parquet's own
  columns per the `_emit_status_for_shard`/`record_empty_for_shard` docstrings — "the fully typed per-(league,fixture)
  reason path is `reprocess_sports_odds` / `record_empty_for_shard`, which carries league_id from the parquet columns")
  so `classify_sports_empty_reason` can actually resolve a calendar-typed reason instead of always falling back to SRZ.
  More invasive (touches the tick-data → instrument-metadata plumbing in both files) but preserves the original intent.

## Status

Open — not yet triaged into an AO-dispatchable todo (bounded outcome unclear until the operator picks A vs B).

## Related escalations (crash root cause — finding 1, RESOLVED)

A second DP-VM-001 escalation (`agt-ccceda`, VM `mdps-backfill-sports-pipelinecheck-20260801-122555-2bf067`,
`deployment_id=d30a4ea2-5599-4c02-860c-53c82423af2f`, `exit_code=1`, date `2025-12-24`) hit the identical crash
signature (52/594 `odds_horizon_bucket` instruments logged "Unknown error") — a duplicate of the exact bug this doc's
finding 1 already root-caused and fixed (`market-data-processing-service@8358b9f`, confirmed on
`origin/live-defi-rollout`). This VM started at `12:25:55Z`, before the fix landed at `12:31:14Z`, so it ran pre-fix
code. **No relaunch performed**: the `mdps-backfill-sports-` prefix for date `2025-12-24` had already failed 4x today
(`110123`, `110907`, `114120`, `122555`), exceeding `rb_infra_relaunch.md`'s `≤2/(vm-prefix,day)` bound, and a recovery
run was already in flight for the same date (`mdps-backfill-sports-pcskip-20260801-130846-2bf067`,
`deployment_id=276fe963-2060-4a41-934e-d954f39c2409`, started `13:08:46Z` — after the fix — heartbeating fresh at
`13:19:28Z`). Finding 2 (the honest-absence `FetchEvidence` gate, this doc's main subject) is unaffected — it degrades
to a `WARNING` and does not crash the VM — and remains open pending the operator's A vs B call.
