---
doc_type: plan
title: "MVP Phase 4 — reconciliation closeout (align codex + plans to canonical v10, resolve flagged items)"
summary:
  "Reconcile codex + every active plan to the canonical MVP v10 scope + the budget constraints, resolve the remaining
  flagged items (MANIFEST_ALLOW_STALE_FALLBACK, a163/G1.2, Kalshi launcher, HL/ASTER docs), and archive superseded
  plans."
nature: process
stage: [meta]
repos: [unified-trading-pm, deployment-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [mvp, reconciliation, codex-alignment, v10, closeout, plan-hygiene, honest-coverage]
related: []
created: 2026-06-27
parent_epic: infrastructure_master
priority: P1
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: correct-codex
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - mvp_catalogue_finalization_v10_2026_06_27
  - mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27
  - mvp_backfill_cefi_tick_v10_2026_06_27
  - mvp_backfill_defi_onchain_v10_2026_06_27
related_plans:
  - plans/active/mvp_catalogue_finalization_v10_2026_06_27.md
  - plans/active/instruments_foundation_completeness_2026_06_24.md
  - plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md
asset_group: cross-asset
---

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** Phase 4 of the remaining MVP arc handed to the
> agent-orchestrator (`planning` VM). One agent, one craft (`data_engineering`), Sonnet/high.
> `drift_direction: correct-codex` — this plan fixes stale docs/plans TOWARD the canonical v10 scope.
>
> **Canonical MVP SSOT (the ONLY scope authority):** `mvp_scope.py` v10 + `codex/02-data/mvp-scope-canonical.md`. Per
> the workspace HARD RULE the SSOT is a codex doc / code, NEVER a plan. **Direction of reconciliation: where any
> existing active plan's MVP/scope CONFLICTS with v10, fix the PLAN to v10 — never the reverse.** This plan is the
> single place that enumerates + closes every such conflict so background agents cannot follow a stale definition.

## Codex SSOTs (READ before executing)

- `codex/02-data/mvp-scope-canonical.md` (v10) — the authority everything reconciles to.
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — MANIFEST_ALLOW_STALE_FALLBACK escape-hatch contract.
- `codex/02-data/honest-absence-downstream-handling.md` — HL/ASTER + DERIBIT-COMBO honest-absence; reason taxonomy.
- `codex/02-data/mvp-scope-canonical.md` § Prediction — Kalshi IN MVP; data_types trades / cqg / market_lifecycle.
- `plans/PLAN_FORMAT.md` + `plans/epics/README.md` — archival 5-step ritual; plan-hygiene QG.

## The 7 v10 decisions every plan must agree with (the reconciliation target)

1. Sports = 94 FOOTBALL leagues (NOT 2-league EPL+LA_LIGA). 2. CeFi OPTION = options_chain ONLY. 3. BINANCE-DELIVERY
   dropped. 4. LIGHTER/EXTENDED/PACIFICA are CeFi. 5. Kalshi IN MVP. 6. TradFi = ohlcv_1m ONLY. 7. Sports structural
   gaps via `is_sports_structural_gap()`.

---

## Todos

### R1 — enumerate + fix plans whose MVP/scope CONFLICTS with v10 (the keystone)

- [ ] [AUDIT] P0. Re-run the conflict scan to produce the CURRENT authoritative list of plans whose MVP/scope disagrees
      with v10 (the scan below was run 2026-06-27 at authoring time; re-run because plans move). Repo:
      `unified-trading-pm`. **Run:** `rg -n -i "EPL.*LA_LIGA|2.league|SportsMvpRule.*4 leagues" plans/active/*.md`;
      `rg -n "ohlcv_1s" plans/active/*.md`; `rg -n "BINANCE-DELIVERY" plans/active/*.md`;
      `rg -n -i "LIGHTER|EXTENDED-STARKNET|PACIFICA" plans/active/*.md`;
      `rg -n -i "kalshi.*(post.mvp|not.*mvp|excluded)" plans/active/*.md`;
      `rg -n -i "options.*(trades|book_snapshot_5).*MVP|per-strike.*MVP" plans/active/*.md`. **Gate:** an updated
      conflict table in this plan's Progress Log (plan path + line + the v10 rule it violates + verdict: FIX /
      HISTORICAL-CONTEXT-OK). SPOT N/A.
- [ ] [SCRIPT] P0. Fix the SPORTS pre-v10 MVP-rule references. **Known conflict (2026-06-27):**
      `plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` L1223/L1234 describes
      `MVP_SCOPE["sports"]` as a 4-league `SportsMvpRule` (EPL/LA_LIGA/...) — that is the PRE-v10 definition.
      **Action:** add an inline `> **[v10 RECONCILED 2026-06-27]**` note at those lines pointing to v10 (sports MVP = 94
      FOOTBALL leagues via `_mvp_football_league_ids()`, NOT 4/2 leagues), so an executing agent does not act on the
      stale count. Do NOT rewrite the historical narrative — annotate it as superseded. **Gate:** both lines carry the
      v10-reconciled note; `mvp_scope.py` confirmed to implement the 94-league rule (it does, v10). SPOT N/A.
