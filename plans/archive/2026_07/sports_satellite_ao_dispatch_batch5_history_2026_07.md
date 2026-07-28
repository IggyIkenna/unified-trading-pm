---
doc_type: plan
title: Sports satellite AO batch 5 — extracted closed-todo history (line-cap remediation)
summary:
  Four fully-closed todos extracted verbatim, byte-for-byte, from sports_satellite_ao_dispatch_batch5_2026_07_26.md to
  bring that live doc back under the 1000-line hard cap — the live file collided with the cap three times in one day
  (2026-07-28) blocking unrelated edits. Every extracted item had already reached its own done-when with no dangling
  open sub-items; zero content loss, a one-line pointer left in the live doc at each removed item's original location.
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, batch-5, line-cap, archive, history]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/issues/sports_satellite_batch5_line_cap_blocks_priority_edit_2026_07_28.md,
  ]
created: "2026-07-28"
parent_epic: sports_master
source:
  Extracted 2026-07-28 per sports_satellite_batch5_line_cap_blocks_priority_edit_2026_07_28.md's SCRIPT P2 remediation
  todo, during the operator's 2026-07-28 decision-digest-apply pass which needed to add content to the live doc.
execution_scope: local-only
assigned_vm: NA
priority: P3
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by: extraction 2026-07-28, live doc back under cap
---

# Sports satellite AO batch 5 — extracted closed-todo history

Four closed todos, extracted verbatim from `sports_satellite_ao_dispatch_batch5_2026_07_26.md` (each was already at its
own done-when with no open sub-items) to relieve that doc's line-cap pressure. Pure historical record — nothing here is
actionable.

## Extracted todo 1 — sports odds manifest-routing regression (originally after the odds-api backfill todo)

