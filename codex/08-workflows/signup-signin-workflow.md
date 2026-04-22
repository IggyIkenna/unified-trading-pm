# Signup / Signin workflow — prospect → client

**Status:** target-state playbook · 2026-04-22

Defines the canonical prospect-to-client journey, how the self-serve signup flow is shaped per commercial path, and the
current vs target state of what the UI actually implements.

**Companion docs:**

- [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md) — the questionnaire form itself (axes,
  submission, envelope).
- [`../14-playbooks/authentication/firebase-staging.md`](../14-playbooks/authentication/firebase-staging.md) /
  [`firebase-production.md`](../14-playbooks/authentication/firebase-production.md) — Firebase project setup, roles, and
  Firestore rules.
- [`../14-playbooks/authentication/light-auth-briefings.md`](../14-playbooks/authentication/light-auth-briefings.md) —
  the briefings access-code gate (separate from the main client sign-in).

---

## 1. The full prospect journey

The target funnel has **six ordered stages**. Each stage writes a durable artifact the next stage consumes; a prospect
can pause and resume at any point via their email address. The sequencing is deliberate — each step tailors the next one
so neither side re-treads ground on later calls.

```
Deep dives / marketing pages (optional read)
       │    (reader decides this is worth a call, requests access code)
       ▼
Questionnaire (~2 min, 6 base + 7 Reg-Umbrella axes)
       │    → Firestore /questionnaires/{id}  (staging/prod)
       │    → localStorage                    (dev / mock)
       │    → sends envelope {email, firm, fingerprint}
       ▼
Initial call (~30 min) — fit discussion
       │    (confirm Odum is the right shape, confirm we understood
       │     enough from the questionnaire to tailor the right product)
       ▼
Demo (guided → self-serve)
       │    (operator walkthrough first; then prospect drives it themselves
       │     and decides whether the value is there)
       ▼
Bespoke tailoring
       │    (catalogue opens here: ~2,500 combinations. Customise strategies,
       │     infrastructure, regulatory posture from it. Contract scope
       │     is locked off in preparation for signup.)
       ▼
Signup + go live (self-serve form → user-management-api)
       │    → Firebase Auth user (disabled, pending_approval)
       │    → Firestore /users/{uid} profile
       │    → attaches questionnaire_response_id from envelope.email
       │    (same week as the bespoke conversation is realistic when green)
       ▼
Signin → dashboard (post-approval, access-token granted)
```

Key properties:

- **The questionnaire's email is the primary cross-link.** The signup flow looks up the prior questionnaire response by
  that email and attaches it to the user record — so client-facing staff opening the admin view see the full journey in
  one place.
- **Signup sits near the end of the funnel, not the start.** Short-circuiting to signup before the demo would mean
  provisioning blind; the sequencing above exists so we don't.
- **The ~2,500-combination catalogue opens at the bespoke-tailoring stage**, not earlier. It's not coy — it's how trust
  is built, and it protects clients who have already locked off their piece.

---

## 2. Stage-by-stage contract

### 2.1 Questionnaire stage

- **Required inputs:** base 6 axes (categories, instrument types, venue scope, strategy styles, service family, fund
  structure). Reg-Umbrella axes 7-13 are conditional on `service_family = "RegUmbrella"`.
- **Envelope fields (optional):** email, firm_name. Envelope is stored alongside the response and is the handle used at
  signup time to find the response.
- **Sink:** Firestore `/questionnaires/{auto-id}` in staging/prod; `localStorage[questionnaire-response-v1]` +
  `[questionnaire-envelope-v1]` in dev / mock.
- **Access gate:** briefing access code (light-auth, shared key). Not the same as the main app sign-in.
- **SSOT:** [`prospect-questionnaire-flow.md`](./prospect-questionnaire-flow.md).

### 2.2 Initial call stage (~30 min)

- **Not a UI write.** Booked via Calendly, operator-led.
- Purpose: fit confirmation. Check that Odum is the right shape for the prospect, and that we've understood enough from
  the questionnaire to tailor the right product at the demo.
- Operator notes go into internal CRM; no public-facing artifact beyond the calendar event.

### 2.3 Demo stage

- **Not a UI write** (platform provisioning at this stage is always an operator-side affair; account + keys come later
  at signup).
- Two halves: (1) guided walkthrough where an Odum operator drives the UI against the prospect's shape, (2) self-serve
  exploration where the prospect runs the platform themselves and forms a value judgement.
- **The catalogue does not open at the demo.** It opens at bespoke tailoring (§2.4) only if the fit is confirmed here.

### 2.4 Bespoke tailoring stage

