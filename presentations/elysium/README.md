# Elysium / POD client-facing documents

Two standalone HTML documents produced 2026-08-11 for the Elysium (POD) DeFi mandate. **Not reveal.js decks** — unlike
the numbered files in the parent directory these are scrolling documents with progressive disclosure, designed to be
read and forwarded rather than presented from a stage.

## Published artifact URLs — USE THESE TO UPDATE, DO NOT REPUBLISH BLIND

Both files are published as private Claude artifacts. **Publishing without passing the existing `url` creates a
DUPLICATE artifact rather than updating the one the operator already has.** From a fresh session, pass the URL:

| File                         | Artifact URL                                                         | Favicon |
| ---------------------------- | -------------------------------------------------------------------- | ------- |
| `platform-architecture.html` | https://claude.ai/code/artifact/cd44b148-6752-437c-919f-d8b4cef42cba | 🏛️      |
| `carveout-engineering.html`  | https://claude.ai/code/artifact/39d52123-63ad-49ac-a62a-99d2b9f26269 | 🧩      |

Keep the favicon stable across redeploys — the operator finds the tab by its icon.

## What each one is

- **`platform-architecture.html`** — the primary client document. 12 sections, 9 hand-authored SVG figures. Covers the
  entity chain, a component map encoding group/ownership/build-stage on three independent channels, the two strategy
  archetypes in mechanical detail, data coverage per venue, the batch/paper/live determinism spine, execution algorithm
  resolution and the connectivity-vs-execution-intelligence boundary, the repository/tier stack, infrastructure and data
  flow, the delivery and CI-escalation loop, live operations, the Article 4 carve-out with a per-repository hand-over
  manifest, and programme status.
- **`carveout-engineering.html`** — CTO-audience companion. All 26 repositories classified (6 contribute to a carve-out,
  20 do not), what "reduced" removes inside each of the six, light-adapter limits, static-config-versus-dynamism,
  shared-infrastructure economics, the expansion path priced both ways with TradFi as the worked discontinuity.

  > **⚠️ OPERATOR FEEDBACK 2026-08-11, NOT YET ACTIONED**: this document "discusses our methodology way too much" and is
  > **not presentable to a CTO as written**. It reads as an internal negotiation memo (sections framed as "an honest
  > summary of the trade", "what we would want to know if the positions were reversed", "our own position"). Needs a
  > rewrite into a technical briefing register before it goes out. Tracked as a todo on
  > [`elysium_sla_v4_support_period_and_stale_dates_2026_08_08`](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).

## Authoring traps — read before editing (each of these cost real time)

1. **`var()` DOES NOT RESOLVE IN SVG PRESENTATION ATTRIBUTES.** `fill="var(--x)"`, `stroke="var(--x)"`,
   `color="var(--x)"` and `font-family="var(--x)"` silently fail — the element renders with the default (black fill,
   inherited font). It must be `style="fill:var(--x)"`, which does resolve. 498 attributes in
   `platform-architecture.html` were written the wrong way first and would have shipped every diagram in black. Any new
   SVG must use `style=`, and the check is:

   ```bash
   grep -cE '\s(fill|stroke|color|font-family)="var\(' presentations/elysium/*.html   # MUST be 0
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
   its heading, lede and key-points strip always visible — measured **70–81%**. Estimate, then measure, then quote the
   measurement.

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
and direct verification against the workspace tree. Repository classification reflects `workspace-manifest.json` as at
that date — **re-derive it before reusing these documents**, since the 6/20 split is the organising number of
`carveout-engineering.html` and a repo added or retired changes it.
