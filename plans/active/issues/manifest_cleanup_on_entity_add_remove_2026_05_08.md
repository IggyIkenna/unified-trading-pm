---
title:
  "Manifest cleanup as MANDATORY acceptance criterion when adding/removing data_types or instrument_ids — workspace-wide
  rule, not just periodic phantom audit"
created: 2026-05-08
author: ikenna
source:
  - instruments-service/scripts/reconcile_phantom_manifest_rows_all.py (cleanup tool — run reactively as periodic audit,
    not as feature-add gate)
  - CLAUDE.md "Reconciliation incidents:
      2026-04-29 — 167k fake PLAYER_VALUES denorm rows + 15k legacy phantoms cleaned up; 2026-05-04 — 130,897
      false-positive phantoms across CeFi"
  - operator directive 2026-05-08:
      "wherever you are removing an entity or adding one, we need to make sure that, in the issues that we reported, we
      have removed them from the manifest as well. They don't appear in data status where they're not supposed to, or
      they appear there if they're supposed to. Sometimes we just did one-off changes in sports or adding stuff in
      features, but we didn't do the proper data manifest updates. Those need to be flagged too."
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Manifest cleanup mandate on entity add/remove

> **Severity**: P1 — silent drift between code/UAC SSOT and manifest's view of "what should exist"; affects every
> coverage % displayed in deployment-ui drilldowns; has caused multiple post-hoc reconciliation incidents. **Blast
> radius**: workspace rule (CLAUDE.md addition) + every plan that adds/removes a data_type or instrument_id (every
> existing P0/P1 issue filed 2026-05-08 must adopt this acceptance criterion) + retro audit of historical entity
> adds/removes. **Suggested owner**: workspace rule lands in CLAUDE.md immediately; retro audit folds into
> `infrastructure_master_2026_05_07.plan.md`.

## What I found

Reconciliation tool exists:
[`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`](../../../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py)
— handles 5 drift axes (hive-vocab `category=` vs `asset_group=`, instrument_type casing, path-prefix drift,
chain-bundle equivalence, empty schema-4 types). **But it's run REACTIVELY as periodic audit, not PREVENTIVELY at
feature-add time.**

Per CLAUDE.md "Manifest phantom audit" section, the reconciler caught:

- **2026-04-29**: 167k fake PLAYER_VALUES denorm rows + 15k legacy phantoms — discovered weeks after the change that
  introduced them.
- **2026-05-04**: 130,897 false-positive phantoms across CeFi — discovered via post-hoc audit after sustained operator
  confusion about coverage %.

In both cases, the original change (PLAYER_VALUES denorm migration; CeFi schema-4 / chain-bundle migration) shipped
without paired manifest cleanup. The drift was discovered + cleaned only when an operator noticed coverage % numbers
didn't match expectations and ran the audit.

**No workspace-wide rule** mandates "every plan that adds/removes a data_type or instrument_id MUST include manifest
cleanup as an explicit acceptance criterion." The reconciler is a safety net, not a process gate.

## Why it matters

- **Coverage % lies**: deployment-ui drilldowns show coverage %s computed from `(captured / expected universe)`. If the
  manifest has stale rows for a removed data_type, the denominator includes phantom rows — coverage % is wrong,
  sometimes dramatically (the 130k false-positive incident moved coverage % readings by 5-10 percentage points across
  CeFi venues).
- **Operator decision-making degraded**: when an operator looks at deployment-ui and sees "FIXTURE_STATS 74% captured" —
  is that 74% real, or is that 74% of a stale denominator that includes phantoms? Without a hard rule, the answer is
  "unknown until audit."
- **writegate Phase 3.D.5 v2 expected-universe enumerator depends on it**: Wave 3 enumerator derives the expected
  universe from `instruments-service catalog × dates × data_types`. If catalog adds a data_type without removing the
  legacy one's manifest rows, the expected-universe denominator double-counts.