- [ ] [SCRIPT] P0. Confirm the remaining hits are HISTORICAL-CONTEXT (not active scope drivers) and annotate any that
      could mislead. **Triage (2026-06-27 authoring scan):** (a) `cefi_manifest_canonicalisation_2026_06_01.md` L176-273
      `options_chain→{trades}` — this is describing the manifest PATH SHAPE (`data_type=trades` is the parquet axis
      inside an options_chain shard), NOT an instruction to backfill per-strike option trades; verify and, if ambiguous,
      annotate that v10 captures Deribit OPTION as options_chain only (no separate per-strike trades/book5 backfill).
      (b) tradfi `ohlcv_1s` hits (`tradfi_multisource_backfill_2026_06_22.md`,
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`, etc.) — most describe the L0 16y FLOOR / a
      features-read dependency, not an MVP backfill of 1s; verify none drives a 1s BACKFILL and annotate v10 (ohlcv_1m
      ONLY) on any that does. (c) BINANCE-DELIVERY / LIGHTER / PACIFICA hits in `instruments_foundation_completeness` /
      `data_completion_to_100_all_ag` — confirm they reflect the v10 catalogue (BINANCE-DELIVERY dropped from MVP;
      LIGHTER/EXTENDED/PACIFICA = CeFi). **Gate:** every scan hit classified FIX-or-OK in the Progress Log; any FIX
      annotated. SPOT N/A.

### R2 — resolve the flagged operational items

- [ ] [SCRIPT] P0. Revert MANIFEST_ALLOW_STALE_FALLBACK once the per-AG consolidators are confirmed re-deployed on the
      fixed image + re-enabled. Repo: `deployment-service`. **Context:** baked `true` at
      `scripts/vm/launch-cefi-instruments-backfill.sh:138` (+ the GCS-uploaded `setup-data-pipeline-vm.sh` copy) as the
      interim escape-hatch while the cefi instruments consolidator was DOWN (tracked
      `instruments_foundation_completeness_2026_06_24.md` L1129-1139). **Action:** confirm
      `uts-prod-manifest-consolidator-instruments-cefi-cron` is ENABLED on the fixed image (`dd17ce23`) with a fresh
      `_index` heartbeat, THEN remove/clear the env from the launcher line 138 + re-upload the VM setup script. Leaving
      it `true` permanently masks consolidator outages — that is the bug this reverts. **Gate:** consolidator ENABLED +
      fresh; `rg -n MANIFEST_ALLOW_STALE_FALLBACK deployment-service/scripts/vm/launch-cefi-instruments-backfill.sh`
      shows it removed; QG green; quickmerged. SPOT N/A. (If the consolidator is still DOWN → leave as-is, record the
      blocker, do NOT revert prematurely.)
- [ ] [SCRIPT] P0. Close a163 G1.2 — capture-time `record_failed` routing + the 2026-06-26 full re-capture. Repos:
      `instruments-service`, `deployment-service`. **Context:** `instruments_foundation_completeness_2026_06_24.md`
      L338-350/L1464 — the thin-day drawdown METRIC shipped (`scripts/cefi_cumulative_drawdown_guard_2026_06_27.py`,
      `instruments-service@cc81cad`); REMAINING = (a) wire the thin-day verdict into the capture path so a partial venue
      day records `attempted_failed` at write time (never overwrite a full prior day → the 06-26 partial drove
      BINANCE-FUTURES 678→47 + 8,520 false-delists); (b) re-capture 2026-06-26 in full once the producer image carries
      the fix. **Action:** implement (a) in `_finalize_completeness`/`process_completeness`; run (b) on a SPOT VM. This
      MUST land before/with the cefi catalogue sign-off (Phase 0 depends on correct active counts). **Gate:** a partial
      venue response → `attempted_failed`; 06-26 fully re-captured; BINANCE-FUTURES active count correct (~678, not
      ~47); QG green; quickmerged. **Full-execution criterion:** real re-capture VM + the corrected `_index` counts.
      SPOT VMs only (re-capture).
- [ ] [SCRIPT] P1. Kalshi book5/lifecycle launcher decision (build only if MVP needs it). Repo: `deployment-service`.
      **v10 prediction data_types = trades · prediction_canonical_question_group · market_lifecycle/MARKET_LIFECYCLE**
      (book_snapshot_5 is NOT a prediction MVP batch data_type — it was retired for forward-poll 2026-04-19 and is
      live-only depth). **Existing coverage:** Kalshi trades = `launch-kalshi-bulk-seed-vm.sh` (deep history, NOTE: this
      launcher is on-demand, not SPOT — acceptable as a one-off campaign, but flag it) +
      `launch-mtds-prediction-backfill-vm.sh --venue KALSHI`; market_lifecycle is written by instruments-service (IS),
      not an MTDS live VM (IS write fix shipped `instruments-service@4105bba3`). **Action:** confirm Kalshi trades +
      cqg + market_lifecycle are covered by existing launchers/IS producer; only BUILD a new launcher if a v10 MVP
      data_type has no path. Do NOT build a Kalshi book5 backfill launcher (not MVP). **Gate:** a written coverage
      verdict (each v10 prediction data_type → its launcher/producer); a new launcher only if a genuine gap exists. SPOT
      N/A (decision) / SPOT if a new backfill launcher is built+run.
- [ ] [SCRIPT] P1. HL/ASTER honest-absence docs confirmed current vs v10. Repos: `unified-trading-pm` (codex),
      cross-check `market-tick-data-service`. **Context:** already shipped + documented —
      `codex/02-data/mvp-scope-canonical.md` L36 (deferred-no-source) +
      `codex/02-data/honest-absence-downstream-handling.md` L613 + issue doc
      `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` (HL trades pre-2025-03-22 →
      `EXPECTED_PRE_SOURCE_COVERAGE_START`; ASTER book5+liquidations → `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE`;
      manifest purge of 48,701 stale cells DONE). **Action:** verify the manifest still shows HL/liquidations=0,
      ASTER/book5=0, ASTER/liquidations=0 in the batch manifest; confirm the codex docs match the shipped behavior
      (correct-codex if drifted). **Gate:** verification recorded; codex matches code; the issue doc archivable if fully
      closed. SPOT N/A.

### R3 — archive superseded plans + final hygiene

- [ ] [AUDIT] P1. Identify + archive plans superseded by this v10 work (the 5-step archival ritual; respect locks).
      Repo: `unified-trading-pm`. **Candidates (verify each against its DoD before archiving — do NOT archive
      blindly):** plans fully subsumed by the v10 catalogue + the 3 v10 backfill plans (e.g. older per-AG MVP-tagging /
      pre-v10 scope plans). `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` is ALREADY archived (do not re-touch).
      `cicd_staging_main_deadcode_retirement_2026_06_27.md` carries `superseded_by` but is a CI/CD plan (out of this
      scope — leave). **Action:** for each genuinely-superseded plan run the 5-step ritual (migrate DEFERRED todos →
      SUPERSEDED banner → codex-alignment check → update CLAUDE.md/codex on any new contract → clear lock); a locked
      plan needs `[unlock-plan]` (ASK the operator, never autonomous). **Gate:** archived plans listed in the Progress
      Log with the ritual steps evidenced; nothing archived that still has open non-superseded todos. SPOT N/A.
- [ ] [SCRIPT] P0. Post-phase codex audit + plan-hygiene green. Repo: `unified-trading-pm`. **Action:** run
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` (frontmatter / todo-format / runbook / orphan-count=0) and
      `python3 scripts/plans/regenerate_active_plan_inventory.py`; confirm the 4 new v10 plans + this plan resolve
      `assigned_vm: planning` in `orchestrator_vm_registry.yaml` and are ingested (`status: active`, not draft). Update
      `codex/02-data/mvp-scope-canonical.md` `last_reviewed` only if a contract changed. **Gate:** hygiene sweep PASS (0
      orphans, 0 hard failures); inventory regenerated; codex↔plan drift = 0. SPOT N/A.

---

## Progress Log

### Conflict scan (authoring-time, 2026-06-27 — re-verify in R1)

| Plan                                                            | Line       | v10 rule violated                                                             | Verdict                                                                    |
| --------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `instruments_mtds_subset_consistency_remediation_2026_06_17.md` | 1223, 1234 | #1 sports = 94 leagues (plan says 4-league `SportsMvpRule` EPL/LA_LIGA)       | FIX (annotate v10)                                                         |
| `cefi_manifest_canonicalisation_2026_06_01.md`                  | 176-273    | #2 options=options_chain only (describes `options_chain→{trades}` path shape) | VERIFY — likely HISTORICAL path-shape, annotate if ambiguous               |
| `tradfi_multisource_backfill_2026_06_22.md`                     | 96-114     | #6 tradfi=ohlcv_1m only (mentions ohlcv_1s L0 floor)                          | VERIFY — likely floor/derived not a 1s backfill, annotate if it drives 1s  |
| `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`      | 77-124     | #6 tradfi=ohlcv_1m only (features-read of ohlcv_1s)                           | VERIFY — read-path dependency, annotate if it drives 1s backfill           |
| `instruments_foundation_completeness_2026_06_24.md`             | 1117-1440  | #3/#4 (BINANCE-DELIVERY / LIGHTER / PACIFICA counts)                          | VERIFY reflects v10 catalogue (BINANCE-DELIVERY non-MVP; LIGHTER/etc CeFi) |
| `sports_canonical_universe_..._2026_06_24.md`                   | 122        | #1 (EPL/LA_LIGA as parallel-VM example)                                       | VERIFY — example, likely OK                                                |

_(R1 produces the authoritative re-scanned table; append below.)_
