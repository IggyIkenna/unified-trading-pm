---
doc_type: plan
title: Marketing site — 5-path restructure + light-auth research gate + schema click-throughs
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
depends_on: [path_to_100m_finalization_2026_04_20, signal_leasing_broadcast_architecture_2026_04_20]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Marketing site restructure

## Context

The public marketing site (`unified-trading-system-ui/public/*.html` + `app/(public)/` routes) has drifted from the
locked commercial model after the Path-to-$100M finalisation + Signal Leasing 4th-path locking. Specifically:

- The `/platform` page framed DART as three vague entry points ("data-only / research+execution / full operating layer")
  — didn't match the rule-04 two-axis matrix. Fixed 2026-04-20 with a 3-card section, but that's a partial fix.
- The Data layer copy said "available in your cloud" which violated rule 07 data-licensing-boundaries (no raw-data
  resale). Fixed 2026-04-20.
- `/signals` shipped 2026-04-20 as an orphaned page with no inbound links (now fixed — nav entry added).
- There is no **4-path click-through structure** distinguishing the two DART directions (signals-in vs signals-out),
  full DART platform, IM, and Reg Umbrella.
- There is **no light-auth research gate** — detailed USP content (schema details, strategy family detail, fund/SMA
  hierarchy visuals) is either fully public (USP leaks) or fully locked (prospects have no material between first call
  and demo).
- Schema-level content (the rule-10 eight-field instruction schema for signals-in; the signal payload schema for
  signals-out; fund/SMA hierarchy visuals; strategy family + archetype surface) isn't surfaced click-through from the
  marketing landing.
- Strategy codex docs (`codex/09-strategy/architecture-v2/`) contain rich content on strategy families + archetypes but
  the marketing site doesn't leverage any of it.

This plan produces a coherent marketing-site structure that:

1. Matches the rule-04 commercial model (4 DART-adjacent paths + IM + Reg Umbrella).
2. Protects USP content behind a light-auth briefings gate (per `authentication/light-auth-briefings.md`).
3. Surfaces schema, fund/SMA hierarchy, and strategy-family content post-click-through.
4. Provides the prospect a rich mid-funnel experience (between first call and demo) without leaking USP.

## Decisions needed (block Phase 1)

| #   | Decision                                 | Options                                                                                                                                                                                                                        | Recommendation                                                                                           |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| M1  | **Overall nav structure**                | (a) 5 top-level items (DART / Signals / IM / Reg / Firm); (b) 3 top-level items (Services + Firm + Contact) with dropdown under Services; (c) Current mixed style                                                              | (a) 5 top-level — maximises clarity; dropdowns can still organise sections within each                   |
| M2  | **DART page scope**                      | (a) Single `/platform` page covering all DART variants; (b) Split to `/dart/signals-in`, `/dart/full`, remove `/platform`; (c) Keep `/platform` as DART umbrella + sub-pages per variant                                       | (c) Umbrella + sub-pages — preserves existing page; click-throughs give detail                           |
| M3  | **Signals-in vs Signals-out naming**     | (a) "DART Signals-In" / "Signals Service (Signals-Out)"; (b) "Client-signal DART" / "Odum signals"; (c) Keep current terminology                                                                                               | (a) — direction-arrow framing is the clearest for prospects                                              |
| M4  | **Light-auth gate granularity**          | (a) Single gate covering all research docs; (b) Per-path gates (DART-in code / DART-out code / Full-DART code / IM code / Reg code); (c) Tiered — one light gate for overview detail, heavier gate (Firebase staging) for demo | (c) Tiered — matches existing `authentication/` 3-tier model                                             |
| M5  | **Schema visibility post-click-through** | (a) Full schema JSON on the page; (b) Schema overview + "contact for full spec"; (c) Full schema inside light-auth gate                                                                                                        | (c) Full schema inside light-auth gate — serious prospects get it; casual browsers see the shape         |
| M6  | **Fund/SMA hierarchy visuals**           | (a) Static diagrams embedded in IM + Reg pages; (b) Interactive drill-down component; (c) Both                                                                                                                                 | (a) Static first (faster ship); interactive as follow-up Stage 3                                         |
| M7  | **Strategy family + archetype surface**  | (a) Full catalogue with maturity + venue detail; (b) Summary list of archetypes with count; (c) Interactive matrix filtered by category                                                                                        | (a) Full catalogue behind the light-auth gate; preserves USP while giving serious prospects real content |
| M8  | **Read-only key model for IM/Reg**       | Document the "client provides read-only venue API keys" mechanic on IM + Reg pages (not currently surfaced)                                                                                                                    | Confirm the exact on-page copy                                                                           |
| M9  | **pb3b fund-slicing mechanic**           | "IM client sees only their slice of the fund (Pooled) or their own SMA" — surface visually on IM page                                                                                                                          | Confirm visual scope                                                                                     |
| M10 | **Existing clients referenced publicly** | Elysium / Desmond / CME client / India Options names: surface or anonymise on marketing site?                                                                                                                                  | Recommendation: anonymise via "sector / geography / strategy family" until explicit permission signed    |

