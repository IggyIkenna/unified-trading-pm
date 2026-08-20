---
doc_type: audit-result
title: Client artefact cross-document consistency + mechanical integrity audit — second-pass audit 2026-08-18
summary: >-
  First cross-document sweep across all six client-disclosure artefacts (prior passes audited each document in
  isolation). Confirms the known strategy-family/instruction-count doc-drift as still live, then finds two much
  larger versions of the same failure mode that no prior pass looked for: the invented "Liquidity provision"/"DeFi
  liquidity provision"/"liquidation capture" pseudo-family appears in THREE documents, not one
  (`strategy-service-walkthrough.html`, `carveout-engineering.html`, `platform-architecture.html`), and the custody
  Fireblocks/Ceffu mismatch is now a confirmed three-way contradiction (`platform-architecture.html` and
  `strategy-service-deep-dive.html` agree the real stack is Copper+Ceffu with no Fireblocks; only
  `strategy-service-walkthrough.html` shows Fireblocks and omits Ceffu). An exhaustive script-based anchor sweep
  found a second, previously-uncaught instance of the known stale `§08`→`§09` cross-reference in the same file.
  Mechanical integrity is otherwise clean: zero broken internal anchors, zero duplicate ids, and all six files parse
  with balanced open/close tags across two independent validators (a custom Python `html.parser` stack-walker and
  `tidy`, after filtering `tidy`'s HTML5-element false positives from its 2006-era HTML4 ruleset).
status: pass
nature: record
audited_scope: >-
  All six client-disclosure artefacts under codex/14-customer-journeys/commercial-model/ — cross-document factual
  consistency (counts, enum members, status marks, venue numbers, mode vocabulary) and mechanical integrity
  (internal anchor resolution, HTML validity), swept exhaustively across all six for the first time.
date: 2026-08-18
auditor: >-
  1 general-purpose sub-agent (sonnet), dispatched as one of 5 parallel agents doing a second-pass audit of
  client-disclosure artefacts, read-only, SUB_AGENT_MANDATORY_RULES.md pasted at spawn.
severity: P0
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
asset_group: [cross-cutting, defi]
stage: [data, strategy, execution, meta]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
created: 2026-08-18
tags: [client-disclosure, nick-ai, elysium, audit, cross-document-consistency, anchor-integrity]
---

# Client artefact cross-document consistency + mechanical integrity audit — 2026-08-18

**Read-only audit.** No HTML file, plan, or issue doc was edited to produce this report. Scope: all six artefacts
under `unified-trading-pm/codex/14-customer-journeys/commercial-model/` —
`platform-external-api-walkthrough.html`, `strategy-service-walkthrough.html`, `platform-architecture.html`,
`carveout-engineering.html`, `strategy-service-deep-dive.html`, `ODUM_Elysium_Phase2_Update_2026-07-24.html`.

## Method

Part 1 (factual consistency) used targeted `grep`/`rg` extraction across all six files for five claim categories
(counts, enum-member lists, status marks, venue numbers, mode vocabulary), followed by direct reads of the matched
regions to get exact wording. `strategy-service-deep-dive.html` (1002 lines) and
`ODUM_Elysium_Phase2_Update_2026-07-24.html` (167 lines) were read in full; the other four were read via
grep-located sections, not line-by-line in full — see § "What I could not verify" for the residual risk this
leaves.

Part 2 (mechanical integrity) was scripted, not sampled: a Python script
(`anchor_check.py`, written to the session scratchpad) extracted every `href="#..."` and every `id="..."` per file
via regex, diffed href-targets against the id set for that same file, and separately ran a custom
`html.parser`-based open/close-tag stack-walker to catch stray closes, mismatched closes, and anything left
unclosed at end-of-file. A second script (`secref_check.py`) extracted every textual `§NN` cross-reference (not
just hyperlinked ones) per file, paired it with that file's own section-heading list, and printed both so each
reference's target topic could be eyeballed against its surrounding sentence. `tidy` (the only HTML validator
installed) was also run per file as a second opinion.

## Section 0 — baseline sanity check: still true

