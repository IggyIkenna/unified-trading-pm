---
doc_type: codex-ssot
title: Staging Demo Setup — Operator Checklist
summary:
  Operator checklist to onboard a new demo client to staging — add persona(s) to personas.ts, register a TIER_BUNDLES
  entry (tier-override pattern writing localStorage tier-override-v1), add QUESTIONNAIRE_PRESEEDS, commit a
  profiles/{id}.yaml, send the invite email, run vitest; UAT runs the demo auth provider (Firebase odum-staging is
  aspirational-only).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [admin, sales, engineer]
tags: [demo-ops, sales, staging, personas, tier-override, onboarding, ui]
related:
  [
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    ../dart/dart-terminal-vs-research.md,
    ../../08-workflows/client-onboarding.md,
  ]
created: 2026-04-24
authoritative_for: [staging demo persona onboarding checklist]
referenced_by:
  [
    /codex/02-data/questionnaire-axes.md,
    /codex/04-architecture/commercial-service-families.md,
    /codex/08-workflows/client-onboarding.md,
    /codex/14-customer-journeys/dart/dart-terminal-vs-research.md,
  ]
owner:
last_reviewed:
code_refs:
  [
    unified-trading-system-ui/lib/auth/personas.ts,
    unified-trading-system-ui/lib/auth/demo-provider.ts,
    unified-trading-system-ui/lib/auth/tier-override.ts,
    unified-trading-system-ui/components/demo/DemoPlanToggle.tsx,
  ]
---

# Staging Demo Setup — Operator Checklist

