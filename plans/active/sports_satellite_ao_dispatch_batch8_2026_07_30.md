---
doc_type: plan
title: Sports satellite AO batch 8 — dedicated triage/design pass on the 2 `doc_too_large_or_risky_for_batch` docs
summary: >-
  Eighth AO-dispatch batch for sports, produced by batch4's own last todo: a dedicated triage/design pass (not a blind
  extraction) on the 2 docs flagged `doc_too_large_or_risky_for_batch` since the original 2026-07-25 triage —
  `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` and
  `issues/sports_features_layer_findings_sweep_2026_07_18.md` (PART 1 of 3 — parts 2/3 were already fully reconciled by
  batch6). The canonical-universe doc yields ZERO new AO-eligible candidates (confirmed fresh, not just re-cited from
  the 2026-07-25 triage) — every remaining item is either already BLOCKED-OPERATOR-tracked, a genuine scope-overlap
  conflict with the consolidated closeout's own separate dual-layout todos, or an explicit design/curation judgment
  call, and the closeout itself frames the whole remaining-todo set as gated on an unmade fold-in-vs-keep-satellite
  decision. The features-sweep Part 1 doc yields 5 candidates: 3 clear real orphans (a bucketing-bug root-cause, a
  cross-asset-group junk-symbol-guard false-positive fix, an Odds-API historical-backfill adapter), 1 bounded
  verify-only check on a claim that may already be superseded, and 1 canonical-naming audit extension. 3 other Part-1
  items were found ALREADY RESOLVED/DUPLICATED elsewhere (live in-play connector already shipped+running, a
  distinct-dimension-values UI listing already tracked generically in prediction's Phase C, and the manifest-staleness
  DIAG already fully root-caused in its own issue doc) and are reconciled in the source doc directly rather than
  re-drafted.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-data-processing-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    deployment-service,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-8, satellite-docs, dedicated-triage]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27.md,
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27_finalize.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  sports_satellite_ao_dispatch_batch4_2026_07_25.md's own last todo ("Give the 2 doc_too_large_or_risky_for_batch docs a
  dedicated triage/design pass"), executed per the ag-closeout-audit skill's Phase 1/Phase 3 methodology (per-doc full
  read, conflict-check against the consolidated closeout + every existing batch plan before drafting).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports satellite AO batch 8 — dedicated triage/design pass

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 5 todos below are same-priority and touch distinct files/repos (verified individually per todo)
> so they are safe to dispatch concurrently once activated.

## Doc 1: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — 0 new AO-eligible candidates

Read in full (2026-07-30). Genuinely remaining open items and why NONE convert to a batch todo:

- **Bare/legacy dual-layout cleanup** (its own `[DATA] P0`, "canonicalise the bare→per-league (in-retention) OR DELETE
  (pre-retention)") — **genuine conflict, not resolvable from evidence alone**:
  `sports_consolidated_closeout_2026_07_19.md` independently tracks TWO narrower dual-layout items of its own
  (`[CODE] P2` "eliminate/document the legacy bare `entity=fixtures/` write path still ACTIVE today"; `[CLEANUP] P2`
  "snapshot-then-cull the dead `sports_reference_v2/by_date/`") — whether this doc's broader per-entity cleanup is the
  SAME ground, a superset, or independent is not determinable from either doc's text. Parked, not drafted (see
  Deferred).
- **UAC canonical registry build/refine** (`[CODE] P1`) — a multi-facet design+build item (league/cup registry schema +
  5+ per-source eligibility maps + team/player/fixture canonical mappings + honest-coverage wiring). Even with the
  operator's verbatim directives as a spec, this is too large for one bounded todo and the closeout's own
  cross-reference (below) gates the whole doc on an unmade reconciliation decision first. Not drafted.
- **Define the curated ~300-league reference set** (`[DATA] P1`) — an explicit curation/editorial judgment call (which
  leagues make the cut), not a checkable worker outcome. Not drafted.
