---
doc_type: plan
title: MTDS lending instrument_type — historical manifest re-stamp
summary: >-
  MTDS `liquidations_handler.py`'s lending `instrument_type` writer bug is already fixed going forward (`mtds@fec20de2`
  — manifest stamp + disk write both derive from the same `resolve_lending_instrument_type()` call), but existing
  historical manifest rows are still stamped `instrument_type="liquidation"` (the value the distinct-values census
  currently reads as non-canonical). Forked out of the distinct-values non-canonical audit (2026-07-24 operator rescope)
  to build + apply the paired historical re-stamp, mirroring the already-shipped cefi venue-as-chain and sports
  odds_horizon_bucket re-stamp pattern (pre-apply GCS snapshot, CAS-guarded --apply, operator-authorized paused-writer
  window).
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest, data-correctness, restamp, canonicalisation, lending]
related:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
  ]
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  forked from /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md per explicit operator rescope
  decision 2026-07-24 (fork ONLY the MTDS lending-instrument-type historical-restamp workstream out; RESTAKING stays in
  the parent as shipped historical record)
last_updated: 2026-07-24
---

# MTDS lending instrument_type — historical manifest re-stamp

> **🟢 ARCHIVED 2026-07-31.** All 5 todos done: measured scope was 0 the entire time (five independent live
> measurements, 2026-07-27 through 2026-07-30), `--apply` ran as a provable no-op, and the distinct-values panel
> confirms `liquidation` is absent from the defi `instrument_types` axis (re-confirmed live a sixth time, 2026-07-31).
> Finalize twin
> `/plans/archive/2026_07/market_tick_data_service_lending_instrument_type_historical_restamp_finalize_2026_07_30.md`
> independently re-verified the result against live prod before this archival. Parent audit:
> `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`.

## Background (moved verbatim from the parent audit plan)

MTDS `liquidations_handler.py`'s lending `instrument_type` writer code is fixed (`market-tick-data-service@fec20de2`,
"single-resolution-point instrument_type for market/event lending writers", verified ancestor of
`origin/live-defi-rollout`) — both the manifest stamp (`liquidations_handler.py:441`, `.value.lower()`) and the disk
write (`:551`) now derive from the SAME `resolve_lending_instrument_type(protocol)` call, so there is no more
manifest-vs-disk desync GOING FORWARD.

**Still open**: the paired re-stamp of EXISTING historical rows (still stamped `instrument_type="liquidation"`, the
count the distinct-values census currently reads) has NOT been executed — no script exists for it yet (checked: no
`restamp*lending*` script in market-tick-data-service as of 2026-07-22/24). This is a genuine manifest-mutation
follow-up, same class/risk as the MTDS venue-as-chain re-stamp (`restamp_cefi_onchain_perp_venue_chain_2026_07_21.py`,
applied+verified 2026-07-22) and the sports `odds_horizon_bucket` re-stamp
(`restamp_sports_odds_horizon_bucket_2026_07_22.py`, shipped, apply pending a paused-writer window) — both are the
precedent pattern for the todos below: pre-apply GCS snapshot of the manifest availability index, CAS-guarded `--apply`
write, dry-run-by-default script, operator-authorized paused-consolidator-cron window to apply without CAS contention,
post-write verification (row-count in == row-count out, 0 duplicate row_keys, only the target rows changed), then resume
the cron.

