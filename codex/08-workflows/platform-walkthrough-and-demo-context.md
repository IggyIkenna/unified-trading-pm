---
doc_type: codex-ssot
title: Platform Walkthrough & Controlled Demo / UAT Context
summary: >-
  Target-state playbook for the controlled demo/UAT access context: the accessContext enum, demo-session magic-link
  entitlement issuance, persona-scoped `/services/*` surfaces, and the demo→production shared-component-stack continuity
  rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [admin, sales, engineer]
tags: [ui, onboarding, mvp, questionnaire, validation]
related: [./signup-signin-workflow.md, ./prospect-questionnaire-flow.md]
created: 2026-04-26
authoritative_for:
  [
    controlled demo/UAT access context (accessContext enum + demo-session entitlement issuance + persona-scoped
    surfaces),
  ]
referenced_by: [/codex/08-workflows/signup-signin-workflow.md]
owner:
last_reviewed:
code_refs:
---

# Platform Walkthrough & Controlled Demo / UAT Context

**Status:** target-state playbook · 2026-04-26 (introduced as part of the Funnel Coherence + Signed-In Services +
Tailored Catalogue plan, Workstream H)

This doc formalises how the Platform walkthrough stage (`signup-signin-workflow.md` §2.5) actually works — specifically,
the **controlled demo / UAT access context** that lets prospects experience the real DART / Reports / Strategy Catalogue
stack against mock data before they sign up.

**Companion docs:**

- [`signup-signin-workflow.md`](./signup-signin-workflow.md) — the canonical funnel; this doc expands §2.5 Platform
  walkthrough.
- [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md) — the questionnaire that seeds the prospect's
  preferences.
- Plan: `~/.claude/plans/below-is-the-full-radiant-lighthouse.md` Workstream H.

---

## §1 — Three-context access model

The same DART / Reports / Strategy Catalogue component stack renders in three distinct contexts depending on where the
prospect/client sits in the funnel. The components are reused across contexts; what changes is the data source,
entitlements, available actions, and labelling.

| Context                         | Where it sits in funnel                    | Data source                                  | Entitlements                                                                                     | Actions                                                                                           | Labelling                                                                |
| ------------------------------- | ------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Public / gated education**    | §2.1 Questionnaire → §2.4b Strategy Review | None — public pages don't open `/services/*` | None                                                                                             | Read-only marketing + briefing surfaces                                                           | Standard public-site treatment                                           |
| **Controlled demo / UAT**       | §2.5 Platform walkthrough                  | Mock / illustrative only                     | Admin-issued demo-session entitlement                                                            | Read-only platform exploration; NO production credentials, NO destructive actions, NO withdrawals | Persistent "Demo / UAT — illustrative data only" banner on every surface |
| **Production signed-in client** | §2.7 Signup → §2.8 Signin onward           | Real production data                         | Tier-based production entitlements (per `personaDashboardShape()` + `lib/auth/tier-override.ts`) | Full operational actions per persona's tier                                                       | Standard signed-in chrome                                                |

The `accessContext` enum (`public` / `briefing` / `strategy_review` / `demo_uat` / `production`) is set on the request
and propagated through layout / page components. Components branch their data source, available actions, and labels off
it.

---

## §2 — Demo-session entitlement issuance

After the prospect's Strategy Review (§2.4b) lands, admin reviews the prep pack + walkthrough agenda and decides whether
to schedule the live walkthrough. When yes:

1. **Admin opens `/admin/demo-sessions`** (mirrors `/admin/strategy-reviews` shape).
2. Selects the prospect record + scopes the demo: which persona profile to render (allocator / DART Signals-In / DART
   Full / Odum Signals counterparty / LP), which surfaces are in scope, expiry window (default 30 days, like Strategy
   Review).
3. **POST** `/api/demo-session/issue-link` issues a demo-session magic token. The token is written to Firestore
   `demo_sessions/{sessionId}` with `prospect_email`, `persona_profile`, `surfaces_in_scope`, `expiresAt`, `revokedAt`,
   `magicToken`, `issuedBy`, `createdAt`.
