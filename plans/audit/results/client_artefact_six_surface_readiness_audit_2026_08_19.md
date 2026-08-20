---
doc_type: audit-result
title: Six-surface × three-mode readiness picture for the client artefacts — 2026-08-19
summary: >-
  Builds the per-venue readiness picture across the six surfaces (market data, position, orders, fills, trades,
  account balance) and three modes (batch, paper, live) the operator named in system_readiness_master.md W1's
  2026-08-19 ruling, using only already-shipped machine checks (readiness-state-dump's 8-leg model, honest-coverage-
  dump). One shared audit feeding both client artefacts, per the same ruling — not duplicated per file. States
  honestly which of the 18 (surface × mode) cells are derived, which are unverified, and which have no check at all,
  then checks both artefacts' current text against that picture for claims that outrun what has actually been
  measured (W21's own defect definition).
status: pass
nature: record
audited_scope: >-
  The six-surface readiness matrix defined in /plans/epics/system_readiness_master.md § W1 (2026-08-19 ruling),
  mapped against the shipped readiness-state-dump 8-leg model and honest-coverage-dump, then checked against the
  current text of platform-external-api-walkthrough.html (Nick AI) and strategy-service-walkthrough.html (Elysium)
  for any claim the derived state does not support. No code changed; no HTML or plan edited to produce this report.
date: 2026-08-19
auditor: >-
  Interactive session (slot 6), direct source reads (epic, both SKILL.md docs, both artefact HTML files, three prior
  2026-08-18 audit docs) — no sub-agents dispatched, no new measurement run (all cited figures are quoted from
  already-shipped skill runs per the dispatching operator's instruction, not re-derived).
severity: P1
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
asset_group: [cross-cutting, defi, cefi, tradfi, sports, prediction]
stage: [data, strategy, execution, meta]
repos: [unified-trading-pm, unified-api-contracts, instruments-service, market-tick-data-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [client-disclosure, nick-ai, elysium, readiness, six-surface, measurement-claims-discipline, system-readiness]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
    /plans/audit/results/client_artefact_cross_document_consistency_2026_08_18.md,
    /plans/audit/results/planning_corpus_assumption_delta_audit_2026_08_18_recheck.md,
    /plans/active/client_artefact_remediation_nickai_2026_08_18.md,
  ]
created: 2026-08-19
source: >-
  Dispatched by the orchestrating session per operator ruling 2026-08-19: "ONE audit feeds BOTH client artefacts —
  not one per artefact." Task brief supplied the five measured figures quoted below with an explicit instruction not
  to re-derive them.
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /cursor-configs/skills/readiness-state-dump/SKILL.md,
    /cursor-configs/skills/honest-coverage-dump/SKILL.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
---

# Six-surface × three-mode readiness picture — 2026-08-19

**Read-only audit. No HTML, plan, or epic file was edited to produce this report.** Per the dispatching operator, this
is the one shared audit that feeds both `platform-external-api-walkthrough.html` (Nick AI) and
`strategy-service-walkthrough.html` (Elysium) — not two per-artefact audits. Applying any recommendation below to
either HTML remains a separate, operator-reviewed step per both owning plans' "operator reviews all numbers before
they reach a client" gate.

## Why this doc exists, precisely

`system_readiness_master.md` § W1 records a **2026-08-19** ruling: readiness is not one number, it is **18 cells** —
six surfaces × three modes, per venue, split by owning service. That ruling is one day newer than the readiness
content currently in either artefact (both dated 2026-08-18). This audit is the bridge: it states what the 18 cells
actually look like today, using only checks that already exist, so the next artefact edit either (a) matches the
six-surface framing honestly, cell for cell, or (b) is deferred until the W1 P0 backend todos below land. Per W21:
**an artefact claim that outruns the derived state is a defect, not a presentation choice.**

## Method

No new measurement was run. Every quoted figure below is reused verbatim from already-shipped, already-run sources,
per the dispatching operator's explicit instruction: `readiness-state-dump` and `honest-coverage-dump`'s own
`SKILL.md` documents (which describe, leg by leg, what is fact vs. proxy vs. absent), the epic's own W1 table, and
the 2026-08-18 `planning_corpus_assumption_delta_audit` re-check (the most recent live run of both skills). The two
artefact HTML files were read directly (not grepped-only) at their readiness-bearing sections — Nick AI §14 "Measured
readiness — 2026-08-18" (lines 2180-2353) and Elysium §06 and §18 (lines 1311-1370, 2211-2288) — to quote their
current text exactly rather than paraphrase it.

---

## Part 1 — The six surfaces, mapped to what actually checks them

The epic's own table (W1, reproduced for this audit's grounding):

| Surface | Owning service | Batch | Paper | Live |
| --- | --- | --- | --- | --- |
| **market data** | MTDS | derived (fact) | unverified | unverified |
| **position** | strategy-service | derived (fact) | derived (fact) | derived (fact) |
| **orders** | execution-service | no check | no check | no check |
| **fills** | execution-service | no check | no check | no check |
| **trades** | execution-service | no check | no check | no check |
| **account balance** | execution-service | no check | no check | no check |

**Of 18 cells: 4 are derived (market data × batch, position × all three modes), 2 are unverified (market data ×
paper/live), and 12 have no check at all (orders/fills/trades/account balance × all three modes).**

### market data (MTDS) — batch derived, paper/live have no independent leg

The shipped `market_tick_data` leg (`readiness-state-dump` `SKILL.md`) reads `coverage.json`'s `captured` counts per
observed data_type — a real, observed-capture fact for **batch**. For paper and live, the same leg always reports
`unverified`, and the reason is structural, not a missing implementation detail: **`coverage.json` is not
mode-partitioned**, so there is no data source from which a paper- or live-specific capture state could be read even
in principle. The epic's own W1 table calls this "no live-feed check exists" — functionally the same statement:
whatever the row prints, nothing has actually verified market data reachability for paper or live.

Per [`paper-batch-live-reconciliation.md`](/codex/09-strategy/operational/paper-batch-live-reconciliation.md) § 0,
**paper always consumes the live market-data feed** — testnet is an execution sub-mode, not a separate price source.
So the honest open question is really two-valued, not three: "does batch have data" (yes, measured) and "is the live
feed itself reachable" (no check exists for this at all today) — a paper-specific market-data leg would be
redundant with the live-feed leg once the live leg exists, per that same ruling.

### position (strategy-service) — the one surface genuinely checked across all three modes, but its published rollup is confounded with a second axis

`position_read_mode_availability(venue) -> PositionReadModeAvailability` is a real, audited, per-(venue, mode) table
(`strategy-service`'s own code) — a fact, not a proxy, per the skill's own tier language. This is the one surface
where all three W1 cells are genuinely derived.

**But the only published rollup number that touches this surface is the readiness-state-dump's combined `strategy`
leg — 24 of 864 pass — and that number is an AND of two different checks, not position readiness alone**: the
position-adapter half (this surface) AND a second, unrelated check (whether at least one strategy archetype's full
`FEATURE_REQUIRED_INPUTS` is satisfiable from that venue). The 2026-08-18 re-check audit's own explanation of the
24/864 figure ("dominated by archetypes whose input declarations are deliberately incomplete rather than by venues
that cannot trade") already says, in effect, that archetype-availability is the dominant constraint in that number —
which means **the 24/864 figure cannot be read as "position readiness passes on 24 venue-modes."** Position's own
cell-level state is real and derivable in principle, but no currently-published number isolates it from the
archetype half. This is not a defect in the underlying check — `position_read_mode_availability` itself is sound —
it is a gap in what the rollup discloses.

### orders, fills, trades, account balance (execution-service) — no check at all, and the two adjacent legs that could be mistaken for one

The 8-leg model's two execution legs are `execution_transfers` and `execution_instruction`. Neither is a check on
any of these four surfaces:

- **`execution_transfers`** checks `VENUE_WALLET_CAPABILITIES` registry membership — a proxy for whether a venue's
  wallet/transfer *structure* is declared, not whether an order can be placed, a fill observed, a trade recorded, or
  an account balance read back. Per the skill's own tier language, absence gives a real `not_ready`, but presence is
  only `unverified` — it does not confirm a working rail, let alone the four operational surfaces above.
- **`execution_instruction`** has **no check wired anywhere in the fleet** (`SKILL.md`: *"(none wired yet)"*) and
  reports `unverified` on all 864 rows, unconditionally. It is the closest thing to an "orders" leg in name, but it
  is not one — there is no code path anywhere that reads it as anything but always-unverified.

**A capability exists adjacent to "account balance" that is easy to conflate with it**: `strategy-service`'s
`BasePositionAdapter.get_balances()` / `get_account_snapshot()` (Elysium artefact §07, `strategy-service-walkthrough
.html` lines 1386-1389) is real, shipped code that reads balances and account snapshots — but it serves the
**position** surface (strategy-service-owned, for reconciliation), not the **account balance** surface W1 names
(execution-service-owned). Same word, two different owning services and purposes; neither reading confirms the
other. Worth naming explicitly if either artefact ever states an account-balance claim, so a reader does not credit
the wrong service's capability.

**Net: orders, fills, trades and account balance readiness genuinely has zero machine check today** — not a proxy,
not an `unverified` leg, nothing. This is exactly what the epic's own W1 table already states; this audit's
contribution is confirming there is no artefact-adjacent capability that could be mistaken for filling that gap
except the one balance-reading conflation noted above.

---

## Part 2 — The measured figures this audit quotes, not re-derives

Per the dispatching operator's instruction, these five figures are quoted as-measured, from the sources named:

- **660 (venue, instrument_type, data_type) triples, 12 unresolved** — the declared-capability denominator
  (`generate_venue_universe_denominator.py`, landed `unified-api-contracts@d19866d339`, W3). This is a **capability
  declaration count**, not a readiness verdict and not a coverage measurement — it answers "how many
  (venue, instrument_type, data_type) combinations does the registry declare," with 12 of those (3.4% of shown by
  the 2026-08-18 re-check) disclosed as unresolved rather than silently dropped.
- **48.54% reachable, volume-weighted, denominator 119,500,618, over 3,960 shards** — `honest-coverage-dump`'s Layer-2
  capture measurement, a **data-availability** figure (captured / (captured + attempted_failed +
  expected_unattempted)), feeding the `instruments_service` and `market_tick_data` legs above. **This is a different
  denominator from the 660-triple figure** — 3,960 is the shard count actually enumerated in the coverage manifest at
  its current grain; 660 is the declared-capability triple count. The 2026-08-18 re-check confirmed the
  instrument_type-axis landing does not yet feed either dump (`expected_universe.py` never read
  `VenueCapabilityRecord`), so the two numbers should not be read as reconciled versions of the same count — they
  answer different questions and currently move independently.
- **Readiness rollup 0 / 844 / 20 across 288 venues × 3 modes = 864 rows** — `readiness-state-dump`'s overall
  verdict (`checks.rollup()`): a venue-mode is `not_ready` if any of the 8 legs fails, `ready` only if every leg
  passes, `unverified` otherwise. This is the **8-leg model's** rollup, not the six-surface model's — see Part 3 for
  why the two are not directly interchangeable.
- **Strategy leg 24/864** — see Part 1 § position above: an AND of position-adapter availability and
  archetype-input satisfiability, dominated by the archetype half per the 2026-08-18 re-check's own reading.

None of these five figures was re-run for this audit; all are reused from the sources cited in each bullet and in
this doc's `related` frontmatter.

---

## Part 3 — The 8-leg model is not the six-surface model, and neither artefact currently says so

The readiness-state-dump's 8 legs (`declared`, `instruments_service`, `market_tick_data`, `market_data_processing`,
`features`, `strategy`, `execution_transfers`, `execution_instruction`) were built before the 2026-08-19 six-surface
ruling and answer a genuinely different question: "can this venue support at least one strategy archetype end to
end," a pipeline-completeness question. The six-surface model asks a narrower, more client-legible question per
surface: "can I see this venue's market data / positions / orders / fills / trades / balance, in this mode." The
two overlap only at `market_tick_data` (→ market data) and partially at `strategy` (→ position, confounded per
Part 1). **Four of the six surfaces (orders, fills, trades, account balance) have no corresponding leg in the
8-leg model at all** — not a weak leg, an absent one.

This mapping gap is not itself a fabricated claim in either artefact — neither document currently states or implies
that the 8-leg model equals six-surface coverage. But it is the reason the artefacts' current 864-row content cannot
be read as answering the operator's actual six-surface question, and the reason a future edit that simply relabels
the existing 8-leg table as "the six surfaces" would be a new, real defect (an artefact number outrunning the
derived state, per W21) rather than a harmless rename.

---

## Part 4 — What each artefact currently claims, checked against the picture above

### Nick AI (`platform-external-api-walkthrough.html` §14, "Measured readiness — 2026-08-18")

**Already disclosed honestly, within the 8-leg frame it uses**: the section states plainly that readiness is
"computed, not declared," that an unchecked leg reports `unverified` rather than a silent pass, names the 8-leg
model explicitly by leg name (including `market_tick_data`, `execution_transfers`, `execution_instruction`), states
the execution-instruction leg is unverified on all 864 rows, and states the strategy leg passes 24/864 with a
one-line explanation. This is a genuinely careful section — it does not claim orders/fills/trades/account-balance
coverage, and it does not claim market data is checked live. **No false statement was found in this section.**

**What it does not yet say, and per W21 should before it is read as the operator's six-surface answer**:

1. It never names the four surfaces (orders, fills, trades, account balance) that have zero check — a reader who
   knows "execution transfers" and "execution instruction" exist as legs, and reasonably assumes "execution"
   colloquially covers order placement and fill/trade recording, would come away believing more is checked than is.
   The section does not say this explicitly, but it also does not say the opposite, and the epic's own table now
   does. Recommend the artefact add the same explicit "no leg" language the epic uses for these four, rather than
   leaving a reader to infer it from two proxy-leg names that do not obviously map to them.
2. It does not disclose that the `market_tick_data` leg is **batch-only by construction** — a reader sees "market
   data" listed as one of 8 legs feeding a pass/fail verdict and has no signal that paper/live rows for this leg are
   structurally unable to resolve, as opposed to a check that simply hasn't been run yet. The distinction matters:
   one is "not measured yet," the other is "cannot currently be measured with the data this system captures."
3. The 24/864 strategy-leg figure is presented as one number with one line of framing ("dominated by archetypes...
   rather than venues that cannot trade") — accurate as far as it goes, but it does not tell a reader that this
   figure cannot be decomposed into a position-readiness number today. Given position is the one surface where a
   real per-mode fact exists, this is the cell most worth being precise about, not the one to leave folded into a
   compound figure.

None of the three points above is a false statement in the artefact today. They are the gap between "honest within
the frame it chose" and "answers the six-surface question the operator asked one day later" — exactly the kind of
gap this audit exists to surface before an editor closes it by simply relabeling existing numbers.

### Elysium (`strategy-service-walkthrough.html`)

**Carries no readiness-matrix content at all.** §18 ("What is still open") is qualitative — it lists open work by
area, including "Audit: extending the immutable record from the manual path to automated orders, fills and
instructions" (line 2247), which is a statement about audit-trail completeness, not a readiness verdict, and should
not be read as a claim that orders/fills readiness has been measured. No overclaim was found, because no claim was
made — the gap here is silence, not a false statement.

**Terminology note worth flagging before either artefact's readiness language is extended**: Elysium §06 is titled
"Venue coverage: three surfaces, tracked apart" (line 1314) and uses "surface" for a different concept entirely —
whether a venue's data capture, position read, and execution wiring are each independently true for that venue. This
is a real, useful distinction in its own right, but it is not the W1 "six surfaces" (market data / position / orders
/ fills / trades / account balance). If a future edit introduces the six-surface table into either artefact, the two
uses of "surface" in the same document (or across the two sibling documents, since a reader may see both) should be
disambiguated — e.g. naming Elysium's existing concept "tracks" or "capability axes" — rather than left to collide.

Per the operator's ruling that one audit feeds both artefacts: since Elysium currently states nothing on this axis,
there is nothing here to correct, but also nothing here yet that reflects the shared picture this audit describes.
Whether Elysium should gain six-surface content (and if so, scoped to its four-venue CeFi-only carve-out or the
full repository, per the disclosure-boundary question already open in the 2026-08-18 audit) is an editorial
decision for the operator, not something this audit resolves.

---

## Part 5 — Summary: cells derived, unverified, and uncheckable, stated once

| Surface | Batch | Paper | Live | Published rollup number available? |
| --- | --- | --- | --- | --- |
| market data (MTDS) | **derived** — `coverage.json` captured counts | **unverified** — not mode-partitioned, structurally unresolvable today | **unverified** — same | No per-surface number; folded into the 8-leg rollup only |
| position (strategy-service) | **derived** — `position_read_mode_availability` | **derived** — same, real per-mode fact | **derived** — same | No — the only published number (24/864) is confounded with archetype-satisfiability |
| orders (execution-service) | **no check** | **no check** | **no check** | No |
| fills (execution-service) | **no check** | **no check** | **no check** | No |
| trades (execution-service) | **no check** | **no check** | **no check** | No |
| account balance (execution-service) | **no check** | **no check** | **no check** | No — a same-named but differently-owned capability exists on the position side only (Part 1) |

**4 of 18 cells derived, 2 unverified-by-construction, 12 with no check at all.** This matches the epic's own W1
framing exactly; this audit's contribution is the artefact-facing detail (which published numbers can and cannot be
read as answering each cell) needed to check the two client documents against it.

## What this audit did not do

- Did not run either skill fresh — all figures are quoted, per the dispatching brief's explicit instruction.
- Did not decompose the 24/864 strategy-leg figure into a pure position-readiness count — that decomposition does
  not exist in any currently-published output; building it is a W1 P0 backend todo (epic line 194-197), not
  something this audit could derive from existing artifacts.
- Did not edit `system_readiness_master.md`, either artefact's HTML, or either owning plan. This report is the
  input to that editorial decision, not the edit itself.
- Did not re-check the four sibling artefacts (`platform-architecture.html`, `carveout-engineering.html`,
  `strategy-service-deep-dive.html`, `ODUM_Elysium_Phase2_Update_2026-07-24.html`) — out of scope per the
  dispatching brief, which named the two lead artefacts specifically; the 2026-08-18 cross-document audit already
  covers those six for a different claim set (instruction counts, family names, custody rosters).

## Progress Log

**2026-08-19 — audit complete.** Built the six-surface × three-mode readiness picture named in
`system_readiness_master.md` § W1's 2026-08-19 ruling, using only already-shipped checks (`readiness-state-dump`'s
8-leg model, `honest-coverage-dump`'s Layer-2 measurement) — no new measurement run, all five brief-supplied figures
quoted verbatim with their sources. Found 4 of 18 cells derived, 2 structurally unverified (market data ×
paper/live), 12 with no check at all (orders/fills/trades/account-balance × all three modes) — matching the epic's
own table. Checked both lead client artefacts against this picture: Nick AI's §14 makes no false statement but
omits the four uncovered-surface names, the market-data batch-only caveat, and the strategy-leg's confound with
archetype-satisfiability — three W21-relevant gaps between "honest within its own 8-leg frame" and "answers the
six-surface question." Elysium carries no readiness-matrix content at all (silence, not an overclaim) and uses
"surface" for an unrelated concept (§06) that would collide with W1's vocabulary if six-surface content is ever
added there. No file other than this one was written or edited.
