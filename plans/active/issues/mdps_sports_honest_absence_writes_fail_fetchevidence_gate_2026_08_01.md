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
source: [DP-VM-001 escalation agt-f5ddd4, agt-ccceda, agt-14585b]
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
   honest-absence gate (DP-FETCH-001, `/codex/05-infrastructure/data-pipeline-alerts.md`) hard-requires `FetchEvidence`
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

Open — finding 2's fix direction is not yet AO-dispatchable (bounded outcome unclear until the operator picks A vs B);
findings 3 and 4 have concrete bounded next steps, tracked as todos below.

## Todos

> Converted from prose 2026-08-02 by the `/plan-reconcile` whole-corpus run's zero-checkbox sweep — this doc carried
> zero `- [ ]`/`- [x]` lines, so all of the remaining work below was invisible to every mechanical check (open-todo
> counts, `regen_backlog_from_plan.py`, the orphan/NA audits). Register:
> [`/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md`](/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md).
> No new work was invented — each todo restates a "Recommended decision" / "Not yet done" item already written above.
> The doc is `execution_scope: local-only`, so these do NOT enter the AO backlog.

- [x] ✅ [OPERATOR] P2. **RULED 2026-08-02 (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md`
      na-eligibility-audit item 21), option A** — mirror the CEFI/DEFI/TRADFI fix: when `classify_sports_empty_reason`
      falls back to `SOURCE_RETURNED_ZERO`, route to `record_failed_for_shard` (shard becomes visible + re-attemptable;
      loses the "legitimate calendar absence" framing — accepted, matches the precedent already set for the other 3
      asset groups on 2026-06-22). Not option B (threading real `league_id` down both call sites) — more invasive,
      deferred. (repo: `market-data-processing-service`)
- [ ] [DATA] P2. **Implement the ruled option A above** in `live_workers_chain.py::_write_or_record_empty_timeframe` and
      `live_workers_streaming.py::_record_streaming_empty_timeframe` — route the `SOURCE_RETURNED_ZERO`-fallback case to
      `record_failed_for_shard` instead of `record_empty`, matching the CEFI/DEFI/TRADFI reference implementation
      (2026-06-22 operator decision). Done-when: a SPORTS honest-absence candle timeframe produces a real manifest row
      (not a `WARNING` + zero rows), proven on one re-run day. UNBLOCKED — ruling above resolved the A-vs-B gate. (repo:
      `market-data-processing-service`)
- [ ] [DIAG] P1. **Settle finding 4's `_collect_future_result` lead for the deterministic `~50/N "Unknown error"`
      crash.** Grep a failing VM's `run.log` for `❌ Exception processing` (specifically — the generic
      `Traceback|Exception` search already came back null twice) to catch the file-level exception
      `batch_workers.py:513` should log before the summary. Done-when: either that grep locates the raising frame, or it
      is null and `_process_instrument_file`'s full body + `_submit_instrument_file_tasks` have been read to find the
      raise whose `str(e)` is `""`. (repo: `market-data-processing-service`)
- [ ] [DIAG] P2. **Local repro against the known-bad instrument_ids** — e.g.
      `FOOTBALL:bovada:h2h:soccer_argentina_primera_division:2025/2026:Racing Club-Estudiantes::AWAY` for `2025-12-18`
      (finding 4) and `2025-12-24` (finding 3). Confirmed deterministic across ≥3 runs per date and reproducing on two
      independent dates, so a single local run settles it without more log archaeology. Done-when: the crash is
      reproduced locally and the raising frame is named. (repo: `market-data-processing-service`)
- [ ] [DIAG] P3. **Read `_streaming_filter_slice` / `_streaming_resolve_inst_info` line-by-line** (finding 3's residual)
      for a raise that stringifies to `""`; these two calls inside `_process_chain_bundle_streaming`'s per-symbol loop
      (`live_workers_streaming.py:777-823`) are NOT individually try/excepted, unlike
      `_streaming_process_slice_timeframes`. Done-when: either a candidate raise is named or both are confirmed
      raise-free. NOTE: finding 4 already DISCONFIRMED the "falling back to eager" half of this hypothesis (zero hits
      for that log string), so this is now the narrow residual, not the leading theory. (repo:
      `market-data-processing-service`)
- [ ] [SCRIPT] P3. **Do NOT relaunch `mdps-backfill-sports-` for `2025-12-24` / `2025-12-18` until the above lands** —
      the prefix has already failed 6x in one day against `rb_infra_relaunch.md`'s `≤2/(vm-prefix,day)` bound, and the
      crash is proven deterministic, so each further relaunch reproduces the identical `~50/N` failure and burns compute
      for zero new information. Done-when: the crash fix is verified, then exactly one relaunch confirms green. (repo:
      `deployment-service`)

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

## Finding 3 (NEW, open) — the streaming chain-bundle path has its OWN "Unknown error" crash, unfixed by 8358b9f

A THIRD DP-VM-001 escalation (`agt-14585b`) landed on VM `mdps-backfill-sports-pcskip-20260801-130846-2bf067`
(`deployment_id=276fe963-2060-4a41-934e-d954f39c2409`, `exit_code=1`, date `2025-12-24`) — the exact "recovery run
already in flight" VM finding 2's writeup expected to succeed (started `13:08:46Z`, well after the `8358b9f` fix at
`12:31:14Z`, and `origin/live-defi-rollout` HEAD at completion time — `0fc0448` — carries no further
`live_workers_streaming.py` changes past that fix). It did NOT succeed: it finished at `13:37:32Z` with the IDENTICAL
`52/594 odds_horizon_bucket` "Unknown error" signature as findings 1's pre-fix crashes, then
`Handler returned non-zero exit code: 1` and self-deleted.

**This proves `8358b9f` does not cover this crash path.** `8358b9f` fixed the `success` formula in the **non-streaming**
`_process_all_timeframes` path (`live_workers_chain.py` / `live_workers.py`, called for a file that either isn't chain
data or whose streaming dispatch declined/fell back). This VM's `run.log` shows every processed file going through
`"Chain-bundle streaming produced 0 candles for instrument_id=..."` — i.e. the **streaming**
`_process_chain_bundle_streaming` path (`live_workers_streaming.py`), which already computed `success=error_count==0` /
`error_message="; ".join(errors) if errors else None` since `1cdf3ecf` (2026-06-11) — long before today's fix and
unrelated to it. Confirmed no misclassification bug there: its honest-absence branch (`_streaming_write_per_tf`,
zero-candle timeframe) does `continue` without ever touching `errors`, so it cannot by itself flip `success` to `False`.

Yet 52/594 files DID end up `success=False` with `error_message` falsy enough that `process_handler.py:468`'s
`result.error_message or "Unknown error"` fell back to the literal string "Unknown error" (confirmed: the log's summary
block literally reads `[odds_horizon_bucket] <instrument_id>: Unknown error` for all 10 it prints in full,
`... and 42 more errors`). Every per-slice/per-write error-string constructor I traced in the streaming path
(`_streaming_process_slice_timeframes`'s `f"{group_value}@{tf}: {e}"`, `_streaming_write_one_group`'s
`f"write@{tf}: {write_error}"`) always produces a non-empty string even when `str(exception)` itself is empty (Python:
`str(SomeError())` with no args → `''`, but the f-string still carries the `group_value@tf: ` prefix) — so NONE of those
sites can produce a fully-empty `error_message` on their own.

**Leading hypothesis (not yet confirmed — needs a follow-up read + a repro, not a guessed fix):**
`_maybe_dispatch_chain_streaming` (`live_workers_streaming.py:196-250`) wraps the ENTIRE
`_process_chain_bundle_streaming` call in
`except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc: logger.error(...); return None` — a "defensive
fall-through to the eager path" documented in its own docstring. Two calls inside `_process_chain_bundle_streaming`'s
per-symbol `for` loop (`live_workers_streaming.py:777-823`) — `_streaming_filter_slice` and
`_streaming_resolve_inst_info` — are NOT individually try/excepted (unlike `_streaming_process_slice_timeframes`, which
is). If either raises for a specific match's slice, the exception propagates out of `_process_chain_bundle_streaming`
entirely, is swallowed by `_maybe_dispatch_chain_streaming`'s broad except (logged as a plain ERROR line — none of which
I could find in this VM's `run.log`, worth re-checking with `grep -i "falling back to eager"` on a fresh repro run since
I searched for `Traceback`/`Exception` generically, not this exact string), and the file falls through to
`live_workers.py`'s EAGER (non-streaming) path (`_read_tick_data` → `_process_all_timeframes`). That eager path does NOT
carry the `no_real_chain_root` / `_group_batches_by_own_type` per-instrument-type split that was added ONLY to the
streaming path (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 5's third bug) — so a sports `ticks.parquet`
bundle re-processed there may hit a DIFFERENT failure mode (or a bare exception whose `str()` really is empty) that
`_collect_future_result` (`batch_workers.py:507-521`) then surfaces as `error_message=str(e)` — empty when `e` itself
has no args — explaining the "Unknown error" fallback.

**Not yet done** (bounding this escalation's own effort — see below): grepping `run.log` for `"falling back to eager"`
to confirm the fallback actually fired for these 52 files (would prove the hypothesis directly); reading
`_streaming_filter_slice`/`_streaming_resolve_inst_info` line-by-line for a raise that could stringify to `""`; a local
repro against the 52 known-bad instrument_ids (listed in this VM's `run.log`, e.g.
`FOOTBALL:bovada:h2h:soccer_argentina_primera_division:2025/2026:Racing Club-Estudiantes::AWAY`) for date `2025-12-24`.

**Confirmed deterministic, not transient**: the exact `52/594` count and the exact same match/bookmaker set recur
identically across at least 3 separate VM runs today (`114120`, `122555`, `130846`) — this is a reproducible code
condition, not network flakiness, so relaunching will fail identically every time.

**No relaunch performed for `130846`'s failure.** The `mdps-backfill-sports-` prefix for date `2025-12-24` has now
failed **5x today** (`110123`, `110907`, `114120`, `122555`, `130846`), well past `rb_infra_relaunch.md`'s
`≤2/(vm-prefix,day)` bound, and per that runbook's own rule ("if it re-fails the SAME way twice, the shard is wedged...
STOP relaunching, file an issue") a 6th relaunch would almost certainly reproduce the identical 52/594 crash. This
finding stays `status: open` pending a follow-up read of `_maybe_dispatch_chain_streaming`'s fallback + the two
unguarded per-slice helper calls.

## Finding 4 (NEW, open) — reproduces on a DIFFERENT date too; "falling back to eager" hypothesis disconfirmed; new lead

A FOURTH DP-VM-001 escalation (`agt-b6e124`, VM `mdps-backfill-sports-pipelinecheck-20260801-134301-2bf067`,
`deployment_id=dc5c436b-e1fd-4977-bef5-d1f9dbb97294`, `exit_code=1`, `started_at=13:45:50Z`, well after both the
`8358b9f` fix (12:31:14Z) and finding 3's `130846` repro (finished 13:37:32Z)) hit the **identical crash signature on a
DIFFERENT date** — `2025-12-18` (all three prior finding-3 repros were `2025-12-24`): `50/638` `odds_horizon_bucket`
instruments logged `"Unknown error"` (breakdown: BOVADA 2/50, CORAL 2/38, FANDUEL 8/38, LADBROKES_UK 2/76, PINNACLE
10/73, SKYBET 6/37, UNIBET_UK 16/48, WILLIAMHILL 4/33 — the same bookmaker set finding 3 already implicated), then
`Handler returned non-zero exit code: 1` and self-deleted. This proves the bug is not date-specific — it is a structural
property of this data shape (H2H/spreads/totals odds_horizon_bucket markets for these 8 bookmakers), not a
`2025-12-24`-only artifact.

**"Falling back to eager" hypothesis (finding 3's leading hypothesis) — DISCONFIRMED for this run**: grepped this VM's
full `run.log` for `"falling back to eager"` (the exact string `_maybe_dispatch_chain_streaming` logs on its broad
except) — zero hits. The log DOES show 1176 `"Chain-bundle streaming produced 0 candles"` lines (streaming path ran
normally for many shards) and traced one specific failing instrument
(`FOOTBALL:bovada:h2h:soccer_argentina_primera_division:2025/2026:Racing Club-Estudiantes::AWAY`, one of the 50) start
in the EAGER path (`_write_or_record_empty_timeframe`, `live_workers_chain.py`) at `tf=15m`/`tf=1h` — its own
FetchEvidence-gate WARNING fires (finding 2's bug) but that path returns `(0, None, None)` for both timeframes, adding
nothing to `errors`, so `_run_adapter_and_write`'s `success = len(errors) == 0` (the `8358b9f` fix) should read
`success=True` for this instrument on its own accounting. Also re-verified BOTH honest-absence branches post-`8358b9f`:
`_write_or_record_empty_timeframe` (eager) and `_streaming_write_per_tf`'s zero-candle `continue` branch →
`_record_streaming_empty_timeframe` (streaming) neither one appends to `errors` — both are correctly excluded from the
failure tally. **Neither of the two known "success formula" call sites (`live_workers.py:444`,
`live_workers_streaming.py:856`) can produce this instrument's empty-`error_message` outcome from what I traced.**

**New concrete lead (not yet confirmed — the next cheap, bounded step)**: `batch_workers.py::_collect_future_result`
(lines 507-521, 493-537) wraps `future.result()` in
`except (OSError, ValueError, RuntimeError, KeyError, TypeError) as e: ... error_message=str(e)` (and a second, broader
`except Exception` branch, same shape). If the underlying exception was raised with NO message (e.g. `raise SomeError()`
with empty parens, or a custom `__str__`/`__repr__` override that can return `""`), `str(e)` is `""` —
`error_message=""` — which is exactly what reproduces `result.error_message or "Unknown error"` at
`process_handler.py:468` (the only other site that ever prints the literal string `"Unknown error"`; confirmed via
`grep -rn "Unknown error"` — no other candidate). This is a DIFFERENT code layer than either "success formula" (it fires
when the WHOLE per-file future raises, not when a per-timeframe/per-symbol accounting produces a non-zero-but-empty
error list) — consistent with `_collect_future_result`'s fallback `ProcessingResult(instrument_id= blob_path, ...)`,
i.e. `_process_instrument_file` itself is the thing raising, not a normal internal error-accumulation path. **Not yet
done**: (1) grep this VM's `run.log` for a bare `ERROR`/traceback line coinciding with each of the 50 timestamps (the
file-level exception, if this hypothesis is right, should log SOMETHING via `logger.error` at `_collect_future_result`
line 513 BEFORE the summary — re-check with `grep -n "❌ Exception processing"` specifically, not the generic
`Traceback|Exception` search finding 3 already ran and I re-ran with the same null result); (2) if that grep also comes
up empty, the exception is being raised+caught+message-lost somewhere BEFORE `_collect_future_result`'s own try (i.e.
inside `_process_instrument_file` itself, in a frame this analysis hasn't reached yet) — read
`_process_instrument_file`'s full body + `_submit_instrument_file_tasks` next; (3) a local repro against one of the 50
known-bad instrument_ids for `2025-12-18` would settle this definitively without more log archaeology.

**No relaunch performed for this VM's failure either.** The `mdps-backfill-sports-` prefix has now failed **6x today**
across two different target dates (`110123`, `110907`, `114120`, `122555`, `130846` for `2025-12-24`; this VM for
`2025-12-18`) — `rb_infra_relaunch.md`'s `≤2/(vm-prefix,day)` bound is read here as scoped to the VM-name prefix within
the CALENDAR day the relaunch decision is being made (not per-target-date), since the runbook's own bound-check language
is "≥2 relaunches of this prefix today"; even read narrowly per-target-date, `2025-12-18` has itself now failed once and
would need a second failure before the bound even engaged, but relaunching a CONFIRMED deterministic code bug (proven
above, now on a second independent date) would not surface new information — it would only reproduce the identical
`~50/N "Unknown error"` crash and burn compute. Escalation ping sent to the authoring slot per the
`data_pipeline_failure` role contract; this doc remains the tracking surface. Status stays `open`.

## Finding 5 (NEW, open) — `_build_candle_output_path` never asset-group-corrects `venue` for SPORTS when `input_venue` is truthy, causing `[partition_mismatch]` write rejects

A genuine from-scratch force+skip re-verification of `SPORTS:odds_horizon_bucket`
([`mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md`](/plans/archive/2026_08/mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md)
todo 4, day=2026-04-14 auto-day, VM `mdps-backfill-sports-pipelinecheck-20260803-080815-d0c755`, `EXIT_STATUS=1`, 84/90
instrument-timeframe cells succeeded, 6 genuinely failed) surfaced a distinct, previously-undocumented write-path bug —
NOT the `9642cbb` bucket-targeting fix's issue (this run's bucket paths were confirmed correct: both legs wrote to the
`--output-bucket` test bucket) and NOT findings 3/4's empty-message "Unknown error" crash (this bug's error message is
fully populated, so it is a different failure signature).

`run.log` shows repeated:

```
ERROR Error writing candles to GCS: StreamingParquetWriter pre-write validation failed: [partition_mismatch] 8 row(s)
inconsistent with partition_path 'day=2026-04-14/asset_group=sports/venue=FOOTBALL/instrument_type=MATCH_ODDS/
data_type=odds_horizon_bucket_15m': venue mismatch in
'FOOTBALL:SPORT888:MATCH_ODDS:SERIE_B:2026-27:US_CATANZARO_1929-MODENA::AWAY': partition declares FOOTBALL, id has
SPORT888; ...
```

Affected this run: SPORT888 + BETONLINEAG + CORAL (all on the `US_CATANZARO_1929-MODENA` match, different markets) and
UNIBET (`SOUTHAMPTON-BLACKBURN` match) — all 6 failed cells trace to the identical root: the partition path's `venue=`
segment is stamped `FOOTBALL` (the sport) while the row's own `instrument_id` carries the true bookmaker in its
BOOKMAKER position — the same "sport-token-as-venue" bug class already fixed once
(`sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2, via the asset-group-aware
`_venue_token_from_canonical_id(raw, asset_group=SPORTS)` helper in `canonical_writer_shaping.py`), recurring here in a
DIFFERENT call site that fix never reached.

