---
doc_type: issue
title:
  "is-daily-enum-sports historical-window backfill OOMs at Cloud Run's 32Gi/8cpu hard ceiling regardless of requested
  window size (5-day, 3-day, and 2-day windows all fail identically) — the durable chunked-scan fix
  (`is_daily_enum_capture_heal_2026_07_07.md`'s P2 follow-up) is now a genuine BLOCKER, not just a ceiling race"
summary: >-
  Attempting the is_daily_enum_capture_heal_2026_07_07.md remaining todo (backfill sports 2026-06-28..2026-07-02) via
  three separate real is-daily-enum-sports Cloud Run Job executions — a full 5-day window, then a split 3-day window,
  then a split 2-day window, ALL at 32Gi/8cpu (Cloud Run's documented hard ceiling for 8 CPU: "memory must be between
  4Gi and 32Gi inclusive") — every single execution failed identically with "The configured memory limit was reached."
  This rules out both memory-bump and window-narrowing as fixes: the routine DAILY cron (a 3-day TRAILING window ending
  today) succeeds reliably at just 8Gi (8 consecutive daily successes verified 07-19..07-26), but ANY HISTORICAL window
  — even 2 days — blows past 32Gi (4x the daily job's working memory). The memory cost is not proportional to requested
  day-count; it is specific to historical (non-trailing) enumeration requests. Real partial data DID land (per-shard
  writes happen incrementally before the eventual OOM) — 37,053 manifest rows across all 5 gap dates with plausible
  capture_status distributions — but expected_unattempted remains high (22-45% per day, worst on 06-30 at 45%), i.e.
  genuinely INCOMPLETE coverage, not a cosmetic exit-code mismatch.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [manifest, capture, oom, memory, is-daily-enum, cloud-run, backfill, sports, durable-fix]
related:
  [
    /plans/active/is_daily_enum_capture_heal_2026_07_07.md,
    /plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: instruments_master
source:
  ["Surfaced while executing is_daily_enum_capture_heal_2026_07_07.md's remaining backfill todo (slot-2, 2026-07-27)."]
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# is-daily-enum-sports historical backfill OOMs at the Cloud Run memory ceiling regardless of window size

## 1. What was attempted

`is_daily_enum_capture_heal_2026_07_07.md`'s remaining todo asks to backfill the missed sports window
(2026-06-28..2026-07-02, 5 days) once the daily job is healed (it is — verified green on 8 consecutive scheduled runs
07-19..07-26). Ran `is-daily-enum-sports` (the real Cloud Run Job, reused via a one-off `--args` override invoking
`instruments_service --operation instruments --mode batch --asset-group sports --start-date <> --end-date <> --force`
directly, bypassing the wrapper's relative `--days-back`) three times:

| attempt | window                                 | memory/cpu                                                                                                                                            | result                                                                           |
| ------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1       | 2026-06-28..2026-07-02 (5 days)        | 8Gi/4cpu → bumped mid-run to 32Gi/8cpu (execution `is-daily-enum-sports-56v2x`, started at 8Gi historical default, failed, re-launched fresh at 32Gi) | FAILED: "The configured memory limit was reached."                               |
| 2       | 2026-06-28..2026-06-30 (3 days, split) | 32Gi/8cpu (`is-daily-enum-sports-jbqx9`)                                                                                                              | FAILED: same message, after ~54 min                                              |
| 3       | 2026-07-01..2026-07-02 (2 days, split) | 32Gi/8cpu (`is-daily-enum-sports-fn2wz`)                                                                                                              | FAILED: same message, after ~92 min (used its 1 automatic Cloud Run retry first) |

`gcloud run jobs update is-daily-enum-sports --memory=64Gi --cpu=8` was attempted and REJECTED by Cloud Run itself:

```
ERROR: (gcloud.run.jobs.update) spec.template.spec.task_spec.containers[0].resources.limits.memory: Invalid value
specified for container memory. For 8.0 CPU, memory must be between 4Gi and 32Gi inclusive.
```

32Gi/8cpu is the documented hard ceiling for this configuration — there is no higher memory tier to bump to.

## 2. Why this rules out the "just needs more memory" / "just needs a smaller window" fixes

- **Not a memory-tier problem**: 32Gi is already 4x the 8Gi the exact same job's ROUTINE daily 3-day TRAILING window
  succeeds at (8 consecutive scheduled successes, `is-daily-enum-sports` executions 07-19 through 07-26, all
  `succeededCount=1`, all at the CURRENT live config of 8Gi/4cpu — confirmed via `gcloud run jobs executions list`
  before starting this backfill). There is no higher Cloud Run memory tier available at 8cpu.
- **Not a window-size problem**: a 3-day HISTORICAL window and a 2-day HISTORICAL window both fail identically at 32Gi —
  if memory scaled with requested day-count, the 2-day window should have needed roughly 2/3 the memory of the 3-day
  window and comfortably fit. It did not. This points to a FIXED, large memory cost specific to the historical
  (non-trailing) code path, not a per-day linear cost.
- **Prediction, by contrast, needed only a modest bump** (8Gi → 16Gi) for the SAME class of request (a 3-day historical
  window, `is-daily-enum-prediction-bjkxs`, succeeded cleanly at 16Gi in ~17 min) — confirming this is a sports-specific
  severity, consistent with the sports canonical index being far larger (~5-6.5GB per the
  `manifest_consolidator_dtype_at_source_fix` / `expected-universe-v2-sports` OOM history in
  `is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`) than prediction's (~25-28K rows).

## 3. Real (partial, honest) data that DID land

Cloud Run Jobs write incrementally per-shard; the manifest consolidator picks up new shard writes within ~1 min even
mid-run, so real data landed before each eventual OOM. Read via `read_availability_index` (column-projected,
`instruments-store-sports-prd-central-element-323112`) after all three attempts concluded:

| date       | captured | empty_confirmed | expected_unattempted | % unattempted |
| ---------- | -------- | --------------- | -------------------- | ------------- |
| 2026-06-28 | 867      | 5002            | 1647                 | 22%           |
| 2026-06-29 | 705      | 5033            | 1647                 | 22%           |
| 2026-06-30 | 216      | 3852            | 3308                 | **45%**       |
| 2026-07-01 | 719      | 5007            | 1667                 | 23%           |
| 2026-07-02 | 723      | 4996            | 1664                 | 23%           |

This satisfies the ORIGINAL todo's literal gate ("the exact day lists above show real (non-zero) manifest rows") but NOT
the "Data pipeline correctness is the heartbeat" hard rule's "fixed in FULL" bar — a real, measurable 22-45% slice of
the expected sports universe per gap day never got a capture attempt before the process died. 2026-06-30 is the worst
(45% unattempted) — it was in the FIRST 5-day attempt AND the split 3-day retry, and neither retry advanced its numbers
past whatever the very first attempt achieved before OOMing, suggesting the per-day processing order means later-OOMing
runs don't necessarily revisit earlier days.

## 4. Root-cause hypothesis (not yet confirmed by profiling)

`daily_is_enumeration.py` → `instruments_service --operation instruments --mode batch` likely needs to reconcile the
requested window against the FULL expected-universe + existing canonical index to correctly classify
captured/empty_confirmed/expected_unattempted (the same reconciliation `expected-universe-v2-sports` needed 16Gi for
even after the `instruments-service@633d7af4` memory-frugal column-projection fix — see
`is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`'s 2026-07-14 03:16Z entry). That fix explicitly
did NOT cover `daily_is_enumeration.py`'s own binary path ("NOTE: is-daily-enum-sports... is the SAME memory family but
a DIFFERENT binary path... its 13:30Z 32Gi verdict + the chunked-scan P2 remain open and are NOT addressed by this
ship"). For a TRAILING window ending today, this reconciliation is presumably cheap (recent dates, little existing
captured data to diff against); for a HISTORICAL window weeks in the past, the reconciliation surface is apparently much
larger — plausibly the FULL historical expected-universe + a wider existing-index read, independent of how many days are
actually requested (consistent with the "size doesn't scale down with fewer days" observation above). This needs real
profiling (`/usr/bin/time -v` against a local repro, or a memory-profiled Cloud Run execution) to confirm — not guessed
further here.

## 5. Recommended fix

The pre-existing P2 follow-up already flagged in `is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`
("Durable fix: bound memory in the prediction CLOB universe scan (chunked pagination → incremental manifest writes, no
full-universe accumulation); same review for the sports enum path.") is the correct fix — this finding UPGRADES its
priority from "ceiling race against universe growth" (a slow-motion future risk) to an ACTIVE BLOCKER: the sports
historical-backfill path cannot complete AT ALL today, at any Cloud Run-supported memory tier. Recommend:

- Profile `daily_is_enumeration.py --asset-group sports --start-date <hist> --end-date <hist>` locally with
  `/usr/bin/time -v` to find the actual peak-RSS driver (which step, which structure) before implementing a fix — don't
  guess at the chunking strategy blind.
- Once fixed, complete the sports backfill for the FULL 5-day window (2026-06-28..2026-07-02) using the exact
  `--start-date`/`--end-date` recipe in this doc (proven to reach the right dates; only the memory ceiling blocked it) —
  the residual gap is precisely the `expected_unattempted` rows tabulated in §3 above, re-measure after the fix lands
  rather than assuming a clean re-run reproduces the same partial numbers.

## 6. Open work

- [x] ✅ [CODE] P1. Profile `daily_is_enumeration.py`'s sports historical-window memory usage locally
      (`/usr/bin/time -v` against a real historical `--start-date`/`--end-date` window) to find the actual peak-RSS
      driver, then implement the durable chunked-scan / bounded-memory fix for the sports enum path (repo:
      instruments-service). This upgrades and supersedes the standing P2 note in
      `plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`. —
      instruments-service@5134a5f0. See Progress Log below for the profiling method + numbers.
- [ ] [VERIFY] P1. Once the durable fix lands, complete the sports backfill for 2026-06-28..2026-07-02 (the exact
      `--start-date`/`--end-date` args are proven correct in §1 above — only memory blocked it) and re-verify via
      `read_availability_index` that `expected_unattempted` drops to the same ~0-few-% baseline the healthy 07-03+ days
      show (repo: instruments-service).

## Progress Log

**2026-07-27 (slot-5)** — Profiled + fixed item 1 above.

Method: rather than reproducing the full 54-92min multi-day historical OOM locally (expensive, burns real API_FOOTBALL
quota, and the earlier §4 hypothesis already pointed at a specific reconciliation read), isolated + measured the exact
`read_availability_index(sports_bucket)` call the sports enum path's per-date pre-flight/ completeness stages make,
using `/usr/bin/time -v` against the REAL prod sports availability index
(`instruments-store-sports-prd-central-element-323112`, 6,755,574 rows × 42 cols).

Findings:

- Full-schema `read_availability_index(bucket)` (no `columns=`): **6.24 GiB peak RSS** per call
  (`Maximum resident set size: 6549776 kbytes`), ~11.0 GB deep pandas memory for the returned frame.
- Slim `columns=` read of the same data: 4.86 GiB peak RSS (`Maximum resident set size: 4857888 kbytes`) — the
  `_SLIM_MERGE_BASE_COLS` dedup-safety set still forces ~18 of 42 columns decoded, so this alone is a modest win.
- **Grep of every call site found 3 places doing the full unfiltered read on the sports enum path**:
  `process_preflight.py:_fixture_leagues_for_date` (once per run, cached),
  `process_completeness.py: _scope_sports_expected_venues` (once per date, NOT cached beyond the 60s `_INDEX_CACHE_TTL`
  — a multi-day historical run's per-date processing takes 18-46min per the §1 table, so this re-reads full-schema EVERY
  date), and `process_completeness.py:_detect_thin_day_venues` — CeFi-only by design (`_THIN_DAY_ABS_FLOOR` docstring:
  "never CeFi (sports days, etc.)") but called UNCONDITIONALLY from `_finalize_completeness` on every date of every
  asset-group run, including sports/tradfi/defi/prediction runs that can only ever find zero CeFi rows — i.e. a
  guaranteed-wasted full 6.2 GiB read on every single date of the reported historical backfill.

Fix shipped (`instruments-service@5134a5f0`):

1. `_fixture_leagues_for_date` + `_scope_sports_expected_venues` → `columns=["date","data_type","league_id"]` slim reads
   (only columns actually used).
2. `_finalize_completeness` now takes `asset_groups` and skips calling `_detect_thin_day_venues` (and its read) entirely
   when `"cefi" not in asset_groups` — eliminates the 100%-wasted full read on every date of every non-CeFi run.
   `_detect_thin_day_venues` itself also switched to a slim `columns=` read as defense-in-depth for the case a
   CeFi-inclusive ("ALL") run does reach it.

This removes the single biggest CONFIRMED per-date memory driver (`_detect_thin_day_venues`'s unconditional full read
was pure waste on every sports date) plus the two genuinely-needed sports reads' ~1.4 GiB/call overhead. It is NOT a
claim that this alone clears the full 32Gi ceiling on the actual multi-hour multi-day run — that can only be confirmed
by item 2 below (the real backfill re-run), which stays open. `basedpyright`/tests/`quality-gates.sh` all green;
targeted unit tests (`test_process_completeness_thin_day.py`, `test_silent_absent_fixes.py`) pass unchanged.

## 7. Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status` semantics.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — per-VM shard → consolidated index merge timing.
- `plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md` — the original OOM
  diagnosis + the standing (now-blocking) P2 durable-fix note this finding upgrades.