- **Curated-universe backfill** / **drop residual out-of-curated rows** (`[DATA] P2` ×2) — sequentially gated on the
  item above; not yet actionable. Not drafted.
- **E8 legacy-delete `--drop-stale` `--apply` firing** — already correctly tracked as `BLOCKED-OPERATOR` in this same
  doc (code shipped via batch5, the irreversible delete itself pending sign-off, partial delete-safety re-check done
  2026-07-29). No new todo needed.
- **Meta-blocker, applies to the whole set**: the consolidated closeout's own Track (lines ~776-784) explicitly frames
  this satellite doc's entire remaining-todo set as gated on an unmade operator decision — "an operator either formally
  folds its remaining todos into this closeout... or confirms satellite-plan status is the intended long-term shape."
  Extracting individual items into a fresh batch now would pre-empt that reconciliation call.

This matches (and, with the dual-layout conflict + meta-blocker, refines) the original 2026-07-25 triage's "0
AO-eligible found anyway — all 8 remaining items are human-only design/operator-sign-off work" conclusion. Confirmed
still true.

## Doc 2: `issues/sports_features_layer_findings_sweep_2026_07_18.md` (PART 1 of 3, §A-F) — 5 candidates + 3 reconciled duplicates

Read in full (2026-07-30). Parts 2 and 3 (the 2026-07-26 line-cap split siblings) were already fully reconciled by
`sports_satellite_ao_dispatch_batch6_2026_07_26.md` todos 1-2 — out of scope here, this doc's OWN §A-F open items only.

