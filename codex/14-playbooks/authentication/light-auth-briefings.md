# Light auth — briefings gate

The pb2 playbook (Research & Documentation) sits behind a lightweight password gate, not Firebase. Not-easily-hackable
but not impenetrable — deliberately low-friction for prospects who have already had a first call.

## Code path

- Gate component:
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx)
- Session store: [lib/briefings/session.ts](unified-trading-system-ui/lib/briefings/session.ts)
- Layout wrapper: [app/(public)/briefings/layout.tsx](<unified-trading-system-ui/app/(public)/briefings/layout.tsx>)
- Storage key: `localStorage.odum-briefing-session`

## Mechanism

1. Prospect visits `/briefings` (or a sub-briefing URL).
2. Layout checks `localStorage.odum-briefing-session` — if valid session exists, renders content.
3. Otherwise renders the gate component.
4. Prospect enters username + access code.
5. Gate compares to `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` (build-time env var).
6. On match, writes session to localStorage with TTL (default: session duration).

## Rotation policy

Rotate the access code when:

- A prospect leaves the funnel (no commercial opportunity)
- 90 days have elapsed since last rotation
- A prospect shares the code externally (inferred from access-log anomaly)

Rotation procedure:

1. Generate new code (strong — 16+ chars mixed case + numeric; humans don't type it, they paste from the welcome email).
2. Update `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` in
   [config/docker-build.env.staging](unified-trading-system-ui/config/docker-build.env.staging) and
   [config/docker-build.env.production](unified-trading-system-ui/config/docker-build.env.production).
3. Redeploy staging + prod UI.
4. Send new code to active prospects via their sales contact.

## Prospect invite flow

1. Sales contact confirms first call went well; prospect wants deeper briefing content.
2. Sales contact sends prospect an email with:
   - Link to `/briefings`
   - Access code (current rotation)
   - One-line framing per pillar (IM / DART / Reg Umbrella) with anchor links to sub-briefings
3. Prospect visits, enters code, reads relevant pillar.
4. Sales contact follows up with a second call based on what prospect read.

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

## Testing

- Playwright spec: `unified-trading-system-ui/tests/playbooks/research-and-documentation.spec.ts`
- Assertions:
  1. Visiting `/briefings` without session → gate renders
  2. Entering correct code → session saves, content renders
  3. Entering wrong code → rejection message, no session
  4. Navigating to a sub-briefing with valid session → renders without re-prompting
  5. localStorage cleared → gate re-appears

## Related

- Post-call journey: [../playbooks/02-research-and-documentation.md](../playbooks/02-research-and-documentation.md)
- Firebase staging (next tier up): [firebase-staging.md](firebase-staging.md)
