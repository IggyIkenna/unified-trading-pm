---
doc_type: issue
title: Close Symbiotic's remaining readiness gaps (NOT a from-zero build — most layers already exist)
summary: >-
  Operator decision 2026-08-16: get Symbiotic (restaking, DefaultCollateral model) to full readiness per the
  VENUE READINESS CONTRACT (/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md, steps 1-19).
  **Corrected same session, before this doc shipped**: an initial pass assumed Symbiotic needed building from
  scratch across every layer; a dedicated research pass found it is ALREADY wired through UAC (venue + capability
  declared), instruments-service (adapter exists), MTDS (batch adapter exists), and execution-service
  (supports_live=True) — strategy-service has a bespoke position adapter (correctly bespoke, not generic, because
  Symbiotic has withdrawal-queue state a balance read would misrepresent). The real gaps are narrower: a wrong
  hardcoded contract address, missing DeFiAdapter dispatch wiring (the actual reachability gap), a missing
  features-service calculator, an un-registered UAC LST address + venue_constants.py entry, a STALE codex catalogue
  doc claiming MTDS/execution are still pending when they've shipped, and unconfirmed manifest/backfill coverage
  (code existing is not the same claim as data flowing — this session's own recurring lesson). This doc reflects the
  corrected, verified state — do not re-read it as "build from zero."
status: resolved
nature: issue
asset_group: [cross-cutting, defi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
    unified-trading-system-ui,
  ]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [defi, symbiotic, restaking, venue-onboarding, venue-readiness-contract, honest-coverage]
priority: P1
source: operator-request-2026-08-16
parent_epic: infrastructure_master
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/karak_decommission_2026_08_16.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-16
resolved_by: unified-trading-system-ui@6065a11586
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    execution-service/execution_service/defi_execution/protocols/symbiotic.py,
    unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py,
  ]
---

> **🟢 ARCHIVED 2026-08-16** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence in `resolved_by:` (unified-trading-system-ui@6065a11586, the final
> todo to land — two commits, manifest resync + the golden-test-count fix it required) — every todo shipped
> repo@sha, cited per-todo in this doc's own checkboxes and Progress Log.
> Single-repo case (plan-of-record in this same worktree), so the checkbox flip and this `git mv` land in the same
> commit per the 2026-08-10-narrowed same-commit-flip+archival sanction.

# Close Symbiotic's remaining readiness gaps

## Ground truth — what already EXISTS, verified (do not rebuild these)

| Layer | File(s) | State |
|---|---|---|
| UAC — venue declared | `registry/defi_venues.py:78,392,477` (`SYMBIOTIC-ETHEREUM` in `ALL_DEFI_VENUES`, short↔long map, status=`live`) | ✅ exists |
| UAC — capability declared | `registry/capability_declarations/_defi.py:1067-1073` (`ProtocolClass.RESTAKING`, `data_types=["staking_yields","oracle_prices"]`) | ✅ exists, no `required_tokens` (correct — multi-vault, no single receipt token) |
| UAC — `venue_constants.py` | — | ❌ **missing entirely** (EtherFi has a full entry: capability sets, protocol type, chain, fee model, alpha profile — Symbiotic has none) |
| UAC — LST token address SSOT | `registry/lst_token_addresses.py` | ❌ **missing** — and the address currently hardcoded in execution-service is WRONG anyway (see below) |
| instruments-service | `reference_data/adapters/defi/symbiotic.py`, registered in `factory.py` | ✅ exists — "4-vault curated registry" per the catalogue doc |
| MTDS batch adapter | `market_interface/adapters/defi/restaking_symbiotic_adapter.py`, registered in `factory.py` | ✅ exists — data types `staking_yields`, `oracle_prices` |
| MDPS | — | ✅ correctly N/A — LST/restaking oracle-price and staking-yield data is consumed raw by strategy-service/FS, no candle-derivation step exists for this shape (same as EtherFi) |
| features-service | — | ❌ **missing** — zero Symbiotic hits; EtherFi's equivalent is `lst_staking_calculator.py`'s `LstStakingCalculator`, but that pattern is single-token-LST-shaped and won't fit Symbiotic's multi-vault shape directly |
| strategy-service position read | `position_interface/factory.py` `case "symbiotic":` → bespoke `position_interface/adapters/symbiotic.py` (`SymbioticPositionAdapter`) | ✅ exists, **correctly bespoke, not generic** — `_generic_token_balance_adapter`'s own docstring explicitly excludes Symbiotic ("withdrawal queues... a bare balance misrepresents" this position) |
| execution-service | `defi_execution/protocols/symbiotic.py:77-79`, `supports_live=True # real DefaultCollateral.deposit()/withdraw() via sign_and_send_transaction() (wstETH only)` | ✅ exists, real write path — **but wrong address, and zero DeFiAdapter dispatch (reachability gap)** |
| Strategy wizard | `unified-trading-system-ui`'s `lib/registry/capability-manifest.ts`, auto-derived from UAC's `openapi/capability-manifest.json` | ✅ **no direct code change needed** — once UAC fully declares the venue and the manifest is regenerated, the wizard picks it up automatically |
| Tests | `test_symbiotic_metadata.py` (IS), `test_restaking_symbiotic_adapter.py` (MTDS), `test_symbiotic_connector.py` + `test_bespoke_defi_readers.py` (strategy-service), `test_connector_live_capability.py` (execution-service) | ✅ exist per layer — **no dedicated FS test**, consistent with the FS gap above |