4. Resend email goes out to the prospect with the demo-session magic link. Subject: "Your Odum Platform walkthrough is
   ready."
5. Prospect clicks the link → server resolves token via `/api/demo-session/verify` → if valid, sets a session cookie /
   token claim with `accessContext: "demo_uat"` + the scoped entitlements + persona profile.

Demo-session tokens are revocable from the same admin tooling (`/api/demo-session/revoke`). Expiry is enforced
server-side on every request.

**One-token-two-doors continuity** (mirrors Strategy Review): a valid demo-session token also unlocks the briefings
session (`setBriefingSessionActive()`) so the prospect can revisit briefings during their demo window without
re-entering an access code.

---

## §3 — Surfaces opened in demo/UAT (per persona)

The persona profile chosen at issuance time determines which `/services/*` tiles the demo session sees. Personas mirror
the production-side persona model defined in `signup-signin-workflow.md` and the Funnel Coherence plan Decision 4
(strict persona-tile separation):

| Persona                       | Demo tiles visible                                                                                                             | Mock data sources                                                                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **IM allocator**              | Reports tile only (Strategy Catalogue + Own-account reports). NO DART, NO Odum Signals, NO Investor Relations.                 | Catalogue: mock strategy universe with maturity tags + illustrative perf series. Own-account reports: empty/illustrative state. |
| **DART Signals-In**           | DART tile (Signals-In subset — execution / post-trade / observe / reporting; NO research / promote / backtest) + Reports tile. | Mock signal stream + matched fills + reconciliation; mock catalogue scoped to subscribed instances.                             |
| **DART Full**                 | DART tile (full surface — research / promote / backtest / paper / live + everything Signals-In has) + Reports tile.            | Same as Signals-In plus mock backtest results + paper P&L + promotion-ladder examples.                                          |
| **Odum Signals counterparty** | Odum Signals tile (`/services/signals/dashboard` counterparty surface) + Reports tile. NO DART.                                | Mock outbound signal stream + delivery health + ack/no-ack telemetry.                                                           |
| **Investor (LP)**             | Investor Relations + Reports tiles. NO DART, NO Odum Signals.                                                                  | Mock fund-level returns, regulatory filings, board materials.                                                                   |
| **Admin**                     | All tiles.                                                                                                                     | Internal-only context, distinct from prospect demo sessions.                                                                    |

The strict separation means a DART prospect's demo session does NOT show them the Odum Signals tile, even though both
are valid Odum offerings — the demo focuses on the prospect's own engagement route to avoid noise.

---

## §4 — Strategy Catalogue in demo/UAT

The Strategy Catalogue (`/services/reports/strategy-catalogue`, post-Workstream-D2 route move) renders in demo/UAT mode
against mock data:

- **Reality view** hydrates the prospect's `catalogue_seed` (computed from their questionnaire + Strategy Evaluation per
  Workstream E5). Shows strategies that match their preferences (asset_groups, instrument_types, market_neutral,
  risk_profile, leverage_preference).
- **Explore view** shows broader available scope — strategies/configurations outside the current seed or entitlement,
  framed as "available under broader scope." This is the surface previously called the "FOMO view"; product copy should
  call it Explore. The internal component name `FomoTearsheetCard.tsx` may stay.
- **Pretty-printing** — archetype IDs render in human form ("Cross-Sectional Momentum" not `cross_sectional_momentum`)
  via `lib/strategy-display.ts` (Workstream E3).
- **Curated examples preview from Strategy Review** — the prospect's Strategy Review §2.4b surface previews 2–3 specific
  strategies that they'll see in the demo Reality view; the demo opens those + the broader Explore view.

**Demo data carries no production performance:** illustrative perf series only; nothing live; clearly flagged in the
`<DemoBanner>` chrome.

---

## §5 — Demo-to-production continuity

The same component stack renders in both demo/UAT and production. Branching happens at three layers:

