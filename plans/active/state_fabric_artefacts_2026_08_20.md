---
doc_type: plan
title: State fabric — client artefacts (two new documents, seven existing, and a readiness ledger to source them from)
summary: >-
  Owns R27 and the artefact surface. Two new client-facing documents (execution hot/warm/cold plus reproducibility;
  recoverability plus risk), the seven existing HTMLs updated against the 27 rulings of 2026-08-20, the shard-level
  coverage drilldown the walkthrough does not currently have, and — the piece that stops all of it rotting — a
  persisted readiness ledger the artefacts RENDER FROM instead of transcribing by hand.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [state-fabric, client-artefacts, readiness-ledger, coverage, disclosure]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/audit/results/state_fabric_reconciliation_dispatch_2026_08_20.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12
locked_by:
locked_since:
depends_on: []
supersedes:
superseded_by:
source:
context_scope:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/epics/system_readiness_master.md,
    /codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
  ]
---

# State fabric — client artefacts

> **Disclosure posture (operator ruling R27, 2026-08-20)**: these are **client-facing**, in
> `codex/14-customer-journeys/commercial-model/`, with gaps framed as **roadmap** rather than as defects — and with
> **factually honest current status**. Roadmap framing sequences the work; it never asserts a capability that does not
> exist. A gap reads as "planned, not yet built", never as an implied capability.
>
> **Standing constraints, unchanged**: no commercial, budget, funding, valuation, cost or ARR figures in any
> client-facing material; never name ClearLoop; nothing from an internal plan reaches a client artefact without
> operator approval.

## The two problems this plan solves

**1. The artefacts do not cover what they are believed to cover.** Measured 2026-08-20 against
`platform-external-api-walkthrough.html` (777KB): it has the right sections — "The coverage model", "Coverage by asset
group", "Shard schemas", "Readiness: batch, paper, live", "Measured versus projected" — but contains **exactly 8
distinct percentage values**, all asset-group rollups (48.73 overall; sports 99.26, prediction 92.81, tradfi 86.96,
cefi 45.57, defi 40.94). Zero occurrences of `capture_status`, `expected_unattempted`, `per day`, `day-by-day`,
`first_date`, `last_date` or `days covered`. It is a **rollup, not a drilldown** — there is no shard-level view and no
per-day coverage anywhere.

**2. The numbers are hand-carried, which is why they rot.** Four skills DERIVE readiness and coverage on demand —
`readiness-state-dump` (with execution instruction-path, execution order-capability, MTDS live-feed and
strategy-position probes), `honest-coverage-dump` (`dump_coverage.py`, `shard_universe.py`),
`archetype-code-completeness`, `gate-evaluation`. **No persisted ledger was found** (searched `readiness_ledger`,
`readiness_state.json`, `readiness_snapshot`, `shard_ledger` — four patterns, so absence is not proof). Derivation
without a ledger means no history, no single artefact to render from, and every update re-runs a skill and transcribes
numbers into HTML by hand. That is exactly how these artefacts went stale before.

Under R17 the readiness state should be a **published, versioned, dated generation** that the audits AND the artefacts
both read — declare once, consume many.

## Todos

### The readiness ledger (do this first — it sources everything below)

- [ ] [BACKEND] P0. **Persist a versioned readiness + coverage ledger** — one dated, content-hashed generation
      emitted by the existing skills rather than a fifth derivation. Must carry: per-shard coverage to the smallest
      shard granularity with per-day resolution, per-venue batch/paper/live readiness, per-archetype code-readiness,
      and the credentials leg. History retained, so improvement is visible.
- [ ] [BACKEND] P0. **Bind the artefacts to the ledger** — HTML renders from the generation, never from transcribed
      numbers. A figure in a client artefact must be traceable to a ledger generation id and date.
- [ ] [REVIEW] P1. **Confirm no fifth derivation was created.** The four existing skills stay authoritative; the
      ledger is their published output. Re-deriving coverage inside the renderer would repeat the exact duplication
      this plan exists to remove.

### The two new documents

- [ ] [DOC] P0. **Execution deep dive** — the whole execution infrastructure across hot / warm / cold path, plus
      reproducibility. Must cover the two orthogonal axes (semantic profile x performance tier), why `hot` on
      `block_ledger` means winning the block rather than microseconds, the order-state diff, output suppression, and
      the batch/paper/live symmetry. Full API contracts, schemas, code snippets and worked examples — spec'd in enough
      detail to be **audited as a design**, not summarised.