**Authoritative onboarding checklist**: `/codex/02-data/defi-venue-protocol-catalogue.md` — this IS the SSOT status
table (✅ PRODUCTION / 🟢 CODE-SHIPPED-AWAITING-BACKFILL / ◐ / ✗ legend), not something this doc should duplicate.
**Its Symbiotic row (line 200) is STALE**: it says "MTDS + EXEC pending Phase 3+4" — both now have real, shipped
code (table above). Fixing that row is todo #1, before anything else, so the next reader of the SSOT doc isn't
misled the same way this issue's first draft was.

## Real gaps (measured this session)

1. **Wrong hardcoded vault address.** `execution_service/defi_execution/protocols/symbiotic.py`'s
   `DEFAULT_COLLATERAL_WSTETH` constant (`0xC0d33c8D411E2d88f6c46BeEa89C51c23e23c52C`) resolves to **zero deployed
   bytecode** on live Ethereum mainnet (verified this session, block 25,765,709). The real, verified contract is
   `0xC329400492C6ff2438472D4651Ad17389fCb843a` ("Symbiotic: DC_wstETH Token" on Etherscan) — confirmed real
   bytecode, live `totalSupply()` = 16,349 wstETH. Same defect class as Karak's wrong address
   (`/plans/active/issues/karak_decommission_2026_08_16.md`), caught before it propagated further into new wiring.
2. **Zero DeFiAdapter dispatch — the actual reachability gap.** `supports_live=True` is real, but nothing in
   `DeFiAdapter`'s `_dispatch_defi_operation` gates on a `"SYMBIOTIC"` venue marker — confirmed via this session's
   own execution_service_venue_reachability_baseline.json (unified-api-contracts), which lists `symbiotic` as an
   unreachable venue alongside `morpho`/`karak`/`pendle`. This is steps 8 and 12 of the readiness contract, and it's
   the one gap that actually blocks live execution — everything else in the table above is either already correct
   or a data/documentation gap, not a "can we trade this" gap.
