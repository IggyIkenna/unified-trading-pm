---
doc_type: plan
title: Instruments remaining-work audit — Progress Log history (2026-07-10 authoring-day synthesis + dispatch narrative)
summary: >-
  Line-cap remediation extraction from plans/active/issues/instruments_remaining_work_audit_2026_07_10.md's Progress Log
  — the full 2026-07-10 authoring-day narrative (the original 83-doc corpus sweep, the §1a CODE_PATH conflict review,
  the 12 operator decisions, the COINBASE-CDE split dispatch, and the wf_60ecfd13-752 P0-wave results), moved verbatim
  so the live doc stays at/under the 1000-line hard cap after a na-eligibility-audit marker addition pushed it to 1003L.
  The live doc's own "Headline P0s" section already carries the current-state summary; this file is the full narrative
  trail behind it — read it only if a deeper citation on a specific 2026-07-10 finding's reasoning is needed.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [instruments, audit, history, line-cap-remediation]
related: [/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md]
created: 2026-08-06
last_updated: 2026-08-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "na-eligibility-audit cross-cutting, dispatch agt-6925b7, 2026-08-06 -- line-cap remediation triggered by this run's
  own KEEP-NA marker addition"
context_scope: [/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md]
---

# Instruments remaining-work audit — Progress Log history (2026-07-10)

> Extracted verbatim from `plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`'s Progress Log,
> 2026-08-06, to keep the live doc under the 1000-line hard cap. This is the FULL 2026-07-10 authoring-day narrative;
> the live doc's later short entries (2026-07-30 onward) stay in place there.

## Progress Log (2026-07-10 entries)