- [ ] [DOC] P0. **Recoverability and risk** — what happens when things go stale, when we start cold without the data
      we need, when we must replay. Cover the finality ladder and retraction, the kill/action-mask unification and its
      three states (`PERMITTED` / `SUPPRESSED` / `KILLED`), recovery-quality levels, warm-up and bootstrap types, and
      the honest current state: order and position durability, the timestamp collision, the dormant epsilon=0 proof.
      Same depth requirement — contracts, schemas, examples.
- [ ] [DOC] P1. **State planned-vs-current explicitly in both**, per item, so the roadmap framing never obscures what
      exists today. A reader must be able to tell shipped from planned without cross-referencing anything.

### The existing seven

- [x] ✅ [DOC] P0. **Update all seven existing HTMLs against the 27 rulings** — five (`platform-api-reference`,
      `platform-architecture`, `platform-external-api-walkthrough`, `strategy-service-deep-dive`,
      `strategy-service-walkthrough`) structure-passed 2026-08-20, `unified-trading-pm@2340bd96b5` +
      `@4ed7be87d0` + `@c1c0e7e81c`. Verified at origin, not just locally, after two separate content-loss incidents
      on the shared checkout — see
      [/plans/active/issues/walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md](/plans/active/issues/walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md).
      `carveout-engineering` and `ODUM_Elysium_Phase2_Update` still not touched — remaining P0.
- [x] ✅ [DOC] P0. **Walkthrough expanded with sections 28-30** — strategy families (9 real `StrategyFamily` values as
      a buy-side pitch over the section 09 registry), the instrument universe (organized by tradable shape:
      spot/perpetual/future/option/swap/ETF, real `InstrumentType` tokens), and execution algorithms in depth (9 real
      `algo_library` modules with their real aggressiveness/slicing parameters, closing on `base_algorithm.py`'s
      `ExecutionAlgorithm` interface). Recovered from a scratchpad snapshot after the agent's direct commit was lost
      to the same checkout instability — see the issue doc above.
- [ ] [DOC] P0. **Add the shard-level coverage drilldown to the walkthrough** — smallest shard granularity, % across
      days, no exceptions, sourced from the ledger. Still the measured gap; sections 28-30 did not touch this.
- [ ] [DOC] P1. **Correct anything the rulings invalidate** — in particular any text implying the Taylor factor form
      is universal (it is the continuous-quote kernel), or that continuous-quote implies the fast path (profile and
      tier are orthogonal).

### The coverage-by-asset-group reframe (operator ruling 2026-08-20)

**The framing gap**: the coverage tree does not make clear that historical and live are the SAME capability question
— operator's words: "if we've got historical, we can get it for live... we're just playing the blocks." Batch vs live
is a `pipeline_mode` transport choice per venue, not two different products. The tree currently reads as if only
batch/historical exists.

**Per-asset-group labeling rules, operator-set 2026-08-20** — apply these once §31/32 land, not before:

- **DeFi `unverified`**: label **"coming soon"** wherever a real adapter exists and a live measurement shows genuine
  capture activity or a plausible smoke-test path (see the T-investigation findings below for exactly which venues
  qualify) — never leave a plausible-capability venue reading as a bare, unexplained "unverified."
- **TradFi `not-ready`/missing data types**: label **"on request"** for tick-level types (10-level book depth, trades,
  BBO) and candle data, **explicitly CME/GLBX.MDP3-scoped** — the Databento billing block is confirmed real
  (`account_delinquent_invoice`, reconfirmed 2026-08-17) but is NOT a blanket TradFi outage. ICE, NASDAQ/NYSE, FX and
  CFE are confirmed unaffected and actively capturing in the same evidence trail — those get honest measured labels,
  not a billing excuse.
- **Unattributed bucket**: relabel from bare "Unattributed" to **"DeFi — pipeline phase, not yet live"** — see the T2
  investigation below; all 24 tokens are real, well-formed DeFi venues, none are manifest artifacts.

- [ ] [DOC] P0. **Write the historical-implies-live reframe** into §04/§05's opening explanation — one clear
      statement, not scattered caveats, that batch and live read from the same adapter/registry and differ only in
      `pipeline_mode`.
