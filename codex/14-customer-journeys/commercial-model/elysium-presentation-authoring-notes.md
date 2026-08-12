---
doc_type: codex-ssot
title: Elysium/POD client document set — authoring notes, artifact URLs and traps
summary: >-
  Operational notes for the Elysium client-facing HTML documents held in this directory: the published artifact URLs
  (republishing without passing the URL creates a duplicate rather than updating), the design token set and validated
  palette, and the authoring traps that each cost real time to learn — chief among them that CSS var() does not resolve
  in SVG presentation attributes, and that an artifact URL absent from the table above is unrecoverable.
authoritative_for:
  - elysium client document authoring traps
  - elysium published artifact urls
status: current
nature: notes
owner: ikennaigboaka
referenced_by: []
last_reviewed: "2026-08-11"
asset_group: [defi]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, client-communication, documentation]
related:
  [
    /codex/14-customer-journeys/commercial-model/carveout-engineering.html,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
    /codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
    /codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md,
  ]
created: 2026-08-11
last_updated: "2026-08-11"
code_refs: []
---

# Elysium / POD client-facing documents

The standalone HTML documents produced from 2026-08-11 for the Elysium (POD) DeFi mandate. **Not reveal.js decks** —
unlike the numbered files in the parent directory these are scrolling documents with progressive disclosure, designed to
be read and forwarded rather than presented from a stage.

## Published artifact URLs — USE THESE TO UPDATE, DO NOT REPUBLISH BLIND

Each file is published as a private Claude artifact. **Publishing without passing the existing `url` creates a DUPLICATE
artifact rather than updating the one the operator already has.** From a fresh session, pass the URL:

| File                              | Artifact URL                                                         | Favicon |
| --------------------------------- | -------------------------------------------------------------------- | ------- |
| `platform-architecture.html`      | https://claude.ai/code/artifact/cd44b148-6752-437c-919f-d8b4cef42cba | 🏛️      |
| `carveout-engineering.html`       | https://claude.ai/code/artifact/39d52123-63ad-49ac-a62a-99d2b9f26269 | 🧩      |
| `strategy-service-deep-dive.html` | https://claude.ai/code/artifact/a99f5b1e-401d-4b2e-b025-f7511bda6552 | ⚙️      |

Keep the favicon stable across redeploys — the operator finds the tab by its icon.

## What each one is

> Section counts are deliberately not given below — they went stale twice (see trap 9). Count `<h2>` and subtract the
> contents block if you need one.

- **`platform-architecture.html`** — the primary client document, and the only one written for a non-engineering reader
  as well as an engineer. Hand-authored SVG figures throughout. Covers the entity chain, a component map encoding
  group/ownership/build-stage on three independent channels, the two strategy archetypes in mechanical detail, data
  coverage per venue, the batch/paper/live determinism spine, execution algorithm resolution and the
  connectivity-vs-execution-intelligence boundary, the repository/tier stack, infrastructure and data flow, the delivery
  and CI-escalation loop, live operations, the Article 4 carve-out with a per-repository hand-over manifest, **the wider
  platform surface and where it can go**, and programme status.

  > The wider-surface section is **deliberately asset-group-agnostic** — it describes market types by their properties
  > ("event-driven markets whose settlement has nothing to do with price at all") and names no asset group, venue or
  > instrument. That was an explicit operator instruction: convey multi-asset-group breadth without naming specifics.
  > Adding a named asset group there would break the constraint the section was written to satisfy.

- **`carveout-engineering.html`** — CTO-audience engineering specification. Defines the acceptance bar for "runnable";
  specifies the **proposed packages** with a declared ship form each (FULL / REDUCED / STATIC / INTERFACE-ONLY); the
  runtime path; **the platform seam of typed interfaces** that resolve either to local implementations or to maintained
  services; the configuration snapshot; the hand-over acceptance criteria; the standing operational functions; extension
  work-items; and the 26-repo estate mapping as the final appendix. Carries an _inspection is not transfer_ note.

