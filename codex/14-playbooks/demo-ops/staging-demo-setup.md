---
scope: [admin, sales, engineer]
---

# Staging Demo Setup — Operator Checklist

> **Status:** canonical (2026-04-24) **Owner:** Sales + UI Architecture **SSOT for:**
> `unified-trading-system-ui/lib/auth/personas.ts`, `unified-trading-system-ui/lib/auth/demo-provider.ts`,
> `unified-trading-system-ui/components/demo/DemoPlanToggle.tsx`. **Plan:**
> [`../../plans/active/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../../plans/active/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
> **Companion docs:** [`demo-restriction-profiles.md`](./demo-restriction-profiles.md),
> [`dart-demo-modes.md`](./dart-demo-modes.md),
> [`../experience/staging-demo-journey.md`](../experience/staging-demo-journey.md),
> [`../../04-architecture/service-family-scope.md`](../../04-architecture/service-family-scope.md),
> [`../../08-workflows/client-onboarding.md`](../../08-workflows/client-onboarding.md).

---

## §1 — What this doc is

Step-by-step checklist for the operator who needs to onboard a new demo client to the staging environment. Covers both
the code changes (personas + preseed) and the sales handoff (profile YAML + email). The checklist is derived from the
live wiring shipped 2026-04-24 around the Desmond H-W and Elysium demo shapes.

This is an operational playbook — _how_ to configure a demo. For the _what_ (commercial framing, scope design), see
[`demo-decision-matrix.md`](./demo-decision-matrix.md) + [`pre-demo-curation-rules.md`](./pre-demo-curation-rules.md).

> **Auth context — important.** UAT (`uat.odum-research.com` → Cloud Run service `odum-portal-staging`) currently runs
> the **demo auth provider** (`NEXT_PUBLIC_AUTH_PROVIDER=demo` in `docker-build.env.uat`). A real Firebase staging
> project (`odum-staging`, aliased `staging` in `.firebaserc`) **is provisioned** but not yet wired into the UAT bundle.
> The demo provider is retained because the `DemoPlanToggle` (DART Full ⇄ Signals-In, DeFi ⇄ DeFi Full) does
> empty-password persona swaps via `loginByEmail(pairedId, "")`, which only works client-side. See
> [`../../08-workflows/environment-mode-philosophy.md`](../../08-workflows/environment-mode-philosophy.md) §Axis 2 for
> the full trade-off analysis and the migration path to a tier-override pattern.

---

## §2 — Email-based demo persona mapping

The demo auth provider (`lib/auth/demo-provider.ts`) accepts both **persona id** and **email + password** as login
credentials. Persona lookup goes via two functions in `lib/auth/personas.ts`:

- `getPersonaById(id)` — used by `DemoPlanToggle` when swapping between paired tiers (Signals-In ↔ Full). Bypasses the
  password check — the toggle trusts the current demo session.
- `getPersonaByEmail(email)` — used when a prospect logs in with their real email. Returns the **first match**. If a
  prospect has two paired personas (same email, different tiers), login lands on whichever is listed first in the
  `PERSONAS` array. Convention: list the **Full tier first** so the initial login is the upgrade-preview variant;
  prospect toggles down to Base tier if they want to see the locked-tab experience.

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

## §3 — Persona naming convention

Every demo-client with a plan-toggle pairing uses the suffix pattern:

| Shape          | Base tier persona id       | Full tier persona id      |
| -------------- | -------------------------- | ------------------------- |
| DART (default) | `{client-slug}-signals-in` | `{client-slug}-dart-full` |
| DeFi-first     | `{client-slug}-defi`       | `{client-slug}-defi-full` |

Live examples:

- `desmond-signals-in` ↔ `desmond-dart-full` (DART shape)
- `elysium-defi` ↔ `elysium-defi-full` (DeFi-first shape — Patrick / Bank Elysium)

`DemoPlanToggle`'s `TOGGLE_MAP` is a bidirectional dict keyed by persona id; both directions must be registered so the
toggle works from either side.

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

### 5.2 Register TOGGLE_MAP (if paired)

Edit `components/demo/DemoPlanToggle.tsx::TOGGLE_MAP` — add both directions:

```ts
TOGGLE_MAP = {
  ...,
  "{client-slug}-dart-full": "{client-slug}-signals-in",
  "{client-slug}-signals-in": "{client-slug}-dart-full",
}
```

Without this, the toggle renders but clicking it is a no-op.

### 5.3 Add questionnaire preseed (if pre-scoped)

Edit `lib/auth/demo-provider.ts::QUESTIONNAIRE_PRESEEDS`. Copy shape from one of the live entries. Same preseed for both
paired personas is fine — it's the same prospect.

### 5.4 Add profile YAML to codex

Create `codex/14-playbooks/demo-ops/profiles/{persona_id}.yaml` per the canonical shape — see
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

1. Move the profile YAML to `codex/14-playbooks/demo-ops/profiles/_archived/`.
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
- [`../../04-architecture/service-family-scope.md`](../../04-architecture/service-family-scope.md) — the feature matrix
  the two tiers expose.
- [`../../08-workflows/client-onboarding.md`](../../08-workflows/client-onboarding.md) — end-to-end 7-step sequence.