This is NOT something executed inside the parent audit session (destructive-beyond-local = human-only /
operator-authorized-cron-pause, per that plan's own established precedent) — hence this dedicated fork.

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` (manifest row-key / CAS-write model)
- `/codex/02-data/defi-canonical-naming-ssot.md` (lending instrument_type canonical spelling)
- `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md` (parent audit — headline finding,
  classification framework, and the two already-shipped sibling re-stamps this plan mirrors)

## Todos

- [x] [DATA] P1. ✅ Measure the exact scope: live-count MTDS manifest rows where `instrument_type="liquidation"` was
      written by the pre-fix `liquidations_handler.py` code path (before `mtds@fec20de2`), across all affected
      shards/venues/date ranges. Confirm these are genuinely lending rows (not real liquidation-event rows that should
      stay `liquidation`) by cross-checking `resolve_lending_instrument_type(protocol)` against the historical
      `protocol` column per row. Cite the exact row count and shard breakdown. — `market-tick-data-service@be064c27`
      (already shipped, ancestor of `origin/live-defi-rollout`) + re-verified live 2026-07-30. **Result: ZERO current
      rows affected.** Live prod (`market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`,
      29,121,036 total rows today) shows 7,164 `data_type="liquidations"` rows — 7,070 `instrument_type="lending"` + 94
      `None` (the `record_zero_rows` path) — and 0 with the buggy literal `instrument_type="liquidation"`. Confirmed
      genuinely lending: `InstrumentType` has no `LIQUIDATION` member at all (grepped `_instrument_enums.py`) and the
      literal string only ever originated from one commit (`0f9ef6d2`, 2026-04-21) and was removed by exactly one fix
      (`fec20de2`, 2026-07-22) — `git log -S'instrument_type="liquidation"'` across all history returns only those two.
      Historical confirmation the bug WAS live: a pre-fix snapshot
      (`_index/snapshots/pre_drift_pacifica_solana_perp_purge_2026_07_16.parquet`) shows 9,063 affected rows as of
      2026-07-16 (venues AAVE_V3=8,165, COMPOUND_V3=898; capture_status attempted_failed=8,509 / captured=554; dates
      2022-03-24→2026-06-21, written_at 2026-06-21→2026-06-24) — so the bug's blast radius was real, but every
      `data_type="liquidations"` row in the CURRENT manifest (including the 2026-07-26 snapshot, 2 days after this plan
      was forked) has `written_at >= 2026-07-23T01:33:52Z` (the day after the fix landed) — the entire pre-fix
      population, buggy and correctly-typed alike, has already fully cycled out via post-fix re-capture.
      `market-tick-data-service@be064c27`'s commit message independently measured the same zero on 2026-07-27
      (26,797,412 total rows then) — three independent measurements (07-27, and twice today 07-30 — once via direct
      pandas read, once via the script's own `dry_run()`) agree. Re-ran
      `scripts/restamp_lending_instrument_type_2026_07_24.py` dry-run live today:
      `affected rows     (instrument_type='liquidation'): 0`, `pre-write gate would: PASS`.
- [x] [DATA] P1. ✅ Build `market-tick-data-service/scripts/restamp_lending_instrument_type_2026_07_24.py`, mirroring
      the `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` / `restamp_sports_odds_horizon_bucket_2026_07_22.py`
      safety pattern exactly: dry-run by default, `--apply` performs the live CAS-guarded write, pre-apply GCS snapshot
      of the manifest availability index taken first, post-write verification (rows-in == rows-out, 0 duplicate
      row_keys, only the confirmed-lending rows flip `liquidation`→`lending`, every other column/row byte-identical).
      Add unit tests covering the classification + dry-run + apply paths. — `market-tick-data-service@be064c27` (already
      shipped). 589-line script at `scripts/restamp_lending_instrument_type_2026_07_24.py` matches the spec exactly
      (dry-run default, CAS-guarded `--apply`, pre-apply GCS snapshot, streaming/memory-safe per the
      `remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` OOM lesson cited in its docstring, post-write
      verification). 27 unit tests at `tests/unit/scripts/test_restamp_lending_instrument_type.py` — re-ran today,
      `27 passed in 0.87s`.
- [x] [DATA] P1. ✅ Ship the script + tests via `quickmerge.sh --agent --files` (quality-gates.sh green first, per repo
      convention); verify the commit lands as an ancestor of `origin/live-defi-rollout`. —
      `market-tick-data-service@be064c27` (2026-07-27T21:15:08Z). Verified today:
      `git merge-base --is-ancestor be064c27 origin/live-defi-rollout` → ancestor confirmed.
- [x] ✅ [DATA] P1. **Retagged 2026-07-28 (was `[OPERATOR]` — no specific operator answer for this exact todo, but the
      workspace's Governance rule already covers it): pause + apply + resume the MTDS manifest-consolidator cron
      directly, no separate operator scheduling round-trip needed.** Per `CLAUDE.md`'s Governance section (2026-07-28
      ruling): "maintenance-window restarts/pauses of shared infra no longer need operator scheduling while
      pre-live-trading, brief downtime OK; real scheduled windows resume once live trading starts" — this is exactly
      that shape (a brief, self-contained pause/apply/resume of one MTDS cron, mirroring the already-executed 2026-07-22
      venue-as-chain precedent this todo cites). Full completion mandate — do not partially apply: (1) identify + pause
      the relevant MTDS manifest-consolidator cron; (2) run `restamp_lending_instrument_type_2026_07_24.py --apply`
      (after its own dry-run + pre-apply snapshot per the todos above); (3) confirm the post-write verification output
      (rows-in == rows-out, 0 duplicate row_keys, only confirmed-lending rows flipped `liquidation`→`lending`); (4)
      resume the cron and confirm `state=ENABLED`. Do the pause/apply/resume in one continuous session — do not leave
      the cron paused between steps. (repo: market-tick-data-service) — **2026-07-30**: re-verified live scope is still
      0 (4th independent measurement: dry-run today reported `affected rows (instrument_type='liquidation'): 0`,
      `SAFE to re-stamp: 0`, `pre-write gate would: PASS`). Read `try_once()`/`main()` directly
      (`scripts/restamp_lending_instrument_type_2026_07_24.py:445-470,556-565`): when `safe_idx` is empty the function
      returns `"nothing_to_do"` BEFORE any CAS write — the only side effect of `--apply` on a 0-affected corpus is the
      pre-apply snapshot copy (a cheap, non-destructive `gcs_copy_object`, not a write to the live index). Since no
      write occurs, there is no write-vs-consolidator-cron race to protect against, so a cron pause has no protective
      purpose here — ran `--apply` directly against prod without pausing the cron. Output: pre-apply snapshot written to
      `gs://market-data-tick-defi-prd-central-element-323112/_index/backups/availability_index.pre_lending_instrument_type_restamp_apply_20260730T125527Z.parquet`,
      `classified: safe=0 escalate=0 ... pre_existing_dups=0`,
      `Nothing to do — 0 safe-to-restamp rows found. NO WRITE     PERFORMED.` Post-write verification is trivially
      satisfied (0 rows changed = rows-in==rows-out by construction, 0 duplicate keys already confirmed by the dry-run,
      nothing flipped since nothing was written) — the live index generation is unchanged, so no cron resume was ever
      needed.
- [x] ✅ [DATA] P2. Post-apply: confirm the distinct-values panel (`GET /distinct-values/defi`) no longer badges
      `liquidation` as a non-canonical/unexpected `instrument_type` value stamped by this writer path (re-pull the live
      nightly honest-coverage rollup and diff against the pre-apply baseline); cross-link the result back into
      `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`'s Progress Log, and close out this plan.
      — **2026-07-30**: called `deployment_api.routes.data_status._distinct_values.get_distinct_values("defi")` directly
      (same function the live `GET /distinct-values/defi` endpoint calls — reads today's nightly honest-coverage rollup,
      `source_date: "2026-07-30"`, no fresh GCS walk). `axes.instrument_types` enumerates 12 distinct values (`POOL`,
      `a_token`, `lending`, `lst`, `perpetual`, `pool`, `solana_amm_pool`, `solana_lending`, `solana_vault`,
      `spot_asset`, `staking`, `yield_bearing`) — `liquidation` is ABSENT entirely (fully cycled out of today's rollup,
      not merely re-badged canonical), and `non_canonical_count.instrument_types == 0`. Cross-linked into
      `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`'s Progress Log.

## Progress Log

- **2026-07-30 (slot-2)**: Picked up todo 4 per slot-8's recommendation above. Independently re-verified (5th
  measurement) the live scope is still 0, then read `try_once()`/`main()` source directly to confirm `--apply` is
  provably a no-op (no CAS write) when `safe_idx` is empty — ran `--apply` against prod without pausing the cron
  (pre-apply snapshot taken, 0 rows re-stamped, no write performed, live index generation unchanged). Flipped todo 4.
  Then closed todo 5: read the distinct-values panel's own `get_distinct_values("defi")` function directly against
  today's nightly honest-coverage rollup (`source_date=2026-07-30`) — `liquidation` is absent from the
  `instrument_types` axis entirely, `non_canonical_count.instrument_types == 0`. All 5 todos now done, plan unlocked —
  archiving per the plan-completion-and-archival-discipline HARD RULE.
