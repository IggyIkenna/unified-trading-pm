---
doc_type: plan
title: Code readiness T1 — contracts, library and the external API surface
summary: >-
  Tranche 1 of the five-agent code-readiness push — makes unified-api-contracts, unified-trading-library and the external API surface code-complete against the four client artefacts. Owns the registry P0s every other tranche blocks on (venue asset-group resolution, the three disagreeing chain registries, the canonical-path oracle) plus the contract extensions T3 and T4 are waiting on.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-api, deployment-api, deployment-ui, unified-trading-system-ui]
scope: [engineer]
tags: [code-readiness, uac, utl, registry-hardening, external-api, tranche-1]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/audit/results/code_readiness_allocation_2026_08_19.json,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 8
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator directive 2026-08-19 — allocate every active plan and issue across five parallel agents and drive the four
  client artefacts to code-ready, excluding manifest migration and data backfills.
assigned_role: backend_engineer
effort: max # multi-day autonomous tranche — 30-40 todos spanning several repos, cross-tranche contract edges
drift_direction: advance-code
---

# Code readiness T1 — contracts, library and the external API surface

> **Tranche 1 of 5.** Owned repos — **unified-api-contracts, unified-trading-library, unified-trading-api, deployment-api, deployment-ui, unified-trading-system-ui**. Allocated corpus —
> **62 docs** (11 spine, 2 excluded as data-movement), **130 open todos**
> at authoring. You are one of five agents running in parallel on disjoint repos.

**T1 is upstream of every other tranche.** Four of the five known cross-tranche blocking edges terminate here.
Land the contract extensions (todos 9-11) EARLY even if their consumers are not ready — an unconsumed field costs
nothing; a missing one stalls two agents for days.

## The goalpost — what "done" means (operator ruling 2026-08-19)

Everything in this tranche is **complete in code**. The ONLY things that may still be pending when this plan closes:

1. **Backfills still running** — batch data landing.
2. **Venue connectivity** — private feed and public feed, orders and trades.
3. **Market data live.**
4. **Testnets, where they exist.**
5. **Strategy archetypes code-ready for batch / paper / live — pending testing with real data.**

Anything outside those five that is not code-complete is REMAINING WORK. SSOT for the goalpost:
`/plans/epics/system_readiness_master.md` § "Definition of done".

**The acceptance test is the artefacts.** These four client-sendable documents must stop carrying `pending`,
`planned`, `partial`, `not built` or `unverified` on any claim that is not one of the five above:

- `/codex/14-customer-journeys/commercial-model/platform-architecture.html`
- `/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html`

Their status markers carry `owner: W1`…`W22` tags binding each claim to a workstream in
`/plans/epics/system_readiness_master.md`. Closing a W-item is what clears its marker. **Never clear a marker by
editing the HTML** — the marker is derived from real state; change the state, then re-derive.

## Standing rules for this tranche — HARD

- **Do NOT run backfills, manifest migrations, corpus sweeps or GCS deletes** (operator ruling 2026-08-19). Fixing
  the manifest-writer / path-registry / capture-status **code** is IN scope; launching the data movement is NOT.
  A todo whose only remaining step is "relaunch the VM" or "apply the delete" is marked `BLOCKED-OPERATOR` and left.
- **Do NOT request or wait on API keys / credentials.** Where a real credential is missing, build the adapter and
  the full code path anyway and mark the item `BLOCKED-CREDENTIALS` — never descope it. SSOT:
  `/codex/02-data/external-data-always-available-rule.md`.
- **Edit ONLY the repos this tranche owns** (listed above). Another tranche owns every other repo, and a same-file
  edit across two agents is the one thing the workspace concurrency model forbids. Need a change in someone else's
  repo? File it via the handoff protocol below — never reach across.
- **Every claim ≤ its measurement.** A proxy (line count, exit 0, a green test, a cached `origin/`) is not the
  property. Measure it or say you did not. SSOT: `/codex/12-agent-workflow/measurement-claims-discipline.md`.
- **Commit + push + flip the checkbox in the SAME turn**, with `<repo>@<sha>` evidence. SSOT:
  `/codex/12-agent-workflow/commit-push-flip-rule.md`.
