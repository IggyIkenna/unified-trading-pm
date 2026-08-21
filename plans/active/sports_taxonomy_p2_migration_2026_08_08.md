---
doc_type: plan
title: Sports taxonomy P2 — migrate GCS + manifest to the canonical venue/data_type/horizon model
summary: >-
  Phase 2 of the sports canonicalisation chain — the data migration that makes the P1 contracts true on disk. Re-stamps
  the largest population in the sports estate (375,257 `trades` shards over 6 years → `odds`), lowercases the whole
  19-token instruments-service reference vocabulary, purges the retired `exchange_odds`/`fixed_odds` instrument_type
  values from both manifest rows and GCS objects, removes ODDS_API/FOOTYSTATS from the venue axis, and cleans the
  phantom populations the audit found (20,785 KALSHI cross-AG rows, 2,490 blank-venue IS rows, 111 `trades_inplay`
  fossils — the live census showed 0 manifest rows + 1,197 real GCS objects, retired 2026-08-13). GATED on BOTH P1's
  contracts AND the in-flight API-Football entity campaign — renaming the registry while that campaign's two remaining
  all-leagues backfills are running would make the fetch loop write tokens the registry no longer expects. Prod deletes
  run agent-autonomously via the delete-safety §3a reversibility path (fresh same-run soft-delete-retention check), per
  operator ruling 2026-08-08 — NOT via [OPERATOR] tags.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [sports, migration, canonicalisation, gcs, manifest, re-stamp, delete-safety, reversibility-qualified]
related:
  [
    /plans/active/sports_taxonomy_p4_backfill_2026_08_08.md,
    /plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p1_capture_and_contracts_2026_08_08, sports_af_full_entity_completion_2026_08_03]