**Reconciled directly in the source doc (this plan's own commit), not re-drafted as todos:**

- § D "Enable the live in-play connector (`odds_api_ws.py`)" — **STALE, superseded.** Live-verified: the connector is
  coded, deployed, and RUNNING (`mtds-live-sports-odds-api-trades` VM, 60s poll) per
  `sports_live_availability_and_source_latency_2026_07_24.md`'s LIVE_ODDS row and
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md`'s 2026-07-29 update. Checked off in source, citing
  both docs.
- § F "Restore the data-status distinct-dimension-values listing" — **clear duplicate.** The identical feature (generic,
  per-asset-group, "mirrors the identical tradfi Phase-C todo") is already an open, properly-scoped todo in
  `prediction_phase_c_data_status_ui_2026_07_24.md` Phase C — sports is covered automatically once that ships
  generically. Checked off in source, citing the covering todo.
- § F6 "why is the instruments-sports consolidated index persistently older than its 120s budget" — **clear duplicate.**
  Already fully root-caused (no per-AG staleness-budget override; ~11min consolidator cadence vs the 120s generic
  default) in `plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`. Checked off in source,
  citing that issue doc.

## Todos

- [ ] [DIAG] P1. **Root-cause the 2025-12-18 / 2025-12-31 in-window bucketing failure (§B1 residual)** — ~360 in-window
      (0-24h-to-kickoff) odds observations on EACH of 2025-12-18 and 2025-12-31 fail to bucket into any `TIER1_HORIZONS`
      slot, while the structurally-similar quiet date 2025-12-24 legitimately has zero. Likely candidates per the source
      doc: a fixture-mapping join dropping them, or a secondary guard beyond `bm<=0`. Do **NOT** "fix" this by
      relabelling the manifest — root-cause first. Once understood: if 2025-12-24 is confirmed to have no genuine
      data-corruption cause of its own, relabel ONLY 2025-12-24 as `empty_confirmed` (2025-12-18 and 2025-12-31 stay
      `attempted_failed` — that is the honest signal of the real bug). Note: `2025-12-18` is already the pinned
      `SPORTS_SMOKE_DATES.known_buggy_odds` reference constant (`features-service@84cb4613`) — that pin documents the
      date as known-bad for smoke tests, it does NOT root-cause or fix the underlying bug; this todo is the
      still-missing root-cause step. **Done when**: the root cause is identified and documented (not just re-labelled),
      2025-12-24 is correctly relabelled if the investigation supports it, and 2025-12-18/2025-12-31 stay
      `attempted_failed` with the root cause noted inline. (repo: market-data-processing-service or features-service,
      whichever owns the bucketer/loss-guard code path — confirm from `odds_loss_guard.py`/`loss_guard.py`). Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18.md` §B1 (lines 286, 289).

- [ ] [CODE] P1. **Narrow the cross-asset-group junk-symbol guard so it stops rejecting legitimate non-ASCII sports team
      names (§D).** `instruments-service/instruments_service/engine/orchestrator/venue_core.py:394-408`
      `_is_junk_instrument` rejects ANY non-ASCII field (`field.isascii()` check), applied to every asset group —
      measured live: it drops ~9.8% of a sample sports date's fixtures for legitimate Latin-accented team names
      (Sanluqueño, União, Potosí, etc.), biased toward Iberian/Latin American leagues, invisibly (rejected instruments
      never enter the coverage denominator). Narrow the rule to target CJK/emoji/symbol ranges specifically (or scope
      the blanket ASCII rule to crypto asset groups only) so it keeps catching the CJK/meme test symbols it was built
      for (confirmed still live 2026-06-24 finding: 龙虾/币安人生/我踏马来了 on BINANCE/BITGET/ASTER — cross-referenced
      in `instruments_foundation_phase0_cross_cutting_2026_07_24.md`'s G1.4, whose "not implemented" framing is itself
      stale — the guard demonstrably already exists, live-verified in code 2026-07-30) while no longer false-positiving
      on sports. Add a regression test pinning `Sanluqueño` / `União` / `Potosí` as KEPT and `龙虾` / `币安人生` as
      REJECTED. Then quantify the corpus-wide loss (the 9.8% figure is one sampled date, 2021-11-26) and re-capture the
      affected date/league range once the guard is narrowed. **Done when**: the regression test passes, the guard no
      longer rejects the 3 pinned Latin-accented names, still rejects the 2 pinned CJK names, and the corpus-wide loss
      has been quantified + the affected range re-captured. (repo: instruments-service). Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18.md` §D (lines 455, 458).

- [ ] [CODE] P1. **Implement The Odds API historical-snapshot adapter leg + backfill the thin early-kickoff horizons
      (§E1-E2).** Confirmed still absent in code as of 2026-07-30 (grep across market-tick-data-service /
      instruments-service / unified-api-contracts finds only a docs reference in
      `market-tick-data-service/docs/SPORTS_ODDS.md`, no implementation) — measured root cause: per-horizon fixture
      counts are non-monotonic (T-24h sees only 25/68 fixtures on a sample date) because a fixture entering capture
      window mid-cycle was never sampled at the earlier horizons; The Odds API's live poll cannot retroactively fill
      those windows, only its `/v4/historical/sports/{sport}/odds?date=<ISO>` endpoint can. Credentials already exist
      for both live and batch (operator 2026-07-18) — this is a code+config gap, not a credential ask. Implement the
      adapter leg (measure cost-per-snapshot before any full-corpus run), then backfill the T-24h (and T-1h/T-0) windows
      for fixtures currently missing a sample there, and re-derive `odds_features` after. **Done when**: the adapter leg
      is implemented + unit-tested, a cost-per-snapshot measurement is recorded, the identified missing- window fixtures
      are backfilled, and `odds_features` has been re-derived for the affected dates. (repo: market-tick-data-service).
      Source: `issues/sports_features_layer_findings_sweep_2026_07_18.md` §E (lines 507, 509).

- [ ] [DIAG] P2. **Verify whether the Tier-3 `odds_t24h`/`t6h`/`t1h` MTDS snapshot cadence already closes §E3's
      sparse-forward-polling gap — close or re-scope, do not re-implement blind.** §E3 (2026-07-18) diagnosed the root
      cause of thin early-horizon buckets as a single daily 12:00 UTC fetch sampling only a narrow slice of each
      declared horizon window. `sports_live_availability_and_source_latency_2026_07_24.md` (last updated 2026-07-29) now
      describes a Tier-3 snapshot system firing multiple horizon-targeted snapshots per day (`odds_t24h`/`t6h`/`t1h`) —
      plausibly the forward-fix §E3 asked for, but this was not confirmed against §E3's specific ask (every declared
      horizon window sampled with enough density, not just at 3 named horizons) during this triage pass. Read the Tier-3
      scheduler config + a sample day's actual per-horizon sample density; if it meets §E3's bar, flip §E3 in the source
      doc citing this evidence; if a real gap remains (e.g. a horizon window still under-sampled), describe it precisely
      as a fresh, separately-scoped follow-up rather than fixing it in this same todo. **Done when**: §E3 is either
      closed-with-citation or replaced by a precisely-scoped new finding. (repo: market-tick-data-service,
      deployment-service — read-only config/log inspection, no code change unless the gap is trivial). Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18.md` §E3 (line 511).

- [ ] [AUDIT] P2. **Extend the canonical-naming audit (§F1-F6 methodology) to league / fixture / betting-market
      identifier columns (§F residual).** The existing F1-F6 audit (case-duplication, dimension-pollution, timeframe-
      in-data_type, suspect venue values) covered `data_type`/`instrument_type`/`venue`; the operator explicitly asked
      ("in sports case leagues and fixtures and betting market canonicals are relevant too") for the same methodology
      applied to league / fixture / betting-market identifier values. Read via `read_availability_index()` (manifest-
      driven, no fresh corpus walk) across the sports manifest surfaces, apply the same case-duplication /
      dimension-pollution checks to league_id / fixture-identifier / bookmaker-market-identifier columns, and report any
      violations found. Fold confirmed violations into `sports_consolidated_closeout_2026_07_19.md`'s Track C
      (canonicalization) as new dated findings rather than fixing them inline here. **Done when**: the audit has run
      against all 3 identifier classes, findings (or a confirmed-clean result) are recorded, and any real violation is
      cross-linked into Track C. (repo: unified-trading-pm doc + read-only manifest reads against instruments-service /
      market-tick-data-service). Source: `issues/sports_features_layer_findings_sweep_2026_07_18.md` §F (line 601).

## Deferred — still genuinely conflict-gated / non-batchable

- **Canonical-universe doc's bare/legacy dual-layout cleanup** — genuine conflict with the consolidated closeout's own
  narrower dual-layout todos (active bare `entity=fixtures/` writer; dead `sports_reference_v2/by_date/`). Not
  resolvable from evidence alone whether these are the same ground, a superset, or independent. Recommend the operator
  rule on scope before either is dispatched — see Doc 1 section above.
- **Canonical-universe doc's UAC canonical registry build/refine + curated ~300-league definition (+ its 2 gated
  sequels)** — genuine design/curation judgment calls, plus the whole doc is meta-gated on the closeout's unmade
  fold-in-vs-keep-satellite decision. Not batchable until that decision lands.
- **§E5 "Consider adding T-6h or T-2h as a MODEL horizon"** — an explicit design/product suggestion ("Consider"), not a
  deterministic worker outcome. Needs an ML/product judgment call, not re-triage.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence — same pattern as batch2-7. This plan's own reconciliation-then-archive step is machine-gated via the companion
`sports_satellite_ao_dispatch_batch8_2026_07_30_finalize.md`
(`depends_on: [sports_satellite_ao_dispatch_batch8_2026_07_30]`

- `gate_on_depends: true`).

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc. The
`/ag-closeout-audit` skill's "batchN methodology" section (`cursor-configs/skills/ag-closeout-audit/SKILL.md`) is the
SSOT for the dedicated-triage-pass procedure this plan followed.