- **`strategy-service-deep-dive.html`** — the companion to sending the strategy-service repository itself, and the most
  technical of the three. Reproduces from source the `StrategyInstructionEnvelope` and **all eleven instruction
  subtypes**, the live `carry_staked_basis.yaml`, the typed configuration schemas, the breakers and kill switch, capital
  movement through Copper (Figure 1), the read surface by module, external-strategy integration, asset-group agnosticism
  and the research path. **Its config extracts are reproduced from real files, so a reader can diff them against the
  repository they receive** — if a schema changes in code, this document is wrong until updated, unlike the other two
  which describe structure rather than quote it.

  > Contains the **placeholder risk thresholds** from the client's own strategy config, still carrying their
  > `⚠️ MAY-23 CUTOVER PLACEHOLDER VALUES ⚠️` banner. That is deliberate honesty, not an oversight — but it means the
  > operator-owned threshold approval is now visible to the client, and the document should be re-checked against the
  > config once those values are ratified.

  > **Rev 1.0 was rejected by the operator** (2026-08-11) as discussing "our methodology way too much" and not
  > presentable to a CTO — it read as an internal negotiation memo. **Rev 2.0 fixed that structurally, not by editing
  > prose**, and the mechanism is the thing to preserve if this document is ever restructured again:
  >
  > **The twenty non-contributing repositories are expressed as ten typed interfaces, not as a list of things the client
  > does not get.** `PortfolioRiskService.circuit_state()`, `TreasuryService.request_transfer()`,
  > `AttributionService.decision_pnl()` — the scope of the platform is communicated in method signatures, with no
  > implementation disclosed and no mechanism described. A loss-list invites argument; a seam invites integration
  > planning. Every "what you don't get" table in rev 1.0 became either a ship-form column, an interface row, an
  > acceptance condition, or an operational function.
  >
  > Also deleted in rev 2.0 and **do not reintroduce**: any first-person advocacy ("we would rather you stayed", "the
  > three questions we would ask in your position"), any claim about our own measured contribution to returns, and any
  > mechanism-level description of how the dynamic layer works (the §05 table states the capability boundary only).
  >
  > Structure was taken from an operator-supplied advisory draft,
  > `~/Downloads/Odum_Elysium_Strategy_Carve_Out_CTO_Architecture.docx` — **input to us, never a document for the
  > client**: its §1, §8 and §9 are an internal strategy memo containing a rebuild-day estimate and the note "I would
  > not put the 180 AI days number in the external CTO document". Four ideas were adopted (ship-form taxonomy, the
  > interface seam, acceptance criteria, proposed package names in place of our real repo names).

  **Open caveat:** §02's eleven packages are labelled a _proposed_ structure and do not exist — verified 2026-08-11, no
  `strategy-basis-core` / `contracts-platform` / lite package is in the workspace. Showing this document therefore
  commits us to building the seam, since a CTO reading §04 will ask to see it. The lite-repo decision is now coupled to
  whether the document goes out.

## Authoring traps — read before editing (each of these cost real time)

1. **`var()` DOES NOT RESOLVE IN SVG PRESENTATION ATTRIBUTES.** `fill="var(--x)"`, `stroke="var(--x)"`,
   `color="var(--x)"` and `font-family="var(--x)"` silently fail — the element renders with the default (black fill,
   inherited font). It must be `style="fill:var(--x)"`, which does resolve. 498 attributes in
   `platform-architecture.html` were written the wrong way first and would have shipped every diagram in black. Any new
   SVG must use `style=`, and the check is:

   ```bash
   grep -cE '\s(fill|stroke|color|font-family)="var\(' codex/14-customer-journeys/commercial-model/*.html   # MUST be 0
   ```

2. **No `<style>` or `<script>` inside the SVG** (artifact CSP + house rule). Page-level `<style>` only; colour SVG via
   `style=` attributes and `currentColor`.

3. **No external font/CSS/script hosts.** A strict CSP blocks every external request, so a linked webfont fails silently
   to a fallback. Both files therefore use system-font stacks only — an oldstyle serif for display and body, system sans
   for labels and tables, monospace for data.

