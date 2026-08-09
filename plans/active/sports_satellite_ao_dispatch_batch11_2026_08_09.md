---
doc_type: plan
title: Sports satellite AO batch 11 — post-RECLASSIFY-sweep residual extraction (2026-08-09)
summary: >-
  Eleventh AO-dispatch batch for sports. Mirrors the satellite-batch-extraction pattern against the 12-doc `sports`
  tranche the same-day RECLASSIFY sweep read end-to-end but did not whole-doc-flip: pulled out only the specific
  bounded, worker-determinable items left behind, leaving genuinely-gated items (operator hard-stops, either/or design
  forks, dependency-blocked work, GCS-delete todos without a live reversibility check) untouched in their source docs.
  10 of the 12 docs yielded ZERO extractable items — nearly all were already resolved by the 2026-08-08 operator-ruling
  wave and are being implemented end-to-end by the `sports_taxonomy_p1-p4_2026_08_08` chain, so extracting a competing
  todo here would have duplicated already-active dispatch. 2 items across 2 docs cleared the conflict check — (1) a
  bounded HTTP-client-timeout audit+fix that this doc's own `na-eligibility-audit` pass had already flagged as a good
  standalone RECLASSIFY candidate but never split out because the sibling todos in the same doc are opportunistic/
  judgment-gated; (2) a parity test the source plan's own 2026-08-08 Progress Log entry flagged as newly ripe once its
  gating 3-repo naming migration (todos 1-6) shipped — `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s
  Conflict-gated section held this exact item back citing "the still-unshipped migration," which is now stale.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, features-service, ml-service, strategy-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-11, satellite-docs]
related:
  [
    /plans/active/issues/mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Satellite-batch-extraction pass (2026-08-09) against the sports-tranche 12-doc candidate list a same-day RECLASSIFY
  sweep had already read end-to-end (1 doc qualified for a whole-doc flip there; this pass covers the other 12, none of
  which whole-doc-qualified). Per-doc classification of every open item against
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" + the shared
  conflict-check protocol in `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    market-tick-data-service/market_interface/adapters/sports/odds_api_adapter.py,
    unified-api-contracts/unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py,
  ]
---

# Sports satellite AO batch 11 — post-RECLASSIFY-sweep residual extraction (2026-08-09)

## Methodology

Read all 12 candidate docs end-to-end (not checkbox-count), re-verifying current state rather than trusting the
candidate list's `open_todos` counts, since several sports docs were touched by both an operator-ruling wave and a
stale-check pass earlier the same day. Classified every open item as **extractable** (bounded, worker-determinable
outcome) or **stays behind** (judgment call, operator-gated, dependency-blocked, or an established-ruling citation).

## Docs with ZERO extractable items (10 of 12) — why

- **`ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`** — sole open todo (wire vs. drop
  `--family`) is resolved by a dated `✅ OPERATOR RULING 2026-08-08` banner and already being implemented by
  `sports_taxonomy_p3_consumers_2026_08_08.md`'s ML section. Extracting here would duplicate active dispatch.
- **`sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`** — sole open todo (enumerate `fixture_ids_override`
  callers, delete if zero real use cases) resolved by a dated `✅ OPERATOR RULING 2026-08-08` banner, implemented by
  `sports_taxonomy_p3_consumers_2026_08_08.md`'s "Catalogue, browser, dependency" section.
- **`sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`** — sole open todo
  (`LC_TARBALL_FRESHNESS=enforce` proposal) already extracted verbatim into
  `sports_satellite_ao_dispatch_batch10_2026_08_06.md` todo 3, whose finalize sibling already carries the
  reconciliation step for this doc.