> **Status:** canonical (2026-04-24) **Owner:** Sales + UI Architecture **SSOT for:**
> `unified-trading-system-ui/lib/auth/personas.ts`, `unified-trading-system-ui/lib/auth/demo-provider.ts`,
> `unified-trading-system-ui/components/demo/DemoPlanToggle.tsx`. **Plan:**
> [`../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
> **Companion docs:** [`demo-restriction-profiles.md`](./demo-restriction-profiles.md),
> [`dart-demo-modes.md`](./dart-demo-modes.md),
> [`../experience/staging-demo-journey.md`](../experience/staging-demo-journey.md),
> [`../../04-architecture/commercial-service-families.md`](../../04-architecture/commercial-service-families.md),
> [`../../08-workflows/client-onboarding.md`](../../08-workflows/client-onboarding.md).

---

## §1 — What this doc is

Step-by-step checklist for the operator who needs to onboard a new demo client to the staging environment. Covers both
the code changes (personas + preseed) and the sales handoff (profile YAML + email). The checklist is derived from the
live wiring shipped 2026-04-24 around the Desmond H-W and Elysium demo shapes.

This is an operational playbook — _how_ to configure a demo. For the _what_ (commercial framing, scope design), see
[`demo-decision-matrix.md`](./demo-decision-matrix.md) + [`pre-demo-curation-rules.md`](./pre-demo-curation-rules.md).

> **Auth context — important (revised 2026-04-25 end-of-day).** UAT (`uat.odum-research.com` → Cloud Run service
> `odum-portal-staging`) runs the **demo auth provider** (`NEXT_PUBLIC_AUTH_PROVIDER=demo` in `docker-build.env.uat`).
> The `odum-staging` Firebase project referenced in `.firebaserc` and `firebase.json` is **aspirational config only** —
> the actual project has not been provisioned (verified via `gcloud projects describe odum-staging` →
> permission-denied/not-found and `firebase projects:list`). The toggle blocker (`DemoPlanToggle` doing empty-password
> persona swaps) has been resolved by the **tier-override refactor** in `lib/auth/tier-override.ts` shipped 2026-04-25 —
> the toggle now writes a localStorage flag that overlays entitlements on top of any user regardless of auth provider.
> UAT can graduate to real Firebase once the operator provisions the `odum-staging` project. See
> [`../../08-workflows/environment-mode-philosophy.md`](../../08-workflows/environment-mode-philosophy.md) §Axis 2 and
> [`../../../plans/ai/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md`](../../../plans/ai/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md)
> Phase A for the operator checklist.

---

## §2 — Email-based demo persona mapping

The demo auth provider (`lib/auth/demo-provider.ts`) accepts both **persona id** and **email + password** as login
credentials. Persona lookup uses `getPersonaByEmail(email)` from `lib/auth/personas.ts` — returns the first match.

> **2026-04-25 — DemoPlanToggle no longer swaps personas.** The toggle is now backed by the **tier-override** pattern in
> [`unified-trading-system-ui/lib/auth/tier-override.ts`](../../../../unified-trading-system-ui/lib/auth/tier-override.ts).
> Click writes a localStorage flag (`tier-override-v1`) keyed by user email. `useAuth()` reads it via
> `applyTierOverride()` and replaces the user's entitlements at render time — identity (email, uid, org, displayName,
> role) stays stable. This decouples the toggle from the auth provider so the same UX works in demo-mode AND real
> Firebase. See `lib/auth/tier-override.ts::TIER_BUNDLES` for the email-keyed bundle definitions.

For paired-tier demo prospects (Desmond, Patrick), the **base persona** in `personas.ts` carries the identity (org,
displayName, base entitlements). The TIER_BUNDLES entry for that email defines the alternate tier's entitlements; the
toggle flips between them client-side.

A persona entry shape:

```ts
{
  id: "desmond-dart-full",
  email: "desmondhw@gmail.com",
  password: "odum-demo-2026",
  displayName: "Desmond H-W",
  role: "client",
  org: { id: "desmond-capital", name: "Desmond Capital" },
  entitlements: [/* entitlement strings + TradingEntitlement objects */],
  description: "…",
}
```

---

## §3 — Persona naming convention (legacy + new)

Until 2026-04-25, every demo-client with a plan-toggle pairing had **two persona IDs sharing one email**, and the
`DemoPlanToggle.TOGGLE_MAP` flipped between them via persona-swap. Live examples kept for backwards compat:

| Shape          | Base tier persona id | Full tier persona id |
| -------------- | -------------------- | -------------------- |
| DART (default) | `desmond-signals-in` | `desmond-dart-full`  |
| DeFi-first     | `elysium-defi`       | `elysium-defi-full`  |

The **new pattern (2026-04-25)** is a single canonical persona per email + a `TierBundle` entry in
`lib/auth/tier-override.ts` that declares both tiers' entitlements declaratively:

```ts
{
  emailPattern: "desmondhw@gmail.com",
  defaultTier: "dart-full",
  tiers: [
    { key: "dart-full",        label: "DART Full",  entitlements: [...], tone: "emerald" },
    { key: "dart-signals-in",  label: "Signals-In", entitlements: [...], tone: "amber"  },
  ],
}
```

The bundle is the SSOT for both tiers' entitlement sets; the persona just carries identity. The toggle reads/writes
`localStorage["tier-override-v1"]` keyed by user email and broadcasts a `TIER_OVERRIDE_EVENT` to force a re-render in
`useAuth()`. No re-login, no `signOut`/`signIn`, no second persona lookup — all client-side state.

---

## §4 — Questionnaire pre-seed on email-based login

`demo-provider.ts` exports a `QUESTIONNAIRE_PRESEEDS` dict keyed by persona id. On successful email-based login, if the
resolved persona matches a preseed key, the provider writes the preseed payload to
`localStorage["questionnaire-response-v1"]` **before** returning the auth user.

This skips the questionnaire page for demo clients who've already discussed shape with Ikenna over email / Calendly. The
Explore tab picks the preseeded response up on first navigation.

A preseed entry has the same shape as a real `QuestionnaireResponse` (see
[`../../02-data/questionnaire-axes.md`](../../02-data/questionnaire-axes.md)):

```ts
"desmond-dart-full": {
  categories: ["CeFi", "DeFi"],
  instrument_types: ["perp"],
  venue_scope: "all",
  strategy_style: ["carry", "arbitrage", "stat_arb"],
  service_family: "DART",
  fund_structure: ["prop"],
  market_neutral: "neutral",
  share_class_preferences: [],
  risk_profile: "low",
  leverage_preference: "low",
  target_sharpe_min: null,
}
```

Preseed is written **after** persona hydration so it's tied to the persona id, not the email — paired Base and Full
personas typically share the same preseed payload (they're the same prospect). `DemoPlanToggle` calls
`loginByEmail(pairedPersonaId, "")`, which re-runs the preseed write — no data loss when toggling tiers.

---

## §5 — Operator checklist: onboard a new demo client

Follow in order; each step depends on the previous.

### 5.1 Add persona(s) to `personas.ts`

Append to the `PERSONAS` array in `unified-trading-system-ui/lib/auth/personas.ts`. If the client wants a plan toggle
(DART Full vs Signals-In, or DeFi-full vs DeFi-base), add **both** personas sharing the same email. List the Full tier
first so `getPersonaByEmail` lands on it.

Entitlement sets:

- **DART Full:** `[investor-relations, investor-platform, data-pro, execution-full, ml-full, strategy-full, reporting]`
- **DART Signals-In:** drop `ml-full` and `strategy-full` from the above.
- **DeFi Full:** `[data-pro, execution-full, strategy-full, {domain:trading-defi, tier:basic}, reporting]`
- **DeFi Base:** drop `strategy-full`.

### 5.2 Register TierBundle (if paired)

Edit `lib/auth/tier-override.ts::TIER_BUNDLES` — append an entry keyed by the prospect's email:

```ts
{
  emailPattern: "<prospect-email>",
  defaultTier: "dart-full",       // or "defi-full" for DeFi-first shape
  tiers: [
    { key: "dart-full",       label: "DART Full",  entitlements: [...full set...], tone: "emerald" },
    { key: "dart-signals-in", label: "Signals-In", entitlements: [...signals-in set...], tone: "amber" },
  ],
}
```

The bundle is the SSOT for what each tier surfaces. `DemoPlanToggle` renders for any user whose email matches a bundle
entry — works in demo mode AND real Firebase mode.

### 5.3 Add questionnaire preseed (if pre-scoped)

Edit `lib/auth/demo-provider.ts::QUESTIONNAIRE_PRESEEDS`. Copy shape from one of the live entries. Same preseed for both
paired personas is fine — it's the same prospect.

### 5.4 Add profile YAML to codex

Create `codex/14-customer-journeys/demo-ops/profiles/{persona_id}.yaml` per the canonical shape — see
[`profiles/desmond-dart-full.yaml`](./profiles/desmond-dart-full.yaml) for the reference template. Include:

- Persona-id, display-name, email, role, org, entitlements
- `questionnaire_response` mirroring the preseed
- `tiles` declaration (unlocked / locked / locked-redirect / hidden per tile)
- `plan_toggle` block (paired persona id + tier labels) if applicable
- `notes` — prospect context (Telegram / email / call insights the operator already has)
- `walkthrough_hints` — landing surfaces + demo talking points

Profile YAMLs are committed alongside code changes so the sales context travels with the persona definition.

### 5.5 Send the invite email

Email template:

```
Subject: Staging demo access — Odum

Hi {first_name},

Your demo account is ready on our staging environment.

  URL:      https://odum-research.com
  Email:    {email}
  Password: {password}

The landing page is shaped by the answers we captured over
{Calendly / email / our call}, so you should see a strategy universe that
matches the shapes we discussed.

If you're on our DART engagement, you'll see a small tier-toggle in the top
nav — flip it to compare the two DART tiers (Full vs Signals-In) in the same
session; the strategy catalogue is identical but the research / promote tools
unlock differently.

Any questions or reservations — reply directly or book a follow-up at
https://calendly.com/odum-ikenna.

— Ikenna
```

### 5.6 QG gate

Run `cd unified-trading-system-ui && CI=true npm test -- --run` to confirm the new persona + preseed don't break the
vitest suite. If green, commit alongside the YAML profile on the same branch.

---

## §6 — Removing a demo persona

If a prospect churns or goes dark, archive rather than delete — prior meeting records in
[`account-intelligence-record.md`](./account-intelligence-record.md) may still reference the persona id.

1. Move the profile YAML to `codex/14-customer-journeys/demo-ops/profiles/_archived/`.
2. Leave the persona in `PERSONAS` with a comment `// archived YYYY-MM-DD — {reason}`.
3. Remove from `TOGGLE_MAP` to clean up the nav toggle.
4. Drop the `QUESTIONNAIRE_PRESEEDS` entry.

---

## §7 — Cross-references

- [`profiles/desmond-dart-full.yaml`](./profiles/desmond-dart-full.yaml) +
  [`profiles/desmond-signals-in.yaml`](./profiles/desmond-signals-in.yaml) — canonical worked example.
- [`demo-restriction-profiles.md`](./demo-restriction-profiles.md) — per-tile locking model this persona system feeds.
- [`dart-demo-modes.md`](./dart-demo-modes.md) — broader-platform / turbo / deep-dive flavours that layer on top of the
  persona.
- [`../../04-architecture/commercial-service-families.md`](../../04-architecture/commercial-service-families.md) — the
  feature matrix the two tiers expose.
- [`../../08-workflows/client-onboarding.md`](../../08-workflows/client-onboarding.md) — end-to-end 7-step sequence.
