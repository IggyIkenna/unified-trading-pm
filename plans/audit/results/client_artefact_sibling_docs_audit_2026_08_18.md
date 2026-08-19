---
doc_type: audit-result
title: Client artefact sibling-docs audit (platform-architecture, carveout-engineering, strategy-service-deep-dive, ODUM Phase2) — second-pass audit 2026-08-18
summary: >-
  Second-pass, read-only audit of the four Elysium/POD client-disclosure artefacts the 2026-08-18 first-pass audit
  did not touch. Found one hard disclosure-boundary violation the first-pass audit's rule set forbids outright —
  "ClearLoop" named six times in strategy-service-deep-dive.html — plus a performance-figure disclosure (a vague
  annualised-return range) repeated verbatim across platform-architecture.html and the ODUM Phase2 email, in
  violation of the owning plan's explicit "no performance figure anywhere until the overlays land" rule. Found one
  materially false present-tense capability claim (platform-architecture.html asserts the staked-basis structure
  "runs on Solana against Drift" today; the owning plan's own investigation confirms DRIFT was removed from the UAC
  collateral matrix over a month before this document's issue date and SOL staked basis is structurally
  unavailable). Found a repeat, in a sibling document, of the exact highest-severity finding the completed audit
  raised for strategy-service-walkthrough.html's transfer-wiring overstatement. Also found strategy-service-deep-dive.html
  getting several facts RIGHT that the already-audited walkthrough got wrong (11 instruction types, the real 9-member
  StrategyFamily list, the correct custody-provider roster) — evidence the four files were authored independently
  rather than copy-drifted from one stale source.
status: pass
nature: record
severity: P0
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope: >-
  platform-architecture.html (~252KB), carveout-engineering.html (~87KB), strategy-service-deep-dive.html (~66KB,
  read in full), ODUM_Elysium_Phase2_Update_2026-07-24.html (~14KB, read in full) — disclosure-boundary grep sweep
  (ClearLoop / dollar figures / budget-ARR-valuation-revenue / performance figures) across all four in full, plus a
  targeted accuracy pass (full-text read on the two smaller files, section-by-section targeted reads plus grep
  sampling covering roughly three-quarters of platform-architecture.html and carveout-engineering.html, weighted
  toward the sections most likely to carry stale specific claims) cross-checked against the two owning plans, the
  carve-out plan, and the completed first-pass audit.
date: 2026-08-18
auditor: >-
  1 general-purpose sub-agent (sonnet), dispatched as one of 5 parallel agents doing a second-pass audit of
  client-disclosure artefacts, read-only, SUB_AGENT_MANDATORY_RULES.md pasted at spawn.
repos: [unified-trading-pm]
asset_group: [cross-cutting, defi]
stage: [strategy, execution, meta]
scope: [engineer, admin]
tags: [client-disclosure, elysium, audit, sibling-artefacts, disclosure-boundary]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
  ]
created: 2026-08-18
---

# Client artefact sibling-docs audit — 2026-08-18

**Do not edit any of the four HTML files or any plan from this report.** Per the governing plans, the operator
reviews every claim before it reaches a client document. This is findings only — read-only task, one file created.

## Method note