**Root cause, precisely located**: `candle_write_mixin.py::_build_candle_output_path` (lines 258-306):

```python
venue = input_venue.upper() if input_venue else "UNKNOWN"
if venue == "UNKNOWN" and "instrument_id" in candles_df.columns and candles_df.height > 0:
    ...  # _venue_token_from_canonical_id(..., asset_group=category) correction
if venue == "UNKNOWN":
    venue = _venue_token_from_canonical_id(instrument_id, asset_group=category).upper()
```

The asset-group-aware `_venue_token_from_canonical_id` correction only fires when `venue` is still `"UNKNOWN"` after the
`input_venue` shortcut — i.e. only when `input_venue` was falsy to begin with. For SPORTS chain-bundle calls,
`input_venue` is the bundle's top-level sport token (`"FOOTBALL"`, non-empty), so the shortcut on line 286 wins and the
correction never runs. This is correct for every OTHER asset_group (venue really is one constant per file/bundle there)
but wrong for SPORTS, where each instrument within one chain-bundled match file can carry a DIFFERENT bookmaker as its
true "venue". Shared by BOTH write paths — `candle_write_mixin.py:187` (eager) and `live_workers_streaming.py:410`
(streaming chain-bundle) both call this same function — so this is not streaming-path-only like the bucket-targeting
bug.

