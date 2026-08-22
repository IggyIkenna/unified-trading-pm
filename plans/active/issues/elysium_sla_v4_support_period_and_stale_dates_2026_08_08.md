---
doc_type: issue
title: >-
  ODUM_SLA_v4 — binding 60-day support period contradicts the 30 days stated in every client-facing summary, plus stale
  June-2026 dates
summary: >-
  Reconciliation of the Elysium client pack (2026-08-08) found two defects in `ODUM_SLA_v4_2026-07-24.md`, the version
  sent to the client as `ODUM_Production_Operations_and_SLA.docx`. (1) SUPPORT PERIOD — binding §3 defines the Initial
  Support Period as "sixty (60) calendar days" and §5's heading reads "DAYS 1-60", but §2 line 88 refers to "the two
  post-30-day continuation options", the docx executive summary states "Initial Support | 30 days", and both the
  2026-07-20 delay letter and the 2026-08-08 follow-up promise "a complimentary 30-day post-launch monitoring period".
  The docx exec summary carries an express "substantive provisions prevail" clause, so on the current drafting the
  client is contractually entitled to 60 days while being told 30. (2) STALE DATES — a document dated 2026-07-24 still
  states Phase-2 acceptance occurs "on or around June 2026" (§2), Exhibit C custody integrations are "scheduled for June
  2026" (§3, Exhibit C), pre-cutover testing runs "through and including May 2026" (§3), and client seed capital arrives
  "from 30 June 2026 onwards" (§3) — all overtaken by the September-readiness / October-acceptance timeline in the very
  letter this SLA accompanied.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, sla, contract, client-communication, operator-gated]
related:
  [
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /codex/14-customer-journeys/commercial-model/elysium-delay-letter-2026-07-20.md,
    /codex/14-customer-journeys/commercial-model/elysium-remaining-work-appendix-2026-07-24.md,
  ]
created: 2026-08-08
author: interactive-session (slot 2)
last_updated: "2026-08-14" # CORRECTED 2026-08-16 (/plan-reconcile Section-3 triage): was 2026-08-09, stale against the 2026-08-14 Progress Log entry
parent_epic: client_isolation_and_governance_master
priority: P1
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role:
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope: [/codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md, /codex/14-customer-journeys/commercial-model/contracts/elysium-consulting-agreement-2025-03.md, /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md, /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md]
source: >-
  interactive session, 2026-08-08 Elysium client-pack reconciliation. Never committed — sat as an uncommitted new file
  in a `.tabs/2` working tree, swept into a protective `foreign-wip-elysium-not-mine-preserved-during-quickmerge-3`
  autostash during a concurrent quickmerge, and undiscovered until a 2026-08-09 fresh stash-pile re-audit found and
  recovered it (content independently re-verified against the live codex docs as still accurate/unchanged before
  filing).
---

# Elysium SLA v4 — support-period contradiction + stale dates

Found during the 2026-08-08 reconciliation of the Elysium client pack against the PM repo record, while checking whether
the two `.docx` attachments sent to the client matched their codex counterparts.

## Finding 1 — 30 vs 60 day Initial Support Period (**material, contract term**)

| Location                                                     | States      |
| ------------------------------------------------------------ | ----------- |
| `ODUM_SLA_v4_2026-07-24.md` §3, line 131 (**binding**)       | **60 days** |
| `ODUM_SLA_v4_2026-07-24.md` §5 heading, line 220             | **60 days** |
| `ODUM_SLA_v4_2026-07-24.md` §2, line 88                      | **30 days** |
| `ODUM_Production_Operations_and_SLA.docx` executive summary  | **30 days** |
| Delay letter 2026-07-20 (sent), Main points + CEFFU sections | **30 days** |
| Follow-up email 2026-08-08                                   | **30 days** |

The docx executive summary states: _"This executive summary is provided for convenience only. In the event of any
inconsistency, the substantive provisions of the Agreement prevail."_ On the current drafting the substantive provision
is **60 days**, so the client's contractual entitlement is double what every client-facing summary has promised. The
exposure runs in the client's favour, which is why it has not surfaced — but it is a live inconsistency in a document
already in the client's hands.

**Decision required (operator, not dispatchable):** is 60 the intent and every summary wrong, or is 30 the intent and
§3 + §5 wrong? Do not "fix" this by silently editing either number — the document has been sent.

## Finding 2 — stale dates in a doc dated 2026-07-24