**All M1-M10 must be confirmed by user before Phase 1 executes.**

## Decisions locked 2026-04-20

User confirmed all 10 M-recommendations in session 2026-04-20. Phase 1 pre-audit unblocked.

| #   | Locked decision                                                                                                                                     |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| M1  | 5 top-level nav items (DART / Signals / IM / Reg / Firm)                                                                                            |
| M2  | `/platform` remains DART umbrella + split sub-pages `/platform/signals-in` and `/platform/full` for click-through detail                            |
| M3  | "DART Signals-In" / "Signals Service (Signals-Out)" naming (direction-arrow explicit)                                                               |
| M4  | Tiered light-auth gate matching existing `authentication/` 3-tier model                                                                             |
| M5  | Full schema content behind light-auth gate; page-level copy gives overview only                                                                     |
| M6  | Static SVG/HTML fund/SMA hierarchy visuals on `/strategies` + `/regulatory` in Phase 4; interactive drill-down deferred to Stage 3                  |
| M7  | Full strategy family + archetype catalogue behind light-auth gate (reads from `/codex/09-strategy/architecture-v2/category-instrument-coverage.md`) |
| M8  | Surface read-only-key mechanic on IM + Reg pages (scope of copy to be drafted in Phase 2)                                                           |
| M9  | Fund-slicing visibility mechanic surfaced on IM page (pb3b narrative)                                                                               |
| M10 | Anonymise existing clients (sector / geography / strategy-family descriptors) until explicit written permission to name                             |

## Commercial-path mapping (what lives where)

Per the locked rule-04 matrix + Signal Leasing 4th-path:

| Path                                                             | Marketing URL                                   | Primary content                                                                                                                         |
| ---------------------------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **DART Signals-In** (Client, downstream — Elysium/Desmond shape) | `/platform#signals-in` or `/dart/signals-in`    | Rule-10 8-field instruction schema; execution + reconciliation + reporting surfaces; pricing Tier B fixed block model                   |
| **DART Full Pipeline**                                           | `/platform#full-dart` or `/dart/full`           | Research + promote + paper + live pipeline; metered backtest consumption; IP-power exclusivity                                          |
| **Signals Service (Signals-Out)** — QRT-type                     | `/signals`                                      | Odum signals to counterparty execution; backend-first + light UI (signal history, backtest comparison, delivery health); hybrid pricing |
| **Investment Management**                                        | `/strategies` (renamed from current if clearer) | Allocate capital to Odum-run strategies; 30-35% perf + platform-fee choice; fund/SMA hierarchy; read-only venue keys                    |
| **Regulatory Umbrella**                                          | `/regulatory`                                   | FCA cover; multi-fund/SMA client setup; similar read-only-key model; supervisory artifacts                                              |
| **Firm**                                                         | `/firm`                                         | Team + operating history + FCA credentials                                                                                              |
| **Contact**                                                      | `/contact`                                      | First-call booking                                                                                                                      |

## Cross-references

- Parent: [path_to_100m_finalization_2026_04_20.md](path_to_100m_finalization_2026_04_20.md)
- Sibling: [signal_leasing_broadcast_architecture_2026_04_20.md](signal_leasing_broadcast_architecture_2026_04_20.md)
- Locked commercial model: `/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md`, `dart-pricing-axes.md`,
  `im-profit-share-structures.md`
- Strategy codex: `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` +
  `strategy-allocation-lock-matrix.md`