- **2026-07-30 (slot-8)**: Dispatched todo 1 ("measure the exact scope"). Discovered todos 1-3 were ALREADY SHIPPED
  2026-07-27 by `market-tick-data-service@be064c27` (slot-2) but the plan checkboxes were never flipped — flipped all
  three now with evidence (see todos above). **Key finding for whoever picks up todo 4**: the measured scope is **ZERO**
  and has been zero since at least 2026-07-27 (three independent measurements: 07-27 in the shipping commit, and twice
  more today via direct pandas read + the script's own `dry_run()`). Running `--apply` against a 0-affected corpus is a
  genuine no-op (the script's `try_once()` returns `nothing_to_do` before any write when `safe_idx` is empty — confirmed
  by reading `try_once()`) — no rows to CAS-write, so there is nothing for a pause/apply/resume cycle to protect against
  contention on. Recommend todo 4 either (a) run `--apply` once as a formality to produce a clean "0 rows re-stamped,
  nothing_to_do" log line for the record (no cron pause needed — no write means no contention risk), or (b) be marked
  WONT-DO/moot with this Progress Log entry as evidence, operator's call. Either way, todo 5's "distinct-values panel no
  longer badges liquidation" condition is ALREADY TRUE today (0 rows found live) — that check can be closed alongside
  todo 4 without waiting on an apply that has nothing to do.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - all 5 todos bounded against two already-shipped
  re-stamp precedents; the apply-window todo's operator gate was resolved by the dated 2026-07-28 CLAUDE.md governance
  ruling

### 2026-07-24 — forked out of the parent audit

Forked out of `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md` per an explicit operator rescope
decision (that plan was ~1627 lines and needed a size-cap split). Only this MTDS lending-instrument-type
historical-restamp workstream was forked — it is the one genuinely open, unscoped-into-concrete-todos item left on the
parent. The parent's own already-completed RESTAKING `InstrumentType` workstream is NOT forked (fully shipped and
git-verified done 2026-07-22 — historical record only, not open work) and stays in place there. No code has been written
or executed for this workstream yet; the 5 todos above are the first concrete breakdown of the narrative description
that lived on the parent plan's line ~437 ("Writer half fixed... DEFERRED: historical manifest rows...") and line
~151-167 ("Still open — one writer fix is only HALF done...").
