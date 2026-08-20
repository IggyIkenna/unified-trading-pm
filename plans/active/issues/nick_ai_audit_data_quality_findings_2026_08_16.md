---
doc_type: issue
title: Data-quality findings from the Nick AI platform-disclosure pre-audit — write-path bugs and schema gaps
summary: >-
  Four concrete, evidenced findings surfaced while measuring honest coverage/readiness for the Nick AI platform
  disclosure artifact pre-audit — real write-path bugs and schema-registration gaps on real production data, none
  previously tracked. Not this audit's own scope to fix (that plan is measurement-only); filed here per the
  findings-triage HARD RULE so they don't sit as untracked prose.
status: open
nature: process
asset_group: [sports, tradfi, prediction]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags: [data-quality, schema-gap, honest-coverage, findings]
related:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
  ]
created: 2026-08-16
last_updated: 2026-08-20
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Surfaced by the 5-agent Nick AI platform-disclosure pre-audit (2026-08-16); each finding traced to its source
  sub-agent report in /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md.
context_scope:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
    /plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md,
    unified-api-contracts/unified_api_contracts/internal/schemas,
    instruments-service/instruments_service/reference_data/adapters/prediction,
  ]
---

# Data-quality findings from the Nick AI platform-disclosure pre-audit

Four concrete, evidenced findings surfaced while measuring honest coverage/readiness for
[`/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)'s
pre-audit (2026-08-16). Fixing data-quality bugs is outside that plan's own scope (measurement only) — filed here
per the findings-triage HARD RULE so they don't sit as untracked prose in a measurement doc. Full evidence for each
is in
[`/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md`](/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md).

- [ ] [AGENT] P2. **Sports `FOOTBALL` venue write-path bug.** 910 manifest rows are stamped with venue=`FOOTBALL`
      (not a real venue) and their `instrument_type` values are literally lowercase bookmaker names (`betmgm`,
      `betway`, `bovada`, `coral`, `fanduel`, `ladbrokes_uk`, `paddypower`, `pinnacle`, `skybet`, `unibet_uk`,
      `williamhill`) — a column-swap at some write path, not a real venue (0% coverage throughout, no real data
      behind it). Find the writer stamping this and fix the column mapping; low severity (cosmetic/data-hygiene,
      doesn't affect real bookmaker coverage numbers) but worth closing before it grows. **DUPLICATE-TRACKING NOTE
      (2026-08-18, plan_reconciler)**: `plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md`
      independently tracks the SAME underlying bug (its P1/P2 todos describe the identical lowercase-bookmaker/
      FOOTBALL-venue column-swap) with no cross-reference either direction — whoever picks either of these up
      should check the other first to avoid duplicate/conflicting work.
- [ ] [AGENT] P2. **TradFi `tbbo` and `yield_curve` have real captured production data with zero registered
      schema.** `tbbo`: real captures at CME (507 rows, 100%)/NYSE (10,567, 65.96%)/NASDAQ (2,493, 33.33%) — cefi
      has a `SchemaContract` for tbbo, tradfi does not. `yield_curve`: FRED's flagship data type, 14,399 rows,
      **100% coverage**, zero `SchemaContract` anywhere. Without a registered schema there's no write-time
      validation for either — register both in `unified_api_contracts/internal/schemas/`, matching the real
      observed columns.
- [ ] [AGENT] P3. **Prediction `market_lifecycle`/`MARKET_LIFECYCLE` (both casings) show zero captured rows**
      despite real writer code in both `instruments-service/.../kalshi.py` and `.../polymarket/parsing.py`
      explicitly designed to populate it. Either the write path isn't live in prod, or rows land under a different
      classification than measured — investigate which.
- [ ] [AGENT] P3. **Sports: KALSHI appears under the sports asset_group with 20,785 manifest rows, 100%
      `empty_confirmed`, 0 real captures** — unresolved whether this is a legitimate not-yet-launched connector or a
      boundary leak from the cefi-scoped `KALSHI-PERP` exclusion list (`is_prediction_market_venue()`). Confirm
      which, and either wire it or exclude it explicitly.

## Progress Log

**2026-08-16 — filed.** Extracted from the Nick AI platform-disclosure pre-audit's 5 parallel sub-agent reports;
none of these 4 were previously tracked anywhere in the corpus (checked against the venue-readiness umbrella plan's
own open todos — DeFi's separate canonical-orthogonality candidates found in the same audit ARE already covered by
that plan's existing "audit the data-type vocabulary for near-duplicates" / "audit for orphaned data types" P0
todos, so those are not duplicated here).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **RECLASSIFY, whole-doc.** All 4 open
  findings are bounded, worker-determinable code/schema/investigation tasks (find-a-writer-and-fix-a-column-mapping;
  register 2 known-schema SchemaContracts against a same-shape cefi precedent; 2 bounded diagnose-one-of-N-hypotheses
  investigations) that were simply never assessed for AO eligibility since filing — no operator gate, no
  `depends_on`, no redirect banner, no prior audit pass on this doc, and this doc's own filing entry confirms
  non-duplication against the rest of the corpus. Flipped `assigned_vm: NA -> planning` +
  `execution_scope: local-only -> orchestrator-agent` in place (frontmatter above); companion finalize plan:
  `nick_ai_audit_data_quality_findings_2026_08_16_finalize_2026_08_17.md`.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