- **`sports_features_layer_findings_sweep_2026_07_18.md`** (Part 1) — 2 open items: the T-12h/T-4h/T-2h
  snapshot-trigger todo names `launch-sports-scheduler-vm.sh`, but 3 independent, more current active docs
  (`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`, `assigned_vm: planning`, ACTIVE;
  `sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`;
  `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`) establish that `sports-scheduler` actually
  runs as the Cloud Run Job `uts-prod-sports-scheduler` dispatched via `uts-prod-sports-scheduler-cron` (`*/5 * * * *`),
  not a standalone VM — the todo's premise conflicts with the live architecture and that exact Cloud Run Job is under
  active OOM investigation in `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` right now. Borderline
  (premise-uncertain + conflicts with an active investigation on the same subsystem) — not extracted per instruction.
  The 2nd item (add T-6h/T-2h as a MODEL horizon) is resolved by this doc's own `✅ OPERATOR RULING 2026-08-08` banner,
  implemented by `sports_taxonomy_p3_consumers_2026_08_08.md`.
- **`sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`** (Part 3) — both open items are digest
  pointers whose own text says "Owned by `sports_consolidated_closeout_2026_07_19.md` Track E... Not duplicated here."
  The real work lives in that closeout's Track E (not one of the 12 candidate docs) — correctly deferring, nothing to
  extract from this doc itself.
- **`sports_odds_stale_fixture_reinjection_2026_07_14.md`** — the `[DATA] P2` RUSSIA_PREMIER_LEAGUE zombie-shard purge
  is a bounded, scoped GCS delete/re-derive with a stated done-when, but is tagged `[DATA]` not `[OPERATOR]` with no
  fresh `gcs_bucket_soft_delete_retention_seconds()` check backing a path-(c) self-justification (task_template.md
  finding T) — attempted the live check this pass (`gcloud storage buckets describe`), blocked by a stale/
  non-interactive auth session on this host, so the check could not actually be run. Per finding T this must be
  "verified, not asserted" — not extracted; every prior `na-eligibility-audit` pass reached the identical conclusion.
  The `[DATA] P3` gate-reassessment todo is explicitly sequenced after the P2 purge above, so it stays with it.
- **`sports_catalog_league_grain_only_scope_2026_07_08.md`** — all 4 open todos resolved by a dated
  `✅ OPERATOR RULING 2026-08-08` banner ("DISPATCH APPROVED, gated on the taxonomy contracts phase"), carried verbatim
  by `sports_taxonomy_p3_consumers_2026_08_08.md`.
- **`sports_fixtures_browser_single_catalogue_source_2026_07_24.md`** — sole open todo (regen-cadence freshness
  either/or) resolved by a dated `✅ OPERATOR RULING 2026-08-08` banner, implemented by
  `sports_taxonomy_p3_consumers_2026_08_08.md` under its `[UI]` + `pw:L2` playwright gate.
- **`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`** — `locked_by: live-defi-rollout` with an explicit
  "do not archive/unlock without an operator ruling" banner; both open todos (extend
  `EXPECTED_BOOKMAKER_MARKET_SETS` to 28 unmapped leagues OR add a `tier_3_global` tier; decide+implement the `trades`
  cluster-validation gap) are genuine either/or design forks with no evidence-based tiebreaker — no 2026-08-08 ruling
  touches either.
