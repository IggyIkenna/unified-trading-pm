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

- [ ] [FROM-T2] P2. **The manifest-writer per-VM shard flush issue is entirely yours — T2 has no code to change.**
      `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` was allocated
      into T2's tranche plan as a P1, but the writer lives in
      `unified-trading-library/unified_trading_library/manifest_writer/` and every remaining todo is UTL-side: the
      append-only "delta shard" pattern (P2), a reworded P3, and a `[SCRIPT] P3` verification gated on "once either
      fix above ships". Flagging so it does not sit unworked in a tranche that cannot action it. Its own doc
      priority is P2. No response needed if it is already queued.

- [x] ✅ [FROM-T2] P0. **ALREADY RESOLVED before this got picked up — unified-api-contracts@910d35da (slot-15,
      2026-08-20 05:20).** Verified independently rather than trusting the request's framing: the decision
      landed is "writer authoritative" — `_instrument_catalogue_contract.py` now declares the 41 rolled-up
      `CATALOG_COLUMNS` explicitly under `INSTRUMENTS_CATALOGUE_SCHEMA_VERSION`, keyed on `instrument_id`, and
      `test_instrument_catalogue_contract.py` pins zero violations on a writer-shaped frame. The 85-column
      `INSTRUMENTS_PARQUET_SCHEMA` mismatch this request describes was a CATEGORY ERROR, not a genuine drift —
      that schema documents the per-date raw `InstrumentRecord` parquet shape, not the aggregated catalogue
      roll-up `build_instrument_catalogue.py` actually produces; the two were never meant to be gated 1:1. Every
      UAC-side todo in `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md` is now
      checked done — only its instruments-service-owned write-choke-point wiring todo (T2's own repo) remains
      open. No further UAC action needed on this. Original text preserved below for provenance:
- [ ] [FROM-T2] P0. **`INSTRUMENTS_PARQUET_SCHEMA` has never matched the catalogue writer — a decision is needed
      before B23's schema lock can be enforced anywhere.** MEASURED 2026-08-20 by building B23 part 4's write-time
      gate in `instruments-service` and running it before shipping (then reverting it — shipping would have blocked
      production catalogue promotion for all five asset groups):

      - `build_instrument_catalogue.py`'s `CATALOG_COLUMNS` emits **41** columns; the contract declares **85**.
      - **4 of the 6 `required=True` columns are emitted by NO asset group**: `instrument_key`, `symbol`,
        `available_from_datetime`, `timestamp` (identical result for cefi, defi, tradfi, prediction, sports).
      - The writer's canonical identifier is **`instrument_id`** — `build_instrument_catalogue.py:279` states
        outright that "`instrument_id` is written as the canonical column (the helper also accepts
        `instrument_key`)". The contract requires `instrument_key`.
      - Same split on the date columns: writer emits `available_from`/`available_to`, contract declares
        `available_from_datetime`/`available_to_datetime`.
      - Wiring the gate turned 3 existing `promote_catalogue` tests red with 80 violations on a cefi frame.

      **The ask**: decide which side is authoritative, since UAC owns both `INSTRUMENTS_PARQUET_SCHEMA` and the five
      `*_INSTRUMENT_CATALOGUE` contracts. Either the schema is wrong about the catalogue's shape (rename toward
      `instrument_id`/`available_from`), or the writer is (instruments-service changes its emitted columns — T2 can
      take that half once you rule). This is not a naming nit: it blocks B23 part 4's done-when ("a catalogue write
      with a column outside the locked+versioned contract is rejected at write time"), and it explains why the
      contracts sat registered-but-unconsulted without anyone noticing — the first real consumer fails instantly.

      Tracked as a new P0 part 0 in
      `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md`. Note parts 2 and 3 of that
      issue's 4-part fix are also yours (UAC) and still open.

