---
title: Marketing homepage refresh — restore old-hero structure + branded service row
priority: P1
status: active
owner: agent
created: 2026-04-22
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: marketing
epic: marketing-site-v2
completion_gates:
  code: C5
  deployment: D0
  business: B6
repo_gates:
  - repo: unified-trading-system-ui
    code: C0
depends_on: []
---

## Context

The current homepage on `live-defi-rollout` (`public/homepage.html` rendered via `app/(public)/page.tsx` →
`MarketingStaticFromFile`) replaced the previous production hero (odum-research.com) with a 4-tile path grid, in-hero
FCA block, and "Four ways to plug into one regulated operating system" lead. Ikenna reviewed production side-by-side and
flagged the old hero as objectively cleaner and more captivating:

- **Product-universe pill** (`TradFi · Crypto · DeFi · Sports · Prediction Markets`) reads as one-glance scope
  communication.
- **Hero H1 = "Unified Trading Infrastructure"** is stronger than "Odum Research" (logo+wordmark already in header — H1
  should state the product, not repeat the brand).
- **"The same infrastructure we use to run our own capital — available to institutional clients at any entry point"** is
  a tight capture of the "own-book-first" USP without overclaiming.
- **Service icon row** (Data / Research / Trading / Regulatory / Investment) with hover-over detail reads as capability
  breadth at a glance. Current 4-tile grid with in-tile hover definitions carries more copy but feels gimmickier than
  branded.
- **Stat strip** (5 asset classes / 127 venues / 24/7 / 100+ TB / 5 service lines) anchors scale without pricing.
- **Trust-badge row** (FCA 975797 / Institutional Security / No-Code to Full-Code) reinforces the regulated +
  institutional + flexibility trio.

The goal is to bring the old hero structure back on top of the current site, accurate to the current commercial model:

