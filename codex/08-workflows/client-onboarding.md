---
scope: [sales, engineer, admin]
---

# Client Onboarding — 7-step canonical sequence

> **Status:** canonical (2026-04-24) **Owner:** Sales + UI Architecture **SSOT for:**
> `unified-trading-system-ui/app/(public)/questionnaire/page.tsx`,
> `unified-trading-system-ui/app/(platform)/services/strategy-catalogue/page.tsx`,
> `unified-trading-system-ui/lib/auth/personas.ts`, `unified-trading-system-ui/lib/auth/demo-provider.ts`. **Plan:**
> [`plans/active/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../plans/active/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
> **Companion docs:** [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md),
> [`signup-signin-workflow.md`](./signup-signin-workflow.md),
> [`../09-strategy/architecture-v2/strategy-questionnaire-mapping.md`](../09-strategy/architecture-v2/strategy-questionnaire-mapping.md),
> [`../09-strategy/architecture-v2/strategy-catalogue-3tier.md`](../09-strategy/architecture-v2/strategy-catalogue-3tier.md),
> [`../04-architecture/service-family-scope.md`](../04-architecture/service-family-scope.md).

---

## §1 — Why one canonical sequence

Prospects arrive through multiple channels (Calendly, `/contact` form, warm intros, briefing pages) but the handshake
into a signed mandate is the same every time: Ikenna qualifies fit on a call, the prospect self-serves the
questionnaire, they play with the strategy universe shaped by their answers, and only then does a commercial call lock
scope. The sequence is deliberately asymmetric — Ikenna does less after each step, the system does more — so that by
step 7 (production onboarding) the mandate shape is self-evident and signup is mechanical.

Every step has three actors: **Ikenna (sales)**, **client (prospect / paying-client)**, and **system (UI + UAC +
Firestore)**. If any actor is missing a defined action, the step stalls — the playbook below names all three at every
step so nothing falls through.

---

## §2 — The 7 steps

### Step 1 — Initial contact

| Actor  | Action                                                                                                                                                                              |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Client | Lands on `odum-research.com`; either books a Calendly slot (`https://calendly.com/odum-ikenna`) or sends a typed message via `/contact?service=<x>&action=<y>`.                     |
| Ikenna | Receives the booking (Calendly email) or `/contact` form submission; replies within 24h acknowledging. For a typed-message request that doesn't yet need scheduling, replies first. |
| System | `/contact` form stored via `api/contact/route.ts`; Calendly booking arrives via email webhook. Neither triggers auth state yet — prospect is anonymous.                             |

**CTA routing convention**: "Book a call / Demo / Discuss a Mandate" sends to Calendly (skip form); "Contact /
Partnership / request access code" sends to `/contact`. See
[`feedback_marketing_cta_routing_calendly_vs_contact.md`](../../../.claude/projects/…/memory/feedback_marketing_cta_routing_calendly_vs_contact.md)
(memory; duplicated here for completeness).

### Step 2 — Briefings review

| Actor  | Action                                                                                                                                                                                                                                                                                                                                                                      |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ikenna | Based on the initial conversation, sends 1-3 briefing links tailored to the prospect's stated shape. Typical bundles: (a) **IM candidate** → `/briefings/investment-management`; (b) **Emerging manager / AR candidate** → `/briefings/regulatory`; (c) **DART Signals-In candidate** → `/briefings/dart-signals-in`; (d) **DART Full candidate** → `/briefings/dart-full`. |
| Client | Reads the briefing(s). If unsure, requests an access code (light-auth gated briefings use `NEXT_PUBLIC_BRIEFING_ACCESS_CODE`; see [`../14-playbooks/authentication/light-auth-briefings.md`](../14-playbooks/authentication/light-auth-briefings.md)).                                                                                                                      |
| System | `BriefingAccessGate` writes `odum-briefing-session` to `localStorage` on successful unlock, so `/questionnaire`, `/briefings/*`, and `/docs` share one session.                                                                                                                                                                                                             |

Not every prospect needs briefings — warm inbound often skips to step 3. But briefings are cheap reading material that
resolves 80% of "is this the right shape?" questions before burning a call.

### Step 3 — Questionnaire

| Actor  | Action                                                                                                                                                                                                                                                                                                                 |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ikenna | Sends the `/questionnaire` URL (or it's linked from the briefing the prospect just read). Access code is the same as briefings.                                                                                                                                                                                        |
| Client | Fills 11 axes (6 base required + 5 strategy-preference optional; 7 Reg-Umbrella optional if `service_family ∈ {RegUmbrella, combo}`). Takes ~5 minutes. Submits.                                                                                                                                                       |
| System | Writes `QuestionnaireResponse` to Firestore `/questionnaires/{id}` (staging/prod) or `localStorage` (dev/mock). Envelope `{email, firm_name, access_code_fingerprint}` stored alongside. After submit, `router.push("/services/strategy-catalogue?tab=explore&from=questionnaire&${filterQs}")` — step 4 is automatic. |

SSOT schema: [`strategy-questionnaire-mapping.md`](../09-strategy/architecture-v2/strategy-questionnaire-mapping.md)
(derivation) + [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md) (admin playback + docs flow) +
[`../02-data/questionnaire-axes.md`](../02-data/questionnaire-axes.md) (full axis catalogue).

### Step 4 — Strategy universe exploration

| Actor  | Action                                                                                                                                                                                                                                                                                                                                                                      |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ikenna | No direct action. Optionally watches admin catalogue view to confirm the prospect's filter surfaces sensible candidates.                                                                                                                                                                                                                                                    |
| Client | Lands on `/services/strategy-catalogue?tab=explore&from=questionnaire&<filters>` with the FOMO feed pre-filtered to their profile. Emerald banner: "Showing strategies that match your questionnaire profile. [View all] [Edit preferences]." In demo mode (`NEXT_PUBLIC_AUTH_PROVIDER=demo`), toggles `DemoPlanToggle` to compare DART Full vs Signals-In universes.       |
| System | `parseCatalogueFilter(URLSearchParams)` hydrates the filter from the URL. FOMO cards render with tier badges (emerald "Full + Signals-In" vs amber "DART Full only") + "View returns →" CTA linking to `/services/reports/strategy/{instanceId}`. If client lacks `strategy-full` entitlement, amber Signals-In banner: "Viewing as Signals-In — N/M strategies available." |

Explore tab is discovery + subscription surface only. Detailed P&L / returns always link out to the reporting service
(`/services/reports/strategy/{instanceId}`); FOMO cards never duplicate charts.

### Step 5 — Strategy evaluation pack (optional)

| Actor  | Action                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ikenna | For proprietary-strategy (DART Signals-In / Full / Odum-Signals-out) prospects, sends the `/strategy-evaluation` URL so they can describe their strategy and upload evidence. Not always used.                                                                                                                                                                                                                                                       |
| Client | Fills the 8-step wizard (about-you → path → strategy shape → backtest setup → evidence/metrics → strategy/risk → path-specific → validation). Trade-log / equity-curve CSV uploads up to 500 MB. Drafts auto-save to localStorage **and** to Firestore (`strategy_evaluation_drafts/{sha256(email)}`) so they can resume from any device.                                                                                                            |
| System | On submit, persists the pack to Firestore (`strategy_evaluations/{id}`) via Firebase **Admin SDK** + emails the submitter a magic-link CTA. The link opens `/strategy-evaluation/status?token=…` — a server-rendered (force-dynamic) page showing submission details, downloadable docs, and an "Edit and resubmit" link. Each refile is a new linked document (`parentSubmissionId` pointer); no in-place mutation. Internal copy BCC'd to `info@`. |
| System | "Already submitted? Resend my access link →" on the form: looks up `strategy_evaluations` by email; falls back to `strategy_evaluation_drafts` and emails a "Resume your draft" link (`/strategy-evaluation?draft=email`). Always returns generic confirmation client-side so the endpoint can't enumerate emails.                                                                                                                                   |
| Admin  | Views submissions at `/admin/strategy-evaluations/{id}`.                                                                                                                                                                                                                                                                                                                                                                                             |

Architecture notes:

- Form is split into a server-component shell (`page.tsx`) and a client wizard (`_client.tsx`). The shell resolves
  `?token=` (magic-link refile) or `?draft=email` (draft resume) via Admin SDK and bakes the prior payload into the
  initial render via `initialData` props — avoids the React 19 / Next.js 15 client-fetch hydration race that produced
  flash-of-empty-fields.
- All Firestore reads/writes from API routes use `firebase-admin` so the routes work regardless of
  `NEXT_PUBLIC_FIREBASE_*` bake-state (UAT historically didn't have those vars).
- Storage rules are size-cap-only (500 MB). Earlier content-type allow-list rejected legitimate `.md` uploads.
- Confirmation emails route via Resend from `hello@mail.odum-research.com` (prod) / `hello@mail.uat.odum-research.com`
  (uat) / `onboarding@resend.dev` (dev).

Skip this step when the prospect is purely interested in Odum-catalogue strategies (majority of DART Full, IM, Reg
Umbrella cases).

### Step 6 — Phone / video call

| Actor  | Action                                                                                                                                                                                                                                                       |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Ikenna | 45-60 min call. Walks the prospect through their filtered universe on the staging UI, toggles DART Full vs Signals-In if relevant, confirms mandate shape (IM vs DART vs Reg Umbrella vs combo), pricing framework, regulatory posture, onboarding timeline. |
| Client | Confirms scope or raises a specific reservation. Outcome of the call is either a named next commitment (mandate signing, onboarding kickoff date, deeper session on one surface) or a specific gap sales addresses directly.                                 |
| System | Sales records call outcome in `account-intelligence-record` (see [`../14-playbooks/demo-ops/account-intelligence-record.md`](../14-playbooks/demo-ops/account-intelligence-record.md)) + `meeting-history-and-interest-tracking` entry.                      |

"Interesting, let's keep in touch" is **not** an outcome. The call is designed to resolve — follow-up is orchestrated by
[`post-demo-followup-orchestration.md`](../14-playbooks/demo-ops/post-demo-followup-orchestration.md) if the commitment
isn't in the meeting.

### Step 7 — Production onboarding

| Actor  | Action                                                                                                                                                                                                                                                                                                                          |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ikenna | Approves signup in `/admin/organizations/[id]`. Sets entitlements (per resolved commercial path — see [`service-family-scope.md`](../04-architecture/service-family-scope.md)). Uploads or collects regulatory docs via `/api/onboarding/upload` (see [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md) §5). |
| Client | Completes signup form → Firebase Auth user created (initially disabled, `pending_approval`). After Ikenna approves, logs in with real credentials → lands on dashboard gated to paid entitlements.                                                                                                                              |
| System | `user-management-api` creates `Firebase Auth` user + Firestore `/users/{uid}` profile; attaches `questionnaire_response_id` from the envelope. `unified-trading-api` reads entitlements; `services/*` tabs render per entitlement + service-family-scope. `DemoPlanToggle` no longer renders (it's demo-provider-only).         |

Post-onboarding, the client operates the same staging UI they demo'd. Same components, same data shapes — only the
auth + data provenance differ (see
[`../14-playbooks/_ssot-rules/03-same-system-principle.md`](../14-playbooks/_ssot-rules/03-same-system-principle.md)).

---

## §3 — Cross-references

- [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md) — questionnaire form, admin playback, docs flow.
- [`signup-signin-workflow.md`](./signup-signin-workflow.md) — self-serve signup mechanics + target-state funnel.
- [`../09-strategy/architecture-v2/strategy-questionnaire-mapping.md`](../09-strategy/architecture-v2/strategy-questionnaire-mapping.md)
  — 11-axis → catalogue-filter derivation.
- [`../09-strategy/architecture-v2/strategy-catalogue-3tier.md`](../09-strategy/architecture-v2/strategy-catalogue-3tier.md)
  — Reality / FOMO tab roles, admin universe / editor surfaces.
- [`../04-architecture/service-family-scope.md`](../04-architecture/service-family-scope.md) — DART Full vs Signals-In
  feature matrix, locked-section design, demo plan toggle.
- [`../14-playbooks/demo-ops/staging-demo-setup.md`](../14-playbooks/demo-ops/staging-demo-setup.md) — staging demo
  persona onboarding checklist.
- [`../14-playbooks/demo-ops/profiles/desmond-dart-full.yaml`](../14-playbooks/demo-ops/profiles/desmond-dart-full.yaml)
  - [`desmond-signals-in.yaml`](../14-playbooks/demo-ops/profiles/desmond-signals-in.yaml) — worked example (real
    client).
