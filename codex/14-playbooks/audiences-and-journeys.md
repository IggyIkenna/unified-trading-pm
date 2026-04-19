# Audiences and Journeys

The full matrix of WHO uses the platform, WHERE they start, and HOW they progress. Every UI route must belong to at
least one cell of this matrix.

## The three axes

1. **Audience / persona** — who the user is
2. **Playbook family** — which journey applies (pre-call / post-call / warm / paying / admin)
3. **Environment** — local dev / staging / production

## Persona × playbook matrix

| Persona                              | pb1 Marketing |  pb2 Briefings  | pb3 Demo  | Real client |           Admin           | Reference fixture                                                                                                                 |
| ------------------------------------ | :-----------: | :-------------: | :-------: | :---------: | :-----------------------: | --------------------------------------------------------------------------------------------------------------------------------- |
| Anonymous visitor                    |      ✅       |        —        |     —     |      —      |             —             | (no auth)                                                                                                                         |
| Post-first-call prospect             |      ✅       | ✅ (light auth) |     —     |      —      |             —             | Briefings access code                                                                                                             |
| Warm prospect — IM flavour           |      ✅       |       ✅        | ✅ (pb3b) |      —      |             —             | persona `prospect-im`                                                                                                             |
| Warm prospect — DART flavour         |      ✅       |       ✅        | ✅ (pb3c) |      —      |             —             | persona `prospect-dart` (to add)                                                                                                  |
| Warm prospect — Reg Umbrella flavour |      ✅       |       ✅        | ✅ (pb3a) |      —      |             —             | persona `prospect-reg` (to add)                                                                                                   |
| Real client — IM                     |      ✅       |       ✅        |     —     |     ✅      |             —             | [lib/auth/personas.ts:38](unified-trading-system-ui/lib/auth/personas.ts#L38) `client-full`, `client-data-only`, `client-premium` |
| Real client — DART (platform-only)   |      ✅       |       ✅        |     —     |     ✅      |             —             | (subset of `client-full` entitlements, no IM reporting)                                                                           |
| Real client — Reg Umbrella           |      ✅       |       ✅        |     —     |     ✅      |             —             | TBD — needs dedicated persona                                                                                                     |
| Odum investor                        |       —       |        —        |     —     |      —      | via `/investor-relations` | persona `investor`, `advisor`                                                                                                     |
| Odum internal trader                 |       —       |        —        |     —     |      —      |            ✅             | persona `internal-trader`                                                                                                         |
| Odum admin                           |      ✅       |       ✅        |    ✅     |     ✅      |            ✅             | persona `admin`                                                                                                                   |

## Environment × playbook matrix

| Playbook    | Local dev                                   | Staging (`odum-research.co.uk`)                   | Production (`odum-research.com`)             |
| ----------- | ------------------------------------------- | ------------------------------------------------- | -------------------------------------------- |
| pb1         | ✅ homepage live                            | ✅                                                | ✅                                           |
| pb2         | ✅ briefings with test password             | ✅ briefings with rotating prospect password      | ✅ briefings with rotating prospect password |
| pb3         | ✅ demo persona via localStorage or sign-in | ✅ demo Firebase account per prospect             | n/a — prospects never use prod               |
| Real client | —                                           | —                                                 | ✅ real Firebase                             |
| Admin       | ✅ admin persona                            | ✅ real admin Firebase account                    | ✅ real admin Firebase account               |
| Investor    | —                                           | ✅ (on staging with rotated password for reviews) | ✅                                           |

## Canonical journey sequence

A typical prospect progresses through this sequence:

```
Anonymous visitor
    ↓ (stumbles on homepage or is referred)
    → Opens / — sees three-service pitch (Invest / Build & Run / Regulate)
    → Clicks a service tile → lands on /investment-management or /platform or /regulatory
    → Clicks "Discuss a Mandate" or "Book a Demo" → /contact
    ↓ (Odum schedules first call)
Post-first-call prospect
    → Odum sends link to /briefings with briefings access code
    → Prospect enters code → lands on /briefings hub
    → Clicks into IM / DART / Reg-Umbrella pillar based on interest
    → Reads deep-briefing content (board-deck quality, not product walkthrough)
    ↓ (Odum schedules deeper call or demo)
Warm prospect (demo)
    → Odum provisions demo user in user-management-ui on staging
    → Odum sends link to odum-research.co.uk + demo credentials
    → Prospect signs in → lands on /dashboard → services portal
    → Experience sliced to their flavour (pb3a / pb3b / pb3c)
    ↓ (prospect commits)
Real client
    → Odum provisions real user in user-management-ui against production Firebase
    → Entitlements set to match paid package
    → Client signs in at odum-research.com → same services portal, sliced to paid entitlements
```

## Related

- Per-journey playbook docs: [playbooks/](playbooks/)
- Auth-tier details: [authentication/](authentication/)
- Environment-specific details: [environments/](environments/)
- Visibility slicing mechanism: [cross-cutting/visibility-slicing.md](cross-cutting/visibility-slicing.md)
- Demo persona fixtures: [lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts)