- **Compounds with every other 2026-05-08 issue**: each of issues 1, 2, 8, 10, 11 either ADDS new data_types
  (FIXTURES_SCHEDULE / FIXTURES_OUTCOMES / sports lifecycle / futures lifecycle / time-versioned governance params) OR
  moves entities (CLOB-on-chain venue asset_group reclassification). Without this mandate, every one of those changes
  risks shipping with stale manifest rows.

## Recommended decision

### Phase 1 — Workspace rule in CLAUDE.md

New section in CLAUDE.md "Manifest cleanup on entity add/remove (HARD RULE)" stating:

> Every plan, issue doc, or commit that adds or removes a data_type, asset_group, venue, instrument_id pattern, or
> shard-key axis MUST include explicit manifest cleanup as an acceptance criterion. Two checkboxes minimum:
>
> - **On REMOVE**: legacy manifest rows for the removed entity purged via
>   `reconcile_phantom_manifest_rows_all.py --asset-group <X> --apply-flips` (or equivalent targeted reconciler).
> - **On ADD**: writegate v2 expected-universe enumerator re-run after the new entity lands so manifest rows
>   pre-populate as `expected_unattempted` for the new entity's universe.
>
> **No exception for one-off changes** — even hot-fix migrations and renames trigger the mandate. The reactive
> `reconcile_phantom_manifest_rows_all.py` audit is a safety net, not the primary mechanism.
>
> **Reviewers reject** any plan or issue doc that adds/removes an entity without the two checkboxes. **Reviewers
> reject** any commit that adds/removes an entity without the matching reconciler-run evidence (commit message includes
> `MANIFEST: reconciled <N> rows / re-enumerated <K> expected_unattempted`).

### Phase 2 — Retroactive audit of recent entity add/remove cycles

Walk PM commit history for the last 90 days. Identify every commit that added/removed:

- A data_type entry in UAC `DATA_TYPES_BY_ASSET_GROUP` / `EMPTY_CONFIRMED_REASONS` / `BUNDLED_DATA_TYPES`.
- A venue entry in `VENUES_BY_ASSET_GROUP`.
- An instrument-discovery adapter or instrument-schema field.
- A shard-key axis (per CLAUDE.md "Per-asset-group shard-key matrix").

For each, verify whether the matching manifest cleanup was performed at commit time. Stragglers (probably most of them
per the 2026-04-29 + 2026-05-04 incidents) get a one-time bulk reconciler run + commit message documenting the cleanup.

### Phase 3 — Update existing 2026-05-08 issues to include manifest cleanup acceptance criteria

For each issue I filed today, add explicit manifest cleanup checkboxes:

| Issue                                                | Add/Remove scope                                                                                                                   | Manifest cleanup required                                                                            |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `fixtures_lookahead_bias_post_match_scores`          | ADD: FIXTURES_SCHEDULE + FIXTURES_OUTCOMES; REMOVE: FIXTURES (after migration)                                                     | Both: re-enumerate expected universe + purge legacy FIXTURES rows                                    |
| `fixtures_postponed_cancelled_lifecycle`             | ADD: `REFERENCE_STATUS_DISCREPANCY` typed reason; ADD: cross-source verifier outputs                                               | New error_reason rows pre-populate expected_unattempted                                              |
| `sports_per_fixture_anchored_cascade`                | CHANGE shard-atom: per-league-per-day → per-fixture-id for FIXTURE_STATS / EVENTS / LINEUPS / INJURIES                             | Migrate manifest row_keys; existing legacy rows transition to expected_unattempted at new shard atom |
| `odds_fixture_anchored_nan_fill`                     | ADD: cluster validation for ODDS_SNAPSHOT bundled writes                                                                           | Cluster validation auto-emits new manifest shape                                                     |
| `mdps_liquidity_baseline_and_live_tick_staleness`    | ADD: `DATA_QUALITY_SUSPECTED_GAP` typed reason                                                                                     | New error_reason: closed-set update propagates to manifest schema                                    |
| `mtds_live_data_recovery_self_detect`                | ADD: `LIVE_CONNECTIVITY_GAP` typed reason                                                                                          | Same                                                                                                 |
| `databento_tradfi_session_type_awareness`            | ADD: `session_type` column on TradFi candles; ADD: `EXPECTED_PRE_MARKET / POST_MARKET / MAINTENANCE_BREAK` typed reasons           | Schema migration of existing Databento parquets; new error_reasons propagate                         |
| `instruments_lifecycle_and_fixtures_endtime_cascade` | ADD: `CanonicalFuturesContract` schema; CHANGE: `CanonicalOptionsChainEntry.expiration` non-nullable; ADD: sports lifecycle fields | Migrate existing futures/options rows; sports lifecycle re-enumeration                               |
| `hard_schema_enforcement_at_write_boundary`          | ADD: `SCHEMA_VALIDATION_FAILED` typed reason                                                                                       | New error_reason rows pre-populate                                                                   |
| `defi_chain_coverage_and_clob_venues`                | ADD: Hyperliquid L1 + Starknet to chain enum; ADD: CLOB-on-chain asset_group OR DeFi venue rows                                    | Major: chain axis added to CLOB venue manifest rows                                                  |
| `defi_protocol_governance_parameters_refresh`        | ADD: time-versioned `governance_params` rows                                                                                       | New canonical path → new manifest rows                                                               |