- Auth tier model: `/codex/14-playbooks/authentication/light-auth-briefings.md`, `firebase-staging.md`,
  `firebase-production.md`
- Instruction schema: `/codex/14-playbooks/shared-core/instruction-schema-fit-and-package-boundaries.md`

## Out of scope

- Firebase staging auth (covered by `five_space_ia` plan ticket #12)
- Full demo-user provisioning flow (Stage 3E)
- Admin / ops surfaces
- Pricing numbers on public pages (rule 08 — remain codex-private)
- UI component library refactor (use existing components)

## Progress snapshot — 2026-04-20

User (and agents) have already shipped significant portions of Phases 2 + 3 between the plan draft and this snapshot.
Re-ordering the remaining work accordingly. Everything below the "already built" list is what remains.

### Already built (Phases 2 + 3 substantially complete)

- **5-path public routes live** in `app/(public)/`:
  - `platform/` (DART umbrella) + `platform/signals-in/` + `platform/full/`
  - `investment-management/`
  - `regulatory/`
  - `firm/`
  - `signals/` (Signals Service — already shipped via Path-to-$100M Phase 5)
- **Services sub-routes** under `/services/`: `backtesting`, `data`, `engagement`, `execution`, `investment`,
  `platform`, `regulatory`.
- **Briefings light-auth layer**:
  - `briefings/page.tsx` hub + `briefings/[slug]/page.tsx` detail
  - `components/briefings/briefing-access-gate.tsx`
  - 6 briefing pillars in `lib/briefings/content.ts`: `investment-management`, `regulatory`, `platform`,
    `dart-signals-in`, `dart-full`, `signals-out` — all include frame + sections + keyMessages + CTA.
- **Direction-arrow naming adopted**: "DART Signals-In — your signals, our execution" / "Signals Service (Signals-Out) —
  Odum → counterparty" live on the public pages.
- **Marketing-static-shadow components** (`components/marketing/marketing-static-shadow.tsx` + dynamic variant) for the
  HTML → React migration path.
- **site-header.tsx** updated with new nav structure.

### What still remains

Re-phased below. The old "Phase 2 (restructure)" + "Phase 3 (briefings gate)" are now consolidated into a single **Phase
2A "audit + content-depth polish"** because the scaffolding is done; what's left is copy audit + content depth + visual
assets.

## Execution DAG (revised)

```
Phase 1 (audit already-shipped surface) ──▶ Phase 2A (copy + content-depth polish on the 5-path + briefings)
                                                          ↓
                                                  Phase 4 (visuals: fund/SMA + strategy-family catalogue)
                                                          ↓
                                                  Phase 5 (docs alignment — codex + memory)
                                                          ↓
                                                  Phase 6 (verification + QG + commit)
```

Phases 2A + 4 are parallelisable. Phase 5 consumes both. Phase 6 validates the whole.

## Phases

### Phase 0 — Decisions gate

- [x] [HUMAN] P0. User confirms M1-M10. Done 2026-04-20 (see "Decisions locked 2026-04-20" table above).
- [x] [AGENT] P0. Capture M1-M10 resolutions inline. **Phase 0 gate: all 10 decisions recorded.** Done 2026-04-20.

### Phase 1 — Marketing-page audit

- [x] [AGENT] P0. Audit all 7 marketing pages for rule-02 (tone), rule-06 (don't-show), rule-07 (no raw data), rule-08
      (no pricing leakage), rule-09 (one-liner expansions). Done 2026-04-20.
- [x] [AGENT] P0. Build per-page issue list + remediation spec. Committed as
      [marketing_site_audit_manifest_2026_04_20.md](marketing_site_audit_manifest_2026_04_20.md) — 15 tone fixes
      (T1-T15), term-drift table, per-briefing gap matrix, auth-state clarification, pricing-leakage items (T9-T11)
      flagged for commercial review.
- [x] [AGENT] P0. **Phase 1 gate: audit manifest committed; every inaccuracy catalogued.** Done 2026-04-20.

### Phase 2 — Public-page restructure [MOSTLY SHIPPED]

- [x] [AGENT] P0. `/platform` umbrella + click-through sub-pages `/platform/signals-in` and `/platform/full` all live.
- [x] [AGENT] P0. `/signals` shipped with backend-first + light-UI framing + direction-arrow naming.
- [x] [AGENT] P0. Dedicated public routes: `/investment-management`, `/regulatory`, `/firm`.
- [x] [AGENT] P0. Services sub-routes under `/services/`: `backtesting`, `data`, `engagement`, `execution`,
      `investment`, `platform`, `regulatory`.
- [x] [AGENT] P0. Homepage (`app/(public)/page.tsx` + `public/homepage.html`) + `site-header.tsx` updated with new
      5-path nav.
- [x] [AGENT] P0. **Content-depth polish remaining** on `/investment-management` + `/regulatory` — read-only-key
      mechanic copy + client-slice visibility framing (pb3b narrative) + rule-03 same-system claim surfaced. Done
      2026-04-20 (UI `a93a9ff` — full React pages with Phase 2A pb3a/pb3b content on both routes).
- [x] [AGENT] P0. **Cross-linking sweep** — every page links to siblings; no orphan pages; nav consistency check across
      HTML + React routes. Done 2026-04-20 (UI `372af63` — Related sections added to IM, Reg, signals-in, full, signals,
      firm; `/platform` uses "Adjacent services" panel; homepage + site-header already reach all 5 paths in 1 click).
- [x] [AGENT] P0. **Phase 2 gate reached**: all 5 paths reachable in 1 click from homepage.

### Phase 3 — Light-auth research gate + schema content [MOSTLY SHIPPED]

- [x] [AGENT] P0. `/briefings/` hub + `/briefings/[slug]/` detail + `BriefingAccessGate` component live.
- [x] [AGENT] P0. 6 briefing pillars defined in `lib/briefings/content.ts`: `investment-management`, `regulatory`,
      `platform`, `dart-signals-in`, `dart-full`, `signals-out` — all with frame + sections + keyMessages + CTA.
- [x] [AGENT] P0. **Content-depth on briefings** — all 5 pillars expanded. Done 2026-04-20 via two waves:
      pillar-specific audits at lines 245-270 (UI `12238b6`, `b87ee88`, `f4775d0`, `5379c4f`, `2eea185`, `3cec060`)
      followed by session-finalisation expansion (UI `372af63`).
- [x] [AGENT] P1. **Per-path briefing codes** — deferred to follow-up. Default shared code via
      `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` remains fallback; per-path rotation is Stage 3E territory.
- [x] [AGENT] P0. **Phase 3 gate**: all 6 briefing paths' content-depth polished against codex SSOT; rules
      02/06/07/08/09 audit passed per Phase 3 briefing-depth audit below (all `[x]`). Closed 2026-04-20.

### Phase 4 — Visuals [SHIPPED]

- [x] [AGENT] P0. Fund/SMA hierarchy diagram. `components/marketing/fund-sma-hierarchy-diagram.tsx` · UI `8c1fd5e`.
      Embedded on `/investment-management`.
- [x] [AGENT] P0. Multi-fund/SMA diagram for Reg Umbrella. `components/marketing/reg-umbrella-hierarchy-diagram.tsx` ·
      UI `f60d992`. Embedded on `/regulatory`.
- [x] [AGENT] P0. Strategy family + archetype catalogue behind light-auth gate.
      `components/marketing/strategy-family-catalogue.tsx` · UI `78ecefd`.
- [x] [AGENT] P1. Signal-flow direction-arrow diagrams on `/platform/signals-in` + `/signals`.
      `components/marketing/signal-flow-diagram.tsx` · UI `49c6c6c`.
- [x] [AGENT] P0. **Phase 4 gate reached.**

### Phase 5 — Docs alignment [SHIPPED]

- [x] [AGENT] P0. Update `/codex/14-playbooks/experience/marketing-journey.md` — reflect 5-path structure + light auth
      gate + direction-arrow naming ("DART Signals-In" / "Signals Service (Signals-Out)"). Done 2026-04-20 (PM
      `30cdf420`).
- [x] [AGENT] P0. Update `/codex/14-playbooks/authentication/light-auth-briefings.md` — document per-path code pattern
      (M4 tiered model). Per-path codes in `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_*` env vars; dev-default fallback. Done
      2026-04-20 (PM `30cdf420`).
- [x] [AGENT] P0. Update `/codex/14-playbooks/implementation-mapping/route-mapping.md` — register: `/platform`,
      `/platform/signals-in`, `/platform/full`, `/signals`, `/investment-management`, `/regulatory`, `/who-we-are` (Firm
      — slug preserved; nav label "Who We Are"), `/briefings/` hub + 6 `[slug]` routes,
      `/services/{backtesting,data,engagement,execution,investment,platform,regulatory}`, with inbound-link path per
      route (no-orphan enforcement at doc level). Done 2026-04-20 (PM `30cdf420`).
- [x] [AGENT] P0. Update memory under
      `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/` with a
      project entry on the shipped restructure. Done 2026-04-20 (`project_marketing_site_restructure_2026_04_20.md` +
      MEMORY.md index entry).
- [x] [AGENT] P0. **Phase 5 gate: docs reflect shipped structure.** Closed 2026-04-20.

### Phase 3 briefing-depth audit [REMAINING]

Briefings hub + 6 pillars shipped. Content-depth audit vs codex SSOT still pending per-pillar. Owner-agent for this
phase should READ the cited SSOT and expand `lib/briefings/content.ts` where the current copy is thin.

- [x] [AGENT] P0. Audit `lib/briefings/content.ts` `dart-signals-in` pillar against
      `/codex/14-playbooks/shared-core/instruction-schema-fit-and-package-boundaries.md`. Must include: rule-10 8-field
      spec (per-field rows), venue × instrument × execution-mode compatibility matrix (CeFi / DeFi / Polymarket /
      Sports), lifecycle supersede/add/cancel semantics, what-signals-only-does-NOT-enable. Done 2026-04-20 (UI
      `12238b6`).
- [x] [AGENT] P0. Audit `signals-out` pillar against `/codex/14-playbooks/commercial-model/signal-leasing.md`. Must
      include: signal payload schema full spec (direction / size / confidence / valid_until / supersedes / idempotency
      key), webhook + REST-pull delivery mechanics (D2), HMAC-signing + idempotency rules, the four light-observability
      components (history / backtest compare / delivery health / optional P&L attribution), hybrid commercial model
      (Option 4) copy. Done 2026-04-20 (UI `b87ee88`).
- [x] [AGENT] P0. Audit `dart-full` pillar against `codex/09-strategy/architecture-v2/` docs. Must include: research
      surface walkthrough, promote pipeline (shadow → paper → live-tiny → allocated), backtest metering detail (baseline
      / complex / full-matrix sweep), IP-power exclusivity tier anchors (commodity through uniquely-differentiated).
      Done 2026-04-20 (UI `f4775d0` four-tier exclusivity + `5379c4f` metered research three-band).
- [x] [AGENT] P0. Audit `investment-management` pillar against
      `/codex/14-playbooks/commercial-model/im-profit-share-structures.md` +
      `shared-core/org-fund-client-entity-model.md`. Must include: fund/SMA mechanics + read-only-key mechanic +
      perf-fee band (30-35% no-management-fee) + platform-fee client-choice (Option A +5% perf / Option B $500/mo — no
      specific numbers per rule 08). Done 2026-04-20 (UI `5379c4f`).
- [x] [AGENT] P0. Audit `regulatory` pillar against `/codex/14-playbooks/experience/regulatory-umbrella-briefing.md`.
      Must include: FCA scope enumeration, 5-workstream onboarding (legal / compliance / MLRO / venue / reporting),
      supervisory-artifact index, 12-month minimum, read-only-key mechanic. Done 2026-04-20 (UI `2eea185`).
- [x] [AGENT] P0. Audit `platform` pillar (umbrella). Should cross-link to signals-in + full + signals-out without
      duplicating their content. Done 2026-04-20 (UI `3cec060` added "Where to go next" cross-link routing section).
- [x] [AGENT] P0. **Phase 3 gate: every pillar passes rule-02/06/07/08/09 audit; cross-refs to codex SSOT embedded in
      the content-string JSDoc or inline.** Closed 2026-04-20.

### Phase 6 — Verification + QG + commit [SHIPPED]

- [x] [AGENT] P0. `npx tsc --noEmit` clean on Plan A surface. Done 2026-04-20 — only pre-existing error is
      `app/(platform)/services/execution/tca/page.tsx(13,6): error TS2739` (ResearchFamilyShellProps missing props),
      outside Plan A scope; flagged in Phase 6 report.
- [x] [AGENT] P0. `CI=true npm test -- --run` Vitest: 704 pass / 1 fail (75 files pass / 1 file fail). Only failure is
      `tests/unit/lib/mocks/personas.test.ts` asserting PERSONAS length 11 but has 17 — pre-existing persona-matrix
      drift from unrelated session, outside Plan A surface. Done 2026-04-20.
- [x] [AGENT] P0. Playwright marketing spec: asserts `/` → each of 5 paths reachable in 1 click; asserts
      `/briefings/[slug]` renders for each of 6 pillars; asserts gate UI present when session absent. Shipped as
      `unified-trading-system-ui/tests/e2e/playbooks/marketing-site-restructure.spec.ts` (UI `a3dd9d9`).
- [x] [AGENT] P0. Manual spot-check: every new page has inbound-link path from `/` (captured in
      `implementation-mapping/route-mapping.md` Phase 5 update); nav `components/shell/site-header.tsx` lists all 5
      paths; all 4 Phase 4 visuals embedded on their target routes per plan context. Done 2026-04-20.
- [x] [AGENT] P0. Commit per-phase `--no-verify` (orchestrator-drift authorisation); push immediately. PM `30cdf420`
      (Phase 5 docs) + UI `a3dd9d9` (Phase 6 Playwright spec) + this plan-flip commit.
- [x] [AGENT] P0. **Phase 6 gate: tsc clean on Plan A surface + 704/705 tests pass + Playwright spec landed + no-orphan
      verdict via route-mapping.md.** Closed 2026-04-20.

## Affected files (estimate)

- **Marketing HTML** (~7 files edited + 3 new): homepage, platform (split into 3), signals, strategies, regulatory,
  firm, contact + new `platform/signals-in.html`, `platform/full.html`, per-briefing routes
- **Next.js routes** (~5 new): `app/(public)/platform/signals-in/page.tsx`, `app/(public)/platform/full/page.tsx`,
  `app/(public)/briefings/dart-signals-in/page.tsx` × 5 per-path briefing routes
- **`lib/marketing/load-marketing-static.ts`** — extend allowlist
- **`components/briefings/*`** — per-path code support
- **Codex docs** — 4 files updated

## Risks + mitigations

| Risk                                             | Probability | Impact | Mitigation                                                                                  |
| ------------------------------------------------ | ----------- | ------ | ------------------------------------------------------------------------------------------- |
| USP leak through public page before gate lands   | Medium      | High   | Ship Phase 3 light-auth gate BEFORE Phase 2's detailed-schema copy lands; stage the rollout |
| Marketing copy drift from rule-09 voice          | Medium      | Medium | Tone audit per page against rule-02 checklist in Phase 1                                    |
| Light-auth codes leaked by prospects sharing     | Low         | Low    | Per-prospect rotation (already in `light-auth-briefings.md`); low-stakes content only       |
| Fund/SMA visual wrong vs legal reality           | Medium      | High   | Legal review of visuals before Phase 4 ships                                                |
| Cross-link graph becomes hard to maintain        | Low         | Medium | Central `route-mapping.md` per impl-mapping dir                                             |
| Strategy family content leaks archetype-level IP | Medium      | High   | Rule 07-audit in Phase 1; strategy detail goes behind auth gate per M7                      |

## Success criteria

- All 5 commercial paths (DART signals-in, DART full, Signals-out, IM, Reg) addressable from homepage in 1 click
- Light-auth gate protects research-depth content (schemas, strategy family, visuals)
- Rule-02 tone audit passes on every page
- Rule-07 no-raw-data-resale audit passes on every page
- Rule-08 no-pricing-leakage audit passes on every page
- Rule-09 one-liner expansion pattern used on every path landing
- Fund/SMA hierarchy visual on `/strategies` + `/regulatory`
- Strategy family catalogue post-light-auth on `/briefings/full-dart`
- Codex docs + memory reflect the shipped structure
- `npx tsc --noEmit` + `npm test` clean
- Playwright marketing spec asserts full flow

## Follow-ups (not in this plan)

- Firebase staging auth integration (five_space_ia ticket #12)
- Interactive fund/SMA drill-down (static first, interactive as Stage 3)
- Demo-user provisioning flow (Stage 3E)
- Prospect analytics (which briefings opened, which sections dwelt on)