- [x] ✅ [DATA] P1. Resolve the sports odds manifest-routing regression opened by the 2026-07-24 addendum to
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`: (1) grep+READ the manifest-write target
      resolution in the sports capture path in market-tick-data-service (same class of `_resolve_manifest_bucket()`
      logic documented in `sports_phantom_audits_reference_not_marketdata_2026_07_14.md`) to determine whether
      `market-data-tick-sports-prd`'s manifest writes for `batch_odds_api` (and every other sports `pipeline_mode`) were
      DELIBERATELY re-routed to `instruments-store-sports-prd` around 2026-07-20/21 (a real code/config change) or are
      an unintended regression -- confirm across the full population, not just the two data points the addendum
      measured; (2) separately investigate the 2026-07-21→2026-07-23 GCS-side writer gap for
      `pipeline_mode=batch_odds_api/asset_group=sports/` (zero venue prefixes on disk for those 3 dates, confirmed by
      direct listing) -- a real fetch/write gap distinct from the manifest-routing question; (3) once (1) is answered,
      record a disposition recommendation for `market-data-tick-sports-prd`'s now-possibly-stale `_index/`: either (a)
      leave it as a documented stale historical artifact, or (b) backfill/repoint it so single-bucket tools (orphan
      sweep, this skill's default Phase-0 methodology, any future `market-data-tick-sports-prd`-scoped reconciliation)
      stop producing a false orphan signal for sports specifically -- if the right disposition is genuinely undecidable
      from the code/data alone (not just unimplemented), state that explicitly and stop rather than picking one
      autonomously. Repo: market-tick-data-service (routing investigation + gap investigation); unified-trading-library
      / market-tick-data-service (disposition, if a code change is warranted). **Done when**: todo 6's manifest-routing
      question is answered (deliberate change vs regression) with a fix or documented rationale if regression; todo 7's
      3-day GCS gap is investigated and its cause reported (or explicitly marked unexplained with evidence gathered);
      todo 8's `_index/` disposition is either implemented or, if it needs an operator call, escalated with the
      recommendation stated rather than left silent; all three findings are recorded as a new dated section in
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`, and the doc's frontmatter `status` is
      flipped to `resolved` if all three are closed (or left `open` with the remaining item named). Source:
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`. **Resolution (2026-07-26, slot 8)**: all
      three closed (deliberate routing / same future-date-guard root cause, no longer reproducible / index left
      stale-by-design) — `unified-trading-pm@3d48c7a9b`.

## Extracted todo 2 — sports odds phantom-uppercase safety-tooling close-out

- [x] ✅ [CODE] P2. **DONE 2026-07-26 (slot-8, `data_engineering`) — closed the last remaining piece, 3.4's dry-run.**
      Direction is fully decided (§4.3 ✅ DECIDED 2026-07-22 — lowercase `data_type` canonical; §4.1/4.2/4.4 also
      closed) — nothing left here was a judgment call, only unbuilt implementation. Scope: (a) build the three
      still-missing Part 3 safety-tooling pieces the RE-TRIAGE (2026-07-23) names as genuinely unbuilt — row-identity
      assertions for the purge/relabel/drop scripts, a consolidator-paused pre-flight check, and a `coverage_drift.py`
      pre-notify mechanism — plus a `--dry-run` mode on the 3.2/3.3/3.4 remediation scripts; (b) in
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`, remove the uppercase
      `"ODDS"`-family case-variant entries from `DATA_TYPES_BY_ASSET_GROUP["sports"]` (keep only the lowercase forms)
      and un-skip `unified-api-contracts/tests/unit/test_sports_data_type_vocabulary.py` (drop the `_SKIP_REASON_K0B`
      gate) per §2.2. Did NOT build or duplicate the cross-object-CAS+alarm mechanism itself — that stays a separate
      tracked open todo (`sports_consolidated_closeout_2026_07_19.md`, "NEW 2026-07-23 (decision 12)"). Did NOT execute
      any actual manifest purge/relabel/drop against prod (3.2/3.3/3.4 remain gated on the standing human-only execution
      trigger per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) — build-only, as scoped. Source:
      `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (RE-TRIAGE 2026-07-23 section + §2.2). **Done when**
      (all now met): the four safety-tooling pieces exist as reviewable code/scripts (dry-run mode included) with unit
      tests, the uppercase `ODDS`-family entries are removed from the sports data_type registry,
      `test_sports_data_type_vocabulary.py` runs unskipped and green, and both repos' `quality-gates.sh` are green —
      with no manifest/GCS write performed. **PARTIAL 2026-07-26 (slot-2)**: (b) done — `uac@a32ad5fb` (+ regression fix
      `mtds@f7504a10`). (a) 2/3 pieces + 1/2 dry-runs — `assert_consolidator_paused`/`assert_row_identity`/3.3 dry-run
      (`mtds@f7504a10`), `coverage_drift.py` pre-notify (`deployment-api@1f0d3a0`); 3.4's dry-run deferred (needs live
      per-row GCS-existence check). All 3 repos green, zero writes. Full writeup + a `consolidator_liveness.py`
      naming-bug finding in `sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s entry — `pm@be0540e3d`. **DONE
      2026-07-26 (slot-8)**: built + live-tested `drop_sports_odds_phantom_uppercase_2026_07_26.py` (`mtds@8b60b415`) —
      `--dry-run`-only (no `--apply` flag at all, same posture as 3.3), 8 unit tests, plus a real prod dry-run against
      85 sampled captured uppercase-ODDS rows (2 separate seeds/sample-sizes): 85/85 confirmed phantom (no backing GCS
      object under either of 2 empirically-discovered `raw_tick_data/` path shapes — the doc's original single-template
      assumption doesn't hold across the full 2020-06-06..2026-04-14 date range, see the script's own module docstring
      for both shapes + how they were verified via direct `gcloud storage ls`, not guessed), 0 unexpected hits, every
      lowercase `odds` twin confirmed present. `quality-gates.sh` green (6993 passed, 80.52% coverage). Confirmed the
      consolidator scheduler-state 404 slot-2 already found + filed (`_scheduler_job_name_for_bucket` "prd" vs real
      "prod") — same already-tracked bug, not re-filed. Zero writes. All 4 safety-tooling pieces + the vocabulary fix
      are now complete — this todo's done-when is fully met.

## Extracted todo 3 — MDT schema-contract drift + phantom-row disposition close-out