- [ ] [DOC] P0. **Apply the DeFi/TradFi/Unattributed labeling rules above** once §31 (T1 findings) is folded in.

### T1 — why `unverified`/`not-ready`, and the three named venues (investigation complete, live-measured)

**Live-measured** (not just code-read) against the 2026-08-20 coverage manifest via `derive_readiness.py` /
`dump_coverage.py`, read-only. Full report in this plan's Progress Log — condensed findings:

- **Two `unverified` shapes confirmed, plus a third nuance**: (a) venue absent from both `VENUE_DATA_TYPE_CAPABILITIES`
  and the manifest — no row produced at all; (b) venue declared, zero shard cells — "no coverage.json shard cells
  observed." New nuance: shape (b) sometimes compounds with an **upstream instruments-service catalog gap** — IS has
  never enumerated the venue either, one level deeper than "MTDS hasn't captured yet."
- **DERIBIT** — mostly working. Live-measured up to 92% reachable on several cells; `not-ready` is driven by exactly
  two bundle-grain cells (`futures_chain/trades`, `options_chain/trades`). **Recommended label: coming soon.**
- **OKX-FUTURES** — shares its adapter with OKX-SWAP/OKX-SPOT, both already capturing. Already at 82-100% reachable
  on real instrument types; gated by one bundle cell + two shard-enumeration holes on the PERPETUAL leaf.
  **Recommended label: coming soon.**
- **PACIFICA-SOLANA** — pure registry-sync gap. Declared correctly in `DATA_TYPE_CAPABILITY_REGISTRY`
  (`live_capable=True`, code-commented "confirmed live 2026-08-14") but absent from `VENUE_DATA_TYPE_CAPABILITIES`,
  the registry readiness tooling actually reads. **Code fix dispatched 2026-08-20 to a background agent** — status
  pending, check for its completion notification before writing this venue's final doc label.
- **DeFi sample (AAVE/LIDO/MORPHO-ETHEREUM)** — real adapters exist, genuinely zero manifest cells, AND the IS catalog
  has never enumerated these venues either (the compound gap above). **Recommended label: coming soon**, but flag
  that closing it needs an IS catalog/backfill step, not just a registry edit.
- **A second instance of the two-registry-disagreement pattern**, worth its own systemic check (first instance was
  the three chain registries): `VENUE_DATA_TYPE_CAPABILITIES` vs `DATA_TYPE_CAPABILITY_REGISTRY` disagree on Pacifica.

- [ ] [DOC] P0. **Write §31 — data breadth and coverage reframe** using the findings above. Correct two prior
      overclaims from this session's own chat: `gas` is NOT a stored historical data_type (code comment: "ESTIMATE —
      no gas data_type in raw_tick GCS," gas is a live execution-time cost, collected once per chain); `economic_events`
      is NOT macro-economic data — it is a feature-engineering label built from `trades`, not a CPI/FOMC feed. Do not
      claim macro data exists as a feed.
- [ ] [REVIEW] P1. **File a systemic issue for the two-registry-disagreement pattern** (`VENUE_DATA_TYPE_CAPABILITIES`
      vs `DATA_TYPE_CAPABILITY_REGISTRY`) — two independent instances now measured (chain registries, venue-capability
      registries). Check for other venues beyond Pacifica affected the same way.

### T2 — the 24 unattributed tokens (investigation complete)

**Verdict: clean.** All 24 are real, well-formed `PROTOCOL-CHAIN` DeFi venues in genuine `DEFI_VENUE_PHASE == "pipeline"`
status — none are manifest artifacts, duplicates, or malformed tokens. `VENUES_BY_ASSET_GROUP["defi"]` is
**deliberately** live-phase-only by design (a real filter, not a bug); the gap is that the resolver (and the doc's
tree) has no fallback to the broader phase-aware registry that already knows these are DeFi.

- Sub-groupings: 4 tokens have a documented, already-tracked capture blocker (crash-looping/never-scheduled cron); 1
  (`FRAX-ETHEREUM`) has real historical data that stopped 2026-06-21 with no scheduler; 3 Solana DEXes (`METEORA`,
  `LIFINITY`, `PHOENIX`) are blocked behind a cited upstream oracle-adapter-drift issue; 16 are simply pipeline-phase
  awaiting backfill scheduling.