- **2026-07-10 (later still) — sub-agent verification pass on 3 of the §0 headline P0s (Instruments Completion Tracker
  dispatch).** (1) **Headline #6 / §2.1 Turbo API 0/0 bug**: partially re-verified — NOT reproducible today via the
  exact function chain `/turbo` wraps (all 8 originally-flagged venues now show correct real coverage on a direct
  prod-GCS call); root cause was never identified so this is "no longer reproducing," not "confirmed fixed" — a live
  HTTP `/turbo` cross-check with cache cleared is the remaining confirming step. One smaller, different residual bug
  found (`PUFFER-ETHEREUM` internal found/captured-count inconsistency). Detail in
  `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. (2) **Headline #3 / §1
  is-daily-enum-{prediction,sports} exit(1)**: CONFIRMED still genuinely failing daily through 2026-07-09; new
  diagnostic finding — the failing execution produces ZERO application-level log lines at all (not even the wrapper's
  trivial startup line) across its full 15-min runtime, a stronger/different symptom than "exc_info swallowed," pointing
  to either a Cloud Logging delivery gap or a silent hard-kill (OOM candidate: the still-open
  `manifest_consolidator_dtype_at_source_fix` utf8-mistyped-numeric-columns finding would inflate in-memory footprint
  for exactly these two large poisoned indexes). Detail in
  `issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`. (3) **§2 MANIFEST_COVERAGE — KALSHI-PERP
  contamination purge**: CONFIRMED fully resolved via live GCS read (0 KALSHI-PERP / 0 POLYMARKET-PERP rows in the cefi
  manifest) — `prediction_capture_incident_remediation_2026_07_06.md` Phase 0 fully closed, and
  `instruments_completion_tracker_2026_07_06.md` Stage 3's KALSHI-PERP prerequisite is cleared (a NEW, different blocker
  now gates Stage 3 instead — a concurrently-running sibling workflow rewriting the cefi denominator files live). No
  code changed in this pass — all 3 findings are read-only live verification (GCS reads, direct service-layer calls,
  `gcloud logging`/`gcloud run` queries). `unified-trading-pm@c5828c496` + this commit.
- 2026-07-10: Synthesized from a 4-shard parallel sweep of 83 real doc-index-derived candidate lines across
  `plans/active/**`; 62 docs kept as genuinely open non-backfill work across 7 categories, 16 excluded as
  resolved-but-not-flipped, 3 fragment lines flagged uncaptured. Read-only audit — no code or plan checkboxes changed.
- 2026-07-10 (later): Added category definitions (§ Category definitions) and a full CODE_PATH conflict +
  target-architecture review (§1a) per operator request. Re-verified and flipped 15 of the 16 excluded docs for real
  (`unified-trading-pm@8f15f8233`); the 16th (`bybit_spot_manifest_stray_captures_2026_07_07.md`) was found to still be
  genuinely open — its checkboxes claimed done but production data shows the fix was never actually applied — moved into
  §2 MANIFEST_COVERAGE P0 instead of flipped. §1a found 2 real mutual conflicts (item #3/#8 COINBASE-FUTURES
  contradiction, item #4/#5 sequencing risk) and 3 items diverging from documented target architecture (items #10, #11,
  #13) among the 14 CODE_PATH items.
- 2026-07-10 (later still): **COINBASE-FUTURES/#3-vs-#8 conflict RESOLVED with real, independently-verified evidence**
  (2 live API cross-checks, both confirmed). Real determination: `COINBASE-FUTURES` is wired identically on BOTH the
  reference-data (`instruments-service`) and live (`market-tick-data-service`) paths to Tardis `coinbase-international`
  / native Coinbase INTX — which genuinely has ZERO dated futures (0 `FUTURE`/`OPTION` confirmed on 2 independent live
  APIs: Tardis 273-symbol listing + Coinbase's own `api.international.coinbase.com` 301-instrument listing, both
  `perpetual`/`spot` only). Item #3's "phantom FUTURE, verified 3 ways" claim is **confirmed correct** for this venue.
  **But item #8's shipped live connector is not simply wrong either** — Coinbase Derivatives Exchange (CDE, the real
  source of `FUTURE`-shaped contracts, e.g. `BIT-31JUL26-CDE` real dated expiry) is a genuinely real, currently-trading,
  99-real-contract product family — confirmed live via
  `api.coinbase.com/api/v3/brokerage/market/products? product_type=FUTURE` — but CDE is **not covered by Tardis at all,
  under any name** (confirmed against the full 62-exchange Tardis registry) and is architecturally a completely separate
  Coinbase product from INTX (own domain, own symbol shape, zero overlap — confirmed by paginating Coinbase's ENTIRE
  Advanced Trade catalog, 1035 real products, zero contain `INTX`). **This is finding-type (3) from the original task
  brief: a real venue-scope gap, not a phantom-type bug in either doc.** Real, previously-uncaught bug found as a
  byproduct: item #8's connector's own code/tests assume a fabricated `BTC-PERP-INTX`-style symbol that Coinbase's
  Advanced Trade WS will never emit (confirmed: zero `INTX` string anywhere in `instruments-service`, zero INTX products
  in the 1035-product Advanced Trade catalog) — the live subscription path likely feeds this connector real INTX-shaped
  ids (resolved from IS's canonical universe) against an endpoint that has never heard of them, a silent zero-row
  capture-gap class this workspace's HARD RULE treats as review-blocking (not yet confirmed against real production
  parquet — the one remaining unverified inference, honestly flagged as such by both the investigation and independent
  verify passes). **Real fix, not yet implemented**: register `COINBASE-CDE` as its own venue key (real dated futures,
  needs a brand-new reference-data adapter since Tardis has zero coverage — `api.coinbase.com`'s Advanced Trade REST is
  a viable no-auth first-party source), re-key `coinbase_futures_ws.py` from `COINBASE-FUTURES` to `COINBASE-CDE` (the
  parsing logic itself is real and correct, only its venue identity is wrong), and scope/rename the existing
  `COINBASE-FUTURES` key to INTX-only (matching item #3's proposed fix — drop the phantom `FUTURE` type, add the real
  missing `SPOT_PAIR`). Dispatched for execution, see below.
- 2026-07-10 (later still): **12 operator decisions made**, closing every real `BLOCKED-OPERATOR-DECISION`/pending-call
  item surfaced across this whole audit doc (not just §1a's CODE_PATH conflicts). Full record:
  1. **OKX-SPOT venue registration**: Option A — declare its own cefi venue (matches BYBIT-SPOT precedent), remove the
     `_CEFI_VENUE_FOLD` entry. (`cefi_layer1_denominator_gaps_2026_07_03.md`,
     `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`)
  2. **DeFi expected_unattempted backlog**: approve the FULL 1,380,376-row apply in one run (99.95% is honest 2018-2019
     pre-launch documentation, zero downloads triggered). (`defi_expected_unattempted_backlog_1m_2026_07_03.md`)
  3. **COINBASE bare-name migration**: flip `coinbase_bare_name_migration_2026_07_06.md` from `draft` to `active`,
     dispatch its full 7-step (S0-S7) plan now.
  4. **UAC data-type-validity fragmentation**: approve the proposed two-layer redesign (real provably-wrong cell exists
     today — CME/ICE share identical valid-data_types despite ICE having no real Databento coverage).
     (`uac_data_type_validity_combinator_fragmentation_2026_07_07.md`)
  5. **TradFi `mvp_mode` dead fetch-time filter**: **REVISED from the earlier §1a recommendation** — operator wants this
     built for real, universally: every asset group should have a real `--mvp`-style fetch mode that pulls canonical MVP
     instruments via the existing catalogue MVP tags/SSOT (real infrastructure already exists —
     `unified_api_contracts/canonical/crosscutting/_mvp_scope_*.py`, `enumerate_expected_universe.py`'s MVP gate — but
     is not consistently wired as a fetch-time filter everywhere). Needs real investigation into what MVP-tag SSOT
     already exists before implementing, not a fresh design. (`tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`)
  6. **Bare COINBASE / DERIBIT-COMBO in MVP_SCOPE.venues**: keep both declared. **Additional real cost-control ask**:
     COINBASE (INTX) should be reduced to `trades`-only data_type — operator notes book-snapshot-class data is
     expensive/memory-intensive for this venue and recalls a possible existing mechanism for this kind of per-venue
     data_type scoping — needs investigation before assuming a new mechanism is required.
     (`cefi_layer1_denominator_gaps_2026_07_03.md`)
  7. **ARCHETYPE_CAPABILITY_REGISTRY missing CEFI cells**: add the missing cells for `CARRY_BASIS_PERP_INV`/
     `CARRY_STAKED_BASIS` × BYBIT/OKX/DERIBIT (registry catches up to the codex claim, not the reverse).
     (`archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md`)
  8. **Kraken FI\_/FF\_ contract-subtype collision**: reuse the existing `@LIN`/`@INV` marker convention (this session's
     own canonicalization decision) rather than inventing a new contract-subtype field — 13 real (ticker, expiry) pairs
     affected, the 2 most liquid (ETH/XBT). (`canonical_id_p0_kraken_futures_collision_2026_07_08.md`)
  9. **6 DeFi venues declared `phase=live` with no backing capability**: add the missing capability-registry entries
     (venues are intended live, close the registry gap rather than downgrade the label).
     (`defi_code_codex_drift_2026_05_27.md`, item D10)
  10. **Pyth Hermes jitoSOL pre-2023-10 backtest scope**: include it — no data-quality problem was flagged for that
      window. (`defi_onchain_derivable_values_and_date_drift_2026_06_20.md`)

  All 10 distinct decisions (covering 12 originally-listed BLOCKED items — some were duplicate/tied) dispatched for
  execution as real code/data changes, not just recorded as resolved-in-principle. See Orchestration state below for the
  dispatched workflow(s).

- **2026-07-10 (later still)**: **COINBASE-CDE split + new adapter + live connector fix SHIPPED** (the
  COINBASE-FUTURES/#3-vs-#8 conflict's real fix, dispatched above). All 3 items landed real, live-verified code —
  `unified-api-contracts@1cafb3c5` (registered `COINBASE-CDE` venue: `INSTRUMENT_TYPES_BY_VENUE={"FUTURE"}`,
  `venue_adapter_keys.py` → `coinbase_cde`, `venue_mapping.py` native-REST routing + start date; rescoped
  `COINBASE-FUTURES` to `{"PERPETUAL","SPOT_PAIR"}` INTX-only, dropping the phantom `FUTURE` and adding the real
  previously-missing `SPOT_PAIR`), `instruments-service@94512ec3` (new `CoinbaseCdeReferenceDataAdapter` sourced from
  Coinbase's public Advanced Trade REST, no-auth, live-verified: 99 real FUTURE instruments, real funding-rate
  distinction between far-dated "nano perpetual" contracts and near-dated dated futures; wired into `factory.py`;
  regenerated `expected_universe/cefi.json` golden), `market-tick-data-service@cdbbdb9b` (re-keyed
  `coinbase_futures_ws.py` → `coinbase_cde_ws.py`, removed the fabricated `-INTX` symbol shape, live end-to-end
  re-verified against `wss://advanced-trade-ws.coinbase.com` with a real captured cassette). The flagged silent
  capture-gap inference is CONFIRMED: a live production manifest read
  (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 2026-07-10) shows the
  pre-fix connector recorded ZERO real rows under any live pipeline_mode since it shipped (`mtds@fd436aea`, 2026-07-06)
  — all 16,819 real `COINBASE-FUTURES` manifest rows are `batch_tardis`, versus real populated
  `live_binance`/`live_bybit`/`live_deribit`/`live_hyperliquid`/`live_kraken`/`live_okx` pipeline_modes for the other
  live-wired CeFi venues. Both `wsfeedconnector_phase35_gap_2026_07_06.md` and
  `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` updated with the full resolution in their own Progress Logs.
  **Multi-agent note**: this dispatch hit repeated destructive `git reset --hard origin/live-defi-rollout` events on the
  shared `unified-api-contracts` working tree from other concurrent sibling sessions mid-task (at least 3 separate
  incidents, each discarding locally-committed-but-unpushed work, confirmed via `git reflog`) — all recovered by redoing
  the edits from a fresh read each time and pushing immediately once committed; no data lost, but flagging the pattern
  as worth a workspace-level look (an unattended `reset --hard` cycle against a SHARED branch is itself a
  HARD-RULE-adjacent risk, distinct from the expected/normal shared-dirty-tree contention this session's sub-agent brief
  already anticipated).

- 2026-07-10 (later still): **`wf_60ecfd13-752` (P0 wave) COMPLETE — 6/6 agents returned, honest mixed outcome, no
  false-done claims.**
  1. **Turbo API 0/0 — mostly fixed.** Root cause was 2 distinct bugs: (a) the `/turbo` staleness gate read a
     non-existent `meta.updated` attribute instead of `meta.last_modified`, so a frozen rollup blob (stale since
     2026-07-05, rollup-worker Scheduler outage) never triggered on-demand fallback — already fixed pre-session by
     `deployment-api@3847d6f`, now confirmed live; (b) SPARK-ETHEREUM stuck on a stale
     `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` flag despite 7,405 real captured rows, + 5 LST venues with zero
     `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entries despite real captured data — fixed `unified-api-contracts@92b1d1a8`
     with a 4-test regression class. New smaller finds, not yet fixed: PUFFER-ETHEREUM found=0 vs captured=21;
     HYPERLIQUID/ASTER confirmed genuinely undeclared in `ALL_DEFI_VENUES` — filed as a new P1 (distinct CEFI/DEFI
     axis-model design question).
  2. **CeFi monotonicity alerting — fixed.** Two distinct findings: the "dark venue" claim was a stale rename artifact
     (LIGHTER/PACIFICA/EXTENDED re-keyed to `*-ZKSYNC`/`*-SOLANA`/`*-STARKNET` 2026-06-25, new keys have unbroken
     captures — no real outage); the OOM was real (`uts-prod-instruments-service-cefi-t1-recon` failed 100% of 11
     straight days) and fixed by bumping 2cpu/4Gi→8cpu/16Gi, verified via a real `gcloud run jobs execute --wait`
     success (`uts-prod-instruments-service-cefi-t1-recon-jt7w8`, 1m2.14s). Full alerting path shipped (UTL event
     constant → UAC `DP-CATALOG-002` → `log_event()` → alerting-service notifier) across 6 repos. Deferred: generalizing
     `_enforce_defi_monotonicity` into `venue_core.py` (real live-file conflict with a concurrent sibling workflow all
     session).
  3. **is-daily-enum-{prediction,sports} crash — STILL OPEN, no fix landed.** Real actionable lead found: the
     already-landed UTL `exc_info` fix (`unified-trading-library@b7925334`) is present in the current UTL `:latest`
     image but the DEPLOYED `instruments-service:latest` image's Dockerfile still pins an older UTL base digest — **this
     is the same class of stale-deployed-image gap independently found by `wf_860fb2ae-54e` for `is-daily-enum-cefi`**
     (pinned to a pre-`@LIN`/`@INV`-fix build). A local repro (`daily_is_enumeration.py --asset-group prediction`) was
     still running in the background when the agent's dispatch window closed — no traceback captured yet, root cause not
     fully confirmed.
  4. **59-bug smoketest — substantial real progress, 9 todos flipped with commit-sha evidence** across
     `unified-api-contracts@42ce2de3`, `instruments-service@9b0c1095`, `market-tick-data-service@f4a118be`,
     `unified-trading-pm@185c7397d`. Real fixes: Polymarket order-book schema (`[[price,size]]`→`[{price,size}]`, was
     crashing every real fetch), 7 DeFi venues flipped pipeline→live phase, Curve factory-pool undercount (49 vs real
     2,372 pools — switched to Curve's combined "all" endpoint), SolBlaze dead-endpoint fix (live production path, not
     dead code). Deliberately deferred: HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT registration (needs a quiet window — same
     UAC registry files under continuous concurrent edit all session). **Superseded 2026-07-12**: this was never a
     "needs a quiet window" deferral — it was a real SSOT contradiction with a same-week peer commit, resolved by the
     operator against registration. See `huobi_bitstamp_htx_ssot_contradiction_2026_07_10.md`'s Resolution section.
  5. **Instruments Completion Tracker — honest partial progress.** Confirmed KALSHI-PERP contamination genuinely purged
     (live read: 0 contaminated rows) — closed 1 real prerequisite. Explicitly recommends **waiting to re-measure Stage
     3** until the concurrent sibling workflows quiesce (a mid-flight remeasure would capture a moving-target
     denominator, not a real number).
  6. **Layer-1 tradfi block — partial, correctly disciplined.** Task 3 verified done + flipped. Task 2 (orphan sweep)
     unblocked + launched (nohup, PID 22320, ~850K objects swept and climbing at session end, ETA 1.5-2h, survives
     independent of session). Tasks 4/6/10 re-audited and correctly LEFT UNFLIPPED (task 6 found a new 520-row CF-4 gap
     from still-running pre-fix tarball VMs; task 10 confirmed 8 `tradfi-bf-*` VMs still running, fleet not drained).
     **Task 11 (legacy-twin bucket deletes) deliberately NOT executed** — correctly identified that the dispatch
     briefing's "pre-approved" framing didn't override `migration_verification_orphan_safety_2026_06_10.md`'s explicit
     HARD-STOP requiring real operator sign-off for an irreversible delete; a briefing paraphrase is not that sign-off.

  **Cross-cutting new finding**: the stale-deployed-image gap (item 3 above) affects BOTH `is-daily-enum-cefi` (per
  `wf_860fb2ae-54e`'s CeFi durability check) and `is-daily-enum-{prediction,sports}` (per this workflow) — a single
  `instruments-service` image rebuild + redeploy is a plausible one-shot fix for two separate open P0s. Investigating
  next.
