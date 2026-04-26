---
name: marketing-site-three-route-consolidation
overview:
  Collapse five public commercial paths to three, harden gating, standardize naming via dual-label SSOT, build Strategy
  Review surface, align IR + signed-in depth content
type: code
epic: marketing-site-v2
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-26
created: 2026-04-26
priority: P0
completion_gates:
  code: C5
  deployment: D0
  business: B6
repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
depends_on: []
---

## Context

The current public site signals "we do everything" via five competing top-level routes (Investment Management / DART
Signals-In / DART Full / Odum Signals / Regulatory Umbrella + Who-We-Are). It carries naming drift between marketing
copy, signup form labels, codex SSOT, and admin tooling; lacks a per-prospect tailored layer between Strategy Evaluation
and the Tailored Demo (`/strategy-review` does not exist); and exposes long-form content (FAQ, founder story) on public
pages that should be gated.

The user reviewed an external "Odum Website Refactor Guide" proposing collapse-to-three commercial paths, naming
standardization, and a controlled progressive-disclosure funnel. After critique + multiple decision rounds, the agreed
direction is: **three public engagement routes** (Odum-Managed Strategies, DART Trading Infrastructure, Regulated
Operating Models) with Investment Management / Regulatory Umbrella retained as legal/contract labels; "Start Your
Review" as the homepage primary CTA routing through `/start-your-review` → `/questionnaire`; a new `/strategy-review`
per-prospect magic-link surface; briefings consolidated 6 → 3 pillars with Risk-and-Governance + Working-with-Odum
content folded into existing pillars (no "Coming soon" pages); plus IR presentations and signed-in platform-services
depth content aligned to the new naming.

User is shipping tomorrow (2026-04-27). Phases 1–4 must ship together as one release train per the Release Rule —
half-renamed state would look worse than the current state.

**Companion docs:**

- Full plan + critique: `~/.claude/plans/below-is-the-full-radiant-lighthouse.md`
- Funnel SSOT (will be updated in Phase 0): `unified-trading-pm/codex/08-workflows/signup-signin-workflow.md`
- Sibling marketing plan (older): `marketing_homepage_old_hero_migration_2026_04_22.plan.md`

## Decisions (binding — confirmed by user)

| #   | Decision                                          | Rule                                                                                                                                                                                                                                      |
| --- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Hero CTAs                                         | Primary `Start Your Review` → `/start-your-review` → `Begin Questionnaire` → `/questionnaire`. Secondary `Contact Odum`. NO direct `Book a call` on homepage.                                                                             |
| 2   | Investment Management label                       | Dual-layer. Marketing surfaces show "Odum-Managed Strategies"; legal/signup/admin keep "Investment Management". URL slug `?service=investment` unchanged.                                                                                 |
| 3   | Regulatory label                                  | Dual-layer (softer). Marketing shows "Regulated Operating Models"; existing legal/admin may retain "Regulatory Umbrella" for backwards compat. New legal drafting prefers specific structure name. TODO: post-refactor compliance review. |
| 4   | Catalogue exposure                                | Curated subset at Strategy Review (deferred to v2); full catalogue at Bespoke Tailoring per codex SSOT §2.6. Strategy Review v1 ships without catalogue.                                                                                  |
| 5   | Story trio                                        | `/who-we-are` + `/story` + `/our-story` left as-is.                                                                                                                                                                                       |
| 6   | Risk-and-Governance + Working-with-Odum briefings | Do NOT expose dedicated pages. If route scaffolds are required by tooling they must immediately call `notFound()` and not appear in nav/cards/links. No "Coming soon". Content folds into existing pillars + `/briefings` index.          |
| 7   | `/contact` placement                              | Keep in primary nav. Restructure page: primary CTA = Start Your Review; four contact tracks (General · Existing client · Press · Advisor); Calendly behind "Prefer to speak first?" sub-section.                                          |
| 8   | Route slugs                                       | All canonical URL slugs unchanged. `/platform` stays canonical for DART (do NOT create `/dart`). `/regulatory` stays canonical (display "Regulated Operating Models").                                                                    |
| 9   | DART briefing canonical slug                      | `/briefings/dart-trading-infrastructure`. Redirects from `/briefings/{platform,dart,dart-full,dart-signals-in,signals-out}` → new slug.                                                                                                   |