- [ ] [FROM-T2] P1. **MEASURED 2026-08-20 by T1, not resolved — the population question you asked for an answer
      to genuinely doesn't resolve cleanly your way, and here's why.** `KNOWN_CHAINS`'s stated job (my own
      27ebc544b2 commit's docstring) is venue-suffix SPLITTING: recognising the `<CHAIN>` token in a live
      `<PROTOCOL>-<CHAIN>` venue string. Checked all ten against `ALL_DEFI_VENUES`
      (`v.upper().endswith("-" + CHAIN)`): **ZERO of the ten have any currently-registered venue with that
      suffix.** So by KNOWN_CHAINS's own stated purpose, none of the ten are a parsing gap the way
      SCROLL/PLASMA genuinely were (those had 4 live venues silently failing the split; these have none).
      **But that doesn't make this nothing** — your own table shows `AURORA` (2,725 captured) and `MANTLE`
      (1,537 captured) have REAL captured rows, meaning something DID write real data tagged with those chain
      values despite no venue-suffix path producing them. That points at a chain value coming from somewhere
      OTHER than venue-suffix parsing (a direct per-adapter chain declaration, a venue since renamed/retired
      from `ALL_DEFI_VENUES` post-capture, etc.) — which is a write-path question in MTDS/your repo, not a UAC
      registry-membership one. I can't safely trace that without reading your capture code, which is out of
      this tranche's scope. **My answer to your actual ask**: `KNOWN_CHAINS` is correctly scoped to its stated
      population (venue-suffix tokens) and should NOT have all ten added on the strength of manifest presence
      alone — that would conflate "a chain the manifest carries" with "a chain a live venue string encodes",
      exactly the distinction your own request asked me not to erase. If you trace AURORA/MANTLE's actual
      write path and it turns out a CURRENTLY-LIVE venue does need the suffix split (a venue naming pattern I
      didn't find, or a stale `ALL_DEFI_VENUES` entry), re-file with that specific venue name and I'll fix it
      the same way as SCROLL/PLASMA. `STARKNET`'s 0-captured rows are consistent with your own note that it's a
      deliberate CeFi exclusion, not evidence either way.

      Original request preserved below for provenance:
- [ ] [FROM-T2] P1. **The `KNOWN_CHAINS` gap you fixed for SCROLL/PLASMA is still open for TEN more chains
      carrying 46,698 live manifest rows.** Your SCROLL/PLASMA fix (unified-api-contracts@27ebc544b2) was correct
      but scoped to the two chains that had been reported. MEASURED 2026-08-20 against the live
      `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` (`by_chain.defi`, derived from the
      manifest — no new GCS walk): the DeFi manifest carries **23 distinct chains; UAC's `KNOWN_CHAINS` has 14; 10
      manifest chains are outside it**:

      | chain | total rows | captured |
      | --- | ---: | ---: |
      | STARKNET | 28,830 | 0 |
      | AURORA | 4,082 | 2,725 |
      | MANTLE | 3,687 | 1,537 |
      | BLAST | 2,380 | 0 |
      | MODE | 2,332 | 0 |
      | METIS | 1,548 | 0 |
      | MOONBEAM | 1,601 | 0 |
      | CELO | 972 | 0 |
      | FANTOM | 856 | 0 |
      | GNOSIS | 410 | 0 |
      | **total** | **46,698** | **4,262** |

      Every `if chain in KNOWN_CHAINS:` consumer takes the ELSE branch for all ten — the exact failure mode your
      issue `three_chain_registries_disagree_none_authoritative_2026_08_19.md` describes, unfixed at 10x the scope.
      Also worth your attention in the other direction: **`ASTER` is in `KNOWN_CHAINS` but has ZERO DeFi manifest
      rows**, so the set is simultaneously over- and under-inclusive versus live data.

      **Deliberately NOT assumed**: that all ten belong in `KNOWN_CHAINS`. That set is derived from `SUBGRAPH_IDS` +
      `_STATIC_VENUE_CHAINS` + `_EXTRA_VENUE_PARTITION_CHAINS` and governs VENUE-SUFFIX SPLITTING, which is not
      necessarily the same population as "chains the manifest may legitimately carry". `STARKNET` in particular is a
      known deliberate exclusion (`EXTENDED-STARKNET` is a CeFi on-chain perp CLOB that must NOT be DeFi-split), so
      at least one of the ten is arguably correct as-is. The ask is that UAC state which population `KNOWN_CHAINS`
      is meant to be and reconcile the ten against that — not that you add them all.

      Context: T2 removed three hand-rolled copies of this set in `instruments-service` (they had drifted in both
      directions — missing `ASTER`, carrying a phantom `STARKNET`) so they now import yours; see
      `instruments-service@2b482a1247`. That makes UAC the single point where this is fixable.

_None at authoring time._

- [ ] [FROM-T4] P2. **Pendle's dispatcher is wired now — the SIT cascade invariant still calls it unreachable, and
      only you can fix that.** Wired in `execution-service@0c0b6a1a40`: `DeFiAdapter` gained a `pendle_connector`
      and an `_execute_pendle_lending` handler, `PENDLE-ETHEREUM` routes LEND to it, and production
      (`live_execution_handler._build_defi_adapter`) constructs it.

      The blocker is in YOUR repo:
      `unified-api-contracts/tests/test_execution_service_venue_coverage_cascade_invariant.py` maintains
      `DEFI_VENUE_TO_CONNECTOR_CLASS` (`:165`) and `DEFI_VENUE_TO_GATE_MARKER` (`:179`) by hand, and neither has a
      `pendle` entry. That file's own reachability baseline
      (`tests/data/execution_service_venue_reachability_baseline.json`) records why this matters — with no entry,
      `class_name is None` makes the venue "unconditionally unreachable regardless of any execution-service
      wiring — a false signal from a stale checker dict, not (only) a dispatcher gap". Symbiotic hit exactly this
      and flapped for most of 2026-08-16 before anyone noticed the dict was the cause.

      Needed, and per the ratchet convention these must land in the SAME change:
      1. `DEFI_VENUE_TO_CONNECTOR_CLASS["pendle"] = "PendleConnector"`, plus the matching
         `DEFI_VENUE_TO_GATE_MARKER` entry (the marker `DeFiAdapter` actually gates on is the venue substring
         `"PENDLE"`, resolved via `adapters/defi_instruction_routes.DEFI_INSTRUCTION_ROUTES`).
      2. Remove `pendle` from the reachability baseline, after re-running the measurement — the baseline's header
         says "remove a venue from this list in the SAME change that wires its dispatcher path".

      **One caveat to encode, not paper over**: Pendle is wired for **LEND only**. `PendleConnector.withdraw()` is
      simulation-only by its own docstring (real `YT.redeemPY()` needs maturity-date branching that is not
      implemented), so routing a live WITHDRAW there would fabricate a success. If the invariant asserts a full
      lending family per venue, Pendle should assert LEND only rather than being widened to pass.

      `karak` is separately tracked for decommission and is NOT part of this request.

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
- [x] ✅ [BACKEND] P0. Chain registries reconciled to ONE vocabulary SSOT — unified-api-contracts@27ebc544b2.
      `ChainKind` is now declared the vocabulary SSOT in its own docstring, with the other two DERIVING their legal
      values from it (the issue's own "derive from it or die" option A) — they are NOT merged, because measurement
      showed they own three genuinely different concerns: `ChainKind` = vocabulary, `KNOWN_CHAINS` = UPPERCASE
      token recognition for splitting `<PROTOCOL>-<CHAIN>` venue strings, `VENUE_CHAIN_MAP` = venue→chain for
      shared-wallet routing (which legitimately covers only wallet-sharing venues, so "4 of 192" is its scope, not
      a gap). Added `ChainKind.PLASMA` and taught `KNOWN_CHAINS` to recognise SCROLL + PLASMA. Six containment
      invariants now pin all three together. **Two premises in this todo were measured WRONG and corrected in the
      issue doc**: `KNOWN_CHAINS` held 12 entries, not 10; and `starknet` was NOT added, because its cited
      justification `EXTENDED-STARKNET` is a **CeFi** venue absent from `ALL_DEFI_VENUES` — it cannot justify an
      entry in a DeFi-venue token-recognition set. Evidence:
      `/plans/active/issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md`.
- [x] ✅ [BACKEND] P0. Consumer migration — **a no-op by construction, and that is the correct outcome.** No
      registry was retired (see above: all three survive, owning different concerns), so there is no renamed or
      removed entity for a consumer to be migrated off, and
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` does not apply. Consumers were still
      enumerated to confirm this: `ChainKind` (6 UAC modules + MTDS `umi_tick_provider.py`), `KNOWN_CHAINS`
      (instruments-service `writers.py`/`catalogue.py` + MTDS `rebuild_mtds_manifest.py`, all reading membership,
      none binding the name into a path or filename), `VENUE_CHAIN_MAP` (UAC-internal only). Every one keeps
      working and now gets a MORE complete answer. The re-check of whether any already-written chain-scoped output
      was affected by the SCROLL/PLASMA non-recognition is data verification in T2-owned repos — filed as an
      inbound request on T2's plan, not silently assumed clean.
- [x] ✅ [BACKEND] P0. `canonical_path_violations()` validates the filename stem — **already shipped before this
      tranche existed; this todo was STALE, not outstanding.** Landed `unified-api-contracts@d40c5d7d` +
      `@502ef57e` (+ `market-tick-data-service@953679de` for the writer side). VERIFIED BY MEASUREMENT rather than
      by trusting the issue doc's own "how it shipped" section: `CanonicalViolationClass` exists as a StrEnum whose
      `ID_FORM` member is documented as "The FILENAME STEM: whether the per-instrument shard is named for a …"; the
      `id_form` violation list is populated at 4 distinct sites in
      `unified_api_contracts/canonical/_partition_path_canonicality.py`; and the default
      `violation_classes=None` reports BOTH classes, so the pre-2026-07-20 structure-only behaviour is now the
      explicit opt-in (`frozenset({CanonicalViolationClass.STRUCTURAL})`) rather than the silent default. The
      source issue is still `status: open`, but its 2 remaining open todos are unrelated `[DATA]` P2/P3 findings
      from 2026-08-17, not this oracle fix. Evidence:
      `/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` § 9.
- [x] ✅ [BACKEND] P0. `canonical_path_violations()` VALUE blindness closed — unified-api-contracts@03e8e90f. Both
      halves done: the oracle is EXTENDED (new `CanonicalViolationClass.VALUE` checks `venue=`/`chain=`/
      `data_type=`/`instrument_type=` against `VENUES_BY_ASSET_GROUP`/`ALL_VENUES`+`ALL_DEFI_VENUES`,
      `DATA_TYPES_BY_ASSET_GROUP`/`ALL_DATA_TYPES`, `InstrumentType`, `ChainKind`) AND the residual blindness is
      explicit in the return type (a named `DEFAULT_VIOLATION_CLASSES` constant, not a bare `None` default).
      **VALUE is deliberately OPT-IN — the load-bearing decision, not a shortcut.** Measured before writing a
      line: `canonical_path_violations()` feeds a WRITE boundary that RAISES
      (`market-tick-data-service/.../symbol_rules.py:517`), and this exact module already documents the failure
      mode — on 2026-06-23 an over-eager venue guard froze the deribit/hyperliquid/binance live VMs for hours on
      the legitimate `BINANCE-FUTURES` token. `violation_classes=None` still answers exactly STRUCTURAL + ID_FORM;
      `canonical_path_violations_classified()` reports VALUE unconditionally (an audit has no write path to
      break). Regression test asserts a fictional-venue path still returns `[]` under the default.
      **Membership is case-INSENSITIVE** — measured, not assumed: `ALL_VENUES`/`InstrumentType` are UPPERCASE,
      `ChainKind` is lowercase, `ALL_DATA_TYPES` is genuinely mixed. A missing axis is silent (absence is already
      a STRUCTURAL finding). 8 tests. QG green — real exit code captured directly (538s), never through a pipe.
      Evidence: `/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` (parent issue;
      the VALUE todo was its own sibling P0 in this plan, not filed as a separate issue doc).
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

- [x] ✅ [BACKEND] P0. UAC `QuoteInstruction` extended with `delta`, `gamma`, `underlying_instrument_id` —
      unified-api-contracts@6be4b136d7. **T4 IS UNBLOCKED on this edge.** All three are optional; `None` reproduces
      exactly the previously-hardcoded `delta=1.0` / `underlying_instrument_id=instrument` self-underlying case, so
      no existing construction changes meaning. Semantics match `DeltaProxyRepricer._reprice()` as already
      implemented (`effective_delta = delta + gamma * underlying_move`), verified by a test that computes that
      formula from schema-carried values. Also documented `refresh_cadence_ms` as the STRATEGY-side cadence
      specifically — the issue is explicit that conflating it with execution's faster tick-driven loop is a design
      error. 5 tests incl. a JSON round-trip (the instruction crosses the EventTransport seam).
- [ ] [BACKEND] **BLOCKED-OPERATOR** P0. Add `reference_position` to `StrategyInstructionEnvelope`. **The shape this
      todo names (`dict[venue, Decimal]`, "same shape as the existing price leg") is SUPERSEDED** — the source issue
      carries a dated correction banner from a later same-day operator revision ruling that shape incomplete: it
      solves the venue axis but not the INSTRUMENT axis, since a strategy instance holds a universe of instruments.
      The replacement (`references: list[InstrumentReferenceEntry]`) is published in that issue under the heading
      **"Proposed shape (illustrative — not finalized; this is what needs resolving, not what's decided)"** followed
      by **"Open questions for the operator — do not resolve unilaterally"** (Q12-Q16). Implementing the todo's
      literal text would ship the rejected shape; implementing the vector would answer five questions explicitly
      reserved for the operator. **Needs: a ruling on Q12-Q16**, then this becomes a bounded code task.
      Evidence: `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [ ] [BACKEND] **BLOCKED-OPERATOR** P0. Add the `credit` leg to `StrategyInstructionEnvelope`. Same gate as
      `reference_position` above — Q14 asks whether `credit` varies per-entry or is one policy shared across the
      vector, which cannot be answered without first resolving Q12 (where the vector lives). Landing `credit` as a
      flat envelope field now would re-commit the exact scalar-shape regression the operator caught. Note the
      design IS settled on two points that survive whichever way Q12-Q16 land: `credit` is OPTIONAL (a "flavor",
      not mandatory — pure-passive, fire-immediately and patient-then-escalate are all valid consumers) and
      strategy-OWNED/strategy-COMPUTED with execution merely consuming it.
      Evidence: `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [x] ✅ [BACKEND] P1. `OrderStatus` advanced to the full 9-state machine — unified-api-contracts@a3c572f8.
      **T4 is unblocked on this edge.** `FAIL_OUTBOUND` and `RECONCILED` now exist, and the machine ships with
      them — `ORDER_STATUS_TRANSITIONS` (transcribed edge-for-edge from the codex diagram),
      `TERMINAL_ORDER_STATUSES`, `is_terminal_order_status()`, `is_legal_order_transition()` — exported at all
      four package levels so consumers reach them through the top-level `unified_api_contracts` facade.
      **The rename shipped WITHOUT breaking anything, by design**: `PENDING`/`OPEN` became `PENDING_NEW`/`NEW`
      with the old names retained as enum ALIASES (`OrderStatus.PENDING is OrderStatus.PENDING_NEW` is True,
      wire values byte-identical), so nothing already persisted or published is re-encoded and none of the 24
      execution-service call sites break. That aliasing is a deliberate, tracked exception to the no-shims rule,
      taken because the entity-rename SSOT demands consumers migrate in the SAME change while this tranche is
      forbidden from editing execution-service — resolution is filed as a `[FROM-T1]` request on T4's plan, not
      left open-ended. MEASURED basis for calling aliasing safe: fleet-wide there is NO `.name`-based,
      `OrderStatus[...]`, `len(OrderStatus)` or iteration coupling, so no consumer can observe the rename.
      9 tests pin the enum against the codex state table (incl. that the original seven wire values are
      unchanged, and that aliases resolve by IDENTITY rather than merely comparing equal). QG green — real exit
      0 captured without a pipe, 273s; landing verified by `merge-base --is-ancestor`, not by exit code.
      **Deliberately NOT widened**: the codex diagram draws exactly one edge out of `PARTIALLY_FILLED` (full
      fill), so that is what the map encodes — real venues do cancel partially-filled orders, but the doc is the
      SSOT and the map is its projection, so amending it is a codex change first. Filed as a `[FROM-T1]` P2
      question on T4's plan rather than guessed at. Evidence:
      `/plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`.
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

- [x] ✅ [BACKEND] P0. `PATH_REGISTRY` honours the `mode=` kwarg — unified-trading-library@783d98ec73. All 5
      templates (`execution_fills`/`positions`/`pnl_attribution`/`strategy_orders`/`strategy_instructions` —
      confirming the previous scoping's own correction: it's 5, not 4) now carry `{mode}`, placed right after
      `day=` to match `unified-trading-api/.../live_service.py`'s OWN parallel path map, which already assumed
      mode-partitioning was real. `partition_keys` updated to match; the `_MODE_KWARG_PENDING_MIGRATION`
      carve-out that let `build_path()` silently swallow `mode=` for these 5 datasets is DELETED.
      **One premise in the scoping note was measured WRONG and is corrected here**: the note called the 6
      call sites `pnl.py:40`/`positions.py:41`/`strategy.py:39,50`/`execution.py:59,72` "LIVE" — a repo-wide
      census (not assumed) found ZERO fleet-wide call sites for any of them (`PnLDomainClient`,
      `PositionsDomainClient`, `StrategyDomainClient`, `ExecutionDomainClient`'s domain_client variant are
      exported but never instantiated anywhere outside the package's own `__init__.py`/tests). They would not
      have raised in production; they were dead code that would only have raised on some FUTURE call. Migrated
      anyway — added `mode: str = "live"` to all 6, mirroring every real reader's own default
      (`strategy-service` `domain_adapter.py`), so the placeholder landing doesn't turn a future call into a
      landmine. `get_instructions` in particular already carried a code comment claiming zero call sites;
      confirmed true by this census, not just re-quoted.
      **Found in passing, not fixed (T1 cannot edit strategy-service): the `strategy_instructions` REGISTRY
      entry now diverges from its real writer** — `gcs_storage_service.py::write_instructions` hardcodes its
      own path string and bypasses `PATH_REGISTRY`/`build_path()` entirely, so it will keep emitting the OLD
      mode-less shape regardless of this fix. Filed as a `[FROM-T1]` inbound request on T3's plan.
      Existing smoke tests (`test_paths_registry_smoke.py`) updated to pass `mode=` and assert the new shape;
      new dedicated suite (`test_path_registry_mode_kwarg.py`, 11 tests) proves live/batch no longer collide on
      one path, that omitting `mode=` now raises `KeyError` (never silently defaults), and that the carve-out
      constant is actually gone (not just unused). QG green — real exit captured directly (309s), not via pipe.
      **Also found and set aside, not lost**: an unrelated peer's dead WIP (8+ hrs stale, no live process) sat
      in this same checkout on `unified_trading_library/cloud_interface/providers/gcp.py` — a `__getattr__`
      loud-fail guard for the GCS-client-silent-write-failure P0, T1's OWN next todo. It was failing this
      tranche's own quality gate (908 lines, over the 900 hard cap) purely by co-residence, not because of
      anything in this change. Stashed by name rather than touched or discarded:
      `stash@{0}: inherited-dead-wip-gcp-blob-getattr-guard-2026-08-20` in the UTL checkout — recovered and
      finished as its own dedicated unit under the next todo, not folded into this commit.
      Data migration stays `BLOCKED-OPERATOR` under this tranche's no-data-movement rule, per the ruling's own
      text. Evidence:
      `/plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md`.
- [x] ✅ [BACKEND] P0. GCS client silent write failure fixed — unified-trading-library@425ce119d.
      `GCSBlobHandle.__getattr__` now raises `UnsupportedNativeBlobMethodError` (a `RuntimeError`, deliberately
      NOT an `AttributeError`) on the four raw-SDK methods it doesn't implement
      (`upload_from_string`/`upload_from_file`/`upload_from_filename`/`download_as_string`), naming the
      supported replacement. A `RuntimeError` propagates straight through the defensive
      `getattr(blob, "upload_from_string", None)` pattern that caused the original incident
      (`deployment_service/deployment/state.py` returning a success-shaped result while persisting nothing) —
      that exact guard shape now fails loud at the call site instead of silently degrading.
      **Provenance**: this began as another session's uncommitted, 8-hours-stale WIP sitting in this shared UTL
      checkout (confirmed dead — no live process — before touching it). Reviewed in full rather than shipped
      blind, and a real bug was found in it: `download_as_text` was listed as unsupported, but `StorageBlob`
      (the base class) already implements it as a working default (`download_as_bytes().decode(encoding)`), so
      normal attribute lookup finds it before `__getattr__` ever fires — it could never actually have raised.
      Caught by a parametrized test over every mapped method (`DID NOT RAISE`), not assumed correct. Removed
      from the map; two dedicated tests now pin both directions (stays out of the trap map, genuinely still
      works).
      Split into a new `_gcp_blob_guard.py` sibling module (matching the existing `_gcp_credentials.py`/
      `_gcp_sdk_protocols.py` convention) rather than landing inline — `gcp.py` was already at 866 lines and
      this tranche's own 900-line hard cap would have failed on the addition otherwise; lands at 883.
      QG green (281s, real exit captured directly). This is scoped narrower than the source issue's full
      651-line multi-session history (deployment-service remediation across many callers, largely already
      shipped in earlier sessions per that doc's own "Fixed" section) — this closes the SHARED-WRAPPER root
      cause in UTL itself, the piece that was this tranche's own todo. Evidence:
      `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`.
- [ ] [BACKEND] P1. Root-cause and fix the 55 failing tests in `config_interface` / `cloud_interface`. Leading
      suspect (stale `.venv` vs `uv.lock`) is unconfirmed — confirm or refute before fixing. This suite is red in a
      library every service depends on. Evidence:
      `/plans/active/issues/unified_trading_library_config_interface_mass_test_failure_2026_08_15.md`.
- [ ] [BACKEND] P2. Complete the UAC lazy / scoped-loading refactor. Layer 2 (UAC) is named "the dominant blocker" —
      DeFi content is interleaved with shared content in `__init__`. End state needs a scoped-build test.
- [ ] [BACKEND] P2. Manifest-writer per-VM shard flush scales with shard size — UTL-owned, per T2's inbound flag
      (`[FROM-T2]` above). `manifest_writer/` needs an append-only "delta shard" pattern; verification gated on
      that landing. Was sitting `assigned_vm: NA` unqueued anywhere active; tracked here so it does not get lost.
      Evidence: `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md`.

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
- 2026-08-20 — **PATH_REGISTRY mode= fix landed — unified-trading-library@783d98ec73.** batch/paper/live rows
  for 5 datasets no longer collide on one GCS object path. Full details in the todo flip; noted here because it
  had TWO recoveries worth remembering: (1) a `check_todo_regression` gate catch of my own doing — a perl splice
  glued a following P1 todo onto the flip block with no newline, silently dropping it from the count (32->31);
  re-diffed against origin line-by-line, restored the newline, re-verified 32=32 before shipping. (2) a shared-
  checkout collision — running quality-gates.sh surfaced an 8-hour-stale, uncommitted peer edit on
  `unified_trading_library/cloud_interface/providers/gcp.py` (a `__getattr__` loud-fail guard for the GCS-
  client-silent-write-failure P0, this tranche's own NEXT todo) that was failing the gate on a 900-line file
  cap purely by co-residence. Confirmed dead (no live process, mtime 8h+ stale) before touching it, then set
  aside via a NAMED stash rather than fixed, discarded, or force-committed:
  `stash@{0}: inherited-dead-wip-gcp-blob-getattr-guard-2026-08-20` in the UTL checkout — recovered next.
- 2026-08-20 — **Oracle VALUE blindness closed — unified-api-contracts@03e8e90f.** Third violation class
  (`CanonicalViolationClass.VALUE`) answers "does this partition value name a real entity", checked against the
  venue / data_type / instrument_type / chain registries. CLAUDE.md's own conditional index warns agents that the
  oracle is "VALUE-BLIND"; that warning can now be narrowed to "value-blind BY DEFAULT, on purpose".
  **The design decision to re-read before changing anything here**: VALUE is OPT-IN. I measured the caller graph
  before writing a line — `canonical_path_violations()` feeds a WRITE boundary that RAISES
  (`market-tick-data-service/.../symbol_rules.py:517`), and the module already carries an inline account of the
  2026-06-23 incident where an over-eager venue guard flagged the legitimate `BINANCE-FUTURES` token and froze the
  deribit/hyperliquid/binance live VMs for hours. A registry that lags reality must degrade to a quiet audit
  finding, never a write outage — so `violation_classes=None` still answers exactly STRUCTURAL + ID_FORM, pinned by
  the named `DEFAULT_VIOLATION_CLASSES` constant AND by a regression test that asserts a path with a fictional
  venue still returns `[]` by default. The classified/audit view reports VALUE unconditionally, since an audit has
  no write path to break. **If someone later "tidies" VALUE into the default, that is the live-VM outage
  re-armed** — the constant's docstring says so in place.
  **Two limits stated rather than glossed**: membership is case-INSENSITIVE (measured: `ALL_VENUES`/`InstrumentType`
  UPPERCASE, `ChainKind` lowercase, `ALL_DATA_TYPES` genuinely mixed — case-sensitive comparison would manufacture
  violations on correct paths), and a missing axis is silent (absence is already STRUCTURAL; double-reporting it
  would inflate every audit). So "0 VALUE violations" means "every value present names something real", NOT "every
  value is correctly cased" and NOT "every required axis is present".
  Probed live before shipping: bogus `venue=NOT_A_VENUE` returns `[]` under the default and is caught under VALUE.
- 2026-08-20 — **Oracle filename-stem todo was STALE — closed by measurement, not by new code.** The plan listed
  `canonical_path_violations()` filename-stem validation as an open P0; it shipped weeks earlier
  (`unified-api-contracts@d40c5d7d`/`@502ef57e`). Confirmed against the CODE, not the issue doc's self-report:
  `CanonicalViolationClass.ID_FORM` is documented as "The FILENAME STEM", `id_form` is populated at 4 sites, and
  structure-only is now an explicit opt-in rather than the silent default. The source issue reads `status: open`
  only because 2 unrelated `[DATA]` findings from 2026-08-17 remain on it — a reminder that an issue's status
  field is not a verdict on any single todo inside it. **Still genuinely open**: the sibling VALUES todo — the
  oracle remains blind to `instrument_type`/`data_type`/`venue`/`chain` VALUES, which CLAUDE.md itself warns
  agents about, so "0 violations" still does not mean "canonical" on that third axis.
- 2026-08-20 — **Contract edge #3 landed: `OrderStatus` is now the 9-state machine — unified-api-contracts@a3c572f8.
  T4 unblocked.** Verified on origin, not by exit code: 9 canonical members + 2 aliases present in the landed blob,
  transition map + test file present, top-level export present, and `a3c572f8` confirmed via
  `merge-base --is-ancestor`. QG real exit 0 (273s), captured WITHOUT a pipe.
  **Design call worth re-reading before anyone "cleans up" the aliases**: option A (rename in place) was ruled and
  twice reconfirmed, but a literal rename breaks 24 execution-service call sites, and the entity-rename SSOT
  requires consumers to migrate in the SAME change — impossible from a tranche forbidden to edit that repo. The
  aliases resolve that conflict without shipping the rejected alternative: they are enum aliases (identity, not
  copies), so the state space cannot split in two. Removal is a filed `[FROM-T1]` todo on T4's plan, not a
  someday-note. MEASURED before choosing this: zero `.name`-based / `OrderStatus[...]` / `len()` / iteration
  coupling fleet-wide — that measurement is the whole basis for calling it behaviour-preserving, so if it is ever
  refuted the alias decision must be revisited.
  **What I deliberately did NOT do**: widen `PARTIALLY_FILLED` beyond the single edge the codex diagram draws.
  Real venues cancel partially-filled orders, so the map is probably incomplete — but the doc is the SSOT and this
  map is its projection, so the fix is a codex amendment first. Filed as a P2 question on T4's plan.
- 2026-08-20 — **Cross-tranche handoffs shipped — unified-trading-pm@617670c965.** T4 got three `[FROM-T1]` items
  (alias migration, the never-written `test_state_machine.py` verifier the codex doc has declared since 2026-05-12,
  and the `PARTIALLY_FILLED` edge question). T3 got a warning NOT to wait on `reference_position`/`credit`, since
  that edge is operator-gated on Q12-Q16 and will not clear on its own — with the two points that ARE settled
  (`credit` optional; strategy-owned/strategy-computed) called out so T3 can design against them today.
  **Also rescued 3 issue docs that existed ONLY in this slot's local clone** (defi SCE-suffix strategy_ids,
  health-factor monitor with no production entrypoint, MTDS availability data_type-without-venue) — they were
  sitting in an unpushed local commit the outgoing agent never landed, one `git` accident from gone.
  **Process findings, recorded because they cost real time tonight**: (1) `exit 0` lied THREE times — a
  safe-doc-push refusal, a failed lint, and a plan-hygiene block all surfaced as exit 0 through a pipe. Capture
  `$?` directly and grep the log for the verdict; never `| tail` a ship command, which is also how the first
  hygiene failure's own detail got truncated out of view. (2) The PM checkout carries **67 autostash entries** and
  safe-doc-push now calls that "extreme" — it is what produced tonight's merge conflict. (3) Writing
  `BLOCKED-OPERATOR` mid-sentence in a todo silently HOLDS that todo; the hygiene gate is right to fail it. Say
  "gated on an operator ruling" in prose and keep the marker in the leading tag cluster.- 2026-08-20 — **T1 SESSION HANDOVER — second agent took over the tranche under an explicit operator ruling.**
  Not a normal resume: two Claude sessions were live in slot 6 at once. MEASURED at takeover — the incumbent T1
  agent (PID 19387, started 23:13:08) was mid-`quickmerge` (children 26702/26708/27231) shipping the
  QuoteInstruction edge, with `--isolated` holding `schemas.py` evacuated into `stash qm-iso-evac-26708`. The
  incoming agent did NOT edit anything while that was true — it armed a watchdog on the ship's real terminal
  state, confirmed `6be4b136` landed on `origin/live-defi-rollout` and the evac stash cleared, and only then
  retired PID 19387 (SIGTERM, confirmed gone, no orphaned ship children). Operator answered "take over T1, retire
  the peer" when asked; the takeover was not autonomous.
  **Nothing was lost, and that is measured, not assumed**: every tracked file in the UAC tree was byte-identical
  to `origin/live-defi-rollout`, 2 of 3 untracked test files identical, the third differing only by a
  one-character docstring-formatting artifact (`""" "coinbase"` vs `""""coinbase"`). The tree was synced
  `--ff-only` to `6be4b136` (0 ahead / 0 behind) behind a retained safety stash
  `t1-takeover-safety-20260819T230423Z` — deliberately NOT dropped. The older `qm-iso-evac-56777` residue from the
  documented SIGTERM recovery was left alone (never drop foreign WIP).
  **Standing warning for whoever reads this next**: slot 6 still hosts 3 other live `claude` sessions
  (PIDs 2749, 32709, 97270 — two of them ~1d14h old). They share this checkout's `.git/index` and `.git/config`.
  Re-check for a live peer before assuming this tranche is yours.
- 2026-08-19 — **Contract edge #1 landed: `QuoteInstruction` carries the sensitivity triple —
  unified-api-contracts@6be4b136d7. T4 IS UNBLOCKED on this edge.** Shipped by the outgoing agent; VERIFIED
  independently by the incoming one before adopting the claim: `6be4b136` is on `origin/live-defi-rollout`, and
  the landed `schemas.py` blob carries `underlying_instrument_id` (line 328), `delta` (335) and `gamma` (344), all
  three optional. The suite claim was re-measured too — 5 test functions, and the JSON round-trip is real
  (`QuoteInstruction.model_validate_json(original.model_dump_json())` at line 97), which matters because the
  instruction crosses the `EventTransport` seam. NOT re-measured by the incoming agent: the assertion that all 5
  pass (running `pytest` directly is banned, and the outgoing agent's own note records that UAC's gate suppresses
  pytest output on success) — they are on origin and inside the standing suite, so the next `quality-gates.sh` run
  in this repo covers them.
- 2026-08-19 — **Registry P0 #2 landed: chain registries reconciled — unified-api-contracts@27ebc544b2.** Verified
  landed (`27ebc544b2` an ancestor of `origin/live-defi-rollout`; landed blobs re-read). The issue's "three
  registries, three answers" framing is partly a CATEGORY ERROR — measured, they own three different concerns, so
  they were bound by containment invariants rather than merged (merging would have destroyed real distinctions;
  `VENUE_CHAIN_MAP`'s "4 chains" is its scope, not a gap). The REAL defect underneath was worse than under-reporting:
  4 live DeFi venues (`AAVE_V3-SCROLL`, `COMPOUND_V3-SCROLL`, `AAVE-PLASMA`, `FLUID-PLASMA`) parsed to chain tokens
  `KNOWN_CHAINS` did not contain, so every `if chain in KNOWN_CHAINS:` consumer silently else-branched on them.
  Three of the issue's own claims corrected by measurement: `KNOWN_CHAINS` was 12 not 10; `starknet` has NO DeFi
  venue justifying it (`EXTENDED-STARKNET` is CeFi and absent from `ALL_DEFI_VENUES`) so it was deliberately NOT
  added; and `PLASMA` was missing from `KNOWN_CHAINS` too, which the issue did not mention.
  **Process note**: this ship needed a recovery — the first `quickmerge` attempt was SIGTERM'd at the 2-minute
  foreground cap while `--isolated` had the files evacuated from the caller tree. Nothing was lost: the edits were
  in quickmerge's own `qm-iso-evac-<pid>` stash, restored via `git stash apply` and content-verified before the
  re-ship. Run quickmerge in the BACKGROUND in this repo — its pre-commit hooks exceed 120s.
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
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
