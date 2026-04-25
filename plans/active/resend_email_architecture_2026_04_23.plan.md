---
title: Resend Email Architecture
status: active
created: 2026-04-23
locked_by: live-defi-rollout
locked_since: 2026-04-23
target_repos:
  - unified-trading-system-ui
readiness: C1
---

# Resend Email Architecture

## Context

The marketing site and platform send transactional email via Resend. Two routes already exist and mostly work but have
wrong sender addresses. Firebase auth emails (verify-email, reset-password) still use Firebase's default email sender —
these need to come through Resend via the Firebase Admin SDK custom-action-link flow (Option 2).

### What already exists

| File                                          | Status  | Issue                                                                      |
| --------------------------------------------- | ------- | -------------------------------------------------------------------------- |
| `app/api/contact/route.ts`                    | Exists  | FROM is `website@` (should be `hello@`); TO is `.co.uk` (should be `.com`) |
| `app/api/onboarding/confirm-email/route.ts`   | Exists  | FROM is `onboarding@` (should be `auth@`); contact link is `.co.uk`        |
| `lib/firebase-admin.ts`                       | Exists  | Already configured with ADC + JSON credential                              |
| `app/(public)/questionnaire/page.tsx`         | Exists  | No email send on submit — Firestore-only                                   |
| `lib/questionnaire/submit.ts`                 | Exists  | Firestore/localStorage only, no email                                      |
| `app/api/auth/send-verification/route.ts`     | Missing | Firebase Admin → generate link → Resend send                               |
| `app/api/auth/send-reset/route.ts`            | Missing | Firebase Admin → generate link → Resend send                               |
| `app/(public)/auth/verify-email/page.tsx`     | Missing | Custom action handler landing page                                         |
| `app/(public)/auth/reset-password/page.tsx`   | Missing | Custom action handler landing page                                         |
| `app/api/questionnaire/email/route.ts`        | Missing | Acknowledgement + internal notify after questionnaire submit               |
| `app/(public)/strategy-evaluation/page.tsx`   | Missing | Online Strategy Evaluation Form (DDQ) — shareable link                     |
| `app/api/strategy-evaluation/submit/route.ts` | Missing | Firestore persist + Resend email for DDQ                                   |
| `lib/email/resend.ts`                         | Missing | Shared env-aware sender config                                             |

### Three-environment email split

| Environment                          | Sending domain                   | Resend sender                                                                  | API key env var                  |
| ------------------------------------ | -------------------------------- | ------------------------------------------------------------------------------ | -------------------------------- |
| Production (`www.odum-research.com`) | `mail.odum-research.com`         | `hello@mail.odum-research.com` / `auth@mail.odum-research.com`                 | `RESEND_API_KEY`                 |
| Staging / Firebase staging           | `staging-mail.odum-research.com` | `hello@staging-mail.odum-research.com` / `auth@staging-mail.odum-research.com` | `RESEND_API_KEY` (staging value) |
| Dev / local                          | Resend test domain               | `onboarding@resend.dev`                                                        | unset — graceful skip            |

### Sender assignment

| Email type                                       | From address                   | Reply-To                 |
| ------------------------------------------------ | ------------------------------ | ------------------------ |
| Contact form notification (internal)             | `hello@mail.odum-research.com` | submitter's email        |
| Questionnaire acknowledgement (to user)          | `hello@mail.odum-research.com` | `info@odum-research.com` |
| Questionnaire notification (internal)            | `hello@mail.odum-research.com` | submitter's email        |
| Strategy Evaluation Form acknowledgement         | `hello@mail.odum-research.com` | `info@odum-research.com` |
| Strategy Evaluation Form notification (internal) | `hello@mail.odum-research.com` | submitter's email        |
| Welcome / account confirmed                      | `auth@mail.odum-research.com`  | —                        |
| Verify email                                     | `auth@mail.odum-research.com`  | —                        |
| Password reset                                   | `auth@mail.odum-research.com`  | —                        |

### Firebase custom action URL flow

Firebase generates action links (verify / reset). The `continueUrl` and `url` in `ActionCodeSettings` point to our
custom handler pages so Firebase redirects to:

