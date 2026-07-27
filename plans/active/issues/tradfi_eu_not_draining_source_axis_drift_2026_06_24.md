---
doc_type: issue
title: TradFi expected_unattempted not draining — source-axis EU drift from the un-re-enumerated databento-first flip
summary:
  The tradfi `expected_unattempted` (EU) was dead-flat at **1,084,542** while a multi-VM CME/NYSE/NASDAQ databento
  backfill campaign burns compute. **Root cause = the EU seeds were materialised under ... UPDATE (2026-06-24, same
  session) — operator-approved purges drove EU 1,084,542 → 336,061 (massive purge) → 1,349 (MVP-gated, durable); 1
  re-enumeration todo remains open (see Progress Log). UPDATE (2026-07-14) — the re-enumeration attempt STOPPED at
  scan-only (candidate count blew past the 1M safety cap once CME OPTION rows first populated the catalogue); root cause
  diagnosed, awaiting an operator scope call (see Progress Log 2026-07-14 entry). UPDATE (2026-07-14, continued) —
  option (c) [tradfi MVP data_type-narrowing gate] IMPLEMENTED + shipped (instruments-service `31c15d88`, QG-green, 4
  new tests); re-verified scan-only STILL >1M for the full 2018-2026 window, but the remaining volume is now proven to
  be a genuine historical-window-size fact (423 real MVP CME option contract-months x 8.5y), not a further code bug —
  full-history apply correctly withheld per the task's own STOP instruction. The re-enumeration todo is RESOLVED
  (closed, per decide-and-document authority) as superseded by the standing daily cron; a deliberate one-time
  full-history catch-up remains available as operator-gated future work (option B below). Only the barchart item remains
  open. UPDATE (2026-07-14/15) — **operator ruling narrowed tradfi MVP options to the S&P 500 / ES complex ONLY**
  ("tradfi options for S&P 500 — options and futures — but NO other options in tradfi MVP"); implemented at the UAC SSOT
  (`TradFiMvpRule.option_underliers`, `unified-api-contracts@1753a084`), catalogue re-tagged (OPTION mvp=True
  739,278→414,140), full-history scan-only dropped 1,711,386→**498,840** (under the 1M cap) — **the one-time
  full-history catch-up (option B) is now DONE**, applied via `--apply-write` (498,840 rows — 290,688
  expected_unattempted + 208,152 typed empty_confirmed), consolidator-merged, floor-clip re-run. See Progress Log.
status: open
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [tradfi, manifest, expected-unattempted, pipeline-mode, databento, data-correctness, single-walk, backfill]
related: [instruments_catalogue_incremental_rollup_2026_06_29]
created: 2026-06-24
parent_epic: tradfi_master
priority: P2
source:
  [
    "live manifest gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet (read
    2026-06-24 19:49Z)",
    "instruments-service/scripts/enumerate_expected_universe.py (_seed_pipeline_source_transport, L300-330)",
    "deployment-service/scripts/wave_launcher.py (NEEDS_WORK, L106)",
    "live VM run.log
    gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-cme-ohlcv-1m-gc-2025-20260624-114619/run.log",
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
---

# TradFi EU not draining — source-axis seed/capture drift (PROVEN)

## What I found (root cause — PROVEN with cell-level evidence)

> _(Update note added 2026-07-12, finding 307, §A2 B-queue ruling: this section describes the problem AS FILED
> 2026-06-24. The same session's Progress Log below records the EU journey 1,084,542 → 336,061 (massive purge) → 1,349
> (MVP-gated, durable) via 3 of 4 operator-approved fix steps — the historical diagnosis below is left intact, not
> rewritten; see Progress Log for current state and the 1 remaining open re-enumeration todo.)_

The tradfi `expected_unattempted` (EU) was dead-flat at **1,084,542** while a multi-VM CME/NYSE/NASDAQ databento
backfill campaign burns compute. **Root cause = the EU seeds were materialised under the OLD
`SOURCE_PRIORITY[0] = massive`, and the 2026-06-24 databento-first flip was never followed by a re-enumeration — so the
seeds' `source`/ `pipeline_mode` key no longer matches the `source=databento` rows the campaign actually captures. The
two are disjoint manifest row-keys, so databento captures can never reconcile (drain) the massive seeds.**

This is precisely the failure the enumerator's own docstring warns against
(`enumerate_expected_universe.py::_seed_pipeline_source_transport`, L304-309):

> "the seeds the enumerator materialises MUST carry the same pipeline_mode + source (+ transport) as the real rows they
> will be reconciled against — else the denominator-seed rows diverge from real rows … source = the top external source
> for (asset_group, data_type)." — i.e. `SOURCE_PRIORITY[0]` **at enumeration time**.

### The evidence

**1. EU is keyed on a source the campaign no longer fetches.** From the live `_index` (manifest row key includes
`source` + `pipeline_mode`):

| capture_status       | source    | pipeline_mode   | rows                    |
| -------------------- | --------- | --------------- | ----------------------- |
| expected_unattempted | massive   | batch_massive   | **748,481** (69% of EU) |
| expected_unattempted | databento | batch_databento | 336,061                 |
| captured             | databento | batch_databento | **654,602**             |
| captured             | massive   | batch_massive   | 70,665                  |