- **Ship code only via** `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` from a `quality-gates.sh`-green
  tree. Doc/plan-only changes go via `bash scripts/dev/safe-doc-push.sh`.

## Cross-tranche handoff protocol

Five agents run in parallel on disjoint repos. When your work needs a change in a repo you do not own:

1. Append a `- [ ]` todo to the OWNING tranche's plan under its `## Inbound requests` section, tagged
   `[FROM-<your-tranche>]`, naming the exact symbol/file and what shape you need.
2. Commit that plan edit via `safe-doc-push.sh` (doc-only, no code).
3. Keep working — build your side against the contract you asked for, behind a feature flag or an adapter seam if
   it does not exist yet. Do not block, and do not edit their repo yourself.

**Known blocking edges at authoring time** (T1 is upstream of everyone — it runs first and fastest by design):

- T4 delta-proxy repricer generalization → needs T1 to extend UAC `QuoteInstruction` with
  `delta` / `gamma` / `underlying_instrument_id`.
- T3 + T4 strategy→execution reference triple → needs T1 to add `reference_position` and `credit` to
  `StrategyInstructionEnvelope`.
- T5 readiness dump's execution-instruction leg (the structural reason all 864 rows read `unverified`) → needs T4
  to expose a real per-venue instruction-path check.
- T5 coverage dump at `instrument_type` / `data_type` grain → needs T2 to land those axes in `coverage.json`.

## Your allocated corpus

The full, reproducible allocation lives in `/plans/audit/results/code_readiness_allocation_2026_08_19.json`,
regenerated by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`. Every one of the 892 active plan/issue
docs is assigned to exactly one tranche, so nothing is orphaned and nothing is worked twice.

```bash
python3 -c "
import json
d=json.load(open('plans/audit/results/code_readiness_allocation_2026_08_19.json'))
for x in d['tranches']['T1-contracts-library-externalapi']['docs']:
    if not x['excluded_data_movement']:
        print(('SPINE ' if x['spine'] else '      '), x['priority'], x['open_todos'], x['path'])
"
```

**Work order**: `spine: true` docs FIRST, in priority order — those are the docs that back a presentation claim.
Then the tail. A doc flagged `excluded_data_movement: true` is skipped per the standing rules above; open its
todos only to confirm they are data-movement, then leave it.


## Inbound requests

> Other tranches append `- [ ] [FROM-Tn]` items here when they need a change in a repo you own. Work them at the
> priority they state — another agent is blocked on each one.

_None at authoring time._

## Todos

### Registry SSOT — the P0s everything else is wrong without

- [x] ✅ [BACKEND] P0. `unified_api_contracts.execution.get_venue_asset_group()` fails closed —
      unified-api-contracts@d4cded41b8. Root cause MEASURED (not the reported one): the lookup was keyed on
      capability-declaration `source` names (`binance`, `aave` — 55 keys) while callers pass `PROTOCOL-CHAIN`
      venue slugs, so the two vocabularies had ZERO overlap and all 209 registered venues missed. Now delegates to
      the existing fail-closed `classify_venue_asset_group()` SSOT, keeps the capability-source table as an
      explicit second step (29 of 55 source keys resolve to nothing in the venue vocabulary, so deleting it would
      have lost real behaviour), and raises `UnknownVenueAssetGroupError` on a real miss. Caller migration was a
      no-op: a fleet-wide grep found ZERO code callers — every hit was docs/plans. Also fixed a collision found in
      the classifier itself (bare `COINBASE` → `defi` via false-match on `COINBASE-ETHEREUM`, the same trap its own
      comment documents for `BINANCE`) plus two systematic invariants so the next one fails the suite. Evidence:
      `/plans/active/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md`.
- [ ] [BACKEND] P0. Reconcile the three chain registries to ONE authoritative source. `ChainKind` (23, missing
      `plasma` which has live venues) / `KNOWN_CHAINS` (10, missing `scroll` and `starknet`, both live) /
      `VENUE_CHAIN_MAP` (4, covering 15 of 192 declared venues) give three different answers. Evidence:
      `/plans/active/issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md`.
- [ ] [BACKEND] P0. Migrate every consumer of the retired registries to the single SSOT in the SAME change — a token
      grep misses path-prefix, filename and registry-membership binders. SSOT:
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`.
- [ ] [BACKEND] P0. `canonical_path_violations()` validates the filename stem. The oracle drops the last path
      segment before validating, so raw venue wire stems and double-wrapped catalogue-miss ids return 0 violations
      == CANONICAL when they are not. Evidence:
      `/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`.
