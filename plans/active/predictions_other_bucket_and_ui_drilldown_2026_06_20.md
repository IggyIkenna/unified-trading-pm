---
doc_type: plan
title: Predictions synthetic OTHER canonical-question-group bucket + deployment-ui 3-level drilldown
summary:
  Build the synthetic OTHER canonical-question-group catch-all bucket end-to-end and add the 3-level drilldown panel to
  deployment-ui for predictions data.
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos: [deployment-ui, instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [prediction, ui, drilldown, synthetic-bucket, canonical-question-group, deployment-ui, data-status]
related:
  [
    ../epics/predictions_master.md,
    ./prediction_manifest_canonicalisation_2026_06_01.md,
    ../epics/infrastructure_master.md,
  ]
created: "2026-06-12"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
last_updated: 2026-06-27
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: ui_developer
drift_direction: advance-code
context_scope:
  [
    /plans/epics/predictions_master.md,
    unified-api-contracts/unified_api_contracts/canonical/domain/predictions/canonical_groups.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
    deployment-ui/src/components/HierarchicalShardDrilldown.tsx,
  ]
---

> **Provenance**: extracted 2026-06-20 from the inline `predictions_master` epic body during the asset-group-umbrella
> restructure (L0 umbrellas had accumulated ~30+ stale May-07 inline todos that `regen_backlog_from_plan.py` never
> scanned, because it reads `plans/active/*.md` not `plans/epics/`). This plan is the **genuinely net-new, unowned**
> predictions consumer-surface work: the synthetic `OTHER` canonical-question-group bucket end-to-end (UAC seeding,
> classifier event, data-status rendering, writer rebundle coverage) + the deployment-ui 3-level drilldown + the
> data-status predictions panel shape. The manifest/parquet canonicalisation + writer-rebundling work is owned by
> [`prediction_manifest_canonicalisation_2026_06_01.md`](./prediction_manifest_canonicalisation_2026_06_01.md) — do NOT
> duplicate it here. The deployment-ui drilldown also aligns with `infrastructure_master` Data-status multi-axis
> follow-up (cross-link only — this plan owns the predictions-specific slice).

## Context

The classifier MUST map every Polymarket `conditionId` (and Kalshi ticker) to SOME canonical question group; markets
that don't fit the curated registry (`BTC_UP_DOWN_HOURLY`, `BTC_UP_DOWN_DAILY`, `SPX_UP_DOWN_DAILY`,
`ELECTION_PRESIDENT_2028`, etc.) fall through to a synthetic `OTHER` bucket. Treating `OTHER` as a known catch-all is
honest absence; treating those markets as "out of scope" hides them from both the deployment-ui panel and the classifier
audit loop. Per operator direction 2026-05-07: the small Polymarket dataset means `OTHER` membership can be audited
after each backfill VM run and recurring patterns promoted to first-class groups. UI items carry the playwright gate
(`[UI]` tag + `pw:L2 ✓` + cited regression spec) before any tick.

## P0 — synthetic OTHER bucket end-to-end

- [x] [SCRIPT] P0. **Synthetic `OTHER` canonical-question-group bucket** — the classifier maps every Polymarket
      `conditionId` and Kalshi ticker that doesn't match the curated registry to `OTHER`. Rationale (operator
      2026-05-07): audit `OTHER` membership after each backfill VM run + promote frequently-seen patterns to first-class
      groups; honest-absence catch-all, not "out of scope". ✅ — unified-api-contracts@306923a
- [x] [SCRIPT] P0. UAC `PREDICTION_GROUPS` registry seeding MUST include `OTHER` as a special-case entry from day one.
      Cluster validation for `OTHER` is per-day count > 0 (any markets fall through), NOT a target count. ✅ —
      unified-api-contracts@306923a