- [x] [DATA] P0. ✅ 2026-07-26 — unified-api-contracts@82db8f8f + market-tick-data-service@f6ea0010. **Close out
      `sports_mtds_odds_trades_index_correctness_followup_2026_07_24`'s two open findings (T2.9 schema-contract drift +
      T2.10 phantom-row disposition).** (1) **T2.9**: canonical's OWN native live-written `(sports, odds, trades)`
      objects already fail the registered MDT schema contract
      (`ts_event, fixture_id, market_type, outcome, odds_decimal, broker, client, data_source`) against the real emitted
      fields (`bm_time, market_key, outcome_name, price, fetch_utc, …`) — since the mismatch is on currently-correct
      native live writers (not a defect in moved/legacy objects), UPDATE the registered contract to match the real
      schema (do not touch the writers); verify ≥1 native canonical object now validates clean under
      `_resolve_strict_validation`. (2) **T2.10**: re-query the CURRENT `market-data-tick-sports-prd` manifest for
      `source=api_football AND data_type=trades` on BOTH surfaces separately — the merged index AND the
      `_index/per_vm/_legacy_seed.parquet` shard (do not assume the merged index proves the seed is clean; the
      2026-07-17 SLOT-3 finding showed the seed re-introduces phantoms every consolidator cycle even after a
      merged-index-only purge). If 0 rows remain on BOTH surfaces, close T2.10 citing
      `issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`'s 2026-07-23 CAS-safe wipe
      (`market-tick-data-service@e9d9dec0`) as the resolution. If any remain, strip them from `_legacy_seed.parquet`
      with the source-filtered predicate (`source=='api_football' AND data_type=='trades'`, NULL-safe COALESCE — the
      real `odds_api × trades` population, 211,313+, MUST survive untouched), back up first, let the consolidator
      re-merge, then verify by content in a separate read process. Source:
      `sports_mtds_odds_trades_index_correctness_followup_2026_07_24`. **Done when**: the MDT `(sports,odds,trades)`
      schema contract validates ≥1 native canonical object AND the manifest (both merged index and
      `_legacy_seed.parquet` shard) shows 0 `api_football × trades` `captured` rows with nonzero `instrument_count`,
      with a written disposition recorded (contract-fix commit sha; T2.10 outcome stated as either "0 remaining, closed
      via 2026-07-23 wipe" or "N phantom rows stripped from seed, verified by content, consolidator re-merge
      confirmed").

## Extracted todo 4 — ml-service odds-feature naming migration close-out

- [x] ✅ [DATA] P2. **DONE 2026-07-26 (slot-10, data_engineering) — `ml-service@10e219f`.** Migrated 4 ml-service files
      still using pre-migration odds-feature names (missed by the earlier ml-service migration commits
      `unified-api-contracts@689efa54`/`ml-service@91f031a`, which covered only the `OddsFeaturesMixin` schema/loader,
      not mock-data generation or target generation). Re-derived the exact 125-entry old→new mapping positionally from
      the already-shipped `features-service@0ded2449` migration diff (ground truth, not hand-guessed), then grepped all
      125 old names (word-boundary) across the 4 named files: - `mock_data_provider.py`: 6 genuine hits fixed in
      `_SPORTS_FEATURE_NAMES` + the matching `X[...]` reads in `_generate_sports_training_data`
      (`velocity_home_24h_to_6h`→`odds_velocity_home_24h_to_6h`, `velocity_home_6h_to_1h`→`odds_velocity_home_6h_to_1h`,
      `steam_magnitude_home`→`odds_steam_magnitude_home`, `sharp_consensus_home`→`odds_consensus_home_sharp`,
      `pinnacle_vs_market_diff_home`→`odds_movement_pinnacle_diff_home`,
      `book_fragmentation_home`→`odds_fragmentation_home`). Left `implied_prob_home/draw/away` untouched — a different,
      coincidental naming (word-order-reversed), not an actual `ODDS_COLUMNS` entry. - `sports_target_generator.py`:
      **needed NO change** — an earlier, unrelated fix (`ml-service@a14985b`, a real data-leakage bug) already replaced
      its bare CLV/velocity column names with the real `odds_`-prefixed ones; its remaining old-name mentions are
      historical bug-documentation comments + `TARGET_TYPE` dict keys (a different namespace: target identifiers, not
      `ODDS_COLUMNS` feature columns). - `test_horizon_gate_shield.py`: 1 genuine hit fixed (3 sites) —
      `opening_home_odds`→`odds_opening_home` (a real pre-match-signal fixture column). -
      `test_sports_feature_loader.py`: 8 sites fixed in `TestOddsJoinKeyCrosswalk` (`home_implied_prob`→
      `prob_implied_home`) — incidental join-key-crosswalk placeholders, unrelated to schema-name validation.
      **Deliberately left unchanged**: `test_naming_mismatch_raises_loudly` (lines 146+149,
      `home_implied_prob`/`draw_implied_prob`) — this test intentionally constructs a dataframe with the OLD
      pre-migration names to prove the schema-validation gate raises loudly on a naming mismatch; renaming them would
      give the fixture 100% overlap with `OddsFeaturesMixin` and silently defeat the test's own purpose — the exact
      same-string-different-schema trap this todo warned about, hit for real. No f-string dynamically-built old-name
      construction found in any of the 4 files. Post-fix repo-wide grep of all 125 old names across the 4 files: zero
      functional hits (only the 2 categories above — the intentional negative test + historical
      comments/different-namespace dict keys — remain, both correctly out of scope). `quality-gates.sh` full run green.