- Minor doc-accuracy note: the walkthrough's existing DeFi-venue-count callout cites `ALCHEMY-ONCHAIN` as the
  cross-chain aggregator; the manifest carries it as bare `ALCHEMY`. Fix in the same pass as the relabel below.

- [ ] [DOC] P1. **Relabel the Unattributed bucket** as "DeFi — pipeline phase, not yet live," with the sub-grouping
      breakdown above (blocked-by-cron / stopped / upstream-blocked / awaiting-backfill), not a bare unexplained list.
      Do NOT add these 24 to `VENUES_BY_ASSET_GROUP["defi"]` itself — that would misrepresent pipeline venues as
      backfilled.
- [ ] [DOC] P2. **Fix the `ALCHEMY-ONCHAIN`/`ALCHEMY` label mismatch** in the same pass.

### T3 — sports deep dive (investigation complete)

**Verdict: the operator's belief was correct, and more precisely than the initial framing.** A genuinely rich sports
pipeline is real, live, and currently capturing production data — fixtures (schedule/outcomes/events/lineups/stats),
injuries, player/team stats, standings, transfer valuations, fixture-linked historical weather (Open-Meteo), and
Understat expected-goals/per-shot xG data for the top 5 European leagues. Real credentialed adapters, confirmed
against actual GCS capture rows.

**Root cause, confirmed structural not a data gap**: the coverage tree walks a bookmaker-**venue**-keyed registry (39
venues) against a 5-token vocabulary (`odds`, `arbitrage_opportunity`, `odds_horizon_bucket`, `trades`,
`trades_inplay`) where almost every venue only populates `odds`. The rich 19-token pipeline (`SPORTS_DATA_TYPE_TO_SOURCE`,
`league_data.py:209`) is keyed by **league**, not venue, and is **deliberately disjoint** by a real 2026-06-29 operator
decision with a test enforcing it (`test_sports_exempt_is_disjoint_from_uac_sports`). A venue-keyed tree generator has
no code path into a league-keyed registry — this document was never built to enumerate the second axis at all.

**Legacy-confusion finding, confirmed nuanced**: a pre-v2 `SPORTS_ARB` strategy is genuinely superseded, and two
standalone repos ("unified-sports-execution-interface," "unified-sports-reference-interface") were eliminated in
March — plausibly the source of the "old brokers" memory. But `ARBITRAGE_SPORTS_DUTCHING` is live and only 9 days
old — arbitrage isn't dead, it was renamed and rebuilt.

**Housekeeping flags**: a stale documentation mirror (`unified-trading-system-ui/context/`, frozen 2026-06-08,
confirmed unused by any live code) risks misleading a future drafting pass — **cleanup dispatched 2026-08-20 to a
background agent**, check for completion. 8 of the 39 sports venues are declared with zero capability entries —
same shape as the Pacifica gap, connects to T1/T2 above.

- [ ] [DOC] P0. **Rebuild the sports section** to surface the real 19-token league-keyed pipeline alongside the
      existing venue-keyed odds tree — fixtures, injuries, weather, understat xG, per the findings above. Do not
      collapse the two registries into one (that would violate the 2026-06-29 disjoint-by-design decision) — show
      both axes in the doc.
- [ ] [REVIEW] P2. **Sports stale-remnant cleanup investigated 2026-08-20, correctly declined.**
      `unified-trading-system-ui/context/` (the frozen 2026-06-08 doc mirror) is unused by any build/runtime
      pipeline (explicitly excluded in `.dockerignore`/`.gcloudignore`/`pyproject.toml`), but three git-tracked docs
      under `docs/core/` actively instruct a reader to open files inside it — an indirect live consumer, correctly
      treated as a stop condition rather than deleted. Needs an operator call: resync `context/` for real, or
      formally deprecate the three pointing docs first, then delete as one coordinated change. Separately: the
      2026-08-03 sports dead-code audit is intact except one **deliberate, well-evidenced reversal** —
      `BetfairAdapter` (MTDS) was restored 8 days after deletion and built into a genuinely live feature
      (factory-wired, canonical fixture-id resolution, matched-volume capture) — not a regression, just makes the
      audit's "dead code" classification stale. `sports/registry.py`'s STATUS note is now slightly out of date
      because of this.
