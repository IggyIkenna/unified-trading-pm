---
doc_type: codex-ssot
title: Rule 13 — Artefact claim marks (status, evidence tier, owner)
summary: "The three-mark system every claim-bearing section in a client-facing presentation artefact carries: the status
  pill (live/partial/planned — what the system does), the evidence-tier badge (verified/check/assumed — how we know),
  and the owner mark (the workstream, plan or epic that closes the gap — who is delivering it). Exact CSS + markup,
  so every artefact renders the three consistently."
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin, sales]
tags: [customer-journey, artefact, disclosure, evidence-tier, owner-mark, docspec]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/client_artefact_remediation_nickai_2026_08_18.md,
  ]
created: 2026-08-18
authoritative_for: [artefact status/evidence-tier/owner-mark markup, owner-mark content grammar]
referenced_by: []
owner:
last_reviewed:
code_refs: [codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html]
---

# Rule 13 — Artefact claim marks (status, evidence tier, owner)

> Every claim-bearing section in a client-facing presentation artefact (`codex/14-customer-journeys/commercial-model/
*.html`) carries three orthogonal marks. This doc is the one place all three are specified, so six documents
> render them the same way instead of six ad-hoc implementations drifting apart.

## Why a written spec, not just "match what's already in the file"

The status pill and evidence tier were defined directly in the two lead artefacts' `<style>` blocks
(`unified-trading-pm@171dc40739` / `ec08cccad1`) — correct at the time, but with no doc capturing the contract, a
third artefact copying the CSS has nothing to diff against, and a fourth mark (this one) has nowhere to be defined
without either duplicating the CSS comment or touching a file it doesn't own. This doc is that place. It restates the
first two marks verbatim (already shipped, included here only for a single source of truth) and defines the third.

## The three marks

| Mark                 | CSS class | Question it answers      | Shape                                                              | Values                                         |
| -------------------- | --------- | ------------------------ | ------------------------------------------------------------------ | ---------------------------------------------- |
| **Status**           | `.st`     | What does the system do? | Solid colour-bordered pill, tinted wash, uppercase sans            | `live` / `partial` / `planned`                 |
| **Evidence tier**    | `.ev`     | How do we know?          | Dashed colour-bordered pill, transparent, monospace, symbol prefix | `✓ verified` / `? check` / `~ assumed`         |
| **Owner** (this doc) | `.own`    | Who closes the gap?      | Solid neutral-filled chip, no colour border, sans                  | A workstream/plan/epic short-ref (see grammar) |

Three different shapes on purpose — a reader must be able to tell which axis they're looking at without reading the
text inside the badge. `.st` and `.ev` are pills (rounded, bordered); `.own` is a chip (small corner radius, filled,
neutral hairline border) so it never gets misread as a fourth status color.

### Status pill — `.st` (already shipped, restated for completeness)

```css
.st {
  font-family: var(--sans);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 3px;
  white-space: nowrap;
  border: 1px solid currentColor;
}
.st-live {
  color: var(--good);
  background: var(--g-data-wash);
}
.st-part {
  color: var(--warn);
  background: var(--g-post-wash);
}
.st-plan {
  color: var(--crit);
  background: var(--accent-wash);
}
```

Legend line:

```html
<span><b class="st st-live">live</b> reachable on a production path AND validated with real capital</span>
<span><b class="st st-part">partial</b> built, reachable for some cases</span>
<span><b class="st st-plan">planned</b> specified, not yet built</span>
```

### Evidence tier — `.ev` (already shipped, restated for completeness)

```css
.ev {
  font-family: var(--mono);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 1px 8px;
  border-radius: 10px;
  white-space: nowrap;
  border: 1px dashed currentColor;
  background: transparent;
}
.ev-verified {
  color: var(--g-data);
}
.ev-check {
  color: var(--ink-3);
}
.ev-assumed {
  color: var(--warn);
}
```

Legend line:

```html
<span
  ><b class="ev ev-verified">✓ verified</b> checked against code or measured data — verifying source named inline</span
>
<span><b class="ev ev-check">? check</b> stated in good faith, not yet independently validated</span>
<span><b class="ev ev-assumed">~ assumed</b> best current understanding — explicitly not verified</span>
```

Machine-verified sections cite the verifying file/command/skill inline in the section body — see the existing
`<p class="mono">Verified directly against <code>...</code></p>` convention at the end of a `sec-body`. The badge
itself never carries the citation; it only states the tier.

### Owner mark — `.own` (new, this doc is its spec)

