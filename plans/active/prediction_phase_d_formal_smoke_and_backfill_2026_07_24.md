---
doc_type: plan
title:
  Prediction Phase D — formal smoke-test green + MVP backfill (split from prediction_consolidated_closeout_2026_07_18)
summary:
  Phase D of the prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — the `-test-`
  bucket isolation, MVP-scope reconciliation, and smoke-adaptation code fixes are shipped; residual open work is running
  `data-pipeline-check-is` / `data-pipeline-check-mtds` for prediction-only, all shards, to a formal post-migration
  green, then the MVP backfill readiness gate.
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [prediction, close-out, smoke-test, data-pipeline-check-is, data-pipeline-check-mtds, mvp-backfill, test-buckets]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-25" # was 2026-07-24 — consolidated-closeout split pass added 3 todos relocated from the parent's "Queued audits + reviews" section (-is/-mtds 3x-cadence top-ups + the adversarial AO-dispatch-readiness pass); open-todo count 3 -> 6
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_phase_ab_residuals_2026_07_24]
gate_on_depends: true
source: >-
  Split from `prediction_consolidated_closeout_2026_07_18.md` (Phase D section, lines 370-437 of that doc as of
  2026-07-18/2026-07-24) per the operator-approved line-cap remediation triage
  `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries"). Content moved verbatim, not summarized. `depends_on` + `gate_on_depends: true` added 2026-07-24 (plan
  audit finding) to encode this doc's own header text ("post-migration completion gate") as a real dispatch gate,
  matching the Phase E sibling's already-correct pattern — the migration is carried by
  `prediction_phase_ab_residuals_2026_07_24.md`.
context_scope:
  [
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/archive/2026_07/prediction_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/base_prediction_adapter.py,
  ]
---

# Prediction Phase D — formal smoke-test green + MVP backfill

> **Split from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-24).** This is the Phase D section of that
> close-out, moved verbatim. For the full historical execution narrative (Progress Log, ticks 1-31, 2026-07-18 through
> 2026-07-20 — including the tick-19/20/22/23 smoke-RED triage and fixes this phase's remaining formal-green run depends
> on) and shared cross-phase context (the Ground-truth verdict table, the prediction shard-atom definition, the MVP
> universe scope), see the parent doc. Sibling phase children: `prediction_phase_c_data_status_ui_2026_07_24.md` (Phase
> C), `prediction_phase_ab_residuals_2026_07_24.md` (Phase A-B), `prediction_phase_e_football_arb_live_2026_07_24.md`
> (Phase E — gated on this plan + the Phase A-B residuals plan).

## Phase D — re-smoke-test the backfills, prediction-only, ALL shards (post-migration completion gate)

> **Terminal data-readiness gate.** Post-migration, run BOTH pipeline-check skills scoped to **prediction only** and
> require green across every prediction shard — force-refetch + skip-if-fresh + a canonical-shape assertion — so we KNOW
> prediction is complete before any MVP backfill. Both skills already accept `--asset-group PREDICTION`; **do NOT pass
> `--tardis-only`** (Polymarket/Kalshi are not Tardis-sourced → it would enumerate 0 shards). Prediction shards: **IS =
> 2** `(PREDICTION, POLYMARKET)`, `(PREDICTION, KALSHI)` (IS atom has no data_type axis); **MTDS = 4**
> `{POLYMARKET, KALSHI} × {trades, book_snapshot_5}`.

- [x] ✅ [INFRA] P0. **MTDS prediction `-test-` bucket isolation FIXED end-to-end (2026-07-18).** The `-test-` bucket
      `market-data-tick-pred-test-central-element-323112` already exists (derived from `cloud-providers.yaml`
      `canonical_tiers=["prd","test"]`; no provisioning needed). THREE write/read paths converged to it: (1)
      verify-read + force-consolidate — `_test_bucket("prediction")` now returns the `-test-` bucket (was PROD
      fallback), `market-tick-data-service@b06d1e6b`; (2) batch WRITE — `get_tick_data_bucket(test_aware=True)` honours
      `IS_TEST_RUN` for prediction (was PROD-only), `mtds@2e50851d`; (3) live WRITE twin — `_resolve_live_bucket`
      honours `IS_TEST_RUN` (preserves `live=batch`), `mtds@86d70de9`. Guard test flipped + cross-AG
      (cefi/tradfi/defi/sports) byte-unchanged; QG-green (6320 passed). **Follow-ups flagged:** stale prose in
      `data_pipeline_e2e_check_2026_07_10.md` (L267-269 / 341-342 / 1025 / 1623 now false — "prediction stays
      PROD-only"), and UTL `get_write_bucket_name` still has a prediction-PROD-only branch (not a tick-write path, but a
      live inconsistency worth a follow-up). (repos: market-tick-data-service ✅)
- [x] ✅ [DATA] P1. **`book_snapshot_5` MVP-scope RECONCILED — `unified-api-contracts@53bf01d6`.** It was in all THREE
      data registries (`DATA_TYPES_BY_ASSET_GROUP`, `VENUE_DATA_TYPE_CAPABILITIES`, `expected_coverage`) but absent from
      `PredictionMvpRule.data_types` — verified NOT a deliberate trades-only exclusion (only COINBASE + Deribit-OPTION
      have such decisions; prediction cited none; all 3 registries re-added it 2026-06-23 when both CLOB venues began
      emitting it — the MVP rule was the un-updated outlier). Added `book_snapshot_5` to `PredictionMvpRule.data_types`
      (captured: 399,713 rows) + bumped `MVP_SCOPE_CONFIG_VERSION` 17→18; rule-11 cross-AG-unchanged test added
      (cefi/tradfi/defi/sports MVP sets pinned). `--mvp-only` prediction now tests all 4 shards. Operator can narrow
      back to trades-only if that was the intent (documented in the code). (repos: unified-api-contracts ✅)
- [x] ✅ [DATA] P1. **CQG cluster grain + `market_lifecycle` smoke coverage SHIPPED — `instruments-service@a3abd7a3`.**
      Added on the IS side — the genuine PRODUCER of both grains (the CQG bundle is written by IS `process_write`;
      `market_lifecycle` by IS `writers._write_market_lifecycle`). Correctly NOT faked on MTDS: MTDS only READS
      `market_lifecycle` as a pre-fetch gate + the CQG bundle is a manifest-only atom with no MTDS producer path, so a
      force/skip cell there would be fiction (documented in the MTDS smoke engine). (repos: instruments-service ✅)
- [x] ✅ [DATA] P0. **Prediction smoke adaptation + canonical regression cell SHIPPED (code-ready) —
      `market-tick-data-service@c805e6cb` + `instruments-service@a3abd7a3`.** Per-shard canonical regression cell added
      (prediction-scoped, mirrors `assert_tradfi_derivative_ids_canonical`): asserts per-CID
      `instrument_type == PREDICTION_MARKET` (the single equality catches every A0 drift — lowercase dupes,
      underlying-leakage, empty) + canonical `instrument_id` (non-empty, whitespace-free, PREDICTION_MARKET
      type-segment); soccer rows checked for `af_fixture_match_status`. Cross-AG byte-unchanged (cefi/tradfi/defi/sports
      pinned). Skills already accept `--asset-group PREDICTION`; the RUN (below) needs an operator `--day`. (repos:
      market-tick-data-service ✅, instruments-service ✅)
- [ ] [DATA] P0. **RULED 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — use `--day 2026-08-05`
      (recommended after research; operator asked for a representative day with data across shards rather than naming
      one directly).** Reasoning: must postdate the 07-01→07-06 prediction capture-incident gap AND the 2026-07-30
      Kalshi `canonical_question_group` write-time-bug fix (`instruments-service@e0f7aaad`) to reflect the CURRENT,
      fixed pipeline state, not a pre-fix day; 2026-08-05 is 2 days before this ruling (2026-08-07), safely
      settled/finalized. **Caveat, stated honestly**: live per-shard row-count verification wasn't feasible from this
      session — the `coverage-summary` API refused the full computation (~83GB estimated, over its 768MB safety budget)
      and a manual GCS walk would violate the single-walk-discipline rule. A documented, already-PROVEN fallback exists
      if 2026-08-05 turns out sparse on any shard: **`2026-06-28`** — this doc's own earlier tick-22 entry confirms the
      IS force leg ran end-to-end against it (0-obj→182 real canonical `PREDICTION_MARKET` objects). The pipeline-check
      run itself will immediately reveal if either day is sparse on a given shard (that is what force/skip proving is
      for) — try 2026-08-05 first, fall back to 2026-06-28 if any shard comes up empty. Run `data-pipeline-check-is` for
      prediction-only, all shards, post-migration — both prediction IS shards prove force/skip + canonical shape; report
      path cited.
- [ ] [DATA] P0. **`--day 2026-08-05` (fallback `2026-06-28`) — same ruling as the `-is` todo above.** Run
      `data-pipeline-check-mtds` for prediction-only, all shards, post-migration — same day, all 4 prediction MTDS
      shards prove force/skip + canonical shape; report path cited.
      **BOTH skills green across all prediction shards = prediction is code-complete, migrated, honestly-covered, and
      verified.** **PARTIAL 2026-07-19 (tick 22):** all 6 smoke fixes landed; IS force leg DEMONSTRATED end-to-end
      (0-obj→182 CQG-first objects w/ canonical `PREDICTION_MARKET`, `-test-` bucket, day=2026-06-28) — the dominant IS
      0/14 RED is resolved; `book_snapshot_5` now honest live-only skip. Formal all-green still blocked ONLY by the
      `trades` catalogue-gating (next todo). The orphaned re-run produced no formal report (VM cleaned up); re-run
      cleanly once the catalogue-order follow-up lands.
- [x] [DATA] P1. **✅ DONE 2026-07-19 (tick 23) — `market-tick-data-service@7b0768d9`: pinned `deployment_env="prod"` on
      the 3 prediction universe-enumeration catalogue reads (`_polymarket_helpers.py` load + JSON fallback,
      `base_prediction_adapter.py::_load_market_lifecycle_for_date` = Kalshi's universe) — option (a): the market
      universe is global PROD reference data, so under `IS_TEST_RUN` the smoke reads the real prod universe (was empty
      `-test-` → 0 trades). Tick WRITES still isolated to `-test-` (separate bucket kind `market-data-tick-prediction`,
      test-aware, untouched); PROD byte-unchanged; RULE-11. +6 tests; QG green. Smoke-orchestration follow-up — `trades`
      `-test-` catalogue-gating (blocks Phase-D formal green) (surfaced tick 22).** The MTDS batch `trades` adapter
      enumerates its market universe from the `instruments-store-prediction` catalogue via ambient
      `DEPLOYMENT_ENV_SHORT`; on the `IS_TEST_RUN` smoke VM it read the empty `-test-` catalogue → 0 trades fetched →
      force/skip RED. Fix EITHER by (a) ordering the smoke so the IS force leg (which now populates the `-test-`
      catalogue — 182 objects proven tick 22) runs before the MTDS `trades` leg AND making the adapter's catalogue read
      `IS_TEST_RUN`-aware (`deployment_env="test"`), OR (b) accepting the prod-catalogue read as canonical (arguably
      more correct) and marking the `-test-` trades universe as prod-catalogue-sourced. NOT a data-correctness bug. Then
      re-run both skills for a formal all-green Phase-D. (repos: market-tick-data-service)
- [ ] [DATA] P2. **`--day` ruled 2026-08-07 same as the P0 todo above (`2026-08-05`, fallback `2026-06-28`)** — these
      are baseline/mid-migration checkpoints, not the post-migration final gate, so exact day matters less; any
      reasonably representative day works. `data-pipeline-check-is` 3x cadence top-up (relocated 2026-07-25 from the
      parent's "Queued audits + reviews" section). Run `/data-pipeline-check-is --asset-group prediction` twice more — a
      pre-Phase-B baseline checkpoint and a Phase-B mid-migration spot-check — to reach the 3x cadence
      `task_template.md` finding K requires (checkpoint 3, the post-migration final gate, is already this doc's own P0
      todo above). Also tracked as an AO-dispatchable partial-slice execution copy in
      `prediction_consolidated_native_ao_extract_2026_07_25.md` (`status: draft`) todo 2 — that plan's own Done-when now
      cites THIS checkbox's Progress Log (updated 2026-07-25, corpus-wide referrer fixup), not the parent's
      now-relocated section; it explicitly does NOT flip this checkbox itself (only the pre-Phase-B leg lands there —
      the mid-migration leg stays tracked here). Done when: both runs' report paths + dates are cited in this plan's
      Progress Log.
- [ ] [DATA] P2. **`--day 2026-08-05` (fallback `2026-06-28`), ruled 2026-08-07, same as above.** `data-pipeline-check-mtds` 3x cadence top-up (relocated
      2026-07-25 from the parent's "Queued audits + reviews" section). Run
      `/data-pipeline-check-mtds --asset-group prediction` twice more — the same pre-Phase-B baseline + Phase-B
      mid-migration checkpoints as the `-is` todo above — to reach the 3x cadence (checkpoint 3 is this doc's own
      sibling P0 todo above). Also tracked as an AO-dispatchable partial-slice execution copy in
      `prediction_consolidated_native_ao_extract_2026_07_25.md` (`status: draft`) todo 3 — same reconciliation-target
      update as the `-is` todo above. Done when: both runs' report paths + dates are cited in this plan's Progress Log.
- [x] ✅ [REVIEW] P2. **Adversarial AO-dispatch-readiness pass, Track-Y-style — DONE 2026-08-04 (slot-7). 0 findings.
      (relocated 2026-07-25 from the parent's "Queued audits + reviews" section).** Run the same adversarial
      AO-dispatch-readiness pass sports's Track Y ran (method: the archived
      `sports_consolidated_closeout_history_2026_07_24.md`'s "Track Y — PLAN-QUALITY REMEDIATION" section) against
      `prediction_consolidated_closeout_2026_07_18.md` itself: check for bare `§X` shorthand, ambiguous verbs
      (absorb/incorporate/handle/address), delete-tagging inconsistency, missing definition-of-done, stale checkboxes,
      and unsafe digest-checkbox syntax. Also tracked as an AO-dispatchable execution copy in
      `prediction_consolidated_native_ao_extract_2026_07_25.md` (`status: draft`) todo 5 — that plan's own Done-when now
      reconciles evidence back into THIS checkbox (updated 2026-07-25, corpus-wide referrer fixup), not the parent's
      now-relocated section. Done when: findings (or an explicit "0 findings") are recorded in this plan's Progress Log,
      mirroring Track Y's format.
- [ ] [DATA] P0. **MVP backfill readiness gate** — only after A–D green: run the prediction MVP backfills and verify
      manifest-counted canonical rows for each MVP cell (Polymarket + Kalshi × trades + book_snapshot_5, CQG cluster).

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 6 open,
  `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` on a still-open prerequisite (gate
  verified by direct read). Independently, 3 of the 6 (the `-is`/`-mtds` 3x-cadence top-ups and the adversarial
  AO-dispatch-readiness pass) are CONFLICT — already extracted into
  `prediction_consolidated_native_ao_extract_2026_07_25.md` todos 2/3/5. Both P0 skill runs also require an
  operator-given `--day`, which the skills refuse to invent.

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase D section verbatim (8 todos total: 5 done / 3 open at split time). See the parent's Progress Log
  (ticks 10, 15, and especially 19-25 — the smoke-RED triage, Class A/B/C fixes, and the IS 0/14→11/14 re-run) for the
  full session-by-session history of what is already shipped here, and for why formal all-green is not yet cited (SPOT
  flakiness + a canonical-read residual + the MTDS `trades` `-test-` catalogue-gating follow-up, per tick 25). Future
  work on this plan logs new entries below.
- **2026-07-25 (consolidated-closeout split pass) — relocated 3 todos in from the parent's now-forked "Queued audits +
  reviews" section**: the `data-pipeline-check-is` and `data-pipeline-check-mtds` 3x-cadence top-ups, and the
  adversarial AO-dispatch-readiness pass. All 3 placed before the MVP-backfill-readiness-gate todo (their natural
  position — checkpoints feed the gate). Net: open-todo count 3 → 6. No engineering work executed in this pass — pure
  relocation + reconciliation of pre-existing tracked items.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- swapped in the real gating dependency
  (phase_ab_residuals) + the AO extract that duplicates 3 of 6 open todos + the MTDS adapter source (still-open `-test-`
  catalogue-gating follow-up location).
- **2026-08-04 (slot 6, data_engineering) — `data-pipeline-check-is` pre-Phase-B baseline (1 of 2) RUN.** Executed
  `/data-pipeline-check-is --asset-group prediction --day 2026-08-02` (operator-supplied day, per the note above that
  the skill refuses to invent one) as the dispatchable pre-Phase-B leg of this doc's `-is` 3x-cadence top-up todo
  (`prediction_consolidated_native_ao_extract_2026_07_25.md` todo 2 — that plan's own checkbox is flipped for this
  partial slice; this checkbox stays open pending the mid-migration leg, per its Done-when). **Result: partial pass.**
  POLYMARKET force+skip both genuinely PASSED (skip-leg needed one retry after a shared-host `gcloud` identity race —
  see below). POLYMARKET live-leg and every KALSHI leg (force x2 attempts, skip x2 attempts, live x1) FAILED, but all 6
  failures independently confirmed via `gcloud compute operations list` as genuine SPOT preemption of the check-VM
  itself (`compute.instances.preempted`), not a pipeline/code/data-correctness defect — corroborates the already-open
  `asia_northeast1_c_spot_preemption_storm_2026_08_04.md` (preemption rate in `asia-northeast1-c` intensified from
  ~1/6min to ~1/1-2min during this run, 06:07-06:23Z, hitting `expected-universe-v2-sports`/`tradfi-bf-cme-*`/these
  `instr-backfill-pred-pchk-*` check-VMs concurrently). Stopped after 2 KALSHI force+skip attempts + 1 live-leg attempt
  per that doc's "do not blind-loop-relaunch during an active storm" guidance (this is a P2 checkpoint, not a
  hard-deadline gate). **Side finding**: the FIRST POLYMARKET skip-leg attempt failed with a
  `compute.instances.create PERMISSION_DENIED` that was NOT a real IAM gap — diagnosed as a shared-host
  `gcloud config set account` race (a different slot flipped the host-wide active identity mid-run); fixed for this
  session via a slot-scoped named gcloud config (`CLOUDSDK_ACTIVE_CONFIG_NAME=slot6-work` pinned to
  `unified-trading-sa`) rather than mutating shared state; second independent confirmation filed to
  `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`. **Report**:
  `/plans/audit/results/data_pipeline_e2e_check_is_2026_08_02.md` (+ sibling `.json`).
- **2026-08-04 (slot 4, data_engineering) — `data-pipeline-check-mtds` pre-Phase-B baseline (1 of 2) RUN.** Executed
  `/data-pipeline-check-mtds --asset-group prediction --day 2026-08-02` (same day as the `-is` pre-Phase-B baseline
  above, chosen for a comparable pair, not an invented default) as the dispatchable pre-Phase-B leg of this doc's
  `-mtds` 3x-cadence top-up todo (`prediction_consolidated_native_ao_extract_2026_07_25.md` todo 3 — that plan's own
  checkbox is flipped for this partial slice; this checkbox stays open pending the mid-migration leg). **Result: mostly
  failed, 2 real findings + 2 confirmed infra-noise items.** Phase 1 (force+skip, 5 shards): 4/8 real `no_parquet_under`
  failures with `Exit=0` (VM launcher succeeded but no parquet landed at the expected test-bucket path — a genuine
  finding, not yet root-caused, flagged for follow-up) + 1 confirmed genuine SPOT preemption
  (POLYMARKET/prediction_trades skip-leg) + 2 `skipped` (book_snapshot_5 is batch-unfetchable by design). Phase 2 (live
  leg, 4 shards, `--mvp-only`): 2 passed (POLYMARKET/KALSHI trades), 2 failed (book_snapshot_5 — no sampled instrument
  available for a live shard-spec, same batch-unfetchable-by-design shape). **2 operational defects found in the checker
  itself** (both confirmed live, filed as
  `mtds_pipeline_e2e_check_report_overwrite_and_post_completion_hang_2026_08_04.md`): (1) running force+skip and live as
  2 separate invocations silently overwrites the same day-keyed report file — the Phase 1 report was manually
  reconstructed from this session's captured output before being lost for good; (2) the checker process hangs
  post-completion (RSS climbing, no new log output, no VMs left to clean up) — hit TWICE, both times terminated via
  exact-PID `SIGTERM` after independently confirming the report was already fully written, no data lost. Session also
  died mid-Phase-2 for an unrelated reason (self-resumed cleanly, orphaned 2 harmless self-terminating `--test-run`
  smoke VMs, re-ran Phase 2 fresh). **Report** (manually merged, see its own provenance note):
  `/plans/audit/results/data_pipeline_e2e_check_mtds_2026_08_02.md` (+ sibling `.json`, live-leg-only content per the
  overwrite defect above).
- **2026-08-04 (slot-7, review) — Adversarial AO-dispatch-readiness pass, Track-Y-style DONE. 0 findings.** Target:
  `prediction_consolidated_closeout_2026_07_18.md`. Method: `task_template.md` §3 findings C/D/E/F/G/H.
  - C (stale checkboxes): 0 — doc has 0 open `- [ ]` todos (coordination hub, `gate_on_depends: false`,
    `archive_exempt: true`). One `[x]` in "Deferred work" correctly closed (STALE — CLOSED 2026-07-31).
  - D (bare §X shorthand): 0 — all §X references either pair with a full file path inline (e.g. §5.1/§A0 +
    `prediction_consolidated_native_ao_extract_2026_07_25.md`), state the action inline ("CQG residual §5"), or appear
    in narrative prose (Progress Log §1/§2/§11), not as todo first-line shorthand.
  - E (ambiguous verbs): 0 — no open `- [ ]` todos; digest bullets use clear non-ambiguous verbs.
  - F (delete-tagging inconsistency): 0 — no open `- [ ]` todos with delete operations.
  - G (missing definition-of-done): 0 — no open `- [ ]` todos.
  - H (unsafe digest-checkbox syntax): 0 — all aggregated-source-docs digest entries use `**[TAG] P<n>.**` bold format.
    Line 457 `- [VERIFY]**[UI] P0.**` is non-standard but NOT parseable by regen
    (`_UNCHECKED_RE = r"^\s*-\s+\[ \]\s+(.+)$"`; `[VERIFY]` ≠ `[ ]`, does not match). Verdict:
    `prediction_consolidated_closeout_2026_07_18.md` passes adversarial AO-dispatch-readiness review clean.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: KEEP-NA, valid — all 5 open todos reconfirmed.
  Items 1/2 (post-migration IS/MTDS formal green) + item 5 (MVP backfill gate): `depends_on` + `gate_on_depends: true`
  prerequisite (`prediction_phase_ab_residuals_2026_07_24`) freshly verified still open (still `status: active`, its own
  `[DATA] P0` enumeration-driven migration todo still `[ ]` unchecked as of today). Items 3/4 (the `-is`/`-mtds`
  3x-cadence top-ups): **independently re-verified against two disagreeing sub-agent passes this run** — one flagged
  RECLASSIFY (citing no active doc covering the mid-migration leg, true but incomplete), the other flagged KEEP-NA
  citing `prediction_consolidated_native_ao_extract_2026_07_25_finalize.md`'s 2026-08-04 slot-15 note ("Phase B has NOT
  landed... 3rd/final post-Phase-B pass still genuinely blocked") — **that citation is a misattribution**: the slot-15
  note is about `prediction_phase_ab_residuals_2026_07_24.md`'s OWN, DIFFERENT `/data-pipeline-reconciliation` cadence
  todo (explicitly documented elsewhere in the same finalize doc as "no overlap — a NARROWER, DIFFERENT check" vs. this
  doc's `data-pipeline-check-is`/`-mtds` items). Direct live read of `prediction_phase_ab_residuals_2026_07_24.md`
  confirms the underlying FACT is still correct by coincidence: its `[DATA] P0` Phase-B `--apply` migration has
  genuinely not started (still `[ ]`, dry-run only). Since items 3/4's remaining scope is specifically a "Phase-B
  **mid-migration** spot-check" (pre-Phase-B leg already done + cited 2026-08-04), and there is no migration currently
  in flight to spot-check, dispatching now would not serve the checkpoint's purpose — stays NA pending Phase-B `--apply`
  actually starting, not because of a duplicate claim (none found, confirmed via `plans/`-wide grep for "3x
  cadence"/"cadence top-up") and not a design/judgment gate, just a genuinely-not-yet-timely bounded task. Re-check once
  `prediction_phase_ab_residuals_2026_07_24.md`'s P0 migration todo shows `--apply` in progress.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 5 open items; same dispatch gate re-confirmed live. Content
  changed since 2026-08-06 (an operator `--day 2026-08-05` ruling was added 2026-08-07) but that doesn't clear this
  doc's own gate.

- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none clear the `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` gate; re-confirmed
  live the prerequisite still has 7 open todos, Phase-B `--apply` still hasn't started. The already-incorporated `--day`
  ruling (2026-08-05, fallback 2026-06-28) is not new round-11 information. No reclassification.
- **na-eligibility-audit 2026-08-10 (prediction tranche)**: KEEP-NA, valid — re-verified live, 5 open, unchanged.
  `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` still open (prerequisite still
  status:active, 7 open todos, Phase-B `--apply` not started). Doc stays NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries) -- re-verified, unchanged.
- **na-eligibility-audit 2026-08-18** [body-hash:39431b602f991e5b]: KEEP-NA, valid -- depends_on+gate_on_depends:true on prediction_phase_ab_residuals_2026_07_24 re-confirmed live still open (its own P0 migration todo unchecked). All 5 open items here are downstream of that unfinished migration. Doc stays NA.
- **na-eligibility-audit 2026-08-19 (prediction tranche, dispatch agt-0e920e)** [body-hash:fe46fdb5946a427f]: KEEP-NA,
  valid — `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` re-confirmed live still
  open (that doc independently re-verified this same run: 4 open todos, P0 migration item still unchecked). All 5
  items here reduce to that same unfinished gate. Doc stays NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