Read the two owning plans in full (`nick_ai_platform_disclosure_artifact_2026_08_16.md`,
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` — 963 lines, read in two passes covering the
whole file), `elysium_carveout_stubbed_strategy_service_2026_08_12.md` in full, `client_artefact_remediation_2026_08_18.md`
in full (the disclosure-boundary wording — "never name ClearLoop," "no performance figure anywhere until the
overlays land" — traces to these), and the completed first-pass audit
(`nick_ai_and_elysium_artefact_audit_2026_08_18.md`) in full as ground truth for cross-checking. `strategy-service-deep-dive.html`
and `ODUM_Elysium_Phase2_Update_2026-07-24.html` were read in full (1001 and 167 lines respectively).
`platform-architecture.html` (3317 lines) and `carveout-engineering.html` (1281 lines) were covered via a
combination of full-section reads (masthead/factbar, §01–§05, §11, §13 for platform-architecture; §01–§04, §08–§09
for carveout-engineering) and exhaustive `rg` sweeps for the specific terms this task and the owning plans flag as
load-bearing (ClearLoop, `$`, budget/ARR/valuation/revenue, Sharpe/return/drawdown figures, instruction-type and
strategy-family counts, custody-provider names, transfer-wiring language, Hyperliquid/Drift/Jupiter/Kamino/Marinade).
Roughly three-quarters of platform-architecture.html's prose was directly read; the remainder (mainly §06–§10,
§12) was grep-sampled, not line-by-line read — flagged explicitly in "What I could not verify" below rather than
silently treated as clean.

---

## Disclosure-boundary findings — read this section first

**One hard-rule violation found: "ClearLoop" is named six times in `strategy-service-deep-dive.html`.**

| File | Verdict |
| --- | --- |
| `platform-architecture.html` | Clean — 0 hits for `clearloop` (case-insensitive), 0 dollar-sign hits, 0 budget/ARR/valuation/revenue hits |
| `carveout-engineering.html` | Clean — 0 hits for `clearloop`, 0 dollar-sign hits, 0 budget/ARR/valuation/revenue hits |
| `strategy-service-deep-dive.html` | **NOT CLEAN — ClearLoop named 6 times** (below). Otherwise clean: 0 dollar-sign hits, 0 budget/ARR/valuation/revenue hits |
| `ODUM_Elysium_Phase2_Update_2026-07-24.html` | Clean on ClearLoop/$/budget/ARR/valuation/revenue. **Carries a performance-figure disclosure** (below) |

### Finding D1 — "ClearLoop" named 6 times in `strategy-service-deep-dive.html`

> **Resolved 2026-08-19 (slot 10, review)** — independent `rg -i clearloop` on the live file (fresh-pulled to
> `aa5cd6a94f`) returns 0 hits; the only remaining corpus hit is the internal non-client-facing
> `elysium-carveout-deferral-message-2026-08-11.md`, out of client-artefact scope.

```
strategy-service-deep-dive.html:620   "...Copper, whose ClearLoop service lets collateral be traded at a venue..."
strategy-service-deep-dive.html:633   SVG alt text: "...which for Copper includes ClearLoop mirroring collateral..."
strategy-service-deep-dive.html:668   SVG label: "on-chain send · ClearLoop / OES mirror"
strategy-service-deep-dive.html:720   callout heading: "Where Copper, ClearLoop and Ceffu actually sit"
strategy-service-deep-dive.html:723   "...mirrored onto the exchange by Copper's ClearLoop service..."
strategy-service-deep-dive.html:727   "...and no ClearLoop-specific code path, and that is by design."
```

This is not an isolated slip — §05 ("Capital, collateral and custody") is built around a callout titled *"Where
Copper, ClearLoop and Ceffu actually sit"* that names the mechanism as central content. `client_artefact_remediation_2026_08_18.md`
states plainly, for the two documents it governs: *"Both artefacts: no commercial figures, never name ClearLoop."*
`nick_ai_platform_disclosure_artifact_2026_08_16.md`'s disclosure boundary separately states *"No third-party
commercial relationships named without an explicit operator ruling."* I found no operator ruling anywhere in the
corpus that explicitly clears "ClearLoop" for client-facing disclosure — the closest is
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §H.10/H.11, which discusses ClearLoop
extensively but frames it as an **accuracy** question (the mirroring capability the documents describe isn't
actually coded — "there is no mirroring call, while the Ceffu equivalent exists" — flagged there as an operator
escalation about wording, explicitly **not** a licence to keep the wording as-is). This document is one of the
"three documents...in the client's hands or about to be" per that same plan's opening line, so this is live,
in-scope client-facing content. **This is the single highest-confidence finding in this audit.**

### Finding D2 — a performance figure (vague but real) repeated across two documents

> **Resolved 2026-08-19 (slot 10, review)** — 0 hits for the "consistent positive annualised returns" phrase in
> either file; the 4 remaining `annualised` occurrences in `platform-architecture.html` are metric labels / a
> market-fact borrow rate / methodology notes, not performance claims.

`elysium_carveout_stubbed_strategy_service_2026_08_12.md` §C states the one hard prohibition on the Elysium
artefacts: *"No performance figure anywhere until the overlays land. The research Sharpe belongs to the 8-overlay
book; production runs 2 (Elysium plan §H.16)."* Both `platform-architecture.html` and the ODUM Phase2 email carry a
near-identical performance claim:

```
platform-architecture.html:3290-3292
  "...we are increasingly confident the strategies generate consistent positive annualised returns, generally
  ranging from single digits into double digits depending on market conditions."

ODUM_Elysium_Phase2_Update_2026-07-24.html:114-116
  "...we're increasingly confident the strategies generate consistent positive annualised returns, generally
  ranging from single digits into double digits depending on market conditions."
```

The wording is close enough to have come from one source and been pasted into both. Two reasons this is more than a
style nit: (1) it is a real performance figure — a wide range, but a disclosed range of annualised returns
nonetheless — sent in documents governed by a rule that says none should appear yet; (2) `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`
§H.16 (audited 2026-08-12, after `platform-architecture.html`'s 11 Aug issue date but describing a state that
already existed) found **production runs only 2 of the 8 overlays the research book's Sharpe/drawdown figures were
measured with** — "No client-facing performance claim may cite the research book's numbers while production runs a
subset." Whether the disclosed range traces to the 8-overlay research book or the 2-overlay production book is not
stated in either document, which is exactly the ambiguity the H.16 finding warns against. `carveout-engineering.html`
and `strategy-service-deep-dive.html` are clean on this — no performance/return/Sharpe/drawdown language found in
either.

### Minor, not flagged as a violation

`ODUM_Elysium_Phase2_Update_2026-07-24.html` contains "at no additional cost" (Deribit venue) and "None of that
additional work has increased the project cost to you" — commercial-adjacent language but with no dollar amount,
percentage or figure attached. I read these as outside the letter of "commercial/budget/funding/valuation/ARR
**figures**" (the rule's own examples are all numeric) and am not flagging them as violations, but noting them since
they sit close to the line.

---

## Accuracy findings — severity-ranked

### P0 — `platform-architecture.html` asserts a Solana/Drift staked-basis capability that does not exist

> **Resolved 2026-08-19 (slot 10, review)** — the present-tense "runs on Solana against Drift, posting jitoSOL and
> mSOL" paragraph is gone (cut outright); 0 `mSOL` / `Drift`-DEX hits, and the one residual `jitoSOL` mention
> (line 1332) is a hedged "requires the perp venue to accept them first" boundary note, not a capability claim.

```
platform-architecture.html:1232-1237
  "Worth noting what the same machinery does elsewhere, because it is the clearest evidence that the venue layer
  is genuinely registry-driven rather than hand-built per venue: the identical staked-basis structure runs on
  Solana against Drift, posting jitoSOL and mSOL as margin. Different chain, different staking protocol, different
  LST, no bespoke engine — the registry row differs and the leg builder adapts."
```

This is stated as present-tense, currently-working fact. It directly contradicts two confirmed findings already on
record in the owning plan:

- `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §H.7 (measured 2026-08-12): *"DRIFT was
  removed from the UAC `VENUE_COLLATERAL_MATRIX` on 2026-07-16 in the Solana-perp-DEX cull, and
  `catalog_staked_basis.py` records that no other live venue accepts JitoSOL or mSOL as `LST_AS_MARGIN`... the
  effect is that SOL staked basis is structurally unavailable, not merely unfunded."*
- Same plan §H.9 (verified 2026-08-12 against the live UAC collateral registry): *"No perp venue anywhere in the
  registry accepts JitoSOL, mSOL, bSOL or even plain SOL as margin."* Jupiter was separately checked and confirmed
  not to restore it either (no LST accepted as perp margin on Jupiter).

The DRIFT removal (2026-07-16) predates `platform-architecture.html`'s own "Issued 11 Aug 2026" date by about a
month, so this was already false on the day the document was issued, not a claim that went stale afterward.
Separately, `elysium_carveout_stubbed_strategy_service_2026_08_12.md` §A3 (2026-08-16 ruling) places "all Solana
DeFi/DEX work (Jupiter perps, Kamino borrow, Marinade...)" **explicitly out of the contracted Elysium scope**
entirely — so even setting the Drift-removal fact aside, citing a Solana/Drift example as evidence of platform
capability sits awkwardly next to the ruling that this exact venue family is out of scope for this client. By
contrast, `carveout-engineering.html` §08 lists Hyperliquid/Drift/Aster correctly as **future roadmap** extension
items ("More perpetual venues"), never as working capability — the two documents are inconsistent with each other
on this point, and `platform-architecture.html` is the one that is wrong.

### P0 — `strategy-service-deep-dive.html` §05/§07 repeats the completed audit's highest-severity transfer-wiring finding, undisclosed

> **Resolved 2026-08-19 (slot 10, review)** — §07 now carries an inline caveat ("Transfer netting and custody
> routing … are not yet wired end-to-end in production — see the caveat in §05"), and §05's pipeline is graded
> `planned`/`partial`; the overstatement is now disclosed rather than presented unconditionally.

The completed first-pass audit's top P0 finding for `strategy-service-walkthrough.html` was: *"§11 'Automated
movement' overstates reachability — no production transfer path exists"* — verified against
`execution-service/execution_service/transfer_coordinator.py` that only `SUBACCOUNT_MOVE` auto-registers a handler,
`CEX_WITHDRAW` is commented "NOT WIRED," and `TransferCoordinator` is never instantiated in production code.

`strategy-service-deep-dive.html` carries the same substance, more prominently, with **no caveat at all**:

- §05 ("Capital, collateral and custody," lines 616–736) is built around Figure 1, a diagram showing
  `Strategy → Netting (IntraClientRebalanceCoordinator) → TransferCoordinator → CompositeTransferAdapter → Venue
  API / Custody` as a smoothly working pipeline, captioned "the full path from a strategy's rebalance request to
  funds arriving" with no wiring-status qualifier anywhere in the section.
- §07's "What applies without you writing it" bullet list (line 847) names **"Transfer netting and custody
  routing"** as a capability that "applies without you writing it" — the identical overstatement the audit already
  flagged, restated as a blanket guarantee in a different document.
- The same bullet list (line 845) also states **"Capital budget enforcement per instance"** unconditionally — this
  claim is still `UNVERIFIED` per `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §B (open
  P0: "no guard was read that refuses an instruction exceeding it"), and is a still-open P2 softening todo in
  `client_artefact_remediation_2026_08_18.md` §A for the sibling walkthrough — this document was never touched by
  that remediation plan and carries the same unqualified claim.

This is the strongest instance in either sibling file of a known, already-flagged-elsewhere error propagating to a
document no active remediation plan currently covers.

### P1 — `platform-architecture.html` presents a "reserve ratio" capital mechanism with no confirmed code behind it

> **Resolved 2026-08-19 (slot 10, review)** — §10 is now graded `partial` + `~ assumed`, so the 20%/10%/30%
> thresholds are no longer presented as confirmed. The underlying "does reserve-ratio behaviour exist" verification
> (`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §H.15) remains a separate open todo.

```
platform-architecture.html:1175
  "reserve ratio     target ≈ 20%   ·   floor ≈ 10%   ·   ceiling ≈ 30%   (configurable)"
```
(In the "Your slots — structure, collateral and build stage" plate, §03.)

`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §H.15 carries this still-open todo: *"Verify
`reserve_ratio`-style behaviour exists or retire the concept. **Zero hits fleet-wide**, yet an early document draft
described capital moving 'on a reserve ratio'. Find it under its real name or confirm absence."* I could not find
`reserve_ratio` (or an equivalent named mechanism) confirmed to exist anywhere in this workspace's plan/codex
corpus — the owning plan's own investigation found zero code hits and left the question open. This document
presents specific numeric thresholds (20%/10%/30%) for a mechanism the plan's own audit has not yet confirmed
exists. Given the todo's phrasing ("an early document draft described capital moving 'on a reserve ratio'"), this
passage is a strong candidate for being that exact draft — flagging it here so the still-open verification closes
against the right source.

### P2 — the invented "DeFi liquidity provision" strategy-family label recurs, uncorrected, in two sibling documents

> **Resolved 2026-08-19 (slot 10, review)** — "DeFi liquidity provision" returns 0 hits in both files; "liquidation
> capture" no longer appears as a family name (the one residual hit, line 1397, is a correct archetype descriptor
> under the real `ARBITRAGE_STRUCTURAL` family, and the real 9-family table is now present).

The completed audit's clearest single finding was that `strategy-service-walkthrough.html` invented a
non-existent "Liquidity provision" `StrategyFamily` member (real enum has 9: `ML_DIRECTIONAL`, `RULES_DIRECTIONAL`,
`CARRY_AND_YIELD`, `ARBITRAGE_STRUCTURAL`, `MARKET_MAKING`, `EVENT_DRIVEN`, `VOL_TRADING`, `STAT_ARB_PAIRS`,
`PORTFOLIO`) — already corrected in `strategy-service-deep-dive.html` per
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §F, and confirmed correct there in this
audit's own re-read (§02/§08 both show "9 Strategy families declared" with the real 9 names). The exact phrase
resurfaces, uncorrected, in the family-adjacent lists of both other large documents:

```
platform-architecture.html:1284-1286
  "Beyond Carry & Yield the platform also carries arbitrage, statistical arbitrage, DeFi liquidity provision,
  volatility, market making, event-driven, liquidation capture and directional families."

platform-architecture.html:3101-3103
  "...the strategy families outside Carry & Yield altogether — arbitrage, market making, ML-directional,
  event-driven, volatility, statistical arbitrage, rules-directional, liquidation capture, DeFi liquidity
  provision — are outside it entirely."

carveout-engineering.html:1099
  "Non-carry strategies | arbitrage · volatility · stat-arb · DeFi liquidity provision"

carveout-engineering.html:1183
  "...archetypes across every family — carry and yield, structural arbitrage, statistical arbitrage, volatility,
  market making, ML- and rules-directional, event-driven and portfolio, including DeFi liquidity-provision
  archetypes..."
```

Two things temper this finding relative to the walkthrough's original error: neither document asserts a specific
total family count next to these lists (the walkthrough's error was "5 families" including the invented one; these
lists are open-ended prose, not a numbered claim), and "DeFi liquidity provision" may be intended as an informal,
archetype-level descriptor rather than a literal `StrategyFamily` name. But the term is the *exact* fabricated
phrase already identified and corrected elsewhere, "liquidation capture" similarly does not map to any of the 9 real
family names, and `PORTFOLIO` — a real family — is never mentioned in any of the four lists above. Given the
already-established pattern (this precise phrase was invented once and had to be corrected), I'd flag this as a
likely repeat rather than an independent, unrelated choice of words, but calibrate it below the P0/P1 findings above
because it is not phrased as a specific, falsifiable count the way the original error was.

### P2 — `platform-architecture.html`'s readiness claims were never re-graded against the 2026-08-18 stricter `live` definition, and use self-reported percentages the corpus otherwise treats as a hard-rule violation

> **Resolved 2026-08-19 (slot 10, review)** — `platform-architecture.html` now carries rule-13 status + evidence-tier
> grading (25 `.st`/`.ev`/`~ assumed`/`? check` markers); §13's self-reported readiness percentages are graded
> `partial` + `? check`, not `live`/`verified`.

`nick_ai_platform_disclosure_artifact_2026_08_16.md`'s Build section carries an open P0 todo: *"Re-grade every
section mark in BOTH artefacts against the STRICTER `live` definition (operator, 2026-08-18): `live` now means
reachable on a production path AND validated with real capital... expect most `live` marks to drop to `partial`."*
That todo is scoped to "BOTH artefacts" — the two documents the completed audit covers
(`platform-external-api-walkthrough.html`, `strategy-service-walkthrough.html`) — and does not mention
`platform-architecture.html`, even though that document runs its own parallel readiness-grading system throughout
(the 1–4 "dots" scale in Figure 2 and the percentage table in §13) and marks the two contracted strategy engines
"production-validated" (4 dots) and lists "Strategy research 100%," "Execution engine 90%," etc. — self-reported,
declared figures with no citation to the honest-coverage or readiness-state-dump machinery that the completed audit
confirmed the other two artefacts now derive their readiness language from ("Readiness derived, never declared" —
landed cleanly in both audited documents). This document's readiness claims predate that discipline and were never
brought into it. Not a confirmed factual error (I could not independently re-derive Elysium's narrow 4-venue slice's
true readiness state in this task), but a scope gap: this document carries the same class of claim the operator's
ruling was written to govern, and no active plan currently re-grades it.

### P2 — the `paper − batch = 0` hard-equality claim is stated unconditionally, same open caveat as the audited sibling

> **Still open 2026-08-19 (slot 10, review)** — no sibling-plan fix; the `paper − batch = 0` caveat for
> `platform-architecture.html` is not covered by `client_artefact_remediation_siblings_2026_08_18.md`. Already
> tracked in `client_artefact_remediation_2026_08_18.md` §A + `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §H.8.

`platform-architecture.html` §05 (Figure 3, line 1523: `"paper − batch = 0"`, captioned "a proof, not a
tolerance") states the equality without qualification. `client_artefact_remediation_2026_08_18.md` §A already
carries this open todo for the sibling walkthrough: *"Add a caveat near §08/§09's hard equality claim — `paper ==
batch-rerun` is asserted unconditionally, but... the now-default-ON dynamic universe currently lacks the
manifest-pinning needed to guarantee this exactly when the universe resolution date differs between runs."* That
gap (`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` §H.8, still open P0) applies equally
here and is not mentioned anywhere in `platform-architecture.html`.

### P3 — promotion-ladder terminal state asserted as settled in two documents, still unconfirmed

> **Still open 2026-08-19 (slot 10, review)** — no sibling-plan fix; the four-rung ladder's terminal full-live state
> remains unconfirmed. Already tracked in `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`
> (open P1).

Both `strategy-service-deep-dive.html` §09 ("Candidate → paper → early live → live") and `platform-architecture.html`
§11 (Figure 9's "candidate, then one-day paper, then early live, then full live") state the same four-rung ladder
as settled fact. `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`'s claims-audit table marks
this `PARTIAL` — `CANDIDATE`, `PAPER_1D` and `live_early` were found in code, but "no terminal full-live state
confirmed" — and carries an open P1 todo to confirm it or correct the documents. Neither document reflects the
open status.

### Positive findings — worth recording, not just gaps

- `strategy-service-deep-dive.html` §02/§08 state **11 instruction types** and the real **9-member `StrategyFamily`
  list** correctly, matching the audit's confirmed ground truth and the already-applied correction in this same
  document per October-delivery plan §F. No error here.
- `strategy-service-deep-dive.html` §05 (line 710) states the custody-provider roster as `mock · local_key ·
  cloud_kms · copper · ceffu` — this is the **correct, working roster**, matching
  `execution-service/execution_service/custody/factory.py` exactly as confirmed in the completed audit. The sibling
  `strategy-service-walkthrough.html` was found to have this wrong (shows Fireblocks, omits Ceffu) — this document
  does not repeat that error.
- `carveout-engineering.html`'s "11 components" (§02) and "10 interface contracts" (§04) match exactly what
  `elysium_carveout_stubbed_strategy_service_2026_08_12.md` describes as already correct ("§04 already states each
  of the ten interfaces 'resolves to a local, static or mock implementation'... what §04 needs is precision, not a
  new structure") — no drift found against that plan's own audit.

---

## Cross-document contradictions with the two audited documents

1. **Custody roster**: `strategy-service-deep-dive.html` (correct: mock/local_key/cloud_kms/copper/ceffu) versus
   `strategy-service-walkthrough.html` (confirmed wrong by the completed audit: shows Fireblocks, omits Ceffu). Same
   underlying fact, two different documents disagree with each other because one is right and one is wrong.
2. **Transfer-wiring overstatement**: present in both `strategy-service-walkthrough.html` (already flagged P0 by
   the completed audit, open remediation todo) and, more prominently and entirely undisclosed, in
   `strategy-service-deep-dive.html` §05/§07 (this audit's finding above) — the same underlying system gap, now
   confirmed to affect a second, unaudited document.
3. **Instruction-type count / family list**: `strategy-service-deep-dive.html` has both correct; the original error
   this audit's sibling `strategy-service-walkthrough.html` carried (9 types, invented "Liquidity provision" family)
   does not reappear here — but a related, softer version of the family-name drift ("DeFi liquidity provision," "liquidation
   capture") reappears in `platform-architecture.html` and `carveout-engineering.html` (finding above).
4. **Solana/Drift staked basis**: not discussed in either already-audited document, but directly contradicted by
   the owning plan's own H.7/H.9 findings (finding above) — this is a contradiction against the *plan's* confirmed
   ground truth rather than against the other two artefacts.
5. **Readiness "derived, never declared"**: the completed audit confirmed this operator ruling "landed cleanly and
   consistently" in both audited documents. `platform-architecture.html` was authored before that ruling existed
   (11 Aug 2026 vs. the ruling's 2026-08-18 date) and was never brought into line with it — not a contradiction of a
   fact so much as a document that predates a standard the corpus has since adopted elsewhere.

---

## What I could not verify

- The specific figure "over a thousand real trades... zero deviation" (appears near-identically in
  `platform-architecture.html` §05 and the ODUM Phase2 email) — plausible given the confirmed batch=live
  determinism architecture, but I had no way to independently check the trade count or deviation result in this
  read-only task.
- Whether "liquidation capture," used as a family-adjacent label in `platform-architecture.html`, maps to a real
  archetype somewhere in the 60-member `StrategyArchetype` enum — I did not enumerate all 60 members to check.
- The true current readiness state of the Elysium-scoped 2-archetype/4-venue slice against the 2026-08-18 stricter
  `live` definition — flagged as a scope gap above, not independently re-derived here.
- Full line-by-line coverage of `platform-architecture.html` §06–§10 and §12 (roughly 1,100 of the file's 3,317
  lines) — covered by targeted `rg` sweeps for the specific terms this task and the owning plans flag as
  load-bearing, not by direct reading. A finding could exist in that unread prose that these sweeps did not surface.
- Whether the "reserve ratio ≈20%/10%/30%" figures in `platform-architecture.html` trace to a real internal
  convention under a different name, versus being genuinely invented — the owning plan's own todo is still open on
  this exact question; I did not resolve it, only located what is very likely the source text the todo refers to.

## Progress Log

**2026-08-18 — audit complete.** One of 5 parallel second-pass audit agents. Read both owning plans in full (963 +
428 lines), the carve-out plan in full (412 lines), the remediation plan in full (244 lines), and the completed
first-pass audit in full (374 lines) as ground truth before touching any of the four target files.
`strategy-service-deep-dive.html` and `ODUM_Elysium_Phase2_Update_2026-07-24.html` read in full;
`platform-architecture.html` and `carveout-engineering.html` covered by full-section reads plus exhaustive
term-targeted `rg` sweeps, per the size/time budget instruction. No file edited; this report is the only file
created.
