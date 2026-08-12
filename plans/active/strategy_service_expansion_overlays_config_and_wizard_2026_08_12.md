---
doc_type: plan
title: >-
  Strategy-service expansion — overlay placement, one schema-backed config surface, and the capability wizard
summary: >-
  Executes the expansion work the Elysium readiness audit surfaced, and it must land BEFORE the strategy-service
  repository is sent, because the client artefacts describe this as the design rather than as a roadmap. Three threads.
  (1) Place the four research overlays that production is missing — rank-buffer hysteresis, no-trade band, beta-hedge,
  vol-target — each at the layer its scope dictates rather than in whichever engine noticed it first; the classification
  rule is whether the overlay reasons about one archetype's selection logic or about any book's risk. (2) Make
  configuration single-surfaced and hot-reloadable per operator ruling 5, starting with the archetypes that have no
  param schema at all and therefore no configurable surface. (3) Upgrade the capability wizard, whose backing
  capability-manifest graph is already the natural SSOT that rulings 3, 4 and 5 all converge on. Split from the Elysium
  plan purely because that plan reached its 1000-line hard cap.
status: draft
nature: process
asset_group: [defi, cefi]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [strategy, archetype, config, overlays, capability-wizard, hot-reload, elysium]
related:
  [
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/04-architecture/transfer-architecture.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 4
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12. Operator instruction to place the four missing overlays "depending on the principles
  we defined already — which part is config, which is strategy-archetype-specific or axis, which is cross-archetype", to
  make all such configuration live in one schema-backed hot-reloadable surface rather than in code, and to establish
  where the strategy capability wizard fits and upgrade it to the expanded reality.
---

# Strategy-service expansion — overlays, config surface, wizard

**This plan must land BEFORE the strategy-service repository is sent.** The client artefacts describe this as the
design, in the present tense, on the operator's explicit instruction — so the gap between artefact and code is closed by
executing this, not by hedging the artefact. See
[the Elysium readiness plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) §§
H.12–H.17 for the audit that produced it.

**Codex SSOTs each change is checked against:**
[capability-wizard](/codex/09-strategy/architecture-v2/capability-wizard.md) ·
[venue-eligibility](/codex/09-strategy/architecture-v2/axes/venue-eligibility.md) ·
[transfer-architecture](/codex/04-architecture/transfer-architecture.md) ·
[config-reloader-pattern](/codex/06-coding-standards/config-reloader-pattern.md) ·
[carry-funding-dispersion](/codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md)

## A. Overlay placement — the classification rule, then the four overlays

**The rule, so future overlays place themselves.** An overlay belongs to the archetype iff it reasons about **that
archetype's selection or signal logic**. It is cross-archetype iff it reasons about **any book's risk or turnover**. If
it is cross-archetype it must be implemented once and shared, never per-engine — and the test for that is whether a
second archetype would need the same thing (`TSMOM_BTC_CTA` already has its own vol-target, which is the duplication
this rule prevents). **Everything, either way, is schema-declared and instance-configurable**; "archetype-specific"
describes where the CODE lives, never that a value is hardcoded.

| Overlay                    | Scope               | Placement                                                                   | Why                                                                                                                                |
| -------------------------- | ------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Rank-buffer hysteresis** | **Archetype**       | The rank layer (upstream rank / rank allocator), params in schema           | It reasons about how THIS archetype turns a rank into a universe. Meaningless to an archetype without a rank                       |
| **No-trade band**          | **Cross-archetype** | Allocator guard-rails, beside the existing turnover cap                     | Pure churn control on target weights. `apply_guard_rails` already caps turnover — this is the same concern at instance granularity |
| **Beta-hedge**             | **Cross-archetype** | Book-level risk overlay (portfolio/risk layer), NOT a per-instrument engine | It needs an actual hedge POSITION sized off the book's trailing beta. No per-coin engine can see the book                          |
| **Vol-target**             | **Cross-archetype** | Shared sizing overlay at the book layer                                     | Scales whole-book exposure to a vol budget. **Already duplicated in `TSMOM_BTC_CTA`** — that is the argument for sharing it        |

**The load-bearing consequence:** beta-hedge and vol-target are **book-level** and the current docstring in
`funding_dispersion.py` claims they are "folded into the rank + the inverse-vol weight feature". They cannot be — a rank
scalar cannot carry a hedge position or a book exposure multiplier. That docstring is the thing to fix first, because it
is what stops anyone looking for them.

- [ ] [SCRIPT] P0. **Correct `CarryFundingDispersionEngine`'s docstring before anything else.** It currently tells a
      reader six overlays are handled elsewhere when four are absent, so the claim actively prevents discovery. State
      plainly which overlays production applies (inverse-vol via feature, squeeze veto in-engine) and which are
      book-layer work pending. **Do this even if the overlays are not built** — shipping a repository containing a
      docstring we know to be wrong is worse than shipping a known gap, and an engineer pointing an LLM at the repo will
      find it.
- [ ] [AGENT] P1. **Implement rank-buffer hysteresis at the rank layer** with `rank_buffer_k` schema-declared. Research
      used a k+6 band to hold a name until it leaves — explicitly tuned for lower turnover while holding Sharpe.
- [ ] [AGENT] P1. **Implement the no-trade band as a guard-rail**, not in an engine. `apply_guard_rails` already
      computes turnover; add a per-instance minimum weight-change threshold (research default 0.03) so every archetype
      inherits it.
- [ ] [AGENT] P0. **Implement the beta-hedge as a book-level risk overlay.** Needs the book's trailing beta to a hedge
      instrument and a real hedge position. Check `LegPortfolioState` / `target_net_delta` / `portfolio_risk_gate.py`
      for the right seam before adding a new concept. **This is the residual-market-exposure control for every
      dollar-neutral, not-delta-neutral book** — dispersion is only the first consumer.
- [ ] [AGENT] P0. **Implement vol-target ONCE at the book layer and migrate `TSMOM_BTC_CTA` onto it.** TSMOM's
      `target_vol`/`vol_floor`/`max_leverage` is the existing implementation to generalise, not a second one to keep.
      The research book calls vol-target "the drawdown DIAL", so this is the primary risk control, not a refinement.
- [ ] [AGENT] P2. **Re-derive the strategy's expected risk profile once the four land**, and only then let any
      performance figure be quoted. Production currently runs 2 of 8 overlays; the research Sharpe belongs to the
      8-overlay book.

## B. One schema-backed, hot-reloadable config surface (operator ruling 5)

Ruling recorded in
[the Elysium plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) § H.17. Machinery
that already exists: `PARAM_SCHEMA_REGISTRY` (35 archetypes, `ParamSpec` with defaults), validation via
`WizardParamPayloadError`, `config_reloaders.py`, GCS-backed `load_strategy_config()`.

- [ ] [AGENT] P0. **Add `CARRY_FUNDING_DISPERSION` to `PARAM_SCHEMA_REGISTRY`.** It is absent entirely — its five params
      are inline `decimal_param` calls with defaults buried in the engine. **This is the prerequisite for the venue-veto
      move below**: the veto needs a schema slot before it can leave the catalogue, or the hardcode simply relocates.
- [ ] [AGENT] P1. **Move the Hyperliquid dispersion exclusion out of `_FUNDING_DISPERSION_VENUES`** into instance config
      as a documented default, per
      [venue-eligibility § RULING 3](/codex/09-strategy/architecture-v2/axes/venue-eligibility.md). Emit the slot; let
      config exclude it. Then sweep for the same category error — any venue omitted for an edge reason rather than a
      capability one.
- [ ] [AGENT] P1. **Add a gate asserting factory-registered ⊆ param-schema-covered.** Three surfaces disagree today (60
      enum / 32 factory / 35 schema) and nothing detects it. A registered archetype with no schema cannot be configured
      through the validated path.
- [ ] [AGENT] P2. **Sweep remaining in-code config onto the surface.** Known: per-venue `ShareClass` in the venue
      bundles, `_BANNED_LST_PERP_COMBOS`, the archetype venue tuples, dispersion overlay thresholds. Test for each:
      **would an operator want to change this without a deploy?**
- [ ] [AGENT] P2. **Verify `config_reloaders.py` reaches instance params**, not only credentials and signal-broadcast
      config. Hot reload existing is not the same as hot reload covering what an operator most wants to change.

## C. The capability wizard — already the convergence point, needs widening

**Where it fits, established 2026-08-12.** `capability_manifest.py` (UAC) is a **capability GRAPH**, not a flat table:
`CapabilityNodeKind` nodes for archetype / venue / chain / instrument_type, with edges like
`leg --trades_instrument--> instrument_type` and `leg --supports--> venue` giving, in its own words, "the per-leg
restriction surface the flat `(asset_group, instrument_type)` cell model cannot express". It carries per-venue
collateral / margin / liquidation policy and it already references `PARAM_SCHEMA_REGISTRY`.
`strategy_config_loader.get_strategy_params()` emits the per-archetype param form from that manifest and validates the
payload against it.

**So the wizard is the UI over the restriction graph, and all three rulings converge on that graph:** ruling 3's
capability-vs-preference split is exactly what `leg --supports--> venue` edges express; ruling 4's funding-route graph
is the same graph extended with borrow/lend/custodian nodes and route edges; ruling 5's schema surface is the manifest's
`param_schema` block. **Nothing new needs inventing — the graph needs widening.**

- [ ] [AGENT] P1. **Widen the capability graph to carry funding routes** (ruling 4) — custodian, borrow venue and lend
      venue nodes, with edges expressing "this share class can reach this venue's margin currency by this route". The
      wizard then shows an operator only the feasible combinations, and an infeasible one fails at resolution rather
      than being pre-excluded.
- [ ] [AGENT] P1. **Regenerate the manifest after the schema additions in § B** so newly-schematised archetypes appear
      in the wizard automatically. Confirm this is generated rather than hand-maintained; if hand-maintained, that is a
      finding.
- [ ] [AGENT] P2. **Reflect archetype reachability in the wizard.** 28 of 60 archetypes cannot be instantiated (Elysium
      plan § H.12). Offering an unbuildable archetype in a config form is a worse failure than omitting it — the
      operator only discovers it at run time via `KeyError`.
- [ ] [AGENT] P2. **Update [capability-wizard](/codex/09-strategy/architecture-v2/capability-wizard.md)** for the
      widened graph and the ruling-3 eligibility split.
- [ ] [AGENT] P3. **Wizard is NOT part of a carve-out — stub it there.** It lives in strategy-service, so a carve-out
      must stub it: the restriction graph and universe registries are exactly the reconciliation IP a carve-out
      withholds. Carried into the carve-out plan; recorded here so the dependency is visible from this side too.

## D. Risk-limit and wallet selection — audited 2026-08-12, two of the four remaining gaps

Audited because the artefacts describe risk and wallet behaviour, so exploring before writing them means writing once.

**Risk selection — what is established.** Two layers exist and only one is schema-backed:

- **Per-archetype capital fraction, in CODE.** `archetype_defaults.py` buckets archetypes into variance tiers as bare
  `Decimal` constants — `_TIER_STABLE_STRUCTURAL` 0.500 · `_TIER_NEAR_FULL` 0.750 · `_TIER_MID_VARIANCE` 0.375 ·
  `_TIER_DIRECTIONAL_ML` 0.250 · `_TIER_HIGH_VARIANCE` 0.125 — mapped per archetype (`CARRY_BASIS_PERP` →
  stable-structural). This is risk appetite as a **hardcoded literal**, so it is a ruling-5 candidate: an operator would
  plausibly want to change a capital fraction without a deploy.
- **Per-(client, archetype) `risk_limits`, but UNTYPED.** `ClientContext` carries `client_id`, `archetype_id`,
  `shard_id` and **`risk_limits: dict[str, object]`**. So the per-client dimension exists — good — but as an untyped bag
  with no schema, no defaults and no validation. **Same weakness as `params: dict[str, str]`**, which
  `PARAM_SCHEMA_REGISTRY` was built to fix; risk limits never got the equivalent.

**Wallet selection — partially established, and I am not asserting the rest.** `treasury_monitor.py` carries a
`treasury_wallet.wallet_id` on config (example value `vault-usdc-eth`), and `WalletMappingConfig` keys treasury and
trading wallets **by share class**. What I did **not** establish is how a specific strategy _instance_ binds to a
specific wallet — whether that is derived from share class alone, or carries an instance-level override. Recorded as
unknown rather than guessed.

- [ ] [AGENT] P1. **Give `risk_limits` a typed schema with defaults**, mirroring `PARAM_SCHEMA_REGISTRY`. An untyped
      `dict[str, object]` on the risk path means a typo in a limit name silently does nothing — the failure mode is a
      limit that is never enforced, which is the worst possible one for a risk control.
- [ ] [AGENT] P2. **Move the archetype capital-fraction tiers onto the config surface**, keeping the tier map as the
      default rather than the only value. Then confirm the tiers are actually consumed — `default_kelly_fraction` is the
      only consumer I found, in `sports_value_betting.py`, and I did not establish whether the tier constants feed
      anything else. **If they are unconsumed, that is a separate and more serious finding** than being hardcoded.
- [x] [AGENT] P1. ✅ **Audited instance→wallet binding — 2026-08-12. The custodian half is already built and correct;
      the binding half is a typed contract with ZERO consumers.** Two separate answers: **(1) The custodian model
      already encodes the operator's principle exactly, and needs no design work.** The operator's framing — _"we track
      our wallets as separate from a trading perspective to monitor balances and keep things agnostic but the adaptor we
      are using to handle the money determines how we actually execute the instructions"_ — is precisely the
      custody-vs-signing-surface split in `architecture_v2/custody_surfaces.py`: `custodian` names who HOLDS,
      `SigningSurface` names the adaptor that SIGNS, and the two deliberately differ for CEFFU, whose signing **routes
      via Copper** so that it has no `SigningSurface` member at all ("documented, not invented" — asserted by
      `test_custody_surfaces.py:115`). `FIREBLOCKS_MPC` is `out_of_scope` per POD stack choice (POD = Copper + CEFFU
      only). **So the two-custodian model is a documentation and wiring job, not a modelling one.** **(2) The binding
      itself is unimplemented — the H.3 keying question has no answer in code yet.** `WalletMappingConfig` declares the
      shape (`custodian` → `chain_env` → `share_class` → one `treasury_wallet` + `trading_wallets[]`, each
      `TradingWalletConfig` carrying a **`strategy_id`**), `WALLET_CONFIG_GCS_PATH` and `wallet_config_gcs_path()` exist
      — and **nothing loads any of it.** `WalletMappingConfig`, `ShareClassWalletMapping`, `TradingWalletConfig` and
      `wallet_config_gcs_path` appear ONLY in `__init__.py` re-export plumbing and `__all__` across UAC,
      execution-service and strategy-service; the one prose mention in
      `execution-service/engine/wallet_preflight_registry.py` says "or **equivalent**", i.e. it does not commit to this
      path. Probed all four symbol names plus `wallet_mapping` and the path constant, so this is an absence established
      against the writer's own vocabulary, not one grep. **Fixed in the same turn**: the `custodian` docstring listed
      `"copper" | "fireblocks" | "mock"` — naming the out-of-scope provider and omitting CEFFU, a real June-1 POD
      custodian — while `custody_surfaces.py`, which imports `SigningSurface` from that very file, says the opposite.
      Corrected with the custody-vs-signing distinction spelled out — `unified-api-contracts@a395119c44`,
      `wallet_config.py` (gate green `--no-fix`, exit measured through a redirect not a pipe; post-push ancestry
      verified against `origin/live-defi-rollout`).
- [ ] [OPERATOR] P0. **Decide the wallet-binding key before the loader is written — it is cheap now and expensive
      later.** Two unresolved choices, both baked into the GCS path shape once a loader exists: **(a) Binding
      granularity.** The schema keys trading wallets by `strategy_id` (values in the sibling slot table read
      `AAVE_LENDING`, `L2_BASIS` — slot-table keys), but v2 instance identity is `slot_label` + `client_id`, and
      `target_universe/` emits **many slots per archetype**. A `strategy_id` key therefore cannot distinguish two
      instances of one archetype on different venues, which is the normal case, not the edge case. **(b) The client
      dimension is absent entirely.** `client_id` appears **zero** times in
      `unified_api_contracts/internal/domain/defi/`, and `WALLET_CONFIG_GCS_PATH` is
      `wallet-config/{chain_env}/wallet_mapping.json` — no client segment, so one mapping serves all clients. Per-client
      funds isolation is a HARD RULE (`CrossClientTransferForbiddenError`,
      [client-funds-isolation](/codex/04-architecture/client-funds-isolation.md)) enforced at the transfer layer by
      `client_id` metadata; if two clients' instances ever resolve to one wallet address through a client-blind mapping,
      that enforcement is keyed on something the wallet layer does not know. **This is NOT a live defect — nothing loads
      the mapping, so there is no current exposure** — but it is the reason to settle the key before wiring rather than
      after. Recommendation: key on `(client_id, slot_label)` and put `client_id` in the path.
- [ ] [AGENT] P1. **Then document the resolved binding** in
      [wallet-hierarchy-and-capital-flow](/codex/04-architecture/wallet-hierarchy-and-capital-flow.md), including the
      custody-vs-signing-surface distinction from (1) above, which no codex doc currently states in one place. The
      artefacts must not describe wallet behaviour until this lands.
- [x] [AGENT] P2. ✅ **Swept the remaining archetypes for misplaced cross-archetype logic — 2026-08-12, bounded verdict:
      exactly TWO clusters, and the catalogue is otherwise clean.** Method: enumerated every module-level `def` across
      all five `target_universe/catalog_*.py` modules (3,526 lines, 32 registered builders) rather than grepping for
      suspected names — the registry was loaded in Python to get the builder count, not inferred from a grep. Everything
      except two clusters is either a pure `build_<archetype>()` or a correctly-shared helper in `catalog_common.py`
      (`make_spec`, `slot_token`) / `catalog.py` (`specs_for_archetype`, `archetype_for_slot_label`); the five `_mm_*`
      helpers in `catalog_trading.py` are genuine sub-helpers of one archetype. **The two clusters are the two todos
      below.** The good news is the scope: the defect class `TSMOM_BTC_CTA` proved does exist, but at the catalogue
      layer it has exactly two instances, both nameable, so the carve-out build has a bounded relocation list rather
      than an open-ended audit. Evidence: `catalog_{carry,staked_basis,trading,directional,yield_defi,common}.py`,
      `catalog.py:90` (`_BUILDERS_BY_ARCHETYPE`, 32 entries against 60 enum members).
- [ ] [AGENT] P1. **Relocate the perp-venue capability cluster out of `catalog_staked_basis.py`.** It is the clearest
      instance of the defect class: `venue_supports_perp_funding()` describes itself as "asset_group-agnostic" and "the
      canonical perp-eligibility gate for hedge-leg selection", and `perp_hedge_candidate_venues(archetype=…)` takes an
      archetype parameter — both are cross-archetype by their own contract, and both are **defined inside one
      archetype's module**, re-exported up through `catalog.py` → `__init__.py` so consumers cannot see where they live.
      Two further symptoms of the same misplacement: `CARRY_BASIS_PERP`'s hedge-venue universe is defined by tuples
      NAMED `_STAKED_BASIS_ETH_PERP_VENUES` / `_STAKED_BASIS_SOL_PERP_VENUES` (`catalog_staked_basis.py:224-225`
      branches on both archetypes), and the function returns a bare `frozenset()` for the other 30 registered archetypes
      with a docstring telling callers to "consult the archetype catalog directly". That empty-set path is **deliberate
      and tested** (`test_target_universe.py:461`, `arbitrage_price_dispersion`) — so this is a placement and naming
      defect, not a correctness bug, and the fix must not change behaviour. Move to a venue-capability module alongside
      the other cross-archetype gates; rename the tuples for the archetypes that actually share them.
- [ ] [AGENT] P1. **Decide whether ADV-ranked universe resolution is a carry feature or a platform one.** It is wired
      into exactly **1 of 32 builders**: `catalog_carry.py` holds all 11 ADV references (`_resolve_dynamic_carry_coins`,
      `_DYNAMIC_CANDIDATE_POOL`, the `as_of_date` cache), and every other builder hardcodes its universe as a tuple. Yet
      the provider it calls is already generic and archetype-blind —
      `rank_top_n_by_adv(candidates, venue, asset_group, as_of, top_n, window)` in
      `engine/core/canonical_adv_ranked_universe_provider.py` — so nothing about liquidity-ranked selection is
      carry-specific. **This asymmetry is visible in the disclosed code and lands on the carve-out**: of the three
      archetypes shipping real implementations, `CARRY_BASIS_PERP` resolves its universe from measured ADV while
      `CARRY_STAKED_BASIS` reads hardcoded venue tuples, with no stated reason for the difference. Either lift the
      wiring to a shared universe-resolution helper the schema can point any archetype at, or record in codex why carry
      is the only archetype that earns it. Ties directly to the § B P2 "archetype venue tuples" sweep — same root cause,
      opposite end: carry escaped the hardcode, nothing else did.
- [x] [AGENT] P2. ✅ **Audited instrument-axis selection beyond coins — 2026-08-12. The mechanism is right; the axes are
      constants, and the structure axis is declared but unimplemented.** Three separable results, because they need
      different responses: **(1) The mechanism is sound and must not be "fixed".** Catalogue rows carry the _rule_, not
      the instrument, and two pure resolvers derive the instrument at tick: `vol_trading/atm_straddle_resolver.py`
      (strike nearest spot, nearest weekly expiry ≥ 7 DTE — the selection rule is stated ONLY in that module's own
      docstring, see the follow-up below) and `carry_and_yield/dated_contract_resolver.py`. Both are total functions of
      `(underlying, venue, mid_price, now_utc, min_dte)` with no I/O and no randomness, so a batch rerun re-derives
      identical instrument ids — the ε=0 determinism spine holds through instrument resolution, which is the hard part.
      `options.py:80-87` prefers explicit `call_instrument`/`put_instrument` params and falls back to the resolver only
      when absent: the right precedence, not a gap. **(2) Each axis is a single point, so "axis" overstates it.**
      `strike_selection` takes exactly one value in the entire repository — `"ATM"`, 27 occurrences, no
      OTM/delta-targeted/skew alternative — and expiry is the one ≥7-DTE-weekly rule. The dated family is the
      counter-example done properly: `dated_expiry` + `roll_on_dte` (`param_schema.py:163-176`, `units="expiry_tag"`) is
      a real policy axis an operator can set per instance. **(3) The declared option-structure axis is read by nothing —
      14 rows, 1 behaviour.** `build_vol_trading_options()` emits `expression` ∈ {straddle, strangle, butterfly,
      calendar, iron_condor} across 14 rows (8 Deribit + 6 CBOE), and `expression` has **zero** non-catalogue references
      anywhere in the service; so do `edge_method`, `iv_percentile_low` and `iv_percentile_high`. `options.py` reads
      exactly four params (`underlying`, `divergence_bps`, `max_slippage_bps`, `stake_vega_notional`), so **4 of the 6
      keys the catalogue emits are dead, and all 14 rows resolve to the same ATM straddle.** A strangle needs two OTM
      strikes, a butterfly three, a calendar two expiries — none is expressible through an ATM-only resolver. **Artefact
      consequence: options coverage cannot be described by counting catalogue rows**, and no artefact may imply
      butterfly/strangle/calendar capability. Evidence: `catalog_trading.py:590-636`; `param_schema.py`
      `VOL_TRADING_OPTIONS` schema =
      `[call_instrument, divergence_bps, max_slippage_bps, put_instrument, stake_vega_notional]`;
      `atm_straddle_resolver.py:1-25`.
- [ ] [AGENT] P1. **Resolve the four dead `VOL_TRADING_OPTIONS` catalogue keys** — either implement `expression` (a
      per-structure resolver beyond ATM straddle) or delete the key and collapse the 14 rows to what actually runs.
      Leaving both is the worst option: the catalogue advertises capability the engine does not have, and row counts
      become a false coverage measure. Same for `edge_method` / `iv_percentile_*` — implement or delete, and add
      whichever survives to the param schema so the validated path covers it. **This is the vol-family instance of the
      catalogue↔engine key-drift class** documented in
      [config-key contract drift](/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md),
      whose own follow-up asked for exactly this sweep beyond DeFi — found here on the `target_universe/` surface rather
      than the `archetype_slots_*` one that doc names, so **both surfaces need the sweep, not just the one named**.
- [ ] [AGENT] P2. **Record the option-instrument selection rule in codex — it currently lives only in a docstring.**
      `atm_straddle_resolver.py` attributes "strike nearest spot, nearest weekly expiry ≥ 7 DTE" to an operator ruling
      of 2026-08-08, and **no live codex doc records it**: the only `ATM` hit under `codex/09-strategy/` outside
      archived pre-v2 material is a _proposed_ `ATM_ONLY` enum member in
      [uac-registry-gaps](/codex/09-strategy/architecture-v2/uac-registry-gaps.md), which is a gaps register, not a
      ruling record. Found because the `check_plan_operator_ruling_evidence` gate rejected a citation of it — the gate
      was right, and the missing durable home is the real finding. A ruling whose only copy is a docstring dies with the
      next refactor of that module.
- [ ] [AGENT] P2. **Add a gate asserting every catalogue-emitted config key is read by its engine or its param schema.**
      Both instances of this defect class were found by hand, months apart, by agents looking for something else. The
      check is mechanical — catalogue keys per archetype vs `PARAM_SCHEMA_REGISTRY` ∪ engine `*_param(self.params, …)`
      reads — and it would have caught all 4 dead vol keys and the earlier DeFi ones at commit time.

## Progress Log

- **2026-08-12 (later)** — **All three blocking audits closed.** Together they were the gate on writing the artefacts
  once instead of twice, and the net result is narrower than feared: the catalogue layer has exactly **two** misplaced
  cross-archetype clusters, not an open-ended sprawl, and the custody model needed no design work at all. Three findings
  change what the artefacts may claim: (1) **options coverage cannot be counted in catalogue rows** — 14
  `VOL_TRADING_OPTIONS` rows differ only in an `expression` key nothing reads, so they all resolve to the same ATM
  straddle, and no artefact may imply butterfly/strangle/calendar capability; (2) **`CARRY_BASIS_PERP` and
  `CARRY_STAKED_BASIS` select their universes by different mechanisms** (measured ADV vs hardcoded tuples) with no
  stated reason, and both ship real in the carve-out, so the asymmetry is visible in disclosed code; (3) **wallet
  behaviour must not be described yet** — the binding schema has zero consumers and no client dimension. One
  cross-cutting lesson: **both instances of the catalogue↔engine dead-key defect were found by hand, months apart, by
  agents looking for something else**, which is why a mechanical gate is now a todo rather than another sweep. A
  same-turn doc fix landed in UAC (`wallet_config.py` named the out-of-scope custodian and omitted a real one).
- **2026-08-12** — Authored from the Elysium readiness audit. **Classification rule established before placing
  anything**, so the four overlays land by principle rather than by convenience: archetype iff it reasons about that
  archetype's selection logic, cross-archetype iff it reasons about any book's risk or turnover. Result: rank-buffer is
  archetype-layer; no-trade band, beta-hedge and vol-target are cross-archetype, with vol-target **already duplicated**
  in `TSMOM_BTC_CTA` — which is the concrete argument for the rule. Established that the capability manifest is a
  restriction GRAPH already consuming `PARAM_SCHEMA_REGISTRY`, so rulings 3, 4 and 5 all converge on widening it rather
  than adding a surface. Split from the Elysium plan at 977/1000 lines against its hard cap.

## Session handoff 2026-08-12 (moved from the Elysium plan at its line cap)

Five plans now carry this programme. **This plan is at its 1000-line hard cap** — anything substantial from the
remaining audits needs its own file or a trim of what is already flipped here. Know that before it forces a decision
mid-audit.

**NOT DONE — blocked on nobody, pick it up.** The three audits: **54-archetype sweep** for misplaced cross-archetype
logic (rule validated on 6 of 60) · **instrument-axis selection** (expiries/strikes/tenors — gates any options claim) ·
**instance→wallet binding** (H.3 keying; established as UNKNOWN, not absent). Then **artifact regeneration** (all 3,
post-plan reality, §04 reframe). Also: the expansion plan (**gates the repo send**), the carve-out build (`depends_on`
expansion — committed to, not optional), the `check_reference_paths` gate fixes, and ADV `as_of_date` manifest stamping
— until which **PIN `DYNAMIC_CARRY_UNIVERSE_AS_OF_DATE` on any run that must reproduce.**

**CANNOT BE DONE YET.** Solana LST carry needs the § A economics answer first, then an operator ruling on the perp
venue.

**OPERATOR-OWNED — do not start.** Risk-threshold ratification (the deep dive discloses them as placeholders) · SLA
reissue to make 30 days binding (client's copy still says 60 under a prevailing-provisions clause) · repository
disclosure review incl. git history · the Jupiter perps decision (codex requires an explicit new ruling).

**Recommended next: the three audits, in that order.** They are the only things between here and an artifact pass
writable once instead of twice, and the first two are pure measurement with no decisions attached.

## Lessons from 2026-08-12 — read before repeating the work

**The measurement lessons were MIGRATED to codex** — they are workspace-wide, not Elysium-specific, and a plan archives:
[measurement-claims-discipline](/codex/12-agent-workflow/measurement-claims-discipline.md) § "The absence-from-one-probe
failure". Five instances in one session, the discharges, and the corollary that over-stating an error's scope is its own
defect. **Read that before repeating any audit here.** Headline: for anything with a registry, ask the registry.

**Corrections to my own claims — the wrong version must not survive.** Rail enum has **5** members
(`transfer_types.TransferType`), not 3: I dropped `CUSTODY_TRANSFER` and `BRIDGE`, the two most relevant, then
"corrected" it against a different 7-member enum. **Four** transfer-type enums exist; codex documents the 5-member one
correctly. "An instance is one coin on one venue" is false — only **2 of 60** archetypes hold set-valued roles. Carry
has **7** archetypes, not 6, the miss being `CARRY_FUNDING_DISPERSION` — the count was wrong _because_ the capability
was unknown. "Liquidity provision" is real (`DEFI_LP_CONCENTRATED`/`_POOL`/`_VAULT`), **misfiled as a family**, not
invented.

**Invariants.** The factory fails **loudly** (`KeyError`) for unregistered archetypes, so the 28 unreachable ones are
dead-but-safe — that is what makes H.12 disclosure rather than correctness. `safe-doc-push` **exit 13 has a
false-positive mode** (fires when content already landed in a prior push); its remedy is stash surgery, so verify at
origin before touching a stash. And piping a gate through `tail`/`grep` **discards its exit code** — redirect to a file
and capture `$?` alone.

**Rejected, so they are not re-walked:** narrowing `StrategyArchetype` for the carve-out (the full enum as stubs IS the
disclosure design); `AtomicInstruction`/`CompensationPolicy` for multi-hop transfers (trade-leg compensation semantics
are wrong for a half-moved custody balance); keying `VENUE_WALLET_CAPABILITIES` by `(venue, client_id)` (mixes venue
physics with client policy); a third routing-config surface (adds an SSOT, the original complaint).
