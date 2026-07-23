---
doc_type: codex-ssot
title: Light auth — Deep Dive briefings gate
summary:
  Tier-1 light-auth gate for Deep Dive briefings (/briefings, /docs, /our-story, /faq) — questionnaire submission or
  access-code entry, localStorage session, seven NEXT_PUBLIC_BRIEFING_ACCESS_CODE env vars (six per-path + one global);
  deliberately not Firebase to keep prospect friction low.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [auth, ui, briefings, access-code, prospect, onboarding]
related:
  [
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/authentication/firebase-production.md,
    ../../08-workflows/client-onboarding.md,
  ]
created: 2026-04-19
authoritative_for: [Deep Dive briefings light-auth code gate, per-path briefing access-code env-var scheme]
referenced_by:
  [
    /codex/08-workflows/client-onboarding.md,
    /codex/08-workflows/prospect-questionnaire-flow.md,
    /codex/08-workflows/signup-signin-workflow.md,
    /codex/14-customer-journeys/authentication/README.md,
    /codex/14-customer-journeys/authentication/firebase-local.md,
    /codex/14-customer-journeys/authentication/firebase-production.md,
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Light auth — Deep Dive briefings gate

The pb2 playbook (Deep Dive — formerly "Research & Documentation") sits behind a lightweight password gate, not
Firebase. Not-easily-hackable but not impenetrable — deliberately low-friction for prospects who haven't yet been
through a Firebase sign-up.

**Primary access path is the brief questionnaire embedded inline on the lock screen** (since 2026-04-25). Submitting it
auto-activates the briefing session AND emails the prospect the code for return visits. The legacy "type the code you
were given" entry is still supported as a secondary disclosure ("I already have an access code") for return-visit /
second-device users.

## Tiered gate model (M4, locked 2026-04-20; updated 2026-04-25)

Decision M4 from `marketing_site_restructure_2026_04_20.plan.md` locks the gate as a **tiered** model matching the
existing 3-tier authentication stack:

| Tier | Scope                                                                                                                     | Mechanism                                                                                                                    |
| ---- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 0    | Public pages (`/`, `/investment-management`, `/platform`, `/signals`, `/regulatory`, `/who-we-are`, `/story`, `/contact`) | No auth. Anonymous. Rule-06 / rule-08 redacted.                                                                              |
| 1    | Deep Dive (`/briefings/*`, `/docs`, `/our-story`, `/faq`)                                                                 | **Light-auth code OR questionnaire submission** (this doc). localStorage session.                                            |
| 2    | Staging Sandbox demo (`/demo/*`)                                                                                          | Firebase staging — see [firebase-staging.md](firebase-staging.md). Gated additionally by Strategy Evaluation DDQ submission. |
| 3    | Production demo + client portal                                                                                           | Firebase production — see [firebase-production.md](firebase-production.md).                                                  |

This doc covers Tier 1 only. The Sandbox demo at Tier 2 has a second human-gate: a submitted Strategy Evaluation DDQ
(`/strategy-evaluation`) is required before Odum provisions a curated walkthrough — see
[../../08-workflows/client-onboarding.md](../../08-workflows/client-onboarding.md) §5.

## Code path

- Gate component:
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx)
  — embeds the QuestionnaireForm as the primary access path; renders a `<details>` "I already have an access code"
  disclosure as the secondary path.
- Embedded form:
  [components/questionnaire/questionnaire-form.tsx](unified-trading-system-ui/components/questionnaire/questionnaire-form.tsx)
  — reusable; mounted both on the standalone `/questionnaire` page and inside the gate (with `compact` + `returnPath`
  props).
- Code validator: [lib/briefings/access-code.ts](unified-trading-system-ui/lib/briefings/access-code.ts)
- Session store: [lib/briefings/session.ts](unified-trading-system-ui/lib/briefings/session.ts)
- Layout wrappers (each route group wraps in `<BriefingAccessGate>`):
  - [app/(public)/briefings/layout.tsx](<unified-trading-system-ui/app/(public)/briefings/layout.tsx>)
  - [app/(public)/docs/layout.tsx](<unified-trading-system-ui/app/(public)/docs/layout.tsx>)
  - [app/(public)/our-story/layout.tsx](<unified-trading-system-ui/app/(public)/our-story/layout.tsx>)
  - [app/(public)/faq/layout.tsx](<unified-trading-system-ui/app/(public)/faq/layout.tsx>)