- [ ] [DOC] P1. **Clarify the arbitrage framing** — `ARBITRAGE_SPORTS_DUTCHING` is the live, current archetype; the
      old `SPORTS_ARB`/`SPORTS_ARB_BACK_LAY` naming is superseded and should not appear as if current.

### T4 — prediction-market canonicalization (investigation complete)

**Confirmed real, richer than recalled.** Three classification layers, not one:

1. **`PredictionShardCategory`** — 13-value topic taxonomy (`_prediction_market_taxonomy.py`), built to fix a real
   problem: the old scheme dumped 4,986 of 4,999 daily markets into one `OTHER` bucket. Multi-dimensional: category ×
   market-structure (binary/scalar/categorical/ranked/range-bracket) × resolution-period.
2. **`PredictionMarketCategory`** — legacy 7-value coarse category. **Investigated for deletion 2026-08-20, verdict:
   DO NOT DELETE.** Genuinely load-bearing on 4 independent live paths: the live Polymarket ingest classification
   (instruments-service, hot path), the cross-venue arb feature pipeline (features-service calculators, confirmed
   shipped per a 2026-07-31 progress note), the live UI catalogue dropdown (`deployment-ui`'s `PredictionCatalogue.tsx`,
   with `CanonicalQuestionGroup` already occupying the paired fine-grained sub-filter slot in the same component —
   collapsing the two would destroy a deliberate two-level filter design), and MVP-scope gating. Full consumer list in
   this plan's Progress Log.
3. **`CanonicalQuestionGroup`** — the real cross-venue canonicalization mechanism, 97 members. A real Kalshi ticker
   and a real Polymarket slug for the same question resolve to the identical group value — production-wired (adapters,
   manifest writer, reader all import it, stability-hashed on manifest rows). Real examples: `KXBTCD-*` and
   `btc-up-or-down-april-15` both → `BTC_UP_DOWN_DAILY`; `KXFEDDECISION` → `FED_RATE_DECISION_PER_FOMC`.

- [x] ✅ [REVIEW] P0. **PredictionMarketCategory deletion investigated and correctly rejected** — do not re-attempt
      without new evidence; the 4-path consumer list above is the reason.
- [ ] [DOC] P0. **Write the prediction-markets section** under the data section using all three layers, with the real
      examples above (test-fixture strings matching real production naming grammar — not confirmed pulled from a live
      manifest; state that distinction in the doc).

### The artefact-to-epic coverage map

- [ ] [BACKEND] P1. **Declare which epic owns which artefact section** (R17, one level up). Measured 2026-08-20: the
      mapping from artefact section to owning epic exists only as reasoning over epic titles — there is no
      machine-readable relation, so nobody can check it and nobody will notice when it drifts. Each artefact section
      names its owning epic; each epic knows which artefact surfaces it feeds. This also gives T7a a real denominator
      for the artefact half of its coverage proof instead of a derived one.
- [ ] [REVIEW] P1. **Resolve the two orphaned artefact sections** — tracked at
      [/plans/active/issues/artefact_sections_with_superseded_owning_epics_2026_08_20.md](/plans/active/issues/artefact_sections_with_superseded_owning_epics_2026_08_20.md).
      The walkthrough's PnL-attribution section and the strategy docs' promote-workflow coverage both map to epics
      that are `status: superseded` with zero active child plans.

### Verification

- [ ] [REVIEW] P1. **Re-run the measurement that found this gap** after the drilldown lands — count distinct
      percentage values and per-day vocabulary in the walkthrough. If it still reads as 8 rollups, the drilldown did
      not land regardless of how much prose was added.
- [ ] [REVIEW] P2. **Check every client-facing figure against the standing constraints** before publication — no
      commercial/budget/funding/valuation/cost/ARR figures, ClearLoop never named.

### Vendor-name delabeling audit (operator ruling 2026-08-20)

**Rule**: never name a third-party data/library vendor to a counterparty (Tardis, Databento, CCXT, DeFiLlama, Odds
API) — relabel around the schema/function. Custody providers (Copper, Ceffu) are a DIFFERENT category and may be
named; this ruling does not extend to them without a separate decision.