```css
/* Owner mark — the THIRD mark, alongside status (what the system does) and evidence
   tier (how we know). Names who closes the gap. Solid neutral-filled chip with a plain
   hairline border — no colour border, no dash, no wash — so it reads as metadata, not
   a fourth status colour, and is never confused with .st or .ev at a glance. */
.own {
  font-family: var(--sans);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.01em;
  padding: 2px 8px;
  border-radius: 3px;
  white-space: nowrap;
  color: var(--ink-2);
  background: var(--surface-2);
  border: 1px solid var(--rule);
  cursor: help;
}
.sec-head .own {
  align-self: center;
}
```

Legend line:

```html
<span
  ><b class="own" title="Example — hover any owner mark for the full reference">owner: W5</b> the workstream, plan or
  epic that closes this gap — hover for the full citation; omitted once status reaches <b class="st st-live">live</b>,
  because a live claim has no open gap to own</span
>
```

Section-head usage — appended after `.st` and `.ev`, in that fixed order (status, evidence, owner):

```html
<div class="sec-head">
  <span class="num">13</span>
  <h2>Treasury, wallets, transfers</h2>
  <b class="st st-part">partial</b>
  <b class="ev ev-verified">✓ verified</b>
  <b
    class="own"
    title="system_readiness_master.md — W5: Venue registry completeness (collateral, cross-margin, transfer eligibility, manual-trade fallback)"
    >owner: W5</b
  >
</div>
```

## Owner-mark content grammar

The badge text is deliberately terse — the full reference lives in the `title` attribute (hover) and, where the
section already carries a machine-verified citation paragraph, is repeated there as a plain-text `Owner:` line so it
survives print/PDF export where `title` tooltips don't.

1. **Workstream inside `system_readiness_master.md`** → badge is `owner: W<N>` (e.g. `owner: W5`). This is the common
   case — W21's own audit found the artefacts' claim surface spans ~20 epics, but the highest-traffic gaps
   (collateral, transfer, reconciliation, PnL attribution, risk, latency/SLA) are this epic's own W5/W10/W12/W13/
   W16/W17/W18.
2. **A specific plan outside that epic** → badge is `owner: <short-tag>` where `<short-tag>` is a recognisable
   abbreviation of the plan slug, optionally with a `§<section>` suffix for a specific gate inside it (e.g.
   `owner: elysium-disclosure §H.8`). The `title` attribute always carries the resolvable path
   (`/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md § H.8`), never just the
   short-tag — the badge is a label, the title is the citation.
3. **An epic, cited at epic grain because no single workstream owns it yet** → badge is `owner: <epic-slug>` (e.g.
   `owner: defi_master`).
4. **Multiple owners** → up to two short-tags, comma-separated (`owner: W5, W10`); beyond two, cite the umbrella
   epic only and let the `title` list every workstream — a badge is not the place for an exhaustive index.
5. **No mark at all** on a section whose status is `live` — W21's own framing is explicit: the owner mark exists to
   catch "an artefact claim nobody is tracking," and a fully live claim has no gap to track. Do not invent an owner
   for a closed claim; an absent `.own` badge on a `live` section is correct, not an omission.

## Applying this to an existing artefact

1. Add the `.own` CSS block (above) to the artefact's `<style>` block, next to the existing `.st`/`.ev` rules.
2. Add the owner legend line to the header's evidence-tier `<div class="legend">` (or its own adjacent `.legend`
   div) — see the shipped legend blocks in `platform-external-api-walkthrough.html` for the exact placement pattern.
3. For every `<div class="sec-head">` whose `.st` is `st-part` or `st-plan`, append a `.own` badge naming the real
   closing item — grep `system_readiness_master.md`'s workstreams first (§ "The closure invariant" names the
   highest-traffic ones); fall back to the specific owning plan when the gap is narrower than a whole workstream
   (e.g. the dynamic-universe pinning gap is `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`
   § H.8, not all of W-anything).
4. Where a machine-verified citation paragraph already exists at the end of the section body, add one line:
   `Owner: <full path> — <one-line workstream/plan label>.`

## Cross-references

- [`06-show-dont-show-discipline.md`](06-show-dont-show-discipline.md) — the disclosure axis this mark system does
  not replace; owner marks and evidence tiers are about internal traceability, not what the audience is shown.
- [`system_readiness_master.md`](/plans/epics/system_readiness_master.md) § "The closure invariant" — the operator
  ruling this mark exists to satisfy, and the workstream numbering the badge content grammar (§ above) draws on.