- Email-back endpoint:
  [app/api/questionnaire/email/route.ts](unified-trading-system-ui/app/api/questionnaire/email/route.ts) — sends the
  access code + Calendly CTA + Strategy Evaluation pointer to the prospect; BCC `info@odum-research.com`.
- Storage key: `localStorage.odum-briefing-session`

## Per-path code pattern

Per-path codes still exist for sales-attribution rotation: a prospect handed the IM code unlocks every Deep Dive page,
but the code's identity tags their cohort in the access-code fingerprint stored on questionnaire submissions. A single
shared **global** code still works as a fallback (useful for broad walkthroughs and dev mode).

### Env vars (six per-path codes + one global)

The code validator reads seven env vars and treats a session as authenticated if the entered code matches **any** of the
non-empty ones:

| Env var                                                  | Pillar slug             | Unlocks                      |
| -------------------------------------------------------- | ----------------------- | ---------------------------- |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE`                       | _(global fallback)_     | Every Deep Dive page         |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_INVESTMENT_MANAGEMENT` | `investment-management` | IM briefing                  |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_REGULATORY`            | `regulatory`            | Regulatory Umbrella briefing |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_PLATFORM`              | `platform`              | DART umbrella briefing       |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_DART_SIGNALS_IN`       | `dart-signals-in`       | DART Signals-In briefing     |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_DART_FULL`             | `dart-full`             | DART Full pipeline briefing  |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_SIGNALS_OUT`           | `signals-out`           | Odum Signals briefing        |

Auto-emit: the code returned in the post-questionnaire email is the **global** code
(`NEXT_PUBLIC_BRIEFING_ACCESS_CODE`). If only per-path codes are configured (no global), the email omits the code
section — prospects in that env unlock via questionnaire submit alone, with no return-visit fallback. Operationally we
always set the global, so this is a defensive branch only.

### Validator semantics

`accessCodeMatches(input)` in `lib/briefings/access-code.ts`:

1. Trim the input.
2. If `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` is set and `input` matches, return `true`.
3. Otherwise, if `input` matches any of the six per-path codes that are set, return `true`.
4. Otherwise, return `false`.

`ACCESS_CODE_REQUIRED` is `true` if any of the seven env vars is set. When none are set (local dev with all env vars
empty) the gate is disabled entirely — useful for UI contributors who don't need to enter codes locally.

### Current-path scoping (follow-up)

The validator today treats any valid code as unlocking _every_ Deep Dive page (session-level auth). A future enhancement
is to scope the session to the pillar that the code belongs to. Tracked as a Stage 3 follow-up. The env-var structure
above is already shaped for this.

> **[DELTA 2026-05-22]** **Current state:** Any valid code (global or per-path) unlocks all Deep Dive pages at the
> session level — no per-pillar scoping. **Planned delta:** Stage 3 follow-up scopes each session to the pillar whose
> code was used; per-path codes already declared (env-var structure ready). **Target:** Stage 3 refactor phase
> (`/codex/14-customer-journeys/roadmap/next-waves.md`).

## Dev-default fallback

For local UI development the plan-locked pattern is: leave every env var empty in `.env.local`. The gate reports
`ACCESS_CODE_REQUIRED = false` and renders Deep Dive content directly. Any staging or production build MUST have at
least one env var set to keep the gate enforced. Current set values:

- `config/docker-build.env.uat:21` → `NEXT_PUBLIC_BRIEFING_ACCESS_CODE=odum-briefings-2026`
- `config/docker-build.env.production:19` → `NEXT_PUBLIC_BRIEFING_ACCESS_CODE=odum-briefings-2026`

## Mechanism (post 2026-04-25)

### Primary path — questionnaire submission

1. Prospect visits any Deep Dive route (`/briefings`, `/briefings/<slug>`, `/docs`, `/our-story`, `/faq`).
2. Layout wraps content in `<BriefingAccessGate>`. Gate checks `localStorage.odum-briefing-session` — if set, renders
   content immediately.
3. Otherwise the gate renders:
   - A confidentiality + funnel intro (3-line explanation of why content is gated and what comes next).
   - The brief 6-axis questionnaire (`<QuestionnaireForm compact returnPath={pathname} />`) embedded inline.
   - A `<details>` "I already have an access code" disclosure with a code-entry input.
4. Prospect fills the questionnaire and submits.
5. On submit:
   - Firestore `/questionnaires/{id}` write (or localStorage in dev mock mode).
   - Persona resolved + persisted.
   - `POST /api/questionnaire/email` fired — sends the access code, "Next steps" numbered block (read briefings → book
     Calendly call → submit Strategy Evaluation DDQ to unlock Sandbox demo), Deep Dive tour list, and the questionnaire
     echo to the prospect; BCCs `info@odum-research.com`.
   - `setBriefingSessionActive()` — writes `localStorage.odum-briefing-session = "1"`.
   - `router.push(returnPath)` after 1.2s — redirects to whichever Deep Dive route the prospect was originally trying to
     reach (or `/briefings` as default).

### Secondary path — pre-existing access code (return visit / second device)

1. Prospect arrives on a Deep Dive route from an email that already contains their code (or has one from prior
   questionnaire submission).
2. Expands the "I already have an access code" disclosure on the gate.
3. Pastes code → form calls `accessCodeMatches(input)`.
4. On match: `setBriefingSessionActive()` + content renders inline (no navigation, no page reload).

## Rotation policy

Rotate the access code when:

- A prospect leaves the funnel (no commercial opportunity)
- 90 days have elapsed since last rotation
- A prospect shares the code externally (inferred from access-log anomaly)

Per-path rotation is independent — rotating the DART code does not invalidate the IM code. The global fallback code
should be rotated on the same 90-day cadence as the per-path codes.

Rotation procedure:

1. Generate new code (strong — 16+ chars mixed case + numeric; humans don't type it, they paste from the welcome email).
2. Update the relevant env var (`NEXT_PUBLIC_BRIEFING_ACCESS_CODE_*` for per-path, or `NEXT_PUBLIC_BRIEFING_ACCESS_CODE`
   for global) in [config/docker-build.env.uat](unified-trading-system-ui/config/docker-build.env.uat) and
   [config/docker-build.env.production](unified-trading-system-ui/config/docker-build.env.production).
3. Redeploy uat + prod UI: `bash scripts/deploy-cloud-run.sh --env=uat` then `--env=prod`.
4. Outstanding prospects holding the old code will need to re-submit the questionnaire (or be sent the new one directly)
   to regain access. Existing localStorage sessions are NOT invalidated — they only key on a session flag, not the code
   itself.

## Prospect invite flow (post 2026-04-25)

There are two valid prospect entry channels:

### Channel A — Cold inbound (most common now)

1. Prospect lands on the marketing site, browses public pages.
2. Clicks any Deep Dive item in the side-nav (`Briefings hub`, `Developer docs`, `FAQ`, `Investment Management`,
   `DART — Start here`, etc.) OR types a Deep Dive URL directly.
3. Hits the gate → fills questionnaire → reads briefings → books Calendly call.
4. Sales (Ikenna) sees the Firestore submission via `/admin/questionnaires` and follows up.

### Channel B — Warm hand-off (sales-led)

1. Sales contact emails prospect a direct briefing link (e.g. `/briefings/regulatory`) plus the per-path code.
2. Prospect uses the secondary "I already have a code" path on the gate.
3. Skips questionnaire (sales has already qualified).
4. Sales arranges call directly.

Both channels converge at the briefings hub, then on to the Strategy Evaluation DDQ → Sandbox demo path documented in
[../../08-workflows/client-onboarding.md](../../08-workflows/client-onboarding.md).

## Why not Firebase for Deep Dive?

- **Friction** — Firebase sign-up/sign-in requires email verification loop; prospects drop off. Light auth via
  questionnaire is one form, one submit, no email confirm.
- **Low-data-value** — briefings content is pre-commercial marketing. Someone who cracks the code gets marketing decks.
  Not a breach. The Sandbox demo (Tier 2) IS Firebase-gated AND Strategy-Eval-gated because it includes simulated client
  data.
- **Rotation simplicity** — access code change is a single env-var update and redeploy; no per-user account cleanup.

## NOT for

- Anything behind `(platform)` (real app features) — Firebase Tier 2/3.
- Investor-relations content (`/investor-relations/*`) — Firebase-gated because it includes un-released financials.
- `/demo` staging + production — Firebase-gated (Tier 2 / Tier 3 above) AND Strategy-Evaluation-gated.

## Nav surfaces

The Deep Dive section appears in TWO nav surfaces:

1. **Site-header Sheet drawer**
   ([components/shell/site-header.tsx](unified-trading-system-ui/components/shell/site-header.tsx)) — the hamburger menu
   shown on every public page. Deep Dive is rendered as a single collapsible toggle button (`Deep Dive ▾`) that expands
   inline to reveal the briefings + docs + FAQ list. Each item shows an amber lock icon when the visitor is signed-out
   and has no cached briefing session. Hardcoded constants `DEEP_DIVE_HEADLINE` + `DEEP_DIVE_BRIEFINGS` in the file
   (intentionally NOT shared with `spaces-nav-sections.tsx` — different surface, different concerns).
2. **Spaces dropdown**
   ([components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx)) —
   the in-app playbook switcher dropdown on signed-in surfaces. Deep Dive section header carries a lock hint when
   signed-out + no cached session. Each gated item routes to a `<LockedItemDialog>` that leads with the questionnaire
   CTA + "I already have a code" disclosure.

When restructuring Deep Dive (renames, additions, lock indicators), edit BOTH files. They duplicate the structure.

## Testing

- Vitest unit specs:
  - `tests/unit/components/briefings/briefing-access-gate.test.tsx` — gate state machine + embedded form + disclosure.
  - `tests/unit/components/locked-item-dialog.test.tsx` — questionnaire CTA href + disclosed code-entry path.
  - `tests/unit/components/spaces-nav-session.test.tsx` — Deep Dive section locked state + items + Overview links.
- Playwright e2e:
  - `tests/e2e/playbooks/research-and-documentation.spec.ts` (describe block: "pb2 — Deep Dive") — gate flow.
  - `tests/e2e/playbooks/refactor/refactor-g1-10-questionnaire.spec.ts` — questionnaire is reachable anonymously +
    submits + writes to localStorage.
- Assertions:
  1. Visiting any Deep Dive route without session → gate renders.
  2. Submitting the embedded questionnaire → session activates, content renders, email fires (mocked in tests).
  3. Pasting correct code into the disclosure → session activates, content renders inline.
  4. Pasting wrong code → rejection message, no session.
  5. Navigating to a sibling Deep Dive route with valid session → renders without re-prompting.
  6. localStorage cleared → gate re-appears.

## Related

- Tier model index: [README.md](README.md)
- Post-call journey: [../playbooks/02-research-and-documentation.md](../playbooks/02-research-and-documentation.md)
- Marketing journey (Tier 0): [../experience/marketing-journey.md](../experience/marketing-journey.md)
- Questionnaire schema + admin playback:
  [../../08-workflows/prospect-questionnaire-flow.md](../../08-workflows/prospect-questionnaire-flow.md)
- Onboarding 7-step sequence: [../../08-workflows/client-onboarding.md](../../08-workflows/client-onboarding.md)
- Firebase staging (next tier up): [firebase-staging.md](firebase-staging.md)
- Route mapping: [../implementation-mapping/route-mapping.md](../implementation-mapping/route-mapping.md)
- Restructure plan:
  [../../../plans/archive/marketing_site_restructure_2026_04_20.plan.md](../../../plans/archive/marketing_site_restructure_2026_04_20.plan.md)