The cross-issue cleanup work bundles naturally into a coordinated migration sprint rather than 11 separate one-offs.

### Phase 4 — Tooling: `add-or-remove-entity` workflow script

New script at `unified-trading-pm/scripts/manifest/entity-lifecycle-cleanup.sh` that:

1. Takes args `(--add|--remove) (--data-type|--venue|--instrument-pattern) <name>`
2. Runs the relevant reconciler with appropriate flags.
3. If `--add`: runs writegate v2 expected-universe enumerator for the new entity.
4. If `--remove`: runs phantom-row purge for the removed entity.
5. Outputs a commit-ready message snippet with row counts.

Plan/issue authors invoke this script as part of their PR; CI verifies the output snippet is present in the commit
message.

## Acceptance criteria

- [ ] CLAUDE.md "Manifest cleanup on entity add/remove (HARD RULE)" section landed.
- [ ] Phase 2 retroactive audit complete; bulk reconciler run for any remaining drift.
- [ ] All 11 issue docs filed 2026-05-08 amended with explicit manifest cleanup acceptance criteria.
- [ ] `entity-lifecycle-cleanup.sh` script shipped + adopted in 2 future entity-change PRs as proof of workflow.
- [ ] PM `quality-gates.sh` (or equivalent) gate: any commit that touches `DATA_TYPES_BY_ASSET_GROUP` /
      `VENUES_BY_ASSET_GROUP` / `BUNDLED_DATA_TYPES` / `EMPTY_CONFIRMED_REASONS` MUST also reference the lifecycle
      script's output in the commit message OR explicitly opt out via `[NO-MANIFEST-CLEANUP]` tag with justification.

## Open questions

- Should the reactive `reconcile_phantom_manifest_rows_all.py` continue to run periodically as a safety net, OR should
  the new preventive workflow make it obsolete? Default: keep both — preventive is the primary mechanism, reactive
  catches anything that slips through.
- For very small entity-name changes (typo fix in a venue name), is the full lifecycle workflow overkill? Probably yes
  for typo fixes — exception list TBD. Default: small renames still trigger workflow because they DO produce manifest
  drift (legacy row_key with old name vs new name).
- Coordination with writegate Phase 3.D.5 Wave 3 v2 enumerator: Wave 3 ships the cross-bucket enumerator that
  pre-populates expected_unattempted from `instruments-service catalog × dates × data_types`. Phase 1 of this issue's
  workflow depends on Wave 3 being shipped to call the enumerator on `--add`. Need to coordinate with writegate plan
  owner.
- For very large purges (the 167k PLAYER_VALUES incident scale): is there a dry-run + size-cap safety gate before
  applying? Recommend `--apply-flips` always requires `--max-rows-to-purge` arg as belt-and-suspenders.