- **`sports_predictions_live_mode_activation_readiness_2026_07_21.md`** — 2 open todos: the `[REVIEW]` promote-workflow
  run is gated on the still-unshipped `sports_group_c_execution_backtest_harness_2026_07_21.md` (reclassified to
  `assigned_vm: planning` in today's earlier RECLASSIFY sweep but not yet shipped); the `[OPERATOR]` live-trading
  go-ahead is the permanent human hard-stop, freshly reaffirmed by a dated `✅ OPERATOR RULING 2026-08-08` banner.

## Todos

- [ ] [SCRIPT] P2. **Audit whether `market-tick-data-service`'s `odds_api` HTTP client calls
      (`market_interface/adapters/sports/odds_api_adapter.py` and any sibling live connector,
      `live/connectors/odds_api_ws.py`) declare explicit connect/read timeouts on every outbound request** — a hung
      socket with no timeout is the leading hypothesis for the 5 consecutive silent VM hangs (~16-21 min each, no
      `CHUNK_FAILED`, no OOM, no traceback) documented in
      `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`. If any call site is missing an explicit
      timeout (bare `requests`/`httpx` call with no `timeout=` kwarg, or a client constructed without a default), add
      one (a sane connect/read timeout in the 10-60s range, consistent with any timeout convention already used
      elsewhere in the adapter), and add a regression test asserting the timeout is set. If every call site already
      declares an explicit timeout, close as a negative-result audit — state the file:line evidence inline. Do NOT
      touch `PREFIX_IDLE_THRESHOLDS`/the watchdog's stale-heartbeat window — that is a separate, judgment-gated todo in
      the source doc, explicitly deferred there pending this audit's finding. `quality-gates.sh --no-fix` green before
      commit; ship via quickmerge. Source:
      `/plans/active/issues/mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` todo 2 (its own
      `na-eligibility-audit 2026-08-08` entry already flagged this exact split — "a good RECLASSIFY candidate on its
      own... not splitting this doc's todos across two `assigned_vm` values in this pass" — this batch is that split).
      Done-when: every real outbound `odds_api` HTTP call site has a stated, tested timeout, or the audit's negative
      result is cited with file:line evidence.
- [ ] [REVIEW] P3. **Write the FSS-output ↔ ml-service-input ↔ strategy-service-input naming-parity test** — assert
      that `features-service`'s `odds_features` exporter output, `ml-service`'s `SportsFeatureLoaderMixin` schema
      validation, and `strategy-service`'s `SportsValueBettingEngine`/`SportsArbDutchingEngine`/
      `sports_feature_subscriber.py` all read/write the SAME field names now that all 3 consumers have been migrated to
      UAC's `SportsFeatureVector`/`OddsFeaturesMixin` as SSOT (verified live: todos 1-6 in the source plan below are
      all `[x]`, shipped across `unified-api-contracts@689efa54`, `features-service@0ded2449`, `ml-service@07976ae`,
      `strategy-service@4c55438c`, `ml-service@10e219f`). This is the original deliverable
      `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` asked for, blocked until the
      migration landed — it has now landed.
      `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s Conflict-gated section held this exact item back citing
      "the still-unshipped 3-repo four-way naming migration" — re-verified this pass: that migration IS shipped
      (source plan's own 2026-08-08 Progress Log entry independently flags the same staleness and recommends exactly
      this extraction), so the prior conflict-gate no longer applies. Test asserts field-name parity across the 3 real
      consumer boundaries against the live UAC schema, not a mock — fails loud on any drift. `quality-gates.sh --no-fix`
      green on every touched repo before commit; ship via quickmerge. Source:
      `/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md` todo 9 (`[REVIEW] P3`). Done-when: a
      new, passing parity test exists in the repo(s) that would actually exercise this boundary, asserting the same
      field-name set across producer/loader/subscriber against the real `OddsFeaturesMixin` schema.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the shared conflict-check protocol
  applied to both todos above
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — the reversibility-check bar that kept the
  `sports_odds_stale_fixture_reinjection_2026_07_14.md` purge todo out of this batch

## Progress Log

- **2026-08-09 (satellite-batch-extraction pass)**: authored from the 12-doc sports-tranche candidate list. 2 items
  extracted across 2 source docs; 10 docs yielded zero extractable items (see table above) — the large majority already
  resolved by the 2026-08-08 operator-ruling wave and implemented end-to-end by the `sports_taxonomy_p1-p4_2026_08_08`
  chain. One live GCS reversibility check (`sports_odds_stale_fixture_reinjection_2026_07_14.md`'s zombie-shard purge)
  was attempted but could not be executed this pass (stale/non-interactive `gcloud` auth on this host) — left open in
  its source doc, not extracted, consistent with every prior audit pass on that item.