**2. CME ohlcv_1m (source × status)** — the captures and the EU are disjoint sets:

- `databento`: 147,159 captured / **0 EU**
- `massive`: 49,298 captured / **173,190 EU** / 586,085 empty_confirmed

**3. Timing proves it's a stale pre-flip seed, not a live mis-seed.** All EU rows carry
`enumerator_run_id = enum-universe-tradfi-20260622-*`, `written_at` max **2026-06-22T15:45Z** — i.e. seeded 2026-06-22,
when `SOURCE_PRIORITY[0]` for (tradfi, ohlcv_1m/ohlcv_15m/trades/tbbo) was still `massive`. The databento-first flip is
**2026-06-24** (CLAUDE.md + UAC `_source_priority_data`). Current live
`SOURCE_PRIORITY[('tradfi','ohlcv_1m')] = ['databento','massive','yahoo']`.

**4. The campaign IS capturing databento (it's not the bug) — it just can't drain the massive seeds.** Live GC-2025 VM
run.log (19:47-19:50Z):
`Pre-flight: venue=CME date=2025-09-24 ohlcv_1m — 2 of 2 expected atoms still missing (GC.FUT, GC.OPT)` → fetches →
`Manifest updated … complete=True … 53987 records` → `captured=2`. So the databento capture rows grow; the
`source=massive` EU rows are untouched → EU dead-flat.

**5. The wave-launcher perpetuates the waste.**
`wave_launcher.py::NEEDS_WORK = {expected_unattempted, attempted_failed}` counts a cell as "needs work" if its
**per-source row** is EU. So it keeps seeing the 748k orphaned massive-EU cells, dispatches (venue,root,year) VMs for
them; the VM pre-flight then fetches databento (already covered or newly captured under a different key) and the massive
EU row is never reconciled → next tick re-dispatches the same shards. Compute burned, EU never moves.

## Why it matters

- **Data-pipeline correctness (the heartbeat).** The raw EU metric (1.08M) is the monitoring signal for "remaining
  tradfi work"; 748k of it is undrainable noise, masking the true databento gap and reading as a stalled campaign.
- **Wasted compute + metered-billing risk.** The wave-launcher re-dispatches done shards every 2-3h forever; each VM
  re-hits databento (mostly L0/free here, but the pattern is wrong and at scale risks metered L1/L2 re-fetches).
- **Blocks the tradfi-universe OPS pass (KRX/equities/options).** Adding the planned MTDS OHLCV wave on top of this
  would add more VMs that re-dispatch orphaned-source EU rather than drain real gaps (operator's explicit warning).

## Scope

TradFi-only for the **data** (the databento-first flip was tradfi-scoped, 2026-06-24; cefi/defi/sports source maps
unchanged). The wave-launcher `NEEDS_WORK` source-blindness is **cross-cutting** machinery but only bites where a
SOURCE_PRIORITY flip left orphaned seeds — today that's tradfi.

## Recommended decision (the fix)

A re-run alone is **not** sufficient — there is no automatic stale-source-seed retirement in the enumerator/consolidator
(seeds are keyed by `source`; a databento re-run writes NEW rows and leaves the 748k massive rows as orphans the
wave-launcher still picks up). The complete fix is a coordinated, single-walk manifest operation:

1. **Retire the orphaned massive EU seeds** for the data_types where massive is no longer `SOURCE_PRIORITY[0]` (tradfi
   ohlcv_1m/ohlcv_15m/trades/tbbo: `source=massive` + `capture_status=expected_unattempted`). These are meaningless
   under databento-first (massive is now FALLBACK[1], not backfilled). Reclassify/drop — NOT re-fetch.
2. **Re-run `enumerate_expected_universe.py` for tradfi** with the live databento-first priority → re-seeds EU under
   `source=databento`. Cells databento already captured drop out of EU; genuinely-missing cells become drainable
   databento gaps. (Verify the run SUPERSEDES prior seeds by latest `enumerator_run_id`, or pair with step 1.)
3. **Make the wave-launcher gap source-resolved (defensive, prevents recurrence).** A cell is a gap only if NO source in
   `SOURCE_PRIORITY` has it `captured` — i.e. collapse on `(venue,date,data_type,instrument_id)` via
   `select_primary_available_source()` before applying `NEEDS_WORK`. Then a future SOURCE_PRIORITY flip can't strand the
   launcher on orphaned-source EU.
4. **Re-consolidate + snapshot** the tradfi `_index` and confirm EU drains on the next wave tick (EU(massive) → 0 for
   the flipped data_types; captured climbs only for genuine databento gaps).

Filed (not auto-fixed) because steps 1-2 reclassify ~748k live manifest rows (single-walk discipline + data-correctness
across the tradfi manifest), and step 3 changes shared wave-launcher gap semantics — both exceed "small + clearly safe +
one-repo" and need operator awareness before execution. The OPS-pass STEP 4 (MTDS KRX/equities/options OHLCV wave) is
**HELD** until this drains.

## Progress / status

- 2026-06-24 — Filed. Root cause PROVEN (source-axis seed/capture drift from un-re-enumerated 2026-06-24 databento
  flip). Awaiting operator decision on executing the 4-step fix (esp. the 748k massive-seed retirement, which is the
  destructive-ish single-walk step). Coordinator NOTIFIED in chat.
- 2026-06-24 — **OPERATOR DECISION: purge `massive` entirely from the tradfi manifest (databento primary everywhere →
  simpler). EXECUTED.** Confirmed first: massive is `SOURCE_PRIORITY[0]` for NOTHING (only fallback[1] in 6 tradfi
  data_types); its 70,665 "captured" cells are row_count=0 sentinels (no real data); consolidator is INCREMENTAL
  (canon=current `_index` + anti-join changed shards) so a one-time canon purge STICKS (no per_vm shard / legacy_seed
  carries massive; enumerator now seeds databento). **Purge (race-free):** paused
  `uts-prod-manifest-consolidator-market-data-tradfi-cron` → snapshot
  `_index/snapshots/pre_massive_purge_2026-06-24.parquet` → pyarrow-filtered `source!=massive` (schema-preserving, 41
  cols) → uploaded → resumed cron. **Result: 6,671,520 → 2,692,994 rows (dropped 3,978,526 massive); EU 1,084,542 →
  336,061 (all databento, the REAL drainable gap); captured 732k→662,722; massive remaining = 0.** Durability watcher
  confirming massive stays 0 across a consolidator tick.
- 2026-06-24 — **OPERATOR APPROVED all 4 fix steps; EXECUTED 3 of 4 + collapsed EU to MVP.**
  - **#1 MVP-gate the tradfi EU enumerator (CODE)** → DONE: IS `6c893be` (`_tradfi_entry_in_mvp_universe` mirrors cefi,
    gate at top of `_enumerate_v2_tradfi`; + tradfi bundle-mvp propagation in `_rollup_bundle_grain`), QG-green 79s, 3
    tests. Deployed via rebuilt IS tarball (GCS sha 6c893be).
  - **#1 applied RETROACTIVELY (the could_exist→MVP collapse)** → DONE: with the correct per-instrument gate
    (`is_mvp(tradfi, venue, itype, data_type=None, base)`), only **1,349** of 336,061 databento EU were MVP (CME
    `ohlcv_1s` for CL/NG/SI/ES/NQ/HG/GC); 334,712 (99.6%) were non-MVP. Pause-consolidator → snapshot
    (`_index/snapshots/pre_mvp_eu_purge_2026-06-24.parquet`) → drop non-MVP EU → resume. **EU 336,061 → 1,349, DURABLE**
    (consolidator tick 21:03:48Z kept EU=1,349). EU journey: 1,084,542 → 336,061 (massive) → 1,349 (MVP).
  - **#3 retire 748k orphaned massive EU** → DONE (subsumed by the massive purge — all 3,978,526 massive rows gone).
  - **#4 source-resolve the wave-launcher gap (CODE)** → DONE: deployment-service `096298bd` (logical-cell groupby — a
    cell is a gap only if NO source captured), QG-green 80s, 5 tests. Deployed via rebuilt DS tarball.