## Release Rule (binding)

Do NOT ship a half-refactored public state. **Release sequencing:**

- Phases 1–4 must merge together or behind one feature branch (atomic).
- Phase 5 (Strategy Review) can ship in the same train OR as a feature-gated follow-up if not ready in time.
- Phase 6 (visual + contact pass) should ship with the public release.
- Phases 7–8 (IR materials + signed-in platform depth) are alignment passes that follow the same naming rules but should
  NOT block the core public refactor unless those surfaces are currently visible to prospects/advisors.

A release where the homepage shows new positioning but the nav still exposes the old five-path model (or vice versa) is
forbidden.

## Pre-audit manifest

| File                                                                         | Phase | Action                                                                                                                                                                      |
| ---------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-pm/codex/08-workflows/signup-signin-workflow.md`            | 0     | Insert §2.4b Strategy Review stage; rename Regulatory Umbrella → Regulated Operating Models in marketing-context table cells; keep IM/Reg legal labels in §2.7.2 path table |
| `unified-trading-pm/codex/08-workflows/prospect-questionnaire-flow.md`       | 0     | Sync naming changes                                                                                                                                                         |
| `unified-trading-system-ui/lib/copy/service-labels.ts`                       | 1     | NEW — `SERVICE_LABELS` SSOT dict with `marketing` + `legal` + `slug` per service                                                                                            |
| `unified-trading-system-ui/components/shell/site-header.tsx`                 | 1, 2  | Display labels in Phase 1; collapse 5 → 3 in Phase 2                                                                                                                        |
| `unified-trading-system-ui/components/shell/spaces-nav-sections.tsx`         | 1, 2  | Match site-header (duplicated surface)                                                                                                                                      |
| `unified-trading-system-ui/components/shell/nav-copy.ts`                     | 1     | Re-export from SERVICE_LABELS                                                                                                                                               |
| `unified-trading-system-ui/app/(public)/investment-management/page.tsx`      | 1     | Display label "Odum-Managed Strategies"; URL stays                                                                                                                          |
| `unified-trading-system-ui/app/(public)/regulatory/page.tsx`                 | 1     | Display label "Regulated Operating Models"; URL stays                                                                                                                       |
| `unified-trading-system-ui/content/briefings/*.yaml`                         | 1, 4  | Title/TLDR copy (Phase 1); pillar consolidation 6 → 3 + new canonical slugs (Phase 4)                                                                                       |
| `unified-trading-system-ui/public/homepage.html`                             | 1, 3  | Hero subheading + meta (Phase 1); deletion when React rebuild lands (Phase 3)                                                                                               |
| `unified-trading-system-ui/app/(public)/platform/{signals-in,full}/page.tsx` | 2     | Delete + 301 redirect to `/platform`                                                                                                                                        |
| `unified-trading-system-ui/app/(public)/signals/page.tsx`                    | 2     | Delete + 301 redirect to `/platform#signals-capability`                                                                                                                     |
| `unified-trading-system-ui/next.config.mjs`                                  | 2, 4  | Route + briefing redirect rules                                                                                                                                             |
| `unified-trading-system-ui/lib/auth/tier-override.ts`                        | 2     | Remap TIER_BUNDLES off deleted Signals path                                                                                                                                 |
| `unified-trading-system-ui/app/(public)/page.tsx`                            | 3     | Replace `MarketingStaticFromFile` with React composition (Hero, EngagementRoutes, WhyOdum, EngagementJourney, GovernanceAndRisk, FinalCTA)                                  |
| `unified-trading-system-ui/app/(public)/start-your-review/page.tsx`          | 3     | NEW context page                                                                                                                                                            |
| `unified-trading-system-ui/app/(public)/briefings/page.tsx`                  | 4     | BRIEFING_PILLARS = 3 entries; embed Working-with-Odum section                                                                                                               |
| `unified-trading-system-ui/app/(public)/faq/page.tsx`                        | 4     | Trim 15 → 8–10 Q&As; migrate rest to faq-extended.yaml                                                                                                                      |
| `unified-trading-system-ui/app/(public)/strategy-review/page.tsx`            | 5     | NEW server component, magic-link gate, force-dynamic                                                                                                                        |
| `unified-trading-system-ui/app/(public)/strategy-review/_client.tsx`         | 5     | NEW                                                                                                                                                                         |
| `unified-trading-system-ui/app/api/strategy-review/issue-link/route.ts`      | 5     | NEW admin endpoint                                                                                                                                                          |
| `unified-trading-system-ui/app/api/strategy-review/verify/route.ts`          | 5     | NEW                                                                                                                                                                         |
| `unified-trading-system-ui/app/(ops)/admin/strategy-reviews/page.tsx`        | 5     | NEW admin list + revoke                                                                                                                                                     |
| `unified-trading-system-ui/lib/briefings/session.ts`                         | 5     | One-token-two-doors hook                                                                                                                                                    |
| `unified-trading-system-ui/app/(public)/contact/page.tsx`                    | 6     | Restructure: Start Your Review primary; four contact tracks; Calendly demoted                                                                                               |
| `unified-trading-system-ui/components/shell/site-footer.tsx`                 | 6     | Footer-only links                                                                                                                                                           |
| All public pages                                                             | 6     | Visual minimum pass per Completion Patch §E                                                                                                                                 |
| `unified-trading-system-ui/app/(authenticated)/investor-relations/*`         | 7     | IR copy + service-list cards aligned to three-route + canonical labels                                                                                                      |
| `unified-trading-system-ui/public/decks/` or `public/investor-relations/*`   | 7     | Static IR deck artefacts (if any) refreshed                                                                                                                                 |
| `unified-trading-system-ui/app/(platform)/dashboard/*`                       | 8     | Service cards + headings                                                                                                                                                    |
| `unified-trading-system-ui/app/(platform)/services/*`                        | 8     | Depth content (catalogue, research, trading, execution, IM funds, signals counterparty, reports)                                                                            |
| `unified-trading-system-ui/components/platform/*`                            | 8     | Shared service-label rendering                                                                                                                                              |

**Authenticated routes protected from rename (per Completion Patch §L):** `/services/signals/dashboard`,
`/services/im/funds`, `/dashboard`, `/admin`, `/signup?service=investment`, `/signup?service=regulatory`. Marketing
labels can change; route contracts and service slugs do NOT.

---

## Phase 0 — Codex SSOT updates (foundation, low-risk)

- [ ] [AGENT] P0. Update `signup-signin-workflow.md`: insert new §2.4b "Strategy Review" stage between current §2.4
      (Strategy Evaluation) and §2.5 (Tailored demo). Update funnel diagram (lines 30-72) to nine stages.
- [ ] [AGENT] P0. Update `signup-signin-workflow.md` §2.7.2 path table: keep "Investment Management" + "Regulatory
      Umbrella" in the legal/contract column; ADD a marketing-display-label column noting "Odum-Managed Strategies" /
      "Regulated Operating Models" / "DART Trading Infrastructure".
- [ ] [AGENT] P0. Update `signup-signin-workflow.md` prose: replace "Regulatory Umbrella" with "Regulated Operating
      Models" wherever the context is marketing/positioning (NOT in the legal/contract column or §2.7.2 service-category
      fields).
- [ ] [AGENT] P0. Update `prospect-questionnaire-flow.md`: sync any naming changes that surface to prospects.
- [ ] [AGENT] P0. Run PM QG: `cd unified-trading-pm && bash scripts/quality-gates.sh` — codex docs are part of QG.
- [ ] [AGENT] P0. Quickmerge PM:
      `bash scripts/quickmerge.sh "docs(codex): insert Strategy Review stage; align naming to three-route model" --agent`.

**Exit criterion:** PM main updated; codex contracts ready for the UI changes that follow.

---

## Phase 1 — SERVICE_LABELS SSOT + naming standardization (UI copy only)

Phases 1–4 ship together as one release train per Release Rule. Phase 1 introduces the SSOT and updates copy without
changing routes.

- [ ] [AGENT] P0. Create `unified-trading-system-ui/lib/copy/service-labels.ts` with `SERVICE_LABELS` exporting
      `{ investment, dart, regulatory, signals }` keys, each `{ marketing, legal, slug }` strings. Add JSDoc explaining
      marketing vs legal context.
- [ ] [AGENT] P0. Update `components/shell/site-header.tsx` to import from `SERVICE_LABELS`; keep five entries (collapse
      comes Phase 2); display labels are the marketing variants.
- [ ] [AGENT] P0. Update `components/shell/spaces-nav-sections.tsx` identically — duplicated surface per
      `feedback_site_header_duplicates_spaces_nav.md`. Same commit.
- [ ] [AGENT] P0. Update `components/shell/nav-copy.ts` to re-export from `SERVICE_LABELS`.
- [ ] [AGENT] P0. Update `app/(public)/investment-management/page.tsx` page title + h1 + breadcrumbs to "Odum-Managed
      Strategies". URL stays `/investment-management`.
- [ ] [AGENT] P0. Update `app/(public)/regulatory/page.tsx` page title + h1 + breadcrumbs to "Regulated Operating
      Models". URL stays `/regulatory`.
- [ ] [AGENT] P0. Update `content/briefings/*.yaml` titles + TLDRs to marketing labels.
- [ ] [AGENT] P0. Update `public/homepage.html` hero subheading + meta description (will be replaced wholesale in Phase
      3).
- [ ] [AGENT] P0. Confirm legal-surface consumers UNCHANGED: `app/(public)/signup/components/signup/signup-data.ts`,
      signup wizard service-confirmation rows, `app/(ops)/admin/*`, email templates — they continue to render
      "Investment Management" / "Regulatory Umbrella".
- [ ] [AGENT] P0. Grep audit: every
      `Investment Management|Regulatory Umbrella|Odum-Managed Strategies|Regulated Operating Models` occurrence is in
      the correct (legal vs marketing) context.
- [ ] [AGENT] P0. Run UI tests: `cd unified-trading-system-ui && CI=true npm test -- --run`. Update snapshots for
      nav-label changes.
- [ ] [AGENT] P0. Manual smoke: `/`, `/investment-management`, `/regulatory` show marketing labels;
      `/signup?service=investment` shows "Investment Management" service category.

---

## Phase 2 — Route consolidation (5 → 3 commercial paths)

- [ ] [AGENT] P0. Delete `app/(public)/platform/signals-in/page.tsx` and `app/(public)/platform/full/page.tsx`. Add 301
      redirects in `next.config.mjs`: `/platform/signals-in` → `/platform#signals-in-capability`; `/platform/full` →
      `/platform#full-stack-capability`.
- [ ] [AGENT] P0. Delete `app/(public)/signals/page.tsx`. Add 301 redirect `/signals` → `/platform#signals-capability`.
- [ ] [AGENT] P0. Rebuild `app/(public)/platform/page.tsx` as the single "DART Trading Infrastructure" page. Absorb
      Signals-In, Full, and Odum Signals as in-page sections (anchors `#signals-in-capability`,
      `#full-stack-capability`, `#signals-capability`). Display label "DART Trading Infrastructure"; URL stays
      `/platform`. Do NOT create `/dart`.
- [ ] [AGENT] P0. Update `components/shell/site-header.tsx`: drop NAV_FIVE_PATHS to NAV_THREE_ROUTES =
      `[/investment-management, /platform, /regulatory, /who-we-are, /contact]`. CTAs: primary "Start Your Review" →
      `/start-your-review`, secondary "Contact Odum" → `/contact`, top-right "Client Login" → `/login`.
- [ ] [AGENT] P0. Update `components/shell/spaces-nav-sections.tsx` to match (same commit).
- [ ] [AGENT] P0. Remap `lib/auth/tier-override.ts` TIER_BUNDLES that reference the deleted standalone Signals path.
- [ ] [AGENT] P0. Verify: `bash scripts/dev-tiers.sh --tier 1`, Playwright-click every legacy URL, confirm 301 + correct
      landing.
- [ ] [AGENT] P0. Verify protected routes unchanged: `/services/signals/dashboard`, `/services/im/funds`, `/dashboard`
      all still resolve for authenticated users.

---

## Phase 3 — Homepage rebuild (static HTML → React) + /start-your-review

- [ ] [AGENT] P0. Replace `app/(public)/page.tsx` body: drop `<MarketingStaticFromFile file="homepage.html" />`; render
      React composition with `<Hero>`, `<EngagementRoutes>` (3 cards), `<WhyOdum>`, `<EngagementJourney>` (six-step),
      `<GovernanceAndRisk>`, `<FinalCTA>`. Reuse `Card`, `Button`, `Term` primitives.
- [ ] [AGENT] P0. Hero CTAs: primary "Start Your Review" → `/start-your-review`, secondary "Contact Odum" → `/contact`.
      NO direct "Book a call" on homepage.
- [ ] [AGENT] P0. Three engagement-route cards (Odum-Managed Strategies / DART Trading Infrastructure / Regulated
      Operating Models): one-sentence explanation + 3 bullets max + CTA to the relevant `/investment-management`,
      `/platform`, `/regulatory` page.
- [ ] [AGENT] P0. Word budget enforcement (Completion Patch §C): homepage 700–1,000 words max. Cut repeated asset-class
      lists, "everything" claims, and lifecycle prose.
- [ ] [AGENT] P0. Apply public asset-class rule (Completion Patch §F): minimal asset-class language in hero; concrete
      examples allowed only on engagement-route pages.
- [ ] [AGENT] P0. Apply SEO metadata (Completion Patch §J): homepage title
      `Odum Research | Systematic Strategies and Trading Infrastructure`; description per spec.
- [ ] [AGENT] P0. Add analytics events (Completion Patch §I): `homepage_start_review_click`, `homepage_contact_click`,
      `engagement_route_card_click`.
- [ ] [AGENT] P0. Create `app/(public)/start-your-review/page.tsx` (250–450 words): explains fit-review process; primary
      CTA "Begin Questionnaire" → `/questionnaire`; secondary "Book a call instead" → `/contact`.
- [ ] [AGENT] P0. Add analytics events on `/start-your-review`: `start_review_begin_questionnaire_click`,
      `start_review_book_call_click`.
- [ ] [AGENT] P0. Delete `public/homepage.html` after React rebuild lands.

---

## Phase 4 — Briefings consolidation (no "Coming soon" anywhere)

- [ ] [AGENT] P0. Update `app/(public)/briefings/page.tsx` `BRIEFING_PILLARS` to three entries: `investment-management`
      (display "Odum-Managed Strategies"), `dart-trading-infrastructure`, `regulated-operating-models`. Embed an inline
      "Working with Odum" section showing the eight-stage journey.
- [ ] [AGENT] P0. Delete `content/briefings/{platform,dart-full,dart-signals-in,signals-out}.yaml`. Create unified
      `content/briefings/dart-trading-infrastructure.yaml` covering Signals-In + Full + Odum Signals as sub-sections,
      plus a Risk-and-Governance section.
- [ ] [AGENT] P0. Rename `content/briefings/regulatory.yaml` → `regulated-operating-models.yaml`; add
      Risk-and-Governance section. Update display title.
- [ ] [AGENT] P0. Update `content/briefings/investment-management.yaml` display title to "Odum-Managed Strategies"; slug
      stays `investment-management`.
- [ ] [AGENT] P0. Update `app/(public)/briefings/[slug]/page.tsx`: `risk-and-governance` and `working-with-odum` slugs
      call `notFound()` immediately. NO "Coming soon" pages, NO placeholder TLDRs.
- [ ] [AGENT] P0. Trim `app/(public)/faq/page.tsx` from 15 Q&As to 8–10. Migrate the rest to a new
      `content/briefings/faq-extended.yaml` linked from `/briefings` index (supporting briefing, NOT a pillar).
- [ ] [AGENT] P0. Add 301 redirects in `next.config.mjs`:
      `/briefings/{platform,dart,dart-full,dart-signals-in,signals-out}` → `/briefings/dart-trading-infrastructure`;
      `/briefings/regulatory` → `/briefings/regulated-operating-models`.
- [ ] [AGENT] P0. Add analytics events: `briefings_unlock_success`, `briefings_book_fit_call_click`.
- [ ] [AGENT] P0. Verify legacy briefing redirects:
      `curl -I localhost:3000/briefings/{platform,dart,dart-full,dart-signals-in,signals-out,regulatory}` → all 301 to
      canonical slugs.
- [ ] [AGENT] P0. Verify `curl -I localhost:3000/briefings/risk-and-governance` returns 404 (NOT 200 with placeholder).

---

## Phase 4.5 — Release-train QG + quickmerge (atomic 1–4)

- [ ] [AGENT] P0. Run UI Pass 1 QG: `cd unified-trading-system-ui && bash scripts/quality-gates.sh`.
- [ ] [AGENT] P0. Quickmerge:
      `bash scripts/quickmerge.sh "refactor(marketing): three-route consolidation + naming SSOT + briefings rebuild" --agent`.
- [ ] [AGENT] P0. Confirm Phase 1–4 land together in one merge — half-state forbidden per Release Rule.

---

## Phase 5 — Strategy Review (NEW gated route + magic-link)

- [ ] [AGENT] P0. Create `app/(public)/strategy-review/page.tsx` (server component, force-dynamic, accepts
      `?token=...`). Mirror server-component prefill pattern from `app/(public)/strategy-evaluation/page.tsx:33-49`.
- [ ] [AGENT] P0. Create `app/(public)/strategy-review/_client.tsx` (read-only display of proposed operating model +
      DART config + regulatory pathway + demo prep + next steps). Sectioned heavily; no hard word cap.
- [ ] [AGENT] P0. Create `app/api/strategy-review/issue-link/route.ts` (admin-only). Mint magic token via
      `randomBytes(32).toString("hex")` (mirror `app/api/strategy-evaluation/submit/route.ts:80`); ADD `expiresAt`
      (default 30 days) and `revokedAt: null`. Persist to Firestore `strategy_reviews` collection. Send email via
      existing Resend pipeline.
- [ ] [AGENT] P0. Create `app/api/strategy-review/verify/route.ts` — validates token (not expired, not revoked).
- [ ] [AGENT] P0. Create `app/(ops)/admin/strategy-reviews/page.tsx` — admin list (mirror
      `/admin/strategy-evaluations`). Buttons: issue link, copy link, revoke.
- [ ] [AGENT] P0. Implement one-token-two-doors: `/strategy-review/page.tsx` resolves a valid token → ALSO call
      `setBriefingSessionActive()` from `lib/briefings/session.ts`. Token unlocks both Strategy Review AND Briefings
      session.
- [ ] [AGENT] P0. Add analytics events: `strategy_review_link_opened`, `strategy_review_book_demo_click`.
- [ ] [AGENT] P0. NOT in this phase: catalogue subset display (deferred to Strategy Review v2).
- [ ] [AGENT] P0. Verify: admin issues token → copy link → open in incognito → renders prospect-specific page; same
      browser navigates `/briefings/dart-trading-infrastructure` → no access-code prompt; admin clicks revoke → reload
      review link → revoked-link page.
- [ ] [AGENT] P0. UI Pass 1 QG + quickmerge.

---

## Phase 6 — /contact restructure + CTA cleanup + Visual minimum pass

- [ ] [AGENT] P0. Restructure `app/(public)/contact/page.tsx`: primary CTA "Start Your Review"; four contact tracks
      (General enquiry · Existing client/counterparty · Press/partnerships · Advisor/referral); "Prefer to speak first?"
      sub-section retains the existing path-specific Calendly CTAs.
- [ ] [AGENT] P0. Update `components/shell/site-footer.tsx`: keep secondary links (Briefings hub, FAQ, Legal, Privacy,
      Terms) in the footer.
- [ ] [AGENT] P0. CTA audit: every public engagement-route page has ≤2 primary CTAs.
- [ ] [AGENT] P0. Visual minimum pass per Completion Patch §E: consistent dark institutional layout across all public
      pages; consistent hero spacing + typography + CTA placement; consistent engagement-route card heights; Briefings +
      Strategy Review feel gated/premium; no large feature grids above the fold; restrained accent colour.
- [ ] [AGENT] P0. Add analytics event: `contact_track_selected`.
- [ ] [AGENT] P0. Verify: Playwright across `/`, `/investment-management`, `/platform`, `/regulatory`, `/contact`,
      `/start-your-review`, `/briefings` — count primary CTAs (assert ≤2). Visual smoke at 1440px + 768px viewports.
- [ ] [AGENT] P0. UI Pass 1 QG + quickmerge.

---

## Phase 7 — Investor Relations presentations refactor (advisor-facing)

- [ ] [AGENT] P0. Locate IR surfaces: `/investor-relations` route (signed-in per `spaces-nav-sections.tsx` Client Access
      section); IR deck artefacts in `public/decks/` or `public/investor-relations/` if present; IR-facing email
      templates.
- [ ] [AGENT] P0. Apply canonical names ONLY: Odum-Managed Strategies / DART Trading Infrastructure / Regulated
      Operating Models. NO "Investment Management" as marketing headline; NO "Regulatory Umbrella" as public IR
      headline; NO "Odum Signals" as top-level service.
- [ ] [AGENT] P0. Three-route framing for the engagement model (not five).
- [ ] [AGENT] P0. CTA discipline: IR pages route to `/start-your-review` for new prospect-style enquiries OR to
      `/contact` (Press / partnerships / Advisor / referral track) — NEVER directly to "Book a call" as primary CTA.
- [ ] [AGENT] P0. Apply word budgets / reduction rule (Completion Patch §C): IR materials concentrated, not exhaustive.
- [ ] [AGENT] P0. Apply legal/compliance copy guardrails (Completion Patch §H): no guaranteed-coverage language.
- [ ] [AGENT] P0. Move any deeper substance reserved for the demo or actual platform services to Phase 8 (signed-in
      depth) — NOT into IR decks.
- [ ] [AGENT] P0. Verify: visit `/investor-relations` signed-in, confirm three-route framing + canonical labels + no
      banned terms. Open IR deck PDF (if hosted), confirm titles + CTAs match. Grep IR surfaces for banned marketing
      labels — must NOT appear.
- [ ] [AGENT] P0. UI Pass 1 QG + quickmerge.

---

## Phase 8 — Signed-in platform services depth content refactor

- [ ] [AGENT] P0. Strategy Catalogue (`/services/research/strategy/catalog`): card titles use marketing labels
      (Odum-Managed Strategies / DART) for legibility; service-category metadata uses legal labels via `SERVICE_LABELS`.
- [ ] [AGENT] P0. DART research/trading/execution surfaces (`/dashboard`, `/services/research/*`, `/services/trading/*`,
      `/services/execution/*`): host the depth content public pages no longer carry — full asset-class taxonomy, venue
      lists, lifecycle diagrams.
- [ ] [AGENT] P0. Funds (IM) (`/services/im/funds`): fund/SMA structure detail page-copy aligned to the new naming
      hierarchy.
- [ ] [AGENT] P0. Counterparty Dashboard (`/services/signals/dashboard`): apply naming — signals appear as "DART signals
      capability" framing, not "Odum Signals as a separate product".
- [ ] [AGENT] P0. Reporting (`/services/reports/*`): client reporting depth content reviewed for canonical labels.
- [ ] [AGENT] P0. Reuse `SERVICE_LABELS` SSOT from Phase 1 — every authenticated surface that displays a service name
      imports from it.
- [ ] [AGENT] P0. Routes are protected from rename per Completion Patch §L — `/services/*`, `/dashboard`, `/admin` keep
      their URL slugs and entitlement contracts.
- [ ] [AGENT] P0. Verify: sign in as each persona (admin / IM client / DART client / Signals counterparty); confirm
      dashboard + services content reads with the new naming hierarchy. Strategy Catalogue page renders correctly
      post-bespoke-tailoring (existing entitlement gate unchanged). No regression on authenticated route contracts.
- [ ] [AGENT] P0. UI Pass 1 QG + quickmerge.

---

## Phase 9 — Final verification

- [ ] [AGENT] P0. **Regression suite (must pass).** Questionnaire submission end-to-end (Firestore write + Resend
      email + auto-unlock + redirect). Strategy Evaluation submit + magic-link refile. Signup wizard for
      `?service=investment` (renders "Investment Management" legal label), `?service=platform` (renders "DART"),
      `?service=regulatory` (renders an approved legal/service label — Regulatory Umbrella for backwards-compat,
      Regulatory / Structuring Review, or Regulated Operating Models if compliance-approved; do NOT hard-require any
      single phrase, but do NOT introduce new public-facing "Regulatory Umbrella" copy). Admin tooling on
      `/admin/questionnaires`, `/admin/strategy-evaluations`, `/admin/strategy-reviews`.
- [ ] [AGENT] P0. **Cold-prospect Playwright flow.** Navigate `/` → confirm three engagement-route cards + Start Your
      Review/Contact Odum CTAs. Click Start Your Review → context page → Begin Questionnaire → fill 6 axes → submit →
      redirect to `/briefings` (three pillars).
- [ ] [AGENT] P0. **Strategy Review Playwright flow.** Submit `/strategy-evaluation` → admin issues review link → open
      in incognito → prospect-specific render. Same browser navigate `/briefings/dart-trading-infrastructure` → no
      access-code prompt. Admin revokes → reload → revoked-link page.
- [ ] [AGENT] P0. **All redirects.** Routes: `/platform/signals-in`, `/platform/full`, `/signals` → `/platform#…`.
      Briefings: `/briefings/{platform,dart,dart-full,dart-signals-in,signals-out}` →
      `/briefings/dart-trading-infrastructure`; `/briefings/regulatory` → `/briefings/regulated-operating-models`.
- [ ] [AGENT] P0. **No "Coming soon" leakage.** `curl -I /briefings/risk-and-governance` → 404. Same for
      `/briefings/working-with-odum`. These slugs MUST NOT appear in any link on the `/briefings` index.
- [ ] [AGENT] P0. **Orphan-audit.** Per memory `project_dart_ui_session_state_2026_04_24.md`, port the orphan-audit
      scanner from deployment-ui to unified-trading-system-ui if not already present. Whitelist
      `/briefings/risk-and-governance` and `/briefings/working-with-odum` as intentionally-hidden.
- [ ] [AGENT] P0. **Email pipeline E2E.** Trigger questionnaire + strategy-eval + admin-issued review link in
      odum-staging. Verify all three Resend emails arrive at a real inbox.
- [ ] [AGENT] P0. **Authenticated-surface regression.** `/services/signals/dashboard`, `/services/im/funds`,
      `/dashboard`, `/admin/*` all still render for authenticated users post-refactor.
- [ ] [AGENT] P0. **Three-persona human review** (Completion Patch §M). Allocator finds Odum-Managed Strategies +
      SMA/fund-route + Start Your Review. Trading team finds DART + signals capability + research-to-execution.
      Regulated-structure prospect finds Regulated Operating Models + case-by-case review.
- [ ] [HUMAN] P0. **Final approval to deploy** UAT → prod across the live-defi-rollout release.

---

## Out of scope (deferred, NOT shipping with this refactor)

- Strategy Review v2: curated-catalogue subset display (depends on DART entitlement-overlay decisions).
- DART internal entitlement structure changes — `/services/*` route entitlements unchanged.
- Full design-system rebuild — minimum visual pass per Phase 6 is in scope; typography overhaul and palette redesign are
  separate workstreams.
- Permanent "Regulatory Umbrella" → "Regulated Operating Models" rename on legal/admin/contract surfaces — gated on
  compliance review (TODO tracked in this plan's Decisions table).

## Final consistency patch (binding — overrides any conflicting wording above)

1. **Regulatory signup verification must accept the currently approved legal/service label.** Do NOT hard-require
   "Regulatory Umbrella" if the implementation has moved to "Regulatory / Structuring Review" or another
   compliance-approved label. Public marketing surfaces must still use "Regulated Operating Models".

2. **Risk-and-Governance and Working-with-Odum dedicated pages are not required for this release.** Do NOT create
   visible pages. If route scaffolds are created for tooling reasons, they must immediately call `notFound()` and must
   be excluded from nav/cards/links.

3. **Release sequencing recap:**
   - Phases 1–4 must ship together or behind one feature branch.
   - Phase 5 Strategy Review can ship in the same train or as a feature-gated follow-up.
   - Phase 6 visual / contact pass should ship with the public release.
   - Phases 7–8 are alignment passes for IR and signed-in depth. Same naming rules; should not block the core public
     refactor unless those surfaces are currently visible to prospects/advisors.

4. **Final framing instruction to the implementing agent:** Do not treat this as a rebrand. Treat it as **reducing
   noise, controlling depth, and making the buyer journey feel institutional**.

---

## Already correct — explicitly do not touch

- `/who-we-are` + `/story` + `/our-story` — already a working progressive-disclosure trio.
- `/strategy-evaluation` 8-step wizard + magic-link refile + DB draft save — already shipped 2026-04-25.
- `BriefingAccessGate` light-auth pattern — already correct. Strategy Review adds a new per-prospect magic-link gate
  alongside it; the briefings shared-code gate stays.
- `dev-tiers.sh` Firebase Emulator default + odum-staging Firebase isolation — already correct, do not regress.
