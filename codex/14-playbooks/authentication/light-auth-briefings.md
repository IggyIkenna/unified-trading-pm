---
scope: [engineer, admin]
---

# Light auth — briefings gate

The pb2 playbook (Research & Documentation) sits behind a lightweight password gate, not Firebase. Not-easily-hackable
but not impenetrable — deliberately low-friction for prospects who have already had a first call.

## Tiered gate model (M4, locked 2026-04-20)

Decision M4 from `marketing_site_restructure_2026_04_20.plan.md` locks the gate as a **tiered** model matching the
existing 3-tier authentication stack:

| Tier | Scope                                                                                          | Mechanism                                                                   |
| ---- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 0    | Public pages (`/platform`, `/signals`, `/investment-management`, `/regulatory`, `/who-we-are`) | No auth. Anonymous. Rule-06 / rule-08 redacted.                             |
| 1    | Briefings (`/briefings/*`)                                                                     | **Light-auth code** (this doc). localStorage session.                       |
| 2    | Staging demo (`/demo/*`)                                                                       | Firebase staging — see [firebase-staging.md](firebase-staging.md).          |
| 3    | Production demo + client portal                                                                | Firebase production — see [firebase-production.md](firebase-production.md). |

This doc covers Tier 1 only.

## Code path

- Gate component:
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx)
- Code validator: [lib/briefings/access-code.ts](unified-trading-system-ui/lib/briefings/access-code.ts)
- Session store: [lib/briefings/session.ts](unified-trading-system-ui/lib/briefings/session.ts)
- Layout wrapper: [app/(public)/briefings/layout.tsx](<unified-trading-system-ui/app/(public)/briefings/layout.tsx>)
- Storage key: `localStorage.odum-briefing-session`

## Per-path code pattern (M4 tiered gate)

Decision M4 also locks **per-path codes**: every pillar can have its own access code so a prospect in (for example) an
Investment Management conversation receives a code that only unlocks the IM briefing, not the DART or Regulatory
pillars. A single shared **global** code still works as a fallback (useful for broad walkthroughs and dev mode).

### Env vars (six per-path codes + one global)

The code validator reads seven env vars and treats a session as authenticated if the entered code matches **any** of the
non-empty ones:

| Env var                                                  | Pillar slug             | Unlocks                                |
| -------------------------------------------------------- | ----------------------- | -------------------------------------- |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE`                       | _(global fallback)_     | Every pillar                           |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_INVESTMENT_MANAGEMENT` | `investment-management` | IM briefing                            |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_REGULATORY`            | `regulatory`            | Regulatory Umbrella briefing           |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_PLATFORM`              | `platform`              | DART umbrella briefing                 |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_DART_SIGNALS_IN`       | `dart-signals-in`       | DART Signals-In briefing               |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_DART_FULL`             | `dart-full`             | DART Full pipeline briefing            |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE_SIGNALS_OUT`           | `signals-out`           | Signals Service (signals-out) briefing |

### Validator semantics

`accessCodeMatches(input)` in `lib/briefings/access-code.ts`:

1. Trim the input.
2. If `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` is set and `input` matches, return `true`.
3. Otherwise, if `input` matches any of the six per-path codes that are set, return `true`.
4. Otherwise, return `false`.

`ACCESS_CODE_REQUIRED` is `true` if any of the seven env vars is set. When none are set (local dev with all env vars
empty) the gate is disabled entirely — useful for UI contributors who don't need to enter codes locally.

### Current-path scoping (follow-up)

The validator today treats any valid code as unlocking _every_ pillar (session-level auth). A future enhancement is to
scope the session to the pillar that the code belongs to — e.g. the IM code unlocks only
`/briefings/investment-management`, forcing the prospect to request a separate code for DART. Tracked as a Stage 3
follow-up. The env-var structure above is already shaped for this.

## Dev-default fallback

For local UI development the plan-locked pattern is: leave every env var empty in `config/docker-build.env.local` and
`.env.local`. The gate reports `ACCESS_CODE_REQUIRED = false` and renders briefing content directly. Any staging or
production build MUST have at least one env var set to keep the gate enforced.

## Mechanism

1. Prospect visits `/briefings` (or a sub-briefing URL).
2. Layout checks `localStorage.odum-briefing-session` — if valid session exists, renders content.
3. Otherwise renders the gate component.
4. Prospect enters username + access code.
5. Gate calls `accessCodeMatches(input)` — matches either the global code or any per-path code.
6. On match, writes session to localStorage with TTL (default: session duration).

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
   for global) in [config/docker-build.env.staging](unified-trading-system-ui/config/docker-build.env.staging) and
   [config/docker-build.env.production](unified-trading-system-ui/config/docker-build.env.production).
3. Redeploy staging + prod UI.
4. Send new code to affected prospects via their sales contact.

## Prospect invite flow

1. Sales contact confirms first call went well; prospect wants deeper briefing content.
2. Sales contact picks the matching pillar(s) from the six available (IM / Regulatory / DART umbrella / DART Signals-In
   / DART Full / Signals-Out) and sends the corresponding per-path code (or the global code if the prospect wants broad
   access).
3. Email to prospect includes:
   - Link to `/briefings/{pillar-slug}`
   - Access code (current rotation)
   - One-line framing of the pillar
4. Prospect visits, enters code, reads the pillar.
5. Sales contact follows up with a second call based on what prospect read.

## Why not Firebase for briefings?

- **Friction** — Firebase sign-up/sign-in requires email verification loop; prospects drop off. Light auth is
  copy-paste-and-go.
- **Low-data-value** — briefings content is pre-commercial marketing. Someone who cracks the code gets marketing decks.
  Not a breach.
- **Rotation simplicity** — access code change is a single env-var update and redeploy; no per-user account cleanup.

## NOT for

- Anything behind `(platform)` (real app features)
- Investor-relations content (`/investor-relations/*`) — that's Firebase-gated because it includes un-released
  financials
- `/demo` staging + production — Firebase-gated (Tier 2 / Tier 3 above)

## Testing

- Playwright specs:
  - `unified-trading-system-ui/tests/e2e/playbooks/research-and-documentation.spec.ts` (pillar walkthrough)
  - `unified-trading-system-ui/tests/e2e/playbooks/marketing-site-restructure.spec.ts` (gate render + 5-path nav)
- Assertions:
  1. Visiting `/briefings` without session → gate renders
  2. Entering correct code (global or any per-path) → session saves, content renders
  3. Entering wrong code → rejection message, no session
  4. Navigating to a sub-briefing with valid session → renders without re-prompting
  5. localStorage cleared → gate re-appears
  6. Each of the six `/briefings/{slug}` pillar routes renders once session is valid

## Related

- Tier model index: [README.md](README.md)
- Post-call journey: [../playbooks/02-research-and-documentation.md](../playbooks/02-research-and-documentation.md)
- Marketing journey (Tier 0): [../experience/marketing-journey.md](../experience/marketing-journey.md)
- Firebase staging (next tier up): [firebase-staging.md](firebase-staging.md)
- Route mapping: [../implementation-mapping/route-mapping.md](../implementation-mapping/route-mapping.md)
- Restructure plan:
  [../../../plans/active/marketing_site_restructure_2026_04_20.plan.md](../../../plans/active/marketing_site_restructure_2026_04_20.plan.md)