**Fix**: gate the `input_venue` shortcut on `category != MarketAssetGroup.SPORTS` (or equivalently, run the
asset-group-aware `_venue_token_from_canonical_id(instrument_id, asset_group=category)` derivation unconditionally for
SPORTS before falling back to `input_venue`), mirroring how `_venue_token_from_canonical_id` and
`_resolve_empty_failed_shard_tuple` are already asset-group-gated elsewhere in this same file family.

**Possible connection to findings 3/4 (not confirmed, worth a cheap check before assuming independence)**: findings 3/4
hypothesize an unguarded raise producing a `str(e)==""` "Unknown error". This finding's validation error is fully
populated when logged directly at the write call site, so it is not itself the empty-message crash — but if some OTHER
caller catches the same `StreamingParquetWriter` validation exception without preserving `args`, it could explain a
subset of findings 3/4's `~50/N "Unknown error"` count. Not chased further here (outside this task's scope).

### Finding 5 todos

- [ ] [CODE] P2. In `candle_write_mixin.py::_build_candle_output_path`, gate the `input_venue.upper()` shortcut
      (line 286) on `category != MarketAssetGroup.SPORTS` so SPORTS always resolves `venue` via
      `_venue_token_from_canonical_id(instrument_id, asset_group=category)` regardless of whether `input_venue` is
      truthy. Done-when: a from-scratch `pipeline_e2e_check.py --asset-group SPORTS --data-types odds_horizon_bucket`
      force run against day=2026-04-14 produces 0 `[partition_mismatch]` rejects for the SPORT888/BETONLINEAG/CORAL
      (`US_CATANZARO_1929-MODENA`) and UNIBET (`SOUTHAMPTON-BLACKBURN`) cells (this finding's repro instruments). (repo:
      `market-data-processing-service`)