- [ ] [BACKEND] P0. `canonical_path_violations()` validates VALUES, not just path structure — today it is blind to
      `instrument_type` / `data_type` / `venue` / `chain` values. Either extend it or make the blindness explicit in
      its return type so a caller cannot mistake it for a full check.
- [ ] [BACKEND] P1. Resolve the venue→chain SSOT overlap and the `VenueFeature` / `VenueCapability` vocabulary
      overlap. Land it in the SAME change as the chain-registry P0 — same blast radius. Evidence:
      `/plans/active/registry_ssot_hardening_2026_08_16.md`.
- [ ] [BACKEND] P1. Coverage-floor registries cross-propagate. Three parallel registries exist; sports registries 1
      and 3 are structurally one SSOT. Evidence:
      `/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`.
- [ ] [BACKEND] P1. Build a genuine `(venue, instrument_type) -> data_types` combinator shared by all five asset
      groups. TradFi currently produces a provably-wrong cell (CME == ICE despite ICE having no Databento coverage).
      Evidence: `/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`.

### Contract extensions — unblock T3 and T4 EARLY

- [ ] [BACKEND] P0. Extend UAC `QuoteInstruction` with `delta`, `gamma` and `underlying_instrument_id`. **T4's
      delta-proxy repricer generalization is blocked on this** — land it first and tell T4.
- [ ] [BACKEND] P0. Add `reference_position` to `StrategyInstructionEnvelope`, per-venue, same shape as the existing
      price leg. **T3 and T4 both block on this.** Design resolved 2026-08-19, not implemented.
- [ ] [BACKEND] P0. Add the `credit` leg to `StrategyInstructionEnvelope`, completing the price + position + credit
      reference triple the artefacts describe. Evidence:
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [ ] [BACKEND] P1. Advance `OrderStatus` to the full 9-state `OrderState` machine the 23-doc SSOT describes. Ruled
      2026-08-06 (Option A — advance the contract), reconfirmed 2026-08-12; the CODE and TEST todos are both still
      open. Evidence: `/plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`.

### W5 — venue registry completeness

- [ ] [BACKEND] P0. Populate `VenueCapabilityV2.collateral_rules` / `MarginSpec` for EVERY venue. The schema exists
      and strategy-service risk-v2 already consumes it, but zero venues are populated, so every risk-v2 read
      degrades silently to "no data". Evidence: epic W5 +
      `/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md`.
- [ ] [BACKEND] P1. Add transfer-capability eligibility fields to `VenueCapabilityV2` (Copper / Ceffu /
      manual-transfer / prime-broker per venue). These are NEW fields, not just population. Blocks W22 transfer
      routing.
- [ ] [BACKEND] P1. Declare the W8 weightings SSOT in the contracts registry — which dimension each weighting
      applies to. P0 in the epic with **no owning plan** at authoring time; this todo is that owner.

### unified-trading-library

- [ ] [BACKEND] P0. `PATH_REGISTRY` honours the `mode=` kwarg. `execution_fills` / `positions` /
      `strategy_instructions` / `pnl_attribution` templates carry no `{mode}` placeholder and `build_path()`'s bare
      `str.format` silently discards it — **batch, paper and live rows for the same (date, id) write to the
      IDENTICAL GCS path today and overwrite each other.** This directly threatens the paper(W) == batch-rerun(W)
      determinism spine. Land the CODE; the data migration strategy stays operator-gated. Evidence:
      `/plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md`.
- [ ] [BACKEND] P0. Fix the GCS client silent write failure — wrong method names swallowed by a broad exception
      handler. Evidence: `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`.