4. **Theme tokens must be defined on bare `:root`.** A colour whose only definition lives inside
   `@media (prefers-color-scheme: dark)` or `[data-theme=...]` never applies in the un-stamped default state, which is
   what most viewers see. Pattern used: complete light palette on `:root`, tokens-only overrides in
   `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }` and `:root[data-theme="dark"]`.

5. **`getBBox()` on rotated `<text>` returns the PRE-transform box.** Two "text escapes the viewBox" findings were false
   positives from this. Verify rotated labels by transforming the bbox corners through
   `t.transform.baseVal.consolidate().matrix`.

6. **`innerText` skips content inside a closed `<details>`.** Any content-presence check must open the toggles first or
   it reports false negatives.

7. **Measure the layout claim, don't estimate it.** Collapsing four reference blocks was predicted to hide ~40% of the
   scroll; measured **7%**. The height was in the figures (17% of the page on their own) and in twelve sections of
   prose, not in the tables. What actually worked was restructuring so every section body sits behind one toggle with
   its heading, lede and key-points strip always visible — measured **70–81%** for `platform-architecture.html`, and
   **44% at default / 64% fully collapsed** for `carveout-engineering.html` rev 2.0 (lower because 3 of its 9 sections
   are deliberately open, so both figures and the capability-boundary table are visible without a click). Estimate, then
   measure, then quote the measurement.

8. **A layout/collision detector that reports zero must be validated before the zero is believed.** Three buggy versions
   of the SVG collision check were written across these two documents: one compared text boxes against _badge_ rects
   across coordinate spaces, one picked an arbitrary host among equal-area sibling rects (reporting 849px phantom
   "spills"), and `getBBox()` on rotated `<text>` returns the **pre-transform** box. The working recipe: use
   `getBoundingClientRect()` for screen-space comparisons, pick the host rect by **nearest left edge**, transform
   rotated corners through `t.transform.baseVal.consolidate().matrix` — and then **inject a known collision and a known
   overflow and confirm the detector fires** before trusting a clean result. A null result from an unvalidated detector
   is not evidence.

9. **Re-derive every asserted count — and prefer not asserting a total at all.** Rev 1.0 claimed 8 carry archetypes and
   13 venue adapters. Both were wrong, and the _corrections_ then rotted too: the "6 carry archetypes" replacement was
   itself wrong (the package declares **seven** `ARCHETYPE` values; the missed one was `CARRY_FUNDING_DISPERSION`), and
   the venue claim _understated_ the estate at 13 against 20 distinct adapters in `trade_execution/adapters/`. Two
   lessons, in order of value:

   - **A total is the most rot-prone thing you can write.** Every one of these numbers was correct when measured and
     wrong within days, because the estate grows. Prefer a property that does not move — "the package names two carry
     archetypes" is stable because it describes the spec, not the tree. Where a client argument genuinely needs the
     contrast, give the shape ("every archetype across every family") rather than an integer.
   - **Derive counts from the enum or registry, never from the directory.** The 6 came from counting files and missing
     one; the definitive oracle was `grep 'ARCHETYPE = StrategyArchetype\.'` over the package. Likewise
     `VENUE_TO_ADAPTER_KEY`, which CLAUDE.md names as the venue-registry SSOT, could not be located in non-test UAC
     sources — so the 20 is a **measured floor from the adapter directory**, not a registry read. Quote the floor and
     say so, or find the registry.

   Corollary trap: **a correction applied to one artefact is not applied to the set.** The "liquidity provision" family
   was fixed in `strategy-service-deep-dive.html` on 2026-08-11 and missed in
   `elysium-carveout-deferral-message-2026-08-11.md`, so a wrong claim stayed live for a day. Grep the whole directory
   for the wrong string, not just the file you found it in.

   And a trap inside that trap — **over-correction.** I recorded the liquidity-provision family as "invented". It is
   not: `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL` and `DEFI_LP_VAULT` are all real `StrategyArchetype` members. The error
   was narrower than I described — liquidity provision is a genuine platform capability **misfiled as a family** when
   `StrategyFamily` has nine members and none of them is LP. Saying "invented" would have led a future reader to delete
   a true capability claim from `platform-architecture.html`, which names DeFi liquidity provision correctly. **Diagnose
   the exact shape of an error before recording it, because the record is what the next person acts on.**