| Line | Text                                                                 |
| ---- | -------------------------------------------------------------------- |
| 119  | Phase-2 production acceptance "occurring on or around **June 2026**" |
| 142  | Exhibit C custody integrations "scheduled for **June 2026**"         |
| 145  | Pre-cutover testing "through and including **May 2026**"             |
| 149  | Client seed capital "provided **from 30 June 2026 onwards**"         |
| 1192 | Integration services delivered "in or around **June 2026**"          |

All are superseded by the September-readiness / October-acceptance timeline stated in the delay letter this SLA was
attached to. §3's capital-and-timing paragraph is the most exposed: it asserts pre-cutover testing "is expected to be
complete" by 30 June 2026, which did not happen.

## Todos

- [x] ✅ [OPERATOR] P1. **RULED 2026-08-09 (operator, interactive): 60 calendar days is the correct Initial Support
      Period** — §3 (line 131, binding) and §5's heading (line 220) were right; §2 (line 88) and the docx executive
      summary were wrong. Fixed the internal codex-record inconsistency: `ODUM_SLA_v4_2026-07-24.md`:88 now reads
      "post-60-day continuation options" (was "post-30-day"), matching §3/§5. **This does NOT correct what's already in
      the client's hands** — the docx executive summary (30 days) and both sent delay-letter/follow-up communications
      (30 days) are unchanged; the client has been told a shorter support window than they're actually entitled to. That
      correction is todo 2 below (reissue vs. side letter) — ruled on the internal record only, not on how/whether to
      notify the client of the discrepancy.
- [x] ✅ [OPERATOR] P1. **SUPERSEDED 2026-08-11** — see
      `/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`'s operator ruling: the
      Initial Support Period is standardised at **30 days**, reversing this doc's own 2026-08-09 ruling above (60 days).
      `ODUM_SLA_v4` §1/§3/§5 now all read 30. This doc's todo 1 above (60 days binding) is now the STALE side of the
      reversal — kept for history, not current guidance. The reissue-vs-side-letter MECHANISM decision (todo below) is
      NOT resolved by this reversal — it's still open, and now also governs the client-facing 30-day correction, not
      just the stale dates.
- [ ] [DOCS] P1. Draft SLA v5 (30-day support period per the 2026-08-11 standardization ruling, corrected
      September/October dates replacing the five stale June/May-2026 dates) for operator review BEFORE anything
      goes to the client. Per D26 ruling (2026-08-22): approved — draft v5 for operator review first.
- [ ] [OPERATOR] P2. Confirm the actual send date of the delay letter. The codex record is dated 2026-07-20, but both
      attachments carry mtime 2026-07-29 18:56, and the sent copy opens "Following the quick WhatsApp massager the other
      day" — wording absent from the 2026-07-20 draft. If the real send was ~29 July, rename/redate the codex record.
- [ ] [AGENT] P3. Typo in the sent letter recorded verbatim in the codex record: "WhatsApp massager" (should be
      "message"). Recorded as-sent deliberately, since that doc is `authoritative_for` exact wording. Correct in any
      future reissue only.

### Added 2026-08-11 — findings from transcribing the underlying contract into codex

> Source docs now in codex:
> [`contracts/elysium-consulting-agreement-2025-03.md`](/codex/14-customer-journeys/commercial-model/contracts/elysium-consulting-agreement-2025-03.md)
> ·
> [`contracts/elysium-subcontracting-agreement-ikenova-odum.md`](/codex/14-customer-journeys/commercial-model/contracts/elysium-subcontracting-agreement-ikenova-odum.md)

- [ ] [OPERATOR] P0. **Locate the $90k → $135k variation document, or stop citing
      $135k.** Annex A of the executed
      contract totals **$90,000** ($45k + $45k) and no addendum exists in codex or
      in `~/Downloads`. The $45k outstanding-balance position rests entirely on a document nobody has produced. Either
      produce it, or agree the uplift in writing with Elysium before invoicing the final tranche.
- [ ] [OPERATOR] P0. **Resolve the entity position before any SLA is signed as "Odum Research".** The only instrument on
      file is an **unsigned, undated subcontracting agreement** under which IkeNova Ltd remains the Elysium counterparty
      and remains fully liable (cl. 3) — not the novation its filename implies. Either execute a real novation with
      Elysium's written consent (required by Art. 7.7), or draft the SLA with IkeNova as Service Provider and Odum
      Research named as its subcontractor.