- Commercial paths have settled at **four** (Investment Management, DART, Odum Signals, Regulatory Umbrella) — the old
  "Data/Research/Trading/Regulatory/Investment" row was capability-lines, not commercial paths. Ikenna's preference: use
  **four commercial paths** for the icon row, keep the capability-lines breakdown as a subordinate stats-strip caption
  (today's homepage already does this).
- `$7.5M+ AUM` is a real IM number — drop the "(indicative)" qualifier currently on the proof strip.
- `London, UK` HQ stays.
- Header already shows the logo + "Odum Research" wordmark + `FCA 975797` pill — the hero should NOT repeat
  `Odum Research` as H1 or re-render the FCA block prominently inside the hero block. Trust-badge row at the bottom of
  the hero can carry `FCA 975797` with the other two badges.

Sibling task (user): **remove the "Read client briefings for full scope, process, and fit. View briefings" copy** from
`components/marketing/public-depth-next-strip.tsx`. The right-side `Next: Briefings → Book → Questionnaire` breadcrumb
already does the job; the left-side sentence is redundant copy.

## Decision gate — Monday 2026-04-27 (B1)

Plan is locked against `live-defi-rollout` and NOT to be implemented until Ikenna confirms the following five calls in
the Monday review. Phase 0 is the brief; Phases 1–4 only execute post-approval.

| #   | Decision                        | Default proposal                                                                                                 | Alt option                                         |
| --- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 1   | H1 copy                         | `Unified Trading Infrastructure`                                                                                 | `One regulated operating system`                   |
| 2   | Sub-tagline                     | `The same infrastructure we use to run our own capital — available to institutional clients at any entry point.` | Current `Unified trading infrastructure` one-liner |
| 3   | Service icon row — 4 or 5 icons | **4 icons** = IM / DART / Odum Signals / Regulatory Umbrella                                                     | 5 icons = add `Data` as separate tile              |
| 4   | CTA pair                        | Keep current: `Discuss a Mandate` (Calendly) + `Explore the Platform`                                            | Old-site: `Get Started` + `Book a Demo`            |
| 5   | AUM line                        | `$7.5M+ AUM — IM mandate scale` (drop "indicative")                                                              | Keep "indicative" qualifier for now                |

## Pre-audit manifest

Files in scope — **single repo** (`unified-trading-system-ui`), no cross-repo blast radius.

| File                                                               | Action                                                                                                        |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `public/homepage.html` (lines 534–621 CSS, 1225–1292 hero markup)  | Rewrite hero section: replace 4-tile path grid with 4-icon service row; restore H1; update CTAs + proof strip |
| `public/homepage.html` (lines 1297–1311 stats strip)               | Update: `$7.5M+ AUM` tile replaces "indicative"; keep 5-asset / venues / 24-7 / 100+ TB / 5-service-lines     |
| `components/marketing/public-depth-next-strip.tsx`                 | Remove left-side "Read client briefings..." sentence + mobile variant; keep right-side breadcrumb             |
| `tests/unit/components/public-pages.test.tsx`                      | Update hero-text assertions (H1 copy, tagline copy, trust-badge presence, proof-strip text)                   |
| `tests/unit/lib/marketing/load-marketing-static.test.ts`           | No change expected — structural, not content-specific                                                         |
| `tests/integration/marketing-static-signin.test.ts`                | Verify inline-script preservation still passes after hero rewrite (galaxy canvas + explorer panels untouched) |
| `e2e/marketing/homepage.spec.ts` (if exists — grep before Phase 3) | Update Playwright hero selectors                                                                              |

Sibling static HTML pages (`platform.html`, `signals.html`, `strategies.html`, `regulatory.html`, `who-we-are.html`,
`contact.html`) are **out of scope** — hero styling is homepage-only.

## Phase 0 — Decision brief (executed inline 2026-04-22 per "execute all" direction)

- [x] [HUMAN] P0. Decisions landed on defaults: H1 = `Unified Trading Infrastructure`; sub-tagline = old-site long
      sentence; service row = 4 (IM / DART / Odum Signals / Regulatory Umbrella); CTAs = `Discuss a Mandate`
      (Calendly) + `Explore the Platform`; AUM = `$7.5M+ AUM` (dropped "indicative").
- [x] [HUMAN] P0. Trust-badge row confirmed: FCA / Institutional Security / No-Code to Full-Code.
- [x] [HUMAN] P0. `Read client briefings...` left-side sentence removed; right-side
      `Next: Briefings → Book →     Questionnaire` breadcrumb stays.

**Exit criterion met:** defaults accepted; proceeded to Phase 1 in-session.

## Phase 1 — Hero rewrite (code)

- [x] [AGENT] P0. Rewrote `public/homepage.html` hero block (lines 1225–1292):
  - Kept `.hero-asset-pill`; extended `Prediction` → `Prediction Markets` label to match old-site pill.
  - H1 now `Unified Trading Infrastructure` (was `Odum Research`).
  - `hero-tagline` now old-site long sub-tagline.
  - Deleted `.hero-fca-block` (FCA now in trust-badge row).
  - Deleted `.hero-path-lead` + `.hero-path-grid` (4-tile grid with in-tile defs).
  - Added `.hero-service-row` — 4 icon buttons (IM / DART / Odum Signals / Regulatory Umbrella), same 4-colour accent
    mapping as the prior path-tiles, hover-def via same `::after data-def` pattern. Icons restyled: stroke-only,
    stroke-linecap round, 18px (down from 26px) — cleaner, less gimmicky.
  - Kept `.hero-ctas` verbatim (`Discuss a Mandate` Calendly + `Explore the Platform`).
  - Added new `.hero-stats` row — 5 items: `5 Asset Classes` / `100+ Venues` / `24/7 Trading` / `100+ TB Market Data` /
    `5 Service Lines`.
  - Added new `.hero-trust-row` — 3 chip badges: FCA Authorised (975797) / Institutional Security / No-Code to
    Full-Code, each with a stroke SVG (shield-check / lock / layers).
  - Rewrote `.proof-strip` — `$7.5M+ AUM — IM mandate scale` (dropped "indicative"); kept Professional & ECP + London,
    UK.
- [x] [AGENT] P0. Rewrote matching CSS — deleted `.hero-path-*`, `.hero-fca-block*`; added `.hero-service-row`,
      `.hero-service-tile` (+ hover/focus/`::after data-def`), `.hero-stats`, `.hero-stat`, `.hero-trust-row`,
      `.hero-trust-badge` (+ `.is-fca/.is-security/.is-flex` colour variants).
- [x] [AGENT] P0. Deleted duplicate stats-strip from Section 2 (the `<div class="stats-strip">` inside
      `<!-- ============ 2. PLATFORM BREADTH` — stats now live once, inside the hero); kept the "Four commercial paths
      vs five service lines" caption paragraph as a thin clarifier band.
- [x] [AGENT] P0. Existing `@media (max-width: 768px)` (line ~1154) works as-is — `.hero-service-row`, `.hero-stats`,
      `.hero-trust-row`, `.proof-strip` all use `flex-wrap: wrap` so phone widths collapse cleanly.
- [x] [AGENT] P0. Removed left-side `"Read client briefings for full scope, process, and fit."` sentence +
      `View briefings` link + the duplicate `sm:hidden` mobile span from
      `components/marketing/public-depth-next-strip.tsx`; right-side `Next: Briefings → Book → Questionnaire` breadcrumb
      stays. Wrapper DOM simplified: `flex flex-col gap-1` → single-row `flex items-center justify-end`.

### Phase 1b — Card row-alignment (added 2026-04-22 per user ask — "same row position for click-throughs, same block length")

- [x] [AGENT] P0. Made the four "Allocate. Run. Lease signals. Regulate." cards (`section 3` — IM / DART / Odum Signals
      / Regulatory Umbrella) align their click-through links on the same row regardless of content length: added
      `display: flex; flex-direction: column` to `.card`, `flex: 0 0 auto` to `.card > ul`, and `margin-top: auto` to
      `.card > .card-link`. CSS grid already stretches card heights to match the tallest; flex-column + auto-top margin
      pushes the link to the bottom of each card so all four `→` CTAs line up horizontally. Combined with the DART
      content trim (`section 3` DART card trimmed 780 → 313 visible chars via dotted-underline hover-over tooltips — see
      commit earlier in session), the four cards now read as a clean grid.

## Phase 2 — Tests + smoke

- [x] [AGENT] P0. Existing `tests/unit/components/public-pages.test.tsx` assertions still hold — `Odum Research` string
      still appears in the file (logo-text in header) so the loose `toContain` check passes; `Get Started` +
      `Book a Demo` still appear elsewhere in the file (CTA buttons on later sections);
      `unified trading     infrastructure` is now in the H1 itself; `FCA[^<]{0,80}975797` regex matches the new
      trust-badge text. No test edits required.
- [x] [AGENT] P0. Grepped `tests/` + `e2e/` for `Read client briefings`, `View briefings`, `hero-path-tile`, `hero-fca`,
      `Four ways to plug` — zero hits, no test updates needed.
- [x] [AGENT] P0. Vitest run: `tests/unit/components/public-pages.test.tsx` + `tests/unit/lib/marketing/` +
      `tests/integration/marketing-static-signin.test.ts` — **52/52 passed**.
- [x] [AGENT] P0. Live dev-server smoke (`http://localhost:3100/`): all 8 new strings render
      (`Unified Trading Infrastructure`, `The same infrastructure we use`, `$7.5M+ AUM`, `FCA Authorised (975797)`,
      `Institutional Security`, `No-Code to Full-Code`, `Discuss a Mandate`, `Explore the Platform`); zero hits for
      `hero-path-tile` or `Read client briefings`.
- [ ] [HUMAN] P1. Manual browser walk-through on 375px mobile — confirm hero + cards stack cleanly. Recommended before
      main-merge but not blocking dev push.
- [ ] [HUMAN] P1. Pass-1 QG (`bash scripts/quality-gates.sh`) — defer to merge time; no Python/UAC churn this round so
      QG should be a formality.

## Phase 3 — Commit + merge

- [ ] [AGENT] P0. Single combined commit on `live-defi-rollout`:
      `feat(homepage): restore old-hero structure + branded service row + trust-badge trio + aligned card CTAs` — covers
      homepage.html hero rewrite + section-2 stats-strip dedup + section-3 card flex alignment + PublicDepthNextStrip
      cleanup.
- [ ] [AGENT] P0. Push to `origin/live-defi-rollout` (manual `git push`, not quickmerge — this is a UI-only change with
      no upstream Python dep in play, matches session convention).

## Phase 4 — Follow-ups + sibling consistency

- [ ] [AGENT] P1. Sibling static pages (`platform.html`, `signals.html`, `strategies.html`, `regulatory.html`,
      `who-we-are.html`, `contact.html`) — audit their page-heros for consistency with new homepage hero. If any subpage
      repeats `Odum Research` as H1, strip it.
- [ ] [AGENT] P1. `app/(public)/investment-management/page.tsx` + `app/(public)/platform/page.tsx` — if any of these
      render a hero inline (not just `MarketingStaticFromFile`), check whether the new trust-badge trio should appear on
      those too. If yes, extract the badge row into a small shared component to avoid drift.
- [ ] [AGENT] P1. Codex SSOT update — add a short entry to `codex/14-playbooks/design/marketing-hero-structure.md` (new
      file if missing) documenting the hero blocks (asset-pill / H1 / tagline / service-row / CTAs / proof-strip /
      trust-row) so future agents don't drift.
- [ ] [HUMAN] P1. Deploy to production (odum-research.com) once main has merged; verify AUM line renders `$7.5M+`
      against the real prod build.

## Success criteria

**C-gates (Phase 1–3):**

- C1: hero rewrite lands; dev server renders cleanly on desktop + mobile.
- C2: vitest green (public-pages.test.tsx + integration marketing-static-signin.test.ts).
- C3: ruff / eslint / basedpyright clean — no new violations introduced.
- C4: Pass-1 QG green.
- C5: Quickmerge to main complete.

**B-gates:**

- B1: five decision rows landed in Phase 0.
- B6: Ikenna sign-off after production deploy — hero reads cleaner than the current live-defi-rollout build.

## Anticipated gotchas

- `homepage.html` is a single 2271-line static file with inline `<style>`, inline `<script>` (galaxy canvas + explorer
  JS), and hand-rolled markup. The hero block sits in the middle — CSS class-name drift between the new hero and the
  later sections (stats-strip, galaxy, who-we-serve) is the main regression risk. Keep `.stats-strip` +
  `.galaxy-section` untouched.
- `MarketingStaticFromFile` strips inline `<script>` tags and re-injects them — verify galaxy + explorer still animate
  after the rewrite.
- `PublicDepthNextStrip` is rendered on every public page, not just homepage. Dropping the left sentence there affects
  every public surface — acceptable per user ask (redundant with right-side breadcrumb).
- Trust-badge copy (`FCA Authorised (975797)`) — the FCA pill already sits in the site-header. Putting another copy in
  the hero trust-row is deliberate redundancy per the old-site design — if it reads as duplication at review, collapse
  to just `Institutional Security` + `No-Code to Full-Code` and rely on the header for FCA.
- Screenshot check on 375px (iPhone SE width) is non-negotiable — the old hero wraps cleanly; the current 4-tile grid
  does too; the rewrite must maintain that.