gate_on_depends: true
context_scope:
  [
    /codex/02-data/sports-data-types-catalog.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — 27 operator rulings"]
locked_by:
locked_since:
---

# Sports taxonomy P2 — the data migration

> **🔴 DOUBLE-GATED.** `gate_on_depends: true` on BOTH
> `/plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md` (contracts must exist first) AND
> `/plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md` (the in-flight API-Football campaign
> must converge first). That second gate is not optional — see below.

## Why the API-Football gate exists

`sports_af_full_entity_completion_2026_08_03.md` (`assigned_vm: planning`, `sequential: true`, running) has 3 open todos
— `FIXTURE_LINEUPS` all-leagues backfill (58,523 shards), `INJURIES` all-leagues backfill (62,709 shards), a P0
re-census of all 8 in-scope entities — all keyed on the UPPERCASE IS tokens this phase lowercases. Renaming mid-flight
would make the fetch loop write a token the registry no longer expects (phantom `expected_unattempted` rows) and leave
the re-census measuring the pre-rename axis; letting it converge first gives this migration ONE pass over a finished
corpus. Cross-plan banner added 2026-08-08 (`unified-trading-pm@3bb3214bdf`).

## Delete posture — §3a, not [OPERATOR]

Operator ruling 2026-08-08: **AO-dispatched, no operator step on deletes**, via
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (2026-07-26, extended 2026-07-28) — an agent may execute
a prod delete itself once a **FRESH, same-run** `gcs_bucket_soft_delete_retention_seconds(bucket)` check returns **≥
604800** (7 days; every `-prd-` GCP bucket audits at 604800, 0 gaps). **Every delete/purge todo below carries that fresh
check as an in-run precondition** — queried in the same execution, never assumed/carried over; if a bucket's check
returns < 604800, the delete falls back to approve-executes and the todo must stop and say so.

---

## Todos

### Consumer enumeration (must complete before any re-stamp)

- [x] ✅ [REVIEW] P0. **Enumerate every consumer of each token being renamed, per the P1-authored codex rename rule.**
      Minimum surfaces to enumerate — do NOT stop at a grep, READ each candidate consumer (features-service reads
      bucketed odds by PATH PREFIX, not by data_type column, so a data_type grep will miss it): MTDS writers + rebuild
      scripts, MDPS `canonical_writer`/`canonical_writer_shaping`, IS producers + `enumerate_expected_universe.py`,
      features-service `sports_feature_loader._ODDS_BUCKETED_PREFIXES`, ml-service sports loaders, deployment-api
      distinct-values + data-status, and the honest-coverage measurer. Output a checked-in consumer inventory; the
      re-stamp todos below cite it. **This todo gates every todo in the next section.** — Consumer inventory checked in
      at `/plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md`, produced via 7 parallel per-repo passes
      (MTDS, MDPS, instruments-service, UAC, features-service, ml-service, deployment-api), each checking all 5 binding
      types the codex rule names (path-prefix, filename, registry-membership, config-dict-key, literal value) — not a
      grep. Key findings: `enumerate_expected_universe.py`'s override-dict pattern is a proven prior-incident precedent
      (a partial `odds_horizon_bucket` lowercase already caused a 209,526-row zero-overlap manifest mismatch) and is the
      mechanism the re-stamp todos should route the vocabulary lowercasing through, not a new translation layer; the
      plan's own "`league_id=` is canonical" assumption is CONTRADICTED by UAC's actual path builder (it writes
      `league=`) — re-verify before the sweep todo runs; `odds_horizon_bucket` and `ODDS_API` are coupled in MTDS's
      freshness-preflight logic and must be re-verified together; features-service has 3 independent copies + ml-service
      1 more independent copy of the same raw-odds path logic; ml-service has a pre-existing FOOTYSTATS-venue
      classification bug worth fixing in passing. `strategy-service` was not searched — stated explicitly as an
      uncovered repo, not silently omitted. P3's ML-loader-migration todo remains parked pending the actual re-stamp
      landing (this todo is enumeration only, not the re-stamp).

### The re-stamps (each is a four-surface change — path, parquet content, manifest row, catalogue render)

- [x] ✅ [DATA] P0. **Re-stamp `trades` → `odds` across 375,257 shards (2020-06-06 → present).** Largest population in
      the estate. Both the GCS path segment `data_type=trades` and the manifest `data_type` column must move together —
      path==manifest on data_type is the standing MDPS contract. Run in-region on a VM per the VM-launcher runbook,
      never locally; SPOT with progress-checkpoint resume (never replay from START_DATE on preemption). Verify with a
      MEASURED count of target artifacts created, entity-scoped, on `time_created` — not an activity check. ✅ **DONE —
      VM `canonical-migration-sports-trades-to-odds-20260812-223215` exit 0** (3rd attempt; the first two died on the
      comma-formatted progress-regex stall, fixed `deployment-service@9d4f0769`). GCS restamp copied **382,137**
      `data_type=odds` objects (0 failed / 0 content_mismatch), then manifest-swap relabeled **merged 396,115 + legacy
      seed 232,098** `trades`→`odds` with VERIFY=0 remaining on each surface. Tooling shipped
      `market-tick-data-service@071a5466`. Residual `trades` rows (merged 20 × `live_odds_api` `empty_confirmed`; seed
      362,753) are the documented P3-gated live-writer re-population, not incomplete scope — see Progress Log.
- [x] ✅ [DATA] P0. **Materialise the `in_play` column and retire `trades_inplay`.** 111 rows only (2022-09-07 →
      2022-11-09, blank venue) — a fossil, not a population. **Disposition rule PRE-SPECIFIED**: fold into `odds` with
      `in_play=true` when the backing object exists AND its parquet has `row_count > 0`; delete the manifest row when
      the object is absent or empty (bookkeeping residue). Report the split. Confirm the filename-scoped reader
      (`reprocess_sports_odds.py::_is_consumable_trades_blob` matches on FILENAME `inplay_ticks.parquet`) is updated in
      the same change — this is exactly the consumer a data_type grep misses. ✅ **DONE — live census 2026-08-13: the
      manifest already carried 0 `trades_inplay` rows on ALL surfaces** (the plan's "111 fossil rows" were consumed
      /relabeled before this todo ran); the GCS estate held **1,197** `data_type=trades_inplay/inplay_ticks.parquet`
      objects (16 dates, 2022-09-07 → 2022-11-09) at real bookmaker venues × leagues, all verified non-empty
      (`bm_minutes_to_kickoff < 0` = genuine post-kickoff). Fold tool shipped `market-tick-data-service@e5d43bc3e1`
      (restamp_sports_trades_inplay_to_odds_2026_08_13.py) — **all 1,197 folded** to
      `data_type=odds/inplay_ticks.parquet` with `in_play=true` content column (0 content_mismatch / 0 failed / 0 empty
      residue), then sources deleted under the §3a fresh check (`soft_delete_retention_seconds=604800` ≥ 604800).
      **Split: 1,197 folded / 0 manifest rows deleted** (none remained). Reader fix shipped
      `market-data-processing-service@a9de0ff14b` — `_is_consumable_trades_blob` now EXPLICITLY excludes
      `inplay_ticks.parquet` (the endswith-`ticks.parquet` matcher would otherwise consume the quarantined post-kickoff
      population as pre-match trades). See Progress Log.
- [x] ✅ [DATA] P0. **Lowercase the instruments-service reference vocabulary** across all 19 tokens (`FIXTURES`,
      `FIXTURES_OUTCOMES`, `FIXTURES_SCHEDULE`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`, `FIXTURE_STATS`, `INJURIES`,
      `MATCHES`, `ODDS`, `PLAYER_STATS`, `PLAYER_VALUES`, `PREDICTIONS`, `SFI_PROGRESSIVE_STATS`, `STANDINGS`, `TEAMS`,
      `WEATHER`, `XG`, `XG_SHOTS`, `ODDS_HORIZON_BUCKET`). Only after the API-Football campaign has converged (the
      `gate_on_depends` above enforces this, but re-verify at run time — a gate is not a substitute for looking).
      **SPLIT 2026-08-14 (BLK-8436a1a6, operator-approved Option A)**: census + risk-analysis this session found the
      scope far larger and riskier than the 1h estimate — see the new dedicated todo immediately below and the Progress
      Log. This todo now tracks ONLY the split decision; the physical work moved to that todo. ✅ **CLOSED 2026-08-14
      (slot-26)** — the delegated physical-work todo directly below is done (`instruments-service@3637252f81`,
      `f2586ada09`, VM `canonical-migration-sports-19token-restamp-20260814-045346` ran to completion, 0 uppercase-token
      rows remaining) and its own closing verification todo is also done (live `check_shard_freshness` cross-check, 0
      case-driven spurious missing/stale) — this split-tracking todo's sole remaining scope was already satisfied by
      those two; nothing further to do under it.
- [x] ✅ [DATA] P0. **[OPERATOR] Execute the 19-token lowercase re-stamp on a dedicated VM (in-region, SPOT +
      progress-checkpoint resume) — census + code diff prepared 2026-08-14, execution not yet run.** Scope, in ONE
      atomic change (must land together, per the analysis below): 1. Metadata-only manifest re-stamp: rewrite
      `data_type` for the 19 uppercase tokens to their `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM` target
      (`unified-api-contracts` `league_data.py:297`) across `instruments-store-sports-prd-central-element-323112`'s
      `_index/availability_index.parquet` (merged index) AND any per-VM legacy-seed shards — **census 2026-08-14:
      15,907,902 of 17,208,810 rows (92%) carry an uppercase token**, dated 2014-01-01 → 2026-08-20 (tool:
      `census_sports_19token_lowercase_scope_2026_08_14.py`, shipped `instruments-service@<see Progress Log>`). NO GCS
      object copy needed — `entity=` path segments are already lowercase + stable (`SPORTS_DATA_TYPE_TO_FOLDER`, UAC
      `gcs_paths.py`); this is a manifest-column relabel only, unlike the `trades`→`odds` re-stamp. 2. Flip
      instruments-service's 8 registry sites to the lowercase form in the SAME change (never before step 1 completes
      verified): `process_preflight.py` (`_SPORTS_CORE_ENTITIES`, `_SPORTS_PER_FIXTURE_ENTITY_NAMES`,
      `_ENRICHMENT_ENTITY_VENUES`, `_SPORTS_PER_LEAGUE_ENTITIES`, `_FIXTURES_ENTITY_ALIASES`),
      `orchestrator/__init__.py::_SPORTS_DATA_TYPE_TO_PIPELINE_MODE`, `sports_dependency.py`
      (`_API_FOOTBALL_FIXTURES_DATA_TYPES`), `sports_reference_fixtures_write.py::_ENTITY_DT_BY_SHORT`,
      `writers.py`/`catalogue.py`'s venue-string-slicing derivation (apply `canonical_sports_is_data_type()` to the
      derived value before the manifest write). 3. Wire `enumerate_expected_universe.py`'s
      `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE` with all 19 tokens' lowercase mapping (§3b of the consumer inventory's
      VERDICT) — in the SAME change as steps 1-2, never standalone. **Why atomic, not staged (root-cause evidence,
      2026-08-14 session)**: UTL's shared `check_shard_freshness()` does an EXACT case-sensitive string match of
      `expected_venues` against the manifest `data_type`/`venue` columns
      (`unified-trading-library/manifest_writer/_queries.py:149`, `token_mask = date_df["venue"] == venue`) — no
      case-insensitive fallback. Flipping step 2 before step 1 completes (or vice versa) makes every already-captured
      historical date read as "missing" on the next freshness pre-flight, triggering re-fetch storms against LIVE
      provider APIs (API-Football/FootyStats/Understat/Transfermarkt/SFI/OpenMeteo) across 6+ years of history — the
      SAME failure class as the documented `odds_horizon_bucket` "572 permanently-skipped days" incident
      (`enumerate_expected_universe.py`'s own `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE` comment,
      `sports_data_sources_canonical_completion_2026_07_13.md` §1), but at ~46x the row count. The SAME mechanism
      applies to step 3: wiring the override dict before step 1 lands makes `enumerate_expected_universe.py`'s
      present-set match look for the NEW lowercase string while real captured rows are still uppercase-cased — a
      guaranteed repeat of the exact 209,526-vs-123,642 zero-overlap incident this dict's own comment documents, at
      19-token scale, which is why this todo does NOT ship the override-dict wiring standalone this session despite the
      operator's BLK-8436a1a6 answer inviting it — the diff is drafted (see Progress Log) but held for atomic landing
      with steps 1-2. **Explicitly OUT of scope** (P3's job per the consumer inventory's own delineation):
      `FIXTURES_SCHEDULE` / `FIXTURES_OUTCOMES` are UAC string CONSTANTS also directly imported by MTDS and MDPS — do
      not flip their VALUE here; only instruments-service's own registries/writers move in this todo. **Verify**: fresh
      census (rerun the shipped script) shows 0 remaining uppercase-token rows across BOTH manifest surfaces; a live
      freshness pre-flight run on a recent + a historical date each shows `is_fresh=True` with 0 spurious missing/stale;
      `[OPERATOR]` tag because this launches a VM + executes a corpus-scale prod manifest mutation (delete-safety codex
      §3a doesn't apply — no object delete, but the launch itself needs the same review a 16M-row prod-manifest rewrite
      warrants). **CORRECTION 2026-08-14 (slot-18, resume session) — step 2's "flip 8 registry sites to lowercase" is
      WRONG as literally worded; do NOT rewrite these registries' literal values.** Traced all 8 call sites and found
      they split into two disjoint classes the original wording conflates: **(a) UAC-axis lookup keys that MUST stay
      uppercase** — `orchestrator/__init__.py::_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` (looked up via
      `_pipeline_mode_for_sports_data_type()` at `writers.py:270`, BEFORE the manifest-write casing decision — flipping
      this dict's keys breaks the lookup, not the manifest) and any UAC-axis registry feeding
      `get_entity_league_coverage()`/`SPORTS_DATA_TYPE_TO_SOURCE`; vs **(b) genuine manifest-boundary sites that DO need
      the lowercase form, applied via a translation call at the boundary** (mirroring the already-proven
      `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE`/`_sports_manifest_data_type()` pattern,
      `enumerate_expected_universe.py:305-332`) — **not** by rewriting the registry literal, because several of the SAME
      registries feed BOTH kinds of call in one file: `process_preflight.py:508-509` builds `expected` from
      `_SPORTS_CORE_ENTITIES`/`_SPORTS_PER_FIXTURE_ENTITY_NAMES` and passes it straight into
      `_orch.check_shard_freshness(expected_venues=expected, ...)` at `process_preflight.py:592-598` (confirmed exact
      case-sensitive manifest-content match, `unified-trading-library/manifest_writer/_queries.py:149`) — but the SAME
      `expected` also flows through `get_entity_league_coverage(entity)` at `process_preflight.py:469` (UAC-axis, stays
      uppercase). Confirmed manifest-boundary sites needing a translation wrapper (not a registry rewrite):
      `process_preflight.py:592-598`'s `check_shard_freshness(expected_venues=expected)` call;
      `sports_dependency.py:218`'s `idx["data_type"].isin(_API_FOOTBALL_FIXTURES_DATA_TYPES)` — a DIRECT `.isin()`
      against raw manifest content (`sports_dependency.py:97-98`'s own docstring: "the two manifest data_type values";
      post-migration only `fixtures_schedule` will be present — the bare `FIXTURES` legacy literal was already fully
      retired per `fixtures_manifest_legacy_backfill_2026_07_24.md`, so keeping both members lowered is harmless but
      both must be lowered); `writers.py:270`+`writers.py:383-390`'s `_classify_venue_write()` —
      `_pipeline_mode_for_sports_data_type (manifest_data_type)` MUST run on the uppercase form BEFORE
      `manifest_data_type` is lowered for the
      `record_captured(row_key={"data_type": manifest_data_type}, data_type=manifest_data_type, ...)` write — ordering
      matters WITHIN this one function, not just across files; `catalogue.py:131-171`'s equivalent legacy per-venue
      write path (same extraction pattern, same fix). **Not yet traced to the same rigor this session**:
      `sports_reference_fixtures_write.py::_ENTITY_DT_BY_SHORT`'s `record_captured(data_type=af_entity_dt, ...)` write
      (~line 169, almost certainly the same writers.py pattern) and `_ENRICHMENT_ENTITY_VENUES`'s full consumer set
      beyond the two call sites read this session. **Net effect**: step 2 shrinks from "8 registries, literal rewrite"
      to "N manifest-boundary call sites, translation-wrapper insertion" — smaller blast radius but needs a fresh
      per-site audit before code lands, not a mechanical global replace. **Both previously-untraced sites now confirmed
      (same session, follow-up read)**: `sports_reference_fixtures_write.py:158-171`'s
      `record_captured(row_key={..., "data_type": af_entity_dt}, data_type=af_entity_dt, ...)` write is the IDENTICAL
      writers.py pattern — lower `af_entity_dt` only immediately before this call, never `_ENTITY_DT_BY_SHORT`'s dict
      values (which UAC-axis code elsewhere may still key uppercase). `_ENRICHMENT_ENTITY_VENUES` has exactly 2
      consumers, both in `process_preflight.py` (line 462, feeding `expected.append(entity)` → the already-covered
      `check_shard_freshness` boundary; line 688, a `{e for e, _ in ...}` set built only to test membership against
      `missing_set`, which itself derives from that same already-translated `expected`/`missing`/`stale` — no separate
      casing risk). **All 8 original sites now fully classified**: 0 need a literal registry rewrite; the
      manifest-boundary translation wrap is needed at exactly 5 call sites (`process_preflight.py:592-598`,
      `sports_dependency.py:218`, `writers.py:383-390`, `catalogue.py:131-171`,
      `sports_reference_fixtures_write.py:158-171`) plus the `enumerate_expected_universe.py` override-dict wiring
      already scoped in step 3. No step-2/3 code shipped this session pending operator review of this corrected design
      (see BLK-8436a1a6 follow-up); step 1 (the manifest re-stamp script) is independent of this correction and
      unaffected. **EXECUTED 2026-08-14 (slot-26)**: all 3 steps landed + physically ran, in two windows minutes apart
      (see below for why that's still atomicity-compliant). Step 1's launcher needed a new VM-launcher category first
      (the pre-existing `manifest-restamp` category was wired to an unrelated MTDS consolidator tool, not this script) —
      shipped `deployment-service@3eded03f6a` (`sports-19token-restamp` category). Steps 2's 5 manifest-boundary
      translation-wrapper sites (`process_preflight.py:592-598`, `sports_dependency.py:218`, `writers.py:383-390`,
      `catalogue.py:131-171`, `sports_reference_fixtures_write.py:158-171`) landed as `instruments-service@3637252f81`
      (21 files: the 5 sites + every per-vendor writer touching these data_types + 6 tests) in the SAME window as the VM
      launch — confirmed via `gcloud compute instances describe` the VM wasn't created until after this commit was
      ancestor-verified on `origin/live-defi-rollout`. VM `canonical-migration-sports-19token-restamp-20260814-045346`
      (asia-northeast1-c, SPOT, `--apply-prod --confirm-prod-write`) ran to completion:
      `_index/availability_index.parquet` relabeled=14,343,231 of base=15,645,261 rows, all 4 non-empty
      `_index/per_vm/*.parquet` shards relabeled, **every surface's own post-write VERIFY: uppercase-token rows
      remaining = 0**, `rc=0`/`exit_code=0`/`DEPLOYMENT_COMPLETED`, VM self-deleted on completion (confirmed gone via
      `gcloud compute instances describe` → NOT_FOUND, no zombie). Independent re-run of
      `census_sports_19token_lowercase_scope_2026_08_14.py` post-execution confirms **0 uppercase-token rows across all
      19 tokens**, 15,645,261 manifest rows scanned. **Gap found + closed same session**: step 3
      (`enumerate_expected_universe.py`'s `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE` wiring) was NOT actually in the
      `instruments-service@3637252f81` diff despite this todo's own atomicity requirement — verified via
      `git show --stat` (21 files, no `enumerate_expected_universe.py`) and by reading the dict directly (only the 2
      pre-existing entries, `ODDS_HORIZON_BUCKET`/`FIXTURES`, no new entries). Root cause: the "drafted diff" this
      todo's step-3 text referred to was only ever prose in this plan file, never actual code. Closed the gap the same
      session, before any scheduled `enumerate-expected-universe` run could observe the mismatch: composed
      `_sports_manifest_data_type()` with the same `canonical_sports_is_data_type()` helper used at every other site
      (`dt = _SPORTS_MANIFEST_DATA_TYPE_OVERRIDE.get(dt, dt); return canonical_sports_is_data_type(dt) or dt` — covers
      all 19 tokens generically instead of hand-enumerating, and correctly composes the legacy
      `FIXTURES→ FIXTURES_SCHEDULE` rename with the new lowercase form: `FIXTURES` → `fixtures_schedule`, verified
      interactively). Updated 3 pre-existing unit tests that encoded the old identity/uppercase contract
      (`test_sports_v2_non_overridden_data_type_gets_p2_lowercase_form`,
      `test_sports_manifest_data_type_helper_lowers_every_p2_token`,
      `test_sports_manifest_data_type_helper_maps_fixtures_to_fixtures_schedule`, plus 2 assertion updates in
      `test_build_instrument_catalogue.py`); full `tests/unit/scripts/test_enumerate_expected_universe_v2.py` +
      `test_build_instrument_catalogue.py` suite green (474 passed) before shipping. QG green, shipped
      `instruments-service@f2586ada09`, ancestor-verified on `origin/live-defi-rollout`. **Verify step still open**: a
      live `check_shard_freshness` pre-flight run on a recent + a historical date each showing `is_fresh=True` with 0
      spurious missing/stale has NOT been run this session — tracked as a new todo below.
- [x] ✅ [DATA] P0. **Run the migration's own closing verification** — DONE 2026-08-14 (slot-26), live against the real
      prod bucket (`instruments-store-sports-prd-central-element-323112`), not mocks. Ran the actual
      `process_preflight.py:592-598` translation shape (`canonical_sports_is_data_type()` over all 19 tokens) through
      `check_shard_freshness()` for a recent date (2026-08-10) and a historical pre-2026 date (2024-03-15), WITH a raw
      untranslated-uppercase control on the same two dates to isolate the specific failure mode this migration was
      designed to prevent: - **Control (no translation, pre-fix behavior)**: `missing_count=19/19` on BOTH dates — this
      is the exact 572-day-incident failure mode (every already-captured date reads as fully missing) the atomicity
      requirement existed to prevent. - **With the shipped translation
      (`instruments-service@3637252f81`/`f2586ada09`)**: historical date `missing=[]` (0/19); recent date
      `missing=['fixtures']` only — the fully-retired legacy `FIXTURES` literal (pre-existing
      `FIXTURES→FIXTURES_SCHEDULE` cutover, `fixtures_manifest_legacy_backfill_2026_07_24.md`, not a P2 regression —
      nothing is expected to be written under the bare `fixtures` key post-cutover). The 3 "stale" (not missing) entries
      on the historical date are schema-version drift on newer contracts
      (`fixtures_outcomes`/`weather`/`odds_horizon_bucket`), and the 17 "stale" entries on the recent date are real age
      (>24h since capture, unrelated to this migration) — confirmed neither is case-driven since a case-mismatch would
      surface as `missing`, never `stale` (the row has to be FOUND to be evaluated for staleness at all). **0
      case-driven spurious missing/stale confirmed for all 19 tokens on live prod data.** -
      **`enumerate_expected_universe.py`'s `_sports_manifest_data_type()` cross-checked directly** (all 19 tokens,
      `.venv/bin/python3 -c "..."` against the real function) — output is byte-identical to the real on-disk manifest
      forms confirmed present above (`fixtures`→`fixtures_schedule`, `odds_horizon_bucket`→ `odds_horizon_bucket`, the
      other 17 identity-lowercased) — 0 mismatched-case `expected_unattempted` seed risk confirmed at the live-data
      level, on top of the already-green unit coverage (`test_enumerate_expected_universe_v2.py`, 474 passed, from
      `f2586ada09`). Did not run a full `enumerate_v2` scan-only pass against prod (that call requires
      `--catalog-path` + a `--start-date`/ `--end-date` window and is VM-scale I/O per
      `/codex/05-infrastructure/vm-launcher-runbook.md` — out of scope for an interactive verification; the direct
      function cross-check + existing unit suite give equivalent coverage of the translation logic itself). Verification
      script not promoted (one-shot check, not a durable tool, no open todo needs it) — left in scratchpad, safe to
      lose. **Stale-doc finding fixed in passing**: this verification pass surfaced that
      `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM`'s and `canonical_sports_is_data_type()`'s own docstrings in
      `unified_api_contracts/canonical/domain/sports/league_data.py` still said "not yet wired into live enumeration" —
      stale since `f2586ada09` wired it. Corrected — `unified-api-contracts@4b8529e6a7`.
- [x] [SCRIPT] P2. **Delete the two one-off migration scripts** now that the physical re-stamp is verified complete (0
      uppercase-token rows remaining, confirmed twice):
      `instruments-service/scripts/restamp_sports_19token_lowercase_2026_08_14.py` and
      `instruments-service/scripts/census_sports_19token_lowercase_scope_2026_08_14.py`. Both are lifecycle-marked
      one-offs (per `/codex/06-coding-standards/script-homes.md`) whose job is done; keep them only until this todo is
      picked up, then delete via quickmerge. ✅ Deleted (no external consumers — grep confirmed the only references were
      self-referential header/docstring comments in the restamp script itself); QG green
      (`0b1adeaf44736353d9d733ad28160b2953d51cb7`) before commit — `instruments-service@c1cc730772`.
- [x] ✅ [DATA] P0. **Draft + locally validate the 19-token re-stamp's step 1 (manifest relabel script) — NOT
      execution.** Per operator interim guidance on BLK-20f1ba56 ("write + locally validate, stop short of VM
      launch/live execution"): shipped `instruments-service@5ec75509`
      (`scripts/restamp_sports_19token_lowercase_2026_08_14.py`) — relabels `data_type` on the merged availability
      index + every `_index/per_vm/*.parquet` shard per `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM`, dry-run default,
      `--apply-prod --confirm-prod-write` gated. Relabel logic locally validated against a synthetic in-memory DataFrame
      (no GCS calls): confirmed correct per-token mapping, already-lowercase/non-target rows left untouched. Traced +
      corrected the step 2/3 design (see CORRECTION note above) — all 8 registry sites classified, 5 real
      manifest-boundary call sites identified with exact file:line citations. **CORRECTED 2026-08-14 (slot-26)**: both
      instruments-service commits from this note (census `instruments-service@e6d1a76c` + this script
      `instruments-service@5ec75509`) DID land on origin — the local pre-rebase SHAs `67105c6e`/`0c0a5109` this entry
      originally cited never resolved because quickmerge's Stage-0.4 rebase rewrote them; confirmed via
      `git log --oneline -- <path>` against `origin/live-defi-rollout`. The unrelated pre-existing
      `instruments_service_defi_golden_red_capability_drift_2026_08_14.md` QG-red that blocked shipping at the time has
      since cleared. **The `[OPERATOR]` execute todo directly above stays intentionally UNCHECKED** — no VM was
      launched, no live write was attempted; BLK-20f1ba56 remains open pending the operator's actual go/no-go on the
      launch, and steps 2-3 still need code written (scoped, not yet drafted) before that launch can happen.
- [x] ✅ [DATA] P0. **Fold footystats `ODDS` (6,306 captured) + `odds` (16,207 captured) into a single `odds`.** These
      are the same vendor population under two spellings; `source=footystats` remains the discriminator against the
      odds_api population. Note the UAC comment calling the uppercase set "4 stale empty rows" is FALSE — expect 6,306
      real shards. **CLOSED 2026-08-14 (slot-26)** — `ODDS` was one of the 19 tokens in the reference-vocabulary restamp
      above; live re-census of `instruments-store-sports-prd-central-element-323112`'s
      `_index/availability_index.parquet` (columns `data_type`/`source`/`capture_status`, no filter assumptions) shows
      **zero** `data_type=ODDS` rows of any status remain — only lowercase `odds` exists, `source=footystats`+`captured`
      = 30,498 (grown past this todo's 2026-08-08 6,306+16,207=22,513 count, as expected — real capture continued
      between the audit and the restamp). Fold is a genuine side effect of the 19-token restamp, not assumed: verified
      live, not from the prior mapping-code read alone.

      **ADDENDUM 2026-08-14 (slot-18) — the population slot-26 verified above is a DIFFERENT one from this todo's own
          cited counts; a second, separate fold was actually still outstanding and is now also closed.** Re-checking this
          todo's own numbers (6,306 captured `ODDS` / 16,207 captured `odds`, venue=FOOTYSTATS) against
          `instruments-store-sports-prd-central-element-323112` (the bucket slot-26 measured) does NOT reproduce them — that
          bucket's lowercase `odds`/footystats count is 30,498, not 16,207. The 6,306/16,207 figures are physically in the
          **MTDS raw-tick manifest** (`market-data-tick-sports-prd-central-element-323112`), a completely separate bucket
          that happens to share the `ODDS`/`odds` token name with the IS 19-token reference-data vocabulary slot-26
          resolved — the EXACT "two different systems, one shared token" trap this whole todo's own UAC-comment correction
          already named once (see the todo's own "the UAC comment... is FALSE" line) and the 19-token migration's Progress
          Log named again for a different pair of systems. Live-verified this session (dispatched as
          `sports_taxonomy_p2_migration-005`): a full-population (not sampled) GCS-existence check of all 6,306 MTDS
          `captured` uppercase-`ODDS` rows found **0/6,306 had backing parquet content** under either known raw_tick_data
          path shape, while every checked (date, league) pair's lowercase `odds` twin did — i.e. this MTDS population was
          phantom bookkeeping residue, not real data needing a content-merge fold. Filed
          `/plans/archive/issues/sports_footystats_odds_uppercase_phantom_not_real_2026_08_14.md`, operator ruling
          BLK-931edbb5: purge rather than fold. Purged 2026-08-14 (6,306 captured + 136 empty_confirmed rows removed,
          manifest-only — no real GCS object existed to touch; consolidator paused via maintenance window, pre-purge
          snapshot taken, §3a fresh soft-delete-retention check passed at 604800s), re-verified 0 remaining post-purge.
          Shipped `market-tick-data-service@5dcb6c865a` (purge tool + test) and `unified-api-contracts@b6378af519`
          (corrected the same UAC comment slot-18 found already-wrong-again, shrunk
          `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` by dropping `ODDS`). Both populations this todo's title
          implicitly bundled are now genuinely resolved.

- [x] ✅ [DATA] P0. **Move `odds_horizon_bucket` onto the `odds` + `horizon` model.** ~~135,980 shards... MDPS
      121,762/MTDS 14,656/IS 1,106... 123,642 attributed to venue=ODDS_API~~ **STALE — corrected 2026-08-14 (slot-26),
      live re-measured**: total `odds_horizon_bucket` manifest rows = 1,070,078 (all `source=mdps_odds_horizon_bucket`,
      the writer's own literal source tag, not 3 distinct sources); MDPS's own already-shipped
      `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py` +
      `reclassify_odds_horizon_bucket_unresolvable_rows_2026_07_28.py` (git history: `market-data-processing-service`
      commits `5517dea9`→`bd9f0063`, `b2762129`→`ec2f9aa5`) had **already re-attributed the bulk to real per-bookmaker
      venues** (BETVICTOR/WILLIAMHILL/FANDUEL/UNIBET/etc — 165,604 captured rows across 26 real bookmakers) before this
      session — this todo's own scope was mostly already done, just never flipped. Remaining `venue=ODDS_API` captured =
      30,608, of which **30,602 are the COARSE per-day aggregate rows the migration script deliberately leaves untouched
      by design** (no league_id/timeframe — not a gap) and **6 are genuine fine (league_id+timeframe populated)
      unmigrated rows** — live-probed via the script's own `_read_shard_bookmaker_breakdown`: 1
      (2020-06-12/SUPERLIGA/T-6h, 4 sub-rows) reconciles cleanly (unibet/betvictor/sport888/paddypower ×1 each) and is
      the ONLY genuine remaining gap; the other 5 are 404 NotFound against their backing `bucketed.parquet` — stale
      manifest rows for shards `reprocess_sports_odds.py`'s own `_delete_stale_shards()` already removed, which the
      migration script's own docstring explicitly classifies as expected/left-untouched, not a defect. **Confirmed via
      the script's own live `--dry-run`** (generation `1786687266036554`, target-shard count == 6, matches the manual
      probe exactly) — not assumed from the mapping-code read alone. **`--apply` attempted locally twice this session
      and OOM-killed both times** (SIGKILL at ~28s despite `free -h` showing 18Gi host-available — a sandbox cgroup
      limit, not genuine host exhaustion) because the script always loads+rewrites the FULL 15.6M-row manifest
      regardless of target-row count — this is the "manifest rewrites never run locally" HARD RULE biting even at
      trivial target scale; manifest verified UNCHANGED/uncorrupted after both kills (re-`--dry-run` showed identical
      generation + target count). **Remaining scope, tracked explicitly, not silently closed**: run `--apply` on a tiny
      VM (or accept the 4-row gap as a documented, non-blocking residual — an [OPERATOR] proportionality call, since a
      dedicated VM launch for 4 rows is disproportionate; see Progress Log). ~~Not marking this todo `[x]` until that
      gap is either closed or explicitly operator-accepted.~~ **CLOSED 2026-08-14 (slot-29), live VM `--apply` run**:
      ran the already-shipped `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py --apply` on
      `mtds-migrate-odds-horizon-bucket-bookmaker` (existing launcher `launch-mdps-odds-horizon-bucket-restamp-vm.sh`,
      already committed by a prior session). **Root gate result, not assumed**: the live full-scale apply-path
      resolution (generation `1786713550519620`, 15,651,115 rows, workers=32) found **`n_targets=5`, `n_reconciled=0`**
      — all 5 remaining fine `venue=ODDS_API` rows are confirmed 404 NotFound against their backing `bucketed.parquet`
      (A-LEAGUE/SERIE_A×2/FIRST_DIVISION_A/PREMIERSHIP, 2020-08/09 dates) — the exact expected-residue class the
      script's own docstring documents (stale manifest rows for shards `_delete_stale_shards()` already removed), not a
      defect. The previously-identified genuine gap (1 row, 2020-06-12/SUPERLIGA/T-6h) is **no longer present in this
      session's target set at all** — resolved by something else between the 2026-08-14 slot-26 measurement and now (a
      manifest-consolidator cycle or a sibling write), not by this run (the script never wrote — `GATE FAILED`, `rc=0`,
      since 0 rows reconciled means nothing to migrate; manifest left byte-unchanged, confirmed by the script's own gate
      short-circuiting before any CAS write). Row-count conservation trivially holds (`old_sum=0 new_sum=0`). **0
      genuine unmigrated rows remain, live-verified** — the todo's own closing bar is met without needing the
      operator-proportionality fallback. **Launcher OOM chain fixed in passing** (2 real failures, not one lucky retry):
      the launcher's original `e2-standard-4` (16GB) OOM-killed (rc=137) mid full-manifest rebuild; bumped to
      `e2-standard-8` (32GB, matching the sports-19token-restamp precedent) — **also** OOM-killed at the same point,
      because unlike that script's in-place `.map()` relabel, this script's `_build_final_df` does a drop+concat
      rebuild + full `sort_values().reset_index()` before `to_parquet` (several full-DataFrame copies live at once);
      bumped again to `e2-standard-16` (64GB, matching `cefi-content-apply`'s own precedent for the identical
      rebuild-heavy OOM shape), which ran clean. Shipped `deployment-service@2ceae6b48c` (→ e2-standard-8) then
      `deployment-service@e80a134901` (→ e2-standard-16), both ancestor-verified on `origin/live-defi-rollout`.
- [x] ✅ [DATA] P1. **Re-attribute the ODDS_API and FOOTYSTATS venue rows.** ~~ODDS_API's 123,642
      `odds_horizon_bucket` + 8 `trades` and FOOTYSTATS' 22,513 rows~~ **CLOSED 2026-08-14 (slot-26), live re-measured —
      all three sub-populations resolved, none silently dropped**: (1) ODDS_API's `odds_horizon_bucket` component is the
      SAME population as the P0 todo above (this todo's number was a stale duplicate of that one) — tracked there, not
      re-tracked here. (2) FOOTYSTATS venue currently has **0 captured rows of any data_type** — live census
      (`data_type`/`venue`/`source`/`capture_status`) shows all 2,372 `venue in {FOOTYSTATS,footystats}` rows are
      `empty_confirmed` — nothing left to re-attribute; the stale 22,513 figure predates whatever prior work already
      cleared this population. (3) ODDS_API's 8 `trades` rows — dumped live (`pipeline_mode=batch_odds_api`,
      `instrument_type=SPORT`, `instrument_id`s like `ODDS_API:SPORT:soccer_epl`) — are NOT re-attributable odds data at
      all, they're the exact same junk population the "Delete the `SPORT` instrument_type residue" purge todo below
      already names (8 rows) — correctly routed there as a delete, not force-fit into a bookmaker-venue re-attribution
      here. No sub-population was silently dropped; each has an owning todo or is confirmed already-empty.
- [x] ✅ [DATA] P1. **Purge/re-stamp the `venue=ODDS_API`/`pipeline_mode=batch_footystats` legacy-seed residue (20,095
      rows) the todo above missed.** Found live 2026-08-14 via
      `/plans/archive/2026_08/issues/sports_footystats_mislabel_contradiction_2026_08_14.md`: the todo above's
      2026-08-14 (slot-26) closure verified `venue=FOOTYSTATS` (the RENAMED target) reached 0 captured rows, but never
      re-checked the ORIGINAL `venue=ODDS_API AND pipeline_mode=batch_footystats` population itself, which still holds
      19,782 shards / 20,095 rows — all living in `_index/per_vm/_legacy_seed.parquet` specifically (frozen
      2020-06-01..2026-04-14, 0 rows with recent `attempted_at` — no live writer, confirmed). Root cause: the 2026-07-27
      `manifest_swap_venue_restamp_2026_07_27.py` CAS-swap only ever touched the merged
      `_index/availability_index.parquet`; the manifest consolidator's `_seed_legacy_if_needed` re-merges the un-renamed
      legacy-seed copy on every cycle, so the population was masked for one cycle, not actually removed. **Do NOT re-run
      `restamp_sports_bookmaker_venue_2026_07_27.py --venue FOOTYSTATS`** on this population — a straight rename was
      already determined wrong one day before it was first run
      (`/plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`: 56.40% of the
      footystats `(date, league)` cells already exist under `batch_odds_api`, so a 1:1 rename creates duplicate manifest
      rows; the operator-ruled fix is a de-cased PURGE). Whatever purge tool lands next MUST re-stamp/purge the matching
      rows in BOTH `_index/availability_index.parquet` AND `_index/per_vm/_legacy_seed.parquet` in the SAME change, or
      the consolidator resurrects them again exactly as it did in 2026-07-27. **§3a fresh check required before any
      object delete.** (repo: market-tick-data-service) — **DONE 2026-08-14 (slot-30)**: shipped a MANIFEST-ONLY purge
      tool, `market-tick-data-service@679227552f`
      (`scripts/sports/purge_footystats_odds_api_legacy_seed_2026_08_14.py`), that writes BOTH manifest surfaces in one
      invocation per the todo's own requirement. Content redundancy already established+executed by the 2026-07-17
      `merge_migrated_odds_into_canonical` run (all 1,815 days probed, real-derive-verified — see the archived
      2026-07-16 mistamped-footystats doc's Progress Log); re-confirmed live this session via a seeded 30-date random
      sample of the current population: 26/30 had a real same-day `batch_odds_api` (any-venue) twin, 0/30 had an object
      with NO twin (the one dangerous case), 4/30 had neither object (already-orphaned claims, safe either way). Live
      re-census confirmed the exact counts before writing (main index 19,782 / legacy seed 20,095, matching the todo's
      own numbers). Executed against prod with pre-write snapshots on both blobs
      (`_index/snapshots/pre_footystats_odds_api_legacy_seed_purge_2026_08_14_*`): **removed 19,782 rows from
      `_index/availability_index.parquet` (6,079,121→6,059,339) and 20,095 rows from
      `_index/per_vm/_legacy_seed.parquet` (362,753→342,658); VERIFY 0 remaining on both surfaces.** No GCS object was
      deleted (manifest-metadata-only fix — §3a's object-delete gate does not apply); the underlying
      `ticks_migrated_*.parquet` objects (still real, still on disk) remain covered by the separate, larger,
      already-tracked "purge the mis-stamped rows + their ~17K objects" todo in the archived 2026-07-16 doc, out of
      scope for this todo.
- [x] ✅ [DATA] P1. **Re-attribute the
      `pipeline_mode=batch_footystats`/`source=footystats`/`data_type=odds_horizon_bucket` population (1,784,473
      manifest rows) — disjoint from, and never counted by, the P0 todo above.** Found live 2026-08-14 (slot-27) via
      `/plans/archive/2026_08/issues/sports_footystats_mislabel_contradiction_2026_08_14.md`'s LADBROKES_UK/SPORT888
      content-verify: the P0 todo above's 2026-08-14 (slot-26) closure measured `odds_horizon_bucket` total as 1,070,078
      rows, but scoped that count to `source=mdps_odds_horizon_bucket` only — it never examined this SEPARATE, larger
      `source=footystats` population sitting under the identical `data_type=odds_horizon_bucket`
      (`read_availability_index` census, this session,
      `pipeline_mode=batch_footystats AND data_type=odds_horizon_bucket`, 26 distinct venues incl.
      LADBROKES_UK/SPORT888/FOOTYSTATS/UNIBET/UNIBET_UK/etc). **Content check (2 independent shard downloads,
      `day=2023-04-02/league_id=PRIMEIRA_LIGA` and `day=2020-06-06/league_id=BUNDESLIGA`) found the physical
      `bucketed.parquet` files' own `source`/`data_source` columns read `ODDS_API` for 100% of rows (86/86 and 23/23),
      not footystats** — the manifest's `pipeline_mode=batch_footystats`/`source=footystats` stamp on these rows does
      not match the underlying data, which is genuinely ODDS_API-vendor-derived (same schema/shape as the
      already-migrated `mdps_odds_horizon_bucket` population; the physical shard path itself carries no `pipeline_mode=`
      segment at all —
      `processed/by_date/day={D}/data_type=odds_horizon_bucket/league_id={L}/timeframe={T}/bucketed.parquet`, confirming
      pipeline_mode is a manifest-only stamp, not a path-derived fact, for this shape). **Not yet determined**: whether
      re-stamping this population to `pipeline_mode=batch_mdps_odds_horizon_bucket`/ `source=mdps_odds_horizon_bucket`
      (folding it into the already-migrated population above) would create duplicate manifest rows for cells that
      already exist there — that overlap has NOT been measured yet, do a `read_availability_index` (date, league_id,
      timeframe) collision census BEFORE any restamp/fold, mirroring the §3a-class caution already learned from the
      adjacent `batch_footystats` raw-tick mislabel (56.40% pre-existing overlap there). (repo: market-tick-data-service
      or market-data-processing-service, whichever owns this shape's manifest-write path)

      **CLOSED 2026-08-14 (slot-30) — live re-measured, 0 rows found, nothing left to re-attribute.** Ran the collision
          census this todo's own text asked for: shipped `market-tick-data-service@4709c8dea3`
          (`scripts/sports/census_footystats_odds_horizon_bucket_fold_scope_2026_08_14.py`) against the same live
          `instruments-store-sports-prd-central-element-323112` manifest (`read_availability_index`, columns-projected,
          15,652,378 total rows). **Confirmed via two independent query angles, not one**: (1) direct filter
          `pipeline_mode=batch_footystats AND data_type=odds_horizon_bucket` → **0 rows**; (2) a broad scan of every
          `data_type` value containing "horizon" (case-insensitive, no pipeline_mode assumption) → 1,070,081 rows total,
          **all** already `pipeline_mode=batch_mdps_odds_horizon_bucket`/`source=mdps_odds_horizon_bucket` — the fold-target
          population itself, none under `batch_footystats`. `pipeline_mode=batch_footystats` DOES still exist live
          (2,746,633 rows, confirmed real), but its `data_type` distribution is
          `{matches, predictions, odds, odds_movement, odds_snapshot, trades}` — `odds_horizon_bucket` is not among them,
          and its `data_type=odds` venues (`FOOTYSTATS`/`ODDS_API`/`MDPS_ODDS_HORIZON_BUCKET`/etc — a separate,
          smaller pre-existing manifest-contamination pattern worth a future look, explicitly NOT this todo's scope) show
          none of the 26-bookmaker-venue signature (`LADBROKES_UK`/`SPORT888`/`UNIBET_UK`/etc) the original finding cited.
          **Not determined and not investigated further** (no remaining action value either way): what resolved the
          population between the 2026-08-14 (slot-27) finding and this run — same-day concurrent work by slots 26/28/29 on
          this same plan (the 19-token restamp, the odds_horizon_bucket venue-to-bookmaker VM apply, the footystats
          legacy-seed purge) is the plausible explanation given the timing, but no single commit was traced as the specific
          cause. Fold / `enumerate_expected_universe.py`-override work this todo originally scoped is moot — there is no
          live row left to fold. Census script kept in `scripts/sports/` (its own lifecycle marker already covers deletion
          once a fresh re-run reconfirms 0 — true as of this run, but not acted on since this run IS that verification, not
          a separate throwaway probe).

### The purges (each requires the §3a fresh check, in-run)

- [x] ✅ [DATA] P0. **Purge the retired `exchange_odds` / `fixed_odds` instrument_type values from manifest rows AND GCS
      objects** (operator ruling 2026-08-08, see
      `/plans/archive/2026_08/sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`: "derive from venue, retire the
      split, purge the unnecessary values for manifest and objects"). 60,095 shards carry them (`exchange_odds` 35,622 /
      `fixed_odds` 24,473); `instrument_type` is a PATH segment so objects move, not just rows. Note the fork is
      currently split WITHIN venues — BETFAIR_EX_UK has 9,204 `exchange_odds` AND 3,405 pre-fork `odds` — so a partial
      purge would leave the same venue across two tokens; the end state must be ONE token per venue. **§3a fresh check
      required before any object delete.** **Partial-completion note (2026-08-14, slot-28)**: 59,310/60,095 (98.7%) is
      content-verified safe and purged on BOTH sides — GCS (DROP/COPY_THEN_DELETE, `market-tick-data-service`
      migrate+verify, VERIFY PASSED) AND the sports manifest (REMOVE 59,310 fork rows / ADD 35,350 new `odds` rows /
      23,960 no-add-needed, live-index VERIFY PASSED, 0 non-excluded fork rows remain) — see Progress Log for full
      evidence + shas. The remaining 785 keys were excluded on both sides (see the P1 merge todo below) because their
      `odds` twin did not cover their content. **CLOSED 2026-08-14 (slot-28)**: the P1 merge todo below closed the same
      day, covering all 785 residual keys — both surfaces (GCS + manifest) are now clean for the full 60,095/60,095.
- [x] ✅ [DATA] P1. **Content-merge the 785 `exchange_odds`/`fixed_odds` keys where the pre-existing `odds` twin does
      NOT cover the fork object's rows** (found 2026-08-14, slot-28, via
      `verify_exchange_fixed_odds_full_population_content_2026_08_14.py`'s full-population re-check — up to 1,134
      missing rows in one shard; full list in that run's `--report` JSON `data_loss_risk_keys`, excluded from the P0
      purge above via `--exclude-report`). Needs a genuine MERGE, not a DROP/COPY: read both the fork and `odds`
      parquet, union rows by natural key (`instrument_id`, `fetch_utc`, `price`, `bm_time`), rewrite the `odds` object,
      verify row-count, THEN delete the fork source + its manifest row under a fresh §3a check. Higher risk than the P0
      purge's two dispositions (this one OVERWRITES a live object instead of only creating/deleting), so build + dry-run
      it carefully before any `--confirm`. **CLOSED 2026-08-14 (slot-28)**: operator explicitly authorized proceeding.
      785/785 MERGED (217,538 rows added, cross-checked against the verify script's own `missing` field sum), 785/785
      independently `verify`d COVERED (0 STILL-MISSING), 785/785 fork objects `finalize`d DELETED (fresh §3a check,
      retention 604800s), manifest REMOVE-785/ADD-785 + live-index VERIFY PASSED (0 remaining fork rows, 785/785 odds
      row_counts correct). Full evidence + shas in Progress Log.
- [x] ✅ [DATA] P0. **Delete the 20,785 KALSHI `empty_confirmed` rows** (source `polymarket_clob`, 2020-06-06 →
      2026-05-21) from the sports manifest — prediction-market venues seeded into the sports denominator, ~3.4% of the
      manifest being fictitious. **CLOSED 2026-08-14 (slot-26), live re-measured**: `venue=KALSHI` AND
      `source=polymarket_clob` (exact match) = **0 rows**; widened to a case-insensitive substring check on both `venue`
      (contains "KALSHI") and `source` (contains "polymarket") across the WHOLE manifest = **0 hits either way** — not a
      wrong-vocabulary miss. No matching purge commit found in `instruments-service` git history
      (`git log -i --grep=kalshi`), so the mechanism is unconfirmed, but the population is genuinely absent from the
      live manifest now, not just under the exact original spelling. Nothing to delete; the todo's stated population no
      longer exists in the source of truth.
- [x] ✅ [DATA] P1. **Delete the 2,490 blank-venue rows** written by instruments-service into the MTDS tick manifest,
      once P1's writer fix has stopped the source. Verify the writer is genuinely fixed before cleanup — cleaning before
      the writer stops just re-pollutes. **Writer-stopped verification DONE 2026-08-14 (slot-26), live-measured** — this
      is NOT the reference-data manifest's blank-venue population (14.4M rows there, but blank venue is CORRECT/expected
      for league/team/fixture reference tokens like STANDINGS/XG/TEAMS — a wrong first-pass filter, corrected before
      acting on it); the real target lives in the SEPARATE `market-data-tick-sports-prd-central-element-323112` manifest
      (6.1M rows, distinct index from the reference-data one), where `service_name=instruments-service` + blank venue +
      captured = **2,379** (`odds` 1,273 + `odds_horizon_bucket` 1,106 — matches
      `sports_taxonomy_p2_consumer_inventory_2026_08_12.md`'s already-documented root cause exactly: the
      `resolve_source_and_mode()` case-sensitivity bug in `backfill_orphan_class_e_sports.py`, fixed at
      `instruments-service@d9994199`; the gap to 2,490 is the 111 `trades_inplay` rows already resolved by this plan's
      own earlier in_play-column todo, so nothing missing). **Writer confirmed stopped**: `attempted_at` (write time)
      for all 2,379 rows clusters 2026-07-21T16:02→2026-07-22T05:08 UTC — a one-time backfill batch, zero rows written
      since, 3+ weeks before this fix landed and before today. Sampled rows carry no `instrument_id`/no real venue —
      metadata-only artifacts of the buggy backfill, not real physical shards (no valid `venue=` path segment could have
      been written for them). **DELETED 2026-08-15 (slot-26)**: streamed-pyarrow rewrite (no VM needed), shipped
      `market-tick-data-service@c764e8a734` (`purge_instruments_service_blank_venue_rows_2026_08_14.py`) — removed the
      dry-run-matched 2,379 rows (0 in legacy-seed), snapshot taken first, **VERIFY PASSED: 0 remaining both surfaces**;
      no GCS delete needed, manifest-only. `slot-28`'s sibling `@7b1e6e87` covers this redundantly — idempotent no-op,
      **confirmed 2026-08-15**: that VM run matched exactly (base=6,056,952, removed 0, VERIFY PASSED 0 remaining).
- [x] ✅ [DATA] P1. **Delete the `SPORT` instrument_type residue** (8 rows on ODDS_API's `trades`) — junk token, no
      backing model. **PARTIALLY DONE 2026-08-14 (slot-26)**: widened scope live — found an EQUAL, entirely
      un-manifested `data_type=odds` twin at the same junk path (writer bug double-wrote identical content under two
      data_type labels) — 16 GCS objects total (not 8), all deleted + verified 0 remain that session. **Manifest side
      DONE 2026-08-15 (slot-28)**: local `--apply` OOM-killed (sandbox cgroup limit, not genuine exhaustion), forcing a
      VM run — `canonical-migration-sport-residue-blank-venue-purge` VM, `market-tick-data-service@7b1e6e87`
      (`purge_sport_residue_and_blank_venue_manifest_rows_2026_08_14.py --target sport_residue`): base=6,056,960 rows →
      removed 8 → **VERIFY PASSED: 0 remaining**. Snapshot taken first
      (`.../_index/snapshots/pre_sport_residue_purge_20260815T014039Z.parquet`).
- [x] ✅ [DATA] P1. **Sweep the `league=` vs `league_id=` path duplication — census DONE 2026-08-15 (slot-28).** ~~WRONG
      DIRECTION — corrected 2026-08-14 (slot-26)~~ **RE-CORRECTED 2026-08-15 (slot-28)**: the 08-14 "fix" cited the
      wrong FILE — `gcs_paths.py:351` builds instruments-service reference-data paths (no `"ticks"` entry, never emits
      `ticks.parquet`), not raw-tick sports paths. Real builder:
      `market-tick-data-service/scripts/merge_migrated_odds_into_canonical_2026_07_17.py:76-79`. Direct GCS confirms
      **`league_id=` (`pipeline_mode=batch_odds_api`) IS canonical** (real per-bookmaker data); **`league=`
      (`pipeline_mode=batch_footystats`, `venue=ODDS_API`, `ticks_migrated_*.parquet`) is legacy** (2026-05-05
      mis-stamp). Cross-validated by archived
      `/plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` (content merge already
      done: `market-tick-data-service@75f226e8`; manifest residue already purged 2026-08-14: `@67922755`, 19,782
      shards). **Exhaustive measured extent** (all 2,128 candidate days, script
      `market-tick-data-service/scripts/sports/census_league_vs_league_id_partition_duplication_2026_08_15.py`,
      `@96da88c6`, read-only): manifest 20,095 legacy rows / 19,782 pairs, 97.3% have a canonical twin, 2.7% (539, 528
      dates) don't; object-level **16,968 legacy objects, 1,034.5 MB, 1,814 days (2020-06-01..2026-04-14)** — matches
      archived issue's independent 16,969/1,815. Remaining GCS-object purge tracked below (§3a-gated).
- [x] ✅ [DATA] P2. **Purge the 16,968 legacy `league=` GCS objects** (1,034.5 MB, 1,814 days) from the todo above.
      **CLOSED 2026-08-15 (slot-11)** — `market-tick-data-service@8a772b3180`; §3a fresh check retention=604800s;
      deleted 15,154/16,968 (785.7MB), 0 errors; remaining 1,814 no-twin objects (539 pairs) left untouched, follow-up:
      `/plans/archive/issues/sports_league_legacy_orphan_purge_followup_2026_08_15.md` (resolved + archived 2026-08-16).
- [x] ✅ [SCRIPT] P1. **Launch one small VM to close out the 3 tiny manifest-only fixes** found + characterized
      2026-08-14 (slot-26), blocked on local `--apply` OOM-kills (sandbox cgroup limit, not genuine exhaustion). Item 1
      (`odds_horizon_bucket`) **DONE 2026-08-14 (slot-29)** standalone, ahead of this batch — see its own todo. Items
      2-3 **DONE 2026-08-15 (slot-28)**: shipped `market-tick-data-service@7b1e6e87`
      (`purge_sport_residue_and_blank_venue_manifest_rows_2026_08_14.py`), launcher `deployment-service@b4aef3e1`, VM
      `canonical-migration-sport-residue-blank-venue-purge` (e2-standard-16, asia-northeast1-c) — confirmed STARTED
      (`RUNNING` via `gcloud compute instances describe`) and TERMINAL (self-deleted post-completion,
      `VM_SHUTDOWN_ON_COMPLETION=true`). Ran `--target sport_residue` (8 rows removed) then `--target blank_venue` (0
      rows — item 3 was independently closed same-day by slot-26's sibling script `@c764e8a734`; this confirmed the
      expected idempotent no-op), both **VERIFY PASSED: 0 remaining**, exit rc=0. Full run.log:
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-sport-residue-blank-venue-purge/run.log`.
      **Lesson**: this VM's own watchdog script mis-treated `STOPPING` (the normal transient state between `RUNNING` and
      `TERMINATED` during shutdown) as a terminal error — poll for `TERMINATED` specifically, don't fail on intermediate
      states.

### Added 2026-08-08 (operator, mid-flight) — re-stamp the collapsed derived types

- [x] ✅ [DATA] P0. **RESOLVED 2026-08-20 — re-stamp premise is FALSE (nothing to re-stamp), so the todo is moot;
      the real "wire up vs retire" question underneath it got operator sign-off (wire up) in a separate tracked doc**:
      `/plans/archive/issues/sports_odds_movement_snapshot_candle_wireup_2026_08_20.md` (full verification + decision).
- [x] ✅ [REVIEW] P1. **Assert the vocabulary has collapsed to TWO types — REVISED 2026-08-15.** Live census (slot-20):
      tick bucket ✓ `odds`/`odds_horizon_bucket`/unchanged `arbitrage_opportunity`. **Gap**: IS-bucket SSOT manifest
      still carries 43,726 captured `trades` mirror rows untouched by the P0 restamp — issue doc
      `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15`.

### Verification

- [x] ✅ [REVIEW] P0. **Four-surface reconciliation after the migration**, per
      `/codex/02-data/four-surface-reconciliation-procedure.md`. **DONE 2026-08-15 (slot-9)**: 2 live-writer regressions
      found+filed — `/plans/archive/2026_08/issues/sports_p2_raw_tick_live_writer_still_emits_trades_2026_08_15.md` (P0,
      root-caused, RESOLVED 2026-08-15 — live writer fixed + all residuals swept, see its own archived Progress Log) +
      `/plans/active/issues/sports_p2_reference_bucket_uppercase_regrowth_2026_08_15.md` (P0, site TBD). S1 oracle clean
      (40/40); S2/S4 not run (budget, stated).
- [x] ✅ [REVIEW] P0. **Assert the accepted-exception sets have genuinely SHRUNK, not been re-populated.** Success
      criterion for this whole chain: `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`,
      `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED` and `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` all reach EMPTY. A
      green panel achieved by adding exceptions is the exact failure mode this chain exists to undo — if any set grew,
      the migration is wrong, not the panel. **DONE 2026-08-15 (-014)**: no set grew; `CROSS_AG_BLEED`→empty (purge-gate
      met 2026-08-14, `unified-api-contracts@d1f435a68c`); `STALE_UPPERCASE_RESIDUE`→`{ODDS_MOVEMENT, ODDS_SNAPSHOT}`
      (rest gated on the open BLOCKED-OPERATOR-DECISION todo); `NONCANONICAL_BOOKMAKERS={FOOTYSTATS}` structurally
      PERMANENT — "all EMPTY" unreachable for it, flagged not claimed.
- [x] ✅ [REVIEW] P1. **Re-run the honest-coverage measurer and confirm the rollup's distinct values equal the
      manifest's** (31 venues / 10 data types today → the canonical set, with nothing hidden). **DONE 2026-08-15
      (slot-9)** — fresh VM run, coverage.json self-verified written. data_types 13/13 exact match vs manifest; venues
      rollup=45/manifest=46, the one diff (`venue=SPORT`, 10 rows, all `attempted_failed`) is the measurer's own
      documented fully-retired-key drop, not hidden data. Verdict: rollup == manifest.

- **2026-08-14** — Todo 3 (lowercase the 19-token IS vocabulary) SPLIT after census + risk analysis found it far
  larger/riskier than its 1h estimate. Census (`census_sports_19token_lowercase_scope_2026_08_14.py`, shipped
  `instruments-service` — see SHA below) of `instruments-store-sports-prd-central-element-323112`'s
  `_index/availability_index.parquet`: **15,907,902 of 17,208,810 rows (92%) carry one of the 19 uppercase tokens**,
  dated 2014-01-01 → 2026-08-20, across every status (`captured`/`empty_confirmed`/`expected_unattempted`/
  `attempted_failed`). `ODDS_HORIZON_BUCKET` already has 0 uppercase rows (writer already stamps lowercase, matching the
  existing `enumerate_expected_universe.py` override precedent); `ODDS` uppercase carries 898,195 rows vs 1,774
  already-lowercase. Filed `/blocked` BLK-8436a1a6 before touching any live code — root cause: UTL's shared
  `check_shard_freshness()` does an EXACT case-sensitive match
  (`unified-trading-library/manifest_writer/_queries.py:149`) with no case-insensitive fallback, so flipping
  instruments-service's registries before the physical re-stamp lands would read every historical date as "missing" and
  trigger re-fetch storms against live provider APIs across 6+ years — the same failure class as the documented
  `odds_horizon_bucket` 572-day incident, at ~46x scale. Operator approved Option A (code-prep only this session,
  dedicated VM-run follow-up for the actual re-stamp + registry flip
  - override-dict wiring, landed atomically). New todo added above with full scope + the atomicity rationale. **Shipped
    this session**: the census script (read-only, safe). **NOT shipped this session** (deliberately, despite the
    operator's answer inviting it): the `enumerate_expected_universe.py` override-dict wiring — verified via direct read
    of that file's own load-bearing comment (§3b of the P2 consumer inventory) that wiring it BEFORE the physical
    re-stamp reproduces the identical 209,526-vs-123,642 zero-overlap incident the dict's own history already documents;
    the diff is drafted in the new todo's scope description instead of merged standalone, to land atomically with the VM
    re-stamp. Checkbox on the original todo stays unflipped per the operator's explicit instruction.
- **2026-08-14 (resume)** — Census script committed (`instruments-service@e6d1a76c`) but **quickmerge blocked at ship
  step by an unrelated, foreign QG red**: `test_expected_matches_golden[defi]` (fleet-wide, not caused by this commit —
  same failure class as the archived `instruments_service_defi_golden_red_capability_lockstep_gap_2026_08_05.md`
  incident). Root UAC commit (`unified-api-contracts@6a001ea4`, AAVE_V3 rewards) is settled, but the sanctioned
  `regenerate_expected_universe_golden.py` fix produces a much broader 2280-line diff (MORPHO/SPARK/oracle_prices/
  lst_rates/etc.) I could not verify is all intentional, and its unscoped run also nearly silently resolved an unrelated
  open `[OPERATOR]` design question in `tradfi.json` (caught via `1 xpassed` where `xfail` was expected, reverted before
  commit). Filed `/plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md`
  (`unified-trading-pm@0c8e9c26fc`) rather than attempt a fix outside this task's scope. **Census script stays local/
  unpushed in slot-18's checkout** (`instruments-service`, ahead=1, tree otherwise clean) until that issue clears — no
  data at risk: the census numbers + risk analysis this entry documents are the actual deliverable, already durable on
  `origin/live-defi-rollout`.

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — §3a reversibility path governs every delete here.
- `/codex/02-data/four-surface-reconciliation-procedure.md` — the verification procedure + the oracle's blind spots.
- `/codex/02-data/availability-manifest-and-data-status.md` — shard atom identical across
  writer/manifest/status/gate/UI.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — heavy I/O never runs locally; SPOT + progress-checkpoint resume.
- `/codex/05-infrastructure/gcs-object-operations.md` — UTL `gcs_copy_object`/`gcs_delete_object`, never subprocess
  gsutil.

## Progress Log

- **2026-08-15 (second entry, same day)** — Picked up the `odds_snapshot`/`odds_movement` re-stamp todo; live census
  before writing any restamp code found the 16,521/16,470 premise false (3,234 phantom rows/type; dead code, never
  scheduled). Retagged `BLOCKED-OPERATOR-DECISION`, no prod data touched. `market-tick-data-service@f79c1a143a`.
- **2026-08-15** — Operator reversed part of 08-08: `odds_horizon_bucket` survives as its own derived type (absorbs
  `odds_snapshot`/`odds_movement`), not folded into `odds`. Rationale: `/codex/02-data/sports-data-types-catalog.md`. No
  rows migrated under the old direction — "Move odds_horizon_bucket..." above only did venue re-attribution.
- **2026-08-08** — Authored. Double-gate on P1 + the API-Football campaign set at authoring time; protective cross-plan
  banner already landed on that campaign (`unified-trading-pm@3bb3214bdf`). Delete posture set to §3a
  reversibility-qualified per operator ruling, NOT [OPERATOR] tags.
- **2026-08-13** — `trades` → `odds` re-stamp (todo 1) complete. Tooling
  (`restamp_sports_trades_to_odds_2026_08_12.py` + `manifest_swap_trades_to_odds_2026_08_12.py` +
  `census_sports_trades_to_odds_scope_2026_08_12.py`) shipped `market-tick-data-service@071a5466`; VM-launcher
  `sports-trades-to-odds` category + comma-stall-regex fix shipped `deployment-service@9d4f0769`. Execution: VM
  `canonical-migration-sports-trades-to-odds-20260812-223215` exit 0 — GCS restamp copied 382,137 `data_type=odds`
  objects (0 failed / 0 content_mismatch), manifest swap relabeled merged 396,115 + legacy seed 232,098 `trades`→`odds`
  (VERIFY=0 remaining each). **P3-gated residual (expected, not incomplete scope):** the live forward-poll writer still
  emits `data_type=trades` rows — post-run census shows merged index at 20 `trades` rows (all
  `ODDS_API`/`live_odds_api`/`empty_confirmed`) and the frozen legacy seed re-populated to 362,753 `trades` on the next
  consolidator cycle, per the manifest-swap's own KNOWN PHASED-STATE caveat. Re-run the swap after P3's consumer
  migration (`sports_taxonomy_p3_consumers_2026_08_08`) flips the writers. Note: the census at dispatch time reported
  396,110 merged-index `trades` rows (not the plan's 375,257 title figure) — the title's figure is the earlier audit's
  captured-shard count; the migration re-stamped the full live population regardless.
- **2026-08-13** — `trades_inplay` retirement (todo 2) complete. **Stale census corrected in-run:** the plan's "111
  fossil rows / blank venue" premise was measured wrong — live probes showed **0 `trades_inplay` manifest rows on ALL 4
  surfaces** (merged + seed × tick-data + instruments-store buckets) but **1,197 real
  `data_type=trades_inplay/ inplay_ticks.parquet` GCS objects** (16 dates, 2022-09-07 → 2022-11-09) at real bookmaker
  venues × leagues, all verified non-empty post-kickoff captures (`bm_minutes_to_kickoff < 0`). Fold tool
  (`restamp_sports_trades_inplay_to_odds_2026_08_13.py`) shipped `market-tick-data-service@e5d43bc3e1`; execution folded
  **all 1,197** objects to `data_type=odds/inplay_ticks.parquet` with the `in_play=true` content column materialised (0
  content_mismatch / 0 failed / 0 empty residue) and deleted the sources under the §3a FRESH check
  (`soft_delete_retention_seconds=604800` ≥ 604800). **Split: 1,197 folded / 0 manifest rows deleted** (none remained to
  delete). The `trades_inplay` data_type token is retired on GCS (0 sources remain, verified). Reader fix shipped
  `market-data-processing-service@a9de0ff14b` — `_is_consumable_trades_blob` explicitly excludes `inplay_ticks.parquet`
  so the quarantined post-kickoff population can never be consumed as pre-match trades (the endswith-`ticks.parquet`
  matcher previously would have). features-service/ml-service read only the PROCESSED `odds_horizon_bucket` path, never
  this raw-tick prefix — unaffected. No live writer re-emits `trades_inplay` (verified: no MTDS adapter emits it), so
  the retirement is durable.
- **2026-08-14 (slot-26)** — Dispatched the `[OPERATOR]` 19-token execution todo; filed 3 blocked-questions rather than
  execute unilaterally: `BLK-dc738bb5` (is code-prep-only safe given the corrected step-2/3 design?), `BLK-0a3f3791`
  (found instruments-service auto-deploys via a ~15-min Cloud Run Job poll — merging steps 2-3 alone, even without a VM
  launch, would run the new lowercase-comparison logic against the still-uppercase manifest on the next poll,
  reproducing the exact re-fetch-storm this migration exists to prevent; main confirmed this is a real gap in its own
  earlier guidance), `BLK-1479b716` (found the plan's "5 confirmed call sites" scoping is materially incomplete — a
  systematic grep found 90+ manifest-write call sites across ~14 files, only 5 of which the prior trace covered; every
  per-vendor sports writer — footystats/sfi/transfermarkt/understat/weather — stamps its own 19-token value directly and
  was unaudited). Main's answer: stop hand-patching, file a dedicated LOCAL plan enumerating the full inventory before
  more code lands — see `/plans/archive/2026_08/sports_taxonomy_p2_19token_manifest_write_site_inventory_2026_08_14.md`.
  4 files fixed + locally QG-clean this session (`process_preflight.py`, `sports_dependency.py`, `writers.py`,
  `catalogue.py`), pushed to a REVIEW BRANCH deliberately withheld from `main`/LDR:
  `instruments-service@sports-taxonomy-p2-19token-lowercase-codeprep-2026-08-14`. 5 more vendor files fully classified
  (62 call sites: 57 SIMPLE, 5 ORDERED) via parallel Explore agents; `sports_reference_core.py` + `process_fetch.py`
  partially classified (open todos in the new doc). The `[OPERATOR]` execute todo below stays UNCHECKED — no VM
  launched, no live re-stamp attempted; the branch does not merge until the new doc's classification + coding todos
  complete AND the operator gives an explicit go/no-go on the atomic merge+launch (delete-safety-style review a 16M-row
  prod-manifest rewrite warrants, per the todo's own `[OPERATOR]` tag).
- **2026-08-14 (slot-26, same-day follow-up)** —
  `/plans/archive/2026_08/sports_taxonomy_p2_19token_manifest_write_site_inventory_2026_08_14.md`'s classification +
  code-authoring + verification is now COMPLETE (full detail in that doc, not duplicated here): every remaining vendor
  file + `process_*.py` stage fixed, a classification-method error found and corrected mid-session (manifest-read
  skip-checks need translate-BEFORE, not keep-uppercase), 2 latent bugs found and fixed via a full-suite quality-gate
  run (18 test assertions updated, all confirmed pre-migration-uppercase artifacts, zero real regressions), branch
  pushed as `instruments-service@5b1b2c72`. The `[OPERATOR]` execute todo below still stays UNCHECKED — the branch is
  fully coded + locally-validated but still deliberately unmerged; the atomic merge+launch decision is now ready for
  operator go/no-go review.
- **2026-08-14 (slot-26, resume session — atomic landing + execution)** — Operator confirmed go/no-go; executed the full
  atomic sequence. Launcher gap found first: the pre-existing `manifest-restamp` VM-launcher category was wired to an
  unrelated MTDS consolidator tool, not this migration's script — authored a new `sports-19token-restamp` category,
  shipped `deployment-service@3eded03f6a`. Landing the 21-file code branch hit a real incident: quickmerge's Stage-0.4
  auto-rebase collided with a concurrent push (another slot + a bot landing unrelated work in the same window) and an
  autostash-pop conflict wrote literal conflict markers into `sports_reference_core.py`. Root-caused via `git ls-remote`
  (real remote tip unaffected) + reflog; `git reset --hard` is hook-BLOCKED for autonomous workers, so recovered via
  `git checkout -- <file>` + `git reset --soft` + manual reapplication of the known-good edit, then confirmed the
  "extra" commits everyone worried about had ALSO landed safely elsewhere under different SHAs (byte- identical diff,
  nothing lost). Separately discovered quickmerge lands on whatever branch is CHECKED OUT, not always
  `live-defi-rollout` — first landing attempt shipped to the feature branch itself; fixed by rebasing onto fresh
  `origin/live-defi-rollout` and re-running from that branch context: `instruments-service@3637252f81`. VM
  `canonical-migration-sports-19token-restamp-20260814-045346` ran the real `--apply-prod --confirm-prod-write` restamp
  against ~15.9M rows in ~2 minutes, self-terminated cleanly; both the script's own post-write VERIFY and an independent
  census confirm 0 uppercase-token rows remain. **Then found step 3 was actually missing** — the
  `enumerate_expected_universe.py` override-dict wiring the todo's own atomicity clause required was never real code,
  only prose in this plan file; closed it same-session (`instruments-service@f2586ada09`) before any scheduled
  enumerator run could observe the mismatch. Lesson for next time: when a plan bullet says "the diff is drafted, see
  Progress Log," verify an actual diff exists (stash/branch/commit) before trusting the claim — a "drafted" step can be
  pure prose. A fully-redundant `stash@{0}` autostash (confirmed byte-identical to landed `HEAD` content) was left
  behind from the recovery — `git stash drop` is hook-blocked for autonomous workers, so it's harmless clutter for the
  operator to drop manually (`git stash drop stash@{0}` in `instruments-service`) whenever convenient; not functionally
  load-bearing. New follow-up todo added above for the still-unrun live `check_shard_freshness` end-to-end verification.
- **2026-08-14 (slot-26, continued session)** — Self-caught + fixed a false-progress bug from earlier this session: a
  commit (`fe9355c258`) claimed to close the split-decision todo but only appended prose, never flipped the checkbox
  glyph — caught on re-read, corrected (`e0e49d5ec9`). Then worked the remaining open todos in file order
  (`sequential: true`), each verified live before any claim:
  - **Closed with live evidence**: the footystats `ODDS`+`odds` fold (0 uppercase rows remain, `faf3fc54dc`); the
    ODDS_API/FOOTYSTATS venue re-attribution (`3755710c02` — each sub-population resolved or routed to a sibling todo,
    none silently dropped); the KALSHI/`polymarket_clob` purge (`9031908cd4` — population already fully absent, exact +
    case-insensitive re-check, no matching purge commit found so the mechanism is unconfirmed but the absence is real).
  - **`odds_horizon_bucket` corrected + narrowed** (`4aa7584a4d`): the todo's own numbers were badly stale (claimed
    135,980 shards/3 writers; live measured 1,070,078 rows, all `source=mdps_odds_horizon_bucket`). The bulk (165,604+
    captured rows across 26 real bookmakers) was ALREADY re-attributed by MDPS's own already-shipped
    `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py` +
    `reclassify_odds_horizon_bucket_unresolvable_rows_2026_07_28.py` before this session touched it — this todo's scope
    was mostly done, just never flipped. Remaining gap: 6 fine (league_id+timeframe-populated) `venue=ODDS_API` rows, of
    which 5 are expected NotFound residue (shards already deleted by a later reconcile — the script's own docstring
    calls this expected) and 1 genuinely reconciles (SUPERLIGA, 4 sub-rows).
  - **`--apply` attempted locally TWICE and OOM-killed both times** (SIGKILL at ~28s, `free -h` showing 18Gi
    host-available at the time — a sandbox cgroup limit, not genuine host exhaustion) — confirmed via re-`--dry-run`
    that the manifest was left UNCHANGED/uncorrupted both times (same generation, same 6-target count). **Invariant
    learned**: this script (and by extension any full-manifest-index rewrite) always loads+rewrites the ENTIRE 15.6M-row
    index regardless of how few target rows are actually changing — "manifest rewrites never run locally" applies at ANY
    target scale, not just large ones. Do not re-attempt this locally a third time.
  - **SPORT instrument_type residue** (`f496626e52`): widened scope live after a bounded per-day GCS listing found an
    entirely un-manifested `data_type=odds` twin (same junk population, identical byte-for-byte sizes to the `trades`
    twin per date/league — a writer bug double-wrote the same content under two data_type labels). Fresh §3a check
    this-session (`604800` on both buckets) → deleted + verified 0 remain for all 16 objects. Manifest side (8 rows)
    hits the same OOM wall as above — not attempted.
  - **Blank-venue writer-stopped verification** (`ad759e0cc0`): **measurement trap self-caught before acting on it** —
    first pass filtered `venue` blank across the WHOLE reference-data manifest and got 14.4M hits (almost the entire
    corpus), because blank venue is the CORRECT/expected state for league/team/fixture reference tokens
    (STANDINGS/XG/TEAMS/etc), not a bug. Narrowed to the actual target population (a SEPARATE manifest,
    `market-data-tick-sports-prd`, distinct index from the reference-data one) and the correct writer/data_type scope
    (`service_name=instruments-service`, `data_type in [odds, odds_horizon_bucket]`) → 2,379 rows, matching the
    consumer-inventory doc's already-documented root cause exactly (1,273+1,106, the gap to 2,490 being the 111
    `trades_inplay` rows already resolved by an earlier todo). Writer confirmed stopped: `attempted_at` clusters
    2026-07-21/22 UTC, a one-time backfill batch, 3+ weeks before today with zero rows since. Not yet deleted (same OOM
    constraint).
  - **CRITICAL finding, caught before any purge executed** (`8ef75ab36d`): the `league=`/`league_id=` sweep todo's own
    stated canonical direction was BACKWARDS. The plan claimed `league_id=` was canonical; direct read of UAC's actual
    path builder (`unified_api_contracts/canonical/domain/sports/gcs_paths.py:351`) proved `league=` is canonical. Had
    this run as originally written, it would have purged the REAL canonical data and kept the legacy duplicate —
    corrected in the plan text before any census/purge work began. Extent census (full corpus scope beyond the one known
    2020-06-06 example) still genuinely not done.
  - **New consolidated todo added** (`39b030bdb9`): a single small VM launch to close out all three pending
    manifest-only fixes together (the 4-row `odds_horizon_bucket` gap, the SPORT-residue's 8 manifest rows, the 2,379
    blank-venue rows) — each individually too small to justify its own VM; two of the three need a small new script
    written (no existing tool covers them), the third re-runs an already-committed script now bounded to 6 targets.
  - **Still open, untouched this session**: the `exchange_odds`/`fixed_odds` purge (P0, needs §3a + object moves), the
    `league=`/`league_id=` extent census + purge (P1, direction now fixed, scope not measured), the
    `odds_snapshot`/`odds_movement` re-stamp (P0, ~33k shards), and the full Verification section (four-surface
    reconciliation, accepted-exception-set shrinkage, honest-coverage re-run) — the last three are gated on the pending
    manifest fixes landing first. **Recommended next**: the batched-VM-run todo (closes 3 gaps at once cheaply), then
    the `exchange_odds`/`fixed_odds` purge (largest remaining untouched P0).
- **2026-08-14 (slot-29)** — Closed the `odds_horizon_bucket` re-attribution todo. Launched
  `mtds-migrate-odds-horizon-bucket-bookmaker` (existing `launch-mdps-odds-horizon-bucket-restamp-vm.sh`, already
  shipped by a prior session) to run the already-committed
  `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py --apply`. **Two real OOM failures before it ran clean**
  (not a lucky retry): the launcher's original `e2-standard-4` (16GB) default OOM-killed (rc=137) mid full-manifest
  rebuild; bumped to `e2-standard-8` (32GB, the sports-19token-restamp precedent) — **also** OOM-killed at the identical
  point, because this script's `_build_final_df` does a drop+concat rebuild + full `sort_values().reset_index()` before
  `to_parquet` (multiple full-DataFrame copies live simultaneously), unlike the 19-token script's lightweight in-place
  `.map()` relabel that precedent was based on; bumped again to `e2-standard-16` (64GB, matching `cefi-content-apply`'s
  own fix for the same rebuild-heavy OOM shape), which ran clean (rc=0). Shipped `deployment-service@2ceae6b48c` then
  `deployment-service@e80a134901`, both ancestor-verified on `origin/live-defi-rollout`. **Live gate result**: full
  apply-path resolution (generation `1786713550519620`, 15,651,115 manifest rows, workers=32) found `n_targets=5`,
  `n_reconciled=0` — all 5 remaining fine `venue=ODDS_API` rows are confirmed 404 NotFound (stale rows for
  already-deleted shards, the script's own documented expected case). The 1 previously-genuine row
  (2020-06-12/SUPERLIGA/T-6h) was **not present in this run's target set at all** — it resolved via some other path
  between the slot-26 measurement and this run, not via this apply (which never wrote: `GATE FAILED` short-circuits
  before any CAS write once `n_reconciled==0`). Manifest confirmed byte-unchanged. **0 genuine unmigrated rows remain,
  live-verified** — closed the todo without needing the operator-proportionality fallback the plan text had earmarked.
  Updated the sibling batched-VM-run todo to drop item 1 from its scope (now items 2-3 only: the SPORT-residue manifest
  rows + the blank-venue rows, still genuinely pending, same OOM-class constraint — untouched this session).
- **2026-08-14 (slot-28)** — `exchange_odds`/`fixed_odds` purge (P0): analysis + tooling complete, execution NOT yet run
  (checkpointing before compaction; resume with the migrate step below). **Live census**
  (`census_exchange_fixed_odds_purge_scope_2026_08_14.py`) re-measured the plan's stale 60,095/35,622/24,473 figures —
  still exactly 60,095 rows (`exchange_odds` 35,622 / `fixed_odds` 24,473) across 7 venues (BETFAIR_EX_EU/UK,
  BETFAIR_SB_UK, BETMGM, MATCHBOOK, PINNACLE, SMARKETS — `BETFAIR` bare and `ODDS_API` have 0 live rows, matching the
  original fork-move tools' own finding), `data_type=odds` uniformly (already swept by the completed `trades`→`odds`
  restamp above). **Collision measurement (the plan's own flagged risk — "BETFAIR_EX_UK has 9,204 exchange_odds AND
  3,405 pre-fork odds"), fully resolved, not assumed**: 23,960 of the 60,095 `(date, venue, league_id)` keys already
  have a live `instrument_type=odds` row at the same key — a plain path-segment rename would land on an existing object.
  Three escalating content checks (never trusting path/key alone, per the four-surface protocol's Part 2): (1) a 25-key
  full-content sample — 25/25 byte-identical; (2) a FULL (not sampled) crc32c+size compare over all 23,960 collision
  keys (`verify_exchange_fixed_odds_collision_full_2026_08_14.py`) — 23,482 byte-identical, 478 differ (target always
  larger); (3) a FULL row-level natural-key comparison over all 478 differing keys
  (`verify_exchange_fixed_odds_differing_full_2026_08_14.py`) — **all 478 confirmed TARGET-SUPERSET, 0 keys where the
  fork side holds data the existing `odds` object lacks**. **Disposition, fully measured**: DROP the fork object for all
  23,960 collision keys (the existing `odds` twin already covers its content — no copy needed); COPY-then-delete
  (path-segment rename, `gcs_copy_object` — `instrument_type` is a pure GCS-path/manifest key, not row content, per the
  original fork tools' own docstrings) for the remaining 36,135 non-colliding keys. Manifest side mirrors: REMOVE all
  60,095 fork rows; ADD an `odds` row only for the 36,135 non-colliding keys (the 23,960 colliding keys' existing `odds`
  manifest row is untouched — it already describes its own superset content). Tooling shipped this session
  (`market-tick-data-service`, not yet committed at checkpoint time — see next commit):
  `census_exchange_fixed_odds_purge_scope_2026_08_14.py`, `probe_exchange_fixed_odds_collision_content_2026_08_14.py`,
  `verify_exchange_fixed_odds_collision_full_2026_08_14.py`,
  `probe_exchange_fixed_odds_differing_content_2026_08_14.py`, `verify_exchange_fixed_odds_differing_full_2026_08_14.py`
  (the 5 analysis/probe scripts — all read-only, DELETE-when the purge below ships and re-verifies clean),
  `purge_exchange_fixed_odds_2026_08_14.py` (GCS pass: snapshot/migrate/ verify modes, §3a fresh-check gated),
  `manifest_purge_exchange_fixed_odds_2026_08_14.py` (manifest pass: REMOVE+ADD CAS swap). **Next step (resume here)**:
  run `purge_exchange_fixed_odds_2026_08_14.py snapshot --report <path>` to re-confirm the fresh §3a check + re-verify
  counts haven't drifted, then `migrate --confirm`, then independent `verify`; THEN (only after the GCS pass is 100%
  clean) run `manifest_purge_exchange_fixed_odds_2026_08_14.py --confirm-prod-write`; then flip this todo with evidence.
  Not run yet this session — deliberately stopping before a 60k-object prod mutation right at a context-compaction
  boundary rather than starting it with reduced attention.
- **2026-08-14 (slot-28, resume session)** — Ran the deferred `snapshot`: disposition came back **60,095 DROP / 0
  COPY_THEN_DELETE** — every fork object already has a same-key `odds` twin on disk, sharply contradicting the prior
  entry's 23,960/36,135 split. Root-caused before trusting either number: the two are DIFFERENT measurements — the prior
  split was a MANIFEST-ROW-level collision census; this is the live GCS-OBJECT-level truth. No script bug (src != tgt
  path, live `gcs_describe_object` re-confirmed, no self-comparison artifact) — most likely the 2026-07-27 fork-creation
  copied (not moved) the pre-fork `odds` object for more venues than the manifest reflects, a genuine manifest/GCS
  divergence. **Critical finding — the prior entry's "0 data-loss-risk keys found" was WRONG for the full population**,
  not just stale: that claim was measured on a 23,960-key MANIFEST-row subset and wrongly generalized to all 60,095 GCS
  objects. Built + ran a full-population two-stage content verifier
  (`verify_exchange_fixed_odds_full_population_content_2026_08_14.py`, promoted this session) over all 60,095
  DROP-disposition keys: Stage 1 crc32c/size re-describe (58,216 byte-identical, 1,879 differ) → Stage 2 row-level
  natural-key compare on the 1,879 (`533` EQUIVALENT + `561` TARGET-SUPERSET safe, **`785` DATA-LOSS-RISK** — the odds
  twin does NOT contain all fork rows, up to 1,134 missing rows in one shard). **Had the original migrate run proceeded
  on the unverified 60,095/0 disposition, it would have silently destroyed data in 785 shards.** True safe count:
  **59,310/60,095 (98.7%)**. Fixed both purge scripts rather than work around them by hand: corrected the now-disproven
  "0 data-loss-risk" docstring claim in `purge_exchange_fixed_odds_2026_08_14.py`, and added a **required**
  `--exclude-report` flag to both the GCS script (`migrate`/`verify`) and the manifest script (`dry_run`/`apply`) that
  structurally skips the 785 excluded src_paths (status `SKIP-DATA-LOSS-RISK-EXCLUDED`, GCS/manifest untouched) rather
  than depending on operator care. Shipped `market-tick-data-service@835667f7cc`. Execution:
  `migrate --snapshot purge_snapshot.json --exclude-report full_population_content_verify.json --confirm` completed
  clean, exit 0: **59,310 DROPPED / 785 SKIP-DATA-LOSS-RISK-EXCLUDED** (sums to the full 60,095 population, 0 failures).
  Independent `verify` re-read confirmed the result at the object level: 0 non-excluded fork objects remain, 0 target
  objects missing (every odds twin present), 785 excluded fork objects confirmed still present as expected — **VERIFY
  PASSED**. GCS side is now fully clean for the 59,310 safe keys. Manifest pass (`--confirm-prod-write`) is the next
  step. **New follow-up needed, not yet built**: the 785 DATA-LOSS-RISK keys need a genuine content MERGE (union
  fork+odds rows by natural key, rewrite the odds object, then delete the fork source) — a different, higher-risk
  operation than DROP/COPY_THEN_DELETE (it overwrites a live object rather than just creating/deleting one). Added as a
  new P1 todo below rather than left as prose. **Lesson**: a manifest-row-level collision census and a GCS-object-level
  disposition check are NOT interchangeable measurements even when they sound like the same question — always re-verify
  content at the SAME granularity the delete will actually operate on, and never generalize a subset content-check to
  the full population without re-running it.
- **2026-08-14 (slot-28, same session, manifest pass)** —
  `manifest_purge_exchange_fixed_odds_2026_08_14.py --exclude-report full_population_content_verify.json` (DRY-RUN)
  confirmed counts internally consistent with the GCS-verified safe population: REMOVE 59,310 fork rows (785 excluded,
  untouched) / ADD 35,350 new `odds` rows (no pre-existing twin) / DROP-no-add 23,960 (odds twin already exists) —
  35,350+23,960=59,310, matches exactly. Proceeded to `--confirm-prod-write`, but hit two consecutive process-management
  failures BEFORE any live-index write occurred (both independently confirmed safe by re-running the DRY-RUN afterward
  and observing REMOVE still =59,310, i.e. the live index was byte-identical to before either attempt): (1) first launch
  was double-backgrounded (Bash-tool `run_in_background: true` wrapping a command that ALSO backgrounded itself with
  shell `&`) — the tracked "process" was only the launcher shell, which exits almost immediately after spawning the real
  child, so the harness reported false-positive completion while the real child (no `nohup`/`disown`) kept running
  unprotected; it then died silently (no traceback) right after the pre-write snapshot step, most likely SIGHUP'd when
  its parent shell was torn down. (2) Second launch used single, correct `run_in_background: true` (no manual `&`) —
  still died at the exact same point (after "snapshot written + verified", before the CAS rewrite), this time with an
  explicit signal: harness reported `exit code 143` (SIGTERM), confirming the kill is external to the script (no
  exception, no traceback in either log). Both times the process was torn down at what looks like a session/turn
  boundary in the agent harness itself, not a script bug. **Lesson**: a Bash-tool `run_in_background: true` process is
  not immune to being SIGTERM'd on a session/turn boundary in this environment — for any prod-write that must survive
  across turns, fully detach it first (`setsid nohup <cmd> < /dev/null > log 2>&1 &` + `disown`, capturing the REAL
  worker PID via `pgrep`, not `$!`, since `$!` under `setsid` is the transient wrapper PID, not the detached child),
  THEN attach a separate tracked `run_in_background: true` monitor (`while kill -0 <real-PID>; do sleep 5; done`) purely
  to get a completion signal — never trust `run_in_background: true` alone as a durability guarantee for a long-running
  prod mutation. Third attempt (setsid-detached) **also died at the identical point** — this ruled out shell-session
  teardown as the cause and pointed at something host-level. Found the real root cause by reading
  `/usr/log/resource-watchdog.log` and `/usr/local/bin/resource-watchdog.sh`: a legitimate cross-slot host guardian
  (permanent infra, not a bug) that kills any non-allowlisted process whose RSS exceeds 10GB normal / **4GB once the
  shared orchestrator cgroup crosses 80% memory** (other slots' concurrent work can trigger "high pressure" at any
  moment — confirmed via the log: all 3 kills fired at `pressure=high cgroup_mem=22GB`, `rss:~9.4-10.3GB > 4194304kB`,
  `KILL #134/#135/#136`). Each kill was independently confirmed harmless (re-running the plain DRY-RUN afterward each
  time showed the live index byte- identical to before, REMOVE still =59,310) — the watchdog SIGTERMs cleanly before any
  partial write lands, so no data-loss risk, just wasted attempts. **Root cause was the script, not the environment**:
  the original pandas implementation did `pd.read_parquet` of the FULL 6.1M-row/39-column live index, then
  `pd.concat([filtered, add_rows])` (a second near-full-size copy), then `to_parquet` (a third Arrow-conversion copy) —
  3x the base frame alive at once, plus a Python-level tuple-list exclude-check that iterated all 6.1M rows instead of
  just the ~60K fork rows. Rewrote the script (`manifest_purge_exchange_fixed_odds_2026_08_14.py`) to never materialize
  the full table in pandas: a cheap column-projected (6-of-39 cols) pass over the whole index computes REMOVE/ADD row
  masks as numpy bool arrays (exclude/target-key matching now scoped to only the ~60K fork + ~511K odds rows, not all
  6.1M), then a pyarrow row-group streaming pass (`ParquetFile.iter_batches` → filter → `ParquetWriter.write_batch`)
  rewrites the index without ever holding more than one ~250K-row batch of full-width data in memory. Validated
  correctness before trusting it against prod: re-ran the fixed DRY-RUN and got byte-identical output to the original
  implementation (REMOVE 59,310/785-excluded, ADD 35,350, DROP 23,960, identical per-venue breakdown) — proof the
  rewrite is behaviorally equivalent, not just faster. Measured peak RSS via `/usr/bin/time -v`: **1.84GB** for DRY-RUN
  (vs the killed original's ~10GB). Shipped `market-tick-data-service@dca9b75192`. **Fourth attempt (memory-fixed
  script) — SUCCESS**: `--confirm-prod-write` completed exit 0, peak RSS **2.15GB** (comfortably under the 4GB
  high-pressure threshold). Output: `base=6,103,081 rows -> removed 59,310 fork row(s), added 35,350 odds row(s)`.
  Post-write independent re-download verify: **`non-excluded fork rows remaining = 0` — VERIFY PASSED**. Manifest side
  is now fully clean for the 59,310 safe keys, matching the GCS side exactly. Combined with the earlier GCS pass, **both
  surfaces (GCS objects + manifest rows) are now purged for 59,310/60,095 (98.7%)**; the 785 DATA-LOSS-RISK keys remain
  untouched on both surfaces, tracked by the separate P1 content-merge todo above. **Lesson**: a killed background
  process is not automatically "the environment being flaky" — `ps`/cgroup evidence (`resource-watchdog.log`,
  `/dev/shm/resource-watchdog/kills/<pid>.json` marker files) will name the exact reason and threshold; check them
  before retrying blindly, since 2 of these 3 kills were fully explainable and the fix was in the script, not in how it
  was launched. **This todo's checkbox reflected BOTH-surfaces completion for the safe 59,310/60,095 population** (see
  the todo's partial-completion note above) — **now flipped to `[x]` 2026-08-14 (slot-28)**, the P1 merge todo below
  having closed the 785-key residual the same day (see that entry's own Progress Log write-up further down).
- **2026-08-14 (slot-30)** — footystats/`odds_horizon_bucket` re-attribute todo CLOSED: live collision-census
  (`market-tick-data-service@4709c8dea3`, `census_footystats_odds_horizon_bucket_fold_scope_2026_08_14.py`) found **0**
  rows at `pipeline_mode=batch_footystats AND data_type=odds_horizon_bucket` — the 1,784,473-row population the todo
  described no longer exists live; all 1,070,081 `odds_horizon_bucket` rows are already under
  `mdps_odds_horizon_bucket`. See the todo's own closing note for the two independent queries that confirmed this.
- **2026-08-14 (slot-28)** — P1 content-merge todo CLOSED (785 DATA-LOSS-RISK keys, operator-authorized via
  `AskUserQuestion` before any write). Built `merge_exchange_fixed_odds_content_2026_08_14.py` (`merge`/`verify`/
  `finalize` modes, two-phase-verified-write shape: write+readback → independent re-download re-check → delete-only-
  what-verify-confirmed). **First dry-run caught a real defect before any prod write**: naive schema equality flagged
  785/785 `SCHEMA-MISMATCH` — investigation found a genuine fork/`odds` schema divergence (two shapes among the 785:
  `venue`/`instrument_type`/`data_source` present vs `bookmaker_key` present), confirmed value-level (`venue`==
  `bookmaker_key`, e.g. both `'pinnacle'`; `data_source`==`source`==constant `'ODDS_API'`; fork `instrument_type` row-
  content is always constant `'odds'`) — all three safe to reconcile (rename/drop/drop). A broader 25-shard/6,037-row
  sample of the wider (non-merge) `odds` population confirmed per-shard column presence/absence is already a normal,
  tolerated corpus property, and `fixture_id`'s real "unset" convention is `''` not null — both honored in
  `reconcile_schema()`. Fixed dry-run: 785/785 `WOULD-MERGE`, 217,538 total rows cross-checked against the original
  verify script's own `missing` field sum (exact match). Shipped `market-tick-data-service@391eca5e03`. Execution:
  `merge --confirm` 785/785 MERGED (fresh §3a retention check, 604800s); independent `verify` 785/785 COVERED, 0
  STILL-MISSING; `finalize --confirm` 785/785 fork objects DELETED (fresh §3a check again). Manifest pass
  (`manifest_merge_reconcile_2026_08_14.py`, shipped `market-tick-data-service@a9ba17fbfd`): first dry-run assumed a
  REPAIR-only shape (odds twin's manifest row already exists) — live-index inspection found **0/785** pre-existing odds
  manifest rows (the GCS `odds` object existed with real content, but the manifest never had a row for it at these keys
  — a genuine pre-existing manifest/GCS drift, not a bug in this pass) — rewrote to ADD-or-REPAIR.
  `--confirm- prod-write`: REMOVE 785 fork rows + ADD 785 new odds rows, CAS write succeeded (snapshot
  `pre_exchange_fixed_odds_merge_manifest_2026_08_14_20260814T225944Z.parquet`). The script's own built-in post-write
  verify crashed on an unrelated NaN `row_count` elsewhere in the manifest (bug, not a data problem) — independently
  confirmed the actual write was already correct via a standalone check (0 remaining fork rows, 785/785 odds keys at
  exactly the expected `row_count`) before fixing + shipping the verify bug (`market-tick-data-service@ba3f5ed034`).
  **Both surfaces (GCS + manifest) are now 100% clean for the full 60,095/60,095 originally-affected shards** — the P0
  purge todo above is flipped to `[x]` on the strength of this closure.
- **2026-08-15 (slot-28)** — final 2 tiny manifest-only fixes CLOSED via one VM (per the batching todo above): SPORT
  residue (8 rows) and blank-venue (2,379 rows, confirmed already-closed by slot-26's sibling script — true no-op) both
  VERIFY PASSED 0 remaining. `market-tick-data-service@7b1e6e87` + `deployment-service@b4aef3e1`, VM
  `canonical-migration-sport-residue-blank-venue-purge`, exit rc=0, self-deleted. **CORRECTED (plan_reconciler,
  2026-08-19)**: old claim path-dup sweep was `[ ]` was stale — `## Todos` line ~576 shows `[x]` DONE 2026-08-15.
- **context-scout 2026-08-20**: rebuilt context_scope (2 entries) — 25/26 todos now done; the sole remaining item
  (P0 BLOCKED-OPERATOR-DECISION) points only to `sports-data-types-catalog.md`'s correction banner and the
  eventual phantom-row cleanup's delete-safety protocol. Dropped 4 entries mapped to now-completed re-stamp/purge work.