- [ ] [OPERATOR] P1. **Obtain Elysium's Art. 1.4 prior written consent for the Odum Research subcontract.** Art. 1.4
      permits outside services only with "the prior written consent of an officer of the Company". Clause 4 of the
      subcontract binds Odum Research to the confidentiality/work-product terms, which covers the second limb of Art.
      1.4 but not the consent limb. Both signatories being the same director makes a written acknowledgement more
      important, not less.
- [ ] [OPERATOR] P1. **Confirm which contract version was executed — 1 or 3 March 2025.** The e-signed PDF
      (`Doc ID 5f6491d203e91ea6c5b836c722dba886e0d1565b`) says 3 March; the `(w specifics)` DOCX and track-changes PDF
      say 1 March; the subcontract cites 3 March twice. Art. 4 and Art. 6 wording is identical across versions, so only
      the date and anything clocking from it is affected — but the SLA preamble asserts a date, so it must be right.
      **Supersedes the earlier codex claim that 1 March is correct and 3 March was an error** — that has been corrected
      in
      [`elysium-managed-sla-2026-05-14.md`](/codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md)
      §1.
- [ ] [OPERATOR] P1. **Get a written reading of Art. 6.2's 24-month clock.** "For 24 months following this agreement" is
      ambiguous between "following execution" (expiring ~March 2027) and "following completion/termination". Codex
      previously asserted the latter, which is the _less_ favourable reading; the text does not settle it. The answer
      sets when the Carry & Yield family unlocks for our own book and other clients.
- [ ] [OPERATOR] P2. **Raise Art. 4.4's "mimic" wording in any variation.** As drafted we may not "use, display, link
      to, reproduce, or mimic materials used in creating any Work Product for any purpose whatsoever" without written
      consent. Read literally that reaches beyond the non-compete and beyond the Work Product itself, to the materials
      used in creating it. Narrow it, or obtain a standing consent scoped to our platform components.
- [ ] [OPERATOR] P2. **Reconcile Annex A Phase One against the carve-out's "excluded" list.** Annex A Phase One
      expressly includes "Development of back-testing framework" as a deliverable, so the backtesting framework is
      arguably Work Product. The SLA Exhibit A manifest lists "Historical batch-ingestion pipelines … (back-test infra)"
      as EXCLUDED platform IP. Those two positions are in tension and counsel should see it before Exhibit A is signed.
- [ ] [AGENT] P3. Six drafting defects in the contract are catalogued in the consulting-agreement record's defect table
      (misspelled "Eysium AM Ltd.", duplicate clause 2.2, Art. 4.1 cross-reference to a non-existent "Section 1.5",
      stray `). ).`, "crypyo"). Raise as a housekeeping schedule if a variation is executed; do not silently fix the
      verbatim record.

### Added 2026-08-11 (second pass) — Exhibit A defects found while drafting the per-repo hand-over manifest

- [ ] [AGENT] P0. **Exhibit A enumerates Work Product by file paths that do not exist.** The manifest in
      [`elysium-managed-sla-2026-05-14.md`](/codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md)
      §2.3 lists `execution_service/.../adapters/cefi/{okx,bybit,binance}_perp_adapter.py`,
      `.../adapters/defi/{copper_mpc,ceffu_oes}_adapter.py` and `.../adapters/defi/lido_staking_adapter.py`. **None of
      those paths resolve.** Verified 2026-08-11 against the tree; the real locations are
      `execution_service/trade_execution/adapters/{okx,bybit,binance,deribit}_ccxt.py`,
      `execution_service/custody/{copper,ceffu}.py`, and `execution_service/venues/lido.py` +
      `execution_service/defi_execution/protocols/lido.py`. Enumerating owned code by a non-resolving path is
      unverifiable for the client and unevidenceable for us — correct the manifest before Exhibit A is signed. Note the
      adapters are ccxt-based, which is a dependency the carve-out inherits and which Exhibit A does not currently
      mention.
- [ ] [OPERATOR] P0. **The carve-out package cannot produce a value the strategy requires.** `staked_basis.py` reads
      `features["funding_rate_apy_bps"]` (alongside `staking_apy_bps`) and returns no decision without it. Under the
      managed service the feature pipeline supplies it. Under Option B there is no feature pipeline, and the ONLY
      direct-from-venue funding-snapshot implementation in the workspace lives in
      `e2e-testing/scripts/defi/funding_ensemble_engine.py` — a test-harness repo that is in neither the transferred nor
      the licensed bucket. Verified 2026-08-11: no production repo (`strategy-service`, `execution-service`,
      `market-tick-data-service`) contains a live funding fetcher outside test fixtures. **As drafted, a carve-out hands
      over engines that ask for a number nothing in the package produces.** Resolve by productionising the venue funding
      readers and adding them to the §A.3 licensed set, or by stating explicitly in the SLA that the client writes them.
      Either way it must be decided before Option B is elected, not at hand-over.
