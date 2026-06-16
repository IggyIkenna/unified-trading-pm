---
title: "Predictions synthetic OTHER canonical-question-group bucket + deployment-ui 3-level drilldown"
parent_epic: predictions_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/predictions_master.md
  - ./prediction_manifest_canonicalisation_2026_06_01.md
  - ../epics/infrastructure_master.md
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
      Cluster validation for `OTHER` is per-day count > 0 (any markets fall through), NOT a target count. ✅ — unified-api-contracts@306923a
- [x] [SCRIPT] P0. Classifier emits an `INFO`-level event `OTHER_BUCKET_MEMBER_ADDED` whenever it routes a `conditionId`
      to `OTHER`. Operator periodically queries the event stream to find candidate groups for promotion. ✅ — unified-api-contracts@306923a
- [x] [SCRIPT] P0. Confirm the writer rebundles `OTHER`-routed rows into the
      `data_type=prediction_canonical_question_group` bundle for `OTHER` coverage (so `OTHER` appears in the manifest
      denominator like any curated group). NOTE: the writer-rebundling code path itself is owned by
      `prediction_manifest_canonicalisation_2026_06_01` — this todo only verifies `OTHER` is included in that bundling,
      not re-implementing the bundler. ✅ — unified-api-contracts@306923a

## P0 — data-status panel + deployment-ui drilldown

- [ ] [SCRIPT][UI] P0. Data-status panel renders `OTHER` as a normal canonical-question-group bucket (NOT "out of
      scope"). Hover tooltip: "Markets not yet mapped to a curated canonical question group — review event stream +
      promote recurring patterns to first-class groups." `[UI]` — playwright gate:
      `npx playwright test --project=chromium tests/smoke/` exits 0 + cite a regression spec in
      `tests/e2e|playbooks|widgets|smoke/` before ticking.
- [ ] [SCRIPT][UI] P0. Predictions asset_group panel — drill-down shape: `(venue, canonical_question_group, day)`.
      (Aligns with `infrastructure_master` Data-status multi-axis follow-up — cross-link only.) `[UI]` — playwright gate
      before ticking.
- [ ] [SCRIPT][UI] P0. **deployment-ui 3-level hierarchy + per-shard parquet download**. MARKETS list is flat today;
      flip to `asset_group → canonical_question_group → cadence (HOURLY/DAILY/etc.)` 3-level drilldown matching the
      sports + tradfi pattern. Per-shard parquet download wires through the existing
      `deployment-ui/src/components/HierarchicalShardDrilldown` machinery. `[UI]` — playwright gate before ticking.
- [ ] [VERIFY][UI] P0. After the writer + UI ship: re-walk the deployment-ui prediction panel; POLYMARKET drill-down
      renders as
      `(venue=POLYMARKET, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)` per
      CLAUDE.md per-asset-group shard-key matrix. No "out of scope" badge. `OTHER` bucket visible alongside curated
      groups. `[UI]` — playwright gate before ticking.
- [ ] [VERIFY] P0. Predictions timeline / panel VERIFY gate: Phase-1 timeline check + after-Phase-1 re-walk that
      POLYMARKET no longer renders "out of scope" in deployment-ui (the badge driven by UAC
      `VENUE_DATA_TYPE_CAPABILITIES` vs the live manifest data_type). This is the operator-facing acceptance gate for
      the panel surface.

## P1 — canonical-groups backfill remainder

- [ ] [SCRIPT] P1. **Phase 5 — canonical-groups backfill (30+ groups beyond the initial 9)**. Full list in the archived
      issue: CRUDE_OIL_UP_DOWN_DAILY, GOLD_UP_DOWN_DAILY, DOGE_UP_DOWN_DAILY, SOL_UP_DOWN_DAILY,
      ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E (CME-linked), and ~24 others. Per-group: define in UAC `PREDICTION_GROUPS`;
      backfill instruments-service catalog + MTDS CLOB tick history; cluster-validation expected counts populated.
      **GATES `cme_polymarket_arb_2026_05_08` Phase 2 cross-link.** NOTE: the 7 CME-linked groups + classifier rules +
      INTRADAY/5MIN/15MIN granularity + the IS/MTDS backfill VMs for those already SHIPPED per the epic body
      (UAC@9c491bdd / 55d068f7 / 228c317a / bd570664 / e6ae5013; IS@d76b877f; MTDS@498148da). This P1 is the REMAINING
      ~24 groups not yet defined/backfilled.

## P2 — prediction sentinel fan-out

- [ ] [SCRIPT] P2. **Prediction sentinel fan-out for `prediction_canonical_question_group` empty rows** — when a
      canonical question group has zero markets trading on a given day, no
      `data_type=prediction_canonical_question_group` `empty_confirmed` row is emitted today (the tier-2 sentinel only
      emits `data_type=trades, SOURCE_RETURNED_ZERO`). Fix: after the finalize loop in `orchestrator.py`, fan out
      `record_empty(SOURCE_RETURNED_ZERO)` for each CQG in the UAC canonical group registry not populated in
      `prediction_cluster_counts_by_venue` for that (venue, day). Ensures the manifest denominator includes
      zero-trading-day groups + the deployment-ui drilldown shows honest 0% for inactive CQGs rather than omitting them.

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
