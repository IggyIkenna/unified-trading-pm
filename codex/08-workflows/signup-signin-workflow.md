---
doc_type: codex-ssot
title: Signup / Signin workflow — prospect → client
summary: >-
  Target-state prospect→client funnel: the 9 ordered stages (questionnaire → deep-dives → call → strategy-eval → review
  → walkthrough → commercial-tailoring → signup → signin), the per-service-path signup fields, and current-vs-target
  state.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [admin, sales]
tags: [onboarding, questionnaire, ui, mvp, validation]
related: [./prospect-questionnaire-flow.md, ./platform-walkthrough-and-demo-context.md, ./client-onboarding.md]
created: 2026-04-22
authoritative_for: [prospect→client signup/signin funnel (9-stage journey + per-service-path signup fields)]
referenced_by:
  [
    /codex/08-workflows/client-onboarding.md,
    /codex/08-workflows/environment-mode-philosophy.md,
    /codex/08-workflows/platform-walkthrough-and-demo-context.md,
    /codex/08-workflows/prospect-questionnaire-flow.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Signup / Signin workflow — prospect → client

**Status:** target-state playbook · 2026-04-25 (revised funnel)

Defines the canonical prospect-to-client journey, how the self-serve signup flow is shaped per commercial path, and the
current vs target state of what the UI actually implements.

**Companion docs:**

- [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md) — the questionnaire form itself (axes,
  submission, envelope).
- [`/codex/14-customer-journeys/authentication/firebase-staging.md`](/codex/14-customer-journeys/authentication/firebase-staging.md)
  / [`firebase-production.md`](/codex/14-customer-journeys/authentication/firebase-production.md) — Firebase project
  setup, roles, and Firestore rules.
- [`/codex/14-customer-journeys/authentication/light-auth-briefings.md`](/codex/14-customer-journeys/authentication/light-auth-briefings.md)
  — the briefings access-code gate (separate from the main client sign-in).

---

## 1. The full prospect journey

The target funnel has **nine ordered stages**. Each stage writes a durable artefact (or context) the next stage
consumes; a prospect can pause and resume at any point via their email address. The sequencing is deliberate — each step
tailors the next one so neither side re-treads ground on later calls.

```
Public marketing pages (browse, decide whether to go deeper)
       │
       ▼
Questionnaire (~2 min, 6 base + 7 Reg-Umbrella axes)
       │    → Firestore /questionnaires/{id}  (staging/prod)
       │    → localStorage                    (dev / mock)
       │    → sends envelope {email, firm, fingerprint}
       │    → submit auto-issues briefings access code
       ▼
Deep dives (briefings access code)
       │    (long-form per-path briefings; reader decides if they want a
       │     call. Ops may also reach out around this point to suggest one.)
       ▼
Initial call (~30 min) — fit discussion
       │    (targeted now that the prospect has read the deep dives;
       │     focused on which products actually fit, not what Odum does)
       ▼
Strategy Evaluation (specifics on the record)
       │    → Firestore /strategy-evaluations/{id}
       │    (assets, venues, risk, structure preferences, capital — what we
       │     tailor against from this point)
       ▼
Strategy Review (pre-demo prep pack — per-prospect)
       │    → Firestore /strategy-reviews/{id}
       │    → admin issues per-prospect magic link with expiry + revoke
       │    (proposed route hypothesis, briefing excerpts, demo agenda,
       │     workflows likely to be shown, curated examples, missing-info
       │     checklist, route-specific risks. NOT a final proposal — a
       │     tailored prep pack that sets up the platform walkthrough.)
       ▼
Platform walkthrough (guided → self-serve)
       │    (operator walkthrough against the prospect's strategy-evaluation
       │     shape and the curated agenda from Strategy Review; then prospect
       │     drives it themselves and forms a value judgement on fit. Was
       │     'Tailored demo'; renamed 2026-04-26.)
       ▼
Commercial Tailoring (operator-led; was 'Bespoke tailoring')
       │    (catalogue opens here: ~2,500 combinations. Customise strategies,
       │     infrastructure, regulatory posture from it. Pricing, mandate
       │     shape, onboarding workplan, and contract scope are locked off
       │     in preparation for signup. No dedicated public UI — operator-
       │     led via shared documents + calls until signup.)
       ▼
Signup + go live (self-serve form → user-management-api)
       │    → Firebase Auth user (disabled, pending_approval)
       │    → Firestore /users/{uid} profile
       │    → attaches questionnaire_response_id from envelope.email
       │    (ambition: live within a month of go-ahead, leveraging the
       │     affiliate network — custodian, fund administrator, AIFM where
       │     applicable — and the repeatable provisioning modules)
       ▼
Signin → dashboard (post-approval, access-token granted)
```

Key properties:

- **The questionnaire's email is the primary cross-link.** The signup flow looks up the prior questionnaire response by
  that email and attaches it to the user record — so client-facing staff opening the admin view see the full journey in
  one place.
- **Questionnaire submission is the briefings access gate.** Submitting issues a code automatically; ops only issue
  codes manually as a fallback for prospects who reach out via /contact or on a call.
- **Strategy Evaluation is on-the-record specifics.** It runs _after_ the initial call so the conversation focuses on
  which products fit; the DDQ then captures concrete assets / venues / risk / structure / capital that we tailor
  against.
- **Signup sits near the end of the funnel, not the start.** Short-circuiting to signup before the platform walkthrough
  and Commercial Tailoring would mean provisioning blind; the sequencing above exists so we don't.
- **The ~2,500-combination catalogue opens at the Commercial Tailoring stage**, not earlier. It's not coy — it's how
  trust is built, and it protects clients who have already locked off their piece. Strategy Review surfaces only curated
  examples (a small handful), never the full catalogue.
- **Three-context access model.** The same DART / Reports / Strategy Catalogue component stack renders in three distinct
  contexts depending on where the prospect/client is in the funnel:
  1. **Public / gated education** (§2.1–§2.4b): public pages + briefings + Strategy Evaluation + Strategy Review. NO
     `/services/*` redirects from public submissions.
  2. **Controlled demo / UAT** (§2.5 Platform walkthrough): admin-issued demo-session entitlements unlock selected
     `/services/*` surfaces in mock-data mode, with clear demo labelling, no production credentials, no destructive
     actions, no withdrawal capability.
  3. **Production signed-in client** (§2.7 Signup → §2.8 Signin): real entitlements, real data, own-account reporting,
     approved account permissions.

  The same components are reused across demo and production wherever possible. Access context controls data source,
  entitlements, labels, and available actions.

---

## 2. Stage-by-stage contract

### 2.1 Questionnaire stage

- **Required inputs:** base 6 axes (categories, instrument types, venue scope, strategy styles, service family, fund
  structure). Reg-Umbrella axes 7-13 are conditional on `service_family = "RegUmbrella"`.
- **Envelope fields (optional):** email, firm_name. Envelope is stored alongside the response and is the handle used at
  signup time to find the response.
- **Sink:** Firestore `/questionnaires/{auto-id}` in staging/prod; `localStorage[questionnaire-response-v1]` +
  `[questionnaire-envelope-v1]` in dev / mock.
- **Access-code issuance:** Submitting the questionnaire auto-issues the briefings access code (light-auth, shared key)
  — the questionnaire is the primary path through the briefings gate. /contact and call-issued codes remain as fallbacks
  for prospects who skip the form.
- **SSOT:** [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md).

### 2.2 Deep dives stage

- **Not a UI write** beyond the access-code consumption.
- Long-form per-path briefings under `/briefings/*`, gated behind the access code from §2.1. Reader chooses whichever
  path matches them.
- **Optional ops nudge:** ops may reach out around this point (post-questionnaire / mid-deep-dive) to ask whether the
  prospect wants to book a call. Whether to reach out is a CRM judgement, not a UI write.
- **SSOT for the access-code gate:**
  [`/codex/14-customer-journeys/authentication/light-auth-briefings.md`](/codex/14-customer-journeys/authentication/light-auth-briefings.md).

### 2.3 Initial call stage (~30 min)

- **Not a UI write.** Booked via Calendly, operator-led.
- Purpose: fit confirmation. By this stage the prospect has read the deep dives, so the call focuses on which products
  actually fit (rather than rehearsing what Odum does). Operator confirms whether to move to Strategy Evaluation.
- Operator notes go into internal CRM; no public-facing artefact beyond the calendar event.

### 2.4 Strategy Evaluation stage

- **UI surface:** `/strategy-evaluation` 8-step wizard (server-component prefill at `page.tsx` → client wizard in
  `_client.tsx`; magic-link confirm + DB draft save + 500MB upload cap; per-field upload errors). The Funnel Coherence
  plan (Workstream A) adds a pre-step gate that branches into Path A (allocator, ~4 steps) vs Path B (builder, existing
  8 steps) based on `engagement_intent`.
- **Sink:** Firestore `/strategy-evaluations/{id}`. Draft key is SHA-256(email).
- Purpose: capture the prospect's specifics on the record — for builders: assets, venues, risk, structure preferences,
  capital, fundraising posture, fee preferences; for allocators: profile, appetite, venue restrictions, leverage caps,
  performance criteria, capital scaling, SMA fees, structure interest. This is the artefact we tailor the Strategy
  Review and the demo against.
- **No catalogue access yet.** The catalogue still opens only at Commercial Tailoring (§2.6). Catalogue seed preferences
  are computed from the evaluation payload and stored on the doc as `catalogue_seed`, but never opened to the prospect
  at this stage.

### 2.4b Strategy Review stage (pre-demo prep pack)

- **UI surface:** `/strategy-review?token=<magicToken>` — server-component, force-dynamic, prospect-specific render.
  Read-only display, sectioned per the Funnel Coherence plan Workstream C2:
  1. Proposed route hypothesis
  2. Relevant briefing excerpts
  3. Demo agenda
  4. Workflows / modules likely to be shown
  5. Curated examples (a small handful — NOT the full catalogue)
  6. Missing-information checklist
  7. Route-specific risks and constraints
- **Sink:** Firestore `/strategy-reviews/{id}` with `magicToken`, `expiresAt` (default 30 days), `revokedAt`.
- **Gating:** per-prospect magic link, NOT a shared access code. Token additionally unlocks the briefings session
  (one-token-two-doors via `lib/briefings/session.ts`) so prospects don't have to re-enter codes during their review
  window.
- **Issuance:** admin-only, via `/admin/strategy-reviews` after the Strategy Evaluation submission has been reviewed.
  Endpoint `POST /api/strategy-review/issue-link`. Email sent via existing Resend pipeline.
- **Verification:** `GET /api/strategy-review/verify?token=...` checks not-expired AND not-revoked.
- **Scope (binding):** Strategy Review is a **pre-demo tailored review and walkthrough preparation pack** — NOT the
  final commercial proposal. Subtitle in the UI: "Your tailored pre-demo review." It MUST NOT show: full strategy
  catalogue, final pricing, final contract structure, full signed-in platform, all bespoke combinations. Those open in
  Commercial Tailoring (§2.6, post-walkthrough, operator-led).
- **Naming history:** introduced 2026-04-26 as a per-prospect surface between Strategy Evaluation and the demo. Briefly
  swapped with the demo later that same day (Strategy Review moved AFTER walkthrough), then reverted to its original
  pre-demo position with a reframed scope (pre-demo prep pack, not post-demo synthesis). The two reorder entries in §4
  record the journey honestly.

### 2.5 Platform walkthrough stage (controlled demo / UAT context)

- **Demo / UAT access context** — admin issues a demo-session entitlement (mirrors `/admin/strategy-reviews` shape; new
  `/admin/demo-sessions` tooling). The token unlocks selected `/services/*` surfaces in **demo/UAT mode**, NOT
  production: mock or illustrative data, no production credentials, no destructive actions, no withdrawal capability.
  Every demo surface carries a persistent "Demo / UAT — illustrative data only" banner.
- Two halves: (1) guided walkthrough where an Odum operator drives the UI against the prospect's Strategy-Evaluation
  shape and the curated agenda from Strategy Review, (2) self-serve exploration where the prospect runs the platform
  themselves (in demo/UAT mode) and forms a value judgement on fit vs reality.
- **Surfaces opened in demo/UAT** (per persona):
  - DART persona: relevant research / execution / observe / reporting modules depending on demo entitlement (Signals-In
    subset or Full).
  - IM allocator: Reports tile + Strategy Catalogue Reality + Explore views.
  - Odum Signals counterparty: counterparty surface (mock signal stream + delivery health).
  - Investor (LP): Investor Relations + Reports tiles (already-client personas may skip the demo entirely).
- **Strategy Catalogue in demo/UAT:** hydrates `catalogue_seed` from the questionnaire / Strategy Evaluation into the
  Reality view; the Explore view shows broader available scope using mock data, framed as "available under broader
  scope" not "FOMO" (`FomoTearsheetCard.tsx` is an internal component name; product copy says Explore).
- **Demo-to-production continuity (binding):** demo and production share the same component stack. The `accessContext`
  (`public` / `briefing` / `strategy_review` / `demo_uat` / `production`) controls data source, entitlements, labels,
  and available actions. Do NOT fork the UI into separate demo-only pages unless unavoidable.
- **The catalogue does not open in production form at the walkthrough.** Pricing, contracts, and bespoke options open at
  Commercial Tailoring (§2.6) only if the fit is confirmed through the walkthrough.
- **Naming history:** previously called "Tailored demo"; renamed 2026-04-26 to "Platform walkthrough" to make the
  controlled-demo / UAT framing explicit.

### 2.6 Commercial Tailoring stage (was 'Bespoke tailoring' until 2026-04-26)

- **Not a UI write.** Operator-led — usually one or two targeted calls, sometimes a shared document trail. No dedicated
  public route.
- **The ~2,500-combination catalogue opens here.** Strategies, infrastructure, regulatory posture are customised from
  it; pricing, mandate shape, onboarding workplan, and contract scope that will drive signup are locked off during this
  stage.
- Output: a concrete contract shape the prospect can sign off on; ready to move to signup.
- **Naming history:** renamed from "Bespoke tailoring" to "Commercial Tailoring" on 2026-04-26 to disambiguate from
  custom-strategy commissioning (which is a separate concept). Mechanics unchanged.

### 2.7 Signup stage

#### 2.7.1 Gate: questionnaire-completed check

- `/signup` reads `localStorage[questionnaire-response-v1]` on mount.
- **If present:** show a one-line acknowledgement banner ("Questionnaire on file for `<email>` — we'll attach your
  answers to this signup") and render the service-specific form.
- **If absent:** show a gate card with two CTAs:
  1. "Take the questionnaire →" (primary) — deep-links to `/questionnaire?service=<mapped>` where mapped = IM / DART /
     RegUmbrella depending on the signup `?service=` param.
  2. "I've already filled it in, continue" (secondary, for cross-device cases) — proceeds directly to the form; we rely
     on email cross-reference at submit time.

#### 2.7.2 Service-specific signup fields

Signup UI is shaped by the `?service=` query param. Four service paths; fields are minimal per path because we already
have the prospect's answers from the questionnaire and the Strategy Evaluation.

**Naming convention (added 2026-04-26 with the three-route marketing refactor):** the **Service path** column below is
the legal / contract / signup label that surfaces inside the wizard, admin tooling, and email templates — these stay
unchanged. The **Marketing label** column is the public-facing display label used on homepage cards, engagement-route
pages, and briefings; on public surfaces, the four signup-side paths collapse into three marketing routes (Odum Signals
folds under DART Trading Infrastructure as a capability, not a separate top-level product). URL slugs (`?service=`) are
unchanged across both layers.

| Service path (legal label)                        | Marketing label                                  | Fields                                                                                                                                                             | Rationale                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Investment Management** (`?service=investment`) | Odum-Managed Strategies                          | Full name · Email · Entity name · Entity registered address · Contact channel (phone / Telegram handle / WhatsApp — pick one) · Password (choose)                  | We generate the investment management agreement and custody letters from these fields. No PEP / KYC docs uploaded at this stage — that moves to the admin-side onboarding queue post-approval.                                                                                                                                                                           |
| **DART** (`?service=platform`)                    | DART Trading Infrastructure                      | Full name · Email · Password (choose)                                                                                                                              | Platform access is provisioned post-demo. Questionnaire + Strategy Evaluation answers already contain the service family, asset-class scope, and strategy profile — no further signup fields needed.                                                                                                                                                                     |
| **Odum Signals** (`?service=signals`)             | DART Trading Infrastructure (signals capability) | Full name · Email · Password (choose)                                                                                                                              | Same rationale as DART. Signal-counterparty agreement is drafted from the questionnaire + Strategy Evaluation + demo call, not the signup form. Public marketing folds Signals under DART; signup keeps Odum Signals as a distinct service path so contract generation and admin tooling remain unambiguous.                                                             |
| **Regulatory Umbrella** (`?service=regulatory`)   | Regulated Operating Models                       | Full name · Email · Entity name · Entity registered address · Contact channel (phone / Telegram / WhatsApp) · Engagement type (AR vs Advisory) · Password (choose) | Contract generation needs entity details; regulatory activities profile comes from the questionnaire. KYC-level docs move to the admin-side queue. The "Regulatory Umbrella" legal label may persist on existing contracts; new legal drafting prefers the specific structure name (Advisory / AR-style / SMA / affiliate fund) — TODO: post-refactor compliance review. |

**Principle:** no document uploads at the public-facing signup stage. The form generates contracts from entity fields;
document exchange (signed agreements, proof of address, etc.) happens on the admin side via Firebase Storage signed URLs
after approval.

#### 2.7.3 Password rules

- Minimum 12 characters, at least one uppercase + lowercase + digit.
- Password is set at signup (not assigned by ops).
- Firebase Auth user is created in `disabled=true` state; ops flips `disabled=false` after KYC/AML checks pass.

#### 2.7.4 Questionnaire attachment

The signup API (POST `/api/v1/signup`) attaches the prospect's prior questionnaire response to the new user profile via
two paths, in priority order:

1. **Direct id (preferred).** The browser persists the response id on the questionnaire envelope (Firestore doc id in
   staging/prod, `q-local-<ts>` in dev/mock — see [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md)).
   The signup wizard reads `submissionId` off `localStorage[questionnaire-envelope-v1]` and forwards it as
   `questionnaire_response_id` on the request body. Backend writes it to the user profile verbatim.
2. **Email lookup (fallback).** If the request body omits `questionnaire_response_id` (cross-device case, envelope
   evicted, etc.), the backend looks up the most recent `/questionnaires/{id}` where
   `submitted_by.email == signup.email` and adopts that id.

If both paths fail the user profile is created with `questionnaire_response_id = null` and ops is notified to link
manually on review.

The signup response body returns the resolved id (or `null`) plus an `email_verification_pending` flag so admin tooling
can show the pending-verify state alongside the application.

#### 2.7.5 Go-live timing and affiliate network

The end-to-end ambition is **live within a month of the prospect giving the go-ahead at the bespoke-tailoring stage**.
Hitting that depends on the affiliate network and repeatable provisioning modules:

- **Custodian** for crypto / on-chain assets (Copper or equivalent regulated custodian per asset class).
- **Fund administrator** + **AIFM partner** when the engagement involves a pooled fund vehicle (NAV, subscriptions /
  redemptions, fund accounting, EU-AIFM cover where applicable).
- **Repeatable provisioning modules** for venue API-key issuance, scoped Secret Manager keys, contract templates, and
  reporting-stack onboarding.

Same-week go-live remains realistic for narrower DART / Signals engagements where there's no fund-structure work.

### 2.8 Signin stage

- Standard Firebase Auth email + password.
- `disabled=true` accounts see a "pending approval" landing page (`/pending`) with status info and a support contact
  link.
- Approved accounts land on `/dashboard` with role-scoped nav.

---

## 3. Current state vs target (as of 2026-04-25)

What's already wired:

- [x] Questionnaire form + Firestore submission ([`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md)).
- [x] `/signup` page structure (generic + onboarding-wizard branches).
- [x] Firebase Auth user creation at step 1 of onboarding wizard (IM + Regulatory).
- [x] `/pending` page for disabled accounts awaiting approval.
- [x] Deep-dive (briefings) light-auth gate via `lib/briefings/access-code.ts`.
- [x] Questionnaire-completed gate on `/signup` (2026-04-22).
- [x] Service-list refresh on signup to match the four-path nav (2026-04-22).
- [x] Signup wizard step 3 is no-upload for both IM and Regulatory; KYC / AML / PEP documents move to the admin
      signed-URL drop-box post-approval (2026-04-22). The step-4 review surfaces the deferral inline so prospects know
      what to expect.
- [x] Contact-channel picker (phone / Telegram / WhatsApp) on wizard step 1, with `contact_channel` + `contact_value` on
      the signup payload (2026-04-22).
- [x] `SignupPayload.questionnaire_response_id` is forwarded by the wizard from
      `localStorage[questionnaire-envelope-v1].submissionId` (Firestore submit now persists the id back onto the
      envelope so cross-page reads are typed). Mock backend implements both the direct-id and email-lookup attachment
      paths described in §2.7.4 (2026-04-22).
- [x] DART + Odum Signals path on `GenericSignup` shows a "post-demo provisioning" callout so prospects know account
      keys are issued after the demo, not at form submit (2026-04-22).
- [x] `SignupPayload.send_email_verification` opts the new account into Firebase admin-SDK email verification at signup
      time. Mock backend records `email_verification_pending: true` on the user profile so admin tooling can surface it
      (2026-04-22).
- [x] Strategy Evaluation DDQ shipped at `/strategy-evaluation` with magic-link confirm + DB draft save + 500MB upload
      cap (2026-04-25).
- [x] Briefings access-code gate accepts an inline questionnaire on the lock screen so submission auto-unlocks
      `/briefings/*`, `/docs`, `/our-story`, `/faq` (2026-04-25).

Gaps remaining:

- [ ] Real user-management-api implementation of the §2.7.4 attachment paths + Firebase admin-SDK email-verification
      link generation. The UI + mock surfaces are in place; production wiring lives outside this workspace and is the
      remaining handoff.
- [ ] Strategy Evaluation → walkthrough input handover: the operator-side admin view should surface the most recent
      `/strategy-evaluations/{id}` for the prospect when they reach the platform-walkthrough stage, so the operator
      drives the walkthrough against their declared shape.
- [ ] Wire stale §2.3.2 / §2.3.4 references in `app/(public)/signup/components/signup/onboarding-wizard.tsx` and
      `lib/api/mock-provisioning-state.ts` to the renumbered §2.7.2 / §2.7.4 anchors.
- [ ] **Strategy Review (§2.5)** — gated route at `/strategy-review` + admin tooling at `/admin/strategy-reviews`.
      Tracked under `marketing_site_three_route_consolidation_2026_04_26.plan.md`. (Stage was §2.4b until the 2026-04-26
      walkthrough/review reorder.)
- [ ] **Three-route marketing collapse** — homepage / nav / engagement-route pages consolidated to three public routes
      (Odum-Managed Strategies / DART Trading Infrastructure / Regulated Operating Models). Service paths in §2.7.2
      remain four; see naming-convention paragraph for the marketing↔legal mapping.
- [ ] **Regulatory legal label compliance review** — decide whether new legal/admin drafting permanently moves from
      "Regulatory Umbrella" to "Regulated Operating Models" or to specific structure names (Advisory / AR / SMA /
      affiliate fund).

---

## 4. Change log

| Date       | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Commit                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| 2026-04-22 | Initial playbook. Questionnaire gate + service-list refresh landed in unified-trading-system-ui.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | _(see live-defi-rollout)_ |
| 2026-04-22 | §2.5.4 + Gaps remaining sweep: slim Regulatory step 3 (no-upload contract-summary panel), drop the IM doc-blocker on submit + the redundant duplicate `submitSignup` in step 4, persist `submissionId` on the questionnaire envelope, mock signup attaches the questionnaire by id-or-email lookup and records the email-verify intent, post-demo provisioning callout on DART / Signals path. Real user-management-api implementation remains as a follow-up.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | _(see live-defi-rollout)_ |
| 2026-04-25 | Funnel revised from 6 to 8 stages. Questionnaire is now the primary briefings access-code gate (deep dives moved AFTER questionnaire); Strategy Evaluation inserted as a new on-the-record DDQ stage between the initial call and the tailored demo; signup go-live timing reframed as "within a month of go-ahead", anchored on the affiliate network (custodian, fund administrator, AIFM partner, repeatable provisioning modules). Signup sub-sections renumbered §2.5.x → §2.7.x. Public FAQ updated to match.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | _(this commit)_           |
| 2026-04-26 | Funnel revised from 8 to 9 stages. New §2.4b Strategy Review stage inserted between Strategy Evaluation (§2.4) and Tailored demo (§2.5) — per-prospect magic-link surface at `/strategy-review` showing proposed operating model, DART config options, regulatory pathway, demo prep, and next steps. §2.7.2 service-path table gains a "Marketing label" column (Odum-Managed Strategies / DART Trading Infrastructure / Regulated Operating Models) — public marketing collapses Odum Signals into DART; legal/contract/signup labels stay unchanged. URL slugs unchanged.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | _(this commit)_           |
| 2026-04-26 | Walkthrough/Review reorder. §2.4b ("Strategy Review") and §2.5 ("Tailored demo") swapped positions and renamed: §2.4b is now "Platform walkthrough" (was "Tailored demo") and §2.5 is now "Strategy Review" (was §2.4b). Rationale: a tailored demo is more useful AFTER the DDQ has scoped the prospect (so the walkthrough hits the right components) and BEFORE the Strategy Review (so synthesis is grounded in fit observations rather than a theoretical operating-model deck). Stage count unchanged at 9. Public homepage rail bumped from 6 to 7 visible steps; engagement-route process strips bumped from 5 to 6. Strategy Review's "demo preparation" section reframed as "walkthrough follow-up".                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | _(this commit)_           |
| 2026-04-26 | Three-context access model added (Funnel Coherence plan, Workstream H). The same DART / Reports / Strategy Catalogue component stack now renders in three contexts: (1) **public / gated education** (§2.1–§2.4b — no `/services/*` redirects from public submissions), (2) **controlled demo / UAT** (§2.5 — admin issues demo-session entitlements that unlock selected `/services/*` surfaces in mock-data mode with clear demo labelling), (3) **production signed-in client** (§2.7 onward — real entitlements + real data). §2.5 Platform walkthrough reframed as the demo/UAT context entry-point: surfaces opened depend on persona (DART research/execution/observe/reporting; IM allocator Reports + Strategy Catalogue Reality+Explore; Odum Signals counterparty surface; LP Investor Relations + Reports). New supporting concepts: `accessContext` enum, `lib/auth/demo-session.ts`, `/admin/demo-sessions` admin tooling, `<DemoBanner>`. `FomoTearsheetCard.tsx` keeps its internal name; product copy says "Explore" not "FOMO".                                                                                                                                                                                                                                                                                                                                                                  | _(this commit)_           |
| 2026-04-26 | Walkthrough/Review reorder ROLLBACK + Commercial Tailoring rename (Funnel Coherence plan, Workstream G). §2.4b is back to "Strategy Review" (pre-§2.5 walkthrough); §2.5 is back to "Platform walkthrough" (kept the rename from "Tailored demo"); §2.6 renamed from "Bespoke tailoring" to "Commercial Tailoring". Strategy Review scope **reframed** to a pre-demo prep pack — proposed route hypothesis, briefing excerpts, demo agenda, workflows likely to be shown, curated examples, missing-info checklist, route-specific risks. NOT a final commercial proposal (that's Commercial Tailoring at §2.6). Rationale: Strategy Review delivered AFTER the demo was awkward because the prospect had already seen the platform — Strategy Review is more useful as a tailored prep pack that sets up a relevant walkthrough. Public homepage rail stays 7 stages but now reads Q → Briefings → Initial → Eval → Review → Walkthrough → Commercial Tailoring (Onboarding implicit, off the rail). Engagement-route process strips on `/investment-management`, `/platform`, `/regulatory` mirror the same 7 stages. Strategy Review `_client.tsx` section schema added 7 new optional fields (proposedRouteHypothesis · briefingExcerpts · demoAgenda · workflowsShown · curatedExamples · missingInformation · routeRisks); legacy fields kept as fallbacks for backwards compat. Stage count unchanged at 9. | _(this commit)_           |
