---
doc_type: epic
title: UAC Master — unified-api-contracts schema, registry, and contract-governance correctness
summary:
  L1 foundational epic owning unified-api-contracts' own schema/contract/registry correctness and governance —
  schema locking + versioning (SchemaContract wrapper), canonical instrument_id derivation, the OrderStatus SSOT,
  the canonical_path_violations() oracle, and availability/semantic completeness of UAC's own registries. Carved
  out of infrastructure_master + client_isolation_and_governance_master 2026-08-18 (see Codex SSOTs).
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [uac, schema-governance, canonical, instrument-id, contract-governance, order-status]
related:
  [
    /codex/11-project-management/epic-taxonomy-2026-08-18.md,
    /plans/epics/instruments_master.md,
    /plans/epics/client_isolation_and_governance_master.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
  ]
created: 2026-08-18
name: uac_master
tier: L1
priority: P1
assigned_vm: NA
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
  - /codex/04-architecture/client-funds-isolation.md
  - /codex/02-data/four-surface-reconciliation-procedure.md
related_plans:
  - ../active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md
  - ../active/issues/instruments_schema_not_locked_versioned_2026_08_18.md
  - ../active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md
  - ../active/issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md
  - ../active/issues/yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md
last_updated: 2026-08-18
locked_by:
locked_since:
---

# UAC Master — unified-api-contracts schema, registry, and contract-governance correctness

## Why this epic exists

Created 2026-08-18 as part of the epic-taxonomy restructure (`/codex/11-project-management/epic-taxonomy-2026-08-18.md`)
— unified-api-contracts is the fleet's schema/contract SSOT (`unified_api_contracts.{domain}`, never `canonical.*` /
deleted dirs), yet no epic owned its own schema-governance correctness directly. UAC-topic content was scattered
across `infrastructure_master` (general catch-all references) and `client_isolation_and_governance_master` (which
owned a "UAC schema evolution" narrative section but had zero actual referrer docs pointing at it for that reason —
see `client_isolation_and_governance_master.md`'s trimmed "🔴 canonical instrument_id" cross-reference, which stays a
pointer to `instruments_master`'s own audit rather than becoming a real UAC-master child, since that specific work was
never filed as a doc under this epic). This epic is the real home for UAC's OWN schema/registry correctness going
forward.

