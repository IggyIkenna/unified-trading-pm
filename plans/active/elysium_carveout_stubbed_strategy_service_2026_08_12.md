---
doc_type: plan
title: >-
  Elysium full carve-out — a partly stubbed strategy-service where the orchestration is real and everything beneath it
  is not
summary: >-
  Specification for the full carve-out, which is a POST-EXPANSION task and must not start before the strategy-service
  expansion lands. The organising principle, per operator ruling 2026-08-12: the substantive deliverable is the
  ORCHESTRATION that decides, for the client's strategy types, what can be done — the decision layer and the
  instructions it emits are real, and everything beneath the strategy-decision boundary is static, mock or inert. The
  ten typed interfaces in contracts-platform are KEPT as the disclosed contract with static implementations behind them
  (operator confirmed), so the seam already documented in carveout-engineering.html §04 stands and needs reframing
  rather than rewriting. Withheld as IP: the universe registries and general resolution functions behind UAC, the
  multi-step capital-movement reconciliation across Copper/Ceffu/venues, the execution adapters and algorithms, and the
  capability-wizard restriction graph. All carved artefacts are NEW repositories — no production code is removed or
  stubbed.
status: draft
nature: process
asset_group: [defi]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [elysium, carve-out, disclosure, stubs, commercial-model, capability-wizard]
related:
  [
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
    /codex/14-customer-journeys/commercial-model/carveout-engineering.html,
    /codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md,
    /codex/04-architecture/transfer-architecture.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: client_isolation_and_governance_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role:
drift_direction: none
depends_on: [strategy_service_expansion_overlays_config_and_wizard_2026_08_12]
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12. Operator rulings — UAC cannot be in the carve-out in final form, so its functions
  return statically what the configured Elysium strategies need; the client does not need the post-decision-layer
  dynamics (multi-step capital movement, execution adapters and algorithms); the reconciliation smarts across
  Copper/Ceffu/venues are IP; the ten typed interfaces are KEPT as the disclosed contract with static implementations
  behind them; the substantive deliverable is the orchestration that decides for their strategy types what can be done;
  all of it is NEW repositories with production untouched.
---

# Full carve-out — stubbed beneath the decision layer

> **THIS IS HAPPENING** (operator, 2026-08-12): _"we'll show them the carve-out code. That's happening anyway, so that's
> got to be part of the plan."_ It is a commitment, not a contingency. `status: draft` and `depends_on` the expansion
> plan reflect **sequencing only** — the two real archetypes (§A2, narrowed 2026-08-16) must be carved from
> post-expansion behaviour, or their
> static implementations freeze the wrong reality and need redoing. Flip to `active` when the expansion lands.

> **All carved artefacts are NEW repositories.** No production code is removed, stubbed or altered. This plan describes
> what gets _built for transfer_, never a change to the running system.

**The organising principle (operator ruling 2026-08-12).** The carve-out is a **partly stubbed strategy-service**. The
line is the **strategy-decision boundary**:

- **REAL** — the orchestration that decides, for the client's strategy types, what can be done: archetype engines for
  the contracted strategies, the configuration surface that constrains them, the decision logic, and the
  `StrategyInstructionEnvelope` instructions it emits.
- **STATIC, MOCK or INERT** — everything beneath that boundary: how an instruction becomes capital movement, which rail
  it takes, how custody mirroring reconciles, how attribution closes.

The client sees **what is decided and what is emitted**. They do not see **how it is executed or reconciled**.

**Codex SSOTs:** [carveout-engineering.html](/codex/14-customer-journeys/commercial-model/carveout-engineering.html)
§§02–04 · [transfer-architecture](/codex/04-architecture/transfer-architecture.md) ·
[capability-wizard](/codex/09-strategy/architecture-v2/capability-wizard.md) ·
[tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md)

## A. The seam stands — §04 is a REFRAME, not a rewrite

Checked 2026-08-12: `carveout-engineering.html` §04 already states each of the ten interfaces "resolves to a local,
static or mock implementation", that "**no implementation transfers** — contracts, schemas and mocks only; nothing
behind them", and that "static universe and frozen configuration satisfy the universe and config contracts". **That is
already the operator's ruling.** The ten interfaces are KEPT (operator confirmed), so what §04 needs is precision about
_what sits behind each_, not a new structure.

Per-interface resolution to specify. `FeatureProvider` · `PricingService` · `ReferenceDataProvider` · `ExecutionService`
· `PortfolioRiskService` · `TreasuryService` · `ReconciliationService` · `AttributionService` · `ConfigVersionService` ·
`UniverseService`.

- [ ] [AGENT] P1. **Write the per-interface resolution table**: for each of the ten, state exactly what ships in
      Resolution A — a static return, a mock, a documented-inert stub, or a real local reader — and what the client must
      supply or source themselves. **Vagueness here is the whole risk**: a CTO reading §04 will ask what
      `UniverseService` returns, and the honest answer is "the resolved universe for your configured strategies, frozen
      at hand-over" — not the ranking functions that produced it.
- [ ] [AGENT] P1. **Specify `UniverseService` as a frozen resolved universe.** It returns the coin/venue/instrument set
      the configured Elysium strategies resolve to at hand-over date. **Withheld:** `rank_top_n_by_adv`, the ADV corpus
      reader, the candidate pools, and the eligibility filters that produced it. They get the answer, not the resolver.
- [ ] [AGENT] P1. **Specify `ConfigVersionService` as frozen configuration** — the instance configs as configured, with
      the param schema for those archetypes only. **Withheld:** `PARAM_SCHEMA_REGISTRY` for the other archetypes and the
      capability-manifest restriction graph.
- [ ] [AGENT] P1. **Specify `TreasuryService` and `ReconciliationService` as inert with documented extension points.**
      This is where the newest IP sits: the Copper/Ceffu mirrored-custody model, the per-client funding-route graph and
      the persisted multi-hop `TransferRoute` (see
      [transfer-architecture](/codex/04-architecture/transfer-architecture.md) rulings 1–4). `request_transfer()`
      accepts and acknowledges; it does not route.
- [ ] [AGENT] P2. **Specify `ExecutionService` as basic routing only.** The carved package's `execution-basic` and
      `adapters-lite` give order placement against a venue API. **Withheld:** execution algorithms, SOR, the
      venue-capability registry and the transfer rails.
- [x] [AGENT] P2. ✅ **Specify `PortfolioRiskService` local guard-rails vs withheld platform risk.** `risk-guards-local`
      gives the local circuit breakers the strategy needs to be safe standalone; cross-client portfolio risk and
      governance stay platform-side.
      **RULED 2026-08-16 (operator) — ship OUR LIVE VALUES, not conservative defaults.** Applies to drawdown control,
      max positions, delta-neutrality bounds and least-increasing-leverage hedge selection. Rationale: maximum
      fidelity — what they run is what we run, so behaviour matches the track record the deliverable is sold on.
      **This overrides the recommendation made at decision time** (conservative-defaults-overridable, on fail-safe
      and non-disclosure-of-risk-appetite grounds); recorded so the trade-off is not silently re-litigated later.
      **Two consequences that follow and must be handled, not assumed away**: (a) shipping live values DISCLOSES our
      risk appetite and position sizing — that is now an accepted disclosure, so it must not be treated as
      confidential elsewhere in the carve-out; (b) a limit tuned to our balance sheet may be wrong for theirs, so
      every shipped limit must remain config-overridable and the delivery docs must say plainly that these are OUR
      operating values, not a recommendation calibrated to their capital.

## A2. Archetype scope — TWO real, the rest shipped as stubs (operator ruling 2026-08-12, narrowed 2026-08-16)

**Only the two contracted archetypes carry real implementations.** `CARRY_FUNDING_DISPERSION` was originally
included as a voluntary breadth-demonstration ("shown deliberately so they can see how an expanded strategy
correlates against the contracted pair") — **operator ruled 2026-08-16: remove it.** Not contractually required
(Annex A scopes to the BTC/ETH/SOL basis strategy only — see §A3), and out of step with this session's direction
toward narrower disclosure generally.

| Archetype                  | In the carve-out                                                       | Why                                                                  |
| --------------------------- | -------------------------------------------------------------------------| ----------------------------------------------------------------------|
| `CARRY_BASIS_PERP`         | **REAL**                                                               | Contracted                                                           |
| `CARRY_STAKED_BASIS`       | **REAL**                                                               | Contracted                                                           |
| `CARRY_FUNDING_DISPERSION` | **STUB** (removed from REAL 2026-08-16, was previously REAL)           | Not contracted — voluntary-breadth inclusion, ruled out              |
| **All other enum members** | **STUB** — signature, docstring, archetype identity; no decision logic | The **universe of archetypes is disclosed; the mechanisms are not**  |

**This is a disclosure design, not a shortcut.** Shipping the full enum as stubs shows the client the real breadth of
the platform — every family, every archetype name — while the alpha logic transfers for two only. Breadth is visible;
mechanism is withheld. It also happens to align with the existing estate: **28 of 60 archetypes are already unreachable
in production** (Elysium plan § H.12), so stubbing the remainder is continuing a pattern rather than inventing one.

- [ ] [AGENT] P1. **Define one stub shape and apply it uniformly.** Each stub carries its archetype identity, family,
      param schema reference and docstring, and raises or returns inert on tick. **It must be unmistakably a stub** — a
      stub that looks like a thin implementation invites a bug report or, worse, an assumption that the strategy is
      runnable.
- [ ] [AGENT] P1. **Stub the internal code the non-carved archetypes depend on**, not just the engines: their
      target-universe builders, rank allocators, catalogue entries and archetype-specific helpers. The import closure
      must still resolve — `contracts-platform` is derived as an import closure over the tier graph, so a dangling
      reference breaks the package build rather than degrading gracefully.
- [ ] [AGENT] P2. **Keep the enum whole.** Do NOT narrow `StrategyArchetype` to the three — the full enum with stubs is
      the point. This supersedes the earlier instinct in § B to narrow it; the correct fix for "don't hit `KeyError` on
      an advertised name" is a stub that fails informatively, saying this archetype is not part of this package.
- [x] [AGENT] P2. ✅ **RULED 2026-08-16: collateral/margin eligibility for the two carry archetypes freezes, same
      treatment as `UniverseService`.** A cross-repo extraction audit traced this precisely (the audit's cited source
      doc, strategy-service's `EXTRACTION_AUDIT.md`, sat unpushed in the author's local working tree at the time an
      earlier same-day check correctly found it missing from the repo — now landed at `strategy-service@efa1525813`;
      the dependent claim also held up on independent spot-check regardless: `staked_basis.py:119-121,361-369` does
      call `accepted_perp_collateral`/`get_collateral_haircut`/`venue_accepts_collateral`): `staked_basis.py`'s
      per-tick structure derivation (`LST_AS_MARGIN` vs `USDC_MARGIN_BUFFERED`) calls UAC's live
      `accepted_perp_collateral`/`get_collateral_haircut`/`venue_accepts_collateral` — distinct from and in addition to
      `UniverseService`'s own already-frozen ADV/eligibility filtering at line 101-103 above. Freezing this too (ship the
      resolved collateral/haircut answer for the configured venues, not the resolver) means the carved package never
      needs UAC's live registry code (`unified_api_contracts.registry`) at runtime at all — only the `StrategyArchetype`
      enum and schema types, which ship whole regardless (small, and disclosure is the point). Without this ruling, UAC's
      eager `internal`/`registry` `__init__.py` graph (1,064 files/~240k lines, DeFi content interleaved with
      CeFi/TradFi/sports in flat enums/dicts — see the audit) would have been pulled in wholesale just to satisfy this
      one call, defeating the IP-withholding intent. **Still open, not yet done:** actually specify and build the frozen
      collateral/haircut substitution and confirm it satisfies all three engines' decision logic bit-for-bit against a
      known input — this ruling settles the *design direction*, not the implementation.

## A3. Venue & asset scope — CEX-only, three assets, one staking route (operator ruling 2026-08-16)

Per operator ruling and Annex A of the signed Consulting Agreement (`Elysium_x_IkeNova_contract.pdf`, executed 3
March 2025, Doc ID `5f6491d203e91ea6c5b836c722dba886e0d1565b`): the contracted "CeFi & DeFi basis trading strategy"
covers exactly:

- **Assets**: BTC, ETH, SOL (+ their perpetuals/derivatives) — matches Annex A verbatim.
- **Venues — CEX ONLY, exactly four**: Bybit, Deribit, Binance, OKX. Used for both spot purchase and perp
  shorting, across all three assets. No other CEX venues. **No DEX/on-chain perp venues at all** — Hyperliquid and
  Aster (the two live DEX-shaped perp venues in production today) are explicitly named OUT of scope; neither is in
  the contracted universe.
- **Staking — ETH only, via Lido (stETH)**. No Marinade, no SOL staking, no other LST protocol. "DeFi" in Annex
  A's "CeFi & DeFi" phrasing resolves to this one staking leg, not to on-chain perp trading.
- **Explicitly excluded as a result**: all Solana DeFi/DEX work (Jupiter perps, Kamino borrow, Marinade — see the
  correction in `solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md`), Hyperliquid, Aster, and any
  other on-chain venue or protocol.

**Effect on §A2's archetype table**: `CARRY_BASIS_PERP` and `CARRY_STAKED_BASIS` cover this scope directly, and
`CARRY_STAKED_BASIS` is largely already live for it — `catalog_staked_basis.py` shows `lido-deribit` (7.5%
haircut) and `lido-bybit` (10% haircut) as verified `LST_AS_MARGIN` slots today; Binance and OKX need no new
LST-margin integration, they resolve via the engine's existing `USDC_MARGIN_BUFFERED` fallback structure.
**`CARRY_FUNDING_DISPERSION` — RULED OUT 2026-08-16.** It was this plan's own voluntary-breadth choice ("shown
deliberately so they can see how an expanded strategy correlates against the contracted pair"), not contractually
required by this scope (Annex A covers the BTC/ETH/SOL basis strategy only). Operator confirmed: remove it. §A2's
table updated in the same edit — it now ships as a stub like every other non-contracted archetype.

**Effect on the frozen-collateral-eligibility ruling above**: this sharply bounds it. The substitution only needs
to cover stETH haircuts/acceptance on 4 named CEX venues, not the fleet-wide `VENUE_COLLATERAL_MATRIX` — a much
smaller, mostly-already-measured surface than originally scoped.

## A4. Data scope — Tardis excluded entirely; DeFi data limited to Lido rate + gas fees (operator ruling 2026-08-16)

**Tardis-sourced market data is not part of the carve-out at all.** Per operator: the Tardis subscription predates
this contract, was never billed to the client, and is the firm's own asset. **The client receives zero historical
Tardis data** — for the CEX market data the two real archetypes need (Bybit/Deribit/Binance/OKX, §A3), the client
sources their own.

**DeFi-specific data — traced against `staked_basis.py`'s actual feature reads**, since Annex A's Phase One
deliverable ("historical performance, risk & volatility, and liquidity of basis trading strategy across major
trading venues **and staking/re-staking programs**") plausibly obligates some unprocessed DeFi data. Given the
narrowed §A3 scope (Lido staking only, no DeFi-side leverage), the archetype's real DeFi-sourced inputs are:

- `staking_apy_bps` — Lido's stETH staking APY.
- `lst_native_rate` / `lst_native_rate_ts` — Lido's stETH:ETH conversion rate.
- `fees_apy_bps` (optional) — its own docstring folds in "funding, swap, **gas**"; the gas component is the
  on-chain execution-cost data.

Matches the operator's stated scope exactly: Lido rate data and gas fees, nothing else.

- [x] [AGENT] P2. ✅ **RESOLVED 2026-08-16 — both trace to genuine on-chain DeFi data, but neither belongs in this
      scope.** `health_factor` is produced by `features-service/features_service/onchain/engine/orchestrator.py`'s
      `_process_health_factor()`, which polls **Aave V3's `getUserAccountData()`** directly — a real on-chain
      lending-protocol borrowing-health read, not CEX-reported. But it exists to gate **DeFi-native
      borrowing/leverage** ("kill gate when LST posted as perp margin" against an Aave position) — and the
      operator has ruled **no DeFi-side leverage is taken in these strategy versions** (§A3/§A4 above). So it's
      on-chain DeFi data, but for a capability this scope doesn't use — **excluded from the data-scope list, not
      owed.** (Also currently unpopulated in this corpus — paper-run substitutes a hardcoded safe constant rather
      than a real per-wallet figure, per `strategy_service/cli/handlers/paper_run_handler.py:26-28,343`.)
      `usdc_idle_yield_apy_bps` similarly traces to genuine on-chain data — Aave V3/Compound V3/Spark stablecoin
      **supply** APY (lending, not borrowing — no leverage involved) via
      `strategy_service/engine/core/canonical_lending_supply_apy_provider.py`. Unlike `health_factor`, supplying
      idle USDC for yield doesn't require leverage, so this one COULD be in scope if the two real archetypes
      actually use it live — but its only confirmed wiring today is paper-run/backtest CLI tooling
      (`paper_run_handler.py`, `paper_universe.py`), not a proven live-trading path. **Not added to the data-scope
      list above** until its live-path status is confirmed; flagged here so it isn't silently dropped if that
      changes.

## A5. Pre-carve-out completion bar (operator ruling 2026-08-16)

Two prerequisites before any carve-out repo is built or sent, beyond the code/venue/data scope rulings above —
these gate readiness to carve, not the carve-out's own content.

- [ ] [OPERATOR] P0. **Full E2E connector + data completeness for the two real archetypes, on the exact §A3
      scope, before anything ships.** Every connector in the chain — instruments-service through execution-service
      — must be built and verified for `CARRY_BASIS_PERP` and `CARRY_STAKED_BASIS` across all three modes: batch,
      live, and paper (paper including proxy/internal-match and testnet where possible). Underlying market data for
      the scoped venues (Bybit, Deribit, Binance, OKX, Lido — §A3/§A4) must be captured to 100% completion, its
      availability verified, and its data types reconciled. This is stronger than "does the code exist" — it's
      "does the pipeline actually run end-to-end and does the data back it up," per this workspace's own
      data-pipeline-correctness standard
      ([data-pipeline-correctness-hard-rule](/codex/02-data/data-pipeline-correctness-hard-rule.md)). Directly
      extends the code-completion bar already gating the repository send in
      [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md)
      §D, now scoped precisely to the two archetypes and four venues this plan actually covers.
> **FORKED OUT 2026-08-16.** The lazy-loading refactor now has its own plan —
> [`/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`](/plans/active/lazy_scoped_loading_refactor_2026_08_16.md)
> — under the umbrella
> [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md),
> which owns track (a): getting the system to full capability in a shape that makes the carve-out doable. Forked
> because the biggest layer (UAC's eager `__init__` graph) has fleet-wide blast radius and would not be found by anyone
> scanning plan titles for it. **The prerequisite below still stands and still gates this plan** — it is now satisfied
> by that child rather than by work tracked here.

- [ ] [OPERATOR] P0. **Land the lazy-loading (factory) refactor before or alongside the carve-out, not as an
      independent question.** Rationale: so that updating the carve-out later doesn't mean re-deriving a frozen
      snapshot against a moving, eagerly-coupled main-system target — if `factory.py`'s archetype registration is
      already lazy/scoped by the time the carve-out exists, keeping it in sync with main-system changes stays
      cheap. **Tracked as a real, already-existing plan**:
      [lazy_scoped_loading_refactor_2026_08_16](/plans/active/lazy_scoped_loading_refactor_2026_08_16.md), which
      independently mirrors this same finding (its own summary states the identical scope conclusion — a lazy
      `factory.py` alone doesn't solve it, UAC needs an equivalent refactor too, fleet-wide blast radius, SIT needs
      no changes). **Scope note, so this isn't treated as free**: this refactor doesn't stop at strategy-service —
      the two real archetypes' live collateral calls mean a genuinely lazy service also needs an equivalent
      UAC-side refactor (`unified_api_contracts`'s `internal`/`registry` `__init__.py` eagerly loads ~240k lines
      regardless), which has fleet-wide blast radius, not a local one. Both approaches are now wanted together, not
      compared as alternatives — this raises total pre-ship scope above what §A2's "well-bounded" note assumed
      when it was written, and is worth the operator seeing stated plainly rather than absorbed silently.
- [x] [AGENT] P2. ✅ **`EXTRACTION_AUDIT.md` citations corrected twice in one day — now landed, cite the commit.**
      An earlier same-day pass correctly found the file missing from strategy-service's repo (it existed only in
      the citing author's local working tree, blocked behind an unrelated dirty dependency) and rewrote all 4
      occurrences (§A2 ruling ~line 151, this prerequisite, wizard-correction ~line 306, Progress Log ~line 367) to
      say so — good, verified work. It has since landed at `strategy-service@efa1525813` once the blocker cleared.
      Each occurrence updated again in the same edit to cite the landed commit rather than either "exists" or
      "doesn't exist" as an unqualified claim. Each dependent claim was spot-checked against the actual code before
      rewriting its citation both times, not just
      stripped: `staked_basis.py:119-121,361-369` does call `accepted_perp_collateral`/`get_collateral_haircut`/
      `venue_accepts_collateral` (§A2 claim confirmed); `restriction_profile_router.py` is confirmed exactly 153
      lines (wizard-correction claim confirmed). Both held up independently of the missing source doc.

## B. What the expansion adds, and therefore what the carve-out must account for

The expansion plan changes what "real" means at the decision boundary, so the carve-out inherits it.

### RESOLVED — the four overlays CARVE, as `risk-guards-local` (2026-08-12)

Derived from the operator's own stated line rather than as a new decision, and reversible if they disagree:

1. **The boundary is the strategy-decision layer.** Risk overlays are **pre-decision** — they size and veto the decision
   before an instruction is emitted. They are not post-decision execution dynamics, so they fall on the **real** side.
2. **The carved package already includes `risk-guards-local`** ("local safety and test: risk-guards · sim-harness ·
   ops"), and the operator's line on risk is that **cross-client portfolio risk and governance** stay platform-side.
   Vol-target and beta-hedge on a single carved book are **local single-book risk**, not cross-client governance.
3. **§03's acceptance bar requires "runnable".** A strategy with no drawdown control is not runnable in any meaningful
   sense — the research book calls vol-target "the drawdown DIAL". Stubbing it would make the package fail our own bar.

So: rank-buffer carves with the engine; **no-trade band, beta-hedge and vol-target carve as `risk-guards-local`**;
`PortfolioRiskService` remains the stub for **cross-client** portfolio risk and governance, which is a genuinely
different capability rather than the same one withheld.

- [ ] [AGENT] P1. **Implement the carved overlays against the same code as production**, not a reimplementation. If they
      are built once at the book layer per the expansion plan § A, the carve is a package-boundary decision rather than
      new code — which is the whole reason to build them shared. A divergent carved copy would be a second
      implementation to keep in sync, the exact defect the vol-target duplication in `TSMOM_BTC_CTA` already
      demonstrates.
- [ ] [AGENT] P2. **State the distinction in §04's resolution table** so `PortfolioRiskService` being a stub is not read
      as "no risk management" — local guard-rails and overlays ship; cross-client portfolio governance does not.
- [x] [AGENT] P2. ✅ **CORRECTED 2026-08-16 — the wizard doesn't live in strategy-service, and its real
      restriction graph isn't wizard-specific.** Per the extraction audit — the cited source doc, strategy-service's
      `EXTRACTION_AUDIT.md`, now landed at `strategy-service@efa1525813` (it existed only locally, blocked behind an
      unrelated dirty dependency, at the time an earlier same-day check correctly found it missing);
      the dependent claim held up on spot-check regardless (`restriction_profile_router.py` confirmed 153 lines):
      the interactive wizard's UI is in `unified-trading-system-ui`, its manifest generator in `unified-trading-pm`,
      and the real restriction GRAPH (`capability_manifest.py`) in UAC. The only wizard-adjacent code in
      strategy-service is a 153-line router (`api/restriction_profile_router.py`) resolving persona/demo-account UI
      tiles — not an archetype-eligibility engine. Deleting or no-op-stubbing that router is trivial; the actual
      sensitive logic (`capability_manifest.py`, `target_universe/` catalogs) is already covered by the "3 real
      archetypes, rest stubbed" mechanism above and the frozen-eligibility ruling in §A2, not by a separate wizard
      carve step. Same correction made in `strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` §C.
- [ ] [AGENT] P2. **Account for archetype reachability.** Only the contracted archetypes carve. The other 50-odd enum
      members must not appear as dead names — either the carved enum is narrowed to what ships, or the unreachable ones
      are visibly marked, so the client's engineer does not hit `KeyError` on a name the code advertises.

## C. Artefact alignment — reality, present tense, no roadmap voice

Operator instruction: the artefacts are the **union of code and codex**, describe **post-plan reality in the present
tense**, carry **no "will be"**, and are **not salesy**. State what the full picture contains and what a carve-out
stubs; the client draws their own conclusion about the middle.

**The framing target, stated precisely because it is easy to get wrong** (operator, 2026-08-12): the artefact should
leave the client understanding that _"it probably doesn't make sense to take the carve-out because of the reduced
implementations"_ — **and it must reach that conclusion through completeness, not advocacy.** The distinction that keeps
it honest:

- **Do** state, per capability, what the hosted form runs and what the carved form resolves to. Ten interfaces resolving
  to static returns and inert stubs, three archetypes real out of the full enum, no execution algorithms, no transfer
  routing — laid out plainly, that speaks for itself.
- **Do NOT** write a recommendation, a comparison verdict, a "you would be giving up…", or any sentence whose subject is
  the client's decision. **The moment we argue for a conclusion, a reader starts discounting the facts** — and rev 1.0
  of `carveout-engineering.html` was rejected for exactly that register.

The reduced implementation is a fact about the package. Let the fact do the work.

- [ ] [AGENT] P1. **Reframe `carveout-engineering.html` §04** with the per-interface resolution table from § A. Keep the
      seam, the ship-form taxonomy and the reversibility property — they are accurate and they are what make the
      document useful to a CTO.
- [ ] [AGENT] P1. **Ensure the full-picture surface is represented across all three artefacts** so the client can see
      what the hosted form contains: the mirrored-custody routing, the funding-route graph, the capability wizard and
      restriction graph, the ADV-ranked dynamic universe, the rank-allocator weighting layer, the book-level overlays,
      venue and instrument capabilities. **Woven into the relevant sections, never stacked in one "what you don't get"
      block** — a loss-list invites argument, a described capability invites integration planning. That framing already
      fixed rev 1.0 of this document.
- [ ] [AGENT] P2. **No performance figure anywhere until the overlays land.** The research Sharpe belongs to the
      8-overlay book; production runs 2 (Elysium plan § H.16). This is the one hard prohibition on the artefacts.
- [ ] [AGENT] P2. **Cross-check the five older Elysium docs** in `commercial-model/` that this session never reviewed —
      `ODUM_Elysium_Phase2_Update_2026-07-24.html`, `elysium-remaining-work-appendix-2026-07-24.md`,
      `elysium-delay-letter-2026-07-20.md`, `elysium-account-trajectory-2026-05-14.md`,
      `elysium-managed-sla-2026-05-14.md` — against everything established since. Any of them may contradict the
      two-custodian model, the archetype counts or the carve-out scope.

## Progress Log

- **2026-08-12** — Authored on operator instruction, `status: draft` and `depends_on` the expansion plan because
  assembling a carve-out from pre-expansion behaviour would freeze the wrong reality into the static implementations.
  **Useful finding while specifying it: §04 does not need rewriting.** It already states that the ten interfaces resolve
  to local/static/mock implementations and that no implementation transfers — the operator's ruling was already the
  documented design, so the work is precision about what sits behind each interface, not a new structure. Operator
  confirmed the ten interfaces are KEPT as the disclosed contract. Recorded the strategy-decision boundary as the
  organising line: the orchestration that decides what can be done for the client's strategy types is real; everything
  beneath it is static, mock or inert. Flagged the book-level-overlay resolution as the most consequential open
  decision, since it determines whether the carved strategy has a working risk profile or an un-overlaid one.
- **2026-08-16** — Interactive session ran a full cross-repo extraction audit ahead of a docs-cleanup pass on
  strategy-service (writeup: strategy-service's `EXTRACTION_AUDIT.md`, internal-only — landed later the same day
  at `strategy-service@efa1525813`, after sitting blocked in the author's local working tree behind an unrelated
  dirty dependency; a same-day check correctly flagged it missing before the blocker cleared, and the claims below
  held up on independent spot-check regardless). Measured,
  not assumed: capability wizard is NOT in strategy-service and the plan's "backing restriction graph
  is exactly the reconciliation IP withheld" framing (§B above) overstates a 153-line UI feature-gate router that calls
  no venue/collateral registry — trivial to stub. SIT has zero coupling to `factory.py`'s registry either way.
  Deployment-api/-service/-ui and the PM repo have zero code coupling — pure CI/tooling a client replaces with their
  own. Instruments-service/MTDS/features-service/ml-service have zero *code* coupling (archetypes receive `features`/
  `mid_price` as plain parameters from an upstream pipeline, never call these services); `MLPrediction` is imported but
  literally unused (`del predictions`) by all three real archetypes. **The one real blocker found: UAC's eager
  `internal`/`registry` `__init__.py` graph (1,064 files/~240k lines) is interleaved DeFi/CeFi/TradFi/sports content
  with no clean-slice import path** — worse than this plan's §A2 todo anticipated, since it affects not just the
  universe resolver but the two carry archetypes' live collateral/margin calls too. Operator ruled 2026-08-16: freeze
  that too (see the §A2 todo above) — closes the open design question; UTL has the identical mechanical eager-import
  flaw but is judged low-stakes (generic infra, no real IP) and ships whole rather than being fixed. execution-service's
  proposed basic/algo/transfer split maps onto real ABC boundaries, with one added cost (SOR shares AMM/gas modules
  with basic DEX swaps) and an already-established lazy-registration pattern to reuse from elsewhere in that repo; zero
  execution-service blast radius from strategy-service's own factory-refactor alternative (not this plan's approach,
  but was scoped for comparison). Net effect: this plan's stub-carve-out approach is now well-bounded and the
  higher-confidence path — the alternative (refactor strategy-service's `factory.py` for lazy registration in
  production) turned out to require an equivalent-or-larger UAC refactor with fleet-wide blast radius, for a benefit
  mostly orthogonal to external disclosure.
