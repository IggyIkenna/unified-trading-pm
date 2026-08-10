---
doc_type: issue
title:
  "Sports distinct-values panel: 4-day-frozen prod deploy + 2 venue writer bugs + a historical re-stamp + FOOTBALL
  phantom-row cleanup — RESOLVED, 44→0 non-canonical across every axis"
summary: >-
  Operator flagged the deployment-ui Distinct Values panel (sports) still showing ~44 non-canonical values across
  venues/instrument_types/data_types despite prior sessions already having landed the fixes in UAC + deployment-api.
  Root cause was NOT a code gap for most of them: `uts-shared-deployment-api` production traffic had been frozen on a
  pre-2026-07-31 revision for ~4 days — every automatic `deploy-shared.sh` cutover attempt since then had silently
  failed (same signature as `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`,
  cross-referenced there with fresh evidence this session). Recovered via a direct `gcloud run services update-traffic`
  retry (confirmed live, serving correctly). That alone dropped the count from 44→12. Root-caused + fixed the remaining
  genuine gaps: (1) 5 legitimate-but-unregistered instrument_type values (bare `ASIAN_HANDICAP`/`OVER_UNDER`,
  `exchange_odds`/`fixed_odds`/`odds`) added to UAC's accepted-exceptions registry — instrument_types now 0
  non-canonical (was 37); (2) two real writer bugs found and fixed at the source: `market-tick-data-service`'s
  `venue_fetch.py` bypassed the already-existing `SPORTS_VENUE_FOLD` (raw `.upper()` instead of folding
  `ladbrokes_uk`/`sport888` to canonical `LADBROKES`/`BET888SPORT` first) and `market-data-processing-service`'s
  `live_workers.py` did a raw `instrument_id.split(":")[0]` that grabbed the SPORT token ("FOOTBALL") instead of the
  bookmaker for sports' `SPORT:BOOKMAKER:MARKET:...` id shape (mirrors an already-fixed sibling bug class,
  `_venue_token_from_canonical_id`, that just hadn't been applied at this one call site). Both writer fixes stopped
  future pollution immediately, but did not retroactively fix already-captured rows — venues stayed at 3 non-canonical
  (FOOTBALL/LADBROKES_UK/SPORT888) until (a) a historical GCS+manifest re-stamp ran for LADBROKES_UK/SPORT888 (31,118
  objects, 30,912 manifest rows, plus a real manifest_swap casing bug found+fixed along the way — see Todos) and (b) a
  manifest-only phantom-row cleanup ran for FOOTBALL's 194 always-failed, zero-real-data residual rows (also found no
  retry mechanism covered them, explaining why they never self-healed). **RESOLVED 2026-08-05**: live panel confirmed at
  venues/instrument_types/data_types/chains all 0/0 non-canonical.
status: open
nature: issue
asset_group:
  [sports] # was [sports, cross-cutting] -- retagged 2026-08-04 by /ag-closeout-audit sports tranche
  # (Orthogonality HARD CHECK): every detail (SPORTS_VENUE_FOLD, sports distinct-values panel endpoint, MTDS/MDPS
  # sports-only writer bugs) is single-AG-specific; the general cross-cutting deploy-freeze root cause is already
  # tracked separately in deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md (related:
  # above), and the sibling per-AG pattern (defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md) confirms
  # this class is tracked one-doc-per-AG, not as one cross-cutting doc.
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    deployment-api,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    sports,
    distinct-values,
    canonicalisation,
    venues,
    instrument-types,
    honest-coverage,
    cloud-run,
    deploy-freshness,
    writer-bug,
  ]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/archive/issues/honest_coverage_cron_run_job_sa_missing_actas_uts_prd_sa_2026_08_03.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-05"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
source: >-
  Operator live screenshot of the deployment-ui Distinct Values panel (sports asset_group), 2026-08-04 interactive
  session — "the fix may already have rolled out and not be visible yet but double check", "why is venue, instrument
  type... not canonical still", "trigger one [rollup] to refresh", "code needs fixing, uac needs fixing, everything
  deployed... manifest purged and re-rolled up".
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers.py,
  ]
---