10. **`safe-doc-push` does not carry deletions, so a `git mv` half-lands.** The script copies **named files** into an
    isolated worktree and commits from there; a deleted path is not a file to copy, so the new path lands and the old
    one stays. Moving these artefacts into codex left **four stale duplicate copies** of client-facing documents live on
    origin at once. After any rename or move, verify both halves:

    ```bash
    git ls-tree -r --name-only origin/live-defi-rollout -- <old-path>   # MUST be empty
    git ls-tree -r --name-only origin/live-defi-rollout -- <new-path>   # MUST list the file
    ```

11. **An artifact URL that is not in the table above is GONE, and "I recorded it" is not evidence that it is.** The
    `strategy-service-deep-dive.html` URL was missing from this table for a day while a session-end verdict asserted
    that all three URLs were safely recorded here. It survived only because a conversation summary happened to carry it;
    had that context been dropped, the operator's published artifact would have become unreachable and a republish would
    have silently created a duplicate at a new URL, leaving them holding a stale link. The claim was a **proxy** — "I
    wrote the notes file, therefore the URL is in it" — never a measurement. Before asserting any artefact is durable:

    ```bash
    grep -c '<the-uuid>' codex/14-*/commercial-model/elysium-presentation-authoring-notes.md   # MUST be 1
    ```

    (The glob is not cosmetic: `check_reference_paths.py` scans **fenced code blocks too**, so a literal repo-relative
    `codex/NN-name/...md` path inside a shell example is a FORMAT violation even though it is a command, not a
    reference. A leading slash would make the command wrong; the glob dodges the pattern and stays runnable.)

    Generalises past URLs: **verify durability by reading the file back, not by remembering that you wrote it.** This is
    the same proxy-vs-property failure as trusting `exit 0` from a checker that never opened the file (see the plan's
    H.6).

## Design system

Both files share one token set so they read as a pair. The three categorical hues (component group / carve-out bucket)
are validated with the `dataviz` skill's palette validator on **all pairs, both modes** — lightness band, chroma floor,
CVD separation, normal-vision floor and contrast vs surface all PASS:

| Role                        | Light     | Dark      |
| --------------------------- | --------- | --------- |
| Data platform               | `#107c5f` | `#15907a` |
| Decision &amp; execution    | `#3b62c4` | `#4c7fda` |
| Post-trade &amp; operations | `#a38112` | `#ae8c24` |
| Brand accent                | `#8c6d14` | `#d4af37` |

If a fourth group hue is ever needed: 4-, 5- and 6-hue sets were all tried and **failed** deuteranopia separation on
all-pairs. The resolution was three hues plus a neutral outline, with ownership carried by letter badges (Y/L/P) and
grouping reinforced spatially. Do not re-attempt a fourth hue without re-running the validator.

## Provenance

Built 2026-08-11 in an interactive session from the codex commercial-model and architecture SSOTs, the underlying
contract (now transcribed at
[`/codex/14-customer-journeys/commercial-model/contracts/`](/codex/14-customer-journeys/commercial-model/contracts/)),
and direct verification against the workspace tree. `carveout-engineering.html` rewritten to rev 2.0 the same day.

**Re-derive the counts before reusing either document.** The 26-repo estate and the 6/20 split are the organising
numbers of the §09 appendix, and a repo added or retired changes them; the 2/6 archetype and 4/20 adapter figures were
both wrong in rev 1.0 and were only caught by re-deriving. The estate count was verified by `.git`-bearing directories
under the workspace root (26), not by `workspace-manifest.json` — that file is at
`unified-trading-pm/workspace-manifest.json`, not the workspace root, which is where an earlier note implied it sits.

**Known contradiction, operator-owned:** `platform-architecture.html` states a "complimentary 30-day support period" in
three places, which conflicts with the 2026-08-09 operator ruling that **60 calendar days** is the binding Initial
Support Period. Left unfixed deliberately — see the P0 in
[`elysium_sla_v4_support_period_and_stale_dates_2026_08_08`](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).
`carveout-engineering.html` rev 2.0 states no number and defers to the SLA.