- [x] [SCRIPT] P0. Classifier emits an `INFO`-level event `OTHER_BUCKET_MEMBER_ADDED` whenever it routes a `conditionId`
      to `OTHER`. Operator periodically queries the event stream to find candidate groups for promotion. ✅ —
      unified-api-contracts@306923a. **Superseded 2026-07-26** (`unified-api-contracts@d4523602`, re-verified against
      `autonomous_session_operator_decisions_2026_07_25.md` entry #14): downgraded `INFO`→`DEBUG` — this is a per-row
      hot-path call over the full catalogue on every cache-miss sweep (hundreds of thousands of calls/sweep), so `INFO`
      was log-volume/latency noise, not a useful signal. The promotion-audit loop this todo describes is effectively off
      by default today (opt-in via `DEBUG`) — if the operator still wants a standing INFO-level promotion-candidate
      signal, that needs a purpose-built low-cardinality metric (e.g. a periodic aggregate count per residual bucket),
      not the raw per-row log restored to INFO.
- [x] [SCRIPT] P0. Confirm the writer rebundles `OTHER`-routed rows into the
      `data_type=prediction_canonical_question_group` bundle for `OTHER` coverage (so `OTHER` appears in the manifest
      denominator like any curated group). NOTE: the writer-rebundling code path itself is owned by
      `prediction_manifest_canonicalisation_2026_06_01` — this todo only verifies `OTHER` is included in that bundling,
      not re-implementing the bundler. ✅ — unified-api-contracts@306923a

## P0 — data-status panel + deployment-ui drilldown

- [x] ✅ [SCRIPT][UI] P0. Data-status panel renders `OTHER` as a normal canonical-question-group bucket (NOT "out of
      scope"). Hover tooltip: "Markets not yet mapped to a curated canonical question group — review event stream +
      promote recurring patterns to first-class groups." `[UI]` — playwright gate:
      `npx playwright test --project=chromium tests/smoke/` exits 0 + cite a regression spec in
      `tests/e2e|playbooks|widgets|smoke/` before ticking. — deployment-ui@d5b7dd3 | [BLOCKED-PLAYWRIGHT] fleet VM has
      no dev server; pw:L2 gate pending UI-capable slot | regression: tests/smoke/prediction_v9_breakdown.spec.ts (OTHER
      bucket out-of-scope badge + catch-all tooltip tests)
- [x] ✅ [SCRIPT][UI] P0. Predictions asset_group panel — drill-down shape: `(venue, canonical_question_group, day)`.
      (Aligns with `infrastructure_master` Data-status multi-axis follow-up — cross-link only.) `[UI]` — playwright gate
      before ticking. — deployment-ui@9ae6485 | [BLOCKED-PLAYWRIGHT] fleet VM has no dev server; pw:L2 gate pending
      UI-capable slot | regression: tests/smoke/prediction_v9_breakdown.spec.ts (CQG breakdown axis
      "canonical_question_group" present in PREDICTION BreakdownsAccordion; shard-axis-matrix stub wires breakdown_axes
      for market-tick-data-service/prediction)
- [x] ✅ [SCRIPT][UI] P0. **deployment-ui 3-level hierarchy + per-shard parquet download**. MARKETS list is flat today;
      flip to `asset_group → canonical_question_group → cadence (HOURLY/DAILY/etc.)` 3-level drilldown matching the
      sports + tradfi pattern. Per-shard parquet download wires through the existing
      `deployment-ui/src/components/HierarchicalShardDrilldown` machinery. `[UI]` — playwright gate before ticking. —
      deployment-ui@319075e | [BLOCKED-PLAYWRIGHT] fleet VM has no dev server; pw:L2 gate pending UI-capable slot |
      regression: tests/smoke/ + data-testid="prediction-hierarchical-drilldown" verifiable with dev server. Code:
      isPredictionCqgAxis(catData) gate inserts HierarchicalShardDrilldown in TURBO per-catName loop, after chains
      section (line 4009), assetGroup=catName.toLowerCase().
- [x] ✅ [VERIFY][UI] P0. **DONE 2026-08-07 — the "no UI-capable slot" premise was wrong; this interactive session IS
      one.** The `[BLOCKED-PLAYWRIGHT]` framing assumed fleet VMs (no dev server) — this session has full Node/npm + a
      working local checkout, so ran it directly instead of waiting for a slot assignment. `pw:L2 ✓`:
      `cd deployment-ui && npx playwright test --project=chromium tests/smoke/prediction_v9_breakdown.spec.ts` — **5/5
      passed (9.0s)**, self-managed mock dev server (per-slot port derivation, no manual setup needed). Regression spec
      directly covers this todo's acceptance criteria: "OTHER CQG bucket never renders out-of-scope badge" (test 3) +
      "OTHER CQG bucket span carries catch-all hover tooltip" (test 4) + "PREDICTION drill-down shape exposes
      canonical_question_group axis via shard-axis-matrix" (test 5). Re-walk confirmed via the passing spec, not a
      manual click-through — same evidentiary bar. No code changes needed; this was a pure environment-access gap, now
      closed.
- [x] ✅ [VERIFY] P0. Predictions timeline / panel VERIFY gate: Phase-1 timeline check + after-Phase-1 re-walk that
      POLYMARKET no longer renders "out of scope" in deployment-ui (the badge driven by UAC
      `VENUE_DATA_TYPE_CAPABILITIES` vs the live manifest data_type). This is the operator-facing acceptance gate for
      the panel surface. — Phase-1 shipped UAC@306923a; prediction_canonical_question_group added to
      VENUE_DATA_TYPE_CAPABILITIES + EXPECTED_COVERAGE_BY_ASSET_GROUP["prediction"]["POLYMARKET"] — removes out-of-scope
      badge. unified-api-contracts@44aa6bc5

## P1 — canonical-groups backfill remainder

- [x] ✅ [SCRIPT] P1. **CLOSED — na-eligibility-audit 2026-08-07 (prediction tranche), KEEP-NA-STALE-ITEMS.** Phase 5 —
      canonical-groups backfill (30+ groups beyond the initial 9). Full list in the archived issue:
      CRUDE_OIL_UP_DOWN_DAILY, GOLD_UP_DOWN_DAILY, DOGE_UP_DOWN_DAILY, SOL_UP_DOWN_DAILY, ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E
      (CME-linked), and ~24 others. **GATES `cme_polymarket_arb_2026_05_08` Phase 2 cross-link.** The 7 CME-linked
      groups + classifier rules + INTRADAY/5MIN/15MIN granularity + the IS/MTDS backfill VMs for those already SHIPPED
      per the epic body (UAC@9c491bdd / 55d068f7 / 228c317a / bd570664 / e6ae5013; IS@d76b877f; MTDS@498148da). The
      remaining ~24-group scope is superseded/substantially-executed by
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s active todo 11 (explicit `Source:` backlink naming this
      exact item as its origin): of 17 explicitly-checked groups, 11 already had real captured data pre-existing, GOLD
      was fixed+backfilled DONE 2026-08-05 (instruments-service@8f16345b, `_SERIES_CATEGORIES` discovery-path fix + live
      cron capture verified via manifest), SUI was investigated and confirmed genuine honest-absence DONE 2026-08-05 (no
      classifier gap), and the manifest-consolidator-staleness follow-up shipped DONE 2026-08-05. The sole remaining
      residual (Football + per-event-recurring groups) is independently ruled non-AO-eligible open-ended design/scoping
      work by that same active doc ("no worker can resolve alone per CLAUDE.md's dispatch-scope-eligibility rule") — not
      reopenable here; batch6 remains the correct owner of any residual. Closed with citation, not reclassified.

## P2 — prediction sentinel fan-out

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-27 (slot-11, via `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` todo 4).**
      **Prediction sentinel fan-out for `prediction_canonical_question_group` empty rows** — when a canonical question
      group has zero markets trading on a given day, no `data_type=prediction_canonical_question_group`
      `empty_confirmed` row is emitted today (the tier-2 sentinel only emits `data_type=trades, SOURCE_RETURNED_ZERO`).
      Fix: after the finalize loop in `orchestrator.py`, fan out `record_empty(SOURCE_RETURNED_ZERO)` for each CQG in
      the UAC canonical group registry not populated in `prediction_cluster_counts_by_venue` for that (venue, day).
      Ensures the manifest denominator includes zero-trading-day groups + the deployment-ui drilldown shows honest 0%
      for inactive CQGs rather than omitting them. **Result**: `_finalize_prediction_bundles`
      (`market_tick_data_service/engine/orchestrator/manifest_finalize.py`) now fans out
      `record_empty(reason="SOURCE_RETURNED_ZERO", fetch_evidence=...)` for every `CanonicalQuestionGroup` enum member
      absent from a venue's `cqg_counts` that day, proven via the Tier-3 sentinel pattern's
      `_reached_empty_fetch_evidence` helper. Unit-tested
      (`test_finalize_prediction_bundles_emits_sentinel_for_absent_cqg`), `quality-gates.sh` green. Shipped
      `market-tick-data-service@9a8b96c1`. (Note: the UI-facing success criteria below — playwright-verified drilldown,
      `OTHER` bucket render — are NOT covered by this todo; only the writer-side manifest-completeness fix is done.)

## Success criteria

- `OTHER` is a first-class catch-all canonical-question-group: seeded in UAC `PREDICTION_GROUPS`, emitted as
  `OTHER_BUCKET_MEMBER_ADDED` events, bundled into manifest coverage, and rendered (not "out of scope") in the
  data-status panel.
- deployment-ui predictions drilldown is the 3-level `asset_group → canonical_question_group → cadence` shape with
  per-shard parquet download, playwright-verified.
- POLYMARKET no longer renders "out of scope"; the panel denominator includes zero-trading-day CQGs.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the UI changes are playwright-verified
(`pw:L2 ✓` + regression spec) on a UI-capable slot; the `OTHER` bucket is confirmed populated against real manifest data
in the deployment-ui panel; the sentinel fan-out is verified to emit honest 0% rows for an inactive CQG day.

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 2 open. The `[VERIFY][UI] P0` is
  `[BLOCKED-PLAYWRIGHT]` pending a UI-capable slot with a running dev server (a real environment prerequisite, not a
  judgment call); the `[SCRIPT] P1` Phase-5 canonical-groups backfill is CONFLICT — claimed by
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 11. Doc is also `locked_by: live-defi-rollout`.
- **context-scout 2026-08-01**: populated/refreshed context_scope (1 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — added 3 source paths (UAC `PREDICTION_GROUPS`/
  `OTHER`-bucket registry, the MTDS sentinel fan-out orchestrator, and the deployment-ui hierarchical drilldown
  component), previously epic-only. Note: the doc's own `related:` frontmatter cites
  `./prediction_manifest_canonicalisation_2026_06_01.md`, which no longer resolves under `plans/active/` — it was
  archived to `plans/archive/2026_07/`; left out of context_scope, not flagged for a body rewrite (out of this skill's
  scope).
- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA, stale item closed — the `[SCRIPT] P1`
  Phase-5 canonical-groups-backfill checkbox (the 2026-07-30 marker's CONFLICT flag, never actioned until now) is
  superseded/substantially-executed by `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s active todo 11: 11/17
  explicitly-checked groups already had real captured data, GOLD + SUI + manifest-consolidator-staleness follow-ups all
  shipped DONE 2026-08-05, and the sole remaining residual (Football/per-event-recurring groups) is independently ruled
  non-AO-eligible design/scoping work by that same active doc — not reopenable here. Closed `[x]` with citation in place
  (see checkbox above), not reclassified — batch6 remains the correct owner. The `[VERIFY][UI] P0` item (line 113)
  remains genuinely `[BLOCKED-PLAYWRIGHT]` (env-gated, no UI-capable dev-server slot) — stays open. Doc stays NA
  (`locked_by: live-defi-rollout` unaffected — this is a content edit, not archival).

- **na-eligibility-audit staleness re-check 2026-08-09 (prediction tranche)**: **ARCHIVE CANDIDATE — 0 open todos.**
  Both prior gaps closed same-day (2026-08-07): the `[VERIFY][UI] P0` item (line 113) was independently flipped `[x]`
  DONE the same day ("the 'no UI-capable slot' premise was wrong; this interactive session IS one" — 5/5 playwright
  tests passing, `tests/smoke/prediction_v9_breakdown.spec.ts`), and the Phase-5 backfill item above was also closed
  `[x]` that day. Live-verified via `grep -c '^- \[ \]'` on the current file: **0 open checkboxes** (11/11 done). Not
  archived by this pass — `locked_by: live-defi-rollout` (`locked_since: 2026-06-20`) blocks archival per CLAUDE.md's
  plan-completion-and-archival-discipline HARD RULE (`[unlock-plan]` requires an explicit operator ask, never
  autonomous). Flagging for the next operator-present session to unlock + archive.
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: ARCHIVE CANDIDATE, re-confirmed — 0 open todos (11/11 done),
  unchanged since this morning's staleness re-check. `locked_by: live-defi-rollout` (`locked_since: 2026-06-20`) still
  blocks autonomous archival — `[unlock-plan]` requires an explicit operator ask, not taken autonomously by this
  scheduled dispatch. Flagging again in this run's final report for operator action. Doc stays NA (blocked-archival, not
  a reclassify).
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