- [ ] [DIAG] P3. Grep a findings-3/4 VM's `run.log` (e.g. `130846`/`134301`) for `[partition_mismatch]` to check whether
      any of those 50-52 "Unknown error" instruments share this same venue-mismatch root cause, before assuming findings
      3/4 and finding 5 are fully independent. Done-when: either a shared root cause is confirmed (fold the findings) or
      the grep comes back empty (confirmed independent). (repo: `market-data-processing-service`)

## Progress Log

- **na-eligibility-audit 2026-08-02**: KEEP-NA, valid (sports tranche) — first verdict on this doc (created 2026-08-01,
  todos converted from prose by `/plan-reconcile` 2026-08-02, so it carried no prior marker). MIXED and left NA. All 6
  open todos accounted for: (1) the `[OPERATOR] P2` A-vs-B ruling is a genuine architecture decision — mirror the
  CEFI/DEFI/TRADFI `record_failed_for_shard` route vs. thread real `league_id` down to both call sites — whose outcome
  is NOT determinable by a worker alone (it trades the "legitimate calendar absence" framing against invasiveness), so
  it fails the dispatch-scope eligibility bar outright; (2) the `[DATA] P2` implementation todo is explicitly BLOCKED on
  that ruling; (3) the `[SCRIPT] P3` no-relaunch item is gated on the fix landing, and is a standing STOP against a
  prefix that has already burned 6 failed VMs in one day past `rb_infra_relaunch.md`'s `≤2/(vm-prefix,day)` bound; (4-6)
  the three `[DIAG]` todos (P1 `_collect_future_result` lead, P2 local repro, P3 `_streaming_filter_slice` read) are
  live-escalation crash debugging on an in-flight DP-VM-001 chain across 4 escalations — each carries a stated
  done-when, but they are the open half of an unresolved root-cause hunt, not settled bounded work, and the doc is
  `execution_scope: local-only` with its own conversion banner stating these do NOT enter the AO backlog. Escalated in
  this run's report as a parked `BLOCKED-OPERATOR-DECISION` (the A-vs-B call); no in-file retag, since the todo already
  carries the correct `[OPERATOR]` tag

- 2026-08-03 (slot-7, data_engineering): Added finding 5 while executing
  [`mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md`](/plans/archive/2026_08/mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md)
  todo 4 (re-verify SPORTS: odds_horizon_bucket force+skip after the bucket-targeting fix; that doc is now archived, all
  5 of its todos done). That re-verification succeeded on its own terms — bucket paths confirmed correct across 3
  attempts (2 SPOT-preempted, 1 genuine completion) — but the genuine completion's force leg hit a NEW, distinct bug:
  `[partition_mismatch]` write rejects for 6/90 cells, root-caused to `candle_write_mixin.py::_build_candle_output_path`
  never asset-group-correcting `venue` for SPORTS when `input_venue` is truthy. Filed here rather than a new doc since
  it lands in the exact function this doc's findings 3/4 already implicate. Did not fix inline (outside this task's
  scope; findings-closure HARD RULE).