- [x] ✅ [REVIEW] P0. **Audited and fixed across all five structure-passed artefacts** — Tardis (walkthrough,
      `platform-api-reference`), Databento (walkthrough), CCXT (`platform-architecture`, `strategy-service-deep-dive`
      x3) all relabeled to describe function. Verified zero hits at origin post-fix,
      `unified-trading-pm@2340bd96b5`/`@4ed7be87d0`/`@c1c0e7e81c`.
- [ ] [REVIEW] P1. **`platform-api-reference.html`'s worked example still returns a real vendor-tagged path live** —
      the DOC now documents `file` as an opaque token (correct target contract), but the live endpoint has not been
      fixed to match. Tracked separately:
      [/plans/active/issues/external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md](/plans/active/issues/external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md).
- [ ] [DOC] P2. **Audit `carveout-engineering.html` and `ODUM_Elysium_Phase2_Update.html`** for the same vendor-name
      pattern — not yet checked, since neither has been structure-passed yet.

### Track record, fund structures and engagement models (operator content, 2026-08-20, not yet written)

Operator-supplied content for a new section, precise figures **explicitly authorized as an override of the standing
no-commercial-figures rule for this specific track-record content only** — the override does not extend to pricing
language ("very cheap" was explicitly declined, kept qualitative).

- [ ] [DOC] P0. **Write the track-record/fund-structures section**: SMA and fund-structure servicing as a capability;
      distribution-channel relationships (qualitative, no pricing language); two DISTINCT track records kept separate
      — trading ($17M proprietary capital ~1.5yr + $5M sub-fund with an external investment manager = $22M combined;
      prior $4.5M HFT track record ~2.5yr) and service provision (an existing secured service-provision relationship,
      client base includes a fund of funds — do not blend the two claims). Close on: "the same infrastructure we
      trust with our own and our clients' money is the infrastructure available to them" — close to verbatim, this is
      the intended hook.
- [ ] [DOC] P0. **Write the engagement-models table** — three ways to engage, tied back to section 01's existing
      "each layer is independently adoptable" framing: (1) signal-in/execution-out — client brings the alpha, our
      execution/infrastructure runs it; (2) full portfolio management, end to end; (3) pure venue connectivity — the
      access layer to ~190 venues, client owns everything above it. Add a 4th: data-only — a unified API for market
      data (live AND historical, same adapters, `pipeline_mode` is the only difference) across CeFi/DeFi/TradFi/sports
      /prediction, without touching execution at all.
- [ ] [DOC] P1. **Add both website links** — `https://www.odum-research.com/` near the "ODUM RESEARCH" masthead mark
      (confirmed reachable, positioning: "Trading Infrastructure for Institutional Clients," no asset-class/strategy
      claims on the page to reconcile against); `https://www.odum-research.com/who-we-are` on the track-record section
      for the team (confirmed reachable, page title only — content not extracted, do not describe its contents,
      just link it).

## Progress Log

**2026-08-20 — authored.** No artefact edited. Created because R27 had zero tracked todos and the shard-drilldown gap
was measured, not assumed. The readiness-ledger todos lead deliberately: writing the drilldown by hand first would
mean transcribing thousands of shard numbers into HTML, which rots the day it is written.

**2026-08-20 (T5, cross-plan note — no todo here claimed or edited):** the two named source skills got real
extensions today, landed on LDR, directly relevant to the ledger todo: `readiness-state-dump/scripts/
derive_readiness.py` now emits `row_grain`/`coverage_source_grain` as two separate fields instead of one
conflated `grain` key (`unified-trading-pm@065067f345`), and its `execution_instruction` leg is now wired to a
real per-venue probe instead of a hardcoded `unverified` (`unified-trading-pm@8d47cf3393`).
`honest-coverage-dump/scripts/dump_coverage.py` now reports a dedup'd distinct-shard count and a per-asset-group
hollow-instrument_type fraction as first-class `dedup_stats` output (`unified-trading-pm@bb81afbcaa`) — the raw
cell count was inflated ~2% by case-variant/nan-vs-blank duplicate keys, still present in the 2026-08-20
coverage.json (measured: 3965 raw / 3877 distinct / 88 duplicates). Flagged the conflict this plan creates with
`/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md`'s own DOC "re-derive the
four artefacts by hand" todos there — held pending coordination on which approach to follow, not started blind.