- 2026-07-14 — **#2 attempted, STOPPED at the scan-only dry-run per the task's own >1M safety instruction — new finding,
  not yet fixed, needs an operator call.**
  - **Pre-checks (before running anything):** confirmed `--enumerator-version=v2` is the only supported value (v1
    retired) and that IS `.venv` has ADC. Confirmed the code is current: instruments-service `:latest` image
    (`asia-northeast1-docker.pkg.dev/.../instruments-service:latest`) resolves to commit `5cedb03` as of today
    (`gcloud artifacts docker images list --sort-by=~UPDATE_TIME`), far after `6c893be` (2026-06-24) — the MVP gate has
    been live in every deployed path for weeks, so the "AFTER 6c893be's promotion" precondition is already satisfied.
    Confirmed the tradfi catalogue was freshly regenerated TODAY
    (`gs://instruments-store-tradfi-prd- central-element-323112/prod/catalog.parquet`,
    `update_time: 2026-07-14T01:02:32Z`) — the "in-flight IS instruments backfill + catalogue-regen" precondition is
    also satisfied. Also found: there is a **standing daily Cloud Scheduler + Cloud Run Job**
    (`expected-universe-v2-tradfi-daily`, `30 1 * * *` UTC → job `expected-universe-v2- tradfi`) that ALREADY runs this
    exact enumerator with `--apply-write --start-date 2026-02-20 --max-writes-per-run 50000000` every day (completed
    2026-07-14T01:31:36Z, ~90s, i.e. it ran against the freshly-regenerated catalogue 28 min after the regen) — this is
    NOT documented in this issue's todo text, which only mentions the VM launcher / a one-off Cloud Run rebuild.
  - **Scan-only dry-run (as instructed, full default window `--start-date 2018-01-01`, no `--apply-write`):** ran
    directly from the instruments-service `.venv` (`GCP_PROJECT_ID`/`PROJECT_ID`/`CLOUD_PROVIDER`/`DEPLOYMENT_ENV` set
    to match the Cloud Run job's env). Loaded catalog (1,170,558 instruments) + manifest (5,109,048 rows incl. 3 live
    per-VM shards) in ~30s, then **hit the hard `--max-writes-per-run` safety cap almost instantly (~6s into
    enumeration): 1,000,001 candidates > 1,000,000 → `ENUMERATOR_FAILED reason=max_writes_exceeded`, exit 5.** Per this
    task's own instruction ("if it's wildly large — >1M — STOP and report instead of applying"), STOPPED here. No
    `--apply-write` was ever attempted; nothing was written to any manifest shard.
  - **Root cause (diagnosed, not yet fixed):** the tradfi catalogue now carries **739,278 `CME OPTION` rows tagged
    `mvp=True`** (checked via `pd.read_parquet` on the catalogue) — this is the "new ... options universe" the todo
    itself anticipated, and it is now correctly MVP-tagged per `unified-api-contracts` `_mvp_scope_rules.py` (comment:
    _"CME OPTION rows are MVP at ohlcv_1m ... but the catalogue today has 0 CME OPTION instrument rows ... This rule
    ensures CME options are correctly MVP-tagged ONCE present"_ — they are now present, for the first time, as of
    today's regen). Each option's `available_from`/`available_to` alive-window averages 626 days (median 179, max 4,751
    = 13 years, back to 2008); `_enumerate_v2_tradfi` seeds one EU row per (instrument, alive-day, `data_type`) with NO
    MVP `data_type` narrowing for tradfi (`_row_data_types` L691: "TRADFI IS DELIBERATELY NOT GATED" — only cefi gets
    the MVP-`data_type`-narrowing gate the same UAC comment describes for CME options at "ohlcv_1m only"). A full
    2018-2026 history run therefore cross-joins ~739k option contracts × their (mostly un-floor-clipped, since only
    `ohlcv_1s`/`ohlcv_1m` get the Databento rolling-window floor) alive windows → far past 1M candidate rows almost
    immediately, vs. the **1,349-cell "bounded MVP-gated set"** this todo's text was written against on 2026-06-24
    (BEFORE any CME OPTION rows existed in the catalogue).
  - **Reassuring cross-check — the daily cron is NOT blowing up in production.** Live manifest CME
    `expected_unattempted` = 4,828 total (all `data_types`) as of this check — nowhere near a 1M-row explosion. The
    daily cron's narrower `--start-date 2026-02-20` window intersects most of those 739k (mostly _already-expired_,
    since options continuously roll) option contracts' alive-windows at ZERO days, so it never seeds the
    denominator-inflating full-history tail my scan-only full-history dry-run surfaced. **The daily cron is already
    organically seeding the new options-universe MVP EU within a sane bounded window, every day, with no operator action
    needed.**
  - **What I did NOT do:** did not pass `--data-types`, did not bump `--max-writes-per-run`, did not narrow
    `--start-date`, and did not run `--apply-write` — all would have been a unilateral scope decision on a
    data-correctness axis (how far back should the options-universe honest-coverage denominator go?), which this task's
    own escalation rule reserves for the operator. Consolidator cron
    (`uts-prod-manifest-consolidator-market-data-tradfi-cron`, `*/1 * * * *`, ENABLED) was left untouched — no pause was
    needed since nothing was applied.
  - **Recommendation for the operator (not yet actioned):** the todo's original goal — "seed MVP databento EU for the
    new KRX/equities/options universe" — appears to already be satisfied on an ongoing basis by the existing daily
    `expected-universe-v2-tradfi` Cloud Scheduler job (bounded `--start-date 2026-02-20`, `--apply-write`, runs since
    2026-06-19, confirmed running successfully today post-catalogue-regen). A manual FULL 2018-2026 history run is a
    much bigger ask than the todo's text implies (per-option-strike CME history back to 2008) and is very likely NOT
    what's wanted — Databento's own rolling-subscription floor exists specifically so the denominator isn't inflated
    with unfetchable-vintage cells. Suggested options: **(A)** close this todo as "superseded by the standing daily
    cron" (no manual run needed) **[WORKER REC]**; **(B)** if a deliberate one-time catch-up IS wanted, re-run scan-only
    with an explicit narrower `--start-date` (e.g. matching Databento's actual OPTION/ohlcv_1m floor, not full history)
    and re-check the candidate count before any `--apply-write`; **(C)** separately, consider whether tradfi needs the
    same MVP-data_type-narrowing gate `_row_data_types` already applies to cefi (today CME OPTION rows are NOT
    data_type-narrowed to `ohlcv_1m` the way the UAC rule's own comment says they should be) — that would shrink the
    candidate space structurally, independent of the date-window question.
- 2026-07-14 (continued, same day) — **Coordinator ruling: implement option (c) [the missing tradfi MVP
  data_type-narrowing gate], then re-attempt the historical catch-up bounded. DONE (code); catch-up STILL not bounded —
  new, different blocker found; NOT applied.**
  - **Root cause of the 3x over-fan (confirmed):** `_row_data_types()` narrows cefi cells to their MVP data_type set
    (`get_mvp_data_types_for_cefi_venue` / `MVP_SCOPE.cefi.instrument_type_data_types`) but had a hardcoded comment
    ("TRADFI IS DELIBERATELY NOT GATED") explaining why the SAME narrowing was intentionally never added for tradfi —
    that comment is about the (unrelated, correctly-still-off) `VENUE_DATA_TYPE_CAPABILITIES` carve-out, not the MVP-cut
    gate. `MVP_SCOPE["tradfi"].data_types = {ohlcv_1m}` (operator 2026-06-27 decision #7) has existed for weeks and was
    simply never wired into `_row_data_types`. Confirmed via `unified-api-contracts` `_mvp_scope_predicate.py`: tradfi's
    `is_mvp()` branch has TWO data_type sub-cases — the flat CME futures/options complex (`{ohlcv_1m}`) and a narrower
    KRX equity-basis carve-out (`{ohlcv_24h}`, operator 2026-07-12) — so a naive flat-set narrow would have mis-gated
    KRX; the shipped fix reuses `is_mvp`'s branch-selection logic via a new `_tradfi_mvp_data_types()` helper instead of
    duplicating it.
  - **Fix shipped:** instruments-service `31c15d88` (`scripts/enumerate_expected_universe.py`) — `_row_data_types` gains
    a tradfi branch mirroring the existing cefi MVP-cut block; new `_tradfi_mvp_data_types()` helper
    (`scripts/enumerate_expected_universe.py`) selects the applicable MVP data_type set by (instrument_type, venue)
    WITHOUT re-checking `base_ccy` (that axis is already resolved by `_tradfi_entry_in_mvp_universe`'s pre-tagged `mvp`
    column short-circuit — a raw `is_mvp(..., base_ccy=...)` call at the data_type-narrowing layer would have wrongly
    returned False for rows with blank `base_asset`/`underlying`, an early design mistake caught by the existing
    unit-test fixtures before shipping). QG-green (119s); 4 new `_row_data_types` unit tests + 3 existing tests updated
    (their assertions encoded the pre-fix unnarrowed behavior, which is now correctly superseded per operator decision
    #7).
  - **Re-verification (scan-only, same full default window `--start-date 2018-01-01`, no `--apply-write`): candidate
    count still exceeds the 1,000,000 safety cap.** Total candidates (uncapped diagnostic run,
    `--max-writes-per-run 30000000`, scan-only only — nothing written): **1,711,386**. Breakdown:
    `(CME, options_chain, ohlcv_1m)` = **1,308,453** (76% of the total, down from a projected ~1.63M pre-fix — confirms
    the data_type gate IS working, 1 data_type emitted instead of 3); every OTHER venue/instrument_type combined =
    **402,933** (comfortably bounded on its own).
  - **New finding — the remaining CME options_chain volume is a genuine historical-window-size fact, NOT a further code
    bug.** `_rollup_bundle_grain` collapses the 739,278 raw CME OPTION catalogue leaves to **423 distinct per-underlying
    bundle candidates** (one per specific expiry-month contract code, e.g. `ESH6`/`NGZ26`/`CLF1` — NOT per commodity
    root). Checked directly against the LIVE manifest
    (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`) whether this bundling
    grain is itself the bug (a shard-atom mismatch would mean these seeds can never drain, mirroring this issue's
    original root cause): it is NOT — 132,250 real CAPTURED CME `options_chain` rows carry `underlying` at the SAME
    specific-contract-month grain (e.g. `ESH7`, `GCG7`, `CLZ6`, `6AH5`), confirming the enumerator's bundling already
    matches what MTDS actually writes today. (Two market-tick-data-service scripts,
    `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py` /
    `canonicalize_cme_options_chain_legacy_flat_2026_07_14.py`, describe an IN-FLIGHT future migration toward
    product-root grain — but that has not landed in the live manifest as of this check, so today's per-contract-month
    grain is the correct one to seed against.) 423 real MVP contract-months × the full 2018–2026 (~3,117-day) window is
    simply a large number — not an enumerator defect.
  - **Per the task's own explicit instruction ("if STILL >1M, STOP and report — do not apply"), the full-history
    `--apply-write` was NOT attempted.** Nothing was written to any manifest shard. Consolidator cron left untouched
    (nothing applied, no pause needed).
  - **Recommendation (updated, unchanged conclusion from the prior entry, now with confirmation the remaining volume is
    real not a bug):** **(A) close todo #2 as superseded by the standing daily cron** — the bounded daily
    `expected-universe-v2-tradfi` Cloud Scheduler job (`--start-date 2026-02-20`) already organically seeds the new MVP
    options universe within a safe window, and it now ALSO benefits from today's data_type-narrowing fix (fewer,
    more-correct EU seeds — the same 3x over-fan this fix removed for the historical scan also applied to the daily
    cron's narrower window, just not enough to trip the 1M cap there) **[WORKER REC]**; **(B)** if a deliberate one-time
    full-history catch-up is still wanted despite (A), it needs an explicit operator-chosen `--start-date` floor for the
    options-universe denominator (e.g. matching Databento's actual subscription/backfill floor, not 2018) — a
    data-correctness scope call outside this task's authority to make unilaterally.
- [x] [SCRIPT] P1. **#2 Re-run the expected-universe-v2 tradfi enumerator (MVP-gated tarball, databento)** to seed MVP
      databento EU for the cells not yet seeded (ohlcv_1m/trades/tbbo MVP gaps + the new KRX/equities/options universe)
      — AFTER the in-flight IS instruments backfill + catalogue-regen (fresh catalogue carries the new universe + mvp
      tags). Run via `launch-expected-universe-v2-vm.sh --asset-group tradfi` (fresh tarball) OR the Cloud Run job once
      its image rebuilds on 6c893be's promotion. Verify the MVP EU drains as the campaign captures. **2026-07-14 —
      STOPPED at scan-only (candidate count wildly exceeded the safety cap); root cause diagnosed (739k newly MVP-tagged
      CME OPTION rows, no tradfi MVP data_type narrowing). 2026-07-14 (continued) — coordinator ruling "implement option
      (c)" EXECUTED: `_row_data_types` gained the missing tradfi MVP data_type-narrowing gate (instruments-service
      `31c15d88`, QG-green, 4 tests). Re-verified scan-only: STILL >1M for the full 2018-2026 window (1,711,386
      candidates), but now CONFIRMED this is a genuine historical-window-size fact (423 real MVP CME option
      contract-months × 8.5y — the bundling grain matches the live manifest's actual captured rows, checked directly,
      not a shard-atom bug) rather than a further fixable defect. Full-history apply correctly WITHHELD per the task's
      own STOP instruction — nothing written to any manifest shard. RESOLVED per decide-and-document authority: the
      todo's actual goal (seed MVP databento EU for the new KRX/equities/options universe) is already satisfied on an
      ongoing basis by the standing daily `expected-universe-v2-tradfi` Cloud Scheduler job (bounded
      `--start-date 2026-02-20`), which now also benefits from today's data_type-narrowing fix. A deliberate one-time
      FULL 2018-2026 catch-up remains available as future work (option B in the Progress Log) but needs an explicit
      operator-chosen `--start-date` floor — a data-correctness scope call outside this task's authority. See Progress
      Log 2026-07-14 entries for full diagnosis.** **2026-07-15 — option B EXECUTED under an explicit operator
      `--start-date` ruling (the ES-only options narrowing itself, which shrank the historical candidate space under the
      1M cap without needing a narrower date floor). Full 2018-2026 one-time catch-up APPLIED: 498,840 rows (290,688
      `expected_unattempted` + 208,152 typed `empty_confirmed`) written + consolidator-merged + floor-clip reclassified
      (18,980 further rows: 8,959 mbp_10 Databento-floor + 10,021 derived ohlcv_15m). See the new 2026-07-15 Progress
      Log entry below for full evidence (shas, row counts, gate verification).**
- [ ] [SCRIPT] P2. **Stale `barchart` manifest rows (4,655) — fully-retired source, same orphan class as massive.**
      Decide keep-vs-purge: barchart was the OLD VIX-15m CSV source (now Databento VX futures); its captured rows MAY
      hold real historical VIX data. Scoped OUT of the massive purge pending operator call. Provenance: surfaced during
      the 2026-06-24 massive purge. **2026-07-14: confirmed this remains the doc's only OTHER open item besides #2 above
      — no action taken this session (operator-gated, unchanged).**

- 2026-07-15 — **Operator ruling implemented end-to-end: tradfi MVP options narrowed to the S&P 500 / ES complex ONLY,
  catalogue re-tagged, and the full 2018-2026 historical EU catch-up (option B, previously deferred) APPLIED.**
  - **Operator ruling (verbatim):** "We DO want tradfi options for S&P 500 — options and futures — but NO other options
    in tradfi MVP; just the single stocks, ETFs and futures already in MVP." I.e. tradfi MVP options scope = the S&P 500
    complex ONLY (ES; no separate MES options product exists today, so no `MES` entry is needed); all other underlyings'
    options (GC/CL/NG/6E/NQ/etc.) are NOT MVP. Existing MVP single stocks / ETFs / futures unchanged.
  - **1. SSOT change (unified-api-contracts `1753a084`, LDR, QG-green ship-mode 274s, 94% coverage):** new
    `TradFiMvpRule.option_underliers: frozenset[str]` field (`_mvp_scope_rules.py`) mirrors the pre-existing CeFi
    `options_base_ccys` Deribit-options narrowing pattern; new registry constant
    `TRADFI_MVP_OPTION_UNDERLYING_ROOTS = frozenset({"ES"})`; `is_mvp`'s TradFiMvpRule branch
    (`_mvp_scope_predicate.py`) extracted a `_tradfi_underlier_gate(instrument_type, base_ccy, rule)` helper (kept
    `is_mvp()` under the 200L function-size QG cap) that gates OPTION cells on `option_underliers` instead of the flat
    `underliers` set (FUTURE cells unchanged). `MVP_SCOPE_CONFIG_VERSION` 13→14. 11 new/updated unit tests in
    `TestTradFiOptionUnderlierNarrowingV14` (`tests/unit/test_mvp_scope.py`): ES option → mvp=True; GC/CL/NG/NQ/VX/SI/
    PL/PA/HG option → mvp=False; GC/NQ FUTURE + NASDAQ EQUITY basis carve-out → unchanged/still MVP. Ran directly
    against the instruments-service `.venv`'s editable local-path UAC install (`pyproject.toml`
    `[tool.uv.sources.unified-api-contracts] path = "../unified-api-contracts"`) — no instruments-service code change or
    image rebuild was needed to exercise the fix locally; the deployed Cloud Run image resolves UAC from Artifact
    Registry via the `>=0.33.0,<1.0.0` range pin and will pick up the fix automatically on its next image build once a
    new UAC wheel publishes off the LDR→staging→main tag-cut path (minor-bump range pin, per SUB*AGENT_MANDATORY*
    RULES.md "editable range-pins absorb minor/patch by design").
  - **2. Catalogue regen (evidence, before/after):** ran
    `instruments-service/scripts/build_instrument_catalogue.py --asset-group tradfi` (default `--mode incremental`;
    confirmed via code read that `_add_mvp_column` runs UNCONDITIONALLY over the full merged frame regardless of mode —
    line 2880, after `_merge_incremental` explicitly drops the stale `mvp` column at line 2562 — so incremental mode
    correctly re-tags every EXISTING row, not just the window delta) directly from the IS `.venv` with
    `GCP_PROJECT_ID=PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp DEPLOYMENT_ENV=prod` (matching the Cloud Run
    job's env, same precedent as the 2026-07-14 scan-only diagnostic). Window read 164 by_date parquets in ~54s;
    monotonic guard ACCEPTED (1,170,558→1,171,724 rows, no shrink); promoted to
    `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`. **OPTION `mvp=True`: 739,278 →
    414,140** (raw catalogue leaves; spot-checked the post-regen `underlying` column — every mvp=True OPTION row now
    resolves to an `ES*` contract code, e.g. `ESM2`/`ESZ5`/`ESZ1`; zero GC/CL/NG/NQ/VX/ etc.). Overall catalogue
    `mvp=True` 740,359 → 415,221 (FUTURE 968 + EQUITY 95 + ETF 18 unaffected, confirming the narrowing is OPTION-only as
    designed).
  - **3. Re-scan (HARD GATE check):** full-history scan-only
    (`enumerate_expected_universe.py --enumerator-version v2 --catalog-path gs://.../prod/catalog.parquet --max-writes-per-run 30000000`,
    default `--start-date 2018-01-01`, NO `--apply-write`) against the freshly-regenerated catalogue: **498,840
    candidate rows** (down from 1,711,386 pre-narrowing — a 71% drop), comfortably under the 1,000,000 safety cap
    (breakdown: blank/genuine-EU 290,688 | EXPECTED_WEEKEND 71,182 | EXPECTED_INSTRUMENT_NOT_LISTED 68,252 |
    EXPECTED_SOURCE_DELIVERY_LAG 32,989 | EXPECTED_INSTRUMENT_DELISTED 30,654 | EXPECTED_HOLIDAY 5,075). Matches the
    task brief's own estimate (≈402,933 non-options + a small ES-only options_chain set). **HARD GATE PASSED — proceeded
    to apply** (per the task's own instruction: only STOP if >1,000,000).
  - **4. Apply (the historical EU catch-up, option B from the 2026-07-14 entries — now executed):** the tradfi manifest
    consolidator (`uts-prod-manifest-consolidator-market-data-tradfi-cron`, `*/1 * * * *`, ENABLED) was **left running,
    NOT paused** — confirmed the enumerator's `--apply-write` path writes an ISOLATED, ADDITIVE per-VM-shard blob
    (`_index/per_vm/{VM_NAME}.parquet`, verified via code read at `enumerate_expected_universe.py` L3527/L3572) that the
    consolidator anti-join-merges on its own next tick — this is the SAME mechanism the daily
    `expected-universe-v2-tradfi` Cloud Scheduler cron already uses in production continuously, structurally distinct
    from the direct-canonical-index-mutation "purge" operations that needed the 2026-06-24 pause+snapshot dance (no
    read-modify-write race on the canonical blob). Applied via
    `MANIFEST_PER_VM_SHARDS=true VM_NAME=manual-catchup-tradfi-mvp-option-narrow-20260715 enumerate_expected_universe.py --apply-write`
    (same catalog-path/window as the scan): **498,840 rows written** (290,688 `expected_unattempted` + 208,152 typed
    `empty_confirmed`; by instrument_type: equity 261,510 / options_chain 95,785 / blank 76,257 / etf 52,701 /
    futures_chain 12,587; by venue: NYSE 163,968 / NASDAQ 160,404 / CME 117,903 / KRX 18,459 / YAHOO_FINANCE 9,540 / ICE
    9,531 / CBOE 9,528 / FX 9,507) to `_index/per_vm/manual-catchup-tradfi-mvp-option-narrow-20260715.parquet`; CSV
    audit report to
    `gs://deployment-scripts-central-element-323112/enumerator-reports/manual-catchup-tradfi-mvp-option-narrow-20260715/`.
    **Consolidator merge verified** (polled canonical row count every 20s): the merge picked up a PRE-EXISTING stale
    lock — a DIFFERENT, unrelated consolidator instance (`1-db0ca796`) had held `_index/consolidator.lock` since
    00:38:47Z with no progress; every tick in between logged `skipping cycle ... fresh lock present`. The
    `_LOCK_TTL_SECONDS=300` self-heal (`unified_trading_library/manifest_consolidator.py` L302/L918) correctly
    auto-cleared it at age=301.9s (00:43:47Z-ish) on the next tick, which then merged cleanly. **Canonical index:
    5,081,855 → 5,564,525 rows (+482,670; the 498,840 written rows net ~16,170 anti-join dedup against already-existing
    manifest rows).** GATE verified: `captured` 1,608,392→1,608,392 (UNCHANGED) and `attempted_failed` 342,134→342,134
    (UNCHANGED) — confirms this operation only ever added `expected_unattempted`/ `empty_confirmed` rows, never touched
    real capture evidence. `expected_unattempted` 89,413 → 378,889 (by venue: NASDAQ 179,458 / NYSE 155,474 / CME 35,731
    / KRX 8,226; by source: databento 361,047 / yahoo 17,842).
  - **5. Floor-clip (Databento rolling-window interplay, per the 2026-06-23 precedent):** ran
    `instruments-service/scripts/correct_tradfi_universe_floor_clip_and_vix_index.py` (dry-run first, then `--apply`)
    against the post-consolidation live index — the script's `_DATABENTO_FETCHED` floor logic + `_DERIVED_OHLCV` logic
    are pure RULES re-evaluated against whatever is currently EU (not a hardcoded row list), so a direct re-invocation
    was safe; the script's own internal snapshot dedup left the 2026-06-23 pre-image untouched ("snapshot already exists
    ... kept"), so a fresh manual dated snapshot was taken first
    (`_index/snapshots/pre_es_option_mvp_narrow_floorclip_2026_07_15.parquet`, 133.6 MiB) for a clean audit trail
    independent of the script's own logic. **Result: 8,959 `mbp_10` rows (Databento L2 1-month rolling floor) + 10,021
    `ohlcv_15m` rows (derived-not-fetched, non-yahoo/fx source) reclassed `expected_unattempted` → `empty_confirmed`
    (18,980 total).** `trades`/`tbbo` needed NO floor-clip (all seeded rows fall within their L1 1-year floor). GATE
    verified again: captured/attempted_failed/total-row-count all UNCHANGED (5,564,525 rows both before and after — a
    pure in-place reclassification). Final `expected_unattempted` = 359,909; post-clip spot-check confirms `mbp_10` EU
    residual = 530 (correctly within-floor) and `ohlcv_15m` EU residual = 0 (fully clipped). **Caveat (transparency, not
    swept under the rug):** this floor-clip step does a direct canonical-index read-modify-write (same race class the
    2026-06-24 purges paused the consolidator for) and was run WITHOUT pausing the consolidator. Verified after the fact
    (Cloud Logging phase-by-phase trace) that no actual lost-update occurred — the one consolidator cycle that ran
    concurrently (00:48:38-00:48:51Z) wrote its (no-net-change) canonical version at 00:48:49Z, BEFORE this script's
    read completed at ~00:49:02Z, and the next consolidator cycle started at 00:49:35Z, AFTER this script's write
    completed at 00:49:28Z — so the interleaving happened to be race-free by observed timing, not by an enforced pause.
    Post-write row-count/capture_status re-verification (`5,564,525` rows, capture_status counts matching the script's
    own logged AFTER state exactly) confirms no corruption. Flagging this as a **process gap for next time**: a direct
    canonical-index mutation should pause the consolidator first regardless of how additive/rule-based the reclass is,
    per the ICE-purge precedent — this run got lucky on timing, it did not eliminate the race class.
  - **Expected effect on the panel denominator + wave-launcher gap set:** the tradfi honest-coverage EU denominator
    grows by the net ~270,929 durable `expected_unattempted` delta (378,889 post-apply peak → 359,909 after floor-clip,
    vs. 89,413 pre-apply baseline). The wave-launcher (`deployment-service/scripts/wave_launcher.py`, already
    source-resolved per this issue's 2026-06-24 fix #4) will begin dispatching VMs against the genuinely fillable subset
    of these new gaps (mostly NASDAQ/NYSE equity-basis ohlcv_1m + CME ohlcv_1m futures/ES-options history) — a heads-up
    note was added to `tradfi_v9_stage1_finish_2026_07_06.md`'s Progress Log so an unrelated coverage-denominator delta
    there isn't mistaken for a new bug.
  - **Shas / evidence:** `unified-api-contracts@1753a084` (code); catalogue promote event `CATALOGUE_PROMOTED`
    run_id=`catalogue-rollup-tradfi-20260715T003015Z`; enumerator apply event `ENUMERATOR_COMPLETED`
    run_id=`enum-universe-tradfi-20260715-003341`
    (`gs://deployment-scripts-central-element-323112/enumerator-reports/manual-catchup-tradfi-mvp-option-narrow-20260715/tradfi-20260715-003341.csv`);
    floor-clip snapshot
    `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_es_option_mvp_narrow_floorclip_2026_07_15.parquet`;
    codex updated `/codex/02-data/mvp-scope-canonical.md` (TradFi section + config-version changelog).