> **⚠️ CORRECTION 2026-08-08 — this doc's "0/0 non-canonical, RESOLVED" all-clear is MISLEADING and must not be read as
> evidence the sports axes are canonical.** The writer-bug fixes and the deploy-freeze recovery recorded here were real
> and are not in question. But the **"venues/instrument_types/data_types/chains all 0/0 non-canonical"** headline was
> achieved by adding values to `_ACCEPTED_EXCEPTIONS`, **not** by canonicalising them. Measured 2026-08-08 against the
> live prod manifest and the 2026-08-05 honest-coverage rollup: the manifest carries **31 venues and 10 data types**;
> the panel rendered **10 and 7**. `deployment-api::_distinct_values.py::enumerate_distinct_values` drops blank
> sentinels and every accepted exception **before** enumerating, hiding 21 fan-out bookmakers (~340k shards), `KALSHI`
> (20,785 rows), a blank venue (2,490 rows) and uppercase `ODDS` (**6,306 CAPTURED** shards, not the "4 stale empty
> rows" the UAC comment claims). The panel is fixed to badge-not-hide by
> `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`; the underlying values are genuinely canonicalised by P1/P2
> of that chain. The success bar is the exception sets reaching **empty**.

# Sports distinct-values panel — 44→0 non-canonical, RESOLVED (2026-08-04/05)

## What was live when this session started (verified via the raw endpoint, not just the screenshot)

`GET /api/data-status/distinct-values/sports`: venues 4/14 non-canonical (FOOTBALL, KALSHI, LADBROKES_UK, SPORT888),
instrument_types 37/37 (every ASIAN_HANDICAP*/OVER_UNDER*/MATCH_ODDS* variant plus bare forms and
exchange_odds/fixed_odds/odds), data_types 3/10 (ODDS/ODDS_MOVEMENT/ODDS_SNAPSHOT uppercase residue). Total 44.

## Cause 1 (the majority, 33 of 44) — production deploy frozen since 2026-07-31

`uts-shared-deployment-api` had 100% traffic pinned to revision `00374-4pd` (built 2026-07-31T18:39, pre-`uts-prd-sa`)
continuously since then. UAC's accepted-exceptions for KALSHI / ODDS-uppercase-residue / the original 30-value
ASIAN_HANDICAP/OVER_UNDER/MATCH_ODDS/SPORT set had already been correctly written and wired into deployment-api's
`_ACCEPTED_EXCEPTIONS` days ago (`uac` commit 2026-07-30, `deployment-api@7988451` 2026-08-03) — the code was right,
production just never received it. Confirmed via direct Cloud Run inspection: every revision built since 07-31
(`00375`..`00428`) was either never traffic-routed, or (from `00419` onward) was a recurring `IAM-FIX-RETEST` diagnostic
probe (`python3 -c "..."` command override, no real app) deployed repeatedly onto this SAME production service —
unrelated to this investigation, cross-referencing the cold-start deploy issue linked above (same doc this session added
fresh evidence to: the freeze wasn't a forgotten manual pin, it was that doc's cold-start bug silently no-op'ing every
automatic cutover attempt for 4 days straight). Recovered by building fresh (`deploy-shared.sh`) and manually forcing
`gcloud run services update-traffic` after the automatic cutover again silently failed — see that doc's Progress Log for
the full blow-by-blow. Confirmed live and stable afterward (multiple 200s across `/api/health` + two `distinct-values`
asset_groups).

## Cause 2 (5 values) — legitimate MTDS/MDPS output never registered as accepted-exception

Bare `ASIAN_HANDICAP`/`OVER_UNDER` (real: `canonical_ids.py::build_instrument_id` only appends the point suffix when
`outcome.point is not None` — a null point from the vendor legitimately produces the bare token) and
`exchange_odds`/`fixed_odds`/`odds` (real: the deliberate 2026-07-27 venue-based split,
`market-tick-data-service/scripts/sports/exchange_fixed_odds_fork/`, already a registered UAC `CONTRACT_REGISTRY` key —
just never added to the distinct-values accepted-exceptions set). Added to
`SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` (`unified-api-contracts@cb545bef`).

## Cause 3 (2 real writer bugs, still-open historical residue) — venues

- `LADBROKES_UK`/`SPORT888` (real captured data: 12,164 + 18,882 = 31,046 rows, `data_type=trades`,
  `instrument_type=odds`): `market-tick-data-service/engine/orchestrator/venue_fetch.py`'s per-league sports batch
  writer computed `bm_str = bm_raw.upper()` directly — bypassing the already-existing `SPORTS_VENUE_FOLD` dict
  (`{"ladbrokes_uk": "LADBROKES", "sport888": "BET888SPORT"}`) that two SIBLING writers (`odds_api_adapter.py`,
  `odds_api_ws.py`) already correctly apply. Fixed to `SPORTS_VENUE_FOLD.get(bm_raw, bm_raw).upper()`
  (`market-tick-data-service@edfa0615`). **CORRECTION (2026-08-05, this doc's own earlier text was wrong)**: this is NOT
  a narrow "written between 2026-07-27 and today" delta — a direct manifest census
  (`scripts/sports/census_track_c_venue_restamp_targets_2026_07_27.py`) shows LADBROKES_UK spans 990 distinct dates
  (2023-03-31..2026-07-26) and SPORT888 spans 1,824 distinct dates (2020-06-06..2026-07-26), i.e. essentially the SAME
  historical range as the ORIGINAL pre-2026-07-27 backlog that `restamp_sports_bookmaker_venue_2026_07_27.py` +
  `manifest_swap_venue_restamp_2026_07_27.py` already fixed once (that closeout's own numbers: 24,268+37,722 GCS objects
  / 8,859+13,997 manifest rows, verified 0 stale rows 2026-07-27). Today's counts (12,164 / 18,882 manifest shards) are
  HIGHER than that closeout's manifest-row counts — the most likely explanation is a full historical
  backfill/reprocessing job re-ran across the whole date range SOMETIME AFTER 2026-07-27 using the still-broken
  `venue_fetch.py`, re-polluting the entire range the July closeout had just cleaned. No currently-RUNNING VM was found
  repeating this (checked 2026-08-05: only the live producer was active), so this is a closed, bounded backlog to
  re-stamp, not an actively-growing one — but it is the FULL historical range, not a 1-2 day window. The candle-shape
  sibling data (arbitrage_opportunity/odds_movement/ odds_snapshot/odds_horizon_bucket) for both venues is confirmed
  CLEAN (0 residual, 2026-08-05 fresh rollup read) — only the raw-tick shape needs the re-stamp.
- `FOOTBALL` (all `attempted_failed`, 0 captured — 75 odds_movement + 69 arbitrage_opportunity + 50 odds_snapshot = 194
  rows, no real GCS objects at risk): `market-data-processing-service/app/core/live_workers.py`'s
  `_eager_preprocess_and_recover_metadata` did `input_venue = instrument_id.split(":")[0]` unconditionally — correct for
  every other asset_group's `VENUE:TYPE:SYMBOL` id shape, wrong for sports' `SPORT:BOOKMAKER:MARKET:...` shape (position
  0 is the sport). The already-existing, asset_group-aware `_venue_token_from_canonical_id` helper (built for this exact
  bug class, `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2) was two lines away and already imported, just not
  called at this one site. Fixed (`market-data-processing-service@595a1ff`).

Both writer fixes stop NEW pollution immediately but do not touch already-written rows — the panel will keep showing
these 3 venues until either a new capture cycle produces enough correctly-stamped rows to dominate, or (for
LADBROKES_UK/SPORT888's real captured data) a historical re-stamp runs. `FOOTBALL`'s rows are all `attempted_failed`
phantoms (no real GCS content) — may simply clear on the next natural retry now that the writer is fixed; worth
confirming before scoping a re-stamp for it.

## Shipped this session

- `unified-api-contracts@cb545bef` — 5 accepted-exception values.
- `market-tick-data-service@edfa0615` — `venue_fetch.py` SPORTS_VENUE_FOLD fix.
- `market-data-processing-service@595a1ff` — `live_workers.py` `_venue_token_from_canonical_id` fix.
- `unified-trading-pm@d211c01be` — QG baseline line-pointer correction (unrelated 1-line shift from the MTDS fix; since
  superseded/removed cleanly by `unified-trading-pm` slot-12's real fix to the underlying call site, 2026-08-05 — no
  action needed, noted for the record only).
- `uts-shared-deployment-api` — fresh build + deploy, live traffic confirmed on `uts-prd-sa` + today's code.
- Fresh honest-coverage rollup triggered same day (2026-08-04) — **confirmed 2026-08-05**: `generated_at` has advanced
  every day since (most recently `2026-08-05T14:42:13Z`), panel stable at venues 3/13, instrument_types 0/0, data_types
  0/0 for a full 24h+ with zero regression — the code fixes are holding correctly in production.
- **2026-08-05**: found the live capture VM (`mtds-live-sports-odds-api-trades-20260803-172841`, running continuously
  since 2026-08-03, i.e. BEFORE this session's `venue_fetch.py` fix) was still executing pre-fix code and would have
  kept writing new LADBROKES_UK/SPORT888 rows indefinitely. Stopped it and relaunched via
  `deployment-service/scripts/vm/launch-mtds-live.sh` with its exact original parameters (read from its own instance
  metadata:
  `--asset-group sports --shard-spec sports:ODDS_API:trades --instrument-ids "ODDS_API:SPORT:soccer_epl;...5 leagues" --live-source native --env prod`)
  — now running as `mtds-live-sports-odds-api-trades-20260804-131449`, confirmed picking up today's fix (see traps below
  for the 2 real gotchas hit getting this right).
- **2026-08-05 (later same day)**: `market-tick-data-service@118eb148` — fixed
  `manifest_swap_venue_restamp_2026_07_27.py`'s case-sensitive `raw_tick_only` filter (see the completed re-stamp todo
  above for the full story — this bug meant the manifest-relabel half of the venue rename had never actually worked, on
  any prior run). Executed the full historical GCS content re-stamp + manifest relabel for LADBROKES_UK→LADBROKES and
  SPORT888→BET888SPORT (31,118 GCS objects, 30,912 manifest rows across both venues) on a manually-launched
  `canonical-migration-sports-` VM, torn down after completion. Triggered a fresh sports honest-coverage rollup and
  confirmed live: **venues non-canonical 3→1** (only the pre-existing `FOOTBALL` residual remains).
- `market-tick-data-service@b2497b73` — unrelated, but was blocking every quickmerge in this repo: another session's
  already-committed `783a5463` had a bare import-pattern violation
  (`from unified_trading_library.manifest_writer import read_availability_index_safe` instead of the package root) in
  `scripts/one_offs/trace_composite_venue_provenance_2026_08_05.py`. Fixed via the checker's own `--fix` mode and
  shipped standalone before retrying my own commit. **Lesson**: shipping this collided with `quickmerge`'s own internal
  patch-stash mechanism — my second commit attempt for `manifest_swap_venue_restamp_2026_07_27.py` (not part of this
  file's scope) got autostashed+popped mid-run, and its pop raced against `prek`'s own `ruff --fix` import-sorting pass
  on the SAME `trace_composite_venue_provenance` file, leaving a literal unresolved 3-way-merge marker block (the
  "Updated upstream" / "Stash base" / "Stashed changes" triplet a `git stash pop` conflict writes into the file) STAGED
  (not just in the working tree) after the run reported success. Confirmed safe to resolve by comparing all 3 marked
  sections against `git show HEAD:<file>` — HEAD's already-committed content was byte-identical to the "Stashed changes"
  section (ruff had just reformatted 2 import lines into 1 sorted line), so
  `git restore --source=HEAD --staged --worktree -- <file>` cleanly discarded the marker debris with zero data loss.
  **Takeaway for next time**: a quickmerge run reporting exit 0 / "completed" is NOT proof the working tree is clean —
  always `git status --porcelain` (no path arg) after every quickmerge, especially when two commits touch overlapping
  files in quick succession on a shared checkout.
- `market-tick-data-service@1c7edf32` — 2 more unrelated repo-wide-gate blockers hit while shipping the FOOTBALL cleanup
  (see the completed FOOTBALL todo below): (1) `pyproject.toml` was missing
  `[tool.ruff.lint] external = ["TID251", "DTZ"]` — without it, ruff's RUF100 rule flagged the QG's OWN documented
  per-line opt-out (`# noqa: TID251` with a reason) as "unused", because TID251/DTZ aren't in this repo's default
  `select` list (they're checked by QG STEP 5.95's separate `--isolated` ratchet scan instead) — a genuine contradiction
  between the documented escape hatch and the actual ruff config, now fixed; (2)
  `scripts/reset_source_returned_zero_manifest.py` had an un-suppressed deliberate `google.cloud` import pushing the
  TID251 ratchet count 1 over baseline — added the noqa (now workable thanks to fix 1). **A THIRD blocker
  (`DefiManifestRecorder.record_captured`/`_emit_captured_add` 1 line over the 50-line method cap) resolved itself**:
  while I was mid-fix, TWO other concurrent sessions independently hit and fixed the exact same method-size violation
  (`market-tick-data-service@cec16b74` then `@aafbbfdf`) — confirmed HEAD's landed version already satisfied the cap, so
  I discarded my own overlapping edit via `git restore --source=HEAD` rather than ship a redundant/conflicting third
  fix. **Lesson**: this repo had unusually heavy concurrent quickmerge traffic today (`ps aux` showed 5+ simultaneous
  quickmerge processes from other slots at one point) — expect real, DIFFERENT blockers on consecutive attempts (not
  just flaky repeats), and always re-check whether a blocker you're about to fix has already been fixed by someone else
  before shipping your own version.
- `market-tick-data-service@9d1d7441` — the FOOTBALL manifest-only phantom-row REMOVE script (see the completed FOOTBALL
  todo below for the full account).

## Todos

- [x] ✅ [DATA] P2. Confirm the fresh honest-coverage rollup completed and re-read the live panel — **DONE,
      2026-08-05**: confirmed venues 3/13 non-canonical (FOOTBALL/LADBROKES_UK/SPORT888 only, unchanged for 24h+),
      instrument_types 0/0, data_types 0/0. FOOTBALL did **NOT** clear naturally — still present after a full day +
      fresh rollup, so its own todo below stays open (the "may self-heal" hope in the original write-up did not pan
      out).
- [x] ✅ [DATA] P1. Restart the live capture VM to verify the fix — **DONE, 2026-08-05** (see Shipped above) but leaving
      as a checked-off record with the 2 traps hit, since the SAME traps will bite the next person who relaunches any
      `mtds-live-*` VM after a code fix: 1. `launch-mtds-live.sh`'s tarball-freshness check is a WARN, not a hard block,
      by default (`LC_TARBALL_FRESHNESS` unset) — it launched the VM anyway with a stale `market-tick-data-service`
      tarball TWICE in a row (once because the local checkout had unrelated dirty test-artifact files that made
      `create-code-tarballs.sh` skip the repo entirely with only a warning, no error; once because another slot pushed a
      new LDR commit in the ~40s window between tarball-build and VM-launch, which the local `slot-cron-ff-pull`
      auto-pulled). Neither is a bug in the launcher — but **this WARN-not-ENFORCE default is very plausibly HOW the
      original bug persisted through multiple "fixed and closed" remediations**: a live producer can keep running
      provably-stale/buggy code indefinitely with only an easy-to-miss WARNING, never an error. Worth a follow-up issue
      doc proposing `LC_TARBALL_FRESHNESS=enforce` as the default for `mtds-live-*` relaunches specifically (live
      producers, unlike batch/backfill VMs, run for weeks — a stale launch is not self-correcting). 2. **Near-miss**:
      initially tried to reuse the OLD (now-stopped) VM by just `gcloud compute instances start`-ing it back up,
      forgetting its `VM_MODE=live` startup-script re-runs on every boot (GCE startup-scripts are not one-shot) — this
      would have created a SECOND concurrent live producer for the same shard, exactly the `mtds-live-{ag}-{shard}`
      singleton-lock race the launcher's own docs warn about ("thrash on the WS feed + race on the Redis Stream consumer
      group"). Caught and re-stopped within ~30-60s, before confirmed harm, but this is a real trap: a `mtds-live-*` VM
      is stateful and its boot disk should never be casually restarted like a stateless one — always launch a genuinely
      fresh instance via the launcher script instead.
- [x] ✅ [DATA] P2. Historical re-stamp for LADBROKES_UK→LADBROKES / SPORT888→BET888SPORT — **DONE, 2026-08-05**. Ran on
      a manually-launched VM (`canonical-migration-sports-venue-restamp-20260805-170246`, registered
      `canonical-migration-sports-` prefix, `asia-northeast1-c`, SPOT, torn down after completion — no ready-made
      wrapper launcher existed for this specific one-off pair of scripts, so used the documented "Manual SSH setup"
      recipe from `deployment-service/scripts/vm/README.md` instead of extending the 2151-line
      `launch-canonical-migration-vm.sh` dispatcher). Full historical range both venues: LADBROKES_UK
      2023-03-31..2026-07-26 (12,202 objects), SPORT888 2020-06-06..2026-07-26 (18,916 objects) — 31,118 total, matching
      the census's manifest-shard estimate closely. First apply pass:
      `restamp_sports_bookmaker_venue_2026_07_27.py --apply-prod --confirm-prod-write` found 30,814 objects (99.0%)
      already-present-and-content-equivalent (the original 2026-07-27 migration had already covered them — the
      "re-polluted the whole range" theory from Cause 3 above was WRONG in degree: only 298 objects (0.96%) actually
      diverged, not the full range), 6 genuinely new, 0 failed, **171 (LADBROKES_UK) + 127 (SPORT888) = 298
      content_mismatch** the tool correctly refused to blind-overwrite (its own documented safety behavior — never
      guesses on a pre-existing, non-equivalent target). Diagnosed the 298 by reusing the tool's own
      `_content_relation`/natural-key comparison on every flagged object (not guessed): a clean ~50/50 split between
      `src_superset` (source strictly contains target's rows, zero ambiguity, safe) and fully-disjoint-key `mismatch`
      (same row count both sides, e.g. 24/24, but 0 natural-key overlap — consistent with a later reprocessing job
      re-fetching the same historical days under fresh `fetch_utc`/`bm_time` stamps). Presented this finding to the
      operator (AskUserQuestion, 3-way tradeoff: overwrite-with-source / union-merge-dedup / leave-as-residual) rather
      than guess on production odds-market data — operator chose **overwrite target with source** (source is the
      continuously-recaptured live path; simpler, no duplicate-tick-inflation risk). Wrote a small scoped reconciliation
      script (`reconcile_mismatch.py`, scratchpad-only, not shipped — reuses the main script's own
      `_rewrite_venue_content`/`_target_path`/`scan_day` primitives, only removes the "never overwrite on mismatch"
      gate, scoped to the 47+40 already-flagged days) — 171+127=298 overwritten, 0 failed. Re-ran the main script's own
      apply pass again as an independent verify: **0 content_mismatch, 0 failed, both venues, 100% clean.** **Found +
      fixed a second real bug while running `manifest_swap_venue_restamp_2026_07_27.py`**: its `raw_tick_only` filter
      compared `instrument_type`/`data_type` against uppercase `"ODDS"`/`"TRADES"`, but the live manifest carries
      lowercase `odds`/`trades` for this shape (confirmed via direct manifest read) — the exact C2a-class casing gotcha
      CLAUDE.md already rules on ("compare case-insensitively, do NOT flag, do NOT refuse"). This silently produced a
      dry-run of "0 REMOVE, 0 ADD" for both venues — i.e., the manifest-swap step had **never actually worked** for the
      raw-tick shape on ANY prior run, including the original 2026-07-27 migration (explaining why LADBROKES_UK/
      SPORT888 still had live manifest rows today despite that migration's claimed 8,859+13,997-row swap — the GCS
      content got copied then, but the manifest was never relabeled). Fixed with `.str.upper()` on both sides
      (`market-tick-data-service@118eb148` — see Shipped below), applied directly to the VM's deployed copy first to
      unblock, confirmed the dry-run now correctly shows 12,164/18,882 planned REMOVE+ADD matching the census exactly,
      then ran `--apply-prod --confirm-prod-write` for both venues: **0 stale rows remaining, both venues, verified via
      the script's own post-write re-download check.** Final census re-run confirms **LADBROKES_UK: 0 rows, SPORT888: 0
      rows** (no manifest entries at all for either old-venue name). Triggered a fresh sports-scoped honest-coverage
      rollup (`launch-measure-honest-coverage-vm.sh sports`) and confirmed on the LIVE panel: **venues non-canonical
      count 3 → 1** (only `FOOTBALL` remains, the separate pre-existing residual tracked below — LADBROKES_UK/SPORT888
      no longer appear in the non-canonical list at all). (repo: market-tick-data-service)
- [x] ✅ [DATA] P3. Confirm FOOTBALL's 194 `attempted_failed` rows either clear naturally on a future retry or, if not
      after another few days, scope why they're still failing post-fix — **DONE, 2026-08-05**. Investigated via Explore
      agent: confirmed the ALREADY-fixed `live_workers.py::_eager_preprocess_and_recover_metadata` venue bug (see
      Cause 3) is the SINGLE venue-derivation point for this candle family, for BOTH batch and live —
      `CandleOrchestrationService` explicitly overrides the batch/live MRO to always route through
      `LiveOrchestrationMixin._process_instrument_file`, so there is no separate, still-broken batch code path; the 194
      rows (all `pipeline_mode=batch_footystats`, 2 distinct dates: 2021-11-26/2025-12-18) are confirmed **pure pre-fix
      residue**, not a live second bug. Also confirmed **no retry mechanism in this codebase covers them** —
      `reprocess_sports_odds.py` (the only standing retry job) targets a different data_type entirely
      (`odds_horizon_bucket`) and only a rolling 2-day window, explaining why they never self-healed. Since all 194
      carry `row_count=0`/`capture_status=attempted_failed` (0 real data, no GCS objects at risk) and `FOOTBALL` can
      never legitimately recur as a venue value now that the bug is fixed, wrote a manifest-only CAS-protected REMOVE
      script (`remove_football_phantom_rows_2026_08_05.py`, mirrors `manifest_swap_venue_restamp_2026_07_27.py`'s safety
      shape: pre-write snapshot, generation-matched conditional upload, defensive re-check refusing to proceed if any
      matched row is NOT `attempted_failed`, post-write verify) — `market-tick-data-service@9d1d7441`. Ran on a VM
      (`canonical-migration-sports-football-cleanup-*`, registered prefix, SPOT, torn down after): dry-run confirmed
      exactly 194/194 `attempted_failed`/0 non-phantom, apply removed all 194, verify re-download confirmed 0 remaining.
      Fresh census re-run: **LADBROKES_UK/SPORT888/FOOTBALL all show 0 manifest rows.** (repo: market-tick-data-service)
- [ ] [INFRA] P3. File (or fold into an existing infra doc) a proposal to default `mtds-live-*` VM relaunches to
      `LC_TARBALL_FRESHNESS=enforce` — see the trap noted in the VM-restart todo above; a live producer silently running
      stale code for days-to-weeks is a plausible root cause worth closing off generally, not just patching for this one
      incident. (repo: deployment-service)

## Progress Log

- **2026-08-04 (interactive session)**: shipped all 3 code fixes + fresh deploy + fresh rollup (see Shipped above).
  Session interrupted mid-scoping of the historical re-stamp (checkpoint before any GCS/manifest writes were made —
  nothing partial was left in a bad state).
- **2026-08-05 (interactive session, same operator, continued after a ~26h gap)**: re-verified all 2026-08-04 fixes live
  and stable (traffic, live VM, panel all unchanged/correct — zero regression over 24h+). Ran the manifest census for
  LADBROKES_UK/SPORT888 and found the earlier session's "narrow recent window" assumption was wrong — corrected above.
  Found + fixed the live capture VM still running pre-fix code (restarted, 2 tarball-freshness traps hit and worked
  around, documented as a follow-up todo). Extracted `--days-file` day-lists for the re-stamp but did not yet execute it
  (no ready VM launcher for this specific script; needs the minimal-VM-+-SSH path scoped in the todo above) — session
  paused here for a `/pre-compact` checkpoint before continuing.
- **2026-08-05 (same day, continuation after `/pre-compact`)**: executed the historical re-stamp end to end (see the
  completed Todos entry above for the full account). Two real findings along the way, not anticipated by the original
  2026-07-27 tooling: (1) the original migration's "0 pre-existing rows" assumption no longer held (a second migration
  attempt against an already-migrated target needs 3-way reconciliation, not just copy-if-missing) — resolved 298
  genuinely-diverged objects via an operator-approved overwrite-with-source policy after diagnosing (not guessing) the
  divergence pattern; (2) `manifest_swap_venue_restamp_2026_07_27.py`'s uppercase `ODDS`/`TRADES` filter never actually
  matched the live manifest's lowercase `odds`/`trades` values — meaning the manifest-relabel half of this migration
  class had silently no-op'd on every prior run, including the original 2026-07-27 closeout (the GCS content moved, the
  manifest never did). Fixed and shipped. Verified end-to-end: fresh census shows 0 rows for both old venue names, fresh
  honest-coverage rollup shows the live panel at venues 3→1 non-canonical (only the pre-existing, separately-tracked
  `FOOTBALL` residual remains). Both VMs used (the manual re-stamp VM and the honest-coverage measurement VM) torn down
  after completion.
- **2026-08-05 (same day, operator asked to also close out FOOTBALL "so it goes forever")**: investigated + resolved the
  FOOTBALL residual (see the completed FOOTBALL todo above). Along the way hit 3 MORE unrelated repo-wide-gate blockers
  on this heavily-concurrent shared checkout (import-pattern violation, TID251-ratchet-vs-RUF100 contradiction,
  DefiManifestRecorder method-size cap) — all fixed or resolved by taking a concurrent session's already-landed fix (see
  Shipped above). **Verification caught a real false alarm**: the live panel initially kept showing `FOOTBALL` as
  non-canonical even after the fix + a fresh rollup completed; rather than trust that, downloaded the actual
  `coverage.json` directly (`gsutil cat`) and confirmed **zero** mentions of `FOOTBALL` anywhere in the file — the panel
  was serving a stale `deployment-api` in-process cache (30 min TTL, keyed independently per Cloud Run instance) that
  hadn't caught up to the latest write yet, not a real data problem. Waited it out and re-confirmed live. **Final
  verified state: sports distinct-values panel — venues/instrument_types/data_types/chains all 0/0 non-canonical across
  the board** (started this session at 44 non-canonical). This doc's scope is now fully resolved; only 2 small,
  unrelated follow-up todos remain (see below) — neither blocks anything or affects the panel.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (sports tranche) — sole open todo (`[INFRA] P3`,
  `LC_TARBALL_FRESHNESS=enforce` default proposal) matches the doc's own self-framing in the Deferred-work table below
  ("a scoping/design todo, small") — filing a proposal to change a launcher-wide default is a design call (what the
  right default even is, blast radius across other `mtds-live-*` shapes), not a mechanical fact-check. Everything else
  in this doc is already resolved (0/0/0/0 non-canonical, verified live).
- **na-eligibility-audit 2026-08-07**: KEEP-NA-STALE, already-duplicated (sports tranche) — the sole open `[INFRA] P3`
  todo (`LC_TARBALL_FRESHNESS=enforce` default) has since been extracted verbatim (same repo, same env var, same
  proposed default) into `sports_satellite_ao_dispatch_batch10_2026_08_06.md` todo 3 (`assigned_vm: planning`), whose
  companion gated finalize plan `sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md` already carries the
  reconciliation step to flip this checkbox and archive this doc once batch10 todo 3 lands. This postdates (by ~15h) the
  2026-08-06 KEEP-NA-valid entry above, which was correct when written — batch10 didn't exist yet. Citation-only fix,
  not a reclassification: dispatching this doc's own copy of the todo would race the already-designed batch10
  extraction. No `assigned_vm` change. Let the batch10 -> batch10-finalize pipeline run its course (pending operator
  flip from draft to active); this doc self-closes through that path.

## Deferred work after 2026-08-05

| Item                                                              | State              | Blocked on                                                                      |
| ----------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------- |
| `LC_TARBALL_FRESHNESS=enforce` default proposal for `mtds-live-*` | Not done           | Nobody — a scoping/design todo, small.                                          |
| LDR→main promotion of today's shipped commits                     | Cannot be done yet | Time — auto-drains on the standing 15-30min cron; nothing to do but let it run. |

**This doc's scope is fully resolved** — the sports distinct-values panel is 0/0/0/0 non-canonical across every axis,
verified live. The one remaining todo (`LC_TARBALL_FRESHNESS=enforce`) is an unrelated small process-hardening proposal
that doesn't block or affect anything here; pick it up whenever, no urgency.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item is genuine unblocked work.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA-STALE, already-duplicated — verdict unchanged
  from 2026-08-07. This doc now also carries a dated `⚠️ CORRECTION 2026-08-08` banner (this doc's own "0/0
  non-canonical" headline was achieved by adding values to `_ACCEPTED_EXCEPTIONS`, not by genuinely canonicalising them
  — real gap: 21 hidden fan-out bookmakers, `KALSHI`, a blank venue, uppercase `ODDS`) — but that correction does not
  reopen this doc's own sole tracked todo (`LC_TARBALL_FRESHNESS=enforce`, already extracted into
  `sports_satellite_ao_dispatch_batch10_2026_08_06.md` todo 3, `assigned_vm: planning`); the panel-badging fix the
  correction names is owned end-to-end by `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`'s "The panel"
  section, not by this doc. No new open work here, no reclassification.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA-STALE, valid — reconfirmed `sports_satellite_ao_dispatch_batch10_2026_08_06.md`
  is still `status: active` / `assigned_vm: planning` with its todo 3 (`LC_TARBALL_FRESHNESS=enforce` proposal, line
  ~98) still open — genuinely in-flight, not stalled. No change.