- `https://www.odum-research.com/auth/verify-email?oobCode=...`
- `https://www.odum-research.com/auth/reset-password?oobCode=...`

The Firebase Console → Authentication → Templates → Action URL must also be set to `https://www.odum-research.com/auth`
so Firebase's own "email action" links redirect to our pages instead of Firebase's default UI.

---

## ⚠️ Human Operator Actions Required BEFORE Code Is Live

These cannot be automated — they require access to Resend and the domain registrar.

### Step 1 — Resend account setup

1. Log into [resend.com](https://resend.com) (create account if needed)
2. **Add domain** → `mail.odum-research.com`
   - Resend will display SPF, DKIM, DMARC DNS records — copy all of them
3. **Add domain** → `staging-mail.odum-research.com`
   - Copy those DNS records too
4. Go to your domain registrar (where `odum-research.com` is registered) and add ALL DNS records for both domains
5. Back in Resend dashboard, click **Verify** for both domains — wait for DNS propagation (may take up to 24h)

### Step 2 — API keys (already in Secret Manager — just verify domain scope)

The prod and staging Resend API keys are already stored in Secret Manager and mounted to Cloud Run. No new key creation
needed. Just confirm in the Resend dashboard that each key has sending permission scoped to the correct domain:

6. Resend → API Keys → open the prod key → confirm it has **Sending access** scoped to `mail.odum-research.com` (if it
   was created with "All domains", that also works — scoping is tighter but optional)
7. Open the staging key → confirm sending access for `staging-mail.odum-research.com`

If either key is scoped to a different domain or has no domain, edit it in Resend to match. The Secret Manager values
and Cloud Run mounts do not need to change.

### Step 3 — Firebase Console

8. Firebase Console → select production project (`central-element-323112`)
9. Authentication → Settings → **Authorized domains** — add:
   - `www.odum-research.com`
   - `odum-research.com`
10. Authentication → **Email Templates** → for each template (Email Verification, Password Reset):
    - Click **Customize action URL**
    - Set to `https://www.odum-research.com/auth`
    - This makes Firebase redirect to our custom handler pages

### Step 4 — Confirm Secret Manager mount name (quick check)

8. Confirm the Secret Manager secret name the prod Cloud Run service mounts `RESEND_API_KEY` from (e.g.
   `gcloud run services describe odum-portal --region ... --format json | jq .spec.template.spec.containers[0].env`).
   Code references `process.env.RESEND_API_KEY` — if the mount uses a different env var name, align it now. Nothing else
   to do — the keys and mounts are already in place.

---

## Dependency graph

```
Phase 0 (operator)
  └── Phase 1: lib/email/resend.ts
        ├── Phase 2a: fix contact route          (parallel)
        ├── Phase 2b: fix confirm-email route    (parallel)
        ├── Phase 2c: questionnaire email route  (parallel)
        ├── Phase 2d: strategy-evaluation page + submit route (parallel)
        └── Phase 3: auth email routes
              ├── Phase 3a: send-verification route
              ├── Phase 3b: send-reset route
              └── Phase 3c: update login page forgot-password
                    └── Phase 4: custom action handler pages
                          └── Phase 5: QG + quickmerge
```

---

## Phase 1 — Shared email client

**Goal:** `lib/email/resend.ts` — single source of truth for Resend calls and env-aware sender addresses.

- [x] [AGENT] P1. Create `lib/email/resend.ts` with:
  - `getResendApiKey(): string | null` — returns `RESEND_API_KEY` (server-only, never `NEXT_PUBLIC_*`)
  - `getSenderFor(type: "hello" | "auth"): string` — returns env-aware `from` address:
    - dev/no-key → `onboarding@resend.dev`
    - staging → `hello@staging-mail.odum-research.com` or `auth@staging-mail.odum-research.com`
    - prod → `hello@mail.odum-research.com` or `auth@mail.odum-research.com`
    - Detection: if `NEXT_PUBLIC_SITE_URL` contains `staging-mail` or `odumresearch.co.uk` → staging; contains
      `www.odum-research.com` → prod; otherwise dev
  - `sendEmail(params: ResendEmailParams): Promise<{ ok: boolean; sent: boolean; reason?: string }>` — thin wrapper over
    raw `fetch("https://api.resend.com/emails")`. Returns `{ ok: true, sent: false, reason: "no_api_key" }` when key
    absent (dev graceful skip).
  - `type ResendEmailParams` —
    `{ to: string | string[]; subject: string; html: string; replyTo?: string; bcc?: string[]; from?: string }` (from
    defaults to `getSenderFor("hello")` if omitted)

**Success criteria:** TypeScript compiles, no `any` types, unit-testable without side effects.

---

## Phase 2 — Fix existing email routes

Both existing routes have the wrong sender address and `.co.uk` typo. Fix them to use the shared client from Phase 1.

### Phase 2a — Fix contact route (PARALLEL with 2b)

- [x] [AGENT] P2a. Update `app/api/contact/route.ts`:
  - Import `sendEmail`, `getSenderFor` from `@/lib/email/resend`
  - Change `FROM_ADDRESS` from `website@mail.odum-research.com` → use `getSenderFor("hello")`
  - Change `TO_ADDRESS` from `info@odum-research.co.uk` → `info@odum-research.com`
  - Replace the inline `fetch("https://api.resend.com/emails", ...)` with `sendEmail({...})`
  - Remove the inline `escapeHtml` → import from `@/lib/email/resend` (or keep local — whichever is cleaner)

### Phase 2b — Fix confirm-email route (PARALLEL with 2a)

- [x] [AGENT] P2b. Update `app/api/onboarding/confirm-email/route.ts`:
  - Change `FROM_ADDRESS` from `onboarding@mail.odum-research.com` → use `getSenderFor("auth")`
  - Fix `info@odum-research.co.uk` → `info@odum-research.com` in the email body
  - Replace the inline `fetch` with `sendEmail({...})`

### Phase 2c — Questionnaire email route (PARALLEL with 2a/2b)

The questionnaire page at `/questionnaire` submits to Firestore but sends no email today. After a successful Firestore
write, the page should fire a POST to a new API route.

- [x] [AGENT] P2c. Create `app/api/questionnaire/email/route.ts`:
  - `POST { email?: string; firmName?: string; serviceFamily?: string; submissionId?: string }`
  - If `email` present: send acknowledgement to user (From: `hello@`, Reply-To: `info@odum-research.com`)
    - Subject: `"Thanks for submitting your questionnaire — Odum"`
    - Body: "We've received your responses and will be in touch to discuss your strategy path."
    - Lists the service family they selected (DART / RegUmbrella / etc.)
    - Signed: "The Odum Team"
  - Always: internal notification to `info@odum-research.com` (From: `hello@`, Reply-To: submitter email if known)
    - Subject: `"New questionnaire submission — ${firmName || email || 'anonymous'}"`
    - Body: table of submitted axes (service family, categories, fund structure)
  - Graceful no-key fallback (same pattern as other routes)

- [x] [AGENT] P2c-wire. Update `app/(public)/questionnaire/page.tsx` `onSubmit`:
  - After `submitQuestionnaire()` returns `{ success: true }`, fire:
    ```ts
    fetch("/api/questionnaire/email", {
      method: "POST",
      body: JSON.stringify({
        email: state.email,
        firmName: state.firm_name,
        serviceFamily: state.service_family,
        submissionId: outcome.submissionId,
      }),
    }).catch(() => {
      /* fire and forget */
    });
    ```
  - Do not await or block the success UX on email delivery

### Phase 2d — Strategy Evaluation Form (PARALLEL with 2a/2b/2c)

The "Odum Strategy Evaluation Pack" (v4 PDF) becomes an online form at `/strategy-evaluation`. This URL is clean enough
to share with prospects directly. No access gate — it is the outreach artifact.

Completing it supersedes the basic questionnaire: if a user submits the strategy evaluation form, that's their primary
intake record and the questionnaire is not needed.

**Form sections (from PDF):**

| Section | Label                      | Type                                                                                                              |
| ------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A       | Submission details         | Text fields: strategy name, lead researcher, email, phone/Telegram                                                |
| B       | Primary commercial path    | Radio: Path A (DART Full), Path B (DART Signals-In), Path C (Regulatory Umbrella)                                 |
| C       | Relationship understanding | 3 checkboxes (confirm reading)                                                                                    |
| D       | Architecture fit           | Checkboxes: asset groups, instrument types, strategy family, archetype markers; free text for pathway description |
| E       | Backtest methodology       | 12 free-text fields (data granularity, window, trigger methodology, fill model, etc.)                             |
| F       | Tear sheet / evidence      | Link inputs for: methodology doc, assumptions doc, tear sheet, trade log, equity curve, pipeline sample           |
| G       | Key performance metrics    | Numeric inputs: Sharpe, Calmar, max DD, CAGR, win rate, winning/losing days, avg expectancy, benchmark notes      |
| H       | Strategy documentation     | 4 textarea fields: overview, alpha thesis, feature/signal/model logic, weaknesses                                 |
| I       | Risk management            | Textarea: sizing, concentration, stops, drawdown, leverage, kill-switch                                           |
| J       | Path A questions           | Conditionally shown when Path A selected: what to reproduce exactly, DART iteration benefit                       |
| K       | Path B questions           | Conditionally shown when Path B: signal payload mapping, execution/fills workflow                                 |
| L       | Path C questions           | Conditionally shown when Path C: API keys/permissions needed, reporting views required                            |
| M       | Deployment                 | Textarea: where code runs, 24/7 continuity, monitoring/restart/failover                                           |
| N       | Paper trading              | Checkboxes + textarea: validation status, methodology, market-session coverage                                    |
| O       | Live trading               | Checkboxes + textarea: live validation status, session coverage, backtest-vs-live comparison                      |
| P       | Reporting readiness        | Textarea: analytics, reporting, position, P&L, trade, order view expectations                                     |

**Sections Q-S (Odum internal review):** NOT shown on the public form — internal use only.

- [x] [AGENT] P2d-page. Create `app/(public)/strategy-evaluation/page.tsx`:
  - Multi-section form matching sections A-P
  - Sections J/K/L conditionally rendered based on selected commercial path (radio B)
  - Progress indicator showing current section (1-of-16 style, or section name breadcrumb)
  - "Save progress" to localStorage (autosave on field change, restore on revisit)
  - Submit: POST to `/api/strategy-evaluation/submit` — do not navigate away until ack received
  - Success state: "Thank you — we've received your evaluation and will be in touch within 3 business days."
  - Styled to match the rest of the marketing site (dark bg, same typography as `/briefings`, `/contact`)
  - Page title: "Strategy Evaluation — Odum" with subtitle explaining the 3 commercial paths briefly
  - Footer: "This form is confidential. Odum Capital Ltd — FCA authorised · FRN 975797"

- [x] [AGENT] P2d-api. Create `app/api/strategy-evaluation/submit/route.ts`:
  - `POST { sections: A-P data, email?: string, strategyName?: string }`
  - Persist to Firestore collection `strategy_evaluations` with `submittedAt: serverTimestamp()`
  - If `email` present: send acknowledgement (From: `hello@`, Reply-To: `info@odum-research.com`)
    - Subject: `"Your strategy evaluation has been received — Odum"`
    - Body: brief "We've received your evaluation of '${strategyName}' and will review it carefully. You can expect to
      hear from us within 3 business days."
    - Commercial path in the email so they know which path was selected
  - Internal notification to `info@odum-research.com`:
    - Subject: `"New strategy evaluation — ${strategyName || email || 'unnamed'}"`
    - Body: table of: strategy name, lead researcher, email, path selected, asset groups, strategy family, Sharpe (if
      provided), max DD (if provided)
    - Link to internal admin view (placeholder: `/admin/strategy-evaluations` — TBD)
  - Graceful no-key fallback
  - Dev: localStorage only (same as questionnaire)

- [x] [AGENT] P2d-nav. Add `/strategy-evaluation` to the site navigation (footer or relevant marketing pages):
  - Add to `/briefings` page: "Download the strategy evaluation form" → "or complete it online at /strategy-evaluation"
  - Add to `/investment-management` page and `/platform` page: CTA "Submit a strategy for evaluation"
  - No access gate on the route itself — the URL is the access control

**QG gate after Phase 2:** `CI=true npm test -- --run` must pass.

---

## Phase 3 — Auth email routes

Firebase Admin generates a one-time action link → our API route emails it via Resend. The recipient clicks the link →
Firebase validates the `oobCode` → redirects to our custom handler page.

### Phase 3a — Send-verification route (PARALLEL with 3b)

- [x] [AGENT] P3a. Create `app/api/auth/send-verification/route.ts`:

```typescript
// POST /api/auth/send-verification
// Body: { email: string }
// Generates a Firebase email-verification link via Admin SDK and sends it through Resend.
// ActionCodeSettings.url = NEXT_PUBLIC_SITE_URL + "/auth/verify-email"
```

- Use `getAdminAuth()` from `@/lib/firebase-admin`
- Call `auth.generateEmailVerificationLink(email, { url: continueUrl })` where
  `continueUrl = process.env.NEXT_PUBLIC_SITE_URL + "/auth/verify-email"`
- Send via
  `sendEmail({ from: getSenderFor("auth"), to: email, subject: "Verify your Odum account", html: verifyEmailHtml(link) })`
- Email HTML: clear CTA button linking to `link`, 24h expiry notice, "If you didn't request this, ignore it."
- If Admin SDK unavailable (no credentials in dev): return `{ ok: true, sent: false, reason: "no_admin_sdk" }`

### Phase 3b — Send-reset route (PARALLEL with 3a)

- [x] [AGENT] P3b. Create `app/api/auth/send-reset/route.ts`:

```typescript
// POST /api/auth/send-reset
// Body: { email: string }
// Generates a Firebase password-reset link via Admin SDK and sends it through Resend.
// ActionCodeSettings.url = NEXT_PUBLIC_SITE_URL + "/auth/reset-password"
```

- Same pattern as 3a but calls `auth.generatePasswordResetLink(email, { url: continueUrl })`
- Subject: `"Reset your Odum password"`
- Email HTML: CTA button + "Link expires in 1 hour. If you didn't request this, ignore it."

### Phase 3c — Update login page forgot-password (SEQUENTIAL after 3b)

- [x] [AGENT] P3c. Update `app/(public)/login/page.tsx` `handleForgotPassword`:
  - Replace direct `sendPasswordResetEmail(auth, email)` Firebase call with
    `fetch("/api/auth/send-reset", { method: "POST", body: JSON.stringify({ email }) })`
  - Keep the demo/mock guard (already there: shows toast and returns early in demo/mock mode)
  - Success toast: "Reset email sent — check your inbox."

**QG gate after Phase 3:** TypeScript clean, no `any` types.

---

## Phase 4 — Custom action handler pages

Firebase redirects `oobCode` + `mode` to our pages after the user clicks the email link.

### Phase 4a — Verify-email page (PARALLEL with 4b)

- [x] [AGENT] P4a. Create `app/(public)/auth/verify-email/page.tsx`:
  - Read `?oobCode=` + `?mode=verifyEmail` from URL params
  - If `mode !== "verifyEmail"` or `oobCode` missing → show error state
  - On mount: call `applyActionCode(auth, oobCode)` from `firebase/auth` (client-side SDK)
  - States: loading → success ("Your email has been verified. You can now log in.") → error
  - Success state: button "Go to dashboard" → `/dashboard`
  - Error state: button "Request a new verification link" (calls `/api/auth/send-verification` with the user's email if
    known, otherwise shows "Contact support")

### Phase 4b — Reset-password page (PARALLEL with 4a)

- [x] [AGENT] P4b. Create `app/(public)/auth/reset-password/page.tsx`:
  - Read `?oobCode=` + `?mode=resetPassword` + `?continueUrl=` from URL params
  - On mount: call `verifyPasswordResetCode(auth, oobCode)` to get the associated email, display it
  - Form: new password input + confirm password input
  - Submit: call `confirmPasswordReset(auth, oobCode, newPassword)` from `firebase/auth`
  - Success: "Password updated. Signing you in…" → auto-redirect to `/login`
  - Error states: expired link, already-used link, mismatch password validation

---

## Phase 5 — QG + quickmerge

- [ ] [AGENT] P5. Run full quality gates and quickmerge:
  ```bash
  cd unified-trading-system-ui && bash scripts/quality-gates.sh
  ```
  Then if clean:
  ```bash
  bash scripts/quickmerge.sh "feat: Resend email architecture — auth@ and hello@ senders, custom action handler pages, fix .co.uk typo" --agent
  ```

---

## Success criteria

| Gate | Criterion                                                                                                                                                                          |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C2   | All existing UI vitest tests still pass (`CI=true npm test -- --run`)                                                                                                              |
| C3   | TypeScript strict — no `any`, no `ts-ignore`                                                                                                                                       |
| C4   | `quality-gates.sh` green (includes invariant Playwright gate [2.6])                                                                                                                |
| C5   | Quickmerge PR created on `live-defi-rollout`                                                                                                                                       |
| D3   | After operator adds `RESEND_API_KEY` to Cloud Run: contact form sends from `hello@mail.odum-research.com`; verify-email and reset-password come from `auth@mail.odum-research.com` |
| B6   | Operator receives a test email from each sender address and confirms deliverability                                                                                                |

## What you do vs what code does

| #   | Who      | Action                                                                                              |
| --- | -------- | --------------------------------------------------------------------------------------------------- |
| 1   | **You**  | Add `mail.odum-research.com` domain in Resend + get DNS records                                     |
| 2   | **You**  | Add `staging-mail.odum-research.com` domain + get DNS records                                       |
| 3   | **You**  | Add DNS records at registrar → verify in Resend                                                     |
| 4   | **You**  | Resend → confirm prod key sending scope covers `mail.odum-research.com` (key already in SM)         |
| 5   | **You**  | Resend → confirm staging key sending scope covers `staging-mail.odum-research.com`                  |
| 6   | **You**  | Confirm Cloud Run mounts SM secrets as `RESEND_API_KEY` (already mounted — just verify the name)    |
| 7   | **You**  | Firebase Console → Auth → Templates → set custom action URL to `https://www.odum-research.com/auth` |
| 8   | **Code** | `lib/email/resend.ts` shared client                                                                 |
| 9   | **Code** | Fix `website@` → `hello@` and `.co.uk` → `.com` in existing routes                                  |
| 10  | **Code** | `/api/questionnaire/email` — acknowledgement + internal notify on questionnaire submit              |
| 11  | **Code** | Wire questionnaire page to call email route after successful Firestore write                        |
| 12  | **Code** | `/strategy-evaluation` — online Strategy Evaluation Form (replaces PDF)                             |
| 13  | **Code** | `/api/strategy-evaluation/submit` — Firestore persist + Resend email                                |
| 14  | **Code** | Add CTA links to `/strategy-evaluation` from briefings and service pages                            |
| 15  | **Code** | `/api/auth/send-verification` — Admin SDK link gen → Resend                                         |
| 16  | **Code** | `/api/auth/send-reset` — Admin SDK link gen → Resend                                                |
| 17  | **Code** | Update login page to use our reset route                                                            |
| 18  | **Code** | `/auth/verify-email` custom action handler page                                                     |
| 19  | **Code** | `/auth/reset-password` custom action handler page                                                   |

---

## Notes

- No `resend` npm package — use raw `fetch` (same as existing routes; keeps bundle clean)
- `RESEND_API_KEY` is server-only — never put it in `NEXT_PUBLIC_*` or `docker-build.env.*`
- Dev has no API key → `sendEmail` returns `{ ok: true, sent: false }` silently — no UX breakage
- Staging Firebase project (if used) needs its own custom action URL pointing to the staging hostname
- The `.co.uk` addresses (`info@odum-research.co.uk`) in the existing routes appear to be a legacy typo — the canonical
  domain is `odum-research.com`