- **Not a UI write.** Usually one or two targeted calls, sometimes a shared document trail.
- **The ~2,500-combination catalogue opens here.** Strategies, infrastructure, regulatory posture are customised from
  it; the contract scope that will drive signup is locked off during this stage.
- Output: a concrete contract shape the prospect can sign off on; ready to move to signup.

### 2.5 Signup stage

#### 2.5.1 Gate: questionnaire-completed check

- `/signup` reads `localStorage[questionnaire-response-v1]` on mount.
- **If present:** show a one-line acknowledgement banner ("Questionnaire on file for `<email>` — we'll attach your
  answers to this signup") and render the service-specific form.
- **If absent:** show a gate card with two CTAs:
  1. "Take the questionnaire →" (primary) — deep-links to `/questionnaire?service=<mapped>` where mapped = IM / DART /
     RegUmbrella depending on the signup `?service=` param.
  2. "I've already filled it in, continue" (secondary, for cross-device cases) — proceeds directly to the form; we rely
     on email cross-reference at submit time.

#### 2.5.2 Service-specific signup fields

Signup UI is shaped by the `?service=` query param. Four paths; fields are minimal per path because we already have the
prospect's answers from the questionnaire.

| Path                                              | Fields                                                                                                                                                             | Rationale                                                                                                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Investment Management** (`?service=investment`) | Full name · Email · Entity name · Entity registered address · Contact channel (phone / Telegram handle / WhatsApp — pick one) · Password (choose)                  | We generate the investment management agreement and custody letters from these fields. No PEP / KYC docs uploaded at this stage — that moves to the admin-side onboarding queue post-approval. |
| **DART** (`?service=platform`)                    | Full name · Email · Password (choose)                                                                                                                              | Platform access is provisioned post-demo. Questionnaire answers already contain the service family, asset-class scope, and strategy profile — no further signup fields needed.                 |
| **Odum Signals** (`?service=signals`)             | Full name · Email · Password (choose)                                                                                                                              | Same rationale as DART. Signal-counterparty agreement is drafted from the questionnaire + demo call, not the signup form.                                                                      |
| **Regulatory Umbrella** (`?service=regulatory`)   | Full name · Email · Entity name · Entity registered address · Contact channel (phone / Telegram / WhatsApp) · Engagement type (AR vs Advisory) · Password (choose) | Contract generation needs entity details; regulatory activities profile comes from the questionnaire. KYC-level docs move to the admin-side queue.                                             |

**Principle:** no document uploads at the public-facing signup stage. The form generates contracts from entity fields;
document exchange (signed agreements, proof of address, etc.) happens on the admin side via Firebase Storage signed URLs
after approval.

#### 2.5.3 Password rules

- Minimum 12 characters, at least one uppercase + lowercase + digit.
- Password is set at signup (not assigned by ops).
- Firebase Auth user is created in `disabled=true` state; ops flips `disabled=false` after KYC/AML checks pass.

#### 2.5.4 Questionnaire attachment

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

### 2.6 Signin stage

- Standard Firebase Auth email + password.
- `disabled=true` accounts see a "pending approval" landing page (`/pending`) with status info and a support contact
  link.
- Approved accounts land on `/dashboard` with role-scoped nav.

---

## 3. Current state vs target (as of 2026-04-22)

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
      paths described in §2.5.4 (2026-04-22).
- [x] DART + Odum Signals path on `GenericSignup` shows a "post-demo provisioning" callout so prospects know account
      keys are issued after the demo, not at form submit (2026-04-22).
- [x] `SignupPayload.send_email_verification` opts the new account into Firebase admin-SDK email verification at signup
      time. Mock backend records `email_verification_pending: true` on the user profile so admin tooling can surface it
      (2026-04-22).

Gaps remaining:

- [ ] Real user-management-api implementation of the §2.5.4 attachment paths + Firebase admin-SDK email-verification
      link generation. The UI + mock surfaces are in place; production wiring lives outside this workspace and is the
      remaining handoff.

---

## 4. Change log

| Date       | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Commit                    |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| 2026-04-22 | Initial playbook. Questionnaire gate + service-list refresh landed in unified-trading-system-ui.                                                                                                                                                                                                                                                                                                                                                               | _(see live-defi-rollout)_ |
| 2026-04-22 | §2.5.4 + Gaps remaining sweep: slim Regulatory step 3 (no-upload contract-summary panel), drop the IM doc-blocker on submit + the redundant duplicate `submitSignup` in step 4, persist `submissionId` on the questionnaire envelope, mock signup attaches the questionnaire by id-or-email lookup and records the email-verify intent, post-demo provisioning callout on DART / Signals path. Real user-management-api implementation remains as a follow-up. | _(see live-defi-rollout)_ |
