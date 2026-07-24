---
doc_type: codex-ssot
title: Email Architecture — Resend (UTS UI)
summary:
  UTS-UI transactional/onboarding email via Resend — server-side sendEmail helper, dispatchEmail client wrapper,
  getMailDomain/getSenderFor domain+sender selection, and resend.dev sandbox routing for local dev.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, email, resend, self-healing, escalation]
related: []
created: 2026-05-06
authoritative_for: [Resend transactional email architecture (UTS-UI)]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Email Architecture — Resend (UTS UI)

**Status:** active. **Source of truth (code):**
[`unified-trading-system-ui/lib/email/`](../../../unified-trading-system-ui/lib/email/). **SSOT for sandbox / domain
rules:** [`lib/email/resend.ts`](../../../unified-trading-system-ui/lib/email/resend.ts) — domain selection, sender
variants, sandbox routing.

All transactional + onboarding emails from the unified-trading-system-ui go through Resend (`api.resend.com/emails`).
This doc captures the surface so consumers can find the right helper, and operators can understand domain / sandbox
routing.

---

## Surface

### Server-side helper (the only place that hits Resend)

`lib/email/resend.ts` — `sendEmail(params: ResendEmailParams) → Promise<SendResult>`:

- Single function. Server-side only (uses `RESEND_API_KEY` env var).
- POSTs to `https://api.resend.com/emails` with `{ from, to, subject, html, reply_to?, bcc? }`.
- If `RESEND_API_KEY` is unset → no-op return `{ ok: true, sent: false, reason: "no_api_key" }` (graceful degrade for
  local dev without secrets).
- On non-2xx from Resend → `{ ok: false, sent: false, reason: "resend_<status>" }`.

### Client-side wrapper

`lib/email/client.ts` — `dispatchEmail(routePath, payload) → Promise<EmailDispatchOutcome>`:

- Used by the public `/contact` form and any other public surface.
- Just `fetch(routePath, POST)` to a server route. The server route does authorisation + validation + the actual
  `sendEmail` call.
- Normalises HTTP outcome into `EmailDispatchOutcome` (`queued` / `client-error` / `server-error`) so the UI renders via
  `EmailStatusBanner`.

### Route-side glue

`lib/email/route-helpers.ts` — common helpers for the API routes (validation, idempotency, error wrapping).

---

## API routes that send email

| Route                                              | Purpose                                                           |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| `app/api/contact/route.ts`                         | Public contact form → ops mailbox                                 |
| `app/api/questionnaire/email/route.ts`             | Questionnaire follow-up email                                     |
| `app/api/strategy-evaluation/email/route.ts`       | Strategy-evaluation result delivery                               |
| `app/api/strategy-evaluation/resend-link/route.ts` | Resend the access link (auth-style)                               |
| `app/api/onboarding/confirm-email/route.ts`        | Account confirmation                                              |
| `lib/strategy-evaluation/email/route.ts`           | Internal helper used by the strategy-evaluation API surface above |

---

## Domain + sender selection

Driven by `NEXT_PUBLIC_SITE_URL` via `getMailDomain()`:

| `NEXT_PUBLIC_SITE_URL` host             | Mail domain              | Notes                                                   |
| --------------------------------------- | ------------------------ | ------------------------------------------------------- |
| `www.odum-research.com`                 | `mail.odum-research.com` | Production sender                                       |
| `uat.odum-research.com`                 | `mail.odum-research.com` | UAT shares prod sender (staging-domain DNS not set up)  |
| `odum-research.co.uk`                   | `mail.odum-research.com` | .co.uk redirect domain — same prod sender               |
| anything else (incl. localhost / unset) | `resend.dev`             | Sandbox mode (Resend free-tier `onboarding@resend.dev`) |

Sender variants via `getSenderFor(type)`:

- `getSenderFor("hello")` → `hello@<domain>` — transactional / contact / questionnaire / strategy-eval delivery.
- `getSenderFor("auth")` → `auth@<domain>` — auth flows (resend-link, confirm-email).
- Sandbox forces sender to `onboarding@resend.dev` regardless of `type`.

---

## Sandbox routing (local dev)

When the resolved domain is `resend.dev`:

- `isSandboxMode()` returns `true`.
- All outbound emails are redirected to `RESEND_TEST_RECIPIENT` (default: `ikenna@odum-research.com`) — Resend's
  free-tier sandbox refuses any recipient that isn't the registered test account.
- `bcc` is dropped in sandbox.
- Subject is prefixed with `[sandbox]`.
- HTML body gets a yellow banner showing the original `to` / `bcc` so the operator can see what the email would have
  looked like in prod.
- UAT + prod paths fall through unchanged.

To override the sandbox recipient for a specific Resend test account, set `RESEND_TEST_RECIPIENT=<email>` in the local
`.env`.

---

## Configuration

| Env var                 | Required | Purpose                                                                        |
| ----------------------- | -------- | ------------------------------------------------------------------------------ |
| `RESEND_API_KEY`        | prod/uat | Resend API key. If unset, `sendEmail` no-ops (`sent: false`).                  |
| `NEXT_PUBLIC_SITE_URL`  | prod/uat | Drives `getMailDomain()` selection                                             |
| `RESEND_TEST_RECIPIENT` | optional | Overrides the sandbox-mode test recipient (default `ikenna@odum-research.com`) |

Local dev: leave `RESEND_API_KEY` set to your personal Resend test key (or unset for no-op mode); `NEXT_PUBLIC_SITE_URL`
defaults to localhost which triggers sandbox routing automatically.

---

## When you add a new email-sending route

1. Server route imports `sendEmail` from `lib/email/resend.ts`. Pass
   `{ to, subject, html, from?: getSenderFor("hello"|"auth"), bcc?, replyTo? }`.
2. If the route is publicly invokable, gate behind auth/rate-limit per `route-helpers.ts` patterns.
3. If the email is auth-related (e.g. confirm-email, resend-link), use `getSenderFor("auth")`. Transactional →
   `getSenderFor("hello")`.
4. Client side: use `dispatchEmail(routePath, payload)` from `lib/email/client.ts`; render `EmailDispatchOutcome` via
   `EmailStatusBanner`.
5. Tests: stub `sendEmail` (or stub `RESEND_API_KEY=null` for the no-op path); don't hit real Resend in CI.

---

## Cross-references

- Original implementation plan (archived): `plans/archive/resend_email_architecture_2026_04_23.plan.md`.
- Master plan: `plans/archive/2026_07/master_to_live_defi_2026_05_23.md` — email is a Tier-2 service surface (UTS-UI).
- Dev secrets: `unified-trading-system-ui/scripts/load-dev-secrets.sh`.
- Deployment env vars: `unified-trading-system-ui/docs/core/DEPLOYMENT.md`.
