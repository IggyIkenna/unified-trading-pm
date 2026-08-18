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
  - ../active/issues/yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md
last_updated: 2026-08-18
locked_by:
locked_since:
---

# UAC Master — unified-api-contracts schema, registry, and contract-governance correctness

## Report

Live HTML ledger: https://claude.ai/code/artifact/59fb54f7-d1ca-40c1-b7f2-cefd26aee3bf (generated 2026-08-18,
`/plan-reconcile uac_master`)

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

## Current state (as of the 2026-08-18 carve-out; `/plan-reconcile uac_master` same day)

Carved out with 5 open issue docs (no active build-out plan yet) — this is a real gap, not a sign the domain is
healthy. **4 remain open** after the first `/plan-reconcile uac_master` pass (same day, 2026-08-18) found the
5th genuinely done and archived it:

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
- **`uac_kamino_venue_reachability_cascade_regression_2026_08_15`** (P2) — **RESOLVED + ARCHIVED 2026-08-18** (see
  `/plans/archive/issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md`): `kamino`/`morpho` left the
  venue-coverage-cascade reachability baseline `unified-api-contracts@9b982906` (2026-08-17) — `DeFiAdapter` already
  dispatches both, confirmed by that commit's own `quality-gates.sh` run and re-verified live by `/plan-reconcile`.
- **`yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13`** (P1, 0.2 AI-days) — mostly resolved: a half-finished
  change added a SOURCE_PRIORITY entry without the matching `AVAILABILITY_AT_SEMANTICS` entry, failing 6 UAC tests
  tree-wide and blocking every UAC ship; fixed as `tick_timestamp` 2026-08-13, only a P3 latency re-check remains open.

## Assigned active plans

_4 active issues declare `parent_epic: uac_master` in their frontmatter (carved from `infrastructure_master` +
`client_isolation_and_governance_master` 2026-08-18; a 5th, `uac_kamino_venue_reachability_cascade_regression_2026_08_15`,
resolved + archived the same day — see Current state above). Workers pick up in priority order (P0 first)._

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

## Progress Log

- **`/plan-reconcile uac_master` 2026-08-18** (first reconcile pass since the epic's carve-out, same day):
  Phase -1 found no prior `plan_reconciler_findings_*.md` doc mentions `uac_master` (expected — brand-new epic) but
  found the 5-doc population is referenced by 6 pre-existing tranche findings docs (cefi/defi/tradfi/all,
  2026-08-12..08-18); reconciled every one — 2 already-fixed-by-a-concurrent-run items confirmed current
  (`canonical_path_oracle`'s mid-line checkbox + §5.1 correction), 1 genuinely open finding still live (`uac_kamino`'s
  `related:` bare-slug + missing `last_updated`, from `plan_reconciler_findings_defi_2026_08_18.md`) and fixed in the
  same pass as its archival below. Phase 0/1: read all 5 children in full; no contradictions found; 2 AO-dispatch-
  readiness gaps found (unstated intra-doc sequencing on `instruments_schema_not_locked_versioned_2026_08_18` and
  `yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13` — both had real prose-only "depends on the todo above"
  ordering with no `sequential: true`; fixed). Phase 2 done-but-unchecked: `uac_kamino_venue_reachability_cascade_regression_2026_08_15`'s
  sole open todo was HARD-evidenced done (`unified-api-contracts@9b982906`, reachable on origin/live-defi-rollout) —
  flipped and archived per the 6-step ritual (see Current state + Assigned active plans above). The other 4 children's
  open todos were verified genuinely still open by direct measurement (live-read the actual UAC/execution-service code:
  `INSTRUMENTS_SCHEMA_VERSION` doesn't exist yet, `OrderStatus` is still the 7-member enum, `schema_version` field
  doesn't exist on `SchemaContract`), not just trusted from doc text. Phase 0 entry-state hygiene sweep (corpus-wide,
  read-only): 1 pre-existing hard failure (`assigned_vm:NA` corpus-size ratchet) and 1 soft warning (delete/VM-launch
  tagging) — both corpus-wide, unrelated to this epic's 4-5 docs specifically, out of this epic-scoped run's remit
  (`/na-eligibility-audit`'s domain). Referrers fixed for the archived doc: this epic file,
  `defi_satellite_ao_dispatch_batch14_2026_08_16.md`, `venue_readiness_and_registry_hardening_2026_08_16.md`,
  `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`. No codex SSOT edit needed this pass (no
  contradiction adjudicated a codex doc as the stale side). **NOT SHIPPED this pass** — working tree only, per
  operator instruction (shared checkout under multi-session contention); the lead session commits/pushes.