**Confirmed still live as of 2026-08-18.** `strategy-service-walkthrough.html` line 220 (`§01`'s stat-row) still
reads `<span class="v">9</span><span class="k">Instruction types</span>`, and line 314 (`§02`'s keypoints) still
lists the invented 5-family set including `"Liquidity provision"`. Neither fix from
`/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md` § A has landed — that plan's own todos are all still
unchecked `- [ ]`, consistent with this. `strategy-service-deep-dive.html` correctly shows `11` instruction types
(factbar line 162, stat-row line 202) and the correct 9-member family list (stat-row line 204, keypoints line 876:
"Carry and yield, structural arbitrage, statistical-arbitrage pairs, volatility, market making, event-driven,
rules-directional, ML-directional, portfolio" — all 9 real `StrategyFamily` members present, correctly named, no
invented member).

---

## Section 1 — Cross-document factual contradictions (severity-ranked)

| # | Sev | Claim | File A says | File B says | Which is correct + citation |
| --- | --- | --- | --- | --- | --- |
| 1 | P0 | Strategy-instruction-type count | `strategy-service-deep-dive.html:162,202` — **11** (+ envelope) | `strategy-service-walkthrough.html:220` — **9** | `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py` declares 11 `StrategyInstructionEnvelope` subclasses (verified by the first-pass audit, re-confirmed here: deep-dive's own §02 code block at lines 256-398 enumerates all 11 by name — Trade, Swap, Quote, Lend, Borrow, Stake, Unstake, Transfer, Bridge, Atomic, Cancel). Deep-dive is correct; walkthrough is wrong. Already tracked as `client_artefact_remediation_2026_08_18.md` § A item 1, still open. |
| 2 | P0 | `StrategyFamily` enum membership (9 real members: `ML_DIRECTIONAL, RULES_DIRECTIONAL, CARRY_AND_YIELD, ARBITRAGE_STRUCTURAL, MARKET_MAKING, EVENT_DRIVEN, VOL_TRADING, STAT_ARB_PAIRS, PORTFOLIO`) | `strategy-service-deep-dive.html:876` — correct, all 9, no invention | Three other files each show a DIFFERENT wrong list — see rows 2a–2c below | Deep-dive is the only one of the four that discusses this taxonomy and gets it exactly right. |
| 2a | P0 | (same axis) | — | `strategy-service-walkthrough.html:314` — 5 families: Carry, Dispersion, Volatility, **"Liquidity provision"**, Event-driven (wrong count, wrong members, invented member) | Known finding, still unfixed (see § 0 above). Already tracked, `client_artefact_remediation_2026_08_18.md` § A item 2. |
| 2b | P1 | (same axis, **not previously flagged — outside the first-pass audit's scope**) | — | `carveout-engineering.html:1099` — table row groups "arbitrage · volatility · stat-arb · **DeFi liquidity provision**" as four peer families | `DeFi liquidity provision` is not a `StrategyFamily` member. Same failure mode as 2a, independently introduced in a document the first-pass audit never looked at (`carveout-engineering.html` is not one of the two files that audit scoped). Not yet in any remediation plan. |
| 2c | P1 | (same axis, **not previously flagged**) | — | `carveout-engineering.html:1183` — correctly names all 9 real members, then appends "**including DeFi liquidity-provision archetypes**" | Lower severity than 2b (the 9 real names are present and correct here), but the same invented term is tacked on as if it were a 10th real family. Not yet in any remediation plan. |
| 2d | P0 | (same axis, **not previously flagged, most severe of the three new instances**) | — | `platform-architecture.html:1284-1286` — "arbitrage, statistical arbitrage, **DeFi liquidity provision**, volatility, market making, event-driven, **liquidation capture** and directional families" — omits `portfolio` entirely, invents **two** non-member terms | Neither "DeFi liquidity provision" nor "liquidation capture" is a `StrategyFamily` member; "portfolio" (a real member) is missing from the enumeration. Worse than 2a/2b/2c because it both invents two terms AND drops a real one. Not yet in any remediation plan. |
| 2e | P0 | (same axis, same document, second occurrence) | — | `platform-architecture.html:3098-3103`, § "Strategy-family scope, stated explicitly" — same defect repeated: "arbitrage, market making, ML-directional, event-driven, volatility, statistical arbitrage, rules-directional, **liquidation capture**, **DeFi liquidity provision**" — again omits `portfolio`, again invents both terms | This section's own heading ("stated explicitly") makes the error worse — it is presented as the authoritative, precise boundary statement in a document whose entire §11 exists to draw IP/scope boundaries precisely. Not yet in any remediation plan. |
| 3 | P1 | Custody provider roster (`SigningSurface` schema vs. the working `custody/factory.py` roster) | `strategy-service-deep-dive.html:710` — `mock · local_key · cloud_kms · copper · ceffu` (no Fireblocks) | `strategy-service-walkthrough.html:817-822` — `LOCAL_KEY, COPPER_MPC, FIREBLOCKS_MPC, MOCK` (has Fireblocks, omits Ceffu) | `execution-service/execution_service/custody/factory.py`'s working branches are `mock, local_key, cloud_kms, copper, ceffu` (verified directly by the first-pass audit). Deep-dive is correct. Already tracked as `client_artefact_remediation_2026_08_18.md` § A item 4 — **but that item cites only the code, not this now-available third-party corroboration.** |
| 3a | P1 | (same axis, **new corroborating evidence not previously cited**) | `platform-architecture.html:567` — states explicitly: **"Fireblocks is out of scope — the stack is Copper plus CEFFU, and CEFFU remains entirely your decision for the Binance leg."** | (contradicts walkthrough's Fireblocks-inclusive, Ceffu-omitting code block, row 3 above) | This is a THIRD, independent document plainly asserting Fireblocks is out of scope and Ceffu is real — strengthening finding 3 from a single-doc accuracy issue into a confirmed 2-vs-1 cross-document contradiction. Worth citing in the existing remediation todo. |
| 4 | P2 | Venue-count headline figure | `platform-external-api-walkthrough.html:530-533,1160-1161` — **288 venues** in the coverage manifest, measured 2026-08-18, cited with date and provenance ("capability registry, re-run from source") | `strategy-service-walkthrough.html:221-222` — **158 Venues in capture / 84 Venue families**, presented unqualified in the §01 headline stat-row (same row that also carries the confirmed-wrong "9 Instruction types") | The first-pass audit's own text (§ Nick AI Axis 2, probe 13) explicitly names "158-84" as a **stale** unit needing reconciliation against the fresher 288/151/183 figures. That characterization was made discussing the Nick AI artefact, but the literal "158"/"84" pair is what the Elysium walkthrough is currently displaying as its own live headline number, with no date or scope qualifier. Not a proven wrong number (it may be a legitimately different, narrower metric — "venues in capture" vs. "venues in the coverage manifest" are not definitionally identical), but presented with the same unqualified confidence as the other stat-row figures sitting right next to a number already known to be wrong. Recommend the same treatment the audit already recommended for Nick AI: either refresh it or scope it explicitly as a dated, narrower measurement. |
| 5 | — | Client-specific archetype/repo counts | `platform-architecture.html:515` — "2 archetypes"; `carveout-engineering.html:1167` — "2 / 6 Carry archetypes transferred" | Consistent — both describe the same client-specific subset. | **Not a contradiction** — checked and cleared. Both artefacts also agree on "26 Repositories" (`platform-architecture.html:517` factbar; `carveout-engineering.html:1165` stat-row — both state 26). |
| 6 | — | Elysium-scope archetype totals (system-wide) vs. client-scope totals | `strategy-service-walkthrough.html:218-219` — "60 Archetypes declared / 32 Factory-registered" (system-wide) | `platform-architecture.html`/`carveout-engineering.html` — "2 archetypes" (this one client's contracted subset) | **Not a contradiction** — different scopes (whole system vs. one client's slice), and the first-pass audit already confirmed 60/32 clean against code. |
| 7 | — | Mode vocabulary (batch/paper/live/testnet) | Checked across all six files | No fourth mode invented anywhere. `strategy-service-walkthrough.html:497-499` correctly frames testnet as a paper sub-mode. `env: Literal["prod", "paper", "canary", "dev"]` appears verbatim as a **code field** in three places (`strategy-service-deep-dive.html:419,431`, `strategy-service-walkthrough.html:289`) — this is the `StrategyInstanceIdentity.env` field reproduced from source, a different axis from the `TradingMode` (`BATCH`/`PAPER`/`LIVE`) enum shown separately at `strategy-service-walkthrough.html:497-499`, and is not presented as a peer trading mode anywhere. "Shadow run" appears only as a project-timeline milestone term (`platform-architecture.html`, `ODUM_Elysium_Phase2_Update_2026-07-24.html:21`), consistently, never as a trading mode. | **Clean — no cross-document mode-vocabulary violation found.** |
| 8 | — | Coverage-percentage / shard / denominator figures (660 triples, 48.54%, 3,960 shards, 119,500,618 denominator) | Appear only in `platform-external-api-walkthrough.html` (stat-row lines 530-533 and the "measured versus projected" table lines 1160-1161), reused identically both times | No other artefact restates these system-wide coverage figures | **Clean, internally self-consistent** — no other document to contradict it. (The first-pass audit's already-flagged internal self-contradiction — the §4 table's "Expected, absent" row counting as "Yes" against a denominator formula that excludes it — is a single-document issue, out of this cross-document audit's scope; not re-litigated here.) |

**Net new findings this pass adds to the corpus**: rows 2b, 2c, 2d, 2e (three additional documents carrying the
"invented strategy family" defect — `carveout-engineering.html` twice, `platform-architecture.html` twice — none
previously flagged because the first-pass audit's scope was only the two walkthrough documents), row 3a (a third
document corroborating the Fireblocks/Ceffu finding), and row 4 (a second document's venue-count figure flagged as
likely-stale, using the first-pass audit's own "stale" characterization of that exact number pair).

---

## Section 2 — Broken internal anchors

**Exhaustive, scripted, not sampled.** Extracted every `href="#..."` and every `id="..."` per file via regex,
diffed href targets against that file's own id set.

| File | `href="#..."` count | `id="..."` count (unique) | Broken anchors |
| --- | --- | --- | --- |
| `platform-external-api-walkthrough.html` | 19 | 19 (19) | **None** |
| `strategy-service-walkthrough.html` | 18 | 18 (18) | **None** |
| `platform-architecture.html` | 27 | 32 (32) | **None** |
| `carveout-engineering.html` | 9 | 13 (13) | **None** |
| `strategy-service-deep-dive.html` | 9 | 12 (12) | **None** |
| `ODUM_Elysium_Phase2_Update_2026-07-24.html` | 0 | 0 (0) | N/A (plain email HTML, no anchors) |

Every `href="#..."` in every file resolves to a real `id="..."` in that same file. No cross-document `href`s exist
in any of the six files (each is self-contained; these artefacts are not designed to be viewed as a linked set, so
cross-document hrefs would be broken by construction if they existed — none do).

**Textual `§NN` cross-references** (not hyperlinked, so outside a literal href/id diff) were separately checked by
pairing every `§NN` occurrence with that file's own section-heading list:

- `platform-external-api-walkthrough.html` — uses **zero** `§NN` textual cross-references anywhere (confirmed via
  regex sweep); nothing to validate.
- `carveout-engineering.html` (22 occurrences) and `platform-architecture.html` (54 occurrences) — every reference
  resolves to a section number that exists in that file, and every one checked was topically consistent with its
  target section's heading (e.g., `carveout-engineering.html`'s repeated `§04`/`§07` references to "the platform
  seam" and "operational responsibilities" both land on the correct sections).
- `strategy-service-deep-dive.html` (14 occurrences) — all resolve correctly, all topically consistent.
- `strategy-service-walkthrough.html` (13 occurrences) — **two broken, both previously uncaught by the second one**:
  - **Line 511** (inside `§05` "Batch, paper and live — the mode axis"): *"it is exactly what makes the determinism
    proof in **§08** meaningful"* — `§08` is "How a strategy picks: coins, venues, funding" (line 616), unrelated.
    The real determinism decomposition (`live − batch = (paper − batch) + (live − paper)`) lives in `§09`
    "Reconciliation — the engines and the scenarios" (lines 669-693). **This is the instance the first-pass audit
    already found** (tracked in `client_artefact_remediation_2026_08_18.md` § A item 5).
  - **Line 1100** (inside `§16` "Backtest fidelity"): *"isolates execution's contribution from the strategy's — the
    same decomposition as **§08**, applied inside a single backtest"* — same wrong target, same correct answer
    (`§09`). **This is a second, previously-uncaught instance of the identical defect in the same file**, found
    only because this pass scripted the extraction exhaustively instead of relying on manual reading. Not currently
    in the remediation plan's todo (which cites only the `§05` occurrence).
  - For contrast, the file's other `§08` references (line 870: *"each slot names its spot and hedge venues
    (§08)"*) and its `§09` references (lines 484, 663, 1010) are all correctly targeted — `§08` genuinely covers
    venue-picking and `§09` genuinely covers reconciliation/determinism, confirming the two flagged instances above
    are real defects and not a mis-read of the section structure.

---

## Section 3 — HTML validity results

**Method disclosed per the task's requirement.** Two independent tools:

1. **Custom Python `html.parser` stack-walker** (`anchor_check.py`, written to session scratchpad) — feeds each
   file through `html.parser.HTMLParser`, tracks an explicit open-tag stack (respecting the standard HTML void-tag
   list), and reports any stray close tag, any close tag that has to skip over unclosed siblings, and anything left
   on the stack at end-of-file. Also independently tracks every `id=` attribute value for exact-match duplicates.
   **Result: all six files — zero structural issues, zero duplicate ids, empty stack at EOF.**

2. **`tidy`** (`HTML Tidy for Mac OS X released on 31 October 2006 - Apple Inc. build 13066` — the only HTML
   validator installed on this machine; no `html5lib`/`lxml` available in the Python environment). Run with `-qe`
   per file. Raw output shows dozens of `Error: <X> is not recognized!` lines per file. **After filtering**, every
   single one of them falls into exactly one of three known-noise categories, confirmed by manual inspection of a
   sample from each file:
   - This tidy build predates HTML5 and does not recognize `<header>`, `<nav>`, `<section>`, `<details>`,
     `<summary>`, `<figure>`, or `<figcaption>` — all six files use these extensively and correctly.
   - "missing `<dd>`" / "inserting implicit `<dl>`" / "missing `</dl>` before `</div>`" — every factbar in every
     file uses the HTML5.1+ `<dl><div><dt>…</dt><dd>…</dd></div>…</dl>` grouping pattern (valid per the current
     HTML spec: a `<dl>` may contain either bare `dt`/`dd` pairs or `div`-wrapped groups of them), which this
     2006-era tidy's ruleset predates and cannot parse.
   - "missing `<!DOCTYPE>` declaration" — five of the six files are Artifact-style content fragments (title + style
     + body content only, no `<!doctype html><html><head><body>` wrapper), consistent with how these pages are
     published; the sixth (`ODUM_Elysium_Phase2_Update_2026-07-24.html`) is a genuine standalone email HTML and
     does carry a full `<!doctype html><html><head>…</head><body>…</body></html>` structure appropriate to its
     different purpose.

   **After excluding all three categories, zero genuine tidy-flagged defects remain in any of the six files.**

| File | `html.parser` stack-walk | `tidy` (after noise filter) |
| --- | --- | --- |
| `platform-external-api-walkthrough.html` | Clean | Clean |
| `strategy-service-walkthrough.html` | Clean | Clean |
| `platform-architecture.html` | Clean | Clean |
| `carveout-engineering.html` | Clean | Clean |
| `strategy-service-deep-dive.html` | Clean | Clean |
| `ODUM_Elysium_Phase2_Update_2026-07-24.html` | Clean | Clean (only two benign `<meta charset>` warnings: proprietary attribute, no `content=` — cosmetic, not structural) |

**Conclusion: all six files are well-formed HTML** under both validators once `tidy`'s tool-generation gap
(pre-HTML5) is accounted for. No unclosed tags, no malformed attributes, no duplicate ids found by either method.

---

## What I could not verify

- **Not a full line-by-line prose read of all six files.** `strategy-service-deep-dive.html` (1002 lines) and
  `ODUM_Elysium_Phase2_Update_2026-07-24.html` (167 lines) were read in full. `platform-architecture.html` (3317
  lines, the largest file by 2.5×), `carveout-engineering.html` (1281 lines), `strategy-service-walkthrough.html`
  (1186 lines), and `platform-external-api-walkthrough.html` (1187 lines) were read via grep-located sections
  covering the five claim categories the brief specified (counts, enums, statuses, venues, modes) plus every
  `§NN` cross-reference site, not read start-to-finish. A narrative contradiction that doesn't surface any of the
  keywords/patterns I searched for (numbers, family names, mode words, `§NN`, `class="st `) would not have been
  caught. Given `platform-architecture.html`'s size and the density of findings already surfaced there (2 of the 2
  new P0 family-invention instances both live in this one file), it is the single highest-risk file for a residual
  uncaught issue.
- **Did not independently re-run the code verification the first-pass audit already did** (the `StrategyFamily`
  9-member enum, the 11 `StrategyInstructionEnvelope` subclasses, the `custody/factory.py` working-branch roster).
  I treated those as settled ground truth (per the task's baseline-confirmation instruction) and used them to judge
  the newly-found instances (2b–2e, 3a) — I did re-open and re-read `strategy-service-deep-dive.html` directly to
  confirm its own rendering matches those cited code facts, which it does.
- **Venue-count and archetype-count differences across files (row 4, row 5, row 6 above) were judged by reading
  surrounding context for stated scope, not by independently re-deriving each number from source data or the
  manifest.** I could not fully rule out that "158 Venues in capture / 84 Venue families" is a genuinely different,
  narrower, currently-accurate metric rather than a stale reuse of the number the first-pass audit called out as
  stale — flagged at P2 (needs reconciliation / scoping) rather than a hard "wrong" claim for that reason.
- **Status/readiness badges** (`class="st st-live/st-part/st-plan"` in the two walkthrough documents) were
  inventoried but not exhaustively cross-checked capability-by-capability against each other or against
  `platform-architecture.html`'s own readiness dots (`§2`'s different "readiness scale," referenced at
  `platform-architecture.html:1183`) — the two walkthroughs cover mostly non-overlapping capability sets (external
  API surface vs. strategy-service internals), so a section-badge-level comparison was judged lower-value than the
  concrete cross-document factual checks in Section 1; a targeted follow-up specifically diffing the same-named
  capability across all status-badge sites was not performed.

## Progress Log

**2026-08-18 — audit complete.** Confirmed the known baseline (instruction-count and strategy-family drift between
`strategy-service-deep-dive.html` and `strategy-service-walkthrough.html`) is still live and unfixed. Ran an
exhaustive script-based anchor/id sweep and a scripted `§NN` cross-reference sweep across all six files (not
sampled), finding one previously-uncaught duplicate instance of the known stale-cross-reference defect. Extracted
and compared five claim categories across all six files via targeted grep, surfacing that the "invented strategy
family" defect the October-delivery plan believed was fixed (in `strategy-service-deep-dive.html` only) is present
in three additional locations across two documents never in scope of the first-pass audit
(`carveout-engineering.html`, `platform-architecture.html`), and that the Fireblocks/Ceffu custody mismatch has a
third, independent corroborating document. Validated HTML structure via two independent methods (a custom
Python `html.parser` stack-walker and `tidy`, with `tidy`'s legacy-ruleset false positives filtered and disclosed).
No file was edited. Findings are ready for the operator to fold into
[`/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md`](/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md)
(currently scoped to only the two walkthrough documents) or a follow-up plan covering
`carveout-engineering.html` and `platform-architecture.html`, which that plan does not currently touch.