- [ ] [AGENT] P1. `staking_apy_total` exists at `features-service/features_service/onchain/engine/staking_apy_total.py`
      and is correctly licensable. There is **no** counterpart calculator file named `funding_apy_bps` — Exhibit A's
      licensed list implies one. Reword to describe the funding value as a pipeline-produced feature, which is what it
      is, and then resolve it via the P0 above.

### Added 2026-08-11 (third pass) — carve-out presentation strategy + the rebuild calibration

> Client-facing documents now live in
> [`/codex/14-customer-journeys/commercial-model/`](/codex/14-customer-journeys/commercial-model/) (both published as
> private artifacts; **URLs recorded in that directory's README — pass the URL when updating or you create a duplicate
> artifact**).

- [x] ✅ [AGENT] P1. **Rewrote `carveout-engineering.html` into a specification register** — rev 2.0, republished to the
      same artifact URL (`39d52123…`, favicon 🧩 unchanged), file at
      [`/codex/14-customer-journeys/commercial-model/carveout-engineering.html`](/codex/14-customer-journeys/commercial-model/carveout-engineering.html).
      Operator verdict 2026-08-11 was that it "discusses our methodology way too much" and was not presentable to a CTO.
      Restructured against an operator-supplied advisory draft
      (`~/Downloads/Odum_Elysium_Strategy_Carve_Out_CTO_Architecture.docx`, **input to us, not a document for the
      client**) whose structure was better than the original nine sections. Four ideas adopted from it: (1) a
      **ship-form taxonomy** — FULL / REDUCED / STATIC / INTERFACE-ONLY — replacing a single flat "reduced" pill; (2)
      **`contracts-platform`, the architectural seam** — the twenty non-contributing repositories are now expressed as
      **10 typed interfaces** the strategy calls, each resolving either to a local implementation or to a maintained
      service, which communicates platform scope in method signatures rather than in a loss-list (this is the change
      that actually fixes the register complaint — showing, not telling); (3) **hand-over acceptance criteria**, nine
      conditions, making the hand-over contractible; (4) **proposed package names** rather than our real repo names, so
      internal topology is not disclosed. Retained from the original: the estate mapping (now a §09 appendix), the
      funding-reader requirement, operational responsibilities, extension work-items. Deleted entirely: the
      internal-negotiation sections ("an honest summary of the trade", "the three questions we would ask in your
      position", "to be direct about our own position") and every mechanism-level description of how the dynamic layer
      works. Two SVG figures (runtime path; the seam resolving two ways). Verified: 0 `var()`-in-SVG-attribute
      occurrences, 0 script/style inside SVG, 0 external hosts, 0 text/text collisions and 0 text-overflows-host **on a
      detector first validated by injecting a known collision and a known overflow and confirming both fired**, no
      horizontal page overflow, themes resolve in all three states (light / dark-stamped / un-stamped), 44% of scroll
      hidden at default and 64% fully collapsed (measured).
- [ ] [AGENT] P1. **Build the lite carve-out repo now, demonstrate it, deliver on election (option (c))** — shows the
      file tree and the import closure running, hands over the manifest, and makes Art. 4.5 compliance a
      days-not-weeks problem; build it regardless of the client decision (validates the import closure/tier
      architecture, becomes the template for the next Carry & Yield client, surfaces gaps like the funding-reader
      defect before a client does). Per D27 ruling (2026-08-22): approved — build the "lite" carve-out repo now;
      ship the inert betfair/ibkr/polymarket adapters as-is.
- [ ] [AGENT] P1. **Withhold `/codex/02-data/carry-venue-live-integration-reference.md` from any carve-out hand-over
      package by default** — it enumerates, per venue, the exact endpoint, funding field, settlement interval,
      symbol mapping and sign-convention gotcha for 13 venues, turning the largest carve-out work item into roughly
      one day if disclosed. Update Exhibit A to state the documentation scope explicitly. Per D27 ruling
      (2026-08-22): approved — withhold the venue-integration reference.
- [ ] [AGENT] P2. **Fix the funding-reader gap BEFORE any lite-repo demonstration**, not just before a hand-over
      (upgrade of scope on the P0 above). If an engineer traces `features["funding_rate_apy_bps"]` to nothing during a
      demo, that is the wrong impression at the worst moment. The readers exist in
      `e2e-testing/scripts/defi/funding_ensemble_engine.py`; productionising them converts the most awkward gap in the
      package into a completeness signal.

### Added 2026-08-11 (fourth pass) — defects found in our OWN published client documents while rewriting

> All three were found by re-deriving numbers the previous pass had asserted, rather than by re-reading the prose. The
> README in [`/codex/14-customer-journeys/commercial-model/`](/codex/14-customer-journeys/commercial-model/) instructs
> re-derivation before reuse for exactly this reason; this is that instruction paying for itself one day later.

- [ ] [OPERATOR] P0. **The published `platform-architecture.html` states a "complimentary 30-day support period" in
      three places (plus "the decision point is day 31") — which contradicts this issue's own operator ruling that **60
      calendar days** is the binding Initial Support Period.** Found 2026-08-11 by grepping the published artifact for
      the support-period wording. The 2026-08-09 ruling (todo 1 above) settled that `ODUM_SLA_v4` §3 line 131 and §5
      line 220 were right at 60 days and every 30-day summary was wrong; the client-facing architecture document I
      published on 2026-08-11 then repeated the wrong number. **Deliberately NOT fixed unilaterally**: which number
      appears in client-facing material is precisely the open operator decision in todo 2 (reissue vs. side letter), and
      changing it silently would pre-empt that ruling and could create a third inconsistent version. The rewritten
      `carveout-engineering.html` avoids the trap by stating no number and deferring to the SLA — the same fix is
      available for the architecture document once the operator rules. **Understates our obligation in the client's
      favour, so it is not urgent commercially — but it is a contradiction sitting in a forwardable document.**
- [x] ✅ [AGENT] P1. **Corrected two over-stated counts in the client documents.** Re-derived from the tree 2026-08-11.
      (a) **Carry archetypes: claimed 8, actual 6** — `carry_and_yield/` contains `basis_dated`, `basis_perp`,
      `recursive_staked`, `rotation_lending`, `staked_basis`, `staking_simple`; the earlier count folded in supporting
      modules (`funding_dispersion`, `dynamic_hedge_ratio`, the writers) that are not archetypes. The transferred figure
      is therefore **2 of 6**, not 2 of 8. (b) **Venue adapters: claimed 13, actual 20 distinct adapters** in
      `trade_execution/adapters/` alone (aster, binance, bitfinex, bitget, bybit, cboe, cme, coinbase, deribit, fx,
      hyperliquid, ibkr, ice, kraken, nasdaq, nyse, okx, polymarket, sports, upbit — Kraken's four files are one venue),
      plus the on-chain protocol modules. So **4 of 20**, and the earlier number _understated_ our own estate. Both
      corrected in the rewrite; `platform-architecture.html` should be checked for the same two figures. **Method
      note:** `VENUE_TO_ADAPTER_KEY` is named in CLAUDE.md as the venue-registry SSOT but its definition was not
      locatable in `unified-api-contracts/` non-test sources in a reasonable search, so the count above is a **measured
      floor from the adapter directory**, not a registry read. Anyone quoting a venue total should either find the
      registry definition or quote the floor and say so.
- [x] ✅ [AGENT] P2. **Locate the real `VENUE_TO_ADAPTER_KEY` definition and record its path in CLAUDE.md's conditional
      index.** CLAUDE.md asserts venue lists and adapter keys are UAC data with `VENUE_TO_ADAPTER_KEY` as the resolver,
      but a `rg -l` across non-test sources returned only _consumers_ (`deployment-api`, `market-tick-data-service`,
      `e2e-testing`, `unified-trading-pm/scripts/cicd`) and one UAC **test** file. Either the symbol lives somewhere the
      search missed or it has been renamed and the doc reference has rotted. A pointer that costs each agent a failed
      search is a defect in the pointer.

#### Rebuild-effort calibration (recorded because it decides the sequencing question, and existed only in chat)

Estimated 2026-08-11 against the workspace estimate multipliers (brand-new 1.0x, infra 0.8x, research 1.2x), assuming
the client holds the carved-out code as reference and uses agent-assisted engineers. **These are estimates, not
measurements** — but the shape is the point, not the precision.

| Component to rebuild                            | AI-days | Note                                                    |
| ----------------------------------------------- | ------- | ------------------------------------------------------- |
| Runner, supervisor, tick loop                   | 3-5     | Genuinely easy                                          |
| Live funding + staking readers, 4 venues        | 5-10    | **1-2 if they receive the venue-integration reference** |
| Secrets, credentials, rotation                  | 3-5     |                                                         |
| Deployment + CI (adequate, not ours)            | 8-15    |                                                         |
| Basic monitoring + alerting                     | 8-15    |                                                         |
| Position/balance reconciliation                 | 12-20   | First thing a fund admin asks for                       |
| Ledger, factor attribution, three-method HWM    | 20-35   | Easy to do badly                                        |
| Execution algos (TWAP/VWAP/POV + simple SOR)    | 20-40   | Agents do textbook versions well                        |
| Backtest harness + determinism proof            | 40-80   | **Gated on data they do not have**                      |
| Capture estate + coverage accounting            | 30-60   | Engineering is the small part                           |
| Dynamic layer (rotation, switching, allocation) | 30-60   | Gated on data + research                                |

**Bare-minimum runnable: 25-45 AI-days. Trustworthy-with-client-capital: 160-300 AI-days.** The operator's stated
decision threshold was ~180 AI-days (below it they rebuild, above it they do not), so the answer straddles the line and
**turns entirely on what standard the client holds itself to** — which is a variable this document set influences.
Framed as "two engines and four adapters" they will estimate ~30 days and try; framed as "a system that produces a
defensible monthly number" they will estimate ~200 and will not.

**The strategic conclusion, which inverts the protective instinct:** the code is NOT the moat, and any strategy resting
on "they cannot build it" depreciates every month that agent tooling improves. What has not become cheap is (1) the data
history — three years of tick, funding and order-book history across four venues cannot be backfilled in a month at any
price, and the vendor licences are real money; (2) the live-probed venue knowledge — which venue takes stETH versus
wstETH, at what haircut, in which margin mode, and the two combinations that silently mis-mark a position daily; (3)
operational track record. Therefore **transparency is the defensive move here, not the risky one**: showing the
architecture does not accelerate a rebuild, it raises the client's internal definition of "done". The real risk is a
client who UNDER-estimates production, tries, fails slowly, and ends the relationship badly.

**Corollary that should shape the commercial framing:** the more ambitious the client roadmap, the worse a carve-out is
for them — more coins needs the capture estate, more venues needs the collateral matrix and error classification, more
strategies needs the shared spine, and TradFi is a second platform with a compliance surface rather than another venue.
So the frame is "here is what the next 24 months costs on the platform versus alone", not "here is what you lose by
leaving". Same facts, forward-looking, and it is the argument we actually believe.

## Deferred work after 2026-08-11

Separated by KIND, because these need different responses. Nothing below is half-committed — everything shipped this
session is on `live-defi-rollout` at `05088f8a18`.

| Item                                                                                                     | Kind                                 | Blocked on                                 |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------ |
| Correct Exhibit A's non-resolving adapter paths in the SLA manifest                                      | **Not done** — real work, pick it up | nobody; wording wanted operator review     |
| Check `platform-architecture.html` for the 8-archetype / 13-venue counts corrected in the rewrite        | **Not done** — real work, pick it up | nobody                                     |
| Locate the real `VENUE_TO_ADAPTER_KEY` definition; fix the rotted CLAUDE.md pointer                      | **Not done** — real work, pick it up | nobody                                     |
| Resolve the 30-vs-60-day support period in the published `platform-architecture.html`                    | **Operator-owned**                   | ruling on todo 2 (reissue vs. side letter) |
| Productionise the venue funding readers into the licensed set                                            | **Not done** — real work, pick it up | nobody                                     |
| Build the lite carve-out repo (recommendation: build now, demo, deliver on election)                     | **Operator-owned**                   | operator go-ahead on sequencing            |
| Decide which DOCUMENTATION ships with a carve-out (the venue-integration reference is the sensitive one) | **Operator-owned**                   | operator decision                          |
| Locate the $90k → $135k variation document, or stop citing $135k                                         | **Operator-owned**                   | document may not exist                     |
| Resolve the entity position (unsigned subcontract, not a novation) before any SLA names Odum Research    | **Operator-owned**                   | counsel + Elysium consent                  |
| Confirm which contract version was executed (1 vs 3 March 2025)                                          | **Operator-owned**                   | Elysium confirmation                       |
| Written reading of Art. 6.2's 24-month clock                                                             | **Operator-owned**                   | counsel                                    |
| Elysium's Art. 1.4 written consent for the Odum Research subcontract                                     | **Cannot be done yet**               | external party                             |

**Recommended NEXT item: productionise the funding readers.** It is the only one that is (a) pure engineering with no
operator dependency, (b) a prerequisite for BOTH remaining paths — a lite-repo demonstration and a real hand-over — and
(c) currently the single defect that would most damage credibility if an Elysium engineer found it first. The Exhibit A
path correction is second and is roughly an hour, but it wants a wording review. The document rewrite that was third
here is **done** (rev 2.0, 2026-08-11).

**Note on sequencing after the rewrite.** The rewritten document now specifies eleven packages and a ten-interface seam
as the deliverable, and labels them a _proposed_ structure that does not yet exist. That is honest, but it also means
the document commits us to building the seam if it is ever shown — a CTO who reads §04 will ask to see
`contracts-platform`. So the lite-repo decision is now **coupled to whether this document goes out**, where previously
they were independent. Worth the operator knowing before forwarding it.

## Progress Log

- **2026-08-08** — Found during Elysium client-pack reconciliation. Both `.docx` attachments in `~/Downloads` extracted
  and compared against codex. SLA body matched (8,136 docx words vs 8,369 md words; delta is the exec summary the docx
  adds and markdown syntax). Commercial terms verified identical: \$3,000/mo retainer, 25% first \$100M AUM / 10%
  thereafter, \$2,500 per additional venue, \$2,500 per additional LST. The remaining-work appendix did **not** match
  and has been corrected under separate change; this issue covers the SLA only.
- **2026-08-09 (recovered)** — This doc was drafted 2026-08-08 but never committed; a concurrent `quickmerge` swept it
  into a protective autostash (`stash@{8}`, tagged `foreign-wip-elysium-not-mine-preserved-during-quickmerge-3`) in a
  `.tabs/2` checkout, where it sat undiscovered for a day. Found and recovered by a fresh stash-pile re-audit
  (dispatched as part of a broader operator-queue cleanup session); both findings independently re-verified against the
  live `codex/14-customer-journeys/commercial-model/` docs before filing — still accurate, unchanged since 2026-08-08.
  Filed now rather than left in the stash pile.
- **2026-08-11** — Operator flagged that "we own the trading code" (in a client-facing architecture deck) contradicts
  the contract. Confirmed: Consulting Agreement **Art. 4.1–4.2** makes all Work Product the exclusive, irrevocably and
  perpetually assigned property of the Elysium **Group**, with only "generic programming methods and open-sourced
  components" retained (Art. 4.6). Located and transcribed both source instruments into codex under
  `codex/14-customer-journeys/commercial-model/contracts/`. Three codex claims corrected in the same pass: (a)
  `pod-elysium-client-onboarding.md` §2's "UTS-managed / trading code" row — relabelled **UTS-operated**, since it
  described operational responsibility and was being read as ownership (this is the line that produced the deck error);
  (b) `elysium-managed-sla-2026-05-14.md` §1's "dated 1 March 2025 (not 3 March)" — the e-signed PDF says 3 March, so
  the date is UNRESOLVED rather than settled; (c) the same row's "IkeNova Ltd has migrated to Odum Research" — the
  instrument on file is an unsigned **subcontract** that keeps IkeNova as counterparty and fully liable, not a novation.
  Also found: the $135k variation document does not exist anywhere on the machine (Annex A totals $90k), and no Art. 1.4
  Elysium consent is evidenced for the Odum Research subcontract. Eight todos filed above.
- **2026-08-11 (second pass)** — Drafting a per-repository Option-B hand-over manifest for the client architecture
  document surfaced two defects in Exhibit A that a checkbox review would not have caught, because both only appear when
  you try to actually assemble the package: the enumerated adapter paths do not resolve against the current tree, and
  the licensed set cannot produce `funding_rate_apy_bps`, which `staked_basis.py` requires to make any decision at all.
  Both filed as P0 above. Real paths and the import-closure extraction method are recorded in the client document's
  hand-over manifest section; the SSOT correction to Exhibit A itself is the P0 todo, not yet applied.
- **2026-08-11 (third pass, pre-compact checkpoint)** — Two client-facing HTML documents built and published as private
  artifacts, then promoted out of the session scratchpad into
  [`/codex/14-customer-journeys/commercial-model/`](/codex/14-customer-journeys/commercial-model/) with a README
  recording the artifact URLs (republishing without the URL creates a duplicate rather than updating), the authoring
  traps, and the validated palette. **The trap most worth carrying forward: CSS `var()` does not resolve in SVG
  presentation attributes** — `fill="var(--x)"` renders black; it must be `style="fill:var(--x)"`. 498 occurrences were
  written the wrong way first and would have shipped every diagram in black. Also recorded a self-correction: a claimed
  ~40% scroll reduction from collapsing reference tables measured at **7%**; the height was in the figures and the
  prose, and the fix that worked was restructuring every section behind a toggle (measured 70-81%). Operator rejected
  `carveout-engineering.html` as too methodology-heavy for a CTO — rewrite is a tracked todo above, not yet done. Pushed
  as docs-only; the operator had earlier said "don't worry about merging yet", which this checkpoint overrides ONLY for
  documentation and plan files (zero code, zero shipping surface) because the alternative was losing the artifacts and
  the calibration to compaction in a shared checkout that already carried another session's staged changes and a stale
  unmerged index entry.
- **2026-08-11 (fourth pass)** — `carveout-engineering.html` rewritten to rev 2.0 and republished to the same artifact
  URL. The register problem the operator identified was fixed structurally rather than by editing prose: the twenty
  non-contributing repositories are now **ten typed interfaces** (`contracts-platform`) that resolve either to local
  implementations or to maintained services, so platform scope is communicated in method signatures instead of in a list
  of things the client does not get. Structure taken from an operator-supplied advisory draft; substance, measurements
  and diagrams retained from the original. **Three defects found in our own published documents by re-deriving asserted
  numbers**: the archetype count was overstated (8 → 6), the venue-adapter count was _understated_ (13 → 20), and the
  published architecture document repeats the 30-day support period that this issue's own ruling had already established
  as wrong (60 is binding). The last is left for the operator because it is the same decision as todo 2. **Process note
  worth keeping: the null result from the SVG collision detector was only trusted after injecting a known collision and
  a known overflow and confirming the detector fired** — the previous pass shipped two buggy versions of that same
  check, so "0 findings" from an unvalidated detector is not evidence.
- **Two standing environment conditions, neither mine to fix.** (1) The checkout still carries a peer's stale unmerged
  index entry for `scripts/dev/ff-starvation-detect.sh` (`UU`, no `MERGE_HEAD`), so `git pull` fails in this slot and
  the five-minute ff-pull cron is failing with it; local HEAD was **171 commits behind** origin during this session.
  Work was unaffected because `safe-doc-push.sh` commits from an isolated worktree, which is exactly the failure this
  script exists for. (2) Because HEAD was stale, the local copy of **this issue doc was the 127-line version while
  origin held 334 lines** — editing the local copy would have destroyed ~200 lines of the previous pass's work. It was
  re-synced from `origin` before editing (stale copy preserved at `/tmp/issue-local-stale-backup.md`). **Any session
  working in a behind-HEAD checkout must read the file from `origin/<branch>` before editing it, not from disk.**
- **context-scout 2026-08-14**: populated context_scope (4 entries).
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:edb7041bdca17290]: KEEP-NA, stale-item corrected -- closed the VENUE_TO_ADAPTER_KEY-location todo (lines 280-285): the premise (symbol location unknown) is false -- the symbol is defined at unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:104 (confirmed live on disk 2026-08-17; the candidate's own rg -l search never reached that repo/path), already documented in the active registry_ssot_hardening_2026_08_16.md's Measured Baseline (line 84) and cross-cited by 2 other candidates from this same audit run. Doc stays assigned_vm: NA for its other 18 open items (this is a HUMAN-gated client-SLA doc). Cross-cutting tranche audit conflict-check finding.
- **2026-08-22 — ruling D26 (Elysium SLA v5 reissue)**: OPERATOR-RULED 2026-08-21 — APPROVED: draft SLA v5 (30-day
  support period, corrected dates) for operator review BEFORE anything goes to the client. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **2026-08-22 — ruling D27 (Elysium disclosure and carve-out scope)**: OPERATOR-RULED 2026-08-21 — APPROVED: build
  the "lite" carve-out repo now, withhold the venue-integration reference, ship the inert betfair/ibkr/polymarket
  adapters as-is. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