- [ ] [BACKEND] P1. Root-cause and fix the 55 failing tests in `config_interface` / `cloud_interface`. Leading
      suspect (stale `.venv` vs `uv.lock`) is unconfirmed — confirm or refute before fixing. This suite is red in a
      library every service depends on. Evidence:
      `/plans/active/issues/unified_trading_library_config_interface_mass_test_failure_2026_08_15.md`.
- [ ] [BACKEND] P2. Complete the UAC lazy / scoped-loading refactor. Layer 2 (UAC) is named "the dominant blocker" —
      DeFi content is interleaved with shared content in `__init__`. End state needs a scoped-build test.

### External API surface — `platform-external-api-walkthrough.html`

- [ ] [BACKEND] P0. Replace the honest HTTP 501s with real implementations — `transfer`, `bridge`, `atomic`,
      `cancel`. The artefact currently describes these as "not a silent drop, but not yet the same".
- [ ] [BACKEND] P0. Build the counterparty-facing surface the artefact marks `planned — shape in`. Specify then
      build; the artefact must be able to cite a live route.
- [ ] [BACKEND] P1. Enumerate exactly the API surface the artefact currently leaves as "pending, to be enumerated
      exactly" — generate the reference from the shipped routes so it cannot drift.
- [ ] [BACKEND] P1. Build the kill-switch (scoped halt) and flatten-position external endpoints, both marked
      `planned, not yet` in the artefact. Arming is autonomous; resume stays inside the auto-recovery matrix. SSOT:
      `/codex/04-architecture/autonomous-recovery-matrix.md`.
- [ ] [UI] P1. Wizard stage detail, screenshots and the generated-config example are `pending, to be expanded` in
      the artefact — build the wizard surface to the point those can be generated from the real UI. Needs `[UI]` +
      `pw:L2 ✓` + a cited regression spec. SSOT: `/codex/06-coding-standards/ui-testing-layers.md`.
- [ ] [BACKEND] P2. Ceffu integration is a stub pending its API spec — build the full code path behind the provider
      interface and tag it credential-gated, never descope. Do NOT invent a distinct Ceffu custody member.
- [ ] [BACKEND] P2. Fee and gas modelling cost components — the artefact says "specified, not built, and nothing
      below is live anywhere in the pipeline today". Build the contracts side; W17's service-side split is T3/T4.

### Close-out

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation (see § "Your allocated corpus") to zero open
      todos or an explicit `BLOCKED-*` tag on every remainder.
- [ ] [AGENT] P0. Post-phase codex audit — update every changed contract doc, stub new patterns, add SUPERSEDED
      banners to invalidated docs. Plan↔codex drift is review-blocking.
- [ ] [AGENT] P0. Confirm every artefact marker owned by this tranche now reads live, or is one of the five allowed
      pending states. Re-derive; never hand-edit the HTML.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.
- 2026-08-19 — **Registry P0 #1 landed: `get_venue_asset_group()` fails closed — unified-api-contracts@d4cded41b8.**
  MEASURED, not assumed: the old lookup held 55 capability-declaration `source` keys (`binance`, `databento`) and
  callers pass venue slugs (`BINANCE-SPOT`) — zero overlap, so all 209 registered venues fell through to the
  hardcoded `"cefi"`. Blast radius measured at ZERO code callers fleet-wide, so nothing stored or published was
  corrupted. Verified landed: `d4cded41b8` confirmed an ancestor of `origin/live-defi-rollout`, and the landed blobs
  re-read from that commit carry the raise + the COINBASE fix. QG green (exit 0, full log captured); the gate
  suppresses UAC's own pytest output on success, so I additionally executed both new test files' assertions
  directly as standalone probes — all passed. Second defect found and fixed in the same commit: bare `COINBASE`
  resolved to `defi` (false-match on `COINBASE-ETHEREUM`), the same trap already documented for `BINANCE`.
- 2026-08-19 — **T1 CLAIMED by slot-6·laptop.** No other slot had claimed a tranche (checked: slots 2-5 running
  unrelated work; no tranche plan referenced in any other slot's session). Taking T1 per the coordinator's
  "launch T1 first — four blocking edges terminate here". If another agent is also on T1, that agent should
  re-read this log before editing UAC/UTL.
