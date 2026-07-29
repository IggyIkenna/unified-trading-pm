---
doc_type: plan
title: Prediction cqg-classifier coverage residual — forked from migration_verification_orphan_safety_2026_06_10
summary: >-
  2 small residual todos forked out of the archived migration-verification/orphan-safety harness plan (2026-07-24 plan
  line-cap remediation split): the operator-gated prediction cqg-classifier coverage decision (before the pred G4 apply)
  and the downstream cqg-grain catalogue wiring it gates.
status: complete # (was: active) 2026-07-29 — both todos done, archived
nature: process
asset_group:
  [prediction] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine
  # mistag: cqg-classifier coverage is prediction-market-specific, inherited the parent harness's cross-cutting
  # tag on fork instead of being corrected to its real single-AG scope
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [prediction, cqg, classifier, manifest, migration, plan-split, residual]
related:
  [
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: data_engineering
drift_direction: advance-code
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (its own Progress Log, entries
  dated 2026-06-11 / 2026-06-16) as part of the 2026-07-24 plan line-cap remediation
  (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's durable
  protocol (CF-15…CF-21) had already migrated to codex; these 2 todos were the last genuinely-open items in its
  prediction-cqg thread and are tracked here going forward.
---

# Prediction cqg-classifier coverage residual

> **Origin.** This plan is a **fork**, not a new investigation — both todos below are moved **verbatim** from
> `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; its full historical
> Progress Log is archived to `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md` as an
> Appendix). Read that appendix for the surrounding narrative/evidence if deeper context is needed — nothing below has
> been rewritten or summarized from the original.
>
> **Ordering note**: item 1 (the classifier coverage decision) is the operator-gated prerequisite item 2 references as
> "Blocked-on: 338" — resolve item 1 first.

## Todos

- [x] ✅ [DATA] P1. **STALE PREMISE, re-scoped 2026-07-26** (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #14): the 94.5%/`ClassifierConfidenceLow` measurement
      below is from 2026-06-11, BEFORE `unified-api-contracts@d4523602`/the OTHER-catch-all classifier change — read
      from current HEAD 2026-07-26, both `classify_polymarket_to_canonical_group` and
      `classify_kalshi_to_canonical_group` are non-Optional (never return `None`) and route every unmatched market to
      `OTHER`, not `attempted_failed[ClassifierConfidenceLow]`. The "extend registry vs ratify
      out-of-registry-stays-failed" decision this todo poses is now MOOT — there is no out-of-registry-stays-failed path
      left to ratify. **Re-scoped to**: (1) re-run the coverage measurement against current HEAD — **DONE 2026-07-27,
      see Progress Log**: `ClassifierConfidenceLow` is confirmed 0.0000% for BOTH venues (not just "expected"), but the
      `~94.5% OTHER` expectation in this todo's own text was WRONG — measured `OTHER` share is ~55.2% of captured rows /
      ~11.1% of captured shards (per-venue split differs materially: KALSHI 49.8% rows / POLYMARKET 56.6% rows), because
      the registry has been extended far beyond just the OTHER-catch-all since 2026-06-11 (alt-coins, weather, macro,
      ~17 sports leagues per decision 338 pass 2), so most of the formerly-`ClassifierConfidenceLow` mass now routes to
      REAL named groups, not just `OTHER`. **This todo's own re-scope premise is itself now annotated re-based, not left
      implying `~94.5% OTHER` is current.** (2) verify
      `market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py`'s `compute_object_atom`
      (its `None`-branch dead code + stale "the rebuild follows the [None→failed] contract" docstring/comment) matches
      the now-unreachable-`None` reality — **DONE 2026-07-29**: both `rebuild_prediction_manifest.py`'s
      `compute_object_atom` docstring/comments AND `kalshi_adapter.py`'s module docstring (lines 21-29) + its
      `_add_canonical_question_group`-equivalent call site (previously `group.value if group is not None else None`) are
      corrected to state the classifier is non-Optional (never `None`) and the `None`-handling branches are kept only as
      a defensive `ClassifierConfidenceLow` safety net for a regressed/test-double classifier, not describing a
      reachable live path. `quality-gates.sh` green. — market-tick-data-service@5bf8a3c7. Repos: unified-api-contracts,
      market-tick-data-service. Original provenance: /tmp/r7_proj/prediction2.log 2026-06-11 (now superseded — see
      2026-07-27 re-based numbers below).
- [x] ✅ [DATA] P2. **DONE 2026-07-29 — 249-b — prediction cqg grain (`prediction_canonical_question_group`) — re-scoped
      2026-07-26, decision 338 resolved (OTHER for all).** Wired the cqg into the loader via a `_canonical_group`
      write-back: `unified-api-contracts@283d7449` adds an additive `InstrumentRecord.canonical_question_group` field;
      `instruments-service@38e393de` has the Polymarket/Kalshi adapters write back the already-computed `group.value`
      onto it (previously dropped after deriving `underlying`), and `build_prediction_catalogue_dataframe` now reads it
      PER-ROW (a single `instruments.parquet` blob spans many cqg groups — the path-level `cqg` value stays
      legacy-fallback-only) so the cqg-grain rows emit — verified via a new rollup test proving two markets sharing one
      group fold into one bundle row. `quality-gates.sh` green in both repos. Prod `catalog.parquet` promotion
      explicitly NOT run, per `prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todo 2's scope boundary — carried
      by `prediction_phase_ab_residuals_2026_07_24.md`'s gated regen.

## Success criteria

1. Coverage re-measured against current HEAD (OTHER-catch-all contract confirmed live for both venues, ~0% residual
   `ClassifierConfidenceLow`), `rebuild_prediction_manifest.py`'s dead `None`-handling cleaned up to match.
2. `prediction_canonical_question_group` cqg-grain rows emit from the catalogue rollup once item 1 resolves; verified by
   re-running `build_instrument_catalogue --asset-group prediction` and reading the promoted `catalog.parquet` back.

## Progress Log

- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  work done yet on either todo beyond what the parent's archived Progress Log already recorded.
- 2026-07-29 — todo 2 (249-b, cqg grain) shipped and flipped, per
  `prediction_satellite_ao_dispatch_batch5_2026_07_26_finalize.md` todo 1's reconciliation instruction —
  `unified-api-contracts@283d7449` + `instruments-service@38e393de`. Todo 1's leg (2) code-cleanup
  (`rebuild_prediction_manifest.py`/`kalshi_adapter.py` dead `None`-branch comments) remains open, tracked separately
  under the MTDS CODE_QUICK backlog pass (`issues/code_quick_cross_repo_fix_backlog_2026_07_28.md`).
- 2026-07-27T15:25:50Z — **todo 1 leg (1) re-measurement complete** (dispatched via
  `prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todo 1, read-only, no `--apply`/no mutation). **Method**:
  single consolidated-object read of the live prediction availability manifest via UTL
  `read_availability_index("market-data-tick-pred-prd-central-element-323112", columns=[...])` (NOT a corpus walk —
  single-walk discipline respected; `_index/latest.json` confirmed the consolidator had just run,
  `last_run_at=2026-07-27T15:19:27Z`, `verdict=produced`, so the read was fresh, not stale-fallback). Filtered to
  `data_type == "prediction_canonical_question_group"` (68,667 shard rows total). Verified against
  `unified-api-contracts` HEAD `classifiers.py` (`classify_polymarket_to_canonical_group` /
  `classify_kalshi_to_canonical_group` — both `-> CanonicalQuestionGroup`, non-Optional, confirmed by reading the full
  function bodies, not just the docstring). **(a) `attempted_failed[ClassifierConfidenceLow]` share, per venue**: KALSHI
  0/22,054 bundled shards (0.0000%); POLYMARKET 0/46,613 bundled shards (0.0000%); combined 0/68,667 (0.0000%). The
  bundled data_type carries only 4 `attempted_failed` rows total (2 KALSHI + 2 POLYMARKET, both dated 2026-06-27/28),
  and every one of them has `error_reason="missing_available_at_envelope"`, NOT `ClassifierConfidenceLow` — the
  `ClassifierConfidenceLow` failure mode is empirically extinct for BOTH venues at current HEAD, not just theoretically
  unreachable. **(b) `OTHER`-group share** (exact `instrument_id == "OTHER"` on `capture_status == "captured"` rows —
  NOT a substring match, which would have wrongly also caught `GEO_OTHER_BY_DATE`; and NOT the `underlying` column,
  which is unpopulated/`None` on 17,592 of 17,592 sampled captured cqg rows for this MTDS raw-tick manifest —
  `instrument_id` is confirmed the correct column per `rebuild_prediction_manifest.py`'s own documented contract
  "`instrument_id=cqg`" and directly verified by reading real values off this manifest, e.g. `ADA_PRICE_RANGE_DAILY`,
  `BNB_UP_DOWN_DAILY`): KALSHI 1,617/10,301 captured shards (15.70%) / 74,473,736 of 149,410,266 captured rows (49.85%);
  POLYMARKET 329/7,291 captured shards (4.51%) / 326,510,683 of 576,523,999 captured rows (56.63%); combined
  1,946/17,592 captured shards (11.06%) / 400,984,419 of 725,934,265 captured rows (55.24%). **This is materially below
  the `~94.5% OTHER` this todo's own re-scoped text predicted** — the registry extensions since 2026-06-11 (alt-coins,
  weather, macro releases, ~17 sports leagues, all decision-338-pass-2 granular sub-type routing) absorbed most of the
  formerly-unclassified mass into REAL named groups, not just into `OTHER`. **(c) max captured day for the bundled
  data_type**: NOT still 2026-04-14 — KALSHI captured cqg bundles now extend to **2026-07-26** (min 2021-06-30),
  POLYMARKET to **2026-07-22** (min 2025-03-14); the bundled data_type's overall max `date` across all capture_status
  values is 2026-07-27. capture_status distribution on the 68,667 bundled shards: `empty_confirmed`=48,044,
  `captured`=17,592, `expected_unattempted`=3,027, `attempted_failed`=4 (sums to 68,667). **Explicitly out of scope for
  this measurement** (per `prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todo 1): the extend-vs-ratify
  registry-coverage decision — these numbers only supply the inputs that decision needs, they don't make the call.
