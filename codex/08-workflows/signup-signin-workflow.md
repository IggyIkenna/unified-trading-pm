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

The target funnel has four ordered stages. Each stage writes a durable artifact the next stage consumes; a prospect can
pause and resume at any point via their email address.

```
Briefings / marketing pages
       │    (reader decides this is worth a call)
       ▼
Questionnaire (~2 min, 6 base + 7 Reg-Umbrella axes)
       │    → Firestore /questionnaires/{id}  (staging/prod)
       │    → localStorage                    (dev / mock)
       │    → sends envelope {email, firm, fingerprint}
       ▼
Demo (45-min call) ← Calendly
       │    (internal notes logged post-call; no UI writes)
       ▼
Signup (self-serve form → user-management-api)
       │    → Firebase Auth user (disabled, pending_approval)
       │    → Firestore /users/{uid} profile
       │    → attaches questionnaire_response_id from envelope.email
       ▼
Signin → dashboard (post-approval, access-token granted)
```

Key property: **the questionnaire's email is the primary cross-link**. The signup flow looks up the prior questionnaire
response by that email and attaches it to the user record — so client-facing staff opening the admin view see the full
journey in one place.

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

### 2.2 Demo stage

- **Not a UI write.** External booking via Calendly.
- Internal CRM follow-up happens in operator tools; no public-facing artifact beyond the calendar event.
- A prospect can reach signup without doing a demo — the funnel strongly prefers demo-before-signup for IM / Regulatory,
  but allows email-capture for DART / Odum Signals before the demo call.

### 2.3 Signup stage

#### 2.3.1 Gate: questionnaire-completed check

- `/signup` reads `localStorage[questionnaire-response-v1]` on mount.
- **If present:** show a one-line acknowledgement banner ("Questionnaire on file for `<email>` — we'll attach your
  answers to this signup") and render the service-specific form.
- **If absent:** show a gate card with two CTAs:
  1. "Take the questionnaire →" (primary) — deep-links to `/questionnaire?service=<mapped>` where mapped = IM / DART /
     RegUmbrella depending on the signup `?service=` param.
  2. "I've already filled it in, continue" (secondary, for cross-device cases) — proceeds directly to the form; we rely
     on email cross-reference at submit time.

#### 2.3.2 Service-specific signup fields

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

#### 2.3.3 Password rules

- Minimum 12 characters, at least one uppercase + lowercase + digit.
- Password is set at signup (not assigned by ops).
- Firebase Auth user is created in `disabled=true` state; ops flips `disabled=false` after KYC/AML checks pass.

#### 2.3.4 Questionnaire attachment

- At submit, the signup API (POST `/api/v1/signup`) receives the prospect's email.
- Backend looks up the most recent `/questionnaires/{id}` document where `submitted_by.email == signup.email` and stores
  that ID on the user profile as `questionnaire_response_id`.
- If no match: user profile is created without the ID; ops is notified so they can manually link on review.

### 2.4 Signin stage

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

Gaps remaining:

- [ ] Signup wizard still has a document-upload step for IM (`onboarding-wizard-tail.tsx` step 3). Target: remove for
      IM; keep a minimal version for Regulatory (engagement type + entity details → contract generation; no PEP docs at
      this stage).
- [ ] Contact-channel picker (phone / Telegram / WhatsApp) not yet implemented — current step 1 only has an optional
      phone field.
- [ ] Signup payload (`lib/api/signup-client.ts::SignupPayload`) doesn't yet carry `questionnaire_response_id`; backend
      lookup-by-email is also not yet implemented in user-management-api.
- [ ] DART + Odum Signals signup currently routes through `GenericSignup` (email capture) rather than a dedicated
      minimal form. Works for now; may want a clearer "post-demo provisioning" label.
- [ ] No email confirmation step — Firebase `sendEmailVerification()` is not called at signup.

---

## 4. Change log

| Date       | Change                                                                                           | Commit                    |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------------------- |
| 2026-04-22 | Initial playbook. Questionnaire gate + service-list refresh landed in unified-trading-system-ui. | _(see live-defi-rollout)_ |