1. **Data source.** Components read their data via hooks that check `accessContext`:
   - `demo_uat` → returns mock fixtures (per persona profile).
   - `production` → returns real data via the live API.
2. **Entitlements.** `useEntitlements()` returns the demo-session's scoped entitlements in `demo_uat`, the user's
   production entitlements in `production`.
3. **Actions.** Mutating actions (place order, withdraw, upload credentials, modify mandate) are disabled in `demo_uat`
   — every action is gated by an `isProductionContext()` check and renders a tooltip in demo mode: "Disabled in demo.
   Available after sign-up."

**Anti-pattern (do NOT do):** forking the UI into separate demo-only pages. Demo and production share the route. The
only acceptable carve-out is a small set of demo-only banners / tooltips / CTA changes layered through context-aware
components.

---

## §6 — Walkthrough flow (operator + self-serve halves)

A typical Platform walkthrough session, per the user-facing description in `signup-signin-workflow.md` §2.5:

1. **Operator-led half (~30–45 min, video call).** Odum operator opens the demo session in their own browser,
   screenshares, walks the prospect through the surfaces flagged in their Strategy Review demo agenda. Mock data +
   persona-scoped tiles + the `<DemoBanner>` chrome are visible throughout.
2. **Hand-over.** At the end of the operator half, the prospect receives the same demo-session link. Their token has the
   same scope, but now they're driving.
3. **Self-serve half (timeboxed by token expiry, default 30 days).** Prospect explores the demo themselves. They can
   revisit briefings (one-token-two-doors), open the catalogue Reality + Explore views, navigate the relevant DART or
   Reports surfaces, leave notes via a feedback form on the demo banner ("What worked, what didn't, what's missing").
4. **Feedback flows back to admin.** The notes feed into the next stage: Commercial Tailoring (§2.6).

---

## §7 — What the demo MUST NOT do

- **No production credentials accepted.** Even if the prospect is already a client of another Odum service, the demo
  session uses the demo persona profile, not their real entitlements.
- **No destructive actions.** No withdraw, no order placement that hits a real venue, no real fund subscription. Every
  mutation is a no-op in `demo_uat`.
- **No real client data leakage.** Demo fixtures must not contain any production client's strategy results, mandate
  terms, or P&L. Fixtures are synthetic and clearly labelled.
- **No silent transitions to production.** A prospect cannot accidentally graduate to a production session — they must
  complete §2.6 Commercial Tailoring + §2.7 Signup explicitly.

---

## §8 — Implementation file map (Workstream H)

| File                                                          | Purpose                                                                                                  |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `lib/auth/access-context.ts`                                  | NEW — defines `accessContext` enum + helpers to resolve the active context from token / session / claims |
| `lib/auth/demo-session.ts`                                    | NEW — demo-session token / entitlement helpers                                                           |
| `app/api/demo-session/issue-link/route.ts`                    | NEW — admin-only issue-link route                                                                        |
| `app/api/demo-session/verify/route.ts`                        | NEW — token verification route                                                                           |
| `app/api/demo-session/revoke/route.ts`                        | NEW — admin revoke route                                                                                 |
| `app/(ops)/admin/demo-sessions/page.tsx`                      | NEW — admin tooling, mirrors `/admin/strategy-reviews`                                                   |
| `components/platform/DemoBanner.tsx`                          | NEW — persistent "Demo / UAT — illustrative data only" banner                                            |
| `app/(platform)/services/reports/strategy-catalogue/page.tsx` | UPDATE — supports demo/UAT context + seed hydration                                                      |
| `app/(platform)/services/reports/own-account/page.tsx`        | UPDATE — demo empty/illustrative state                                                                   |
| `app/(platform)/dashboard/page.tsx`                           | UPDATE — supports demo tile set per persona profile                                                      |

---

## §9 — Change log

| Date       | Change                                                                                                                                                | Commit          |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 2026-04-26 | Doc created. Three-context access model formalised. Demo-session issuance + persona-scoped surfaces + demo-to-production continuity rules documented. | _(this commit)_ |