3. **UAC registration incomplete.** No `venue_constants.py` entry, no LST address SSOT entry (blocked on fixing the
   address first — don't migrate a wrong address into the SSOT).
4. **No features-service calculator.** Real gap, needs its own design (multi-vault shape, not the single-token LST
   calculator pattern EtherFi uses) — or an explicit "declared unused" per the umbrella plan's step 18 bar, if FS
   genuinely isn't the right consumer for this data shape.
5. **Manifest/backfill coverage unconfirmed.** Code existing at every layer is not the same claim as data actually
   flowing and reconciling — per this session's own repeated lesson ("built but unreachable" / "code-shipped
   awaiting backfill" are different states from "PRODUCTION"). This doc's batch-smoke-test proof (below) is a
   Dune-sourced spot-check, not a confirmation that MTDS's own `restaking_symbiotic_adapter.py` has actually been
   run and is reconciling in the manifest.
6. **`carry_and_yield` strategy-archetype coverage for Symbiotic specifically is unconfirmed** — the research pass
   found EtherFi's chain-map entry (`staked_basis.py:167`) but did not confirm or deny a Symbiotic equivalent;
   needs a direct check, not an assumption either way.

## Batch-backfill smoke test — PROVEN, real data (2026-08-16, this session)

Per the operator's explicit sequencing ("first smoke test... once you've proven we can get a day, then it's
great"): queried Dune's pre-indexed `symbiotic_ethereum.defaultcollateral_evt_deposit`/`_evt_withdraw` decoded
tables (ABI-decoded, no raw `eth_getLogs` needed — the free-tier RPC route hit provider-side rate limits on log
queries, Dune's indexed tables were the production-grade alternative) against the **verified real** contract
address for a single UTC day, **2026-08-15**: 3 real withdraw events, real tx hashes, real amounts (0.0116 /
0.2248 / 0.0313 wstETH), zero deposits that day. Dune query IDs: `8345258` (day slice), `8345262` (earliest
activity / genesis lookup). This proves the raw data is fetchable at daily granularity; it does NOT prove MTDS's
own adapter has been run against it (gap #5 above) — those are different claims.

**Genesis / honest-coverage floor: 2024-06-11.** Cross-verified two ways: public reporting places Symbiotic's
mainnet launch in June 2024; the earliest `Transfer` event the verified vault contract ever emitted is
`2024-06-11 11:00:35 UTC` (Dune query `8345262`). Use as the backfill floor — pre-genesis data is
fabrication-by-construction, same principle as the sports 2020-06 floor
(`/codex/02-data/sports-2020-06-data-floor.md`).

## Todos

- [x] [AGENT] P0. **Refresh the stale catalogue-doc row** (`/codex/02-data/defi-venue-protocol-catalogue.md:200`) —
      updated: EXEC column now ✅ real write path (`SymbioticConnector`, `supports_live=True`, wired into
      `DeFiAdapter` STAKE dispatch, execution-service@85c8310b20); MTDS column now
      🟢 CODE-SHIPPED-AWAITING-BACKFILL (not ✅ PRODUCTION) per the targeted live GCS check below confirming zero
      real captured rows — matches the gap #5 prediction exactly. — unified-trading-pm@4f3f315b69.
- [x] [AGENT] P0. **Fix the wrong `DEFAULT_COLLATERAL_WSTETH` address** in
      `execution_service/defi_execution/protocols/symbiotic.py` to `0xC329400492C6ff2438472D4651Ad17389fCb843a`,
      citing this issue doc as provenance (matching the `# DERIVED from <source>` citation convention every other
      address in that file uses). — execution-service@70ac877f6a, QG green.
- [x] [AGENT] P0. **Wire Symbiotic into `DeFiAdapter`'s real dispatch** (the reachability gap) — add a
      `symbiotic_connector` parameter + a `"SYMBIOTIC"` venue-gate marker in the STAKE handler (mirrors
      `LIDO-ETHEREUM`'s gating in `_execute_staking`), matching `symbiotic.py`'s existing
      `preflight_validate_operation(venue_id, "supply")` pattern. Remove `symbiotic` from
      `unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json`'s
      `unreachable_defi_venues` list in the SAME change (ratchet-down convention). — execution-service@85c8310b20,
      QG green. Baseline already excluded `symbiotic` (removed by a concurrent session earlier this session) — no
      change needed there. Also wired `symbiotic_connector` into `LiveExecutionHandler._build_defi_adapter` (the
      real live-execution constructor call site) so the connector actually reaches the adapter at runtime, not just
      in the dispatcher's type signature.
- [x] [AGENT] P0. **Add `venue_constants.py` entry** for Symbiotic (UAC) — mirror EtherFi's shape (capability sets,
      `ProtocolClass.RESTAKING`, chain, fee model, alpha profile). Added `DefiProtocolType.RESTAKING` (new enum
      value, distinct from `LIQUID_STAKING`) since Symbiotic is restaking middleware, not an LST issuer — full
      entry across `VENUE_CATEGORY_MAP`/`INSTRUMENT_TYPES_BY_VENUE`(`{"RESTAKING"}`)/`VENUE_CAPABILITIES`
      (`{STAKE, UNSTAKE}`)/`VENUE_PROTOCOL_TYPE`/`VENUE_CHAIN_MAP`/`VENUE_FEE_MODEL_MAP`/`VENUE_ALPHA_PROFILE`/
      `ZERO_ALPHA_VENUES`. Also fixed a real pre-existing gap surfaced by this addition: the reachability-checker
      test's own `DEFI_VENUE_TO_CONNECTOR_CLASS`/`DEFI_VENUE_TO_GATE_MARKER` dicts had NO entry for
      `symbiotic`/`karak`/`pendle` at all (so they measured unconditionally "unreachable" regardless of real
      execution-service wiring) — added the real `symbiotic` entry (now measures reachable) and re-added
      `karak`/`pendle` to the ratchet baseline (they are genuinely still unreachable, unrelated to this dispatch).
      — unified-api-contracts@6dba7ac515, QG green (39/39 targeted tests + full gate).
- [x] [AGENT] P0. **Add the corrected address to the UAC LST SSOT** (`registry/lst_token_addresses.py`,
      `LST_TOKEN_ADDRESS_BY_CHAIN["ETHEREUM"]["wstETH-symbiotic"]`) — composite key, decided via
      autonomous-authority (see Progress Log, resolves the `[OPERATOR]` todo below too). Mid-implementation
      discovery: initially ALSO added `"SYMBIOTIC": ("wstETH-symbiotic",)` to `LST_VENUE_TO_TOKENS` per the key's
      own suggested shape, but a live strategy-service test failure
      (`test_factory_generic_token_balance_routing.py`) proved that composition makes the address "reachable"
      through the GENERIC `GenericTokenBalanceAdapter` routing path — which Symbiotic correctly does NOT use
      (bespoke `SymbioticPositionAdapter`, withdrawal-queue state a bare `balanceOf()` would misrepresent).
      Corrected: kept the `LST_TOKEN_ADDRESS_BY_CHAIN` entry (drift-tracked against execution-service's own
      `SymbioticConnector` literal via `LST_ADDRESS_SOURCE`) but excluded it from `LST_VENUE_TO_TOKENS` with a
      documented reason, and added a matching documented exclusion to UAC's own orphan-symbol completeness test
      (`_DELIBERATELY_UNDECLARED_SYMBOLS`). — unified-api-contracts@09318066a3, 1e91acf381 (follow-up docstring
      clarity + capability-manifest regen), QG green. Also resolved a `git stash pop` conflict against a concurrent
      session that landed an equivalent fix independently (own `_DELIBERATELY_UNREACHABLE_VIA_VENUE_COMPOSITION`
      tuple-key variant) — reconciled to the concurrent session's already-landed version rather than duplicate it.
- [x] [AGENT] P1. **Confirm whether MTDS's `restaking_symbiotic_adapter.py` has actually been run and is
      reconciling in the availability manifest** — gap #5, confirmed NO. Ran a targeted (not whole-corpus) live GCS
      listing against the real prod defi market-data bucket (`market-data-tick-defi-prd-central-element-323112`,
      via `get_storage_client().list_blobs()`, never `gsutil`) across 3 sampled days spanning ~1.5 months
      (2026-07-01, 2026-08-01, 2026-08-15): 10,316 / 985 / 33 real defi blobs matched respectively (confirming the
      listing mechanism itself works against real data), **zero `SYMBIOTIC` matches across all three days**.
      Cross-checked the code: `SymbioticRestakingAdapter` is registered generically in MTDS's `factory.py`
      (`"symbiotic": ("defi", SymbioticRestakingAdapter)`), but unlike EigenLayer there is no dedicated write-
      handler script (`eigenlayer_rewards_handler.py` has no Symbiotic equivalent) — so nothing currently invokes
      it in a scheduled backfill. This is the real remaining batch-backfill work, scoped by the genesis date
      established above (2024-06-11); catalogue-doc row corrected in todo #1 above to
      🟢 CODE-SHIPPED-AWAITING-BACKFILL, not ✅ PRODUCTION.
- [x] [AGENT] P1. **Design (or explicitly decline) a features-service calculator** for Symbiotic's multi-vault
      restaking shape — DESIGNED AND BUILT, not declined. Found a real precedent to mirror: `EigenRewardsCalculator`
      is ALSO a restaking-shaped calculator (not the single-token LST pattern `lst_staking_calculator.py` uses),
      giving a real dual-path (MTDS-primary + DefiLlama-fallback) template. Built `SymbioticRestakingCalculator`
      (`features_service/onchain/app/calculators/symbiotic_restaking_calculator.py`), registered as
      `"symbiotic_restaking"`, wired into `calculators/__init__.py`. **Deliberately DefiLlama-only, no MTDS-primary
      path** — per the gap #5 finding directly above (zero real MTDS shards exist yet), building an MTDS read path
      today would mean guessing an unwritten shard-suffix convention, the exact anti-pattern
      `EigenRewardsCalculator`'s own history warns against ("a stale guess that never matched anything on disk").
      Features: `symbiotic_restaking_apy` (TVL-weighted mean across matched pools, not naive mean — avoids a
      dust-TVL pool's outlier APY dominating), `symbiotic_restaking_tvl_usd`, `symbiotic_pool_count`. Reads the
      same DefiLlama `project="symbiotic"` slug MTDS's own adapter already uses. — features-service@492b6451,
      QG green (also updated `test_golden_fixture_phase0_resolve_build_order.py`'s onchain golden snapshot for
      the newly-registered calculator name — a real expected side effect, not a bug).
- [x] [AGENT] P1. **Confirm or add `carry_and_yield` strategy-archetype coverage** for Symbiotic — confirmed ABSENT,
      then ADDED. `staked_basis.py`'s `_STAKING_PROTOCOL_CHAIN` dict (line ~163, the exact chain-map the research
      pass found EtherFi's entry in) had `"etherfi"` and `"eigenlayer"` but no `"symbiotic"` key at all —
      `recursive_staked.py` was independently confirmed to take `staking_protocol` as a free-form param with no
      chain-map dependency, so `staked_basis.py` was the only real gap. Added `"symbiotic": "ethereum"` mirroring
      the `eigenlayer` entry (same RESTAKING shape, not the LST `etherfi` shape) immediately above it.
      — strategy-service@73c9edf0, QG green.
- [x] [AGENT] P2. **Regenerate/copy the UAC `openapi/capability-manifest.json`** into
      `unified-trading-system-ui`'s wizard registry — regenerated via
      `unified-trading-pm/scripts/openapi/generate_capability_manifest.py` (the real generator; `MANIFEST_PATH` in
      `scripts/generate_archetype_capability_manifest.py` is a DIFFERENT, unrelated manifest file — do not confuse
      the two) after the UAC-layer todos above landed, then copied to
      `unified-trading-system-ui/lib/registry/capability-manifest.json` per that file's own
      `lib/registry/capability-manifest.ts` header instruction. No wizard TS code change needed, matching the
      ground-truth table's prediction. Also had to update `tests/unit/wizard/graph.test.ts` and
      `tests/unit/wizard/parity-gates.test.ts`'s hardcoded golden node/edge/venue counts (627→642 nodes,
      2882→2919 edges, 224→230 venues) — the manifest resync alone left 8 tests red against the stale counts.
      Landed as two commits (manifest resync raced a transient `.git/index.lock` held by a concurrent slot
      process — a genuinely live PID, not a stale lock, so retried rather than force-cleared; the retry split the
      ship into two quickmerges): unified-trading-system-ui@afc9860735 (manifest only) +
      unified-trading-system-ui@6065a11586 (both test files' golden counts). Both required together — verified
      full `quality-gates.sh --no-fix` green only after both landed.
- [x] [AGENT] P2. **Add a features-service test** — the calculator design todo above BUILT a real calculator (not
      declined), so this is a real test, not an N/A. Added
      `tests/onchain/unit/test_symbiotic_restaking_calculator.py` (10 tests: project-slug lockstep-with-MTDS check,
      source-name, feature-names, pool-record flattening incl. missing-pool_id skip, empty-input handling,
      TVL-weighted-APY arithmetic incl. the zero-TVL guard, and the three `fetch_data` orchestration paths —
      success / no-pools / connection-error, mirroring `test_eigen_rewards_calculator.py`'s DefiLlama-path
      coverage shape). All 10 pass. — features-service@492b6451 (same commit as the calculator), QG green.
- [x] [OPERATOR] P2. **Decide the LST SSOT key shape for multi-vault protocols** — RESOLVED via autonomous-
      authority (rule 3, operator away): composite `"<symbol>-<venue>"` key (`"wstETH-symbiotic"`) inside the
      existing single-namespace `LST_TOKEN_ADDRESS_BY_CHAIN` dict, matching the issue doc's own leading suggestion,
      over inventing a parallel SSOT structure for one venue. **Refined mid-implementation** (see the LST-SSOT
      todo above): the harder real decision wasn't the key SHAPE, it was whether Symbiotic belongs in
      `LST_VENUE_TO_TOKENS`'s generic-adapter-routing composition AT ALL — a live test failure proved it must NOT
      (bespoke adapter, not generic). Final shape: address lives in `LST_TOKEN_ADDRESS_BY_CHAIN` (composite key,
      for execution-service drift-tracking) but is explicitly excluded from `LST_VENUE_TO_TOKENS` (documented
      exception in both UAC's own orphan-check test and the dict's own comment) rather than wired into it.

## Progress Log

- **2026-08-16 (draft 1, superseded same session)**: initial pass assumed Symbiotic needed building from zero
  across every layer. Corrected before shipping — see draft 2 below.
- **2026-08-16 (draft 2, current)**: corrected after a dedicated cross-repo research pass found Symbiotic already
  substantially wired (UAC, IS, MTDS, execution-service, strategy-service all have real code). Rewrote the whole
  doc to reflect "close remaining gaps" rather than "onboard from zero" — leaving the first framing in place would
  have sent whoever picks this up down a wasteful rebuild path, the same "didn't verify, assumed absence" error
  this workspace has flagged repeatedly (`e2e_wiring_reachability_audit_2026_08_15.md`'s own lessons section).
  Batch-backfill smoke test proven (Dune, real day 2026-08-15, real events) and genesis date established
  (2024-06-11, two independent sources), per the operator's explicit sequencing. Found and scoped the wrong
  hardcoded vault address (same defect class as Karak's).
- **2026-08-16 (draft 3, dispatch complete — every todo now `[x]`)**: shipped todos #1 and #3-#9 (todos #2 and the
  address fix were already shipped by the prior session). Shipped, repo@sha per todo:
  `/codex/02-data/defi-venue-protocol-catalogue.md` refresh — unified-trading-pm@4f3f315b69; `venue_constants.py`
  RESTAKING entry + reachability-checker fix — unified-api-contracts@6dba7ac515; LST SSOT address entry (+ a
  concurrent-session conflict reconciled) — unified-api-contracts@09318066a3/1e91acf381; MTDS backfill-coverage
  finding (gap #5 confirmed, zero real captured rows via a targeted live GCS check) — research-only, no ship;
  `SymbioticRestakingCalculator` + its test — features-service@492b6451; `carry_and_yield` chain-map entry —
  strategy-service@73c9edf0; UI capability-manifest resync + golden-count fixes (two commits — the first left the
  golden node/edge/venue-count assertions stale, second corrected them; a full `quality-gates.sh --no-fix` only
  went green after both) — unified-trading-system-ui@afc9860735 + unified-trading-system-ui@6065a11586.
  **Two autonomous judgment calls made under rule 3** (operator away, decisions delegated): (1) the LST SSOT key
  shape for multi-vault protocols — composite `"<symbol>-<venue>"` key inside the existing
  `LST_TOKEN_ADDRESS_BY_CHAIN` dict, matching the doc's own leading suggestion, refined mid-implementation once a
  live strategy-service test proved the address must stay OUT of `LST_VENUE_TO_TOKENS`'s generic-adapter-routing
  composition (Symbiotic's real adapter is bespoke, not generic — see the LST-SSOT todo above for the full
  reasoning); (2) the features-service calculator build-vs-decline call — BUILT, not declined, after finding
  `EigenRewardsCalculator` as a real restaking-shaped precedent, but deliberately scoped DefiLlama-only (no
  MTDS-primary read path) since gap #5's own finding proved there is nothing on disk yet to read from.
  **One out-of-scope finding fixed on contact** (HARD RULE: a misleading pointer is fixed where found): W4/W5 in
  `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md` claimed two child plans were "forked to"
  specific paths that were never actually created — delinked (not re-authored; that's separate, larger, out-of-
  scope work) because the dead links were actively failing the shared cross-repo production-readiness validator,
  blocking every quickmerge on this dispatch. **One near-miss corrected**: this repo's own edits (todo checkboxes,
  the catalogue-doc row) were twice silently reverted by `git pull --ff-only`/autostash-quarantine cycles run
  mid-session before being committed — re-applied and shipped in the same turn as this entry, no further pulls in
  between, to avoid a third loss. Every todo box above is now `[x]`.