**Small bucket by design, not by omission**: content-based classification of the ~300 docs carved out of
`infrastructure_master` (see the restructure plan's Progress Log) found only 5 docs whose PRIMARY subject is UAC's own
schema/contract governance, as distinct from (a) asset-group data content that merely references a UAC-defined type in
passing (stayed with `security_and_cross_cutting_master` or the relevant asset-group epic), and (b) CI-gate blind
spots where the trigger was a UAC content change but the doc's own subject is the GATE mechanism, not UAC's schema
(went to `ci_master` — see that epic's "Cross-epic coordination" section for the boundary rule applied). Most UAC
content genuinely lives elsewhere already: `instruments_master` (instrument-id/instrument-type schema, the audit this
epic's "🔴" cross-reference points at) and `client_isolation_and_governance_master` (client/strategy ID + share-class
schema).

## Scope

- **Schema locking + versioning** — whether `INSTRUMENTS_PARQUET_SCHEMA` and its per-asset-group `SchemaContract`
  wrappers carry a real version field, are consulted by writers/readers, and would fail loud on a silent column
  change (currently: no — see `instruments_schema_not_locked_versioned_2026_08_18`, the epic's largest single item).
- **The `canonical_path_violations()` oracle** — the machine oracle for canonical/non-canonical GCS path structure;
  known blind spots (path-structure-only, doesn't validate the filename instrument_id stem or field VALUES) are
  tracked here when the fix is to the oracle itself.
- **Order/state SSOT drift** — whether a documented state machine (e.g. `order-state-machine.md`'s 9-state
  `OrderState`) actually matches the shipped UAC `OrderStatus` enum.
- **Registry/invariant completeness** — UAC-owned cross-repo invariants (e.g. the venue-coverage reachability cascade
  invariant) failing because a venue/registry entry was never properly completed, not because the invariant itself is
  wrong.
- **Availability/semantic registry completeness** — missing `AVAILABILITY_AT_SEMANTICS` / similar semantic-decision
  entries in UAC's own registries that block UAC's own ship pipeline tree-wide.

**Explicitly NOT in scope** (stays with `ci_master` or the relevant asset-group epic instead): a CI/SIT gate's
blindness to a UAC content edit (the gate is the subject, not the schema); asset-group data-content bugs that happen
to reference a UAC-defined type/registry value in passing.

## Current state (as of the 2026-08-18 carve-out)

Only 5 docs, all `status: open` issue docs (no active build-out plan yet) — this is a real gap, not a sign the domain
is healthy:

- **`instruments_schema_not_locked_versioned_2026_08_18`** (P1, 0.8 AI-days) — the largest and most structural: the
  51/85-column instruments schema has no version field anywhere in the chain (schema itself, `SchemaContract`
  wrapper, per-asset-group synthesized contracts), and no golden/hash test would catch a silent column change. Carries
  a tracked 4-part fix.
- **`canonical_path_oracle_blind_to_filename_stem_2026_07_20`** (P0) — `canonical_path_violations()` returned
  FALSE-CLEAN for ~811,200 wire-named CeFi objects because it never validated the filename instrument-id stem, only
  path structure. Highest-priority item in this epic — a machine oracle silently under-reporting violations at this
  volume is a correctness-gate failure, not a cosmetic bug.
- **`order_state_machine_ssot_vs_uac_orderstatus_2026_07_31`** (P2) — `order-state-machine.md` documents a 9-state
  `OrderState` that does not exist in UAC; the shipped contract is a 7-member `OrderStatus` missing states the docs
  claim are authoritative.
- **`uac_kamino_venue_reachability_cascade_regression_2026_08_15`** (P2) — the UAC-owned venue-coverage cascade
  invariant fails on the kamino DeFi venue (no reachable execution-service connector), blocking quickmerge fleet-wide
  — a registry-completeness gap, not an invariant-logic bug.
- **`yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13`** (P1, 0.2 AI-days) — mostly resolved: a half-finished
  change added a SOURCE_PRIORITY entry without the matching `AVAILABILITY_AT_SEMANTICS` entry, failing 6 UAC tests
  tree-wide and blocking every UAC ship; fixed as `tick_timestamp` 2026-08-13, only a P3 latency re-check remains open.

## Assigned active plans

_5 active issues declare `parent_epic: uac_master` in their frontmatter (carved from `infrastructure_master` +
`client_isolation_and_governance_master` 2026-08-18). Workers pick up in priority order (P0 first)._

## P0 — must complete before next foundation gate

### [`canonical_path_oracle_blind_to_filename_stem_2026_07_20`](../active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md)
**status**: open
**title**: UAC canonical_path_violations() was blind to the filename instrument-id stem — false-clean for ~811,200 wire-named CeFi objects

## P1 — important; post-current-gate

### [`instruments_schema_not_locked_versioned_2026_08_18`](../active/issues/instruments_schema_not_locked_versioned_2026_08_18.md)
**status**: open · **estimate**: 0.8 cal AI-days (class: infra)
**title**: B23 determination — the 51/85-column instruments schema is not locked or versioned; 4-part fix

### [`yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13`](../active/issues/yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md)
**status**: open · **estimate**: 0.2 cal AI-days (class: design)
**title**: tradfi ohlcv_1h added to SOURCE_PRIORITY without an availability semantic — fixed as tick_timestamp; P3 latency re-check remains

## P2 — useful; opportunistic

### [`order_state_machine_ssot_vs_uac_orderstatus_2026_07_31`](../active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md)
**status**: open
**title**: order-state-machine.md is authoritative_for a 9-state OrderState that does not exist in UAC — shipped contract is 7-member OrderStatus

### [`uac_kamino_venue_reachability_cascade_regression_2026_08_15`](../active/issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md)
**status**: open
**title**: unified-api-contracts: kamino DeFi venue fails execution-service reachability cascade invariant

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Cross-epic coordination

- **`instruments_master`** — owns instrument-id/instrument-type schema content broadly (the
  `canonical_instrument_id_audit_2026_07_08` referenced by `client_isolation_and_governance_master`'s trimmed UAC
  cross-reference lives there, not here); this epic owns UAC's schema-CONTRACT mechanics (locking, versioning, the
  path oracle), not every instrument-schema-adjacent audit.
- **`client_isolation_and_governance_master`** — its "🔴 canonical instrument_id — UAC-schema governance angle"
  section is trimmed to a pointer only (no docs actually moved from there — see that epic's own note); its
  `ClientConfig`/share-class/strategy-ID UAC-schema work stays there, since it is client-governance-specific, not
  general contract-governance.
- **`ci_master`** — a CI/SIT gate's blindness to a UAC content edit stays in `ci_master` (the gate is the subject);
  only genuine UAC schema/registry correctness/completeness work lives here. See `ci_master`'s own cross-epic note for
  the boundary examples (`breaking_change_differ_blind_to_registry_data_dicts`,
  `uac_value_only_config_change_breaks_utl_untested`).

## Codex SSOTs

| Doc | Owns |
| --- | --- |
| `/codex/04-architecture/client-funds-isolation.md` | Cross-client UAC schema enforcement (3-layer) |
| `/codex/02-data/four-surface-reconciliation-procedure.md` | The `canonical_path_violations()` oracle's scope + known blind spots |
